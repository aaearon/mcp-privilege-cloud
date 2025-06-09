import asyncio
import httpx
import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from .auth import CyberArkAuthenticator

logger = logging.getLogger(__name__)


class CyberArkAPIError(Exception):
    """Raised when CyberArk API returns an error"""
    pass


class CyberArkMCPServer:
    """CyberArk Privilege Cloud MCP Server"""
    
    def __init__(
        self,
        authenticator: CyberArkAuthenticator,
        subdomain: str,
        timeout: int = 30,
        max_retries: int = 3
    ):
        self.authenticator = authenticator
        self.subdomain = subdomain
        self.timeout = timeout
        self.max_retries = max_retries
        self.logger = logger
        
        # Construct base API URL
        self.base_url = f"https://{subdomain}.privilegecloud.cyberark.cloud/PasswordVault/api"
    
    @classmethod
    def from_environment(cls) -> "CyberArkMCPServer":
        """Create server from environment variables"""
        subdomain = os.getenv("CYBERARK_SUBDOMAIN")
        timeout = int(os.getenv("CYBERARK_API_TIMEOUT", "30"))
        max_retries = int(os.getenv("CYBERARK_MAX_RETRIES", "3"))
        
        if not subdomain:
            raise ValueError("CYBERARK_SUBDOMAIN environment variable is required")
        
        # Create authenticator from environment
        authenticator = CyberArkAuthenticator.from_environment()
        
        return cls(
            authenticator=authenticator,
            subdomain=subdomain,
            timeout=timeout,
            max_retries=max_retries
        )
    
    def _get_api_url(self, endpoint: str) -> str:
        """Construct full API URL for an endpoint"""
        return f"{self.base_url}/{endpoint}"
    
    async def _make_api_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """Make an authenticated API request to CyberArk"""
        url = self._get_api_url(endpoint)
        
        try:
            # Get authentication headers
            auth_headers = await self.authenticator.get_auth_header()
            headers = {
                "Content-Type": "application/json",
                **auth_headers
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                self.logger.debug(f"Making {method} request to {url}")
                
                if method.upper() == "GET":
                    response = await client.get(url, headers=headers, params=params)
                elif method.upper() == "POST":
                    response = await client.post(url, headers=headers, json=json or data, params=params)
                elif method.upper() == "PUT":
                    response = await client.put(url, headers=headers, json=json or data, params=params)
                elif method.upper() == "DELETE":
                    response = await client.delete(url, headers=headers, params=params)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                response.raise_for_status()
                
                # Handle different response types
                if response.headers.get("content-type", "").startswith("application/json"):
                    return response.json()
                else:
                    return {"result": response.text}
                    
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401 and retry_count < self.max_retries:
                self.logger.warning("Received 401, refreshing token and retrying")
                # Force token refresh by clearing cached token
                self.authenticator._token = None
                return await self._make_api_request(method, endpoint, params, data, json, retry_count + 1)
            else:
                self._handle_api_error(e)
                raise CyberArkAPIError(f"API request failed: {e}")
        except httpx.ConnectError as e:
            self._log_error(f"Network error: {e}")
            raise CyberArkAPIError(f"Network error: {e}")
        except Exception as e:
            self._log_error(f"Unexpected error: {e}")
            raise CyberArkAPIError(f"Unexpected error: {e}")
    
    def _handle_api_error(self, error: httpx.HTTPStatusError):
        """Handle API errors with appropriate logging"""
        status_code = error.response.status_code
        self.logger.error(f"API error {status_code}: {error}")
        
        if status_code == 429:
            self.logger.warning("Rate limit exceeded")
        elif status_code == 403:
            self.logger.error("Insufficient permissions")
        elif status_code == 404:
            self.logger.warning("Resource not found")
    
    def _log_error(self, message: str):
        """Log error message"""
        self.logger.error(message)
    
    def get_available_tools(self) -> List[str]:
        """Get list of available MCP tools"""
        return [
            "list_accounts",
            "get_account_details",
            "search_accounts",
            "create_account",
            "list_safes",
            "get_safe_details",
            "list_platforms",
            "get_platform_details"
        ]
    
    # Account Management Tools
    
    async def list_accounts(
        self,
        safe_name: Optional[str] = None,
        username: Optional[str] = None,
        address: Optional[str] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """List accounts from CyberArk Privilege Cloud"""
        params = {}
        
        if safe_name:
            params["safeName"] = safe_name
        if username:
            params["userName"] = username
        if address:
            params["address"] = address
        
        # Add any additional filter parameters
        params.update(kwargs)
        
        self.logger.info(f"Listing accounts with filters: {params}")
        response = await self._make_api_request("GET", "Accounts", params=params)
        
        # CyberArk API returns accounts in 'value' field
        return response.get("value", [])
    
    async def get_account_details(self, account_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific account"""
        self.logger.info(f"Getting details for account ID: {account_id}")
        return await self._make_api_request("GET", f"Accounts/{account_id}")
    
    async def search_accounts(
        self,
        keywords: Optional[str] = None,
        safe_name: Optional[str] = None,
        username: Optional[str] = None,
        address: Optional[str] = None,
        platform_id: Optional[str] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Search for accounts with various criteria"""
        params = {}
        
        if keywords:
            params["search"] = keywords
        if safe_name:
            params["safeName"] = safe_name
        if username:
            params["userName"] = username
        if address:
            params["address"] = address
        if platform_id:
            params["platformId"] = platform_id
        
        # Add any additional search parameters
        params.update(kwargs)
        
        self.logger.info(f"Searching accounts with criteria: {params}")
        response = await self._make_api_request("GET", "Accounts", params=params)
        
        return response.get("value", [])
    
    async def create_account(
        self,
        platform_id: str,
        safe_name: str,
        name: Optional[str] = None,
        address: Optional[str] = None,
        user_name: Optional[str] = None,
        secret: Optional[str] = None,
        secret_type: Optional[str] = None,
        platform_account_properties: Optional[Dict[str, Any]] = None,
        secret_management: Optional[Dict[str, Any]] = None,
        remote_machines_access: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a new privileged account in CyberArk Privilege Cloud"""
        
        # Validate required parameters
        if not platform_id:
            raise ValueError("platformId is required")
        if not safe_name:
            raise ValueError("safeName is required")
        
        # Validate secret type if provided
        if secret_type and secret_type not in ["password", "key"]:
            raise ValueError("secretType must be 'password' or 'key'")
        
        # Validate account name for special characters if provided
        if name:
            invalid_chars = r'\/:;*?"<>|	 '  # Includes tab and space
            if any(char in name for char in invalid_chars):
                raise ValueError("Account name contains invalid characters")
        
        # Build request payload, filtering out None and empty values
        payload = {}
        
        # Required fields
        payload["platformId"] = platform_id
        payload["safeName"] = safe_name
        
        # Optional fields - only add if not None or empty
        if name:
            payload["name"] = name
        if address:
            payload["address"] = address
        if user_name:
            payload["userName"] = user_name
        if secret:
            payload["secret"] = secret
        if secret_type:
            payload["secretType"] = secret_type
        if platform_account_properties:
            payload["platformAccountProperties"] = platform_account_properties
        if secret_management:
            payload["secretManagement"] = secret_management
        if remote_machines_access:
            payload["remoteMachinesAccess"] = remote_machines_access
        
        # Add any additional parameters
        for key, value in kwargs.items():
            if value is not None and value != "":
                # Convert snake_case to camelCase for API compatibility
                if key == "platform_account_properties":
                    payload["platformAccountProperties"] = value
                elif key == "secret_management":
                    payload["secretManagement"] = value
                elif key == "remote_machines_access":
                    payload["remoteMachinesAccess"] = value
                elif key == "secret_type":
                    payload["secretType"] = value
                elif key == "user_name":
                    payload["userName"] = value
                elif key == "safe_name":
                    payload["safeName"] = value
                elif key == "platform_id":
                    payload["platformId"] = value
                else:
                    payload[key] = value
        
        self.logger.info(f"Creating account in safe '{safe_name}' with platform '{platform_id}'")
        
        try:
            response = await self._make_api_request("POST", "Accounts", json=payload)
            self.logger.info(f"Successfully created account with ID: {response.get('id', 'unknown')}")
            return response
        except Exception as e:
            self.logger.error(f"Failed to create account: {e}")
            raise
    
    # Safe Management Tools
    
    async def list_safes(
        self,
        search: Optional[str] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """List all accessible safes"""
        params = {}
        
        if search:
            params["search"] = search
        
        # Add any additional parameters
        params.update(kwargs)
        
        self.logger.info(f"Listing safes with parameters: {params}")
        response = await self._make_api_request("GET", "Safes", params=params)
        
        return response.get("value", [])
    
    async def get_safe_details(self, safe_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific safe"""
        self.logger.info(f"Getting details for safe: {safe_name}")
        return await self._make_api_request("GET", f"Safes/{safe_name}")
    
    # Health and Status Methods
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check of the CyberArk connection"""
        try:
            # Try to list safes as a simple health check
            safes = await self.list_safes()
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "safes_accessible": len(safes)
            }
        except Exception as e:
            return {
                "status": "unhealthy", 
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
    
    # Platform Management Tools
    
    async def list_platforms(
        self,
        search: Optional[str] = None,
        active: Optional[bool] = None,
        system_type: Optional[str] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """List available platforms from CyberArk Privilege Cloud"""
        params = {}
        
        if search:
            params["search"] = search
        if active is not None:
            params["active"] = "true" if active else "false"
        if system_type:
            params["systemType"] = system_type
        
        # Add any additional filter parameters
        params.update(kwargs)
        
        self.logger.info(f"Listing platforms with filters: {params}")
        response = await self._make_api_request("GET", "Platforms", params=params)
        
        # CyberArk API returns platforms in 'Platforms' field (capitalized), fallback to 'value' for consistency
        return response.get("Platforms", response.get("value", []))
    
    async def get_platform_details(self, platform_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific platform"""
        self.logger.info(f"Getting details for platform ID: {platform_id}")
        return await self._make_api_request("GET", f"Platforms/{platform_id}")