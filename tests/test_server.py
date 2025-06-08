import pytest
from unittest.mock import Mock, AsyncMock, patch
import os

from src.cyberark_mcp.server import CyberArkMCPServer
from src.cyberark_mcp.auth import CyberArkAuthenticator


class TestCyberArkMCPServer:
    """Test cases for CyberArk MCP Server"""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing"""
        return {
            "identity_tenant_id": "test-tenant",
            "client_id": "test-client",
            "client_secret": "test-secret",
            "subdomain": "test-subdomain",
            "timeout": 30
        }

    @pytest.fixture
    def mock_authenticator(self, mock_config):
        """Mock authenticator for testing"""
        auth = Mock(spec=CyberArkAuthenticator)
        auth.get_auth_header = AsyncMock(return_value={"Authorization": "Bearer test-token"})
        return auth

    @pytest.fixture
    def server(self, mock_authenticator, mock_config):
        """Create server instance for testing"""
        return CyberArkMCPServer(
            authenticator=mock_authenticator,
            subdomain=mock_config["subdomain"],
            timeout=mock_config["timeout"]
        )

    def test_server_initialization(self, server, mock_authenticator, mock_config):
        """Test that server initializes with correct parameters"""
        assert server.authenticator == mock_authenticator
        assert server.subdomain == mock_config["subdomain"]
        assert server.timeout == mock_config["timeout"]
        assert server.base_url == f"https://{mock_config['subdomain']}.privilegecloud.cyberark.cloud/PasswordVault/api"

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

    def test_get_api_url(self, server):
        """Test API URL construction"""
        endpoint = "Accounts"
        expected_url = "https://test-subdomain.privilegecloud.cyberark.cloud/PasswordVault/api/Accounts"
        assert server._get_api_url(endpoint) == expected_url

    async def test_make_api_request_success(self, server, mock_authenticator):
        """Test successful API request"""
        mock_response_data = {"value": [{"id": "123", "name": "test-account"}]}
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            result = await server._make_api_request("GET", "Accounts")
            
            assert result == mock_response_data
            mock_authenticator.get_auth_header.assert_called_once()
            mock_get.assert_called_once()

    async def test_make_api_request_with_params(self, server, mock_authenticator):
        """Test API request with query parameters"""
        params = {"safeName": "test-safe", "search": "admin"}
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {}
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            await server._make_api_request("GET", "Accounts", params=params)
            
            # Verify params were passed to the request
            call_args = mock_get.call_args
            assert call_args[1]['params'] == params

    async def test_make_api_request_http_error(self, server, mock_authenticator):
        """Test API request with HTTP error"""
        import httpx
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "404 Not Found", request=Mock(), response=Mock()
            )
            mock_get.return_value = mock_response
            
            with pytest.raises(Exception):  # Should raise appropriate exception
                await server._make_api_request("GET", "NonExistentEndpoint")

    async def test_make_api_request_network_error(self, server, mock_authenticator):
        """Test API request with network error"""
        import httpx
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.side_effect = httpx.ConnectError("Connection failed")
            
            with pytest.raises(Exception):  # Should raise appropriate exception
                await server._make_api_request("GET", "Accounts")

    def test_tool_registration(self, server):
        """Test that required tools are registered"""
        # This will test the actual tool registration once implemented
        tools = server.get_available_tools()
        expected_tools = [
            "list_accounts",
            "get_account_details", 
            "search_accounts",
            "list_safes",
            "get_safe_details"
        ]
        
        for tool_name in expected_tools:
            assert tool_name in tools

    async def test_list_accounts_tool(self, server):
        """Test list_accounts tool functionality"""
        mock_accounts = [
            {"id": "123", "name": "account1", "safeName": "safe1"},
            {"id": "456", "name": "account2", "safeName": "safe2"}
        ]
        
        with patch.object(server, '_make_api_request', return_value={"value": mock_accounts}):
            result = await server.list_accounts()
            assert result == mock_accounts

    async def test_list_accounts_with_filters(self, server):
        """Test list_accounts with filter parameters"""
        filters = {"safeName": "test-safe", "userName": "admin"}
        
        with patch.object(server, '_make_api_request') as mock_request:
            mock_request.return_value = {"value": []}
            await server.list_accounts(**filters)
            mock_request.assert_called_once_with("GET", "Accounts", params=filters)

    async def test_get_account_details_tool(self, server):
        """Test get_account_details tool functionality"""
        account_id = "123"
        mock_account = {"id": "123", "name": "test-account", "safeName": "test-safe"}
        
        with patch.object(server, '_make_api_request', return_value=mock_account):
            result = await server.get_account_details(account_id)
            assert result == mock_account

    async def test_search_accounts_tool(self, server):
        """Test search_accounts tool functionality"""
        search_params = {"keywords": "admin", "safeName": "test-safe"}
        mock_results = [{"id": "123", "name": "admin-account"}]
        
        with patch.object(server, '_make_api_request', return_value={"value": mock_results}):
            result = await server.search_accounts(**search_params)
            assert result == mock_results

    async def test_list_safes_tool(self, server):
        """Test list_safes tool functionality"""
        mock_safes = [
            {"safeName": "safe1", "description": "Test safe 1"},
            {"safeName": "safe2", "description": "Test safe 2"}
        ]
        
        with patch.object(server, '_make_api_request', return_value={"value": mock_safes}):
            result = await server.list_safes()
            assert result == mock_safes

    async def test_get_safe_details_tool(self, server):
        """Test get_safe_details tool functionality"""
        safe_name = "test-safe"
        mock_safe = {"safeName": "test-safe", "description": "Test safe", "location": "\\"}
        
        with patch.object(server, '_make_api_request', return_value=mock_safe):
            result = await server.get_safe_details(safe_name)
            assert result == mock_safe

    def test_error_handling_configuration(self, server):
        """Test that error handling is properly configured"""
        # Verify that server has appropriate error handling methods
        assert hasattr(server, '_handle_api_error')
        assert hasattr(server, '_log_error')

    async def test_authentication_refresh_on_401(self, server, mock_authenticator):
        """Test that authentication is refreshed on 401 errors"""
        import httpx
        
        # First call raises 401, second call succeeds
        call_count = 0
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                mock_response = Mock()
                mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                    "401 Unauthorized", request=Mock(), response=Mock()
                )
                return mock_response
            else:
                mock_response = Mock()
                mock_response.json.return_value = {"value": []}
                mock_response.raise_for_status.return_value = None
                return mock_response
        
        with patch('httpx.AsyncClient.get', side_effect=side_effect):
            result = await server._make_api_request("GET", "Accounts")
            # Should have called get_auth_header twice (initial + retry)
            assert mock_authenticator.get_auth_header.call_count >= 2

    def test_logging_configuration(self, server):
        """Test that logging is properly configured"""
        assert hasattr(server, 'logger')
        # Verify logger is configured for the correct module
        assert server.logger.name == 'src.cyberark_mcp.server'

    async def test_concurrent_requests(self, server):
        """Test that server can handle concurrent requests"""
        import asyncio
        
        with patch.object(server, '_make_api_request') as mock_request:
            mock_request.return_value = {"value": []}
            
            # Make multiple concurrent requests
            tasks = [
                server.list_accounts(),
                server.list_safes(),
                server.search_accounts(keywords="test")
            ]
            
            results = await asyncio.gather(*tasks)
            assert len(results) == 3
            assert mock_request.call_count == 3