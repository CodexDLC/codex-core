[🏠 Home](../../index.md) | [🧭 Guide (EN)](../README.md) | [🚀 Getting Started](getting_started.md)

# Getting Started (EN)

Welcome! This guide will help you integrate **codex-core** into your project quickly and correctly.

## Installation

Install the library using pip:

```bash
pip install codex-core
```

### Installation from Source
If you need the latest changes from the `main` branch, you can install it directly from the repository:

```bash
pip install git+https://github.com/codexdlc/codex-core.git
```

### Optional Dependencies
If you want to use the pre-configured Loguru setup, you'll need to install `loguru` manually:

```bash
pip install loguru
```

## First Steps

### 1. Create a BaseDTO
Inherit from `BaseDTO` to get automated PII masking in your logs:

```python
from codex_core.core import BaseDTO

class UserDTO(BaseDTO):
    full_name: str
    email: str
    phone: str
```

### 2. Configure Settings
Use `BaseCommonSettings` for a standardized environment variable loading:

```python
from codex_core.settings import BaseCommonSettings

class ProjectSettings(BaseCommonSettings):
    my_api_key: str = "secret"
```

## Next Steps
Check out the [🛡️ Architecture Guide](../architecture/README.md) for more details.
