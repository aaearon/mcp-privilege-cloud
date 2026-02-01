# CyberArk Privilege Cloud MCP Server

An MCP server for CyberArk Privilege Cloud, built on the official [ark-sdk-python](https://github.com/cyberark/ark-sdk-python) library. Provides 53 tools for privileged access management.

## Quick Start

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

## Example Prompts

Once configured, you can ask Claude things like:

**Account Management:**
- "List all accounts in the Production safe"
- "Show me Windows accounts that are failing management"
- "Create a new local admin account for server PROD-WEB-01"
- "Which accounts haven't had their passwords changed in 90 days?"

**Safe Management:**
- "Create a new safe called 'DevOps-Credentials' with 30-day retention"
- "Add the DevOps team as safe members with retrieve permissions"
- "Show me all safes and their member counts"

**Platform & Session Monitoring:**
- "List all active platforms and their account counts"
- "Show me active privileged sessions"
- "Get session activity for the last hour"

## Prerequisites

- [CyberArk Identity Service User](https://docs.cyberark.com/identity-administration/latest/en/content/ispss/ispss-add-service-user.htm) with:
  - Appropriate Identity roles for the desired operations (e.g., Privilege Cloud Administrator for platform management)
  - Safe permissions granting access to the safes and accounts you want to manage

## Client Integration

### Claude Desktop

See [Quick Start](#quick-start) above for configuration.

If the configuration file doesn't exist, create it. If it already exists with other MCP servers, add the `cyberark-privilege-cloud` entry to the existing `mcpServers` object.

### Claude Code

Add the MCP server using the Claude Code CLI:

```bash
claude mcp add cyberark-privilege-cloud \
  -e CYBERARK_CLIENT_ID=your-service-user-username \
  -e CYBERARK_CLIENT_SECRET=your-service-user-password \
  -- uvx --from git+https://github.com/aaearon/mcp-privilege-cloud.git mcp-privilege-cloud
```

## Available Tools (53 Total)

**Account Management (18 tools):**
- **Core Operations**: `list_accounts`, `get_account_details`, `search_accounts`, `create_account`, `update_account`, `delete_account`
- **Password Management**: `change_account_password`, `set_next_password`, `verify_account_password`, `reconcile_account_password`
- **Advanced Search**: `filter_accounts_by_platform_group`, `filter_accounts_by_environment`, `filter_accounts_by_management_status`, `group_accounts_by_safe`, `group_accounts_by_platform`, `analyze_account_distribution`, `search_accounts_by_pattern`, `count_accounts_by_criteria`

**Safe Management (11 tools):**
- **Core Operations**: `list_safes`, `get_safe_details`, `add_safe`, `update_safe`, `delete_safe`
- **Member Management**: `list_safe_members`, `get_safe_member_details`, `add_safe_member`, `update_safe_member`, `remove_safe_member`

**Platform Management (12 tools):**
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

## Features

- **Complete Account Lifecycle**: Create, read, update, delete accounts with advanced search and password management
- **Comprehensive Safe Operations**: Full CRUD operations plus member management with granular permissions
- **Platform Management**: Complete platform lifecycle including statistics, import/export, and target platform operations
- **Applications Management**: Full application lifecycle with authentication method management
- **Session Monitoring**: Real-time session tracking, activity monitoring, and analytics
- **Enterprise Security**: Built on official ark-sdk-python with OAuth and comprehensive error handling

## Configuration

The MCP server requires two environment variables for authentication:

| Variable | Description |
|----------|-------------|
| `CYBERARK_CLIENT_ID` | Your Service User username |
| `CYBERARK_CLIENT_SECRET` | Your Service User password |

**For Claude Desktop/Claude Code**: Pass these directly in the configuration (see [Client Integration](#client-integration)). No `.env` file is needed.

**For local development/testing**: Create a `.env` file in the project root directory:

```bash
CYBERARK_CLIENT_ID=your-service-user-username
CYBERARK_CLIENT_SECRET=your-service-user-password
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| MCP not appearing in Claude | Restart Claude Desktop after saving configuration |
| Authentication failed | Verify Service User credentials in CyberArk Identity |
| Permission errors | Ensure the Service User has appropriate Identity roles and safe permissions |
| Connection issues | Verify you're using the `.cloud` domain (not `.com`) |
| `uvx` not found | Install uv: `curl -LsSf https://astral.sh/uv/install.sh \| sh` |

**Verify MCP server manually:**
```bash
uvx --from git+https://github.com/aaearon/mcp-privilege-cloud.git mcp-privilege-cloud
```

## Development

### Installation

```bash
git clone https://github.com/aaearon/mcp-privilege-cloud.git
cd mcp-privilege-cloud
uv sync
```

### Running Tests

```bash
uv run pytest                              # Run all tests
uv run pytest --cov=mcp_privilege_cloud    # Run with coverage
uv run pytest -m integration               # Integration tests only
```

### Running the Server Locally

```bash
uv run mcp-privilege-cloud      # With uv
python -m mcp_privilege_cloud   # Direct module execution
```

### Testing with MCP Inspector

```bash
npx @modelcontextprotocol/inspector
```

Configure with command `uv run mcp-privilege-cloud` and your credentials.

## Documentation

- **[API Reference](docs/API_REFERENCE.md)** - Complete tool specifications and parameters
- **[Architecture](ARCHITECTURE.md)** - System design and components
- **[Development Guide](DEVELOPMENT.md)** - Contributing and development workflows
- **[Testing Guide](docs/TESTING.md)** - Detailed testing instructions

## Security

- Never commit credentials to version control
- Use secure environment variable management
- Grant minimal required permissions to Service Users
- Official SDK provides automatic token management and secure protocols

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

For issues and feature requests, please use [GitHub Issues](https://github.com/aaearon/mcp-privilege-cloud/issues).
