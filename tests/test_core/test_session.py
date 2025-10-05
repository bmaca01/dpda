"""
Tests for DPDA Session Management.
Following TDD - these tests are written before implementation.
"""

import pytest
import tempfile
import json
from pathlib import Path
from typing import Set

# These imports will fail initially (TDD Red phase)
from core.session import DPDASession, SessionError
from models.dpda_definition import DPDADefinition
from models.transition import Transition
from validation.dpda_validator import DPDAValidator


class TestDPDASession:
    """Test DPDA session management functionality."""

    def test_create_session(self):
        """Test basic session creation."""
        session = DPDASession("test_session")

        assert session.name == "test_session"
        assert session.current_dpda is None
        assert len(session.dpdas) == 0
        assert session.is_modified == False

    def test_create_new_dpda(self):
        """Test creating a new DPDA in the session."""
        session = DPDASession("test")

        session.new_dpda("dpda1")

        assert session.current_dpda_name == "dpda1"
        assert "dpda1" in session.dpdas
        assert session.current_dpda is not None
        assert session.is_modified == True

    def test_set_states(self):
        """Test setting states for current DPDA."""
        session = DPDASession("test")
        session.new_dpda("dpda1")

        states = {'q0', 'q1', 'q2'}
        session.set_states(states)

        builder = session.get_current_builder()
        assert builder.states == states
        assert session.is_modified == True

    def test_set_alphabets(self):
        """Test setting input and stack alphabets."""
        session = DPDASession("test")
        session.new_dpda("dpda1")

        input_alphabet = {'0', '1'}
        stack_alphabet = {'Z', 'X'}

        session.set_input_alphabet(input_alphabet)
        session.set_stack_alphabet(stack_alphabet)

        builder = session.get_current_builder()
        assert builder.input_alphabet == input_alphabet
        assert builder.stack_alphabet == stack_alphabet

    def test_set_initial_config(self):
        """Test setting initial state and stack symbol."""
        session = DPDASession("test")
        session.new_dpda("dpda1")
        session.set_states({'q0', 'q1'})
        session.set_stack_alphabet({'Z'})

        session.set_initial_state('q0')
        session.set_initial_stack_symbol('Z')

        builder = session.get_current_builder()
        assert builder.initial_state == 'q0'
        assert builder.initial_stack_symbol == 'Z'

    def test_set_accept_states(self):
        """Test setting accept states."""
        session = DPDASession("test")
        session.new_dpda("dpda1")
        session.set_states({'q0', 'q1', 'q2'})

        session.set_accept_states({'q2'})

        builder = session.get_current_builder()
        assert builder.accept_states == {'q2'}

    def test_add_transition(self):
        """Test adding transitions incrementally."""
        session = DPDASession("test")
        session.new_dpda("dpda1")
        session.set_states({'q0', 'q1'})
        session.set_input_alphabet({'a'})
        session.set_stack_alphabet({'Z'})

        session.add_transition('q0', 'a', 'Z', 'q1', 'Z')

        builder = session.get_current_builder()
        assert len(builder.transitions) == 1
        trans = builder.transitions[0]
        assert trans.from_state == 'q0'
        assert trans.input_symbol == 'a'
        assert trans.stack_top == 'Z'
        assert trans.to_state == 'q1'
        assert trans.stack_push == 'Z'

    def test_add_epsilon_transition(self):
        """Test adding epsilon transitions."""
        session = DPDASession("test")
        session.new_dpda("dpda1")
        session.set_states({'q0', 'q1'})
        session.set_stack_alphabet({'Z'})

        # Add epsilon transition (None for epsilon)
        session.add_transition('q0', None, 'Z', 'q1', 'Z')

        builder = session.get_current_builder()
        trans = builder.transitions[0]
        assert trans.input_symbol is None

    def test_remove_transition(self):
        """Test removing a transition."""
        session = DPDASession("test")
        session.new_dpda("dpda1")
        session.set_states({'q0', 'q1'})
        session.set_input_alphabet({'a'})
        session.set_stack_alphabet({'Z'})

        session.add_transition('q0', 'a', 'Z', 'q1', 'Z')
        session.add_transition('q1', 'a', 'Z', 'q0', 'Z')

        assert len(session.get_current_builder().transitions) == 2

        # Remove first transition
        session.remove_transition(0)

        builder = session.get_current_builder()
        assert len(builder.transitions) == 1
        assert builder.transitions[0].from_state == 'q1'

    def test_build_dpda(self):
        """Test building a complete DPDA from session."""
        session = DPDASession("test")
        session.new_dpda("dpda1")

        # Build a simple DPDA
        session.set_states({'q0', 'q1'})
        session.set_input_alphabet({'a'})
        session.set_stack_alphabet({'Z'})
        session.set_initial_state('q0')
        session.set_initial_stack_symbol('Z')
        session.set_accept_states({'q1'})
        session.add_transition('q0', 'a', 'Z', 'q1', 'Z')

        # Build the DPDA
        dpda = session.build_current_dpda()

        assert isinstance(dpda, DPDADefinition)
        assert dpda.states == {'q0', 'q1'}
        assert dpda.initial_state == 'q0'
        assert dpda.accept_states == {'q1'}
        assert len(dpda.transitions) == 1

    def test_validate_current_dpda(self):
        """Test validation of current DPDA being built."""
        session = DPDASession("test")
        session.new_dpda("dpda1")

        # Build a DPDA with validation issues
        session.set_states({'q0', 'q1'})
        session.set_input_alphabet({'a'})
        session.set_stack_alphabet({'Z'})
        session.set_initial_state('q0')
        session.set_initial_stack_symbol('Z')
        session.set_accept_states({'q1'})

        # Add conflicting transitions (violates determinism)
        session.add_transition('q0', 'a', 'Z', 'q1', 'Z')
        session.add_transition('q0', 'a', 'Z', 'q0', 'Z')  # Conflict!

        validation_result = session.validate_current()

        assert validation_result.is_valid == False
        assert len(validation_result.errors) > 0

    def test_multiple_dpdas(self):
        """Test managing multiple DPDAs in a session."""
        session = DPDASession("test")

        # Create first DPDA
        session.new_dpda("dpda1")
        session.set_states({'q0', 'q1'})
        session.set_initial_state('q0')

        # Create second DPDA
        session.new_dpda("dpda2")
        session.set_states({'p0', 'p1', 'p2'})
        session.set_initial_state('p0')

        # Check both exist
        assert "dpda1" in session.dpdas
        assert "dpda2" in session.dpdas
        assert session.current_dpda_name == "dpda2"

        # Switch back to first
        session.switch_to("dpda1")
        assert session.current_dpda_name == "dpda1"
        builder = session.get_current_builder()
        assert 'q0' in builder.states

    def test_delete_dpda(self):
        """Test deleting a DPDA from session."""
        session = DPDASession("test")

        session.new_dpda("dpda1")
        session.new_dpda("dpda2")
        session.new_dpda("dpda3")

        assert len(session.dpdas) == 3

        session.delete_dpda("dpda2")

        assert len(session.dpdas) == 2
        assert "dpda2" not in session.dpdas
        assert "dpda1" in session.dpdas
        assert "dpda3" in session.dpdas

    def test_rename_dpda(self):
        """Test renaming a DPDA."""
        session = DPDASession("test")

        session.new_dpda("old_name")
        session.set_states({'q0'})

        session.rename_dpda("old_name", "new_name")

        assert "old_name" not in session.dpdas
        assert "new_name" in session.dpdas
        assert session.current_dpda_name == "new_name"

    def test_save_session(self):
        """Test saving session to file."""
        session = DPDASession("test")

        # Create a DPDA
        session.new_dpda("dpda1")
        session.set_states({'q0', 'q1'})
        session.set_input_alphabet({'a'})
        session.set_stack_alphabet({'Z'})
        session.set_initial_state('q0')
        session.set_initial_stack_symbol('Z')
        session.set_accept_states({'q1'})
        session.add_transition('q0', 'a', 'Z', 'q1', 'Z')

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            filepath = f.name

        try:
            session.save_to_file(filepath)

            # Check file exists and contains session data
            assert Path(filepath).exists()

            with open(filepath, 'r') as f:
                data = json.load(f)
                assert 'session_name' in data
                assert 'dpdas' in data
                assert 'dpda1' in data['dpdas']
        finally:
            Path(filepath).unlink()

    def test_load_session(self):
        """Test loading session from file."""
        # Create and save a session
        session1 = DPDASession("original")
        session1.new_dpda("dpda1")
        session1.set_states({'q0', 'q1'})
        session1.set_input_alphabet({'a'})
        session1.set_stack_alphabet({'Z'})
        session1.set_initial_state('q0')
        session1.set_initial_stack_symbol('Z')
        session1.set_accept_states({'q1'})
        session1.add_transition('q0', 'a', 'Z', 'q1', 'Z')

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            filepath = f.name

        try:
            session1.save_to_file(filepath)

            # Load into new session
            session2 = DPDASession.load_from_file(filepath)

            assert session2.name == "original"
            assert "dpda1" in session2.dpdas

            # Build and verify DPDA
            session2.switch_to("dpda1")
            dpda = session2.build_current_dpda()
            assert dpda.states == {'q0', 'q1'}
            assert dpda.initial_state == 'q0'
        finally:
            Path(filepath).unlink()

    def test_session_with_serializer_integration(self):
        """Test that built DPDAs can be serialized."""
        from serialization.dpda_serializer import DPDASerializer

        session = DPDASession("test")
        session.new_dpda("dpda1")

        # Build a DPDA
        session.set_states({'q0', 'q1'})
        session.set_input_alphabet({'0', '1'})
        session.set_stack_alphabet({'Z', 'X'})
        session.set_initial_state('q0')
        session.set_initial_stack_symbol('Z')
        session.set_accept_states({'q1'})
        session.add_transition('q0', '0', 'Z', 'q0', 'X,Z')
        session.add_transition('q0', '1', 'X', 'q1', '')

        dpda = session.build_current_dpda()

        # Should be serializable
        serializer = DPDASerializer()
        json_str = serializer.to_json(dpda)
        loaded_dpda = serializer.from_json(json_str)

        assert loaded_dpda.states == dpda.states
        assert len(loaded_dpda.transitions) == len(dpda.transitions)

    def test_clear_current_dpda(self):
        """Test clearing the current DPDA builder."""
        session = DPDASession("test")
        session.new_dpda("dpda1")

        session.set_states({'q0', 'q1'})
        session.add_transition('q0', 'a', 'Z', 'q1', 'Z')

        session.clear_current()

        builder = session.get_current_builder()
        assert len(builder.states) == 0
        assert len(builder.transitions) == 0
        assert session.is_modified == True

    def test_copy_dpda(self):
        """Test copying a DPDA within session."""
        session = DPDASession("test")

        # Create original
        session.new_dpda("original")
        session.set_states({'q0', 'q1'})
        session.set_initial_state('q0')
        session.add_transition('q0', 'a', 'Z', 'q1', 'Z')

        # Copy it
        session.copy_dpda("original", "copy")

        assert "copy" in session.dpdas
        session.switch_to("copy")

        builder = session.get_current_builder()
        assert builder.states == {'q0', 'q1'}
        assert builder.initial_state == 'q0'
        assert len(builder.transitions) == 1

    def test_session_error_handling(self):
        """Test error handling in session operations."""
        session = DPDASession("test")

        # Try to get current builder when no DPDA exists
        with pytest.raises(SessionError, match="No current DPDA"):
            session.get_current_builder()

        # Try to switch to non-existent DPDA
        with pytest.raises(SessionError, match="not found"):
            session.switch_to("nonexistent")

        # Try to set invalid initial state
        session.new_dpda("dpda1")
        session.set_states({'q0'})
        with pytest.raises(SessionError, match="not in states"):
            session.set_initial_state('q99')

        # Try to add duplicate DPDA name
        with pytest.raises(SessionError, match="already exists"):
            session.new_dpda("dpda1")

    def test_get_dpda_list(self):
        """Test getting list of all DPDAs in session."""
        session = DPDASession("test")

        session.new_dpda("dpda1")
        session.new_dpda("dpda2")
        session.new_dpda("dpda3")

        dpda_list = session.get_dpda_list()

        assert len(dpda_list) == 3
        assert "dpda1" in dpda_list
        assert "dpda2" in dpda_list
        assert "dpda3" in dpda_list

    def test_modified_flag(self):
        """Test that modified flag is properly tracked."""
        session = DPDASession("test")

        assert session.is_modified == False

        session.new_dpda("dpda1")
        assert session.is_modified == True

        # Save should clear modified flag
        with tempfile.NamedTemporaryFile(suffix='.json', delete=True) as f:
            session.save_to_file(f.name)
            assert session.is_modified == False

        # Further changes should set it again
        session.set_states({'q0'})
        assert session.is_modified == True