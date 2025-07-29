import pytest
import asyncio
from unittest.mock import Mock, patch
from typing import List, Dict, Any

from src.mcp_privilege_cloud.server import CyberArkMCPServer, CyberArkAPIError


@pytest.mark.integration
class TestAccountManagement:
    """Test cases for account management operations using SDK"""

    @pytest.fixture
    def server(self):
        """Create server instance for testing"""
        # Mock environment variables needed for SDK authentication - simplified
        with patch.dict('os.environ', {
            'CYBERARK_CLIENT_ID': 'test-client',
            'CYBERARK_CLIENT_SECRET': 'test-secret'
        }):
            # Mock the SDK components to prevent actual authentication during tests
            with patch('src.mcp_privilege_cloud.server.CyberArkSDKAuthenticator') as mock_sdk_auth_class:
                mock_sdk_auth = Mock()
                mock_sdk_auth.get_authenticated_client.return_value = Mock()
                mock_sdk_auth_class.from_environment.return_value = mock_sdk_auth
                
                # Create server with simplified constructor
                server = CyberArkMCPServer()
                
                # Mock the SDK services
                server.sdk_authenticator = mock_sdk_auth
                server._accounts_service = Mock()
                server._safes_service = Mock()
                server._platforms_service = Mock()
                
                yield server

    @pytest.fixture
    def sample_accounts(self):
        """Sample account data for testing"""
        return [
            {
                "id": "123_456", 
                "name": "admin-server01",
                "safeName": "IT-Infrastructure",
                "userName": "admin",
                "address": "server01.domain.com",
                "platformId": "WindowsDomainAccount",
                "secretType": "password"
            },
            {
                "id": "789_012",
                "name": "service-db01", 
                "safeName": "Database-Services",
                "userName": "dbservice",
                "address": "db01.domain.com",
                "platformId": "OracleAccount",
                "secretType": "password"
            }
        ]

    def _setup_accounts_service_mock(self, server, accounts_data):
        """Helper method to set up accounts service mock with proper SDK structure"""
        mock_page = Mock()
        mock_items = []
        for acc in accounts_data:
            mock_item = Mock()
            mock_item.model_dump.return_value = acc
            mock_items.append(mock_item)
        mock_page.items = mock_items
        
        mock_accounts_service = Mock()
        mock_accounts_service.list_accounts.return_value = [mock_page]
        server.accounts_service = mock_accounts_service
        return mock_accounts_service

    async def test_list_accounts_no_filters(self, server, sample_accounts):
        """Test listing all accounts without filters"""
        mock_service = self._setup_accounts_service_mock(server, sample_accounts)
        
        result = await server.list_accounts()
        
        # Convert Pydantic models to dicts for comparison
        result_dicts = [item.model_dump() for item in result]
        assert result_dicts == sample_accounts
        mock_service.list_accounts.assert_called_once_with(accounts_filter=None)

    async def test_list_accounts_with_safe_filter(self, server, sample_accounts):
        """Test listing accounts filtered by safe name"""
        filtered_accounts = [sample_accounts[0]]  # Only first account
        mock_service = self._setup_accounts_service_mock(server, filtered_accounts)
        
        result = await server.list_accounts(safe_name="IT-Infrastructure")
        
        # Convert Pydantic models to dicts for comparison
        result_dicts = [item.model_dump() for item in result]
        assert result_dicts == filtered_accounts
        # Verify that a filter was passed
        mock_service.list_accounts.assert_called_once()
        call_args = mock_service.list_accounts.call_args
        assert call_args[1]['accounts_filter'] is not None

    async def test_list_accounts_empty_response(self, server):
        """Test listing accounts when no accounts are found"""
        mock_service = self._setup_accounts_service_mock(server, [])
        
        result = await server.list_accounts()
        
        assert result == []
        mock_service.list_accounts.assert_called_once()

    async def test_search_accounts_basic(self, server, sample_accounts):
        """Test basic account search functionality"""
        # Mock the accounts service for search
        mock_page = Mock()
        mock_items = []
        for acc in sample_accounts:
            mock_item = Mock()
            mock_item.model_dump.return_value = acc
            mock_items.append(mock_item)
        mock_page.items = mock_items
        
        mock_accounts_service = Mock()
        mock_accounts_service.list_accounts.return_value = [mock_page]
        server.accounts_service = mock_accounts_service
        
        result = await server.search_accounts(query="admin")
        
        assert result == sample_accounts
        mock_accounts_service.list_accounts.assert_called_once()

    async def test_search_accounts_with_filters(self, server, sample_accounts):
        """Test account search with multiple filters"""
        filtered_accounts = [sample_accounts[0]]
        
        # Mock the accounts service for search
        mock_page = Mock()
        mock_items = []
        for acc in filtered_accounts:
            mock_item = Mock()
            mock_item.model_dump.return_value = acc
            mock_items.append(mock_item)
        mock_page.items = mock_items
        
        mock_accounts_service = Mock()
        mock_accounts_service.list_accounts.return_value = [mock_page]
        server.accounts_service = mock_accounts_service
        
        result = await server.search_accounts(
            query="admin",
            safe_name="IT-Infrastructure",
            username="admin"
        )
        
        assert result == filtered_accounts
        mock_accounts_service.list_accounts.assert_called_once()

    async def test_get_account_details(self, server, sample_accounts):
        """Test getting account details by ID"""
        account_id = "123_456"
        expected_account = sample_accounts[0]
        
        # Mock the accounts service for get account
        mock_account = Mock()
        mock_account.model_dump.return_value = expected_account
        
        mock_accounts_service = Mock()
        mock_accounts_service.get_account.return_value = mock_account
        server.accounts_service = mock_accounts_service
        
        result = await server.get_account_details(account_id)
        
        assert result == expected_account
        mock_accounts_service.get_account.assert_called_once_with(account_id=account_id)

    async def test_create_account_minimal(self, server):
        """Test creating account with minimal required fields"""
        account_data = {
            "name": "test-account",
            "platform_id": "WindowsDomainAccount",
            "safe_name": "Test-Safe",
            "user_name": "testuser",
            "secret": "password123"
        }
        
        expected_response = {"id": "new_123", **account_data}
        
        # Mock the accounts service for create account
        mock_account = Mock()
        mock_account.model_dump.return_value = expected_response
        
        mock_accounts_service = Mock()
        mock_accounts_service.add_account.return_value = mock_account
        server.accounts_service = mock_accounts_service
        
        result = await server.create_account(**account_data)
        
        assert result == expected_response
        mock_accounts_service.add_account.assert_called_once()

    async def test_create_account_complete(self, server):
        """Test creating account with all available fields"""
        account_data = {
            "name": "test-account-complete",
            "platform_id": "WindowsDomainAccount", 
            "safe_name": "Test-Safe",
            "user_name": "testuser",
            "secret": "password123",
            "address": "server.domain.com",
            "platform_account_properties": {"Port": "22"},
            "secret_management": {
                "automaticManagementEnabled": True,
                "manualManagementReason": "test"
            }
        }
        
        expected_response = {"id": "new_456", **account_data}
        
        # Mock the accounts service for create account
        mock_account = Mock()
        mock_account.model_dump.return_value = expected_response
        
        mock_accounts_service = Mock()
        mock_accounts_service.add_account.return_value = mock_account
        server.accounts_service = mock_accounts_service
        
        result = await server.create_account(**account_data)
        
        assert result == expected_response
        mock_accounts_service.add_account.assert_called_once()

    async def test_change_account_password(self, server):
        """Test changing account password"""
        account_id = "123_456"
        new_password = "newpassword123"
        
        expected_response = {"status": "success", "message": "Password changed"}
        
        # Mock the accounts service for change password
        mock_response = Mock()
        mock_response.model_dump.return_value = expected_response
        
        mock_accounts_service = Mock()
        mock_accounts_service.change_account_credentials.return_value = mock_response
        server.accounts_service = mock_accounts_service
        
        result = await server.change_account_password(
            account_id=account_id,
            new_password=new_password
        )
        
        assert result == expected_response
        mock_accounts_service.change_account_credentials.assert_called_once()

    async def test_verify_account_password(self, server):
        """Test verifying account password"""
        account_id = "123_456"
        
        expected_response = {"verified": True, "message": "Password verified"}
        
        # Mock the accounts service for verify password
        mock_response = Mock()
        mock_response.model_dump.return_value = expected_response
        
        mock_accounts_service = Mock()
        mock_accounts_service.verify_account_credentials.return_value = mock_response
        server.accounts_service = mock_accounts_service
        
        result = await server.verify_account_password(account_id=account_id)
        
        assert result == expected_response
        mock_accounts_service.verify_account_credentials.assert_called_once()

    async def test_set_next_password(self, server):
        """Test setting next password for account"""
        account_id = "123_456"
        next_password = "nextpassword123"
        
        expected_response = {"status": "success", "message": "Next password set"}
        
        # Mock the accounts service for set next password
        mock_response = Mock()
        mock_response.model_dump.return_value = expected_response
        
        mock_accounts_service = Mock()
        mock_accounts_service.set_account_next_credentials.return_value = mock_response
        server.accounts_service = mock_accounts_service
        
        result = await server.set_next_password(
            account_id=account_id,
            new_password=next_password
        )
        
        assert result == expected_response
        mock_accounts_service.set_account_next_credentials.assert_called_once()

    async def test_reconcile_account_password(self, server):
        """Test reconciling account password"""
        account_id = "123_456"
        
        expected_response = {"status": "success", "message": "Password reconciled"}
        
        # Mock the accounts service for reconcile password
        mock_response = Mock()
        mock_response.model_dump.return_value = expected_response
        
        mock_accounts_service = Mock()
        mock_accounts_service.reconcile_account_credentials.return_value = mock_response
        server.accounts_service = mock_accounts_service
        
        result = await server.reconcile_account_password(account_id=account_id)
        
        assert result == expected_response
        mock_accounts_service.reconcile_account_credentials.assert_called_once()

    async def test_concurrent_account_operations(self, server, sample_accounts):
        """Test concurrent account operations"""
        # Set up mocks for multiple operations
        mock_service = self._setup_accounts_service_mock(server, sample_accounts)
        
        # Run multiple operations concurrently
        tasks = [
            server.list_accounts(),
            server.list_accounts(safe_name="IT-Infrastructure"),
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Verify all operations completed
        assert len(results) == 2
        assert all(isinstance(result, list) for result in results)
        
        # Verify service was called multiple times
        assert mock_service.list_accounts.call_count >= 2

    async def test_account_service_error_handling(self, server):
        """Test error handling in account operations"""
        # Mock the accounts service to raise an exception
        mock_accounts_service = Mock()
        mock_accounts_service.list_accounts.side_effect = Exception("SDK Error")
        server.accounts_service = mock_accounts_service
        
        # Test that the exception is properly propagated
        with pytest.raises(Exception, match="SDK Error"):
            await server.list_accounts()

    async def test_update_account_success(self, server):
        """Test updating an existing account"""
        account_id = "123_456"
        update_data = {
            "name": "updated-account-name",
            "address": "updated-server.domain.com",
            "user_name": "updated_user",
            "platform_account_properties": {"Port": "2222"}
        }
        
        expected_response = {"id": account_id, **update_data, "updated": True}
        
        # Mock the accounts service for update account
        mock_response = Mock()
        mock_response.model_dump.return_value = expected_response
        
        mock_accounts_service = Mock()
        mock_accounts_service.update_account.return_value = mock_response
        server.accounts_service = mock_accounts_service
        
        result = await server.update_account(account_id=account_id, **update_data)
        
        assert result == expected_response
        mock_accounts_service.update_account.assert_called_once()
        
        # Verify the call was made with ArkPCloudUpdateAccount model
        call_args = mock_accounts_service.update_account.call_args
        assert call_args[1]['account_id'] == account_id
        assert 'update_account' in call_args[1]

    async def test_update_account_minimal_data(self, server):
        """Test updating account with minimal data"""
        account_id = "123_456"
        update_data = {"name": "new-name-only"}
        
        expected_response = {"id": account_id, "name": "new-name-only", "updated": True}
        
        # Mock the accounts service
        mock_response = Mock()
        mock_response.model_dump.return_value = expected_response
        
        mock_accounts_service = Mock()
        mock_accounts_service.update_account.return_value = mock_response
        server.accounts_service = mock_accounts_service
        
        result = await server.update_account(account_id=account_id, **update_data)
        
        assert result == expected_response
        mock_accounts_service.update_account.assert_called_once()

    async def test_update_account_error_handling(self, server):
        """Test error handling in update account operation"""
        account_id = "123_456"
        
        # Mock the accounts service to raise an exception
        mock_accounts_service = Mock()
        mock_accounts_service.update_account.side_effect = Exception("Update failed")
        server.accounts_service = mock_accounts_service
        
        # Test that the exception is properly propagated
        with pytest.raises(Exception, match="Update failed"):
            await server.update_account(account_id=account_id, name="test")

    async def test_delete_account_success(self, server):
        """Test deleting an existing account"""
        account_id = "123_456"
        
        expected_response = {"id": account_id, "deleted": True, "status": "success"}
        
        # Mock the accounts service for delete account
        mock_response = Mock()
        mock_response.model_dump.return_value = expected_response
        
        mock_accounts_service = Mock()
        mock_accounts_service.delete_account.return_value = mock_response
        server.accounts_service = mock_accounts_service
        
        result = await server.delete_account(account_id=account_id)
        
        assert result == expected_response
        mock_accounts_service.delete_account.assert_called_once()
        
        # Verify the call was made with correct account_id and ArkPCloudDeleteAccount model
        call_args = mock_accounts_service.delete_account.call_args
        assert call_args[1]['account_id'] == account_id
        assert 'delete_account' in call_args[1]

    async def test_delete_account_error_handling(self, server):
        """Test error handling in delete account operation"""
        account_id = "123_456"
        
        # Mock the accounts service to raise an exception
        mock_accounts_service = Mock()
        mock_accounts_service.delete_account.side_effect = Exception("Delete failed")
        server.accounts_service = mock_accounts_service
        
        # Test that the exception is properly propagated
        with pytest.raises(Exception, match="Delete failed"):
            await server.delete_account(account_id=account_id)

    async def test_update_delete_operations_validation(self, server):
        """Test parameter validation for update and delete operations"""
        # Mock the accounts service to avoid initialization issues
        mock_accounts_service = Mock()
        server.accounts_service = mock_accounts_service
        
        # Test update with empty account_id
        with pytest.raises(ValueError, match="account_id is required"):
            await server.update_account(account_id="", name="test")
        
        # Test delete with empty account_id
        with pytest.raises(ValueError, match="account_id is required"):
            await server.delete_account(account_id="")

    async def test_update_account_comprehensive_data(self, server):
        """Test updating account with comprehensive data"""
        account_id = "123_456"
        comprehensive_update = {
            "name": "comprehensive-test-account",
            "address": "comprehensive.server.domain.com",
            "user_name": "comprehensive_user",
            "platform_account_properties": {
                "Port": "3389",
                "LogonDomain": "CORPORATE"
            },
            "secret_management": {
                "automaticManagementEnabled": False,
                "manualManagementReason": "Security policy requirement"
            },
            "remote_machines_access": {
                "remoteMachines": "server1.corp.com;server2.corp.com",
                "restrictMachineAccessToList": True
            }
        }
        
        expected_response = {"id": account_id, **comprehensive_update, "updated": True}
        
        # Mock the accounts service
        mock_response = Mock()
        mock_response.model_dump.return_value = expected_response
        
        mock_accounts_service = Mock()
        mock_accounts_service.update_account.return_value = mock_response
        server.accounts_service = mock_accounts_service
        
        result = await server.update_account(account_id=account_id, **comprehensive_update)
        
        assert result == expected_response
        mock_accounts_service.update_account.assert_called_once()


@pytest.mark.integration
class TestSafeManagement:
    """Test cases for safe management operations using SDK"""

    @pytest.fixture
    def server(self):
        """Create server instance for testing"""
        # Mock environment variables needed for SDK authentication - simplified
        with patch.dict('os.environ', {
            'CYBERARK_CLIENT_ID': 'test-client',
            'CYBERARK_CLIENT_SECRET': 'test-secret'
        }):
            # Mock the SDK components to prevent actual authentication during tests
            with patch('src.mcp_privilege_cloud.server.CyberArkSDKAuthenticator') as mock_sdk_auth_class:
                mock_sdk_auth = Mock()
                mock_sdk_auth.get_authenticated_client.return_value = Mock()
                mock_sdk_auth_class.from_environment.return_value = mock_sdk_auth
                
                server = CyberArkMCPServer()
                
                # Mock the SDK services
                server.sdk_authenticator = mock_sdk_auth
                server._accounts_service = Mock()
                server._safes_service = Mock()
                server._platforms_service = Mock()
                
                yield server

    @pytest.fixture
    def sample_safes(self):
        """Sample safe data for testing"""
        return [
            {
                "safeName": "IT-Infrastructure",
                "safeNumber": 15,
                "description": "IT Infrastructure Safe",
                "location": "\\IT\\",
                "creator": "admin",
                "numberOfVersionsRetention": 7
            },
            {
                "safeName": "Database-Services", 
                "safeNumber": 20,
                "description": "Database Services Safe",
                "location": "\\DB\\",
                "creator": "dbadmin",
                "numberOfVersionsRetention": 10
            }
        ]

    async def test_list_safes_basic(self, server, sample_safes):
        """Test basic safe listing functionality"""
        # Mock SDK response structure for safes
        mock_page = Mock()
        mock_items = []
        for safe in sample_safes:
            mock_item = Mock()
            mock_item.model_dump.return_value = safe
            mock_items.append(mock_item)
        mock_page.items = mock_items
        
        mock_safes_service = Mock()
        mock_safes_service.list_safes.return_value = [mock_page]
        server.safes_service = mock_safes_service
        
        result = await server.list_safes()
        
        assert result == sample_safes
        mock_safes_service.list_safes.assert_called_once()

    async def test_list_safes_with_search(self, server, sample_safes):
        """Test safe listing with search parameter"""
        # Return only matching safes
        filtered_safes = [sample_safes[0]]  # Only IT-Infrastructure
        
        mock_page = Mock()
        mock_items = []
        for safe in filtered_safes:
            mock_item = Mock()
            mock_item.model_dump.return_value = safe
            mock_items.append(mock_item)
        mock_page.items = mock_items
        
        mock_safes_service = Mock()
        mock_safes_service.list_safes.return_value = [mock_page]
        server.safes_service = mock_safes_service
        
        result = await server.list_safes(search="IT")
        
        assert result == filtered_safes
        mock_safes_service.list_safes.assert_called_once()

    async def test_get_safe_details(self, server, sample_safes):
        """Test getting safe details by name"""
        safe_name = "IT-Infrastructure"
        expected_safe = sample_safes[0]
        
        # Mock the safes service for get safe
        mock_safe = Mock()
        mock_safe.model_dump.return_value = expected_safe
        
        mock_safes_service = Mock()
        mock_safes_service.safe.return_value = mock_safe
        server.safes_service = mock_safes_service
        
        result = await server.get_safe_details(safe_name)
        
        assert result == expected_safe
        mock_safes_service.safe.assert_called_once()

    async def test_add_safe_minimal_fields(self, server):
        """Test creating a safe with minimal required fields"""
        safe_name = "TestSafeMinimal"
        description = None
        
        # Mock successful safe creation response
        expected_response = {
            "safeName": safe_name,
            "safeId": "123",
            "description": "",
            "location": "\\",
            "creator": "admin",
            "isExpiredMembersAutoOlationEnabled": False
        }
        
        mock_safe = Mock()
        mock_safe.model_dump.return_value = expected_response
        
        mock_safes_service = Mock()
        mock_safes_service.add_safe.return_value = mock_safe
        server.safes_service = mock_safes_service
        
        result = await server.add_safe(safe_name, description)
        
        assert result == expected_response
        mock_safes_service.add_safe.assert_called_once()
        call_args = mock_safes_service.add_safe.call_args[1]['safe']
        assert call_args.safe_name == safe_name
        assert call_args.description == description

    async def test_add_safe_with_description(self, server):
        """Test creating a safe with description"""
        safe_name = "TestSafeWithDesc"
        description = "A test safe with description"
        
        # Mock successful safe creation response
        expected_response = {
            "safeName": safe_name,
            "safeId": "124",
            "description": description,
            "location": "\\",
            "creator": "admin",
            "isExpiredMembersAutoOlationEnabled": False
        }
        
        mock_safe = Mock()
        mock_safe.model_dump.return_value = expected_response
        
        mock_safes_service = Mock()
        mock_safes_service.add_safe.return_value = mock_safe
        server.safes_service = mock_safes_service
        
        result = await server.add_safe(safe_name, description)
        
        assert result == expected_response
        mock_safes_service.add_safe.assert_called_once()
        call_args = mock_safes_service.add_safe.call_args[1]['safe']
        assert call_args.safe_name == safe_name
        assert call_args.description == description

    async def test_add_safe_already_exists_error(self, server):
        """Test error handling when safe already exists"""
        safe_name = "ExistingSafe"
        
        # Mock API error for duplicate safe
        from src.mcp_privilege_cloud.exceptions import CyberArkAPIError
        mock_safes_service = Mock()
        mock_safes_service.add_safe.side_effect = CyberArkAPIError(
            "Safe already exists", 
            status_code=409
        )
        server.safes_service = mock_safes_service
        
        with pytest.raises(CyberArkAPIError, match="Safe already exists"):
            await server.add_safe(safe_name)

    async def test_add_safe_permission_denied_error(self, server):
        """Test error handling for insufficient permissions"""
        safe_name = "RestrictedSafe"
        
        # Mock API error for insufficient permissions
        from src.mcp_privilege_cloud.exceptions import CyberArkAPIError
        mock_safes_service = Mock()
        mock_safes_service.add_safe.side_effect = CyberArkAPIError(
            "Insufficient permissions to create safe",
            status_code=403
        )
        server.safes_service = mock_safes_service
        
        with pytest.raises(CyberArkAPIError, match="Insufficient permissions"):
            await server.add_safe(safe_name)

    # Update Safe Tests
    async def test_update_safe_minimal_fields(self, server):
        """Test updating a safe with minimal required fields"""
        safe_id = "123"
        safe_name = "UpdatedSafeName"
        
        # Mock successful safe update response
        expected_response = {
            "safeId": safe_id,
            "safeName": safe_name,
            "description": "Original description",
            "location": "\\",
            "creator": "admin",
            "isExpiredMembersAutoOlationEnabled": False
        }
        
        mock_safe = Mock()
        mock_safe.model_dump.return_value = expected_response
        
        mock_safes_service = Mock()
        mock_safes_service.update_safe.return_value = mock_safe
        server.safes_service = mock_safes_service
        
        result = await server.update_safe(safe_id, safe_name=safe_name)
        
        assert result == expected_response
        mock_safes_service.update_safe.assert_called_once()
        call_args = mock_safes_service.update_safe.call_args[1]['update_safe']
        assert call_args.safe_id == safe_id
        assert call_args.safe_name == safe_name

    async def test_update_safe_all_fields(self, server):
        """Test updating a safe with all available fields"""
        safe_id = "123"
        safe_name = "UpdatedSafeName"
        description = "Updated description"
        location = "\\UpdatedLocation"
        number_of_days_retention = 30
        number_of_versions_retention = 5
        auto_purge_enabled = True
        olac_enabled = True
        managing_cpm = "UpdatedCPM"
        
        # Mock successful safe update response
        expected_response = {
            "safeId": safe_id,
            "safeName": safe_name,
            "description": description,
            "location": location,
            "numberOfDaysRetention": number_of_days_retention,
            "numberOfVersionsRetention": number_of_versions_retention,
            "autoPurgeEnabled": auto_purge_enabled,
            "olacEnabled": olac_enabled,
            "managingCpm": managing_cpm
        }
        
        mock_safe = Mock()
        mock_safe.model_dump.return_value = expected_response
        
        mock_safes_service = Mock()
        mock_safes_service.update_safe.return_value = mock_safe
        server.safes_service = mock_safes_service
        
        result = await server.update_safe(
            safe_id=safe_id,
            safe_name=safe_name,
            description=description,
            location=location,
            number_of_days_retention=number_of_days_retention,
            number_of_versions_retention=number_of_versions_retention,
            auto_purge_enabled=auto_purge_enabled,
            olac_enabled=olac_enabled,
            managing_cpm=managing_cpm
        )
        
        assert result == expected_response
        mock_safes_service.update_safe.assert_called_once()
        call_args = mock_safes_service.update_safe.call_args[1]['update_safe']
        assert call_args.safe_id == safe_id
        assert call_args.safe_name == safe_name
        assert call_args.description == description
        assert call_args.location == location
        assert call_args.number_of_days_retention == number_of_days_retention
        assert call_args.number_of_versions_retention == number_of_versions_retention
        assert call_args.auto_purge_enabled == auto_purge_enabled
        assert call_args.olac_enabled == olac_enabled
        assert call_args.managing_cpm == managing_cpm

    async def test_update_safe_partial_fields(self, server):
        """Test updating a safe with only some fields provided"""
        safe_id = "123"
        description = "Only updating description"
        auto_purge_enabled = False
        
        # Mock successful safe update response
        expected_response = {
            "safeId": safe_id,
            "safeName": "OriginalName",
            "description": description,
            "autoPurgeEnabled": auto_purge_enabled
        }
        
        mock_safe = Mock()
        mock_safe.model_dump.return_value = expected_response
        
        mock_safes_service = Mock()
        mock_safes_service.update_safe.return_value = mock_safe
        server.safes_service = mock_safes_service
        
        result = await server.update_safe(
            safe_id=safe_id,
            description=description,
            auto_purge_enabled=auto_purge_enabled
        )
        
        assert result == expected_response
        mock_safes_service.update_safe.assert_called_once()
        call_args = mock_safes_service.update_safe.call_args[1]['update_safe']
        assert call_args.safe_id == safe_id
        assert call_args.description == description
        assert call_args.auto_purge_enabled == auto_purge_enabled
        # Ensure only provided fields are included
        assert not hasattr(call_args, 'safe_name') or call_args.safe_name is None

    async def test_update_safe_not_found_error(self, server):
        """Test error handling for safe not found"""
        safe_id = "nonexistent"
        
        # Mock API error for safe not found
        from src.mcp_privilege_cloud.exceptions import CyberArkAPIError
        mock_safes_service = Mock()
        mock_safes_service.update_safe.side_effect = CyberArkAPIError(
            "Safe not found",
            status_code=404
        )
        server.safes_service = mock_safes_service
        
        with pytest.raises(CyberArkAPIError, match="Safe not found"):
            await server.update_safe(safe_id, safe_name="NewName")

    async def test_update_safe_permission_denied_error(self, server):
        """Test error handling for insufficient permissions"""
        safe_id = "restricted"
        
        # Mock API error for insufficient permissions
        from src.mcp_privilege_cloud.exceptions import CyberArkAPIError
        mock_safes_service = Mock()
        mock_safes_service.update_safe.side_effect = CyberArkAPIError(
            "Insufficient permissions to update safe",
            status_code=403
        )
        server.safes_service = mock_safes_service
        
        with pytest.raises(CyberArkAPIError, match="Insufficient permissions"):
            await server.update_safe(safe_id, safe_name="NewName")

    # Delete Safe Tests
    async def test_delete_safe_success(self, server):
        """Test successful safe deletion"""
        safe_id = "123"
        
        # Mock successful safe deletion (SDK returns None)
        mock_safes_service = Mock()
        mock_safes_service.delete_safe.return_value = None
        server.safes_service = mock_safes_service
        
        result = await server.delete_safe(safe_id)
        
        expected_response = {
            "message": f"Safe {safe_id} deleted successfully",
            "safe_id": safe_id
        }
        assert result == expected_response
        mock_safes_service.delete_safe.assert_called_once()
        call_args = mock_safes_service.delete_safe.call_args[1]['delete_safe']
        assert call_args.safe_id == safe_id

    async def test_delete_safe_not_found_error(self, server):
        """Test error handling for safe not found during deletion"""
        safe_id = "nonexistent"
        
        # Mock API error for safe not found
        from src.mcp_privilege_cloud.exceptions import CyberArkAPIError
        mock_safes_service = Mock()
        mock_safes_service.delete_safe.side_effect = CyberArkAPIError(
            "Safe not found",
            status_code=404
        )
        server.safes_service = mock_safes_service
        
        with pytest.raises(CyberArkAPIError, match="Safe not found"):
            await server.delete_safe(safe_id)

    async def test_delete_safe_permission_denied_error(self, server):
        """Test error handling for insufficient permissions during deletion"""
        safe_id = "restricted"
        
        # Mock API error for insufficient permissions
        from src.mcp_privilege_cloud.exceptions import CyberArkAPIError
        mock_safes_service = Mock()
        mock_safes_service.delete_safe.side_effect = CyberArkAPIError(
            "Insufficient permissions to delete safe",
            status_code=403
        )
        server.safes_service = mock_safes_service
        
        with pytest.raises(CyberArkAPIError, match="Insufficient permissions"):
            await server.delete_safe(safe_id)

    async def test_delete_safe_dependency_error(self, server):
        """Test error handling for safe with dependencies that cannot be deleted"""
        safe_id = "safe_with_accounts"
        
        # Mock API error for safe with dependencies
        from src.mcp_privilege_cloud.exceptions import CyberArkAPIError
        mock_safes_service = Mock()
        mock_safes_service.delete_safe.side_effect = CyberArkAPIError(
            "Safe contains accounts and cannot be deleted",
            status_code=400
        )
        server.safes_service = mock_safes_service
        
        with pytest.raises(CyberArkAPIError, match="Safe contains accounts"):
            await server.delete_safe(safe_id)


class TestSafeMemberManagement:
    """Test cases for safe member management operations"""

    @pytest.fixture
    def server(self):
        """Create server instance for testing"""
        # Mock environment variables needed for SDK authentication - simplified
        with patch.dict('os.environ', {
            'CYBERARK_CLIENT_ID': 'test-client',
            'CYBERARK_CLIENT_SECRET': 'test-secret'
        }):
            # Mock the SDK components to prevent actual authentication during tests
            with patch('src.mcp_privilege_cloud.server.CyberArkSDKAuthenticator') as mock_sdk_auth_class:
                mock_sdk_auth = Mock()
                mock_sdk_auth.get_authenticated_client.return_value = Mock()
                mock_sdk_auth_class.from_environment.return_value = mock_sdk_auth
                
                server = CyberArkMCPServer()
                
                # Mock the SDK services
                server.sdk_authenticator = mock_sdk_auth
                server.accounts_service = Mock()
                server.safes_service = Mock()
                server.platforms_service = Mock()
                
                yield server

    @pytest.fixture
    def sample_safe_members(self):
        """Sample safe members for testing"""
        return [
            {
                "safeName": "IT-Infrastructure",
                "memberName": "admin@domain.com",
                "memberType": "User",
                "membershipExpirationDate": None,
                "isExpiredMemberAutomaticallyDisabled": False,
                "isPredefinedUser": False,
                "permissions": {
                    "listAccounts": True,
                    "useAccounts": True,
                    "retrieveAccounts": True,
                    "addAccounts": True,
                    "updateAccountProperties": True,
                    "updateAccountContent": True,
                    "initiateCPMAccountManagementOperations": True,
                    "specifyNextAccountContent": True,
                    "renameAccounts": True,
                    "deleteAccounts": True,
                    "unlockAccounts": True,
                    "viewSafeMembers": True,
                    "manageSafeMembers": True,
                    "viewAuditLog": True,
                    "accessWithoutConfirmation": True,
                    "requestsAuthorizationLevel1": True,
                    "manageSafe": True,
                    "backupSafe": True,
                    "moveAccountsAndFolders": True,
                    "createFolders": True,
                    "deleteFolders": True
                },
                "permissionSet": "Full"
            },
            {
                "safeName": "IT-Infrastructure", 
                "memberName": "ReadOnlyUser",
                "memberType": "User",
                "membershipExpirationDate": None,
                "isExpiredMemberAutomaticallyDisabled": False,
                "isPredefinedUser": False,
                "permissions": {
                    "listAccounts": True,
                    "useAccounts": True,
                    "retrieveAccounts": True,
                    "addAccounts": False,
                    "updateAccountProperties": False,
                    "updateAccountContent": False,
                    "initiateCPMAccountManagementOperations": False,
                    "specifyNextAccountContent": False,
                    "renameAccounts": False,
                    "deleteAccounts": False,
                    "unlockAccounts": False,
                    "viewSafeMembers": False,
                    "manageSafeMembers": False,
                    "viewAuditLog": False,
                    "accessWithoutConfirmation": False,
                    "requestsAuthorizationLevel1": False,
                    "manageSafe": False,
                    "backupSafe": False,
                    "moveAccountsAndFolders": False,
                    "createFolders": False,
                    "deleteFolders": False
                },
                "permissionSet": "ReadOnly"
            },
            {
                "safeName": "IT-Infrastructure",
                "memberName": "ApproverGroup",
                "memberType": "Group", 
                "membershipExpirationDate": None,
                "isExpiredMemberAutomaticallyDisabled": False,
                "isPredefinedUser": False,
                "permissions": {
                    "listAccounts": True,
                    "useAccounts": False,
                    "retrieveAccounts": False,
                    "addAccounts": False,
                    "updateAccountProperties": False,
                    "updateAccountContent": False,
                    "initiateCPMAccountManagementOperations": False,
                    "specifyNextAccountContent": False,
                    "renameAccounts": False,
                    "deleteAccounts": False,
                    "unlockAccounts": False,
                    "viewSafeMembers": True,
                    "manageSafeMembers": True,
                    "viewAuditLog": False,
                    "accessWithoutConfirmation": False,
                    "requestsAuthorizationLevel1": True,
                    "manageSafe": False,
                    "backupSafe": False,
                    "moveAccountsAndFolders": False,
                    "createFolders": False,
                    "deleteFolders": False
                },
                "permissionSet": "Approver"
            }
        ]

    async def test_list_safe_members_basic(self, server, sample_safe_members):
        """Test basic safe member listing functionality"""
        safe_name = "IT-Infrastructure"
        
        # Mock SDK response structure for safe members
        mock_page = Mock()
        mock_items = []
        for member in sample_safe_members:
            mock_item = Mock()
            mock_item.model_dump.return_value = member
            mock_items.append(mock_item)
        mock_page.items = mock_items
        
        mock_safes_service = Mock()
        mock_safes_service.list_safe_members.return_value = [mock_page]
        server.safes_service = mock_safes_service
        
        result = await server.list_safe_members(safe_name)
        
        assert result == sample_safe_members
        mock_safes_service.list_safe_members.assert_called_once()

    async def test_list_safe_members_with_filters(self, server, sample_safe_members):
        """Test safe member listing with member type filter"""
        safe_name = "IT-Infrastructure"
        member_type = "User"
        
        # Return only user members
        filtered_members = [m for m in sample_safe_members if m["memberType"] == "User"]
        
        mock_page = Mock()
        mock_items = []
        for member in filtered_members:
            mock_item = Mock()
            mock_item.model_dump.return_value = member
            mock_items.append(mock_item)
        mock_page.items = mock_items
        
        mock_safes_service = Mock()
        mock_safes_service.list_safe_members_by.return_value = [mock_page]
        server.safes_service = mock_safes_service
        
        result = await server.list_safe_members(safe_name, member_type=member_type)
        
        assert result == filtered_members
        mock_safes_service.list_safe_members_by.assert_called_once()

    async def test_get_safe_member_details(self, server, sample_safe_members):
        """Test getting details of a specific safe member"""
        safe_name = "IT-Infrastructure"
        member_name = "admin@domain.com"
        expected_member = sample_safe_members[0]
        
        # Mock the safes service for get safe member - server method returns Pydantic model
        mock_member = Mock()
        mock_member.model_dump.return_value = expected_member
        
        mock_safes_service = Mock()
        mock_safes_service.safe_member.return_value = mock_member
        server.safes_service = mock_safes_service
        
        result = await server.get_safe_member_details(safe_name, member_name)
        
        # Server method returns Pydantic model, not dictionary
        assert result == mock_member
        mock_safes_service.safe_member.assert_called_once()

    async def test_add_safe_member_with_permission_set(self, server):
        """Test adding a safe member with predefined permission set"""
        safe_name = "IT-Infrastructure"
        member_name = "newuser@domain.com"
        member_type = "User"
        permission_set = "ReadOnly"
        
        # Mock successful member addition response
        expected_response = {
            "safeName": safe_name,
            "memberName": member_name,
            "memberType": member_type,
            "permissionSet": permission_set,
            "membershipExpirationDate": None,
            "isExpiredMemberAutomaticallyDisabled": False,
            "isPredefinedUser": False
        }
        
        mock_member = Mock()
        mock_member.model_dump.return_value = expected_response
        
        mock_safes_service = Mock()
        mock_safes_service.add_safe_member.return_value = mock_member
        server.safes_service = mock_safes_service
        
        result = await server.add_safe_member(
            safe_name=safe_name,
            member_name=member_name,
            member_type=member_type,
            permission_set=permission_set
        )
        
        # Server method returns Pydantic model, not dictionary
        assert result == mock_member
        mock_safes_service.add_safe_member.assert_called_once()

    async def test_add_safe_member_with_custom_permissions(self, server):
        """Test adding a safe member with custom permissions"""
        safe_name = "IT-Infrastructure"
        member_name = "customuser@domain.com"
        member_type = "User"
        custom_permissions = {
            "listAccounts": True,
            "useAccounts": True,
            "retrieveAccounts": False,
            "addAccounts": False,
            "updateAccountProperties": False,
            "updateAccountContent": False
        }
        
        # Mock successful member addition response
        expected_response = {
            "safeName": safe_name,
            "memberName": member_name,
            "memberType": member_type,
            "permissions": custom_permissions,
            "permissionSet": "Custom"
        }
        
        mock_member = Mock()
        mock_member.model_dump.return_value = expected_response
        
        mock_safes_service = Mock()
        mock_safes_service.add_safe_member.return_value = mock_member
        server.safes_service = mock_safes_service
        
        result = await server.add_safe_member(
            safe_name=safe_name,
            member_name=member_name,
            member_type=member_type,
            permissions=custom_permissions
        )
        
        # Server method returns Pydantic model, not dictionary
        assert result == mock_member
        mock_safes_service.add_safe_member.assert_called_once()

    async def test_update_safe_member_permissions(self, server):
        """Test updating safe member permissions"""
        safe_name = "IT-Infrastructure"
        member_name = "admin@domain.com"
        new_permission_set = "AccountsManager"
        
        # Mock successful member update response
        expected_response = {
            "safeName": safe_name,
            "memberName": member_name,
            "memberType": "User",
            "permissionSet": new_permission_set,
            "permissions": {
                "listAccounts": True,
                "useAccounts": True,
                "retrieveAccounts": True,
                "addAccounts": True,
                "updateAccountProperties": True,
                "updateAccountContent": True,
                "initiateCPMAccountManagementOperations": True,
                "specifyNextAccountContent": True,
                "renameAccounts": True,
                "deleteAccounts": True,
                "unlockAccounts": True,
                "viewSafeMembers": True,
                "manageSafeMembers": True,
                "viewAuditLog": True,
                "accessWithoutConfirmation": True
            }
        }
        
        mock_member = Mock()
        mock_member.model_dump.return_value = expected_response
        
        mock_safes_service = Mock()
        mock_safes_service.update_safe_member.return_value = mock_member
        server.safes_service = mock_safes_service
        
        result = await server.update_safe_member(
            safe_name=safe_name,
            member_name=member_name,
            permission_set=new_permission_set
        )
        
        # Server method returns Pydantic model, not dictionary
        assert result == mock_member
        mock_safes_service.update_safe_member.assert_called_once()

    async def test_remove_safe_member(self, server):
        """Test removing a member from a safe"""
        safe_name = "IT-Infrastructure"
        member_name = "usertoremove@domain.com"
        
        mock_safes_service = Mock()
        mock_safes_service.delete_safe_member.return_value = None
        server.safes_service = mock_safes_service
        
        result = await server.remove_safe_member(safe_name, member_name)
        
        expected_response = {
            "message": f"Member {member_name} removed from safe {safe_name} successfully",
            "safe_name": safe_name,
            "member_name": member_name
        }
        assert result == expected_response
        mock_safes_service.delete_safe_member.assert_called_once()

    async def test_add_safe_member_already_exists_error(self, server):
        """Test error handling for adding duplicate safe member"""
        safe_name = "IT-Infrastructure"
        member_name = "existinguser@domain.com"
        member_type = "User"
        
        # Mock API error for member already exists
        from src.mcp_privilege_cloud.exceptions import CyberArkAPIError
        mock_safes_service = Mock()
        mock_safes_service.add_safe_member.side_effect = CyberArkAPIError(
            "Member already exists in safe",
            status_code=409
        )
        server.safes_service = mock_safes_service
        
        with pytest.raises(CyberArkAPIError, match="Member already exists"):
            await server.add_safe_member(safe_name, member_name, member_type)

    async def test_update_safe_member_not_found_error(self, server):
        """Test error handling for updating non-existent safe member"""
        safe_name = "IT-Infrastructure"
        member_name = "nonexistentuser@domain.com"
        
        # Mock API error for member not found
        from src.mcp_privilege_cloud.exceptions import CyberArkAPIError
        mock_safes_service = Mock()
        mock_safes_service.update_safe_member.side_effect = CyberArkAPIError(
            "Member not found in safe",
            status_code=404
        )
        server.safes_service = mock_safes_service
        
        with pytest.raises(CyberArkAPIError, match="Member not found"):
            await server.update_safe_member(safe_name, member_name)

    async def test_remove_safe_member_not_found_error(self, server):
        """Test error handling for removing non-existent safe member"""
        safe_name = "IT-Infrastructure"
        member_name = "nonexistentuser@domain.com"
        
        # Mock API error for member not found
        from src.mcp_privilege_cloud.exceptions import CyberArkAPIError
        mock_safes_service = Mock()
        mock_safes_service.delete_safe_member.side_effect = CyberArkAPIError(
            "Member not found in safe",
            status_code=404
        )
        server.safes_service = mock_safes_service
        
        with pytest.raises(CyberArkAPIError, match="Member not found"):
            await server.remove_safe_member(safe_name, member_name)

    async def test_add_safe_member_permission_denied_error(self, server):
        """Test error handling for insufficient permissions to add safe member"""
        safe_name = "IT-Infrastructure"
        member_name = "newuser@domain.com"
        member_type = "User"
        
        # Mock API error for insufficient permissions
        from src.mcp_privilege_cloud.exceptions import CyberArkAPIError
        mock_safes_service = Mock()
        mock_safes_service.add_safe_member.side_effect = CyberArkAPIError(
            "Insufficient permissions to add member to safe",
            status_code=403
        )
        server.safes_service = mock_safes_service
        
        with pytest.raises(CyberArkAPIError, match="Insufficient permissions"):
            await server.add_safe_member(safe_name, member_name, member_type)


@pytest.mark.integration
class TestAdvancedAccountSearch:
    """Test cases for advanced account search and filtering capabilities"""

    @pytest.fixture
    def server(self):
        """Create server instance for testing"""
        with patch.dict('os.environ', {
            'CYBERARK_CLIENT_ID': 'test-client',
            'CYBERARK_CLIENT_SECRET': 'test-secret'
        }):
            with patch('src.mcp_privilege_cloud.server.CyberArkSDKAuthenticator') as mock_sdk_auth_class:
                mock_sdk_auth = Mock()
                mock_sdk_auth.get_authenticated_client.return_value = Mock()
                mock_sdk_auth_class.from_environment.return_value = mock_sdk_auth
                
                server = CyberArkMCPServer()
                server.sdk_authenticator = mock_sdk_auth
                server._accounts_service = Mock()
                server._safes_service = Mock()
                server._platforms_service = Mock()
                
                yield server

    @pytest.fixture
    def diverse_accounts(self):
        """Sample diverse account data for advanced filtering tests"""
        return [
            {
                "id": "123_456", 
                "name": "admin-web01",
                "safeName": "Web-Servers",
                "userName": "admin",
                "address": "web01.production.com",
                "platformId": "WindowsDomainAccount",
                "secretType": "password",
                "platformAccountProperties": {"Port": "3389"},
                "secretManagement": {"automaticManagementEnabled": True}
            },
            {
                "id": "789_012",
                "name": "service-db01", 
                "safeName": "Database-Servers",
                "userName": "sqlservice",
                "address": "db01.production.com",
                "platformId": "SQLServerAccount",
                "secretType": "password",
                "platformAccountProperties": {"Port": "1433"},
                "secretManagement": {"automaticManagementEnabled": False}
            },
            {
                "id": "345_678",
                "name": "admin-app01",
                "safeName": "Application-Servers", 
                "userName": "admin",
                "address": "app01.staging.com",
                "platformId": "LinuxAccount",
                "secretType": "key",
                "platformAccountProperties": {"Port": "22"},
                "secretManagement": {"automaticManagementEnabled": True}
            },
            {
                "id": "901_234",
                "name": "backup-web02",
                "safeName": "Web-Servers",
                "userName": "backup",
                "address": "web02.production.com", 
                "platformId": "WindowsDomainAccount",
                "secretType": "password",
                "platformAccountProperties": {"Port": "3389"},
                "secretManagement": {"automaticManagementEnabled": False}
            }
        ]

    def _setup_accounts_service_mock(self, server, return_accounts):
        """Helper to set up accounts service mock"""
        mock_page = Mock()
        # Create a separate mock for each account with proper closure
        mock_items = []
        for acc in return_accounts:
            mock_account = Mock()
            mock_account.model_dump = lambda account=acc: account  # Capture account in closure
            mock_items.append(mock_account)
        mock_page.items = mock_items
        
        mock_service = Mock()
        mock_service.list_accounts.return_value = [mock_page]
        server.accounts_service = mock_service
        return mock_service

    async def test_filter_accounts_by_platform_group(self, server, diverse_accounts):
        """Test filtering accounts by platform type grouping"""
        # Mock service should return ALL accounts, filtering happens in server logic
        mock_service = self._setup_accounts_service_mock(server, diverse_accounts)
        
        result = await server.filter_accounts_by_platform_group("Windows")
        
        assert len(result) == 2
        assert all("WindowsDomainAccount" in acc["platformId"] for acc in result)
        mock_service.list_accounts.assert_called_once()

    async def test_filter_accounts_by_environment(self, server, diverse_accounts):
        """Test filtering accounts by environment (production vs staging)"""
        # Mock service should return ALL accounts, filtering happens in server logic
        mock_service = self._setup_accounts_service_mock(server, diverse_accounts)
        
        result = await server.filter_accounts_by_environment("production")
        
        assert len(result) == 3
        assert all("production" in acc["address"] for acc in result)
        mock_service.list_accounts.assert_called_once()

    async def test_filter_accounts_by_management_status(self, server, diverse_accounts):
        """Test filtering accounts by automatic management status"""
        # Mock service should return ALL accounts, filtering happens in server logic
        mock_service = self._setup_accounts_service_mock(server, diverse_accounts)
        
        result = await server.filter_accounts_by_management_status(auto_managed=True)
        
        assert len(result) == 2
        assert all(acc["secretManagement"]["automaticManagementEnabled"] for acc in result)
        mock_service.list_accounts.assert_called_once()

    async def test_group_accounts_by_safe(self, server, diverse_accounts):
        """Test grouping accounts by safe name"""
        mock_service = self._setup_accounts_service_mock(server, diverse_accounts)
        
        result = await server.group_accounts_by_safe()
        
        assert "Web-Servers" in result
        assert "Database-Servers" in result
        assert "Application-Servers" in result
        assert len(result["Web-Servers"]) == 2
        assert len(result["Database-Servers"]) == 1
        assert len(result["Application-Servers"]) == 1
        mock_service.list_accounts.assert_called_once()

    async def test_group_accounts_by_platform(self, server, diverse_accounts):
        """Test grouping accounts by platform type"""
        mock_service = self._setup_accounts_service_mock(server, diverse_accounts)
        
        result = await server.group_accounts_by_platform()
        
        assert "WindowsDomainAccount" in result
        assert "SQLServerAccount" in result
        assert "LinuxAccount" in result
        assert len(result["WindowsDomainAccount"]) == 2
        assert len(result["SQLServerAccount"]) == 1
        assert len(result["LinuxAccount"]) == 1
        mock_service.list_accounts.assert_called_once()

    async def test_analyze_account_distribution(self, server, diverse_accounts):
        """Test account distribution analysis"""
        mock_service = self._setup_accounts_service_mock(server, diverse_accounts)
        
        result = await server.analyze_account_distribution()
        
        assert "total_accounts" in result
        assert "by_safe" in result
        assert "by_platform" in result
        assert "by_environment" in result
        assert "auto_managed_percentage" in result
        assert result["total_accounts"] == 4
        mock_service.list_accounts.assert_called_once()

    async def test_search_accounts_by_pattern(self, server, diverse_accounts):
        """Test searching accounts using multiple criteria patterns"""
        # Mock service should return ALL accounts, filtering happens in server logic
        mock_service = self._setup_accounts_service_mock(server, diverse_accounts)
        
        result = await server.search_accounts_by_pattern(
            username_pattern="admin",
            environment="production"
        )
        
        # Should find admin accounts in production environment
        assert len(result) == 1  # Only admin-web01 matches both criteria
        assert all("admin" in acc["userName"] for acc in result)
        assert all("production" in acc["address"] for acc in result)
        mock_service.list_accounts.assert_called_once()

    async def test_count_accounts_by_criteria(self, server, diverse_accounts):
        """Test counting accounts by various criteria"""
        mock_service = self._setup_accounts_service_mock(server, diverse_accounts)
        
        result = await server.count_accounts_by_criteria()
        
        assert "total" in result
        assert "by_platform" in result
        assert "by_safe" in result
        assert "auto_managed" in result
        assert "manual_managed" in result
        assert result["total"] == 4
        assert result["auto_managed"] == 2
        assert result["manual_managed"] == 2
        mock_service.list_accounts.assert_called_once()

    async def test_advanced_account_search_error_handling(self, server):
        """Test error handling for advanced search methods"""
        from src.mcp_privilege_cloud.exceptions import CyberArkAPIError
        
        mock_service = Mock()
        mock_service.list_accounts.side_effect = CyberArkAPIError("API Error", status_code=500)
        server.accounts_service = mock_service
        
        with pytest.raises(CyberArkAPIError):
            await server.filter_accounts_by_platform_group("Windows")

    async def test_filter_accounts_empty_result(self, server):
        """Test filtering accounts with no matches"""
        mock_service = self._setup_accounts_service_mock(server, [])
        
        result = await server.filter_accounts_by_environment("nonexistent")
        
        assert result == []
        mock_service.list_accounts.assert_called_once()