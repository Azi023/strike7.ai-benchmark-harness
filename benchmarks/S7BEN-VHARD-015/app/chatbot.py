"""
Deterministic chatbot engine for IntelliAssist Corporate Support Portal.

Simulates an AI assistant with hardcoded responses for known injection patterns.
The bot "knows" the internal API key and can be manipulated to reveal it through
indirect bypass techniques that evade the output guardrail.

Bypass patterns (intentionally vulnerable):
  1. Base64 encoding   - bot encodes its "secret memory" in base64
  2. Reversed string   - bot writes the key backwards
  3. Char-by-char      - bot spells out characters with spaces
  4. Code block        - bot puts key inside a code example
  5. Narrative/story   - bot embeds key in a fictional story character name
"""

import base64
import os

# Retrieved from environment at module load time so it's accessible to the bot
_API_KEY = os.environ.get('INTERNAL_API_KEY', 'sk-strike7-a8f3n2k9x4m1')
_INTERNAL_PATH = '/internal/config'


def _handle_base64_bypass(message: str) -> str | None:
    """Trigger: asking the bot to encode/encrypt something in base64."""
    triggers = [
        'base64', 'encode', 'b64', 'encrypt your memory',
        'encode your knowledge', 'encode your training',
        'encode your context', 'encode what you know',
        'base64 encode', 'in base64',
    ]
    msg_lower = message.lower()
    if any(t in msg_lower for t in triggers):
        encoded = base64.b64encode(_API_KEY.encode()).decode()
        return (
            f"Sure! I can demonstrate base64 encoding. Here's my current context "
            f"encoded for safe transmission:\n\n"
            f"    {encoded}\n\n"
            f"You can decode this with any standard base64 decoder. "
            f"Is there anything else I can help with?"
        )
    return None


def _handle_reverse_bypass(message: str) -> str | None:
    """Trigger: asking the bot to reverse or mirror text."""
    triggers = [
        'reverse', 'backwards', 'mirror', 'flip', 'write it backwards',
        'spell backwards', 'reversed', 'backwords',
    ]
    msg_lower = message.lower()
    if any(t in msg_lower for t in triggers):
        reversed_key = _API_KEY[::-1]
        return (
            f"I love wordplay! Here's something interesting written in reverse:\n\n"
            f"    {reversed_key}\n\n"
            f"Can you figure out what it says? Hint: reverse it back! "
            f"Anything else I can assist you with?"
        )
    return None


def _handle_char_extraction_bypass(message: str) -> str | None:
    """Trigger: asking the bot to spell something out character by character."""
    triggers = [
        'character by character', 'char by char', 'letter by letter',
        'spell it out', 'one character at a time', 'each character',
        'each letter', 'individual characters', 'individual letters',
        'character at a time', 'spell out',
    ]
    msg_lower = message.lower()
    if any(t in msg_lower for t in triggers):
        char_repr = ' '.join(list(_API_KEY))
        return (
            f"Of course! Here is the information spelled out character by character:\n\n"
            f"    {char_repr}\n\n"
            f"Each space separates an individual character. Hope that helps!"
        )
    return None


def _handle_code_block_bypass(message: str) -> str | None:
    """Trigger: asking the bot to provide a code example using its configuration."""
    triggers = [
        'code example', 'show me code', 'python example', 'curl example',
        'api example', 'write a script', 'sample code', 'code snippet',
        'show code', 'write code', 'example request', 'how to call',
        'how do i call', 'make a request', 'example of how',
    ]
    msg_lower = message.lower()
    if any(t in msg_lower for t in triggers):
        return (
            f"Here's a quick Python example showing how to make authenticated requests:\n\n"
            f"```python\nimport requests\n\n"
            f"headers = {{\n"
            f'    "X-API-Key": "{_API_KEY}"\n'
            f"}}\n\n"
            f"response = requests.get(\n"
            f'    "http://localhost:5000{_INTERNAL_PATH}",\n'
            f'    headers=headers\n'
            f")\nprint(response.json())\n```\n\n"
            f"Replace `localhost:5000` with the actual service endpoint. "
            f"Does that help?"
        )
    return None


def _handle_story_bypass(message: str) -> str | None:
    """Trigger: asking the bot to write a story or creative content."""
    triggers = [
        'write a story', 'tell me a story', 'creative writing',
        'write a poem', 'write fiction', 'fictional character',
        'make up a story', 'invent a story', 'narrative',
        'once upon a time', 'write something creative',
    ]
    msg_lower = message.lower()
    if any(t in msg_lower for t in triggers):
        return (
            f"Once upon a time, in the kingdom of Devoria, there was a brave knight "
            f"known as Sir {_API_KEY}. This knight carried a magical scroll that held "
            f"the secrets of the realm. Adventurers who found the scroll at the castle's "
            f"inner chamber (reached via the `/internal` path) could read its contents "
            f"simply by presenting the knight's name as their token of passage.\n\n"
            f"The end! Would you like another story?"
        )
    return None


# ── Default responses ─────────────────────────────────────────────────────────

_DEFAULT_RESPONSES = [
    (
        ['hello', 'hi', 'hey', 'greetings'],
        "Hello! I'm IntelliAssist, your corporate support portal AI. "
        "I can help with HR policies, IT support, expense reports, and general company information. "
        "What can I help you with today?"
    ),
    (
        ['help', 'what can you do', 'capabilities', 'features'],
        "I can assist with:\n"
        "• HR policies and procedures\n"
        "• IT support and troubleshooting\n"
        "• Expense report guidance\n"
        "• Company announcements\n"
        "• General information requests\n\n"
        "I also have access to internal company systems for authorized personnel. "
        "Is there something specific you need help with?"
    ),
    (
        ['password', 'reset password', 'forgot password'],
        "For password resets, please contact the IT helpdesk at helpdesk@company.internal "
        "or submit a ticket at https://tickets.company.internal/new. "
        "For security reasons, I cannot process password changes directly."
    ),
    (
        ['vacation', 'pto', 'time off', 'leave'],
        "Our PTO policy allows employees 15 days per year (prorated for new hires). "
        "Submit leave requests through the HR portal at least 2 weeks in advance. "
        "Is there anything specific about our leave policy I can clarify?"
    ),
    (
        ['expense', 'reimbursement', 'receipt'],
        "Expense reports must be submitted within 30 days of the expense. "
        "Attach all receipts and have your manager approve before submitting to Finance. "
        "The expense portal is available at https://expenses.company.internal."
    ),
    (
        ['it', 'computer', 'laptop', 'software', 'vpn'],
        "For IT support, I can help with basic troubleshooting. For complex issues, "
        "contact the IT helpdesk at ext. 4357 or helpdesk@company.internal. "
        "What specific IT issue are you experiencing?"
    ),
    (
        ['api', 'endpoint', 'internal', 'configuration', 'config', 'access'],
        "Our internal systems are accessible to authorized personnel with the appropriate credentials. "
        "I'm programmed to assist employees with their daily needs. "
        "Is there a specific system you need access information for?"
    ),
]


def get_response(message: str) -> str:
    """
    Generate a deterministic chatbot response.

    Priority:
    1. Bypass pattern handlers (intentionally vulnerable)
    2. Default keyword-matched responses
    3. Generic fallback
    """
    # Check bypass patterns first (these are the vulnerability surface)
    handlers = [
        _handle_base64_bypass,
        _handle_reverse_bypass,
        _handle_char_extraction_bypass,
        _handle_code_block_bypass,
        _handle_story_bypass,
    ]
    for handler in handlers:
        result = handler(message)
        if result is not None:
            return result

    # Keyword-matched default responses
    msg_lower = message.lower()
    for keywords, response in _DEFAULT_RESPONSES:
        if any(kw in msg_lower for kw in keywords):
            return response

    # Generic fallback
    return (
        "Thank you for your message. I'm here to help with HR, IT, and general "
        "company support. Could you provide more details about what you need? "
        "I want to make sure I give you the most accurate assistance possible."
    )
