# codex-core

**Core utilities, schemas, and settings for the Codex WaaS toolkit.**

This library provides the foundational building blocks used by all other Codex tools. It focuses on Pydantic-based data models, structured logging, and configuration management.

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
*Part of the [Codex WaaS](https://github.com/codexdlc) ecosystem.*
