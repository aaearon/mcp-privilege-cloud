# Implementation Plan: Missing MCP Prompts Implementation

**Priority**: High  
**Estimated Effort**: 4-5 hours  
**Complexity**: Medium  

## Problem Statement

The current MCP server implementation lacks prompts, which are a key MCP feature that provides pre-configured, contextual prompt templates for AI assistants. Prompts enable clients to quickly generate specialized queries and analyses for CyberArk security data without requiring deep domain knowledge.

## Current State Analysis

### Missing Capabilities
1. **No Prompt Templates**: No pre-configured prompts for common CyberArk workflows
2. **Limited AI Integration**: Clients can't easily generate security-focused analyses
3. **No Context Injection**: No way to inject current CyberArk state into prompts
4. **Poor Discovery**: No standard way to find relevant prompt templates

### MCP Prompt Benefits
- **Domain Expertise**: Embed security expertise in prompt templates
- **Context Awareness**: Include real-time CyberArk data in prompts
- **Workflow Acceleration**: Quick access to common analysis patterns
- **Consistency**: Standardized security analysis approaches

## Prompt Categories Design

### Security Analysis Prompts
1. **Account Security Assessment**: Analyze account risk profiles
2. **Safe Compliance Review**: Evaluate safe configurations
3. **Platform Security Audit**: Review platform settings
4. **Password Policy Analysis**: Assess password management

### Operational Prompts  
1. **Account Lifecycle Management**: Manage account creation/retirement
2. **Access Review Templates**: Generate access review reports
3. **Incident Response**: Security incident investigation prompts
4. **Compliance Reporting**: Generate compliance documentation

### Monitoring & Alerting Prompts
1. **Anomaly Detection**: Identify unusual access patterns
2. **Risk Assessment**: Evaluate privileged access risks
3. **Trend Analysis**: Analyze usage and access trends
4. **Recommendation Engine**: Generate security recommendations

## Implementation Strategy

### Phase 1: Prompt Framework
1. **Create Prompt Infrastructure**
   - Prompt base classes and utilities
   - Context injection mechanisms
   - Dynamic content generation

2. **Prompt Registry**
   - Central prompt discovery and management
   - Categorization and tagging system
   - Prompt metadata and versioning

### Phase 2: Security Analysis Prompts
1. **Account Analysis Prompts**
   - Risk assessment templates
   - Compliance checking prompts
   - Account lifecycle prompts

2. **Safe and Platform Prompts**
   - Configuration review templates
   - Security best practice checks
   - Audit preparation prompts

### Phase 3: Operational and Reporting Prompts
1. **Operational Workflow Prompts**
   - Standard operating procedures
   - Incident response templates
   - Change management prompts

2. **Reporting and Compliance Prompts**
   - Automated report generation
   - Compliance documentation
   - Executive summary templates

## Detailed Implementation Steps

### Step 1: Create Prompt Infrastructure
File Structure:
```bash
mkdir -p src/mcp_privilege_cloud/prompts
touch src/mcp_privilege_cloud/prompts/__init__.py
touch src/mcp_privilege_cloud/prompts/base.py
touch src/mcp_privilege_cloud/prompts/registry.py
touch src/mcp_privilege_cloud/prompts/security_analysis.py
touch src/mcp_privilege_cloud/prompts/operational.py
touch src/mcp_privilege_cloud/prompts/reporting.py
touch src/mcp_privilege_cloud/prompts/context_providers.py
```

### Step 2: Prompt Base Classes
File: `src/mcp_privilege_cloud/prompts/base.py`
- `BasePrompt` - Abstract base for all prompts
- `ContextualPrompt` - Prompts with dynamic CyberArk data
- `StaticPrompt` - Fixed template prompts
- `PromptArgument` - Prompt parameter definitions

### Step 3: Context Providers
File: `src/mcp_privilege_cloud/prompts/context_providers.py`
- `SafeContextProvider` - Inject safe data into prompts
- `AccountContextProvider` - Inject account data into prompts
- `PlatformContextProvider` - Inject platform data into prompts
- `SystemContextProvider` - Inject system health data into prompts

### Step 4: Security Analysis Prompts
File: `src/mcp_privilege_cloud/prompts/security_analysis.py`

#### Account Risk Assessment Prompt
```python
class AccountRiskAssessmentPrompt(ContextualPrompt):
    name = "account_risk_assessment"
    description = "Analyze account security risk profile"
    
    arguments = [
        PromptArgument("account_id", "Account ID to analyze", required=True),
        PromptArgument("include_history", "Include password change history", default=True)
    ]
    
    template = """
    Analyze the security risk profile for the following CyberArk account:
    
    Account Details:
    {account_details}
    
    Safe Configuration:
    {safe_details}
    
    Platform Settings:
    {platform_details}
    
    Please evaluate:
    1. Password policy compliance
    2. Access control effectiveness  
    3. Privilege escalation risks
    4. Monitoring and auditing coverage
    5. Compliance with security standards
    
    Provide specific recommendations for risk mitigation.
    """
```

#### Safe Compliance Review Prompt
```python
class SafeComplianceReviewPrompt(ContextualPrompt):
    name = "safe_compliance_review"
    description = "Review safe configuration for compliance"
    
    arguments = [
        PromptArgument("safe_name", "Safe name to review", required=True),
        PromptArgument("compliance_framework", "Compliance framework (SOX, PCI, etc.)", required=False)
    ]
    
    template = """
    Review the following CyberArk safe for compliance with security standards:
    
    Safe Configuration:
    {safe_details}
    
    Safe Members and Permissions:
    {safe_members}
    
    Accounts in Safe:
    {accounts_summary}
    
    Compliance Framework: {compliance_framework}
    
    Evaluate against:
    1. Access control principles (least privilege)
    2. Segregation of duties
    3. Audit trail requirements
    4. Data protection standards
    5. Change management controls
    
    Identify any compliance gaps and provide remediation steps.
    """
```

### Step 5: Operational Prompts
File: `src/mcp_privilege_cloud/prompts/operational.py`

#### Account Lifecycle Management Prompt
```python
class AccountLifecyclePrompt(ContextualPrompt):
    name = "account_lifecycle_management"
    description = "Generate account lifecycle management procedures"
    
    arguments = [
        PromptArgument("lifecycle_stage", "Lifecycle stage (creation, maintenance, retirement)", required=True),
        PromptArgument("account_type", "Account type (service, admin, shared)", required=False)
    ]
    
    template = """
    Generate procedures for {lifecycle_stage} of privileged accounts in CyberArk:
    
    Current Environment Context:
    - Available Platforms: {platform_summary}
    - Safe Structure: {safe_summary}
    - Security Policies: {security_policies}
    
    Account Type: {account_type}
    Lifecycle Stage: {lifecycle_stage}
    
    Create detailed procedures covering:
    1. Prerequisites and requirements
    2. Step-by-step process
    3. Verification and testing steps
    4. Documentation requirements
    5. Approval workflows
    6. Rollback procedures (if applicable)
    
    Include specific CyberArk commands and API calls where appropriate.
    """
```

#### Incident Response Prompt
```python
class IncidentResponsePrompt(ContextualPrompt):
    name = "incident_response_cyberark"
    description = "Generate incident response procedures for CyberArk security events"
    
    arguments = [
        PromptArgument("incident_type", "Type of incident (unauthorized access, credential compromise, etc.)", required=True),
        PromptArgument("affected_accounts", "Affected account IDs or patterns", required=False)
    ]
    
    template = """
    Generate incident response procedures for CyberArk security incident:
    
    Incident Type: {incident_type}
    Affected Accounts: {affected_accounts}
    
    Current System State:
    {system_health}
    
    Potentially Affected Resources:
    {affected_resources}
    
    Create comprehensive incident response plan covering:
    
    IMMEDIATE ACTIONS (0-30 minutes):
    1. Incident containment steps
    2. Evidence preservation
    3. Initial impact assessment
    4. Stakeholder notification
    
    SHORT-TERM ACTIONS (30 minutes - 4 hours):
    1. Detailed forensic analysis
    2. Root cause investigation
    3. System hardening measures
    4. Communication plan execution
    
    RECOVERY ACTIONS (4+ hours):
    1. System restoration procedures
    2. Preventive measures implementation
    3. Monitoring enhancement
    4. Post-incident documentation
    
    Include specific CyberArk commands for investigation and remediation.
    """
```

### Step 6: Reporting Prompts
File: `src/mcp_privilege_cloud/prompts/reporting.py`

#### Executive Security Summary Prompt
```python
class ExecutiveSecuritySummaryPrompt(ContextualPrompt):
    name = "executive_security_summary"
    description = "Generate executive-level security summary report"
    
    arguments = [
        PromptArgument("report_period", "Reporting period (weekly, monthly, quarterly)", default="monthly"),
        PromptArgument("focus_areas", "Specific focus areas to highlight", required=False)
    ]
    
    template = """
    Generate an executive-level security summary for CyberArk Privilege Cloud:
    
    Reporting Period: {report_period}
    Focus Areas: {focus_areas}
    
    Current Security Posture:
    - Total Privileged Accounts: {total_accounts}
    - Active Safes: {total_safes}
    - Platform Coverage: {platform_summary}
    - System Health: {health_status}
    
    Key Metrics:
    {key_metrics}
    
    Create executive summary covering:
    
    SECURITY HIGHLIGHTS:
    1. Key security achievements
    2. Risk reduction measures implemented
    3. Compliance status updates
    4. System performance metrics
    
    AREAS OF CONCERN:
    1. Identified security gaps
    2. Emerging threats and risks
    3. Compliance challenges
    4. Resource limitations
    
    RECOMMENDATIONS:
    1. Strategic security initiatives
    2. Investment priorities
    3. Policy updates needed
    4. Training requirements
    
    ACTION ITEMS:
    1. Immediate priorities (next 30 days)
    2. Short-term goals (next quarter)
    3. Long-term strategic objectives
    
    Present information in business-friendly language with quantified risk metrics.
    """
```

### Step 7: MCP Server Integration
Update `src/mcp_privilege_cloud/mcp_server.py`:

```python
from .prompts.registry import PromptRegistry

# Initialize prompt registry
prompt_registry = PromptRegistry()

@mcp.list_prompts()
async def list_prompts() -> list[Prompt]:
    """List all available CyberArk security prompts"""
    return await prompt_registry.list_all_prompts()

@mcp.get_prompt()
async def get_prompt(
    name: str,
    arguments: Optional[dict[str, str]] = None
) -> GetPromptResult:
    """Get specific prompt with context injection"""
    return await prompt_registry.get_prompt(name, arguments or {})
```

## Prompt Context Integration

### Dynamic Data Injection
Each contextual prompt automatically fetches relevant CyberArk data:

1. **Account Context**: Account details, safe information, platform configuration
2. **Safe Context**: Safe settings, member permissions, account summaries  
3. **Platform Context**: Platform capabilities, connection components, security settings
4. **System Context**: Health status, performance metrics, recent activities

### Context Caching
- Cache frequently accessed context data
- Implement smart refresh based on data volatility
- Optimize context loading for prompt performance

## Testing Requirements

### Unit Tests
- Prompt template rendering with various contexts
- Context provider functionality
- Prompt argument validation
- Dynamic content injection

### Integration Tests
- End-to-end prompt execution with real CyberArk data
- Context accuracy validation
- Prompt discovery through MCP clients
- Performance testing for context-heavy prompts

### Prompt-Specific Tests
- Security analysis prompt accuracy
- Operational prompt completeness
- Reporting prompt formatting
- Context injection correctness

## Documentation Requirements

### New Documentation Files
1. `docs/PROMPTS.md` - Comprehensive prompt documentation
2. `docs/PROMPT_CONTEXTS.md` - Context injection documentation  
3. Update `SERVER_CAPABILITIES.md` - Add prompt capabilities

### Documentation Content
- Complete prompt catalog with descriptions
- Context injection examples
- Usage patterns for different prompt types
- Custom prompt development guide
- Best practices for prompt utilization

## Security Considerations

### Sensitive Data Handling
- Filter sensitive information from prompt contexts
- Implement data access controls based on user permissions
- Audit prompt usage and context access
- Sanitize prompt outputs to prevent data leakage

### Prompt Security
- Validate prompt arguments to prevent injection attacks
- Sanitize dynamic content insertion
- Implement prompt execution rate limiting
- Log prompt usage for security monitoring

## Performance Optimization

### Context Loading
- Implement lazy loading for expensive context operations
- Cache context data with appropriate TTL
- Batch context requests to reduce API calls
- Optimize context data structure for prompt rendering

### Prompt Execution
- Pre-compile prompt templates for faster rendering
- Implement prompt result caching where appropriate
- Monitor prompt execution times and optimize bottlenecks

## Validation Criteria

### Success Metrics
1. **Prompt Discovery**: All prompts discoverable through MCP clients
2. **Context Accuracy**: Dynamic contexts reflect current CyberArk state
3. **Prompt Quality**: Generated content provides actionable insights
4. **Performance**: Prompt execution < 2 seconds response time
5. **Client Integration**: Prompts work seamlessly in MCP clients

### Testing Checklist
- [ ] All prompt categories implemented and functional
- [ ] Context injection working correctly for all prompt types
- [ ] Prompt discovery working in MCP Inspector
- [ ] Performance benchmarks met for all prompts
- [ ] Security controls properly implemented
- [ ] Documentation complete with examples

## Risk Mitigation

### Implementation Risks
- **Context Performance**: Complex context loading might be slow
  - *Mitigation*: Implement efficient caching and lazy loading
- **Data Accuracy**: Stale context data might mislead users
  - *Mitigation*: Smart cache invalidation and real-time updates
- **Prompt Complexity**: Overly complex prompts might be hard to maintain
  - *Mitigation*: Modular prompt design with reusable components

### Security Risks
- **Data Exposure**: Prompts might expose sensitive CyberArk data
  - *Mitigation*: Careful context filtering and access control
- **Prompt Injection**: Malicious prompt arguments might cause issues
  - *Mitigation*: Strict argument validation and sanitization

## Dependencies

### Existing Dependencies
- MCP framework (already installed)
- Jinja2 or similar templating engine (add to dependencies)
- Existing CyberArk API integration

### New Dependencies
```toml
[project.dependencies]
# Add to existing dependencies
"jinja2>=3.1.0",  # For prompt templating
```

## Rollout Strategy

### Phase 1: Infrastructure (Days 1-2)
- Create prompt framework and base classes
- Implement context providers
- Set up prompt registry system

### Phase 2: Security Prompts (Days 2-3)
- Implement security analysis prompts
- Add account and safe analysis templates
- Create compliance review prompts

### Phase 3: Operational Prompts (Days 3-4)
- Add operational workflow prompts
- Implement incident response templates
- Create lifecycle management prompts

### Phase 4: Reporting & Integration (Days 4-5)
- Add reporting and executive summary prompts
- Complete MCP server integration
- Finalize documentation and testing

## Success Criteria

1. ✅ Complete prompt catalog covering all major CyberArk workflows
2. ✅ Dynamic context injection working for all contextual prompts
3. ✅ Prompt discovery functional in MCP clients
4. ✅ Performance targets met (< 2 seconds response time)
5. ✅ Security controls properly implemented and tested
6. ✅ Comprehensive documentation with usage examples
7. ✅ Client integration validated with real-world scenarios

---

**Next Steps**: After approval, begin with Phase 1 infrastructure setup and prompt framework implementation.