#!/usr/bin/env python3
"""
Debug script to test CyberArk Platform API response parsing
This script helps verify that the API response parsing fix is working correctly.
"""

import asyncio
import os
import json
from src.cyberark_mcp.server import CyberArkMCPServer

async def test_platform_api():
    """Test the platform API directly"""
    try:
        # Initialize server from environment
        server = CyberArkMCPServer.from_environment()
        
        print("🔍 Testing CyberArk Platform API...")
        print(f"API Base URL: {server.base_url}")
        
        # Test list_platforms
        print("\n📋 Testing list_platforms...")
        platforms = await server.list_platforms()
        print(f"✅ Retrieved {len(platforms)} platforms")
        
        if platforms:
            print("\n🔧 Platform Summary:")
            for platform in platforms[:5]:  # Show first 5 platforms
                platform_id = platform.get('id', 'Unknown')
                platform_name = platform.get('Name', platform.get('name', 'Unknown'))
                system_type = platform.get('SystemType', platform.get('systemType', 'Unknown'))
                active = platform.get('Active', platform.get('active', 'Unknown'))
                print(f"  • {platform_id}: {platform_name} ({system_type}) - Active: {active}")
            
            if len(platforms) > 5:
                print(f"  ... and {len(platforms) - 5} more platforms")
            
            # Test get_platform_details with first platform
            if platforms:
                first_platform_id = platforms[0].get('id')
                if first_platform_id:
                    print(f"\n🔍 Testing get_platform_details for '{first_platform_id}'...")
                    details = await server.get_platform_details(first_platform_id)
                    print(f"✅ Retrieved detailed configuration for platform '{first_platform_id}'")
                    
                    # Show some key details
                    if 'Details' in details:
                        cmp = details['Details'].get('CredentialsManagementPolicy', {})
                        if cmp:
                            print(f"  • Password Change: {cmp.get('Change', 'Unknown')}")
                            print(f"  • Password Verify: {cmp.get('Verify', 'Unknown')}")
        else:
            print("⚠️  No platforms found. This could indicate:")
            print("   1. The service account is not a member of the Privilege Cloud Administrator role")
            print("   2. There are no platforms configured in this tenant")
            print("   3. The API response format has changed")
        
        # Test with filters
        print("\n🔍 Testing list_platforms with active=true filter...")
        active_platforms = await server.list_platforms(active=True)
        print(f"✅ Retrieved {len(active_platforms)} active platforms")
        
        print("\n🎉 Platform API testing completed successfully!")
        
    except Exception as e:
        print(f"❌ Error testing platform API: {e}")
        print("\n🔧 Troubleshooting tips:")
        print("   1. Verify environment variables are set correctly")
        print("   2. Check that the service account is a member of the Privilege Cloud Administrator role")
        print("   3. Ensure the CyberArk tenant has platforms configured")
        raise

async def debug_api_response():
    """Debug the raw API response to see the exact structure"""
    try:
        server = CyberArkMCPServer.from_environment()
        
        print("\n🔍 Making raw API request to debug response structure...")
        response = await server._make_api_request("GET", "Platforms", params={"active": "true"})
        
        print("📊 Raw API Response Structure:")
        print(json.dumps(response, indent=2))
        
        # Check what fields are available
        print(f"\n🔑 Available response fields: {list(response.keys())}")
        
        if 'Platforms' in response:
            platforms = response['Platforms']
            print(f"✅ Found 'Platforms' field with {len(platforms)} entries")
            if platforms:
                print(f"📋 First platform structure: {list(platforms[0].keys())}")
        elif 'value' in response:
            platforms = response['value']
            print(f"✅ Found 'value' field with {len(platforms)} entries")
        else:
            print("⚠️  Neither 'Platforms' nor 'value' field found in response")
            
    except Exception as e:
        print(f"❌ Error debugging API response: {e}")
        raise

if __name__ == "__main__":
    print("🚀 CyberArk Platform API Debug Script")
    print("=" * 50)
    
    # Check environment variables
    required_vars = [
        "CYBERARK_IDENTITY_TENANT_ID",
        "CYBERARK_CLIENT_ID", 
        "CYBERARK_CLIENT_SECRET",
        "CYBERARK_SUBDOMAIN"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"❌ Missing required environment variables: {missing_vars}")
        exit(1)
    
    print("✅ All required environment variables are set")
    
    # Run tests
    try:
        asyncio.run(test_platform_api())
        print("\n" + "=" * 50)
        asyncio.run(debug_api_response())
    except KeyboardInterrupt:
        print("\n🛑 Script interrupted by user")
    except Exception as e:
        print(f"\n💥 Script failed: {e}")
        exit(1)