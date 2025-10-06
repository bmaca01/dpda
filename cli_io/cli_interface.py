"""
CLI interface for DPDA simulator.
Handles user interaction for setting up and running DPDA simulations.
"""

from typing import Set, List, Optional, Dict
from models.dpda_definition import DPDADefinition
from models.transition import Transition
from models.configuration import Configuration
from models.computation_result import ComputationResult
from core.dpda_engine import DPDAEngine
from validation.dpda_validator import DPDAValidator
from cli_io.formatter import OutputFormatter


class CLIInterface:
    """Manages command-line interaction for DPDA simulator."""

    def __init__(self):
        """Initialize CLI interface."""
        self.formatter = OutputFormatter()
        self.validator = DPDAValidator()
        self.engine = DPDAEngine()

    def collect_states(self) -> Set[str]:
        """
        Collect number of states from user input.

        Returns:
            Set of state names as strings ('0', '1', '2', ...)
        """
        while True:
            try:
                num_states = int(input("Enter number of states :\n"))
                # Return set of state names
                return {str(i) for i in range(num_states)}
            except ValueError:
                print("Invalid input: number of states must be int")
            except EOFError:
                raise  # Let the caller handle EOF

    def collect_input_alphabet(self) -> Set[str]:
        """
        Collect input alphabet from user.

        Returns:
            Set of input symbols
        """
        while True:
            user_input = input(
                "Enter input alphabet as a comma-separated list of symbols :\n"
            ).strip()

            if not user_input:
                print("Input alphabet can't be empty")
                continue

            # Split by comma and clean up whitespace
            symbols = {s.strip() for s in user_input.split(',') if s.strip()}

            if not symbols:
                print("Input alphabet can't be empty")
                continue

            return symbols

    def collect_accept_states(self, states: Set[str]) -> Set[str]:
        """
        Collect accept states from user.

        Args:
            states: Set of all states in the DPDA

        Returns:
            Set of accept state names
        """
        num_states = len(states)
        while True:
            try:
                user_input = input(
                    "Enter accepting states as a comma-separated list of integers :\n"
                ).strip()

                if not user_input:
                    # No accept states
                    return set()

                # Parse state numbers
                accept_nums = []
                state_nums = list(map(int, user_input.split(',')))

                # Check max value
                max_state = max(state_nums)
                if max_state >= num_states:
                    print(f"invalid state {max_state}; enter a value between 0 and {num_states - 1}")
                    continue

                for state_num in state_nums:
                    accept_nums.append(str(state_num))

                return set(accept_nums)

            except (ValueError, IndexError):
                print("Invalid input: accept state must be integers")

    def collect_transition(
        self,
        state: str,
        input_alphabet: Set[str],
        stack_alphabet: Set[str],
        num_states: int = None
    ) -> Optional[Transition]:
        """
        Collect a single transition from user.

        Args:
            state: Current state for which to add transition
            input_alphabet: Valid input symbols
            stack_alphabet: Valid stack symbols
            num_states: Total number of states

        Returns:
            Transition object or None if user doesn't want to add
        """
        # Ask if user wants to add a transition
        while True:
            response = input(
                f"Need a transition rule for state {state} ? (y or n)\n"
            ).strip().lower()

            if response == 'n':
                return None
            elif response == 'y':
                break
            else:
                print("Invalid input: must be 'y' or 'n'")

        # Collect input symbol
        while True:
            input_sym = input(
                "Input Symbol to read (enter - for epsilon, enter -- for '-'): "
            )

            # Convert '-' to None for epsilon, '--' to '-'
            if input_sym == '-':
                input_sym = None
                break
            elif input_sym == '--':
                input_sym = '-'
                if input_sym in input_alphabet:
                    break
                else:
                    print("Invalid input: symbol not in alphabet")
            elif input_sym == '':
                # Empty string also means epsilon
                input_sym = None
                break
            elif input_sym in input_alphabet:
                break
            else:
                print("Invalid input: symbol not in alphabet")

        # Collect stack top symbol
        while True:
            stack_top = input(
                "Stack symbol to match and pop (enter - for epsilon, enter -- for '-'): "
            )

            # Convert '-' to None for epsilon, '--' to '-'
            if stack_top == '-':
                stack_top = None
                break
            elif stack_top == '--':
                stack_top = '-'
                # Always add new stack symbols to alphabet
                stack_alphabet.add(stack_top)
                break
            elif stack_top == '':
                # Empty string also means epsilon
                stack_top = None
                break
            elif stack_top in stack_alphabet:
                break
            else:
                # Add new stack symbol to alphabet (like original)
                stack_alphabet.add(stack_top)
                break

        # Collect next state
        while True:
            try:
                next_state = int(input("State to transition to : "))
                if num_states and next_state >= num_states:
                    print(f"Invalid input: input greater than {num_states}")
                    continue
                next_state = str(next_state)
                break
            except ValueError:
                print("Invalid input: state must be integer")

        # Collect symbols to push (comma-separated like original)
        push_input = input(
            "Stack symbols to push as comma separated list, first symbol to top of stack (enter - for epsilon, enter -- for '-'): "
        )

        # Parse push symbols - handle special cases like original
        push_symbols = ''
        if push_input == '-':
            # Epsilon push - empty string
            push_symbols = ''
        elif push_input == '--':
            # Single dash character
            push_symbols = '-'
            stack_alphabet.add('-')
        elif push_input:
            # Parse comma-separated list
            symbols = []
            for s in push_input.split(','):
                if s == '--':
                    symbols.append('-')
                    stack_alphabet.add('-')
                else:
                    symbols.append(s)
                    stack_alphabet.add(s)
            # Keep symbols comma-separated for multi-symbol pushes
            # This preserves the boundaries between multi-char symbols
            if len(symbols) > 1:
                push_symbols = ','.join(symbols)
            else:
                # Single symbol, no comma needed
                push_symbols = symbols[0] if symbols else ''

        return Transition(state, input_sym, stack_top, next_state, push_symbols)

    def collect_all_transitions(
        self,
        states: Set[str],
        input_alphabet: Set[str],
        stack_alphabet: Set[str]
    ) -> List[Transition]:
        """
        Collect all transitions for the DPDA.

        Args:
            states: Set of all states
            input_alphabet: Set of input symbols
            stack_alphabet: Set of stack symbols

        Returns:
            List of transitions
        """
        transitions = []
        num_states = len(states)

        # Collect transitions for each state
        for state_num in sorted(states, key=int):
            print(f"Transitions for state {state_num}:")

            # Display existing transitions for this state (if any)
            state_transitions = [t for t in transitions if t.from_state == state_num]
            if state_transitions:
                for trans in state_transitions:
                    print(self.format_transition_display(trans))

            # Collect new transitions for this state
            while True:
                trans = self.collect_transition(
                    state_num,
                    input_alphabet,
                    stack_alphabet,
                    num_states
                )

                if trans is None:
                    break

                # Check for determinism violations
                violation_msg = self._check_determinism_violation(trans, transitions, state_num)
                if violation_msg:
                    print(violation_msg)
                    continue

                transitions.append(trans)
                # Update stack alphabet if new symbols introduced
                if trans.stack_push and trans.stack_push != '-':
                    # Split by comma to get individual symbols
                    symbols = trans.stack_push.split(',')
                    for symbol in symbols:
                        stack_alphabet.add(symbol)

        return transitions

    def _check_determinism_violation(
        self,
        new_trans: Transition,
        existing: List[Transition],
        state: str = None
    ) -> Optional[str]:
        """
        Check if adding a transition would violate DPDA determinism.

        Args:
            new_trans: New transition to add
            existing: List of existing transitions
            state: Current state (for error messages)

        Returns:
            Error message if violation would occur, None otherwise
        """
        for trans in existing:
            # Check for exact match (violation of property a)
            if (trans.from_state == new_trans.from_state and
                trans.input_symbol == new_trans.input_symbol and
                trans.stack_top == new_trans.stack_top):
                # Format transition for error message matching original
                trans_str = self.format_transition_display(trans)
                if new_trans.input_symbol is None and new_trans.stack_top is None:
                    # Epsilon/epsilon transition attempt
                    return f"Violation of DPDA due to epsilon input/epsilon stack transition from state {state or trans.from_state}:{trans_str}"
                elif new_trans.stack_top is None:
                    # Epsilon stack transition
                    return f"Violation of DPDA due to epsilon stack transition from state {state or trans.from_state}:{trans_str}"
                else:
                    # Multiple transitions for same input and stack
                    return f"Violation of DPDA due to multiple transitions for the same input and stack top from state {state or trans.from_state}:{trans_str}"

            # Check epsilon/non-epsilon conflict (property b)
            if trans.from_state == new_trans.from_state:
                if trans.stack_top == new_trans.stack_top:
                    # One has epsilon input, other doesn't
                    if (trans.input_symbol is None) != (new_trans.input_symbol is None):
                        if trans.input_symbol is None:
                            return f"Violation of DPDA: epsilon and non-epsilon transitions from same state {state or trans.from_state} with same stack"
                        else:
                            return f"Violation of DPDA: non-epsilon and epsilon transitions from same state {state or trans.from_state} with same stack"

                # Check for epsilon stack conflicts
                # Can't add epsilon stack transition if specific stack already exists
                if (trans.input_symbol == new_trans.input_symbol and
                    trans.stack_top is not None and new_trans.stack_top is None):
                    return f"Violation of DPDA due to epsilon stack transition from state {state or trans.from_state}:{self.format_transition_display(trans)}"

                # Can't add specific stack if epsilon stack already exists
                if (trans.input_symbol == new_trans.input_symbol and
                    trans.stack_top is None and new_trans.stack_top is not None):
                    return f"Violation of DPDA due to epsilon stack already exists from state {state or trans.from_state}:{self.format_transition_display(trans)}"

        return None

    def format_transition_display(self, transition: Transition) -> str:
        """
        Format a transition for display.

        Args:
            transition: Transition to format

        Returns:
            Formatted string
        """
        return self.formatter.format_transition(
            transition.input_symbol,
            transition.stack_top,
            transition.stack_push
        )

    def display_transitions(self, transitions: List[Transition], num_states: int):
        """
        Display all transitions grouped by state.

        Args:
            transitions: List of transitions
            num_states: Total number of states
        """
        for state_num in range(num_states):
            state = str(state_num)
            print(f"Transitions for state {state_num}:")

            state_transitions = [t for t in transitions if t.from_state == state]
            for trans in state_transitions:
                print(self.format_transition_display(trans))

    def process_input_string(self, dpda: DPDADefinition, engine: DPDAEngine):
        """
        Process an input string through the DPDA.

        Args:
            dpda: DPDA definition
            engine: Computation engine
        """
        # Get input string from user
        try:
            input_string = input("Enter an input string to be processed by the PDA : ")
        except EOFError:
            # EOF reached - exit gracefully without exception
            return False

        # Run computation
        result = engine.compute(dpda, input_string)

        # Display result
        print(f"Accept string {input_string}?", result.accepted)

        # Format and display trace
        # Note: We need to get transitions from the result or compute them separately
        if hasattr(result, 'configurations'):
            # For testing - mock object has these attributes
            trace = self.formatter.format_computation_trace(
                result.configurations,
                result.transitions,
                result.accepted
            )
            print(trace)
        elif result.trace:
            # For real ComputationResult - format the trace with transitions
            trace_str = ""
            for i, config in enumerate(result.trace):
                trace_str += self.formatter.format_configuration(config)
                if i < len(result.trace) - 1:
                    # Try to find the transition that was taken
                    curr_config = result.trace[i]
                    next_config = result.trace[i + 1]
                    transition_str = self._find_transition_between_configs(
                        dpda, curr_config, next_config
                    )
                    trace_str += f"--{transition_str}-->"
            print(trace_str)

        return True

    def _find_transition_between_configs(
        self,
        dpda,
        curr_config: 'Configuration',
        next_config: 'Configuration'
    ) -> str:
        """
        Find and format the transition taken between two configurations.

        Args:
            dpda: The DPDA definition
            curr_config: Current configuration
            next_config: Next configuration

        Returns:
            Formatted transition string like "[a,$->X]"
        """
        # Determine what input was consumed
        if len(curr_config.remaining_input) > len(next_config.remaining_input):
            input_consumed = curr_config.remaining_input[0]
        else:
            input_consumed = None  # Epsilon transition

        # Determine what was on stack top
        if curr_config.stack:
            stack_top = curr_config.stack[0]
        else:
            stack_top = None

        # Find matching transition in DPDA
        for trans in dpda.transitions:
            if (trans.from_state == curr_config.state and
                trans.input_symbol == input_consumed and
                trans.stack_top == stack_top and
                trans.to_state == next_config.state):
                # Found the transition - format it
                return self.formatter.format_transition(trans)

        # If no exact match found, create a generic transition string
        input_str = input_consumed if input_consumed else 'eps'
        stack_str = stack_top if stack_top else 'eps'
        # Determine what was pushed
        if len(next_config.stack) > len(curr_config.stack) - 1:
            # Something was pushed
            pushed = next_config.stack[:len(next_config.stack) - len(curr_config.stack) + 1]
            push_str = ','.join(reversed(pushed)) if pushed else 'eps'
        else:
            push_str = 'eps'

        return f"[{input_str},{stack_str}->{push_str}]"

    def run_interactive_session(self):
        """Run a complete interactive DPDA session."""
        try:
            # Collect DPDA components
            states = self.collect_states()
            input_alphabet = self.collect_input_alphabet()

            # Stack alphabet starts with input alphabet (original behavior)
            # Don't pre-add Z - let it be added through transitions
            stack_alphabet = input_alphabet.copy()

            accept_states = self.collect_accept_states(states)

            # Collect transitions
            transitions = self.collect_all_transitions(
                states, input_alphabet, stack_alphabet
            )

            # Display all transitions
            self.display_transitions(transitions, len(states))

            # The original DPDA starts with an EMPTY stack
            initial_stack = ''

            # Add empty string to stack alphabet to allow empty stack
            stack_alphabet.add('')

            # Create DPDA definition
            dpda = DPDADefinition(
                states=states,
                input_alphabet=input_alphabet,
                stack_alphabet=stack_alphabet,
                initial_state='0',
                initial_stack_symbol=initial_stack,
                accept_states=accept_states,
                transitions=transitions
            )

            # Validate DPDA but don't block on stack alphabet issues
            # The original allows transitions to use any stack symbols
            result = self.validator.validate(dpda)
            if not result.is_valid:
                # Filter out stack alphabet errors - the original allows this
                critical_errors = [e for e in result.errors if "stack symbol" not in e.lower()]
                if critical_errors:
                    print("DPDA validation failed:")
                    for error in critical_errors:
                        print(f"  - {error}")
                    return

            # Process input strings
            while True:
                try:
                    if not self.process_input_string(dpda, self.engine):
                        # EOF reached, exit gracefully
                        print("")
                        break
                except KeyboardInterrupt:
                    print("\nExiting...")
                    break
                except Exception as e:
                    print(f"Error processing string: {e}")

        except (KeyboardInterrupt, EOFError):
            # Exit gracefully without exception message
            print("")
        except Exception as e:
            print(f"Error during setup: {e}")