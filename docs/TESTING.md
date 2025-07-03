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
# Run all tests (148+ total)
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=src/mcp_privilege_cloud

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

**TestServerCore** - Basic server operations and API integration (28+ tests)
- Health check functionality
- Core server initialization and configuration
- Network error handling
- Response parsing validation
- API endpoint testing

**TestPlatformManagement** - Platform operations and API integration (16+ tests)
- Platform package import functionality
- Platform details retrieval
- Administrator role permission testing
- Gen2 API endpoint compliance

#### `tests/test_account_operations.py` (35+ tests)
- Account creation with full parameter validation
- Password management operations (change, set, verify, reconcile)
- Account lifecycle management testing
- Error handling for account operations
- Special character handling in account data
- Account security operation validation

#### `tests/test_mcp_integration.py` (15+ tests)
**TestMCPAccountTools** - Account management MCP tools (8+ tests)
- Account creation MCP tool wrapper
- Password management MCP tool wrappers (change, set, verify, reconcile)
- Parameter passing and validation
- Error handling and response formatting

**TestMCPPlatformTools** - Platform MCP tools integration (3+ tests)
- Platform package import MCP wrapper
- Platform management parameter validation

**TestMCPResourceIntegration** - Resource testing framework (4+ tests)
- Resource discovery and validation
- Resource content retrieval testing
- Resource error handling

#### `tests/test_integration.py` (25+ tests)
**TestPlatformIntegration** - Comprehensive end-to-end integration testing (9+ tests)
- Complete platform workflow from MCP resource to API calls
- Track A & B enhancement integration (server + resource improvements)
- Field transformation integration across all data types
- Mixed success/failure scenarios with graceful degradation
- Error handling integration across all layers (auth, server, resource)
- Performance characteristics of concurrent operations
- Backward compatibility with existing implementations
- Resource metadata integration testing
- MCP server initialization with enhanced features

#### `tests/test_resources.py` (24+ tests)
- Resource implementation testing
- Resource registry functionality
- Resource content generation and validation
- Resource error handling and edge cases
- Resource URI pattern matching

### Test Coverage Metrics
- **Total Tests**: 267+ comprehensive test cases
- **Target Coverage**: Minimum 80% code coverage
- **Mock Strategy**: All external CyberArk API dependencies are mocked
- **Test Types**: Unit, integration, MCP tools, and MCP resources tests
- **Platform Enhancement Coverage**: Complete Track A & B integration testing

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

# Resource tests only
pytest tests/test_resources.py
```

#### Run by Test Categories
```bash
# Authentication tests
pytest -m auth

# Unit tests (excludes integration)
pytest -m unit

# Integration tests (requires environment setup)
pytest -m integration

# Platform enhancement integration tests
pytest tests/test_integration.py::TestPlatformIntegration -v

# Platform management tests
pytest -k platform

# Resource tests
pytest -k resource

# Account management tests (tools and operations)
pytest -k account

# Password management tests
pytest -k password
```

#### Platform Enhancement Integration Testing
The platform enhancement integration tests validate the complete Track A and Track B implementations:

```bash
# Run all platform enhancement integration tests
pytest tests/test_integration.py::TestPlatformIntegration -v

# Run specific integration test scenarios
pytest tests/test_integration.py::TestPlatformIntegration::test_complete_platform_workflow -v
pytest tests/test_integration.py::TestPlatformIntegration::test_field_transformation_comprehensive_integration -v
pytest tests/test_integration.py::TestPlatformIntegration::test_error_handling_integration_across_layers -v
pytest tests/test_integration.py::TestPlatformIntegration::test_concurrent_operations_performance -v

# Test backward compatibility
pytest tests/test_integration.py::TestPlatformIntegration::test_backward_compatibility_integration -v

# Test graceful degradation
pytest tests/test_integration.py::TestPlatformIntegration::test_mixed_success_failure_scenarios -v
```

### Coverage Testing
```bash
# Generate coverage report
pytest --cov=src/mcp_privilege_cloud

# Coverage with HTML report
pytest --cov=src/mcp_privilege_cloud --cov-report=html

# Coverage with missing lines
pytest --cov=src/mcp_privilege_cloud --cov-report=term-missing

# Coverage for specific module
pytest --cov=src/mcp_privilege_cloud/auth tests/test_core_functionality.py::TestAuthentication
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
# Recommended: Use uv for development
uv run mcp-privilege-cloud

# Alternative: Use uvx for production-like testing
uvx mcp-privilege-cloud

# Legacy: Direct execution
python -m mcp_privilege_cloud
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
2. **Command**: Enter one of:
   ```bash
   # Recommended for development
   uv run mcp-privilege-cloud
   
   # Or for production-like testing
   uvx mcp-privilege-cloud
   
   # Or legacy method
   python -m mcp_privilege_cloud
   ```
3. **Click Connect**

#### Verify Available Tools and Resources
You should see these **6 tools** in the Inspector:
- `create_account`
- `change_account_password`
- `set_next_password`
- `verify_account_password`
- `reconcile_account_password`
- `import_platform_package`

And these **4 resources**:
- `cyberark://health/` - System health status
- `cyberark://safes/` - All accessible safes
- `cyberark://accounts/` - All accessible accounts
- `cyberark://platforms/` - All available platforms

### Parameter Validation Testing

Test tool parameter validation without real API calls:

#### Test Required Parameters
```json
// Should fail - missing required parameter
{
  "tool": "create_account",
  "arguments": {}
}

// Should fail - missing required parameter
{
  "tool": "change_account_password",
  "arguments": {}
}
```

#### Test Optional Parameters
```json
// Should validate successfully
{
  "tool": "create_account",
  "arguments": {
    "platform_id": "WinServerLocal",
    "safe_name": "TestSafe",
    "address": "test.server.com",
    "user_name": "testuser"
  }
}

// Should validate successfully  
{
  "tool": "change_account_password",
  "arguments": {
    "account_id": "123_456"
  }
}
```

### Resource Testing

Resources provide read-only access to CyberArk data through URI-based endpoints. Test resource accessibility without real API calls:

#### Test Resource Discovery
Resources should be discoverable in the MCP Inspector under the "Resources" section.

#### Test Resource URIs
```bash
# Health status resource
cyberark://health/

# Safes collection resource  
cyberark://safes/

# Accounts collection resource
cyberark://accounts/

# Platforms collection resource
cyberark://platforms/
```

#### Expected Resource Behavior
- **Without credentials**: Resources should return error information explaining missing configuration
- **With credentials**: Resources should return formatted JSON data from CyberArk APIs
- **Invalid URIs**: Should return clear error messages for unsupported resource patterns

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
from src.mcp_privilege_cloud.server import CyberArkMCPServer
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
uv run mcp-privilege-cloud
```

**Expected Output:**
```
INFO - Starting CyberArk Privilege Cloud MCP Server
INFO - CyberArk server connection established successfully
```

### Real API Testing Sequence

#### Test 1: Read Health Resource
```
Resource URI: cyberark://health/
```
**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-07-01T...",
  "safes_accessible": 5
}
```

#### Test 2: Read Safes Resource
```
Resource URI: cyberark://safes/
```

#### Test 3: Read Accounts Resource
```
Resource URI: cyberark://accounts/
```

#### Test 4: Create Account Tool
```json
{
  "tool": "create_account",
  "arguments": {
    "platform_id": "WinServerLocal",
    "safe_name": "YourSafeName",
    "address": "test.server.com",
    "user_name": "testuser"
  }
}
```

#### Test 5: Change Account Password Tool
```json
{
  "tool": "change_account_password",
  "arguments": {
    "account_id": "123_456"
  }
}
```

#### Test 6: Read Platforms Resource
```
Resource URI: cyberark://platforms/
```

## Test Categories

### Unit Tests
- **Authentication Module**: Token management, OAuth flow, credential validation
- **Server Core**: HTTP client, API response parsing, error handling
- **MCP Tools**: Action tool wrappers, parameter validation, response formatting
- **MCP Resources**: Resource content generation, URI pattern matching, registry functionality

### Integration Tests
- **End-to-end Workflows**: Complete operations from authentication to action execution
- **Cross-component Integration**: Authentication + server + MCP layer testing
- **API Compliance**: Real CyberArk API behavior validation
- **Resource Integration**: Resource content retrieval and formatting testing

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

### Dedicated Performance Test Suite

The project includes a comprehensive performance test suite in `tests/test_performance.py` with 11+ specialized tests covering:

#### Core Performance Tests
- **Platform List Performance**: Tests platform listing with various sizes (1, 10, 125+ platforms)
- **Concurrent Platform Details**: Validates concurrent API calls with proper rate limiting
- **Memory Usage Monitoring**: Tracks memory consumption during large operations
- **Scalability Testing**: Verifies linear scaling characteristics

#### Performance Test Execution
```bash
# Run all performance tests
pytest -m performance

# Run specific performance test categories
pytest -m memory                    # Memory usage tests
pytest -k "test_platform_list"      # Platform performance tests
pytest -k "test_concurrent"         # Concurrency tests

# Run with performance metrics
pytest -m performance --durations=10 -v
```

#### Performance Benchmarks and Targets
From comprehensive testing with real API simulation:

**Platform Operations**:
- **Basic Platform List** (125 platforms): ~1.5s total, ~12ms per platform
- **Enhanced Platform List** (125 platforms): ~4.2s total, ~34ms per platform
- **Concurrent Enhancement**: 3-5x improvement over sequential processing
- **Memory Usage**: <0.002 MB per enhanced platform object

**Scalability Metrics**:
- **Linear Scaling**: Maintained up to 125+ platforms
- **Concurrency Limit**: 5 concurrent requests (configurable)
- **Error Handling**: 20% failure rate adds <0.3s overhead
- **Memory Efficiency**: Enhanced objects 4.9x larger but <3KB each

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
python -m memory_profiler src/mcp_privilege_cloud/server.py
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
pytest --cov=src/mcp_privilege_cloud --cov-report=xml
```

## Success Criteria

### Test Suite Health
- ✅ All tests pass consistently
- ✅ Minimum 80% code coverage maintained
- ✅ No flaky or intermittent test failures
- ✅ Fast test execution (< 2 minutes for full suite)

### MCP Inspector Integration
- ✅ All 6 action tools visible in Inspector interface
- ✅ All 4 resources accessible in Inspector interface
- ✅ Tool parameters correctly displayed and validated
- ✅ Resource content properly loaded and displayed
- ✅ Successful tool execution with real credentials
- ✅ Clear error messages for invalid operations

### Performance Benchmarks
- ✅ Test suite execution < 2 minutes
- ✅ Individual test execution < 5 seconds
- ✅ Memory usage within acceptable limits
- ✅ No memory leaks in long-running tests

## Next Steps

After successful testing:
1. **Integration**: Connect to preferred MCP client (Claude Desktop, etc.)
2. **Automation**: Integrate action tools and resources into automated workflows
3. **Monitoring**: Set up production logging and monitoring
4. **Enhancement**: Add additional password management features and resources

---

This testing guide provides comprehensive coverage for validating the CyberArk Privilege Cloud MCP Server functionality across all testing scenarios.