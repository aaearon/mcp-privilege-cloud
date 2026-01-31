"""
Typed Tool Returns Tests (RED then GREEN Phase)

Tests verifying that MCP tools return typed Pydantic models for structured output.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import os


class TestAccountToolsTypedReturns:
    """Test account tools return typed models"""

    @pytest.mark.asyncio
    async def test_get_account_details_returns_account_model(self):
        """get_account_details should return AccountDetails model for type safety"""
        from mcp_privilege_cloud.mcp_server import get_account_details, AppContext
        from mcp_privilege_cloud.models import AccountDetails

        # Mock server returning dict (simulating SDK response)
        mock_server = AsyncMock()
        mock_server.get_account_details.return_value = {
            "id": "123_456",
            "platformId": "WinServerLocal",
            "safeName": "IT-Infrastructure",
            "userName": "admin",
            "address": "server01.corp.com"
        }

        mock_ctx = Mock()
        mock_ctx.request_context.lifespan_context = AppContext(server=mock_server)

        result = await get_account_details("123_456", ctx=mock_ctx)

        # Result should be dict (execute_tool converts to dict for MCP)
        # but the data should match AccountDetails schema
        assert isinstance(result, dict)
        assert result["id"] == "123_456"
        assert "platformId" in result or "platform_id" in result

    @pytest.mark.asyncio
    async def test_list_accounts_returns_list_of_accounts(self):
        """list_accounts should return list compatible with AccountSummary"""
        from mcp_privilege_cloud.mcp_server import list_accounts, AppContext
        from mcp_privilege_cloud.models import AccountSummary

        mock_server = AsyncMock()
        mock_server.list_accounts.return_value = [
            {"id": "1", "platformId": "Win", "safeName": "Safe1", "name": "acc1"},
            {"id": "2", "platformId": "Unix", "safeName": "Safe2", "name": "acc2"}
        ]

        mock_ctx = Mock()
        mock_ctx.request_context.lifespan_context = AppContext(server=mock_server)

        result = await list_accounts(ctx=mock_ctx)

        assert isinstance(result, list)
        assert len(result) == 2
        # Each item should be dict with expected fields
        for item in result:
            assert "id" in item
            assert "platformId" in item or "platform_id" in item


class TestSafeToolsTypedReturns:
    """Test safe tools return typed models"""

    @pytest.mark.asyncio
    async def test_get_safe_details_returns_safe_model(self):
        """get_safe_details should return SafeDetails compatible data"""
        from mcp_privilege_cloud.mcp_server import get_safe_details, AppContext
        from mcp_privilege_cloud.models import SafeDetails

        mock_server = AsyncMock()
        mock_server.get_safe_details.return_value = {
            "safeUrlId": "TestSafe",
            "safeName": "TestSafe",
            "safeNumber": 123,
            "description": "Test safe"
        }

        mock_ctx = Mock()
        mock_ctx.request_context.lifespan_context = AppContext(server=mock_server)

        result = await get_safe_details("TestSafe", ctx=mock_ctx)

        assert isinstance(result, dict)
        assert result["safeName"] == "TestSafe"
        # Verify SafeDetails model can parse the result
        safe = SafeDetails(**result)
        assert safe.safe_name == "TestSafe"


class TestPlatformToolsTypedReturns:
    """Test platform tools return typed models"""

    @pytest.mark.asyncio
    async def test_list_platforms_returns_platform_list(self):
        """list_platforms should return list compatible with PlatformDetails"""
        from mcp_privilege_cloud.mcp_server import list_platforms, AppContext
        from mcp_privilege_cloud.models import PlatformDetails

        mock_server = AsyncMock()
        mock_server.list_platforms.return_value = [
            {"id": "Win", "name": "Windows", "systemType": "Windows", "active": True},
            {"id": "Unix", "name": "Unix SSH", "systemType": "Unix", "active": True}
        ]

        mock_ctx = Mock()
        mock_ctx.request_context.lifespan_context = AppContext(server=mock_server)

        result = await list_platforms(ctx=mock_ctx)

        assert isinstance(result, list)
        assert len(result) == 2
        # Verify PlatformDetails model can parse each result
        for item in result:
            platform = PlatformDetails(**item)
            assert platform.id is not None
            assert platform.name is not None


class TestModelSchemaGeneration:
    """Test that models generate proper JSON schemas for MCP"""

    def test_account_details_schema_for_mcp(self):
        """AccountDetails should generate MCP-compatible JSON schema"""
        from mcp_privilege_cloud.models import AccountDetails

        schema = AccountDetails.model_json_schema()

        # Schema should have required MCP structure
        assert "properties" in schema
        assert "type" in schema
        assert schema["type"] == "object"

        # Key fields should be present with descriptions
        assert "id" in schema["properties"]
        assert "description" in schema["properties"]["id"]

    def test_safe_details_schema_for_mcp(self):
        """SafeDetails should generate MCP-compatible JSON schema"""
        from mcp_privilege_cloud.models import SafeDetails

        schema = SafeDetails.model_json_schema()

        assert "properties" in schema
        assert "safeName" in schema["properties"]  # Aliased field

    def test_platform_details_schema_for_mcp(self):
        """PlatformDetails should generate MCP-compatible JSON schema"""
        from mcp_privilege_cloud.models import PlatformDetails

        schema = PlatformDetails.model_json_schema()

        assert "properties" in schema
        assert "id" in schema["properties"]
        assert "name" in schema["properties"]


class TestPydanticModelConversion:
    """Test Pydantic model conversion at MCP boundary"""

    @pytest.mark.asyncio
    async def test_sdk_pydantic_model_converted_to_dict(self):
        """SDK Pydantic models should be converted to dicts for MCP"""
        from mcp_privilege_cloud.mcp_server import get_account_details, AppContext, _convert_to_dict
        from pydantic import BaseModel

        # Create a mock Pydantic model similar to SDK response
        class MockSDKAccount(BaseModel):
            id: str
            platformId: str
            safeName: str

        mock_account = MockSDKAccount(id="123", platformId="Win", safeName="Safe")

        # Conversion should produce dict
        result = _convert_to_dict(mock_account)
        assert isinstance(result, dict)
        assert result["id"] == "123"

    def test_list_of_pydantic_models_converted(self):
        """List of Pydantic models should all be converted to dicts"""
        from mcp_privilege_cloud.mcp_server import _convert_to_dict
        from pydantic import BaseModel

        class MockItem(BaseModel):
            id: str
            name: str

        items = [MockItem(id="1", name="a"), MockItem(id="2", name="b")]

        result = _convert_to_dict(items)
        assert isinstance(result, list)
        assert all(isinstance(item, dict) for item in result)

    def test_nested_dict_with_pydantic_converted(self):
        """Nested structures with Pydantic models should be fully converted"""
        from mcp_privilege_cloud.mcp_server import _convert_to_dict
        from pydantic import BaseModel

        class MockNested(BaseModel):
            value: str

        nested = {"outer": MockNested(value="inner"), "plain": "text"}

        result = _convert_to_dict(nested)
        assert isinstance(result["outer"], dict)
        assert result["outer"]["value"] == "inner"
        assert result["plain"] == "text"
