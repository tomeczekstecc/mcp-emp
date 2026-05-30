"""Root test configuration — shared fixtures and pytest plugins."""

import pytest


@pytest.fixture
def anyio_backend() -> str:
    """Use asyncio for all async tests."""
    return "asyncio"
