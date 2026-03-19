[🏠 Home](../../index.md) | [🧭 Guide (EN)](../README.md) | [🛡️ Architecture](../api/index.md)

# 🛡️ Architecture & Platform Overview (EN)

This section provides a high-level overview of the architectural patterns and foundational components provided by the **codex-core** library.

## Domain Structure
We divide the platform into three main domains, each serving a specific purpose:

| Domain | Description | Key Components |
| :--- | :--- | :--- |
| **[🛡️ Core](platform/core.md)** | Essential data models and security. | `BaseDTO`, PII Masking, `mask_value`. |
| **[🛠️ Common](platform/common.md)** | Standardized utility functions. | `normalize_phone`, `normalize_name`, `TaskLogContext`. |
| **[⚙️ Settings](platform/settings.md)** | Infrastructure configuration. | `BaseCommonSettings`, `redis_url`. |

## Core Principles
1. **Security First**: PII protection is integrated at the base DTO level.
2. **Immutability**: Data models are frozen by default to prevent side effects.
3. **Standardization**: Common tasks (phone, name, logging) are solved once for all Codex projects.
4. **Developer Friendly**: Comprehensive documentation and type hinting ensure a smooth experience.

## Next Steps
- Read about [🛡️ Core: PII & DTO](platform/core.md).
- Explore [🛠️ Common Utilities](platform/common.md).
- Understand [⚙️ Settings Architecture](platform/settings.md).
