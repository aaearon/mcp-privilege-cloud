#!/usr/bin/env python3
"""
CyberArk Privilege Cloud MCP Server

This server provides tools for interacting with CyberArk Privilege Cloud
through the Model Context Protocol (MCP).
"""

import json
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


# New tool functions to replace resources - return raw API data
@mcp.tool()
async def list_accounts() -> List[Dict[str, Any]]:
    """List all accessible accounts in CyberArk Privilege Cloud.
    
    Returns:
        List of account objects with their exact API fields
    """
    try:
        server = CyberArkMCPServer.from_environment()
        return await server.list_accounts()
    except Exception as e:
        logger.error(f"Error listing accounts: {e}")
        raise

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
    try:
        server = CyberArkMCPServer.from_environment()
        return await server.search_accounts(
            keywords=query,
            safe_name=safe_name,
            username=username,
            address=address,
            platform_id=platform_id
        )
    except Exception as e:
        logger.error(f"Error searching accounts: {e}")
        raise

@mcp.tool()
async def list_safes() -> List[Dict[str, Any]]:
    """List all accessible safes in CyberArk Privilege Cloud.
    
    Returns:
        List of safe objects with their exact API fields
    """
    try:
        server = CyberArkMCPServer.from_environment()
        return await server.list_safes()
    except Exception as e:
        logger.error(f"Error listing safes: {e}")
        raise

@mcp.tool()
async def list_platforms() -> List[Dict[str, Any]]:
    """List all available platforms in CyberArk Privilege Cloud.
    
    Returns:
        List of platform objects with their exact API fields
    """
    try:
        server = CyberArkMCPServer.from_environment()
        return await server.list_platforms()
    except Exception as e:
        logger.error(f"Error listing platforms: {e}")
        raise








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