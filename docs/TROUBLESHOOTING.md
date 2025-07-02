# Troubleshooting Guide

Comprehensive troubleshooting guide for the CyberArk Privilege Cloud MCP Server. This guide consolidates all known issues, solutions, and debugging procedures from across the project documentation.

## Table of Contents

- [Quick Diagnostics](#quick-diagnostics)
- [Common Issues](#common-issues)
- [Authentication Problems](#authentication-problems)
- [Connection Issues](#connection-issues)
- [MCP Inspector Problems](#mcp-inspector-problems)
- [Import and Startup Errors](#import-and-startup-errors)
- [Platform Management Issues](#platform-management-issues)
- [Resource Access Issues](#resource-access-issues)
- [Debug Mode](#debug-mode)
- [Health Check Procedures](#health-check-procedures)
- [Advanced Debugging](#advanced-debugging)

## Quick Diagnostics

### Health Check Command
Run this command first to verify overall system health:
```bash
python -c "
import asyncio
from src.mcp_privilege_cloud.server import CyberArkMCPServer
server = CyberArkMCPServer.from_environment()
health = asyncio.run(server.health_check())
print(f'Status: {health['status']}')
if health['status'] == 'healthy':
    print(f'Safes accessible: {health['safes_accessible']}')
else:
    print(f'Error: {health['error']}')
"
```

### Environment Verification
```bash
# Check required environment variables
echo "Tenant ID: $CYBERARK_IDENTITY_TENANT_ID"
echo "Client ID: $CYBERARK_CLIENT_ID"
echo "Subdomain: $CYBERARK_SUBDOMAIN"
echo "Secret: ${CYBERARK_CLIENT_SECRET:+SET}"

# Verify Python environment
python --version
which python
pip list | grep mcp
```

### MVP Test
```bash
# Run the MVP test script (if available)
python test_mvp.py
```

## Common Issues

### 1. Missing Environment Variables

**Symptoms:**
```
ERROR - Missing required environment variables: ['CYBERARK_IDENTITY_TENANT_ID', 'CYBERARK_CLIENT_ID', 'CYBERARK_CLIENT_SECRET', 'CYBERARK_SUBDOMAIN']
```

**Solutions:**
1. **Create .env file:**
   ```bash
   cp .env.example .env
   nano .env  # Edit with your values
   ```

2. **Verify .env format:**
   ```bash
   # Correct format (no quotes, no trailing spaces)
   CYBERARK_IDENTITY_TENANT_ID=your-tenant-id
   CYBERARK_CLIENT_ID=your-service-account-username
   CYBERARK_CLIENT_SECRET=your-service-account-password
   CYBERARK_SUBDOMAIN=your-privilege-cloud-subdomain
   ```

3. **Check file permissions:**
   ```bash
   chmod 600 .env
   ls -la .env
   ```

4. **Verify no trailing spaces:**
   ```bash
   cat -A .env  # Shows all characters including spaces
   ```

### 2. Server Won't Start

**Symptoms:** Server exits immediately or shows import errors

**Diagnosis Commands:**
```bash
# Check Python environment
which python
python --version

# Check dependencies
pip list | grep mcp
pip list | grep fastapi

# Verify project structure
ls -la run_server.py
ls -la src/mcp_privilege_cloud/
```

**Solutions:**
1. **Use recommended entry point:**
   ```bash
   python run_server.py
   ```

2. **Check virtual environment:**
   ```bash
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate     # Windows
   ```

3. **Reinstall dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### 3. Unicode/Encoding Errors (Windows)

**Symptoms:**
```
UnicodeEncodeError: 'charmap' codec can't encode character
```

**Solutions:**
1. **Use the multiplatform launcher:**
   ```bash
   python run_server.py  # Handles Windows encoding automatically
   ```

2. **Set environment variables:**
   ```bash
   set PYTHONIOENCODING=utf-8
   set PYTHONLEGACYWINDOWSSTDIO=1
   python src/mcp_privilege_cloud/mcp_server.py
   ```

3. **Claude Desktop configuration:**
   ```json
   {
     "mcpServers": {
       "cyberark-privilege-cloud": {
         "command": "python",
         "args": ["C:/path/to/run_server.py"],
         "env": {
           "PYTHONIOENCODING": "utf-8",
           "PYTHONLEGACYWINDOWSSTDIO": "1"
         }
       }
     }
   }
   ```

## Authentication Problems

### 1. Authentication Failed (401 Unauthorized)

**Symptoms:**
```
Authentication failed: 401 Unauthorized
Error: Authentication failed
```

**Solutions:**
1. **Verify service account credentials:**
   ```bash
   # Test credentials manually
   curl -X POST "https://${CYBERARK_IDENTITY_TENANT_ID}.id.cyberark.cloud/oauth2/platformtoken" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "grant_type=client_credentials&client_id=${CYBERARK_CLIENT_ID}&client_secret=${CYBERARK_CLIENT_SECRET}"
   ```

2. **Check OAuth settings in CyberArk Identity:**
   - Verify service account exists
   - Ensure "Is OAuth confidential client" is enabled
   - Confirm client credentials are correct

3. **Verify tenant ID format:**
   ```bash
   # Correct: just the tenant ID
   CYBERARK_IDENTITY_TENANT_ID=abc123
   
   # Incorrect: includes full domain
   CYBERARK_IDENTITY_TENANT_ID=abc123.id.cyberark.cloud  # ❌
   ```

4. **Test authentication only:**
   ```bash
   python -c "
   from src.mcp_privilege_cloud.auth import CyberArkAuthenticator
   import asyncio
   auth = CyberArkAuthenticator.from_environment()
   print(asyncio.run(auth.get_auth_header()))
   "
   ```

### 2. Permission Errors (403 Forbidden)

**Symptoms:**
```
HTTP 403 Forbidden
Error: Insufficient permissions
```

**Solutions:**
1. **Verify safe-level permissions:**
   - Service account needs "List Accounts" permission in target safes
   - Check "View Safe Members" permission
   - Verify "View Account Details" permission

2. **Check Privilege Cloud Administrator role:**
   ```bash
   # For platform management operations
   # Service account must be member of Privilege Cloud Administrator role
   ```

3. **Test safes resource access:**
   ```bash
   python -c "
   from src.mcp_privilege_cloud.mcp_server import _read_resource_content
   import asyncio
   import json
   content = asyncio.run(_read_resource_content('cyberark://safes/'))
   data = json.loads(content)
   if 'error' in data:
       print(f'Error accessing safes: {data[\"error\"]}')
   else:
       safes = data.get('safes', [])
       print(f'Accessible safes: {len(safes)}')
       for safe in safes[:3]:
           print(f'- {safe.get(\"safeName\", \"Unknown\")}')
   "
   ```

## Connection Issues

### 1. Network Error: No Address Associated with Hostname

**Symptoms:**
```
Network error: No address associated with hostname
Could not resolve hostname
```

**Solutions:**
1. **Verify subdomain format:**
   ```bash
   # Correct: just the subdomain
   CYBERARK_SUBDOMAIN=mycompany
   
   # Incorrect: includes full domain
   CYBERARK_SUBDOMAIN=mycompany.privilegecloud.cyberark.cloud  # ❌
   ```

2. **Check TLD (.cloud vs .com):**
   ```bash
   # Correct TLD
   curl -I "https://mycompany.privilegecloud.cyberark.cloud"
   
   # Common mistake - .com instead of .cloud
   curl -I "https://mycompany.privilegecloud.cyberark.com"  # ❌
   ```

3. **Test connectivity:**
   ```bash
   # Test DNS resolution
   nslookup ${CYBERARK_SUBDOMAIN}.privilegecloud.cyberark.cloud
   
   # Test HTTPS connection
   curl -I "https://${CYBERARK_SUBDOMAIN}.privilegecloud.cyberark.cloud"
   ```

4. **Check firewall/proxy settings:**
   ```bash
   # Test direct connection
   telnet ${CYBERARK_SUBDOMAIN}.privilegecloud.cyberark.cloud 443
   ```

### 2. Rate Limiting (429 Too Many Requests)

**Symptoms:**
```
HTTP 429 Too Many Requests
Rate limit exceeded
```

**Solutions:**
1. **Reduce request frequency in client code**
2. **Implement backoff strategies:**
   ```python
   import time
   import random
   
   def exponential_backoff(attempt):
       return min(60, (2 ** attempt) + random.random())
   ```

3. **Monitor request patterns:**
   ```bash
   export CYBERARK_LOG_LEVEL=DEBUG
   python src/mcp_privilege_cloud/mcp_server.py
   ```

## MCP Inspector Problems

### 1. Inspector Can't Connect to Server

**Symptoms:**
- Connection timeout
- Connection refused
- Inspector shows "Failed to connect"

**Solutions:**
1. **Ensure server is running:**
   ```bash
   # Start server and leave running
   python run_server.py
   # Server should show log output and not exit
   ```

2. **Use correct command path:**
   ```bash
   # In MCP Inspector, use full absolute path
   python /mnt/c/Users/Tim/Projects/mcp-privilege-cloud/run_server.py
   ```

3. **Try different connection methods:**
   - Connection Method: "Command" (recommended)
   - Connection Method: "Local" (alternative)

4. **Restart both components:**
   ```bash
   # Stop server (Ctrl+C)
   # Restart server
   python run_server.py
   # Refresh MCP Inspector browser page
   ```

### 2. Tools Not Visible in Inspector

**Symptoms:** Inspector connects but shows no tools or fewer than expected tools

**Solutions:**
1. **Verify server startup:**
   ```bash
   # Should see successful startup messages
   INFO - Starting CyberArk Privilege Cloud MCP Server
   ```

2. **Check for import errors:**
   ```bash
   # Run server in debug mode
   export CYBERARK_LOG_LEVEL=DEBUG
   python run_server.py
   ```

3. **Test tool and resource loading:**
   ```bash
   python -c "
   from src.mcp_privilege_cloud.mcp_server import mcp, resource_registry
   print('MCP server loaded:', mcp.name)
   print('Available tools:', len(mcp._handlers.get('tools', {})))
   print('Available resource patterns:', len(resource_registry.get_registered_patterns()))
   "
   ```

### 3. Tool Execution Errors in Inspector

**Symptoms:** Tools appear but fail when executed

**Solutions:**
1. **Check authentication status:**
   ```json
   {
     "tool": "health_check",
     "arguments": {}
   }
   ```

2. **Verify parameter format:**
   ```json
   // Correct parameter format
   {
     "tool": "get_account_details",
     "arguments": {
       "account_id": "123_456"
     }
   }
   
   // Incorrect - missing required parameter
   {
     "tool": "get_account_details",
     "arguments": {}
   }
   ```

3. **Test resource access:**
   ```json
   {
     "uri": "cyberark://safes/",
     "description": "Test safes resource access"
   }
   ```

### 4. Resource Access Errors in Inspector

**Symptoms:** Resources appear but fail when accessed or return empty data

**Solutions:**
1. **Test resource access directly:**
   ```json
   {
     "resource": "cyberark://health/",
     "description": "Test health resource access"
   }
   ```

2. **Verify resource URI format:**
   ```json
   // Correct resource URIs
   {
     "resource": "cyberark://safes/",
     "description": "List all safes"
   }
   {
     "resource": "cyberark://accounts/search",
     "description": "Search accounts"
   }
   {
     "resource": "cyberark://platforms/WinServerLocal",
     "description": "Get specific platform"
   }
   ```

3. **Check resource with parameters:**
   ```json
   {
     "resource": "cyberark://safes/MySafe/accounts",
     "description": "Get accounts in specific safe"
   }
   ```

## Import and Startup Errors

### 1. ImportError: Attempted Relative Import

**Symptoms:**
```
ImportError: attempted relative import with no known parent package
```

**Solution:**
Use the dedicated entry point which handles import paths automatically:
```bash
python run_server.py  # ✅ Recommended
```

**Alternative Solutions:**
```bash
# Add project root to Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python src/mcp_privilege_cloud/mcp_server.py

# Or use module execution
python -m src.mcp_privilege_cloud.mcp_server
```

### 2. Module Not Found Errors

**Symptoms:**
```
ModuleNotFoundError: No module named 'mcp_privilege_cloud'
ModuleNotFoundError: No module named 'fastmcp'
```

**Solutions:**
1. **Verify virtual environment:**
   ```bash
   source venv/bin/activate
   pip list | grep -E "(mcp|fastmcp|fastapi)"
   ```

2. **Reinstall dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Check project structure:**
   ```bash
   ls -la src/mcp_privilege_cloud/
   # Should show: __init__.py, auth.py, server.py, mcp_server.py
   ```

## Platform Management Issues

### 1. Platform Management Returns 0 Platforms

**Symptoms:**
```
Found 0 platforms
Empty platform list returned
```

**Solutions:**
1. **Verify Administrator role membership:**
   - Service account must be member of "Privilege Cloud Administrator" role
   - Check role assignment in CyberArk Identity admin portal

2. **Test platforms resource access:**
   ```bash
   python -c "
   from src.mcp_privilege_cloud.mcp_server import _read_resource_content
   import asyncio
   import json
   content = asyncio.run(_read_resource_content('cyberark://platforms/'))
   data = json.loads(content)
   if 'error' in data:
       print(f'Error accessing platforms: {data[\"error\"]}')
   else:
       platforms = data.get('platforms', [])
       print(f'Found {len(platforms)} platforms')
       if platforms:
           print('First platform:', platforms[0].get('Name', 'Unknown'))
   "
   ```

3. **Debug platform API response:**
   ```bash
   python debug_platform_api.py  # If available
   ```

4. **Check API response structure:**
   - Platform API uses `Platforms` field (not `value` like other APIs)
   - Verify response parsing handles both field names

### 2. Platform Details Not Available

**Symptoms:**
- Platform list works but `get_platform_details` fails
- 404 errors for specific platform IDs

**Solutions:**
1. **Verify platform ID format:**
   ```bash
   # Correct platform ID examples
   WinServerLocal
   UnixSSH
   UnixSSHKey
   ```

2. **Access platforms resource first:**
   ```json
   {
     "uri": "cyberark://platforms/",
     "description": "Get available platforms"
   }
   ```

3. **Access specific platform resource:**
   ```json
   {
     "uri": "cyberark://platforms/WinServerLocal",
     "description": "Get specific platform details"
   }
   ```

## Resource Access Issues

### 1. Resource URI Parsing Errors

**Symptoms:**
```
Error: Invalid URI format
Resource not found for URI: cyberark://invalid-resource/
```

**Solutions:**
1. **Verify URI format:**
   ```bash
   # Correct URI patterns
   cyberark://health/
   cyberark://safes/
   cyberark://safes/MySafe/accounts
   cyberark://accounts/
   cyberark://accounts/search
   cyberark://accounts/123_456
   cyberark://platforms/
   cyberark://platforms/WinServerLocal
   cyberark://platforms/packages
   ```

2. **Test URI pattern matching:**
   ```bash
   python -c "
   from src.mcp_privilege_cloud.mcp_server import resource_registry
   patterns = resource_registry.get_registered_patterns()
   print('Available URI patterns:')
   for pattern in patterns:
       print(f'- {pattern}')
   "
   ```

3. **Validate specific URI:**
   ```bash
   python -c "
   from src.mcp_privilege_cloud.mcp_server import resource_registry
   uri = 'cyberark://safes/MySafe'
   resource = resource_registry.get_resource_class_for_uri(uri)
   print(f'URI {uri} -> Resource: {resource.__name__ if resource else \"Not Found\"}')
   "
   ```

### 2. Resource Access Permission Errors

**Symptoms:**
```
Error: 403 Forbidden when accessing resource
Resource returns empty data despite valid authentication
```

**Solutions:**
1. **Check resource-specific permissions:**
   ```bash
   # Test each resource type individually
   python -c "
   from src.mcp_privilege_cloud.mcp_server import _read_resource_content
   import asyncio
   import json
   
   resources = [
       'cyberark://health/',
       'cyberark://safes/',
       'cyberark://accounts/',
       'cyberark://platforms/'
   ]
   
   for uri in resources:
       try:
           content = asyncio.run(_read_resource_content(uri))
           data = json.loads(content)
           if 'error' in data:
               print(f'❌ {uri}: {data[\"error\"]}')
           else:
               print(f'✅ {uri}: Access successful')
       except Exception as e:
           print(f'❌ {uri}: {str(e)}')
   "
   ```

2. **Verify safe-specific access:**
   ```bash
   # Test specific safe access
   python -c "
   from src.mcp_privilege_cloud.mcp_server import _read_resource_content
   import asyncio
   import json
   
   safe_name = 'YourSafeName'  # Replace with actual safe name
   uri = f'cyberark://safes/{safe_name}'
   content = asyncio.run(_read_resource_content(uri))
   data = json.loads(content)
   print(json.dumps(data, indent=2))
   "
   ```

### 3. Resource Data Format Issues

**Symptoms:**
```
Resource returns data but in unexpected format
Missing expected fields in resource response
```

**Solutions:**
1. **Inspect raw resource content:**
   ```bash
   python -c "
   from src.mcp_privilege_cloud.mcp_server import _read_resource_content
   import asyncio
   import json
   
   uri = 'cyberark://safes/'
   content = asyncio.run(_read_resource_content(uri))
   print('Raw content:')
   print(content)
   print('\\nParsed JSON:')
   print(json.dumps(json.loads(content), indent=2))
   "
   ```

2. **Validate resource schema:**
   ```bash
   python -c "
   from src.mcp_privilege_cloud.mcp_server import _read_resource_content
   import asyncio
   import json
   
   uri = 'cyberark://accounts/'
   content = asyncio.run(_read_resource_content(uri))
   data = json.loads(content)
   
   # Check expected fields
   expected_fields = ['accounts', 'total_count', 'metadata']
   missing_fields = [f for f in expected_fields if f not in data]
   
   if missing_fields:
       print(f'Missing fields: {missing_fields}')
   else:
       print('All expected fields present')
   
   print(f'Available fields: {list(data.keys())}')
   "
   ```

### 4. Resource Performance Issues

**Symptoms:**
```
Resource requests timeout
Slow resource response times
```

**Solutions:**
1. **Test resource response times:**
   ```bash
   python -c "
   import time
   import asyncio
   import json
   from src.mcp_privilege_cloud.mcp_server import _read_resource_content
   
   uri = 'cyberark://safes/'
   start_time = time.time()
   content = asyncio.run(_read_resource_content(uri))
   end_time = time.time()
   
   data = json.loads(content)
   if 'error' not in data:
       print(f'Resource {uri} responded in {end_time - start_time:.2f} seconds')
       print(f'Data size: {len(content)} characters')
   else:
       print(f'Error: {data[\"error\"]}')
   "
   ```

2. **Use resource pagination:**
   ```bash
   python -c "
   from src.mcp_privilege_cloud.mcp_server import _read_resource_content
   import asyncio
   import json
   
   # Use search resource with filters for better performance
   uri = 'cyberark://accounts/search?keywords=admin&limit=10'
   content = asyncio.run(_read_resource_content(uri))
   data = json.loads(content)
   print(f'Limited search results: {len(data.get(\"accounts\", []))} accounts')
   "
   ```

## Debug Mode

### Enable Debug Logging
```bash
# Set debug level
export CYBERARK_LOG_LEVEL=DEBUG

# Run server with debug output
python run_server.py

# Run tests with debug
pytest -v -s
```

### Debug Configuration
```bash
# Show all environment variables
env | grep CYBERARK

# Test configuration loading
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('Loaded environment variables:')
for key in ['CYBERARK_IDENTITY_TENANT_ID', 'CYBERARK_CLIENT_ID', 'CYBERARK_SUBDOMAIN']:
    value = os.getenv(key)
    print(f'{key}: {value[:10] if value else None}...')
"
```

### Network Debug
```bash
# Test DNS resolution
nslookup ${CYBERARK_SUBDOMAIN}.privilegecloud.cyberark.cloud

# Test HTTPS connectivity
curl -v "https://${CYBERARK_SUBDOMAIN}.privilegecloud.cyberark.cloud/PasswordVault/api/Server"

# Test authentication endpoint
curl -v "https://${CYBERARK_IDENTITY_TENANT_ID}.id.cyberark.cloud/oauth2/platformtoken"
```

## Health Check Procedures

### Basic Health Check
```bash
python -c "
import asyncio
from src.mcp_privilege_cloud.server import CyberArkMCPServer
server = CyberArkMCPServer.from_environment()
health = asyncio.run(server.health_check())
print('Health Status:', health['status'])
if health['status'] == 'healthy':
    print('✅ System operational')
    print(f'Safes accessible: {health.get('safes_accessible', 'Unknown')}')
else:
    print('❌ System issues detected')
    print(f'Error: {health.get('error', 'Unknown error')}')
"
```

### Component Health Checks

#### Authentication Test
```bash
python -c "
from src.mcp_privilege_cloud.auth import CyberArkAuthenticator
import asyncio
try:
    auth = CyberArkAuthenticator.from_environment()
    header = asyncio.run(auth.get_auth_header())
    print('✅ Authentication successful')
except Exception as e:
    print('❌ Authentication failed:', str(e))
"
```

#### Server Connection Test
```bash
python -c "
from src.mcp_privilege_cloud.mcp_server import _read_resource_content
import asyncio
import json
try:
    content = asyncio.run(_read_resource_content('cyberark://safes/'))
    data = json.loads(content)
    if 'error' in data:
        print(f'❌ Server connection failed: {data[\"error\"]}')
    else:
        safes = data.get('safes', [])
        print(f'✅ Server connection successful - {len(safes)} safes accessible')
except Exception as e:
    print('❌ Server connection failed:', str(e))
"
```

#### MCP Integration Test
```bash
python -c "
try:
    from src.mcp_privilege_cloud.mcp_server import mcp
    print('✅ MCP integration loaded successfully')
    print(f'Server name: {mcp.name}')
except Exception as e:
    print('❌ MCP integration failed:', str(e))
"
```

## Advanced Debugging

### Python Debugger
```bash
# Run with Python debugger
python -m pdb src/mcp_privilege_cloud/mcp_server.py

# Set breakpoint in code and run
python -c "
import pdb; pdb.set_trace()
from src.mcp_privilege_cloud.server import CyberArkMCPServer
server = CyberArkMCPServer.from_environment()
"
```

### Memory and Performance Debugging
```bash
# Install profiling tools
pip install memory-profiler line-profiler

# Profile memory usage
python -m memory_profiler src/mcp_privilege_cloud/server.py

# Profile execution time
kernprof -l -v src/mcp_privilege_cloud/server.py
```

### Network Traffic Analysis
```bash
# Monitor HTTP requests (if available)
mitmproxy -p 8080

# Set proxy for testing
export HTTP_PROXY=http://localhost:8080
export HTTPS_PROXY=http://localhost:8080
python run_server.py
```

## Error Code Reference

### HTTP Status Codes
- **401 Unauthorized**: Invalid or expired token → Check authentication
- **403 Forbidden**: Insufficient permissions → Verify service account roles
- **404 Not Found**: Resource not found → Check safe names, account IDs
- **429 Too Many Requests**: Rate limit exceeded → Implement backoff
- **500 Internal Server Error**: CyberArk API error → Check CyberArk status

### Application Error Patterns
- **"Missing required environment variables"**: Configuration issue
- **"Authentication failed"**: Credential or OAuth setup problem
- **"Network error"**: DNS, connectivity, or firewall issue
- **"Platform management returns 0"**: Administrator role missing
- **"ImportError"**: Python path or dependency issue
- **"Resource not found for URI"**: Invalid resource URI format
- **"No resource handler found"**: URI pattern not registered
- **"Resource returns empty data"**: Permission or filtering issue

## Getting Support

### Information to Collect
When seeking support, gather this information:

1. **Environment Details:**
   ```bash
   python --version
   pip list | grep mcp
   uname -a  # Linux/Mac
   ver       # Windows
   ```

2. **Error Messages:**
   - Copy complete error output
   - Include stack traces
   - Note reproduction steps

3. **Configuration (sanitized):**
   ```bash
   # Don't share actual secrets, just structure
   echo "CYBERARK_IDENTITY_TENANT_ID: ${CYBERARK_IDENTITY_TENANT_ID:+SET}"
   echo "CYBERARK_CLIENT_ID: ${CYBERARK_CLIENT_ID:+SET}"
   echo "CYBERARK_CLIENT_SECRET: ${CYBERARK_CLIENT_SECRET:+SET}"
   echo "CYBERARK_SUBDOMAIN: ${CYBERARK_SUBDOMAIN:+SET}"
   ```

4. **Health Check Output:**
   ```bash
   python -c "
   import asyncio
   from src.mcp_privilege_cloud.server import CyberArkMCPServer
   server = CyberArkMCPServer.from_environment()
   health = asyncio.run(server.health_check())
   print('Health:', health)
   "
   ```

### Troubleshooting Checklist

Before seeking support, verify:
- [ ] Environment variables are set correctly
- [ ] Virtual environment is activated
- [ ] Dependencies are installed
- [ ] CyberArk service account has proper permissions
- [ ] Network connectivity to CyberArk cloud is working
- [ ] Using correct TLD (.cloud, not .com)
- [ ] Heath check passes
- [ ] MCP Inspector can connect to server
- [ ] Resource URIs follow correct format (cyberark://resource/)
- [ ] Resource access returns expected data structures

---

This troubleshooting guide covers the most common issues encountered with the CyberArk Privilege Cloud MCP Server. For additional support, ensure you've followed the troubleshooting checklist and collected the necessary diagnostic information.