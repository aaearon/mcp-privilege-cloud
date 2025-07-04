# CyberArk Privilege Cloud MCP Server Capabilities

This document provides a comprehensive overview of all capabilities provided by the CyberArk Privilege Cloud MCP Server, including tools and resources.

## Overview

The CyberArk Privilege Cloud MCP Server provides comprehensive access to CyberArk Privilege Cloud through:

**Tools**: Function-based operations for all CyberArk interactions, including data access and entity management. All tools return exact CyberArk API data with no field manipulation.

## Server Information

- **Name**: CyberArk Privilege Cloud MCP Server
- **Version**: 0.1.0
- **Protocol**: Model Context Protocol (MCP)
- **Framework**: FastMCP
- **Language**: Python 3.8+

## Tools

The server provides 10 tools for CyberArk operations, returning exact API data with no manipulation:

### Data Access Tools

#### `list_accounts`
- **Purpose**: List all accessible accounts
- **Parameters**: None
- **Returns**: List of account objects with exact CyberArk API fields
- **Example Response**:
  ```json
  [
    {
      "id": "123_456",
      "name": "admin@server01",
      "userName": "admin",
      "address": "server01.corp.com",
      "platformId": "WinServerLocal",
      "safeName": "IT-Infrastructure",
      "secretType": "password",
      "createdTime": "2025-01-01T00:00:00Z"
    }
  ]
  ```

#### `search_accounts`
- **Purpose**: Search accounts with various criteria
- **Parameters**:
  - `query` (optional): General search keywords
  - `safe_name` (optional): Filter by safe name
  - `username` (optional): Filter by username  
  - `address` (optional): Filter by address
  - `platform_id` (optional): Filter by platform ID
- **Returns**: List of matching account objects with search scores
- **Example**:
  ```json
  {
    "query": "admin",
    "safe_name": "IT-Infrastructure",
    "platform_id": "WinServerLocal"
  }
  ```

#### `list_safes`
- **Purpose**: List all accessible safes
- **Parameters**: None
- **Returns**: List of safe objects with exact CyberArk API fields
- **Example Response**:
  ```json
  [
    {
      "safeName": "IT-Infrastructure",
      "safeNumber": 123,
      "description": "IT Infrastructure accounts",
      "managingCPM": "PasswordManager",
      "createdBy": "Administrator"
    }
  ]
  ```

#### `list_platforms`
- **Purpose**: List all available platforms
- **Parameters**: None  
- **Returns**: List of platform objects with exact CyberArk API fields
- **Example Response**:
  ```json
  [
    {
      "id": "WinServerLocal",
      "name": "Windows Server Local",
      "systemType": "Windows",
      "active": true,
      "platformType": "Regular",
      "description": "Windows Server Local Accounts"
    }
  ]
  ```

### Account Management Tools

#### `create_account`
- **Purpose**: Create a new privileged account
- **Parameters**:
  - `platform_id` (required): Platform identifier
  - `safe_name` (required): Target safe name
  - `name` (optional): Account name
  - `address` (optional): Account address
  - `user_name` (optional): Username
  - `secret` (optional): Password/secret
  - `secret_type` (optional): Type of secret
  - `platform_account_properties` (optional): Platform-specific properties
  - `secret_management` (optional): Secret management settings
  - `remote_machines_access` (optional): Remote access settings
- **Returns**: Created account object with ID
- **Example**:
  ```json
  {
    "platform_id": "WinServerLocal",
    "safe_name": "ProductionServers",
    "name": "webserver01-admin",
    "address": "webserver01.prod.corp.com",
    "user_name": "administrator"
  }
  ```

### Password Management Tools

#### `change_account_password`
- **Purpose**: Change password for an account
- **Parameters**:
  - `account_id` (required): Account identifier
  - `new_password` (optional): New password
- **Returns**: Operation result
- **Example**:
  ```json
  {
    "account_id": "12345",
    "new_password": "NewSecurePassword123!"
  }
  ```

#### `set_next_password`
- **Purpose**: Set the next password for an account
- **Parameters**:
  - `account_id` (required): Account identifier
  - `password` (required): Next password to set
- **Returns**: Operation result
- **Example**:
  ```json
  {
    "account_id": "12345",
    "password": "NextPassword123!"
  }
  ```

#### `verify_account_password`
- **Purpose**: Verify the current password for an account
- **Parameters**:
  - `account_id` (required): Account identifier
- **Returns**: Verification result
- **Example**:
  ```json
  {
    "account_id": "12345"
  }
  ```

#### `reconcile_account_password`
- **Purpose**: Reconcile account password with target system
- **Parameters**:
  - `account_id` (required): Account identifier
- **Returns**: Reconciliation result
- **Example**:
  ```json
  {
    "account_id": "12345"
  }
  ```

### Platform Management Tools

#### `import_platform_package`
- **Purpose**: Import a platform package
- **Parameters**:
  - `platform_package_file` (required): Platform package file path
- **Returns**: Import result with platform ID
- **Example**:
  ```json
  {
    "platform_package_file": "/path/to/platform.zip"
  }
  ```

## Key Features

### Tool-Based Architecture
- **Direct Function Calls**: Simple tool invocation vs complex URI handling
- **Better Client Compatibility**: Works consistently across all MCP clients  
- **Exact API Data**: Zero field manipulation - returns raw CyberArk API responses
- **Type Safety**: Full TypeScript/Python type annotations for all parameters
- **Error Handling**: Structured error responses with detailed messages

### Data Integrity
- **Original Field Names**: Preserves CamelCase fields (e.g., `userName`, `platformId`)
- **Raw API Values**: No data transformation or conversion applied
- **Complete Structures**: Full API response objects maintained
- **Search Scores**: Preserved when available (e.g., `_score` field)

### Performance & Reliability
- **Direct Server Methods**: Tools call server methods directly
- **Efficient Operations**: No URI parsing or resource registry overhead
- **Concurrent Safe**: All tools support concurrent execution
- **Authentication**: Automatic OAuth token refresh and validation

## Authentication & Security

### Authentication
- **Method**: OAuth 2.0 Client Credentials Flow
- **Token Lifetime**: 15 minutes with automatic refresh
- **Scope**: CyberArk Privilege Cloud API access

### Required Environment Variables
- `CYBERARK_IDENTITY_TENANT_ID` - Tenant identifier
- `CYBERARK_CLIENT_ID` - OAuth client ID
- `CYBERARK_CLIENT_SECRET` - OAuth client secret
- `CYBERARK_SUBDOMAIN` - Privilege Cloud subdomain

### Security Features
- Automatic token refresh with double-checked locking
- Secure credential management through environment variables
- API permission validation
- Safe-based access control
- Audit logging for all operations

## Error Handling

### Tool Errors
Tools return structured error information:
- HTTP status code mapping
- Detailed error messages
- Operation context
- Retry recommendations

### Resource Errors
Resources return JSON error objects:
- Error type classification
- Human-readable messages
- Available alternatives
- Troubleshooting guidance

### Common Error Types
- **Authentication Errors**: Invalid credentials or expired tokens
- **Permission Errors**: Insufficient privileges for operations
- **Not Found Errors**: Requested entities don't exist
- **Validation Errors**: Invalid parameters or data
- **Server Errors**: CyberArk API or network issues

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

## Client Integration

### MCP Client Support
- **Claude Desktop**: Full support with `uvx mcp-privilege-cloud`
- **MCP Inspector**: Complete tool and resource browsing
- **Custom Clients**: Standard MCP protocol compatibility

### Integration Patterns
1. **Resource-first Discovery**: Use resources to browse and discover accounts, safes, and platforms
2. **Tool-based Actions**: Use tools for creating accounts, managing passwords, and platform operations
3. **Hybrid Workflow**: Combine resource browsing with targeted tool actions for optimal experience

### Best Practices
- Start with health check resource to verify connectivity
- Use collection resources (accounts/, safes/, platforms/) for discovery and browsing
- Use search resources for filtered views and specific queries
- Use tools only for create/modify operations (account creation, password management)
- Implement client-side caching for frequently accessed resources
- Handle errors gracefully with user feedback

## Monitoring & Observability

### Logging
- Structured logging with configurable levels
- Operation tracking and performance metrics
- Error logging with context and stack traces
- Authentication and authorization audit trail

### Metrics
- Tool usage statistics
- Resource access patterns
- Response time distributions
- Error rates and types
- Authentication success/failure rates

### Health Monitoring
- Connectivity status to CyberArk APIs
- Token refresh success rates
- API response time monitoring
- Safe accessibility verification

## Future Capabilities

### Planned Enhancements
1. **Advanced Password Operations**: Retrieve, rotate, and manage secrets
2. **Safe Management**: Create, update, and configure safes
3. **User Management**: Manage safe members and permissions
4. **Session Management**: Monitor and control privileged sessions
5. **Audit & Compliance**: Access audit logs and compliance reports

### API Evolution
- Backward compatibility guaranteed
- Incremental capability additions
- Optional feature flags
- Version negotiation support

---

For detailed usage examples and integration guides, see:
- [Resource Documentation](docs/RESOURCES.md)
- [URI Schema Reference](docs/URI_SCHEMA.md)
- [README](README.md)
- [Testing Guide](docs/TESTING.md)