"""Pydantic models for API request and response validation."""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum


class CreateDPDARequest(BaseModel):
    """Request model for creating a new DPDA."""
    name: str = Field(..., min_length=1, description="Name of the DPDA")
    description: Optional[str] = Field(None, description="Optional description")


class CreateDPDAResponse(BaseModel):
    """Response model for DPDA creation."""
    id: str = Field(..., description="Unique identifier for the DPDA")
    name: str = Field(..., description="Name of the created DPDA")
    created: bool = Field(..., description="Whether creation was successful")
    message: str = Field(..., description="Status message")


class SetStatesRequest(BaseModel):
    """Request model for setting DPDA states."""
    states: List[str] = Field(..., min_length=1, description="List of state names")
    initial_state: str = Field(..., description="Initial state")
    accept_states: List[str] = Field(default_factory=list, description="Accept states")

    @field_validator('states')
    @classmethod
    def validate_unique_states(cls, v: List[str]) -> List[str]:
        """Ensure states are unique."""
        if len(v) != len(set(v)):
            raise ValueError("States must be unique")
        return v

    @model_validator(mode='after')
    def validate_state_membership(self) -> 'SetStatesRequest':
        """Validate that initial and accept states are in states list."""
        if self.initial_state not in self.states:
            raise ValueError(f"Initial state '{self.initial_state}' must be in states list")
        for state in self.accept_states:
            if state not in self.states:
                raise ValueError(f"Accept state '{state}' must be in states list")
        return self


class SetAlphabetsRequest(BaseModel):
    """Request model for setting DPDA alphabets."""
    input_alphabet: List[str] = Field(..., min_length=0, description="Input alphabet symbols")
    stack_alphabet: List[str] = Field(..., min_length=1, description="Stack alphabet symbols")
    initial_stack_symbol: str = Field(..., description="Initial stack symbol")

    @model_validator(mode='after')
    def validate_initial_symbol(self) -> 'SetAlphabetsRequest':
        """Validate initial stack symbol is in stack alphabet."""
        if self.initial_stack_symbol not in self.stack_alphabet:
            raise ValueError(f"Initial stack symbol '{self.initial_stack_symbol}' must be in stack alphabet")
        return self


class AddTransitionRequest(BaseModel):
    """Request model for adding a transition."""
    from_state: str = Field(..., description="Source state")
    input_symbol: Optional[str] = Field(None, description="Input symbol (None for epsilon)")
    stack_top: Optional[str] = Field(None, description="Stack top symbol (None for epsilon)")
    to_state: str = Field(..., description="Target state")
    stack_push: List[str] = Field(default_factory=list, description="Symbols to push onto stack")


class ComputeRequest(BaseModel):
    """Request model for computing string acceptance."""
    input_string: str = Field(..., description="Input string to process")
    max_steps: int = Field(10000, gt=0, description="Maximum computation steps")
    show_trace: bool = Field(False, description="Include computation trace in response")


class ComputeResponse(BaseModel):
    """Response model for computation results."""
    accepted: bool = Field(..., description="Whether the string was accepted")
    final_state: str = Field(..., description="Final state after computation")
    final_stack: List[str] = Field(..., description="Final stack contents")
    steps_taken: int = Field(..., description="Number of steps in computation")
    trace: Optional[List[Dict[str, Any]]] = Field(None, description="Computation trace if requested")
    reason: Optional[str] = Field(None, description="Rejection reason if not accepted")


class ValidationViolation(BaseModel):
    """Model for a validation violation."""
    type: str = Field(..., description="Violation type")
    state: Optional[str] = Field(None, description="State involved in violation")
    description: str = Field(..., description="Human-readable description")


class ValidationResponse(BaseModel):
    """Response model for DPDA validation."""
    is_valid: bool = Field(..., description="Whether the DPDA is valid")
    violations: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of violations if invalid"
    )
    message: str = Field(..., description="Summary message")


class DPDAInfoResponse(BaseModel):
    """Response model for DPDA information."""
    id: str = Field(..., description="DPDA identifier")
    name: str = Field(..., description="DPDA name")
    states: List[str] = Field(..., description="List of states")
    input_alphabet: List[str] = Field(..., description="Input alphabet")
    stack_alphabet: List[str] = Field(..., description="Stack alphabet")
    initial_state: str = Field(..., description="Initial state")
    initial_stack_symbol: str = Field(..., description="Initial stack symbol")
    accept_states: List[str] = Field(..., description="Accept states")
    num_transitions: int = Field(..., description="Number of transitions")
    is_complete: bool = Field(..., description="Whether DPDA is completely defined")
    is_valid: bool = Field(..., description="Whether DPDA is valid")


class ExportResponse(BaseModel):
    """Response model for DPDA export."""
    format: str = Field(..., description="Export format (json, xml, etc.)")
    data: Dict[str, Any] = Field(..., description="Exported DPDA data")
    version: str = Field(..., description="Export format version")


class VisualizationFormat(str, Enum):
    """Supported visualization formats."""
    DOT = "dot"
    D3 = "d3"
    CYTOSCAPE = "cytoscape"


class VisualizationResponse(BaseModel):
    """Response model for DPDA visualization."""
    format: str = Field(..., description="Visualization format")
    data: Union[str, Dict[str, Any]] = Field(..., description="Visualization data")


class ErrorResponse(BaseModel):
    """Response model for API errors."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class ListDPDAsResponse(BaseModel):
    """Response model for listing DPDAs."""
    dpdas: List[Dict[str, Any]] = Field(..., description="List of DPDA summaries")
    count: int = Field(..., description="Total count of DPDAs")


class DeleteTransitionResponse(BaseModel):
    """Response model for deleting a transition."""
    deleted: bool = Field(..., description="Whether deletion was successful")
    message: str = Field(..., description="Status message")
    remaining_transitions: int = Field(..., description="Number of remaining transitions")


class TransitionItem(BaseModel):
    """Model for a single transition item."""
    from_state: str = Field(..., description="Source state")
    input_symbol: Optional[str] = Field(None, description="Input symbol (None for epsilon)")
    stack_top: Optional[str] = Field(None, description="Stack top symbol (None for epsilon)")
    to_state: str = Field(..., description="Target state")
    stack_push: List[str] = Field(..., description="Symbols to push onto stack")


class TransitionsResponse(BaseModel):
    """Response model for getting transitions."""
    transitions: List[TransitionItem] = Field(..., description="List of transitions")
    total: int = Field(..., description="Total number of transitions")


class UpdateDPDARequest(BaseModel):
    """Request model for updating DPDA metadata."""
    name: Optional[str] = Field(None, min_length=1, description="New name for the DPDA")
    description: Optional[str] = Field(None, description="New description for the DPDA")


class UpdateDPDAResponse(BaseModel):
    """Response model for DPDA update."""
    id: str = Field(..., description="DPDA identifier")
    updated: bool = Field(..., description="Whether update was successful")
    message: str = Field(..., description="Status message")
    changes: Dict[str, Any] = Field(..., description="Dictionary of changed fields")


class UpdateStatesRequest(BaseModel):
    """Request model for partial update of DPDA states."""
    states: Optional[List[str]] = Field(None, min_length=1, description="New list of state names")
    initial_state: Optional[str] = Field(None, description="New initial state")
    accept_states: Optional[List[str]] = Field(None, description="New accept states")

    @field_validator('states')
    @classmethod
    def validate_unique_states(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Ensure states are unique if provided."""
        if v is not None and len(v) != len(set(v)):
            raise ValueError("States must be unique")
        return v

    @model_validator(mode='after')
    def validate_state_membership(self) -> 'UpdateStatesRequest':
        """Validate that initial and accept states are in states list if both provided."""
        if self.states is not None:
            if self.initial_state is not None and self.initial_state not in self.states:
                raise ValueError(f"Initial state '{self.initial_state}' must be in states list")
            if self.accept_states is not None:
                for state in self.accept_states:
                    if state not in self.states:
                        raise ValueError(f"Accept state '{state}' must be in states list")
        return self


class UpdateAlphabetsRequest(BaseModel):
    """Request model for partial update of DPDA alphabets."""
    input_alphabet: Optional[List[str]] = Field(None, description="New input alphabet symbols")
    stack_alphabet: Optional[List[str]] = Field(None, min_length=1, description="New stack alphabet symbols")
    initial_stack_symbol: Optional[str] = Field(None, description="New initial stack symbol")

    @model_validator(mode='after')
    def validate_initial_symbol(self) -> 'UpdateAlphabetsRequest':
        """Validate initial stack symbol is in stack alphabet if both provided."""
        if self.stack_alphabet is not None and self.initial_stack_symbol is not None:
            if self.initial_stack_symbol not in self.stack_alphabet:
                raise ValueError(f"Initial stack symbol '{self.initial_stack_symbol}' must be in stack alphabet")
        return self


class UpdateTransitionRequest(BaseModel):
    """Request model for updating a transition."""
    from_state: Optional[str] = Field(None, description="New source state")
    input_symbol: Optional[str] = Field(None, description="New input symbol (None for epsilon)")
    stack_top: Optional[str] = Field(None, description="New stack top symbol (None for epsilon)")
    to_state: Optional[str] = Field(None, description="New target state")
    stack_push: Optional[List[str]] = Field(None, description="New symbols to push onto stack")


class UpdateTransitionResponse(BaseModel):
    """Response model for transition update."""
    updated: bool = Field(..., description="Whether update was successful")
    message: str = Field(..., description="Status message")
    changes: Dict[str, Any] = Field(..., description="Dictionary of changed fields")