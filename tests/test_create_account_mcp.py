import pytest
from unittest.mock import Mock, AsyncMock, patch

from src.cyberark_mcp.mcp_server import create_account


class TestCreateAccountMCP:
    """Test the create_account MCP tool"""

    @pytest.mark.asyncio
    async def test_create_account_mcp_tool_minimal(self):
        """Test MCP tool with minimal required parameters"""
        expected_response = {
            "id": "123_456",
            "platformId": "WinServerLocal",
            "safeName": "IT-Infrastructure",
            "createdDateTime": "2025-06-09T10:30:00Z"
        }
        
        with patch('src.cyberark_mcp.mcp_server.CyberArkMCPServer.from_environment') as mock_server_factory:
            mock_server = Mock()
            mock_server.create_account = AsyncMock(return_value=expected_response)
            mock_server_factory.return_value = mock_server
            
            result = await create_account(
                platform_id="WinServerLocal",
                safe_name="IT-Infrastructure"
            )
            
            assert result == expected_response
            mock_server.create_account.assert_called_once_with(
                platform_id="WinServerLocal",
                safe_name="IT-Infrastructure",
                name=None,
                address=None,
                user_name=None,
                secret=None,
                secret_type=None,
                platform_account_properties=None,
                secret_management=None,
                remote_machines_access=None
            )

    @pytest.mark.asyncio
    async def test_create_account_mcp_tool_complete(self):
        """Test MCP tool with all parameters"""
        expected_response = {
            "id": "123_456",
            "name": "admin-server01",
            "address": "server01.example.com",
            "userName": "admin",
            "platformId": "WinServerLocal",
            "safeName": "IT-Infrastructure",
            "secretType": "password",
            "createdDateTime": "2025-06-09T10:30:00Z"
        }
        
        platform_properties = {"LogonDomain": "EXAMPLE", "Port": "3389"}
        secret_mgmt = {"automaticManagementEnabled": True}
        
        with patch('src.cyberark_mcp.mcp_server.CyberArkMCPServer.from_environment') as mock_server_factory:
            mock_server = Mock()
            mock_server.create_account = AsyncMock(return_value=expected_response)
            mock_server_factory.return_value = mock_server
            
            result = await create_account(
                platform_id="WinServerLocal",
                safe_name="IT-Infrastructure",
                name="admin-server01",
                address="server01.example.com",
                user_name="admin",
                secret="SecurePassword123!",
                secret_type="password",
                platform_account_properties=platform_properties,
                secret_management=secret_mgmt
            )
            
            assert result == expected_response
            mock_server.create_account.assert_called_once_with(
                platform_id="WinServerLocal",
                safe_name="IT-Infrastructure",
                name="admin-server01",
                address="server01.example.com",
                user_name="admin",
                secret="SecurePassword123!",
                secret_type="password",
                platform_account_properties=platform_properties,
                secret_management=secret_mgmt,
                remote_machines_access=None
            )