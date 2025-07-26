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
CYBERARK_CLIENT_ID=service-account-username    # OAuth service account
CYBERARK_CLIENT_SECRET=service-account-password

# Optional Configuration
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

### Data Access Tools (Discovery)
1. **Accounts**: `list_accounts()`, `search_accounts()` - List and search accounts
2. **Safes**: `list_safes()` - List and filter safes
3. **Platforms**: `list_platforms()` - List available platforms

### Future Enhancement Categories
1. **Account Lifecycle**: Update and delete operations
2. **Session Management**: Active session monitoring
3. **Reporting**: Access reports and analytics
4. **Advanced Safe Management**: Create and update operations

## Account Management Tools

### `list_accounts`

**Description**: List all accessible accounts in CyberArk Privilege Cloud.

**Parameters**: None

**Returns**: List of account objects with exact API fields

**Example Usage**:
```python
# List all accessible accounts
accounts = await client.call_tool("list_accounts", {})
```

**Response Example**:
```json
[
  {
    "id": "123_456",
    "name": "DatabaseAdmin", 
    "address": "db.company.com",
    "userName": "dbadmin",
    "platformId": "MySQLDB",
    "safeName": "Database-Safes",
    "secretType": "password",
    "createdTime": 1640995200
  }
]
```

---

### `search_accounts`

**Description**: Search for accounts with various criteria.

**Parameters**:
- `query` (optional, string): General search keywords
- `safe_name` (optional, string): Filter by safe name
- `username` (optional, string): Filter by username
- `address` (optional, string): Filter by address/hostname
- `platform_id` (optional, string): Filter by platform ID

**Returns**: List of matching account objects with exact API fields

**Example Usage**:
```python
# Search with multiple criteria
accounts = await client.call_tool("search_accounts", {
    "query": "database",
    "safe_name": "Database-Safes",
    "platform_id": "MySQLDB"
})

# Search by address pattern
accounts = await client.call_tool("search_accounts", {
    "address": "*.company.com"
})
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

### `list_safes`

**Description**: List all accessible safes in CyberArk Privilege Cloud.

**Parameters**: None

**Returns**: List of safe objects with exact API fields

**Example Usage**:
```python
# List all accessible safes
safes = await client.call_tool("list_safes", {})
```

**Response Example**:
```json
[
  {
    "safeName": "Database-Safes",
    "description": "Database server accounts", 
    "location": "\\",
    "creator": "Admin",
    "olacEnabled": false,
    "managingCPM": "PasswordManager",
    "numberOfVersionsRetention": 5,
    "numberOfDaysRetention": 7,
    "autoPurgeEnabled": false,
    "creationTime": 1640995200,
    "modificationTime": 1640995300
  }
]
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

### `list_platforms`

**Description**: List all available platforms in CyberArk Privilege Cloud.

**Required Permissions**: Service account must be a member of the Privilege Cloud Administrator role

**Parameters**: None

**Returns**: List of platform objects with exact API fields

**Example Usage**:
```python
# List all platforms
platforms = await client.call_tool("list_platforms", {})
```

**Response Example**:
```json
[
  {
    "ID": "WinServerLocal",
    "Name": "Windows Server Local", 
    "SystemType": "Windows",
    "Active": true,
    "Description": "Windows Server Local Account",
    "PlatformBaseID": "WinServer",
    "PlatformType": "Regular"
  },
  {
    "ID": "UnixSSH",
    "Name": "Unix SSH",
    "SystemType": "Unix", 
    "Active": true,
    "Description": "Unix account via SSH",
    "PlatformBaseID": "Unix",
    "PlatformType": "Regular"
  }
]
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
# 1. Search for existing accounts using tools
existing_accounts = await client.call_tool("search_accounts", {
    "query": "webserver",
    "safe_name": "Web-Servers"
})

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
# 1. List all accessible safes using tools
all_safes = await client.call_tool("list_safes", {})

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
# 1. List all platforms using tools
platforms = await client.call_tool("list_platforms", {})

# 2. Filter for active platforms
active_platforms = [p for p in platforms if p.get("Active", False)]

# 3. Analyze platform information
for platform in active_platforms:
    platform_id = platform["ID"]
    platform_name = platform["Name"]
    system_type = platform["SystemType"]
    print(f"{platform_id} ({platform_name}): {system_type} platform")
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
        "CYBERARK_CLIENT_ID": "your-client-id",
        "CYBERARK_CLIENT_SECRET": "your-client-secret"
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

# Alternative approach using search tools for account discovery
async def discover_and_process_accounts(safe_name):
    # Discover accounts using search tools
    accounts = await client.call_tool("search_accounts", {
        "safe_name": safe_name
    })
    
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
            # Search for existing account using tools
            existing = await client.call_tool("search_accounts", {
                "username": account_data['user_name'],
                "address": account_data['address']
            })
            return {"success": False, "reason": "exists", "existing": existing}
        else:
            return {"success": False, "reason": "error", "error": str(e)}
```

## Performance Characteristics

### Response Times (Typical)
- Health check resource: < 100ms
- Collection resources: < 500ms
- Individual entity resources: < 300ms
- Search resources: < 1000ms
- Tool operations: < 2000ms

### Scalability
- Supports concurrent operations
- Connection pooling for API calls
- Efficient caching mechanisms
- Pagination for large datasets

### Rate Limiting
- Respects CyberArk API rate limits
- Automatic retry with exponential backoff
- Connection management optimization

## Best Practices

- Start with `list_accounts`, `list_safes`, or `list_platforms` tools to verify connectivity and discover available resources
- Use `search_accounts` tool for filtered views and specific account queries
- Use management tools (`create_account`, password management) for create/modify operations
- Implement client-side caching for frequently accessed data from list operations
- Handle errors gracefully with user feedback
- Use specific tools rather than broad listing when possible for better performance

---

This API reference provides comprehensive documentation for integrating with the CyberArk Privilege Cloud MCP Server. For additional examples and testing guidance, refer to the [Testing Guide](TESTING.md).