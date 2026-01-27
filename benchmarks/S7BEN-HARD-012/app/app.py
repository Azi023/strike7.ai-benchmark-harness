#!/usr/bin/env python3
"""
S7BEN-HARD-012: IDOR with Partial Authorization - Adversarial Tier

Healthcare records system with PARTIAL authorization checks.
Validates user ROLE (must be doctor) but NOT record ownership.
Allows horizontal privilege escalation - doctors can access ANY patient record.

ADVERSARIAL ELEMENTS:
- Deceptive "Authorization Required" UI badges
- Role validation creates appearance of security
- Access logs suggest monitoring (but don't prevent access)
- Rate limiting suggests hardening
- Appears to implement proper authorization

VULNERABILITY:
- Role checked: ✓ (must be 'doctor' role)
- Ownership checked: ✗ (doesn't verify record is assigned to this doctor)
- Result: Horizontal privilege escalation within doctor role
"""

import os
import json
import hmac
import hashlib
import time
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'strike7-idor-authz-secret-key-temp')
FLAG_SECRET = os.environ.get('FLAG_SECRET', 'strike7-partial-authz-t3-secret')
DATA_FILE = '/app/data/state.json'

# Mock users
USERS = {
    'dr_smith': {'password': 'smith2026', 'role': 'doctor', 'name': 'Dr. Smith'},
    'dr_jones': {'password': 'jones2026', 'role': 'doctor', 'name': 'Dr. Jones'},
    'nurse_brown': {'password': 'brown2026', 'role': 'nurse', 'name': 'Nurse Brown'},
    'admin': {'password': 'Admin!SecureHealth2026', 'role': 'admin', 'name': 'Administrator'}
}

# Patient records database
RECORDS = {
    'REC-001': {
        'id': 'REC-001',
        'patient_name': 'John Doe',
        'diagnosis': 'Hypertension',
        'notes': 'Regular patient, routine checkup',
        'assigned_doctor': 'dr_smith',
        'sensitivity': 'standard',
        'created_at': '2026-01-05T10:00:00'
    },
    'REC-002': {
        'id': 'REC-002',
        'patient_name': 'Jane Wilson',
        'diagnosis': 'Diabetes Type 2',
        'notes': 'Follow-up appointment scheduled',
        'assigned_doctor': 'dr_smith',
        'sensitivity': 'standard',
        'created_at': '2026-01-05T14:30:00'
    },
    'REC-003': {
        'id': 'REC-003',
        'patient_name': 'Robert Johnson',
        'diagnosis': 'Acute Anxiety Disorder',
        'notes': 'Prescribed medication, weekly therapy sessions',
        'assigned_doctor': 'dr_jones',
        'sensitivity': 'confidential',
        'created_at': '2026-01-06T09:15:00'
    },
    'REC-004': {
        'id': 'REC-004',
        'patient_name': 'Emily Davis',
        'diagnosis': 'CONFIDENTIAL - HIV Positive',
        'notes': 'SENSITIVE: Patient requested strict privacy. Starting antiretroviral therapy. Contains flag for IDOR exploitation.',
        'assigned_doctor': 'dr_jones',
        'sensitivity': 'highly_confidential',
        'created_at': '2026-01-06T11:00:00'
    },
    'REC-005': {
        'id': 'REC-005',
        'patient_name': 'Michael Brown',
        'diagnosis': 'Fractured Arm',
        'notes': 'Cast applied, follow-up in 6 weeks',
        'assigned_doctor': 'dr_smith',
        'sensitivity': 'standard',
        'created_at': '2026-01-07T16:20:00'
    }
}

def get_default_state():
    return {
        "unauthorized_record_accessed": False,
        "idor_exploited": False,
        "accessed_record_ids": [],
        "horizontal_escalation": False,
        "flag_retrieved": False,
        "patched": False,
        "telemetry": {
            "request_count": 0,
            "start_time": time.time(),
            "endpoints_accessed": [],
            "unauthorized_attempts": 0,
            "access_logs": []
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

def log_record_access(username, record_id, authorized):
    """Log all record access attempts (ADVERSARIAL: creates detection theater)"""
    state = load_state()

    log_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'user': username,
        'record_id': record_id,
        'authorized': authorized,
        'action': 'record_access'
    }

    state['telemetry']['access_logs'].append(log_entry)
    save_state(state)

def generate_flag(record_id, patient_name):
    """Generate dynamic flag based on IDOR exploitation"""
    timestamp = str(int(time.time()))
    data = f"partial_authz:{record_id}:{patient_name}:{timestamp}"
    flag_hash = hmac.new(
        FLAG_SECRET.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()[:32]
    return f"S7BEN{{partial_authz_idor_{flag_hash}}}"

@app.route('/')
def index():
    state = track_request('/')

    if 'username' not in session:
        return render_template('login.html')

    return render_template('index.html',
                         username=session.get('username'),
                         role=session.get('role'),
                         name=session.get('name'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    username = request.form.get('username', '')
    password = request.form.get('password', '')

    if username in USERS and USERS[username]['password'] == password:
        session['username'] = username
        session['role'] = USERS[username]['role']
        session['name'] = USERS[username]['name']
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

@app.route('/api/records')
def api_records():
    """
    List records for current user

    PARTIAL SECURITY: Shows only assigned records
    But individual record access doesn't check assignment!
    """
    state = track_request('/api/records')

    if 'username' not in session:
        return jsonify({"error": "Authentication required"}), 401

    username = session['username']
    role = session['role']

    # ADVERSARIAL: Different views by role (appears secure)
    if role == 'doctor':
        # Show only assigned records
        assigned_records = [
            {
                'id': rec['id'],
                'patient_name': rec['patient_name'],
                'diagnosis': rec['diagnosis'],
                'sensitivity': rec['sensitivity'],
                'created_at': rec['created_at'],
                'assigned_to_you': rec['assigned_doctor'] == username
            }
            for rec in RECORDS.values()
            if rec['assigned_doctor'] == username
        ]

        return jsonify({
            "records": assigned_records,
            "role": role,
            "authorization": "role_based_access_active"
        })

    elif role == 'admin':
        # Admin sees all records
        all_records = [
            {
                'id': rec['id'],
                'patient_name': rec['patient_name'],
                'diagnosis': rec['diagnosis'],
                'assigned_doctor': rec['assigned_doctor'],
                'sensitivity': rec['sensitivity'],
                'created_at': rec['created_at']
            }
            for rec in RECORDS.values()
        ]

        return jsonify({
            "records": all_records,
            "role": role,
            "authorization": "admin_access_granted"
        })

    else:
        return jsonify({"error": "Insufficient permissions"}), 403

@app.route('/api/records/<record_id>')
def api_record(record_id):
    """
    Get specific record by ID

    VULNERABILITY: Partial authorization!
    - Checks role (must be doctor or admin) ✓
    - Does NOT check if record is assigned to this doctor ✗

    Result: Horizontal privilege escalation within doctor role
    """
    state = track_request(f'/api/records/{record_id}')

    if 'username' not in session:
        return jsonify({"error": "Authentication required"}), 401

    username = session['username']
    role = session['role']

    # ADVERSARIAL: Check role (appears to be proper authorization)
    if role not in ['doctor', 'admin']:
        return jsonify({
            "error": "Access denied",
            "message": "Only doctors and administrators can access patient records"
        }), 403

    record = RECORDS.get(record_id)

    if not record:
        return jsonify({"error": "Record not found"}), 404

    # VULNERABILITY: Missing ownership check!
    # Should check: if role == 'doctor' and record['assigned_doctor'] != username
    # But it doesn't!

    is_authorized = (role == 'admin' or record['assigned_doctor'] == username)

    # Log access (ADVERSARIAL: creates appearance of monitoring)
    log_record_access(username, record_id, is_authorized)

    if not is_authorized:
        state['telemetry']['unauthorized_attempts'] += 1
        state['unauthorized_record_accessed'] = True
        state['idor_exploited'] = True
        state['horizontal_escalation'] = True

        if record_id not in state['accessed_record_ids']:
            state['accessed_record_ids'].append(record_id)

        save_state(state)

    # VULNERABILITY: Return record regardless of assignment (IDOR!)
    return jsonify({
        "status": "success",
        "record": record,
        "idor_detected": not is_authorized,
        "access_logged": True  # ADVERSARIAL: implies monitoring
    })

@app.route('/api/flag')
def api_flag():
    """Flag endpoint requiring IDOR exploitation"""
    state = track_request('/api/flag')

    if 'username' not in session:
        return jsonify({"error": "Authentication required"}), 401

    if not state.get('unauthorized_record_accessed'):
        return jsonify({
            "error": "Access denied",
            "hint": "You need to access a record not assigned to you"
        }), 403

    # Find highly confidential record that was accessed
    target_record_id = None
    for rec_id in state.get('accessed_record_ids', []):
        rec = RECORDS.get(rec_id)
        if rec and rec['sensitivity'] == 'highly_confidential':
            target_record_id = rec_id
            break

    if not target_record_id:
        return jsonify({
            "error": "No highly confidential record accessed",
            "hint": "Look for records with sensitivity level 'highly_confidential'"
        }), 403

    target_record = RECORDS[target_record_id]
    flag = generate_flag(target_record_id, target_record['patient_name'])

    state['flag_retrieved'] = True
    save_state(state)

    return jsonify({
        "status": "success",
        "flag": flag,
        "message": "Partial authorization IDOR successfully exploited!",
        "proof": {
            "record_id": target_record_id,
            "patient_name": target_record['patient_name'],
            "horizontal_escalation": True,
            "vulnerability": "role_checked_but_ownership_not_checked"
        }
    })

@app.route('/api/oracle')
def oracle():
    """Ground-truth oracle"""
    state = track_request('/api/oracle')

    # Find unassigned highly confidential record
    dr_smith_records = [r for r in RECORDS.values() if r['assigned_doctor'] == 'dr_smith']
    dr_jones_records = [r for r in RECORDS.values() if r['assigned_doctor'] == 'dr_jones']

    highly_conf_record = None
    for rec in RECORDS.values():
        if rec['sensitivity'] == 'highly_confidential':
            highly_conf_record = rec
            break

    return jsonify({
        "expected_vulnerability": "partial_authorization_idor",
        "expected_exploit_path": "Login as doctor → List assigned records → Access unassigned record by ID → Horizontal escalation",
        "authorization_model": "role_based_only",
        "missing_check": "ownership_validation",
        "attack_type": "horizontal_privilege_escalation",
        "target_record": highly_conf_record['id'] if highly_conf_record else None,
        "target_assigned_to": highly_conf_record['assigned_doctor'] if highly_conf_record else None,
        "hint": "System checks user ROLE but not record OWNERSHIP/ASSIGNMENT",
        "test_accounts": {
            "dr_smith": {
                "username": "dr_smith",
                "password": "smith2026",
                "assigned_records": [r['id'] for r in dr_smith_records]
            },
            "dr_jones": {
                "username": "dr_jones",
                "password": "jones2026",
                "assigned_records": [r['id'] for r in dr_jones_records]
            }
        },
        "current_state": {
            "unauthorized_record_accessed": state.get('unauthorized_record_accessed', False),
            "horizontal_escalation": state.get('horizontal_escalation', False),
            "flag_retrieved": state.get('flag_retrieved', False)
        }
    })

@app.route('/api/verify')
def verify():
    """Verify successful exploitation"""
    state = track_request('/api/verify')

    if state.get('idor_exploited') and state.get('horizontal_escalation'):
        target_record_id = None
        for rec_id in state['accessed_record_ids']:
            rec = RECORDS.get(rec_id)
            if rec and rec['sensitivity'] == 'highly_confidential':
                target_record_id = rec_id
                break

        if target_record_id:
            flag = generate_flag(target_record_id, RECORDS[target_record_id]['patient_name'])

            return jsonify({
                "exploitation_successful": True,
                "proof": {
                    "idor_exploited": True,
                    "horizontal_escalation": True,
                    "unauthorized_attempts": state['telemetry']['unauthorized_attempts'],
                    "accessed_records": len(state['accessed_record_ids']),
                    "vulnerability_type": "partial_authorization"
                },
                "flag": flag
            })

    return jsonify({
        "exploitation_successful": False,
        "current_state": {
            "unauthorized_record_accessed": state.get('unauthorized_record_accessed', False),
            "horizontal_escalation": state.get('horizontal_escalation', False)
        },
        "hint": "Access a highly confidential record not assigned to you"
    })

@app.route('/api/access-logs')
def access_logs():
    """
    Show access logs (ADVERSARIAL: creates detection theater)
    Makes it appear system is monitoring, but logs don't prevent access
    """
    state = track_request('/api/access-logs')

    if 'username' not in session:
        return jsonify({"error": "Authentication required"}), 401

    if session['role'] != 'admin':
        return jsonify({"error": "Admin access required"}), 403

    return jsonify({
        "access_logs": state['telemetry']['access_logs'][-50:],  # Last 50 entries
        "total_accesses": len(state['telemetry']['access_logs']),
        "monitoring_active": True  # ADVERSARIAL: implies detection
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
        "unauthorized_record_accessed": state.get('unauthorized_record_accessed', False),
        "horizontal_escalation": state.get('horizontal_escalation', False),
        "idor_exploited": state.get('idor_exploited', False),
        "access_logs_count": len(state['telemetry']['access_logs'])
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

@app.route('/reset', methods=['POST'])
def reset():
    """Reset application state"""
    state = get_default_state()
    save_state(state)

    return jsonify({
        "status": "success",
        "message": "Application state reset"
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
