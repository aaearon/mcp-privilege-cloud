import asyncio
import httpx
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """Raised when authentication with CyberArk fails"""
    pass


class CyberArkAuthenticator:
    """Handles OAuth 2.0 authentication with CyberArk Identity Shared Services"""
    
    def __init__(
        self,
        identity_tenant_id: str,
        client_id: str,
        client_secret: str,
        timeout: int = 30
    ):
        self.identity_tenant_id = identity_tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.timeout = timeout
        
        # Token management
        self._token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None
        self._token_lock = asyncio.Lock()
        
        # Safety margin for token refresh (60 seconds before expiry)
        self._expiry_margin = timedelta(seconds=60)
    
    @classmethod
    def from_environment(cls) -> "CyberArkAuthenticator":
        """Create authenticator from environment variables"""
        identity_tenant_id = os.getenv("CYBERARK_IDENTITY_TENANT_ID")
        client_id = os.getenv("CYBERARK_CLIENT_ID")
        client_secret = os.getenv("CYBERARK_CLIENT_SECRET")
        timeout = int(os.getenv("CYBERARK_API_TIMEOUT", "30"))
        
        if not identity_tenant_id:
            raise ValueError("CYBERARK_IDENTITY_TENANT_ID environment variable is required")
        if not client_id:
            raise ValueError("CYBERARK_CLIENT_ID environment variable is required")
        if not client_secret:
            raise ValueError("CYBERARK_CLIENT_SECRET environment variable is required")
        
        return cls(
            identity_tenant_id=identity_tenant_id,
            client_id=client_id,
            client_secret=client_secret,
            timeout=timeout
        )
    
    def _get_token_url(self) -> str:
        """Get the OAuth token endpoint URL"""
        return f"https://{self.identity_tenant_id}.id.cyberark.cloud/oauth2/platformtoken"
    
    async def _request_new_token(self) -> str:
        """Request a new OAuth token from CyberArk"""
        url = self._get_token_url()
        
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.debug(f"Requesting new token from {url}")
                response = await client.post(url, data=data, headers=headers)
                response.raise_for_status()
                
                try:
                    token_data = response.json()
                except ValueError as e:
                    raise AuthenticationError(f"Invalid response format: {e}")
                
                if "access_token" not in token_data:
                    raise AuthenticationError("Missing access_token in response")
                
                access_token = token_data["access_token"]
                expires_in = token_data.get("expires_in", 900)  # Default 15 minutes
                
                # Set token expiry
                self._token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)
                
                logger.info("Successfully obtained new OAuth token")
                return access_token
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error during authentication: {e}")
            raise AuthenticationError(f"Failed to authenticate: {e}")
        except httpx.ConnectError as e:
            logger.error(f"Network error during authentication: {e}")
            raise AuthenticationError(f"Network error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during authentication: {e}")
            raise AuthenticationError(f"Authentication failed: {e}")
    
    def _is_token_valid(self) -> bool:
        """Check if the current token is valid and not near expiry"""
        if not self._token or not self._token_expiry:
            return False
        
        # Check if token is expired or near expiry (with safety margin)
        now = datetime.utcnow()
        expiry_with_margin = self._token_expiry - self._expiry_margin
        
        return now < expiry_with_margin
    
    async def get_valid_token(self) -> str:
        """Get a valid OAuth token, refreshing if necessary"""
        async with self._token_lock:
            if self._is_token_valid():
                logger.debug("Using cached token")
                return self._token
            
            logger.debug("Token invalid or near expiry, requesting new token")
            self._token = await self._request_new_token()
            return self._token
    
    async def get_auth_header(self) -> Dict[str, str]:
        """Get the authorization header with a valid bearer token"""
        token = await self.get_valid_token()
        return {"Authorization": f"Bearer {token}"}