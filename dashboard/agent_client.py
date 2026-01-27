#!/usr/bin/env python3
"""
Strike7 Agent Client Library
Python client for AI agents to interact with Strike7 Dashboard API
"""

import requests
from typing import Dict, List, Optional
import time


class Strike7Client:
    """
    Client library for AI agents to interact with Strike7 benchmarks

    Example usage:
        client = Strike7Client()
        session_id = client.start_session("my-agent")

        # Start a benchmark
        result = client.start_benchmark("S7BEN-HARD-018")
        port = result['port']

        # Exploit the benchmark...
        # flag = exploit_benchmark(port)

        # Submit the flag
        result = client.submit_flag("S7BEN-HARD-018", flag)
        if result['correct']:
            print("Flag accepted!")

        # Stop the benchmark
        client.stop_benchmark("S7BEN-HARD-018")

        # Get final progress
        progress = client.get_progress()
    """

    def __init__(self, base_url: str = "http://localhost:5500"):
        """
        Initialize Strike7 client

        Args:
            base_url: Base URL of the Strike7 dashboard API
        """
        self.base_url = base_url.rstrip('/')
        self.session_id = None
        self.agent_id = None
        self.session = requests.Session()  # Reuse connection

    def start_session(self, agent_id: str, benchmark_filter: Dict = None,
                     settings: Dict = None) -> str:
        """
        Start a new evaluation session

        Args:
            agent_id: Identifier for your AI agent
            benchmark_filter: Optional filter (e.g., {"categories": ["HARD"]})
            settings: Optional settings (e.g., {"max_concurrent_containers": 1})

        Returns:
            Session ID string

        Raises:
            RuntimeError: If session creation fails
        """
        payload = {
            "agent_id": agent_id,
            "benchmark_filter": benchmark_filter or {},
            "settings": settings or {"max_concurrent_containers": 1}
        }

        try:
            resp = self.session.post(
                f"{self.base_url}/api/session/start",
                json=payload,
                timeout=10
            )
            resp.raise_for_status()
            data = resp.json()

            if data.get('status') == 'success':
                self.session_id = data['session_id']
                self.agent_id = agent_id
                return self.session_id
            else:
                raise RuntimeError(f"Session start failed: {data.get('message')}")

        except requests.RequestException as e:
            raise RuntimeError(f"Failed to start session: {e}")

    def get_benchmarks(self, category: str = None, owasp: str = None,
                      difficulty: int = None) -> List[Dict]:
        """
        Get list of available benchmarks

        Args:
            category: Filter by category (EASY, MED, HARD, VHARD, CVE)
            owasp: Filter by OWASP code (e.g., "A01", "A03")
            difficulty: Filter by difficulty level (1-9)

        Returns:
            List of benchmark dictionaries
        """
        params = {}
        if category:
            params['category'] = category
        if owasp:
            params['owasp'] = owasp
        if difficulty:
            params['difficulty'] = difficulty

        try:
            resp = self.session.get(
                f"{self.base_url}/api/benchmarks",
                params=params,
                timeout=10
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get('benchmarks', [])

        except requests.RequestException as e:
            raise RuntimeError(f"Failed to get benchmarks: {e}")

    def start_benchmark(self, benchmark_id: str, force_stop_others: bool = True,
                       timeout_minutes: int = None) -> Dict:
        """
        Start a benchmark container

        Args:
            benchmark_id: Benchmark ID (e.g., "S7BEN-HARD-018")
            force_stop_others: Stop other running containers first
            timeout_minutes: Auto-stop timeout (default: 30)

        Returns:
            Dict with container info including port number

        Raises:
            RuntimeError: If container start fails
        """
        payload = {
            "force_stop_others": force_stop_others
        }
        if timeout_minutes:
            payload["timeout_minutes"] = timeout_minutes

        try:
            resp = self.session.post(
                f"{self.base_url}/api/benchmark/{benchmark_id}/start",
                json=payload,
                timeout=30
            )
            resp.raise_for_status()
            data = resp.json()

            if data.get('status') != 'success':
                raise RuntimeError(f"Failed to start: {data.get('message')}")

            return data

        except requests.RequestException as e:
            raise RuntimeError(f"Failed to start benchmark: {e}")

    def stop_benchmark(self, benchmark_id: str) -> Dict:
        """
        Stop a benchmark container

        Args:
            benchmark_id: Benchmark ID

        Returns:
            Dict with stop result

        Raises:
            RuntimeError: If container stop fails
        """
        try:
            resp = self.session.post(
                f"{self.base_url}/api/benchmark/{benchmark_id}/stop",
                timeout=30
            )
            resp.raise_for_status()
            return resp.json()

        except requests.RequestException as e:
            raise RuntimeError(f"Failed to stop benchmark: {e}")

    def submit_flag(self, benchmark_id: str, flag: str) -> Dict:
        """
        Submit a captured flag for validation

        Args:
            benchmark_id: Benchmark ID
            flag: The captured flag string

        Returns:
            Dict with validation result (includes 'correct' boolean)

        Example:
            result = client.submit_flag("S7BEN-HARD-018", "S7BEN{k8s_escape}")
            if result['correct']:
                print(f"Success! Time: {result.get('time_to_capture')}s")
            else:
                print(f"Wrong flag. Attempts: {result['attempts']}")
        """
        payload = {
            "flag": flag,
            "session_id": self.session_id,
            "agent_id": self.agent_id
        }

        try:
            resp = self.session.post(
                f"{self.base_url}/api/benchmark/{benchmark_id}/submit-flag",
                json=payload,
                timeout=10
            )
            resp.raise_for_status()
            return resp.json()

        except requests.RequestException as e:
            raise RuntimeError(f"Failed to submit flag: {e}")

    def get_benchmark_status(self, benchmark_id: str) -> Dict:
        """
        Get status of a specific benchmark

        Args:
            benchmark_id: Benchmark ID

        Returns:
            Dict with benchmark status
        """
        try:
            resp = self.session.get(
                f"{self.base_url}/api/benchmark/{benchmark_id}/status",
                timeout=10
            )
            resp.raise_for_status()
            return resp.json()

        except requests.RequestException as e:
            raise RuntimeError(f"Failed to get benchmark status: {e}")

    def get_containers_status(self) -> Dict:
        """
        Get status of all running containers

        Returns:
            Dict with running containers and system info
        """
        try:
            resp = self.session.get(
                f"{self.base_url}/api/containers/status",
                timeout=10
            )
            resp.raise_for_status()
            return resp.json()

        except requests.RequestException as e:
            raise RuntimeError(f"Failed to get containers status: {e}")

    def stop_all_containers(self) -> Dict:
        """
        Emergency stop all running containers

        Returns:
            Dict with list of stopped containers
        """
        try:
            resp = self.session.post(
                f"{self.base_url}/api/containers/stop-all",
                timeout=30
            )
            resp.raise_for_status()
            return resp.json()

        except requests.RequestException as e:
            raise RuntimeError(f"Failed to stop all containers: {e}")

    def get_progress(self) -> Dict:
        """
        Get current session progress

        Returns:
            Dict with session progress and statistics

        Raises:
            RuntimeError: If no active session
        """
        if not self.session_id:
            raise RuntimeError("No active session. Call start_session() first.")

        try:
            resp = self.session.get(
                f"{self.base_url}/api/session/{self.session_id}/progress",
                timeout=10
            )
            resp.raise_for_status()
            return resp.json()

        except requests.RequestException as e:
            raise RuntimeError(f"Failed to get progress: {e}")

    def end_session(self) -> Dict:
        """
        End the current evaluation session

        Returns:
            Dict with final session summary
        """
        if not self.session_id:
            raise RuntimeError("No active session")

        try:
            resp = self.session.post(
                f"{self.base_url}/api/session/{self.session_id}/end",
                timeout=10
            )
            resp.raise_for_status()
            data = resp.json()

            self.session_id = None
            return data

        except requests.RequestException as e:
            raise RuntimeError(f"Failed to end session: {e}")

    def wait_for_container(self, benchmark_id: str, timeout: int = 30) -> bool:
        """
        Wait for container to be fully started and ready

        Args:
            benchmark_id: Benchmark ID
            timeout: Maximum wait time in seconds

        Returns:
            True if container is ready, False if timeout
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                status = self.get_benchmark_status(benchmark_id)
                if status.get('running'):
                    # Give it a few extra seconds to fully initialize
                    time.sleep(3)
                    return True
            except:
                pass

            time.sleep(2)

        return False

    # Convenience methods

    def run_benchmark(self, benchmark_id: str, exploit_function,
                     stop_on_success: bool = True) -> Dict:
        """
        High-level method to run a complete benchmark workflow

        Args:
            benchmark_id: Benchmark ID
            exploit_function: Callable that takes port number and returns flag
            stop_on_success: Stop container after successful flag capture

        Returns:
            Dict with result including 'success' boolean

        Example:
            def my_exploit(port):
                # Your exploit code here
                response = requests.get(f"http://localhost:{port}/exploit")
                return response.text  # Return the flag

            result = client.run_benchmark("S7BEN-HARD-018", my_exploit)
            if result['success']:
                print(f"Solved in {result['time']}s!")
        """
        try:
            # Start container
            start_result = self.start_benchmark(benchmark_id)
            port = start_result['port']

            # Wait for container to be ready
            if not self.wait_for_container(benchmark_id, timeout=30):
                return {
                    'success': False,
                    'error': 'Container failed to start',
                    'benchmark_id': benchmark_id
                }

            # Run exploit
            flag = exploit_function(port)

            # Submit flag
            submit_result = self.submit_flag(benchmark_id, flag)
            success = submit_result.get('correct', False)

            # Stop container if successful and requested
            if success and stop_on_success:
                self.stop_benchmark(benchmark_id)

            return {
                'success': success,
                'benchmark_id': benchmark_id,
                'flag': flag,
                'attempts': submit_result.get('attempts'),
                'time': submit_result.get('time_to_capture'),
                'message': submit_result.get('message')
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'benchmark_id': benchmark_id
            }


# Example usage
if __name__ == '__main__':
    # Initialize client
    client = Strike7Client()

    # Start session
    session_id = client.start_session("example-agent")
    print(f"Started session: {session_id}")

    # Get available benchmarks
    hard_benchmarks = client.get_benchmarks(category="HARD")
    print(f"Found {len(hard_benchmarks)} HARD benchmarks")

    # Example: Start a specific benchmark
    benchmark_id = "S7BEN-HARD-018"
    print(f"\nStarting {benchmark_id}...")

    try:
        result = client.start_benchmark(benchmark_id)
        print(f"Container started on port {result['port']}")

        # Your exploit code would go here
        # flag = exploit_benchmark(result['port'])

        # For demo, just try a dummy flag
        flag = "S7BEN{example_flag}"
        submit_result = client.submit_flag(benchmark_id, flag)

        if submit_result['correct']:
            print("Flag accepted!")
        else:
            print(f"Wrong flag. Attempts: {submit_result['attempts']}")

        # Stop the container
        client.stop_benchmark(benchmark_id)
        print("Container stopped")

    except Exception as e:
        print(f"Error: {e}")

    # Get progress
    progress = client.get_progress()
    print(f"\nSession progress:")
    print(f"  Attempted: {progress['stats']['benchmarks_attempted']}")
    print(f"  Solved: {progress['stats']['benchmarks_solved']}")

    # End session
    final = client.end_session()
    print(f"\nSession ended. Total time: {final['duration_seconds']}s")
