import pytest


def pytest_collection_modifyitems(items):
    """Automatically add 'integration' marker to all tests in tests/integration/"""
    for item in items:
        item.add_marker(pytest.mark.integration)
