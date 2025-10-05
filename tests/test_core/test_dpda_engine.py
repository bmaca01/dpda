"""
Test suite for the core DPDA engine module.
Following TDD, these tests are written before the implementation.
"""

import pytest
from typing import Optional, Set, Tuple

# These imports will fail initially (RED phase of TDD)
from core.dpda_engine import DPDAEngine
from models.dpda_definition import DPDADefinition
from models.transition import Transition
from models.configuration import Configuration


class TestDPDAEngine:
    """Test the stateless DPDA computation engine."""

    def setup_method(self):
        """Set up a simple DPDA for testing: accepts {0^n 1^n | n >= 0}"""
        # Define states, alphabets, and transitions
        states = {'q0', 'q1', 'q2'}
        input_alphabet = {'0', '1'}
        stack_alphabet = {'Z', 'X'}
        accept_states = {'q2'}
        initial_state = 'q0'
        initial_stack = 'Z'

        # Transitions: (state, input, stack_top) -> (new_state, stack_operation)
        transitions = [
            Transition('q0', '0', 'Z', 'q0', 'X,Z'),  # Push X for each 0 (comma-separated)
            Transition('q0', '0', 'X', 'q0', 'X,X'),  # Continue pushing X (comma-separated)
            Transition('q0', '1', 'X', 'q1', ''),     # Start popping on 1
            Transition('q1', '1', 'X', 'q1', ''),     # Continue popping
            Transition('q1', None, 'Z', 'q2', 'Z'),   # Accept on epsilon with Z
        ]

        self.dpda = DPDADefinition(
            states=states,
            input_alphabet=input_alphabet,
            stack_alphabet=stack_alphabet,
            initial_state=initial_state,
            initial_stack_symbol=initial_stack,
            accept_states=accept_states,
            transitions=transitions
        )
        self.engine = DPDAEngine()

    def test_single_step_computation(self):
        """Test single-step transitions."""
        # Start configuration
        config = Configuration('q0', '0011', 'Z')

        # Execute one step
        next_config = self.engine.step(self.dpda, config)

        assert next_config is not None
        assert next_config.state == 'q0'
        assert next_config.remaining_input == '011'
        assert next_config.stack == ['X', 'Z']  # Stack is now a list

    def test_epsilon_transition(self):
        """Test epsilon transitions (None input)."""
        # Configuration ready for epsilon transition
        config = Configuration('q1', '', 'Z')

        # Should take epsilon transition to q2
        next_config = self.engine.step(self.dpda, config)

        assert next_config is not None
        assert next_config.state == 'q2'
        assert next_config.remaining_input == ''
        assert next_config.stack == ['Z']  # Stack is now a list

    def test_no_valid_transition(self):
        """Test when no valid transition exists."""
        # Configuration with no valid transition
        config = Configuration('q0', '1', 'Z')  # Can't read 1 in q0 with Z

        next_config = self.engine.step(self.dpda, config)

        assert next_config is None

    def test_compute_accepts_valid_string(self):
        """Test full computation on accepting string."""
        result = self.engine.compute(self.dpda, '0011')

        assert result.accepted is True
        assert result.final_state == 'q2'
        assert len(result.trace) > 0

    def test_compute_rejects_invalid_string(self):
        """Test full computation on rejecting string."""
        result = self.engine.compute(self.dpda, '001')  # Unbalanced

        assert result.accepted is False

    def test_empty_string_acceptance(self):
        """Test empty string acceptance (epsilon-only path)."""
        # Modify DPDA to accept empty string
        transitions = [
            Transition('q0', None, 'Z', 'q2', 'Z'),  # Direct epsilon to accept
        ]

        dpda = DPDADefinition(
            states={'q0', 'q2'},
            input_alphabet={'0', '1'},
            stack_alphabet={'Z'},
            initial_state='q0',
            initial_stack_symbol='Z',
            accept_states={'q2'},
            transitions=transitions
        )

        result = self.engine.compute(dpda, '')
        assert result.accepted is True

    def test_stack_operations(self):
        """Test various stack operations."""
        # Test push operation
        config = Configuration('q0', '0', 'Z')
        next_config = self.engine.step(self.dpda, config)
        assert next_config.stack == ['X', 'Z']  # Stack is now a list

        # Test pop operation (empty string means pop)
        config = Configuration('q1', '1', 'X')
        next_config = self.engine.step(self.dpda, config)
        assert next_config.stack == []  # X was popped, nothing remains (empty list)

    def test_determinism_preserved(self):
        """Test that computation is deterministic."""
        # Run same computation twice
        result1 = self.engine.compute(self.dpda, '0011')
        result2 = self.engine.compute(self.dpda, '0011')

        # Should produce identical results
        assert result1.accepted == result2.accepted
        assert result1.final_state == result2.final_state
        assert len(result1.trace) == len(result2.trace)

    def test_computation_trace(self):
        """Test that computation trace is properly recorded."""
        result = self.engine.compute(self.dpda, '01')

        # Should have a trace of configurations
        assert len(result.trace) > 0

        # First configuration should be initial
        assert result.trace[0].state == 'q0'
        assert result.trace[0].remaining_input == '01'
        assert result.trace[0].stack == ['Z']  # Stack is now a list

        # Last configuration should be final
        last = result.trace[-1]
        assert last.remaining_input == ''  # All input consumed

    def test_max_steps_limit(self):
        """Test that computation has a maximum step limit to prevent infinite loops."""
        # Create a DPDA with potential infinite loop
        transitions = [
            Transition('q0', None, 'Z', 'q0', 'XZ'),  # Infinite epsilon loop
        ]

        dpda = DPDADefinition(
            states={'q0'},
            input_alphabet={'0'},
            stack_alphabet={'Z', 'X'},
            initial_state='q0',
            initial_stack_symbol='Z',
            accept_states=set(),
            transitions=transitions
        )

        # Should terminate even with infinite loop
        result = self.engine.compute(dpda, '', max_steps=100)
        assert result.accepted is False
        assert len(result.trace) <= 100