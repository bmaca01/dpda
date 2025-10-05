"""
Core DPDA computation engine.
Provides stateless functions for DPDA simulation.
"""

from typing import Optional, List
from models.dpda_definition import DPDADefinition
from models.configuration import Configuration
from models.computation_result import ComputationResult


class DPDAEngine:
    """Stateless DPDA computation engine."""

    def step(
        self,
        dpda: DPDADefinition,
        config: Configuration
    ) -> Optional[Configuration]:
        """
        Execute a single step of DPDA computation.

        Args:
            dpda: The DPDA definition
            config: Current configuration

        Returns:
            Next configuration, or None if no valid transition
        """
        # Get the applicable transition
        transition = dpda.get_transition(
            config.state,
            config.next_input_symbol,
            config.stack_top
        )

        if transition is None:
            return None

        # Compute new configuration
        new_state = transition.to_state

        # Handle input consumption
        if transition.is_epsilon:
            new_input = config.remaining_input
        else:
            # Consume one input symbol
            new_input = config.remaining_input[1:]

        # Handle stack operations (now with list-based stack)
        if transition.stack_top is None:
            # Epsilon stack top means don't pop anything
            remaining_stack = config.stack.copy()
        elif config.stack and config.stack[0] == transition.stack_top:
            # Pop the matching stack top
            remaining_stack = config.stack[1:]
        else:
            # This shouldn't happen if get_transition worked correctly
            remaining_stack = config.stack.copy()

        # Parse push symbols (may be multi-character symbols separated by commas)
        # The transition.stack_push is a string that may contain comma-separated symbols
        new_stack_symbols = []
        if transition.stack_push:
            # Check if it contains commas (multi-symbol push)
            if ',' in transition.stack_push:
                # Split by comma - each part is a symbol
                for symbol in transition.stack_push.split(','):
                    if symbol:  # Skip empty strings
                        new_stack_symbols.append(symbol)
            else:
                # No commas - treat as single symbol (could be multi-char like "E1")
                new_stack_symbols.append(transition.stack_push)

        # Create new stack: pushed symbols + remaining stack
        new_stack = new_stack_symbols + remaining_stack

        return Configuration(new_state, new_input, new_stack)

    def compute(
        self,
        dpda: DPDADefinition,
        input_string: str,
        max_steps: int = 1000
    ) -> ComputationResult:
        """
        Run the DPDA on an input string.

        Args:
            dpda: The DPDA definition
            input_string: Input string to process
            max_steps: Maximum steps before timeout

        Returns:
            ComputationResult with acceptance status and trace
        """
        # Initialize configuration
        config = Configuration(
            dpda.initial_state,
            input_string,
            dpda.initial_stack_symbol
        )

        trace = [config]
        steps = 0

        # Run computation
        while steps < max_steps:
            # Check if we can take an epsilon transition to accept
            if (config.remaining_input == '' and
                config.state in dpda.accept_states):
                return ComputationResult(
                    accepted=True,
                    final_state=config.state,
                    trace=trace,
                    steps_taken=steps
                )

            # Try to take a step
            next_config = self.step(dpda, config)

            if next_config is None:
                # No valid transition - check if we're in accept state
                if (config.remaining_input == '' and
                    config.state in dpda.accept_states):
                    return ComputationResult(
                        accepted=True,
                        final_state=config.state,
                        trace=trace,
                        steps_taken=steps
                    )
                else:
                    # Stuck with no valid transition
                    rejection_reason = "No valid transition"
                    if config.remaining_input:
                        rejection_reason = "Input not fully consumed"
                    return ComputationResult(
                        accepted=False,
                        final_state=config.state,
                        trace=trace,
                        steps_taken=steps,
                        rejection_reason=rejection_reason
                    )

            # Move to next configuration
            config = next_config
            trace.append(config)
            steps += 1

        # Exceeded max steps
        return ComputationResult(
            accepted=False,
            final_state=config.state,
            trace=trace,
            steps_taken=steps,
            rejection_reason="Maximum steps exceeded"
        )