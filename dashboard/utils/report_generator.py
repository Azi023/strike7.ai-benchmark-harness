"""
Auto-generate markdown benchmark performance reports from comparison run data.

Pure-function module — no Flask/DB dependencies.  All data passed as arguments.
"""
from datetime import datetime, timezone

# Tier ordering for sorting
_TIER_ORDER = {'EASY': 0, 'MED': 1, 'HARD': 2, 'VHARD': 3, 'CVE': 4}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fmt_time(seconds):
    """Format seconds into human-readable string."""
    if seconds is None:
        return '--'
    seconds = float(seconds)
    if seconds < 60:
        return f"{seconds:.0f}s"
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins}m {secs}s"


def _fmt_pct(ratio):
    """Format a 0-1 ratio as a percentage string."""
    if ratio is None:
        return '--'
    return f"{ratio * 100:.1f}%"


def _fmt_delta(current, previous):
    """Format numeric delta with sign."""
    if current is None or previous is None:
        return '--'
    d = current - previous
    if d > 0:
        return f"+{d:.1f}"
    return f"{d:.1f}"


def _safe_div(n, d, default=0):
    """Safe division — returns default when d is zero."""
    if not d:
        return default
    return n / d


def _benchmark_sort_key(benchmark_id):
    """Sort key: (tier_index, number)."""
    parts = benchmark_id.replace('S7BEN-', '').split('-')
    tier = parts[0] if parts else ''
    try:
        num = int(parts[1]) if len(parts) > 1 else 0
    except ValueError:
        num = 0
    return (_TIER_ORDER.get(tier, 99), num)


def _lookup_meta(benchmark_id, meta_list):
    """Find benchmark metadata dict by id, or return empty dict."""
    for m in (meta_list or []):
        if m.get('id') == benchmark_id:
            return m
    return {}


def _group_by(items, key_fn):
    """Group a list of dicts by key_fn result."""
    groups = {}
    for item in items:
        k = key_fn(item)
        groups.setdefault(k, []).append(item)
    return groups


# ---------------------------------------------------------------------------
# Section generators (all return markdown strings)
# ---------------------------------------------------------------------------

def _report_header(filters, campaign_info):
    lines = ['# Strike7 — Benchmark Performance Report', '']

    meta = []
    meta.append(f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")

    if campaign_info:
        if campaign_info.get('campaign_name'):
            meta.append(f"**Campaign:** {campaign_info['campaign_name']}")
        if campaign_info.get('product_name'):
            meta.append(f"**Product:** {campaign_info['product_name']}")

    if filters:
        if filters.get('product_name') and not campaign_info:
            meta.append(f"**Product:** {filters['product_name']}")
        if filters.get('provider'):
            meta.append(f"**Provider:** {filters['provider']}")
        if filters.get('difficulty_tier'):
            meta.append(f"**Tier:** {filters['difficulty_tier']}")
        if filters.get('model_name'):
            meta.append(f"**Model:** {filters['model_name']}")

    for m in meta:
        lines.append(m)
    lines.append('')
    lines.append('---')
    lines.append('')
    return '\n'.join(lines)


def _executive_summary(runs, previous_runs):
    total = len(runs)
    captured = sum(1 for r in runs if r.get('flag_captured'))
    rate = _safe_div(captured, total)

    success_times = [r['total_duration_s'] for r in runs
                     if r.get('flag_captured') and r.get('total_duration_s') is not None]
    fail_times = [r['total_duration_s'] for r in runs
                  if not r.get('flag_captured') and r.get('total_duration_s') is not None]

    avg_success = _safe_div(sum(success_times), len(success_times)) if success_times else None
    avg_fail = _safe_div(sum(fail_times), len(fail_times)) if fail_times else None

    lines = ['## Executive Summary', '']

    summary = f"**{captured}/{total}** flags captured (**{_fmt_pct(rate)}** pass rate)"
    if avg_success is not None:
        summary += f" — successful exploits averaged **{_fmt_time(avg_success)}**"
    if avg_fail is not None:
        summary += f", failures averaged **{_fmt_time(avg_fail)}**"

    lines.append(summary)

    if previous_runs:
        prev_total = len(previous_runs)
        prev_captured = sum(1 for r in previous_runs if r.get('flag_captured'))
        prev_rate = _safe_div(prev_captured, prev_total)
        delta = rate - prev_rate
        direction = 'improvement' if delta > 0 else 'regression' if delta < 0 else 'no change'
        lines.append('')
        lines.append(f"vs. previous: {_fmt_pct(prev_rate)} → {_fmt_pct(rate)} ({_fmt_delta(rate * 100, prev_rate * 100)}pp {direction})")

    lines.extend(['', '---', ''])
    return '\n'.join(lines)


def _coverage_table(runs, previous_runs):
    total = len(runs)
    captured = sum(1 for r in runs if r.get('flag_captured'))
    failed = total - captured

    success_times = [r['total_duration_s'] for r in runs
                     if r.get('flag_captured') and r.get('total_duration_s') is not None]
    fail_times = [r['total_duration_s'] for r in runs
                  if not r.get('flag_captured') and r.get('total_duration_s') is not None]
    success_steps = [r['steps_taken'] for r in runs
                     if r.get('flag_captured') and r.get('steps_taken') is not None]
    fail_steps = [r['steps_taken'] for r in runs
                  if not r.get('flag_captured') and r.get('steps_taken') is not None]

    lines = ['## Test Coverage', '',
             '| Metric | Value |',
             '|--------|-------|']
    lines.append(f"| Total Benchmarks Attempted | {total} |")
    lines.append(f"| Flags Captured | {captured} |")
    lines.append(f"| Flags Missed | {failed} |")
    lines.append(f"| **Overall Pass Rate** | **{_fmt_pct(_safe_div(captured, total))}** |")

    if success_times:
        lines.append(f"| Avg Time to Flag (successes) | {_fmt_time(_safe_div(sum(success_times), len(success_times)))} |")
    if fail_times:
        lines.append(f"| Avg Time on Failures | {_fmt_time(_safe_div(sum(fail_times), len(fail_times)))} |")
    if success_steps:
        lines.append(f"| Avg Steps (successes) | {_safe_div(sum(success_steps), len(success_steps)):.1f} |")
    if fail_steps:
        lines.append(f"| Avg Steps (failures) | {_safe_div(sum(fail_steps), len(fail_steps)):.1f} |")

    # Cost summary
    costs = [r['cost_usd'] for r in runs if r.get('cost_usd') is not None]
    if costs:
        lines.append(f"| Total Cost | ${sum(costs):.4f} |")
        lines.append(f"| Avg Cost per Run | ${_safe_div(sum(costs), len(costs)):.4f} |")
    else:
        lines.append("| Cost Data | Not available |")

    lines.extend(['', '---', ''])
    return '\n'.join(lines)


def _per_benchmark_table(runs, benchmarks_meta, previous_runs):
    sorted_runs = sorted(runs, key=lambda r: _benchmark_sort_key(r.get('benchmark_id', '')))

    prev_map = {}
    if previous_runs:
        for r in previous_runs:
            prev_map[r.get('benchmark_id')] = r

    lines = ['## Per-Benchmark Breakdown', '',
             '| # | Benchmark ID | Application | OWASP | Result | Time | Steps |',
             '|---|-------------|-------------|-------|--------|------|-------|']

    for i, r in enumerate(sorted_runs, 1):
        bid = r.get('benchmark_id', '')
        meta = _lookup_meta(bid, benchmarks_meta)
        name = meta.get('name', r.get('benchmark_name', ''))
        owasp = meta.get('owasp_category', r.get('vuln_category', '')) or ''
        # Shorten OWASP display
        if ':' in owasp:
            owasp = owasp.split(' - ')[0] if ' - ' in owasp else owasp.split(':')[0]

        captured = r.get('flag_captured')
        result = '**CAPTURED**' if captured else 'FAILED'
        time_str = _fmt_time(r.get('total_duration_s'))
        steps = r.get('steps_taken', '--')

        # Add delta indicator vs previous
        prev = prev_map.get(bid)
        if prev:
            prev_captured = prev.get('flag_captured')
            if captured and not prev_captured:
                result += ' (NEW)'
            elif not captured and prev_captured:
                result += ' (REGR)'

        lines.append(f"| {i} | {bid} | {name} | {owasp} | {result} | {time_str} | {steps} |")

    lines.extend(['', '---', ''])
    return '\n'.join(lines)


def _performance_by_outcome(runs):
    captured_runs = [r for r in runs if r.get('flag_captured')]
    failed_runs = [r for r in runs if not r.get('flag_captured')]

    def _agg(subset):
        times = [r['total_duration_s'] for r in subset if r.get('total_duration_s') is not None]
        steps = [r['steps_taken'] for r in subset if r.get('steps_taken') is not None]
        return {
            'count': len(subset),
            'avg_time': _safe_div(sum(times), len(times)) if times else None,
            'avg_steps': _safe_div(sum(steps), len(steps)) if steps else None,
            'min_time': min(times) if times else None,
            'max_time': max(times) if times else None,
        }

    cap = _agg(captured_runs)
    fail = _agg(failed_runs)

    lines = ['## Performance by Outcome', '',
             '| Outcome | Count | Avg Time | Avg Steps | Min Time | Max Time |',
             '|---------|-------|----------|-----------|----------|----------|']

    for label, a in [('**Captured**', cap), ('**Failed**', fail)]:
        lines.append(
            f"| {label} | {a['count']} "
            f"| {_fmt_time(a['avg_time'])} "
            f"| {a['avg_steps']:.1f} " if a['avg_steps'] is not None else f"| {label} | {a['count']} | {_fmt_time(a['avg_time'])} | -- "
        )

    # Rebuild properly to avoid partial ternary issues
    lines = ['## Performance by Outcome', '',
             '| Outcome | Count | Avg Time | Avg Steps | Min Time | Max Time |',
             '|---------|-------|----------|-----------|----------|----------|']

    for label, a in [('**Captured**', cap), ('**Failed**', fail)]:
        avg_steps_str = f"{a['avg_steps']:.1f}" if a['avg_steps'] is not None else '--'
        lines.append(
            f"| {label} | {a['count']} | {_fmt_time(a['avg_time'])} "
            f"| {avg_steps_str} | {_fmt_time(a['min_time'])} | {_fmt_time(a['max_time'])} |"
        )

    lines.extend(['', '---', ''])
    return '\n'.join(lines)


def _vulnerability_analysis(runs, benchmarks_meta):
    # Group runs by OWASP category
    def _get_owasp(r):
        meta = _lookup_meta(r.get('benchmark_id', ''), benchmarks_meta)
        owasp = meta.get('owasp_category', r.get('vuln_category', 'Unknown'))
        return owasp or 'Unknown'

    groups = _group_by(runs, _get_owasp)

    lines = ['## Vulnerability Category Analysis', '',
             '| OWASP / Category | Attempted | Captured | Pass Rate |',
             '|-----------------|-----------|----------|-----------|']

    for cat in sorted(groups.keys()):
        group_runs = groups[cat]
        attempted = len(group_runs)
        captured = sum(1 for r in group_runs if r.get('flag_captured'))
        rate = _fmt_pct(_safe_div(captured, attempted))
        lines.append(f"| {cat} | {attempted} | {captured} | {rate} |")

    lines.extend(['', '---', ''])
    return '\n'.join(lines)


def _speed_profile(runs):
    fast = [r for r in runs if r.get('total_duration_s') is not None and r['total_duration_s'] < 60]
    medium = [r for r in runs if r.get('total_duration_s') is not None and 60 <= r['total_duration_s'] < 180]
    slow = [r for r in runs if r.get('total_duration_s') is not None and r['total_duration_s'] >= 180]

    lines = ['## Speed Profile', '']

    for label, subset in [('Fast (< 60s)', fast), ('Medium (60-180s)', medium), ('Slow (> 180s)', slow)]:
        if subset:
            ids = ', '.join(r.get('benchmark_id', '?') for r in subset)
            captured = sum(1 for r in subset if r.get('flag_captured'))
            lines.append(f"- **{label}:** {len(subset)} runs ({captured} captured) — {ids}")

    lines.extend(['', '---', ''])
    return '\n'.join(lines)


def _failure_analysis_section(failure_data, runs):
    lines = ['## Failure Analysis', '']

    if not failure_data:
        lines.append('No failure taxonomy data available.')
        lines.extend(['', '---', ''])
        return '\n'.join(lines)

    # Stage funnel
    stage_funnel = failure_data.get('stage_funnel', [])
    if stage_funnel:
        lines.extend([
            '### Failure Stage Funnel', '',
            '| Stage | Count |',
            '|-------|-------|',
        ])
        for entry in stage_funnel:
            lines.append(f"| {entry.get('stage', '?')} | {entry.get('count', 0)} |")
        lines.append('')

    # Reason breakdown
    reason_breakdown = failure_data.get('reason_breakdown', [])
    if reason_breakdown:
        lines.extend([
            '### Top Failure Reasons', '',
            '| Reason | Stage | Count |',
            '|--------|-------|-------|',
        ])
        for entry in sorted(reason_breakdown, key=lambda x: -x.get('count', 0))[:10]:
            lines.append(
                f"| {entry.get('reason', '?')} | {entry.get('stage', '?')} | {entry.get('count', 0)} |"
            )
        lines.append('')

    lines.extend(['---', ''])
    return '\n'.join(lines)


def _efficiency_metrics(runs):
    captured_runs = [r for r in runs if r.get('flag_captured')]
    failed_runs = [r for r in runs if not r.get('flag_captured')]

    def _avg(subset, field):
        vals = [r[field] for r in subset if r.get(field) is not None]
        return _safe_div(sum(vals), len(vals)) if vals else None

    lines = ['## Efficiency Metrics', '',
             '| Metric | Captures | Failures | Delta |',
             '|--------|----------|----------|-------|']

    metrics = [
        ('Avg time', 'total_duration_s', 's'),
        ('Avg steps', 'steps_taken', ''),
        ('Avg tokens', 'total_tokens', ''),
        ('Avg cost', 'cost_usd', '$'),
    ]

    for label, field, prefix in metrics:
        cap_val = _avg(captured_runs, field)
        fail_val = _avg(failed_runs, field)

        def _fmt_val(v, pfx):
            if v is None:
                return '--'
            if pfx == '$':
                return f"${v:.4f}"
            if pfx == 's':
                return _fmt_time(v)
            return f"{v:.1f}"

        cap_str = _fmt_val(cap_val, prefix)
        fail_str = _fmt_val(fail_val, prefix)

        if cap_val is not None and fail_val is not None and cap_val > 0:
            multiplier = fail_val / cap_val
            delta_str = f"{multiplier:.1f}x"
        else:
            delta_str = '--'

        lines.append(f"| {label} | {cap_str} | {fail_str} | {delta_str} |")

    lines.extend(['', '---', ''])
    return '\n'.join(lines)


def _regression_analysis(runs, previous_runs):
    if not previous_runs:
        return ''

    lines = ['## Regression Analysis', '']

    current_map = {r.get('benchmark_id'): r for r in runs}
    previous_map = {r.get('benchmark_id'): r for r in previous_runs}

    common = set(current_map.keys()) & set(previous_map.keys())
    if not common:
        lines.append('No overlapping benchmarks found for comparison.')
        lines.extend(['', '---', ''])
        return '\n'.join(lines)

    improvements = []
    regressions = []
    time_deltas = []

    for bid in sorted(common, key=_benchmark_sort_key):
        curr = current_map[bid]
        prev = previous_map[bid]

        curr_pass = bool(curr.get('flag_captured'))
        prev_pass = bool(prev.get('flag_captured'))

        if curr_pass and not prev_pass:
            improvements.append(bid)
        elif not curr_pass and prev_pass:
            regressions.append(bid)

        curr_time = curr.get('total_duration_s')
        prev_time = prev.get('total_duration_s')
        if curr_time is not None and prev_time is not None:
            time_deltas.append((bid, curr_time - prev_time))

    lines.append(f"**Benchmarks compared:** {len(common)}")
    lines.append('')

    if improvements:
        lines.append(f"### Improvements (FAIL → PASS): {len(improvements)}")
        for bid in improvements:
            lines.append(f"- {bid}")
        lines.append('')

    if regressions:
        lines.append(f"### Regressions (PASS → FAIL): {len(regressions)}")
        for bid in regressions:
            lines.append(f"- {bid}")
        lines.append('')

    if time_deltas:
        lines.append('### Time Deltas')
        lines.append('')
        lines.append('| Benchmark | Delta | Direction |')
        lines.append('|-----------|-------|-----------|')
        for bid, delta in time_deltas:
            direction = 'faster' if delta < 0 else 'slower' if delta > 0 else 'same'
            lines.append(f"| {bid} | {_fmt_delta(delta, 0)}s | {direction} |")
        lines.append('')

    lines.extend(['---', ''])
    return '\n'.join(lines)


def _data_gaps(runs):
    missing_tokens = sum(1 for r in runs if r.get('total_tokens') is None)
    missing_cost = sum(1 for r in runs if r.get('cost_usd') is None)
    missing_failure = sum(1 for r in runs
                         if not r.get('flag_captured') and not r.get('failure_reason'))
    missing_stage = sum(1 for r in runs
                        if not r.get('flag_captured') and not r.get('failure_stage'))
    total = len(runs)

    gaps = []
    if missing_tokens:
        gaps.append(('No token data', f"{missing_tokens}/{total} runs",
                      'Cannot calculate cost efficiency'))
    if missing_cost:
        gaps.append(('No cost data', f"{missing_cost}/{total} runs",
                      'Cannot compare cost-per-flag'))
    if missing_failure:
        gaps.append(('No failure_reason', f"{missing_failure} failed runs",
                      'Failures not classified'))
    if missing_stage:
        gaps.append(('No failure_stage', f"{missing_stage} failed runs",
                      'Cannot build failure funnel'))

    if not gaps:
        return ''

    lines = ['## Data Gaps', '',
             '| Gap | Affected | Impact |',
             '|-----|----------|--------|']
    for gap, affected, impact in gaps:
        lines.append(f"| {gap} | {affected} | {impact} |")

    lines.extend(['', '---', ''])
    return '\n'.join(lines)


def _recommendations(runs, failure_data, previous_runs):
    lines = ['## Recommendations', '']
    total = len(runs)
    captured = sum(1 for r in runs if r.get('flag_captured'))
    rate = _safe_div(captured, total)

    short_term = []
    medium_term = []
    long_term = []

    # Token/cost gaps
    missing_tokens = sum(1 for r in runs if r.get('total_tokens') is None)
    if missing_tokens > total * 0.5:
        short_term.append('Instrument token tracking to enable cost analysis')

    # Low pass rate
    if rate < 0.5:
        short_term.append('Investigate failing benchmarks — pass rate below 50%')
    elif rate < 0.7:
        medium_term.append('Target failing benchmarks for improvement — pass rate below 70%')

    # Failures without classification
    unclassified = sum(1 for r in runs
                       if not r.get('flag_captured') and not r.get('failure_reason'))
    if unclassified:
        short_term.append(f'Classify {unclassified} untagged failures with failure_reason/failure_stage')

    # Regression-detected items
    if previous_runs:
        current_map = {r.get('benchmark_id'): r for r in runs}
        previous_map = {r.get('benchmark_id'): r for r in previous_runs}
        regressions = [bid for bid in set(current_map) & set(previous_map)
                       if not current_map[bid].get('flag_captured')
                       and previous_map[bid].get('flag_captured')]
        if regressions:
            short_term.append(f"Investigate {len(regressions)} regressions: {', '.join(regressions)}")

    # Failure funnel insights
    if failure_data:
        stages = {e.get('stage'): e.get('count', 0)
                  for e in failure_data.get('stage_funnel', [])}
        worst_stage = max(stages, key=stages.get) if stages else None
        if worst_stage:
            medium_term.append(f"Most failures occur at '{worst_stage}' stage — focus improvement here")

    # General long-term
    long_term.append('Run multi-attempt campaigns (3+ per benchmark) to measure consistency')
    if total < 20:
        medium_term.append(f'Expand test coverage — only {total} benchmarks tested')

    if short_term:
        lines.append('### Short-Term')
        for i, item in enumerate(short_term, 1):
            lines.append(f"{i}. {item}")
        lines.append('')

    if medium_term:
        lines.append('### Medium-Term')
        for i, item in enumerate(medium_term, 1):
            lines.append(f"{i}. {item}")
        lines.append('')

    if long_term:
        lines.append('### Long-Term')
        for i, item in enumerate(long_term, 1):
            lines.append(f"{i}. {item}")
        lines.append('')

    lines.extend(['---', ''])
    return '\n'.join(lines)


def _run_metadata_appendix(runs):
    if not runs:
        return ''

    sorted_runs = sorted(runs, key=lambda r: r.get('run_timestamp', ''))

    lines = ['## Appendix: Run Metadata', '',
             '| Benchmark | Run ID | Timestamp |',
             '|-----------|--------|-----------|']

    for r in sorted_runs:
        bid = r.get('benchmark_id', '?')
        rid = r.get('run_id', '?')
        # Truncate run_id for readability
        rid_short = rid[:8] if len(rid) > 8 else rid
        ts = r.get('run_timestamp', '?')
        lines.append(f"| {bid} | `{rid_short}` | {ts} |")

    lines.append('')
    return '\n'.join(lines)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_report(runs, benchmarks_meta, failure_data=None,
                    previous_runs=None, filters=None, campaign_info=None):
    """Generate a complete markdown benchmark report.

    Args:
        runs: list of run dicts (from model_benchmark_runs)
        benchmarks_meta: list of benchmark metadata dicts (from benchmarks.json)
        failure_data: dict with stage_funnel / reason_breakdown (from failure-analysis API)
        previous_runs: list of previous run dicts for regression comparison
        filters: dict of active filters (product_name, provider, etc.)
        campaign_info: dict with campaign metadata (campaign_name, product_name, etc.)

    Returns:
        Complete markdown report as a string.
    """
    sections = [
        _report_header(filters, campaign_info),
        _executive_summary(runs, previous_runs),
        _coverage_table(runs, previous_runs),
        _per_benchmark_table(runs, benchmarks_meta, previous_runs),
        _performance_by_outcome(runs),
        _vulnerability_analysis(runs, benchmarks_meta),
        _speed_profile(runs),
        _failure_analysis_section(failure_data, runs),
        _efficiency_metrics(runs),
        _regression_analysis(runs, previous_runs),
        _data_gaps(runs),
        _recommendations(runs, failure_data, previous_runs),
        _run_metadata_appendix(runs),
    ]

    return '\n'.join(section for section in sections if section)
