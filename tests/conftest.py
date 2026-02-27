"""
Shared pytest configuration and fixtures for test isolation.
"""

import pytest
from unittest.mock import AsyncMock


@pytest.fixture
def mock_server():
    """Provide a mock CyberArkMCPServer for testing tools."""
    server = AsyncMock()
    server.list_accounts.return_value = []
    server.list_safes.return_value = []
    server.list_platforms.return_value = []
    return server
