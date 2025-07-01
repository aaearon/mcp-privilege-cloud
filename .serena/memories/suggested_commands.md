# Suggested Commands for CyberArk MCP Server Development

## Core Development Commands

### Testing
```bash
# Run all tests
pytest

# Run specific test categories
pytest -m auth           # Authentication tests only
pytest -m integration    # Integration tests only
pytest -k platform      # Platform management tests
pytest -k safe          # Safe management tests

# Run with coverage
pytest --cov=src/mcp_privilege_cloud

# Exclude integration tests (for CI)
pytest -m "not integration"
```

### Running the Server
```bash
# Main entry point (cross-platform)
python run_server.py

# Alternative direct execution
python -m mcp_privilege_cloud.mcp_server
```

### Environment Setup
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate      # Linux/Mac
venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt
```

### Development Tools
```bash
# Use fdfind instead of find for file searching
fdfind "*.py" tests/

# Use rg instead of grep for text searching
rg "pytest\.fixture" tests/

# Use ast-grep for code structure search
ast-grep --lang python -p 'class $NAME'

# Use jq for JSON manipulation
echo '{"key": "value"}' | jq .

# Use gh for GitHub operations
gh pr create --title "New feature"
```

### Environment Configuration
```bash
# Create .env file with required variables
cat > .env << EOF
CYBERARK_IDENTITY_TENANT_ID=your-tenant-id
CYBERARK_CLIENT_ID=service-account-username
CYBERARK_CLIENT_SECRET=service-account-password
CYBERARK_SUBDOMAIN=your-subdomain
EOF
```

### Debug Commands
```bash
# Test configuration
python -c "from src.mcp_privilege_cloud.server import CyberArkMCPServer; import asyncio; server = CyberArkMCPServer.from_environment(); print(asyncio.run(server.health_check()))"

# Test authentication
python -c "from src.mcp_privilege_cloud.auth import CyberArkAuthenticator; import asyncio; auth = CyberArkAuthenticator.from_environment(); print(asyncio.run(auth.get_auth_header()))"
```