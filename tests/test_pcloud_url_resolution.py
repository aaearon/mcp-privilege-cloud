"""Tests for PCloud URL resolution with CYBERARK_SUBDOMAIN override.

Verifies that the SDK resolves the correct PCloud API URL when the
OAuth JWT lacks subdomain/platform_domain claims.
"""

import os
import time

import pytest
from unittest.mock import patch, MagicMock

from ark_sdk_python.common.isp.ark_isp_service_client import ArkISPServiceClient


class TestPCloudURLResolution:
    """Test ArkISPServiceClient.service_url() behavior with different JWT claims."""

    def test_jwt_with_subdomain_claim_resolves_correctly(self):
        """JWT with subdomain claim should resolve the correct PCloud URL."""
        import base64, json

        claims = {"subdomain": "cyberiam", "platform_domain": "cyberark.cloud"}
        payload = base64.urlsafe_b64encode(json.dumps(claims).encode()).rstrip(b"=").decode()
        fake_jwt = f"eyJhbGciOiJSUzI1NiJ9.{payload}.fakesig"

        url = ArkISPServiceClient.service_url(
            service_name="privilegecloud",
            token=fake_jwt,
        )

        assert url == "https://cyberiam.privilegecloud.cyberark.cloud"

    def test_jwt_without_subdomain_uses_unique_name_fallback(self):
        """JWT without subdomain claim falls back to unique_name parsing."""
        import base64, json

        # This simulates the OAuth JWT from CyberArk Identity
        claims = {"unique_name": "timtest@cyberark.cloud.3240"}
        payload = base64.urlsafe_b64encode(json.dumps(claims).encode()).rstrip(b"=").decode()
        fake_jwt = f"eyJhbGciOiJSUzI1NiJ9.{payload}.fakesig"

        url = ArkISPServiceClient.service_url(
            service_name="privilegecloud",
            token=fake_jwt,
        )

        # BUG: SDK extracts 'cyberark' from 'cyberark.cloud.3240'
        assert url == "https://cyberark.privilegecloud.cyberark.cloud"

    def test_tenant_subdomain_param_overrides_bad_unique_name(self):
        """Explicit tenant_subdomain parameter should override unique_name fallback."""
        import base64, json

        claims = {"unique_name": "timtest@cyberark.cloud.3240"}
        payload = base64.urlsafe_b64encode(json.dumps(claims).encode()).rstrip(b"=").decode()
        fake_jwt = f"eyJhbGciOiJSUzI1NiJ9.{payload}.fakesig"

        url = ArkISPServiceClient.service_url(
            service_name="privilegecloud",
            tenant_subdomain="cyberiam",
            token=fake_jwt,
        )

        # tenant_subdomain only applies when JWT has no subdomain claim
        # Since our JWT has no subdomain claim, tenant_subdomain is used
        assert url == "https://cyberiam.privilegecloud.cyberark.cloud"


class TestOverridePCloudBaseUrl:
    """Test the _override_pcloud_base_url helper."""

    def test_overrides_base_url_on_service_client(self):
        """Should replace the service's _client base URL with the correct subdomain."""
        from mcp_privilege_cloud.server import CyberArkMCPServer
        from ark_sdk_python.common.ark_client import ArkClient

        # Create a real ArkClient so name-mangled attribute works
        client = ArkClient(
            base_url="https://cyberark.privilegecloud.cyberark.cloud/passwordvault/api/"
        )
        mock_service = MagicMock()
        mock_service._client = client

        CyberArkMCPServer._override_pcloud_base_url(mock_service, "cyberiam")

        expected = "https://cyberiam.privilegecloud.cyberark.cloud/passwordvault/api/"
        assert client.base_url == expected
