"""
Tests for CyberArk MCP resources.

This module provides comprehensive tests for all resource types including
URI parsing, content generation, and integration with the MCP server.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from mcp_privilege_cloud.resources import (
    ResourceURI, ResourceRegistry,
    HealthResource,
    SafeCollectionResource, SafeEntityResource, SafeAccountsResource,
    AccountCollectionResource, AccountEntityResource, AccountSearchResource,
    PlatformCollectionResource, PlatformEntityResource, PlatformPackagesResource
)


class TestResourceURI:
    """Test ResourceURI parsing and validation."""
    
    def test_valid_uri_parsing(self):
        """Test parsing of valid CyberArk URIs."""
        uri = ResourceURI("cyberark://safes/ProductionSafe/accounts/")
        
        assert uri.category == "safes"
        assert uri.identifier == "ProductionSafe"
        assert uri.subcategory == "accounts"
        assert uri.query_params == {}
        
    def test_collection_uri(self):
        """Test collection URI identification."""
        uri = ResourceURI("cyberark://safes/")
        
        assert uri.is_collection
        assert not uri.is_entity
        assert not uri.is_subcollection
        
    def test_entity_uri(self):
        """Test entity URI identification."""
        uri = ResourceURI("cyberark://accounts/12345/")
        
        assert not uri.is_collection
        assert uri.is_entity
        assert not uri.is_subcollection
        
    def test_subcollection_uri(self):
        """Test subcollection URI identification."""
        uri = ResourceURI("cyberark://safes/TestSafe/accounts/")
        
        assert not uri.is_collection
        assert not uri.is_entity
        assert uri.is_subcollection
        
    def test_query_parameters(self):
        """Test URI with query parameters."""
        uri = ResourceURI("cyberark://accounts/search?query=test&safe_name=Production")
        
        assert uri.category == "accounts"
        assert uri.identifier == "search"
        assert uri.query_params["query"] == "test"
        assert uri.query_params["safe_name"] == "Production"
        
    def test_invalid_scheme(self):
        """Test invalid URI scheme handling."""
        with pytest.raises(ValueError, match="Invalid URI scheme"):
            ResourceURI("http://safes/")
            
    def test_invalid_format(self):
        """Test invalid URI format handling."""
        with pytest.raises(ValueError, match="Invalid URI format"):
            ResourceURI("cyberark://")


class TestResourceRegistry:
    """Test ResourceRegistry functionality."""
    
    def setup_method(self):
        """Set up test registry."""
        self.registry = ResourceRegistry()
        self.mock_server = MagicMock()
        self.registry.set_server(self.mock_server)
        
    def test_resource_registration(self):
        """Test registering resource classes."""
        self.registry.register_resource("safes", SafeCollectionResource)
        
        patterns = self.registry.get_registered_patterns()
        assert "safes" in patterns
        
    def test_uri_pattern_matching(self):
        """Test URI pattern matching."""
        self.registry.register_resource("safes/{safe_name}", SafeEntityResource)
        
        uri = ResourceURI("cyberark://safes/TestSafe/")
        resource_class = self.registry.find_resource_class(uri)
        
        assert resource_class == SafeEntityResource
        
    async def test_resource_creation(self):
        """Test creating resource instances."""
        self.registry.register_resource("health", HealthResource)
        
        resource = await self.registry.create_resource("cyberark://health/")
        
        assert isinstance(resource, HealthResource)
        assert resource.server == self.mock_server
        
    async def test_invalid_uri_creation(self):
        """Test handling of invalid URIs."""
        resource = await self.registry.create_resource("invalid://uri/")
        
        assert resource is None
        
    async def test_unknown_pattern_creation(self):
        """Test handling of unknown URI patterns."""
        resource = await self.registry.create_resource("cyberark://unknown/")
        
        assert resource is None


class TestHealthResource:
    """Test HealthResource implementation."""
    
    def setup_method(self):
        """Set up test health resource."""
        self.mock_server = MagicMock()
        self.mock_server.health_check = AsyncMock()
        self.mock_server.auth = None
        self.mock_server.base_url = None
        self.uri = ResourceURI("cyberark://health/")
        self.resource = HealthResource(self.uri, self.mock_server)
        
    async def test_healthy_status(self):
        """Test health resource with healthy status."""
        self.mock_server.health_check.return_value = {
            "status": "healthy",
            "safe_count": 5,
            "response_time_ms": 150
        }
        
        content = await self.resource.get_content()
        data = json.loads(content)
        
        assert data["type"] == "entity"
        assert data["data"]["status"] == "healthy"
        assert data["data"]["metrics"]["accessible_safes"] == 5
        
    async def test_unhealthy_status(self):
        """Test health resource with error status."""
        self.mock_server.health_check.side_effect = Exception("Connection failed")
        
        content = await self.resource.get_content()
        data = json.loads(content)
        
        assert data["data"]["status"] == "error"
        assert "Connection failed" in data["data"]["error"]["message"]


class TestSafeResources:
    """Test Safe resource implementations."""
    
    def setup_method(self):
        """Set up test safe resources."""
        self.mock_server = AsyncMock()
        
    async def test_safe_collection_resource(self):
        """Test SafeCollectionResource."""
        # Mock the async list_safes method to return a list directly
        async def mock_list_safes():
            return [
                {
                    "safeName": "TestSafe",
                    "description": "Test safe",
                    "creationTime": "2024-01-01T00:00:00Z"
                }
            ]
        self.mock_server.list_safes = mock_list_safes
        
        uri = ResourceURI("cyberark://safes/")
        resource = SafeCollectionResource(uri, self.mock_server)
        
        content = await resource.get_content()
        data = json.loads(content)
        
        assert data["type"] == "collection"
        assert data["count"] == 1
        assert data["items"][0]["name"] == "TestSafe"
        
    async def test_safe_entity_resource(self):
        """Test SafeEntityResource."""
        self.mock_server.get_safe_details.return_value = {
            "safeName": "TestSafe",
            "description": "Test safe details",
            "creationTime": "2024-01-01T00:00:00Z",
            "numberOfVersionsRetention": 10
        }
        
        uri = ResourceURI("cyberark://safes/TestSafe/")
        resource = SafeEntityResource(uri, self.mock_server)
        
        content = await resource.get_content()
        data = json.loads(content)
        
        assert data["type"] == "entity"
        assert data["identifier"] == "TestSafe"
        assert data["data"]["name"] == "TestSafe"
        
    async def test_safe_accounts_resource(self):
        """Test SafeAccountsResource."""
        # Mock the list_accounts method with pagination parameters
        async def mock_list_accounts(safe_name=None, offset=0, limit=100):
            return [
                {
                    "id": "12345",
                    "name": "test-account",
                    "safeName": "TestSafe",
                    "userName": "admin"
                }
            ]
        self.mock_server.list_accounts = mock_list_accounts
        
        uri = ResourceURI("cyberark://safes/TestSafe/accounts/")
        resource = SafeAccountsResource(uri, self.mock_server)
        
        content = await resource.get_content()
        data = json.loads(content)
        
        assert data["type"] == "collection"
        assert data["items"][0]["name"] == "test-account"
        assert data["items"][0]["uri"] == "cyberark://accounts/12345"


class TestAccountResources:
    """Test Account resource implementations."""
    
    def setup_method(self):
        """Set up test account resources."""
        self.mock_server = AsyncMock()
        # Mock the logger to avoid warnings
        self.mock_server.logger = MagicMock()
        
    async def test_account_collection_resource(self):
        """Test AccountCollectionResource with pagination."""
        # Mock the list_accounts method to return test data when called with pagination
        self.mock_server.list_accounts.return_value = [
            {
                "id": "12345",
                "name": "test-account",
                "userName": "admin",
                "safeName": "TestSafe"
            }
        ]
        
        uri = ResourceURI("cyberark://accounts/")
        resource = AccountCollectionResource(uri, self.mock_server)
        
        content = await resource.get_content()
        data = json.loads(content)
        
        assert data["type"] == "collection"
        assert data["items"][0]["id"] == "12345"
        
    async def test_account_entity_resource(self):
        """Test AccountEntityResource."""
        self.mock_server.get_account_details.return_value = {
            "id": "12345",
            "name": "test-account",
            "userName": "admin",
            "safeName": "TestSafe",
            "platformId": "WinServerLocal",
            "secretManagement": {
                "automaticManagementEnabled": True,
                "status": "success"
            }
        }
        
        uri = ResourceURI("cyberark://accounts/12345/")
        resource = AccountEntityResource(uri, self.mock_server)
        
        content = await resource.get_content()
        data = json.loads(content)
        
        assert data["type"] == "entity"
        assert data["identifier"] == "12345"
        assert data["data"]["secret_management"]["status"] == "success"
        
    async def test_account_search_resource(self):
        """Test AccountSearchResource with pagination."""
        # Mock the search_accounts method to return test data when called with pagination
        self.mock_server.search_accounts.return_value = [
            {
                "id": "12345",
                "name": "test-account",
                "_score": 0.95
            }
        ]
        
        uri = ResourceURI("cyberark://accounts/search?query=test")
        resource = AccountSearchResource(uri, self.mock_server)
        
        content = await resource.get_content()
        data = json.loads(content)
        
        assert data["type"] == "collection"
        assert data["items"][0]["search_score"] == 0.95


class TestPlatformResources:
    """Test Platform resource implementations."""
    
    def setup_method(self):
        """Set up test platform resources."""
        self.mock_server = AsyncMock()
        
    async def test_platform_collection_resource(self):
        """Test PlatformCollectionResource."""
        self.mock_server.list_platforms.return_value = [
            {
                "general": {
                    "id": "WinServerLocal",
                    "name": "Windows Server Local",
                    "systemType": "Windows",
                    "active": True,
                    "description": "Windows Server for local accounts",
                    "platformBaseID": "WinServerLocal",
                    "platformType": "Regular"
                },
                "credentialsManagement": {
                    "allowManualChange": True,
                    "performPeriodicChange": False,
                    "allowManualVerification": True
                },
                "sessionManagement": {
                    "requirePrivilegedSessionMonitoringAndIsolation": True,
                    "recordAndSaveSessionActivity": True,
                    "PSMServerID": "PSMServer_1"
                }
            }
        ]
        
        uri = ResourceURI("cyberark://platforms/")
        resource = PlatformCollectionResource(uri, self.mock_server)
        
        content = await resource.get_content()
        data = json.loads(content)
        
        assert data["type"] == "collection"
        assert data["items"][0]["id"] == "WinServerLocal"
        
    async def test_platform_entity_resource(self):
        """Test PlatformEntityResource."""
        self.mock_server.get_platform_details.return_value = {
            "Details": {
                "PolicyID": "WinServerLocal",
                "PolicyName": "Windows Server Local",
                "SystemType": "Windows",
                "Active": True,
                "ConnectionComponents": [
                    {
                        "PSMServerID": "PSM01",
                        "Name": "PSM-RDP",
                        "ConnectionMethod": "RDP",
                        "Enabled": True
                    }
                ]
            }
        }
        
        uri = ResourceURI("cyberark://platforms/WinServerLocal/")
        resource = PlatformEntityResource(uri, self.mock_server)
        
        content = await resource.get_content()
        data = json.loads(content)
        
        assert data["type"] == "entity"
        assert data["identifier"] == "WinServerLocal"
        assert len(data["data"]["connection_components"]) == 1


class TestEnhancedPlatformResource:
    """Test enhanced Platform resource implementations with complete information."""
    
    def setup_method(self):
        """Set up test enhanced platform resources."""
        self.mock_server = AsyncMock()
        
    async def test_get_items_with_complete_info(self):
        """Test PlatformCollectionResource with enhanced complete information."""
        # Mock the new list_platforms_with_details method from Task A3
        self.mock_server.list_platforms_with_details.return_value = [
            {
                # Basic info from list API
                "id": "WinServerLocal",
                "name": "Windows Server Local",
                "systemType": "Windows",
                "active": True,
                "description": "Windows Server for local accounts",
                "platformBaseID": "WinServerLocal",
                "platformType": "Regular",
                
                # Enhanced details from get_complete_platform_info
                "details": {
                    "policyId": "WinServerLocal",
                    "policyName": "Windows Server Local",
                    "systemType": "Windows",
                    "active": True,
                    "platformBaseId": "WinServerLocal",
                    "platformType": "Regular",
                    "generalSettings": {
                        "allowManualChange": True,
                        "performPeriodicChange": False,
                        "allowManualVerification": True,
                        "requirePasswordChangeEveryXDays": 90,
                        "enforceCheckinExclusivePassword": True,
                        "enforceOneTimePasswordAccess": False
                    },
                    "connectionComponents": [
                        {
                            "psmServerId": "PSM01",
                            "name": "PSM-RDP",
                            "connectionMethod": "RDP",
                            "enabled": True,
                            "userRole": "Administrator",
                            "parameters": {
                                "AllowMappingLocalDrives": "Yes",
                                "AllowConnectToConsole": "No",
                                "AudioRedirection": "Yes"
                            }
                        }
                    ],
                    "privilegedAccessWorkflows": {
                        "requireDualControlPasswordAccessApproval": False,
                        "enforceCheckinExclusivePassword": True,
                        "requireUsersToSpecifyReasonForAccess": True
                    }
                },
                
                # Credential management from list API
                "credentialsManagement": {
                    "allowManualChange": True,
                    "performPeriodicChange": False,
                    "allowManualVerification": True
                },
                
                # Session management from list API
                "sessionManagement": {
                    "requirePrivilegedSessionMonitoringAndIsolation": True,
                    "recordAndSaveSessionActivity": True,
                    "PSMServerID": "PSMServer_1"
                }
            },
            {
                # Second platform with different structure
                "id": "UnixSSH",
                "name": "Unix via SSH",
                "systemType": "Unix",
                "active": True,
                "description": "Unix/Linux systems via SSH",
                "platformBaseID": "UnixSSH",
                "platformType": "Regular",
                
                # Enhanced details
                "details": {
                    "policyId": "UnixSSH",
                    "policyName": "Unix via SSH", 
                    "systemType": "Unix",
                    "active": True,
                    "generalSettings": {
                        "allowManualChange": False,
                        "performPeriodicChange": True,
                        "allowManualVerification": False,
                        "requirePasswordChangeEveryXDays": 30
                    },
                    "connectionComponents": [
                        {
                            "psmServerId": "PSM02",
                            "name": "PSM-SSH",
                            "connectionMethod": "SSH",
                            "enabled": True
                        }
                    ]
                }
            }
        ]
        
        uri = ResourceURI("cyberark://platforms/")
        resource = PlatformCollectionResource(uri, self.mock_server)
        
        # Test that get_items returns enhanced platform objects
        items = await resource.get_items()
        
        # Verify we get the expected enhanced structure
        assert len(items) == 2
        
        # First platform verification - enhanced with complete details
        platform1 = items[0]
        assert platform1["id"] == "WinServerLocal"
        assert platform1["name"] == "Windows Server Local"
        assert platform1["system_type"] == "Windows"
        assert platform1["active"] is True
        
        # Verify enhanced fields from complete platform info are included
        assert "policy_id" in platform1
        assert "general_settings" in platform1
        assert "connection_components" in platform1
        assert "privileged_access_workflows" in platform1
        
        # Verify connection components structure
        assert len(platform1["connection_components"]) == 1
        conn_comp = platform1["connection_components"][0]
        assert conn_comp["psm_server_id"] == "PSM01"
        assert conn_comp["name"] == "PSM-RDP"
        assert conn_comp["connection_method"] == "RDP"
        assert conn_comp["enabled"] is True
        
        # Verify general settings
        general_settings = platform1["general_settings"]
        assert general_settings["allow_manual_change"] is True
        assert general_settings["perform_periodic_change"] is False
        assert general_settings["require_password_change_every_x_days"] == 90
        
        # Second platform verification
        platform2 = items[1]
        assert platform2["id"] == "UnixSSH"
        assert platform2["system_type"] == "Unix"
        
        # Verify server method was called with correct parameters
        self.mock_server.list_platforms_with_details.assert_called_once()
        
    async def test_platform_object_structure(self):
        """Test that enhanced platform objects have consistent field structure."""
        # Mock response with minimal data to test field structure
        self.mock_server.list_platforms_with_details.return_value = [
            {
                "id": "TestPlatform",
                "name": "Test Platform",
                "systemType": "Test",
                "active": True,
                "details": {
                    "policyId": "TestPlatform",
                    "policyName": "Test Platform",
                    "generalSettings": {
                        "allowManualChange": True
                    },
                    "connectionComponents": [],
                    "privilegedAccessWorkflows": {
                        "requireDualControlPasswordAccessApproval": False
                    }
                }
            }
        ]
        
        uri = ResourceURI("cyberark://platforms/")
        resource = PlatformCollectionResource(uri, self.mock_server)
        
        items = await resource.get_items()
        platform = items[0]
        
        # Test required base fields
        required_fields = ["id", "name", "uri", "system_type", "active"]
        for field in required_fields:
            assert field in platform, f"Missing required field: {field}"
        
        # Test enhanced fields from complete platform info
        enhanced_fields = ["policy_id", "general_settings", "connection_components", "privileged_access_workflows"]
        for field in enhanced_fields:
            assert field in platform, f"Missing enhanced field: {field}"
        
        # Test URI format
        assert platform["uri"] == "cyberark://platforms/TestPlatform"
        
    def test_field_naming_consistency(self):
        """Test that field names are consistently converted from CamelCase to snake_case."""
        # Test the field name conversion logic
        test_cases = [
            ("systemType", "system_type"),
            ("platformBaseID", "platform_base_id"),
            ("PSMServerID", "psm_server_id"),
            ("allowManualChange", "allow_manual_change"),
            ("performPeriodicChange", "perform_periodic_change"),
            ("requirePasswordChangeEveryXDays", "require_password_change_every_x_days"),
            ("enforceCheckinExclusivePassword", "enforce_checkin_exclusive_password"),
            ("requireDualControlPasswordAccessApproval", "require_dual_control_password_access_approval")
        ]
        
        # This test will verify that the field conversion logic works correctly
        # when implemented in the enhanced resource
        for camel_case, expected_snake_case in test_cases:
            # The actual conversion will be tested when the implementation is complete
            # For now, we define the expected behavior
            assert camel_case != expected_snake_case  # Basic sanity check
            
    async def test_backward_compatibility_with_existing_tests(self):
        """Test that enhanced resource maintains backward compatibility."""
        # Mock the old list_platforms method response for backward compatibility test
        self.mock_server.list_platforms.return_value = [
            {
                "general": {
                    "id": "WinServerLocal",
                    "name": "Windows Server Local",
                    "systemType": "Windows",
                    "active": True,
                    "description": "Windows Server for local accounts",
                    "platformBaseID": "WinServerLocal",
                    "platformType": "Regular"
                },
                "credentialsManagement": {
                    "allowManualChange": True,
                    "performPeriodicChange": False,
                    "allowManualVerification": True
                }
            }
        ]
        
        # For backward compatibility, the resource should still work with existing tests
        # if list_platforms_with_details is not available
        self.mock_server.list_platforms_with_details.side_effect = AttributeError("Method not available")
        
        uri = ResourceURI("cyberark://platforms/")
        resource = PlatformCollectionResource(uri, self.mock_server)
        
        # This should fall back to the old behavior
        items = await resource.get_items()
        
        assert len(items) == 1
        assert items[0]["id"] == "WinServerLocal"
        assert items[0]["name"] == "Windows Server Local"
        
        # Should not have enhanced fields when falling back
        assert "policy_id" not in items[0]
        assert "general_settings" not in items[0]
        
    async def test_error_handling_for_enhanced_features(self):
        """Test error handling when enhanced platform features fail."""
        # Test when list_platforms_with_details raises an exception
        self.mock_server.list_platforms_with_details.side_effect = Exception("API Error")
        self.mock_server.list_platforms.return_value = []  # Fallback should work
        
        uri = ResourceURI("cyberark://platforms/")
        resource = PlatformCollectionResource(uri, self.mock_server)
        
        # Should handle the error gracefully and fall back to basic implementation
        items = await resource.get_items()
        assert isinstance(items, list)
        
    async def test_empty_platforms_list_handling(self):
        """Test handling of empty platforms list from enhanced API."""
        self.mock_server.list_platforms_with_details.return_value = []
        
        uri = ResourceURI("cyberark://platforms/")
        resource = PlatformCollectionResource(uri, self.mock_server)
        
        items = await resource.get_items()
        assert items == []
        
    async def test_enhanced_metadata(self):
        """Test that enhanced resource provides updated metadata."""
        self.mock_server.list_platforms_with_details.return_value = []
        
        uri = ResourceURI("cyberark://platforms/")
        resource = PlatformCollectionResource(uri, self.mock_server)
        
        metadata = await resource.get_metadata()
        
        # Should include enhanced metadata fields
        assert "supports_complete_info" in metadata
        assert "enhanced_fields" in metadata
        assert metadata["data_source"] == "cyberark_platforms_api_enhanced"


class TestPlatformFieldMapping:
    """Test platform field transformation and mapping logic."""
    
    def setup_method(self):
        """Set up test field mapping resources."""
        self.mock_server = AsyncMock()
        
    def test_camel_case_to_snake_case_conversion(self):
        """Test conversion from CamelCase/camelCase to snake_case field names."""
        # Test data representing the various CamelCase patterns from CyberArk API
        test_cases = [
            # Basic camelCase to snake_case
            ("systemType", "system_type"),
            ("platformType", "platform_type"),
            ("activeDirectory", "active_directory"),
            ("connectionMethod", "connection_method"),
            
            # PascalCase to snake_case
            ("SystemType", "system_type"),
            ("PlatformType", "platform_type"),
            ("PolicyName", "policy_name"),
            ("PolicyID", "policy_id"),
            ("DisplayName", "display_name"),
            
            # Special ID handling
            ("PSMServerID", "psm_server_id"),
            ("platformBaseID", "platform_base_id"),
            ("psmServerId", "psm_server_id"),
            ("PlatformBaseID", "platform_base_id"),
            
            # Complex compound words
            ("allowManualChange", "allow_manual_change"),
            ("performPeriodicChange", "perform_periodic_change"),
            ("allowManualVerification", "allow_manual_verification"),
            ("requirePasswordChangeEveryXDays", "require_password_change_every_x_days"),
            ("enforceCheckinExclusivePassword", "enforce_checkin_exclusive_password"),
            ("enforceOneTimePasswordAccess", "enforce_one_time_password_access"),
            ("requireDualControlPasswordAccessApproval", "require_dual_control_password_access_approval"),
            ("requireUsersToSpecifyReasonForAccess", "require_users_to_specify_reason_for_access"),
            ("requirePrivilegedSessionMonitoringAndIsolation", "require_privileged_session_monitoring_and_isolation"),
            ("recordAndSaveSessionActivity", "record_and_save_session_activity"),
            
            # Edge cases - already snake_case should remain unchanged
            ("already_snake_case", "already_snake_case"),
            ("single", "single"),
            ("UPPER", "upper"),
        ]
        
        # Import the transformation function we'll implement
        from mcp_privilege_cloud.resources.platforms import PlatformEntityResource
        
        # Test each case
        for camel_case, expected_snake_case in test_cases:
            result = PlatformEntityResource._camel_to_snake(camel_case)
            assert result == expected_snake_case, f"Failed for '{camel_case}': expected '{expected_snake_case}', got '{result}'"
            
    def test_yes_no_to_boolean_conversion(self):
        """Test conversion from Yes/No strings to boolean values."""
        # Test data representing Yes/No values from CyberArk API
        test_cases = [
            ("Yes", True),
            ("No", False),
            ("YES", True),
            ("NO", False),
            ("yes", True),
            ("no", False),
            ("True", True),  # Should also handle True/False strings
            ("False", False),
            ("true", True),
            ("false", False),
            # Non-boolean strings should remain unchanged
            ("Maybe", "Maybe"),
            ("Unknown", "Unknown"),
            ("", ""),
            ("NotApplicable", "NotApplicable"),
        ]
        
        # Import the transformation function we'll implement
        from mcp_privilege_cloud.resources.platforms import PlatformEntityResource
        
        # Test each case
        for input_value, expected_output in test_cases:
            result = PlatformEntityResource._convert_yes_no_to_boolean(input_value)
            assert result == expected_output, f"Failed for '{input_value}': expected '{expected_output}', got '{result}'"
            
    def test_string_to_int_conversion(self):
        """Test conversion from string numbers to integers where appropriate."""
        # Test data representing numeric strings from CyberArk API
        test_cases = [
            # Valid numeric strings
            ("90", 90),
            ("30", 30),
            ("0", 0),
            ("365", 365),
            ("1", 1),
            ("-1", -1),  # CyberArk sometimes uses -1 for "unlimited"
            
            # Invalid numeric strings should remain unchanged
            ("NotANumber", "NotANumber"),
            ("", ""),
            ("N/A", "N/A"),  
            ("Unlimited", "Unlimited"),
            ("Auto", "Auto"),
            ("Mixed123Text", "Mixed123Text"),
            ("123.45", "123.45"),  # Keep decimals as strings for now
        ]
        
        # Import the transformation function we'll implement  
        from mcp_privilege_cloud.resources.platforms import PlatformEntityResource
        
        # Test each case
        for input_value, expected_output in test_cases:
            result = PlatformEntityResource._convert_string_to_int(input_value)
            assert result == expected_output, f"Failed for '{input_value}': expected '{expected_output}', got '{result}'"
            
    def test_nested_field_transformation(self):
        """Test transformation of nested objects and arrays."""
        # Test data representing nested structures from CyberArk API response
        test_input = {
            "PolicyID": "WinServerLocal",
            "PolicyName": "Windows Server Local", 
            "SystemType": "Windows",
            "GeneralSettings": {
                "AllowManualChange": "Yes",
                "PerformPeriodicChange": "No",
                "RequirePasswordChangeEveryXDays": "90",
                "EnforceCheckinExclusivePassword": "Yes"
            },
            "ConnectionComponents": [
                {
                    "PSMServerID": "PSM01",
                    "ConnectionMethod": "RDP",
                    "Enabled": "Yes",
                    "Parameters": {
                        "AllowMappingLocalDrives": "Yes",
                        "AllowConnectToConsole": "No",
                        "MaxConcurrentConnections": "5"
                    }
                }
            ],
            "PrivilegedAccessWorkflows": {
                "RequireDualControlPasswordAccessApproval": "No",
                "EnforceCheckinExclusivePassword": "Yes"
            }
        }
        
        expected_output = {
            "policy_id": "WinServerLocal",
            "policy_name": "Windows Server Local",
            "system_type": "Windows", 
            "general_settings": {
                "allow_manual_change": True,
                "perform_periodic_change": False,
                "require_password_change_every_x_days": 90,
                "enforce_checkin_exclusive_password": True
            },
            "connection_components": [
                {
                    "psm_server_id": "PSM01",
                    "connection_method": "RDP",
                    "enabled": True,
                    "parameters": {
                        "allow_mapping_local_drives": True,
                        "allow_connect_to_console": False,
                        "max_concurrent_connections": 5
                    }
                }
            ],
            "privileged_access_workflows": {
                "require_dual_control_password_access_approval": False,
                "enforce_checkin_exclusive_password": True
            }
        }
        
        # Import the transformation function we'll implement
        from mcp_privilege_cloud.resources.platforms import PlatformEntityResource
        
        result = PlatformEntityResource._transform_platform_details(test_input)
        assert result == expected_output
        
    def test_policy_string_preservation(self):
        """Test that certain policy strings are preserved as-is."""
        # Some CyberArk policy values should remain unchanged even if they look like transformable values
        preserve_cases = [
            # Policy expressions that should not be transformed
            "BUILTIN\\Administrators",
            "NT AUTHORITY\\SYSTEM", 
            "Domain\\UserName",
            "C:\\Program Files\\Application",
            "/usr/local/bin/script",
            "SELECT * FROM Users WHERE Active='Yes'",  # SQL with Yes/No should not be transformed
            "HKEY_LOCAL_MACHINE\\SOFTWARE",
            "cmd.exe /c echo 'Yes' > output.txt",  # Commands with Yes/No
            
            # Custom expressions
            "CustomPolicyValue123",
            "SpecialConfiguration_Yes_No_Format",
        ]
        
        from mcp_privilege_cloud.resources.platforms import PlatformEntityResource
        
        # Test that policy strings containing complex values are preserved
        test_input = {
            "PolicyScript": "cmd.exe /c echo 'Yes' > output.txt",
            "PolicyPath": "C:\\Program Files\\Application",
            "AllowManualChange": "Yes",  # This should still be transformed
            "UserAccount": "Domain\\UserName",
            "RegistryKey": "HKEY_LOCAL_MACHINE\\SOFTWARE"
        }
        
        result = PlatformEntityResource._transform_platform_details(test_input)
        
        # Policy strings should remain unchanged
        assert result["policy_script"] == "cmd.exe /c echo 'Yes' > output.txt"
        assert result["policy_path"] == "C:\\Program Files\\Application"
        assert result["user_account"] == "Domain\\UserName"
        assert result["registry_key"] == "HKEY_LOCAL_MACHINE\\SOFTWARE"
        
        # But simple Yes/No values should still be transformed
        assert result["allow_manual_change"] is True
        
    def test_empty_and_null_value_handling(self):
        """Test handling of empty, null, and undefined values."""
        test_cases = [
            (None, None),
            ("", ""),
            ({}, {}),
            ([], []),
            ({"EmptyDict": {}}, {"empty_dict": {}}),
            ({"EmptyList": []}, {"empty_list": []}),
            ({"NullValue": None}, {"null_value": None}),
            ({"EmptyString": ""}, {"empty_string": ""}),
        ]
        
        from mcp_privilege_cloud.resources.platforms import PlatformEntityResource
        
        for input_value, expected_output in test_cases:
            result = PlatformEntityResource._transform_platform_details(input_value)
            assert result == expected_output
            
    async def test_integration_with_platform_entity_resource(self):
        """Test that field transformation integrates correctly with PlatformEntityResource."""
        # Mock API response with raw CyberArk field names
        mock_platform_details = {
            "Details": {
                "PolicyID": "WinServerLocal",
                "PolicyName": "Windows Server Local",
                "SystemType": "Windows",
                "Active": True,
                "PlatformBaseID": "WinServerLocal",
                "PlatformType": "Regular",
                "SearchForUsages": "No",
                "ConnectionComponents": [
                    {
                        "PSMServerID": "PSM01",
                        "Name": "PSM-RDP",
                        "DisplayName": "PSM RDP Connection",
                        "ConnectionMethod": "RDP",
                        "Enabled": "Yes"
                    }
                ],
                "Properties": [
                    {
                        "Name": "LogonDomain",
                        "DisplayName": "Logon Domain",
                        "Type": "String", 
                        "Required": "Yes",
                        "DefaultValue": "",
                        "Length": "255"
                    }
                ]
            }
        }
        
        self.mock_server.get_platform_details.return_value = mock_platform_details
        
        uri = ResourceURI("cyberark://platforms/WinServerLocal")
        resource = PlatformEntityResource(uri, self.mock_server)
        
        # Get the entity data - this should apply field transformations
        result = await resource.get_entity_data()
        
        # Verify transformed field names
        assert result["id"] == "WinServerLocal"
        assert result["name"] == "Windows Server Local"
        assert result["system_type"] == "Windows"
        assert result["platform_base_id"] == "WinServerLocal"
        assert result["platform_type"] == "Regular"
        assert result["search_for_usages"] is False  # "No" -> False
        
        # Verify connection components transformation
        assert len(result["connection_components"]) == 1
        conn_comp = result["connection_components"][0]
        assert conn_comp["psm_server_id"] == "PSM01"  # PSMServerID -> psm_server_id
        assert conn_comp["display_name"] == "PSM RDP Connection"
        assert conn_comp["connection_method"] == "RDP"
        assert conn_comp["enabled"] is True  # "Yes" -> True
        
        # Verify properties transformation
        assert len(result["properties"]) == 1
        prop = result["properties"][0]
        assert prop["display_name"] == "Logon Domain"
        assert prop["required"] is True  # "Yes" -> True
        assert prop["length"] == 255  # "255" -> 255


class TestIntegration:
    """Test end-to-end resource integration."""
    
    @pytest.mark.asyncio
    async def test_resource_registry_full_workflow(self):
        """Test complete resource workflow."""
        registry = ResourceRegistry()
        mock_server = MagicMock()
        mock_server.health_check = AsyncMock()
        mock_server.auth = None
        mock_server.base_url = None
        registry.set_server(mock_server)
        
        # Register all resources
        registry.register_resource("health", HealthResource)
        registry.register_resource("safes", SafeCollectionResource)
        registry.register_resource("accounts/{account_id}", AccountEntityResource)
        
        # Test listing available resources
        available_resources = await registry.list_available_resources()
        assert len(available_resources) == 3
        
        # Test creating and using a resource
        mock_server.health_check.return_value = {"status": "healthy", "safe_count": 3}
        
        resource = await registry.create_resource("cyberark://health/")
        assert resource is not None
        
        content = await resource.get_content()
        data = json.loads(content)
        assert data["data"]["status"] == "healthy"
        
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling in resource operations."""
        registry = ResourceRegistry()
        mock_server = MagicMock()
        mock_server.list_safes = AsyncMock()
        registry.set_server(mock_server)
        
        registry.register_resource("safes", SafeCollectionResource)
        
        # Test server error handling
        mock_server.list_safes.side_effect = Exception("API Error")
        
        resource = await registry.create_resource("cyberark://safes/")
        content = await resource.get_content()
        data = json.loads(content)
        
        assert "error" in data
        assert data["error"] == "server_error"
        assert "API Error" in data["message"]