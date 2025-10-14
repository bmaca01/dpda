"""Repository pattern for DPDA persistence operations."""

import json
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from persistence.database import DPDARecord
from core.session import DPDABuilder


class RepositoryError(Exception):
    """Custom exception for repository-related errors."""
    pass


class DPDARepository:
    """
    Repository for DPDA CRUD operations with session isolation.

    All operations are scoped to a specific session_id, ensuring that
    different users/sessions cannot access each other's DPDAs.
    """

    def __init__(self, db: Session):
        """
        Initialize repository with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def create_dpda(self, dpda_id: str, session_id: str, name: str, builder: DPDABuilder) -> str:
        """
        Create a new DPDA record.

        Args:
            dpda_id: Unique identifier for the DPDA (within session)
            session_id: Session identifier for isolation
            name: Human-readable name for the DPDA
            builder: DPDABuilder instance to persist

        Returns:
            The created DPDA's ID

        Raises:
            RepositoryError: If DPDA with same (id, session_id) already exists
        """
        # Serialize builder to JSON
        builder_json = json.dumps(builder.to_dict())

        # Create record
        record = DPDARecord(
            id=dpda_id,
            session_id=session_id,
            name=name,
            builder_json=builder_json
        )

        try:
            self.db.add(record)
            self.db.commit()
            return dpda_id
        except IntegrityError as e:
            self.db.rollback()
            raise RepositoryError(f"DPDA with id '{dpda_id}' already exists in session '{session_id}'") from e

    def get_dpda(self, dpda_id: str, session_id: str) -> Optional[DPDABuilder]:
        """
        Retrieve a DPDA by ID and session.

        Args:
            dpda_id: DPDA identifier
            session_id: Session identifier

        Returns:
            DPDABuilder instance if found, None otherwise
        """
        record = self.db.query(DPDARecord).filter_by(
            id=dpda_id,
            session_id=session_id
        ).first()

        if record is None:
            return None

        # Update last accessed timestamp
        self.update_last_accessed(dpda_id, session_id)

        # Deserialize and return builder
        builder_dict = json.loads(record.builder_json)
        return DPDABuilder.from_dict(builder_dict)

    def list_dpdas(self, session_id: str) -> List[Dict[str, Any]]:
        """
        List all DPDAs for a given session.

        Args:
            session_id: Session identifier

        Returns:
            List of dictionaries containing DPDA metadata
        """
        records = self.db.query(DPDARecord).filter_by(
            session_id=session_id
        ).order_by(DPDARecord.created_at.asc()).all()

        return [
            {
                'id': record.id,
                'name': record.name,
                'created_at': record.created_at,
                'last_accessed_at': record.last_accessed_at
            }
            for record in records
        ]

    def update_dpda(self, dpda_id: str, session_id: str, builder: DPDABuilder) -> bool:
        """
        Update an existing DPDA.

        Args:
            dpda_id: DPDA identifier
            session_id: Session identifier
            builder: Updated DPDABuilder instance

        Returns:
            True if updated successfully, False if not found
        """
        record = self.db.query(DPDARecord).filter_by(
            id=dpda_id,
            session_id=session_id
        ).first()

        if record is None:
            return False

        # Update builder JSON
        record.builder_json = json.dumps(builder.to_dict())
        record.last_accessed_at = datetime.now(timezone.utc)

        self.db.commit()
        return True

    def delete_dpda(self, dpda_id: str, session_id: str) -> bool:
        """
        Delete a DPDA.

        Args:
            dpda_id: DPDA identifier
            session_id: Session identifier

        Returns:
            True if deleted successfully, False if not found
        """
        record = self.db.query(DPDARecord).filter_by(
            id=dpda_id,
            session_id=session_id
        ).first()

        if record is None:
            return False

        self.db.delete(record)
        self.db.commit()
        return True

    def dpda_exists(self, dpda_id: str, session_id: str) -> bool:
        """
        Check if a DPDA exists.

        Args:
            dpda_id: DPDA identifier
            session_id: Session identifier

        Returns:
            True if exists, False otherwise
        """
        count = self.db.query(DPDARecord).filter_by(
            id=dpda_id,
            session_id=session_id
        ).count()
        return count > 0

    def update_last_accessed(self, dpda_id: str, session_id: str) -> bool:
        """
        Update the last_accessed_at timestamp for a DPDA.

        Args:
            dpda_id: DPDA identifier
            session_id: Session identifier

        Returns:
            True if updated, False if not found
        """
        record = self.db.query(DPDARecord).filter_by(
            id=dpda_id,
            session_id=session_id
        ).first()

        if record is None:
            return False

        record.last_accessed_at = datetime.now(timezone.utc)
        self.db.commit()
        return True

    def count_dpdas(self, session_id: str) -> int:
        """
        Count the number of DPDAs for a session.

        Args:
            session_id: Session identifier

        Returns:
            Number of DPDAs in the session
        """
        return self.db.query(DPDARecord).filter_by(
            session_id=session_id
        ).count()

    def get_dpda_name(self, dpda_id: str, session_id: str) -> Optional[str]:
        """
        Get just the name of a DPDA without loading full builder.

        Args:
            dpda_id: DPDA identifier
            session_id: Session identifier

        Returns:
            DPDA name if found, None otherwise
        """
        record = self.db.query(DPDARecord.name).filter_by(
            id=dpda_id,
            session_id=session_id
        ).first()

        return record.name if record else None

    def update_dpda_name(self, dpda_id: str, session_id: str, new_name: str) -> bool:
        """
        Update just the name of a DPDA.

        Args:
            dpda_id: DPDA identifier
            session_id: Session identifier
            new_name: New name for the DPDA

        Returns:
            True if updated, False if not found
        """
        record = self.db.query(DPDARecord).filter_by(
            id=dpda_id,
            session_id=session_id
        ).first()

        if record is None:
            return False

        record.name = new_name
        record.last_accessed_at = datetime.now(timezone.utc)
        self.db.commit()
        return True
