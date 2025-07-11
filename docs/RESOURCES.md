# CyberArk Privilege Cloud MCP Resources

This document provides comprehensive documentation for the CyberArk Privilege Cloud MCP Resources implementation, enabling URI-based access to CyberArk entities through the Model Context Protocol.

## Overview

MCP Resources provide a standardized way to access and represent CyberArk data objects using URI-based addressing. This enables MCP clients to browse, cache, and reference CyberArk entities like safes, accounts, and platforms through a hierarchical URI structure.

## Benefits

- **URI-based Addressing**: Direct access to CyberArk entities via URIs like `cyberark://safes/ProductionSafe/accounts/`
- **Resource Discovery**: Clients can enumerate all available resources
- **Efficient Caching**: Resources can be cached by URI for improved performance
- **Structured Navigation**: Hierarchical browsing of CyberArk infrastructure
- **Standardized Access**: Consistent API for accessing different entity types

## URI Schema

All CyberArk resources use the URI scheme `cyberark://` followed by a hierarchical path structure:

```
cyberark://{category}/[{identifier}/][{subcategory}/][?{query_params}]
```

### Resource Categories

- `health` - System health and status information
- `safes` - Safe management and browsing
- `accounts` - Account management and search
- `platforms` - Platform configuration and details

## Available Resources

### System Resources

#### Health Resource
- **URI**: `cyberark://health/`
- **Type**: Entity Resource
- **Description**: Provides real-time system health status and connectivity information
- **Content**:
  - System status (healthy/unhealthy/error)
  - Connectivity status to CyberArk APIs
  - Metrics (accessible safes count, response times)
  - Service information and capabilities
  - API endpoint configurations

**Example Response**:
```json
{
  "uri": "cyberark://health/",
  "type": "entity",
  "category": "health",
  "data": {
    "status": "healthy",
    "timestamp": "2024-01-15T10:30:00Z",
    "connectivity": {
      "cyberark_api": true,
      "authentication": true
    },
    "metrics": {
      "accessible_safes": 15,
      "response_time_ms": 120
    },
    "service_info": {
      "name": "CyberArk Privilege Cloud MCP Server",
      "version": "0.1.0",
      "capabilities": ["tools", "resources"]
    }
  }
}
```

### Safe Resources

#### Safe Collection Resource
- **URI**: `cyberark://safes/`
- **Type**: Collection Resource
- **Description**: Lists all accessible safes with summary information
- **Supports**: Filtering, search, sorting

**Example Response**:
```json
{
  "uri": "cyberark://safes/",
  "type": "collection",
  "category": "safes",
  "count": 3,
  "items": [
    {
      "name": "ProductionServers",
      "uri": "cyberark://safes/ProductionServers/",
      "description": "Production server accounts",
      "created_time": "2024-01-01T00:00:00Z",
      "number_of_versions_retention": 10
    }
  ]
}
```

#### Safe Entity Resource
- **URI**: `cyberark://safes/{safe_name}/`
- **Type**: Entity Resource
- **Description**: Detailed information about a specific safe
- **Related Resources**: Accounts within the safe, safe members

**Example Response**:
```json
{
  "uri": "cyberark://safes/ProductionServers/",
  "type": "entity",
  "category": "safes",
  "identifier": "ProductionServers",
  "data": {
    "name": "ProductionServers",
    "description": "Production server accounts",
    "location": "\\Production\\Servers",
    "created_time": "2024-01-01T00:00:00Z",
    "created_by": "admin@company.com",
    "number_of_versions_retention": 10,
    "auto_purge_enabled": true,
    "related_resources": {
      "accounts": "cyberark://safes/ProductionServers/accounts/",
      "members": "cyberark://safes/ProductionServers/members/"
    }
  }
}
```

#### Safe Accounts Collection
- **URI**: `cyberark://safes/{safe_name}/accounts/`
- **Type**: Collection Resource
- **Description**: All accounts stored within a specific safe
- **Supports**: Filtering, search, sorting by account properties

### Account Resources

#### Account Collection Resource
- **URI**: `cyberark://accounts/`
- **Type**: Collection Resource
- **Description**: Lists all accessible accounts across all safes
- **Supports**: Filtering, search, pagination, sorting

#### Account Entity Resource
- **URI**: `cyberark://accounts/{account_id}/`
- **Type**: Entity Resource
- **Description**: Detailed information about a specific account
- **Related Resources**: Parent safe, platform configuration

**Example Response**:
```json
{
  "uri": "cyberark://accounts/12345/",
  "type": "entity",
  "category": "accounts",
  "identifier": "12345",
  "data": {
    "id": "12345",
    "name": "webserver01-admin",
    "address": "webserver01.prod.corp.com",
    "user_name": "administrator",
    "platform_id": "WinServerLocal",
    "safe_name": "ProductionServers",
    "secret_type": "password",
    "secret_management": {
      "automatic_management_enabled": true,
      "status": "success",
      "last_verified": "2024-01-10T14:30:00Z"
    },
    "platform_account_properties": {
      "LogonDomain": "PROD",
      "Port": "3389"
    },
    "related_resources": {
      "safe": "cyberark://safes/ProductionServers/",
      "platform": "cyberark://platforms/WinServerLocal/"
    }
  }
}
```

#### Account Search Resource
- **URI**: `cyberark://accounts/search?query={search_terms}&safe_name={safe}&...`
- **Type**: Collection Resource
- **Description**: Search accounts with various query parameters and filters
- **Query Parameters**:
  - `query` - Free text search across account properties
  - `safe_name` - Filter by specific safe
  - `username` - Filter by username
  - `address` - Filter by address
  - `platform_id` - Filter by platform

### Platform Resources

#### Platform Collection Resource
- **URI**: `cyberark://platforms/`
- **Type**: Collection Resource
- **Description**: Lists all available platforms for account management with **basic platform information**
- **Supports**: Filtering by system type, active status, advanced search
- **Performance**: Optimized for fast response times (<2 seconds)
- **Features**: 
  - Basic platform information (id, name, systemType, active status)
  - Raw API data preservation (no field transformations)
  - Single API call for optimal performance
  - Consistent field naming from CyberArk API

**Example Basic Response**:
```json
{
  "uri": "cyberark://platforms/",
  "type": "collection",
  "category": "platforms",
  "count": 2,
  "metadata": {
    "supports_complete_info": false,
    "data_source": "cyberark_platforms_api_basic",
    "field_conversion": "none - preserves raw API data exactly",
    "performance_optimized": true,
    "note": "Optimized for performance using single API call"
  },
  "items": [
    {
      "id": "WinServerLocal",
      "name": "Windows Server Local",
      "uri": "cyberark://platforms/WinServerLocal/",
      "systemType": "Windows",
      "active": true,
      "description": "Windows Server for local accounts",
      "platformBaseID": "WinServerLocal",
      "platformType": "Regular",
      "allowManualChange": true,
      "performPeriodicChange": false,
      "allowManualVerification": true,
      "requirePrivilegedSessionMonitoringAndIsolation": true,
      "recordAndSaveSessionActivity": true,
      "PSMServerID": "PSMServer_1"
    }
  ]
}
```

#### Platform Entity Resource
- **URI**: `cyberark://platforms/{platform_id}/`
- **Type**: Entity Resource  
- **Description**: **Comprehensive platform configuration with complete detailed information**
- **Data Sources**: Combines basic platform info + detailed Policy INI configuration (66+ fields)
- **Performance**: ~200ms per platform for complete detailed information
- **Related Resources**: Accounts using this platform
- **Raw Data Preservation**: All field names and values preserved exactly as returned by CyberArk APIs

**Key Features**:
- **Complete Platform Details**: Combines data from both platforms list API and platform details API
- **Comprehensive Policy Configuration**: 66+ detailed policy fields including credentials management, session settings, workflows
- **Raw API Data Integrity**: No field transformations - preserves original CamelCase names and string values
- **Graceful Degradation**: Falls back to basic platform info if detailed access is unavailable
- **Enhanced Error Handling**: Specific guidance for 403/404 errors with troubleshooting context

**Example Response**:
```json
{
  "uri": "cyberark://platforms/WinServerLocal/",
  "type": "entity",
  "category": "platforms", 
  "identifier": "WinServerLocal",
  "data": {
    "id": "WinServerLocal",
    "name": "Windows Server Local",
    "systemType": "Windows",
    "active": true,
    "platformType": "Regular",
    "description": "Windows Server Local Accounts",
    
    // Detailed Policy INI configuration (66+ fields preserved exactly as returned)
    "PasswordLength": "12",
    "ResetOveridesMinValidity": "Yes", 
    "XMLFile": "Yes",
    "FromHour": "-1",
    "PSMServerID": "PSMServer_abc123",
    "PolicyType": "Regular",
    "platformBaseID": "WinDomain",
    
    "ConnectionComponents": [
      {
        "PSMServerID": "PSM01",
        "Name": "PSM-RDP", 
        "ConnectionMethod": "RDP",
        "Enabled": true
      }
    ],
    
    // Additional detailed policy fields available...
    // All field names and values preserved exactly as returned by CyberArk APIs
    
    "related_resources": {
      "accounts_using_platform": "cyberark://accounts/?platform_id=WinServerLocal"
    }
  }
}
```

#### Platform Packages Resource
- **URI**: `cyberark://platforms/packages/`
- **Type**: Collection Resource
- **Description**: Information about platform package import capabilities
- **Note**: Currently provides import capability information; full package listing is a future enhancement

## Resource Metadata

Each resource includes metadata providing information about:

- **Resource Type**: collection, entity, or subcollection
- **Capabilities**: What operations are supported (filtering, search, updates)
- **Related Resources**: Links to related resource URIs
- **Permissions**: Required permissions for access
- **Data Source**: API endpoints and data sources

## Client Integration

### MCP Client Usage

Resources can be discovered and accessed through any MCP-compatible client:

1. **List Available Resources**:
   ```
   mcp.list_resources()
   ```

2. **Read Specific Resource**:
   ```
   mcp.read_resource("cyberark://safes/ProductionServers/")
   ```

3. **Browse Resource Hierarchy**:
   - Start with collections: `cyberark://safes/`
   - Navigate to entities: `cyberark://safes/ProductionServers/`
   - Access subcollections: `cyberark://safes/ProductionServers/accounts/`

### Caching Recommendations

- **Health Resource**: Cache for 30 seconds (real-time data)
- **Safe Collections**: Cache for 5 minutes
- **Account Collections**: Cache for 2 minutes
- **Platform Resources**: Cache for 1 hour (relatively static)
- **Individual Entities**: Cache for 5 minutes

### Error Handling

Resources return structured error information when issues occur:

```json
{
  "error": "resource_not_found",
  "message": "No resource handler found for URI: cyberark://unknown/",
  "uri": "cyberark://unknown/",
  "available_patterns": ["health", "safes", "accounts", "platforms"]
}
```

Common error types:
- `resource_not_found` - URI pattern not recognized
- `resource_read_error` - Error reading resource content
- `server_error` - CyberArk API or authentication error

## Raw API Data Preservation

### Overview

The CyberArk MCP Server preserves all API data exactly as returned by CyberArk APIs, ensuring complete fidelity and data integrity. No field name conversions, value transformations, or data modifications are applied.

### Key Principles

#### Complete Data Fidelity
- **No Field Name Conversion**: Original CamelCase field names preserved exactly (e.g., `PSMServerID`, `PolicyType`)
- **No Value Transformation**: All values preserved as returned by API (`"Yes"` stays `"Yes"`, `"12"` stays `"12"`)
- **Complete Data Integrity**: Empty/null values, special characters, and all original formatting preserved
- **API Response Fidelity**: Zero modification of CyberArk API responses

#### Raw Data Examples

**Original CyberArk API Response** (preserved exactly):
```json
{
  "id": "WinServerLocal",
  "name": "Windows Server Local",
  "systemType": "Windows",
  "active": true,
  "PolicyID": "WinServerLocal",
  "PolicyName": "Windows Server Local",
  "PSMServerID": "PSMServer_abc123",
  "AllowManualChange": "Yes",
  "RequirePasswordChangeEveryXDays": "90",
  "PasswordLength": "12",
  "ResetOveridesMinValidity": "Yes",
  "FromHour": "-1",
  "platformBaseID": "WinDomain"
}
```

### Benefits of Raw Data Preservation

#### Data Integrity
- **Complete Information**: No data loss through transformation
- **Original Context**: Field names and values maintain CyberArk context
- **Debugging Capability**: Easier to correlate with CyberArk documentation
- **API Consistency**: Direct correlation with CyberArk API responses

#### Performance Benefits
- **Zero Transformation Overhead**: No processing time spent on field conversion
- **Memory Efficiency**: No duplicate field storage
- **Reduced Complexity**: Simpler data pipeline
- **Faster Processing**: Direct API response handling

#### Client Flexibility
- **Client-Side Control**: Clients can apply their own transformations if needed
- **Multiple Client Support**: Different clients can handle data differently
- **Future Compatibility**: Changes to transformation logic don't affect data
- **Original Documentation**: Client developers can use CyberArk API docs directly

## Performance Considerations

### Optimization Features

- **Lazy Loading**: Resource content loaded on-demand
- **Efficient API Usage**: Leverages existing CyberArk API integrations
- **Response Caching**: Built-in caching mechanisms
- **Pagination Support**: Large collections can be paginated

### Performance Targets

- Resource discovery: < 100ms
- Individual resource access: < 500ms
- Collection resources: < 1000ms
- Large collections (>100 items): < 2000ms

## Security

### Access Control

- All resources respect CyberArk API permissions
- Resource access requires valid authentication
- Safe-based access control enforced
- Account permissions validated per resource

### Data Protection

- Sensitive data filtering in resource content
- No password or secret exposure in resources
- Audit logging for resource access
- URI validation and sanitization

## Future Enhancements

### Planned Features

1. **Real-time Updates**: WebSocket-based resource updates
2. **Advanced Filtering**: Complex query capabilities
3. **Resource Mutations**: Support for creating/updating resources
4. **Extended Metadata**: More detailed resource relationships
5. **Performance Metrics**: Resource access analytics

### API Evolution

- Backward compatibility maintained
- Version negotiation for new features
- Gradual feature rollout
- Client capability detection

## Troubleshooting

### Common Issues

1. **Resource Not Found**:
   - Verify URI pattern is correct
   - Check available patterns with `list_resources()`
   - Ensure proper authentication

2. **Permission Denied**:
   - Verify CyberArk API permissions
   - Check safe access rights
   - Validate authentication token

3. **Slow Performance**:
   - Enable resource caching
   - Check network connectivity
   - Verify API response times

### Debug Information

Enable debug logging to see:
- Resource URI parsing
- API call timings
- Cache hit/miss ratios
- Authentication status

---

For more information, see:
- [URI Schema Reference](URI_SCHEMA.md)
- [Server Capabilities](SERVER_CAPABILITIES.md)
- [MCP Integration Guide](../README.md#mcp-integration)