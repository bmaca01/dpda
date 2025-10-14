"""Tests for repository pattern implementation."""

import pytest
import os
from datetime import datetime

# These imports will fail initially (RED phase)
from persistence.database import init_db, get_db, Base, engine
from persistence.repository import DPDARepository, RepositoryError
from core.session import DPDABuilder


class TestDPDARepository:
    """Test suite for DPDA repository operations."""

    @pytest.fixture(autouse=True)
    def setup_db(self):
        """Setup test database before each test."""
        os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
        init_db()
        yield
        Base.metadata.drop_all(bind=engine)

    @pytest.fixture
    def repository(self):
        """Create a repository instance for testing."""
        db = next(get_db())
        repo = DPDARepository(db)
        yield repo
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

    def test_create_dpda(self, repository, sample_builder):
        """Test creating a DPDA through the repository."""
        dpda_id = 'test-dpda-1'
        session_id = 'session-abc'
        name = 'Test DPDA'

        # Create DPDA
        created_id = repository.create_dpda(
            dpda_id=dpda_id,
            session_id=session_id,
            name=name,
            builder=sample_builder
        )

        assert created_id == dpda_id

    def test_get_dpda_exists(self, repository, sample_builder):
        """Test retrieving an existing DPDA."""
        dpda_id = 'test-dpda-2'
        session_id = 'session-abc'

        # Create DPDA
        repository.create_dpda(dpda_id, session_id, 'Test', sample_builder)

        # Retrieve DPDA
        builder = repository.get_dpda(dpda_id, session_id)

        assert builder is not None
        assert builder.states == sample_builder.states
        assert builder.input_alphabet == sample_builder.input_alphabet
        assert builder.initial_state == sample_builder.initial_state

    def test_get_dpda_not_found(self, repository):
        """Test retrieving a non-existent DPDA returns None."""
        builder = repository.get_dpda('nonexistent-id', 'session-abc')
        assert builder is None

    def test_get_dpda_wrong_session(self, repository, sample_builder):
        """Test that DPDA can't be accessed with wrong session_id."""
        dpda_id = 'test-dpda-3'
        session_id = 'session-correct'

        # Create DPDA with one session
        repository.create_dpda(dpda_id, session_id, 'Test', sample_builder)

        # Try to access with different session
        builder = repository.get_dpda(dpda_id, 'session-wrong')
        assert builder is None

    def test_list_dpdas_for_session(self, repository, sample_builder):
        """Test listing all DPDAs for a specific session."""
        session_id = 'session-list-test'

        # Create multiple DPDAs for this session
        repository.create_dpda('dpda-1', session_id, 'DPDA 1', sample_builder)
        repository.create_dpda('dpda-2', session_id, 'DPDA 2', sample_builder)
        repository.create_dpda('dpda-3', session_id, 'DPDA 3', sample_builder)

        # Create DPDA for different session
        repository.create_dpda('dpda-4', 'other-session', 'DPDA 4', sample_builder)

        # List DPDAs for our session
        dpdas = repository.list_dpdas(session_id)

        assert len(dpdas) == 3
        dpda_ids = [dpda['id'] for dpda in dpdas]
        assert 'dpda-1' in dpda_ids
        assert 'dpda-2' in dpda_ids
        assert 'dpda-3' in dpda_ids
        assert 'dpda-4' not in dpda_ids

    def test_list_dpdas_includes_metadata(self, repository, sample_builder):
        """Test that list_dpdas returns metadata about each DPDA."""
        session_id = 'session-metadata-test'

        repository.create_dpda('dpda-1', session_id, 'My DPDA', sample_builder)

        dpdas = repository.list_dpdas(session_id)

        assert len(dpdas) == 1
        dpda = dpdas[0]

        # Check metadata fields
        assert 'id' in dpda
        assert 'name' in dpda
        assert 'created_at' in dpda
        assert 'last_accessed_at' in dpda
        assert dpda['id'] == 'dpda-1'
        assert dpda['name'] == 'My DPDA'

    def test_update_dpda(self, repository, sample_builder):
        """Test updating an existing DPDA."""
        dpda_id = 'test-dpda-4'
        session_id = 'session-update'

        # Create initial DPDA
        repository.create_dpda(dpda_id, session_id, 'Original', sample_builder)

        # Modify builder
        modified_builder = sample_builder.copy()
        modified_builder.states.add('q3')

        # Update DPDA
        success = repository.update_dpda(dpda_id, session_id, modified_builder)
        assert success is True

        # Verify update
        retrieved = repository.get_dpda(dpda_id, session_id)
        assert 'q3' in retrieved.states

    def test_update_dpda_not_found(self, repository, sample_builder):
        """Test updating a non-existent DPDA returns False."""
        success = repository.update_dpda('nonexistent', 'session-x', sample_builder)
        assert success is False

    def test_update_dpda_wrong_session(self, repository, sample_builder):
        """Test updating DPDA with wrong session_id fails."""
        dpda_id = 'test-dpda-5'
        session_id = 'session-correct'

        # Create DPDA
        repository.create_dpda(dpda_id, session_id, 'Test', sample_builder)

        # Try to update with wrong session
        modified_builder = sample_builder.copy()
        success = repository.update_dpda(dpda_id, 'session-wrong', modified_builder)
        assert success is False

    def test_delete_dpda(self, repository, sample_builder):
        """Test deleting a DPDA."""
        dpda_id = 'test-dpda-6'
        session_id = 'session-delete'

        # Create DPDA
        repository.create_dpda(dpda_id, session_id, 'Test', sample_builder)

        # Delete DPDA
        success = repository.delete_dpda(dpda_id, session_id)
        assert success is True

        # Verify it's gone
        builder = repository.get_dpda(dpda_id, session_id)
        assert builder is None

    def test_delete_dpda_not_found(self, repository):
        """Test deleting a non-existent DPDA returns False."""
        success = repository.delete_dpda('nonexistent', 'session-x')
        assert success is False

    def test_delete_dpda_wrong_session(self, repository, sample_builder):
        """Test deleting DPDA with wrong session_id fails."""
        dpda_id = 'test-dpda-7'
        session_id = 'session-correct'

        # Create DPDA
        repository.create_dpda(dpda_id, session_id, 'Test', sample_builder)

        # Try to delete with wrong session
        success = repository.delete_dpda(dpda_id, 'session-wrong')
        assert success is False

        # Verify it still exists with correct session
        builder = repository.get_dpda(dpda_id, session_id)
        assert builder is not None

    def test_dpda_exists(self, repository, sample_builder):
        """Test checking if DPDA exists."""
        dpda_id = 'test-dpda-8'
        session_id = 'session-exists'

        # Should not exist initially
        assert repository.dpda_exists(dpda_id, session_id) is False

        # Create DPDA
        repository.create_dpda(dpda_id, session_id, 'Test', sample_builder)

        # Should now exist
        assert repository.dpda_exists(dpda_id, session_id) is True

        # Should not exist with wrong session
        assert repository.dpda_exists(dpda_id, 'wrong-session') is False

    def test_update_last_accessed(self, repository, sample_builder):
        """Test updating the last_accessed_at timestamp."""
        dpda_id = 'test-dpda-9'
        session_id = 'session-access'

        # Create DPDA
        repository.create_dpda(dpda_id, session_id, 'Test', sample_builder)

        # Get initial access time
        dpdas = repository.list_dpdas(session_id)
        initial_time = dpdas[0]['last_accessed_at']

        # Wait a bit
        import time
        time.sleep(0.1)

        # Update access time
        repository.update_last_accessed(dpda_id, session_id)

        # Verify it changed
        dpdas = repository.list_dpdas(session_id)
        new_time = dpdas[0]['last_accessed_at']
        assert new_time > initial_time

    def test_create_duplicate_dpda_raises_error(self, repository, sample_builder):
        """Test that creating duplicate DPDA raises error."""
        dpda_id = 'duplicate-id'
        session_id = 'session-dup'

        # Create first DPDA
        repository.create_dpda(dpda_id, session_id, 'First', sample_builder)

        # Try to create duplicate
        with pytest.raises(RepositoryError):
            repository.create_dpda(dpda_id, session_id, 'Second', sample_builder)

    def test_list_empty_session(self, repository):
        """Test listing DPDAs for a session with no DPDAs."""
        dpdas = repository.list_dpdas('empty-session')
        assert dpdas == []

    def test_count_dpdas_for_session(self, repository, sample_builder):
        """Test counting DPDAs for a specific session."""
        session_id = 'session-count'

        # Initially zero
        count = repository.count_dpdas(session_id)
        assert count == 0

        # Create DPDAs
        repository.create_dpda('dpda-1', session_id, 'DPDA 1', sample_builder)
        repository.create_dpda('dpda-2', session_id, 'DPDA 2', sample_builder)

        # Should be 2
        count = repository.count_dpdas(session_id)
        assert count == 2

    def test_get_dpda_name(self, repository, sample_builder):
        """Test getting just the name of a DPDA."""
        dpda_id = 'test-dpda-10'
        session_id = 'session-name'
        name = 'My Special DPDA'

        # Create DPDA
        repository.create_dpda(dpda_id, session_id, name, sample_builder)

        # Get name
        fetched_name = repository.get_dpda_name(dpda_id, session_id)
        assert fetched_name == name

    def test_get_dpda_name_not_found(self, repository):
        """Test getting name of non-existent DPDA returns None."""
        name = repository.get_dpda_name('nonexistent', 'session-x')
        assert name is None

    def test_update_dpda_name(self, repository, sample_builder):
        """Test updating just the name of a DPDA."""
        dpda_id = 'test-dpda-11'
        session_id = 'session-rename'

        # Create DPDA
        repository.create_dpda(dpda_id, session_id, 'Old Name', sample_builder)

        # Update name
        success = repository.update_dpda_name(dpda_id, session_id, 'New Name')
        assert success is True

        # Verify
        name = repository.get_dpda_name(dpda_id, session_id)
        assert name == 'New Name'
