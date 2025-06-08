# CyberArk Privilege Cloud MCP Server - Development Context

This document provides comprehensive context for Claude and other AI assistants to facilitate continued development of the CyberArk Privilege Cloud MCP Server.

## Project Overview

**Purpose**: A Model Context Protocol (MCP) server that integrates with CyberArk Privilege Cloud, enabling AI assistants and other MCP clients to securely interact with privileged account management capabilities.

**Current Status**: ✅ MVP Complete - Production ready with full functionality
**Last Updated**: June 8, 2025

## Architecture Overview

### Core Components

1. **Authentication Module** (`src/cyberark_mcp/auth.py`)
   - OAuth 2.0 client credentials flow
   - Automatic token refresh (15-minute expiration with 60-second safety margin)
   - Secure credential management via environment variables
   - Comprehensive error handling and retry logic

2. **Server Module** (`src/cyberark_mcp/server.py`) 
   - Core CyberArk API integration
   - HTTP client with proper authentication headers
   - Rate limiting and network error handling
   - Account and safe management operations

3. **MCP Integration** (`src/cyberark_mcp/mcp_server.py`)
   - FastMCP server implementation
   - 6 exposed tools for CyberArk operations
   - Proper tool parameter validation
   - Windows-compatible encoding handling

### API Integration Details

**Base URL Pattern**: `https://{subdomain}.privilegecloud.cyberark.cloud/PasswordVault/api`
**Authentication**: `https://{tenant-id}.id.cyberark.cloud/oauth2/platformtoken`

**Key Implementation Notes**:
- Uses `.cloud` TLD, not `.com` (common mistake)
- Token management requires automatic refresh due to 15-minute expiration
- API responses use `value` field for array results
- Proper error handling for 401 (auth), 403 (permissions), 429 (rate limiting)

## Available MCP Tools

| Tool | Purpose | Parameters | Returns |
|------|---------|------------|---------|
| `health_check` | Verify connectivity | None | Health status with safe count |
| `list_safes` | List accessible safes | `search` (optional) | Array of safe objects |
| `list_accounts` | List accounts | `safe_name`, `username`, `address` (all optional) | Array of account objects |
| `search_accounts` | Advanced account search | `keywords`, `safe_name`, `username`, `address`, `platform_id` (all optional) | Array of matching accounts |
| `get_account_details` | Get specific account info | `account_id` (required) | Detailed account object |
| `get_safe_details` | Get specific safe info | `safe_name` (required) | Detailed safe object |

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

1. **`run_server.py`** - Main cross-platform entry point
2. **`run_server_windows.py`** - Windows-specific with encoding fixes
3. **`run_server.bat`** - Windows batch file for easy execution

## Testing Strategy

### Test Structure
- `tests/test_auth.py` - Authentication and token management (20+ tests)
- `tests/test_server.py` - Core server functionality (25+ tests) 
- `tests/test_account_mgmt.py` - Account operations (20+ tests)
- `tests/test_integration.py` - End-to-end integration (10+ tests)

### Running Tests
```bash
pytest                    # All tests
pytest -m auth           # Authentication tests only
pytest -m integration    # Integration tests only
pytest --cov=src/cyberark_mcp  # With coverage
```

## Known Issues and Limitations

### Current Limitations
1. **No password retrieval** - API supports it but not implemented for security
2. **No account creation/modification** - Read-only operations only
3. **Basic rate limiting** - Could be enhanced with exponential backoff
4. **Single tenant support** - No multi-tenant architecture

### Windows-Specific Issues (Resolved)
- Unicode encoding errors with console output (fixed in run_server_windows.py)
- FastMCP context passing issues (resolved by removing lifespan context)

## Future Enhancement Opportunities

### High Priority
1. **Password Management Tools**
   - `get_password` - Retrieve account passwords (requires additional security considerations)
   - `change_password` - Initiate password changes
   - `verify_password` - Check password compliance

2. **Advanced Account Operations**
   - `create_account` - Add new privileged accounts
   - `update_account` - Modify account properties
   - `delete_account` - Remove accounts from safes

### Medium Priority
1. **Session Management**
   - `list_sessions` - View active privileged sessions
   - `terminate_session` - End active sessions
   - `get_session_recordings` - Access session recordings

2. **Platform Management**
   - `list_platforms` - Get available account platforms
   - `get_platform_details` - View platform configurations

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
      "args": ["C:/path/to/run_server_windows.py"],
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
# Connect with command: python /path/to/run_server.py
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
   - Use `run_server_windows.py` instead of `run_server.py`
   - Set PYTHONIOENCODING=utf-8 environment variable

### Debugging Commands
```bash
# Test configuration
python -c "from src.cyberark_mcp.server import CyberArkMCPServer; import asyncio; server = CyberArkMCPServer.from_environment(); print(asyncio.run(server.health_check()))"

# Verify MCP server loads
python -c "from src.cyberark_mcp.mcp_server import mcp; print('MCP server loaded:', mcp.name)"

# Test authentication only
python -c "from src.cyberark_mcp.auth import CyberArkAuthenticator; import asyncio; auth = CyberArkAuthenticator.from_environment(); print(asyncio.run(auth.get_auth_header()))"
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
1. Run full test suite
2. Test with MCP Inspector
3. Validate Claude Desktop integration
4. Update version numbers and documentation
5. Create git tag and release notes

This CLAUDE.md provides comprehensive context for any AI assistant to understand the project structure, implementation details, and development patterns to facilitate continued development of the CyberArk MCP Server.