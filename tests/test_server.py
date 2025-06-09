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
            "get_safe_details",
            "list_platforms",
            "get_platform_details"
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

    # Safe Management Tests
    
    @pytest.mark.asyncio
    async def test_list_safes_basic(self, server):
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
        
        with patch.object(server, '_make_api_request', return_value=mock_response):
            result = await server.list_safes()
            assert result == mock_safes
            assert len(result) == 2
            assert result[0]["safeName"] == "VaultInternal"
            assert result[1]["safeName"] == "HRSafe"

    @pytest.mark.asyncio
    async def test_list_safes_with_search(self, server):
        """Test list_safes with search parameter"""
        search_term = "HR"
        
        with patch.object(server, '_make_api_request') as mock_request:
            mock_request.return_value = {"value": [], "count": 0}
            await server.list_safes(search=search_term)
            mock_request.assert_called_once_with("GET", "Safes", params={"search": search_term})

    @pytest.mark.asyncio
    async def test_list_safes_with_pagination_params(self, server):
        """Test list_safes with pagination parameters"""
        params = {
            "search": "test",
            "offset": 10,
            "limit": 5,
            "sort": "safeName desc",
            "includeAccounts": True,
            "extendedDetails": False
        }
        
        with patch.object(server, '_make_api_request') as mock_request:
            mock_request.return_value = {"value": [], "count": 0}
            await server.list_safes(**params)
            mock_request.assert_called_once_with("GET", "Safes", params=params)

    @pytest.mark.asyncio
    async def test_list_safes_with_pagination_response(self, server):
        """Test list_safes with paginated response"""
        mock_response = {
            "value": [{"safeName": "TestSafe", "safeUrlId": "TestSafe"}],
            "count": 100,
            "nextLink": "api/safes?offset=25&limit=25&useCache=False"
        }
        
        with patch.object(server, '_make_api_request', return_value=mock_response):
            result = await server.list_safes(limit=25)
            assert result == mock_response["value"]
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_list_safes_empty_response(self, server):
        """Test list_safes with empty response"""
        mock_response = {"value": [], "count": 0}
        
        with patch.object(server, '_make_api_request', return_value=mock_response):
            result = await server.list_safes()
            assert result == []

    @pytest.mark.asyncio
    async def test_list_safes_no_value_field(self, server):
        """Test list_safes when API returns no 'value' field"""
        mock_response = {"count": 0}
        
        with patch.object(server, '_make_api_request', return_value=mock_response):
            result = await server.list_safes()
            assert result == []

    @pytest.mark.asyncio
    async def test_get_safe_details_basic(self, server):
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
        
        with patch.object(server, '_make_api_request', return_value=mock_safe):
            result = await server.get_safe_details(safe_name)
            assert result == mock_safe
            assert result["safeName"] == safe_name
            assert result["safeNumber"] == 687

    @pytest.mark.asyncio 
    async def test_get_safe_details_with_url_encoding(self, server):
        """Test get_safe_details with special characters requiring URL encoding"""
        safe_name = "My Safe With Spaces"
        expected_endpoint = f"Safes/{safe_name}"
        
        with patch.object(server, '_make_api_request') as mock_request:
            mock_request.return_value = {"safeName": safe_name}
            await server.get_safe_details(safe_name)
            mock_request.assert_called_once_with("GET", expected_endpoint, params=None)

    @pytest.mark.asyncio
    async def test_get_safe_details_with_query_params(self, server):
        """Test get_safe_details with query parameters"""
        safe_name = "TestSafe"
        params = {
            "includeAccounts": True,
            "useCache": False
        }
        
        with patch.object(server, '_make_api_request') as mock_request:
            mock_request.return_value = {"safeName": safe_name}
            await server.get_safe_details(safe_name, **params)
            mock_request.assert_called_once_with("GET", f"Safes/{safe_name}", params=params)

    @pytest.mark.asyncio
    async def test_get_safe_details_with_accounts(self, server):
        """Test get_safe_details with accounts included"""
        safe_name = "HRSafe"
        mock_safe = {
            "safeName": "HRSafe",
            "accounts": [
                {"id": "123", "name": "hr-admin"},
                {"id": "456", "name": "hr-user"}
            ]
        }
        
        with patch.object(server, '_make_api_request', return_value=mock_safe):
            result = await server.get_safe_details(safe_name, includeAccounts=True)
            assert result == mock_safe
            assert len(result["accounts"]) == 2

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

    # Platform Management Tests
    
    @pytest.mark.asyncio
    async def test_list_platforms_tool(self, server):
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
        
        with patch.object(server, '_make_api_request', return_value={"Platforms": mock_platforms}):
            result = await server.list_platforms()
            assert result == mock_platforms

    @pytest.mark.asyncio
    async def test_list_platforms_with_search(self, server):
        """Test list_platforms with search parameter"""
        search_term = "Windows"
        
        with patch.object(server, '_make_api_request') as mock_request:
            mock_request.return_value = {"Platforms": []}
            await server.list_platforms(search=search_term)
            mock_request.assert_called_once_with("GET", "Platforms", params={"search": search_term})

    @pytest.mark.asyncio
    async def test_list_platforms_with_active_filter(self, server):
        """Test list_platforms with active filter"""
        with patch.object(server, '_make_api_request') as mock_request:
            mock_request.return_value = {"Platforms": []}
            await server.list_platforms(active=True)
            mock_request.assert_called_once_with("GET", "Platforms", params={"active": "true"})

    @pytest.mark.asyncio
    async def test_list_platforms_with_system_type_filter(self, server):
        """Test list_platforms with system type filter"""
        system_type = "Windows"
        
        with patch.object(server, '_make_api_request') as mock_request:
            mock_request.return_value = {"Platforms": []}
            await server.list_platforms(system_type=system_type)
            mock_request.assert_called_once_with("GET", "Platforms", params={"systemType": system_type})

    @pytest.mark.asyncio
    async def test_list_platforms_with_multiple_filters(self, server):
        """Test list_platforms with multiple filter parameters"""
        filters = {"search": "Windows", "active": True, "systemType": "Windows"}
        expected_params = {"search": "Windows", "active": "true", "systemType": "Windows"}
        
        with patch.object(server, '_make_api_request') as mock_request:
            mock_request.return_value = {"Platforms": []}
            await server.list_platforms(**filters)
            mock_request.assert_called_once_with("GET", "Platforms", params=expected_params)

    @pytest.mark.asyncio
    async def test_get_platform_details_tool(self, server):
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
        
        with patch.object(server, '_make_api_request', return_value=mock_platform):
            result = await server.get_platform_details(platform_id)
            assert result == mock_platform

    @pytest.mark.asyncio
    async def test_get_platform_details_with_invalid_id(self, server):
        """Test get_platform_details with invalid platform ID"""
        platform_id = "NonExistentPlatform"
        
        import httpx
        with patch.object(server, '_make_api_request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_request.side_effect = httpx.HTTPStatusError(
                "404 Not Found", request=Mock(), response=mock_response
            )
            
            with pytest.raises(Exception):
                await server.get_platform_details(platform_id)

    @pytest.mark.asyncio
    async def test_list_platforms_empty_result(self, server):
        """Test list_platforms when no platforms are found"""
        with patch.object(server, '_make_api_request', return_value={"Platforms": []}):
            result = await server.list_platforms()
            assert result == []

    @pytest.mark.asyncio
    async def test_list_platforms_api_error_handling(self, server):
        """Test list_platforms error handling"""
        import httpx
        
        with patch.object(server, '_make_api_request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 403
            mock_request.side_effect = httpx.HTTPStatusError(
                "403 Forbidden", request=Mock(), response=mock_response
            )
            
            with pytest.raises(Exception):
                await server.list_platforms()

    @pytest.mark.asyncio
    async def test_platform_management_concurrent_calls(self, server):
        """Test concurrent platform management calls"""
        import asyncio
        
        with patch.object(server, '_make_api_request') as mock_request:
            mock_request.return_value = {"Platforms": []}
            
            # Make concurrent platform management requests
            tasks = [
                server.list_platforms(),
                server.list_platforms(search="Windows"),
                server.list_platforms(active=True)
            ]
            
            results = await asyncio.gather(*tasks)
            assert len(results) == 3
            assert mock_request.call_count == 3