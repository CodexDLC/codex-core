"""Environment-driven base settings shared across all codex_tools services.

Provides :class:`BaseCommonSettings`, the canonical superclass for
every application settings class in the codex_tools ecosystem (Django
web server, Telegram bot, async worker, CLI tool, etc.).

Design decisions:

- **No automatic .env loading** — ``env_file`` is intentionally absent
  from the base ``model_config``.  Each consuming project must override
  ``model_config`` with the project-local ``.env`` path.  This prevents
  the library from silently reading an unexpected file when imported.
- **Redis by default** — Redis connection parameters are present at
  the base level because every codex_tools service uses Redis as a
  shared cache / broker.  Services that do not use Redis can simply
  leave the defaults in place.
- **Computed properties** — :attr:`redis_url`, :attr:`is_production`,
  and :attr:`is_development` are read-only properties rather than
  stored fields to ensure they are always derived from the current
  field values and cannot be set incorrectly via environment variables.

Usage::

    from codex_core.settings import BaseCommonSettings
    from pathlib import Path
    from pydantic_settings import SettingsConfigDict

    class BookingSettings(BaseCommonSettings):
        calendar_api_key: str

        model_config = SettingsConfigDict(
            env_file=Path(__file__).parent / ".env",
            env_file_encoding="utf-8",
            extra="ignore",
        )

    settings = BookingSettings()
"""

from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseCommonSettings(BaseSettings):
    """Shared environment-driven settings for all codex_tools services.

    Subclass this in each project and override ``model_config`` to
    point at the project's ``.env`` file.  All fields defined here
    can be overridden via environment variables following pydantic-
    settings conventions (upper-case, optional prefix).

    Attributes:
        debug: When ``True`` the service runs in development mode:
            verbose logging, detailed error pages, non-production
            credentials.  Defaults to ``True`` so that misconfigured
            deployments fail loudly rather than silently entering
            production mode.
        redis_host: Hostname or IP of the Redis server.
        redis_port: TCP port of the Redis server.
        redis_password: Optional password for Redis AUTH.  When set,
            it is URL-encoded before being embedded in
            :attr:`redis_url` to handle special characters safely.
        redis_max_connections: Maximum number of connections in the
            connection pool.
        redis_timeout: Socket timeout in seconds for Redis operations.

    Note:
        ``model_config`` at this level intentionally omits ``env_file``
        so that child classes control which ``.env`` file is loaded.
        Do not add ``env_file`` here.

    Example:
        ```python
        from codex_core.settings import BaseCommonSettings
        from pathlib import Path
        from pydantic_settings import SettingsConfigDict

        class ProjectSettings(BaseCommonSettings):
            my_api_key: str = "changeme"

            model_config = SettingsConfigDict(
                env_file=Path(__file__).parent / ".env",
                env_file_encoding="utf-8",
                extra="ignore",
            )

        settings = ProjectSettings()
        print(settings.redis_url)   # → "redis://localhost:6379"
        print(settings.is_production)  # → False  (debug=True by default)
        ```
    """

    debug: bool = True
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str | None = None
    redis_max_connections: int = 50
    redis_timeout: int = 5

    @property
    def redis_url(self) -> str:
        """Construct a Redis connection URL from the current field values.

        Uses ``urllib.parse.quote_plus`` to percent-encode the password
        so that special characters (``@``, ``/``, ``#``, etc.) do not
        corrupt the URL structure.

        Returns:
            A ``redis://`` URL string.  Format:

            - Without password: ``redis://<host>:<port>``
            - With password: ``redis://:<encoded_password>@<host>:<port>``
        """
        if self.redis_password:
            safe_password = quote_plus(self.redis_password)
            return f"redis://:{safe_password}@{self.redis_host}:{self.redis_port}"

        return f"redis://{self.redis_host}:{self.redis_port}"

    @property
    def is_production(self) -> bool:
        """Return ``True`` when the service is running in production mode.

        Production mode is defined as ``debug=False``.  Use this
        property in conditional code paths that must behave differently
        in production (e.g. disabling detailed tracebacks in API
        responses).

        Returns:
            ``True`` if ``debug`` is ``False``, ``False`` otherwise.
        """
        return not self.debug

    @property
    def is_development(self) -> bool:
        """Return ``True`` when the service is running in development mode.

        Development mode is defined as ``debug=True`` (the default).
        Convenience inverse of :attr:`is_production`.

        Returns:
            ``True`` if ``debug`` is ``True``, ``False`` otherwise.
        """
        return self.debug

    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        extra="ignore",
    )
