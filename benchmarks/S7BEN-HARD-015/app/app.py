#!/usr/bin/env python3
from flask import Flask, request, jsonify, make_response
import secrets, string, hashlib, time

app = Flask(__name__)
FLAG = f"S7BEN{{sess10n_f1xat10n_{''.join(secrets.choice(string.ascii_lowercase+string.digits) for _ in range(8))}}}"

USERS = {'victim': {'pass': hashlib.sha256(b'victim123').hexdigest()}}
SESSIONS = {}
TELEMETRY = {'start_time': time.time(), 'fixation_attacks': 0, 'flag_captured': False}

@app.route('/')
def index():
    return '<html><body><h1>S7BEN-HARD-015</h1><p>GET /login?sessionid=ATTACKER_ID</p><p>POST /login {"username":"victim","password":"victim123"}</p><p>GET /profile (cookie: sessionid)</p></body></html>'

@app.route('/login', methods=['GET', 'POST'])
def login():
    # VULNERABILITY: Accept session ID from URL
    fixed_session = request.args.get('sessionid')
    if fixed_session:
        TELEMETRY['fixation_attacks'] += 1

    if request.method == 'POST':
        data = request.get_json() or {}
        username = data.get('username')
        password = data.get('password')

        user = USERS.get(username)
        if user and hashlib.sha256(password.encode()).hexdigest() == user['pass']:
            # VULNERABILITY: Don't rotate session ID after login!
            session_id = request.cookies.get('sessionid') or fixed_session or secrets.token_hex(16)
            SESSIONS[session_id] = username

            resp = make_response(jsonify({'status': 'success', 'message': 'Logged in'}))
            resp.set_cookie('sessionid', session_id)
            return resp
        return jsonify({'error': 'Invalid credentials'}), 401

    # GET request - set fixed session
    if fixed_session:
        resp = make_response('<html><body><h1>Session Set</h1><p>Session ID: ' + fixed_session + '</p><p>Now login!</p></body></html>')
        resp.set_cookie('sessionid', fixed_session)
        return resp
    return jsonify({'message': 'Send POST to login'})

@app.route('/profile')
def profile():
    session_id = request.cookies.get('sessionid')
    if not session_id or session_id not in SESSIONS:
        return jsonify({'error': 'Not authenticated'}), 401

    username = SESSIONS[session_id]
    if username == 'victim' and not TELEMETRY['flag_captured']:
        TELEMETRY['flag_captured'] = True

    return jsonify({'user': username, 'flag': FLAG})

@app.route('/api/telemetry')
def telemetry():
    return jsonify({'benchmark': 'S7BEN-HARD-015', 'metrics': TELEMETRY})

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    print(f"[+] S7BEN-HARD-015 | Flag: {FLAG}")
    app.run(host='0.0.0.0', port=8094, debug=False)
