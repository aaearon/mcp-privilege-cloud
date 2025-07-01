# CyberArk Privilege Cloud MCP Server

## Purpose
A Model Context Protocol (MCP) server that provides seamless integration with CyberArk Privilege Cloud. This server enables AI assistants and other MCP clients to interact with CyberArk's privileged account management capabilities.

## Tech Stack
- **Language**: Python 3.8+
- **Core Framework**: FastMCP (MCP protocol implementation)
- **HTTP Client**: aiohttp for async API requests
- **Authentication**: OAuth 2.0 client credentials flow
- **Testing**: pytest with asyncio support
- **Environment**: Virtual environments with .env configuration

## Key Components
- **Authentication Module** (`src/mcp_privilege_cloud/auth.py`): OAuth 2.0 token management
- **Server Module** (`src/mcp_privilege_cloud/server.py`): Core CyberArk API integration  
- **MCP Integration** (`src/mcp_privilege_cloud/mcp_server.py`): FastMCP server with 10+ tools
- **Entry Point** (`run_server.py`): Multiplatform server runner with Windows UTF-8 support

## API Integration
- Base URL: `https://{subdomain}.privilegecloud.cyberark.cloud/PasswordVault/api`
- Auth URL: `https://{tenant-id}.id.cyberark.cloud/oauth2/platformtoken`
- Uses Gen2 API endpoints exclusively (when both Gen1/Gen2 available)
- 15-minute token expiration with automatic refresh