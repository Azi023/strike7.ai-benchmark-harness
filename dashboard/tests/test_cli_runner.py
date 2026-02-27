#!/usr/bin/env python3
"""Tests for cli_runner.py -- automated CLI benchmark execution."""
import json
import os
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@pytest.fixture
def mock_gemini_output():
    return json.dumps({
        'response': 'I found the flag: S7BEN{test_flag_123}',
        'stats': {
            'models': {
                'gemini-2.5-flash': {
                    'tokens': {'prompt': 3000, 'candidates': 1500, 'cached': 200, 'thoughts': 50, 'tool': 100},
                    'api': {'totalLatencyMs': 8500, 'totalRequests': 6, 'totalErrors': 0}
                }
            },
            'tools': {'totalCalls': 8, 'totalSuccess': 8, 'totalFail': 0, 'totalDurationMs': 5200}
        }
    })

@pytest.fixture
def mock_claude_output():
    return json.dumps({
        'type': 'result', 'subtype': 'success', 'session_id': 'test-session-abc',
        'total_cost_usd': 0.0245, 'is_error': False,
        'duration_ms': 15200, 'duration_api_ms': 12100, 'num_turns': 6,
        'result': 'Flag captured: S7BEN{test_flag_456}',
        'usage': {'input_tokens': 8000, 'output_tokens': 3500, 'cache_creation_input_tokens': 0, 'cache_read_input_tokens': 500}
    })

@pytest.fixture
def mock_codex_output():
    events = [
        '{"type": "thread.started"}',
        '{"type": "turn.started"}',
        '{"type": "item.completed"}', '{"type": "item.completed"}', '{"type": "item.completed"}',
        '{"type": "token_count", "input_tokens": 2000, "output_tokens": 800, "reasoning_tokens": 200, "total_tokens": 3000}',
        '{"type": "turn.completed"}',
        '{"type": "turn.started"}',
        '{"type": "item.completed"}',
        '{"type": "token_count", "input_tokens": 4500, "output_tokens": 1800, "reasoning_tokens": 400, "total_tokens": 6700}',
        '{"type": "turn.completed"}',
    ]
    return '\n'.join(events)


class TestRedactFlags:
    def test_redacts_single_flag(self):
        from utils.cli_runner import redact_flags
        text = "I found the flag: S7BEN{secret_value_123}"
        assert 'S7BEN{REDACTED}' in redact_flags(text)
        assert 'secret_value_123' not in redact_flags(text)

    def test_redacts_multiple_flags(self):
        from utils.cli_runner import redact_flags
        text = "First: S7BEN{flag1} and second: S7BEN{flag2}"
        result = redact_flags(text)
        assert result.count('S7BEN{REDACTED}') == 2

    def test_preserves_non_flag_text(self):
        from utils.cli_runner import redact_flags
        text = "No flags here, just S7BEN prefix"
        assert redact_flags(text) == text

    def test_empty_input(self):
        from utils.cli_runner import redact_flags
        assert redact_flags("") == ""
        assert redact_flags(None) is None


class TestBuildRunRecord:
    def test_build_from_gemini(self, mock_gemini_output):
        from utils.cli_runner import build_run_record
        from utils.token_estimator import parse_cli_output

        parsed = parse_cli_output('google', mock_gemini_output)
        record = build_run_record(
            benchmark_id='S7BEN-EASY-001', provider='google', model_name='gemini-2.5-flash',
            parsed_metrics=parsed,
            flag_result={'flag_captured': True, 'time_to_flag_s': 12.5, 'flag_attempts': 1},
            total_duration_s=45.2, prompt_hash='abc123', raw_output=mock_gemini_output,
        )

        assert record['benchmark_id'] == 'S7BEN-EASY-001'
        assert record['provider'] == 'google'
        assert record['flag_captured'] == 1
        assert record['total_tokens'] == 4500
        assert record['token_source'] == 'exact'
        assert record['time_to_flag_s'] == 12.5
        assert record['total_duration_s'] == 45.2
        assert record['system_prompt_hash'] == 'abc123'
        assert record['execution_method'] == 'cli_automated'
        assert 'S7BEN{REDACTED}' in record['agent_transcript']
        assert 'test_flag_123' not in record['agent_transcript']

    def test_build_from_claude_with_direct_cost(self, mock_claude_output):
        from utils.cli_runner import build_run_record
        from utils.token_estimator import parse_cli_output

        parsed = parse_cli_output('anthropic', mock_claude_output)
        record = build_run_record(
            benchmark_id='S7BEN-MED-020', provider='anthropic', model_name='claude-sonnet-4.5',
            parsed_metrics=parsed,
            flag_result={'flag_captured': True, 'time_to_flag_s': 30.0, 'flag_attempts': 2},
            total_duration_s=60.0, prompt_hash='def456', raw_output=mock_claude_output,
        )

        assert record['input_tokens'] == 8000
        assert record['output_tokens'] == 3500
        assert record['cost_usd'] == 0.0245
        assert record['cost_source'] == 'exact'
        assert record['steps_taken'] == 6

    def test_build_failed_run(self):
        from utils.cli_runner import build_run_record
        from utils.token_estimator import _empty_result

        record = build_run_record(
            benchmark_id='S7BEN-HARD-023', provider='openai', model_name='gpt-4.1',
            parsed_metrics=_empty_result(),
            flag_result={'flag_captured': False, 'time_to_flag_s': None, 'flag_attempts': 0},
            total_duration_s=300.0, prompt_hash='ghi789', raw_output='',
            failure_reason='timeout',
        )

        assert record['flag_captured'] == 0
        assert record['failure_reason'] == 'timeout'
        assert record['time_to_flag_s'] is None

    def test_difficulty_tier_auto_extracted(self):
        from utils.cli_runner import build_run_record
        from utils.token_estimator import _empty_result

        record = build_run_record(
            benchmark_id='S7BEN-VHARD-005', provider='google', model_name='gemini-2.5-pro',
            parsed_metrics=_empty_result(),
            flag_result={'flag_captured': False, 'time_to_flag_s': None, 'flag_attempts': 0},
            total_duration_s=100.0, prompt_hash='xyz', raw_output='',
        )

        assert record['difficulty_tier'] == 'VHARD'


class TestRunBenchmarkAutomated:
    @patch('utils.cli_runner.subprocess.Popen')
    @patch('utils.cli_runner.requests.post')
    @patch('utils.cli_runner.requests.get')
    def test_successful_run_google(self, mock_get, mock_post, mock_popen, mock_gemini_output):
        from utils.cli_runner import run_benchmark_automated

        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {'status': 'success', 'prompt': 'Test prompt', 'prompt_hash': 'hash123'},
        )
        mock_post.return_value = MagicMock(
            status_code=201,
            json=lambda: {'status': 'success', 'run': {'run_id': 'test-run-id'}},
        )

        process_mock = MagicMock()
        process_mock.communicate.return_value = (mock_gemini_output.encode(), b'')
        process_mock.returncode = 0
        process_mock.pid = 12345
        mock_popen.return_value = process_mock

        with patch('utils.cli_runner.query_events_in_window', return_value=[
            {'event_type': 'flag_correct', 'details': {'attempts': 1, 'time_to_capture': 12.5}},
        ]):
            with patch('utils.cli_runner.extract_flag_result', return_value={
                'flag_captured': True, 'time_to_flag_s': 12.5, 'flag_attempts': 1,
            }):
                result = run_benchmark_automated(
                    benchmark_id='S7BEN-EASY-001', provider='google', model_name='gemini-2.5-flash',
                )

        assert result['status'] == 'success'
        assert result['flag_captured'] is True
        assert result['total_tokens'] > 0

    @patch('utils.cli_runner.subprocess.Popen')
    @patch('utils.cli_runner.requests.post')
    @patch('utils.cli_runner.requests.get')
    def test_timeout_records_failure(self, mock_get, mock_post, mock_popen):
        from utils.cli_runner import run_benchmark_automated

        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {'status': 'success', 'prompt': 'Test', 'prompt_hash': 'h'},
        )
        mock_post.return_value = MagicMock(
            status_code=201,
            json=lambda: {'status': 'success', 'run': {'run_id': 'timeout-run'}},
        )

        process_mock = MagicMock()
        process_mock.communicate.side_effect = subprocess.TimeoutExpired(cmd='gemini', timeout=300)
        process_mock.pid = 99999
        process_mock.poll.return_value = None
        mock_popen.return_value = process_mock

        with patch('utils.cli_runner.query_events_in_window', return_value=[]):
            with patch('utils.cli_runner.extract_flag_result', return_value={
                'flag_captured': False, 'time_to_flag_s': None, 'flag_attempts': 0,
            }):
                with patch('os.killpg'):
                    with patch('os.getpgid', return_value=99999):
                        result = run_benchmark_automated(
                            benchmark_id='S7BEN-HARD-023', provider='google', model_name='gemini-2.5-flash',
                        )

        assert result['status'] == 'success'
        assert result['flag_captured'] is False
        assert result['failure_reason'] == 'timeout'

    def test_dry_run_returns_command(self):
        from utils.cli_runner import run_benchmark_automated

        with patch('utils.cli_runner.requests.get') as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: {'status': 'success', 'prompt': 'Test prompt', 'prompt_hash': 'hash123'},
            )
            result = run_benchmark_automated(
                benchmark_id='S7BEN-EASY-001', provider='google', model_name='gemini-2.5-flash',
                dry_run=True,
            )

        assert result['status'] == 'dry_run'
        assert 'command' in result
        assert 'gemini' in result['command'][0]
