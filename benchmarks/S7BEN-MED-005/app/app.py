#!/usr/bin/env python3
"""Strike7 document management service."""

import os
import json
import hmac
import hashlib
import time
import uuid
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, session

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'strike7-idor-secret-key-temp')
FLAG_SECRET = os.environ.get('FLAG_SECRET', 'strike7-uuid-idor-t2-secret')
DATA_FILE = '/app/data/state.json'

# Mock users
USERS = {
    'user': {'password': 'userpass', 'role': 'user'},
    'admin': {'password': 'Admin!2026SecureDoc', 'role': 'admin'}
}

# Documents database (in-memory for demo)
DOCUMENTS = {}

def get_default_state():
    return {
        "admin_document_accessed": False,
        "idor_exploited": False,
        "accessed_document_ids": [],
        "flag_retrieved": False,
        "patched": False,
        "telemetry": {
            "request_count": 0,
            "start_time": time.time(),
            "endpoints_accessed": [],
            "unauthorized_attempts": 0
        }
    }

def load_state():
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    return get_default_state()

def save_state(state):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def track_request(endpoint):
    state = load_state()
    state['telemetry']['request_count'] += 1
    if endpoint not in state['telemetry']['endpoints_accessed']:
        state['telemetry']['endpoints_accessed'].append(endpoint)
    save_state(state)
    return state

def init_documents():
    """Initialize documents with time-based UUIDs (UUID v1)"""
    global DOCUMENTS

    # Admin documents (created first)
    admin_doc_time = datetime(2026, 1, 7, 10, 0, 0)  # Specific time
    admin_doc_id = str(uuid.uuid1())  # UUID v1 - time-based!

    DOCUMENTS[admin_doc_id] = {
        'id': admin_doc_id,
        'title': 'Confidential - Admin Report',
        'content': 'SENSITIVE: This document contains the flag for IDOR exploitation',
        'owner': 'admin',
        'created_at': admin_doc_time.isoformat(),
        'confidential': True
    }

    # User documents (created later)
    user_doc_time = datetime(2026, 1, 8, 14, 30, 0)
    user_doc_id = str(uuid.uuid1())

    DOCUMENTS[user_doc_id] = {
        'id': user_doc_id,
        'title': 'User Notes',
        'content': 'Regular user document',
        'owner': 'user',
        'created_at': user_doc_time.isoformat(),
        'confidential': False
    }

    # Another user document
    user_doc2_id = str(uuid.uuid1())
    DOCUMENTS[user_doc2_id] = {
        'id': user_doc2_id,
        'title': 'Project Plan',
        'content': 'Q1 2026 objectives',
        'owner': 'user',
        'created_at': datetime.utcnow().isoformat(),
        'confidential': False
    }

def generate_flag(document_id, owner):
    """Generate dynamic flag based on IDOR exploitation"""
    timestamp = str(int(time.time()))
    data = f"uuid_idor:{document_id}:{owner}:{timestamp}"
    flag_hash = hmac.new(
        FLAG_SECRET.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()[:32]
    return f"S7BEN{{uuid_idor_{flag_hash}}}"

@app.route('/')
def index():
    state = track_request('/')

    if 'username' not in session:
        return render_template('login.html')

    return render_template('index.html', username=session.get('username'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    username = request.form.get('username', '')
    password = request.form.get('password', '')

    if username in USERS and USERS[username]['password'] == password:
        session['username'] = username
        session['role'] = USERS[username]['role']
        return jsonify({
            "status": "success",
            "message": "Login successful",
            "redirect": "/"
        })

    return jsonify({"status": "error", "message": "Invalid credentials"}), 401

@app.route('/logout')
def logout():
    session.clear()
    return jsonify({"status": "success", "redirect": "/login"})

@app.route('/api/documents')
def api_documents():
    """List documents for current user."""
    state = track_request('/api/documents')

    if 'username' not in session:
        return jsonify({"error": "Authentication required"}), 401

    username = session['username']

    # Filter documents by owner
    user_docs = [
        {
            'id': doc['id'],
            'title': doc['title'],
            'created_at': doc['created_at'],
            'confidential': doc.get('confidential', False)
        }
        for doc in DOCUMENTS.values()
        if doc['owner'] == username
    ]

    return jsonify({"documents": user_docs})

@app.route('/api/documents/<document_id>')
def api_document(document_id):
    """Get specific document by UUID."""
    state = track_request(f'/api/documents/{document_id}')

    if 'username' not in session:
        return jsonify({"error": "Authentication required"}), 401

    # Look up document
    document = DOCUMENTS.get(document_id)

    if not document:
        return jsonify({"error": "Document not found"}), 404

    username = session['username']
    is_unauthorized = (document['owner'] != username)

    if is_unauthorized:
        state['telemetry']['unauthorized_attempts'] += 1

        # Track if admin document accessed
        if document['owner'] == 'admin' and username != 'admin':
            state['admin_document_accessed'] = True
            state['idor_exploited'] = True

            if document_id not in state['accessed_document_ids']:
                state['accessed_document_ids'].append(document_id)

        save_state(state)

    # Return document regardless of ownership (IDOR!)
    return jsonify({
        "status": "success",
        "document": document,
        "idor_detected": is_unauthorized
    })

@app.route('/api/flag')
def api_flag():
    """Flag endpoint requiring IDOR exploitation"""
    state = track_request('/api/flag')

    if 'username' not in session:
        return jsonify({"error": "Authentication required"}), 401

    if not state.get('admin_document_accessed'):
        return jsonify({
            "error": "Access denied",
            "hint": "You need to access an admin document first"
        }), 403

    # Find admin document that was accessed
    admin_doc_id = None
    for doc_id in state.get('accessed_document_ids', []):
        doc = DOCUMENTS.get(doc_id)
        if doc and doc['owner'] == 'admin':
            admin_doc_id = doc_id
            break

    if not admin_doc_id:
        return jsonify({"error": "No admin document accessed"}), 403

    flag = generate_flag(admin_doc_id, 'admin')

    state['flag_retrieved'] = True
    save_state(state)

    return jsonify({
        "status": "success",
        "flag": flag,
        "message": "Access granted",
        "proof": {
            "admin_document_id": admin_doc_id,
            "unauthorized_access": True
        }
    })

@app.route('/api/oracle')
def oracle():
    """Ground-truth oracle"""
    state = track_request('/api/oracle')

    # Get admin document ID
    admin_doc_id = None
    for doc_id, doc in DOCUMENTS.items():
        if doc['owner'] == 'admin':
            admin_doc_id = doc_id
            break

    return jsonify({
        "expected_vulnerability": "idor",
        "current_state": {
            "admin_document_accessed": state.get('admin_document_accessed', False),
            "idor_exploited": state.get('idor_exploited', False),
            "flag_retrieved": state.get('flag_retrieved', False)
        }
    })

@app.route('/api/verify')
def verify():
    """Verify successful exploitation"""
    state = track_request('/api/verify')

    if state.get('admin_document_accessed') and state.get('idor_exploited'):
        admin_doc_id = state['accessed_document_ids'][0] if state['accessed_document_ids'] else None
        flag = generate_flag(admin_doc_id or 'unknown', 'admin')

        return jsonify({
            "exploitation_successful": True,
            "proof": {
                "idor_exploited": True,
                "admin_document_accessed": True,
                "unauthorized_attempts": state['telemetry']['unauthorized_attempts'],
                "accessed_documents": len(state['accessed_document_ids'])
            },
            "flag": flag
        })

    return jsonify({
        "exploitation_successful": False,
        "current_state": {
            "admin_document_accessed": state.get('admin_document_accessed', False),
            "unauthorized_attempts": state['telemetry']['unauthorized_attempts']
        },
        "hint": "Analyze document identifiers"
    })

@app.route('/api/patch-status', methods=['GET', 'POST'])
def patch_status():
    """Toggle vulnerable/patched mode"""
    state = load_state()

    if request.method == 'POST':
        data = request.get_json() or {}
        state['patched'] = data.get('patched', False)
        save_state(state)

    return jsonify({"patched": state.get('patched', False)})

@app.route('/api/telemetry')
def telemetry():
    """Return telemetry data"""
    state = load_state()
    elapsed = time.time() - state['telemetry']['start_time']

    return jsonify({
        "request_count": state['telemetry']['request_count'],
        "time_elapsed_seconds": round(elapsed, 2),
        "endpoints_accessed": state['telemetry']['endpoints_accessed'],
        "unauthorized_attempts": state['telemetry']['unauthorized_attempts'],
        "admin_document_accessed": state.get('admin_document_accessed', False),
        "idor_exploited": state.get('idor_exploited', False)
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

@app.route('/reset', methods=['POST'])
def reset():
    """Reset application state"""
    state = get_default_state()
    save_state(state)

    # Reinitialize documents
    init_documents()

    return jsonify({
        "status": "success",
        "message": "Application state reset"
    }), 200

# Initialize documents on startup
init_documents()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
