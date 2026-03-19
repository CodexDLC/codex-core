[🏠 Home](../../index.md) | [⚙️ API Reference](index.md) | [🛡️ Core API](core.md)

# 🛡️ Core API (DTO & PII)

This section describes the essential data models and security utilities of the **codex-core** library.

## BaseDTO
`BaseDTO` is an immutable Pydantic model with built-in PII masking for `repr` and `str`.

::: codex_core.core.base_dto

## PII Protection
Utilities for identifying and masking sensitive data.

::: codex_core.core.pii
