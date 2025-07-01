"""
Resource registry for managing and routing CyberArk MCP resources.

This module provides the central registry system for discovering and accessing
CyberArk resources through URI patterns.
"""

import re
from typing import Any, Dict, List, Optional, Type, Union

from .base import BaseResource, ResourceURI


class ResourceRegistry:
    """Central registry for managing CyberArk MCP resources."""
    
    def __init__(self) -> None:
        """Initialize the resource registry."""
        self._resource_classes: Dict[str, Type[BaseResource]] = {}
        self._uri_patterns: List[tuple[re.Pattern[str], Type[BaseResource]]] = []
        self._server: Optional[Any] = None
    
    def set_server(self, server: Any) -> None:
        """Set the CyberArk server instance for resource creation."""
        self._server = server
    
    def register_resource(
        self, 
        uri_pattern: str, 
        resource_class: Type[BaseResource]
    ) -> None:
        """Register a resource class for a specific URI pattern.
        
        Args:
            uri_pattern: Regex pattern to match URIs (without cyberark:// prefix)
            resource_class: Resource class to handle matched URIs
        """
        # Convert simple patterns to regex
        pattern = uri_pattern
        if not pattern.startswith("^"):
            # Convert simple patterns like "safes" or "safes/{safe_name}" to regex
            pattern = pattern.replace("{", "(?P<").replace("}", ">[^/]+)")
            pattern = f"^{pattern}$"
        
        compiled_pattern = re.compile(pattern)
        self._uri_patterns.append((compiled_pattern, resource_class))
        self._resource_classes[uri_pattern] = resource_class
    
    def find_resource_class(self, uri: ResourceURI) -> Optional[Type[BaseResource]]:
        """Find the appropriate resource class for a given URI."""
        # Create the path part of the URI for pattern matching
        path_parts = [uri.category]
        if uri.identifier:
            path_parts.append(uri.identifier)
        if uri.subcategory:
            path_parts.append(uri.subcategory)
        
        uri_path = "/".join(path_parts)
        
        # Try to match against registered patterns
        for pattern, resource_class in self._uri_patterns:
            if pattern.match(uri_path):
                return resource_class
        
        return None
    
    async def create_resource(self, uri_str: str) -> Optional[BaseResource]:
        """Create a resource instance for the given URI string."""
        if not self._server:
            raise RuntimeError("Server instance not set. Call set_server() first.")
        
        try:
            uri = ResourceURI(uri_str)
        except ValueError:
            return None
        
        resource_class = self.find_resource_class(uri)
        if not resource_class:
            return None
        
        return resource_class(uri, self._server)
    
    async def list_available_resources(self) -> List[Dict[str, Any]]:
        """List all available resource patterns and their capabilities."""
        resources = []
        
        for pattern_str, resource_class in self._resource_classes.items():
            # Create example URIs for documentation
            example_uris = self._generate_example_uris(pattern_str)
            
            resource_info = {
                "pattern": pattern_str,
                "class": resource_class.__name__,
                "description": resource_class.__doc__ or "No description available",
                "example_uris": example_uris,
            }
            resources.append(resource_info)
        
        return resources
    
    def _generate_example_uris(self, pattern: str) -> List[str]:
        """Generate example URIs for a given pattern."""
        examples = []
        base_uri = f"cyberark://{pattern}"
        
        # Simple replacement for common patterns
        replacements = {
            "{safe_name}": "ProductionSafe",
            "{account_id}": "12345",
            "{platform_id}": "WinServerLocal",
            "{identifier}": "example",
        }
        
        example_uri = base_uri
        for placeholder, value in replacements.items():
            example_uri = example_uri.replace(placeholder, value)
        
        examples.append(example_uri)
        
        # Add collection version if this is an entity pattern
        if any(placeholder in pattern for placeholder in replacements.keys()):
            collection_pattern = pattern
            for placeholder in replacements.keys():
                collection_pattern = collection_pattern.replace(f"/{placeholder}", "")
            examples.append(f"cyberark://{collection_pattern}")
        
        return examples
    
    def get_registered_patterns(self) -> List[str]:
        """Get all registered URI patterns."""
        return list(self._resource_classes.keys())
    
    def clear_registry(self) -> None:
        """Clear all registered resources (useful for testing)."""
        self._resource_classes.clear()
        self._uri_patterns.clear()