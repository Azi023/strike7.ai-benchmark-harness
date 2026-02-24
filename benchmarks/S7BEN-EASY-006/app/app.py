import os
import re
import secrets
from flask import Flask, render_template_string, request, jsonify
from datetime import datetime

app = Flask(__name__)
FLAG = f"S7BEN{{l0g_1nj3ct10n_{secrets.token_hex(8)}}}"

# Write flag for dashboard dynamic validation
try:
    with open('/tmp/flag.txt', 'w') as _flag_file:
        _flag_file.write(FLAG)
except Exception:
    pass


# Log file path
LOG_FILE = '/tmp/app.log'

# Simple user database
USERS = {
    'admin': 'supersecret',
    'user': 'password123'
}

def init_log():
    """Initialize log file"""
    with open(LOG_FILE, 'w') as f:
        f.write(f"[{datetime.now().isoformat()}] Application started\n")
        f.write(f"[{datetime.now().isoformat()}] Log file initialized\n")

# Initialize log on startup
init_log()

def log_message(message):
    """Write message to log file"""
    timestamp = datetime.now().isoformat()
    with open(LOG_FILE, 'a') as f:
        f.write(f"[{timestamp}] {message}\n")

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Strike7 Secure Login</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 600px;
            margin: 50px auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 { color: #333; }
        .info {
            background: #fff3cd;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
            border-left: 4px solid #ffc107;
        }
        input {
            width: 100%;
            padding: 10px;
            margin: 5px 0;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-sizing: border-box;
        }
        button {
            background: #007bff;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            width: 100%;
            margin: 10px 0;
        }
        button:hover { background: #0056b3; }
        .secondary {
            background: #6c757d;
        }
        .secondary:hover {
            background: #5a6268;
        }
        .message {
            padding: 15px;
            margin: 15px 0;
            border-radius: 4px;
        }
        .error { background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; }
        .success { background: #d4edda; border: 1px solid #c3e6cb; color: #155724; }
        pre {
            background: #f4f4f4;
            padding: 10px;
            border-radius: 4px;
            overflow-x: auto;
            font-size: 12px;
            max-height: 400px;
            overflow-y: auto;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Strike7 Secure Login</h1>

        <div class="info">
            <strong>Security Note:</strong> All login attempts are logged for security monitoring.
        </div>

        <form method="POST" action="/login">
            <label>Username:</label>
            <input type="text" name="username" required>
            <label>Password:</label>
            <input type="password" name="password" required>
            <button type="submit">Login</button>
        </form>

        <button class="secondary" onclick="window.location.href='/logs'">View Logs</button>
        <button class="secondary" onclick="window.location.href='/verify'">Verify Injection</button>

        {% if message %}
        <div class="message {{ message_type }}">{{ message }}</div>
        {% endif %}
    </div>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    ip = request.remote_addr

    log_message(f"Login attempt - Username: {username}, IP: {ip}")

    # Check credentials
    if username in USERS and USERS[username] == password:
        log_message(f"Login successful - Username: {username}, IP: {ip}")
        return render_template_string(HTML_TEMPLATE,
                                     message=f"Welcome, {username}!",
                                     message_type="success")

    log_message(f"Login failed - Invalid credentials for username: {username}")
    return render_template_string(HTML_TEMPLATE,
                                 message="Invalid credentials",
                                 message_type="error")

@app.route('/logs')
def view_logs():
    """View the log file"""
    try:
        with open(LOG_FILE, 'r') as f:
            logs = f.read()

        html = f'''
        <html>
        <head>
            <title>Application Logs</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 20px;
                    background: #f5f5f5;
                }}
                .container {{
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    max-width: 1200px;
                    margin: 0 auto;
                }}
                pre {{
                    background: #f4f4f4;
                    padding: 15px;
                    border-radius: 4px;
                    overflow-x: auto;
                    font-size: 12px;
                }}
                button {{
                    background: #007bff;
                    color: white;
                    padding: 10px 20px;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    margin: 10px 5px;
                }}
                button:hover {{ background: #0056b3; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Application Logs</h1>
                <button onclick="window.location.href='/'">Back to Login</button>
                <button onclick="window.location.href='/verify'">Verify Injection</button>
                <pre>{logs}</pre>
            </div>
        </body>
        </html>
        '''
        return html
    except Exception as e:
        return f"Error reading logs: {e}", 500

@app.route('/verify')
def verify_injection():
    """
    Verify if a successful log injection was performed.
    Checks if logs contain a forged admin login from trusted IP.
    """
    try:
        with open(LOG_FILE, 'r') as f:
            logs = f.read()

        # Pattern to detect forged admin login from localhost
        # Looking for entries that appear to be legitimate but were injected
        patterns = [
            r'Login successful - Username: admin, IP: 127\.0\.0\.1',
            r'Login attempt - Username: admin, IP: 127\.0\.0\.1',
        ]

        # Check if the log contains what looks like a forged entry
        # We need to detect if someone injected a newline to create a fake "successful" entry

        # Look for the specific pattern of a successful admin login from localhost
        # that was NOT actually a real login (i.e., was injected)

        # Strategy: Look for admin login success from 127.0.0.1 AFTER a login attempt
        # that contains newlines in the username field

        lines = logs.split('\n')

        # Check if there's evidence of newline injection
        injection_detected = False
        forged_success = False

        for i, line in enumerate(lines):
            # Look for login attempts with suspicious patterns
            # If a line doesn't start with timestamp but contains login info, it's injected
            if 'Login' in line and not line.startswith('['):
                injection_detected = True

            # Look for forged admin success from localhost
            if re.search(patterns[0], line):
                # Check if this is in a suspicious context
                # (part of an injected sequence, not a real login)
                if injection_detected or (i > 0 and not lines[i-1].strip().endswith(']')):
                    forged_success = True

        if forged_success:
            flag = FLAG

            html = f'''
            <html>
            <head>
                <title>Verification Result</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        margin: 20px;
                        background: #f5f5f5;
                    }}
                    .container {{
                        background: white;
                        padding: 30px;
                        border-radius: 8px;
                        max-width: 800px;
                        margin: 0 auto;
                    }}
                    .success {{
                        background: #d4edda;
                        border: 2px solid #c3e6cb;
                        color: #155724;
                        padding: 20px;
                        border-radius: 8px;
                        margin: 20px 0;
                    }}
                    .flag {{
                        background: #f0f0f0;
                        padding: 15px;
                        border-radius: 4px;
                        font-family: monospace;
                        font-size: 18px;
                        margin: 15px 0;
                    }}
                    button {{
                        background: #007bff;
                        color: white;
                        padding: 10px 20px;
                        border: none;
                        border-radius: 4px;
                        cursor: pointer;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Verification Successful!</h1>
                    <div class="success">
                        <h2>Challenge Complete!</h2>
                        <p>You successfully completed the log challenge.</p>
                        <div class="flag">FLAG: {flag}</div>
                    </div>
                    <button onclick="window.location.href='/'">Back to Login</button>
                    <button onclick="window.location.href='/logs'">View Logs</button>
                </div>
            </body>
            </html>
            '''
            return html
        else:
            html = '''
            <html>
            <head>
                <title>Verification Result</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        margin: 20px;
                        background: #f5f5f5;
                    }
                    .container {
                        background: white;
                        padding: 30px;
                        border-radius: 8px;
                        max-width: 800px;
                        margin: 0 auto;
                    }
                    .error {
                        background: #f8d7da;
                        border: 2px solid #f5c6cb;
                        color: #721c24;
                        padding: 20px;
                        border-radius: 8px;
                    }
                    button {
                        background: #007bff;
                        color: white;
                        padding: 10px 20px;
                        border: none;
                        border-radius: 4px;
                        cursor: pointer;
                        margin: 10px 5px;
                    }
                    .hint {
                        background: #fff3cd;
                        padding: 15px;
                        margin: 15px 0;
                        border-radius: 4px;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>No Valid Injection Detected</h1>
                    <div class="error">
                        <p>The log file does not contain a forged admin login entry from 127.0.0.1.</p>
                    </div>
                    <button onclick="window.location.href='/'">Back to Login</button>
                    <button onclick="window.location.href='/logs'">View Logs</button>
                </div>
            </body>
            </html>
            '''
            return html

    except Exception as e:
        return f"Error verifying injection: {e}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
