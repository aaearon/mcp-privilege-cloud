#!/usr/bin/env python3
"""
CyberArk Privilege Cloud MCP Server

This server provides tools for interacting with CyberArk Privilege Cloud
through the Model Context Protocol (MCP).
"""

import logging
import os
import sys
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP

# Add the src directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from .server import CyberArkMCPServer
except ImportError:
    # Fallback for direct execution
    from mcp_privilege_cloud.server import CyberArkMCPServer

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv not available, try manual loading
    env_file = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
    if os.path.exists(env_file):
        with open(env_file) as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    if key and value:
                        os.environ[key] = value

# Configure logging
logging.basicConfig(
    level=os.getenv("CYBERARK_LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize the MCP server
mcp = FastMCP("CyberArk Privilege Cloud MCP Server")

# Server instance will be created lazily by tools
server = None

def get_server():
    """Get or create the server instance lazily."""
    global server
    if server is None:
        try:
            server = CyberArkMCPServer.from_environment()
            logger.info("Successfully initialized CyberArk MCP Server")
        except ValueError as e:
            logger.error(f"Failed to initialize server: {e}")
            raise
    return server

def reset_server():
    """Reset the global server instance. Used for testing to ensure clean state."""
    global server
    server = None

async def execute_tool(tool_name: str, *args, **kwargs):
    """Execute a CyberArk tool by calling the corresponding server method."""
    try:
        server_instance = get_server()
        server_method = getattr(server_instance, tool_name)
        result = await server_method(*args, **kwargs)
        logger.info(f"Successfully executed tool: {tool_name}")
        return result
    except Exception as e:
        logger.error(f"Error executing tool '{tool_name}': {e}")
        raise


@mcp.tool()
async def create_account(
    platform_id: str,
    safe_name: str,
    name: Optional[str] = None,
    address: Optional[str] = None,
    user_name: Optional[str] = None,
    secret: Optional[str] = None,
    secret_type: Optional[str] = None,
    platform_account_properties: Optional[Dict[str, Any]] = None,
    secret_management: Optional[Dict[str, Any]] = None,
    remote_machines_access: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a new privileged account in CyberArk Privilege Cloud.
    
    Args:
        platform_id: Platform ID (required) - Examples: "WinServerLocal", "UnixSSH", "Oracle"
        safe_name: Target safe name (required) - Must exist and be accessible
        name: Account identifier (optional) - Account display name
        address: Target address (optional) - Examples: "server01.corp.com", "192.168.1.100"
        user_name: Username (optional) - Examples: "admin", "oracle", "service_account"
        secret: Password/key (optional) - Will be auto-generated if not provided
        secret_type: Secret type (optional) - "password" (default) or "key"
        platform_account_properties: Platform properties (optional) - {"LogonDomain": "CORP", "Port": "3389"}
        secret_management: Management config (optional) - {"automaticManagementEnabled": true}
        remote_machines_access: Access config (optional) - {"remoteMachines": "server1;server2"}
    
    Returns:
        Created account object with ID and metadata
        
    Example:
        create_account("WinServerLocal", "Production-Servers", address="web01.corp.com", user_name="admin")
    """
    return await execute_tool("create_account", platform_id=platform_id, safe_name=safe_name, 
                             name=name, address=address, user_name=user_name, secret=secret, 
                             secret_type=secret_type, platform_account_properties=platform_account_properties,
                             secret_management=secret_management, remote_machines_access=remote_machines_access)

@mcp.tool()
async def change_account_password(
    account_id: str,
    new_password: Optional[str] = None
) -> Dict[str, Any]:
    """
    Change the password for an existing account in CyberArk Privilege Cloud.
    
    This operation initiates an immediate password change for the specified account.
    If no new password is provided, the Central Password Manager (CPM) will generate
    a new password according to the platform's password policy.
    
    Args:
        account_id: The unique ID of the account to change password for (required)
        new_password: Optional new password. If not provided, CPM will generate one automatically
    
    Returns:
        Password change response containing status, timestamps, and account metadata
        
    Security Notes:
        - This operation requires appropriate permissions for password management
        - Password changes are audited and logged in CyberArk
        - Use CPM-generated passwords when possible for better security compliance
    """
    return await execute_tool("change_account_password", account_id=account_id, new_password=new_password)

@mcp.tool()
async def set_next_password(
    account_id: str,
    new_password: str,
    change_immediately: bool = True
) -> Dict[str, Any]:
    """
    Set the next password for an existing account in CyberArk Privilege Cloud.
    
    This operation manually sets the next password for an account, which is different 
    from CPM-managed password changes. The password will be set immediately by default.
    
    Args:
        account_id: The unique ID of the account to set password for (required)
        new_password: The new password to set for the account (required)
        change_immediately: Whether to change the password immediately (default: True)
    
    Returns:
        Password set response containing status, timestamps, and account metadata
        
    Security Notes:
        - This operation requires appropriate permissions for password management
        - Password changes are audited and logged in CyberArk
        - Use strong passwords that comply with your organization's policy
    """
    return await execute_tool("set_next_password", account_id=account_id, new_password=new_password, change_immediately=change_immediately)

@mcp.tool()
async def verify_account_password(
    account_id: str
) -> Dict[str, Any]:
    """
    Verify the password for an existing account in CyberArk Privilege Cloud.
    
    This operation verifies that the current password for the specified account
    is valid and up-to-date. It's useful for checking password status before
    performing other operations or as part of compliance checks.
    
    Args:
        account_id: The unique ID of the account to verify password for (required)
    
    Returns:
        Password verification response containing verification status, timestamps, and account metadata
        
    Security Notes:
        - This operation requires appropriate permissions for password verification
        - Password verifications are audited and logged in CyberArk
        - This operation does not expose the actual password, only verification status
    """
    return await execute_tool("verify_account_password", account_id=account_id)

@mcp.tool()
async def reconcile_account_password(
    account_id: str
) -> Dict[str, Any]:
    """
    Reconcile the password for an existing account in CyberArk Privilege Cloud.
    
    This operation synchronizes the password between the CyberArk Vault and the target system.
    It's useful when passwords may have been changed outside of CyberArk or when there's
    a mismatch between the vault and target system credentials.
    
    Args:
        account_id: The unique ID of the account to reconcile password for (required)
    
    Returns:
        Password reconciliation response containing reconciliation status, timestamps, and account metadata
        
    Security Notes:
        - This operation requires appropriate permissions for password management
        - Password reconciliations are audited and logged in CyberArk
        - This operation may take longer to complete as it involves communication with target systems
        - The operation synchronizes credentials between vault and target without exposing passwords
    """
    return await execute_tool("reconcile_account_password", account_id=account_id)

@mcp.tool()
async def update_account(
    account_id: str,
    name: Optional[str] = None,
    address: Optional[str] = None,
    user_name: Optional[str] = None,
    platform_account_properties: Optional[Dict[str, Any]] = None,
    secret_management: Optional[Dict[str, Any]] = None,
    remote_machines_access: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Update an existing account in CyberArk Privilege Cloud.
    
    This operation allows modification of account properties while preserving
    the account's identity and credentials. Only provided fields will be updated.
    
    Args:
        account_id: The unique ID of the account to update (required)
        name: New account display name (optional)
        address: New target address (optional) - Examples: "server02.corp.com", "192.168.1.101"
        user_name: New username (optional) - Examples: "administrator", "oracle", "app_service"
        platform_account_properties: Platform-specific properties (optional) - {"LogonDomain": "NEWCORP", "Port": "3390"}
        secret_management: Management configuration (optional) - {"automaticManagementEnabled": false}
        remote_machines_access: Access configuration (optional) - {"remoteMachines": "newserver1;newserver2"}
    
    Returns:
        Updated account object with modified properties and metadata
        
    Security Notes:
        - This operation requires appropriate permissions for account management
        - Account updates are audited and logged in CyberArk
        - Existing credentials and account ID remain unchanged
        - Platform properties must be compatible with the account's platform type
        
    Example:
        update_account("123_456", name="updated-web-server", address="web02.corp.com", 
                      platform_account_properties={"Port": "8080"})
    """
    return await execute_tool("update_account", account_id=account_id, name=name, address=address,
                             user_name=user_name, platform_account_properties=platform_account_properties,
                             secret_management=secret_management, remote_machines_access=remote_machines_access)

@mcp.tool()
async def delete_account(
    account_id: str
) -> Dict[str, Any]:
    """
    Delete an existing account from CyberArk Privilege Cloud.
    
    This operation permanently removes the account and all its associated data
    from the CyberArk Vault. This action cannot be undone.
    
    Args:
        account_id: The unique ID of the account to delete (required)
    
    Returns:
        Deletion response containing deletion status, timestamps, and confirmation metadata
        
    Security Notes:
        - This operation requires appropriate permissions for account management
        - Account deletions are audited and logged in CyberArk
        - This action is irreversible - the account and its credentials are permanently removed
        - Consider disabling or moving accounts instead of deletion for audit trail preservation
        - Deletion may affect dependent systems or applications using the account
        
    Warning:
        This is a destructive operation. Ensure the account is no longer needed before deletion.
        
    Example:
        delete_account("123_456")  # Permanently removes account with ID 123_456
    """
    return await execute_tool("delete_account", account_id=account_id)












@mcp.tool()
async def import_platform_package(
    platform_package_file: str
) -> Dict[str, Any]:
    """
    Import a platform package ZIP file to CyberArk Privilege Cloud to add new platform types.
    
    Args:
        platform_package_file: Full path to platform package ZIP file (required) - Must be valid ZIP ≤ 20MB
    
    Returns:
        Import result containing PlatformID of the imported platform and status information
        
    Example:
        import_platform_package("/path/to/CustomPlatform.zip")
        
    Requirements:
        - File must be a valid ZIP archive
        - Maximum file size: 20MB
        - Must contain valid platform definition files
        - Supports: Target, Dependent, Group, and Rotational group platform types
        
    Note: Requires Privilege Cloud Administrator role for platform management operations
    """
    return await execute_tool("import_platform_package", platform_package_file=platform_package_file)


@mcp.tool()
async def export_platform(
    platform_id: str,
    output_folder: str
) -> Dict[str, Any]:
    """
    Export a platform configuration package from CyberArk Privilege Cloud.
    
    Args:
        platform_id: The unique ID of the platform to export (required)
        output_folder: The local folder path where the platform package should be exported (required)
    
    Returns:
        Export result containing the platform_id, output_folder, and status
        
    Example:
        export_platform("WinServerLocal", "/home/user/exports")
        
    Requirements:
        - Platform must exist
        - Output folder must be accessible
        - Requires Privilege Cloud Administrator role for platform management operations
        
    Note: Exports platform configuration as a ZIP package to the specified folder
    """
    return await execute_tool("export_platform", platform_id=platform_id, output_folder=output_folder)


@mcp.tool()
async def duplicate_target_platform(
    target_platform_id: int,
    name: str,
    description: str = None
) -> Dict[str, Any]:
    """
    Duplicate/clone an existing target platform in CyberArk Privilege Cloud.
    
    Args:
        target_platform_id: The unique integer ID of the target platform to duplicate (required)
        name: The name for the new duplicated platform (required)
        description: Optional description for the new platform
    
    Returns:
        Details of the newly created duplicated platform
        
    Example:
        duplicate_target_platform(123, "Custom Windows Platform Copy", "Duplicated platform for testing")
        
    Requirements:
        - Target platform must exist
        - New platform name must be unique
        - Requires Privilege Cloud Administrator role for platform management operations
        
    Note: Creates a copy of an existing target platform with new name and optional description
    """
    return await execute_tool("duplicate_target_platform", target_platform_id=target_platform_id, name=name, description=description)


@mcp.tool()
async def activate_target_platform(
    target_platform_id: int
) -> Dict[str, Any]:
    """
    Activate/enable a target platform in CyberArk Privilege Cloud.
    
    Args:
        target_platform_id: The unique integer ID of the target platform to activate (required)
    
    Returns:
        Activation result containing the target_platform_id and status
        
    Example:
        activate_target_platform(123)
        
    Requirements:
        - Target platform must exist
        - Platform must be in inactive state
        - Requires Privilege Cloud Administrator role for platform management operations
        
    Note: Activates the platform making it available for account creation and management
    """
    return await execute_tool("activate_target_platform", target_platform_id=target_platform_id)


@mcp.tool()
async def deactivate_target_platform(
    target_platform_id: int
) -> Dict[str, Any]:
    """
    Deactivate/disable a target platform in CyberArk Privilege Cloud.
    
    Args:
        target_platform_id: The unique integer ID of the target platform to deactivate (required)
    
    Returns:
        Deactivation result containing the target_platform_id and status
        
    Example:
        deactivate_target_platform(123)
        
    Requirements:
        - Target platform must exist
        - Platform must be in active state
        - No active accounts should be using this platform
        - Requires Privilege Cloud Administrator role for platform management operations
        
    Note: Deactivates the platform preventing new account creation with this platform
    """
    return await execute_tool("deactivate_target_platform", target_platform_id=target_platform_id)


@mcp.tool()
async def delete_target_platform(
    target_platform_id: int
) -> Dict[str, Any]:
    """
    Delete a target platform from CyberArk Privilege Cloud.
    
    Args:
        target_platform_id: The unique integer ID of the target platform to delete (required)
    
    Returns:
        Deletion result containing the target_platform_id and status
        
    Example:
        delete_target_platform(123)
        
    Requirements:
        - Target platform must exist
        - Platform must be inactive
        - No accounts should be associated with this platform
        - Requires Privilege Cloud Administrator role for platform management operations
        
    Warning: This operation permanently removes the platform and cannot be undone
    """
    return await execute_tool("delete_target_platform", target_platform_id=target_platform_id)

@mcp.tool()
async def get_platform_statistics() -> Dict[str, Any]:
    """
    Calculate comprehensive platform statistics from CyberArk Privilege Cloud.
    
    Returns:
        Platform statistics including total count and distribution by platform type
        
    Example Response:
        {
            "platforms_count": 15,
            "platforms_count_by_type": {
                "regular": 12,
                "rotational_group": 2,
                "group": 1
            }
        }
        
    Example:
        get_platform_statistics()
        
    Requirements:
        - Requires authenticated access to CyberArk Privilege Cloud
        - User must have read access to platforms
        
    Note: Statistics are calculated from all visible platforms based on user permissions
    """
    return await execute_tool("get_platform_statistics")

@mcp.tool()
async def get_target_platform_statistics() -> Dict[str, Any]:
    """
    Calculate comprehensive target platform statistics from CyberArk Privilege Cloud.
    
    Returns:
        Target platform statistics including total count and distribution by system type
        
    Example Response:
        {
            "target_platforms_count": 8,
            "target_platforms_count_by_system_type": {
                "Windows": 3,
                "Unix": 2,
                "Oracle": 2,
                "Database": 1
            }
        }
        
    Example:
        get_target_platform_statistics()
        
    Requirements:
        - Requires authenticated access to CyberArk Privilege Cloud
        - User must have read access to target platforms
        
    Note: Statistics are calculated from all visible target platforms based on user permissions
    """
    return await execute_tool("get_target_platform_statistics")


# Data access tools - return raw API data
@mcp.tool()
async def get_account_details(account_id: str) -> Dict[str, Any]:
    """Get detailed information about a specific account in CyberArk Privilege Cloud.
    
    Args:
        account_id: The unique ID of the account to retrieve details for (required)
    
    Returns:
        Account object with complete details and exact API fields
    """
    return await execute_tool("get_account_details", account_id=account_id)

@mcp.tool()
async def list_accounts() -> List[Dict[str, Any]]:
    """List all accessible accounts in CyberArk Privilege Cloud.
    
    Returns:
        List of account objects with their exact API fields
    """
    return await execute_tool("list_accounts")

@mcp.tool()
async def search_accounts(
    query: Optional[str] = None,
    safe_name: Optional[str] = None,
    username: Optional[str] = None,
    address: Optional[str] = None,
    platform_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Search for accounts with various criteria.
    
    Args:
        query: General search keywords
        safe_name: Filter by safe name
        username: Filter by username
        address: Filter by address
        platform_id: Filter by platform ID
        
    Returns:
        List of matching account objects with exact API fields
    """
    return await execute_tool("search_accounts", query=query, safe_name=safe_name, 
                             username=username, address=address, platform_id=platform_id)

# Advanced Account Search and Filtering Tools
@mcp.tool()
async def filter_accounts_by_platform_group(platform_group: str) -> List[Dict[str, Any]]:
    """Filter accounts by platform type grouping (Windows, Linux, Database, etc.).
    
    Args:
        platform_group: Platform group to filter by (Windows, Linux, Database, Network, Cloud)
        
    Returns:
        List of accounts matching the platform group with exact API fields
    """
    return await execute_tool("filter_accounts_by_platform_group", platform_group=platform_group)

@mcp.tool()
async def filter_accounts_by_environment(environment: str) -> List[Dict[str, Any]]:
    """Filter accounts by environment (production, staging, development, etc.).
    
    Args:
        environment: Environment name to filter by (found in account addresses)
        
    Returns:
        List of accounts in the specified environment with exact API fields
    """
    return await execute_tool("filter_accounts_by_environment", environment=environment)

@mcp.tool()
async def filter_accounts_by_management_status(auto_managed: bool = True) -> List[Dict[str, Any]]:
    """Filter accounts by automatic password management status.
    
    Args:
        auto_managed: True for automatically managed accounts, False for manually managed
        
    Returns:
        List of accounts with the specified management status and exact API fields
    """
    return await execute_tool("filter_accounts_by_management_status", auto_managed=auto_managed)

@mcp.tool()
async def group_accounts_by_safe() -> Dict[str, List[Dict[str, Any]]]:
    """Group all accounts by their safe name.
    
    Returns:
        Dictionary with safe names as keys and lists of accounts as values
    """
    return await execute_tool("group_accounts_by_safe")

@mcp.tool()
async def group_accounts_by_platform() -> Dict[str, List[Dict[str, Any]]]:
    """Group all accounts by their platform type.
    
    Returns:
        Dictionary with platform IDs as keys and lists of accounts as values
    """
    return await execute_tool("group_accounts_by_platform")

@mcp.tool()
async def analyze_account_distribution() -> Dict[str, Any]:
    """Analyze distribution of accounts across safes, platforms, and environments.
    
    Returns:
        Analysis report with counts and percentages for various account categories
    """
    return await execute_tool("analyze_account_distribution")

@mcp.tool()
async def search_accounts_by_pattern(
    username_pattern: Optional[str] = None,
    address_pattern: Optional[str] = None, 
    environment: Optional[str] = None,
    platform_group: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Search accounts using multiple pattern criteria.
    
    Args:
        username_pattern: Pattern to match in usernames
        address_pattern: Pattern to match in addresses
        environment: Environment name to filter by
        platform_group: Platform group to filter by (Windows, Linux, Database, etc.)
        
    Returns:
        List of accounts matching all specified criteria with exact API fields
    """
    return await execute_tool("search_accounts_by_pattern", 
                             username_pattern=username_pattern,
                             address_pattern=address_pattern,
                             environment=environment,
                             platform_group=platform_group)

@mcp.tool()
async def count_accounts_by_criteria() -> Dict[str, Any]:
    """Count accounts by various criteria (platform, safe, management status).
    
    Returns:
        Count summary with totals for different account categories
    """
    return await execute_tool("count_accounts_by_criteria")

@mcp.tool()
async def get_safe_details(safe_name: str) -> Dict[str, Any]:
    """Get detailed information about a specific safe in CyberArk Privilege Cloud.
    
    Args:
        safe_name: The name of the safe to retrieve details for (required)
    
    Returns:
        Safe object with complete details and exact API fields
    """
    return await execute_tool("get_safe_details", safe_name=safe_name)

@mcp.tool()
async def list_safes() -> List[Dict[str, Any]]:
    """List all accessible safes in CyberArk Privilege Cloud.
    
    Returns:
        List of safe objects with their exact API fields
    """
    return await execute_tool("list_safes")

@mcp.tool()
async def add_safe(
    safe_name: str,
    description: Optional[str] = None
) -> Dict[str, Any]:
    """Add a new safe to CyberArk Privilege Cloud.
    
    Args:
        safe_name: The name of the new safe (required)
        description: Optional description for the safe
    
    Returns:
        Safe object with its exact API fields after creation
    """
    return await execute_tool("add_safe", safe_name=safe_name, description=description)

@mcp.tool()
async def update_safe(
    safe_id: str,
    safe_name: Optional[str] = None,
    description: Optional[str] = None,
    location: Optional[str] = None,
    number_of_days_retention: Optional[int] = None,
    number_of_versions_retention: Optional[int] = None,
    auto_purge_enabled: Optional[bool] = None,
    olac_enabled: Optional[bool] = None,
    managing_cpm: Optional[str] = None
) -> Dict[str, Any]:
    """Update properties of an existing safe in CyberArk Privilege Cloud.
    
    Args:
        safe_id: The unique ID of the safe to update (required)
        safe_name: New name for the safe
        description: New description for the safe
        location: Location of the safe in the vault (e.g. "\\")
        number_of_days_retention: Number of retention days on the safe objects
        number_of_versions_retention: Number of retention versions on the safe objects
        auto_purge_enabled: Whether auto purge is enabled on the safe
        olac_enabled: Whether object level access control is enabled
        managing_cpm: Managing CPM of the safe
    
    Returns:
        Updated safe object with its exact API fields
    """
    return await execute_tool(
        "update_safe",
        safe_id=safe_id,
        safe_name=safe_name,
        description=description,
        location=location,
        number_of_days_retention=number_of_days_retention,
        number_of_versions_retention=number_of_versions_retention,
        auto_purge_enabled=auto_purge_enabled,
        olac_enabled=olac_enabled,
        managing_cpm=managing_cpm
    )

@mcp.tool()
async def delete_safe(safe_id: str) -> Dict[str, Any]:
    """Delete a safe from CyberArk Privilege Cloud.
    
    WARNING: This action permanently removes the safe and all its contents.
    
    Args:
        safe_id: The unique ID of the safe to delete (required)
    
    Returns:
        Confirmation message with the deleted safe ID
    """
    return await execute_tool("delete_safe", safe_id=safe_id)


# Safe Member Management Tools

@mcp.tool()
async def list_safe_members(
    safe_name: str,
    search: Optional[str] = None,
    sort: Optional[str] = None,
    offset: Optional[int] = None,
    limit: Optional[int] = None,
    member_type: Optional[str] = None
) -> List[Dict[str, Any]]:
    """List all members of a specific safe with their permissions.
    
    Args:
        safe_name: The name of the safe to list members for (required)
        search: Optional search term to filter members
        sort: Optional sort field (e.g., "memberName", "memberType")
        offset: Optional offset for pagination
        limit: Optional limit for pagination
        member_type: Optional filter by member type ("User", "Group", "Role")
    
    Returns:
        List of safe member objects with permissions and details
        
    Example:
        list_safe_members("IT-Infrastructure")
        list_safe_members("HR-Safe", member_type="User")
    """
    return await execute_tool(
        "list_safe_members", 
        safe_name=safe_name,
        search=search,
        sort=sort,
        offset=offset,
        limit=limit,
        member_type=member_type
    )

@mcp.tool()
async def get_safe_member_details(safe_name: str, member_name: str) -> Dict[str, Any]:
    """Get detailed information about a specific safe member.
    
    Args:
        safe_name: The name of the safe (required)
        member_name: The name of the member to get details for (required)
    
    Returns:
        Safe member object with complete permissions and membership details
        
    Example:
        get_safe_member_details("IT-Infrastructure", "admin@domain.com")
    """
    return await execute_tool("get_safe_member_details", safe_name=safe_name, member_name=member_name)

@mcp.tool()
async def add_safe_member(
    safe_name: str,
    member_name: str,
    member_type: str,
    search_in: Optional[str] = None,
    membership_expiration_date: Optional[str] = None,
    permissions: Optional[Dict[str, Any]] = None,
    permission_set: Optional[str] = None
) -> Dict[str, Any]:
    """Add a new member to a safe with specified permissions.
    
    Args:
        safe_name: The name of the safe to add the member to (required)
        member_name: The name/username of the member to add (required)
        member_type: Type of member - "User", "Group", or "Role" (required)
        search_in: Optional domain to search for the member in
        membership_expiration_date: Optional ISO 8601 date when membership expires
        permissions: Optional custom permissions dict (use with permission_set="Custom")
        permission_set: Optional predefined permission set - "ConnectOnly", "ReadOnly", "Approver", "AccountsManager", "Full", "Custom"
    
    Returns:
        Created safe member object with assigned permissions
        
    Examples:
        add_safe_member("IT-Infrastructure", "newuser@domain.com", "User", permission_set="ReadOnly")
        add_safe_member("HR-Safe", "ApproverGroup", "Group", permission_set="Approver")
        
    Note: Defaults to "ReadOnly" permission set if no permissions specified
    """
    return await execute_tool(
        "add_safe_member",
        safe_name=safe_name,
        member_name=member_name,
        member_type=member_type,
        search_in=search_in,
        membership_expiration_date=membership_expiration_date,
        permissions=permissions,
        permission_set=permission_set
    )

@mcp.tool()
async def update_safe_member(
    safe_name: str,
    member_name: str,
    search_in: Optional[str] = None,
    membership_expiration_date: Optional[str] = None,
    permissions: Optional[Dict[str, Any]] = None,
    permission_set: Optional[str] = None
) -> Dict[str, Any]:
    """Update permissions for an existing safe member.
    
    Args:
        safe_name: The name of the safe (required)
        member_name: The name of the member to update (required)
        search_in: Optional domain to search for the member in
        membership_expiration_date: Optional ISO 8601 date when membership expires
        permissions: Optional custom permissions dict (use with permission_set="Custom")
        permission_set: Optional predefined permission set - "ConnectOnly", "ReadOnly", "Approver", "AccountsManager", "Full", "Custom"
    
    Returns:
        Updated safe member object with new permissions
        
    Examples:
        update_safe_member("IT-Infrastructure", "user@domain.com", permission_set="AccountsManager")
        update_safe_member("HR-Safe", "admin", membership_expiration_date="2024-12-31T23:59:59Z")
    """
    return await execute_tool(
        "update_safe_member",
        safe_name=safe_name,
        member_name=member_name,
        search_in=search_in,
        membership_expiration_date=membership_expiration_date,
        permissions=permissions,
        permission_set=permission_set
    )

@mcp.tool()
async def remove_safe_member(safe_name: str, member_name: str) -> Dict[str, Any]:
    """Remove a member from a safe.
    
    Args:
        safe_name: The name of the safe (required)
        member_name: The name of the member to remove (required)
    
    Returns:
        Confirmation message with removal details
        
    Example:
        remove_safe_member("IT-Infrastructure", "olduser@domain.com")
        
    Note: This action permanently removes the member's access to the safe
    """
    return await execute_tool("remove_safe_member", safe_name=safe_name, member_name=member_name)


@mcp.tool()
async def get_platform_details(platform_id: str) -> Dict[str, Any]:
    """Get detailed information about a specific platform in CyberArk Privilege Cloud.
    
    Args:
        platform_id: The unique ID of the platform to retrieve details for (required)
    
    Returns:
        Platform object with complete configuration details and exact API fields
    """
    return await execute_tool("get_platform_details", platform_id=platform_id)

@mcp.tool()
async def list_platforms() -> List[Dict[str, Any]]:
    """List all available platforms in CyberArk Privilege Cloud.
    
    Returns:
        List of platform objects with their exact API fields
    """
    return await execute_tool("list_platforms")


# Application Management Tools using ArkPCloudApplicationsService

@mcp.tool()
async def list_applications(
    location: Optional[str] = None,
    only_enabled: Optional[bool] = None,
    business_owner_name: Optional[str] = None,
    business_owner_email: Optional[str] = None
) -> List[Dict[str, Any]]:
    """List applications from CyberArk Privilege Cloud.
    
    Args:
        location: Filter by application location
        only_enabled: Filter to only enabled applications
        business_owner_name: Filter by business owner name
        business_owner_email: Filter by business owner email
    
    Returns:
        List of application objects with their exact API fields
    """
    kwargs = {}
    if location is not None:
        kwargs['location'] = location
    if only_enabled is not None:
        kwargs['only_enabled'] = only_enabled
    if business_owner_name is not None:
        kwargs['business_owner_name'] = business_owner_name
    if business_owner_email is not None:
        kwargs['business_owner_email'] = business_owner_email
    
    return await execute_tool("list_applications", **kwargs)


@mcp.tool()
async def get_application_details(app_id: str) -> Dict[str, Any]:
    """Get detailed information about a specific application.
    
    Args:
        app_id: The unique identifier of the application
    
    Returns:
        Application object with all configuration details
    """
    return await execute_tool("get_application_details", app_id=app_id)


@mcp.tool()
async def add_application(
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
    business_owner_phone: str = ""
) -> Dict[str, Any]:
    """Add a new application to CyberArk Privilege Cloud.
    
    Args:
        app_id: Unique identifier for the application
        description: Description of the application
        location: Location of the application
        access_permitted_from: Start time for permitted access (HH:MM format)
        access_permitted_to: End time for permitted access (HH:MM format)
        expiration_date: Expiration date for the application (YYYY-MM-DD format)
        disabled: Whether the application is disabled
        business_owner_first_name: Business owner's first name
        business_owner_last_name: Business owner's last name
        business_owner_email: Business owner's email address
        business_owner_phone: Business owner's phone number
    
    Returns:
        Created application object with its details
    """
    return await execute_tool(
        "add_application",
        app_id=app_id,
        description=description,
        location=location,
        access_permitted_from=access_permitted_from,
        access_permitted_to=access_permitted_to,
        expiration_date=expiration_date,
        disabled=disabled,
        business_owner_first_name=business_owner_first_name,
        business_owner_last_name=business_owner_last_name,
        business_owner_email=business_owner_email,
        business_owner_phone=business_owner_phone
    )


@mcp.tool()
async def delete_application(app_id: str) -> Dict[str, Any]:
    """Delete an application from CyberArk Privilege Cloud.
    
    Args:
        app_id: The unique identifier of the application to delete
    
    Returns:
        Confirmation of deletion
    """
    return await execute_tool("delete_application", app_id=app_id)


@mcp.tool()
async def list_application_auth_methods(
    app_id: str,
    auth_types: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """List authentication methods for a specific application.
    
    Args:
        app_id: The unique identifier of the application
        auth_types: Filter by specific authentication types
    
    Returns:
        List of authentication method objects for the application
    """
    kwargs = {"app_id": app_id}
    if auth_types is not None:
        kwargs['auth_types'] = auth_types
    
    return await execute_tool("list_application_auth_methods", **kwargs)


@mcp.tool()
async def get_application_auth_method_details(app_id: str, auth_id: str) -> Dict[str, Any]:
    """Get detailed information about a specific application authentication method.
    
    Args:
        app_id: The unique identifier of the application
        auth_id: The unique identifier of the authentication method
    
    Returns:
        Authentication method object with all configuration details
    """
    return await execute_tool("get_application_auth_method_details", app_id=app_id, auth_id=auth_id)


@mcp.tool()
async def add_application_auth_method(
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
    subject_alternative_name: str = ""
) -> Dict[str, Any]:
    """Add an authentication method to an application.
    
    Args:
        app_id: The unique identifier of the application
        auth_type: Type of authentication method
        auth_value: Value for the authentication method
        is_folder: Whether this is a folder-based authentication
        allow_internal_scripts: Whether to allow internal scripts
        comment: Comment for the authentication method
        namespace: Namespace for the authentication method
        image: Image for the authentication method
        env_var_name: Environment variable name
        env_var_value: Environment variable value
        subject: Subject for certificate-based authentication
        issuer: Issuer for certificate-based authentication
        subject_alternative_name: Subject alternative name for certificates
    
    Returns:
        Created authentication method object
    """
    return await execute_tool(
        "add_application_auth_method",
        app_id=app_id,
        auth_type=auth_type,
        auth_value=auth_value,
        is_folder=is_folder,
        allow_internal_scripts=allow_internal_scripts,
        comment=comment,
        namespace=namespace,
        image=image,
        env_var_name=env_var_name,
        env_var_value=env_var_value,
        subject=subject,
        issuer=issuer,
        subject_alternative_name=subject_alternative_name
    )


@mcp.tool()
async def delete_application_auth_method(app_id: str, auth_id: str) -> Dict[str, Any]:
    """Delete an authentication method from an application.
    
    Args:
        app_id: The unique identifier of the application
        auth_id: The unique identifier of the authentication method to delete
    
    Returns:
        Confirmation of deletion
    """
    return await execute_tool("delete_application_auth_method", app_id=app_id, auth_id=auth_id)


@mcp.tool()
async def get_applications_stats() -> Dict[str, Any]:
    """Get comprehensive statistics about applications in CyberArk Privilege Cloud.
    
    Returns:
        Statistics object with application metrics including total count,
        disabled applications, authentication types distribution, and
        authentication method statistics
    """
    return await execute_tool("get_applications_stats")


# Session Monitoring Tools using ArkSMService

@mcp.tool()
async def list_sessions() -> List[Dict[str, Any]]:
    """List recent privileged sessions from CyberArk Session Monitoring.
    
    Returns all sessions from the last 24 hours with session details including
    protocol, start time, duration, user, and target information.
    
    Returns:
        List of session objects with their exact API fields
    """
    return await execute_tool("list_sessions")


@mcp.tool()
async def list_sessions_by_filter(search: Optional[str] = None) -> List[Dict[str, Any]]:
    """List privileged sessions with advanced filtering from CyberArk Session Monitoring.
    
    Supports advanced filtering using CyberArk session query syntax:
    - Time filtering: 'startTime ge 2024-01-15T08:00:00Z'
    - Duration filtering: 'sessionDuration GE 00:00:01'
    - Protocol filtering: 'protocol IN SSH,RDP,Database'
    - Combined queries with AND/OR operators
    
    Args:
        search: Optional filter query using CyberArk session search syntax
    
    Returns:
        List of filtered session objects with their exact API fields
    """
    return await execute_tool("list_sessions_by_filter", search=search)


@mcp.tool()
async def get_session_details(session_id: str) -> Dict[str, Any]:
    """Get detailed information about a specific privileged session.
    
    Retrieves comprehensive session information including protocol details,
    timing information, user context, target system, and account information.
    
    Args:
        session_id: Unique session identifier (UUID format)
    
    Returns:
        Detailed session object with all available API fields
    """
    return await execute_tool("get_session_details", session_id=session_id)


@mcp.tool()
async def list_session_activities(session_id: str) -> List[Dict[str, Any]]:
    """List all activities performed within a specific privileged session.
    
    Retrieves chronological log of commands, actions, and operations
    performed during the session for audit and analysis purposes.
    
    Args:
        session_id: Unique session identifier (UUID format)
    
    Returns:
        List of activity objects with timestamps, commands, and results
    """
    return await execute_tool("list_session_activities", session_id=session_id)


@mcp.tool()
async def count_sessions(search: Optional[str] = None) -> Dict[str, Any]:
    """Count privileged sessions with optional filtering.
    
    Provides session counts for analysis and reporting. Supports the same
    filtering capabilities as list_sessions_by_filter.
    
    Args:
        search: Optional filter query using CyberArk session search syntax
    
    Returns:
        Dictionary with session count and applied filter information
    """
    return await execute_tool("count_sessions", search=search)


@mcp.tool()
async def get_session_statistics() -> Dict[str, Any]:
    """Get general session statistics and analytics.
    
    Provides high-level session metrics including total sessions,
    active sessions, protocol distribution, and usage patterns
    typically covering the last 30 days.
    
    Returns:
        Statistics object with session analytics and metrics
    """
    return await execute_tool("get_session_statistics")


def main():
    """Main entry point for the MCP server"""
    logger.info("Starting CyberArk Privilege Cloud MCP Server")
    # Environment validation is handled by server initialization above
    mcp.run()


if __name__ == "__main__":
    main()