"""
Test suite for DPDA validation logic.
Tests the four properties that must hold for a valid DPDA:
(a) At most one transition per (state, input, stack) triple
(b) No epsilon and non-epsilon transitions from same (state, stack) pair
(c) Multiple epsilon transitions must have disjoint stack requirements
(d) Stack operations must use valid symbols
"""

import pytest
from typing import Set

# These imports will fail initially (RED phase of TDD)
from validation.dpda_validator import DPDAValidator, ValidationResult
from models.dpda_definition import DPDADefinition
from models.transition import Transition


class TestDPDAValidator:
    """Test the DPDA validation logic."""

    def setup_method(self):
        """Set up validator instance."""
        self.validator = DPDAValidator()

    def test_valid_dpda(self):
        """Test validation of a valid DPDA."""
        transitions = [
            Transition('q0', '0', 'Z', 'q0', 'X,Z'),  # Use comma-separated format
            Transition('q0', '0', 'X', 'q0', 'X,X'),  # Use comma-separated format
            Transition('q0', '1', 'X', 'q1', ''),
            Transition('q1', '1', 'X', 'q1', ''),
            Transition('q1', None, 'Z', 'q2', 'Z'),
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

        result = self.validator.validate(dpda)

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_property_a_violation(self):
        """Test detection of multiple transitions for same (state, input, stack)."""
        transitions = [
            Transition('q0', '0', 'Z', 'q1', 'X,Z'),  # Use comma-separated format
            Transition('q0', '0', 'Z', 'q2', 'Y,Z'),  # Violation! Same (state, input, stack)
        ]

        dpda = DPDADefinition(
            states={'q0', 'q1', 'q2'},
            input_alphabet={'0'},
            stack_alphabet={'Z', 'X', 'Y'},
            initial_state='q0',
            initial_stack_symbol='Z',
            accept_states={'q2'},
            transitions=transitions
        )

        result = self.validator.validate(dpda)

        assert result.is_valid is False
        assert any('property (a)' in error.lower() for error in result.errors)

    def test_property_b_violation(self):
        """Test detection of epsilon and non-epsilon from same (state, stack)."""
        transitions = [
            Transition('q0', '0', 'Z', 'q1', 'XZ'),
            Transition('q0', None, 'Z', 'q2', 'Z'),  # Violation!
        ]

        dpda = DPDADefinition(
            states={'q0', 'q1', 'q2'},
            input_alphabet={'0'},
            stack_alphabet={'Z', 'X'},
            initial_state='q0',
            initial_stack_symbol='Z',
            accept_states={'q2'},
            transitions=transitions
        )

        result = self.validator.validate(dpda)

        assert result.is_valid is False
        assert any('property (b)' in error.lower() for error in result.errors)

    def test_property_c_violation(self):
        """Test detection of multiple epsilon transitions with same stack top."""
        transitions = [
            Transition('q0', None, 'Z', 'q1', 'XZ'),
            Transition('q0', None, 'Z', 'q2', 'YZ'),  # Violation!
        ]

        dpda = DPDADefinition(
            states={'q0', 'q1', 'q2'},
            input_alphabet={'0'},
            stack_alphabet={'Z', 'X', 'Y'},
            initial_state='q0',
            initial_stack_symbol='Z',
            accept_states={'q2'},
            transitions=transitions
        )

        result = self.validator.validate(dpda)

        assert result.is_valid is False
        assert any('property (c)' in error.lower() for error in result.errors)

    def test_property_c_allowed_case(self):
        """Test that multiple epsilon transitions with different stack tops are allowed."""
        transitions = [
            Transition('q0', None, 'X', 'q1', ''),
            Transition('q0', None, 'Y', 'q2', ''),  # Different stack top - OK
        ]

        dpda = DPDADefinition(
            states={'q0', 'q1', 'q2'},
            input_alphabet={'0'},
            stack_alphabet={'Z', 'X', 'Y'},
            initial_state='q0',
            initial_stack_symbol='Z',
            accept_states={'q2'},
            transitions=transitions
        )

        result = self.validator.validate(dpda)

        assert result.is_valid is True

    def test_property_d_violation_input_symbol(self):
        """Test detection of invalid input symbol in transition."""
        transitions = [
            Transition('q0', '2', 'Z', 'q1', 'Z'),  # '2' not in input alphabet
        ]

        dpda = DPDADefinition(
            states={'q0', 'q1'},
            input_alphabet={'0', '1'},
            stack_alphabet={'Z'},
            initial_state='q0',
            initial_stack_symbol='Z',
            accept_states={'q1'},
            transitions=transitions
        )

        result = self.validator.validate(dpda)

        assert result.is_valid is False
        assert any('input symbol' in error.lower() for error in result.errors)

    def test_property_d_violation_stack_symbol(self):
        """Test detection of invalid stack symbol in transition."""
        transitions = [
            Transition('q0', '0', 'W', 'q1', 'Z'),  # 'W' not in stack alphabet
        ]

        dpda = DPDADefinition(
            states={'q0', 'q1'},
            input_alphabet={'0', '1'},
            stack_alphabet={'Z', 'X'},
            initial_state='q0',
            initial_stack_symbol='Z',
            accept_states={'q1'},
            transitions=transitions
        )

        result = self.validator.validate(dpda)

        assert result.is_valid is False
        assert any('stack symbol' in error.lower() for error in result.errors)

    def test_property_d_violation_push_symbols(self):
        """Test detection of invalid symbols in push operation."""
        transitions = [
            Transition('q0', '0', 'Z', 'q1', 'WZ'),  # 'WZ' as single symbol not in stack alphabet
        ]

        dpda = DPDADefinition(
            states={'q0', 'q1'},
            input_alphabet={'0', '1'},
            stack_alphabet={'Z', 'X'},  # 'WZ' not in alphabet
            initial_state='q0',
            initial_stack_symbol='Z',
            accept_states={'q1'},
            transitions=transitions
        )

        result = self.validator.validate(dpda)

        assert result.is_valid is False
        assert any('push' in error.lower() for error in result.errors)

    def test_property_d_violation_state(self):
        """Test detection of invalid state in transition."""
        transitions = [
            Transition('q0', '0', 'Z', 'q3', 'Z'),  # 'q3' not in states
        ]

        dpda = DPDADefinition(
            states={'q0', 'q1'},
            input_alphabet={'0'},
            stack_alphabet={'Z'},
            initial_state='q0',
            initial_stack_symbol='Z',
            accept_states={'q1'},
            transitions=transitions
        )

        result = self.validator.validate(dpda)

        assert result.is_valid is False
        assert any('state' in error.lower() for error in result.errors)

    def test_multiple_violations(self):
        """Test detection of multiple violations."""
        transitions = [
            Transition('q0', '0', 'Z', 'q1', 'XZ'),
            Transition('q0', '0', 'Z', 'q2', 'YZ'),  # Property (a) violation
            Transition('q0', None, 'Z', 'q1', 'Z'),  # Property (b) violation
            Transition('q0', '2', 'X', 'q1', 'X'),   # Invalid input symbol
        ]

        dpda = DPDADefinition(
            states={'q0', 'q1', 'q2'},
            input_alphabet={'0', '1'},
            stack_alphabet={'Z', 'X', 'Y'},
            initial_state='q0',
            initial_stack_symbol='Z',
            accept_states={'q2'},
            transitions=transitions
        )

        result = self.validator.validate(dpda)

        assert result.is_valid is False
        assert len(result.errors) >= 3  # At least 3 violations

    def test_empty_dpda(self):
        """Test validation of DPDA with no transitions."""
        dpda = DPDADefinition(
            states={'q0'},
            input_alphabet={'0'},
            stack_alphabet={'Z'},
            initial_state='q0',
            initial_stack_symbol='Z',
            accept_states=set(),
            transitions=[]
        )

        result = self.validator.validate(dpda)

        assert result.is_valid is True  # Empty DPDA is technically valid

    def test_validation_result_details(self):
        """Test that validation result provides detailed information."""
        transitions = [
            Transition('q0', '0', 'Z', 'q1', 'XZ'),
            Transition('q0', '0', 'Z', 'q2', 'YZ'),  # Violation
        ]

        dpda = DPDADefinition(
            states={'q0', 'q1', 'q2'},
            input_alphabet={'0'},
            stack_alphabet={'Z', 'X', 'Y'},
            initial_state='q0',
            initial_stack_symbol='Z',
            accept_states={'q2'},
            transitions=transitions
        )

        result = self.validator.validate(dpda)

        assert result.is_valid is False
        assert len(result.errors) > 0
        # Error should mention the specific conflict
        assert any('q0' in error for error in result.errors)
        assert any('0' in error for error in result.errors)
        assert any('Z' in error for error in result.errors)