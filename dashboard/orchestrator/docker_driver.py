"""
Strike7 Docker Driver

Abstracts Docker/docker-compose operations behind a clean interface.
Supports two modes:
  - LocalDriver:  Runs docker-compose directly on the same machine
  - SSHDriver:    Runs docker-compose via SSH on a remote worker

The orchestrator service uses a driver instance — switching from local
to remote is purely a configuration change, no code changes needed.
"""

import subprocess
import shlex
import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("s7.orchestrator.docker_driver")


class DockerResult:
    """Standard result from a Docker operation."""

    def __init__(self, success: bool, stdout: str = "", stderr: str = "",
                 return_code: int = 0, error: str = None):
        self.success = success
        self.stdout = stdout
        self.stderr = stderr
        self.return_code = return_code
        self.error = error

    def to_dict(self):
        return {
            "success": self.success,
            "stdout": self.stdout[:500] if self.stdout else "",
            "stderr": self.stderr[:500] if self.stderr else "",
            "return_code": self.return_code,
            "error": self.error,
        }


class DockerDriver(ABC):
    """Abstract base class for Docker operations."""

    @abstractmethod
    def compose_up(self, project_dir: str, project_name: str = None,
                   detach: bool = True) -> DockerResult:
        """Start containers with docker-compose up."""
        pass

    @abstractmethod
    def compose_down(self, project_dir: str, project_name: str = None,
                     volumes: bool = False) -> DockerResult:
        """Stop and remove containers with docker-compose down."""
        pass

    @abstractmethod
    def compose_ps(self, project_dir: str, project_name: str = None) -> DockerResult:
        """List containers for a compose project."""
        pass

    @abstractmethod
    def container_inspect(self, container_name_or_id: str) -> DockerResult:
        """Inspect a running container."""
        pass

    @abstractmethod
    def container_list(self, filters: Dict = None, all_containers: bool = False) -> DockerResult:
        """List Docker containers with optional filters."""
        pass

    @abstractmethod
    def container_stop(self, container_name_or_id: str, timeout: int = 10) -> DockerResult:
        """Stop a specific container."""
        pass

    @abstractmethod
    def container_health(self, container_name_or_id: str) -> str:
        """Get container health status: 'healthy', 'unhealthy', 'starting', 'none', 'not_found'."""
        pass

    @abstractmethod
    def system_info(self) -> DockerResult:
        """Get Docker system info (for resource monitoring)."""
        pass

    @abstractmethod
    def image_exists(self, image_name: str) -> bool:
        """Check if a Docker image exists locally."""
        pass


class LocalDriver(DockerDriver):
    """
    Runs Docker commands directly on the local machine.
    Used in Phase 0 (single VPS) and for worker-local operations.
    """

    def __init__(self, compose_cmd: str = "docker-compose"):
        self.compose_cmd = compose_cmd
        logger.info(f"LocalDriver initialized with compose_cmd={compose_cmd}")

    def _run(self, cmd: List[str], cwd: str = None, timeout: int = 120) -> DockerResult:
        """Execute a command locally."""
        cmd_str = " ".join(cmd)
        logger.debug(f"Executing: {cmd_str} (cwd={cwd})")

        try:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            success = result.returncode == 0
            if not success:
                logger.warning(f"Command failed ({result.returncode}): {cmd_str}\n"
                                f"stderr: {result.stderr[:300]}")
            return DockerResult(
                success=success,
                stdout=result.stdout,
                stderr=result.stderr,
                return_code=result.returncode,
            )
        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out after {timeout}s: {cmd_str}")
            return DockerResult(success=False, error=f"Timeout after {timeout}s")
        except FileNotFoundError:
            logger.error(f"Command not found: {cmd[0]}")
            return DockerResult(success=False, error=f"Command not found: {cmd[0]}")
        except Exception as e:
            logger.error(f"Command failed: {cmd_str}: {e}")
            return DockerResult(success=False, error=str(e))

    def compose_up(self, project_dir: str, project_name: str = None,
                   detach: bool = True) -> DockerResult:
        cmd = [self.compose_cmd]
        if project_name:
            cmd.extend(["-p", project_name])
        cmd.append("up")
        if detach:
            cmd.append("-d")
        return self._run(cmd, cwd=project_dir, timeout=180)

    def compose_down(self, project_dir: str, project_name: str = None,
                     volumes: bool = False) -> DockerResult:
        cmd = [self.compose_cmd]
        if project_name:
            cmd.extend(["-p", project_name])
        cmd.append("down")
        if volumes:
            cmd.append("-v")
        return self._run(cmd, cwd=project_dir, timeout=60)

    def compose_ps(self, project_dir: str, project_name: str = None) -> DockerResult:
        cmd = [self.compose_cmd]
        if project_name:
            cmd.extend(["-p", project_name])
        cmd.append("ps")
        return self._run(cmd, cwd=project_dir)

    def container_inspect(self, container_name_or_id: str) -> DockerResult:
        cmd = ["docker", "inspect", container_name_or_id]
        return self._run(cmd)

    def container_list(self, filters: Dict = None, all_containers: bool = False) -> DockerResult:
        cmd = ["docker", "ps", "--format", "{{json .}}"]
        if all_containers:
            cmd.append("-a")
        if filters:
            for k, v in filters.items():
                cmd.extend(["--filter", f"{k}={v}"])
        return self._run(cmd)

    def container_stop(self, container_name_or_id: str, timeout: int = 10) -> DockerResult:
        cmd = ["docker", "stop", "-t", str(timeout), container_name_or_id]
        return self._run(cmd)

    def container_health(self, container_name_or_id: str) -> str:
        result = self._run([
            "docker", "inspect",
            "--format", "{{.State.Health.Status}}",
            container_name_or_id,
        ])
        if not result.success:
            if "No such" in (result.stderr or ""):
                return "not_found"
            return "unknown"
        status = result.stdout.strip()
        if status in ("healthy", "unhealthy", "starting"):
            return status
        # Container exists but has no healthcheck
        return "none"

    def system_info(self) -> DockerResult:
        """Get system resource info."""
        cmd = ["docker", "system", "df", "--format", "{{json .}}"]
        return self._run(cmd)

    def image_exists(self, image_name: str) -> bool:
        result = self._run(["docker", "image", "inspect", image_name])
        return result.success

    def get_running_containers(self) -> List[Dict]:
        """Parse running containers into structured data."""
        result = self.container_list()
        if not result.success:
            return []

        containers = []
        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                containers.append({
                    "id": data.get("ID", ""),
                    "name": data.get("Names", ""),
                    "image": data.get("Image", ""),
                    "status": data.get("Status", ""),
                    "ports": data.get("Ports", ""),
                    "created": data.get("CreatedAt", ""),
                })
            except json.JSONDecodeError:
                continue
        return containers

    def get_container_port(self, container_name: str) -> Optional[int]:
        """Get the host port mapped to a container."""
        result = self._run([
            "docker", "port", container_name,
        ])
        if not result.success:
            return None
        # Parse "5000/tcp -> 0.0.0.0:5005"
        for line in result.stdout.strip().split("\n"):
            if "->" in line:
                try:
                    host_part = line.split("->")[1].strip()
                    port = int(host_part.split(":")[-1])
                    return port
                except (ValueError, IndexError):
                    continue
        return None


class SSHDriver(DockerDriver):
    """
    Runs Docker commands on a remote worker via SSH.
    Used in Phase 1+ (control plane + worker node architecture).

    Requires SSH key-based auth to be configured (no password prompts).
    """

    def __init__(self, host: str, user: str = "root",
                 ssh_key: str = None, compose_cmd: str = "docker-compose",
                 benchmarks_dir: str = "/opt/strike7.ai-benchmark-harness/benchmarks"):
        self.host = host
        self.user = user
        self.ssh_key = ssh_key
        self.compose_cmd = compose_cmd
        self.benchmarks_dir = benchmarks_dir

        self._ssh_base = ["ssh", "-o", "StrictHostKeyChecking=no",
                          "-o", "ConnectTimeout=10"]
        if ssh_key:
            self._ssh_base.extend(["-i", ssh_key])
        self._ssh_base.append(f"{user}@{host}")

        logger.info(f"SSHDriver initialized: {user}@{host}")

    def _run_remote(self, cmd_str: str, timeout: int = 120) -> DockerResult:
        """Execute a command on the remote worker via SSH."""
        full_cmd = self._ssh_base + [cmd_str]
        logger.debug(f"SSH execute on {self.host}: {cmd_str}")

        try:
            result = subprocess.run(
                full_cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            success = result.returncode == 0
            if not success:
                logger.warning(f"SSH command failed ({result.returncode}) on {self.host}: "
                                f"{cmd_str[:100]}\nstderr: {result.stderr[:300]}")
            return DockerResult(
                success=success,
                stdout=result.stdout,
                stderr=result.stderr,
                return_code=result.returncode,
            )
        except subprocess.TimeoutExpired:
            logger.error(f"SSH command timed out after {timeout}s on {self.host}")
            return DockerResult(success=False, error=f"SSH timeout after {timeout}s")
        except Exception as e:
            logger.error(f"SSH command failed on {self.host}: {e}")
            return DockerResult(success=False, error=str(e))

    def compose_up(self, project_dir: str, project_name: str = None,
                   detach: bool = True) -> DockerResult:
        cmd = f"cd {shlex.quote(project_dir)} && {self.compose_cmd}"
        if project_name:
            cmd += f" -p {shlex.quote(project_name)}"
        cmd += " up"
        if detach:
            cmd += " -d"
        return self._run_remote(cmd, timeout=180)

    def compose_down(self, project_dir: str, project_name: str = None,
                     volumes: bool = False) -> DockerResult:
        cmd = f"cd {shlex.quote(project_dir)} && {self.compose_cmd}"
        if project_name:
            cmd += f" -p {shlex.quote(project_name)}"
        cmd += " down"
        if volumes:
            cmd += " -v"
        return self._run_remote(cmd, timeout=60)

    def compose_ps(self, project_dir: str, project_name: str = None) -> DockerResult:
        cmd = f"cd {shlex.quote(project_dir)} && {self.compose_cmd}"
        if project_name:
            cmd += f" -p {shlex.quote(project_name)}"
        cmd += " ps"
        return self._run_remote(cmd)

    def container_inspect(self, container_name_or_id: str) -> DockerResult:
        return self._run_remote(f"docker inspect {shlex.quote(container_name_or_id)}")

    def container_list(self, filters: Dict = None, all_containers: bool = False) -> DockerResult:
        cmd = 'docker ps --format "{{json .}}"'
        if all_containers:
            cmd += " -a"
        if filters:
            for k, v in filters.items():
                cmd += f" --filter {shlex.quote(f'{k}={v}')}"
        return self._run_remote(cmd)

    def container_stop(self, container_name_or_id: str, timeout: int = 10) -> DockerResult:
        return self._run_remote(
            f"docker stop -t {timeout} {shlex.quote(container_name_or_id)}"
        )

    def container_health(self, container_name_or_id: str) -> str:
        result = self._run_remote(
            f'docker inspect --format "{{{{.State.Health.Status}}}}" '
            f'{shlex.quote(container_name_or_id)}'
        )
        if not result.success:
            return "not_found" if "No such" in (result.stderr or "") else "unknown"
        status = result.stdout.strip()
        return status if status in ("healthy", "unhealthy", "starting") else "none"

    def system_info(self) -> DockerResult:
        return self._run_remote('docker system df --format "{{json .}}"')

    def image_exists(self, image_name: str) -> bool:
        result = self._run_remote(f"docker image inspect {shlex.quote(image_name)}")
        return result.success

    def ping(self) -> bool:
        """Check SSH connectivity to the worker."""
        result = self._run_remote("echo pong", timeout=10)
        return result.success and "pong" in result.stdout


def create_driver(worker_config: Dict, compose_cmd: str = "docker-compose",
                  benchmarks_dir: str = None) -> DockerDriver:
    """
    Factory function: create the appropriate driver based on worker config.

    worker_config example (local):
      {"id": "local", "mode": "local", "host": "localhost"}

    worker_config example (remote):
      {"id": "worker-1", "mode": "remote", "host": "10.0.0.2",
       "ssh_user": "root", "ssh_key": "/root/.ssh/worker1_key"}
    """
    mode = worker_config.get("mode", "local")

    if mode == "local":
        return LocalDriver(compose_cmd=compose_cmd)
    elif mode in ("remote", "ssh"):
        return SSHDriver(
            host=worker_config["host"],
            user=worker_config.get("ssh_user", "root"),
            ssh_key=worker_config.get("ssh_key"),
            compose_cmd=compose_cmd,
            benchmarks_dir=benchmarks_dir or "/opt/strike7.ai-benchmark-harness/benchmarks",
        )
    else:
        raise ValueError(f"Unknown driver mode: {mode}")
