"""Tests for database models and operations."""

import pytest
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
import tempfile
import os

# These imports will fail initially (RED phase) - that's expected!
from persistence.database import DPDARecord, init_db, get_db, engine, Base
from core.session import DPDABuilder


class TestDatabaseSetup:
    """Test database initialization and connection."""

    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.db', delete=False) as f:
            db_path = f.name
        yield db_path
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)

    def test_init_db_creates_tables(self, temp_db_path):
        """Test that init_db creates all required tables."""
        # Set database URL for testing
        os.environ['DATABASE_URL'] = f'sqlite:///{temp_db_path}'

        # Initialize database
        init_db()

        # Verify tables exist by checking metadata
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        assert 'dpda_records' in tables

    def test_get_db_returns_session(self):
        """Test that get_db returns a valid database session."""
        db = next(get_db())
        assert db is not None
        db.close()


class TestDPDARecordModel:
    """Test the DPDARecord SQLAlchemy model."""

    @pytest.fixture(autouse=True)
    def setup_db(self):
        """Setup test database before each test."""
        # Use in-memory SQLite for tests
        os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
        init_db()
        yield
        # Cleanup
        Base.metadata.drop_all(bind=engine)

    @pytest.fixture
    def db_session(self):
        """Create a database session for testing."""
        db = next(get_db())
        yield db
        db.close()

    @pytest.fixture
    def sample_builder(self):
        """Create a sample DPDABuilder for testing."""
        builder = DPDABuilder()
        builder.states = {'q0', 'q1', 'q2'}
        builder.input_alphabet = {'0', '1'}
        builder.stack_alphabet = {'X', 'Z'}
        builder.initial_state = 'q0'
        builder.initial_stack_symbol = 'Z'
        builder.accept_states = {'q2'}
        return builder

    def test_dpda_record_creation(self, db_session, sample_builder):
        """Test creating a DPDA record."""
        record = DPDARecord(
            id='test-dpda-1',
            session_id='session-123',
            name='Test DPDA',
            builder_json=json.dumps(sample_builder.to_dict())
        )

        db_session.add(record)
        db_session.commit()

        # Verify record was created
        fetched = db_session.query(DPDARecord).filter_by(id='test-dpda-1').first()
        assert fetched is not None
        assert fetched.session_id == 'session-123'
        assert fetched.name == 'Test DPDA'

    def test_dpda_record_timestamps(self, db_session, sample_builder):
        """Test that timestamps are automatically set."""
        record = DPDARecord(
            id='test-dpda-2',
            session_id='session-123',
            name='Test DPDA',
            builder_json=json.dumps(sample_builder.to_dict())
        )

        db_session.add(record)
        db_session.commit()

        fetched = db_session.query(DPDARecord).filter_by(id='test-dpda-2').first()
        assert fetched.created_at is not None
        assert fetched.last_accessed_at is not None
        assert isinstance(fetched.created_at, datetime)
        assert isinstance(fetched.last_accessed_at, datetime)

    def test_dpda_record_json_storage(self, db_session, sample_builder):
        """Test that builder JSON is stored and retrieved correctly."""
        record = DPDARecord(
            id='test-dpda-3',
            session_id='session-123',
            name='Test DPDA',
            builder_json=json.dumps(sample_builder.to_dict())
        )

        db_session.add(record)
        db_session.commit()

        # Fetch and deserialize
        fetched = db_session.query(DPDARecord).filter_by(id='test-dpda-3').first()
        builder_dict = json.loads(fetched.builder_json)
        restored_builder = DPDABuilder.from_dict(builder_dict)

        # Verify all fields match
        assert restored_builder.states == sample_builder.states
        assert restored_builder.input_alphabet == sample_builder.input_alphabet
        assert restored_builder.stack_alphabet == sample_builder.stack_alphabet
        assert restored_builder.initial_state == sample_builder.initial_state
        assert restored_builder.initial_stack_symbol == sample_builder.initial_stack_symbol
        assert restored_builder.accept_states == sample_builder.accept_states

    def test_session_id_filtering(self, db_session, sample_builder):
        """Test that DPDAs are properly filtered by session_id."""
        # Create DPDAs for different sessions
        record1 = DPDARecord(
            id='dpda-session1-a',
            session_id='session-111',
            name='Session 1 DPDA A',
            builder_json=json.dumps(sample_builder.to_dict())
        )
        record2 = DPDARecord(
            id='dpda-session1-b',
            session_id='session-111',
            name='Session 1 DPDA B',
            builder_json=json.dumps(sample_builder.to_dict())
        )
        record3 = DPDARecord(
            id='dpda-session2-a',
            session_id='session-222',
            name='Session 2 DPDA A',
            builder_json=json.dumps(sample_builder.to_dict())
        )

        db_session.add_all([record1, record2, record3])
        db_session.commit()

        # Query for session 1
        session1_dpdas = db_session.query(DPDARecord).filter_by(
            session_id='session-111'
        ).all()
        assert len(session1_dpdas) == 2
        assert all(r.session_id == 'session-111' for r in session1_dpdas)

        # Query for session 2
        session2_dpdas = db_session.query(DPDARecord).filter_by(
            session_id='session-222'
        ).all()
        assert len(session2_dpdas) == 1
        assert session2_dpdas[0].session_id == 'session-222'

    def test_composite_id_session_lookup(self, db_session, sample_builder):
        """Test looking up DPDA by both id and session_id."""
        # Create DPDA
        record = DPDARecord(
            id='shared-id',
            session_id='session-aaa',
            name='DPDA A',
            builder_json=json.dumps(sample_builder.to_dict())
        )
        db_session.add(record)
        db_session.commit()

        # Create another DPDA with same ID but different session (should be allowed)
        record2 = DPDARecord(
            id='shared-id',
            session_id='session-bbb',
            name='DPDA B',
            builder_json=json.dumps(sample_builder.to_dict())
        )
        db_session.add(record2)
        db_session.commit()

        # Query with both id and session_id
        found = db_session.query(DPDARecord).filter_by(
            id='shared-id',
            session_id='session-aaa'
        ).first()

        assert found is not None
        assert found.name == 'DPDA A'

        found2 = db_session.query(DPDARecord).filter_by(
            id='shared-id',
            session_id='session-bbb'
        ).first()

        assert found2 is not None
        assert found2.name == 'DPDA B'

    def test_update_last_accessed_timestamp(self, db_session, sample_builder):
        """Test that last_accessed_at can be updated."""
        # Create record
        record = DPDARecord(
            id='test-dpda-4',
            session_id='session-123',
            name='Test DPDA',
            builder_json=json.dumps(sample_builder.to_dict())
        )
        db_session.add(record)
        db_session.commit()

        original_time = record.last_accessed_at

        # Simulate time passing
        import time
        time.sleep(0.1)

        # Update timestamp
        record.last_accessed_at = datetime.now(timezone.utc)
        db_session.commit()

        # Verify timestamp changed
        fetched = db_session.query(DPDARecord).filter_by(id='test-dpda-4').first()
        assert fetched.last_accessed_at > original_time

    def test_delete_dpda_record(self, db_session, sample_builder):
        """Test deleting a DPDA record."""
        # Create record
        record = DPDARecord(
            id='test-dpda-5',
            session_id='session-123',
            name='Test DPDA',
            builder_json=json.dumps(sample_builder.to_dict())
        )
        db_session.add(record)
        db_session.commit()

        # Delete record
        db_session.delete(record)
        db_session.commit()

        # Verify it's gone
        fetched = db_session.query(DPDARecord).filter_by(id='test-dpda-5').first()
        assert fetched is None

    def test_unique_constraint_on_id_and_session(self, db_session, sample_builder):
        """Test that (id, session_id) pairs must be unique."""
        # Create first record
        record1 = DPDARecord(
            id='duplicate-test',
            session_id='session-xyz',
            name='First',
            builder_json=json.dumps(sample_builder.to_dict())
        )
        db_session.add(record1)
        db_session.commit()

        # Try to create duplicate (same id AND session_id)
        record2 = DPDARecord(
            id='duplicate-test',
            session_id='session-xyz',
            name='Second',
            builder_json=json.dumps(sample_builder.to_dict())
        )
        db_session.add(record2)

        # Should raise IntegrityError
        with pytest.raises(Exception):  # SQLAlchemy IntegrityError
            db_session.commit()

    def test_query_by_session_id_ordering(self, db_session, sample_builder):
        """Test that queries can be ordered by creation time."""
        # Create multiple DPDAs with slight time gaps
        import time
        for i in range(3):
            record = DPDARecord(
                id=f'dpda-{i}',
                session_id='session-999',
                name=f'DPDA {i}',
                builder_json=json.dumps(sample_builder.to_dict())
            )
            db_session.add(record)
            db_session.commit()
            if i < 2:
                time.sleep(0.05)  # Small delay

        # Query ordered by created_at
        dpdas = db_session.query(DPDARecord).filter_by(
            session_id='session-999'
        ).order_by(DPDARecord.created_at.asc()).all()

        assert len(dpdas) == 3
        assert dpdas[0].name == 'DPDA 0'
        assert dpdas[1].name == 'DPDA 1'
        assert dpdas[2].name == 'DPDA 2'

        # Verify ordering is correct
        assert dpdas[0].created_at <= dpdas[1].created_at <= dpdas[2].created_at
