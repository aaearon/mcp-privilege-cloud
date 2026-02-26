"""Token-based authentication bridge for ark-sdk-python.

Subclasses ArkISPAuth to accept pre-existing JWT tokens from external OAuth flows
(e.g., CyberArk Identity Authorization Code flow) instead of performing its own
authentication. This enables per-user OAuth in Resource Server mode.
"""

import base64
import json
import logging
import os
import time
from datetime import datetime
from typing import Optional

from pydantic import SecretStr

from ark_sdk_python.auth import ArkISPAuth
from ark_sdk_python.models.auth import (
    ArkAuthMethod,
    ArkAuthProfile,
    ArkToken,
    ArkTokenType,
    IdentityArkAuthMethodSettings,
)

logger = logging.getLogger(__name__)


def _decode_jwt_claims(jwt_token: str) -> dict:
    """Decode JWT claims without signature verification.

    Verification is already performed upstream by CyberArkTokenVerifier.
    This only extracts claims for constructing the ArkToken.

    Raises:
        ValueError: If the JWT cannot be decoded.
    """
    try:
        parts = jwt_token.split(".")
        if len(parts) != 3:
            raise ValueError("Invalid JWT format: expected 3 segments")
        # Add padding for base64 decoding
        payload = parts[1]
        padding = 4 - len(payload) % 4
        if padding != 4:
            payload += "=" * padding
        decoded = base64.urlsafe_b64decode(payload)
        return json.loads(decoded)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise ValueError(f"Invalid JWT: could not decode payload: {e}") from e


class ArkISPAuthFromToken(ArkISPAuth):
    """ArkISPAuth pre-loaded with an externally-obtained OAuth JWT token.

    Bridges CyberArk Identity OAuth Authorization Code flow JWTs into the
    ark-sdk-python authentication interface, enabling per-user sessions
    with PCloud services.
    """

    def __init__(
        self,
        jwt_token: str,
        username: str,
        refresh_token: Optional[str] = None,
    ) -> None:
        """Initialize with a pre-existing JWT token.

        Args:
            jwt_token: Raw JWT access token string from CyberArk Identity.
            username: Username associated with the token.
            refresh_token: Optional OAuth refresh token for token renewal.

        Raises:
            ValueError: If the JWT is malformed, expired, or missing required claims.
        """
        # Decode claims (verification already done by TokenVerifier)
        claims = _decode_jwt_claims(jwt_token)

        # Validate required claims
        if "sub" not in claims:
            raise ValueError("JWT missing required 'sub' claim")

        # Check expiry
        exp = claims.get("exp")
        if exp is not None and exp < time.time():
            raise ValueError(
                f"JWT token expired at {datetime.fromtimestamp(exp).isoformat()}"
            )

        # Log claims relevant to SDK URL resolution
        logger.info(
            "JWT claims for SDK URL resolution — subdomain: %s, "
            "platform_domain: %s, unique_name: %s",
            claims.get("subdomain"),
            claims.get("platform_domain"),
            claims.get("unique_name"),
        )

        # Determine env from platform_domain or default to prod
        env = os.environ.get("DEPLOY_ENV", "prod")

        # Build ArkToken with metadata compatible with PCloud service initialization
        ark_token = ArkToken(
            token=SecretStr(jwt_token),
            username=username,
            endpoint=claims.get("iss", ""),
            token_type=ArkTokenType.JWT,
            auth_method=ArkAuthMethod.Identity,
            expires_in=(
                datetime.fromtimestamp(exp) if exp else None
            ),
            refresh_token=refresh_token,
            metadata={"env": env},
        )

        # Initialize parent with pre-existing token, no caching
        super().__init__(cache_authentication=False, token=ark_token)

        # Set active auth profile for service compatibility
        self._active_auth_profile = ArkAuthProfile(
            username=username,
            auth_method=ArkAuthMethod.Identity,
            auth_method_settings=IdentityArkAuthMethodSettings(),
        )

        logger.info(
            "Token auth bridge initialized for user: %s (exp: %s)",
            username,
            datetime.fromtimestamp(exp).isoformat() if exp else "none",
        )
