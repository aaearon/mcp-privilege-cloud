# CyberArk Privilege Cloud MCP Server - AI Development Context

**CRITICAL FOR LLM**: This document provides essential development context specifically optimized for AI assistant code development. Read this document completely before making any code changes.

## 🤖 LLM Development Guidelines

**BEFORE CODING**:
1. **Always read this entire CLAUDE.md file first** - Contains critical patterns and constraints
2. **Check current test status** - All changes must maintain 48/48 passing tests
3. **Follow existing patterns** - Simplified architecture patterns are established and documented
4. **Use official SDK** - All CyberArk operations MUST use ark-sdk-python (never direct HTTP)
5. **MANDATORY: Use context7 MCP tools for ALL API documentation** - Before working with any library or API, use context7 MCP server tools to get up-to-date documentation

**CODING CONSTRAINTS**:
- ❌ **Never break existing patterns** - Error handling decorator, tool execution, service initialization
- ❌ **Never add boilerplate** - Simplified architecture eliminates repetitive code
- ❌ **Never bypass SDK** - Direct HTTP requests to CyberArk APIs forbidden
- ❌ **Never use outdated documentation** - Always use context7 MCP tools for current API/library docs
- ✅ **Always preserve test coverage** - Every change verified by existing test suite
- ✅ **Always use type hints** - Maintain existing type annotation patterns
- ✅ **Always follow TDD** - Write failing tests first
- ✅ **MANDATORY: Use context7 MCP tools** - Get up-to-date documentation for ANY library/API before coding

## 📚 **MANDATORY: Context7 Documentation Usage**

**🤖 CRITICAL FOR ALL LLM DEVELOPMENT**: Before working with ANY library or API, you MUST use context7 MCP server tools to get current documentation.

### Required Context7 Usage Patterns

**Before working with ark-sdk-python:**
```
Use context7 MCP tools to get latest ark-sdk-python documentation for:
- ArkPCloudAccountsService methods and parameters
- ArkPCloudSafesService API updates  
- ArkPCloudPlatformsService changes
- Authentication patterns and model classes

Workflow: resolve-library-id → get-library-docs
```

**Before working with FastMCP:**
```
Use context7 MCP tools to get latest FastMCP documentation for:
- @mcp.tool() decorator updates
- Parameter validation patterns
- Response formatting changes
- Error handling best practices

Workflow: resolve-library-id → get-library-docs
```

**Before working with any Python library:**
```
Use context7 MCP tools to get current documentation for:
- asyncio patterns and best practices
- aiohttp client usage
- pytest testing frameworks
- Type hints and annotation updates

Workflow: resolve-library-id → get-library-docs
```

### Context7 MCP Tool Usage for This Project

```
# Use context7 MCP tools to get library documentation
# Access through your MCP client (Claude Desktop, etc.)

Use context7 resolve-library-id and get-library-docs tools:

1. resolve-library-id: "ark-sdk-python" 
   → get-library-docs with resolved ID

2. resolve-library-id: "fastmcp"
   → get-library-docs with resolved ID  

3. resolve-library-id: "pytest"
   → get-library-docs with resolved ID

4. resolve-library-id: "aiohttp"
   → get-library-docs with resolved ID
```

**🚨 WARNING**: Using outdated API documentation can lead to:
- Deprecated method usage
- Incorrect parameter passing
- Security vulnerabilities
- Test failures
- Integration issues

**✅ RULE**: Always use context7 MCP tools FIRST, then code using current patterns.

## Project Overview

**Purpose**: MCP server for CyberArk Privilege Cloud integration, enabling AI assistants to securely manage privileged accounts.

**Current Status**: ✅ **SIMPLIFIED ARCHITECTURE COMPLETE** - Production ready with simplified codebase, official ark-sdk-python integration, 13 MCP tools, and enhanced maintainability  
**Last Updated**: July 26, 2025  
**Recent Enhancement**: Comprehensive code simplification achieving ~27% code reduction (from ~1,365 to ~1,000 lines) while maintaining all functionality. Eliminated redundant patterns, streamlined error handling, and improved maintainability. Built on official ark-sdk-python library with enhanced reliability and enterprise support.

## Architecture

For a complete overview of the system architecture, see [ARCHITECTURE.md](ARCHITECTURE.md).

## Available MCP Tools

The server provides 13 MCP tools for CyberArk operations, built on the official ark-sdk-python library. For detailed specifications, parameters, examples, and integration patterns, see [API Reference](docs/API_REFERENCE.md).

**Tool Categories**:  
- **Data Access Tools**: `list_accounts`, `get_account_details`, `search_accounts`, `list_safes`, `get_safe_details`, `list_platforms`, `get_platform_details`
- **Account Management Tools**: `create_account`, `change_account_password`, `set_next_password`, `verify_account_password`, `reconcile_account_password`
- **Platform Management Tools**: `import_platform_package`

> **SDK Migration**: All tools now use the official ark-sdk-python library for enhanced reliability and enterprise support. Resources have been replaced by tools for better MCP client compatibility. All tools return exact CyberArk API data with no field manipulation.

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
- **Rate Limiting Protection**: Limits concurrent requests to 5 to avoid API rate limits
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
- **Concurrency Limit**: 5 concurrent requests (configurable via semaphore)
- **Batch Processing**: Automatically handles large platform lists (tested up to 125 platforms)
- **Failure Isolation**: Individual platform failures don't affect overall operation
- **Memory Optimization**: Enhanced platform objects are 4.9x larger but <3KB each
- **Raw Data Preservation**: No field conversion overhead - original API data structure maintained

#### Error Handling
- **List API Errors**: Propagated immediately (authentication, authorization)
- **Individual Failures**: Platforms with detail fetch failures are skipped
- **Logging**: Comprehensive performance metrics and failure tracking
- **Graceful Degradation**: Returns successful platforms even if some fail

## Data Access Tools

The server provides comprehensive data access tools for CyberArk operations with complete API data fidelity through the official ark-sdk-python library:

**Account Tools**: `list_accounts()`, `get_account_details()`, `search_accounts()` - Access and search all privileged accounts with SDK-powered reliability
**Safe Tools**: `list_safes()`, `get_safe_details()` - Access all safes with complete details and enhanced error handling  
**Platform Tools**: `list_platforms()`, `get_platform_details()` - Access platform definitions with raw API data preserved exactly

*All tools return exact CyberArk API data with no field manipulation or transformations applied, powered by the official SDK*

## 🏗️ Code Simplification Architecture ✅ **COMPLETED** 

### Comprehensive Refactoring Results

The codebase underwent a systematic simplification process achieving **~27% code reduction** (from ~1,365 to ~1,000 lines) while maintaining 100% functionality and test coverage.

**🤖 FOR LLM**: These patterns are ESTABLISHED ARCHITECTURE. Do not recreate eliminated patterns. Follow the simplified patterns shown below for any new code.

#### Phase 1: Tool Infrastructure Simplification
**1.1: Eliminate Redundant Tool Decorator Pattern** ✅ **COMPLETED**
- **Before**: ~270 lines of boilerplate tool wrapper decorators in `mcp_server.py`
- **After**: Single `execute_tool()` function with consistent parameter passing
- **Result**: Eliminated repetitive code while maintaining identical MCP tool behavior

**1.2: Simplify Service Property Pattern** ✅ **COMPLETED** 
- **Before**: Complex lazy-loaded service properties with nested initialization logic
- **After**: Direct service initialization in constructor with graceful fallback for testing
- **Result**: Simplified service management while preserving SDK integration patterns

#### Phase 2: Core Logic Streamlining
**2.1: Streamline Platform Data Processing** ✅ **COMPLETED**
- **Before**: Complex nested data merging with redundant validation and transformation steps
- **After**: Simplified `_flatten_platform_structure()` and `_merge_platform_data()` methods
- **Result**: Maintained data integrity while reducing processing complexity

**2.2: Consolidate Error Handling Patterns** ✅ **COMPLETED**
- **Before**: ~70+ lines of repetitive try/catch blocks across all SDK methods
- **After**: Centralized `@handle_sdk_errors(operation_name)` decorator
- **Result**: Consistent error logging format with significantly reduced code duplication

#### Architecture Benefits Achieved

**Maintainability Improvements**:
- **Single Point of Control**: Error handling, tool execution, and service management
- **Reduced Duplication**: Eliminated repetitive patterns across multiple methods
- **Enhanced Readability**: Core business logic more prominent without boilerplate
- **Simplified Testing**: Cleaner test patterns with reduced mocking complexity

**Performance & Reliability**:
- **Zero Functional Regression**: All 48 tests passing with identical behavior
- **Preserved SDK Integration**: Official ark-sdk-python patterns maintained
- **Graceful Error Handling**: Centralized error management with consistent logging
- **Backward Compatibility**: No breaking changes to MCP tool interfaces

#### Implementation Patterns

**🤖 MANDATORY PATTERN: Error Handling Decorator**
```python
# USE THIS PATTERN for all new SDK methods - DO NOT create manual try/catch blocks
@handle_sdk_errors("describing the operation")
async def your_new_method(self, param: str, **kwargs) -> Dict[str, Any]:
    # Clean business logic without repetitive error handling
    self._ensure_service_initialized('service_name')  # accounts_service, safes_service, platforms_service
    # SDK operation here
    result = self.service.sdk_method()
    self.logger.info(f"Success message")
    return result.model_dump()  # Always use .model_dump() for SDK responses
```

**🤖 MANDATORY PATTERN: Tool Execution**
```python
# DO NOT create individual tool wrappers - use this pattern in mcp_server.py
@mcp.tool()
async def your_new_tool(param: str) -> Dict[str, Any]:
    """Tool description for MCP clients"""
    return await execute_tool("method_name", param=param)
```

**🤖 FILE STRUCTURE GUIDE**:
- `sdk_auth.py` - Authentication only, no business logic
- `server.py` - Business logic with @handle_sdk_errors decorator
- `mcp_server.py` - MCP tools using execute_tool() function
- `exceptions.py` - Custom exceptions only

### Testing Validation ✅ **VERIFIED**
- **48/48 tests passing** - Zero functionality regression
- **Test Coverage Maintained** - All simplification preserved existing test patterns
- **Integration Tests Updated** - MCP tool parameter passing verified
- **Performance Baseline** - No degradation in execution performance

## Configuration

**Required Environment Variables**:
- `CYBERARK_CLIENT_ID` - OAuth service account username  
- `CYBERARK_CLIENT_SECRET` - Service account password

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
- **`run_server.py`** - Legacy multiplatform entry point (removed in SDK migration)
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

**Claude Desktop**: Connect via `uvx mcp-privilege-cloud` (recommended) with official SDK integration  
**MCP Inspector**: Use `npx @modelcontextprotocol/inspector` for enhanced SDK-powered tool testing

*See README.md for complete integration configuration including SDK migration benefits*

## 🎯 Next Development Priorities (LLM-Optimized)

**🤖 CRITICAL**: Follow exact patterns below for new features. Do NOT recreate eliminated boilerplate.

### 🔥 **Immediate Priority** - Password Management Tools

**Implementation Template**:
```python
# 1. Add to server.py (follow existing create_account pattern):
@handle_sdk_errors("retrieving account password")  
async def get_account_password(self, account_id: str, **kwargs) -> Dict[str, Any]:
    self._ensure_service_initialized('accounts_service')
    # Use SDK: result = self.accounts_service.get_password(account_id=account_id)
    # Add security logging: self.logger.warning(f"Password accessed for account: {account_id}")
    return result.model_dump()

# 2. Add to mcp_server.py (follow existing tool pattern):
@mcp.tool()
async def get_account_password(account_id: str) -> Dict[str, Any]:
    """Retrieve password for specified account - high security operation"""
    return await execute_tool("get_account_password", account_id=account_id)

# 3. Add tests to test_account_operations.py (follow existing patterns)
```

**Required Methods**: `get_password`, `update_account`, `delete_account`  
**API Endpoints**: `POST /PasswordVault/API/Accounts/{accountId}/Password/Retrieve`  
**Security**: Additional authentication, audit logging, secure token handling

### 🚀 **Medium Priority** - Safe/Session Management

**Follow same pattern above** for:
- `create_safe`, `update_safe`, `list_safe_members` 
- `list_sessions`, `terminate_session`, `get_session_recordings`

### 🔧 **LLM Implementation Rules**

1. **STEP 1: Use context7 FIRST** - Get current library documentation before any code changes
2. **NEVER bypass patterns** - Always use @handle_sdk_errors decorator
3. **ALWAYS follow TDD** - Write failing test first, then implementation  
4. **SDK-only operations** - Never create direct HTTP requests
5. **Preserve test coverage** - All 48 tests must continue passing
6. **Use existing models** - Leverage ark-sdk-python model classes

**🔍 Mandatory Context7 Workflow**:
```
# Before implementing any new feature:
1. Use context7 MCP tools to get latest SDK documentation:
   - resolve-library-id: "ark-sdk-python"
   - get-library-docs with the resolved ID
2. Write failing test using current patterns
3. Implement using up-to-date SDK methods  
4. Verify all 48 tests still pass
```

## References

- **README.md** - Complete setup and configuration documentation
- **ARCHITECTURE.md** - System architecture and component details
- **DEVELOPMENT.md** - Development workflows and procedures
- **INSTRUCTIONS.md** - Development workflow and coding standards
- **docs/API_REFERENCE.md** - Complete tool specifications and examples
- **docs/TESTING.md** - Comprehensive testing guidelines and procedures

---

*This document provides essential AI assistant context for continued development of the CyberArk MCP Server.*