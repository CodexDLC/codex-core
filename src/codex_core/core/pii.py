"""PII field registry and masking utilities for GDPR-safe logging."""

from __future__ import annotations

from typing import Any

# Keywords for partial case-insensitive matching in field names.
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

MASK = "***"


def is_pii_field(field_name: str) -> bool:
    """Return True if field name matches any PII keyword (case-insensitive)."""
    name_lower = field_name.lower()
    return any(kw in name_lower for kw in PII_KEYWORDS)


def mask_value(field_name: str, value: Any) -> Any:
    """
    Return masked value if field is PII, otherwise return as-is.
    Recursively masks values in nested dictionaries.
    """
    if is_pii_field(field_name):
        return MASK

    if isinstance(value, dict):
        return {k: mask_value(k, v) for k, v in value.items()}

    if isinstance(value, list):
        return [mask_value(field_name, item) for item in value]

    return value
