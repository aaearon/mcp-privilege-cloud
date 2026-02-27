"""
Shared pytest configuration and fixtures for test isolation.

Provides modern context/lifespan fixtures for testing MCP tools
via the execute_tool() code path with context injection.
"""

import pytest
import os
from unittest.mock import patch, Mock, AsyncMock


@pytest.fixture
def mock_env_vars():
    """Provide mock environment variables for testing."""
    return {
        'CYBERARK_CLIENT_ID': 'test-client-id',
        'CYBERARK_CLIENT_SECRET': 'test-client-secret'
    }


@pytest.fixture
def mock_server():
    """Provide a mock CyberArkMCPServer for testing tools."""
    server = AsyncMock()
    # Configure common method returns
    server.list_accounts.return_value = []
    server.list_safes.return_value = []
    server.list_platforms.return_value = []
    return server


@pytest.fixture
def mock_context(mock_server):
    """Provide a mock MCP context with lifespan_context for testing tools.

    Usage in tests:
        async def test_tool(mock_context):
            result = await some_tool(param, ctx=mock_context)
    """
    from mcp_privilege_cloud.mcp_server import AppContext

    ctx = Mock()
    ctx.request_context.lifespan_context = AppContext(server=mock_server)
    return ctx


@pytest.fixture
def mock_context_with_server(mock_server):
    """Provide mock context with configurable server.

    Returns a tuple of (context, server) so tests can configure the server.

    Usage in tests:
        async def test_tool(mock_context_with_server):
            ctx, server = mock_context_with_server
            server.get_account_details.return_value = {...}
            result = await get_account_details("123", ctx=ctx)
    """
    from mcp_privilege_cloud.mcp_server import AppContext

    ctx = Mock()
    ctx.request_context.lifespan_context = AppContext(server=mock_server)
    return ctx, mock_server


@pytest.fixture
def mock_oauth_context(mock_server):
    """Provide a mock MCP context for OAuth-mode testing.

    Simulates the service account bridge where is_oauth=True
    and user identity is verified before tool execution.

    Usage in tests:
        async def test_tool(mock_oauth_context):
            ctx, server = mock_oauth_context
            server.list_accounts.return_value = [...]
            result = await some_tool(param, ctx=ctx)
    """
    from mcp_privilege_cloud.mcp_server import AppContext

    ctx = Mock()
    ctx.request_context.lifespan_context = AppContext(
        server=mock_server, is_oauth=True
    )
    return ctx, mock_server
