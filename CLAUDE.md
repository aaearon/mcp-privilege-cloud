# CyberArk Privilege Cloud MCP Server - Development Context

This document provides essential context for AI assistants developing the CyberArk Privilege Cloud MCP Server.

## Project Overview

**Purpose**: MCP server for CyberArk Privilege Cloud integration, enabling AI assistants to securely manage privileged accounts.

**Current Status**: ✅ MVP+ Complete - Production ready with automated CI/CD pipeline  
**Last Updated**: June 9, 2025  
**Recent Enhancement**: Enhanced safe management tools with full Gen2 API compliance

## Architecture Overview

### Core Components

1. **Authentication Module** (`src/cyberark_mcp/auth.py`)
   - OAuth 2.0 client credentials flow with 15-minute token expiration
   - Automatic token refresh with double-checked locking
   - Environment variable-based credential management

2. **Server Module** (`src/cyberark_mcp/server.py`)
   - CyberArk API integration with authentication headers
   - Account, safe, and platform management operations
   - Error handling for 401/403/429 status codes

3. **MCP Integration** (`src/cyberark_mcp/mcp_server.py`)
   - FastMCP server implementation
   - 11 exposed tools for CyberArk operations
   - Proper tool parameter validation
   - Windows-compatible encoding handling

### Critical API Integration Notes

- **Base URL**: `https://{subdomain}.privilegecloud.cyberark.cloud/PasswordVault/api`
- **Authentication**: `https://{tenant-id}.id.cyberark.cloud/oauth2/platformtoken`
- **TLD**: Uses `.cloud` not `.com` (common mistake)
- **API Version Policy**: ALWAYS use Gen2 endpoints when available (not Gen1)
- **Response Parsing**: `value` field for arrays (except Platforms API uses `Platforms`)
- **Platform APIs**: Require Privilege Cloud Administrator role membership

## Available MCP Tools

| Tool | Purpose | Parameters | Returns |
|------|---------|------------|---------|
| `health_check` | Verify connectivity | None | Health status with safe count |
| `list_safes` | List accessible safes with pagination | `search`, `offset`, `limit`, `sort`, `include_accounts`, `extended_details` (all optional) | Array of safe objects (excludes Internal Safes) |
| `list_accounts` | List accounts | `safe_name`, `username`, `address` (all optional) | Array of account objects |
| `search_accounts` | Advanced account search | `keywords`, `safe_name`, `username`, `address`, `platform_id` (all optional) | Array of matching accounts |
| `get_account_details` | Get specific account info | `account_id` (required) | Detailed account object |
| `create_account` | Create new privileged account | `platform_id`, `safe_name` (required); `name`, `address`, `user_name`, `secret`, `secret_type`, `platform_account_properties`, `secret_management`, `remote_machines_access` (optional) | Created account object with ID |
| `get_safe_details` | Get specific safe info with options | `safe_name` (required); `include_accounts`, `use_cache` (optional) | Detailed safe object |
| `list_platforms` | List available platforms | `search`, `active`, `system_type` (all optional) | Array of platform objects |
| `get_platform_details` | Get platform configuration | `platform_id` (required) | Detailed platform object |
| `import_platform_package` | Import platform package | `platform_package_file` (required) | Import result with platform ID |

## Configuration

**Required Environment Variables**:
- `CYBERARK_IDENTITY_TENANT_ID` - Tenant ID (without .id.cyberark.cloud suffix)
- `CYBERARK_CLIENT_ID` - OAuth service account username  
- `CYBERARK_CLIENT_SECRET` - Service account password
- `CYBERARK_SUBDOMAIN` - Subdomain (without .privilegecloud.cyberark.cloud suffix)

*See README.md for complete configuration details*

## Development Patterns

### Test-Driven Development (TDD)
1. Write failing tests first
2. Implement minimal code to pass tests  
3. Refactor while maintaining green tests
4. Comprehensive test coverage with mocked external dependencies

### Modern Development Workflow
1. **Use `uv` for dependency management**: `uv run pytest` for testing
2. **Standardized execution**: `uv run mcp-privilege-cloud` for development
3. **Production deployment**: `uvx mcp-privilege-cloud` for end users
4. **Module testing**: `python -m cyberark_mcp` for compatibility verification

### Error Handling Strategy
- **401 Errors**: Automatic token refresh and retry
- **403 Errors**: Clear error messages with guidance
- **429 Errors**: Basic rate limiting (exponential backoff pending)
- **Network Errors**: Comprehensive logging and user-friendly messages

### Security Practices
- Never log sensitive information (tokens, passwords)
- Environment variable-based configuration only
- OAuth token caching with automatic refresh
- Secure .gitignore patterns

### Entry Points

#### Standardized Execution Methods (Recommended)
- **`uvx mcp-privilege-cloud`** - Primary production execution method
- **`uv run mcp-privilege-cloud`** - Development execution with dependency management
- **`python -m cyberark_mcp`** - Standard Python module execution

#### Legacy Entry Points (Deprecated)
- **`run_server.py`** - Legacy multiplatform entry point (deprecated)
- **`python src/cyberark_mcp/mcp_server.py`** - Legacy direct execution (deprecated)

## Testing Strategy

**Test Files**: 124+ total tests across 4 test files
- `tests/test_core_functionality.py` - Authentication, server core, platform management (64+ tests)
- `tests/test_account_operations.py` - Account lifecycle management (35+ tests)  
- `tests/test_mcp_integration.py` - MCP tool wrappers and integration (15+ tests)
- `tests/test_integration.py` - End-to-end integration tests (10+ tests)

**Key Commands**: 
- Modern: `uv run pytest`, `uv run pytest --cov=src/cyberark_mcp`, `uv run pytest -m integration`
- Legacy: `pytest`, `pytest --cov=src/cyberark_mcp`, `pytest -m integration`

*See TESTING.md for comprehensive testing documentation*

## Current Limitations

1. **No password retrieval** - API supports it but not implemented for security
2. **No account modification/deletion** - Create and read operations only  
3. **Basic rate limiting** - Could be enhanced with exponential backoff
4. **Single tenant support** - No multi-tenant architecture

## Integration Examples

**Claude Desktop**: Connect via `uvx mcp-privilege-cloud` (recommended) or `python /path/to/run_server.py` (legacy)  
**MCP Inspector**: Use `npx @modelcontextprotocol/inspector`

*See README.md for complete integration configuration*

## Next Development Priorities

### 🔥 **Immediate Priority**
1. **Password Management Tools** - Highest business value
   - `get_password`, `change_password`, `verify_password`
   - **API Endpoints**: `POST /PasswordVault/API/Accounts/{accountId}/Password/Retrieve`
   - **Security**: Additional authentication, audit logging, secure token handling

2. **~~Advanced Account Operations~~ ✅ PARTIALLY COMPLETED**
   - ~~`create_account`~~ ✅ **IMPLEMENTED**
   - `update_account`, `delete_account` (pending)
   - **API Endpoints**: `PATCH /PasswordVault/API/Accounts/{accountId}`, `DELETE`

### 🚀 **Medium Priority**  
3. **Enhanced Safe Management** - Complete safe lifecycle
   - `create_safe`, `update_safe`, `list_safe_members`
   - **API Endpoints**: `POST /PasswordVault/API/Safes`, `PUT /PasswordVault/API/Safes/{safeName}`

4. **Session Management** - Monitoring and compliance
   - `list_sessions`, `terminate_session`, `get_session_recordings`
   - **API Endpoints**: `GET /PasswordVault/API/LiveSessions`

### 🔧 **Key Implementation Patterns**

1. **API Response Parsing** - Handle inconsistent field names (`value` vs `Platforms`)
2. **Test-First Development** - TDD with comprehensive unit/integration tests
3. **Security Implementation** - Enhanced security for password operations
4. **Error Handling** - Robust error management for production use

## References

- **README.md** - Complete setup and configuration documentation
- **TESTING.md** - Comprehensive testing guidelines and commands  
- **TROUBLESHOOTING.md** - Detailed troubleshooting guide and debugging commands
- **SERVER_CAPABILITIES.md** - Complete tool specifications and examples
- **INSTRUCTIONS.md** - Development workflow and coding standards

---

*This document provides essential AI assistant context for continued development of the CyberArk MCP Server.*