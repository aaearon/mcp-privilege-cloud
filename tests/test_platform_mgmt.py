import pytest
from unittest.mock import Mock, AsyncMock, patch
import os

from src.cyberark_mcp.server import CyberArkMCPServer
from src.cyberark_mcp.auth import CyberArkAuthenticator


class TestPlatformManagement:
    """Dedicated test class for platform management functionality"""

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

    @pytest.mark.asyncio
    async def test_list_platforms_comprehensive(self, server):
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
        
        with patch.object(server, '_make_api_request', return_value={"Platforms": mock_platforms}):
            # Test without filters
            result = await server.list_platforms()
            assert len(result) == 3
            assert result[0]["id"] == "WinServerLocal"
            assert result[1]["systemType"] == "Unix"
            
            # Test with search filter
            result = await server.list_platforms(search="Windows")
            assert len(result) == 3  # Mock returns all, but request should have search param
            
            # Test with active filter
            result = await server.list_platforms(active=True)
            assert len(result) == 3
            
            # Test with system type filter
            result = await server.list_platforms(system_type="Windows")
            assert len(result) == 3

    @pytest.mark.asyncio
    async def test_get_platform_details_comprehensive(self, server):
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
        
        with patch.object(server, '_make_api_request', return_value=mock_platform_details):
            result = await server.get_platform_details(platform_id)
            
            assert result["id"] == platform_id
            assert result["name"] == "Windows Server Local"
            assert result["details"]["credentialsManagementPolicy"]["change"] == "on"
            assert result["details"]["sessionManagementPolicy"]["requirePrivilegedSessionMonitoring"] is True
            assert len(result["details"]["connectionComponents"]) == 1

    @pytest.mark.asyncio
    async def test_platform_api_responses(self, server):
        """Test platform APIs handle different response formats"""
        # Test response with 'Platforms' field
        platforms_response = {"Platforms": [{"id": "test1"}]}
        with patch.object(server, '_make_api_request', return_value=platforms_response):
            result = await server.list_platforms()
            assert len(result) == 1
            assert result[0]["id"] == "test1"
        
        # Test response with 'value' field (fallback)
        value_response = {"value": [{"id": "test2"}]}
        with patch.object(server, '_make_api_request', return_value=value_response):
            result = await server.list_platforms()
            assert len(result) == 1
            assert result[0]["id"] == "test2"
        
        # Test empty response
        empty_response = {}
        with patch.object(server, '_make_api_request', return_value=empty_response):
            result = await server.list_platforms()
            assert result == []

    @pytest.mark.asyncio
    async def test_platform_error_scenarios(self, server):
        """Test platform management error handling"""
        import httpx
        
        # Test 404 error for non-existent platform
        with patch.object(server, '_make_api_request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_request.side_effect = httpx.HTTPStatusError(
                "404 Not Found", request=Mock(), response=mock_response
            )
            
            with pytest.raises(Exception):
                await server.get_platform_details("NonExistentPlatform")
        
        # Test 403 error for insufficient permissions
        with patch.object(server, '_make_api_request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 403
            mock_request.side_effect = httpx.HTTPStatusError(
                "403 Forbidden", request=Mock(), response=mock_response
            )
            
            with pytest.raises(Exception):
                await server.list_platforms()

    def test_platform_tools_in_available_tools(self, server):
        """Test that platform tools are included in available tools list"""
        tools = server.get_available_tools()
        assert "list_platforms" in tools
        assert "get_platform_details" in tools
        
        # Verify ordering and completeness
        expected_tools = [
            "list_accounts", "get_account_details", "search_accounts",
            "list_safes", "get_safe_details",
            "list_platforms", "get_platform_details"
        ]
        for tool in expected_tools:
            assert tool in tools

    @pytest.mark.asyncio
    async def test_platform_parameter_handling(self, server):
        """Test platform methods handle parameters correctly"""
        with patch.object(server, '_make_api_request') as mock_request:
            mock_request.return_value = {"Platforms": []}
            
            # Test boolean parameter conversion
            await server.list_platforms(active=True)
            args, kwargs = mock_request.call_args
            assert kwargs['params']['active'] == 'true'
            
            await server.list_platforms(active=False)
            args, kwargs = mock_request.call_args
            assert kwargs['params']['active'] == 'false'
            
            # Test None parameter handling
            await server.list_platforms(active=None)
            args, kwargs = mock_request.call_args
            assert 'active' not in kwargs['params']
            
            # Test multiple parameters
            await server.list_platforms(search="test", system_type="Windows", active=True)
            args, kwargs = mock_request.call_args
            expected_params = {"search": "test", "systemType": "Windows", "active": "true"}
            assert kwargs['params'] == expected_params

    @pytest.mark.asyncio 
    async def test_platform_logging(self, server):
        """Test that platform operations log appropriately"""
        with patch.object(server, '_make_api_request', return_value={"Platforms": []}):
            with patch.object(server.logger, 'info') as mock_log:
                await server.list_platforms(search="test")
                mock_log.assert_called_with("Listing platforms with filters: {'search': 'test'}")
        
        with patch.object(server, '_make_api_request', return_value={}):
            with patch.object(server.logger, 'info') as mock_log:
                await server.get_platform_details("TestPlatform")
                mock_log.assert_called_with("Getting details for platform ID: TestPlatform")