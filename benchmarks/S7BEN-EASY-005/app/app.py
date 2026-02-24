import os
import secrets
from flask import Flask, render_template_string, request, session, redirect, url_for, jsonify
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'session-secret-key')
FLAG = f"S7BEN{{l0gg1ng_f41lure_{secrets.token_hex(8)}}}"

# Write flag for dashboard dynamic validation
try:
    with open('/tmp/flag.txt', 'w') as _flag_file:
        _flag_file.write(FLAG)
except Exception:
    pass


# Simple user database
USERS = {
    'admin': 'weakpass123',
    'user': 'password123'
}

# Track successful logins
successful_logins = []

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Strike7 Login Portal</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 500px; margin: 50px auto; padding: 20px; }
        .container { border: 1px solid #ccc; padding: 20px; border-radius: 5px; }
        input { width: 100%; padding: 8px; margin: 5px 0; box-sizing: border-box; }
        button { background: #007bff; color: white; padding: 10px 20px; border: none; cursor: pointer; width: 100%; }
        button:hover { background: #0056b3; }
        .error { color: red; margin: 10px 0; }
        .success { color: green; margin: 10px 0; }
        .info { background: #f0f0f0; padding: 10px; margin: 10px 0; border-radius: 3px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Strike7 Login Portal</h1>
        {% if message %}
            <div class="{{ message_type }}">{{ message }}</div>
        {% endif %}
        <form method="POST" action="/login">
            <label>Username:</label>
            <input type="text" name="username" required>
            <label>Password:</label>
            <input type="password" name="password" required>
            <button type="submit">Login</button>
        </form>
    </div>
</body>
</html>
'''

ADMIN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Admin Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
        .container { border: 1px solid #ccc; padding: 20px; border-radius: 5px; }
        .success { color: green; font-size: 24px; margin: 20px 0; }
        .flag { background: #f0f0f0; padding: 20px; border-radius: 5px; font-family: monospace; font-size: 18px; }
        .logout { margin-top: 20px; }
        a { color: #007bff; text-decoration: none; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Admin Dashboard</h1>
        <div class="success">Welcome, {{ username }}!</div>
        <h2>Flag:</h2>
        <div class="flag">{{ flag }}</div>
        <p>You accessed the admin panel successfully.</p>
        <div class="logout">
            <a href="/logout">Logout</a>
        </div>
    </div>
</body>
</html>
'''

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return render_template_string(HTML_TEMPLATE)

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')

    # Check credentials
    if username in USERS and USERS[username] == password:
        session['username'] = username

        # GOOD PRACTICE: Log successful logins
        successful_logins.append({
            'username': username,
            'timestamp': datetime.now().isoformat(),
            'ip': request.remote_addr
        })

        return redirect(url_for('dashboard'))

    return render_template_string(HTML_TEMPLATE,
                                 message="Invalid credentials",
                                 message_type="error")

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('index'))

    username = session['username']

    # Only admin gets the flag
    if username == 'admin':
        flag = FLAG
        return render_template_string(ADMIN_TEMPLATE, username=username, flag=flag)

    # Regular users see a basic dashboard
    return f'''
    <html>
    <body>
        <h1>User Dashboard</h1>
        <p>Welcome, {username}!</p>
        <p>You don't have admin privileges.</p>
        <a href="/logout">Logout</a>
    </body>
    </html>
    '''

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/logs')
def logs():
    """Show login activity."""
    return jsonify({
        'successful_logins': successful_logins,
        'failed_logins': []
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
