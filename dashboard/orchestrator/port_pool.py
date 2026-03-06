"""
Strike7 Port Pool Manager

Manages allocation of host ports for benchmark containers.
Persists state to SQLite so port assignments survive restarts.
Supports per-worker port pools for multi-worker setups.
"""

import sqlite3
import threading
import logging
from typing import Optional, Set, Dict, List

logger = logging.getLogger("s7.orchestrator.port_pool")


class PortPool:
    """
    Thread-safe port allocator backed by SQLite.

    On init, loads existing allocations from the DB and computes
    which ports are available. Supports multiple workers, each
    with its own port range.
    """

    def __init__(self, db_path: str, default_start: int = 5001,
                 default_end: int = 5299, reserved: Set[int] = None):
        self.db_path = db_path
        self.default_start = default_start
        self.default_end = default_end
        self.reserved = reserved or set()
        self._lock = threading.Lock()

        self._init_db()
        self._recover_state()

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self):
        """Create the port allocations table if it doesn't exist."""
        conn = self._get_conn()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS port_allocations (
                    port INTEGER PRIMARY KEY,
                    worker_id TEXT NOT NULL,
                    benchmark_id TEXT NOT NULL,
                    session_id TEXT,
                    container_id TEXT,
                    allocated_at TEXT DEFAULT (datetime('now')),
                    released_at TEXT
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_port_active
                ON port_allocations(worker_id, released_at)
            """)
            conn.commit()
        finally:
            conn.close()

    def _recover_state(self):
        """On startup, check if previously allocated ports are still in use."""
        conn = self._get_conn()
        try:
            # Ensure table exists (handles :memory: and fresh DBs)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS port_allocations (
                    port INTEGER PRIMARY KEY,
                    worker_id TEXT NOT NULL,
                    benchmark_id TEXT NOT NULL,
                    session_id TEXT,
                    container_id TEXT,
                    allocated_at TEXT DEFAULT (datetime('now')),
                    released_at TEXT
                )
            """)
            rows = conn.execute(
                "SELECT port, benchmark_id, worker_id FROM port_allocations "
                "WHERE released_at IS NULL"
            ).fetchall()
            logger.info(f"Port pool recovered {len(rows)} active allocations from DB")
        except Exception as e:
            logger.warning(f"Port pool recovery skipped: {e}")
        finally:
            conn.close()

    def allocate(self, worker_id: str, benchmark_id: str,
                 session_id: str = None, preferred_port: int = None,
                 port_range: tuple = None) -> Optional[int]:
        """
        Allocate an available port for a benchmark.

        Args:
            worker_id: Worker node identifier
            benchmark_id: Benchmark being started
            session_id: Optional agent session ID
            preferred_port: Try this port first (for consistency with existing mappings)
            port_range: (start, end) range for this worker. Falls back to defaults.

        Returns:
            Allocated port number, or None if no ports available.
        """
        start, end = port_range or (self.default_start, self.default_end)

        with self._lock:
            conn = self._get_conn()
            try:
                # Get currently allocated ports for this worker
                rows = conn.execute(
                    "SELECT port FROM port_allocations "
                    "WHERE worker_id = ? AND released_at IS NULL",
                    (worker_id,)
                ).fetchall()
                used_ports = {row["port"] for row in rows}

                # Try preferred port first
                if preferred_port and preferred_port not in used_ports \
                        and preferred_port not in self.reserved \
                        and start <= preferred_port <= end:
                    port = preferred_port
                else:
                    # Find first available port
                    port = None
                    for p in range(start, end + 1):
                        if p not in used_ports and p not in self.reserved:
                            port = p
                            break

                if port is None:
                    logger.error(f"No ports available for worker {worker_id} "
                                  f"(range {start}-{end}, {len(used_ports)} used)")
                    return None

                # Record allocation
                conn.execute(
                    "INSERT OR REPLACE INTO port_allocations "
                    "(port, worker_id, benchmark_id, session_id) "
                    "VALUES (?, ?, ?, ?)",
                    (port, worker_id, benchmark_id, session_id)
                )
                conn.commit()

                logger.info(f"Port {port} allocated for {benchmark_id} "
                             f"on worker {worker_id}")
                return port

            finally:
                conn.close()

    def release(self, port: int) -> bool:
        """Release a previously allocated port."""
        with self._lock:
            conn = self._get_conn()
            try:
                result = conn.execute(
                    "UPDATE port_allocations SET released_at = datetime('now') "
                    "WHERE port = ? AND released_at IS NULL",
                    (port,)
                )
                conn.commit()
                released = result.rowcount > 0
                if released:
                    logger.info(f"Port {port} released")
                else:
                    logger.warning(f"Port {port} was not allocated (no-op release)")
                return released
            finally:
                conn.close()

    def release_by_benchmark(self, benchmark_id: str, worker_id: str = None) -> List[int]:
        """Release all ports for a given benchmark."""
        with self._lock:
            conn = self._get_conn()
            try:
                query = ("UPDATE port_allocations SET released_at = datetime('now') "
                         "WHERE benchmark_id = ? AND released_at IS NULL")
                params = [benchmark_id]
                if worker_id:
                    query += " AND worker_id = ?"
                    params.append(worker_id)

                # First, get the ports we're about to release
                select = ("SELECT port FROM port_allocations "
                          "WHERE benchmark_id = ? AND released_at IS NULL")
                s_params = [benchmark_id]
                if worker_id:
                    select += " AND worker_id = ?"
                    s_params.append(worker_id)

                rows = conn.execute(select, s_params).fetchall()
                ports = [row["port"] for row in rows]

                conn.execute(query, params)
                conn.commit()

                logger.info(f"Released ports {ports} for benchmark {benchmark_id}")
                return ports
            finally:
                conn.close()

    def get_active_allocations(self, worker_id: str = None) -> List[Dict]:
        """Get all currently active port allocations."""
        conn = self._get_conn()
        try:
            if worker_id:
                rows = conn.execute(
                    "SELECT * FROM port_allocations "
                    "WHERE worker_id = ? AND released_at IS NULL "
                    "ORDER BY port",
                    (worker_id,)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM port_allocations "
                    "WHERE released_at IS NULL ORDER BY port"
                ).fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def get_port_for_benchmark(self, benchmark_id: str,
                                worker_id: str = None) -> Optional[int]:
        """Look up the active port for a running benchmark."""
        conn = self._get_conn()
        try:
            query = ("SELECT port FROM port_allocations "
                     "WHERE benchmark_id = ? AND released_at IS NULL")
            params = [benchmark_id]
            if worker_id:
                query += " AND worker_id = ?"
                params.append(worker_id)
            query += " LIMIT 1"

            row = conn.execute(query, params).fetchone()
            return row["port"] if row else None
        finally:
            conn.close()

    def count_active(self, worker_id: str = None) -> int:
        """Count active allocations."""
        conn = self._get_conn()
        try:
            if worker_id:
                row = conn.execute(
                    "SELECT COUNT(*) as cnt FROM port_allocations "
                    "WHERE worker_id = ? AND released_at IS NULL",
                    (worker_id,)
                ).fetchone()
            else:
                row = conn.execute(
                    "SELECT COUNT(*) as cnt FROM port_allocations "
                    "WHERE released_at IS NULL"
                ).fetchone()
            return row["cnt"]
        finally:
            conn.close()

    def cleanup_stale(self, active_ports: Set[int], worker_id: str = "local") -> int:
        """
        Clean up allocations for ports that are no longer in use.
        Called during reconciliation with actual Docker state.
        """
        with self._lock:
            conn = self._get_conn()
            try:
                rows = conn.execute(
                    "SELECT port FROM port_allocations "
                    "WHERE worker_id = ? AND released_at IS NULL",
                    (worker_id,)
                ).fetchall()

                stale_count = 0
                for row in rows:
                    if row["port"] not in active_ports:
                        conn.execute(
                            "UPDATE port_allocations SET released_at = datetime('now') "
                            "WHERE port = ? AND released_at IS NULL",
                            (row["port"],)
                        )
                        stale_count += 1

                conn.commit()
                if stale_count > 0:
                    logger.info(f"Cleaned up {stale_count} stale port allocations "
                                 f"on worker {worker_id}")
                return stale_count
            finally:
                conn.close()
