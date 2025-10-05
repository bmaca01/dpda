"""
Computation result model.
Represents the result of running a DPDA on an input string.
"""

from typing import List, Optional
from models.configuration import Configuration


class ComputationResult:
    """Result of a DPDA computation."""

    def __init__(
        self,
        accepted: bool,
        final_state: str,
        trace: List[Configuration],
        steps_taken: int,
        rejection_reason: Optional[str] = None
    ):
        """
        Initialize a computation result.

        Args:
            accepted: Whether the input was accepted
            final_state: The final state reached
            trace: List of configurations in the computation
            steps_taken: Number of steps taken
            rejection_reason: Reason for rejection (if not accepted)
        """
        self.accepted = accepted
        self.final_state = final_state
        self.trace = trace
        self.steps_taken = steps_taken
        self.rejection_reason = rejection_reason

    def __str__(self) -> str:
        """String representation."""
        status = "ACCEPTED" if self.accepted else "REJECTED"
        return f"{status} in {self.steps_taken} steps, final state: {self.final_state}"

    def __repr__(self) -> str:
        """Detailed representation."""
        return (
            f"ComputationResult(accepted={self.accepted}, "
            f"final_state='{self.final_state}', "
            f"steps={self.steps_taken}, "
            f"trace_length={len(self.trace)})"
        )