from unittest.mock import MagicMock, patch

import pytest

from codex_core.common.log_context import TaskLogContext

pytestmark = pytest.mark.unit


def test_task_log_context_initialization():
    """Test that context is initialized with base extra and logger name."""
    ctx = TaskLogContext("my_task", worker="worker_1")
    assert ctx._base_extra == {"task": "my_task", "worker": "worker_1"}
    assert ctx._logger.name == "my_task"

    ctx_with_custom_logger = TaskLogContext("my_task", logger_name="custom.logger", worker="worker_2")
    assert ctx_with_custom_logger._base_extra == {"task": "my_task", "worker": "worker_2"}
    assert ctx_with_custom_logger._logger.name == "custom.logger"


@patch("logging.getLogger")
def test_task_log_context_methods(mock_get_logger):
    """Test that all logging methods forward calls properly."""
    mock_logger = MagicMock()
    mock_get_logger.return_value = mock_logger

    ctx = TaskLogContext("test_task", worker="test_worker")

    # Test debug
    ctx.debug("debug message", extra={"key": "val"})
    mock_logger.debug.assert_called_once_with(
        "debug message", extra={"task": "test_task", "worker": "test_worker", "key": "val"}
    )

    # Test info
    ctx.info("info message")
    mock_logger.info.assert_called_once_with("info message", extra={"task": "test_task", "worker": "test_worker"})

    # Test warning
    ctx.warning("warning message")
    mock_logger.warning.assert_called_once_with("warning message", extra={"task": "test_task", "worker": "test_worker"})

    # Test error
    ctx.error("error message", exc_info=True)
    mock_logger.error.assert_called_once_with(
        "error message", extra={"task": "test_task", "worker": "test_worker"}, exc_info=True
    )

    # Test exception
    ctx.exception("exception message")
    mock_logger.exception.assert_called_once_with(
        "exception message", extra={"task": "test_task", "worker": "test_worker"}
    )
