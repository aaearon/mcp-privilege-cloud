# CyberArk Identity Setup Guide

This guide explains how to configure CyberArk Identity for use with the MCP Privilege Cloud server in OAuth per-user mode.

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
  - PCloud API access via `/oauth2/platformtoken` (client_credentials grant)
  - Returned to MCP clients via DCR for the authorization_code flow

## Part B: Create the OAuth2 Client Application

The OAuth2 Client app defines the OAuth endpoints, redirect URIs, and token settings.

### Step 1: Create the App

1. Navigate to **Apps & Widgets** > **Add Web Apps** > **Custom** > **OAuth2 Client**
2. Name the app `mcpprivilegecloud` (this is the default `CYBERARK_OIDC_APP_ID`)
   - This name becomes the **ServiceName** and appears in OIDC URL paths (e.g., `/OAuth2/Authorize/mcpprivilegecloud`)

### Step 2: Configure General Usage Tab

- **Client ID Type**: Set to **"Anything"**
  - "Anything" supports BOTH PKCE (claude.ai) and confidential (Copilot Studio) clients
  - "List" = PKCE only, "Confidential" = secret required
  - If only using PKCE clients (claude.ai): "List" also works

### Step 3: Configure Trust Tab

Add redirect URIs for each MCP client:

| Client | Redirect URI |
|--------|-------------|
| claude.ai | `https://claude.ai/api/mcp/auth_callback` |
| Copilot Studio | (Copilot Studio's callback URL) |
| Local development | `http://localhost:8000/oauth/callback` |

**Important**: After saving the Trust tab, note the auto-generated credentials:
- **Client ID** (UUID format, e.g., `c21840a7-...`) = `CYBERARK_OAUTH_CLIENT_ID`
- **Client Secret** = `CYBERARK_OAUTH_CLIENT_SECRET`

These are different from the service user credentials in Part A.

### Step 4: Note the App's Internal ID

The app's internal ID (used as the JWT `aud` claim) differs from the Trust tab Client ID. To find it:

1. Open the app in CyberArk Identity Admin Portal
2. Check the URL - it contains the app's UUID
3. Alternatively, the `aud` claim in issued JWTs will contain this value

This value = `CYBERARK_OAUTH_AUDIENCE`

### Step 5: Configure Tokens Tab

- Token lifetime: 1 hour (3600s) recommended
- Scopes: `openid profile` minimum

### Step 6: Add Trusted DNS Domains (Required for PKCE Clients)

CyberArk Identity requires PKCE clients to have their domain added to trusted DNS domains:

1. Navigate to **Settings** > **Authentication** > **Security Settings** > **API Security**
2. Under **Trusted DNS Domains for API Calls**, add:
   - `claude.ai` (for claude.ai integration)
   - Any other MCP client domains that will use the OAuth flow
3. Save the settings

**Without this step, CyberArk Identity will return `invalid_client` errors during the authorization code flow.**

### Step 7: Assign Users/Roles

1. Navigate to the application's **Permissions** tab
2. Add the users or roles that should have access to the MCP server
3. Users must also have appropriate **Privilege Cloud** permissions (safe access, platform admin, etc.)

### Step 8: Verify OIDC Discovery

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

# Service account -- for PCloud API access via platform token
CYBERARK_CLIENT_ID=mcp-service@cyberark.cloud.XXXX
CYBERARK_CLIENT_SECRET=service-user-password

# OIDC app -- from Trust tab, for DCR
CYBERARK_OAUTH_CLIENT_ID=your-oidc-app-client-id
CYBERARK_OAUTH_CLIENT_SECRET=your-oidc-app-client-secret

# JWT audience -- the app's internal ID (differs from Trust tab client_id)
CYBERARK_OAUTH_AUDIENCE=your-oidc-app-internal-id

# PCloud subdomain -- required when OAuth JWTs lack the subdomain claim
# the SDK needs to resolve the PCloud API URL
CYBERARK_SUBDOMAIN=your-pcloud-subdomain
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
5. **CyberArkTokenVerifier** validates the JWT signature against the JWKS endpoint (`/OAuth2/Keys/mcpprivilegecloud`, RS256)
6. **execute_tool()** verifies user identity from the OIDC JWT, then routes API calls through the service account's platform token
7. **Tools execute** under the service account's CyberArk permissions, with the authenticated user's identity logged for audit

**Architecture note**: All API calls use a single shared service account platform token. The OIDC JWT is used solely for identity verification and audit logging -- it is not used for PCloud API authorization.

## OIDC App Configuration Reference

The following details describe the expected configuration of the CyberArk Identity OIDC app as queried from the Identity API:

| Setting | Value |
|---------|-------|
| App Name | `MCP Privilege Cloud` |
| App Type | Web (OpenID Connect) |
| Template | Generic OpenID Connect |
| ServiceName (URL slug) | `mcpprivilegecloud` |
| State | Active |
| Signing Algorithm | RS256 |
| OIDC Discovery | `https://{tenant}/mcpprivilegecloud/.well-known/openid-configuration` |
| JWKS Endpoint | `https://{tenant}/OAuth2/Keys/mcpprivilegecloud` |
| Authorization Endpoint | `https://{tenant}/OAuth2/Authorize/mcpprivilegecloud` |
| Token Endpoint | `https://{tenant}/OAuth2/Token/mcpprivilegecloud` |

### Tenant-Level OIDC Discovery

The tenant-level discovery document (at `/.well-known/openid-configuration`) exposes:

| Field | Value |
|-------|-------|
| `issuer` | `https://{tenant}/` |
| `authorization_endpoint` | `https://{tenant}/Oauth/Openid` |
| `token_endpoint` | `https://{tenant}/Oauth/GetToken` |
| `jwks_uri` | `https://{tenant}/Oauth/Keys` |
| `userinfo_endpoint` | `https://{tenant}/Oauth/UserInfo` |
| `scopes_supported` | `openid`, `profile`, `email`, `address`, `phone` |
| `id_token_signing_alg_values_supported` | `RS256` |
| `response_types_supported` | `code`, `id_token`, `id_token token`, `code id_token`, `code token`, `code id_token token` |
| `code_challenge_methods_supported` | `plain`, `S256` |

## Security Considerations

- JWTs are verified against the JWKS endpoint on every request (keys are cached)
- All PCloud API calls use a shared service account platform token (not per-user tokens)
- The OIDC JWT establishes user identity for audit logging only
- Service user credentials are stored server-side and never exposed to end users
- Token verification uses RS256 signature validation via CyberArk Identity's public keys

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `invalid_client` during auth | Verify trusted DNS domains include the MCP client's domain (Part B, Step 6) and that `CYBERARK_CLIENT_ID` is a service user marked as "OAuth 2.0 confidential client" |
| "Token verification failed" | Verify `CYBERARK_IDENTITY_TENANT_URL` is correct and the user has a valid token |
| "JWKS connection failed" | Verify `CYBERARK_IDENTITY_TENANT_URL` is reachable and the app's JWKS endpoint responds |
| Server starts in legacy mode | Ensure `CYBERARK_IDENTITY_TENANT_URL` is set |
| Copilot Studio auth fails | Ensure `CYBERARK_CLIENT_SECRET` is set and Client ID Type is "Anything" or "Confidential" |
| PCloud URL resolution fails | Set `CYBERARK_SUBDOMAIN` to your PCloud subdomain |
| JWT `aud` claim mismatch | Set `CYBERARK_OAUTH_AUDIENCE` to the app's internal ID (not the Trust tab client_id) |
