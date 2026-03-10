"""
Strike7 Orchestrator API — Flask Blueprint

This Blueprint provides the orchestrator's REST API endpoints.
It is registered into the existing Flask dashboard app.

Endpoints:
  POST   /api/orchestrator/provision          Start a benchmark
  POST   /api/orchestrator/deprovision        Stop a benchmark
  GET    /api/orchestrator/status              Get all active sessions
  GET    /api/orchestrator/status/<id>         Get specific benchmark status
  GET    /api/orchestrator/stats               Get orchestrator statistics
  GET    /api/orchestrator/health              Health check
  GET    /api/orchestrator/workers             Worker node status
  GET    /api/orchestrator/sessions            Session history
  GET    /api/orchestrator/ports               Port pool status

  # Backward-compatible endpoints (wrap orchestrator calls)
  POST   /api/benchmark/<id>/start             Provision (dashboard compat)
  POST   /api/benchmark/<id>/stop              Deprovision (dashboard compat)
  GET    /api/containers/status                Container status (dashboard compat)
"""

import logging
from flask import Blueprint, request, jsonify, current_app

logger = logging.getLogger("s7.orchestrator.api")

orchestrator_bp = Blueprint("orchestrator", __name__)


def get_orchestrator():
    """Get the orchestrator service instance from the Flask app."""
    return current_app.config.get("ORCHESTRATOR")


# ── Orchestrator Native API ──────────────────────────────────────────────

@orchestrator_bp.route("/api/orchestrator/provision", methods=["POST"])
def provision():
    """Provision (start) a benchmark."""
    orch = get_orchestrator()
    if not orch:
        return jsonify({"error": "Orchestrator not initialized"}), 503

    data = request.get_json(force=True, silent=True) or {}
    benchmark_id = data.get("benchmark_id")
    if not benchmark_id:
        return jsonify({"error": "benchmark_id required"}), 400

    timeout_min = data.get("timeout_minutes")
    result = orch.provision(
        benchmark_id=benchmark_id,
        agent_id=data.get("agent_id"),
        force_stop_others=data.get("force_stop_others", True),
        preferred_port=data.get("preferred_port"),
        timeout_override=int(timeout_min) * 60 if timeout_min else None,
        model_name=data.get("model_name"),
        provider=data.get("provider"),
        product=data.get("product"),
    )

    status_code = 200 if result.get("success") else 500
    return jsonify(result), status_code


@orchestrator_bp.route("/api/orchestrator/deprovision", methods=["POST"])
def deprovision():
    """Deprovision (stop) a benchmark.

    Accepts benchmark_id and/or session_id.  When both are given,
    session_id is preferred (needed for concurrent same-benchmark instances).
    """
    orch = get_orchestrator()
    if not orch:
        return jsonify({"error": "Orchestrator not initialized"}), 503

    data = request.get_json(force=True, silent=True) or {}
    benchmark_id = data.get("benchmark_id")
    session_id = data.get("session_id")
    if not benchmark_id and not session_id:
        return jsonify({"error": "benchmark_id or session_id required"}), 400

    result = orch.deprovision(
        benchmark_id=benchmark_id,
        session_id=session_id,
        reason=data.get("reason", "api_request"),
    )
    return jsonify(result)


@orchestrator_bp.route("/api/orchestrator/status", methods=["GET"])
def all_status():
    """Get status of all active sessions and workers."""
    orch = get_orchestrator()
    if not orch:
        return jsonify({"error": "Orchestrator not initialized"}), 503
    return jsonify(orch.status())


@orchestrator_bp.route("/api/orchestrator/status/<benchmark_id>", methods=["GET"])
def benchmark_status(benchmark_id):
    """Get status of a specific benchmark."""
    orch = get_orchestrator()
    if not orch:
        return jsonify({"error": "Orchestrator not initialized"}), 503
    return jsonify(orch.status(benchmark_id))


@orchestrator_bp.route("/api/orchestrator/stats", methods=["GET"])
def stats():
    """Get orchestrator statistics and analytics."""
    orch = get_orchestrator()
    if not orch:
        return jsonify({"error": "Orchestrator not initialized"}), 503
    return jsonify(orch.get_stats())


@orchestrator_bp.route("/api/orchestrator/health", methods=["GET"])
def health():
    """Orchestrator health check."""
    orch = get_orchestrator()
    if not orch:
        return jsonify({"status": "error", "detail": "not initialized"}), 503

    status_data = orch.status()
    workers_healthy = all(
        w.get("healthy", False) for w in status_data.get("workers", [])
    )

    return jsonify({
        "status": "healthy" if workers_healthy else "degraded",
        "active_sessions": status_data.get("total_active", 0),
        "workers": status_data.get("workers", []),
        "version": "1.0.0",
    })


@orchestrator_bp.route("/api/orchestrator/workers", methods=["GET"])
def workers():
    """Get detailed worker status."""
    orch = get_orchestrator()
    if not orch:
        return jsonify({"error": "Orchestrator not initialized"}), 503

    worker_list = []
    for wid, ws in orch.workers.items():
        worker_list.append({
            "id": wid,
            "mode": ws.config.get("mode", "local"),
            "host": ws.config.get("host", "localhost"),
            "healthy": ws.healthy,
            "active_containers": orch.sessions.count_active(worker_id=wid),
            "max_containers": ws.max_containers,
            "port_range": list(ws.port_range),
            "last_health_check": ws.last_health_check,
        })

    return jsonify({"workers": worker_list})


@orchestrator_bp.route("/api/orchestrator/sessions", methods=["GET"])
def session_history():
    """Get session history."""
    orch = get_orchestrator()
    if not orch:
        return jsonify({"error": "Orchestrator not initialized"}), 503

    benchmark_id = request.args.get("benchmark_id")
    limit = int(request.args.get("limit", 50))

    history = orch.sessions.get_session_history(
        benchmark_id=benchmark_id, limit=limit
    )
    return jsonify({"sessions": history, "total": len(history)})


@orchestrator_bp.route("/api/orchestrator/ports", methods=["GET"])
def port_status():
    """Get port pool status."""
    orch = get_orchestrator()
    if not orch:
        return jsonify({"error": "Orchestrator not initialized"}), 503

    allocations = orch.port_pool.get_active_allocations()
    return jsonify({
        "active_allocations": allocations,
        "total_active": len(allocations),
        "pool_range": [orch.config.port_pool_start, orch.config.port_pool_end],
    })


# ── Dashboard-Compatible Endpoints ──────────────────────────────────────
# These wrap the orchestrator to maintain backward compatibility with
# the existing dashboard frontend and MCP server.

@orchestrator_bp.route("/api/benchmark/<benchmark_id>/start", methods=["POST"])
def compat_start(benchmark_id):
    """
    Dashboard-compatible start endpoint.
    Wraps orchestrator.provision().
    """
    orch = get_orchestrator()
    if not orch:
        return jsonify({"error": "Orchestrator not initialized"}), 503

    data = request.get_json(force=True, silent=True) or {}
    timeout_min = data.get("timeout_minutes")

    result = orch.provision(
        benchmark_id=benchmark_id,
        agent_id=data.get("agent_id"),
        force_stop_others=data.get("force_stop_others", True),
        timeout_override=int(timeout_min) * 60 if timeout_min else None,
        model_name=data.get("model_name"),
        provider=data.get("provider"),
        product=data.get("product"),
    )

    # Transform to existing dashboard response format
    if result.get("success"):
        return jsonify({
            "status": "started",
            "message": f"Benchmark {benchmark_id} started successfully",
            "benchmark_id": benchmark_id,
            "port": result.get("port"),
            "url": result.get("url"),
            "session_id": result.get("session_id"),
            "run_id": result.get("run_id"),
            "expires_at": result.get("expires_at"),
        })
    else:
        return jsonify({
            "status": "error",
            "message": result.get("error", "Failed to start benchmark"),
        }), 500


@orchestrator_bp.route("/api/benchmark/<benchmark_id>/stop", methods=["POST"])
def compat_stop(benchmark_id):
    """
    Dashboard-compatible stop endpoint.
    Wraps orchestrator.deprovision().
    """
    orch = get_orchestrator()
    if not orch:
        return jsonify({"error": "Orchestrator not initialized"}), 503

    result = orch.deprovision(benchmark_id=benchmark_id, reason="dashboard_stop")

    return jsonify({
        "status": "stopped",
        "message": f"Benchmark {benchmark_id} stopped",
        "benchmark_id": benchmark_id,
    })


@orchestrator_bp.route("/api/containers/status", methods=["GET"])
def compat_container_status():
    """
    Dashboard-compatible container status endpoint.
    Returns status in the format the dashboard JS expects:
    {"running_count": N, "max_allowed": M, "containers": [...], "system": {}}
    """
    orch = get_orchestrator()
    if not orch:
        return jsonify({
            "running_count": 0,
            "max_allowed": 0,
            "containers": [],
            "system": {}
        }), 503

    raw = orch.get_all_container_status()

    # Transform from {benchmark_id: {...}} to the list format the dashboard expects
    containers = []
    for bid, info in raw.items():
        containers.append({
            "benchmark_id": bid,
            "status": info.get("status", "running"),
            "health_status": "running" if info.get("status") == "running" else "starting",
            "port": info.get("port"),
            "started_at": info.get("started_at"),
            "session_id": info.get("session_id"),
            "runtime_seconds": 0,
            "memory_mb": 0,
            "cpu_percent": 0,
            "service_count": 1,
        })

    return jsonify({
        "running_count": len(containers),
        "max_allowed": orch.config._config.get("limits", {}).get("max_containers_per_worker", 15),
        "containers": containers,
        "system": {}
    })


# ── Run Tracking Endpoints ───────────────────────────────────────────────

@orchestrator_bp.route("/api/comparison/runs/<run_id>/detail", methods=["GET"])
def run_detail(run_id):
    """Get full run detail including steps, flag attempts, and metrics."""
    orch = get_orchestrator()
    if not orch or not hasattr(orch, 'run_tracker'):
        return jsonify({"error": "Run tracker not available"}), 503

    run = orch.run_tracker.get_run(run_id)
    if not run:
        return jsonify({"error": "Run not found"}), 404

    steps = orch.run_tracker.get_run_steps(run_id)
    flags = orch.run_tracker.get_run_flags(run_id)

    # Calculate additional metrics
    unique_paths = len(set(s["path"] for s in steps))

    # Detect loops: same path requested 3+ times consecutively
    loop_sequences = []
    if len(steps) >= 3:
        for i in range(2, len(steps)):
            if steps[i]["path"] == steps[i-1]["path"] == steps[i-2]["path"]:
                if not loop_sequences or loop_sequences[-1]["path"] != steps[i]["path"]:
                    loop_sequences.append({
                        "path": steps[i]["path"],
                        "start_step": steps[i-2]["step_number"],
                        "count": 3
                    })
                else:
                    loop_sequences[-1]["count"] += 1

    # Time analysis
    step_times = [s["duration_ms"] for s in steps if s.get("duration_ms")]
    avg_step_time = sum(step_times) / len(step_times) if step_times else 0

    return jsonify({
        "run": run,
        "steps": steps,
        "flag_attempts": flags,
        "metrics": {
            "total_steps": len(steps),
            "unique_paths": unique_paths,
            "loop_count": len(loop_sequences),
            "loops": loop_sequences,
            "avg_step_duration_ms": round(avg_step_time, 1),
            "total_request_time_ms": sum(step_times),
        }
    })


@orchestrator_bp.route("/api/comparison/runs/active", methods=["GET"])
def active_runs_with_steps():
    """Get all currently active runs with their latest steps — for real-time display."""
    orch = get_orchestrator()
    if not orch or not hasattr(orch, 'run_tracker'):
        return jsonify({"active_runs": []}), 200

    import sqlite3 as _sqlite3
    db_path = orch.run_tracker.db_path
    conn = _sqlite3.connect(db_path)
    conn.row_factory = _sqlite3.Row

    # Get running runs
    runs = conn.execute(
        "SELECT * FROM model_benchmark_runs WHERE status = 'running' ORDER BY run_timestamp DESC"
    ).fetchall()

    result = []
    for run in runs:
        run_dict = dict(run)
        run_id = run_dict.get("run_id")

        # Get latest 20 steps
        steps = conn.execute(
            "SELECT * FROM run_steps WHERE run_id = ? ORDER BY step_number DESC LIMIT 20",
            (run_id,)
        ).fetchall()
        steps = [dict(s) for s in reversed(steps)]

        # Step count
        count = conn.execute(
            "SELECT COUNT(*) as cnt FROM run_steps WHERE run_id = ?", (run_id,)
        ).fetchone()["cnt"]

        # Unique paths
        paths = conn.execute(
            "SELECT DISTINCT path FROM run_steps WHERE run_id = ?", (run_id,)
        ).fetchall()

        run_dict["live_steps"] = steps
        run_dict["total_steps"] = count
        run_dict["unique_paths"] = len(paths)

        result.append(run_dict)

    conn.close()
    return jsonify({"active_runs": result})
