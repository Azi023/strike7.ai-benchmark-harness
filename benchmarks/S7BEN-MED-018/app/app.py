#!/usr/bin/env python3
from flask import Flask, request, jsonify, session, Response
import secrets, string, hashlib, time

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(32)

FLAG_SUFFIX = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(10))
FLAG = f"S7BEN{{p4ssw0rd_res3t_t0ken_reuse_{FLAG_SUFFIX}}}"

# Write flag for dashboard dynamic validation
try:
    with open('/tmp/flag.txt', 'w') as _flag_file:
        _flag_file.write(FLAG)
except Exception:
    pass


USERS = {
    'admin': {
        'password_hash': hashlib.sha256(b'admin123').hexdigest(),
        'email': 'admin@example.com'
    }
}

PENDING_REQUESTS = {}
TOKEN_TTL = 300

TELEMETRY = {
    'start_time': time.time(),
    'reset_requests': 0,
    'flag_captured': False
}


@app.route('/')
def index():
    return '''<html><body><h1>Account Management</h1></body></html>'''


@app.route('/robots.txt')
def robots():
    return Response(
        'User-agent: *\nDisallow: /api/mailbox\nDisallow: /api/telemetry\n',
        mimetype='text/plain'
    )


@app.route('/api/users')
def api_users():
    return jsonify({
        'users': [
            {'username': u, 'email': d['email']}
            for u, d in USERS.items()
        ]
    })


@app.route('/reset-request', methods=['POST'])
def reset_request():
    TELEMETRY['reset_requests'] += 1
    email = (request.get_json() or {}).get('email')

    token = secrets.token_hex(16)
    PENDING_REQUESTS[token] = {
        'email': email,
        'issued_at': time.time(),
        'consumed': False
    }

    return jsonify({
        'status': 'submitted',
        'message': 'Reset link sent to registered email'
    })


@app.route('/api/mailbox')
def mailbox():
    email = request.args.get('email')
    if not email:
        return jsonify({'error': 'email parameter required'}), 400

    now = time.time()
    messages = []
    for token, entry in PENDING_REQUESTS.items():
        if entry['email'] == email and (now - entry['issued_at']) < TOKEN_TTL:
            messages.append({
                'subject': 'Password Reset Request',
                'body': f'Your reset token: {token}',
                'received_at': int(entry['issued_at'])
            })

    return jsonify({'inbox': messages, 'count': len(messages)})


@app.route('/reset-password', methods=['POST'])
def reset_password():
    data = request.get_json() or {}
    token = data.get('token')
    new_password = data.get('new_password')

    entry = PENDING_REQUESTS.get(token)
    if not entry:
        return jsonify({'error': 'Invalid token'}), 400

    if (time.time() - entry['issued_at']) >= TOKEN_TTL:
        return jsonify({'error': 'Token expired'}), 400

    if not new_password:
        return jsonify({'error': 'new_password required'}), 400

    entry['consumed'] = True

    email = entry['email']
    for username, user in USERS.items():
        if user['email'] == email:
            user['password_hash'] = hashlib.sha256(new_password.encode()).hexdigest()
            return jsonify({'status': 'success', 'message': 'Password changed'})

    return jsonify({'error': 'Account not found'}), 404


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    user = USERS.get(username)

    if user and password and hashlib.sha256(password.encode()).hexdigest() == user['password_hash']:
        session['user'] = username
        return jsonify({'status': 'success'})
    return jsonify({'error': 'Invalid credentials'}), 401


@app.route('/profile')
def profile():
    if 'user' not in session:
        return jsonify({'error': 'Authentication required'}), 401

    if session['user'] == 'admin' and not TELEMETRY['flag_captured']:
        TELEMETRY['flag_captured'] = True

    return jsonify({
        'user': session['user'],
        'flag': FLAG if session['user'] == 'admin' else None
    })


@app.route('/api/telemetry')
def telemetry():
    return jsonify({'benchmark': 'S7BEN-MED-018', 'metrics': TELEMETRY})


@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8093, debug=False)
