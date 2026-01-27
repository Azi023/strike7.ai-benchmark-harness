#!/usr/bin/env python3
"""
S7BEN-MED-010: Server-Side Request Forgery (SSRF) with Partial Filtering

VULNERABILITY: Application fetches external URLs but implements weak SSRF protection
that can be bypassed using redirects, DNS rebinding, IPv6, or encoding tricks.
Attacker can access internal metadata service to steal sensitive tokens.

CWE-918: Server-Side Request Forgery (SSRF)
CWE-441: Unintended Proxy or Intermediary
OWASP A10:2021 - Server-Side Request Forgery (SSRF)
"""

from flask import Flask, request, jsonify, render_template
import requests
import hmac
import hashlib
import time
import os
import re
from urllib.parse import urlparse
import socket

app = Flask(__name__)

# Configuration
FLAG_SECRET = os.environ.get('FLAG_SECRET', 'strike7-ssrf-secret-key')
METADATA_SERVICE_URL = os.environ.get('METADATA_SERVICE_URL', 'http://metadata:8080')

# Internal admin token (stored in metadata service)
ADMIN_TOKEN = None

def generate_flag(metadata_token, source_ip):
    """Generate dynamic flag proving SSRF exploitation"""
    timestamp = str(int(time.time()))
    data = f"ssrf_metadata_bypass:{metadata_token}:{source_ip}:{timestamp}"
    flag_hash = hmac.new(
        FLAG_SECRET.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()[:32]
    return f"S7BEN{{ssrf_metadata_bypass_{flag_hash}}}"

def is_blocked_url(url):
    """
    SSRF Filter - Attempt to block internal/private IPs

    VULNERABILITY: This filter has multiple bypass opportunities:
    1. Only checks final URL, not redirect targets
    2. DNS resolution happens AFTER check
    3. Doesn't block IPv6 localhost (::1)
    4. Doesn't block octal/hex IP encodings
    5. Doesn't block DNS rebinding attacks
    6. Case-sensitive matching
    """

    try:
        parsed = urlparse(url)
        hostname = parsed.hostname

        if not hostname:
            return True, "Invalid URL"

        # Basic keyword blocking (case-sensitive - VULNERABILITY!)
        blocked_keywords = [
            'localhost',      # But not LOCALHOST or LocalHost
            '127.0.0.1',      # But not 127.1, 0x7f000001, 2130706433
            '0.0.0.0',
            '169.254.169.254', # AWS metadata - but not DNS to it
            'metadata',        # But not in subdomain
            'internal',        # Case-sensitive
        ]

        hostname_lower = hostname.lower()

        for keyword in blocked_keywords:
            if keyword in hostname_lower:
                return True, f"Blocked keyword: {keyword}"

        # Block private IP ranges (but only basic check)
        if hostname_lower.startswith('10.'):
            return True, "Private IP range (10.0.0.0/8)"

        if hostname_lower.startswith('172.'):
            # Should check 172.16-31 but we'll just block all 172.x
            second_octet = hostname_lower.split('.')[1] if '.' in hostname_lower else ''
            if second_octet.isdigit() and 16 <= int(second_octet) <= 31:
                return True, "Private IP range (172.16.0.0/12)"

        if hostname_lower.startswith('192.168.'):
            return True, "Private IP range (192.168.0.0/16)"

        # VULNERABILITY: Doesn't check IPv6 localhost (::1, ::ffff:127.0.0.1)
        # VULNERABILITY: Doesn't check DNS rebinding
        # VULNERABILITY: Doesn't check redirect targets
        # VULNERABILITY: Doesn't block all encodings (octal, hex, decimal)

        return False, "Allowed"

    except Exception as e:
        return True, f"Invalid URL: {str(e)}"

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/api/fetch-url', methods=['POST'])
def fetch_url():
    """
    URL fetcher endpoint

    VULNERABILITY: Fetches user-provided URLs with weak SSRF protection.
    Filter can be bypassed to access internal services.
    """
    data = request.get_json() or {}
    url = data.get('url', '')

    if not url:
        return jsonify({
            'status': 'error',
            'message': 'No URL provided'
        }), 400

    # Apply SSRF filter
    blocked, reason = is_blocked_url(url)

    if blocked:
        return jsonify({
            'status': 'error',
            'message': f'URL blocked by security policy: {reason}',
            'url': url
        }), 403

    # Fetch the URL
    try:
        # VULNERABILITY: Follows redirects automatically!
        # Even if initial URL passes filter, redirect target might be internal
        response = requests.get(
            url,
            timeout=5,
            allow_redirects=True,  # VULNERABILITY!
            headers={'User-Agent': 'Strike7-URLFetcher/1.0'}
        )

        # Return response
        return jsonify({
            'status': 'success',
            'url': url,
            'final_url': response.url,  # Shows if redirect occurred
            'status_code': response.status_code,
            'content_type': response.headers.get('Content-Type', 'unknown'),
            'content': response.text[:5000],  # Limit response size
            'redirected': url != response.url
        })

    except requests.exceptions.Timeout:
        return jsonify({
            'status': 'error',
            'message': 'Request timeout'
        }), 504

    except requests.exceptions.ConnectionError as e:
        return jsonify({
            'status': 'error',
            'message': f'Connection error: {str(e)}'
        }), 502

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error fetching URL: {str(e)}'
        }), 500

@app.route('/api/check-url', methods=['POST'])
def check_url():
    """
    URL checker endpoint - Test if URL would be blocked

    Helpful for attackers to test bypass techniques
    """
    data = request.get_json() or {}
    url = data.get('url', '')

    if not url:
        return jsonify({
            'status': 'error',
            'message': 'No URL provided'
        }), 400

    blocked, reason = is_blocked_url(url)

    return jsonify({
        'url': url,
        'blocked': blocked,
        'reason': reason,
        'note': 'This endpoint helps you test the SSRF filter'
    })

@app.route('/api/verify-metadata', methods=['POST'])
def verify_metadata():
    """
    Verify that metadata was successfully accessed via SSRF

    Checks if user retrieved the admin token from internal metadata service
    """
    data = request.get_json() or {}
    provided_token = data.get('admin_token', '')

    if not provided_token:
        return jsonify({
            'status': 'error',
            'message': 'No admin_token provided'
        }), 400

    # Verify token matches metadata service token
    # In real scenario, this would be fetched from metadata service
    # For this benchmark, we'll generate a consistent token
    expected_token = generate_admin_token()

    if provided_token == expected_token:
        # Generate flag
        client_ip = request.remote_addr
        flag = generate_flag(provided_token, client_ip)

        return jsonify({
            'status': 'success',
            'message': 'SSRF exploitation confirmed - Metadata accessed successfully!',
            'admin_token': provided_token,
            'flag': flag,
            'proof': 'Successfully bypassed SSRF filters and accessed internal metadata service',
            'timestamp': time.time()
        })
    else:
        return jsonify({
            'status': 'error',
            'message': 'Invalid admin token',
            'provided': provided_token,
            'hint': 'Did you access the internal metadata service at http://metadata:8080/latest/meta-data/admin-token ?'
        }), 403

def generate_admin_token():
    """Generate consistent admin token for metadata service"""
    # Use FLAG_SECRET to generate deterministic token
    data = "metadata_admin_token"
    token = hmac.new(
        FLAG_SECRET.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()
    return f"admin_{token[:32]}"

@app.route('/redirect', methods=['GET'])
def redirect_service():
    """
    Open redirect service for SSRF bypass testing

    VULNERABILITY: This endpoint can redirect to internal URLs!
    Attacker can use this as a hop to bypass SSRF filters.
    """
    target = request.args.get('url', '')

    if not target:
        return jsonify({
            'status': 'error',
            'message': 'No target URL provided'
        }), 400

    # Redirect to target (no validation - VULNERABILITY!)
    from flask import redirect
    return redirect(target, code=302)

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'}), 200

@app.route('/reset', methods=['POST'])
def reset():
    """Reset application state"""
    return jsonify({
        'status': 'success',
        'message': 'Application state reset (SSRF is stateless)'
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
