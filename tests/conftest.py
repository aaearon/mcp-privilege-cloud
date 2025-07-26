"""
Shared pytest configuration and fixtures for test isolation.

This file provides fixtures to ensure proper test isolation by resetting
global state between tests.
"""

import pytest
import os
from unittest.mock import patch


@pytest.fixture(autouse=True)
def reset_global_state():
    """
    Automatically reset global state before each test to ensure isolation.
    
    This fixture:
    1. Resets the global server instance
    2. Clears any cached authentication
    3. Ensures clean state between tests
    """
    # Reset global server state before each test
    try:
        from mcp_privilege_cloud.mcp_server import reset_server
        reset_server()
    except ImportError:
        # If mcp_server is not available, skip
        pass
    
    yield  # Run the test
    
    # Clean up after each test
    try:
        from mcp_privilege_cloud.mcp_server import reset_server
        reset_server()
    except ImportError:
        pass


@pytest.fixture
def mock_env_vars():
    """Provide mock environment variables for testing."""
    return {
        'CYBERARK_CLIENT_ID': 'test-client-id',
        'CYBERARK_CLIENT_SECRET': 'test-client-secret'
    }


@pytest.fixture
def isolated_server():
    """
    Provide a completely isolated server instance for testing.
    
    This fixture mocks the SDK authenticator to prevent real authentication
    and provides a clean server instance.
    """
    with patch.dict(os.environ, {
        'CYBERARK_CLIENT_ID': 'test-client-id',
        'CYBERARK_CLIENT_SECRET': 'test-client-secret'
    }):
        # Mock the SDK authenticator to prevent real authentication
        with patch('src.mcp_privilege_cloud.server.CyberArkSDKAuthenticator') as mock_auth_class:
            from src.mcp_privilege_cloud.server import CyberArkMCPServer
            
            # Create mock authenticator
            mock_auth = mock_auth_class.from_environment.return_value
            mock_auth.get_authenticated_client.return_value = 'mock_sdk_client'
            
            # Create server instance
            server = CyberArkMCPServer()
            
            # Clear any cache to ensure isolation
            server.clear_cache()
            
            yield server
            
            # Clean up after test
            server.clear_cache()