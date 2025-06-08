#!/usr/bin/env python3
"""
Quick test script to verify the CyberArk MCP Server MVP is working correctly.
This script tests basic functionality without requiring actual CyberArk credentials.
"""

import asyncio
import sys
import os
from unittest.mock import Mock, AsyncMock, patch

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from cyberark_mcp.server import CyberArkMCPServer
from cyberark_mcp.auth import CyberArkAuthenticator


async def test_mvp():
    """Test the MVP functionality"""
    print("🔧 Testing CyberArk Privilege Cloud MCP Server MVP...")
    
    # Test 1: Authentication Module
    print("\n1️⃣ Testing Authentication Module...")
    try:
        # Test authenticator initialization
        auth = CyberArkAuthenticator(
            identity_tenant_id="test-tenant",
            client_id="test-client", 
            client_secret="test-secret"
        )
        
        # Test URL construction
        token_url = auth._get_token_url()
        expected_url = "https://test-tenant.id.cyberark.cloud/oauth2/platformtoken"
        assert token_url == expected_url, f"Expected {expected_url}, got {token_url}"
        
        print("   ✅ Authentication module initialized correctly")
        print(f"   ✅ Token URL: {token_url}")
        
    except Exception as e:
        print(f"   ❌ Authentication test failed: {e}")
        return False
    
    # Test 2: Server Module  
    print("\n2️⃣ Testing Server Module...")
    try:
        # Create mock authenticator
        mock_auth = Mock(spec=CyberArkAuthenticator)
        mock_auth.get_auth_header = AsyncMock(return_value={"Authorization": "Bearer test-token"})
        
        # Test server initialization
        server = CyberArkMCPServer(
            authenticator=mock_auth,
            subdomain="test-subdomain",
            timeout=30
        )
        
        # Test URL construction
        api_url = server._get_api_url("Accounts")
        expected_url = "https://test-subdomain.privilegecloud.cyberark.com/PasswordVault/api/Accounts"
        assert api_url == expected_url, f"Expected {expected_url}, got {api_url}"
        
        # Test available tools
        tools = server.get_available_tools()
        expected_tools = ["list_accounts", "get_account_details", "search_accounts", "list_safes", "get_safe_details"]
        assert all(tool in tools for tool in expected_tools), f"Missing tools: {set(expected_tools) - set(tools)}"
        
        print("   ✅ Server module initialized correctly")
        print(f"   ✅ API URL: {api_url}")
        print(f"   ✅ Available tools: {tools}")
        
    except Exception as e:
        print(f"   ❌ Server test failed: {e}")
        return False
    
    # Test 3: Account Management Operations
    print("\n3️⃣ Testing Account Management Operations...")
    try:
        # Mock successful API responses
        mock_accounts = [
            {"id": "123", "name": "test-account", "safeName": "test-safe"},
            {"id": "456", "name": "admin-account", "safeName": "admin-safe"}
        ]
        
        mock_account_detail = {
            "id": "123",
            "name": "test-account", 
            "safeName": "test-safe",
            "userName": "testuser",
            "platformId": "TestPlatform"
        }
        
        # Test list_accounts
        with patch.object(server, '_make_api_request', return_value={"value": mock_accounts}):
            accounts = await server.list_accounts()
            assert len(accounts) == 2, f"Expected 2 accounts, got {len(accounts)}"
            print("   ✅ list_accounts working correctly")
        
        # Test get_account_details
        with patch.object(server, '_make_api_request', return_value=mock_account_detail):
            account = await server.get_account_details("123")
            assert account["name"] == "test-account", f"Expected 'test-account', got {account['name']}"
            print("   ✅ get_account_details working correctly")
        
        # Test search_accounts
        with patch.object(server, '_make_api_request', return_value={"value": [mock_accounts[0]]}):
            results = await server.search_accounts(keywords="test")
            assert len(results) == 1, f"Expected 1 result, got {len(results)}"
            print("   ✅ search_accounts working correctly")
        
    except Exception as e:
        print(f"   ❌ Account management test failed: {e}")
        return False
    
    # Test 4: Safe Management Operations
    print("\n4️⃣ Testing Safe Management Operations...")
    try:
        mock_safes = [
            {"safeName": "test-safe", "description": "Test Safe"},
            {"safeName": "admin-safe", "description": "Admin Safe"}
        ]
        
        mock_safe_detail = {
            "safeName": "test-safe",
            "description": "Test Safe",
            "location": "\\",
            "managingCPM": "PasswordManager"
        }
        
        # Test list_safes
        with patch.object(server, '_make_api_request', return_value={"value": mock_safes}):
            safes = await server.list_safes()
            assert len(safes) == 2, f"Expected 2 safes, got {len(safes)}"
            print("   ✅ list_safes working correctly")
        
        # Test get_safe_details
        with patch.object(server, '_make_api_request', return_value=mock_safe_detail):
            safe = await server.get_safe_details("test-safe")
            assert safe["safeName"] == "test-safe", f"Expected 'test-safe', got {safe['safeName']}"
            print("   ✅ get_safe_details working correctly")
        
    except Exception as e:
        print(f"   ❌ Safe management test failed: {e}")
        return False
    
    # Test 5: Health Check
    print("\n5️⃣ Testing Health Check...")
    try:
        with patch.object(server, 'list_safes', return_value=mock_safes):
            health = await server.health_check()
            assert health["status"] == "healthy", f"Expected 'healthy', got {health['status']}"
            assert "timestamp" in health, "Missing timestamp in health check"
            print("   ✅ Health check working correctly")
            print(f"   ✅ Health status: {health}")
        
    except Exception as e:
        print(f"   ❌ Health check test failed: {e}")
        return False
    
    # Test 6: MCP Server Integration
    print("\n6️⃣ Testing MCP Server Integration...")
    try:
        from cyberark_mcp.mcp_server import mcp
        assert mcp is not None, "MCP server not initialized"
        assert mcp.name == "CyberArk Privilege Cloud MCP Server", f"Unexpected server name: {mcp.name}"
        print("   ✅ MCP server integration working correctly")
        print(f"   ✅ Server name: {mcp.name}")
        
    except Exception as e:
        print(f"   ❌ MCP integration test failed: {e}")
        return False
    
    print("\n🎉 All MVP tests passed successfully!")
    print("\nNext Steps:")
    print("1. Set up your CyberArk environment variables (.env file)")
    print("2. Test with real CyberArk credentials using the health check")
    print("3. Use MCP Inspector to test the tools interactively")
    print("4. Integrate with your preferred MCP client")
    
    return True


def print_next_steps():
    """Print instructions for next steps"""
    print("\n" + "="*60)
    print("📋 MVP TESTING INSTRUCTIONS")
    print("="*60)
    
    print("\n🔧 Setup Instructions:")
    print("1. Copy .env.example to .env")
    print("2. Fill in your CyberArk credentials:")
    print("   - CYBERARK_IDENTITY_TENANT_ID")
    print("   - CYBERARK_CLIENT_ID") 
    print("   - CYBERARK_CLIENT_SECRET")
    print("   - CYBERARK_SUBDOMAIN")
    
    print("\n🏥 Health Check Test:")
    print("python -c \"")
    print("import asyncio")
    print("from src.cyberark_mcp.server import CyberArkMCPServer")
    print("server = CyberArkMCPServer.from_environment()")
    print("health = asyncio.run(server.health_check())")
    print("print('Health:', health['status'])")
    print("\"")
    
    print("\n🚀 Start MCP Server:")
    print("python src/cyberark_mcp/mcp_server.py")
    
    print("\n🔍 Test with MCP Inspector:")
    print("1. Install: npx @modelcontextprotocol/inspector")
    print("2. Connect to your server")
    print("3. Test available tools:")
    print("   - health_check")
    print("   - list_safes")
    print("   - list_accounts")
    print("   - search_accounts")
    print("   - get_account_details")
    print("   - get_safe_details")


if __name__ == "__main__":
    success = asyncio.run(test_mvp())
    if success:
        print_next_steps()
    else:
        print("\n❌ MVP tests failed. Please check the error messages above.")
        sys.exit(1)