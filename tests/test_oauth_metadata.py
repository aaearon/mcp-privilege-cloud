"""Tests for OAuth discovery and Dynamic Client Registration endpoints.

Tests the RFC 8414 metadata endpoint and RFC 7591 DCR proxy that enable
claude.ai OAuth flow compatibility with CyberArk Identity.
"""

import os

import httpx
import pytest
from unittest.mock import AsyncMock, patch


# Sample OIDC discovery response from CyberArk Identity
SAMPLE_OIDC_DISCOVERY = {
    "issuer": "https://abc1234.id.cyberark.cloud/",
    "authorization_endpoint": "https://abc1234.id.cyberark.cloud/OAuth2/Authorize/__idaptive_cybr_user_oidc",
    "token_endpoint": "https://abc1234.id.cyberark.cloud/OAuth2/Token/__idaptive_cybr_user_oidc",
    "userinfo_endpoint": "https://abc1234.id.cyberark.cloud/OAuth2/UserInfo/__idaptive_cybr_user_oidc",
    "jwks_uri": "https://abc1234.id.cyberark.cloud/OAuth2/Keys/__idaptive_cybr_user_oidc",
    "response_types_supported": ["code", "id_token", "code id_token"],
    "code_challenge_methods_supported": ["S256"],
    "scopes_supported": ["openid", "profile", "email"],
    "subject_types_supported": ["public"],
    "id_token_signing_alg_values_supported": ["RS256"],
}

SERVER_URL = "https://mcp.example.com"


class TestFetchOidcDiscovery:
    """Test the _fetch_oidc_discovery helper function."""

    @pytest.mark.asyncio
    async def test_fetches_and_returns_oidc_config(self):
        """Should fetch OIDC discovery from tenant URL and return parsed JSON."""
        from mcp_privilege_cloud.mcp_server import _fetch_oidc_discovery

        # httpx.Response.json() is sync, raise_for_status() is sync
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = lambda: SAMPLE_OIDC_DISCOVERY
        mock_response.raise_for_status = lambda: None

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("mcp_privilege_cloud.mcp_server.httpx.AsyncClient", return_value=mock_client):
            # Clear any cached value from previous tests
            import mcp_privilege_cloud.mcp_server as mod
            mod._oidc_discovery_cache = None

            result = await _fetch_oidc_discovery("https://abc1234.id.cyberark.cloud")

        assert result["issuer"] == "https://abc1234.id.cyberark.cloud/"
        assert "authorization_endpoint" in result
        mock_client.get.assert_called_once_with(
            "https://abc1234.id.cyberark.cloud/.well-known/openid-configuration"
        )

    @pytest.mark.asyncio
    async def test_caches_oidc_discovery(self):
        """Should fetch OIDC discovery once and return cached result on subsequent calls."""
        from mcp_privilege_cloud.mcp_server import _fetch_oidc_discovery

        import mcp_privilege_cloud.mcp_server as mod
        mod._oidc_discovery_cache = None

        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = lambda: SAMPLE_OIDC_DISCOVERY
        mock_response.raise_for_status = lambda: None

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("mcp_privilege_cloud.mcp_server.httpx.AsyncClient", return_value=mock_client):
            result1 = await _fetch_oidc_discovery("https://abc1234.id.cyberark.cloud")
            result2 = await _fetch_oidc_discovery("https://abc1234.id.cyberark.cloud")

        assert result1 is result2
        # Only one HTTP call despite two invocations
        mock_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_strips_trailing_slash_from_tenant_url(self):
        """Should handle tenant URLs with trailing slashes."""
        from mcp_privilege_cloud.mcp_server import _fetch_oidc_discovery

        import mcp_privilege_cloud.mcp_server as mod
        mod._oidc_discovery_cache = None

        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = lambda: SAMPLE_OIDC_DISCOVERY
        mock_response.raise_for_status = lambda: None

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("mcp_privilege_cloud.mcp_server.httpx.AsyncClient", return_value=mock_client):
            await _fetch_oidc_discovery("https://abc1234.id.cyberark.cloud/")

        mock_client.get.assert_called_once_with(
            "https://abc1234.id.cyberark.cloud/.well-known/openid-configuration"
        )

    @pytest.mark.asyncio
    async def test_raises_on_http_error(self):
        """Should propagate HTTP errors from OIDC discovery endpoint."""
        from mcp_privilege_cloud.mcp_server import _fetch_oidc_discovery

        import mcp_privilege_cloud.mcp_server as mod
        mod._oidc_discovery_cache = None

        mock_request = httpx.Request("GET", "https://example.com/.well-known/openid-configuration")
        mock_response = httpx.Response(500, request=mock_request)

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("mcp_privilege_cloud.mcp_server.httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(httpx.HTTPStatusError):
                await _fetch_oidc_discovery("https://abc1234.id.cyberark.cloud")


class TestBuildOAuthMetadata:
    """Test the _build_oauth_metadata helper."""

    def test_returns_correct_rfc8414_fields(self):
        """Should return RFC 8414 metadata mapped from OIDC discovery."""
        from mcp_privilege_cloud.mcp_server import _build_oauth_metadata

        metadata = _build_oauth_metadata(SAMPLE_OIDC_DISCOVERY, SERVER_URL)

        assert metadata["issuer"] == SAMPLE_OIDC_DISCOVERY["issuer"]
        assert metadata["authorization_endpoint"] == SAMPLE_OIDC_DISCOVERY["authorization_endpoint"]
        assert metadata["token_endpoint"] == SAMPLE_OIDC_DISCOVERY["token_endpoint"]
        assert metadata["response_types_supported"] == ["code", "id_token", "code id_token"]
        assert metadata["code_challenge_methods_supported"] == ["S256"]
        assert metadata["scopes_supported"] == ["openid", "profile", "email"]

    def test_includes_registration_endpoint(self):
        """Should include registration_endpoint pointing to our server."""
        from mcp_privilege_cloud.mcp_server import _build_oauth_metadata

        metadata = _build_oauth_metadata(SAMPLE_OIDC_DISCOVERY, SERVER_URL)

        assert metadata["registration_endpoint"] == f"{SERVER_URL}/register"

    def test_includes_grant_types_and_auth_methods(self):
        """Should include grant_types_supported and token_endpoint_auth_methods."""
        from mcp_privilege_cloud.mcp_server import _build_oauth_metadata

        metadata = _build_oauth_metadata(SAMPLE_OIDC_DISCOVERY, SERVER_URL)

        assert metadata["grant_types_supported"] == ["authorization_code", "refresh_token"]
        assert metadata["token_endpoint_auth_methods_supported"] == ["none"]

    def test_defaults_when_oidc_fields_missing(self):
        """Should use sensible defaults when OIDC discovery omits optional fields."""
        from mcp_privilege_cloud.mcp_server import _build_oauth_metadata

        minimal_oidc = {
            "issuer": "https://abc1234.id.cyberark.cloud/",
            "authorization_endpoint": "https://abc1234.id.cyberark.cloud/OAuth2/Authorize/x",
            "token_endpoint": "https://abc1234.id.cyberark.cloud/OAuth2/Token/x",
        }

        metadata = _build_oauth_metadata(minimal_oidc, SERVER_URL)

        assert metadata["response_types_supported"] == ["code"]
        assert metadata["code_challenge_methods_supported"] == ["S256"]
        assert "scopes_supported" not in metadata

    def test_excludes_none_scopes(self):
        """Should not include scopes_supported when not in OIDC config."""
        from mcp_privilege_cloud.mcp_server import _build_oauth_metadata

        minimal_oidc = {
            "issuer": "https://abc1234.id.cyberark.cloud/",
            "authorization_endpoint": "https://abc1234.id.cyberark.cloud/OAuth2/Authorize/x",
            "token_endpoint": "https://abc1234.id.cyberark.cloud/OAuth2/Token/x",
        }

        metadata = _build_oauth_metadata(minimal_oidc, SERVER_URL)

        assert "scopes_supported" not in metadata


class TestDynamicClientRegistration:
    """Test the /register DCR proxy endpoint."""

    def test_dcr_returns_cyberark_oidc_client_id(self):
        """DCR should return the pre-configured CyberArk Identity OIDC app ID."""
        from mcp_privilege_cloud.mcp_server import _build_dcr_response

        body = {
            "client_name": "Claude",
            "redirect_uris": ["https://claude.ai/api/mcp/auth_callback"],
        }

        response = _build_dcr_response(body)

        assert response["client_id"] == "mcpprivilegecloud"
        assert response["token_endpoint_auth_method"] == "none"
        assert response["grant_types"] == ["authorization_code", "refresh_token"]
        assert response["response_types"] == ["code"]

    def test_dcr_echoes_client_name(self):
        """DCR should echo back the client_name from the request."""
        from mcp_privilege_cloud.mcp_server import _build_dcr_response

        response = _build_dcr_response({"client_name": "My MCP Client"})
        assert response["client_name"] == "My MCP Client"

    def test_dcr_echoes_redirect_uris(self):
        """DCR should echo back redirect_uris from the request."""
        from mcp_privilege_cloud.mcp_server import _build_dcr_response

        uris = ["https://claude.ai/api/mcp/auth_callback"]
        response = _build_dcr_response({"redirect_uris": uris})
        assert response["redirect_uris"] == uris

    def test_dcr_defaults_for_empty_body(self):
        """DCR should use defaults when request body is empty."""
        from mcp_privilege_cloud.mcp_server import _build_dcr_response

        response = _build_dcr_response({})

        assert response["client_id"] == "mcpprivilegecloud"
        assert response["client_name"] == "MCP Client"
        assert response["redirect_uris"] == []


class TestOAuthRouteRegistration:
    """Test that OAuth routes are registered correctly."""

    def test_routes_registered_in_oauth_mode(self):
        """OAuth routes should be registered in OAuth mode."""
        with patch.dict(os.environ, {
            "CYBERARK_IDENTITY_TENANT_URL": "https://abc1234.id.cyberark.cloud",
        }):
            with patch("mcp_privilege_cloud.mcp_server.is_oauth_mode", return_value=True):
                import mcp_privilege_cloud.mcp_server as mod

                assert hasattr(mod, '_register_oauth_routes')

    def test_routes_not_registered_in_legacy_mode(self):
        """OAuth routes should NOT be registered when OAuth is disabled."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("mcp_privilege_cloud.mcp_server.is_oauth_mode", return_value=False):
                from mcp_privilege_cloud.mcp_server import is_oauth_mode
                assert is_oauth_mode() is False
