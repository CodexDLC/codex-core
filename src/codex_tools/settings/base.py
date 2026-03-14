"""
Base settings for all services (Django, Bot, Worker).

Extend in your project to add service-specific fields:

```python
class MySettings(BaseCommonSettings):
    log_level: str = "INFO"
    redis_site_settings_key: str = "site_settings_hash"

    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
```

Note: `env_file` is NOT set here - the project sets it via `model_config` override.
"""

import os
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseCommonSettings(BaseSettings):
    """
    Base settings for all services (Django, Bot, Worker).
    Does NOT load `.env` automatically - this must be configured in the child class.

    Example of a proper implementation in a project:
    ```python
    from codex_tools.settings import BaseCommonSettings
    from pathlib import Path

    class ProjectSettings(BaseCommonSettings):
        # Add your own fields
        my_api_key: str = "secret"

        # Mandatory: specify where to look for .env
        model_config = SettingsConfigDict(
            env_file=Path(__file__).parent / ".env",
            env_file_encoding="utf-8",
            extra="ignore",
        )
    ```
    """

    debug: bool = True
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str | None = None
    redis_max_connections: int = 50
    redis_timeout: int = 5

    @property
    def is_inside_docker(self) -> bool:
        """Returns True if running inside a Docker container."""
        return os.path.exists("/.dockerenv")

    @property
    def effective_redis_host(self) -> str:
        """Returns the effective Redis host (resolves 'localhost' → 'redis' inside Docker)."""
        if self.redis_host != "localhost":
            return self.redis_host
        return "redis" if self.is_inside_docker else "localhost"

    @property
    def redis_url(self) -> str:
        """
        Returns the Redis connection URL.
        Automatically masks quotes in passwords and handles host resolution.
        """
        host = self.effective_redis_host
        password = self.redis_password
        if password:
            password = password.strip("'\"").strip()
            return f"redis://:{quote_plus(password)}@{host}:{self.redis_port}"
        return f"redis://{host}:{self.redis_port}"

    @property
    def is_production(self) -> bool:
        """Returns True if running in production mode (debug=False)."""
        return not self.debug

    @property
    def is_development(self) -> bool:
        """Returns True if running in development mode (debug=True)."""
        return self.debug

    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        extra="ignore",
        # env_file НЕ задаём здесь — проект задаёт сам через override
    )
