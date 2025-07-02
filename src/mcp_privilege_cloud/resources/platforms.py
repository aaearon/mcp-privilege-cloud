"""
Platform resources for CyberArk MCP server.

This module provides resources for accessing CyberArk platforms and their
configurations through URI-based addressing.
"""

from typing import Any, Dict, List

from .base import BaseResource, CollectionResource, EntityResource


class PlatformCollectionResource(CollectionResource):
    """Resource for listing all available platforms.
    
    Provides a collection of all platforms that can be used for account creation
    and management.
    
    URI: cyberark://platforms
    """
    
    async def get_items(self) -> List[Dict[str, Any]]:
        """Get list of all available platforms with complete information.
        
        This enhanced implementation uses the list_platforms_with_details() method
        from Task A3 to provide comprehensive platform information including:
        - Basic platform info (id, name, systemType, etc.)
        - Detailed policy settings 
        - Connection components
        - Privileged access workflows
        - Enhanced field conversion and data formatting
        
        Falls back gracefully to basic platform info if enhanced features fail.
        """
        try:
            # Try to use enhanced API from Task A3 first
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
                
            # Extract data from the nested structure (existing logic)
            general = platform.get("general", {})
            if not general:
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
            platform_item = BaseResource._clean_data(platform_item, remove_empty_strings=True)
            platform_items.append(platform_item)
        
        return platform_items
    
    def _create_enhanced_platform_item(self, platform: Dict[str, Any]) -> Dict[str, Any]:
        """Create enhanced platform item with complete information and field conversion."""
        # Start with basic platform info
        platform_item = {
            "id": platform.get("id"),
            "name": platform.get("name"),
            "uri": f"cyberark://platforms/{platform.get('id')}",
            "description": platform.get("description", ""),
            "system_type": platform.get("systemType"),
            "active": platform.get("active", True),
            "platform_base_id": platform.get("platformBaseID"),
            "platform_type": platform.get("platformType"),
        }
        
        # Add enhanced details if available
        details = platform.get("details", {})
        if details:
            # Add policy information
            platform_item.update({
                "policy_id": details.get("policyId"),
                "policy_name": details.get("policyName"),
            })
            
            # Add general settings with field conversion
            general_settings = details.get("generalSettings", {})
            if general_settings:
                converted_general = self._convert_field_names(general_settings)
                platform_item["general_settings"] = converted_general
            
            # Add connection components with field conversion
            connection_components = details.get("connectionComponents", [])
            if connection_components:
                converted_components = []
                for component in connection_components:
                    converted_component = self._convert_field_names(component)
                    # Handle nested parameters
                    if "parameters" in component:
                        converted_component["parameters"] = self._convert_field_names(component["parameters"])
                    converted_components.append(converted_component)
                platform_item["connection_components"] = converted_components
            else:
                platform_item["connection_components"] = []
            
            # Add privileged access workflows with field conversion
            workflows = details.get("privilegedAccessWorkflows", {})
            if workflows:
                converted_workflows = self._convert_field_names(workflows)
                platform_item["privileged_access_workflows"] = converted_workflows
            else:
                platform_item["privileged_access_workflows"] = {}
        
        # Add credential management info if available (from basic platform info)
        creds_mgmt = platform.get("credentialsManagement", {})
        if creds_mgmt:
            platform_item.update({
                "credential_management": True,
                "allow_manual_change": creds_mgmt.get("allowManualChange", False),
                "perform_periodic_change": creds_mgmt.get("performPeriodicChange", False),
                "allow_manual_verification": creds_mgmt.get("allowManualVerification", False),
            })
        
        # Add session management info if available (from basic platform info)
        session_mgmt = platform.get("sessionManagement", {})
        if session_mgmt:
            platform_item.update({
                "privileged_session_management": session_mgmt.get("requirePrivilegedSessionMonitoringAndIsolation", False),
                "record_sessions": session_mgmt.get("recordAndSaveSessionActivity", False),
                "psm_server_id": session_mgmt.get("PSMServerID"),
            })
        
        # Remove None values and empty strings
        platform_item = BaseResource._clean_data(platform_item, remove_empty_strings=True)
        return platform_item
    
    def _convert_field_names(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert CamelCase field names to snake_case for consistency."""
        if not isinstance(data, dict):
            return data
        
        converted = {}
        for key, value in data.items():
            # Convert CamelCase to snake_case
            snake_key = self._camel_to_snake(key)
            
            # Recursively convert nested dictionaries
            if isinstance(value, dict):
                converted[snake_key] = self._convert_field_names(value)
            elif isinstance(value, list) and value and isinstance(value[0], dict):
                converted[snake_key] = [self._convert_field_names(item) for item in value]
            else:
                converted[snake_key] = value
        
        return converted
    
    def _camel_to_snake(self, name: str) -> str:
        """Convert CamelCase to snake_case."""
        import re
        
        # Handle special cases
        special_cases = {
            "PSMServerID": "psm_server_id",
            "PSMServerId": "psm_server_id", 
            "platformBaseID": "platform_base_id",
            "systemType": "system_type",
            "platformType": "platform_type",
            "allowManualChange": "allow_manual_change",
            "performPeriodicChange": "perform_periodic_change",
            "allowManualVerification": "allow_manual_verification",
            "requirePasswordChangeEveryXDays": "require_password_change_every_x_days",
            "enforceCheckinExclusivePassword": "enforce_checkin_exclusive_password",
            "enforceOneTimePasswordAccess": "enforce_one_time_password_access",
            "requireDualControlPasswordAccessApproval": "require_dual_control_password_access_approval",
            "requireUsersToSpecifyReasonForAccess": "require_users_to_specify_reason_for_access",
            "connectionMethod": "connection_method",
            "userRole": "user_role",
            "policyId": "policy_id",
            "policyName": "policy_name",
            "psmServerId": "psm_server_id"
        }
        
        if name in special_cases:
            return special_cases[name]
        
        # General conversion: insert underscore before uppercase letters
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    
    async def get_metadata(self) -> Dict[str, Any]:
        """Get enhanced platform collection metadata."""
        base_metadata = await super().get_metadata()
        
        # Check if enhanced features are available
        has_enhanced_features = hasattr(self.server, 'list_platforms_with_details')
        
        base_metadata.update({
            "supports_filtering": True,
            "supports_search": True,
            "filterable_fields": ["system_type", "active", "platform_type"],
            "sortable_fields": ["name", "id", "system_type"],
        })
        
        if has_enhanced_features:
            # Enhanced metadata when complete info is available
            base_metadata.update({
                "data_source": "cyberark_platforms_api_enhanced",
                "supports_complete_info": True,
                "enhanced_fields": [
                    "policy_id", "policy_name", "general_settings", 
                    "connection_components", "privileged_access_workflows"
                ],
                "field_conversion": "camelCase_to_snake_case",
                "enhanced_filterable_fields": [
                    "policy_id", "connection_method", "psm_server_id"
                ]
            })
        else:
            # Basic metadata when only basic info is available
            base_metadata.update({
                "data_source": "cyberark_platforms_api",
                "supports_complete_info": False
            })
        
        return base_metadata


class PlatformEntityResource(EntityResource):
    """Resource for individual platform details.
    
    Provides detailed configuration information about a specific platform.
    
    URI: cyberark://platforms/{platform_id}
    """
    
    
    @staticmethod
    def _camel_to_snake(name: str) -> str:
        """Convert CamelCase/camelCase to snake_case.
        
        Handles various CyberArk API field name patterns:
        - SystemType -> system_type
        - PSMServerID -> psm_server_id  
        - allowManualChange -> allow_manual_change
        - requirePasswordChangeEveryXDays -> require_password_change_every_x_days
        """
        if not name:
            return name
            
        # Handle special cases first
        # Convert common ID patterns
        name = name.replace('ID', '_id')
        name = name.replace('_id_', '_id')  # Fix double replacement
        
        # Insert underscores before uppercase letters (but not at start)
        import re
        # First, handle sequences of uppercase letters followed by lowercase
        name = re.sub('([A-Z]+)([A-Z][a-z])', r'\1_\2', name)
        # Then handle lowercase followed by uppercase
        name = re.sub('([a-z])([A-Z])', r'\1_\2', name)
        
        # Convert to lowercase
        result = name.lower()
        
        # Clean up multiple underscores
        result = re.sub('_+', '_', result)
        
        # Remove leading/trailing underscores
        result = result.strip('_')
        
        return result
    
    @staticmethod 
    def _convert_yes_no_to_boolean(value: Any) -> Any:
        """Convert Yes/No strings to boolean values.
        
        Handles CyberArk API boolean representations:
        - "Yes" -> True
        - "No" -> False
        - Case insensitive
        - Also handles "True"/"False" strings
        - Non-boolean strings remain unchanged
        """
        if not isinstance(value, str):
            return value
            
        value_lower = value.lower()
        if value_lower in ('yes', 'true'):
            return True
        elif value_lower in ('no', 'false'):
            return False
        else:
            return value
    
    @staticmethod
    def _convert_string_to_int(value: Any) -> Any:
        """Convert string numbers to integers where appropriate.
        
        Handles CyberArk API numeric strings:
        - "90" -> 90
        - "-1" -> -1 (for unlimited values)
        - Non-numeric strings remain unchanged
        - Decimal strings remain unchanged
        """
        if not isinstance(value, str) or not value:
            return value
            
        # Only convert if it's a valid integer (no decimal point)
        if value.isdigit() or (value.startswith('-') and value[1:].isdigit()):
            try:
                return int(value)
            except ValueError:
                return value
        else:
            return value
    
    @staticmethod
    def _is_policy_string(key: str, value: str) -> bool:
        """Determine if a string value should be preserved as-is.
        
        Policy strings that contain paths, commands, SQL, etc. should not
        be transformed even if they contain Yes/No or numeric values.
        """
        if not isinstance(value, str):
            return False
            
        # Check for common policy string patterns
        policy_indicators = [
            '\\',  # Windows paths or domain names
            '/',   # Unix paths
            'SELECT', 'INSERT', 'UPDATE', 'DELETE',  # SQL
            'cmd.exe', 'powershell', 'bash',  # Commands
            'HKEY_', 'BUILTIN\\', 'NT AUTHORITY\\',  # Registry/Windows
            'C:', 'D:', '/usr/', '/etc/', '/var/',  # Paths
        ]
        
        value_upper = value.upper()
        for indicator in policy_indicators:
            if indicator.upper() in value_upper:
                return True
                
        # Check for complex expressions (contains special chars beyond basic alphanumeric)
        import re
        if re.search(r'[\\/:;=\'"<>{}[\]()&|]', value):
            return True
            
        return False
    
    @classmethod
    def _transform_platform_details(cls, data: Any) -> Any:
        """Transform platform details API response to snake_case fields.
        
        Recursively transforms:
        - Field names: CamelCase -> snake_case
        - Yes/No strings -> boolean (except in policy strings)
        - Numeric strings -> integers (except in policy strings)
        """
        if data is None:
            return None
            
        if isinstance(data, dict):
            transformed = {}
            for key, value in data.items():
                # Transform the key name
                snake_key = cls._camel_to_snake(key)
                
                # Recursively transform the value
                if isinstance(value, (dict, list)):
                    transformed_value = cls._transform_platform_details(value)
                elif isinstance(value, str) and not cls._is_policy_string(key, value):
                    # Apply string transformations only if not a policy string
                    transformed_value = cls._convert_yes_no_to_boolean(value)
                    if transformed_value == value:  # If not converted to boolean, try int
                        transformed_value = cls._convert_string_to_int(value)
                else:
                    transformed_value = value
                    
                transformed[snake_key] = transformed_value
            return transformed
            
        elif isinstance(data, list):
            return [cls._transform_platform_details(item) for item in data]
        else:
            return data

    async def get_entity_data(self) -> Dict[str, Any]:
        """Get detailed data for a specific platform."""
        platform_id = self.uri.identifier
        if not platform_id:
            raise ValueError("Platform ID is required for platform entity resource")
        
        # Use existing get_platform_details method from the server
        platform_details = await self.server.get_platform_details(platform_id)
        
        # Apply field transformation to the entire platform details response
        # This handles the raw API response and transforms field names and values
        transformed_details = self._transform_platform_details(platform_details)
        
        # Extract the transformed details section
        details = transformed_details.get("details", {})
        
        # Format the platform data using transformed field names
        platform_data = {
            "id": details.get("policy_id"),
            "name": details.get("policy_name"),
            "description": details.get("description", ""),
            "system_type": details.get("system_type"),
            "active": details.get("active", True),
            "platform_base_id": details.get("platform_base_id"),
            "platform_type": details.get("platform_type"),
            "search_for_usages": details.get("search_for_usages", False),
        }
        
        # Add connection components if available (already transformed)
        connection_components = details.get("connection_components", [])
        if connection_components:
            platform_data["connection_components"] = []
            for component in connection_components:
                comp_data = {
                    "psm_server_id": component.get("psm_server_id"),
                    "name": component.get("name"),
                    "display_name": component.get("display_name"),
                    "connection_method": component.get("connection_method"),
                    "enabled": component.get("enabled", False),
                }
                # Remove None values
                comp_data = BaseResource._clean_data(comp_data)
                platform_data["connection_components"].append(comp_data)
        
        # Add properties if available (already transformed)
        properties = details.get("properties", [])
        if properties:
            platform_data["properties"] = []
            for prop in properties:
                prop_data = {
                    "name": prop.get("name"),
                    "display_name": prop.get("display_name"),
                    "type": prop.get("type"),
                    "required": prop.get("required", False),
                    "default_value": prop.get("default_value"),
                    "length": prop.get("length"),
                }
                # Remove None values
                prop_data = BaseResource._clean_data(prop_data)
                platform_data["properties"].append(prop_data)
        
        # Add capabilities information (using transformed field names)
        platform_data["capabilities"] = {
            "privileged_session_management": details.get("privileged_session_management", False),
            "credential_management": details.get("credentials_management", False),
            "supports_password_change": any(
                comp.get("connection_method") == "RPC" 
                for comp in connection_components
            ),
        }
        
        # Add related resources
        platform_data["related_resources"] = {
            "accounts_using_platform": f"cyberark://accounts?platform_id={platform_id}",
        }
        
        # Remove None values and empty lists/dicts
        platform_data = BaseResource._clean_data(platform_data, remove_empty_collections=True)
        
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