#!/usr/bin/env python3
import os
import re
import json
from typing import Dict, List, Any, Tuple


RE_BENCHMARK_DIR = re.compile(r"^S7BEN-[A-Z]+-\d{3}$")

KEYWORDS_HINT = [
    "sqli", "xss", "ssrf", "idor", "rce", "csrf",
    "lfi", "rfi", "traversal", "path_traversal",
    "inject", "injection", "exploit", "bypass",
    "open_redirect", "deserialization", "overflow"
]

WEB_ROOT_HINTS = [
    "/usr/share/nginx/html", "/var/www", "/www", "/htdocs",
    "/app/static", "/app/public", "/public", "/static"
]

def list_benchmarks(root: str) -> List[str]:
    entries = []
    for name in os.listdir(root):
        path = os.path.join(root, name)
        if os.path.isdir(path) and RE_BENCHMARK_DIR.match(name):
            entries.append(name)
    entries.sort()
    return entries

def read_text_safe(path: str) -> str:
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except Exception:
        return ""

def grep_terms_in_dir(dirpath: str, terms: List[str]) -> List[Tuple[str,int,str]]:
    matches: List[Tuple[str,int,str]] = []
    for root, _, files in os.walk(dirpath):
        for fn in files:
            # Skip obvious binaries and large artifacts
            if any(fn.lower().endswith(ext) for ext in [
                '.png','.jpg','.jpeg','.gif','.svg','.ico','.pdf',
                '.zip','.tar','.gz','.tgz','.7z','.jar','.war',
                '.pyc','.o','.so','.bin'
            ]):
                continue
            fpath = os.path.join(root, fn)
            try:
                with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                    for i, line in enumerate(f, start=1):
                        for t in terms:
                            if t in line:
                                snippet = line.strip()[:300]
                                matches.append((os.path.relpath(fpath, dirpath), i, snippet))
                                break
            except Exception:
                continue
    return matches

def scan_flag_hardcoded(dirpath: str) -> Dict[str, Any]:
    # Strong indicator: literal S7{...}
    matches = grep_terms_in_dir(dirpath, ["S7{"])
    return {
        "pass": len(matches) == 0,
        "details": [
            {"file": m[0], "line": m[1], "snippet": m[2]} for m in matches
        ]
    }

DOC_EXT_SKIP = {'.md', '.markdown', '.rst', '.txt'}

def scan_comment_hints(dirpath: str) -> Dict[str, Any]:
    results: List[Dict[str, Any]] = []
    for root, _, files in os.walk(dirpath):
        for fn in files:
            lower = fn.lower()
            if any(lower.endswith(ext) for ext in [
                '.png','.jpg','.jpeg','.gif','.svg','.ico','.pdf',
                '.zip','.tar','.gz','.tgz','.7z','.jar','.war',
                '.pyc','.o','.so','.bin'
            ]):
                continue
            if any(lower.endswith(ext) for ext in DOC_EXT_SKIP):
                continue
            fpath = os.path.join(root, fn)
            try:
                with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                    for i, line in enumerate(f, start=1):
                        low = line.lower()
                        if not any(k in low for k in KEYWORDS_HINT):
                            continue
                        if any(m in low for m in ['#','//','/*','<!--']):
                            results.append({
                                "file": os.path.relpath(fpath, dirpath),
                                "line": i,
                                "snippet": line.strip()[:300]
                            })
            except Exception:
                continue
    return {
        "pass": len(results) == 0,
        "details": results
    }

def scan_revealing_identifiers(dirpath: str) -> Dict[str, Any]:
    results: List[Dict[str, Any]] = []
    pattern = re.compile(r"[A-Za-z0-9_/-]*?(" + "|".join(map(re.escape, KEYWORDS_HINT)) + r")[A-Za-z0-9_/-]*")
    for root, _, files in os.walk(dirpath):
        for fn in files:
            lower = fn.lower()
            if any(lower.endswith(ext) for ext in [
                '.png','.jpg','.jpeg','.gif','.svg','.ico','.pdf',
                '.zip','.tar','.gz','.tgz','.7z','.jar','.war',
                '.pyc','.o','.so','.bin'
            ]):
                continue
            if any(lower.endswith(ext) for ext in DOC_EXT_SKIP):
                continue
            fpath = os.path.join(root, fn)
            try:
                with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                    for i, line in enumerate(f, start=1):
                        low = line.lower()
                        if not any(k in low for k in KEYWORDS_HINT):
                            continue
                        # Skip lines that appear to be only comments
                        if any(m in low for m in ['#','//','/*','<!--']):
                            continue
                        if (
                            'def ' in line or 'class ' in line or '=' in line or 'function ' in line or 'route(' in low or '@app.route' in low
                        ):
                            m = pattern.search(low)
                            if m:
                                results.append({
                                    "file": os.path.relpath(fpath, dirpath),
                                    "line": i,
                                    "identifier_like": m.group(0)[:120],
                                    "snippet": line.strip()[:300]
                                })
            except Exception:
                continue
    return {
        "pass": len(results) == 0,
        "details": results
    }

def scan_compose_healthchecks(bench_dir: str) -> Dict[str, Any]:
    compose_path = os.path.join(bench_dir, 'docker-compose.yml')
    if not os.path.exists(compose_path):
        return {"pass": False, "details": ["docker-compose.yml missing"]}
    text = read_text_safe(compose_path)
    has_health = 'healthcheck:' in text
    return {
        "pass": has_health,
        "details": ([] if has_health else ["No 'healthcheck' found in docker-compose.yml"]) 
    }

def scan_dockerfile_flag_arg(bench_dir: str) -> Dict[str, Any]:
    dockerfiles: List[str] = []
    for root, _, files in os.walk(bench_dir):
        for fn in files:
            if fn == 'Dockerfile' or fn.lower().endswith('.dockerfile'):
                dockerfiles.append(os.path.join(root, fn))
    if not dockerfiles:
        return {"pass": False, "details": ["No Dockerfile found"]}
    details: List[str] = []
    ok = True
    for df in dockerfiles:
        txt = read_text_safe(df)
        has_arg = re.search(r"^\s*ARG\s+flag\b", txt, flags=re.IGNORECASE | re.MULTILINE) is not None
        used = re.search(r"\$(?:\{?flag\}?)\b", txt, flags=re.IGNORECASE) is not None
        if not has_arg or not used:
            ok = False
        details.append(f"{os.path.relpath(df, bench_dir)}: ARG flag={'yes' if has_arg else 'no'}, used={'yes' if used else 'no'}")
    return {"pass": ok, "details": details}

def scan_config_description_leak(bench_dir: str) -> Dict[str, Any]:
    suspects = ['benchmark-config.json', 'benchmark.yaml', 'benchmark.yml']
    found = None
    for s in suspects:
        p = os.path.join(bench_dir, s)
        if os.path.exists(p):
            found = p
            break
    if not found:
        return {"pass": False, "details": ["No benchmark-config.json or benchmark.yaml found"]}
    description = None
    if found.endswith('.json'):
        try:
            with open(found, 'r', encoding='utf-8') as f:
                data = json.load(f)
            description = data.get('description')
        except Exception as e:
            return {"pass": False, "details": [f"Invalid JSON in {os.path.basename(found)}: {e}"]}
    else:
        # naive YAML extraction of description: the first non-comment line starting with 'description:'
        for line in read_text_safe(found).splitlines():
            if line.strip().startswith('#') or line.strip().startswith('//'):
                continue
            if line.strip().lower().startswith('description:'):
                description = line.split(':', 1)[1].strip().strip('"\'')
                break
    if description is None:
        return {"pass": False, "details": [f"No description found in {os.path.basename(found)}"]}
    low = str(description).lower()
    leak_terms = [
        'sqli','sql injection','xss','cross-site scripting','ssrf','idor','insecure direct object','rce','remote code execution',
        'path traversal','directory traversal','bypass','exploit','flag is','flag located','/flag','hardcoded'
    ]
    leaked = any(t in low for t in leak_terms)
    return {
        "pass": not leaked,
        "details": ([f"description contains potential leak: '{description}'"] if leaked else [])
    }

def scan_direct_flag_access(bench_dir: str) -> Dict[str, Any]:
    findings: List[str] = []
    # files named flag or flag.txt
    for root, _, files in os.walk(bench_dir):
        for fn in files:
            low = fn.lower()
            if low in ('flag', 'flag.txt', 'flag.md'):
                findings.append(os.path.relpath(os.path.join(root, fn), bench_dir))
    # Dockerfile COPY lines placing flag into web roots
    for root, _, files in os.walk(bench_dir):
        for fn in files:
            if fn == 'Dockerfile' or fn.lower().endswith('.dockerfile'):
                path = os.path.join(root, fn)
                for line in read_text_safe(path).splitlines():
                    low = line.lower()
                    if low.strip().startswith('copy') or low.strip().startswith('add'):
                        if 'flag' in low:
                            # try to split src dest; naive but good enough
                            parts = line.split()
                            if len(parts) >= 3:
                                dest = parts[-1]
                                if any(h in dest for h in WEB_ROOT_HINTS):
                                    findings.append(f"{os.path.relpath(path, bench_dir)}: {line.strip()}")
    return {
        "pass": len(findings) == 0,
        "details": findings
    }

def audit_benchmark(benchmarks_root: str, bench_name: str) -> Dict[str, Any]:
    bench_dir = os.path.join(benchmarks_root, bench_name)
    result: Dict[str, Any] = {
        "benchmark": bench_name,
        "checks": {}
    }
    result["checks"]["flag_hardcoded"] = scan_flag_hardcoded(bench_dir)
    result["checks"]["comment_hints"] = scan_comment_hints(bench_dir)
    result["checks"]["revealing_identifiers"] = scan_revealing_identifiers(bench_dir)
    result["checks"]["docker_compose_healthchecks"] = scan_compose_healthchecks(bench_dir)
    result["checks"]["dockerfile_flag_arg"] = scan_dockerfile_flag_arg(bench_dir)
    result["checks"]["config_description_leak"] = scan_config_description_leak(bench_dir)
    result["checks"]["direct_flag_access"] = scan_direct_flag_access(bench_dir)
    # App start check skipped in static environment
    result["checks"]["app_starts"] = {
        "pass": False,
        "status": "skipped",
        "details": ["Runtime start check skipped (no Docker in QA sandbox)"]
    }
    return result

def main() -> None:
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    benchmarks_root = os.path.join(repo_root, 'benchmarks')
    out_path = os.path.join(repo_root, 'docs', 'qa-audit-report.json')
    benches = list_benchmarks(benchmarks_root)
    report: Dict[str, Any] = {
        "summary": {
            "total": len(benches),
        },
        "benchmarks": []
    }
    total_passes: Dict[str, int] = {}
    for name in benches:
        res = audit_benchmark(benchmarks_root, name)
        report["benchmarks"].append(res)
        # aggregate
        for check, data in res["checks"].items():
            if check == 'app_starts' and data.get('status') == 'skipped':
                continue
            total_passes.setdefault(check, 0)
            if data.get('pass'):
                total_passes[check] += 1
    report["summary"]["passes_by_check"] = total_passes

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(out_path)

if __name__ == '__main__':
    main()
