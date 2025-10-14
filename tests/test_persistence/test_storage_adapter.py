"""Tests for storage adapter abstraction layer.

This module tests the StorageBackend interface and its implementations:
- MemoryStorage: In-memory storage (current implementation)
- DatabaseStorage: SQLite-backed persistent storage

The adapter pattern allows switching storage backends via configuration.
"""

import pytest
from core.session import DPDABuilder


class TestStorageBackendInterface:
    """Test that storage backends implement the required interface."""

    def test_memory_storage_implements_interface(self):
        """Memory storage should implement all required methods."""
        from persistence.storage_adapter import MemoryStorage

        storage = MemoryStorage()

        # Check all required methods exist
        assert hasattr(storage, 'create_dpda')
        assert hasattr(storage, 'get_dpda')
        assert hasattr(storage, 'list_dpdas')
        assert hasattr(storage, 'update_dpda')
        assert hasattr(storage, 'delete_dpda')
        assert hasattr(storage, 'exists')

    def test_database_storage_implements_interface(self):
        """Database storage should implement all required methods."""
        from persistence.storage_adapter import DatabaseStorage

        storage = DatabaseStorage()

        # Check all required methods exist
        assert hasattr(storage, 'create_dpda')
        assert hasattr(storage, 'get_dpda')
        assert hasattr(storage, 'list_dpdas')
        assert hasattr(storage, 'update_dpda')
        assert hasattr(storage, 'delete_dpda')
        assert hasattr(storage, 'exists')


class TestMemoryStorage:
    """Test in-memory storage implementation."""

    @pytest.fixture
    def storage(self):
        """Create memory storage instance."""
        from persistence.storage_adapter import MemoryStorage
        return MemoryStorage()

    @pytest.fixture
    def sample_builder(self):
        """Create sample DPDA builder."""
        builder = DPDABuilder()
        builder.states = {'q0', 'q1'}
        builder.initial_state = 'q0'
        builder.accept_states = {'q1'}
        builder.input_alphabet = {'a', 'b'}
        builder.stack_alphabet = {'$', 'X'}
        builder.initial_stack_symbol = '$'
        return builder

    def test_create_dpda_in_memory(self, storage, sample_builder):
        """Should create DPDA in memory storage."""
        dpda_id = storage.create_dpda(
            dpda_id='test-dpda',
            session_id='session-123',
            name='Test DPDA',
            builder=sample_builder
        )

        assert dpda_id == 'test-dpda'
        assert storage.exists('test-dpda', 'session-123')

    def test_get_dpda_from_memory(self, storage, sample_builder):
        """Should retrieve DPDA from memory storage."""
        storage.create_dpda('test-dpda', 'session-123', 'Test', sample_builder)

        result = storage.get_dpda('test-dpda', 'session-123')

        assert result is not None
        assert isinstance(result, DPDABuilder)
        assert result.initial_state == 'q0'

    def test_get_dpda_not_found_in_memory(self, storage):
        """Should return None for non-existent DPDA."""
        result = storage.get_dpda('nonexistent', 'session-123')
        assert result is None

    def test_get_dpda_wrong_session_in_memory(self, storage, sample_builder):
        """Should not retrieve DPDA from different session."""
        storage.create_dpda('test-dpda', 'session-123', 'Test', sample_builder)

        result = storage.get_dpda('test-dpda', 'session-456')
        assert result is None

    def test_list_dpdas_in_memory(self, storage, sample_builder):
        """Should list all DPDAs for a session."""
        storage.create_dpda('dpda-1', 'session-123', 'DPDA 1', sample_builder)
        storage.create_dpda('dpda-2', 'session-123', 'DPDA 2', sample_builder)
        storage.create_dpda('dpda-3', 'session-456', 'DPDA 3', sample_builder)

        dpdas = storage.list_dpdas('session-123')

        assert len(dpdas) == 2
        ids = [d['id'] for d in dpdas]
        assert 'dpda-1' in ids
        assert 'dpda-2' in ids
        assert 'dpda-3' not in ids

    def test_update_dpda_in_memory(self, storage, sample_builder):
        """Should update existing DPDA in memory."""
        storage.create_dpda('test-dpda', 'session-123', 'Original', sample_builder)

        # Modify builder
        sample_builder.states = {'q0', 'q1', 'q2'}

        success = storage.update_dpda('test-dpda', 'session-123', sample_builder)

        assert success is True
        result = storage.get_dpda('test-dpda', 'session-123')
        assert len(result.states) == 3

    def test_update_dpda_not_found_in_memory(self, storage, sample_builder):
        """Should return False when updating non-existent DPDA."""
        success = storage.update_dpda('nonexistent', 'session-123', sample_builder)
        assert success is False

    def test_delete_dpda_from_memory(self, storage, sample_builder):
        """Should delete DPDA from memory storage."""
        storage.create_dpda('test-dpda', 'session-123', 'Test', sample_builder)

        success = storage.delete_dpda('test-dpda', 'session-123')

        assert success is True
        assert not storage.exists('test-dpda', 'session-123')

    def test_delete_dpda_not_found_in_memory(self, storage):
        """Should return False when deleting non-existent DPDA."""
        success = storage.delete_dpda('nonexistent', 'session-123')
        assert success is False

    def test_exists_in_memory(self, storage, sample_builder):
        """Should check DPDA existence in memory."""
        assert not storage.exists('test-dpda', 'session-123')

        storage.create_dpda('test-dpda', 'session-123', 'Test', sample_builder)

        assert storage.exists('test-dpda', 'session-123')

    def test_session_isolation_in_memory(self, storage, sample_builder):
        """Should isolate DPDAs by session in memory."""
        storage.create_dpda('same-id', 'session-123', 'Session 1', sample_builder)
        storage.create_dpda('same-id', 'session-456', 'Session 2', sample_builder)

        # Both should exist in their own sessions
        assert storage.exists('same-id', 'session-123')
        assert storage.exists('same-id', 'session-456')

        # But they should be separate
        dpda1 = storage.get_dpda('same-id', 'session-123')
        dpda2 = storage.get_dpda('same-id', 'session-456')

        # They should be different instances (can modify one without affecting other)
        assert dpda1 is not dpda2


class TestDatabaseStorage:
    """Test database-backed storage implementation."""

    @pytest.fixture
    def storage(self):
        """Create database storage instance with test database."""
        from persistence.storage_adapter import DatabaseStorage
        from persistence.database import init_db, Base, engine

        # Initialize database and clean up any existing data
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

        # Yield storage for test
        yield DatabaseStorage()

        # Cleanup: drop all tables after test
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

    @pytest.fixture
    def sample_builder(self):
        """Create sample DPDA builder."""
        builder = DPDABuilder()
        builder.states = {'q0', 'q1'}
        builder.initial_state = 'q0'
        builder.accept_states = {'q1'}
        builder.input_alphabet = {'a', 'b'}
        builder.stack_alphabet = {'$', 'X'}
        builder.initial_stack_symbol = '$'
        return builder

    def test_create_dpda_in_database(self, storage, sample_builder):
        """Should create DPDA in database storage."""
        dpda_id = storage.create_dpda(
            dpda_id='test-dpda',
            session_id='session-123',
            name='Test DPDA',
            builder=sample_builder
        )

        assert dpda_id == 'test-dpda'
        assert storage.exists('test-dpda', 'session-123')

    def test_get_dpda_from_database(self, storage, sample_builder):
        """Should retrieve DPDA from database storage."""
        storage.create_dpda('test-dpda', 'session-123', 'Test', sample_builder)

        result = storage.get_dpda('test-dpda', 'session-123')

        assert result is not None
        assert isinstance(result, DPDABuilder)
        assert result.initial_state == 'q0'

    def test_get_dpda_not_found_in_database(self, storage):
        """Should return None for non-existent DPDA."""
        result = storage.get_dpda('nonexistent', 'session-123')
        assert result is None

    def test_get_dpda_wrong_session_in_database(self, storage, sample_builder):
        """Should not retrieve DPDA from different session."""
        storage.create_dpda('test-dpda', 'session-123', 'Test', sample_builder)

        result = storage.get_dpda('test-dpda', 'session-456')
        assert result is None

    def test_list_dpdas_in_database(self, storage, sample_builder):
        """Should list all DPDAs for a session from database."""
        storage.create_dpda('dpda-1', 'session-123', 'DPDA 1', sample_builder)
        storage.create_dpda('dpda-2', 'session-123', 'DPDA 2', sample_builder)
        storage.create_dpda('dpda-3', 'session-456', 'DPDA 3', sample_builder)

        dpdas = storage.list_dpdas('session-123')

        assert len(dpdas) == 2
        ids = [d['id'] for d in dpdas]
        assert 'dpda-1' in ids
        assert 'dpda-2' in ids
        assert 'dpda-3' not in ids

    def test_update_dpda_in_database(self, storage, sample_builder):
        """Should update existing DPDA in database."""
        storage.create_dpda('test-dpda', 'session-123', 'Original', sample_builder)

        # Modify builder
        sample_builder.states = {'q0', 'q1', 'q2'}

        success = storage.update_dpda('test-dpda', 'session-123', sample_builder)

        assert success is True
        result = storage.get_dpda('test-dpda', 'session-123')
        assert len(result.states) == 3

    def test_update_dpda_not_found_in_database(self, storage, sample_builder):
        """Should return False when updating non-existent DPDA."""
        success = storage.update_dpda('nonexistent', 'session-123', sample_builder)
        assert success is False

    def test_delete_dpda_from_database(self, storage, sample_builder):
        """Should delete DPDA from database storage."""
        storage.create_dpda('test-dpda', 'session-123', 'Test', sample_builder)

        success = storage.delete_dpda('test-dpda', 'session-123')

        assert success is True
        assert not storage.exists('test-dpda', 'session-123')

    def test_delete_dpda_not_found_in_database(self, storage):
        """Should return False when deleting non-existent DPDA."""
        success = storage.delete_dpda('nonexistent', 'session-123')
        assert success is False

    def test_exists_in_database(self, storage, sample_builder):
        """Should check DPDA existence in database."""
        assert not storage.exists('test-dpda', 'session-123')

        storage.create_dpda('test-dpda', 'session-123', 'Test', sample_builder)

        assert storage.exists('test-dpda', 'session-123')

    def test_session_isolation_in_database(self, storage, sample_builder):
        """Should isolate DPDAs by session in database."""
        storage.create_dpda('same-id', 'session-123', 'Session 1', sample_builder)
        storage.create_dpda('same-id', 'session-456', 'Session 2', sample_builder)

        # Both should exist in their own sessions
        assert storage.exists('same-id', 'session-123')
        assert storage.exists('same-id', 'session-456')


class TestStorageBackendFactory:
    """Test storage backend factory pattern."""

    def test_get_storage_memory_backend(self):
        """Should return memory storage when configured."""
        from persistence.storage_adapter import get_storage_backend

        storage = get_storage_backend('memory')

        assert storage.__class__.__name__ == 'MemoryStorage'

    def test_get_storage_database_backend(self):
        """Should return database storage when configured."""
        from persistence.storage_adapter import get_storage_backend
        from persistence.database import init_db

        # Initialize test database
        init_db()

        storage = get_storage_backend('database')

        assert storage.__class__.__name__ == 'DatabaseStorage'

    def test_get_storage_default_is_memory(self, monkeypatch):
        """Should default to memory storage when not configured."""
        from persistence.storage_adapter import get_storage_backend

        # Clear environment variable to test default behavior
        monkeypatch.delenv('STORAGE_BACKEND', raising=False)

        storage = get_storage_backend()

        assert storage.__class__.__name__ == 'MemoryStorage'

    def test_get_storage_invalid_backend_raises_error(self):
        """Should raise error for invalid backend type."""
        from persistence.storage_adapter import get_storage_backend

        with pytest.raises(ValueError, match="Invalid storage backend"):
            get_storage_backend('invalid')


class TestStorageBackendConfiguration:
    """Test storage backend configuration from environment."""

    def test_storage_backend_from_env_variable(self, monkeypatch):
        """Should read storage backend from STORAGE_BACKEND env var."""
        from persistence.storage_adapter import get_storage_backend

        monkeypatch.setenv('STORAGE_BACKEND', 'memory')
        storage = get_storage_backend()
        assert storage.__class__.__name__ == 'MemoryStorage'

    def test_storage_backend_env_override(self, monkeypatch):
        """Should allow explicit override of env variable."""
        from persistence.storage_adapter import get_storage_backend

        monkeypatch.setenv('STORAGE_BACKEND', 'database')

        # Explicit parameter should override env var
        storage = get_storage_backend('memory')
        assert storage.__class__.__name__ == 'MemoryStorage'
