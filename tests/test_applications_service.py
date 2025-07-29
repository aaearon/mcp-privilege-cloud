#!/usr/bin/env python3
"""
Tests for Application Management functionality
Tests the ArkPCloudApplicationsService integration and MCP tools
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch, call
from typing import Dict, Any, List

from src.mcp_privilege_cloud.server import CyberArkMCPServer
from src.mcp_privilege_cloud.exceptions import CyberArkAPIError


@pytest.fixture
def mock_server():
    """Create a mock server instance"""
    with patch('src.mcp_privilege_cloud.server.CyberArkSDKAuthenticator') as mock_auth:
        mock_sdk_auth = Mock()
        mock_auth.from_environment.return_value.get_authenticated_client.return_value = mock_sdk_auth
        
        server = CyberArkMCPServer()
        
        # Mock all services to None initially for clean testing
        server.accounts_service = None
        server.safes_service = None  
        server.platforms_service = None
        server.applications_service = None
        server.sm_service = None
        
        return server


class TestApplicationsServiceIntegration:
    """Test applications service integration with server"""
    
    def test_applications_service_in_available_tools(self, mock_server):
        """Test that applications tools are included in available tools"""
        available_tools = mock_server.get_available_tools()
        
        applications_tools = [
            "list_applications",
            "get_application_details", 
            "add_application",
            "delete_application",
            "list_application_auth_methods",
            "get_application_auth_method_details",
            "add_application_auth_method",
            "delete_application_auth_method",
            "get_applications_stats"
        ]
        
        for tool in applications_tools:
            assert tool in available_tools, f"Application tool '{tool}' not in available tools"
        
        # Verify total count increased 
        assert len(available_tools) >= 40, f"Expected at least 40 tools, got {len(available_tools)}"
    
    @patch('src.mcp_privilege_cloud.server.ArkPCloudApplicationsService')
    def test_ensure_applications_service_initialized(self, mock_apps_service_class, mock_server):
        """Test applications service initialization"""
        mock_apps_service = Mock()
        mock_apps_service_class.return_value = mock_apps_service
        
        # Test service initialization
        mock_server._ensure_service_initialized('applications_service')
        
        # Verify service was created and assigned
        assert mock_server.applications_service is not None
        mock_apps_service_class.assert_called_once()
    
    @patch('src.mcp_privilege_cloud.server.ArkPCloudApplicationsService')
    @patch('src.mcp_privilege_cloud.server.ArkPCloudAccountsService')
    @patch('src.mcp_privilege_cloud.server.ArkPCloudSafesService')
    @patch('src.mcp_privilege_cloud.server.ArkPCloudPlatformsService')
    @patch('src.mcp_privilege_cloud.server.ArkSMService')
    def test_reinitialize_services_includes_applications(self, mock_sm_service, mock_platforms_service, 
                                                        mock_safes_service, mock_accounts_service, 
                                                        mock_apps_service_class, mock_server):
        """Test that reinitialize_services includes applications service"""
        # Mock SDK auth object
        mock_sdk_auth = Mock()
        mock_sdk_auth.token.metadata.keys.return_value = ['env']
        mock_server.sdk_authenticator.get_authenticated_client.return_value = mock_sdk_auth
        
        # Test reinitialize
        mock_server.reinitialize_services()
        
        # Verify applications service was initialized
        assert mock_server.applications_service is not None
        mock_apps_service_class.assert_called_once_with(mock_sdk_auth)


class TestApplicationsOperations:
    """Test applications management operations"""
    
    @pytest.mark.asyncio
    @patch('src.mcp_privilege_cloud.server.ArkPCloudApplicationsService')
    async def test_list_applications_success(self, mock_apps_service_class, mock_server):
        """Test successful application listing"""
        # Setup mock
        mock_apps_service = Mock()
        mock_app1 = Mock()
        mock_app1.model_dump.return_value = {
            'app_id': 'app1',
            'description': 'Test Application 1',
            'location': 'test-location',
            'disabled': False
        }
        mock_app2 = Mock()
        mock_app2.model_dump.return_value = {
            'app_id': 'app2', 
            'description': 'Test Application 2',
            'location': 'test-location',
            'disabled': True
        }
        
        mock_apps_service.list_applications.return_value = [mock_app1, mock_app2]
        mock_apps_service_class.return_value = mock_apps_service
        mock_server.applications_service = mock_apps_service
        
        # Test
        result = await mock_server.list_applications()
        
        # Verify
        assert len(result) == 2
        assert result[0]['app_id'] == 'app1'
        assert result[1]['app_id'] == 'app2'
        mock_apps_service.list_applications.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.mcp_privilege_cloud.server.ArkPCloudApplicationsService')
    @patch('src.mcp_privilege_cloud.server.ArkPCloudApplicationsFilter')
    async def test_list_applications_with_filter(self, mock_filter_class, mock_apps_service_class, mock_server):
        """Test application listing with filters"""
        # Setup mock
        mock_apps_service = Mock()
        mock_filter = Mock()
        mock_filter_class.return_value = mock_filter
        mock_apps_service.list_applications_by.return_value = []
        mock_apps_service_class.return_value = mock_apps_service
        mock_server.applications_service = mock_apps_service
        
        # Test with filters
        await mock_server.list_applications(location='test', only_enabled=True)
        
        # Verify filter was created and used
        mock_filter_class.assert_called_once_with(location='test', only_enabled=True)
        mock_apps_service.list_applications_by.assert_called_once_with(mock_filter)
    
    @pytest.mark.asyncio
    @patch('src.mcp_privilege_cloud.server.ArkPCloudApplicationsService')
    @patch('src.mcp_privilege_cloud.server.ArkPCloudGetApplication')
    async def test_get_application_details_success(self, mock_get_app_class, mock_apps_service_class, mock_server):
        """Test successful application details retrieval"""
        # Setup mock
        mock_apps_service = Mock()
        mock_get_app = Mock()
        mock_app = Mock()
        mock_app.model_dump.return_value = {
            'app_id': 'test-app',
            'description': 'Test Application',
            'location': 'test-location'
        }
        
        mock_get_app_class.return_value = mock_get_app
        mock_apps_service.application.return_value = mock_app
        mock_apps_service_class.return_value = mock_apps_service
        mock_server.applications_service = mock_apps_service
        
        # Test
        result = await mock_server.get_application_details('test-app')
        
        # Verify - server method returns Pydantic model, not dictionary
        assert result == mock_app
        mock_get_app_class.assert_called_once_with(app_id='test-app')
        mock_apps_service.application.assert_called_once_with(mock_get_app)
    
    @pytest.mark.asyncio
    @patch('src.mcp_privilege_cloud.server.ArkPCloudApplicationsService')
    @patch('src.mcp_privilege_cloud.server.ArkPCloudAddApplication')
    async def test_add_application_success(self, mock_add_app_class, mock_apps_service_class, mock_server):
        """Test successful application creation"""
        # Setup mock
        mock_apps_service = Mock()
        mock_add_app = Mock()
        mock_app = Mock()
        mock_app.model_dump.return_value = {
            'app_id': 'new-app',
            'description': 'New Application',
            'location': 'new-location'
        }
        
        mock_add_app_class.return_value = mock_add_app
        mock_apps_service.add_application.return_value = mock_app
        mock_apps_service_class.return_value = mock_apps_service
        mock_server.applications_service = mock_apps_service
        
        # Test
        result = await mock_server.add_application(
            app_id='new-app',
            description='New Application',
            location='new-location'
        )
        
        # Verify - server method returns Pydantic model, not dictionary
        assert result == mock_app
        mock_add_app_class.assert_called_once()
        mock_apps_service.add_application.assert_called_once_with(mock_add_app)
    
    @pytest.mark.asyncio
    @patch('src.mcp_privilege_cloud.server.ArkPCloudApplicationsService')
    @patch('src.mcp_privilege_cloud.server.ArkPCloudDeleteApplication')
    async def test_delete_application_success(self, mock_delete_app_class, mock_apps_service_class, mock_server):
        """Test successful application deletion"""
        # Setup mock
        mock_apps_service = Mock()
        mock_delete_app = Mock()
        mock_delete_app_class.return_value = mock_delete_app
        mock_apps_service_class.return_value = mock_apps_service
        mock_server.applications_service = mock_apps_service
        
        # Test
        result = await mock_server.delete_application('test-app')
        
        # Verify
        assert result['app_id'] == 'test-app'
        assert result['status'] == 'deleted'
        mock_delete_app_class.assert_called_once_with(app_id='test-app')
        mock_apps_service.delete_application.assert_called_once_with(mock_delete_app)


class TestApplicationAuthMethods:
    """Test application authentication methods operations"""
    
    @pytest.mark.asyncio
    @patch('src.mcp_privilege_cloud.server.ArkPCloudApplicationsService')
    @patch('src.mcp_privilege_cloud.server.ArkPCloudListApplicationAuthMethods')
    async def test_list_application_auth_methods(self, mock_list_auth_class, mock_apps_service_class, mock_server):
        """Test listing application authentication methods"""
        # Setup mock
        mock_apps_service = Mock()
        mock_list_auth = Mock()
        mock_auth_method = Mock()
        mock_auth_method.model_dump.return_value = {
            'auth_id': 'auth1',
            'auth_type': 'certificate',
            'auth_value': 'test-cert'
        }
        
        mock_list_auth_class.return_value = mock_list_auth
        mock_apps_service.list_application_auth_methods.return_value = [mock_auth_method]
        mock_apps_service_class.return_value = mock_apps_service
        mock_server.applications_service = mock_apps_service
        
        # Test
        result = await mock_server.list_application_auth_methods('test-app')
        
        # Verify - server method returns list of Pydantic models, not dictionaries
        assert len(result) == 1
        assert result[0] == mock_auth_method
        mock_list_auth_class.assert_called_once_with(app_id='test-app')
        mock_apps_service.list_application_auth_methods.assert_called_once_with(mock_list_auth)
    
    @pytest.mark.asyncio
    @patch('src.mcp_privilege_cloud.server.ArkPCloudApplicationsService')
    @patch('src.mcp_privilege_cloud.server.ArkPCloudApplicationAuthMethodsFilter')
    async def test_list_application_auth_methods_with_filter(self, mock_filter_class, mock_apps_service_class, mock_server):
        """Test listing application auth methods with filter"""
        # Setup mock
        mock_apps_service = Mock()
        mock_filter = Mock()
        mock_filter_class.return_value = mock_filter
        mock_apps_service.list_application_auth_methods_by.return_value = []
        mock_apps_service_class.return_value = mock_apps_service
        mock_server.applications_service = mock_apps_service
        
        # Test
        await mock_server.list_application_auth_methods('test-app', auth_types=['certificate'])
        
        # Verify
        mock_filter_class.assert_called_once_with(app_id='test-app', auth_types=['certificate'])
        mock_apps_service.list_application_auth_methods_by.assert_called_once_with(mock_filter)
    
    @pytest.mark.asyncio
    @patch('src.mcp_privilege_cloud.server.ArkPCloudApplicationsService')
    @patch('src.mcp_privilege_cloud.server.ArkPCloudAddApplicationAuthMethod')
    async def test_add_application_auth_method(self, mock_add_auth_class, mock_apps_service_class, mock_server):
        """Test adding application authentication method"""
        # Setup mock
        mock_apps_service = Mock()
        mock_add_auth = Mock()
        mock_auth_method = Mock()
        mock_auth_method.model_dump.return_value = {
            'auth_id': 'new-auth',
            'auth_type': 'certificate',
            'auth_value': 'new-cert'
        }
        
        mock_add_auth_class.return_value = mock_add_auth
        mock_apps_service.add_application_auth_method.return_value = mock_auth_method
        mock_apps_service_class.return_value = mock_apps_service
        mock_server.applications_service = mock_apps_service
        
        # Test
        result = await mock_server.add_application_auth_method(
            app_id='test-app',
            auth_type='certificate',
            auth_value='new-cert'
        )
        
        # Verify - server method returns Pydantic model, not dictionary
        assert result == mock_auth_method
        mock_add_auth_class.assert_called_once()
        mock_apps_service.add_application_auth_method.assert_called_once_with(mock_add_auth)
    
    @pytest.mark.asyncio
    @patch('src.mcp_privilege_cloud.server.ArkPCloudApplicationsService')
    @patch('src.mcp_privilege_cloud.server.ArkPCloudDeleteApplicationAuthMethod')
    async def test_delete_application_auth_method(self, mock_delete_auth_class, mock_apps_service_class, mock_server):
        """Test deleting application authentication method"""
        # Setup mock
        mock_apps_service = Mock()
        mock_delete_auth = Mock()
        mock_delete_auth_class.return_value = mock_delete_auth
        mock_apps_service_class.return_value = mock_apps_service
        mock_server.applications_service = mock_apps_service
        
        # Test
        result = await mock_server.delete_application_auth_method('test-app', 'auth1')
        
        # Verify
        assert result['app_id'] == 'test-app'
        assert result['auth_id'] == 'auth1'
        assert result['status'] == 'deleted'
        mock_delete_auth_class.assert_called_once_with(app_id='test-app', auth_id='auth1')
        mock_apps_service.delete_application_auth_method.assert_called_once_with(mock_delete_auth)


class TestApplicationsStatistics:
    """Test applications statistics operations"""
    
    @pytest.mark.asyncio
    @patch('src.mcp_privilege_cloud.server.ArkPCloudApplicationsService')
    async def test_get_applications_stats(self, mock_apps_service_class, mock_server):
        """Test getting applications statistics"""
        # Setup mock
        mock_apps_service = Mock()
        mock_stats = Mock()
        mock_stats.model_dump.return_value = {
            'count': 25,
            'disabled_apps': 3,
            'auth_types_count': {
                'certificate': 15,
                'hash': 8,
                'path': 2
            }
        }
        
        mock_apps_service.applications_stats.return_value = mock_stats
        mock_apps_service_class.return_value = mock_apps_service
        mock_server.applications_service = mock_apps_service
        
        # Test
        result = await mock_server.get_applications_stats()
        
        # Verify - server method returns Pydantic model, not dictionary
        assert result == mock_stats
        mock_apps_service.applications_stats.assert_called_once()


class TestApplicationsErrorHandling:
    """Test error handling for applications operations"""
    
    @pytest.mark.asyncio
    @patch('src.mcp_privilege_cloud.server.ArkPCloudApplicationsService')
    async def test_list_applications_error(self, mock_apps_service_class, mock_server):
        """Test error handling in list applications"""
        # Setup mock to raise exception
        mock_apps_service = Mock()
        mock_apps_service.list_applications.side_effect = Exception("API Error")
        mock_apps_service_class.return_value = mock_apps_service
        mock_server.applications_service = mock_apps_service
        
        # Test that exception is re-raised
        with pytest.raises(Exception, match="API Error"):
            await mock_server.list_applications()
    
    @pytest.mark.asyncio
    @patch('src.mcp_privilege_cloud.server.ArkPCloudApplicationsService')
    async def test_get_application_details_error(self, mock_apps_service_class, mock_server):
        """Test error handling in get application details"""
        # Setup mock to raise exception
        mock_apps_service = Mock()
        mock_apps_service.application.side_effect = Exception("Application not found")
        mock_apps_service_class.return_value = mock_apps_service
        mock_server.applications_service = mock_apps_service
        
        # Test that exception is re-raised
        with pytest.raises(Exception, match="Application not found"):
            await mock_server.get_application_details('nonexistent-app')


if __name__ == '__main__':
    pytest.main([__file__])