"""
Tests for DPDA serialization module.
Following TDD - these tests are written before implementation.
"""

import pytest
import json
import tempfile
import os
from pathlib import Path

# These imports will fail initially (TDD Red phase)
from serialization.dpda_serializer import DPDASerializer
from models.dpda_definition import DPDADefinition
from models.transition import Transition


class TestDPDASerializer:
    """Test DPDA serialization and deserialization."""

    @pytest.fixture
    def simple_dpda(self):
        """Create a simple DPDA for testing."""
        states = {'q0', 'q1', 'q2'}
        input_alphabet = {'0', '1'}
        stack_alphabet = {'Z', 'X'}
        accept_states = {'q2'}

        transitions = [
            Transition('q0', '0', 'Z', 'q0', 'X,Z'),
            Transition('q0', '0', 'X', 'q0', 'X,X'),
            Transition('q0', '1', 'X', 'q1', ''),
            Transition('q1', '1', 'X', 'q1', ''),
            Transition('q1', None, 'Z', 'q2', 'Z'),
        ]

        return DPDADefinition(
            states=states,
            input_alphabet=input_alphabet,
            stack_alphabet=stack_alphabet,
            initial_state='q0',
            initial_stack_symbol='Z',
            accept_states=accept_states,
            transitions=transitions
        )

    @pytest.fixture
    def complex_dpda(self):
        """Create a more complex DPDA with epsilon transitions."""
        states = {'q0', 'q1', 'q2', 'q3'}
        input_alphabet = {'a', 'b', 'c'}
        stack_alphabet = {'Z', 'A', 'B'}
        accept_states = {'q3'}

        transitions = [
            # Various transition types
            Transition('q0', 'a', 'Z', 'q1', 'A,Z'),
            Transition('q1', 'b', 'A', 'q1', 'B,A'),
            Transition('q1', 'c', 'B', 'q2', ''),
            Transition('q2', None, 'A', 'q2', ''),  # Epsilon transition
            Transition('q2', None, 'Z', 'q3', 'Z'),
        ]

        return DPDADefinition(
            states=states,
            input_alphabet=input_alphabet,
            stack_alphabet=stack_alphabet,
            initial_state='q0',
            initial_stack_symbol='Z',
            accept_states=accept_states,
            transitions=transitions
        )

    def test_to_dict_basic(self, simple_dpda):
        """Test conversion of DPDA to dictionary format."""
        serializer = DPDASerializer()
        result = serializer.to_dict(simple_dpda)

        assert isinstance(result, dict)
        assert 'version' in result
        assert result['version'] == '1.0'
        assert 'dpda' in result

        dpda_dict = result['dpda']
        assert dpda_dict['states'] == ['q0', 'q1', 'q2']  # Sorted for consistency
        assert set(dpda_dict['input_alphabet']) == {'0', '1'}
        assert set(dpda_dict['stack_alphabet']) == {'Z', 'X'}
        assert dpda_dict['initial_state'] == 'q0'
        assert dpda_dict['initial_stack_symbol'] == 'Z'
        assert dpda_dict['accept_states'] == ['q2']
        assert 'transitions' in dpda_dict
        assert len(dpda_dict['transitions']) == 5

    def test_to_dict_transition_format(self, simple_dpda):
        """Test that transitions are properly formatted in dictionary."""
        serializer = DPDASerializer()
        result = serializer.to_dict(simple_dpda)

        transitions = result['dpda']['transitions']
        # Check first transition
        trans = transitions[0]
        assert 'from_state' in trans
        assert 'input_symbol' in trans
        assert 'stack_top' in trans
        assert 'to_state' in trans
        assert 'stack_push' in trans

        # Check epsilon representation
        epsilon_trans = next(t for t in transitions if t['from_state'] == 'q1' and t['to_state'] == 'q2')
        assert epsilon_trans['input_symbol'] is None  # Epsilon as None

    def test_from_dict_basic(self, simple_dpda):
        """Test recreation of DPDA from dictionary."""
        serializer = DPDASerializer()
        dpda_dict = serializer.to_dict(simple_dpda)

        reconstructed = serializer.from_dict(dpda_dict)

        assert isinstance(reconstructed, DPDADefinition)
        assert reconstructed.states == simple_dpda.states
        assert reconstructed.input_alphabet == simple_dpda.input_alphabet
        assert reconstructed.stack_alphabet == simple_dpda.stack_alphabet
        assert reconstructed.initial_state == simple_dpda.initial_state
        assert reconstructed.initial_stack_symbol == simple_dpda.initial_stack_symbol
        assert reconstructed.accept_states == simple_dpda.accept_states

    def test_round_trip_consistency(self, simple_dpda, complex_dpda):
        """Test that DPDA survives serialization round-trip."""
        serializer = DPDASerializer()

        for dpda in [simple_dpda, complex_dpda]:
            # Serialize and deserialize
            dict_form = serializer.to_dict(dpda)
            reconstructed = serializer.from_dict(dict_form)

            # Check equality of all components
            assert reconstructed.states == dpda.states
            assert reconstructed.input_alphabet == dpda.input_alphabet
            assert reconstructed.stack_alphabet == dpda.stack_alphabet
            assert reconstructed.initial_state == dpda.initial_state
            assert reconstructed.initial_stack_symbol == dpda.initial_stack_symbol
            assert reconstructed.accept_states == dpda.accept_states
            assert len(reconstructed.transitions) == len(dpda.transitions)

    def test_to_json(self, simple_dpda):
        """Test JSON export functionality."""
        serializer = DPDASerializer()
        json_str = serializer.to_json(simple_dpda)

        assert isinstance(json_str, str)
        # Should be valid JSON
        parsed = json.loads(json_str)
        assert 'version' in parsed
        assert 'dpda' in parsed

    def test_from_json(self, simple_dpda):
        """Test JSON import functionality."""
        serializer = DPDASerializer()
        json_str = serializer.to_json(simple_dpda)

        reconstructed = serializer.from_json(json_str)

        assert isinstance(reconstructed, DPDADefinition)
        assert reconstructed.states == simple_dpda.states

    def test_json_round_trip(self, complex_dpda):
        """Test complete JSON round-trip."""
        serializer = DPDASerializer()

        json_str = serializer.to_json(complex_dpda)
        reconstructed = serializer.from_json(json_str)

        assert reconstructed.states == complex_dpda.states
        assert reconstructed.input_alphabet == complex_dpda.input_alphabet
        assert len(reconstructed.transitions) == len(complex_dpda.transitions)

    def test_save_to_file(self, simple_dpda):
        """Test saving DPDA to file."""
        serializer = DPDASerializer()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            filepath = f.name

        try:
            serializer.save_to_file(simple_dpda, filepath)

            assert os.path.exists(filepath)
            with open(filepath, 'r') as f:
                content = json.load(f)
                assert 'version' in content
                assert 'dpda' in content
        finally:
            os.unlink(filepath)

    def test_load_from_file(self, complex_dpda):
        """Test loading DPDA from file."""
        serializer = DPDASerializer()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            filepath = f.name

        try:
            serializer.save_to_file(complex_dpda, filepath)
            loaded = serializer.load_from_file(filepath)

            assert isinstance(loaded, DPDADefinition)
            assert loaded.states == complex_dpda.states
            assert len(loaded.transitions) == len(complex_dpda.transitions)
        finally:
            os.unlink(filepath)

    def test_file_round_trip(self, simple_dpda):
        """Test complete file save/load round-trip."""
        serializer = DPDASerializer()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            filepath = f.name

        try:
            serializer.save_to_file(simple_dpda, filepath)
            loaded = serializer.load_from_file(filepath)

            assert loaded.states == simple_dpda.states
            assert loaded.input_alphabet == simple_dpda.input_alphabet
            assert loaded.stack_alphabet == simple_dpda.stack_alphabet
            assert loaded.initial_state == simple_dpda.initial_state
            assert loaded.accept_states == simple_dpda.accept_states
        finally:
            os.unlink(filepath)

    def test_empty_dpda_serialization(self):
        """Test serialization of DPDA with minimal components."""
        # Minimal valid DPDA
        dpda = DPDADefinition(
            states={'q0'},
            input_alphabet=set(),
            stack_alphabet={'Z'},
            initial_state='q0',
            initial_stack_symbol='Z',
            accept_states=set(),
            transitions=[]
        )

        serializer = DPDASerializer()
        dict_form = serializer.to_dict(dpda)
        reconstructed = serializer.from_dict(dict_form)

        assert reconstructed.states == {'q0'}
        assert reconstructed.input_alphabet == set()
        assert reconstructed.transitions == []

    def test_version_tracking(self, simple_dpda):
        """Test that version is properly tracked."""
        serializer = DPDASerializer()
        result = serializer.to_dict(simple_dpda)

        assert 'version' in result
        assert result['version'] == '1.0'

        # Test with JSON
        json_str = serializer.to_json(simple_dpda)
        parsed = json.loads(json_str)
        assert parsed['version'] == '1.0'

    def test_invalid_json_handling(self):
        """Test handling of invalid JSON input."""
        serializer = DPDASerializer()

        with pytest.raises(ValueError, match="Invalid JSON"):
            serializer.from_json("not valid json {}")

        with pytest.raises(ValueError, match="Missing version"):
            serializer.from_json('{"dpda": {}}')

        with pytest.raises(ValueError, match="Missing dpda"):
            serializer.from_json('{"version": "1.0"}')

    def test_invalid_dict_handling(self):
        """Test handling of invalid dictionary input."""
        serializer = DPDASerializer()

        with pytest.raises(ValueError, match="Missing version"):
            serializer.from_dict({})

        with pytest.raises(ValueError, match="Missing dpda"):
            serializer.from_dict({"version": "1.0"})

        with pytest.raises(ValueError, match="Missing required field"):
            serializer.from_dict({
                "version": "1.0",
                "dpda": {"states": ["q0"]}  # Missing other required fields
            })

    def test_backward_compatibility_check(self):
        """Test version compatibility checking."""
        serializer = DPDASerializer()

        # Future version should raise warning or error
        future_dict = {
            "version": "2.0",
            "dpda": {
                "states": ["q0"],
                "input_alphabet": [],
                "stack_alphabet": ["Z"],
                "initial_state": "q0",
                "initial_stack_symbol": "Z",
                "accept_states": [],
                "transitions": []
            }
        }

        # Should handle gracefully or warn about version mismatch
        with pytest.raises(ValueError, match="Unsupported version"):
            serializer.from_dict(future_dict)