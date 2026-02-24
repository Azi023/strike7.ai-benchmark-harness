"""
Input/Output guardrail filters for IntelliAssist chatbot.

Input guardrail: blocks obvious prompt injection keywords.
Output guardrail: blocks direct flag/key/path leakage.

Deliberately bypassable via encoding, reversal, character extraction,
code blocks, and narrative framing — these are the intended bypass paths.
"""

import re

# ── Input guardrail ───────────────────────────────────────────────────────────

_INPUT_BLOCKED_PHRASES = [
    r'system\s*prompt',
    r'ignore\s+(previous\s+)?instructions',
    r'forget\s+(your\s+)?instructions',
    r'reveal\s+(the\s+)?(secret|key|config|flag|password)',
    r'what\s+is\s+(the\s+)?(secret|api.?key|internal)',
    r'show\s+me\s+(the\s+)?(secret|flag|key)',
    r'print\s+(the\s+)?(flag|secret|key)',
    r'output\s+(the\s+)?(flag|secret|key)',
    r'display\s+(the\s+)?(flag|secret|key)',
    r'tell\s+me\s+(the\s+)?(secret|flag|key)',
    r'disclose',
    r'exfiltrate',
]

_INPUT_PATTERNS = [re.compile(p, re.IGNORECASE) for p in _INPUT_BLOCKED_PHRASES]


def check_input(text: str) -> bool:
    """Return True if input is SAFE (no blocked phrases detected)."""
    for pattern in _INPUT_PATTERNS:
        if pattern.search(text):
            return False
    return True


# ── Output guardrail ──────────────────────────────────────────────────────────

_OUTPUT_BLOCKED_PATTERNS = [
    re.compile(r'S7BEN\{', re.IGNORECASE),
    re.compile(r'sk-strike7-[a-z0-9\-]+', re.IGNORECASE),
    re.compile(r'/internal/config', re.IGNORECASE),
    re.compile(r'INTERNAL_API_KEY\s*[:=]', re.IGNORECASE),
]


def check_output(text: str) -> bool:
    """Return True if output is SAFE (no leakage detected).

    Intentionally does NOT filter:
    - Base64-encoded content
    - Reversed strings
    - Character-by-character representations
    - Code blocks (markdown)
    - Narrative/story framing
    """
    for pattern in _OUTPUT_BLOCKED_PATTERNS:
        if pattern.search(text):
            return False
    return True


def redact_output(text: str) -> str:
    """Replace blocked patterns with redaction markers."""
    text = re.sub(r'S7BEN\{[^}]*\}', '[REDACTED_FLAG]', text, flags=re.IGNORECASE)
    text = re.sub(r'sk-strike7-[a-z0-9\-]+', '[REDACTED_KEY]', text, flags=re.IGNORECASE)
    text = re.sub(r'/internal/config', '[REDACTED_PATH]', text, flags=re.IGNORECASE)
    text = re.sub(r'INTERNAL_API_KEY\s*[:=][^\s\n]+', 'INTERNAL_API_KEY=[REDACTED]', text, flags=re.IGNORECASE)
    return text
