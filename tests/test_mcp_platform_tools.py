import pytest
from unittest.mock import Mock, AsyncMock, patch
import os
import sys

# Add src to Python path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from cyberark_mcp.mcp_server import list_platforms, get_platform_details
    from cyberark_mcp.server import CyberArkMCPServer
except ImportError as e:
    pytest.skip(f"Could not import MCP modules: {e}", allow_module_level=True)


class TestMCPPlatformTools:
    """Test MCP platform management tools integration"""

    @pytest.fixture
    def mock_env_vars(self):
        """Mock environment variables"""
        return {
            "CYBERARK_IDENTITY_TENANT_ID": "test-tenant",
            "CYBERARK_CLIENT_ID": "test-client",
            "CYBERARK_CLIENT_SECRET": "test-secret",
            "CYBERARK_SUBDOMAIN": "test-subdomain"
        }

    @pytest.mark.asyncio
    async def test_mcp_list_platforms_tool(self, mock_env_vars):
        """Test the MCP list_platforms tool"""
        mock_platforms = [
            {"id": "WinServerLocal", "name": "Windows Server Local"},
            {"id": "UnixSSH", "name": "Unix via SSH"}
        ]
        
        with patch.dict(os.environ, mock_env_vars):
            with patch.object(CyberArkMCPServer, 'list_platforms', new_callable=AsyncMock) as mock_list:
                mock_list.return_value = mock_platforms
                
                result = await list_platforms()
                
                assert result == mock_platforms
                mock_list.assert_called_once_with(
                    search=None,
                    active=None,
                    system_type=None
                )

    @pytest.mark.asyncio
    async def test_mcp_list_platforms_with_filters(self, mock_env_vars):
        """Test the MCP list_platforms tool with filters"""
        mock_platforms = [{"id": "WinServerLocal", "name": "Windows Server Local"}]
        
        with patch.dict(os.environ, mock_env_vars):
            with patch.object(CyberArkMCPServer, 'list_platforms', new_callable=AsyncMock) as mock_list:
                mock_list.return_value = mock_platforms
                
                result = await list_platforms(
                    search="Windows",
                    active=True,
                    system_type="Windows"
                )
                
                assert result == mock_platforms
                mock_list.assert_called_once_with(
                    search="Windows",
                    active=True,
                    system_type="Windows"
                )

    @pytest.mark.asyncio
    async def test_mcp_get_platform_details_tool(self, mock_env_vars):
        """Test the MCP get_platform_details tool"""
        platform_id = "WinServerLocal"
        mock_platform = {
            "id": platform_id,
            "name": "Windows Server Local",
            "details": {"credentialsManagementPolicy": {"change": "on"}}
        }
        
        with patch.dict(os.environ, mock_env_vars):
            with patch.object(CyberArkMCPServer, 'get_platform_details', new_callable=AsyncMock) as mock_get:
                mock_get.return_value = mock_platform
                
                result = await get_platform_details(platform_id)
                
                assert result == mock_platform
                mock_get.assert_called_once_with(platform_id)

    @pytest.mark.asyncio
    async def test_mcp_platform_tools_error_handling(self, mock_env_vars):
        """Test MCP platform tools handle errors properly"""
        with patch.dict(os.environ, mock_env_vars):
            with patch.object(CyberArkMCPServer, 'list_platforms', new_callable=AsyncMock) as mock_list:
                mock_list.side_effect = Exception("API Error")
                
                with pytest.raises(Exception, match="API Error"):
                    await list_platforms()
            
            with patch.object(CyberArkMCPServer, 'get_platform_details', new_callable=AsyncMock) as mock_get:
                mock_get.side_effect = Exception("Platform not found")
                
                with pytest.raises(Exception, match="Platform not found"):
                    await get_platform_details("NonExistentPlatform")

    @pytest.mark.asyncio
    async def test_mcp_platform_tools_environment_handling(self):
        """Test MCP platform tools handle missing environment variables"""
        # Clear environment variables
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError):
                await list_platforms()
            
            with pytest.raises(ValueError):
                await get_platform_details("TestPlatform")