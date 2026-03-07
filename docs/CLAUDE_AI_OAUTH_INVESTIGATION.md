# Claude.ai Remote MCP OAuth Integration — Investigation Report

## Goal

Connect the MCP Privilege Cloud server as a **Remote MCP Server** in claude.ai using OAuth 2.1 with CyberArk Identity as the authorization server.

## Background

Claude.ai supports adding Remote MCP Servers that require OAuth authentication. The MCP spec (2025-03-26) defines a discovery and authorization flow based on:

- **RFC 9728** — OAuth 2.0 Protected Resource Metadata (`/.well-known/oauth-protected-resource`)
- **RFC 8414** — OAuth 2.0 Authorization Server Metadata (`/.well-known/oauth-authorization-server`)
- **RFC 7591** — OAuth 2.0 Dynamic Client Registration (`POST /register`)
- **OAuth 2.1** — Authorization Code + PKCE

Our server delegates authentication to CyberArk Identity (an external authorization server) rather than being its own authorization server. This creates a mismatch because:

1. FastMCP only creates `/.well-known/oauth-authorization-server` when acting as its own auth server (via `auth_server_provider`)
2. CyberArk Identity serves `/.well-known/openid-configuration` (OIDC) but NOT `/.well-known/oauth-authorization-server` (RFC 8414)

## What We Implemented

### 1. RFC 8414 Authorization Server Metadata Endpoint (WORKING)

**Problem**: claude.ai fetches `/.well-known/oauth-authorization-server` from the MCP server and gets 404.

**Solution**: Added a `custom_route` on FastMCP that fetches CyberArk Identity's `/.well-known/openid-configuration`, caches it, and maps it to RFC 8414 format.

```
GET https://mcp.ams.iosharp.com/.well-known/oauth-authorization-server
→ 200 OK with authorization_endpoint, token_endpoint, registration_endpoint, etc.
```

**Key detail — app-specific endpoints**: CyberArk Identity's tenant-level OIDC discovery returns generic endpoints (`/Oauth/Openid`, `/Oauth/GetToken`) that don't bind to a specific OIDC app. These fail with a generic error page. The correct endpoints include the app ID in the path:

- `/OAuth2/Authorize/{app_id}` (not `/Oauth/Openid`)
- `/OAuth2/Token/{app_id}` (not `/Oauth/GetToken`)

### 2. Protected Resource Metadata — `authorization_servers` Fix (WORKING)

**Problem**: FastMCP populates `authorization_servers` in `/.well-known/oauth-protected-resource` from `AuthSettings.issuer_url`. We initially set this to CyberArk Identity's tenant URL, so claude.ai fetched `/.well-known/oauth-authorization-server` from CyberArk Identity (which doesn't serve it) rather than from our server.

**Solution**: Set `issuer_url` to our own server URL (`MCP_SERVER_URL`). This makes `authorization_servers` point to our server, where we serve the proxied metadata.

```python
kwargs["auth"] = AuthSettings(
    issuer_url=AnyHttpUrl(server_url),      # our server, NOT tenant_url
    resource_server_url=AnyHttpUrl(server_url),
)
```

### 3. Dynamic Client Registration Proxy (WORKING)

**Problem**: claude.ai requires RFC 7591 Dynamic Client Registration to obtain `client_id` (and optionally `client_secret`) before starting the OAuth flow. Without a `registration_endpoint` in the metadata, claude.ai can't proceed.

**Solution**: Added a `/register` custom route that returns pre-configured CyberArk Identity OIDC app credentials from environment variables.

```
POST https://mcp.ams.iosharp.com/register
← 201 Created { "client_id": "...", "client_secret": "...", "token_endpoint_auth_method": "client_secret_post" }
```

The DCR response uses:
- `CYBERARK_CLIENT_ID` env var as `client_id` (falls back to `CYBERARK_OIDC_APP_ID`)
- `CYBERARK_CLIENT_SECRET` env var as `client_secret` (if set; otherwise public client)

### 4. Custom OIDC App in CyberArk Identity (PARTIALLY WORKING)

**Problem**: The built-in `__idaptive_cybr_user_oidc` app doesn't allow adding redirect URIs, so claude.ai's callback URL (`https://claude.ai/api/mcp/auth_callback`) couldn't be registered.

**Solution**: Created a custom OIDC app `mcpprivilegecloud` in CyberArk Identity with the claude.ai callback as an allowed redirect URI.

The OIDC app ID is configurable via `CYBERARK_OIDC_APP_ID` env var (default: `mcpprivilegecloud`).

## What Worked End-to-End

The following steps complete successfully:

| Step | Endpoint | Status |
|------|----------|--------|
| 1. Initial request | `POST /mcp` | 401 Unauthorized (correct) |
| 2. Protected resource discovery | `GET /.well-known/oauth-protected-resource` | 200 OK |
| 3. Authorization server discovery | `GET /.well-known/oauth-authorization-server` | 200 OK |
| 4. Dynamic Client Registration | `POST /register` | 201 Created |
| 5. Redirect to CyberArk Identity | Browser → `/OAuth2/Authorize/mcpprivilegecloud` | 302 → login page |
| 6. User authentication | CyberArk Identity login form | User authenticates successfully |
| 7. Authorization code issuance | CyberArk Identity → callback | **FAILS: `invalid_client` / `invalid client creds`** |

## Where It Fails — The Blocking Issue

After the user successfully authenticates with CyberArk Identity, the authorization server returns an error instead of an authorization code:

```
https://claude.ai/api/mcp/auth_callback?error=invalid_client&error_description=invalid%20client%20creds
```

This means CyberArk Identity **authenticated the user** but **rejected the OAuth client** when trying to issue the authorization code.

### Root Cause Analysis

CyberArk Identity's OIDC app configuration does not appear to support the standard OAuth 2.1 authorization code flow as expected by MCP clients. Specifically:

1. **The built-in `__idaptive_cybr_user_oidc` app** — Cannot modify redirect URIs, so it can't support claude.ai's callback URL.

2. **Custom OIDC apps** — Can be created, but CyberArk Identity returns `invalid_client` after user authentication regardless of:
   - Client ID type set to "Anything"
   - App set to "Confidential" with matching `client_id` and `client_secret`
   - Redirect URI properly registered
   - All standard OAuth parameters present (response_type, code_challenge, scope, etc.)

3. **The `invalid client creds` error** occurs AFTER user authentication, during the authorization code issuance step. This suggests CyberArk Identity's OIDC implementation has specific requirements for client validation that differ from standard OAuth 2.1.

### Possible Explanations

- CyberArk Identity may require a specific client authentication method during the authorization request (not just token exchange)
- The OIDC app may need additional configuration beyond what's visible in the admin UI (e.g., API-level settings, specific OAuth profile, or trust relationships)
- The `client_id` format expected by CyberArk Identity for custom apps may differ from what we're sending
- CyberArk Identity may not fully support the public/PKCE flow that MCP clients expect, or may require additional parameters

## Files Modified

| File | Purpose |
|------|---------|
| `src/mcp_privilege_cloud/mcp_server.py` | Added `_fetch_oidc_discovery()`, `_build_oauth_metadata()`, `_build_dcr_response()`, `_register_oauth_routes()` with custom routes for `/.well-known/oauth-authorization-server` and `/register` |
| `src/mcp_privilege_cloud/token_verifier.py` | Made `CYBERARK_OIDC_APP_ID` configurable via env var (default: `mcpprivilegecloud`) |
| `tests/test_oauth_metadata.py` | 16 tests covering OIDC discovery fetching/caching, metadata building, DCR response, route registration |
| `CLAUDE.md` | Updated status and test file listings |

## Environment Variables (New/Changed)

| Variable | Purpose | Default |
|----------|---------|---------|
| `CYBERARK_OIDC_APP_ID` | OIDC app ID for URL paths and token audience validation | `mcpprivilegecloud` |
| `CYBERARK_CLIENT_ID` | OAuth client_id returned in DCR response | Falls back to `CYBERARK_OIDC_APP_ID` |
| `CYBERARK_CLIENT_SECRET` | OAuth client_secret returned in DCR (confidential client) | None (public client) |

## Likely Resolution: DCR Client ID Fix

**Update (2026-02-26)**: CyberArk Identity OAuth2 Client apps do NOT provide their own client_id/client_secret. Instead, the `client_id` and `client_secret` come from a **service user** marked as "OAuth 2.0 confidential client". The service user's login name IS the `client_id` (format: `<name>@cyberark.cloud.<suffix>`), and the password IS the `client_secret`.

This means `CYBERARK_CLIENT_ID` was already the correct value for DCR all along. The `invalid_client` error from Step 7 may instead be caused by:
- Missing trusted DNS domains (most likely)
- Client ID Type misconfiguration on the OAuth2 Client app
- Service user not properly marked as OAuth 2.0 confidential client

Code changes made:
- `CYBERARK_OAUTH_CLIENT_ID`/`CYBERARK_OAUTH_CLIENT_SECRET` added as optional overrides (for cases where different credentials are needed for DCR vs legacy mode)
- DCR priority chain: `CYBERARK_OAUTH_CLIENT_ID` > `CYBERARK_CLIENT_ID` > `CYBERARK_OIDC_APP_ID`
- Token verifier audience uses same priority chain
- `DEPLOY_ENV` removed as dead code

**To verify**: Ensure `CYBERARK_CLIENT_ID` is a service user marked as "OAuth 2.0 confidential client", trusted DNS domains are configured, then test the full claude.ai OAuth flow.

## Other Next Steps

1. **CyberArk Identity investigation** — If the DCR fix doesn't fully resolve the issue, determine the exact OIDC app configuration required:
   - CyberArk support engagement
   - Reviewing CyberArk Identity API documentation for OIDC app configuration
   - Testing with CyberArk Identity's own OAuth playground/test tools

2. **Alternative: Token proxy approach** — Instead of delegating the OAuth flow to CyberArk Identity, our MCP server could act as its own authorization server (using FastMCP's `auth_server_provider`) that:
   - Handles the OAuth flow with claude.ai directly
   - Authenticates users against CyberArk Identity on the backend
   - Issues its own tokens to the MCP client
   - This is the "Third-Party Authorization Flow" described in the MCP spec

3. **Alternative: mcp-remote proxy** — Use the community `mcp-remote` tool as a bridge, which handles OAuth complexity for providers that don't fully support Dynamic Client Registration.

## References

- [MCP Authorization Specification (2025-03-26)](https://modelcontextprotocol.io/specification/2025-03-26/basic/authorization)
- [Building custom connectors via remote MCP servers (claude.ai)](https://support.claude.com/en/articles/11503834-building-custom-connectors-via-remote-mcp-servers)
- [RFC 8414 — OAuth 2.0 Authorization Server Metadata](https://datatracker.ietf.org/doc/html/rfc8414)
- [RFC 7591 — OAuth 2.0 Dynamic Client Registration](https://datatracker.ietf.org/doc/html/rfc7591)
- [RFC 9728 — OAuth 2.0 Protected Resource Metadata](https://datatracker.ietf.org/doc/html/rfc9728)
- [Claude OAuth requires DCR — GitHub Issue](https://github.com/anthropics/claude-code/issues/2527)
- [Evolving OAuth Client Registration in MCP](https://blog.modelcontextprotocol.io/posts/client_registration/)
