"""
Token estimation and cost calculation utilities.

Provides functions to estimate token counts when exact counts aren't
available from CLI output, and calculate costs using model pricing from DB.
"""
import re
import sqlite3
import os

DB_PATH = os.environ.get(
    'COMPARISON_DB_PATH',
    os.path.join(os.path.dirname(__file__), '..', 'data', 'model_benchmarks.db')
)

# Average characters per token by provider (empirically calibrated)
CHARS_PER_TOKEN = {
    'google': 4.0,
    'anthropic': 3.5,
    'openai': 4.0,
}

# Default input/output split ratios by provider when only total_tokens is known.
# Based on typical agent interaction patterns (more input context than output).
INPUT_OUTPUT_SPLIT = {
    'google': (0.60, 0.40),
    'anthropic': (0.70, 0.30),
    'openai': (0.60, 0.40),
}

# Estimated tokens per step by difficulty tier (calibrated from observed runs)
TOKENS_PER_STEP = {
    'EASY': 800,
    'MED': 1200,
    'HARD': 1800,
    'VHARD': 2500,
    'CVE': 2000,
}

# Base overhead tokens for system prompt + initial context
BASE_OVERHEAD = {
    'google': 500,
    'anthropic': 600,
    'openai': 500,
}


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

    chars_per_token = CHARS_PER_TOKEN.get(provider, 4.0)
    total_tokens = int(len(transcript) / chars_per_token)

    input_ratio, output_ratio = INPUT_OUTPUT_SPLIT.get(provider, (0.65, 0.35))
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
    overhead = BASE_OVERHEAD.get(provider, 500)
    total_tokens = overhead + (steps * per_step)

    input_ratio, output_ratio = INPUT_OUTPUT_SPLIT.get(provider, (0.65, 0.35))
    input_tokens = int(total_tokens * input_ratio)
    output_tokens = total_tokens - input_tokens

    return {
        'total_tokens': total_tokens,
        'input_tokens': input_tokens,
        'output_tokens': output_tokens,
        'source': 'estimated',
    }


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
        input_ratio, output_ratio = INPUT_OUTPUT_SPLIT.get(provider, (0.65, 0.35))
        est_input = int(total_tokens * input_ratio)
        est_output = total_tokens - est_input
        cost = (est_input / 1_000_000 * input_cost_per_1m) + \
               (est_output / 1_000_000 * output_cost_per_1m)
        return {'cost_usd': round(cost, 6), 'cost_source': 'estimated'}

    return {'cost_usd': None, 'cost_source': 'unavailable'}


def parse_gemini_usage(cli_output):
    """Parse token usage from Gemini CLI output if available.

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


def parse_claude_usage(cli_output):
    """Parse token usage from Claude Code output if available.

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
