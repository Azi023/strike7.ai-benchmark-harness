#!/usr/bin/env python3
"""
Test suite for the multi-model benchmark comparison system.

Covers:
- DB initialization and idempotency
- Token estimation utilities
- All comparison API endpoints (CRUD, summary, matrix, models)
- Input validation and error handling
- Pagination and filtering

Uses Flask test client with a temporary SQLite DB for isolation.
"""
import json
import os
import sys
import tempfile
import uuid

import pytest

# Ensure dashboard modules are importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope='session')
def db_path():
    """Create a temporary DB file for all tests in this session."""
    fd, path = tempfile.mkstemp(suffix='.db', prefix='test_comparison_')
    os.close(fd)
    os.environ['COMPARISON_DB_PATH'] = path
    yield path
    os.unlink(path)


@pytest.fixture(scope='session')
def app(db_path):
    """Create Flask app with comparison blueprint registered."""
    # Import after setting env var so modules pick up test DB path
    from app import app as flask_app
    flask_app.config['TESTING'] = True
    return flask_app


@pytest.fixture(scope='session')
def client(app):
    """Flask test client."""
    return app.test_client()


@pytest.fixture
def sample_run():
    """Minimal valid run data."""
    return {
        'benchmark_id': 'S7BEN-EASY-001',
        'difficulty_tier': 'EASY',
        'provider': 'google',
        'model_name': 'gemini-2.5-flash',
        'flag_captured': 1,
        'time_to_flag_s': 15.2,
        'total_duration_s': 20.0,
        'steps_taken': 5,
        'total_tokens': 3041,
        'attempt_number': 1,
    }


@pytest.fixture
def sample_run_with_split_tokens():
    """Run data with separate input/output tokens for exact cost."""
    return {
        'benchmark_id': 'S7BEN-MED-001',
        'difficulty_tier': 'MED',
        'provider': 'anthropic',
        'model_name': 'claude-sonnet-4.5',
        'flag_captured': 1,
        'time_to_flag_s': 45.0,
        'total_duration_s': 60.0,
        'steps_taken': 12,
        'input_tokens': 5000,
        'output_tokens': 2000,
        'attempt_number': 1,
    }


def _post_run(client, data):
    """Helper to POST a run and return response."""
    return client.post(
        '/api/comparison/runs',
        data=json.dumps(data),
        content_type='application/json',
    )


# ---------------------------------------------------------------------------
# DB Initialization Tests
# ---------------------------------------------------------------------------

class TestDBInitialization:
    """Tests for init_comparison_db.py"""

    def test_db_initialized(self, app, db_path):
        """DB should have all tables after app import triggered auto-init."""
        import sqlite3
        conn = sqlite3.connect(db_path)
        tables = {row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()}
        conn.close()

        assert 'benchmark_models' in tables
        assert 'model_benchmark_runs' in tables
        assert 'schema_version' in tables

    def test_pil_view_exists(self, app, db_path):
        """PIL training data view should exist."""
        import sqlite3
        conn = sqlite3.connect(db_path)
        views = {row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='view'"
        ).fetchall()}
        conn.close()

        assert 'pil_training_data' in views

    def test_seed_models_present(self, app, db_path):
        """All 6 seed models should be present."""
        import sqlite3
        conn = sqlite3.connect(db_path)
        count = conn.execute("SELECT COUNT(*) FROM benchmark_models").fetchone()[0]
        conn.close()

        assert count == 6

    def test_idempotent_init(self, db_path):
        """Running init twice should not duplicate models."""
        from init_comparison_db import init_db
        init_db(db_path=db_path)  # Second init
        init_db(db_path=db_path)  # Third init

        import sqlite3
        conn = sqlite3.connect(db_path)
        count = conn.execute("SELECT COUNT(*) FROM benchmark_models").fetchone()[0]
        conn.close()

        assert count == 6

    def test_schema_version(self, db_path):
        """Schema version should be 1."""
        import sqlite3
        conn = sqlite3.connect(db_path)
        version = conn.execute("SELECT version FROM schema_version").fetchone()[0]
        conn.close()

        assert version == 1

    def test_wal_mode(self, db_path):
        """DB should use WAL journal mode."""
        import sqlite3
        conn = sqlite3.connect(db_path)
        mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
        conn.close()

        assert mode == 'wal'

    def test_indexes_exist(self, db_path):
        """All expected indexes should exist."""
        import sqlite3
        conn = sqlite3.connect(db_path)
        indexes = {row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'"
        ).fetchall()}
        conn.close()

        expected = {
            'idx_runs_benchmark', 'idx_runs_provider', 'idx_runs_model',
            'idx_runs_tier', 'idx_runs_composite', 'idx_runs_timestamp',
        }
        assert expected.issubset(indexes)


# ---------------------------------------------------------------------------
# Token Estimator Tests
# ---------------------------------------------------------------------------

class TestTokenEstimator:
    """Tests for utils/token_estimator.py"""

    def test_estimate_from_transcript_google(self):
        from utils.token_estimator import estimate_from_transcript
        result = estimate_from_transcript("a" * 400, 'google')

        assert result['source'] == 'estimated'
        assert result['total_tokens'] == 100  # 400 chars / 4.0 chars per token
        assert result['input_tokens'] + result['output_tokens'] == result['total_tokens']
        assert result['input_tokens'] == 60  # 60% for google

    def test_estimate_from_transcript_anthropic(self):
        from utils.token_estimator import estimate_from_transcript
        result = estimate_from_transcript("a" * 350, 'anthropic')

        assert result['total_tokens'] == 100  # 350 / 3.5
        assert result['input_tokens'] == 70  # 70% for anthropic

    def test_estimate_from_transcript_empty(self):
        from utils.token_estimator import estimate_from_transcript
        result = estimate_from_transcript("", 'google')

        assert result['total_tokens'] == 0
        assert result['input_tokens'] == 0
        assert result['output_tokens'] == 0

    def test_estimate_from_transcript_none(self):
        from utils.token_estimator import estimate_from_transcript
        result = estimate_from_transcript(None, 'google')

        assert result['total_tokens'] == 0

    def test_estimate_from_transcript_unknown_provider(self):
        from utils.token_estimator import estimate_from_transcript
        result = estimate_from_transcript("a" * 400, 'unknown_provider')

        # Falls back to 4.0 chars per token
        assert result['total_tokens'] == 100

    def test_estimate_from_steps(self):
        from utils.token_estimator import estimate_from_steps
        result = estimate_from_steps(5, 'google', 'EASY')

        # 500 overhead + 5 * 800 per step = 4500
        assert result['total_tokens'] == 4500
        assert result['source'] == 'estimated'

    def test_estimate_from_steps_zero(self):
        from utils.token_estimator import estimate_from_steps
        result = estimate_from_steps(0, 'google', 'EASY')

        assert result['total_tokens'] == 0

    def test_estimate_from_steps_none(self):
        from utils.token_estimator import estimate_from_steps
        result = estimate_from_steps(None, 'google', 'EASY')

        assert result['total_tokens'] == 0

    def test_calculate_cost_exact(self, db_path):
        from utils.token_estimator import calculate_cost
        # gemini-2.5-flash: $0.075 input, $0.30 output per 1M
        result = calculate_cost(
            total_tokens=7000,
            input_tokens=5000,
            output_tokens=2000,
            model_name='gemini-2.5-flash',
            db_path=db_path,
        )

        expected_cost = (5000 / 1_000_000 * 0.075) + (2000 / 1_000_000 * 0.30)
        assert result['cost_source'] == 'exact'
        assert abs(result['cost_usd'] - expected_cost) < 0.000001

    def test_calculate_cost_estimated(self, db_path):
        from utils.token_estimator import calculate_cost
        result = calculate_cost(
            total_tokens=7000,
            input_tokens=None,
            output_tokens=None,
            model_name='gemini-2.5-flash',
            db_path=db_path,
        )

        assert result['cost_source'] == 'estimated'
        assert result['cost_usd'] is not None
        assert result['cost_usd'] > 0

    def test_calculate_cost_unknown_model(self, db_path):
        from utils.token_estimator import calculate_cost
        result = calculate_cost(
            total_tokens=7000,
            input_tokens=None,
            output_tokens=None,
            model_name='nonexistent-model',
            db_path=db_path,
        )

        assert result['cost_source'] == 'unavailable'
        assert result['cost_usd'] is None

    def test_calculate_cost_no_tokens(self, db_path):
        from utils.token_estimator import calculate_cost
        result = calculate_cost(
            total_tokens=None,
            input_tokens=None,
            output_tokens=None,
            model_name='gemini-2.5-flash',
            db_path=db_path,
        )

        assert result['cost_source'] == 'unavailable'

    def test_parse_gemini_usage_full(self):
        from utils.token_estimator import parse_gemini_usage
        output = "Token count: 1234 input, 567 output\nDone."
        result = parse_gemini_usage(output)

        assert result is not None
        assert result['input_tokens'] == 1234
        assert result['output_tokens'] == 567
        assert result['total_tokens'] == 1801
        assert result['source'] == 'parsed'

    def test_parse_gemini_usage_total_only(self):
        from utils.token_estimator import parse_gemini_usage
        output = "Total tokens: 5000\n"
        result = parse_gemini_usage(output)

        assert result is not None
        assert result['total_tokens'] == 5000
        assert result['input_tokens'] is None

    def test_parse_gemini_usage_no_match(self):
        from utils.token_estimator import parse_gemini_usage
        assert parse_gemini_usage("no token info here") is None
        assert parse_gemini_usage("") is None
        assert parse_gemini_usage(None) is None

    def test_parse_claude_usage_full(self):
        from utils.token_estimator import parse_claude_usage
        output = "Total input tokens: 5,000\nTotal output tokens: 2,000\n"
        result = parse_claude_usage(output)

        assert result is not None
        assert result['input_tokens'] == 5000
        assert result['output_tokens'] == 2000
        assert result['total_tokens'] == 7000
        assert result['source'] == 'parsed'

    def test_parse_claude_usage_total_only(self):
        from utils.token_estimator import parse_claude_usage
        output = "Total tokens: 7,000\n"
        result = parse_claude_usage(output)

        assert result is not None
        assert result['total_tokens'] == 7000

    def test_parse_claude_usage_no_match(self):
        from utils.token_estimator import parse_claude_usage
        assert parse_claude_usage("no data") is None
        assert parse_claude_usage(None) is None


# ---------------------------------------------------------------------------
# API Endpoint Tests: Runs
# ---------------------------------------------------------------------------

class TestCreateRun:
    """POST /api/comparison/runs"""

    def test_create_run_success(self, client, sample_run):
        resp = _post_run(client, sample_run)
        data = resp.get_json()

        assert resp.status_code == 201
        assert data['status'] == 'success'
        assert data['run']['benchmark_id'] == 'S7BEN-EASY-001'
        assert data['run']['flag_captured'] == 1
        assert data['run']['run_id'] is not None
        assert data['run']['run_timestamp'] is not None

    def test_create_run_auto_cost_estimated(self, client, sample_run):
        """Cost should be auto-calculated from total_tokens with heuristic split."""
        resp = _post_run(client, sample_run)
        data = resp.get_json()

        assert data['run']['cost_usd'] is not None
        assert data['run']['cost_usd'] > 0
        assert data['run']['cost_source'] == 'estimated'

    def test_create_run_auto_cost_exact(self, client, sample_run_with_split_tokens):
        """Cost should be exact when input/output tokens are both provided."""
        resp = _post_run(client, sample_run_with_split_tokens)
        data = resp.get_json()

        assert data['run']['cost_source'] == 'exact'
        assert data['run']['cost_usd'] is not None

    def test_create_run_custom_run_id(self, client, sample_run):
        custom_id = 'custom-test-' + uuid.uuid4().hex[:8]
        sample_run['run_id'] = custom_id
        resp = _post_run(client, sample_run)
        data = resp.get_json()

        assert resp.status_code == 201
        assert data['run']['run_id'] == custom_id

    def test_create_run_missing_benchmark_id(self, client, sample_run):
        del sample_run['benchmark_id']
        resp = _post_run(client, sample_run)
        data = resp.get_json()

        assert resp.status_code == 400
        assert 'benchmark_id' in data['errors'][0]

    def test_create_run_missing_provider(self, client, sample_run):
        del sample_run['provider']
        resp = _post_run(client, sample_run)

        assert resp.status_code == 400

    def test_create_run_missing_model_name(self, client, sample_run):
        del sample_run['model_name']
        resp = _post_run(client, sample_run)

        assert resp.status_code == 400

    def test_create_run_missing_total_duration(self, client, sample_run):
        del sample_run['total_duration_s']
        resp = _post_run(client, sample_run)

        assert resp.status_code == 400

    def test_create_run_missing_difficulty_tier(self, client, sample_run):
        del sample_run['difficulty_tier']
        resp = _post_run(client, sample_run)

        assert resp.status_code == 400

    def test_create_run_invalid_tier(self, client, sample_run):
        sample_run['difficulty_tier'] = 'INVALID'
        resp = _post_run(client, sample_run)
        data = resp.get_json()

        assert resp.status_code == 400
        assert 'difficulty_tier' in data['errors'][0]

    def test_create_run_invalid_flag_captured(self, client, sample_run):
        sample_run['flag_captured'] = 5
        resp = _post_run(client, sample_run)

        assert resp.status_code == 400

    def test_create_run_negative_duration(self, client, sample_run):
        sample_run['total_duration_s'] = -10.0
        resp = _post_run(client, sample_run)

        assert resp.status_code == 400

    def test_create_run_no_json_body(self, client):
        resp = client.post(
            '/api/comparison/runs',
            data='not valid json',
            content_type='application/json',
        )

        assert resp.status_code == 400

    def test_create_run_failed_attempt(self, client):
        """A failed run (no flag captured) should be recorded."""
        data = {
            'benchmark_id': 'S7BEN-HARD-001',
            'difficulty_tier': 'HARD',
            'provider': 'openai',
            'model_name': 'gpt-4.1',
            'flag_captured': 0,
            'total_duration_s': 300.0,
            'failure_reason': 'timeout',
            'failure_details': 'Agent got stuck in a loop',
            'loop_detected': 1,
            'loop_count': 3,
        }
        resp = _post_run(client, data)
        result = resp.get_json()

        assert resp.status_code == 201
        assert result['run']['flag_captured'] == 0
        assert result['run']['failure_reason'] == 'timeout'
        assert result['run']['loop_detected'] == 1


class TestListRuns:
    """GET /api/comparison/runs"""

    def test_list_runs(self, client):
        resp = client.get('/api/comparison/runs')
        data = resp.get_json()

        assert resp.status_code == 200
        assert data['status'] == 'success'
        assert 'runs' in data
        assert 'total' in data
        assert 'limit' in data
        assert 'offset' in data

    def test_list_runs_filter_by_provider(self, client):
        resp = client.get('/api/comparison/runs?provider=google')
        data = resp.get_json()

        assert resp.status_code == 200
        for run in data['runs']:
            assert run['provider'] == 'google'

    def test_list_runs_filter_by_tier(self, client):
        resp = client.get('/api/comparison/runs?difficulty_tier=EASY')
        data = resp.get_json()

        assert resp.status_code == 200
        for run in data['runs']:
            assert run['difficulty_tier'] == 'EASY'

    def test_list_runs_filter_by_model(self, client):
        resp = client.get('/api/comparison/runs?model_name=gemini-2.5-flash')
        data = resp.get_json()

        assert resp.status_code == 200
        for run in data['runs']:
            assert run['model_name'] == 'gemini-2.5-flash'

    def test_list_runs_filter_by_benchmark(self, client):
        resp = client.get('/api/comparison/runs?benchmark_id=S7BEN-EASY-001')
        data = resp.get_json()

        assert resp.status_code == 200
        for run in data['runs']:
            assert run['benchmark_id'] == 'S7BEN-EASY-001'

    def test_list_runs_filter_flag_captured(self, client):
        resp = client.get('/api/comparison/runs?flag_captured=true')
        data = resp.get_json()

        assert resp.status_code == 200
        for run in data['runs']:
            assert run['flag_captured'] == 1

    def test_list_runs_pagination(self, client):
        resp = client.get('/api/comparison/runs?limit=2&offset=0')
        data = resp.get_json()

        assert resp.status_code == 200
        assert len(data['runs']) <= 2

    def test_list_runs_max_limit_capped(self, client):
        resp = client.get('/api/comparison/runs?limit=9999')
        data = resp.get_json()

        assert data['limit'] == 500  # Capped at MAX_LIMIT

    def test_list_runs_no_transcript_in_list(self, client):
        """agent_transcript should NOT be in list response (Issue #8)."""
        resp = client.get('/api/comparison/runs')
        data = resp.get_json()

        for run in data['runs']:
            assert 'agent_transcript' not in run


class TestGetRun:
    """GET /api/comparison/runs/<run_id>"""

    def test_get_run_success(self, client, sample_run):
        # Create a run first
        create_resp = _post_run(client, sample_run)
        run_id = create_resp.get_json()['run']['run_id']

        resp = client.get(f'/api/comparison/runs/{run_id}')
        data = resp.get_json()

        assert resp.status_code == 200
        assert data['run']['run_id'] == run_id
        # Detail view SHOULD include agent_transcript field
        assert 'agent_transcript' in data['run']

    def test_get_run_not_found(self, client):
        resp = client.get('/api/comparison/runs/nonexistent-id')

        assert resp.status_code == 404
        assert resp.get_json()['status'] == 'error'


class TestDeleteRun:
    """DELETE /api/comparison/runs/<run_id>"""

    def test_delete_run_without_confirm(self, client, sample_run):
        create_resp = _post_run(client, sample_run)
        run_id = create_resp.get_json()['run']['run_id']

        resp = client.delete(f'/api/comparison/runs/{run_id}')

        assert resp.status_code == 400
        assert 'confirm=true' in resp.get_json()['message']

    def test_delete_run_with_confirm(self, client, sample_run):
        create_resp = _post_run(client, sample_run)
        run_id = create_resp.get_json()['run']['run_id']

        resp = client.delete(f'/api/comparison/runs/{run_id}?confirm=true')

        assert resp.status_code == 200
        assert resp.get_json()['status'] == 'success'

        # Verify it's gone
        get_resp = client.get(f'/api/comparison/runs/{run_id}')
        assert get_resp.status_code == 404

    def test_delete_run_not_found(self, client):
        resp = client.delete('/api/comparison/runs/nonexistent?confirm=true')

        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# API Endpoint Tests: Summary
# ---------------------------------------------------------------------------

class TestSummary:
    """GET /api/comparison/summary"""

    def test_summary_returns_data(self, client):
        resp = client.get('/api/comparison/summary')
        data = resp.get_json()

        assert resp.status_code == 200
        assert data['status'] == 'success'
        assert 'summaries' in data
        assert 'total_groups' in data

    def test_summary_has_expected_fields(self, client):
        resp = client.get('/api/comparison/summary')
        data = resp.get_json()

        if data['summaries']:
            s = data['summaries'][0]
            assert 'provider' in s
            assert 'model_name' in s
            assert 'total_runs' in s
            assert 'successful_runs' in s
            assert 'pass_rate' in s
            assert 'avg_time_s' in s
            assert 'avg_tokens' in s
            assert 'total_cost_usd' in s

    def test_summary_filter_by_provider(self, client):
        resp = client.get('/api/comparison/summary?provider=google')
        data = resp.get_json()

        for s in data['summaries']:
            assert s['provider'] == 'google'

    def test_summary_filter_by_tier(self, client):
        resp = client.get('/api/comparison/summary?difficulty_tier=EASY')
        data = resp.get_json()

        for s in data['summaries']:
            assert s['difficulty_tier'] == 'EASY'


# ---------------------------------------------------------------------------
# API Endpoint Tests: Matrix
# ---------------------------------------------------------------------------

class TestMatrix:
    """GET /api/comparison/matrix"""

    def test_matrix_returns_structure(self, client):
        resp = client.get('/api/comparison/matrix')
        data = resp.get_json()

        assert resp.status_code == 200
        assert data['status'] == 'success'
        assert 'matrix' in data
        assert 'models' in data
        assert 'benchmarks' in data
        assert isinstance(data['models'], list)
        assert isinstance(data['benchmarks'], list)

    def test_matrix_cell_has_expected_fields(self, client):
        resp = client.get('/api/comparison/matrix')
        data = resp.get_json()

        for model, benchmarks in data['matrix'].items():
            for bench_id, cell in benchmarks.items():
                assert 'total_runs' in cell
                assert 'successes' in cell
                assert 'pass_rate' in cell
                assert 'avg_time_s' in cell


# ---------------------------------------------------------------------------
# API Endpoint Tests: Models
# ---------------------------------------------------------------------------

class TestModels:
    """GET/POST /api/comparison/models"""

    def test_list_models(self, client):
        resp = client.get('/api/comparison/models')
        data = resp.get_json()

        assert resp.status_code == 200
        assert data['status'] == 'success'
        assert data['total'] >= 6  # At least the seed models

    def test_list_models_active_only(self, client):
        resp = client.get('/api/comparison/models?active_only=true')
        data = resp.get_json()

        assert resp.status_code == 200
        for model in data['models']:
            assert model['is_active'] == 1

    def test_register_new_model(self, client):
        model_data = {
            'model_name': 'test-model-' + uuid.uuid4().hex[:8],
            'provider': 'test',
            'display_name': 'Test Model',
            'tier': 'test',
            'input_cost_per_1m': 1.0,
            'output_cost_per_1m': 2.0,
        }
        resp = client.post(
            '/api/comparison/models',
            data=json.dumps(model_data),
            content_type='application/json',
        )
        data = resp.get_json()

        assert resp.status_code == 201
        assert data['model']['model_name'] == model_data['model_name']
        assert data['model']['provider'] == 'test'

    def test_register_model_missing_fields(self, client):
        resp = client.post(
            '/api/comparison/models',
            data=json.dumps({'model_name': 'incomplete'}),
            content_type='application/json',
        )

        assert resp.status_code == 400
        assert 'Missing required' in resp.get_json()['message']

    def test_register_model_no_json(self, client):
        resp = client.post(
            '/api/comparison/models',
            data='not valid json',
            content_type='application/json',
        )

        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Combined filter tests
# ---------------------------------------------------------------------------

class TestCombinedFilters:
    """Test multiple filters working together."""

    def test_runs_combined_filter(self, client, sample_run):
        """Filtering by both provider and tier should intersect."""
        _post_run(client, sample_run)

        resp = client.get('/api/comparison/runs?provider=google&difficulty_tier=EASY')
        data = resp.get_json()

        assert resp.status_code == 200
        for run in data['runs']:
            assert run['provider'] == 'google'
            assert run['difficulty_tier'] == 'EASY'

    def test_summary_combined_filter(self, client):
        resp = client.get('/api/comparison/summary?provider=google&difficulty_tier=EASY')
        data = resp.get_json()

        assert resp.status_code == 200
        for s in data['summaries']:
            assert s['provider'] == 'google'
            assert s['difficulty_tier'] == 'EASY'
