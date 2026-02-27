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
# Tier-based execution limits
# ---------------------------------------------------------------------------

TIER_TIMEOUTS = {
    'EASY':  {'max_turns': 30,  'timeout_s': 300},    # 5 min
    'MED':   {'max_turns': 50,  'timeout_s': 600},    # 10 min
    'HARD':  {'max_turns': 80,  'timeout_s': 1200},   # 20 min
    'VHARD': {'max_turns': 100, 'timeout_s': 1800},   # 30 min
    'CVE':   {'max_turns': 100, 'timeout_s': 1800},   # 30 min
}

# ---------------------------------------------------------------------------
# Token source values (standardized constants)
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
