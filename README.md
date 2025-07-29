# CyberArk Privilege Cloud MCP Server

A production-ready Model Context Protocol (MCP) server for comprehensive CyberArk Privilege Cloud integration using the official ark-sdk-python library. Provides complete privileged access management through 45 enterprise-grade MCP tools covering all four PCloud services.

## Features

- **Complete Account Lifecycle**: Create, read, update, delete accounts with advanced search and password management (17 tools)
- **Comprehensive Safe Operations**: Full CRUD operations plus member management with granular permissions (11 tools)  
- **Platform Management**: Complete platform lifecycle including statistics, import/export, and target platform operations (10 tools)
- **Applications Management**: Full application lifecycle with authentication method management and statistics (9 tools)
- **Advanced Analytics**: Account filtering, grouping, distribution analysis, and environment categorization
- **Enterprise Security**: Built on official ark-sdk-python with OAuth, audit logging, and comprehensive error handling
- **Production Ready**: 144 passing tests, zero regression, complete API coverage with exact data fidelity

## Prerequisites

- Python 3.10+
- CyberArk Privilege Cloud service account

## Installation

```bash
# Recommended: Install from GitHub repository
uvx --from git+https://github.com/aaearon/mcp-privilege-cloud.git mcp-privilege-cloud

# Development: Clone repository
git clone https://github.com/aaearon/mcp-privilege-cloud.git
cd mcp-privilege-cloud
uv sync
```

## Configuration

Create `.env` file with required credentials:

```bash
CYBERARK_CLIENT_ID=your-service-account-username
CYBERARK_CLIENT_SECRET=your-service-account-password
```

Test configuration:
```bash
python -c "from mcp_privilege_cloud.server import CyberArkMCPServer; import asyncio; server = CyberArkMCPServer.from_environment(); print('Health:', asyncio.run(server.health_check())['status'])"
```

## Usage

### Running the Server

```bash
# Production
uvx --from git+https://github.com/aaearon/mcp-privilege-cloud.git mcp-privilege-cloud

# Development  
uv run mcp-privilege-cloud

# Module execution
python -m mcp_privilege_cloud
```

### Available Tools (45 Total)

**Account Management (17 tools):**
- **Core Operations**: `list_accounts`, `get_account_details`, `search_accounts`, `create_account`, `update_account`, `delete_account`
- **Password Management**: `change_account_password`, `set_next_password`, `verify_account_password`, `reconcile_account_password`
- **Advanced Search**: `filter_accounts_by_platform_group`, `filter_accounts_by_environment`, `filter_accounts_by_management_status`, `group_accounts_by_safe`, `group_accounts_by_platform`, `analyze_account_distribution`, `search_accounts_by_pattern`, `count_accounts_by_criteria`

**Safe Management (11 tools):**
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

## Client Integration

### Claude Code

Add the MCP server using the Claude Code CLI:

```bash
# Add MCP server from GitHub repository with environment variables
CYBERARK_CLIENT_ID=your-service-account-username CYBERARK_CLIENT_SECRET=your-service-account-password claude mcp add cyberark-privilege-cloud -- uvx --from git+https://github.com/aaearon/mcp-privilege-cloud.git mcp-privilege-cloud
```

### Claude Desktop

Add to your Claude Desktop MCP settings file:

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
        "CYBERARK_CLIENT_ID": "your-service-account-username",
        "CYBERARK_CLIENT_SECRET": "your-service-account-password"
      }
    }
  }
}
```

## Testing with MCP Inspector

**Quick Start:**
```bash
npx @modelcontextprotocol/inspector
```
Configure with server command `uvx --from git+https://github.com/aaearon/mcp-privilege-cloud.git mcp-privilege-cloud` and your service account credentials. Should show 45 tools available across all four PCloud services.

For comprehensive testing procedures, see [DEVELOPMENT.md](DEVELOPMENT.md).

## Testing

### Unit/Integration Tests
```bash
# Run all tests
uv run pytest

# Run with coverage  
uv run pytest --cov=mcp_privilege_cloud

# Integration tests
uv run pytest -m integration
```

### MCP Inspector CLI Testing
For programmatic testing and LLM-driven validation:

```bash
# Install inspector (one-time setup)
npm install @modelcontextprotocol/inspector

# Test with the single-file testing script
python test_mcp_cli.py health_check      # Server health check
python test_mcp_cli.py list_tools        # List all 45 tools
python test_mcp_cli.py call_tool list_accounts  # Test specific tool
python test_mcp_cli.py generate_report   # Full test report

# Python API for LLMs
from test_mcp_cli import MCPTester
tester = MCPTester()
tools = tester.list_tools()              # Get all tools
health = tester.test_server_health()     # Health check
```

The `test_mcp_cli.py` script provides a single-file solution for programmatic MCP server testing, designed for LLM integration and ad-hoc validation.

## Troubleshooting

**Common Issues:**

- **Missing environment variables**: Create `.env` file with credentials
- **Authentication failed**: Verify service account in CyberArk Identity
- **Permission errors**: Ensure safe permissions for service account
- **Connection issues**: Verify `.cloud` domain (not `.com`)

**Quick Health Check:**
```bash
python -c "from mcp_privilege_cloud.server import CyberArkMCPServer; import asyncio; server = CyberArkMCPServer.from_environment(); print('Status:', asyncio.run(server.health_check())['status'])"
```

## Documentation

- **[API Reference](docs/API_REFERENCE.md)** - Complete tool specifications
- **[Development Guide](DEVELOPMENT.md)** - Architecture and contributing
- **[Testing Guide](docs/TESTING.md)** - Detailed testing instructions

## Security

- Never commit credentials to version control
- Use secure environment variable management
- Grant minimal required permissions to service accounts
- Official SDK provides automatic token management and secure protocols

## License

[Add appropriate license information]

## Support

[Add support contact information]