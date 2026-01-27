#!/usr/bin/env python3
"""
Strike7 Benchmark Dashboard - Backend API
Provides REST API for benchmark management, filtering, and statistics
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import yaml
import os
import subprocess
import json
from datetime import datetime
from collections import Counter

# Import new API modules
from api.flag_submission import FlagValidator
from api.container_manager import ContainerManager
from api.session_tracker import SessionTracker
from api.metrics import MetricsTracker

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)  # Enable CORS for API access

# Configuration
BENCHMARKS_FILE = os.path.join(os.path.dirname(__file__), 'config', 'benchmarks.yaml')
BENCHMARKS_DIR = os.path.join(os.path.dirname(__file__), '..', 'benchmarks')

# Load benchmarks from YAML
def load_benchmarks():
    """Load all benchmarks from the registry YAML file"""
    try:
        with open(BENCHMARKS_FILE, 'r') as f:
            data = yaml.safe_load(f)
            return data.get('benchmarks', [])
    except Exception as e:
        print(f"Error loading benchmarks: {e}")
        return []

# Cache benchmarks in memory
BENCHMARKS_CACHE = load_benchmarks()

# Initialize API modules
flag_validator = FlagValidator(BENCHMARKS_CACHE)
container_manager = ContainerManager(BENCHMARKS_CACHE)
session_tracker = SessionTracker()
metrics_tracker = MetricsTracker()

@app.route('/')
def index():
    """Serve the main dashboard page"""
    return send_from_directory('templates', 'index.html')

@app.route('/api/benchmarks', methods=['GET'])
def get_benchmarks():
    """
    Get all benchmarks with optional filtering
    Query parameters:
    - category: Filter by category (EASY, MED, HARD, VHARD, CVE)
    - owasp: Filter by OWASP category (e.g., A01, A03)
    - difficulty: Filter by difficulty level (1-9)
    - cwe: Filter by CWE code
    - phase: Filter by phase number
    - search: Search in name/description
    """
    benchmarks = BENCHMARKS_CACHE.copy()

    # Apply filters
    category = request.args.get('category')
    if category:
        benchmarks = [b for b in benchmarks if b.get('category') == category.upper()]

    owasp = request.args.get('owasp')
    if owasp:
        benchmarks = [b for b in benchmarks if owasp.upper() in b.get('owasp', '')]

    difficulty = request.args.get('difficulty')
    if difficulty:
        try:
            diff = int(difficulty)
            benchmarks = [b for b in benchmarks if b.get('difficulty') == diff]
        except ValueError:
            pass

    cwe = request.args.get('cwe')
    if cwe:
        benchmarks = [b for b in benchmarks if cwe.upper() in b.get('cwe', '')]

    phase = request.args.get('phase')
    if phase:
        try:
            p = int(phase)
            benchmarks = [b for b in benchmarks if b.get('phase') == p]
        except ValueError:
            pass

    search = request.args.get('search')
    if search:
        search_lower = search.lower()
        benchmarks = [b for b in benchmarks
                     if search_lower in b.get('name', '').lower()
                     or search_lower in b.get('id', '').lower()]

    return jsonify({
        'total': len(benchmarks),
        'benchmarks': benchmarks
    })

@app.route('/api/benchmarks/<benchmark_id>', methods=['GET'])
def get_benchmark(benchmark_id):
    """Get a single benchmark by ID"""
    benchmark = next((b for b in BENCHMARKS_CACHE if b.get('id') == benchmark_id), None)
    if benchmark:
        return jsonify(benchmark)
    return jsonify({'error': 'Benchmark not found'}), 404

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """Get aggregated statistics across all benchmarks"""
    benchmarks = BENCHMARKS_CACHE

    # Count by category
    category_counts = Counter(b.get('category') for b in benchmarks)

    # Count by OWASP
    owasp_counts = Counter()
    for b in benchmarks:
        owasp = b.get('owasp', '')
        # Extract A01, A02, etc.
        if owasp:
            owasp_code = owasp.split(':')[0].split('-')[0].strip()
            owasp_counts[owasp_code] += 1

    # Count by difficulty
    difficulty_counts = Counter(b.get('difficulty') for b in benchmarks)

    # Count by CWE (top 10) - handle both string and list CWE values
    cwe_counts = Counter()
    for b in benchmarks:
        cwe = b.get('cwe')
        if cwe:
            # Handle CWE as list or string
            if isinstance(cwe, list):
                for c in cwe:
                    cwe_counts[c] += 1
            else:
                cwe_counts[cwe] += 1

    # Count by phase
    phase_counts = Counter(b.get('phase') for b in benchmarks)

    # Multi-container benchmarks
    multi_container = sum(1 for b in benchmarks if b.get('containers'))

    return jsonify({
        'total_benchmarks': len(benchmarks),
        'by_category': dict(category_counts),
        'by_owasp': dict(owasp_counts),
        'by_difficulty': dict(difficulty_counts),
        'by_cwe': dict(cwe_counts.most_common(10)),
        'by_phase': dict(phase_counts),
        'multi_container_count': multi_container,
        'generated_at': datetime.now().isoformat()
    })

@app.route('/api/statistics/owasp', methods=['GET'])
def get_owasp_coverage():
    """Get detailed OWASP Top 10 coverage"""
    benchmarks = BENCHMARKS_CACHE

    owasp_mapping = {
        'A01': 'Broken Access Control',
        'A02': 'Cryptographic Failures',
        'A03': 'Injection',
        'A04': 'Insecure Design',
        'A05': 'Security Misconfiguration',
        'A06': 'Vulnerable and Outdated Components',
        'A07': 'Identification and Authentication Failures',
        'A08': 'Software and Data Integrity Failures',
        'A09': 'Security Logging and Monitoring Failures',
        'A10': 'Server-Side Request Forgery (SSRF)'
    }

    coverage = {}
    for code, name in owasp_mapping.items():
        count = sum(1 for b in benchmarks if code in b.get('owasp', ''))
        coverage[code] = {
            'name': name,
            'count': count,
            'percentage': round((count / len(benchmarks)) * 100, 1) if benchmarks else 0
        }

    return jsonify({
        'coverage': coverage,
        'total_categories': len([c for c in coverage.values() if c['count'] > 0]),
        'total_benchmarks': len(benchmarks)
    })

@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Get list of all categories with counts"""
    benchmarks = BENCHMARKS_CACHE
    category_info = {}

    for category in ['EASY', 'MED', 'HARD', 'VHARD', 'CVE']:
        count = sum(1 for b in benchmarks if b.get('category') == category)
        category_info[category] = {
            'count': count,
            'percentage': round((count / len(benchmarks)) * 100, 1) if benchmarks else 0
        }

    return jsonify(category_info)

@app.route('/api/benchmark/<benchmark_id>/status', methods=['GET'])
def get_benchmark_status(benchmark_id):
    """Check if a benchmark container is running"""
    try:
        # Get benchmark info
        benchmark = next((b for b in BENCHMARKS_CACHE if b.get('id') == benchmark_id), None)
        if not benchmark:
            return jsonify({'error': 'Benchmark not found'}), 404

        # Check Docker container status
        container_name = benchmark_id.lower().replace('_', '-')
        result = subprocess.run(
            ['docker', 'ps', '--filter', f'name={container_name}', '--format', '{{.Status}}'],
            capture_output=True,
            text=True
        )

        is_running = bool(result.stdout.strip())

        return jsonify({
            'benchmark_id': benchmark_id,
            'running': is_running,
            'status': result.stdout.strip() if is_running else 'stopped',
            'port': benchmark.get('port')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/benchmark/<benchmark_id>/telemetry', methods=['GET'])
def get_benchmark_telemetry(benchmark_id):
    """Get telemetry data from a running benchmark"""
    try:
        benchmark = next((b for b in BENCHMARKS_CACHE if b.get('id') == benchmark_id), None)
        if not benchmark:
            return jsonify({'error': 'Benchmark not found'}), 404

        port = benchmark.get('port', 5000)

        # Try to fetch telemetry from the benchmark
        import requests
        try:
            response = requests.get(f'http://localhost:{port}/telemetry', timeout=2)
            if response.status_code == 200:
                return jsonify(response.json())
        except:
            pass

        return jsonify({
            'error': 'Telemetry not available',
            'benchmark_id': benchmark_id,
            'port': port
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'benchmarks_loaded': len(BENCHMARKS_CACHE),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/reload', methods=['POST'])
def reload_benchmarks():
    """Reload benchmarks from YAML file"""
    global BENCHMARKS_CACHE, flag_validator, container_manager
    BENCHMARKS_CACHE = load_benchmarks()
    # Reinitialize API modules with new data
    flag_validator = FlagValidator(BENCHMARKS_CACHE)
    container_manager = ContainerManager(BENCHMARKS_CACHE)
    return jsonify({
        'status': 'reloaded',
        'count': len(BENCHMARKS_CACHE),
        'timestamp': datetime.now().isoformat()
    })


# ===== NEW API ENDPOINTS - TASK B =====

@app.route('/api/benchmark/<benchmark_id>/submit-flag', methods=['POST'])
def submit_flag(benchmark_id):
    """
    Submit a flag for validation
    Request body: {"flag": "S7BEN{...}", "agent_id": "...", "session_id": "..."}
    """
    try:
        data = request.get_json() or {}
        submitted_flag = data.get('flag')
        session_id = data.get('session_id')
        agent_id = data.get('agent_id')

        if not submitted_flag:
            return jsonify({
                'status': 'error',
                'message': 'Flag is required'
            }), 400

        # Validate flag
        result = flag_validator.validate_flag(benchmark_id, submitted_flag, session_id)

        # Record attempt in session if session_id provided
        if session_id and result.get('correct') is not None:
            session_tracker.record_attempt(
                session_id,
                benchmark_id,
                result['correct']
            )

        # Record attempt in metrics system if agent_id provided
        if agent_id and session_id:
            metrics_tracker.record_attempt(
                session_id=session_id,
                agent_id=agent_id,
                benchmark_id=benchmark_id,
                success=result.get('correct', False),
                time_to_flag=result.get('time_to_capture'),
                tool_calls=data.get('tool_calls'),
                tokens_used=data.get('tokens_used'),
                detected=data.get('detected', False),
                metadata=data.get('metadata')
            )

        # Return appropriate status code
        if result['status'] == 'error' and 'not found' in result.get('message', '').lower():
            return jsonify(result), 404
        elif result['correct']:
            return jsonify(result), 200
        else:
            return jsonify(result), 200  # Still 200, just incorrect flag

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/benchmark/<benchmark_id>/start', methods=['POST'])
def start_benchmark(benchmark_id):
    """
    Start a benchmark container
    Request body: {"force_stop_others": true, "timeout_minutes": 30}
    """
    try:
        data = request.get_json() or {}
        force_stop_others = data.get('force_stop_others', True)
        timeout_minutes = data.get('timeout_minutes')

        result = container_manager.start_container(
            benchmark_id,
            force_stop_others=force_stop_others,
            timeout_minutes=timeout_minutes
        )

        # Mark container start time for flag validation timing
        if result['status'] == 'success':
            flag_validator.mark_container_started(benchmark_id)

        status_code = 200 if result['status'] == 'success' else 400
        return jsonify(result), status_code

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'benchmark_id': benchmark_id
        }), 500


@app.route('/api/benchmark/<benchmark_id>/stop', methods=['POST'])
def stop_benchmark(benchmark_id):
    """Stop a benchmark container"""
    try:
        result = container_manager.stop_container(benchmark_id)

        # Mark container stopped for flag validation
        if result['status'] == 'success':
            flag_validator.mark_container_stopped(benchmark_id)

        status_code = 200 if result['status'] == 'success' else 400
        return jsonify(result), status_code

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'benchmark_id': benchmark_id
        }), 500


@app.route('/api/containers/status', methods=['GET'])
def get_containers_status():
    """Get status of all running containers and system resources"""
    try:
        running = container_manager.get_running_containers()
        system = container_manager.get_system_status()

        return jsonify({
            'running_count': len(running),
            'max_allowed': container_manager.config['max_concurrent'],
            'containers': running,
            'system': system
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/containers/stop-all', methods=['POST'])
def stop_all_containers():
    """Emergency stop all benchmark containers"""
    try:
        stopped = container_manager.stop_all_containers()

        return jsonify({
            'status': 'success',
            'stopped_count': len(stopped),
            'stopped_benchmarks': [c['benchmark_id'] for c in stopped]
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/session/start', methods=['POST'])
def start_session():
    """
    Start a new evaluation session
    Request body: {
        "agent_id": "strike7-agent-001",
        "benchmark_filter": {...},
        "settings": {...}
    }
    """
    try:
        data = request.get_json() or {}
        agent_id = data.get('agent_id', 'anonymous')
        benchmark_filter = data.get('benchmark_filter')
        settings = data.get('settings')

        result = session_tracker.start_session(
            agent_id,
            benchmark_filter=benchmark_filter,
            settings=settings
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/session/<session_id>/end', methods=['POST'])
def end_session(session_id):
    """End an evaluation session"""
    try:
        result = session_tracker.end_session(session_id)

        status_code = 200 if result['status'] == 'success' else 404
        return jsonify(result), status_code

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/session/<session_id>/progress', methods=['GET'])
def get_session_progress(session_id):
    """Get current progress for a session"""
    try:
        result = session_tracker.get_session_progress(session_id)

        if result.get('status') == 'error':
            return jsonify(result), 404

        return jsonify(result)

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/sessions', methods=['GET'])
def get_sessions():
    """Get all sessions (optionally filter to active only)"""
    try:
        active_only = request.args.get('active_only', 'false').lower() == 'true'
        sessions = session_tracker.get_all_sessions(active_only=active_only)

        return jsonify({
            'count': len(sessions),
            'sessions': sessions
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    """Get leaderboard of best performing sessions"""
    try:
        limit = request.args.get('limit', 10, type=int)
        leaderboard = session_tracker.get_leaderboard(limit=limit)

        return jsonify({
            'count': len(leaderboard),
            'leaderboard': leaderboard
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


# ===== EVALUATION METRICS ENDPOINTS =====

@app.route('/api/metrics/attempt', methods=['POST'])
def record_attempt():
    """
    Record a benchmark attempt for metrics tracking

    Request body:
    {
        "session_id": "...",
        "agent_id": "...",
        "benchmark_id": "...",
        "success": true/false,
        "time_to_flag": 123.45,  // seconds
        "tool_calls": 15,
        "tokens_used": 5000,
        "detected": false,
        "metadata": {}  // optional additional data
    }
    """
    try:
        data = request.get_json() or {}

        required = ['session_id', 'agent_id', 'benchmark_id', 'success']
        missing = [f for f in required if f not in data]
        if missing:
            return jsonify({
                'status': 'error',
                'message': f'Missing required fields: {", ".join(missing)}'
            }), 400

        attempt = metrics_tracker.record_attempt(
            session_id=data['session_id'],
            agent_id=data['agent_id'],
            benchmark_id=data['benchmark_id'],
            success=data['success'],
            time_to_flag=data.get('time_to_flag'),
            tool_calls=data.get('tool_calls'),
            tokens_used=data.get('tokens_used'),
            detected=data.get('detected', False),
            metadata=data.get('metadata')
        )

        return jsonify({
            'status': 'recorded',
            'attempt': attempt
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/metrics/pass-at-k', methods=['GET'])
def get_pass_at_k():
    """
    Calculate pass@k metric

    Query parameters:
    - agent_id: Filter by agent (optional)
    - benchmark_id: Filter by benchmark (optional)
    - k: Number of attempts to consider (default: 3)
    """
    try:
        agent_id = request.args.get('agent_id')
        benchmark_id = request.args.get('benchmark_id')
        k = int(request.args.get('k', 3))

        result = metrics_tracker.calculate_pass_at_k(
            agent_id=agent_id,
            benchmark_id=benchmark_id,
            k=k
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/metrics/pass-pow-k', methods=['GET'])
def get_pass_pow_k():
    """
    Calculate pass^k metric (consecutive success rate)

    Query parameters:
    - agent_id: Filter by agent (optional)
    - k: Window size for consecutive attempts (default: 3)
    """
    try:
        agent_id = request.args.get('agent_id')
        k = int(request.args.get('k', 3))

        result = metrics_tracker.calculate_pass_pow_k(
            agent_id=agent_id,
            k=k
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/metrics/ttf', methods=['GET'])
def get_ttf_stats():
    """
    Get Time-to-Flag (TTF) statistics

    Query parameters:
    - agent_id: Filter by agent (optional)
    - benchmark_id: Filter by benchmark (optional)
    """
    try:
        agent_id = request.args.get('agent_id')
        benchmark_id = request.args.get('benchmark_id')

        result = metrics_tracker.calculate_ttf_stats(
            agent_id=agent_id,
            benchmark_id=benchmark_id
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/metrics/efficiency', methods=['GET'])
def get_efficiency_metrics():
    """
    Get efficiency metrics (tool calls, tokens, time)

    Query parameters:
    - agent_id: Filter by agent (optional)
    - benchmark_id: Filter by benchmark (optional)
    """
    try:
        agent_id = request.args.get('agent_id')
        benchmark_id = request.args.get('benchmark_id')

        result = metrics_tracker.calculate_efficiency_metrics(
            agent_id=agent_id,
            benchmark_id=benchmark_id
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/metrics/stealth', methods=['GET'])
def get_stealth_score():
    """
    Get stealth score (detection avoidance)

    Query parameters:
    - agent_id: Filter by agent (optional)
    - benchmark_id: Filter by benchmark (optional)
    """
    try:
        agent_id = request.args.get('agent_id')
        benchmark_id = request.args.get('benchmark_id')

        result = metrics_tracker.calculate_stealth_score(
            agent_id=agent_id,
            benchmark_id=benchmark_id
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/metrics/leaderboard', methods=['GET'])
def get_metrics_leaderboard():
    """
    Get agent leaderboard sorted by metric

    Query parameters:
    - metric: Metric to sort by (pass@3, ttf, efficiency, stealth)
    - limit: Number of agents to return (default: 10)
    """
    try:
        metric = request.args.get('metric', 'pass@3')
        limit = int(request.args.get('limit', 10))

        result = metrics_tracker.get_agent_leaderboard(
            metric=metric,
            limit=limit
        )

        return jsonify({
            'metric': metric,
            'limit': limit,
            'leaderboard': result
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/metrics/benchmark-difficulty', methods=['GET'])
def get_benchmark_difficulty():
    """Get benchmark difficulty analysis based on success rates"""
    try:
        result = metrics_tracker.get_benchmark_difficulty_analysis()
        return jsonify(result)

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/metrics/dashboard', methods=['GET'])
def get_metrics_dashboard():
    """
    Get comprehensive metrics dashboard data

    Query parameters:
    - agent_id: Filter by agent (optional)
    """
    try:
        agent_id = request.args.get('agent_id')

        # Calculate all metrics
        pass_at_1 = metrics_tracker.calculate_pass_at_k(agent_id=agent_id, k=1)
        pass_at_3 = metrics_tracker.calculate_pass_at_k(agent_id=agent_id, k=3)
        pass_at_5 = metrics_tracker.calculate_pass_at_k(agent_id=agent_id, k=5)
        pass_pow_3 = metrics_tracker.calculate_pass_pow_k(agent_id=agent_id, k=3)
        ttf = metrics_tracker.calculate_ttf_stats(agent_id=agent_id)
        efficiency = metrics_tracker.calculate_efficiency_metrics(agent_id=agent_id)
        stealth = metrics_tracker.calculate_stealth_score(agent_id=agent_id)
        leaderboard = metrics_tracker.get_agent_leaderboard(metric='pass@3', limit=10)
        difficulty = metrics_tracker.get_benchmark_difficulty_analysis()

        return jsonify({
            'agent_id': agent_id,
            'timestamp': datetime.now().isoformat(),
            'metrics': {
                'pass_at_1': pass_at_1,
                'pass_at_3': pass_at_3,
                'pass_at_5': pass_at_5,
                'pass_pow_3': pass_pow_3,
                'time_to_flag': ttf,
                'efficiency': efficiency,
                'stealth': stealth
            },
            'leaderboard': leaderboard,
            'benchmark_difficulty': difficulty
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


if __name__ == '__main__':
    print(f"[+] Strike7 Dashboard API starting...")
    print(f"[+] Loaded {len(BENCHMARKS_CACHE)} benchmarks")
    print(f"[+] Dashboard will be available at http://localhost:5500")
    app.run(host='0.0.0.0', port=5500, debug=True, threaded=True, use_reloader=False)
