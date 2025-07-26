"""
Integration Tests for CyberArk MCP Tools

This module provides integration tests for the new tool-based approach,
replacing the previous resource-based tests.
"""

import pytest
from unittest.mock import AsyncMock, patch

from mcp_privilege_cloud.mcp_server import list_platforms
from mcp_privilege_cloud.server import CyberArkMCPServer


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
        
        with patch('mcp_privilege_cloud.mcp_server.CyberArkMCPServer.from_environment') as mock_server_factory:
            mock_server = AsyncMock()
            mock_server.list_platforms.return_value = mock_platforms
            mock_server_factory.return_value = mock_server
            
            # Test the tool function
            result = await list_platforms()
            
            # Verify exact API data is returned (no manipulation)
            assert result == mock_platforms
            assert result[0]["systemType"] == "Windows"  # Original camelCase preserved
            assert result[0]["platformType"] == "Regular"  # Original camelCase preserved
            
            # Verify server method was called
            mock_server.list_platforms.assert_called_once()

    @pytest.mark.asyncio 
    async def test_tool_error_propagation(self):
        """Test that tool errors are properly propagated."""
        with patch('mcp_privilege_cloud.mcp_server.CyberArkMCPServer.from_environment') as mock_server_factory:
            mock_server = AsyncMock()
            mock_server.list_platforms.side_effect = Exception("Server Error")
            mock_server_factory.return_value = mock_server
            
            with pytest.raises(Exception, match="Server Error"):
                await list_platforms()