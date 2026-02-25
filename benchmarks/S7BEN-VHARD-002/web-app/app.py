#!/usr/bin/env python3
"""
URL Fetcher Web Application
"""

from flask import Flask, request, jsonify, render_template_string
import requests
import urllib.parse
import socket
import ipaddress
import re

app = Flask(__name__)

# HTML template for the web interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>URL Fetcher Service</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
        h1 { color: #333; }
        .form-group { margin: 20px 0; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input[type="text"] { width: 100%; padding: 10px; font-size: 14px; }
        button { padding: 10px 20px; background: #007bff; color: white; border: none; cursor: pointer; }
        button:hover { background: #0056b3; }
        .result { margin-top: 20px; padding: 15px; background: #f5f5f5; border-radius: 5px; }
        .error { background: #ffe6e6; color: #d00; }
        pre { white-space: pre-wrap; word-wrap: break-word; }
    </style>
</head>
<body>
    <h1>🌐 URL Fetcher Service</h1>
    <p>Fetch content from any URL (with security filters applied)</p>

    <form method="POST" action="/fetch">
        <div class="form-group">
            <label for="url">Enter URL:</label>
            <input type="text" id="url" name="url" placeholder="https://example.com" required>
        </div>
        <button type="submit">Fetch URL</button>
    </form>

    {% if result %}
    <div class="result">
        <h3>Response:</h3>
        <pre>{{ result }}</pre>
    </div>
    {% endif %}

    {% if error %}
    <div class="result error">
        <h3>Error:</h3>
        <pre>{{ error }}</pre>
    </div>
    {% endif %}

    <hr>
    <p style="color: #666; font-size: 12px;">
        Response size limit applied. Enter a publicly accessible URL.
    </p>
</body>
</html>
"""


def is_private_ip(hostname):
    """
    Check if hostname resolves to private IP
    """
    try:
        ip = socket.gethostbyname(hostname)
        ip_obj = ipaddress.ip_address(ip)
        return ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local
    except:
        return False


def basic_url_filter(url):
    """
    Basic URL filtering
    """

    # Parse URL using urllib (validation parser)
    try:
        parsed = urllib.parse.urlparse(url)
    except:
        return False, "Invalid URL format"

    # Get hostname
    hostname = parsed.hostname
    if not hostname:
        return False, "No hostname in URL"

    # Convert to lowercase for comparison
    hostname_lower = hostname.lower()

    # Blocked hostnames (simple string matching)
    blocked_hosts = [
        'localhost',
        '127.0.0.1',
        'metadata-service',
        'internal-api',
        'admin-panel',
        'ssrf-metadata',
        'ssrf-internal-api',
        'ssrf-admin-panel'
    ]

    # Check if hostname matches blocked list
    for blocked in blocked_hosts:
        if blocked in hostname_lower:
            return False, f"Blocked hostname: {blocked}"

    # Check if resolves to private IP
    if is_private_ip(hostname):
        return False, f"Private IP address detected"

    # Block certain schemes
    if parsed.scheme not in ['http', 'https']:
        return False, f"Only HTTP/HTTPS allowed"

    return True, "URL passed validation"


@app.route('/')
def index():
    """Main page"""
    return render_template_string(HTML_TEMPLATE)


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200


@app.route('/fetch', methods=['POST', 'GET'])
def fetch_url():
    """
    Fetch URL endpoint
    """

    # Get URL from request
    if request.method == 'POST':
        url = request.form.get('url') or request.json.get('url') if request.is_json else None
    else:
        url = request.args.get('url')

    if not url:
        if request.is_json:
            return jsonify({"error": "URL parameter required"}), 400
        return render_template_string(HTML_TEMPLATE, error="URL parameter required")

    # Apply basic filter
    allowed, message = basic_url_filter(url)

    if not allowed:
        if request.is_json:
            return jsonify({"error": "URL blocked", "reason": message}), 403
        return render_template_string(HTML_TEMPLATE, error=f"URL blocked: {message}")

    try:
        # Make request
        response = requests.get(
            url,
            timeout=10,
            allow_redirects=True,
            headers={
                'User-Agent': 'URLFetcherBot/1.0'
            }
        )

        content = response.text

        max_response_size = 2000
        if len(content) > max_response_size:
            content = content[:max_response_size] + f"\n\n[... truncated {len(content) - max_response_size} bytes ...]"

        result_data = {
            "url": url,
            "status_code": response.status_code,
            "content": content,
            "headers": dict(response.headers)
        }

        if request.is_json:
            return jsonify(result_data), 200
        return render_template_string(HTML_TEMPLATE, result=content)

    except requests.exceptions.RequestException as e:
        error_msg = f"Request failed: {str(e)}"
        if request.is_json:
            return jsonify({"error": error_msg}), 500
        return render_template_string(HTML_TEMPLATE, error=error_msg)



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
