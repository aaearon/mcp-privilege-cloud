"""
Platform resources for CyberArk MCP server.

This module provides resources for accessing CyberArk platforms and their
configurations through URI-based addressing. All platform data is returned
exactly as provided by the CyberArk APIs with no field name or value transformations.
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
        """Get list of all available platforms with complete information.
        
        This enhanced implementation uses the list_platforms_with_details() method
        to provide comprehensive platform information including:
        - Basic platform info (id, name, systemType, etc.)
        - Detailed policy settings from Policy INI configuration
        - Connection components and privileged access workflows
        - Raw API field names and values preserved exactly as returned
        
        IMPORTANT: No transformations are applied - all CyberArk API responses
        are preserved exactly including field names, values, and empty/null fields.
        
        Falls back gracefully to basic platform info if enhanced features fail or timeout.
        """
        import asyncio
        
        try:
            # Try to use enhanced API
            if hasattr(self.server, 'list_platforms_with_details'):
                platforms = await self.server.list_platforms_with_details()
                return await self._format_enhanced_platforms(platforms)
            else:
                # Fallback to basic implementation if enhanced method not available
                return await self._format_basic_platforms()
                
        except Exception as e:
            # If enhanced method fails, fallback to basic implementation
            if hasattr(self.server, 'logger'):
                self.server.logger.warning(f"Enhanced platform listing failed, falling back to basic: {e}")
            return await self._format_basic_platforms()
    
    async def _format_enhanced_platforms(self, platforms: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format enhanced platform data with complete information."""
        if not isinstance(platforms, list):
            raise ValueError(f"Expected list of platforms, got {type(platforms)}")
        
        platform_items = []
        for platform in platforms:
            if not isinstance(platform, dict):
                raise ValueError(f"Expected platform to be a dictionary, got {type(platform)}")
            
            # Create enhanced platform item with complete information
            platform_item = self._create_enhanced_platform_item(platform)
            
            
            if platform_item:  # Only add if successfully processed
                platform_items.append(platform_item)
        
        return platform_items
    
    async def _format_basic_platforms(self) -> List[Dict[str, Any]]:
        """Format basic platform data using existing list_platforms method."""
        platforms = await self.server.list_platforms()
        
        if not isinstance(platforms, list):
            raise ValueError(f"Expected list of platforms, got {type(platforms)}")
        
        platform_items = []
        for platform in platforms:
            if not isinstance(platform, dict):
                raise ValueError(f"Expected platform to be a dictionary, got {type(platform)}")
            
            # Start with the complete platform data, preserving original structure
            platform_item = dict(platform)
            
            # Only add the URI field which is resource-specific
            general = platform.get("general", {})
            if general and general.get("id"):
                platform_item["uri"] = f"cyberark://platforms/{general.get('id')}"
            
            # Do not remove None values or empty strings - preserve raw API data exactly
            platform_items.append(platform_item)
        
        return platform_items
    
    def _create_enhanced_platform_item(self, platform: Dict[str, Any]) -> Dict[str, Any]:
        """Create enhanced platform item with complete information.
        
        Preserves original CyberArk API field names and values exactly:
        - No CamelCase to snake_case conversion
        - No value transformations (Yes/No, string numbers, etc.)
        - No removal of empty/null values
        - Only adds resource-specific 'uri' field
        """
        # Start with the complete platform data from combined API response
        platform_item = dict(platform)
        
        # Only add the URI field which is resource-specific
        if "id" in platform:
            platform_item["uri"] = f"cyberark://platforms/{platform.get('id')}"
        
        # Do not remove None values or empty strings - preserve raw API data exactly
        return platform_item
    
    
    async def get_metadata(self) -> Dict[str, Any]:
        """Get enhanced platform collection metadata."""
        base_metadata = await super().get_metadata()
        
        # Check if enhanced features are available and update metadata accordingly
        has_enhanced_features = hasattr(self.server, 'list_platforms_with_details')
        
        base_metadata.update({
            "supports_filtering": True,
            "supports_search": True,
            "filterable_fields": ["systemType", "active", "platformType"],
            "sortable_fields": ["name", "id", "systemType"],
        })
        
        if has_enhanced_features:
            # Enhanced metadata when complete info is available
            base_metadata.update({
                "data_source": "cyberark_platforms_api_enhanced",
                "supports_complete_info": True,
                "enhanced_fields": [
                    "PolicyID", "PolicyName", "general", 
                    "connectionComponents", "privilegedAccessWorkflows"
                ],
                "field_conversion": "none - preserves raw API data exactly",
                "enhanced_filterable_fields": [
                    "PolicyID", "connectionMethod", "PSMServerID"
                ],

            })
        else:
            # Basic metadata when only basic info is available
            base_metadata.update({
                "data_source": "cyberark_platforms_api_basic",
                "supports_complete_info": False,
                "field_conversion": "none - preserves raw API data exactly",
                "note": "Enhanced platform details not available - upgrade server for complete information"
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
        
        # Return the raw API response with only URI added
        platform_data = dict(platform_details)
        platform_data["uri"] = f"cyberark://platforms/{platform_id}"
        
        # Do not remove None values or empty strings - preserve raw API data exactly
        
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