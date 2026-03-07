# Development Guide - CyberArk Privilege Cloud MCP Server

This comprehensive guide provides everything developers need to contribute to the CyberArk Privilege Cloud MCP Server project.

## Table of Contents

- [Development Setup](#development-setup)
- [Architecture Overview](#architecture-overview)
- [Development Workflow](#development-workflow)
- [Code Quality Standards](#code-quality-standards)
- [Testing Guide](#testing-guide)
- [Contributing Guidelines](#contributing-guidelines)
- [Troubleshooting](#troubleshooting)

## Development Setup

### Prerequisites

- Python 3.11 or higher
- Git
- CyberArk Privilege Cloud tenant (for integration testing)
- CyberArk Identity service account

### Installation

1. **Clone and setup environment**:
   ```bash
   git clone <repository-url>
   cd mcp-privilege-cloud
   
   # Install dependencies with uv (modern approach)
   uv sync
   ```

2. **Configure environment**:
   ```bash
   # Copy example configuration
   cp .env.example .env
   
   # Edit .env with your CyberArk credentials
   # Required variables:
   # CYBERARK_CLIENT_ID=your-service-account-username
   # CYBERARK_CLIENT_SECRET=your-service-account-password
   ```

3. **Verify setup**:
   ```bash
   # Test basic functionality
   python3 -c "
   from mcp_privilege_cloud.server import CyberArkMCPServer
   import asyncio
   server = CyberArkMCPServer.from_environment()
   health = asyncio.run(server.health_check())
   print('Health:', health['status'])
   "

   # Run tests
   uv run pytest
   ```

### Development Tools

The project includes these entry points for development:

- **`uv run mcp-privilege-cloud`** - Development server execution
- **`python -m mcp_privilege_cloud`** - Standard Python module execution
- **`uvx mcp-privilege-cloud`** - Production execution

## Architecture

For a complete overview of the system architecture, components, and API integration details, see [ARCHITECTURE.md](ARCHITECTURE.md).

## Development Workflow

### Test-Driven Development (TDD)

The project strictly follows TDD principles:

1. **Write Failing Tests First**:
   ```bash
   # Create test for new feature
   # tests/test_new_feature.py
   def test_new_functionality():
       # Test the desired behavior
       assert expected_behavior()
   ```

2. **Implement Minimal Code**:
   ```python
   # src/mcp_privilege_cloud/server.py
   def new_functionality(self):
       # Minimal implementation to pass test
       pass
   ```

3. **Refactor and Enhance**:
   ```bash
   # Run tests to ensure green state
   pytest tests/test_new_feature.py
   
   # Refactor while maintaining passing tests
   pytest --cov=src/mcp_privilege_cloud
   ```

### Git Workflow

Follow the feature branch Git workflow:

1. **Create Feature Branch**:
   ```bash
   git checkout -b feature/new-functionality
   ```

2. **Development Cycle**:
   ```bash
   # Write tests
   # Implement code
   # Run tests
   pytest
   
   # Commit with meaningful messages
   git add .
   git commit -m "feat: add new functionality with comprehensive tests"
   ```

3. **Integration**:
   ```bash
   # Push feature branch
   git push origin feature/new-functionality
   
   # Create pull request for review
   # Automated CI/CD runs all tests
   ```

### Adding New Action Tools

Follow this systematic approach for adding new action tools:

1. **Define Tool Specification**:
   - Document in `docs/API_REFERENCE.md`
   - Define parameters, return types, and behavior

2. **Write Comprehensive Tests** (TDD):
   ```python
   # tests/test_new_tool.py
   @pytest.mark.asyncio
   async def test_new_action_tool_success(mock_server):
       result = await mock_server.new_action_tool(param1="value")
       assert result["status"] == "success"
   
   @pytest.mark.asyncio  
   async def test_new_action_tool_error_handling(mock_server):
       with pytest.raises(CyberArkAPIError):
           await mock_server.new_action_tool(invalid_param="bad")
   ```

3. **Implement Server Method**:
   ```python
   # src/mcp_privilege_cloud/server.py
   async def new_action_tool(self, param1: str) -> Dict[str, Any]:
       """Tool description with type hints and docstring."""
       # Implementation
   ```

4. **Add MCP Tool Wrapper**:
   ```python
   # src/mcp_privilege_cloud/mcp_server.py
   @mcp.tool()
   async def new_action_tool(
       param1: str,
       ctx: Optional[Context[ServerSession, AppContext]] = None
   ) -> Dict[str, Any]:
       """MCP tool wrapper with parameter validation."""
       return await execute_tool("new_action_tool", ctx=ctx, param1=param1)
   ```

## Code Quality Standards

### Style Guidelines

- **PEP 8 Compliance**: Follow Python style guide
- **Type Hints**: Required for all function parameters and returns
- **Documentation**: Comprehensive docstrings for all public methods
- **Line Length**: Maximum 100 characters
- **Naming Conventions**: Meaningful, descriptive names

```python
# Example of proper style for action tools
async def create_account(
    self,
    platform_id: str,
    safe_name: str,
    name: Optional[str] = None,
    address: Optional[str] = None,
    user_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new privileged account in CyberArk Privilege Cloud.
    
    Args:
        platform_id: Platform ID for the account
        safe_name: Safe where account will be stored
        name: Optional account name
        address: Optional target system address
        user_name: Optional username for the account
        
    Returns:
        Dictionary containing created account details with ID
        
    Raises:
        CyberArkAPIError: On API communication errors
        AuthenticationError: On authentication failures
        ValidationError: On invalid input parameters
    """
    # Implementation with proper error handling
```

### Error Handling Strategy

- **Authentication Errors (401)**: Automatic token refresh and retry
- **Permission Errors (403)**: Clear error messages with guidance
- **Rate Limiting (429)**: Graceful degradation (backoff coming soon)
- **Network Errors**: Comprehensive logging and user-friendly messages
- **Input Validation**: Validate all parameters before API calls

### Security Practices

- **Never log sensitive information**: tokens, passwords, secrets
- **Environment variables only**: No hardcoded credentials
- **Secure token caching**: Automatic refresh with proper cleanup
- **Input validation**: Sanitize all user inputs
- **Principle of least privilege**: Minimal required permissions

## Testing Guide

### Test Structure

The test suite is organized into focused categories:

```
tests/
├── conftest.py                      # Shared fixtures
├── test_core_functionality.py       # Auth, server core, platforms
├── test_applications_service.py     # Applications service
├── test_mcp_integration.py          # MCP tool wrappers
├── test_integration_tools.py        # End-to-end integration
├── test_enhanced_error_handling.py  # Error handling validation
├── test_enhanced_error_messages.py  # Error message consistency
├── test_token_verifier.py           # JWT verification
├── test_token_bridge.py             # Token bridge tests
├── test_oauth_integration.py        # OAuth integration
├── test_oauth_metadata.py           # RFC 8414 metadata
├── test_transport.py                # Transport configuration
├── test_env_var_resolution.py       # Env var priority chain
├── test_pcloud_url_resolution.py    # PCloud URL resolution
├── test_context_injection.py        # Context injection
├── test_lifespan.py                 # Lifespan management
├── test_response_models.py          # Response models
└── test_typed_tools.py              # Typed tool validation
```

### Running Tests

```bash
# All tests (292 total)
uv run pytest

# Specific test categories
uv run pytest tests/test_core_functionality.py    # Core functionality
uv run pytest tests/test_mcp_integration.py       # MCP action tools
uv run pytest tests/test_oauth_integration.py     # OAuth integration

# By markers
uv run pytest -m auth          # Authentication tests
uv run pytest -m integration   # Integration tests only
uv run pytest -k platform      # Platform management tests

# With coverage
uv run pytest --cov=src/mcp_privilege_cloud

# Verbose output with detailed failures
uv run pytest -v --tb=short
```

### Test Patterns

#### Async Testing
```python
@pytest.mark.asyncio
async def test_async_operation(mock_server):
    result = await mock_server.some_operation()
    assert result["status"] == "success"
```

#### Mocking External APIs
```python
@pytest.fixture
def mock_cyberark_api(mocker):
    """Mock CyberArk API responses."""
    mock_response = mocker.MagicMock()
    mock_response.json.return_value = {"value": []}
    mock_response.status_code = 200
    return mock_response
```

#### Error Scenario Testing
```python
@pytest.mark.asyncio
async def test_api_error_handling(mock_server, mocker):
    # Mock API error response
    mocker.patch('aiohttp.ClientSession.request', 
                 side_effect=aiohttp.ClientError("Network error"))
    
    with pytest.raises(CyberArkAPIError):
        await mock_server.create_account(platform_id="test", safe_name="test")
```

### Test Coverage Requirements

- **Minimum 80% coverage** for all modules
- **100% coverage** for critical security functions
- **All public methods** must have tests
- **Both success and failure scenarios** covered
- **Performance/timeout testing** for network operations

## Contributing Guidelines

### Pull Request Process

1. **Create Feature Branch**:
   ```bash
   git checkout -b feature/descriptive-name
   ```

2. **Follow TDD Workflow**:
   - Write tests first
   - Implement minimal functionality
   - Refactor while maintaining green tests

3. **Ensure Quality**:
   ```bash
   # Run full test suite
   pytest --cov=src/mcp_privilege_cloud
   
   # Check style compliance
   ruff check src/
   
   # Verify MCP integration
   uv run mcp-privilege-cloud  # Test with Inspector
   ```

4. **Submit Pull Request**:
   - Clear description of changes
   - Reference any related issues
   - Include test results and coverage
   - Document any breaking changes

### Code Review Checklist

- [ ] Tests written before implementation (TDD)
- [ ] All tests passing with good coverage
- [ ] PEP 8 compliance and type hints
- [ ] Comprehensive error handling
- [ ] Security best practices followed
- [ ] Documentation updated
- [ ] MCP Inspector testing completed

### Release Process

1. **Automated Testing**: GitHub Actions runs full test suite
2. **Manual Validation**: Test with MCP Inspector and real CyberArk environment
3. **Documentation Updates**: Version numbers and changelog
4. **Release Creation**: Git tag and release notes
5. **CI/CD Verification**: All checks must pass

## Troubleshooting

### Development Environment Issues

#### Python Environment
```bash
# Check Python version and environment
python3 --version
which python3
uv pip list | grep mcp

# Reinstall dependencies if needed
uv sync
```

#### Import Errors
```bash
# Verify project structure
ls -la src/mcp_privilege_cloud/
python -c "import sys; print(sys.path)"

# Test imports directly
python3 -c "from mcp_privilege_cloud.server import CyberArkMCPServer"
```

### API Integration Issues

#### Authentication Problems
```bash
# Test authentication separately
python3 -c "
from mcp_privilege_cloud.sdk_auth import CyberArkSDKAuthenticator
auth = CyberArkSDKAuthenticator.from_environment()
client = auth.get_authenticated_client()
print('Authenticated:', bool(client))
"
```

#### Network Connectivity
```bash
# Test basic connectivity
curl -I https://your-subdomain.privilegecloud.cyberark.cloud

# Test authentication endpoint
curl -X POST https://your-tenant.id.cyberark.cloud/oauth2/platformtoken \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=test&client_secret=test"
```

### Testing Issues

#### Test Failures
```bash
# Run specific failing test with verbose output
pytest tests/test_specific.py::test_function -v --tb=long

# Check for async issues
pytest tests/test_async.py -v --asyncio-mode=auto

# Clear pytest cache
pytest --cache-clear
```

#### Mock Issues
```bash
# Verify mock setup
pytest tests/test_with_mocks.py -v -s

# Check fixture scoping
pytest --fixtures tests/
```

## MCP Inspector Testing Guide

This section provides comprehensive testing procedures using the MCP Inspector tool, specifically designed for AI assistants and LLMs working with this MCP server.

### Quick Setup for LLMs

When an LLM needs to test this MCP server, follow these standardized procedures:

#### 1. Web Interface Testing (Recommended for Interactive Analysis)

```bash
# Launch MCP Inspector web interface
npx @modelcontextprotocol/inspector
```

**Configuration in Browser:**
- **Server Command**: `uvx --from git+https://github.com/aaearon/mcp-privilege-cloud.git mcp-privilege-cloud`
- **Environment Variables**: Add these two required variables:
  - `CYBERARK_CLIENT_ID`: your-client-id  
  - `CYBERARK_CLIENT_SECRET`: your-secret
- **Expected Result**: Connection shows "53 tools available"

#### 2. Command Line Testing (Recommended for Automation)

**Basic connectivity test:**
```bash
npx @modelcontextprotocol/inspector -e CYBERARK_CLIENT_ID=your-client-id -e CYBERARK_CLIENT_SECRET=your-secret uvx --from git+https://github.com/aaearon/mcp-privilege-cloud.git mcp-privilege-cloud
```

**List available tools (should return 13):**
```bash
npx @modelcontextprotocol/inspector --cli -e CYBERARK_CLIENT_ID=your-client-id -e CYBERARK_CLIENT_SECRET=your-secret uvx --from git+https://github.com/aaearon/mcp-privilege-cloud.git mcp-privilege-cloud --method tools/list
```

**Test specific tool functionality:**
```bash
# Test account listing
npx @modelcontextprotocol/inspector --cli -e CYBERARK_CLIENT_ID=your-client-id -e CYBERARK_CLIENT_SECRET=your-secret uvx --from git+https://github.com/aaearon/mcp-privilege-cloud.git mcp-privilege-cloud --method tools/call --tool-name list_accounts

# Test platform listing  
npx @modelcontextprotocol/inspector --cli -e CYBERARK_CLIENT_ID=your-client-id -e CYBERARK_CLIENT_SECRET=your-secret uvx --from git+https://github.com/aaearon/mcp-privilege-cloud.git mcp-privilege-cloud --method tools/call --tool-name list_platforms
```

### Expected Behavior Patterns

#### Successful Connection Indicators
- ✅ **Tool Count**: `tools/list` returns exactly 53 tools
- ✅ **Resource Count**: `resources/list` returns empty array (correct - server uses tools, not resources)
- ✅ **Authentication**: All tool calls require valid CyberArk credentials
- ✅ **Response Format**: All tools return JSON with exact CyberArk API field names

#### Tool Categories and Testing
```bash
# Data Access Tools (7 tools)
list_accounts, get_account_details, search_accounts
list_safes, get_safe_details  
list_platforms, get_platform_details

# Account Management Tools (5 tools)
create_account, change_account_password, set_next_password
verify_account_password, reconcile_account_password

# Platform Management Tools (1 tool)
import_platform_package
```

### Troubleshooting for LLMs

#### Quick Diagnostic Commands
```bash
# 1. Verify server responds
npx @modelcontextprotocol/inspector --cli [env-vars] uvx --from git+https://github.com/aaearon/mcp-privilege-cloud.git mcp-privilege-cloud --method tools/list

# 2. Test with debug logging
CYBERARK_LOG_LEVEL=DEBUG npx @modelcontextprotocol/inspector [env-vars] uvx --from git+https://github.com/aaearon/mcp-privilege-cloud.git mcp-privilege-cloud

# 3. Check specific tool
npx @modelcontextprotocol/inspector --cli [env-vars] uvx --from git+https://github.com/aaearon/mcp-privilege-cloud.git mcp-privilege-cloud --method tools/call --tool-name health_check
```

#### Common Error Patterns and Solutions

**"No tools listed" or "Connection failed"**
- **Cause**: Environment variables incorrect or missing
- **Solution**: Verify all 4 required environment variables are set correctly
- **Debug**: Check that variable names match exactly (case-sensitive)

**"401 Unauthorized"** 
- **Cause**: Invalid service account credentials
- **Solution**: Verify `CYBERARK_CLIENT_ID` and `CYBERARK_CLIENT_SECRET` in CyberArk Identity
- **Debug**: Test credentials with direct API call

**"403 Forbidden"**
- **Cause**: Service account lacks required safe permissions
- **Solution**: Grant appropriate safe access in CyberArk Privilege Cloud
- **Debug**: Check safe membership for the service account

**"Empty response" or "No data returned"**
- **Cause**: Normal behavior for some tools depending on safe contents
- **Solution**: Not an error - verify with `list_platforms` which should always return data

### Testing Workflow for LLMs

When validating this MCP server, follow this systematic approach:

#### Step 1: Basic Connectivity
```bash
# Verify 13 tools are available
npx @modelcontextprotocol/inspector --cli [env-vars] uvx --from git+https://github.com/aaearon/mcp-privilege-cloud.git mcp-privilege-cloud --method tools/list
```

#### Step 2: Authentication Test  
```bash
# Test with simplest data access tool
npx @modelcontextprotocol/inspector --cli [env-vars] uvx --from git+https://github.com/aaearon/mcp-privilege-cloud.git mcp-privilege-cloud --method tools/call --tool-name list_platforms
```

#### Step 3: Comprehensive Tool Testing
```bash
# Test each tool category
npx @modelcontextprotocol/inspector --cli [env-vars] uvx --from git+https://github.com/aaearon/mcp-privilege-cloud.git mcp-privilege-cloud --method tools/call --tool-name list_safes
npx @modelcontextprotocol/inspector --cli [env-vars] uvx --from git+https://github.com/aaearon/mcp-privilege-cloud.git mcp-privilege-cloud --method tools/call --tool-name list_accounts
```

#### Step 4: Validate Response Structure
- Verify responses contain exact CyberArk API field names (no transformations)
- Check that platform tools return raw Policy INI values ("Yes"/"No", "12", etc.)
- Confirm error responses provide helpful context

### Environment Variable Management

For secure testing, LLMs should use this pattern:

```bash
# Method 1: Inline environment variables (recommended)
npx @modelcontextprotocol/inspector -e VAR1=value1 -e VAR2=value2 [command]

# Method 2: Export then run (alternative)
export CYBERARK_CLIENT_ID=your-client-id
export CYBERARK_CLIENT_SECRET=your-secret  
npx @modelcontextprotocol/inspector uvx --from git+https://github.com/aaearon/mcp-privilege-cloud.git mcp-privilege-cloud
```

### MCP Inspector Issues

#### Connection Problems
```bash
# Start server with debug logging
export CYBERARK_LOG_LEVEL=DEBUG
uvx --from git+https://github.com/aaearon/mcp-privilege-cloud.git mcp-privilege-cloud

# Test with different execution methods
uv run mcp-privilege-cloud  # Development mode
python -m mcp_privilege_cloud  # Module execution
```

#### Tool Validation
```bash
# Verify tool definitions via MCP Inspector
python -c "
from mcp_privilege_cloud.mcp_server import mcp
print(f'MCP server: {mcp.name}')
"
```

### Performance Issues

#### Slow API Responses
```bash
# Enable debug logging
export CYBERARK_LOG_LEVEL=DEBUG

# Test with minimal operations
python3 -c "
import time, asyncio
from mcp_privilege_cloud.server import CyberArkMCPServer
server = CyberArkMCPServer.from_environment()
start = time.time()
health = asyncio.run(server.health_check())
print(f'Health check took: {time.time() - start:.2f}s')
"
```

### Debugging Commands

Quick diagnostic commands for common issues:

```bash
# Complete environment verification
python3 -c "
import os, sys
from mcp_privilege_cloud.server import CyberArkMCPServer
print('Python:', sys.version)
print('Environment variables set:', bool(os.getenv('CYBERARK_CLIENT_ID')))
try:
    server = CyberArkMCPServer.from_environment()
    print('Server initialized successfully')
except Exception as e:
    print('Server initialization failed:', e)
"

# MCP server validation
python3 -c "
from mcp_privilege_cloud.mcp_server import mcp
print(f'MCP server: {mcp.name}')
"
```

For additional support, review the [project documentation](docs/development/) or create an issue with detailed error information and environment details.