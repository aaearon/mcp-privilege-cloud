"""
Entry point for running the CyberArk MCP server as a module.

Usage:
    python -m mcp_privilege_cloud
"""

if __name__ == "__main__":
    try:
        from .mcp_server import main
        main()
    except ImportError as e:
        print(f"Error importing main function: {e}")
        print("Please ensure the package is properly installed.")
        exit(1)
    except Exception as e:
        print(f"Error running MCP server: {e}")
        exit(1)