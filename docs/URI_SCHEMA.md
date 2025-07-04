# CyberArk MCP URI Schema Reference (Legacy)

**⚠️ DEPRECATED**: This document describes the legacy URI schema for resources. Resources have been replaced by tools for better MCP client compatibility.

## Migration Notice

URI-based resources have been replaced with direct tool functions. Instead of using URIs like `cyberark://accounts/`, use the corresponding tools:

- `cyberark://accounts/` → `list_accounts()`
- `cyberark://accounts/search?query=...` → `search_accounts(query=..., safe_name=..., etc.)`
- `cyberark://safes/` → `list_safes()`
- `cyberark://platforms/` → `list_platforms()`

For current capabilities, see [Server Capabilities](../SERVER_CAPABILITIES.md).

---

## Legacy URI Schema (For Reference Only)

This section is maintained for historical reference and migration purposes.

## URI Format

All CyberArk MCP resources follow a standardized URI format:

```
cyberark://{category}/[{identifier}/][{subcategory}/][?{query_parameters}]
```

### Components

- **Scheme**: Always `cyberark://`
- **Category**: Resource type (safes, accounts, platforms, health)
- **Identifier**: Specific entity identifier (optional for collections)
- **Subcategory**: Sub-resource type (optional)
- **Query Parameters**: Filters and search parameters (optional)

### URI Types

1. **Collection URIs**: Lists of entities
   - Format: `cyberark://{category}/`
   - Example: `cyberark://safes/`

2. **Entity URIs**: Individual entities
   - Format: `cyberark://{category}/{identifier}/`
   - Example: `cyberark://safes/ProductionSafe/`

3. **Subcollection URIs**: Collections within entities
   - Format: `cyberark://{category}/{identifier}/{subcategory}/`
   - Example: `cyberark://safes/ProductionSafe/accounts/`

4. **Search URIs**: Query-based resources
   - Format: `cyberark://{category}/search?{parameters}`
   - Example: `cyberark://accounts/search?query=server&safe_name=Production`

## Complete URI Reference

### Health Resources

| URI | Type | Description |
|-----|------|-------------|
| `cyberark://health/` | Entity | System health status and metrics |

**Examples**:
```
cyberark://health/
```

### Safe Resources

| URI Pattern | Type | Description |
|-------------|------|-------------|
| `cyberark://safes/` | Collection | All accessible safes |
| `cyberark://safes/{safe_name}/` | Entity | Specific safe details |
| `cyberark://safes/{safe_name}/accounts/` | Subcollection | Accounts in safe |
| `cyberark://safes/{safe_name}/members/` | Subcollection | Safe members (future) |

**Examples**:
```
cyberark://safes/
cyberark://safes/ProductionServers/
cyberark://safes/ProductionServers/accounts/
cyberark://safes/Development%20Environment/
cyberark://safes/HR-Systems/accounts/
```

**Safe Name Encoding**:
- Spaces: URL encoded as `%20`
- Special characters: URL encoded
- Case sensitive: Preserve exact case

### Account Resources

| URI Pattern | Type | Description |
|-------------|------|-------------|
| `cyberark://accounts/` | Collection | All accessible accounts |
| `cyberark://accounts/{account_id}/` | Entity | Specific account details |
| `cyberark://accounts/search` | Collection | Search accounts with filters |

**Examples**:
```
cyberark://accounts/
cyberark://accounts/12345/
cyberark://accounts/67890/
cyberark://accounts/search?query=webserver
cyberark://accounts/search?safe_name=ProductionServers
cyberark://accounts/search?platform_id=WinServerLocal
cyberark://accounts/search?query=admin&safe_name=Production&platform_id=LinuxSSH
```

**Search Query Parameters**:
- `query`: Free text search across account properties
- `safe_name`: Filter by specific safe name
- `username`: Filter by account username
- `address`: Filter by account address
- `platform_id`: Filter by platform identifier

### Platform Resources

| URI Pattern | Type | Description |
|-------------|------|-------------|
| `cyberark://platforms/` | Collection | All available platforms |
| `cyberark://platforms/{platform_id}/` | Entity | Specific platform details |
| `cyberark://platforms/packages/` | Collection | Platform packages info |

**Examples**:
```
cyberark://platforms/
cyberark://platforms/WinServerLocal/
cyberark://platforms/LinuxSSH/
cyberark://platforms/UnixSSH/
cyberark://platforms/OracleDB/
cyberark://platforms/packages/
```

**Platform ID Format**:
- No spaces allowed
- CamelCase convention
- Alphanumeric characters
- Examples: `WinServerLocal`, `LinuxSSH`, `OracleDB`

## URI Validation Rules

### General Rules

1. **Scheme**: Must be exactly `cyberark://`
2. **Case Sensitivity**: Preserve case for identifiers
3. **URL Encoding**: Required for special characters
4. **Trailing Slashes**: Optional but recommended for consistency

### Category Validation

- Must be one of: `health`, `safes`, `accounts`, `platforms`
- Lowercase only
- No special characters

### Identifier Validation

- **Safe Names**: 
  - 1-50 characters
  - Alphanumeric, spaces, hyphens, underscores
  - URL encode spaces and special characters
  
- **Account IDs**: 
  - Numeric strings
  - Length varies by system
  - Obtained from API responses
  
- **Platform IDs**:
  - Alphanumeric characters
  - No spaces
  - CamelCase convention

### Query Parameter Validation

- **Keys**: Lowercase, underscore-separated
- **Values**: URL encoded
- **Multiple Values**: Comma-separated or repeated parameters
- **Boolean Values**: `true` or `false`

## Usage Patterns

### Resource Discovery

Start with collection resources to discover available entities:

```
1. cyberark://safes/                    # List all safes
2. cyberark://safes/ProductionSafe/     # Get safe details
3. cyberark://safes/ProductionSafe/accounts/  # List accounts in safe
4. cyberark://accounts/12345/           # Get specific account
```

### Search Workflows

Use search resources for finding specific entities:

```
1. cyberark://accounts/search?query=webserver
2. cyberark://accounts/search?safe_name=Production&platform_id=WinServerLocal
3. cyberark://accounts/search?username=admin
```

### Health Monitoring

Monitor system status with health resources:

```
1. cyberark://health/                   # Check system health
```

### Platform Management

Explore platform configurations:

```
1. cyberark://platforms/                # List all platforms
2. cyberark://platforms/WinServerLocal/ # Get platform details
3. cyberark://platforms/packages/       # Check import capabilities
```

## Advanced URI Features

### Query Parameter Combinations

Multiple parameters can be combined for complex searches:

```
cyberark://accounts/search?query=prod&safe_name=ProductionServers&platform_id=WinServerLocal
```

### URL Encoding Examples

Common encoding requirements:

| Character | Encoded | Example |
|-----------|---------|---------|
| Space | `%20` | `Development%20Environment` |
| & | `%26` | `R%26D%20Lab` |
| + | `%2B` | `Server%2B1` |
| # | `%23` | `DMZ%23Network` |

### Resource Relationships

URIs express hierarchical relationships:

```
cyberark://safes/ProductionServers/           # Parent safe
cyberark://safes/ProductionServers/accounts/  # Child accounts
cyberark://accounts/12345/                    # Specific account
```

## Error Handling

### Invalid URI Patterns

Invalid URIs return structured error responses:

```json
{
  "error": "resource_not_found",
  "message": "No resource handler found for URI: cyberark://invalid/",
  "available_patterns": ["health", "safes", "accounts", "platforms"]
}
```

### Common URI Errors

1. **Invalid Scheme**: 
   - Wrong: `http://safes/`
   - Correct: `cyberark://safes/`

2. **Invalid Category**:
   - Wrong: `cyberark://unknown/`
   - Correct: `cyberark://safes/`

3. **Malformed Identifiers**:
   - Wrong: `cyberark://safes//`
   - Correct: `cyberark://safes/SafeName/`

4. **Invalid Query Parameters**:
   - Wrong: `cyberark://accounts/search?invalid_param=value`
   - Correct: `cyberark://accounts/search?query=value`

## Best Practices

### URI Construction

1. **Use URL Encoding**: Always encode special characters
2. **Consistent Casing**: Preserve original case for identifiers
3. **Validate Input**: Check identifier formats before constructing URIs
4. **Handle Errors**: Gracefully handle invalid URI responses

### Client Implementation

1. **Start with Collections**: Use collection URIs for discovery
2. **Cache Appropriately**: Cache based on resource type and frequency
3. **Handle Relationships**: Follow related resource URIs for navigation
4. **Monitor Health**: Regularly check health resource for system status

### Performance Optimization

1. **Batch Requests**: Use collection resources instead of multiple entity requests
2. **Filter Early**: Use query parameters to reduce response size
3. **Cache Strategy**: Implement appropriate caching based on data volatility
4. **Pagination**: Handle large collections efficiently

## URI Evolution

### Versioning Strategy

- URIs remain stable across versions
- New resource types added without breaking existing URIs
- Query parameters extended in backward-compatible way
- Deprecation notices provided for any changes

### Future Extensions

Planned URI schema extensions:

1. **Audit Resources**: `cyberark://audit/`
2. **Session Resources**: `cyberark://sessions/`
3. **User Resources**: `cyberark://users/`
4. **Policy Resources**: `cyberark://policies/`

### Compatibility

- Current URIs will remain supported
- New features added through new URI patterns
- Optional parameters for enhanced functionality
- Client capability detection for feature support

---

For more information, see:
- [Resource Documentation](RESOURCES.md)
- [Server Capabilities](SERVER_CAPABILITIES.md)
- [Integration Guide](../README.md)