"""PII field registry and masking utilities for GDPR-safe logging.

This module is the single source of truth for Personally Identifiable
Information (PII) detection within codex_core.  It is consumed by
:class:`~codex_core.core.base_dto.BaseDTO` to scrub sensitive fields
before any string serialization reaches a log sink.

The detection strategy supports two modes:

1. **Declarative Registry (Recommended)**: Subclass :class:`PIIRegistry`
   to list exact field names from your database or domain model. This
   disables heuristic "magic" matching and uses only your specified fields.

2. **Heuristic Fallback**: If no registry is defined, the module uses
   keyword-based substring matching (phone, email, name, etc.).

Example:
    ```python
    from codex_core.core.pii import PIIRegistry

    class DatabasePII(PIIRegistry):
        # Match these exact column names from your DB
        user_phone: str
        customer_email: str
    ```
"""

from __future__ import annotations

import logging
from typing import Any, ClassVar

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Declarative Registry
# ---------------------------------------------------------------------------


class PIIRegistry:
    """Base class for declaring an explicit PII field registry.

    Subclass this and list your sensitive field names as class attributes
    or type annotations. The registry automatically collects these names.

    When any subclass of PIIRegistry is defined, the global masking logic
    switches from "substring matching" to "exact match" against these fields.
    """

    _registered_fields: ClassVar[frozenset[str]] = frozenset()

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Collect field names from annotations and class attributes."""
        super().__init_subclass__(**kwargs)

        # Collect from annotations: email: str -> "email" (normalized to lowercase)
        fields = {k.lower() for k in cls.__annotations__}

        # Collect from class attributes: phone = True -> "phone" (normalized to lowercase)
        fields.update(
            name.lower() for name, value in cls.__dict__.items() if not name.startswith("_") and not callable(value)
        )

        # Merge into global singleton registry
        new_fields = set(PIIRegistry._registered_fields)
        new_fields.update(fields)
        PIIRegistry._registered_fields = frozenset(new_fields)

        logger.debug(f"PII Registry updated. Fields: {list(PIIRegistry._registered_fields)}")


# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

PII_KEYWORDS: frozenset[str] = frozenset(
    {
        "phone",
        "email",
        "name",
        "address",
        "note",
        "comment",
        "phone_number",
        "email_address",
    }
)
"""Immutable set of substrings used for heuristic PII detection."""

MASK: str = "***"
"""Redaction placeholder substituted for PII field values in logs."""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def is_pii_field(field_name: str) -> bool:
    """Determine whether a field name should be masked.

    The check follows this priority:
    1. If a :class:`PIIRegistry` is defined, it checks for an exact match
       (case-insensitive) against the registered fields.
    2. Otherwise, it performs a case-insensitive substring search against
       :data:`PII_KEYWORDS`.

    Args:
        field_name: The field name to evaluate.

    Returns:
        ``True`` if the field matches the PII criteria, ``False`` otherwise.
    """
    name_lower = field_name.lower()

    # Priority 1: Explicit Registry (Exact match)
    if PIIRegistry._registered_fields:
        return name_lower in PIIRegistry._registered_fields

    # Priority 2: Heuristic Fallback (Substring match)
    return any(kw in name_lower for kw in PII_KEYWORDS)


def mask_value(field_name: str, value: Any) -> Any:
    """Return a redacted representation of *value* when the field is PII.

    Applies :data:`MASK` as a flat replacement for scalar PII fields.
    For non-PII fields the function recurses into ``dict`` and ``list``
    containers so that nested structures are also scrubbed.

    Args:
        field_name: Name of the field being evaluated.
        value: The value to inspect and potentially redact.

    Returns:
        :data:`MASK` for PII fields; a recursively masked ``dict`` or
        ``list`` for containers; or the original *value* unchanged.
    """
    if is_pii_field(field_name):
        return MASK

    if isinstance(value, dict):
        return {k: mask_value(k, v) for k, v in value.items()}

    if isinstance(value, list):
        return [mask_value(field_name, item) for item in value]

    return value
