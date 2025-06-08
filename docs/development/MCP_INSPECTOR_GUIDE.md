# MCP Inspector Testing Guide
Complete step-by-step guide for testing the CyberArk Privilege Cloud MCP Server with MCP Inspector.

## 🚀 Quick Start Testing (No CyberArk Credentials Required)

### Step 1: Install MCP Inspector
```bash
# Install globally
npm install -g @modelcontextprotocol/inspector

# Or run directly with npx
npx @modelcontextprotocol/inspector
```

### Step 2: Start the MCP Server
```bash
# Navigate to project directory
cd /mnt/c/Users/Tim/Projects/mcp-privilege-cloud

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Start the server (it will show validation errors for missing env vars but still work)
python src/cyberark_mcp/mcp_server.py
```

**Expected Output:**
```
ERROR - Missing required environment variables: ['CYBERARK_IDENTITY_TENANT_ID', 'CYBERARK_CLIENT_ID', 'CYBERARK_CLIENT_SECRET', 'CYBERARK_SUBDOMAIN']
```
This is expected for testing - the server will still start and you can test the tool structure.

### Step 3: Open MCP Inspector
1. Open your browser and go to the MCP Inspector interface
2. You'll see a connection interface

### Step 4: Connect to Your Server
1. **Connection Method**: Choose "Local" or "Command"
2. **Command**: If using command mode, enter:
   ```bash
   python /mnt/c/Users/Tim/Projects/mcp-privilege-cloud/src/cyberark_mcp/mcp_server.py
   ```
3. **Click Connect**

### Step 5: Explore Available Tools
Once connected, you should see these tools in the Inspector:

#### Available Tools:
- `health_check`
- `list_accounts` 
- `get_account_details`
- `search_accounts`
- `list_safes`
- `get_safe_details`

## 🧪 Testing Without Real Credentials

You can test the tool structure and validation even without CyberArk credentials:

### Test 1: Tool Discovery
In MCP Inspector, you should see all 6 tools listed. Click on each to see their parameters:

#### `health_check`
- **Parameters**: None
- **Purpose**: Check CyberArk connectivity

#### `list_accounts`
- **Parameters**: 
  - `safe_name` (optional): Filter by safe name
  - `username` (optional): Filter by username
  - `address` (optional): Filter by address
- **Purpose**: List CyberArk accounts

#### `get_account_details`
- **Parameters**:
  - `account_id` (required): Account identifier
- **Purpose**: Get detailed account info

#### `search_accounts`
- **Parameters**:
  - `keywords` (optional): Search terms
  - `safe_name` (optional): Safe filter
  - `username` (optional): Username filter  
  - `address` (optional): Address filter
  - `platform_id` (optional): Platform filter
- **Purpose**: Advanced account search

#### `list_safes`
- **Parameters**:
  - `search` (optional): Search term for safe names
- **Purpose**: List accessible safes

#### `get_safe_details`
- **Parameters**:
  - `safe_name` (required): Name of the safe
- **Purpose**: Get detailed safe information

### Test 2: Parameter Validation
Try calling tools with invalid parameters to test validation:

1. **Call `get_account_details` without `account_id`**:
   - Should show parameter validation error
   
2. **Call `get_safe_details` without `safe_name`**:
   - Should show parameter validation error

## 🔐 Testing With Real CyberArk Credentials

### Step 1: Configure Environment
Create a `.env` file in the project root:

```bash
# Copy the example file
cp .env.example .env

# Edit with your actual values
nano .env
```

**Required Configuration:**
```bash
# CyberArk Identity tenant (without .id.cyberark.cloud)
CYBERARK_IDENTITY_TENANT_ID=your-tenant-id

# Service account credentials
CYBERARK_CLIENT_ID=your-service-account-username
CYBERARK_CLIENT_SECRET=your-service-account-password

# Privilege Cloud subdomain (without .privilegecloud.cyberark.com)
CYBERARK_SUBDOMAIN=your-privilege-cloud-subdomain

# Optional settings
CYBERARK_API_TIMEOUT=30
CYBERARK_MAX_RETRIES=3
CYBERARK_LOG_LEVEL=INFO
```

### Step 2: Verify Configuration
Test your configuration before using MCP Inspector:

```bash
# Health check test
python -c "
import asyncio
from src.cyberark_mcp.server import CyberArkMCPServer
server = CyberArkMCPServer.from_environment()
health = asyncio.run(server.health_check())
print('Health Status:', health['status'])
if health['status'] == 'healthy':
    print('✅ Ready for MCP Inspector testing!')
    print(f'Safes accessible: {health.get(\"safes_accessible\", \"Unknown\")}')
else:
    print('❌ Configuration issue:', health.get('error', 'Unknown error'))
"
```

### Step 3: Restart MCP Server
```bash
# Stop the current server (Ctrl+C)
# Restart with proper environment
source venv/bin/activate
python src/cyberark_mcp/mcp_server.py
```

**Expected Output:**
```
INFO - Starting CyberArk Privilege Cloud MCP Server
INFO - CyberArk server connection established successfully
```

### Step 4: Test Tools with Real Data

#### Test Sequence 1: Health Check
```json
{
  "tool": "health_check",
  "arguments": {}
}
```

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-06-08T...",
  "safes_accessible": 5
}
```

#### Test Sequence 2: List Safes
```json
{
  "tool": "list_safes",
  "arguments": {}
}
```

**Expected Response:**
```json
[
  {
    "safeName": "Safe1",
    "description": "Description...",
    "location": "\\",
    ...
  }
]
```

#### Test Sequence 3: List Accounts
```json
{
  "tool": "list_accounts",
  "arguments": {
    "safe_name": "YourSafeName"
  }
}
```

#### Test Sequence 4: Search Accounts
```json
{
  "tool": "search_accounts",
  "arguments": {
    "keywords": "admin"
  }
}
```

#### Test Sequence 5: Get Account Details
Use an account ID from the previous results:
```json
{
  "tool": "get_account_details",
  "arguments": {
    "account_id": "123_456"
  }
}
```

## 🔍 Troubleshooting Inspector Issues

### Common Connection Issues

#### 1. Server Won't Start
**Symptoms**: Server exits immediately
**Solution**: Check environment variables
```bash
python test_mvp.py  # Run MVP test first
```

#### 2. Inspector Can't Connect
**Symptoms**: Connection timeout or refused
**Solutions**:
- Ensure server is running in terminal
- Check the command path is correct
- Try restarting both server and inspector

#### 3. Authentication Errors
**Symptoms**: 401 Unauthorized in tool responses
**Solutions**:
- Verify service account credentials
- Check OAuth is enabled for service account
- Confirm tenant ID format (no .id.cyberark.cloud suffix)

#### 4. Permission Errors
**Symptoms**: 403 Forbidden in tool responses
**Solutions**:
- Verify service account permissions in CyberArk
- Check safe-level permissions
- Ensure account has "List Accounts" permission

### Debug Mode
Enable debug logging for detailed troubleshooting:

```bash
export CYBERARK_LOG_LEVEL=DEBUG
python src/cyberark_mcp/mcp_server.py
```

## 📊 Expected Test Results

### Successful Connection
- ✅ 6 tools appear in Inspector interface
- ✅ Tool parameters are correctly displayed
- ✅ Tools can be called without errors

### Successful API Integration
- ✅ `health_check` returns "healthy" status
- ✅ `list_safes` returns array of safe objects
- ✅ `list_accounts` returns account data
- ✅ Error messages are helpful and descriptive

### Error Handling
- ✅ Invalid parameters show validation errors
- ✅ Network issues show appropriate error messages
- ✅ Authentication failures are clearly reported

## 🎯 Next Steps After Testing

1. **Integration**: Connect to your preferred MCP client
2. **Automation**: Use the tools in automated workflows
3. **Monitoring**: Set up logging and monitoring for production use
4. **Enhancement**: Add additional features as needed

## 🆘 Support

If you encounter issues:
1. Run `python test_mvp.py` to verify basic functionality
2. Check the server logs for detailed error messages
3. Verify your CyberArk service account permissions
4. Test connectivity with the health check tool first