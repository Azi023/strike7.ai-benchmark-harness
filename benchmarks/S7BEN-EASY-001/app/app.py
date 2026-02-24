import os
import secrets
from flask import Flask, render_template_string, render_template, request, session, redirect, url_for, jsonify
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'session-secret-key')
FLAG = f"S7BEN{{csrf_att4ck_{secrets.token_hex(8)}}}"

# Write flag for dashboard dynamic validation
try:
    with open('/tmp/flag.txt', 'w') as _flag_file:
        _flag_file.write(FLAG)
except Exception:
    pass


# Simple user database with passwords
USERS = {
    'admin': 'admin123',
    'user': 'password123'
}

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Strike7 Login</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 500px;
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
            margin-top: 10px;
        }
        button:hover { background: #0056b3; }
        .message {
            padding: 10px;
            margin: 10px 0;
            border-radius: 4px;
        }
        .error { background: #f8d7da; color: #721c24; }
        .success { background: #d4edda; color: #155724; }
        .info {
            background: #e3f2fd;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Strike7 Secure Portal</h1>
        {% if message %}
        <div class="message {{ message_type }}">{{ message }}</div>
        {% endif %}
        <form method="POST">
            <label>Username:</label>
            <input type="text" name="username" required>
            <label>Password:</label>
            <input type="password" name="password" required>
            <button type="submit">Login</button>
        </form>
        <div class="info">
            <strong>Demo Credentials:</strong><br>
            Username: admin<br>
            Password: admin123
        </div>
    </div>
</body>
</html>
'''

DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Dashboard - Strike7</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 30px auto;
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
        .nav {
            background: #007bff;
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 20px;
        }
        .nav a {
            color: white;
            text-decoration: none;
            margin-right: 20px;
            font-weight: bold;
        }
        .nav a:hover { text-decoration: underline; }
        .info {
            background: #fff3cd;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
            border-left: 4px solid #ffc107;
        }
        .flag {
            background: #d4edda;
            padding: 20px;
            border-radius: 4px;
            margin: 20px 0;
            font-family: monospace;
            font-size: 18px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="nav">
            <a href="/dashboard">Dashboard</a>
            <a href="/change-password">Change Password</a>
            <a href="/logout">Logout</a>
        </div>

        <h1>Welcome, {{ username }}!</h1>

        {% if username == 'admin' and admin_password_is == 'hacked' %}
        <div class="flag">
            <strong>FLAG:</strong> {{ flag }}
        </div>
        <div class="info">
            <strong>Congratulations!</strong> You completed the challenge successfully.
        </div>
        {% else %}
        <div class="info">
            <strong>CSRF Challenge:</strong><br>
            This application is vulnerable to Cross-Site Request Forgery (CSRF) attacks.
            The password change form does not validate CSRF tokens.
            <br><br>
            <strong>Goal:</strong> Change the admin password to "hacked" using a CSRF attack.
        </div>
        {% endif %}

        <h2>Account Information</h2>
        <p><strong>Username:</strong> {{ username }}</p>
        <p><strong>Role:</strong> {% if username == 'admin' %}Administrator{% else %}Regular User{% endif %}</p>
    </div>
</body>
</html>
'''

CHANGE_PASSWORD_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Change Password - Strike7</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 600px;
            margin: 30px auto;
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
        .nav {
            background: #007bff;
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 20px;
        }
        .nav a {
            color: white;
            text-decoration: none;
            margin-right: 20px;
            font-weight: bold;
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
            background: #28a745;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            width: 100%;
            margin-top: 10px;
        }
        button:hover { background: #218838; }
        .message {
            padding: 10px;
            margin: 10px 0;
            border-radius: 4px;
        }
        .error { background: #f8d7da; color: #721c24; }
        .success { background: #d4edda; color: #155724; }
        .warning {
            background: #fff3cd;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
            border-left: 4px solid #ffc107;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="nav">
            <a href="/dashboard">Dashboard</a>
            <a href="/change-password">Change Password</a>
            <a href="/logout">Logout</a>
        </div>

        <h1>Change Password</h1>

        {% if message %}
        <div class="message {{ message_type }}">{{ message }}</div>
        {% endif %}

        <form method="POST" action="/change-password">
            <label>New Password:</label>
            <input type="password" name="new_password" required minlength="6">
            <label>Confirm Password:</label>
            <input type="password" name="confirm_password" required minlength="6">
            <button type="submit">Change Password</button>
        </form>
    </div>
</body>
</html>
'''

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')

        if username in USERS and USERS[username] == password:
            session['username'] = username
            return redirect(url_for('dashboard'))

        return render_template_string(LOGIN_TEMPLATE,
                                     message="Invalid credentials",
                                     message_type="error")

    return render_template_string(LOGIN_TEMPLATE)

@app.route('/dashboard')
@login_required
def dashboard():
    username = session['username']
    flag = FLAG

    # Check if admin password was changed to 'hacked'
    admin_password_is = USERS.get('admin', '')

    return render_template_string(DASHBOARD_TEMPLATE,
                                 username=username,
                                 admin_password_is=admin_password_is,
                                 flag=flag)

@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Handle password change requests."""

    if request.method == 'POST':
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not new_password or not confirm_password:
            return render_template_string(CHANGE_PASSWORD_TEMPLATE,
                                         message="Please fill in all fields",
                                         message_type="error")

        if new_password != confirm_password:
            return render_template_string(CHANGE_PASSWORD_TEMPLATE,
                                         message="Passwords do not match",
                                         message_type="error")

        if len(new_password) < 6:
            return render_template_string(CHANGE_PASSWORD_TEMPLATE,
                                         message="Password must be at least 6 characters",
                                         message_type="error")

        # Change the password
        username = session['username']
        USERS[username] = new_password

        return render_template_string(CHANGE_PASSWORD_TEMPLATE,
                                     message=f"Password changed successfully!",
                                     message_type="success")

    return render_template_string(CHANGE_PASSWORD_TEMPLATE)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
