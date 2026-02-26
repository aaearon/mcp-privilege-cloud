"""Tests for environment variable resolution priority chains.

Tests the DCR client_id/secret and token verifier audience resolution
logic to ensure CYBERARK_OAUTH_CLIENT_ID takes priority over legacy vars.
"""

import os

import pytest
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

    def test_legacy_client_id_still_works(self):
        """CYBERARK_CLIENT_ID should be used when CYBERARK_OAUTH_CLIENT_ID is absent."""
        from mcp_privilege_cloud.mcp_server import _build_dcr_response

        env = {"CYBERARK_CLIENT_ID": "timtest@cyberark.cloud.3240"}
        with patch.dict(os.environ, env, clear=True):
            response = _build_dcr_response({})

        assert response["client_id"] == "timtest@cyberark.cloud.3240"

    def test_falls_back_to_oidc_app_id(self):
        """Without either client ID var, should fall back to CYBERARK_OIDC_APP_ID."""
        from mcp_privilege_cloud.mcp_server import _build_dcr_response
        from mcp_privilege_cloud.token_verifier import CYBERARK_OIDC_APP_ID

        with patch.dict(os.environ, {}, clear=True):
            response = _build_dcr_response({})

        assert response["client_id"] == CYBERARK_OIDC_APP_ID

    def test_oauth_client_secret_takes_priority(self):
        """CYBERARK_OAUTH_CLIENT_SECRET should win over CYBERARK_CLIENT_SECRET."""
        from mcp_privilege_cloud.mcp_server import _build_dcr_response

        env = {
            "CYBERARK_OAUTH_CLIENT_SECRET": "oauth-app-secret",
            "CYBERARK_CLIENT_SECRET": "service-account-password",
        }
        with patch.dict(os.environ, env, clear=True):
            response = _build_dcr_response({})

        assert response["client_secret"] == "oauth-app-secret"
        assert response["token_endpoint_auth_method"] == "client_secret_post"

    def test_legacy_secret_still_works(self):
        """CYBERARK_CLIENT_SECRET should be used when CYBERARK_OAUTH_CLIENT_SECRET is absent."""
        from mcp_privilege_cloud.mcp_server import _build_dcr_response

        env = {"CYBERARK_CLIENT_SECRET": "service-account-password"}
        with patch.dict(os.environ, env, clear=True):
            response = _build_dcr_response({})

        assert response["client_secret"] == "service-account-password"
        assert response["token_endpoint_auth_method"] == "client_secret_post"

    def test_no_secret_is_public_client(self):
        """Without any secret, DCR should return public client (token_endpoint_auth_method=none)."""
        from mcp_privilege_cloud.mcp_server import _build_dcr_response

        with patch.dict(os.environ, {}, clear=True):
            response = _build_dcr_response({})

        assert response["token_endpoint_auth_method"] == "none"
        assert "client_secret" not in response


class TestTokenVerifierAudienceResolution:
    """Test audience priority chain:
    CYBERARK_OAUTH_AUDIENCE > CYBERARK_OAUTH_CLIENT_ID > CYBERARK_CLIENT_ID > CYBERARK_OIDC_APP_ID
    """

    def test_oauth_audience_highest_priority(self):
        """CYBERARK_OAUTH_AUDIENCE should take highest priority (explicit override)."""
        from mcp_privilege_cloud.token_verifier import CyberArkTokenVerifier

        env = {
            "CYBERARK_OAUTH_AUDIENCE": "1fc81892-a1ba-49ca-9bf9-7d1f1de19ea6",
            "CYBERARK_OAUTH_CLIENT_ID": "c21840a7-trust-tab-id",
            "CYBERARK_CLIENT_ID": "timtest@cyberark.cloud.3240",
        }
        with patch.dict(os.environ, env):
            verifier = CyberArkTokenVerifier(
                identity_tenant_url="https://abc1234.id.cyberark.cloud",
            )

        assert verifier._expected_audience == "1fc81892-a1ba-49ca-9bf9-7d1f1de19ea6"

    def test_oauth_client_id_second_priority(self):
        """CYBERARK_OAUTH_CLIENT_ID should be 2nd priority for audience."""
        from mcp_privilege_cloud.token_verifier import CyberArkTokenVerifier

        env = {
            "CYBERARK_OAUTH_CLIENT_ID": "c21840a7-trust-tab-id",
            "CYBERARK_CLIENT_ID": "timtest@cyberark.cloud.3240",
        }
        with patch.dict(os.environ, env):
            os.environ.pop("CYBERARK_OAUTH_AUDIENCE", None)
            verifier = CyberArkTokenVerifier(
                identity_tenant_url="https://abc1234.id.cyberark.cloud",
            )

        assert verifier._expected_audience == "c21840a7-trust-tab-id"

    def test_legacy_client_id_fallback(self):
        """CYBERARK_CLIENT_ID should be used as 3rd fallback for audience."""
        from mcp_privilege_cloud.token_verifier import CyberArkTokenVerifier

        env = {"CYBERARK_CLIENT_ID": "some-client-id"}
        with patch.dict(os.environ, env):
            os.environ.pop("CYBERARK_OAUTH_CLIENT_ID", None)
            os.environ.pop("CYBERARK_OAUTH_AUDIENCE", None)
            verifier = CyberArkTokenVerifier(
                identity_tenant_url="https://abc1234.id.cyberark.cloud",
            )

        assert verifier._expected_audience == "some-client-id"

    def test_ultimate_fallback_to_oidc_app_id(self):
        """Without any env vars, audience should fall back to CYBERARK_OIDC_APP_ID."""
        from mcp_privilege_cloud.token_verifier import CyberArkTokenVerifier, CYBERARK_OIDC_APP_ID

        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("CYBERARK_OAUTH_CLIENT_ID", None)
            os.environ.pop("CYBERARK_OAUTH_AUDIENCE", None)
            os.environ.pop("CYBERARK_CLIENT_ID", None)
            verifier = CyberArkTokenVerifier(
                identity_tenant_url="https://abc1234.id.cyberark.cloud",
            )

        assert verifier._expected_audience == CYBERARK_OIDC_APP_ID
