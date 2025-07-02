#!/usr/bin/env python3
"""
Script to verify platform API endpoints and understand their responses.

This script tests both platform API endpoints:
1. GET /PasswordVault/API/Platforms/ - Get platforms list
2. GET /PasswordVault/API/Platforms/{PlatformName}/ - Get platform details

The goal is to understand the differences in the response structure
and plan how to combine the information for a complete platform resource.
"""

import asyncio
import json
import os
import sys
from typing import Dict, Any, List, Optional
from pathlib import Path

# Add project src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mcp_privilege_cloud.auth import CyberArkAuthenticator
from mcp_privilege_cloud.server import CyberArkMCPServer


async def test_platform_apis():
    """Test both platform API endpoints and analyze their responses."""
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Initialize auth and server
    auth = CyberArkAuthenticator(
        identity_tenant_id=os.getenv("CYBERARK_IDENTITY_TENANT_ID"),
        client_id=os.getenv("CYBERARK_CLIENT_ID"),
        client_secret=os.getenv("CYBERARK_CLIENT_SECRET")
    )
    
    server = CyberArkMCPServer(
        authenticator=auth,
        subdomain=os.getenv("CYBERARK_SUBDOMAIN")
    )
    
    print("=== Testing Platform API Endpoints ===\n")
    
    try:
        # Test 1: Get platforms list (current implementation)
        print("1. Testing GET /PasswordVault/API/Platforms/ (Get platforms list)")
        print("-" * 60)
        
        platforms_response = await server._make_api_request("GET", "Platforms")
        platforms_list = platforms_response.get("Platforms", [])
        
        print(f"Response structure keys: {list(platforms_response.keys())}")
        print(f"Number of platforms returned: {len(platforms_list)}")
        
        if platforms_list:
            first_platform = platforms_list[0]
            print(f"\nFirst platform structure keys: {list(first_platform.keys())}")
            print(f"First platform general info keys: {list(first_platform.get('general', {}).keys())}")
            
            # Save sample platform list response
            with open("sample_platforms_list_response.json", "w") as f:
                json.dump(platforms_response, f, indent=2)
            print(f"Sample response saved to: sample_platforms_list_response.json")
            
            # Test 2: Get platform details for the first platform
            platform_id = first_platform.get("general", {}).get("id")
            if platform_id:
                print(f"\n2. Testing GET /PasswordVault/API/Platforms/{platform_id}/ (Get platform details)")
                print("-" * 60)
                
                try:
                    details_response = await server._make_api_request("GET", f"Platforms/{platform_id}")
                    
                    print(f"Platform details response keys: {list(details_response.keys())}")
                    
                    # Save sample platform details response
                    with open("sample_platform_details_response.json", "w") as f:
                        json.dump(details_response, f, indent=2)
                    print(f"Sample details response saved to: sample_platform_details_response.json")
                    
                    # Compare the two responses
                    print(f"\n3. Comparing the two API responses")
                    print("-" * 60)
                    
                    print("Fields only in list API:")
                    list_fields = set(get_all_keys(first_platform))
                    details_fields = set(get_all_keys(details_response))
                    
                    only_in_list = list_fields - details_fields
                    only_in_details = details_fields - list_fields
                    common_fields = list_fields & details_fields
                    
                    print(f"  - {sorted(only_in_list)}")
                    print(f"\nFields only in details API:")
                    print(f"  - {sorted(only_in_details)}")
                    print(f"\nCommon fields: {len(common_fields)}")
                    
                    # Test with a few more platforms for comparison
                    print(f"\n4. Testing platform details for multiple platforms")
                    print("-" * 60)
                    
                    platforms_to_test = platforms_list[:3]  # Test first 3 platforms
                    all_details = {}
                    
                    for i, platform in enumerate(platforms_to_test):
                        platform_id = platform.get("general", {}).get("id")
                        if platform_id:
                            try:
                                details = await server._make_api_request("GET", f"Platforms/{platform_id}")
                                all_details[platform_id] = details
                                print(f"  ✓ Successfully got details for platform: {platform_id}")
                            except Exception as e:
                                print(f"  ✗ Failed to get details for platform {platform_id}: {e}")
                    
                    # Save all details for analysis
                    with open("sample_multiple_platform_details.json", "w") as f:
                        json.dump(all_details, f, indent=2)
                    print(f"\nMultiple platform details saved to: sample_multiple_platform_details.json")
                    
                except Exception as e:
                    print(f"Error getting platform details: {e}")
            else:
                print("No platform ID found in first platform")
        
        else:
            print("No platforms returned from the API")
            
    except Exception as e:
        print(f"Error during API testing: {e}")
        import traceback
        traceback.print_exc()


def get_all_keys(obj: Any, prefix: str = "") -> List[str]:
    """Recursively get all keys from a nested dictionary."""
    keys = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            full_key = f"{prefix}.{key}" if prefix else key
            keys.append(full_key)
            if isinstance(value, dict):
                keys.extend(get_all_keys(value, full_key))
            elif isinstance(value, list) and value and isinstance(value[0], dict):
                keys.extend(get_all_keys(value[0], f"{full_key}[0]"))
    return keys


def analyze_structure_differences():
    """Analyze the differences between the saved API responses."""
    print("\n=== Analysis of API Response Differences ===\n")
    
    try:
        # Load the saved responses
        with open("sample_platforms_list_response.json", "r") as f:
            list_response = json.load(f)
        
        with open("sample_platform_details_response.json", "r") as f:
            details_response = json.load(f)
        
        # Analyze the structure
        print("List API Response Structure:")
        print(f"  - Top level keys: {list(list_response.keys())}")
        
        if "Platforms" in list_response and list_response["Platforms"]:
            platform = list_response["Platforms"][0]
            print(f"  - Platform object keys: {list(platform.keys())}")
            for key, value in platform.items():
                if isinstance(value, dict):
                    print(f"    - {key}: {list(value.keys())}")
        
        print(f"\nDetails API Response Structure:")
        print(f"  - Top level keys: {list(details_response.keys())}")
        
        # Check what additional information is in details API
        if "Properties" in details_response:
            print(f"  - Properties count: {len(details_response.get('Properties', []))}")
            if details_response.get('Properties'):
                sample_props = details_response['Properties'][:3]
                print(f"  - Sample properties: {sample_props}")
        
    except FileNotFoundError as e:
        print(f"Could not load saved responses: {e}")
        print("Please run the API tests first.")


if __name__ == "__main__":
    # Run the API tests
    asyncio.run(test_platform_apis())
    
    # Analyze the differences
    analyze_structure_differences()
    
    print("\n=== Summary ===")
    print("The script has tested both platform API endpoints and saved sample responses.")
    print("Review the JSON files and output above to understand the differences.")
    print("This information will be used to plan the implementation for complete platform information.")