"""Common utilities: logging, caching, phone normalization, text processing."""

from .log_context import TaskLogContext
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
