# CyberArk Privilege Cloud MCP Server - Architecture

This document provides the complete architectural overview of the CyberArk Privilege Cloud MCP Server.

## Overview

The CyberArk Privilege Cloud MCP Server follows a layered architecture with clear separation of concerns, enabling AI assistants to securely manage privileged accounts through the Model Context Protocol (MCP).

## Core Components

The project is structured around three main modules:

```
src/mcp_privilege_cloud/
├── auth.py          # OAuth 2.0 authentication module
├── server.py        # Core CyberArk API integration
└── mcp_server.py    # MCP protocol implementation
```

### 1. Authentication Module (`auth.py`)

**Purpose**: Secure token-based authentication with CyberArk Identity

**Key Features**:
- **OAuth 2.0 Client Credentials Flow**: Secure token-based authentication
- **Automatic Token Refresh**: 15-minute expiration with 60-second safety margin
- **Concurrent Request Handling**: Double-checked locking pattern for thread safety
- **Error Recovery**: Comprehensive retry logic for authentication failures
- **Environment Variable Configuration**: Secure credential management

**Implementation Details**:
- Token caching with automatic refresh
- Double-checked locking for concurrent token requests
- Graceful handling of token expiration scenarios

### 2. Server Module (`server.py`)

**Purpose**: Core business logic for CyberArk API integration

**Key Features**:
- **CyberArk API Integration**: Core business logic for account/safe/platform operations
- **HTTP Client Management**: Proper authentication headers and timeout handling
- **Response Processing**: Handles API inconsistencies (value vs Platforms fields)
- **Error Handling**: Network, permission, and rate limiting scenarios
- **Data Integrity**: Preserves exact API responses without field transformations

**Implementation Details**:
- Standardized HTTP client with authentication injection
- Consistent error handling across all API operations
- Response normalization while preserving data integrity

### 3. MCP Integration (`mcp_server.py`)

**Purpose**: Model Context Protocol implementation and tool exposure

**Key Features**:
- **FastMCP Server**: MCP protocol implementation
- **Action Tools**: 10 action tools for CyberArk operations
- **Parameter Validation**: Input validation and type checking
- **Cross-Platform Support**: Windows encoding compatibility
- **Tool-Based Architecture**: Function-based operations replacing resource URIs

**Implementation Details**:
- Tool registration and parameter validation
- Direct method invocation from MCP tools to server methods
- Comprehensive error handling and response formatting

## API Integration Architecture

### Authentication Flow

```
Client Request → MCP Tool → Server Method → Auth Module → CyberArk Identity
                                      ↓
                            Generate/Refresh Token
                                      ↓
Server Method → CyberArk API → Response Processing → MCP Response
```

### Base URLs and Endpoints

- **API Base**: `https://{subdomain}.privilegecloud.cyberark.cloud/PasswordVault/api`
- **Authentication**: `https://{tenant-id}.id.cyberark.cloud/oauth2/platformtoken`

### Critical Integration Notes

- **TLD**: Uses `.cloud` not `.com` (common mistake)
- **API Version Policy**: ALWAYS use Gen2 endpoints when available (not Gen1)
- **Response Parsing**: `value` field for arrays (except Platforms API uses `Platforms`)
- **Platform APIs**: Require Privilege Cloud Administrator role membership
- **Data Integrity**: All API responses preserved exactly - no field name or value transformations applied

### Error Handling Strategy

**Authentication Errors (401)**:
- Automatic token refresh and retry
- Comprehensive logging for debugging

**Permission Errors (403)**:
- Enhanced error messages with specific role requirements
- Graceful degradation where possible

**Rate Limiting (429)**:
- Detection and retry recommendations
- Concurrency guidance for batch operations

**Network Errors**:
- Comprehensive logging and user-friendly messages
- Timeout and connection failure handling

## Data Flow Architecture

### Tool Invocation Flow

1. **MCP Client** calls tool via MCP protocol
2. **MCP Server** validates parameters and routes to server method
3. **Server Method** authenticates via Auth Module
4. **Auth Module** provides valid token (refresh if needed)
5. **Server Method** calls CyberArk API with authenticated request
6. **Response Processing** normalizes response while preserving data integrity
7. **MCP Response** returns exact API data to client

### Configuration Management

**Environment Variables**:
- `CYBERARK_IDENTITY_TENANT_ID` - Tenant ID (without .id.cyberark.cloud suffix)
- `CYBERARK_CLIENT_ID` - OAuth service account username
- `CYBERARK_CLIENT_SECRET` - Service account password
- `CYBERARK_SUBDOMAIN` - Subdomain (without .privilegecloud.cyberark.cloud suffix)

**Security Principles**:
- Never log sensitive information (tokens, passwords)
- Environment variable-based configuration only
- OAuth token caching with automatic refresh
- Principle of least privilege for service accounts

## Tool Architecture

The server exposes 10 MCP tools organized by functionality:

**Data Access Tools**:
- `list_accounts`, `search_accounts`, `list_safes`, `list_platforms`

**Account Management Tools**:
- `create_account`, `change_account_password`, `set_next_password`, `verify_account_password`, `reconcile_account_password`

**Platform Management Tools**:
- `import_platform_package`

All tools follow consistent patterns:
- Direct server method invocation
- Standardized parameter validation
- Exact API data preservation
- Comprehensive error handling

## Performance Characteristics

**Concurrent Operations**: Supported with proper authentication token sharing
**Connection Pooling**: HTTP client connection reuse
**Token Caching**: Secure in-memory token storage with automatic refresh
**Response Times**: Optimized for sub-2-second tool operations

For detailed API specifications, see [API Reference](docs/API_REFERENCE.md).
For development workflows, see [Development Guide](DEVELOPMENT.md).