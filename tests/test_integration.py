"""
Integration tests for the DPDA simulator.
Tests the complete system including CLI, engine, and validator.
"""

import pytest
from unittest.mock import patch, MagicMock
from io import StringIO
import sys

# Import the components
from cli_io.cli_interface import CLIInterface
from core.dpda_engine import DPDAEngine
from core.session import DPDASession
from models.dpda_definition import DPDADefinition
from models.transition import Transition
from validation.dpda_validator import DPDAValidator
from serialization.dpda_serializer import DPDASerializer


class TestIntegration:
    """End-to-end integration tests."""

    def test_0n1n_language(self):
        """Test DPDA that accepts {0^n 1^n | n >= 1}."""
        # Create DPDA for 0^n 1^n (n >= 1)
        # Note: Cannot easily accept empty string with deterministic PDA
        # without violating property (b)
        states = {'0', '1', '2'}
        input_alphabet = {'0', '1'}
        stack_alphabet = {'Z', 'X'}
        accept_states = {'2'}

        transitions = [
            # From state 0: push X for each 0
            Transition('0', '0', 'Z', '0', 'X,Z'),  # Push X for first 0 (comma-separated)
            Transition('0', '0', 'X', '0', 'X,X'),  # Continue pushing X (comma-separated)
            Transition('0', '1', 'X', '1', ''),     # Start popping on 1
            # From state 1: continue popping
            Transition('1', '1', 'X', '1', ''),     # Continue popping
            Transition('1', None, 'Z', '2', 'Z'),   # Accept when stack has only Z
        ]

        dpda = DPDADefinition(
            states=states,
            input_alphabet=input_alphabet,
            stack_alphabet=stack_alphabet,
            initial_state='0',
            initial_stack_symbol='Z',
            accept_states=accept_states,
            transitions=transitions
        )

        # Validate DPDA
        validator = DPDAValidator()
        result = validator.validate(dpda)
        assert result.is_valid, f"DPDA validation failed: {result.errors}"

        # Test with engine
        engine = DPDAEngine()

        # Test accepting strings (n >= 1)
        assert engine.compute(dpda, "01").accepted
        assert engine.compute(dpda, "0011").accepted
        assert engine.compute(dpda, "000111").accepted

        # Test rejecting strings
        assert not engine.compute(dpda, "").accepted  # Empty string not accepted
        assert not engine.compute(dpda, "0").accepted
        assert not engine.compute(dpda, "1").accepted
        assert not engine.compute(dpda, "001").accepted
        assert not engine.compute(dpda, "0101").accepted

    def test_palindrome_with_center(self):
        """Test DPDA for palindromes with center marker 'c'."""
        states = {'0', '1', '2'}
        input_alphabet = {'0', '1', 'c'}
        stack_alphabet = {'Z', '0', '1'}
        accept_states = {'2'}

        transitions = [
            # Push phase (before 'c') - use comma separation for multiple symbols
            Transition('0', '0', 'Z', '0', '0,Z'),
            Transition('0', '0', '0', '0', '0,0'),
            Transition('0', '0', '1', '0', '0,1'),
            Transition('0', '1', 'Z', '0', '1,Z'),
            Transition('0', '1', '0', '0', '1,0'),
            Transition('0', '1', '1', '0', '1,1'),

            # Center marker
            Transition('0', 'c', 'Z', '1', 'Z'),
            Transition('0', 'c', '0', '1', '0'),
            Transition('0', 'c', '1', '1', '1'),

            # Pop phase (after 'c')
            Transition('1', '0', '0', '1', ''),
            Transition('1', '1', '1', '1', ''),

            # Accept
            Transition('1', None, 'Z', '2', 'Z'),
        ]

        dpda = DPDADefinition(
            states=states,
            input_alphabet=input_alphabet,
            stack_alphabet=stack_alphabet,
            initial_state='0',
            initial_stack_symbol='Z',
            accept_states=accept_states,
            transitions=transitions
        )

        # Validate DPDA
        validator = DPDAValidator()
        result = validator.validate(dpda)
        assert result.is_valid, f"DPDA validation failed: {result.errors}"

        engine = DPDAEngine()

        # Test accepting palindromes
        assert engine.compute(dpda, "c").accepted  # Just center
        assert engine.compute(dpda, "0c0").accepted
        assert engine.compute(dpda, "1c1").accepted
        assert engine.compute(dpda, "01c10").accepted
        assert engine.compute(dpda, "110c011").accepted

        # Test rejecting non-palindromes
        assert not engine.compute(dpda, "0c1").accepted
        assert not engine.compute(dpda, "01c01").accepted
        assert not engine.compute(dpda, "00c01").accepted

    def test_cli_output_format(self, monkeypatch):
        """Test that CLI output matches expected format."""
        cli = CLIInterface()

        # Create a simple DPDA
        dpda = DPDADefinition(
            states={'0', '1'},
            input_alphabet={'a'},
            stack_alphabet={'Z', 'X'},
            initial_state='0',
            initial_stack_symbol='Z',
            accept_states={'1'},
            transitions=[
                Transition('0', 'a', 'Z', '1', 'XZ')
            ]
        )

        # Mock user input
        inputs = iter(['a'])
        monkeypatch.setattr('builtins.input', lambda _: next(inputs))

        # Capture output
        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            cli.process_input_string(dpda, cli.engine)

        output = captured_output.getvalue()

        # Check output format
        assert "Accept string a?" in output
        assert "True" in output or "False" in output

    def test_full_session_simulation(self, monkeypatch):
        """Simulate a complete interactive session."""
        # Mock all user inputs for a simple DPDA
        inputs = iter([
            # Number of states
            '2',
            # Input alphabet
            'a,b',
            # Accept states
            '1',
            # State 0 transitions
            'y', 'a', 'Z', '0', 'X,Z',  # First transition (comma-separated)
            'y', 'b', 'X', '1', '',      # Second transition
            'n',  # No more transitions for state 0
            # State 1 transitions
            'n',  # No transitions for state 1
            # Test input strings
            'ab',  # First test string
        ])

        def mock_input(prompt):
            try:
                return next(inputs)
            except StopIteration:
                raise KeyboardInterrupt()

        monkeypatch.setattr('builtins.input', mock_input)

        cli = CLIInterface()

        # Capture output
        with patch('builtins.print') as mock_print:
            try:
                cli.run_interactive_session()
            except KeyboardInterrupt:
                pass  # Expected when we run out of inputs

        # Get all printed outputs
        output_lines = [str(call) for call in mock_print.call_args_list]
        output = '\n'.join(output_lines)

        # Check that key outputs appear - the CLI prints transitions
        assert any("Transitions for state" in line for line in output_lines)
        assert any("Transitions for state 0:" in line for line in output_lines)
        assert any("[a,Z->X,Z]" in line for line in output_lines)
        assert any("[b,X->eps]" in line for line in output_lines)
        assert any("Accept string ab?" in line for line in output_lines)

    def test_backward_compatibility_prompts(self, monkeypatch):
        """Ensure prompts exactly match original implementation."""
        expected_prompts = [
            "Enter number of states :",
            "Enter input alphabet as a comma-separated list of symbols :",
            "Enter accepting states as a comma-separated list of integers :",
            "Need a transition rule for state 0 ? (y or n)",
            "Input Symbol to read (enter - for epsilon, enter -- for '-'): ",
            "Stack symbol to match and pop (enter - for epsilon, enter -- for '-'): ",
            "State to transition to : ",
            "Stack symbols to push as comma separated list, first symbol to top of stack (enter - for epsilon, enter -- for '-'): ",
            "Enter an input string to be processed by the PDA : "
        ]

        # Track which prompts were called
        prompts_seen = []

        def mock_input(prompt):
            prompts_seen.append(prompt)
            # Provide appropriate response
            if "states" in prompt and "number" in prompt:
                return '2'
            elif "alphabet" in prompt:
                return 'a,b'
            elif "accept" in prompt:
                return '1'
            elif "Need a transition" in prompt:
                return 'n'
            elif "input string" in prompt:
                raise KeyboardInterrupt()
            return ''

        monkeypatch.setattr('builtins.input', mock_input)

        cli = CLIInterface()

        # Run part of the session
        try:
            cli.run_interactive_session()
        except KeyboardInterrupt:
            pass

        # Check that expected prompts were used
        for expected in expected_prompts[:3]:  # Check first few prompts
            assert any(expected in prompt for prompt in prompts_seen), \
                f"Expected prompt '{expected}' not found"

    def test_epsilon_handling_consistency(self):
        """Test that epsilon is handled consistently throughout."""
        # Create DPDA with epsilon transitions
        dpda = DPDADefinition(
            states={'0', '1'},
            input_alphabet={'a'},
            stack_alphabet={'Z', 'X'},
            initial_state='0',
            initial_stack_symbol='Z',
            accept_states={'1'},
            transitions=[
                Transition('0', None, 'Z', '1', 'Z')  # Epsilon transition
            ]
        )

        from cli_io.formatter import OutputFormatter

        engine = DPDAEngine()
        formatter = OutputFormatter()

        # Test that epsilon transition works
        result = engine.compute(dpda, "")
        assert result.accepted

        # Test formatting
        trans_str = formatter.format_transition(None, 'Z', 'Z')
        assert trans_str == "[eps,Z->Z]"

    def test_integration_with_validator(self):
        """Test that validator correctly identifies invalid DPDAs."""
        # Create DPDA with determinism violation
        states = {'0', '1'}
        input_alphabet = {'a'}
        stack_alphabet = {'Z'}
        accept_states = {'1'}

        # These transitions violate property (a) - same (state, input, stack)
        transitions = [
            Transition('0', 'a', 'Z', '0', 'Z'),
            Transition('0', 'a', 'Z', '1', 'Z'),  # Violation!
        ]

        dpda = DPDADefinition(
            states=states,
            input_alphabet=input_alphabet,
            stack_alphabet=stack_alphabet,
            initial_state='0',
            initial_stack_symbol='Z',
            accept_states=accept_states,
            transitions=transitions
        )

        validator = DPDAValidator()
        result = validator.validate(dpda)

        assert not result.is_valid
        assert any("multiple transitions" in error.lower() for error in result.errors)

    def test_serialization_integration(self):
        """Test serialization works with all components."""
        # Create the 0^n1^n DPDA
        states = {'0', '1', '2'}
        input_alphabet = {'0', '1'}
        stack_alphabet = {'Z', 'X'}
        accept_states = {'2'}

        transitions = [
            Transition('0', '0', 'Z', '0', 'X,Z'),
            Transition('0', '0', 'X', '0', 'X,X'),
            Transition('0', '1', 'X', '1', ''),
            Transition('1', '1', 'X', '1', ''),
            Transition('1', None, 'Z', '2', 'Z'),
        ]

        original_dpda = DPDADefinition(
            states=states,
            input_alphabet=input_alphabet,
            stack_alphabet=stack_alphabet,
            initial_state='0',
            initial_stack_symbol='Z',
            accept_states=accept_states,
            transitions=transitions
        )

        # Serialize and deserialize
        serializer = DPDASerializer()
        json_str = serializer.to_json(original_dpda)
        loaded_dpda = serializer.from_json(json_str)

        # Validate both DPDAs
        validator = DPDAValidator()
        original_valid = validator.validate(original_dpda)
        loaded_valid = validator.validate(loaded_dpda)

        assert original_valid.is_valid
        assert loaded_valid.is_valid

        # Test that both DPDAs accept the same strings
        engine = DPDAEngine()
        test_strings = ["01", "0011", "000111", "", "0", "1", "001", "0101"]

        for test_str in test_strings:
            original_result = engine.compute(original_dpda, test_str)
            loaded_result = engine.compute(loaded_dpda, test_str)
            assert original_result.accepted == loaded_result.accepted, \
                f"Mismatch for string '{test_str}'"

    def test_serialization_with_complex_dpda(self):
        """Test serialization with a complex DPDA including epsilon transitions."""
        # Create palindrome DPDA
        states = {'0', '1', '2'}
        input_alphabet = {'0', '1', 'c'}
        stack_alphabet = {'Z', '0', '1'}
        accept_states = {'2'}

        transitions = [
            # Push phase
            Transition('0', '0', 'Z', '0', '0,Z'),
            Transition('0', '0', '0', '0', '0,0'),
            Transition('0', '0', '1', '0', '0,1'),
            Transition('0', '1', 'Z', '0', '1,Z'),
            Transition('0', '1', '0', '0', '1,0'),
            Transition('0', '1', '1', '0', '1,1'),
            # Center
            Transition('0', 'c', 'Z', '1', 'Z'),
            Transition('0', 'c', '0', '1', '0'),
            Transition('0', 'c', '1', '1', '1'),
            # Pop phase
            Transition('1', '0', '0', '1', ''),
            Transition('1', '1', '1', '1', ''),
            # Accept
            Transition('1', None, 'Z', '2', 'Z'),
        ]

        original_dpda = DPDADefinition(
            states=states,
            input_alphabet=input_alphabet,
            stack_alphabet=stack_alphabet,
            initial_state='0',
            initial_stack_symbol='Z',
            accept_states=accept_states,
            transitions=transitions
        )

        # Test round-trip through dictionary format
        serializer = DPDASerializer()
        dict_form = serializer.to_dict(original_dpda)
        loaded_dpda = serializer.from_dict(dict_form)

        # Verify components match
        assert loaded_dpda.states == original_dpda.states
        assert loaded_dpda.input_alphabet == original_dpda.input_alphabet
        assert loaded_dpda.stack_alphabet == original_dpda.stack_alphabet
        assert loaded_dpda.initial_state == original_dpda.initial_state
        assert loaded_dpda.accept_states == original_dpda.accept_states
        assert len(loaded_dpda.transitions) == len(original_dpda.transitions)

        # Test functionality
        engine = DPDAEngine()
        test_cases = [
            ("c", True),
            ("0c0", True),
            ("1c1", True),
            ("01c10", True),
            ("0c1", False),
            ("01c01", False),
        ]

        for test_str, expected in test_cases:
            result = engine.compute(loaded_dpda, test_str)
            assert result.accepted == expected, f"Failed for '{test_str}'"

    def test_session_integration(self):
        """Test session management with full workflow."""
        import tempfile
        from pathlib import Path

        # Create a session and build a DPDA
        session = DPDASession("integration_test")

        # Build 0^n1^n language DPDA
        session.new_dpda("0n1n")
        session.set_states({'q0', 'q1', 'q2'})
        session.set_input_alphabet({'0', '1'})
        session.set_stack_alphabet({'Z', 'X'})
        session.set_initial_state('q0')
        session.set_initial_stack_symbol('Z')
        session.set_accept_states({'q2'})

        # Add transitions
        session.add_transition('q0', '0', 'Z', 'q0', 'X,Z')
        session.add_transition('q0', '0', 'X', 'q0', 'X,X')
        session.add_transition('q0', '1', 'X', 'q1', '')
        session.add_transition('q1', '1', 'X', 'q1', '')
        session.add_transition('q1', None, 'Z', 'q2', 'Z')

        # Validate the DPDA
        validation = session.validate_current()
        assert validation.is_valid

        # Build and test the DPDA
        dpda = session.build_current_dpda()
        engine = DPDAEngine()

        assert engine.compute(dpda, "01").accepted
        assert engine.compute(dpda, "0011").accepted
        assert not engine.compute(dpda, "001").accepted

        # Save session to file
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            filepath = f.name

        try:
            session.save_to_file(filepath)

            # Load in new session
            loaded_session = DPDASession.load_from_file(filepath)
            assert loaded_session.name == "integration_test"
            assert "0n1n" in loaded_session.get_dpda_list()

            loaded_session.switch_to("0n1n")
            loaded_dpda = loaded_session.build_current_dpda()

            # Verify it still works
            assert engine.compute(loaded_dpda, "01").accepted
            assert engine.compute(loaded_dpda, "0011").accepted
        finally:
            Path(filepath).unlink()

    def test_session_multi_dpda_workflow(self):
        """Test session with multiple DPDAs."""
        session = DPDASession("multi_test")

        # Create first DPDA (accepts 'a')
        session.new_dpda("simple1")
        session.set_states({'q0', 'q1'})
        session.set_input_alphabet({'a'})
        session.set_stack_alphabet({'Z'})
        session.set_initial_state('q0')
        session.set_initial_stack_symbol('Z')
        session.set_accept_states({'q1'})
        session.add_transition('q0', 'a', 'Z', 'q1', 'Z')

        # Create second DPDA (accepts 'b')
        session.new_dpda("simple2")
        session.set_states({'p0', 'p1'})
        session.set_input_alphabet({'b'})
        session.set_stack_alphabet({'Z'})
        session.set_initial_state('p0')
        session.set_initial_stack_symbol('Z')
        session.set_accept_states({'p1'})
        session.add_transition('p0', 'b', 'Z', 'p1', 'Z')

        # Test both DPDAs
        engine = DPDAEngine()

        session.switch_to("simple1")
        dpda1 = session.build_current_dpda()
        assert engine.compute(dpda1, "a").accepted
        assert not engine.compute(dpda1, "b").accepted

        session.switch_to("simple2")
        dpda2 = session.build_current_dpda()
        assert engine.compute(dpda2, "b").accepted
        assert not engine.compute(dpda2, "a").accepted

        # Copy and modify
        session.copy_dpda("simple1", "simple1_modified")
        session.switch_to("simple1_modified")
        session.add_transition('q1', 'a', 'Z', 'q1', 'Z')  # Add self-loop

        dpda_mod = session.build_current_dpda()
        assert engine.compute(dpda_mod, "a").accepted
        assert engine.compute(dpda_mod, "aa").accepted  # Now accepts 'aa'

    def test_session_serializer_integration(self):
        """Test that session-built DPDAs work with serializer."""
        session = DPDASession("serializer_test")

        # Build a simple DPDA
        session.new_dpda("test_dpda")
        session.set_states({'q0', 'q1'})
        session.set_input_alphabet({'x'})
        session.set_stack_alphabet({'Z'})
        session.set_initial_state('q0')
        session.set_initial_stack_symbol('Z')
        session.set_accept_states({'q1'})
        session.add_transition('q0', 'x', 'Z', 'q1', 'Z')

        # Build DPDA
        dpda = session.build_current_dpda()

        # Serialize it
        serializer = DPDASerializer()
        json_str = serializer.to_json(dpda)

        # Load it back
        loaded_dpda = serializer.from_json(json_str)

        # Test both work the same
        engine = DPDAEngine()
        assert engine.compute(dpda, "x").accepted == engine.compute(loaded_dpda, "x").accepted
        assert engine.compute(dpda, "").accepted == engine.compute(loaded_dpda, "").accepted