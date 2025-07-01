# Simplified Implementation Plan: MCP Schema & Tool Definitions Enhancement

**Priority**: High  
**Estimated Effort**: 2-3 hours  
**Complexity**: Low-Medium  

## Problem Statement

Current MCP tools use basic Python typing without comprehensive documentation and structured parameter definitions. This makes tools harder to discover and integrate with MCP clients.

## Simplified Solution

Instead of creating separate schema files, enhance existing tool definitions with:
1. **Comprehensive docstrings** with structured parameter documentation
2. **Pydantic response models** for consistent return types
3. **Enhanced type hints** with proper Optional/Union usage
4. **Usage examples** in docstrings

## Implementation Steps

### Step 1: Create Response Models Only
File: `src/mcp_privilege_cloud/models.py` (single file)

```python
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class AccountResponse(BaseModel):
    id: str
    name: str
    address: Optional[str] = None
    userName: Optional[str] = None
    safeName: str
    platformId: str
    # ... other fields

class SafeResponse(BaseModel):
    safeName: str
    description: Optional[str] = None
    location: Optional[str] = None
    # ... other fields

class PlatformResponse(BaseModel):
    platformId: str
    platformName: str
    systemType: str
    # ... other fields
```

### Step 2: Enhance Tool Docstrings
Update each tool function with comprehensive documentation:

```python
@mcp.tool()
async def create_account(
    platform_id: str,
    safe_name: str,
    name: Optional[str] = None,
    address: Optional[str] = None,
    user_name: Optional[str] = None,
    # ... other parameters
) -> Dict[str, Any]:
    """
    Create a new privileged account in CyberArk Privilege Cloud.
    
    Args:
        platform_id: Platform ID (required). Examples: "WinServerLocal", "UnixSSH"
        safe_name: Target safe name (required). Must exist and be accessible
        name: Account identifier (optional). If not provided, will use user_name
        address: Target hostname/IP (optional). Examples: "server01.corp.com", "192.168.1.100"
        user_name: Username for account (optional). Examples: "admin", "service_account"
        
    Returns:
        Dict containing created account details with 'id' field
        
    Examples:
        # Create Windows server account
        create_account("WinServerLocal", "Production-Servers", 
                      address="web01.corp.com", user_name="admin")
        
        # Create Unix account with SSH key
        create_account("UnixSSH", "Unix-Servers", 
                      address="db01.corp.com", user_name="oracle")
    
    Raises:
        CyberArkAPIError: If safe doesn't exist or platform is invalid
        AuthenticationError: If insufficient permissions
    """
```

### Step 3: Add Type Hints
Improve type hints for better IDE support:

```python
from typing import Dict, Any, List, Optional, Union

@mcp.tool()
async def list_accounts(
    safe_name: Optional[str] = None,
    username: Optional[str] = None,
    address: Optional[str] = None
) -> List[Dict[str, Any]]:  # More specific return type
```

### Step 4: Add Response Validation (Optional)
For critical tools, add response validation:

```python
@mcp.tool()
async def create_account(...) -> Dict[str, Any]:
    """..."""
    try:
        server = CyberArkMCPServer.from_environment()
        result = await server.create_account(...)
        
        # Validate response has required fields
        if 'id' not in result:
            raise ValueError("Account creation failed - no ID returned")
            
        return result
    except Exception as e:
        logger.error(f"Error creating account: {e}")
        raise
```

## Minimal File Changes

### Files to Modify
1. `src/mcp_privilege_cloud/mcp_server.py` - Update all 13 tool functions
2. `src/mcp_privilege_cloud/models.py` - Create (simple response models)
3. `tests/test_mcp_integration.py` - Add docstring tests

### Documentation Updates
1. Update `SERVER_CAPABILITIES.md` with enhanced tool descriptions
2. Add usage examples to `README.md`

## Benefits of Simplified Approach

1. **Faster Implementation**: 2-3 hours vs 4-6 hours
2. **Less Maintenance**: Single file vs multiple schema files
3. **Immediate Value**: Better documentation and examples
4. **Incremental**: Can add full validation later if needed
5. **Backward Compatible**: No breaking changes

## Success Criteria

- ✅ All 13 tools have comprehensive docstrings with examples
- ✅ Improved type hints for better IDE support  
- ✅ Basic response models for key data structures
- ✅ Enhanced tool discoverability in MCP clients
- ✅ Updated documentation with usage examples

## Next Steps

1. **Phase 1** (1 hour): Create basic response models
2. **Phase 2** (1-2 hours): Update all tool docstrings with examples
3. **Phase 3** (30 minutes): Update documentation and README

This simplified approach provides 80% of the benefits with 50% of the effort, while maintaining the option to add full validation later if needed.

---

**Implementation Order**: Start with most-used tools (list_accounts, create_account, list_safes) first for immediate impact.