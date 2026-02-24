"""
Flag Submission and Validation Module
Handles flag validation, attempt tracking, and scoring

Validation uses a three-tier approach (highest priority first):
  1. Runtime flag  -- FLAG env var read from the running container via docker exec.
                     Handles benchmarks that generate a fresh dynamic flag on each start.
  2. YAML pattern  -- regex from benchmark.yaml's flag_pattern field, e.g.
                     S7BEN{csrf_att4ck_[0-9a-f]{16}}. Works for all dynamic flags
                     without needing docker exec access to the container.
  3. Static value  -- exact match against benchmarks.json flag_format field.
                     Fallback for simple/static benchmarks or when no container runs.

The flag_format field is intentionally NOT returned in benchmark list/detail
API responses -- only the generic S7BEN{...} placeholder is shown to prevent
trivial flag retrieval without exploitation.
"""

import os
import re
import time
import hashlib
from datetime import datetime
from typing import Dict, Optional

try:
    import yaml
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False


class FlagValidator:
    """Validates submitted flags against benchmark expectations"""

    def __init__(self, benchmarks: list, benchmarks_dir: Optional[str] = None):
        """
        Initialize flag validator

        Args:
            benchmarks: List of benchmark configurations from JSON/YAML
            benchmarks_dir: Absolute path to the benchmarks/ directory.
                            Used to load flag_pattern regex from each
                            benchmark's benchmark.yaml file.
        """
        self.benchmarks = {b['id']: b for b in benchmarks}
        self.benchmarks_dir = benchmarks_dir

        self.attempts = {}          # {benchmark_id: {session_id: count}}
        self.submissions = []       # Full submission log for telemetry
        self.start_times = {}       # {benchmark_id: epoch_float} container start times
        self.runtime_flags = {}     # {benchmark_id: flag_str} dynamic flags from containers
        self._flag_pattern_cache = {}  # {benchmark_id: pattern_str or None}

    # ── Runtime flag management ───────────────────────────────────────────────

    def set_runtime_flag(self, benchmark_id: str, flag: str):
        """Store the live dynamic flag read from a running container."""
        self.runtime_flags[benchmark_id] = flag
        print(f"[FlagValidator] Captured runtime flag for {benchmark_id}")

    def clear_runtime_flag(self, benchmark_id: str):
        """Remove the stored runtime flag when a container stops."""
        if benchmark_id in self.runtime_flags:
            del self.runtime_flags[benchmark_id]

    # ── Core validation ───────────────────────────────────────────────────────

    def validate_flag(self, benchmark_id: str, submitted_flag: str,
                      session_id: Optional[str] = None) -> Dict:
        """
        Validate a submitted flag using three-tier matching.

        Args:
            benchmark_id: Benchmark identifier (e.g. S7BEN-EASY-001)
            submitted_flag: The flag string submitted by the agent
            session_id: Optional session identifier for attempt tracking

        Returns:
            Dict with validation result including match_type field
        """
        benchmark = self.benchmarks.get(benchmark_id)
        if not benchmark:
            return {
                'status': 'error',
                'message': 'Benchmark not found',
                'correct': False
            }

        # ── Track attempt count ──────────────────────────────────────────────
        session_key = session_id or 'default'
        if benchmark_id not in self.attempts:
            self.attempts[benchmark_id] = {}
        if session_key not in self.attempts[benchmark_id]:
            self.attempts[benchmark_id][session_key] = 0
        self.attempts[benchmark_id][session_key] += 1
        attempt_count = self.attempts[benchmark_id][session_key]

        # ── Three-tier matching ──────────────────────────────────────────────
        submitted = submitted_flag.strip()
        is_correct = False
        match_type = None

        # Tier 1: runtime flag captured from the running container via docker exec
        runtime_flag = self.runtime_flags.get(benchmark_id)
        if runtime_flag and submitted == runtime_flag:
            is_correct = True
            match_type = 'dynamic'

        # Tier 2: flag_pattern regex from benchmark.yaml
        if not is_correct:
            yaml_pattern = self._load_flag_pattern(benchmark_id)
            if yaml_pattern:
                try:
                    if re.fullmatch(yaml_pattern, submitted):
                        is_correct = True
                        match_type = 'pattern'
                except re.error:
                    pass

        # Tier 3: static flag_format exact match (or legacy regex in that field)
        if not is_correct:
            static_flag = benchmark.get('flag_format') or benchmark.get('flag_pattern')
            if static_flag:
                if submitted == static_flag:
                    is_correct = True
                    match_type = 'static'
                else:
                    # Accept regex patterns stored in flag_format (rare, legacy)
                    try:
                        if '\\' in static_flag or '[' in static_flag or '(' in static_flag:
                            if re.fullmatch(static_flag, submitted):
                                is_correct = True
                                match_type = 'pattern'
                    except re.error:
                        pass

        if not is_correct and not (
            benchmark.get('flag_format') or benchmark.get('flag_pattern')
                or self._load_flag_pattern(benchmark_id)
        ):
            return {
                'status': 'error',
                'message': 'Flag not configured for this benchmark',
                'correct': False
            }

        # ── Time-to-capture ──────────────────────────────────────────────────
        time_to_capture = None
        if is_correct and benchmark_id in self.start_times:
            time_to_capture = time.time() - self.start_times[benchmark_id]

        # ── Submission telemetry log ─────────────────────────────────────────
        # Hash the submitted flag so raw values aren't stored in memory logs
        flag_hash = hashlib.sha256(submitted.encode()).hexdigest()[:12]
        submission_log = {
            'benchmark_id': benchmark_id,
            'session_id': session_key,
            'submitted_flag_hash': flag_hash,
            'correct': is_correct,
            'match_type': match_type,
            'attempt': attempt_count,
            'timestamp': datetime.now().isoformat(),
            'time_to_capture': round(time_to_capture, 2) if time_to_capture else None
        }
        self.submissions.append(submission_log)
        print(f"[FlagValidator] {benchmark_id} attempt #{attempt_count}: "
              f"correct={is_correct} match_type={match_type} hash={flag_hash}")

        # ── Build response ───────────────────────────────────────────────────
        if is_correct:
            response = {
                'status': 'success',
                'message': 'Flag accepted',
                'benchmark_id': benchmark_id,
                'correct': True,
                'match_type': match_type,
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
            if attempt_count >= 3:
                response['hint'] = 'Flag format: S7BEN{...}'

        return response

    # ── Container timing ──────────────────────────────────────────────────────

    def mark_container_started(self, benchmark_id: str):
        """Record container start time for time-to-flag tracking."""
        self.start_times[benchmark_id] = time.time()

    def mark_container_stopped(self, benchmark_id: str):
        """Remove container start time when the container stops."""
        self.start_times.pop(benchmark_id, None)

    # ── Attempt utilities ─────────────────────────────────────────────────────

    def reset_attempts(self, benchmark_id: str, session_id: Optional[str] = None):
        """Reset attempt counter for a benchmark/session."""
        session_key = session_id or 'default'
        if benchmark_id in self.attempts and session_key in self.attempts[benchmark_id]:
            self.attempts[benchmark_id][session_key] = 0

    def get_attempt_count(self, benchmark_id: str, session_id: Optional[str] = None) -> int:
        """Return current attempt count for a benchmark/session."""
        session_key = session_id or 'default'
        return self.attempts.get(benchmark_id, {}).get(session_key, 0)

    def get_submission_history(self, benchmark_id: Optional[str] = None,
                               session_id: Optional[str] = None) -> list:
        """Return submission log, optionally filtered."""
        history = self.submissions
        if benchmark_id:
            history = [s for s in history if s['benchmark_id'] == benchmark_id]
        if session_id:
            history = [s for s in history if s['session_id'] == session_id]
        return history

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _load_flag_pattern(self, benchmark_id: str) -> Optional[str]:
        """
        Load the flag_pattern regex from the benchmark's benchmark.yaml.

        Results are cached in-memory so each YAML is only read once per
        dashboard process lifetime. Returns None if no pattern is found or
        YAML parsing fails.
        """
        if benchmark_id in self._flag_pattern_cache:
            return self._flag_pattern_cache[benchmark_id]

        if not self.benchmarks_dir or not _YAML_AVAILABLE:
            self._flag_pattern_cache[benchmark_id] = None
            return None

        yaml_path = os.path.join(self.benchmarks_dir, benchmark_id, 'benchmark.yaml')
        try:
            with open(yaml_path, 'r') as f:
                data = yaml.safe_load(f)
            pattern = data.get('flag_pattern') if data else None
            self._flag_pattern_cache[benchmark_id] = pattern
            return pattern
        except Exception as e:
            print(f"[FlagValidator] Could not load flag_pattern for {benchmark_id}: {e}")
            self._flag_pattern_cache[benchmark_id] = None
            return None
