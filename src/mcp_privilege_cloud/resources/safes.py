"""
Safe resources for CyberArk MCP server.

This module provides resources for accessing CyberArk safes and their contents
through URI-based addressing.
"""

from typing import Any, Dict, List

from .base import CollectionResource, EntityResource


class SafeCollectionResource(CollectionResource):
    """Resource for listing all accessible safes.
    
    Provides a collection of all safes that the authenticated user can access.
    
    URI: cyberark://safes
    """
    
    async def get_items(self) -> List[Dict[str, Any]]:
        """Get list of all accessible safes."""
        # Use existing list_safes method from the server
        safes = await self.server.list_safes()
        
        # Format safes for resource consumption
        safe_items = []
        for safe in safes:
            safe_item = {
                "name": safe.get("safeName"),
                "uri": f"cyberark://safes/{safe.get('safeName')}",
                "description": safe.get("description", ""),
                "location": safe.get("location", ""),
                "created_time": safe.get("creationTime"),
                "last_modified": safe.get("lastModifiedTime"),
                "managing_cpm": safe.get("managingCPM"),
                "number_of_versions_retention": safe.get("numberOfVersionsRetention"),
                "number_of_days_retention": safe.get("numberOfDaysRetention"),
                "auto_purge_enabled": safe.get("autoPurgeEnabled", False),
                "ole_db_enabled": safe.get("oleDbEnabled", False),
            }
            # Remove None values
            safe_item = {k: v for k, v in safe_item.items() if v is not None}
            safe_items.append(safe_item)
        
        return safe_items
    
    async def get_metadata(self) -> Dict[str, Any]:
        """Get safe collection metadata."""
        base_metadata = await super().get_metadata()
        base_metadata.update({
            "supports_filtering": True,
            "supports_search": True,
            "filterable_fields": ["name", "description", "location"],
            "sortable_fields": ["name", "created_time", "last_modified"],
        })
        return base_metadata


class SafeEntityResource(EntityResource):
    """Resource for individual safe details.
    
    Provides detailed information about a specific safe.
    
    URI: cyberark://safes/{safe_name}
    """
    
    async def get_entity_data(self) -> Dict[str, Any]:
        """Get detailed data for a specific safe."""
        safe_name = self.uri.identifier
        if not safe_name:
            raise ValueError("Safe name is required for safe entity resource")
        
        # Use existing get_safe_details method from the server
        safe_details = await self.server.get_safe_details(safe_name)
        
        # Format the safe details
        safe_data = {
            "name": safe_details.get("safeName"),
            "description": safe_details.get("description", ""),
            "location": safe_details.get("location", ""),
            "created_time": safe_details.get("creationTime"),
            "created_by": safe_details.get("createdBy"),
            "last_modified": safe_details.get("lastModifiedTime"),
            "last_modified_by": safe_details.get("lastModifiedBy"),
            "managing_cpm": safe_details.get("managingCPM"),
            "number_of_versions_retention": safe_details.get("numberOfVersionsRetention"),
            "number_of_days_retention": safe_details.get("numberOfDaysRetention"),
            "auto_purge_enabled": safe_details.get("autoPurgeEnabled", False),
            "ole_db_enabled": safe_details.get("oleDbEnabled", False),
            "is_expired": safe_details.get("isExpired", False),
            "size": safe_details.get("size"),
            "purge_frequency_days": safe_details.get("purgeFrequencyDays"),
        }
        
        # Add related resources
        safe_data["related_resources"] = {
            "accounts": f"cyberark://safes/{safe_name}/accounts",
            "members": f"cyberark://safes/{safe_name}/members",  # Future implementation
        }
        
        # Remove None values
        safe_data = {k: v for k, v in safe_data.items() if v is not None}
        
        return safe_data
    
    async def get_metadata(self) -> Dict[str, Any]:
        """Get safe entity metadata."""
        base_metadata = await super().get_metadata()
        base_metadata.update({
            "supports_updates": False,  # Not implemented yet
            "supports_deletion": False,  # Not implemented yet
            "related_resources": ["accounts", "members"],
            "permissions_required": ["list_safes", "get_safe_details"],
        })
        return base_metadata


class SafeAccountsResource(CollectionResource):
    """Resource for accounts within a specific safe.
    
    Provides a collection of all accounts stored in a specific safe.
    
    URI: cyberark://safes/{safe_name}/accounts
    """
    
    async def get_items(self) -> List[Dict[str, Any]]:
        """Get list of accounts in the specified safe."""
        safe_name = self.uri.identifier
        if not safe_name:
            raise ValueError("Safe name is required for safe accounts resource")
        
        # Use existing list_accounts method with safe filter
        accounts = await self.server.list_accounts(safe_name=safe_name)
        
        # Format accounts for resource consumption
        account_items = []
        for account in accounts:
            account_item = {
                "id": account.get("id"),
                "name": account.get("name"),
                "uri": f"cyberark://accounts/{account.get('id')}",
                "address": account.get("address"),
                "user_name": account.get("userName"),
                "platform_id": account.get("platformId"),
                "safe_name": account.get("safeName"),
                "secret_type": account.get("secretType"),
                "status": account.get("secretManagement", {}).get("status"),
                "last_modified": account.get("secretManagement", {}).get("lastModifiedTime"),
                "last_verified": account.get("secretManagement", {}).get("lastVerifiedTime"),
                "created_time": account.get("createdTime"),
            }
            # Remove None values
            account_item = {k: v for k, v in account_item.items() if v is not None}
            account_items.append(account_item)
        
        return account_items
    
    async def get_metadata(self) -> Dict[str, Any]:
        """Get safe accounts collection metadata."""
        base_metadata = await super().get_metadata()
        base_metadata.update({
            "parent_safe": self.uri.identifier,
            "supports_filtering": True,
            "supports_search": True,
            "filterable_fields": ["name", "address", "user_name", "platform_id"],
            "sortable_fields": ["name", "created_time", "last_modified"],
        })
        return base_metadata