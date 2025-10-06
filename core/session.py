"""
DPDA Session Management module.
Provides stateful session handling for building and managing multiple DPDAs.
"""

import json
from typing import Dict, Set, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, field

from models.dpda_definition import DPDADefinition
from models.transition import Transition
from validation.dpda_validator import DPDAValidator, ValidationResult
from serialization.dpda_serializer import DPDASerializer


class SessionError(Exception):
    """Custom exception for session-related errors."""
    pass


@dataclass
class DPDABuilder:
    """Builder class for incrementally constructing a DPDA."""
    states: Set[str] = field(default_factory=set)
    input_alphabet: Set[str] = field(default_factory=set)
    stack_alphabet: Set[str] = field(default_factory=set)
    initial_state: Optional[str] = None
    initial_stack_symbol: Optional[str] = None
    accept_states: Set[str] = field(default_factory=set)
    transitions: List[Transition] = field(default_factory=list)

    def clear(self):
        """Clear all builder data."""
        self.states.clear()
        self.input_alphabet.clear()
        self.stack_alphabet.clear()
        self.initial_state = None
        self.initial_stack_symbol = None
        self.accept_states.clear()
        self.transitions.clear()

    def copy(self) -> 'DPDABuilder':
        """Create a deep copy of this builder."""
        return DPDABuilder(
            states=self.states.copy(),
            input_alphabet=self.input_alphabet.copy(),
            stack_alphabet=self.stack_alphabet.copy(),
            initial_state=self.initial_state,
            initial_stack_symbol=self.initial_stack_symbol,
            accept_states=self.accept_states.copy(),
            transitions=self.transitions.copy()
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert builder to dictionary for serialization."""
        return {
            'states': sorted(list(self.states)),
            'input_alphabet': sorted(list(self.input_alphabet)),
            'stack_alphabet': sorted(list(self.stack_alphabet)),
            'initial_state': self.initial_state,
            'initial_stack_symbol': self.initial_stack_symbol,
            'accept_states': sorted(list(self.accept_states)),
            'transitions': [
                {
                    'from_state': t.from_state,
                    'input_symbol': t.input_symbol,
                    'stack_top': t.stack_top,
                    'to_state': t.to_state,
                    'stack_push': t.stack_push
                }
                for t in self.transitions
            ]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DPDABuilder':
        """Create builder from dictionary."""
        builder = cls()
        builder.states = set(data.get('states', []))
        builder.input_alphabet = set(data.get('input_alphabet', []))
        builder.stack_alphabet = set(data.get('stack_alphabet', []))
        builder.initial_state = data.get('initial_state')
        builder.initial_stack_symbol = data.get('initial_stack_symbol')
        builder.accept_states = set(data.get('accept_states', []))

        # Recreate transitions
        for trans_dict in data.get('transitions', []):
            transition = Transition(
                from_state=trans_dict['from_state'],
                input_symbol=trans_dict['input_symbol'],
                stack_top=trans_dict['stack_top'],
                to_state=trans_dict['to_state'],
                stack_push=trans_dict['stack_push']
            )
            builder.transitions.append(transition)

        return builder


class DPDASession:
    """
    Session manager for DPDA construction and management.

    Allows incremental building of multiple DPDAs with save/load functionality.
    """

    def __init__(self, name: str):
        """
        Initialize a new DPDA session.

        Args:
            name: Name of the session
        """
        self.name = name
        self.dpdas: Dict[str, DPDABuilder] = {}
        self.current_dpda_name: Optional[str] = None
        self.is_modified = False
        self._validator = DPDAValidator()

    @property
    def current_dpda(self) -> Optional[DPDABuilder]:
        """Get the current DPDA builder."""
        if self.current_dpda_name and self.current_dpda_name in self.dpdas:
            return self.dpdas[self.current_dpda_name]
        return None

    def new_dpda(self, name: str) -> None:
        """
        Create a new DPDA in the session.

        Args:
            name: Name for the new DPDA

        Raises:
            SessionError: If name already exists
        """
        if name in self.dpdas:
            raise SessionError(f"DPDA '{name}' already exists in session")

        self.dpdas[name] = DPDABuilder()
        self.current_dpda_name = name
        self.is_modified = True

    def get_current_builder(self) -> DPDABuilder:
        """
        Get the current DPDA builder.

        Returns:
            Current DPDABuilder instance

        Raises:
            SessionError: If no current DPDA
        """
        if self.current_dpda is None:
            raise SessionError("No current DPDA selected")
        return self.current_dpda

    def set_states(self, states: Set[str]) -> None:
        """Set states for current DPDA."""
        builder = self.get_current_builder()
        builder.states = states.copy()
        self.is_modified = True

    def set_input_alphabet(self, alphabet: Set[str]) -> None:
        """Set input alphabet for current DPDA."""
        builder = self.get_current_builder()
        builder.input_alphabet = alphabet.copy()
        self.is_modified = True

    def set_stack_alphabet(self, alphabet: Set[str]) -> None:
        """Set stack alphabet for current DPDA."""
        builder = self.get_current_builder()
        builder.stack_alphabet = alphabet.copy()
        self.is_modified = True

    def set_initial_state(self, state: str) -> None:
        """
        Set initial state for current DPDA.

        Raises:
            SessionError: If state not in states
        """
        builder = self.get_current_builder()
        if state not in builder.states:
            raise SessionError(f"State '{state}' not in states")
        builder.initial_state = state
        self.is_modified = True

    def set_initial_stack_symbol(self, symbol: str) -> None:
        """
        Set initial stack symbol for current DPDA.

        Raises:
            SessionError: If symbol not in stack alphabet
        """
        builder = self.get_current_builder()
        if symbol not in builder.stack_alphabet:
            raise SessionError(f"Symbol '{symbol}' not in stack alphabet")
        builder.initial_stack_symbol = symbol
        self.is_modified = True

    def set_accept_states(self, states: Set[str]) -> None:
        """
        Set accept states for current DPDA.

        Raises:
            SessionError: If any state not in states
        """
        builder = self.get_current_builder()
        invalid = states - builder.states
        if invalid:
            raise SessionError(f"States {invalid} not in states")
        builder.accept_states = states.copy()
        self.is_modified = True

    def add_transition(self, from_state: str, input_symbol: Optional[str],
                      stack_top: Optional[str], to_state: str, stack_push: str) -> None:
        """
        Add a transition to current DPDA.

        Args:
            from_state: Source state
            input_symbol: Input symbol (None for epsilon)
            stack_top: Stack symbol to match (None for epsilon - no stack check)
            to_state: Target state
            stack_push: Stack symbols to push
        """
        builder = self.get_current_builder()
        transition = Transition(from_state, input_symbol, stack_top,
                               to_state, stack_push)
        builder.transitions.append(transition)
        self.is_modified = True

    def remove_transition(self, index: int) -> None:
        """
        Remove a transition by index.

        Args:
            index: Index of transition to remove

        Raises:
            IndexError: If index out of range
        """
        builder = self.get_current_builder()
        if index < 0 or index >= len(builder.transitions):
            raise IndexError(f"Transition index {index} out of range")
        del builder.transitions[index]
        self.is_modified = True

    def build_current_dpda(self) -> DPDADefinition:
        """
        Build a DPDADefinition from current builder.

        Returns:
            Complete DPDA definition

        Raises:
            SessionError: If required fields are missing
        """
        builder = self.get_current_builder()

        # Validate required fields
        if not builder.states:
            raise SessionError("States not set")
        if builder.initial_state is None:
            raise SessionError("Initial state not set")
        if not builder.stack_alphabet:
            raise SessionError("Stack alphabet not set")
        if builder.initial_stack_symbol is None:
            raise SessionError("Initial stack symbol not set")

        return DPDADefinition(
            states=builder.states.copy(),
            input_alphabet=builder.input_alphabet.copy(),
            stack_alphabet=builder.stack_alphabet.copy(),
            initial_state=builder.initial_state,
            initial_stack_symbol=builder.initial_stack_symbol,
            accept_states=builder.accept_states.copy(),
            transitions=builder.transitions.copy()
        )

    def validate_current(self) -> ValidationResult:
        """
        Validate the current DPDA being built.

        Returns:
            ValidationResult with any errors found
        """
        try:
            dpda = self.build_current_dpda()
            return self._validator.validate(dpda)
        except SessionError as e:
            # If can't build, return error
            result = ValidationResult()
            result.is_valid = False
            result.errors.append(str(e))
            return result

    def switch_to(self, name: str) -> None:
        """
        Switch to a different DPDA.

        Args:
            name: Name of DPDA to switch to

        Raises:
            SessionError: If DPDA not found
        """
        if name not in self.dpdas:
            raise SessionError(f"DPDA '{name}' not found in session")
        self.current_dpda_name = name

    def delete_dpda(self, name: str) -> None:
        """
        Delete a DPDA from the session.

        Args:
            name: Name of DPDA to delete

        Raises:
            SessionError: If DPDA not found
        """
        if name not in self.dpdas:
            raise SessionError(f"DPDA '{name}' not found")

        del self.dpdas[name]
        self.is_modified = True

        # If deleted current, clear selection
        if self.current_dpda_name == name:
            self.current_dpda_name = None

    def rename_dpda(self, old_name: str, new_name: str) -> None:
        """
        Rename a DPDA.

        Args:
            old_name: Current name
            new_name: New name

        Raises:
            SessionError: If old name not found or new name exists
        """
        if old_name not in self.dpdas:
            raise SessionError(f"DPDA '{old_name}' not found")
        if new_name in self.dpdas:
            raise SessionError(f"DPDA '{new_name}' already exists")

        self.dpdas[new_name] = self.dpdas[old_name]
        del self.dpdas[old_name]

        if self.current_dpda_name == old_name:
            self.current_dpda_name = new_name

        self.is_modified = True

    def clear_current(self) -> None:
        """Clear the current DPDA builder."""
        builder = self.get_current_builder()
        builder.clear()
        self.is_modified = True

    def copy_dpda(self, source: str, target: str) -> None:
        """
        Copy a DPDA to a new name.

        Args:
            source: Name of DPDA to copy
            target: Name for the copy

        Raises:
            SessionError: If source not found or target exists
        """
        if source not in self.dpdas:
            raise SessionError(f"DPDA '{source}' not found")
        if target in self.dpdas:
            raise SessionError(f"DPDA '{target}' already exists")

        self.dpdas[target] = self.dpdas[source].copy()
        self.is_modified = True

    def get_dpda_list(self) -> List[str]:
        """Get list of all DPDA names in session."""
        return list(self.dpdas.keys())

    def save_to_file(self, filepath: str) -> None:
        """
        Save session to a file.

        Args:
            filepath: Path to save file
        """
        data = {
            'version': '1.0',
            'session_name': self.name,
            'current_dpda': self.current_dpda_name,
            'dpdas': {
                name: builder.to_dict()
                for name, builder in self.dpdas.items()
            }
        }

        path = Path(filepath)
        path.write_text(json.dumps(data, indent=2))
        self.is_modified = False

    @classmethod
    def load_from_file(cls, filepath: str) -> 'DPDASession':
        """
        Load session from a file.

        Args:
            filepath: Path to load from

        Returns:
            Loaded DPDASession instance

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format invalid
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Session file not found: {filepath}")

        data = json.loads(path.read_text())

        # Validate version
        if 'version' not in data:
            raise ValueError("Missing version in session file")
        if data['version'] != '1.0':
            raise ValueError(f"Unsupported session version: {data['version']}")

        # Create session
        session = cls(data.get('session_name', 'unnamed'))

        # Load DPDAs
        for name, builder_data in data.get('dpdas', {}).items():
            session.dpdas[name] = DPDABuilder.from_dict(builder_data)

        # Set current DPDA
        if data.get('current_dpda') in session.dpdas:
            session.current_dpda_name = data['current_dpda']

        session.is_modified = False
        return session