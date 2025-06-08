# CyberArk Privilege Cloud MCP Server

A Model Context Protocol (MCP) server that provides seamless integration with CyberArk Privilege Cloud. This server enables AI assistants and other MCP clients to interact with CyberArk's privileged account management capabilities.

## Features

### Current (MVP)
- **Account Management**: List, search, and retrieve detailed account information
- **Safe Management**: List and view safe information  
- **OAuth 2.0 Authentication**: Secure API token authentication with CyberArk Identity
- **Health Monitoring**: Built-in health check functionality
- **Comprehensive Logging**: Detailed logging for all operations
- **Error Handling**: Robust error handling with automatic token refresh

### Planned (Future Releases)
- Password management operations
- Account lifecycle management (create, update, delete)
- Session monitoring and management
- Platform management
- Advanced reporting and analytics

## Prerequisites

- Python 3.8 or higher
- CyberArk Privilege Cloud tenant
- CyberArk Identity service account with appropriate permissions

## Installation

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

### Environment Variables

Create a `.env` file in the project root with the following variables:

```bash
# Required: CyberArk Identity tenant ID
CYBERARK_IDENTITY_TENANT_ID=your-tenant-id

# Required: Service account credentials  
CYBERARK_CLIENT_ID=your-service-account-username
CYBERARK_CLIENT_SECRET=your-service-account-password

# Required: CyberArk Privilege Cloud subdomain
CYBERARK_SUBDOMAIN=your-privilege-cloud-subdomain

# Optional: Configuration settings
CYBERARK_API_TIMEOUT=30
CYBERARK_MAX_RETRIES=3
CYBERARK_LOG_LEVEL=INFO
```

### CyberArk Service Account Setup

1. **Create OAuth Service Account**:
   - Log into CyberArk Identity Administration portal
   - Create a new service user
   - Enable "Is OAuth confidential client" setting
   - Note the username (client_id) and password (client_secret)

2. **Assign Permissions**:
   - Assign appropriate service roles for account management
   - Ensure the service account has permissions to:
     - List Accounts in target safes
     - View Account Details
     - Access Safe information

3. **Test Configuration**:
   ```bash
   python -c "
   from src.cyberark_mcp.server import CyberArkMCPServer
   import asyncio
   server = CyberArkMCPServer.from_environment()
   health = asyncio.run(server.health_check())
   print('Health:', health['status'])
   "
   ```

## Usage

### Running the MCP Server

```bash
# Direct execution
python src/cyberark_mcp/mcp_server.py

# Or using the module
python -m src.cyberark_mcp.mcp_server
```

### Available Tools

The server provides the following MCP tools:

#### `list_accounts`
List accounts from CyberArk Privilege Cloud with optional filters.

```python
# Parameters:
# - safe_name (optional): Filter by safe name
# - username (optional): Filter by username  
# - address (optional): Filter by address/hostname

# Example usage in MCP client:
await client.call_tool("list_accounts", {"safe_name": "IT-Infrastructure"})
```

#### `get_account_details`
Get detailed information about a specific account.

```python
# Parameters:
# - account_id (required): Unique account identifier

# Example:
await client.call_tool("get_account_details", {"account_id": "123_456"})
```

#### `search_accounts`
Search for accounts using various criteria.

```python
# Parameters:
# - keywords (optional): Search keywords
# - safe_name (optional): Filter by safe name
# - username (optional): Filter by username
# - address (optional): Filter by address
# - platform_id (optional): Filter by platform

# Example:
await client.call_tool("search_accounts", {
    "keywords": "admin",
    "safe_name": "Database-Safes"
})
```

#### `list_safes`
List all accessible safes.

```python
# Parameters:
# - search (optional): Search term for safe names

# Example:
await client.call_tool("list_safes", {"search": "Database"})
```

#### `get_safe_details`
Get detailed information about a specific safe.

```python
# Parameters:
# - safe_name (required): Name of the safe

# Example:
await client.call_tool("get_safe_details", {"safe_name": "IT-Infrastructure"})
```

#### `health_check`
Perform a health check of the CyberArk connection.

```python
# No parameters required

# Example:
await client.call_tool("health_check", {})
```

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

- `tests/test_auth.py`: Authentication and token management tests
- `tests/test_server.py`: Core server functionality tests
- `tests/test_account_mgmt.py`: Account management operation tests
- `tests/test_integration.py`: End-to-end integration tests

## MCP Inspector Testing

The MCP Inspector is a tool for testing and debugging MCP servers.

### Installation

```bash
npx @modelcontextprotocol/inspector
```

### Testing with Inspector

1. **Start the MCP Server**:
   ```bash
   python src/cyberark_mcp/mcp_server.py
   ```

2. **Connect Inspector**:
   - Open MCP Inspector in your browser
   - Connect to your server endpoint
   - Test available tools and resources

3. **Verify Functionality**:
   - Test `health_check` tool first
   - Try `list_safes` to verify permissions
   - Test account operations with appropriate parameters

### Example Inspector Test Sequence

1. **Health Check**:
   ```json
   {
     "tool": "health_check",
     "arguments": {}
   }
   ```

2. **List Safes**:
   ```json
   {
     "tool": "list_safes", 
     "arguments": {}
   }
   ```

3. **List Accounts** (if you have a known safe):
   ```json
   {
     "tool": "list_accounts",
     "arguments": {
       "safe_name": "your-safe-name"
     }
   }
   ```

## Troubleshooting

### Common Issues

1. **Authentication Errors (401)**:
   - Verify service account credentials
   - Check that OAuth is enabled for the service account
   - Ensure tenant ID is correct

2. **Permission Errors (403)**:
   - Verify service account has required permissions
   - Check safe-level permissions for account operations

3. **Network Errors**:
   - Verify subdomain is correct
   - Check firewall/network connectivity
   - Verify CyberArk Privilege Cloud is accessible

4. **Rate Limiting (429)**:
   - Reduce request frequency
   - Implement backoff strategies in client code

### Debug Mode

Enable debug logging:

```bash
export CYBERARK_LOG_LEVEL=DEBUG
python src/cyberark_mcp/mcp_server.py
```

### Health Check

Use the built-in health check to verify connectivity:

```bash
python -c "
import asyncio
from src.cyberark_mcp.server import CyberArkMCPServer
server = CyberArkMCPServer.from_environment()
health = asyncio.run(server.health_check())
print(f'Status: {health[\"status\"]}')
if health['status'] == 'healthy':
    print(f'Safes accessible: {health[\"safes_accessible\"]}')
else:
    print(f'Error: {health[\"error\"]}')
"
```

## Security Considerations

- **Credential Storage**: Never commit credentials to version control
- **Environment Variables**: Use secure methods to manage environment variables
- **Network Security**: Ensure all communications use HTTPS
- **Principle of Least Privilege**: Grant minimal required permissions to service accounts
- **Token Management**: Tokens are automatically refreshed and cached securely
- **Logging**: Sensitive information is never logged

## Development

### Project Structure

```
mcp-privilege-cloud/
├── src/cyberark_mcp/
│   ├── __init__.py
│   ├── auth.py              # Authentication module
│   ├── server.py            # Core server functionality  
│   └── mcp_server.py        # MCP protocol integration
├── tests/
│   ├── test_auth.py         # Authentication tests
│   ├── test_server.py       # Server tests
│   ├── test_account_mgmt.py # Account management tests
│   └── test_integration.py  # Integration tests
├── requirements.txt         # Python dependencies
├── pytest.ini             # Test configuration
├── .env.example            # Environment variable template
└── README.md              # This file
```

### Contributing

1. Follow Test-Driven Development (TDD) principles
2. Write tests before implementing features
3. Maintain high test coverage
4. Follow Python PEP 8 style guidelines
5. Add comprehensive logging for new features

## License

[Add appropriate license information]

## Support

[Add support contact information]