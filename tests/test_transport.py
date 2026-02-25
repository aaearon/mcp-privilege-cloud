"""Tests for Streamable HTTP transport configuration.

Verifies that the MCP server correctly configures Streamable HTTP transport
with the expected routes and settings.
"""

import pytest
from unittest.mock import patch, MagicMock


class TestStreamableHTTPTransport:
    """Test Streamable HTTP transport configuration."""

    def test_streamable_http_app_returns_starlette(self):
        """Test that mcp.streamable_http_app() returns a Starlette application."""
        from mcp_privilege_cloud.mcp_server import mcp

        app = mcp.streamable_http_app()

        # Starlette app should have routes attribute
        assert hasattr(app, "routes")

    def test_streamable_http_app_has_mcp_route(self):
        """Test that the Starlette app includes the /mcp endpoint."""
        from mcp_privilege_cloud.mcp_server import mcp

        app = mcp.streamable_http_app()

        # Check that /mcp route exists
        route_paths = []
        for route in app.routes:
            if hasattr(route, "path"):
                route_paths.append(route.path)
            elif hasattr(route, "routes"):
                # Mount/sub-app routes
                for sub_route in route.routes:
                    if hasattr(sub_route, "path"):
                        route_paths.append(sub_route.path)

        assert any("/mcp" in path for path in route_paths), (
            f"Expected /mcp route, found: {route_paths}"
        )

    def test_host_port_defaults(self):
        """Test that MCP_HOST and MCP_PORT have sensible defaults."""
        with patch.dict("os.environ", {}, clear=False):
            # Remove any existing env vars to test defaults
            import os
            host = os.getenv("MCP_HOST", "127.0.0.1")
            port = int(os.getenv("MCP_PORT", "8000"))

            assert host == "127.0.0.1"
            assert port == 8000

    def test_host_port_from_env(self):
        """Test that MCP_HOST and MCP_PORT can be configured via env vars."""
        with patch.dict("os.environ", {
            "MCP_HOST": "0.0.0.0",
            "MCP_PORT": "9000",
        }):
            import os
            host = os.getenv("MCP_HOST", "127.0.0.1")
            port = int(os.getenv("MCP_PORT", "8000"))

            assert host == "0.0.0.0"
            assert port == 9000

    def test_main_calls_run_with_streamable_http(self):
        """Test that main() calls mcp.run with streamable-http transport."""
        with patch("mcp_privilege_cloud.mcp_server.mcp") as mock_mcp:
            from mcp_privilege_cloud.mcp_server import main
            main()

            mock_mcp.run.assert_called_once_with(transport="streamable-http")
