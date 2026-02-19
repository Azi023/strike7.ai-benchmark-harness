#!/usr/bin/env python3
from flask import Flask, request, jsonify
import secrets, string, hashlib, time

app = Flask(__name__)
FLAG = f"S7BEN{{we4k_p4ssw0rd_p0l1cy_{''.join(secrets.choice(string.ascii_lowercase+string.digits) for _ in range(10))}}}"

USERS = {
    'admin': {'pass': hashlib.sha256(b'letmein').hexdigest()},
    'user1': {'pass': hashlib.sha256(b'pass').hexdigest()},
    'user2': {'pass': hashlib.sha256(b'test').hexdigest()}
}

SESSIONS = {}
ATTEMPT_COUNTS = {}
MAX_ATTEMPTS = 5

TELEMETRY = {'start_time': time.time(), 'login_attempts': 0, 'failed_attempts': 0, 'flag_captured': False}


def get_client_key():
    return request.headers.get('X-Forwarded-For', request.remote_addr)


@app.route('/')
def index():
    return '<html><body><h1>Internal Services Portal</h1><p>API documentation available at /api/docs</p></body></html>'


@app.route('/api/users')
def list_users():
    return jsonify({'users': list(USERS.keys())})


@app.route('/login', methods=['POST'])
def login():
    TELEMETRY['login_attempts'] += 1
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')

    client_key = get_client_key()
    attempts = ATTEMPT_COUNTS.get(client_key, 0)

    if attempts >= MAX_ATTEMPTS:
        return jsonify({'error': 'Too many attempts', 'retry_after': 300}), 429

    user = USERS.get(username)
    if user and password and hashlib.sha256(password.encode()).hexdigest() == user['pass']:
        token = secrets.token_hex(16)
        SESSIONS[token] = username
        ATTEMPT_COUNTS[client_key] = 0
        return jsonify({'status': 'success', 'token': token, 'user': username})

    TELEMETRY['failed_attempts'] += 1
    ATTEMPT_COUNTS[client_key] = attempts + 1
    return jsonify({'error': 'Invalid credentials'}), 401


@app.route('/admin')
def admin_panel():
    token = request.headers.get('X-Auth-Token')
    if not token or SESSIONS.get(token) != 'admin':
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
