"""
Agent activity logger for Strike7 benchmarks.
Logs events to SQLite and broadcasts to SSE subscribers.
"""
import sqlite3
import json
import os
import threading
import queue
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'agent_activity.db')

# Thread-safe list of subscriber queues for SSE broadcasting
_subscribers_lock = threading.Lock()
_subscribers = []


def _ensure_db():
    """Create tables if they don't exist (idempotent)."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS agent_activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            session_id TEXT,
            event_type TEXT NOT NULL,
            benchmark_id TEXT,
            details TEXT DEFAULT '{}',
            severity TEXT DEFAULT 'info'
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS agent_sessions (
            session_id TEXT PRIMARY KEY,
            started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            ended_at DATETIME,
            agent_name TEXT DEFAULT 'strike7-agent',
            benchmarks_attempted INTEGER DEFAULT 0,
            benchmarks_solved INTEGER DEFAULT 0
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_activity_type ON agent_activity(event_type)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_activity_bench ON agent_activity(benchmark_id)")
    conn.commit()
    conn.close()


# Auto-initialize on import
_ensure_db()


def log_activity(event_type, benchmark_id=None, details=None, severity="info", session_id=None):
    """Log an agent activity event to SQLite and broadcast to SSE subscribers."""
    details_json = json.dumps(details or {})
    timestamp = datetime.utcnow().isoformat() + "Z"

    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        INSERT INTO agent_activity (timestamp, session_id, event_type, benchmark_id, details, severity)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (timestamp, session_id, event_type, benchmark_id, details_json, severity))
    conn.commit()
    conn.close()

    event = {
        "timestamp": timestamp,
        "session_id": session_id,
        "event_type": event_type,
        "benchmark_id": benchmark_id,
        "details": details or {},
        "severity": severity
    }
    broadcast_activity(event)


def broadcast_activity(event):
    """Push an event to all SSE subscribers."""
    with _subscribers_lock:
        dead = []
        for q in _subscribers:
            try:
                q.put_nowait(event)
            except queue.Full:
                dead.append(q)
        for q in dead:
            _subscribers.remove(q)


def subscribe():
    """Create a new subscriber queue and register it. Returns the queue."""
    q = queue.Queue(maxsize=256)
    with _subscribers_lock:
        _subscribers.append(q)
    return q


def unsubscribe(q):
    """Remove a subscriber queue."""
    with _subscribers_lock:
        if q in _subscribers:
            _subscribers.remove(q)


def get_activity_history(limit=100):
    """Return recent activity events as a list of dicts."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT timestamp, session_id, event_type, benchmark_id, details, severity
        FROM agent_activity
        ORDER BY id DESC LIMIT ?
    """, (limit,)).fetchall()
    conn.close()

    events = []
    for r in reversed(rows):
        events.append({
            "timestamp": r["timestamp"],
            "session_id": r["session_id"],
            "event_type": r["event_type"],
            "benchmark_id": r["benchmark_id"],
            "details": json.loads(r["details"]) if r["details"] else {},
            "severity": r["severity"]
        })
    return events


def get_agent_summary():
    """Return aggregate stats: solved/attempted per tier."""
    conn = sqlite3.connect(DB_PATH)

    total_starts = conn.execute(
        "SELECT COUNT(*) FROM agent_activity WHERE event_type='benchmark_start'"
    ).fetchone()[0]

    total_correct = conn.execute(
        "SELECT COUNT(*) FROM agent_activity WHERE event_type='flag_correct'"
    ).fetchone()[0]

    total_attempts = conn.execute(
        "SELECT COUNT(*) FROM agent_activity WHERE event_type IN ('flag_correct','flag_incorrect')"
    ).fetchone()[0]

    tiers = {}
    for tier in ['EASY', 'MED', 'HARD', 'VHARD', 'CVE']:
        solved = conn.execute("""
            SELECT COUNT(DISTINCT benchmark_id) FROM agent_activity
            WHERE event_type='flag_correct' AND benchmark_id LIKE ?
        """, (f"S7BEN-{tier}-%",)).fetchone()[0]

        attempted = conn.execute("""
            SELECT COUNT(DISTINCT benchmark_id) FROM agent_activity
            WHERE event_type='benchmark_start' AND benchmark_id LIKE ?
        """, (f"S7BEN-{tier}-%",)).fetchone()[0]

        tiers[tier] = {"solved": solved, "attempted": attempted}

    conn.close()

    return {
        "benchmarks_attempted": total_starts,
        "benchmarks_solved": total_correct,
        "total_flag_attempts": total_attempts,
        "pass_rate": f"{(total_correct / max(total_attempts, 1)) * 100:.0f}%",
        "tiers": tiers
    }


def clear_activity():
    """Clear all activity data (for fresh test runs)."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM agent_activity")
    conn.execute("DELETE FROM agent_sessions")
    conn.commit()
    conn.close()
