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

    result = orch.provision(
        benchmark_id=benchmark_id,
        agent_id=data.get("agent_id"),
        force_stop_others=data.get("force_stop_others", True),
        preferred_port=data.get("preferred_port"),
        timeout_override=data.get("timeout_minutes", None),
    )

    status_code = 200 if result.get("success") else 500
    return jsonify(result), status_code


@orchestrator_bp.route("/api/orchestrator/deprovision", methods=["POST"])
def deprovision():
    """Deprovision (stop) a benchmark."""
    orch = get_orchestrator()
    if not orch:
        return jsonify({"error": "Orchestrator not initialized"}), 503

    data = request.get_json(force=True, silent=True) or {}
    benchmark_id = data.get("benchmark_id")
    if not benchmark_id:
        return jsonify({"error": "benchmark_id required"}), 400

    result = orch.deprovision(
        benchmark_id=benchmark_id,
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

    result = orch.provision(
        benchmark_id=benchmark_id,
        agent_id=data.get("agent_id"),
        force_stop_others=data.get("force_stop_others", True),
        timeout_override=data.get("timeout_minutes"),
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
