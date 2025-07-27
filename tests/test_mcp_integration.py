#\!/usr/bin/env python3
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
from mcp_privilege_cloud.mcp_server import create_account, set_next_password, update_account, delete_account

# Platform management MCP tools  
from mcp_privilege_cloud.mcp_server import (
    import_platform_package,
    export_platform,
    duplicate_target_platform,
    activate_target_platform,
    deactivate_target_platform,
    delete_target_platform
)

# New listing MCP tools that replaced resources
from mcp_privilege_cloud.mcp_server import list_accounts, search_accounts, list_safes, add_safe, list_platforms

# Safe member management MCP tools
from mcp_privilege_cloud.mcp_server import (
    list_safe_members,
    get_safe_member_details,
    add_safe_member,
    update_safe_member,
    remove_safe_member
)

from mcp_privilege_cloud.server import CyberArkMCPServer


@pytest.mark.integration
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
        
        # Use AsyncMock for the server instance
        mock_server = AsyncMock(spec=CyberArkMCPServer)
        mock_server.create_account.return_value = expected_response

        # Correctly patch the get_server function
        with patch('mcp_privilege_cloud.mcp_server.get_server', return_value=mock_server) as mock_get_server:
            result = await create_account(
                platform_id="WinServerLocal",
                safe_name="IT-Infrastructure"
            )
            
            assert result == expected_response
            mock_get_server.assert_called_once()
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
        
        # Use AsyncMock for the server instance
        mock_server = AsyncMock(spec=CyberArkMCPServer)
        mock_server.create_account.return_value = expected_response

        # Correctly patch the get_server function
        with patch('mcp_privilege_cloud.mcp_server.get_server', return_value=mock_server) as mock_get_server:
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
            mock_get_server.assert_called_once()
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
        from mcp_privilege_cloud.mcp_server import change_account_password
        
        account_id = "123_456_789"
        mock_response = {
            "id": account_id,
            "lastModifiedTime": "2025-06-30T10:30:00Z",
            "status": "Password change initiated successfully"
        }
        
        # Mock get_server to avoid SDK authentication
        mock_server = AsyncMock()
        mock_server.change_account_password.return_value = mock_response
        
        with patch('mcp_privilege_cloud.mcp_server.get_server', return_value=mock_server):
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
        from mcp_privilege_cloud.mcp_server import change_account_password
        from mcp_privilege_cloud.server import CyberArkAPIError
        
        account_id = "invalid_account"
        
        # Use AsyncMock for the server instance
        mock_server = AsyncMock()
        mock_server.change_account_password.side_effect = CyberArkAPIError("Account not found", 404)

        # Correctly patch the get_server function
        with patch('mcp_privilege_cloud.mcp_server.get_server', return_value=mock_server):
            # Verify that the error is propagated
            with pytest.raises(CyberArkAPIError, match="Account not found"):
                await change_account_password(account_id=account_id)
            
            # Verify server method was called correctly
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
        
        # Use AsyncMock for the server instance
        mock_server = AsyncMock(spec=CyberArkMCPServer)
        mock_server.set_next_password.return_value = mock_response

        # Correctly patch the get_server function
        with patch('mcp_privilege_cloud.mcp_server.get_server', return_value=mock_server) as mock_get_server:
            # Call the MCP tool
            result = await set_next_password(
                account_id=account_id,
                new_password=new_password
            )
            
            # Verify result
            assert result == mock_response
            assert result["id"] == account_id
            assert "lastModifiedTime" in result
            
            # Verify mock_get_server was called and server method was called correctly
            mock_get_server.assert_called_once()
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
        
        # Use AsyncMock for the server instance
        mock_server = AsyncMock(spec=CyberArkMCPServer)
        mock_server.set_next_password.return_value = mock_response

        # Correctly patch the get_server function
        with patch('mcp_privilege_cloud.mcp_server.get_server', return_value=mock_server) as mock_get_server:
            # Call the MCP tool
            result = await set_next_password(
                account_id=account_id,
                new_password=new_password,
                change_immediately=False
            )
            
            # Verify result
            assert result == mock_response
            assert result["id"] == account_id
            
            # Verify mock_get_server was called and server method was called correctly
            mock_get_server.assert_called_once()
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
        
        # Use AsyncMock for the server instance
        mock_server = AsyncMock(spec=CyberArkMCPServer)
        mock_server.set_next_password.side_effect = CyberArkAPIError("Account not found", 404)

        # Correctly patch the get_server function
        with patch('mcp_privilege_cloud.mcp_server.get_server', return_value=mock_server) as mock_get_server:
            # Verify that the error is propagated
            with pytest.raises(CyberArkAPIError, match="Account not found"):
                await set_next_password(
                    account_id=account_id,
                    new_password=new_password
                )
            
            # Verify mock_get_server was called and server method was called correctly
            mock_get_server.assert_called_once()
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
        
        # Import the MCP tool function
        from mcp_privilege_cloud.mcp_server import verify_account_password
        
        mock_server = AsyncMock()
        mock_server.verify_account_password.return_value = mock_response
        
        with patch('mcp_privilege_cloud.mcp_server.get_server', return_value=mock_server):
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
        
        # Import the MCP tool function
        from mcp_privilege_cloud.mcp_server import verify_account_password
        
        mock_server = AsyncMock()
        mock_server.verify_account_password.side_effect = Exception("Account not found")
        
        with patch('mcp_privilege_cloud.mcp_server.get_server', return_value=mock_server):
            with pytest.raises(Exception, match="Account not found"):
                await verify_account_password(account_id=account_id)
            
            # Verify server method was called
            mock_server.verify_account_password.assert_called_once_with(account_id=account_id)

    @pytest.mark.asyncio
    async def test_reconcile_account_password_mcp_tool_success(self):
        """Test the reconcile_account_password MCP tool with successful reconciliation"""
        from mcp_privilege_cloud.mcp_server import reconcile_account_password
        
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
        
        # Use AsyncMock for the server instance
        mock_server = AsyncMock(spec=CyberArkMCPServer)
        mock_server.reconcile_account_password.return_value = mock_response

        # Correctly patch the get_server function
        with patch('mcp_privilege_cloud.mcp_server.get_server', return_value=mock_server) as mock_get_server:
            # Call the MCP tool function
            result = await reconcile_account_password(account_id=account_id)
            
            # Verify the result
            assert result == mock_response
            assert result["id"] == account_id
            assert result["reconciled"] is True
            assert result["status"] == "Password reconciled successfully"
            assert result["lastReconciledDateTime"] == "2025-06-30T10:30:00Z"
            
            # Verify mock_get_server was called and server method was called correctly
            mock_get_server.assert_called_once()
            mock_server.reconcile_account_password.assert_called_once_with(account_id=account_id)

    @pytest.mark.asyncio
    async def test_reconcile_account_password_mcp_tool_error_handling(self):
        """Test the reconcile_account_password MCP tool error handling"""
        from mcp_privilege_cloud.mcp_server import reconcile_account_password
        from mcp_privilege_cloud.server import CyberArkAPIError
        
        account_id = "invalid_account"
        
        # Use AsyncMock for the server instance
        mock_server = AsyncMock(spec=CyberArkMCPServer)
        mock_server.reconcile_account_password.side_effect = CyberArkAPIError("Account not found", 404)

        # Correctly patch the get_server function
        with patch('mcp_privilege_cloud.mcp_server.get_server', return_value=mock_server) as mock_get_server:
            # Call the MCP tool function and expect error
            with pytest.raises(CyberArkAPIError) as exc_info:
                await reconcile_account_password(account_id=account_id)
            
            # Verify the error details
            assert exc_info.value.status_code == 404
            assert "Account not found" in str(exc_info.value)
            
            # Verify mock_get_server was called and server method was called correctly
            mock_get_server.assert_called_once()
            mock_server.reconcile_account_password.assert_called_once_with(account_id=account_id)


@pytest.mark.integration
class TestMCPPlatformTools:
    """Test MCP platform management tools integration"""

    @pytest.fixture
    def platform_mock_env_vars(self):
        """Mock environment variables for platform tests"""
        return {
            "CYBERARK_CLIENT_ID": "test-client",
            "CYBERARK_CLIENT_SECRET": "test-secret"
        }

    @pytest.mark.asyncio
    async def test_mcp_import_platform_package_tool(self, platform_mock_env_vars):
        """Test the MCP import_platform_package tool"""
        platform_file = "/tmp/test_platform.zip"
        mock_response = {"PlatformID": "ImportedPlatform123"}
        
        mock_server = AsyncMock()
        mock_server.import_platform_package.return_value = mock_response
        
        with patch('mcp_privilege_cloud.mcp_server.get_server', return_value=mock_server):
            result = await import_platform_package(platform_file)
            
            assert result == mock_response
            mock_server.import_platform_package.assert_called_once_with(platform_package_file=platform_file)

    @pytest.mark.asyncio
    async def test_mcp_import_platform_package_error_handling(self, platform_mock_env_vars):
        """Test MCP import_platform_package tool handles errors properly"""
        mock_server = AsyncMock()
        mock_server.import_platform_package.side_effect = ValueError("Platform package file not found")
        
        with patch('mcp_privilege_cloud.mcp_server.get_server', return_value=mock_server):
            with pytest.raises(ValueError, match="Platform package file not found"):
                await import_platform_package("/tmp/nonexistent.zip")

    @pytest.mark.asyncio
    async def test_mcp_export_platform_tool(self, platform_mock_env_vars):
        """Test the MCP export_platform tool"""
        platform_id = "WinServerLocal"
        output_folder = "/tmp/exports"
        mock_response = {
            "platform_id": platform_id,
            "output_folder": output_folder,
            "status": "exported"
        }
        
        mock_server = AsyncMock()
        mock_server.export_platform.return_value = mock_response
        
        with patch('mcp_privilege_cloud.mcp_server.get_server', return_value=mock_server):
            result = await export_platform(platform_id, output_folder)
            
            assert result == mock_response
            mock_server.export_platform.assert_called_once_with(
                platform_id=platform_id, 
                output_folder=output_folder
            )

    @pytest.mark.asyncio
    async def test_mcp_export_platform_error_handling(self, platform_mock_env_vars):
        """Test MCP export_platform tool handles errors properly"""
        mock_server = AsyncMock()
        mock_server.export_platform.side_effect = ValueError("Platform not found")
        
        with patch('mcp_privilege_cloud.mcp_server.get_server', return_value=mock_server):
            with pytest.raises(ValueError, match="Platform not found"):
                await export_platform("NonexistentPlatform", "/tmp/exports")

    @pytest.mark.asyncio
    async def test_mcp_duplicate_target_platform_tool(self, platform_mock_env_vars):
        """Test the MCP duplicate_target_platform tool"""
        target_platform_id = 123
        name = "Duplicated Platform"
        description = "Test duplicate"
        mock_response = {
            "target_platform_id": 456,
            "name": name,
            "description": description,
            "status": "duplicated"
        }
        
        mock_server = AsyncMock()
        mock_server.duplicate_target_platform.return_value = mock_response
        
        with patch('mcp_privilege_cloud.mcp_server.get_server', return_value=mock_server):
            result = await duplicate_target_platform(target_platform_id, name, description)
            
            assert result == mock_response
            mock_server.duplicate_target_platform.assert_called_once_with(
                target_platform_id=target_platform_id,
                name=name,
                description=description
            )

    @pytest.mark.asyncio
    async def test_mcp_duplicate_target_platform_without_description(self, platform_mock_env_vars):
        """Test the MCP duplicate_target_platform tool without description"""
        target_platform_id = 123
        name = "Duplicated Platform"
        mock_response = {
            "target_platform_id": 456,
            "name": name,
            "description": None,
            "status": "duplicated"
        }
        
        mock_server = AsyncMock()
        mock_server.duplicate_target_platform.return_value = mock_response
        
        with patch('mcp_privilege_cloud.mcp_server.get_server', return_value=mock_server):
            result = await duplicate_target_platform(target_platform_id, name)
            
            assert result == mock_response
            mock_server.duplicate_target_platform.assert_called_once_with(
                target_platform_id=target_platform_id,
                name=name,
                description=None
            )

    @pytest.mark.asyncio
    async def test_mcp_duplicate_target_platform_error_handling(self, platform_mock_env_vars):
        """Test MCP duplicate_target_platform tool handles errors properly"""
        mock_server = AsyncMock()
        mock_server.duplicate_target_platform.side_effect = ValueError("Target platform not found")
        
        with patch('mcp_privilege_cloud.mcp_server.get_server', return_value=mock_server):
            with pytest.raises(ValueError, match="Target platform not found"):
                await duplicate_target_platform(999, "Test Platform")

    @pytest.mark.asyncio
    async def test_mcp_activate_target_platform_tool(self, platform_mock_env_vars):
        """Test the MCP activate_target_platform tool"""
        target_platform_id = 123
        mock_response = {
            "target_platform_id": target_platform_id,
            "status": "activated"
        }
        
        mock_server = AsyncMock()
        mock_server.activate_target_platform.return_value = mock_response
        
        with patch('mcp_privilege_cloud.mcp_server.get_server', return_value=mock_server):
            result = await activate_target_platform(target_platform_id)
            
            assert result == mock_response
            mock_server.activate_target_platform.assert_called_once_with(
                target_platform_id=target_platform_id
            )

    @pytest.mark.asyncio
    async def test_mcp_activate_target_platform_error_handling(self, platform_mock_env_vars):
        """Test MCP activate_target_platform tool handles errors properly"""
        mock_server = AsyncMock()
        mock_server.activate_target_platform.side_effect = ValueError("Target platform not found")
        
        with patch('mcp_privilege_cloud.mcp_server.get_server', return_value=mock_server):
            with pytest.raises(ValueError, match="Target platform not found"):
                await activate_target_platform(999)

    @pytest.mark.asyncio
    async def test_mcp_deactivate_target_platform_tool(self, platform_mock_env_vars):
        """Test the MCP deactivate_target_platform tool"""
        target_platform_id = 123
        mock_response = {
            "target_platform_id": target_platform_id,
            "status": "deactivated"
        }
        
        mock_server = AsyncMock()
        mock_server.deactivate_target_platform.return_value = mock_response
        
        with patch('mcp_privilege_cloud.mcp_server.get_server', return_value=mock_server):
            result = await deactivate_target_platform(target_platform_id)
            
            assert result == mock_response
            mock_server.deactivate_target_platform.assert_called_once_with(
                target_platform_id=target_platform_id
            )

    @pytest.mark.asyncio
    async def test_mcp_deactivate_target_platform_error_handling(self, platform_mock_env_vars):
        """Test MCP deactivate_target_platform tool handles errors properly"""
        mock_server = AsyncMock()
        mock_server.deactivate_target_platform.side_effect = ValueError("Target platform not found")
        
        with patch('mcp_privilege_cloud.mcp_server.get_server', return_value=mock_server):
            with pytest.raises(ValueError, match="Target platform not found"):
                await deactivate_target_platform(999)

    @pytest.mark.asyncio
    async def test_mcp_delete_target_platform_tool(self, platform_mock_env_vars):
        """Test the MCP delete_target_platform tool"""
        target_platform_id = 123
        mock_response = {
            "target_platform_id": target_platform_id,
            "status": "deleted"
        }
        
        mock_server = AsyncMock()
        mock_server.delete_target_platform.return_value = mock_response
        
        with patch('mcp_privilege_cloud.mcp_server.get_server', return_value=mock_server):
            result = await delete_target_platform(target_platform_id)
            
            assert result == mock_response
            mock_server.delete_target_platform.assert_called_once_with(
                target_platform_id=target_platform_id
            )

    @pytest.mark.asyncio
    async def test_mcp_delete_target_platform_error_handling(self, platform_mock_env_vars):
        """Test MCP delete_target_platform tool handles errors properly"""
        mock_server = AsyncMock()
        mock_server.delete_target_platform.side_effect = ValueError("Target platform not found or has dependencies")
        
        with patch('mcp_privilege_cloud.mcp_server.get_server', return_value=mock_server):
            with pytest.raises(ValueError, match="Target platform not found or has dependencies"):
                await delete_target_platform(999)


@pytest.mark.integration
class TestMCPListingTools:
    """Test MCP listing tools that replaced resources"""

    @pytest.fixture
    def mock_env_vars(self):
        """Mock environment variables for tests."""
        return {
            "CYBERARK_CLIENT_ID": "test-client-id",
            "CYBERARK_CLIENT_SECRET": "test-secret"
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
        
        mock_server = AsyncMock()
        mock_server.list_accounts.return_value = mock_accounts
        
        with patch('mcp_privilege_cloud.mcp_server.get_server', return_value=mock_server):
            result = await list_accounts()
            
            assert result == mock_accounts
            mock_server.list_accounts.assert_called_once()

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
        
        mock_server = AsyncMock()
        mock_server.search_accounts.return_value = mock_accounts
        
        with patch('mcp_privilege_cloud.mcp_server.get_server', return_value=mock_server):
            result = await search_accounts(query="admin", safe_name="IT-Infrastructure")
            
            assert result == mock_accounts
            mock_server.search_accounts.assert_called_once_with(
                query="admin",
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
        
        mock_server = AsyncMock()
        mock_server.list_safes.return_value = mock_safes
        
        with patch('mcp_privilege_cloud.mcp_server.get_server', return_value=mock_server):
            result = await list_safes()
            
            assert result == mock_safes
            mock_server.list_safes.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_safe_tool(self, mock_env_vars):
        """Test the add_safe MCP tool"""
        safe_name = "TestSafe"
        description = "Test safe description"
        
        mock_response = {
            "safeName": safe_name,
            "safeId": "123",
            "description": description,
            "location": "\\",
            "creator": "admin"
        }
        
        mock_server = AsyncMock()
        mock_server.add_safe.return_value = mock_response
        
        with patch('mcp_privilege_cloud.mcp_server.get_server', return_value=mock_server):
            result = await add_safe(safe_name, description)
            
            assert result == mock_response
            mock_server.add_safe.assert_called_once_with(safe_name=safe_name, description=description)

    @pytest.mark.asyncio
    async def test_add_safe_tool_minimal(self, mock_env_vars):
        """Test the add_safe MCP tool with minimal parameters"""
        safe_name = "MinimalTestSafe"
        
        mock_response = {
            "safeName": safe_name,
            "safeId": "124",
            "description": "",
            "location": "\\",
            "creator": "admin"
        }
        
        mock_server = AsyncMock()
        mock_server.add_safe.return_value = mock_response
        
        with patch('mcp_privilege_cloud.mcp_server.get_server', return_value=mock_server):
            result = await add_safe(safe_name)
            
            assert result == mock_response
            mock_server.add_safe.assert_called_once_with(safe_name=safe_name, description=None)

    @pytest.mark.asyncio
    async def test_update_safe_tool(self, mock_env_vars):
        """Test the update_safe MCP tool"""
        safe_id = "123"
        safe_name = "UpdatedSafeName"
        description = "Updated description"
        
        mock_response = {
            "safeId": safe_id,
            "safeName": safe_name,
            "description": description,
            "location": "\\",
            "numberOfDaysRetention": 30
        }
        
        mock_server = AsyncMock()
        mock_server.update_safe.return_value = mock_response
        
        with patch('mcp_privilege_cloud.mcp_server.get_server', return_value=mock_server):
            from mcp_privilege_cloud.mcp_server import update_safe
            result = await update_safe(safe_id, safe_name=safe_name, description=description)
            
            assert result == mock_response
            mock_server.update_safe.assert_called_once_with(
                safe_id=safe_id,
                safe_name=safe_name,
                description=description,
                location=None,
                number_of_days_retention=None,
                number_of_versions_retention=None,
                auto_purge_enabled=None,
                olac_enabled=None,
                managing_cpm=None
            )

    @pytest.mark.asyncio
    async def test_update_safe_tool_minimal(self, mock_env_vars):
        """Test the update_safe MCP tool with minimal parameters"""
        safe_id = "123"
        
        mock_response = {
            "safeId": safe_id,
            "safeName": "ExistingSafeName",
            "description": "Existing description",
            "location": "\\"
        }
        
        mock_server = AsyncMock()
        mock_server.update_safe.return_value = mock_response
        
        with patch('mcp_privilege_cloud.mcp_server.get_server', return_value=mock_server):
            from mcp_privilege_cloud.mcp_server import update_safe
            result = await update_safe(safe_id)
            
            assert result == mock_response
            mock_server.update_safe.assert_called_once_with(
                safe_id=safe_id,
                safe_name=None,
                description=None,
                location=None,
                number_of_days_retention=None,
                number_of_versions_retention=None,
                auto_purge_enabled=None,
                olac_enabled=None,
                managing_cpm=None
            )

    @pytest.mark.asyncio
    async def test_delete_safe_tool(self, mock_env_vars):
        """Test the delete_safe MCP tool"""
        safe_id = "123"
        
        mock_response = {
            "message": f"Safe {safe_id} deleted successfully",
            "safe_id": safe_id
        }
        
        mock_server = AsyncMock()
        mock_server.delete_safe.return_value = mock_response
        
        with patch('mcp_privilege_cloud.mcp_server.get_server', return_value=mock_server):
            from mcp_privilege_cloud.mcp_server import delete_safe
            result = await delete_safe(safe_id)
            
            assert result == mock_response
            mock_server.delete_safe.assert_called_once_with(safe_id=safe_id)

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
        
        mock_server = AsyncMock()
        mock_server.list_platforms.return_value = mock_platforms
        
        with patch('mcp_privilege_cloud.mcp_server.get_server', return_value=mock_server):
            result = await list_platforms()
            
            assert result == mock_platforms
            mock_server.list_platforms.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_account_tool(self, mock_env_vars):
        """Test the update_account MCP tool"""
        account_id = "123_456"
        update_data = {
            "name": "updated-account-name",
            "address": "updated-server.domain.com",
            "user_name": "updated_user",
            "platform_account_properties": {"Port": "2222"}
        }
        
        mock_response = {"id": account_id, **update_data, "updated": True}
        
        mock_server = AsyncMock()
        mock_server.update_account.return_value = mock_response
        
        with patch('mcp_privilege_cloud.mcp_server.get_server', return_value=mock_server):
            result = await update_account(account_id=account_id, **update_data)
            
            assert result == mock_response
            mock_server.update_account.assert_called_once_with(
                account_id=account_id,
                name=update_data["name"],
                address=update_data["address"],
                user_name=update_data["user_name"],
                platform_account_properties=update_data["platform_account_properties"],
                secret_management=None,
                remote_machines_access=None
            )

    @pytest.mark.asyncio
    async def test_update_account_tool_minimal(self, mock_env_vars):
        """Test the update_account MCP tool with minimal parameters"""
        account_id = "123_456"
        name = "minimal-update"
        
        mock_response = {"id": account_id, "name": name, "updated": True}
        
        mock_server = AsyncMock()
        mock_server.update_account.return_value = mock_response
        
        with patch('mcp_privilege_cloud.mcp_server.get_server', return_value=mock_server):
            result = await update_account(account_id=account_id, name=name)
            
            assert result == mock_response
            mock_server.update_account.assert_called_once_with(
                account_id=account_id,
                name=name,
                address=None,
                user_name=None,
                platform_account_properties=None,
                secret_management=None,
                remote_machines_access=None
            )

    @pytest.mark.asyncio
    async def test_delete_account_tool(self, mock_env_vars):
        """Test the delete_account MCP tool"""
        account_id = "123_456"
        
        mock_response = {"id": account_id, "deleted": True, "status": "success"}
        
        mock_server = AsyncMock()
        mock_server.delete_account.return_value = mock_response
        
        with patch('mcp_privilege_cloud.mcp_server.get_server', return_value=mock_server):
            result = await delete_account(account_id=account_id)
            
            assert result == mock_response
            mock_server.delete_account.assert_called_once_with(account_id=account_id)

    @pytest.mark.asyncio
    async def test_update_account_tool_error_handling(self, mock_env_vars):
        """Test update_account MCP tool handles errors properly"""
        mock_server = AsyncMock()
        mock_server.update_account.side_effect = ValueError("account_id is required")
        
        with patch('mcp_privilege_cloud.mcp_server.get_server', return_value=mock_server):
            with pytest.raises(ValueError, match="account_id is required"):
                await update_account(account_id="", name="test")

    @pytest.mark.asyncio
    async def test_delete_account_tool_error_handling(self, mock_env_vars):
        """Test delete_account MCP tool handles errors properly"""
        mock_server = AsyncMock()
        mock_server.delete_account.side_effect = ValueError("account_id is required")
        
        with patch('mcp_privilege_cloud.mcp_server.get_server', return_value=mock_server):
            with pytest.raises(ValueError, match="account_id is required"):
                await delete_account(account_id="")


@pytest.mark.integration
class TestMCPSafeMemberTools:
    """Test MCP safe member management tools"""

    @pytest.fixture
    def mock_env_vars(self):
        """Mock required environment variables"""
        with patch.dict('os.environ', {
            'CYBERARK_CLIENT_ID': 'test-client',
            'CYBERARK_CLIENT_SECRET': 'test-secret'
        }):
            yield

    @pytest.mark.asyncio
    async def test_list_safe_members_tool(self, mock_env_vars):
        """Test the list_safe_members MCP tool"""
        safe_name = "IT-Infrastructure"
        mock_members = [
            {
                "safeName": safe_name,
                "memberName": "admin@domain.com",
                "memberType": "User",
                "permissionSet": "Full"
            },
            {
                "safeName": safe_name,
                "memberName": "ReadOnlyUser",
                "memberType": "User", 
                "permissionSet": "ReadOnly"
            }
        ]
        
        mock_server = AsyncMock()
        mock_server.list_safe_members.return_value = mock_members
        
        with patch('mcp_privilege_cloud.mcp_server.get_server', return_value=mock_server):
            result = await list_safe_members(safe_name=safe_name)
            
            assert result == mock_members
            mock_server.list_safe_members.assert_called_once_with(
                safe_name=safe_name,
                search=None,
                sort=None,
                offset=None,
                limit=None,
                member_type=None
            )

    @pytest.mark.asyncio
    async def test_add_safe_member_tool(self, mock_env_vars):
        """Test the add_safe_member MCP tool"""
        safe_name = "IT-Infrastructure"
        member_name = "newuser@domain.com"
        member_type = "User"
        permission_set = "ReadOnly"
        
        mock_response = {
            "safeName": safe_name,
            "memberName": member_name,
            "memberType": member_type,
            "permissionSet": permission_set
        }
        
        mock_server = AsyncMock()
        mock_server.add_safe_member.return_value = mock_response
        
        with patch('mcp_privilege_cloud.mcp_server.get_server', return_value=mock_server):
            result = await add_safe_member(
                safe_name=safe_name,
                member_name=member_name,
                member_type=member_type,
                permission_set=permission_set
            )
            
            assert result == mock_response
            mock_server.add_safe_member.assert_called_once_with(
                safe_name=safe_name,
                member_name=member_name,
                member_type=member_type,
                search_in=None,
                membership_expiration_date=None,
                permissions=None,
                permission_set=permission_set
            )

    @pytest.mark.asyncio
    async def test_update_safe_member_tool(self, mock_env_vars):
        """Test the update_safe_member MCP tool"""
        safe_name = "IT-Infrastructure"
        member_name = "user@domain.com"
        permission_set = "AccountsManager"
        
        mock_response = {
            "safeName": safe_name,
            "memberName": member_name,
            "permissionSet": permission_set,
            "updated": True
        }
        
        mock_server = AsyncMock()
        mock_server.update_safe_member.return_value = mock_response
        
        with patch('mcp_privilege_cloud.mcp_server.get_server', return_value=mock_server):
            result = await update_safe_member(
                safe_name=safe_name,
                member_name=member_name,
                permission_set=permission_set
            )
            
            assert result == mock_response
            mock_server.update_safe_member.assert_called_once_with(
                safe_name=safe_name,
                member_name=member_name,
                search_in=None,
                membership_expiration_date=None,
                permissions=None,
                permission_set=permission_set
            )

    @pytest.mark.asyncio
    async def test_remove_safe_member_tool(self, mock_env_vars):
        """Test the remove_safe_member MCP tool"""
        safe_name = "IT-Infrastructure"
        member_name = "olduser@domain.com"
        
        mock_response = {
            "message": f"Member {member_name} removed from safe {safe_name} successfully",
            "safe_name": safe_name,
            "member_name": member_name
        }
        
        mock_server = AsyncMock()
        mock_server.remove_safe_member.return_value = mock_response
        
        with patch('mcp_privilege_cloud.mcp_server.get_server', return_value=mock_server):
            result = await remove_safe_member(safe_name=safe_name, member_name=member_name)
            
            assert result == mock_response
            mock_server.remove_safe_member.assert_called_once_with(
                safe_name=safe_name,
                member_name=member_name
            )

    async def test_get_platform_statistics_tool(self, mock_env_vars):
        """Test get_platform_statistics MCP tool integration"""
        # Import the tool function
        from mcp_privilege_cloud.mcp_server import get_platform_statistics
        
        mock_response = {
            "platforms_count": 15,
            "platforms_count_by_type": {
                "regular": 12,
                "rotational_group": 2,
                "group": 1
            }
        }
        
        mock_server = AsyncMock()
        mock_server.get_platform_statistics.return_value = mock_response
        
        with patch('mcp_privilege_cloud.mcp_server.get_server', return_value=mock_server):
            result = await get_platform_statistics()
            
            assert result == mock_response
            mock_server.get_platform_statistics.assert_called_once()

    async def test_get_target_platform_statistics_tool(self, mock_env_vars):
        """Test get_target_platform_statistics MCP tool integration"""
        # Import the tool function
        from mcp_privilege_cloud.mcp_server import get_target_platform_statistics
        
        mock_response = {
            "target_platforms_count": 8,
            "target_platforms_count_by_system_type": {
                "Windows": 3,
                "Unix": 2,
                "Oracle": 2,
                "Database": 1
            }
        }
        
        mock_server = AsyncMock()
        mock_server.get_target_platform_statistics.return_value = mock_response
        
        with patch('mcp_privilege_cloud.mcp_server.get_server', return_value=mock_server):
            result = await get_target_platform_statistics()
            
            assert result == mock_response
            mock_server.get_target_platform_statistics.assert_called_once()
