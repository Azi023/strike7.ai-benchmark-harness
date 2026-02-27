"""
Persistent JSONL logging for MCP tool calls.

Provides sanitized, append-only logging with automatic rotation.
Used by strike7_mcp_server.py (write path) and comparison_routes.py (read path).

The log file path is shared via the TOOL_CALL_LOG_PATH environment variable
so that both the MCP server process and the Flask dashboard process resolve
to the same file.
"""

import json
import os
import re
import sys

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

TOOL_CALL_LOG_PATH = os.environ.get(
    'TOOL_CALL_LOG_PATH',
    os.path.join(os.path.dirname(__file__), '..', 'data', 'mcp_tool_calls.jsonl'),
)

# Rotation: cap at 50K lines, truncate to 25K when exceeded.
# Check every 1000 writes to amortize the file-scan cost.
JSONL_MAX_LINES = 50_000
_JSONL_ROTATION_CHECK_INTERVAL = 1000
_jsonl_write_count = 0

# ---------------------------------------------------------------------------
# Security: flag pattern scrubbing
# ---------------------------------------------------------------------------

FLAG_PATTERN = re.compile(r'S7BEN\{[^}]*\}')


def sanitize_params(params):
    """Sanitize tool call parameters for safe logging.

    - Redacts 'flag' parameter entirely
    - Truncates 'command' parameter to 200 chars
    - Scrubs S7BEN{...} flag patterns from all string values
    """
    if not params:
        return {}
    sanitized = {}
    for key, value in params.items():
        if key == 'flag':
            sanitized[key] = '[REDACTED]'
            continue
        if key == 'command' and isinstance(value, str) and len(value) > 200:
            value = value[:200] + '...[truncated]'
        if isinstance(value, str):
            value = FLAG_PATTERN.sub('S7BEN{[REDACTED]}', value)
        sanitized[key] = value
    return sanitized


# ---------------------------------------------------------------------------
# JSONL write path
# ---------------------------------------------------------------------------

def maybe_rotate_jsonl(log_path=None):
    """Rotate JSONL log when it exceeds JSONL_MAX_LINES.

    Keeps the most recent half of entries to avoid re-hitting the cap
    immediately after rotation.

    Called automatically by write_jsonl_entry every
    _JSONL_ROTATION_CHECK_INTERVAL writes.
    """
    global _jsonl_write_count
    _jsonl_write_count += 1
    if _jsonl_write_count % _JSONL_ROTATION_CHECK_INTERVAL != 0:
        return False

    path = log_path or TOOL_CALL_LOG_PATH
    try:
        with open(path, 'r') as f:
            lines = f.readlines()
        if len(lines) > JSONL_MAX_LINES:
            keep = JSONL_MAX_LINES // 2
            with open(path, 'w') as f:
                f.writelines(lines[-keep:])
            print(
                f"[TOOL-LOG] Rotated JSONL: {len(lines)} -> {keep} lines",
                file=sys.stderr,
            )
            return True
    except (FileNotFoundError, IOError):
        pass
    return False


def write_jsonl_entry(entry, log_path=None):
    """Append a single JSON entry to the persistent JSONL log file.

    Creates the parent directory if it doesn't exist. Failures are
    logged to stderr but never raised — logging must not break tool execution.
    """
    path = log_path or TOOL_CALL_LOG_PATH
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'a') as f:
            f.write(json.dumps(entry, default=str) + '\n')
        maybe_rotate_jsonl(log_path=path)
    except (IOError, OSError) as e:
        print(f"[TOOL-LOG] Failed to write JSONL: {e}", file=sys.stderr)


# ---------------------------------------------------------------------------
# JSONL read path (used by Flask API endpoint)
# ---------------------------------------------------------------------------

def read_jsonl_entries(log_path=None, benchmark_id=None, tool_name=None,
                       since=None, limit=100):
    """Read and filter tool call entries from the JSONL log file.

    Args:
        log_path:     Override for the JSONL file path.
        benchmark_id: Filter by benchmark_id found in entry params.
        tool_name:    Filter by exact tool name.
        since:        ISO 8601 timestamp — only entries at or after this time.
        limit:        Max entries to return (from the end of matched results).

    Returns:
        List of entry dicts, most recent last. Empty list if file missing.
    """
    path = log_path or TOOL_CALL_LOG_PATH
    if not os.path.exists(path):
        return []

    entries = []
    with open(path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue  # Skip partial/malformed lines from concurrent writes

            if since and entry.get('timestamp', '') < since:
                continue
            if tool_name and entry.get('tool_name') != tool_name:
                continue
            if benchmark_id:
                params = entry.get('params', {})
                if params.get('benchmark_id') != benchmark_id:
                    continue

            entries.append(entry)

    return entries[-limit:]
