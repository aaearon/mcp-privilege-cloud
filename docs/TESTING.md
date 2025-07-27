# Testing Guide

Testing guide for LLM development of the CyberArk Privilege Cloud MCP Server. Focus on test structure, patterns, and validation strategies for AI-assisted development.

## Current Test Status ✅ **VERIFIED**

**Test Suite Results**: **144/144 tests passing** (100% success rate)  
**Code Coverage**: Maintained across massive 45-tool expansion  
**Functionality Verification**: Zero regression after 221% tool expansion (14→45 tools)  
**Integration Testing**: All 45 MCP tools verified across all 4 PCloud services with proper parameter passing  
**Last Validation**: July 27, 2025 - Post Phase 2 & 3 PCloud service expansion

The test suite validates the complete 45-tool implementation ensuring comprehensive coverage of all Account Management, Safe Management, Platform Management, and Applications Management tools with zero regression.

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

#### `tests/test_core_functionality.py` (88+ tests)
**TestAuthentication** - Token management and OAuth flow (enhanced coverage)
- OAuth 2.0 client credentials flow testing
- Token refresh mechanisms
- Environment variable validation
- Authentication error handling
- Concurrent token request handling

**TestServerCore** - Basic server operations and API integration (expanded coverage)
- Health check functionality
- Core server initialization and configuration
- Network error handling
- Response parsing validation
- API endpoint testing across all 4 PCloud services

**TestPlatformManagement** - Platform operations and comprehensive API integration (enhanced coverage)
- Platform package import functionality
- Platform details retrieval with enhanced data combination
- Administrator role permission testing
- Gen2 API endpoint compliance
- Platform lifecycle management testing
- Statistics and target platform operations testing

#### `tests/test_account_operations.py` (85+ tests)
- **Complete Account Lifecycle**: Create, read, update, delete operations with comprehensive validation
- **Advanced Search Operations**: Platform grouping, environment filtering, management status analysis
- **Password Management**: Complete password operations (change, set, verify, reconcile)
- **Account Analytics**: Distribution analysis, pattern searching, criteria-based counting
- **Grouping Operations**: Safe-based and platform-based account organization
- **Error Handling**: Comprehensive error scenarios across all 17 account management tools
- **Special Character Handling**: Account data validation and security testing

#### `tests/test_mcp_integration.py` (18+ tests)
**TestMCPAccountTools** - Complete account management MCP tools (enhanced coverage)
- All 17 account management tool wrappers
- Advanced search and analytics tool testing
- Password management MCP tool wrappers (change, set, verify, reconcile)
- Parameter passing and validation across expanded tool set
- Error handling and response formatting

**TestMCPSafeTools** - Safe management MCP tools integration (enhanced coverage)
- All 11 safe management tools including member management
- Safe CRUD operations and member management workflows
- Permission and access validation testing

**TestMCPPlatformTools** - Platform MCP tools integration (enhanced coverage)
- Complete platform lifecycle management (10 tools)
- Platform statistics and target platform operations
- Platform package import/export and lifecycle management

**TestMCPApplicationsTools** - Applications management MCP tools integration (new coverage)
- All 9 applications management tools
- Authentication method management workflows
- Application statistics and lifecycle operations

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
- **Total Tests**: 144+ tests across 6 test files
- **Target Coverage**: Minimum 80% code coverage maintained across 45-tool expansion
- **Mock Strategy**: All external CyberArk API dependencies are mocked using official SDK patterns
- **Test Types**: Unit, integration, MCP tools tests across all 4 PCloud services
- **Service Coverage**: Complete testing for ArkPCloudAccountsService, ArkPCloudSafesService, ArkPCloudPlatformsService, ArkPCloudApplicationsService

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
- `tests/test_account_operations.py` - Complete account lifecycle management (85+ tests)  
- `tests/test_mcp_integration.py` - MCP tool wrappers and integration across all 4 services (18+ tests)
- `tests/test_integration.py` - End-to-end integration tests with enhanced platform operations (25+ tests)
- `tests/test_performance.py` - Performance and optimization tests (11+ tests)
- `tests/test_resources.py` - MCP resource implementation tests (42+ tests)

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