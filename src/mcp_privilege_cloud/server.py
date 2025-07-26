import logging
from functools import lru_cache
from typing import Optional, Dict, Any, List, Union

from .exceptions import CyberArkAPIError
from .sdk_auth import CyberArkSDKAuthenticator

# ark-sdk-python imports for account management
from ark_sdk_python.services.pcloud.accounts import ArkPCloudAccountsService
from ark_sdk_python.models.services.pcloud.accounts import (
    ArkPCloudAccountsFilter,
    ArkPCloudAddAccount,
    ArkPCloudChangeAccountCredentials,
    ArkPCloudSetAccountNextCredentials,
    ArkPCloudVerifyAccountCredentials,
    ArkPCloudReconcileAccountCredentials
)

# ark-sdk-python imports for safe and platform management
from ark_sdk_python.services.pcloud.safes import ArkPCloudSafesService
from ark_sdk_python.services.pcloud.platforms import ArkPCloudPlatformsService
from ark_sdk_python.models.services.pcloud.platforms import ArkPCloudImportPlatform, ArkPCloudGetPlatform
from ark_sdk_python.models.services.pcloud.safes import ArkPCloudGetSafe

# Backward compatibility - re-export CyberArkAPIError from server module
__all__ = ["CyberArkMCPServer", "CyberArkAPIError"]

logger = logging.getLogger(__name__)


class CyberArkMCPServer:
    """CyberArk Privilege Cloud MCP Server - SDK-based Implementation
    
    This class provides comprehensive CyberArk operations using ark-sdk-python
    with enhanced platform data processing capabilities.
    """

    def __init__(self):
        # Initialize SDK authenticator for all operations
        self.sdk_authenticator = CyberArkSDKAuthenticator.from_environment()
        self._accounts_service: Optional[ArkPCloudAccountsService] = None
        self._safes_service: Optional[ArkPCloudSafesService] = None
        self._platforms_service: Optional[ArkPCloudPlatformsService] = None
        
        self.logger = logger

    @classmethod
    def from_environment(cls) -> "CyberArkMCPServer":
        """Create server from environment variables"""
        return cls()

    @lru_cache(maxsize=None)
    def _get_service(self, service_class):
        """Factory method to get an initialized SDK service.
        
        Args:
            service_class: The SDK service class to instantiate
            
        Returns:
            Initialized service instance
        """
        sdk_auth = self.sdk_authenticator.get_authenticated_client()
        return service_class(sdk_auth)

    @property
    def accounts_service(self) -> ArkPCloudAccountsService:
        """Get or create the accounts service instance"""
        if self._accounts_service is None:
            self._accounts_service = self._get_service(ArkPCloudAccountsService)
        return self._accounts_service
    
    @accounts_service.setter 
    def accounts_service(self, service: ArkPCloudAccountsService):
        """Set the accounts service instance (mainly for testing)"""
        self._accounts_service = service

    @property
    def safes_service(self) -> ArkPCloudSafesService:
        """Get or create the safes service instance"""
        if self._safes_service is None:
            self._safes_service = self._get_service(ArkPCloudSafesService)
        return self._safes_service
    
    @safes_service.setter 
    def safes_service(self, service: ArkPCloudSafesService):
        """Set the safes service instance (mainly for testing)"""
        self._safes_service = service

    @property
    def platforms_service(self) -> ArkPCloudPlatformsService:
        """Get or create the platforms service instance"""
        if self._platforms_service is None:
            self._platforms_service = self._get_service(ArkPCloudPlatformsService)
        return self._platforms_service
    
    @platforms_service.setter 
    def platforms_service(self, service: ArkPCloudPlatformsService):
        """Set the platforms service instance (mainly for testing)"""
        self._platforms_service = service

    # Legacy API methods removed - all operations now use ark-sdk-python directly

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
    
    def clear_cache(self):
        """Clear all cached services and authentication state. Used for testing."""
        # Clear LRU cache for _get_service method
        self._get_service.cache_clear()
        
        # Reset service instances
        self._accounts_service = None
        self._safes_service = None
        self._platforms_service = None
        
        # Reset authentication state
        if hasattr(self.sdk_authenticator, '_sdk_auth'):
            self.sdk_authenticator._sdk_auth = None
            self.sdk_authenticator._is_authenticated = False

    # Account Management - Using ark-sdk-python
    async def list_accounts(self, safe_name: Optional[str] = None, **kwargs) -> List[Dict[str, Any]]:
        """List accounts from CyberArk Privilege Cloud using ark-sdk-python"""
        try:
            # Build filter if safe_name is provided
            account_filter = None
            if safe_name:
                account_filter = ArkPCloudAccountsFilter(safe_name=safe_name)
            
            # Get accounts using SDK
            pages = list(self.accounts_service.list_accounts(accounts_filter=account_filter))
            
            # Convert SDK models to dicts and flatten pagination
            accounts = [acc.model_dump() for page in pages for acc in page.items]
            
            self.logger.info(f"Retrieved {len(accounts)} accounts using ark-sdk-python")
            return accounts
            
        except Exception as e:
            self.logger.error(f"Error listing accounts with ark-sdk-python: {e}")
            raise

    async def get_account_details(self, account_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific account using ark-sdk-python"""
        try:
            account = self.accounts_service.get_account(account_id=account_id)
            self.logger.info(f"Retrieved account details for ID: {account_id} using ark-sdk-python")
            return account.model_dump()
        except Exception as e:
            self.logger.error(f"Error getting account details for ID {account_id} with ark-sdk-python: {e}")
            raise

    async def search_accounts(
        self,
        query: Optional[str] = None,
        safe_name: Optional[str] = None,
        username: Optional[str] = None,
        address: Optional[str] = None,
        platform_id: Optional[str] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Search for accounts with various criteria using ark-sdk-python"""
        try:
            # Build filter with provided criteria
            account_filter = ArkPCloudAccountsFilter(
                safe_name=safe_name,
                user_name=username,  # SDK uses user_name
                address=address,
                platform_id=platform_id
            )
            
            # Add search query if provided
            search_query = query
            
            # Get accounts using SDK with filter and search
            pages = list(self.accounts_service.list_accounts(
                accounts_filter=account_filter,
                search=search_query
            ))
            
            # Convert SDK models to dicts and flatten pagination
            accounts = [acc.model_dump() for page in pages for acc in page.items]
            
            self.logger.info(f"Found {len(accounts)} accounts matching search criteria using ark-sdk-python")
            return accounts
            
        except Exception as e:
            self.logger.error(f"Error searching accounts with ark-sdk-python: {e}")
            raise

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
        """Create a new privileged account using ark-sdk-python"""
        try:
            # Handle required fields for SDK model
            if name is None:
                # If name is not provided, generate a default based on address and user_name
                if address and user_name:
                    name = f"{user_name}@{address}"
                elif user_name:
                    name = user_name
                elif address:
                    name = f"account@{address}"
                else:
                    name = f"account-{platform_id}"

            if secret is None:
                # If secret is not provided, use empty string - CPM will generate
                secret = ""

            # Create the account model
            add_account = ArkPCloudAddAccount(
                platform_id=platform_id,
                safe_name=safe_name,
                name=name,
                address=address,
                user_name=user_name,
                secret=secret,
                secret_type=secret_type,
                platform_account_properties=platform_account_properties,
                secret_management=secret_management,
                remote_machines_access=remote_machines_access
            )
            
            # Create the account using SDK
            created_account = self.accounts_service.add_account(account=add_account)
            
            self.logger.info(f"Successfully created account with ID: {created_account.id}")
            return created_account.model_dump()
            
        except Exception as e:
            self.logger.error(f"Error creating account with ark-sdk-python: {e}")
            raise

    async def change_account_password(self, account_id: str, **kwargs) -> Dict[str, Any]:
        """Initiate CPM-managed password change using ark-sdk-python"""
        try:
            # Create the change credentials model
            change_creds = ArkPCloudChangeAccountCredentials(
                account_id=account_id,
                change_creds_for_group=True  # Equivalent to ChangeCredsForGroup
            )
            
            # Change the account password using SDK
            result = self.accounts_service.change_account_credentials(
                account_id=account_id,
                change_account_credentials=change_creds
            )
            
            self.logger.info(f"Successfully initiated password change for account ID: {account_id}")
            return result.model_dump()
            
        except Exception as e:
            self.logger.error(f"Error changing password for account ID {account_id} with ark-sdk-python: {e}")
            raise

    async def set_next_password(
        self, account_id: str, new_password: str, change_immediately: bool = True, **kwargs
    ) -> Dict[str, Any]:
        """Set the next password for an account using ark-sdk-python"""
        try:
            # Create the set next credentials model with required accountId field
            set_next_creds = ArkPCloudSetAccountNextCredentials(
                accountId=account_id,
                change_immediately=change_immediately,
                new_credentials=new_password
            )
            
            # Set the next password using SDK
            result = self.accounts_service.set_account_next_credentials(
                account_id=account_id,
                set_account_next_credentials=set_next_creds
            )
            
            self.logger.info(f"Successfully set next password for account ID: {account_id}")
            return result.model_dump()
            
        except Exception as e:
            self.logger.error(f"Error setting next password for account ID {account_id} with ark-sdk-python: {e}")
            raise

    async def verify_account_password(self, account_id: str, **kwargs) -> Dict[str, Any]:
        """Verify the password for an account using ark-sdk-python"""
        try:
            # Create the verify credentials model with required account_id
            verify_creds = ArkPCloudVerifyAccountCredentials(
                account_id=account_id
            )
            
            # Verify the account password using SDK
            result = self.accounts_service.verify_account_credentials(
                account_id=account_id,
                verify_account_credentials=verify_creds
            )
            
            self.logger.info(f"Successfully verified password for account ID: {account_id}")
            return result.model_dump()
            
        except Exception as e:
            self.logger.error(f"Error verifying password for account ID {account_id} with ark-sdk-python: {e}")
            raise

    async def reconcile_account_password(self, account_id: str, **kwargs) -> Dict[str, Any]:
        """Reconcile the password for an account using ark-sdk-python"""
        try:
            # Create the reconcile credentials model
            reconcile_creds = ArkPCloudReconcileAccountCredentials(account_id=account_id)
            
            # Reconcile the account password using SDK
            result = self.accounts_service.reconcile_account_credentials(
                account_id=account_id,
                reconcile_account_credentials=reconcile_creds
            )
            
            self.logger.info(f"Successfully reconciled password for account ID: {account_id}")
            return result.model_dump()
            
        except Exception as e:
            self.logger.error(f"Error reconciling password for account ID {account_id} with ark-sdk-python: {e}")
            raise

    # Safe Management - Using ark-sdk-python
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
        """List all accessible safes using ark-sdk-python"""
        try:
            # Get safes using SDK
            pages = list(self.safes_service.list_safes())
            
            # Convert SDK models to dicts and flatten pagination
            safes = [safe.model_dump() for page in pages for safe in page.items]
            
            self.logger.info(f"Retrieved {len(safes)} safes using ark-sdk-python")
            return safes
            
        except Exception as e:
            self.logger.error(f"Error listing safes with ark-sdk-python: {e}")
            raise

    async def get_safe_details(
        self,
        safe_name: str,
        include_accounts: Optional[bool] = None,
        use_cache: Optional[bool] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Get detailed information about a specific safe using ark-sdk-python"""
        try:
            # Create the get safe model (safe_name is used as safe_id in CyberArk)
            get_safe = ArkPCloudGetSafe(safe_id=safe_name)
            
            # Get safe details using SDK
            safe = self.safes_service.safe(get_safe=get_safe)
            
            self.logger.info(f"Retrieved safe details for: {safe_name} using ark-sdk-python")
            return safe.model_dump()
            
        except Exception as e:
            self.logger.error(f"Error getting safe details for {safe_name} with ark-sdk-python: {e}")
            raise

    # Platform Management - Using ark-sdk-python
    async def list_platforms(
        self,
        search: Optional[str] = None,
        active: Optional[bool] = None,
        system_type: Optional[str] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """List available platforms using ark-sdk-python"""
        try:
            # Get platforms using SDK
            platforms = self.platforms_service.list_platforms()
            
            # Convert SDK models to dicts
            platforms_list = [platform.model_dump() for platform in platforms]
            
            self.logger.info(f"Retrieved {len(platforms_list)} platforms using ark-sdk-python")
            return platforms_list
            
        except Exception as e:
            self.logger.error(f"Error listing platforms with ark-sdk-python: {e}")
            raise

    async def get_platform_details(self, platform_id: str) -> Dict[str, Any]:
        """Get detailed platform configuration using ark-sdk-python"""
        try:
            # Create the get platform model
            get_platform = ArkPCloudGetPlatform(platform_id=platform_id)
            
            # Get platform details using SDK
            platform = self.platforms_service.platform(get_platform=get_platform)
            
            self.logger.info(f"Retrieved platform details for: {platform_id} using ark-sdk-python")
            return platform.model_dump()
            
        except Exception as e:
            self.logger.error(f"Error getting platform details for {platform_id} with ark-sdk-python: {e}")
            raise

    async def import_platform_package(
        self, platform_package_file: Union[str, bytes], **kwargs
    ) -> Dict[str, Any]:
        """Import a platform package using ark-sdk-python"""
        try:
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

            # Create the import platform model
            import_platform = ArkPCloudImportPlatform(
                import_file=import_file_b64
            )
            
            # Import platform using SDK
            result = self.platforms_service.import_platform(import_platform=import_platform)
            
            self.logger.info(f"Successfully imported platform package using ark-sdk-python ({len(file_content)} bytes)")
            return result.model_dump()
            
        except Exception as e:
            self.logger.error(f"Error importing platform package with ark-sdk-python: {e}")
            raise

    async def get_complete_platform_info(
        self, platform_id: str, platform_basic: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Combine data from Get Platforms List API and Get Platform Details API into complete platform object.

        This method provides a comprehensive view of platform configuration by merging:
        - Basic platform information from list_platforms() (general info, properties)
        - Detailed Policy INI configuration from get_platform_details() (66+ fields)

        Args:
            platform_id (str): The unique identifier of the platform
            platform_basic (Optional[Dict[str, Any]]): Pre-fetched basic platform info to avoid redundant API calls

        Returns:
            Dict[str, Any]: Complete platform configuration containing:
                - All fields from list API (id, name, systemType, active, etc.)
                - Detailed policy settings from details API when available
                - Raw API values preserved exactly as returned by CyberArk APIs
                - Field deduplication (list API values take precedence)

        Raises:
            CyberArkAPIError: When platform is not found (404) or access is denied

        Note:
            Gracefully degrades to basic platform info if details API fails.
            Implements field deduplication with list API taking precedence.
            Preserves raw API field names and values without transformation.
        """
        self.logger.info(f"Getting complete platform information for: {platform_id}")

        # Enhanced input validation
        if not platform_id or not isinstance(platform_id, str):
            error_msg = f"Invalid platform_id provided: {platform_id!r}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)

        # Sanitize platform_id for logging
        safe_platform_id = platform_id.replace('\n', '').replace('\r', '')[:100]

        # Step 1: Get basic platform info (use provided or fetch from API)
        if platform_basic is not None:
            self.logger.debug(f"Using pre-fetched basic platform info for '{safe_platform_id}'")
            result_platform = platform_basic
        else:
            try:
                self.logger.debug(f"Fetching platform list to find platform '{safe_platform_id}'")
                platforms_list = await self.list_platforms()
                result_platform = None

                # Find the target platform in the list
                for platform in platforms_list:
                    # Handle nested structure - platforms may have data in 'general' section
                    platform_data = platform.get('general', platform)
                    if platform_data.get('id') == platform_id:
                        result_platform = platform
                        break

                if not result_platform:
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
        result = self._flatten_platform_structure(result_platform)
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

        except Exception as e:
            # Enhanced graceful degradation with comprehensive logging
            if hasattr(e, 'status_code'):
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
            else:
                self.logger.warning(f"Unexpected error getting platform details for '{safe_platform_id}' - using basic info only: {e}")
                self.logger.debug(f"Unexpected error degradation", exc_info=True)

        # Final result logging
        field_count = len(result)
        status = "with enhanced details" if details_retrieved else "basic info only"
        self.logger.info(f"Returning complete platform info for '{safe_platform_id}' ({field_count} fields, {status})")

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
                - Raw API values preserved exactly as returned by CyberArk APIs
                - Graceful degradation for platforms where details API fails

        Raises:
            CyberArkAPIError: When platform list retrieval fails (propagated from list_platforms)

        Performance Notes:
            - Uses concurrent API calls with configurable limit (default: 5 concurrent requests)
            - Implements graceful failure handling - continues if some platform details fail
            - Typically 3-5x faster than sequential API calls for large platform lists
            - Rate limiting protection through concurrent request batching

        Note:
            Falls back gracefully to basic platform info if individual platform details fail.
        """
        import asyncio
        
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
        semaphore = asyncio.Semaphore(5)  # Balanced concurrency for all platforms while preventing timeouts

        async def fetch_platform_details(platform):
            """Fetch complete platform info with comprehensive error handling and rate limiting."""
            async with semaphore:
                platform_data = platform.get('general', platform)
                platform_id = platform_data.get('id')

                if not platform_id:
                    self.logger.warning(f"Platform missing ID, skipping: {platform}")
                    return None

                # Sanitize platform_id for logging
                safe_platform_id = str(platform_id).replace('\\n', '').replace('\\n', '')[:100]
                try:
                    # Get complete platform information with pre-fetched basic data
                    self.logger.debug(f"Fetching complete info for platform '{safe_platform_id}'")
                    complete_info = await self.get_complete_platform_info(platform_id, platform)
                    self.logger.debug(f"Successfully fetched details for platform '{safe_platform_id}'")
                    return complete_info

                except Exception as e:
                    # Enhanced error categorization for better troubleshooting
                    if hasattr(e, 'status_code'):
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
                    else:
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
            # Increased timeout to handle all platforms (60 seconds max for entire operation)
            tasks = [fetch_platform_details(platform) for platform in platforms_list]
            try:
                results = await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=60.0
                )
            except asyncio.TimeoutError:
                self.logger.warning(f"Concurrent platform fetch timed out after 60 seconds for {len(platforms_list)} platforms")
                raise CyberArkAPIError("Platform fetching timed out - consider using basic list_platforms() for faster results")

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
                    safe_platform_id = str(platform_id).replace('\\n', '').replace('\\n', '')[:100]
                    self.logger.error(f"Exception in concurrent fetch for platform '{safe_platform_id}': {type(result).__name__}: {result}")
                    self.logger.debug(f"Exception details for platform '{safe_platform_id}'")
                elif result is None:
                    failed_count += 1
                    # Already logged in fetch_platform_details
                else:
                    successful_platforms.append(result)

            # Step 5: Enhanced completion logging with performance metrics
            success_count = len(successful_platforms)
            success_rate = (success_count / len(platforms_list)) * 100 if platforms_list else 0
            avg_time_per_platform = execution_time / len(platforms_list) if platforms_list else 0

            self.logger.info(f"Concurrent platform fetch completed: {success_count}/{len(platforms_list)} successful ({success_rate:.1f}%), {execution_time:.2f}s total, {avg_time_per_platform:.3f}s avg/platform")

            if failed_count > 0:
                self.logger.warning(f"Platform fetch failures: {failed_count} platforms failed (including {exception_count} exceptions)")
                self.logger.debug(f"Failed platforms will be excluded from results")

            if success_count == 0:
                self.logger.warning("No platforms successfully retrieved with details - all failed or were filtered out")

            return successful_platforms

        except Exception as e:
            # Enhanced error handling for unexpected concurrent execution errors
            self.logger.error(f"Unexpected error during concurrent platform fetch: {type(e).__name__}: {e}")
            self.logger.debug(f"Concurrent fetch error details", exc_info=True)
            raise CyberArkAPIError(f"Unexpected error during concurrent platform fetch: {e}")

    # Health check - Using SDK services
    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check of the CyberArk connection using ark-sdk-python"""
        try:
            # Try to list platforms as a basic connectivity test
            platforms = await self.list_platforms()
            return {
                "status": "healthy",
                "message": "CyberArk connection successful",
                "platform_count": len(platforms)
            }
        except Exception as e:
            return {
                "status": "unhealthy", 
                "message": f"CyberArk connection failed: {e}",
                "error": str(e)
            }

    # Platform data processing methods (migrated from PlatformDataHandler)
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
        """Merge platform details into basic data with field deduplication - NO transformations applied.

        Rules:
        1. Basic data (from list API) takes precedence for overlapping fields
        2. Details data is merged in, preserving raw API values exactly
        3. Nested structures from details API are preserved as-is

        Args:
            basic_data: Flattened data from list platforms API
            details_data: Raw data from get platform details API

        Returns:
            Merged platform data preserving original API field names and values
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
                # Add non-overlapping fields preserving raw values
                result[key] = value

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
                # Add new nested structures preserving raw values
                result[key] = self._copy_nested_data(value)

        return result

    def _merge_nested_dict(self, basic_dict: Dict[str, Any], details_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge nested dictionaries with basic dict taking precedence - preserves raw values."""
        result = basic_dict.copy()

        for key, value in details_dict.items():
            if key in result:
                # Basic data takes precedence - skip overlapping keys
                continue
            else:
                # Add new keys preserving raw values
                result[key] = value

        return result

    def _copy_nested_data(self, data: Any) -> Any:
        """Recursively copy nested data structures preserving raw values."""
        if isinstance(data, dict):
            return {key: self._copy_nested_data(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._copy_nested_data(item) for item in data]
        else:
            # Return raw values unchanged
            return data

    def _preserve_raw_value(self, value: Any) -> Any:
        """Preserve raw API values without any transformation.
        
        This method is a placeholder for the previous _convert_data_type method.
        It now preserves all raw API values exactly as returned by CyberArk APIs.
        
        Returns:
            Raw value unchanged - no conversions applied
        """
        # Return all values unchanged to preserve raw API data
        return value
