"""JWT token verification against CyberArk Identity JWKS.

Implements the MCP SDK's TokenVerifier protocol to validate OAuth JWTs
issued by CyberArk Identity, enabling per-user authentication in
Resource Server mode.

JWKS URI is resolved lazily from OIDC discovery on first token
verification, ensuring compatibility with all CyberArk Identity app
types (OAuth 2.0 Client, OIDC, etc.).
"""

import logging
import os
from typing import Optional

import httpx
import jwt as pyjwt
from jwt import PyJWKClient

from mcp.server.auth.provider import AccessToken, TokenVerifier

logger = logging.getLogger(__name__)

# OIDC application ID for CyberArk Identity.
# Configurable via CYBERARK_OIDC_APP_ID env var; defaults to custom app.
CYBERARK_OIDC_APP_ID = os.getenv("CYBERARK_OIDC_APP_ID", "mcpprivilegecloud")


class CyberArkTokenVerifier(TokenVerifier):
    """Verify JWTs against CyberArk Identity JWKS endpoint.

    Implements the MCP SDK TokenVerifier protocol:
        async def verify_token(self, token: str) -> AccessToken | None

    The JWKS URI is resolved lazily from the OIDC discovery document
    on first use, so it works regardless of CyberArk Identity app type.
    Returns AccessToken on success, None on any verification failure.
    """

    def __init__(self, identity_tenant_url: str) -> None:
        """Initialize the token verifier.

        Args:
            identity_tenant_url: CyberArk Identity tenant URL
                (e.g., "https://abc1234.id.cyberark.cloud").
        """
        self._identity_tenant_url = identity_tenant_url.rstrip("/")
        self._jwks_uri: Optional[str] = None
        self._jwks_client: Optional[PyJWKClient] = None

        # The app name used for OIDC discovery and issuer validation
        self._expected_app_id = CYBERARK_OIDC_APP_ID

        # Accepted audiences for JWT validation. CyberArk Identity sets the
        # `aud` claim to the client_id used in the authorization request.
        # When DCR returns CYBERARK_OAUTH_CLIENT_ID, tokens will have that
        # as the audience. The internal app ID (CYBERARK_OAUTH_AUDIENCE) may
        # differ, so we accept both.
        audiences = set()
        for var in ("CYBERARK_OAUTH_AUDIENCE", "CYBERARK_OAUTH_CLIENT_ID"):
            val = os.getenv(var)
            if val:
                audiences.add(val)
        if not audiences:
            audiences.add(CYBERARK_OIDC_APP_ID)
        self._expected_audience = audiences

        logger.info(
            "Token verifier initialized (tenant: %s, accepted audiences: %s)",
            self._identity_tenant_url,
            self._expected_audience,
        )

    async def _ensure_jwks_client(self) -> None:
        """Lazily resolve JWKS URI from OIDC discovery and create client.

        Fetches the OIDC discovery document to obtain the authoritative
        jwks_uri. Falls back to a constructed URI if discovery fails.
        """
        if self._jwks_client is not None:
            return

        discovery_url = (
            f"{self._identity_tenant_url}/{CYBERARK_OIDC_APP_ID}"
            f"/.well-known/openid-configuration"
        )
        fallback_uri = f"{self._identity_tenant_url}/OAuth2/Keys/{CYBERARK_OIDC_APP_ID}"

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(discovery_url)
                resp.raise_for_status()
                oidc_config = resp.json()
                self._jwks_uri = oidc_config.get("jwks_uri", fallback_uri)
                logger.info("JWKS URI resolved from OIDC discovery: %s", self._jwks_uri)
        except Exception as e:
            logger.warning(
                "OIDC discovery failed (%s), using fallback JWKS URI: %s",
                e, fallback_uri,
            )
            self._jwks_uri = fallback_uri

        self._jwks_client = PyJWKClient(self._jwks_uri, cache_keys=True)

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
        ) as e:
            logger.warning("Token verification failed: %s", e)
            self._log_unverified_claims(token)
            return None
        except Exception:
            logger.exception("Unexpected error during token verification")
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

    def _log_unverified_claims(self, token: str) -> None:
        """Log token claims (without signature) for debugging."""
        try:
            unverified = pyjwt.decode(token, options={"verify_signature": False})
            logger.warning(
                "Token claims — iss: %s, aud: %s, sub: %s (expected aud: %s)",
                unverified.get("iss"), unverified.get("aud"), unverified.get("sub"),
                self._expected_audience,
            )
        except Exception:
            pass

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
        await self._ensure_jwks_client()
        signing_key = self._jwks_client.get_signing_key_from_jwt(token)

        return pyjwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=self._expected_audience,
            issuer=f"{self._identity_tenant_url}/{self._expected_app_id}/",
            options={"require": ["exp", "iss", "sub", "aud"]},
        )
