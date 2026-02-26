# CyberArk Identity Setup Guide

This guide explains how to configure CyberArk Identity for use with the MCP Privilege Cloud server.

## Prerequisites

- CyberArk Identity administrator access
- CyberArk Privilege Cloud tenant

## Part A: Create a Service User (OAuth Confidential Client)

CyberArk Identity OAuth2 apps do NOT provide their own client_id/client_secret. Instead, credentials come from a **service user** marked as an OAuth 2.0 confidential client.

### Step 1: Create the Service User

1. Navigate to **Core Services** > **Users** > **Add User**
2. Fill in:
   - Login name (e.g., `mcp-service@cyberark.cloud.XXXX`)
   - Display name
   - Password
3. In Status checklist, select **"Is OAuth confidential client"**
   - This auto-selects: "Is Service User", "Password never expires"
4. Click **Create User**

### Step 2: Assign Roles

1. Navigate to **Core Services** > **Roles** > select the required role
2. Add the service user as a member
3. Typical roles: Privilege Cloud Administrator, Safe Management, etc.

### Step 3: Note Credentials

- Login name = `CYBERARK_CLIENT_ID` (e.g., `mcp-service@cyberark.cloud.3240`)
- Password = `CYBERARK_CLIENT_SECRET`
- These credentials are used for:
  - Legacy service account mode (`/oauth2/platformtoken` client_credentials grant)
  - DCR response (returned to MCP clients for the authorization_code flow)

## Part B: Create the OAuth2 Client Application

The OAuth2 Client app defines the OAuth endpoints, redirect URIs, and token settings.

### Step 1: Create the App

1. Navigate to **Apps & Widgets** > **Add Web Apps** > **Custom** > **OAuth2 Client**
2. Name the app `mcpprivilegecloud` (this is the default `CYBERARK_OIDC_APP_ID`)

### Step 2: Configure General Usage Tab

- **Client ID Type**: Set to **"Anything"**
  - "Anything" supports BOTH PKCE (claude.ai) and confidential (Copilot Studio) clients
  - "List" = PKCE only, "Confidential" = secret required
  - If only using PKCE clients (claude.ai): "List" also works

### Step 3: Configure Trust Tab (Redirect URIs)

Add redirect URIs for each MCP client:

| Client | Redirect URI |
|--------|-------------|
| claude.ai | `https://claude.ai/api/mcp/auth_callback` |
| Copilot Studio | (Copilot Studio's callback URL) |
| Local development | `http://localhost:8000/oauth/callback` |

### Step 4: Configure Tokens Tab

- Token lifetime: 1 hour (3600s) recommended
- Scopes: `openid profile` minimum

### Step 5: Add Trusted DNS Domains (Required for PKCE Clients)

CyberArk Identity requires PKCE clients to have their domain added to trusted DNS domains:

1. Navigate to **Settings** > **Authentication** > **Security Settings** > **API Security**
2. Under **Trusted DNS Domains for API Calls**, add:
   - `claude.ai` (for claude.ai integration)
   - Any other MCP client domains that will use the OAuth flow
3. Save the settings

**Without this step, CyberArk Identity will return `invalid_client` errors during the authorization code flow.**

### Step 6: Assign Users/Roles

1. Navigate to the application's **Permissions** tab
2. Add the users or roles that should have access to the MCP server
3. Users must also have appropriate **Privilege Cloud** permissions (safe access, platform admin, etc.)

### Step 7: Verify OIDC Discovery

Verify the OIDC discovery endpoint is accessible for your app:

```bash
curl https://YOUR_TENANT.id.cyberark.cloud/mcpprivilegecloud/.well-known/openid-configuration
```

This should return JSON with `authorization_endpoint`, `token_endpoint`, and `jwks_uri` that include the app ID in the path (e.g., `/OAuth2/Authorize/mcpprivilegecloud`).

## Part C: MCP Server Environment Variables

### OAuth Per-User Mode (Recommended)

```bash
# Required: triggers OAuth mode
CYBERARK_IDENTITY_TENANT_URL=https://abc1234.id.cyberark.cloud

# Service account — for PCloud API access via platform token
CYBERARK_CLIENT_ID=mcp-service@cyberark.cloud.XXXX
CYBERARK_CLIENT_SECRET=service-user-password

# OIDC app — from Trust tab, for DCR
CYBERARK_OAUTH_CLIENT_ID=your-oidc-app-client-id
CYBERARK_OAUTH_CLIENT_SECRET=your-oidc-app-client-secret
# JWT audience — the app's internal ID (differs from Trust tab client_id)
CYBERARK_OAUTH_AUDIENCE=your-oidc-app-internal-id
```

### Legacy Service Account Mode

Uses the service account credentials directly for all PCloud API calls (no OAuth):

```bash
CYBERARK_CLIENT_ID=mcp-service@cyberark.cloud.XXXX
CYBERARK_CLIENT_SECRET=service-user-password
```

## How It Works

1. **User connects** to the MCP server via an MCP client (claude.ai, Copilot Studio, etc.)
2. **MCP client** calls DCR (`/register`) and receives OIDC app credentials from `CYBERARK_OAUTH_CLIENT_ID`/`SECRET`
3. **MCP client** redirects to CyberArk Identity for user authentication (authorization_code flow)
4. **MCP server** receives the Bearer JWT token with each request
5. **CyberArkTokenVerifier** validates the JWT signature against the JWKS endpoint
6. **execute_tool()** verifies user identity from the OIDC JWT, then routes API calls through the service account's platform token
7. **Tools execute** under the service account's CyberArk permissions, with the authenticated user's identity logged for audit

## Security Considerations

- JWTs are verified against the JWKS endpoint on every request (keys are cached)
- Sessions are keyed by SHA-256 hash of the access token
- Expired sessions are automatically evicted
- Each user gets an isolated SDK session with their own permissions
- Service user credentials are only sent via DCR; per-user operations use the user's own JWT

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `invalid_client` during auth | Verify trusted DNS domains include the MCP client's domain (Part B, Step 5) and that `CYBERARK_CLIENT_ID` is a service user marked as "OAuth 2.0 confidential client" |
| "Token verification failed" | Verify `CYBERARK_IDENTITY_TENANT_URL` is correct and the user has a valid token |
| "JWKS connection failed" | Verify `CYBERARK_IDENTITY_TENANT_URL` is reachable |
| "Session limit reached" | Increase `MCP_MAX_SESSIONS` or decrease `MCP_SESSION_TTL` |
| Server starts in legacy mode | Ensure `CYBERARK_IDENTITY_TENANT_URL` is set |
| Copilot Studio auth fails | Ensure `CYBERARK_CLIENT_SECRET` is set and Client ID Type is "Anything" or "Confidential" |
