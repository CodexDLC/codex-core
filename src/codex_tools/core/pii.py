"""PII field registry and masking utilities for GDPR-safe logging."""

from __future__ import annotations

PII_FIELDS: frozenset[str] = frozenset(
    {
        "first_name",
        "last_name",
        "phone",
        "email",
        "notes",
        "comment",
        "address",
        "recipient_phone",
        "recipient_email",
    }
)

MASK = "***"


def mask_value(field_name: str, value: object) -> object:
    """Return masked value if field is PII, otherwise return as-is."""
    if field_name in PII_FIELDS:
        return MASK
    return value
