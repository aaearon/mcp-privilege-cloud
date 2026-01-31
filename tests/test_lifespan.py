"""
Lifespan Management Tests (RED then GREEN Phase)

Tests for MCP server lifecycle management using FastMCP lifespan.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import os


class TestAppContext:
    """Test AppContext dataclass"""

    def test_app_context_holds_server(self):
        """AppContext should hold a CyberArkMCPServer instance"""
        from mcp_privilege_cloud.mcp_server import AppContext

        mock_server = Mock()
        ctx = AppContext(server=mock_server)
        assert ctx.server is mock_server

    def test_app_context_is_dataclass(self):
        """AppContext should be a dataclass for proper typing"""
        from mcp_privilege_cloud.mcp_server import AppContext
        from dataclasses import is_dataclass

        assert is_dataclass(AppContext)


class TestLifespanContextManager:
    """Test app_lifespan async context manager"""

    @pytest.mark.asyncio
    async def test_lifespan_initializes_server(self):
        """Lifespan should create CyberArkMCPServer on startup"""
        from mcp_privilege_cloud.mcp_server import app_lifespan, mcp

        mock_server = Mock()

        with patch.dict(os.environ, {
            'CYBERARK_CLIENT_ID': 'test-client',
            'CYBERARK_CLIENT_SECRET': 'test-secret'
        }):
            with patch('mcp_privilege_cloud.mcp_server.CyberArkMCPServer') as mock_class:
                mock_class.from_environment.return_value = mock_server

                async with app_lifespan(mcp) as ctx:
                    assert ctx.server is mock_server
                    mock_class.from_environment.assert_called_once()

    @pytest.mark.asyncio
    async def test_lifespan_context_has_server_attribute(self):
        """Yielded context should have server attribute"""
        from mcp_privilege_cloud.mcp_server import app_lifespan, mcp, AppContext

        with patch.dict(os.environ, {
            'CYBERARK_CLIENT_ID': 'test-client',
            'CYBERARK_CLIENT_SECRET': 'test-secret'
        }):
            with patch('mcp_privilege_cloud.mcp_server.CyberArkMCPServer') as mock_class:
                mock_class.from_environment.return_value = Mock()

                async with app_lifespan(mcp) as ctx:
                    assert isinstance(ctx, AppContext)
                    assert hasattr(ctx, 'server')

    @pytest.mark.asyncio
    async def test_lifespan_cleanup_on_shutdown(self):
        """Lifespan should cleanup executor on shutdown"""
        from mcp_privilege_cloud.mcp_server import app_lifespan, mcp

        mock_executor = Mock()
        mock_server = Mock()
        mock_server._executor = mock_executor

        with patch.dict(os.environ, {
            'CYBERARK_CLIENT_ID': 'test-client',
            'CYBERARK_CLIENT_SECRET': 'test-secret'
        }):
            with patch('mcp_privilege_cloud.mcp_server.CyberArkMCPServer') as mock_class:
                mock_class.from_environment.return_value = mock_server

                async with app_lifespan(mcp) as ctx:
                    pass  # Context active

                # After exit, executor should be shut down
                mock_executor.shutdown.assert_called_once_with(wait=True)

    @pytest.mark.asyncio
    async def test_lifespan_handles_server_without_executor(self):
        """Lifespan should handle servers without _executor gracefully"""
        from mcp_privilege_cloud.mcp_server import app_lifespan, mcp

        mock_server = Mock(spec=['list_accounts'])  # No _executor attribute

        with patch.dict(os.environ, {
            'CYBERARK_CLIENT_ID': 'test-client',
            'CYBERARK_CLIENT_SECRET': 'test-secret'
        }):
            with patch('mcp_privilege_cloud.mcp_server.CyberArkMCPServer') as mock_class:
                mock_class.from_environment.return_value = mock_server

                # Should not raise when no _executor exists
                async with app_lifespan(mcp) as ctx:
                    assert ctx.server is mock_server


class TestMCPServerWithLifespan:
    """Test that mcp server is configured with lifespan"""

    def test_mcp_has_lifespan_configured(self):
        """FastMCP instance should be created with lifespan parameter"""
        from mcp_privilege_cloud.mcp_server import mcp, app_lifespan

        # Check that lifespan is configured on the server
        # FastMCP stores lifespan function in _mcp_server.lifespan
        assert hasattr(mcp, '_mcp_server')
        assert hasattr(mcp._mcp_server, 'lifespan')
        # The lifespan should be our app_lifespan function
        assert mcp._mcp_server.lifespan is not None


class TestLifespanErrorHandling:
    """Test lifespan error handling"""

    @pytest.mark.asyncio
    async def test_lifespan_propagates_init_errors(self):
        """Lifespan should propagate server initialization errors"""
        from mcp_privilege_cloud.mcp_server import app_lifespan, mcp

        with patch.dict(os.environ, {
            'CYBERARK_CLIENT_ID': 'test-client',
            'CYBERARK_CLIENT_SECRET': 'test-secret'
        }):
            with patch('mcp_privilege_cloud.mcp_server.CyberArkMCPServer') as mock_class:
                mock_class.from_environment.side_effect = ValueError("Missing credentials")

                with pytest.raises(ValueError, match="Missing credentials"):
                    async with app_lifespan(mcp) as ctx:
                        pass

    @pytest.mark.asyncio
    async def test_lifespan_cleanup_runs_on_error(self):
        """Lifespan should run cleanup even if error occurs in context"""
        from mcp_privilege_cloud.mcp_server import app_lifespan, mcp

        mock_executor = Mock()
        mock_server = Mock()
        mock_server._executor = mock_executor

        with patch.dict(os.environ, {
            'CYBERARK_CLIENT_ID': 'test-client',
            'CYBERARK_CLIENT_SECRET': 'test-secret'
        }):
            with patch('mcp_privilege_cloud.mcp_server.CyberArkMCPServer') as mock_class:
                mock_class.from_environment.return_value = mock_server

                try:
                    async with app_lifespan(mcp) as ctx:
                        raise RuntimeError("Simulated error")
                except RuntimeError:
                    pass

                # Cleanup should still run
                mock_executor.shutdown.assert_called_once_with(wait=True)
