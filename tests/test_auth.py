import pytest
import httpx
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
import os

from src.cyberark_mcp.auth import CyberArkAuthenticator, AuthenticationError


class TestCyberArkAuthenticator:
    """Test cases for CyberArk API token authentication"""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing"""
        return {
            "identity_tenant_id": "test-tenant",
            "client_id": "test-client",
            "client_secret": "test-secret",
            "timeout": 30
        }

    @pytest.fixture
    def authenticator(self, mock_config):
        """Create authenticator instance for testing"""
        return CyberArkAuthenticator(
            identity_tenant_id=mock_config["identity_tenant_id"],
            client_id=mock_config["client_id"],
            client_secret=mock_config["client_secret"],
            timeout=mock_config["timeout"]
        )

    @pytest.mark.auth
    def test_authenticator_initialization(self, authenticator, mock_config):
        """Test that authenticator initializes with correct parameters"""
        assert authenticator.identity_tenant_id == mock_config["identity_tenant_id"]
        assert authenticator.client_id == mock_config["client_id"]
        assert authenticator.client_secret == mock_config["client_secret"]
        assert authenticator.timeout == mock_config["timeout"]
        assert authenticator._token is None
        assert authenticator._token_expiry is None

    @pytest.mark.auth
    def test_get_token_url(self, authenticator):
        """Test that token URL is constructed correctly"""
        expected_url = "https://test-tenant.id.cyberark.cloud/oauth2/platformtoken"
        assert authenticator._get_token_url() == expected_url

    @pytest.mark.auth
    async def test_successful_token_request(self, authenticator):
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
            
            token = await authenticator._request_new_token()
            
            assert token == "test-token-12345"
            mock_post.assert_called_once()
            
            # Verify request parameters
            call_args = mock_post.call_args
            assert call_args[1]['data']['grant_type'] == 'client_credentials'
            assert call_args[1]['data']['client_id'] == 'test-client'
            assert call_args[1]['data']['client_secret'] == 'test-secret'

    @pytest.mark.auth
    async def test_token_request_with_http_error(self, authenticator):
        """Test token request with HTTP error response"""
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "401 Unauthorized", request=Mock(), response=Mock()
            )
            mock_post.return_value = mock_response
            
            with pytest.raises(AuthenticationError, match="Failed to authenticate"):
                await authenticator._request_new_token()

    @pytest.mark.auth
    async def test_token_request_with_network_error(self, authenticator):
        """Test token request with network error"""
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.side_effect = httpx.ConnectError("Connection failed")
            
            with pytest.raises(AuthenticationError, match="Network error"):
                await authenticator._request_new_token()

    @pytest.mark.auth
    async def test_token_request_with_invalid_response(self, authenticator):
        """Test token request with invalid JSON response"""
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = Mock()
            mock_response.json.side_effect = ValueError("Invalid JSON")
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            with pytest.raises(AuthenticationError, match="Invalid response format"):
                await authenticator._request_new_token()

    @pytest.mark.auth
    async def test_token_request_missing_access_token(self, authenticator):
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
                await authenticator._request_new_token()

    @pytest.mark.auth
    async def test_get_valid_token_first_time(self, authenticator):
        """Test getting token for the first time"""
        with patch.object(authenticator, '_request_new_token', return_value="new-token"):
            token = await authenticator.get_valid_token()
            assert token == "new-token"
            assert authenticator._token == "new-token"

    @pytest.mark.auth
    async def test_get_valid_token_cached(self, authenticator):
        """Test getting cached token when still valid"""
        # Set up cached token
        authenticator._token = "cached-token"
        authenticator._token_expiry = datetime.utcnow() + timedelta(minutes=10)
        
        with patch.object(authenticator, '_request_new_token') as mock_request:
            token = await authenticator.get_valid_token()
            assert token == "cached-token"
            mock_request.assert_not_called()

    @pytest.mark.auth
    async def test_get_valid_token_expired(self, authenticator):
        """Test getting new token when cached token is expired"""
        # Set up expired token
        authenticator._token = "expired-token"
        authenticator._token_expiry = datetime.utcnow() - timedelta(minutes=1)
        
        with patch.object(authenticator, '_request_new_token', return_value="new-token"):
            token = await authenticator.get_valid_token()
            assert token == "new-token"
            assert authenticator._token == "new-token"

    @pytest.mark.auth
    async def test_get_valid_token_near_expiry(self, authenticator):
        """Test getting new token when cached token is near expiry (safety margin)"""
        # Set up token near expiry (within 60 seconds)
        authenticator._token = "near-expiry-token"
        authenticator._token_expiry = datetime.utcnow() + timedelta(seconds=30)
        
        with patch.object(authenticator, '_request_new_token', return_value="new-token"):
            token = await authenticator.get_valid_token()
            assert token == "new-token"
            assert authenticator._token == "new-token"

    @pytest.mark.auth
    def test_is_token_valid_no_token(self, authenticator):
        """Test token validity check when no token exists"""
        assert not authenticator._is_token_valid()

    @pytest.mark.auth
    def test_is_token_valid_no_expiry(self, authenticator):
        """Test token validity check when token has no expiry"""
        authenticator._token = "test-token"
        assert not authenticator._is_token_valid()

    @pytest.mark.auth
    def test_is_token_valid_expired(self, authenticator):
        """Test token validity check for expired token"""
        authenticator._token = "test-token"
        authenticator._token_expiry = datetime.utcnow() - timedelta(minutes=1)
        assert not authenticator._is_token_valid()

    @pytest.mark.auth
    def test_is_token_valid_near_expiry(self, authenticator):
        """Test token validity check for token near expiry"""
        authenticator._token = "test-token"
        authenticator._token_expiry = datetime.utcnow() + timedelta(seconds=30)
        assert not authenticator._is_token_valid()  # Should be False due to safety margin

    @pytest.mark.auth
    def test_is_token_valid_good_token(self, authenticator):
        """Test token validity check for valid token"""
        authenticator._token = "test-token"
        authenticator._token_expiry = datetime.utcnow() + timedelta(minutes=10)
        assert authenticator._is_token_valid()

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
    async def test_get_auth_header(self, authenticator):
        """Test getting authorization header with token"""
        with patch.object(authenticator, 'get_valid_token', return_value="test-token"):
            header = await authenticator.get_auth_header()
            assert header == {"Authorization": "Bearer test-token"}

    @pytest.mark.auth
    async def test_concurrent_token_requests(self, authenticator):
        """Test that concurrent token requests don't cause race conditions"""
        import asyncio
        from datetime import datetime, timedelta
        
        # Make sure there's no valid token initially
        authenticator._token = None
        authenticator._token_expiry = None
        
        async def mock_request_new_token():
            # Simulate some delay and side effects
            await asyncio.sleep(0.1)
            authenticator._token = "concurrent-token"
            authenticator._token_expiry = datetime.utcnow() + timedelta(minutes=15)
            return "concurrent-token"
        
        with patch.object(authenticator, '_request_new_token', side_effect=mock_request_new_token) as mock_request:
            # Simulate multiple concurrent requests
            tasks = [authenticator.get_valid_token() for _ in range(5)]
            tokens = await asyncio.gather(*tasks)
            
            # All should return the same token
            assert all(token == "concurrent-token" for token in tokens)
            # Should only make one actual request due to locking
            assert mock_request.call_count == 1