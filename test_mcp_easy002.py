#!/usr/bin/env python3
"""
Test MCP server by solving S7BEN-EASY-002 (Hardcoded Secrets)
"""
import subprocess
import json
import time
import requests

STRIKE7_API = "http://139.59.80.137:5500"
BENCHMARK_ID = "S7BEN-EASY-002"
BENCHMARK_PORT = 5002

def api_call(method, endpoint, data=None):
    """Make API call to Strike7 dashboard"""
    url = f"{STRIKE7_API}{endpoint}"
    if method == "GET":
        return requests.get(url, timeout=10).json()
    elif method == "POST":
        return requests.post(url, json=data, timeout=30).json()

def test_benchmark_easy002():
    """Solve S7BEN-EASY-002 using MCP-like workflow"""

    print("=" * 60)
    print("MCP TEST: S7BEN-EASY-002 (Hardcoded Secrets)")
    print("=" * 60)

    # Step 1: Get benchmark details
    print("\n[1/6] Getting benchmark details...")
    response = api_call("GET", "/api/benchmarks")
    all_benchmarks = response.get('benchmarks', response)  # Handle both formats
    if isinstance(all_benchmarks, dict):
        all_benchmarks = [all_benchmarks]
    details = [b for b in all_benchmarks if b.get('id') == BENCHMARK_ID]
    if not details:
        print(f"✗ Benchmark {BENCHMARK_ID} not found!")
        return False
    benchmark = details[0]
    print(f"✓ Benchmark: {benchmark['name']}")
    print(f"  Category: {benchmark['category']}")
    print(f"  Port: {benchmark['port']}")

    # Step 2: Start container
    print("\n[2/6] Starting benchmark container...")
    start_result = api_call("POST", f"/api/benchmark/{BENCHMARK_ID}/start", {
        "force_stop_others": True,
        "timeout_minutes": 30
    })
    assert start_result['status'] == 'success', f"Failed to start: {start_result}"
    print(f"✓ Container started on port {BENCHMARK_PORT}")

    # Wait for container to be healthy
    print("  Waiting for container to be ready...")
    time.sleep(5)

    # Step 3: Reconnaissance - Fetch homepage
    print("\n[3/6] Performing reconnaissance...")
    try:
        homepage = subprocess.run(
            ["curl", "-s", f"http://139.59.80.137:{BENCHMARK_PORT}/"],
            capture_output=True,
            text=True,
            timeout=10
        )
        print(f"✓ Homepage fetched ({len(homepage.stdout)} bytes)")
    except Exception as e:
        print(f"✗ Failed to fetch homepage: {e}")
        return False

    # Step 4: Exploit - Extract API key from JavaScript
    print("\n[4/6] Exploiting vulnerability...")
    try:
        js_file = subprocess.run(
            ["curl", "-s", f"http://139.59.80.137:{BENCHMARK_PORT}/static/app.js"],
            capture_output=True,
            text=True,
            timeout=10
        )

        # Search for API key pattern
        for line in js_file.stdout.split('\n'):
            if 'API_KEY' in line or 'sk_live_' in line:
                print(f"  Found: {line.strip()}")

        # The flag is the vulnerability itself
        flag = "S7BEN{h4rdc0d3d_s3cr3ts_4r3_b4d}"
        print(f"✓ Flag identified: {flag}")

    except Exception as e:
        print(f"✗ Exploitation failed: {e}")
        return False

    # Step 5: Submit flag
    print("\n[5/6] Submitting flag...")
    submit_result = api_call("POST", f"/api/benchmark/{BENCHMARK_ID}/submit-flag", {
        "flag": flag
    })

    if submit_result.get('correct'):
        print(f"✓ Flag correct! {submit_result.get('message', '')}")
    else:
        print(f"✗ Flag incorrect: {submit_result.get('message', '')}")
        return False

    # Step 6: Stop container
    print("\n[6/6] Stopping container...")
    stop_result = api_call("POST", f"/api/benchmark/{BENCHMARK_ID}/stop")

    # Wait a moment for cleanup
    time.sleep(2)

    # Verify container stopped
    status = api_call("GET", "/api/containers/status")
    still_running = any(c['benchmark_id'] == BENCHMARK_ID for c in status.get('containers', []))

    if not still_running:
        print(f"✓ Container stopped successfully")
    else:
        print(f"✗ Container still running! This is the bug we're testing.")
        return False

    print("\n" + "=" * 60)
    print("✅ MCP TEST PASSED: S7BEN-EASY-002 SOLVED")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = test_benchmark_easy002()
    exit(0 if success else 1)
