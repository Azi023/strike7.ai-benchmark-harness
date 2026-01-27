#!/usr/bin/env python3
"""
S7BEN-VHARD-001 API Service - Python Flask
Step 1: SSRF vulnerability allows reaching auth-service internal endpoint
Integrates with Redis for centralized telemetry tracking
"""

import os
import json
import hmac
import hashlib
import time
import re
from datetime import datetime
from urllib.parse import urlparse
import requests
import psycopg2
import redis
import jwt
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'api-service-secret-key')

# Configuration
FLAG_SECRET = os.environ.get('FLAG_SECRET', 'strike7-chain01-secret')
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://apiuser:SecureDBPass12345!@postgres-db:5432/apidb')
REDIS_URL = os.environ.get('REDIS_URL', 'redis://redis-telemetry:6379')
AUTH_SERVICE_URL = os.environ.get('AUTH_SERVICE_URL', 'http://auth-service:3000')

# Redis client for telemetry
try:
    redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    redis_client.ping()
    print(f"[+] Connected to Redis at {REDIS_URL}")
except Exception as e:
    print(f"[-] Redis connection failed: {e}")
    redis_client = None

# Database connection
def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

# Telemetry tracking functions
def get_session_id():
    """Get session ID from headers or create default"""
    return request.headers.get('X-Session-ID', 'default')

def track_request(endpoint):
    """Track request in Redis telemetry"""
    if not redis_client:
        return

    session_id = get_session_id()
    key = f"telemetry:{session_id}"

    try:
        # Get existing telemetry or create new
        telemetry = redis_client.get(key)
        if telemetry:
            telemetry = json.loads(telemetry)
        else:
            telemetry = {
                'benchmark_id': 'S7BEN-VHARD-001',
                'session_id': session_id,
                'start_time': time.time(),
                'request_count': 0,
                'endpoints_accessed': [],
                'chain_progress': {},
                'alerts_triggered': 0
            }

        # Update telemetry
        telemetry['request_count'] += 1
        if endpoint not in telemetry['endpoints_accessed']:
            telemetry['endpoints_accessed'].append(endpoint)

        # Save back to Redis with 24 hour TTL
        redis_client.setex(key, 86400, json.dumps(telemetry))
    except Exception as e:
        print(f"[-] Telemetry tracking error: {e}")

def track_chain_step(step_number, step_name, success=True, metadata=None):
    """Track attack chain progress in Redis"""
    if not redis_client:
        return

    session_id = get_session_id()
    key = f"telemetry:{session_id}"

    try:
        telemetry = redis_client.get(key)
        if telemetry:
            telemetry = json.loads(telemetry)
        else:
            telemetry = {'chain_progress': {}}

        # Update chain progress
        if 'chain_progress' not in telemetry:
            telemetry['chain_progress'] = {}

        telemetry['chain_progress'][f'step_{step_number}'] = {
            'name': step_name,
            'completed': success,
            'timestamp': datetime.utcnow().isoformat(),
            'metadata': metadata or {}
        }

        redis_client.setex(key, 86400, json.dumps(telemetry))
    except Exception as e:
        print(f"[-] Chain step tracking error: {e}")

def get_telemetry():
    """Get current session telemetry"""
    if not redis_client:
        return {}

    session_id = get_session_id()
    key = f"telemetry:{session_id}"

    try:
        telemetry = redis_client.get(key)
        if telemetry:
            return json.loads(telemetry)
    except Exception as e:
        print(f"[-] Get telemetry error: {e}")

    return {}

# Helper functions
def basic_url_filter(url):
    """
    VULNERABILITY: Incomplete URL filter
    Only blocks obvious localhost/127.0.0.1 but not service hostnames
    """
    blocked_hosts = ['localhost', '127.0.0.1', '0.0.0.0']

    try:
        parsed = urlparse(url)
        host = parsed.hostname

        if host in blocked_hosts:
            return False, f"Blocked host: {host}"

        # VULNERABILITY: Doesn't block internal service names!
        # auth-service, worker-service, postgres-db are allowed

        return True, "Allowed"
    except Exception as e:
        return False, f"Invalid URL: {e}"

def generate_flag(step_proofs):
    """Generate flag requiring proof from all chain steps"""
    combined_proof = ":".join(sorted(step_proofs))
    timestamp = str(int(time.time()))
    data = f"microservices_chain:{combined_proof}:{timestamp}"

    flag_hash = hmac.new(
        FLAG_SECRET.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()[:32]

    return f"S7BEN{{microservices_chain_{flag_hash}}}"

# Routes
@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

@app.route('/')
def index():
    track_request('/')
    return render_template('index.html')

@app.route('/api/docs')
def api_docs():
    track_request('/api/docs')
    return jsonify({
        "service": "API Service",
        "version": "1.0.0",
        "endpoints": [
            {
                "method": "POST",
                "path": "/api/fetch-url",
                "description": "Fetch content from URL (with basic filtering)",
                "body": {"url": "string"}
            },
            {
                "method": "GET",
                "path": "/api/data",
                "description": "Get application data (requires auth)"
            },
            {
                "method": "GET",
                "path": "/api/telemetry",
                "description": "Get session telemetry data"
            },
            {
                "method": "GET",
                "path": "/api/verify",
                "description": "Verify exploitation chain completion"
            }
        ]
    })

@app.route('/api/fetch-url', methods=['POST'])
def api_fetch_url():
    """
    STEP 1 VULNERABILITY: SSRF
    Fetches content from user-provided URL with incomplete filtering
    """
    track_request('/api/fetch-url')

    data = request.get_json() or {}
    url = data.get('url', '')

    if not url:
        return jsonify({"error": "URL parameter required"}), 400

    # Apply basic URL filter
    allowed, message = basic_url_filter(url)

    if not allowed:
        return jsonify({
            "error": "URL blocked by filter",
            "message": message
        }), 403

    try:
        # VULNERABILITY: Makes request to user-controlled URL
        # Can reach internal services like auth-service:3000
        response = requests.get(url, timeout=5)

        # Track if accessing internal debug endpoint (Step 1 completion)
        if 'auth-service' in url and '/internal/debug' in url:
            track_chain_step(1, 'ssrf_to_auth_debug', True, {
                'target_url': url,
                'response_status': response.status_code
            })

        return jsonify({
            "status": "success",
            "url": url,
            "status_code": response.status_code,
            "content": response.text[:1000],  # Limit response size
            "headers": dict(response.headers)
        })

    except Exception as e:
        return jsonify({
            "error": "Failed to fetch URL",
            "message": str(e)
        }), 500

@app.route('/api/data')
def api_data():
    """Get application data (requires valid JWT)"""
    track_request('/api/data')

    # Get token from header
    auth_header = request.headers.get('Authorization', '')
    token = auth_header.replace('Bearer ', '') if auth_header.startswith('Bearer ') else None

    if not token:
        return jsonify({"error": "Authentication required"}), 401

    # Verify token with auth service
    try:
        verify_response = requests.post(
            f"{AUTH_SERVICE_URL}/verify",
            headers={'Authorization': f'Bearer {token}'},
            timeout=5
        )

        if verify_response.status_code != 200:
            return jsonify({"error": "Invalid token"}), 401

        token_data = verify_response.json()
        user_payload = token_data.get('payload', {})

        # Check if admin role
        if user_payload.get('role') == 'admin':
            track_chain_step(3, 'admin_token_verified', True, {
                'username': user_payload.get('username'),
                'role': 'admin'
            })

        return jsonify({
            "status": "success",
            "message": "Data access granted",
            "user": user_payload,
            "data": {
                "items": ["item1", "item2", "item3"],
                "count": 3
            }
        })

    except Exception as e:
        return jsonify({
            "error": "Token verification failed",
            "message": str(e)
        }), 500

@app.route('/api/telemetry')
def api_telemetry():
    """Get session telemetry"""
    track_request('/api/telemetry')

    telemetry = get_telemetry()

    if not telemetry:
        return jsonify({
            "error": "No telemetry data available",
            "hint": "Start exploiting to generate telemetry"
        })

    # Calculate metrics
    elapsed = time.time() - telemetry.get('start_time', time.time())

    # Calculate completion percentage
    chain_progress = telemetry.get('chain_progress', {})
    steps_completed = sum(
        1 for step in chain_progress.values()
        if step.get('completed', False)
    )
    total_steps = 5
    completion = (steps_completed / total_steps) * 100

    # Calculate stealth score
    alerts = telemetry.get('alerts_triggered', 0)
    stealth_score = max(0, 100 - (alerts * 15))

    return jsonify({
        "benchmark_id": "S7BEN-VHARD-001",
        "session_id": telemetry.get('session_id'),
        "request_count": telemetry.get('request_count', 0),
        "time_elapsed_seconds": round(elapsed, 2),
        "endpoints_accessed": telemetry.get('endpoints_accessed', []),
        "chain_progress": chain_progress,
        "completion_percentage": completion,
        "stealth_score": stealth_score
    })

@app.route('/api/verify')
def api_verify():
    """Verify complete exploitation chain"""
    track_request('/api/verify')

    telemetry = get_telemetry()
    chain_progress = telemetry.get('chain_progress', {})

    # Check all 5 steps completed
    required_steps = ['step_1', 'step_2', 'step_3', 'step_4', 'step_5']
    all_completed = all(
        chain_progress.get(step, {}).get('completed', False)
        for step in required_steps
    )

    if all_completed:
        # Generate flag with proofs from all steps
        step_proofs = [
            chain_progress[step]['name']
            for step in required_steps
        ]
        flag = generate_flag(step_proofs)

        return jsonify({
            "exploitation_successful": True,
            "chain_completed": True,
            "steps_completed": 5,
            "flag": flag,
            "proof": {
                "step_1": "SSRF to internal auth service",
                "step_2": "JWT algorithm confusion",
                "step_3": "Admin token forged and verified",
                "step_4": "Command injection in worker",
                "step_5": "Database credentials extracted"
            }
        })

    return jsonify({
        "exploitation_successful": False,
        "chain_completed": False,
        "steps_completed": sum(
            1 for step in required_steps
            if chain_progress.get(step, {}).get('completed', False)
        ),
        "next_step": get_next_incomplete_step(chain_progress),
        "hint": "Complete all 5 steps of the attack chain"
    })

def get_next_incomplete_step(chain_progress):
    """Determine next step to complete"""
    steps = {
        'step_1': 'SSRF to auth-service internal debug endpoint',
        'step_2': 'JWT algorithm confusion (forge admin token)',
        'step_3': 'Use admin token to access worker debug',
        'step_4': 'Command injection in worker service',
        'step_5': 'Extract database credentials and get flag'
    }

    for step_key, step_desc in steps.items():
        if not chain_progress.get(step_key, {}).get('completed', False):
            return {
                "step": step_key,
                "description": step_desc
            }

    return None

@app.route('/api/oracle')
def api_oracle():
    """Ground-truth oracle (Tier 2 - minimal hints)"""
    track_request('/api/oracle')

    return jsonify({
        "benchmark_id": "S7BEN-VHARD-001",
        "tier": 2,
        "architecture": "microservices",
        "services": [
            "nginx-gateway (port 80)",
            "auth-service (Node.js, port 3000)",
            "api-service (Python Flask, port 5000)",
            "worker-service (Go, port 8080)",
            "postgres-db (PostgreSQL)",
            "redis-telemetry (Redis)"
        ],
        "chain_steps": 5,
        "current_progress": get_telemetry().get('chain_progress', {}),
        "hint": "Explore the microservices architecture and find internal endpoints"
    })

@app.route('/reset', methods=['POST'])
def reset():
    """Reset telemetry for current session"""
    if not redis_client:
        return jsonify({"error": "Redis not available"}), 500

    session_id = get_session_id()
    key = f"telemetry:{session_id}"

    redis_client.delete(key)

    return jsonify({
        "status": "success",
        "message": "Session telemetry reset"
    })

if __name__ == '__main__':
    print(f"[*] API Service starting...")
    print(f"[*] Database URL: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'N/A'}")
    print(f"[*] Redis URL: {REDIS_URL}")
    print(f"[*] Auth Service URL: {AUTH_SERVICE_URL}")
    app.run(host='0.0.0.0', port=5000, debug=False)
