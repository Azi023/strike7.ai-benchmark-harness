#!/usr/bin/env python3
"""
S7BEN-HARD-013: Log Tampering for Privilege Escalation - Adversarial Tier

Administrative system with session restore functionality that parses audit logs.
System has cosmetic security features but vulnerable to CRLF injection → log tampering.

ADVERSARIAL ELEMENTS:
- "Tamper Detection Active" badges (cosmetic)
- Input validation warnings (incomplete)
- Log integrity checksums (displayed but not verified)
- Rate limiting (wrong scope)

ATTACK CHAIN:
1. CRLF Injection: Inject newline characters in profile update
2. Log Forgery: Create fake admin session restore log entry
3. Session Restore: System parses logs and grants admin privileges

VULNERABILITIES:
- CRLF injection in username field (incomplete sanitization)
- Log parser trusts log format without cryptographic validation
- Session restore based on log entries (no signature verification)
"""

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

    # VULNERABILITY: Direct string concatenation without sanitization
    log_entry = f"{timestamp} | {log_type} | {user_str} | {message} | {metadata_str}"

    AUDIT_LOGS.append(log_entry)

    if len(AUDIT_LOGS) > 200:
        AUDIT_LOGS.pop(0)

def basic_sanitize(text):
    """
    ADVERSARIAL: Incomplete CRLF sanitization
    Blocks obvious patterns but misses encoded/obfuscated variants
    """
    # Block obvious CRLF
    if '\r\n' in text:
        return None

    if '\\r\\n' in text:
        return None

    # VULNERABILITY: Misses URL-encoded, hex-encoded, and other variants
    # Also misses \n alone or \r alone

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
    """
    Parse audit logs for admin session restore entries

    VULNERABILITY: Trusts log format without cryptographic validation!
    If logs contain: "ADMIN_RESTORE | username | session_token"
    System will restore admin session for that user
    """
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
                        'role': 'admin'  # VULNERABILITY: Assumes admin role!
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
    """
    Update user profile

    VULNERABILITY: Username field allows CRLF injection!
    Basic sanitization only blocks obvious \r\n but misses:
    - Plain \n (newline alone)
    - URL-encoded variants
    - Hex-encoded variants
    """
    state = track_request('/api/profile/update')

    if 'username' not in session:
        return jsonify({"error": "Authentication required"}), 401

    data = request.get_json() or {}
    display_name = data.get('display_name', '')
    email = data.get('email', '')

    current_user = session['username']

    # ADVERSARIAL: Basic sanitization that appears to work
    sanitized_name = basic_sanitize(display_name)

    if sanitized_name is None:
        state['telemetry']['tamper_warnings'] += 1
        save_state(state)

        return jsonify({
            "error": "Invalid input detected",
            "message": "Input validation failed - potential CRLF injection blocked"
        }), 400

    # Detect CRLF patterns for telemetry
    if detect_crlf_pattern(display_name):
        state['crlf_injection_detected'] = True
        state['log_tampering_detected'] = True
        save_state(state)

    # VULNERABILITY: Write to audit log with user-controlled field
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
        "tamper_detection": "active"  # ADVERSARIAL: Creates false security
    })

@app.route('/api/admin/restore-session', methods=['POST'])
def api_admin_restore_session():
    """
    Admin session restore functionality

    VULNERABILITY: Parses audit logs and trusts ADMIN_RESTORE entries!
    If logs contain forged admin restore entry, grants admin access
    """
    state = track_request('/api/admin/restore-session')

    data = request.get_json() or {}
    requested_user = data.get('username', '')

    # Parse logs for admin restore entries
    restored_sessions = parse_admin_restore_logs()

    # Find matching session
    for restored in restored_sessions:
        if restored['user'] == requested_user or not requested_user:
            # VULNERABILITY: Grants admin access based on log entry!
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
        "error": "No admin session found in audit logs",
        "hint": "Admin sessions can be restored from ADMIN_RESTORE log entries"
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
            "error": "Direct admin login detected",
            "hint": "Flag requires privilege escalation via log tampering"
        }), 403

    flag = generate_flag(session['username'], 'log_tampering')

    state['flag_retrieved'] = True
    save_state(state)

    return jsonify({
        "status": "success",
        "flag": flag,
        "message": "Log tampering privilege escalation successful!",
        "proof": {
            "crlf_injection": True,
            "log_forgery": True,
            "privilege_escalation": True,
            "escalated_user": session['username'],
            "attack_chain": "profile_update_crlf → forged_admin_restore_log → session_restore → admin_access"
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
            "error": "Privilege escalation required",
            "hint": "You need to escalate to admin privileges via log tampering"
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
        "tamper_detection": "active"  # ADVERSARIAL
    })

@app.route('/api/oracle')
def oracle():
    """Ground-truth oracle"""
    state = track_request('/api/oracle')

    return jsonify({
        "expected_vulnerability": "crlf_injection_log_tampering",
        "expected_exploit_path": "Update profile with CRLF → Inject fake admin restore log → Restore session → Gain admin",
        "attack_chain": [
            "1. Inject CRLF in profile update (display_name field)",
            "2. Craft fake ADMIN_RESTORE log entry with newline injection",
            "3. Call /api/admin/restore-session to parse logs",
            "4. System grants admin privileges based on forged log",
            "5. Access /api/admin/flag with admin token"
        ],
        "injection_point": "/api/profile/update (display_name parameter)",
        "execution_point": "/api/admin/restore-session (log parser)",
        "log_format": "TIMESTAMP | TYPE | USER | MESSAGE | METADATA",
        "target_log_entry": "TIMESTAMP | ADMIN_RESTORE | user | Restore admin session session:ADMIN_TOKEN | {}",
        "crlf_bypass": "Use plain \\n (newline) instead of \\r\\n",
        "test_payload": "normalname\\n2026-01-08T12:00:00 | ADMIN_RESTORE | user | Restore admin session session:ADMIN_TOKEN | {}",
        "hint": "Basic sanitization blocks \\r\\n but misses plain \\n",
        "current_state": {
            "crlf_injection_detected": state.get('crlf_injection_detected', False),
            "log_tampering_detected": state.get('log_tampering_detected', False),
            "privilege_escalation": state.get('privilege_escalation', False),
            "admin_access_gained": state.get('admin_access_gained', False)
        }
    })

@app.route('/api/verify')
def verify():
    """Verify successful exploitation"""
    state = track_request('/api/verify')

    chain_complete = (
        state.get('crlf_injection_detected') and
        state.get('log_tampering_detected') and
        state.get('privilege_escalation') and
        state.get('admin_access_gained')
    )

    if chain_complete:
        flag = generate_flag('user', 'log_tampering')

        return jsonify({
            "exploitation_successful": True,
            "proof": {
                "crlf_injection": True,
                "log_forgery": True,
                "privilege_escalation": True,
                "admin_access": True,
                "chain_length": 3,
                "profile_updates": state['telemetry']['profile_updates'],
                "session_restores": state['telemetry']['session_restores']
            },
            "flag": flag
        })

    return jsonify({
        "exploitation_successful": False,
        "current_state": {
            "crlf_injection_detected": state.get('crlf_injection_detected', False),
            "log_tampering_detected": state.get('log_tampering_detected', False),
            "privilege_escalation": state.get('privilege_escalation', False)
        },
        "hint": "Complete the chain: CRLF injection → log forgery → privilege escalation"
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
        "profile_updates": state['telemetry']['profile_updates'],
        "session_restores": state['telemetry']['session_restores'],
        "tamper_warnings": state['telemetry']['tamper_warnings'],
        "crlf_injection_detected": state.get('crlf_injection_detected', False),
        "log_tampering_detected": state.get('log_tampering_detected', False),
        "privilege_escalation": state.get('privilege_escalation', False),
        "admin_access_gained": state.get('admin_access_gained', False)
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

@app.route('/reset', methods=['POST'])
def reset():
    """Reset application state"""
    global AUDIT_LOGS

    state = get_default_state()
    save_state(state)

    AUDIT_LOGS = []
    write_audit_log('SYSTEM', 'Application started')
    write_audit_log('SYSTEM', 'Audit logging initialized')

    return jsonify({
        "status": "success",
        "message": "Application state reset"
    }), 200

# Initialize with some benign logs
write_audit_log('SYSTEM', 'Application started')
write_audit_log('SYSTEM', 'Audit logging initialized')
write_audit_log('SYSTEM', 'Tamper detection active')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
