"""
Integration Tests for CyberArk MCP Tools

Tests tool-based approach with context injection.
"""

import pytest
from unittest.mock import AsyncMock, Mock

from mcp_privilege_cloud.mcp_server import list_platforms, AppContext
from mcp_privilege_cloud.server import CyberArkMCPServer


def _make_ctx(mock_server):
    ctx = Mock()
    ctx.request_context.lifespan_context = AppContext(server=mock_server)
    return ctx


@pytest.mark.integration
class TestToolIntegration:
    """Test integration of tools with the CyberArk server."""

    @pytest.mark.asyncio
    async def test_list_platforms_integration(self):
        """Test that list_platforms tool properly integrates with server."""
        mock_platforms = [
            {
                "id": "WinServerLocal",
                "name": "Windows Server Local",
                "systemType": "Windows",
                "active": True,
                "platformType": "Regular",
                "description": "Windows Server Local Accounts"
            }
        ]

        mock_server = AsyncMock(spec=CyberArkMCPServer)
        mock_server.list_platforms.return_value = mock_platforms
        ctx = _make_ctx(mock_server)

        result = await list_platforms(ctx=ctx)

        assert result == mock_platforms
        assert result[0]["systemType"] == "Windows"
        assert result[0]["platformType"] == "Regular"
        mock_server.list_platforms.assert_called_once()

    @pytest.mark.asyncio
    async def test_tool_error_propagation(self):
        """Test that tool errors are properly propagated."""
        mock_server = AsyncMock(spec=CyberArkMCPServer)
        mock_server.list_platforms.side_effect = Exception("Server Error")
        ctx = _make_ctx(mock_server)

        with pytest.raises(Exception, match="Server Error"):
            await list_platforms(ctx=ctx)
