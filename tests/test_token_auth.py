"""Tests for token-based authentication bridge.

Tests ArkISPAuthFromToken which accepts pre-existing JWT tokens from external
OAuth flows (CyberArk Identity Authorization Code flow) and bridges them into
ark-sdk-python's ArkISPAuth interface.
"""

import base64
import json
import time

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock


def _make_jwt(claims: dict, header: dict | None = None) -> str:
    """Create a minimal JWT string (unsigned) for testing."""
    if header is None:
        header = {"alg": "RS256", "typ": "JWT"}
    h = base64.urlsafe_b64encode(json.dumps(header).encode()).rstrip(b"=").decode()
    p = base64.urlsafe_b64encode(json.dumps(claims).encode()).rstrip(b"=").decode()
    s = base64.urlsafe_b64encode(b"fakesig").rstrip(b"=").decode()
    return f"{h}.{p}.{s}"


def _default_claims(**overrides: object) -> dict:
    """Return default valid JWT claims with optional overrides."""
    claims = {
        "sub": "testuser@cyberark.cloud.12345",
        "iss": "https://abc1234.id.cyberark.cloud/",
        "aud": "test-app-id",
        "exp": int(time.time()) + 3600,
        "iat": int(time.time()),
        "unique_name": "testuser@abc1234.cyberark.cloud",
        "subdomain": "abc1234",
        "platform_domain": "cyberark.cloud",
    }
    claims.update(overrides)
    return claims


class TestArkISPAuthFromToken:
    """Test creating ArkISPAuth from pre-existing JWT tokens."""

    def test_create_from_valid_jwt(self):
        """ArkISPAuthFromToken should construct successfully from a valid JWT."""
        from mcp_privilege_cloud.token_auth import ArkISPAuthFromToken

        claims = _default_claims()
        jwt_token = _make_jwt(claims)

        auth = ArkISPAuthFromToken(
            jwt_token=jwt_token,
            username=claims["unique_name"],
        )

        assert auth.token is not None
        assert auth.token.token.get_secret_value() == jwt_token

    def test_token_username_set(self):
        """Token should have the correct username set."""
        from mcp_privilege_cloud.token_auth import ArkISPAuthFromToken

        claims = _default_claims()
        jwt_token = _make_jwt(claims)

        auth = ArkISPAuthFromToken(
            jwt_token=jwt_token,
            username="testuser@abc1234.cyberark.cloud",
        )

        assert auth.token.username == "testuser@abc1234.cyberark.cloud"

    def test_token_expiry_set(self):
        """Token expiry should be derived from JWT exp claim."""
        from mcp_privilege_cloud.token_auth import ArkISPAuthFromToken

        exp_time = int(time.time()) + 7200
        claims = _default_claims(exp=exp_time)
        jwt_token = _make_jwt(claims)

        auth = ArkISPAuthFromToken(
            jwt_token=jwt_token,
            username=claims["unique_name"],
        )

        assert auth.token.expires_in is not None
        # Expiry should be within a reasonable window of exp claim
        expected = datetime.fromtimestamp(exp_time)
        actual = auth.token.expires_in
        assert abs((expected - actual).total_seconds()) < 5

    def test_token_metadata_env(self):
        """Token metadata should contain env for PCloud service initialization."""
        from mcp_privilege_cloud.token_auth import ArkISPAuthFromToken

        claims = _default_claims()
        jwt_token = _make_jwt(claims)

        auth = ArkISPAuthFromToken(
            jwt_token=jwt_token,
            username=claims["unique_name"],
        )

        assert "env" in auth.token.metadata

    def test_active_auth_profile_set(self):
        """_active_auth_profile must be set for service compatibility."""
        from mcp_privilege_cloud.token_auth import ArkISPAuthFromToken

        claims = _default_claims()
        jwt_token = _make_jwt(claims)

        auth = ArkISPAuthFromToken(
            jwt_token=jwt_token,
            username=claims["unique_name"],
        )

        assert auth._active_auth_profile is not None
        assert auth._active_auth_profile.username == claims["unique_name"]

    def test_expired_token_raises(self):
        """Creating auth from an expired JWT should raise ValueError."""
        from mcp_privilege_cloud.token_auth import ArkISPAuthFromToken

        claims = _default_claims(exp=int(time.time()) - 100)
        jwt_token = _make_jwt(claims)

        with pytest.raises(ValueError, match="expired"):
            ArkISPAuthFromToken(
                jwt_token=jwt_token,
                username=claims["unique_name"],
            )

    def test_missing_sub_claim_raises(self):
        """JWT without sub claim should raise ValueError."""
        from mcp_privilege_cloud.token_auth import ArkISPAuthFromToken

        claims = _default_claims()
        del claims["sub"]
        jwt_token = _make_jwt(claims)

        with pytest.raises(ValueError, match="sub"):
            ArkISPAuthFromToken(
                jwt_token=jwt_token,
                username=claims["unique_name"],
            )

    def test_malformed_jwt_raises(self):
        """Malformed JWT string should raise ValueError."""
        from mcp_privilege_cloud.token_auth import ArkISPAuthFromToken

        with pytest.raises(ValueError, match="decode|Invalid"):
            ArkISPAuthFromToken(
                jwt_token="not-a-jwt",
                username="testuser",
            )

    def test_refresh_token_stored(self):
        """Refresh token should be stored in ArkToken when provided."""
        from mcp_privilege_cloud.token_auth import ArkISPAuthFromToken

        claims = _default_claims()
        jwt_token = _make_jwt(claims)

        auth = ArkISPAuthFromToken(
            jwt_token=jwt_token,
            username=claims["unique_name"],
            refresh_token="mock-refresh-token",
        )

        assert auth.token.refresh_token == "mock-refresh-token"

    def test_no_refresh_token_is_none(self):
        """When no refresh token provided, ArkToken.refresh_token should be None."""
        from mcp_privilege_cloud.token_auth import ArkISPAuthFromToken

        claims = _default_claims()
        jwt_token = _make_jwt(claims)

        auth = ArkISPAuthFromToken(
            jwt_token=jwt_token,
            username=claims["unique_name"],
        )

        assert auth.token.refresh_token is None

    def test_cache_authentication_disabled(self):
        """Token auth should not use keyring caching."""
        from mcp_privilege_cloud.token_auth import ArkISPAuthFromToken

        claims = _default_claims()
        jwt_token = _make_jwt(claims)

        auth = ArkISPAuthFromToken(
            jwt_token=jwt_token,
            username=claims["unique_name"],
        )

        assert auth._cache_authentication is False


class TestCyberArkMCPServerFromToken:
    """Test CyberArkMCPServer.from_token factory method."""

    def test_from_token_creates_instance(self):
        """from_token should create a CyberArkMCPServer instance."""
        from mcp_privilege_cloud.server import CyberArkMCPServer

        claims = _default_claims()
        jwt_token = _make_jwt(claims)

        with patch("mcp_privilege_cloud.server.ArkPCloudAccountsService"):
            with patch("mcp_privilege_cloud.server.ArkPCloudSafesService"):
                with patch("mcp_privilege_cloud.server.ArkPCloudPlatformsService"):
                    with patch("mcp_privilege_cloud.server.ArkPCloudApplicationsService"):
                        with patch("mcp_privilege_cloud.server.ArkSMService"):
                            server = CyberArkMCPServer.from_token(
                                jwt_token=jwt_token,
                                username=claims["unique_name"],
                            )

        assert server is not None
        assert hasattr(server, "accounts_service")
        assert hasattr(server, "safes_service")
        assert hasattr(server, "platforms_service")
        assert hasattr(server, "applications_service")
        assert hasattr(server, "sm_service")
        assert hasattr(server, "logger")
        assert hasattr(server, "_executor")

    def test_from_token_with_refresh_token(self):
        """from_token should pass refresh_token through to token auth."""
        from mcp_privilege_cloud.server import CyberArkMCPServer

        claims = _default_claims()
        jwt_token = _make_jwt(claims)

        with patch("mcp_privilege_cloud.server.ArkPCloudAccountsService"):
            with patch("mcp_privilege_cloud.server.ArkPCloudSafesService"):
                with patch("mcp_privilege_cloud.server.ArkPCloudPlatformsService"):
                    with patch("mcp_privilege_cloud.server.ArkPCloudApplicationsService"):
                        with patch("mcp_privilege_cloud.server.ArkSMService"):
                            server = CyberArkMCPServer.from_token(
                                jwt_token=jwt_token,
                                username=claims["unique_name"],
                                refresh_token="test-refresh",
                            )

        assert server is not None

    def test_from_token_expired_raises(self):
        """from_token with expired JWT should raise ValueError."""
        from mcp_privilege_cloud.server import CyberArkMCPServer

        claims = _default_claims(exp=int(time.time()) - 100)
        jwt_token = _make_jwt(claims)

        with pytest.raises(ValueError, match="expired"):
            CyberArkMCPServer.from_token(
                jwt_token=jwt_token,
                username=claims["unique_name"],
            )
