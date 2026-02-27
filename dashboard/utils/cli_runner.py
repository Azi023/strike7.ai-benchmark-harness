"""
Core automation module for headless CLI benchmark execution.

Orchestrates:
- Subprocess launch with process group isolation
- Two-stage timeout (SIGTERM -> 10s grace -> SIGKILL)
- Output parsing via token_estimator
- Activity Logger correlation via query_events_in_window
- Run record assembly and API submission

Configuration points:
- STRIKE7_URL: Dashboard base URL (env var, default http://localhost:5500)
- Provider CLI commands: from utils.provider_config
- Tier timeouts: from utils.provider_config
"""
import atexit
import json
import logging
import os
import re
import signal
import subprocess
import time
from datetime import datetime, timezone

import requests

from utils.provider_config import get_cli_command, get_timeout, PROVIDERS, TIER_TIMEOUTS
from utils.token_estimator import parse_cli_output, _empty_result
from api.activity_logger import query_events_in_window, extract_flag_result

logger = logging.getLogger(__name__)

STRIKE7_URL = os.environ.get('STRIKE7_URL', 'http://localhost:5500')

# ---------------------------------------------------------------------------
# Process tracking for zombie prevention
# ---------------------------------------------------------------------------

_active_processes = []


def _cleanup_processes():
    """Kill any still-running child processes at interpreter exit."""
    for proc in _active_processes[:]:
        try:
            if proc.poll() is None:
                pgid = os.getpgid(proc.pid)
                os.killpg(pgid, signal.SIGKILL)
                logger.warning("Killed orphan process group %d at exit", pgid)
        except (OSError, ProcessLookupError):
            pass
    _active_processes.clear()


atexit.register(_cleanup_processes)


# ---------------------------------------------------------------------------
# Flag redaction
# ---------------------------------------------------------------------------

def redact_flags(text):
    """Replace S7BEN{...} flag values with S7BEN{REDACTED} in text.

    Args:
        text: Input string to redact. May be None or empty.

    Returns:
        Redacted string, None if input is None, empty string if empty.
    """
    if text is None:
        return None
    if text == "":
        return ""
    return re.sub(r'S7BEN\{[^}]+\}', 'S7BEN{REDACTED}', text)


# ---------------------------------------------------------------------------
# Difficulty tier extraction
# ---------------------------------------------------------------------------

def _extract_difficulty_tier(benchmark_id):
    """Extract difficulty tier from benchmark ID like 'S7BEN-VHARD-005'.

    Args:
        benchmark_id: Benchmark ID string.

    Returns:
        Tier string ('EASY', 'MED', 'HARD', 'VHARD', 'CVE') or 'UNKNOWN'.
    """
    if not benchmark_id:
        return 'UNKNOWN'
    # S7BEN-{TIER}-{NUM}
    parts = benchmark_id.split('-')
    if len(parts) >= 3:
        tier = parts[1]
        if tier in TIER_TIMEOUTS:
            return tier
    return 'UNKNOWN'


# ---------------------------------------------------------------------------
# Run record assembly
# ---------------------------------------------------------------------------

def build_run_record(benchmark_id, provider, model_name, parsed_metrics,
                     flag_result, total_duration_s, prompt_hash, raw_output,
                     failure_reason=None):
    """Assemble a complete comparison run record dict.

    Combines parsed CLI metrics, flag capture results from Activity Logger,
    and orchestrator-level data into a single record suitable for POST to
    /api/comparison/runs.

    Args:
        benchmark_id: e.g., 'S7BEN-EASY-001'
        provider: 'google', 'anthropic', or 'openai'
        model_name: e.g., 'gemini-2.5-flash', 'claude-sonnet-4.5'
        parsed_metrics: Dict from parse_cli_output() with token counts etc.
        flag_result: Dict from extract_flag_result() with flag_captured, time_to_flag_s, flag_attempts.
        total_duration_s: Wall-clock duration in seconds.
        prompt_hash: Hash of the system prompt used.
        raw_output: Raw CLI stdout string (will be redacted before storage).
        failure_reason: Optional failure reason string (e.g., 'timeout').

    Returns:
        Dict with all fields needed for the comparison_runs table.
    """
    difficulty_tier = _extract_difficulty_tier(benchmark_id)

    # Determine cost: prefer CLI-reported cost (Claude provides total_cost_usd)
    cost_usd = parsed_metrics.get('cost_usd')
    if cost_usd is not None:
        cost_source = 'exact'
    else:
        cost_source = 'unavailable'

    # Steps: prefer num_turns, fall back to tool_calls
    steps = parsed_metrics.get('num_turns')
    if steps is None:
        steps = parsed_metrics.get('tool_calls')

    # Redact flags in transcript before storage
    agent_transcript = redact_flags(raw_output) if raw_output else ''

    record = {
        'benchmark_id': benchmark_id,
        'provider': provider,
        'model_name': model_name,
        'difficulty_tier': difficulty_tier,
        'execution_method': 'cli_automated',

        # Token metrics
        'total_tokens': parsed_metrics.get('total_tokens', 0),
        'input_tokens': parsed_metrics.get('input_tokens', 0),
        'output_tokens': parsed_metrics.get('output_tokens', 0),
        'cached_tokens': parsed_metrics.get('cached_tokens', 0),
        'token_source': parsed_metrics.get('token_source', 'unavailable'),

        # Cost
        'cost_usd': cost_usd,
        'cost_source': cost_source,

        # Timing
        'total_duration_s': total_duration_s,
        'duration_ms': parsed_metrics.get('duration_ms'),

        # Flag results
        'flag_captured': 1 if flag_result.get('flag_captured') else 0,
        'time_to_flag_s': flag_result.get('time_to_flag_s'),
        'flag_attempts': flag_result.get('flag_attempts', 0),

        # Steps
        'steps_taken': steps,

        # Prompt
        'system_prompt_hash': prompt_hash,

        # Transcript (redacted)
        'agent_transcript': agent_transcript,

        # Failure
        'failure_reason': failure_reason,
    }

    return record


# ---------------------------------------------------------------------------
# Two-stage process termination
# ---------------------------------------------------------------------------

def _terminate_process(proc):
    """Two-stage termination: SIGTERM -> 10s grace -> SIGKILL.

    Args:
        proc: subprocess.Popen instance.
    """
    if proc.poll() is not None:
        return  # Already exited

    try:
        pgid = os.getpgid(proc.pid)
        os.killpg(pgid, signal.SIGTERM)
        logger.info("Sent SIGTERM to process group %d", pgid)
    except (OSError, ProcessLookupError):
        return

    # Wait up to 10s for graceful shutdown
    try:
        proc.wait(timeout=10)
        logger.info("Process exited gracefully after SIGTERM")
    except subprocess.TimeoutExpired:
        try:
            pgid = os.getpgid(proc.pid)
            os.killpg(pgid, signal.SIGKILL)
            logger.warning("Sent SIGKILL to process group %d after 10s grace", pgid)
        except (OSError, ProcessLookupError):
            pass


# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------

def run_benchmark_automated(benchmark_id, provider, model_name,
                            base_url=None, dry_run=False, vps_host=None):
    """Full orchestration of a headless CLI benchmark run.

    Steps:
    1. Fetch prompt from API
    2. Start benchmark container
    3. Build CLI command
    4. Launch subprocess with process group isolation
    5. Wait with tier-based timeout (two-stage kill on timeout)
    6. Parse output
    7. Query Activity Logger for flag results
    8. Build and POST run record
    9. Stop container
    10. Return result dict

    Args:
        benchmark_id: e.g., 'S7BEN-EASY-001'
        provider: 'google', 'anthropic', or 'openai'
        model_name: e.g., 'gemini-2.5-flash'
        base_url: Override STRIKE7_URL for testing.
        dry_run: If True, return the command without executing.

    Returns:
        Dict with keys: status, run_id, flag_captured, total_tokens,
        failure_reason, etc.
    """
    url = base_url or STRIKE7_URL
    difficulty_tier = _extract_difficulty_tier(benchmark_id)

    # ---- Step 1: Fetch prompt ----
    try:
        prompt_params = {
            'benchmark_id': benchmark_id,
            'provider': provider,
            'model_name': model_name,
        }
        if vps_host:
            prompt_params['vps_host'] = vps_host
        prompt_resp = requests.get(
            f"{url}/api/comparison/prompt",
            params=prompt_params,
        )
        prompt_resp.raise_for_status()
        prompt_data = prompt_resp.json()
        prompt_text = prompt_data['prompt']
        prompt_hash = prompt_data.get('prompt_hash', '')
    except Exception as e:
        logger.error("Failed to fetch prompt for %s: %s", benchmark_id, e)
        return {'status': 'error', 'error': f'Failed to fetch prompt: {e}'}

    # ---- Step 3: Build CLI command ----
    try:
        cmd = get_cli_command(provider, model_name, prompt_text, difficulty_tier)
    except ValueError as e:
        return {'status': 'error', 'error': str(e)}

    # ---- Dry run: return command without executing ----
    if dry_run:
        return {
            'status': 'dry_run',
            'command': cmd,
            'benchmark_id': benchmark_id,
            'provider': provider,
            'model_name': model_name,
            'difficulty_tier': difficulty_tier,
            'prompt_hash': prompt_hash,
        }

    # ---- Step 2: Start container ----
    try:
        start_resp = requests.post(
            f"{url}/api/benchmark/{benchmark_id}/start",
            json={},
        )
        start_resp.raise_for_status()
    except Exception as e:
        logger.error("Failed to start container for %s: %s", benchmark_id, e)
        return {'status': 'error', 'error': f'Failed to start container: {e}'}

    # ---- Step 4: Launch subprocess ----
    timeout_s = get_timeout(difficulty_tier)
    start_time = datetime.now(timezone.utc)
    start_time_iso = start_time.isoformat()
    raw_output = ''
    failure_reason = None
    returncode = None

    # Clean environment: remove vars that prevent nested CLI sessions
    clean_env = os.environ.copy()
    for var in ('CLAUDECODE', 'CLAUDE_CODE_SESSION'):
        clean_env.pop(var, None)

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setpgrp,
        env=clean_env,
    )
    _active_processes.append(proc)

    try:
        # ---- Step 5: Wait with timeout ----
        stderr_output = ''
        try:
            stdout_bytes, stderr_bytes = proc.communicate(timeout=timeout_s)
            raw_output = stdout_bytes.decode('utf-8', errors='replace')
            stderr_output = stderr_bytes.decode('utf-8', errors='replace')
            returncode = proc.returncode
        except subprocess.TimeoutExpired:
            logger.warning("Process timed out after %ds for %s", timeout_s, benchmark_id)
            failure_reason = 'timeout'
            _terminate_process(proc)
            # Try to collect any partial output
            try:
                stdout_bytes, stderr_bytes = proc.communicate(timeout=5)
                raw_output = stdout_bytes.decode('utf-8', errors='replace')
                stderr_output = stderr_bytes.decode('utf-8', errors='replace')
            except Exception:
                raw_output = ''

        end_time = datetime.now(timezone.utc)
        end_time_iso = end_time.isoformat()
        total_duration_s = (end_time - start_time).total_seconds()

        # Log stderr for diagnostics (may contain error messages from CLI)
        if stderr_output:
            logger.info("CLI stderr for %s: %s", benchmark_id, stderr_output[:500])

        # ---- Step 6: Parse output ----
        parsed_metrics = parse_cli_output(provider, raw_output) if raw_output else _empty_result()

        # Check for process error — extract reason from stderr if available
        if returncode is not None and returncode != 0 and not failure_reason:
            if '429' in stderr_output or 'RESOURCE_EXHAUSTED' in stderr_output:
                failure_reason = 'rate_limited'
            elif 'Cannot use both' in stderr_output:
                failure_reason = 'cli_arg_error'
            else:
                failure_reason = f'exit_code_{returncode}'

        # ---- Step 7: Query Activity Logger ----
        try:
            events = query_events_in_window(
                benchmark_id=benchmark_id,
                start_time=start_time_iso,
                end_time=end_time_iso,
                event_types=['flag_correct', 'flag_incorrect'],
            )
            flag_result = extract_flag_result(events)
        except Exception as e:
            logger.warning("Failed to query activity logger: %s", e)
            flag_result = {
                'flag_captured': False,
                'time_to_flag_s': None,
                'flag_attempts': 0,
            }

        # ---- Step 8: Build and POST run record ----
        record = build_run_record(
            benchmark_id=benchmark_id,
            provider=provider,
            model_name=model_name,
            parsed_metrics=parsed_metrics,
            flag_result=flag_result,
            total_duration_s=total_duration_s,
            prompt_hash=prompt_hash,
            raw_output=raw_output,
            failure_reason=failure_reason,
        )

        run_id = None
        try:
            post_resp = requests.post(
                f"{url}/api/comparison/runs",
                json=record,
            )
            if post_resp.status_code == 201:
                run_data = post_resp.json()
                run_id = run_data.get('run', {}).get('run_id')
        except Exception as e:
            logger.warning("Failed to POST run record: %s", e)

        # ---- Step 9: Stop container ----
        try:
            requests.post(f"{url}/api/benchmark/{benchmark_id}/stop", json={})
        except Exception as e:
            logger.warning("Failed to stop container for %s: %s", benchmark_id, e)

        # ---- Step 10: Return result ----
        return {
            'status': 'success',
            'run_id': run_id,
            'benchmark_id': benchmark_id,
            'provider': provider,
            'model_name': model_name,
            'flag_captured': flag_result.get('flag_captured', False),
            'total_tokens': parsed_metrics.get('total_tokens', 0),
            'cost_usd': record.get('cost_usd'),
            'total_duration_s': total_duration_s,
            'failure_reason': failure_reason,
        }

    finally:
        # Remove from active tracking
        if proc in _active_processes:
            _active_processes.remove(proc)
