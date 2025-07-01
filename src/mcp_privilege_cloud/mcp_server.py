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


@mcp.tool()
async def list_accounts(
    safe_name: Optional[str] = None,
    search: Optional[str] = None,
    search_type: Optional[str] = None,
    sort: Optional[str] = None,
    offset: Optional[int] = None,
    limit: Optional[int] = None,
    filter: Optional[str] = None,
    saved_filter: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    List privileged accounts from CyberArk Privilege Cloud with optional filtering.
    
    Args:
        safe_name: Filter by safe name (optional) - Examples: "Production-Servers", "Database-Accounts"
        search: Keywords to search for (optional) - Examples: "admin", "database"
        search_type: Search type - "contains" or "startswith" (optional)
        sort: Sort order (optional) - Examples: "name", "address", "platformId"
        offset: Pagination offset (optional) - Example: 0, 20, 40
        limit: Maximum results to return (optional) - Example: 50, 100
        filter: Custom filter expression (optional) - Example: "platformId eq WindowsAccount"
        saved_filter: Predefined filter name (optional)
    
    Returns:
        List of account objects containing id, name, address, userName, safeName, platformId
        
    Example:
        list_accounts(safe_name="Production-Servers", search="admin", limit=50)
    """
    try:
        # Get the server instance from the current context
        server = CyberArkMCPServer.from_environment()
        
        # Build kwargs for the server method
        kwargs = {}
        if search is not None:
            kwargs["search"] = search
        if search_type is not None:
            kwargs["searchType"] = search_type
        if sort is not None:
            kwargs["sort"] = sort
        if offset is not None:
            kwargs["offset"] = offset
        if limit is not None:
            kwargs["limit"] = limit
        if filter is not None:
            kwargs["filter"] = filter
        if saved_filter is not None:
            kwargs["savedfilter"] = saved_filter
            
        accounts = await server.list_accounts(safe_name=safe_name, **kwargs)
        logger.info(f"Retrieved {len(accounts)} accounts")
        return accounts
    except Exception as e:
        logger.error(f"Error listing accounts: {e}")
        raise


@mcp.tool()
async def get_account_details(
    account_id: str
) -> Dict[str, Any]:
    """
    Get detailed information about a specific privileged account.
    
    Args:
        account_id: Unique identifier for the account (required) - Numeric string, e.g., "12345"
    
    Returns:
        Account object with detailed information including platform properties, last password change, status
        
    Example:
        get_account_details("12345")
    """
    try:
        server = CyberArkMCPServer.from_environment()
        account = await server.get_account_details(account_id)
        logger.info(f"Retrieved details for account {account_id}")
        return account
    except Exception as e:
        logger.error(f"Error getting account details for {account_id}: {e}")
        raise


@mcp.tool()
async def search_accounts(
    keywords: Optional[str] = None,
    safe_name: Optional[str] = None,
    username: Optional[str] = None,
    address: Optional[str] = None,
    platform_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Search for privileged accounts using advanced criteria and keywords.
    
    Args:
        keywords: Search keywords (optional) - Free text search across account properties
        safe_name: Filter by safe name (optional) - Examples: "Production-Servers", "Database-Accounts"
        username: Filter by username (optional) - Examples: "admin", "service_account"
        address: Filter by address/hostname (optional) - Examples: "server01.corp.com", "192.168.1.100"
        platform_id: Filter by platform ID (optional) - Examples: "WinServerLocal", "UnixSSH"
    
    Returns:
        List of matching account objects with relevance scoring
        
    Example:
        search_accounts(keywords="production database", platform_id="UnixSSH")
    """
    try:
        server = CyberArkMCPServer.from_environment()
        accounts = await server.search_accounts(
            keywords=keywords,
            safe_name=safe_name,
            username=username,
            address=address,
            platform_id=platform_id
        )
        logger.info(f"Search returned {len(accounts)} accounts")
        return accounts
    except Exception as e:
        logger.error(f"Error searching accounts: {e}")
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
    try:
        server = CyberArkMCPServer.from_environment()
        account = await server.create_account(
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
        logger.info(f"Created account with ID: {account.get('id', 'unknown')}")
        return account
    except Exception as e:
        logger.error(f"Error creating account: {e}")
        raise

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
    try:
        server = CyberArkMCPServer.from_environment()
        result = await server.change_account_password(
            account_id=account_id,
            new_password=new_password
        )
        logger.info(f"Password change initiated for account ID: {account_id}")
        return result
    except Exception as e:
        logger.error(f"Error changing password for account ID: {account_id} - {e}")
        raise

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
    try:
        server = CyberArkMCPServer.from_environment()
        result = await server.set_next_password(
            account_id=account_id,
            new_password=new_password,
            change_immediately=change_immediately
        )
        logger.info(f"Next password set for account ID: {account_id}")
        return result
    except Exception as e:
        logger.error(f"Error setting next password for account ID: {account_id} - {e}")
        raise

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
    try:
        server = CyberArkMCPServer.from_environment()
        result = await server.verify_account_password(account_id=account_id)
        logger.info(f"Password verification completed for account ID: {account_id}")
        return result
    except Exception as e:
        logger.error(f"Error verifying password for account ID: {account_id} - {e}")
        raise

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
    try:
        server = CyberArkMCPServer.from_environment()
        result = await server.reconcile_account_password(account_id=account_id)
        logger.info(f"Password reconciliation completed for account ID: {account_id}")
        return result
    except Exception as e:
        logger.error(f"Error reconciling password for account ID: {account_id} - {e}")
        raise


@mcp.tool()
async def list_safes(
    search: Optional[str] = None,
    offset: Optional[int] = None,
    limit: Optional[int] = None,
    sort: Optional[str] = None,
    include_accounts: Optional[bool] = None,
    extended_details: Optional[bool] = None
) -> List[Dict[str, Any]]:
    """
    List all accessible safes in CyberArk Privilege Cloud with pagination and filtering.
    
    Args:
        search: Search term for safe names (optional) - Partial match, automatically URL encoded
        offset: Pagination offset (optional) - Default: 0, Max: 10000
        limit: Results per page (optional) - Default: 25, Max: 1000
        sort: Sort order (optional) - "safeName asc" or "safeName desc", Default: "safeName asc"
        include_accounts: Include account counts (optional) - Default: false
        extended_details: Return full details (optional) - Default: true
    
    Returns:
        List of safe objects (excludes Internal Safes) with name, description, location, member count
        
    Example:
        list_safes(search="Production", limit=50, include_accounts=true)
    """
    try:
        server = CyberArkMCPServer.from_environment()
        safes = await server.list_safes(
            search=search,
            offset=offset,
            limit=limit,
            sort=sort,
            include_accounts=include_accounts,
            extended_details=extended_details
        )
        logger.info(f"Retrieved {len(safes)} safes")
        return safes
    except Exception as e:
        logger.error(f"Error listing safes: {e}")
        raise


@mcp.tool()
async def get_safe_details(
    safe_name: str,
    include_accounts: Optional[bool] = None,
    use_cache: Optional[bool] = None
) -> Dict[str, Any]:
    """
    Get detailed information about a specific safe including configuration and permissions.
    
    Args:
        safe_name: Safe name (required) - Examples: "Production-Servers", "Database.Accounts"
        include_accounts: Include account list (optional) - Default: false
        use_cache: Use session cache (optional) - Default: false for real-time data
    
    Returns:
        Safe object with detailed configuration, permissions, location, and optionally account list
        
    Example:
        get_safe_details("Production-Servers", include_accounts=true)
        
    Note:
        Safe names with special characters (dots, spaces) are automatically URL encoded
    """
    try:
        server = CyberArkMCPServer.from_environment()
        safe = await server.get_safe_details(
            safe_name,
            include_accounts=include_accounts,
            use_cache=use_cache
        )
        logger.info(f"Retrieved details for safe {safe_name}")
        return safe
    except Exception as e:
        logger.error(f"Error getting safe details for {safe_name}: {e}")
        raise


@mcp.tool()
async def health_check() -> Dict[str, Any]:
    """
    Perform a comprehensive health check of the CyberArk Privilege Cloud connection and services.
    
    Returns:
        Health status information including connectivity, authentication, and service availability
        
    Example:
        health_check()
        
    Response includes:
        - status: "healthy" or "unhealthy"
        - timestamp: Check execution time
        - safe_count: Number of accessible safes (indicates proper permissions)
        - response_time: API response time in milliseconds
    """
    try:
        server = CyberArkMCPServer.from_environment()
        health = await server.health_check()
        logger.info(f"Health check completed: {health['status']}")
        return health
    except Exception as e:
        logger.error(f"Error performing health check: {e}")
        raise


@mcp.tool()
async def list_platforms(
    search: Optional[str] = None,
    active: Optional[bool] = None,
    system_type: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    List all available platforms in CyberArk Privilege Cloud with filtering options.
    
    Args:
        search: Search term for platform names (optional) - Partial match across platform names
        active: Filter by active status (optional) - true for active platforms only
        system_type: Filter by system type (optional) - Examples: "Windows", "Unix", "Database"
    
    Returns:
        List of platform objects with platformId, platformName, systemType, and capabilities
        
    Example:
        list_platforms(system_type="Windows", active=true)
        
    Common platform types: WinServerLocal, UnixSSH, Oracle, SQLServer, MySQL, PostgreSQL
    """
    try:
        server = CyberArkMCPServer.from_environment()
        platforms = await server.list_platforms(
            search=search,
            active=active,
            system_type=system_type
        )
        logger.info(f"Retrieved {len(platforms)} platforms")
        return platforms
    except Exception as e:
        logger.error(f"Error listing platforms: {e}")
        raise


@mcp.tool()
async def get_platform_details(
    platform_id: str
) -> Dict[str, Any]:
    """
    Get detailed configuration information about a specific platform.
    
    Args:
        platform_id: Platform identifier (required) - Examples: "WinServerLocal", "UnixSSH", "Oracle"
    
    Returns:
        Platform object with detailed configuration including connection components, properties, and policies
        
    Example:
        get_platform_details("WinServerLocal")
        
    Response includes platform settings, connection components, password policies, and capabilities
    """
    try:
        server = CyberArkMCPServer.from_environment()
        platform = await server.get_platform_details(platform_id)
        logger.info(f"Retrieved details for platform {platform_id}")
        return platform
    except Exception as e:
        logger.error(f"Error getting platform details for {platform_id}: {e}")
        raise

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
    try:
        server = CyberArkMCPServer.from_environment()
        result = await server.import_platform_package(platform_package_file)
        logger.info(f"Successfully imported platform package. Platform ID: {result.get('PlatformID', 'Unknown')}")
        return result
    except Exception as e:
        logger.error(f"Error importing platform package: {e}")
        raise


# Resources will be added in future versions


def main():
    """Main entry point for the MCP server"""
    logger.info("Starting CyberArk Privilege Cloud MCP Server")
    
    # Verify required environment variables
    required_vars = [
        "CYBERARK_IDENTITY_TENANT_ID",
        "CYBERARK_CLIENT_ID", 
        "CYBERARK_CLIENT_SECRET",
        "CYBERARK_SUBDOMAIN"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        return
    
    # Run the MCP server
    mcp.run()


if __name__ == "__main__":
    main()