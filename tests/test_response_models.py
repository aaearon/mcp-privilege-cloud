"""
Response Models Tests (RED Phase)

Tests for Pydantic response models used in MCP tool return types.
These tests verify model validation and JSON schema generation for MCP compatibility.
"""

import pytest
from typing import Optional, List, Dict, Any


class TestAccountModels:
    """Test account-related response models"""

    def test_account_details_model_validates_required_fields(self):
        """Model should validate required SDK response fields"""
        from mcp_privilege_cloud.models import AccountDetails

        data = {
            "id": "123_456",
            "platformId": "WinServerLocal",
            "safeName": "IT-Infrastructure"
        }
        account = AccountDetails(**data)
        assert account.id == "123_456"
        assert account.platform_id == "WinServerLocal"
        assert account.safe_name == "IT-Infrastructure"

    def test_account_details_model_validates_optional_fields(self):
        """Model should handle optional fields correctly"""
        from mcp_privilege_cloud.models import AccountDetails

        data = {
            "id": "123_456",
            "platformId": "WinServerLocal",
            "safeName": "IT-Infrastructure",
            "name": "admin-server01",
            "userName": "admin",
            "address": "server01.corp.com",
            "secretType": "password"
        }
        account = AccountDetails(**data)
        assert account.name == "admin-server01"
        assert account.user_name == "admin"
        assert account.address == "server01.corp.com"
        assert account.secret_type == "password"

    def test_account_details_model_generates_schema(self):
        """Model should generate JSON schema for MCP structured output"""
        from mcp_privilege_cloud.models import AccountDetails

        schema = AccountDetails.model_json_schema()
        assert "properties" in schema
        assert "id" in schema["properties"]
        assert "platformId" in schema["properties"]  # Alias should appear in schema
        assert "safeName" in schema["properties"]

    def test_account_details_model_serializes_with_aliases(self):
        """Model should serialize using API field names (aliases)"""
        from mcp_privilege_cloud.models import AccountDetails

        account = AccountDetails(
            id="123_456",
            platform_id="WinServerLocal",
            safe_name="IT-Infrastructure",
            user_name="admin"
        )
        serialized = account.model_dump(by_alias=True)
        assert "platformId" in serialized
        assert "safeName" in serialized
        assert "userName" in serialized
        assert serialized["platformId"] == "WinServerLocal"

    def test_account_summary_model_validates(self):
        """AccountSummary should contain minimal account info for lists"""
        from mcp_privilege_cloud.models import AccountSummary

        data = {
            "id": "123_456",
            "name": "admin-server01",
            "platformId": "WinServerLocal",
            "safeName": "IT-Infrastructure"
        }
        summary = AccountSummary(**data)
        assert summary.id == "123_456"
        assert summary.name == "admin-server01"


class TestSafeModels:
    """Test safe-related response models"""

    def test_safe_details_model_validates(self):
        """SafeDetails should validate safe properties"""
        from mcp_privilege_cloud.models import SafeDetails

        data = {
            "safeUrlId": "IT-Infrastructure",
            "safeName": "IT-Infrastructure",
            "safeNumber": 123,
            "description": "IT Infrastructure accounts",
            "location": "\\",
            "creator": {"id": "1", "name": "Administrator"}
        }
        safe = SafeDetails(**data)
        assert safe.safe_url_id == "IT-Infrastructure"
        assert safe.safe_name == "IT-Infrastructure"
        assert safe.safe_number == 123

    def test_safe_details_model_generates_schema(self):
        """SafeDetails should generate JSON schema"""
        from mcp_privilege_cloud.models import SafeDetails

        schema = SafeDetails.model_json_schema()
        assert "properties" in schema
        assert "safeName" in schema["properties"]
        assert "safeNumber" in schema["properties"]

    def test_safe_member_model_validates(self):
        """SafeMember should validate member properties and permissions"""
        from mcp_privilege_cloud.models import SafeMember

        data = {
            "memberName": "admin@domain.com",
            "memberType": "User",
            "permissions": {
                "useAccounts": True,
                "retrieveAccounts": True,
                "listAccounts": True
            }
        }
        member = SafeMember(**data)
        assert member.member_name == "admin@domain.com"
        assert member.member_type == "User"
        assert member.permissions is not None


class TestPlatformModels:
    """Test platform-related response models"""

    def test_platform_details_model_validates(self):
        """PlatformDetails should validate platform properties"""
        from mcp_privilege_cloud.models import PlatformDetails

        data = {
            "id": "WinServerLocal",
            "name": "Windows Server Local",
            "systemType": "Windows",
            "active": True,
            "platformType": "Regular"
        }
        platform = PlatformDetails(**data)
        assert platform.id == "WinServerLocal"
        assert platform.name == "Windows Server Local"
        assert platform.system_type == "Windows"
        assert platform.active is True

    def test_platform_details_model_handles_policy_details(self):
        """PlatformDetails should handle detailed Policy INI configuration"""
        from mcp_privilege_cloud.models import PlatformDetails

        data = {
            "id": "WinServerLocal",
            "name": "Windows Server Local",
            "systemType": "Windows",
            "active": True,
            "platformType": "Regular",
            # Additional policy details from details API
            "PasswordLength": "12",
            "MinUpperCase": "2",
            "MinLowerCase": "2"
        }
        platform = PlatformDetails(**data)
        assert platform.id == "WinServerLocal"
        # Policy details should be preserved in extra fields
        assert platform.model_extra.get("PasswordLength") == "12"

    def test_platform_details_generates_schema(self):
        """PlatformDetails should generate JSON schema"""
        from mcp_privilege_cloud.models import PlatformDetails

        schema = PlatformDetails.model_json_schema()
        assert "properties" in schema
        assert "id" in schema["properties"]
        assert "name" in schema["properties"]


class TestApplicationModels:
    """Test application-related response models"""

    def test_application_details_model_validates(self):
        """ApplicationDetails should validate application properties"""
        from mcp_privilege_cloud.models import ApplicationDetails

        data = {
            "AppID": "TestApp",
            "Description": "Test application",
            "Location": "\\Applications",
            "Disabled": False
        }
        app = ApplicationDetails(**data)
        assert app.app_id == "TestApp"
        assert app.description == "Test application"
        assert app.disabled is False

    def test_application_auth_method_model_validates(self):
        """ApplicationAuthMethod should validate auth method properties"""
        from mcp_privilege_cloud.models import ApplicationAuthMethod

        data = {
            "authType": "certificate",
            "authValue": "CN=TestCert"
        }
        auth = ApplicationAuthMethod(**data)
        assert auth.auth_type == "certificate"
        assert auth.auth_value == "CN=TestCert"


class TestSessionModels:
    """Test session monitoring response models"""

    def test_session_details_model_validates(self):
        """SessionDetails should validate session properties"""
        from mcp_privilege_cloud.models import SessionDetails

        data = {
            "SessionId": "550e8400-e29b-41d4-a716-446655440000",
            "Protocol": "SSH",
            "User": "admin",
            "FromIP": "192.168.1.100",
            "SessionDuration": "00:30:00"
        }
        session = SessionDetails(**data)
        assert session.session_id == "550e8400-e29b-41d4-a716-446655440000"
        assert session.protocol == "SSH"
        assert session.user == "admin"

    def test_session_activity_model_validates(self):
        """SessionActivity should validate activity log entries"""
        from mcp_privilege_cloud.models import SessionActivity

        data = {
            "Timestamp": "2025-01-15T10:30:00Z",
            "Command": "ls -la",
            "Result": "success"
        }
        activity = SessionActivity(**data)
        assert activity.timestamp == "2025-01-15T10:30:00Z"
        assert activity.command == "ls -la"


class TestModelConfig:
    """Test model configuration and behavior"""

    def test_models_allow_population_by_field_name(self):
        """Models should allow population using Python field names"""
        from mcp_privilege_cloud.models import AccountDetails

        # Using Python field names (snake_case)
        account = AccountDetails(
            id="123",
            platform_id="WinServerLocal",
            safe_name="TestSafe"
        )
        assert account.platform_id == "WinServerLocal"
        assert account.safe_name == "TestSafe"

    def test_models_allow_population_by_alias(self):
        """Models should allow population using API aliases (CamelCase)"""
        from mcp_privilege_cloud.models import AccountDetails

        # Using API aliases (CamelCase)
        account = AccountDetails(
            id="123",
            platformId="WinServerLocal",
            safeName="TestSafe"
        )
        assert account.platform_id == "WinServerLocal"
        assert account.safe_name == "TestSafe"

    def test_models_use_extra_allow_for_unknown_fields(self):
        """Models should allow extra fields for API forward compatibility"""
        from mcp_privilege_cloud.models import AccountDetails

        # API may return new fields not yet in model
        data = {
            "id": "123",
            "platformId": "WinServerLocal",
            "safeName": "TestSafe",
            "newApiField": "someValue",  # Unknown field
            "anotherNewField": 42
        }
        account = AccountDetails(**data)
        assert account.id == "123"
        # Extra fields should be accessible via model_extra
        assert account.model_extra.get("newApiField") == "someValue"


class TestListModels:
    """Test list/collection response models"""

    def test_accounts_list_model_validates(self):
        """AccountsList should wrap list of account summaries"""
        from mcp_privilege_cloud.models import AccountsList, AccountSummary

        data = {
            "value": [
                {"id": "1", "name": "acc1", "platformId": "Win", "safeName": "Safe1"},
                {"id": "2", "name": "acc2", "platformId": "Unix", "safeName": "Safe2"}
            ],
            "count": 2
        }
        accounts_list = AccountsList(**data)
        assert accounts_list.count == 2
        assert len(accounts_list.value) == 2
        assert accounts_list.value[0].id == "1"
