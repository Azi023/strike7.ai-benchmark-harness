#!/usr/bin/env python3
"""
S7BEN-MED-009: Content Security Policy (CSP) Bypass via Script Gadgets

VULNERABILITY: Strict CSP blocks inline scripts, but application includes AngularJS
which has exploitable DOM-based script gadgets (ng-app, ng-csp directives).
Attacker bypasses CSP using whitelisted library features.

CWE-79: Cross-site Scripting (XSS)
CWE-1021: Improper Restriction of Rendered UI Layers
OWASP A03:2021 - Injection
"""

from flask import Flask, request, render_template, make_response, jsonify
import hmac
import hashlib
import secrets
import time
import os
from datetime import datetime, timedelta
from html import escape

app = Flask(__name__)

# Configuration
FLAG_SECRET = os.environ.get('FLAG_SECRET', 'strike7-csp-secret-key')

# Admin session (simulated)
ADMIN_SESSION = {
    'session_id': secrets.token_urlsafe(32),
    'username': 'admin',
    'role': 'admin',
    'created_at': datetime.utcnow().isoformat()
}

# Track stolen sessions
STOLEN_SESSIONS = {}

def generate_flag(session_id, victim_username, attack_method):
    """Generate dynamic flag proving CSP bypass and session theft"""
    timestamp = str(int(time.time()))
    data = f"csp_bypass:{session_id}:{victim_username}:{attack_method}:{timestamp}"
    flag_hash = hmac.new(
        FLAG_SECRET.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()[:32]
    return f"S7BEN{{csp_bypass_gadget_{flag_hash}}}"

@app.after_request
def set_csp_header(response):
    """
    Set Content Security Policy header

    VULNERABILITY: CSP is strict and blocks:
    - Inline scripts (no <script>alert(1)</script>)
    - eval() and Function()
    - Inline event handlers (no onclick="...")

    BUT: It allows scripts from 'self' and CDN, including AngularJS!
    AngularJS has DOM-based gadgets that can execute arbitrary expressions.
    """
    csp_policy = (
        "default-src 'self'; "
        "script-src 'self' https://ajax.googleapis.com https://code.angularjs.org; "
        "style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com; "
        "img-src 'self' data:; "
        "connect-src 'self'; "
        "font-src 'self'; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "form-action 'self'; "
    )

    response.headers['Content-Security-Policy'] = csp_policy
    return response

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/search')
def search():
    """
    Search endpoint with reflected XSS

    VULNERABILITY: Search query is reflected in HTML without proper escaping!
    Combined with CSP bypass via AngularJS gadgets, this enables XSS.
    """
    query = request.args.get('q', '')

    # Simulate search results
    results = []
    if query:
        # Some basic filtering (but not enough!)
        # Blocks obvious XSS attempts
        if '<script' in query.lower() or 'javascript:' in query.lower():
            results = [{'title': 'Blocked', 'description': 'Security filter triggered'}]
        else:
            # VULNERABILITY: Query is reflected without escaping!
            results = [
                {'title': f'Search result for: {query}', 'description': 'Sample product 1'},
                {'title': f'Related to: {query}', 'description': 'Sample product 2'}
            ]

    return render_template('search.html', query=query, results=results)

@app.route('/admin/session')
def admin_session():
    """
    Admin endpoint that returns session information

    This simulates an admin user being logged in. The goal is to steal
    this session via CSP bypass XSS.
    """
    # Check if this is the admin
    session_id = request.cookies.get('admin_session')

    if session_id == ADMIN_SESSION['session_id']:
        return jsonify({
            'status': 'success',
            'username': ADMIN_SESSION['username'],
            'role': ADMIN_SESSION['role'],
            'session_id': session_id,
            'note': 'This is a simulated admin session for testing CSP bypass'
        })

    return jsonify({
        'status': 'error',
        'message': 'Admin session required'
    }), 401

@app.route('/exfiltrate', methods=['GET', 'POST'])
def exfiltrate():
    """
    Attacker-controlled endpoint for session exfiltration

    VULNERABILITY: This endpoint receives stolen session data from CSP bypass XSS.
    In a real attack, this would be on attacker's server.
    """
    if request.method == 'POST':
        data = request.get_json() or {}
    else:
        # Support GET for simpler exploitation
        data = {
            'session_id': request.args.get('session'),
            'username': request.args.get('user'),
            'method': request.args.get('method', 'unknown')
        }

    session_id = data.get('session_id')
    username = data.get('username')
    method = data.get('method', 'csp_bypass')

    if session_id and username:
        # Store stolen session
        STOLEN_SESSIONS[session_id] = {
            'username': username,
            'method': method,
            'stolen_at': datetime.utcnow().isoformat()
        }

        return jsonify({
            'status': 'success',
            'message': 'Session data received',
            'stolen_session': session_id[:16] + '...'
        })

    return jsonify({
        'status': 'error',
        'message': 'Invalid data'
    }), 400

@app.route('/api/verify-exploit', methods=['POST'])
def verify_exploit():
    """
    Verify successful CSP bypass exploitation

    Checks if admin session was stolen and returns flag
    """
    data = request.get_json() or {}
    stolen_session_id = data.get('session_id')

    if not stolen_session_id:
        return jsonify({
            'status': 'error',
            'message': 'No session_id provided'
        }), 400

    # Check if this session was stolen
    if stolen_session_id in STOLEN_SESSIONS:
        stolen_data = STOLEN_SESSIONS[stolen_session_id]

        # Verify it's the admin session
        if stolen_session_id == ADMIN_SESSION['session_id']:
            flag = generate_flag(
                stolen_session_id,
                stolen_data['username'],
                stolen_data['method']
            )

            return jsonify({
                'status': 'success',
                'message': 'CSP bypass exploitation confirmed!',
                'victim_username': stolen_data['username'],
                'attack_method': stolen_data['method'],
                'stolen_at': stolen_data['stolen_at'],
                'flag': flag,
                'proof': f"Successfully bypassed CSP using {stolen_data['method']} and stole admin session",
                'timestamp': datetime.utcnow().isoformat()
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Session stolen but not admin session'
            }), 400

    return jsonify({
        'status': 'error',
        'message': 'Session not found in stolen sessions. Did you successfully exfiltrate it?'
    }), 400

@app.route('/victim')
def victim():
    """
    Simulated victim page (admin user)

    This represents an admin user visiting a malicious link.
    In a real attack, the attacker would send this URL to the victim.
    """
    # Set admin session cookie
    response = make_response(render_template('victim.html'))
    response.set_cookie('admin_session', ADMIN_SESSION['session_id'], httponly=False)
    return response

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'}), 200

@app.route('/reset', methods=['POST'])
def reset():
    """Reset application state"""
    global STOLEN_SESSIONS, ADMIN_SESSION

    # Clear stolen sessions
    STOLEN_SESSIONS.clear()

    # Regenerate admin session
    ADMIN_SESSION = {
        'session_id': secrets.token_urlsafe(32),
        'username': 'admin',
        'role': 'admin',
        'created_at': datetime.utcnow().isoformat()
    }

    return jsonify({
        'status': 'success',
        'message': 'Application state reset successfully'
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
