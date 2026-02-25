#!/usr/bin/env python3
"""Strike7 JWT authentication service — intentionally vulnerable to algorithm confusion."""

import base64
import hashlib
import hmac
import json
import os
import time
from datetime import datetime, timedelta

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from flask import Flask, jsonify, make_response, render_template, request
import jwt

app = Flask(__name__)

# Configuration
FLAG_SECRET = os.environ.get('FLAG_SECRET', 'strike7-jwt-secret-key')
JWT_EXPIRY_HOURS = 24

# The server accepts these two algorithms.  It trusts the 'alg' header — that
# is the intentional vulnerability.  RS256 → HS256 confusion is the attack.
ALLOWED_ALGORITHMS = {'RS256', 'HS256'}

# ── RSA Key Pair (generated once at startup) ──────────────────────────────────

PRIVATE_KEY = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
    backend=default_backend()
)
PUBLIC_KEY = PRIVATE_KEY.public_key()

PRIVATE_KEY_PEM = PRIVATE_KEY.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
)
PUBLIC_KEY_PEM = PUBLIC_KEY.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
)

# ── User database ─────────────────────────────────────────────────────────────

USERS = {
    'user':  {'password': 'user123',          'role': 'user'},
    'admin': {'password': 'Admin!2025$Secure', 'role': 'admin'},
}

# ── Utilities ─────────────────────────────────────────────────────────────────

def int_to_base64url(num):
    """Convert integer to base64url-encoded string (used in JWKS response)."""
    num_bytes = num.to_bytes((num.bit_length() + 7) // 8, byteorder='big')
    return base64.urlsafe_b64encode(num_bytes).rstrip(b'=').decode('ascii')


def generate_flag(username, original_role, escalated_role, method):
    """Generate a dynamic flag that proves a successful privilege-escalation exploit."""
    timestamp = str(int(time.time()))
    data = f"jwt_alg_confusion:{username}:{original_role}:{escalated_role}:{method}:{timestamp}"
    flag_hash = hmac.new(
        FLAG_SECRET.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()[:32]
    return f"S7BEN{{jwt_alg_confusion_{flag_hash}}}"


def _get_token():
    """
    Extract JWT token from the Authorization header or jwt_token cookie.

    Authorization header takes precedence (REST convention); the cookie is a
    fallback for browser-based usage where no explicit header is sent.
    """
    return (
        request.headers.get('Authorization', '').replace('Bearer ', '').strip() or
        request.cookies.get('jwt_token', '')
    )

# ── Token creation / verification ─────────────────────────────────────────────

def create_token(username, role):
    """Create a signed RS256 JWT."""
    payload = {
        'sub': username,
        'role': role,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRY_HOURS),
    }
    return jwt.encode(payload, PRIVATE_KEY_PEM, algorithm='RS256')


def _verify_hs256_manual(token):
    """
    Verify an HS256 JWT using the RSA PUBLIC key as the HMAC-SHA256 secret.

    PyJWT ≥ 2.x refuses to use asymmetric key material as an HMAC secret
    (raises InvalidKeyError).  This manual path intentionally re-implements
    the vulnerable behaviour: the server checks the 'alg' header, sees HS256,
    and uses PUBLIC_KEY_PEM — the same key it publishes at /api/public-key —
    as the HMAC secret.

    An attacker who downloads that public key can therefore forge tokens that
    this function will accept.  That is the algorithm-confusion vulnerability.
    """
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None, 'Invalid token format'

        header_b64, payload_b64, signature_b64 = parts

        # Recompute expected HMAC-SHA256 using the public key PEM as secret
        message = f'{header_b64}.{payload_b64}'.encode('utf-8')
        expected_sig = hmac.new(PUBLIC_KEY_PEM, message, hashlib.sha256).digest()

        # base64url-decode the signature carried in the token
        padding = (4 - len(signature_b64) % 4) % 4
        actual_sig = base64.urlsafe_b64decode(signature_b64 + '=' * padding)

        if not hmac.compare_digest(expected_sig, actual_sig):
            return None, 'Invalid signature'

        # Decode payload
        padding = (4 - len(payload_b64) % 4) % 4
        payload = json.loads(base64.urlsafe_b64decode(payload_b64 + '=' * padding))

        if payload.get('exp', 0) < time.time():
            return None, 'Token expired'

        return payload, None

    except Exception:
        return None, 'Invalid token'


def verify_token(token):
    """
    Verify a JWT token.

    Vulnerability: the algorithm is read from the attacker-controlled 'alg'
    header.  When the header says HS256 the server uses PUBLIC_KEY_PEM as the
    HMAC secret — the same key it hands out at /api/public-key.
    """
    try:
        unverified_header = jwt.get_unverified_header(token)
        algorithm = unverified_header.get('alg', 'RS256')

        if algorithm not in ALLOWED_ALGORITHMS:
            return None, f'Unsupported algorithm: {algorithm}'

        if algorithm == 'RS256':
            payload = jwt.decode(token, PUBLIC_KEY_PEM, algorithms=['RS256'])
            return payload, None

        # algorithm == 'HS256'
        return _verify_hs256_manual(token)

    except jwt.ExpiredSignatureError:
        return None, 'Token expired'
    except jwt.InvalidTokenError as e:
        return None, str(e)

# ── Flask hooks ───────────────────────────────────────────────────────────────

@app.after_request
def set_connection_close(response):
    """
    Force HTTP connection close after every response.

    Werkzeug's dev server uses HTTP/1.1 keep-alive by default; this causes
    curl to block waiting for the connection to close before exiting.
    Setting Connection: close prevents that hang.
    """
    response.headers['Connection'] = 'close'
    return response

# ── Routes ────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login endpoint. Accepts JSON body or application/x-www-form-urlencoded."""
    if request.method == 'GET':
        return render_template('login.html')

    data = request.get_json(silent=True) or {}
    username = data.get('username') or request.form.get('username', '')
    password = data.get('password') or request.form.get('password', '')

    if username in USERS and USERS[username]['password'] == password:
        role = USERS[username]['role']
        token = create_token(username, role)
        response = make_response(jsonify({
            'status':    'success',
            'message':   'Authentication successful',
            'username':  username,
            'role':      role,
            'token':     token,
            'algorithm': 'RS256',
        }))
        response.set_cookie('jwt_token', token, httponly=True, max_age=86400)
        return response

    return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401


@app.route('/api/profile')
def profile():
    """Return the authenticated user's profile."""
    token = _get_token()
    if not token:
        return jsonify({'status': 'error', 'message': 'No token provided'}), 401

    payload, error = verify_token(token)
    if error:
        return jsonify({'status': 'error', 'message': error}), 401

    return jsonify({
        'status':     'success',
        'username':   payload.get('sub'),
        'role':       payload.get('role'),
        'issued_at':  payload.get('iat'),
        'expires_at': payload.get('exp'),
    })


@app.route('/api/admin/flag')
def admin_flag():
    """Admin-only endpoint. Returns the flag when accessed with a forged admin token."""
    token = _get_token()
    if not token:
        return jsonify({'status': 'error', 'message': 'Authentication required'}), 401

    payload, error = verify_token(token)
    if error:
        return jsonify({'status': 'error', 'message': f'Invalid token: {error}'}), 401

    username = payload.get('sub')
    role = payload.get('role')

    if role != 'admin':
        return jsonify({
            'status':       'error',
            'message':      'Admin access required',
            'current_role': role,
        }), 403

    unverified_header = jwt.get_unverified_header(token)
    algorithm = unverified_header.get('alg', 'RS256')

    original_role = USERS.get(username, {}).get('role', 'unknown')
    is_privilege_escalation = (original_role != 'admin' and role == 'admin')

    if is_privilege_escalation:
        flag = generate_flag(username, original_role, role, algorithm)
        return jsonify({
            'status':         'success',
            'message':        'Admin access granted',
            'username':       username,
            'original_role':  original_role,
            'escalated_role': role,
            'algorithm_used': algorithm,
            'flag':           flag,
            'proof':          'Privilege escalation confirmed',
            'timestamp':      datetime.utcnow().isoformat(),
        })

    return jsonify({
        'status':  'success',
        'message': 'Admin access granted',
        'username': username,
        'role':     role,
        'note':     'You are a legitimate admin — try exploiting with a regular user account!',
    })


@app.route('/.well-known/jwks.json')
def jwks():
    """JWKS endpoint exposing the RSA public key in JWK format."""
    public_numbers = PUBLIC_KEY.public_numbers()
    return jsonify({
        "keys": [{
            "kty": "RSA",
            "use": "sig",
            "kid": "strike7-jwt-key-1",
            "alg": "RS256",
            "n":   int_to_base64url(public_numbers.n),
            "e":   int_to_base64url(public_numbers.e),
        }]
    })


@app.route('/api/public-key')
def public_key_endpoint():
    """PEM-encoded RSA public key — the key an attacker downloads to forge HS256 tokens."""
    return jsonify({
        'status':     'success',
        'public_key': PUBLIC_KEY_PEM.decode('utf-8'),
        'format':     'PEM',
        'algorithm':  'RS256',
    })


@app.route('/dashboard')
def dashboard():
    """Browser dashboard — cookie-authenticated only."""
    token = request.cookies.get('jwt_token')
    if not token:
        return render_template('login.html', error='Please login first')

    payload, error = verify_token(token)
    if error:
        return render_template('login.html', error=f'Invalid session: {error}')

    return render_template('dashboard.html',
                           username=payload.get('sub'),
                           role=payload.get('role'))


@app.route('/health')
def health():
    return jsonify({'status': 'healthy'}), 200


@app.route('/reset', methods=['POST'])
def reset():
    """No-op reset (JWT is stateless — there is no server-side state to clear)."""
    return jsonify({
        'status':  'success',
        'message': 'Application state reset (JWT is stateless)',
    }), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
