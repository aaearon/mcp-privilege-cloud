# Testing Guide

Comprehensive testing guide for the CyberArk Privilege Cloud MCP Server. This guide consolidates all testing strategies, commands, and procedures for unit tests, integration tests, and MCP Inspector testing.

## Table of Contents

- [Quick Start Testing](#quick-start-testing)
- [Test Structure](#test-structure)
- [Running Tests](#running-tests)
- [MCP Inspector Testing](#mcp-inspector-testing)
- [Test Categories](#test-categories)
- [Testing Strategy](#testing-strategy)
- [Performance Testing](#performance-testing)
- [Debug Testing](#debug-testing)

## Quick Start Testing

### Prerequisites
```bash
# Ensure you're in the project directory
cd /mnt/c/Users/Tim/Projects/mcp-privilege-cloud

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### Basic Test Commands
```bash
# Run all tests (124+ total)
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=src/cyberark_mcp

# Run specific test categories
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m auth          # Authentication tests only
```

## Test Structure

The test suite is organized into specialized test files with comprehensive coverage:

### Core Test Files

#### `tests/test_core_functionality.py` (64+ tests)
**TestAuthentication** - Token management and OAuth flow (20+ tests)
- OAuth 2.0 client credentials flow testing
- Token refresh mechanisms
- Environment variable validation
- Authentication error handling
- Concurrent token request handling

**TestServerCore** - Basic server operations and safe management (28+ tests)
- Health check functionality
- Safe listing with pagination
- Safe details retrieval
- Network error handling
- Response parsing validation

**TestPlatformManagement** - Platform operations and API integration (16+ tests)
- Platform listing with filters
- Platform details retrieval
- Administrator role permission testing
- Gen2 API endpoint compliance

#### `tests/test_account_operations.py` (35+ tests)
- Account listing with various filters
- Account details retrieval
- Advanced account search functionality
- Account creation with full parameter validation
- Error handling for account operations
- Special character handling in account data

#### `tests/test_mcp_integration.py` (15+ tests)
**TestMCPAccountTools** - Account creation MCP tools (2+ tests)
- MCP tool wrapper validation
- Parameter passing and validation

**TestMCPPlatformTools** - Platform MCP tools integration (5+ tests)
- Platform listing MCP wrapper
- Platform details MCP wrapper

**TestMCPSafeTools** - Safe management MCP tools integration (8+ tests)
- Safe listing MCP wrapper with pagination
- Safe details MCP wrapper with options

#### `tests/test_integration.py` (10+ tests)
- End-to-end integration scenarios
- Complete workflow testing
- Cross-component integration validation

### Test Coverage Metrics
- **Total Tests**: 124+ comprehensive test cases
- **Target Coverage**: Minimum 80% code coverage
- **Mock Strategy**: All external CyberArk API dependencies are mocked
- **Test Types**: Unit, integration, and MCP protocol tests

## Running Tests

### Standard Test Execution

#### Run All Tests
```bash
# Complete test suite
pytest

# With detailed output
pytest -v

# With test timings
pytest --durations=10
```

#### Run Specific Test Files
```bash
# Core functionality tests only
pytest tests/test_core_functionality.py

# Account operations tests only
pytest tests/test_account_operations.py

# MCP integration tests only
pytest tests/test_mcp_integration.py

# Integration tests only
pytest tests/test_integration.py
```

#### Run by Test Categories
```bash
# Authentication tests
pytest -m auth

# Unit tests (excludes integration)
pytest -m unit

# Integration tests (requires environment setup)
pytest -m integration

# Platform management tests
pytest -k platform

# Safe management tests
pytest -k safe

# Account management tests
pytest -k account
```

### Coverage Testing
```bash
# Generate coverage report
pytest --cov=src/cyberark_mcp

# Coverage with HTML report
pytest --cov=src/cyberark_mcp --cov-report=html

# Coverage with missing lines
pytest --cov=src/cyberark_mcp --cov-report=term-missing

# Coverage for specific module
pytest --cov=src/cyberark_mcp/auth tests/test_core_functionality.py::TestAuthentication
```

### Parallel Test Execution
```bash
# Install pytest-xdist for parallel execution
pip install pytest-xdist

# Run tests in parallel
pytest -n auto

# Run with specific number of workers
pytest -n 4
```

## MCP Inspector Testing

### Installation and Setup

#### Install MCP Inspector
```bash
# Install globally
npm install -g @modelcontextprotocol/inspector

# Or run directly with npx
npx @modelcontextprotocol/inspector
```

#### Start MCP Server for Testing
```bash
# Recommended: Use multiplatform launcher
python run_server.py

# Alternative: Direct execution
python src/cyberark_mcp/mcp_server.py
```

### Testing Without Credentials

For testing tool structure and validation without real CyberArk credentials:

#### Expected Server Output
```
ERROR - Missing required environment variables: ['CYBERARK_IDENTITY_TENANT_ID', 'CYBERARK_CLIENT_ID', 'CYBERARK_CLIENT_SECRET', 'CYBERARK_SUBDOMAIN']
```
**Note**: This is expected for testing - the server will still start and you can test tool structure.

#### Connect MCP Inspector
1. **Connection Method**: Choose "Local" or "Command"
2. **Command**: Enter the full path:
   ```bash
   python /mnt/c/Users/Tim/Projects/mcp-privilege-cloud/run_server.py
   ```
3. **Click Connect**

#### Verify Available Tools
You should see these 10 tools in the Inspector:
- `health_check`
- `list_accounts`
- `get_account_details`
- `search_accounts`
- `create_account`
- `list_safes`
- `get_safe_details`
- `list_platforms`
- `get_platform_details`

### Parameter Validation Testing

Test tool parameter validation without real API calls:

#### Test Required Parameters
```json
// Should fail - missing required parameter
{
  "tool": "get_account_details",
  "arguments": {}
}

// Should fail - missing required parameter
{
  "tool": "get_safe_details",
  "arguments": {}
}
```

#### Test Optional Parameters
```json
// Should validate successfully
{
  "tool": "list_accounts",
  "arguments": {
    "safe_name": "TestSafe",
    "username": "testuser"
  }
}

// Should validate successfully  
{
  "tool": "list_safes",
  "arguments": {
    "search": "Database",
    "limit": 10
  }
}
```

### Testing With Real Credentials

#### Environment Configuration
Create `.env` file in project root:
```bash
# Required Configuration
CYBERARK_IDENTITY_TENANT_ID=your-tenant-id
CYBERARK_CLIENT_ID=your-service-account-username
CYBERARK_CLIENT_SECRET=your-service-account-password
CYBERARK_SUBDOMAIN=your-privilege-cloud-subdomain

# Optional Configuration
CYBERARK_API_TIMEOUT=30
CYBERARK_MAX_RETRIES=3
CYBERARK_LOG_LEVEL=INFO
```

#### Verify Configuration
Test configuration before MCP Inspector testing:
```bash
python -c "
import asyncio
from src.cyberark_mcp.server import CyberArkMCPServer
server = CyberArkMCPServer.from_environment()
health = asyncio.run(server.health_check())
print('Health Status:', health['status'])
if health['status'] == 'healthy':
    print('✅ Ready for MCP Inspector testing!')
    print(f'Safes accessible: {health.get('safes_accessible', 'Unknown')}')
else:
    print('❌ Configuration issue:', health.get('error', 'Unknown error'))
"
```

#### Restart Server with Credentials
```bash
# Stop current server (Ctrl+C)
# Restart with proper environment
python run_server.py
```

**Expected Output:**
```
INFO - Starting CyberArk Privilege Cloud MCP Server
INFO - CyberArk server connection established successfully
```

### Real API Testing Sequence

#### Test 1: Health Check
```json
{
  "tool": "health_check",
  "arguments": {}
}
```
**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-06-28T...",
  "safes_accessible": 5
}
```

#### Test 2: List Safes
```json
{
  "tool": "list_safes",
  "arguments": {}
}
```

#### Test 3: List Accounts with Filter
```json
{
  "tool": "list_accounts",
  "arguments": {
    "safe_name": "YourSafeName"
  }
}
```

#### Test 4: Search Accounts
```json
{
  "tool": "search_accounts",
  "arguments": {
    "keywords": "admin"
  }
}
```

#### Test 5: Get Account Details
```json
{
  "tool": "get_account_details",
  "arguments": {
    "account_id": "123_456"
  }
}
```

#### Test 6: List Platforms
```json
{
  "tool": "list_platforms",
  "arguments": {
    "active": true
  }
}
```

## Test Categories

### Unit Tests
- **Authentication Module**: Token management, OAuth flow, credential validation
- **Server Core**: HTTP client, API response parsing, error handling
- **MCP Integration**: Tool wrappers, parameter validation, response formatting

### Integration Tests
- **End-to-end Workflows**: Complete operations from authentication to data retrieval
- **Cross-component Integration**: Authentication + server + MCP layer testing
- **API Compliance**: Real CyberArk API behavior validation

### Performance Tests
- **Response Time Testing**: API call performance measurement
- **Concurrent Request Testing**: Multiple simultaneous operations
- **Token Refresh Testing**: Authentication performance under load

## Testing Strategy

### Test-Driven Development (TDD)
The project follows strict TDD principles:
1. **Write Failing Tests First**: Define expected behavior before implementation
2. **Implement Minimal Code**: Write just enough code to pass tests
3. **Refactor While Green**: Improve code while maintaining passing tests
4. **Comprehensive Coverage**: Test both success and failure scenarios

### Mock Strategy
- **External Dependencies**: All CyberArk API calls are mocked in unit tests
- **Realistic Response Data**: Mock responses match real API behavior
- **Error Simulation**: Mock various error conditions (401, 403, 429, 500)
- **Network Conditions**: Simulate timeouts and connection failures

### Test Data Management
- **Consistent Test Data**: Standardized test account and safe names
- **Special Characters**: Test data includes edge cases (spaces, Unicode)
- **Boundary Conditions**: Test limits, empty responses, large datasets

## Performance Testing

### Response Time Benchmarks
```bash
# Measure test execution time
pytest --durations=10

# Profile specific test categories
pytest -k "test_auth" --durations=5
pytest -k "test_platform" --durations=5
```

### Load Testing
```bash
# Install pytest-benchmark for performance testing
pip install pytest-benchmark

# Run performance benchmarks
pytest tests/ --benchmark-only
```

### Memory Usage Testing
```bash
# Install memory profiler
pip install memory-profiler

# Profile memory usage
python -m memory_profiler src/cyberark_mcp/server.py
```

## Debug Testing

### Debug Mode Configuration
```bash
# Enable debug logging
export CYBERARK_LOG_LEVEL=DEBUG

# Run tests with debug output
pytest -v -s

# Run with Python debugger
pytest --pdb
```

### Test Debugging Commands
```bash
# Run single test with maximum verbosity
pytest -vvv tests/test_core_functionality.py::TestAuthentication::test_token_refresh

# Debug test failure
pytest --pdb-trace tests/test_account_operations.py::test_create_account

# Run with print statements visible
pytest -s tests/test_mcp_integration.py
```

### Common Debug Scenarios
```bash
# Debug authentication issues
pytest -k "auth" -v -s

# Debug API response parsing
pytest -k "response" -v -s

# Debug parameter validation
pytest -k "validation" -v -s
```

## Continuous Integration

### GitHub Actions Workflow
The project includes automated testing:
- **Triggers**: Every push and pull request
- **Environment**: Python 3.13 on Ubuntu latest
- **Test Scope**: All unit tests (excludes integration tests)
- **Features**: Dependency caching, coverage reporting

### CI Test Commands
```bash
# Commands used in CI environment
pytest -m "not integration"
pytest --cov=src/cyberark_mcp --cov-report=xml
```

## Success Criteria

### Test Suite Health
- ✅ All tests pass consistently
- ✅ Minimum 80% code coverage maintained
- ✅ No flaky or intermittent test failures
- ✅ Fast test execution (< 2 minutes for full suite)

### MCP Inspector Integration
- ✅ All 10 tools visible in Inspector interface
- ✅ Tool parameters correctly displayed and validated
- ✅ Successful tool execution with real credentials
- ✅ Clear error messages for invalid operations

### Performance Benchmarks
- ✅ Test suite execution < 2 minutes
- ✅ Individual test execution < 5 seconds
- ✅ Memory usage within acceptable limits
- ✅ No memory leaks in long-running tests

## Next Steps

After successful testing:
1. **Integration**: Connect to preferred MCP client
2. **Automation**: Integrate tools into automated workflows
3. **Monitoring**: Set up production logging and monitoring
4. **Enhancement**: Add additional features based on test feedback

---

This testing guide provides comprehensive coverage for validating the CyberArk Privilege Cloud MCP Server functionality across all testing scenarios.