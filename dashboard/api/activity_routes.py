"""
Flask Blueprint for agent activity feed endpoints.
Provides SSE live stream, history, summary, and clear.
"""
import json
import os
import sqlite3
import queue
from flask import Blueprint, Response, jsonify, request, render_template
from api.activity_logger import (
    subscribe, unsubscribe, get_activity_history, get_agent_summary, clear_activity
)

COMPARISON_DB_PATH = os.environ.get(
    'COMPARISON_DB_PATH',
    os.path.join(os.path.dirname(__file__), '..', 'data', 'model_benchmarks.db')
)

activity_bp = Blueprint('activity', __name__)


@activity_bp.route('/api/activity-feed')
def activity_feed():
    """Server-Sent Events stream for live agent activity."""
    def event_stream():
        q = subscribe()
        try:
            while True:
                try:
                    event = q.get(timeout=30)
                    yield f"data: {json.dumps(event)}\n\n"
                except queue.Empty:
                    # Send keepalive comment to prevent connection timeout
                    yield ": keepalive\n\n"
        except GeneratorExit:
            pass
        finally:
            unsubscribe(q)

    return Response(
        event_stream(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive'
        }
    )


@activity_bp.route('/api/activity-history')
def activity_history():
    """Get recent activity events (for page load)."""
    limit = request.args.get('limit', 100, type=int)
    events = get_activity_history(limit=limit)
    return jsonify({"events": events})


@activity_bp.route('/api/agent-summary')
def agent_summary():
    """Get summary statistics merging activity logger and comparison DB."""
    summary = get_agent_summary()

    # Merge stats from comparison DB as fallback for historical runs
    try:
        if os.path.exists(COMPARISON_DB_PATH):
            conn = sqlite3.connect(COMPARISON_DB_PATH)
            total_runs = conn.execute(
                "SELECT COUNT(*) FROM model_benchmark_runs"
            ).fetchone()[0]
            total_captures = conn.execute(
                "SELECT COUNT(*) FROM model_benchmark_runs WHERE flag_captured = 1"
            ).fetchone()[0]

            tier_rows = conn.execute("""
                SELECT difficulty_tier,
                       COUNT(*) as attempted,
                       SUM(flag_captured) as solved
                FROM model_benchmark_runs
                GROUP BY difficulty_tier
            """).fetchall()
            conn.close()

            # Use comparison DB numbers if they exceed activity logger counts
            if total_runs > summary.get('benchmarks_attempted', 0):
                summary['benchmarks_attempted'] = total_runs
            if total_captures > summary.get('benchmarks_solved', 0):
                summary['benchmarks_solved'] = total_captures

            total_flag_events = summary.get('total_flag_attempts', 0)
            if total_runs > total_flag_events:
                summary['total_flag_attempts'] = total_runs

            # Recalculate pass rate from best numbers
            attempted = summary['total_flag_attempts'] or summary['benchmarks_attempted']
            solved = summary['benchmarks_solved']
            summary['pass_rate'] = f"{(solved / max(attempted, 1)) * 100:.0f}%"

            # Merge tier stats
            tiers = summary.get('tiers', {})
            for row in tier_rows:
                tier = row[0]
                comp_attempted = row[1] or 0
                comp_solved = row[2] or 0
                if tier in tiers:
                    if comp_attempted > tiers[tier]['attempted']:
                        tiers[tier]['attempted'] = comp_attempted
                    if comp_solved > tiers[tier]['solved']:
                        tiers[tier]['solved'] = comp_solved
                else:
                    tiers[tier] = {'solved': comp_solved, 'attempted': comp_attempted}
            summary['tiers'] = tiers
    except Exception:
        pass  # Activity logger stats alone are fine as fallback

    return jsonify(summary)


@activity_bp.route('/api/activity-clear', methods=['POST'])
def activity_clear():
    """Clear all activity data (for fresh test runs)."""
    clear_activity()
    return jsonify({"status": "cleared", "message": "All activity data cleared"})


@activity_bp.route('/agent-feed')
def agent_feed_page():
    """Serve the agent activity feed page."""
    return render_template('agent_feed.html')
