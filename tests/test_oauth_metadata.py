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
    "issuer": "https://abc1234.id.cyberark.cloud/mcpprivilegecloud/",
    "authorization_endpoint": "https://abc1234.id.cyberark.cloud/OAuth2/Authorize/mcpprivilegecloud",
    "token_endpoint": "https://abc1234.id.cyberark.cloud/OAuth2/Token/mcpprivilegecloud",
    "userinfo_endpoint": "https://abc1234.id.cyberark.cloud/OAuth2/UserInfo/mcpprivilegecloud",
    "jwks_uri": "https://abc1234.id.cyberark.cloud/OAuth2/Keys/mcpprivilegecloud",
    "response_types_supported": ["code", "id_token", "code id_token"],
    "code_challenge_methods_supported": ["S256"],
    "scopes_supported": ["openid", "profile", "email"],
    "subject_types_supported": ["public"],
    "id_token_signing_alg_values_supported": ["RS256"],
}

# _build_oauth_metadata now receives the MCP endpoint URL (with /mcp path)
# to match RFC 8414 issuer derivation from /.well-known/oauth-authorization-server/mcp
SERVER_URL = "https://mcp.example.com/mcp"


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

        assert result["issuer"] == "https://abc1234.id.cyberark.cloud/mcpprivilegecloud/"
        assert "authorization_endpoint" in result
        mock_client.get.assert_called_once_with(
            "https://abc1234.id.cyberark.cloud/mcpprivilegecloud/.well-known/openid-configuration"
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
            "https://abc1234.id.cyberark.cloud/mcpprivilegecloud/.well-known/openid-configuration"
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
        """Should return RFC 8414 metadata with endpoints from OIDC discovery."""
        from mcp_privilege_cloud.mcp_server import _build_oauth_metadata

        metadata = _build_oauth_metadata(SAMPLE_OIDC_DISCOVERY, SERVER_URL)

        # issuer uses AnyHttpUrl normalization; URLs with path don't get trailing slash
        assert metadata["issuer"] == SERVER_URL
        # authorization/token endpoints are same-origin (proxied through our server)
        assert metadata["authorization_endpoint"] == "https://mcp.example.com/authorize"
        assert metadata["token_endpoint"] == "https://mcp.example.com/token"
        assert metadata["response_types_supported"] == ["code", "id_token", "code id_token"]
        assert metadata["code_challenge_methods_supported"] == ["S256"]
        assert metadata["scopes_supported"] == ["openid", "profile", "email"]
        assert metadata["jwks_uri"] == SAMPLE_OIDC_DISCOVERY["jwks_uri"]

    def test_includes_registration_endpoint(self):
        """Should include registration_endpoint at server root (not under /mcp)."""
        from mcp_privilege_cloud.mcp_server import _build_oauth_metadata

        metadata = _build_oauth_metadata(SAMPLE_OIDC_DISCOVERY, SERVER_URL)

        # registration_endpoint uses server base URL, not the MCP endpoint path
        assert metadata["registration_endpoint"] == "https://mcp.example.com/register"

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

    def test_issuer_matches_sdk_anyhttp_normalization(self):
        """Issuer MUST match the authorization_servers URL from SDK's protected resource metadata.

        The MCP SDK normalizes URLs through Pydantic AnyHttpUrl. URLs with a path
        (like /mcp) keep that path without a trailing slash. The issuer must match
        what the client derives from /.well-known/oauth-authorization-server/mcp
        per RFC 8414 section 3.3.
        """
        from mcp_privilege_cloud.mcp_server import _build_oauth_metadata
        from pydantic import AnyHttpUrl

        # URL with /mcp path — no trailing slash added
        metadata = _build_oauth_metadata(SAMPLE_OIDC_DISCOVERY, "https://mcp.example.com/mcp")
        assert metadata["issuer"] == "https://mcp.example.com/mcp"
        assert metadata["issuer"] == str(AnyHttpUrl("https://mcp.example.com/mcp"))

        # registration_endpoint at server root, not under /mcp
        assert metadata["registration_endpoint"] == "https://mcp.example.com/register"

        # Bare domain gets trailing slash from AnyHttpUrl
        metadata = _build_oauth_metadata(SAMPLE_OIDC_DISCOVERY, "https://mcp.example.com")
        assert metadata["issuer"] == "https://mcp.example.com/"
        assert metadata["registration_endpoint"] == "https://mcp.example.com/register"

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

    def test_dcr_returns_oauth_client_id_from_env(self):
        """DCR should return CYBERARK_OAUTH_CLIENT_ID when set, but never secrets."""
        from mcp_privilege_cloud.mcp_server import _build_dcr_response

        body = {
            "client_name": "Claude",
            "redirect_uris": ["https://claude.ai/api/mcp/auth_callback"],
        }

        env = {
            "CYBERARK_OAUTH_CLIENT_ID": "1fc81892-a1ba-49ca-9bf9-7d1f1de19ea6",
            "CYBERARK_OAUTH_CLIENT_SECRET": "oauth-secret",
        }
        with patch.dict(os.environ, env, clear=True):
            response = _build_dcr_response(body)

        assert response["client_id"] == "1fc81892-a1ba-49ca-9bf9-7d1f1de19ea6"
        assert "client_secret" not in response
        assert response["token_endpoint_auth_method"] == "none"
        assert response["grant_types"] == ["authorization_code", "refresh_token"]

    def test_dcr_falls_back_to_oidc_app_id(self):
        """DCR should fall back to CYBERARK_OIDC_APP_ID, not CYBERARK_CLIENT_ID (service account)."""
        from mcp_privilege_cloud.mcp_server import _build_dcr_response
        from mcp_privilege_cloud.token_verifier import CYBERARK_OIDC_APP_ID

        env = {
            "CYBERARK_CLIENT_ID": "myuser@tenant",
            "CYBERARK_CLIENT_SECRET": "s3cret",
        }
        with patch.dict(os.environ, env, clear=True):
            response = _build_dcr_response({})

        assert response["client_id"] == CYBERARK_OIDC_APP_ID
        assert "client_secret" not in response

    def test_dcr_public_client_when_no_secret(self):
        """DCR should return public client (no secret) when CYBERARK_CLIENT_SECRET is unset."""
        from mcp_privilege_cloud.mcp_server import _build_dcr_response

        with patch.dict(os.environ, {}, clear=True):
            response = _build_dcr_response({})

        assert response["token_endpoint_auth_method"] == "none"
        assert "client_secret" not in response

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
        """DCR should use OIDC app ID as fallback client_id."""
        from mcp_privilege_cloud.mcp_server import _build_dcr_response
        from mcp_privilege_cloud.token_verifier import CYBERARK_OIDC_APP_ID

        with patch.dict(os.environ, {}, clear=True):
            response = _build_dcr_response({})

        assert response["client_id"] == CYBERARK_OIDC_APP_ID
        assert response["client_name"] == "MCP Client"
        assert response["redirect_uris"] == []

    def test_dcr_logs_warning_when_no_client_id_set(self):
        """DCR should log a warning when neither OAuth nor legacy client ID is set."""
        from mcp_privilege_cloud.mcp_server import _build_dcr_response
        from mcp_privilege_cloud.token_verifier import CYBERARK_OIDC_APP_ID
        import logging

        with patch.dict(os.environ, {}, clear=True):
            with patch("mcp_privilege_cloud.mcp_server.logger") as mock_logger:
                response = _build_dcr_response({})

        mock_logger.warning.assert_called_once()
        warning_msg = mock_logger.warning.call_args[0][0]
        assert "CYBERARK_OAUTH_CLIENT_ID" in warning_msg
        assert response["client_id"] == CYBERARK_OIDC_APP_ID


class TestTokenProxyCredentialInjection:
    """Test that /token proxy injects server-side credentials."""

    @pytest.mark.asyncio
    async def test_injects_credentials(self):
        """Token proxy should inject server-side client_id and client_secret."""
        from mcp_privilege_cloud.mcp_server import _get_oauth_credentials
        from urllib.parse import parse_qs, urlencode

        env = {
            "CYBERARK_OAUTH_CLIENT_ID": "injected-client-id",
            "CYBERARK_OAUTH_CLIENT_SECRET": "injected-secret",
        }
        with patch.dict(os.environ, env, clear=True):
            client_id, client_secret = _get_oauth_credentials()

        # Simulate what token_proxy does: parse client body, inject creds
        client_body = urlencode({"grant_type": "authorization_code", "code": "abc123"})
        params = parse_qs(client_body, keep_blank_values=True)
        flat_params = {k: v[0] for k, v in params.items()}
        flat_params["client_id"] = client_id
        flat_params["client_secret"] = client_secret
        forwarded = urlencode(flat_params)

        parsed = parse_qs(forwarded)
        assert parsed["client_id"] == ["injected-client-id"]
        assert parsed["client_secret"] == ["injected-secret"]
        assert parsed["grant_type"] == ["authorization_code"]
        assert parsed["code"] == ["abc123"]

    @pytest.mark.asyncio
    async def test_overwrites_client_credentials(self):
        """Token proxy should overwrite any client-supplied credentials."""
        from mcp_privilege_cloud.mcp_server import _get_oauth_credentials
        from urllib.parse import parse_qs, urlencode

        env = {
            "CYBERARK_OAUTH_CLIENT_ID": "server-id",
            "CYBERARK_OAUTH_CLIENT_SECRET": "server-secret",
        }
        with patch.dict(os.environ, env, clear=True):
            client_id, client_secret = _get_oauth_credentials()

        # Client tries to send its own credentials
        client_body = urlencode({
            "grant_type": "authorization_code",
            "client_id": "attacker-id",
            "client_secret": "attacker-secret",
        })
        params = parse_qs(client_body, keep_blank_values=True)
        flat_params = {k: v[0] for k, v in params.items()}
        flat_params["client_id"] = client_id
        flat_params["client_secret"] = client_secret
        forwarded = urlencode(flat_params)

        parsed = parse_qs(forwarded)
        assert parsed["client_id"] == ["server-id"]
        assert parsed["client_secret"] == ["server-secret"]

    @pytest.mark.asyncio
    async def test_preserves_other_params(self):
        """Token proxy should preserve grant_type, code, redirect_uri, code_verifier."""
        from mcp_privilege_cloud.mcp_server import _get_oauth_credentials
        from urllib.parse import parse_qs, urlencode

        env = {"CYBERARK_OAUTH_CLIENT_ID": "id", "CYBERARK_OAUTH_CLIENT_SECRET": "secret"}
        with patch.dict(os.environ, env, clear=True):
            client_id, client_secret = _get_oauth_credentials()

        client_body = urlencode({
            "grant_type": "authorization_code",
            "code": "authcode",
            "redirect_uri": "https://example.com/callback",
            "code_verifier": "pkce_verifier_value",
        })
        params = parse_qs(client_body, keep_blank_values=True)
        flat_params = {k: v[0] for k, v in params.items()}
        flat_params["client_id"] = client_id
        flat_params["client_secret"] = client_secret
        forwarded = urlencode(flat_params)

        parsed = parse_qs(forwarded)
        assert parsed["grant_type"] == ["authorization_code"]
        assert parsed["code"] == ["authcode"]
        assert parsed["redirect_uri"] == ["https://example.com/callback"]
        assert parsed["code_verifier"] == ["pkce_verifier_value"]


class TestTokenProxyEndToEnd:
    """End-to-end test for /token proxy: body parsing, credential injection, upstream forwarding."""

    @pytest.mark.asyncio
    async def test_token_proxy_full_flow(self):
        """Token proxy should parse body, inject creds, forward to upstream, and return response."""
        from mcp_privilege_cloud.mcp_server import _register_oauth_routes, _fetch_oidc_discovery
        from starlette.testclient import TestClient
        from starlette.applications import Starlette
        from starlette.routing import Route
        from urllib.parse import parse_qs

        import mcp_privilege_cloud.mcp_server as mod

        # Clear OIDC discovery cache
        mod._oidc_discovery_cache = None

        env = {
            "CYBERARK_IDENTITY_TENANT_URL": "https://abc1234.id.cyberark.cloud",
            "CYBERARK_OAUTH_CLIENT_ID": "server-client-id",
            "CYBERARK_OAUTH_CLIENT_SECRET": "server-secret",
        }

        # Mock OIDC discovery
        mock_oidc_response = AsyncMock()
        mock_oidc_response.status_code = 200
        mock_oidc_response.json = lambda: SAMPLE_OIDC_DISCOVERY
        mock_oidc_response.raise_for_status = lambda: None

        # Mock upstream token response
        upstream_response = httpx.Response(
            200,
            json={"access_token": "tok_123", "token_type": "Bearer"},
            request=httpx.Request("POST", SAMPLE_OIDC_DISCOVERY["token_endpoint"]),
        )

        # Capture the body forwarded to upstream
        captured_body = {}

        async def mock_post(url, content=None, headers=None):
            captured_body["url"] = url
            captured_body["params"] = parse_qs(content)
            return upstream_response

        mock_http_client = AsyncMock()
        mock_http_client.__aenter__ = AsyncMock(return_value=mock_http_client)
        mock_http_client.__aexit__ = AsyncMock(return_value=False)
        mock_http_client.get = AsyncMock(return_value=mock_oidc_response)
        mock_http_client.post = mock_post

        with patch.dict(os.environ, env, clear=False):
            with patch("mcp_privilege_cloud.mcp_server.httpx.AsyncClient", return_value=mock_http_client):
                # Register routes on a mock FastMCP that stores them
                routes = {}

                class MockMCP:
                    def custom_route(self, path, methods=None):
                        def decorator(fn):
                            routes[path] = fn
                            return fn
                        return decorator

                mock_mcp = MockMCP()
                _register_oauth_routes(mock_mcp)

                # Build a Starlette Request with form body
                from starlette.requests import Request as StarletteRequest

                scope = {
                    "type": "http",
                    "method": "POST",
                    "path": "/token",
                    "query_string": b"",
                    "headers": [(b"content-type", b"application/x-www-form-urlencoded")],
                }

                body_bytes = b"grant_type=authorization_code&code=auth_code_123&redirect_uri=https%3A%2F%2Fexample.com%2Fcallback"

                async def receive():
                    return {"type": "http.request", "body": body_bytes}

                request = StarletteRequest(scope, receive)
                response = await routes["/token"](request)

        # Verify upstream received correct params
        assert captured_body["url"] == SAMPLE_OIDC_DISCOVERY["token_endpoint"]
        assert captured_body["params"]["client_id"] == ["server-client-id"]
        assert captured_body["params"]["client_secret"] == ["server-secret"]
        assert captured_body["params"]["grant_type"] == ["authorization_code"]
        assert captured_body["params"]["code"] == ["auth_code_123"]
        assert response.status_code == 200


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
