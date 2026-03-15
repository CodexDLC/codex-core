"""BaseDTO with GDPR-safe __repr__ (PII masking)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from .pii import mask_value


class BaseDTO(BaseModel):
    """
    Immutable base model for all codex_core DTOs.

    PII masking: __repr__ and __str__ replace personal data fields
    (names, phones, emails, notes, comments, addresses) with '***'.
    Recursively masks nested dictionaries.

    PERFORMANCE NOTE: Do NOT log BaseDTO subclasses in hot paths
    (e.g. inside ChainFinder backtracking loops).
    Use only at entry/exit points of public API methods.
    """

    model_config = ConfigDict(frozen=True)

    def __repr__(self) -> str:
        cls_name = type(self).__name__
        pairs: list[str] = [
            f"{field_name}={mask_value(field_name, value)!r}"
            for field_name, value in self.__dict__.items()
        ]
        return f"{cls_name}({', '.join(pairs)})"

    __str__ = __repr__
