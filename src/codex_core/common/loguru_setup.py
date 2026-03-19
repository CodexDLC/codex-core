"""Application-level Loguru configuration helpers (optional dependency).

Provides opinionated, zero-boilerplate Loguru setup for codex_tools
applications.  The codex_core *library* itself never calls these
helpers; it uses the standard ``logging`` module exclusively so that
consumers retain full control over their log infrastructure.

Three configurable sinks are created by both setup functions:

1. **stdout** — colourised, human-readable format for local development.
2. **debug.log** — rotating plain-text file, ``enqueue=True`` for
   async-safe writing.
3. **errors.json** — rotating JSON-serialised file capturing ``ERROR``
   and above; suitable for ingestion by ELK / Loki pipelines.

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
from typing import TYPE_CHECKING, Protocol, runtime_checkable

try:
    from loguru import logger
except ImportError:
    logger = None


if TYPE_CHECKING:
    from types import FrameType


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
        """Forward a single ``logging.LogRecord`` to the active Loguru logger.

        Resolves the Loguru level name from the record's level name,
        falls back to the integer level when the name is unknown, then
        walks up the call stack to find the frame that originally issued
        the log call — ensuring Loguru displays the correct source
        location instead of the handler internals.

        Args:
            record: The log record produced by the standard-library
                logging infrastructure.

        Note:
            If ``loguru`` is not installed (``logger is None``), this
            method returns silently to avoid masking the original
            ``ImportError``.
        """
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

    Sink layout after the call:

    - **stdout** — colourised, ``console_level`` threshold.
    - **<log_dir>/debug.log** — rotating plain text, ``file_level``
      threshold, ``backtrace`` / ``diagnose`` enabled when
      ``is_debug=True``.
    - **<log_dir>/errors.json** — rotating JSON, ``ERROR`` threshold,
      async-enqueued.
    - **Root logger** — intercepted via :class:`InterceptHandler`.

    Args:
        log_dir: Directory where log files are created.  Created
            recursively if it does not exist.
        service_name: Label embedded in the console format string to
            distinguish output from multiple co-running services.
        console_level: Minimum level for stdout output (e.g. ``"INFO"``).
        file_level: Minimum level for the debug log file
            (e.g. ``"DEBUG"``).
        rotation: Loguru rotation threshold string (e.g. ``"10 MB"`` or
            ``"1 day"``).
        is_debug: When ``True``, enables full ``backtrace`` and
            ``diagnose`` output in the debug file sink.

    Raises:
        ImportError: If ``loguru`` is not installed in the environment.

    Example:
        ```python
        from pathlib import Path
        from codex_core.common.loguru_setup import setup_universal_logging

        setup_universal_logging(
            log_dir=Path("/var/log/myapp"),
            service_name="booking-worker",
            is_debug=True,
        )
        ```
    """
    if logger is None:
        raise ImportError("loguru is not installed. Please install it manually: pip install loguru")

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


@runtime_checkable
class LoggingSettingsProtocol(Protocol):
    """Structural protocol describing the logging-related subset of settings.

    Any settings object that exposes these five attributes satisfies this
    protocol and can be passed to :func:`setup_logging` without explicit
    inheritance.  :class:`~codex_core.settings.BaseCommonSettings`
    satisfies this protocol out of the box when its subclass adds the
    required logging fields.

    Attributes:
        log_level_console: Minimum Loguru level for stdout
            (e.g. ``"INFO"``).
        log_level_file: Minimum Loguru level for the rotating debug
            file (e.g. ``"DEBUG"``).
        log_rotation: Loguru rotation threshold
            (e.g. ``"10 MB"`` or ``"1 day"``).
        log_dir: Base directory for log files.  A service-name
            subdirectory is appended automatically by
            :func:`setup_logging`.
        debug: When ``True``, enables ``backtrace`` and ``diagnose``
            in the file sink.
    """

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
    """Configure Loguru from a settings object conforming to :class:`LoggingSettingsProtocol`.

    Preferred entry-point for applications that use
    :class:`~codex_core.settings.BaseCommonSettings`.  Configuration
    is read from *settings* rather than raw arguments, enabling
    environment-driven log levels without code changes.

    PII masking is **not** handled here; it is the responsibility of
    :class:`~codex_core.core.base_dto.BaseDTO.__repr__` at the DTO
    level.  Do not log raw user input through this logger.

    Side effects:
        - Removes all existing Loguru handlers (``logger.remove()``).
        - Creates ``<settings.log_dir>/<service_name>/`` directory tree.
        - Replaces the root ``logging`` handler with
          :class:`InterceptHandler`.
        - Optionally replaces handlers on loggers listed in
          *intercept_loggers*.
        - Optionally sets log levels on loggers listed in *log_levels*.

    Args:
        settings: Any object satisfying :class:`LoggingSettingsProtocol`.
            Typically a subclass of
            :class:`~codex_core.settings.BaseCommonSettings`.
        service_name: Identifies the service in log output and is used
            as the leaf directory name under ``settings.log_dir``.
        intercept_loggers: Optional list of logger names whose handlers
            should be replaced with :class:`InterceptHandler`
            (e.g. ``["aiogram", "sqlalchemy.engine"]``).
        log_levels: Optional mapping of ``{logger_name: level_int}``
            for silencing verbose third-party libraries
            (e.g. ``{"httpx": logging.WARNING}``).

    Raises:
        ImportError: If ``loguru`` is not installed in the environment.

    Example:
        ```python
        import logging
        from codex_core.common.loguru_setup import setup_logging

        setup_logging(
            settings=app_settings,
            service_name="api",
            intercept_loggers=["uvicorn", "sqlalchemy.engine"],
            log_levels={"httpx": logging.WARNING},
        )
        ```
    """
    if logger is None:
        raise ImportError("loguru is not installed. Please install it manually: pip install loguru")

    logger.remove()

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
