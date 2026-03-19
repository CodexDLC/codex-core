[🏠 Home](../index.md) | [🧭 Guide (EN)](../en/README.md) | [🗺 Roadmap](roadmap.md)

# Evolution & Philosophy

**codex-core** is the foundational layer for the entire Codex ecosystem. It serves as a shared base for our specialized libraries and services, ensuring architectural consistency across the board.

## Core Purpose
This library is a collection of "source-of-truth" components that are:
- **Reusable**: Core settings and PII patterns that shouldn't be duplicated.
- **Universal**: Framework-agnostic utility scripts and common helpers.
- **Standardized**: A unified way to handle data masking and configuration.

## Direct Usage
While **codex-core** is a primary dependency for our internal stack, it is designed as a standalone, lightweight package. Any project requiring robust Pydantic-based settings, immutable DTOs, or reliable data normalization (phones, names) can use this library directly.

## How it Evolves
We don't add features for the sake of features. The evolution of **codex-core** is driven by the needs of our higher-level projects. When we identify a stable, universal pattern in a specific service, we migrate it here to make it available for everyone.
