# CyberArk Privilege Cloud MCP Server - Troubleshooting Guide

This document provides comprehensive troubleshooting guidance for common issues with the CyberArk Privilege Cloud MCP Server.

## Platform Management Error Scenarios

### Platform Details Access Errors

#### 404 - Platform Not Found

**Symptoms:**
```
CyberArkAPIError: Platform 'MyPlatform' does not exist or is not accessible (404)
```

**Common Causes:**
- Platform ID does not exist in CyberArk
- Platform has been deleted or deactivated
- Typo in platform ID
- Platform exists but is not accessible to current user

**Troubleshooting Steps:**
1. **Verify Platform Exists:**
   ```python
   # List all available platforms
   platforms = await server.list_platforms()
   platform_ids = [p.get('general', p).get('id') for p in platforms]
   print("Available platforms:", platform_ids)
   ```

2. **Check Platform ID Spelling:**
   - Platform IDs are case-sensitive
   - Common examples: `WinServerLocal`, `UnixSSH`, `WinDomainAccount`

3. **Verify Platform Status:**
   - Check if platform is active in CyberArk console
   - Ensure platform hasn't been recently deleted

**Resolution:**
- Use correct platform ID from `list_platforms()` output
- Contact CyberArk administrator if platform should exist

#### 403 - Insufficient Privileges

**Symptoms:**
```
CyberArkAPIError: Access denied to platform 'MyPlatform'. Requires Privilege Cloud Administrator role membership. (403)
```

**Common Causes:**
- User lacks required administrative privileges
- Missing "Privilege Cloud Administrator" role
- Platform details API requires higher privileges than platform list API

**Troubleshooting Steps:**
1. **Check User Roles:**
   - Log into CyberArk Identity Administration
   - Navigate to Users → [Your User] → Roles
   - Verify "Privilege Cloud Administrator" role is assigned

2. **Test Basic vs Detailed Access:**
   ```python
   # This should work with basic user privileges
   platforms = await server.list_platforms()
   
   # This requires admin privileges
   details = await server.get_platform_details("WinServerLocal")
   ```

3. **Use Graceful Degradation:**
   ```python
   # Will fall back to basic info if details fail
   complete_info = await server.get_complete_platform_info("WinServerLocal")
   ```

**Resolution:**
- Request "Privilege Cloud Administrator" role from CyberArk administrator
- Use `get_complete_platform_info()` for graceful degradation to basic platform info
- Use `list_platforms_with_details()` which automatically handles permission failures

#### 429 - Rate Limiting

**Symptoms:**
```
CyberArkAPIError: Rate limit exceeded while accessing platform 'MyPlatform'. Please retry after a delay. (429)
```

**Common Causes:**
- Making too many concurrent API requests
- Exceeding CyberArk API rate limits
- High API usage across multiple applications

**Troubleshooting Steps:**
1. **Reduce Concurrent Requests:**
   ```python
   # Reduce concurrency limit in server configuration
   # Default is 10, try reducing to 5 or 3
   ```

2. **Implement Retry Logic:**
   ```python
   import asyncio
   
   async def retry_with_backoff():
       for attempt in range(3):
           try:
               return await server.get_platform_details("MyPlatform")
           except CyberArkAPIError as e:
               if e.status_code == 429:
                   delay = 2 ** attempt  # Exponential backoff
                   await asyncio.sleep(delay)
               else:
                   raise
   ```

3. **Monitor API Usage:**
   - Check server logs for rate limiting patterns
   - Consider spreading requests over longer time periods

**Resolution:**
- Implement exponential backoff retry logic
- Reduce concurrent request limits
- Contact CyberArk support if rate limits seem too restrictive

### Batch Operations Error Handling

#### Partial Failures in `list_platforms_with_details()`

**Symptoms:**
```
WARNING: Some platforms failed to fetch details (5/20), continuing with available data
```

**Expected Behavior:**
- Method continues execution and returns successful platforms
- Failed platforms are logged and excluded from results
- No exceptions raised for individual platform failures

**Troubleshooting:**
1. **Review Logs for Failure Patterns:**
   ```bash
   # Look for specific error patterns
   grep "403\|404\|429" server.log | grep platform
   ```

2. **Check Success Rate:**
   ```python
   platforms = await server.list_platforms_with_details()
   total_platforms = len(await server.list_platforms())
   success_rate = len(platforms) / total_platforms * 100
   print(f"Success rate: {success_rate:.1f}%")
   ```

3. **Handle Mixed Permissions:**
   ```python
   # Some platforms may be accessible, others not
   # This is normal in environments with mixed permissions
   platforms = await server.list_platforms_with_details()
   print(f"Retrieved {len(platforms)} platforms with details")
   ```

**Resolution:**
- This is expected behavior for graceful degradation
- Review individual platform permissions if specific platforms are needed
- Use higher-privileged account if full platform access is required

## Authentication and Connection Issues

### Token Refresh Failures

**Symptoms:**
```
WARNING: Received 401, refreshing token and retrying
CyberArkAPIError: API request failed: Authentication failed
```

**Troubleshooting Steps:**
1. **Verify Credentials:**
   ```bash
   echo $CYBERARK_CLIENT_ID
   echo $CYBERARK_CLIENT_SECRET
   echo $CYBERARK_TENANT_ID
   echo $CYBERARK_SUBDOMAIN
   ```

2. **Test Authentication Manually:**
   ```python
   authenticator = CyberArkAuthenticator(
       tenant_id="your-tenant",
       client_id="your-client-id", 
       client_secret="your-secret"
   )
   token = await authenticator.get_auth_header()
   ```

3. **Check Token Expiration:**
   - Tokens expire after 15 minutes
   - Server should automatically refresh
   - Check for system clock synchronization issues

**Resolution:**
- Verify all environment variables are correctly set
- Ensure service account credentials are valid
- Check network connectivity to identity endpoints

### Network Connectivity Issues

**Symptoms:**
```
CyberArkAPIError: Network error: Connection failed
```

**Troubleshooting Steps:**
1. **Test Connectivity:**
   ```bash
   curl -I https://your-subdomain.privilegecloud.cyberark.cloud
   curl -I https://your-tenant.id.cyberark.cloud
   ```

2. **Check DNS Resolution:**
   ```bash
   nslookup your-subdomain.privilegecloud.cyberark.cloud
   nslookup your-tenant.id.cyberark.cloud
   ```

3. **Verify Firewall/Proxy:**
   - Ensure HTTPS (443) access to `*.cyberark.cloud`
   - Check corporate firewall rules
   - Verify proxy configuration if applicable

## Input Validation Errors

### Invalid Platform IDs

**Symptoms:**
```
ValueError: Invalid platform_id provided: None
ValueError: Invalid platform_id provided: 123
```

**Common Causes:**
- Passing None, empty string, or non-string values
- Programming errors in client code

**Resolution:**
```python
# Always validate platform_id before API calls
def validate_platform_id(platform_id):
    if not platform_id or not isinstance(platform_id, str):
        raise ValueError(f"Platform ID must be a non-empty string, got: {platform_id!r}")
    return platform_id.strip()

# Use validation in your code
platform_id = validate_platform_id(user_input)
details = await server.get_platform_details(platform_id)
```

## Performance Issues

### Slow Concurrent Operations

**Symptoms:**
- `list_platforms_with_details()` taking longer than expected
- Timeout errors in batch operations

**Troubleshooting:**
1. **Monitor Execution Time:**
   ```python
   import time
   
   start = time.time()
   platforms = await server.list_platforms_with_details()
   duration = time.time() - start
   print(f"Execution time: {duration:.2f}s for {len(platforms)} platforms")
   ```

2. **Adjust Concurrency:**
   ```python
   # Reduce concurrent requests if experiencing timeouts
   # Modify semaphore limit in list_platforms_with_details
   ```

3. **Check Network Latency:**
   ```bash
   ping your-subdomain.privilegecloud.cyberark.cloud
   ```

**Resolution:**
- Reduce concurrent request limit from 10 to 5 or 3
- Implement request batching for very large platform lists
- Consider caching platform details for frequently accessed platforms

## Debugging Commands

### Enable Debug Logging
```python
import logging
logging.getLogger('mcp_privilege_cloud').setLevel(logging.DEBUG)
```

### Test Individual Components
```python
# Test authentication only
auth = CyberArkAuthenticator.from_environment()
token = await auth.get_auth_header()

# Test basic platform list
platforms = await server.list_platforms()

# Test single platform details
details = await server.get_platform_details("WinServerLocal")

# Test graceful degradation
complete = await server.get_complete_platform_info("WinServerLocal")
```

### Log Analysis
```bash
# Find error patterns
grep -E "(ERROR|WARNING|CRITICAL)" server.log

# Check authentication issues
grep "401\|403" server.log

# Monitor rate limiting
grep "429" server.log

# Platform-specific issues
grep "platform.*error" server.log -i
```

## Getting Help

### Support Resources
1. **CyberArk Documentation:** [CyberArk Privilege Cloud REST API](https://docs.cyberark.com/PrivilegeCloud/latest/en/Content/SDK/rest-api-auth.htm)
2. **Server Documentation:** `SERVER_CAPABILITIES.md` for complete API reference
3. **Development Guide:** `DEVELOPMENT.md` for development setup

### Reporting Issues
When reporting issues, include:
- Full error messages and stack traces
- Environment configuration (sanitized)
- Steps to reproduce
- Expected vs actual behavior
- Relevant log excerpts

### Emergency Procedures
For production issues:
1. Check service status at [CyberArk Status Page](https://status.cyberark.com/)
2. Verify network connectivity to CyberArk cloud
3. Test with backup service account credentials
4. Implement fallback to basic platform operations if needed

---

*Last Updated: Task A4 Implementation - Enhanced Error Handling*