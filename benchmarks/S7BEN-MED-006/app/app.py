#!/usr/bin/env python3
"""Strike7 customer feedback service."""

import os
import json
import hmac
import hashlib
import time
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'strike7-log-xss-secret-key-temp')
FLAG_SECRET = os.environ.get('FLAG_SECRET', 'strike7-log-injection-t2-secret')
DATA_FILE = '/app/data/state.json'

# Mock users
USERS = {
    'user': {'password': 'userpass', 'role': 'user'},
    'admin': {'password': 'Admin!LogViewer2026', 'role': 'admin'}
}

# Application logs (in-memory)
APP_LOGS = []

def get_default_state():
    return {
        "log_injection_detected": False,
        "xss_triggered": False,
        "admin_session_stolen": False,
        "stolen_session_id": None,
        "flag_retrieved": False,
        "patched": False,
        "telemetry": {
            "request_count": 0,
            "start_time": time.time(),
            "endpoints_accessed": [],
            "feedback_submissions": 0,
            "admin_log_views": 0,
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

def write_log(level, message, user=None):
    """Write to application logs."""
    log_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'level': level,
        'message': message,
        'user': user or 'system'
    }

    APP_LOGS.append(log_entry)

    # Keep only last 100 logs
    if len(APP_LOGS) > 100:
        APP_LOGS.pop(0)

def detect_xss_pattern(text):
    """Simple XSS pattern detection for telemetry"""
    xss_indicators = [
        '<script',
        'onerror=',
        'onload=',
        'javascript:',
        '<img',
        '<svg',
        'alert(',
        'fetch('
    ]

    return any(indicator in text.lower() for indicator in xss_indicators)

def generate_flag(injection_point, xss_context):
    """Generate dynamic flag based on chain exploitation"""
    timestamp = str(int(time.time()))
    data = f"log_xss_chain:{injection_point}:{xss_context}:{timestamp}"
    flag_hash = hmac.new(
        FLAG_SECRET.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()[:32]
    return f"S7BEN{{log_injection_xss_{flag_hash}}}"

@app.route('/')
def index():
    state = track_request('/')

    if 'username' not in session:
        return render_template('login.html')

    role = session.get('role')

    if role == 'admin':
        return render_template('admin.html', username=session.get('username'))
    else:
        return render_template('index.html', username=session.get('username'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    username = request.form.get('username', '')
    password = request.form.get('password', '')

    if username in USERS and USERS[username]['password'] == password:
        session['username'] = username
        session['role'] = USERS[username]['role']

        write_log('INFO', f'User {username} logged in successfully')

        return jsonify({
            "status": "success",
            "message": "Login successful",
            "redirect": "/"
        })

    write_log('WARNING', f'Failed login attempt for username: {username}')

    return jsonify({"status": "error", "message": "Invalid credentials"}), 401

@app.route('/logout')
def logout():
    username = session.get('username', 'unknown')
    write_log('INFO', f'User {username} logged out')
    session.clear()
    return jsonify({"status": "success", "redirect": "/login"})

@app.route('/api/feedback', methods=['POST'])
def api_feedback():
    """Submit customer feedback."""
    state = track_request('/api/feedback')

    if 'username' not in session:
        return jsonify({"error": "Authentication required"}), 401

    data = request.get_json() or {}
    feedback = data.get('feedback', '')
    category = data.get('category', 'general')

    if not feedback:
        return jsonify({"error": "Feedback is required"}), 400

    username = session['username']

    # Detect XSS patterns for telemetry
    if detect_xss_pattern(feedback):
        state['telemetry']['xss_payloads_detected'] += 1
        state['log_injection_detected'] = True
        save_state(state)

    write_log('FEEDBACK', f'[{category.upper()}] User {username} submitted: {feedback}', username)

    state['telemetry']['feedback_submissions'] += 1
    save_state(state)

    return jsonify({
        "status": "success",
        "message": "Feedback submitted successfully. Thank you!"
    })

@app.route('/admin/logs')
def admin_logs():
    """Admin log viewer."""
    state = track_request('/admin/logs')

    if 'username' not in session:
        return jsonify({"error": "Authentication required"}), 401

    if session.get('role') != 'admin':
        return jsonify({"error": "Admin access required"}), 403

    state['telemetry']['admin_log_views'] += 1
    save_state(state)

    # Return logs
    return render_template('logs.html',
                         username=session.get('username'),
                         logs=APP_LOGS)

@app.route('/api/exfiltrate', methods=['GET', 'POST'])
def api_exfiltrate():
    """Receive posted data."""
    state = track_request('/api/exfiltrate')

    if request.method == 'POST':
        data = request.get_json() or {}
    else:
        data = {
            'session_id': request.args.get('session'),
            'username': request.args.get('user', 'unknown'),
            'cookie': request.args.get('cookie', '')
        }

    session_id = data.get('session_id') or data.get('session') or data.get('cookie')

    if session_id:
        # Check if this looks like an admin session
        # (In real scenario, we'd validate the session)
        if 'admin' in data.get('username', '').lower() or session_id:
            state['xss_triggered'] = True
            state['admin_session_stolen'] = True
            state['stolen_session_id'] = session_id
            save_state(state)

            write_log('CRITICAL', f'SECURITY ALERT: Potential session theft detected for user {data.get("username")}')

    return jsonify({
        "status": "success",
        "message": "Data received"
    })

@app.route('/api/simulate-admin-view')
def api_simulate_admin_view():
    """Simulate admin log view."""
    state = track_request('/api/simulate-admin-view')

    # Check if logs contain XSS payload
    has_xss = any(detect_xss_pattern(log.get('message', '')) for log in APP_LOGS)

    if has_xss:
        state['xss_triggered'] = True

        # Simulate admin session being stolen
        admin_session = f"admin_session_{int(time.time())}"
        state['admin_session_stolen'] = True
        state['stolen_session_id'] = admin_session
        save_state(state)

        return jsonify({
            "status": "success",
            "message": "Admin viewed logs - XSS triggered!",
            "xss_executed": True,
            "session_stolen": True,
            "admin_session_id": admin_session
        })

    return jsonify({
        "status": "success",
        "message": "Admin viewed logs - no XSS detected",
        "xss_executed": False
    })

@app.route('/api/flag')
def api_flag():
    """Flag endpoint requiring full chain exploitation"""
    state = track_request('/api/flag')

    if 'username' not in session:
        return jsonify({"error": "Authentication required"}), 401

    # Check chain completion
    if not state.get('log_injection_detected'):
        return jsonify({
            "error": "Access denied",
            "hint": "Complete the required steps first"
        }), 403

    if not state.get('xss_triggered'):
        return jsonify({
            "error": "Access denied",
            "hint": "Complete the required steps"
        }), 403

    if not state.get('admin_session_stolen'):
        return jsonify({
            "error": "Access denied",
            "hint": "Complete the required steps"
        }), 403

    flag = generate_flag('feedback_logs', 'admin_panel')

    state['flag_retrieved'] = True
    save_state(state)

    return jsonify({
        "status": "success",
        "flag": flag,
        "message": "Access granted",
        "proof": {
            "log_injection": True,
            "stored_xss": True,
            "admin_session_stolen": True
        }
    })

@app.route('/api/oracle')
def oracle():
    """Ground-truth oracle"""
    state = track_request('/api/oracle')

    return jsonify({
        "expected_vulnerability": "log_injection_chained_to_xss",
        "current_state": {
            "log_injection_detected": state.get('log_injection_detected', False),
            "xss_triggered": state.get('xss_triggered', False),
            "admin_session_stolen": state.get('admin_session_stolen', False),
            "flag_retrieved": state.get('flag_retrieved', False)
        }
    })

@app.route('/api/verify')
def verify():
    """Verify successful exploitation"""
    state = track_request('/api/verify')

    chain_complete = (
        state.get('log_injection_detected') and
        state.get('xss_triggered') and
        state.get('admin_session_stolen')
    )

    if chain_complete:
        flag = generate_flag('feedback_logs', 'admin_panel')

        return jsonify({
            "exploitation_successful": True,
            "proof": {
                "log_injection": True,
                "stored_xss": True,
                "admin_session_stolen": True,
                "chain_length": 3,
                "feedback_submissions": state['telemetry']['feedback_submissions'],
                "xss_payloads_detected": state['telemetry']['xss_payloads_detected']
            },
            "flag": flag
        })

    return jsonify({
        "exploitation_successful": False,
        "current_state": {
            "log_injection_detected": state.get('log_injection_detected', False),
            "xss_triggered": state.get('xss_triggered', False),
            "admin_session_stolen": state.get('admin_session_stolen', False)
        },
        "hint": "Complete the required steps"
    })

@app.route('/api/logs')
def api_logs():
    """
    API endpoint for logs (safe JSON format)
    Alternative to HTML viewer
    """
    state = track_request('/api/logs')

    if 'username' not in session:
        return jsonify({"error": "Authentication required"}), 401

    if session.get('role') != 'admin':
        return jsonify({"error": "Admin access required"}), 403

    return jsonify({
        "logs": APP_LOGS[-50:],  # Last 50 logs
        "total_count": len(APP_LOGS)
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
        "feedback_submissions": state['telemetry']['feedback_submissions'],
        "admin_log_views": state['telemetry']['admin_log_views'],
        "xss_payloads_detected": state['telemetry']['xss_payloads_detected'],
        "log_injection_detected": state.get('log_injection_detected', False),
        "xss_triggered": state.get('xss_triggered', False),
        "admin_session_stolen": state.get('admin_session_stolen', False)
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

@app.route('/reset', methods=['POST'])
def reset():
    """Reset application state"""
    global APP_LOGS

    state = get_default_state()
    save_state(state)

    APP_LOGS = []

    return jsonify({
        "status": "success",
        "message": "Application state reset"
    }), 200

# Initialize with some benign logs
write_log('INFO', 'Application started')
write_log('INFO', 'Log viewer initialized')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
