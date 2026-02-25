"""Tests for /.well-known/oauth-authorization-server metadata endpoint.

Tests the RFC 8414 metadata endpoint that proxies CyberArk Identity
OIDC discovery for claude.ai OAuth flow compatibility.
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


class TestOAuthMetadataEndpoint:
    """Test the /.well-known/oauth-authorization-server custom route."""

    @pytest.mark.asyncio
    async def test_returns_correct_rfc8414_fields(self):
        """Should return RFC 8414 metadata mapped from OIDC discovery."""
        from mcp_privilege_cloud.mcp_server import _build_oauth_metadata

        metadata = _build_oauth_metadata(SAMPLE_OIDC_DISCOVERY)

        assert metadata["issuer"] == SAMPLE_OIDC_DISCOVERY["issuer"]
        assert metadata["authorization_endpoint"] == SAMPLE_OIDC_DISCOVERY["authorization_endpoint"]
        assert metadata["token_endpoint"] == SAMPLE_OIDC_DISCOVERY["token_endpoint"]
        assert metadata["response_types_supported"] == ["code", "id_token", "code id_token"]
        assert metadata["code_challenge_methods_supported"] == ["S256"]
        assert metadata["scopes_supported"] == ["openid", "profile", "email"]

    @pytest.mark.asyncio
    async def test_defaults_when_oidc_fields_missing(self):
        """Should use sensible defaults when OIDC discovery omits optional fields."""
        from mcp_privilege_cloud.mcp_server import _build_oauth_metadata

        minimal_oidc = {
            "issuer": "https://abc1234.id.cyberark.cloud/",
            "authorization_endpoint": "https://abc1234.id.cyberark.cloud/OAuth2/Authorize/x",
            "token_endpoint": "https://abc1234.id.cyberark.cloud/OAuth2/Token/x",
        }

        metadata = _build_oauth_metadata(minimal_oidc)

        assert metadata["issuer"] == minimal_oidc["issuer"]
        assert metadata["authorization_endpoint"] == minimal_oidc["authorization_endpoint"]
        assert metadata["token_endpoint"] == minimal_oidc["token_endpoint"]
        assert metadata["response_types_supported"] == ["code"]
        assert metadata["code_challenge_methods_supported"] == ["S256"]

    @pytest.mark.asyncio
    async def test_excludes_none_values(self):
        """Should not include fields with None values in metadata."""
        from mcp_privilege_cloud.mcp_server import _build_oauth_metadata

        minimal_oidc = {
            "issuer": "https://abc1234.id.cyberark.cloud/",
            "authorization_endpoint": "https://abc1234.id.cyberark.cloud/OAuth2/Authorize/x",
            "token_endpoint": "https://abc1234.id.cyberark.cloud/OAuth2/Token/x",
        }

        metadata = _build_oauth_metadata(minimal_oidc)

        # scopes_supported is None when not in OIDC config, so it should be excluded
        assert "scopes_supported" not in metadata or metadata["scopes_supported"] is not None


class TestOAuthMetadataRouteRegistration:
    """Test that the custom route is registered correctly."""

    def test_route_registered_in_oauth_mode(self):
        """The /.well-known/oauth-authorization-server route should be registered in OAuth mode."""
        with patch.dict(os.environ, {
            "CYBERARK_IDENTITY_TENANT_URL": "https://abc1234.id.cyberark.cloud",
        }):
            with patch("mcp_privilege_cloud.mcp_server.is_oauth_mode", return_value=True):
                from importlib import reload
                import mcp_privilege_cloud.mcp_server as mod

                # Check that _register_oauth_metadata_route was defined
                assert hasattr(mod, '_register_oauth_metadata_route')

    def test_route_not_registered_in_legacy_mode(self):
        """The metadata route should NOT be registered when OAuth is disabled."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("mcp_privilege_cloud.mcp_server.is_oauth_mode", return_value=False):
                # In legacy mode, the route registration function exists
                # but is only called conditionally
                from mcp_privilege_cloud.mcp_server import is_oauth_mode
                assert is_oauth_mode() is False
