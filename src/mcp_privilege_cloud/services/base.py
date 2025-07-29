"""Base service class for CyberArk PCloud services."""

import logging
from functools import wraps
from typing import Dict, Any, Callable, TypeVar, Awaitable

from ..exceptions import CyberArkAPIError

F = TypeVar('F', bound=Callable[..., Any])

def handle_sdk_errors(operation_name: str) -> Callable[[F], F]:
    """Decorator for consistent SDK error handling across all service methods.
    
    Args:
        operation_name: Human-readable description of the operation for logging
        
    Returns:
        Decorated function with centralized error handling
    """
    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            try:
                result = await func(self, *args, **kwargs)
                return result
            except Exception as e:
                self.logger.error(f"Error in {operation_name}: {str(e)}")
                if "401" in str(e) or "authentication" in str(e).lower():
                    raise CyberArkAPIError(f"Authentication failed during {operation_name}: {str(e)}")
                elif "403" in str(e) or "forbidden" in str(e).lower():
                    raise CyberArkAPIError(f"Access denied for {operation_name}: {str(e)}")
                elif "404" in str(e) or "not found" in str(e).lower():
                    raise CyberArkAPIError(f"Resource not found during {operation_name}: {str(e)}")
                elif "429" in str(e) or "rate limit" in str(e).lower():
                    raise CyberArkAPIError(f"Rate limit exceeded during {operation_name}: {str(e)}")
                else:
                    raise CyberArkAPIError(f"Failed {operation_name}: {str(e)}")
        return wrapper  # type: ignore
    return decorator


class BaseService:
    """Base class for all CyberArk PCloud service implementations."""
    
    def __init__(self, sdk_authenticator: Any, logger: logging.Logger) -> None:
        """Initialize base service with SDK authenticator and logger.
        
        Args:
            sdk_authenticator: CyberArk SDK authenticator instance
            logger: Logger instance for this service
        """
        self.sdk_authenticator = sdk_authenticator
        self.logger = logger
        
    def _ensure_service_initialized(self, service_name: str, service_instance: Any) -> None:
        """Ensure SDK service is properly initialized.
        
        Args:
            service_name: Name of the service for error reporting
            service_instance: SDK service instance to check
            
        Raises:
            CyberArkAPIError: If service is not initialized
        """
        if service_instance is None:
            raise CyberArkAPIError(f"{service_name} not initialized")