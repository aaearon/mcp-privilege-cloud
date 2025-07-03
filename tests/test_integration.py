"""
Integration tests for CyberArk MCP platform resource workflows.

This module provides end-to-end integration tests for platform resource workflows,
focusing on the interaction between collection and entity resources, performance
characteristics, and error handling scenarios.
"""

import json
import pytest
import time
from unittest.mock import AsyncMock, MagicMock

from mcp_privilege_cloud.resources import (
    ResourceURI, ResourceRegistry,
    PlatformCollectionResource, PlatformEntityResource
)


class TestPlatformWorkflows:
    """Test end-to-end platform resource workflows."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_server = MagicMock()
        self.mock_server.list_platforms = AsyncMock()
        self.mock_server.get_complete_platform_info = AsyncMock()
        
    @pytest.mark.asyncio
    async def test_platform_workflow_collection_to_entity(self):
        """Test workflow from collection browsing to entity details."""
        # Setup mock data for collection (basic platform info)
        collection_platforms = [
            {
                "id": "WinServerLocal",
                "name": "Windows Server Local",
                "systemType": "Windows",
                "active": True,
                "description": "Windows Server for local accounts",
                "platformBaseID": "WinServerLocal",
                "platformType": "Regular",
                "allowManualChange": True,
                "performPeriodicChange": False,
                "allowManualVerification": True,
                "requirePrivilegedSessionMonitoringAndIsolation": True,
                "recordAndSaveSessionActivity": True,
                "PSMServerID": "PSMServer_1"
            },
            {
                "id": "LinuxSSH",
                "name": "Unix via SSH",
                "systemType": "Unix",
                "active": True,
                "description": "Unix accounts via SSH",
                "platformBaseID": "UnixSSH",
                "platformType": "Regular",
                "allowManualChange": True,
                "performPeriodicChange": True,
                "allowManualVerification": True,
                "requirePrivilegedSessionMonitoringAndIsolation": False,
                "recordAndSaveSessionActivity": False,
                "PSMServerID": ""
            }
        ]
        
        # Setup mock data for entity (complete platform info with Policy INI details)
        entity_platform = {
            "id": "WinServerLocal",
            "name": "Windows Server Local", 
            "systemType": "Windows",
            "active": True,
            "platformType": "Regular",
            "description": "Windows Server Local Accounts",
            # Detailed Policy INI configuration fields (raw from API)
            "PasswordLength": "12",
            "ResetOveridesMinValidity": "Yes",
            "XMLFile": "Yes",
            "FromHour": "-1",
            "PSMServerID": "PSMServer_abc123",
            "PolicyType": "Regular",
            "platformBaseID": "WinDomain",
            "MinValidityPeriod": "60",
            "ChangeNotificationPeriod": "7",
            "DaysNotifyPriorExpiration": "7",
            "VFExcludeCommand": "1",
            "VFPromptChange": "0",
            "ConnectionComponents": [
                {
                    "PSMServerID": "PSM01",
                    "Name": "PSM-RDP",
                    "ConnectionMethod": "RDP",
                    "Enabled": True
                }
            ]
        }
        
        # Configure mocks
        self.mock_server.list_platforms.return_value = collection_platforms
        self.mock_server.get_complete_platform_info.return_value = entity_platform
        
        # Step 1: Browse platform collection (fast, basic info)
        collection_uri = ResourceURI("cyberark://platforms/")
        collection_resource = PlatformCollectionResource(collection_uri, self.mock_server)
        
        # Measure collection performance
        start_time = time.time()
        collection_content = await collection_resource.get_content()
        collection_time = time.time() - start_time
        
        collection_data = json.loads(collection_content)
        
        # Verify collection response structure
        assert collection_data["type"] == "collection"
        assert collection_data["category"] == "platforms"
        assert collection_data["count"] == 2
        assert collection_data["metadata"]["performance_optimized"] is True
        assert collection_data["metadata"]["supports_complete_info"] is False
        assert len(collection_data["items"]) == 2
        
        # Verify basic platform data in collection
        win_platform = collection_data["items"][0]
        assert win_platform["id"] == "WinServerLocal"
        assert win_platform["name"] == "Windows Server Local"
        assert win_platform["systemType"] == "Windows"
        assert win_platform["active"] is True
        assert "uri" in win_platform  # Should contain URI for entity access
        
        # Verify collection is missing detailed fields
        assert "PasswordLength" not in win_platform
        assert "ResetOveridesMinValidity" not in win_platform
        assert "ConnectionComponents" not in win_platform
        
        # Step 2: Access specific platform entity (detailed info)
        entity_uri = ResourceURI("cyberark://platforms/WinServerLocal/")
        entity_resource = PlatformEntityResource(entity_uri, self.mock_server)
        
        # Measure entity performance
        start_time = time.time()
        entity_content = await entity_resource.get_content()
        entity_time = time.time() - start_time
        
        entity_data = json.loads(entity_content)
        
        # Verify entity response structure
        assert entity_data["type"] == "entity"
        assert entity_data["category"] == "platforms"
        assert entity_data["identifier"] == "WinServerLocal"
        
        # Verify basic fields are preserved
        platform_data = entity_data["data"]
        assert platform_data["id"] == "WinServerLocal"
        assert platform_data["name"] == "Windows Server Local"
        assert platform_data["systemType"] == "Windows"
        assert platform_data["active"] is True
        
        # Verify detailed Policy INI fields are present (raw from API)
        assert platform_data["PasswordLength"] == "12"
        assert platform_data["ResetOveridesMinValidity"] == "Yes"
        assert platform_data["XMLFile"] == "Yes"
        assert platform_data["FromHour"] == "-1"
        assert platform_data["PSMServerID"] == "PSMServer_abc123"
        assert platform_data["PolicyType"] == "Regular"
        assert platform_data["platformBaseID"] == "WinDomain"
        
        # Verify connection components
        assert len(platform_data["ConnectionComponents"]) == 1
        assert platform_data["ConnectionComponents"][0]["PSMServerID"] == "PSM01"
        assert platform_data["ConnectionComponents"][0]["Name"] == "PSM-RDP"
        
        # Verify performance characteristics
        # Collection should be fast (single API call)
        assert collection_time < 1.0, f"Collection took {collection_time:.3f}s, expected <1s"
        
        # Entity can be slower but should be reasonable
        assert entity_time < 2.0, f"Entity took {entity_time:.3f}s, expected <2s"
        
        # Verify correct API methods were called
        self.mock_server.list_platforms.assert_called_once()
        self.mock_server.get_complete_platform_info.assert_called_once_with("WinServerLocal")
        
    @pytest.mark.asyncio
    async def test_platform_resource_separation(self):
        """Test separation of collection (basic) vs entity (detailed) resources."""
        # Setup distinct mock responses to verify separation
        basic_platforms = [
            {
                "id": "TestPlatform",
                "name": "Test Platform",
                "systemType": "Test",
                "active": True,
                "platformType": "Regular"
            }
        ]
        
        detailed_platform = {
            "id": "TestPlatform",
            "name": "Test Platform",
            "systemType": "Test", 
            "active": True,
            "platformType": "Regular",
            # Additional detailed fields that should NOT appear in collection
            "PasswordLength": "8",
            "ComplexityMinUpperCase": "1",
            "ComplexityMinLowerCase": "1", 
            "ComplexityMinDigit": "1",
            "ComplexityMinSymbol": "0",
            "PasswordLevelRequestTimeframe": "5",
            "MinValidityPeriod": "1",
            "ResetOveridesMinValidity": "No",
            "Timeout": "30",
            "UnlockIfFail": "No",
            "MaxConcurrentConnections": "3"
        }
        
        self.mock_server.list_platforms.return_value = basic_platforms
        self.mock_server.get_complete_platform_info.return_value = detailed_platform
        
        # Test collection resource (basic info)
        collection_uri = ResourceURI("cyberark://platforms/")
        collection_resource = PlatformCollectionResource(collection_uri, self.mock_server)
        collection_content = await collection_resource.get_content()
        collection_data = json.loads(collection_content)
        
        # Test entity resource (detailed info)
        entity_uri = ResourceURI("cyberark://platforms/TestPlatform/")
        entity_resource = PlatformEntityResource(entity_uri, self.mock_server)
        entity_content = await entity_resource.get_content()
        entity_data = json.loads(entity_content)
        
        # Verify separation: collection has basic info only
        collection_platform = collection_data["items"][0]
        basic_fields = {"id", "name", "systemType", "active", "platformType", "uri"}
        detailed_fields = {"PasswordLength", "ComplexityMinUpperCase", "MinValidityPeriod", 
                          "ResetOveridesMinValidity", "Timeout", "UnlockIfFail", "MaxConcurrentConnections"}
        
        # Collection should have basic fields
        for field in basic_fields:
            if field != "uri":  # URI is added by resource
                assert field in collection_platform, f"Basic field {field} missing from collection"
        
        # Collection should NOT have detailed fields
        for field in detailed_fields:
            assert field not in collection_platform, f"Detailed field {field} should not be in collection"
        
        # Entity should have both basic AND detailed fields
        entity_platform = entity_data["data"]
        for field in basic_fields:
            if field != "uri":  # URI is added by resource
                assert field in entity_platform, f"Basic field {field} missing from entity"
        
        for field in detailed_fields:
            assert field in entity_platform, f"Detailed field {field} missing from entity"
        
        # Verify metadata indicates capabilities correctly
        assert collection_data["metadata"]["supports_complete_info"] is False
        assert collection_data["metadata"]["performance_optimized"] is True
        assert collection_data["metadata"]["data_source"] == "cyberark_platforms_api_basic"
        
        # Verify different API methods were used
        self.mock_server.list_platforms.assert_called_once()
        self.mock_server.get_complete_platform_info.assert_called_once_with("TestPlatform")
        
    @pytest.mark.asyncio
    async def test_platform_error_handling_both_types(self):
        """Test error handling for both collection and entity resources."""
        
        # Test 1: Collection resource error handling
        collection_uri = ResourceURI("cyberark://platforms/")
        collection_resource = PlatformCollectionResource(collection_uri, self.mock_server)
        
        # Test authentication error in collection
        self.mock_server.list_platforms.side_effect = Exception("401 Unauthorized")
        collection_content = await collection_resource.get_content()
        collection_data = json.loads(collection_content)
        
        assert "error" in collection_data
        assert collection_data["error"] == "server_error"
        assert "401 Unauthorized" in collection_data["message"]
        
        # Test 2: Entity resource error handling - platform not found
        entity_uri = ResourceURI("cyberark://platforms/NonExistentPlatform/")
        entity_resource = PlatformEntityResource(entity_uri, self.mock_server)
        
        # Reset mock and setup 404 error
        self.mock_server.reset_mock()
        self.mock_server.get_complete_platform_info.side_effect = Exception("Platform NonExistentPlatform not found")
        
        entity_content = await entity_resource.get_content()
        entity_data = json.loads(entity_content)
        
        assert "error" in entity_data
        assert entity_data["error"] == "server_error"
        assert "Platform NonExistentPlatform not found" in entity_data["message"]
        
        # Test 3: Entity resource graceful degradation (403 permissions error)
        # This should fallback to basic platform info when detailed access fails
        basic_platform = {
            "id": "RestrictedPlatform",
            "name": "Restricted Platform",
            "systemType": "Windows",
            "active": True,
            "platformType": "Regular"
        }
        
        # Reset mock and setup different behavior for graceful degradation
        self.mock_server.reset_mock()
        self.mock_server.get_complete_platform_info.side_effect = None
        self.mock_server.get_complete_platform_info.return_value = basic_platform  # Fallback to basic info
        
        restricted_uri = ResourceURI("cyberark://platforms/RestrictedPlatform/")
        restricted_resource = PlatformEntityResource(restricted_uri, self.mock_server)
        
        restricted_content = await restricted_resource.get_content()
        restricted_data = json.loads(restricted_content)
        
        # Should still work but with basic info only
        assert restricted_data["type"] == "entity"
        assert restricted_data["identifier"] == "RestrictedPlatform"
        assert restricted_data["data"]["id"] == "RestrictedPlatform"
        assert restricted_data["data"]["name"] == "Restricted Platform"
        
        # Should not have detailed Policy INI fields in degraded mode
        assert "PasswordLength" not in restricted_data["data"]
        assert "ResetOveridesMinValidity" not in restricted_data["data"]
        
        # Test 4: Network error handling for both resources
        network_error = Exception("Connection timeout")
        
        # Collection network error
        self.mock_server.reset_mock()
        self.mock_server.list_platforms.side_effect = network_error
        
        collection_content = await collection_resource.get_content()
        collection_data = json.loads(collection_content)
        assert "error" in collection_data
        assert "Connection timeout" in collection_data["message"]
        
        # Entity network error
        self.mock_server.get_complete_platform_info.side_effect = network_error
        
        entity_content = await entity_resource.get_content()
        entity_data = json.loads(entity_content)
        assert "error" in entity_data
        assert "Connection timeout" in entity_data["message"]
        
        # Verify both resources handle errors gracefully without crashes
        assert collection_data["error"] == "server_error"
        assert entity_data["error"] == "server_error"