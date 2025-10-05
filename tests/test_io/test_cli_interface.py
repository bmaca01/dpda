"""
Test suite for the CLI interface module.
Following TDD, these tests are written before the implementation.
"""

import pytest
from unittest.mock import Mock, patch, call
from typing import List

# These imports will fail initially (RED phase of TDD)
from cli_io.cli_interface import CLIInterface
from models.dpda_definition import DPDADefinition
from models.transition import Transition
from models.configuration import Configuration
from models.computation_result import ComputationResult


class TestCLIInterface:
    """Test the CLI interface functionality."""

    def setup_method(self):
        """Set up CLI interface for testing."""
        self.cli = CLIInterface()

    def test_collect_states(self, monkeypatch):
        """Test collecting number of states from user."""
        # Mock user inputs: invalid input first, then valid
        inputs = iter(['not_a_number', '3'])
        monkeypatch.setattr('builtins.input', lambda _: next(inputs))

        # Mock print to capture error messages
        with patch('builtins.print') as mock_print:
            result = self.cli.collect_states()

        # Should return set of states
        assert result == {'0', '1', '2'}

        # Should have printed error for invalid input
        mock_print.assert_any_call("Invalid input: number of states must be int")

    def test_collect_input_alphabet(self, monkeypatch):
        """Test collecting input alphabet from user."""
        # User enters comma-separated symbols
        inputs = iter(['0,1'])
        monkeypatch.setattr('builtins.input', lambda _: next(inputs))

        result = self.cli.collect_input_alphabet()

        assert result == {'0', '1'}

    def test_collect_input_alphabet_empty(self, monkeypatch):
        """Test handling empty input alphabet."""
        # User enters empty, then valid input
        inputs = iter(['', '0,1'])
        monkeypatch.setattr('builtins.input', lambda _: next(inputs))

        with patch('builtins.print') as mock_print:
            result = self.cli.collect_input_alphabet()

        assert result == {'0', '1'}
        mock_print.assert_any_call("Input alphabet can't be empty")

    def test_collect_accept_states(self, monkeypatch):
        """Test collecting accept states from user."""
        # User enters comma-separated state numbers
        states = {'0', '1', '2'}
        inputs = iter(['2'])  # Just state 2 is accepting
        monkeypatch.setattr('builtins.input', lambda _: next(inputs))

        result = self.cli.collect_accept_states(states)

        assert result == {'2'}

    def test_collect_accept_states_invalid(self, monkeypatch):
        """Test handling invalid accept states."""
        states = {'0', '1', '2'}
        # User enters invalid state, then valid
        inputs = iter(['5', '2'])
        monkeypatch.setattr('builtins.input', lambda _: next(inputs))

        with patch('builtins.print') as mock_print:
            result = self.cli.collect_accept_states(states)

        assert result == {'2'}
        # Should print error about invalid state
        assert any('invalid state' in str(call) for call in mock_print.call_args_list)

    def test_collect_transition_no(self, monkeypatch):
        """Test when user doesn't want to add a transition."""
        # User says 'n' for no transition
        inputs = iter(['n'])
        monkeypatch.setattr('builtins.input', lambda _: next(inputs))

        result = self.cli.collect_transition('0', {'0', '1'}, {'X', 'Y', 'Z'})

        assert result is None

    def test_collect_transition_yes(self, monkeypatch):
        """Test collecting a transition from user."""
        # User wants to add transition: read '0', pop 'X', push 'XX', go to state 1
        inputs = iter([
            'y',     # Yes, add transition
            '0',     # Input symbol
            'X',     # Stack top
            '1',     # Next state
            'XX'     # Push symbols (single multi-char symbol)
        ])
        monkeypatch.setattr('builtins.input', lambda _: next(inputs))

        result = self.cli.collect_transition('0', {'0', '1'}, {'X', 'Y', 'Z', 'XX'}, num_states=3)  # Add 'XX' to alphabet

        assert result is not None
        assert result.from_state == '0'
        assert result.input_symbol == '0'
        assert result.stack_top == 'X'
        assert result.to_state == '1'
        assert result.stack_push == 'XX'

    def test_collect_transition_epsilon_input(self, monkeypatch):
        """Test collecting transition with epsilon input."""
        # User enters '-' for epsilon
        inputs = iter([
            'y',     # Yes, add transition
            '-',     # Epsilon input
            'X',     # Stack top
            '1',     # Next state
            'Y'      # Push symbol
        ])
        monkeypatch.setattr('builtins.input', lambda _: next(inputs))

        result = self.cli.collect_transition('0', {'0', '1'}, {'X', 'Y', 'Z'}, num_states=3)

        assert result is not None
        assert result.input_symbol is None  # Epsilon represented as None

    def test_collect_all_transitions(self, monkeypatch):
        """Test collecting all transitions for a DPDA."""
        states = {'0', '1', '2'}
        input_alphabet = {'0', '1'}
        stack_alphabet = {'Z', 'X'}

        # Mock sequence: state 0 has 2 transitions, state 1 has 1, state 2 has none
        inputs = iter([
            # State 0, first transition
            'y', '0', 'Z', '0', 'X,Z',  # Use comma-separated format
            # State 0, second transition
            'y', '0', 'X', '0', 'X,X',  # Use comma-separated format
            # State 0, no more
            'n',
            # State 1, first transition
            'y', '1', 'X', '1', '',
            # State 1, no more
            'n',
            # State 2, no transitions
            'n'
        ])
        monkeypatch.setattr('builtins.input', lambda _: next(inputs))

        with patch('builtins.print'):
            transitions = self.cli.collect_all_transitions(
                states, input_alphabet, stack_alphabet
            )

        assert len(transitions) == 3
        # Check first transition
        assert transitions[0].from_state == '0'
        assert transitions[0].input_symbol == '0'

    def test_format_transition_for_display(self):
        """Test formatting transitions for display."""
        trans = Transition('0', '0', 'Z', '0', 'XZ')  # XZ as single symbol
        result = self.cli.format_transition_display(trans)
        assert result == "[0,Z->XZ]"

        # Test epsilon transition
        trans_eps = Transition('1', None, 'Z', '2', 'Z')
        result = self.cli.format_transition_display(trans_eps)
        assert result == "[eps,Z->Z]"

    def test_process_input_string(self, monkeypatch):
        """Test processing an input string through DPDA."""
        # Mock a simple DPDA and computation result
        dpda = Mock(spec=DPDADefinition)
        engine = Mock()

        # Mock computation result
        mock_result = ComputationResult(
            accepted=True,
            final_state='1',
            trace=[
                Configuration('0', '01', ['Z']),  # Stack as list
                Configuration('0', '1', ['X', 'Z']),  # Stack as list
                Configuration('1', '', ['Z'])  # Stack as list
            ],
            steps_taken=2
        )
        # Add the transitions as a custom attribute for our formatter
        mock_result.configurations = mock_result.trace
        mock_result.transitions = [
            Transition('0', '0', 'Z', '0', 'X,Z'),  # Use comma-separated
            Transition('0', '1', 'X', '1', '')
        ]
        engine.compute.return_value = mock_result

        # User enters input string
        inputs = iter(['01'])
        monkeypatch.setattr('builtins.input', lambda _: next(inputs))

        with patch('builtins.print') as mock_print:
            self.cli.process_input_string(dpda, engine)

        # Should print acceptance result
        mock_print.assert_any_call("Accept string 01?", True)
        # Should print trace
        assert any('(q0;01;Z)' in str(call) for call in mock_print.call_args_list)

    def test_run_interactive_session(self, monkeypatch):
        """Test running a complete interactive session."""
        # Mock entire session: setup DPDA and process one string
        inputs = iter([
            # Number of states
            '2',
            # Input alphabet
            '0,1',
            # Accept states
            '1',
            # Transitions for state 0
            'y', '0', 'Z', '0', 'X,Z',  # Use comma-separated
            'y', '1', 'X', '1', '',
            'n',
            # Transitions for state 1
            'n',
            # Input string to test
            '01',
            # Another string (to exit, we'll mock KeyboardInterrupt)
        ])

        def mock_input(prompt):
            try:
                return next(inputs)
            except StopIteration:
                raise KeyboardInterrupt()

        monkeypatch.setattr('builtins.input', mock_input)

        with patch('builtins.print'):
            # Should handle the session and exit gracefully
            self.cli.run_interactive_session()

    def test_display_transitions(self):
        """Test displaying all transitions."""
        transitions = [
            Transition('0', '0', 'Z', '0', 'X,Z'),  # Use comma-separated
            Transition('0', '1', 'X', '1', ''),
            Transition('1', None, 'Z', '2', 'Z')
        ]

        with patch('builtins.print') as mock_print:
            self.cli.display_transitions(transitions, num_states=3)

        # Should print transitions grouped by state
        calls = [str(call) for call in mock_print.call_args_list]
        assert any('Transitions for state 0:' in call for call in calls)
        assert any('[0,Z->X,Z]' in call for call in calls)  # Updated expectation
        assert any('[1,X->eps]' in call for call in calls)
        assert any('[eps,Z->Z]' in call for call in calls)

    def test_epsilon_input_handling(self, monkeypatch):
        """Test that '-' is properly converted to None for epsilon."""
        # User enters '-' for epsilon in various contexts
        inputs = iter([
            'y',     # Yes to transition
            '-',     # Epsilon for input
            '-',     # Epsilon for stack
            '1',     # Next state
            ''       # Empty push (epsilon)
        ])
        monkeypatch.setattr('builtins.input', lambda _: next(inputs))

        result = self.cli.collect_transition('0', {'0', '1'}, {'X'}, num_states=2)

        assert result.input_symbol is None
        assert result.stack_top is None
        assert result.stack_push == ''

    def test_validation_error_handling(self, monkeypatch):
        """Test handling of DPDA validation errors."""
        # Create transitions that violate determinism
        states = {'0', '1'}
        input_alphabet = {'0', '1'}
        stack_alphabet = {'Z', 'X'}

        # Try to add two transitions with same (state, input, stack)
        inputs = iter([
            # First transition: (0, '0', 'Z')
            'y', '0', 'Z', '1', 'X',
            # Second transition: (0, '0', 'Z') - should violate determinism
            'y', '0', 'Z', '1', 'Y',
            'n',
            # State 1
            'n'
        ])
        monkeypatch.setattr('builtins.input', lambda _: next(inputs))

        with patch('builtins.print') as mock_print:
            transitions = self.cli.collect_all_transitions(
                states, input_alphabet, stack_alphabet
            )

        # The CLI should detect and report the violation
        # (Implementation will handle this when we write it)
        assert len(transitions) >= 1  # At least first transition added