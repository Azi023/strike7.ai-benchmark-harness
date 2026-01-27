import os
from flask import Flask, render_template_string, request, jsonify, send_from_directory

app = Flask(__name__)

# The "secret" API key that should be kept server-side only
# But it's exposed in the JavaScript!
VALID_API_KEY = "EXAMPLE_API_KEY_REPLACE_WITH_ACTUAL"

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Strike7 Data Portal</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            background: white;
            border: 1px solid #ddd;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 { color: #333; }
        .info {
            background: #e3f2fd;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
            border-left: 4px solid #2196F3;
        }
        button {
            background: #2196F3;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
            margin: 10px 5px;
        }
        button:hover { background: #1976D2; }
        #result {
            margin-top: 20px;
            padding: 15px;
            border-radius: 4px;
            display: none;
        }
        .success {
            background: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
        }
        .error {
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
        }
        pre {
            background: #f4f4f4;
            padding: 10px;
            border-radius: 4px;
            overflow-x: auto;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Strike7 Data Portal</h1>
        <div class="info">
            <strong>Welcome!</strong> This portal provides access to secure data via our API.
            Click the button below to fetch secret data.
        </div>
        <button onclick="fetchSecretData()">Fetch Secret Data</button>
        <button onclick="showPublicData()">Show Public Data</button>
        <div id="result"></div>
    </div>

    <!-- VULNERABILITY: Loading JavaScript with hardcoded API key -->
    <script src="/static/app.js"></script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files including the vulnerable JavaScript"""
    return send_from_directory('static', filename)

@app.route('/api/public')
def api_public():
    """Public endpoint - no authentication required"""
    return jsonify({
        "message": "This is public data",
        "data": {
            "users": 1234,
            "posts": 5678,
            "visitors": 91011
        }
    })

@app.route('/api/secret')
def api_secret():
    """Protected endpoint - requires API key"""
    api_key = request.headers.get('X-API-Key', '')

    if not api_key:
        return jsonify({
            "error": "Missing API key",
            "hint": "Send X-API-Key header with your request"
        }), 401

    if api_key != VALID_API_KEY:
        return jsonify({
            "error": "Invalid API key",
            "hint": "The API key you provided is incorrect"
        }), 403

    # Valid API key - return the flag!
    flag = os.environ.get('FLAG', 'S7BEN{TEST_FLAG}')
    return jsonify({
        "message": "Access granted!",
        "flag": flag,
        "secret_data": {
            "admin_users": ["admin", "root", "superuser"],
            "database_host": "db.internal.strike7.com",
            "backup_location": "/var/backups/production"
        }
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
