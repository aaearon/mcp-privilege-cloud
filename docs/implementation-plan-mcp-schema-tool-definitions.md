# Implementation Plan: MCP Schema & Tool Definitions Enhancement

**Priority**: High  
**Estimated Effort**: 4-6 hours  
**Complexity**: Medium  

## Problem Statement

Current MCP tools lack comprehensive schema definitions and proper documentation standards. Tools use basic Python typing without leveraging MCP's full schema capabilities, making them less discoverable and harder for clients to integrate.

## Current State Analysis

### Issues Identified
1. **Minimal Parameter Documentation**: Tools have basic docstrings but lack structured parameter schemas
2. **Inconsistent Return Types**: Return types are generic `Dict[str, Any]` without specific schemas  
3. **No Input Validation**: Parameters only use basic Python typing
4. **Poor Discoverability**: Clients can't easily understand tool capabilities
5. **Missing Examples**: No usage examples in tool definitions

### Affected Files
- `src/mcp_privilege_cloud/mcp_server.py` (13 tool functions)
- All `@mcp.tool()` decorated functions need enhancement

## Implementation Strategy

### Phase 1: Schema Definition Framework
1. **Create Schema Models Directory**
   - Create `src/mcp_privilege_cloud/schemas/` directory
   - Separate schema files by domain: `accounts.py`, `safes.py`, `platforms.py`

2. **Base Schema Classes**
   - Create base classes for common patterns
   - Standardize error response schemas
   - Define pagination schema patterns

### Phase 2: Tool Parameter Schemas
1. **Input Parameter Models**
   - Create Pydantic models for each tool's parameters
   - Add field validation and descriptions
   - Include examples in field definitions

2. **Output Response Models** 
   - Define structured response models
   - Standardize success/error response patterns
   - Add response examples

### Phase 3: Tool Function Enhancement
1. **Update Tool Decorators**
   - Add comprehensive docstrings with parameter details
   - Include usage examples
   - Specify return type schemas

2. **Parameter Validation Integration**
   - Integrate Pydantic models with tool functions
   - Add proper type hints
   - Enhance error messages

## Detailed Implementation Steps

### Step 1: Create Schema Infrastructure
```bash
mkdir -p src/mcp_privilege_cloud/schemas
touch src/mcp_privilege_cloud/schemas/__init__.py
touch src/mcp_privilege_cloud/schemas/accounts.py
touch src/mcp_privilege_cloud/schemas/safes.py
touch src/mcp_privilege_cloud/schemas/platforms.py
touch src/mcp_privilege_cloud/schemas/common.py
```

### Step 2: Define Base Schema Classes
File: `src/mcp_privilege_cloud/schemas/common.py`
- `BaseRequest` - Common request patterns
- `BaseResponse` - Standardized response wrapper
- `ErrorResponse` - Structured error responses
- `PaginationParams` - Pagination parameters
- `PaginatedResponse` - Paginated response wrapper

### Step 3: Account Schema Implementation
File: `src/mcp_privilege_cloud/schemas/accounts.py`
- `ListAccountsParams` - Parameters for listing accounts
- `SearchAccountsParams` - Parameters for account search
- `CreateAccountParams` - Account creation parameters
- `AccountResponse` - Single account response
- `AccountListResponse` - Account list response

### Step 4: Safe Schema Implementation  
File: `src/mcp_privilege_cloud/schemas/safes.py`
- `ListSafesParams` - Safe listing parameters
- `SafeDetailsParams` - Safe details parameters
- `SafeResponse` - Safe object response
- `SafeListResponse` - Safe list response

### Step 5: Platform Schema Implementation
File: `src/mcp_privilege_cloud/schemas/platforms.py`
- `ListPlatformsParams` - Platform listing parameters
- `PlatformResponse` - Platform object response
- `ImportPlatformParams` - Platform import parameters

### Step 6: Tool Function Updates
For each tool in `mcp_server.py`:
1. Import relevant schema classes
2. Update function signatures with proper types
3. Add comprehensive docstrings with examples
4. Integrate parameter validation
5. Return properly typed responses

## Example Implementation Patterns

### Enhanced Tool Definition Pattern
```python
@mcp.tool()
async def list_accounts(
    safe_name: Optional[str] = None,
    username: Optional[str] = None, 
    address: Optional[str] = None
) -> AccountListResponse:
    """
    List accounts from CyberArk Privilege Cloud with optional filtering.
    
    This tool retrieves privileged accounts from CyberArk Privilege Cloud,
    allowing filtering by safe name, username, or address/hostname.
    
    Args:
        safe_name: Filter accounts by safe name. Case-sensitive exact match.
        username: Filter accounts by username. Supports partial matching.
        address: Filter accounts by address/hostname. Supports partial matching.
    
    Returns:
        AccountListResponse: Structured response containing list of accounts
        with metadata including total count and pagination info.
    
    Examples:
        # List all accessible accounts
        await list_accounts()
        
        # List accounts in specific safe
        await list_accounts(safe_name="Production-Servers")
        
        # Find accounts by username pattern
        await list_accounts(username="admin")
    
    Raises:
        CyberArkAPIError: When API request fails
        AuthenticationError: When authentication fails
    """
```

## Testing Requirements

### Unit Tests
- Schema validation tests for all parameter models
- Tool function parameter validation tests
- Response schema validation tests

### Integration Tests
- End-to-end tool execution with schema validation
- Error handling with proper schema responses
- MCP client integration tests

## Documentation Updates

### Files to Update
1. `SERVER_CAPABILITIES.md` - Add schema documentation
2. `README.md` - Update tool usage examples
3. `docs/SCHEMAS.md` - New comprehensive schema documentation

### Documentation Requirements
- Parameter schema documentation for each tool
- Response format documentation
- Usage examples with actual schemas
- Error response documentation

## Validation Criteria

### Success Metrics
1. **Schema Coverage**: All 13 tools have comprehensive parameter schemas
2. **Type Safety**: All tool parameters properly validated
3. **Documentation**: Complete schema documentation with examples
4. **Client Integration**: MCP clients can auto-discover tool capabilities
5. **Error Handling**: Structured error responses with proper schemas

### Testing Checklist
- [ ] All tools have parameter validation
- [ ] All responses follow schema patterns
- [ ] Schema documentation is complete
- [ ] Unit tests pass for all schemas
- [ ] Integration tests validate end-to-end schema usage
- [ ] MCP Inspector shows enhanced tool information

## Risk Mitigation

### Breaking Changes
- **Risk**: Schema changes might break existing clients
- **Mitigation**: Maintain backward compatibility in parameter names and types

### Performance Impact
- **Risk**: Additional validation might slow down tool execution
- **Mitigation**: Benchmark performance before/after, optimize if necessary

### Maintenance Overhead
- **Risk**: Additional schema files increase maintenance
- **Mitigation**: Use inheritance and composition to reduce duplication

## Dependencies

### New Dependencies
- Existing Pydantic dependency sufficient
- No additional external dependencies required

### Development Dependencies
- Schema validation testing utilities
- MCP client testing tools

## Rollout Strategy

### Phase 1: Infrastructure (Day 1)
- Create schema directory structure
- Implement base schema classes
- Set up testing framework

### Phase 2: Core Schemas (Days 2-3)
- Implement account, safe, platform schemas
- Create comprehensive parameter models
- Add response models

### Phase 3: Tool Integration (Days 4-5)
- Update all tool functions with schemas
- Integrate parameter validation
- Update documentation

### Phase 4: Validation & Testing (Day 6)
- Complete testing suite
- Validate MCP client integration
- Performance testing and optimization

## Success Criteria

1. ✅ All tools have comprehensive parameter schemas with validation
2. ✅ Standardized response formats across all tools
3. ✅ Complete documentation with examples
4. ✅ Enhanced MCP client discoverability
5. ✅ Maintained backward compatibility
6. ✅ Performance impact < 10% increase in response time
7. ✅ 100% test coverage for schema validation

---

**Next Steps**: After approval, begin with Phase 1 infrastructure setup and base schema implementation.