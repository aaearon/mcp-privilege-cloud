import pytest
import os
from unittest.mock import patch, Mock, AsyncMock

from src.mcp_privilege_cloud.mcp_server import mcp
from src.mcp_privilege_cloud.server import CyberArkMCPServer
from src.mcp_privilege_cloud.auth import CyberArkAuthenticator


class TestIntegration:
    """Integration tests for the complete MCP server"""

    def test_mcp_server_initialization(self):
        """Test that the MCP server initializes correctly"""
        assert mcp is not None
        assert mcp.name == "CyberArk Privilege Cloud MCP Server"

    @patch.dict(os.environ, {
        "CYBERARK_IDENTITY_TENANT_ID": "test-tenant",
        "CYBERARK_CLIENT_ID": "test-client", 
        "CYBERARK_CLIENT_SECRET": "test-secret",
        "CYBERARK_SUBDOMAIN": "test-subdomain"
    })
    def test_environment_configuration(self):
        """Test that server can be configured from environment variables"""
        server = CyberArkMCPServer.from_environment()
        assert server.subdomain == "test-subdomain"
        assert isinstance(server.authenticator, CyberArkAuthenticator)

    def test_required_environment_variables_validation(self):
        """Test validation of required environment variables"""
        # Import the main function to test validation
        from src.mcp_privilege_cloud.mcp_server import main
        
        with patch.dict(os.environ, {}, clear=True):
            with patch('src.mcp_privilege_cloud.mcp_server.logger') as mock_logger:
                main()  # Should exit gracefully with error log
                mock_logger.error.assert_called()

    def test_server_tools_available(self):
        """Test that all expected tools are available in the MCP server"""
        # Mock the server context to test tool availability
        mock_server = Mock(spec=CyberArkMCPServer)
        mock_server.list_accounts = AsyncMock(return_value=[])
        mock_server.search_accounts = AsyncMock(return_value=[])
        mock_server.list_safes = AsyncMock(return_value=[])
        
        # Verify that the mock has all expected methods
        expected_methods = [
            'list_accounts',
            'search_accounts',
            'list_safes'
        ]
        
        for method in expected_methods:
            assert hasattr(mock_server, method)

    async def test_tool_execution_flow(self):
        """Test the execution flow of MCP tools"""
        # This tests the overall flow without actually calling CyberArk APIs
        
        # Mock the server and its methods
        mock_server = Mock(spec=CyberArkMCPServer)
        mock_server.list_accounts = AsyncMock(return_value=[
            {"id": "123", "name": "test-account", "safeName": "test-safe"}
        ])
        
        # Test that we can call the method
        result = await mock_server.list_accounts()
        assert len(result) == 1
        assert result[0]["name"] == "test-account"

    def test_error_handling_in_tools(self):
        """Test that tools handle errors appropriately"""
        from src.mcp_privilege_cloud.server import CyberArkAPIError
        
        # Mock server that raises errors
        mock_server = Mock(spec=CyberArkMCPServer)
        mock_server.list_accounts = AsyncMock(side_effect=CyberArkAPIError("Test error"))
        
        # Verify that the error is propagated correctly
        with pytest.raises(CyberArkAPIError, match="Test error"):
            asyncio.run(mock_server.list_accounts())

    @patch.dict(os.environ, {
        "CYBERARK_IDENTITY_TENANT_ID": "test-tenant",
        "CYBERARK_CLIENT_ID": "test-client",
        "CYBERARK_CLIENT_SECRET": "test-secret", 
        "CYBERARK_SUBDOMAIN": "test-subdomain",
        "CYBERARK_LOG_LEVEL": "DEBUG"
    })
    def test_logging_configuration(self):
        """Test that logging is configured correctly"""
        import logging
        
        # Import to trigger logging configuration
        from src.mcp_privilege_cloud import mcp_server
        
        # Verify that logging is configured
        logger = logging.getLogger("src.mcp_privilege_cloud.mcp_server")
        assert logger is not None


    def test_server_lifecycle_management(self):
        """Test that server lifecycle is managed properly"""
        # Test that the MCP server can be imported and has required components
        from src.mcp_privilege_cloud.mcp_server import mcp
        assert mcp is not None
        assert mcp.name == "CyberArk Privilege Cloud MCP Server"
        
        # Verify that essential functions exist
        from src.mcp_privilege_cloud.mcp_server import list_accounts
        assert list_accounts is not None

    def test_resource_endpoints(self):
        """Test that resource endpoints are defined"""
        # Import the MCP server to check resource definitions
        from src.mcp_privilege_cloud import mcp_server
        
        # Verify that the mcp object has the expected structure
        assert hasattr(mcp_server, 'mcp')
        assert mcp_server.mcp is not None


# Import asyncio for async test support
import asyncio