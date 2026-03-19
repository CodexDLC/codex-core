"""Shared test fixtures."""

import pytest

from codex_core.core.pii import PIIRegistry


@pytest.fixture(autouse=True)
def reset_pii_registry():
    """Autouse fixture to ensure PIIRegistry global state is reset between tests.

    This is required to maintain test isolation because PIIRegistry modifies
    a class-level frozenset during subclass creation.
    """
    # Store original state
    original_fields = PIIRegistry._registered_fields

    yield

    # Restore original state after test
    PIIRegistry._registered_fields = original_fields
