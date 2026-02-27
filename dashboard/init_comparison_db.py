"""
Initialize the multi-model comparison database.

Creates tables, indexes, and seeds model pricing data.
Uses a schema_version table for future migration support.

Run standalone:  python dashboard/init_comparison_db.py
Also auto-initialized on import by comparison_routes.py

SCHEMA_CHANGELOG:
  v1 — Initial schema: benchmark_models, model_benchmark_runs, pil_training_data view
  v2 — Product evaluation framework: product_name/underlying_model/campaign_id/failure_stage
       columns on runs; benchmark_campaigns table; campaign+product indexes; data backfill
"""
import sqlite3
import os

DB_PATH = os.environ.get(
    'COMPARISON_DB_PATH',
    os.path.join(os.path.dirname(__file__), 'data', 'model_benchmarks.db')
)

CURRENT_SCHEMA_VERSION = 2


def _get_schema_version(conn):
    """Get current schema version, or 0 if table doesn't exist."""
    try:
        row = conn.execute("SELECT version FROM schema_version").fetchone()
        return row[0] if row else 0
    except sqlite3.OperationalError:
        return 0


def _apply_migrations(conn):
    """Apply incremental schema migrations based on current version."""
    version = _get_schema_version(conn)

    if version < 1:
        _migrate_v1(conn)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER NOT NULL
            )
        """)
        conn.execute("INSERT INTO schema_version (version) VALUES (1)")

    if version < 2:
        _migrate_v2(conn)
        conn.execute("UPDATE schema_version SET version = 2")


def _migrate_v1(conn):
    """Version 1: Initial schema with models, runs, and PIL view."""

    # --- Model registry with pricing ---
    conn.execute("""
        CREATE TABLE IF NOT EXISTS benchmark_models (
            model_name TEXT PRIMARY KEY,
            provider TEXT NOT NULL,
            display_name TEXT NOT NULL,
            tier TEXT NOT NULL,
            input_cost_per_1m REAL,
            output_cost_per_1m REAL,
            access_method TEXT DEFAULT 'cli',
            is_active INTEGER DEFAULT 1,
            notes TEXT
        )
    """)

    # --- Individual benchmark runs ---
    conn.execute("""
        CREATE TABLE IF NOT EXISTS model_benchmark_runs (
            run_id TEXT PRIMARY KEY,
            run_timestamp TEXT NOT NULL,
            benchmark_id TEXT NOT NULL,
            benchmark_name TEXT,
            difficulty_tier TEXT NOT NULL,
            vuln_category TEXT,
            provider TEXT NOT NULL,
            model_name TEXT NOT NULL,
            model_tier TEXT,
            execution_method TEXT DEFAULT 'cli',
            flag_captured INTEGER NOT NULL DEFAULT 0,
            flag_value TEXT,
            time_to_flag_s REAL,
            total_duration_s REAL NOT NULL,
            attempt_number INTEGER NOT NULL DEFAULT 1,
            total_tokens INTEGER,
            input_tokens INTEGER,
            output_tokens INTEGER,
            token_source TEXT DEFAULT 'estimated',
            steps_taken INTEGER,
            http_requests_made INTEGER,
            cost_usd REAL,
            cost_source TEXT DEFAULT 'estimated',
            failure_reason TEXT,
            failure_details TEXT,
            loop_detected INTEGER DEFAULT 0,
            loop_count INTEGER DEFAULT 0,
            container_port INTEGER,
            system_prompt_hash TEXT,
            agent_transcript TEXT,
            notes TEXT
        )
    """)

    # --- Indexes on frequently queried columns ---
    conn.execute("CREATE INDEX IF NOT EXISTS idx_runs_benchmark ON model_benchmark_runs(benchmark_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_runs_provider ON model_benchmark_runs(provider)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_runs_model ON model_benchmark_runs(model_name)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_runs_tier ON model_benchmark_runs(difficulty_tier)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_runs_composite ON model_benchmark_runs(provider, model_name, benchmark_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_runs_timestamp ON model_benchmark_runs(run_timestamp)")

    # --- PIL (Prediction Intelligence Layer) training data export ---
    # Filters: successful captures + runs lasting >30s (excludes trivial failures/instant timeouts)
    # Consumer: ML pipeline for benchmark difficulty prediction (not yet implemented)
    # Note: includes v2 columns (product_name etc.) — safe for fresh DBs since
    # _migrate_v2 ALTER TABLEs run before this view is queried.
    conn.execute("""
        CREATE VIEW IF NOT EXISTS pil_training_data AS
        SELECT
            r.benchmark_id, r.difficulty_tier, r.vuln_category,
            r.provider, r.model_name, r.model_tier,
            r.flag_captured, r.time_to_flag_s, r.total_tokens,
            r.steps_taken, r.cost_usd, r.loop_detected,
            r.loop_count, r.failure_reason, r.attempt_number,
            r.product_name, r.underlying_model, r.campaign_id,
            r.failure_stage, r.total_duration_s,
            m.input_cost_per_1m, m.output_cost_per_1m
        FROM model_benchmark_runs r
        LEFT JOIN benchmark_models m ON r.model_name = m.model_name
        WHERE r.flag_captured = 1 OR r.total_duration_s > 30
    """)


def _migrate_v2(conn):
    """Version 2: Product evaluation framework.

    Adds product/campaign tracking columns to runs, creates campaigns table,
    and backfills product_name for existing data.
    """

    # --- New columns on model_benchmark_runs ---
    for col_def in [
        "product_name TEXT",
        "underlying_model TEXT",
        "campaign_id TEXT",
        "failure_stage TEXT",
    ]:
        try:
            conn.execute(f"ALTER TABLE model_benchmark_runs ADD COLUMN {col_def}")
        except sqlite3.OperationalError:
            pass  # Column already exists (idempotent)

    # --- Campaign management table ---
    conn.execute("""
        CREATE TABLE IF NOT EXISTS benchmark_campaigns (
            campaign_id      TEXT PRIMARY KEY,
            campaign_name    TEXT NOT NULL,
            product_name     TEXT NOT NULL,
            product_version  TEXT,
            underlying_model TEXT,
            started_at       TEXT NOT NULL,
            completed_at     TEXT,
            status           TEXT DEFAULT 'running',
            target_tier      TEXT,
            target_benchmarks TEXT,
            config           TEXT,
            notes            TEXT
        )
    """)

    # --- New indexes ---
    conn.execute("CREATE INDEX IF NOT EXISTS idx_runs_campaign ON model_benchmark_runs(campaign_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_runs_product ON model_benchmark_runs(product_name)")

    # --- Backfill product_name for existing data ---
    conn.execute("""
        UPDATE model_benchmark_runs SET product_name = 'strike7-cyberchat'
        WHERE model_name = 'strike7-cyberchat' AND product_name IS NULL
    """)
    conn.execute("""
        UPDATE model_benchmark_runs SET product_name = 'strike7-cli-runner'
        WHERE model_name IN ('claude-sonnet-4.5','gemini-2.5-flash','gemini-2.5-pro',
                             'claude-opus-4.6','gpt-4.1-mini','gpt-4.1')
        AND product_name IS NULL
    """)

    # --- Upgrade PIL view to include v2 columns ---
    conn.execute("DROP VIEW IF EXISTS pil_training_data")
    conn.execute("""
        CREATE VIEW pil_training_data AS
        SELECT
            r.benchmark_id, r.difficulty_tier, r.vuln_category,
            r.provider, r.model_name, r.model_tier,
            r.flag_captured, r.time_to_flag_s, r.total_tokens,
            r.steps_taken, r.cost_usd, r.loop_detected,
            r.loop_count, r.failure_reason, r.attempt_number,
            r.product_name, r.underlying_model, r.campaign_id,
            r.failure_stage, r.total_duration_s,
            m.input_cost_per_1m, m.output_cost_per_1m
        FROM model_benchmark_runs r
        LEFT JOIN benchmark_models m ON r.model_name = m.model_name
        WHERE r.flag_captured = 1 OR r.total_duration_s > 30
    """)


# --- Seed data: known model pricing ---
SEED_MODELS = [
    ('gemini-2.5-flash', 'google', 'Gemini 2.5 Flash', 'flash', 0.075, 0.30, 'cli', 1, None),
    ('gemini-2.5-pro', 'google', 'Gemini 2.5 Pro', 'pro', 1.25, 10.00, 'cli', 1, None),
    ('claude-sonnet-4.5', 'anthropic', 'Claude Sonnet 4.5', 'standard', 3.00, 15.00, 'cli', 1, None),
    ('claude-opus-4.6', 'anthropic', 'Claude Opus 4.6', 'flagship', 15.00, 75.00, 'cli', 1, None),
    ('gpt-4.1-mini', 'openai', 'GPT-4.1 Mini', 'budget', 0.40, 1.60, 'cli', 1, None),
    ('gpt-4.1', 'openai', 'GPT-4.1', 'standard', 2.00, 8.00, 'cli', 1, None),
]


def _seed_models(conn):
    """Insert default models if they don't already exist."""
    conn.executemany("""
        INSERT OR IGNORE INTO benchmark_models
            (model_name, provider, display_name, tier,
             input_cost_per_1m, output_cost_per_1m, access_method, is_active, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, SEED_MODELS)


def init_db(db_path=None):
    """Initialize the comparison database with schema and seed data.

    Args:
        db_path: Override DB path (for testing). Defaults to DB_PATH.
    """
    path = db_path or DB_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)

    conn = sqlite3.connect(path)
    conn.execute("PRAGMA journal_mode=WAL;")

    _apply_migrations(conn)
    _seed_models(conn)

    conn.commit()
    conn.close()
    print(f"[+] Comparison database initialized at {path} (schema v{CURRENT_SCHEMA_VERSION})")


if __name__ == '__main__':
    init_db()
