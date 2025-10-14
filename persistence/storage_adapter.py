"""Storage adapter pattern for flexible backend selection.

This module provides an abstraction layer for DPDA storage, allowing
switching between in-memory and database backends via configuration.

Backends:
- MemoryStorage: Fast in-memory storage (default, not persistent)
- DatabaseStorage: SQLite-backed persistent storage
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from core.session import DPDABuilder
from persistence.database import get_db
from persistence.repository import DPDARepository


class StorageBackend(ABC):
    """Abstract base class for storage backends."""

    @abstractmethod
    def create_dpda(self, dpda_id: str, session_id: str, name: str, builder: DPDABuilder) -> str:
        """Create a new DPDA in storage."""
        pass

    @abstractmethod
    def get_dpda(self, dpda_id: str, session_id: str) -> Optional[DPDABuilder]:
        """Retrieve a DPDA from storage."""
        pass

    @abstractmethod
    def list_dpdas(self, session_id: str) -> List[Dict]:
        """List all DPDAs for a session."""
        pass

    @abstractmethod
    def update_dpda(self, dpda_id: str, session_id: str, builder: DPDABuilder) -> bool:
        """Update an existing DPDA."""
        pass

    @abstractmethod
    def delete_dpda(self, dpda_id: str, session_id: str) -> bool:
        """Delete a DPDA from storage."""
        pass

    @abstractmethod
    def exists(self, dpda_id: str, session_id: str) -> bool:
        """Check if a DPDA exists in storage."""
        pass


class MemoryStorage(StorageBackend):
    """In-memory storage implementation (not persistent across restarts)."""

    def __init__(self):
        """Initialize in-memory storage."""
        # Storage format: {"{session_id}:{dpda_id}": {"name": str, "builder": DPDABuilder}}
        self._storage: Dict[str, Dict] = {}

    def _make_key(self, dpda_id: str, session_id: str) -> str:
        """Create storage key from session and DPDA ID."""
        return f"{session_id}:{dpda_id}"

    def create_dpda(self, dpda_id: str, session_id: str, name: str, builder: DPDABuilder) -> str:
        """Create a new DPDA in memory."""
        key = self._make_key(dpda_id, session_id)
        self._storage[key] = {
            "id": dpda_id,
            "session_id": session_id,
            "name": name,
            "builder": builder.copy()  # Store a copy to avoid shared references
        }
        return dpda_id

    def get_dpda(self, dpda_id: str, session_id: str) -> Optional[DPDABuilder]:
        """Retrieve a DPDA from memory."""
        key = self._make_key(dpda_id, session_id)
        if key in self._storage:
            return self._storage[key]["builder"].copy()  # Return a copy to avoid mutations
        return None

    def list_dpdas(self, session_id: str) -> List[Dict]:
        """List all DPDAs for a session from memory."""
        session_prefix = f"{session_id}:"
        result = []

        for key, data in self._storage.items():
            if key.startswith(session_prefix):
                result.append({
                    "id": data["id"],
                    "name": data["name"],
                    "session_id": data["session_id"]
                })

        return result

    def update_dpda(self, dpda_id: str, session_id: str, builder: DPDABuilder, name: str = None) -> bool:
        """Update an existing DPDA in memory."""
        key = self._make_key(dpda_id, session_id)
        if key in self._storage:
            self._storage[key]["builder"] = builder.copy()  # Store a copy
            # Update name if provided
            if name is not None:
                self._storage[key]["name"] = name
            return True
        return False

    def delete_dpda(self, dpda_id: str, session_id: str) -> bool:
        """Delete a DPDA from memory."""
        key = self._make_key(dpda_id, session_id)
        if key in self._storage:
            del self._storage[key]
            return True
        return False

    def exists(self, dpda_id: str, session_id: str) -> bool:
        """Check if a DPDA exists in memory."""
        key = self._make_key(dpda_id, session_id)
        return key in self._storage


class DatabaseStorage(StorageBackend):
    """Database-backed storage implementation (persistent across restarts)."""

    def __init__(self):
        """Initialize database storage."""
        # Repository is created per-operation to ensure proper session management
        pass

    def create_dpda(self, dpda_id: str, session_id: str, name: str, builder: DPDABuilder) -> str:
        """Create a new DPDA in database."""
        db = next(get_db())
        try:
            repo = DPDARepository(db)
            return repo.create_dpda(dpda_id, session_id, name, builder)
        finally:
            db.close()

    def get_dpda(self, dpda_id: str, session_id: str) -> Optional[DPDABuilder]:
        """Retrieve a DPDA from database."""
        db = next(get_db())
        try:
            repo = DPDARepository(db)
            return repo.get_dpda(dpda_id, session_id)
        finally:
            db.close()

    def list_dpdas(self, session_id: str) -> List[Dict]:
        """List all DPDAs for a session from database."""
        db = next(get_db())
        try:
            repo = DPDARepository(db)
            return repo.list_dpdas(session_id)
        finally:
            db.close()

    def update_dpda(self, dpda_id: str, session_id: str, builder: DPDABuilder, name: str = None) -> bool:
        """Update an existing DPDA in database."""
        db = next(get_db())
        try:
            repo = DPDARepository(db)
            success = repo.update_dpda(dpda_id, session_id, builder)
            # If name is provided, also update the record name
            if success and name is not None:
                repo.update_dpda_name(dpda_id, session_id, name)
            return success
        finally:
            db.close()

    def delete_dpda(self, dpda_id: str, session_id: str) -> bool:
        """Delete a DPDA from database."""
        db = next(get_db())
        try:
            repo = DPDARepository(db)
            return repo.delete_dpda(dpda_id, session_id)
        finally:
            db.close()

    def exists(self, dpda_id: str, session_id: str) -> bool:
        """Check if a DPDA exists in database."""
        db = next(get_db())
        try:
            repo = DPDARepository(db)
            return repo.dpda_exists(dpda_id, session_id)
        finally:
            db.close()


def get_storage_backend(backend_type: Optional[str] = None) -> StorageBackend:
    """
    Factory function to get storage backend instance.

    Args:
        backend_type: Type of storage ('memory' or 'database').
                     If None, reads from config.STORAGE_BACKEND.
                     Defaults to 'memory' if not specified.

    Returns:
        StorageBackend instance

    Raises:
        ValueError: If invalid backend type specified
    """
    # Determine backend type
    if backend_type is None:
        # Import here to avoid circular dependency
        from config import config
        backend_type = config.STORAGE_BACKEND

    backend_type = backend_type.lower()

    if backend_type == 'memory':
        return MemoryStorage()
    elif backend_type == 'database':
        return DatabaseStorage()
    else:
        raise ValueError(f"Invalid storage backend: {backend_type}. Must be 'memory' or 'database'.")
