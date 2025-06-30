import pytest
import httpx
from unittest.mock import Mock, AsyncMock, patch, mock_open
from datetime import datetime, timedelta
import os
import asyncio
import base64

from src.cyberark_mcp.auth import CyberArkAuthenticator, AuthenticationError
from src.cyberark_mcp.server import CyberArkMCPServer


class TestAuthentication:
    """Test cases for CyberArk API token authentication"""

    @pytest.fixture
    def auth_mock_config(self):
        """Mock configuration for testing"""
        return {
            "identity_tenant_id": "test-tenant",
            "client_id": "test-client",
            "client_secret": "test-secret",
            "timeout": 30
        }

    @pytest.fixture
    def auth_authenticator(self, auth_mock_config):
        """Create authenticator instance for testing"""
        return CyberArkAuthenticator(
            identity_tenant_id=auth_mock_config["identity_tenant_id"],
            client_id=auth_mock_config["client_id"],
            client_secret=auth_mock_config["client_secret"],
            timeout=auth_mock_config["timeout"]
        )

    @pytest.mark.auth
    def test_authenticator_initialization(self, auth_authenticator, auth_mock_config):
        """Test that authenticator initializes with correct parameters"""
        assert auth_authenticator.identity_tenant_id == auth_mock_config["identity_tenant_id"]
        assert auth_authenticator.client_id == auth_mock_config["client_id"]
        assert auth_authenticator.client_secret == auth_mock_config["client_secret"]
        assert auth_authenticator.timeout == auth_mock_config["timeout"]
        assert auth_authenticator._token is None
        assert auth_authenticator._token_expiry is None

    @pytest.mark.auth
    def test_get_token_url(self, auth_authenticator):
        """Test that token URL is constructed correctly"""
        expected_url = "https://test-tenant.id.cyberark.cloud/oauth2/platformtoken"
        assert auth_authenticator._get_token_url() == expected_url

    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_successful_token_request(self, auth_authenticator):
        """Test successful token acquisition"""
        mock_response_data = {
            "access_token": "test-token-12345",
            "token_type": "Bearer",
            "expires_in": 900
        }
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            token = await auth_authenticator._request_new_token()
            
            assert token == "test-token-12345"
            mock_post.assert_called_once()
            
            # Verify request parameters
            call_args = mock_post.call_args
            assert call_args[1]['data']['grant_type'] == 'client_credentials'
            assert call_args[1]['data']['client_id'] == 'test-client'
            assert call_args[1]['data']['client_secret'] == 'test-secret'

    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_token_request_with_http_error(self, auth_authenticator):
        """Test token request with HTTP error response"""
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "401 Unauthorized", request=Mock(), response=Mock()
            )
            mock_post.return_value = mock_response
            
            with pytest.raises(AuthenticationError, match="Failed to authenticate"):
                await auth_authenticator._request_new_token()

    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_token_request_with_network_error(self, auth_authenticator):
        """Test token request with network error"""
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.side_effect = httpx.ConnectError("Connection failed")
            
            with pytest.raises(AuthenticationError, match="Network error"):
                await auth_authenticator._request_new_token()

    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_token_request_with_invalid_response(self, auth_authenticator):
        """Test token request with invalid JSON response"""
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = Mock()
            mock_response.json.side_effect = ValueError("Invalid JSON")
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            with pytest.raises(AuthenticationError, match="Invalid response format"):
                await auth_authenticator._request_new_token()

    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_token_request_missing_access_token(self, auth_authenticator):
        """Test token request with missing access_token in response"""
        mock_response_data = {
            "token_type": "Bearer",
            "expires_in": 900
        }
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            with pytest.raises(AuthenticationError, match="Missing access_token"):
                await auth_authenticator._request_new_token()

    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_get_valid_token_first_time(self, auth_authenticator):
        """Test getting token for the first time"""
        with patch.object(auth_authenticator, '_request_new_token', return_value="new-token"):
            token = await auth_authenticator.get_valid_token()
            assert token == "new-token"
            assert auth_authenticator._token == "new-token"

    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_get_valid_token_cached(self, auth_authenticator):
        """Test getting cached token when still valid"""
        # Set up cached token
        auth_authenticator._token = "cached-token"
        auth_authenticator._token_expiry = datetime.utcnow() + timedelta(minutes=10)
        
        with patch.object(auth_authenticator, '_request_new_token') as mock_request:
            token = await auth_authenticator.get_valid_token()
            assert token == "cached-token"
            mock_request.assert_not_called()

    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_get_valid_token_expired(self, auth_authenticator):
        """Test getting new token when cached token is expired"""
        # Set up expired token
        auth_authenticator._token = "expired-token"
        auth_authenticator._token_expiry = datetime.utcnow() - timedelta(minutes=1)
        
        with patch.object(auth_authenticator, '_request_new_token', return_value="new-token"):
            token = await auth_authenticator.get_valid_token()
            assert token == "new-token"
            assert auth_authenticator._token == "new-token"

    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_get_valid_token_near_expiry(self, auth_authenticator):
        """Test getting new token when cached token is near expiry (safety margin)"""
        # Set up token near expiry (within 60 seconds)
        auth_authenticator._token = "near-expiry-token"
        auth_authenticator._token_expiry = datetime.utcnow() + timedelta(seconds=30)
        
        with patch.object(auth_authenticator, '_request_new_token', return_value="new-token"):
            token = await auth_authenticator.get_valid_token()
            assert token == "new-token"
            assert auth_authenticator._token == "new-token"

    @pytest.mark.auth
    def test_is_token_valid_no_token(self, auth_authenticator):
        """Test token validity check when no token exists"""
        assert not auth_authenticator._is_token_valid()

    @pytest.mark.auth
    def test_is_token_valid_no_expiry(self, auth_authenticator):
        """Test token validity check when token has no expiry"""
        auth_authenticator._token = "test-token"
        assert not auth_authenticator._is_token_valid()

    @pytest.mark.auth
    def test_is_token_valid_expired(self, auth_authenticator):
        """Test token validity check for expired token"""
        auth_authenticator._token = "test-token"
        auth_authenticator._token_expiry = datetime.utcnow() - timedelta(minutes=1)
        assert not auth_authenticator._is_token_valid()

    @pytest.mark.auth
    def test_is_token_valid_near_expiry(self, auth_authenticator):
        """Test token validity check for token near expiry"""
        auth_authenticator._token = "test-token"
        auth_authenticator._token_expiry = datetime.utcnow() + timedelta(seconds=30)
        assert not auth_authenticator._is_token_valid()  # Should be False due to safety margin

    @pytest.mark.auth
    def test_is_token_valid_good_token(self, auth_authenticator):
        """Test token validity check for valid token"""
        auth_authenticator._token = "test-token"
        auth_authenticator._token_expiry = datetime.utcnow() + timedelta(minutes=10)
        assert auth_authenticator._is_token_valid()

    @pytest.mark.auth
    def test_environment_variable_initialization(self):
        """Test authenticator initialization from environment variables"""
        env_vars = {
            "CYBERARK_IDENTITY_TENANT_ID": "env-tenant",
            "CYBERARK_CLIENT_ID": "env-client",
            "CYBERARK_CLIENT_SECRET": "env-secret",
            "CYBERARK_API_TIMEOUT": "60"
        }
        
        with patch.dict(os.environ, env_vars):
            authenticator = CyberArkAuthenticator.from_environment()
            assert authenticator.identity_tenant_id == "env-tenant"
            assert authenticator.client_id == "env-client"
            assert authenticator.client_secret == "env-secret"
            assert authenticator.timeout == 60

    @pytest.mark.auth
    def test_environment_variable_initialization_missing_required(self):
        """Test authenticator initialization with missing required environment variables"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="CYBERARK_IDENTITY_TENANT_ID"):
                CyberArkAuthenticator.from_environment()

    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_get_auth_header(self, auth_authenticator):
        """Test getting authorization header with token"""
        with patch.object(auth_authenticator, 'get_valid_token', return_value="test-token"):
            header = await auth_authenticator.get_auth_header()
            assert header == {"Authorization": "Bearer test-token"}

    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_concurrent_token_requests(self, auth_authenticator):
        """Test that concurrent token requests don't cause race conditions"""
        # Make sure there's no valid token initially
        auth_authenticator._token = None
        auth_authenticator._token_expiry = None
        
        async def mock_request_new_token():
            # Simulate some delay and side effects
            await asyncio.sleep(0.1)
            auth_authenticator._token = "concurrent-token"
            auth_authenticator._token_expiry = datetime.utcnow() + timedelta(minutes=15)
            return "concurrent-token"
        
        with patch.object(auth_authenticator, '_request_new_token', side_effect=mock_request_new_token) as mock_request:
            # Simulate multiple concurrent requests
            tasks = [auth_authenticator.get_valid_token() for _ in range(5)]
            tokens = await asyncio.gather(*tasks)
            
            # All should return the same token
            assert all(token == "concurrent-token" for token in tokens)
            # Should only make one actual request due to locking
            assert mock_request.call_count == 1


class TestServerCore:
    """Test cases for CyberArk MCP Server core functionality (excluding platform-specific tests)"""

    @pytest.fixture
    def server_mock_config(self):
        """Mock configuration for testing"""
        return {
            "identity_tenant_id": "test-tenant",
            "client_id": "test-client",
            "client_secret": "test-secret",
            "subdomain": "test-subdomain",
            "timeout": 30
        }

    @pytest.fixture
    def server_mock_authenticator(self, server_mock_config):
        """Mock authenticator for testing"""
        auth = Mock(spec=CyberArkAuthenticator)
        auth.get_auth_header = AsyncMock(return_value={"Authorization": "Bearer test-token"})
        return auth

    @pytest.fixture
    def server_instance(self, server_mock_authenticator, server_mock_config):
        """Create server instance for testing"""
        return CyberArkMCPServer(
            authenticator=server_mock_authenticator,
            subdomain=server_mock_config["subdomain"],
            timeout=server_mock_config["timeout"]
        )

    def test_server_initialization(self, server_instance, server_mock_authenticator, server_mock_config):
        """Test that server initializes with correct parameters"""
        assert server_instance.authenticator == server_mock_authenticator
        assert server_instance.subdomain == server_mock_config["subdomain"]
        assert server_instance.timeout == server_mock_config["timeout"]
        assert server_instance.base_url == f"https://{server_mock_config['subdomain']}.privilegecloud.cyberark.cloud/PasswordVault/api"

    def test_server_from_environment(self):
        """Test server initialization from environment variables"""
        env_vars = {
            "CYBERARK_IDENTITY_TENANT_ID": "env-tenant",
            "CYBERARK_CLIENT_ID": "env-client",
            "CYBERARK_CLIENT_SECRET": "env-secret",
            "CYBERARK_SUBDOMAIN": "env-subdomain",
            "CYBERARK_API_TIMEOUT": "60"
        }
        
        with patch.dict(os.environ, env_vars):
            server = CyberArkMCPServer.from_environment()
            assert server.subdomain == "env-subdomain"
            assert server.timeout == 60
            assert isinstance(server.authenticator, CyberArkAuthenticator)

    def test_server_from_environment_missing_required(self):
        """Test server initialization with missing required environment variables"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="CYBERARK_SUBDOMAIN"):
                CyberArkMCPServer.from_environment()

    def test_get_api_url(self, server_instance):
        """Test API URL construction"""
        endpoint = "Accounts"
        expected_url = "https://test-subdomain.privilegecloud.cyberark.cloud/PasswordVault/api/Accounts"
        assert server_instance._get_api_url(endpoint) == expected_url

    @pytest.mark.asyncio
    async def test_make_api_request_success(self, server_instance, server_mock_authenticator):
        """Test successful API request"""
        mock_response_data = {"value": [{"id": "123", "name": "test-account"}]}
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            result = await server_instance._make_api_request("GET", "Accounts")
            
            assert result == mock_response_data
            server_mock_authenticator.get_auth_header.assert_called_once()
            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_make_api_request_with_params(self, server_instance, server_mock_authenticator):
        """Test API request with query parameters"""
        params = {"safeName": "test-safe", "search": "admin"}
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {}
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            await server_instance._make_api_request("GET", "Accounts", params=params)
            
            # Verify params were passed to the request
            call_args = mock_get.call_args
            assert call_args[1]['params'] == params

    @pytest.mark.asyncio
    async def test_make_api_request_http_error(self, server_instance, server_mock_authenticator):
        """Test API request with HTTP error"""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "404 Not Found", request=Mock(), response=Mock()
            )
            mock_get.return_value = mock_response
            
            with pytest.raises(Exception):  # Should raise appropriate exception
                await server_instance._make_api_request("GET", "NonExistentEndpoint")

    @pytest.mark.asyncio
    async def test_make_api_request_network_error(self, server_instance, server_mock_authenticator):
        """Test API request with network error"""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.side_effect = httpx.ConnectError("Connection failed")
            
            with pytest.raises(Exception):  # Should raise appropriate exception
                await server_instance._make_api_request("GET", "Accounts")

    def test_tool_registration(self, server_instance):
        """Test that required tools are registered"""
        # This will test the actual tool registration once implemented
        tools = server_instance.get_available_tools()
        expected_tools = [
            "list_accounts",
            "get_account_details", 
            "search_accounts",
            "list_safes",
            "get_safe_details",
            "list_platforms",
            "get_platform_details"
        ]
        
        for tool_name in expected_tools:
            assert tool_name in tools

    @pytest.mark.asyncio
    async def test_list_accounts_tool(self, server_instance):
        """Test list_accounts tool functionality"""
        mock_accounts = [
            {"id": "123", "name": "account1", "safeName": "safe1"},
            {"id": "456", "name": "account2", "safeName": "safe2"}
        ]
        
        with patch.object(server_instance, '_make_api_request', return_value={"value": mock_accounts}):
            result = await server_instance.list_accounts()
            assert result == mock_accounts

    @pytest.mark.asyncio
    async def test_list_accounts_with_filters(self, server_instance):
        """Test list_accounts with filter parameters"""
        filters = {"safeName": "test-safe", "userName": "admin"}
        
        with patch.object(server_instance, '_make_api_request') as mock_request:
            mock_request.return_value = {"value": []}
            await server_instance.list_accounts(**filters)
            mock_request.assert_called_once_with("GET", "Accounts", params=filters)

    @pytest.mark.asyncio
    async def test_get_account_details_tool(self, server_instance):
        """Test get_account_details tool functionality"""
        account_id = "123"
        mock_account = {"id": "123", "name": "test-account", "safeName": "test-safe"}
        
        with patch.object(server_instance, '_make_api_request', return_value=mock_account):
            result = await server_instance.get_account_details(account_id)
            assert result == mock_account

    @pytest.mark.asyncio
    async def test_search_accounts_tool(self, server_instance):
        """Test search_accounts tool functionality"""
        search_params = {"keywords": "admin", "safeName": "test-safe"}
        mock_results = [{"id": "123", "name": "admin-account"}]
        
        with patch.object(server_instance, '_make_api_request', return_value={"value": mock_results}):
            result = await server_instance.search_accounts(**search_params)
            assert result == mock_results

    # Safe Management Tests
    
    @pytest.mark.asyncio
    async def test_list_safes_basic(self, server_instance):
        """Test basic list_safes functionality"""
        mock_safes = [
            {
                "safeUrlId": "VaultInternal",
                "safeName": "VaultInternal", 
                "safeNumber": 2,
                "description": "",
                "location": "\\",
                "creator": {
                    "id": "84425267_6da7_4c2c_9ad6_26aef85c83be",
                    "name": "Administrator"
                },
                "olacEnabled": False,
                "managingCPM": "",
                "numberOfVersionsRetention": None,
                "numberOfDaysRetention": 30,
                "autoPurgeEnabled": False,
                "creationTime": 1608827926,
                "lastModificationTime": 1610319618268452,
                "isExpiredMember": False
            },
            {
                "safeUrlId": "HRSafe",
                "safeName": "HRSafe",
                "safeNumber": 687,
                "description": "HR Safe for sensitive data",
                "location": "\\",
                "creator": {
                    "id": "user123",
                    "name": "HRAdmin"
                },
                "olacEnabled": True,
                "managingCPM": "PasswordManager",
                "numberOfVersionsRetention": 5,
                "numberOfDaysRetention": 90,
                "autoPurgeEnabled": True,
                "creationTime": 1621412613,
                "lastModificationTime": 1622361852859451,
                "isExpiredMember": False
            }
        ]
        
        mock_response = {
            "value": mock_safes,
            "count": 2,
            "nextLink": None
        }
        
        with patch.object(server_instance, '_make_api_request', return_value=mock_response):
            result = await server_instance.list_safes()
            assert result == mock_safes
            assert len(result) == 2
            assert result[0]["safeName"] == "VaultInternal"
            assert result[1]["safeName"] == "HRSafe"

    @pytest.mark.asyncio
    async def test_list_safes_with_search(self, server_instance):
        """Test list_safes with search parameter"""
        search_term = "HR"
        
        with patch.object(server_instance, '_make_api_request') as mock_request:
            mock_request.return_value = {"value": [], "count": 0}
            await server_instance.list_safes(search=search_term)
            mock_request.assert_called_once_with("GET", "Safes", params={"search": search_term})

    @pytest.mark.asyncio
    async def test_list_safes_with_pagination_params(self, server_instance):
        """Test list_safes with pagination parameters"""
        params = {
            "search": "test",
            "offset": 10,
            "limit": 5,
            "sort": "safeName desc",
            "includeAccounts": True,
            "extendedDetails": False
        }
        
        with patch.object(server_instance, '_make_api_request') as mock_request:
            mock_request.return_value = {"value": [], "count": 0}
            await server_instance.list_safes(**params)
            mock_request.assert_called_once_with("GET", "Safes", params=params)

    @pytest.mark.asyncio
    async def test_list_safes_with_pagination_response(self, server_instance):
        """Test list_safes with paginated response"""
        mock_response = {
            "value": [{"safeName": "TestSafe", "safeUrlId": "TestSafe"}],
            "count": 100,
            "nextLink": "api/safes?offset=25&limit=25&useCache=False"
        }
        
        with patch.object(server_instance, '_make_api_request', return_value=mock_response):
            result = await server_instance.list_safes(limit=25)
            assert result == mock_response["value"]
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_list_safes_empty_response(self, server_instance):
        """Test list_safes with empty response"""
        mock_response = {"value": [], "count": 0}
        
        with patch.object(server_instance, '_make_api_request', return_value=mock_response):
            result = await server_instance.list_safes()
            assert result == []

    @pytest.mark.asyncio
    async def test_list_safes_no_value_field(self, server_instance):
        """Test list_safes when API returns no 'value' field"""
        mock_response = {"count": 0}
        
        with patch.object(server_instance, '_make_api_request', return_value=mock_response):
            result = await server_instance.list_safes()
            assert result == []

    @pytest.mark.asyncio
    async def test_get_safe_details_basic(self, server_instance):
        """Test basic get_safe_details functionality"""
        safe_name = "HRSafe"
        mock_safe = {
            "safeUrlId": "HRSafe",
            "safeName": "HRSafe",
            "safeNumber": 687,
            "description": "HRSafe_Desc",
            "location": "\\",
            "creator": {
                "id": "84425267_6da7_4c2c_9ad6_26aef85c83be",
                "name": "Administrator"
            },
            "olacEnabled": False,
            "managingCPM": "",
            "numberOfVersionsRetention": None,
            "numberOfDaysRetention": 6,
            "autoPurgeEnabled": False,
            "creationTime": 1621412613,
            "lastModificationTime": 1622361852859451,
            "accounts": [],
            "isExpiredMember": False
        }
        
        with patch.object(server_instance, '_make_api_request', return_value=mock_safe):
            result = await server_instance.get_safe_details(safe_name)
            assert result == mock_safe
            assert result["safeName"] == safe_name
            assert result["safeNumber"] == 687

    @pytest.mark.asyncio 
    async def test_get_safe_details_with_url_encoding(self, server_instance):
        """Test get_safe_details with special characters requiring URL encoding"""
        safe_name = "My Safe With Spaces"
        expected_endpoint = f"Safes/{safe_name}"
        
        with patch.object(server_instance, '_make_api_request') as mock_request:
            mock_request.return_value = {"safeName": safe_name}
            await server_instance.get_safe_details(safe_name)
            mock_request.assert_called_once_with("GET", expected_endpoint, params=None)

    @pytest.mark.asyncio
    async def test_get_safe_details_with_query_params(self, server_instance):
        """Test get_safe_details with query parameters"""
        safe_name = "TestSafe"
        params = {
            "includeAccounts": True,
            "useCache": False
        }
        
        with patch.object(server_instance, '_make_api_request') as mock_request:
            mock_request.return_value = {"safeName": safe_name}
            await server_instance.get_safe_details(safe_name, **params)
            mock_request.assert_called_once_with("GET", f"Safes/{safe_name}", params=params)

    @pytest.mark.asyncio
    async def test_get_safe_details_with_accounts(self, server_instance):
        """Test get_safe_details with accounts included"""
        safe_name = "HRSafe"
        mock_safe = {
            "safeName": "HRSafe",
            "accounts": [
                {"id": "123", "name": "hr-admin"},
                {"id": "456", "name": "hr-user"}
            ]
        }
        
        with patch.object(server_instance, '_make_api_request', return_value=mock_safe):
            result = await server_instance.get_safe_details(safe_name, includeAccounts=True)
            assert result == mock_safe
            assert len(result["accounts"]) == 2

    def test_error_handling_configuration(self, server_instance):
        """Test that error handling is properly configured"""
        # Verify that server has appropriate error handling methods
        assert hasattr(server_instance, '_handle_api_error')
        assert hasattr(server_instance, '_log_error')

    @pytest.mark.asyncio
    async def test_authentication_refresh_on_401(self, server_instance, server_mock_authenticator):
        """Test that authentication is refreshed on 401 errors"""
        # First call raises 401, second call succeeds
        call_count = 0
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                mock_response = Mock()
                mock_error_response = Mock()
                mock_error_response.status_code = 401
                mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                    "401 Unauthorized", request=Mock(), response=mock_error_response
                )
                return mock_response
            else:
                mock_response = Mock()
                mock_response.json.return_value = {"value": []}
                mock_response.raise_for_status.return_value = None
                return mock_response
        
        with patch('httpx.AsyncClient.get', side_effect=side_effect):
            result = await server_instance._make_api_request("GET", "Accounts")
            # Should have called get_auth_header twice (initial + retry)
            assert server_mock_authenticator.get_auth_header.call_count >= 2

    def test_logging_configuration(self, server_instance):
        """Test that logging is properly configured"""
        assert hasattr(server_instance, 'logger')
        # Verify logger is configured for the correct module
        assert server_instance.logger.name == 'src.cyberark_mcp.server'

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, server_instance):
        """Test that server can handle concurrent requests"""
        with patch.object(server_instance, '_make_api_request') as mock_request:
            mock_request.return_value = {"value": []}
            
            # Make multiple concurrent requests
            tasks = [
                server_instance.list_accounts(),
                server_instance.list_safes(),
                server_instance.search_accounts(keywords="test")
            ]
            
            results = await asyncio.gather(*tasks)
            assert len(results) == 3
            assert mock_request.call_count == 3


class TestPlatformManagement:
    """Dedicated test class for platform management functionality"""

    @pytest.fixture
    def platform_mock_config(self):
        """Mock configuration for testing"""
        return {
            "identity_tenant_id": "test-tenant",
            "client_id": "test-client",
            "client_secret": "test-secret",
            "subdomain": "test-subdomain",
            "timeout": 30
        }

    @pytest.fixture
    def platform_mock_authenticator(self, platform_mock_config):
        """Mock authenticator for testing"""
        auth = Mock(spec=CyberArkAuthenticator)
        auth.get_auth_header = AsyncMock(return_value={"Authorization": "Bearer test-token"})
        return auth

    @pytest.fixture
    def platform_server(self, platform_mock_authenticator, platform_mock_config):
        """Create server instance for testing"""
        return CyberArkMCPServer(
            authenticator=platform_mock_authenticator,
            subdomain=platform_mock_config["subdomain"],
            timeout=platform_mock_config["timeout"]
        )

    @pytest.mark.asyncio
    async def test_list_platforms_tool(self, platform_server):
        """Test list_platforms tool functionality"""
        mock_platforms = [
            {
                "id": "WinServerLocal",
                "name": "Windows Server Local",
                "platformType": "Regular",
                "active": True,
                "systemType": "Windows"
            },
            {
                "id": "UnixSSH", 
                "name": "Unix via SSH",
                "platformType": "Regular",
                "active": True,
                "systemType": "Unix"
            }
        ]
        
        with patch.object(platform_server, '_make_api_request', return_value={"Platforms": mock_platforms}):
            result = await platform_server.list_platforms()
            assert result == mock_platforms

    @pytest.mark.asyncio
    async def test_list_platforms_with_search(self, platform_server):
        """Test list_platforms with search parameter"""
        search_term = "Windows"
        
        with patch.object(platform_server, '_make_api_request') as mock_request:
            mock_request.return_value = {"Platforms": []}
            await platform_server.list_platforms(search=search_term)
            mock_request.assert_called_once_with("GET", "Platforms", params={"search": search_term})

    @pytest.mark.asyncio
    async def test_list_platforms_with_active_filter(self, platform_server):
        """Test list_platforms with active filter"""
        with patch.object(platform_server, '_make_api_request') as mock_request:
            mock_request.return_value = {"Platforms": []}
            await platform_server.list_platforms(active=True)
            mock_request.assert_called_once_with("GET", "Platforms", params={"active": "true"})

    @pytest.mark.asyncio
    async def test_list_platforms_with_system_type_filter(self, platform_server):
        """Test list_platforms with system type filter"""
        system_type = "Windows"
        
        with patch.object(platform_server, '_make_api_request') as mock_request:
            mock_request.return_value = {"Platforms": []}
            await platform_server.list_platforms(system_type=system_type)
            mock_request.assert_called_once_with("GET", "Platforms", params={"systemType": system_type})

    @pytest.mark.asyncio
    async def test_list_platforms_with_multiple_filters(self, platform_server):
        """Test list_platforms with multiple filter parameters"""
        filters = {"search": "Windows", "active": True, "systemType": "Windows"}
        expected_params = {"search": "Windows", "active": "true", "systemType": "Windows"}
        
        with patch.object(platform_server, '_make_api_request') as mock_request:
            mock_request.return_value = {"Platforms": []}
            await platform_server.list_platforms(**filters)
            mock_request.assert_called_once_with("GET", "Platforms", params=expected_params)

    @pytest.mark.asyncio
    async def test_get_platform_details_tool(self, platform_server):
        """Test get_platform_details tool functionality"""
        platform_id = "WinServerLocal"
        mock_platform = {
            "id": "WinServerLocal",
            "name": "Windows Server Local", 
            "platformType": "Regular",
            "active": True,
            "systemType": "Windows",
            "details": {
                "credentialsManagementPolicy": {
                    "change": "on",
                    "reconcile": "on",
                    "verify": "on"
                },
                "sessionManagementPolicy": {
                    "requirePrivilegedSessionMonitoring": True,
                    "recordPrivilegedSession": True
                },
                "privilegedAccessWorkflows": {
                    "requireUsersToSpecifyReasonForAccess": False,
                    "requireDualControlPasswordAccessApproval": False
                }
            }
        }
        
        with patch.object(platform_server, '_make_api_request', return_value=mock_platform):
            result = await platform_server.get_platform_details(platform_id)
            assert result == mock_platform

    @pytest.mark.asyncio
    async def test_get_platform_details_with_invalid_id(self, platform_server):
        """Test get_platform_details with invalid platform ID"""
        platform_id = "NonExistentPlatform"
        
        with patch.object(platform_server, '_make_api_request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_request.side_effect = httpx.HTTPStatusError(
                "404 Not Found", request=Mock(), response=mock_response
            )
            
            with pytest.raises(Exception):
                await platform_server.get_platform_details(platform_id)

    @pytest.mark.asyncio
    async def test_list_platforms_empty_result(self, platform_server):
        """Test list_platforms when no platforms are found"""
        with patch.object(platform_server, '_make_api_request', return_value={"Platforms": []}):
            result = await platform_server.list_platforms()
            assert result == []

    @pytest.mark.asyncio
    async def test_list_platforms_api_error_handling(self, platform_server):
        """Test list_platforms error handling"""
        with patch.object(platform_server, '_make_api_request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 403
            mock_request.side_effect = httpx.HTTPStatusError(
                "403 Forbidden", request=Mock(), response=mock_response
            )
            
            with pytest.raises(Exception):
                await platform_server.list_platforms()

    @pytest.mark.asyncio
    async def test_platform_management_concurrent_calls(self, platform_server):
        """Test concurrent platform management calls"""
        with patch.object(platform_server, '_make_api_request') as mock_request:
            mock_request.return_value = {"Platforms": []}
            
            # Make concurrent platform management requests
            tasks = [
                platform_server.list_platforms(),
                platform_server.list_platforms(search="Windows"),
                platform_server.list_platforms(active=True)
            ]
            
            results = await asyncio.gather(*tasks)
            assert len(results) == 3
            assert mock_request.call_count == 3

    @pytest.mark.asyncio
    async def test_list_platforms_comprehensive(self, platform_server):
        """Comprehensive test for list_platforms functionality"""
        mock_platforms = [
            {
                "id": "WinServerLocal",
                "name": "Windows Server Local",
                "platformType": "Regular",
                "active": True,
                "systemType": "Windows",
                "description": "Windows Server Local Accounts"
            },
            {
                "id": "UnixSSH",
                "name": "Unix via SSH",
                "platformType": "Regular", 
                "active": True,
                "systemType": "Unix",
                "description": "Unix accounts accessed via SSH"
            },
            {
                "id": "OracleDB",
                "name": "Oracle Database",
                "platformType": "Database",
                "active": False,
                "systemType": "Database",
                "description": "Oracle Database accounts"
            }
        ]
        
        with patch.object(platform_server, '_make_api_request', return_value={"Platforms": mock_platforms}):
            # Test without filters
            result = await platform_server.list_platforms()
            assert len(result) == 3
            assert result[0]["id"] == "WinServerLocal"
            assert result[1]["systemType"] == "Unix"
            
            # Test with search filter
            result = await platform_server.list_platforms(search="Windows")
            assert len(result) == 3  # Mock returns all, but request should have search param
            
            # Test with active filter
            result = await platform_server.list_platforms(active=True)
            assert len(result) == 3
            
            # Test with system type filter
            result = await platform_server.list_platforms(system_type="Windows")
            assert len(result) == 3

    @pytest.mark.asyncio
    async def test_get_platform_details_comprehensive(self, platform_server):
        """Comprehensive test for get_platform_details functionality"""
        platform_id = "WinServerLocal"
        mock_platform_details = {
            "id": "WinServerLocal",
            "name": "Windows Server Local",
            "platformType": "Regular",
            "active": True,
            "systemType": "Windows",
            "description": "Windows Server Local Accounts",
            "details": {
                "credentialsManagementPolicy": {
                    "change": "on",
                    "changeFrequency": 90,
                    "reconcile": "on",
                    "verify": "on",
                    "verifyFrequency": 7
                },
                "sessionManagementPolicy": {
                    "requirePrivilegedSessionMonitoring": True,
                    "recordPrivilegedSession": True,
                    "psmServerID": "PSM_SERVER"
                },
                "privilegedAccessWorkflows": {
                    "requireUsersToSpecifyReasonForAccess": False,
                    "requireDualControlPasswordAccessApproval": False,
                    "enforceCheckinCheckoutExclusiveAccess": True
                },
                "connectionComponents": [
                    {
                        "id": "PSM-RDP",
                        "name": "PSM-RDP",
                        "enabled": True
                    }
                ]
            }
        }
        
        with patch.object(platform_server, '_make_api_request', return_value=mock_platform_details):
            result = await platform_server.get_platform_details(platform_id)
            
            assert result["id"] == platform_id
            assert result["name"] == "Windows Server Local"
            assert result["details"]["credentialsManagementPolicy"]["change"] == "on"
            assert result["details"]["sessionManagementPolicy"]["requirePrivilegedSessionMonitoring"] is True
            assert len(result["details"]["connectionComponents"]) == 1

    @pytest.mark.asyncio
    async def test_platform_api_responses(self, platform_server):
        """Test platform APIs handle different response formats"""
        # Test response with 'Platforms' field
        platforms_response = {"Platforms": [{"id": "test1"}]}
        with patch.object(platform_server, '_make_api_request', return_value=platforms_response):
            result = await platform_server.list_platforms()
            assert len(result) == 1
            assert result[0]["id"] == "test1"
        
        # Test response with 'value' field (fallback)
        value_response = {"value": [{"id": "test2"}]}
        with patch.object(platform_server, '_make_api_request', return_value=value_response):
            result = await platform_server.list_platforms()
            assert len(result) == 1
            assert result[0]["id"] == "test2"
        
        # Test empty response
        empty_response = {}
        with patch.object(platform_server, '_make_api_request', return_value=empty_response):
            result = await platform_server.list_platforms()
            assert result == []

    @pytest.mark.asyncio
    async def test_platform_error_scenarios(self, platform_server):
        """Test platform management error handling"""
        # Test 404 error for non-existent platform
        with patch.object(platform_server, '_make_api_request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_request.side_effect = httpx.HTTPStatusError(
                "404 Not Found", request=Mock(), response=mock_response
            )
            
            with pytest.raises(Exception):
                await platform_server.get_platform_details("NonExistentPlatform")
        
        # Test 403 error for insufficient permissions
        with patch.object(platform_server, '_make_api_request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 403
            mock_request.side_effect = httpx.HTTPStatusError(
                "403 Forbidden", request=Mock(), response=mock_response
            )
            
            with pytest.raises(Exception):
                await platform_server.list_platforms()

    def test_platform_tools_in_available_tools(self, platform_server):
        """Test that platform tools are included in available tools list"""
        tools = platform_server.get_available_tools()
        assert "list_platforms" in tools
        assert "get_platform_details" in tools
        
        # Verify ordering and completeness
        expected_tools = [
            "list_accounts", "get_account_details", "search_accounts",
            "list_safes", "get_safe_details",
            "list_platforms", "get_platform_details", "import_platform_package"
        ]
        for tool in expected_tools:
            assert tool in tools

    @pytest.mark.asyncio
    async def test_platform_parameter_handling(self, platform_server):
        """Test platform methods handle parameters correctly"""
        with patch.object(platform_server, '_make_api_request') as mock_request:
            mock_request.return_value = {"Platforms": []}
            
            # Test boolean parameter conversion
            await platform_server.list_platforms(active=True)
            args, kwargs = mock_request.call_args
            assert kwargs['params']['active'] == 'true'
            
            await platform_server.list_platforms(active=False)
            args, kwargs = mock_request.call_args
            assert kwargs['params']['active'] == 'false'
            
            # Test None parameter handling
            await platform_server.list_platforms(active=None)
            args, kwargs = mock_request.call_args
            assert 'active' not in kwargs['params']
            
            # Test multiple parameters
            await platform_server.list_platforms(search="test", system_type="Windows", active=True)
            args, kwargs = mock_request.call_args
            expected_params = {"search": "test", "systemType": "Windows", "active": "true"}
            assert kwargs['params'] == expected_params

    @pytest.mark.asyncio 
    async def test_platform_logging(self, platform_server):
        """Test that platform operations log appropriately"""
        with patch.object(platform_server, '_make_api_request', return_value={"Platforms": []}):
            with patch.object(platform_server.logger, 'info') as mock_log:
                await platform_server.list_platforms(search="test")
                mock_log.assert_called_with("Listing platforms with filters: {'search': 'test'}")
        
        with patch.object(platform_server, '_make_api_request', return_value={}):
            with patch.object(platform_server.logger, 'info') as mock_log:
                await platform_server.get_platform_details("TestPlatform")
                mock_log.assert_called_with("Getting details for platform ID: TestPlatform")

    @pytest.mark.asyncio
    async def test_import_platform_package_with_file_path(self, platform_server):
        """Test import_platform_package with file path"""
        mock_platform_file = "/tmp/test_platform.zip"
        mock_file_content = b"PK\x03\x04test_zip_content"  # Mock ZIP file content
        expected_b64 = base64.b64encode(mock_file_content).decode('utf-8')
        mock_response = {"PlatformID": "ImportedPlatform123"}
        
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=mock_file_content)), \
             patch.object(platform_server, '_make_api_request', return_value=mock_response):
            
            result = await platform_server.import_platform_package(mock_platform_file)
            
            # Verify the result
            assert result == mock_response
            assert result["PlatformID"] == "ImportedPlatform123"
            
            # Verify the API call was made correctly
            platform_server._make_api_request.assert_called_once_with(
                "POST", "Platforms/Import", json={"ImportFile": expected_b64}
            )

    @pytest.mark.asyncio
    async def test_import_platform_package_with_bytes(self, platform_server):
        """Test import_platform_package with bytes content"""
        mock_file_content = b"PK\x03\x04test_zip_content"
        expected_b64 = base64.b64encode(mock_file_content).decode('utf-8')
        mock_response = {"PlatformID": "ImportedPlatform456"}
        
        with patch.object(platform_server, '_make_api_request', return_value=mock_response):
            result = await platform_server.import_platform_package(mock_file_content)
            
            assert result == mock_response
            platform_server._make_api_request.assert_called_once_with(
                "POST", "Platforms/Import", json={"ImportFile": expected_b64}
            )

    @pytest.mark.asyncio
    async def test_import_platform_package_file_not_found(self, platform_server):
        """Test import_platform_package with non-existent file"""
        non_existent_file = "/tmp/does_not_exist.zip"
        
        with patch('os.path.exists', return_value=False):
            with pytest.raises(ValueError, match="Platform package file not found"):
                await platform_server.import_platform_package(non_existent_file)

    @pytest.mark.asyncio
    async def test_import_platform_package_invalid_input_type(self, platform_server):
        """Test import_platform_package with invalid input type"""
        with pytest.raises(ValueError, match="platform_package_file must be either a file path"):
            await platform_server.import_platform_package(123)  # Invalid type

    @pytest.mark.asyncio
    async def test_import_platform_package_file_too_large(self, platform_server):
        """Test import_platform_package with file exceeding 20MB limit"""
        # Create mock file content larger than 20MB
        large_content = b"x" * (21 * 1024 * 1024)  # 21MB
        
        with pytest.raises(ValueError, match="Platform package file is too large"):
            await platform_server.import_platform_package(large_content)

    @pytest.mark.asyncio
    async def test_import_platform_package_max_size_allowed(self, platform_server):
        """Test import_platform_package with exactly 20MB file (should succeed)"""
        # Create mock file content exactly 20MB
        max_content = b"x" * (20 * 1024 * 1024)  # 20MB
        expected_b64 = base64.b64encode(max_content).decode('utf-8')
        mock_response = {"PlatformID": "LargePlatform"}
        
        with patch.object(platform_server, '_make_api_request', return_value=mock_response):
            result = await platform_server.import_platform_package(max_content)
            
            assert result == mock_response
            platform_server._make_api_request.assert_called_once_with(
                "POST", "Platforms/Import", json={"ImportFile": expected_b64}
            )

    @pytest.mark.asyncio
    async def test_import_platform_package_api_error(self, platform_server):
        """Test import_platform_package with API error"""
        mock_file_content = b"PK\x03\x04test_zip_content"
        
        with patch.object(platform_server, '_make_api_request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 400
            mock_request.side_effect = httpx.HTTPStatusError(
                "400 Bad Request", request=Mock(), response=mock_response
            )
            
            with pytest.raises(Exception):
                await platform_server.import_platform_package(mock_file_content)

    @pytest.mark.asyncio
    async def test_import_platform_package_logging(self, platform_server):
        """Test that import_platform_package logs appropriately"""
        mock_file_content = b"PK\x03\x04test_zip_content"
        mock_response = {"PlatformID": "TestPlatform"}
        
        with patch.object(platform_server, '_make_api_request', return_value=mock_response), \
             patch.object(platform_server.logger, 'info') as mock_log:
            
            await platform_server.import_platform_package(mock_file_content)
            
            mock_log.assert_called_with(f"Importing platform package ({len(mock_file_content)} bytes)")

    @pytest.mark.asyncio
    async def test_import_platform_package_comprehensive(self, platform_server):
        """Comprehensive test for import_platform_package functionality"""
        # Test with various file sizes and types
        test_cases = [
            (b"small_content", "SmallPlatform"),
            (b"x" * 1024, "MediumPlatform"),  # 1KB
            (b"x" * (1024 * 1024), "LargePlatform"),  # 1MB
        ]
        
        for content, platform_id in test_cases:
            mock_response = {"PlatformID": platform_id}
            expected_b64 = base64.b64encode(content).decode('utf-8')
            
            with patch.object(platform_server, '_make_api_request', return_value=mock_response):
                result = await platform_server.import_platform_package(content)
                
                assert result["PlatformID"] == platform_id
                platform_server._make_api_request.assert_called_with(
                    "POST", "Platforms/Import", json={"ImportFile": expected_b64}
                )
