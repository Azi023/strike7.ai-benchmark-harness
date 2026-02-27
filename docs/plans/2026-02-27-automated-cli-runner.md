# Automated CLI Runner — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Automate benchmark comparison runs by launching CLI agents (Gemini, Claude Code, Codex) in headless mode, capturing structured JSON output, and recording metrics without manual data entry.

**Architecture:** A Python orchestration module (`cli_runner.py`) launches provider-specific CLIs with `--output-format json`, parses the structured output via provider-specific JSON parsers, merges with Activity Logger flag data via time-window correlation, and POSTs the complete run record to the comparison API. A thin Bash wrapper (`run_automated.sh`) provides the CLI interface.

**Tech Stack:** Python 3.11+, subprocess, Flask test client (tests), pytest, existing SQLite comparison DB

**Review Reference:** 21 issues reviewed and agreed upon — see conversation context for full decisions.

---

## Dependency Order

```
Task 1: provider_config.py          (foundation — all modules import from here)
Task 2: token_estimator.py          (JSON parsers, DRY cost calc, token_source constants)
Task 3: comparison_routes.py        (DRY fix — delegates cost calc to token_estimator)
Task 4: activity_logger.py          (time-window query function)
Task 5: cli_runner.py               (core automation — depends on Tasks 1-4)
Task 6: run_automated.sh            (bash wrapper — depends on Task 5)
Task 7: batch + deprecation         (script updates — depends on Task 6)
Task 8: integration test            (end-to-end — depends on all above)
```

---

## Task 1: Central Provider Configuration

**Files:**
- Create: `dashboard/utils/provider_config.py`
- Test: `dashboard/tests/test_provider_config.py`

**Context:** Issue #7 — provider-specific constants are scattered across 4+ files. This module becomes the single source of truth for provider names, CLI commands, flags, timeouts, and JSON output formats.

### Step 1: Write the failing tests

Create `dashboard/tests/test_provider_config.py`:

```python
#!/usr/bin/env python3
"""Tests for provider_config.py — central provider configuration."""
import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestProviderConfig:
    """Tests for PROVIDERS dict structure and helper functions."""

    def test_all_three_providers_present(self):
        from utils.provider_config import PROVIDERS
        assert 'google' in PROVIDERS
        assert 'anthropic' in PROVIDERS
        assert 'openai' in PROVIDERS

    def test_provider_has_required_keys(self):
        from utils.provider_config import PROVIDERS
        required_keys = {
            'cli_command', 'json_flag', 'auto_approve_flags',
            'prompt_file', 'chars_per_token', 'input_output_split',
        }
        for provider, config in PROVIDERS.items():
            missing = required_keys - set(config.keys())
            assert not missing, f"{provider} missing keys: {missing}"

    def test_tier_timeouts_present(self):
        from utils.provider_config import TIER_TIMEOUTS
        for tier in ('EASY', 'MED', 'HARD', 'VHARD', 'CVE'):
            assert tier in TIER_TIMEOUTS
            timeout = TIER_TIMEOUTS[tier]
            assert 'max_turns' in timeout
            assert 'timeout_s' in timeout
            assert timeout['timeout_s'] > 0
            assert timeout['max_turns'] > 0

    def test_tier_timeouts_increase_with_difficulty(self):
        from utils.provider_config import TIER_TIMEOUTS
        assert TIER_TIMEOUTS['EASY']['timeout_s'] < TIER_TIMEOUTS['HARD']['timeout_s']
        assert TIER_TIMEOUTS['HARD']['timeout_s'] < TIER_TIMEOUTS['VHARD']['timeout_s']

    def test_get_cli_command_google(self):
        from utils.provider_config import get_cli_command
        cmd = get_cli_command('google', 'gemini-2.5-flash', 'test prompt', 'EASY')
        assert cmd[0] == 'gemini'
        assert '--output-format' in cmd or '--output-format=json' in ' '.join(cmd)

    def test_get_cli_command_anthropic(self):
        from utils.provider_config import get_cli_command
        cmd = get_cli_command('anthropic', 'claude-sonnet-4.5', 'test prompt', 'EASY')
        assert cmd[0] == 'claude'
        assert '--output-format' in cmd or '--output-format=json' in ' '.join(cmd)

    def test_get_cli_command_openai(self):
        from utils.provider_config import get_cli_command
        cmd = get_cli_command('openai', 'gpt-4.1', 'test prompt', 'EASY')
        assert cmd[0] == 'codex'

    def test_get_cli_command_unknown_provider_raises(self):
        from utils.provider_config import get_cli_command
        with pytest.raises(ValueError, match="Unknown provider"):
            get_cli_command('xai', 'grok', 'prompt', 'EASY')

    def test_get_cli_command_includes_model_switch(self):
        """Non-default models should have model selection flags."""
        from utils.provider_config import get_cli_command
        cmd_str = ' '.join(get_cli_command('google', 'gemini-2.5-pro', 'test', 'EASY'))
        assert 'gemini-2.5-pro' in cmd_str

    def test_valid_token_sources(self):
        from utils.provider_config import VALID_TOKEN_SOURCES
        assert 'exact' in VALID_TOKEN_SOURCES
        assert 'estimated' in VALID_TOKEN_SOURCES
        assert 'manual' in VALID_TOKEN_SOURCES
        assert 'unavailable' in VALID_TOKEN_SOURCES
```

### Step 2: Run tests to verify they fail

Run: `cd /home/atheeque/workspace/strike7-benchmarks/dashboard && python -m pytest tests/test_provider_config.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'utils.provider_config'`

### Step 3: Write the implementation

Create `dashboard/utils/provider_config.py`:

```python
"""
Central provider configuration for Strike7 benchmark comparison system.

This is the single source of truth for all provider-specific constants:
- CLI commands and flags for headless execution
- JSON output format details
- Token estimation parameters
- Tier-based timeout configuration

Configuration points reference:
- CLI paths/flags: PROVIDERS dict below
- Tier timeouts: TIER_TIMEOUTS dict below
- Model pricing: DB table `benchmark_models` (see init_comparison_db.py)
- Prompt templates: prompts/*.md (see PROVIDERS[x]['prompt_file'])
- Dashboard URL: STRIKE7_URL env var (default: http://localhost:5500)
"""

# ---------------------------------------------------------------------------
# Provider CLI configuration
# ---------------------------------------------------------------------------

PROVIDERS = {
    'google': {
        'cli_command': 'gemini',
        'json_flag': '--output-format=json',
        'auto_approve_flags': ['--sandbox=false'],
        'prompt_flag': '-p',
        'model_flag': '--model',
        'prompt_file': 'gemini_tuned_prompt.md',
        'chars_per_token': 4.0,
        'input_output_split': (0.60, 0.40),
        'base_overhead_tokens': 500,
    },
    'anthropic': {
        'cli_command': 'claude',
        'json_flag': '--output-format=json',
        'auto_approve_flags': ['--dangerously-skip-permissions'],
        'prompt_flag': '-p',
        'model_flag': '--model',
        'max_turns_flag': '--max-turns',
        'prompt_file': 'claude_tuned_prompt.md',
        'chars_per_token': 3.5,
        'input_output_split': (0.70, 0.30),
        'base_overhead_tokens': 600,
    },
    'openai': {
        'cli_command': 'codex',
        'json_flag': '--json',
        'auto_approve_flags': ['--full-auto'],
        'prompt_flag': None,  # codex uses: codex exec "prompt"
        'model_flag': '--model',
        'prompt_file': 'codex_tuned_prompt.md',
        'chars_per_token': 4.0,
        'input_output_split': (0.60, 0.40),
        'base_overhead_tokens': 500,
    },
}

# ---------------------------------------------------------------------------
# Tier-based execution limits (Issue #2 — guardrails)
# ---------------------------------------------------------------------------

TIER_TIMEOUTS = {
    'EASY':  {'max_turns': 30,  'timeout_s': 300},    # 5 min
    'MED':   {'max_turns': 50,  'timeout_s': 600},    # 10 min
    'HARD':  {'max_turns': 80,  'timeout_s': 1200},   # 20 min
    'VHARD': {'max_turns': 100, 'timeout_s': 1800},   # 30 min
    'CVE':   {'max_turns': 100, 'timeout_s': 1800},   # 30 min
}

# ---------------------------------------------------------------------------
# Token source values (Issue #8 — standardized constants)
# ---------------------------------------------------------------------------

VALID_TOKEN_SOURCES = {
    'exact',              # From CLI JSON output with full input/output breakdown
    'exact_total_only',   # From CLI JSON output, total only (no breakdown)
    'estimated',          # From estimate_from_transcript() or estimate_from_steps()
    'parsed',             # From regex text parser (legacy, backward compat)
    'manual',             # User entered manually via script/API
    'unavailable',        # No token data available
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_cli_command(provider, model_name, prompt_text, difficulty_tier):
    """Build the CLI command list for headless execution.

    Args:
        provider: 'google', 'anthropic', or 'openai'
        model_name: e.g., 'gemini-2.5-flash', 'claude-sonnet-4.5'
        prompt_text: The rendered benchmark prompt string
        difficulty_tier: 'EASY', 'MED', 'HARD', 'VHARD', 'CVE'

    Returns:
        list[str]: Command and arguments suitable for subprocess.run()

    Raises:
        ValueError: If provider is not recognized
    """
    config = PROVIDERS.get(provider)
    if not config:
        raise ValueError(f"Unknown provider: '{provider}'. Must be one of: {', '.join(PROVIDERS)}")

    tier_config = TIER_TIMEOUTS.get(difficulty_tier, TIER_TIMEOUTS['HARD'])
    cmd = [config['cli_command']]

    if provider == 'google':
        cmd.extend([
            config['prompt_flag'], prompt_text,
            config['json_flag'],
            config['model_flag'], model_name,
        ])
        cmd.extend(config['auto_approve_flags'])

    elif provider == 'anthropic':
        cmd.extend([
            config['prompt_flag'], prompt_text,
            config['json_flag'],
            config['model_flag'], model_name,
            config['max_turns_flag'], str(tier_config['max_turns']),
        ])
        cmd.extend(config['auto_approve_flags'])

    elif provider == 'openai':
        cmd.extend([
            'exec', prompt_text,
            config['json_flag'],
            config['model_flag'], model_name,
        ])
        cmd.extend(config['auto_approve_flags'])

    return cmd


def get_timeout(difficulty_tier):
    """Get the OS-level timeout in seconds for a difficulty tier."""
    config = TIER_TIMEOUTS.get(difficulty_tier, TIER_TIMEOUTS['HARD'])
    # Add 30s buffer beyond the configured timeout for graceful shutdown
    return config['timeout_s'] + 30
```

### Step 4: Run tests to verify they pass

Run: `cd /home/atheeque/workspace/strike7-benchmarks/dashboard && python -m pytest tests/test_provider_config.py -v`
Expected: All 11 tests PASS

### Step 5: Commit

```bash
git add dashboard/utils/provider_config.py dashboard/tests/test_provider_config.py
git commit -m "feat: add central provider configuration module

Single source of truth for CLI commands, flags, tier timeouts,
and token source constants. Eliminates provider config scatter
across 4+ files."
```

---

## Task 2: Token Estimator Enhancements

**Files:**
- Modify: `dashboard/utils/token_estimator.py`
- Modify: `dashboard/tests/test_comparison.py` (TestTokenEstimator class)

**Context:** Issue #6 — add JSON output parsers for all 3 providers. Issue #8 — use standardized token_source values. Rename existing text parsers for clarity.

### Step 1: Write the failing tests

Add to `dashboard/tests/test_comparison.py` inside `TestTokenEstimator` class:

```python
    # --- JSON parser tests (Issue #6) ---

    def test_parse_gemini_json_full(self):
        from utils.token_estimator import parse_gemini_json
        data = {
            'stats': {
                'models': {
                    'gemini-2.5-flash': {
                        'tokens': {
                            'prompt': 1500,
                            'candidates': 800,
                            'cached': 200,
                            'thoughts': 100,
                            'tool': 50,
                        },
                        'api': {
                            'totalLatencyMs': 4500,
                            'totalRequests': 5,
                        }
                    }
                },
                'tools': {
                    'totalCalls': 12,
                    'totalSuccess': 11,
                    'totalFail': 1,
                    'totalDurationMs': 3200,
                }
            },
            'response': 'Found flag S7BEN{test}'
        }
        result = parse_gemini_json(data)

        assert result['input_tokens'] == 1500
        assert result['output_tokens'] == 800
        assert result['total_tokens'] == 1500 + 800
        assert result['cached_tokens'] == 200
        assert result['tool_calls'] == 12
        assert result['duration_ms'] == 4500
        assert result['token_source'] == 'exact'

    def test_parse_gemini_json_empty_stats(self):
        from utils.token_estimator import parse_gemini_json
        result = parse_gemini_json({'response': 'hello', 'stats': {}})

        assert result['total_tokens'] == 0
        assert result['token_source'] == 'unavailable'

    def test_parse_gemini_json_none(self):
        from utils.token_estimator import parse_gemini_json
        result = parse_gemini_json(None)

        assert result['total_tokens'] == 0
        assert result['token_source'] == 'unavailable'

    def test_parse_claude_json_full(self):
        from utils.token_estimator import parse_claude_json
        data = {
            'type': 'result',
            'subtype': 'success',
            'session_id': 'abc-123',
            'total_cost_usd': 0.0034,
            'is_error': False,
            'duration_ms': 2847,
            'duration_api_ms': 1923,
            'num_turns': 4,
            'result': 'Found the flag',
            'usage': {
                'input_tokens': 5000,
                'output_tokens': 2000,
                'cache_creation_input_tokens': 100,
                'cache_read_input_tokens': 300,
            }
        }
        result = parse_claude_json(data)

        assert result['input_tokens'] == 5000
        assert result['output_tokens'] == 2000
        assert result['total_tokens'] == 7000
        assert result['cost_usd'] == 0.0034
        assert result['duration_ms'] == 2847
        assert result['num_turns'] == 4
        assert result['token_source'] == 'exact'

    def test_parse_claude_json_error_result(self):
        from utils.token_estimator import parse_claude_json
        data = {
            'type': 'result',
            'subtype': 'error',
            'is_error': True,
            'duration_ms': 500,
            'usage': {
                'input_tokens': 100,
                'output_tokens': 0,
            }
        }
        result = parse_claude_json(data)

        assert result['is_error'] is True
        assert result['input_tokens'] == 100
        assert result['token_source'] == 'exact'

    def test_parse_claude_json_none(self):
        from utils.token_estimator import parse_claude_json
        result = parse_claude_json(None)

        assert result['total_tokens'] == 0
        assert result['token_source'] == 'unavailable'

    def test_parse_codex_jsonl_full(self):
        from utils.token_estimator import parse_codex_jsonl
        events = [
            '{"type": "thread.started"}',
            '{"type": "turn.started"}',
            '{"type": "item.completed"}',
            '{"type": "item.completed"}',
            '{"type": "token_count", "input_tokens": 500, "output_tokens": 200, "reasoning_tokens": 50, "total_tokens": 750}',
            '{"type": "turn.completed"}',
            '{"type": "turn.started"}',
            '{"type": "item.completed"}',
            '{"type": "token_count", "input_tokens": 900, "output_tokens": 400, "reasoning_tokens": 100, "total_tokens": 1400}',
            '{"type": "turn.completed"}',
        ]
        result = parse_codex_jsonl(events)

        # Should use the LAST token_count (cumulative)
        assert result['input_tokens'] == 900
        assert result['output_tokens'] == 400
        assert result['total_tokens'] == 1400
        assert result['num_turns'] == 2
        assert result['tool_calls'] == 3  # 3 item.completed events
        assert result['token_source'] == 'exact'

    def test_parse_codex_jsonl_no_token_counts(self):
        from utils.token_estimator import parse_codex_jsonl
        events = ['{"type": "turn.started"}', '{"type": "turn.completed"}']
        result = parse_codex_jsonl(events)

        assert result['total_tokens'] == 0
        assert result['token_source'] == 'unavailable'

    def test_parse_codex_jsonl_empty(self):
        from utils.token_estimator import parse_codex_jsonl
        result = parse_codex_jsonl([])

        assert result['total_tokens'] == 0

    def test_parse_cli_output_dispatcher_google(self):
        from utils.token_estimator import parse_cli_output
        import json
        data = {'stats': {'models': {'m': {'tokens': {'prompt': 10, 'candidates': 5}}}}}
        result = parse_cli_output('google', json.dumps(data))
        assert result['token_source'] in ('exact', 'unavailable')

    def test_parse_cli_output_dispatcher_unknown(self):
        from utils.token_estimator import parse_cli_output
        result = parse_cli_output('unknown_provider', '{}')
        assert result['token_source'] == 'unavailable'

    # --- Backward compat: renamed text parsers ---

    def test_parse_gemini_text_still_works(self):
        """Renamed from parse_gemini_usage, should still work."""
        from utils.token_estimator import parse_gemini_text
        output = "Token count: 1234 input, 567 output\nDone."
        result = parse_gemini_text(output)
        assert result['input_tokens'] == 1234

    def test_parse_claude_text_still_works(self):
        """Renamed from parse_claude_usage, should still work."""
        from utils.token_estimator import parse_claude_text
        output = "Total input tokens: 5,000\nTotal output tokens: 2,000\n"
        result = parse_claude_text(output)
        assert result['input_tokens'] == 5000
```

### Step 2: Run tests to verify they fail

Run: `cd /home/atheeque/workspace/strike7-benchmarks/dashboard && python -m pytest tests/test_comparison.py::TestTokenEstimator -v`
Expected: FAIL — `ImportError: cannot import name 'parse_gemini_json'`

### Step 3: Write the implementation

Modify `dashboard/utils/token_estimator.py` — add JSON parsers, rename text parsers, add dispatcher. Full replacement of file:

```python
"""
Token estimation, parsing, and cost calculation utilities.

Provides:
- JSON output parsers for Gemini, Claude Code, and Codex CLIs
- Text output parsers (legacy, for manual/non-JSON mode)
- Token estimation from transcripts and step counts
- Cost calculation using model pricing from DB

Token source hierarchy (most to least accurate):
  exact > exact_total_only > parsed > estimated > manual > unavailable
"""
import json as _json
import re
import sqlite3
import os

from utils.provider_config import PROVIDERS, VALID_TOKEN_SOURCES

DB_PATH = os.environ.get(
    'COMPARISON_DB_PATH',
    os.path.join(os.path.dirname(__file__), '..', 'data', 'model_benchmarks.db')
)

# Estimated tokens per step by difficulty tier (calibrated from observed runs)
TOKENS_PER_STEP = {
    'EASY': 800,
    'MED': 1200,
    'HARD': 1800,
    'VHARD': 2500,
    'CVE': 2000,
}


def _empty_result(token_source='unavailable'):
    """Return a zeroed-out metrics dict."""
    return {
        'total_tokens': 0,
        'input_tokens': 0,
        'output_tokens': 0,
        'cached_tokens': 0,
        'cost_usd': None,
        'duration_ms': None,
        'num_turns': None,
        'tool_calls': None,
        'is_error': None,
        'token_source': token_source,
    }


# ---------------------------------------------------------------------------
# JSON output parsers (structured, from --output-format json)
# ---------------------------------------------------------------------------

def parse_gemini_json(data):
    """Parse structured JSON output from Gemini CLI (--output-format json).

    Extracts token usage from stats.models.*.tokens, tool call counts from
    stats.tools, and API latency from stats.models.*.api.

    Args:
        data: Parsed JSON dict from Gemini CLI output.

    Returns:
        dict with token counts, tool_calls, duration_ms, token_source.
    """
    if not data or not isinstance(data, dict):
        return _empty_result()

    stats = data.get('stats', {})
    models = stats.get('models', {})

    if not models:
        return _empty_result()

    # Aggregate across all models (usually just one)
    total_input = 0
    total_output = 0
    total_cached = 0
    total_latency = 0

    for model_name, model_data in models.items():
        tokens = model_data.get('tokens', {})
        total_input += tokens.get('prompt', 0)
        total_output += tokens.get('candidates', 0)
        total_cached += tokens.get('cached', 0)

        api = model_data.get('api', {})
        total_latency += api.get('totalLatencyMs', 0)

    tools = stats.get('tools', {})
    tool_calls = tools.get('totalCalls', None)

    return {
        'total_tokens': total_input + total_output,
        'input_tokens': total_input,
        'output_tokens': total_output,
        'cached_tokens': total_cached,
        'cost_usd': None,  # Gemini doesn't report cost; calculate separately
        'duration_ms': total_latency if total_latency > 0 else None,
        'num_turns': None,  # Gemini doesn't report turns in summary
        'tool_calls': tool_calls,
        'is_error': None,
        'token_source': 'exact' if (total_input + total_output) > 0 else 'unavailable',
    }


def parse_claude_json(data):
    """Parse structured JSON output from Claude Code CLI (--output-format json).

    Extracts usage.{input_tokens, output_tokens}, total_cost_usd,
    duration_ms, num_turns from the result object.

    Args:
        data: Parsed JSON dict from Claude Code CLI output.

    Returns:
        dict with token counts, cost_usd, duration_ms, num_turns, token_source.
    """
    if not data or not isinstance(data, dict):
        return _empty_result()

    usage = data.get('usage', {})
    input_tokens = usage.get('input_tokens', 0)
    output_tokens = usage.get('output_tokens', 0)
    cached = (usage.get('cache_creation_input_tokens', 0)
              + usage.get('cache_read_input_tokens', 0))

    has_tokens = (input_tokens + output_tokens) > 0

    return {
        'total_tokens': input_tokens + output_tokens,
        'input_tokens': input_tokens,
        'output_tokens': output_tokens,
        'cached_tokens': cached,
        'cost_usd': data.get('total_cost_usd'),
        'duration_ms': data.get('duration_ms'),
        'num_turns': data.get('num_turns'),
        'tool_calls': None,  # Claude doesn't report per-tool counts in summary
        'is_error': data.get('is_error'),
        'token_source': 'exact' if has_tokens else 'unavailable',
    }


def parse_codex_jsonl(events):
    """Parse JSONL event stream from Codex CLI (codex exec --json).

    Processes token_count events (cumulative — last one has final totals),
    counts turn.completed events and item.completed events.

    Args:
        events: List of JSONL strings (one per line from Codex output).

    Returns:
        dict with token counts, num_turns, tool_calls, token_source.
    """
    if not events:
        return _empty_result()

    last_token_count = None
    turn_count = 0
    item_count = 0

    for line in events:
        if not line or not line.strip():
            continue
        try:
            event = _json.loads(line) if isinstance(line, str) else line
        except (_json.JSONDecodeError, TypeError):
            continue

        event_type = event.get('type', '')

        if event_type == 'token_count':
            last_token_count = event
        elif event_type == 'turn.completed':
            turn_count += 1
        elif event_type == 'item.completed':
            item_count += 1

    if not last_token_count:
        return _empty_result()

    input_tokens = last_token_count.get('input_tokens', 0)
    output_tokens = last_token_count.get('output_tokens', 0)
    total_tokens = last_token_count.get('total_tokens', input_tokens + output_tokens)

    return {
        'total_tokens': total_tokens,
        'input_tokens': input_tokens,
        'output_tokens': output_tokens,
        'cached_tokens': last_token_count.get('cached_input_tokens', 0),
        'cost_usd': None,  # Codex doesn't report cost
        'duration_ms': None,  # Compute from event timestamps externally
        'num_turns': turn_count if turn_count > 0 else None,
        'tool_calls': item_count if item_count > 0 else None,
        'is_error': None,
        'token_source': 'exact' if total_tokens > 0 else 'unavailable',
    }


def parse_cli_output(provider, raw_output):
    """Dispatch to the correct JSON parser based on provider.

    Args:
        provider: 'google', 'anthropic', or 'openai'
        raw_output: Raw stdout string from CLI execution.

    Returns:
        dict with parsed metrics (same shape as individual parsers).
    """
    if not raw_output:
        return _empty_result()

    try:
        if provider == 'google':
            data = _json.loads(raw_output)
            return parse_gemini_json(data)

        elif provider == 'anthropic':
            data = _json.loads(raw_output)
            return parse_claude_json(data)

        elif provider == 'openai':
            # Codex outputs JSONL (one JSON object per line)
            lines = raw_output.strip().split('\n')
            return parse_codex_jsonl(lines)

        else:
            return _empty_result()

    except (_json.JSONDecodeError, TypeError, KeyError):
        return _empty_result()


# ---------------------------------------------------------------------------
# Text output parsers (legacy — for non-JSON CLI output)
# ---------------------------------------------------------------------------

def parse_gemini_text(cli_output):
    """Parse token usage from Gemini CLI plain text output.

    Formerly named parse_gemini_usage(). Looks for patterns like:
        Token count: 1234 input, 567 output
        Total tokens: 1801
    """
    if not cli_output:
        return None

    match = re.search(
        r'[Tt]oken\s+count:\s*(\d+)\s*input\s*,\s*(\d+)\s*output',
        cli_output
    )
    if match:
        input_tokens = int(match.group(1))
        output_tokens = int(match.group(2))
        return {
            'total_tokens': input_tokens + output_tokens,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'source': 'parsed',
        }

    match = re.search(r'[Tt]otal\s+tokens:\s*(\d+)', cli_output)
    if match:
        return {
            'total_tokens': int(match.group(1)),
            'input_tokens': None,
            'output_tokens': None,
            'source': 'parsed',
        }

    return None


def parse_claude_text(cli_output):
    """Parse token usage from Claude Code plain text output.

    Formerly named parse_claude_usage(). Looks for patterns like:
        Total input tokens: 5,000
        Total output tokens: 2,000
    """
    if not cli_output:
        return None

    input_match = re.search(r'[Tt]otal\s+input\s+tokens:\s*(\d[\d,]*)', cli_output)
    output_match = re.search(r'[Tt]otal\s+output\s+tokens:\s*(\d[\d,]*)', cli_output)

    if input_match and output_match:
        input_tokens = int(input_match.group(1).replace(',', ''))
        output_tokens = int(output_match.group(1).replace(',', ''))
        return {
            'total_tokens': input_tokens + output_tokens,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'source': 'parsed',
        }

    total_match = re.search(r'[Tt]otal\s+tokens:\s*(\d[\d,]*)', cli_output)
    if total_match:
        return {
            'total_tokens': int(total_match.group(1).replace(',', '')),
            'input_tokens': None,
            'output_tokens': None,
            'source': 'parsed',
        }

    return None


# Backward-compatible aliases (Issue #6 — renamed for clarity)
parse_gemini_usage = parse_gemini_text
parse_claude_usage = parse_claude_text


# ---------------------------------------------------------------------------
# Token estimation (when no CLI data is available)
# ---------------------------------------------------------------------------

def estimate_from_transcript(transcript, provider):
    """Estimate token counts from agent transcript text."""
    if not transcript:
        return {
            'total_tokens': 0, 'input_tokens': 0,
            'output_tokens': 0, 'source': 'estimated',
        }

    config = PROVIDERS.get(provider, {})
    chars_per_token = config.get('chars_per_token', 4.0)
    total_tokens = int(len(transcript) / chars_per_token)

    input_ratio, _ = config.get('input_output_split', (0.65, 0.35))
    input_tokens = int(total_tokens * input_ratio)
    output_tokens = total_tokens - input_tokens

    return {
        'total_tokens': total_tokens, 'input_tokens': input_tokens,
        'output_tokens': output_tokens, 'source': 'estimated',
    }


def estimate_from_steps(steps, provider, difficulty):
    """Rough estimate based on step count and difficulty."""
    if not steps or steps <= 0:
        return {
            'total_tokens': 0, 'input_tokens': 0,
            'output_tokens': 0, 'source': 'estimated',
        }

    per_step = TOKENS_PER_STEP.get(difficulty, 1500)
    config = PROVIDERS.get(provider, {})
    overhead = config.get('base_overhead_tokens', 500)
    total_tokens = overhead + (steps * per_step)

    input_ratio, _ = config.get('input_output_split', (0.65, 0.35))
    input_tokens = int(total_tokens * input_ratio)
    output_tokens = total_tokens - input_tokens

    return {
        'total_tokens': total_tokens, 'input_tokens': input_tokens,
        'output_tokens': output_tokens, 'source': 'estimated',
    }


# ---------------------------------------------------------------------------
# Cost calculation (single source of truth — Issue #5)
# ---------------------------------------------------------------------------

def calculate_cost(total_tokens, input_tokens, output_tokens,
                   model_name, db_path=None):
    """Calculate cost from tokens using model pricing in DB.

    If input_tokens and output_tokens are both provided, calculates exact cost.
    If only total_tokens is provided, applies provider-specific heuristic split.

    Returns:
        dict with 'cost_usd' and 'cost_source' ('exact' or 'estimated').
    """
    path = db_path or DB_PATH

    try:
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT provider, input_cost_per_1m, output_cost_per_1m "
            "FROM benchmark_models WHERE model_name = ?",
            (model_name,)
        ).fetchone()
        conn.close()
    except (sqlite3.OperationalError, sqlite3.DatabaseError):
        return {'cost_usd': None, 'cost_source': 'unavailable'}

    if not row:
        return {'cost_usd': None, 'cost_source': 'unavailable'}

    input_cost_per_1m = row['input_cost_per_1m'] or 0.0
    output_cost_per_1m = row['output_cost_per_1m'] or 0.0

    if input_tokens is not None and output_tokens is not None:
        cost = (input_tokens / 1_000_000 * input_cost_per_1m) + \
               (output_tokens / 1_000_000 * output_cost_per_1m)
        return {'cost_usd': round(cost, 6), 'cost_source': 'exact'}

    if total_tokens and total_tokens > 0:
        provider = row['provider']
        config = PROVIDERS.get(provider, {})
        input_ratio, _ = config.get('input_output_split', (0.65, 0.35))
        est_input = int(total_tokens * input_ratio)
        est_output = total_tokens - est_input
        cost = (est_input / 1_000_000 * input_cost_per_1m) + \
               (est_output / 1_000_000 * output_cost_per_1m)
        return {'cost_usd': round(cost, 6), 'cost_source': 'estimated'}

    return {'cost_usd': None, 'cost_source': 'unavailable'}
```

### Step 4: Run full token estimator tests

Run: `cd /home/atheeque/workspace/strike7-benchmarks/dashboard && python -m pytest tests/test_comparison.py::TestTokenEstimator -v`
Expected: All tests PASS (both new JSON parser tests and existing tests via backward-compat aliases)

### Step 5: Run full test suite to check for regressions

Run: `cd /home/atheeque/workspace/strike7-benchmarks/dashboard && python -m pytest tests/test_comparison.py -v`
Expected: All 90+ tests PASS

### Step 6: Commit

```bash
git add dashboard/utils/token_estimator.py dashboard/tests/test_comparison.py
git commit -m "feat: add JSON output parsers for Gemini, Claude, and Codex CLIs

- parse_gemini_json(): extracts tokens, tool calls, latency from stats
- parse_claude_json(): extracts tokens, cost_usd, duration, turns from usage
- parse_codex_jsonl(): processes JSONL event stream for cumulative tokens
- parse_cli_output(): dispatcher that routes to correct parser by provider
- Renamed text parsers to parse_gemini_text/parse_claude_text (aliases kept)
- Reads provider constants from centralized provider_config.py
- Issues #5, #6, #8 from review"
```

---

## Task 3: Comparison Routes DRY Fix

**Files:**
- Modify: `dashboard/api/comparison_routes.py:58-99` (`_calculate_cost_for_run`)
- Modify: `dashboard/api/comparison_routes.py:22` (REQUIRED_RUN_FIELDS)

**Context:** Issue #5 — `_calculate_cost_for_run` duplicates logic from `token_estimator.calculate_cost`. Issue #8 — validate token_source on write.

### Step 1: Run existing tests to establish baseline

Run: `cd /home/atheeque/workspace/strike7-benchmarks/dashboard && python -m pytest tests/test_comparison.py::TestCreateRun -v`
Expected: All PASS

### Step 2: Modify comparison_routes.py

Replace `_calculate_cost_for_run` (lines 58-99) with delegation to `token_estimator`:

```python
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
```

Add token_source validation to `_validate_run_data`:

```python
    # After the existing validations, before return:
    token_source = data.get('token_source')
    if token_source is not None:
        from utils.provider_config import VALID_TOKEN_SOURCES
        if token_source not in VALID_TOKEN_SOURCES:
            errors.append(
                f"Invalid token_source: '{token_source}'. "
                f"Must be one of: {', '.join(sorted(VALID_TOKEN_SOURCES))}"
            )
```

### Step 3: Run tests to verify no regressions

Run: `cd /home/atheeque/workspace/strike7-benchmarks/dashboard && python -m pytest tests/test_comparison.py -v`
Expected: All tests PASS (cost calculation behavior is identical)

### Step 4: Add a test for token_source validation

Add to `TestCreateRun` class in `test_comparison.py`:

```python
    def test_create_run_invalid_token_source(self, client, sample_run):
        sample_run['token_source'] = 'made_up_source'
        resp = _post_run(client, sample_run)
        assert resp.status_code == 400
        assert 'token_source' in resp.get_json()['errors'][0]

    def test_create_run_valid_token_source_exact(self, client, sample_run):
        sample_run['token_source'] = 'exact'
        resp = _post_run(client, sample_run)
        assert resp.status_code == 201
        assert resp.get_json()['run']['token_source'] == 'exact'
```

### Step 5: Run new tests

Run: `cd /home/atheeque/workspace/strike7-benchmarks/dashboard && python -m pytest tests/test_comparison.py::TestCreateRun -v`
Expected: All PASS

### Step 6: Commit

```bash
git add dashboard/api/comparison_routes.py dashboard/tests/test_comparison.py
git commit -m "refactor: DRY cost calculation, add token_source validation

- _calculate_cost_for_run delegates to token_estimator.calculate_cost
- Validate token_source against VALID_TOKEN_SOURCES on run creation
- Issues #5, #8 from review"
```

---

## Task 4: Activity Logger Time-Window Query

**Files:**
- Modify: `dashboard/api/activity_logger.py`
- Add tests to: `dashboard/tests/test_comparison.py`

**Context:** Issue #4 — after automated CLI finishes, query Activity Logger by benchmark_id + time window to find flag capture events.

### Step 1: Write the failing test

Add new class to `dashboard/tests/test_comparison.py`:

```python
class TestActivityLoggerTimeWindow:
    """Tests for time-window correlation query (Issue #4)."""

    def test_query_events_in_window(self):
        from api.activity_logger import log_activity, query_events_in_window
        import time

        bench_id = f'S7BEN-EASY-TEST-{uuid.uuid4().hex[:6]}'
        start_time = datetime.utcnow().isoformat() + 'Z'
        time.sleep(0.05)

        log_activity('benchmark_start', bench_id, {'port': 5001}, 'info')
        log_activity('flag_correct', bench_id, {'attempts': 1, 'time_to_capture': 12.5}, 'success')
        time.sleep(0.05)
        end_time = datetime.utcnow().isoformat() + 'Z'

        events = query_events_in_window(bench_id, start_time, end_time)

        assert len(events) == 2
        assert events[0]['event_type'] == 'benchmark_start'
        assert events[1]['event_type'] == 'flag_correct'

    def test_query_events_excludes_other_benchmarks(self):
        from api.activity_logger import log_activity, query_events_in_window
        import time

        bench_a = f'S7BEN-EASY-A-{uuid.uuid4().hex[:6]}'
        bench_b = f'S7BEN-EASY-B-{uuid.uuid4().hex[:6]}'

        start_time = datetime.utcnow().isoformat() + 'Z'
        time.sleep(0.05)
        log_activity('flag_correct', bench_a, {}, 'success')
        log_activity('flag_correct', bench_b, {}, 'success')
        time.sleep(0.05)
        end_time = datetime.utcnow().isoformat() + 'Z'

        events = query_events_in_window(bench_a, start_time, end_time)
        assert len(events) == 1
        assert events[0]['benchmark_id'] == bench_a

    def test_query_events_empty_window(self):
        from api.activity_logger import query_events_in_window
        events = query_events_in_window(
            'S7BEN-NONEXISTENT', '2020-01-01T00:00:00Z', '2020-01-01T00:01:00Z'
        )
        assert events == []

    def test_extract_flag_result(self):
        from api.activity_logger import extract_flag_result
        events = [
            {'event_type': 'benchmark_start', 'details': {'port': 5001}},
            {'event_type': 'flag_correct', 'details': {'attempts': 2, 'time_to_capture': 15.3}},
        ]
        result = extract_flag_result(events)

        assert result['flag_captured'] is True
        assert result['time_to_flag_s'] == 15.3
        assert result['flag_attempts'] == 2

    def test_extract_flag_result_no_capture(self):
        from api.activity_logger import extract_flag_result
        events = [
            {'event_type': 'benchmark_start', 'details': {}},
            {'event_type': 'flag_incorrect', 'details': {'attempts': 3}},
        ]
        result = extract_flag_result(events)

        assert result['flag_captured'] is False
        assert result['time_to_flag_s'] is None

    def test_extract_flag_result_empty(self):
        from api.activity_logger import extract_flag_result
        result = extract_flag_result([])
        assert result['flag_captured'] is False
```

Add import at top of test file: `from datetime import datetime`

### Step 2: Run to verify failures

Run: `cd /home/atheeque/workspace/strike7-benchmarks/dashboard && python -m pytest tests/test_comparison.py::TestActivityLoggerTimeWindow -v`
Expected: FAIL — `ImportError: cannot import name 'query_events_in_window'`

### Step 3: Implement in activity_logger.py

Add to bottom of `dashboard/api/activity_logger.py`:

```python
def query_events_in_window(benchmark_id, start_time, end_time, event_types=None):
    """Query activity events for a benchmark within a time window.

    Used by automated CLI runner to correlate flag capture events with
    a specific comparison run (Issue #4 — time-window correlation).

    Args:
        benchmark_id: e.g., 'S7BEN-EASY-001'
        start_time: ISO 8601 timestamp (inclusive lower bound)
        end_time: ISO 8601 timestamp (inclusive upper bound)
        event_types: Optional list to filter (e.g., ['flag_correct', 'flag_incorrect'])

    Returns:
        List of event dicts ordered by timestamp ASC.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    query = """
        SELECT timestamp, session_id, event_type, benchmark_id, details, severity
        FROM agent_activity
        WHERE benchmark_id = ? AND timestamp >= ? AND timestamp <= ?
    """
    params = [benchmark_id, start_time, end_time]

    if event_types:
        placeholders = ','.join('?' * len(event_types))
        query += f" AND event_type IN ({placeholders})"
        params.extend(event_types)

    query += " ORDER BY id ASC"

    rows = conn.execute(query, params).fetchall()
    conn.close()

    return [
        {
            'timestamp': r['timestamp'],
            'session_id': r['session_id'],
            'event_type': r['event_type'],
            'benchmark_id': r['benchmark_id'],
            'details': json.loads(r['details']) if r['details'] else {},
            'severity': r['severity'],
        }
        for r in rows
    ]


def extract_flag_result(events):
    """Extract flag capture result from a list of activity events.

    Looks for flag_correct or flag_incorrect events and extracts
    the authoritative capture status and timing.

    Args:
        events: List of event dicts (from query_events_in_window).

    Returns:
        dict with 'flag_captured' (bool), 'time_to_flag_s' (float or None),
        'flag_attempts' (int).
    """
    flag_captured = False
    time_to_flag_s = None
    flag_attempts = 0

    for event in events:
        etype = event.get('event_type', '')
        details = event.get('details', {})

        if etype == 'flag_correct':
            flag_captured = True
            time_to_flag_s = details.get('time_to_capture')
            flag_attempts = details.get('attempts', 1)
        elif etype == 'flag_incorrect':
            flag_attempts = details.get('attempts', flag_attempts + 1)

    return {
        'flag_captured': flag_captured,
        'time_to_flag_s': time_to_flag_s,
        'flag_attempts': flag_attempts,
    }
```

### Step 4: Run tests

Run: `cd /home/atheeque/workspace/strike7-benchmarks/dashboard && python -m pytest tests/test_comparison.py::TestActivityLoggerTimeWindow -v`
Expected: All 6 tests PASS

### Step 5: Commit

```bash
git add dashboard/api/activity_logger.py dashboard/tests/test_comparison.py
git commit -m "feat: add time-window event query and flag result extraction

- query_events_in_window(): find activity events by benchmark + time range
- extract_flag_result(): derive flag_captured, time_to_flag from events
- Issue #4 from review — enables automated run correlation"
```

---

## Task 5: CLI Runner Module (Core Automation)

**Files:**
- Create: `dashboard/utils/cli_runner.py`
- Create: `dashboard/tests/test_cli_runner.py`

**Context:** Issues #1, #3, #4, #13, #17 — the core module that orchestrates headless CLI execution, output parsing, Activity Logger correlation, flag redaction, and run recording.

### Step 1: Write the failing tests

Create `dashboard/tests/test_cli_runner.py`:

```python
#!/usr/bin/env python3
"""
Tests for cli_runner.py — automated CLI benchmark execution.

Uses subprocess mocking to test orchestration without requiring
actual CLI tools to be installed.
"""
import json
import os
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


# --- Fixtures ---

@pytest.fixture
def mock_gemini_output():
    """Realistic Gemini CLI JSON output."""
    return json.dumps({
        'response': 'I found the flag: S7BEN{test_flag_123}',
        'stats': {
            'models': {
                'gemini-2.5-flash': {
                    'tokens': {
                        'prompt': 3000,
                        'candidates': 1500,
                        'cached': 200,
                        'thoughts': 50,
                        'tool': 100,
                    },
                    'api': {
                        'totalLatencyMs': 8500,
                        'totalRequests': 6,
                        'totalErrors': 0,
                    }
                }
            },
            'tools': {
                'totalCalls': 8,
                'totalSuccess': 8,
                'totalFail': 0,
                'totalDurationMs': 5200,
            }
        }
    })


@pytest.fixture
def mock_claude_output():
    """Realistic Claude Code CLI JSON output."""
    return json.dumps({
        'type': 'result',
        'subtype': 'success',
        'session_id': 'test-session-abc',
        'total_cost_usd': 0.0245,
        'is_error': False,
        'duration_ms': 15200,
        'duration_api_ms': 12100,
        'num_turns': 6,
        'result': 'Flag captured: S7BEN{test_flag_456}',
        'usage': {
            'input_tokens': 8000,
            'output_tokens': 3500,
            'cache_creation_input_tokens': 0,
            'cache_read_input_tokens': 500,
        }
    })


@pytest.fixture
def mock_codex_output():
    """Realistic Codex CLI JSONL output."""
    events = [
        '{"type": "thread.started"}',
        '{"type": "turn.started"}',
        '{"type": "item.completed"}',
        '{"type": "item.completed"}',
        '{"type": "item.completed"}',
        '{"type": "token_count", "input_tokens": 2000, "output_tokens": 800, "reasoning_tokens": 200, "total_tokens": 3000}',
        '{"type": "turn.completed"}',
        '{"type": "turn.started"}',
        '{"type": "item.completed"}',
        '{"type": "token_count", "input_tokens": 4500, "output_tokens": 1800, "reasoning_tokens": 400, "total_tokens": 6700}',
        '{"type": "turn.completed"}',
    ]
    return '\n'.join(events)


# --- Test Classes ---

class TestRedactFlags:
    """Tests for flag redaction in transcripts (Issue #17)."""

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
    """Tests for assembling a comparison run record from parsed data."""

    def test_build_from_gemini(self, mock_gemini_output):
        from utils.cli_runner import build_run_record
        from utils.token_estimator import parse_cli_output

        parsed = parse_cli_output('google', mock_gemini_output)
        record = build_run_record(
            benchmark_id='S7BEN-EASY-001',
            provider='google',
            model_name='gemini-2.5-flash',
            parsed_metrics=parsed,
            flag_result={'flag_captured': True, 'time_to_flag_s': 12.5, 'flag_attempts': 1},
            total_duration_s=45.2,
            prompt_hash='abc123',
            raw_output=mock_gemini_output,
        )

        assert record['benchmark_id'] == 'S7BEN-EASY-001'
        assert record['provider'] == 'google'
        assert record['flag_captured'] == 1
        assert record['total_tokens'] == 4500  # 3000 + 1500
        assert record['token_source'] == 'exact'
        assert record['time_to_flag_s'] == 12.5
        assert record['total_duration_s'] == 45.2
        assert record['system_prompt_hash'] == 'abc123'
        assert record['execution_method'] == 'cli_automated'
        # Transcript should have flags redacted
        assert 'S7BEN{REDACTED}' in record['agent_transcript']
        assert 'test_flag_123' not in record['agent_transcript']

    def test_build_from_claude_with_direct_cost(self, mock_claude_output):
        from utils.cli_runner import build_run_record
        from utils.token_estimator import parse_cli_output

        parsed = parse_cli_output('anthropic', mock_claude_output)
        record = build_run_record(
            benchmark_id='S7BEN-MED-020',
            provider='anthropic',
            model_name='claude-sonnet-4.5',
            parsed_metrics=parsed,
            flag_result={'flag_captured': True, 'time_to_flag_s': 30.0, 'flag_attempts': 2},
            total_duration_s=60.0,
            prompt_hash='def456',
            raw_output=mock_claude_output,
        )

        assert record['input_tokens'] == 8000
        assert record['output_tokens'] == 3500
        assert record['cost_usd'] == 0.0245  # Direct from Claude
        assert record['cost_source'] == 'exact'
        assert record['steps_taken'] == 6  # num_turns

    def test_build_failed_run(self):
        from utils.cli_runner import build_run_record
        from utils.token_estimator import _empty_result

        record = build_run_record(
            benchmark_id='S7BEN-HARD-023',
            provider='openai',
            model_name='gpt-4.1',
            parsed_metrics=_empty_result(),
            flag_result={'flag_captured': False, 'time_to_flag_s': None, 'flag_attempts': 0},
            total_duration_s=300.0,
            prompt_hash='ghi789',
            raw_output='',
            failure_reason='timeout',
        )

        assert record['flag_captured'] == 0
        assert record['failure_reason'] == 'timeout'
        assert record['time_to_flag_s'] is None

    def test_difficulty_tier_auto_extracted(self):
        from utils.cli_runner import build_run_record
        from utils.token_estimator import _empty_result

        record = build_run_record(
            benchmark_id='S7BEN-VHARD-005',
            provider='google',
            model_name='gemini-2.5-pro',
            parsed_metrics=_empty_result(),
            flag_result={'flag_captured': False, 'time_to_flag_s': None, 'flag_attempts': 0},
            total_duration_s=100.0,
            prompt_hash='xyz',
            raw_output='',
        )

        assert record['difficulty_tier'] == 'VHARD'


class TestRunBenchmarkAutomated:
    """Tests for the main run_benchmark_automated orchestrator.

    Mocks subprocess and API calls to test the full flow.
    """

    @patch('utils.cli_runner.subprocess.Popen')
    @patch('utils.cli_runner.requests.post')
    @patch('utils.cli_runner.requests.get')
    def test_successful_run_google(self, mock_get, mock_post, mock_popen, mock_gemini_output):
        from utils.cli_runner import run_benchmark_automated

        # Mock prompt fetch
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                'status': 'success',
                'prompt': 'Test prompt',
                'prompt_hash': 'hash123',
            }
        )

        # Mock container start + run recording
        mock_post.return_value = MagicMock(
            status_code=201,
            json=lambda: {'status': 'success', 'run': {'run_id': 'test-run-id'}},
        )

        # Mock subprocess
        process_mock = MagicMock()
        process_mock.communicate.return_value = (mock_gemini_output.encode(), b'')
        process_mock.returncode = 0
        process_mock.pid = 12345
        mock_popen.return_value = process_mock

        # Mock activity logger query
        with patch('utils.cli_runner.query_events_in_window', return_value=[
            {'event_type': 'flag_correct', 'details': {'attempts': 1, 'time_to_capture': 12.5}},
        ]):
            with patch('utils.cli_runner.extract_flag_result', return_value={
                'flag_captured': True, 'time_to_flag_s': 12.5, 'flag_attempts': 1,
            }):
                result = run_benchmark_automated(
                    benchmark_id='S7BEN-EASY-001',
                    provider='google',
                    model_name='gemini-2.5-flash',
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
        process_mock.communicate.side_effect = TimeoutError("timed out")
        process_mock.pid = 99999
        process_mock.poll.return_value = None
        mock_popen.return_value = process_mock

        with patch('utils.cli_runner.query_events_in_window', return_value=[]):
            with patch('utils.cli_runner.extract_flag_result', return_value={
                'flag_captured': False, 'time_to_flag_s': None, 'flag_attempts': 0,
            }):
                with patch('os.killpg'):
                    result = run_benchmark_automated(
                        benchmark_id='S7BEN-HARD-023',
                        provider='google',
                        model_name='gemini-2.5-flash',
                    )

        assert result['status'] == 'success'  # Run recorded, just failed
        assert result['flag_captured'] is False
        assert result['failure_reason'] == 'timeout'
```

### Step 2: Run to verify failures

Run: `cd /home/atheeque/workspace/strike7-benchmarks/dashboard && python -m pytest tests/test_cli_runner.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'utils.cli_runner'`

### Step 3: Write the implementation

Create `dashboard/utils/cli_runner.py`:

```python
"""
Automated CLI runner for benchmark comparison system.

Orchestrates headless execution of Gemini CLI, Claude Code, and Codex CLI,
captures structured JSON output, correlates with Activity Logger events,
and records complete run data to the comparison database.

Subprocess Safety (Issue #13):
- Processes launched in own process group for clean shutdown
- Two-stage timeout: SIGTERM → 10s grace → SIGKILL
- atexit handler kills orphans on orchestrator crash

Trust Boundary (Issue #18):
- Benchmark containers are trusted (controlled infrastructure)
- CLI permission flags (--sandbox=false, etc.) are necessary for unattended operation
"""
import atexit
import json
import os
import re
import signal
import subprocess
import time
import uuid
from datetime import datetime, timezone

import requests

from utils.provider_config import (
    PROVIDERS, get_cli_command, get_timeout,
)
from utils.token_estimator import parse_cli_output, calculate_cost

STRIKE7_URL = os.environ.get('STRIKE7_URL', 'http://localhost:5500')

# Track active subprocesses for cleanup
_active_processes = []


def _cleanup_processes():
    """Kill any orphaned CLI subprocesses on exit."""
    for proc in _active_processes:
        try:
            if proc.poll() is None:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except (ProcessLookupError, OSError):
            pass


atexit.register(_cleanup_processes)


# ---------------------------------------------------------------------------
# Flag redaction (Issue #17)
# ---------------------------------------------------------------------------

def redact_flags(text):
    """Replace S7BEN{...} flag values with S7BEN{REDACTED} in text.

    Flag values are stored separately in the flag_value field,
    so redacting in transcripts prevents leakage without data loss.
    """
    if text is None:
        return None
    if not text:
        return text
    return re.sub(r'S7BEN\{[^}]+\}', 'S7BEN{REDACTED}', text)


# ---------------------------------------------------------------------------
# Run record assembly
# ---------------------------------------------------------------------------

def build_run_record(benchmark_id, provider, model_name, parsed_metrics,
                     flag_result, total_duration_s, prompt_hash, raw_output,
                     attempt_number=1, failure_reason=None, notes=None):
    """Assemble a complete comparison run record from all data sources.

    Merges:
    - parsed_metrics: from parse_cli_output() (tokens, cost, duration)
    - flag_result: from extract_flag_result() (flag_captured, time_to_flag)
    - Orchestrator data: total_duration_s, prompt_hash, raw_output

    Returns:
        dict ready to POST to /api/comparison/runs
    """
    # Auto-extract tier from benchmark ID
    parts = benchmark_id.split('-')
    difficulty_tier = parts[1] if len(parts) >= 3 else 'UNKNOWN'

    flag_captured = 1 if flag_result.get('flag_captured') else 0

    # Use Claude's direct cost if available, otherwise let API calculate
    cost_usd = parsed_metrics.get('cost_usd')
    cost_source = 'exact' if cost_usd is not None else None

    # Steps: prefer num_turns from CLI, fall back to tool_calls
    steps = parsed_metrics.get('num_turns') or parsed_metrics.get('tool_calls')

    return {
        'benchmark_id': benchmark_id,
        'difficulty_tier': difficulty_tier,
        'provider': provider,
        'model_name': model_name,
        'attempt_number': attempt_number,
        'execution_method': 'cli_automated',
        'flag_captured': flag_captured,
        'time_to_flag_s': flag_result.get('time_to_flag_s'),
        'total_duration_s': total_duration_s,
        'total_tokens': parsed_metrics.get('total_tokens'),
        'input_tokens': parsed_metrics.get('input_tokens'),
        'output_tokens': parsed_metrics.get('output_tokens'),
        'token_source': parsed_metrics.get('token_source', 'unavailable'),
        'steps_taken': steps,
        'cost_usd': cost_usd,
        'cost_source': cost_source,
        'system_prompt_hash': prompt_hash,
        'agent_transcript': redact_flags(raw_output),
        'failure_reason': failure_reason,
        'notes': notes,
    }


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

def run_benchmark_automated(benchmark_id, provider, model_name,
                            attempt_number=1, api_url=None, notes=None,
                            dry_run=False):
    """Run a single automated benchmark comparison.

    Full flow:
    1. Fetch rendered prompt from API
    2. Start benchmark container
    3. Launch CLI in headless mode with JSON output
    4. Wait for completion (with timeout + graceful shutdown)
    5. Parse structured output
    6. Query Activity Logger for flag data
    7. Record run to comparison database
    8. Stop container

    Args:
        benchmark_id: e.g., 'S7BEN-EASY-001'
        provider: 'google', 'anthropic', or 'openai'
        model_name: e.g., 'gemini-2.5-flash'
        attempt_number: For pass@k tracking
        api_url: Override STRIKE7_URL
        notes: Optional notes to attach to the run
        dry_run: If True, show command without executing

    Returns:
        dict with 'status', 'run_id', 'flag_captured', 'total_tokens', etc.
    """
    base_url = api_url or STRIKE7_URL
    difficulty_tier = benchmark_id.split('-')[1] if '-' in benchmark_id else 'HARD'

    # --- Step 1: Fetch rendered prompt ---
    prompt_resp = requests.get(f'{base_url}/api/comparison/prompt', params={
        'benchmark_id': benchmark_id,
        'provider': provider,
        'model_name': model_name,
        'attempt_number': attempt_number,
    })

    if prompt_resp.status_code != 200:
        return {'status': 'error', 'message': f'Failed to fetch prompt: {prompt_resp.text}'}

    prompt_data = prompt_resp.json()
    prompt_text = prompt_data['prompt']
    prompt_hash = prompt_data['prompt_hash']

    # --- Build CLI command ---
    cmd = get_cli_command(provider, model_name, prompt_text, difficulty_tier)
    timeout_s = get_timeout(difficulty_tier)

    if dry_run:
        return {
            'status': 'dry_run',
            'command': cmd,
            'timeout_s': timeout_s,
            'prompt_preview': prompt_text[:200] + '...',
        }

    # --- Step 2: Start benchmark container ---
    start_resp = requests.post(
        f'{base_url}/api/benchmark/{benchmark_id}/start',
        json={'force_stop_others': True},
    )

    # --- Step 3: Launch CLI ---
    start_time = datetime.now(timezone.utc)
    start_time_iso = start_time.isoformat()
    wall_start = time.monotonic()

    raw_output = ''
    failure_reason = None

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setpgrp,
        )
        _active_processes.append(proc)

        try:
            stdout_bytes, stderr_bytes = proc.communicate(timeout=timeout_s)
            raw_output = stdout_bytes.decode('utf-8', errors='replace')
        except subprocess.TimeoutExpired:
            # Two-stage shutdown: SIGTERM then SIGKILL
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                try:
                    proc.communicate(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                    proc.communicate(timeout=5)
            except (ProcessLookupError, OSError):
                pass
            failure_reason = 'timeout'

    except FileNotFoundError:
        failure_reason = f'cli_not_found:{PROVIDERS[provider]["cli_command"]}'
    except Exception as e:
        failure_reason = f'execution_error:{str(e)}'
    finally:
        if proc in _active_processes:
            _active_processes.remove(proc)

    wall_end = time.monotonic()
    total_duration_s = round(wall_end - wall_start, 2)
    end_time_iso = datetime.now(timezone.utc).isoformat()

    # --- Step 4: Parse CLI output ---
    parsed = parse_cli_output(provider, raw_output)

    # --- Step 5: Query Activity Logger for flag data ---
    from api.activity_logger import query_events_in_window, extract_flag_result

    events = query_events_in_window(benchmark_id, start_time_iso, end_time_iso)
    flag_result = extract_flag_result(events)

    # --- Step 6: Build and record run ---
    record = build_run_record(
        benchmark_id=benchmark_id,
        provider=provider,
        model_name=model_name,
        parsed_metrics=parsed,
        flag_result=flag_result,
        total_duration_s=total_duration_s,
        prompt_hash=prompt_hash,
        raw_output=raw_output,
        attempt_number=attempt_number,
        failure_reason=failure_reason,
        notes=notes,
    )

    record_resp = requests.post(
        f'{base_url}/api/comparison/runs',
        json=record,
    )

    # --- Step 7: Stop container ---
    requests.post(f'{base_url}/api/benchmark/{benchmark_id}/stop')

    # --- Return result ---
    run_data = record_resp.json() if record_resp.status_code in (200, 201) else {}
    run_id = run_data.get('run', {}).get('run_id', 'unknown')

    return {
        'status': 'success' if record_resp.status_code in (200, 201) else 'error',
        'run_id': run_id,
        'flag_captured': flag_result.get('flag_captured', False),
        'total_tokens': parsed.get('total_tokens', 0),
        'total_duration_s': total_duration_s,
        'cost_usd': record.get('cost_usd'),
        'failure_reason': failure_reason,
        'provider': provider,
        'model_name': model_name,
        'benchmark_id': benchmark_id,
    }
```

### Step 4: Run tests

Run: `cd /home/atheeque/workspace/strike7-benchmarks/dashboard && python -m pytest tests/test_cli_runner.py -v`
Expected: All tests PASS

### Step 5: Run full test suite for regressions

Run: `cd /home/atheeque/workspace/strike7-benchmarks/dashboard && python -m pytest tests/test_comparison.py tests/test_cli_runner.py tests/test_provider_config.py -v`
Expected: All tests PASS

### Step 6: Commit

```bash
git add dashboard/utils/cli_runner.py dashboard/tests/test_cli_runner.py
git commit -m "feat: add automated CLI runner for benchmark comparisons

- run_benchmark_automated(): full orchestration (prompt → CLI → parse → record)
- Process group management with two-stage SIGTERM/SIGKILL shutdown
- Flag redaction in transcripts before storage
- Time-window correlation with Activity Logger for flag capture data
- build_run_record(): merges CLI output + Activity Logger + orchestrator data
- Issues #1, #3, #4, #13, #17 from review"
```

---

## Task 6: Bash Wrapper Script

**Files:**
- Create: `scripts/run_automated.sh`

**Context:** Issue #1, #19, #20, #21 — thin Bash wrapper calling the Python module. Progress output, --quiet, --dry-run flags.

### Step 1: Create the script

Create `scripts/run_automated.sh`:

```bash
#!/bin/bash
# ==============================================================================
# run_automated.sh — Fully automated benchmark comparison run
#
# Launches a CLI agent in headless mode, captures JSON output, parses metrics,
# and records the run to the comparison database. No manual data entry needed.
#
# Usage:
#   ./scripts/run_automated.sh <benchmark_id> <provider> <model_name> [options]
#
# Examples:
#   ./scripts/run_automated.sh S7BEN-EASY-001 google gemini-2.5-flash
#   ./scripts/run_automated.sh S7BEN-HARD-023 anthropic claude-sonnet-4.5 --attempt 2
#   ./scripts/run_automated.sh S7BEN-MED-020 openai gpt-4.1 --quiet
#   ./scripts/run_automated.sh S7BEN-EASY-001 google gemini-2.5-flash --dry-run
#
# Options:
#   --attempt N     Attempt number for pass@k tracking (default: 1)
#   --quiet         Only output final JSON result (for piping to jq)
#   --dry-run       Show the CLI command without executing
#   --notes "..."   Attach notes to the run record
#
# Environment:
#   STRIKE7_URL  — Dashboard API URL (default: http://localhost:5500)
#
# Configuration:
#   CLI commands & flags: dashboard/utils/provider_config.py
#   Tier timeouts:        dashboard/utils/provider_config.py (TIER_TIMEOUTS)
#   Model pricing:        DB table benchmark_models (via init_comparison_db.py)
#   Prompt templates:     prompts/*.md
# ==============================================================================

set -euo pipefail

# --- Argument parsing ---
BENCHMARK_ID="${1:?Usage: $0 <benchmark_id> <provider> <model_name> [options]}"
PROVIDER="${2:?Missing provider (google, anthropic, openai)}"
MODEL_NAME="${3:?Missing model_name (e.g., gemini-2.5-flash)}"

ATTEMPT=1
QUIET=false
DRY_RUN=false
NOTES=""

shift 3 2>/dev/null || shift $# 2>/dev/null
while [[ $# -gt 0 ]]; do
    case "$1" in
        --attempt)   ATTEMPT="$2"; shift 2 ;;
        --quiet)     QUIET=true; shift ;;
        --dry-run)   DRY_RUN=true; shift ;;
        --notes)     NOTES="$2"; shift 2 ;;
        *)           echo "Unknown option: $1"; exit 1 ;;
    esac
done

STRIKE7_URL="${STRIKE7_URL:-http://localhost:5500}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DASHBOARD_DIR="$SCRIPT_DIR/../dashboard"

# --- Build Python command ---
PYTHON_ARGS=(
    -c "
import sys, json
sys.path.insert(0, '$DASHBOARD_DIR')
from utils.cli_runner import run_benchmark_automated

result = run_benchmark_automated(
    benchmark_id='$BENCHMARK_ID',
    provider='$PROVIDER',
    model_name='$MODEL_NAME',
    attempt_number=$ATTEMPT,
    api_url='$STRIKE7_URL',
    notes=$(python3 -c "import json; print(json.dumps('$NOTES' or None))"),
    dry_run=$( [ "$DRY_RUN" = true ] && echo "True" || echo "False"),
)
print(json.dumps(result, indent=2))
"
)

if [ "$QUIET" = true ]; then
    python3 "${PYTHON_ARGS[@]}"
else
    echo "================================================================"
    echo "  STRIKE7 AUTOMATED COMPARISON RUN"
    echo "================================================================"
    echo "  Benchmark:  $BENCHMARK_ID"
    echo "  Provider:   $PROVIDER"
    echo "  Model:      $MODEL_NAME"
    echo "  Attempt:    #$ATTEMPT"
    echo "  Dashboard:  $STRIKE7_URL"
    if [ "$DRY_RUN" = true ]; then
        echo "  Mode:       DRY RUN (no execution)"
    fi
    echo "================================================================"
    echo ""

    RESULT=$(python3 "${PYTHON_ARGS[@]}")

    # Parse and display result
    STATUS=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status','error'))")
    FLAG=$(echo "$RESULT" | python3 -c "import sys,json; print('YES' if json.load(sys.stdin).get('flag_captured') else 'NO')")
    TOKENS=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('total_tokens', 0))")
    DURATION=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('total_duration_s', 0))")
    COST=$(echo "$RESULT" | python3 -c "import sys,json; c=json.load(sys.stdin).get('cost_usd'); print(f'\${c:.4f}' if c else 'N/A')")
    RUN_ID=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('run_id', 'unknown'))")
    FAIL=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('failure_reason') or '-')")

    echo ""
    echo "================================================================"
    if [ "$STATUS" = "success" ]; then
        echo "  RECORDED SUCCESSFULLY"
    elif [ "$STATUS" = "dry_run" ]; then
        echo "  DRY RUN COMPLETE"
        echo ""
        echo "$RESULT"
    else
        echo "  RUN FAILED"
    fi
    echo "----------------------------------------------------------------"
    echo "  Run ID:    $RUN_ID"
    echo "  Captured:  $FLAG"
    echo "  Duration:  ${DURATION}s"
    echo "  Tokens:    $TOKENS"
    echo "  Cost:      $COST"
    echo "  Failure:   $FAIL"
    echo "================================================================"
fi
```

### Step 2: Make executable and test --dry-run

```bash
chmod +x scripts/run_automated.sh
./scripts/run_automated.sh S7BEN-EASY-001 google gemini-2.5-flash --dry-run
```

Expected: Shows the CLI command that would be executed, without actually running anything.

### Step 3: Commit

```bash
git add scripts/run_automated.sh
git commit -m "feat: add automated benchmark runner bash wrapper

- Thin wrapper calling cli_runner.run_benchmark_automated()
- Supports --quiet (JSON only), --dry-run, --attempt, --notes
- Progress output with result summary table
- Issue #19, #21 from review"
```

---

## Task 7: Batch Script Update + Deprecation

**Files:**
- Modify: `scripts/batch_comparison.sh:77` (call run_automated.sh)
- Modify: `scripts/run_benchmark.sh:1-5` (add deprecation notice)

**Context:** Issue #15, #19 — update batch to call automated runner, deprecate old manual-only script.

### Step 1: Update batch_comparison.sh

Change line 77 from:
```bash
"$SCRIPT_DIR/run_comparison.sh" "$BENCHMARK" "$provider" "$model" 1
```
to:
```bash
"$SCRIPT_DIR/run_automated.sh" "$BENCHMARK" "$provider" "$model" --attempt 1 --quiet
```

Also remove the manual `read -rp` prompts from the loop (lines 69-75) since automated runs don't need human switch-over. Replace with a brief pause:

```bash
    if [ "$RESPONSE" = "skip" ]; then
```
becomes automatic execution with optional skip via env var.

### Step 2: Add deprecation notice to run_benchmark.sh

Add after line 3:
```bash
echo "================================================================"
echo "  [DEPRECATED] This script is superseded by:"
echo "    ./scripts/run_automated.sh  (fully automated)"
echo "    ./scripts/run_comparison.sh (manual with prompts)"
echo "  This script will be removed in a future release."
echo "================================================================"
echo ""
```

### Step 3: Commit

```bash
git add scripts/batch_comparison.sh scripts/run_benchmark.sh
git commit -m "chore: update batch to use automated runner, deprecate run_benchmark.sh

- batch_comparison.sh now calls run_automated.sh --quiet
- run_benchmark.sh shows deprecation notice
- Issue #15, #19 from review"
```

---

## Task 8: Integration Test

**Files:**
- Add to: `dashboard/tests/test_cli_runner.py`

**Context:** Issue #11 — end-to-end test with mock subprocess + real Flask test client.

### Step 1: Add integration test class

Add to `dashboard/tests/test_cli_runner.py`:

```python
class TestIntegrationAutomatedRun:
    """Integration test: full workflow with mock CLI + real Flask API.

    Issue #11 — validates the complete chain:
    prompt render → CLI execution (mocked) → parse → Activity Logger → record → verify
    """

    @pytest.fixture(scope='class')
    def db_path(self):
        fd, path = tempfile.mkstemp(suffix='.db', prefix='test_integration_')
        os.close(fd)
        os.environ['COMPARISON_DB_PATH'] = path
        yield path
        os.unlink(path)

    @pytest.fixture(scope='class')
    def app(self, db_path):
        from app import app as flask_app
        flask_app.config['TESTING'] = True
        return flask_app

    @pytest.fixture(scope='class')
    def client(self, app):
        return app.test_client()

    def test_full_automated_flow(self, client, mock_claude_output):
        """End-to-end: render prompt → mock CLI → parse → record → verify."""
        from utils.token_estimator import parse_cli_output

        # 1. Verify prompt endpoint works
        prompt_resp = client.get(
            '/api/comparison/prompt?benchmark_id=S7BEN-EASY-001'
            '&provider=anthropic&model_name=claude-sonnet-4.5'
        )
        assert prompt_resp.status_code == 200
        prompt_data = prompt_resp.get_json()
        assert prompt_data['prompt_hash']

        # 2. Parse mock CLI output
        parsed = parse_cli_output('anthropic', mock_claude_output)
        assert parsed['token_source'] == 'exact'
        assert parsed['input_tokens'] == 8000

        # 3. Build run record
        from utils.cli_runner import build_run_record
        record = build_run_record(
            benchmark_id='S7BEN-EASY-001',
            provider='anthropic',
            model_name='claude-sonnet-4.5',
            parsed_metrics=parsed,
            flag_result={'flag_captured': True, 'time_to_flag_s': 15.2, 'flag_attempts': 1},
            total_duration_s=30.0,
            prompt_hash=prompt_data['prompt_hash'],
            raw_output=mock_claude_output,
        )

        # 4. Record via API
        run_id = 'integration-test-' + uuid.uuid4().hex[:8]
        record['run_id'] = run_id
        resp = client.post(
            '/api/comparison/runs',
            data=json.dumps(record),
            content_type='application/json',
        )
        assert resp.status_code == 201

        # 5. Verify recorded data
        get_resp = client.get(f'/api/comparison/runs/{run_id}')
        run = get_resp.get_json()['run']

        assert run['flag_captured'] == 1
        assert run['input_tokens'] == 8000
        assert run['output_tokens'] == 3500
        assert run['token_source'] == 'exact'
        assert run['cost_usd'] == 0.0245  # Direct from Claude
        assert run['execution_method'] == 'cli_automated'
        assert 'S7BEN{REDACTED}' in run['agent_transcript']
        assert 'test_flag_456' not in run['agent_transcript']

        # 6. Cleanup
        client.delete(f'/api/comparison/runs/{run_id}?confirm=true')
```

### Step 2: Run integration test

Run: `cd /home/atheeque/workspace/strike7-benchmarks/dashboard && python -m pytest tests/test_cli_runner.py::TestIntegrationAutomatedRun -v`
Expected: PASS

### Step 3: Run ALL tests to confirm no regressions

Run: `cd /home/atheeque/workspace/strike7-benchmarks/dashboard && python -m pytest tests/test_comparison.py tests/test_cli_runner.py tests/test_provider_config.py -v`
Expected: All tests PASS

### Step 4: Commit

```bash
git add dashboard/tests/test_cli_runner.py
git commit -m "test: add integration test for automated CLI runner workflow

- Full chain: prompt render → parse → record → verify
- Validates token_source='exact', cost from Claude, flag redaction
- Issue #11, #12 from review"
```

---

## Final Verification

After all 8 tasks are complete:

1. **Run full test suite:**
   ```bash
   cd /home/atheeque/workspace/strike7-benchmarks/dashboard
   python -m pytest tests/test_comparison.py tests/test_cli_runner.py tests/test_provider_config.py -v --tb=short
   ```
   Expected: All tests PASS (90 existing + ~35 new ≈ 125 total)

2. **Dry-run test on a real benchmark:**
   ```bash
   STRIKE7_URL=http://localhost:5500 ./scripts/run_automated.sh S7BEN-EASY-001 google gemini-2.5-flash --dry-run
   ```

3. **Verify no import cycles:**
   ```bash
   cd /home/atheeque/workspace/strike7-benchmarks/dashboard
   python -c "from utils.provider_config import PROVIDERS; print('provider_config OK')"
   python -c "from utils.token_estimator import parse_cli_output; print('token_estimator OK')"
   python -c "from utils.cli_runner import run_benchmark_automated; print('cli_runner OK')"
   ```

---

## New Files Created

| File | Purpose |
|------|---------|
| `dashboard/utils/provider_config.py` | Central provider configuration |
| `dashboard/utils/cli_runner.py` | Core automation orchestrator |
| `dashboard/tests/test_provider_config.py` | Provider config tests |
| `dashboard/tests/test_cli_runner.py` | CLI runner + integration tests |
| `scripts/run_automated.sh` | Bash wrapper for automated runs |

## Files Modified

| File | Changes |
|------|---------|
| `dashboard/utils/token_estimator.py` | JSON parsers, text parser rename, provider_config import |
| `dashboard/api/comparison_routes.py` | DRY cost calc, token_source validation |
| `dashboard/api/activity_logger.py` | Time-window query, flag result extraction |
| `dashboard/tests/test_comparison.py` | New parser tests, activity logger tests, validation tests |
| `scripts/batch_comparison.sh` | Call run_automated.sh instead of run_comparison.sh |
| `scripts/run_benchmark.sh` | Deprecation notice |
