# CyberArk Privilege Cloud MCP Server

A Model Context Protocol (MCP) server for CyberArk Privilege Cloud integration using the official ark-sdk-python library. Enables AI assistants to securely manage privileged accounts through 13 comprehensive MCP tools.

## Features

- **Account Management**: Create, list, search accounts and manage passwords
- **Safe Management**: List and get detailed safe information  
- **Platform Management**: List platforms and import platform packages
- **Official SDK**: Built on ark-sdk-python for enterprise reliability
- **Comprehensive Tools**: 13 MCP tools with exact API data

## Prerequisites

- Python 3.8+
- CyberArk Privilege Cloud service account

## Installation

```bash
# Recommended: Direct installation
uvx mcp-privilege-cloud

# Development: Clone repository
git clone <repository-url>
cd mcp-privilege-cloud
pip install -e .
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
uvx mcp-privilege-cloud

# Development  
uv run mcp-privilege-cloud

# Module execution
python -m mcp_privilege_cloud
```

### Available Tools

**Data Access:**
- `list_accounts`, `get_account_details`, `search_accounts`
- `list_safes`, `get_safe_details`  
- `list_platforms`, `get_platform_details`

**Account Management:**
- `create_account`
- `change_account_password`, `set_next_password`
- `verify_account_password`, `reconcile_account_password`

**Platform Management:**
- `import_platform_package`

## Client Integration

### Claude Code

Add the MCP server using the Claude Code CLI:

```bash
# Add MCP server from GitHub repository
claude mcp add cyberark-privilege-cloud -- uvx --from git+https://github.com/your-org/mcp-privilege-cloud.git mcp-privilege-cloud

# Set environment variables
export CYBERARK_CLIENT_ID=your-service-account-username
export CYBERARK_CLIENT_SECRET=your-service-account-password
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
        "git+https://github.com/your-org/mcp-privilege-cloud.git",
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
Configure with server command `uvx mcp-privilege-cloud` and your service account credentials. Should show 13 tools available.

For comprehensive testing procedures, see [DEVELOPMENT.md](DEVELOPMENT.md).

## Testing

```bash
# Run all tests
uv run pytest

# Run with coverage  
uv run pytest --cov=mcp_privilege_cloud

# Integration tests
uv run pytest -m integration
```

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