#!/usr/bin/env python3
import os
import re
import json
from typing import Dict, List, Any, Optional


RE_S7_DIR = re.compile(r"^S7BEN-[A-Z]+-\d{3}$")

XBOW_ROOT = os.path.join('third_party', 'xbow-validation-benchmarks')
XBOW_BENCH_ROOT = os.path.join(XBOW_ROOT, 'benchmarks')


def list_dirs(path: str, pattern: Optional[re.Pattern] = None) -> List[str]:
    out: List[str] = []
    if not os.path.isdir(path):
        return out
    for n in os.listdir(path):
        p = os.path.join(path, n)
        if os.path.isdir(p) and (pattern is None or pattern.match(n)):
            out.append(n)
    out.sort()
    return out


def read_text(path: str) -> str:
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except Exception:
        return ''


def s7_benchmarks(repo_root: str) -> List[str]:
    return list_dirs(os.path.join(repo_root, 'benchmarks'), RE_S7_DIR)


def find_files(dirpath: str, name: str) -> List[str]:
    hits: List[str] = []
    for root, _, files in os.walk(dirpath):
        for fn in files:
            if fn == name:
                hits.append(os.path.join(root, fn))
    return hits


def dockerfiles_under(dirpath: str) -> List[str]:
    hits: List[str] = []
    for root, _, files in os.walk(dirpath):
        for fn in files:
            low = fn.lower()
            if low == 'dockerfile' or low.endswith('.dockerfile'):
                hits.append(os.path.join(root, fn))
    return hits


def compose_has_build_services(compose_text: str) -> bool:
    return 'build:' in compose_text


def dockerfile_accepts_flag(dockerfile_text: str) -> Dict[str, Any]:
    has_arg_flag = re.search(r"^\s*ARG\s+flag\b", dockerfile_text, flags=re.IGNORECASE | re.MULTILINE) is not None
    uses_flag = re.search(r"\$(?:\{?flag\}?|\{?FLAG\}?)\b", dockerfile_text) is not None
    has_arg_FLAG = re.search(r"^\s*ARG\s+FLAG\b", dockerfile_text, flags=re.MULTILINE) is not None
    return {
        'has_ARG_flag': has_arg_flag,
        'has_ARG_FLAG': has_arg_FLAG,
        'uses_flag_var': uses_flag,
        'compatible': (has_arg_flag or has_arg_FLAG) and uses_flag
    }


def s7_metadata(bench_dir: str) -> Dict[str, Any]:
    # Parse tags from benchmark-config.json or benchmark.yaml/yml
    data: Dict[str, Any] = {'tags': [], 'level': None}
    json_path = os.path.join(bench_dir, 'benchmark-config.json')
    yaml_path = os.path.join(bench_dir, 'benchmark.yaml')
    if os.path.exists(json_path):
        try:
            j = json.loads(read_text(json_path))
            data['tags'] = j.get('tags') or []
            data['level'] = j.get('level')
        except Exception:
            pass
    elif os.path.exists(yaml_path):
        tags: List[str] = []
        level: Any = None
        lines = read_text(yaml_path).splitlines()
        in_tags = False
        for line in lines:
            s = line.strip()
            if s.startswith('#') or s.startswith('//'):
                continue
            if s.lower().startswith('tags:'):
                in_tags = True
                # inline list?
                rest = s[5:].strip()
                if rest.startswith('[') and rest.endswith(']'):
                    inner = rest[1:-1]
                    for it in inner.split(','):
                        val = it.strip().strip('"\'')
                        if val:
                            tags.append(val)
                    in_tags = False
                continue
            if in_tags:
                if s.startswith('- '):
                    val = s[2:].strip().strip('"\'')
                    if val:
                        tags.append(val)
                else:
                    in_tags = False
            if s.lower().startswith('level:'):
                lvl = s.split(':',1)[1].strip().strip('"\'')
                level = lvl
        data['tags'] = tags
        data['level'] = level
    return data


def xbow_metadata(bench_dir: str) -> Dict[str, Any]:
    # prefer benchmark.json
    path = os.path.join(bench_dir, 'benchmark.json')
    data: Dict[str, Any] = {'tags': [], 'level': None}
    try:
        j = json.loads(read_text(path))
        data['tags'] = j.get('tags') or []
        data['level'] = j.get('level')
    except Exception:
        pass
    return data


def analyze_xbow_structure(xbow_root: str) -> Dict[str, Any]:
    benches = list_dirs(os.path.join(xbow_root, 'benchmarks'))
    expected = {
        'docker-compose.yml': 0,
        'benchmark.json': 0,
        'benchmark.yaml': 0,
        'Makefile_includes_common_mk': 0
    }
    tags: set = set()
    levels: List[Any] = []
    for b in benches:
        d = os.path.join(xbow_root, 'benchmarks', b)
        if os.path.exists(os.path.join(d, 'docker-compose.yml')):
            expected['docker-compose.yml'] += 1
        if os.path.exists(os.path.join(d, 'benchmark.json')):
            expected['benchmark.json'] += 1
        if os.path.exists(os.path.join(d, 'benchmark.yaml')):
            expected['benchmark.yaml'] += 1
        mk = os.path.join(d, 'Makefile')
        if os.path.exists(mk) and '../../common.mk' in read_text(mk):
            expected['Makefile_includes_common_mk'] += 1
        md = xbow_metadata(d)
        for t in md['tags']:
            tags.add(t)
        if md['level'] is not None:
            levels.append(str(md['level']))
    return {
        'bench_count': len(benches),
        'expected_counts': expected,
        'unique_tags': sorted(list(tags)),
        'levels_used': sorted(list(set(levels))),
        'benchmarks': benches,
    }


def analyze_s7_compat(repo_root: str, xbow_root: str) -> Dict[str, Any]:
    benches = s7_benchmarks(repo_root)
    results: List[Dict[str, Any]] = []
    compat_summary = {'compatible_count': 0, 'total': len(benches)}
    structural_match = {'matches': 0, 'total': len(benches)}
    s7_tags: set = set()
    s7_levels: List[Any] = []

    for b in benches:
        bd = os.path.join(repo_root, 'benchmarks', b)
        has_compose = os.path.exists(os.path.join(bd, 'docker-compose.yml'))
        has_bjson = os.path.exists(os.path.join(bd, 'benchmark.json'))
        has_byaml = os.path.exists(os.path.join(bd, 'benchmark.yaml')) or os.path.exists(os.path.join(bd, 'benchmark.yml'))
        has_mk = os.path.exists(os.path.join(bd, 'Makefile'))
        mk_includes = False
        if has_mk:
            mk_text = read_text(os.path.join(bd, 'Makefile'))
            mk_includes = 'common.mk' in mk_text

        # Structural match to XBOW expected
        structural_ok = has_compose and has_bjson and has_mk and mk_includes
        if structural_ok:
            structural_match['matches'] += 1

        # Build compatibility via common.mk: require at least one Dockerfile that accepts ARG flag/FLAG and uses it
        accepts = []
        for df in dockerfiles_under(bd):
            info = dockerfile_accepts_flag(read_text(df))
            if info['compatible']:
                accepts.append({'dockerfile': os.path.relpath(df, bd), **info})
        compatible = has_compose and len(accepts) > 0
        if compatible:
            compat_summary['compatible_count'] += 1

        md = s7_metadata(bd)
        for t in md['tags']:
            s7_tags.add(t)
        if md['level'] is not None:
            s7_levels.append(str(md['level']))

        # Suggested changes per benchmark
        suggestions: List[str] = []
        if not has_bjson:
            suggestions.append('add benchmark.json (metadata) with tags, level, name, description')
        if has_mk and not mk_includes:
            suggestions.append('add Makefile line: include ../../common.mk')
        if not compatible:
            # derive which services need ARG
            if not accepts:
                suggestions.append('update Dockerfile(s) to include ARG flag or ARG FLAG and use it in app logic')
        if not has_compose:
            suggestions.append('add docker-compose.yml with build services and healthchecks')
        if not has_byaml:
            suggestions.append('add benchmark.yaml for pipeline metadata (optional)')

        results.append({
            'benchmark': b,
            'structure': {
                'docker_compose': has_compose,
                'benchmark_json': has_bjson,
                'benchmark_yaml': has_byaml,
                'makefile': has_mk,
                'makefile_includes_common_mk': mk_includes
            },
            'common_mk_build_compatible': compatible,
            'dockerfiles_accepting_flag': accepts,
            'suggested_changes': suggestions
        })

    return {
        'structural_match': structural_match,
        'compatibility': compat_summary,
        'results': results,
        'unique_tags': sorted(list(s7_tags)),
        'levels_used': sorted(list(set(s7_levels)))
    }


def compare_tags_and_categories(s7: Dict[str, Any], xbow: Dict[str, Any]) -> Dict[str, Any]:
    s7_tags = set(s7.get('unique_tags', []))
    x_tags = set(xbow.get('unique_tags', []))
    return {
        's7_tags_count': len(s7_tags),
        'xbow_tags_count': len(x_tags),
        'overlap': sorted(list(s7_tags & x_tags)),
        'only_in_s7': sorted(list(s7_tags - x_tags)),
        'only_in_xbow': sorted(list(x_tags - s7_tags))
    }


def build_report(repo_root: str) -> Dict[str, Any]:
    report: Dict[str, Any] = {'errors': []}
    if not os.path.isdir(XBOW_ROOT):
        report['errors'].append('XBOW repo not found at third_party/xbow-validation-benchmarks. Clone it before running.')
        return report
    xbow = analyze_xbow_structure(XBOW_ROOT)
    s7 = analyze_s7_compat(repo_root, XBOW_ROOT)
    report['summary'] = {
        'strike7_benchmarks': s7['compatibility']['total'],
        'xbow_benchmarks': xbow['bench_count'],
        'strike7_structural_match_to_xbow_expected': s7['structural_match'],
        'strike7_common_mk_build_compatibility': s7['compatibility'],
    }
    report['xbow_expected'] = xbow['expected_counts']
    report['compatibility_by_benchmark'] = s7['results']
    report['tag_coverage'] = compare_tags_and_categories(s7, xbow)
    # Categories: S7 uses folder names (EASY, MED, HARD, VHARD, CVE). XBOW uses level 1/2/3.
    # Summarize distributions
    s7_cat_counts: Dict[str, int] = {}
    for n in s7_benchmarks(repo_root):
        parts = n.split('-')
        if len(parts) >= 3:
            s7_cat_counts[parts[1]] = s7_cat_counts.get(parts[1], 0) + 1
    report['category_coverage'] = {
        'strike7': s7_cat_counts,
        'xbow_levels': xbow['levels_used']
    }
    return report


def main() -> None:
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    out_path = os.path.join(repo_root, 'docs', 'xbow-compatibility-report.json')
    rpt = build_report(repo_root)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(rpt, f, indent=2, ensure_ascii=False)
    print(out_path)


if __name__ == '__main__':
    main()
