import os
import sqlite3
import hmac
import hashlib
import secrets
import time
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, redirect, url_for, make_response
from functools import wraps

app = Flask(__name__)
FLAG_SECRET = os.environ.get('FLAG_SECRET', 'strike7-secret-key-for-flag-generation')
DB_FILE = '/app/data/sessions.db'

# User database
USERS = {
    'alice': 'password123',
    'bob': 'secretpass',
    'charlie': 'admin2025'
}

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_FILE, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database"""
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)

    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            created_by TEXT,
            created_at TEXT,
            authenticated_user TEXT,
            authenticated_at TEXT,
            last_accessed TEXT,
            expires_at TEXT,
            is_authenticated INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()
    print("[*] Database initialized")

# Initialize on startup
init_db()

def generate_flag(session_id, hijacker, victim):
    """
    Generate dynamic flag based on successful hijack.

    Flag format: S7BEN{HMAC(secret, hijacker + victim + session_id + timestamp)}
    This proves the attacker successfully hijacked a session they didn't create.
    """
    timestamp = str(int(time.time()))
    data = f"{hijacker}:{victim}:{session_id}:{timestamp}"
    flag_hash = hmac.new(
        FLAG_SECRET.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()[:32]

    return f"S7BEN{{session_fixation_{flag_hash}}}"

def get_session():
    """Get current session data"""
    session_id = request.cookies.get('session_id') or request.args.get('sid')

    if not session_id:
        return None

    conn = get_db()
    cur = conn.execute('SELECT * FROM sessions WHERE session_id = ?', (session_id,))
    session = cur.fetchone()
    conn.close()

    if not session:
        return None

    # Check expiry
    expires_at = datetime.fromisoformat(session['expires_at'])
    if datetime.now() > expires_at:
        return None

    # Update last accessed
    conn = get_db()
    conn.execute(
        'UPDATE sessions SET last_accessed = ? WHERE session_id = ?',
        (datetime.now().isoformat(), session_id)
    )
    conn.commit()
    conn.close()

    return dict(session)

def create_session(created_by, session_id=None):
    """
    Create a new session.

    VULNERABILITY: If session_id is provided (from URL), we use it instead of generating new one!
    """
    if not session_id:
        session_id = secrets.token_urlsafe(32)

    now = datetime.now()
    expires = now + timedelta(minutes=10)

    conn = get_db()

    # Check if session already exists
    cur = conn.execute('SELECT * FROM sessions WHERE session_id = ?', (session_id,))
    existing = cur.fetchone()

    if existing:
        # Session already exists - just return it (vulnerability!)
        conn.close()
        return session_id

    # Create new session
    conn.execute('''
        INSERT INTO sessions
        (session_id, created_by, created_at, last_accessed, expires_at, is_authenticated)
        VALUES (?, ?, ?, ?, ?, 0)
    ''', (session_id, created_by, now.isoformat(), now.isoformat(), expires.isoformat()))

    conn.commit()
    conn.close()

    return session_id

def authenticate_session(session_id, username):
    """
    Authenticate an existing session.

    VULNERABILITY: Session ID is NOT regenerated after authentication!
    Proper fix would be to create a new session_id and migrate data.
    """
    conn = get_db()

    conn.execute('''
        UPDATE sessions
        SET authenticated_user = ?,
            authenticated_at = ?,
            is_authenticated = 1
        WHERE session_id = ?
    ''', (username, datetime.now().isoformat(), session_id))

    conn.commit()
    conn.close()

def login_required(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        session = get_session()
        if not session or not session['is_authenticated']:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    """Homepage"""
    session = get_session()

    if session and session['is_authenticated']:
        return redirect(url_for('dashboard'))

    return render_template('index.html')

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok"})

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Login endpoint.

    VULNERABILITY: Accepts session ID from URL parameter (?sid=XXX)
    and doesn't regenerate it after successful authentication.
    """
    if request.method == 'GET':
        # Check if session ID provided in URL
        sid = request.args.get('sid')

        if sid:
            # VULNERABILITY: Create/use session with attacker-provided ID
            create_session('attacker_controlled', session_id=sid)

        return render_template('login.html', sid=sid)

    # POST: Process login
    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        return render_template('login.html', error="Please provide username and password")

    if username not in USERS or USERS[username] != password:
        return render_template('login.html', error="Invalid credentials")

    # Get or create session
    session = get_session()
    session_id = request.cookies.get('session_id') or request.args.get('sid')

    if not session_id:
        # No existing session - create new one
        session_id = create_session(username)
    else:
        # Existing session - just authenticate it (VULNERABILITY!)
        # Proper fix: session_id = regenerate_session(session_id)
        pass

    # Authenticate the session
    authenticate_session(session_id, username)

    # Set cookie
    response = make_response(redirect(url_for('dashboard')))
    response.set_cookie('session_id', session_id, max_age=600, httponly=True)

    return response

@app.route('/dashboard')
@login_required
def dashboard():
    """Protected dashboard"""
    session = get_session()
    return render_template('dashboard.html', session=session)

@app.route('/logout')
def logout():
    """Logout endpoint"""
    session_id = request.cookies.get('session_id')

    if session_id:
        conn = get_db()
        conn.execute('DELETE FROM sessions WHERE session_id = ?', (session_id,))
        conn.commit()
        conn.close()

    response = make_response(redirect(url_for('index')))
    response.delete_cookie('session_id')
    return response

@app.route('/api/session')
def api_session():
    """Get current session info (JSON)"""
    session = get_session()

    if not session:
        return jsonify({
            "status": "no_session",
            "session_exists": False
        })

    return jsonify({
        "status": "success",
        "session_exists": True,
        "session_id": session['session_id'],
        "created_by": session['created_by'],
        "created_at": session['created_at'],
        "authenticated_user": session['authenticated_user'],
        "authenticated_at": session['authenticated_at'],
        "is_authenticated": bool(session['is_authenticated']),
        "last_accessed": session['last_accessed'],
        "expires_at": session['expires_at']
    })

@app.route('/api/verify-hijack', methods=['POST'])
def verify_hijack():
    """
    Verify if current session represents a successful hijack.

    A hijack is proven when:
    - Session is authenticated
    - Session was created_by someone other than the authenticated_user
    - Attacker is accessing with the fixed session_id

    Returns dynamic flag if hijack detected.
    """
    session = get_session()

    if not session:
        return jsonify({
            "status": "error",
            "message": "No active session"
        }), 400

    if not session['is_authenticated']:
        return jsonify({
            "status": "error",
            "message": "Session not authenticated"
        }), 400

    # Check if this is a hijacked session
    created_by = session['created_by']
    authenticated_user = session['authenticated_user']
    session_id = session['session_id']

    # Hijack detected if:
    # 1. created_by is 'attacker_controlled' (from URL param)
    # 2. authenticated_user is a real user (victim logged in)
    # 3. They are different

    is_hijack = (
        created_by == 'attacker_controlled' and
        authenticated_user and
        authenticated_user in USERS
    )

    if is_hijack:
        # Generate dynamic flag
        flag = generate_flag(session_id, created_by, authenticated_user)

        return jsonify({
            "status": "exploited",
            "hijack_detected": True,
            "operation": "verify_hijack",
            "session_id": session_id,
            "session_created_by": created_by,
            "authenticated_user": authenticated_user,
            "proof": "Session was created with attacker-controlled ID, then victim authenticated",
            "flag": flag,
            "timestamp": datetime.now().isoformat()
        })

    return jsonify({
        "status": "no_hijack",
        "hijack_detected": False,
        "session_id": session_id,
        "created_by": created_by,
        "authenticated_user": authenticated_user,
        "message": "No session fixation detected. Session was created by the authenticated user."
    })

@app.route('/reset', methods=['POST'])
def reset():
    """Reset all sessions and state"""
    conn = get_db()
    conn.execute('DELETE FROM sessions')
    conn.commit()
    conn.close()

    return jsonify({
        "status": "success",
        "message": "All sessions cleared",
        "timestamp": datetime.now().isoformat()
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
