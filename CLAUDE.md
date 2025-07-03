# CyberArk Privilege Cloud MCP Server - Development Context

This document provides essential context for AI assistants developing the CyberArk Privilege Cloud MCP Server.

## Project Overview

**Purpose**: MCP server for CyberArk Privilege Cloud integration, enabling AI assistants to securely manage privileged accounts.

**Current Status**: ✅ **PLATFORM ENHANCEMENT COMPLETE** - Production ready with comprehensive platform management, concurrent optimization, and performance testing  
**Last Updated**: July 2, 2025  
**Recent Enhancement**: Concurrent platform fetching optimization with 3-5x performance improvement, enhanced platform data combination logic with comprehensive Policy INI integration, data type conversion, and graceful fallback handling

## Architecture Overview

### Core Components

1. **Authentication Module** (`src/mcp_privilege_cloud/auth.py`)
   - OAuth 2.0 client credentials flow with 15-minute token expiration
   - Automatic token refresh with double-checked locking
   - Environment variable-based credential management

2. **Server Module** (`src/mcp_privilege_cloud/server.py`)
   - CyberArk API integration with authentication headers
   - Account, safe, and platform management operations
   - Error handling for 401/403/429 status codes

3. **MCP Integration** (`src/mcp_privilege_cloud/mcp_server.py`)
   - FastMCP server implementation
   - 7 exposed action tools for CyberArk operations
   - Proper tool parameter validation
   - Windows-compatible encoding handling

### Critical API Integration Notes

- **Base URL**: `https://{subdomain}.privilegecloud.cyberark.cloud/PasswordVault/api`
- **Authentication**: `https://{tenant-id}.id.cyberark.cloud/oauth2/platformtoken`
- **TLD**: Uses `.cloud` not `.com` (common mistake)
- **API Version Policy**: ALWAYS use Gen2 endpoints when available (not Gen1)
- **Response Parsing**: `value` field for arrays (except Platforms API uses `Platforms`)
- **Platform APIs**: Require Privilege Cloud Administrator role membership
- **Data Integrity**: All API responses preserved exactly - no field name or value transformations applied

## Available MCP Tools (Actions Only)

| Tool | Purpose | Parameters | Returns |
|------|---------|------------|---------|

| `create_account` | Create new privileged account | `platform_id`, `safe_name` (required); `name`, `address`, `user_name`, `secret`, `secret_type`, `platform_account_properties`, `secret_management`, `remote_machines_access` (optional) | Created account object with ID |
| `change_account_password` | Change password for an account | `account_id` (required); `new_password` (optional) | Operation result |
| `set_next_password` | Set the next password for an account | `account_id`, `password` (required) | Operation result |
| `verify_account_password` | Verify the current password for an account | `account_id` (required) | Verification result |
| `reconcile_account_password` | Reconcile account password with target system | `account_id` (required) | Reconciliation result |

| `get_platform_details` | Get comprehensive platform configuration from Policy INI file | `platform_id` (required) | Complete platform configuration with 66+ detailed settings including credentials management policy, session management, workflows, and connection components |
| `import_platform_package` | Import platform package | `platform_package_file` (required) | Import result with platform ID |

## Enhanced Platform Data Combination

### Platform Information Integration

The server now provides **`get_complete_platform_info(platform_id)`** method that intelligently combines data from two CyberArk APIs:

1. **Get Platforms List API** - Basic platform information (id, name, systemType, active, etc.)
2. **Get Platform Details API** - Comprehensive Policy INI configuration (66+ detailed settings)

### Key Features

#### Data Combination Logic
- **Zero Field Overlap Handling**: APIs return completely different data structures
- **Intelligent Merging**: Combines nested platform sections (general, properties, credentialsManagement)
- **Field Deduplication**: List API values take precedence for overlapping fields
- **Graceful Degradation**: Falls back to basic info if details API fails

#### Raw Data Preservation
- **No Field Name Conversion**: Original CamelCase field names preserved (e.g., `PSMServerID`, `PolicyType`)
- **No Value Transformation**: All values preserved exactly as returned by API (`"Yes"` stays `"Yes"`, `"12"` stays `"12"`)
- **Complete Data Integrity**: Empty/null values, special characters, and all original formatting preserved
- **API Response Fidelity**: Zero modification of CyberArk API responses

#### Enhanced Platform Structure
```json
{
  "id": "WinServerLocal",
  "name": "Windows Server Local",
  "systemType": "Windows", 
  "active": true,                    // From list API (original boolean)
  "platformType": "Regular",
  "description": "Windows Server Local Accounts",
  
  // Detailed Policy INI configuration (from details API) - RAW VALUES
  "PasswordLength": "12",            // Preserved as string from API
  "ResetOveridesMinValidity": "Yes", // Preserved as string from API
  "XMLFile": "Yes",                  // Preserved as string from API
  "FromHour": "-1",                  // Preserved as string from API
  "PSMServerID": "PSMServer_abc123", // Original CamelCase field name
  "PolicyType": "Regular",           // Original CamelCase field name
  "platformBaseID": "WinDomain"      // Original CamelCase field name
}
```

#### Error Handling
- **404 Platform Not Found**: Clear error message with platform ID
- **403 Access Denied**: Graceful degradation to basic platform info
- **API Failures**: Automatic fallback to list API data only
- **Comprehensive Logging**: Debug information for troubleshooting

### Usage Examples

```python
# Get complete platform information with automatic data combination
server = CyberArkMCPServer.from_environment()
platform_info = await server.get_complete_platform_info("WinServerLocal")

# Access basic info (from list API)
print(platform_info["name"])        # "Windows Server Local"
print(platform_info["active"])      # True (original boolean from API)

# Access detailed policy info (from details API) - RAW VALUES
print(platform_info["PasswordLength"])         # "12" (preserved as string)
print(platform_info["ResetOveridesMinValidity"]) # "Yes" (preserved as string)
print(platform_info["PSMServerID"])              # "PSMServer_abc123" (original CamelCase)

# Graceful handling when details unavailable
basic_info = await server.get_complete_platform_info("RestrictedPlatform")
# Returns basic platform info without detailed policies
```

## Concurrent Platform Fetching

### Performance Optimization for Platform Lists

The server now provides **`list_platforms_with_details(**kwargs)`** method that optimizes platform data retrieval through concurrent API calls:

#### Key Features
- **Concurrent API Calls**: Fetches detailed platform information in parallel using `asyncio.gather()`
- **Rate Limiting Protection**: Limits concurrent requests to 10 to avoid API rate limits
- **Graceful Failure Handling**: Skips platforms that fail detailed info retrieval
- **Parameter Pass-through**: Supports all `list_platforms()` parameters (search, filter, etc.)
- **Performance Gains**: Typically 3-5x faster than sequential API calls

#### Usage Example
```python
# Get all platforms with complete details (concurrent)
platforms = await server.list_platforms_with_details()

# With filtering/search parameters
windows_platforms = await server.list_platforms_with_details(search="Windows")
active_platforms = await server.list_platforms_with_details(filter="Active eq true")
```

#### Performance Characteristics

**Baseline Performance Metrics** (from comprehensive performance testing):

- **125 Platform Test**: 1.34s total time (10.7ms avg/platform) with 9.3x concurrency improvement
- **Scalability**: Linear scaling maintained up to 100+ platforms
- **Memory Usage**: 0.19 MB peak for 100 enhanced platforms (0.002 MB/platform)
- **Enhanced vs Basic**: 10.9x overhead ratio (acceptable for detailed information retrieval)
- **Error Handling**: 20% failure rate adds <0.3s overhead with graceful degradation

**Technical Implementation**:
- **Concurrency Limit**: 10 concurrent requests (configurable via semaphore)
- **Batch Processing**: Automatically handles large platform lists (tested up to 125 platforms)
- **Failure Isolation**: Individual platform failures don't affect overall operation
- **Memory Optimization**: Enhanced platform objects are 4.9x larger but <3KB each
- **Raw Data Preservation**: No field conversion overhead - original API data structure maintained

#### Error Handling
- **List API Errors**: Propagated immediately (authentication, authorization)
- **Individual Failures**: Platforms with detail fetch failures are skipped
- **Logging**: Comprehensive performance metrics and failure tracking
- **Graceful Degradation**: Returns successful platforms even if some fail

## Available MCP Resources (Read Operations)

| Resource | Purpose | URI Pattern | Description |
|----------|---------|-------------|-------------|
| **Accounts** | List and search accounts | `cyberark://accounts/` | All accessible accounts across safes |
| **Account Search** | Advanced account search | `cyberark://accounts/search?query=...` | Search with filters and keywords |
| **Safes** | List accessible safes | `cyberark://safes/` | All safes with pagination support |
| **Platforms** | List available platforms | `cyberark://platforms/` | Platform definitions with raw API data preserved exactly |

*Resources provide read-only access via URIs with complete API data fidelity - no transformations applied*

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
4. **Module testing**: `python -m mcp_privilege_cloud` for compatibility verification

### Error Handling Strategy ✅ ENHANCED (Task A4)
- **401 Errors**: Automatic token refresh and retry
- **403 Errors**: Enhanced error messages with specific role requirements and troubleshooting guidance
- **404 Errors**: Platform-specific error messages with suggested resolution steps
- **429 Errors**: Rate limiting detection with retry recommendations and concurrency guidance
- **Network Errors**: Comprehensive logging and user-friendly messages
- **Input Validation**: Enhanced validation with sanitized logging for security
- **Graceful Degradation**: Robust fallback to basic platform info when details API fails
- **Concurrent Operations**: Individual failure handling without affecting batch operations
- **Troubleshooting**: Comprehensive error categorization and debug logging

### Security Practices
- Never log sensitive information (tokens, passwords)
- Environment variable-based configuration only
- OAuth token caching with automatic refresh
- Secure .gitignore patterns

### Entry Points

#### Standardized Execution Methods (Recommended)
- **`uvx mcp-privilege-cloud`** - Primary production execution method
- **`uv run mcp-privilege-cloud`** - Development execution with dependency management
- **`python -m mcp_privilege_cloud`** - Standard Python module execution

#### Legacy Entry Points (Deprecated)
- **`run_server.py`** - Legacy multiplatform entry point (deprecated)
- **`python src/mcp_privilege_cloud/mcp_server.py`** - Legacy direct execution (deprecated)

## Testing Strategy

**Test Files**: 267+ total tests across 6 test files
- `tests/test_core_functionality.py` - Authentication, server core, platform management (88+ tests including Task A4 error handling)
- `tests/test_account_operations.py` - Account lifecycle management (85+ tests)  
- `tests/test_mcp_integration.py` - MCP tool wrappers and integration (18+ tests)
- `tests/test_integration.py` - End-to-end integration tests (25+ tests including platform enhancement integration)
- `tests/test_resources.py` - MCP resource implementation tests (42+ tests)
- `tests/test_performance.py` - **✅ COMPLETED**: Performance and optimization tests (11+ tests including Task C2)

**Key Commands**: 
- Modern: `uv run pytest`, `uv run pytest --cov=src/mcp_privilege_cloud`, `uv run pytest -m integration`
- Legacy: `pytest`, `pytest --cov=src/mcp_privilege_cloud`, `pytest -m integration`
- Performance: `uv run pytest -m performance`, `uv run pytest -m memory` for performance and memory tests

*See TESTING.md for comprehensive testing documentation*

## Current Limitations

1. **No password retrieval** - API supports it but not implemented for security
2. **No account modification/deletion** - Create and read operations only  
3. **~~Basic rate limiting~~ ✅ ENHANCED** - ~~Could be enhanced with exponential backoff~~ Now includes rate limiting detection, logging, and retry guidance
4. **Single tenant support** - No multi-tenant architecture
5. **Platform Details API Permissions** - Requires Privilege Cloud Administrator role; gracefully degrades to basic platform info when insufficient permissions

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
- **TROUBLESHOOTING.md** - ✅ NEW: Comprehensive troubleshooting guide for platform error scenarios (Task A4)
- **SERVER_CAPABILITIES.md** - Complete tool specifications and examples
- **INSTRUCTIONS.md** - Development workflow and coding standards

---

*This document provides essential AI assistant context for continued development of the CyberArk MCP Server.*