"""Test for CLI stack alphabet character iteration bug fix."""

import pytest
from unittest.mock import Mock, patch
from io import StringIO
from models.transition import Transition
from cli_io.cli_interface import CLIInterface


def test_cli_collect_transitions_stack_alphabet():
    """Test that CLIInterface.collect_all_transitions correctly handles multi-character stack symbols.

    Bug: When stack_push contains multi-character symbols like "E1,T1",
    the code iterates over characters ('E', '1', ',', 'T', '1') instead
    of symbols ('E1', 'T1').
    """
    cli = CLIInterface()

    # Mock user inputs for collecting transitions
    with patch('builtins.input') as mock_input:
        # Setup transition with multi-character stack symbols
        mock_input.side_effect = [
            'y',      # Need transition for state 0?
            'a',      # Input symbol
            '$',      # Stack top
            '1',      # Target state
            'E1,T1',  # Stack push with multi-character symbols
            'n',      # More transitions?
            'n'       # Need transition for state 1?
        ]

        # Initial stack alphabet
        stack_alphabet = {'$'}

        # Collect transitions
        transitions = cli.collect_all_transitions(
            states={'0', '1'},
            input_alphabet={'a', 'b'},
            stack_alphabet=stack_alphabet  # This is modified in-place
        )

    # Check that stack alphabet was updated correctly
    # Should have E1 and T1 as separate symbols, not individual characters
    assert 'E1' in stack_alphabet, f"Expected 'E1' in {stack_alphabet}"
    assert 'T1' in stack_alphabet, f"Expected 'T1' in {stack_alphabet}"

    # These should NOT be in the alphabet if bug is fixed
    assert 'E' not in stack_alphabet, f"Should not have 'E' alone in {stack_alphabet}"
    assert '1' not in stack_alphabet, f"Should not have '1' alone in {stack_alphabet}"
    assert ',' not in stack_alphabet, f"Should not have ',' in {stack_alphabet}"


def test_stack_alphabet_single_symbol():
    """Test single stack symbol without commas."""
    trans = Transition(
        from_state="q0",
        input_symbol="b",
        stack_top="X",
        to_state="q1",
        stack_push="ABC"  # Single multi-character symbol, no comma
    )

    stack_alphabet = set()

    if trans.stack_push and trans.stack_push != '-':
        if ',' in trans.stack_push:
            symbols = trans.stack_push.split(',')
        else:
            symbols = [trans.stack_push]
        for symbol in symbols:
            stack_alphabet.add(symbol)

    # Should have one symbol "ABC", not individual characters
    assert stack_alphabet == {'ABC'}
    assert 'A' not in stack_alphabet
    assert 'B' not in stack_alphabet
    assert 'C' not in stack_alphabet


def test_stack_alphabet_epsilon():
    """Test epsilon (empty) stack push."""
    trans = Transition(
        from_state="q0",
        input_symbol="c",
        stack_top="Y",
        to_state="q1",
        stack_push="-"  # Epsilon
    )

    stack_alphabet = set()

    if trans.stack_push and trans.stack_push != '-':
        symbols = trans.stack_push.split(',')
        for symbol in symbols:
            stack_alphabet.add(symbol)

    # Should have no symbols added for epsilon
    assert stack_alphabet == set()