#!/usr/bin/env python3
"""Strike7 JWT authentication service."""

from flask import Flask, request, jsonify, render_template, make_response
import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
import hmac
import hashlib
import time
import os
import json
from datetime import datetime, timedelta

app = Flask(__name__)

# Configuration
FLAG_SECRET = os.environ.get('FLAG_SECRET', 'strike7-jwt-secret-key')
JWT_EXPIRY_HOURS = 24

# RSA Key Pair Generation
PRIVATE_KEY = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
    backend=default_backend()
)

PUBLIC_KEY = PRIVATE_KEY.public_key()

# Serialize keys
PRIVATE_KEY_PEM = PRIVATE_KEY.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
)

PUBLIC_KEY_PEM = PUBLIC_KEY.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
)

# Test users
USERS = {
    'user': {'password': 'user123', 'role': 'user'},
    'admin': {'password': 'Admin!2025$Secure', 'role': 'admin'}
}

def generate_flag(username, original_role, escalated_role, method):
    """Generate dynamic flag proving JWT algorithm confusion exploit"""
    timestamp = str(int(time.time()))
    data = f"jwt_alg_confusion:{username}:{original_role}:{escalated_role}:{method}:{timestamp}"
    flag_hash = hmac.new(
        FLAG_SECRET.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()[:32]
    return f"S7BEN{{jwt_alg_confusion_{flag_hash}}}"

def create_token(username, role, algorithm='RS256'):
    """Create JWT token."""
    payload = {
        'sub': username,
        'role': role,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRY_HOURS)
    }

    if algorithm == 'RS256':
        token = jwt.encode(payload, PRIVATE_KEY_PEM, algorithm='RS256')
    elif algorithm == 'HS256':
        token = jwt.encode(payload, PUBLIC_KEY_PEM, algorithm='HS256')
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")

    return token

def verify_token(token):
    """Verify JWT token."""
    try:
        # Decode header to check algorithm
        unverified_header = jwt.get_unverified_header(token)
        algorithm = unverified_header.get('alg', 'RS256')

        if algorithm == 'RS256':
            payload = jwt.decode(token, PUBLIC_KEY_PEM, algorithms=['RS256'])
        elif algorithm == 'HS256':
            payload = jwt.decode(token, PUBLIC_KEY_PEM, algorithms=['HS256'])
        elif algorithm == 'none':
            payload = jwt.decode(token, options={"verify_signature": False}, algorithms=['none'])
        else:
            return None, f"Unsupported algorithm: {algorithm}"

        return payload, None
    except jwt.ExpiredSignatureError:
        return None, "Token expired"
    except jwt.InvalidTokenError as e:
        return None, str(e)

@app.route('/')
def index():
    """Home page with JWT authentication demo"""
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login endpoint - returns JWT token"""
    if request.method == 'GET':
        return render_template('login.html')

    username = request.form.get('username', '')
    password = request.form.get('password', '')

    if username in USERS and USERS[username]['password'] == password:
        role = USERS[username]['role']
        token = create_token(username, role, algorithm='RS256')

        response = make_response(jsonify({
            'status': 'success',
            'message': 'Authentication successful',
            'username': username,
            'role': role,
            'token': token,
            'algorithm': 'RS256'
        }))

        # Set cookie for browser-based access
        response.set_cookie('jwt_token', token, httponly=True, max_age=86400)

        return response

    return jsonify({
        'status': 'error',
        'message': 'Invalid credentials'
    }), 401

@app.route('/api/profile')
def profile():
    """Get user profile from JWT token"""
    token = request.cookies.get('jwt_token') or request.headers.get('Authorization', '').replace('Bearer ', '')

    if not token:
        return jsonify({'status': 'error', 'message': 'No token provided'}), 401

    payload, error = verify_token(token)

    if error:
        return jsonify({'status': 'error', 'message': error}), 401

    return jsonify({
        'status': 'success',
        'username': payload.get('sub'),
        'role': payload.get('role'),
        'issued_at': payload.get('iat'),
        'expires_at': payload.get('exp')
    })

@app.route('/api/admin/flag')
def admin_flag():
    """Admin-only flag endpoint."""
    token = request.cookies.get('jwt_token') or request.headers.get('Authorization', '').replace('Bearer ', '')

    if not token:
        return jsonify({
            'status': 'error',
            'message': 'Authentication required'
        }), 401

    payload, error = verify_token(token)

    if error:
        return jsonify({
            'status': 'error',
            'message': f'Invalid token: {error}'
        }), 401

    username = payload.get('sub')
    role = payload.get('role')

    # Check if admin role
    if role != 'admin':
        return jsonify({
            'status': 'error',
            'message': 'Admin access required',
            'current_role': role
        }), 403

    # Detect if this is a forged token (algorithm confusion)
    unverified_header = jwt.get_unverified_header(token)
    algorithm = unverified_header.get('alg', 'RS256')

    # Check if user was supposed to be admin
    original_role = USERS.get(username, {}).get('role', 'unknown')
    is_privilege_escalation = (original_role != 'admin' and role == 'admin')

    if is_privilege_escalation:
        # Generate flag for successful exploit
        flag = generate_flag(username, original_role, role, algorithm)

        return jsonify({
            'status': 'success',
            'message': 'Admin access granted',
            'username': username,
            'original_role': original_role,
            'escalated_role': role,
            'algorithm_used': algorithm,
            'flag': flag,
            'proof': 'Privilege escalation confirmed',
            'timestamp': datetime.utcnow().isoformat()
        })
    else:
        # Legitimate admin access
        return jsonify({
            'status': 'success',
            'message': 'Admin access granted',
            'username': username,
            'role': role,
            'note': 'You are a legitimate admin - try exploiting with a regular user account!'
        })

@app.route('/.well-known/jwks.json')
def jwks():
    """JWKS endpoint."""
    # Export public key components
    public_numbers = PUBLIC_KEY.public_numbers()

    # Convert to base64url format (JWT standard)
    import base64

    def int_to_base64url(num):
        """Convert integer to base64url encoded bytes"""
        num_bytes = num.to_bytes((num.bit_length() + 7) // 8, byteorder='big')
        return base64.urlsafe_b64encode(num_bytes).rstrip(b'=').decode('ascii')

    jwk = {
        "keys": [
            {
                "kty": "RSA",
                "use": "sig",
                "kid": "strike7-jwt-key-1",
                "alg": "RS256",
                "n": int_to_base64url(public_numbers.n),
                "e": int_to_base64url(public_numbers.e)
            }
        ]
    }

    return jsonify(jwk)

@app.route('/api/public-key')
def public_key():
    """Public key endpoint."""
    return jsonify({
        'status': 'success',
        'public_key': PUBLIC_KEY_PEM.decode('utf-8'),
        'format': 'PEM',
        'algorithm': 'RS256'
    })

@app.route('/dashboard')
def dashboard():
    """Dashboard page - requires authentication"""
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
    """Health check endpoint"""
    return jsonify({'status': 'healthy'}), 200

@app.route('/reset', methods=['POST'])
def reset():
    """Reset application state"""
    # JWT vulnerabilities are stateless, nothing to reset
    # But we provide this endpoint for consistency
    return jsonify({
        'status': 'success',
        'message': 'Application state reset (JWT is stateless)'
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
