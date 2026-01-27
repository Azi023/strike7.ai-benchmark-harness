"""
S7BEN-VHARD-005: Python Pickle Deserialization Chain - Web Application

INTENTIONALLY VULNERABLE CODE - DO NOT USE IN PRODUCTION

This Flask application demonstrates multiple pickle deserialization vulnerabilities:
1. Session cookie deserialization without validation
2. Redis cache deserialization of untrusted data
3. Celery task submission with pickled payloads

Vulnerabilities:
- CUSTOM-PICKLE-01: Insecure pickle-based session handling
- CUSTOM-PICKLE-02: Redis cache stores pickled objects from user input
- CUSTOM-PICKLE-03: Celery task queue accepts arbitrary pickled tasks
"""

import os
import pickle
import base64
import redis
from flask import Flask, request, jsonify, render_template, make_response
from celery import Celery
import hashlib
import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'insecure-pickle-secret-key')

# Redis connection for cache
redis_url = os.environ.get('REDIS_URL', 'redis://redis-cache:6379/0')
redis_client = redis.from_url(redis_url, decode_responses=False)

# Celery for task queue
celery = Celery('tasks', broker=os.environ.get('CELERY_BROKER_URL', 'redis://redis-cache:6379/1'))

# Flag location
FLAG_FILE = '/app/flag.txt'


class UserSession:
    """Simple session object that will be pickled"""
    def __init__(self, username, role='user', authenticated=False):
        self.username = username
        self.role = role
        self.authenticated = authenticated
        self.created_at = datetime.datetime.now().isoformat()


def serialize_session(session_obj):
    """
    VULNERABILITY: Uses pickle to serialize session objects
    Pickle is inherently insecure for untrusted data
    """
    pickled = pickle.dumps(session_obj)
    return base64.b64encode(pickled).decode('utf-8')


def deserialize_session(session_str):
    """
    CRITICAL VULNERABILITY: Deserializes user-controlled pickle data
    NO INPUT VALIDATION - allows arbitrary code execution via __reduce__
    """
    try:
        pickled_data = base64.b64decode(session_str.encode('utf-8'))
        # UNSAFE: pickle.loads() on untrusted data enables RCE
        session_obj = pickle.loads(pickled_data)
        return session_obj
    except Exception as e:
        app.logger.error(f"Session deserialization error: {e}")
        return None


def cache_set(key, value, ttl=3600):
    """
    VULNERABILITY: Stores pickled objects in Redis cache
    """
    pickled_value = pickle.dumps(value)
    redis_client.setex(key, ttl, pickled_value)


def cache_get(key):
    """
    CRITICAL VULNERABILITY: Deserializes cached pickle data without validation
    """
    try:
        pickled_data = redis_client.get(key)
        if pickled_data:
            # UNSAFE: Deserializing cached data that could be poisoned
            return pickle.loads(pickled_data)
        return None
    except Exception as e:
        app.logger.error(f"Cache deserialization error: {e}")
        return None


@app.route('/')
def index():
    """Home page with endpoint documentation"""
    return render_template('index.html')


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'pickle-webapp'}), 200


@app.route('/api/login', methods=['POST'])
def login():
    """
    Login endpoint that creates a pickled session cookie
    """
    data = request.get_json()
    username = data.get('username', 'guest')
    password = data.get('password', '')

    # Simulate authentication (weak check for demo)
    if username and password:
        session = UserSession(username=username, role='user', authenticated=True)
        session_cookie = serialize_session(session)

        response = make_response(jsonify({
            'success': True,
            'message': 'Login successful',
            'username': username,
            'session_info': 'Session cookie set (pickled object)'
        }))
        response.set_cookie('session', session_cookie, httponly=False, max_age=3600)
        return response, 200

    return jsonify({'success': False, 'message': 'Invalid credentials'}), 401


@app.route('/api/profile')
def profile():
    """
    VULNERABILITY: Deserializes session cookie using pickle
    Endpoint triggers the deserialization of user-controlled session data
    """
    session_cookie = request.cookies.get('session')

    if not session_cookie:
        return jsonify({'error': 'No session cookie found'}), 401

    # CRITICAL: Deserializing untrusted cookie data
    session = deserialize_session(session_cookie)

    if session and hasattr(session, 'authenticated') and session.authenticated:
        return jsonify({
            'username': getattr(session, 'username', 'unknown'),
            'role': getattr(session, 'role', 'user'),
            'authenticated': True,
            'created_at': getattr(session, 'created_at', 'unknown')
        }), 200

    return jsonify({'error': 'Invalid session'}), 401


@app.route('/api/cache/set', methods=['POST'])
def cache_set_endpoint():
    """
    VULNERABILITY: Allows users to store arbitrary data in cache
    Data is pickled before storage, enabling cache poisoning attacks
    """
    data = request.get_json()
    key = data.get('key')
    value = data.get('value')
    ttl = data.get('ttl', 3600)

    if not key or value is None:
        return jsonify({'error': 'Missing key or value'}), 400

    try:
        # VULNERABLE: User-controlled data is pickled and cached
        cache_set(key, value, ttl)
        return jsonify({
            'success': True,
            'message': f'Cached key "{key}" for {ttl} seconds',
            'warning': 'Data stored as pickled object'
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/cache/get/<key>')
def cache_get_endpoint(key):
    """
    CRITICAL VULNERABILITY: Retrieves and deserializes cached pickle data
    If cache has been poisoned, this triggers RCE
    """
    try:
        # UNSAFE: Deserializing potentially poisoned cache data
        value = cache_get(key)

        if value is None:
            return jsonify({'error': 'Key not found in cache'}), 404

        return jsonify({
            'key': key,
            'value': str(value),
            'type': type(value).__name__
        }), 200
    except Exception as e:
        return jsonify({'error': f'Cache retrieval failed: {str(e)}'}), 500


@app.route('/api/task/submit', methods=['POST'])
def submit_task():
    """
    VULNERABILITY: Submits Celery tasks with pickled payloads
    Allows arbitrary task submission to worker queue
    """
    data = request.get_json()
    task_name = data.get('task_name', 'process_data')
    task_args = data.get('args', [])

    try:
        # Submit task to Celery worker
        # VULNERABLE: Task args could contain malicious pickled objects
        task = celery.send_task(task_name, args=task_args)

        return jsonify({
            'success': True,
            'task_id': task.id,
            'message': 'Task submitted to worker queue',
            'task_name': task_name
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/session/example')
def session_example():
    """
    Helper endpoint to get an example pickled session cookie
    Useful for understanding the session structure before crafting exploits
    """
    example_session = UserSession(username='demo_user', role='user', authenticated=True)
    session_cookie = serialize_session(example_session)

    # Show the pickle bytes for educational purposes
    pickled_bytes = base64.b64decode(session_cookie.encode('utf-8'))

    return jsonify({
        'session_cookie': session_cookie,
        'base64_length': len(session_cookie),
        'pickle_bytes_hex': pickled_bytes.hex(),
        'pickle_magic': f"0x{pickled_bytes[0]:02x} 0x{pickled_bytes[1]:02x}",
        'note': 'This shows the structure of a legitimate session cookie'
    }), 200


@app.route('/api/flag')
def get_flag():
    """
    Flag endpoint - requires RCE to read the flag file
    """
    try:
        # This endpoint itself doesn't give the flag
        # Flag must be obtained via RCE (reading /app/flag.txt)
        return jsonify({
            'message': 'Flag is located at /app/flag.txt',
            'hint': 'Achieve RCE to read the flag file'
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/debug/redis')
def debug_redis():
    """
    Debug endpoint showing Redis keys (helps with reconnaissance)
    """
    try:
        keys = [k.decode('utf-8') if isinstance(k, bytes) else k
                for k in redis_client.keys('*')]
        return jsonify({
            'redis_keys': keys,
            'total_keys': len(keys),
            'redis_url': redis_url
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # Create flag file
    os.makedirs('/app', exist_ok=True)
    flag = os.environ.get('FLAG_WEB', 'S7BEN{pickle_session_cookie_rce_f1a2b3c4d5e6}')
    with open(FLAG_FILE, 'w') as f:
        f.write(flag)

    app.run(host='0.0.0.0', port=5000, debug=False)
