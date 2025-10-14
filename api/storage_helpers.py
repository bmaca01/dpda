"""Helper functions for bridging DPDASession and storage backend.

The API endpoints work with DPDASession objects (which provide convenient methods),
while the storage backend works with DPDABuilder objects (pure data).

These helpers manage the conversion between the two.
"""

from typing import Optional
from core.session import DPDASession, DPDABuilder
from persistence.storage_adapter import get_storage_backend, StorageBackend


class SessionStorage:
    """Manages DPDA sessions with persistent storage backend."""

    def __init__(self):
        """Initialize with configured storage backend."""
        self.storage: StorageBackend = get_storage_backend()

    def create_session(self, dpda_id: str, session_id: str, name: str) -> DPDASession:
        """
        Create a new DPDA session and store it.

        Args:
            dpda_id: DPDA identifier
            session_id: Session identifier
            name: DPDA name

        Returns:
            New DPDASession instance
        """
        # Create a new session
        session = DPDASession(name=f"session_{dpda_id}")
        session.new_dpda(name)

        # Store the builder
        builder = session.get_current_builder()
        self.storage.create_dpda(dpda_id, session_id, name, builder)

        return session

    def get_session(self, dpda_id: str, session_id: str) -> Optional[DPDASession]:
        """
        Retrieve a DPDA session from storage.

        Args:
            dpda_id: DPDA identifier
            session_id: Session identifier

        Returns:
            DPDASession instance if found, None otherwise
        """
        # Load builder from storage
        builder = self.storage.get_dpda(dpda_id, session_id)
        if builder is None:
            return None

        # Get DPDA metadata to retrieve the actual name
        dpdas_list = self.storage.list_dpdas(session_id)
        dpda_name = None
        for dpda_info in dpdas_list:
            if dpda_info['id'] == dpda_id:
                dpda_name = dpda_info.get('name', f"dpda_{dpda_id}")
                break

        if dpda_name is None:
            dpda_name = f"dpda_{dpda_id}"

        # Reconstruct session from builder
        session = DPDASession(name=f"session_{dpda_id}")
        session.dpdas[dpda_name] = builder
        session.current_dpda_name = dpda_name

        return session

    def update_session(self, dpda_id: str, session_id: str, session: DPDASession, name: str = None) -> bool:
        """
        Update a DPDA session in storage.

        Args:
            dpda_id: DPDA identifier
            session_id: Session identifier
            session: Updated DPDASession instance
            name: New DPDA name (optional, updates the record name if provided)

        Returns:
            True if updated successfully, False if not found
        """
        builder = session.get_current_builder()
        return self.storage.update_dpda(dpda_id, session_id, builder, name=name)

    def delete_session(self, dpda_id: str, session_id: str) -> bool:
        """
        Delete a DPDA session from storage.

        Args:
            dpda_id: DPDA identifier
            session_id: Session identifier

        Returns:
            True if deleted successfully, False if not found
        """
        return self.storage.delete_dpda(dpda_id, session_id)

    def exists(self, dpda_id: str, session_id: str) -> bool:
        """
        Check if a DPDA session exists.

        Args:
            dpda_id: DPDA identifier
            session_id: Session identifier

        Returns:
            True if exists, False otherwise
        """
        return self.storage.exists(dpda_id, session_id)

    def list_sessions(self, session_id: str) -> list:
        """
        List all DPDA sessions for a given session ID.

        Args:
            session_id: Session identifier

        Returns:
            List of DPDA metadata dictionaries
        """
        return self.storage.list_dpdas(session_id)


# Global instance
session_storage = SessionStorage()
