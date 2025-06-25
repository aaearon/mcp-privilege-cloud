# Quick Start Guide - Fixed Import Issue

## ✅ Issue Resolved
The import error has been fixed! You now have multiple ways to start the server.

## 📋 Prerequisites

Before starting the server, ensure you have:
- Python 3.8 or higher
- pipenv installed (`pip install pipenv`)

## 🚀 Setup and Installation

### First Time Setup
```bash
# Navigate to project directory
cd /mnt/c/Users/Tim/Projects/mcp-privilege-cloud

# Install dependencies and create virtual environment
pipenv install --dev

# Verify installation
pipenv graph
```

## 🚀 How to Start the Server

### Option 1: Using the New Entry Point (Recommended)
```bash
# Navigate to project directory
cd /mnt/c/Users/Tim/Projects/mcp-privilege-cloud

# Start server using pipenv (automatically handles virtual environment)
pipenv run python run_server.py
```

### Option 2: Using the Original MCP Server File
```bash
# Navigate to project directory
cd /mnt/c/Users/Tim/Projects/mcp-privilege-cloud

# Start server using pipenv (now with fixed imports)
pipenv run python src/cyberark_mcp/mcp_server.py
```

### Option 3: Using the Inspector Helper Script
```bash
# Navigate to project directory
cd /mnt/c/Users/Tim/Projects/mcp-privilege-cloud

# Start with helpful Inspector instructions using pipenv
pipenv run python start_for_inspector.py
```

## 🔧 What Was Fixed

The original error was:
```
ImportError: attempted relative import with no known parent package
```

**Root Cause:** The relative import `from .server import CyberArkMCPServer` failed when running the script directly.

**Solution Applied:**
1. Added proper path setup to locate the src directory
2. Added fallback import handling for direct execution
3. Created a dedicated entry point script (`run_server.py`)

## 🧪 Testing with MCP Inspector

### Step 1: Start the Server
```bash
pipenv run python run_server.py
```

**Expected Output:**
```
🚀 Starting CyberArk Privilege Cloud MCP Server...
INFO - Starting CyberArk Privilege Cloud MCP Server
ERROR - Missing required environment variables: [...]  # This is expected for testing
```

### Step 2: Install MCP Inspector
```bash
npm install -g @modelcontextprotocol/inspector
```

### Step 3: Connect Inspector
1. Open MCP Inspector in your browser
2. Choose **"Command"** connection type
3. Enter: `pipenv run python /mnt/c/Users/Tim/Projects/mcp-privilege-cloud/run_server.py`
4. Click **"Connect"**

**Note**: Make sure you're in the project directory when running the Inspector command, or use the full path with pipenv.

### Step 4: Test Tools
You should see these 6 tools available:
- `health_check`
- `list_accounts`
- `get_account_details`
- `search_accounts`
- `list_safes`
- `get_safe_details`

## 🔐 For Real CyberArk Testing

1. **Create `.env` file:**
   ```bash
   cp .env.example .env
   # Edit with your real CyberArk credentials
   ```

2. **Test connectivity:**
   ```bash
   pipenv run python -c "
   import asyncio, sys, os
   sys.path.insert(0, 'src')
   from cyberark_mcp.server import CyberArkMCPServer
   server = CyberArkMCPServer.from_environment()
   health = asyncio.run(server.health_check())
   print('Health Status:', health['status'])
   "
   ```

3. **Start server with real credentials:**
   ```bash
   pipenv run python run_server.py
   ```

## 🆘 Troubleshooting

### Server Won't Start
```bash
# Check Python environment
which python
python --version

# Check pipenv installation
which pipenv
pipenv --version

# Check virtual environment and dependencies
pipenv graph

# Run MVP test
pipenv run python test_mvp.py
```

### Import Errors
```bash
# Verify you're in the correct directory
pwd
ls -la run_server.py

# Check src directory exists
ls -la src/cyberark_mcp/

# Check pipenv virtual environment status
pipenv --venv
pipenv check
```

### Inspector Connection Issues
1. Ensure server is running and showing log output
2. Try the absolute path in Inspector command
3. Check firewall/antivirus isn't blocking the connection
4. Restart both server and Inspector

## ✅ Success Indicators

**Server Started Successfully:**
- No import errors
- Log messages appearing
- Server doesn't exit immediately

**Inspector Connected:**
- 6 tools visible in Inspector interface
- Tools show parameter schemas
- Can call `health_check` tool

**Real CyberArk Integration:**
- Health check returns "healthy" status
- Can list safes from your environment
- Account operations return real data

You're now ready to test with MCP Inspector! 🎉