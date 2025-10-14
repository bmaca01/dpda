#!/usr/bin/env python3
"""
Script to run the DPDA FastAPI server.

This script loads configuration from .env file (if present) or environment variables,
then starts the uvicorn server with the configured settings.

Configuration:
- Storage backend: memory (fast, non-persistent) or database (persistent)
- API host/port: Configurable via API_HOST and API_PORT
- CORS origins: Configurable via CORS_ORIGINS
- See .env.example for all available configuration options

Usage:
    python run_api.py

    # Or with environment overrides:
    STORAGE_BACKEND=database python run_api.py
    API_PORT=8080 python run_api.py
"""

import uvicorn
from config import config
from persistence.database import init_db


def print_startup_banner():
    """Print startup information banner."""
    print("=" * 70)
    print("  DPDA Simulator API Server")
    print("=" * 70)
    print(f"Storage Backend:  {config.STORAGE_BACKEND.upper()}")
    if config.STORAGE_BACKEND == 'database':
        print(f"Database URL:     {config.DATABASE_URL}")
    print(f"API Endpoint:     http://{config.API_HOST}:{config.API_PORT}")
    print(f"API Docs:         http://{config.API_HOST}:{config.API_PORT}/docs")
    print(f"CORS Origins:     {', '.join(config.CORS_ORIGINS)}")
    print(f"Auto-reload:      {config.API_RELOAD}")
    print(f"Log Level:        {config.LOG_LEVEL.upper()}")
    print(f"Environment:      {'DEVELOPMENT' if config.is_development() else 'PRODUCTION'}")
    print("=" * 70)
    print()


if __name__ == "__main__":
    # Print configuration banner
    print_startup_banner()

    # Initialize database if using database backend
    if config.STORAGE_BACKEND == 'database':
        print("Initializing database tables...")
        init_db()
        print("Database initialized.\n")

    # Start uvicorn server
    uvicorn.run(
        "api.endpoints:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=config.API_RELOAD,
        log_level=config.LOG_LEVEL
    )
