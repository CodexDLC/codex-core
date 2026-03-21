<!-- Type: LANDING -->
# codex-core

[![PyPI](https://img.shields.io/pypi/v/codex-core)](https://pypi.org/project/codex-core/)
[![Python](https://img.shields.io/pypi/pyversions/codex-core)](https://pypi.org/project/codex-core/)
[![License](https://img.shields.io/badge/license-Apache--2.0-green)](https://github.com/codexdlc/codex-core/blob/main/LICENSE)
[![Documentation](https://img.shields.io/badge/docs-codexdlc.github.io-blue)](https://codexdlc.github.io/codex-core/)

Core utilities, immutable DTOs, and environment-driven settings for the Codex WaaS toolkit.
Provides the foundational building blocks and PII masking used by all other Codex components.

---

## Install

```bash
# Core only
pip install codex-core

# With Loguru support for advanced structured logging
pip install "codex-core[loguru]"
```

## Quick Start

```python
from codex_core.core.base_dto import BaseDTO

# 1. Define an immutable, PII-aware data transfer object
class UserDTO(BaseDTO):
    id: int
    email: str         # Automatically masked in logs
    phone_number: str  # Automatically masked in logs

user = UserDTO(id=42, email="user@example.com", phone_number="+491511234567")

# 2. Safely log the DTO without leaking personal data
print(user)
# Output: UserDTO(id=42, email='***', phone_number='***')
```

## Modules

| Module | Extra | Description |
| :--- | :--- | :--- |
| `codex_core.core` | - | Immutable `BaseDTO` and automated `PIIRegistry` for GDPR-safe logging. |
| `codex_core.common` | `[loguru]` | Phone/name normalization and structured logging adapters (`TaskLogContext`). |
| `codex_core.settings` | - | Environment-driven configuration via `BaseCommonSettings` (Pydantic Settings). |
| `codex_core.dev` | `[dev]` | Internal developer tools (`BaseCheckRunner`, `StaticCompiler`, `ProjectTreeGenerator`). |

## Documentation

Full docs with architecture, API reference, and data flow diagrams:

**[https://codexdlc.github.io/codex-core/](https://codexdlc.github.io/codex-core/)**

## Part of the Codex ecosystem

| Package | Role |
| :--- | :--- |
| **codex-core** | Foundation — immutable DTOs, PII masking, env settings |
| [codex-platform](https://github.com/codexdlc/codex-platform) | Infrastructure — Redis, Streams, ARQ workers, Notifications |
| [codex-ai](https://github.com/codexdlc/codex-ai) | LLM layer — unified async interface for OpenAI, Gemini, Anthropic |
| [codex-services](https://github.com/codexdlc/codex-services) | Business logic — Booking engine, CRM, Calendar |

Each library is **fully standalone** — install only what your project needs.
Together they form the backbone of **[codex-bot](https://github.com/codexdlc/codex-bot)**
(Telegram AI-agent infrastructure built on aiogram) and
**[codex-django](https://github.com/codexdlc/codex-django)** (Django integration layer).
