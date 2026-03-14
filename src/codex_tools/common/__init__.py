"""Common utilities: logging, caching, phone normalization, text processing."""

from .log_context import TaskLogContext
from .loguru_setup import (
    InterceptHandler,
    LoggingSettingsProtocol,
    mask_sensitive_data,
    masking_patcher,
    setup_logging,
    setup_universal_logging,
)
from .text import clean_string, normalize_name, sanitize_for_sms, transliterate

__all__ = [
    "TaskLogContext",
    "InterceptHandler",
    "LoggingSettingsProtocol",
    "mask_sensitive_data",
    "masking_patcher",
    "setup_logging",
    "setup_universal_logging",
    "clean_string",
    "normalize_name",
    "sanitize_for_sms",
    "transliterate",
]
