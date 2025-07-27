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
    ArkPCloudReconcileAccountCredentials,
    ArkPCloudUpdateAccount,
    ArkPCloudDeleteAccount
)

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
    ArkPCloudApplicationAuthMethodsFilter
)

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
            elif service_name == 'applications_service':
                self.applications_service = ArkPCloudApplicationsService(sdk_auth)
            elif service_name == 'sm_service':
                self.sm_service = ArkSMService(sdk_auth)

    def reinitialize_services(self):
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
    ) -> Dict[str, Any]:
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
        result = self.accounts_service.update_account(
            account_id=account_id,
            update_account=update_account
        )
        
        self.logger.info(f"Successfully updated account ID: {account_id}")
        return result.model_dump()

    @handle_sdk_errors("deleting account")
    async def delete_account(self, account_id: str, **kwargs) -> Dict[str, Any]:
        """Delete an existing account using ark-sdk-python"""
        self._ensure_service_initialized('accounts_service')
        
        # Validate required parameters
        if not account_id or not isinstance(account_id, str):
            raise ValueError("account_id is required and must be a non-empty string")
        
        # Create the delete account model
        delete_account = ArkPCloudDeleteAccount(account_id=account_id)
        
        # Delete the account using SDK
        result = self.accounts_service.delete_account(
            account_id=account_id,
            delete_account=delete_account
        )
        
        self.logger.info(f"Successfully deleted account ID: {account_id}")
        return result.model_dump()

    # Advanced Account Search and Filtering - Using ark-sdk-python
    @handle_sdk_errors("filtering accounts by platform group")
    async def filter_accounts_by_platform_group(self, platform_group: str, **kwargs) -> List[Dict[str, Any]]:
        """Filter accounts by platform type grouping (Windows, Linux, Database, etc.)"""
        self._ensure_service_initialized('accounts_service')
        
        # Get all accounts
        pages = list(self.accounts_service.list_accounts())
        all_accounts = [acc.model_dump() for page in pages for acc in page.items]
        
        # Define platform group mappings
        platform_groups = {
            "Windows": ["WindowsDomainAccount", "WindowsServerLocalAccount", "WindowsDesktopLocalAccount"],
            "Linux": ["LinuxAccount", "UnixAccount", "UnixSSH"],
            "Database": ["SQLServerAccount", "OracleAccount", "MySQLAccount", "PostgreSQLAccount"],
            "Network": ["CiscoAccount", "JuniperAccount", "F5Account"],
            "Cloud": ["AWSAccount", "AzureAccount", "GCPAccount"]
        }
        
        # Filter by platform group
        group_platforms = platform_groups.get(platform_group, [platform_group])
        filtered_accounts = [
            acc for acc in all_accounts 
            if any(platform in acc.get("platformId", "") for platform in group_platforms)
        ]
        
        self.logger.info(f"Found {len(filtered_accounts)} accounts in platform group '{platform_group}'")
        return filtered_accounts

    @handle_sdk_errors("filtering accounts by environment")
    async def filter_accounts_by_environment(self, environment: str, **kwargs) -> List[Dict[str, Any]]:
        """Filter accounts by environment (production, staging, development, etc.)"""
        self._ensure_service_initialized('accounts_service')
        
        # Get all accounts
        pages = list(self.accounts_service.list_accounts())
        all_accounts = [acc.model_dump() for page in pages for acc in page.items]
        
        # Filter by environment in address field
        filtered_accounts = [
            acc for acc in all_accounts 
            if environment.lower() in acc.get("address", "").lower()
        ]
        
        self.logger.info(f"Found {len(filtered_accounts)} accounts in '{environment}' environment")
        return filtered_accounts

    @handle_sdk_errors("filtering accounts by management status")
    async def filter_accounts_by_management_status(self, auto_managed: bool = True, **kwargs) -> List[Dict[str, Any]]:
        """Filter accounts by automatic password management status"""
        self._ensure_service_initialized('accounts_service')
        
        # Get all accounts
        pages = list(self.accounts_service.list_accounts())
        all_accounts = [acc.model_dump() for page in pages for acc in page.items]
        
        # Filter by management status
        filtered_accounts = [
            acc for acc in all_accounts 
            if acc.get("secretManagement", {}).get("automaticManagementEnabled", False) == auto_managed
        ]
        
        status_text = "automatically managed" if auto_managed else "manually managed"
        self.logger.info(f"Found {len(filtered_accounts)} {status_text} accounts")
        return filtered_accounts

    @handle_sdk_errors("grouping accounts by safe")
    async def group_accounts_by_safe(self, **kwargs) -> Dict[str, List[Dict[str, Any]]]:
        """Group accounts by safe name"""
        self._ensure_service_initialized('accounts_service')
        
        # Get all accounts
        pages = list(self.accounts_service.list_accounts())
        all_accounts = [acc.model_dump() for page in pages for acc in page.items]
        
        # Group by safe
        grouped_accounts = {}
        for acc in all_accounts:
            safe_name = acc.get("safeName", "Unknown")
            if safe_name not in grouped_accounts:
                grouped_accounts[safe_name] = []
            grouped_accounts[safe_name].append(acc)
        
        self.logger.info(f"Grouped {len(all_accounts)} accounts into {len(grouped_accounts)} safes")
        return grouped_accounts

    @handle_sdk_errors("grouping accounts by platform")
    async def group_accounts_by_platform(self, **kwargs) -> Dict[str, List[Dict[str, Any]]]:
        """Group accounts by platform type"""
        self._ensure_service_initialized('accounts_service')
        
        # Get all accounts
        pages = list(self.accounts_service.list_accounts())
        all_accounts = [acc.model_dump() for page in pages for acc in page.items]
        
        # Group by platform
        grouped_accounts = {}
        for acc in all_accounts:
            platform_id = acc.get("platformId", "Unknown")
            if platform_id not in grouped_accounts:
                grouped_accounts[platform_id] = []
            grouped_accounts[platform_id].append(acc)
        
        self.logger.info(f"Grouped {len(all_accounts)} accounts into {len(grouped_accounts)} platform types")
        return grouped_accounts

    @handle_sdk_errors("analyzing account distribution")
    async def analyze_account_distribution(self, **kwargs) -> Dict[str, Any]:
        """Analyze distribution of accounts across safes, platforms, and environments"""
        self._ensure_service_initialized('accounts_service')
        
        # Get all accounts
        pages = list(self.accounts_service.list_accounts())
        all_accounts = [acc.model_dump() for page in pages for acc in page.items]
        
        # Analyze distribution
        safe_counts = {}
        platform_counts = {}
        env_counts = {}
        auto_managed_count = 0
        
        for acc in all_accounts:
            # Count by safe
            safe_name = acc.get("safeName", "Unknown")
            safe_counts[safe_name] = safe_counts.get(safe_name, 0) + 1
            
            # Count by platform
            platform_id = acc.get("platformId", "Unknown")
            platform_counts[platform_id] = platform_counts.get(platform_id, 0) + 1
            
            # Count by environment (extracted from address)
            address = acc.get("address", "")
            for env in ["production", "staging", "development", "test"]:
                if env in address.lower():
                    env_counts[env] = env_counts.get(env, 0) + 1
                    break
            
            # Count auto-managed
            if acc.get("secretManagement", {}).get("automaticManagementEnabled", False):
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
    ) -> List[Dict[str, Any]]:
        """Search accounts using multiple pattern criteria"""
        self._ensure_service_initialized('accounts_service')
        
        # Get all accounts
        pages = list(self.accounts_service.list_accounts())
        all_accounts = [acc.model_dump() for page in pages for acc in page.items]
        
        # Apply filters
        filtered_accounts = all_accounts
        
        if username_pattern:
            filtered_accounts = [
                acc for acc in filtered_accounts 
                if username_pattern.lower() in acc.get("userName", "").lower()
            ]
        
        if address_pattern:
            filtered_accounts = [
                acc for acc in filtered_accounts 
                if address_pattern.lower() in acc.get("address", "").lower()
            ]
        
        if environment:
            filtered_accounts = [
                acc for acc in filtered_accounts 
                if environment.lower() in acc.get("address", "").lower()
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
                if any(platform in acc.get("platformId", "") for platform in group_platforms)
            ]
        
        self.logger.info(f"Found {len(filtered_accounts)} accounts matching pattern criteria")
        return filtered_accounts

    @handle_sdk_errors("counting accounts by criteria")
    async def count_accounts_by_criteria(self, **kwargs) -> Dict[str, Any]:
        """Count accounts by various criteria"""
        self._ensure_service_initialized('accounts_service')
        
        # Get all accounts
        pages = list(self.accounts_service.list_accounts())
        all_accounts = [acc.model_dump() for page in pages for acc in page.items]
        
        # Count by criteria
        total = len(all_accounts)
        auto_managed = sum(1 for acc in all_accounts 
                          if acc.get("secretManagement", {}).get("automaticManagementEnabled", False))
        manual_managed = total - auto_managed
        
        # Count by platform
        platform_counts = {}
        for acc in all_accounts:
            platform_id = acc.get("platformId", "Unknown")
            platform_counts[platform_id] = platform_counts.get(platform_id, 0) + 1
        
        # Count by safe
        safe_counts = {}
        for acc in all_accounts:
            safe_name = acc.get("safeName", "Unknown")
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

    @handle_sdk_errors("adding safe")
    async def add_safe(
        self,
        safe_name: str,
        description: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Add a new safe to CyberArk Privilege Cloud using ark-sdk-python"""
        self._ensure_service_initialized('safes_service')
        
        # Create the add safe model
        add_safe = ArkPCloudAddSafe(
            safe_name=safe_name,
            description=description
        )
        
        # Add the safe using SDK
        created_safe = self.safes_service.add_safe(safe=add_safe)
        
        self.logger.info(f"Successfully created safe: {safe_name}")
        return created_safe.model_dump()

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
    ) -> Dict[str, Any]:
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
        
        # Update the safe using SDK
        updated_safe = self.safes_service.update_safe(update_safe=update_safe)
        
        self.logger.info(f"Successfully updated safe: {safe_id}")
        return updated_safe.model_dump()

    @handle_sdk_errors("deleting safe")
    async def delete_safe(
        self,
        safe_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Delete a safe from CyberArk Privilege Cloud using ark-sdk-python"""
        self._ensure_service_initialized('safes_service')
        
        # Create the delete safe model
        delete_safe = ArkPCloudDeleteSafe(safe_id=safe_id)
        
        # Delete the safe using SDK (returns None)
        self.safes_service.delete_safe(delete_safe=delete_safe)
        
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
    ) -> List[Dict[str, Any]]:
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
            pages = list(self.safes_service.list_safe_members_by(filters))
        else:
            # Use basic list
            list_members = ArkPCloudListSafeMembers(safe_id=safe_name)
            pages = list(self.safes_service.list_safe_members(list_members))
        
        # Convert SDK models to dicts and flatten pagination
        members = [member.model_dump() for page in pages for member in page.items]
        
        self.logger.info(f"Retrieved {len(members)} safe members for safe: {safe_name} using ark-sdk-python")
        return members

    @handle_sdk_errors("getting safe member details")
    async def get_safe_member_details(self, safe_name: str, member_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific safe member using ark-sdk-python"""
        self._ensure_service_initialized('safes_service')
        
        # Create the get safe member model
        get_member = ArkPCloudGetSafeMember(safe_id=safe_name, member_name=member_name)
        
        # Get safe member details using SDK
        member = self.safes_service.safe_member(get_member)
        
        self.logger.info(f"Retrieved safe member details for: {member_name} in safe: {safe_name} using ark-sdk-python")
        return member.model_dump()

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
    ) -> Dict[str, Any]:
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
        
        # Add the safe member using SDK
        created_member = self.safes_service.add_safe_member(add_member)
        
        self.logger.info(f"Successfully added member {member_name} to safe: {safe_name}")
        return created_member.model_dump()

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
    ) -> Dict[str, Any]:
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
        
        # Update the safe member using SDK
        updated_member = self.safes_service.update_safe_member(update_member)
        
        self.logger.info(f"Successfully updated member {member_name} in safe: {safe_name}")
        return updated_member.model_dump()

    @handle_sdk_errors("removing safe member")
    async def remove_safe_member(
        self,
        safe_name: str,
        member_name: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Remove a member from a safe using ark-sdk-python"""
        self._ensure_service_initialized('safes_service')
        
        # Create the delete safe member model
        delete_member = ArkPCloudDeleteSafeMember(safe_id=safe_name, member_name=member_name)
        
        # Delete the safe member using SDK (returns None)
        self.safes_service.delete_safe_member(delete_member)
        
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

    @handle_sdk_errors("exporting platform")
    async def export_platform(self, platform_id: str, output_folder: str, **kwargs) -> Dict[str, Any]:
        """Export platform configuration package using ark-sdk-python"""
        self._ensure_service_initialized('platforms_service')
        
        # Create the export platform model
        export_platform = ArkPCloudExportPlatform(
            platform_id=platform_id,
            output_folder=output_folder
        )
        
        # Export the platform using SDK
        self.platforms_service.export_platform(export_platform=export_platform)
        
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
    ) -> Dict[str, Any]:
        """Duplicate/clone a target platform using ark-sdk-python"""
        self._ensure_service_initialized('platforms_service')
        
        # Create the duplicate target platform model
        duplicate_platform = ArkPCloudDuplicateTargetPlatform(
            target_platform_id=target_platform_id,
            name=name,
            description=description
        )
        
        # Duplicate the target platform using SDK
        duplicated_platform = self.platforms_service.duplicate_target_platform(
            duplicate_target_platform=duplicate_platform
        )
        
        self.logger.info(f"Target platform duplicated successfully: {target_platform_id} -> {name}")
        return duplicated_platform.model_dump()

    @handle_sdk_errors("activating target platform")
    async def activate_target_platform(self, target_platform_id: int, **kwargs) -> Dict[str, Any]:
        """Activate/enable target platform using ark-sdk-python"""
        self._ensure_service_initialized('platforms_service')
        
        # Create the activate target platform model
        activate_platform = ArkPCloudActivateTargetPlatform(
            target_platform_id=target_platform_id
        )
        
        # Activate the target platform using SDK
        self.platforms_service.activate_target_platform(
            activate_target_platform=activate_platform
        )
        
        self.logger.info(f"Target platform activated successfully: {target_platform_id}")
        return {
            "target_platform_id": target_platform_id,
            "status": "activated"
        }

    @handle_sdk_errors("deactivating target platform")
    async def deactivate_target_platform(self, target_platform_id: int, **kwargs) -> Dict[str, Any]:
        """Deactivate/disable target platform using ark-sdk-python"""
        self._ensure_service_initialized('platforms_service')
        
        # Create the deactivate target platform model
        deactivate_platform = ArkPCloudDeactivateTargetPlatform(
            target_platform_id=target_platform_id
        )
        
        # Deactivate the target platform using SDK
        self.platforms_service.deactivate_target_platform(
            deactivate_target_platform=deactivate_platform
        )
        
        self.logger.info(f"Target platform deactivated successfully: {target_platform_id}")
        return {
            "target_platform_id": target_platform_id,
            "status": "deactivated"
        }

    @handle_sdk_errors("deleting target platform")
    async def delete_target_platform(self, target_platform_id: int, **kwargs) -> Dict[str, Any]:
        """Delete target platform using ark-sdk-python"""
        self._ensure_service_initialized('platforms_service')
        
        # Create the delete target platform model
        delete_platform = ArkPCloudDeleteTargetPlatform(
            target_platform_id=target_platform_id
        )
        
        # Delete the target platform using SDK
        self.platforms_service.delete_target_platform(
            delete_target_platform=delete_platform
        )
        
        self.logger.info(f"Target platform deleted successfully: {target_platform_id}")
        return {
            "target_platform_id": target_platform_id,
            "status": "deleted"
        }

    @handle_sdk_errors("calculating platform statistics")
    async def get_platform_statistics(self, **kwargs) -> Dict[str, Any]:
        """Calculate comprehensive platform statistics using ark-sdk-python"""
        self._ensure_service_initialized('platforms_service')
        
        # Get platform statistics using SDK
        stats = self.platforms_service.platforms_stats()
        
        self.logger.info(f"Platform statistics calculated: {stats.platforms_count} total platforms")
        return stats.model_dump()

    @handle_sdk_errors("calculating target platform statistics")
    async def get_target_platform_statistics(self, **kwargs) -> Dict[str, Any]:
        """Calculate comprehensive target platform statistics using ark-sdk-python"""
        self._ensure_service_initialized('platforms_service')
        
        # Get target platform statistics using SDK
        stats = self.platforms_service.target_platforms_stats()
        
        self.logger.info(f"Target platform statistics calculated: {stats.target_platforms_count} total target platforms")
        return stats.model_dump()

    # Session Monitoring Methods using ArkSMService
    
    @handle_sdk_errors("listing sessions")
    async def list_sessions(self, **kwargs) -> List[Dict[str, Any]]:
        """List recent sessions using ArkSMService"""
        self._ensure_service_initialized('sm_service')
        
        # Use default filter for recent sessions (last 24 hours)
        from datetime import datetime, timedelta
        start_time_from = (datetime.utcnow() - timedelta(days=1)).isoformat(timespec='seconds') + 'Z'
        default_search = f'startTime ge {start_time_from}'
        
        sessions_filter = ArkSMSessionsFilter(search=default_search)
        
        # Get sessions using SDK
        pages = list(self.sm_service.list_sessions_by(sessions_filter))
        
        # Convert SDK models to dicts and flatten pagination
        sessions = [session.model_dump() for page in pages for session in page.items]
        
        self.logger.info(f"Retrieved {len(sessions)} sessions using ArkSMService")
        return sessions

    @handle_sdk_errors("listing sessions by filter")
    async def list_sessions_by_filter(self, search: Optional[str] = None, **kwargs) -> List[Dict[str, Any]]:
        """List sessions with advanced filtering using ArkSMService"""
        self._ensure_service_initialized('sm_service')
        
        # Create filter with search query - use default if none provided
        if search is None:
            from datetime import datetime, timedelta
            start_time_from = (datetime.utcnow() - timedelta(days=1)).isoformat(timespec='seconds') + 'Z'
            search = f'startTime ge {start_time_from}'
        
        sessions_filter = ArkSMSessionsFilter(search=search)
        
        # Get sessions using SDK
        pages = list(self.sm_service.list_sessions_by(sessions_filter))
        
        # Convert SDK models to dicts and flatten pagination
        sessions = [session.model_dump() for page in pages for session in page.items]
        
        self.logger.info(f"Retrieved {len(sessions)} filtered sessions using ArkSMService")
        return sessions

    @handle_sdk_errors("getting session details")
    async def get_session_details(self, session_id: str, **kwargs) -> Dict[str, Any]:
        """Get detailed information about a specific session using ArkSMService"""
        self._ensure_service_initialized('sm_service')
        
        # Get session details using SDK
        get_session = ArkSMGetSession(session_id=session_id)
        session = self.sm_service.session(get_session)
        
        self.logger.info(f"Retrieved session details for ID: {session_id} using ArkSMService")
        return session.model_dump()

    @handle_sdk_errors("listing session activities")
    async def list_session_activities(self, session_id: str, **kwargs) -> List[Dict[str, Any]]:
        """List activities for a specific session using ArkSMService"""
        self._ensure_service_initialized('sm_service')
        
        # Get session activities using SDK
        get_session_activities = ArkSMGetSessionActivities(session_id=session_id)
        pages = list(self.sm_service.list_session_activities(get_session_activities))
        
        # Convert SDK models to dicts and flatten pagination
        activities = [activity.model_dump() for page in pages for activity in page.items]
        
        self.logger.info(f"Retrieved {len(activities)} activities for session: {session_id} using ArkSMService")
        return activities

    @handle_sdk_errors("counting sessions")
    async def count_sessions(self, search: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Count sessions with optional filtering using ArkSMService"""
        self._ensure_service_initialized('sm_service')
        
        # Create filter with search query - use default if none provided
        if search is None:
            from datetime import datetime, timedelta
            start_time_from = (datetime.utcnow() - timedelta(days=1)).isoformat(timespec='seconds') + 'Z'
            search = f'startTime ge {start_time_from}'
        
        sessions_filter = ArkSMSessionsFilter(search=search)
        
        # Get session count using SDK
        count = self.sm_service.count_sessions_by(sessions_filter)
        
        self.logger.info(f"Counted {count} sessions using ArkSMService")
        return {"count": count, "filter": search}

    @handle_sdk_errors("getting session statistics")
    async def get_session_statistics(self, **kwargs) -> Dict[str, Any]:
        """Get general session statistics using ArkSMService"""
        self._ensure_service_initialized('sm_service')
        
        # Get session statistics using SDK
        stats = self.sm_service.sessions_stats()
        
        self.logger.info(f"Retrieved session statistics using ArkSMService")
        return stats.model_dump()

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
            
        if filter_params:
            app_filter = ArkPCloudApplicationsFilter(**filter_params)
            applications = self.applications_service.list_applications_by(app_filter)
        else:
            applications = self.applications_service.list_applications()
        
        self.logger.info(f"Applications listed successfully: {len(applications)} found")
        return [app.model_dump() for app in applications]
    
    @handle_sdk_errors("getting application details")
    async def get_application_details(self, app_id: str) -> Dict[str, Any]:
        """Get detailed application information using ark-sdk-python"""
        self._ensure_service_initialized('applications_service')
        
        get_app = ArkPCloudGetApplication(app_id=app_id)
        application = self.applications_service.application(get_app)
        
        self.logger.info(f"Application details retrieved successfully for: {app_id}")
        return application.model_dump()
    
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
    ) -> Dict[str, Any]:
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
        application = self.applications_service.add_application(add_app)
        
        self.logger.info(f"Application added successfully: {app_id}")
        return application.model_dump()
    
    @handle_sdk_errors("deleting application")
    async def delete_application(self, app_id: str, **kwargs) -> Dict[str, Any]:
        """Delete application using ark-sdk-python"""
        self._ensure_service_initialized('applications_service')
        
        delete_app = ArkPCloudDeleteApplication(app_id=app_id)
        self.applications_service.delete_application(delete_app)
        
        self.logger.info(f"Application deleted successfully: {app_id}")
        return {"app_id": app_id, "status": "deleted"}
    
    @handle_sdk_errors("listing application auth methods")
    async def list_application_auth_methods(self, app_id: str, **kwargs) -> List[Dict[str, Any]]:
        """List authentication methods for an application using ark-sdk-python"""
        self._ensure_service_initialized('applications_service')
        
        # Create filter if auth_types provided
        if 'auth_types' in kwargs:
            auth_filter = ArkPCloudApplicationAuthMethodsFilter(
                app_id=app_id,
                auth_types=kwargs['auth_types']
            )
            auth_methods = self.applications_service.list_application_auth_methods_by(auth_filter)
        else:
            list_auth_methods = ArkPCloudListApplicationAuthMethods(app_id=app_id)
            auth_methods = self.applications_service.list_application_auth_methods(list_auth_methods)
        
        self.logger.info(f"Application auth methods listed successfully for {app_id}: {len(auth_methods)} found")
        return [method.model_dump() for method in auth_methods]
    
    @handle_sdk_errors("getting application auth method details")
    async def get_application_auth_method_details(self, app_id: str, auth_id: str) -> Dict[str, Any]:
        """Get detailed application auth method information using ark-sdk-python"""
        self._ensure_service_initialized('applications_service')
        
        get_auth_method = ArkPCloudGetApplicationAuthMethod(app_id=app_id, auth_id=auth_id)
        auth_method = self.applications_service.application_auth_method(get_auth_method)
        
        self.logger.info(f"Application auth method details retrieved successfully for {app_id}/{auth_id}")
        return auth_method.model_dump()
    
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
        subject: str = "",
        issuer: str = "",
        subject_alternative_name: str = "",
        **kwargs
    ) -> Dict[str, Any]:
        """Add authentication method to application using ark-sdk-python"""
        self._ensure_service_initialized('applications_service')
        
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
            'subject': subject,
            'issuer': issuer,
            'subject_alternative_name': subject_alternative_name
        }
        
        add_auth_method = ArkPCloudAddApplicationAuthMethod(**add_auth_params)
        auth_method = self.applications_service.add_application_auth_method(add_auth_method)
        
        self.logger.info(f"Application auth method added successfully to {app_id}")
        return auth_method.model_dump()
    
    @handle_sdk_errors("deleting application auth method")
    async def delete_application_auth_method(self, app_id: str, auth_id: str, **kwargs) -> Dict[str, Any]:
        """Delete application authentication method using ark-sdk-python"""
        self._ensure_service_initialized('applications_service')
        
        delete_auth_method = ArkPCloudDeleteApplicationAuthMethod(app_id=app_id, auth_id=auth_id)
        self.applications_service.delete_application_auth_method(delete_auth_method)
        
        self.logger.info(f"Application auth method deleted successfully: {app_id}/{auth_id}")
        return {"app_id": app_id, "auth_id": auth_id, "status": "deleted"}
    
    @handle_sdk_errors("getting applications statistics")
    async def get_applications_stats(self, **kwargs) -> Dict[str, Any]:
        """Get applications statistics using ark-sdk-python"""
        self._ensure_service_initialized('applications_service')
        
        stats = self.applications_service.applications_stats()
        
        self.logger.info("Applications statistics retrieved successfully")
        return stats.model_dump()

