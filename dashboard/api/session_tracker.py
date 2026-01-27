"""
Session Tracking Module
Tracks AI agent progress across benchmarks and evaluation sessions
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional


class SessionTracker:
    """Tracks evaluation sessions and benchmark progress"""

    def __init__(self):
        """Initialize session tracker"""
        self.sessions = {}  # {session_id: session_data}
        self.active_sessions = set()  # Set of currently active session IDs

    def start_session(self, agent_id: str, benchmark_filter: Dict = None,
                     settings: Dict = None) -> Dict:
        """
        Start a new evaluation session

        Args:
            agent_id: Identifier for the AI agent
            benchmark_filter: Optional filter criteria for benchmarks
            settings: Optional session settings

        Returns:
            Dict with session information
        """
        session_id = f"sess_{uuid.uuid4().hex[:12]}"

        session_data = {
            'session_id': session_id,
            'agent_id': agent_id,
            'started_at': datetime.now().isoformat(),
            'ended_at': None,
            'status': 'active',
            'benchmark_filter': benchmark_filter or {},
            'settings': settings or self._default_settings(),
            'results': [],
            'current_benchmark': None,
            'stats': {
                'benchmarks_attempted': 0,
                'benchmarks_solved': 0,
                'benchmarks_failed': 0,
                'total_time_seconds': 0,
                'total_attempts': 0
            }
        }

        self.sessions[session_id] = session_data
        self.active_sessions.add(session_id)

        return {
            'status': 'success',
            'session_id': session_id,
            'agent_id': agent_id,
            'started_at': session_data['started_at'],
            'settings': session_data['settings']
        }

    def _default_settings(self) -> Dict:
        """Get default session settings"""
        return {
            'max_concurrent_containers': 1,
            'timeout_per_benchmark': 600,  # 10 minutes
            'auto_advance': True,
            'max_attempts_per_benchmark': 10
        }

    def record_benchmark_start(self, session_id: str, benchmark_id: str) -> Dict:
        """
        Record that a benchmark has been started

        Args:
            session_id: Session identifier
            benchmark_id: Benchmark identifier

        Returns:
            Dict with status
        """
        session = self.sessions.get(session_id)
        if not session:
            return {
                'status': 'error',
                'message': 'Session not found'
            }

        session['current_benchmark'] = {
            'benchmark_id': benchmark_id,
            'started_at': datetime.now().isoformat(),
            'attempts': 0,
            'status': 'in_progress'
        }

        session['stats']['benchmarks_attempted'] += 1

        return {
            'status': 'success',
            'session_id': session_id,
            'benchmark_id': benchmark_id
        }

    def record_attempt(self, session_id: str, benchmark_id: str,
                      correct: bool) -> Dict:
        """
        Record a flag submission attempt

        Args:
            session_id: Session identifier
            benchmark_id: Benchmark identifier
            correct: Whether the flag was correct

        Returns:
            Dict with status
        """
        session = self.sessions.get(session_id)
        if not session:
            return {
                'status': 'error',
                'message': 'Session not found'
            }

        current = session.get('current_benchmark')
        if not current or current['benchmark_id'] != benchmark_id:
            # Start tracking this benchmark if not already
            self.record_benchmark_start(session_id, benchmark_id)
            current = session['current_benchmark']

        current['attempts'] += 1
        session['stats']['total_attempts'] += 1

        if correct:
            current['status'] = 'solved'
            current['solved_at'] = datetime.now().isoformat()

        return {
            'status': 'success',
            'attempts': current['attempts']
        }

    def record_benchmark_result(self, session_id: str, benchmark_id: str,
                               status: str, time_seconds: float = None,
                               attempts: int = None) -> Dict:
        """
        Record the final result for a benchmark

        Args:
            session_id: Session identifier
            benchmark_id: Benchmark identifier
            status: Result status (solved, failed, timeout, skipped)
            time_seconds: Time taken in seconds
            attempts: Number of attempts made

        Returns:
            Dict with status
        """
        session = self.sessions.get(session_id)
        if not session:
            return {
                'status': 'error',
                'message': 'Session not found'
            }

        current = session.get('current_benchmark')
        if current and current['benchmark_id'] == benchmark_id:
            # Use current benchmark data
            if time_seconds is None and 'started_at' in current:
                started = datetime.fromisoformat(current['started_at'])
                time_seconds = (datetime.now() - started).total_seconds()
            if attempts is None:
                attempts = current.get('attempts', 0)
        else:
            # Create new result record
            time_seconds = time_seconds or 0
            attempts = attempts or 0

        result = {
            'benchmark_id': benchmark_id,
            'status': status,
            'time_seconds': round(time_seconds, 2),
            'attempts': attempts,
            'completed_at': datetime.now().isoformat()
        }

        session['results'].append(result)
        session['current_benchmark'] = None

        # Update stats
        if status == 'solved':
            session['stats']['benchmarks_solved'] += 1
        elif status in ['failed', 'timeout']:
            session['stats']['benchmarks_failed'] += 1

        session['stats']['total_time_seconds'] += time_seconds

        return {
            'status': 'success',
            'result': result
        }

    def end_session(self, session_id: str) -> Dict:
        """
        End an evaluation session

        Args:
            session_id: Session identifier

        Returns:
            Dict with final session summary
        """
        session = self.sessions.get(session_id)
        if not session:
            return {
                'status': 'error',
                'message': 'Session not found'
            }

        session['ended_at'] = datetime.now().isoformat()
        session['status'] = 'completed'

        if session_id in self.active_sessions:
            self.active_sessions.remove(session_id)

        # Calculate total session time
        started = datetime.fromisoformat(session['started_at'])
        ended = datetime.now()
        total_duration = (ended - started).total_seconds()

        return {
            'status': 'success',
            'session_id': session_id,
            'ended_at': session['ended_at'],
            'duration_seconds': round(total_duration, 2),
            'stats': session['stats'],
            'results': session['results']
        }

    def get_session_progress(self, session_id: str) -> Dict:
        """
        Get current progress for a session

        Args:
            session_id: Session identifier

        Returns:
            Dict with session progress
        """
        session = self.sessions.get(session_id)
        if not session:
            return {
                'status': 'error',
                'message': 'Session not found'
            }

        # Calculate elapsed time
        started = datetime.fromisoformat(session['started_at'])
        elapsed = (datetime.now() - started).total_seconds()

        progress = {
            'session_id': session_id,
            'agent_id': session['agent_id'],
            'status': session['status'],
            'started_at': session['started_at'],
            'elapsed_seconds': round(elapsed, 2),
            'current_benchmark': session.get('current_benchmark'),
            'stats': session['stats'],
            'results': session['results']
        }

        if session['ended_at']:
            progress['ended_at'] = session['ended_at']

        return progress

    def get_all_sessions(self, active_only: bool = False) -> List[Dict]:
        """
        Get all sessions

        Args:
            active_only: Only return active sessions

        Returns:
            List of session summaries
        """
        sessions = []

        for session_id, session in self.sessions.items():
            if active_only and session_id not in self.active_sessions:
                continue

            sessions.append({
                'session_id': session_id,
                'agent_id': session['agent_id'],
                'status': session['status'],
                'started_at': session['started_at'],
                'ended_at': session.get('ended_at'),
                'stats': session['stats']
            })

        return sessions

    def get_leaderboard(self, limit: int = 10) -> List[Dict]:
        """
        Get leaderboard of best performing sessions

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of leaderboard entries
        """
        completed_sessions = [
            s for s in self.sessions.values()
            if s['status'] == 'completed'
        ]

        # Sort by: solved count (desc), then total time (asc)
        sorted_sessions = sorted(
            completed_sessions,
            key=lambda s: (-s['stats']['benchmarks_solved'],
                          s['stats']['total_time_seconds'])
        )

        leaderboard = []
        for i, session in enumerate(sorted_sessions[:limit], 1):
            leaderboard.append({
                'rank': i,
                'session_id': session['session_id'],
                'agent_id': session['agent_id'],
                'benchmarks_solved': session['stats']['benchmarks_solved'],
                'total_time_seconds': round(session['stats']['total_time_seconds'], 2),
                'success_rate': round(
                    session['stats']['benchmarks_solved'] /
                    max(session['stats']['benchmarks_attempted'], 1) * 100,
                    1
                )
            })

        return leaderboard
