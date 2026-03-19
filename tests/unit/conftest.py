import pytest


def pytest_collection_modifyitems(items):
    """Automatically add 'unit' marker to all tests in tests/unit/"""
    for item in items:
        item.add_marker(pytest.mark.unit)
