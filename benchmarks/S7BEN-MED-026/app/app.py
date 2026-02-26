import json
import os
import sqlite3
import subprocess
import re

from flask import Flask, request, session, jsonify, render_template, redirect, url_for, g
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.urandom(32)

DB_PATH = '/tmp/packageforge.db'
PATCH_STATUS_FILE = '/tmp/patch_status.json'


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exc):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    """Create tables and seed data if the database doesn't exist yet."""
    if os.path.exists(DB_PATH):
        return
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.executescript('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'developer'
        );

        CREATE TABLE packages (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            owner_id INTEGER REFERENCES users(id),
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE versions (
            id INTEGER PRIMARY KEY,
            package_id INTEGER REFERENCES packages(id),
            version TEXT NOT NULL,
            description TEXT,
            scripts TEXT,
            published_by INTEGER REFERENCES users(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(package_id, version)
        );

        CREATE TABLE builds (
            id INTEGER PRIMARY KEY,
            requested_by INTEGER REFERENCES users(id),
            packages TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            log TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')

    # Seed users
    admin_hash = generate_password_hash('S7adminSecret!2026')
    demo_hash = generate_password_hash('demo2026')
    db.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
               ('admin', admin_hash, 'admin'))
    db.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
               ('demo', demo_hash, 'developer'))

    # Seed packages (all owned by admin, id=1)
    db.execute("INSERT INTO packages (name, owner_id, description) VALUES (?, ?, ?)",
               ('forge-core', 1, 'Core platform library for internal services'))
    db.execute("INSERT INTO packages (name, owner_id, description) VALUES (?, ?, ?)",
               ('forge-auth', 1, 'Authentication and session management module'))
    db.execute("INSERT INTO packages (name, owner_id, description) VALUES (?, ?, ?)",
               ('forge-utils', 1, 'Shared utility functions and helpers'))

    # Seed versions
    db.execute("INSERT INTO versions (package_id, version, description, scripts, published_by) VALUES (?, ?, ?, ?, ?)",
               (1, '1.0.0', 'Initial stable release', json.dumps({"postinstall": "echo 'Core library initialized'"}), 1))
    db.execute("INSERT INTO versions (package_id, version, description, scripts, published_by) VALUES (?, ?, ?, ?, ?)",
               (2, '2.1.0', 'Added token refresh support', json.dumps({"postinstall": "echo 'Auth module configured'"}), 1))
    db.execute("INSERT INTO versions (package_id, version, description, scripts, published_by) VALUES (?, ?, ?, ?, ?)",
               (3, '1.3.2', 'Bug fixes and performance improvements', json.dumps({}), 1))

    db.commit()
    db.close()


# ---------------------------------------------------------------------------
# Patch mode
# ---------------------------------------------------------------------------

def is_patched():
    try:
        with open(PATCH_STATUS_FILE, 'r') as f:
            return json.load(f).get('patched', False)
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({"error": "Authentication required"}), 401
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated


def get_current_user():
    db = get_db()
    return db.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],)).fetchone()


# ---------------------------------------------------------------------------
# Semver comparison helper
# ---------------------------------------------------------------------------

def version_tuple(v):
    """Parse version string into sortable tuple."""
    parts = re.split(r'[.\-]', v)
    result = []
    for p in parts:
        try:
            result.append(int(p))
        except ValueError:
            result.append(p)
    return tuple(result)


# ---------------------------------------------------------------------------
# Public routes
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login')
def login_page():
    return render_template('login.html')


@app.route('/docs')
def docs_page():
    return render_template('docs.html')


@app.route('/health')
def health():
    return jsonify({"status": "healthy", "service": "packageforge-app"})


@app.route('/api/patch-status', methods=['GET', 'POST'])
def patch_status():
    if request.method == 'POST':
        data = request.get_json(force=True)
        patched = data.get('patched', False)
        with open(PATCH_STATUS_FILE, 'w') as f:
            json.dump({"patched": bool(patched)}, f)
        return jsonify({"patched": bool(patched)})
    return jsonify({"patched": is_patched()})


# ---------------------------------------------------------------------------
# Auth endpoints
# ---------------------------------------------------------------------------

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json(force=True)
    username = data.get('username', '')
    password = data.get('password', '')

    db = get_db()
    user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

    if user and check_password_hash(user['password_hash'], password):
        session['user_id'] = user['id']
        session['username'] = user['username']
        return jsonify({"message": "Login successful", "username": user['username'], "role": user['role']})

    return jsonify({"error": "Invalid credentials"}), 401


@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({"message": "Logged out"})


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@app.route('/dashboard')
@login_required
def dashboard():
    db = get_db()
    packages = db.execute('''
        SELECT p.name, p.description, u.username as owner,
               (SELECT v.version FROM versions v WHERE v.package_id = p.id ORDER BY v.created_at DESC LIMIT 1) as latest_version
        FROM packages p JOIN users u ON p.owner_id = u.id
    ''').fetchall()
    return render_template('docs.html', packages=packages, logged_in=True)


# ---------------------------------------------------------------------------
# Package endpoints
# ---------------------------------------------------------------------------

@app.route('/api/packages')
@login_required
def list_packages():
    db = get_db()
    packages = db.execute('''
        SELECT p.name, p.description, u.username as owner,
               (SELECT v.version FROM versions v WHERE v.package_id = p.id ORDER BY v.created_at DESC LIMIT 1) as latest_version
        FROM packages p JOIN users u ON p.owner_id = u.id
    ''').fetchall()
    return jsonify([dict(row) for row in packages])


@app.route('/api/packages/<name>')
@login_required
def get_package(name):
    db = get_db()
    pkg = db.execute('''
        SELECT p.*, u.username as owner FROM packages p
        JOIN users u ON p.owner_id = u.id WHERE p.name = ?
    ''', (name,)).fetchone()

    if not pkg:
        return jsonify({"error": "Package not found"}), 404

    versions = db.execute('''
        SELECT v.version, v.description, v.scripts, u.username as published_by, v.created_at
        FROM versions v JOIN users u ON v.published_by = u.id
        WHERE v.package_id = ? ORDER BY v.created_at DESC
    ''', (pkg['id'],)).fetchall()

    version_list = []
    for v in versions:
        vd = dict(v)
        vd['scripts'] = json.loads(vd['scripts']) if vd['scripts'] else {}
        version_list.append(vd)

    return jsonify({
        "name": pkg['name'],
        "owner": pkg['owner'],
        "description": pkg['description'],
        "versions": version_list
    })


@app.route('/api/packages/<name>/versions', methods=['POST'])
@login_required
def publish_version(name):
    db = get_db()
    pkg = db.execute("SELECT * FROM packages WHERE name = ?", (name,)).fetchone()
    if not pkg:
        return jsonify({"error": "Package not found"}), 404

    # VULNERABILITY: No ownership check in unpatched mode
    if is_patched():
        if pkg['owner_id'] != session['user_id']:
            return jsonify({"error": "Not authorized to publish versions for this package"}), 403

    data = request.get_json(force=True)
    version = data.get('version', '')
    description = data.get('description', '')
    scripts = data.get('scripts', {})

    if not version:
        return jsonify({"error": "Version is required"}), 400

    # Check version format
    if not re.match(r'^\d+\.\d+\.\d+$', version):
        return jsonify({"error": "Version must follow semver format (e.g., 1.0.1)"}), 400

    # Check for duplicate version
    existing = db.execute(
        "SELECT id FROM versions WHERE package_id = ? AND version = ?",
        (pkg['id'], version)
    ).fetchone()
    if existing:
        return jsonify({"error": "Version already exists"}), 409

    db.execute(
        "INSERT INTO versions (package_id, version, description, scripts, published_by) VALUES (?, ?, ?, ?, ?)",
        (pkg['id'], version, description, json.dumps(scripts), session['user_id'])
    )
    db.commit()

    return jsonify({"message": f"Version {version} published for {name}", "version": version}), 201


# ---------------------------------------------------------------------------
# Build endpoints
# ---------------------------------------------------------------------------

@app.route('/api/builds', methods=['GET', 'POST'])
@login_required
def builds():
    db = get_db()

    if request.method == 'POST':
        data = request.get_json(force=True)
        package_names = data.get('packages', [])

        if not package_names or not isinstance(package_names, list):
            return jsonify({"error": "packages must be a non-empty array"}), 400

        # Verify all packages exist
        for pname in package_names:
            pkg = db.execute("SELECT id FROM packages WHERE name = ?", (pname,)).fetchone()
            if not pkg:
                return jsonify({"error": f"Package '{pname}' not found"}), 404

        # Create build record
        db.execute(
            "INSERT INTO builds (requested_by, packages, status) VALUES (?, ?, ?)",
            (session['user_id'], json.dumps(package_names), 'running')
        )
        db.commit()
        build_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]

        # Run build synchronously
        log_lines = []
        for pname in package_names:
            pkg = db.execute("SELECT id FROM packages WHERE name = ?", (pname,)).fetchone()

            # Find latest version
            versions = db.execute(
                "SELECT version, scripts FROM versions WHERE package_id = ? ORDER BY created_at DESC",
                (pkg['id'],)
            ).fetchall()

            if not versions:
                log_lines.append(f"No versions found for {pname}, skipping.")
                continue

            # Sort by semver and pick latest
            sorted_versions = sorted(versions, key=lambda v: version_tuple(v['version']), reverse=True)
            latest = sorted_versions[0]
            ver = latest['version']
            scripts = json.loads(latest['scripts']) if latest['scripts'] else {}

            log_lines.append(f"Installing {pname}@{ver}...")

            if scripts.get('postinstall'):
                log_lines.append("Running postinstall script...")
                try:
                    result = subprocess.run(
                        scripts['postinstall'],
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.stdout.strip():
                        log_lines.append(result.stdout.strip())
                    if result.stderr.strip():
                        log_lines.append(f"Warning: {result.stderr.strip()}")
                except subprocess.TimeoutExpired:
                    log_lines.append("Warning: Script timed out after 5 seconds")
                except Exception as e:
                    log_lines.append(f"Warning: Script error - {str(e)}")

        log_lines.append("Build completed.")

        db.execute(
            "UPDATE builds SET status = 'completed', log = ? WHERE id = ?",
            ('\n'.join(log_lines), build_id)
        )
        db.commit()

        return jsonify({"message": "Build completed", "build_id": build_id}), 201

    # GET - list builds for current user
    user_builds = db.execute(
        "SELECT id, packages, status, created_at FROM builds WHERE requested_by = ? ORDER BY created_at DESC",
        (session['user_id'],)
    ).fetchall()
    return jsonify([dict(b) for b in user_builds])


@app.route('/api/builds/<int:build_id>')
@login_required
def get_build(build_id):
    db = get_db()
    build = db.execute("SELECT * FROM builds WHERE id = ?", (build_id,)).fetchone()

    if not build:
        return jsonify({"error": "Build not found"}), 404

    result = dict(build)
    result['packages'] = json.loads(result['packages'])
    return jsonify(result)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
