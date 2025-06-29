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

- Python 3.8 or higher
- Git
- CyberArk Privilege Cloud tenant (for integration testing)
- CyberArk Identity service account

### Installation

1. **Clone and setup environment**:
   ```bash
   git clone <repository-url>
   cd mcp-privilege-cloud
   
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   # Copy example configuration
   cp .env.example .env
   
   # Edit .env with your CyberArk credentials
   # Required variables:
   # CYBERARK_IDENTITY_TENANT_ID=your-tenant-id
   # CYBERARK_CLIENT_ID=your-service-account-username
   # CYBERARK_CLIENT_SECRET=your-service-account-password
   # CYBERARK_SUBDOMAIN=your-subdomain
   ```

3. **Verify setup**:
   ```bash
   # Test basic functionality
   python -c "
   from src.cyberark_mcp.server import CyberArkMCPServer
   import asyncio
   server = CyberArkMCPServer.from_environment()
   health = asyncio.run(server.health_check())
   print('Health:', health['status'])
   "
   
   # Run tests
   pytest
   ```

### Development Tools

The project includes several entry points for development:

- **`run_server.py`** - Multiplatform MCP server launcher
- **`debug_platform_api.py`** - Platform API debugging script
- **`test_mvp.py`** - MVP functionality verification

## Architecture Overview

### Core Components

The project follows a layered architecture with clear separation of concerns:

```
src/cyberark_mcp/
├── auth.py          # OAuth 2.0 authentication module
├── server.py        # Core CyberArk API integration
└── mcp_server.py    # MCP protocol implementation
```

#### 1. Authentication Module (`auth.py`)
- **OAuth 2.0 Client Credentials Flow**: Secure token-based authentication
- **Automatic Token Refresh**: 15-minute expiration with 60-second safety margin
- **Concurrent Request Handling**: Double-checked locking pattern
- **Error Recovery**: Comprehensive retry logic for auth failures

#### 2. Server Module (`server.py`)
- **CyberArk API Integration**: Core business logic for account/safe/platform operations
- **HTTP Client Management**: Proper authentication headers and timeout handling
- **Response Processing**: Handles API inconsistencies (value vs Platforms fields)
- **Error Handling**: Network, permission, and rate limiting scenarios

#### 3. MCP Integration (`mcp_server.py`)
- **FastMCP Server**: MCP protocol implementation
- **Tool Definitions**: 10 exposed tools for CyberArk operations
- **Parameter Validation**: Input validation and type checking
- **Cross-Platform Support**: Windows encoding compatibility

### API Integration Details

**Base URLs**:
- **API Base**: `https://{subdomain}.privilegecloud.cyberark.cloud/PasswordVault/api`
- **Authentication**: `https://{tenant-id}.id.cyberark.cloud/oauth2/platformtoken`

**Key Implementation Notes**:
- Uses `.cloud` TLD (not `.com`)
- Always use Gen2 API endpoints when available
- Handle inconsistent response formats across endpoints
- Implement proper URL encoding for special characters
- Follow principle of least privilege for service accounts

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
   # src/cyberark_mcp/server.py
   def new_functionality(self):
       # Minimal implementation to pass test
       pass
   ```

3. **Refactor and Enhance**:
   ```bash
   # Run tests to ensure green state
   pytest tests/test_new_feature.py
   
   # Refactor while maintaining passing tests
   pytest --cov=src/cyberark_mcp
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

### Adding New Tools

Follow this systematic approach:

1. **Define Tool Specification**:
   - Document in `docs/development/SERVER_CAPABILITIES.md`
   - Define parameters, return types, and behavior

2. **Write Comprehensive Tests** (TDD):
   ```python
   # tests/test_new_tool.py
   @pytest.mark.asyncio
   async def test_new_tool_success(mock_server):
       result = await mock_server.new_tool(param1="value")
       assert result["status"] == "success"
   
   @pytest.mark.asyncio  
   async def test_new_tool_error_handling(mock_server):
       with pytest.raises(CyberArkAPIError):
           await mock_server.new_tool(invalid_param="bad")
   ```

3. **Implement Server Method**:
   ```python
   # src/cyberark_mcp/server.py
   async def new_tool(self, param1: str) -> Dict[str, Any]:
       """Tool description with type hints and docstring."""
       # Implementation
   ```

4. **Add MCP Tool Wrapper**:
   ```python
   # src/cyberark_mcp/mcp_server.py
   @mcp.tool()
   async def new_tool(param1: str) -> Dict[str, Any]:
       """MCP tool wrapper with parameter validation."""
       server = CyberArkMCPServer.from_environment()
       return await server.new_tool(param1)
   ```

5. **Test Integration**:
   ```bash
   # Test with MCP Inspector
   python run_server.py
   # Connect Inspector and validate tool functionality
   ```

## Code Quality Standards

### Style Guidelines

- **PEP 8 Compliance**: Follow Python style guide
- **Type Hints**: Required for all function parameters and returns
- **Documentation**: Comprehensive docstrings for all public methods
- **Line Length**: Maximum 100 characters
- **Naming Conventions**: Meaningful, descriptive names

```python
# Example of proper style
async def list_accounts(
    self, 
    safe_name: Optional[str] = None,
    username: Optional[str] = None,
    address: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    List accounts from CyberArk Privilege Cloud with optional filters.
    
    Args:
        safe_name: Optional safe name filter
        username: Optional username filter  
        address: Optional address filter
        
    Returns:
        List of account dictionaries
        
    Raises:
        CyberArkAPIError: On API communication errors
        AuthenticationError: On authentication failures
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
├── test_core_functionality.py    # Auth, server core, platforms (64+ tests)
├── test_account_operations.py    # Account lifecycle (35+ tests)  
├── test_mcp_integration.py       # MCP tool wrappers (15+ tests)
└── test_integration.py           # End-to-end tests (10+ tests)
```

### Running Tests

```bash
# All tests (124+ total)
pytest

# Specific test categories
pytest tests/test_core_functionality.py    # Core functionality
pytest tests/test_account_operations.py    # Account operations
pytest tests/test_mcp_integration.py       # MCP integration

# By markers
pytest -m auth          # Authentication tests
pytest -m integration   # Integration tests only
pytest -k platform      # Platform management tests
pytest -k safe          # Safe management tests

# With coverage
pytest --cov=src/cyberark_mcp

# Verbose output with detailed failures
pytest -v --tb=short
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
        await mock_server.list_accounts()
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
   pytest --cov=src/cyberark_mcp
   
   # Check style compliance
   flake8 src/
   
   # Verify MCP integration
   python run_server.py  # Test with Inspector
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
python --version
which python
pip list | grep mcp

# Recreate virtual environment if needed
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Import Errors
```bash
# Verify project structure
ls -la src/cyberark_mcp/
python -c "import sys; print(sys.path)"

# Test imports directly
python -c "from src.cyberark_mcp.server import CyberArkMCPServer"
```

### API Integration Issues

#### Authentication Problems
```bash
# Test authentication separately
python -c "
from src.cyberark_mcp.auth import CyberArkAuthenticator
import asyncio
auth = CyberArkAuthenticator.from_environment()
result = asyncio.run(auth.get_auth_header())
print('Auth header obtained:', bool(result))
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

### MCP Inspector Issues

#### Connection Problems
```bash
# Start server with debug logging
export CYBERARK_LOG_LEVEL=DEBUG
python run_server.py

# Test with different connection methods
python src/cyberark_mcp/mcp_server.py  # Direct execution
```

#### Tool Validation
```bash
# Verify tool definitions
python -c "
from src.cyberark_mcp.mcp_server import mcp
print('Available tools:')
for tool in mcp.list_tools():
    print(f'- {tool.name}')
"
```

### Performance Issues

#### Slow API Responses
```bash
# Enable debug timing
export CYBERARK_LOG_LEVEL=DEBUG
export CYBERARK_API_TIMEOUT=60

# Test with minimal operations
python -c "
import time, asyncio
from src.cyberark_mcp.server import CyberArkMCPServer
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
python -c "
import os, sys
from src.cyberark_mcp.server import CyberArkMCPServer
print('Python:', sys.version)
print('Environment variables set:', bool(os.getenv('CYBERARK_CLIENT_ID')))
try:
    server = CyberArkMCPServer.from_environment()
    print('Server initialized successfully')
except Exception as e:
    print('Server initialization failed:', e)
"

# MCP server validation
python -c "
from src.cyberark_mcp.mcp_server import mcp
print(f'MCP server: {mcp.name}')
print(f'Tools available: {len(list(mcp.list_tools()))}')
"

# Platform management debug
python debug_platform_api.py
```

For additional support, review the [project documentation](docs/development/) or create an issue with detailed error information and environment details.