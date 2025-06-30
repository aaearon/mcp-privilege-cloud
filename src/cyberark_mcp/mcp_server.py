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
    from cyberark_mcp.server import CyberArkMCPServer

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
    username: Optional[str] = None,
    address: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    List accounts from CyberArk Privilege Cloud.
    
    Args:
        safe_name: Filter accounts by safe name
        username: Filter accounts by username
        address: Filter accounts by address/hostname
    
    Returns:
        List of account objects
    """
    try:
        # Get the server instance from the current context
        server = CyberArkMCPServer.from_environment()
        accounts = await server.list_accounts(
            safe_name=safe_name,
            username=username,
            address=address
        )
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
    Get detailed information about a specific account.
    
    Args:
        account_id: Unique identifier for the account
    
    Returns:
        Account object with detailed information
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
    Search for accounts using various criteria.
    
    Args:
        keywords: Search keywords
        safe_name: Filter by safe name
        username: Filter by username
        address: Filter by address/hostname
        platform_id: Filter by platform ID
    
    Returns:
        List of matching account objects
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
        platform_id: Platform ID for the account (required, e.g., WinServerLocal, UnixSSH)
        safe_name: Safe where the account will be created (required)
        name: Account name/identifier (optional)
        address: Target address/hostname (optional)
        user_name: Username for the account (optional)
        secret: Password or SSH key (optional)
        secret_type: Type of secret - 'password' or 'key' (optional, defaults to 'password')
        platform_account_properties: Platform-specific properties (optional, e.g., {"LogonDomain": "CORP", "Port": "3389"})
        secret_management: Secret management configuration (optional, e.g., {"automaticManagementEnabled": true})
        remote_machines_access: Remote access configuration (optional, e.g., {"remoteMachines": "server1;server2", "accessRestrictedToRemoteMachines": true})
    
    Returns:
        Created account object with ID and metadata
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
async def list_safes(
    search: Optional[str] = None,
    offset: Optional[int] = None,
    limit: Optional[int] = None,
    sort: Optional[str] = None,
    include_accounts: Optional[bool] = None,
    extended_details: Optional[bool] = None
) -> List[Dict[str, Any]]:
    """
    List all accessible safes in CyberArk Privilege Cloud.
    
    Args:
        search: Search term for safe names (URL encoded automatically)
        offset: Offset of the first Safe returned (default: 0)
        limit: Maximum number of Safes returned (default: 25)
        sort: Sort order - "safeName asc" or "safeName desc" (default: safeName asc)
        include_accounts: Whether to include accounts for each Safe (default: False)
        extended_details: Whether to return all Safe details or only safeName (default: True)
    
    Returns:
        List of safe objects (excludes Internal Safes)
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
    Get detailed information about a specific safe.
    
    Args:
        safe_name: Name of the safe (special characters will be URL encoded automatically)
        include_accounts: Whether to include accounts for the Safe (default: False)
        use_cache: Whether to retrieve from session cache (default: False)
    
    Returns:
        Safe object with detailed information
        
    Note:
        For safe names with special characters like dots (.), the API may require
        special handling. Contact your CyberArk administrator if you encounter issues.
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
    Perform a health check of the CyberArk connection.
    
    Returns:
        Health status information
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
    List available platforms in CyberArk Privilege Cloud.
    
    Args:
        search: Search term for platform names
        active: Filter by active status (true/false)
        system_type: Filter by system type (e.g., Windows, Unix)
    
    Returns:
        List of platform objects
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
    Get detailed information about a specific platform.
    
    Args:
        platform_id: Unique identifier for the platform (e.g., WinServerLocal, UnixSSH)
    
    Returns:
        Platform object with detailed configuration information
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
    Import a platform package to CyberArk Privilege Cloud.
    
    Args:
        platform_package_file: Path to the platform package ZIP file to import.
                              Must be a valid ZIP file and not exceed 20MB.
    
    Returns:
        Dict containing the imported platform ID
    
    Note:
        - The platform package file must be a ZIP file containing platform definition and dependencies
        - Maximum file size is 20MB
        - Supports all four platform types: Target, Dependent, Group, and Rotational group
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