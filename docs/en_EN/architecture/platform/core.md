[🏠 Home](../../../index.md) | [🧭 Guide (EN)](../../README.md) | [🛡️ Core API](../../../api/core.md)

# 🛡️ Core: PII & DTO (Architecture)

This section describes how data is structured and protected within the **codex-core** ecosystem.

## Domain Goal
The primary goal of the `core` domain is to ensure that personal data (PII) is never accidentally leaked into logs, while maintaining an immutable and standardized data representation for internal logic.

## 1. Automated PII Masking
The `BaseDTO` automatically masks sensitive information in its `repr` and `str` methods.

### How it works:
1. **Keyword matching**: If a field name contains any of the predefined keywords (`phone`, `email`, `name`, `address`, `note`, `comment`), its value will be replaced by `***` in logs.
2. **Recursive masking**: If a field is not directly PII, but contains a dictionary or a list of dictionaries (e.g., `metadata`), the library will recursively scan those for PII keywords.

### Example:
```python
from codex_core.core import BaseDTO

class OrderDTO(BaseDTO):
    order_id: int
    customer_email: str  # Will be masked
    notes: str           # Will be masked
    meta: dict           # Scanned recursively
```

## 2. Immutability
All DTOs are **frozen** by default (using `pydantic.ConfigDict(frozen=True)`). This ensures that data cannot be modified after creation, which is essential for multi-threaded and concurrent environments.

## Best Practices
- **Do not log DTOs in hot paths**: While efficient, the PII masking logic still introduces some overhead. Avoid logging DTOs inside tight loops or high-frequency backtracking algorithms.
- **Use meaningful field names**: Always name your fields according to their contents. If you name a phone number field as `p`, it won't be masked automatically. Use `phone`, `user_phone`, etc.
- **Explicit masking**: If you have a sensitive field that doesn't match our keywords, you can still mask it by naming it accordingly (e.g., `secret_note`).
