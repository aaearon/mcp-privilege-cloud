"""Tests for service account token bridge in OAuth mode.

Tests that in OAuth mode:
- app_lifespan creates a service account server with is_oauth=True
- execute_tool verifies user identity via access token, then uses the service account server
- Unauthenticated requests in OAuth mode are rejected
- Authenticated user identity is logged
"""

import os

import pytest
from unittest.mock import AsyncMock, MagicMock, Mock, patch


class TestOAuthLifespanServiceAccountBridge:
    """Test that OAuth lifespan creates a service account server with is_oauth=True."""

    @pytest.mark.asyncio
    async def test_oauth_lifespan_creates_service_account_server(self):
        """In OAuth mode, app_lifespan should create server with is_oauth=True."""
        from mcp_privilege_cloud.mcp_server import app_lifespan

        with patch.dict(os.environ, {
            "CYBERARK_IDENTITY_TENANT_URL": "https://abc1234.id.cyberark.cloud",
        }):
            with patch("mcp_privilege_cloud.mcp_server.is_oauth_mode", return_value=True):
                with patch(
                    "mcp_privilege_cloud.mcp_server.CyberArkMCPServer.from_environment"
                ) as mock_from_env:
                    mock_server = MagicMock()
                    mock_server._executor = MagicMock()
                    mock_from_env.return_value = mock_server

                    mock_fastmcp = MagicMock()
                    async with app_lifespan(mock_fastmcp) as app_ctx:
                        assert app_ctx.is_oauth is True
                        assert app_ctx.server is not None
                        assert app_ctx.server is mock_server

                    mock_from_env.assert_called_once()

    @pytest.mark.asyncio
    async def test_oauth_lifespan_shuts_down_executor(self):
        """On shutdown, OAuth lifespan should clean up executor."""
        from mcp_privilege_cloud.mcp_server import app_lifespan

        with patch.dict(os.environ, {
            "CYBERARK_IDENTITY_TENANT_URL": "https://abc1234.id.cyberark.cloud",
        }):
            with patch("mcp_privilege_cloud.mcp_server.is_oauth_mode", return_value=True):
                with patch(
                    "mcp_privilege_cloud.mcp_server.CyberArkMCPServer.from_environment"
                ) as mock_from_env:
                    mock_server = MagicMock()
                    mock_executor = MagicMock()
                    mock_server._executor = mock_executor
                    mock_from_env.return_value = mock_server

                    mock_fastmcp = MagicMock()
                    async with app_lifespan(mock_fastmcp) as app_ctx:
                        pass

                    mock_executor.shutdown.assert_called_once_with(wait=True)


class TestExecuteToolServiceAccountBridge:
    """Test execute_tool uses service account server after identity verification."""

    @pytest.mark.asyncio
    async def test_execute_tool_verifies_identity_uses_service_account(self):
        """execute_tool should verify identity via access_token, then use app_ctx.server."""
        from mcp_privilege_cloud.mcp_server import AppContext, execute_tool

        mock_server = AsyncMock()
        mock_server.list_accounts = AsyncMock(return_value=[])

        ctx = Mock()
        ctx.request_context.lifespan_context = AppContext(
            server=mock_server, is_oauth=True
        )

        mock_access_token = Mock()
        mock_access_token.token = "fake.jwt.token"
        mock_access_token.client_id = "testuser@cyberark.cloud.12345"

        with patch(
            "mcp_privilege_cloud.mcp_server.get_access_token",
            return_value=mock_access_token,
        ):
            result = await execute_tool("list_accounts", ctx=ctx)

        mock_server.list_accounts.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_tool_rejects_unauthenticated_in_oauth_mode(self):
        """When is_oauth=True but no access token, should raise PermissionError."""
        from mcp_privilege_cloud.mcp_server import AppContext, execute_tool

        mock_server = AsyncMock()

        ctx = Mock()
        ctx.request_context.lifespan_context = AppContext(
            server=mock_server, is_oauth=True
        )

        with patch(
            "mcp_privilege_cloud.mcp_server.get_access_token",
            return_value=None,
        ):
            with pytest.raises(PermissionError, match="OAuth mode requires authentication"):
                await execute_tool("list_accounts", ctx=ctx)

    @pytest.mark.asyncio
    async def test_execute_tool_logs_authenticated_user(self):
        """execute_tool should log the authenticated user's identity."""
        from mcp_privilege_cloud.mcp_server import AppContext, execute_tool

        mock_server = AsyncMock()
        mock_server.list_accounts = AsyncMock(return_value=[])

        ctx = Mock()
        ctx.request_context.lifespan_context = AppContext(
            server=mock_server, is_oauth=True
        )

        mock_access_token = Mock()
        mock_access_token.token = "fake.jwt.token"
        mock_access_token.client_id = "testuser@cyberark.cloud.12345"

        with patch(
            "mcp_privilege_cloud.mcp_server.get_access_token",
            return_value=mock_access_token,
        ):
            with patch("mcp_privilege_cloud.mcp_server.logger") as mock_logger:
                await execute_tool("list_accounts", ctx=ctx)

                mock_logger.info.assert_any_call(
                    "Authenticated user: %s", "testuser@cyberark.cloud.12345"
                )
