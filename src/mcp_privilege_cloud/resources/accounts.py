"""
Account resources for CyberArk MCP server.

This module provides resources for accessing CyberArk accounts through
URI-based addressing, including collections, individual accounts, and search.
"""

from typing import Any, Dict, List

from .base import CollectionResource, EntityResource


class AccountCollectionResource(CollectionResource):
    """Resource for listing all accessible accounts.
    
    Provides a collection of all accounts that the authenticated user can access
    across all safes.
    
    URI: cyberark://accounts
    """
    
    async def get_items(self) -> List[Dict[str, Any]]:
        """Get list of all accessible accounts."""
        # Use existing list_accounts method from the server
        accounts = await self.server.list_accounts()
        
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
                "platform_account_properties": account.get("platformAccountProperties", {}),
            }
            # Remove None values and empty dicts
            account_item = {k: v for k, v in account_item.items() if v is not None and v != {}}
            account_items.append(account_item)
        
        return account_items
    
    async def get_metadata(self) -> Dict[str, Any]:
        """Get account collection metadata."""
        base_metadata = await super().get_metadata()
        base_metadata.update({
            "supports_filtering": True,
            "supports_search": True,
            "supports_pagination": True,
            "filterable_fields": ["safe_name", "platform_id", "user_name", "address"],
            "sortable_fields": ["name", "created_time", "last_modified", "safe_name"],
            "search_endpoint": "cyberark://accounts/search",
        })
        return base_metadata


class AccountEntityResource(EntityResource):
    """Resource for individual account details.
    
    Provides detailed information about a specific account.
    
    URI: cyberark://accounts/{account_id}
    """
    
    async def get_entity_data(self) -> Dict[str, Any]:
        """Get detailed data for a specific account."""
        account_id = self.uri.identifier
        if not account_id:
            raise ValueError("Account ID is required for account entity resource")
        
        # Use existing get_account_details method from the server
        account_details = await self.server.get_account_details(account_id)
        
        # Format the account details
        account_data = {
            "id": account_details.get("id"),
            "name": account_details.get("name"),
            "address": account_details.get("address"),
            "user_name": account_details.get("userName"),
            "platform_id": account_details.get("platformId"),
            "safe_name": account_details.get("safeName"),
            "secret_type": account_details.get("secretType"),
            "created_time": account_details.get("createdTime"),
            "created_by": account_details.get("createdBy"),
            "last_modified": account_details.get("lastModifiedTime"),
            "last_modified_by": account_details.get("lastModifiedBy"),
        }
        
        # Add secret management information
        secret_mgmt = account_details.get("secretManagement", {})
        if secret_mgmt:
            account_data["secret_management"] = {
                "automatic_management_enabled": secret_mgmt.get("automaticManagementEnabled", False),
                "status": secret_mgmt.get("status"),
                "last_modified": secret_mgmt.get("lastModifiedTime"),
                "last_verified": secret_mgmt.get("lastVerifiedTime"),
                "last_reconciled": secret_mgmt.get("lastReconciledTime"),
            }
        
        # Add platform account properties
        platform_props = account_details.get("platformAccountProperties", {})
        if platform_props:
            account_data["platform_account_properties"] = platform_props
        
        # Add remote machines access info
        remote_access = account_details.get("remoteMachinesAccess", {})
        if remote_access:
            account_data["remote_machines_access"] = remote_access
        
        # Add related resources
        account_data["related_resources"] = {
            "safe": f"cyberark://safes/{account_details.get('safeName')}",
            "platform": f"cyberark://platforms/{account_details.get('platformId')}",
        }
        
        # Remove None values and empty dicts
        account_data = {k: v for k, v in account_data.items() if v is not None and v != {}}
        
        return account_data
    
    async def get_metadata(self) -> Dict[str, Any]:
        """Get account entity metadata."""
        base_metadata = await super().get_metadata()
        base_metadata.update({
            "supports_updates": True,  # create_account exists
            "supports_deletion": False,  # Not implemented yet
            "supports_password_operations": True,
            "related_resources": ["safe", "platform"],
            "permissions_required": ["list_accounts", "get_account_details"],
            "available_operations": [
                "change_password",
                "verify_password", 
                "set_next_password",
                "reconcile_password"
            ],
        })
        return base_metadata


class AccountSearchResource(CollectionResource):
    """Resource for searching accounts with query parameters.
    
    Provides search functionality for accounts with various filters.
    
    URI: cyberark://accounts/search?query={search_terms}&safe_name={safe}&...
    """
    
    async def get_items(self) -> List[Dict[str, Any]]:
        """Get search results for accounts based on query parameters."""
        query_params = self.uri.query_params
        
        # Extract search parameters
        keywords = query_params.get("query", "")
        safe_name = query_params.get("safe_name")
        username = query_params.get("username")
        address = query_params.get("address")
        platform_id = query_params.get("platform_id")
        
        # Use existing search_accounts method from the server
        accounts = await self.server.search_accounts(
            keywords=keywords if keywords else None,
            safe_name=safe_name,
            username=username,
            address=address,
            platform_id=platform_id
        )
        
        # Format accounts for resource consumption (same as AccountCollectionResource)
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
                # Add search relevance score if available
                "search_score": account.get("_score"),
            }
            # Remove None values and empty dicts
            account_item = {k: v for k, v in account_item.items() if v is not None and v != {}}
            account_items.append(account_item)
        
        return account_items
    
    async def get_metadata(self) -> Dict[str, Any]:
        """Get account search metadata."""
        base_metadata = await super().get_metadata()
        query_params = self.uri.query_params
        
        base_metadata.update({
            "search_query": query_params.get("query", ""),
            "search_filters": {k: v for k, v in query_params.items() if k != "query"},
            "supports_ranking": True,
            "supports_advanced_filters": True,
            "available_filters": [
                "safe_name",
                "username", 
                "address",
                "platform_id"
            ],
        })
        return base_metadata