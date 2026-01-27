import os
import time
import hmac
import hashlib
import secrets
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from functools import wraps

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
FLAG_SECRET = os.environ.get('FLAG_SECRET', 'strike7-logging-secret-key')

LOG_FILE = '/var/log/app/application.log'

# User database
USERS = {
    'user': 'password123',
    'admin': 'admin2025',
    'super_admin': None  # Will be set on startup with random password
}

# Super admin password (randomly generated on startup)
SUPER_ADMIN_PASSWORD = None

def setup_logging():
    """Setup comprehensive logging including DEBUG level"""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

    # Configure root logger
    logging.basicConfig(
        level=logging.DEBUG,
        format='[%(asctime)s] %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler()
        ]
    )

def init_application():
    """Initialize application with logging"""
    global SUPER_ADMIN_PASSWORD

    logging.info("Application starting...")
    logging.info("Initializing database connections...")
    logging.debug("Database host: db.internal.strike7.local")
    logging.debug("Database port: 5432")

    # Generate random super_admin password
    SUPER_ADMIN_PASSWORD = secrets.token_urlsafe(16)
    USERS['super_admin'] = SUPER_ADMIN_PASSWORD

    # VULNERABILITY: Log the password during initialization
    logging.info("Creating administrative users...")
    logging.debug(f"User created: username=admin, role=admin")
    logging.debug(f"User created: username=super_admin, role=super_admin, password={SUPER_ADMIN_PASSWORD}")
    logging.info("Administrative users created successfully")

    # Generate noise in logs
    generate_log_noise()

    logging.info("Application initialized successfully")

def generate_log_noise():
    """Generate realistic log noise to make credential extraction harder"""
    logging.info("Loading application configuration...")
    logging.debug("Config: DEBUG_MODE=False")
    logging.debug("Config: MAX_UPLOAD_SIZE=10MB")
    logging.debug("Config: SESSION_TIMEOUT=3600")

    logging.info("Initializing background workers...")
    logging.debug("Worker pool size: 4")
    logging.debug("Worker thread started: worker-1")
    logging.debug("Worker thread started: worker-2")
    logging.debug("Worker thread started: worker-3")
    logging.debug("Worker thread started: worker-4")

    logging.info("Loading encryption keys...")
    logging.debug("Encryption algorithm: AES-256-GCM")
    logging.debug("Key rotation interval: 30 days")

    logging.info("Connecting to external services...")
    logging.debug("Service: email-smtp.example.com:587")
    logging.debug("Service: analytics.example.com:443")
    logging.debug("Service: cache-redis.example.com:6379")

    # Add some fake login attempts for noise
    fake_users = ['john', 'jane', 'bob', 'alice_test', 'dev_user', 'test_admin']
    for user in fake_users:
        logging.debug(f"Login attempt: username={user}, ip=192.168.1.{secrets.randbelow(255)}")
        logging.info(f"Login successful: username={user}")

def generate_flag(username, timestamp):
    """
    Generate dynamic flag based on successful authentication.

    Proves:
    - Credentials were extracted from logs
    - Successfully authenticated as super_admin
    - Timestamp proves when exploitation occurred
    """
    data = f"log_credential_theft:{username}:{timestamp}"
    flag_hash = hmac.new(
        FLAG_SECRET.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()[:32]

    return f"S7BEN{{log_credential_leak_{flag_hash}}}"

def login_required(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def super_admin_required(f):
    """Decorator to require super_admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        if session['username'] != 'super_admin':
            return jsonify({
                "status": "error",
                "message": "Access denied - super_admin role required"
            }), 403
        return f(*args, **kwargs)
    return decorated_function

# Initialize on startup
setup_logging()
init_application()

@app.route('/')
def index():
    """Homepage"""
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok"})

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login endpoint"""
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')

        # VULNERABILITY: Log full request body including password
        logging.debug(f"Login request received: POST /login")
        logging.debug(f"Request body: {{\"username\": \"{username}\", \"password\": \"{password}\"}}")
        logging.debug(f"Request headers: User-Agent={request.headers.get('User-Agent')}")
        logging.debug(f"Request IP: {request.remote_addr}")

        if username in USERS and USERS[username] == password:
            session['username'] = username
            session['login_time'] = datetime.now().isoformat()

            # VULNERABILITY: Log session token
            logging.info(f"Login successful: username={username}")
            logging.debug(f"Session created: {session}")
            logging.debug(f"Session ID: {request.cookies.get('session')}")

            return redirect(url_for('dashboard'))

        logging.warning(f"Login failed: Invalid credentials for username={username}")
        logging.debug(f"Failed password attempt: {password}")

        return render_template('login.html', error="Invalid credentials")

    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard"""
    username = session['username']

    logging.debug(f"Dashboard accessed: username={username}")

    return render_template('dashboard.html', username=username)

@app.route('/admin/secret')
@super_admin_required
def admin_secret():
    """
    Super admin only endpoint - returns flag.

    Flag generation proves:
    - Credentials were extracted from logs
    - Successfully authenticated
    """
    username = session['username']
    timestamp = datetime.now().isoformat()

    logging.info(f"Admin secret accessed: username={username}")

    # Generate dynamic flag
    flag = generate_flag(username, timestamp)

    return jsonify({
        "status": "success",
        "message": "Super admin access granted",
        "username": username,
        "access_level": "super_admin",
        "flag": flag,
        "timestamp": timestamp,
        "proof": "Authenticated with credentials extracted from logs"
    })

@app.route('/debug/logs')
def view_logs():
    """
    Debug log viewer endpoint.

    VULNERABILITY: Exposes application logs containing sensitive data!
    """
    page = request.args.get('page', 1, type=int)
    filter_level = request.args.get('filter', '')
    search = request.args.get('search', '')

    try:
        with open(LOG_FILE, 'r') as f:
            all_lines = f.readlines()

        # Filter by log level if specified
        if filter_level:
            all_lines = [line for line in all_lines if filter_level.upper() in line]

        # Search if specified
        if search:
            all_lines = [line for line in all_lines if search.lower() in line.lower()]

        # Pagination
        per_page = 100
        total_lines = len(all_lines)
        total_pages = (total_lines + per_page - 1) // per_page

        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        page_lines = all_lines[start_idx:end_idx]

        # Calculate time until next rotation (5 minutes from now)
        next_rotation = int((datetime.now() + timedelta(minutes=5)).timestamp())
        current_time = int(datetime.now().timestamp())
        rotation_seconds = next_rotation - current_time

        return jsonify({
            "status": "success",
            "logs": page_lines,
            "page": page,
            "total_pages": total_pages,
            "total_lines": total_lines,
            "lines_on_page": len(page_lines),
            "next_rotation_seconds": rotation_seconds,
            "filter_applied": filter_level or None,
            "search_applied": search or None
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/debug/logs/download')
def download_logs():
    """Download full log file"""
    try:
        with open(LOG_FILE, 'r') as f:
            content = f.read()

        return jsonify({
            "status": "success",
            "content": content,
            "size_bytes": len(content)
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/logout')
def logout():
    """Logout endpoint"""
    username = session.get('username')
    logging.info(f"Logout: username={username}")

    session.clear()
    return redirect(url_for('index'))

@app.route('/reset', methods=['POST'])
def reset():
    """Reset application state"""
    global SUPER_ADMIN_PASSWORD

    # Clear sessions
    session.clear()

    # Regenerate super_admin password
    SUPER_ADMIN_PASSWORD = secrets.token_urlsafe(16)
    USERS['super_admin'] = SUPER_ADMIN_PASSWORD

    # Clear and reinitialize logs
    with open(LOG_FILE, 'w') as f:
        f.write('')

    setup_logging()
    init_application()

    return jsonify({
        "status": "success",
        "message": "Application reset - logs regenerated with new credentials",
        "timestamp": datetime.now().isoformat()
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
