import os

import pytest

from codex_core.settings.base import BaseCommonSettings

pytestmark = pytest.mark.integration


def test_settings_load_from_env(tmp_path):
    """
    Integration test: check if settings correctly pick up environment variables.
    This simulates how the library would behave in a real project environment.
    """
    # 1. Prepare environment variables
    os.environ["REDIS_HOST"] = "remote.redis.com"
    os.environ["REDIS_PORT"] = "9999"
    os.environ["DEBUG"] = "False"

    try:
        # 2. Initialize settings (Pydantic automatically reads from environment)
        settings = BaseCommonSettings()

        # 3. Verify real behavior
        assert settings.redis_host == "remote.redis.com"
        assert settings.redis_port == 9999
        assert settings.is_production is True
        assert "redis://remote.redis.com:9999" in settings.redis_url

    finally:
        # Cleanup environment variables to avoid side effects
        del os.environ["REDIS_HOST"]
        del os.environ["REDIS_PORT"]
        del os.environ["DEBUG"]
