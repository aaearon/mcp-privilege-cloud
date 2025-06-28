# Task Completion Checklist

## For Every Task Completion

### 1. Testing Requirements
- [ ] Write tests first (TDD approach)
- [ ] All tests pass: `pytest`
- [ ] Specific test categories pass if applicable
- [ ] Integration tests excluded for unit testing: `pytest -m "not integration"`
- [ ] Coverage maintained: `pytest --cov=src/cyberark_mcp`

### 2. Code Quality
- [ ] Follow PEP 8 style guidelines
- [ ] Add type hints to all new functions
- [ ] Write comprehensive docstrings
- [ ] Handle errors appropriately
- [ ] No sensitive data in logs

### 3. Documentation Updates
- [ ] Update CLAUDE.md if architecture changes
- [ ] Update README.md if new features added
- [ ] Update docstrings for public methods
- [ ] Add comments for complex logic

### 4. Version Control
- [ ] Use feature branch Git workflow
- [ ] Meaningful commit messages
- [ ] Group related changes in single commit
- [ ] Update documentation as part of same task

### 5. Environment Considerations
- [ ] Windows compatibility maintained
- [ ] Virtual environment setup documented
- [ ] Required environment variables documented
- [ ] No hardcoded paths or credentials

### 6. MCP Integration
- [ ] New tools properly registered in MCP server
- [ ] Tool parameter validation implemented
- [ ] Error handling for MCP tool execution
- [ ] Test with MCP Inspector if new tools added

### 7. Final Verification
- [ ] Manual testing with `python run_server.py`
- [ ] Check CI/CD pipeline passes (GitHub Actions)
- [ ] Verify no breaking changes to existing functionality
- [ ] Confirm task objectives fully met