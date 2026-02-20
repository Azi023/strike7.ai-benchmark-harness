"""
S7BEN-VHARD-005: Celery Worker Service

This Celery worker demonstrates pickle deserialization vulnerabilities
in asynchronous task processing.

Vulnerability:
- CUSTOM-PICKLE-03: Celery deserializes task payloads using pickle (insecure)
"""

import os
import pickle
from celery import Celery

# Celery configuration
BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://redis-cache:6379/1')
RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://redis-cache:6379/1')

app = Celery('tasks', broker=BROKER_URL, backend=RESULT_BACKEND)

# Using pickle as task serializer
app.conf.update(
    task_serializer='pickle',
    result_serializer='pickle',
    accept_content=['pickle', 'json'],  # Accepts pickle content
    timezone='UTC',
    enable_utc=True,
)

FLAG_FILE = '/worker/secret_flag.txt'


@app.task(name='process_data')
def process_data(*args, **kwargs):
    """
    Sample Celery task that processes data
    """
    print(f"[WORKER] Processing task with args: {args}, kwargs: {kwargs}")

    result = {
        'status': 'processed',
        'args_count': len(args),
        'kwargs_count': len(kwargs)
    }

    return result


@app.task(name='compute_hash')
def compute_hash(data):
    """
    Task that computes hash of data
    """
    import hashlib

    print(f"[WORKER] Computing hash for data: {data}")

    if isinstance(data, str):
        hash_value = hashlib.sha256(data.encode()).hexdigest()
    else:
        hash_value = hashlib.sha256(str(data).encode()).hexdigest()

    return {
        'hash': hash_value,
        'algorithm': 'SHA-256'
    }


@app.task(name='execute_command')
def execute_command(command):
    """
    DANGEROUS: Task that executes system commands
    This demonstrates the severity of pickle deserialization RCE

    In a real attack, this task wouldn't exist - instead, the attacker
    would inject a malicious pickle payload that bypasses task routing
    """
    import subprocess

    print(f"[WORKER] WARNING: Executing command: {command}")

    try:
        result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
        return {
            'output': result.decode('utf-8'),
            'success': True
        }
    except subprocess.CalledProcessError as e:
        return {
            'output': e.output.decode('utf-8'),
            'success': False,
            'error': str(e)
        }


if __name__ == '__main__':
    # Create flag file
    os.makedirs('/worker', exist_ok=True)
    flag = os.environ.get('FLAG_WORKER', 'S7BEN{celery_worker_task_deserialization_m3n4o5p6q7r8}')
    with open(FLAG_FILE, 'w') as f:
        f.write(flag)

    print("[WORKER] Starting Celery worker")

    # Start worker
    app.worker_main(['worker', '--loglevel=info'])
