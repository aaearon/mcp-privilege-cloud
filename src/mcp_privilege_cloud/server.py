import asyncio
import httpx
import os
import logging
from typing import Optional, Dict, Any, List, Union
from datetime import datetime

from .auth import CyberArkAuthenticator

logger = logging.getLogger(__name__)


class CyberArkAPIError(Exception):
    """Raised when CyberArk API returns an error"""
    
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


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
                raise CyberArkAPIError(f"API request failed: {e}", e.response.status_code)
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
            "change_account_password",
            "set_next_password",
            "verify_account_password",
            "reconcile_account_password",
            "list_safes",
            "get_safe_details",
            "list_platforms",
            "get_platform_details",
            "import_platform_package"
        ]
    
    # Account Management Tools
    
    async def list_accounts(
        self,
        safe_name: Optional[str] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """List accounts from CyberArk Privilege Cloud
        
        Args:
            safe_name: Optional safe name to filter accounts by
            **kwargs: Additional valid API parameters including:
                - search: Keywords to search for
                - searchType: "contains" or "startswith"
                - sort: Sort order
                - offset: Pagination offset
                - limit: Maximum results to return
                - filter: Filter expression (e.g., "safeName eq MySafe")
                - savedfilter: Predefined filter names
        
        Returns:
            List of account dictionaries
        """
        params = {}
        
        if safe_name:
            params["filter"] = f"safeName eq {safe_name}"
        
        # Add any additional valid API parameters
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
        """Search for accounts with various criteria using proper API filter syntax
        
        Args:
            keywords: General search keywords (mapped to 'search' parameter)
            safe_name: Filter by safe name (added to filter expression)
            username: Filter by username (added to filter expression)
            address: Filter by address (added to filter expression)
            platform_id: Filter by platform ID (added to filter expression)
            **kwargs: Additional search parameters
            
        Returns:
            List of account objects matching the search criteria
            
        Note:
            This method uses the GET /Accounts endpoint with proper parameter names:
            - 'search' for general keywords
            - 'filter' for complex filtering with expressions like "safeName eq MySafe AND userName eq myuser"
            - Other parameters like searchType can be passed via kwargs
        """
        params = {}
        filter_expressions = []
        
        # Handle general keyword search
        if keywords:
            params["search"] = keywords
        
        # Build filter expressions for specific criteria
        if safe_name:
            filter_expressions.append(f"safeName eq {safe_name}")
        if username:
            filter_expressions.append(f"userName eq {username}")
        if address:
            filter_expressions.append(f"address eq {address}")
        if platform_id:
            filter_expressions.append(f"platformId eq {platform_id}")
        
        # Combine filter expressions with AND operator
        if filter_expressions:
            params["filter"] = " AND ".join(filter_expressions)
        
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

    async def change_account_password(
        self,
        account_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Initiate CPM-managed password change for an existing account in CyberArk Privilege Cloud
        
        This method triggers the Central Policy Manager (CPM) to change the account password
        according to the platform's password policy. The CPM will automatically generate
        a new password based on the platform configuration.
        
        Args:
            account_id: The unique ID of the account to change password for
            **kwargs: Additional parameters (not used currently)
            
        Returns:
            Dict containing password change response with status and timestamps
            
        Raises:
            ValueError: If account_id is missing or invalid
            CyberArkAPIError: If the API request fails
        """
        # Validate required parameters
        if not account_id or (isinstance(account_id, str) and not account_id.strip()):
            raise ValueError("account_id is required")
        
        # Ensure account_id is a string
        if not isinstance(account_id, str):
            raise ValueError("account_id is required")
            
        # Clean account_id
        account_id = account_id.strip()
        
        # Build request payload for CPM-managed password change
        payload = {"ChangeCredsForGroup": True}
        
        # Log operation
        self.logger.info(f"Initiating CPM-managed password change for account ID: {account_id}")
        
        try:
            response = await self._make_api_request(
                "POST", 
                f"Accounts/{account_id}/Change/",
                json=payload
            )
            self.logger.info(f"CPM-managed password change initiated successfully for account ID: {account_id}")
            return response
        except Exception as e:
            self.logger.error(f"Failed to initiate CPM-managed password change for account ID: {account_id} - {e}")
            raise

    async def set_next_password(
        self,
        account_id: str,
        new_password: str,
        change_immediately: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """Set the next password for an existing account in CyberArk Privilege Cloud
        
        This method manually sets the next password for an account, which is different from
        CPM-managed password changes. The password will be set immediately by default.
        
        Args:
            account_id: The unique ID of the account to set password for
            new_password: The new password to set for the account
            change_immediately: Whether to change the password immediately (default: True)
            **kwargs: Additional parameters (not used currently)
            
        Returns:
            Dict containing password set response with status and timestamps
            
        Raises:
            ValueError: If account_id or new_password is missing or invalid
            CyberArkAPIError: If the API request fails
        """
        # Validate required parameters
        if not account_id or (isinstance(account_id, str) and not account_id.strip()):
            raise ValueError("account_id is required")
        
        if not new_password or (isinstance(new_password, str) and not new_password.strip()):
            raise ValueError("new_password is required")
        
        # Ensure account_id is a string
        if not isinstance(account_id, str):
            raise ValueError("account_id must be a string")
            
        # Ensure new_password is a string
        if not isinstance(new_password, str):
            raise ValueError("new_password must be a string")
            
        # Clean account_id
        account_id = account_id.strip()
        
        # Build request payload
        payload = {
            "ChangeImmediately": change_immediately,
            "NewCredentials": new_password
        }
        
        # Log operation (without sensitive data)
        self.logger.info(f"Setting next password for account ID: {account_id} (change_immediately={change_immediately})")
        
        try:
            response = await self._make_api_request(
                "POST", 
                f"Accounts/{account_id}/SetNextPassword/",
                json=payload
            )
            self.logger.info(f"Next password set successfully for account ID: {account_id}")
            return response
        except Exception as e:
            self.logger.error(f"Failed to set next password for account ID: {account_id} - {e}")
            raise

    async def verify_account_password(
        self,
        account_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Verify the password for an existing account in CyberArk Privilege Cloud
        
        Args:
            account_id: The unique ID of the account to verify password for
            **kwargs: Additional parameters (not used currently)
            
        Returns:
            Dict containing password verification response with status and timestamps
            
        Raises:
            ValueError: If account_id is missing or invalid
            CyberArkAPIError: If the API request fails
        """
        # Validate required parameters
        if not account_id or (isinstance(account_id, str) and not account_id.strip()):
            raise ValueError("account_id is required")
        
        # Ensure account_id is a string
        if not isinstance(account_id, str):
            raise ValueError("account_id is required")
            
        # Clean account_id
        account_id = account_id.strip()
        
        # Log operation (without sensitive data)
        self.logger.info(f"Initiating password verification for account ID: {account_id}")
        
        try:
            response = await self._make_api_request(
                "POST", 
                f"Accounts/{account_id}/Verify/",
                json={}
            )
            self.logger.info(f"Password verification completed successfully for account ID: {account_id}")
            return response
        except Exception as e:
            self.logger.error(f"Failed to verify password for account ID: {account_id} - {e}")
            raise

    async def reconcile_account_password(
        self,
        account_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Reconcile the password for an existing account in CyberArk Privilege Cloud
        
        Args:
            account_id: The unique ID of the account to reconcile password for
            **kwargs: Additional parameters (not used currently)
            
        Returns:
            Dict containing password reconciliation response with status and timestamps
            
        Raises:
            ValueError: If account_id is missing or invalid
            CyberArkAPIError: If the API request fails
        """
        # Validate required parameters
        if not account_id or (isinstance(account_id, str) and not account_id.strip()):
            raise ValueError("account_id is required")
        
        # Ensure account_id is a string
        if not isinstance(account_id, str):
            raise ValueError("account_id is required")
            
        # Clean account_id
        account_id = account_id.strip()
        
        # Log operation (without sensitive data)
        self.logger.info(f"Initiating password reconciliation for account ID: {account_id}")
        
        try:
            response = await self._make_api_request(
                "POST", 
                f"Accounts/{account_id}/Reconcile/",
                json={}
            )
            self.logger.info(f"Password reconciliation completed successfully for account ID: {account_id}")
            return response
        except Exception as e:
            self.logger.error(f"Failed to reconcile password for account ID: {account_id} - {e}")
            raise
    
    # Safe Management Tools
    
    async def list_safes(
        self,
        search: Optional[str] = None,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
        sort: Optional[str] = None,
        include_accounts: Optional[bool] = None,
        extended_details: Optional[bool] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        List all accessible safes from CyberArk Privilege Cloud.
        
        Args:
            search: Search term for safe names (URL encoded automatically)
            offset: Offset of the first Safe returned (default: 0)
            limit: Maximum number of Safes returned (default: 25)
            sort: Sort order - "safeName asc" or "safeName desc" (default: safeName asc)
            include_accounts: Whether to include accounts for each Safe (default: False)
            extended_details: Whether to return all Safe details or only safeName (default: True)
            **kwargs: Additional query parameters
            
        Returns:
            List of safe objects (excludes Internal Safes)
        """
        params = {}
        
        if search:
            params["search"] = search
        if offset is not None:
            params["offset"] = offset
        if limit is not None:
            params["limit"] = limit
        if sort:
            params["sort"] = sort
        if include_accounts is not None:
            params["includeAccounts"] = "true" if include_accounts else "false"
        if extended_details is not None:
            params["extendedDetails"] = "true" if extended_details else "false"
        
        # Add any additional parameters
        params.update(kwargs)
        
        self.logger.info(f"Listing safes with parameters: {params}")
        response = await self._make_api_request("GET", "Safes", params=params)
        
        # API returns safes in 'value' field
        return response.get("value", [])
    
    async def get_safe_details(
        self, 
        safe_name: str,
        include_accounts: Optional[bool] = None,
        use_cache: Optional[bool] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Get detailed information about a specific safe.
        
        Args:
            safe_name: The Safe name (URL encoding handled automatically by httpx)
            include_accounts: Whether to include accounts for the Safe (default: False)
            use_cache: Whether to retrieve from session cache (default: False)
            **kwargs: Additional query parameters
            
        Returns:
            Safe object with detailed information
            
        Note:
            Safe name should be URL encoded for special characters.
            For dots (.), add forward slash (/) at end of URL.
        """
        params = {}
        
        if include_accounts is not None:
            params["includeAccounts"] = "true" if include_accounts else "false"
        if use_cache is not None:
            params["useCache"] = "true" if use_cache else "false"
            
        # Add any additional parameters
        params.update(kwargs)
        
        self.logger.info(f"Getting details for safe: {safe_name}")
        if params:
            self.logger.debug(f"Using query parameters: {params}")
            
        return await self._make_api_request("GET", f"Safes/{safe_name}", params=params if params else None)
    
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

    async def import_platform_package(
        self,
        platform_package_file: Union[str, bytes],
        **kwargs
    ) -> Dict[str, Any]:
        """Import a platform package to CyberArk Privilege Cloud
        
        Args:
            platform_package_file: Either a file path (str) or file content (bytes) of the platform package ZIP file
            **kwargs: Additional parameters
            
        Returns:
            Dict containing the imported platform ID
            
        Raises:
            CyberArkAPIError: If import fails
            ValueError: If file is invalid or too large
        """
        import base64
        import os
        
        # Handle file input - convert to base64 encoded bytes
        if isinstance(platform_package_file, str):
            # It's a file path
            if not os.path.exists(platform_package_file):
                raise ValueError(f"Platform package file not found: {platform_package_file}")
            
            with open(platform_package_file, 'rb') as f:
                file_content = f.read()
        elif isinstance(platform_package_file, bytes):
            # It's already file content
            file_content = platform_package_file
        else:
            raise ValueError("platform_package_file must be either a file path (str) or file content (bytes)")
        
        # Check file size (20MB limit according to API docs)
        max_size = 20 * 1024 * 1024  # 20MB in bytes
        if len(file_content) > max_size:
            raise ValueError(f"Platform package file is too large. Maximum size is 20MB, got {len(file_content)} bytes")
        
        # Encode to base64
        import_file_b64 = base64.b64encode(file_content).decode('utf-8')
        
        # Prepare request body
        body = {
            "ImportFile": import_file_b64
        }
        
        self.logger.info(f"Importing platform package ({len(file_content)} bytes)")
        response = await self._make_api_request("POST", "Platforms/Import", json=body)
        
        return response
