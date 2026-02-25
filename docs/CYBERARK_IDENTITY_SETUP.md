# CyberArk Identity OAuth Setup Guide

This guide explains how to configure a CyberArk Identity OAuth2 application for use with the MCP Privilege Cloud server in per-user OAuth mode.

## Prerequisites

- CyberArk Identity administrator access
- CyberArk Privilege Cloud tenant

## Step 1: Register an OAuth2 Application

1. Log in to your CyberArk Identity Administration portal
2. Navigate to **Apps & Widgets** > **Web Apps**
3. Click **Add Web Apps** > **Custom** > **OAuth2 Client**
4. Configure the application:

| Setting | Value |
|---------|-------|
| **Application ID** | `mcp-privilege-cloud` (or your preferred name) |
| **Application Name** | MCP Privilege Cloud Server |
| **Grant Type** | Authorization Code |
| **Token Type** | JWT |
| **Issuer** | Your tenant URL (e.g., `https://abc1234.id.cyberark.cloud`) |

5. Under **Tokens**:
   - Set **Token Lifetime** to your desired duration (recommended: 1 hour)
   - Enable **Refresh Tokens** for long-lived sessions

6. Under **Scope**:
   - Add scopes as required for your deployment (e.g., `openid`, `profile`)

7. Save the application and note the **Application ID**

## Step 2: Configure Redirect URIs

Add the appropriate redirect URI based on your MCP client:

| Client | Redirect URI |
|--------|-------------|
| Local development | `http://localhost:8000/oauth/callback` |
| Production | `https://your-server.example.com/oauth/callback` |

## Step 3: Assign Users/Roles

1. Navigate to the application's **Permissions** tab
2. Add the users or roles that should have access to the MCP server
3. Users must also have appropriate **Privilege Cloud** permissions (safe access, platform admin, etc.)

## Step 4: Configure the MCP Server

Set the following environment variables:

```bash
# Required
CYBERARK_IDENTITY_TENANT_URL=https://abc1234.id.cyberark.cloud
CYBERARK_OAUTH_APP_ID=mcp-privilege-cloud

# Optional
MCP_HOST=127.0.0.1        # Server bind address
MCP_PORT=8000              # Server port
MCP_MAX_SESSIONS=100       # Max concurrent user sessions
MCP_SESSION_TTL=3600       # Session lifetime in seconds
```

## Step 5: Verify Configuration

Start the server and verify it initializes in OAuth mode:

```bash
uv run mcp-privilege-cloud
```

You should see log output indicating OAuth per-user mode:
```
Initializing in OAuth per-user mode...
Token verifier initialized (tenant: https://abc1234.id.cyberark.cloud, app: mcp-privilege-cloud)
Session manager initialized (max=100, ttl=3600s)
```

## How It Works

1. **User connects** to the MCP server via an MCP client
2. **MCP client** obtains a JWT from CyberArk Identity via OAuth Authorization Code flow
3. **MCP server** receives the Bearer token with each request
4. **CyberArkTokenVerifier** validates the JWT signature against the JWKS endpoint at `{tenant_url}/oauth2/certs`
5. **UserSessionManager** creates (or retrieves) an isolated `CyberArkMCPServer` instance for that user
6. **Tools execute** with the user's own CyberArk permissions and audit trail

## Security Considerations

- JWTs are verified against the JWKS endpoint on every request (keys are cached)
- Sessions are keyed by SHA-256 hash of the access token
- Expired sessions are automatically evicted
- Each user gets an isolated SDK session with their own permissions
- No service account credentials are stored or shared

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Token verification failed" | Verify `CYBERARK_OAUTH_APP_ID` matches the Application ID in CyberArk Identity |
| "JWKS connection failed" | Verify `CYBERARK_IDENTITY_TENANT_URL` is reachable and correct |
| "Session limit reached" | Increase `MCP_MAX_SESSIONS` or decrease `MCP_SESSION_TTL` |
| Server starts in legacy mode | Ensure both `CYBERARK_IDENTITY_TENANT_URL` and `CYBERARK_OAUTH_APP_ID` are set |
