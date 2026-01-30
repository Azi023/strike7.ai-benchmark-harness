#!/usr/bin/env python3
"""
Generate dashboard/data/benchmarks.json from config/benchmarks.yaml
with port mappings matching docker-compose.yml files.
"""
import json
import yaml
from pathlib import Path

# Port allocation ranges
PORT_RANGES = {
    'EASY': 5001,
    'MED': 5010,
    'HARD': 5030,
    'VHARD': 5050,
    'CVE': 5070,
}

def load_yaml_config():
    """Load benchmarks.yaml"""
    config_path = Path(__file__).parent.parent / 'config' / 'benchmarks.yaml'
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def generate_port_mapping():
    """Generate port mapping for all benchmarks"""
    config = load_yaml_config()
    port_map = {}

    # Group benchmarks by category
    by_category = {}
    for bench in config['benchmarks']:
        category = bench['category']
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(bench)

    # Assign sequential ports per category
    for category, benchmarks in by_category.items():
        base_port = PORT_RANGES.get(category, 5000)
        for idx, bench in enumerate(sorted(benchmarks, key=lambda x: x['id'])):
            port_map[bench['id']] = base_port + idx

    return port_map

def generate_benchmarks_json():
    """Generate complete benchmarks.json"""
    config = load_yaml_config()
    port_map = generate_port_mapping()

    benchmarks = []
    for bench in config['benchmarks']:
        bench_id = bench['id']
        benchmarks.append({
            'id': bench_id,
            'name': bench['name'],
            'category': bench['category'],
            'owasp_category': bench.get('owasp', 'N/A'),
            'cwe': bench.get('cwe', 'N/A'),
            'difficulty': bench.get('difficulty', 5),
            'port': port_map.get(bench_id, bench.get('port', 5000)),
            'flag_format': bench.get('flag_format', 'S7BEN{...}'),
            'phase': bench.get('phase', 1),
            'description': bench.get('description', ''),
            'hints': bench.get('hints', []),
        })

    return benchmarks

def main():
    """Main execution"""
    output_path = Path(__file__).parent.parent / 'data' / 'benchmarks.json'

    # Ensure data directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Generate benchmarks
    benchmarks = generate_benchmarks_json()

    # Write to file
    with open(output_path, 'w') as f:
        json.dump(benchmarks, f, indent=2)

    print(f"✅ Generated {len(benchmarks)} benchmarks to {output_path}")

    # Print port allocation summary
    by_category = {}
    for bench in benchmarks:
        cat = bench['category']
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(bench['port'])

    print("\n📊 Port Allocation Summary:")
    for cat, ports in sorted(by_category.items()):
        print(f"  {cat:6} → {min(ports)}-{max(ports)} ({len(ports)} benchmarks)")

if __name__ == '__main__':
    main()
