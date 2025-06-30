# CyberArk Privilege Cloud MCP Server

A Model Context Protocol (MCP) server that provides seamless integration with CyberArk Privilege Cloud. This server enables AI assistants and other MCP clients to interact with CyberArk's privileged account management capabilities.

## Features

### Current (MVP+)
- **Account Management**: List, search, retrieve detailed information, and create new privileged accounts
- **Safe Management**: List and view safe information
- **Platform Management**: List available platforms and view detailed platform configurations
- **OAuth 2.0 Authentication**: Secure API token authentication with CyberArk Identity
- **Health Monitoring**: Built-in health check functionality
- **Comprehensive Logging**: Detailed logging for all operations
- **Error Handling**: Robust error handling with automatic token refresh

### Planned (Future Releases)
- Password management operations (retrieve, change, verify)
- Account lifecycle management (update, delete)
- Session monitoring and management
- Advanced reporting and analytics

## Prerequisites

- Python 3.8 or higher
- CyberArk Privilege Cloud tenant
- CyberArk Identity service account with appropriate permissions

## Installation

### Recommended Installation (using `uv`)

1. **Install uv** (Python package manager):
   ```bash
   # macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Windows
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   
   # Or via pip
   pip install uv
   ```

2. **Install the MCP server**:
   ```bash
   # Production installation
   uvx mcp-privilege-cloud
   
   # Or clone for development
   git clone <repository-url>
   cd mcp-privilege-cloud
   ```

### Alternative Installation (traditional Python)

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd mcp-privilege-cloud
   ```

2. **Create and activate virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

### Quick Setup

1. **Create `.env` file** with required credentials:
   ```bash
   CYBERARK_IDENTITY_TENANT_ID=your-tenant-id
   CYBERARK_CLIENT_ID=your-service-account-username
   CYBERARK_CLIENT_SECRET=your-service-account-password
   CYBERARK_SUBDOMAIN=your-privilege-cloud-subdomain
   ```

2. **Test configuration**:
   ```bash
   python -c "from src.cyberark_mcp.server import CyberArkMCPServer; import asyncio; server = CyberArkMCPServer.from_environment(); print('Health:', asyncio.run(server.health_check())['status'])"
   ```

For detailed setup instructions, service account configuration, and troubleshooting, see [Troubleshooting Guide](docs/TROUBLESHOOTING.md).

## Usage

### Running the MCP Server

#### Standardized Execution Methods (Recommended)

```bash
# Primary: Production execution (requires installation via uvx)
uvx mcp-privilege-cloud

# Development: Execute from project directory
uv run mcp-privilege-cloud

# Module execution: Standard Python module approach
python -m cyberark_mcp
```

#### Legacy Execution Methods

```bash
# Legacy: Multiplatform launcher (deprecated)
python run_server.py

# Legacy: Direct execution (deprecated)  
python src/cyberark_mcp/mcp_server.py

# Legacy: Module path execution (deprecated)
python -m src.cyberark_mcp.mcp_server
```

> **Note**: The standardized execution methods (`uvx` and `uv run`) are now the recommended approach for running the MCP server. Legacy methods are maintained for backward compatibility but may be removed in future versions.

### Available Tools

The server provides 10 MCP tools for CyberArk operations:

- **Account Management**: `list_accounts`, `get_account_details`, `search_accounts`, `create_account`
- **Safe Management**: `list_safes`, `get_safe_details` 
- **Platform Management**: `list_platforms`, `get_platform_details`
- **System**: `health_check`

For detailed tool specifications, parameters, and examples, see [API Reference](docs/API_REFERENCE.md).

## Standardized MCP Server Approach

This project follows the MCP server standardization guidelines with:

### Modern Execution Methods
- **`uvx mcp-privilege-cloud`**: Direct execution without local installation
- **`uv run mcp-privilege-cloud`**: Development execution with dependency management
- **`python -m cyberark_mcp`**: Standard Python module execution

### Key Benefits
- **Simplified deployment**: No manual dependency management required
- **Consistent experience**: Standardized across all MCP servers
- **Development efficiency**: `uv` handles virtual environments automatically
- **Production ready**: Direct execution with `uvx` for end users

### Migration from Legacy Methods
If you're currently using legacy execution methods (`python run_server.py`), we recommend migrating to the standardized approach:

1. Install `uv`: Follow the installation instructions above
2. Use `uvx mcp-privilege-cloud` for production deployments
3. Use `uv run mcp-privilege-cloud` for development work
4. Update any automation or integration scripts

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest -m auth      # Authentication tests
pytest -m unit      # Unit tests
pytest -m integration  # Integration tests

# Run with coverage
pytest --cov=src/cyberark_mcp

# Verbose output
pytest -v
```

### Test Structure

- `tests/test_core_functionality.py`: Authentication, server core, and platform management tests (64+ tests)
- `tests/test_account_operations.py`: Account lifecycle management tests (35+ tests)
- `tests/test_mcp_integration.py`: MCP tool wrappers and integration tests (15+ tests)
- `tests/test_integration.py`: End-to-end integration tests (10+ tests)

## MCP Inspector Testing

Quick start for testing with MCP Inspector:
1. Install: `npx @modelcontextprotocol/inspector`
2. Start server: `uvx mcp-privilege-cloud` (recommended) or `python run_server.py` (legacy)
3. Connect Inspector to test tools interactively

For detailed testing instructions, see [Testing Guide](docs/TESTING.md).

## Troubleshooting

For comprehensive troubleshooting, setup issues, and debugging guidance, see [Troubleshooting Guide](docs/TROUBLESHOOTING.md).

## Security Considerations

- **Credential Storage**: Never commit credentials to version control
- **Environment Variables**: Use secure methods to manage environment variables
- **Network Security**: Ensure all communications use HTTPS
- **Principle of Least Privilege**: Grant minimal required permissions to service accounts
- **Token Management**: Tokens are automatically refreshed and cached securely
- **Logging**: Sensitive information is never logged

## Documentation

### User Guides
- **[API Reference](docs/API_REFERENCE.md)** - Complete tool specifications with examples
- **[Testing Guide](docs/TESTING.md)** - Test execution and MCP Inspector usage
- **[Troubleshooting Guide](docs/TROUBLESHOOTING.md)** - Setup, debugging, and common issues

### Developer Guides  
- **[Development Guide](DEVELOPMENT.md)** - Architecture, contributing, and code standards
- **[Project Instructions](INSTRUCTIONS.md)** - Development workflow and patterns

## Contributing

1. Follow Test-Driven Development (TDD) principles
2. Write tests before implementing features  
3. Maintain high test coverage
4. Follow Python PEP 8 style guidelines
5. Add comprehensive logging for new features

For detailed development information, see [DEVELOPMENT.md](DEVELOPMENT.md).

## License

[Add appropriate license information]

## Support

[Add support contact information]