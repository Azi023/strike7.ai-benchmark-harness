"""
Strike7 Orchestrator Service

The central service that manages the benchmark container lifecycle.
All Docker operations go through this service — the dashboard and MCP
gateway call the orchestrator, never Docker directly.

Key responsibilities:
  - Provision: Start a benchmark on the best available worker
  - Deprovision: Stop and clean up a benchmark
  - Status: Report on running benchmarks across all workers
  - Health: Monitor container health and auto-recover
  - Timeout: Auto-stop benchmarks that exceed their time limit
"""

import os
import json
import threading
import time
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from .config import OrchestratorConfig
from .docker_driver import DockerDriver, LocalDriver, SSHDriver, create_driver
from .port_pool import PortPool
from .run_tracker import RunTracker
from .session_manager import SessionManager

logger = logging.getLogger("s7.orchestrator.service")


# ── Benchmark registry helpers ──────────────────────────────────────────

def _extract_tier(benchmark_id: str) -> str:
    """Extract difficulty tier from benchmark ID.  S7BEN-EASY-001 → EASY"""
    parts = benchmark_id.split("-")
    if len(parts) >= 2:
        return parts[1].upper()
    return "DEFAULT"


def _get_benchmark_dir(benchmarks_base: str, benchmark_id: str) -> Optional[str]:
    """Resolve the benchmark directory path."""
    path = os.path.join(benchmarks_base, benchmark_id)
    if os.path.isdir(path):
        return path
    # Fallback: case-insensitive search
    if os.path.isdir(benchmarks_base):
        for entry in os.listdir(benchmarks_base):
            if entry.upper() == benchmark_id.upper():
                return os.path.join(benchmarks_base, entry)
    return None


# ── Worker state ────────────────────────────────────────────────────────

class WorkerState:
    """Tracks the state of a single worker node."""

    def __init__(self, worker_config: Dict, driver: DockerDriver):
        self.id = worker_config["id"]
        self.config = worker_config
        self.driver = driver
        self.healthy = True
        self.last_health_check = None
        self.consecutive_failures = 0
        self.port_range = tuple(worker_config.get("port_range", [5001, 5299]))
        self.max_containers = worker_config.get("max_containers", 15)


# ── Main Orchestrator ───────────────────────────────────────────────────

class OrchestratorService:
    """
    The orchestrator manages all benchmark container lifecycle operations.

    Usage:
        config = OrchestratorConfig()
        orch = OrchestratorService(config)
        orch.start()  # Starts background threads

        # Provision a benchmark
        result = orch.provision("S7BEN-EASY-001")

        # Check status
        status = orch.status("S7BEN-EASY-001")

        # Deprovision
        orch.deprovision("S7BEN-EASY-001")
    """

    def __init__(self, config: OrchestratorConfig):
        self.config = config
        self._running = False

        # Initialize database path
        db_dir = os.path.dirname(config.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        db_path = config.db_path
        if not os.path.isabs(db_path):
            # Resolve relative to the dashboard directory
            base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(base, db_path)
            if not os.path.exists(os.path.dirname(db_path)):
                os.makedirs(os.path.dirname(db_path), exist_ok=True)

        # Initialize sub-systems
        self.port_pool = PortPool(
            db_path=db_path,
            default_start=config.port_pool_start,
            default_end=config.port_pool_end,
            reserved=config.reserved_ports,
        )
        self.sessions = SessionManager(db_path=db_path)
        self.sessions.cleanup_orphaned()

        # Run tracker: bridges orchestrator sessions to comparison DB
        comparison_db = os.path.join(os.path.dirname(db_path), "model_benchmarks.db")
        self.run_tracker = RunTracker(db_path=comparison_db)

        # Initialize workers
        self.workers: Dict[str, WorkerState] = {}
        for wc in config.workers:
            driver = create_driver(
                wc,
                compose_cmd=config.docker_compose_cmd,
                benchmarks_dir=config.benchmarks_dir,
            )
            self.workers[wc["id"]] = WorkerState(wc, driver)

        # Background threads
        self._timeout_thread = None
        self._health_thread = None
        self._reconcile_thread = None

        logger.info(f"OrchestratorService initialized with {len(self.workers)} worker(s)")

    # ── Lifecycle ────────────────────────────────────────────────────────

    def start(self):
        """Start background daemon threads."""
        self._running = True

        # Timeout daemon: checks for expired sessions every 30s
        self._timeout_thread = threading.Thread(
            target=self._timeout_loop, daemon=True, name="s7-timeout-daemon"
        )
        self._timeout_thread.start()

        # Health monitor: checks worker/container health
        self._health_thread = threading.Thread(
            target=self._health_loop, daemon=True, name="s7-health-monitor"
        )
        self._health_thread.start()

        # Reconciliation: syncs DB state with actual Docker state
        self._reconcile_thread = threading.Thread(
            target=self._reconcile_loop, daemon=True, name="s7-reconciler"
        )
        self._reconcile_thread.start()

        logger.info("Orchestrator background daemons started")

    def stop(self):
        """Stop background threads."""
        self._running = False
        logger.info("Orchestrator stopping...")

    # ── Core Operations ──────────────────────────────────────────────────

    def provision(self, benchmark_id: str, agent_id: str = None,
                  force_stop_others: bool = True,
                  preferred_port: int = None,
                  timeout_override: int = None,
                  model_name: str = None,
                  provider: str = None,
                  product: str = None) -> Dict:
        """
        Provision (start) a benchmark.

        1. Check if already running
        2. Optionally stop other running benchmarks
        3. Select the best worker
        4. Allocate a port
        5. Start the container(s)
        6. Wait for health
        7. Return session info

        Returns:
            {
                "success": True/False,
                "session_id": "sess_abc123",
                "benchmark_id": "S7BEN-EASY-001",
                "worker_id": "local",
                "port": 5005,
                "host": "139.59.80.137",
                "url": "http://139.59.80.137:5005",
                "expires_at": "...",
                "error": None
            }
        """
        logger.info(f"Provisioning {benchmark_id} (agent={agent_id})")

        # Check if already running
        existing = self.sessions.get_active_session_for_benchmark(benchmark_id)
        if existing:
            logger.info(f"{benchmark_id} already has active session {existing['session_id']}")
            return {
                "success": True,
                "session_id": existing["session_id"],
                "benchmark_id": benchmark_id,
                "worker_id": existing["worker_id"],
                "port": existing["port"],
                "host": self._get_worker_host(existing["worker_id"]),
                "url": self._build_url(existing["worker_id"], existing["port"]),
                "expires_at": existing["expires_at"],
                "already_running": True,
                "error": None,
            }

        # Optionally stop other benchmarks (current safety daemon behavior)
        if force_stop_others:
            self._stop_all_running(reason="force_stop_for_new_provision")

        # Select worker
        worker = self._select_worker(benchmark_id)
        if not worker:
            return self._error("No available workers")

        # Resolve benchmark directory
        bench_dir = _get_benchmark_dir(self.config.benchmarks_dir, benchmark_id)
        if not bench_dir:
            return self._error(f"Benchmark directory not found: {benchmark_id}")

        # Determine timeout
        tier = _extract_tier(benchmark_id)
        timeout = timeout_override or self.config.get_timeout_for_tier(tier)

        # Check existing port from docker-compose.yml (for backward compatibility)
        compose_port = self._read_compose_port(bench_dir)
        preferred = preferred_port or compose_port

        # Allocate port
        port = self.port_pool.allocate(
            worker_id=worker.id,
            benchmark_id=benchmark_id,
            session_id=None,  # Will be set after session creation
            preferred_port=preferred,
            port_range=worker.port_range,
        )
        if not port:
            return self._error("No ports available")

        # Create session
        session_id = self.sessions.create_session(
            benchmark_id=benchmark_id,
            worker_id=worker.id,
            port=port,
            timeout_seconds=timeout,
            tier=tier,
            agent_id=agent_id,
        )

        # Start containers
        try:
            # Override port in docker-compose via environment
            os.environ["S7_HOST_PORT"] = str(port)

            result = worker.driver.compose_up(
                project_dir=bench_dir,
                project_name=benchmark_id.lower(),
                detach=True,
            )

            if not result.success:
                # Cleanup on failure
                self.port_pool.release(port)
                self.sessions.update_status(session_id, "stopped",
                                            stop_reason=f"compose_up_failed: {result.error or result.stderr[:200]}")
                return self._error(
                    f"Failed to start containers: {result.error or result.stderr[:200]}",
                    session_id=session_id
                )

            # Update session to running
            self.sessions.update_status(session_id, "running")

            # Create a tracked run if model info provided
            run_id = None
            if model_name or provider:
                run_id = self.run_tracker.create_run(
                    session_id=session_id,
                    benchmark_id=benchmark_id,
                    model_name=model_name,
                    provider=provider,
                    product=product,
                    agent_id=agent_id,
                    difficulty_tier=tier,
                    port=port,
                    worker_id=worker.id,
                )

            host = self._get_worker_host(worker.id)
            url = self._build_url(worker.id, port)

            logger.info(f"✅ {benchmark_id} provisioned: session={session_id}, "
                         f"port={port}, url={url}, run_id={run_id}")

            return {
                "success": True,
                "session_id": session_id,
                "run_id": run_id,
                "benchmark_id": benchmark_id,
                "worker_id": worker.id,
                "port": port,
                "host": host,
                "url": url,
                "expires_at": self.sessions.get_session(session_id)["expires_at"],
                "already_running": False,
                "error": None,
            }

        except Exception as e:
            self.port_pool.release(port)
            self.sessions.update_status(session_id, "stopped",
                                        stop_reason=f"exception: {str(e)}")
            logger.error(f"Provision failed for {benchmark_id}: {e}")
            return self._error(str(e), session_id=session_id)

    def deprovision(self, benchmark_id: str, reason: str = "user_requested") -> Dict:
        """
        Deprovision (stop) a benchmark.

        1. Find active session
        2. Stop containers
        3. Release port
        4. Update session
        """
        logger.info(f"Deprovisioning {benchmark_id} (reason={reason})")

        session = self.sessions.get_active_session_for_benchmark(benchmark_id)

        # Resolve benchmark directory
        bench_dir = _get_benchmark_dir(self.config.benchmarks_dir, benchmark_id)

        if bench_dir:
            # Get the worker driver
            worker_id = session["worker_id"] if session else "local"
            worker = self.workers.get(worker_id)
            if worker:
                result = worker.driver.compose_down(
                    project_dir=bench_dir,
                    project_name=benchmark_id.lower(),
                )
                if not result.success:
                    logger.warning(f"compose_down partial failure for {benchmark_id}: "
                                    f"{result.stderr[:200]}")

        # Finalize any active run for this benchmark
        active_run = self.run_tracker.get_active_run_for_benchmark(benchmark_id)
        if active_run and active_run.get("run_id"):
            self.run_tracker.finalize_run(active_run["run_id"], stop_reason=reason)

        # Release port
        if session and session.get("port"):
            self.port_pool.release(session["port"])

        # Update session
        if session:
            self.sessions.update_status(
                session["session_id"], "stopped", stop_reason=reason
            )

        # Also try direct docker-compose down without project name (fallback)
        if bench_dir:
            fallback_worker = self.workers.get("local")
            if fallback_worker:
                fallback_worker.driver.compose_down(project_dir=bench_dir)

        logger.info(f"✅ {benchmark_id} deprovisioned")
        return {
            "success": True,
            "benchmark_id": benchmark_id,
            "session_id": session["session_id"] if session else None,
            "reason": reason,
        }

    def status(self, benchmark_id: str = None) -> Dict:
        """
        Get status of a specific benchmark or all benchmarks.

        Returns:
            If benchmark_id specified:
                {"benchmark_id": "...", "running": True/False, "session": {...}, "port": 5005}
            If no benchmark_id:
                {"active_sessions": [...], "total_active": N, "workers": [...]}
        """
        if benchmark_id:
            session = self.sessions.get_active_session_for_benchmark(benchmark_id)
            if session:
                return {
                    "benchmark_id": benchmark_id,
                    "running": True,
                    "session": session,
                    "port": session.get("port"),
                    "worker_id": session.get("worker_id"),
                    "url": self._build_url(session["worker_id"], session["port"]),
                    "expires_at": session.get("expires_at"),
                }
            return {
                "benchmark_id": benchmark_id,
                "running": False,
                "session": None,
                "port": None,
            }

        # All active sessions
        active = self.sessions.get_all_active()
        worker_status = []
        for wid, ws in self.workers.items():
            worker_status.append({
                "id": wid,
                "healthy": ws.healthy,
                "active_containers": self.sessions.count_active(worker_id=wid),
                "max_containers": ws.max_containers,
                "last_health_check": ws.last_health_check,
            })

        return {
            "active_sessions": active,
            "total_active": len(active),
            "workers": worker_status,
            "port_pool_active": self.port_pool.count_active(),
        }

    def get_all_container_status(self) -> Dict[str, Dict]:
        """
        Get running status of all benchmarks (for dashboard compatibility).
        Returns a dict keyed by benchmark_id with status info.
        """
        active_sessions = self.sessions.get_all_active()
        result = {}
        for sess in active_sessions:
            result[sess["benchmark_id"]] = {
                "status": "running" if sess["status"] == "running" else "starting",
                "port": sess.get("port"),
                "session_id": sess["session_id"],
                "worker_id": sess["worker_id"],
                "started_at": sess["started_at"],
                "expires_at": sess["expires_at"],
            }
        return result

    # ── Worker Selection ─────────────────────────────────────────────────

    def _select_worker(self, benchmark_id: str) -> Optional[WorkerState]:
        """
        Select the best worker for a new benchmark.
        Strategy: least-loaded healthy worker with capacity.
        """
        candidates = []
        for wid, ws in self.workers.items():
            if not ws.healthy:
                continue
            active = self.sessions.count_active(worker_id=wid)
            if active < ws.max_containers:
                candidates.append((ws, active))

        if not candidates:
            logger.error("No workers with capacity available")
            return None

        # Sort by active count (least loaded first)
        candidates.sort(key=lambda x: x[1])
        return candidates[0][0]

    # ── Background Daemons ───────────────────────────────────────────────

    def _timeout_loop(self):
        """Check for expired sessions and stop them."""
        while self._running:
            try:
                expired = self.sessions.get_expired_sessions()
                for sess in expired:
                    logger.warning(f"Session {sess['session_id']} expired for "
                                    f"{sess['benchmark_id']}")
                    self.deprovision(
                        sess["benchmark_id"],
                        reason="timeout_expired"
                    )
            except Exception as e:
                logger.error(f"Timeout daemon error: {e}")
            time.sleep(30)

    def _health_loop(self):
        """Periodically check worker health."""
        while self._running:
            try:
                for wid, ws in self.workers.items():
                    if ws.config.get("mode") == "remote":
                        # Check SSH connectivity for remote workers
                        if hasattr(ws.driver, 'ping') and not ws.driver.ping():
                            ws.consecutive_failures += 1
                            if ws.consecutive_failures >= 3:
                                ws.healthy = False
                                logger.error(f"Worker {wid} marked unhealthy "
                                              f"({ws.consecutive_failures} failures)")
                        else:
                            ws.consecutive_failures = 0
                            ws.healthy = True
                    else:
                        # Local worker: just check Docker is responding
                        result = ws.driver.container_list()
                        ws.healthy = result.success
                        if not result.success:
                            logger.warning(f"Local Docker not responding")

                    ws.last_health_check = datetime.now(timezone.utc).isoformat()

            except Exception as e:
                logger.error(f"Health monitor error: {e}")
            time.sleep(self.config.health_check_interval)

    def _reconcile_loop(self):
        """
        Periodically reconcile DB state with actual Docker state.
        Catches containers that were stopped outside the orchestrator.
        """
        while self._running:
            try:
                time.sleep(60)  # First check after 60s, then every 60s
                self._reconcile()
            except Exception as e:
                logger.error(f"Reconciliation error: {e}")

    def _reconcile(self):
        """Sync orchestrator DB with actual Docker container state."""
        for wid, ws in self.workers.items():
            active_sessions = self.sessions.get_all_active(worker_id=wid)
            if not active_sessions:
                continue

            for sess in active_sessions:
                bench_id = sess["benchmark_id"]
                bench_dir = _get_benchmark_dir(self.config.benchmarks_dir, bench_id)
                if not bench_dir:
                    continue

                # Use compose ps to check if the benchmark's containers are running.
                # This works regardless of custom container_name directives because
                # docker-compose tracks containers by project label, not name.
                result = ws.driver.compose_ps(
                    project_dir=bench_dir,
                    project_name=bench_id.lower(),
                )

                has_running = False
                if result.success and result.stdout:
                    for line in result.stdout.strip().split("\n"):
                        if "Up" in line or "running" in line.lower():
                            has_running = True
                            break

                if not has_running:
                    logger.warning(f"Session {sess['session_id']} for "
                                    f"{sess['benchmark_id']} has no running containers "
                                    f"— marking as stopped")
                    self.port_pool.release(sess["port"])
                    self.sessions.update_status(
                        sess["session_id"], "stopped",
                        stop_reason="reconciled_no_containers"
                    )

    # ── Helpers ──────────────────────────────────────────────────────────

    def _stop_all_running(self, reason: str = "force_stop"):
        """Stop all running benchmarks (safety daemon behavior)."""
        active = self.sessions.get_all_active()
        for sess in active:
            self.deprovision(sess["benchmark_id"], reason=reason)

    def _get_worker_host(self, worker_id: str) -> str:
        """Get the externally reachable host for a worker."""
        ws = self.workers.get(worker_id)
        if not ws:
            return "localhost"
        # Use public_host if available (for external-facing URLs)
        public_host = ws.config.get("public_host")
        if public_host:
            return public_host
        host = ws.config.get("host", "localhost")
        # For local worker, return the VPS public IP or 0.0.0.0
        if host == "localhost" and ws.config.get("mode") == "local":
            return os.environ.get("S7_PUBLIC_HOST", "0.0.0.0")
        return host

    def _build_url(self, worker_id: str, port: int) -> str:
        """Build the URL for accessing a benchmark."""
        # If proxy is enabled, route through control plane
        control_host = os.environ.get("S7_PUBLIC_HOST", "64.227.163.82")
        if self.config._config.get("proxy", {}).get("enabled", False):
            return f"http://{control_host}/benchmark/{port}"
        # Otherwise direct to worker
        host = self._get_worker_host(worker_id)
        return f"http://{host}:{port}"

    def _read_compose_port(self, bench_dir: str) -> Optional[int]:
        """
        Read the host port from docker-compose.yml for backward compatibility.
        Extracts the port from 'ports: ["XXXX:5000"]' patterns.
        """
        compose_path = os.path.join(bench_dir, "docker-compose.yml")
        if not os.path.exists(compose_path):
            compose_path = os.path.join(bench_dir, "docker-compose.yaml")
        if not os.path.exists(compose_path):
            return None

        try:
            import yaml
            with open(compose_path, "r") as f:
                compose = yaml.safe_load(f)

            services = compose.get("services", {})
            for svc_name, svc_config in services.items():
                ports = svc_config.get("ports", [])
                for port_mapping in ports:
                    port_str = str(port_mapping)
                    if ":" in port_str:
                        host_port = port_str.split(":")[0]
                        try:
                            return int(host_port)
                        except ValueError:
                            continue
        except Exception:
            pass
        return None

    def _error(self, message: str, session_id: str = None) -> Dict:
        """Create an error response."""
        logger.error(f"Orchestrator error: {message}")
        return {
            "success": False,
            "error": message,
            "session_id": session_id,
        }

    # ── Stats / Analytics ────────────────────────────────────────────────

    def get_stats(self) -> Dict:
        """Get orchestrator statistics."""
        all_active = self.sessions.get_all_active()
        history = self.sessions.get_session_history(limit=100)

        # Calculate averages
        completed = [s for s in history if s.get("stopped_at") and s.get("started_at")]
        avg_duration = 0
        if completed:
            durations = []
            for s in completed:
                try:
                    started = datetime.fromisoformat(s["started_at"])
                    stopped = datetime.fromisoformat(s["stopped_at"])
                    durations.append((stopped - started).total_seconds())
                except (ValueError, TypeError):
                    pass
            if durations:
                avg_duration = sum(durations) / len(durations)

        return {
            "active_sessions": len(all_active),
            "total_sessions_last_100": len(history),
            "avg_session_duration_seconds": round(avg_duration, 1),
            "timeout_stops": len([s for s in history if s.get("stop_reason") == "timeout_expired"]),
            "port_pool_active": self.port_pool.count_active(),
            "workers": {
                wid: {
                    "healthy": ws.healthy,
                    "active": self.sessions.count_active(worker_id=wid),
                    "max": ws.max_containers,
                }
                for wid, ws in self.workers.items()
            },
        }
