"""Base exception hierarchy for the codex_core library.

All domain-specific exceptions raised by codex_core subpackages and
downstream libraries (e.g. codex-business) must inherit from
:class:`CodexToolsError`.  This single root makes it possible for
consumers to write a single ``except CodexToolsError`` clause to catch
any library-level error without accidentally suppressing unrelated
runtime exceptions.

Usage pattern in dependent packages::

    from codex_core.core.exceptions import CodexToolsError

    class BookingError(CodexToolsError):
        \"\"\"Raised when a booking operation cannot be completed.\"\"\"
"""

from __future__ import annotations


class CodexToolsError(Exception):
    """Root exception for all errors originating within codex_core.

    Serves as the common base class for the entire codex_tools exception
    hierarchy.  Downstream packages (codex-business, codex-ai, etc.)
    define their own subclasses to communicate domain-specific failure
    modes while remaining catchable via a single ``except`` clause at
    integration boundaries.

    This class adds no additional state beyond ``Exception``; the
    *message* argument follows the standard ``Exception(message)``
    convention.

    Raises:
        CodexToolsError: Re-raised by subclasses to propagate structured
            errors up through service layers.

    Example:
        ```python
        from codex_core.core.exceptions import CodexToolsError

        class SlotUnavailableError(CodexToolsError):
            \"\"\"Raised when the requested time slot is no longer available.\"\"\"

        try:
            book_slot(slot_id=42)
        except CodexToolsError as exc:
            logger.error("Library error: %s", exc)
        ```
    """
