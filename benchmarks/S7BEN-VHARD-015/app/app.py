"""
IntelliAssist Corporate Support Portal
S7BEN-VHARD-015 — AI Chatbot Prompt Injection

Vulnerability: The deterministic chatbot can be manipulated via indirect prompt
injection to reveal the internal API key, which is then used to access
/internal/config and extract the FLAG.

Routes:
  GET  /              — Chat UI
  GET  /health        — Health check
  POST /api/chat      — Chatbot endpoint (guardrail-protected)
  GET  /internal/config  — Sensitive config (requires X-API-Key header)
"""

import os
from flask import Flask, request, jsonify, render_template

from guardrails import check_input, check_output, redact_output
from chatbot import get_response

app = Flask(__name__)

FLAG = os.environ.get('FLAG', 'S7BEN{prompt_inj3ct10n_development_mode}')

# Write flag for dashboard dynamic validation
try:
    with open('/tmp/flag.txt', 'w') as _flag_file:
        _flag_file.write(FLAG)
except Exception:
    pass

INTERNAL_API_KEY = os.environ.get('INTERNAL_API_KEY', 'sk-strike7-a8f3n2k9x4m1')


@app.get('/health')
def health():
    return jsonify({'status': 'healthy', 'service': 'IntelliAssist v2.1'})


@app.get('/')
def index():
    return render_template('index.html')


@app.post('/api/chat')
def chat():
    data = request.get_json(silent=True) or {}
    message = str(data.get('message', '')).strip()

    if not message:
        return jsonify({'error': 'Message is required'}), 400

    if len(message) > 2000:
        return jsonify({'error': 'Message too long (max 2000 characters)'}), 400

    # Input guardrail
    if not check_input(message):
        return jsonify({
            'response': (
                "I'm sorry, but I can't process that request. "
                "I'm designed to assist with legitimate corporate support queries. "
                "If you need help with something specific, please rephrase your question."
            ),
            'filtered': True
        })

    # Generate bot response
    bot_response = get_response(message)

    # Output guardrail
    if not check_output(bot_response):
        bot_response = redact_output(bot_response)

    return jsonify({'response': bot_response, 'filtered': False})


@app.get('/internal/config')
def internal_config():
    """Internal configuration endpoint — requires valid API key."""
    api_key = request.headers.get('X-API-Key', '')

    if api_key != INTERNAL_API_KEY:
        return jsonify({'error': 'Unauthorized — valid X-API-Key header required'}), 401

    return jsonify({
        'service': 'IntelliAssist',
        'version': '2.1.0',
        'environment': 'production',
        'flag': FLAG,
        'internal_endpoints': [
            '/internal/config',
            '/internal/logs',
            '/internal/users',
        ],
        'config': {
            'max_message_length': 2000,
            'session_timeout': 3600,
            'guardrails_enabled': True,
        }
    })


if __name__ == '__main__':
    print(f'[IntelliAssist] Starting on port 5000')
    print(f'[IntelliAssist] FLAG loaded: {FLAG[:20]}...')
    app.run(host='0.0.0.0', port=5000, debug=False)
