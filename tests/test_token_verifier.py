"""Tests for CyberArkTokenVerifier.

Tests JWT verification against CyberArk Identity JWKS endpoint,
implementing the MCP SDK's TokenVerifier protocol.
"""

import base64
import json
import os
import time

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


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
        "scope": "openid profile pvwa",
    }
    claims.update(overrides)
    return claims


class TestCyberArkTokenVerifierInit:
    """Test CyberArkTokenVerifier initialization."""

    def test_oidc_app_id_constant(self):
        """CYBERARK_OIDC_APP_ID should default to the custom app."""
        from mcp_privilege_cloud.token_verifier import CYBERARK_OIDC_APP_ID

        assert CYBERARK_OIDC_APP_ID == "mcpprivilegecloud"

    def test_init_with_tenant_url(self):
        """Verifier should initialize with a CyberArk Identity tenant URL."""
        from mcp_privilege_cloud.token_verifier import CyberArkTokenVerifier

        verifier = CyberArkTokenVerifier(
            identity_tenant_url="https://abc1234.id.cyberark.cloud",
        )

        assert verifier._identity_tenant_url == "https://abc1234.id.cyberark.cloud"

    def test_init_strips_trailing_slash(self):
        """Tenant URL should have trailing slash stripped."""
        from mcp_privilege_cloud.token_verifier import CyberArkTokenVerifier

        verifier = CyberArkTokenVerifier(
            identity_tenant_url="https://abc1234.id.cyberark.cloud/",
        )

        assert verifier._identity_tenant_url == "https://abc1234.id.cyberark.cloud"

    def test_jwks_uri_none_before_resolution(self):
        """JWKS URI should be None before lazy resolution."""
        from mcp_privilege_cloud.token_verifier import CyberArkTokenVerifier

        verifier = CyberArkTokenVerifier(
            identity_tenant_url="https://abc1234.id.cyberark.cloud",
        )

        assert verifier._jwks_uri is None


class TestCyberArkTokenVerifierVerify:
    """Test CyberArkTokenVerifier.verify_token() method."""

    @pytest.mark.asyncio
    async def test_valid_token_returns_access_token(self):
        """A valid JWT should return an AccessToken with correct fields."""
        from mcp_privilege_cloud.token_verifier import CyberArkTokenVerifier

        claims = _default_claims()
        jwt_token = _make_jwt(claims)

        verifier = CyberArkTokenVerifier(
            identity_tenant_url="https://abc1234.id.cyberark.cloud",
        )

        # Mock the JWT decode to return our claims (skip actual signature verification)
        with patch.object(verifier, "_decode_and_verify", return_value=claims):
            result = await verifier.verify_token(jwt_token)

        assert result is not None
        assert result.token == jwt_token
        assert result.client_id == claims["sub"]
        assert result.expires_at == claims["exp"]

    @pytest.mark.asyncio
    async def test_valid_token_extracts_scopes(self):
        """Scopes should be extracted from the JWT scope claim."""
        from mcp_privilege_cloud.token_verifier import CyberArkTokenVerifier

        claims = _default_claims(scope="openid profile pvwa")
        jwt_token = _make_jwt(claims)

        verifier = CyberArkTokenVerifier(
            identity_tenant_url="https://abc1234.id.cyberark.cloud",
        )

        with patch.object(verifier, "_decode_and_verify", return_value=claims):
            result = await verifier.verify_token(jwt_token)

        assert result is not None
        assert result.scopes == ["openid", "profile", "pvwa"]

    @pytest.mark.asyncio
    async def test_expired_token_returns_none(self):
        """An expired JWT should return None."""
        from mcp_privilege_cloud.token_verifier import CyberArkTokenVerifier

        claims = _default_claims(exp=int(time.time()) - 100)
        jwt_token = _make_jwt(claims)

        verifier = CyberArkTokenVerifier(
            identity_tenant_url="https://abc1234.id.cyberark.cloud",
        )

        # Simulate PyJWT raising ExpiredSignatureError
        import jwt as pyjwt

        with patch.object(
            verifier,
            "_decode_and_verify",
            side_effect=pyjwt.ExpiredSignatureError("token expired"),
        ):
            result = await verifier.verify_token(jwt_token)

        assert result is None

    @pytest.mark.asyncio
    async def test_invalid_signature_returns_none(self):
        """A JWT with invalid signature should return None."""
        from mcp_privilege_cloud.token_verifier import CyberArkTokenVerifier

        jwt_token = _make_jwt(_default_claims())

        verifier = CyberArkTokenVerifier(
            identity_tenant_url="https://abc1234.id.cyberark.cloud",
        )

        import jwt as pyjwt

        with patch.object(
            verifier,
            "_decode_and_verify",
            side_effect=pyjwt.InvalidSignatureError("bad signature"),
        ):
            result = await verifier.verify_token(jwt_token)

        assert result is None

    @pytest.mark.asyncio
    async def test_invalid_audience_returns_none(self):
        """A JWT with wrong audience should return None."""
        from mcp_privilege_cloud.token_verifier import CyberArkTokenVerifier

        claims = _default_claims(aud="wrong-app-id")
        jwt_token = _make_jwt(claims)

        verifier = CyberArkTokenVerifier(
            identity_tenant_url="https://abc1234.id.cyberark.cloud",
        )

        import jwt as pyjwt

        with patch.object(
            verifier,
            "_decode_and_verify",
            side_effect=pyjwt.InvalidAudienceError("invalid audience"),
        ):
            result = await verifier.verify_token(jwt_token)

        assert result is None

    @pytest.mark.asyncio
    async def test_malformed_token_returns_none(self):
        """A malformed JWT string should return None."""
        from mcp_privilege_cloud.token_verifier import CyberArkTokenVerifier

        verifier = CyberArkTokenVerifier(
            identity_tenant_url="https://abc1234.id.cyberark.cloud",
        )

        import jwt as pyjwt

        with patch.object(
            verifier,
            "_decode_and_verify",
            side_effect=pyjwt.DecodeError("invalid token"),
        ):
            result = await verifier.verify_token("not-a-jwt")

        assert result is None

    @pytest.mark.asyncio
    async def test_missing_sub_claim_returns_none(self):
        """A JWT missing the sub claim should return None."""
        from mcp_privilege_cloud.token_verifier import CyberArkTokenVerifier

        claims = _default_claims()
        del claims["sub"]
        jwt_token = _make_jwt(claims)

        verifier = CyberArkTokenVerifier(
            identity_tenant_url="https://abc1234.id.cyberark.cloud",
        )

        with patch.object(verifier, "_decode_and_verify", return_value=claims):
            result = await verifier.verify_token(jwt_token)

        assert result is None

    @pytest.mark.asyncio
    async def test_empty_scope_returns_empty_list(self):
        """A JWT with no scope claim should return empty scopes list."""
        from mcp_privilege_cloud.token_verifier import CyberArkTokenVerifier

        claims = _default_claims()
        del claims["scope"]
        jwt_token = _make_jwt(claims)

        verifier = CyberArkTokenVerifier(
            identity_tenant_url="https://abc1234.id.cyberark.cloud",
        )

        with patch.object(verifier, "_decode_and_verify", return_value=claims):
            result = await verifier.verify_token(jwt_token)

        assert result is not None
        assert result.scopes == []


class TestCyberArkTokenVerifierJWKS:
    """Test JWKS fetching and caching."""

    def test_jwks_client_not_created_at_init(self):
        """JWKS client should NOT be created at init (lazy resolution)."""
        from mcp_privilege_cloud.token_verifier import CyberArkTokenVerifier

        verifier = CyberArkTokenVerifier(
            identity_tenant_url="https://abc1234.id.cyberark.cloud",
        )

        assert verifier._jwks_client is None

    @pytest.mark.asyncio
    async def test_jwks_uri_resolved_from_oidc_discovery(self):
        """JWKS URI should be resolved from OIDC discovery on first use."""
        from mcp_privilege_cloud.token_verifier import CyberArkTokenVerifier

        verifier = CyberArkTokenVerifier(
            identity_tenant_url="https://abc1234.id.cyberark.cloud",
        )

        oidc_response = {
            "jwks_uri": "https://abc1234.id.cyberark.cloud/OAuth2/Keys/real-app-key-id",
            "issuer": "https://abc1234.id.cyberark.cloud/mcpprivilegecloud/",
        }

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = oidc_response
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_resp
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            await verifier._ensure_jwks_client()

        assert verifier._jwks_uri == "https://abc1234.id.cyberark.cloud/OAuth2/Keys/real-app-key-id"
        assert verifier._jwks_client is not None

    @pytest.mark.asyncio
    async def test_jwks_uri_falls_back_on_discovery_failure(self):
        """Should fall back to constructed JWKS URI if OIDC discovery fails."""
        from mcp_privilege_cloud.token_verifier import CyberArkTokenVerifier, CYBERARK_OIDC_APP_ID

        verifier = CyberArkTokenVerifier(
            identity_tenant_url="https://abc1234.id.cyberark.cloud",
        )

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get.side_effect = Exception("connection refused")
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            await verifier._ensure_jwks_client()

        expected_fallback = f"https://abc1234.id.cyberark.cloud/OAuth2/Keys/{CYBERARK_OIDC_APP_ID}"
        assert verifier._jwks_uri == expected_fallback
        assert verifier._jwks_client is not None

    @pytest.mark.asyncio
    async def test_jwks_client_cached_after_first_resolution(self):
        """JWKS client should be reused after first resolution."""
        from mcp_privilege_cloud.token_verifier import CyberArkTokenVerifier

        verifier = CyberArkTokenVerifier(
            identity_tenant_url="https://abc1234.id.cyberark.cloud",
        )

        oidc_response = {
            "jwks_uri": "https://abc1234.id.cyberark.cloud/OAuth2/Keys/real-key",
            "issuer": "https://abc1234.id.cyberark.cloud/mcpprivilegecloud/",
        }

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = oidc_response
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_resp
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            await verifier._ensure_jwks_client()
            first_client = verifier._jwks_client

            # Second call should not re-fetch
            await verifier._ensure_jwks_client()
            assert verifier._jwks_client is first_client

    @pytest.mark.asyncio
    async def test_jwks_fetch_failure_returns_none(self):
        """If JWKS fetch fails, verify_token should return None."""
        from mcp_privilege_cloud.token_verifier import CyberArkTokenVerifier

        jwt_token = _make_jwt(_default_claims())

        verifier = CyberArkTokenVerifier(
            identity_tenant_url="https://abc1234.id.cyberark.cloud",
        )

        import jwt as pyjwt

        with patch.object(
            verifier,
            "_decode_and_verify",
            side_effect=pyjwt.PyJWKClientConnectionError("connection failed"),
        ):
            result = await verifier.verify_token(jwt_token)

        assert result is None

    @pytest.mark.asyncio
    async def test_decode_and_verify_calls_pyjwt(self):
        """_decode_and_verify should use PyJWKClient and jwt.decode."""
        from mcp_privilege_cloud.token_verifier import CyberArkTokenVerifier

        claims = _default_claims()
        jwt_token = _make_jwt(claims)

        verifier = CyberArkTokenVerifier(
            identity_tenant_url="https://abc1234.id.cyberark.cloud",
        )

        mock_key = MagicMock()
        mock_key.key = "mock-public-key"

        # Pre-set a mock JWKS client so _ensure_jwks_client is a no-op
        mock_jwks_client = MagicMock()
        mock_jwks_client.get_signing_key_from_jwt.return_value = mock_key
        verifier._jwks_client = mock_jwks_client

        with patch("jwt.decode", return_value=claims) as mock_decode:
            result = await verifier._decode_and_verify(jwt_token)

            mock_decode.assert_called_once_with(
                jwt_token,
                mock_key.key,
                algorithms=["RS256"],
                audience=verifier._expected_audience,
                issuer=f"{verifier._identity_tenant_url}/{verifier._expected_app_id}/",
                options={"require": ["exp", "iss", "sub", "aud"]},
            )
            assert result == claims


class TestCyberArkTokenVerifierAudience:
    """Test audience resolution: CYBERARK_OAUTH_AUDIENCE > CYBERARK_OAUTH_CLIENT_ID > CYBERARK_CLIENT_ID > app ID."""

    @pytest.mark.asyncio
    async def test_audience_prefers_oauth_audience(self):
        """CYBERARK_OAUTH_AUDIENCE should take highest priority (explicit audience override)."""
        from mcp_privilege_cloud.token_verifier import CyberArkTokenVerifier

        oauth_audience = "1fc81892-a1ba-49ca-9bf9-7d1f1de19ea6"
        claims = _default_claims(aud=oauth_audience)
        jwt_token = _make_jwt(claims)

        env = {
            "CYBERARK_OAUTH_AUDIENCE": oauth_audience,
            "CYBERARK_OAUTH_CLIENT_ID": "c21840a7-different-trust-tab-id",
            "CYBERARK_CLIENT_ID": "timtest@cyberark.cloud.3240",
        }
        with patch.dict(os.environ, env):
            verifier = CyberArkTokenVerifier(
                identity_tenant_url="https://abc1234.id.cyberark.cloud",
            )

        assert verifier._expected_audience == oauth_audience

        mock_key = MagicMock()
        mock_key.key = "mock-public-key"
        mock_jwks_client = MagicMock()
        mock_jwks_client.get_signing_key_from_jwt.return_value = mock_key
        verifier._jwks_client = mock_jwks_client

        with patch("jwt.decode", return_value=claims) as mock_decode:
            await verifier._decode_and_verify(jwt_token)

            mock_decode.assert_called_once_with(
                jwt_token,
                mock_key.key,
                algorithms=["RS256"],
                audience=oauth_audience,
                issuer=f"{verifier._identity_tenant_url}/{verifier._expected_app_id}/",
                options={"require": ["exp", "iss", "sub", "aud"]},
            )

    @pytest.mark.asyncio
    async def test_audience_falls_back_to_oauth_client_id(self):
        """Without CYBERARK_OAUTH_AUDIENCE, CYBERARK_OAUTH_CLIENT_ID should be used."""
        from mcp_privilege_cloud.token_verifier import CyberArkTokenVerifier

        oauth_client_id = "c21840a7-trust-tab-client-id"

        env = {
            "CYBERARK_OAUTH_CLIENT_ID": oauth_client_id,
            "CYBERARK_CLIENT_ID": "timtest@cyberark.cloud.3240",
        }
        with patch.dict(os.environ, env):
            os.environ.pop("CYBERARK_OAUTH_AUDIENCE", None)
            verifier = CyberArkTokenVerifier(
                identity_tenant_url="https://abc1234.id.cyberark.cloud",
            )

        assert verifier._expected_audience == oauth_client_id

    @pytest.mark.asyncio
    async def test_audience_falls_back_to_client_id(self):
        """Without CYBERARK_OAUTH_CLIENT_ID or CYBERARK_OAUTH_AUDIENCE, should use CYBERARK_CLIENT_ID."""
        from mcp_privilege_cloud.token_verifier import CyberArkTokenVerifier

        client_id = "some-client-id"

        env = {"CYBERARK_CLIENT_ID": client_id}
        with patch.dict(os.environ, env):
            os.environ.pop("CYBERARK_OAUTH_CLIENT_ID", None)
            os.environ.pop("CYBERARK_OAUTH_AUDIENCE", None)
            verifier = CyberArkTokenVerifier(
                identity_tenant_url="https://abc1234.id.cyberark.cloud",
            )

        assert verifier._expected_audience == client_id

    @pytest.mark.asyncio
    async def test_audience_falls_back_to_oidc_app_id(self):
        """Without any env vars, should use CYBERARK_OIDC_APP_ID as audience."""
        from mcp_privilege_cloud.token_verifier import CyberArkTokenVerifier, CYBERARK_OIDC_APP_ID

        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("CYBERARK_OAUTH_CLIENT_ID", None)
            os.environ.pop("CYBERARK_OAUTH_AUDIENCE", None)
            os.environ.pop("CYBERARK_CLIENT_ID", None)
            verifier = CyberArkTokenVerifier(
                identity_tenant_url="https://abc1234.id.cyberark.cloud",
            )

        assert verifier._expected_audience == CYBERARK_OIDC_APP_ID


class TestCyberArkTokenVerifierProtocol:
    """Test that CyberArkTokenVerifier satisfies the MCP TokenVerifier protocol."""

    def test_has_verify_token_method(self):
        """Verifier must have an async verify_token method."""
        from mcp_privilege_cloud.token_verifier import CyberArkTokenVerifier

        verifier = CyberArkTokenVerifier(
            identity_tenant_url="https://abc1234.id.cyberark.cloud",
        )

        assert hasattr(verifier, "verify_token")
        assert callable(verifier.verify_token)

    def test_returns_access_token_type(self):
        """verify_token return type should be compatible with MCP AccessToken."""
        from mcp.server.auth.provider import AccessToken

        # Just verify AccessToken can be imported and has expected fields
        token = AccessToken(
            token="test",
            client_id="client",
            scopes=["read"],
            expires_at=None,
        )
        assert token.token == "test"
        assert token.client_id == "client"
        assert token.scopes == ["read"]
