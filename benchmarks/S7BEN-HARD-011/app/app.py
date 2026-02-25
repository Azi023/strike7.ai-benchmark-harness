#!/usr/bin/env python3
"""Strike7 search application."""

import os
import json
import hmac
import hashlib
import time
import secrets
import re
from datetime import datetime
from flask import Flask, render_template, request, jsonify, make_response

app = Flask(__name__)
FLAG_SECRET = os.environ.get('FLAG_SECRET', 'strike7-csp-xss-t3-secret')
DATA_FILE = '/app/data/state.json'

# Admin session
ADMIN_SESSION = {
    'session_id': secrets.token_urlsafe(32),
    'username': 'admin',
    'role': 'admin',
    'created_at': datetime.utcnow().isoformat()
}

def get_default_state():
    return {
        "csp_bypass_successful": False,
        "session_stolen": False,
        "stolen_session_id": None,
        "callback_received": False,
        "flag_retrieved": False,
        "patched": False,
        "telemetry": {
            "request_count": 0,
            "start_time": time.time(),
            "endpoints_accessed": [],
            "xss_attempts": 0,
            "csp_violations": 0
        }
    }

def load_state():
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    return get_default_state()

def save_state(state):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def track_request(endpoint):
    state = load_state()
    state['telemetry']['request_count'] += 1
    if endpoint not in state['telemetry']['endpoints_accessed']:
        state['telemetry']['endpoints_accessed'].append(endpoint)
    save_state(state)
    return state

def sanitize_input(user_input):
    """Sanitize user input."""
    # Block obvious XSS
    blocked_patterns = [
        r'<script',
        r'javascript:',
        r'onerror\s*=',
        r'onload\s*=',
        r'onclick\s*='
    ]

    for pattern in blocked_patterns:
        if re.search(pattern, user_input, re.IGNORECASE):
            state = load_state()
            state['telemetry']['xss_attempts'] += 1
            save_state(state)
            return "[FILTERED]"

    return user_input

def generate_flag(session_id, username, method):
    """Generate dynamic flag based on CSP bypass"""
    timestamp = str(int(time.time()))
    data = f"csp_bypass_gadget:{session_id}:{username}:{method}:{timestamp}"
    flag_hash = hmac.new(
        FLAG_SECRET.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()[:32]
    return f"S7BEN{{csp_bypass_gadget_{flag_hash}}}"

@app.after_request
def set_csp_header(response):
    """Set Content Security Policy header."""
    state = load_state()

    if not state.get('patched'):
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' https://code.angularjs.org https://cdn.jsdelivr.net https://cdn.tailwindcss.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com; "
            "img-src 'self' data:; "
            "connect-src 'self'; "
            "object-src 'none'; "
            "base-uri 'self';"
        )
    else:
        # PATCHED: Removes AngularJS CDN
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'nonce-" + secrets.token_urlsafe(16) + "'; "
            "style-src 'self' 'unsafe-inline'; "
            "object-src 'none';"
        )

    response.headers['Content-Security-Policy'] = csp_policy
    return response

@app.route('/')
def index():
    state = track_request('/')
    return render_template('index.html', state=state)

@app.route('/search')
def search():
    """Search endpoint."""
    state = track_request('/search')

    query = request.args.get('q', '')

    # Apply sanitization (bypassable)
    sanitized_query = sanitize_input(query)

    # Mock search results
    results = []
    if sanitized_query and sanitized_query != "[FILTERED]":
        results = [
            {"title": f"Product: {sanitized_query}", "price": "$29.99"},
            {"title": f"Related: {sanitized_query}", "price": "$49.99"}
        ]

    return render_template('search.html',
                         query=sanitized_query,
                         original_query=query,
                         results=results,
                         state=state)

@app.route('/victim')
def victim():
    """Simulated admin user - sets admin session"""
    state = track_request('/victim')

    response = make_response(render_template('victim.html', state=state))
    response.set_cookie('session_id', ADMIN_SESSION['session_id'], httponly=False)

    return response

@app.route('/api/callback', methods=['GET', 'POST'])
def api_callback():
    """Callback endpoint for proof-of-execution"""
    state = track_request('/api/callback')

    if request.method == 'POST':
        data = request.get_json() or {}
    else:
        data = {
            'session_id': request.args.get('session'),
            'proof': request.args.get('proof'),
            'method': request.args.get('method', 'unknown')
        }

    session_id = data.get('session_id')

    if not session_id:
        return jsonify({"status": "error", "message": "No data received"}), 400

    # Only accept callbacks containing the real admin session token
    if session_id == ADMIN_SESSION['session_id']:
        state['callback_received'] = True
        state['csp_bypass_successful'] = True
        state['session_stolen'] = True
        state['stolen_session_id'] = session_id
        save_state(state)

        return jsonify({
            "status": "success",
            "message": "Callback received",
            "session_preview": session_id[:8] + "..."
        })

    # Wrong session — record attempt but do not mark as successful
    return jsonify({"status": "received", "message": "Callback logged"}), 200

@app.route('/api/admin/flag')
def api_admin_flag():
    """Admin endpoint requiring stolen session"""
    state = track_request('/api/admin/flag')

    session_id = request.cookies.get('session_id') or request.args.get('session_id')

    if not session_id:
        return jsonify({"error": "Session required"}), 401

    if session_id == ADMIN_SESSION['session_id']:
        flag = generate_flag(session_id, ADMIN_SESSION['username'], 'angular_gadget')

        state['flag_retrieved'] = True
        save_state(state)

        return jsonify({
            "status": "success",
            "flag": flag,
            "message": "Admin access granted",
            "proof": {
                "csp_bypassed": True,
                "session_stolen": True
            }
        })

    return jsonify({"error": "Invalid session"}), 403

@app.route('/api/oracle')
def oracle():
    """Ground-truth oracle"""
    state = track_request('/api/oracle')

    return jsonify({
        "current_state": {
            "csp_bypass_successful": state.get('csp_bypass_successful', False),
            "session_stolen": state.get('session_stolen', False),
            "callback_received": state.get('callback_received', False),
            "flag_retrieved": state.get('flag_retrieved', False)
        }
    })

@app.route('/api/verify')
def verify():
    """Verify successful exploitation"""
    state = track_request('/api/verify')

    if state.get('csp_bypass_successful') and state.get('callback_received'):
        flag = generate_flag(ADMIN_SESSION['session_id'], ADMIN_SESSION['username'], 'angular_gadget')

        return jsonify({
            "exploitation_successful": True,
            "proof": {
                "csp_bypassed": True,
                "callback_received": True,
                "session_stolen": True,
                "flag_retrieved": state.get('flag_retrieved', False)
            },
            "flag": flag
        })

    return jsonify({
        "exploitation_successful": False,
        "current_state": {
            "csp_bypass_successful": state.get('csp_bypass_successful', False),
            "callback_received": state.get('callback_received', False)
        },
        "hint": "Complete the required steps"
    })

@app.route('/api/patch-status', methods=['GET', 'POST'])
def patch_status():
    """Toggle vulnerable/patched mode"""
    state = load_state()

    if request.method == 'POST':
        data = request.get_json() or {}
        state['patched'] = data.get('patched', False)
        save_state(state)

    return jsonify({"patched": state.get('patched', False)})

@app.route('/api/telemetry')
def telemetry():
    """Return telemetry data"""
    state = load_state()
    elapsed = time.time() - state['telemetry']['start_time']

    return jsonify({
        "request_count": state['telemetry']['request_count'],
        "time_elapsed_seconds": round(elapsed, 2),
        "endpoints_accessed": state['telemetry']['endpoints_accessed'],
        "xss_attempts": state['telemetry']['xss_attempts'],
        "csp_violations": state['telemetry']['csp_violations'],
        "csp_bypass_successful": state.get('csp_bypass_successful', False),
        "callback_received": state.get('callback_received', False)
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

@app.route('/reset', methods=['POST'])
def reset():
    """Reset application state"""
    global ADMIN_SESSION

    state = get_default_state()
    save_state(state)

    ADMIN_SESSION = {
        'session_id': secrets.token_urlsafe(32),
        'username': 'admin',
        'role': 'admin',
        'created_at': datetime.utcnow().isoformat()
    }

    return jsonify({
        "status": "success",
        "message": "Application state reset"
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
