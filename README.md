# codex-core

**Core utilities, schemas, and settings for the Codex WaaS toolkit.**

[![PyPI](https://img.shields.io/pypi/v/codex-core)](https://pypi.org/project/codex-core/)
[![Python](https://img.shields.io/pypi/pyversions/codex-core)](https://pypi.org/project/codex-core/)
[![License](https://img.shields.io/badge/license-Apache--2.0-green)](https://github.com/codexdlc/codex-core/blob/main/LICENSE)
[![Documentation](https://img.shields.io/badge/docs-codexdlc.github.io-blue)](https://codexdlc.github.io/codex-core/)

This library provides the foundational building blocks used by all other Codex tools. It focuses on Pydantic-based data models, structured logging, and configuration management.

> **Documentation:**
> [EN](https://codexdlc.github.io/codex-core/en_EN/) · [RU](https://codexdlc.github.io/codex-core/ru_RU/) · [API Reference](https://codexdlc.github.io/codex-core/api/) · [Changelog](https://codexdlc.github.io/codex-core/changelog/)

## 🚀 Key Features

*   **Core Interfaces**: Base classes and protocols for Codex components.
*   **Common Utilities**: Logger setup (Loguru), phone number validation, text processing, and caching.
*   **Schemas**: Shared Pydantic models for cross-service communication.
*   **Settings**: Modern configuration management using `pydantic-settings`.

## 📦 Installation

```bash
pip install codex-core
```

## 🛠️ Quick Start

```python
from codex_tools.common.logger import setup_logger

logger = setup_logger("my-app")
logger.info("Codex Core is ready!")
```

---
*Part of the [Codex WaaS](https://github.com/codexdlc) ecosystem. · [EN Docs](https://codexdlc.github.io/codex-core/en_EN/) · [RU Docs](https://codexdlc.github.io/codex-core/ru_RU/) · [API](https://codexdlc.github.io/codex-core/api/) · [Changelog](https://codexdlc.github.io/codex-core/changelog/) · [Source](https://github.com/codexdlc/codex-core)*
