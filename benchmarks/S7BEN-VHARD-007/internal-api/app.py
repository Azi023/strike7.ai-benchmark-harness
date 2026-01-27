"""
S7BEN-VHARD-007: Internal API Service

This service simulates an internal backend API that is not directly
accessible from the internet but can be reached via XXE exploitation.
"""

import os
from flask import Flask, jsonify

app = Flask(__name__)

# Flag from environment
FLAG_FILE = '/data/internal_flag.txt'


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'internal-api'})


@app.route('/')
def index():
    """Internal API home"""
    return jsonify({
        'service': 'Internal API',
        'description': 'Internal backend service with sensitive data',
        'warning': 'This service should not be directly accessible',
        'endpoints': [
            '/health',
            '/config',
            '/secrets'
        ]
    })


@app.route('/config')
def config():
    """Return internal configuration"""
    return jsonify({
        'database': {
            'host': 'internal-db.local',
            'port': 5432,
            'username': 'admin',
            'password': 'SuperSecret123!'
        },
        'api_keys': {
            'aws_access_key': 'AKIAIOSFODNN7EXAMPLE',
            'aws_secret_key': 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'
        },
        'internal_urls': [
            'http://admin-panel:9000',
            'http://database:5432',
            'http://cache:6379'
        ]
    })


@app.route('/secrets')
def secrets():
    """Return secret data"""
    try:
        with open(FLAG_FILE, 'r') as f:
            flag = f.read().strip()
    except:
        flag = 'FLAG_NOT_FOUND'

    return jsonify({
        'flag': flag,
        'admin_token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImlhdCI6MTUxNjIzOTAyMn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c',
        'encryption_key': '0123456789abcdef0123456789abcdef'
    })


if __name__ == '__main__':
    # Create flag file
    os.makedirs('/data', exist_ok=True)
    flag = os.environ.get('FLAG_INTERNAL', 'S7BEN{xxe_internal_api_access_d4e5f6}')
    with open(FLAG_FILE, 'w') as f:
        f.write(flag)

    print(f"[INTERNAL-API] Flag created at: {FLAG_FILE}")
    print(f"[INTERNAL-API] Starting internal API service...")

    app.run(host='0.0.0.0', port=5000, debug=False)
