# CyberArk Privilege Cloud MCP Server Capabilities

This document provides a comprehensive overview of all capabilities provided by the CyberArk Privilege Cloud MCP Server, including tools and resources.

## Overview

The CyberArk Privilege Cloud MCP Server provides two main types of capabilities:

1. **Tools**: Function-based operations for managing CyberArk entities
2. **Resources**: URI-based access to CyberArk data objects

## Server Information

- **Name**: CyberArk Privilege Cloud MCP Server
- **Version**: 0.1.0
- **Protocol**: Model Context Protocol (MCP)
- **Framework**: FastMCP
- **Language**: Python 3.8+

## Tools

The server provides 10 tools for comprehensive CyberArk management:

### Account Management Tools

#### `list_accounts`
- **Purpose**: List accounts with optional filtering
- **Parameters**: 
  - `safe_name` (optional): Filter by safe name
  - `username` (optional): Filter by username
  - `address` (optional): Filter by address
- **Returns**: Array of account objects
- **Example**:
  ```json
  {
    "safe_name": "ProductionServers",
    "username": "admin"
  }
  ```

#### `get_account_details`
- **Purpose**: Get detailed information for a specific account
- **Parameters**:
  - `account_id` (required): Unique account identifier
- **Returns**: Detailed account object with all properties
- **Example**:
  ```json
  {
    "account_id": "12345"
  }
  ```

#### `search_accounts`
- **Purpose**: Advanced account search with multiple criteria
- **Parameters**:
  - `keywords` (optional): Free text search
  - `safe_name` (optional): Filter by safe
  - `username` (optional): Filter by username
  - `address` (optional): Filter by address
  - `platform_id` (optional): Filter by platform
- **Returns**: Array of matching accounts
- **Example**:
  ```json
  {
    "keywords": "webserver",
    "safe_name": "ProductionServers",
    "platform_id": "WinServerLocal"
  }
  ```

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

### Safe Management Tools

#### `list_safes`
- **Purpose**: List accessible safes with optional filtering
- **Parameters**:
  - `search` (optional): Search term
  - `offset` (optional): Pagination offset
  - `limit` (optional): Results limit
  - `sort` (optional): Sort order
  - `include_accounts` (optional): Include account counts
  - `extended_details` (optional): Include extended metadata
- **Returns**: Array of safe objects
- **Example**:
  ```json
  {
    "search": "Production",
    "limit": 20,
    "include_accounts": true
  }
  ```

#### `get_safe_details`
- **Purpose**: Get detailed information for a specific safe
- **Parameters**:
  - `safe_name` (required): Safe name
  - `include_accounts` (optional): Include account list
  - `use_cache` (optional): Use cached data
- **Returns**: Detailed safe object
- **Example**:
  ```json
  {
    "safe_name": "ProductionServers",
    "include_accounts": true
  }
  ```

### Platform Management Tools

#### `list_platforms`
- **Purpose**: List available platforms
- **Parameters**:
  - `search` (optional): Search term
  - `active` (optional): Filter by active status
  - `system_type` (optional): Filter by system type
- **Returns**: Array of platform objects
- **Example**:
  ```json
  {
    "active": true,
    "system_type": "Windows"
  }
  ```

#### `get_platform_details`
- **Purpose**: Get detailed platform configuration
- **Parameters**:
  - `platform_id` (required): Platform identifier
- **Returns**: Detailed platform object
- **Example**:
  ```json
  {
    "platform_id": "WinServerLocal"
  }
  ```

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

## Resources

The server provides URI-based resource access for browsing and caching CyberArk data:

### Resource Types

1. **Collection Resources**: Lists of entities
2. **Entity Resources**: Individual objects with full details
3. **Search Resources**: Query-based filtered views
4. **System Resources**: Health and status information

### Available Resources

#### Health Resources
- `cyberark://health/` - System health and connectivity status

#### Safe Resources
- `cyberark://safes/` - Collection of all accessible safes
- `cyberark://safes/{safe_name}/` - Individual safe details
- `cyberark://safes/{safe_name}/accounts/` - Accounts within a safe

#### Account Resources
- `cyberark://accounts/` - Collection of all accessible accounts
- `cyberark://accounts/{account_id}/` - Individual account details
- `cyberark://accounts/search?query={terms}` - Search accounts with filters

#### Platform Resources
- `cyberark://platforms/` - Collection of all available platforms
- `cyberark://platforms/{platform_id}/` - Individual platform details
- `cyberark://platforms/packages/` - Platform package information

### Resource Features

- **URI-based Addressing**: Direct access via standardized URIs
- **Hierarchical Navigation**: Browse from collections to entities
- **Search Capabilities**: Query-based resource filtering
- **Metadata Support**: Rich metadata for each resource
- **Caching Friendly**: Resources designed for client-side caching
- **Error Handling**: Structured error responses

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
- Health check: < 100ms
- List operations: < 500ms
- Individual entity access: < 300ms
- Search operations: < 1000ms
- Create operations: < 2000ms

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
1. **Tool-based Workflow**: Use tools for operations and modifications
2. **Resource-based Browsing**: Use resources for discovery and navigation
3. **Hybrid Approach**: Combine tools and resources for optimal experience

### Best Practices
- Start with health check to verify connectivity
- Use resources for discovery and browsing
- Use tools for specific operations and modifications
- Implement appropriate caching strategies
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