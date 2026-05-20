import logging
from unittest.mock import MagicMock, patch

import pytest

from codex_core.common.loguru_setup import InterceptHandler, setup_logging, setup_universal_logging

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# InterceptHandler
# ---------------------------------------------------------------------------


def test_intercept_handler_without_loguru():
    handler = InterceptHandler()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="test message",
        args=(),
        exc_info=None,
    )
    with patch("codex_core.common.loguru_setup.logger", None):
        handler.emit(record)


@patch("codex_core.common.loguru_setup.logger")
def test_intercept_handler_with_loguru(mock_logger):
    handler = InterceptHandler()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="test message",
        args=(),
        exc_info=None,
    )
    mock_opt = MagicMock()
    mock_logger.opt.return_value = mock_opt
    mock_logger.level.return_value.name = "INFO"

    handler.emit(record)

    mock_logger.opt.assert_called_once()
    mock_opt.log.assert_called_once_with("INFO", "test message")


# ---------------------------------------------------------------------------
# setup_universal_logging
# ---------------------------------------------------------------------------


def test_setup_universal_logging_without_loguru(tmp_path):
    with (
        patch("codex_core.common.loguru_setup.logger", None),
        pytest.raises(ImportError, match="loguru is not installed"),
    ):
        setup_universal_logging(log_dir=tmp_path)


@patch("codex_core.common.loguru_setup.logger")
@patch("logging.basicConfig")
def test_setup_universal_logging_with_loguru(mock_basic_config, mock_logger, tmp_path):
    setup_universal_logging(
        log_dir=tmp_path,
        service_name="test_service",
        console_level="DEBUG",
        file_level="INFO",
        rotation="5 MB",
        is_debug=True,
    )

    mock_logger.remove.assert_called_once()
    mock_logger.configure.assert_called_once()
    assert mock_logger.add.call_count == 3
    assert tmp_path.exists()
    mock_basic_config.assert_called_once()


# ---------------------------------------------------------------------------
# setup_logging — dev mode (debug=True)
# ---------------------------------------------------------------------------


class DummySettings:
    def __init__(self, log_dir, debug=True):
        self.log_level_console = "INFO"
        self.log_level_file = "DEBUG"
        self.log_rotation = "1 MB"
        self.log_dir = str(log_dir)
        self.debug = debug


def test_setup_logging_without_loguru(tmp_path):
    settings = DummySettings(tmp_path)
    with (
        patch("codex_core.common.loguru_setup.logger", None),
        pytest.raises(ImportError, match="loguru is not installed"),
    ):
        setup_logging(settings, service_name="test")


@patch("codex_core.common.loguru_setup.logger")
@patch("logging.basicConfig")
@patch("logging.getLogger")
def test_setup_logging_dev_mode(mock_get_logger, mock_basic_config, mock_logger, tmp_path):
    """Dev mode (debug=True) creates 3 sinks: console + debug file + errors file."""
    settings = DummySettings(tmp_path, debug=True)
    mock_sub_logger = MagicMock()
    mock_get_logger.return_value = mock_sub_logger

    setup_logging(
        settings=settings,
        service_name="test_service",
        intercept_loggers=["my_library"],
        log_levels={"noisy_lib": logging.WARNING},
    )

    mock_logger.remove.assert_called_once()
    mock_logger.configure.assert_called_once()
    assert mock_logger.add.call_count == 3

    expected_dir = tmp_path / "test_service"
    assert expected_dir.exists()

    mock_basic_config.assert_called_once()
    assert mock_get_logger.call_count == 2
    mock_sub_logger.setLevel.assert_called_once_with(logging.WARNING)


# ---------------------------------------------------------------------------
# setup_logging — prod mode (debug=False)
# ---------------------------------------------------------------------------


@patch("codex_core.common.loguru_setup.logger")
@patch("logging.basicConfig")
def test_setup_logging_prod_mode(mock_basic_config, mock_logger, tmp_path):
    """Prod mode (debug=False) creates only 1 sink: JSON stdout."""
    settings = DummySettings(tmp_path, debug=False)

    setup_logging(settings=settings, service_name="api")

    mock_logger.remove.assert_called_once()
    mock_logger.configure.assert_called_once()

    # Only 1 sink in prod (JSON stdout)
    assert mock_logger.add.call_count == 1

    add_call = mock_logger.add.call_args
    assert add_call.kwargs.get("serialize") is True
    assert add_call.kwargs.get("colorize") is False

    mock_basic_config.assert_called_once()


# ---------------------------------------------------------------------------
# Patcher
# ---------------------------------------------------------------------------


@patch("codex_core.common.loguru_setup.logger")
@patch("logging.basicConfig")
def test_patcher_injects_service_name(mock_basic_config, mock_logger, tmp_path):
    """The patcher passed to logger.configure() injects 'service' into extra."""
    settings = DummySettings(tmp_path)

    setup_logging(settings=settings, service_name="backend")

    patcher = mock_logger.configure.call_args.kwargs.get("patcher")
    assert patcher is not None

    record = {"extra": {}}
    patcher(record)
    assert record["extra"]["service"] == "backend"


@patch("codex_core.common.loguru_setup.logger")
@patch("logging.basicConfig")
def test_patcher_merges_log_context(mock_basic_config, mock_logger, tmp_path):
    """The patcher merges contextvars from set_log_context."""
    from codex_core.common.log_context import clear_log_context, set_log_context

    settings = DummySettings(tmp_path)
    setup_logging(settings=settings, service_name="backend")

    patcher = mock_logger.configure.call_args.kwargs.get("patcher")

    set_log_context(request_id="req-42", char_id=7)
    try:
        record = {"extra": {}}
        patcher(record)
        assert record["extra"]["service"] == "backend"
        assert record["extra"]["request_id"] == "req-42"
        assert record["extra"]["char_id"] == 7
    finally:
        clear_log_context()


# ---------------------------------------------------------------------------
# Healthcheck filter
# ---------------------------------------------------------------------------


def test_healthcheck_filter_passes_normal_records():
    from codex_core.common.loguru_setup import _healthcheck_filter

    assert _healthcheck_filter({"extra": {}}) is True
    assert _healthcheck_filter({"extra": {"request_id": "abc"}}) is True


def test_healthcheck_filter_blocks_healthcheck_records():
    from codex_core.common.loguru_setup import _healthcheck_filter

    assert _healthcheck_filter({"extra": {"healthcheck": True}}) is False
    assert _healthcheck_filter({"extra": {"healthcheck": False}}) is True
