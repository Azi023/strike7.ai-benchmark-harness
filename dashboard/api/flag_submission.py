"""
Flag Submission and Validation Module
Handles flag validation, attempt tracking, and scoring
"""

import re
import time
from datetime import datetime
from typing import Dict, Optional, Tuple


class FlagValidator:
    """Validates submitted flags against benchmark expectations"""

    def __init__(self, benchmarks: list):
        """
        Initialize flag validator

        Args:
            benchmarks: List of benchmark configurations from YAML
        """
        self.benchmarks = {b['id']: b for b in benchmarks}
        self.attempts = {}  # Track attempts: {benchmark_id: {session_id: count}}
        self.submissions = []  # Log all submissions for analysis
        self.start_times = {}  # Track container start times: {benchmark_id: timestamp}

    def validate_flag(self, benchmark_id: str, submitted_flag: str,
                     session_id: Optional[str] = None) -> Dict:
        """
        Validate a submitted flag

        Args:
            benchmark_id: Benchmark identifier (e.g., S7BEN-HARD-018)
            submitted_flag: The flag string submitted by the user
            session_id: Optional session identifier for tracking

        Returns:
            Dictionary with validation result
        """
        # Get benchmark info
        benchmark = self.benchmarks.get(benchmark_id)
        if not benchmark:
            return {
                'status': 'error',
                'message': 'Benchmark not found',
                'correct': False
            }

        # Track attempt
        session_key = session_id or 'default'
        if benchmark_id not in self.attempts:
            self.attempts[benchmark_id] = {}
        if session_key not in self.attempts[benchmark_id]:
            self.attempts[benchmark_id][session_key] = 0
        self.attempts[benchmark_id][session_key] += 1

        attempt_count = self.attempts[benchmark_id][session_key]

        # Get expected flag (exact match or regex pattern)
        expected_flag = benchmark.get('flag_format') or benchmark.get('flag_pattern')
        if not expected_flag:
            return {
                'status': 'error',
                'message': 'Flag not configured for this benchmark',
                'correct': False
            }

        # Validate flag
        is_correct = self._check_flag(submitted_flag, expected_flag)

        # Calculate time to capture (if container start time is tracked)
        time_to_capture = None
        if is_correct and benchmark_id in self.start_times:
            time_to_capture = time.time() - self.start_times[benchmark_id]

        # Log submission
        submission_log = {
            'benchmark_id': benchmark_id,
            'session_id': session_key,
            'submitted_flag': submitted_flag,
            'correct': is_correct,
            'attempt': attempt_count,
            'timestamp': datetime.now().isoformat(),
            'time_to_capture': time_to_capture
        }
        self.submissions.append(submission_log)

        # Build response
        if is_correct:
            response = {
                'status': 'success',
                'message': 'Flag accepted',
                'benchmark_id': benchmark_id,
                'correct': True,
                'attempts': attempt_count
            }
            if time_to_capture is not None:
                response['time_to_capture'] = round(time_to_capture, 2)
        else:
            response = {
                'status': 'error',
                'message': 'Incorrect flag',
                'benchmark_id': benchmark_id,
                'correct': False,
                'attempts': attempt_count
            }
            # Provide hint after 3 failed attempts
            if attempt_count >= 3:
                response['hint'] = 'Flag format: S7BEN{...}'

        return response

    def _check_flag(self, submitted: str, expected: str) -> bool:
        """
        Check if submitted flag matches expected flag
        Supports both exact match and regex patterns

        Args:
            submitted: The submitted flag
            expected: Expected flag (exact string or regex pattern)

        Returns:
            True if flag is correct, False otherwise
        """
        # Remove whitespace
        submitted = submitted.strip()
        expected = expected.strip()

        # Try exact match first
        if submitted == expected:
            return True

        # Try regex pattern match (for dynamic flags)
        try:
            # Check if expected looks like a regex pattern
            if '\\' in expected or '[' in expected or '(' in expected:
                pattern = re.compile(expected)
                return bool(pattern.fullmatch(submitted))
        except re.error:
            pass

        return False

    def mark_container_started(self, benchmark_id: str):
        """
        Mark when a benchmark container was started (for time tracking)

        Args:
            benchmark_id: Benchmark identifier
        """
        self.start_times[benchmark_id] = time.time()

    def mark_container_stopped(self, benchmark_id: str):
        """
        Mark when a benchmark container was stopped

        Args:
            benchmark_id: Benchmark identifier
        """
        if benchmark_id in self.start_times:
            del self.start_times[benchmark_id]

    def reset_attempts(self, benchmark_id: str, session_id: Optional[str] = None):
        """
        Reset attempt counter for a benchmark

        Args:
            benchmark_id: Benchmark identifier
            session_id: Optional session identifier
        """
        session_key = session_id or 'default'
        if benchmark_id in self.attempts and session_key in self.attempts[benchmark_id]:
            self.attempts[benchmark_id][session_key] = 0

    def get_attempt_count(self, benchmark_id: str, session_id: Optional[str] = None) -> int:
        """
        Get current attempt count for a benchmark

        Args:
            benchmark_id: Benchmark identifier
            session_id: Optional session identifier

        Returns:
            Number of attempts made
        """
        session_key = session_id or 'default'
        return self.attempts.get(benchmark_id, {}).get(session_key, 0)

    def get_submission_history(self, benchmark_id: Optional[str] = None,
                              session_id: Optional[str] = None) -> list:
        """
        Get submission history

        Args:
            benchmark_id: Optional filter by benchmark
            session_id: Optional filter by session

        Returns:
            List of submission records
        """
        history = self.submissions

        if benchmark_id:
            history = [s for s in history if s['benchmark_id'] == benchmark_id]

        if session_id:
            history = [s for s in history if s['session_id'] == session_id]

        return history
