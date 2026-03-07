# CyberArk Privilege Cloud MCP Server

An MCP server for CyberArk Privilege Cloud, built on the official [ark-sdk-python](https://github.com/cyberark/ark-sdk-python) library. Provides 53 tools for privileged access management.

Supports two authentication modes:
- **OAuth per-user mode** (recommended) -- each user authenticates with their own CyberArk Identity credentials via OAuth. Requires [Streamable HTTP transport](#docker-deployment) and an OIDC app in CyberArk Identity ([setup guide](docs/CYBERARK_IDENTITY_SETUP.md)).
- **Legacy service account mode** -- a single shared service account authenticates all requests via stdio transport. Simpler setup, shown in [Quick Start](#quick-start) below.

## Quick Start

> This sets up the **legacy service account mode** via stdio. For OAuth per-user mode, see [OAuth Per-User Mode](#oauth-per-user-mode).

**1. Install uv** (if not already installed):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**2. Configure Claude Desktop** - Add to your configuration file:

| OS | Configuration File Location |
|----|----------------------------|
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |
| Linux | `~/.config/Claude/claude_desktop_config.json` |

```json
{
  "mcpServers": {
    "cyberark-privilege-cloud": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/aaearon/mcp-privilege-cloud.git",
        "mcp-privilege-cloud"
      ],
      "env": {
        "CYBERARK_CLIENT_ID": "your-service-user-username",
        "CYBERARK_CLIENT_SECRET": "your-service-user-password"
      }
    }
  }
}
```

**3. Restart Claude Desktop** - The MCP server will appear in the tools menu (hammer icon) when connected.

### Claude Code

```bash
claude mcp add cyberark-privilege-cloud \
  -e CYBERARK_CLIENT_ID=your-service-user-username \
  -e CYBERARK_CLIENT_SECRET=your-service-user-password \
  -- uvx --from git+https://github.com/aaearon/mcp-privilege-cloud.git mcp-privilege-cloud
```

## Example Prompts

Once configured, you can ask Claude things like:

- "List all accounts in the Production safe"
- "Show me Windows accounts that are failing management"
- "Create a new safe called 'DevOps-Credentials' with 30-day retention"
- "Add the DevOps team as safe members with retrieve permissions"
- "List all active platforms and their account counts"
- "Show me active privileged sessions"

## Prerequisites

- [CyberArk Identity Service User](https://docs.cyberark.com/identity-administration/latest/en/content/ispss/ispss-add-service-user.htm) with:
  - Appropriate Identity roles for the desired operations (e.g., Privilege Cloud Administrator for platform management)
  - Safe permissions granting access to the safes and accounts you want to manage
- For OAuth per-user mode: an OIDC app in CyberArk Identity (see [setup guide](docs/CYBERARK_IDENTITY_SETUP.md))

## Configuration

### OAuth Per-User Mode

Each connecting user authenticates with their own CyberArk Identity credentials via OAuth. The server verifies user identity from the OIDC JWT, then uses a shared service account platform token for all PCloud API calls.

Requires Streamable HTTP transport -- see [Docker Deployment](#docker-deployment) or set `MCP_TRANSPORT=streamable-http` when running locally.

| Variable | Required | Description |
|----------|----------|-------------|
| `CYBERARK_IDENTITY_TENANT_URL` | Yes | CyberArk Identity tenant URL (e.g., `https://abc1234.id.cyberark.cloud`) |
| `CYBERARK_CLIENT_ID` | Yes | Service account login name (for PCloud platform token) |
| `CYBERARK_CLIENT_SECRET` | Yes | Service account password |
| `CYBERARK_OAUTH_CLIENT_ID` | Yes | OIDC app client ID from Trust tab (for DCR and JWT audience) |
| `CYBERARK_OAUTH_CLIENT_SECRET` | Yes | OIDC app client secret from Trust tab (injected server-side in /token proxy) |
| `MCP_TRANSPORT` | No | Transport protocol (default: `stdio`; set to `streamable-http` for OAuth) |
| `MCP_HOST` | No | Server bind host (default: `127.0.0.1`) |
| `MCP_PORT` | No | Server bind port (default: `8000`) |
| `MCP_SERVER_URL` | No | Public URL for OAuth metadata (default: `http://{host}:{port}`) |

See [CyberArk Identity Setup](docs/CYBERARK_IDENTITY_SETUP.md) for full configuration instructions.

### Legacy Service Account Mode

| Variable | Required | Description |
|----------|----------|-------------|
| `CYBERARK_CLIENT_ID` | Yes | Your Service User username |
| `CYBERARK_CLIENT_SECRET` | Yes | Your Service User password |

## Docker Deployment

The included `Dockerfile` and `docker-compose.yml` run the server in Streamable HTTP mode, suitable for OAuth per-user authentication and remote MCP clients.

```bash
# Create .env with your credentials (see .env.example)
docker compose up -d --build
```

When deploying behind a reverse proxy, configure it to strip trailing slashes from request paths. MCP clients may POST to `/mcp/` (trailing slash), causing a 307 redirect that strips the `Authorization` header. Set `MCP_SERVER_URL` to the public URL of your server.

## Available Tools (53 Total)

**Account Management (18 tools):**
- **Core Operations**: `list_accounts`, `get_account_details`, `search_accounts`, `create_account`, `update_account`, `delete_account`
- **Password Management**: `change_account_password`, `set_next_password`, `verify_account_password`, `reconcile_account_password`
- **Advanced Search**: `filter_accounts_by_platform_group`, `filter_accounts_by_environment`, `filter_accounts_by_management_status`, `group_accounts_by_safe`, `group_accounts_by_platform`, `analyze_account_distribution`, `search_accounts_by_pattern`, `count_accounts_by_criteria`

**Safe Management (10 tools):**
- **Core Operations**: `list_safes`, `get_safe_details`, `add_safe`, `update_safe`, `delete_safe`
- **Member Management**: `list_safe_members`, `get_safe_member_details`, `add_safe_member`, `update_safe_member`, `remove_safe_member`

**Platform Management (10 tools):**
- **Core Operations**: `list_platforms`, `get_platform_details`, `import_platform_package`, `export_platform`
- **Lifecycle Management**: `duplicate_target_platform`, `activate_target_platform`, `deactivate_target_platform`, `delete_target_platform`
- **Statistics**: `get_platform_statistics`, `get_target_platform_statistics`

**Applications Management (9 tools):**
- **Core Operations**: `list_applications`, `get_application_details`, `add_application`, `delete_application`
- **Auth Methods**: `list_application_auth_methods`, `get_application_auth_method_details`, `add_application_auth_method`, `delete_application_auth_method`
- **Statistics**: `get_applications_stats`

**Session Monitoring (6 tools):**
- **Session Management**: `list_sessions`, `list_sessions_by_filter`, `get_session_details`, `count_sessions`
- **Activity Tracking**: `list_session_activities`, `get_session_statistics`

## Troubleshooting

| Issue | Solution |
|-------|----------|
| MCP not appearing in Claude | Restart Claude Desktop after saving configuration |
| Authentication failed | Verify Service User credentials in CyberArk Identity |
| Permission errors | Ensure the Service User has appropriate Identity roles and safe permissions |
| Connection issues | Verify you're using the `.cloud` domain (not `.com`) |
| OAuth 401 behind reverse proxy | Ensure the proxy strips trailing slashes (see [Docker Deployment](#docker-deployment)) |
| `uvx` not found | Install uv: `curl -LsSf https://astral.sh/uv/install.sh \| sh` |

**Verify MCP server manually:**
```bash
uvx --from git+https://github.com/aaearon/mcp-privilege-cloud.git mcp-privilege-cloud
```

## Development

```bash
git clone https://github.com/aaearon/mcp-privilege-cloud.git
cd mcp-privilege-cloud
uv sync
uv run pytest                              # Run all tests
uv run pytest --cov=mcp_privilege_cloud    # Run with coverage
uv run mcp-privilege-cloud                 # Run the server locally
```

## Documentation

- **[API Reference](docs/API_REFERENCE.md)** - Complete tool specifications and parameters
- **[Architecture](docs/ARCHITECTURE.md)** - System design and components
- **[CyberArk Identity Setup](docs/CYBERARK_IDENTITY_SETUP.md)** - OAuth app configuration guide
- **[Development Guide](docs/DEVELOPMENT.md)** - Contributing and development workflows
- **[Testing Guide](docs/TESTING.md)** - Detailed testing instructions

## Security

- Never commit credentials to version control
- Use secure environment variable management
- Grant minimal required permissions to Service Users
- In OAuth mode, DCR returns public clients only -- secrets are injected server-side
- Official SDK provides automatic token management and secure protocols

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

For issues and feature requests, please use [GitHub Issues](https://github.com/aaearon/mcp-privilege-cloud/issues).
