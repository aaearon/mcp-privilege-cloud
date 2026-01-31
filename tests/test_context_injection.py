"""
Context Injection Tests (RED then GREEN Phase)

Tests for accessing server via Context in MCP tools instead of global state.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import os


class TestContextAccess:
    """Test accessing server through context in tools"""

    @pytest.mark.asyncio
    async def test_tool_accesses_server_via_context(self):
        """Tool should get server from context, not global"""
        from mcp_privilege_cloud.mcp_server import get_account_details, AppContext

        # Create mock server with expected method
        mock_server = AsyncMock()
        mock_server.get_account_details.return_value = {
            "id": "123",
            "platformId": "WinServerLocal",
            "safeName": "TestSafe"
        }

        # Create mock context with lifespan_context
        mock_ctx = Mock()
        mock_ctx.request_context.lifespan_context = AppContext(server=mock_server)

        # Call tool with context
        result = await get_account_details("123", ctx=mock_ctx)

        assert result["id"] == "123"
        mock_server.get_account_details.assert_called_once_with(account_id="123")

    @pytest.mark.asyncio
    async def test_tool_works_without_context_backwards_compatible(self):
        """Tool should fall back to global server when context not provided"""
        from mcp_privilege_cloud.mcp_server import get_account_details

        mock_server = AsyncMock()
        mock_server.get_account_details.return_value = {
            "id": "123",
            "platformId": "WinServerLocal",
            "safeName": "TestSafe"
        }

        # Use legacy pattern without context
        with patch('mcp_privilege_cloud.mcp_server.get_server', return_value=mock_server):
            result = await get_account_details("123")

            assert result["id"] == "123"
            mock_server.get_account_details.assert_called_once()


class TestContextInjectionForHighUsageTools:
    """Test context injection for high-usage tools"""

    @pytest.mark.asyncio
    async def test_list_accounts_with_context(self):
        """list_accounts should work with context injection"""
        from mcp_privilege_cloud.mcp_server import list_accounts, AppContext

        mock_accounts = [
            {"id": "1", "platformId": "Win", "safeName": "Safe1"},
            {"id": "2", "platformId": "Unix", "safeName": "Safe2"}
        ]

        mock_server = AsyncMock()
        mock_server.list_accounts.return_value = mock_accounts

        mock_ctx = Mock()
        mock_ctx.request_context.lifespan_context = AppContext(server=mock_server)

        result = await list_accounts(ctx=mock_ctx)

        assert len(result) == 2
        mock_server.list_accounts.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_safe_details_with_context(self):
        """get_safe_details should work with context injection"""
        from mcp_privilege_cloud.mcp_server import get_safe_details, AppContext

        mock_safe = {
            "safeUrlId": "TestSafe",
            "safeName": "TestSafe",
            "safeNumber": 123
        }

        mock_server = AsyncMock()
        mock_server.get_safe_details.return_value = mock_safe

        mock_ctx = Mock()
        mock_ctx.request_context.lifespan_context = AppContext(server=mock_server)

        result = await get_safe_details("TestSafe", ctx=mock_ctx)

        assert result["safeName"] == "TestSafe"
        mock_server.get_safe_details.assert_called_once_with(safe_name="TestSafe")

    @pytest.mark.asyncio
    async def test_list_platforms_with_context(self):
        """list_platforms should work with context injection"""
        from mcp_privilege_cloud.mcp_server import list_platforms, AppContext

        mock_platforms = [
            {"id": "Win", "name": "Windows", "active": True}
        ]

        mock_server = AsyncMock()
        mock_server.list_platforms.return_value = mock_platforms

        mock_ctx = Mock()
        mock_ctx.request_context.lifespan_context = AppContext(server=mock_server)

        result = await list_platforms(ctx=mock_ctx)

        assert len(result) == 1
        mock_server.list_platforms.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_account_with_context(self):
        """create_account should work with context injection"""
        from mcp_privilege_cloud.mcp_server import create_account, AppContext

        mock_response = {
            "id": "new_123",
            "platformId": "WinServerLocal",
            "safeName": "IT-Safe"
        }

        mock_server = AsyncMock()
        mock_server.create_account.return_value = mock_response

        mock_ctx = Mock()
        mock_ctx.request_context.lifespan_context = AppContext(server=mock_server)

        result = await create_account(
            platform_id="WinServerLocal",
            safe_name="IT-Safe",
            ctx=mock_ctx
        )

        assert result["id"] == "new_123"
        mock_server.create_account.assert_called_once()


class TestContextTypeAnnotations:
    """Test that context type annotations are correct"""

    def test_context_type_is_available(self):
        """Context type should be importable from mcp.server.fastmcp"""
        from mcp.server.fastmcp import Context
        assert Context is not None

    def test_server_session_type_is_available(self):
        """ServerSession type should be importable"""
        from mcp.server.session import ServerSession
        assert ServerSession is not None

    def test_app_context_type_is_available(self):
        """AppContext should be importable from mcp_server"""
        from mcp_privilege_cloud.mcp_server import AppContext
        assert AppContext is not None


class TestContextWithErrors:
    """Test error handling with context injection"""

    @pytest.mark.asyncio
    async def test_tool_propagates_errors_with_context(self):
        """Errors from server methods should propagate through context-based tools"""
        from mcp_privilege_cloud.mcp_server import get_account_details, AppContext

        mock_server = AsyncMock()
        mock_server.get_account_details.side_effect = ValueError("Account not found")

        mock_ctx = Mock()
        mock_ctx.request_context.lifespan_context = AppContext(server=mock_server)

        with pytest.raises(ValueError, match="Account not found"):
            await get_account_details("invalid_id", ctx=mock_ctx)

    @pytest.mark.asyncio
    async def test_tool_handles_none_context_gracefully(self):
        """Tools should handle None context by falling back to get_server()"""
        from mcp_privilege_cloud.mcp_server import list_accounts

        mock_server = AsyncMock()
        mock_server.list_accounts.return_value = []

        with patch('mcp_privilege_cloud.mcp_server.get_server', return_value=mock_server):
            # Explicitly pass None for ctx
            result = await list_accounts(ctx=None)

            assert result == []
            mock_server.list_accounts.assert_called_once()
