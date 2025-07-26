import pytest
import os
from unittest.mock import Mock, patch
from src.mcp_privilege_cloud.exceptions import AuthenticationError
from src.mcp_privilege_cloud.server import CyberArkMCPServer, CyberArkAPIError


class TestAuthentication:
    """Test cases for CyberArk API token authentication (now SDK-based)"""

    @pytest.fixture
    def server(self):
        """Create server instance for testing"""
        # Mock environment variables needed for SDK authentication - simplified to only required vars
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
                server.accounts_service = Mock()
                server.safes_service = Mock()
                server.platforms_service = Mock()
                
                yield server

    @pytest.mark.auth
    def test_server_initialization_with_sdk(self, server):
        """Test that server initializes with SDK authenticator"""
        assert server.sdk_authenticator is not None
        assert hasattr(server, 'accounts_service')
        assert hasattr(server, 'safes_service')
        assert hasattr(server, 'platforms_service')

    @pytest.mark.auth
    def test_server_from_environment(self):
        """Test server creation from environment variables"""
        with patch.dict('os.environ', {
            'CYBERARK_CLIENT_ID': 'test-client',
            'CYBERARK_CLIENT_SECRET': 'test-secret'
        }):
            with patch('src.mcp_privilege_cloud.server.CyberArkSDKAuthenticator') as mock_sdk_auth_class:
                # Mock the entire authentication chain
                mock_sdk_auth = Mock()
                mock_sdk_auth.get_authenticated_client.side_effect = TypeError("Mock error")
                mock_sdk_auth_class.from_environment.return_value = mock_sdk_auth
                
                server = CyberArkMCPServer.from_environment()
                assert server.sdk_authenticator is not None
                # Services should be None due to mock error
                assert server.accounts_service is None
                assert server.safes_service is None
                assert server.platforms_service is None

    @pytest.mark.auth  
    def test_server_missing_client_id_env_var(self):
        """Test server creation fails when CYBERARK_CLIENT_ID is missing"""
        with patch.dict('os.environ', {
            'CYBERARK_CLIENT_SECRET': 'test-secret'
        }, clear=True):
            with pytest.raises(ValueError, match="CYBERARK_CLIENT_ID environment variable is required"):
                CyberArkMCPServer.from_environment()
    
    @pytest.mark.auth  
    def test_server_missing_client_secret_env_var(self):
        """Test server creation fails when CYBERARK_CLIENT_SECRET is missing"""
        with patch.dict('os.environ', {
            'CYBERARK_CLIENT_ID': 'test-client'
        }, clear=True):
            with pytest.raises(ValueError, match="CYBERARK_CLIENT_SECRET environment variable is required"):
                CyberArkMCPServer.from_environment()


class TestServerCore:
    """Test cases for CyberArk MCP Server core functionality using SDK implementation"""

    @pytest.fixture
    def server_mock_config(self):
        """Mock configuration for testing"""
        return {
            "client_id": "test-client",
            "client_secret": "test-secret",
            "timeout": 30
        }

    @pytest.fixture  
    def server_instance(self, server_mock_config):
        """Create server instance for testing"""
        # Mock environment variables needed for SDK authentication - simplified
        with patch.dict('os.environ', {
            'CYBERARK_CLIENT_ID': server_mock_config['client_id'],
            'CYBERARK_CLIENT_SECRET': server_mock_config['client_secret']
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
                
                return server

    def test_server_initialization(self, server_instance, server_mock_config):
        """Test that server initializes with correct parameters"""
        assert server_instance.sdk_authenticator is not None

    def test_server_from_environment(self):
        """Test server initialization from environment variables"""
        env_vars = {
            "CYBERARK_CLIENT_ID": "env-client",
            "CYBERARK_CLIENT_SECRET": "env-secret"
        }
        
        with patch.dict(os.environ, env_vars):
            with patch('src.mcp_privilege_cloud.server.CyberArkSDKAuthenticator') as mock_sdk_auth_class:
                # Mock the entire authentication chain to avoid service initialization errors
                mock_sdk_auth = Mock()
                mock_sdk_auth.get_authenticated_client.side_effect = TypeError("Mock error")
                mock_sdk_auth_class.from_environment.return_value = mock_sdk_auth
                
                server = CyberArkMCPServer.from_environment()
                assert server.sdk_authenticator is not None
                # Services should be None due to mock error
                assert server.accounts_service is None

    def test_server_from_environment_missing_required(self):
        """Test server initialization with missing required environment variables"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="CYBERARK_CLIENT_ID"):
                CyberArkMCPServer.from_environment()

    def test_tool_registration(self, server_instance):
        """Test that required tools are registered"""
        tools = server_instance.get_available_tools()
        expected_tools = [
            "list_accounts",
            "search_accounts", 
            "list_safes",
            "list_platforms",
            "create_account",
            "change_account_password", 
            "set_next_password",
            "verify_account_password",
            "reconcile_account_password",
            "import_platform_package"
        ]
        
        for tool_name in expected_tools:
            assert tool_name in tools

    @pytest.mark.asyncio
    async def test_server_sdk_integration(self, server_instance):
        """Test that server integrates properly with SDK authenticator"""
        # Test that SDK authenticator is properly initialized
        assert server_instance.sdk_authenticator is not None
        
        # Test that services can be initialized
        accounts_service = server_instance.accounts_service
        assert accounts_service is not None
        
        safes_service = server_instance.safes_service
        assert safes_service is not None
        
        platforms_service = server_instance.platforms_service
        assert platforms_service is not None

    @pytest.mark.asyncio
    async def test_server_health_check(self, server_instance):
        """Test server health check functionality"""
        # Mock the platforms service to return successful result for health check
        mock_platform = Mock()
        mock_platform.model_dump.return_value = {"id": "TestPlatform", "name": "Test Platform"}
        
        # Platforms service returns a direct list of platform objects
        server_instance.platforms_service.list_platforms.return_value = [mock_platform]
        
        result = await server_instance.health_check()
        
        assert result["status"] == "healthy"
        assert "message" in result
        assert "platform_count" in result
        assert result["platform_count"] == 1

    @pytest.mark.asyncio
    async def test_server_accounts_service_integration(self, server_instance):
        """Test server accounts service integration with SDK"""
        # Mock the accounts service to return test data in SDK format
        mock_account = Mock()
        mock_account.model_dump.return_value = {"id": "test1", "userName": "testuser"}
        
        mock_page = Mock()
        mock_page.items = [mock_account]
        
        server_instance.accounts_service.list_accounts.return_value = [mock_page]
        
        result = await server_instance.list_accounts()
        
        # Verify the service was called and results returned
        server_instance.accounts_service.list_accounts.assert_called_once()
        assert len(result) == 1
        assert result[0]["id"] == "test1"

    @pytest.mark.asyncio
    async def test_server_platforms_service_integration(self, server_instance):
        """Test server platforms service integration with SDK"""
        # Mock the platforms service to return test data in SDK format (direct list, not pages)
        mock_platform = Mock()
        mock_platform.model_dump.return_value = {"id": "TestPlatform", "name": "Test Platform"}
        
        # Platforms service returns a direct list of platform objects
        server_instance.platforms_service.list_platforms.return_value = [mock_platform]
        
        result = await server_instance.list_platforms()
        
        # Verify the service was called and results returned
        server_instance.platforms_service.list_platforms.assert_called_once()
        assert len(result) == 1
        assert result[0]["id"] == "TestPlatform"