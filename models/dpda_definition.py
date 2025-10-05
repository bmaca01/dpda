"""
DPDA Definition model.
Represents the formal definition of a Deterministic Pushdown Automaton.
"""

from typing import Set, List, Optional
from models.transition import Transition


class DPDADefinition:
    """Formal definition of a Deterministic Pushdown Automaton."""

    def __init__(
        self,
        states: Set[str],
        input_alphabet: Set[str],
        stack_alphabet: Set[str],
        initial_state: str,
        initial_stack_symbol: str,
        accept_states: Set[str],
        transitions: List[Transition]
    ):
        """
        Initialize a DPDA definition.

        Args:
            states: Set of state names
            input_alphabet: Set of input symbols
            stack_alphabet: Set of stack symbols
            initial_state: Initial state name
            initial_stack_symbol: Initial stack symbol
            accept_states: Set of accepting state names
            transitions: List of transitions

        Raises:
            ValueError: If the definition is invalid
        """
        self.states = states
        self.input_alphabet = input_alphabet
        self.stack_alphabet = stack_alphabet
        self.initial_state = initial_state
        self.initial_stack_symbol = initial_stack_symbol
        self.accept_states = accept_states
        self.transitions = transitions

        # Build transition lookup table for efficiency
        self._transition_table = {}
        for trans in transitions:
            key = (trans.from_state, trans.input_symbol, trans.stack_top)
            self._transition_table[key] = trans

        # Validate the definition
        self._validate()

    def _validate(self):
        """Validate the DPDA definition for basic consistency."""
        # Check initial state is in states
        if self.initial_state not in self.states:
            raise ValueError(f"Initial state '{self.initial_state}' not in states")

        # Check accept states are subset of states
        for state in self.accept_states:
            if state not in self.states:
                raise ValueError(f"Accept state '{state}' not in states")

        # Check initial stack symbol is in stack alphabet
        if self.initial_stack_symbol not in self.stack_alphabet:
            raise ValueError(
                f"Initial stack symbol '{self.initial_stack_symbol}' "
                f"not in stack alphabet"
            )

    def get_transition(
        self,
        state: str,
        input_symbol: Optional[str],
        stack_top: str
    ) -> Optional[Transition]:
        """
        Find the transition for a given configuration.

        Args:
            state: Current state
            input_symbol: Input symbol (None for epsilon)
            stack_top: Top of stack

        Returns:
            The matching transition, or None if no transition exists
        """
        # First try exact match
        key = (state, input_symbol, stack_top)
        if key in self._transition_table:
            return self._transition_table[key]

        # Try with epsilon stack (matches any stack top)
        eps_stack_key = (state, input_symbol, None)
        if eps_stack_key in self._transition_table:
            return self._transition_table[eps_stack_key]

        # If no input transition found and input_symbol is not None,
        # try epsilon input transitions
        if input_symbol is not None:
            # Try epsilon input with exact stack match
            epsilon_key = (state, None, stack_top)
            if epsilon_key in self._transition_table:
                return self._transition_table[epsilon_key]

            # Try epsilon input with epsilon stack (matches any)
            eps_both_key = (state, None, None)
            if eps_both_key in self._transition_table:
                return self._transition_table[eps_both_key]

        return None

    def __str__(self) -> str:
        """String representation."""
        return (
            f"DPDA(states={len(self.states)}, "
            f"alphabet={len(self.input_alphabet)}, "
            f"transitions={len(self.transitions)})"
        )

    def __repr__(self) -> str:
        """Detailed representation."""
        return (
            f"DPDADefinition(states={self.states}, "
            f"input_alphabet={self.input_alphabet}, "
            f"stack_alphabet={self.stack_alphabet}, "
            f"initial_state='{self.initial_state}', "
            f"initial_stack_symbol='{self.initial_stack_symbol}', "
            f"accept_states={self.accept_states}, "
            f"transitions={self.transitions})"
        )