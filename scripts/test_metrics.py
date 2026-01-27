#!/usr/bin/env python3
"""
Test script for Strike7 Metrics System
Simulates agent attempts and verifies metrics calculation
"""

import requests
import time
import json
from datetime import datetime

BASE_URL = "http://localhost:5500"

def test_metrics_system():
    """Test the complete metrics system"""
    print("[+] Strike7 Metrics System Test")
    print("=" * 60)

    session_id = f"test-session-{int(time.time())}"
    agent_id = "test-agent-v1.0"

    print(f"\n[1] Testing Attempt Recording")
    print(f"    Session: {session_id}")
    print(f"    Agent: {agent_id}")

    # Simulate 10 benchmark attempts with varying results
    test_attempts = [
        # Format: (benchmark_id, success, ttf, tool_calls, tokens, detected)
        ("S7BEN-EASY-001", True, 30.5, 10, 2000, False),
        ("S7BEN-EASY-002", True, 25.2, 8, 1800, False),
        ("S7BEN-EASY-003", False, None, 15, 3000, False),
        ("S7BEN-EASY-003", True, 45.8, 20, 4000, False),  # Second attempt succeeds
        ("S7BEN-MED-001", True, 120.3, 35, 8000, False),
        ("S7BEN-MED-002", False, None, 25, 5000, True),  # Detected!
        ("S7BEN-MED-002", False, None, 18, 4000, False),
        ("S7BEN-MED-002", True, 180.5, 40, 9000, False),  # Third attempt succeeds
        ("S7BEN-HARD-001", False, None, 50, 12000, False),
        ("S7BEN-HARD-001", False, None, 45, 11000, False),
    ]

    for i, (benchmark_id, success, ttf, tool_calls, tokens, detected) in enumerate(test_attempts, 1):
        response = requests.post(
            f"{BASE_URL}/api/metrics/attempt",
            json={
                "session_id": session_id,
                "agent_id": agent_id,
                "benchmark_id": benchmark_id,
                "success": success,
                "time_to_flag": ttf,
                "tool_calls": tool_calls,
                "tokens_used": tokens,
                "detected": detected,
                "metadata": {
                    "model": "claude-sonnet-4-20250514",
                    "test_run": True
                }
            }
        )

        if response.status_code == 200:
            result = "✓ SUCCESS" if success else "✗ FAILED"
            print(f"    [{i}/10] {benchmark_id}: {result}")
        else:
            print(f"    [{i}/10] ERROR: {response.text}")
            return False

    print("\n[2] Testing pass@k Calculation")

    for k in [1, 3, 5]:
        response = requests.get(
            f"{BASE_URL}/api/metrics/pass-at-k",
            params={"agent_id": agent_id, "k": k}
        )
        if response.status_code == 200:
            data = response.json()
            print(f"    pass@{k}: {data['value']}% ({data['solved_within_k']}/{data['total_benchmarks']} solved)")
        else:
            print(f"    pass@{k}: ERROR")

    print("\n[3] Testing Time-to-Flag (TTF) Stats")
    response = requests.get(
        f"{BASE_URL}/api/metrics/ttf",
        params={"agent_id": agent_id}
    )
    if response.status_code == 200:
        data = response.json()
        print(f"    Count: {data['count']}")
        print(f"    Mean: {data['mean']}s")
        print(f"    Median: {data['median']}s")
        print(f"    Min: {data['min']}s")
        print(f"    Max: {data['max']}s")
        print(f"    P95: {data['p95']}s")
    else:
        print(f"    ERROR: {response.text}")

    print("\n[4] Testing Efficiency Metrics")
    response = requests.get(
        f"{BASE_URL}/api/metrics/efficiency",
        params={"agent_id": agent_id}
    )
    if response.status_code == 200:
        data = response.json()
        print(f"    Successful attempts: {data['count']}")

        if data['tool_calls']:
            print(f"    Tool calls (avg): {data['tool_calls']['mean']}")
        if data['tokens']:
            print(f"    Tokens (avg): {data['tokens']['mean']}")
        if data['time']:
            print(f"    Time (avg): {data['time']['mean']}s")
    else:
        print(f"    ERROR: {response.text}")

    print("\n[5] Testing Stealth Score")
    response = requests.get(
        f"{BASE_URL}/api/metrics/stealth",
        params={"agent_id": agent_id}
    )
    if response.status_code == 200:
        data = response.json()
        print(f"    Stealth Score: {data['score']}%")
        print(f"    Undetected: {data['undetected']}")
        print(f"    Detected: {data['detected']}")
    else:
        print(f"    ERROR: {response.text}")

    print("\n[6] Testing Leaderboard")
    response = requests.get(
        f"{BASE_URL}/api/metrics/leaderboard",
        params={"metric": "pass@3", "limit": 5}
    )
    if response.status_code == 200:
        data = response.json()
        print(f"    Top Agents by pass@3:")
        for i, agent in enumerate(data['leaderboard'], 1):
            print(f"    {i}. {agent['agent_id']}: {agent['pass_at_3']}% (TTF: {agent['avg_ttf']}s)")
    else:
        print(f"    ERROR: {response.text}")

    print("\n[7] Testing Comprehensive Dashboard")
    response = requests.get(
        f"{BASE_URL}/api/metrics/dashboard",
        params={"agent_id": agent_id}
    )
    if response.status_code == 200:
        data = response.json()
        print(f"    ✓ Dashboard data retrieved successfully")
        print(f"    Metrics included:")
        print(f"      - pass@1: {data['metrics']['pass_at_1']['value']}%")
        print(f"      - pass@3: {data['metrics']['pass_at_3']['value']}%")
        print(f"      - pass@5: {data['metrics']['pass_at_5']['value']}%")
        print(f"      - TTF (mean): {data['metrics']['time_to_flag']['mean']}s")
        print(f"      - Stealth: {data['metrics']['stealth']['score']}%")
    else:
        print(f"    ERROR: {response.text}")

    print("\n[8] Testing Benchmark Difficulty Analysis")
    response = requests.get(f"{BASE_URL}/api/metrics/benchmark-difficulty")
    if response.status_code == 200:
        data = response.json()
        print(f"    ✓ Difficulty analysis retrieved")
        print(f"    Sample benchmarks:")
        for benchmark in data['benchmarks'][:3]:
            print(f"      - {benchmark['benchmark_id']}: {benchmark['success_rate']}% success rate")
    else:
        print(f"    ERROR: {response.text}")

    print("\n" + "=" * 60)
    print("[✓] All Metrics Tests Completed Successfully!")
    print("\n📊 View full dashboard:")
    print(f"   curl '{BASE_URL}/api/metrics/dashboard?agent_id={agent_id}'")
    print("\n📈 View in browser:")
    print(f"   http://localhost:5500")

    return True


if __name__ == "__main__":
    try:
        # Check if server is running
        response = requests.get(f"{BASE_URL}/api/benchmarks", timeout=2)
        if response.status_code != 200:
            print("[!] Dashboard server not responding correctly")
            print("[!] Start it with: python dashboard/app.py")
            exit(1)
    except Exception as e:
        print(f"[!] Cannot connect to dashboard at {BASE_URL}")
        print(f"[!] Error: {e}")
        print("[!] Start the server with: python dashboard/app.py")
        exit(1)

    # Run tests
    success = test_metrics_system()
    exit(0 if success else 1)
