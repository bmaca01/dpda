"""
Configuration model for DPDA.
Represents an instantaneous description (ID) of the DPDA.
"""

from typing import Optional, List, Union


class Configuration:
    """Represents a configuration (instantaneous description) of a DPDA."""

    def __init__(self, state: str, remaining_input: str, stack: Union[str, List[str]]):
        """
        Initialize a configuration.

        Args:
            state: Current state
            remaining_input: Remaining input string to process
            stack: Current stack contents (top is first element)
                   Can be string (for backward compat) or list of symbols
        """
        self.state = state
        self.remaining_input = remaining_input

        # Convert string stack to list for uniform handling
        if isinstance(stack, str):
            # Empty string becomes empty list
            if stack == '':
                self.stack = []
            else:
                # For simple single-char stacks, split into chars
                # This maintains backward compatibility
                self.stack = list(stack)
        else:
            self.stack = stack if stack is not None else []

    @property
    def has_input(self) -> bool:
        """Check if there is remaining input."""
        return len(self.remaining_input) > 0

    @property
    def next_input_symbol(self) -> Optional[str]:
        """Get the next input symbol, or None if input is empty."""
        return self.remaining_input[0] if self.remaining_input else None

    @property
    def stack_top(self) -> Optional[str]:
        """Get the top of the stack, or None if stack is empty."""
        return self.stack[0] if self.stack else None

    @property
    def stack_as_string(self) -> str:
        """Get stack as string for display (backward compat)."""
        return ''.join(self.stack)

    def __eq__(self, other) -> bool:
        """Check equality with another configuration."""
        if not isinstance(other, Configuration):
            return False
        return (
            self.state == other.state and
            self.remaining_input == other.remaining_input and
            self.stack == other.stack
        )

    def __hash__(self) -> int:
        """Hash for use in sets/dicts."""
        return hash((self.state, self.remaining_input, tuple(self.stack)))

    def __str__(self) -> str:
        """String representation for trace output."""
        input_str = self.remaining_input if self.remaining_input else 'ε'
        # For display, join stack symbols (may be multi-char)
        stack_str = ''.join(self.stack) if self.stack else 'ε'
        return f"({self.state}, {input_str}, {stack_str})"

    def __repr__(self) -> str:
        """Representation for debugging."""
        return (
            f"Configuration('{self.state}', "
            f"'{self.remaining_input}', '{self.stack}')"
        )