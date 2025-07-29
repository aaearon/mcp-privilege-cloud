"""SDK-based authentication for CyberArk using ark-sdk-python"""

import os
import logging
from typing import Optional

from ark_sdk_python.auth import ArkISPAuth
from ark_sdk_python.models.auth import (
    ArkAuthProfile,
    ArkAuthMethod,
    ArkSecret,
    IdentityArkAuthMethodSettings
)

logger = logging.getLogger(__name__)


class SDKAuthenticationError(Exception):
    """Raised when SDK authentication with CyberArk fails"""
    pass


class CyberArkSDKAuthenticator:
    """Handles authentication with CyberArk using the official ark-sdk-python"""

    def __init__(
        self,
        client_id: str,
        client_secret: str
    ):
        self.client_id = client_id
        self.client_secret = client_secret

        # SDK auth instance
        self._sdk_auth: Optional[ArkISPAuth] = None
        self._is_authenticated = False

    @classmethod
    def from_environment(cls) -> "CyberArkSDKAuthenticator":
        """Create authenticator from environment variables"""
        # Debug: log all environment variables for debugging
        logger.debug(f"Environment variables check:")
        logger.debug(f"CYBERARK_CLIENT_ID: {bool(os.getenv('CYBERARK_CLIENT_ID'))}")
        logger.debug(f"CYBERARK_CLIENT_SECRET: {bool(os.getenv('CYBERARK_CLIENT_SECRET'))}")
        logger.debug(f"CYBERARK_IDENTITY_TENANT_ID: {bool(os.getenv('CYBERARK_IDENTITY_TENANT_ID'))}")
        logger.debug(f"CYBERARK_SUBDOMAIN: {bool(os.getenv('CYBERARK_SUBDOMAIN'))}")

        client_id = os.getenv("CYBERARK_CLIENT_ID")
        client_secret = os.getenv("CYBERARK_CLIENT_SECRET")

        if not client_id:
            logger.error("CYBERARK_CLIENT_ID environment variable is missing")
            raise ValueError("CYBERARK_CLIENT_ID environment variable is required")
        if not client_secret:
            logger.error("CYBERARK_CLIENT_SECRET environment variable is missing")
            raise ValueError("CYBERARK_CLIENT_SECRET environment variable is required")

        logger.debug(f"Successfully loaded credentials for client_id: {client_id[:10]}...")
        return cls(
            client_id=client_id,
            client_secret=client_secret
        )

    def _initialize_sdk_auth(self) -> ArkISPAuth:
        """Initialize the SDK authentication object"""
        if self._sdk_auth is None:
            logger.debug("Initializing ark-sdk-python authentication")
            # Disable authentication caching to avoid D-Bus/keyring issues in CLI environments
            self._sdk_auth = ArkISPAuth(cache_authentication=False)

        return self._sdk_auth

    def authenticate(self) -> ArkISPAuth:
        """Authenticate with CyberArk using the SDK and return authenticated client"""
        try:
            sdk_auth = self._initialize_sdk_auth()

            # Create authentication profile for Identity method
            auth_profile = ArkAuthProfile(
                username=self.client_id,
                auth_method=ArkAuthMethod.Identity,
                auth_method_settings=IdentityArkAuthMethodSettings()
            )

            # Create secret object
            secret = ArkSecret(secret=self.client_secret)

            logger.info("Authenticating with CyberArk using ark-sdk-python")

            # Perform authentication
            sdk_auth.authenticate(
                auth_profile=auth_profile,
                secret=secret
            )

            self._is_authenticated = True
            logger.info("Successfully authenticated with CyberArk SDK")

            return sdk_auth

        except Exception as e:
            logger.error(f"SDK authentication failed: {e}")
            raise SDKAuthenticationError(f"Failed to authenticate with CyberArk SDK: {e}")

    def get_authenticated_client(self) -> ArkISPAuth:
        """Get an authenticated SDK client, authenticating if necessary"""
        if not self._is_authenticated or self._sdk_auth is None:
            return self.authenticate()

        # TODO: Add token validity check and re-authentication logic
        # The SDK should handle this internally, but we may want to add explicit checks

        return self._sdk_auth

    def is_authenticated(self) -> bool:
        """Check if the client is currently authenticated"""
        return self._is_authenticated and self._sdk_auth is not None


# Backward compatibility function for existing code
def create_sdk_authenticator() -> CyberArkSDKAuthenticator:
    """Create SDK authenticator from environment variables"""
    return CyberArkSDKAuthenticator.from_environment()