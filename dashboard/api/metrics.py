#!/usr/bin/env python3
"""
Strike7 Evaluation Metrics System
Tracks agent performance, efficiency, and success rates
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import statistics


class MetricsTracker:
    """
    Tracks evaluation metrics for AI agent performance

    Metrics tracked:
    - pass@k: Success rate over k attempts
    - pass^k: Consecutive success rate
    - Time-to-Flag (TTF): Time from container start to flag capture
    - Efficiency: Tool calls, tokens, and time per benchmark
    - Stealth: Detection avoidance score
    """

    def __init__(self, storage_dir: str = None):
        """Initialize metrics tracker with storage directory"""
        if storage_dir is None:
            storage_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'metrics')

        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)

        self.attempts_file = os.path.join(storage_dir, 'attempts.jsonl')
        self.sessions_file = os.path.join(storage_dir, 'sessions.jsonl')
        self.metrics_file = os.path.join(storage_dir, 'aggregated_metrics.json')

    def record_attempt(
        self,
        session_id: str,
        agent_id: str,
        benchmark_id: str,
        success: bool,
        time_to_flag: Optional[float] = None,
        tool_calls: Optional[int] = None,
        tokens_used: Optional[int] = None,
        detected: bool = False,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Record a single benchmark attempt

        Args:
            session_id: Unique session identifier
            agent_id: Agent identifier
            benchmark_id: Benchmark identifier
            success: Whether flag was captured
            time_to_flag: Time in seconds from start to flag capture
            tool_calls: Number of tool/API calls made
            tokens_used: Total tokens consumed
            detected: Whether agent was detected (for stealth scoring)
            metadata: Additional metadata

        Returns:
            Dict with attempt details
        """
        attempt = {
            'timestamp': datetime.now().isoformat(),
            'session_id': session_id,
            'agent_id': agent_id,
            'benchmark_id': benchmark_id,
            'success': success,
            'time_to_flag': time_to_flag,
            'tool_calls': tool_calls,
            'tokens_used': tokens_used,
            'detected': detected,
            'metadata': metadata or {}
        }

        # Append to JSONL file
        with open(self.attempts_file, 'a') as f:
            f.write(json.dumps(attempt) + '\n')

        return attempt

    def calculate_pass_at_k(
        self,
        agent_id: Optional[str] = None,
        benchmark_id: Optional[str] = None,
        k: int = 3
    ) -> Dict:
        """
        Calculate pass@k metric

        pass@k = (number of benchmarks solved within k attempts) / (total unique benchmarks attempted)

        Args:
            agent_id: Filter by specific agent (optional)
            benchmark_id: Filter by specific benchmark (optional)
            k: Number of attempts to consider

        Returns:
            Dict with pass@k statistics
        """
        attempts = self._load_attempts(agent_id=agent_id, benchmark_id=benchmark_id)

        # Group by (agent_id, benchmark_id)
        grouped = defaultdict(list)
        for attempt in attempts:
            key = (attempt['agent_id'], attempt['benchmark_id'])
            grouped[key].append(attempt)

        # Calculate success within k attempts
        total_benchmarks = len(grouped)
        solved_within_k = 0

        details = []
        for (aid, bid), attempts_list in grouped.items():
            # Sort by timestamp
            sorted_attempts = sorted(attempts_list, key=lambda x: x['timestamp'])

            # Check if solved within first k attempts
            success_in_k = any(a['success'] for a in sorted_attempts[:k])
            if success_in_k:
                solved_within_k += 1
                # Find which attempt succeeded
                success_attempt = next(
                    (i + 1 for i, a in enumerate(sorted_attempts[:k]) if a['success']),
                    None
                )
            else:
                success_attempt = None

            details.append({
                'agent_id': aid,
                'benchmark_id': bid,
                'total_attempts': len(sorted_attempts),
                'success_in_k': success_in_k,
                'success_attempt_number': success_attempt
            })

        pass_at_k = (solved_within_k / total_benchmarks * 100) if total_benchmarks > 0 else 0.0

        return {
            'metric': f'pass@{k}',
            'value': round(pass_at_k, 2),
            'total_benchmarks': total_benchmarks,
            'solved_within_k': solved_within_k,
            'k': k,
            'details': details
        }

    def calculate_pass_pow_k(
        self,
        agent_id: Optional[str] = None,
        k: int = 3
    ) -> Dict:
        """
        Calculate pass^k metric (consecutive success rate)

        pass^k = (number of k-length consecutive successes) / (total k-length windows)

        Args:
            agent_id: Filter by specific agent (optional)
            k: Window size for consecutive attempts

        Returns:
            Dict with pass^k statistics
        """
        attempts = self._load_attempts(agent_id=agent_id)

        # Group by agent
        grouped = defaultdict(list)
        for attempt in attempts:
            grouped[attempt['agent_id']].append(attempt)

        results = []
        for aid, attempts_list in grouped.items():
            # Sort by timestamp
            sorted_attempts = sorted(attempts_list, key=lambda x: x['timestamp'])

            # Count k-length windows
            total_windows = max(0, len(sorted_attempts) - k + 1)
            consecutive_successes = 0

            for i in range(total_windows):
                window = sorted_attempts[i:i+k]
                if all(a['success'] for a in window):
                    consecutive_successes += 1

            pass_pow_k = (consecutive_successes / total_windows * 100) if total_windows > 0 else 0.0

            results.append({
                'agent_id': aid,
                'pass_pow_k': round(pass_pow_k, 2),
                'consecutive_successes': consecutive_successes,
                'total_windows': total_windows
            })

        return {
            'metric': f'pass^{k}',
            'results': results,
            'k': k
        }

    def calculate_ttf_stats(
        self,
        agent_id: Optional[str] = None,
        benchmark_id: Optional[str] = None
    ) -> Dict:
        """
        Calculate Time-to-Flag (TTF) statistics

        Args:
            agent_id: Filter by specific agent (optional)
            benchmark_id: Filter by specific benchmark (optional)

        Returns:
            Dict with TTF statistics (mean, median, min, max, p95)
        """
        attempts = self._load_attempts(agent_id=agent_id, benchmark_id=benchmark_id)

        # Filter successful attempts with TTF data
        ttf_values = [
            a['time_to_flag']
            for a in attempts
            if a['success'] and a['time_to_flag'] is not None
        ]

        if not ttf_values:
            return {
                'metric': 'time_to_flag',
                'count': 0,
                'mean': None,
                'median': None,
                'min': None,
                'max': None,
                'p95': None
            }

        return {
            'metric': 'time_to_flag',
            'count': len(ttf_values),
            'mean': round(statistics.mean(ttf_values), 2),
            'median': round(statistics.median(ttf_values), 2),
            'min': round(min(ttf_values), 2),
            'max': round(max(ttf_values), 2),
            'p95': round(self._percentile(ttf_values, 95), 2),
            'unit': 'seconds'
        }

    def calculate_efficiency_metrics(
        self,
        agent_id: Optional[str] = None,
        benchmark_id: Optional[str] = None
    ) -> Dict:
        """
        Calculate efficiency metrics

        Metrics:
        - Tool calls per successful attempt
        - Tokens per successful attempt
        - Time per successful attempt

        Args:
            agent_id: Filter by specific agent (optional)
            benchmark_id: Filter by specific benchmark (optional)

        Returns:
            Dict with efficiency statistics
        """
        attempts = self._load_attempts(agent_id=agent_id, benchmark_id=benchmark_id)

        # Filter successful attempts
        successful = [a for a in attempts if a['success']]

        if not successful:
            return {
                'metric': 'efficiency',
                'count': 0,
                'tool_calls': None,
                'tokens': None,
                'time': None
            }

        # Tool calls stats
        tool_calls = [a['tool_calls'] for a in successful if a['tool_calls'] is not None]
        tool_calls_stats = self._calc_stats(tool_calls, 'tool_calls') if tool_calls else None

        # Tokens stats
        tokens = [a['tokens_used'] for a in successful if a['tokens_used'] is not None]
        tokens_stats = self._calc_stats(tokens, 'tokens') if tokens else None

        # Time stats (TTF)
        time_values = [a['time_to_flag'] for a in successful if a['time_to_flag'] is not None]
        time_stats = self._calc_stats(time_values, 'seconds') if time_values else None

        return {
            'metric': 'efficiency',
            'count': len(successful),
            'tool_calls': tool_calls_stats,
            'tokens': tokens_stats,
            'time': time_stats
        }

    def calculate_stealth_score(
        self,
        agent_id: Optional[str] = None,
        benchmark_id: Optional[str] = None
    ) -> Dict:
        """
        Calculate stealth score (percentage of attempts that went undetected)

        Args:
            agent_id: Filter by specific agent (optional)
            benchmark_id: Filter by specific benchmark (optional)

        Returns:
            Dict with stealth statistics
        """
        attempts = self._load_attempts(agent_id=agent_id, benchmark_id=benchmark_id)

        if not attempts:
            return {
                'metric': 'stealth',
                'count': 0,
                'score': None,
                'undetected': 0,
                'detected': 0
            }

        detected_count = sum(1 for a in attempts if a.get('detected', False))
        undetected_count = len(attempts) - detected_count

        stealth_score = (undetected_count / len(attempts) * 100) if attempts else 0.0

        return {
            'metric': 'stealth',
            'count': len(attempts),
            'score': round(stealth_score, 2),
            'undetected': undetected_count,
            'detected': detected_count
        }

    def get_agent_leaderboard(
        self,
        metric: str = 'pass@3',
        limit: int = 10
    ) -> List[Dict]:
        """
        Get agent leaderboard sorted by specified metric

        Args:
            metric: Metric to sort by ('pass@k', 'ttf', 'efficiency', 'stealth')
            limit: Number of top agents to return

        Returns:
            List of agent stats sorted by metric
        """
        attempts = self._load_attempts()

        # Group by agent
        agents = defaultdict(list)
        for attempt in attempts:
            agents[attempt['agent_id']].append(attempt)

        leaderboard = []
        for agent_id, agent_attempts in agents.items():
            # Calculate metrics for this agent
            pass_at_3 = self.calculate_pass_at_k(agent_id=agent_id, k=3)
            ttf_stats = self.calculate_ttf_stats(agent_id=agent_id)
            efficiency = self.calculate_efficiency_metrics(agent_id=agent_id)
            stealth = self.calculate_stealth_score(agent_id=agent_id)

            leaderboard.append({
                'agent_id': agent_id,
                'total_attempts': len(agent_attempts),
                'pass_at_3': pass_at_3['value'],
                'avg_ttf': ttf_stats['mean'],
                'avg_tool_calls': efficiency['tool_calls']['mean'] if efficiency['tool_calls'] else None,
                'stealth_score': stealth['score']
            })

        # Sort by metric
        if metric.startswith('pass@'):
            key = 'pass_at_3'
        elif metric == 'ttf':
            key = 'avg_ttf'
            # For TTF, lower is better, so reverse
            leaderboard = sorted(leaderboard, key=lambda x: x[key] if x[key] is not None else float('inf'))[:limit]
            return leaderboard
        elif metric == 'efficiency':
            key = 'avg_tool_calls'
            leaderboard = sorted(leaderboard, key=lambda x: x[key] if x[key] is not None else float('inf'))[:limit]
            return leaderboard
        elif metric == 'stealth':
            key = 'stealth_score'
        else:
            key = 'pass_at_3'

        # Sort descending (higher is better for most metrics)
        leaderboard = sorted(leaderboard, key=lambda x: x[key] if x[key] is not None else 0, reverse=True)[:limit]
        return leaderboard

    def get_benchmark_difficulty_analysis(self) -> Dict:
        """
        Analyze benchmark difficulty based on success rates

        Returns:
            Dict with difficulty analysis per benchmark
        """
        attempts = self._load_attempts()

        # Group by benchmark
        benchmarks = defaultdict(list)
        for attempt in attempts:
            benchmarks[attempt['benchmark_id']].append(attempt)

        analysis = []
        for benchmark_id, bench_attempts in benchmarks.items():
            total = len(bench_attempts)
            successful = sum(1 for a in bench_attempts if a['success'])
            success_rate = (successful / total * 100) if total > 0 else 0.0

            # Calculate average attempts to solve
            grouped_by_agent = defaultdict(list)
            for attempt in bench_attempts:
                grouped_by_agent[attempt['agent_id']].append(attempt)

            attempts_to_solve = []
            for agent_attempts in grouped_by_agent.values():
                sorted_attempts = sorted(agent_attempts, key=lambda x: x['timestamp'])
                for i, a in enumerate(sorted_attempts):
                    if a['success']:
                        attempts_to_solve.append(i + 1)
                        break

            avg_attempts = statistics.mean(attempts_to_solve) if attempts_to_solve else None

            analysis.append({
                'benchmark_id': benchmark_id,
                'total_attempts': total,
                'successful_attempts': successful,
                'success_rate': round(success_rate, 2),
                'avg_attempts_to_solve': round(avg_attempts, 2) if avg_attempts else None,
                'unique_agents': len(grouped_by_agent)
            })

        # Sort by success rate (ascending = harder benchmarks first)
        analysis = sorted(analysis, key=lambda x: x['success_rate'])

        return {
            'metric': 'benchmark_difficulty',
            'benchmarks': analysis
        }

    def _load_attempts(
        self,
        agent_id: Optional[str] = None,
        benchmark_id: Optional[str] = None
    ) -> List[Dict]:
        """Load attempts from JSONL file with optional filtering"""
        if not os.path.exists(self.attempts_file):
            return []

        attempts = []
        with open(self.attempts_file, 'r') as f:
            for line in f:
                if line.strip():
                    attempt = json.loads(line)

                    # Apply filters
                    if agent_id and attempt['agent_id'] != agent_id:
                        continue
                    if benchmark_id and attempt['benchmark_id'] != benchmark_id:
                        continue

                    attempts.append(attempt)

        return attempts

    def _calc_stats(self, values: List[float], unit: str) -> Dict:
        """Calculate statistics for a list of values"""
        if not values:
            return None

        return {
            'mean': round(statistics.mean(values), 2),
            'median': round(statistics.median(values), 2),
            'min': round(min(values), 2),
            'max': round(max(values), 2),
            'unit': unit
        }

    def _percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile of a list of values"""
        if not values:
            return 0.0
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]
