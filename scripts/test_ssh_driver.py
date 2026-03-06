#!/usr/bin/env python3
"""Test SSHDriver by connecting to localhost (loopback)."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "dashboard"))
from orchestrator.docker_driver import SSHDriver

SSH_KEY = "/root/.ssh/worker_key"
driver = SSHDriver(host="localhost", user="root", ssh_key=SSH_KEY)

results = {}

# Test 1: Ping
ping_ok = driver.ping()
results["ping"] = ping_ok
print(f"Ping:           {'PASS' if ping_ok else 'FAIL'}")

# Test 2: Container list
cl = driver.container_list()
results["container_list"] = cl.success
print(f"container_list: {'PASS' if cl.success else 'FAIL'}")

# Test 3: System info
si = driver.system_info()
results["system_info"] = si.success
print(f"system_info:    {'PASS' if si.success else 'FAIL'}")

# Test 4: Image check
ie = driver.image_exists("alpine:latest")
results["image_exists"] = isinstance(ie, bool)
print(f"image_exists:   {'PASS' if isinstance(ie, bool) else 'FAIL'} (alpine={ie})")

# Test 5: compose_ps on a benchmark dir
bench_dir = "/opt/strike7.ai-benchmark-harness/benchmarks/S7BEN-EASY-001"
if os.path.isdir(bench_dir):
    ps = driver.compose_ps(bench_dir)
    results["compose_ps"] = ps.success
    print(f"compose_ps:     {'PASS' if ps.success else 'FAIL'}")
else:
    print(f"compose_ps:     SKIP (dir not found)")

# Summary
print()
passed = sum(1 for v in results.values() if v)
total = len(results)
if passed == total:
    print(f"SSHDriver: ALL {total} TESTS PASSED")
else:
    print(f"SSHDriver: {passed}/{total} PASSED")
    sys.exit(1)
