# Implementation Plan: Tool Parameter Validation Enhancement

**Priority**: High  
**Estimated Effort**: 3-4 hours  
**Complexity**: Medium  

## Problem Statement

Current MCP tools have minimal parameter validation, relying only on basic Python type hints. This leads to runtime errors, poor user experience, and unclear error messages when invalid parameters are provided. The tools need comprehensive parameter validation with clear error messages and proper constraint checking.

## Current State Analysis

### Issues Identified
1. **No Input Validation**: Tools accept any string values without format checking
2. **Runtime Errors**: Invalid parameters cause exceptions during API calls
3. **Poor Error Messages**: Generic errors don't help users understand requirements
4. **No Constraint Checking**: No validation of parameter relationships or business rules
5. **Missing Required Parameter Enforcement**: Optional parameters sometimes required in context

### Impact Areas
- User experience degradation
- Debugging difficulty for integrators
- Potential security vulnerabilities
- Inconsistent error handling across tools

## Validation Strategy Design

### Validation Layers
1. **Syntax Validation**: Format, length, character constraints
2. **Semantic Validation**: Business rule validation and parameter relationships
3. **Security Validation**: Input sanitization and injection prevention
4. **Context Validation**: Environment-specific constraint checking

### Validation Framework
- **Pydantic Models**: Structured parameter validation with field constraints
- **Custom Validators**: Business logic validation for CyberArk-specific rules
- **Error Standardization**: Consistent error messages and response formats
- **Async Validation**: Non-blocking validation for complex checks

## Implementation Strategy

### Phase 1: Validation Framework
1. **Create Validation Infrastructure**
   - Base validation classes and utilities
   - Error message standardization
   - Validation result structures

2. **Parameter Model Definitions**
   - Pydantic models for each tool's parameters
   - Field-level validation rules
   - Cross-field validation logic

### Phase 2: Tool-Specific Validation
1. **Account Management Validation**
   - Account creation parameter validation
   - Search parameter validation
   - Account ID format validation

2. **Safe Management Validation**
   - Safe name validation
   - Permission parameter validation
   - Search criteria validation

### Phase 3: Platform and System Validation
1. **Platform Validation**
   - Platform ID format validation
   - Platform package validation
   - Import parameter validation

2. **System Validation**
   - Health check parameter validation
   - Configuration parameter validation

## Detailed Implementation Steps

### Step 1: Create Validation Infrastructure
File Structure:
```bash
mkdir -p src/mcp_privilege_cloud/validation
touch src/mcp_privilege_cloud/validation/__init__.py
touch src/mcp_privilege_cloud/validation/base.py
touch src/mcp_privilege_cloud/validation/models.py
touch src/mcp_privilege_cloud/validation/validators.py
touch src/mcp_privilege_cloud/validation/errors.py
```

### Step 2: Base Validation Classes
File: `src/mcp_privilege_cloud/validation/base.py`

```python
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator

class ValidationError(Exception):
    """Base validation error"""
    def __init__(self, field: str, message: str, value: Any = None):
        self.field = field
        self.message = message
        self.value = value
        super().__init__(f"{field}: {message}")

class BaseParameterModel(BaseModel):
    """Base class for all parameter validation models"""
    
    class Config:
        extra = "forbid"  # Prevent unknown parameters
        validate_assignment = True
        use_enum_values = True
        
    def validate_business_rules(self) -> List[ValidationError]:
        """Override to implement business rule validation"""
        return []
    
    async def validate_async(self) -> List[ValidationError]:
        """Override to implement async validation (e.g., API checks)"""
        return []

class ValidatorMixin:
    """Mixin for common validation utilities"""
    
    @staticmethod
    def validate_cyberark_name(name: str, field_name: str) -> str:
        """Validate CyberArk object names (safes, accounts, etc.)"""
        if not name or not name.strip():
            raise ValidationError(field_name, "Name cannot be empty")
        
        if len(name) > 255:
            raise ValidationError(field_name, "Name too long (max 255 characters)")
            
        # CyberArk naming restrictions
        invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
        for char in invalid_chars:
            if char in name:
                raise ValidationError(field_name, f"Name contains invalid character: {char}")
                
        return name.strip()
```

### Step 3: Parameter Models for Each Tool
File: `src/mcp_privilege_cloud/validation/models.py`

```python
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator, root_validator
from enum import Enum

class SecretType(str, Enum):
    PASSWORD = "password"  
    KEY = "key"

class ListAccountsParams(BaseParameterModel):
    """Parameter validation for list_accounts tool"""
    
    safe_name: Optional[str] = Field(
        None,
        description="Safe name to filter accounts",
        min_length=1,
        max_length=255
    )
    
    username: Optional[str] = Field(
        None,
        description="Username to filter accounts",
        min_length=1,
        max_length=255
    )
    
    address: Optional[str] = Field(
        None,
        description="Address/hostname to filter accounts",
        min_length=1,
        max_length=255
    )
    
    @validator('safe_name')
    def validate_safe_name(cls, v):
        if v is not None:
            return ValidatorMixin.validate_cyberark_name(v, 'safe_name')
        return v

class CreateAccountParams(BaseParameterModel):
    """Parameter validation for create_account tool"""
    
    platform_id: str = Field(
        ...,
        description="Platform ID for the account",
        min_length=1,
        max_length=100,
        regex=r'^[a-zA-Z0-9_-]+$'
    )
    
    safe_name: str = Field(
        ...,
        description="Safe where account will be created",
        min_length=1,
        max_length=255
    )
    
    name: Optional[str] = Field(
        None,
        description="Account name/identifier",
        max_length=255
    )
    
    address: Optional[str] = Field(
        None,
        description="Target address/hostname", 
        max_length=255
    )
    
    user_name: Optional[str] = Field(
        None,
        description="Username for the account",
        min_length=1,
        max_length=255
    )
    
    secret: Optional[str] = Field(
        None,
        description="Password or SSH key",
        min_length=1
    )
    
    secret_type: Optional[SecretType] = Field(
        SecretType.PASSWORD,
        description="Type of secret"
    )
    
    platform_account_properties: Optional[Dict[str, Any]] = Field(
        None,
        description="Platform-specific properties"
    )
    
    secret_management: Optional[Dict[str, Any]] = Field(
        None,
        description="Secret management configuration"
    )
    
    remote_machines_access: Optional[Dict[str, Any]] = Field(
        None,
        description="Remote access configuration"
    )
    
    @validator('safe_name', 'name')
    def validate_names(cls, v, field):
        if v is not None:
            return ValidatorMixin.validate_cyberark_name(v, field.name)
        return v
    
    @validator('address')
    def validate_address(cls, v):
        if v is not None:
            # Basic hostname/IP validation
            if len(v.strip()) == 0:
                raise ValidationError('address', 'Address cannot be empty')
            # Could add more sophisticated hostname/IP validation
        return v
    
    @validator('secret')
    def validate_secret(cls, v, values):
        if v is not None:
            secret_type = values.get('secret_type', SecretType.PASSWORD)
            
            if secret_type == SecretType.PASSWORD:
                # Password complexity validation
                if len(v) < 8:
                    raise ValidationError('secret', 'Password must be at least 8 characters')
                    
            elif secret_type == SecretType.KEY:
                # SSH key format validation
                if not (v.startswith('ssh-') or v.startswith('-----BEGIN')):
                    raise ValidationError('secret', 'Invalid SSH key format')
                    
        return v
    
    @root_validator
    def validate_required_fields(cls, values):
        """Validate business rules across fields"""
        # If secret is provided, secret_type should be specified
        if values.get('secret') and not values.get('secret_type'):
            values['secret_type'] = SecretType.PASSWORD
            
        # If creating account, either name or user_name should be provided
        if not values.get('name') and not values.get('user_name'):
            raise ValidationError('name', 'Either name or user_name must be provided')
            
        return values

class SearchAccountsParams(BaseParameterModel):
    """Parameter validation for search_accounts tool"""
    
    keywords: Optional[str] = Field(
        None,
        description="Search keywords",
        min_length=1,
        max_length=500
    )
    
    safe_name: Optional[str] = Field(
        None,
        description="Filter by safe name",
        min_length=1,
        max_length=255
    )
    
    username: Optional[str] = Field(
        None,
        description="Filter by username",
        min_length=1,
        max_length=255
    )
    
    address: Optional[str] = Field(
        None,
        description="Filter by address",
        min_length=1,
        max_length=255
    )
    
    platform_id: Optional[str] = Field(
        None,
        description="Filter by platform ID",
        min_length=1,
        max_length=100
    )
    
    @root_validator
    def validate_search_criteria(cls, values):
        """Ensure at least one search criterion is provided"""
        search_fields = ['keywords', 'safe_name', 'username', 'address', 'platform_id']
        if not any(values.get(field) for field in search_fields):
            raise ValidationError('search', 'At least one search criterion must be provided')
        return values

class ListSafesParams(BaseParameterModel):
    """Parameter validation for list_safes tool"""
    
    search: Optional[str] = Field(
        None,
        description="Search term for safe names",
        min_length=1,
        max_length=255  
    )
    
    offset: Optional[int] = Field(
        0,
        description="Pagination offset",
        ge=0,
        le=10000
    )
    
    limit: Optional[int] = Field(
        25,
        description="Results per page",
        ge=1,
        le=1000  
    )
    
    sort: Optional[str] = Field(
        None,
        description="Sort field and direction",
        regex=r'^[a-zA-Z_]+(\s+(asc|desc))?$'
    )
    
    include_accounts: Optional[bool] = Field(
        False,
        description="Include account counts"
    )
    
    extended_details: Optional[bool] = Field(
        False,
        description="Include extended safe details"
    )
```

### Step 4: Custom Validators
File: `src/mcp_privilege_cloud/validation/validators.py`

```python
from typing import Optional, Any
import re
import ipaddress

class CyberArkValidators:
    """Collection of CyberArk-specific validators"""
    
    @staticmethod
    def validate_account_id(account_id: str) -> bool:
        """Validate CyberArk account ID format"""
        if not account_id:
            return False
        # Account IDs are typically numeric strings
        return account_id.isdigit() and len(account_id) <= 20
    
    @staticmethod
    def validate_platform_id(platform_id: str) -> bool:
        """Validate platform ID format"""
        if not platform_id:
            return False
        # Platform IDs follow specific naming conventions
        pattern = r'^[a-zA-Z][a-zA-Z0-9_-]*$'
        return re.match(pattern, platform_id) and len(platform_id) <= 100
    
    @staticmethod
    def validate_safe_name(safe_name: str) -> bool:
        """Validate safe name format"""
        if not safe_name:
            return False
        # Safe names have specific character restrictions
        invalid_chars = '<>:"/\\|?*'
        return not any(char in safe_name for char in invalid_chars)
    
    @staticmethod
    def validate_ip_or_hostname(address: str) -> bool:
        """Validate IP address or hostname format"""
        if not address:
            return False
            
        # Try IP address validation first
        try:
            ipaddress.ip_address(address)
            return True
        except ValueError:
            pass
            
        # Hostname validation
        hostname_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$'
        return re.match(hostname_pattern, address) is not None
    
    @staticmethod
    async def validate_safe_exists(safe_name: str, server) -> bool:
        """Async validation to check if safe exists"""
        try:
            await server.get_safe_details(safe_name)
            return True
        except Exception:
            return False
    
    @staticmethod  
    async def validate_platform_exists(platform_id: str, server) -> bool:
        """Async validation to check if platform exists"""
        try:
            await server.get_platform_details(platform_id)
            return True
        except Exception:
            return False
```

### Step 5: Integration with MCP Tools
Update `src/mcp_privilege_cloud/mcp_server.py`:

```python
from .validation.models import (
    ListAccountsParams, CreateAccountParams, SearchAccountsParams,
    ListSafesParams, GetAccountDetailsParams
)
from .validation.errors import ValidationError

async def validate_parameters(param_class, **kwargs):
    """Validate parameters using Pydantic model"""
    try:
        # Basic validation
        params = param_class(**kwargs)
        
        # Business rule validation
        business_errors = params.validate_business_rules()
        if business_errors:
            raise ValidationError("validation", "; ".join([str(e) for e in business_errors]))
        
        # Async validation
        async_errors = await params.validate_async()
        if async_errors:
            raise ValidationError("validation", "; ".join([str(e) for e in async_errors]))
            
        return params
        
    except ValidationError as e:
        logger.error(f"Parameter validation failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Validation error: {e}")
        raise ValidationError("validation", f"Invalid parameters: {str(e)}")

# Updated tool with validation
@mcp.tool()
async def create_account(
    platform_id: str,
    safe_name: str,
    name: Optional[str] = None,
    address: Optional[str] = None,
    user_name: Optional[str] = None,
    secret: Optional[str] = None,
    secret_type: Optional[str] = None,
    platform_account_properties: Optional[Dict[str, Any]] = None,
    secret_management: Optional[Dict[str, Any]] = None,
    remote_machines_access: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create account with comprehensive parameter validation"""
    
    # Validate parameters
    params = await validate_parameters(
        CreateAccountParams,
        platform_id=platform_id,
        safe_name=safe_name,
        name=name,
        address=address,
        user_name=user_name,
        secret=secret,
        secret_type=secret_type,
        platform_account_properties=platform_account_properties,
        secret_management=secret_management,
        remote_machines_access=remote_machines_access
    )
    
    try:
        server = CyberArkMCPServer.from_environment()
        account = await server.create_account(**params.dict(exclude_none=True))
        logger.info(f"Created account with ID: {account.get('id', 'unknown')}")
        return account
    except Exception as e:
        logger.error(f"Error creating account: {e}")
        raise
```

### Step 6: Error Handling Enhancement
File: `src/mcp_privilege_cloud/validation/errors.py`

```python
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class ValidationErrorDetail:
    field: str
    message: str
    value: Optional[Any] = None
    constraint: Optional[str] = None

class ValidationException(Exception):
    """Enhanced validation exception with detailed error information"""
    
    def __init__(self, errors: List[ValidationErrorDetail]):
        self.errors = errors
        self.message = self._format_errors()
        super().__init__(self.message)
    
    def _format_errors(self) -> str:
        """Format errors into user-friendly message"""
        if len(self.errors) == 1:
            error = self.errors[0]
            return f"Validation failed for '{error.field}': {error.message}"
        
        error_messages = []
        for error in self.errors:
            error_messages.append(f"  - {error.field}: {error.message}")
        
        return f"Validation failed:\n" + "\n".join(error_messages)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "error": "validation_failed",
            "message": self.message,
            "details": [
                {
                    "field": error.field,
                    "message": error.message,
                    "value": error.value,
                    "constraint": error.constraint
                }
                for error in self.errors
            ]
        }
```

## Testing Requirements

### Unit Tests
File: `tests/test_parameter_validation.py`
- Parameter model validation tests
- Custom validator function tests
- Error handling and message formatting tests
- Edge case validation tests

### Integration Tests
- End-to-end tool execution with validation
- Error propagation through MCP layer
- Performance impact measurement
- Real-world parameter validation scenarios

### Validation Test Categories
1. **Format Validation**: Character restrictions, length limits, pattern matching
2. **Business Rule Validation**: Cross-field validation, contextual requirements
3. **Security Validation**: Input sanitization, injection prevention
4. **Async Validation**: External dependency validation (safe/platform existence)

## Documentation Requirements

### Documentation Updates
1. `docs/PARAMETER_VALIDATION.md` - Comprehensive validation documentation
2. `SERVER_CAPABILITIES.md` - Update with validation details
3. `docs/ERROR_HANDLING.md` - Error response format documentation
4. Tool docstrings - Add validation examples and constraints

### Documentation Content
- Parameter constraint reference for each tool
- Validation error message catalog
- Best practices for parameter validation
- Custom validator development guide

## Performance Considerations

### Optimization Strategies
1. **Validation Caching**: Cache validation results for repeated parameters
2. **Lazy Validation**: Only perform expensive validation when needed
3. **Parallel Validation**: Run independent validations in parallel
4. **Smart Async Validation**: Batch async validations to reduce API calls

### Performance Monitoring
- Track validation execution time per tool
- Monitor validation cache hit rates
- Measure impact on overall tool response time
- Alert on validation performance degradation

## Security Enhancements

### Input Sanitization
- SQL injection prevention (though not directly applicable)
- Command injection prevention for system operations
- Path traversal prevention for file operations
- XSS prevention for output content

### Validation Security
- Prevent validation bypass attempts
- Log validation failures for security monitoring
- Rate limiting for validation-heavy operations
- Audit trail for parameter validation events

## Validation Criteria

### Success Metrics
1. **Validation Coverage**: 100% of tool parameters have validation
2. **Error Quality**: Clear, actionable error messages for all validation failures
3. **Performance Impact**: < 50ms additional latency for validation
4. **User Experience**: Reduced runtime errors, better parameter guidance
5. **Security**: No successful injection or bypass attempts

### Testing Checklist
- [ ] All parameter models implemented and tested
- [ ] Custom validators working correctly
- [ ] Error messages are clear and actionable
- [ ] Performance impact within acceptable limits
- [ ] Security validation prevents common attacks
- [ ] Documentation complete with examples

## Risk Mitigation

### Implementation Risks
- **Performance Degradation**: Validation might slow down tool execution
  - *Mitigation*: Optimize validation logic, implement caching
- **Validation Complexity**: Complex rules might be hard to maintain
  - *Mitigation*: Modular validation design, comprehensive testing
- **Breaking Changes**: New validation might break existing integrations
  - *Mitigation*: Gradual rollout, backward compatibility where possible

### Security Risks
- **Validation Bypass**: Malicious users might try to bypass validation
  - *Mitigation*: Defense in depth, server-side validation enforcement
- **DoS via Validation**: Complex validation might be used for DoS attacks
  - *Mitigation*: Rate limiting, validation timeout limits

## Dependencies

### Existing Dependencies
- Pydantic (already included in project)
- Python typing module
- Existing logging infrastructure

### New Dependencies
No additional external dependencies required.

## Rollout Strategy

### Phase 1: Infrastructure (Day 1)
- Create validation framework and base classes
- Implement error handling infrastructure
- Set up testing framework

### Phase 2: Core Tool Validation (Days 1-2)
- Implement validation for account management tools
- Add safe management tool validation
- Create comprehensive unit tests

### Phase 3: Extended Validation (Days 2-3)
- Add platform and system tool validation
- Implement async validation capabilities
- Performance optimization and tuning

### Phase 4: Integration & Documentation (Days 3-4)
- Complete MCP tool integration
- Finalize documentation and examples
- End-to-end testing and validation

## Success Criteria

1. ✅ All 13 MCP tools have comprehensive parameter validation
2. ✅ Clear, actionable error messages for all validation failures
3. ✅ Performance impact < 50ms additional latency
4. ✅ Security validation prevents injection and bypass attempts
5. ✅ Comprehensive test coverage for all validation scenarios
6. ✅ Complete documentation with constraint reference
7. ✅ User experience significantly improved with better error guidance

---

**Next Steps**: After approval, begin with Phase 1 infrastructure setup and validation framework implementation.