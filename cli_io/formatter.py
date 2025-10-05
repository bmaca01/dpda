"""
Output formatter for DPDA simulator.
Handles formatting of transitions, configurations, and computation traces.
"""

from typing import Optional, List, Tuple, Union
from models.configuration import Configuration
from models.transition import Transition


class OutputFormatter:
    """Formats DPDA output for display."""

    def format_transition(
        self,
        input_symbol: Optional[str],
        stack_top: Optional[str],
        push_symbols: str
    ) -> str:
        """
        Format a transition in the form [input,stack_top->push].

        Args:
            input_symbol: Input symbol or None for epsilon
            stack_top: Stack top symbol or None for epsilon
            push_symbols: Symbols to push (empty string for epsilon)

        Returns:
            Formatted transition string
        """
        # Convert None to "eps" for display
        input_str = "eps" if input_symbol is None or input_symbol == '' else input_symbol
        stack_str = "eps" if stack_top is None or stack_top == '' else stack_top
        push_str = "eps" if push_symbols == '' else push_symbols

        return f"[{input_str},{stack_str}->{push_str}]"

    def format_configuration(self, config: Configuration) -> str:
        """
        Format a configuration in the form (state;input;stack).

        Args:
            config: Configuration object

        Returns:
            Formatted configuration string
        """
        state_str = self.format_state(config.state)
        input_str = self.format_input(config.remaining_input)
        stack_str = self.format_stack(config.stack)

        return f"({state_str};{input_str};{stack_str})"

    def format_state(self, state: str) -> str:
        """
        Format state for display.

        Args:
            state: State identifier

        Returns:
            Formatted state (with 'q' prefix if numeric)
        """
        # If state is numeric string, add 'q' prefix
        if state.isdigit():
            return f"q{state}"
        # If already has prefix or non-numeric, return as-is
        return state

    def format_input(self, input_str: str) -> str:
        """
        Format input string for display.

        Args:
            input_str: Remaining input

        Returns:
            Formatted input or "eps" if empty
        """
        return "eps" if input_str == '' else input_str

    def format_stack(self, stack: Union[str, List[str]]) -> str:
        """
        Format stack for display.

        Args:
            stack: Stack contents (string or list of symbols, top at index 0)

        Returns:
            Formatted stack or "eps" if empty
        """
        # Handle both string and list formats
        if isinstance(stack, str):
            if stack == '':
                return "eps"
            # Display stack with bottom first (reverse of internal representation)
            return stack[::-1]
        else:
            # List of symbols
            if not stack:
                return "eps"
            # Reverse the list and join symbols
            # Display with bottom first
            return ''.join(reversed(stack))

    def format_computation_trace(
        self,
        configurations: List[Configuration],
        transitions: List[Transition],
        accepted: bool
    ) -> str:
        """
        Format a complete computation trace.

        Args:
            configurations: List of configurations in the computation
            transitions: List of transitions taken
            accepted: Whether the string was accepted

        Returns:
            Formatted trace string
        """
        if not configurations:
            return ""

        trace_parts = []

        # Add initial configuration
        trace_parts.append(self.format_configuration(configurations[0]))

        # Add each transition and resulting configuration
        for i, transition in enumerate(transitions):
            if i + 1 < len(configurations):
                # Format the transition
                trans_str = self.format_transition(
                    transition.input_symbol,
                    transition.stack_top,
                    transition.stack_push
                )
                trace_parts.append(f"--{trans_str}-->")

                # Add the next configuration
                trace_parts.append(self.format_configuration(configurations[i + 1]))

        return "".join(trace_parts)

    def format_transition_tuple(self, tup: Tuple) -> str:
        """
        Format a transition from the original tuple format.

        Args:
            tup: Tuple (input, stack_top, next_state, push_symbols, condition)
                condition: 1=eps/eps, 2=eps/stack, 3=input/eps, 4=input/stack

        Returns:
            Formatted transition string
        """
        input_sym = tup[0]
        stack_top = tup[1]
        push_symbols = tup[3]

        # Convert empty strings to None for epsilon
        if input_sym == '':
            input_sym = None
        if stack_top == '':
            stack_top = None

        return self.format_transition(input_sym, stack_top, push_symbols)