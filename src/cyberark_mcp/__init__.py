"""
CyberArk Privilege Cloud MCP Server

This package provides MCP server functionality for CyberArk Privilege Cloud integration.
"""

import logging
import sys
from typing import NoReturn


def main() -> NoReturn:
    """
    Main entry point for the CyberArk Privilege Cloud MCP Server.
    
    This function serves as the primary entry point when the package is installed
    and called via `uvx cyberark-mcp-server` or similar console scripts.
    
    It delegates to the main() function in mcp_server.py which handles:
    - Environment variable validation
    - Logging configuration
    - MCP server initialization and execution
    
    Raises:
        SystemExit: If there are configuration errors or the server cannot start
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Import and delegate to the actual server main function
        from .mcp_server import main as server_main
        logger.info("Starting CyberArk Privilege Cloud MCP Server via main entry point")
        server_main()
    except ImportError as e:
        logger.error(f"Failed to import MCP server module: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to start MCP server: {e}")
        sys.exit(1)