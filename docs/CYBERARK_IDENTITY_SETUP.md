# Idira Identity Setup Guide

This guide explains how to configure Idira Identity for use with the MCP Privilege Cloud server in OAuth per-user mode.

## Prerequisites

- Idira Identity administrator access
- Idira Privilege Cloud tenant

## Part A: Create a Service User (OAuth Confidential Client)

Idira Identity OAuth2 apps do NOT provide their own client_id/client_secret. Instead, credentials come from a **service user** marked as an OAuth 2.0 confidential client.

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
- These credentials are used **only** for PCloud API access via `/oauth2/platformtoken` (client_credentials grant)
- They are NOT used for the OAuth authorization flow — that uses the OIDC app credentials from Part B

## Part B: Create the OIDC Application

The OIDC app defines the OAuth/OIDC endpoints, redirect URIs, token settings, and issues the JWTs that the MCP server validates on every request.

### Step 1: Create the App

1. Navigate to **Apps & Widgets** > **Add Web Apps** > **Custom** > select the **OpenID Connect** template
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

### Step 4: Configure Tokens Tab

**Signing Algorithm**: Must be **RS256** (the only algorithm the MCP server accepts for JWT signature verification).

**Token Lifetime**: 1 hour (3600s) recommended.

**Scopes**: Configure at least `openid profile`:

| Scope | Required | Why |
|-------|----------|-----|
| `openid` | Yes | Produces the `sub` claim (user identity) — the MCP server requires this claim and rejects tokens without it |
| `profile` | Recommended | Adds `unique_name` and display name claims for richer audit logging |

**Required JWT Claims**: The MCP server validates these claims on every request. All are standard OIDC claims produced automatically by Idira Identity when the scopes above are configured:

| Claim | Set By | Validated Against |
|-------|--------|-------------------|
| `sub` | `openid` scope | Must be non-empty (used as user identity for audit logging) |
| `exp` | Always present | Must not be expired |
| `iss` | Always present | Must match `{tenant_url}/{app_name}/` (e.g., `https://abc1234.id.cyberark.cloud/mcpprivilegecloud/`) |
| `aud` | Set to the `client_id` used in the authorization request | Must match `CYBERARK_OAUTH_CLIENT_ID` (see [JWT Validation](#jwt-validation) below) |

### Step 5: Add Trusted DNS Domains (Required for PKCE Clients)

Idira Identity requires PKCE clients to have their domain added to trusted DNS domains:

1. Navigate to **Settings** > **Authentication** > **Security Settings** > **API Security**
2. Under **Trusted DNS Domains for API Calls**, add:
   - `claude.ai` (for claude.ai integration)
   - Any other MCP client domains that will use the OAuth flow
3. Save the settings

**Without this step, Idira Identity will return `invalid_client` errors during the authorization code flow.**

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

# Service account (Part A) -- for PCloud API access via platform token
CYBERARK_CLIENT_ID=mcp-service@cyberark.cloud.XXXX
CYBERARK_CLIENT_SECRET=service-user-password

# OIDC app (Part B, Step 3) -- injected server-side in /token proxy, never exposed via DCR
CYBERARK_OAUTH_CLIENT_ID=your-oidc-app-client-id
CYBERARK_OAUTH_CLIENT_SECRET=your-oidc-app-client-secret
```

### Legacy Service Account Mode

Uses the service account credentials directly for all PCloud API calls (no OAuth):

```bash
CYBERARK_CLIENT_ID=mcp-service@cyberark.cloud.XXXX
CYBERARK_CLIENT_SECRET=service-user-password
```

## How It Works

1. **User connects** to the MCP server via an MCP client (claude.ai, Copilot Studio, etc.)
2. **MCP client** calls DCR (`/register`) and receives the `client_id` (public client, no secret)
3. **MCP client** redirects to Idira Identity for user authentication (authorization_code flow with PKCE)
4. **MCP server** receives the Bearer JWT token with each request
5. **CyberArkTokenVerifier** validates the JWT signature against the JWKS endpoint (`/OAuth2/Keys/mcpprivilegecloud`, RS256)
6. **execute_tool()** verifies user identity from the OIDC JWT, then routes API calls through the service account's platform token
7. **Tools execute** under the service account's Idira permissions, with the authenticated user's identity logged for audit

**Architecture note**: All API calls use a single shared service account platform token. The OIDC JWT is used solely for identity verification and audit logging -- it is not used for PCloud API authorization.

## JWT Validation

The MCP server validates every incoming Bearer JWT against Idira Identity's JWKS endpoint. Understanding these checks helps diagnose authentication failures.

**Signature**: RS256 only, verified against keys from `{tenant}/{app_name}/.well-known/openid-configuration` → `jwks_uri`. Keys are cached after first fetch.

**Required claims** (token is rejected if any are missing):

| Claim | Validation Rule | Common Failure |
|-------|----------------|----------------|
| `sub` | Must be non-empty | Missing when `openid` scope is not configured on the app |
| `exp` | Must be in the future | Token has expired — check token lifetime in Tokens tab |
| `iss` | Must equal `{tenant_url}/{app_name}/` | Wrong app name or tenant URL in `CYBERARK_IDENTITY_TENANT_URL` |
| `aud` | Must match a configured audience value | See audience resolution below |

**Audience resolution**: The server accepts these values as a valid `aud` claim:

1. `CYBERARK_OAUTH_CLIENT_ID` — the Trust tab client ID (Part B, Step 3)
2. Fallback: `CYBERARK_OIDC_APP_ID` (default: `mcpprivilegecloud`)

Idira Identity sets `aud` to the `client_id` used in the authorization request. When DCR returns `CYBERARK_OAUTH_CLIENT_ID`, tokens will have that UUID as the audience.

**Debugging token issues**: Set `CYBERARK_LOG_LEVEL=DEBUG` to see the actual `iss`, `aud`, and `sub` claims from rejected tokens. You can also decode a token manually:

```bash
# Decode JWT payload (no verification) to inspect claims
echo "<token>" | cut -d. -f2 | base64 -d 2>/dev/null | python3 -m json.tool
```

## OIDC App Configuration Reference

The following details describe the expected configuration of the Idira Identity OIDC app created in Part B.

| Setting | Value |
|---------|-------|
| App Name | `MCP Privilege Cloud` (display name) |
| App Type | Web (OpenID Connect) |
| ServiceName (URL slug) | `mcpprivilegecloud` |
| Client ID Type | Anything (supports PKCE + confidential clients) |
| Signing Algorithm | RS256 |
| Scopes | `openid profile` minimum |
| State | Active |
| OIDC Discovery | `https://{tenant}/mcpprivilegecloud/.well-known/openid-configuration` |
| JWKS Endpoint | `https://{tenant}/OAuth2/Keys/mcpprivilegecloud` |
| Authorization Endpoint | `https://{tenant}/OAuth2/Authorize/mcpprivilegecloud` |
| Token Endpoint | `https://{tenant}/OAuth2/Token/mcpprivilegecloud` |

### Tenant-Level OIDC Discovery

The tenant-level discovery document (at `/.well-known/openid-configuration`) is NOT used by the MCP server — it exposes generic endpoints that don't resolve the app context. The MCP server uses the app-specific discovery at `/{app_name}/.well-known/openid-configuration` instead.

For reference, the tenant-level discovery exposes:

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

## Security Limitations

> **Important**: All authenticated users share the same service account's PCloud permissions. The OIDC JWT verifies *who* the user is, but API calls are executed using the service account's platform token. This means:
>
> - Any authenticated user can perform any operation the service account is authorized for
> - Per-user permission enforcement is **not** supported — Idira PCloud does not accept OIDC tokens for API authorization
> - The service account's roles and safe permissions define the ceiling for all users
> - User identity is logged for audit purposes only
>
> **Recommendation**: Grant the service account the minimum PCloud permissions required, and restrict which users can authenticate by limiting the OIDC app's assigned users/roles in Idira Identity (Part B, Step 6).

## Security Considerations

- JWTs are verified against the JWKS endpoint on every request (keys are cached)
- All PCloud API calls use a shared service account platform token (not per-user tokens)
- The OIDC JWT establishes user identity for audit logging only
- Service user credentials are stored server-side and never exposed to end users
- DCR (`/register`) returns public client only (`token_endpoint_auth_method: "none"`) -- secrets are injected server-side by the `/token` proxy
- Token verification uses RS256 signature validation via Idira Identity's public keys

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `invalid_client` during auth | Verify trusted DNS domains include the MCP client's domain (Part B, Step 5) and that Client ID Type is set to "Anything" |
| "Token verification failed" | Set `CYBERARK_LOG_LEVEL=DEBUG` to see actual vs expected claims. Verify `CYBERARK_IDENTITY_TENANT_URL` is correct |
| "Token missing required 'sub' claim" | Ensure `openid` scope is configured on the Tokens tab (Part B, Step 4) |
| "JWKS connection failed" | Verify `CYBERARK_IDENTITY_TENANT_URL` is reachable and the app's OIDC discovery endpoint responds |
| Server starts in legacy mode | Ensure `CYBERARK_IDENTITY_TENANT_URL` is set |
| Copilot Studio auth fails | Ensure `CYBERARK_OAUTH_CLIENT_SECRET` is set and Client ID Type is "Anything" or "Confidential" |
| JWT `aud` claim mismatch | Verify `CYBERARK_OAUTH_CLIENT_ID` matches the Trust tab client ID (decode the token to check — see [JWT Validation](#jwt-validation)) |
| JWT `iss` claim mismatch | The issuer must be `{tenant_url}/{app_name}/` — verify the app name matches `CYBERARK_OIDC_APP_ID` (default: `mcpprivilegecloud`) |
