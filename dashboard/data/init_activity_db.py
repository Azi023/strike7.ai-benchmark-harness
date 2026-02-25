"""Initialize the agent activity database."""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'agent_activity.db')


def init_db():
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
    print(f"[+] Activity database initialized at {DB_PATH}")


if __name__ == '__main__':
    init_db()
