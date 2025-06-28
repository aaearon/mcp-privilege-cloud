# General Coding Instructions

- Write in Python.
- Use consistent naming conventions seen in Python best practices.
- Follow test driven development (TDD) principles.
- Write clear and concise comments to explain complex logic.
- Follow DRY (Don't Repeat Yourself) principles to reduce code duplication.
- Keep dependencies up to date and remove unused ones.
- Use environment variables for sensitive information (e.g., API keys).
- Use meaningful commit messages that describe the changes made.
- Start with the smallest possible implementation that meets the requirements.
- Use Python virtual environments to keep dependencies manageable.

# Writing a MCP Server

- Refer to the [MCP Protocol documentation](https://modelcontextprotocol.io) for detailed information on implementing the server.
- Refer to the [MCP Protocol GitHub repository](https://github.com/modelcontextprotocol/python-sdk) for source code and issues.
- Ensure the server can be tested with a valid CyberArk environment.
- Implement logging for all operations, especially for error handling.

# Privilege Cloud information

- Use [API token authentication for CyberArk Identity Shared Services](https://stoplight.io/api/v1/projects/cHJqOjI1MDczMQ/nodes/2c297daca8a97-api-token-authentication-for-cyber-ark-identity-security-platform-shared-services)
- Leverage the CyberArk Privilege Cloud official API documentation at https://docs.cyberark.com/privilege-cloud-shared-services/latest/en/content/webservices/implementing%20privileged%20account%20security%20web%20services%20.htm
- Reference the CyberArk Privilege Cloud API Bruno collection at https://github.com/IAM-Jah/CyberArk-REST-API-Bruno/tree/main/Privilege%20Cloud%20and%20Shared%20Services%20REST%20API as needed.
- Refer to the official [Python SDK for CyberArk](https://github.com/cyberark/ark-sdk-python) for information about API endpoints.
- You MUST NOT assume any specific knowledge about CyberArk Privilege Cloud or its APIs.

# MCP Inspector

- Provide information on how to test the MCP server using the MCP Inspector.
- Review the documentation for MCP Inspector at https://modelcontextprotocol.io/docs/tools/inspector