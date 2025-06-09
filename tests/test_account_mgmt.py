import pytest
from unittest.mock import Mock, AsyncMock, patch
from typing import List, Dict, Any

from src.cyberark_mcp.server import CyberArkMCPServer, CyberArkAPIError
from src.cyberark_mcp.auth import CyberArkAuthenticator


class TestAccountManagement:
    """Test cases for account management operations"""

    @pytest.fixture
    def mock_authenticator(self):
        """Mock authenticator for testing"""
        auth = Mock(spec=CyberArkAuthenticator)
        auth.get_auth_header = AsyncMock(return_value={"Authorization": "Bearer test-token"})
        return auth

    @pytest.fixture
    def server(self, mock_authenticator):
        """Create server instance for testing"""
        return CyberArkMCPServer(
            authenticator=mock_authenticator,
            subdomain="test-subdomain",
            timeout=30
        )

    @pytest.fixture
    def sample_accounts(self):
        """Sample account data for testing"""
        return [
            {
                "id": "123_456", 
                "name": "admin-server01",
                "safeName": "IT-Infrastructure",
                "userName": "admin",
                "address": "server01.example.com",
                "platformId": "WindowsDomainAccount",
                "secretType": "password"
            },
            {
                "id": "789_012",
                "name": "database-admin", 
                "safeName": "Database-Safes",
                "userName": "dbadmin",
                "address": "db01.example.com",
                "platformId": "MySQLAccount",
                "secretType": "password"
            }
        ]

    @pytest.fixture
    def sample_account_detail(self):
        """Sample detailed account data for testing"""
        return {
            "id": "123_456",
            "name": "admin-server01",
            "safeName": "IT-Infrastructure", 
            "userName": "admin",
            "address": "server01.example.com",
            "platformId": "WindowsDomainAccount",
            "secretType": "password",
            "platformAccountProperties": {
                "LogonDomain": "EXAMPLE",
                "Port": "3389"
            },
            "secretManagement": {
                "automaticManagementEnabled": True,
                "lastModifiedTime": "2025-01-06T10:30:00Z"
            },
            "createdTime": "2025-01-01T09:00:00Z"
        }

    async def test_list_accounts_no_filters(self, server, sample_accounts):
        """Test listing all accounts without filters"""
        mock_response = {"value": sample_accounts}
        
        with patch.object(server, '_make_api_request', return_value=mock_response) as mock_request:
            result = await server.list_accounts()
            
            assert result == sample_accounts
            mock_request.assert_called_once_with("GET", "Accounts", params={})

    async def test_list_accounts_with_safe_filter(self, server, sample_accounts):
        """Test listing accounts filtered by safe name"""
        filtered_accounts = [sample_accounts[0]]  # Only first account
        mock_response = {"value": filtered_accounts}
        
        with patch.object(server, '_make_api_request', return_value=mock_response) as mock_request:
            result = await server.list_accounts(safe_name="IT-Infrastructure")
            
            assert result == filtered_accounts
            mock_request.assert_called_once_with(
                "GET", "Accounts", params={"safeName": "IT-Infrastructure"}
            )

    async def test_list_accounts_with_multiple_filters(self, server, sample_accounts):
        """Test listing accounts with multiple filters"""
        mock_response = {"value": sample_accounts}
        
        with patch.object(server, '_make_api_request', return_value=mock_response) as mock_request:
            result = await server.list_accounts(
                safe_name="IT-Infrastructure",
                username="admin",
                address="server01.example.com"
            )
            
            assert result == sample_accounts
            expected_params = {
                "safeName": "IT-Infrastructure",
                "userName": "admin", 
                "address": "server01.example.com"
            }
            mock_request.assert_called_once_with("GET", "Accounts", params=expected_params)

    async def test_list_accounts_empty_response(self, server):
        """Test listing accounts when no accounts are found"""
        mock_response = {"value": []}
        
        with patch.object(server, '_make_api_request', return_value=mock_response):
            result = await server.list_accounts()
            
            assert result == []

    async def test_list_accounts_api_error(self, server):
        """Test listing accounts when API returns an error"""
        with patch.object(server, '_make_api_request', side_effect=CyberArkAPIError("API Error")):
            with pytest.raises(CyberArkAPIError, match="API Error"):
                await server.list_accounts()

    async def test_get_account_details_success(self, server, sample_account_detail):
        """Test getting account details successfully"""
        account_id = "123_456"
        
        with patch.object(server, '_make_api_request', return_value=sample_account_detail) as mock_request:
            result = await server.get_account_details(account_id)
            
            assert result == sample_account_detail
            mock_request.assert_called_once_with("GET", f"Accounts/{account_id}")

    async def test_get_account_details_not_found(self, server):
        """Test getting account details for non-existent account"""
        account_id = "nonexistent"
        
        with patch.object(server, '_make_api_request', side_effect=CyberArkAPIError("Account not found")):
            with pytest.raises(CyberArkAPIError, match="Account not found"):
                await server.get_account_details(account_id)

    async def test_search_accounts_with_keywords(self, server, sample_accounts):
        """Test searching accounts with keywords"""
        mock_response = {"value": sample_accounts}
        
        with patch.object(server, '_make_api_request', return_value=mock_response) as mock_request:
            result = await server.search_accounts(keywords="admin")
            
            assert result == sample_accounts
            mock_request.assert_called_once_with(
                "GET", "Accounts", params={"search": "admin"}
            )

    async def test_search_accounts_with_all_filters(self, server, sample_accounts):
        """Test searching accounts with all possible filters"""
        mock_response = {"value": sample_accounts}
        
        with patch.object(server, '_make_api_request', return_value=mock_response) as mock_request:
            result = await server.search_accounts(
                keywords="admin",
                safe_name="IT-Infrastructure", 
                username="admin",
                address="server01.example.com",
                platform_id="WindowsDomainAccount"
            )
            
            assert result == sample_accounts
            expected_params = {
                "search": "admin",
                "safeName": "IT-Infrastructure",
                "userName": "admin",
                "address": "server01.example.com", 
                "platformId": "WindowsDomainAccount"
            }
            mock_request.assert_called_once_with("GET", "Accounts", params=expected_params)

    async def test_search_accounts_no_results(self, server):
        """Test searching accounts with no results"""
        mock_response = {"value": []}
        
        with patch.object(server, '_make_api_request', return_value=mock_response):
            result = await server.search_accounts(keywords="nonexistent")
            
            assert result == []

    async def test_search_accounts_additional_params(self, server, sample_accounts):
        """Test searching accounts with additional keyword arguments"""
        mock_response = {"value": sample_accounts}
        
        with patch.object(server, '_make_api_request', return_value=mock_response) as mock_request:
            result = await server.search_accounts(
                keywords="admin",
                limit=50,
                offset=0
            )
            
            assert result == sample_accounts
            expected_params = {
                "search": "admin",
                "limit": 50,
                "offset": 0
            }
            mock_request.assert_called_once_with("GET", "Accounts", params=expected_params)

    async def test_account_operations_logging(self, server, sample_accounts, caplog):
        """Test that account operations generate appropriate log messages"""
        import logging
        
        mock_response = {"value": sample_accounts}
        
        with patch.object(server, '_make_api_request', return_value=mock_response):
            with caplog.at_level(logging.INFO):
                await server.list_accounts(safe_name="test-safe")
                
                # Check that appropriate log message was generated
                assert "Listing accounts with filters" in caplog.text
                assert "test-safe" in caplog.text

    async def test_account_detail_logging(self, server, sample_account_detail, caplog):
        """Test that getting account details generates appropriate log messages"""
        import logging
        
        account_id = "123_456"
        
        with patch.object(server, '_make_api_request', return_value=sample_account_detail):
            with caplog.at_level(logging.INFO):
                await server.get_account_details(account_id)
                
                # Check that appropriate log message was generated
                assert f"Getting details for account ID: {account_id}" in caplog.text

    async def test_search_accounts_logging(self, server, sample_accounts, caplog):
        """Test that searching accounts generates appropriate log messages"""
        import logging
        
        mock_response = {"value": sample_accounts}
        
        with patch.object(server, '_make_api_request', return_value=mock_response):
            with caplog.at_level(logging.INFO):
                await server.search_accounts(keywords="admin", safe_name="test-safe")
                
                # Check that appropriate log message was generated
                assert "Searching accounts with criteria" in caplog.text
                assert "admin" in caplog.text
                assert "test-safe" in caplog.text

    async def test_concurrent_account_operations(self, server, sample_accounts, sample_account_detail):
        """Test concurrent account operations"""
        import asyncio
        
        mock_list_response = {"value": sample_accounts}
        
        def mock_request_side_effect(method, endpoint, params=None):
            if endpoint == "Accounts":
                return mock_list_response
            elif endpoint == "Accounts/123_456":
                return sample_account_detail
            else:
                raise ValueError(f"Unexpected endpoint: {endpoint}")
        
        with patch.object(server, '_make_api_request', side_effect=mock_request_side_effect):
            # Run multiple operations concurrently
            tasks = [
                server.list_accounts(),
                server.get_account_details("123_456"),
                server.search_accounts(keywords="admin")
            ]
            
            results = await asyncio.gather(*tasks)
            
            assert len(results) == 3
            assert results[0] == sample_accounts  # list_accounts
            assert results[1] == sample_account_detail  # get_account_details
            assert results[2] == sample_accounts  # search_accounts

    async def test_account_operations_with_network_error(self, server):
        """Test account operations handle network errors appropriately"""
        import httpx
        
        # Mock the _make_api_request to raise a network error
        with patch.object(server, '_make_api_request', side_effect=CyberArkAPIError("Network error")):
            with pytest.raises(CyberArkAPIError, match="Network error"):
                await server.list_accounts()
            
            with pytest.raises(CyberArkAPIError, match="Network error"):
                await server.get_account_details("123")
                
            with pytest.raises(CyberArkAPIError, match="Network error"):
                await server.search_accounts(keywords="test")

    async def test_account_response_without_value_field(self, server):
        """Test handling API responses that don't have the expected 'value' field"""
        # Some endpoints might return data directly without wrapping in 'value'
        mock_response = {"accounts": []}  # Different structure
        
        with patch.object(server, '_make_api_request', return_value=mock_response):
            result = await server.list_accounts()
            # Should return empty list when 'value' field is missing
            assert result == []

    # CREATE ACCOUNT TESTS
    @pytest.fixture
    def minimal_account_data(self):
        """Minimal required data for creating an account"""
        return {
            "platformId": "WinServerLocal",
            "safeName": "IT-Infrastructure"
        }

    @pytest.fixture
    def complete_account_data(self):
        """Complete account data for testing full functionality"""
        return {
            "name": "admin-server01",
            "address": "server01.example.com",
            "userName": "admin",
            "platformId": "WinServerLocal", 
            "safeName": "IT-Infrastructure",
            "secretType": "password",
            "secret": "SecurePassword123!",
            "platformAccountProperties": {
                "LogonDomain": "EXAMPLE",
                "Port": "3389"
            },
            "secretManagement": {
                "automaticManagementEnabled": True,
                "manualManagementReason": ""
            },
            "remoteMachinesAccess": {
                "remoteMachines": "server1.example.com;server2.example.com",
                "accessRestrictedToRemoteMachines": True
            }
        }

    @pytest.fixture
    def created_account_response(self):
        """Sample response for successfully created account"""
        return {
            "id": "123_456",
            "name": "admin-server01",
            "address": "server01.example.com", 
            "userName": "admin",
            "platformId": "WinServerLocal",
            "safeName": "IT-Infrastructure",
            "secretType": "password",
            "platformAccountProperties": {
                "LogonDomain": "EXAMPLE",
                "Port": "3389"
            },
            "secretManagement": {
                "automaticManagementEnabled": True,
                "status": "succeeded",
                "lastModifiedDateTime": "2025-06-09T10:30:00Z"
            },
            "remoteMachinesAccess": {
                "remoteMachines": "server1.example.com;server2.example.com",
                "accessRestrictedToRemoteMachines": True
            },
            "createdDateTime": "2025-06-09T10:30:00Z"
        }

    async def test_create_account_minimal_required_fields(self, server, minimal_account_data, created_account_response):
        """Test creating account with only required fields"""
        expected_response = {
            "id": "123_456",
            "platformId": "WinServerLocal",
            "safeName": "IT-Infrastructure", 
            "secretManagement": {
                "automaticManagementEnabled": True
            },
            "createdDateTime": "2025-06-09T10:30:00Z"
        }
        
        with patch.object(server, '_make_api_request', return_value=expected_response) as mock_request:
            result = await server.create_account(
                platform_id=minimal_account_data["platformId"],
                safe_name=minimal_account_data["safeName"]
            )
            
            assert result == expected_response
            mock_request.assert_called_once_with("POST", "Accounts", json=minimal_account_data)

    async def test_create_account_complete_data(self, server, complete_account_data, created_account_response):
        """Test creating account with all optional fields"""
        with patch.object(server, '_make_api_request', return_value=created_account_response) as mock_request:
            result = await server.create_account(
                name=complete_account_data["name"],
                address=complete_account_data["address"],
                user_name=complete_account_data["userName"],
                platform_id=complete_account_data["platformId"],
                safe_name=complete_account_data["safeName"],
                secret_type=complete_account_data["secretType"],
                secret=complete_account_data["secret"],
                platform_account_properties=complete_account_data["platformAccountProperties"],
                secret_management=complete_account_data["secretManagement"],
                remote_machines_access=complete_account_data["remoteMachinesAccess"]
            )
            
            assert result == created_account_response
            mock_request.assert_called_once_with("POST", "Accounts", json=complete_account_data)

    async def test_create_account_missing_platform_id(self, server):
        """Test creating account without required platformId fails validation"""
        with pytest.raises(ValueError, match="platformId is required"):
            await server.create_account(platform_id="", safe_name="IT-Infrastructure")

    async def test_create_account_missing_safe_name(self, server):
        """Test creating account without required safeName fails validation"""
        with pytest.raises(ValueError, match="safeName is required"):
            await server.create_account(platform_id="WinServerLocal", safe_name="")

    async def test_create_account_invalid_secret_type(self, server, minimal_account_data):
        """Test creating account with invalid secretType"""
        with pytest.raises(ValueError, match="secretType must be 'password' or 'key'"):
            await server.create_account(
                platform_id=minimal_account_data["platformId"],
                safe_name=minimal_account_data["safeName"],
                secret_type="invalid"
            )

    async def test_create_account_special_characters_validation(self, server, minimal_account_data):
        """Test creating account with special characters in name fails validation"""
        with pytest.raises(ValueError, match="Account name contains invalid characters"):
            await server.create_account(
                platform_id=minimal_account_data["platformId"],
                safe_name=minimal_account_data["safeName"],
                name="invalid/name:with*special?chars"
            )

    async def test_create_account_with_ssh_key(self, server, minimal_account_data, created_account_response):
        """Test creating account with SSH key secret type"""
        ssh_key = "-----BEGIN OPENSSH PRIVATE KEY-----\ntest-key-content\n-----END OPENSSH PRIVATE KEY-----"
        
        expected_response = {
            **created_account_response,
            "secretType": "key",
            "userName": "ubuntu"
        }
        
        expected_api_call = {
            **minimal_account_data,
            "secretType": "key",
            "secret": ssh_key,
            "userName": "ubuntu"
        }
        
        with patch.object(server, '_make_api_request', return_value=expected_response) as mock_request:
            result = await server.create_account(
                platform_id=minimal_account_data["platformId"],
                safe_name=minimal_account_data["safeName"],
                secret_type="key",
                secret=ssh_key,
                user_name="ubuntu"
            )
            
            assert result == expected_response
            assert result["secretType"] == "key"
            mock_request.assert_called_once_with("POST", "Accounts", json=expected_api_call)

    async def test_create_account_with_platform_properties(self, server, minimal_account_data, created_account_response):
        """Test creating account with platform-specific properties"""
        account_data = {
            **minimal_account_data,
            "platformAccountProperties": {
                "LogonDomain": "CORPORATE",
                "Port": "22",
                "Location": "DataCenter1"
            }
        }
        
        with patch.object(server, '_make_api_request', return_value=created_account_response) as mock_request:
            result = await server.create_account(**account_data)
            
            assert result == created_account_response
            mock_request.assert_called_once_with("POST", "Accounts", json=account_data)

    async def test_create_account_with_manual_secret_management(self, server, minimal_account_data, created_account_response):
        """Test creating account with manual secret management"""
        account_data = {
            **minimal_account_data,
            "secretManagement": {
                "automaticManagementEnabled": False,
                "manualManagementReason": "Legacy system compatibility"
            }
        }
        
        expected_response = {
            **created_account_response,
            "secretManagement": {
                "automaticManagementEnabled": False,
                "manualManagementReason": "Legacy system compatibility"
            }
        }
        
        with patch.object(server, '_make_api_request', return_value=expected_response) as mock_request:
            result = await server.create_account(**account_data)
            
            assert result == expected_response
            assert result["secretManagement"]["automaticManagementEnabled"] is False
            mock_request.assert_called_once_with("POST", "Accounts", json=account_data)

    async def test_create_account_with_remote_machines_access(self, server, minimal_account_data, created_account_response):
        """Test creating account with remote machine access restrictions"""
        account_data = {
            **minimal_account_data,
            "remoteMachinesAccess": {
                "remoteMachines": "web01.example.com;web02.example.com;db01.example.com",
                "accessRestrictedToRemoteMachines": True
            }
        }
        
        with patch.object(server, '_make_api_request', return_value=created_account_response) as mock_request:
            result = await server.create_account(**account_data)
            
            assert result == created_account_response
            mock_request.assert_called_once_with("POST", "Accounts", json=account_data)

    async def test_create_account_api_permission_error(self, server, minimal_account_data):
        """Test creating account with insufficient permissions"""
        with patch.object(server, '_make_api_request', side_effect=CyberArkAPIError("Insufficient permissions")):
            with pytest.raises(CyberArkAPIError, match="Insufficient permissions"):
                await server.create_account(**minimal_account_data)

    async def test_create_account_duplicate_account_error(self, server, minimal_account_data):
        """Test creating account that already exists"""
        with patch.object(server, '_make_api_request', side_effect=CyberArkAPIError("Account already exists")):
            with pytest.raises(CyberArkAPIError, match="Account already exists"):
                await server.create_account(**minimal_account_data)

    async def test_create_account_invalid_platform_error(self, server, minimal_account_data):
        """Test creating account with non-existent platform"""
        account_data = {**minimal_account_data, "platformId": "NonExistentPlatform"}
        
        with patch.object(server, '_make_api_request', side_effect=CyberArkAPIError("Platform not found")):
            with pytest.raises(CyberArkAPIError, match="Platform not found"):
                await server.create_account(**account_data)

    async def test_create_account_invalid_safe_error(self, server, minimal_account_data):
        """Test creating account in non-existent safe"""
        account_data = {**minimal_account_data, "safeName": "NonExistentSafe"}
        
        with patch.object(server, '_make_api_request', side_effect=CyberArkAPIError("Safe not found")):
            with pytest.raises(CyberArkAPIError, match="Safe not found"):
                await server.create_account(**account_data)

    async def test_create_account_network_error(self, server, minimal_account_data):
        """Test creating account with network connectivity issues"""
        with patch.object(server, '_make_api_request', side_effect=CyberArkAPIError("Network error")):
            with pytest.raises(CyberArkAPIError, match="Network error"):
                await server.create_account(**minimal_account_data)

    async def test_create_account_logging(self, server, minimal_account_data, created_account_response, caplog):
        """Test that account creation generates appropriate log messages"""
        import logging
        
        with patch.object(server, '_make_api_request', return_value=created_account_response):
            with caplog.at_level(logging.INFO):
                await server.create_account(**minimal_account_data)
                
                # Check that appropriate log message was generated
                assert "Creating account in safe" in caplog.text
                assert "IT-Infrastructure" in caplog.text
                assert "WinServerLocal" in caplog.text

    async def test_create_account_parameter_sanitization(self, server, minimal_account_data):
        """Test that None and empty parameters are properly handled"""
        account_data = {
            **minimal_account_data,
            "name": "",
            "address": None,
            "userName": "",
            "secret": None
        }
        
        # Mock to capture the actual request data
        expected_clean_data = {
            "platformId": "WinServerLocal",
            "safeName": "IT-Infrastructure"
        }
        
        with patch.object(server, '_make_api_request', return_value={"id": "123"}) as mock_request:
            await server.create_account(**account_data)
            
            # Verify that empty/None values were filtered out
            called_args = mock_request.call_args
            actual_json = called_args[1]['json']
            
            # Should only contain non-empty values
            assert "name" not in actual_json or actual_json.get("name") != ""
            assert "address" not in actual_json
            assert "userName" not in actual_json or actual_json.get("userName") != ""
            assert "secret" not in actual_json

    async def test_create_account_concurrent_creation(self, server, minimal_account_data, created_account_response):
        """Test concurrent account creation operations"""
        import asyncio
        
        account_data_1 = {**minimal_account_data, "userName": "admin1"}
        account_data_2 = {**minimal_account_data, "userName": "admin2"}
        
        response_1 = {**created_account_response, "id": "123_1", "userName": "admin1"}
        response_2 = {**created_account_response, "id": "123_2", "userName": "admin2"}
        
        def mock_request_side_effect(method, endpoint, json=None):
            if json and json.get("userName") == "admin1":
                return response_1
            elif json and json.get("userName") == "admin2":
                return response_2
            else:
                return created_account_response
        
        with patch.object(server, '_make_api_request', side_effect=mock_request_side_effect):
            # Run account creations concurrently
            tasks = [
                server.create_account(**account_data_1),
                server.create_account(**account_data_2)
            ]
            
            results = await asyncio.gather(*tasks)
            
            assert len(results) == 2
            assert results[0]["id"] == "123_1"
            assert results[1]["id"] == "123_2"
            assert results[0]["userName"] == "admin1"
            assert results[1]["userName"] == "admin2"