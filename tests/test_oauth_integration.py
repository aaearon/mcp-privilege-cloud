"""Integration tests for OAuth + Streamable HTTP wiring.

Tests the full integration of:
- FastMCP configured with CyberArkTokenVerifier and AuthSettings
- AppContext with session_manager
- execute_tool resolving per-user server via session manager
- OAuth env var configuration
- Backward compatibility with legacy service account mode
"""

import base64
import json
import os
import time

import pytest
from unittest.mock import AsyncMock, MagicMock, Mock, patch


def _make_jwt(claims: dict, header: dict | None = None) -> str:
    """Create a minimal JWT string (unsigned) for testing."""
    if header is None:
        header = {"alg": "RS256", "typ": "JWT", "kid": "test-key-id"}
    h = base64.urlsafe_b64encode(json.dumps(header).encode()).rstrip(b"=").decode()
    p = base64.urlsafe_b64encode(json.dumps(claims).encode()).rstrip(b"=").decode()
    s = base64.urlsafe_b64encode(b"fakesig").rstrip(b"=").decode()
    return f"{h}.{p}.{s}"


def _default_claims(**overrides: object) -> dict:
    """Return default valid JWT claims with optional overrides."""
    claims = {
        "sub": "testuser@cyberark.cloud.12345",
        "iss": "https://abc1234.id.cyberark.cloud/mcpprivilegecloud/",
        "aud": "mcpprivilegecloud",
        "exp": int(time.time()) + 3600,
        "iat": int(time.time()),
        "unique_name": "testuser@abc1234.cyberark.cloud",
        "subdomain": "abc1234",
        "platform_domain": "cyberark.cloud",
    }
    claims.update(overrides)
    return claims


class TestOAuthEnvVarConfiguration:
    """Test OAuth environment variable detection and configuration."""

    def test_oauth_mode_detected_when_env_vars_set(self):
        """OAuth mode should be detected when CYBERARK_IDENTITY_TENANT_URL is set."""
        from mcp_privilege_cloud.mcp_server import is_oauth_mode

        with patch.dict(os.environ, {
            "CYBERARK_IDENTITY_TENANT_URL": "https://abc1234.id.cyberark.cloud",
        }):
            assert is_oauth_mode() is True

    def test_legacy_mode_when_no_oauth_vars(self):
        """Legacy mode should be detected when OAuth env vars are absent."""
        from mcp_privilege_cloud.mcp_server import is_oauth_mode

        with patch.dict(os.environ, {}, clear=True):
            assert is_oauth_mode() is False

    def test_legacy_mode_with_only_client_id(self):
        """Legacy mode when only CYBERARK_CLIENT_ID is set."""
        from mcp_privilege_cloud.mcp_server import is_oauth_mode

        with patch.dict(os.environ, {
            "CYBERARK_CLIENT_ID": "svc-account",
            "CYBERARK_CLIENT_SECRET": "secret",
        }, clear=True):
            assert is_oauth_mode() is False


class TestAppContextWithSessionManager:
    """Test AppContext supports session_manager field."""

    def test_app_context_has_session_manager(self):
        """AppContext should accept session_manager parameter."""
        from mcp_privilege_cloud.mcp_server import AppContext
        from mcp_privilege_cloud.session_manager import UserSessionManager

        manager = UserSessionManager()
        ctx = AppContext(server=None, session_manager=manager)

        assert ctx.session_manager is manager

    def test_app_context_session_manager_optional(self):
        """AppContext.session_manager should be optional for backward compat."""
        from mcp_privilege_cloud.mcp_server import AppContext

        mock_server = MagicMock()
        ctx = AppContext(server=mock_server)

        assert ctx.session_manager is None

    def test_app_context_backward_compat_server_field(self):
        """AppContext.server should still work for legacy mode."""
        from mcp_privilege_cloud.mcp_server import AppContext

        mock_server = MagicMock()
        ctx = AppContext(server=mock_server)

        assert ctx.server is mock_server


class TestExecuteToolOAuthResolution:
    """Test execute_tool resolving per-user server via session manager."""

    @pytest.mark.asyncio
    async def test_execute_tool_uses_session_manager_when_available(self):
        """execute_tool should use session_manager when auth context provides a token."""
        from mcp_privilege_cloud.mcp_server import AppContext, execute_tool
        from mcp_privilege_cloud.session_manager import UserSessionManager

        # Create mock session manager
        mock_server = AsyncMock()
        mock_server.list_accounts = AsyncMock(return_value=[])

        mock_manager = AsyncMock(spec=UserSessionManager)
        mock_manager.get_or_create = AsyncMock(return_value=mock_server)

        # Create mock context with session_manager and access token
        claims = _default_claims()
        jwt_token = _make_jwt(claims)

        ctx = Mock()
        ctx.request_context.lifespan_context = AppContext(
            server=None, session_manager=mock_manager
        )

        # Mock get_access_token to return an AccessToken-like object
        mock_access_token = Mock()
        mock_access_token.token = jwt_token
        mock_access_token.client_id = claims["sub"]

        with patch(
            "mcp_privilege_cloud.mcp_server.get_access_token",
            return_value=mock_access_token,
        ):
            result = await execute_tool("list_accounts", ctx=ctx)

        mock_manager.get_or_create.assert_called_once()
        mock_server.list_accounts.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_tool_falls_back_to_legacy_server(self):
        """execute_tool should fall back to ctx.server when no session manager."""
        from mcp_privilege_cloud.mcp_server import AppContext, execute_tool

        mock_server = AsyncMock()
        mock_server.list_accounts = AsyncMock(return_value=[])

        ctx = Mock()
        ctx.request_context.lifespan_context = AppContext(server=mock_server)

        # No access token in context → should fall back to legacy server
        with patch(
            "mcp_privilege_cloud.mcp_server.get_access_token",
            return_value=None,
        ):
            result = await execute_tool("list_accounts", ctx=ctx)

        mock_server.list_accounts.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_tool_extracts_username_from_token(self):
        """execute_tool should extract username from JWT claims for session creation."""
        from mcp_privilege_cloud.mcp_server import AppContext, execute_tool
        from mcp_privilege_cloud.session_manager import UserSessionManager

        mock_server = AsyncMock()
        mock_server.list_accounts = AsyncMock(return_value=[])

        mock_manager = AsyncMock(spec=UserSessionManager)
        mock_manager.get_or_create = AsyncMock(return_value=mock_server)

        claims = _default_claims()
        jwt_token = _make_jwt(claims)

        ctx = Mock()
        ctx.request_context.lifespan_context = AppContext(
            server=None, session_manager=mock_manager
        )

        mock_access_token = Mock()
        mock_access_token.token = jwt_token
        mock_access_token.client_id = claims["sub"]

        with patch(
            "mcp_privilege_cloud.mcp_server.get_access_token",
            return_value=mock_access_token,
        ):
            await execute_tool("list_accounts", ctx=ctx)

        # Verify username was extracted from client_id
        call_kwargs = mock_manager.get_or_create.call_args
        assert call_kwargs.kwargs["username"] == claims["sub"]
        assert call_kwargs.kwargs["jwt_token"] == jwt_token


class TestAppLifespanOAuthMode:
    """Test app_lifespan behavior in OAuth mode."""

    @pytest.mark.asyncio
    async def test_lifespan_creates_session_manager_in_oauth_mode(self):
        """In OAuth mode, app_lifespan should create a UserSessionManager."""
        from mcp_privilege_cloud.mcp_server import app_lifespan

        with patch.dict(os.environ, {
            "CYBERARK_IDENTITY_TENANT_URL": "https://abc1234.id.cyberark.cloud",
        }):
            with patch("mcp_privilege_cloud.mcp_server.is_oauth_mode", return_value=True):
                mock_fastmcp = MagicMock()
                async with app_lifespan(mock_fastmcp) as app_ctx:
                    assert app_ctx.session_manager is not None
                    assert app_ctx.server is None

    @pytest.mark.asyncio
    async def test_lifespan_creates_server_in_legacy_mode(self):
        """In legacy mode, app_lifespan should create a CyberArkMCPServer."""
        from mcp_privilege_cloud.mcp_server import app_lifespan

        with patch("mcp_privilege_cloud.mcp_server.is_oauth_mode", return_value=False):
            with patch(
                "mcp_privilege_cloud.mcp_server.CyberArkMCPServer.from_environment"
            ) as mock_from_env:
                mock_server = MagicMock()
                mock_server._executor = MagicMock()
                mock_from_env.return_value = mock_server

                mock_fastmcp = MagicMock()
                async with app_lifespan(mock_fastmcp) as app_ctx:
                    assert app_ctx.server is mock_server
                    assert app_ctx.session_manager is None

    @pytest.mark.asyncio
    async def test_lifespan_shutdown_calls_session_manager_shutdown(self):
        """On shutdown, lifespan should call session_manager.shutdown()."""
        from mcp_privilege_cloud.mcp_server import app_lifespan

        with patch.dict(os.environ, {
            "CYBERARK_IDENTITY_TENANT_URL": "https://abc1234.id.cyberark.cloud",
        }):
            with patch("mcp_privilege_cloud.mcp_server.is_oauth_mode", return_value=True):
                with patch(
                    "mcp_privilege_cloud.mcp_server.UserSessionManager"
                ) as MockManager:
                    mock_manager = AsyncMock()
                    MockManager.return_value = mock_manager

                    mock_fastmcp = MagicMock()
                    async with app_lifespan(mock_fastmcp) as app_ctx:
                        pass

                    mock_manager.shutdown.assert_called_once()


class TestMCPServerOAuthInit:
    """Test FastMCP initialization with OAuth settings."""

    def test_create_mcp_server_oauth_creates_verifier(self):
        """create_mcp_server should create a CyberArkTokenVerifier in OAuth mode."""
        from mcp_privilege_cloud.mcp_server import create_mcp_server

        with patch.dict(os.environ, {
            "CYBERARK_IDENTITY_TENANT_URL": "https://abc1234.id.cyberark.cloud",
            "MCP_HOST": "127.0.0.1",
            "MCP_PORT": "8000",
        }):
            with patch("mcp_privilege_cloud.mcp_server.is_oauth_mode", return_value=True):
                with patch("mcp_privilege_cloud.mcp_server.FastMCP") as MockFastMCP:
                    create_mcp_server()

                    # Verify FastMCP was called with token_verifier and auth
                    call_kwargs = MockFastMCP.call_args.kwargs
                    assert "token_verifier" in call_kwargs
                    assert call_kwargs["token_verifier"] is not None
                    assert "auth" in call_kwargs
                    assert call_kwargs["auth"] is not None

    def test_create_mcp_server_legacy_no_verifier(self):
        """create_mcp_server in legacy mode should not set token_verifier."""
        from mcp_privilege_cloud.mcp_server import create_mcp_server

        with patch("mcp_privilege_cloud.mcp_server.is_oauth_mode", return_value=False):
            with patch("mcp_privilege_cloud.mcp_server.FastMCP") as MockFastMCP:
                create_mcp_server()

                call_kwargs = MockFastMCP.call_args.kwargs
                # In legacy mode, no token_verifier or auth
                assert call_kwargs.get("token_verifier") is None
                assert call_kwargs.get("auth") is None
