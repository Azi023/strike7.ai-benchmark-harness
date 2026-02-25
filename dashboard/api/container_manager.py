"""
Container Management Module
Handles Docker container lifecycle, status monitoring, and safety enforcement
"""

import subprocess
import json
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple


class ContainerManager:
    """Manages benchmark Docker containers with safety controls"""

    # Tier-based startup timeouts (seconds) for docker-compose up --build.
    # Heavy benchmarks (multi-container AD, source compilation) need much more
    # time than simple single-container Flask apps.
    TIER_TIMEOUTS = {
        'EASY': 60,
        'MED': 60,
        'HARD': 120,
        'VHARD': 300,
        'CVE': 300,
    }
    DEFAULT_STARTUP_TIMEOUT = 120  # fallback for unknown tiers

    def __init__(self, benchmarks: list, config: Dict = None):
        """
        Initialize container manager

        Args:
            benchmarks: List of benchmark configurations
            config: Optional configuration dict with safety settings
        """
        self.benchmarks = {b['id']: b for b in benchmarks}
        self.project_to_benchmark = {b['id'].lower(): b['id'] for b in benchmarks}
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

    @staticmethod
    def _extract_tier(benchmark_id: str) -> Optional[str]:
        """
        Extract the tier from a benchmark ID.

        Examples:
            'S7BEN-EASY-001' -> 'EASY'
            'S7BEN-VHARD-003' -> 'VHARD'
            'S7BEN-CVE-012'  -> 'CVE'
            'unknown'        -> None
        """
        if not benchmark_id or not benchmark_id.startswith('S7BEN-'):
            return None
        parts = benchmark_id.split('-')
        if len(parts) >= 3:
            return parts[1].upper()
        return None

    def _get_startup_timeout(self, benchmark_id: str) -> int:
        """
        Get the subprocess timeout (seconds) for docker-compose up based on
        the benchmark's tier.
        """
        tier = self._extract_tier(benchmark_id)
        return self.TIER_TIMEOUTS.get(tier, self.DEFAULT_STARTUP_TIMEOUT)

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

        # Get benchmark directory and compose project name
        benchmark_dir = self._get_benchmark_directory(benchmark_id)
        compose_project = self._get_compose_project_name(benchmark_id)

        # Check if benchmark already running BEFORE concurrent limit check
        # (re-starting an already-running benchmark should always succeed)
        if self._is_benchmark_running(benchmark_id):
            return {
                'status': 'success',
                'message': 'Container already running',
                'benchmark_id': benchmark_id,
                'container_name': compose_project,
                'port': benchmark.get('port'),
                'already_running': True
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

        # Start container using docker-compose
        startup_timeout = self._get_startup_timeout(benchmark_id)
        tier = self._extract_tier(benchmark_id) or 'UNKNOWN'
        if startup_timeout > 120:
            print(f"[INFO] Starting {tier} benchmark {benchmark_id} "
                  f"— extended timeout of {startup_timeout}s")

        try:
            result = subprocess.run(
                ['docker-compose', 'up', '-d', '--build'],
                cwd=benchmark_dir,
                capture_output=True,
                text=True,
                timeout=startup_timeout
            )

            if result.returncode != 0:
                return {
                    'status': 'error',
                    'message': 'Failed to start container',
                    'error': result.stderr,
                    'benchmark_id': benchmark_id
                }

            # Calculate auto-stop time using UTC to avoid timezone skew
            timeout = timeout_minutes or self.config['timeout_minutes']
            now_utc = datetime.now(timezone.utc)
            auto_stop_at = now_utc + timedelta(minutes=timeout)

            # Track running container
            container_info = {
                'benchmark_id': benchmark_id,
                'container_name': compose_project,
                'port': benchmark.get('port'),
                # Use ISO 8601 with milliseconds and UTC offset to ensure
                # consistent parsing in browsers and backend.
                'started_at': now_utc.isoformat(timespec='milliseconds'),
                'auto_stop_at': auto_stop_at.isoformat(timespec='milliseconds'),
                'timeout_minutes': timeout
            }
            self.running_containers[benchmark_id] = container_info

            return {
                'status': 'success',
                'benchmark_id': benchmark_id,
                'container_name': compose_project,
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

        benchmark_dir = self._get_benchmark_directory(benchmark_id)

        # Check if benchmark is running (project-scoped)
        if not self._is_benchmark_running(benchmark_id):
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
                timeout=60
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
                # Backward compatibility: if stored timestamp is naive, assume UTC
                if started_at.tzinfo is None:
                    started_at = started_at.replace(tzinfo=timezone.utc)
                now_utc = datetime.now(timezone.utc)
                runtime_seconds = (now_utc - started_at).total_seconds()
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
                # Aggregate per benchmark (not per container)
                by_benchmark = {}

                for line in result.stdout.strip().split('\n'):
                    if not line:
                        continue
                    try:
                        container = json.loads(line)
                        container_name = container.get('Names', '')
                        labels = container.get('Labels', '')

                        # First choice: compose project label; fallback to name parsing
                        benchmark_id = self._benchmark_id_from_labels(labels)
                        if not benchmark_id:
                            benchmark_id = self._benchmark_id_from_container_name(container_name)

                        if benchmark_id:
                            # Get additional stats
                            stats = self._get_container_stats(container_name)

                            # Parse health status from Status field
                            status_text = container.get('Status', '')
                            health_status = self._parse_health_status(status_text)

                            container_info = {
                                'benchmark_id': benchmark_id,
                                'container_name': container_name,
                                'status': status_text,
                                'health_status': health_status,
                                'port': self.benchmarks.get(benchmark_id, {}).get('port'),
                                'memory_mb': stats.get('memory_mb', 0),
                                'cpu_percent': stats.get('cpu_percent', 0)
                            }

                            # Add tracking info if available
                            if benchmark_id in self.running_containers:
                                tracked = self.running_containers[benchmark_id]
                                container_info['started_at'] = tracked['started_at']
                                started = datetime.fromisoformat(tracked['started_at'])
                                # Backward compatibility for older naive timestamps
                                if started.tzinfo is None:
                                    started = started.replace(tzinfo=timezone.utc)
                                now_utc = datetime.now(timezone.utc)
                                container_info['runtime_seconds'] = (
                                    now_utc - started
                                ).total_seconds()

                            # Keep one status object per benchmark. Prefer a container that
                            # has the mapped benchmark port and a more stable health state.
                            existing = by_benchmark.get(benchmark_id)
                            if not existing:
                                container_info['service_count'] = 1
                                by_benchmark[benchmark_id] = container_info
                            else:
                                existing['service_count'] = existing.get('service_count', 1) + 1
                                existing['memory_mb'] = round(existing.get('memory_mb', 0) + container_info.get('memory_mb', 0), 2)
                                existing['cpu_percent'] = round(existing.get('cpu_percent', 0) + container_info.get('cpu_percent', 0), 2)

                                merged_health = self._merge_health_status(
                                    existing.get('health_status', 'unknown'),
                                    container_info.get('health_status', 'unknown')
                                )
                                existing['health_status'] = merged_health

                    except json.JSONDecodeError:
                        continue

                containers.extend(by_benchmark.values())

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
        """Get the absolute directory path for a benchmark"""
        # Convert S7BEN-HARD-018 to /absolute/path/benchmarks/S7BEN-HARD-018
        import os
        # Get absolute path to dashboard directory (dashboard/)
        dashboard_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # Go up one level to project root, then into benchmarks
        project_root = os.path.dirname(dashboard_dir)
        benchmark_dir = os.path.join(project_root, 'benchmarks', benchmark_id)
        return os.path.abspath(benchmark_dir)  # Ensure absolute path

    def _get_container_name(self, benchmark_id: str) -> str:
        """Get standard container name for a benchmark"""
        # Docker-compose names containers as: <directory>_<service>_<number>
        # For S7BEN-EASY-001, this becomes: s7ben-easy-001_app_1 (note underscore before app)
        return f"{benchmark_id.lower()}_app_1"

    def _get_compose_project_name(self, benchmark_id: str) -> str:
        """Docker Compose default project name for a benchmark directory."""
        return benchmark_id.lower()

    def _benchmark_id_from_container_name(self, container_name: str) -> Optional[str]:
        """Extract benchmark ID from container name"""
        # Convert s7ben-easy-001_app_1 or s7ben-easy-001-app-1 to S7BEN-EASY-001
        if container_name.startswith('s7ben-'):
            # Remove the _app_1 or -app-1 suffix (docker-compose uses underscore)
            cleaned = container_name.replace('_app_1', '').replace('-app-1', '')
            parts = cleaned.upper().split('-')
            if len(parts) >= 3:
                candidate = '-'.join(parts[:3])
                if candidate in self.benchmarks:
                    return candidate
        return None

    def _benchmark_id_from_labels(self, labels: str) -> Optional[str]:
        """Extract benchmark ID from docker compose labels."""
        if not labels:
            return None

        project = None
        for label in labels.split(','):
            label = label.strip()
            if label.startswith('com.docker.compose.project='):
                project = label.split('=', 1)[1]
                break

        if not project:
            return None

        return self.project_to_benchmark.get(project.lower())

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

    def _is_benchmark_running(self, benchmark_id: str) -> bool:
        """Check whether any running container belongs to the benchmark compose project."""
        project = self._get_compose_project_name(benchmark_id)
        try:
            result = subprocess.run(
                ['docker', 'ps', '--filter', f'label=com.docker.compose.project={project}', '--format', '{{.Names}}'],
                capture_output=True,
                text=True
            )
            return bool(result.stdout.strip())
        except Exception:
            return False

    def _merge_health_status(self, a: str, b: str) -> str:
        """Merge health statuses across multiple service containers for one benchmark."""
        rank = {
            'unhealthy': 4,
            'starting': 3,
            'unknown': 2,
            'none': 1,
            'healthy': 0
        }
        return a if rank.get(a, 2) >= rank.get(b, 2) else b

    def _parse_health_status(self, status_text: str) -> str:
        """
        Parse health status from Docker status string

        Examples:
            "Up 2 minutes (healthy)" -> "healthy"
            "Up 2 minutes (unhealthy)" -> "unhealthy"
            "Up 2 minutes" -> "none"  # No health check configured
            "Up 39 seconds (health: starting)" -> "starting"

        Returns:
            One of: "healthy", "unhealthy", "starting", "none", "unknown"
        """
        import re

        if not status_text:
            return "unknown"

        # Check for explicit health status in parentheses
        health_match = re.search(r'\(([^)]*health[^)]*)\)', status_text, re.IGNORECASE)
        if health_match:
            health_text = health_match.group(1).lower()

            if 'unhealthy' in health_text:
                return "unhealthy"
            elif 'starting' in health_text or 'health: starting' in health_text:
                return "starting"
            elif 'healthy' in health_text:
                return "healthy"

        # No health check configured or status not available
        return "none"

    def read_runtime_flag(self, benchmark_id: str) -> Optional[str]:
        """
        Try to read the dynamic FLAG from a running benchmark container.

        Per-container probe order:
          1. printenv FLAG
          2. printenv S7BEN_FLAG
          3. python3 -c "import os; print(os.environ.get('FLAG',''))"
          4. cat /tmp/flag.txt
          5. cat /flag.txt
          6. cat /app/flag.txt
          7. cat /var/www/flag.txt

        Container discovery:
          - All containers in the compose project (via label filter)
          - Conventional name fallbacks: _app_1, -app-1, _web_1, -web-1, etc.

        Returns the flag string (e.g. "S7BEN{...}") or None if not found.
        Benchmarks where the flag is a Python module-level variable (not in env
        or on disk) cannot be captured here; tier-2 YAML pattern matching is
        used for those instead.
        """
        project = self._get_compose_project_name(benchmark_id)

        # ── Discover running containers for this benchmark ───────────────────
        container_candidates: List[str] = []
        try:
            result = subprocess.run(
                ['docker', 'ps',
                 '--filter', f'label=com.docker.compose.project={project}',
                 '--format', '{{.Names}}'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                for name in result.stdout.strip().split('\n'):
                    name = name.strip()
                    if name:
                        container_candidates.append(name)
        except Exception:
            pass

        # Conventional fallback names when label lookup returns nothing
        suffixes = ['_app_1', '-app-1', '_app', '_web_1', '-web-1',
                    '_flask_1', '-flask-1', '_server_1', '-server-1']
        seen = set(container_candidates)
        for suffix in suffixes:
            candidate = f"{project}{suffix}"
            if candidate not in seen:
                container_candidates.append(candidate)
                seen.add(candidate)

        # ── Probe each container with multiple methods ───────────────────────
        flag_files = ['/tmp/flag.txt', '/flag.txt', '/app/flag.txt', '/var/www/flag.txt']

        for container_name in container_candidates:
            flag = self._probe_container_for_flag(container_name, flag_files)
            if flag:
                print(f"[FLAG] Captured runtime flag for {benchmark_id} "
                      f"from container {container_name}")
                return flag

        # ── Last resort: docker-compose exec ────────────────────────────────
        try:
            benchmark_dir = self._get_benchmark_directory(benchmark_id)
            result = subprocess.run(
                ['docker-compose', 'exec', '-T', 'app', 'printenv', 'FLAG'],
                capture_output=True, text=True, timeout=5, cwd=benchmark_dir
            )
            if result.returncode == 0:
                flag = result.stdout.strip()
                if flag.startswith('S7BEN{'):
                    print(f"[FLAG] Captured runtime flag for {benchmark_id} "
                          f"via docker-compose exec")
                    return flag
        except Exception:
            pass

        print(f"[FLAG] WARNING: Could not capture dynamic flag for {benchmark_id} "
              f"-- YAML pattern fallback will be used for validation")
        return None

    def _probe_container_for_flag(self, container_name: str,
                                  flag_files: List[str]) -> Optional[str]:
        """
        Try every known method to extract a S7BEN{...} flag from one container.
        Returns the flag string, or None if nothing matched.
        """
        # Method 1: printenv FLAG
        flag = self._exec_and_extract(container_name, ['printenv', 'FLAG'])
        if flag:
            return flag

        # Method 2: printenv S7BEN_FLAG
        flag = self._exec_and_extract(container_name, ['printenv', 'S7BEN_FLAG'])
        if flag:
            return flag

        # Method 3: python3 os.environ (some containers set FLAG in a subprocess
        # environment rather than the top-level env, but it's still readable this way)
        flag = self._exec_and_extract(
            container_name,
            ['python3', '-c', "import os; print(os.environ.get('FLAG',''))"]
        )
        if flag:
            return flag

        # Method 4–6: flag files on disk
        for path in flag_files:
            flag = self._exec_and_extract(container_name, ['cat', path])
            if flag:
                return flag

        return None

    def _exec_and_extract(self, container_name: str,
                          cmd: List[str]) -> Optional[str]:
        """
        Run `docker exec <container_name> <cmd>` and return the output if it
        starts with 'S7BEN{', otherwise return None.
        """
        try:
            result = subprocess.run(
                ['docker', 'exec', container_name] + cmd,
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                flag = result.stdout.strip()
                if flag.startswith('S7BEN{'):
                    return flag
        except Exception:
            pass
        return None

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
        now = datetime.now(timezone.utc)

        for benchmark_id, info in list(self.running_containers.items()):
            auto_stop_at = datetime.fromisoformat(info['auto_stop_at'])
            if auto_stop_at.tzinfo is None:
                auto_stop_at = auto_stop_at.replace(tzinfo=timezone.utc)
            if now >= auto_stop_at:
                result = self.stop_container(benchmark_id)
                if result['status'] == 'success':
                    stopped.append(benchmark_id)

        return stopped
