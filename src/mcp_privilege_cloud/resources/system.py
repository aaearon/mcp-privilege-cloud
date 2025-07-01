"""
System and health resources for CyberArk MCP server.

This module provides resources for system health monitoring and status information.
"""

import datetime
from typing import Any, Dict

from .base import EntityResource


class HealthResource(EntityResource):
    """Resource for CyberArk system health status.
    
    Provides health check information including connectivity status,
    response times, and system metrics.
    
    URI: cyberark://health/
    """
    
    async def get_entity_data(self) -> Dict[str, Any]:
        """Get health check data from the CyberArk server."""
        try:
            # Use existing health check method from the server
            health_result = await self.server.health_check()
            
            # Extract health information
            safe_count = health_result.get("safe_count", 0)
            is_healthy = health_result.get("status") == "healthy"
            
            health_data = {
                "status": "healthy" if is_healthy else "unhealthy",
                "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
                "connectivity": {
                    "cyberark_api": is_healthy,
                    "authentication": is_healthy,
                },
                "metrics": {
                    "accessible_safes": safe_count,
                    "response_time_ms": health_result.get("response_time_ms"),
                },
                "service_info": {
                    "name": "CyberArk Privilege Cloud MCP Server",
                    "version": "0.1.0",
                    "capabilities": ["tools", "resources"],
                },
                "endpoints": {
                    "identity_url": getattr(getattr(self.server, 'auth', None), 'identity_url', None),
                    "api_url": getattr(self.server, 'base_url', None),
                }
            }
            
            return health_data
            
        except Exception as e:
            # Return error status if health check fails
            return {
                "status": "error",
                "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
                "error": {
                    "message": str(e),
                    "type": type(e).__name__,
                },
                "connectivity": {
                    "cyberark_api": False,
                    "authentication": False,
                },
                "service_info": {
                    "name": "CyberArk Privilege Cloud MCP Server",
                    "version": "0.1.0",
                    "capabilities": ["tools", "resources"],
                }
            }
    
    async def get_metadata(self) -> Dict[str, Any]:
        """Get health resource metadata."""
        base_metadata = await super().get_metadata()
        base_metadata.update({
            "refresh_interval_seconds": 30,
            "provides_real_time_data": True,
            "monitoring_capabilities": [
                "connectivity_status",
                "response_time_metrics", 
                "safe_accessibility",
                "authentication_status"
            ]
        })
        return base_metadata