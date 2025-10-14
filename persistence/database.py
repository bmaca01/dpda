"""SQLAlchemy database models and configuration for DPDA persistence."""

import os
from datetime import datetime
from typing import Generator

from sqlalchemy import create_engine, Column, String, Text, DateTime, Index, func
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase

# Get database URL from environment or use default SQLite
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./dpda_sessions.db')

# Create engine with appropriate settings
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith('sqlite') else {},
    echo=False  # Set to True for SQL query logging
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base using SQLAlchemy 2.0 style
class Base(DeclarativeBase):
    pass


class DPDARecord(Base):
    """
    SQLAlchemy model for persisting DPDA state.

    Stores DPDA builder state as JSON, associated with a session_id for isolation.
    The (id, session_id) pair must be unique - same id can exist in different sessions.
    """
    __tablename__ = 'dpda_records'

    # Primary key is composite: (id, session_id)
    id = Column(String(100), primary_key=True, nullable=False)
    session_id = Column(String(100), primary_key=True, nullable=False)

    # DPDA metadata
    name = Column(String(200), nullable=False)

    # Serialized DPDABuilder as JSON
    builder_json = Column(Text, nullable=False)

    # Timestamps - using SQL func.now() for timezone-aware timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    last_accessed_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Create index for efficient session-based queries
    __table_args__ = (
        Index('idx_session_id', 'session_id'),
        Index('idx_session_id_created', 'session_id', 'created_at'),
    )

    def __repr__(self):
        return f"<DPDARecord(id='{self.id}', session_id='{self.session_id}', name='{self.name}')>"


def init_db() -> None:
    """
    Initialize database by creating all tables.

    This should be called once at application startup.
    """
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency that provides a database session.

    Yields:
        Session: SQLAlchemy database session

    Usage:
        db = next(get_db())
        # ... use db ...
        db.close()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def drop_all_tables() -> None:
    """
    Drop all tables from the database.

    WARNING: This will delete all data! Only use for testing or cleanup.
    """
    Base.metadata.drop_all(bind=engine)
