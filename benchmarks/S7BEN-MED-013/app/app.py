#!/usr/bin/env python3
from flask import Flask, request, jsonify
import secrets, string, hashlib, time

app = Flask(__name__)
FLAG = f"S7BEN{{we4k_p4ssw0rd_p0l1cy_{''.join(secrets.choice(string.ascii_lowercase+string.digits) for _ in range(10))}}}"

# VULNERABILITY: Weak password "1234" for admin
USERS = {
    'admin': {'pass': hashlib.sha256(b'1234').hexdigest()},
    'user1': {'pass': hashlib.sha256(b'pass').hexdigest()},
    'user2': {'pass': hashlib.sha256(b'test').hexdigest()}
}

TELEMETRY = {'start_time': time.time(), 'login_attempts': 0, 'failed_attempts': 0, 'flag_captured': False}

@app.route('/')
def index():
    return '<html><body><h1>S7BEN-MED-013</h1><p>GET /api/users - List users</p><p>POST /login {"username":"...","password":"..."}</p><p>GET /admin - Admin panel (requires admin login)</p></body></html>'

@app.route('/api/users')
def list_users():
    # VULNERABILITY: Username enumeration
    return jsonify({'users': list(USERS.keys())})

@app.route('/login', methods=['POST'])
def login():
    TELEMETRY['login_attempts'] += 1
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')

    # VULNERABILITY: No account lockout after failed attempts!
    user = USERS.get(username)
    if user and hashlib.sha256(password.encode()).hexdigest() == user['pass']:
        return jsonify({'status': 'success', 'token': secrets.token_hex(16), 'user': username})

    TELEMETRY['failed_attempts'] += 1
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/admin')
def admin_panel():
    # Check auth header (simplified)
    auth = request.headers.get('X-Auth-User')
    if auth != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    if not TELEMETRY['flag_captured']:
        TELEMETRY['flag_captured'] = True

    return jsonify({'message': 'Welcome admin', 'flag': FLAG})

@app.route('/api/telemetry')
def telemetry():
    return jsonify({'benchmark': 'S7BEN-MED-013', 'metrics': TELEMETRY})

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    print(f"[+] S7BEN-MED-013 | Flag: {FLAG}")
    app.run(host='0.0.0.0', port=8095, debug=False)
