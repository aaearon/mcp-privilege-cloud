"""JWT token verification against CyberArk Identity JWKS.

Implements the MCP SDK's TokenVerifier protocol to validate OAuth JWTs
issued by CyberArk Identity, enabling per-user authentication in
Resource Server mode.
"""

import logging
from typing import Optional

import jwt as pyjwt
from jwt import PyJWKClient

from mcp.server.auth.provider import AccessToken, TokenVerifier

logger = logging.getLogger(__name__)

# OIDC application ID for CyberArk Identity.
# Configurable via CYBERARK_OIDC_APP_ID env var; defaults to custom app.
import os
CYBERARK_OIDC_APP_ID = os.getenv("CYBERARK_OIDC_APP_ID", "mcpprivilegecloud")


class CyberArkTokenVerifier(TokenVerifier):
    """Verify JWTs against CyberArk Identity JWKS endpoint.

    Implements the MCP SDK TokenVerifier protocol:
        async def verify_token(self, token: str) -> AccessToken | None

    Returns AccessToken on success, None on any verification failure.
    """

    def __init__(self, identity_tenant_url: str) -> None:
        """Initialize the token verifier.

        Args:
            identity_tenant_url: CyberArk Identity tenant URL
                (e.g., "https://abc1234.id.cyberark.cloud").
        """
        self._identity_tenant_url = identity_tenant_url.rstrip("/")
        self._jwks_uri = f"{self._identity_tenant_url}/oauth2/certs"
        self._jwks_client = PyJWKClient(self._jwks_uri, cache_keys=True)

        logger.info(
            "Token verifier initialized (tenant: %s)",
            self._identity_tenant_url,
        )

    async def verify_token(self, token: str) -> Optional[AccessToken]:
        """Verify a JWT token and return an AccessToken if valid.

        Args:
            token: Raw JWT Bearer token string.

        Returns:
            AccessToken with client_id, scopes, and expiry on success.
            None if verification fails for any reason.
        """
        try:
            claims = await self._decode_and_verify(token)
        except (
            pyjwt.ExpiredSignatureError,
            pyjwt.InvalidSignatureError,
            pyjwt.InvalidAudienceError,
            pyjwt.InvalidIssuerError,
            pyjwt.DecodeError,
            pyjwt.InvalidTokenError,
            pyjwt.PyJWKClientConnectionError,
            Exception,
        ) as e:
            logger.warning("Token verification failed: %s", e)
            return None

        # Validate required claims
        sub = claims.get("sub")
        if not sub:
            logger.warning("Token missing required 'sub' claim")
            return None

        # Extract scopes from space-delimited scope claim
        scope_str = claims.get("scope", "")
        scopes = scope_str.split() if scope_str else []

        return AccessToken(
            token=token,
            client_id=sub,
            scopes=scopes,
            expires_at=claims.get("exp"),
        )

    async def _decode_and_verify(self, token: str) -> dict:
        """Decode and verify a JWT using JWKS.

        Fetches the signing key from CyberArk Identity's JWKS endpoint
        and verifies the token signature, expiry, audience, and issuer.

        Args:
            token: Raw JWT string.

        Returns:
            Decoded JWT claims dictionary.

        Raises:
            jwt.PyJWTError: On any verification failure.
        """
        signing_key = self._jwks_client.get_signing_key_from_jwt(token)

        return pyjwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=CYBERARK_OIDC_APP_ID,
            issuer=self._identity_tenant_url + "/",
            options={"require": ["exp", "iss", "sub", "aud"]},
        )
