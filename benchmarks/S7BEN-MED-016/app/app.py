#!/usr/bin/env python3
import base64
from flask import Flask, request, jsonify, Response
import secrets

app = Flask(__name__)

FLAG = f"S7BEN{{def4ult_creds_{secrets.token_hex(5)}}}"

_CREDS = {'admin': 'str1ke7_adm1n'}
_SESSIONS = {}

_BACKUP_CONTENT = base64.b64encode(
    b"# Site configuration backup\n"
    b"# Generated: 2025-11-14\n"
    b"[auth]\n"
    b"username=admin\n"
    b"password=str1ke7_adm1n\n"
    b"[database]\n"
    b"host=db.internal\n"
    b"port=5432\n"
).decode()


@app.route('/')
def index():
    return '<html><body><h1>Strike7 Portal</h1><p>Welcome.</p></body></html>'


@app.route('/robots.txt')
def robots():
    return Response(
        'User-agent: *\nDisallow: /backup/\nDisallow: /admin/\n',
        mimetype='text/plain'
    )


@app.route('/backup/config.bak')
def backup_config():
    return Response(_BACKUP_CONTENT, mimetype='text/plain')


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    u = data.get('user') or data.get('username')
    p = data.get('pass') or data.get('password')

    if _CREDS.get(u) == p:
        token = secrets.token_hex(20)
        _SESSIONS[token] = u
        return jsonify({'status': 'ok', 'token': token})
    return jsonify({'error': 'nope'}), 401


@app.route('/admin/dashboard')
def dashboard():
    token = request.headers.get('X-Session-Token')
    if not token or _SESSIONS.get(token) != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify({'flag': FLAG})


@app.route('/health')
def health():
    return 'ok'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8104)
