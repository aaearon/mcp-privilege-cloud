"""Base service class for CyberArk PCloud services."""

import logging
from typing import Any

from ..exceptions import CyberArkAPIError


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
