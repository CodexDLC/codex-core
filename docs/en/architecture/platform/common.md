[🏠 Home](../../../index.md) | [🧭 Guide (EN)](../../README.md) | [🛠️ Common API](../../api/common.md)

# 🛠️ Common: Utilities (Architecture)

This section describes the shared utility functions that facilitate common tasks within the **codex-core** ecosystem.

## Domain Goal
The `common` domain provides a collection of robust, standardized, and framework-agnostic utilities to reduce boilerplate and prevent errors across multiple projects.

## 1. Phone Normalization
Standardized phone number formatting is essential for communication and consistency.

### Features:
- **International Support**: Handles `+49`, `0049`, and other international prefixes correctly.
- **Local Formats**: Automatically converts local German numbers (starting with `0`) to the international `49` format.
- **Robust Cleaning**: Removes non-digit characters while preserving important structure.

```python
from codex_core.common.phone import normalize_phone

# Output: "491511234567"
normalize_phone("0151 1234567")
normalize_phone("+49 151 1234567")
```

## 2. Name Normalization
A utility for correctly formatting first and last names, ensuring consistency in databases and communications.

### Key Logic:
- **Case Correction**: Automatically capitalizes names correctly (e.g., `ivan` -> `Ivan`).
- **Compound Names**: Correctly handles hyphenated and space-separated names (e.g., `ivanov-petrov` -> `Ivanov-Petrov`).
- **Space Management**: Removes extra spaces while preserving necessary separators.

## 3. Structured Logging
The `TaskLogContext` helper simplifies logging for structured background operations and tasks.

### Advantages:
- **Automatic Fields**: Adds `task` and `context` names to every log record.
- **Compatibility**: Works seamlessly with standard `logging` and third-party tools like `loguru` and ELK.
- **Traceability**: Makes it easy to filter logs by task or context in your log management system.
