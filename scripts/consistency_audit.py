#!/usr/bin/env python3
import os
import re
import json
from typing import Dict, List, Any, Tuple


RE_BENCHMARK_DIR = re.compile(r"^S7BEN-[A-Z]+-\d{3}$")

DOC_SKIP_EXT = {'.png','.jpg','.jpeg','.gif','.svg','.ico','.pdf','.zip','.tar','.gz','.tgz','.7z','.jar','.war','.pyc','.o','.so','.bin'}


def list_benchmarks(root: str) -> List[str]:
    out = []
    for name in os.listdir(root):
        p = os.path.join(root, name)
        if os.path.isdir(p) and RE_BENCHMARK_DIR.match(name):
            out.append(name)
    out.sort()
    return out


def read_text(path: str) -> str:
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except Exception:
        return ''


def find_files(dirpath: str, name: str) -> List[str]:
    hits: List[str] = []
    for root, _, files in os.walk(dirpath):
        for fn in files:
            if fn == name:
                hits.append(os.path.join(root, fn))
    return hits


def find_like_dockerfiles(dirpath: str) -> List[str]:
    hits: List[str] = []
    for root, _, files in os.walk(dirpath):
        for fn in files:
            low = fn.lower()
            if low == 'dockerfile' or low.endswith('.dockerfile') or low.startswith('dockerfile.'):
                hits.append(os.path.join(root, fn))
            if low in ('dockerfile.old','dockerfile.bak','dockerfile.backup'):
                hits.append(os.path.join(root, fn))
    return hits


def has_config(bench_dir: str) -> Dict[str, Any]:
    candidates = ['benchmark-config.json','benchmark.yaml','benchmark.yml']
    found: List[str] = []
    for c in candidates:
        p = os.path.join(bench_dir, c)
        if os.path.exists(p):
            found.append(c)
    return {
        'pass': len(found) >= 1,
        'found': found
    }


def parse_compose_ports(compose_path: str) -> List[str]:
    # returns list of mapping strings as written (e.g., "8080:8080" or "127.0.0.1:8080:80")
    text = read_text(compose_path)
    mappings: List[str] = []
    for line in text.splitlines():
        l = line.strip()
        if not l or l.lstrip().startswith('#'):
            continue
        # list form: - "host:container"
        if l.startswith('- '):
            val = l[2:].strip().strip('"\'')
            if re.match(r"^\d+(?::\d+){1,2}$", val) or re.match(r"^[0-9.]+:\d+:\d+$", val) or re.match(r"^\d+/tcp$", val) or re.match(r"^\d+$", val):
                mappings.append(val)
        # inline YAML array: ["8080:8080"] already captured above when parsed as lines in file
    return mappings


def check_port_convention(mappings: List[str]) -> Dict[str, Any]:
    # Convention: prefer host==container numeric (e.g., 8090:8090) without IP binds.
    # Evaluate all ports: if any mapping not host==container, mark inconsistent.
    inconsistent: List[str] = []
    analyzed: List[Dict[str, Any]] = []
    for m in mappings:
        info = {'mapping': m, 'host_eq_container': False, 'ip_bound': False}
        if re.match(r"^[0-9.]+:\d+:\d+$", m):
            info['ip_bound'] = True
            host, cport = m.split(':')[-2:]
            info['host_eq_container'] = (host == cport)
        elif re.match(r"^\d+:\d+$", m):
            h, c = m.split(':', 1)
            info['host_eq_container'] = (h == c)
        elif re.match(r"^\d+$", m) or re.match(r"^\d+/tcp$", m):
            # container-only publish; treat as inconsistent with convention
            info['host_eq_container'] = False
        else:
            info['host_eq_container'] = False
        analyzed.append(info)
        if not info['host_eq_container'] or info['ip_bound']:
            inconsistent.append(m)
    return {
        'pass': len(inconsistent) == 0,
        'details': {
            'inconsistent_mappings': inconsistent,
            'analyzed': analyzed
        }
    }


def check_makefile_targets(bench_dir: str) -> Dict[str, Any]:
    mk_path = os.path.join(bench_dir, 'Makefile')
    if not os.path.exists(mk_path):
        return {'pass': False, 'details': ['Makefile missing'], 'missing_targets': ['up','down','test']}
    text = read_text(mk_path)
    targets = set()
    for m in re.finditer(r"^([a-zA-Z0-9_-]+):", text, flags=re.MULTILINE):
        targets.add(m.group(1))
    required = ['up','down','test']
    missing = [t for t in required if t not in targets]
    # common optional ones
    optional = ['build','logs','restart','clean']
    return {
        'pass': len(missing) == 0,
        'missing_targets': missing,
        'present_optional': [t for t in optional if t in targets],
        'all_targets': sorted(list(targets))
    }


def scan_flag_formats(bench_dir: str) -> Dict[str, Any]:
    formats = {'S7BEN{':0, 'S7{':0, 'SBEN{':0}
    locations: List[Dict[str, Any]] = []
    for root, _, files in os.walk(bench_dir):
        for fn in files:
            low = fn.lower()
            if any(low.endswith(ext) for ext in DOC_SKIP_EXT):
                continue
            fpath = os.path.join(root, fn)
            try:
                with open(fpath,'r',encoding='utf-8',errors='ignore') as f:
                    for i, line in enumerate(f, start=1):
                        for key in list(formats.keys()):
                            if key in line:
                                formats[key] += 1
                                locations.append({'file': os.path.relpath(fpath, bench_dir), 'line': i, 'match': key})
            except Exception:
                continue
    used = [k for k,v in formats.items() if v>0]
    # Consistency rule: prefer S7BEN{...} or S7{...}; SBEN{ is inconsistent.
    inconsistent = 'SBEN{' in used
    return {
        'pass': (len(used) == 0) or (not inconsistent),
        'found_formats': {k:v for k,v in formats.items() if v>0},
        'locations': locations,
        'has_sben': 'SBEN{' in used
    }


def find_orphaned_dockerfiles(bench_dir: str) -> Dict[str, Any]:
    compose_path = os.path.join(bench_dir, 'docker-compose.yml')
    compose_text = read_text(compose_path) if os.path.exists(compose_path) else ''
    dockerfiles = find_like_dockerfiles(bench_dir)
    orphans: List[str] = []
    extras: List[str] = []
    for df in dockerfiles:
        rel = os.path.relpath(df, bench_dir)
        name = os.path.basename(df)
        # If explicitly referenced in compose via 'dockerfile: <name>' keep it
        if f"dockerfile: {name}" in compose_text or f"dockerfile: ./{rel}" in compose_text or f"dockerfile: {rel}" in compose_text:
            continue
        # default Dockerfile in a build context will be used implicitly; collect extras
        if name.lower() not in ('dockerfile',):
            extras.append(rel)
        # Mark obviously old/backup as orphaned
        if name.lower() in ('dockerfile.old','dockerfile.bak','dockerfile.backup') or name.lower().startswith('dockerfile.old'):
            orphans.append(rel)
    return {
        'pass': len(orphans) == 0,
        'orphans': orphans,
        'extras': extras,
        'all_dockerfiles': [os.path.relpath(p, bench_dir) for p in dockerfiles]
    }


def audit_benchmark(bench_root: str, name: str) -> Dict[str, Any]:
    bench_dir = os.path.join(bench_root, name)
    res: Dict[str, Any] = {'benchmark': name, 'checks': {}}
    # 1. Config presence
    res['checks']['config_present'] = has_config(bench_dir)
    # 2. Port convention in compose
    compose_path = os.path.join(bench_dir, 'docker-compose.yml')
    if os.path.exists(compose_path):
        mappings = parse_compose_ports(compose_path)
        res['checks']['compose_port_convention'] = check_port_convention(mappings)
        res['checks']['compose_ports_found'] = mappings
    else:
        res['checks']['compose_port_convention'] = {'pass': False, 'details': {'error': 'docker-compose.yml missing'}}
        res['checks']['compose_ports_found'] = []
    # 3. Flag format consistency
    res['checks']['flag_formats'] = scan_flag_formats(bench_dir)
    # 4. Makefile structure
    res['checks']['makefile_targets'] = check_makefile_targets(bench_dir)
    # 5. Orphaned/extra Dockerfiles
    res['checks']['orphaned_dockerfiles'] = find_orphaned_dockerfiles(bench_dir)
    return res


def main() -> None:
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    bench_root = os.path.join(repo_root, 'benchmarks')
    out_path = os.path.join(repo_root, 'docs', 'consistency-report.json')
    names = list_benchmarks(bench_root)
    report: Dict[str, Any] = {'summary': {'total': len(names)}, 'benchmarks': []}
    aggregate = {
        'config_present': 0,
        'compose_port_convention': 0,
        'flag_formats_clean': 0,
        'makefile_targets_ok': 0,
        'no_orphaned_dockerfiles': 0
    }
    for n in names:
        item = audit_benchmark(bench_root, n)
        report['benchmarks'].append(item)
        if item['checks']['config_present']['pass']:
            aggregate['config_present'] += 1
        if item['checks']['compose_port_convention']['pass']:
            aggregate['compose_port_convention'] += 1
        if item['checks']['flag_formats']['pass'] and not item['checks']['flag_formats']['has_sben']:
            aggregate['flag_formats_clean'] += 1
        if item['checks']['makefile_targets']['pass']:
            aggregate['makefile_targets_ok'] += 1
        if item['checks']['orphaned_dockerfiles']['pass']:
            aggregate['no_orphaned_dockerfiles'] += 1
    report['summary']['passes_by_check'] = aggregate
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(out_path)


if __name__ == '__main__':
    main()

