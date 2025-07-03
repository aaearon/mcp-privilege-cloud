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
        """Get list of all available platforms with basic information.
        
        This optimized implementation uses the fast list_platforms() method
        to provide basic platform information including:
        - Basic platform info (id, name, systemType, etc.)
        - Raw API field names and values preserved exactly as returned
        
        IMPORTANT: No transformations are applied - all CyberArk API responses
        are preserved exactly including field names, values, and empty/null fields.
        
        Optimized for performance: single API call instead of 125+ concurrent calls.
        """
        platforms = await self.server.list_platforms()
        return await self._format_basic_platforms(platforms)
    
    async def _format_basic_platforms(self, platforms: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format basic platform data using platforms list."""
        if not isinstance(platforms, list):
            raise ValueError(f"Expected list of platforms, got {type(platforms)}")
        
        platform_items = []
        for platform in platforms:
            if not isinstance(platform, dict):
                raise ValueError(f"Expected platform to be a dictionary, got {type(platform)}")
            
            # Start with the complete platform data, preserving original structure
            platform_item = dict(platform)
            
            # Only add the URI field which is resource-specific
            if "id" in platform:
                platform_item["uri"] = f"cyberark://platforms/{platform.get('id')}"
            
            # Do not remove None values or empty strings - preserve raw API data exactly
            platform_items.append(platform_item)
        
        return platform_items
    

    
    
    async def get_metadata(self) -> Dict[str, Any]:
        """Get basic platform collection metadata."""
        base_metadata = await super().get_metadata()
        
        # Update metadata for basic platform collection
        base_metadata.update({
            "supports_filtering": True,
            "supports_search": True,
            "filterable_fields": ["systemType", "active", "platformType"],
            "sortable_fields": ["name", "id", "systemType"],
            "data_source": "cyberark_platforms_api_basic",
            "supports_complete_info": False,
            "field_conversion": "none - preserves raw API data exactly",
            "performance_optimized": True,
            "note": "Optimized for performance using single API call"
        })
        
        return base_metadata


class PlatformEntityResource(EntityResource):
    """Resource for individual platform details.
    
    Provides detailed configuration information about a specific platform.
    
    URI: cyberark://platforms/{platform_id}
    """
    
    async def get_entity_data(self) -> Dict[str, Any]:
        """Get complete detailed data for a specific platform.
        
        Provides comprehensive platform information by combining:
        - Basic platform metadata from list API
        - Detailed Policy INI configuration (66+ fields) from details API
        - Raw API data preservation with no field transformations
        
        Returns:
            Dict[str, Any]: Complete platform configuration with all available details
        """
        platform_id = self.uri.identifier
        if not platform_id:
            raise ValueError("Platform ID is required for platform entity resource")
        
        # Use get_complete_platform_info to get comprehensive platform data
        # This combines basic info from list API with detailed Policy INI from details API
        platform_data = await self.server.get_complete_platform_info(platform_id)
        
        # Add URI to the platform data
        platform_data["uri"] = f"cyberark://platforms/{platform_id}"
        
        # Preserve raw API data exactly as returned - no field transformations
        return platform_data
    
    async def get_metadata(self) -> Dict[str, Any]:
        """Get platform entity metadata with detailed capabilities emphasis."""
        base_metadata = await super().get_metadata()
        base_metadata.update({
            "supports_updates": False,  # Not implemented
            "supports_deletion": False,  # Not implemented
            "supports_package_import": True,  # import_platform_package exists
            "related_resources": ["accounts"],
            "permissions_required": ["list_platforms", "get_platform_details"],
            "data_completeness": "comprehensive",  # Emphasize detailed data
            "configuration_sections": [
                "basic_platform_info",
                "credentials_management_policy", 
                "session_management_settings",
                "connection_components",
                "privileged_access_workflows",
                "policy_ini_configuration",
                "ui_behavior_settings"
            ],
            "policy_fields_count": "66+",  # Emphasize comprehensive policy data
            "data_sources": [
                "platforms_list_api",  # Basic platform info
                "platform_details_api"  # Detailed Policy INI configuration
            ],
            "graceful_degradation": True,  # Falls back to basic info if details unavailable
            "performance_target": "~200ms",  # Individual platform detail performance
            "raw_api_preservation": True,  # No field transformations applied
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