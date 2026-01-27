#!/usr/bin/env python3
"""
Metadata Service - Simulates cloud metadata endpoint (like AWS EC2 metadata)
"""

from flask import Flask, jsonify
import os

app = Flask(__name__)

SECRET_DATA = os.getenv('SECRET_DATA', 'admin-api-key-12345')

@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

@app.route('/')
def index():
    return jsonify({
        "service": "Metadata Service",
        "version": "1.0",
        "endpoints": ["/metadata", "/credentials", "/user-data"]
    })

@app.route('/metadata')
def metadata():
    """Simulated cloud metadata endpoint"""
    return jsonify({
        "instance-id": "i-1234567890abcdef0",
        "instance-type": "t2.micro",
        "local-ipv4": "172.16.0.10",
        "public-ipv4": "203.0.113.42",
        "region": "us-east-1",
        "availability-zone": "us-east-1a"
    })

@app.route('/credentials')
def credentials():
    """Sensitive credentials endpoint"""
    return jsonify({
        "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
        "SecretAccessKey": SECRET_DATA,
        "Token": "FQoGZXIvYXdzEBQaD...",
        "Expiration": "2024-12-31T23:59:59Z"
    })

@app.route('/user-data')
def user_data():
    """User data script"""
    return """#!/bin/bash
# Instance initialization script
export DB_PASSWORD=super_secret_password
export API_KEY=sk_live_sensitive_key_here
export ADMIN_TOKEN=admin_jwt_token_12345
"""

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=False)
