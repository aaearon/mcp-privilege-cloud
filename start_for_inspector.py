#!/usr/bin/env python3
"""
Start CyberArk MCP Server for Inspector Testing

This script starts the server in a way that's easy to test with MCP Inspector,
even without real CyberArk credentials.
"""

import os
import sys
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def setup_test_environment():
    """Set up environment for testing without real credentials"""
    # Set minimal required env vars for testing (will fail auth but server will start)
    test_env = {
        'CYBERARK_IDENTITY_TENANT_ID': 'test-tenant',
        'CYBERARK_CLIENT_ID': 'test-client',
        'CYBERARK_CLIENT_SECRET': 'test-secret',
        'CYBERARK_SUBDOMAIN': 'test-subdomain',
        'CYBERARK_LOG_LEVEL': 'INFO'
    }
    
    for key, value in test_env.items():
        if not os.getenv(key):
            os.environ[key] = value
            print(f"🔧 Set {key} = {value} (for testing)")

def main():
    """Main entry point"""
    print("🚀 Starting CyberArk MCP Server for Inspector Testing")
    print("=" * 60)
    
    # Check if we have real credentials
    real_creds = all(os.getenv(var) for var in [
        'CYBERARK_IDENTITY_TENANT_ID',
        'CYBERARK_CLIENT_ID', 
        'CYBERARK_CLIENT_SECRET',
        'CYBERARK_SUBDOMAIN'
    ])
    
    if real_creds:
        print("✅ Real CyberArk credentials detected")
        print("   Server will connect to actual CyberArk APIs")
    else:
        print("⚠️  No real credentials found")
        print("   Setting up test environment for tool structure testing")
        setup_test_environment()
    
    print("\n📋 Inspector Connection Instructions:")
    print("1. Open MCP Inspector in your browser")
    print("2. Choose 'Command' connection type")
    print("3. Enter this command:")
    print(f"   python {os.path.abspath(__file__)}")
    print("4. Click 'Connect'")
    
    print("\n🛠️  Available Tools to Test:")
    tools = [
        "health_check - Check server connectivity",
        "list_safes - List accessible safes", 
        "list_accounts - List accounts with optional filters",
        "search_accounts - Advanced account search",
        "get_account_details - Get detailed account info",
        "get_safe_details - Get detailed safe info"
    ]
    for tool in tools:
        print(f"   • {tool}")
    
    print("\n🔄 Starting server...")
    print("=" * 60)
    
    # Import and start the server
    try:
        from cyberark_mcp.mcp_server import main as server_main
        server_main()
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        print("\n🔍 Troubleshooting:")
        print("1. Ensure virtual environment is activated")
        print("2. Check that dependencies are installed: pip install -r requirements.txt")
        print("3. Verify your .env file if using real credentials")

if __name__ == "__main__":
    main()