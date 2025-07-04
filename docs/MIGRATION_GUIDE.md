# Migration Guide: Resources to Tools

This guide helps users migrate from the legacy resource-based approach to the new tool-based architecture.

## Overview

**Version**: 0.2.0  
**Breaking Change**: Resources have been completely replaced by tools for better MCP client compatibility.

## Why This Change?

- **Better MCP Client Compatibility**: Tools work consistently across all MCP clients
- **Simplified Architecture**: Direct function calls vs complex URI parsing
- **Type Safety**: Full parameter validation and type hints
- **Exact API Data**: Zero field manipulation - returns raw CyberArk API responses
- **Performance**: Eliminated resource registry and URI parsing overhead

## Migration Mapping

| Legacy Resource | New Tool | Parameters | Benefits |
|----------------|----------|------------|----------|
| `cyberark://accounts/` | `list_accounts()` | None | Direct function call, better caching |
| `cyberark://accounts/search?query=admin&safe_name=IT` | `search_accounts(query="admin", safe_name="IT")` | Type-safe parameters | Easier to use, IDE support |
| `cyberark://safes/` | `list_safes()` | None | Simplified access |
| `cyberark://platforms/` | `list_platforms()` | None | Direct API data |

## Code Examples

### Before (Resources)
```python
# Old resource-based approach
import mcp
client = mcp.Client()

# List accounts via resource URI
accounts_content = await client.read_resource("cyberark://accounts/")
accounts = json.loads(accounts_content)["items"]

# Search accounts with query parameters  
search_uri = "cyberark://accounts/search?query=admin&safe_name=IT-Infrastructure"
search_content = await client.read_resource(search_uri)
search_results = json.loads(search_content)["items"]
```

### After (Tools)
```python
# New tool-based approach
import mcp
client = mcp.Client()

# List accounts via tool
accounts = await client.call_tool("list_accounts")

# Search accounts with typed parameters
search_results = await client.call_tool("search_accounts", {
    "query": "admin",
    "safe_name": "IT-Infrastructure"
})
```

## Data Format Changes

**Good News**: No data format changes! Tools return exactly the same data structures as resources, with the same field names and values.

### Example Response (Unchanged)
```json
[
  {
    "id": "123_456",
    "userName": "admin",
    "platformId": "WinServerLocal", 
    "safeName": "IT-Infrastructure",
    "secretType": "password",
    "createdTime": "2025-01-01T00:00:00Z"
  }
]
```

## Benefits of Tools Over Resources

### 1. Better Client Compatibility
- **Resources**: Inconsistent support across MCP clients
- **Tools**: Universal support in all MCP clients

### 2. Type Safety
- **Resources**: String URIs, runtime errors
- **Tools**: Typed parameters, compile-time validation

### 3. Performance
- **Resources**: URI parsing + resource registry + content generation
- **Tools**: Direct server method calls

### 4. Developer Experience
- **Resources**: Manual URI construction, hard to debug
- **Tools**: IDE autocompletion, clear parameter names

## Integration Updates

### Claude Desktop Configuration
```json
{
  "mcp": {
    "servers": {
      "cyberark": {
        "command": "uvx",
        "args": ["mcp-privilege-cloud"]
      }
    }
  }
}
```

### MCP Inspector Testing
```bash
# Tools are automatically discovered
npx @modelcontextprotocol/inspector uvx mcp-privilege-cloud
```

## Troubleshooting

### "Resource not found" Errors
**Error**: `No resource handler found for URI: cyberark://accounts/`  
**Solution**: Use `list_accounts()` tool instead

### "Invalid URI" Errors
**Error**: `Invalid URI format: cyberark://accounts/search?query=...`  
**Solution**: Use `search_accounts(query="...")` tool with parameters

### Missing Data
**Issue**: Tool returns different data than resource  
**Solution**: This shouldn't happen - tools return identical data. Check tool parameters.

## Support

- **Documentation**: [Server Capabilities](SERVER_CAPABILITIES.md)
- **Examples**: [API Reference](API_REFERENCE.md)  
- **Issues**: GitHub repository issues section
- **Migration Help**: See tool definitions in codebase

## Timeline

- **v0.1.x**: Resources supported (legacy)
- **v0.2.0**: Resources removed, tools only
- **Future**: Tools will remain stable, new features added as tools

This migration improves reliability and compatibility while maintaining all existing functionality.