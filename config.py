"""Centralized configuration management for DPDA Simulator API.

This module loads configuration from environment variables with sensible defaults.
Configuration can be set via:
1. Environment variables (highest priority)
2. .env file (loaded automatically if present)
3. Default values (lowest priority)

Usage:
    from config import config

    storage_backend = config.STORAGE_BACKEND
    database_url = config.DATABASE_URL
"""

import os
from pathlib import Path
from typing import List


class Config:
    """Application configuration loaded from environment variables."""

    def __init__(self):
        """Initialize configuration by loading .env file if present."""
        self._load_env_file()

    def _load_env_file(self):
        """Load environment variables from .env file if it exists."""
        env_file = Path(__file__).parent / '.env'
        if env_file.exists():
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue
                    # Parse KEY=VALUE
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        # Only set if not already in environment
                        if key not in os.environ:
                            os.environ[key] = value

    # ========================================================================
    # STORAGE CONFIGURATION
    # ========================================================================

    @property
    def STORAGE_BACKEND(self) -> str:
        """Storage backend type: 'memory' or 'database'."""
        return os.getenv('STORAGE_BACKEND', 'memory').lower()

    @property
    def DATABASE_URL(self) -> str:
        """Database connection URL."""
        return os.getenv('DATABASE_URL', 'sqlite:///./dpda_sessions.db')

    # ========================================================================
    # API SERVER CONFIGURATION
    # ========================================================================

    @property
    def API_HOST(self) -> str:
        """API server host."""
        return os.getenv('API_HOST', '0.0.0.0')

    @property
    def API_PORT(self) -> int:
        """API server port."""
        return int(os.getenv('API_PORT', '8000'))

    @property
    def API_RELOAD(self) -> bool:
        """Enable auto-reload on code changes."""
        return os.getenv('API_RELOAD', 'true').lower() == 'true'

    @property
    def LOG_LEVEL(self) -> str:
        """Logging level."""
        return os.getenv('LOG_LEVEL', 'info').lower()

    # ========================================================================
    # CORS CONFIGURATION
    # ========================================================================

    @property
    def CORS_ORIGINS(self) -> List[str]:
        """List of allowed CORS origins."""
        origins_str = os.getenv('CORS_ORIGINS', '*')
        if origins_str == '*':
            return ['*']
        return [origin.strip() for origin in origins_str.split(',')]

    # ========================================================================
    # SESSION CONFIGURATION
    # ========================================================================

    @property
    def SESSION_MAX_AGE(self) -> int:
        """Maximum session age in seconds."""
        return int(os.getenv('SESSION_MAX_AGE', '86400'))  # 24 hours

    @property
    def SESSION_CLEANUP_INTERVAL(self) -> int:
        """Session cleanup interval in seconds."""
        return int(os.getenv('SESSION_CLEANUP_INTERVAL', '3600'))  # 1 hour

    # ========================================================================
    # PERFORMANCE CONFIGURATION
    # ========================================================================

    @property
    def DB_POOL_SIZE(self) -> int:
        """Database connection pool size."""
        return int(os.getenv('DB_POOL_SIZE', '5'))

    @property
    def DB_MAX_OVERFLOW(self) -> int:
        """Maximum overflow connections beyond pool size."""
        return int(os.getenv('DB_MAX_OVERFLOW', '10'))

    @property
    def ENABLE_CACHING(self) -> bool:
        """Enable query result caching."""
        return os.getenv('ENABLE_CACHING', 'false').lower() == 'true'

    # ========================================================================
    # SECURITY CONFIGURATION
    # ========================================================================

    @property
    def RATE_LIMIT(self) -> int:
        """Rate limit (requests per minute per session)."""
        return int(os.getenv('RATE_LIMIT', '100'))

    @property
    def MAX_INPUT_LENGTH(self) -> int:
        """Maximum input string length for DPDA computation."""
        return int(os.getenv('MAX_INPUT_LENGTH', '10000'))

    @property
    def MAX_COMPUTATION_STEPS(self) -> int:
        """Maximum computation steps."""
        return int(os.getenv('MAX_COMPUTATION_STEPS', '10000'))

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    def is_development(self) -> bool:
        """Check if running in development mode."""
        return os.getenv('ENVIRONMENT', 'development').lower() == 'development'

    def is_production(self) -> bool:
        """Check if running in production mode."""
        return os.getenv('ENVIRONMENT', 'development').lower() == 'production'

    def is_testing(self) -> bool:
        """Check if running in test mode."""
        return os.getenv('TESTING', 'false').lower() == 'true'

    def summary(self) -> dict:
        """Return a dictionary of current configuration values."""
        return {
            'storage_backend': self.STORAGE_BACKEND,
            'database_url': self.DATABASE_URL,
            'api_host': self.API_HOST,
            'api_port': self.API_PORT,
            'api_reload': self.API_RELOAD,
            'log_level': self.LOG_LEVEL,
            'cors_origins': self.CORS_ORIGINS,
            'is_development': self.is_development(),
            'is_production': self.is_production(),
        }


# Global configuration instance
config = Config()


# Convenience function for testing
def override_config(**kwargs):
    """
    Override configuration values for testing.

    Example:
        override_config(STORAGE_BACKEND='database', DATABASE_URL='sqlite:///:memory:')
    """
    for key, value in kwargs.items():
        os.environ[key] = str(value)
