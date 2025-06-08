#!/usr/bin/env python3
"""
Diagnostic script to troubleshoot CyberArk MCP Server issues
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def check_environment():
    """Check environment variables"""
    print("🔍 Checking Environment Variables")
    print("=" * 50)
    
    required_vars = [
        'CYBERARK_IDENTITY_TENANT_ID',
        'CYBERARK_CLIENT_ID',
        'CYBERARK_CLIENT_SECRET', 
        'CYBERARK_SUBDOMAIN'
    ]
    
    optional_vars = [
        'CYBERARK_API_TIMEOUT',
        'CYBERARK_MAX_RETRIES',
        'CYBERARK_LOG_LEVEL'
    ]
    
    missing_required = []
    
    print("Required Variables:")
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Show first 3 chars and length for security
            masked = f"{value[:3]}{'*' * (len(value) - 3)}" if len(value) > 3 else "***"
            print(f"  ✅ {var} = {masked} (length: {len(value)})")
        else:
            print(f"  ❌ {var} = NOT SET")
            missing_required.append(var)
    
    print("\nOptional Variables:")
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print(f"  ✅ {var} = {value}")
        else:
            print(f"  ⚪ {var} = not set (using default)")
    
    return missing_required

def check_imports():
    """Check if imports work"""
    print("\n🔧 Checking Imports")
    print("=" * 50)
    
    try:
        print("Testing: import cyberark_mcp.auth")
        from cyberark_mcp.auth import CyberArkAuthenticator
        print("  ✅ Authentication module imported successfully")
    except Exception as e:
        print(f"  ❌ Authentication import failed: {e}")
        return False
    
    try:
        print("Testing: import cyberark_mcp.server")
        from cyberark_mcp.server import CyberArkMCPServer
        print("  ✅ Server module imported successfully")
    except Exception as e:
        print(f"  ❌ Server import failed: {e}")
        return False
    
    try:
        print("Testing: import cyberark_mcp.mcp_server")
        from cyberark_mcp.mcp_server import mcp
        print("  ✅ MCP server module imported successfully")
    except Exception as e:
        print(f"  ❌ MCP server import failed: {e}")
        return False
    
    return True

def check_dependencies():
    """Check required dependencies"""
    print("\n📦 Checking Dependencies")
    print("=" * 50)
    
    required_packages = [
        'mcp',
        'httpx',
        'pydantic',
        'dotenv'  # python-dotenv imports as 'dotenv'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"  ✅ {package} is installed")
        except ImportError:
            print(f"  ❌ {package} is NOT installed")
            missing_packages.append(package)
    
    return missing_packages

def test_basic_functionality():
    """Test basic functionality"""
    print("\n🧪 Testing Basic Functionality")
    print("=" * 50)
    
    try:
        from cyberark_mcp.auth import CyberArkAuthenticator
        
        # Test authenticator creation
        auth = CyberArkAuthenticator(
            identity_tenant_id="test",
            client_id="test", 
            client_secret="test"
        )
        print("  ✅ Can create CyberArkAuthenticator")
        
        # Test URL construction
        url = auth._get_token_url()
        expected = "https://test.id.cyberark.cloud/oauth2/platformtoken"
        if url == expected:
            print("  ✅ Token URL construction works")
        else:
            print(f"  ❌ Token URL wrong: got {url}, expected {expected}")
        
    except Exception as e:
        print(f"  ❌ Basic functionality test failed: {e}")
        return False
    
    try:
        from cyberark_mcp.server import CyberArkMCPServer
        from unittest.mock import Mock, AsyncMock
        
        # Test server creation
        mock_auth = Mock()
        mock_auth.get_auth_header = AsyncMock(return_value={"Authorization": "Bearer test"})
        
        server = CyberArkMCPServer(
            authenticator=mock_auth,
            subdomain="test"
        )
        print("  ✅ Can create CyberArkMCPServer")
        
        # Test available tools
        tools = server.get_available_tools()
        if len(tools) >= 5:
            print(f"  ✅ Server has {len(tools)} tools available")
        else:
            print(f"  ❌ Server has only {len(tools)} tools, expected at least 5")
        
    except Exception as e:
        print(f"  ❌ Server functionality test failed: {e}")
        return False
    
    return True

def test_environment_loading():
    """Test loading from environment"""
    print("\n🌍 Testing Environment Loading")
    print("=" * 50)
    
    missing_vars = check_environment()
    if missing_vars:
        print(f"  ❌ Cannot test - missing required variables: {missing_vars}")
        return False
    
    try:
        from cyberark_mcp.auth import CyberArkAuthenticator
        auth = CyberArkAuthenticator.from_environment()
        print("  ✅ Can create authenticator from environment")
        
        from cyberark_mcp.server import CyberArkMCPServer  
        server = CyberArkMCPServer.from_environment()
        print("  ✅ Can create server from environment")
        
    except Exception as e:
        print(f"  ❌ Environment loading failed: {e}")
        return False
    
    return True

def load_env_file():
    """Load .env file if it exists"""
    env_file = '.env'
    if os.path.exists(env_file):
        print(f"📁 Loading {env_file}")
        try:
            from dotenv import load_dotenv
            load_dotenv()
            print("  ✅ .env file loaded successfully")
        except ImportError:
            print("  ⚠️  python-dotenv not available, reading manually")
            # Manual .env parsing
            with open(env_file) as f:
                for line in f:
                    if '=' in line and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        os.environ[key] = value
        except Exception as e:
            print(f"  ❌ Failed to load .env: {e}")
    else:
        print("  ⚪ No .env file found")

def main():
    """Run all diagnostics"""
    print("🔍 CyberArk MCP Server Diagnostics")
    print("=" * 60)
    
    # Load environment
    load_env_file()
    
    # Run checks
    missing_deps = check_dependencies()
    if missing_deps:
        print(f"\n❌ Missing dependencies: {missing_deps}")
        print("Run: pip install -r requirements.txt")
        return
    
    imports_ok = check_imports()
    if not imports_ok:
        print("\n❌ Import issues detected")
        return
    
    basic_ok = test_basic_functionality()
    if not basic_ok:
        print("\n❌ Basic functionality issues detected")
        return
    
    env_ok = test_environment_loading()
    
    print("\n" + "=" * 60)
    if env_ok:
        print("🎉 All diagnostics passed! Your setup looks good.")
        print("\n📋 Next steps:")
        print("1. Try starting the server: python run_server.py")
        print("2. If it still fails, share the exact error message")
    else:
        print("⚠️  Some issues detected. Check the output above.")
        print("\n🔧 Common fixes:")
        print("1. Verify your .env file values")
        print("2. Check CyberArk service account setup")
        print("3. Verify network connectivity")

if __name__ == "__main__":
    main()