#!/usr/bin/env python3
"""
Test the fixed MCP server tools
"""

import os
import sys
import asyncio

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_tools():
    """Test the MCP tools directly"""
    print("[INFO] Testing fixed MCP server tools...")
    
    # Load environment
    from dotenv import load_dotenv
    load_dotenv()
    
    # Import the tool functions directly
    from cyberark_mcp.mcp_server import health_check, list_safes, list_accounts
    
    try:
        print("\n[TEST 1] Health Check...")
        health = await health_check()
        print(f"Health Status: {health['status']}")
        
        if health['status'] == 'healthy':
            print("\n[TEST 2] List Safes...")
            safes = await list_safes()
            print(f"Found {len(safes)} safes")
            
            print("\n[TEST 3] List Accounts...")
            accounts = await list_accounts()
            print(f"Found {len(accounts)} accounts")
            
            print("\n[SUCCESS] All tools working correctly!")
            return True
        else:
            print(f"[ERROR] Health check failed: {health.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"[ERROR] Tool test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_tools())
    if success:
        print("\n[OK] MCP server tools are working correctly!")
        print("You can now restart Claude Desktop and the tools should work.")
    else:
        print("\n[FAIL] MCP server tools have issues.")
        print("Check your CyberArk credentials and network connectivity.")