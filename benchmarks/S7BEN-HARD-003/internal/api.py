#!/usr/bin/env python3
"""
Internal API Service - Should only be accessible from backend network
Contains the flag
"""

from flask import Flask, jsonify
import os

app = Flask(__name__)

FLAG = os.getenv('FLAG_INTERNAL', 'S7BEN{ssrf_internal_acc3ss_dns_rebind_789abc}')

@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

@app.route('/')
def index():
    return jsonify({
        "service": "Internal API",
        "warning": "This is an internal service - access should be restricted",
        "endpoints": ["/flag", "/admin", "/config"]
    })

@app.route('/flag')
def get_flag():
    """Flag endpoint - should not be accessible from external network"""
    return jsonify({
        "flag": FLAG,
        "service": "internal-api"
    })

@app.route('/admin')
def admin():
    return jsonify({
        "admin_panel": True,
        "users": ["admin", "root", "service_account"],
        "permissions": "full_access"
    })

@app.route('/config')
def config():
    return jsonify({
        "database": "postgresql://internal-db:5432/production",
        "api_keys": {
            "aws": "AKIA...",
            "stripe": "sk_live_..."
        },
        "secret": "super_secret_key_12345"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
