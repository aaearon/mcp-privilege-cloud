# Coding Standards and Patterns

## Code Style Guidelines
- **PEP 8**: Follow Python PEP 8 style guide
- **Type Hints**: Use type hints for all function parameters and returns
- **Docstrings**: Comprehensive docstrings for all public methods
- **Line Length**: Maximum 100 characters
- **Naming**: Meaningful variable and function names

## Testing Standards
- **TDD**: Test-Driven Development - write tests first
- **Coverage**: Minimum 80% test coverage
- **Async**: Use `@pytest.mark.asyncio` for async tests
- **Markers**: Use pytest markers: `@pytest.mark.auth`, `@pytest.mark.integration`
- **Mocking**: Mock external dependencies (CyberArk APIs)
- **Fixtures**: Use pytest fixtures for shared test data

## Error Handling Strategy
- **Authentication (401)**: Automatic token refresh and retry
- **Permissions (403)**: Clear error messages with guidance
- **Rate Limiting (429)**: Exponential backoff (future enhancement)
- **Network Errors**: Comprehensive logging and user-friendly messages
- **Never log sensitive data**: tokens, passwords, secrets

## Security Practices
- **Environment Variables**: Use exclusively for configuration
- **Token Caching**: Secure with automatic refresh
- **.gitignore**: Prevent credential commits
- **Principle of Least Privilege**: Service accounts with minimal permissions

## API Integration Patterns
- **Gen2 Endpoints**: Always use Gen2 when available (not Gen1)
- **Response Parsing**: Handle inconsistent field names (`value` vs `Platforms`)
- **URL Encoding**: Proper encoding for special characters
- **Error Responses**: Consistent error handling across all endpoints
- **Pagination**: Support for offset/limit parameters