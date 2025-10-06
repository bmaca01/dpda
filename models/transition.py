"""
Transition model for DPDA.
Represents a single transition in the DPDA transition function.
"""

from typing import Optional


class Transition:
    """Represents a transition in a DPDA."""

    def __init__(
        self,
        from_state: str,
        input_symbol: Optional[str],
        stack_top: Optional[str],
        to_state: str,
        stack_push: str
    ):
        """
        Initialize a transition.

        Args:
            from_state: Source state
            input_symbol: Input symbol to read (None for epsilon)
            stack_top: Symbol that must be on top of stack (None for epsilon - no stack check)
            to_state: Destination state
            stack_push: String to push onto stack (empty string means pop)
        """
        self.from_state = from_state
        self.input_symbol = input_symbol
        self.stack_top = stack_top
        self.to_state = to_state
        self.stack_push = stack_push

    @property
    def is_epsilon(self) -> bool:
        """Check if this is an epsilon transition."""
        return self.input_symbol is None

    @property
    def is_pop_operation(self) -> bool:
        """Check if this transition pops from the stack."""
        return self.stack_push == ''

    def __eq__(self, other) -> bool:
        """Check equality with another transition."""
        if not isinstance(other, Transition):
            return False
        return (
            self.from_state == other.from_state and
            self.input_symbol == other.input_symbol and
            self.stack_top == other.stack_top and
            self.to_state == other.to_state and
            self.stack_push == other.stack_push
        )

    def __hash__(self) -> int:
        """Hash for use in sets/dicts."""
        return hash((
            self.from_state,
            self.input_symbol,
            self.stack_top,
            self.to_state,
            self.stack_push
        ))

    def __str__(self) -> str:
        """String representation for debugging."""
        input_str = self.input_symbol if self.input_symbol is not None else 'ε'
        push_str = self.stack_push if self.stack_push else 'ε'
        return f"δ({self.from_state}, {input_str}, {self.stack_top}) = ({self.to_state}, {push_str})"

    def __repr__(self) -> str:
        """Representation for debugging."""
        return (
            f"Transition('{self.from_state}', "
            f"{repr(self.input_symbol)}, '{self.stack_top}', "
            f"'{self.to_state}', '{self.stack_push}')"
        )