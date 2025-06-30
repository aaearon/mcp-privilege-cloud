import pytest
import asyncio
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
        platform_properties = {
            "LogonDomain": "CORPORATE",
            "Port": "22",
            "Location": "DataCenter1"
        }
        
        expected_api_call = {
            **minimal_account_data,
            "platformAccountProperties": platform_properties
        }
        
        with patch.object(server, '_make_api_request', return_value=created_account_response) as mock_request:
            result = await server.create_account(
                platform_id=minimal_account_data["platformId"],
                safe_name=minimal_account_data["safeName"],
                platform_account_properties=platform_properties
            )
            
            assert result == created_account_response
            mock_request.assert_called_once_with("POST", "Accounts", json=expected_api_call)

    async def test_create_account_with_manual_secret_management(self, server, minimal_account_data, created_account_response):
        """Test creating account with manual secret management"""
        secret_mgmt = {
            "automaticManagementEnabled": False,
            "manualManagementReason": "Legacy system compatibility"
        }
        
        expected_response = {
            **created_account_response,
            "secretManagement": secret_mgmt
        }
        
        expected_api_call = {
            **minimal_account_data,
            "secretManagement": secret_mgmt
        }
        
        with patch.object(server, '_make_api_request', return_value=expected_response) as mock_request:
            result = await server.create_account(
                platform_id=minimal_account_data["platformId"],
                safe_name=minimal_account_data["safeName"],
                secret_management=secret_mgmt
            )
            
            assert result == expected_response
            assert result["secretManagement"]["automaticManagementEnabled"] is False
            mock_request.assert_called_once_with("POST", "Accounts", json=expected_api_call)

    async def test_create_account_with_remote_machines_access(self, server, minimal_account_data, created_account_response):
        """Test creating account with remote machine access restrictions"""
        remote_access = {
            "remoteMachines": "web01.example.com;web02.example.com;db01.example.com",
            "accessRestrictedToRemoteMachines": True
        }
        
        expected_api_call = {
            **minimal_account_data,
            "remoteMachinesAccess": remote_access
        }
        
        with patch.object(server, '_make_api_request', return_value=created_account_response) as mock_request:
            result = await server.create_account(
                platform_id=minimal_account_data["platformId"],
                safe_name=minimal_account_data["safeName"],
                remote_machines_access=remote_access
            )
            
            assert result == created_account_response
            mock_request.assert_called_once_with("POST", "Accounts", json=expected_api_call)

    async def test_create_account_api_permission_error(self, server, minimal_account_data):
        """Test creating account with insufficient permissions"""
        with patch.object(server, '_make_api_request', side_effect=CyberArkAPIError("Insufficient permissions")):
            with pytest.raises(CyberArkAPIError, match="Insufficient permissions"):
                await server.create_account(
                    platform_id=minimal_account_data["platformId"],
                    safe_name=minimal_account_data["safeName"]
                )

    async def test_create_account_duplicate_account_error(self, server, minimal_account_data):
        """Test creating account that already exists"""
        with patch.object(server, '_make_api_request', side_effect=CyberArkAPIError("Account already exists")):
            with pytest.raises(CyberArkAPIError, match="Account already exists"):
                await server.create_account(
                    platform_id=minimal_account_data["platformId"],
                    safe_name=minimal_account_data["safeName"]
                )

    async def test_create_account_invalid_platform_error(self, server, minimal_account_data):
        """Test creating account with non-existent platform"""
        with patch.object(server, '_make_api_request', side_effect=CyberArkAPIError("Platform not found")):
            with pytest.raises(CyberArkAPIError, match="Platform not found"):
                await server.create_account(
                    platform_id="NonExistentPlatform",
                    safe_name=minimal_account_data["safeName"]
                )

    async def test_create_account_invalid_safe_error(self, server, minimal_account_data):
        """Test creating account in non-existent safe"""
        with patch.object(server, '_make_api_request', side_effect=CyberArkAPIError("Safe not found")):
            with pytest.raises(CyberArkAPIError, match="Safe not found"):
                await server.create_account(
                    platform_id=minimal_account_data["platformId"],
                    safe_name="NonExistentSafe"
                )

    async def test_create_account_network_error(self, server, minimal_account_data):
        """Test creating account with network connectivity issues"""
        with patch.object(server, '_make_api_request', side_effect=CyberArkAPIError("Network error")):
            with pytest.raises(CyberArkAPIError, match="Network error"):
                await server.create_account(
                    platform_id=minimal_account_data["platformId"],
                    safe_name=minimal_account_data["safeName"]
                )

    async def test_create_account_logging(self, server, minimal_account_data, created_account_response, caplog):
        """Test that account creation generates appropriate log messages"""
        import logging
        
        with patch.object(server, '_make_api_request', return_value=created_account_response):
            with caplog.at_level(logging.INFO):
                await server.create_account(
                    platform_id=minimal_account_data["platformId"],
                    safe_name=minimal_account_data["safeName"]
                )
                
                # Check that appropriate log message was generated
                assert "Creating account in safe" in caplog.text
                assert "IT-Infrastructure" in caplog.text
                assert "WinServerLocal" in caplog.text

    async def test_create_account_parameter_sanitization(self, server, minimal_account_data):
        """Test that None and empty parameters are properly handled"""
        with patch.object(server, '_make_api_request', return_value={"id": "123"}) as mock_request:
            await server.create_account(
                platform_id=minimal_account_data["platformId"],
                safe_name=minimal_account_data["safeName"],
                name="",
                address=None,
                user_name="",
                secret=None
            )
            
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
                server.create_account(
                    platform_id=minimal_account_data["platformId"],
                    safe_name=minimal_account_data["safeName"],
                    user_name="admin1"
                ),
                server.create_account(
                    platform_id=minimal_account_data["platformId"],
                    safe_name=minimal_account_data["safeName"],
                    user_name="admin2"
                )
            ]
            
            results = await asyncio.gather(*tasks)
            
            assert len(results) == 2
            assert results[0]["id"] == "123_1"
            assert results[1]["id"] == "123_2"
            assert results[0]["userName"] == "admin1"
            assert results[1]["userName"] == "admin2"

    # Password Change Tests
    
    async def test_change_account_password_cpm_managed(self, server):
        """Test changing password for CPM-managed account (no new password specified)"""
        account_id = "123_456_789"
        
        # Mock successful password change response
        mock_response = {
            "id": account_id,
            "lastModifiedTime": "2025-06-30T10:30:00Z",
            "status": "Password change initiated successfully"
        }
        
        with patch.object(server, '_make_api_request', return_value=mock_response):
            result = await server.change_account_password(account_id=account_id)
            
            assert result["id"] == account_id
            assert "lastModifiedTime" in result
            assert "status" in result
            
            # Verify API call was made correctly
            server._make_api_request.assert_called_once_with(
                "POST", 
                f"Accounts/{account_id}/Change/",
                json={"ChangeImmediately": True}
            )

    async def test_change_account_password_manual_password(self, server):
        """Test changing password with manually specified new password"""
        account_id = "123_456_789"
        new_password = "NewSecureP@ssw0rd123"
        
        # Mock successful password change response
        mock_response = {
            "id": account_id,
            "lastModifiedTime": "2025-06-30T10:30:00Z",
            "status": "Password changed successfully"
        }
        
        with patch.object(server, '_make_api_request', return_value=mock_response):
            result = await server.change_account_password(
                account_id=account_id, 
                new_password=new_password
            )
            
            assert result["id"] == account_id
            assert "lastModifiedTime" in result
            
            # Verify API call was made correctly with new password
            server._make_api_request.assert_called_once_with(
                "POST", 
                f"Accounts/{account_id}/Change/",
                json={
                    "ChangeImmediately": True,
                    "NewCredentials": new_password
                }
            )

    async def test_change_account_password_missing_account_id(self, server):
        """Test error when account_id is missing"""
        with pytest.raises(ValueError, match="account_id is required"):
            await server.change_account_password(account_id="")

    async def test_change_account_password_invalid_account_id(self, server):
        """Test error when account_id is None"""
        with pytest.raises(ValueError, match="account_id is required"):
            await server.change_account_password(account_id=None)

    async def test_change_account_password_account_not_found(self, server):
        """Test handling of 404 error for non-existent account"""
        account_id = "non_existent_account"
        
        # Mock 404 response
        mock_error = CyberArkAPIError("Account not found", 404)
        
        with patch.object(server, '_make_api_request', side_effect=mock_error):
            with pytest.raises(CyberArkAPIError) as exc_info:
                await server.change_account_password(account_id=account_id)
            
            assert exc_info.value.status_code == 404
            assert "Account not found" in str(exc_info.value)

    async def test_change_account_password_permission_denied(self, server):
        """Test handling of 403 error for insufficient permissions"""
        account_id = "123_456_789"
        
        # Mock 403 response
        mock_error = CyberArkAPIError("Insufficient permissions", 403)
        
        with patch.object(server, '_make_api_request', side_effect=mock_error):
            with pytest.raises(CyberArkAPIError) as exc_info:
                await server.change_account_password(account_id=account_id)
            
            assert exc_info.value.status_code == 403
            assert "Insufficient permissions" in str(exc_info.value)

    async def test_change_account_password_rate_limited(self, server):
        """Test handling of 429 rate limit error"""
        account_id = "123_456_789"
        
        # Mock 429 response
        mock_error = CyberArkAPIError("Rate limit exceeded", 429)
        
        with patch.object(server, '_make_api_request', side_effect=mock_error):
            with pytest.raises(CyberArkAPIError) as exc_info:
                await server.change_account_password(account_id=account_id)
            
            assert exc_info.value.status_code == 429
            assert "Rate limit exceeded" in str(exc_info.value)

    async def test_change_account_password_network_error(self, server):
        """Test handling of network connectivity errors"""
        account_id = "123_456_789"
        
        with patch.object(server, '_make_api_request', side_effect=Exception("Network connection failed")):
            with pytest.raises(Exception, match="Network connection failed"):
                await server.change_account_password(account_id=account_id)

    async def test_change_account_password_logging_no_sensitive_data(self, server, caplog):
        """Test that password change operations don't log sensitive data"""
        import logging
        
        account_id = "123_456_789"
        new_password = "SuperSecretPassword123!"
        
        mock_response = {
            "id": account_id,
            "lastModifiedTime": "2025-06-30T10:30:00Z"
        }
        
        with patch.object(server, '_make_api_request', return_value=mock_response):
            with caplog.at_level(logging.INFO):
                await server.change_account_password(account_id=account_id, new_password=new_password)
                
                # Check that logs don't contain the password
                log_messages = [record.message for record in caplog.records]
                for message in log_messages:
                    assert new_password not in message
                    assert "SuperSecretPassword123!" not in message
                
                # Verify appropriate info was logged (account ID should be present)
                assert any(account_id in message for message in log_messages)

    async def test_change_account_password_concurrent_operations(self, server):
        """Test concurrent password change operations"""
        import asyncio
        
        account_id_1 = "123_456_789"
        account_id_2 = "987_654_321"
        
        response_1 = {"id": account_id_1, "status": "Password changed for account 1"}
        response_2 = {"id": account_id_2, "status": "Password changed for account 2"}
        
        def mock_request_side_effect(method, endpoint, json=None):
            if f"Accounts/{account_id_1}/Change/" in endpoint:
                return response_1
            elif f"Accounts/{account_id_2}/Change/" in endpoint:
                return response_2
            else:
                return {"id": "unknown", "status": "Unknown"}
        
        with patch.object(server, '_make_api_request', side_effect=mock_request_side_effect):
            # Run password changes concurrently
            tasks = [
                server.change_account_password(account_id=account_id_1),
                server.change_account_password(account_id=account_id_2)
            ]
            
            results = await asyncio.gather(*tasks)
            
            assert len(results) == 2
            assert results[0]["id"] == account_id_1
            assert results[1]["id"] == account_id_2
            assert results[0]["status"] == "Password changed for account 1"
            assert results[1]["status"] == "Password changed for account 2"

    async def test_change_account_password_parameter_validation(self, server):
        """Test parameter validation and sanitization"""
        # Test various invalid account IDs
        invalid_account_ids = ["", "   ", None, 123, [], {}]
        
        for invalid_id in invalid_account_ids:
            with pytest.raises(ValueError, match="account_id is required"):
                await server.change_account_password(account_id=invalid_id)
        
        # Test valid account ID formats
        valid_account_ids = [
            "123_456_789",
            "abc-def-123",
            "AccountID123",
            "12345"
        ]
        
        mock_response = {"id": "test", "status": "Password changed"}
        
        with patch.object(server, '_make_api_request', return_value=mock_response):
            for valid_id in valid_account_ids:
                result = await server.change_account_password(account_id=valid_id)
                assert result["id"] == "test"

    # ========================
    # Verify Account Password Tests
    # ========================
    
    @pytest.mark.asyncio
    async def test_verify_account_password_success(self, server):
        """Test successful password verification"""
        account_id = "123_456_789"
        
        # Mock successful password verification response
        mock_response = {
            "id": account_id,
            "lastVerifiedDateTime": "2025-06-30T10:30:00Z",
            "verified": True,
            "status": "Password verified successfully"
        }
        
        with patch.object(server, '_make_api_request', return_value=mock_response):
            result = await server.verify_account_password(account_id=account_id)
            
            assert result["id"] == account_id
            assert result["verified"] is True
            assert "lastVerifiedDateTime" in result
            assert "status" in result
            
            # Verify API call was made correctly
            server._make_api_request.assert_called_once_with(
                "POST", 
                f"Accounts/{account_id}/Verify/",
                json={}
            )
    
    @pytest.mark.asyncio
    async def test_verify_account_password_missing_account_id(self, server):
        """Test verify password with missing account ID"""
        with pytest.raises(ValueError, match="account_id is required"):
            await server.verify_account_password(account_id="")
    
    @pytest.mark.asyncio
    async def test_verify_account_password_invalid_account_id(self, server):
        """Test verify password with invalid account ID"""
        with pytest.raises(ValueError, match="account_id is required"):
            await server.verify_account_password(account_id=None)
    
    @pytest.mark.asyncio
    async def test_verify_account_password_account_not_found(self, server):
        """Test verify password with non-existent account"""
        account_id = "nonexistent_account"
        
        with patch.object(server, '_make_api_request', side_effect=Exception("Account not found")):
            with pytest.raises(Exception, match="Account not found"):
                await server.verify_account_password(account_id=account_id)
                
            # Verify correct API endpoint was called
            server._make_api_request.assert_called_once_with(
                "POST",
                f"Accounts/{account_id}/Verify/",
                json={}
            )
    
    @pytest.mark.asyncio
    async def test_verify_account_password_permission_denied(self, server):
        """Test verify password with insufficient permissions"""
        account_id = "123_456_789"
        
        with patch.object(server, '_make_api_request', side_effect=Exception("Permission denied")):
            with pytest.raises(Exception, match="Permission denied"):
                await server.verify_account_password(account_id=account_id)
                
            # Verify correct API endpoint was called
            server._make_api_request.assert_called_once_with(
                "POST",
                f"Accounts/{account_id}/Verify/",
                json={}
            )
    
    @pytest.mark.asyncio
    async def test_verify_account_password_rate_limited(self, server):
        """Test verify password with rate limiting"""
        account_id = "123_456_789"
        
        with patch.object(server, '_make_api_request', side_effect=Exception("Rate limited")):
            with pytest.raises(Exception, match="Rate limited"):
                await server.verify_account_password(account_id=account_id)
                
            # Verify correct API endpoint was called
            server._make_api_request.assert_called_once_with(
                "POST",
                f"Accounts/{account_id}/Verify/",
                json={}
            )
    
    @pytest.mark.asyncio
    async def test_verify_account_password_network_error(self, server):
        """Test verify password with network error"""
        account_id = "123_456_789"
        
        with patch.object(server, '_make_api_request', side_effect=Exception("Network error")):
            with pytest.raises(Exception, match="Network error"):
                await server.verify_account_password(account_id=account_id)
    
    @pytest.mark.asyncio
    async def test_verify_account_password_logging_no_sensitive_data(self, server):
        """Test that verify password logging doesn't expose sensitive data"""
        account_id = "123_456_789"
        
        mock_response = {
            "id": account_id,
            "lastVerifiedDateTime": "2025-06-30T10:30:00Z",
            "verified": True,
            "status": "Password verified successfully"
        }
        
        with patch.object(server, '_make_api_request', return_value=mock_response):
            with patch.object(server.logger, 'info') as mock_log_info:
                with patch.object(server.logger, 'error') as mock_log_error:
                    result = await server.verify_account_password(account_id=account_id)
                    
                    # Check that logs don't contain sensitive information
                    log_calls = [call.args[0] for call in mock_log_info.call_args_list]
                    error_calls = [call.args[0] for call in mock_log_error.call_args_list]
                    
                    all_logs = log_calls + error_calls
                    for log_message in all_logs:
                        # If 'password' is in the message, 'verify' should also be present (since this is a verification operation)
                        if "password" in log_message.lower():
                            assert "verif" in log_message.lower(), f"Log message contains 'password' but not 'verify': {log_message}"
                        # These sensitive terms should never appear in logs
                        assert "credential" not in log_message.lower()
                        assert "secret" not in log_message.lower()
    
    @pytest.mark.asyncio
    async def test_verify_account_password_concurrent_operations(self, server):
        """Test concurrent password verification operations"""
        account_ids = ["account_1", "account_2", "account_3"]
        
        def mock_request_side_effect(*args, **kwargs):
            # Extract account_id from the API endpoint (e.g., "Accounts/account_1/Verify/")
            endpoint = args[1]
            account_id = endpoint.split('/')[1]
            return {
                "id": account_id,
                "lastVerifiedDateTime": "2025-06-30T10:30:00Z",
                "verified": True,
                "status": "Password verified successfully"
            }
        
        with patch.object(server, '_make_api_request', side_effect=mock_request_side_effect):
            # Run concurrent verification operations
            tasks = [
                server.verify_account_password(account_id=account_id)
                for account_id in account_ids
            ]
            
            results = await asyncio.gather(*tasks)
            
            # Verify all operations completed successfully
            assert len(results) == len(account_ids)
            for i, result in enumerate(results):
                assert result["id"] == account_ids[i]
                assert result["verified"] is True
                assert "lastVerifiedDateTime" in result
    
    @pytest.mark.asyncio
    async def test_verify_account_password_parameter_validation(self, server):
        """Test parameter validation and sanitization"""
        # Test various invalid account IDs
        invalid_account_ids = ["", "   ", None, 123, [], {}]
        
        for invalid_id in invalid_account_ids:
            with pytest.raises(ValueError, match="account_id is required"):
                await server.verify_account_password(account_id=invalid_id)
        
        # Test valid account ID formats
        valid_account_ids = [
            "123_456_789",
            "abc-def-123",
            "AccountID123",
            "12345"
        ]
        
        mock_response = {
            "id": "test", 
            "verified": True, 
            "status": "Password verified",
            "lastVerifiedDateTime": "2025-06-30T10:30:00Z"
        }
        
        with patch.object(server, '_make_api_request', return_value=mock_response):
            for valid_id in valid_account_ids:
                result = await server.verify_account_password(account_id=valid_id)
                assert result["id"] == "test"
                assert result["verified"] is True

    # ===== RECONCILE PASSWORD TESTS =====

    @pytest.mark.asyncio
    async def test_reconcile_account_password_success(self, server):
        """Test successful password reconciliation"""
        account_id = "test_account_123"
        
        mock_response = {
            "id": account_id,
            "reconciled": True,
            "status": "Password reconciled successfully",
            "lastReconciledDateTime": "2025-06-30T10:30:00Z",
            "platformId": "WinDomain",
            "safeName": "TestSafe"
        }
        
        with patch.object(server, '_make_api_request', return_value=mock_response) as mock_request:
            result = await server.reconcile_account_password(account_id=account_id)
            
            # Verify API call
            mock_request.assert_called_once_with(
                "POST",
                f"Accounts/{account_id}/Reconcile/",
                json={}
            )
            
            # Verify response
            assert result["id"] == account_id
            assert result["reconciled"] is True
            assert result["status"] == "Password reconciled successfully"
            assert result["lastReconciledDateTime"] == "2025-06-30T10:30:00Z"

    @pytest.mark.asyncio
    async def test_reconcile_account_password_missing_account_id(self, server):
        """Test error handling for missing account ID"""
        with pytest.raises(ValueError, match="account_id is required"):
            await server.reconcile_account_password(account_id="")

    @pytest.mark.asyncio
    async def test_reconcile_account_password_invalid_account_id(self, server):
        """Test error handling for invalid account ID"""
        with pytest.raises(ValueError, match="account_id is required"):
            await server.reconcile_account_password(account_id=None)

    @pytest.mark.asyncio
    async def test_reconcile_account_password_account_not_found(self, server):
        """Test error handling when account is not found"""
        account_id = "nonexistent_account"
        
        mock_error = CyberArkAPIError(
            "Account not found",
            status_code=404
        )
        
        with patch.object(server, '_make_api_request', side_effect=mock_error):
            with pytest.raises(CyberArkAPIError) as exc_info:
                await server.reconcile_account_password(account_id=account_id)
            
            assert exc_info.value.status_code == 404
            assert "Account not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_reconcile_account_password_permission_denied(self, server):
        """Test error handling for permission denied"""
        account_id = "test_account_123"
        
        mock_error = CyberArkAPIError(
            "Permission denied",
            status_code=403
        )
        
        with patch.object(server, '_make_api_request', side_effect=mock_error):
            with pytest.raises(CyberArkAPIError) as exc_info:
                await server.reconcile_account_password(account_id=account_id)
            
            assert exc_info.value.status_code == 403
            assert "Permission denied" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_reconcile_account_password_rate_limited(self, server):
        """Test error handling for rate limiting"""
        account_id = "test_account_123"
        
        mock_error = CyberArkAPIError(
            "Rate limit exceeded",
            status_code=429
        )
        
        with patch.object(server, '_make_api_request', side_effect=mock_error):
            with pytest.raises(CyberArkAPIError) as exc_info:
                await server.reconcile_account_password(account_id=account_id)
            
            assert exc_info.value.status_code == 429
            assert "Rate limit exceeded" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_reconcile_account_password_network_error(self, server):
        """Test error handling for network errors"""
        account_id = "test_account_123"
        
        with patch.object(server, '_make_api_request', side_effect=Exception("Network error")):
            with pytest.raises(Exception, match="Network error"):
                await server.reconcile_account_password(account_id=account_id)

    @pytest.mark.asyncio
    async def test_reconcile_account_password_logging_no_sensitive_data(self, server):
        """Test that reconcile password operations don't log sensitive data"""
        account_id = "test_account_123"
        
        mock_response = {
            "id": account_id,
            "reconciled": True,
            "status": "Password reconciled successfully",
            "lastReconciledDateTime": "2025-06-30T10:30:00Z"
        }
        
        with patch.object(server, '_make_api_request', return_value=mock_response):
            with patch.object(server.logger, 'info') as mock_info:
                with patch.object(server.logger, 'error') as mock_error:
                    await server.reconcile_account_password(account_id=account_id)
                    
                    # Check info logs
                    info_calls = [call.args[0] for call in mock_info.call_args_list]
                    for log_message in info_calls:
                        # For reconcile operations, "password reconciliation" is acceptable in logs
                        # But no actual passwords/credentials should be logged
                        assert account_id in log_message
                        # These sensitive terms should never appear in logs
                        assert "credential" not in log_message.lower()
                        assert "secret" not in log_message.lower()
                    
                    # Ensure no error logs in successful case
                    mock_error.assert_not_called()
        
        # Test error case logging
        with patch.object(server, '_make_api_request', side_effect=Exception("API error")):
            with patch.object(server.logger, 'error') as mock_error:
                try:
                    await server.reconcile_account_password(account_id=account_id)
                except Exception:
                    pass
                
                # Check error logs don't contain sensitive data
                error_calls = [call.args[0] for call in mock_error.call_args_list]
                for log_message in error_calls:
                    assert account_id in log_message
                    # These sensitive terms should never appear in logs
                    assert "credential" not in log_message.lower()
                    assert "secret" not in log_message.lower()

    @pytest.mark.asyncio
    async def test_reconcile_account_password_concurrent_operations(self, server):
        """Test concurrent reconcile password operations"""
        account_ids = ["account_1", "account_2", "account_3"]
        
        async def mock_api_request(method, url, **kwargs):
            # Extract account ID from URL
            account_id = url.split("/")[1]
            return {
                "id": account_id,
                "reconciled": True,
                "status": "Password reconciled successfully",
                "lastReconciledDateTime": "2025-06-30T10:30:00Z"
            }
        
        with patch.object(server, '_make_api_request', side_effect=mock_api_request):
            # Run concurrent reconcile operations
            tasks = [
                server.reconcile_account_password(account_id=account_id)
                for account_id in account_ids
            ]
            
            results = await asyncio.gather(*tasks)
            
            # Verify all operations completed successfully
            assert len(results) == len(account_ids)
            for i, result in enumerate(results):
                assert result["id"] == account_ids[i]
                assert result["reconciled"] is True
                assert result["status"] == "Password reconciled successfully"

    @pytest.mark.asyncio
    async def test_reconcile_account_password_parameter_validation(self, server):
        """Test parameter validation and sanitization"""
        # Test various invalid account IDs
        invalid_account_ids = ["", "   ", None, 123, [], {}]
        
        for invalid_id in invalid_account_ids:
            with pytest.raises(ValueError, match="account_id is required"):
                await server.reconcile_account_password(account_id=invalid_id)
        
        # Test valid account ID formats
        valid_account_ids = [
            "123_456_789",
            "abc-def-123",
            "AccountID123",
            "12345"
        ]
        
        mock_response = {
            "id": "test", 
            "reconciled": True, 
            "status": "Password reconciled successfully",
            "lastReconciledDateTime": "2025-06-30T10:30:00Z"
        }
        
        with patch.object(server, '_make_api_request', return_value=mock_response):
            for valid_id in valid_account_ids:
                result = await server.reconcile_account_password(account_id=valid_id)
                assert result["id"] == "test"
                assert result["reconciled"] is True

    @pytest.mark.asyncio
    async def test_reconcile_account_password_long_running_operation(self, server):
        """Test handling of long-running reconciliation operations"""
        account_id = "test_account_123"
        
        # Mock a response that indicates the operation is in progress
        mock_response = {
            "id": account_id,
            "reconciled": False,
            "status": "Reconciliation in progress",
            "lastReconciledDateTime": None,
            "operationId": "op_12345"
        }
        
        with patch.object(server, '_make_api_request', return_value=mock_response) as mock_request:
            result = await server.reconcile_account_password(account_id=account_id)
            
            # Verify API call
            mock_request.assert_called_once_with(
                "POST",
                f"Accounts/{account_id}/Reconcile/",
                json={}
            )
            
            # Verify response handles in-progress status
            assert result["id"] == account_id
            assert result["reconciled"] is False
            assert result["status"] == "Reconciliation in progress"
            assert result["lastReconciledDateTime"] is None
            assert "operationId" in result

    @pytest.mark.asyncio
    async def test_reconcile_account_password_reconciliation_status_validation(self, server):
        """Test validation of reconciliation status in response"""
        account_id = "test_account_123"
        
        # Test successful reconciliation
        success_response = {
            "id": account_id,
            "reconciled": True,
            "status": "Password reconciled successfully",
            "lastReconciledDateTime": "2025-06-30T10:30:00Z"
        }
        
        with patch.object(server, '_make_api_request', return_value=success_response):
            result = await server.reconcile_account_password(account_id=account_id)
            assert result["reconciled"] is True
            assert result["lastReconciledDateTime"] is not None
        
        # Test failed reconciliation
        failed_response = {
            "id": account_id,
            "reconciled": False,
            "status": "Reconciliation failed - target system unavailable",
            "lastReconciledDateTime": "2025-06-29T10:30:00Z",
            "error": "Connection timeout"
        }
        
        with patch.object(server, '_make_api_request', return_value=failed_response):
            result = await server.reconcile_account_password(account_id=account_id)
            assert result["reconciled"] is False
            assert "error" in result
            assert result["status"] == "Reconciliation failed - target system unavailable"
