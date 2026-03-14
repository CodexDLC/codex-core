"""
codex_tools.common.log_context
================================
Structured logging context for worker tasks.

Provides TaskLogContext — a logging adapter that automatically adds
structured fields (task name, worker name, custom extras) to all log records.

Usage:
    log = TaskLogContext("send_booking_notification", worker="notification_worker")
    log.info("Processing appointment", extra={"appointment_id": 123})
    # → "Processing appointment" with extra fields: task=send_booking_notification,
    #   worker=notification_worker, appointment_id=123
"""

import logging
from typing import Any


class TaskLogContext:
    """
    Logging adapter that adds structured context fields to all log records.

    All extra fields are attached to the LogRecord and can be picked up
    by log formatters (JSON formatter, loguru, ELK, etc.).

    Args:
        task_name: Name of the current task/operation.
        logger_name: Name for the underlying logger (defaults to task_name).
        **extra: Additional structured fields to include in every log record.
    """

    def __init__(self, task_name: str, logger_name: str | None = None, **extra: Any) -> None:
        self._logger = logging.getLogger(logger_name or task_name)
        self._base_extra = {"task": task_name, **extra}

    def _merge_extra(self, extra: dict[str, Any] | None) -> dict[str, Any]:
        if extra:
            return {**self._base_extra, **extra}
        return self._base_extra

    def debug(self, msg: str, *args: Any, extra: dict[str, Any] | None = None, **kwargs: Any) -> None:
        self._logger.debug(msg, *args, extra=self._merge_extra(extra), **kwargs)

    def info(self, msg: str, *args: Any, extra: dict[str, Any] | None = None, **kwargs: Any) -> None:
        self._logger.info(msg, *args, extra=self._merge_extra(extra), **kwargs)

    def warning(self, msg: str, *args: Any, extra: dict[str, Any] | None = None, **kwargs: Any) -> None:
        self._logger.warning(msg, *args, extra=self._merge_extra(extra), **kwargs)

    def error(self, msg: str, *args: Any, extra: dict[str, Any] | None = None, **kwargs: Any) -> None:
        self._logger.error(msg, *args, extra=self._merge_extra(extra), **kwargs)

    def exception(self, msg: str, *args: Any, extra: dict[str, Any] | None = None, **kwargs: Any) -> None:
        self._logger.exception(msg, *args, extra=self._merge_extra(extra), **kwargs)
