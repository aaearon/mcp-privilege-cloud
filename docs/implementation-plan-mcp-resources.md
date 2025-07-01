# Implementation Plan: Missing MCP Resources Implementation

**Priority**: High  
**Estimated Effort**: 6-8 hours  
**Complexity**: Medium-High  

## Problem Statement

The current MCP server implementation only provides tools (functions) but lacks MCP resources. Resources provide a standardized way to access and represent data objects, enabling clients to browse, cache, and reference CyberArk entities using URI-based addressing.

## Current State Analysis

### Missing Capabilities
1. **No Resource Discovery**: Clients cannot browse available CyberArk objects
2. **No URI-based Access**: No standardized way to reference specific accounts, safes, or platforms
3. **Limited Caching**: Clients cannot efficiently cache frequently accessed data
4. **Poor Data Navigation**: No hierarchical browsing of CyberArk structure

### MCP Resource Benefits
- **URI-based Addressing**: `cyberark://safes/ProductionSafe/accounts/webserver01`
- **Resource Discovery**: Clients can enumerate available resources
- **Efficient Caching**: Resources can be cached by URI
- **Structured Navigation**: Hierarchical resource relationships

## Resource Architecture Design

### Resource URI Schema
```
cyberark://
├── safes/                          # List all accessible safes
│   ├── {safe_name}/               # Specific safe details
│   │   ├── accounts/              # Accounts in this safe
│   │   └── members/               # Safe members (future)
├── accounts/                       # List all accessible accounts
│   ├── {account_id}/              # Specific account details
│   └── search?query={search}      # Search results as resource
├── platforms/                      # List all platforms
│   ├── {platform_id}/             # Specific platform details
│   └── packages/                  # Platform packages (future)
└── health/                         # Health check as resource
```

### Resource Types
1. **Collection Resources**: Lists of objects (safes, accounts, platforms)
2. **Entity Resources**: Individual objects with full details
3. **Query Resources**: Search results and filtered views
4. **Status Resources**: Health checks and system status

## Implementation Strategy

### Phase 1: Resource Infrastructure
1. **Create Resource Framework**
   - Resource base classes and utilities
   - URI parsing and validation
   - Resource content formatting

2. **Resource Registry**
   - Central resource discovery mechanism
   - URI pattern matching
   - Resource metadata management

### Phase 2: Core Resources Implementation
1. **Safe Resources**
   - Safe list resource
   - Individual safe resources
   - Safe account collections

2. **Account Resources**
   - Account list resource
   - Individual account resources
   - Account search resources

### Phase 3: Platform and System Resources
1. **Platform Resources**
   - Platform list resource
   - Individual platform resources

2. **System Resources**
   - Health check resource
   - System status resources

## Detailed Implementation Steps

### Step 1: Create Resource Infrastructure
File: `src/mcp_privilege_cloud/resources/`
```bash
mkdir -p src/mcp_privilege_cloud/resources
touch src/mcp_privilege_cloud/resources/__init__.py
touch src/mcp_privilege_cloud/resources/base.py
touch src/mcp_privilege_cloud/resources/registry.py
touch src/mcp_privilege_cloud/resources/safes.py
touch src/mcp_privilege_cloud/resources/accounts.py
touch src/mcp_privilege_cloud/resources/platforms.py
touch src/mcp_privilege_cloud/resources/system.py
```

### Step 2: Resource Base Classes
File: `src/mcp_privilege_cloud/resources/base.py`
- `BaseResource` - Abstract base for all resources
- `CollectionResource` - Base for list-type resources
- `EntityResource` - Base for individual object resources
- `ResourceURI` - URI parsing and validation utilities

### Step 3: Resource Registry System
File: `src/mcp_privilege_cloud/resources/registry.py`
- `ResourceRegistry` - Central resource management
- URI pattern matching and routing
- Resource discovery and enumeration
- Metadata management for resources

### Step 4: Safe Resources Implementation
File: `src/mcp_privilege_cloud/resources/safes.py`

#### Safe Collection Resource
- **URI**: `cyberark://safes/`
- **Content**: List of all accessible safes with summary info
- **Format**: JSON with safe names, descriptions, member counts

#### Individual Safe Resource
- **URI**: `cyberark://safes/{safe_name}/`
- **Content**: Complete safe details including permissions, settings
- **Format**: Detailed JSON with full safe metadata

#### Safe Account Collection
- **URI**: `cyberark://safes/{safe_name}/accounts/`
- **Content**: All accounts within the specified safe
- **Format**: Account list with safe-specific context

### Step 5: Account Resources Implementation
File: `src/mcp_privilege_cloud/resources/accounts.py`

#### Account Collection Resource
- **URI**: `cyberark://accounts/`
- **Content**: List of all accessible accounts across safes
- **Format**: Account summaries with safe associations

#### Individual Account Resource
- **URI**: `cyberark://accounts/{account_id}/`
- **Content**: Complete account details and properties
- **Format**: Full account object with platform properties

#### Account Search Resource
- **URI**: `cyberark://accounts/search?query={search_terms}`
- **Content**: Search results matching query parameters
- **Format**: Filtered account list with search metadata

### Step 6: Platform Resources Implementation
File: `src/mcp_privilege_cloud/resources/platforms.py`

#### Platform Collection Resource
- **URI**: `cyberark://platforms/`
- **Content**: List of all available platforms
- **Format**: Platform summaries with capabilities

#### Individual Platform Resource
- **URI**: `cyberark://platforms/{platform_id}/`
- **Content**: Complete platform configuration and properties
- **Format**: Full platform details with connection components

### Step 7: System Resources Implementation
File: `src/mcp_privilege_cloud/resources/system.py`

#### Health Resource
- **URI**: `cyberark://health/`
- **Content**: System health status and connectivity
- **Format**: Health check results with timestamps

## MCP Server Integration

### Resource Registration
Update `src/mcp_privilege_cloud/mcp_server.py`:
1. Import resource registry
2. Register all resource handlers
3. Implement `list_resources()` handler
4. Implement `read_resource()` handler

### Resource Handler Pattern
```python
@mcp.list_resources()
async def list_resources() -> list[Resource]:
    """List all available CyberArk resources"""
    return await resource_registry.list_all_resources()

@mcp.read_resource()
async def read_resource(uri: AnyUrl) -> str:
    """Read specific CyberArk resource by URI"""
    return await resource_registry.read_resource(uri)
```

## Resource Content Formats

### Safe Resource Example
```json
{
  "uri": "cyberark://safes/ProductionServers/",
  "name": "ProductionServers",
  "description": "Production server accounts",
  "created": "2024-01-15T10:30:00Z",
  "members": 5,
  "accounts": 23,
  "permissions": {
    "canList": true,
    "canAdd": true,
    "canUpdate": false
  },
  "settings": {
    "maxVersions": 10,
    "requiredDualControl": true
  }
}
```

### Account Resource Example
```json
{
  "uri": "cyberark://accounts/12345/",
  "id": "12345",
  "name": "webserver01-admin",
  "address": "webserver01.prod.corp.com",
  "userName": "administrator",
  "safeName": "ProductionServers",
  "platformId": "WinServerLocal",
  "lastPasswordChange": "2024-01-10T14:30:00Z",
  "nextPasswordChange": "2024-02-10T14:30:00Z",
  "status": "active",
  "platformProperties": {
    "LogonDomain": "PROD",
    "Port": "3389"
  }
}
```

## Testing Requirements

### Unit Tests
- Resource URI parsing and validation
- Resource content generation
- Resource registry functionality
- Individual resource implementations

### Integration Tests
- End-to-end resource retrieval
- Resource discovery through MCP client
- Resource content accuracy
- Performance testing for large collections

### Resource-Specific Tests
- Safe resource hierarchy navigation
- Account resource search functionality
- Platform resource completeness
- System resource real-time updates

## Documentation Requirements

### New Documentation Files
1. `docs/RESOURCES.md` - Comprehensive resource documentation
2. `docs/URI_SCHEMA.md` - URI patterns and examples
3. Update `SERVER_CAPABILITIES.md` - Add resource capabilities

### Documentation Content
- Complete URI schema reference
- Resource content format specifications
- Usage examples for each resource type
- Client integration patterns
- Caching recommendations

## Performance Considerations

### Optimization Strategies
1. **Resource Caching**: Cache frequently accessed resources
2. **Lazy Loading**: Load resource content on-demand
3. **Pagination**: Implement pagination for large collections
4. **Filtering**: Server-side filtering for collection resources

### Monitoring Requirements
- Resource access patterns
- Cache hit rates
- Response times by resource type
- Memory usage for resource caching

## Security Considerations

### Access Control
- Resource-level permission checking
- URI validation and sanitization
- Audit logging for resource access
- Rate limiting for resource requests

### Data Exposure
- Sensitive data filtering in resource content
- Safe-based access control enforcement
- Account permission validation
- Platform visibility restrictions

## Validation Criteria

### Success Metrics
1. **Resource Discovery**: Clients can enumerate all available resources
2. **URI Navigation**: All URI patterns work correctly
3. **Content Accuracy**: Resource content matches API data
4. **Performance**: Resource access < 500ms response time
5. **Client Integration**: MCP clients can browse resources effectively

### Testing Checklist
- [ ] All resource URI patterns implemented
- [ ] Resource discovery working in MCP Inspector
- [ ] Content format validation passes
- [ ] Performance benchmarks met
- [ ] Security access controls enforced
- [ ] Documentation complete and accurate

## Risk Mitigation

### Implementation Risks
- **Performance Impact**: Large resource collections might be slow
  - *Mitigation*: Implement pagination and caching
- **Memory Usage**: Resource caching might consume memory
  - *Mitigation*: LRU cache with size limits
- **API Rate Limits**: Too many resource requests might hit limits
  - *Mitigation*: Intelligent caching and batching

### Security Risks
- **Data Exposure**: Resources might expose sensitive information
  - *Mitigation*: Careful content filtering and access control
- **URI Injection**: Malformed URIs might cause issues
  - *Mitigation*: Strict URI validation and sanitization

## Dependencies

### Existing Dependencies
- MCP framework (already installed)
- Pydantic for data validation
- httpx for API requests

### New Dependencies
- No additional external dependencies required
- Leverage existing CyberArk API integration

## Rollout Strategy

### Phase 1: Infrastructure (Days 1-2)
- Create resource framework and base classes
- Implement resource registry system
- Set up testing infrastructure

### Phase 2: Core Resources (Days 3-5)
- Implement safe and account resources
- Add resource discovery mechanisms
- Create comprehensive tests

### Phase 3: Extended Resources (Days 6-7)
- Add platform and system resources
- Implement advanced features (search, filtering)
- Performance optimization

### Phase 4: Integration & Documentation (Day 8)
- MCP server integration
- Complete documentation
- Client integration testing

## Success Criteria

1. ✅ Complete URI schema implementation covering all CyberArk entities
2. ✅ Resource discovery functionality working in MCP clients
3. ✅ All resources return accurate, well-formatted content
4. ✅ Performance targets met (< 500ms response time)
5. ✅ Security access controls properly enforced
6. ✅ Comprehensive documentation with examples
7. ✅ Client integration validated with MCP Inspector

---

**Next Steps**: After approval, begin with Phase 1 infrastructure setup and resource framework implementation.