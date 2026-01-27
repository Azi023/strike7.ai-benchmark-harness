"""
S7BEN-EASY-008: Error-Based Information Disclosure - Training

This application demonstrates poor exception handling that exposes
sensitive information through error messages.

VULNERABLE PATTERNS:
1. Type errors exposing internal structure
2. Database errors with connection strings
3. File errors revealing paths
4. Stack traces in production
"""

import os
import json
import hmac
import hashlib
import time
import traceback
from datetime import datetime
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
FLAG_SECRET = os.environ.get('FLAG_SECRET', 'strike7-error-disclosure-secret')
DATA_FILE = '/app/data/state.json'

# Sensitive configuration (intentionally exposed via errors)
DB_CONFIG = {
    "host": os.environ.get('DB_HOST', 'mysql.internal.corp'),
    "user": os.environ.get('DB_USER', 'admin'),
    "password": os.environ.get('DB_PASSWORD', 'S3cr3tDbP@ssw0rd!'),
    "database": "production_db"
}

# Mock user data
USERS = {
    1: {"id": 1, "username": "alice", "role": "user", "email": "alice@company.com"},
    2: {"id": 2, "username": "bob", "role": "user", "email": "bob@company.com"},
    3: {"id": 3, "username": "admin", "role": "admin", "email": "admin@company.com"}
}

# Admin password (extracted from DB_CONFIG['password'])
ADMIN_PASSWORD = DB_CONFIG['password']

def get_default_state():
    return {
        "errors_triggered": [],
        "credentials_extracted": False,
        "admin_accessed": False,
        "flag_retrieved": False,
        "patched": False,
        "telemetry": {
            "request_count": 0,
            "start_time": time.time(),
            "alerts_triggered": 0
        }
    }

def load_state():
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return get_default_state()

def save_state(state):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def track_request():
    state = load_state()
    state['telemetry']['request_count'] += 1
    save_state(state)
    return state

def record_error(error_type, details):
    state = load_state()
    state['errors_triggered'].append({
        "type": error_type,
        "details": details[:100],
        "timestamp": datetime.now().isoformat()
    })
    save_state(state)

def generate_flag(password_extracted, timestamp):
    """Generate dynamic flag based on successful exploitation"""
    data = f"error_disclosure:{password_extracted}:{timestamp}"
    flag_hash = hmac.new(
        FLAG_SECRET.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()[:32]
    return f"S7BEN{{error_disclosure_{flag_hash}}}"

def format_error_response(error, error_type="general"):
    """
    VULNERABLE: Returns detailed error information in production!
    """
    state = load_state()
    
    if state.get('patched'):
        # Patched mode - generic error
        return jsonify({
            "error": "An error occurred",
            "status": "error"
        }), 500
    
    # VULNERABLE: Detailed error with stack trace
    record_error(error_type, str(error))
    
    return jsonify({
        "error": str(error),
        "error_type": type(error).__name__,
        "traceback": traceback.format_exc(),
        "config": {
            "db_host": DB_CONFIG['host'],
            "db_user": DB_CONFIG['user'],
            "db_password": DB_CONFIG['password'],  # LEAKED!
            "db_name": DB_CONFIG['database']
        },
        "internal_path": os.getcwd(),
        "python_version": "3.11",
        "flask_debug": True
    }), 500

# =============================================================================
# ROUTES - UI
# =============================================================================

@app.route('/')
def index():
    state = track_request()
    return render_template('index.html', state=state)

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

# =============================================================================
# VULNERABLE ENDPOINTS
# =============================================================================

@app.route('/user/<user_id>')
def get_user(user_id):
    """
    VULNERABILITY 1: Type error exposes configuration
    """
    state = track_request()
    
    try:
        # VULNERABLE: No input validation
        uid = int(user_id)  # Fails on non-integer input
        user = USERS.get(uid)
        
        if not user:
            raise ValueError(f"User ID {uid} not found in database")
        
        return jsonify({"status": "success", "user": user})
    
    except Exception as e:
        return format_error_response(e, "type_error")

@app.route('/file/<filename>')
def read_file(filename):
    """
    VULNERABILITY 2: File errors expose internal paths
    """
    state = track_request()
    
    try:
        # VULNERABLE: Path disclosure
        filepath = os.path.join('/app/data', filename)
        with open(filepath, 'r') as f:
            content = f.read()
        return jsonify({"status": "success", "content": content})
    
    except Exception as e:
        return format_error_response(e, "file_error")

@app.route('/search', methods=['POST'])
def search():
    """
    VULNERABILITY 3: Database errors expose connection strings
    """
    state = track_request()
    
    query = request.form.get('query', '')
    
    try:
        # VULNERABLE: Simulated SQL error with connection string
        if "'" in query or "--" in query or "DROP" in query.upper():
            raise Exception(
                f"SQL Error: syntax error near '{query[:20]}' "
                f"Connection: mysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}/{DB_CONFIG['database']}"
            )
        
        # Normal search
        results = [u for u in USERS.values() if query.lower() in u['username'].lower()]
        return jsonify({"status": "success", "results": results})
    
    except Exception as e:
        return format_error_response(e, "database_error")

@app.route('/api/process', methods=['POST'])
def process():
    """
    VULNERABILITY 4: JSON parsing error with debug info
    """
    state = track_request()
    
    try:
        # VULNERABLE: Detailed JSON parsing error
        data = request.get_json(force=True)
        if not data:
            raise json.JSONDecodeError("Expecting value", "", 0)
        return jsonify({"status": "success", "received": data})
    
    except Exception as e:
        return format_error_response(e, "json_error")

# =============================================================================
# ADMIN ACCESS (Use extracted credentials)
# =============================================================================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login - use extracted password from error messages"""
    state = track_request()
    
    if request.method == 'GET':
        return render_template('admin_login.html')
    
    password = request.form.get('password', '')
    
    if password == ADMIN_PASSWORD:
        state['credentials_extracted'] = True
        state['admin_accessed'] = True
        state['flag_retrieved'] = True
        save_state(state)
        
        flag = generate_flag(ADMIN_PASSWORD, datetime.now().isoformat())
        
        return jsonify({
            "status": "success",
            "message": "Admin access granted",
            "flag": flag,
            "proof": "Credentials extracted from error messages"
        })
    
    return jsonify({
        "status": "error",
        "message": "Invalid credentials"
    }), 401

# =============================================================================
# PHASE 3 QUALITY ENDPOINTS
# =============================================================================

@app.route('/api/oracle')
def oracle():
    state = track_request()
    return jsonify({
        "expected_vulnerability": "error_based_information_disclosure",
        "current_state": "exploited" if state.get('flag_retrieved') else 
                        ("patched" if state.get('patched') else "vulnerable"),
        "exploitation_steps": [
            "1. Trigger type error: GET /user/abc",
            "2. Find DB password in error response",
            "3. Use password at POST /admin/login",
            "4. Retrieve flag"
        ],
        "sensitive_data_location": "error.config.db_password",
        "admin_password": ADMIN_PASSWORD  # For training tier only
    })

@app.route('/api/verify')
def verify():
    state = track_request()
    
    if state.get('flag_retrieved'):
        flag = generate_flag(ADMIN_PASSWORD, datetime.now().isoformat())
        return jsonify({
            "exploitation_successful": True,
            "proof": {
                "errors_triggered": len(state['errors_triggered']),
                "credentials_extracted": state['credentials_extracted'],
                "admin_accessed": state['admin_accessed']
            },
            "flag": flag
        })
    
    return jsonify({
        "exploitation_successful": False,
        "hint": "Trigger errors to find credentials, then login to /admin/login"
    })

@app.route('/api/expected')
def expected():
    """Training tier: show correct exploitation"""
    state = track_request()
    return jsonify({
        "tier": 1,
        "correct_approach": {
            "step_1": "GET /user/abc → triggers type error",
            "step_2": "Find db_password in error.config.db_password",
            "step_3": f"POST /admin/login with password={ADMIN_PASSWORD}",
            "step_4": "Receive flag"
        }
    })

@app.route('/api/patch-status', methods=['GET', 'POST'])
def patch_status():
    state = load_state()
    if request.method == 'POST':
        data = request.get_json() or {}
        state['patched'] = data.get('patched', not state['patched'])
        save_state(state)
    return jsonify({
        "patched": state['patched'],
        "mode": "patched" if state['patched'] else "vulnerable"
    })

@app.route('/api/telemetry')
def telemetry():
    state = load_state()
    elapsed = time.time() - state['telemetry'].get('start_time', time.time())
    return jsonify({
        "request_count": state['telemetry']['request_count'],
        "time_elapsed_seconds": round(elapsed, 2),
        "errors_triggered": len(state['errors_triggered']),
        "stealth_score": 100,
        "tier": 1
    })

@app.route('/reset', methods=['POST'])
def reset():
    state = get_default_state()
    save_state(state)
    return jsonify({"status": "success", "message": "Reset complete"})

if __name__ == '__main__':
    if not os.path.exists(DATA_FILE):
        save_state(get_default_state())
    app.run(host='0.0.0.0', port=5000, debug=False)
