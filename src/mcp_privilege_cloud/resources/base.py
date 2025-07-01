"""
Base resource classes for CyberArk MCP resources.

This module provides the foundational classes and utilities for implementing
MCP resources that represent CyberArk entities.
"""

import json
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from urllib.parse import parse_qs, urlparse


class ResourceURI:
    """Utility class for parsing and validating CyberArk resource URIs."""
    
    SCHEME = "cyberark"
    URI_PATTERN = re.compile(r"^cyberark://([^/]+)(?:/([^/?]+)?)?(?:/([^/?]+)?)?(?:\?(.+))?/?$")
    
    def __init__(self, uri: str) -> None:
        """Initialize ResourceURI with validation."""
        self.uri = uri
        self._parsed = self._parse_uri(uri)
    
    def _parse_uri(self, uri: str) -> Dict[str, Optional[str]]:
        """Parse and validate the resource URI."""
        if not uri.startswith(f"{self.SCHEME}://"):
            raise ValueError(f"Invalid URI scheme. Expected '{self.SCHEME}://', got: {uri}")
        
        match = self.URI_PATTERN.match(uri)
        if not match:
            raise ValueError(f"Invalid URI format: {uri}")
        
        category, identifier, subcategory, query_string = match.groups()
        
        query_params = {}
        if query_string:
            query_params = parse_qs(query_string)
            # Flatten single-value query parameters
            query_params = {k: v[0] if len(v) == 1 else v for k, v in query_params.items()}
        
        return {
            "category": category,
            "identifier": identifier,
            "subcategory": subcategory,
            "query_params": query_params,
        }
    
    @property
    def category(self) -> str:
        """Get the resource category (e.g., 'safes', 'accounts', 'platforms')."""
        return self._parsed["category"]
    
    @property
    def identifier(self) -> Optional[str]:
        """Get the resource identifier (e.g., safe name, account ID)."""
        return self._parsed["identifier"]
    
    @property
    def subcategory(self) -> Optional[str]:
        """Get the resource subcategory (e.g., 'accounts', 'members')."""
        return self._parsed["subcategory"]
    
    @property
    def query_params(self) -> Dict[str, Any]:
        """Get the query parameters as a dictionary."""
        return self._parsed["query_params"]
    
    @property
    def is_collection(self) -> bool:
        """Check if this URI represents a collection resource."""
        return self.identifier is None
    
    @property
    def is_entity(self) -> bool:
        """Check if this URI represents an individual entity resource."""
        return self.identifier is not None and self.subcategory is None
    
    @property
    def is_subcollection(self) -> bool:
        """Check if this URI represents a subcollection resource."""
        return self.identifier is not None and self.subcategory is not None
    
    def __str__(self) -> str:
        return self.uri
    
    def __repr__(self) -> str:
        return f"ResourceURI('{self.uri}')"


class BaseResource(ABC):
    """Abstract base class for all CyberArk MCP resources."""
    
    def __init__(self, uri: ResourceURI, server: Any) -> None:
        """Initialize the resource with URI and server instance."""
        self.uri = uri
        self.server = server
    
    @abstractmethod
    async def get_content(self) -> str:
        """Get the resource content as a string (typically JSON)."""
        pass
    
    @abstractmethod
    async def get_metadata(self) -> Dict[str, Any]:
        """Get resource metadata for discovery."""
        pass
    
    def _format_json(self, data: Any) -> str:
        """Format data as JSON string with proper indentation."""
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    async def _handle_server_error(self, error: Exception) -> str:
        """Handle server errors and return appropriate error response."""
        error_data = {
            "error": "server_error",
            "message": str(error),
            "uri": str(self.uri),
            "type": self.__class__.__name__
        }
        return self._format_json(error_data)


class CollectionResource(BaseResource):
    """Base class for collection-type resources (lists of entities)."""
    
    @abstractmethod
    async def get_items(self) -> List[Dict[str, Any]]:
        """Get the list of items in this collection."""
        pass
    
    async def get_content(self) -> str:
        """Get collection content as JSON."""
        try:
            items = await self.get_items()
            collection_data = {
                "uri": str(self.uri),
                "type": "collection",
                "category": self.uri.category,
                "count": len(items),
                "items": items,
                "metadata": await self.get_metadata()
            }
            return self._format_json(collection_data)
        except Exception as e:
            return await self._handle_server_error(e)
    
    async def get_metadata(self) -> Dict[str, Any]:
        """Get collection metadata."""
        return {
            "type": "collection",
            "category": self.uri.category,
            "supports_pagination": False,
            "supports_filtering": False,
        }


class EntityResource(BaseResource):
    """Base class for individual entity resources."""
    
    @abstractmethod
    async def get_entity_data(self) -> Dict[str, Any]:
        """Get the entity data dictionary."""
        pass
    
    async def get_content(self) -> str:
        """Get entity content as JSON."""
        try:
            entity_data = await self.get_entity_data()
            entity_content = {
                "uri": str(self.uri),
                "type": "entity",
                "category": self.uri.category,
                "identifier": self.uri.identifier,
                "data": entity_data,
                "metadata": await self.get_metadata()
            }
            return self._format_json(entity_content)
        except Exception as e:
            return await self._handle_server_error(e)
    
    async def get_metadata(self) -> Dict[str, Any]:
        """Get entity metadata."""
        return {
            "type": "entity",
            "category": self.uri.category,
            "identifier": self.uri.identifier,
            "supports_updates": False,
        }