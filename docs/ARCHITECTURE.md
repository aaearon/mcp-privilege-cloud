# CyberArk Privilege Cloud MCP Server - Architecture

This document provides the complete architectural overview of the CyberArk Privilege Cloud MCP Server, now built on the official ark-sdk-python library.

## Overview

The CyberArk Privilege Cloud MCP Server follows a streamlined architecture leveraging the official CyberArk SDK, with clear separation of concerns and enterprise-grade reliability. It enables AI assistants to securely manage privileged accounts through the Model Context Protocol (MCP) with official CyberArk support.

## Core Components

The project is structured around four main modules leveraging the official ark-sdk-python:

```
src/mcp_privilege_cloud/
├── sdk_auth.py      # Official SDK authentication wrapper
├── server.py        # Core CyberArk API integration via SDK
├── mcp_server.py    # MCP protocol implementation  
└── exceptions.py    # Custom exception handling
```

### 1. SDK Authentication Module (`sdk_auth.py`)

**Purpose**: Official CyberArk SDK authentication wrapper for enterprise-grade security

**Key Features**:
- **Official SDK Integration**: Uses ark-sdk-python for authenticated API access
- **Automatic Token Management**: SDK handles token lifecycle automatically
- **Enterprise Security**: CyberArk-tested authentication patterns
- **Environment Configuration**: Seamless integration with existing credential management
- **Future-Proof Design**: Automatic compatibility with SDK updates

**Implementation Details**:
- Wraps ark-sdk-python authentication client
- Provides consistent interface for server methods
- Leverages SDK's built-in token management and error handling

### 2. Server Module (`server.py`)

**Purpose**: Core business logic using official ark-sdk-python services

**Key Features**:
- **SDK Service Integration**: Uses ArkPCloudAccountsService, ArkPCloudSafesService, ArkPCloudPlatformsService
- **Simplified Architecture**: Eliminates custom HTTP client in favor of SDK services
- **Enhanced Reliability**: SDK handles authentication, rate limiting, and error handling
- **Response Processing**: Direct SDK response handling with data integrity preservation
- **Concurrent Operations**: Optimized platform fetching with concurrent SDK calls

**Implementation Details**:
- Service-based architecture using SDK service classes
- Property-based lazy loading of SDK services
- Direct SDK method invocation with enhanced error handling
- Response normalization while preserving data integrity

### 3. MCP Integration (`mcp_server.py`)

**Purpose**: Model Context Protocol implementation with enhanced SDK-powered tools

**Key Features**:
- **FastMCP Server**: MCP protocol implementation
- **Enhanced Tool Suite**: 13 action tools for comprehensive CyberArk operations
- **SDK-Powered Reliability**: All tools leverage official ark-sdk-python services
- **Parameter Validation**: Enhanced input validation and type checking
- **Cross-Platform Support**: Windows encoding compatibility
- **Tool-Based Architecture**: Function-based operations with SDK service integration

**Implementation Details**:
- Tool registration and parameter validation
- Direct method invocation from MCP tools to server methods
- Comprehensive error handling and response formatting

## API Integration Architecture

### SDK-Enhanced Authentication Flow

```
Client Request → MCP Tool → Server Method → SDK Auth → ark-sdk-python → CyberArk Identity
                                      ↓                      ↓
                              SDK Service Instance    Auto Token Management
                                      ↓                      ↓
Server Method → SDK Service → CyberArk API → SDK Response → MCP Response
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

### SDK-Powered Tool Invocation Flow

1. **MCP Client** calls tool via MCP protocol
2. **MCP Server** validates parameters and routes to server method
3. **Server Method** obtains SDK service instance (accounts/safes/platforms)
4. **SDK Service** automatically handles authentication via ark-sdk-python
5. **SDK Service** calls CyberArk API with proper authentication and error handling
6. **SDK Response** provides exact API data with built-in data integrity
7. **MCP Response** returns SDK response data to client with enhanced reliability

### Configuration Management

**Environment Variables**:
- `CYBERARK_CLIENT_ID` - OAuth service account username
- `CYBERARK_CLIENT_SECRET` - Service account password

**Security Principles**:
- Never log sensitive information (tokens, passwords)
- Environment variable-based configuration only
- OAuth token caching with automatic refresh
- Principle of least privilege for service accounts

## Tool Architecture

The server exposes 13 MCP tools organized by functionality, all powered by ark-sdk-python:

**Data Access Tools**:
- `list_accounts`, `get_account_details`, `search_accounts`, `list_safes`, `get_safe_details`, `list_platforms`, `get_platform_details`

**Account Management Tools**:
- `create_account`, `change_account_password`, `set_next_password`, `verify_account_password`, `reconcile_account_password`

**Platform Management Tools**:
- `import_platform_package`

All tools follow consistent SDK-powered patterns:
- Direct SDK service method invocation
- Enhanced parameter validation with SDK models
- Exact API data preservation through SDK responses
- Comprehensive error handling with SDK exceptions

## Performance Characteristics

**SDK-Enhanced Performance**:
- **Concurrent Operations**: Supported with SDK-managed authentication token sharing
- **Connection Pooling**: SDK handles HTTP client connection reuse automatically
- **Token Management**: SDK provides secure automatic token refresh and caching
- **Response Times**: Optimized for sub-2-second tool operations with SDK efficiency
- **Enterprise Reliability**: Official CyberArk SDK provides production-grade performance

For detailed API specifications, see [API Reference](docs/API_REFERENCE.md).
For development workflows, see [Development Guide](DEVELOPMENT.md).