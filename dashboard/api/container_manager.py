"""
Container Management Module
Handles Docker container lifecycle, status monitoring, and safety enforcement
"""

import subprocess
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple


class ContainerManager:
    """Manages benchmark Docker containers with safety controls"""

    def __init__(self, benchmarks: list, config: Dict = None):
        """
        Initialize container manager

        Args:
            benchmarks: List of benchmark configurations
            config: Optional configuration dict with safety settings
        """
        self.benchmarks = {b['id']: b for b in benchmarks}
        self.config = config or self._default_config()
        self.running_containers = {}  # {benchmark_id: container_info}

    def _default_config(self) -> Dict:
        """Get default configuration"""
        return {
            'max_concurrent': 1,
            'auto_stop_on_new': True,
            'timeout_minutes': 30,
            'memory_limit_mb': 512,
            'cpu_limit': 0.5
        }

    def start_container(self, benchmark_id: str, force_stop_others: bool = True,
                       timeout_minutes: Optional[int] = None) -> Dict:
        """
        Start a benchmark container

        Args:
            benchmark_id: Benchmark identifier
            force_stop_others: Stop other running containers if limit reached
            timeout_minutes: Override default timeout

        Returns:
            Dict with container start information
        """
        # Check if benchmark exists
        benchmark = self.benchmarks.get(benchmark_id)
        if not benchmark:
            return {
                'status': 'error',
                'message': 'Benchmark not found',
                'benchmark_id': benchmark_id
            }

        # Check concurrent limit
        running_count = len(self.get_running_containers())
        if running_count >= self.config['max_concurrent']:
            if force_stop_others:
                stopped = self.stop_all_containers()
                stopped_ids = [c['benchmark_id'] for c in stopped]
            else:
                return {
                    'status': 'error',
                    'message': f'Maximum concurrent containers ({self.config["max_concurrent"]}) reached',
                    'suggestion': 'Stop running containers or set force_stop_others=true'
                }
        else:
            stopped_ids = []

        # Get benchmark directory and container name
        benchmark_dir = self._get_benchmark_directory(benchmark_id)
        container_name = self._get_container_name(benchmark_id)

        # Check if container already running
        if self._is_container_running(container_name):
            return {
                'status': 'success',
                'message': 'Container already running',
                'benchmark_id': benchmark_id,
                'container_name': container_name,
                'port': benchmark.get('port'),
                'already_running': True
            }

        # Start container using docker-compose
        try:
            result = subprocess.run(
                ['docker-compose', 'up', '-d'],
                cwd=benchmark_dir,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                return {
                    'status': 'error',
                    'message': 'Failed to start container',
                    'error': result.stderr,
                    'benchmark_id': benchmark_id
                }

            # Calculate auto-stop time
            timeout = timeout_minutes or self.config['timeout_minutes']
            auto_stop_at = datetime.now() + timedelta(minutes=timeout)

            # Track running container
            container_info = {
                'benchmark_id': benchmark_id,
                'container_name': container_name,
                'port': benchmark.get('port'),
                'started_at': datetime.now().isoformat(),
                'auto_stop_at': auto_stop_at.isoformat(),
                'timeout_minutes': timeout
            }
            self.running_containers[benchmark_id] = container_info

            return {
                'status': 'success',
                'benchmark_id': benchmark_id,
                'container_name': container_name,
                'port': benchmark.get('port'),
                'started_at': container_info['started_at'],
                'auto_stop_at': container_info['auto_stop_at'],
                'stopped_benchmarks': stopped_ids if stopped_ids else []
            }

        except subprocess.TimeoutExpired:
            return {
                'status': 'error',
                'message': 'Container start timeout',
                'benchmark_id': benchmark_id
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'benchmark_id': benchmark_id
            }

    def stop_container(self, benchmark_id: str) -> Dict:
        """
        Stop a benchmark container

        Args:
            benchmark_id: Benchmark identifier

        Returns:
            Dict with stop result
        """
        benchmark = self.benchmarks.get(benchmark_id)
        if not benchmark:
            return {
                'status': 'error',
                'message': 'Benchmark not found',
                'benchmark_id': benchmark_id
            }

        container_name = self._get_container_name(benchmark_id)
        benchmark_dir = self._get_benchmark_directory(benchmark_id)

        # Check if container is running
        if not self._is_container_running(container_name):
            # Remove from tracking if it was there
            if benchmark_id in self.running_containers:
                del self.running_containers[benchmark_id]
            return {
                'status': 'success',
                'message': 'Container not running',
                'benchmark_id': benchmark_id,
                'already_stopped': True
            }

        # Stop container using docker-compose
        try:
            result = subprocess.run(
                ['docker-compose', 'down'],
                cwd=benchmark_dir,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                return {
                    'status': 'error',
                    'message': 'Failed to stop container',
                    'error': result.stderr,
                    'benchmark_id': benchmark_id
                }

            # Calculate runtime
            runtime_seconds = None
            if benchmark_id in self.running_containers:
                started_at = datetime.fromisoformat(
                    self.running_containers[benchmark_id]['started_at']
                )
                runtime_seconds = (datetime.now() - started_at).total_seconds()
                del self.running_containers[benchmark_id]

            return {
                'status': 'success',
                'benchmark_id': benchmark_id,
                'stopped_at': datetime.now().isoformat(),
                'runtime_seconds': round(runtime_seconds, 2) if runtime_seconds else None
            }

        except subprocess.TimeoutExpired:
            return {
                'status': 'error',
                'message': 'Container stop timeout',
                'benchmark_id': benchmark_id
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'benchmark_id': benchmark_id
            }

    def get_running_containers(self) -> List[Dict]:
        """
        Get list of all running benchmark containers

        Returns:
            List of running container info dicts
        """
        containers = []

        try:
            # Use docker ps to get all running containers
            result = subprocess.run(
                ['docker', 'ps', '--format', '{{json .}}'],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if not line:
                        continue
                    try:
                        container = json.loads(line)
                        container_name = container.get('Names', '')

                        # Check if this is a Strike7 benchmark container
                        benchmark_id = self._benchmark_id_from_container_name(container_name)
                        if benchmark_id:
                            # Get additional stats
                            stats = self._get_container_stats(container_name)

                            container_info = {
                                'benchmark_id': benchmark_id,
                                'container_name': container_name,
                                'status': container.get('Status', ''),
                                'port': self.benchmarks.get(benchmark_id, {}).get('port'),
                                'memory_mb': stats.get('memory_mb', 0),
                                'cpu_percent': stats.get('cpu_percent', 0)
                            }

                            # Add tracking info if available
                            if benchmark_id in self.running_containers:
                                tracked = self.running_containers[benchmark_id]
                                container_info['started_at'] = tracked['started_at']
                                started = datetime.fromisoformat(tracked['started_at'])
                                container_info['runtime_seconds'] = (
                                    datetime.now() - started
                                ).total_seconds()

                            containers.append(container_info)
                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            print(f"Error getting running containers: {e}")

        return containers

    def stop_all_containers(self) -> List[Dict]:
        """
        Stop all running benchmark containers

        Returns:
            List of stopped container info dicts
        """
        running = self.get_running_containers()
        stopped = []

        for container in running:
            result = self.stop_container(container['benchmark_id'])
            if result['status'] == 'success':
                stopped.append({
                    'benchmark_id': container['benchmark_id'],
                    'container_name': container['container_name']
                })

        return stopped

    def get_system_status(self) -> Dict:
        """
        Get system resource status

        Returns:
            Dict with system metrics
        """
        try:
            # Get CPU count
            cpu_result = subprocess.run(
                ['nproc'],
                capture_output=True,
                text=True
            )
            cpu_count = int(cpu_result.stdout.strip()) if cpu_result.returncode == 0 else 0

            # Get memory info (Linux)
            mem_result = subprocess.run(
                ['free', '-m'],
                capture_output=True,
                text=True
            )
            total_memory = 0
            available_memory = 0
            if mem_result.returncode == 0:
                lines = mem_result.stdout.strip().split('\n')
                if len(lines) > 1:
                    parts = lines[1].split()
                    if len(parts) >= 7:
                        total_memory = int(parts[1])
                        available_memory = int(parts[6])

            # Get load average
            load_result = subprocess.run(
                ['uptime'],
                capture_output=True,
                text=True
            )
            load_average = 0.0
            if load_result.returncode == 0:
                output = load_result.stdout
                if 'load average:' in output:
                    load_str = output.split('load average:')[1].split(',')[0].strip()
                    load_average = float(load_str)

            return {
                'total_memory_mb': total_memory,
                'available_memory_mb': available_memory,
                'cpu_count': cpu_count,
                'load_average': load_average
            }
        except Exception as e:
            print(f"Error getting system status: {e}")
            return {
                'total_memory_mb': 0,
                'available_memory_mb': 0,
                'cpu_count': 0,
                'load_average': 0.0
            }

    def _get_benchmark_directory(self, benchmark_id: str) -> str:
        """Get the directory path for a benchmark"""
        # Convert S7BEN-HARD-018 to benchmarks/S7BEN-HARD-018
        import os
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_dir, '..', 'benchmarks', benchmark_id)

    def _get_container_name(self, benchmark_id: str) -> str:
        """Get standard container name for a benchmark"""
        # Docker-compose names containers as: <directory>-<service>-<number>
        # For S7BEN-EASY-001, this becomes: s7ben-easy-001-app-1
        return f"{benchmark_id.lower()}-app-1"

    def _benchmark_id_from_container_name(self, container_name: str) -> Optional[str]:
        """Extract benchmark ID from container name"""
        # Convert s7ben-easy-001-app-1 to S7BEN-EASY-001
        if container_name.startswith('s7ben-'):
            # Remove the -app-1 suffix
            parts = container_name.replace('-app-1', '').upper().split('-')
            if len(parts) >= 3:
                return '-'.join(parts[:3])
        return None

    def _is_container_running(self, container_name: str) -> bool:
        """Check if a specific container is running"""
        try:
            result = subprocess.run(
                ['docker', 'ps', '--filter', f'name={container_name}', '--format', '{{.Names}}'],
                capture_output=True,
                text=True
            )
            return container_name in result.stdout
        except Exception:
            return False

    def _get_container_stats(self, container_name: str) -> Dict:
        """Get resource stats for a container"""
        try:
            result = subprocess.run(
                ['docker', 'stats', '--no-stream', '--format',
                 '{{.MemUsage}}\t{{.CPUPerc}}', container_name],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                parts = result.stdout.strip().split('\t')
                if len(parts) >= 2:
                    # Parse memory (e.g., "128MiB / 512MiB")
                    mem_str = parts[0].split('/')[0].strip()
                    mem_mb = float(mem_str.replace('MiB', '').replace('GiB', '000').strip())

                    # Parse CPU (e.g., "2.5%")
                    cpu_str = parts[1].strip().replace('%', '')
                    cpu_percent = float(cpu_str)

                    return {
                        'memory_mb': round(mem_mb, 2),
                        'cpu_percent': round(cpu_percent, 2)
                    }
        except Exception:
            pass

        return {'memory_mb': 0, 'cpu_percent': 0}

    def check_timeouts(self) -> List[str]:
        """
        Check for containers that have exceeded timeout and stop them

        Returns:
            List of benchmark IDs that were stopped due to timeout
        """
        stopped = []
        now = datetime.now()

        for benchmark_id, info in list(self.running_containers.items()):
            auto_stop_at = datetime.fromisoformat(info['auto_stop_at'])
            if now >= auto_stop_at:
                result = self.stop_container(benchmark_id)
                if result['status'] == 'success':
                    stopped.append(benchmark_id)

        return stopped
