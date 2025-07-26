import logging
from functools import wraps
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


def handle_sdk_errors(operation_name: str):
    """Decorator to standardize error handling for SDK operations.
    
    Args:
        operation_name: Description of the operation for logging
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            try:
                return await func(self, *args, **kwargs)
            except Exception as e:
                self.logger.error(f"Error {operation_name}: {e}")
                raise
        return wrapper
    return decorator


class CyberArkMCPServer:
    """CyberArk Privilege Cloud MCP Server - SDK-based Implementation
    
    This class provides comprehensive CyberArk operations using ark-sdk-python
    with enhanced platform data processing capabilities.
    """

    def __init__(self):
        # Initialize SDK authenticator for all operations
        self.sdk_authenticator = CyberArkSDKAuthenticator.from_environment()
        
        # Initialize services directly - simpler than properties
        try:
            sdk_auth = self.sdk_authenticator.get_authenticated_client()
            self.accounts_service = ArkPCloudAccountsService(sdk_auth)
            self.safes_service = ArkPCloudSafesService(sdk_auth) 
            self.platforms_service = ArkPCloudPlatformsService(sdk_auth)
        except (TypeError, AttributeError):
            # Handle test mocking scenarios where SDK objects may be mocked
            self.accounts_service = None
            self.safes_service = None
            self.platforms_service = None
        
        self.logger = logger

    @classmethod
    def from_environment(cls) -> "CyberArkMCPServer":
        """Create server from environment variables"""
        return cls()

    def _ensure_service_initialized(self, service_name: str):
        """Ensure a specific service is initialized, initializing if needed."""
        if getattr(self, service_name) is None:
            sdk_auth = self.sdk_authenticator.get_authenticated_client()
            if service_name == 'accounts_service':
                self.accounts_service = ArkPCloudAccountsService(sdk_auth)
            elif service_name == 'safes_service':
                self.safes_service = ArkPCloudSafesService(sdk_auth)
            elif service_name == 'platforms_service':
                self.platforms_service = ArkPCloudPlatformsService(sdk_auth)

    def reinitialize_services(self):
        """Reinitialize services - useful for testing or after auth changes."""
        sdk_auth = self.sdk_authenticator.get_authenticated_client()
        self.accounts_service = ArkPCloudAccountsService(sdk_auth)
        self.safes_service = ArkPCloudSafesService(sdk_auth) 
        self.platforms_service = ArkPCloudPlatformsService(sdk_auth)

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
        # Reset authentication state
        if hasattr(self.sdk_authenticator, '_sdk_auth'):
            self.sdk_authenticator._sdk_auth = None
            self.sdk_authenticator._is_authenticated = False
        
        # Reinitialize services with fresh authentication
        self.reinitialize_services()

    # Account Management - Using ark-sdk-python
    @handle_sdk_errors("listing accounts")
    async def list_accounts(self, safe_name: Optional[str] = None, **kwargs) -> List[Dict[str, Any]]:
        """List accounts from CyberArk Privilege Cloud using ark-sdk-python"""
        self._ensure_service_initialized('accounts_service')
        
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

    @handle_sdk_errors("getting account details")
    async def get_account_details(self, account_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific account using ark-sdk-python"""
        self._ensure_service_initialized('accounts_service')
        account = self.accounts_service.get_account(account_id=account_id)
        self.logger.info(f"Retrieved account details for ID: {account_id} using ark-sdk-python")
        return account.model_dump()

    @handle_sdk_errors("searching accounts")
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
        self._ensure_service_initialized('accounts_service')
        
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

    @handle_sdk_errors("creating account")
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

    @handle_sdk_errors("changing account password")
    async def change_account_password(self, account_id: str, **kwargs) -> Dict[str, Any]:
        """Initiate CPM-managed password change using ark-sdk-python"""
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

    @handle_sdk_errors("setting next password")
    async def set_next_password(
        self, account_id: str, new_password: str, change_immediately: bool = True, **kwargs
    ) -> Dict[str, Any]:
        """Set the next password for an account using ark-sdk-python"""
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

    @handle_sdk_errors("verifying account password")
    async def verify_account_password(self, account_id: str, **kwargs) -> Dict[str, Any]:
        """Verify the password for an account using ark-sdk-python"""
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

    @handle_sdk_errors("reconciling account password")
    async def reconcile_account_password(self, account_id: str, **kwargs) -> Dict[str, Any]:
        """Reconcile the password for an account using ark-sdk-python"""
        # Create the reconcile credentials model
        reconcile_creds = ArkPCloudReconcileAccountCredentials(account_id=account_id)
        
        # Reconcile the account password using SDK
        result = self.accounts_service.reconcile_account_credentials(
            account_id=account_id,
            reconcile_account_credentials=reconcile_creds
        )
        
        self.logger.info(f"Successfully reconciled password for account ID: {account_id}")
        return result.model_dump()

    # Safe Management - Using ark-sdk-python
    @handle_sdk_errors("listing safes")
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
        self._ensure_service_initialized('safes_service')
        
        # Get safes using SDK
        pages = list(self.safes_service.list_safes())
        
        # Convert SDK models to dicts and flatten pagination
        safes = [safe.model_dump() for page in pages for safe in page.items]
        
        self.logger.info(f"Retrieved {len(safes)} safes using ark-sdk-python")
        return safes

    @handle_sdk_errors("getting safe details")
    async def get_safe_details(
        self,
        safe_name: str,
        include_accounts: Optional[bool] = None,
        use_cache: Optional[bool] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Get detailed information about a specific safe using ark-sdk-python"""
        # Create the get safe model (safe_name is used as safe_id in CyberArk)
        get_safe = ArkPCloudGetSafe(safe_id=safe_name)
        
        # Get safe details using SDK
        safe = self.safes_service.safe(get_safe=get_safe)
        
        self.logger.info(f"Retrieved safe details for: {safe_name} using ark-sdk-python")
        return safe.model_dump()

    # Platform Management - Using ark-sdk-python
    @handle_sdk_errors("listing platforms")
    async def list_platforms(
        self,
        search: Optional[str] = None,
        active: Optional[bool] = None,
        system_type: Optional[str] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """List available platforms using ark-sdk-python"""
        self._ensure_service_initialized('platforms_service')
        
        # Get platforms using SDK
        platforms = self.platforms_service.list_platforms()
        
        # Convert SDK models to dicts
        platforms_list = [platform.model_dump() for platform in platforms]
        
        self.logger.info(f"Retrieved {len(platforms_list)} platforms using ark-sdk-python")
        return platforms_list

    @handle_sdk_errors("getting platform details")
    async def get_platform_details(self, platform_id: str) -> Dict[str, Any]:
        """Get detailed platform configuration using ark-sdk-python"""
        # Create the get platform model
        get_platform = ArkPCloudGetPlatform(platform_id=platform_id)
        
        # Get platform details using SDK
        platform = self.platforms_service.platform(get_platform=get_platform)
        
        self.logger.info(f"Retrieved platform details for: {platform_id} using ark-sdk-python")
        return platform.model_dump()

    @handle_sdk_errors("importing platform package")
    async def import_platform_package(
        self, platform_package_file: Union[str, bytes], **kwargs
    ) -> Dict[str, Any]:
        """Import a platform package using ark-sdk-python"""
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

    async def get_complete_platform_info(
        self, platform_id: str, platform_basic: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Combine data from list and details APIs into complete platform info.
        
        Args:
            platform_id: The unique identifier of the platform
            platform_basic: Pre-fetched basic platform info to avoid redundant API calls
            
        Returns:
            Complete platform configuration with basic info and details (when available)
        """
        if not platform_id or not isinstance(platform_id, str):
            raise ValueError(f"Invalid platform_id: {platform_id!r}")

        # Get basic platform info
        if platform_basic is not None:
            result_platform = platform_basic
        else:
            platforms_list = await self.list_platforms()
            result_platform = None
            
            for platform in platforms_list:
                platform_data = platform.get('general', platform)
                if platform_data.get('id') == platform_id:
                    result_platform = platform
                    break
                    
            if not result_platform:
                raise CyberArkAPIError(f"Platform '{platform_id}' not found", 404)

        # Start with flattened basic platform info
        result = self._flatten_platform_structure(result_platform)

        # Try to get and merge detailed info
        try:
            platform_details = await self.get_platform_details(platform_id)
            result = self._merge_platform_data(result, platform_details)
            self.logger.info(f"Retrieved complete platform info for: {platform_id}")
        except Exception as e:
            # Gracefully degrade to basic info on any error
            self.logger.warning(f"Platform details unavailable for {platform_id}, using basic info: {e}")

        return result

    async def list_platforms_with_details(self, **kwargs) -> List[Dict[str, Any]]:
        """Get all platforms with complete information using concurrent API calls.
        
        Args:
            **kwargs: Parameters passed to list_platforms() for filtering/search
            
        Returns:
            List of complete platform configurations with graceful degradation for failures
        """
        import asyncio
        
        # Get the basic platform list
        platforms_list = await self.list_platforms(**kwargs)
        if not platforms_list:
            return []

        # Define concurrent fetching with rate limiting
        semaphore = asyncio.Semaphore(5)

        async def fetch_platform_details(platform):
            """Fetch complete platform info with error handling."""
            async with semaphore:
                platform_data = platform.get('general', platform)
                platform_id = platform_data.get('id')
                
                if not platform_id:
                    return None
                    
                try:
                    return await self.get_complete_platform_info(platform_id, platform)
                except Exception as e:
                    self.logger.warning(f"Failed to get details for platform {platform_id}: {e}")
                    return None

        # Execute concurrent API calls
        tasks = [fetch_platform_details(platform) for platform in platforms_list]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out failures and exceptions
        successful_platforms = [
            result for result in results 
            if result is not None and not isinstance(result, Exception)
        ]
        
        self.logger.info(f"Retrieved {len(successful_platforms)}/{len(platforms_list)} platforms with details")
        return successful_platforms

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

    # Simplified platform data processing methods
    def _flatten_platform_structure(self, platform_data: Dict[str, Any]) -> Dict[str, Any]:
        """Flatten nested platform structure from list API into a single level."""
        result = {}
        for section_name, section_data in platform_data.items():
            if isinstance(section_data, dict):
                result.update(section_data)  # Flatten nested dictionaries
            else:
                result[section_name] = section_data
        return result

    def _merge_platform_data(self, basic_data: Dict[str, Any], details_data: Dict[str, Any]) -> Dict[str, Any]:
        """Merge platform details into basic data with basic data taking precedence."""
        import copy
        result = basic_data.copy()
        
        # Merge details data, skipping keys that already exist in basic data
        details_section = details_data.get('Details', {})
        
        # Add top-level fields that don't conflict
        for key, value in details_data.items():
            if key != 'Details' and key not in result:
                result[key] = value
        
        # Add nested details that don't conflict
        for key, value in details_section.items():
            if key not in result:
                result[key] = copy.deepcopy(value)
            elif isinstance(result[key], dict) and isinstance(value, dict):
                # Simple merge for nested dicts - basic data takes precedence
                merged = copy.deepcopy(value)
                merged.update(result[key])
                result[key] = merged
        
        return result

