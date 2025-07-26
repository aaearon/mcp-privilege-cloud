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
        
        assert result == sample_accounts
        mock_service.list_accounts.assert_called_once_with(accounts_filter=None)

    async def test_list_accounts_with_safe_filter(self, server, sample_accounts):
        """Test listing accounts filtered by safe name"""
        filtered_accounts = [sample_accounts[0]]  # Only first account
        mock_service = self._setup_accounts_service_mock(server, filtered_accounts)
        
        result = await server.list_accounts(safe_name="IT-Infrastructure")
        
        assert result == filtered_accounts
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
        mock_accounts_service.search_accounts.return_value = [mock_page]
        server.accounts_service = mock_accounts_service
        
        result = await server.search_accounts(keywords="admin")
        
        assert result == sample_accounts
        mock_accounts_service.search_accounts.assert_called_once()

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
        mock_accounts_service.search_accounts.return_value = [mock_page]
        server.accounts_service = mock_accounts_service
        
        result = await server.search_accounts(
            keywords="admin",
            safe_name="IT-Infrastructure",
            username="admin"
        )
        
        assert result == filtered_accounts
        mock_accounts_service.search_accounts.assert_called_once()

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
            "platformId": "WindowsDomainAccount",
            "safeName": "Test-Safe",
            "userName": "testuser",
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
            "platformId": "WindowsDomainAccount", 
            "safeName": "Test-Safe",
            "userName": "testuser",
            "secret": "password123",
            "address": "server.domain.com",
            "platformAccountProperties": {"Port": "22"},
            "secretManagement": {
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
        mock_safes_service.get_safe.return_value = mock_safe
        server.safes_service = mock_safes_service
        
        result = await server.get_safe_details(safe_name)
        
        assert result == expected_safe
        mock_safes_service.get_safe.assert_called_once()