import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import wraps
from typing import Optional, Dict, Any, List, Union

# Import BaseModel for Pydantic model type annotations
from pydantic import BaseModel

from .exceptions import CyberArkAPIError, is_sdk_exception, convert_sdk_exception
from .sdk_auth import CyberArkSDKAuthenticator

# ark-sdk-python imports for account management
from ark_sdk_python.services.pcloud.accounts import ArkPCloudAccountsService
from ark_sdk_python.models.services.pcloud.accounts import (
    ArkPCloudAccountsFilter,
    ArkPCloudAddAccount,
    ArkPCloudChangeAccountCredentials,
    ArkPCloudSetAccountNextCredentials,
    ArkPCloudVerifyAccountCredentials,
    ArkPCloudReconcileAccountCredentials,
    ArkPCloudUpdateAccount,
    ArkPCloudDeleteAccount
)

# Try to import response model types - these may be generic Pydantic models
try:
    # These are the likely response model names based on SDK patterns
    from ark_sdk_python.models.services.pcloud.accounts import (
        ArkPCloudAccount,  # Individual account response
        ArkPCloudAccountsList,  # List accounts response
    )
except ImportError:
    # Fallback to BaseModel if specific response types aren't available
    ArkPCloudAccount = BaseModel
    ArkPCloudAccountsList = BaseModel

# Import common response types for proper type annotations
try:
    from ark_sdk_python.models.services.pcloud.safes import (
        ArkPCloudSafe,
        ArkPCloudSafeMember,
    )
except ImportError:
    ArkPCloudSafe = BaseModel
    ArkPCloudSafeMember = BaseModel

try:
    from ark_sdk_python.models.services.pcloud.platforms import (
        ArkPCloudPlatform,
        ArkPCloudPlatformStatistics,
        ArkPCloudTargetPlatformStatistics,
    )
except ImportError:
    ArkPCloudPlatform = BaseModel
    ArkPCloudPlatformStatistics = BaseModel
    ArkPCloudTargetPlatformStatistics = BaseModel

try:
    from ark_sdk_python.models.services.pcloud.applications import (
        ArkPCloudApplication,
        ArkPCloudApplicationAuthMethod,
        ArkPCloudApplicationStatistics,
    )
except ImportError:
    ArkPCloudApplication = BaseModel
    ArkPCloudApplicationAuthMethod = BaseModel
    ArkPCloudApplicationStatistics = BaseModel

try:
    from ark_sdk_python.models.services.sm import (
        ArkSMSession,
        ArkSMSessionActivity,
        ArkSMSessionStatistics,
    )
except ImportError:
    ArkSMSession = BaseModel
    ArkSMSessionActivity = BaseModel
    ArkSMSessionStatistics = BaseModel

# ark-sdk-python imports for safe, platform, and applications management
from ark_sdk_python.services.pcloud.safes import ArkPCloudSafesService
from ark_sdk_python.services.pcloud.platforms import ArkPCloudPlatformsService
from ark_sdk_python.services.pcloud.applications import ArkPCloudApplicationsService

# ark-sdk-python imports for session monitoring
from ark_sdk_python.services.sm import ArkSMService
from ark_sdk_python.models.services.sm import (
    ArkSMSessionsFilter,
    ArkSMGetSession,
    ArkSMGetSessionActivities
)
from ark_sdk_python.models.services.pcloud.platforms import (
    ArkPCloudImportPlatform, 
    ArkPCloudGetPlatform,
    ArkPCloudExportPlatform,
    ArkPCloudDuplicateTargetPlatform,
    ArkPCloudActivateTargetPlatform,
    ArkPCloudDeactivateTargetPlatform,
    ArkPCloudDeleteTargetPlatform
)
from ark_sdk_python.models.services.pcloud.safes import (
    ArkPCloudGetSafe, 
    ArkPCloudAddSafe, 
    ArkPCloudUpdateSafe, 
    ArkPCloudDeleteSafe,
    ArkPCloudListSafeMembers,
    ArkPCloudAddSafeMember,
    ArkPCloudUpdateSafeMember,
    ArkPCloudDeleteSafeMember,
    ArkPCloudGetSafeMember,
    ArkPCloudSafeMembersFilters,
    ArkPCloudSafeMemberType,
    ArkPCloudSafeMemberPermissionSet,
    ArkPCloudSafeMemberPermissions
)
from ark_sdk_python.models.services.pcloud.applications import (
    ArkPCloudApplicationsFilter,
    ArkPCloudAddApplication,
    ArkPCloudGetApplication,
    ArkPCloudDeleteApplication,
    ArkPCloudAddApplicationAuthMethod,
    ArkPCloudGetApplicationAuthMethod,
    ArkPCloudDeleteApplicationAuthMethod,
    ArkPCloudListApplicationAuthMethods,
    ArkPCloudApplicationAuthMethodsFilter,
    ArkPCloudApplicationAuthMethodCertKeyVal
)

# Backward compatibility - re-export CyberArkAPIError from server module
__all__ = ["CyberArkMCPServer", "CyberArkAPIError"]

logger = logging.getLogger(__name__)


def _get_model_attribute(model: BaseModel, *attr_names: str, default: Any = None) -> Any:
    """Safely get attribute from Pydantic model with fallback to different naming conventions.
    
    Args:
        model: Pydantic model instance
        *attr_names: Alternative attribute names to try (e.g., 'platformId', 'platform_id')
        default: Default value if none of the attributes exist
        
    Returns:
        The attribute value or default
    """
    for attr_name in attr_names:
        if hasattr(model, attr_name):
            return getattr(model, attr_name)
    return default


def handle_sdk_errors(operation_name: str) -> Any:
    """Decorator to standardize error handling for SDK operations with enhanced CyberArk-specific guidance.
    
    Args:
        operation_name: Description of the operation for logging
    """
    def decorator(func: Any) -> Any:
        @wraps(func)
        async def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            try:
                result = await func(self, *args, **kwargs)
                return result
            except Exception as e:
                # Special handling for known SDK validation issues
                error_str = str(e).lower()
                if "rotationalgroup" in error_str and operation_name == "listing platforms":
                    self.logger.warning(f"SDK validation failed due to API/SDK enum mismatch for {operation_name}, attempting direct API workaround: {e}")
                    
                    # Attempt direct API call workaround for the platforms enum issue
                    try:
                        # Import necessary modules
                        import json
                        import httpx
                        
                        # Get authentication token
                        auth_token = await self._run_in_executor(
                            lambda: self.platforms_service._isp_auth.token.token.get_secret_value()
                        )
                        
                        # Make direct API call
                        async with httpx.AsyncClient() as client:
                            headers = {
                                'Authorization': f'Bearer {auth_token}',
                                'Content-Type': 'application/json'
                            }
                            
                            # Build API URL using helper method
                            api_url = self._build_api_url('platforms_service', 'Platforms')
                            
                            response = await client.get(api_url, headers=headers)
                            if response.status_code == 200:
                                raw_data = response.json()
                                
                                # Fix the enum value in the response
                                for platform in raw_data.get('Platforms', []):
                                    general = platform.get('general', {})
                                    if general.get('platformType') == 'rotationalgroup':
                                        general['platformType'] = 'rotationalGroups'
                                
                                self.logger.info(f"Retrieved {len(raw_data.get('Platforms', []))} platforms via direct API call with enum fix")
                                return raw_data.get('Platforms', [])
                            else:
                                raise Exception(f"API call failed with status {response.status_code}")
                                    
                    except Exception as api_error:
                        self.logger.error(f"Direct API call workaround failed for {operation_name}: {api_error}")
                        # Fall through to normal error handling
                        pass
                
                # Enhanced error handling with SDK-specific exceptions and user guidance
                if is_sdk_exception(e):
                    # Extract status code from original SDK exception first
                    status_code = getattr(e, 'status_code', None) or getattr(e, 'response_code', None)
                    
                    # Convert SDK exception to our legacy format for backward compatibility
                    converted_error = convert_sdk_exception(e)
                    
                    # Provide specific guidance based on HTTP status codes
                    if status_code == 401:
                        self.logger.error(f"Authentication failed {operation_name}: {e}")
                        enhanced_message = (
                            f"Authentication failed for {operation_name}. "
                            "Please verify your CyberArk credentials (CYBERARK_CLIENT_ID and CYBERARK_CLIENT_SECRET) "
                            "and ensure your service account has proper access. "
                            "Token may have expired - consider restarting the MCP server."
                        )
                        raise CyberArkAPIError(enhanced_message, 401) from e
                        
                    elif status_code == 403:
                        self.logger.error(f"Access denied {operation_name}: {e}")
                        enhanced_message = (
                            f"Access denied for {operation_name}. "
                            "Your CyberArk user account lacks the required permissions. "
                            "For most operations, you need 'Privilege Cloud Administrator' role. "
                            "Contact your CyberArk administrator to verify and assign appropriate roles."
                        )
                        raise CyberArkAPIError(enhanced_message, 403) from e
                        
                    elif status_code == 404:
                        self.logger.error(f"Resource not found {operation_name}: {e}")
                        enhanced_message = (
                            f"Resource not found for {operation_name}. "
                            "Please verify the resource ID/name exists and is spelled correctly. "
                            "You may also lack permissions to view this resource."
                        )
                        raise CyberArkAPIError(enhanced_message, 404) from e
                        
                    elif status_code == 429:
                        self.logger.warning(f"Rate limit exceeded {operation_name}: {e}")
                        enhanced_message = (
                            f"Rate limit exceeded for {operation_name}. "
                            "CyberArk API has temporary rate limiting in effect. "
                            "Please wait a few seconds and retry the operation. "
                            "Consider reducing concurrent operations if this persists."
                        )
                        raise CyberArkAPIError(enhanced_message, 429) from e
                    else:
                        # For other SDK exceptions, provide the converted error with enhanced logging
                        self.logger.error(f"CyberArk SDK error {operation_name}: {e}")
                        raise converted_error from e
                else:
                    # For non-SDK exceptions, provide generic enhanced logging
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
        
        # Initialize ThreadPoolExecutor for non-blocking SDK calls
        self._executor = ThreadPoolExecutor(max_workers=5, thread_name_prefix="cyberark-sdk")
        
        # Initialize services directly - simpler than properties
        try:
            sdk_auth = self.sdk_authenticator.get_authenticated_client()
            self.accounts_service = ArkPCloudAccountsService(sdk_auth)
            self.safes_service = ArkPCloudSafesService(sdk_auth) 
            self.platforms_service = ArkPCloudPlatformsService(sdk_auth)
            self.applications_service = ArkPCloudApplicationsService(sdk_auth)
            self.sm_service = ArkSMService(sdk_auth)
        except (TypeError, AttributeError):
            # Handle test mocking scenarios where SDK objects may be mocked
            self.accounts_service = None
            self.safes_service = None
            self.platforms_service = None
            self.applications_service = None
            self.sm_service = None
        
        self.logger = logger

    @classmethod
    def from_environment(cls) -> "CyberArkMCPServer":
        """Create server from environment variables"""
        return cls()
    
    async def _run_in_executor(self, func: Any, *args: Any, **kwargs: Any) -> Any:
        """Run synchronous SDK calls in ThreadPoolExecutor to avoid blocking the event loop."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self._executor, lambda: func(*args, **kwargs))

    def _build_api_url(self, service_name: str, endpoint: str) -> str:
        """Build CyberArk API URL from SDK client base URL.
        
        Args:
            service_name: Name of the service ('platforms_service' or 'applications_service')
            endpoint: API endpoint (e.g., 'Platforms', 'Applications', 'Applications/Stats')
            
        Returns:
            Complete API URL with proper case conversion
        """
        if service_name == 'platforms_service':
            base_url = self.platforms_service._client.base_url
        elif service_name == 'applications_service':
            base_url = self.applications_service._client.base_url
        else:
            raise ValueError(f"Unknown service: {service_name}")
        
        return base_url.replace('passwordvault', 'PasswordVault') + endpoint

    def _ensure_service_initialized(self, service_name: str) -> None:
        """Ensure a specific service is initialized, initializing if needed."""
        if getattr(self, service_name) is None:
            sdk_auth = self.sdk_authenticator.get_authenticated_client()
            if service_name == 'accounts_service':
                self.accounts_service = ArkPCloudAccountsService(sdk_auth)
            elif service_name == 'safes_service':
                self.safes_service = ArkPCloudSafesService(sdk_auth)
            elif service_name == 'platforms_service':
                self.platforms_service = ArkPCloudPlatformsService(sdk_auth)
            elif service_name == 'applications_service':
                self.applications_service = ArkPCloudApplicationsService(sdk_auth)
            elif service_name == 'sm_service':
                self.sm_service = ArkSMService(sdk_auth)

    def reinitialize_services(self) -> None:
        """Reinitialize services - useful for testing or after auth changes."""
        sdk_auth = self.sdk_authenticator.get_authenticated_client()
        self.accounts_service = ArkPCloudAccountsService(sdk_auth)
        self.safes_service = ArkPCloudSafesService(sdk_auth) 
        self.platforms_service = ArkPCloudPlatformsService(sdk_auth)
        self.applications_service = ArkPCloudApplicationsService(sdk_auth)
        self.sm_service = ArkSMService(sdk_auth)

    # Legacy API methods removed - all operations now use ark-sdk-python directly

    def get_available_tools(self) -> List[str]:
        """Get list of available MCP tools"""
        return [
            "list_accounts",
            "get_account_details", 
            "search_accounts",
            "create_account",
            "update_account",
            "delete_account",
            "change_account_password",
            "set_next_password",
            "verify_account_password",
            "reconcile_account_password",
            "filter_accounts_by_platform_group",
            "filter_accounts_by_environment", 
            "filter_accounts_by_management_status",
            "group_accounts_by_safe",
            "group_accounts_by_platform",
            "analyze_account_distribution",
            "search_accounts_by_pattern",
            "count_accounts_by_criteria",
            "list_safes",
            "get_safe_details",
            "add_safe",
            "update_safe",
            "delete_safe",
            "list_safe_members",
            "get_safe_member_details", 
            "add_safe_member",
            "update_safe_member",
            "remove_safe_member",
            "list_platforms",
            "get_platform_details",
            "import_platform_package",
            "export_platform",
            "duplicate_target_platform",
            "activate_target_platform",
            "deactivate_target_platform",
            "delete_target_platform",
            "list_applications",
            "get_application_details",
            "add_application",
            "delete_application",
            "list_application_auth_methods",
            "get_application_auth_method_details",
            "add_application_auth_method",
            "delete_application_auth_method",
            "get_applications_stats"
        ]
    
    def clear_cache(self) -> None:
        """Clear all cached services and authentication state. Used for testing."""
        # Reset authentication state
        if hasattr(self.sdk_authenticator, '_sdk_auth'):
            self.sdk_authenticator._sdk_auth = None
            self.sdk_authenticator._is_authenticated = False
        
        # Reinitialize services with fresh authentication
        self.reinitialize_services()
    
    def shutdown(self) -> None:
        """Shutdown the ThreadPoolExecutor and clean up resources."""
        if hasattr(self, '_executor') and self._executor:
            self._executor.shutdown(wait=True)
            self.logger.info("ThreadPoolExecutor shutdown completed")

    # Account Management - Using ark-sdk-python
    @handle_sdk_errors("listing accounts")
    async def list_accounts(self, safe_name: Optional[str] = None, **kwargs) -> List[BaseModel]:
        """List accounts from CyberArk Privilege Cloud using ark-sdk-python"""
        self._ensure_service_initialized('accounts_service')
        
        # Build filter if safe_name is provided
        account_filter = None
        if safe_name:
            account_filter = ArkPCloudAccountsFilter(safe_name=safe_name)
        
        # Get accounts using SDK in executor
        if account_filter:
            # Use list_accounts_by method for filtering
            pages = await self._run_in_executor(
                lambda: list(self.accounts_service.list_accounts_by(accounts_filter=account_filter))
            )
        else:
            # Use basic list_accounts method without parameters
            pages = await self._run_in_executor(
                lambda: list(self.accounts_service.list_accounts())
            )
        
        # Return Pydantic models directly - flatten pagination
        accounts = [acc for page in pages for acc in page.items]
        
        self.logger.info(f"Retrieved {len(accounts)} accounts using ark-sdk-python")
        return accounts

    @handle_sdk_errors("getting account details")
    async def get_account_details(self, account_id: str) -> ArkPCloudAccount:
        """Get detailed information about a specific account using ark-sdk-python"""
        self._ensure_service_initialized('accounts_service')
        account = await self._run_in_executor(
            self.accounts_service.get_account, account_id=account_id
        )
        self.logger.info(f"Retrieved account details for ID: {account_id} using ark-sdk-python")
        return account

    @handle_sdk_errors("searching accounts")
    async def search_accounts(
        self,
        query: Optional[str] = None,
        safe_name: Optional[str] = None,
        username: Optional[str] = None,
        address: Optional[str] = None,
        platform_id: Optional[str] = None,
        **kwargs
    ) -> List[BaseModel]:
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
        
        # Get accounts using SDK with filter and search in executor
        if search_query:
            # Use list_accounts with search parameter
            pages = await self._run_in_executor(
                lambda: list(self.accounts_service.list_accounts(search=search_query))
            )
        else:
            # Use list_accounts_by for filtering only
            pages = await self._run_in_executor(
                lambda: list(self.accounts_service.list_accounts_by(accounts_filter=account_filter))
            )
        
        # Return Pydantic models directly - flatten pagination
        accounts = [acc for page in pages for acc in page.items]
        
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
    ) -> BaseModel:
        """Create a new privileged account using ark-sdk-python"""
        self._ensure_service_initialized('accounts_service')

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
        
        # Create the account using SDK in executor
        created_account = await self._run_in_executor(
            self.accounts_service.add_account, add_account
        )
        
        self.logger.info(f"Successfully created account with ID: {created_account.id}")
        return created_account

    @handle_sdk_errors("changing account password")
    async def change_account_password(self, account_id: str, **kwargs) -> BaseModel:
        """Initiate CPM-managed password change using ark-sdk-python"""
        self._ensure_service_initialized('accounts_service')

        # Create the change credentials model
        change_creds = ArkPCloudChangeAccountCredentials(
            account_id=account_id,
            change_creds_for_group=True  # Equivalent to ChangeCredsForGroup
        )
        
        # Change the account password using SDK
        result = await self._run_in_executor(
            self.accounts_service.change_account_credentials, change_creds
        )
        
        self.logger.info(f"Successfully initiated password change for account ID: {account_id}")
        return result

    @handle_sdk_errors("setting next password")
    async def set_next_password(
        self, account_id: str, new_password: str, change_immediately: bool = True, **kwargs
    ) -> BaseModel:
        """Set the next password for an account using ark-sdk-python"""
        self._ensure_service_initialized('accounts_service')

        # Create the set next credentials model with required accountId field
        set_next_creds = ArkPCloudSetAccountNextCredentials(
            accountId=account_id,
            change_immediately=change_immediately,
            new_credentials=new_password
        )
        
        # Set the next password using SDK
        result = await self._run_in_executor(
            self.accounts_service.set_account_next_credentials, set_next_creds
        )
        
        self.logger.info(f"Successfully set next password for account ID: {account_id}")
        return result

    @handle_sdk_errors("verifying account password")
    async def verify_account_password(self, account_id: str, **kwargs) -> BaseModel:
        """Verify the password for an account using ark-sdk-python"""
        self._ensure_service_initialized('accounts_service')

        # Create the verify credentials model with required account_id
        verify_creds = ArkPCloudVerifyAccountCredentials(
            account_id=account_id
        )
        
        # Verify the account password using SDK
        result = await self._run_in_executor(
            self.accounts_service.verify_account_credentials, verify_creds
        )
        
        self.logger.info(f"Successfully verified password for account ID: {account_id}")
        return result

    @handle_sdk_errors("reconciling account password")
    async def reconcile_account_password(self, account_id: str, **kwargs) -> BaseModel:
        """Reconcile the password for an account using ark-sdk-python"""
        self._ensure_service_initialized('accounts_service')

        # Create the reconcile credentials model
        reconcile_creds = ArkPCloudReconcileAccountCredentials(account_id=account_id)
        
        # Reconcile the account password using SDK
        result = await self._run_in_executor(
            self.accounts_service.reconcile_account_credentials, reconcile_creds
        )
        
        self.logger.info(f"Successfully reconciled password for account ID: {account_id}")
        return result

    @handle_sdk_errors("updating account")
    async def update_account(
        self,
        account_id: str,
        name: Optional[str] = None,
        address: Optional[str] = None,
        user_name: Optional[str] = None,
        platform_account_properties: Optional[Dict[str, Any]] = None,
        secret_management: Optional[Dict[str, Any]] = None,
        remote_machines_access: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> BaseModel:
        """Update an existing account using ark-sdk-python"""
        self._ensure_service_initialized('accounts_service')
        
        # Validate required parameters
        if not account_id or not isinstance(account_id, str):
            raise ValueError("account_id is required and must be a non-empty string")
        
        # Create the update account model with proper field mapping for SDK
        update_data = {'accountId': account_id}  # Required field
        if name is not None:
            update_data['name'] = name
        if address is not None:
            update_data['address'] = address
        if user_name is not None:
            update_data['username'] = user_name  # SDK uses 'username', not 'user_name'
        if platform_account_properties is not None:
            update_data['platformAccountProperties'] = platform_account_properties
        if secret_management is not None:
            update_data['secretManagement'] = secret_management
        if remote_machines_access is not None:
            update_data['remoteMachinesAccess'] = remote_machines_access
        
        # Create the update account model
        update_account = ArkPCloudUpdateAccount(**update_data)
        
        # Update the account using SDK
        result = await self._run_in_executor(
            self.accounts_service.update_account, update_account
        )
        
        self.logger.info(f"Successfully updated account ID: {account_id}")
        return result

    @handle_sdk_errors("deleting account")
    async def delete_account(self, account_id: str, **kwargs) -> BaseModel:
        """Delete an existing account using ark-sdk-python"""
        self._ensure_service_initialized('accounts_service')
        
        # Validate required parameters
        if not account_id or not isinstance(account_id, str):
            raise ValueError("account_id is required and must be a non-empty string")
        
        # Create the delete account model
        delete_account = ArkPCloudDeleteAccount(account_id=account_id)
        
        # Delete the account using SDK
        result = await self._run_in_executor(
            self.accounts_service.delete_account, delete_account
        )
        
        self.logger.info(f"Successfully deleted account ID: {account_id}")
        return result

    # Advanced Account Search and Filtering - Using ark-sdk-python
    @handle_sdk_errors("filtering accounts by platform group")
    async def filter_accounts_by_platform_group(self, platform_group: str, **kwargs) -> List[BaseModel]:
        """Filter accounts by platform type grouping (Windows, Linux, Database, etc.)"""
        self._ensure_service_initialized('accounts_service')
        
        # Get all accounts in executor
        pages = await self._run_in_executor(
            lambda: list(self.accounts_service.list_accounts())
        )
        all_accounts = [acc for page in pages for acc in page.items]
        
        # Define platform group mappings
        platform_groups = {
            "Windows": ["WindowsDomainAccount", "WindowsServerLocalAccount", "WindowsDesktopLocalAccount"],
            "Linux": ["LinuxAccount", "UnixAccount", "UnixSSH"],
            "Database": ["SQLServerAccount", "OracleAccount", "MySQLAccount", "PostgreSQLAccount"],
            "Network": ["CiscoAccount", "JuniperAccount", "F5Account"],
            "Cloud": ["AWSAccount", "AzureAccount", "GCPAccount"]
        }
        
        # Filter by platform group - access Pydantic model attributes
        group_platforms = platform_groups.get(platform_group, [platform_group])
        filtered_accounts = [
            acc for acc in all_accounts 
            if any(platform in _get_model_attribute(acc, 'platformId', 'platform_id', default='') for platform in group_platforms)
        ]
        
        self.logger.info(f"Found {len(filtered_accounts)} accounts in platform group '{platform_group}'")
        return filtered_accounts

    @handle_sdk_errors("filtering accounts by environment")
    async def filter_accounts_by_environment(self, environment: str, **kwargs) -> List[BaseModel]:
        """Filter accounts by environment (production, staging, development, etc.)"""
        self._ensure_service_initialized('accounts_service')
        
        # Get all accounts in executor
        pages = await self._run_in_executor(
            lambda: list(self.accounts_service.list_accounts())
        )
        all_accounts = [acc for page in pages for acc in page.items]
        
        # Filter by environment in address field - access Pydantic model attributes
        filtered_accounts = [
            acc for acc in all_accounts 
            if environment.lower() in str(_get_model_attribute(acc, 'address', default='')).lower()
        ]
        
        self.logger.info(f"Found {len(filtered_accounts)} accounts in '{environment}' environment")
        return filtered_accounts

    @handle_sdk_errors("filtering accounts by management status")
    async def filter_accounts_by_management_status(self, auto_managed: bool = True, **kwargs) -> List[BaseModel]:
        """Filter accounts by automatic password management status"""
        self._ensure_service_initialized('accounts_service')

        # Get all accounts in executor
        pages = await self._run_in_executor(
            lambda: list(self.accounts_service.list_accounts())
        )
        all_accounts = [acc for page in pages for acc in page.items]
        
        # Filter by management status - handle nested Pydantic model attributes
        filtered_accounts = []
        for acc in all_accounts:
            secret_mgmt = _get_model_attribute(acc, 'secretManagement', 'secret_management')
            if secret_mgmt:
                auto_mgmt_enabled = _get_model_attribute(secret_mgmt, 'automaticManagementEnabled', 'automatic_management_enabled', default=False)
                if auto_mgmt_enabled == auto_managed:
                    filtered_accounts.append(acc)
            elif not auto_managed:  # If no secret management info and looking for manual
                filtered_accounts.append(acc)
        
        status_text = "automatically managed" if auto_managed else "manually managed"
        self.logger.info(f"Found {len(filtered_accounts)} {status_text} accounts")
        return filtered_accounts

    @handle_sdk_errors("grouping accounts by safe")
    async def group_accounts_by_safe(self, **kwargs) -> Dict[str, List[Dict[str, Any]]]:
        """Group accounts by safe name"""
        self._ensure_service_initialized('accounts_service')
        
        # Get all accounts in executor
        pages = await self._run_in_executor(
            lambda: list(self.accounts_service.list_accounts())
        )
        all_accounts = [acc for page in pages for acc in page.items]
        
        # Group by safe - work with Pydantic models, convert only when building return dict
        grouped_accounts = {}
        for acc in all_accounts:
            safe_name = _get_model_attribute(acc, "safeName", "safe_name", default="Unknown")
            if safe_name not in grouped_accounts:
                grouped_accounts[safe_name] = []
            grouped_accounts[safe_name].append(acc.model_dump())
        
        self.logger.info(f"Grouped {len(all_accounts)} accounts into {len(grouped_accounts)} safes")
        return grouped_accounts

    @handle_sdk_errors("grouping accounts by platform")
    async def group_accounts_by_platform(self, **kwargs) -> Dict[str, List[Dict[str, Any]]]:
        """Group accounts by platform type"""
        self._ensure_service_initialized('accounts_service')
        
        # Get all accounts
        pages = await self._run_in_executor(
            lambda: list(self.accounts_service.list_accounts())
        )
        all_accounts = [acc for page in pages for acc in page.items]
        
        # Group by platform - work with Pydantic models, convert only when building return dict
        grouped_accounts = {}
        for acc in all_accounts:
            platform_id = _get_model_attribute(acc, "platformId", "platform_id", default="Unknown")
            if platform_id not in grouped_accounts:
                grouped_accounts[platform_id] = []
            grouped_accounts[platform_id].append(acc.model_dump())
        
        self.logger.info(f"Grouped {len(all_accounts)} accounts into {len(grouped_accounts)} platform types")
        return grouped_accounts

    @handle_sdk_errors("analyzing account distribution")
    async def analyze_account_distribution(self, **kwargs) -> Any:
        """Analyze distribution of accounts across safes, platforms, and environments"""
        self._ensure_service_initialized('accounts_service')
        
        # Get all accounts
        pages = await self._run_in_executor(
            lambda: list(self.accounts_service.list_accounts())
        )
        all_accounts = [acc for page in pages for acc in page.items]
        
        # Analyze distribution
        safe_counts = {}
        platform_counts = {}
        env_counts = {}
        auto_managed_count = 0
        
        for acc in all_accounts:
            # Count by safe - use Pydantic model attribute access
            safe_name = _get_model_attribute(acc, "safeName", "safe_name", default="Unknown")
            safe_counts[safe_name] = safe_counts.get(safe_name, 0) + 1
            
            # Count by platform
            platform_id = _get_model_attribute(acc, "platformId", "platform_id", default="Unknown")
            platform_counts[platform_id] = platform_counts.get(platform_id, 0) + 1
            
            # Count by environment (extracted from address)
            address = str(_get_model_attribute(acc, "address", default=""))
            for env in ["production", "staging", "development", "test"]:
                if env in address.lower():
                    env_counts[env] = env_counts.get(env, 0) + 1
                    break
            
            # Count auto-managed - handle nested Pydantic model attributes
            secret_mgmt = _get_model_attribute(acc, 'secretManagement', 'secret_management')
            if secret_mgmt:
                auto_mgmt_enabled = _get_model_attribute(secret_mgmt, 'automaticManagementEnabled', 'automatic_management_enabled', default=False)
                if auto_mgmt_enabled:
                    auto_managed_count += 1
        
        total_accounts = len(all_accounts)
        auto_managed_percentage = (auto_managed_count / total_accounts * 100) if total_accounts > 0 else 0
        
        distribution = {
            "total_accounts": total_accounts,
            "by_safe": safe_counts,
            "by_platform": platform_counts,
            "by_environment": env_counts,
            "auto_managed_count": auto_managed_count,
            "auto_managed_percentage": round(auto_managed_percentage, 2)
        }
        
        self.logger.info(f"Analyzed distribution for {total_accounts} accounts")
        return distribution

    @handle_sdk_errors("searching accounts by pattern")
    async def search_accounts_by_pattern(
        self,
        username_pattern: Optional[str] = None,
        address_pattern: Optional[str] = None,
        environment: Optional[str] = None,
        platform_group: Optional[str] = None,
        **kwargs
    ) -> Any:
        """Search accounts using multiple pattern criteria"""
        self._ensure_service_initialized('accounts_service')
        
        # Get all accounts
        pages = await self._run_in_executor(
            lambda: list(self.accounts_service.list_accounts())
        )
        all_accounts = [acc for page in pages for acc in page.items]
        
        # Apply filters
        filtered_accounts = all_accounts
        
        if username_pattern:
            filtered_accounts = [
                acc for acc in filtered_accounts 
                if username_pattern.lower() in str(_get_model_attribute(acc, "userName", "user_name", default="")).lower()
            ]
        
        if address_pattern:
            filtered_accounts = [
                acc for acc in filtered_accounts 
                if address_pattern.lower() in str(_get_model_attribute(acc, "address", default="")).lower()
            ]
        
        if environment:
            filtered_accounts = [
                acc for acc in filtered_accounts 
                if environment.lower() in str(_get_model_attribute(acc, "address", default="")).lower()
            ]
        
        if platform_group:
            platform_groups = {
                "Windows": ["WindowsDomainAccount", "WindowsServerLocalAccount", "WindowsDesktopLocalAccount"],
                "Linux": ["LinuxAccount", "UnixAccount", "UnixSSH"],
                "Database": ["SQLServerAccount", "OracleAccount", "MySQLAccount", "PostgreSQLAccount"]
            }
            group_platforms = platform_groups.get(platform_group, [platform_group])
            filtered_accounts = [
                acc for acc in filtered_accounts 
                if any(platform in str(_get_model_attribute(acc, "platformId", "platform_id", default="")) for platform in group_platforms)
            ]
        
        self.logger.info(f"Found {len(filtered_accounts)} accounts matching pattern criteria")
        return filtered_accounts

    @handle_sdk_errors("counting accounts by criteria")
    async def count_accounts_by_criteria(self, **kwargs) -> Any:
        """Count accounts by various criteria"""
        self._ensure_service_initialized('accounts_service')
        
        # Get all accounts
        pages = await self._run_in_executor(
            lambda: list(self.accounts_service.list_accounts())
        )
        all_accounts = [acc for page in pages for acc in page.items]
        
        # Count by criteria
        total = len(all_accounts)
        auto_managed = 0
        for acc in all_accounts:
            secret_mgmt = _get_model_attribute(acc, 'secretManagement', 'secret_management')
            if secret_mgmt:
                auto_mgmt_enabled = _get_model_attribute(secret_mgmt, 'automaticManagementEnabled', 'automatic_management_enabled', default=False)
                if auto_mgmt_enabled:
                    auto_managed += 1
        manual_managed = total - auto_managed
        
        # Count by platform
        platform_counts = {}
        for acc in all_accounts:
            platform_id = _get_model_attribute(acc, "platformId", "platform_id", default="Unknown")
            platform_counts[platform_id] = platform_counts.get(platform_id, 0) + 1
        
        # Count by safe
        safe_counts = {}
        for acc in all_accounts:
            safe_name = _get_model_attribute(acc, "safeName", "safe_name", default="Unknown")
            safe_counts[safe_name] = safe_counts.get(safe_name, 0) + 1
        
        counts = {
            "total": total,
            "auto_managed": auto_managed,
            "manual_managed": manual_managed,
            "by_platform": platform_counts,
            "by_safe": safe_counts
        }
        
        self.logger.info(f"Counted {total} accounts across all criteria")
        return counts

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
    ) -> List[BaseModel]:
        """List all accessible safes using ark-sdk-python"""
        self._ensure_service_initialized('safes_service')
        
        # Get safes using SDK in executor
        pages = await self._run_in_executor(
            lambda: list(self.safes_service.list_safes())
        )
        
        # Return Pydantic models directly - flatten pagination
        safes = [safe for page in pages for safe in page.items]
        
        self.logger.info(f"Retrieved {len(safes)} safes using ark-sdk-python")
        return safes

    @handle_sdk_errors("getting safe details")
    async def get_safe_details(
        self,
        safe_name: str,
        include_accounts: Optional[bool] = None,
        use_cache: Optional[bool] = None,
        **kwargs
    ) -> BaseModel:
        """Get detailed information about a specific safe using ark-sdk-python"""
        self._ensure_service_initialized('safes_service')

        # Create the get safe model (safe_name is used as safe_id in CyberArk)
        get_safe = ArkPCloudGetSafe(safe_id=safe_name)
        
        # Get safe details using SDK in executor
        safe = await self._run_in_executor(
            self.safes_service.safe, get_safe=get_safe
        )
        
        self.logger.info(f"Retrieved safe details for: {safe_name} using ark-sdk-python")
        return safe

    @handle_sdk_errors("adding safe")
    async def add_safe(
        self,
        safe_name: str,
        description: Optional[str] = None,
        **kwargs
    ) -> BaseModel:
        """Add a new safe to CyberArk Privilege Cloud using ark-sdk-python"""
        self._ensure_service_initialized('safes_service')
        
        # Create the add safe model
        add_safe = ArkPCloudAddSafe(
            safe_name=safe_name,
            description=description
        )
        
        # Add the safe using SDK in executor
        created_safe = await self._run_in_executor(
            self.safes_service.add_safe, add_safe
        )
        
        self.logger.info(f"Successfully created safe: {safe_name}")
        return created_safe

    @handle_sdk_errors("updating safe")
    async def update_safe(
        self,
        safe_id: str,
        safe_name: Optional[str] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        number_of_days_retention: Optional[int] = None,
        number_of_versions_retention: Optional[int] = None,
        auto_purge_enabled: Optional[bool] = None,
        olac_enabled: Optional[bool] = None,
        managing_cpm: Optional[str] = None,
        **kwargs
    ) -> BaseModel:
        """Update an existing safe in CyberArk Privilege Cloud using ark-sdk-python"""
        self._ensure_service_initialized('safes_service')
        
        # Create the update safe model with only provided fields
        update_data = {'safe_id': safe_id}
        if safe_name is not None:
            update_data['safe_name'] = safe_name
        if description is not None:
            update_data['description'] = description
        if location is not None:
            update_data['location'] = location
        if number_of_days_retention is not None:
            update_data['number_of_days_retention'] = number_of_days_retention
        if number_of_versions_retention is not None:
            update_data['number_of_versions_retention'] = number_of_versions_retention
        if auto_purge_enabled is not None:
            update_data['auto_purge_enabled'] = auto_purge_enabled
        if olac_enabled is not None:
            update_data['olac_enabled'] = olac_enabled
        if managing_cpm is not None:
            update_data['managing_cpm'] = managing_cpm
            
        update_safe = ArkPCloudUpdateSafe(**update_data)

        # Update the safe using SDK in executor
        updated_safe = await self._run_in_executor(
            lambda: self.safes_service.update_safe(update_safe=update_safe)
        )

        self.logger.info(f"Successfully updated safe: {safe_id}")
        return updated_safe

    @handle_sdk_errors("deleting safe")
    async def delete_safe(
        self,
        safe_id: str,
        **kwargs
    ) -> Any:
        """Delete a safe from CyberArk Privilege Cloud using ark-sdk-python"""
        self._ensure_service_initialized('safes_service')
        
        # Create the delete safe model
        delete_safe = ArkPCloudDeleteSafe(safe_id=safe_id)

        # Delete the safe using SDK in executor (returns None)
        await self._run_in_executor(
            lambda: self.safes_service.delete_safe(delete_safe=delete_safe)
        )

        self.logger.info(f"Successfully deleted safe: {safe_id}")
        return {"message": f"Safe {safe_id} deleted successfully", "safe_id": safe_id}

    # Safe Member Management - Using ark-sdk-python
    @handle_sdk_errors("listing safe members")
    async def list_safe_members(
        self,
        safe_name: str,
        search: Optional[str] = None,
        sort: Optional[str] = None,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
        member_type: Optional[str] = None,
        **kwargs
    ) -> Any:
        """List all members of a specific safe using ark-sdk-python"""
        self._ensure_service_initialized('safes_service')
        
        # Handle basic list vs filtered list
        if any([search, sort, offset, limit, member_type]):
            # Use filtered list with ArkPCloudSafeMembersFilters
            member_type_enum = None
            if member_type:
                try:
                    member_type_enum = ArkPCloudSafeMemberType(member_type)
                except ValueError:
                    raise ValueError(f"Invalid member_type: {member_type}. Valid types: User, Group, Role")
            
            filters = ArkPCloudSafeMembersFilters(
                safe_id=safe_name,
                search=search,
                sort=sort,
                offset=offset,
                limit=limit,
                member_type=member_type_enum
            )
            pages = await self._run_in_executor(
                lambda: list(self.safes_service.list_safe_members_by(filters))
            )
        else:
            # Use basic list
            list_members = ArkPCloudListSafeMembers(safe_id=safe_name)
            pages = await self._run_in_executor(
                lambda: list(self.safes_service.list_safe_members(list_members))
            )
        
        # Flatten pagination and return Pydantic models
        members = [member for page in pages for member in page.items]
        
        self.logger.info(f"Retrieved {len(members)} safe members for safe: {safe_name} using ark-sdk-python")
        return members

    @handle_sdk_errors("getting safe member details")
    async def get_safe_member_details(self, safe_name: str, member_name: str) -> ArkPCloudSafeMember:
        """Get detailed information about a specific safe member using ark-sdk-python"""
        self._ensure_service_initialized('safes_service')
        
        # Create the get safe member model
        get_member = ArkPCloudGetSafeMember(safe_id=safe_name, member_name=member_name)

        # Get safe member details using SDK in executor
        member = await self._run_in_executor(
            lambda: self.safes_service.safe_member(get_member)
        )

        self.logger.info(f"Retrieved safe member details for: {member_name} in safe: {safe_name} using ark-sdk-python")
        return member

    @handle_sdk_errors("adding safe member")
    async def add_safe_member(
        self,
        safe_name: str,
        member_name: str,
        member_type: str,
        search_in: Optional[str] = None,
        membership_expiration_date: Optional[str] = None,
        permissions: Optional[Dict[str, Any]] = None,
        permission_set: Optional[str] = None,
        **kwargs
    ) -> Any:
        """Add a new member to a safe using ark-sdk-python"""
        self._ensure_service_initialized('safes_service')
        
        # Convert string member_type to enum
        try:
            member_type_enum = ArkPCloudSafeMemberType(member_type)
        except ValueError:
            raise ValueError(f"Invalid member_type: {member_type}. Valid types: User, Group, Role")
        
        # Handle permission set or custom permissions
        permission_set_enum = None
        permissions_model = None
        
        if permission_set:
            # Convert common user-friendly names to actual enum values
            permission_set_mapping = {
                "ConnectOnly": ArkPCloudSafeMemberPermissionSet.ConnectOnly,
                "connect_only": ArkPCloudSafeMemberPermissionSet.ConnectOnly,
                "ReadOnly": ArkPCloudSafeMemberPermissionSet.ReadOnly,
                "read_only": ArkPCloudSafeMemberPermissionSet.ReadOnly,
                "Approver": ArkPCloudSafeMemberPermissionSet.Approver,
                "approver": ArkPCloudSafeMemberPermissionSet.Approver,
                "AccountsManager": ArkPCloudSafeMemberPermissionSet.AccountsManager,
                "accounts_manager": ArkPCloudSafeMemberPermissionSet.AccountsManager,
                "Full": ArkPCloudSafeMemberPermissionSet.Full,
                "full": ArkPCloudSafeMemberPermissionSet.Full,
                "Custom": ArkPCloudSafeMemberPermissionSet.Custom,
                "custom": ArkPCloudSafeMemberPermissionSet.Custom,
            }
            permission_set_enum = permission_set_mapping.get(permission_set)
            if not permission_set_enum:
                raise ValueError(f"Invalid permission_set: {permission_set}. Valid sets: ConnectOnly, ReadOnly, Approver, AccountsManager, Full, Custom")
        
        if permissions:
            permissions_model = ArkPCloudSafeMemberPermissions(**permissions)
            if not permission_set:
                permission_set_enum = ArkPCloudSafeMemberPermissionSet.Custom
        
        # Default to ReadOnly if no permissions specified
        if not permission_set_enum and not permissions_model:
            permission_set_enum = ArkPCloudSafeMemberPermissionSet.ReadOnly
        
        # Handle expiration date
        from datetime import datetime
        expiration_date = None
        if membership_expiration_date:
            try:
                expiration_date = datetime.fromisoformat(membership_expiration_date.replace('Z', '+00:00'))
            except ValueError:
                raise ValueError(f"Invalid membership_expiration_date format: {membership_expiration_date}. Use ISO 8601 format.")
        
        # Create the add safe member model
        add_member = ArkPCloudAddSafeMember(
            safe_id=safe_name,
            member_name=member_name,
            member_type=member_type_enum,
            search_in=search_in,
            membership_expiration_date=expiration_date,
            permissions=permissions_model,
            permission_set=permission_set_enum
        )

        # Add the safe member using SDK in executor
        created_member = await self._run_in_executor(
            lambda: self.safes_service.add_safe_member(add_member)
        )

        self.logger.info(f"Successfully added member {member_name} to safe: {safe_name}")
        return created_member

    @handle_sdk_errors("updating safe member")
    async def update_safe_member(
        self,
        safe_name: str,
        member_name: str,
        search_in: Optional[str] = None,
        membership_expiration_date: Optional[str] = None,
        permissions: Optional[Dict[str, Any]] = None,
        permission_set: Optional[str] = None,
        **kwargs
    ) -> Any:
        """Update permissions for an existing safe member using ark-sdk-python"""
        self._ensure_service_initialized('safes_service')
        
        # Handle permission set or custom permissions
        permission_set_enum = None
        permissions_model = None
        
        if permission_set:
            # Convert common user-friendly names to actual enum values
            permission_set_mapping = {
                "ConnectOnly": ArkPCloudSafeMemberPermissionSet.ConnectOnly,
                "connect_only": ArkPCloudSafeMemberPermissionSet.ConnectOnly,
                "ReadOnly": ArkPCloudSafeMemberPermissionSet.ReadOnly,
                "read_only": ArkPCloudSafeMemberPermissionSet.ReadOnly,
                "Approver": ArkPCloudSafeMemberPermissionSet.Approver,
                "approver": ArkPCloudSafeMemberPermissionSet.Approver,
                "AccountsManager": ArkPCloudSafeMemberPermissionSet.AccountsManager,
                "accounts_manager": ArkPCloudSafeMemberPermissionSet.AccountsManager,
                "Full": ArkPCloudSafeMemberPermissionSet.Full,
                "full": ArkPCloudSafeMemberPermissionSet.Full,
                "Custom": ArkPCloudSafeMemberPermissionSet.Custom,
                "custom": ArkPCloudSafeMemberPermissionSet.Custom,
            }
            permission_set_enum = permission_set_mapping.get(permission_set)
            if not permission_set_enum:
                raise ValueError(f"Invalid permission_set: {permission_set}. Valid sets: ConnectOnly, ReadOnly, Approver, AccountsManager, Full, Custom")
        
        if permissions:
            permissions_model = ArkPCloudSafeMemberPermissions(**permissions)
            if not permission_set:
                permission_set_enum = ArkPCloudSafeMemberPermissionSet.Custom
        
        # Handle expiration date
        from datetime import datetime
        expiration_date = None
        if membership_expiration_date:
            try:
                expiration_date = datetime.fromisoformat(membership_expiration_date.replace('Z', '+00:00'))
            except ValueError:
                raise ValueError(f"Invalid membership_expiration_date format: {membership_expiration_date}. Use ISO 8601 format.")
        
        # Create the update safe member model
        update_member = ArkPCloudUpdateSafeMember(
            safe_id=safe_name,
            member_name=member_name,
            search_in=search_in,
            membership_expiration_date=expiration_date,
            permissions=permissions_model,
            permission_set=permission_set_enum
        )

        # Update the safe member using SDK in executor
        updated_member = await self._run_in_executor(
            lambda: self.safes_service.update_safe_member(update_member)
        )

        self.logger.info(f"Successfully updated member {member_name} in safe: {safe_name}")
        return updated_member

    @handle_sdk_errors("removing safe member")
    async def remove_safe_member(
        self,
        safe_name: str,
        member_name: str,
        **kwargs
    ) -> Any:
        """Remove a member from a safe using ark-sdk-python"""
        self._ensure_service_initialized('safes_service')
        
        # Create the delete safe member model
        delete_member = ArkPCloudDeleteSafeMember(safe_id=safe_name, member_name=member_name)

        # Delete the safe member using SDK in executor (returns None)
        await self._run_in_executor(
            lambda: self.safes_service.delete_safe_member(delete_member)
        )

        self.logger.info(f"Successfully removed member {member_name} from safe: {safe_name}")
        return {
            "message": f"Member {member_name} removed from safe {safe_name} successfully",
            "safe_name": safe_name,
            "member_name": member_name
        }

    # Platform Management - Using ark-sdk-python
    @handle_sdk_errors("listing platforms")
    async def list_platforms(
        self,
        search: Optional[str] = None,
        active: Optional[bool] = None,
        system_type: Optional[str] = None,
        **kwargs
    ) -> Any:
        """List available platforms using ark-sdk-python with proper pagination handling"""
        self._ensure_service_initialized('platforms_service')
        
        # Get platforms using SDK in executor with pagination handling
        def get_all_platforms():
            """Get all platforms from all pages"""
            all_platforms = []
            # The SDK returns a page iterator, we need to iterate through all pages
            for page in self.platforms_service.list_platforms():
                for platform in page:
                    all_platforms.append(platform)
            return all_platforms
        
        platforms = await self._run_in_executor(get_all_platforms)
        
        self.logger.info(f"Retrieved {len(platforms)} platforms using ark-sdk-python (all pages)")
        
        # Convert to dict format to avoid Pydantic validation issues
        # The SDK model may have stricter validation than the actual API responses
        return [platform.model_dump() if hasattr(platform, 'model_dump') else platform for platform in platforms]

    @handle_sdk_errors("getting platform details")
    async def get_platform_details(self, platform_id: str) -> Dict[str, Any]:
        """Get detailed platform configuration using ark-sdk-python"""
        self._ensure_service_initialized('platforms_service')

        # Create the get platform model
        get_platform = ArkPCloudGetPlatform(platform_id=platform_id)
        
        # Get platform details using SDK in executor
        platform = await self._run_in_executor(
            self.platforms_service.platform, get_platform=get_platform
        )
        
        self.logger.info(f"Retrieved platform details for: {platform_id} using ark-sdk-python")
        
        # Convert to dict format to avoid Pydantic validation issues
        return platform.model_dump() if hasattr(platform, 'model_dump') else platform

    @handle_sdk_errors("importing platform package")
    async def import_platform_package(
        self, platform_package_file: Union[str, bytes], **kwargs
    ) -> Any:
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
        
        # Import platform using SDK in executor
        result = await self._run_in_executor(
            lambda: self.platforms_service.import_platform(import_platform=import_platform)
        )

        self.logger.info(f"Successfully imported platform package using ark-sdk-python ({len(file_content)} bytes)")
        return result

    async def get_complete_platform_info(
        self, platform_id: str, platform_basic: Optional[Dict[str, Any]] = None
    ) -> Any:
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

    async def list_platforms_with_details(self, **kwargs) -> Any:
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

    @handle_sdk_errors("exporting platform")
    async def export_platform(self, platform_id: str, output_folder: str, **kwargs) -> Any:
        """Export platform configuration package using ark-sdk-python"""
        self._ensure_service_initialized('platforms_service')
        
        # Create the export platform model
        export_platform = ArkPCloudExportPlatform(
            platform_id=platform_id,
            output_folder=output_folder
        )
        
        # Export the platform using SDK in executor
        await self._run_in_executor(
            lambda: self.platforms_service.export_platform(export_platform=export_platform)
        )

        self.logger.info(f"Platform exported successfully: {platform_id} to {output_folder}")
        return {
            "platform_id": platform_id,
            "output_folder": output_folder,
            "status": "exported"
        }

    @handle_sdk_errors("duplicating target platform")
    async def duplicate_target_platform(
        self, 
        target_platform_id: int, 
        name: str, 
        description: Optional[str] = None, 
        **kwargs
    ) -> Any:
        """Duplicate/clone a target platform using ark-sdk-python"""
        self._ensure_service_initialized('platforms_service')
        
        # Create the duplicate target platform model
        duplicate_platform = ArkPCloudDuplicateTargetPlatform(
            target_platform_id=target_platform_id,
            name=name,
            description=description
        )
        
        # Duplicate the target platform using SDK in executor
        duplicated_platform = await self._run_in_executor(
            lambda: self.platforms_service.duplicate_target_platform(
                duplicate_target_platform=duplicate_platform
            )
        )

        self.logger.info(f"Target platform duplicated successfully: {target_platform_id} -> {name}")
        return duplicated_platform

    @handle_sdk_errors("activating target platform")
    async def activate_target_platform(self, target_platform_id: int, **kwargs) -> Any:
        """Activate/enable target platform using ark-sdk-python"""
        self._ensure_service_initialized('platforms_service')
        
        # Create the activate target platform model
        activate_platform = ArkPCloudActivateTargetPlatform(
            target_platform_id=target_platform_id
        )
        
        # Activate the target platform using SDK in executor
        await self._run_in_executor(
            lambda: self.platforms_service.activate_target_platform(
                activate_target_platform=activate_platform
            )
        )

        self.logger.info(f"Target platform activated successfully: {target_platform_id}")
        return {
            "target_platform_id": target_platform_id,
            "status": "activated"
        }

    @handle_sdk_errors("deactivating target platform")
    async def deactivate_target_platform(self, target_platform_id: int, **kwargs) -> Any:
        """Deactivate/disable target platform using ark-sdk-python"""
        self._ensure_service_initialized('platforms_service')
        
        # Create the deactivate target platform model
        deactivate_platform = ArkPCloudDeactivateTargetPlatform(
            target_platform_id=target_platform_id
        )
        
        # Deactivate the target platform using SDK in executor
        await self._run_in_executor(
            lambda: self.platforms_service.deactivate_target_platform(
                deactivate_target_platform=deactivate_platform
            )
        )

        self.logger.info(f"Target platform deactivated successfully: {target_platform_id}")
        return {
            "target_platform_id": target_platform_id,
            "status": "deactivated"
        }

    @handle_sdk_errors("deleting target platform")
    async def delete_target_platform(self, target_platform_id: int, **kwargs) -> Any:
        """Delete target platform using ark-sdk-python"""
        self._ensure_service_initialized('platforms_service')
        
        # Create the delete target platform model
        delete_platform = ArkPCloudDeleteTargetPlatform(
            target_platform_id=target_platform_id
        )
        
        # Delete the target platform using SDK in executor
        await self._run_in_executor(
            lambda: self.platforms_service.delete_target_platform(
                delete_target_platform=delete_platform
            )
        )

        self.logger.info(f"Target platform deleted successfully: {target_platform_id}")
        return {
            "target_platform_id": target_platform_id,
            "status": "deleted"
        }

    @handle_sdk_errors("calculating platform statistics")
    async def get_platform_statistics(self, **kwargs) -> ArkPCloudPlatformStatistics:
        """Calculate comprehensive platform statistics using ark-sdk-python"""
        self._ensure_service_initialized('platforms_service')

        # Get platform statistics using SDK in executor
        stats = await self._run_in_executor(
            lambda: self.platforms_service.platforms_stats()
        )

        self.logger.info(f"Platform statistics calculated: {stats.platforms_count} total platforms")
        return stats

    @handle_sdk_errors("calculating target platform statistics")
    async def get_target_platform_statistics(self, **kwargs) -> ArkPCloudTargetPlatformStatistics:
        """Calculate comprehensive target platform statistics using ark-sdk-python"""
        self._ensure_service_initialized('platforms_service')

        # Get target platform statistics using SDK in executor
        stats = await self._run_in_executor(
            lambda: self.platforms_service.target_platforms_stats()
        )

        self.logger.info(f"Target platform statistics calculated: {stats.target_platforms_count} total target platforms")
        return stats

    # Session Monitoring Methods using ArkSMService
    
    @handle_sdk_errors("listing sessions")
    async def list_sessions(self, **kwargs) -> List[ArkSMSession]:
        """List recent sessions using ArkSMService"""
        self._ensure_service_initialized('sm_service')
        
        # Use default filter for recent sessions (last 24 hours)
        from datetime import datetime, timedelta
        start_time_from = (datetime.utcnow() - timedelta(days=1)).isoformat(timespec='seconds') + 'Z'
        default_search = f'startTime ge {start_time_from}'
        
        sessions_filter = ArkSMSessionsFilter(search=default_search)

        # Get sessions using SDK in executor
        pages = await self._run_in_executor(
            lambda: list(self.sm_service.list_sessions_by(sessions_filter))
        )

        # Flatten pagination and return Pydantic models
        sessions = [session for page in pages for session in page.items]

        self.logger.info(f"Retrieved {len(sessions)} sessions using ArkSMService")
        return sessions

    @handle_sdk_errors("listing sessions by filter")
    async def list_sessions_by_filter(self, search: Optional[str] = None, **kwargs) -> List[ArkSMSession]:
        """List sessions with advanced filtering using ArkSMService"""
        self._ensure_service_initialized('sm_service')

        # Create filter with search query - use default if none provided
        if search is None:
            from datetime import datetime, timedelta
            start_time_from = (datetime.utcnow() - timedelta(days=1)).isoformat(timespec='seconds') + 'Z'
            search = f'startTime ge {start_time_from}'

        sessions_filter = ArkSMSessionsFilter(search=search)

        # Get sessions using SDK in executor
        pages = await self._run_in_executor(
            lambda: list(self.sm_service.list_sessions_by(sessions_filter))
        )

        # Flatten pagination and return Pydantic models
        sessions = [session for page in pages for session in page.items]

        self.logger.info(f"Retrieved {len(sessions)} filtered sessions using ArkSMService")
        return sessions

    @handle_sdk_errors("getting session details")
    async def get_session_details(self, session_id: str, **kwargs) -> ArkSMSession:
        """Get detailed information about a specific session using ArkSMService"""
        self._ensure_service_initialized('sm_service')
        
        # Get session details using SDK in executor
        get_session = ArkSMGetSession(session_id=session_id)
        session = await self._run_in_executor(
            lambda: self.sm_service.session(get_session)
        )

        self.logger.info(f"Retrieved session details for ID: {session_id} using ArkSMService")
        return session

    @handle_sdk_errors("listing session activities")
    async def list_session_activities(self, session_id: str, **kwargs) -> List[ArkSMSessionActivity]:
        """List activities for a specific session using ArkSMService"""
        self._ensure_service_initialized('sm_service')
        
        # Get session activities using SDK in executor
        get_session_activities = ArkSMGetSessionActivities(session_id=session_id)
        pages = await self._run_in_executor(
            lambda: list(self.sm_service.list_session_activities(get_session_activities))
        )

        # Flatten pagination and return Pydantic models
        activities = [activity for page in pages for activity in page.items]

        self.logger.info(f"Retrieved {len(activities)} activities for session: {session_id} using ArkSMService")
        return activities

    @handle_sdk_errors("counting sessions")
    async def count_sessions(self, search: Optional[str] = None, **kwargs) -> Any:
        """Count sessions with optional filtering using ArkSMService"""
        self._ensure_service_initialized('sm_service')
        
        # Create filter with search query - use default if none provided
        if search is None:
            from datetime import datetime, timedelta
            start_time_from = (datetime.utcnow() - timedelta(days=1)).isoformat(timespec='seconds') + 'Z'
            search = f'startTime ge {start_time_from}'
        
        sessions_filter = ArkSMSessionsFilter(search=search)

        # Get session count using SDK in executor
        count = await self._run_in_executor(
            lambda: self.sm_service.count_sessions_by(sessions_filter)
        )

        self.logger.info(f"Counted {count} sessions using ArkSMService")
        return {"count": count, "filter": search}

    @handle_sdk_errors("getting session statistics")
    async def get_session_statistics(self, **kwargs) -> ArkSMSessionStatistics:
        """Get general session statistics using ArkSMService"""
        self._ensure_service_initialized('sm_service')

        # Get session statistics using SDK in executor
        stats = await self._run_in_executor(
            lambda: self.sm_service.sessions_stats()
        )

        self.logger.info(f"Retrieved session statistics using ArkSMService")
        return stats

    # Health check - Using SDK services
    async def health_check(self) -> Any:
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
    def _flatten_platform_structure(self, platform_data: Dict[str, Any]) -> Any:
        """Flatten nested platform structure from list API into a single level."""
        result = {}
        for section_name, section_data in platform_data.items():
            if isinstance(section_data, dict):
                result.update(section_data)  # Flatten nested dictionaries
            else:
                result[section_name] = section_data
        return result

    def _merge_platform_data(self, basic_data: Dict[str, Any], details_data: Dict[str, Any]) -> Any:
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

    # Application Management - Using ark-sdk-python
    @handle_sdk_errors("listing applications")
    async def list_applications(self, **kwargs) -> List[Dict[str, Any]]:
        """List applications from CyberArk Privilege Cloud using ark-sdk-python"""
        self._ensure_service_initialized('applications_service')
        
        # Create filter if parameters provided
        app_filter = None
        filter_params = {}
        
        if 'location' in kwargs:
            filter_params['location'] = kwargs['location']
        if 'only_enabled' in kwargs:
            filter_params['only_enabled'] = kwargs['only_enabled']
        if 'business_owner_name' in kwargs:
            filter_params['business_owner_name'] = kwargs['business_owner_name']
        if 'business_owner_email' in kwargs:
            filter_params['business_owner_email'] = kwargs['business_owner_email']
            
        try:
            if filter_params:
                app_filter = ArkPCloudApplicationsFilter(**filter_params)
                applications = await self._run_in_executor(
                    self.applications_service.list_applications_by, app_filter
                )
            else:
                applications = await self._run_in_executor(
                    self.applications_service.list_applications
                )
            
            self.logger.info(f"Applications listed successfully: {len(applications)} found")
            
            # Convert to dict format to avoid Pydantic validation issues with null ExpirationDate fields
            return [app.model_dump() if hasattr(app, 'model_dump') else app for app in applications]
            
        except Exception as e:
            # Handle SDK validation errors by bypassing strict validation
            error_str = str(e).lower()
            error_type = type(e).__name__.lower()
            if (("validationerror" in error_str or "validation error" in error_str or "validationerror" in error_type) 
                and "expirationdate" in error_str):
                self.logger.warning(f"SDK validation failed due to null ExpirationDate fields, attempting raw API call workaround: {e}")
                
                # Import necessary modules for direct API call
                import json
                import httpx
                
                # Get authentication token
                auth_token = await self._run_in_executor(
                    lambda: self.applications_service._isp_auth.token.token.get_secret_value()
                )
                
                # Make direct API call
                async with httpx.AsyncClient() as client:
                    headers = {
                        'Authorization': f'Bearer {auth_token}',
                        'Content-Type': 'application/json'
                    }
                    
                    # Build API URL using helper method
                    api_url = self._build_api_url('applications_service', 'Applications')
                    
                    response = await client.get(api_url, headers=headers)
                    if response.status_code == 200:
                        raw_data = response.json()
                        applications_list = raw_data.get('Applications', [])
                        
                        self.logger.info(f"Retrieved {len(applications_list)} applications via direct API call")
                        return applications_list
                    else:
                        raise Exception(f"API call failed with status {response.status_code}")
            else:
                # Re-raise non-validation errors
                raise
    
    @handle_sdk_errors("getting application details")
    async def get_application_details(self, app_id: str) -> ArkPCloudApplication:
        """Get detailed application information using ark-sdk-python"""
        self._ensure_service_initialized('applications_service')
        
        get_app = ArkPCloudGetApplication(app_id=app_id)
        application = await self._run_in_executor(
            lambda: self.applications_service.application(get_app)
        )

        self.logger.info(f"Application details retrieved successfully for: {app_id}")
        return application
    
    @handle_sdk_errors("adding application")
    async def add_application(
        self,
        app_id: str,
        description: str = "",
        location: str = "",
        access_permitted_from: Optional[str] = None,
        access_permitted_to: Optional[str] = None,
        expiration_date: Optional[str] = None,
        disabled: bool = False,
        business_owner_first_name: str = "",
        business_owner_last_name: str = "",
        business_owner_email: str = "",
        business_owner_phone: str = "",
        **kwargs
    ) -> Any:
        """Add new application using ark-sdk-python"""
        self._ensure_service_initialized('applications_service')
        
        add_app_params = {
            'app_id': app_id,
            'description': description,
            'location': location,
            'disabled': disabled,
            'business_owner_first_name': business_owner_first_name,
            'business_owner_last_name': business_owner_last_name,
            'business_owner_email': business_owner_email,
            'business_owner_phone': business_owner_phone
        }
        
        if access_permitted_from:
            add_app_params['access_permitted_from'] = access_permitted_from
        if access_permitted_to:
            add_app_params['access_permitted_to'] = access_permitted_to
        if expiration_date:
            add_app_params['expiration_date'] = expiration_date
            
        add_app = ArkPCloudAddApplication(**add_app_params)
        application = await self._run_in_executor(
            lambda: self.applications_service.add_application(add_app)
        )

        self.logger.info(f"Application added successfully: {app_id}")
        return application
    
    @handle_sdk_errors("deleting application")
    async def delete_application(self, app_id: str, **kwargs) -> Any:
        """Delete application using ark-sdk-python"""
        self._ensure_service_initialized('applications_service')
        
        delete_app = ArkPCloudDeleteApplication(app_id=app_id)
        await self._run_in_executor(
            lambda: self.applications_service.delete_application(delete_app)
        )

        self.logger.info(f"Application deleted successfully: {app_id}")
        return {"app_id": app_id, "status": "deleted"}
    
    @handle_sdk_errors("listing application auth methods")
    async def list_application_auth_methods(self, app_id: str, **kwargs) -> List[ArkPCloudApplicationAuthMethod]:
        """List authentication methods for an application using ark-sdk-python"""
        self._ensure_service_initialized('applications_service')
        
        # Create filter if auth_types provided
        if 'auth_types' in kwargs:
            auth_filter = ArkPCloudApplicationAuthMethodsFilter(
                app_id=app_id,
                auth_types=kwargs['auth_types']
            )
            auth_methods = await self._run_in_executor(
                lambda: self.applications_service.list_application_auth_methods_by(auth_filter)
            )
        else:
            list_auth_methods = ArkPCloudListApplicationAuthMethods(app_id=app_id)
            auth_methods = await self._run_in_executor(
                lambda: self.applications_service.list_application_auth_methods(list_auth_methods)
            )

        self.logger.info(f"Application auth methods listed successfully for {app_id}: {len(auth_methods)} found")
        return auth_methods
    
    @handle_sdk_errors("getting application auth method details")
    async def get_application_auth_method_details(self, app_id: str, auth_id: str) -> ArkPCloudApplicationAuthMethod:
        """Get detailed application auth method information using ark-sdk-python"""
        self._ensure_service_initialized('applications_service')
        
        get_auth_method = ArkPCloudGetApplicationAuthMethod(app_id=app_id, auth_id=auth_id)
        auth_method = await self._run_in_executor(
            lambda: self.applications_service.application_auth_method(get_auth_method)
        )

        self.logger.info(f"Application auth method details retrieved successfully for {app_id}/{auth_id}")
        return auth_method
    
    @handle_sdk_errors("adding application auth method")
    async def add_application_auth_method(
        self,
        app_id: str,
        auth_type: str,
        auth_value: str = "",
        is_folder: bool = False,
        allow_internal_scripts: bool = False,
        comment: str = "",
        namespace: str = "",
        image: str = "",
        env_var_name: str = "",
        env_var_value: str = "",
        subject: Optional[List[Dict[str, str]]] = None,
        issuer: Optional[List[Dict[str, str]]] = None,
        subject_alternative_name: Optional[List[Dict[str, str]]] = None,
        **kwargs
    ) -> Any:
        """Add authentication method to application using ark-sdk-python"""
        self._ensure_service_initialized('applications_service')
        
        # Convert certificate fields to proper key-value objects if provided
        def convert_cert_field(field_data, default_key):
            """Convert certificate field data to ArkPCloudApplicationAuthMethodCertKeyVal objects"""
            cert_list = []
            if field_data is not None:
                for item in field_data:
                    if isinstance(item, dict):
                        # Create ArkPCloudApplicationAuthMethodCertKeyVal object from dict
                        cert_list.append(ArkPCloudApplicationAuthMethodCertKeyVal(**item))
                    elif isinstance(item, str):
                        # Handle legacy string format - create a basic key-value pair
                        cert_list.append(ArkPCloudApplicationAuthMethodCertKeyVal(key=default_key, value=item))
            return cert_list
        
        cert_subject = convert_cert_field(subject, "CN")
        cert_issuer = convert_cert_field(issuer, "CN")
        cert_subject_alternative_name = convert_cert_field(subject_alternative_name, "DNS")
        
        add_auth_params = {
            'app_id': app_id,
            'auth_type': auth_type,
            'auth_value': auth_value,
            'is_folder': is_folder,
            'allow_internal_scripts': allow_internal_scripts,
            'comment': comment,
            'namespace': namespace,
            'image': image,
            'env_var_name': env_var_name,
            'env_var_value': env_var_value,
            'subject': cert_subject,
            'issuer': cert_issuer,
            'subject_alternative_name': cert_subject_alternative_name
        }
        
        add_auth_method = ArkPCloudAddApplicationAuthMethod(**add_auth_params)
        auth_method = await self._run_in_executor(
            self.applications_service.add_application_auth_method, add_auth_method
        )
        
        self.logger.info(f"Application auth method added successfully to {app_id}")
        return auth_method
    
    @handle_sdk_errors("deleting application auth method")
    async def delete_application_auth_method(self, app_id: str, auth_id: str, **kwargs) -> Any:
        """Delete application authentication method using ark-sdk-python"""
        self._ensure_service_initialized('applications_service')
        
        delete_auth_method = ArkPCloudDeleteApplicationAuthMethod(app_id=app_id, auth_id=auth_id)
        await self._run_in_executor(
            lambda: self.applications_service.delete_application_auth_method(delete_auth_method)
        )

        self.logger.info(f"Application auth method deleted successfully: {app_id}/{auth_id}")
        return {"app_id": app_id, "auth_id": auth_id, "status": "deleted"}
    
    @handle_sdk_errors("getting applications statistics")
    async def get_applications_stats(self, **kwargs) -> Dict[str, Any]:
        """Get applications statistics using ark-sdk-python"""
        self._ensure_service_initialized('applications_service')
        
        try:
            stats = await self._run_in_executor(
                self.applications_service.applications_stats
            )
            
            self.logger.info("Applications statistics retrieved successfully")
            
            # Convert to dict format to avoid Pydantic validation issues with null ExpirationDate fields
            return stats.model_dump() if hasattr(stats, 'model_dump') else stats
            
        except Exception as e:
            # Handle SDK validation errors by bypassing strict validation
            error_str = str(e).lower()
            error_type = type(e).__name__.lower()
            if (("validationerror" in error_str or "validation error" in error_str or "validationerror" in error_type) 
                and "expirationdate" in error_str):
                self.logger.warning(f"SDK validation failed due to null ExpirationDate fields, attempting raw API call workaround: {e}")
                
                # Import necessary modules for direct API call
                import json
                import httpx
                
                # Get authentication token
                auth_token = await self._run_in_executor(
                    lambda: self.applications_service._isp_auth.token.token.get_secret_value()
                )
                
                # Make direct API call
                async with httpx.AsyncClient() as client:
                    headers = {
                        'Authorization': f'Bearer {auth_token}',
                        'Content-Type': 'application/json'
                    }
                    
                    # Build API URL using helper method
                    api_url = self._build_api_url('applications_service', 'Applications/Stats')
                    
                    response = await client.get(api_url, headers=headers)
                    if response.status_code == 200:
                        raw_data = response.json()
                        
                        self.logger.info("Retrieved applications statistics via direct API call")
                        return raw_data
                    else:
                        raise Exception(f"API call failed with status {response.status_code}")
            else:
                # Re-raise non-validation errors
                raise

