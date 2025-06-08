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