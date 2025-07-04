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
        # Mock the basic platform listing method
        self.mock_server.list_platforms.return_value = [
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
            }
        ]
        
        uri = ResourceURI("cyberark://platforms/")
        resource = PlatformCollectionResource(uri, self.mock_server)
        
        content = await resource.get_content()
        data = json.loads(content)
        
        assert data["type"] == "collection"
        assert data["items"][0]["id"] == "WinServerLocal"
        
    async def test_platform_entity_resource(self):
        """Test PlatformEntityResource with complete platform information."""
        # Mock the get_complete_platform_info method instead of get_platform_details
        self.mock_server.get_complete_platform_info.return_value = {
            "id": "WinServerLocal",
            "name": "Windows Server Local",
            "systemType": "Windows",
            "active": True,
            "platformType": "Regular",
            "description": "Windows Server Local Accounts",
            # Detailed Policy INI configuration fields
            "PasswordLength": "12",
            "ResetOveridesMinValidity": "Yes",
            "XMLFile": "Yes",
            "FromHour": "-1",
            "PSMServerID": "PSMServer_abc123",
            "PolicyType": "Regular",
            "platformBaseID": "WinDomain",
            "ConnectionComponents": [
                {
                    "PSMServerID": "PSM01",
                    "Name": "PSM-RDP",
                    "ConnectionMethod": "RDP",
                    "Enabled": True
                }
            ]
        }
        
        uri = ResourceURI("cyberark://platforms/WinServerLocal/")
        resource = PlatformEntityResource(uri, self.mock_server)
        
        content = await resource.get_content()
        data = json.loads(content)
        
        assert data["type"] == "entity"
        assert data["identifier"] == "WinServerLocal"
        assert data["data"]["id"] == "WinServerLocal"
        assert data["data"]["name"] == "Windows Server Local"
        assert data["data"]["systemType"] == "Windows"
        assert data["data"]["active"] is True
        
        # Verify detailed Policy INI fields are present
        assert data["data"]["PasswordLength"] == "12"
        assert data["data"]["ResetOveridesMinValidity"] == "Yes"
        assert data["data"]["PSMServerID"] == "PSMServer_abc123"
        
        # Verify connection components
        assert len(data["data"]["ConnectionComponents"]) == 1
        assert data["data"]["ConnectionComponents"][0]["PSMServerID"] == "PSM01"
        
        # Verify URI is added
        assert data["data"]["uri"] == "cyberark://platforms/WinServerLocal"
        
        # Verify the correct method was called
        self.mock_server.get_complete_platform_info.assert_called_once_with("WinServerLocal")





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