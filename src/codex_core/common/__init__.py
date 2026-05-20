"""Common utilities: logging, caching, phone normalization, text processing."""

from .log_context import TaskLogContext, clear_log_context, get_log_context, set_log_context
from .loguru_setup import (
    InterceptHandler,
    LoggingSettingsProtocol,
    setup_logging,
    setup_universal_logging,
)
from .phone import normalize_phone
from .text import clean_string, normalize_name, sanitize_for_sms, transliterate

__all__ = [
    "TaskLogContext",
    "clear_log_context",
    "get_log_context",
    "set_log_context",
    "InterceptHandler",
    "LoggingSettingsProtocol",
    "setup_logging",
    "setup_universal_logging",
    "normalize_phone",
    "clean_string",
    "normalize_name",
    "sanitize_for_sms",
    "transliterate",
]
