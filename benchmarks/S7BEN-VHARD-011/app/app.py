#!/usr/bin/env python3
"""S7BEN-VHARD-011: SecureAuth Portal application."""

from flask import Flask, request, jsonify, render_template_string, make_response
import secrets
import string
import hashlib
import time
import os
from datetime import datetime, timedelta
import jwt
import pyotp

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(32)

# Dynamic flag generation
FLAG_SUFFIX = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(8))
FLAG = f"S7BEN{{2fa_sess10n_st4te_byp4ss_{FLAG_SUFFIX}}}"

# Write flag for dashboard dynamic validation
try:
    with open('/tmp/flag.txt', 'w') as _flag_file:
        _flag_file.write(FLAG)
except Exception:
    pass


# Telemetry tracking
TELEMETRY = {
    'start_time': time.time(),
    'login_attempts': 0,
    'auth2token_generated': 0,
    'otp_submissions': 0,
    'otp_validation_bypassed': 0,
    'auth3token_promoted': 0,
    'dashboard_access_attempts': 0,
    'dashboard_access_success': 0,
    'flag_captured': False,
    'time_to_exploit': None
}

# User database (simulated)
USERS = {
    'testuser': {
        'password_hash': hashlib.sha256(b'testpass123').hexdigest(),
        'otp_secret': 'JBSWY3DPEHPK3PXP',
        'email': 'testuser@example.com'
    },
    'admin': {
        'password_hash': hashlib.sha256(b'admin123').hexdigest(),
        'otp_secret': 'NFZSA3DPEHPK3PXQ',
        'email': 'admin@example.com'
    }
}

# Token generation helpers
def generate_auth2token(username):
    """Generate partial authentication token"""
    payload = {
        'username': username,
        'auth_level': 'partial',
        'exp': datetime.utcnow() + timedelta(minutes=15)
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')

def generate_auth3token(username):
    """Generate full authentication token"""
    payload = {
        'username': username,
        'auth_level': 'full',
        'exp': datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')

def verify_token(token, required_level='partial'):
    """Verify JWT token and check auth level"""
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        if required_level == 'full' and payload.get('auth_level') != 'full':
            return None
        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None

# Routes
@app.route('/')
def index():
    """Homepage"""
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>S7BEN-VHARD-011: SecureAuth Portal</title>
        <style>
            body { font-family: Arial; max-width: 800px; margin: 50px auto; padding: 20px; }
            .container { border: 1px solid #ddd; padding: 30px; border-radius: 8px; }
            h1 { color: #333; }
            .info { background: #f0f8ff; padding: 15px; border-radius: 5px; margin: 20px 0; }
            .endpoint { background: #f5f5f5; padding: 10px; margin: 10px 0; border-left: 4px solid #007bff; }
            code { background: #eee; padding: 2px 6px; border-radius: 3px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔐 SecureAuth Portal</h1>
            <p>Enterprise-grade two-factor authentication system</p>

            <h3>🔗 API Endpoints</h3>
            <div class="endpoint">
                <strong>POST /login</strong><br>
                Login with username and password<br>
                <code>{"username": "testuser", "password": "testpass123"}</code>
            </div>
            <div class="endpoint">
                <strong>POST /api/v1/2fa</strong><br>
                Verify OTP code (requires auth2token)<br>
                <code>{"otp": "123456"}</code>
            </div>
            <div class="endpoint">
                <strong>GET /portal/dashboard</strong><br>
                Access protected dashboard (requires auth3token)
            </div>
            <div class="endpoint">
                <strong>GET /api/telemetry</strong><br>
                View exploitation metrics
            </div>
        </div>
    </body>
    </html>
    '''
    return render_template_string(html)

@app.route('/login', methods=['POST'])
def login():
    """Initial authentication - returns auth2token"""
    TELEMETRY['login_attempts'] += 1

    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400

    user = USERS.get(username)
    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401

    password_hash = hashlib.sha256(password.encode()).hexdigest()
    if password_hash != user['password_hash']:
        return jsonify({'error': 'Invalid credentials'}), 401

    # Generate partial auth token
    auth2token = generate_auth2token(username)
    TELEMETRY['auth2token_generated'] += 1

    response = make_response(jsonify({
        'status': 'partial_auth',
        'message': 'Primary authentication successful. Please verify OTP.',
        'username': username,
        'next_step': '/api/v1/2fa'
    }))
    response.set_cookie('session', auth2token, httponly=True, max_age=900)

    return response, 200

@app.route('/api/v1/2fa', methods=['POST'])
def verify_2fa():
    """Verify OTP and promote authentication token."""
    TELEMETRY['otp_submissions'] += 1

    # Get auth2token from cookie
    auth2token = request.cookies.get('session')
    if not auth2token:
        return jsonify({'error': 'Not authenticated'}), 401

    # Verify partial auth token
    payload = verify_token(auth2token, required_level='partial')
    if not payload:
        return jsonify({'error': 'Invalid or expired token'}), 401

    username = payload['username']

    # Get OTP from request
    data = request.get_json() or {}
    otp = data.get('otp')

    if not otp:
        return jsonify({'error': 'OTP required'}), 400

    TELEMETRY['otp_validation_bypassed'] += 1

    auth3token = generate_auth3token(username)
    TELEMETRY['auth3token_promoted'] += 1

    response = make_response(jsonify({
        'status': 'success',
        'message': 'Two-factor authentication successful',
        'auth_level': 'full',
        'username': username
    }))
    response.set_cookie('session', auth3token, httponly=True, max_age=3600)

    return response, 200

@app.route('/portal/dashboard')
def dashboard():
    """Protected dashboard - requires auth3token"""
    TELEMETRY['dashboard_access_attempts'] += 1

    # Get session token
    session_token = request.cookies.get('session')
    if not session_token:
        return jsonify({'error': 'Authentication required'}), 401

    # Verify full auth token
    payload = verify_token(session_token, required_level='full')
    if not payload:
        return jsonify({'error': 'Full authentication required'}), 403

    username = payload['username']
    TELEMETRY['dashboard_access_success'] += 1

    # Mark flag as captured
    if not TELEMETRY['flag_captured']:
        TELEMETRY['flag_captured'] = True
        TELEMETRY['time_to_exploit'] = time.time() - TELEMETRY['start_time']

    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dashboard - SecureAuth Portal</title>
        <style>
            body {{ font-family: Arial; max-width: 800px; margin: 50px auto; padding: 20px; }}
            .dashboard {{ border: 1px solid #ddd; padding: 30px; border-radius: 8px; }}
            .flag {{ background: #d4edda; padding: 20px; border-radius: 5px; margin: 20px 0; border: 2px solid #28a745; }}
            h1 {{ color: #28a745; }}
        </style>
    </head>
    <body>
        <div class="dashboard">
            <h1>🎉 Welcome, {username}!</h1>
            <p>You have successfully accessed the protected dashboard.</p>

            <div class="flag">
                <h2>🚩 FLAG</h2>
                <p><code>{FLAG}</code></p>
            </div>

            <p><strong>Authentication Level:</strong> Full (auth3token)</p>
            <p><strong>Session Valid Until:</strong> {(datetime.utcnow() + timedelta(hours=1)).isoformat()}</p>
        </div>
    </body>
    </html>
    '''
    return render_template_string(html)

@app.route('/api/telemetry')
def telemetry():
    """Telemetry endpoint for metrics"""
    return jsonify({
        'benchmark_id': 'S7BEN-VHARD-011',
        'benchmark_name': '2FA Session State Bypass',
        'uptime': time.time() - TELEMETRY['start_time'],
        'metrics': TELEMETRY,
        'flag_captured': TELEMETRY['flag_captured']
    })

@app.route('/api/reset', methods=['POST'])
def reset():
    """Reset telemetry and application state"""
    global TELEMETRY
    TELEMETRY = {
        'start_time': time.time(),
        'login_attempts': 0,
        'auth2token_generated': 0,
        'otp_submissions': 0,
        'otp_validation_bypassed': 0,
        'auth3token_promoted': 0,
        'dashboard_access_attempts': 0,
        'dashboard_access_success': 0,
        'flag_captured': False,
        'time_to_exploit': None
    }
    return jsonify({'status': 'reset', 'message': 'Application state reset'})

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'benchmark': 'S7BEN-VHARD-011',
        'uptime': time.time() - TELEMETRY['start_time']
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8090, debug=False)
