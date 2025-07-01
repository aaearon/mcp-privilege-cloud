# Configuration Centralization - Code Examples

## Core Configuration Infrastructure

### File: `src/mcp_privilege_cloud/config.py`

```python
"""
Centralized configuration management for CyberArk MCP Server.

This module provides type-safe configuration loading, validation, and caching
for all CyberArk MCP Server components.
"""

import os
import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from pathlib import Path


@dataclass(frozen=True)
class CyberArkConfig:
    """Immutable configuration for CyberArk MCP Server."""
    
    # Authentication Configuration
    identity_tenant_id: str
    client_id: str  
    client_secret: str
    
    # Server Configuration
    subdomain: str
    api_timeout: int = 30
    max_retries: int = 3
    
    # Logging Configuration
    log_level: str = "INFO"
    
    # Advanced Configuration (extensibility)
    additional_config: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        ConfigValidator.validate_config(self)


class ConfigDefaults:
    """Centralized default values for configuration parameters."""
    
    API_TIMEOUT = 30
    MAX_RETRIES = 3
    LOG_LEVEL = "INFO"
    
    # Validation constants
    MIN_TIMEOUT = 5
    MAX_TIMEOUT = 300
    MIN_RETRIES = 1
    MAX_RETRIES = 10
    VALID_LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class ConfigValidator:
    """Configuration validation with comprehensive error handling."""
    
    @classmethod
    def validate_config(cls, config: CyberArkConfig) -> None:
        """Validate complete configuration with detailed error messages."""
        errors = []
        
        # Required fields validation
        if not config.identity_tenant_id:
            errors.append("CYBERARK_IDENTITY_TENANT_ID is required")
            
        if not config.client_id:
            errors.append("CYBERARK_CLIENT_ID is required")
            
        if not config.client_secret:
            errors.append("CYBERARK_CLIENT_SECRET is required")
            
        if not config.subdomain:
            errors.append("CYBERARK_SUBDOMAIN is required")
        
        # Numeric validation
        if not (ConfigDefaults.MIN_TIMEOUT <= config.api_timeout <= ConfigDefaults.MAX_TIMEOUT):
            errors.append(f"CYBERARK_API_TIMEOUT must be between {ConfigDefaults.MIN_TIMEOUT} and {ConfigDefaults.MAX_TIMEOUT} seconds")
            
        if not (ConfigDefaults.MIN_RETRIES <= config.max_retries <= ConfigDefaults.MAX_RETRIES):
            errors.append(f"CYBERARK_MAX_RETRIES must be between {ConfigDefaults.MIN_RETRIES} and {ConfigDefaults.MAX_RETRIES}")
        
        # Log level validation
        if config.log_level.upper() not in ConfigDefaults.VALID_LOG_LEVELS:
            errors.append(f"CYBERARK_LOG_LEVEL must be one of: {', '.join(ConfigDefaults.VALID_LOG_LEVELS)}")
        
        if errors:
            raise ValueError(f"Configuration validation failed:\n" + "\n".join(f"  - {error}" for error in errors))


class ConfigManager:
    """Singleton configuration manager with caching and validation."""
    
    _instance: Optional['ConfigManager'] = None
    _config: Optional[CyberArkConfig] = None
    
    def __new__(cls) -> 'ConfigManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def get_config(cls, reload: bool = False) -> CyberArkConfig:
        """Get validated configuration with caching."""
        manager = cls()
        
        if manager._config is None or reload:
            manager._config = manager._load_from_environment()
            
        return manager._config
    
    def _load_from_environment(self) -> CyberArkConfig:
        """Load configuration from environment variables."""
        try:
            # Required configuration
            identity_tenant_id = self._get_required_env("CYBERARK_IDENTITY_TENANT_ID")
            client_id = self._get_required_env("CYBERARK_CLIENT_ID")
            client_secret = self._get_required_env("CYBERARK_CLIENT_SECRET")
            subdomain = self._get_required_env("CYBERARK_SUBDOMAIN")
            
            # Optional configuration with defaults
            api_timeout = self._get_optional_env("CYBERARK_API_TIMEOUT", ConfigDefaults.API_TIMEOUT, int)
            max_retries = self._get_optional_env("CYBERARK_MAX_RETRIES", ConfigDefaults.MAX_RETRIES, int)
            log_level = self._get_optional_env("CYBERARK_LOG_LEVEL", ConfigDefaults.LOG_LEVEL, str).upper()
            
            return CyberArkConfig(
                identity_tenant_id=identity_tenant_id,
                client_id=client_id,
                client_secret=client_secret,
                subdomain=subdomain,
                api_timeout=api_timeout,
                max_retries=max_retries,
                log_level=log_level
            )
            
        except Exception as e:
            raise ValueError(f"Failed to load configuration: {e}")
    
    def _get_required_env(self, name: str) -> str:
        """Get required environment variable with clear error message."""
        value = os.getenv(name)
        if not value:
            raise ValueError(f"Required environment variable {name} is not set")
        return value
    
    def _get_optional_env(self, name: str, default: Any, var_type: type = str) -> Any:
        """Get optional environment variable with type conversion."""
        value = os.getenv(name)
        if value is None:
            return default
        return ConfigValidator.validate_environment_variable(name, value, var_type)
    
    @classmethod
    def reset(cls) -> None:
        """Reset configuration cache (for testing)."""
        manager = cls()
        manager._config = None


# Configuration testing utilities
class ConfigTestUtils:
    """Utilities for testing configuration in unit tests."""
    
    @staticmethod
    def create_test_config(**overrides) -> CyberArkConfig:
        """Create test configuration with optional overrides."""
        defaults = {
            'identity_tenant_id': 'test-tenant',
            'client_id': 'test-client',
            'client_secret': 'test-secret',
            'subdomain': 'test-subdomain',
            'api_timeout': 30,
            'max_retries': 3,
            'log_level': 'INFO'
        }
        defaults.update(overrides)
        return CyberArkConfig(**defaults)
    
    @staticmethod
    def mock_environment(env_vars: Dict[str, str]):
        """Context manager for mocking environment variables in tests."""
        import unittest.mock
        return unittest.mock.patch.dict(os.environ, env_vars)
```

## Migration Examples

### Authentication Migration Pattern

```python
# File: src/mcp_privilege_cloud/auth.py (Updated sections)

# Add import for new config system
from .config import CyberArkConfig, ConfigManager

class CyberArkAuthenticator:
    """CyberArk authentication client with centralized configuration."""
    
    def __init__(
        self,
        identity_tenant_id: str,
        client_id: str,
        client_secret: str,
        timeout: int = 30
    ):
        # Existing initialization logic remains unchanged
        pass
    
    @classmethod
    def from_config(cls, config: CyberArkConfig) -> "CyberArkAuthenticator":
        """Create authenticator from centralized configuration."""
        return cls(
            identity_tenant_id=config.identity_tenant_id,
            client_id=config.client_id,
            client_secret=config.client_secret,
            timeout=config.api_timeout
        )
    
    @classmethod
    def from_environment(cls) -> "CyberArkAuthenticator":
        """Create authenticator from environment variables (backward compatible)."""
        config = ConfigManager.get_config()
        return cls.from_config(config)
```

### Server Migration Pattern

```python
# File: src/mcp_privilege_cloud/server.py (Updated sections)

# Add import for new config system
from .config import CyberArkConfig, ConfigManager

class CyberArkMCPServer:
    """CyberArk MCP Server with centralized configuration."""
    
    def __init__(
        self,
        authenticator: CyberArkAuthenticator,
        subdomain: str,
        timeout: int = 30,
        max_retries: int = 3
    ):
        # Existing initialization logic remains unchanged
        pass
    
    @classmethod
    def from_config(cls, config: CyberArkConfig) -> "CyberArkMCPServer":
        """Create server from centralized configuration."""
        authenticator = CyberArkAuthenticator.from_config(config)
        return cls(
            authenticator=authenticator,
            subdomain=config.subdomain,
            timeout=config.api_timeout,
            max_retries=config.max_retries
        )
    
    @classmethod 
    def from_environment(cls) -> "CyberArkMCPServer":
        """Create server from environment variables (backward compatible)."""
        config = ConfigManager.get_config()
        return cls.from_config(config)
```

## Testing Infrastructure Examples

### Test Configuration Creation

```python
# File: tests/test_config.py

import pytest
import os
from unittest.mock import patch

from mcp_privilege_cloud.config import (
    CyberArkConfig, ConfigManager, ConfigDefaults, 
    ConfigValidator, ConfigTestUtils
)


class TestCyberArkConfig:
    """Test configuration data class and validation."""
    
    def test_config_creation_with_required_fields(self):
        """Test configuration creation with all required fields."""
        config = CyberArkConfig(
            identity_tenant_id="test-tenant",
            client_id="test-client", 
            client_secret="test-secret",
            subdomain="test-subdomain"
        )
        
        assert config.identity_tenant_id == "test-tenant"
        assert config.api_timeout == ConfigDefaults.API_TIMEOUT
        assert config.log_level == ConfigDefaults.LOG_LEVEL
    
    def test_config_validation_missing_required(self):
        """Test configuration validation with missing required fields."""
        with pytest.raises(ValueError, match="identity_tenant_id is required"):
            CyberArkConfig(
                identity_tenant_id="",
                client_id="test-client",
                client_secret="test-secret", 
                subdomain="test-subdomain"
            )


class TestConfigManager:
    """Test configuration manager functionality."""
    
    def setup_method(self):
        """Reset configuration before each test."""
        ConfigManager.reset()
    
    @patch.dict(os.environ, {
        'CYBERARK_IDENTITY_TENANT_ID': 'test-tenant',
        'CYBERARK_CLIENT_ID': 'test-client',
        'CYBERARK_CLIENT_SECRET': 'test-secret',
        'CYBERARK_SUBDOMAIN': 'test-subdomain'
    })
    def test_load_from_environment_success(self):
        """Test successful configuration loading from environment."""
        config = ConfigManager.get_config()
        
        assert config.identity_tenant_id == 'test-tenant'
        assert config.client_id == 'test-client'
        assert config.subdomain == 'test-subdomain'
        assert config.api_timeout == ConfigDefaults.API_TIMEOUT


class TestConfigTestUtils:
    """Test configuration testing utilities."""
    
    def test_create_test_config_defaults(self):
        """Test test configuration creation with defaults."""
        config = ConfigTestUtils.create_test_config()
        
        assert config.identity_tenant_id == 'test-tenant'
        assert config.api_timeout == 30
    
    def test_create_test_config_overrides(self):
        """Test test configuration creation with overrides."""
        config = ConfigTestUtils.create_test_config(
            api_timeout=60,
            log_level='DEBUG'
        )
        
        assert config.api_timeout == 60
        assert config.log_level == 'DEBUG'
```