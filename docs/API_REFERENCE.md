# API Reference

Comprehensive API reference for the CyberArk Privilege Cloud MCP Server. This guide provides complete specifications, parameters, examples, and integration details for all available MCP tools.

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Tool Categories](#tool-categories)
- [Account Management Tools](#account-management-tools)
- [Safe Management Tools](#safe-management-tools)
- [Platform Management Tools](#platform-management-tools)
- [Health Monitoring Tools](#health-monitoring-tools)
- [Error Handling](#error-handling)
- [Usage Examples](#usage-examples)
- [Integration Patterns](#integration-patterns)

## Overview

The CyberArk Privilege Cloud MCP Server provides **6 specialized tools** for privileged account management through the Model Context Protocol (MCP). All tools follow consistent patterns for authentication, parameter validation, and error handling.

### Core Capabilities
- **Account Management**: Create and retrieve detailed account information
- **Resource Discovery**: Access accounts, safes, and platforms through MCP resources
- **Password Operations**: Advanced password management capabilities
- **Health Monitoring**: Verify connectivity and system status

### API Integration Details
- **Base URL**: `https://{subdomain}.privilegecloud.cyberark.cloud/PasswordVault/api`
- **Authentication**: OAuth 2.0 with automatic token refresh
- **API Version**: Gen2 endpoints (preferred over Gen1 legacy endpoints)
- **Response Format**: JSON with standardized error handling

## Authentication

### OAuth 2.0 Configuration
All tools require proper authentication configuration through environment variables:

```bash
# Required Environment Variables
CYBERARK_IDENTITY_TENANT_ID=your-tenant-id    # Without .id.cyberark.cloud suffix
CYBERARK_CLIENT_ID=service-account-username    # OAuth service account
CYBERARK_CLIENT_SECRET=service-account-password
CYBERARK_SUBDOMAIN=your-subdomain             # Without .privilegecloud.cyberark.cloud suffix

# Optional Configuration
CYBERARK_API_TIMEOUT=30        # API request timeout in seconds
CYBERARK_MAX_RETRIES=3         # Maximum retry attempts  
CYBERARK_LOG_LEVEL=INFO        # Logging level
```

### Token Management
- **Expiration**: 15 minutes with automatic refresh
- **Caching**: Secure in-memory token caching
- **Concurrency**: Thread-safe token refresh with double-checked locking
- **Error Recovery**: Automatic retry on 401 authentication errors

## Tool Categories

### Primary Tools (MVP)
1. **Account Management**: `create_account`, `get_account_details`
2. **Password Operations**: `change_account_password`, `set_next_password`, `verify_account_password`, `reconcile_account_password`
3. **Platform Management**: `import_platform_package`
4. **Health Monitoring**: `health_check`

### MCP Resources (Discovery)
1. **Accounts**: `cyberark://accounts` - List and search accounts
2. **Safes**: `cyberark://safes` - List and filter safes
3. **Platforms**: `cyberark://platforms` - List available platforms

### Future Enhancement Categories
1. **Account Lifecycle**: Update and delete operations
2. **Session Management**: Active session monitoring
3. **Reporting**: Access reports and analytics
4. **Advanced Safe Management**: Create and update operations

## Account Management Tools

### Account Discovery via MCP Resources

**Description**: List and search accounts through MCP resource URIs instead of dedicated tools.

**Base URI**: `cyberark://accounts`

**Supported Query Parameters**:
- `safe_name`: Filter accounts by safe name
- `username`: Filter accounts by username  
- `address`: Filter accounts by address/hostname
- `keywords`: Search keywords
- `platform_id`: Filter by platform ID

**Example Resource URIs**:
```
# List all accessible accounts
cyberark://accounts

# Filter by safe name
cyberark://accounts?safe_name=IT-Infrastructure

# Multiple filters
cyberark://accounts?safe_name=Database-Safes&username=admin

# Search with keywords
cyberark://accounts?keywords=database&platform_id=MySQLDB

# Search by address pattern
cyberark://accounts?address=*.company.com
```

**Resource Response Example**:
```json
{
  "uri": "cyberark://accounts?safe_name=Database-Safes",
  "name": "Accounts in Database-Safes",
  "description": "Filtered list of accounts",
  "mimeType": "application/json",
  "text": "[{\"id\": \"123_456\", \"name\": \"DatabaseAdmin\", \"address\": \"db.company.com\", \"userName\": \"dbadmin\", \"platformId\": \"MySQLDB\", \"safeName\": \"Database-Safes\", \"secretType\": \"password\", \"createdTime\": 1640995200}]"
}
```

---

### `get_account_details`

**Description**: Get detailed information about a specific account.

**API Endpoint**: `GET /PasswordVault/API/Accounts/{accountId}`

**Parameters**:
- `account_id` (required, string): Unique identifier for the account

**Returns**: Complete account object with all properties

**Example Usage**:
```python
# Get detailed account information
await client.call_tool("get_account_details", {
    "account_id": "123_456"
})
```

**Response Example**:
```json
{
  "id": "123_456",
  "name": "DatabaseAdmin",
  "address": "db.company.com",
  "userName": "dbadmin",
  "platformId": "MySQLDB",
  "safeName": "Database-Safes",
  "secretType": "password",
  "platformAccountProperties": {
    "Port": "3306",
    "Database": "production"
  },
  "secretManagement": {
    "automaticManagementEnabled": true,
    "lastModifiedTime": 1640995200
  },
  "createdTime": 1640995200,
  "modifiedTime": 1640995300
}
```


### `create_account`

**Description**: Create a new privileged account in CyberArk Privilege Cloud.

**API Endpoint**: `POST /PasswordVault/API/Accounts`

**Parameters**:
- `platform_id` (required, string): Platform ID (e.g., WinServerLocal, UnixSSH)
- `safe_name` (required, string): Safe where account will be created
- `name` (optional, string): Account name/identifier
- `address` (optional, string): Target address/hostname
- `user_name` (optional, string): Username for the account
- `secret` (optional, string): Password or SSH key
- `secret_type` (optional, string): Type of secret ('password' or 'key')
- `platform_account_properties` (optional, object): Platform-specific properties
- `secret_management` (optional, object): Secret management configuration
- `remote_machines_access` (optional, object): Remote access configuration

**Returns**: Created account object with ID and metadata

**Example Usage**:
```python
# Basic account creation
await client.call_tool("create_account", {
    "platform_id": "WinServerLocal",
    "safe_name": "IT-Infrastructure",
    "name": "ServerAdmin",
    "address": "server.domain.com",
    "user_name": "admin"
})

# Advanced account creation with properties
await client.call_tool("create_account", {
    "platform_id": "WinServerLocal", 
    "safe_name": "IT-Infrastructure",
    "name": "DatabaseServer",
    "address": "db.company.com",
    "user_name": "dbadmin",
    "secret": "SecurePassword123!",
    "secret_type": "password",
    "platform_account_properties": {
        "LogonDomain": "CORP",
        "Port": "3389"
    },
    "secret_management": {
        "automaticManagementEnabled": true,
        "manualManagementReason": ""
    }
})

# SSH key account creation
await client.call_tool("create_account", {
    "platform_id": "UnixSSHKey",
    "safe_name": "Unix-Servers",
    "name": "LinuxAdmin",
    "address": "linux.company.com",
    "user_name": "root",
    "secret": "-----BEGIN PRIVATE KEY-----\n...",
    "secret_type": "key"
})
```

**Response Example**:
```json
{
  "id": "789_012",
  "name": "ServerAdmin",
  "address": "server.domain.com",
  "userName": "admin",
  "platformId": "WinServerLocal",
  "safeName": "IT-Infrastructure",
  "secretType": "password",
  "createdTime": 1640995400,
  "status": "created"
}
```

## Safe Management Tools

### Safe Discovery via MCP Resources

**Description**: List and filter safes through MCP resource URIs instead of dedicated tools.

**Base URI**: `cyberark://safes`

**Supported Query Parameters**:
- `search`: Search term for safe names
- `offset`: Pagination offset (default: 0)
- `limit`: Number of safes to return (default: 25, max: 1000)
- `sort`: Sort order - "safeName asc" or "safeName desc"
- `include_accounts`: Include account lists with each safe
- `extended_details`: Include extended safe information

**Example Resource URIs**:
```
# List all accessible safes
cyberark://safes

# Search safes by name
cyberark://safes?search=Database

# Paginated results with sorting
cyberark://safes?offset=0&limit=10&sort=safeName+asc

# Include accounts in each safe
cyberark://safes?include_accounts=true&extended_details=true
```

**Resource Response Example**:
```json
{
  "uri": "cyberark://safes?search=Database",
  "name": "Safes matching 'Database'",
  "description": "Filtered list of safes",
  "mimeType": "application/json",
  "text": "[{\"safeName\": \"Database-Safes\", \"description\": \"Database server accounts\", \"location\": \"\\\\\", \"creator\": \"Admin\", \"olacEnabled\": false, \"managingCPM\": \"PasswordManager\", \"numberOfVersionsRetention\": 5, \"numberOfDaysRetention\": 7, \"autoPurgeEnabled\": false, \"creationTime\": 1640995200, \"modificationTime\": 1640995300}]"
}
```

---

### `get_safe_details`

**Description**: Get detailed information about a specific safe with optional account inclusion and caching.

**API Endpoint**: `GET /PasswordVault/API/Safes/{safeName}`

**Parameters**:
- `safe_name` (required, string): Name of the safe
- `include_accounts` (optional, boolean): Include account lists with the safe
- `use_cache` (optional, boolean): Use session-based caching for performance

**Returns**: Safe object with properties and optional account list

**Example Usage**:
```python
# Basic safe details
await client.call_tool("get_safe_details", {
    "safe_name": "IT-Infrastructure"
})

# Include accounts in the safe
await client.call_tool("get_safe_details", {
    "safe_name": "Database-Safes",
    "include_accounts": True
})

# With caching for performance
await client.call_tool("get_safe_details", {
    "safe_name": "IT-Infrastructure",
    "use_cache": True,
    "include_accounts": True
})
```

**Response Example**:
```json
{
  "safeName": "IT-Infrastructure",
  "description": "IT infrastructure accounts",
  "location": "\\",
  "creator": "Admin",
  "olacEnabled": false,
  "managingCPM": "PasswordManager",
  "numberOfVersionsRetention": 5,
  "numberOfDaysRetention": 7,
  "autoPurgeEnabled": false,
  "creationTime": 1640995200,
  "modificationTime": 1640995300,
  "accounts": [
    {
      "id": "123_456",
      "name": "ServerAdmin",
      "userName": "admin",
      "address": "server.domain.com"
    }
  ]
}
```

## Platform Management Tools

### Platform Discovery via MCP Resources

**Description**: List and filter platforms through MCP resource URIs instead of dedicated tools.

**Base URI**: `cyberark://platforms`

**Required Permissions**: Service account must be a member of the Privilege Cloud Administrator role

**Supported Query Parameters**:
- `search`: Search term for platform names
- `active`: Filter by active status (true/false)
- `system_type`: Filter by system type (e.g., Windows, Unix)

**Example Resource URIs**:
```
# List all platforms
cyberark://platforms

# Filter by active platforms
cyberark://platforms?active=true

# Search and filter
cyberark://platforms?search=Windows&active=true&system_type=Windows
```

**Resource Response Example**:
```json
{
  "uri": "cyberark://platforms?active=true",
  "name": "Active Platforms",
  "description": "List of active platforms",
  "mimeType": "application/json",
  "text": "[{\"ID\": \"WinServerLocal\", \"Name\": \"Windows Server Local\", \"SystemType\": \"Windows\", \"Active\": true, \"Description\": \"Windows Server Local Account\", \"PlatformBaseID\": \"WinServer\", \"PlatformType\": \"Regular\"}, {\"ID\": \"UnixSSH\", \"Name\": \"Unix SSH\", \"SystemType\": \"Unix\", \"Active\": true, \"Description\": \"Unix account via SSH\", \"PlatformBaseID\": \"Unix\", \"PlatformType\": \"Regular\"}]"
}
```

### `import_platform_package`

**Description**: Import a platform package into CyberArk Privilege Cloud.

**API Endpoint**: `POST /PasswordVault/API/Platforms/Import`

**Required Permissions**: Service account must be a member of the Privilege Cloud Administrator role

**Parameters**:
- `platform_package_file` (required, string): Base64-encoded platform package file content

**Returns**: Import result with platform ID and status

**Example Usage**:
```python
# Import platform package
await client.call_tool("import_platform_package", {
    "platform_package_file": "UEsDBBQAAAAIAOt..." # Base64 encoded zip file
})
```

**Response Example**:
```json
{
  "PlatformID": "CustomPlatform-001",
  "Status": "Success",
  "Message": "Platform imported successfully"
}
```

---

### Platform Details via MCP Resources

**Description**: Get detailed information about specific platforms through resource URIs.

**Base URI**: `cyberark://platforms/{platformId}`

**Required Permissions**: Service account must be a member of the Privilege Cloud Administrator role

**Example Resource URIs**:
```
# Get Windows Server platform details
cyberark://platforms/WinServerLocal

# Get Unix SSH platform details
cyberark://platforms/UnixSSH
```

**Resource Response Example**:
```json
{
  "uri": "cyberark://platforms/WinServerLocal",
  "name": "Windows Server Local Platform",
  "description": "Detailed platform configuration",
  "mimeType": "application/json",
  "text": "{\"ID\": \"WinServerLocal\", \"Name\": \"Windows Server Local\", \"SystemType\": \"Windows\", \"Active\": true, \"Description\": \"Windows Server Local Account\", \"PlatformBaseID\": \"WinServer\", \"PlatformType\": \"Regular\", \"Properties\": {\"required\": [\"Address\", \"UserName\"], \"optional\": [\"Port\", \"LogonDomain\"]}, \"CredentialsManagementPolicy\": {\"Verification\": {\"RequirePasswordVerificationEveryXDays\": 1, \"AutomaticPasswordVerificationEnabled\": true}, \"Change\": {\"RequirePasswordChangeEveryXDays\": 90, \"AutomaticPasswordChangeEnabled\": true}}}"
}
```

## Password Management Tools

### `change_account_password`

**Description**: Change the password for a specific account.

**API Endpoint**: `POST /PasswordVault/API/Accounts/{accountId}/Change`

**Parameters**:
- `account_id` (required, string): Unique identifier for the account
- `new_password` (optional, string): New password (if not provided, system will generate one)

**Returns**: Password change operation result

**Example Usage**:
```python
# Change password with specified value
await client.call_tool("change_account_password", {
    "account_id": "123_456",
    "new_password": "NewSecurePassword123!"
})

# Change password with system-generated value
await client.call_tool("change_account_password", {
    "account_id": "123_456"
})
```

**Response Example**:
```json
{
  "status": "success",
  "message": "Password changed successfully"
}
```

---

### `set_next_password`

**Description**: Set the next password for an account (password will be applied on next change).

**API Endpoint**: `POST /PasswordVault/API/Accounts/{accountId}/SetNextPassword`

**Parameters**:
- `account_id` (required, string): Unique identifier for the account
- `password` (required, string): The next password to set

**Returns**: Set next password operation result

**Example Usage**:
```python
# Set next password
await client.call_tool("set_next_password", {
    "account_id": "123_456",
    "password": "FuturePassword123!"
})
```

**Response Example**:
```json
{
  "status": "success",
  "message": "Next password set successfully"
}
```

---

### `verify_account_password`

**Description**: Verify that the current password for an account is correct.

**API Endpoint**: `POST /PasswordVault/API/Accounts/{accountId}/Verify`

**Parameters**:
- `account_id` (required, string): Unique identifier for the account

**Returns**: Password verification result

**Example Usage**:
```python
# Verify account password
await client.call_tool("verify_account_password", {
    "account_id": "123_456"
})
```

**Response Example**:
```json
{
  "status": "success",
  "verified": true,
  "message": "Password verification completed"
}
```

---

### `reconcile_account_password`

**Description**: Reconcile the account password with the target system.

**API Endpoint**: `POST /PasswordVault/API/Accounts/{accountId}/Reconcile`

**Parameters**:
- `account_id` (required, string): Unique identifier for the account

**Returns**: Password reconciliation operation result

**Example Usage**:
```python
# Reconcile account password
await client.call_tool("reconcile_account_password", {
    "account_id": "123_456"
})
```

**Response Example**:
```json
{
  "status": "success",
  "message": "Password reconciliation completed"
}
```

## Health Monitoring Tools

### `health_check`

**Description**: Perform a comprehensive health check of the CyberArk connection and system status.

**API Endpoint**: Multiple endpoints for comprehensive validation

**Parameters**: None

**Returns**: Health status object with system information

**Example Usage**:
```python
# Perform health check
await client.call_tool("health_check", {})
```

**Response Examples**:

**Healthy System**:
```json
{
  "status": "healthy",
  "timestamp": "2025-06-28T10:30:00Z",
  "safes_accessible": 12,
  "authentication": "valid",
  "api_connectivity": "operational"
}
```

**System Issues**:
```json
{
  "status": "unhealthy",
  "timestamp": "2025-06-28T10:30:00Z",
  "error": "Authentication failed: Invalid credentials",
  "authentication": "failed",
  "api_connectivity": "unreachable"
}
```

## Error Handling

### Standard Error Responses

All tools follow consistent error handling patterns:

#### Authentication Errors (401)
```json
{
  "error": "Authentication failed",
  "details": "Token expired or invalid credentials",
  "troubleshooting": "Verify service account credentials and OAuth configuration"
}
```

#### Permission Errors (403)  
```json
{
  "error": "Insufficient permissions",
  "details": "Service account lacks required permissions",
  "troubleshooting": "Verify service account has appropriate safe permissions"
}
```

#### Resource Not Found (404)
```json
{
  "error": "Resource not found", 
  "details": "Account ID '123_456' not found",
  "troubleshooting": "Verify the resource identifier is correct"
}
```

#### Rate Limiting (429)
```json
{
  "error": "Rate limit exceeded",
  "details": "Too many requests in short timeframe",
  "troubleshooting": "Implement request throttling and retry with exponential backoff"
}
```

#### Validation Errors
```json
{
  "error": "Parameter validation failed",
  "details": "Required parameter 'account_id' is missing",
  "troubleshooting": "Review tool documentation for required parameters"
}
```

### Error Recovery Mechanisms

1. **Automatic Token Refresh**: 401 errors trigger automatic token refresh and retry
2. **Retry Logic**: Transient network errors are retried with exponential backoff
3. **Detailed Logging**: All errors are logged with comprehensive context
4. **User-Friendly Messages**: Error responses include troubleshooting guidance

## Usage Examples

### Account Lifecycle Management

```python
# 1. Search for existing accounts via MCP resources
existing_accounts_resource = await client.read_resource("cyberark://accounts?keywords=webserver&safe_name=Web-Servers")
existing_accounts = json.loads(existing_accounts_resource.text)

# 2. Create new account if not found
if not existing_accounts:
    new_account = await client.call_tool("create_account", {
        "platform_id": "WinServerLocal",
        "safe_name": "Web-Servers", 
        "name": "WebServer01",
        "address": "web01.company.com",
        "user_name": "iisadmin",
        "platform_account_properties": {
            "LogonDomain": "CORP",
            "Port": "3389"
        }
    })
    account_id = new_account["id"]
else:
    account_id = existing_accounts[0]["id"]

# 3. Get detailed account information
account_details = await client.call_tool("get_account_details", {
    "account_id": account_id
})

# 4. Manage account password
await client.call_tool("change_account_password", {
    "account_id": account_id,
    "new_password": "NewSecurePassword123!"
})
```

### Safe Discovery and Analysis

```python
# 1. List all accessible safes via MCP resources
all_safes_resource = await client.read_resource("cyberark://safes?sort=safeName+asc")
all_safes = json.loads(all_safes_resource.text)

# 2. Filter for database-related safes
db_safes = [safe for safe in all_safes 
           if "database" in safe["safeName"].lower()]

# 3. Get detailed information for each database safe
for safe in db_safes:
    safe_details = await client.call_tool("get_safe_details", {
        "safe_name": safe["safeName"],
        "include_accounts": True
    })
    
    print(f"Safe: {safe_details['safeName']}")
    print(f"Accounts: {len(safe_details.get('accounts', []))}")
```

### Platform Configuration Review

```python
# 1. List all active platforms via MCP resources
platforms_resource = await client.read_resource("cyberark://platforms?active=true")
platforms = json.loads(platforms_resource.text)

# 2. Get detailed configuration for each platform
platform_configs = {}
for platform in platforms:
    details_resource = await client.read_resource(f"cyberark://platforms/{platform['ID']}")
    details = json.loads(details_resource.text)
    platform_configs[platform["ID"]] = details

# 3. Analyze password policies
for platform_id, config in platform_configs.items():
    policy = config.get("CredentialsManagementPolicy", {})
    change_policy = policy.get("Change", {})
    print(f"{platform_id}: Password change every {change_policy.get('RequirePasswordChangeEveryXDays', 'N/A')} days")
```

## Integration Patterns

### MCP Client Integration

#### Claude Desktop Configuration
```json
{
  "mcpServers": {
    "cyberark-privilege-cloud": {
      "command": "uvx",
      "args": ["mcp-privilege-cloud"],
      "env": {
        "CYBERARK_IDENTITY_TENANT_ID": "your-tenant-id",
        "CYBERARK_CLIENT_ID": "your-client-id",
        "CYBERARK_CLIENT_SECRET": "your-client-secret",
        "CYBERARK_SUBDOMAIN": "your-subdomain"
      }
    }
  }
}
```

#### MCP Inspector Testing
```bash
# Connect MCP Inspector with uvx
npx @modelcontextprotocol/inspector
# Command: uvx mcp-privilege-cloud

# Alternative with uv run for development
npx @modelcontextprotocol/inspector  
# Command: uv run mcp-privilege-cloud
```

### Batch Operations

```python
# Process multiple accounts efficiently
async def process_accounts_in_safe(safe_name):
    # Get safe details with accounts
    safe_details = await client.call_tool("get_safe_details", {
        "safe_name": safe_name,
        "include_accounts": True
    })
    
    # Process each account
    results = []
    for account in safe_details.get("accounts", []):
        account_details = await client.call_tool("get_account_details", {
            "account_id": account["id"]
        })
        results.append(account_details)
    
    return results

# Alternative approach using MCP resources for account discovery
async def discover_and_process_accounts(safe_name):
    # Discover accounts via MCP resources
    accounts_resource = await client.read_resource(f"cyberark://accounts?safe_name={safe_name}")
    accounts = json.loads(accounts_resource.text)
    
    # Process each account
    results = []
    for account in accounts:
        account_details = await client.call_tool("get_account_details", {
            "account_id": account["id"]
        })
        results.append(account_details)
    
    return results
```

### Error Handling Patterns

```python
async def robust_account_creation(account_data):
    try:
        # Attempt account creation
        result = await client.call_tool("create_account", account_data)
        return {"success": True, "account": result}
        
    except Exception as e:
        if "already exists" in str(e):
            # Search for existing account via MCP resources
            search_uri = f"cyberark://accounts?username={account_data['user_name']}&address={account_data['address']}"
            existing_resource = await client.read_resource(search_uri)
            existing = json.loads(existing_resource.text)
            return {"success": False, "reason": "exists", "existing": existing}
        else:
            return {"success": False, "reason": "error", "error": str(e)}
```

---

This API reference provides comprehensive documentation for integrating with the CyberArk Privilege Cloud MCP Server. For additional examples and troubleshooting guidance, refer to the [Testing Guide](TESTING.md) and [Troubleshooting Guide](TROUBLESHOOTING.md).