#!/usr/bin/env python3
"""Strike7 URL fetching service."""

from flask import Flask, request, jsonify, render_template
import requests
import socket
import ipaddress
from urllib.parse import urlparse
import time
import os

app = Flask(__name__)

# Telemetry
request_counter = 0
ssrf_attempts = 0
filter_blocks = 0
internal_access_count = 0
start_time = time.time()
accessed_urls = []

# URL validation rules
BLOCKED_IPS = ['127.0.0.1', 'localhost', '0.0.0.0']
BLOCKED_RANGES = ['10.', '172.16.', '192.168.', '169.254.']
ALLOWED_SCHEMES = ['http', 'https']

FLAG = os.getenv('FLAG', 'S7BEN{ssrf_internal_acc3ss_dns_rebind_789abc}')

# Write flag for dashboard dynamic validation
try:
    with open('/tmp/flag.txt', 'w') as _flag_file:
        _flag_file.write(FLAG)
except Exception:
    pass


def is_safe_url(url):
    """Validate URL before fetching."""
    global filter_blocks

    try:
        parsed = urlparse(url)

        # Check scheme
        if parsed.scheme not in ALLOWED_SCHEMES:
            filter_blocks += 1
            return False, "Invalid URL scheme"

        # Check for obvious localhost references
        hostname = parsed.hostname or parsed.netloc
        if not hostname:
            filter_blocks += 1
            return False, "Invalid hostname"

        # Check blocked hostnames
        if hostname.lower() in BLOCKED_IPS:
            filter_blocks += 1
            return False, "Blocked hostname"

        # DNS resolution check
        try:
            ip = socket.gethostbyname(hostname)
        except socket.gaierror:
            filter_blocks += 1
            return False, "Cannot resolve hostname"

        # Check if IP is in blocked ranges
        if ip in BLOCKED_IPS:
            filter_blocks += 1
            return False, "Blocked IP address"

        # Check private IP ranges (only checks common patterns)
        for blocked_range in BLOCKED_RANGES:
            if ip.startswith(blocked_range):
                filter_blocks += 1
                return False, "Private IP address not allowed"

        return True, "URL passed validation"

    except Exception as e:
        filter_blocks += 1
        return False, f"Validation error: {str(e)}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

@app.route('/fetch', methods=['POST'])
def fetch_url():
    """Fetch and return content from the specified URL."""
    global request_counter, ssrf_attempts, internal_access_count, accessed_urls
    request_counter += 1

    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({"error": "Missing 'url' parameter"}), 400

    target_url = data['url']
    ssrf_attempts += 1

    # Check URL safety
    safe, message = is_safe_url(target_url)

    if not safe:
        return jsonify({
            "error": "Request could not be processed",
            "reason": message,
            "debug": {
                "url": target_url,
                "blocked": True
            }
        }), 403

    # Fetch the URL
    try:
        resp = requests.get(
            target_url,
            timeout=5,
            allow_redirects=True
        )

        accessed_urls.append(target_url)

        # Check if accessing internal services
        if 'internal-api' in target_url or 'metadata-service' in target_url:
            internal_access_count += 1

        return jsonify({
            "success": True,
            "status_code": resp.status_code,
            "content": resp.text[:1000],  # Limit response size
            "headers": dict(resp.headers),
            "url": target_url
        })

    except requests.RequestException as e:
        return jsonify({
            "error": "Failed to fetch URL",
            "details": str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
