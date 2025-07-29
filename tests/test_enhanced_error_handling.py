import pytest
import logging
from unittest.mock import Mock, patch
from src.mcp_privilege_cloud.server import CyberArkMCPServer, CyberArkAPIError
from src.mcp_privilege_cloud.exceptions import (
    ArkServiceException, 
    ArkPCloudException, 
    ArkAuthException,
    is_sdk_exception,
    convert_sdk_exception
)


class TestEnhancedErrorHandling:
    """Test cases for enhanced error handling with SDK-specific exceptions and user guidance"""

    @pytest.fixture
    def server(self):
        """Create server instance for testing"""
        with patch.dict('os.environ', {
            'CYBERARK_CLIENT_ID': 'test-client',
            'CYBERARK_CLIENT_SECRET': 'test-secret'
        }):
            with patch('src.mcp_privilege_cloud.server.CyberArkSDKAuthenticator') as mock_sdk_auth_class:
                mock_sdk_auth = Mock()
                mock_sdk_auth.get_authenticated_client.return_value = Mock()
                mock_sdk_auth_class.from_environment.return_value = mock_sdk_auth
                
                server = CyberArkMCPServer()
                server.sdk_authenticator = mock_sdk_auth
                server.accounts_service = Mock()
                server.safes_service = Mock()
                server.platforms_service = Mock()
                
                yield server

    async def test_enhanced_401_authentication_error(self, server):
        """Test enhanced 401 authentication error handling"""
        # Create an SDK authentication exception
        sdk_exception = ArkAuthException("Token expired")
        sdk_exception.status_code = 401
        
        # Mock the accounts service to raise SDK exception
        server.accounts_service.list_accounts.side_effect = sdk_exception
        
        # Test that the enhanced error message is provided
        with pytest.raises(CyberArkAPIError) as exc_info:
            await server.list_accounts()
        
        error = exc_info.value
        assert error.status_code == 401
        assert "Authentication failed" in str(error)
        assert "CYBERARK_CLIENT_ID and CYBERARK_CLIENT_SECRET" in str(error)
        assert "Token may have expired" in str(error)
        assert "restarting the MCP server" in str(error)

    async def test_enhanced_403_access_denied_error(self, server):
        """Test enhanced 403 access denied error handling"""
        # Create an SDK service exception with 403
        sdk_exception = ArkPCloudException("Insufficient permissions")
        sdk_exception.status_code = 403
        
        server.accounts_service.list_accounts.side_effect = sdk_exception
        
        with pytest.raises(CyberArkAPIError) as exc_info:
            await server.list_accounts()
        
        error = exc_info.value
        assert error.status_code == 403
        assert "Access denied" in str(error)
        assert "Privilege Cloud Administrator" in str(error)
        assert "Contact your CyberArk administrator" in str(error)

    async def test_enhanced_404_not_found_error(self, server):
        """Test enhanced 404 not found error handling"""
        # Create an SDK service exception with 404
        sdk_exception = ArkServiceException("Platform not found")
        sdk_exception.status_code = 404
        
        server.platforms_service.platform.side_effect = sdk_exception
        
        with pytest.raises(CyberArkAPIError) as exc_info:
            await server.get_platform_details("NonExistentPlatform")
        
        error = exc_info.value
        assert error.status_code == 404
        assert "Resource not found" in str(error)
        assert "verify the resource ID/name exists" in str(error)
        assert "lack permissions to view" in str(error)

    async def test_enhanced_429_rate_limit_error(self, server):
        """Test enhanced 429 rate limit error handling"""
        # Create an SDK service exception with 429
        sdk_exception = ArkPCloudException("Rate limit exceeded")
        sdk_exception.status_code = 429
        
        server.accounts_service.list_accounts.side_effect = sdk_exception
        
        with pytest.raises(CyberArkAPIError) as exc_info:
            await server.list_accounts()
        
        error = exc_info.value
        assert error.status_code == 429
        assert "Rate limit exceeded" in str(error)
        assert "wait a few seconds and retry" in str(error)
        assert "reducing concurrent operations" in str(error)

    async def test_sdk_exception_conversion(self, server):
        """Test that SDK exceptions are properly converted using existing utilities"""
        # Create an SDK service exception with status code
        sdk_exception = ArkServiceException("Generic SDK error")
        sdk_exception.status_code = 500
        
        server.accounts_service.list_accounts.side_effect = sdk_exception
        
        with pytest.raises(CyberArkAPIError) as exc_info:
            await server.list_accounts()
        
        error = exc_info.value
        assert error.status_code == 500
        assert "Generic SDK error" in str(error)

    async def test_non_sdk_exception_passthrough(self, server):
        """Test that non-SDK exceptions are passed through unchanged"""
        # Create a regular Python exception
        regular_exception = ValueError("Invalid parameter")
        
        server.accounts_service.list_accounts.side_effect = regular_exception
        
        # Should raise the original exception, not a converted one
        with pytest.raises(ValueError) as exc_info:
            await server.list_accounts()
        
        assert "Invalid parameter" in str(exc_info.value)

    async def test_sdk_exception_without_status_code(self, server):
        """Test SDK exception handling when no status code is available"""
        # Create an SDK exception without status_code attribute
        sdk_exception = ArkServiceException("SDK error without status")
        
        server.accounts_service.list_accounts.side_effect = sdk_exception
        
        with pytest.raises(CyberArkAPIError) as exc_info:
            await server.list_accounts()
        
        error = exc_info.value
        assert "SDK error without status" in str(error)
        # Should not have status_code when not provided
        assert error.status_code is None

    def test_is_sdk_exception_utility(self):
        """Test the is_sdk_exception utility function"""
        # Test with SDK exceptions
        assert is_sdk_exception(ArkServiceException("test"))
        assert is_sdk_exception(ArkPCloudException("test"))
        assert is_sdk_exception(ArkAuthException("test"))
        
        # Test with non-SDK exceptions
        assert not is_sdk_exception(ValueError("test"))
        assert not is_sdk_exception(Exception("test"))

    def test_convert_sdk_exception_utility(self):
        """Test the convert_sdk_exception utility function"""
        # Test ArkAuthException conversion
        auth_exception = ArkAuthException("Auth failed")
        converted = convert_sdk_exception(auth_exception)
        assert isinstance(converted, Exception)  # Should be AuthenticationError but checking base
        
        # Test ArkServiceException conversion
        service_exception = ArkServiceException("Service error")
        service_exception.status_code = 500
        converted = convert_sdk_exception(service_exception)
        assert isinstance(converted, CyberArkAPIError)
        assert converted.status_code == 500
        
        # Test non-SDK exception conversion
        regular_exception = ValueError("Regular error")
        converted = convert_sdk_exception(regular_exception)
        assert isinstance(converted, CyberArkAPIError)
        assert "Regular error" in str(converted)

    async def test_logging_behavior(self, server, caplog):
        """Test that enhanced error handling includes proper logging"""
        with caplog.at_level(logging.ERROR):
            # Create a 403 SDK exception
            sdk_exception = ArkPCloudException("Access denied")
            sdk_exception.status_code = 403
            
            server.accounts_service.list_accounts.side_effect = sdk_exception
            
            with pytest.raises(CyberArkAPIError):
                await server.list_accounts()
            
            # Verify logging occurred
            assert "Access denied listing accounts" in caplog.text
            assert "Access denied" in caplog.text

    async def test_logging_behavior_rate_limit(self, server, caplog):
        """Test that rate limit errors use warning level logging"""
        with caplog.at_level(logging.WARNING):
            # Create a 429 SDK exception
            sdk_exception = ArkPCloudException("Rate limit")
            sdk_exception.status_code = 429
            
            server.accounts_service.list_accounts.side_effect = sdk_exception
            
            with pytest.raises(CyberArkAPIError):
                await server.list_accounts()
            
            # Verify warning level logging occurred
            assert "Rate limit exceeded listing accounts" in caplog.text

    async def test_exception_chaining(self, server):
        """Test that original exceptions are properly chained using 'from e'"""
        # Create an SDK exception
        sdk_exception = ArkAuthException("Original auth error")
        sdk_exception.status_code = 401
        
        server.accounts_service.list_accounts.side_effect = sdk_exception
        
        with pytest.raises(CyberArkAPIError) as exc_info:
            await server.list_accounts()
        
        # Verify exception chaining
        error = exc_info.value
        assert error.__cause__ is sdk_exception
        assert isinstance(error.__cause__, ArkAuthException)