#!/usr/bin/env python3
"""Tests for provider_config.py — central provider configuration."""
import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestProviderConfig:
    """Tests for PROVIDERS dict structure and helper functions."""

    def test_all_three_providers_present(self):
        from utils.provider_config import PROVIDERS
        assert 'google' in PROVIDERS
        assert 'anthropic' in PROVIDERS
        assert 'openai' in PROVIDERS

    def test_provider_has_required_keys(self):
        from utils.provider_config import PROVIDERS
        required_keys = {
            'cli_command', 'json_flag', 'auto_approve_flags',
            'prompt_file', 'chars_per_token', 'input_output_split',
        }
        for provider, config in PROVIDERS.items():
            missing = required_keys - set(config.keys())
            assert not missing, f"{provider} missing keys: {missing}"

    def test_tier_timeouts_present(self):
        from utils.provider_config import TIER_TIMEOUTS
        for tier in ('EASY', 'MED', 'HARD', 'VHARD', 'CVE'):
            assert tier in TIER_TIMEOUTS
            timeout = TIER_TIMEOUTS[tier]
            assert 'max_turns' in timeout
            assert 'timeout_s' in timeout
            assert timeout['timeout_s'] > 0
            assert timeout['max_turns'] > 0

    def test_tier_timeouts_increase_with_difficulty(self):
        from utils.provider_config import TIER_TIMEOUTS
        assert TIER_TIMEOUTS['EASY']['timeout_s'] < TIER_TIMEOUTS['HARD']['timeout_s']
        assert TIER_TIMEOUTS['HARD']['timeout_s'] < TIER_TIMEOUTS['VHARD']['timeout_s']

    def test_get_cli_command_google(self):
        from utils.provider_config import get_cli_command
        cmd = get_cli_command('google', 'gemini-2.5-flash', 'test prompt', 'EASY')
        assert cmd[0] == 'gemini'
        assert '--output-format=json' in cmd

    def test_get_cli_command_anthropic(self):
        from utils.provider_config import get_cli_command
        cmd = get_cli_command('anthropic', 'claude-sonnet-4.5', 'test prompt', 'EASY')
        assert cmd[0] == 'claude'
        assert '--output-format=json' in cmd

    def test_get_cli_command_openai(self):
        from utils.provider_config import get_cli_command
        cmd = get_cli_command('openai', 'gpt-4.1', 'test prompt', 'EASY')
        assert cmd[0] == 'codex'

    def test_get_cli_command_unknown_provider_raises(self):
        from utils.provider_config import get_cli_command
        with pytest.raises(ValueError, match="Unknown provider"):
            get_cli_command('xai', 'grok', 'prompt', 'EASY')

    def test_get_cli_command_includes_model_switch(self):
        from utils.provider_config import get_cli_command
        cmd_str = ' '.join(get_cli_command('google', 'gemini-2.5-pro', 'test', 'EASY'))
        assert 'gemini-2.5-pro' in cmd_str

    def test_valid_token_sources(self):
        from utils.provider_config import VALID_TOKEN_SOURCES
        assert 'exact' in VALID_TOKEN_SOURCES
        assert 'estimated' in VALID_TOKEN_SOURCES
        assert 'manual' in VALID_TOKEN_SOURCES
        assert 'unavailable' in VALID_TOKEN_SOURCES
