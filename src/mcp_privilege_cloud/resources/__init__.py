"""
MCP Resources package for CyberArk Privilege Cloud integration.

This package provides resource implementations for the Model Context Protocol (MCP),
enabling URI-based access to CyberArk entities like safes, accounts, and platforms.
"""

from .accounts import AccountCollectionResource, AccountEntityResource, AccountSearchResource
from .base import BaseResource, CollectionResource, EntityResource, ResourceURI
from .platforms import PlatformCollectionResource, PlatformEntityResource, PlatformPackagesResource
from .registry import ResourceRegistry
from .safes import SafeAccountsResource, SafeCollectionResource, SafeEntityResource
from .system import HealthResource

__all__ = [
    # Base classes
    "BaseResource",
    "CollectionResource", 
    "EntityResource",
    "ResourceURI",
    "ResourceRegistry",
    # System resources
    "HealthResource",
    # Safe resources
    "SafeCollectionResource",
    "SafeEntityResource", 
    "SafeAccountsResource",
    # Account resources
    "AccountCollectionResource",
    "AccountEntityResource",
    "AccountSearchResource",
    # Platform resources
    "PlatformCollectionResource",
    "PlatformEntityResource",
    "PlatformPackagesResource",
]