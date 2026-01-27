#!/usr/bin/env python3
"""
Internal Metadata Service

Simulates cloud provider metadata endpoints (AWS EC2, GCP, Azure).
This service should ONLY be accessible from internal network.
"""

from flask import Flask, jsonify, request
import hmac
import hashlib
import os

app = Flask(__name__)

FLAG_SECRET = os.environ.get('FLAG_SECRET', 'strike7-ssrf-secret-key')

def generate_admin_token():
    """Generate consistent admin token"""
    data = "metadata_admin_token"
    token = hmac.new(
        FLAG_SECRET.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()
    return f"admin_{token[:32]}"

@app.route('/')
def index():
    """Metadata service root"""
    return jsonify({
        'service': 'Internal Metadata Service',
        'version': '1.0',
        'endpoints': [
            '/latest/meta-data/',
            '/latest/meta-data/instance-id',
            '/latest/meta-data/hostname',
            '/latest/meta-data/admin-token'
        ],
        'warning': 'This service should only be accessible from internal network!'
    })

@app.route('/latest/meta-data/')
def metadata_root():
    """Metadata root directory"""
    return '''instance-id
hostname
local-ipv4
public-ipv4
admin-token
iam/security-credentials/
'''

@app.route('/latest/meta-data/instance-id')
def instance_id():
    """Instance ID"""
    return 'i-0a1b2c3d4e5f67890'

@app.route('/latest/meta-data/hostname')
def hostname():
    """Hostname"""
    return 'ip-10-0-1-100.internal'

@app.route('/latest/meta-data/local-ipv4')
def local_ip():
    """Local IPv4 address"""
    return '10.0.1.100'

@app.route('/latest/meta-data/public-ipv4')
def public_ip():
    """Public IPv4 address"""
    return '54.123.45.67'

@app.route('/latest/meta-data/admin-token')
def admin_token():
    """
    SENSITIVE: Admin token

    This is the target for SSRF exploitation!
    Attackers who successfully bypass SSRF filters can access this.
    """
    client_ip = request.remote_addr

    # Log access attempt
    print(f"[SECURITY] Admin token accessed from: {client_ip}")

    token = generate_admin_token()

    return jsonify({
        'admin_token': token,
        'expires_in': 3600,
        'type': 'Bearer',
        'scope': 'admin',
        'accessed_from': client_ip
    })

@app.route('/latest/meta-data/iam/security-credentials/')
def iam_roles():
    """IAM roles"""
    return 'admin-role\n'

@app.route('/latest/meta-data/iam/security-credentials/<role>')
def iam_credentials(role):
    """IAM credentials for role"""
    if role == 'admin-role':
        return jsonify({
            'Code': 'Success',
            'LastUpdated': '2026-01-08T12:00:00Z',
            'Type': 'AWS-HMAC',
            'AccessKeyId': 'ASIA' + 'X' * 16,
            'SecretAccessKey': 'SECRET' + 'Y' * 34,
            'Token': generate_admin_token(),
            'Expiration': '2026-01-08T18:00:00Z'
        })

    return jsonify({'Code': 'Error', 'Message': 'Role not found'}), 404

@app.route('/health')
def health():
    """Health check"""
    return jsonify({'status': 'healthy', 'service': 'metadata'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
