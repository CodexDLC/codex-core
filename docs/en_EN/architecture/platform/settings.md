[🏠 Home](../../../index.md) | [🧭 Guide (EN)](../../README.md) | [⚙️ Settings API](../../../api/settings.md)

# ⚙️ Settings: Config Architecture

This section describes the base configuration patterns used to manage application settings across the **codex-core** ecosystem.

## Domain Goal
The `settings` domain provides a robust and standardized base for loading configuration from environment variables and `.env` files, specifically designed to handle common infrastructure like Redis.

## 1. BaseCommonSettings
`BaseCommonSettings` is an immutable Pydantic Settings model that serves as the foundation for project-specific configurations.

### Key Features:
- **Redis Connection**: Automatically builds a `redis_url` property from host, port, and password.
- **Safe Passwords**: Uses `quote_plus` to ensure special characters in passwords don't break the connection string.
- **Environment Aware**: Provides `is_production` and `is_development` flags based on the `debug` setting.

## 2. Project Implementation
Projects should inherit from `BaseCommonSettings` and define their own `model_config` to specify the location of the `.env` file.

```python
from codex_core.settings import BaseCommonSettings
from pydantic_settings import SettingsConfigDict
from pathlib import Path

class ProjectSettings(BaseCommonSettings):
    # Project-specific settings
    my_api_token: str = "secret"

    # Mandatory: specify where to look for .env
    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
```

## Best Practices
- **Never commit .env**: Ensure `.env` files are in `.gitignore`.
- **Use clear naming**: Prefer descriptive environment variable names like `REDIS_PASSWORD` over generic ones.
- **Explicit defaults**: Define sensible defaults in your settings class for local development.
