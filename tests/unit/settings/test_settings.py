import pytest

from codex_core.settings.base import BaseCommonSettings

pytestmark = pytest.mark.unit


def test_redis_url_without_password():
    settings = BaseCommonSettings(redis_host="redis_server", redis_port=6379, redis_password=None)
    assert settings.redis_url == "redis://redis_server:6379"


def test_redis_url_with_password():
    settings = BaseCommonSettings(redis_host="localhost", redis_port=6379, redis_password="my@password#123")
    # Password must be escaped (quote_plus)
    # '@' -> '%40', '#' -> '%23'
    assert settings.redis_url == "redis://:my%40password%23123@localhost:6379"


def test_debug_flags():
    settings_dev = BaseCommonSettings(debug=True)
    assert settings_dev.is_development is True
    assert settings_dev.is_production is False

    settings_prod = BaseCommonSettings(debug=False)
    assert settings_prod.is_development is False
    assert settings_prod.is_production is True
