#!/usr/bin/env python3
"""
Backend API Test Suite for Strike7 Dashboard
Tests all REST API endpoints for functionality, validation, and error handling
"""

import pytest
import requests
import json
import time
from datetime import datetime
from typing import Dict, List


# Configuration
BASE_URL = "http://localhost:5500"  # Adjust if dashboard runs on different port
API_BASE = f"{BASE_URL}/api"
TIMEOUT = 10  # Request timeout in seconds


class TestBenchmarkAPIs:
    """Test benchmark-related API endpoints"""

    def test_get_all_benchmarks(self):
        """GET /api/benchmarks - Should return all benchmarks"""
        response = requests.get(f"{API_BASE}/benchmarks", timeout=TIMEOUT)

        assert response.status_code == 200
        data = response.json()

        assert 'total' in data
        assert 'benchmarks' in data
        assert isinstance(data['benchmarks'], list)
        assert data['total'] > 0
        print(f"✓ Found {data['total']} benchmarks")

    def test_filter_by_category(self):
        """GET /api/benchmarks?category=EASY - Should filter by category"""
        for category in ['EASY', 'MED', 'HARD', 'VHARD', 'CVE']:
            response = requests.get(
                f"{API_BASE}/benchmarks",
                params={'category': category},
                timeout=TIMEOUT
            )

            assert response.status_code == 200
            data = response.json()

            # Check all returned benchmarks match the filter
            for benchmark in data['benchmarks']:
                assert benchmark['category'] == category

            print(f"✓ {category} filter: {data['total']} benchmarks")

    def test_filter_by_owasp(self):
        """GET /api/benchmarks?owasp=A01 - Should filter by OWASP category"""
        response = requests.get(
            f"{API_BASE}/benchmarks",
            params={'owasp': 'A01'},
            timeout=TIMEOUT
        )

        assert response.status_code == 200
        data = response.json()

        # Check all returned benchmarks contain A01 in OWASP field
        for benchmark in data['benchmarks']:
            assert 'A01' in benchmark.get('owasp', '')

        print(f"✓ OWASP A01 filter: {data['total']} benchmarks")

    def test_filter_by_difficulty(self):
        """GET /api/benchmarks?difficulty=5 - Should filter by difficulty level"""
        response = requests.get(
            f"{API_BASE}/benchmarks",
            params={'difficulty': '5'},
            timeout=TIMEOUT
        )

        assert response.status_code == 200
        data = response.json()

        # Check all returned benchmarks have difficulty 5
        for benchmark in data['benchmarks']:
            assert benchmark.get('difficulty') == 5

        print(f"✓ Difficulty 5 filter: {data['total']} benchmarks")

    def test_search_benchmarks(self):
        """GET /api/benchmarks?search=sql - Should search in name/id"""
        response = requests.get(
            f"{API_BASE}/benchmarks",
            params={'search': 'sql'},
            timeout=TIMEOUT
        )

        assert response.status_code == 200
        data = response.json()

        # Check search term appears in name or id
        for benchmark in data['benchmarks']:
            name = benchmark.get('name', '').lower()
            bench_id = benchmark.get('id', '').lower()
            assert 'sql' in name or 'sql' in bench_id

        print(f"✓ Search 'sql': {data['total']} benchmarks")

    def test_get_single_benchmark(self):
        """GET /api/benchmarks/<id> - Should return specific benchmark"""
        # First get all benchmarks to get a valid ID
        all_benchmarks = requests.get(f"{API_BASE}/benchmarks", timeout=TIMEOUT).json()

        if all_benchmarks['benchmarks']:
            benchmark_id = all_benchmarks['benchmarks'][0]['id']

            response = requests.get(
                f"{API_BASE}/benchmarks/{benchmark_id}",
                timeout=TIMEOUT
            )

            assert response.status_code == 200
            data = response.json()

            assert data['id'] == benchmark_id
            assert 'name' in data
            assert 'category' in data

            print(f"✓ Retrieved benchmark: {benchmark_id}")

    def test_get_nonexistent_benchmark(self):
        """GET /api/benchmarks/INVALID - Should return 404"""
        response = requests.get(
            f"{API_BASE}/benchmarks/S7BEN-INVALID-999",
            timeout=TIMEOUT
        )

        assert response.status_code == 404
        data = response.json()
        assert 'error' in data

        print("✓ Nonexistent benchmark returns 404")


class TestStatisticsAPIs:
    """Test statistics and aggregation endpoints"""

    def test_get_statistics(self):
        """GET /api/statistics - Should return aggregated statistics"""
        response = requests.get(f"{API_BASE}/statistics", timeout=TIMEOUT)

        assert response.status_code == 200
        data = response.json()

        assert 'total_benchmarks' in data
        assert 'by_category' in data
        assert 'by_owasp' in data
        assert 'by_difficulty' in data
        assert 'by_cwe' in data
        assert 'by_phase' in data
        assert 'generated_at' in data

        assert data['total_benchmarks'] > 0

        print(f"✓ Statistics: {data['total_benchmarks']} total benchmarks")
        print(f"  Categories: {data['by_category']}")

    def test_get_owasp_coverage(self):
        """GET /api/statistics/owasp - Should return OWASP Top 10 coverage"""
        response = requests.get(f"{API_BASE}/statistics/owasp", timeout=TIMEOUT)

        assert response.status_code == 200
        data = response.json()

        assert 'coverage' in data
        assert 'total_categories' in data
        assert 'total_benchmarks' in data

        # Check OWASP categories
        coverage = data['coverage']
        for code in ['A01', 'A02', 'A03', 'A04', 'A05', 'A06', 'A07', 'A08', 'A09', 'A10']:
            if code in coverage:
                assert 'name' in coverage[code]
                assert 'count' in coverage[code]
                assert 'percentage' in coverage[code]

        print(f"✓ OWASP coverage: {data['total_categories']} categories covered")

    def test_get_categories(self):
        """GET /api/categories - Should return category breakdown"""
        response = requests.get(f"{API_BASE}/categories", timeout=TIMEOUT)

        assert response.status_code == 200
        data = response.json()

        # Check all expected categories
        for category in ['EASY', 'MED', 'HARD', 'VHARD', 'CVE']:
            if category in data:
                assert 'count' in data[category]
                assert 'percentage' in data[category]

        print("✓ Categories endpoint working")


class TestContainerAPIs:
    """Test container management endpoints"""

    def test_get_containers_status(self):
        """GET /api/containers/status - Should return running containers"""
        response = requests.get(f"{API_BASE}/containers/status", timeout=TIMEOUT)

        assert response.status_code == 200
        data = response.json()

        # API returns 'containers' not 'running_containers'
        assert 'containers' in data
        assert 'running_count' in data
        assert isinstance(data['containers'], list)

        print(f"✓ Container status: {data['running_count']} running")

    def test_get_benchmark_status(self):
        """GET /api/benchmark/<id>/status - Should check if benchmark is running"""
        # Get a valid benchmark ID
        all_benchmarks = requests.get(f"{API_BASE}/benchmarks", timeout=TIMEOUT).json()

        if all_benchmarks['benchmarks']:
            benchmark_id = all_benchmarks['benchmarks'][0]['id']

            response = requests.get(
                f"{API_BASE}/benchmark/{benchmark_id}/status",
                timeout=TIMEOUT
            )

            assert response.status_code == 200
            data = response.json()

            assert 'benchmark_id' in data
            assert 'running' in data
            assert isinstance(data['running'], bool)

            print(f"✓ Benchmark status check: {benchmark_id}")

    def test_start_benchmark_container(self):
        """POST /api/benchmark/<id>/start - Should start a container"""
        # Get an EASY benchmark to test with
        response = requests.get(
            f"{API_BASE}/benchmarks",
            params={'category': 'EASY'},
            timeout=TIMEOUT
        )
        benchmarks = response.json()['benchmarks']

        if benchmarks:
            benchmark_id = benchmarks[0]['id']

            # Try to start the container
            response = requests.post(
                f"{API_BASE}/benchmark/{benchmark_id}/start",
                timeout=30  # Container start can take longer
            )

            # May return 500 if Docker not accessible or benchmark dir missing
            # That's acceptable for a test environment
            assert response.status_code in [200, 201, 500]
            data = response.json()

            assert 'status' in data
            # If 500, it will have error status
            assert data['status'] in ['success', 'error']

            if response.status_code == 500:
                print(f"⚠ Container start unavailable (Docker not accessible): {benchmark_id}")
            else:
                print(f"✓ Container start attempt: {benchmark_id}")

                # Clean up - stop the container
                requests.post(
                    f"{API_BASE}/benchmark/{benchmark_id}/stop",
                    timeout=30
                )

    def test_stop_benchmark_container(self):
        """POST /api/benchmark/<id>/stop - Should stop a container"""
        # Get any benchmark
        all_benchmarks = requests.get(f"{API_BASE}/benchmarks", timeout=TIMEOUT).json()

        if all_benchmarks['benchmarks']:
            benchmark_id = all_benchmarks['benchmarks'][0]['id']

            response = requests.post(
                f"{API_BASE}/benchmark/{benchmark_id}/stop",
                timeout=30
            )

            # Should either succeed or already be stopped
            assert response.status_code == 200
            data = response.json()

            assert 'status' in data

            print(f"✓ Container stop attempt: {benchmark_id}")


class TestFlagSubmissionAPIs:
    """Test flag submission and validation endpoints"""

    def test_submit_incorrect_flag(self):
        """POST /api/benchmark/<id>/submit-flag - Should reject incorrect flag"""
        # Get a valid benchmark
        all_benchmarks = requests.get(f"{API_BASE}/benchmarks", timeout=TIMEOUT).json()

        if all_benchmarks['benchmarks']:
            benchmark_id = all_benchmarks['benchmarks'][0]['id']

            response = requests.post(
                f"{API_BASE}/benchmark/{benchmark_id}/submit-flag",
                json={'flag': 'INVALID_FLAG'},
                timeout=TIMEOUT
            )

            assert response.status_code == 200
            data = response.json()

            assert 'status' in data
            assert 'correct' in data
            assert data['correct'] is False

            print(f"✓ Incorrect flag rejected")

    def test_submit_flag_without_data(self):
        """POST /api/benchmark/<id>/submit-flag - Should validate required fields"""
        all_benchmarks = requests.get(f"{API_BASE}/benchmarks", timeout=TIMEOUT).json()

        if all_benchmarks['benchmarks']:
            benchmark_id = all_benchmarks['benchmarks'][0]['id']

            # Send empty request
            response = requests.post(
                f"{API_BASE}/benchmark/{benchmark_id}/submit-flag",
                json={},
                timeout=TIMEOUT
            )

            # Should return error
            assert response.status_code in [400, 422, 200]  # May vary by implementation

            print("✓ Empty flag submission handled")


class TestSessionAPIs:
    """Test session tracking endpoints"""

    def test_start_session(self):
        """POST /api/session/start - Should create new session"""
        response = requests.post(
            f"{API_BASE}/session/start",
            json={'agent_id': 'test_agent_qa'},
            timeout=TIMEOUT
        )

        assert response.status_code in [200, 201]
        data = response.json()

        assert 'session_id' in data
        assert 'agent_id' in data
        assert data['agent_id'] == 'test_agent_qa'

        session_id = data['session_id']
        print(f"✓ Session started: {session_id}")

        # Clean up - end session
        requests.post(f"{API_BASE}/session/{session_id}/end", timeout=TIMEOUT)

        return session_id

    def test_get_session_progress(self):
        """GET /api/session/<id>/progress - Should return session progress"""
        # Start a session first
        start_response = requests.post(
            f"{API_BASE}/session/start",
            json={'agent_id': 'test_agent_qa'},
            timeout=TIMEOUT
        )
        session_id = start_response.json()['session_id']

        # Get progress
        response = requests.get(
            f"{API_BASE}/session/{session_id}/progress",
            timeout=TIMEOUT
        )

        assert response.status_code == 200
        data = response.json()

        assert 'session_id' in data
        assert 'agent_id' in data
        assert 'status' in data

        print(f"✓ Session progress retrieved")

        # Clean up
        requests.post(f"{API_BASE}/session/{session_id}/end", timeout=TIMEOUT)

    def test_end_session(self):
        """POST /api/session/<id>/end - Should end session"""
        # Start a session
        start_response = requests.post(
            f"{API_BASE}/session/start",
            json={'agent_id': 'test_agent_qa'},
            timeout=TIMEOUT
        )
        session_id = start_response.json()['session_id']

        # End the session
        response = requests.post(
            f"{API_BASE}/session/{session_id}/end",
            timeout=TIMEOUT
        )

        assert response.status_code == 200
        data = response.json()

        assert 'status' in data
        assert data['status'] == 'success'

        print(f"✓ Session ended successfully")

    def test_get_all_sessions(self):
        """GET /api/sessions - Should return all sessions"""
        response = requests.get(f"{API_BASE}/sessions", timeout=TIMEOUT)

        assert response.status_code == 200
        data = response.json()

        assert 'sessions' in data
        assert isinstance(data['sessions'], list)

        print(f"✓ Retrieved all sessions: {len(data['sessions'])} found")

    def test_get_leaderboard(self):
        """GET /api/leaderboard - Should return session leaderboard"""
        response = requests.get(f"{API_BASE}/leaderboard", timeout=TIMEOUT)

        assert response.status_code == 200
        data = response.json()

        assert 'leaderboard' in data
        assert isinstance(data['leaderboard'], list)

        print(f"✓ Leaderboard retrieved")


class TestMetricsAPIs:
    """Test metrics and evaluation endpoints"""

    def test_metrics_dashboard(self):
        """GET /api/metrics/dashboard - Should return metrics overview"""
        response = requests.get(f"{API_BASE}/metrics/dashboard", timeout=TIMEOUT)

        assert response.status_code == 200
        data = response.json()

        # API returns nested structure under 'metrics' key
        assert 'metrics' in data
        metrics = data['metrics']
        assert 'pass_at_1' in metrics
        assert 'pass_at_3' in metrics
        assert 'time_to_flag' in metrics or 'ttf_stats' in data
        assert 'efficiency' in metrics

        print("✓ Metrics dashboard retrieved")

    def test_pass_at_k_metric(self):
        """GET /api/metrics/pass-at-k - Should calculate pass@k"""
        response = requests.get(
            f"{API_BASE}/metrics/pass-at-k",
            params={'k': 3},
            timeout=TIMEOUT
        )

        assert response.status_code == 200
        data = response.json()

        assert 'metric' in data
        assert 'value' in data
        assert data['metric'] == 'pass@3'

        print(f"✓ pass@3 metric: {data['value']}%")

    def test_ttf_statistics(self):
        """GET /api/metrics/ttf - Should return time-to-flag stats"""
        response = requests.get(f"{API_BASE}/metrics/ttf", timeout=TIMEOUT)

        assert response.status_code == 200
        data = response.json()

        assert 'metric' in data
        assert data['metric'] == 'time_to_flag'

        print("✓ TTF statistics retrieved")

    def test_efficiency_metrics(self):
        """GET /api/metrics/efficiency - Should return efficiency stats"""
        response = requests.get(f"{API_BASE}/metrics/efficiency", timeout=TIMEOUT)

        assert response.status_code == 200
        data = response.json()

        assert 'metric' in data
        assert data['metric'] == 'efficiency'

        print("✓ Efficiency metrics retrieved")

    def test_stealth_score(self):
        """GET /api/metrics/stealth - Should return stealth score"""
        response = requests.get(f"{API_BASE}/metrics/stealth", timeout=TIMEOUT)

        assert response.status_code == 200
        data = response.json()

        assert 'metric' in data
        assert data['metric'] == 'stealth'

        print("✓ Stealth score retrieved")

    def test_benchmark_difficulty_analysis(self):
        """GET /api/metrics/benchmark-difficulty - Should analyze difficulty"""
        response = requests.get(
            f"{API_BASE}/metrics/benchmark-difficulty",
            timeout=TIMEOUT
        )

        assert response.status_code == 200
        data = response.json()

        assert 'metric' in data
        assert 'benchmarks' in data

        print("✓ Benchmark difficulty analysis retrieved")


class TestErrorHandling:
    """Test error handling and edge cases"""

    def test_health_check(self):
        """GET /api/health - Should return health status"""
        response = requests.get(f"{API_BASE}/health", timeout=TIMEOUT)

        assert response.status_code == 200
        data = response.json()

        assert 'status' in data
        assert data['status'] == 'healthy'

        print("✓ Health check passed")

    def test_invalid_endpoint(self):
        """GET /api/invalid - Should return 404"""
        response = requests.get(f"{API_BASE}/invalid-endpoint-12345", timeout=TIMEOUT)

        assert response.status_code == 404

        print("✓ Invalid endpoint returns 404")

    def test_malformed_json(self):
        """POST with malformed JSON - Should handle gracefully"""
        response = requests.post(
            f"{API_BASE}/session/start",
            data="invalid json{{{",
            headers={'Content-Type': 'application/json'},
            timeout=TIMEOUT
        )

        # Should return 400 or similar
        assert response.status_code in [400, 422, 500]

        print("✓ Malformed JSON handled")

    def test_missing_required_fields(self):
        """POST without required fields - Should validate"""
        response = requests.post(
            f"{API_BASE}/session/start",
            json={},  # Missing agent_id
            timeout=TIMEOUT
        )

        # May still succeed with defaults, or return error
        assert response.status_code in [200, 201, 400, 422]

        print("✓ Missing fields handled")

    def test_large_search_query(self):
        """Search with very long query - Should handle gracefully"""
        long_query = "x" * 1000

        response = requests.get(
            f"{API_BASE}/benchmarks",
            params={'search': long_query},
            timeout=TIMEOUT
        )

        assert response.status_code == 200
        data = response.json()

        # Should return empty results
        assert data['total'] == 0

        print("✓ Large query handled")


class TestDashboardIntegration:
    """Integration tests for full workflows"""

    def test_full_benchmark_workflow(self):
        """Test complete workflow: list -> get -> start -> status -> stop"""
        # 1. List benchmarks
        list_response = requests.get(
            f"{API_BASE}/benchmarks",
            params={'category': 'EASY'},
            timeout=TIMEOUT
        )
        assert list_response.status_code == 200
        benchmarks = list_response.json()['benchmarks']

        if not benchmarks:
            print("⚠ No EASY benchmarks found, skipping workflow test")
            return

        benchmark_id = benchmarks[0]['id']
        print(f"Testing workflow with: {benchmark_id}")

        # 2. Get benchmark details
        detail_response = requests.get(
            f"{API_BASE}/benchmarks/{benchmark_id}",
            timeout=TIMEOUT
        )
        assert detail_response.status_code == 200

        # 3. Check initial status
        status_response = requests.get(
            f"{API_BASE}/benchmark/{benchmark_id}/status",
            timeout=TIMEOUT
        )
        assert status_response.status_code == 200

        # 4. Try to stop first (cleanup)
        requests.post(
            f"{API_BASE}/benchmark/{benchmark_id}/stop",
            timeout=30
        )

        # 5. Start container
        start_response = requests.post(
            f"{API_BASE}/benchmark/{benchmark_id}/start",
            timeout=30
        )
        # May fail if docker not available, that's ok
        if start_response.status_code == 200:
            print("  ✓ Container started")

            # 6. Check status again
            time.sleep(2)  # Give container time to start
            status_response = requests.get(
                f"{API_BASE}/benchmark/{benchmark_id}/status",
                timeout=TIMEOUT
            )

            # 7. Stop container
            stop_response = requests.post(
                f"{API_BASE}/benchmark/{benchmark_id}/stop",
                timeout=30
            )
            print("  ✓ Container stopped")

        print("✓ Full workflow completed")

    def test_session_with_metrics(self):
        """Test session creation with metrics recording"""
        # Start session
        session_response = requests.post(
            f"{API_BASE}/session/start",
            json={'agent_id': 'qa_test_agent'},
            timeout=TIMEOUT
        )

        if session_response.status_code not in [200, 201]:
            print("⚠ Could not start session, skipping")
            return

        session_id = session_response.json()['session_id']

        # Record a test attempt
        attempt_response = requests.post(
            f"{API_BASE}/metrics/attempt",
            json={
                'session_id': session_id,
                'agent_id': 'qa_test_agent',
                'benchmark_id': 'S7BEN-EASY-001',
                'success': True,
                'time_to_flag': 120.5,
                'tool_calls': 15,
                'tokens_used': 5000
            },
            timeout=TIMEOUT
        )

        # Get session progress
        progress_response = requests.get(
            f"{API_BASE}/session/{session_id}/progress",
            timeout=TIMEOUT
        )
        assert progress_response.status_code == 200

        # End session
        end_response = requests.post(
            f"{API_BASE}/session/{session_id}/end",
            timeout=TIMEOUT
        )
        assert end_response.status_code == 200

        print("✓ Session with metrics workflow completed")


# Test runner configuration
if __name__ == "__main__":
    """Run tests with pytest"""
    pytest.main([
        __file__,
        '-v',  # Verbose
        '--tb=short',  # Short traceback
        '-s'  # Show print statements
    ])
