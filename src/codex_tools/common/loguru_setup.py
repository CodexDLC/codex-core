"""
codex_tools.common.loguru_setup
================================
OPTIONAL: Project-level Loguru configuration.

This is a helper to quickly set up Loguru for your *application*.
The codex_tools library itself uses the standard 'logging' module.
Requires: pip install codex-tools[loguru]
"""

import logging
import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from loguru import logger

if TYPE_CHECKING:
    from types import FrameType

    from loguru import Record


class InterceptHandler(logging.Handler):
    """
    Intercepts standard logging messages and redirects them to loguru.
    """

    def emit(self, record: logging.LogRecord) -> None:
        level: str | int
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame: FrameType | None = logging.currentframe()
        depth = 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def setup_universal_logging(
    log_dir: Path,
    service_name: str = "App",
    console_level: str = "INFO",
    file_level: str = "DEBUG",
    rotation: str = "10 MB",
    is_debug: bool = False,
) -> None:
    """
    Configures loguru with interception of standard logs.

    For settings-object based setup, use :func:`setup_logging` instead.
    """
    logger.remove()
    log_dir.mkdir(parents=True, exist_ok=True)

    # 1. Console output
    logger.add(
        sink=sys.stdout,
        level=console_level,
        colorize=True,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            f"<magenta>{service_name}</magenta> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
    )

    # 2. Debug file
    logger.add(
        sink=str(log_dir / "debug.log"),
        level=file_level,
        rotation=rotation,
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        enqueue=True,
        backtrace=is_debug,
        diagnose=is_debug,
    )

    # 3. Errors file (JSON)
    logger.add(
        sink=str(log_dir / "errors.json"),
        level="ERROR",
        serialize=True,
        rotation=rotation,
        compression="zip",
        enqueue=True,
    )

    # 4. Intercept standard logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    logger.info(f"Loguru setup complete for {service_name}. Logs: {log_dir}")


# ---------------------------------------------------------------------------
# PII masking
# ---------------------------------------------------------------------------

# Compiled pattern for sensitive key=value pairs.
_SENSITIVE_KV_RE = re.compile(
    r"(?i)(password|token|secret|api_key|authorization|cookie|session_id)"
    r"""([\s:=(\"']*)([\S]{4,})""",
)


def mask_sensitive_data(text: str) -> str:
    """Masks phones, emails, and sensitive key-value pairs in log text."""
    if not isinstance(text, str):
        return text
    # Phones: +49 176 12345678 → +49 176 *** 5678
    text = re.sub(r"(\+?\d{1,3}[\s-]?\d{3})[\s-]?\d{3,}[\s-]?(\d{2,4})", r"\1 *** \2", text)
    # Emails: user@example.com → u***@example.com
    text = re.sub(r"([a-zA-Z0-9_.+-])[a-zA-Z0-9_.+-]*@([a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)", r"\1***@\2", text)
    # Key-value: password=secret123 → password=***
    text = _SENSITIVE_KV_RE.sub(r"\1\2***", text)
    return text


def masking_patcher(record: "Record") -> None:
    """Loguru patcher — masks all log messages automatically."""
    record["message"] = mask_sensitive_data(record["message"])


# ---------------------------------------------------------------------------
# Settings-aware setup
# ---------------------------------------------------------------------------


@runtime_checkable
class LoggingSettingsProtocol(Protocol):
    """Duck-typing protocol for settings objects passed to setup_logging."""

    log_level_console: str
    log_level_file: str
    log_rotation: str
    log_dir: str
    debug: bool


def setup_logging(
    settings: LoggingSettingsProtocol,
    service_name: str,
    intercept_loggers: list[str] | None = None,
    log_levels: dict[str, int] | None = None,
) -> None:
    """
    Configure loguru from a settings object with PII masking.
    """
    # IMPORTANT: patcher is configured BEFORE logger.add()
    logger.remove()
    logger.configure(patcher=masking_patcher)

    log_dir = Path(settings.log_dir) / service_name
    log_dir.mkdir(parents=True, exist_ok=True)

    # Console
    logger.add(
        sink=sys.stdout,
        level=settings.log_level_console,
        colorize=True,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            f"<magenta>{service_name}</magenta> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
    )

    # Debug file
    logger.add(
        sink=str(log_dir / "debug.log"),
        level=settings.log_level_file,
        rotation=settings.log_rotation,
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        enqueue=True,
        backtrace=settings.debug,
        diagnose=settings.debug,
    )

    # Errors file (JSON)
    logger.add(
        sink=str(log_dir / "errors.json"),
        level="ERROR",
        serialize=True,
        rotation=settings.log_rotation,
        compression="zip",
        enqueue=True,
    )

    # Intercept standard logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # Intercept specified loggers
    if intercept_loggers:
        for name in intercept_loggers:
            logging.getLogger(name).handlers = [InterceptHandler()]

    # Set levels for noisy libraries
    if log_levels:
        for name, level in log_levels.items():
            logging.getLogger(name).setLevel(level)
