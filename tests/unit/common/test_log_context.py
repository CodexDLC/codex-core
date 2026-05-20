from unittest.mock import MagicMock, patch

import pytest

from codex_core.common.log_context import (
    TaskLogContext,
    clear_log_context,
    get_log_context,
    set_log_context,
)

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# contextvars functions
# ---------------------------------------------------------------------------


class TestContextVars:
    def setup_method(self):
        clear_log_context()

    def teardown_method(self):
        clear_log_context()

    def test_empty_by_default(self):
        assert get_log_context() == {}

    def test_set_and_get(self):
        set_log_context(request_id="abc-123", char_id=42)
        ctx = get_log_context()
        assert ctx == {"request_id": "abc-123", "char_id": 42}

    def test_set_merges_incrementally(self):
        set_log_context(request_id="abc")
        set_log_context(char_id=42)
        assert get_log_context() == {"request_id": "abc", "char_id": 42}

    def test_set_overwrites_existing_key(self):
        set_log_context(request_id="old")
        set_log_context(request_id="new")
        assert get_log_context() == {"request_id": "new"}

    def test_clear_resets_to_empty(self):
        set_log_context(request_id="abc", char_id=42)
        clear_log_context()
        assert get_log_context() == {}

    def test_get_returns_copy(self):
        set_log_context(request_id="abc")
        ctx = get_log_context()
        ctx["injected"] = True
        assert "injected" not in get_log_context()


# ---------------------------------------------------------------------------
# TaskLogContext (existing tests preserved)
# ---------------------------------------------------------------------------


def test_task_log_context_initialization():
    ctx = TaskLogContext("my_task", worker="worker_1")
    assert ctx._base_extra == {"task": "my_task", "worker": "worker_1"}
    assert ctx._logger.name == "my_task"

    ctx_with_custom_logger = TaskLogContext("my_task", logger_name="custom.logger", worker="worker_2")
    assert ctx_with_custom_logger._base_extra == {"task": "my_task", "worker": "worker_2"}
    assert ctx_with_custom_logger._logger.name == "custom.logger"


@patch("logging.getLogger")
def test_task_log_context_methods(mock_get_logger):
    mock_logger = MagicMock()
    mock_get_logger.return_value = mock_logger

    ctx = TaskLogContext("test_task", worker="test_worker")

    ctx.debug("debug message", extra={"key": "val"})
    mock_logger.debug.assert_called_once_with(
        "debug message", extra={"task": "test_task", "worker": "test_worker", "key": "val"}
    )

    ctx.info("info message")
    mock_logger.info.assert_called_once_with("info message", extra={"task": "test_task", "worker": "test_worker"})

    ctx.warning("warning message")
    mock_logger.warning.assert_called_once_with("warning message", extra={"task": "test_task", "worker": "test_worker"})

    ctx.error("error message", exc_info=True)
    mock_logger.error.assert_called_once_with(
        "error message", extra={"task": "test_task", "worker": "test_worker"}, exc_info=True
    )

    ctx.exception("exception message")
    mock_logger.exception.assert_called_once_with(
        "exception message", extra={"task": "test_task", "worker": "test_worker"}
    )
