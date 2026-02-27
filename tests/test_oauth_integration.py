"""Integration tests for OAuth + Streamable HTTP wiring.

Tests the full integration of:
- FastMCP configured with CyberArkTokenVerifier and AuthSettings
- AppContext with is_oauth flag
- execute_tool verifying user identity, then using shared service account server
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


class TestAppContextIsOAuth:
    """Test AppContext supports is_oauth field."""

    def test_app_context_has_is_oauth(self):
        """AppContext should accept is_oauth parameter."""
        from mcp_privilege_cloud.mcp_server import AppContext

        ctx = AppContext(server=MagicMock(), is_oauth=True)
        assert ctx.is_oauth is True

    def test_app_context_is_oauth_defaults_false(self):
        """AppContext.is_oauth should default to False for legacy compat."""
        from mcp_privilege_cloud.mcp_server import AppContext

        mock_server = MagicMock()
        ctx = AppContext(server=mock_server)
        assert ctx.is_oauth is False

    def test_app_context_backward_compat_server_field(self):
        """AppContext.server should still work for legacy mode."""
        from mcp_privilege_cloud.mcp_server import AppContext

        mock_server = MagicMock()
        ctx = AppContext(server=mock_server)
        assert ctx.server is mock_server


class TestExecuteToolOAuthResolution:
    """Test execute_tool verifying identity and using service account server."""

    @pytest.mark.asyncio
    async def test_execute_tool_uses_service_account_server_in_oauth_mode(self):
        """execute_tool should verify identity via token, then use app_ctx.server."""
        from mcp_privilege_cloud.mcp_server import AppContext, execute_tool

        mock_server = AsyncMock()
        mock_server.list_accounts = AsyncMock(return_value=[])

        claims = _default_claims()
        jwt_token = _make_jwt(claims)

        ctx = Mock()
        ctx.request_context.lifespan_context = AppContext(
            server=mock_server, is_oauth=True
        )

        mock_access_token = Mock()
        mock_access_token.token = jwt_token
        mock_access_token.client_id = claims["sub"]

        with patch(
            "mcp_privilege_cloud.mcp_server.get_access_token",
            return_value=mock_access_token,
        ):
            result = await execute_tool("list_accounts", ctx=ctx)

        mock_server.list_accounts.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_tool_falls_back_to_legacy_server(self):
        """execute_tool should use ctx.server when is_oauth=False."""
        from mcp_privilege_cloud.mcp_server import AppContext, execute_tool

        mock_server = AsyncMock()
        mock_server.list_accounts = AsyncMock(return_value=[])

        ctx = Mock()
        ctx.request_context.lifespan_context = AppContext(server=mock_server)

        result = await execute_tool("list_accounts", ctx=ctx)
        mock_server.list_accounts.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_tool_rejects_unauthenticated_oauth(self):
        """execute_tool should reject unauthenticated requests in OAuth mode."""
        from mcp_privilege_cloud.mcp_server import AppContext, execute_tool

        mock_server = AsyncMock()

        ctx = Mock()
        ctx.request_context.lifespan_context = AppContext(
            server=mock_server, is_oauth=True
        )

        with patch(
            "mcp_privilege_cloud.mcp_server.get_access_token",
            return_value=None,
        ):
            with pytest.raises(PermissionError, match="OAuth mode requires authentication"):
                await execute_tool("list_accounts", ctx=ctx)


class TestAppLifespanOAuthMode:
    """Test app_lifespan behavior in OAuth mode."""

    @pytest.mark.asyncio
    async def test_lifespan_creates_oauth_context(self):
        """In OAuth mode, app_lifespan should create context with is_oauth=True."""
        from mcp_privilege_cloud.mcp_server import app_lifespan

        with patch.dict(os.environ, {
            "CYBERARK_IDENTITY_TENANT_URL": "https://abc1234.id.cyberark.cloud",
        }):
            with patch("mcp_privilege_cloud.mcp_server.is_oauth_mode", return_value=True):
                with patch(
                    "mcp_privilege_cloud.mcp_server.CyberArkMCPServer.from_environment"
                ) as mock_from_env:
                    mock_server = MagicMock()
                    mock_server._executor = MagicMock()
                    mock_from_env.return_value = mock_server

                    mock_fastmcp = MagicMock()
                    async with app_lifespan(mock_fastmcp) as app_ctx:
                        assert app_ctx.is_oauth is True
                        assert app_ctx.server is not None

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
                    assert app_ctx.is_oauth is False

    @pytest.mark.asyncio
    async def test_lifespan_shutdown_cleans_up_executor(self):
        """On shutdown, lifespan should call executor.shutdown()."""
        from mcp_privilege_cloud.mcp_server import app_lifespan

        with patch("mcp_privilege_cloud.mcp_server.is_oauth_mode", return_value=True):
            with patch(
                "mcp_privilege_cloud.mcp_server.CyberArkMCPServer.from_environment"
            ) as mock_from_env:
                mock_server = MagicMock()
                mock_executor = MagicMock()
                mock_server._executor = mock_executor
                mock_from_env.return_value = mock_server

                mock_fastmcp = MagicMock()
                async with app_lifespan(mock_fastmcp) as app_ctx:
                    pass

                mock_executor.shutdown.assert_called_once_with(wait=True)


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
                assert call_kwargs.get("token_verifier") is None
                assert call_kwargs.get("auth") is None
