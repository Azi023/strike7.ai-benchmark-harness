"""
Strike7 Run Tracker

Bridges orchestrator sessions with the model comparison database.
Every benchmark attempt creates a "run" that tracks:
- Who ran it (model, provider, product)
- Every HTTP step the agent took
- Flag submission attempts and outcomes
- Timing, duration, step count
"""

import sqlite3
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

logger = logging.getLogger("s7.orchestrator.run_tracker")


class RunTracker:
    # Canonical model names — prevents duplicate entries from variant spellings
    _MODEL_ALIASES = {
        "claude-sonnet-4-5": "claude-sonnet-4.5",
        "claude_sonnet_4.5": "claude-sonnet-4.5",
        "claude-sonnet-4_5": "claude-sonnet-4.5",
        "gemini-2-5-flash": "gemini-2.5-flash",
        "gemini-2-5-pro": "gemini-2.5-pro",
    }

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    @classmethod
    def normalize_model_name(cls, name: str) -> str:
        """Normalize model names to prevent duplicates."""
        if not name:
            return "unknown"
        name = name.lower().strip()
        return cls._MODEL_ALIASES.get(name, name)

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self):
        """Create/upgrade tables for run tracking."""
        conn = self._get_conn()
        try:
            # Steps table — every HTTP request to a benchmark
            conn.execute("""
                CREATE TABLE IF NOT EXISTS run_steps (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    step_number INTEGER NOT NULL,
                    timestamp TEXT NOT NULL,
                    method TEXT NOT NULL,
                    path TEXT NOT NULL,
                    query_string TEXT,
                    status_code INTEGER,
                    duration_ms REAL,
                    response_size_bytes INTEGER,
                    source_ip TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_steps_run ON run_steps(run_id)")

            # Flag attempts table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS flag_attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    benchmark_id TEXT NOT NULL,
                    attempt_number INTEGER NOT NULL,
                    flag_submitted TEXT,
                    result TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_flags_run ON flag_attempts(run_id)")

            # Add columns to model_benchmark_runs if they don't exist
            # (safely handles if columns already exist)
            for col_def in [
                ("run_id", "TEXT"),
                ("session_id", "TEXT"),
                ("product", "TEXT"),
                ("port", "INTEGER"),
                ("worker_id", "TEXT"),
                ("total_steps", "INTEGER DEFAULT 0"),
                ("flag_attempt_count", "INTEGER DEFAULT 0"),
                ("status", "TEXT DEFAULT 'running'"),
                ("stop_reason", "TEXT"),
            ]:
                try:
                    conn.execute(
                        f"ALTER TABLE model_benchmark_runs ADD COLUMN {col_def[0]} {col_def[1]}"
                    )
                except sqlite3.OperationalError:
                    pass  # Column already exists

            conn.commit()
        finally:
            conn.close()

    def create_run(
        self,
        session_id: str,
        benchmark_id: str,
        model_name: str = None,
        provider: str = None,
        product: str = None,
        agent_id: str = None,
        difficulty_tier: str = None,
        port: int = None,
        worker_id: str = None,
    ) -> str:
        """Create a new run when a benchmark is provisioned with model info."""
        run_id = f"run_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        model_name = self.normalize_model_name(model_name)

        conn = self._get_conn()
        try:
            conn.execute(
                """
                INSERT INTO model_benchmark_runs
                (run_id, session_id, benchmark_id, provider, model_name, product,
                 product_name, difficulty_tier, port, worker_id, status,
                 run_timestamp, execution_method,
                 flag_captured, total_duration_s, attempt_number)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'running', ?, 'orchestrator',
                        0, 0, 1)
            """,
                (
                    run_id,
                    session_id,
                    benchmark_id,
                    provider or "unknown",
                    model_name,
                    product or "unknown",
                    product or "unknown",
                    difficulty_tier or "UNKNOWN",
                    port,
                    worker_id,
                    now,
                ),
            )
            conn.commit()
            logger.info(
                f"Run {run_id} created for {benchmark_id} "
                f"({provider}/{model_name}/{product})"
            )
            return run_id
        except Exception as e:
            logger.error(f"Failed to create run: {e}")
            return run_id
        finally:
            conn.close()

    def add_step(
        self,
        run_id: str,
        method: str,
        path: str,
        status_code: int = None,
        duration_ms: float = None,
        response_size: int = None,
        query_string: str = None,
        source_ip: str = None,
    ):
        """Record an HTTP step for a run."""
        conn = self._get_conn()
        try:
            # Get current step count
            row = conn.execute(
                "SELECT COALESCE(MAX(step_number), 0) as max_step FROM run_steps WHERE run_id = ?",
                (run_id,),
            ).fetchone()
            step_num = (row["max_step"] if row else 0) + 1

            conn.execute(
                """
                INSERT INTO run_steps
                (run_id, step_number, timestamp, method, path, query_string,
                 status_code, duration_ms, response_size_bytes, source_ip)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    run_id,
                    step_num,
                    datetime.now(timezone.utc).isoformat(),
                    method,
                    path,
                    query_string,
                    status_code,
                    duration_ms,
                    response_size,
                    source_ip,
                ),
            )

            # Update step count on the run
            conn.execute(
                "UPDATE model_benchmark_runs SET total_steps = ? WHERE run_id = ?",
                (step_num, run_id),
            )
            conn.commit()
        except Exception as e:
            logger.warning(f"Failed to add step to run {run_id}: {e}")
        finally:
            conn.close()

    def add_flag_attempt(
        self, run_id: str, benchmark_id: str, flag: str, result: str
    ):
        """Record a flag submission attempt."""
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT COALESCE(MAX(attempt_number), 0) as max FROM flag_attempts WHERE run_id = ?",
                (run_id,),
            ).fetchone()
            attempt_num = (row["max"] if row else 0) + 1

            conn.execute(
                """
                INSERT INTO flag_attempts
                (run_id, benchmark_id, attempt_number, flag_submitted, result, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    run_id,
                    benchmark_id,
                    attempt_num,
                    flag,
                    result,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )

            # Update flag count and capture status
            updates = {"flag_attempt_count": attempt_num}
            if result == "correct":
                updates["flag_captured"] = 1
                # Calculate time_to_flag
                run = self.get_run(run_id)
                if run and run.get("run_timestamp"):
                    try:
                        started = datetime.fromisoformat(run["run_timestamp"])
                        now = datetime.now(timezone.utc)
                        updates["time_to_flag_s"] = int(
                            (now - started).total_seconds()
                        )
                    except Exception:
                        pass

            set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
            conn.execute(
                f"UPDATE model_benchmark_runs SET {set_clause} WHERE run_id = ?",
                list(updates.values()) + [run_id],
            )
            conn.commit()
            logger.info(f"Flag attempt #{attempt_num} for run {run_id}: {result}")
        except Exception as e:
            logger.error(f"Failed to record flag attempt: {e}")
        finally:
            conn.close()

    def finalize_run(self, run_id: str, stop_reason: str = None):
        """Called on deprovision — calculates final metrics."""
        conn = self._get_conn()
        try:
            run = conn.execute(
                "SELECT * FROM model_benchmark_runs WHERE run_id = ?", (run_id,)
            ).fetchone()
            if not run:
                return

            now = datetime.now(timezone.utc)
            updates = {
                "status": "completed" if run["flag_captured"] else "failed",
                "stop_reason": stop_reason or "completed",
            }

            # Calculate total duration
            if run["run_timestamp"]:
                try:
                    started = datetime.fromisoformat(run["run_timestamp"])
                    updates["total_duration_s"] = int(
                        (now - started).total_seconds()
                    )
                except Exception:
                    pass

            # Count steps — update both total_steps and steps_taken
            # (steps_taken is used by comparison summary queries)
            step_count = conn.execute(
                "SELECT COUNT(*) as cnt FROM run_steps WHERE run_id = ?", (run_id,)
            ).fetchone()["cnt"]
            updates["total_steps"] = step_count
            updates["steps_taken"] = step_count
            updates["http_requests_made"] = step_count

            # Detect loops (same path requested 3+ times in a row)
            steps = conn.execute(
                "SELECT path FROM run_steps WHERE run_id = ? ORDER BY step_number",
                (run_id,),
            ).fetchall()
            loop_count = 0
            if len(steps) >= 3:
                for i in range(2, len(steps)):
                    if (
                        steps[i]["path"]
                        == steps[i - 1]["path"]
                        == steps[i - 2]["path"]
                    ):
                        loop_count += 1
            if loop_count > 0:
                updates["loop_detected"] = 1
                updates["loop_count"] = loop_count

            set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
            conn.execute(
                f"UPDATE model_benchmark_runs SET {set_clause} WHERE run_id = ?",
                list(updates.values()) + [run_id],
            )
            conn.commit()
            logger.info(
                f"Run {run_id} finalized: {updates.get('status')}, "
                f"{step_count} steps, {updates.get('total_duration_s', '?')}s"
            )
        except Exception as e:
            logger.error(f"Failed to finalize run {run_id}: {e}")
        finally:
            conn.close()

    def get_run(self, run_id: str) -> Optional[Dict]:
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT * FROM model_benchmark_runs WHERE run_id = ?", (run_id,)
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_run_steps(self, run_id: str) -> List[Dict]:
        conn = self._get_conn()
        try:
            rows = conn.execute(
                "SELECT * FROM run_steps WHERE run_id = ? ORDER BY step_number",
                (run_id,),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_run_flags(self, run_id: str) -> List[Dict]:
        conn = self._get_conn()
        try:
            rows = conn.execute(
                "SELECT * FROM flag_attempts WHERE run_id = ? ORDER BY attempt_number",
                (run_id,),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_active_run_for_benchmark(self, benchmark_id: str) -> Optional[Dict]:
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT * FROM model_benchmark_runs "
                "WHERE benchmark_id = ? AND status = 'running' "
                "ORDER BY run_timestamp DESC LIMIT 1",
                (benchmark_id,),
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_active_run_by_session(self, session_id: str) -> Optional[Dict]:
        """Find the active run for a specific session."""
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT * FROM model_benchmark_runs "
                "WHERE session_id = ? AND status = 'running' "
                "ORDER BY run_timestamp DESC LIMIT 1",
                (session_id,),
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_active_run_by_port(self, port: int) -> Optional[Dict]:
        """Find the active run using a specific port (for step logging)."""
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT * FROM model_benchmark_runs "
                "WHERE port = ? AND status = 'running' "
                "ORDER BY run_timestamp DESC LIMIT 1",
                (port,),
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()


# ── Future: Non-HTTP Agent Action Tracking ──────────────────────────────
#
# Currently only HTTP requests through the nginx proxy are captured as
# run steps.  Agents also perform non-HTTP actions (reading source code,
# running scripts, MCP tool calls, reasoning decisions) that aren't tracked.
#
# Planned API:
#   POST /api/comparison/runs/<run_id>/action
#   {
#       "action_type": "read_file" | "run_script" | "mcp_tool" | "reasoning",
#       "target": "app.py",
#       "details": "Reading source for vulns",
#       "duration_ms": 120
#   }
#
# This would go into a `run_actions` table (separate from run_steps which
# tracks HTTP only) and surface in the run detail modal alongside the
# HTTP timeline.
#
# Prerequisites:
#   - Agent prompts with self-reporting instructions
#   - MCP tool call logging (partially built in strike7_mcp_server.py)
#   - An "agent report" endpoint on the orchestrator
