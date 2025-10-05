"""
DPDA validation logic.
Checks the four properties that must hold for a valid DPDA.
"""

from typing import List, Set, Dict, Tuple, Optional
from dataclasses import dataclass
from models.dpda_definition import DPDADefinition
from models.transition import Transition


@dataclass
class ValidationResult:
    """Result of DPDA validation."""
    is_valid: bool
    errors: List[str]


class DPDAValidator:
    """Validates DPDA definitions for determinism properties."""

    def validate(self, dpda: DPDADefinition) -> ValidationResult:
        """
        Validate a DPDA definition.

        Checks the following properties:
        (a) At most one transition per (state, input, stack) triple
        (b) No epsilon and non-epsilon transitions from same (state, stack) pair
        (c) Multiple epsilon transitions must have disjoint stack requirements
        (d) All symbols and states in transitions are valid

        Args:
            dpda: The DPDA definition to validate

        Returns:
            ValidationResult with validity status and error messages
        """
        errors = []

        # Property (d): Check all symbols and states are valid
        errors.extend(self._check_property_d(dpda))

        # Property (a): Check for determinism on (state, input, stack)
        errors.extend(self._check_property_a(dpda))

        # Property (b): Check no epsilon/non-epsilon conflicts
        errors.extend(self._check_property_b(dpda))

        # Property (c): Check epsilon transitions have disjoint stack requirements
        errors.extend(self._check_property_c(dpda))

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )

    def _check_property_a(self, dpda: DPDADefinition) -> List[str]:
        """Check property (a): at most one transition per (state, input, stack)."""
        errors = []
        seen = {}

        for trans in dpda.transitions:
            key = (trans.from_state, trans.input_symbol, trans.stack_top)
            if key in seen:
                prev_trans = seen[key]
                input_str = trans.input_symbol if trans.input_symbol else 'epsilon'
                errors.append(
                    f"Property (a) violation: Multiple transitions for "
                    f"({trans.from_state}, {input_str}, {trans.stack_top}). "
                    f"Found transitions to states {prev_trans.to_state} and {trans.to_state}"
                )
            else:
                seen[key] = trans

        return errors

    def _check_property_b(self, dpda: DPDADefinition) -> List[str]:
        """Check property (b): no epsilon and non-epsilon from same (state, stack)."""
        errors = []

        # Group transitions by (from_state, stack_top)
        state_stack_groups: Dict[Tuple[str, str], List[Transition]] = {}
        for trans in dpda.transitions:
            key = (trans.from_state, trans.stack_top)
            if key not in state_stack_groups:
                state_stack_groups[key] = []
            state_stack_groups[key].append(trans)

        # Check each group
        for (state, stack), transitions in state_stack_groups.items():
            has_epsilon = any(t.is_epsilon for t in transitions)
            has_non_epsilon = any(not t.is_epsilon for t in transitions)

            if has_epsilon and has_non_epsilon:
                errors.append(
                    f"Property (b) violation: Both epsilon and non-epsilon transitions "
                    f"from state {state} with stack top {stack}"
                )

        return errors

    def _check_property_c(self, dpda: DPDADefinition) -> List[str]:
        """Check property (c): multiple epsilon transitions have disjoint stack requirements."""
        errors = []

        # Group epsilon transitions by from_state
        epsilon_by_state: Dict[str, List[Transition]] = {}
        for trans in dpda.transitions:
            if trans.is_epsilon:
                if trans.from_state not in epsilon_by_state:
                    epsilon_by_state[trans.from_state] = []
                epsilon_by_state[trans.from_state].append(trans)

        # Check each state's epsilon transitions
        for state, epsilon_trans in epsilon_by_state.items():
            if len(epsilon_trans) > 1:
                # Check for same stack top
                stack_tops = [t.stack_top for t in epsilon_trans]
                if len(stack_tops) != len(set(stack_tops)):
                    # Find duplicates
                    seen = set()
                    for stack_top in stack_tops:
                        if stack_top in seen:
                            errors.append(
                                f"Property (c) violation: Multiple epsilon transitions "
                                f"from state {state} with same stack top {stack_top}"
                            )
                            break
                        seen.add(stack_top)

        return errors

    def _check_property_d(self, dpda: DPDADefinition) -> List[str]:
        """Check property (d): all symbols and states in transitions are valid."""
        errors = []

        for trans in dpda.transitions:
            # Check from_state
            if trans.from_state not in dpda.states:
                errors.append(
                    f"Property (d) violation: Transition from invalid state '{trans.from_state}'"
                )

            # Check to_state
            if trans.to_state not in dpda.states:
                errors.append(
                    f"Property (d) violation: Transition to invalid state '{trans.to_state}'"
                )

            # Check input symbol
            if trans.input_symbol is not None and trans.input_symbol not in dpda.input_alphabet:
                errors.append(
                    f"Property (d) violation: Transition uses invalid input symbol '{trans.input_symbol}'"
                )

            # Check stack top
            if trans.stack_top not in dpda.stack_alphabet:
                errors.append(
                    f"Property (d) violation: Transition uses invalid stack symbol '{trans.stack_top}'"
                )

            # Check stack push symbols
            # Handle multi-character symbols: if no comma, treat as single symbol
            if trans.stack_push:  # Only check if not empty string
                if ',' in trans.stack_push:
                    # Comma-separated symbols
                    for symbol in trans.stack_push.split(','):
                        if symbol and symbol not in dpda.stack_alphabet:
                            errors.append(
                                f"Property (d) violation: Transition pushes invalid symbol '{symbol}' "
                                f"in push string '{trans.stack_push}'"
                            )
                else:
                    # Single symbol (could be multi-character)
                    if trans.stack_push not in dpda.stack_alphabet:
                        errors.append(
                            f"Property (d) violation: Transition pushes invalid symbol '{trans.stack_push}' "
                            f"not in stack alphabet"
                        )

        return errors