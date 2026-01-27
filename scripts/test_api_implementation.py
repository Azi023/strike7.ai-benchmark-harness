#!/usr/bin/env python3
"""
Test script for Phase 6C API implementation
Tests all new endpoints without requiring containers to be running
"""

import sys
import os

# Add dashboard to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'dashboard'))

from api.flag_submission import FlagValidator
from api.container_manager import ContainerManager
from api.session_tracker import SessionTracker
import yaml


def load_benchmarks():
    """Load benchmarks from YAML"""
    benchmarks_file = os.path.join(
        os.path.dirname(__file__),
        'dashboard',
        'config',
        'benchmarks.yaml'
    )
    with open(benchmarks_file, 'r') as f:
        data = yaml.safe_load(f)
        return data.get('benchmarks', [])


def test_flag_validation():
    """Test flag validation system"""
    print("\n" + "="*60)
    print("TEST 1: Flag Validation System")
    print("="*60)

    benchmarks = load_benchmarks()
    fv = FlagValidator(benchmarks)

    # Test 1: Correct flag (exact match)
    result = fv.validate_flag('S7BEN-EASY-001', 'S7BEN{csrf_att4ck_succ3ssful}')
    assert result['correct'] == True, "Correct flag should validate"
    assert result['status'] == 'success', "Status should be success"
    print("[PASS] Correct flag validation (exact match)")

    # Test 2: Incorrect flag
    result = fv.validate_flag('S7BEN-EASY-001', 'S7BEN{wrong_flag}')
    assert result['correct'] == False, "Wrong flag should not validate"
    assert result['status'] == 'error', "Status should be error"
    print("[PASS] Incorrect flag rejection")

    # Test 3: Attempt tracking
    result1 = fv.validate_flag('S7BEN-EASY-002', 'S7BEN{wrong1}')
    result2 = fv.validate_flag('S7BEN-EASY-002', 'S7BEN{wrong2}')
    result3 = fv.validate_flag('S7BEN-EASY-002', 'S7BEN{wrong3}')
    assert result1['attempts'] == 1, "First attempt should be 1"
    assert result2['attempts'] == 2, "Second attempt should be 2"
    assert result3['attempts'] == 3, "Third attempt should be 3"
    print("[PASS] Attempt counting")

    # Test 4: Hint after 3 attempts
    assert 'hint' in result3, "Hint should appear after 3 attempts"
    print("[PASS] Hint provision after 3 attempts")

    # Test 5: Non-existent benchmark
    result = fv.validate_flag('S7BEN-FAKE-999', 'S7BEN{test}')
    assert result['status'] == 'error', "Should error for non-existent benchmark"
    assert 'not found' in result['message'].lower(), "Should mention not found"
    print("[PASS] Non-existent benchmark handling")

    print("\n[OK] Flag Validation: All tests passed!")
    return True


def test_container_manager():
    """Test container manager (without actually starting containers)"""
    print("\n" + "="*60)
    print("TEST 2: Container Manager")
    print("="*60)

    benchmarks = load_benchmarks()
    cm = ContainerManager(benchmarks)

    # Test 1: Initialization
    assert cm.config['max_concurrent'] == 1, "Default max_concurrent should be 1"
    assert cm.config['timeout_minutes'] == 30, "Default timeout should be 30"
    print("[PASS] Container manager initialization")

    # Test 2: Get system status (should not error)
    status = cm.get_system_status()
    assert 'cpu_count' in status, "System status should include cpu_count"
    print("[PASS] System status retrieval")

    # Test 3: Get running containers (should return empty list if none running)
    running = cm.get_running_containers()
    assert isinstance(running, list), "Should return list"
    print(f"[PASS] Get running containers (found {len(running)})")

    print("\n[OK] Container Manager: All tests passed!")
    return True


def test_session_tracker():
    """Test session tracking system"""
    print("\n" + "="*60)
    print("TEST 3: Session Tracker")
    print("="*60)

    st = SessionTracker()

    # Test 1: Start session
    result = st.start_session('test-agent-001')
    assert result['status'] == 'success', "Session start should succeed"
    assert 'session_id' in result, "Should return session_id"
    session_id = result['session_id']
    print(f"[PASS] Session creation: {session_id}")

    # Test 2: Record attempts
    st.record_attempt(session_id, 'S7BEN-EASY-001', False)
    st.record_attempt(session_id, 'S7BEN-EASY-001', True)
    progress = st.get_session_progress(session_id)
    assert progress['stats']['total_attempts'] == 2, "Should track 2 attempts"
    print("[PASS] Attempt recording")

    # Test 3: Record benchmark result
    result = st.record_benchmark_result(
        session_id,
        'S7BEN-EASY-001',
        'solved',
        time_seconds=45.2,
        attempts=2
    )
    assert result['status'] == 'success', "Should record result successfully"
    print("[PASS] Benchmark result recording")

    # Test 4: Get progress
    progress = st.get_session_progress(session_id)
    assert progress['session_id'] == session_id, "Session ID should match"
    assert progress['stats']['benchmarks_solved'] == 1, "Should have 1 solved"
    assert len(progress['results']) == 1, "Should have 1 result"
    print("[PASS] Progress tracking")

    # Test 5: End session
    final = st.end_session(session_id)
    assert final['status'] == 'success', "Session end should succeed"
    assert 'duration_seconds' in final, "Should include duration"
    print("[PASS] Session termination")

    # Test 6: Multiple sessions
    session1 = st.start_session('agent-1')['session_id']
    session2 = st.start_session('agent-2')['session_id']
    sessions = st.get_all_sessions()
    assert len(sessions) >= 2, "Should have at least 2 sessions"
    print("[PASS] Multiple session support")

    # Test 7: Leaderboard
    st.record_benchmark_result(session1, 'S7BEN-EASY-001', 'solved', 30.0, 1)
    st.record_benchmark_result(session1, 'S7BEN-EASY-002', 'solved', 40.0, 1)
    st.end_session(session1)

    st.record_benchmark_result(session2, 'S7BEN-EASY-001', 'solved', 50.0, 2)
    st.end_session(session2)

    leaderboard = st.get_leaderboard(limit=10)
    assert len(leaderboard) > 0, "Should have leaderboard entries"
    assert leaderboard[0]['rank'] == 1, "First entry should be rank 1"
    print("[PASS] Leaderboard generation")

    print("\n[OK] Session Tracker: All tests passed!")
    return True


def test_integration():
    """Test integration between modules"""
    print("\n" + "="*60)
    print("TEST 4: Module Integration")
    print("="*60)

    benchmarks = load_benchmarks()
    fv = FlagValidator(benchmarks)
    cm = ContainerManager(benchmarks)
    st = SessionTracker()

    # Simulate complete workflow
    session_id = st.start_session('integration-test-agent')['session_id']
    print(f"[PASS] Created session: {session_id}")

    # Simulate flag submission with session tracking
    benchmark_id = 'S7BEN-EASY-001'

    # Wrong attempt
    result = fv.validate_flag(benchmark_id, 'S7BEN{wrong}', session_id)
    st.record_attempt(session_id, benchmark_id, result['correct'])
    print("[PASS] Recorded failed attempt")

    # Correct attempt
    result = fv.validate_flag(benchmark_id, 'S7BEN{csrf_att4ck_succ3ssful}', session_id)
    st.record_attempt(session_id, benchmark_id, result['correct'])
    print("[PASS] Recorded successful attempt")

    # Record final result
    st.record_benchmark_result(session_id, benchmark_id, 'solved', 60.0, 2)

    # Get progress
    progress = st.get_session_progress(session_id)
    assert progress['stats']['benchmarks_solved'] == 1, "Should show 1 solved"
    assert progress['stats']['total_attempts'] == 2, "Should show 2 attempts"
    print("[PASS] Integrated progress tracking")

    # End session
    st.end_session(session_id)
    print("[PASS] Session completed")

    print("\n[OK] Integration: All tests passed!")
    return True


def main():
    """Run all tests"""
    print("="*60)
    print("Phase 6C API Implementation Test Suite")
    print("="*60)

    tests = [
        test_flag_validation,
        test_container_manager,
        test_session_tracker,
        test_integration
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"\n[FAIL] {test.__name__}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Total Tests: {len(tests)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    if failed == 0:
        print("\n*** ALL TESTS PASSED ***")
        return 0
    else:
        print(f"\n*** {failed} TEST(S) FAILED ***")
        return 1


if __name__ == '__main__':
    sys.exit(main())
