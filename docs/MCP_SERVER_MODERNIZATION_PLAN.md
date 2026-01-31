# MCP Server Modernization Plan (TDD Approach)

**Status:** APPROVED - All Phases
**Created:** 2026-01-31
**Scope:** Full modernization (Phases 1-4)

## Overview

Modernize the CyberArk MCP server to leverage current `mcp` SDK (v1.26.0) features including typed return values, lifespan management, and structured output.

## TDD Workflow Per Phase

Each phase follows: **RED** (failing test) → **GREEN** (minimal implementation) → **REFACTOR** (improve)

---

## Phase 1: Response Models (High Priority)

### 1.1 Create Response Model Definitions

**RED - Write failing tests first:**
- Create `tests/test_response_models.py` with model validation tests
- Test JSON schema generation for MCP compatibility

**GREEN - Implement models:**
- Create `src/mcp_privilege_cloud/models.py` with Pydantic models
- Models: AccountDetails, AccountSummary, SafeDetails, SafeMember, PlatformDetails, ApplicationDetails, SessionDetails

**Files:**
- CREATE: `src/mcp_privilege_cloud/models.py`
- CREATE: `tests/test_response_models.py`

### 1.2 Update Tool Return Types

**RED - Test typed returns:**
- Create `tests/test_typed_tools.py` with typed return tests

**GREEN - Update tool signatures:**
- Update high-use tools to return Pydantic models

**Files:**
- MODIFY: `src/mcp_privilege_cloud/mcp_server.py`

---

## Phase 2: Lifespan Management (Medium Priority)

### 2.1 Implement Lifespan Context

**RED - Test lifespan initialization:**
- Create `tests/test_lifespan.py` with lifecycle tests

**GREEN - Implement lifespan:**
- Create `AppContext` dataclass
- Implement `app_lifespan()` async context manager
- Pass to `FastMCP(lifespan=app_lifespan)`

**Files:**
- MODIFY: `src/mcp_privilege_cloud/mcp_server.py`
- CREATE: `tests/test_lifespan.py`

---

## Phase 3: Context Injection (Medium Priority)

### 3.1 Update Tools to Use Context

**RED - Test context access:**
- Create `tests/test_context_injection.py`

**GREEN - Update tool signatures:**
- Add `ctx: Context[ServerSession, AppContext]` parameter
- Access server via `ctx.request_context.lifespan_context.server`

**Files:**
- MODIFY: `src/mcp_privilege_cloud/mcp_server.py`
- CREATE: `tests/test_context_injection.py`

---

## Phase 4: Remove Legacy Code (Low Priority)

### 4.1 Remove Manual Dict Conversion

- Delete `_convert_to_dict()` function
- Delete `execute_tool()` wrapper
- Tools call server methods directly via context

### 4.2 Remove Legacy Globals

- Remove global `server` variable
- Remove `get_server()` function
- Remove `reset_server()` function
- Update `conftest.py` fixtures

---

## Implementation Order (TDD Cycles)

### Cycle 1: Models Foundation
1. Write `test_response_models.py` with model tests (RED)
2. Create `models.py` with Pydantic models (GREEN)
3. Run tests, verify pass
4. Refactor model organization if needed

### Cycle 2: Lifespan Management
1. Write lifespan initialization/cleanup tests (RED)
2. Implement `app_lifespan()` and `AppContext` (GREEN)
3. Run tests, verify lifecycle works

### Cycle 3: Context Injection
1. Write context access tests (RED)
2. Update pilot tools to use Context (GREEN)
3. Run tests, verify context flows correctly

### Cycle 4: Update High-Use Tools
1. Write typed return tests (RED)
2. Update tools to return typed models (GREEN)
3. Run full test suite, verify no regression

### Cycle 5: Cleanup
1. Remove `_convert_to_dict()` (GREEN)
2. Remove legacy globals (REFACTOR)
3. Final test run: all 160+ tests pass

---

## Files Summary

### New Files

| File | Purpose |
|------|---------|
| `src/mcp_privilege_cloud/models.py` | Pydantic response models |
| `tests/test_response_models.py` | Model validation tests |
| `tests/test_lifespan.py` | Lifespan management tests |
| `tests/test_context_injection.py` | Context DI tests |
| `tests/test_typed_tools.py` | Typed return tests |

### Modified Files

| File | Changes |
|------|---------|
| `src/mcp_privilege_cloud/mcp_server.py` | Lifespan, Context, typed returns |
| `tests/conftest.py` | New fixtures for lifespan/context |

---

## Verification Plan

### After Each TDD Cycle

```bash
# Run all tests
uv run pytest

# Check coverage didn't drop
uv run pytest --cov=src/mcp_privilege_cloud --cov-report=term-missing

# Verify MCP server still starts
uv run mcp-privilege-cloud &
# (verify no startup errors, then kill)
```

### Final Verification

```bash
# Full test suite
uv run pytest -v

# Coverage report
uv run pytest --cov=src/mcp_privilege_cloud --cov-report=html

# MCP Inspector test
npx @modelcontextprotocol/inspector uv run mcp-privilege-cloud
# Verify tools show output schemas
```

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Breaking existing tests | Run full suite after each change |
| SDK response format changes | Models use `populate_by_name` for alias flexibility |
| Context not available in tests | Create mock context fixtures in conftest.py |
| Lifespan errors on startup | Keep fallback to lazy init during transition |

---

## Rollback Plan

If issues arise:
1. Models are additive - can coexist with `Any` returns
2. Lifespan is optional - can remove from FastMCP constructor
3. Context is optional - can fall back to global pattern
4. Git feature branch allows easy revert
