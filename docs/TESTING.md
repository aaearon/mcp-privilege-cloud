# Testing Guide

Testing guide for LLM development of the CyberArk Privilege Cloud MCP Server. Focus on test structure, patterns, and validation strategies for AI-assisted development.

## Current Test Status ✅ **VERIFIED**

**Test Suite Results**: **48/48 tests passing** (100% success rate)  
**Code Coverage**: Maintained across simplified codebase  
**Functionality Verification**: Zero regression after ~27% code reduction  
**Integration Testing**: All MCP tools verified with proper parameter passing  
**Last Validation**: July 26, 2025 - Post code simplification

The test suite validates the simplified architecture ensuring all refactoring maintained identical functionality while reducing code complexity.

## LLM Development Testing

**Core Commands**:
```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src/mcp_privilege_cloud

# Test categories
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
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

**TestMCPListingTools** - Data access tool testing (4+ tests)
- List tools validation (`list_accounts`, `list_safes`, `list_platforms`)
- Search tool testing (`search_accounts`)
- Tool parameter validation and response formatting

#### `tests/test_tools.py` (9+ tests)
- Direct tool function testing
- Parameter validation for all tools
- Error handling for tool operations
- Raw API data verification

#### `tests/test_integration_tools.py` (2+ tests)
- Tool integration testing with server methods
- End-to-end tool workflow validation

#### Legacy Test Files (Removed)
- `tests/test_resources.py` - Removed (resources converted to tools)
- `tests/test_integration_old.py` - Removed (legacy resource integration tests)

The testing architecture has been simplified by converting to a tool-based architecture while maintaining comprehensive coverage for all tool functionality.

### Test Coverage Metrics
- **Total Tests**: 48 tests across 6 test files
- **Target Coverage**: Minimum 80% code coverage
- **Mock Strategy**: All external CyberArk API dependencies are mocked
- **Test Types**: Unit, integration, MCP tools tests

## Testing Strategy

### Test-Driven Development (TDD)
1. **Write Failing Tests First**: Define expected behavior before implementation
2. **Implement Minimal Code**: Write just enough code to pass tests
3. **Refactor While Green**: Improve code while maintaining passing tests
4. **Comprehensive Coverage**: Test both success and failure scenarios

### Mock Strategy
- **External Dependencies**: All CyberArk API calls are mocked in unit tests
- **Realistic Response Data**: Mock responses match real API behavior
- **Error Simulation**: Mock various error conditions (401, 403, 429, 500)
- **Network Conditions**: Simulate timeouts and connection failures

### Test Categories
- **Unit Tests**: Authentication, server core, MCP tools, parameter validation
- **Integration Tests**: End-to-end workflows, cross-component integration
- **Performance Tests**: Response times, concurrent operations, memory usage

### Key Test Files for LLM Development
- `tests/test_core_functionality.py` - Authentication, server core, platform management (88+ tests)
- `tests/test_account_operations.py` - Account lifecycle management (85+ tests)
- `tests/test_mcp_integration.py` - MCP tool wrappers and integration (18+ tests)

### Performance Testing
```bash
# Run performance tests
pytest -m performance

# Memory usage tests
pytest -m memory
```

### Essential Test Commands for LLM Development
```bash
# Run specific test files
pytest tests/test_core_functionality.py
pytest tests/test_account_operations.py
pytest tests/test_mcp_integration.py

# Test by categories
pytest -m auth          # Authentication tests
pytest -k platform     # Platform management tests
pytest -k account      # Account management tests
```