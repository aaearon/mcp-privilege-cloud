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
async def list_safes(
    search: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    List all accessible safes in CyberArk Privilege Cloud.
    
    Args:
        search: Search term for safe names
    
    Returns:
        List of safe objects
    """
    try:
        server = CyberArkMCPServer.from_environment()
        safes = await server.list_safes(search=search)
        logger.info(f"Retrieved {len(safes)} safes")
        return safes
    except Exception as e:
        logger.error(f"Error listing safes: {e}")
        raise


@mcp.tool()
async def get_safe_details(
    safe_name: str
) -> Dict[str, Any]:
    """
    Get detailed information about a specific safe.
    
    Args:
        safe_name: Name of the safe
    
    Returns:
        Safe object with detailed information
    """
    try:
        server = CyberArkMCPServer.from_environment()
        safe = await server.get_safe_details(safe_name)
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