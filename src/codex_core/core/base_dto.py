"""Immutable base DTO with GDPR-safe string representation.

Provides :class:`BaseDTO`, the canonical superclass for all Data
Transfer Objects in the codex_core ecosystem.  Every DTO that crosses
a service boundary (API layer → domain layer, domain layer → log sink)
should extend this class to guarantee immutability and automatic PII
redaction in log output.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from .pii import mask_value


class BaseDTO(BaseModel):
    """Immutable Pydantic model with automatic PII masking in ``__repr__``.

    Acts as the single inheritance root for all DTOs across codex_core
    and downstream libraries.  Two invariants are enforced at the class
    level:

    1. **Immutability** — ``model_config = ConfigDict(frozen=True)``
       prevents in-place mutation after construction, making instances
       safe to pass across async boundaries and to cache.

    2. **GDPR-safe logging** — ``__repr__`` (and therefore ``__str__``)
       delegates to :func:`~codex_core.core.pii.mask_value` for every
       field, replacing sensitive fields with ``"***"``.  Which fields
       are masked depends on the active detection mode in
       :mod:`~codex_core.core.pii`: exact-match against
       :class:`~codex_core.core.pii.PIIRegistry` when a subclass is
       defined, or heuristic keyword-based matching otherwise.  Nested
       ``dict`` values are recursively scrubbed.

    Subclasses must **not** override ``model_config`` in a way that
    removes ``frozen=True`` unless the calling code explicitly manages
    mutation safety.

    Performance note:
        ``__repr__`` iterates over all fields on every call.  Avoid
        logging ``BaseDTO`` instances inside tight loops (e.g. backtracking
        search algorithms).  Prefer logging at entry/exit points of
        public API methods only.

    Example:
        ```python
        from codex_core.core.base_dto import BaseDTO
        from codex_core.core.pii import PIIRegistry

        class UserPII(PIIRegistry):
            email: str
            phone_number: str

        class AppointmentDTO(BaseDTO):
            appointment_id: int
            client_name: str
            email: str
            slot_count: int

        dto = AppointmentDTO(
            appointment_id=7,
            client_name="Alice Müller",
            email="alice@example.com",
            slot_count=2,
        )
        print(dto)
        # AppointmentDTO(appointment_id=7, client_name='Alice Müller', email='***', slot_count=2)
        # Note: client_name is NOT masked because UserPII specified ONLY email/phone_number.
        ```
    """

    model_config = ConfigDict(frozen=True)

    def __repr__(self) -> str:
        """Build a PII-safe string representation of this DTO instance.

        Iterates over all instance fields and passes each ``(field_name,
        value)`` pair through :func:`~codex_core.core.pii.mask_value`
        before formatting.  The result follows the standard Pydantic
        repr convention ``ClassName(field=value, ...)``.

        Returns:
            A human-readable string suitable for log output with all
            PII fields replaced by ``"***"``.
        """
        cls_name = type(self).__name__
        pairs: list[str] = [
            f"{field_name}={mask_value(field_name, value)!r}" for field_name, value in self.__dict__.items()
        ]
        return f"{cls_name}({', '.join(pairs)})"

    __str__ = __repr__
