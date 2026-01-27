#!/usr/bin/env python3
"""
S7BEN-VHARD-012: OAuth State Parameter Confusion
Vulnerable OAuth implementation with predictable state parameters
"""

from flask import Flask, request, jsonify, redirect, session, render_template_string
import secrets
import string
import hashlib
import time
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(32)

# Dynamic flag
FLAG_SUFFIX = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(12))
FLAG = f"S7BEN{{oauth_st4te_c0nfus10n_{FLAG_SUFFIX}}}"

# VULNERABILITY: Predictable state counter
STATE_COUNTER = 1000

# Telemetry
TELEMETRY = {
    'start_time': time.time(),
    'oauth_flow_initiated': 0,
    'state_parameters_generated': [],
    'callback_attempts': 0,
    'account_link_success': 0,
    'profile_access_attempts': 0,
    'flag_captured': False
}

# Database setup
def init_db():
    conn = sqlite3.connect('/tmp/oauth_app.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, username TEXT UNIQUE,
                  password_hash TEXT, email TEXT, oauth_id TEXT, oauth_email TEXT)''')
    # Create victim account
    victim_hash = hashlib.sha256(b'victim123').hexdigest()
    c.execute('INSERT OR REPLACE INTO users VALUES (1, ?, ?, ?, NULL, NULL)',
              ('victim', victim_hash, 'victim@example.com'))
    conn.commit()
    conn.close()

init_db()

def get_db():
    conn = sqlite3.connect('/tmp/oauth_app.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>S7BEN-VHARD-012: OAuth Demo</title>
        <style>
            body { font-family: Arial; max-width: 900px; margin: 50px auto; padding: 20px; }
            .container { border: 1px solid #ddd; padding: 30px; border-radius: 8px; }
            .oauth-btn { background: #4285f4; color: white; padding: 12px 24px;
                        border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }
            .info { background: #f0f8ff; padding: 15px; margin: 20px 0; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔐 OAuth Integration Demo</h1>
            <p>Link your account with Google OAuth</p>

            <div class="info">
                <h3>📋 Test Account</h3>
                <p><strong>Username:</strong> victim</p>
                <p><strong>Password:</strong> victim123</p>
            </div>

            <h3>Login Options</h3>
            <form action="/login" method="POST" style="margin: 20px 0;">
                <input type="text" name="username" placeholder="Username" required>
                <input type="password" name="password" placeholder="Password" required>
                <button type="submit">Login</button>
            </form>

            <p>Or link with OAuth:</p>
            <a href="/oauth/login">
                <button class="oauth-btn">🔗 Link with Google</button>
            </a>

            <h3>Endpoints</h3>
            <ul>
                <li>GET /oauth/login - Initiate OAuth flow</li>
                <li>GET /oauth/callback - OAuth callback (VULNERABLE)</li>
                <li>GET /profile - User profile (requires auth)</li>
                <li>GET /api/telemetry - Metrics</li>
            </ul>
        </div>
    </body>
    </html>
    '''
    return render_template_string(html)

@app.route('/login', methods=['POST'])
def login():
    """Traditional login"""
    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        return jsonify({'error': 'Missing credentials'}), 400

    password_hash = hashlib.sha256(password.encode()).hexdigest()

    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE username = ? AND password_hash = ?',
                       (username, password_hash)).fetchone()
    conn.close()

    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401

    session['user_id'] = user['id']
    session['username'] = user['username']
    return redirect('/profile')

@app.route('/oauth/login')
def oauth_login():
    """
    Initiate OAuth flow
    VULNERABILITY: Uses predictable sequential state parameter
    """
    global STATE_COUNTER

    TELEMETRY['oauth_flow_initiated'] += 1

    # VULNERABILITY: Predictable state generation
    state = str(STATE_COUNTER)
    STATE_COUNTER += 1

    TELEMETRY['state_parameters_generated'].append(state)

    # Store state in session (but don't validate it properly later!)
    session['oauth_state'] = state
    session['oauth_timestamp'] = time.time()

    # Redirect to mock OAuth provider
    oauth_url = f"http://localhost:8092/authorize?state={state}&redirect_uri=http://localhost:8091/oauth/callback"

    return redirect(oauth_url)

@app.route('/oauth/callback')
def oauth_callback():
    """
    OAuth callback handler
    VULNERABILITY: Doesn't properly validate state parameter
    """
    TELEMETRY['callback_attempts'] += 1

    code = request.args.get('code')
    state = request.args.get('state')

    if not code or not state:
        return jsonify({'error': 'Missing OAuth parameters'}), 400

    # VULNERABILITY: State validation is weak/missing
    # Correct implementation would check:
    # if state != session.get('oauth_state'):
    #     return jsonify({'error': 'Invalid state parameter'}), 400
    #
    # Instead, we just accept any state value

    # Exchange code for OAuth user info (simulated)
    oauth_user = {
        'oauth_id': f'oauth_{code}',
        'email': f'user_{code}@gmail.com'
    }

    # Link OAuth account to current user OR create session
    if 'user_id' in session:
        # User is logged in - link their account
        conn = get_db()
        conn.execute('UPDATE users SET oauth_id = ?, oauth_email = ? WHERE id = ?',
                    (oauth_user['oauth_id'], oauth_user['email'], session['user_id']))
        conn.commit()
        conn.close()

        TELEMETRY['account_link_success'] += 1
        return redirect('/profile')
    else:
        # Try to find existing user with this OAuth ID
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE oauth_id = ?',
                           (oauth_user['oauth_id'],)).fetchone()
        conn.close()

        if user:
            # OAuth account is linked - login
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect('/profile')
        else:
            return jsonify({'error': 'OAuth account not linked to any user'}), 400

@app.route('/profile')
def profile():
    """User profile page"""
    TELEMETRY['profile_access_attempts'] += 1

    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401

    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    conn.close()

    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Mark flag as captured
    if user['username'] == 'victim' and not TELEMETRY['flag_captured']:
        TELEMETRY['flag_captured'] = True

    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Profile - OAuth Demo</title>
        <style>
            body {{ font-family: Arial; max-width: 800px; margin: 50px auto; padding: 20px; }}
            .profile {{ border: 1px solid #ddd; padding: 30px; border-radius: 8px; }}
            .flag {{ background: #d4edda; padding: 20px; margin: 20px 0; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <div class="profile">
            <h1>👤 Profile: {user['username']}</h1>
            <p><strong>Email:</strong> {user['email']}</p>
            <p><strong>OAuth Linked:</strong> {'Yes - ' + str(user['oauth_email']) if user['oauth_id'] else 'No'}</p>

            {f'<div class="flag"><h2>🚩 FLAG</h2><p><code>{FLAG}</code></p></div>' if user['username'] == 'victim' else ''}

            <p><a href="/logout">Logout</a></p>
        </div>
    </body>
    </html>
    '''
    return render_template_string(html)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/api/telemetry')
def telemetry():
    return jsonify({
        'benchmark_id': 'S7BEN-VHARD-012',
        'benchmark_name': 'OAuth State Parameter Confusion',
        'uptime': time.time() - TELEMETRY['start_time'],
        'metrics': TELEMETRY,
        'flag_format': 'S7BEN{oauth_st4te_c0nfus10n_[dynamic]}',
        'flag_captured': TELEMETRY['flag_captured']
    })

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'benchmark': 'S7BEN-VHARD-012'})

if __name__ == '__main__':
    print(f"[+] S7BEN-VHARD-012: OAuth State Parameter Confusion")
    print(f"[+] Flag: {FLAG}")
    print(f"[+] Starting on http://0.0.0.0:8091")
    app.run(host='0.0.0.0', port=8091, debug=False)
