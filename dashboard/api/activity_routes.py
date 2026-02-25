"""
Flask Blueprint for agent activity feed endpoints.
Provides SSE live stream, history, summary, and clear.
"""
import json
import queue
from flask import Blueprint, Response, jsonify, request, render_template
from api.activity_logger import (
    subscribe, unsubscribe, get_activity_history, get_agent_summary, clear_activity
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
    """Get summary statistics for agent activity."""
    summary = get_agent_summary()
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
