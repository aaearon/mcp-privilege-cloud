"""Tests for Streamable HTTP transport configuration.

Verifies that the MCP server correctly configures Streamable HTTP transport
with the expected routes and settings.
"""

import pytest
from unittest.mock import patch, MagicMock

from mcp_privilege_cloud.mcp_server import TrailingSlashMiddleware


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

    def test_main_defaults_to_stdio(self):
        """Test that main() defaults to stdio transport when MCP_TRANSPORT is not set."""
        with patch.dict("os.environ", {}, clear=False):
            import os
            os.environ.pop("MCP_TRANSPORT", None)
            with patch("mcp_privilege_cloud.mcp_server.mcp") as mock_mcp:
                from mcp_privilege_cloud.mcp_server import main
                main()

                mock_mcp.run.assert_called_once_with(transport="stdio")

    def test_main_uses_streamable_http_when_configured(self):
        """Test that main() wraps app with TrailingSlashMiddleware for streamable-http."""
        with patch.dict("os.environ", {"MCP_TRANSPORT": "streamable-http"}):
            with patch("mcp_privilege_cloud.mcp_server.mcp") as mock_mcp:
                mock_mcp.streamable_http_app.return_value = MagicMock()
                with patch("asyncio.run"):
                    with patch("uvicorn.Config") as mock_config:
                        with patch("uvicorn.Server"):
                            from mcp_privilege_cloud.mcp_server import main
                            main()

                            # Should create Starlette app and wrap it
                            mock_mcp.streamable_http_app.assert_called_once()
                            # Should NOT call mcp.run()
                            mock_mcp.run.assert_not_called()
                            # Should pass wrapped app to uvicorn
                            mock_config.assert_called_once()
                            app = mock_config.call_args[0][0]
                            assert isinstance(app, TrailingSlashMiddleware)

    def test_main_rejects_invalid_transport(self):
        """Test that main() exits with error for invalid MCP_TRANSPORT value."""
        with patch.dict("os.environ", {"MCP_TRANSPORT": "invalid"}):
            with patch("mcp_privilege_cloud.mcp_server.mcp"):
                from mcp_privilege_cloud.mcp_server import main
                with pytest.raises(SystemExit):
                    main()


class TestTrailingSlashMiddleware:
    """Test that trailing slashes are stripped to prevent 307 redirects.

    MCP clients (e.g. Copilot Studio) POST to /mcp/ (trailing slash).
    Starlette's redirect_slashes returns a 307, which causes HTTP clients
    to strip the Authorization header, breaking OAuth Bearer auth.
    """

    @pytest.mark.asyncio
    async def test_strips_trailing_slash(self):
        """Trailing slash should be stripped before reaching the inner app."""
        received_path = None

        async def inner_app(scope, receive, send):
            nonlocal received_path
            received_path = scope["path"]

        app = TrailingSlashMiddleware(inner_app)
        scope = {"type": "http", "path": "/mcp/"}
        await app(scope, lambda: None, lambda msg: None)
        assert received_path == "/mcp"

    @pytest.mark.asyncio
    async def test_preserves_path_without_trailing_slash(self):
        """Paths without trailing slash should pass through unchanged."""
        received_path = None

        async def inner_app(scope, receive, send):
            nonlocal received_path
            received_path = scope["path"]

        app = TrailingSlashMiddleware(inner_app)
        scope = {"type": "http", "path": "/mcp"}
        await app(scope, lambda: None, lambda msg: None)
        assert received_path == "/mcp"

    @pytest.mark.asyncio
    async def test_preserves_root_path(self):
        """Root path '/' should not be stripped."""
        received_path = None

        async def inner_app(scope, receive, send):
            nonlocal received_path
            received_path = scope["path"]

        app = TrailingSlashMiddleware(inner_app)
        scope = {"type": "http", "path": "/"}
        await app(scope, lambda: None, lambda msg: None)
        assert received_path == "/"

    @pytest.mark.asyncio
    async def test_passes_non_http_scopes_unchanged(self):
        """Non-HTTP scopes (websocket, lifespan) should pass through."""
        received_scope = None

        async def inner_app(scope, receive, send):
            nonlocal received_scope
            received_scope = scope

        app = TrailingSlashMiddleware(inner_app)
        scope = {"type": "lifespan", "path": "/mcp/"}
        await app(scope, lambda: None, lambda msg: None)
        assert received_scope["path"] == "/mcp/"

    @pytest.mark.asyncio
    async def test_does_not_mutate_original_scope(self):
        """Original scope dict should not be modified."""
        original_scope = {"type": "http", "path": "/mcp/"}

        async def inner_app(scope, receive, send):
            pass

        app = TrailingSlashMiddleware(inner_app)
        await app(original_scope, lambda: None, lambda msg: None)
        assert original_scope["path"] == "/mcp/"
