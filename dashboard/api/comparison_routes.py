"""
Flask Blueprint for multi-model benchmark comparison endpoints.

Provides CRUD for comparison runs, model registry, summary aggregation,
campaign management, and capability matrix generation.
"""
import sqlite3
import os
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from api.activity_logger import log_activity

comparison_bp = Blueprint('comparison', __name__)

DB_PATH = os.environ.get(
    'COMPARISON_DB_PATH',
    os.path.join(os.path.dirname(__file__), '..', 'data', 'model_benchmarks.db')
)

VALID_TIERS = {'EASY', 'MED', 'HARD', 'VHARD', 'CVE'}
REQUIRED_RUN_FIELDS = ['benchmark_id', 'difficulty_tier', 'provider', 'model_name', 'total_duration_s']

# Allowed filter fields for list/summary queries
_FILTER_FIELDS = (
    'benchmark_id', 'provider', 'model_name', 'difficulty_tier',
    'campaign_id', 'product_name',
)

# Dynamic field spec: (column_name, data_key, default)
# Adding a column = adding one tuple here + ALTER TABLE migration
_RUN_FIELDS = [
    ('run_id', 'run_id', None),
    ('run_timestamp', 'run_timestamp', None),
    ('benchmark_id', 'benchmark_id', None),
    ('benchmark_name', 'benchmark_name', None),
    ('difficulty_tier', 'difficulty_tier', None),
    ('vuln_category', 'vuln_category', None),
    ('provider', 'provider', None),
    ('model_name', 'model_name', None),
    ('model_tier', 'model_tier', None),
    ('execution_method', 'execution_method', 'cli'),
    ('flag_captured', 'flag_captured', 0),
    ('flag_value', 'flag_value', None),
    ('time_to_flag_s', 'time_to_flag_s', None),
    ('total_duration_s', 'total_duration_s', None),
    ('attempt_number', 'attempt_number', 1),
    ('total_tokens', 'total_tokens', None),
    ('input_tokens', 'input_tokens', None),
    ('output_tokens', 'output_tokens', None),
    ('token_source', 'token_source', 'estimated'),
    ('steps_taken', 'steps_taken', None),
    ('http_requests_made', 'http_requests_made', None),
    ('cost_usd', 'cost_usd', None),
    ('cost_source', 'cost_source', 'estimated'),
    ('failure_reason', 'failure_reason', None),
    ('failure_details', 'failure_details', None),
    ('loop_detected', 'loop_detected', 0),
    ('loop_count', 'loop_count', 0),
    ('container_port', 'container_port', None),
    ('system_prompt_hash', 'system_prompt_hash', None),
    ('agent_transcript', 'agent_transcript', None),
    ('notes', 'notes', None),
    # v2 columns
    ('product_name', 'product_name', None),
    ('underlying_model', 'underlying_model', None),
    ('campaign_id', 'campaign_id', None),
    ('failure_stage', 'failure_stage', None),
]

# Fields returned by list queries (excludes large payloads: failure_details, agent_transcript)
_LIST_COLUMNS = [
    col for col, _, _ in _RUN_FIELDS
    if col not in ('failure_details', 'agent_transcript')
]

# Failure taxonomy enums
VALID_FAILURE_REASONS = {
    'vuln_not_identified', 'wrong_attack_vector', 'exploit_failed',
    'defense_not_bypassed', 'payload_incorrect', 'flag_not_found',
    'flag_wrong_format', 'flag_rejected', 'tool_missing', 'tool_error',
    'container_error', 'timeout', 'loop_detected', 'context_exhausted',
    'hallucinated_flag', 'gave_up',
}

VALID_FAILURE_STAGES = {
    'recon', 'analysis', 'exploitation', 'flag_extraction', 'flag_submission',
}

# Text field size limits
_TEXT_LIMITS = {
    'notes': 10_000,
    'failure_details': 5_000,
    'agent_transcript': 500_000,
}

# Default and max pagination limits
DEFAULT_LIMIT = 50
MAX_LIMIT = 500


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

@contextmanager
def _get_db():
    """Context manager for SQLite connections — auto-closes on exit."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def _build_filters(allowed_fields=_FILTER_FIELDS):
    """Build WHERE clause from request.args for allowed fields."""
    conditions, params = [], []
    for field in allowed_fields:
        value = request.args.get(field)
        if value:
            conditions.append(f"{field} = ?")
            params.append(value)
    return " AND ".join(conditions) or "1=1", params


def _ensure_db():
    """Create tables if they don't exist (auto-init on import)."""
    from init_comparison_db import init_db
    init_db(db_path=DB_PATH)


def _calculate_cost_for_run(data, conn):
    """Calculate cost_usd from token counts and model pricing.

    Delegates to token_estimator.calculate_cost() — single source of truth.

    Returns (cost_usd, cost_source) tuple.
    """
    from utils.token_estimator import calculate_cost

    total_tokens = data.get('total_tokens')
    input_tokens = data.get('input_tokens')
    output_tokens = data.get('output_tokens')
    model_name = data.get('model_name')

    if not total_tokens and not (input_tokens and output_tokens):
        return None, 'unavailable'

    result = calculate_cost(total_tokens, input_tokens, output_tokens, model_name)
    return result.get('cost_usd'), result.get('cost_source', 'unavailable')


def _validate_run_data(data):
    """Validate required fields and value constraints for a run.

    Returns list of error strings (empty if valid).
    """
    errors = []

    for field in REQUIRED_RUN_FIELDS:
        if field not in data or data[field] is None:
            errors.append(f"Missing required field: '{field}'")

    if not errors:
        tier = data.get('difficulty_tier')
        if tier not in VALID_TIERS:
            errors.append(
                f"Invalid difficulty_tier: '{tier}'. Must be one of: {', '.join(sorted(VALID_TIERS))}"
            )

        flag = data.get('flag_captured')
        if flag is not None and flag not in (0, 1, True, False):
            errors.append(f"Invalid flag_captured: '{flag}'. Must be 0 or 1")

        duration = data.get('total_duration_s')
        if duration is not None:
            try:
                if float(duration) < 0:
                    errors.append("total_duration_s must be non-negative")
            except (TypeError, ValueError):
                errors.append(f"total_duration_s must be a number, got: '{duration}'")

        attempt = data.get('attempt_number')
        if attempt is not None:
            try:
                if int(attempt) < 1:
                    errors.append("attempt_number must be >= 1")
            except (TypeError, ValueError):
                errors.append(f"attempt_number must be an integer, got: '{attempt}'")

        token_source = data.get('token_source')
        if token_source is not None:
            from utils.provider_config import VALID_TOKEN_SOURCES
            if token_source not in VALID_TOKEN_SOURCES:
                errors.append(
                    f"Invalid token_source: '{token_source}'. "
                    f"Must be one of: {', '.join(sorted(VALID_TOKEN_SOURCES))}"
                )

        failure_reason = data.get('failure_reason')
        if failure_reason and failure_reason not in VALID_FAILURE_REASONS:
            errors.append(
                f"Invalid failure_reason: '{failure_reason}'. "
                f"Must be one of: {sorted(VALID_FAILURE_REASONS)}"
            )

        failure_stage = data.get('failure_stage')
        if failure_stage and failure_stage not in VALID_FAILURE_STAGES:
            errors.append(
                f"Invalid failure_stage: '{failure_stage}'. "
                f"Must be one of: {sorted(VALID_FAILURE_STAGES)}"
            )

        for field, max_len in _TEXT_LIMITS.items():
            val = data.get(field)
            if val and len(val) > max_len:
                errors.append(f"{field} exceeds max length ({max_len} chars)")

    return errors


# ---------------------------------------------------------------------------
# Auto-initialize DB on import (matches activity_logger.py pattern)
# ---------------------------------------------------------------------------
try:
    _ensure_db()
except Exception as e:
    print(f"[!] Warning: Could not auto-initialize comparison DB: {e}")


# ---------------------------------------------------------------------------
# Run endpoints
# ---------------------------------------------------------------------------

@comparison_bp.route('/api/comparison/runs', methods=['POST'])
def create_run():
    """Record a new benchmark comparison run."""
    data = request.get_json()
    if not data:
        return jsonify({'status': 'error', 'message': 'Request body must be JSON'}), 400

    errors = _validate_run_data(data)
    if errors:
        return jsonify({'status': 'error', 'message': 'Validation failed', 'errors': errors}), 400

    run_id = data.get('run_id') or uuid.uuid4().hex
    run_timestamp = data.get('run_timestamp') or datetime.now(timezone.utc).isoformat()

    with _get_db() as conn:
        try:
            # Auto-calculate cost if not provided
            cost_usd = data.get('cost_usd')
            cost_source = data.get('cost_source', 'estimated')
            if cost_usd is None:
                cost_usd, cost_source = _calculate_cost_for_run(data, conn)

            flag_captured = 1 if data.get('flag_captured') else 0

            # Build INSERT dynamically from _RUN_FIELDS
            # Override computed fields in data for the insert
            insert_data = dict(data)
            insert_data['run_id'] = run_id
            insert_data['run_timestamp'] = run_timestamp
            insert_data['flag_captured'] = flag_captured
            insert_data['cost_usd'] = cost_usd
            insert_data['cost_source'] = cost_source

            columns = [col for col, _, _ in _RUN_FIELDS]
            values = [insert_data.get(key, default) for _, key, default in _RUN_FIELDS]
            placeholders = ', '.join(['?'] * len(columns))
            col_names = ', '.join(columns)

            conn.execute(
                f"INSERT INTO model_benchmark_runs ({col_names}) VALUES ({placeholders})",
                values,
            )
            conn.commit()

            # Sync to activity logger so /agent-feed sees these runs
            _log_run_activity(data, run_id, flag_captured, cost_usd)

            # Fetch the created run to return
            row = conn.execute(
                "SELECT * FROM model_benchmark_runs WHERE run_id = ?", (run_id,)
            ).fetchone()

            return jsonify({
                'status': 'success',
                'message': 'Run recorded',
                'run': dict(row),
            }), 201

        except sqlite3.IntegrityError:
            return jsonify({'status': 'error', 'message': f'Duplicate run_id: {run_id}'}), 409
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500


def _log_run_activity(data, run_id, flag_captured, cost_usd):
    """Emit activity events for a comparison run so /agent-feed sees it."""
    benchmark_id = data['benchmark_id']
    session_id = f"comparison-{run_id}"

    # Common fields for all events
    common = {
        'model': data.get('model_name'),
        'provider': data.get('provider'),
        'source': 'comparison',
        'product_name': data.get('product_name'),
        'campaign_id': data.get('campaign_id'),
    }

    # benchmark_start
    log_activity('benchmark_start', benchmark_id, {
        **common,
        'port': data.get('container_port'),
    }, severity='info', session_id=session_id)

    # flag result
    if flag_captured:
        log_activity('flag_correct', benchmark_id, {
            **common,
            'time_to_capture': data.get('time_to_flag_s'),
            'attempts': data.get('attempt_number', 1),
            'cost_usd': cost_usd,
            'total_tokens': data.get('total_tokens'),
        }, severity='success', session_id=session_id)
    else:
        log_activity('flag_incorrect', benchmark_id, {
            **common,
            'message': data.get('failure_reason', 'Flag not captured'),
            'attempts': data.get('attempt_number', 1),
            'cost_usd': cost_usd,
            'total_tokens': data.get('total_tokens'),
        }, severity='error', session_id=session_id)

    # benchmark_stop
    log_activity('benchmark_stop', benchmark_id, {
        **common,
        'runtime_seconds': data.get('total_duration_s'),
    }, severity='info', session_id=session_id)


@comparison_bp.route('/api/comparison/sync-activity', methods=['POST'])
def sync_activity():
    """Backfill activity logger with all existing comparison runs.

    One-time sync: reads model_benchmark_runs and emits corresponding
    flag_correct / flag_incorrect events so /agent-feed is up to date.
    """
    with _get_db() as conn:
        try:
            cursor = conn.execute(
                "SELECT * FROM model_benchmark_runs ORDER BY run_timestamp ASC"
            )
            synced = 0
            while True:
                batch = cursor.fetchmany(100)
                if not batch:
                    break
                for row in batch:
                    r = dict(row)
                    _log_run_activity(r, r['run_id'], r['flag_captured'], r.get('cost_usd'))
                    synced += 1

            return jsonify({
                'status': 'success',
                'message': f'Synced {synced} runs to activity logger',
                'synced': synced,
            })

        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500


@comparison_bp.route('/api/comparison/runs', methods=['GET'])
def list_runs():
    """List benchmark runs with optional filters and pagination.

    Query params: benchmark_id, provider, model_name, difficulty_tier,
                  campaign_id, product_name, flag_captured, limit, offset
    """
    limit = min(request.args.get('limit', DEFAULT_LIMIT, type=int), MAX_LIMIT)
    offset = request.args.get('offset', 0, type=int)

    where_clause, params = _build_filters()

    flag_captured = request.args.get('flag_captured')
    if flag_captured is not None:
        where_clause += " AND flag_captured = ?"
        params.append(1 if flag_captured.lower() in ('1', 'true') else 0)

    columns = ", ".join(_LIST_COLUMNS)

    with _get_db() as conn:
        try:
            total = conn.execute(
                f"SELECT COUNT(*) FROM model_benchmark_runs WHERE {where_clause}",
                params
            ).fetchone()[0]

            rows = conn.execute(
                f"SELECT {columns} FROM model_benchmark_runs "
                f"WHERE {where_clause} ORDER BY run_timestamp DESC LIMIT ? OFFSET ?",
                params + [limit, offset]
            ).fetchall()

            return jsonify({
                'status': 'success',
                'runs': [dict(r) for r in rows],
                'total': total,
                'limit': limit,
                'offset': offset,
            })

        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500


@comparison_bp.route('/api/comparison/runs/<run_id>', methods=['GET'])
def get_run(run_id):
    """Get full details for a specific run (includes agent_transcript)."""
    with _get_db() as conn:
        row = conn.execute(
            "SELECT * FROM model_benchmark_runs WHERE run_id = ?", (run_id,)
        ).fetchone()

    if not row:
        return jsonify({'status': 'error', 'message': f'Run not found: {run_id}'}), 404

    return jsonify({'status': 'success', 'run': dict(row)})


@comparison_bp.route('/api/comparison/runs/<run_id>', methods=['DELETE'])
def delete_run(run_id):
    """Delete a run. Requires ?confirm=true to prevent accidental deletion."""
    confirm = request.args.get('confirm', '').lower()
    if confirm != 'true':
        return jsonify({
            'status': 'error',
            'message': 'Pass ?confirm=true to delete this run',
        }), 400

    with _get_db() as conn:
        cursor = conn.execute(
            "DELETE FROM model_benchmark_runs WHERE run_id = ?", (run_id,)
        )
        conn.commit()
        deleted = cursor.rowcount

    if deleted == 0:
        return jsonify({'status': 'error', 'message': f'Run not found: {run_id}'}), 404

    return jsonify({'status': 'success', 'message': f'Deleted run {run_id}'})


# ---------------------------------------------------------------------------
# Summary endpoint (computed on read, no summary table — Issue #1)
# ---------------------------------------------------------------------------

@comparison_bp.route('/api/comparison/summary', methods=['GET'])
def get_summary():
    """Aggregated summary data, computed from runs on each request.

    Optional filters: provider, model_name, difficulty_tier, benchmark_id,
                      campaign_id, product_name
    """
    where_clause, params = _build_filters()

    # Add product_name to GROUP BY when filtering by product
    group_cols = "provider, model_name, difficulty_tier, benchmark_id"
    if request.args.get('product_name'):
        group_cols = "product_name, " + group_cols

    with _get_db() as conn:
        try:
            rows = conn.execute(f"""
                SELECT
                    {'product_name,' if request.args.get('product_name') else ''}
                    provider,
                    model_name,
                    difficulty_tier,
                    benchmark_id,
                    COUNT(*) as total_runs,
                    SUM(flag_captured) as successful_runs,
                    ROUND(CAST(SUM(flag_captured) AS REAL) / COUNT(*), 4) as pass_rate,
                    ROUND(AVG(CASE WHEN flag_captured = 1 THEN time_to_flag_s END), 2) as avg_time_s,
                    ROUND(MIN(CASE WHEN flag_captured = 1 THEN time_to_flag_s END), 2) as min_time_s,
                    ROUND(MAX(CASE WHEN flag_captured = 1 THEN time_to_flag_s END), 2) as max_time_s,
                    ROUND(AVG(total_tokens), 0) as avg_tokens,
                    ROUND(AVG(steps_taken), 1) as avg_steps,
                    ROUND(AVG(cost_usd), 6) as avg_cost_usd,
                    ROUND(SUM(cost_usd), 6) as total_cost_usd,
                    ROUND(CAST(SUM(loop_detected) AS REAL) / COUNT(*), 4) as loop_rate
                FROM model_benchmark_runs
                WHERE {where_clause}
                GROUP BY {group_cols}
                ORDER BY {group_cols}
            """, params).fetchall()

            summaries = []
            for row in rows:
                summary = dict(row)
                summary['successful_runs'] = summary['successful_runs'] or 0
                summaries.append(summary)

            return jsonify({
                'status': 'success',
                'summaries': summaries,
                'total_groups': len(summaries),
            })

        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500


# ---------------------------------------------------------------------------
# Matrix endpoint (single GROUP BY, pivot in Python — Issue #14)
# ---------------------------------------------------------------------------

@comparison_bp.route('/api/comparison/matrix', methods=['GET'])
def get_matrix():
    """Capability heatmap data: model x benchmark grid.

    Optional filters: product_name, campaign_id

    Returns a matrix where each cell contains pass_rate, avg_time, total_runs
    for a (model, benchmark) pair.
    """
    where_clause, params = _build_filters(('product_name', 'campaign_id'))

    with _get_db() as conn:
        try:
            rows = conn.execute(f"""
                SELECT
                    model_name,
                    provider,
                    benchmark_id,
                    difficulty_tier,
                    COUNT(*) as total_runs,
                    SUM(flag_captured) as successes,
                    ROUND(CAST(SUM(flag_captured) AS REAL) / COUNT(*), 4) as pass_rate,
                    ROUND(AVG(CASE WHEN flag_captured = 1 THEN time_to_flag_s END), 2) as avg_time_s,
                    ROUND(AVG(cost_usd), 6) as avg_cost_usd
                FROM model_benchmark_runs
                WHERE {where_clause}
                GROUP BY model_name, benchmark_id
                ORDER BY model_name, benchmark_id
            """, params).fetchall()

            # Pivot into nested dict: {model_name: {benchmark_id: {...stats}}}
            matrix = {}
            models = set()
            benchmarks = set()

            for row in rows:
                r = dict(row)
                model = r['model_name']
                bench = r['benchmark_id']
                models.add(model)
                benchmarks.add(bench)

                if model not in matrix:
                    matrix[model] = {}

                matrix[model][bench] = {
                    'provider': r['provider'],
                    'difficulty_tier': r['difficulty_tier'],
                    'total_runs': r['total_runs'],
                    'successes': r['successes'] or 0,
                    'pass_rate': r['pass_rate'],
                    'avg_time_s': r['avg_time_s'],
                    'avg_cost_usd': r['avg_cost_usd'],
                }

            return jsonify({
                'status': 'success',
                'matrix': matrix,
                'models': sorted(models),
                'benchmarks': sorted(benchmarks),
            })

        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500


# ---------------------------------------------------------------------------
# Enums endpoint
# ---------------------------------------------------------------------------

@comparison_bp.route('/api/comparison/enums', methods=['GET'])
def get_enums():
    """Return valid enum values for failure_reason, failure_stage, tiers."""
    return jsonify({
        'status': 'success',
        'failure_reasons': sorted(VALID_FAILURE_REASONS),
        'failure_stages': sorted(VALID_FAILURE_STAGES),
        'difficulty_tiers': sorted(VALID_TIERS),
    })


# ---------------------------------------------------------------------------
# Campaign endpoints
# ---------------------------------------------------------------------------

@comparison_bp.route('/api/comparison/campaigns', methods=['POST'])
def create_campaign():
    """Create a new benchmark campaign."""
    data = request.get_json()
    if not data:
        return jsonify({'status': 'error', 'message': 'Request body must be JSON'}), 400

    campaign_name = data.get('campaign_name')
    product_name = data.get('product_name')
    if not campaign_name or not product_name:
        return jsonify({
            'status': 'error',
            'message': 'Required fields: campaign_name, product_name',
        }), 400

    target_tier = data.get('target_tier', 'ALL')
    campaign_id = data.get('campaign_id') or f"{product_name}-{target_tier}-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6]}"
    started_at = data.get('started_at') or datetime.now(timezone.utc).isoformat()

    with _get_db() as conn:
        try:
            conn.execute("""
                INSERT INTO benchmark_campaigns (
                    campaign_id, campaign_name, product_name, product_version,
                    underlying_model, started_at, status, target_tier,
                    target_benchmarks, config, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                campaign_id, campaign_name, product_name, data.get('product_version'),
                data.get('underlying_model'), started_at, 'running', data.get('target_tier'),
                data.get('target_benchmarks'), data.get('config'), data.get('notes'),
            ))
            conn.commit()

            row = conn.execute(
                "SELECT * FROM benchmark_campaigns WHERE campaign_id = ?",
                (campaign_id,)
            ).fetchone()

            return jsonify({
                'status': 'success',
                'message': 'Campaign created',
                'campaign': dict(row),
            }), 201

        except sqlite3.IntegrityError:
            return jsonify({
                'status': 'error',
                'message': f'Duplicate campaign_id: {campaign_id}',
            }), 409
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500


@comparison_bp.route('/api/comparison/campaigns', methods=['GET'])
def list_campaigns():
    """List campaigns with computed aggregates from runs."""
    conditions, params = [], []

    for field in ('product_name', 'status'):
        value = request.args.get(field)
        if value:
            conditions.append(f"c.{field} = ?")
            params.append(value)

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    with _get_db() as conn:
        try:
            rows = conn.execute(f"""
                SELECT
                    c.*,
                    COUNT(r.run_id) as total_runs,
                    COALESCE(SUM(r.flag_captured), 0) as solved,
                    COUNT(r.run_id) - COALESCE(SUM(r.flag_captured), 0) as failed,
                    CASE WHEN COUNT(r.run_id) > 0
                        THEN ROUND(CAST(SUM(r.flag_captured) AS REAL) / COUNT(r.run_id), 4)
                        ELSE 0 END as pass_rate,
                    ROUND(COALESCE(SUM(r.cost_usd), 0), 6) as total_cost
                FROM benchmark_campaigns c
                LEFT JOIN model_benchmark_runs r ON c.campaign_id = r.campaign_id
                WHERE {where_clause}
                GROUP BY c.campaign_id
                ORDER BY c.started_at DESC
            """, params).fetchall()

            return jsonify({
                'status': 'success',
                'campaigns': [dict(r) for r in rows],
                'total': len(rows),
            })

        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500


@comparison_bp.route('/api/comparison/campaigns/<campaign_id>', methods=['GET'])
def get_campaign(campaign_id):
    """Get a single campaign with computed summary stats."""
    with _get_db() as conn:
        row = conn.execute("""
            SELECT
                c.*,
                COUNT(r.run_id) as total_runs,
                COALESCE(SUM(r.flag_captured), 0) as solved,
                COUNT(r.run_id) - COALESCE(SUM(r.flag_captured), 0) as failed,
                CASE WHEN COUNT(r.run_id) > 0
                    THEN ROUND(CAST(SUM(r.flag_captured) AS REAL) / COUNT(r.run_id), 4)
                    ELSE 0 END as pass_rate,
                ROUND(COALESCE(SUM(r.cost_usd), 0), 6) as total_cost,
                ROUND(AVG(CASE WHEN r.flag_captured = 1 THEN r.time_to_flag_s END), 2) as avg_time_s
            FROM benchmark_campaigns c
            LEFT JOIN model_benchmark_runs r ON c.campaign_id = r.campaign_id
            WHERE c.campaign_id = ?
            GROUP BY c.campaign_id
        """, (campaign_id,)).fetchone()

    if not row:
        return jsonify({'status': 'error', 'message': f'Campaign not found: {campaign_id}'}), 404

    return jsonify({'status': 'success', 'campaign': dict(row)})


@comparison_bp.route('/api/comparison/campaigns/<campaign_id>', methods=['PATCH'])
def update_campaign(campaign_id):
    """Update campaign status or notes (partial update)."""
    data = request.get_json()
    if not data:
        return jsonify({'status': 'error', 'message': 'Request body must be JSON'}), 400

    allowed = {'status', 'completed_at', 'notes'}
    updates = {k: v for k, v in data.items() if k in allowed}
    if not updates:
        return jsonify({
            'status': 'error',
            'message': f'No valid fields to update. Allowed: {sorted(allowed)}',
        }), 400

    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [campaign_id]

    with _get_db() as conn:
        cursor = conn.execute(
            f"UPDATE benchmark_campaigns SET {set_clause} WHERE campaign_id = ?",
            values,
        )
        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({'status': 'error', 'message': f'Campaign not found: {campaign_id}'}), 404

        row = conn.execute(
            "SELECT * FROM benchmark_campaigns WHERE campaign_id = ?",
            (campaign_id,)
        ).fetchone()

    return jsonify({'status': 'success', 'campaign': dict(row)})


# ---------------------------------------------------------------------------
# Prompt rendering endpoint
# ---------------------------------------------------------------------------

@comparison_bp.route('/api/comparison/failure-analysis', methods=['GET'])
def get_failure_analysis():
    """Failure funnel analysis: where agents fail across the attack pipeline.

    Optional filters: provider, model_name, difficulty_tier, benchmark_id,
                      campaign_id, product_name

    Returns stage funnel counts and top failure reasons with stage context.
    """
    where_clause, params = _build_filters()

    with _get_db() as conn:
        try:
            # Stage funnel — ordered pipeline counts
            stage_rows = conn.execute(f"""
                SELECT failure_stage, COUNT(*) as count
                FROM model_benchmark_runs
                WHERE flag_captured = 0 AND failure_stage IS NOT NULL AND {where_clause}
                GROUP BY failure_stage
            """, params).fetchall()

            # Reason breakdown — with stage context
            reason_rows = conn.execute(f"""
                SELECT failure_reason, failure_stage, COUNT(*) as count
                FROM model_benchmark_runs
                WHERE flag_captured = 0 AND failure_reason IS NOT NULL AND {where_clause}
                GROUP BY failure_reason, failure_stage
                ORDER BY count DESC
            """, params).fetchall()

            # Total failures count
            total_failures = conn.execute(f"""
                SELECT COUNT(*) FROM model_benchmark_runs
                WHERE flag_captured = 0 AND {where_clause}
            """, params).fetchone()[0]

            # Build stage funnel in pipeline order
            stage_counts = {r['failure_stage']: r['count'] for r in stage_rows}
            pipeline_order = ['recon', 'analysis', 'exploitation', 'flag_extraction', 'flag_submission']
            stage_funnel = [
                {'stage': stage, 'count': stage_counts.get(stage, 0)}
                for stage in pipeline_order
                if stage_counts.get(stage, 0) > 0
            ]

            reason_breakdown = [
                {'reason': r['failure_reason'], 'stage': r['failure_stage'], 'count': r['count']}
                for r in reason_rows
            ]

            return jsonify({
                'status': 'success',
                'stage_funnel': stage_funnel,
                'reason_breakdown': reason_breakdown,
                'total_failures': total_failures,
            })

        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500


@comparison_bp.route('/api/comparison/prompt', methods=['GET'])
def get_prompt():
    """Render a provider-tuned benchmark prompt with all variables filled in.

    Query params: benchmark_id (required), provider (required), model_name (required),
                  attempt_number, model_tier, vps_host
    """
    benchmark_id = request.args.get('benchmark_id')
    provider = request.args.get('provider')
    model_name = request.args.get('model_name')

    if not all([benchmark_id, provider, model_name]):
        return jsonify({
            'status': 'error',
            'message': 'Required params: benchmark_id, provider, model_name',
        }), 400

    attempt_number = request.args.get('attempt_number', 1, type=int)
    model_tier = request.args.get('model_tier')
    vps_host = request.args.get('vps_host', 'localhost')

    # Try to resolve port and name from benchmark registry
    port = None
    benchmark_name = None
    try:
        import json as _json
        benchmarks_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'benchmarks.json')
        if os.path.exists(benchmarks_path):
            with open(benchmarks_path, 'r') as f:
                benchmarks = _json.load(f)
            for b in benchmarks:
                if b.get('id') == benchmark_id:
                    port = b.get('port')
                    benchmark_name = b.get('name')
                    break
    except Exception:
        pass  # Non-critical — prompt will use placeholders

    from utils.prompt_renderer import render_prompt

    result = render_prompt(
        benchmark_id=benchmark_id,
        provider=provider,
        model_name=model_name,
        port=port,
        benchmark_name=benchmark_name,
        model_tier=model_tier,
        attempt_number=attempt_number,
        vps_host=vps_host,
    )

    return jsonify({
        'status': 'success',
        **result,
    })


# ---------------------------------------------------------------------------
# Tool call log endpoint (reads JSONL written by MCP server)
# ---------------------------------------------------------------------------

@comparison_bp.route('/api/comparison/tool-calls', methods=['GET'])
def get_tool_calls():
    """Query tool call log entries from the persistent JSONL file.

    Query params:
        benchmark_id: Filter by benchmark_id found in tool params
        tool_name:    Filter by exact tool name
        since:        ISO 8601 timestamp — only entries at or after this time
        limit:        Max entries to return (default 100, max 1000)
    """
    from utils.tool_call_logger import read_jsonl_entries

    limit = min(request.args.get('limit', 100, type=int), 1000)

    try:
        entries = read_jsonl_entries(
            benchmark_id=request.args.get('benchmark_id'),
            tool_name=request.args.get('tool_name'),
            since=request.args.get('since'),
            limit=limit,
        )

        return jsonify({
            'status': 'success',
            'tool_calls': entries,
            'total': len(entries),
        })

    except (IOError, OSError) as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to read tool call log: {e}',
        }), 500


# ---------------------------------------------------------------------------
# Model registry endpoints
# ---------------------------------------------------------------------------

@comparison_bp.route('/api/comparison/models', methods=['GET'])
def list_models():
    """List all registered models with pricing info."""
    active_only = request.args.get('active_only', 'false').lower() == 'true'

    with _get_db() as conn:
        if active_only:
            rows = conn.execute(
                "SELECT * FROM benchmark_models WHERE is_active = 1 ORDER BY provider, model_name"
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM benchmark_models ORDER BY provider, model_name"
            ).fetchall()

    return jsonify({
        'status': 'success',
        'models': [dict(r) for r in rows],
        'total': len(rows),
    })


@comparison_bp.route('/api/comparison/models', methods=['POST'])
def register_model():
    """Register a new model or update pricing for an existing one."""
    data = request.get_json()
    if not data:
        return jsonify({'status': 'error', 'message': 'Request body must be JSON'}), 400

    required = ['model_name', 'provider', 'display_name', 'tier']
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({
            'status': 'error',
            'message': f"Missing required fields: {', '.join(missing)}",
        }), 400

    with _get_db() as conn:
        try:
            conn.execute("""
                INSERT OR REPLACE INTO benchmark_models
                    (model_name, provider, display_name, tier,
                     input_cost_per_1m, output_cost_per_1m, access_method, is_active, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['model_name'], data['provider'], data['display_name'], data['tier'],
                data.get('input_cost_per_1m'), data.get('output_cost_per_1m'),
                data.get('access_method', 'cli'), data.get('is_active', 1), data.get('notes'),
            ))
            conn.commit()

            row = conn.execute(
                "SELECT * FROM benchmark_models WHERE model_name = ?",
                (data['model_name'],)
            ).fetchone()

            return jsonify({
                'status': 'success',
                'message': f"Model '{data['model_name']}' registered",
                'model': dict(row),
            }), 201

        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500
