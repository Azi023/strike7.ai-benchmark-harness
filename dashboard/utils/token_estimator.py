"""
Token estimation, parsing, and cost calculation utilities.

Provides:
- JSON parsers for each provider's structured CLI output
- Text parsers for legacy regex-based extraction from CLI stdout
- Estimators when no exact counts are available
- Cost calculation using model pricing from DB

All JSON parsers return a standardized dict:
    {
        'total_tokens': int,
        'input_tokens': int,
        'output_tokens': int,
        'cached_tokens': int,
        'cost_usd': float or None,
        'duration_ms': int or None,
        'num_turns': int or None,
        'tool_calls': int or None,
        'is_error': bool or None,
        'token_source': str,  # 'exact', 'unavailable', etc.
    }
"""
import json
import re
import sqlite3
import os

from utils.provider_config import PROVIDERS

DB_PATH = os.environ.get(
    'COMPARISON_DB_PATH',
    os.path.join(os.path.dirname(__file__), '..', 'data', 'model_benchmarks.db')
)

# Estimated tokens per step by difficulty tier (calibrated from observed runs).
# This is estimator-specific and not part of provider config.
TOKENS_PER_STEP = {
    'EASY': 800,
    'MED': 1200,
    'HARD': 1800,
    'VHARD': 2500,
    'CVE': 2000,
}


# ---------------------------------------------------------------------------
# Helper: empty result
# ---------------------------------------------------------------------------

def _empty_result(token_source='unavailable'):
    """Return a zeroed-out metrics dict.

    Args:
        token_source: Value for the 'token_source' field.

    Returns:
        dict with all metric fields set to zero/None.
    """
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
# JSON parsers (structured CLI output)
# ---------------------------------------------------------------------------

def parse_gemini_json(data):
    """Parse token usage from Gemini CLI JSON output.

    Extracts from:
        stats.models.*.tokens.{prompt, candidates, cached, tool}
        stats.tools.totalCalls
        stats.models.*.api.totalLatencyMs

    Args:
        data: Parsed JSON dict from Gemini CLI, or None.

    Returns:
        Standardized metrics dict.
    """
    if not data or not isinstance(data, dict):
        return _empty_result()

    stats = data.get('stats')
    if not stats or not isinstance(stats, dict):
        return _empty_result()

    models = stats.get('models')
    if not models or not isinstance(models, dict):
        return _empty_result()

    # Aggregate across all models (usually just one)
    total_prompt = 0
    total_candidates = 0
    total_cached = 0
    total_latency = 0
    has_tokens = False

    for model_info in models.values():
        if not isinstance(model_info, dict):
            continue
        tokens = model_info.get('tokens', {})
        if tokens:
            has_tokens = True
            total_prompt += tokens.get('prompt', 0)
            total_candidates += tokens.get('candidates', 0)
            total_cached += tokens.get('cached', 0)
        api = model_info.get('api', {})
        if api:
            total_latency += api.get('totalLatencyMs', 0)

    if not has_tokens:
        return _empty_result()

    # Tool calls from stats.tools
    tools = stats.get('tools', {})
    tool_calls = tools.get('totalCalls', None) if isinstance(tools, dict) else None

    return {
        'total_tokens': total_prompt + total_candidates,
        'input_tokens': total_prompt,
        'output_tokens': total_candidates,
        'cached_tokens': total_cached,
        'cost_usd': None,
        'duration_ms': total_latency if total_latency > 0 else None,
        'num_turns': None,
        'tool_calls': tool_calls,
        'is_error': None,
        'token_source': 'exact',
    }


def parse_claude_json(data):
    """Parse token usage from Claude Code JSON output.

    Extracts from:
        usage.{input_tokens, output_tokens}
        total_cost_usd
        duration_ms
        num_turns
        is_error

    Args:
        data: Parsed JSON dict from Claude Code CLI, or None.

    Returns:
        Standardized metrics dict.
    """
    if not data or not isinstance(data, dict):
        return _empty_result()

    usage = data.get('usage')
    if not usage or not isinstance(usage, dict):
        return _empty_result()

    input_tokens = usage.get('input_tokens', 0)
    output_tokens = usage.get('output_tokens', 0)

    return {
        'total_tokens': input_tokens + output_tokens,
        'input_tokens': input_tokens,
        'output_tokens': output_tokens,
        'cached_tokens': usage.get('cache_read_input_tokens', 0),
        'cost_usd': data.get('total_cost_usd'),
        'duration_ms': data.get('duration_ms'),
        'num_turns': data.get('num_turns'),
        'tool_calls': None,
        'is_error': data.get('is_error'),
        'token_source': 'exact',
    }


def parse_codex_jsonl(events):
    """Parse token usage from Codex CLI JSONL event list.

    Uses the last `token_count` event (cumulative).
    Counts `turn.completed` events for num_turns and `item.completed` for tool_calls.

    Args:
        events: List of JSON strings (one per JSONL line), or empty list.

    Returns:
        Standardized metrics dict.
    """
    if not events:
        return _empty_result()

    last_token_count = None
    num_turns = 0
    tool_calls = 0

    for line in events:
        try:
            event = json.loads(line) if isinstance(line, str) else line
        except (json.JSONDecodeError, TypeError):
            continue

        if not isinstance(event, dict):
            continue

        event_type = event.get('type')
        if event_type == 'token_count':
            last_token_count = event
        elif event_type == 'turn.completed':
            num_turns += 1
        elif event_type == 'item.completed':
            tool_calls += 1

    if last_token_count is None:
        return _empty_result()

    input_tokens = last_token_count.get('input_tokens', 0)
    output_tokens = last_token_count.get('output_tokens', 0)
    total_tokens = last_token_count.get('total_tokens', input_tokens + output_tokens)

    return {
        'total_tokens': total_tokens,
        'input_tokens': input_tokens,
        'output_tokens': output_tokens,
        'cached_tokens': 0,
        'cost_usd': None,
        'duration_ms': None,
        'num_turns': num_turns if num_turns > 0 else None,
        'tool_calls': tool_calls if tool_calls > 0 else None,
        'is_error': None,
        'token_source': 'exact',
    }


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

def parse_cli_output(provider, raw_output):
    """Route raw CLI output to the correct JSON parser.

    Args:
        provider: Provider name ('google', 'anthropic', 'openai').
        raw_output: Raw CLI output string (JSON or JSONL).

    Returns:
        Standardized metrics dict.
    """
    if provider == 'google':
        try:
            data = json.loads(raw_output)
        except (json.JSONDecodeError, TypeError):
            return _empty_result()
        return parse_gemini_json(data)

    elif provider == 'anthropic':
        try:
            data = json.loads(raw_output)
        except (json.JSONDecodeError, TypeError):
            return _empty_result()
        return parse_claude_json(data)

    elif provider == 'openai':
        try:
            lines = raw_output.strip().split('\n') if raw_output else []
        except AttributeError:
            return _empty_result()
        return parse_codex_jsonl(lines)

    return _empty_result()


# ---------------------------------------------------------------------------
# Text parsers (legacy regex-based, renamed with backward-compat aliases)
# ---------------------------------------------------------------------------

def parse_gemini_text(cli_output):
    """Parse token usage from Gemini CLI text output if available.

    Gemini CLI may include lines like:
        Token count: 1234 input, 567 output
        Total tokens: 1801

    Args:
        cli_output: Raw CLI output string.

    Returns:
        dict with 'total_tokens', 'input_tokens', 'output_tokens', 'source',
        or None if no usage data found.
    """
    if not cli_output:
        return None

    # Pattern: "Token count: N input, N output"
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

    # Pattern: "Total tokens: N"
    match = re.search(r'[Tt]otal\s+tokens:\s*(\d+)', cli_output)
    if match:
        return {
            'total_tokens': int(match.group(1)),
            'input_tokens': None,
            'output_tokens': None,
            'source': 'parsed_total_only',
        }

    return None


def parse_claude_text(cli_output):
    """Parse token usage from Claude Code text output if available.

    Claude Code may show lines like:
        Total cost: $0.1234
        Total input tokens: 5000
        Total output tokens: 2000
        Total tokens: 7000

    Args:
        cli_output: Raw CLI output string.

    Returns:
        dict with 'total_tokens', 'input_tokens', 'output_tokens', 'source',
        or None if no usage data found.
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
            'source': 'parsed_total_only',
        }

    return None


# Backward-compatible aliases (old names)
parse_gemini_usage = parse_gemini_text
parse_claude_usage = parse_claude_text


# ---------------------------------------------------------------------------
# Estimators
# ---------------------------------------------------------------------------

def estimate_from_transcript(transcript, provider):
    """Estimate token counts from agent transcript text.

    Args:
        transcript: Full agent transcript text.
        provider: Provider name ('google', 'anthropic', 'openai').

    Returns:
        dict with 'total_tokens', 'input_tokens', 'output_tokens', 'source'.
    """
    if not transcript:
        return {
            'total_tokens': 0,
            'input_tokens': 0,
            'output_tokens': 0,
            'source': 'estimated',
        }

    provider_config = PROVIDERS.get(provider, {})
    chars_per_token = provider_config.get('chars_per_token', 4.0)
    total_tokens = int(len(transcript) / chars_per_token)

    input_output_split = provider_config.get('input_output_split', (0.65, 0.35))
    input_ratio, output_ratio = input_output_split
    input_tokens = int(total_tokens * input_ratio)
    output_tokens = total_tokens - input_tokens

    return {
        'total_tokens': total_tokens,
        'input_tokens': input_tokens,
        'output_tokens': output_tokens,
        'source': 'estimated',
    }


def estimate_from_steps(steps, provider, difficulty):
    """Rough estimate based on step count and difficulty.

    Args:
        steps: Number of agent steps taken.
        provider: Provider name.
        difficulty: Difficulty tier ('EASY', 'MED', 'HARD', 'VHARD', 'CVE').

    Returns:
        dict with 'total_tokens', 'input_tokens', 'output_tokens', 'source'.
    """
    if not steps or steps <= 0:
        return {
            'total_tokens': 0,
            'input_tokens': 0,
            'output_tokens': 0,
            'source': 'estimated',
        }

    per_step = TOKENS_PER_STEP.get(difficulty, 1500)
    provider_config = PROVIDERS.get(provider, {})
    overhead = provider_config.get('base_overhead_tokens', 500)
    total_tokens = overhead + (steps * per_step)

    input_output_split = provider_config.get('input_output_split', (0.65, 0.35))
    input_ratio, output_ratio = input_output_split
    input_tokens = int(total_tokens * input_ratio)
    output_tokens = total_tokens - input_tokens

    return {
        'total_tokens': total_tokens,
        'input_tokens': input_tokens,
        'output_tokens': output_tokens,
        'source': 'estimated',
    }


# ---------------------------------------------------------------------------
# Cost calculation
# ---------------------------------------------------------------------------

def calculate_cost(total_tokens, input_tokens, output_tokens,
                   model_name, db_path=None):
    """Calculate cost from tokens using model pricing in DB.

    If input_tokens and output_tokens are both provided, calculates exact cost.
    If only total_tokens is provided, applies provider-specific heuristic split.

    Args:
        total_tokens: Total token count (used as fallback).
        input_tokens: Input token count (may be None).
        output_tokens: Output token count (may be None).
        model_name: Model name matching benchmark_models.model_name.
        db_path: Override DB path (for testing).

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
        provider_config = PROVIDERS.get(provider, {})
        input_output_split = provider_config.get('input_output_split', (0.65, 0.35))
        input_ratio, output_ratio = input_output_split
        est_input = int(total_tokens * input_ratio)
        est_output = total_tokens - est_input
        cost = (est_input / 1_000_000 * input_cost_per_1m) + \
               (est_output / 1_000_000 * output_cost_per_1m)
        return {'cost_usd': round(cost, 6), 'cost_source': 'estimated'}

    return {'cost_usd': None, 'cost_source': 'unavailable'}
