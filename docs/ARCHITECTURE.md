# Idira Privilege Cloud MCP Server - Architecture Reference

**🤖 LLM REFERENCE**: This document provides complete architectural patterns for implementing new features. Use as reference for maintaining consistency with established patterns.

**QUICK REFERENCE FOR LLM**:
- ✅ **Use**: @handle_sdk_errors decorator, execute_tool() function, SDK service classes
- ❌ **Never**: Manual try/catch blocks, individual tool wrappers, direct HTTP clients

## Overview

The Idira Privilege Cloud MCP Server follows a **simplified, streamlined architecture** leveraging the official Idira SDK, with clear separation of concerns and enterprise-grade reliability. Through comprehensive refactoring, the codebase achieved **~27% code reduction** while maintaining full functionality. It enables AI assistants to securely manage privileged accounts through the Model Context Protocol (MCP) with official Idira support.

## Core Components

The project is structured around these core modules leveraging the official ark-sdk-python:

```
src/mcp_privilege_cloud/
├── sdk_auth.py          # Legacy service account authentication
├── token_verifier.py    # JWT verification via Idira Identity JWKS
├── server.py            # Core Idira API integration via SDK
├── mcp_server.py        # MCP protocol implementation (Streamable HTTP)
└── exceptions.py        # Custom exception handling
```

### Authentication Architecture (Dual-Mode)

The server supports two authentication modes:

**OAuth Per-User Mode** (recommended for multi-user deployments):
- Users authenticate via Idira Identity OAuth Authorization Code flow
- Each user's JWT is verified against the JWKS endpoint by `CyberArkTokenVerifier`
- A shared service account platform token is used for all PCloud API calls
- User identity from the JWT is logged for audit purposes

**Legacy Service Account Mode** (single shared identity):
- A single service account authenticates via `CYBERARK_CLIENT_ID`/`CYBERARK_CLIENT_SECRET`
- All requests share one `CyberArkMCPServer` instance
- Authentication handled by `CyberArkSDKAuthenticator` in `sdk_auth.py`

### 1. Token Verifier (`token_verifier.py`)

**Purpose**: MCP SDK `TokenVerifier` protocol implementation for Idira Identity JWTs

**Key Features**:
- **JWKS Validation**: Verifies JWT signatures against Idira Identity `/oauth2/certs`
- **MCP Protocol Compliance**: Returns `AccessToken` for MCP auth middleware
- **Claim Validation**: Enforces `exp`, `iss`, `sub`, `aud` with RS256 algorithm
- **Graceful Failures**: Returns `None` on any verification failure (no exceptions)

### 2. Legacy SDK Authentication (`sdk_auth.py`)

**Purpose**: Service account authentication wrapper (legacy mode)

**Key Features**:
- **Official SDK Integration**: Uses ark-sdk-python for authenticated API access
- **Automatic Token Management**: SDK handles token lifecycle automatically
- **Environment Configuration**: Seamless integration with existing credential management

### 3. Server Module (`server.py`)

**Purpose**: Core business logic using official ark-sdk-python services

**Key Features**:
- **Complete SDK Service Integration**: Uses ArkPCloudAccountsService, ArkPCloudSafesService, ArkPCloudPlatformsService, ArkPCloudApplicationsService, ArkSMService (all 5 PCloud services)
- **Simplified Architecture**: Eliminates custom HTTP client in favor of SDK services
- **Enhanced Reliability**: SDK handles authentication, rate limiting, and error handling
- **Response Processing**: Direct SDK response handling with data integrity preservation
- **Concurrent Operations**: Optimized platform fetching with concurrent SDK calls

**Implementation Details**:
- Service-based architecture using SDK service classes
- Property-based lazy loading of SDK services
- Direct SDK method invocation with enhanced error handling
- Response normalization while preserving data integrity

### 4. MCP Integration (`mcp_server.py`)

**Purpose**: Model Context Protocol implementation with enhanced SDK-powered tools

**Key Features**:
- **FastMCP Server**: MCP protocol implementation
- **Comprehensive Tool Suite**: 53 enterprise-grade action tools for complete Idira PCloud operations across all 5 services (18+10+10+9+6)
- **SDK-Powered Reliability**: All tools leverage official ark-sdk-python services
- **Parameter Validation**: Enhanced input validation and type checking
- **Cross-Platform Support**: Windows encoding compatibility
- **Tool-Based Architecture**: Function-based operations with SDK service integration

**Implementation Details**:
- Tool registration and parameter validation
- Direct method invocation from MCP tools to server methods
- Comprehensive error handling and response formatting

## API Integration Architecture

### Authentication Flows

**OAuth Per-User Mode:**
```
MCP Client → Bearer Token → CyberArkTokenVerifier (JWKS) → AccessToken
                                                               ↓
execute_tool() → get_access_token() → verify user identity (audit log)
                                              ↓
                              Shared CyberArkMCPServer (service account)
                                              ↓
                              SDK Services → Idira PCloud API
```

**Legacy Service Account Mode:**
```
Client Request → MCP Tool → Server Method → SDK Auth → ark-sdk-python → Idira Identity
                                      ↓                      ↓
                              SDK Service Instance    Auto Token Management
                                      ↓                      ↓
Server Method → SDK Service → Idira API → SDK Response → MCP Response
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
3. **Server Method** obtains SDK service instance (accounts/safes/platforms/applications for complete PCloud coverage)
4. **SDK Service** automatically handles authentication via ark-sdk-python
5. **SDK Service** calls Idira API with proper authentication and error handling
6. **SDK Response** provides exact API data with built-in data integrity
7. **MCP Response** returns SDK response data to client with enhanced reliability

### Configuration Management

**OAuth Per-User Mode Environment Variables** (recommended):
- `CYBERARK_IDENTITY_TENANT_URL` - Idira Identity tenant URL (e.g., `https://abc1234.id.cyberark.cloud`)
- `CYBERARK_CLIENT_ID` - Service account login name (for PCloud platform token)
- `CYBERARK_CLIENT_SECRET` - Service account password
- `CYBERARK_OAUTH_CLIENT_ID` - OIDC app client ID from Trust tab (for DCR and JWT audience)
- `CYBERARK_OAUTH_CLIENT_SECRET` - OIDC app client secret from Trust tab (injected server-side in /token proxy)
- `MCP_TRANSPORT` - Transport protocol: `stdio`, `sse`, or `streamable-http` (default: `stdio`)
- `MCP_HOST` - Server bind host (default: `127.0.0.1`)
- `MCP_PORT` - Server bind port (default: `8000`)
- `MCP_SERVER_URL` - Public URL for metadata (default: `http://{host}:{port}`)

**Legacy Service Account Mode Environment Variables**:
- `CYBERARK_CLIENT_ID` - OAuth service account username
- `CYBERARK_CLIENT_SECRET` - Service account password

**Mode Detection**: The server automatically selects OAuth mode when `CYBERARK_IDENTITY_TENANT_URL` is set; otherwise falls back to legacy mode.

**Security Principles**:
- Never log sensitive information (tokens, passwords)
- Environment variable-based configuration only
- JWT verification via JWKS for per-user tokens
- Principle of least privilege for service accounts

## Tool Architecture

The server exposes 53 enterprise-grade MCP tools organized by functionality across all 5 PCloud services, all powered by ark-sdk-python:

**Account Management Tools (18 tools)**:
- Core Operations: `list_accounts`, `get_account_details`, `search_accounts`, `create_account`, `update_account`, `delete_account`
- Password Management: `change_account_password`, `set_next_password`, `verify_account_password`, `reconcile_account_password`
- Advanced Search: `filter_accounts_by_platform_group`, `filter_accounts_by_environment`, `filter_accounts_by_management_status`, `group_accounts_by_safe`, `group_accounts_by_platform`, `analyze_account_distribution`, `search_accounts_by_pattern`, `count_accounts_by_criteria`

**Safe Management Tools (10 tools)**:
- Core Operations: `list_safes`, `get_safe_details`, `add_safe`, `update_safe`, `delete_safe`
- Member Management: `list_safe_members`, `get_safe_member_details`, `add_safe_member`, `update_safe_member`, `remove_safe_member`

**Platform Management Tools (10 tools)**:
- Core Operations: `list_platforms`, `get_platform_details`, `import_platform_package`, `export_platform`
- Lifecycle Management: `duplicate_target_platform`, `activate_target_platform`, `deactivate_target_platform`, `delete_target_platform`
- Statistics: `get_platform_statistics`, `get_target_platform_statistics`

**Applications Management Tools (9 tools)**:
- Core Operations: `list_applications`, `get_application_details`, `add_application`, `delete_application`
- Auth Methods: `list_application_auth_methods`, `get_application_auth_method_details`, `add_application_auth_method`, `delete_application_auth_method`
- Statistics: `get_applications_stats`

**Session Monitoring Tools (6 tools)**:
- Session Management: `list_sessions`, `list_sessions_by_filter`, `get_session_details`, `count_sessions`
- Activity Tracking: `list_session_activities`, `get_session_statistics`

All tools follow consistent SDK-powered patterns:
- Direct SDK service method invocation
- Enhanced parameter validation with SDK models
- Exact API data preservation through SDK responses
- Comprehensive error handling with SDK exceptions

## Simplified Architecture Patterns ✅ **ENHANCED**

### Code Simplification Results

The codebase underwent systematic refactoring achieving **~27% code reduction** (from ~1,365 to ~1,000 lines) while maintaining 100% functionality and test coverage.

#### Key Simplification Achievements

**1. Centralized Error Handling**:
```python
@handle_sdk_errors("operation description")
async def server_method(self, *args, **kwargs):
    # Clean business logic without repetitive try/catch
    return await sdk_operation()
```

**2. Streamlined Tool Execution**:
```python
async def execute_tool(tool_name: str, ctx=None, **kwargs):
    app_ctx = ctx.request_context.lifespan_context
    server_method = getattr(app_ctx.server, tool_name)
    return await server_method(**kwargs)
```

**3. Simplified Service Management**:
```python
def __init__(self):
    sdk_auth = self.sdk_authenticator.get_authenticated_client()
    self.accounts_service = ArkPCloudAccountsService(sdk_auth)
    self.safes_service = ArkPCloudSafesService(sdk_auth)
    self.platforms_service = ArkPCloudPlatformsService(sdk_auth)
    self.applications_service = ArkPCloudApplicationsService(sdk_auth)
```

**4. Optimized Data Processing**:
```python
def _flatten_platform_structure(self, platform_data: Dict[str, Any]) -> Dict[str, Any]:
    result = {}
    for section_name, section_data in platform_data.items():
        if isinstance(section_data, dict):
            result.update(section_data)
        else:
            result[section_name] = section_data
    return result
```

### Architecture Benefits

**Maintainability**:
- Single point of control for error handling, tool execution, service initialization
- Reduced cognitive load with less code to understand and maintain
- Enhanced debugging with centralized logging and error patterns
- Simplified testing with cleaner mocking and assertion patterns

**Performance & Reliability**:
- Zero regression - all tests pass with identical behavior
- Preserved SDK benefits with official integration patterns
- Improved error consistency with standardized logging
- Future-proof design with simpler patterns easier to extend