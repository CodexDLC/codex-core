"""Application-level Loguru configuration helpers (optional dependency).

Provides opinionated, zero-boilerplate Loguru setup for codex_tools
applications.  The codex_core *library* itself never calls these
helpers; it uses the standard ``logging`` module exclusively so that
consumers retain full control over their log infrastructure.

**Dev mode** (``debug=True``): three sinks — colourised stdout, rotating
plain-text ``debug.log``, and JSON ``errors.json``.

**Prod mode** (``debug=False``): a single JSON-serialised stdout sink
designed for ingestion by Grafana Alloy / Loki / ELK.  File sinks are
omitted because container runtimes capture stdout natively.

Both modes inject a **patcher** that enriches every log record with:

- ``service`` — the service name passed to the setup function.
- Any fields set via :func:`~codex_core.common.log_context.set_log_context`
  (request_id, char_id, correlation_id, etc.).

A built-in **healthcheck filter** suppresses records whose ``extra``
contains ``healthcheck=True``, preventing ``/health`` endpoint noise
from reaching log aggregators.

Standard-library ``logging`` records are bridged via
:class:`InterceptHandler` so that third-party libraries (SQLAlchemy,
httpx, aiogram, etc.) are automatically captured by Loguru.

Availability:
    ``loguru`` is an **optional** dependency.  Both :func:`setup_logging`
    and :func:`setup_universal_logging` raise :exc:`ImportError` with an
    actionable message when ``loguru`` is not installed.
"""

import logging
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from .log_context import get_log_context

if TYPE_CHECKING:
    from types import FrameType

    from loguru import Logger, Record

logger: "Logger | None"
try:
    from loguru import logger as _loguru_logger
except ImportError:
    logger = None
else:
    logger = _loguru_logger


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_context_patcher(service_name: str) -> Any:
    """Return a Loguru patcher that injects service name and contextvars."""

    def _patcher(record: dict[str, Any]) -> None:
        record["extra"]["service"] = service_name
        record["extra"].update(get_log_context())

    return _patcher


def _healthcheck_filter(record: "Record") -> bool:
    """Suppress log records tagged with ``healthcheck=True``."""
    return not record["extra"].get("healthcheck", False)


# ---------------------------------------------------------------------------
# InterceptHandler
# ---------------------------------------------------------------------------


class InterceptHandler(logging.Handler):
    """Bridge standard-library ``logging`` records to the Loguru sink.

    Install this handler on the root logger (or any named logger) to
    forward all ``logging``-based records into Loguru transparently.
    The handler resolves the correct call-stack depth so that Loguru
    reports the *original* call site rather than the handler frame.

    This class is stateless and thread-safe; a single instance may be
    shared across all intercepted loggers.

    Example:
        ```python
        import logging
        from codex_core.common.loguru_setup import InterceptHandler

        logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
        ```
    """

    def emit(self, record: logging.LogRecord) -> None:
        if logger is None:
            return

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


# ---------------------------------------------------------------------------
# setup_universal_logging (raw-args variant)
# ---------------------------------------------------------------------------

_CONSOLE_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<magenta>{extra[service]}</magenta> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)

_FILE_FORMAT = "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"


def setup_universal_logging(
    log_dir: Path,
    service_name: str = "App",
    console_level: str = "INFO",
    file_level: str = "DEBUG",
    rotation: str = "10 MB",
    is_debug: bool = False,
) -> None:
    """Configure Loguru with three sinks and standard-library interception.

    Intended for applications that do not use
    :class:`~codex_core.settings.BaseCommonSettings` but still want the
    full codex_core logging stack.  Callers supply raw configuration
    values directly rather than a settings object.

    Args:
        log_dir: Directory where log files are created.
        service_name: Label embedded in the console format string.
        console_level: Minimum level for stdout output.
        file_level: Minimum level for the debug log file.
        rotation: Loguru rotation threshold string.
        is_debug: When ``True``, enables ``backtrace`` and ``diagnose``.

    Raises:
        ImportError: If ``loguru`` is not installed.
    """
    if logger is None:
        raise ImportError("loguru is not installed. Please install it manually: pip install loguru")

    logger.remove()
    log_dir.mkdir(parents=True, exist_ok=True)

    logger.configure(patcher=_make_context_patcher(service_name))

    logger.add(
        sink=sys.stdout,
        level=console_level,
        colorize=True,
        filter=_healthcheck_filter,
        format=_CONSOLE_FORMAT,
    )

    logger.add(
        sink=str(log_dir / "debug.log"),
        level=file_level,
        rotation=rotation,
        compression="zip",
        format=_FILE_FORMAT,
        enqueue=True,
        backtrace=is_debug,
        diagnose=is_debug,
    )

    logger.add(
        sink=str(log_dir / "errors.json"),
        level="ERROR",
        serialize=True,
        rotation=rotation,
        compression="zip",
        enqueue=True,
    )

    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    logger.info("LoguruSetupComplete log_dir={}", log_dir)


# ---------------------------------------------------------------------------
# LoggingSettingsProtocol
# ---------------------------------------------------------------------------


@runtime_checkable
class LoggingSettingsProtocol(Protocol):
    """Structural protocol for the logging-related subset of settings."""

    log_level_console: str
    log_level_file: str
    log_rotation: str
    log_dir: str
    debug: bool


# ---------------------------------------------------------------------------
# setup_logging (settings-based variant)
# ---------------------------------------------------------------------------


def setup_logging(
    settings: LoggingSettingsProtocol,
    service_name: str,
    intercept_loggers: list[str] | None = None,
    log_levels: dict[str, int] | None = None,
) -> None:
    """Configure Loguru from a settings object.

    **Dev** (``settings.debug is True``): colourised console + file sinks.
    **Prod** (``settings.debug is False``): JSON-serialised stdout only.

    Both modes apply a patcher (service name + contextvars) and a
    healthcheck filter.

    Args:
        settings: Object satisfying :class:`LoggingSettingsProtocol`.
        service_name: Identifies the service in log output.
        intercept_loggers: Logger names whose handlers are replaced
            with :class:`InterceptHandler`.
        log_levels: ``{logger_name: level_int}`` for silencing noisy
            libraries.

    Raises:
        ImportError: If ``loguru`` is not installed.
    """
    if logger is None:
        raise ImportError("loguru is not installed. Please install it manually: pip install loguru")

    logger.remove()

    logger.configure(patcher=_make_context_patcher(service_name))

    if settings.debug:
        # ── Dev: colourised console + file sinks ──
        log_dir = Path(settings.log_dir) / service_name
        log_dir.mkdir(parents=True, exist_ok=True)

        logger.add(
            sink=sys.stdout,
            level=settings.log_level_console,
            colorize=True,
            filter=_healthcheck_filter,
            format=_CONSOLE_FORMAT,
        )

        logger.add(
            sink=str(log_dir / "debug.log"),
            level=settings.log_level_file,
            rotation=settings.log_rotation,
            compression="zip",
            format=_FILE_FORMAT,
            enqueue=True,
            backtrace=True,
            diagnose=True,
        )

        logger.add(
            sink=str(log_dir / "errors.json"),
            level="ERROR",
            serialize=True,
            rotation=settings.log_rotation,
            compression="zip",
            enqueue=True,
        )
    else:
        # ── Prod: JSON stdout only (Alloy / Loki / ELK ingestion) ──
        logger.add(
            sink=sys.stdout,
            level=settings.log_level_console,
            serialize=True,
            colorize=False,
            filter=_healthcheck_filter,
            enqueue=True,
        )

    # Intercept standard logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    if intercept_loggers:
        for name in intercept_loggers:
            logging.getLogger(name).handlers = [InterceptHandler()]

    if log_levels:
        for name, level in log_levels.items():
            logging.getLogger(name).setLevel(level)
