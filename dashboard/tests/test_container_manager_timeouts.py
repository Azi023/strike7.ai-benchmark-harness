"""
Unit tests for ContainerManager tier-based timeout logic.

Tests _extract_tier() and _get_startup_timeout() methods to ensure
correct timeout values are applied per benchmark tier.
"""

import pytest
import sys
import os

# Add dashboard directory to path so we can import the module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from api.container_manager import ContainerManager


# Minimal benchmark list for constructing a ContainerManager instance
_STUB_BENCHMARKS = [
    {'id': 'S7BEN-EASY-001', 'port': 5000},
    {'id': 'S7BEN-MED-007', 'port': 5016},
    {'id': 'S7BEN-HARD-001', 'port': 5030},
    {'id': 'S7BEN-VHARD-003', 'port': 5052},
    {'id': 'S7BEN-CVE-005', 'port': 5074},
]


@pytest.fixture
def cm():
    return ContainerManager(_STUB_BENCHMARKS)


# ── _extract_tier tests ─────────────────────────────────────────────

class TestExtractTier:
    def test_easy_tier(self):
        assert ContainerManager._extract_tier('S7BEN-EASY-001') == 'EASY'

    def test_med_tier(self):
        assert ContainerManager._extract_tier('S7BEN-MED-012') == 'MED'

    def test_hard_tier(self):
        assert ContainerManager._extract_tier('S7BEN-HARD-001') == 'HARD'

    def test_vhard_tier(self):
        assert ContainerManager._extract_tier('S7BEN-VHARD-003') == 'VHARD'

    def test_cve_tier(self):
        assert ContainerManager._extract_tier('S7BEN-CVE-012') == 'CVE'

    def test_lowercase_normalised_to_upper(self):
        assert ContainerManager._extract_tier('S7BEN-easy-001') == 'EASY'

    def test_missing_prefix_returns_none(self):
        assert ContainerManager._extract_tier('EASY-001') is None

    def test_empty_string_returns_none(self):
        assert ContainerManager._extract_tier('') is None

    def test_none_returns_none(self):
        assert ContainerManager._extract_tier(None) is None

    def test_malformed_id_too_few_parts(self):
        assert ContainerManager._extract_tier('S7BEN-EASY') is None


# ── _get_startup_timeout tests ───────────────────────────────────────

class TestGetStartupTimeout:
    def test_easy_timeout(self, cm):
        assert cm._get_startup_timeout('S7BEN-EASY-001') == 60

    def test_med_timeout(self, cm):
        assert cm._get_startup_timeout('S7BEN-MED-007') == 60

    def test_hard_timeout(self, cm):
        assert cm._get_startup_timeout('S7BEN-HARD-001') == 120

    def test_vhard_timeout(self, cm):
        assert cm._get_startup_timeout('S7BEN-VHARD-003') == 300

    def test_cve_timeout(self, cm):
        assert cm._get_startup_timeout('S7BEN-CVE-005') == 300

    def test_unknown_tier_falls_back_to_default(self, cm):
        assert cm._get_startup_timeout('S7BEN-FUTURE-001') == ContainerManager.DEFAULT_STARTUP_TIMEOUT

    def test_malformed_id_falls_back_to_default(self, cm):
        assert cm._get_startup_timeout('garbage') == ContainerManager.DEFAULT_STARTUP_TIMEOUT


# ── TIER_TIMEOUTS constant integrity ─────────────────────────────────

class TestTierTimeoutsConstant:
    def test_all_expected_tiers_present(self):
        expected = {'EASY', 'MED', 'HARD', 'VHARD', 'CVE'}
        assert set(ContainerManager.TIER_TIMEOUTS.keys()) == expected

    def test_values_are_positive_integers(self):
        for tier, timeout in ContainerManager.TIER_TIMEOUTS.items():
            assert isinstance(timeout, int), f"{tier} timeout is not int"
            assert timeout > 0, f"{tier} timeout must be positive"

    def test_heavier_tiers_have_longer_timeouts(self):
        t = ContainerManager.TIER_TIMEOUTS
        assert t['EASY'] <= t['MED'] <= t['HARD'] <= t['VHARD']
        assert t['CVE'] >= t['HARD']
