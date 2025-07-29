import pytest
from unittest.mock import Mock, patch
from src.mcp_privilege_cloud.server import CyberArkMCPServer, CyberArkAPIError
from src.mcp_privilege_cloud.exceptions import ArkAuthException, ArkPCloudException, ArkServiceException


class TestEnhancedErrorMessages:
    """Test cases to verify enhanced error messages provide actionable guidance"""

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

    async def test_authentication_error_provides_credential_guidance(self, server):
        """Test that 401 errors provide clear credential troubleshooting steps"""
        # Simulate token expiration
        sdk_exception = ArkAuthException("Authentication token expired")
        sdk_exception.status_code = 401
        server.accounts_service.list_accounts.side_effect = sdk_exception
        
        with pytest.raises(CyberArkAPIError) as exc_info:
            await server.list_accounts()
        
        error_message = str(exc_info.value)
        
        # Verify the error provides actionable guidance
        assert "Authentication failed" in error_message
        assert "CYBERARK_CLIENT_ID and CYBERARK_CLIENT_SECRET" in error_message
        assert "Token may have expired" in error_message
        assert "restarting the MCP server" in error_message

    async def test_permission_error_provides_role_guidance(self, server):
        """Test that 403 errors provide clear role requirement guidance"""
        # Simulate permission denied
        sdk_exception = ArkPCloudException("User lacks required permissions")
        sdk_exception.status_code = 403
        server.safes_service.add_safe.side_effect = sdk_exception
        
        with pytest.raises(CyberArkAPIError) as exc_info:
            await server.add_safe("TestSafe")
        
        error_message = str(exc_info.value)
        
        # Verify the error provides actionable guidance
        assert "Access denied" in error_message
        assert "Privilege Cloud Administrator" in error_message
        assert "Contact your CyberArk administrator" in error_message

    async def test_not_found_error_provides_verification_guidance(self, server):
        """Test that 404 errors provide clear verification guidance"""
        # Simulate resource not found
        sdk_exception = ArkServiceException("Platform does not exist")
        sdk_exception.status_code = 404
        server.platforms_service.platform.side_effect = sdk_exception
        
        with pytest.raises(CyberArkAPIError) as exc_info:
            await server.get_platform_details("NonExistentPlatform")
        
        error_message = str(exc_info.value)
        
        # Verify the error provides actionable guidance
        assert "Resource not found" in error_message
        assert "verify the resource ID/name exists" in error_message
        assert "lack permissions to view" in error_message

    async def test_rate_limit_error_provides_retry_guidance(self, server):
        """Test that 429 errors provide clear retry guidance"""
        # Simulate rate limiting
        sdk_exception = ArkPCloudException("Too many requests")
        sdk_exception.status_code = 429
        server.accounts_service.list_accounts.side_effect = sdk_exception
        
        with pytest.raises(CyberArkAPIError) as exc_info:
            await server.list_accounts()
        
        error_message = str(exc_info.value)
        
        # Verify the error provides actionable guidance
        assert "Rate limit exceeded" in error_message
        assert "wait a few seconds and retry" in error_message
        assert "reducing concurrent operations" in error_message

    async def test_generic_sdk_error_preserves_original_message(self, server):
        """Test that generic SDK errors preserve original messages while adding context"""
        # Simulate generic SDK error
        sdk_exception = ArkServiceException("Internal server error occurred")
        sdk_exception.status_code = 500
        server.accounts_service.list_accounts.side_effect = sdk_exception
        
        with pytest.raises(CyberArkAPIError) as exc_info:
            await server.list_accounts()
        
        error_message = str(exc_info.value)
        
        # Verify original error message is preserved
        assert "Internal server error occurred" in error_message

    async def test_non_sdk_errors_remain_unchanged(self, server):
        """Test that non-SDK errors pass through unchanged"""
        # Simulate non-SDK error
        regular_exception = ValueError("Invalid input parameter")
        server.accounts_service.list_accounts.side_effect = regular_exception
        
        with pytest.raises(ValueError) as exc_info:
            await server.list_accounts()
        
        # Verify the original exception type and message are preserved
        assert isinstance(exc_info.value, ValueError)
        assert "Invalid input parameter" in str(exc_info.value)

    async def test_error_status_codes_are_preserved(self, server):
        """Test that HTTP status codes are properly preserved in enhanced errors"""
        test_cases = [
            (401, ArkAuthException),
            (403, ArkPCloudException),
            (404, ArkServiceException),
            (429, ArkPCloudException),
        ]
        
        for status_code, exception_class in test_cases:
            sdk_exception = exception_class(f"Test error {status_code}")
            sdk_exception.status_code = status_code
            server.accounts_service.list_accounts.side_effect = sdk_exception
            
            with pytest.raises(CyberArkAPIError) as exc_info:
                await server.list_accounts()
            
            # Verify status code is preserved
            assert exc_info.value.status_code == status_code

    async def test_exception_chaining_preserves_original_context(self, server):
        """Test that exception chaining preserves the original exception context"""
        sdk_exception = ArkAuthException("Original authentication error")
        sdk_exception.status_code = 401
        server.accounts_service.list_accounts.side_effect = sdk_exception
        
        with pytest.raises(CyberArkAPIError) as exc_info:
            await server.list_accounts()
        
        # Verify the original exception is chained
        assert exc_info.value.__cause__ is sdk_exception
        assert isinstance(exc_info.value.__cause__, ArkAuthException)
        assert "Original authentication error" in str(exc_info.value.__cause__)