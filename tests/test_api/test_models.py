"""Tests for API Pydantic models."""

import pytest
from typing import Dict, List, Optional, Any
import json


class TestAPIModels:
    """Test suite for API request/response models."""

    def test_create_dpda_request(self):
        """Test CreateDPDARequest model."""
        from api.models import CreateDPDARequest

        # Valid request
        data = {"name": "test_dpda"}
        request = CreateDPDARequest(**data)
        assert request.name == "test_dpda"

        # Optional description
        data_with_desc = {"name": "test_dpda", "description": "A test DPDA"}
        request = CreateDPDARequest(**data_with_desc)
        assert request.description == "A test DPDA"

    def test_create_dpda_response(self):
        """Test CreateDPDAResponse model."""
        from api.models import CreateDPDAResponse

        response = CreateDPDAResponse(
            id="dpda_123",
            name="test_dpda",
            created=True,
            message="DPDA created successfully"
        )
        assert response.id == "dpda_123"
        assert response.created is True

    def test_set_states_request(self):
        """Test SetStatesRequest model."""
        from api.models import SetStatesRequest

        # Valid request with all fields
        data = {
            "states": ["q0", "q1", "q2"],
            "initial_state": "q0",
            "accept_states": ["q2"]
        }
        request = SetStatesRequest(**data)
        assert len(request.states) == 3
        assert request.initial_state == "q0"
        assert request.accept_states == ["q2"]

        # States must be non-empty
        with pytest.raises(ValueError):
            SetStatesRequest(states=[], initial_state="q0")

        # Initial state must be in states
        with pytest.raises(ValueError):
            SetStatesRequest(
                states=["q0", "q1"],
                initial_state="q3",
                accept_states=[]
            )

    def test_set_alphabets_request(self):
        """Test SetAlphabetsRequest model."""
        from api.models import SetAlphabetsRequest

        # Valid request
        data = {
            "input_alphabet": ["0", "1"],
            "stack_alphabet": ["A", "B", "$"],
            "initial_stack_symbol": "$"
        }
        request = SetAlphabetsRequest(**data)
        assert len(request.input_alphabet) == 2
        assert "$" in request.stack_alphabet

        # Initial stack symbol must be in stack alphabet
        with pytest.raises(ValueError):
            SetAlphabetsRequest(
                input_alphabet=["0", "1"],
                stack_alphabet=["A", "B"],
                initial_stack_symbol="$"
            )

    def test_add_transition_request(self):
        """Test AddTransitionRequest model."""
        from api.models import AddTransitionRequest

        # Valid transition
        data = {
            "from_state": "q0",
            "input_symbol": "0",
            "stack_top": "$",
            "to_state": "q1",
            "stack_push": ["0", "$"]
        }
        request = AddTransitionRequest(**data)
        assert request.from_state == "q0"
        assert request.stack_push == ["0", "$"]

        # Epsilon transitions
        epsilon_data = {
            "from_state": "q1",
            "input_symbol": None,
            "stack_top": None,
            "to_state": "q2",
            "stack_push": []
        }
        request = AddTransitionRequest(**epsilon_data)
        assert request.input_symbol is None
        assert request.stack_push == []

    def test_compute_request(self):
        """Test ComputeRequest model."""
        from api.models import ComputeRequest

        # Valid request
        data = {
            "input_string": "0011",
            "max_steps": 1000,
            "show_trace": True
        }
        request = ComputeRequest(**data)
        assert request.input_string == "0011"
        assert request.max_steps == 1000

        # Default values
        minimal_data = {"input_string": ""}
        request = ComputeRequest(**minimal_data)
        assert request.max_steps == 10000  # default
        assert request.show_trace is False  # default

    def test_compute_response(self):
        """Test ComputeResponse model."""
        from api.models import ComputeResponse

        # Accepted response with trace
        response = ComputeResponse(
            accepted=True,
            final_state="q2",
            final_stack=[],
            steps_taken=5,
            trace=[
                {"state": "q0", "input": "0011", "stack": ["$"]},
                {"state": "q1", "input": "011", "stack": ["0", "$"]}
            ]
        )
        assert response.accepted is True
        assert len(response.trace) == 2

        # Rejected response without trace
        response = ComputeResponse(
            accepted=False,
            final_state="q1",
            final_stack=["0", "$"],
            steps_taken=3,
            reason="No valid transition"
        )
        assert response.reason == "No valid transition"

    def test_validation_response(self):
        """Test ValidationResponse model."""
        from api.models import ValidationResponse

        # Valid DPDA
        response = ValidationResponse(
            is_valid=True,
            violations=[],
            message="DPDA is deterministic"
        )
        assert response.is_valid is True
        assert len(response.violations) == 0

        # Invalid DPDA with violations
        response = ValidationResponse(
            is_valid=False,
            violations=[
                {
                    "type": "PROPERTY_A",
                    "state": "q1",
                    "description": "State has both ε-ε and other transitions"
                }
            ],
            message="DPDA violates determinism properties"
        )
        assert response.is_valid is False
        assert response.violations[0]["type"] == "PROPERTY_A"

    def test_dpda_info_response(self):
        """Test DPDAInfoResponse model."""
        from api.models import DPDAInfoResponse

        response = DPDAInfoResponse(
            id="dpda_123",
            name="test_dpda",
            states=["q0", "q1", "q2"],
            input_alphabet=["0", "1"],
            stack_alphabet=["$", "0", "1"],
            initial_state="q0",
            initial_stack_symbol="$",
            accept_states=["q2"],
            num_transitions=5,
            is_complete=True,
            is_valid=True
        )
        assert response.num_transitions == 5
        assert response.is_complete is True

    def test_export_response(self):
        """Test ExportResponse model."""
        from api.models import ExportResponse

        dpda_data = {
            "states": ["q0", "q1"],
            "input_alphabet": ["0", "1"],
            "transitions": []
        }
        response = ExportResponse(
            format="json",
            data=dpda_data,
            version="1.0"
        )
        assert response.format == "json"
        assert response.version == "1.0"

        # Can serialize to JSON
        json_str = response.model_dump_json()
        assert "transitions" in json_str

    def test_visualization_response(self):
        """Test VisualizationResponse model."""
        from api.models import VisualizationResponse

        # DOT format
        dot_response = VisualizationResponse(
            format="dot",
            data="digraph G { q0 -> q1 }"
        )
        assert dot_response.format == "dot"
        assert "digraph" in dot_response.data

        # D3.js format
        d3_response = VisualizationResponse(
            format="d3",
            data={
                "nodes": [{"id": "q0"}, {"id": "q1"}],
                "links": [{"source": "q0", "target": "q1"}]
            }
        )
        assert d3_response.format == "d3"
        assert len(d3_response.data["nodes"]) == 2

    def test_error_response(self):
        """Test ErrorResponse model."""
        from api.models import ErrorResponse

        response = ErrorResponse(
            error="ValidationError",
            message="Invalid state name",
            details={"field": "initial_state", "value": "q99"}
        )
        assert response.error == "ValidationError"
        assert response.details["field"] == "initial_state"

    def test_list_dpdas_response(self):
        """Test ListDPDAsResponse model."""
        from api.models import ListDPDAsResponse

        response = ListDPDAsResponse(
            dpdas=[
                {"id": "dpda_1", "name": "0n1n", "is_valid": True},
                {"id": "dpda_2", "name": "palindrome", "is_valid": False}
            ],
            count=2
        )
        assert response.count == 2
        assert response.dpdas[0]["name"] == "0n1n"

    def test_delete_transition_response(self):
        """Test DeleteTransitionResponse model."""
        from api.models import DeleteTransitionResponse

        response = DeleteTransitionResponse(
            deleted=True,
            message="Transition removed successfully",
            remaining_transitions=4
        )
        assert response.deleted is True
        assert response.remaining_transitions == 4

    def test_model_validation_constraints(self):
        """Test model validation constraints."""
        from api.models import ComputeRequest, SetStatesRequest

        # Max steps must be positive
        with pytest.raises(ValueError):
            ComputeRequest(input_string="test", max_steps=-1)

        # States must be unique
        with pytest.raises(ValueError):
            SetStatesRequest(
                states=["q0", "q1", "q0"],
                initial_state="q0"
            )

    def test_model_json_serialization(self):
        """Test that all models can be serialized to JSON."""
        from api.models import (
            CreateDPDARequest,
            AddTransitionRequest,
            ComputeResponse
        )

        # Request model
        request = CreateDPDARequest(name="test")
        json_data = request.model_dump_json()
        assert '"name":"test"' in json_data

        # Complex response model
        response = ComputeResponse(
            accepted=True,
            final_state="q2",
            final_stack=[],
            steps_taken=10,
            trace=[{"state": "q0", "input": "01", "stack": ["$"]}]
        )
        json_data = response.model_dump_json()
        parsed = json.loads(json_data)
        assert parsed["accepted"] is True
        assert len(parsed["trace"]) == 1