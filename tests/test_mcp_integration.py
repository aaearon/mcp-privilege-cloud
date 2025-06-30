#!/usr/bin/env python3
"""
MCP Integration Tests

Consolidated test suite for all MCP tool integrations including account, platform,
and safe management functionality. Tests ensure proper parameter passing,
error handling, and integration with the CyberArk MCP Server.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import os
import sys

# Add src to Python path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Account management MCP tools
from cyberark_mcp.mcp_server import create_account

# Platform management MCP tools  
from cyberark_mcp.mcp_server import list_platforms, get_platform_details, import_platform_package
from cyberark_mcp.server import CyberArkMCPServer

# Safe management MCP tools
from cyberark_mcp.mcp_server import list_safes as mcp_list_safes
from cyberark_mcp.mcp_server import get_safe_details as mcp_get_safe_details


class TestMCPAccountTools:
    """Test MCP account management tools integration"""

    @pytest.mark.asyncio
    async def test_create_account_mcp_tool_minimal(self):
        """Test MCP tool with minimal required parameters"""
        expected_response = {
            "id": "123_456",
            "platformId": "WinServerLocal",
            "safeName": "IT-Infrastructure",
            "createdDateTime": "2025-06-09T10:30:00Z"
        }
        
        with patch('cyberark_mcp.mcp_server.CyberArkMCPServer.from_environment') as mock_server_factory:
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
        
        account_platform_properties = {"LogonDomain": "EXAMPLE", "Port": "3389"}
        account_secret_mgmt = {"automaticManagementEnabled": True}
        
        with patch('cyberark_mcp.mcp_server.CyberArkMCPServer.from_environment') as mock_server_factory:
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
                platform_account_properties=account_platform_properties,
                secret_management=account_secret_mgmt
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
                platform_account_properties=account_platform_properties,
                secret_management=account_secret_mgmt,
                remote_machines_access=None
            )


class TestMCPPlatformTools:
    """Test MCP platform management tools integration"""

    @pytest.fixture
    def platform_mock_env_vars(self):
        """Mock environment variables for platform tests"""
        return {
            "CYBERARK_IDENTITY_TENANT_ID": "test-tenant",
            "CYBERARK_CLIENT_ID": "test-client",
            "CYBERARK_CLIENT_SECRET": "test-secret",
            "CYBERARK_SUBDOMAIN": "test-subdomain"
        }

    @pytest.mark.asyncio
    async def test_mcp_list_platforms_tool(self, platform_mock_env_vars):
        """Test the MCP list_platforms tool"""
        mock_platforms = [
            {"id": "WinServerLocal", "name": "Windows Server Local"},
            {"id": "UnixSSH", "name": "Unix via SSH"}
        ]
        
        with patch.dict(os.environ, platform_mock_env_vars):
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
    async def test_mcp_list_platforms_with_filters(self, platform_mock_env_vars):
        """Test the MCP list_platforms tool with filters"""
        mock_platforms = [{"id": "WinServerLocal", "name": "Windows Server Local"}]
        
        with patch.dict(os.environ, platform_mock_env_vars):
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
    async def test_mcp_get_platform_details_tool(self, platform_mock_env_vars):
        """Test the MCP get_platform_details tool"""
        platform_id = "WinServerLocal"
        mock_platform = {
            "id": platform_id,
            "name": "Windows Server Local",
            "details": {"credentialsManagementPolicy": {"change": "on"}}
        }
        
        with patch.dict(os.environ, platform_mock_env_vars):
            with patch.object(CyberArkMCPServer, 'get_platform_details', new_callable=AsyncMock) as mock_get:
                mock_get.return_value = mock_platform
                
                result = await get_platform_details(platform_id)
                
                assert result == mock_platform
                mock_get.assert_called_once_with(platform_id)

    @pytest.mark.asyncio
    async def test_mcp_platform_tools_error_handling(self, platform_mock_env_vars):
        """Test MCP platform tools handle errors properly"""
        with patch.dict(os.environ, platform_mock_env_vars):
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

    @pytest.mark.asyncio
    async def test_mcp_import_platform_package_tool(self, platform_mock_env_vars):
        """Test the MCP import_platform_package tool"""
        platform_file = "/tmp/test_platform.zip"
        mock_response = {"PlatformID": "ImportedPlatform123"}
        
        with patch.dict(os.environ, platform_mock_env_vars):
            with patch.object(CyberArkMCPServer, 'import_platform_package', new_callable=AsyncMock) as mock_import:
                mock_import.return_value = mock_response
                
                result = await import_platform_package(platform_file)
                
                assert result == mock_response
                mock_import.assert_called_once_with(platform_file)

    @pytest.mark.asyncio
    async def test_mcp_import_platform_package_error_handling(self, platform_mock_env_vars):
        """Test MCP import_platform_package tool handles errors properly"""
        with patch.dict(os.environ, platform_mock_env_vars):
            with patch.object(CyberArkMCPServer, 'import_platform_package', new_callable=AsyncMock) as mock_import:
                mock_import.side_effect = ValueError("Platform package file not found")
                
                with pytest.raises(ValueError, match="Platform package file not found"):
                    await import_platform_package("/tmp/nonexistent.zip")


class TestMCPSafeTools:
    """Test MCP safe management tools integration"""

    @pytest.mark.asyncio
    async def test_mcp_list_safes_basic(self):
        """Test MCP list_safes tool with basic usage"""
        mock_safes = [
            {"safeName": "HRSafe", "description": "HR Safe"},
            {"safeName": "ITSafe", "description": "IT Safe"}
        ]
        
        with patch('cyberark_mcp.mcp_server.CyberArkMCPServer.from_environment') as mock_from_env:
            mock_server = AsyncMock()
            mock_server.list_safes.return_value = mock_safes
            mock_from_env.return_value = mock_server
            
            result = await mcp_list_safes()
            
            mock_server.list_safes.assert_called_once_with(
                search=None,
                offset=None,
                limit=None,
                sort=None,
                include_accounts=None,
                extended_details=None
            )
            assert result == mock_safes

    @pytest.mark.asyncio
    async def test_mcp_list_safes_with_parameters(self):
        """Test MCP list_safes tool with all parameters"""
        mock_safes = [{"safeName": "HRSafe"}]
        
        safe_params = {
            "search": "HR",
            "offset": 10,
            "limit": 5,
            "sort": "safeName desc",
            "include_accounts": True,
            "extended_details": False
        }
        
        with patch('cyberark_mcp.mcp_server.CyberArkMCPServer.from_environment') as mock_from_env:
            mock_server = AsyncMock()
            mock_server.list_safes.return_value = mock_safes
            mock_from_env.return_value = mock_server
            
            result = await mcp_list_safes(**safe_params)
            
            mock_server.list_safes.assert_called_once_with(**safe_params)
            assert result == mock_safes

    @pytest.mark.asyncio
    async def test_mcp_list_safes_error_handling(self):
        """Test MCP list_safes tool error handling"""
        with patch('cyberark_mcp.mcp_server.CyberArkMCPServer.from_environment') as mock_from_env:
            mock_server = AsyncMock()
            mock_server.list_safes.side_effect = Exception("API Error")
            mock_from_env.return_value = mock_server
            
            with pytest.raises(Exception, match="API Error"):
                await mcp_list_safes()

    @pytest.mark.asyncio
    async def test_mcp_get_safe_details_basic(self):
        """Test MCP get_safe_details tool with basic usage"""
        safe_name = "HRSafe"
        mock_safe = {
            "safeName": safe_name,
            "description": "HR Safe",
            "accounts": []
        }
        
        with patch('cyberark_mcp.mcp_server.CyberArkMCPServer.from_environment') as mock_from_env:
            mock_server = AsyncMock()
            mock_server.get_safe_details.return_value = mock_safe
            mock_from_env.return_value = mock_server
            
            result = await mcp_get_safe_details(safe_name)
            
            mock_server.get_safe_details.assert_called_once_with(
                safe_name,
                include_accounts=None,
                use_cache=None
            )
            assert result == mock_safe

    @pytest.mark.asyncio
    async def test_mcp_get_safe_details_with_parameters(self):
        """Test MCP get_safe_details tool with parameters"""
        safe_name = "HRSafe"
        mock_safe = {
            "safeName": safe_name,
            "accounts": [{"id": "123", "name": "hr-admin"}]
        }
        
        with patch('cyberark_mcp.mcp_server.CyberArkMCPServer.from_environment') as mock_from_env:
            mock_server = AsyncMock()
            mock_server.get_safe_details.return_value = mock_safe
            mock_from_env.return_value = mock_server
            
            result = await mcp_get_safe_details(
                safe_name,
                include_accounts=True,
                use_cache=False
            )
            
            mock_server.get_safe_details.assert_called_once_with(
                safe_name,
                include_accounts=True,
                use_cache=False
            )
            assert result == mock_safe

    @pytest.mark.asyncio
    async def test_mcp_get_safe_details_error_handling(self):
        """Test MCP get_safe_details tool error handling"""
        safe_name = "NonExistentSafe"
        
        with patch('cyberark_mcp.mcp_server.CyberArkMCPServer.from_environment') as mock_from_env:
            mock_server = AsyncMock()
            mock_server.get_safe_details.side_effect = Exception("Safe not found")
            mock_from_env.return_value = mock_server
            
            with pytest.raises(Exception, match="Safe not found"):
                await mcp_get_safe_details(safe_name)

    @pytest.mark.asyncio
    async def test_mcp_list_safes_pagination_scenario(self):
        """Test MCP list_safes with pagination parameters"""
        # Simulate a paginated request
        mock_safes = [{"safeName": f"Safe{i}"} for i in range(10)]
        
        with patch('cyberark_mcp.mcp_server.CyberArkMCPServer.from_environment') as mock_from_env:
            mock_server = AsyncMock()
            mock_server.list_safes.return_value = mock_safes
            mock_from_env.return_value = mock_server
            
            result = await mcp_list_safes(
                offset=20,
                limit=10,
                sort="safeName asc"
            )
            
            mock_server.list_safes.assert_called_once_with(
                search=None,
                offset=20,
                limit=10,
                sort="safeName asc",
                include_accounts=None,
                extended_details=None
            )
            assert len(result) == 10

    @pytest.mark.asyncio
    async def test_mcp_get_safe_details_with_special_characters(self):
        """Test MCP get_safe_details with safe names containing special characters"""
        safe_name = "My Safe With Spaces & Special Characters"
        mock_safe = {"safeName": safe_name}
        
        with patch('cyberark_mcp.mcp_server.CyberArkMCPServer.from_environment') as mock_from_env:
            mock_server = AsyncMock()
            mock_server.get_safe_details.return_value = mock_safe
            mock_from_env.return_value = mock_server
            
            result = await mcp_get_safe_details(safe_name)
            
            # Verify the safe name is passed through correctly
            mock_server.get_safe_details.assert_called_once_with(
                safe_name,
                include_accounts=None,
                use_cache=None
            )
            assert result == mock_safe