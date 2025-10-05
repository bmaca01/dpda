"""
Test suite for the formatter module.
Following TDD, these tests are written before the implementation.
"""

import pytest
from typing import Optional, List

# These imports will fail initially (RED phase of TDD)
from cli_io.formatter import OutputFormatter
from models.transition import Transition
from models.configuration import Configuration


class TestOutputFormatter:
    """Test the output formatting functionality."""

    def setup_method(self):
        """Set up formatter for testing."""
        self.formatter = OutputFormatter()

    def test_format_transition_basic(self):
        """Test basic transition formatting."""
        # Normal transition: read 'a', pop 'X', push 'YZ'
        result = self.formatter.format_transition('a', 'X', 'YZ')
        assert result == "[a,X->YZ]"

    def test_format_transition_epsilon_input(self):
        """Test transition with epsilon input."""
        # Epsilon input should display as "eps"
        result = self.formatter.format_transition(None, 'X', 'Y')
        assert result == "[eps,X->Y]"

    def test_format_transition_epsilon_stack_top(self):
        """Test transition with epsilon stack top."""
        # Epsilon stack top should display as "eps"
        result = self.formatter.format_transition('a', None, 'XY')
        assert result == "[a,eps->XY]"

    def test_format_transition_epsilon_push(self):
        """Test transition with epsilon push (pop only)."""
        # Empty push should display as "eps"
        result = self.formatter.format_transition('a', 'X', '')
        assert result == "[a,X->eps]"

    def test_format_transition_all_epsilon(self):
        """Test transition with all epsilon."""
        result = self.formatter.format_transition(None, None, '')
        assert result == "[eps,eps->eps]"

    def test_format_configuration_basic(self):
        """Test basic configuration formatting."""
        # Stack 'XYZ' means X on top internally, displayed as ZYX (bottom first)
        config = Configuration('q0', 'abc', 'XYZ')
        result = self.formatter.format_configuration(config)
        assert result == "(q0;abc;ZYX)"

    def test_format_configuration_empty_input(self):
        """Test configuration with empty input."""
        # Stack 'XYZ' means X on top internally, displayed as ZYX (bottom first)
        config = Configuration('q1', '', 'XYZ')
        result = self.formatter.format_configuration(config)
        assert result == "(q1;eps;ZYX)"

    def test_format_configuration_empty_stack(self):
        """Test configuration with empty stack."""
        config = Configuration('q2', 'abc', '')
        result = self.formatter.format_configuration(config)
        assert result == "(q2;abc;eps)"

    def test_format_configuration_all_empty(self):
        """Test configuration with all empty."""
        config = Configuration('q0', '', '')
        result = self.formatter.format_configuration(config)
        assert result == "(q0;eps;eps)"

    def test_format_state_display(self):
        """Test state formatting for display."""
        # States are stored as strings but displayed with 'q' prefix if numeric
        assert self.formatter.format_state('0') == 'q0'
        assert self.formatter.format_state('1') == 'q1'
        assert self.formatter.format_state('10') == 'q10'
        assert self.formatter.format_state('q0') == 'q0'  # Already has prefix

    def test_format_computation_trace_accept(self):
        """Test formatting a complete computation trace that accepts."""
        configs = [
            Configuration('0', '0011', 'Z'),
            Configuration('0', '011', 'XZ'),
            Configuration('0', '11', 'XXZ'),
            Configuration('1', '1', 'XZ'),
            Configuration('1', '', 'Z'),
            Configuration('2', '', 'Z')
        ]

        transitions = [
            Transition('0', '0', 'Z', '0', 'XZ'),
            Transition('0', '0', 'X', '0', 'XX'),
            Transition('0', '1', 'X', '1', ''),
            Transition('1', '1', 'X', '1', ''),
            Transition('1', None, 'Z', '2', 'Z')
        ]

        result = self.formatter.format_computation_trace(configs, transitions, accepted=True)

        # Check that it starts with the initial configuration
        assert result.startswith("(q0;0011;Z)")

        # Check that it contains transition arrows
        assert "-->" in result

        # Check specific transitions appear
        assert "[0,Z->XZ]" in result
        assert "[eps,Z->Z]" in result

        # Check final configuration
        assert "(q2;eps;Z)" in result

    def test_format_computation_trace_reject(self):
        """Test formatting a computation trace that rejects."""
        configs = [
            Configuration('0', '01', 'Z'),
            Configuration('0', '1', 'XZ'),
            Configuration('1', '', 'Z')
        ]

        transitions = [
            Transition('0', '0', 'Z', '0', 'XZ'),
            Transition('0', '1', 'X', '1', '')
        ]

        result = self.formatter.format_computation_trace(configs, transitions, accepted=False)

        # Should contain configurations and transitions
        assert "(q0;01;Z)" in result
        assert "[0,Z->XZ]" in result
        assert "(q1;eps;Z)" in result

    def test_format_transition_from_tuple(self):
        """Test formatting transition from original tuple format."""
        # Original format: (input, stack_top, next_state, push_symbols, condition)
        # condition: 1=eps/eps, 2=eps/stack, 3=input/eps, 4=input/stack

        # Case 1: eps, eps
        tup = ('', '', 1, 'X', 1)
        result = self.formatter.format_transition_tuple(tup)
        assert result == "[eps,eps->X]"

        # Case 2: eps, stack
        tup = ('', 'Y', 1, 'X', 2)
        result = self.formatter.format_transition_tuple(tup)
        assert result == "[eps,Y->X]"

        # Case 3: input, eps
        tup = ('a', '', 1, 'X', 3)
        result = self.formatter.format_transition_tuple(tup)
        assert result == "[a,eps->X]"

        # Case 4: input, stack
        tup = ('a', 'Y', 1, 'XX', 4)
        result = self.formatter.format_transition_tuple(tup)
        assert result == "[a,Y->XX]"

    def test_format_stack_string(self):
        """Test stack formatting from string representation."""
        # Empty stack
        assert self.formatter.format_stack('') == 'eps'

        # Non-empty stack (displayed in reverse for original compatibility)
        assert self.formatter.format_stack('XYZ') == 'ZYX'
        assert self.formatter.format_stack('A') == 'A'

    def test_format_input_string(self):
        """Test input string formatting."""
        # Empty input
        assert self.formatter.format_input('') == 'eps'

        # Non-empty input
        assert self.formatter.format_input('abc') == 'abc'
        assert self.formatter.format_input('0011') == '0011'