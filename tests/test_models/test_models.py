"""
Test suite for DPDA model classes.
Following TDD, these tests define the expected behavior of our data models.
"""

import pytest
from typing import Set, Optional

# These imports will fail initially (RED phase of TDD)
from models.dpda_definition import DPDADefinition
from models.transition import Transition
from models.configuration import Configuration
from models.computation_result import ComputationResult


class TestTransition:
    """Test the Transition model class."""

    def test_transition_creation(self):
        """Test creating a transition."""
        trans = Transition('q0', '0', 'Z', 'q1', 'XZ')

        assert trans.from_state == 'q0'
        assert trans.input_symbol == '0'
        assert trans.stack_top == 'Z'
        assert trans.to_state == 'q1'
        assert trans.stack_push == 'XZ'

    def test_epsilon_transition(self):
        """Test epsilon transition (None input)."""
        trans = Transition('q0', None, 'Z', 'q1', 'Z')

        assert trans.input_symbol is None
        assert trans.is_epsilon is True

    def test_transition_equality(self):
        """Test transition equality comparison."""
        trans1 = Transition('q0', '0', 'Z', 'q1', 'XZ')
        trans2 = Transition('q0', '0', 'Z', 'q1', 'XZ')
        trans3 = Transition('q0', '1', 'Z', 'q1', 'XZ')

        assert trans1 == trans2
        assert trans1 != trans3

    def test_transition_string_representation(self):
        """Test string representation for debugging."""
        trans = Transition('q0', '0', 'Z', 'q1', 'XZ')
        str_repr = str(trans)

        assert 'q0' in str_repr
        assert 'q1' in str_repr
        assert '0' in str_repr
        assert 'Z' in str_repr
        assert 'XZ' in str_repr

    def test_pop_operation(self):
        """Test that empty stack_push means pop."""
        trans = Transition('q0', '1', 'X', 'q1', '')

        assert trans.stack_push == ''
        assert trans.is_pop_operation is True


class TestConfiguration:
    """Test the Configuration model class."""

    def test_configuration_creation(self):
        """Test creating a configuration."""
        config = Configuration('q0', '0011', 'Z')

        assert config.state == 'q0'
        assert config.remaining_input == '0011'
        assert config.stack == ['Z']  # Stack is now a list

    def test_empty_input_configuration(self):
        """Test configuration with empty input."""
        config = Configuration('q1', '', 'XZ')

        assert config.remaining_input == ''
        assert config.has_input is False

    def test_configuration_equality(self):
        """Test configuration equality."""
        config1 = Configuration('q0', '01', 'Z')
        config2 = Configuration('q0', '01', 'Z')
        config3 = Configuration('q1', '01', 'Z')

        assert config1 == config2
        assert config1 != config3

    def test_configuration_next_symbol(self):
        """Test getting next input symbol."""
        config = Configuration('q0', '0011', 'Z')

        assert config.next_input_symbol == '0'

        config_empty = Configuration('q0', '', 'Z')
        assert config_empty.next_input_symbol is None

    def test_configuration_stack_top(self):
        """Test getting stack top."""
        config = Configuration('q0', '01', 'XYZ')

        assert config.stack_top == 'X'

        # Empty stack case
        config_empty = Configuration('q0', '01', '')
        assert config_empty.stack_top is None

    def test_configuration_string_representation(self):
        """Test string representation for trace output."""
        config = Configuration('q0', '0011', 'XZ')
        str_repr = str(config)

        # Should show in format: (state, remaining_input, stack)
        assert 'q0' in str_repr
        assert '0011' in str_repr
        assert 'XZ' in str_repr


class TestDPDADefinition:
    """Test the DPDADefinition model class."""

    def test_dpda_creation(self):
        """Test creating a DPDA definition."""
        transitions = [
            Transition('q0', '0', 'Z', 'q1', 'XZ'),
            Transition('q1', '1', 'X', 'q1', ''),
        ]

        dpda = DPDADefinition(
            states={'q0', 'q1', 'q2'},
            input_alphabet={'0', '1'},
            stack_alphabet={'Z', 'X'},
            initial_state='q0',
            initial_stack_symbol='Z',
            accept_states={'q2'},
            transitions=transitions
        )

        assert dpda.states == {'q0', 'q1', 'q2'}
        assert dpda.input_alphabet == {'0', '1'}
        assert dpda.initial_state == 'q0'
        assert len(dpda.transitions) == 2

    def test_dpda_validation_states(self):
        """Test that DPDA validates states are consistent."""
        with pytest.raises(ValueError, match="Initial state"):
            DPDADefinition(
                states={'q1', 'q2'},
                input_alphabet={'0'},
                stack_alphabet={'Z'},
                initial_state='q0',  # Not in states
                initial_stack_symbol='Z',
                accept_states={'q2'},
                transitions=[]
            )

    def test_dpda_validation_accept_states(self):
        """Test that DPDA validates accept states."""
        with pytest.raises(ValueError, match="Accept state"):
            DPDADefinition(
                states={'q0', 'q1'},
                input_alphabet={'0'},
                stack_alphabet={'Z'},
                initial_state='q0',
                initial_stack_symbol='Z',
                accept_states={'q2'},  # Not in states
                transitions=[]
            )

    def test_dpda_validation_stack_symbol(self):
        """Test that DPDA validates initial stack symbol."""
        with pytest.raises(ValueError, match="Initial stack symbol"):
            DPDADefinition(
                states={'q0'},
                input_alphabet={'0'},
                stack_alphabet={'X'},
                initial_state='q0',
                initial_stack_symbol='Z',  # Not in stack alphabet
                accept_states=set(),
                transitions=[]
            )

    def test_dpda_get_transition(self):
        """Test finding applicable transition."""
        transitions = [
            Transition('q0', '0', 'Z', 'q1', 'XZ'),
            Transition('q0', '1', 'Z', 'q2', 'Z'),
        ]

        dpda = DPDADefinition(
            states={'q0', 'q1', 'q2'},
            input_alphabet={'0', '1'},
            stack_alphabet={'Z', 'X'},
            initial_state='q0',
            initial_stack_symbol='Z',
            accept_states={'q2'},
            transitions=transitions
        )

        # Should find transition for (q0, 0, Z)
        trans = dpda.get_transition('q0', '0', 'Z')
        assert trans is not None
        assert trans.to_state == 'q1'

        # Should not find transition for (q1, 0, Z)
        trans = dpda.get_transition('q1', '0', 'Z')
        assert trans is None


class TestComputationResult:
    """Test the ComputationResult model class."""

    def test_accepted_result(self):
        """Test accepted computation result."""
        trace = [
            Configuration('q0', '01', 'Z'),
            Configuration('q1', '1', 'XZ'),
            Configuration('q2', '', 'Z'),
        ]

        result = ComputationResult(
            accepted=True,
            final_state='q2',
            trace=trace,
            steps_taken=3
        )

        assert result.accepted is True
        assert result.final_state == 'q2'
        assert len(result.trace) == 3
        assert result.steps_taken == 3

    def test_rejected_result(self):
        """Test rejected computation result."""
        trace = [
            Configuration('q0', '01', 'Z'),
            Configuration('q1', '1', 'XZ'),
        ]

        result = ComputationResult(
            accepted=False,
            final_state='q1',
            trace=trace,
            steps_taken=2,
            rejection_reason="No valid transition"
        )

        assert result.accepted is False
        assert result.rejection_reason == "No valid transition"

    def test_result_with_remaining_input(self):
        """Test result when input is not fully consumed."""
        trace = [
            Configuration('q0', '011', 'Z'),
            Configuration('q2', '11', 'Z'),  # Stopped with input remaining
        ]

        result = ComputationResult(
            accepted=False,
            final_state='q2',
            trace=trace,
            steps_taken=2,
            rejection_reason="Input not fully consumed"
        )

        assert result.accepted is False
        assert "Input not fully consumed" in result.rejection_reason