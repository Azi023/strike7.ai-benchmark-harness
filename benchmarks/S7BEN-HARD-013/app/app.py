#!/usr/bin/env python3
"""Strike7 administrative service."""

import os
import json
import hmac
import hashlib
import time
import re
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'strike7-log-tamper-secret-key-temp')
FLAG_SECRET = os.environ.get('FLAG_SECRET', 'strike7-log-tampering-t3-secret')
DATA_FILE = '/app/data/state.json'

# Mock users
USERS = {
    'user': {'password': 'userpass', 'role': 'user', 'email': 'user@example.com'},
    'admin': {'password': 'Admin!LogTamper2026', 'role': 'admin', 'email': 'admin@example.com'}
}

# Audit logs (in-memory)
AUDIT_LOGS = []

def get_default_state():
    return {
        "crlf_injection_detected": False,
        "log_tampering_detected": False,
        "privilege_escalation": False,
        "admin_access_gained": False,
        "flag_retrieved": False,
        "patched": False,
        "telemetry": {
            "request_count": 0,
            "start_time": time.time(),
            "endpoints_accessed": [],
            "profile_updates": 0,
            "session_restores": 0,
            "tamper_warnings": 0
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

def write_audit_log(log_type, message, user=None, metadata=None):
    """
    Write to audit logs

    Format: TIMESTAMP | TYPE | USER | MESSAGE | METADATA
    """
    timestamp = datetime.utcnow().isoformat()
    user_str = user or 'system'
    metadata_str = json.dumps(metadata) if metadata else '{}'

    log_entry = f"{timestamp} | {log_type} | {user_str} | {message} | {metadata_str}"

    AUDIT_LOGS.append(log_entry)

    if len(AUDIT_LOGS) > 200:
        AUDIT_LOGS.pop(0)

def basic_sanitize(text):
    """Sanitize input."""
    # Block obvious CRLF
    if '\r\n' in text:
        return None

    if '\\r\\n' in text:
        return None

    return text

def detect_crlf_pattern(text):
    """Detect CRLF injection attempts for telemetry"""
    patterns = [
        r'\\r\\n',
        r'\\n',
        r'%0d%0a',
        r'%0a',
        r'%0D%0A',
        '\r\n',
        '\n',
        '\r'
    ]

    for pattern in patterns:
        if pattern in text.lower() or pattern in text:
            return True

    return False

def parse_admin_restore_logs():
    """Parse audit logs for admin session restore entries."""
    restored_sessions = []

    for log_line in AUDIT_LOGS:
        # Look for ADMIN_RESTORE entries
        if '| ADMIN_RESTORE |' in log_line:
            # Parse log format
            parts = log_line.split(' | ')
            if len(parts) >= 5:
                # parts: [timestamp, type, user, message, metadata]
                user = parts[2]
                message = parts[3]

                # Extract session token from message
                if 'session:' in message:
                    session_token = message.split('session:')[-1].strip()
                    restored_sessions.append({
                        'user': user,
                        'session_token': session_token,
                        'role': 'admin'
                    })

    return restored_sessions

def generate_flag(username, escalation_method):
    """Generate dynamic flag based on privilege escalation"""
    timestamp = str(int(time.time()))
    data = f"log_tamper:{username}:{escalation_method}:{timestamp}"
    flag_hash = hmac.new(
        FLAG_SECRET.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()[:32]
    return f"S7BEN{{log_tampering_privesc_{flag_hash}}}"

@app.route('/')
def index():
    state = track_request('/')

    if 'username' not in session:
        return render_template('login.html')

    role = session.get('role', 'user')

    if role == 'admin':
        return render_template('admin.html',
                             username=session.get('username'),
                             role=role)
    else:
        return render_template('index.html',
                             username=session.get('username'),
                             email=USERS.get(session.get('username'), {}).get('email', ''),
                             role=role)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    username = request.form.get('username', '')
    password = request.form.get('password', '')

    if username in USERS and USERS[username]['password'] == password:
        session['username'] = username
        session['role'] = USERS[username]['role']

        write_audit_log('LOGIN', f'User {username} logged in successfully', username)

        return jsonify({
            "status": "success",
            "message": "Login successful",
            "redirect": "/"
        })

    write_audit_log('LOGIN_FAILED', f'Failed login attempt for username: {username}')

    return jsonify({"status": "error", "message": "Invalid credentials"}), 401

@app.route('/logout')
def logout():
    username = session.get('username', 'unknown')
    write_audit_log('LOGOUT', f'User logged out', username)
    session.clear()
    return jsonify({"status": "success", "redirect": "/login"})

@app.route('/api/profile/update', methods=['POST'])
def api_profile_update():
    """Update user profile."""
    state = track_request('/api/profile/update')

    if 'username' not in session:
        return jsonify({"error": "Authentication required"}), 401

    data = request.get_json() or {}
    display_name = data.get('display_name', '')
    email = data.get('email', '')

    current_user = session['username']

    sanitized_name = basic_sanitize(display_name)

    if sanitized_name is None:
        state['telemetry']['tamper_warnings'] += 1
        save_state(state)

        return jsonify({
            "error": "Invalid input",
            "message": "Input validation failed"
        }), 400

    # Detect CRLF patterns for telemetry
    if detect_crlf_pattern(display_name):
        state['crlf_injection_detected'] = True
        state['log_tampering_detected'] = True
        save_state(state)

    write_audit_log(
        'PROFILE_UPDATE',
        f'User updated profile: display_name={display_name}, email={email}',
        current_user
    )

    state['telemetry']['profile_updates'] += 1
    save_state(state)

    return jsonify({
        "status": "success",
        "message": "Profile updated successfully",
        "tamper_detection": "active"
    })

@app.route('/api/admin/restore-session', methods=['POST'])
def api_admin_restore_session():
    """Admin session restore functionality."""
    state = track_request('/api/admin/restore-session')

    if 'username' not in session:
        return jsonify({"error": "Authentication required"}), 401

    data = request.get_json() or {}
    requested_user = data.get('username', '')

    if not requested_user:
        return jsonify({"error": "Username required"}), 400

    # Parse logs for admin restore entries
    restored_sessions = parse_admin_restore_logs()

    # Find matching session
    for restored in restored_sessions:
        if restored['user'] == requested_user:
            session['username'] = restored['user']
            session['role'] = 'admin'
            session['restored'] = True

            state['privilege_escalation'] = True
            state['admin_access_gained'] = True
            state['telemetry']['session_restores'] += 1
            save_state(state)

            write_audit_log('SESSION_RESTORED', f'Admin session restored for user {restored["user"]}', 'system')

            return jsonify({
                "status": "success",
                "message": f"Admin session restored for {restored['user']}",
                "session_token": restored['session_token'],
                "role": "admin"
            })

    return jsonify({
        "error": "No admin session found in audit logs"
    }), 404

@app.route('/api/admin/flag')
def api_admin_flag():
    """Admin-only flag endpoint"""
    state = track_request('/api/admin/flag')

    if 'username' not in session:
        return jsonify({"error": "Authentication required"}), 401

    if session.get('role') != 'admin':
        return jsonify({"error": "Admin access required"}), 403

    if not state.get('privilege_escalation'):
        return jsonify({
            "error": "Access denied"
        }), 403

    flag = generate_flag(session['username'], 'log_tampering')

    state['flag_retrieved'] = True
    save_state(state)

    return jsonify({
        "status": "success",
        "flag": flag,
        "message": "Admin access granted",
        "proof": {
            "crlf_injection": True,
            "log_forgery": True,
            "privilege_escalation": True,
            "escalated_user": session['username']
        }
    })

@app.route('/api/flag')
def api_flag():
    """General flag endpoint (redirects to admin)"""
    state = track_request('/api/flag')

    if 'username' not in session:
        return jsonify({"error": "Authentication required"}), 401

    if not state.get('privilege_escalation'):
        return jsonify({
            "error": "Privilege escalation required"
        }), 403

    # Redirect to admin flag
    return api_admin_flag()

@app.route('/api/logs')
def api_logs():
    """View audit logs (admin only)"""
    state = track_request('/api/logs')

    if 'username' not in session:
        return jsonify({"error": "Authentication required"}), 401

    if session.get('role') != 'admin':
        return jsonify({"error": "Admin access required"}), 403

    return jsonify({
        "logs": AUDIT_LOGS[-50:],  # Last 50 entries
        "total_count": len(AUDIT_LOGS),
        "tamper_detection": "active"
    })


@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200


# Initialize with some benign logs
write_audit_log('SYSTEM', 'Application started')
write_audit_log('SYSTEM', 'Audit logging initialized')
write_audit_log('SYSTEM', 'Tamper detection active')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
