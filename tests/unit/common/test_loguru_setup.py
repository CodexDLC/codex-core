import logging
from unittest.mock import MagicMock, patch

import pytest

# We mock loguru in the tests because loguru is an optional dependency
# and might not be installed in all test environments.
from codex_core.common.loguru_setup import InterceptHandler, setup_logging, setup_universal_logging

pytestmark = pytest.mark.unit


def test_intercept_handler_without_loguru():
    """Test InterceptHandler falls back silently if loguru is not installed."""
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
    # Patch the logger variable inside loguru_setup module to None
    with patch("codex_core.common.loguru_setup.logger", None):
        # Should not raise an error, just return silently
        handler.emit(record)


@patch("codex_core.common.loguru_setup.logger")
def test_intercept_handler_with_loguru(mock_logger):
    """Test InterceptHandler correctly forwards to loguru."""
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

    # Setup mock
    mock_opt = MagicMock()
    mock_logger.opt.return_value = mock_opt
    mock_logger.level.return_value.name = "INFO"

    handler.emit(record)

    mock_logger.opt.assert_called_once()
    mock_opt.log.assert_called_once_with("INFO", "test message")


def test_setup_universal_logging_without_loguru(tmp_path):
    """Test setup_universal_logging raises ImportError if loguru is missing."""
    with (
        patch("codex_core.common.loguru_setup.logger", None),
        pytest.raises(ImportError, match="loguru is not installed"),
    ):
        setup_universal_logging(log_dir=tmp_path)


@patch("codex_core.common.loguru_setup.logger")
@patch("logging.basicConfig")
def test_setup_universal_logging_with_loguru(mock_basic_config, mock_logger, tmp_path):
    """Test setup_universal_logging configuration logic."""
    setup_universal_logging(
        log_dir=tmp_path,
        service_name="test_service",
        console_level="DEBUG",
        file_level="INFO",
        rotation="5 MB",
        is_debug=True,
    )

    # Check logger was reset
    mock_logger.remove.assert_called_once()

    # Check 3 sinks were added: console, debug file, errors file
    assert mock_logger.add.call_count == 3

    # Check directory was created
    assert tmp_path.exists()

    # Check basic config was called to intercept stdlib logging
    mock_basic_config.assert_called_once()


class DummySettings:
    """Mock settings object that satisfies LoggingSettingsProtocol."""

    def __init__(self, log_dir):
        self.log_level_console = "INFO"
        self.log_level_file = "DEBUG"
        self.log_rotation = "1 MB"
        self.log_dir = str(log_dir)
        self.debug = True


def test_setup_logging_without_loguru(tmp_path):
    """Test setup_logging raises ImportError if loguru is missing."""
    settings = DummySettings(tmp_path)
    with (
        patch("codex_core.common.loguru_setup.logger", None),
        pytest.raises(ImportError, match="loguru is not installed"),
    ):
        setup_logging(settings, service_name="test")


@patch("codex_core.common.loguru_setup.logger")
@patch("logging.basicConfig")
@patch("logging.getLogger")
def test_setup_logging_with_loguru(mock_get_logger, mock_basic_config, mock_logger, tmp_path):
    """Test setup_logging configuration logic."""
    settings = DummySettings(tmp_path)

    mock_sub_logger = MagicMock()
    mock_get_logger.return_value = mock_sub_logger

    setup_logging(
        settings=settings,
        service_name="test_service",
        intercept_loggers=["my_library"],
        log_levels={"noisy_lib": logging.WARNING},
    )

    mock_logger.remove.assert_called_once()
    assert mock_logger.add.call_count == 3

    expected_dir = tmp_path / "test_service"
    assert expected_dir.exists()

    mock_basic_config.assert_called_once()

    # Check that intercept_loggers and log_levels were processed
    # Two calls to getLogger: one for intercept, one for log levels
    assert mock_get_logger.call_count == 2
    mock_sub_logger.setLevel.assert_called_once_with(logging.WARNING)
