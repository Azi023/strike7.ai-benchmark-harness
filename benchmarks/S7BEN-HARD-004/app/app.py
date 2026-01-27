#!/usr/bin/env python3
"""
S7BEN-HARD-004: Auth Bypass with Rate Limiting
JWT Algorithm Confusion vulnerability
"""

from flask import Flask, request, jsonify
import jwt
import time
import os
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

app = Flask(__name__)

# Telemetry
request_counter = 0
login_attempts = 0
rate_limit_hits = 0
jwt_verifications = 0
admin_access_attempts = 0
start_time = time.time()

JWT_SECRET = os.getenv('JWT_SECRET', 'weak_secret_key_12345')
FLAG = os.getenv('FLAG', 'S7BEN{jwt_alg0_c0nfusion_rs256_to_hs256_xyz789}')

# Generate RSA key pair (for RS256)
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
    backend=default_backend()
)
public_key = private_key.public_key()

# Export keys
PRIVATE_KEY_PEM = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
)

PUBLIC_KEY_PEM = public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
)

# Test user database
USERS = {
    'admin': {'password': 'admin123', 'role': 'admin'},
    'user': {'password': 'user123', 'role': 'user'},
    'guest': {'password': 'guest123', 'role': 'guest'}
}

@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

@app.route('/')
def index():
    return jsonify({
        "service": "JWT Authentication Service",
        "endpoints": [
            "/login",
            "/api/token",
            "/api/jwks",
            "/admin/flag",
            "/api/telemetry"
        ],
        "info": "Login to get JWT token"
    })

@app.route('/login', methods=['POST'])
def login():
    """
    Login endpoint - Rate limited by nginx (5 req/min)
    """
    global request_counter, login_attempts
    request_counter += 1
    login_attempts += 1

    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"error": "Missing username or password"}), 400

    username = data['username']
    password = data['password']

    if username not in USERS or USERS[username]['password'] != password:
        return jsonify({"error": "Invalid credentials"}), 401

    # Create JWT token using RS256
    payload = {
        'username': username,
        'role': USERS[username]['role'],
        'exp': int(time.time()) + 3600  # 1 hour expiry
    }

    token = jwt.encode(payload, PRIVATE_KEY_PEM, algorithm='RS256')

    return jsonify({
        "token": token,
        "username": username,
        "role": USERS[username]['role']
    })

@app.route('/api/token', methods=['POST'])
def api_token():
    """
    Alternative token endpoint - NOT rate limited (vulnerability!)
    Same functionality as /login but bypasses nginx rate limiting
    """
    global request_counter, login_attempts
    request_counter += 1
    login_attempts += 1

    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"error": "Missing username or password"}), 400

    username = data['username']
    password = data['password']

    if username not in USERS or USERS[username]['password'] != password:
        return jsonify({"error": "Invalid credentials"}), 401

    # Create JWT token using RS256 (same as /login)
    payload = {
        'username': username,
        'role': USERS[username]['role'],
        'exp': int(time.time()) + 3600
    }

    token = jwt.encode(payload, PRIVATE_KEY_PEM, algorithm='RS256')

    return jsonify({
        "token": token,
        "username": username,
        "role": USERS[username]['role'],
        "note": "This endpoint is not rate limited"
    })

@app.route('/api/jwks')
def jwks():
    """
    JWKS endpoint - Exposes public key
    This is needed for JWT verification but also exposes key for algorithm confusion
    """
    return jsonify({
        "keys": [{
            "kty": "RSA",
            "use": "sig",
            "alg": "RS256",
            "public_key_pem": PUBLIC_KEY_PEM.decode('utf-8')
        }]
    })

def verify_token(token):
    """
    Verify JWT token with ALGORITHM CONFUSION VULNERABILITY
    Accepts both RS256 and HS256 (dangerous!)
    """
    global jwt_verifications
    jwt_verifications += 1

    try:
        # VULNERABLE: Accepts algorithm from token header without validation
        # Should use algorithms=['RS256'] to enforce specific algorithm
        # Instead uses decode_complete to get header
        decoded = jwt.decode(
            token,
            PUBLIC_KEY_PEM,
            algorithms=['RS256', 'HS256']  # VULNERABLE: Accepts both!
        )
        return decoded, None
    except jwt.ExpiredSignatureError:
        return None, "Token expired"
    except jwt.InvalidTokenError as e:
        # Try with secret key if RS256 fails (algorithm confusion)
        try:
            decoded = jwt.decode(
                token,
                JWT_SECRET,
                algorithms=['HS256']
            )
            return decoded, None
        except:
            return None, str(e)

@app.route('/admin/flag')
def admin_flag():
    """
    Admin endpoint - Requires admin role
    """
    global request_counter, admin_access_attempts
    request_counter += 1
    admin_access_attempts += 1

    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "Missing or invalid Authorization header"}), 401

    token = auth_header.split(' ')[1]
    payload, error = verify_token(token)

    if error:
        return jsonify({"error": f"Invalid token: {error}"}), 401

    if payload.get('role') != 'admin':
        return jsonify({
            "error": "Forbidden - Admin access required",
            "your_role": payload.get('role')
        }), 403

    # Admin access granted
    return jsonify({
        "flag": FLAG,
        "message": "Congratulations! You bypassed rate limiting and forged an admin JWT",
        "user": payload.get('username'),
        "role": payload.get('role')
    })

@app.route('/api/telemetry')
def telemetry():
    """Telemetry endpoint for monitoring"""
    return jsonify({
        "benchmark_id": "S7BEN-HARD-004",
        "request_count": request_counter,
        "login_attempts": login_attempts,
        "rate_limit_hits": rate_limit_hits,
        "jwt_verifications": jwt_verifications,
        "admin_access_attempts": admin_access_attempts,
        "uptime_seconds": int(time.time() - start_time)
    })

@app.route('/reset', methods=['POST'])
def reset():
    """Reset telemetry counters"""
    global request_counter, login_attempts, rate_limit_hits, jwt_verifications, admin_access_attempts
    request_counter = 0
    login_attempts = 0
    rate_limit_hits = 0
    jwt_verifications = 0
    admin_access_attempts = 0
    return jsonify({"status": "reset_complete"})

@app.route('/debug/config')
def debug_config():
    """Debug endpoint showing vulnerabilities"""
    return jsonify({
        "jwt_algorithm": "RS256 (but also accepts HS256)",
        "public_key_exposed": "/api/jwks",
        "rate_limiting": {
            "/login": "5 requests/minute",
            "/api/token": "NO LIMIT (vulnerability)"
        },
        "vulnerabilities": [
            "Algorithm confusion - accepts both RS256 and HS256",
            "Public key can be used as HS256 secret",
            "/api/token endpoint not rate limited",
            "JWT secret is weak"
        ]
    })

if __name__ == '__main__':
    # Save public key to file for reference
    os.makedirs('keys', exist_ok=True)
    with open('keys/public_key.pem', 'wb') as f:
        f.write(PUBLIC_KEY_PEM)

    app.run(host='0.0.0.0', port=5000, debug=True)
