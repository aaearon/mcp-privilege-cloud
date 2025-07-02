"""
Platform resources for CyberArk MCP server.

This module provides resources for accessing CyberArk platforms and their
configurations through URI-based addressing.
"""

from typing import Any, Dict, List

from .base import CollectionResource, EntityResource


class PlatformCollectionResource(CollectionResource):
    """Resource for listing all available platforms.
    
    Provides a collection of all platforms that can be used for account creation
    and management.
    
    URI: cyberark://platforms
    """
    
    async def get_items(self) -> List[Dict[str, Any]]:
        """Get list of all available platforms."""
        # Use existing list_platforms method from the server
        platforms = await self.server.list_platforms()
        
        # Ensure platforms is a list of dictionaries
        if not isinstance(platforms, list):
            raise ValueError(f"Expected list of platforms, got {type(platforms)}")
        
        # Format platforms for resource consumption
        platform_items = []
        for platform in platforms:
            if not isinstance(platform, dict):
                raise ValueError(f"Expected platform to be a dictionary, got {type(platform)}")
                
            # Extract data from the nested structure
            general = platform.get("general", {})
            if not general:
                # Skip platforms without general info
                continue
                
            platform_item = {
                "id": general.get("id"),
                "name": general.get("name"),
                "uri": f"cyberark://platforms/{general.get('id')}",
                "description": general.get("description", ""),
                "system_type": general.get("systemType"),
                "active": general.get("active", True),
                "platform_base_id": general.get("platformBaseID"),
                "platform_type": general.get("platformType"),
            }
            
            # Add credential management info if available
            creds_mgmt = platform.get("credentialsManagement", {})
            if creds_mgmt:
                platform_item.update({
                    "credential_management": True,
                    "allow_manual_change": creds_mgmt.get("allowManualChange", False),
                    "perform_periodic_change": creds_mgmt.get("performPeriodicChange", False),
                    "allow_manual_verification": creds_mgmt.get("allowManualVerification", False),
                })
            
            # Add session management info if available
            session_mgmt = platform.get("sessionManagement", {})
            if session_mgmt:
                platform_item.update({
                    "privileged_session_management": session_mgmt.get("requirePrivilegedSessionMonitoringAndIsolation", False),
                    "record_sessions": session_mgmt.get("recordAndSaveSessionActivity", False),
                    "psm_server_id": session_mgmt.get("PSMServerID"),
                })
            
            # Remove None values and empty strings
            platform_item = {k: v for k, v in platform_item.items() if v is not None and v != ""}
            platform_items.append(platform_item)
        
        return platform_items
    
    async def get_metadata(self) -> Dict[str, Any]:
        """Get platform collection metadata."""
        base_metadata = await super().get_metadata()
        base_metadata.update({
            "supports_filtering": True,
            "supports_search": True,
            "filterable_fields": ["system_type", "active", "platform_type"],
            "sortable_fields": ["name", "id", "system_type"],
            "data_source": "cyberark_platforms_api",
        })
        return base_metadata


class PlatformEntityResource(EntityResource):
    """Resource for individual platform details.
    
    Provides detailed configuration information about a specific platform.
    
    URI: cyberark://platforms/{platform_id}
    """
    
    async def get_entity_data(self) -> Dict[str, Any]:
        """Get detailed data for a specific platform."""
        platform_id = self.uri.identifier
        if not platform_id:
            raise ValueError("Platform ID is required for platform entity resource")
        
        # Use existing get_platform_details method from the server
        platform_details = await self.server.get_platform_details(platform_id)
        
        # Format the platform details
        platform_data = {
            "id": platform_details.get("Details", {}).get("PolicyID"),
            "name": platform_details.get("Details", {}).get("PolicyName"),
            "description": platform_details.get("Details", {}).get("Description", ""),
            "system_type": platform_details.get("Details", {}).get("SystemType"),
            "active": platform_details.get("Details", {}).get("Active", True),
            "platform_base_id": platform_details.get("Details", {}).get("PlatformBaseID"),
            "platform_type": platform_details.get("Details", {}).get("PlatformType"),
            "search_for_usages": platform_details.get("Details", {}).get("SearchForUsages", False),
        }
        
        # Add connection components if available
        connection_components = platform_details.get("Details", {}).get("ConnectionComponents", [])
        if connection_components:
            platform_data["connection_components"] = []
            for component in connection_components:
                comp_data = {
                    "psmserver_id": component.get("PSMServerID"),
                    "name": component.get("Name"),
                    "display_name": component.get("DisplayName"),
                    "connection_method": component.get("ConnectionMethod"),
                    "enabled": component.get("Enabled", False),
                }
                # Remove None values
                comp_data = {k: v for k, v in comp_data.items() if v is not None}
                platform_data["connection_components"].append(comp_data)
        
        # Add properties if available
        properties = platform_details.get("Details", {}).get("Properties", [])
        if properties:
            platform_data["properties"] = []
            for prop in properties:
                prop_data = {
                    "name": prop.get("Name"),
                    "display_name": prop.get("DisplayName"),
                    "type": prop.get("Type"),
                    "required": prop.get("Required", False),
                    "default_value": prop.get("DefaultValue"),
                    "length": prop.get("Length"),
                }
                # Remove None values
                prop_data = {k: v for k, v in prop_data.items() if v is not None}
                platform_data["properties"].append(prop_data)
        
        # Add capabilities information
        platform_data["capabilities"] = {
            "privileged_session_management": platform_details.get("Details", {}).get("PrivilegedSessionManagement", False),
            "credential_management": platform_details.get("Details", {}).get("CredentialsManagement", False),
            "supports_password_change": any(
                comp.get("ConnectionMethod") == "RPC" 
                for comp in connection_components
            ),
        }
        
        # Add related resources
        platform_data["related_resources"] = {
            "accounts_using_platform": f"cyberark://accounts?platform_id={platform_id}",
        }
        
        # Remove None values and empty lists/dicts
        platform_data = {
            k: v for k, v in platform_data.items() 
            if v is not None and v != [] and v != {}
        }
        
        return platform_data
    
    async def get_metadata(self) -> Dict[str, Any]:
        """Get platform entity metadata."""
        base_metadata = await super().get_metadata()
        base_metadata.update({
            "supports_updates": False,  # Not implemented
            "supports_deletion": False,  # Not implemented
            "supports_package_import": True,  # import_platform_package exists
            "related_resources": ["accounts"],
            "permissions_required": ["list_platforms", "get_platform_details"],
            "configuration_sections": [
                "connection_components",
                "properties", 
                "capabilities"
            ],
        })
        return base_metadata


class PlatformPackagesResource(CollectionResource):
    """Resource for platform packages (future implementation).
    
    Provides access to platform packages that can be imported.
    
    URI: cyberark://platforms/packages
    """
    
    async def get_items(self) -> List[Dict[str, Any]]:
        """Get list of available platform packages."""
        # This is a placeholder for future implementation
        # Platform packages would typically be files that can be imported
        # For now, return information about the import capability
        
        package_items = [
            {
                "type": "import_capability",
                "description": "Platform packages can be imported using the import_platform_package tool",
                "supported_formats": [".zip", ".platformpackage"],
                "import_endpoint": "import_platform_package",
                "usage": "Use the import_platform_package tool to import platform packages",
            }
        ]
        
        return package_items
    
    async def get_metadata(self) -> Dict[str, Any]:
        """Get platform packages metadata."""
        base_metadata = await super().get_metadata()
        base_metadata.update({
            "feature_status": "partial_implementation",
            "import_supported": True,
            "listing_supported": False,
            "available_operations": ["import_platform_package"],
        })
        return base_metadata