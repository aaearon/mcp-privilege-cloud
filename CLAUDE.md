# CyberArk Privilege Cloud MCP Server - Development Context

This document provides comprehensive context for Claude and other AI assistants to facilitate continued development of the CyberArk Privilege Cloud MCP Server.

## Project Overview

**Purpose**: A Model Context Protocol (MCP) server that integrates with CyberArk Privilege Cloud, enabling AI assistants and other MCP clients to securely interact with privileged account management capabilities.

**Current Status**: ✅ MVP+ Complete - Production ready with automated CI/CD pipeline
**Last Updated**: June 9, 2025
**Recent Enhancement**: Enhanced safe management tools with full Gen2 API compliance and comprehensive test coverage

## Architecture Overview

### Core Components

1. **Authentication Module** (`src/cyberark_mcp/auth.py`)
   - OAuth 2.0 client credentials flow
   - Automatic token refresh (15-minute expiration with 60-second safety margin)
   - Double-checked locking pattern for concurrent token requests
   - Secure credential management via environment variables
   - Comprehensive error handling and retry logic

2. **Server Module** (`src/cyberark_mcp/server.py`)
   - Core CyberArk API integration
   - HTTP client with proper authentication headers
   - Rate limiting and network error handling
   - Account, safe, and platform management operations

3. **MCP Integration** (`src/cyberark_mcp/mcp_server.py`)
   - FastMCP server implementation
   - 10 exposed tools for CyberArk operations
   - Proper tool parameter validation
   - Windows-compatible encoding handling

### API Integration Details

**Base URL Pattern**: `https://{subdomain}.privilegecloud.cyberark.cloud/PasswordVault/api`
**Authentication**: `https://{tenant-id}.id.cyberark.cloud/oauth2/platformtoken`

**Key Implementation Notes**:
- Uses `.cloud` TLD, not `.com` (common mistake)
- Token management requires automatic refresh due to 15-minute expiration
- API responses use `value` field for array results, except Platforms API which uses `Platforms` field
- Proper error handling for 401 (auth), 403 (permissions), 429 (rate limiting)
- Platform APIs require Privilege Cloud Administrator role membership
- **API Version Policy**: When CyberArk documentation offers both Gen1 and Gen2 endpoints, ALWAYS use Gen2 endpoints only. Gen1 endpoints are legacy and should be avoided for new implementations.

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

## Configuration

### Required Environment Variables
```bash
CYBERARK_IDENTITY_TENANT_ID=your-tenant-id    # Without .id.cyberark.cloud suffix
CYBERARK_CLIENT_ID=service-account-username    # OAuth service account
CYBERARK_CLIENT_SECRET=service-account-password
CYBERARK_SUBDOMAIN=your-subdomain             # Without .privilegecloud.cyberark.cloud suffix
```

### Optional Environment Variables
```bash
CYBERARK_API_TIMEOUT=30        # API request timeout in seconds
CYBERARK_MAX_RETRIES=3         # Maximum retry attempts
CYBERARK_LOG_LEVEL=INFO        # Logging level
```

## Development Patterns

See @INSTRUCTIONS.md.

### Continuous Integration (CI/CD)
The project includes automated testing infrastructure to ensure code quality:

**GitHub Actions Workflow** (`.github/workflows/test.yml`):
- **Triggers**: Runs on every push to any branch and pull requests to main/develop
- **Environment**: Python 3.13 on Ubuntu latest
- **Test Scope**: All unit tests excluding integration tests (`pytest -m "not integration"`)
- **Features**: Dependency caching, coverage reporting, async test support
- **Purpose**: Catch regressions early and ensure all changes pass tests before merge

**Key CI/CD Benefits**:
- Immediate feedback on test failures for any code changes
- Prevents broken code from being merged into main branch
- Ensures consistent test environment across different development machines
- Validates that new features don't break existing functionality

### Test-Driven Development (TDD)
The project follows strict TDD principles:
1. Write failing tests first
2. Implement minimal code to pass tests
3. Refactor while maintaining green tests
4. Comprehensive test coverage with mocked external dependencies

### Error Handling Strategy
- **Authentication Errors (401)**: Automatic token refresh and retry
- **Permission Errors (403)**: Clear error messages with guidance
- **Rate Limiting (429)**: Exponential backoff (not yet implemented - future enhancement)
- **Network Errors**: Comprehensive logging and user-friendly messages

### Security Practices
- Never log sensitive information (tokens, passwords)
- Environment variable-based configuration only
- Proper .gitignore to prevent credential commits
- OAuth token caching with automatic refresh

## Entry Points

1. **`run_server.py`** - Multiplatform entry point with automatic platform detection

## Testing Strategy

### Test Structure
- `tests/test_core_functionality.py` - Authentication, server core, and platform management (64+ tests)
  - TestAuthentication - Token management and OAuth flow (20+ tests)
  - TestServerCore - Basic server operations and safe management (28+ tests) 
  - TestPlatformManagement - Platform operations and API integration (16+ tests)
- `tests/test_account_operations.py` - Account lifecycle management (35+ tests)
  - Account listing, details, search, and creation operations
  - Comprehensive validation and error handling scenarios
- `tests/test_mcp_integration.py` - MCP tool wrappers and integration (15+ tests)
  - TestMCPAccountTools - Account creation MCP tools (2+ tests)
  - TestMCPPlatformTools - Platform MCP tools integration (5+ tests)
  - TestMCPSafeTools - Safe management MCP tools integration (8+ tests)
- `tests/test_integration.py` - End-to-end integration and system tests (10+ tests)

### Running Tests
```bash
pytest                              # All tests (124+ total)
pytest tests/test_core_functionality.py    # Core functionality tests only
pytest tests/test_account_operations.py    # Account operations tests only
pytest tests/test_mcp_integration.py       # MCP integration tests only
pytest -m integration              # Integration tests only
pytest -k platform                 # Platform management tests only
pytest -k safe                     # Safe management tests only
pytest --cov=src/cyberark_mcp      # With coverage
```

## Known Issues and Limitations

### Current Limitations
1. **No password retrieval** - API supports it but not implemented for security
2. **No account modification/deletion** - Create and read operations only
3. **Basic rate limiting** - Could be enhanced with exponential backoff
4. **Single tenant support** - No multi-tenant architecture

### Windows-Specific Issues (Resolved)
- Unicode encoding errors with console output (handled automatically in run_server.py)
- FastMCP context passing issues (resolved by removing lifespan context)

## Future Enhancement Opportunities

### High Priority
1. **Password Management Tools**
   - `get_password` - Retrieve account passwords (requires additional security considerations)
   - `change_password` - Initiate password changes
   - `verify_password` - Check password compliance

2. **~~Advanced Account Operations~~ ✅ PARTIALLY COMPLETED**
   - ~~`create_account` - Add new privileged accounts~~ ✅ **IMPLEMENTED**
   - `update_account` - Modify account properties
   - `delete_account` - Remove accounts from safes

### Medium Priority
1. **Session Management**
   - `list_sessions` - View active privileged sessions
   - `terminate_session` - End active sessions
   - `get_session_recordings` - Access session recordings

2. **~~Platform Management~~ ✅ COMPLETED**
   - ~~`list_platforms` - Get available account platforms~~ ✅ **IMPLEMENTED**
   - ~~`get_platform_details` - View platform configurations~~ ✅ **IMPLEMENTED**

### Low Priority
1. **Reporting and Analytics**
   - `generate_access_report` - Account access reports
   - `get_compliance_status` - Compliance dashboard data
   - `audit_trail` - Access audit information

2. **Performance Enhancements**
   - Connection pooling for better performance
   - Caching for frequently accessed data
   - Batch operations for multiple accounts

## Integration Examples

### Claude Desktop Configuration
```json
{
  "mcpServers": {
    "cyberark-privilege-cloud": {
      "command": "python",
      "args": ["C:/path/to/run_server.py"],
      "env": {
        "PYTHONIOENCODING": "utf-8",
        "PYTHONLEGACYWINDOWSSTDIO": "1"
      }
    }
  }
}
```

### MCP Inspector Testing
```bash
npx @modelcontextprotocol/inspector
# Connect with command: python /path/to/run_server.py (works on all platforms)
```

## Troubleshooting Guide

### Common Issues

1. **"Missing required environment variables"**
   - Verify .env file exists and has correct format
   - Check environment variable names (no typos)
   - Ensure no trailing spaces in values

2. **"Authentication failed"**
   - Verify service account credentials
   - Check OAuth is enabled for service account in CyberArk Identity
   - Confirm tenant ID format (no .id.cyberark.cloud suffix)

3. **"Network error: No address associated with hostname"**
   - Check subdomain spelling
   - Verify using .cloud TLD, not .com
   - Test network connectivity to CyberArk

4. **Unicode encoding errors on Windows**
   - The multiplatform `run_server.py` handles Windows encoding automatically
   - Set PYTHONIOENCODING=utf-8 environment variable

5. **"Platform management returns 0 platforms"**
   - Verify service account is a member of the Privilege Cloud Administrator role
   - Check that platforms exist in the CyberArk tenant
   - API response parsing was fixed (Platforms field vs platforms field)

### Debugging Commands
```bash
# Test configuration
python -c "from src.cyberark_mcp.server import CyberArkMCPServer; import asyncio; server = CyberArkMCPServer.from_environment(); print(asyncio.run(server.health_check()))"

# Verify MCP server loads
python -c "from src.cyberark_mcp.mcp_server import mcp; print('MCP server loaded:', mcp.name)"

# Test authentication only
python -c "from src.cyberark_mcp.auth import CyberArkAuthenticator; import asyncio; auth = CyberArkAuthenticator.from_environment(); print(asyncio.run(auth.get_auth_header()))"

# Test platform management specifically
python -c "from src.cyberark_mcp.server import CyberArkMCPServer; import asyncio; server = CyberArkMCPServer.from_environment(); platforms = asyncio.run(server.list_platforms()); print(f'Found {len(platforms)} platforms')"

# Debug platform API response structure
python debug_platform_api.py  # Use the debug script for detailed platform analysis
```

## Code Quality Standards

### Style Guidelines
- Follow PEP 8 Python style guide
- Use type hints for all function parameters and returns
- Comprehensive docstrings for all public methods
- Meaningful variable and function names
- Maximum line length: 100 characters

### Error Handling
- Always log errors with appropriate level (ERROR, WARNING, INFO)
- Provide user-friendly error messages
- Include troubleshooting guidance in error messages
- Never expose sensitive information in logs or error messages

### Testing Requirements
- Minimum 80% test coverage
- All public methods must have tests
- Mock external dependencies (CyberArk APIs)
- Test both success and failure scenarios
- Include performance/timeout testing where relevant
- Keep debug scripts for troubleshooting and development use

## Security Considerations

### Credential Management
- Never hardcode credentials or tokens
- Use environment variables exclusively
- Implement secure token caching
- Clear tokens from memory when possible
- Log authentication events but never token values

### API Security
- Always use HTTPS for all communications
- Validate all input parameters
- Implement proper timeout handling
- Follow principle of least privilege for service accounts
- Regular token rotation (handled automatically by CyberArk)

### Deployment Security
- Secure .env file permissions (600 or more restrictive)
- Use secure communication channels for credential distribution
- Implement monitoring for authentication failures
- Regular security updates for dependencies

## Performance Considerations

### Current Performance
- Token caching eliminates redundant authentication requests
- HTTP connection reuse within single operations
- Reasonable timeout settings (30 seconds default)
- Efficient JSON parsing and response handling

### Optimization Opportunities
- Connection pooling for high-volume usage
- Response caching for frequently accessed data
- Batch operation support for multiple accounts
- Asynchronous operation improvements

## Recent Safe Management Enhancements (June 2025)

### Enhanced Safe Management Tools
The safe management functionality has been significantly improved with full Gen2 API compliance:

#### **`list_safes` Tool Enhancements**:
- **Pagination Support**: `offset`, `limit` parameters for handling large safe collections
- **Advanced Sorting**: `sort` parameter ("safeName asc" or "safeName desc")
- **Account Inclusion**: `include_accounts` option to include account lists with each safe
- **Detail Control**: `extended_details` parameter to control response verbosity
- **Search Enhancement**: Improved search functionality with URL encoding support

#### **`get_safe_details` Tool Enhancements**:
- **Account Integration**: `include_accounts` parameter for comprehensive safe information
- **Performance Optimization**: `use_cache` parameter for session-based caching
- **Special Character Support**: Proper URL encoding for safe names with spaces and special characters
- **Query Parameter Support**: Full support for additional API parameters

#### **API Compliance Improvements**:
- **Gen2 Endpoint Usage**: Exclusively uses Gen2 API endpoints as per best practices
- **Response Parsing**: Proper handling of `value`, `count`, and `nextLink` fields
- **Error Handling**: Enhanced error handling for pagination and special characters
- **URL Encoding**: Automatic handling of special characters in safe names

#### **Test Coverage Enhancements**:
- **10 New Server Tests**: Comprehensive unit tests for safe management functionality
- **8 New MCP Integration Tests**: Complete MCP tool wrapper testing
- **Pagination Testing**: Full pagination scenario coverage
- **Error Scenario Testing**: Comprehensive error handling validation
- **Special Character Testing**: URL encoding and special character support

## Development Workflow

### Adding New Tools
1. Define tool specification in SERVER_CAPABILITIES.md
2. Write comprehensive tests first (TDD)
3. Implement server method in `server.py`
4. Add MCP tool wrapper in `mcp_server.py`
5. Update documentation and examples
6. Test with MCP Inspector and Claude Desktop

### Modifying Existing Tools
1. Update tests to reflect new requirements
2. Modify implementation to pass updated tests
3. Update documentation and type hints
4. Verify backward compatibility where possible
5. Test with real CyberArk environment

### Release Process
1. **Automated Testing**: GitHub Actions automatically runs full test suite on push
2. **Manual Validation**: Test with MCP Inspector and Claude Desktop integration
3. **Documentation**: Update version numbers and documentation
4. **Release**: Create git tag and release notes
5. **Verification**: Ensure all CI/CD checks pass before release

## Next Development Priorities

Based on the completed MVP and current enhancement patterns, the following areas are prioritized for future development:

### 🔥 **Immediate Priority (Next Sprint)**
1. **Password Management Tools** - Highest business value
   - `get_password` - Secure password retrieval with additional authentication
   - `change_password` - Password rotation capabilities
   - `verify_password` - Password compliance checking
   - **API Endpoints**: `POST /PasswordVault/API/Accounts/{accountId}/Password/Retrieve`, `POST /PasswordVault/API/Accounts/{accountId}/Change`
   - **Security Considerations**: Requires additional authentication, audit logging, secure token handling

2. **~~Advanced Account Operations~~ ✅ PARTIALLY COMPLETED** - Complete lifecycle management
   - ~~`create_account` - Onboard new privileged accounts~~ ✅ **IMPLEMENTED**
   - `update_account` - Modify account properties and platform assignments
   - `delete_account` - Secure account removal with audit trail
   - **API Endpoints**: ~~`POST /PasswordVault/API/Accounts`~~ ✅ **IMPLEMENTED**, `PATCH /PasswordVault/API/Accounts/{accountId}`, `DELETE /PasswordVault/API/Accounts/{accountId}`

### 🚀 **Medium Priority (Future Sprints)**
3. **Enhanced Safe Management** - Complete safe lifecycle
   - `create_safe` - Create new vaults for account organization
   - `update_safe` - Modify safe permissions and properties
   - `list_safe_members` - View safe member permissions
   - **API Endpoints**: `POST /PasswordVault/API/Safes`, `PUT /PasswordVault/API/Safes/{safeName}`

### 📊 **Lower Priority (Long-term)**
4. **Session Management** - Monitoring and compliance capabilities
   - `list_sessions` - View active PSM sessions
   - `terminate_session` - Emergency session termination
   - `get_session_recordings` - Access to session recordings
   - **API Endpoints**: `GET /PasswordVault/API/LiveSessions`, `POST /PasswordVault/API/LiveSessions/{sessionId}/Terminate`

5. **Reporting and Analytics** - Business intelligence
   - `generate_access_report` - Account access patterns and compliance
   - `get_compliance_status` - Security posture dashboard
   - `audit_trail` - Complete audit information for investigations

### 🔧 **Development Implementation Patterns**

When implementing the next features, follow these established patterns from the platform management implementation:

1. **API Response Parsing** - Be aware of inconsistent field names in CyberArk APIs
   - Accounts/Safes use `value` field for arrays
   - Platforms use `Platforms` field (capital P)
   - Always implement fallback parsing: `response.get("SpecificField", response.get("value", []))`

2. **Test-First Development** - Maintain TDD discipline
   - Create dedicated test files: `tests/test_password_mgmt.py`, `tests/test_session_mgmt.py`
   - Write comprehensive unit tests and MCP integration tests
   - Mock external API calls with realistic response data

3. **Security Implementation** - Enhanced security for sensitive operations
   - Password operations require additional authentication flows
   - Implement secure credential caching with automatic cleanup
   - Never log sensitive data (passwords, session tokens)
   - Use separate security audit logging for privileged operations

4. **Error Handling** - Robust error management for production use
   - Enhanced error messages for permission-denied scenarios
   - Graceful degradation when optional features aren't available
   - Rate limiting awareness for high-frequency operations

This CLAUDE.md provides comprehensive context for any AI assistant to understand the project structure, implementation details, development patterns, and next development priorities to facilitate continued development of the CyberArk MCP Server.