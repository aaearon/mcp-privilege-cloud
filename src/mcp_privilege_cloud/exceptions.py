"""
CyberArk MCP Server Exceptions

Centralized exception definitions for the CyberArk Privilege Cloud MCP Server.
Includes compatibility layer for ark-sdk-python exceptions.
"""

from typing import Optional

# SDK exception imports for compatibility
try:
    from ark_sdk_python.models.services.pcloud.common.base_exceptions import (
        ArkServiceException,
        ArkPCloudException
    )
    from ark_sdk_python.models.auth.exceptions import ArkAuthException
    _SDK_AVAILABLE = True
except ImportError:
    # Fallback classes if SDK not available
    _SDK_AVAILABLE = False
    
    class ArkServiceException(Exception):  # type: ignore[no-redef]
        """Fallback class when SDK is not available"""
        pass
    
    class ArkPCloudException(Exception):  # type: ignore[no-redef]
        """Fallback class when SDK is not available"""
        pass
    
    class ArkAuthException(Exception):  # type: ignore[no-redef]
        """Fallback class when SDK is not available"""
        pass


class CyberArkAPIError(Exception):
    """Raised when CyberArk API returns an error - Legacy compatibility exception"""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class AuthenticationError(Exception):
    """Raised when authentication fails - Legacy compatibility exception"""
    pass


# SDK exception compatibility functions
def is_sdk_exception(exception: Exception) -> bool:
    """Check if an exception is from ark-sdk-python"""
    # Always check for our exception types (either real SDK or fallback classes)
    return isinstance(exception, (ArkServiceException, ArkPCloudException, ArkAuthException))


def convert_sdk_exception(exception: Exception) -> CyberArkAPIError:
    """Convert SDK exception to legacy CyberArkAPIError for backward compatibility"""
    if isinstance(exception, ArkAuthException):
        # AuthenticationError inherits from Exception but needs to return CyberArkAPIError
        return CyberArkAPIError(f"Authentication failed: {str(exception)}")
    elif isinstance(exception, (ArkServiceException, ArkPCloudException)):
        # Try to extract status code if available
        status_code = getattr(exception, 'status_code', None) or getattr(exception, 'response_code', None)
        return CyberArkAPIError(str(exception), status_code)
    else:
        # For any other exception, wrap it as CyberArkAPIError
        return CyberArkAPIError(str(exception))


# Re-export SDK exceptions for direct use
__all__ = [
    "CyberArkAPIError",
    "AuthenticationError", 
    "ArkServiceException",
    "ArkPCloudException",
    "ArkAuthException",
    "is_sdk_exception",
    "convert_sdk_exception"
]