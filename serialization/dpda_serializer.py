"""
DPDA Serializer module.
Handles serialization and deserialization of DPDA definitions to/from various formats.
"""

import json
from typing import Dict, Any, List, Optional, Set
from pathlib import Path

from models.dpda_definition import DPDADefinition
from models.transition import Transition


class DPDASerializer:
    """Serializer for DPDA definitions."""

    CURRENT_VERSION = "1.0"
    SUPPORTED_VERSIONS = {"1.0"}

    def to_dict(self, dpda: DPDADefinition) -> Dict[str, Any]:
        """
        Convert a DPDA definition to a dictionary format.

        Args:
            dpda: The DPDA definition to serialize

        Returns:
            Dictionary representation with version and DPDA data
        """
        # Convert transitions to dictionaries
        transitions = []
        for trans in dpda.transitions:
            transitions.append({
                'from_state': trans.from_state,
                'input_symbol': trans.input_symbol,  # None for epsilon
                'stack_top': trans.stack_top,
                'to_state': trans.to_state,
                'stack_push': trans.stack_push
            })

        # Sort states and accept states for consistency
        sorted_states = sorted(list(dpda.states))
        sorted_accept_states = sorted(list(dpda.accept_states))
        sorted_input_alphabet = sorted(list(dpda.input_alphabet))
        sorted_stack_alphabet = sorted(list(dpda.stack_alphabet))

        dpda_dict = {
            'states': sorted_states,
            'input_alphabet': sorted_input_alphabet,
            'stack_alphabet': sorted_stack_alphabet,
            'initial_state': dpda.initial_state,
            'initial_stack_symbol': dpda.initial_stack_symbol,
            'accept_states': sorted_accept_states,
            'transitions': transitions
        }

        return {
            'version': self.CURRENT_VERSION,
            'dpda': dpda_dict
        }

    def from_dict(self, data: Dict[str, Any]) -> DPDADefinition:
        """
        Create a DPDA definition from a dictionary.

        Args:
            data: Dictionary containing version and DPDA data

        Returns:
            Reconstructed DPDA definition

        Raises:
            ValueError: If data is invalid or version unsupported
        """
        # Validate structure
        if 'version' not in data:
            raise ValueError("Missing version in serialized data")
        if 'dpda' not in data:
            raise ValueError("Missing dpda in serialized data")

        # Check version compatibility
        version = data['version']
        if version not in self.SUPPORTED_VERSIONS:
            raise ValueError(f"Unsupported version: {version}")

        dpda_data = data['dpda']

        # Validate required fields
        required_fields = [
            'states', 'input_alphabet', 'stack_alphabet',
            'initial_state', 'initial_stack_symbol',
            'accept_states', 'transitions'
        ]

        for field in required_fields:
            if field not in dpda_data:
                raise ValueError(f"Missing required field: {field}")

        # Convert lists back to sets
        states = set(dpda_data['states'])
        input_alphabet = set(dpda_data['input_alphabet'])
        stack_alphabet = set(dpda_data['stack_alphabet'])
        accept_states = set(dpda_data['accept_states'])

        # Recreate transitions
        transitions = []
        for trans_dict in dpda_data['transitions']:
            transition = Transition(
                from_state=trans_dict['from_state'],
                input_symbol=trans_dict['input_symbol'],  # None for epsilon
                stack_top=trans_dict['stack_top'],
                to_state=trans_dict['to_state'],
                stack_push=trans_dict['stack_push']
            )
            transitions.append(transition)

        # Create and return DPDA
        return DPDADefinition(
            states=states,
            input_alphabet=input_alphabet,
            stack_alphabet=stack_alphabet,
            initial_state=dpda_data['initial_state'],
            initial_stack_symbol=dpda_data['initial_stack_symbol'],
            accept_states=accept_states,
            transitions=transitions
        )

    def to_json(self, dpda: DPDADefinition, indent: Optional[int] = 2) -> str:
        """
        Convert a DPDA definition to JSON string.

        Args:
            dpda: The DPDA definition to serialize
            indent: Number of spaces for indentation (None for compact)

        Returns:
            JSON string representation
        """
        dpda_dict = self.to_dict(dpda)
        return json.dumps(dpda_dict, indent=indent)

    def from_json(self, json_str: str) -> DPDADefinition:
        """
        Create a DPDA definition from a JSON string.

        Args:
            json_str: JSON string containing DPDA data

        Returns:
            Reconstructed DPDA definition

        Raises:
            ValueError: If JSON is invalid or data is malformed
        """
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")

        return self.from_dict(data)

    def save_to_file(self, dpda: DPDADefinition, filepath: str) -> None:
        """
        Save a DPDA definition to a file.

        Args:
            dpda: The DPDA definition to save
            filepath: Path to the output file
        """
        json_str = self.to_json(dpda)
        path = Path(filepath)
        path.write_text(json_str)

    def load_from_file(self, filepath: str) -> DPDADefinition:
        """
        Load a DPDA definition from a file.

        Args:
            filepath: Path to the input file

        Returns:
            Loaded DPDA definition

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file contains invalid data
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        json_str = path.read_text()
        return self.from_json(json_str)