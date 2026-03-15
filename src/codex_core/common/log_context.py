"""Structured logging context bound to a named task or worker.

Provides :class:`TaskLogContext` — a thin, stateful wrapper around
``logging.Logger`` that automatically enriches every log record with
a fixed set of structured fields (task name, worker name, arbitrary
extras).

This module intentionally avoids any dependency on Loguru so that it
works with any log sink: standard-library ``logging``, Loguru (via
:class:`~codex_core.common.loguru_setup.InterceptHandler`), JSON
formatters, ELK, or Loki.

Example:
    ```python
    from codex_core.common.log_context import TaskLogContext

    log = TaskLogContext("send_booking_notification", worker="notification_worker")
    log.info("Processing appointment", extra={"appointment_id": 123})
    # LogRecord contains: task="send_booking_notification",
    #   worker="notification_worker", appointment_id=123
    ```
"""

import logging
from typing import Any


class TaskLogContext:
    """Structured logging adapter that binds context fields to every record.

    Wraps a standard ``logging.Logger`` and automatically merges a
    fixed ``_base_extra`` dict (built at construction time) with any
    per-call ``extra`` dict before forwarding the record.  This
    eliminates repetitive ``extra={"task": ...}`` boilerplate in
    worker loops.

    The class is **stateful** in the sense that ``_base_extra`` is
    set once at construction and shared across all log calls.  It is
    **not** thread-safe to mutate ``_base_extra`` after construction;
    create a new instance per task if context must change.

    Args:
        task_name: Logical name of the current operation
            (e.g. ``"send_booking_notification"``).  Stored as
            ``task`` in every log record's ``extra``.
        logger_name: Name passed to ``logging.getLogger()``.
            Defaults to *task_name* when omitted.
        **extra: Arbitrary keyword arguments added to ``_base_extra``
            alongside ``task`` (e.g. ``worker="notification_worker"``).

    Example:
        ```python
        log = TaskLogContext(
            "slot_calculation",
            logger_name="codex.booking",
            worker="slot_worker",
            tenant_id=42,
        )
        log.debug("Starting slot search")
        log.error("Slot not found", extra={"slot_id": 7})
        ```
    """

    def __init__(self, task_name: str, logger_name: str | None = None, **extra: Any) -> None:
        self._logger = logging.getLogger(logger_name or task_name)
        self._base_extra = {"task": task_name, **extra}

    def _merge_extra(self, extra: dict[str, Any] | None) -> dict[str, Any]:
        """Merge per-call extra fields with the base context.

        Args:
            extra: Optional per-call fields.  Keys in *extra* take
                precedence over identically named keys in
                ``_base_extra``.

        Returns:
            A new ``dict`` containing the merged fields.
        """
        if extra:
            return {**self._base_extra, **extra}
        return self._base_extra

    def debug(self, msg: str, *args: Any, extra: dict[str, Any] | None = None, **kwargs: Any) -> None:
        """Emit a ``DEBUG`` record enriched with the bound context fields.

        Args:
            msg: Log message format string.
            *args: Positional arguments passed to ``Logger.debug``.
            extra: Per-call structured fields merged with ``_base_extra``.
            **kwargs: Additional keyword arguments forwarded to ``Logger.debug``.
        """
        self._logger.debug(msg, *args, extra=self._merge_extra(extra), **kwargs)

    def info(self, msg: str, *args: Any, extra: dict[str, Any] | None = None, **kwargs: Any) -> None:
        """Emit an ``INFO`` record enriched with the bound context fields.

        Args:
            msg: Log message format string.
            *args: Positional arguments passed to ``Logger.info``.
            extra: Per-call structured fields merged with ``_base_extra``.
            **kwargs: Additional keyword arguments forwarded to ``Logger.info``.
        """
        self._logger.info(msg, *args, extra=self._merge_extra(extra), **kwargs)

    def warning(self, msg: str, *args: Any, extra: dict[str, Any] | None = None, **kwargs: Any) -> None:
        """Emit a ``WARNING`` record enriched with the bound context fields.

        Args:
            msg: Log message format string.
            *args: Positional arguments passed to ``Logger.warning``.
            extra: Per-call structured fields merged with ``_base_extra``.
            **kwargs: Additional keyword arguments forwarded to ``Logger.warning``.
        """
        self._logger.warning(msg, *args, extra=self._merge_extra(extra), **kwargs)

    def error(self, msg: str, *args: Any, extra: dict[str, Any] | None = None, **kwargs: Any) -> None:
        """Emit an ``ERROR`` record enriched with the bound context fields.

        Args:
            msg: Log message format string.
            *args: Positional arguments passed to ``Logger.error``.
            extra: Per-call structured fields merged with ``_base_extra``.
            **kwargs: Additional keyword arguments forwarded to ``Logger.error``.
        """
        self._logger.error(msg, *args, extra=self._merge_extra(extra), **kwargs)

    def exception(self, msg: str, *args: Any, extra: dict[str, Any] | None = None, **kwargs: Any) -> None:
        """Emit an ``ERROR`` record with exception traceback and bound context.

        Equivalent to :meth:`error` but always captures the current
        exception info (``exc_info=True`` is implicit).  Call inside an
        ``except`` block.

        Args:
            msg: Log message format string.
            *args: Positional arguments passed to ``Logger.exception``.
            extra: Per-call structured fields merged with ``_base_extra``.
            **kwargs: Additional keyword arguments forwarded to ``Logger.exception``.
        """
        self._logger.exception(msg, *args, extra=self._merge_extra(extra), **kwargs)
