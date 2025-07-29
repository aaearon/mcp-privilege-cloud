import pytest
import os
from unittest.mock import Mock, patch
from mcp_privilege_cloud.exceptions import AuthenticationError
from mcp_privilege_cloud.server import CyberArkMCPServer, CyberArkAPIError


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
            with patch('mcp_privilege_cloud.server.CyberArkSDKAuthenticator') as mock_sdk_auth_class:
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
            with patch('mcp_privilege_cloud.server.CyberArkSDKAuthenticator') as mock_sdk_auth_class:
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
            with patch('mcp_privilege_cloud.server.CyberArkSDKAuthenticator') as mock_sdk_auth_class:
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
            with patch('mcp_privilege_cloud.server.CyberArkSDKAuthenticator') as mock_sdk_auth_class:
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
        # Server method returns list of Pydantic models, not dictionaries
        assert result[0] == mock_account

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

    @pytest.mark.asyncio
    async def test_server_export_platform_integration(self, server_instance):
        """Test server export_platform method integration with SDK"""
        platform_id = "WinServerLocal"
        output_folder = "/tmp/exports"
        
        # Mock the platforms service export_platform method
        server_instance.platforms_service.export_platform.return_value = None
        
        result = await server_instance.export_platform(platform_id, output_folder)
        
        # Verify the service was called correctly
        server_instance.platforms_service.export_platform.assert_called_once()
        call_args = server_instance.platforms_service.export_platform.call_args[1]
        assert call_args['export_platform'].platform_id == platform_id
        assert call_args['export_platform'].output_folder == output_folder
        
        # Verify return format
        assert result['platform_id'] == platform_id
        assert result['output_folder'] == output_folder
        assert result['status'] == "exported"

    @pytest.mark.asyncio
    async def test_server_duplicate_target_platform_integration(self, server_instance):
        """Test server duplicate_target_platform method integration with SDK"""
        target_platform_id = 123
        name = "Duplicated Platform"
        description = "Test duplicate"
        
        # Mock the platforms service to return duplicated platform info
        mock_duplicated = Mock()
        mock_duplicated.model_dump.return_value = {
            "target_platform_id": 456,
            "name": name,
            "description": description,
            "status": "duplicated"
        }
        server_instance.platforms_service.duplicate_target_platform.return_value = mock_duplicated
        
        result = await server_instance.duplicate_target_platform(target_platform_id, name, description)
        
        # Verify the service was called correctly
        server_instance.platforms_service.duplicate_target_platform.assert_called_once()
        call_args = server_instance.platforms_service.duplicate_target_platform.call_args[1]
        assert call_args['duplicate_target_platform'].target_platform_id == target_platform_id
        assert call_args['duplicate_target_platform'].name == name
        assert call_args['duplicate_target_platform'].description == description
        
        # Verify return format - server method returns Pydantic model, not dictionary
        assert result == mock_duplicated

    @pytest.mark.asyncio
    async def test_server_activate_target_platform_integration(self, server_instance):
        """Test server activate_target_platform method integration with SDK"""
        target_platform_id = 123
        
        # Mock the platforms service activate method
        server_instance.platforms_service.activate_target_platform.return_value = None
        
        result = await server_instance.activate_target_platform(target_platform_id)
        
        # Verify the service was called correctly
        server_instance.platforms_service.activate_target_platform.assert_called_once()
        call_args = server_instance.platforms_service.activate_target_platform.call_args[1]
        assert call_args['activate_target_platform'].target_platform_id == target_platform_id
        
        # Verify return format
        assert result['target_platform_id'] == target_platform_id
        assert result['status'] == "activated"

    @pytest.mark.asyncio
    async def test_server_deactivate_target_platform_integration(self, server_instance):
        """Test server deactivate_target_platform method integration with SDK"""
        target_platform_id = 123
        
        # Mock the platforms service deactivate method
        server_instance.platforms_service.deactivate_target_platform.return_value = None
        
        result = await server_instance.deactivate_target_platform(target_platform_id)
        
        # Verify the service was called correctly
        server_instance.platforms_service.deactivate_target_platform.assert_called_once()
        call_args = server_instance.platforms_service.deactivate_target_platform.call_args[1]
        assert call_args['deactivate_target_platform'].target_platform_id == target_platform_id
        
        # Verify return format
        assert result['target_platform_id'] == target_platform_id
        assert result['status'] == "deactivated"

    @pytest.mark.asyncio
    async def test_server_delete_target_platform_integration(self, server_instance):
        """Test server delete_target_platform method integration with SDK"""
        target_platform_id = 123
        
        # Mock the platforms service delete method
        server_instance.platforms_service.delete_target_platform.return_value = None
        
        result = await server_instance.delete_target_platform(target_platform_id)
        
        # Verify the service was called correctly
        server_instance.platforms_service.delete_target_platform.assert_called_once()
        call_args = server_instance.platforms_service.delete_target_platform.call_args[1]
        assert call_args['delete_target_platform'].target_platform_id == target_platform_id
        
        # Verify return format
        assert result['target_platform_id'] == target_platform_id
        assert result['status'] == "deleted"

    async def test_server_get_platform_statistics_integration(self, server_instance):
        """Test server get_platform_statistics method integration with SDK"""
        # Mock platforms_stats response with proper pydantic model structure
        from unittest.mock import MagicMock
        
        mock_stats = MagicMock()
        mock_stats.model_dump.return_value = {
            'platforms_count': 15,
            'platforms_count_by_type': {
                'regular': 12,
                'rotational_group': 2,
                'group': 1
            }
        }
        
        # Mock the platforms service stats method
        server_instance.platforms_service.platforms_stats.return_value = mock_stats
        
        result = await server_instance.get_platform_statistics()
        
        # Verify the service was called correctly
        server_instance.platforms_service.platforms_stats.assert_called_once()
        
        # Verify return format - server method returns Pydantic model, not dictionary
        assert result == mock_stats

    async def test_server_get_target_platform_statistics_integration(self, server_instance):
        """Test server get_target_platform_statistics method integration with SDK"""
        # Mock target_platforms_stats response with proper pydantic model structure
        from unittest.mock import MagicMock
        
        mock_stats = MagicMock()
        mock_stats.model_dump.return_value = {
            'target_platforms_count': 8,
            'target_platforms_count_by_system_type': {
                'Windows': 3,
                'Unix': 2,
                'Oracle': 2,
                'Database': 1
            }
        }
        
        # Mock the platforms service stats method
        server_instance.platforms_service.target_platforms_stats.return_value = mock_stats
        
        result = await server_instance.get_target_platform_statistics()
        
        # Verify the service was called correctly
        server_instance.platforms_service.target_platforms_stats.assert_called_once()
        
        # Verify return format - server method returns Pydantic model, not dictionary
        assert result == mock_stats


class TestSessionManagement:
    """Test cases for Session Monitoring functionality using ArkSMService"""

    @pytest.fixture
    def server_with_sm_service(self):
        """Create server instance with mocked SM service for testing"""
        # Mock environment variables needed for SDK authentication
        with patch.dict('os.environ', {
            'CYBERARK_CLIENT_ID': 'test-client',
            'CYBERARK_CLIENT_SECRET': 'test-secret'
        }):
            # Mock the SDK components to prevent actual authentication during tests
            with patch('mcp_privilege_cloud.server.CyberArkSDKAuthenticator') as mock_sdk_auth_class:
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
                
                # Mock the SM service that we'll add
                server.sm_service = Mock()
                
                return server

    async def test_list_sessions_basic(self, server_with_sm_service):
        """Test list_sessions method basic functionality"""
        server_instance = server_with_sm_service
        
        # Mock sessions response
        from unittest.mock import MagicMock
        
        mock_page = MagicMock()
        mock_session = MagicMock()
        mock_session.model_dump.return_value = {
            'session_id': '5e62bdb8-cd81-42b8-ac72-1e06bf9c496d',
            'protocol': 'SSH',
            'start_time': '2024-01-15T10:30:00Z',
            'duration': '00:15:30',
            'user': 'admin@example.com',
            'target': '10.0.0.100'
        }
        mock_page.items = [mock_session]
        
        # Mock the sm service list_sessions_by method
        server_instance.sm_service.list_sessions_by.return_value = [mock_page]
        
        result = await server_instance.list_sessions()
        
        # Verify the service was called correctly
        server_instance.sm_service.list_sessions_by.assert_called_once()
        
        # Verify return format - server method returns list of Pydantic models, not dictionaries
        assert len(result) == 1
        assert result[0] == mock_session

    async def test_list_sessions_with_filter(self, server_with_sm_service):
        """Test list_sessions_by_filter method with advanced filtering"""
        server_instance = server_with_sm_service
        
        # Mock filtered sessions response
        from unittest.mock import MagicMock
        
        mock_page = MagicMock()
        mock_session1 = MagicMock()
        mock_session1.model_dump.return_value = {
            'session_id': '5e62bdb8-cd81-42b8-ac72-1e06bf9c496d',
            'protocol': 'SSH',
            'start_time': '2024-01-15T10:30:00Z',
            'duration': '00:15:30'
        }
        mock_session2 = MagicMock()
        mock_session2.model_dump.return_value = {
            'session_id': '7f73cdc9-de92-53c9-bd83-2f17cg0d507e',
            'protocol': 'RDP',
            'start_time': '2024-01-15T11:00:00Z',
            'duration': '00:22:45'
        }
        mock_page.items = [mock_session1, mock_session2]
        
        # Mock the sm service list_sessions_by method
        server_instance.sm_service.list_sessions_by.return_value = [mock_page]
        
        filter_query = 'startTime ge 2024-01-15T08:00:00Z AND protocol IN SSH,RDP'
        result = await server_instance.list_sessions_by_filter(search=filter_query)
        
        # Verify the service was called with correct filter
        server_instance.sm_service.list_sessions_by.assert_called_once()
        
        # Verify return format - server method returns list of Pydantic models, not dictionaries
        assert len(result) == 2
        assert result[0] == mock_session1
        assert result[1] == mock_session2

    async def test_get_session_details(self, server_with_sm_service):
        """Test get_session_details method"""
        server_instance = server_with_sm_service
        
        # Mock session details response
        from unittest.mock import MagicMock
        
        mock_session = MagicMock()
        mock_session.model_dump.return_value = {
            'session_id': '5e62bdb8-cd81-42b8-ac72-1e06bf9c496d',
            'protocol': 'SSH',
            'start_time': '2024-01-15T10:30:00Z',
            'end_time': '2024-01-15T10:45:30Z',
            'duration': '00:15:30',
            'user': 'admin@example.com',
            'target': '10.0.0.100',
            'account_name': 'root',
            'safe_name': 'Unix-Servers'
        }
        
        # Mock the sm service session method
        server_instance.sm_service.session.return_value = mock_session
        
        session_id = '5e62bdb8-cd81-42b8-ac72-1e06bf9c496d'
        result = await server_instance.get_session_details(session_id=session_id)
        
        # Verify the service was called correctly
        server_instance.sm_service.session.assert_called_once()
        
        # Verify return format - server method returns Pydantic model, not dictionary
        assert result == mock_session

    async def test_list_session_activities(self, server_with_sm_service):
        """Test list_session_activities method"""
        server_instance = server_with_sm_service
        
        # Mock session activities response
        from unittest.mock import MagicMock
        
        mock_page = MagicMock()
        mock_activity1 = MagicMock()
        mock_activity1.model_dump.return_value = {
            'activity_id': 'act-001',
            'timestamp': '2024-01-15T10:31:00Z',
            'command': 'ls -la',
            'result': 'SUCCESS'
        }
        mock_activity2 = MagicMock()
        mock_activity2.model_dump.return_value = {
            'activity_id': 'act-002',
            'timestamp': '2024-01-15T10:32:00Z',
            'command': 'cat /etc/passwd',
            'result': 'SUCCESS'
        }
        mock_page.items = [mock_activity1, mock_activity2]
        
        # Mock the sm service list_session_activities method
        server_instance.sm_service.list_session_activities.return_value = [mock_page]
        
        session_id = '5e62bdb8-cd81-42b8-ac72-1e06bf9c496d'
        result = await server_instance.list_session_activities(session_id=session_id)
        
        # Verify the service was called correctly
        server_instance.sm_service.list_session_activities.assert_called_once()
        
        # Verify return format - server method returns list of Pydantic models, not dictionaries
        assert len(result) == 2
        assert result[0] == mock_activity1
        assert result[1] == mock_activity2

    async def test_count_sessions(self, server_with_sm_service):
        """Test count_sessions method"""
        server_instance = server_with_sm_service
        
        # Mock session count response
        server_instance.sm_service.count_sessions_by.return_value = 42
        
        result = await server_instance.count_sessions()
        
        # Verify the service was called correctly
        server_instance.sm_service.count_sessions_by.assert_called_once()
        
        # Verify return format
        assert result['count'] == 42

    async def test_get_session_statistics(self, server_with_sm_service):
        """Test get_session_statistics method"""
        server_instance = server_with_sm_service
        
        # Mock session statistics response
        from unittest.mock import MagicMock
        
        mock_stats = MagicMock()
        mock_stats.model_dump.return_value = {
            'total_sessions': 150,
            'active_sessions': 5,
            'protocols': {
                'SSH': 80,
                'RDP': 50,
                'Database': 20
            },
            'average_session_duration': '00:25:30',
            'period': 'last_30_days'
        }
        
        # Mock the sm service sessions_stats method
        server_instance.sm_service.sessions_stats.return_value = mock_stats
        
        result = await server_instance.get_session_statistics()
        
        # Verify the service was called correctly
        server_instance.sm_service.sessions_stats.assert_called_once()
        
        # Verify return format - server method returns Pydantic model, not dictionary
        assert result == mock_stats