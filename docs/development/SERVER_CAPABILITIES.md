# CyberArk Privilege Cloud MCP Server Capabilities

## Overview
This document defines the capabilities that the MCP server will provide for CyberArk Privilege Cloud integration.

## Authentication
- **Method**: OAuth 2.0 API token authentication using client credentials flow
- **Token Management**: Automatic token refresh (15-minute expiration)
- **Configuration**: Environment variables for secure credential storage

## Core Capabilities (MVP)

### 1. Account Management Tools

#### `list_accounts`
- **Description**: Retrieve a list of accounts from CyberArk Privilege Cloud
- **Parameters**:
  - `safe_name` (optional): Filter accounts by safe name
  - `username` (optional): Filter accounts by username
  - `address` (optional): Filter accounts by address
- **Returns**: List of account objects with basic information
- **API Endpoint**: `GET /PasswordVault/API/Accounts`

#### `get_account_details`
- **Description**: Get detailed information about a specific account
- **Parameters**:
  - `account_id` (required): Unique identifier for the account
- **Returns**: Complete account object with all properties
- **API Endpoint**: `GET /PasswordVault/API/Accounts/{accountId}`

#### `search_accounts`
- **Description**: Advanced search for accounts with multiple filter criteria
- **Parameters**:
  - `keywords` (optional): Search keywords
  - `safe_name` (optional): Filter by safe name
  - `username` (optional): Filter by username
  - `address` (optional): Filter by address/hostname
  - `platform_id` (optional): Filter by platform ID
- **Returns**: List of matching accounts
- **API Endpoint**: `GET /PasswordVault/API/Accounts` with query parameters

#### `create_account` ✅ **IMPLEMENTED**
- **Description**: Create a new privileged account in CyberArk Privilege Cloud
- **Parameters**:
  - `platform_id` (required): Platform ID for the account (e.g., WinServerLocal, UnixSSH)
  - `safe_name` (required): Safe where the account will be created
  - `name` (optional): Account name/identifier
  - `address` (optional): Target address/hostname
  - `user_name` (optional): Username for the account
  - `secret` (optional): Password or SSH key
  - `secret_type` (optional): Type of secret - 'password' or 'key'
  - `platform_account_properties` (optional): Platform-specific properties
  - `secret_management` (optional): Secret management configuration
  - `remote_machines_access` (optional): Remote access configuration
- **Returns**: Created account object with ID and metadata
- **API Endpoint**: `POST /PasswordVault/API/Accounts`
- **Validation**: Required parameters, special character checking, secret type validation
- **Security**: Secure credential handling, comprehensive input validation

### 2. Safe Management Tools (Basic)

#### `list_safes`
- **Description**: List all accessible safes
- **Parameters**:
  - `search` (optional): Search term for safe names
- **Returns**: List of safe objects
- **API Endpoint**: `GET /PasswordVault/API/Safes`

#### `get_safe_details`
- **Description**: Get detailed information about a specific safe
- **Parameters**:
  - `safe_name` (required): Name of the safe
- **Returns**: Safe object with properties and permissions
- **API Endpoint**: `GET /PasswordVault/API/Safes/{safeName}`

### 3. Platform Management Tools

#### `list_platforms`
- **Description**: List all available platforms in CyberArk Privilege Cloud
- **Parameters**:
  - `search` (optional): Search term for platform names
  - `active` (optional): Filter by active status (true/false)
  - `system_type` (optional): Filter by system type (e.g., Windows, Unix)
- **Returns**: List of platform objects with basic information
- **API Endpoint**: `GET /PasswordVault/API/Platforms`
- **Required Permissions**: Service account must be a member of Privilege Cloud Administrator role

#### `get_platform_details`
- **Description**: Get detailed information about a specific platform
- **Parameters**:
  - `platform_id` (required): Unique identifier for the platform (e.g., WinServerLocal, UnixSSH)
- **Returns**: Complete platform object with configuration details
- **API Endpoint**: `GET /PasswordVault/API/Platforms/{platformId}`
- **Required Permissions**: Service account must be a member of Privilege Cloud Administrator role

## Environment Configuration

### Required Environment Variables
```
CYBERARK_IDENTITY_TENANT_ID=your-tenant-id
CYBERARK_CLIENT_ID=service-account-username
CYBERARK_CLIENT_SECRET=service-account-password
CYBERARK_SUBDOMAIN=your-privilege-cloud-subdomain
```

### Optional Environment Variables
```
CYBERARK_API_TIMEOUT=30
CYBERARK_MAX_RETRIES=3
CYBERARK_LOG_LEVEL=INFO
```

## Error Handling

### Standard Error Responses
- **401 Unauthorized**: Token expired or invalid credentials
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: CyberArk API error

### Error Recovery
- Automatic token refresh on 401 errors
- Exponential backoff retry for 429 errors
- Comprehensive logging for all error scenarios

## Security Considerations

### Authentication Security
- Store credentials in environment variables only
- Never log sensitive information (tokens, passwords)
- Implement secure token caching with automatic refresh

### API Security
- Use HTTPS for all communications
- Validate all input parameters
- Follow principle of least privilege for service accounts

## Future Enhancements (Post-MVP)

### Password Management
- `get_password`: Retrieve password for an account
- `change_password`: Initiate password change
- `verify_password`: Verify password compliance

### Advanced Account Operations
- `create_account`: Add new privileged account
- `update_account`: Modify account properties
- `delete_account`: Remove account from safe

### Session Management
- `list_sessions`: View active sessions
- `terminate_session`: End active session
- `get_session_recordings`: Access session recordings

### Platform Management
- `list_platforms`: Get available platforms ✅ **IMPLEMENTED**
- `get_platform_details`: View platform configuration ✅ **IMPLEMENTED**

### Reporting and Analytics
- `generate_access_report`: Account access reports
- `get_compliance_status`: Compliance dashboard data
- `audit_trail`: Access audit information

## Tool Categories

### Primary Tools (MVP)
1. **Account Discovery**: `list_accounts`, `search_accounts`
2. **Account Information**: `get_account_details`
3. **Safe Information**: `list_safes`, `get_safe_details`
4. **Platform Information**: `list_platforms`, `get_platform_details`

### Secondary Tools (Future)
1. **Password Operations**: Password retrieval and management
2. **Account Lifecycle**: Create, update, delete operations
3. **Session Management**: Active session monitoring
4. **Reporting**: Access reports and analytics

## Success Metrics

### MVP Success Criteria
- [ ] Successful authentication with CyberArk Privilege Cloud
- [ ] Ability to list and search accounts
- [ ] Retrieve detailed account information
- [ ] List and view safe information
- [ ] Proper error handling and logging
- [ ] Integration with MCP Inspector for testing

### Performance Targets
- **Response Time**: < 5 seconds for typical API calls
- **Token Management**: Automatic refresh without user intervention
- **Error Recovery**: Graceful handling of temporary API failures
- **Rate Limiting**: Respect CyberArk API rate limits