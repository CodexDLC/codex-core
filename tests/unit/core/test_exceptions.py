import pytest

from codex_core.core.exceptions import CodexToolsError

pytestmark = pytest.mark.unit


def test_codex_tools_error():
    """Test that the base exception can be instantiated and caught."""
    error = CodexToolsError("Something went wrong")

    assert isinstance(error, Exception)
    assert str(error) == "Something went wrong"

    with pytest.raises(CodexToolsError):
        raise error
