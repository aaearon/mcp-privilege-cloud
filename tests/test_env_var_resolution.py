"""Tests for environment variable resolution priority chains.

Tests the DCR client_id/secret priority chain to ensure
CYBERARK_OAUTH_CLIENT_ID takes priority over legacy vars.
"""

import os

from unittest.mock import patch


class TestDCRClientIdResolution:
    """Test _build_dcr_response() client_id priority chain:
    CYBERARK_OAUTH_CLIENT_ID > CYBERARK_CLIENT_ID > CYBERARK_OIDC_APP_ID
    """

    def test_oauth_client_id_takes_priority(self):
        """CYBERARK_OAUTH_CLIENT_ID should win over CYBERARK_CLIENT_ID."""
        from mcp_privilege_cloud.mcp_server import _build_dcr_response

        env = {
            "CYBERARK_OAUTH_CLIENT_ID": "1fc81892-a1ba-49ca-9bf9-7d1f1de19ea6",
            "CYBERARK_CLIENT_ID": "timtest@cyberark.cloud.3240",
        }
        with patch.dict(os.environ, env, clear=True):
            response = _build_dcr_response({})

        assert response["client_id"] == "1fc81892-a1ba-49ca-9bf9-7d1f1de19ea6"

    def test_legacy_client_id_not_leaked_via_dcr(self):
        """CYBERARK_CLIENT_ID (service account) should NOT be returned via DCR.
        DCR client_id chain: CYBERARK_OAUTH_CLIENT_ID > CYBERARK_OIDC_APP_ID only."""
        from mcp_privilege_cloud.mcp_server import _build_dcr_response
        from mcp_privilege_cloud.token_verifier import CYBERARK_OIDC_APP_ID

        env = {"CYBERARK_CLIENT_ID": "timtest@cyberark.cloud.3240"}
        with patch.dict(os.environ, env, clear=True):
            response = _build_dcr_response({})

        # Should fall back to OIDC app ID, NOT leak service account username
        assert response["client_id"] == CYBERARK_OIDC_APP_ID

    def test_falls_back_to_oidc_app_id(self):
        """Without either client ID var, should fall back to CYBERARK_OIDC_APP_ID."""
        from mcp_privilege_cloud.mcp_server import _build_dcr_response
        from mcp_privilege_cloud.token_verifier import CYBERARK_OIDC_APP_ID

        with patch.dict(os.environ, {}, clear=True):
            response = _build_dcr_response({})

        assert response["client_id"] == CYBERARK_OIDC_APP_ID

    def test_secret_never_in_dcr_response(self):
        """DCR should NEVER return client_secret, even when secrets are configured."""
        from mcp_privilege_cloud.mcp_server import _build_dcr_response

        env = {
            "CYBERARK_OAUTH_CLIENT_SECRET": "oauth-app-secret",
            "CYBERARK_CLIENT_SECRET": "service-account-password",
        }
        with patch.dict(os.environ, env, clear=True):
            response = _build_dcr_response({})

        assert "client_secret" not in response
        assert response["token_endpoint_auth_method"] == "none"

    def test_legacy_secret_never_in_dcr_response(self):
        """DCR should NEVER return CYBERARK_CLIENT_SECRET (service account password)."""
        from mcp_privilege_cloud.mcp_server import _build_dcr_response

        env = {"CYBERARK_CLIENT_SECRET": "service-account-password"}
        with patch.dict(os.environ, env, clear=True):
            response = _build_dcr_response({})

        assert "client_secret" not in response
        assert response["token_endpoint_auth_method"] == "none"

    def test_no_secret_is_public_client(self):
        """Without any secret, DCR should return public client (token_endpoint_auth_method=none)."""
        from mcp_privilege_cloud.mcp_server import _build_dcr_response

        with patch.dict(os.environ, {}, clear=True):
            response = _build_dcr_response({})

        assert response["token_endpoint_auth_method"] == "none"
        assert "client_secret" not in response


class TestGetOAuthCredentials:
    """Test _get_oauth_credentials() helper for server-side credential injection."""

    def test_oauth_secret_takes_priority(self):
        """CYBERARK_OAUTH_CLIENT_SECRET should win over CYBERARK_CLIENT_SECRET."""
        from mcp_privilege_cloud.mcp_server import _get_oauth_credentials

        env = {
            "CYBERARK_OAUTH_CLIENT_SECRET": "oauth-app-secret",
            "CYBERARK_CLIENT_SECRET": "service-account-password",
        }
        with patch.dict(os.environ, env, clear=True):
            _, secret = _get_oauth_credentials()

        assert secret == "oauth-app-secret"

    def test_no_legacy_secret_fallback(self):
        """Should NOT fall back to CYBERARK_CLIENT_SECRET for OAuth credentials."""
        from mcp_privilege_cloud.mcp_server import _get_oauth_credentials

        env = {"CYBERARK_CLIENT_SECRET": "service-account-password"}
        with patch.dict(os.environ, env, clear=True):
            _, secret = _get_oauth_credentials()

        assert secret == ""

    def test_warns_when_client_id_set_without_secret(self):
        """Should warn when CYBERARK_OAUTH_CLIENT_ID is set but secret is not."""
        from mcp_privilege_cloud.mcp_server import _get_oauth_credentials

        env = {"CYBERARK_OAUTH_CLIENT_ID": "some-uuid"}
        with patch.dict(os.environ, env, clear=True):
            with patch("mcp_privilege_cloud.mcp_server.logger") as mock_logger:
                _, secret = _get_oauth_credentials()

        assert secret == ""
        mock_logger.warning.assert_called_once()
        assert "CYBERARK_OAUTH_CLIENT_SECRET" in mock_logger.warning.call_args[0][0]

    def test_client_id_chain(self):
        """Client ID: CYBERARK_OAUTH_CLIENT_ID > CYBERARK_OIDC_APP_ID."""
        from mcp_privilege_cloud.mcp_server import _get_oauth_credentials
        from mcp_privilege_cloud.token_verifier import CYBERARK_OIDC_APP_ID

        env = {"CYBERARK_OAUTH_CLIENT_ID": "oauth-uuid-id"}
        with patch.dict(os.environ, env, clear=True):
            client_id, _ = _get_oauth_credentials()
        assert client_id == "oauth-uuid-id"

        # Without CYBERARK_OAUTH_CLIENT_ID, falls back to OIDC app ID
        with patch.dict(os.environ, {}, clear=True):
            client_id, _ = _get_oauth_credentials()
        assert client_id == CYBERARK_OIDC_APP_ID

    def test_empty_secret(self):
        """Should return empty string when no secret configured."""
        from mcp_privilege_cloud.mcp_server import _get_oauth_credentials

        with patch.dict(os.environ, {}, clear=True):
            _, secret = _get_oauth_credentials()

        assert secret == ""


