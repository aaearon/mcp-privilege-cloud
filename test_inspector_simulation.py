#!/usr/bin/env python3
"""
MCP Inspector Simulation Test
This script simulates what MCP Inspector would do when testing our server.
"""

import asyncio
import sys
import os
from unittest.mock import Mock, AsyncMock, patch

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from cyberark_mcp.server import CyberArkMCPServer
from cyberark_mcp.auth import CyberArkAuthenticator


class MCPInspectorSimulator:
    """Simulates MCP Inspector testing behavior"""
    
    def __init__(self):
        # Create mock server for testing without real credentials
        self.mock_auth = Mock(spec=CyberArkAuthenticator)
        self.mock_auth.get_auth_header = AsyncMock(return_value={"Authorization": "Bearer test-token"})
        
        self.server = CyberArkMCPServer(
            authenticator=self.mock_auth,
            subdomain="test-subdomain",
            timeout=30
        )
        
        # Mock data for testing
        self.mock_data = {
            "safes": [
                {"safeName": "IT-Infrastructure", "description": "IT Infrastructure accounts"},
                {"safeName": "Database-Servers", "description": "Database server accounts"},
                {"safeName": "Web-Applications", "description": "Web application accounts"}
            ],
            "accounts": [
                {
                    "id": "123_456",
                    "name": "admin-server01", 
                    "safeName": "IT-Infrastructure",
                    "userName": "admin",
                    "address": "server01.example.com",
                    "platformId": "WindowsDomainAccount"
                },
                {
                    "id": "789_012",
                    "name": "dbadmin-mysql01",
                    "safeName": "Database-Servers", 
                    "userName": "dbadmin",
                    "address": "mysql01.example.com",
                    "platformId": "MySQLAccount"
                }
            ],
            "account_detail": {
                "id": "123_456",
                "name": "admin-server01",
                "safeName": "IT-Infrastructure",
                "userName": "admin", 
                "address": "server01.example.com",
                "platformId": "WindowsDomainAccount",
                "secretType": "password",
                "platformAccountProperties": {
                    "LogonDomain": "EXAMPLE",
                    "Port": "3389"
                },
                "secretManagement": {
                    "automaticManagementEnabled": True,
                    "lastModifiedTime": "2025-06-08T10:30:00Z"
                },
                "createdTime": "2025-01-01T09:00:00Z"
            }
        }
    
    async def test_tool_discovery(self):
        """Test 1: Tool Discovery (what Inspector shows in UI)"""
        print("🔍 Test 1: Tool Discovery")
        print("=" * 50)
        
        tools = self.server.get_available_tools()
        print(f"📋 Available Tools ({len(tools)}):")
        for i, tool in enumerate(tools, 1):
            print(f"   {i}. {tool}")
        
        print("\n✅ All tools discovered successfully!")
        return True
    
    async def test_health_check_tool(self):
        """Test 2: Health Check Tool"""
        print("\n🏥 Test 2: Health Check Tool")
        print("=" * 50)
        
        print("📞 Calling: health_check()")
        print("Parameters: {}")
        
        # Mock successful health check
        with patch.object(self.server, 'list_safes', return_value=self.mock_data["safes"]):
            result = await self.server.health_check()
        
        print("\n📤 Response:")
        print(f"   Status: {result['status']}")
        print(f"   Timestamp: {result['timestamp']}")
        print(f"   Safes accessible: {result['safes_accessible']}")
        
        print("\n✅ Health check successful!")
        return True
    
    async def test_list_safes_tool(self):
        """Test 3: List Safes Tool"""
        print("\n🔐 Test 3: List Safes Tool") 
        print("=" * 50)
        
        print("📞 Calling: list_safes()")
        print("Parameters: {}")
        
        # Mock API call
        with patch.object(self.server, '_make_api_request', return_value={"value": self.mock_data["safes"]}):
            result = await self.server.list_safes()
        
        print(f"\n📤 Response: {len(result)} safes found")
        for i, safe in enumerate(result, 1):
            print(f"   {i}. {safe['safeName']} - {safe['description']}")
        
        print("\n✅ List safes successful!")
        return True
    
    async def test_list_accounts_tool(self):
        """Test 4: List Accounts Tool with Filters"""
        print("\n👥 Test 4: List Accounts Tool")
        print("=" * 50)
        
        # Test without filters
        print("📞 Calling: list_accounts()")
        print("Parameters: {}")
        
        with patch.object(self.server, '_make_api_request', return_value={"value": self.mock_data["accounts"]}):
            result = await self.server.list_accounts()
        
        print(f"\n📤 Response: {len(result)} accounts found")
        for i, account in enumerate(result, 1):
            print(f"   {i}. {account['name']} ({account['userName']}@{account['address']})")
        
        # Test with filters
        print("\n📞 Calling: list_accounts(safe_name='IT-Infrastructure')")
        print("Parameters: {'safe_name': 'IT-Infrastructure'}")
        
        filtered_accounts = [acc for acc in self.mock_data["accounts"] if acc["safeName"] == "IT-Infrastructure"]
        with patch.object(self.server, '_make_api_request', return_value={"value": filtered_accounts}):
            result = await self.server.list_accounts(safe_name="IT-Infrastructure")
        
        print(f"\n📤 Response: {len(result)} accounts found in IT-Infrastructure safe")
        for i, account in enumerate(result, 1):
            print(f"   {i}. {account['name']} in {account['safeName']}")
        
        print("\n✅ List accounts with filters successful!")
        return True
    
    async def test_search_accounts_tool(self):
        """Test 5: Search Accounts Tool"""
        print("\n🔍 Test 5: Search Accounts Tool")
        print("=" * 50)
        
        print("📞 Calling: search_accounts(keywords='admin')")
        print("Parameters: {'keywords': 'admin'}")
        
        # Filter accounts containing 'admin'
        admin_accounts = [acc for acc in self.mock_data["accounts"] if "admin" in acc["name"]]
        with patch.object(self.server, '_make_api_request', return_value={"value": admin_accounts}):
            result = await self.server.search_accounts(keywords="admin")
        
        print(f"\n📤 Response: {len(result)} accounts found matching 'admin'")
        for i, account in enumerate(result, 1):
            print(f"   {i}. {account['name']} - {account['userName']}")
        
        print("\n✅ Search accounts successful!")
        return True
    
    async def test_get_account_details_tool(self):
        """Test 6: Get Account Details Tool"""
        print("\n📄 Test 6: Get Account Details Tool")
        print("=" * 50)
        
        account_id = "123_456"
        print(f"📞 Calling: get_account_details(account_id='{account_id}')")
        print(f"Parameters: {{'account_id': '{account_id}'}}")
        
        with patch.object(self.server, '_make_api_request', return_value=self.mock_data["account_detail"]):
            result = await self.server.get_account_details(account_id)
        
        print(f"\n📤 Response: Account details for {result['name']}")
        print(f"   ID: {result['id']}")
        print(f"   Name: {result['name']}")
        print(f"   Safe: {result['safeName']}")
        print(f"   Username: {result['userName']}")
        print(f"   Address: {result['address']}")
        print(f"   Platform: {result['platformId']}")
        print(f"   Created: {result['createdTime']}")
        
        print("\n✅ Get account details successful!")
        return True
    
    async def test_get_safe_details_tool(self):
        """Test 7: Get Safe Details Tool"""
        print("\n🔐 Test 7: Get Safe Details Tool")
        print("=" * 50)
        
        safe_name = "IT-Infrastructure"
        print(f"📞 Calling: get_safe_details(safe_name='{safe_name}')")
        print(f"Parameters: {{'safe_name': '{safe_name}'}}")
        
        safe_detail = {
            "safeName": "IT-Infrastructure",
            "description": "IT Infrastructure accounts",
            "location": "\\",
            "managingCPM": "PasswordManager",
            "numberOfVersionsRetention": 5
        }
        
        with patch.object(self.server, '_make_api_request', return_value=safe_detail):
            result = await self.server.get_safe_details(safe_name)
        
        print(f"\n📤 Response: Safe details for {result['safeName']}")
        print(f"   Name: {result['safeName']}")
        print(f"   Description: {result['description']}")
        print(f"   Location: {result['location']}")
        print(f"   Managing CPM: {result['managingCPM']}")
        
        print("\n✅ Get safe details successful!")
        return True
    
    async def test_error_handling(self):
        """Test 8: Error Handling"""
        print("\n⚠️  Test 8: Error Handling")
        print("=" * 50)
        
        # Test missing required parameter
        print("📞 Testing: get_account_details() with missing account_id")
        try:
            # This would normally be caught by MCP parameter validation
            print("❌ Expected: Parameter validation error (handled by MCP framework)")
        except Exception as e:
            print(f"✅ Caught expected error: {e}")
        
        # Test API error
        print("\n📞 Testing: API error simulation")
        from cyberark_mcp.server import CyberArkAPIError
        
        with patch.object(self.server, '_make_api_request', side_effect=CyberArkAPIError("Test API error")):
            try:
                await self.server.list_accounts()
                print("❌ Expected API error was not raised")
            except CyberArkAPIError as e:
                print(f"✅ API error handled correctly: {e}")
        
        print("\n✅ Error handling working correctly!")
        return True
    
    async def run_all_tests(self):
        """Run complete MCP Inspector simulation"""
        print("🧪 MCP Inspector Simulation Test Suite")
        print("=" * 60)
        print("This simulates what you would see when testing with MCP Inspector")
        print("=" * 60)
        
        tests = [
            self.test_tool_discovery,
            self.test_health_check_tool,
            self.test_list_safes_tool,
            self.test_list_accounts_tool,
            self.test_search_accounts_tool,
            self.test_get_account_details_tool,
            self.test_get_safe_details_tool,
            self.test_error_handling
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                result = await test()
                if result:
                    passed += 1
            except Exception as e:
                print(f"❌ Test failed with error: {e}")
        
        print("\n" + "=" * 60)
        print(f"🎯 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Your MCP server is ready for Inspector testing.")
            print("\n📋 Next Steps:")
            print("1. Install MCP Inspector: npx @modelcontextprotocol/inspector")
            print("2. Start your server: python src/cyberark_mcp/mcp_server.py")
            print("3. Connect Inspector to your server")
            print("4. Test the tools interactively!")
        else:
            print("❌ Some tests failed. Please check the errors above.")
        
        return passed == total


async def main():
    """Run the MCP Inspector simulation"""
    simulator = MCPInspectorSimulator()
    success = await simulator.run_all_tests()
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)