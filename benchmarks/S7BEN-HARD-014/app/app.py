#!/usr/bin/env python3
from flask import Flask, request, jsonify, session
import secrets, string, hashlib, time

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(32)

FLAG_SUFFIX = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(10))
FLAG = f"S7BEN{{p4ssw0rd_res3t_t0ken_reuse_{FLAG_SUFFIX}}}"

USERS = {
    'admin': {
        'password_hash': hashlib.sha256(b'admin123').hexdigest(),
        'email': 'admin@example.com'
    }
}

# VULNERABILITY: Tokens stored but never invalidated
RESET_TOKENS = {}
TELEMETRY = {'start_time': time.time(), 'reset_requests': 0, 'token_reuses': 0, 'flag_captured': False}

@app.route('/')
def index():
    return '''<html><body><h1>Password Reset Demo</h1>
    <p>POST /reset-request {"email":"admin@example.com"}</p>
    <p>POST /reset-password {"token":"...", "new_password":"..."}</p>
    <p>POST /login {"username":"admin", "password":"..."}</p>
    <p>GET /profile (requires auth)</p></body></html>'''

@app.route('/reset-request', methods=['POST'])
def reset_request():
    TELEMETRY['reset_requests'] += 1
    email = request.json.get('email')
    token = secrets.token_hex(16)
    RESET_TOKENS[token] = {'email': email, 'used': False}  # BUG: Never check 'used' flag!
    return jsonify({'status': 'success', 'token': token, 'message': 'Check your email'})

@app.route('/reset-password', methods=['POST'])
def reset_password():
    token = request.json.get('token')
    new_password = request.json.get('new_password')

    if token not in RESET_TOKENS:
        return jsonify({'error': 'Invalid token'}), 400

    # VULNERABILITY: Token not invalidated after use!
    # Should check: if RESET_TOKENS[token]['used']: return error
    # Should set: RESET_TOKENS[token]['used'] = True

    if RESET_TOKENS[token].get('used'):
        TELEMETRY['token_reuses'] += 1

    email = RESET_TOKENS[token]['email']
    for username, user in USERS.items():
        if user['email'] == email:
            user['password_hash'] = hashlib.sha256(new_password.encode()).hexdigest()
            return jsonify({'status': 'success', 'message': 'Password changed'})

    return jsonify({'error': 'User not found'}), 404

@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')
    user = USERS.get(username)

    if user and hashlib.sha256(password.encode()).hexdigest() == user['password_hash']:
        session['user'] = username
        return jsonify({'status': 'success'})
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/profile')
def profile():
    if 'user' not in session:
        return jsonify({'error': 'Authentication required'}), 401

    if session['user'] == 'admin' and not TELEMETRY['flag_captured']:
        TELEMETRY['flag_captured'] = True

    return jsonify({'user': session['user'], 'flag': FLAG if session['user'] == 'admin' else None})

@app.route('/api/telemetry')
def telemetry():
    return jsonify({'benchmark': 'S7BEN-HARD-014', 'metrics': TELEMETRY})

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    print(f"[+] S7BEN-HARD-014 | Flag: {FLAG}")
    app.run(host='0.0.0.0', port=8093, debug=False)
