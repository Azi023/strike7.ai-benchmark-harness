"""
Strike7 Session Manager

Tracks active benchmark sessions: which benchmarks are running,
on which worker, when they started, and when they expire.
Persisted to SQLite for crash recovery.
"""

import sqlite3
import threading
import uuid
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

logger = logging.getLogger("s7.orchestrator.sessions")


class SessionManager:
    """Manages benchmark session lifecycle with SQLite persistence."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_db()

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self):
        conn = self._get_conn()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    benchmark_id TEXT NOT NULL,
                    worker_id TEXT NOT NULL DEFAULT 'local',
                    port INTEGER,
                    container_names TEXT,
                    status TEXT NOT NULL DEFAULT 'provisioning',
                    agent_id TEXT,
                    tier TEXT,
                    started_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    stopped_at TEXT,
                    stop_reason TEXT,
                    created_at TEXT DEFAULT (datetime('now'))
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_session_benchmark
                ON sessions(benchmark_id, status)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_session_status
                ON sessions(status, expires_at)
            """)

            # Activity log for audit trail
            conn.execute("""
                CREATE TABLE IF NOT EXISTS session_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    details TEXT,
                    timestamp TEXT DEFAULT (datetime('now')),
                    FOREIGN KEY(session_id) REFERENCES sessions(session_id)
                )
            """)
            conn.commit()
        finally:
            conn.close()

    def create_session(self, benchmark_id: str, worker_id: str, port: int,
                       timeout_seconds: int, tier: str = None,
                       agent_id: str = None) -> str:
        """
        Create a new benchmark session.
        Returns session_id.
        """
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=timeout_seconds)

        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute(
                    "INSERT INTO sessions "
                    "(session_id, benchmark_id, worker_id, port, status, "
                    " agent_id, tier, started_at, expires_at) "
                    "VALUES (?, ?, ?, ?, 'provisioning', ?, ?, ?, ?)",
                    (session_id, benchmark_id, worker_id, port,
                     agent_id, tier,
                     now.isoformat(), expires_at.isoformat())
                )
                conn.execute(
                    "INSERT INTO session_events (session_id, event_type, details) "
                    "VALUES (?, 'created', ?)",
                    (session_id, f"port={port}, worker={worker_id}, "
                                  f"timeout={timeout_seconds}s")
                )
                conn.commit()
                logger.info(f"Session {session_id} created for {benchmark_id} "
                             f"on {worker_id}:{port} (expires {expires_at.isoformat()})")
                return session_id
            finally:
                conn.close()

    def update_status(self, session_id: str, status: str,
                      container_names: str = None,
                      stop_reason: str = None):
        """Update session status (provisioning → running → stopped)."""
        with self._lock:
            conn = self._get_conn()
            try:
                updates = ["status = ?"]
                params = [status]

                if container_names:
                    updates.append("container_names = ?")
                    params.append(container_names)

                if status == "stopped":
                    updates.append("stopped_at = datetime('now')")
                    if stop_reason:
                        updates.append("stop_reason = ?")
                        params.append(stop_reason)

                params.append(session_id)
                conn.execute(
                    f"UPDATE sessions SET {', '.join(updates)} "
                    f"WHERE session_id = ?",
                    params
                )
                conn.execute(
                    "INSERT INTO session_events (session_id, event_type, details) "
                    "VALUES (?, ?, ?)",
                    (session_id, f"status_change:{status}", stop_reason or "")
                )
                conn.commit()
                logger.info(f"Session {session_id} → {status}"
                             f"{f' ({stop_reason})' if stop_reason else ''}")
            finally:
                conn.close()

    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session details."""
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT * FROM sessions WHERE session_id = ?",
                (session_id,)
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_active_session_for_benchmark(self, benchmark_id: str) -> Optional[Dict]:
        """Get the active (running/provisioning) session for a benchmark."""
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT * FROM sessions "
                "WHERE benchmark_id = ? AND status IN ('running', 'provisioning') "
                "ORDER BY started_at DESC LIMIT 1",
                (benchmark_id,)
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_all_active(self, worker_id: str = None) -> List[Dict]:
        """Get all active sessions."""
        conn = self._get_conn()
        try:
            if worker_id:
                rows = conn.execute(
                    "SELECT * FROM sessions "
                    "WHERE status IN ('running', 'provisioning') "
                    "AND worker_id = ? ORDER BY started_at",
                    (worker_id,)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM sessions "
                    "WHERE status IN ('running', 'provisioning') "
                    "ORDER BY started_at"
                ).fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def get_expired_sessions(self) -> List[Dict]:
        """Get sessions that have exceeded their timeout."""
        now = datetime.now(timezone.utc).isoformat()
        conn = self._get_conn()
        try:
            rows = conn.execute(
                "SELECT * FROM sessions "
                "WHERE status IN ('running', 'provisioning') "
                "AND expires_at < ?",
                (now,)
            ).fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def count_active(self, worker_id: str = None,
                     agent_id: str = None) -> int:
        """Count active sessions with optional filters."""
        conn = self._get_conn()
        try:
            query = "SELECT COUNT(*) as cnt FROM sessions WHERE status IN ('running', 'provisioning')"
            params = []
            if worker_id:
                query += " AND worker_id = ?"
                params.append(worker_id)
            if agent_id:
                query += " AND agent_id = ?"
                params.append(agent_id)
            row = conn.execute(query, params).fetchone()
            return row["cnt"]
        finally:
            conn.close()

    def get_session_history(self, benchmark_id: str = None,
                            limit: int = 50) -> List[Dict]:
        """Get session history for analytics."""
        conn = self._get_conn()
        try:
            if benchmark_id:
                rows = conn.execute(
                    "SELECT * FROM sessions WHERE benchmark_id = ? "
                    "ORDER BY started_at DESC LIMIT ?",
                    (benchmark_id, limit)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM sessions ORDER BY started_at DESC LIMIT ?",
                    (limit,)
                ).fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def get_events(self, session_id: str) -> List[Dict]:
        """Get all events for a session."""
        conn = self._get_conn()
        try:
            rows = conn.execute(
                "SELECT * FROM session_events WHERE session_id = ? "
                "ORDER BY timestamp",
                (session_id,)
            ).fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def cleanup_orphaned(self) -> int:
        """
        Mark any sessions stuck in 'provisioning' for > 5 minutes as failed.
        Called on startup to clean up after crashes.
        """
        cutoff = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
        with self._lock:
            conn = self._get_conn()
            try:
                result = conn.execute(
                    "UPDATE sessions SET status = 'stopped', "
                    "stopped_at = datetime('now'), stop_reason = 'orphaned_on_startup' "
                    "WHERE status = 'provisioning' AND started_at < ?",
                    (cutoff,)
                )
                conn.commit()
                count = result.rowcount
                if count > 0:
                    logger.warning(f"Cleaned up {count} orphaned sessions")
                return count
            finally:
                conn.close()
