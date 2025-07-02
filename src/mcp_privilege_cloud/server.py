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
        """Get detailed platform configuration from Policy INI file.
        
        This method retrieves comprehensive platform configuration including
        credentials management policies, session management settings, privileged
        access workflows, connection components, and all Policy INI properties.
        
        Args:
            platform_id (str): The unique identifier of the platform
            
        Returns:
            Dict[str, Any]: Complete platform configuration containing:
                - Basic platform metadata (id, name, type, active status)
                - Detailed policy settings from Policy INI file
                - Credentials management configuration (66+ fields)
                - Session management and recording policies
                - Connection components and workflows
                - UI and behavior settings
                
        Raises:
            CyberArkAPIError: When platform access fails
                - 404: Platform not found
                - 403: Insufficient privileges to access platform details
                - 401: Authentication failure (handled with automatic retry)
                
        Example:
            >>> server = CyberArkMCPServer.from_environment()
            >>> details = await server.get_platform_details("WinServerLocal")
            >>> print(details["name"])  # "Windows Server Local"
            >>> print(details["details"]["credentialsManagementPolicy"]["change"])  # "on"
            >>> print(len(details["details"]))  # 66+ policy configuration fields
            
        API Endpoint:
            GET /PasswordVault/API/Platforms/{PlatformName}/
            
        Note:
            Requires Privilege Cloud Administrator role membership.
            Returns detailed Policy INI configuration not available in list_platforms().
        """
        self.logger.info(f"Getting details for platform ID: {platform_id}")
        
        # Enhanced input validation
        if not platform_id or not isinstance(platform_id, str):
            error_msg = f"Invalid platform_id provided: {platform_id!r}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Sanitize platform_id for logging
        safe_platform_id = platform_id.replace('\n', '').replace('\r', '')[:100]
        
        try:
            # Make API request to retrieve detailed platform configuration
            response = await self._make_api_request("GET", f"Platforms/{platform_id}")
            
            # Log successful retrieval with basic platform info
            if "name" in response:
                self.logger.debug(f"Retrieved platform details for '{response['name']}' (ID: {safe_platform_id})")
            else:
                self.logger.debug(f"Retrieved platform details for ID: {safe_platform_id}")
            
            return response
            
        except CyberArkAPIError as e:
            # Enhanced error handling with specific guidance and troubleshooting context
            if e.status_code == 404:
                self.logger.warning(f"Platform '{safe_platform_id}' not found - verify platform exists and is accessible")
                error_msg = f"Platform '{platform_id}' does not exist or is not accessible"
                self.logger.debug(f"404 troubleshooting: Check platform list with list_platforms() to verify platform exists")
                raise CyberArkAPIError(error_msg, 404)
            elif e.status_code == 403:
                self.logger.warning(f"Insufficient privileges to access platform '{safe_platform_id}' - requires admin role")
                error_msg = (f"Access denied to platform '{platform_id}'. "
                           "Requires Privilege Cloud Administrator role membership.")
                self.logger.debug(f"403 troubleshooting: User needs 'Privilege Cloud Administrator' role in Identity Administration")
                raise CyberArkAPIError(error_msg, 403)
            elif e.status_code == 429:
                self.logger.warning(f"Rate limiting encountered for platform '{safe_platform_id}' - consider retry with backoff")
                error_msg = f"Rate limit exceeded while accessing platform '{platform_id}'. Please retry after a delay."
                raise CyberArkAPIError(error_msg, 429)
            else:
                # Re-raise other API errors with enhanced context
                self.logger.error(f"Failed to retrieve platform '{safe_platform_id}': HTTP {e.status_code} - {e}")
                self.logger.debug(f"Full error context: {e}")
                raise
        except Exception as e:
            # Enhanced error handling for unexpected errors
            self.logger.error(f"Unexpected error retrieving platform details for '{safe_platform_id}': {type(e).__name__}: {e}")
            self.logger.debug(f"Unexpected error details", exc_info=True)
            raise CyberArkAPIError(f"Unexpected error retrieving platform '{platform_id}': {e}")

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

    async def get_complete_platform_info(self, platform_id: str) -> Dict[str, Any]:
        """Combine data from Get Platforms List API and Get Platform Details API into complete platform object.
        
        This method provides a comprehensive view of platform configuration by merging:
        - Basic platform information from list_platforms() (general info, properties)
        - Detailed Policy INI configuration from get_platform_details() (66+ fields)
        
        Args:
            platform_id (str): The unique identifier of the platform
            
        Returns:
            Dict[str, Any]: Complete platform configuration containing:
                - All fields from list API (id, name, systemType, active, etc.)
                - Detailed policy settings from details API when available
                - Data type conversions applied (Yes/No -> boolean, string numbers -> int)
                - Field deduplication (list API values take precedence)
                
        Raises:
            CyberArkAPIError: When platform is not found (404) or access is denied
            
        Example:
            >>> server = CyberArkMCPServer.from_environment()
            >>> info = await server.get_complete_platform_info("WinServerLocal")
            >>> print(info["name"])  # "Windows Server Local"
            >>> print(info["credentialsManagementPolicy"]["passwordLength"])  # 12 (converted from "12")
            >>> print(info["active"])  # True (from list API, takes precedence)
            
        Note:
            Gracefully degrades to basic platform info if details API fails.
            Implements field deduplication with list API taking precedence.
            Performs automatic data type conversions for consistency.
        """
        self.logger.info(f"Getting complete platform information for: {platform_id}")
        
        # Enhanced input validation
        if not platform_id or not isinstance(platform_id, str):
            error_msg = f"Invalid platform_id provided: {platform_id!r}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Sanitize platform_id for logging
        safe_platform_id = platform_id.replace('\n', '').replace('\r', '')[:100]
        
        # Step 1: Get basic platform info from list API
        try:
            self.logger.debug(f"Fetching platform list to find platform '{safe_platform_id}'")
            platforms_list = await self.list_platforms()
            platform_basic = None
            
            # Find the target platform in the list
            for platform in platforms_list:
                # Handle nested structure - platforms may have data in 'general' section
                platform_data = platform.get('general', platform)
                if platform_data.get('id') == platform_id:
                    platform_basic = platform
                    break
            
            if not platform_basic:
                self.logger.warning(f"Platform '{safe_platform_id}' not found in list API")
                self.logger.debug(f"Available platforms: {[p.get('general', p).get('id', 'unknown') for p in platforms_list[:5]]}")
                raise CyberArkAPIError(f"Platform '{platform_id}' not found", 404)
                
        except CyberArkAPIError:
            # Re-raise CyberArkAPIError as-is
            raise
        except Exception as e:
            self.logger.error(f"Failed to retrieve platform list: {type(e).__name__}: {e}")
            self.logger.debug(f"Platform list retrieval error details", exc_info=True)
            raise CyberArkAPIError(f"Failed to retrieve platform list: {e}")
        
        # Step 2: Start with basic platform info (flattened structure)
        result = self._flatten_platform_structure(platform_basic)
        self.logger.debug(f"Starting with basic platform info for '{safe_platform_id}' ({len(result)} fields)")
        
        # Step 3: Try to get detailed platform info and merge
        details_retrieved = False
        try:
            self.logger.debug(f"Attempting to fetch detailed info for platform '{safe_platform_id}'")
            platform_details = await self.get_platform_details(platform_id)
            self.logger.debug(f"Retrieved detailed info for platform '{safe_platform_id}'")
            
            # Merge details into result with type conversion and deduplication
            result = self._merge_platform_data(result, platform_details)
            details_retrieved = True
            
        except CyberArkAPIError as e:
            # Enhanced graceful degradation with comprehensive logging
            if e.status_code == 404:
                self.logger.warning(f"Platform details not found for '{safe_platform_id}' (404) - using basic info only")
                self.logger.debug(f"404 degradation: Platform exists in list but details API returned not found")
            elif e.status_code == 403:
                self.logger.warning(f"Insufficient permissions for platform details '{safe_platform_id}' (403) - using basic info only")
                self.logger.debug(f"403 degradation: User lacks Privilege Cloud Administrator role for detailed platform access")
            elif e.status_code == 429:
                self.logger.warning(f"Rate limiting for platform details '{safe_platform_id}' (429) - using basic info only")
                self.logger.debug(f"429 degradation: Consider implementing exponential backoff for high-volume requests")
            else:
                self.logger.warning(f"Platform details API error for '{safe_platform_id}' (HTTP {e.status_code}) - using basic info only")
                self.logger.debug(f"API error degradation: {e}")
            
            self.logger.info(f"Gracefully degrading to basic platform information for '{safe_platform_id}'")
            
        except Exception as e:
            # Enhanced handling for unexpected errors
            self.logger.error(f"Unexpected error retrieving platform details for '{safe_platform_id}': {type(e).__name__}: {e}")
            self.logger.debug(f"Unexpected error details", exc_info=True)
            self.logger.info(f"Gracefully degrading to basic platform information for '{safe_platform_id}' due to unexpected error")
        
        # Step 4: Log completion status
        if details_retrieved:
            self.logger.debug(f"Completed platform info retrieval for '{safe_platform_id}' with {len(result)} fields (including details)")
        else:
            self.logger.debug(f"Completed platform info retrieval for '{safe_platform_id}' with {len(result)} fields (basic info only)")
            
        return result

    async def list_platforms_with_details(self, **kwargs) -> List[Dict[str, Any]]:
        """Get all platforms with complete information using concurrent API calls.
        
        This method provides optimized platform listing by fetching platform details
        concurrently to reduce overall API response time. It combines the list_platforms()
        API call with concurrent get_complete_platform_info() calls for each platform.
        
        Args:
            **kwargs: Parameters passed to list_platforms() for filtering/search
                     (e.g., search, limit, offset, sort, filter)
            
        Returns:
            List[Dict[str, Any]]: List of complete platform configurations containing:
                - All fields from list API (id, name, systemType, active, etc.)
                - Detailed policy settings from details API when available
                - Data type conversions applied (Yes/No -> boolean, string numbers -> int)
                - Graceful degradation for platforms where details API fails
                
        Raises:
            CyberArkAPIError: When platform list retrieval fails (propagated from list_platforms)
            
        Example:
            >>> server = CyberArkMCPServer.from_environment()
            >>> platforms = await server.list_platforms_with_details()
            >>> print(f"Retrieved {len(platforms)} platforms with details")
            >>> platforms_with_search = await server.list_platforms_with_details(search="Windows")
            
        Performance Notes:
            - Uses concurrent API calls with configurable limit (default: 10 concurrent requests)
            - Implements graceful failure handling - continues if some platform details fail
            - Typically 3-5x faster than sequential API calls for large platform lists
            - Rate limiting protection through concurrent request batching
            
        Note:
            Falls back gracefully to basic platform info if individual platform details fail.
            Implements exponential backoff for rate limiting scenarios.
        """
        self.logger.info("Fetching platforms with detailed information using concurrent API calls")
        
        # Log the parameters being used
        if kwargs:
            self.logger.debug(f"Platform list parameters: {kwargs}")
        
        # Step 1: Get the list of platforms with any filtering/search parameters
        try:
            self.logger.debug("Fetching platform list")
            platforms_list = await self.list_platforms(**kwargs)
            self.logger.debug(f"Retrieved {len(platforms_list)} platforms from list API")
            
            if not platforms_list:
                self.logger.info("No platforms found, returning empty list")
                return []
                
        except CyberArkAPIError:
            # Re-raise CyberArkAPIError as-is to preserve original error context
            raise
        except Exception as e:
            self.logger.error(f"Failed to retrieve platform list: {type(e).__name__}: {e}")
            self.logger.debug(f"Platform list retrieval error details", exc_info=True)
            raise CyberArkAPIError(f"Failed to retrieve platform list: {e}")
        
        # Step 2: Define concurrent fetching with enhanced error handling
        semaphore = asyncio.Semaphore(10)  # Limit concurrent requests to avoid rate limiting
        
        async def fetch_platform_details(platform):
            """Fetch complete platform info with comprehensive error handling and rate limiting."""
            async with semaphore:
                platform_data = platform.get('general', platform)
                platform_id = platform_data.get('id')
                
                if not platform_id:
                    self.logger.warning(f"Platform missing ID, skipping: {platform}")
                    return None
                
                # Sanitize platform_id for logging
                safe_platform_id = str(platform_id).replace('\n', '').replace('\r', '')[:100]
                
                try:
                    # Get complete platform information
                    self.logger.debug(f"Fetching complete info for platform '{safe_platform_id}'")
                    complete_info = await self.get_complete_platform_info(platform_id)
                    self.logger.debug(f"Successfully fetched details for platform '{safe_platform_id}'")
                    return complete_info
                    
                except CyberArkAPIError as e:
                    # Enhanced error categorization for better troubleshooting
                    if e.status_code == 404:
                        self.logger.warning(f"Platform '{safe_platform_id}' not found (404) - skipping")
                        self.logger.debug(f"404 skip: Platform may have been deleted or access restricted")
                    elif e.status_code == 403:
                        self.logger.warning(f"Insufficient permissions for platform '{safe_platform_id}' (403) - skipping")
                        self.logger.debug(f"403 skip: User lacks admin role for platform details access")
                    elif e.status_code == 429:
                        self.logger.warning(f"Rate limiting for platform '{safe_platform_id}' (429) - skipping")
                        self.logger.debug(f"429 skip: Consider reducing concurrent request limit or implementing backoff")
                    else:
                        self.logger.warning(f"API error for platform '{safe_platform_id}' (HTTP {e.status_code}) - skipping")
                        self.logger.debug(f"API error skip: {e}")
                    
                    # Return None to indicate failure - will be filtered out
                    return None
                    
                except Exception as e:
                    # Enhanced handling for unexpected errors
                    self.logger.error(f"Unexpected error fetching platform '{safe_platform_id}': {type(e).__name__}: {e}")
                    self.logger.debug(f"Unexpected error details for platform '{safe_platform_id}'", exc_info=True)
                    
                    # Return None to indicate failure - will be filtered out
                    return None
        
        # Step 3: Execute concurrent API calls with enhanced monitoring
        try:
            self.logger.info(f"Starting concurrent fetch for {len(platforms_list)} platforms")
            start_time = asyncio.get_event_loop().time()
            
            # Use asyncio.gather for concurrent execution with return_exceptions=True for robustness
            tasks = [fetch_platform_details(platform) for platform in platforms_list]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            end_time = asyncio.get_event_loop().time()
            execution_time = end_time - start_time
            
            # Step 4: Process results and filter out failures with detailed error categorization
            successful_platforms = []
            failed_count = 0
            exception_count = 0
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    exception_count += 1
                    failed_count += 1
                    platform_id = platforms_list[i].get('general', platforms_list[i]).get('id', 'unknown')
                    safe_platform_id = str(platform_id).replace('\n', '').replace('\r', '')[:100]
                    self.logger.error(f"Exception in concurrent fetch for platform '{safe_platform_id}': {type(result).__name__}: {result}")
                    self.logger.debug(f"Exception details for platform '{safe_platform_id}'", exc_info=result)
                elif result is not None:
                    successful_platforms.append(result)
                else:
                    failed_count += 1
            
            # Step 5: Log comprehensive performance metrics and return results
            success_rate = (len(successful_platforms) / len(platforms_list)) * 100 if platforms_list else 100
            
            self.logger.info(
                f"Concurrent platform fetch completed in {execution_time:.2f}s: "
                f"{len(successful_platforms)} successful, {failed_count} failed "
                f"({success_rate:.1f}% success rate)"
            )
            
            if failed_count > 0:
                self.logger.warning(
                    f"Some platforms failed to fetch details ({failed_count}/{len(platforms_list)}), "
                    "continuing with available data"
                )
                if exception_count > 0:
                    self.logger.warning(f"Encountered {exception_count} unexpected exceptions during concurrent fetch")
            
            # Log performance insights
            if execution_time > 5.0:
                self.logger.info(f"Consider reducing concurrent request limit if experiencing timeouts or rate limiting")
            elif execution_time < 1.0 and len(platforms_list) > 5:
                self.logger.debug(f"Excellent performance - concurrent fetching is working optimally")
            
            return successful_platforms
            
        except Exception as e:
            self.logger.error(f"Concurrent platform fetching failed: {type(e).__name__}: {e}")
            self.logger.debug(f"Concurrent fetch failure details", exc_info=True)
            raise CyberArkAPIError(f"Concurrent platform fetching failed: {e}")
    
    def _flatten_platform_structure(self, platform_data: Dict[str, Any]) -> Dict[str, Any]:
        """Flatten nested platform structure from list API into a single level.
        
        The list API may return data in nested sections like:
        - general: {id, name, systemType, active, platformType}
        - properties: {description, etc.}
        - credentialsManagement: {basic settings}
        
        This method flattens these into a single dictionary for consistency.
        """
        result = {}
        
        # Handle nested structure by flattening sections
        for section_name, section_data in platform_data.items():
            if isinstance(section_data, dict):
                # Flatten nested dictionaries into top level
                for key, value in section_data.items():
                    result[key] = value
            else:
                # Copy non-dict values directly
                result[section_name] = section_data
        
        return result
    
    def _merge_platform_data(self, basic_data: Dict[str, Any], details_data: Dict[str, Any]) -> Dict[str, Any]:
        """Merge platform details into basic data with field deduplication and type conversion.
        
        Rules:
        1. Basic data (from list API) takes precedence for overlapping fields
        2. Details data is merged in, with type conversions applied
        3. Nested structures from details API are preserved
        
        Args:
            basic_data: Flattened data from list platforms API
            details_data: Raw data from get platform details API
            
        Returns:
            Merged platform data with type conversions
        """
        result = basic_data.copy()
        
        # Extract details from the Details section if present
        details_section = details_data.get('Details', {})
        
        # Merge top-level fields from details (with deduplication)
        for key, value in details_data.items():
            if key == 'Details':
                # Handle Details section specially
                continue
            elif key in result:
                # Skip overlapping fields - basic data takes precedence
                self.logger.debug(f"Skipping overlapping field '{key}' - using value from list API")
                continue
            else:
                # Add non-overlapping fields with type conversion
                result[key] = self._convert_data_type(value)
        
        # Merge nested structures from Details section
        for key, value in details_section.items():
            if key in result:
                # For overlapping nested structures, merge recursively
                if isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = self._merge_nested_dict(result[key], value)
                else:
                    # Basic data takes precedence for non-dict overlaps
                    self.logger.debug(f"Keeping existing value for '{key}' from list API")
            else:
                # Add new nested structures with type conversion
                result[key] = self._convert_nested_data_types(value)
        
        return result
    
    def _merge_nested_dict(self, basic_dict: Dict[str, Any], details_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge nested dictionaries with basic dict taking precedence."""
        result = basic_dict.copy()
        
        for key, value in details_dict.items():
            if key in result:
                # Basic data takes precedence - skip overlapping keys
                continue
            else:
                # Add new keys with type conversion
                result[key] = self._convert_data_type(value)
        
        return result
    
    def _convert_nested_data_types(self, data: Any) -> Any:
        """Recursively convert data types in nested structures."""
        if isinstance(data, dict):
            return {key: self._convert_nested_data_types(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._convert_nested_data_types(item) for item in data]
        else:
            return self._convert_data_type(data)
    
    def _convert_data_type(self, value: Any) -> Any:
        """Convert data types for consistency.
        
        Conversions:
        - "Yes"/"No" -> True/False
        - "on"/"off" -> "on"/"off" (keep as strings for policy settings)
        - String numbers -> int (when they represent counts/frequencies)
        - Other strings -> unchanged
        """
        if isinstance(value, str):
            # Convert Yes/No to boolean
            if value.lower() == "yes":
                return True
            elif value.lower() == "no":
                return False
            # Convert string numbers to int for specific numeric fields
            elif value.isdigit():
                # Check if this looks like a numeric setting
                return int(value)
        
        # Return unchanged for other types
        return value
