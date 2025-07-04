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
from mcp_privilege_cloud.mcp_server import create_account, set_next_password

# Platform management MCP tools  
from mcp_privilege_cloud.mcp_server import import_platform_package

# New listing MCP tools that replaced resources
from mcp_privilege_cloud.mcp_server import list_accounts, search_accounts, list_safes, list_platforms

from mcp_privilege_cloud.server import CyberArkMCPServer


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
        
        with patch('mcp_privilege_cloud.mcp_server.CyberArkMCPServer.from_environment') as mock_server_factory:
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
        
        with patch('mcp_privilege_cloud.mcp_server.CyberArkMCPServer.from_environment') as mock_server_factory:
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

    @pytest.mark.asyncio
    async def test_change_account_password_mcp_tool_cpm_managed(self):
        """Test change_account_password MCP tool for CPM-managed accounts"""
        from src.mcp_privilege_cloud.mcp_server import change_account_password
        
        account_id = "123_456_789"
        mock_response = {
            "id": account_id,
            "lastModifiedTime": "2025-06-30T10:30:00Z",
            "status": "Password change initiated successfully"
        }
        
        with patch('src.mcp_privilege_cloud.mcp_server.CyberArkMCPServer.from_environment') as mock_server_factory:
            # Mock the server instance and its method
            mock_server = Mock()
            mock_server.change_account_password = AsyncMock(return_value=mock_response)
            mock_server_factory.return_value = mock_server
            
            # Call the MCP tool
            result = await change_account_password(account_id=account_id)
            
            # Verify result
            assert result == mock_response
            assert result["id"] == account_id
            assert "lastModifiedTime" in result
            
            # Verify server method was called correctly
            mock_server.change_account_password.assert_called_once_with(
                account_id=account_id,
                new_password=None
            )



    @pytest.mark.asyncio
    async def test_change_account_password_mcp_tool_error_handling(self):
        """Test change_account_password MCP tool error handling"""
        from src.mcp_privilege_cloud.mcp_server import change_account_password
        from src.mcp_privilege_cloud.server import CyberArkAPIError
        
        account_id = "invalid_account"
        
        with patch('src.mcp_privilege_cloud.mcp_server.CyberArkMCPServer.from_environment') as mock_server_factory:
            # Mock the server instance to raise an error
            mock_server = Mock()
            mock_server.change_account_password = AsyncMock(
                side_effect=CyberArkAPIError("Account not found", 404)
            )
            mock_server_factory.return_value = mock_server
            
            # Verify that the error is propagated
            with pytest.raises(CyberArkAPIError, match="Account not found"):
                await change_account_password(account_id=account_id)
            
            # Verify server method was called
            mock_server.change_account_password.assert_called_once_with(
                account_id=account_id,
                new_password=None
            )

    @pytest.mark.asyncio
    async def test_set_next_password_mcp_tool_success(self):
        """Test set_next_password MCP tool with successful operation"""
        account_id = "123_456_789"
        new_password = "NewSecureP@ssw0rd123"
        
        mock_response = {
            "id": account_id,
            "lastModifiedTime": "2025-06-30T10:30:00Z",
            "status": "Next password set successfully"
        }
        
        with patch('mcp_privilege_cloud.mcp_server.CyberArkMCPServer.from_environment') as mock_server_factory:
            # Mock the server instance and its method
            mock_server = Mock()
            mock_server.set_next_password = AsyncMock(return_value=mock_response)
            mock_server_factory.return_value = mock_server
            
            # Call the MCP tool
            result = await set_next_password(
                account_id=account_id,
                new_password=new_password
            )
            
            # Verify result
            assert result == mock_response
            assert result["id"] == account_id
            assert "lastModifiedTime" in result
            
            # Verify server method was called correctly
            mock_server.set_next_password.assert_called_once_with(
                account_id=account_id,
                new_password=new_password,
                change_immediately=True
            )

    @pytest.mark.asyncio
    async def test_set_next_password_mcp_tool_with_change_immediately_false(self):
        """Test set_next_password MCP tool with change_immediately=False"""
        account_id = "123_456_789"
        new_password = "NewSecureP@ssw0rd123"
        
        mock_response = {
            "id": account_id,
            "lastModifiedTime": "2025-06-30T10:30:00Z",
            "status": "Next password scheduled successfully"
        }
        
        with patch('mcp_privilege_cloud.mcp_server.CyberArkMCPServer.from_environment') as mock_server_factory:
            # Mock the server instance and its method
            mock_server = Mock()
            mock_server.set_next_password = AsyncMock(return_value=mock_response)
            mock_server_factory.return_value = mock_server
            
            # Call the MCP tool
            result = await set_next_password(
                account_id=account_id,
                new_password=new_password,
                change_immediately=False
            )
            
            # Verify result
            assert result == mock_response
            assert result["id"] == account_id
            
            # Verify server method was called correctly
            mock_server.set_next_password.assert_called_once_with(
                account_id=account_id,
                new_password=new_password,
                change_immediately=False
            )

    @pytest.mark.asyncio
    async def test_set_next_password_mcp_tool_error_handling(self):
        """Test set_next_password MCP tool error handling"""
        from mcp_privilege_cloud.server import CyberArkAPIError
        
        account_id = "invalid_account"
        new_password = "TestPassword123"
        
        with patch('mcp_privilege_cloud.mcp_server.CyberArkMCPServer.from_environment') as mock_server_factory:
            # Mock the server instance to raise an error
            mock_server = Mock()
            mock_server.set_next_password = AsyncMock(
                side_effect=CyberArkAPIError("Account not found", 404)
            )
            mock_server_factory.return_value = mock_server
            
            # Verify that the error is propagated
            with pytest.raises(CyberArkAPIError, match="Account not found"):
                await set_next_password(
                    account_id=account_id,
                    new_password=new_password
                )
            
            # Verify server method was called
            mock_server.set_next_password.assert_called_once_with(
                account_id=account_id,
                new_password=new_password,
                change_immediately=True
            )

    @pytest.mark.asyncio
    async def test_verify_account_password_mcp_tool_success(self):
        """Test verify account password MCP tool with successful verification"""
        account_id = "123_456_789"
        
        mock_response = {
            "id": account_id,
            "lastVerifiedDateTime": "2025-06-30T10:30:00Z",
            "verified": True,
            "status": "Password verified successfully"
        }
        
        with patch('src.mcp_privilege_cloud.mcp_server.CyberArkMCPServer') as mock_server_class:
            mock_server = AsyncMock()
            mock_server.verify_account_password.return_value = mock_response
            mock_server_class.from_environment.return_value = mock_server
            
            # Import and call the MCP tool function
            from src.mcp_privilege_cloud.mcp_server import verify_account_password
            
            result = await verify_account_password(account_id=account_id)
            
            # Verify the result
            assert result["id"] == account_id
            assert result["verified"] is True
            assert "lastVerifiedDateTime" in result
            assert "status" in result
            
            # Verify server method was called correctly
            mock_server.verify_account_password.assert_called_once_with(account_id=account_id)
    
    @pytest.mark.asyncio
    async def test_verify_account_password_mcp_tool_error_handling(self):
        """Test verify account password MCP tool error handling"""
        account_id = "invalid_account"
        
        with patch('src.mcp_privilege_cloud.mcp_server.CyberArkMCPServer') as mock_server_class:
            mock_server = AsyncMock()
            mock_server.verify_account_password.side_effect = Exception("Account not found")
            mock_server_class.from_environment.return_value = mock_server
            
            # Import and call the MCP tool function
            from src.mcp_privilege_cloud.mcp_server import verify_account_password
            
            with pytest.raises(Exception, match="Account not found"):
                await verify_account_password(account_id=account_id)
            
            # Verify server method was called
            mock_server.verify_account_password.assert_called_once_with(account_id=account_id)

    @pytest.mark.asyncio
    async def test_reconcile_account_password_mcp_tool_success(self):
        """Test the reconcile_account_password MCP tool with successful reconciliation"""
        from src.mcp_privilege_cloud.mcp_server import reconcile_account_password
        
        account_id = "test_account_123"
        
        # Mock response from server
        mock_response = {
            "id": account_id,
            "reconciled": True,
            "status": "Password reconciled successfully",
            "lastReconciledDateTime": "2025-06-30T10:30:00Z",
            "platformId": "WinDomain",
            "safeName": "TestSafe"
        }
        
        with patch('src.mcp_privilege_cloud.mcp_server.CyberArkMCPServer.from_environment') as mock_server_factory:
            # Mock the server instance
            mock_server = Mock()
            mock_server.reconcile_account_password = AsyncMock(return_value=mock_response)
            mock_server_factory.return_value = mock_server
            
            # Call the MCP tool function
            result = await reconcile_account_password(account_id=account_id)
            
            # Verify the result
            assert result == mock_response
            assert result["id"] == account_id
            assert result["reconciled"] is True
            assert result["status"] == "Password reconciled successfully"
            assert result["lastReconciledDateTime"] == "2025-06-30T10:30:00Z"
            
            # Verify server method was called correctly
            mock_server.reconcile_account_password.assert_called_once_with(account_id=account_id)

    @pytest.mark.asyncio
    async def test_reconcile_account_password_mcp_tool_error_handling(self):
        """Test the reconcile_account_password MCP tool error handling"""
        from src.mcp_privilege_cloud.mcp_server import reconcile_account_password
        from src.mcp_privilege_cloud.server import CyberArkAPIError
        
        account_id = "invalid_account"
        
        with patch('src.mcp_privilege_cloud.mcp_server.CyberArkMCPServer.from_environment') as mock_server_factory:
            # Mock the server instance to raise an error
            mock_server = Mock()
            mock_server.reconcile_account_password = AsyncMock(
                side_effect=CyberArkAPIError("Account not found", 404)
            )
            mock_server_factory.return_value = mock_server
            
            # Call the MCP tool function and expect error
            with pytest.raises(CyberArkAPIError) as exc_info:
                await reconcile_account_password(account_id=account_id)
            
            # Verify the error details
            assert exc_info.value.status_code == 404
            assert "Account not found" in str(exc_info.value)
            
            # Verify server method was called
            mock_server.reconcile_account_password.assert_called_once_with(account_id=account_id)


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


class TestMCPListingTools:
    """Test MCP listing tools that replaced resources"""

    @pytest.fixture
    def mock_env_vars(self):
        """Mock environment variables for tests."""
        return {
            "CYBERARK_IDENTITY_TENANT_ID": "test-tenant",
            "CYBERARK_CLIENT_ID": "test-client-id",
            "CYBERARK_CLIENT_SECRET": "test-secret",
            "CYBERARK_SUBDOMAIN": "test-subdomain"
        }

    @pytest.mark.asyncio
    async def test_list_accounts_tool(self, mock_env_vars):
        """Test the list_accounts MCP tool"""
        mock_accounts = [
            {
                "id": "123_456",
                "name": "admin@server01",
                "address": "server01.corp.com",
                "userName": "admin",
                "platformId": "WinServerLocal",
                "safeName": "IT-Infrastructure"
            }
        ]
        
        with patch.dict(os.environ, mock_env_vars):
            with patch.object(CyberArkMCPServer, 'list_accounts', new_callable=AsyncMock) as mock_list:
                mock_list.return_value = mock_accounts
                
                result = await list_accounts()
                
                assert result == mock_accounts
                mock_list.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_accounts_tool(self, mock_env_vars):
        """Test the search_accounts MCP tool"""
        mock_accounts = [
            {
                "id": "123_456",
                "name": "admin@server01",
                "userName": "admin",
                "platformId": "WinServerLocal",
                "_score": 0.85
            }
        ]
        
        with patch.dict(os.environ, mock_env_vars):
            with patch.object(CyberArkMCPServer, 'search_accounts', new_callable=AsyncMock) as mock_search:
                mock_search.return_value = mock_accounts
                
                result = await search_accounts(query="admin", safe_name="IT-Infrastructure")
                
                assert result == mock_accounts
                mock_search.assert_called_once_with(
                    keywords="admin",
                    safe_name="IT-Infrastructure",
                    username=None,
                    address=None,
                    platform_id=None
                )

    @pytest.mark.asyncio
    async def test_list_safes_tool(self, mock_env_vars):
        """Test the list_safes MCP tool"""
        mock_safes = [
            {
                "safeName": "IT-Infrastructure",
                "safeNumber": 123,
                "description": "IT Infrastructure accounts",
                "createdBy": "Administrator"
            }
        ]
        
        with patch.dict(os.environ, mock_env_vars):
            with patch.object(CyberArkMCPServer, 'list_safes', new_callable=AsyncMock) as mock_list:
                mock_list.return_value = mock_safes
                
                result = await list_safes()
                
                assert result == mock_safes
                mock_list.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_platforms_tool(self, mock_env_vars):
        """Test the list_platforms MCP tool"""
        mock_platforms = [
            {
                "id": "WinServerLocal",
                "name": "Windows Server Local",
                "systemType": "Windows",
                "active": True,
                "platformType": "Regular"
            }
        ]
        
        with patch.dict(os.environ, mock_env_vars):
            with patch.object(CyberArkMCPServer, 'list_platforms', new_callable=AsyncMock) as mock_list:
                mock_list.return_value = mock_platforms
                
                result = await list_platforms()
                
                assert result == mock_platforms
                mock_list.assert_called_once()




