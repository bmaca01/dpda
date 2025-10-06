"""Tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient
import json
from typing import Dict, Any


class TestAPIEndpoints:
    """Test suite for FastAPI endpoints."""

    @pytest.fixture
    def client(self):
        """Create a test client for the FastAPI app."""
        from api.endpoints import app
        return TestClient(app)

    @pytest.fixture
    def sample_dpda_id(self, client):
        """Create a sample DPDA and return its ID."""
        response = client.post("/api/dpda/create", json={"name": "test_dpda"})
        return response.json()["id"]

    def test_create_dpda_endpoint(self, client):
        """Test creating a new DPDA."""
        # Create DPDA
        response = client.post(
            "/api/dpda/create",
            json={"name": "0n1n", "description": "Accepts 0^n1^n"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["created"] is True
        assert data["name"] == "0n1n"
        assert "id" in data

        # Create without description
        response = client.post("/api/dpda/create", json={"name": "simple"})
        assert response.status_code == 200

        # Invalid request (missing name)
        response = client.post("/api/dpda/create", json={})
        assert response.status_code == 422

    def test_get_dpda_info(self, client, sample_dpda_id):
        """Test getting DPDA information."""
        # Get existing DPDA
        response = client.get(f"/api/dpda/{sample_dpda_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_dpda_id
        assert data["name"] == "test_dpda"

        # Get non-existent DPDA
        response = client.get("/api/dpda/invalid_id")
        assert response.status_code == 404

    def test_set_states_endpoint(self, client, sample_dpda_id):
        """Test setting DPDA states."""
        # Valid states configuration
        states_data = {
            "states": ["q0", "q1", "q2"],
            "initial_state": "q0",
            "accept_states": ["q2"]
        }
        response = client.post(
            f"/api/dpda/{sample_dpda_id}/states",
            json=states_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Invalid: initial state not in states
        invalid_data = {
            "states": ["q0", "q1"],
            "initial_state": "q3",
            "accept_states": []
        }
        response = client.post(
            f"/api/dpda/{sample_dpda_id}/states",
            json=invalid_data
        )
        assert response.status_code == 400

    def test_set_alphabets_endpoint(self, client, sample_dpda_id):
        """Test setting DPDA alphabets."""
        # Valid alphabets
        alphabet_data = {
            "input_alphabet": ["0", "1"],
            "stack_alphabet": ["X", "Y", "$"],
            "initial_stack_symbol": "$"
        }
        response = client.post(
            f"/api/dpda/{sample_dpda_id}/alphabets",
            json=alphabet_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Invalid: initial symbol not in stack alphabet
        invalid_data = {
            "input_alphabet": ["a", "b"],
            "stack_alphabet": ["A", "B"],
            "initial_stack_symbol": "$"
        }
        response = client.post(
            f"/api/dpda/{sample_dpda_id}/alphabets",
            json=invalid_data
        )
        assert response.status_code == 400

    def test_add_transition_endpoint(self, client, sample_dpda_id):
        """Test adding transitions."""
        # Set up states and alphabets first
        client.post(f"/api/dpda/{sample_dpda_id}/states", json={
            "states": ["q0", "q1", "q2"],
            "initial_state": "q0",
            "accept_states": ["q2"]
        })
        client.post(f"/api/dpda/{sample_dpda_id}/alphabets", json={
            "input_alphabet": ["0", "1"],
            "stack_alphabet": ["$", "X"],
            "initial_stack_symbol": "$"
        })

        # Add valid transition
        transition_data = {
            "from_state": "q0",
            "input_symbol": "0",
            "stack_top": "$",
            "to_state": "q1",
            "stack_push": ["X", "$"]
        }
        response = client.post(
            f"/api/dpda/{sample_dpda_id}/transition",
            json=transition_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["added"] is True

        # Add epsilon transition
        epsilon_transition = {
            "from_state": "q1",
            "input_symbol": None,
            "stack_top": "X",
            "to_state": "q2",
            "stack_push": []
        }
        response = client.post(
            f"/api/dpda/{sample_dpda_id}/transition",
            json=epsilon_transition
        )
        assert response.status_code == 200

    def test_delete_transition_endpoint(self, client, sample_dpda_id):
        """Test deleting transitions."""
        # Setup and add transitions
        client.post(f"/api/dpda/{sample_dpda_id}/states", json={
            "states": ["q0", "q1"],
            "initial_state": "q0",
            "accept_states": []
        })
        client.post(f"/api/dpda/{sample_dpda_id}/alphabets", json={
            "input_alphabet": ["a"],
            "stack_alphabet": ["$"],
            "initial_stack_symbol": "$"
        })
        client.post(f"/api/dpda/{sample_dpda_id}/transition", json={
            "from_state": "q0",
            "input_symbol": "a",
            "stack_top": "$",
            "to_state": "q1",
            "stack_push": ["$"]
        })

        # Delete transition
        response = client.delete(f"/api/dpda/{sample_dpda_id}/transition/0")
        assert response.status_code == 200
        data = response.json()
        assert data["deleted"] is True
        assert data["remaining_transitions"] == 0

        # Delete non-existent transition
        response = client.delete(f"/api/dpda/{sample_dpda_id}/transition/99")
        assert response.status_code == 404

    def test_compute_endpoint(self, client, sample_dpda_id):
        """Test string computation."""
        # Build a simple 0^n1^n DPDA
        client.post(f"/api/dpda/{sample_dpda_id}/states", json={
            "states": ["q0", "q1", "q2"],
            "initial_state": "q0",
            "accept_states": ["q2"]
        })
        client.post(f"/api/dpda/{sample_dpda_id}/alphabets", json={
            "input_alphabet": ["0", "1"],
            "stack_alphabet": ["$", "X"],
            "initial_stack_symbol": "$"
        })
        # Add transitions for 0^n1^n
        client.post(f"/api/dpda/{sample_dpda_id}/transition", json={
            "from_state": "q0", "input_symbol": "0", "stack_top": "$",
            "to_state": "q0", "stack_push": ["X", "$"]
        })
        client.post(f"/api/dpda/{sample_dpda_id}/transition", json={
            "from_state": "q0", "input_symbol": "0", "stack_top": "X",
            "to_state": "q0", "stack_push": ["X", "X"]
        })
        client.post(f"/api/dpda/{sample_dpda_id}/transition", json={
            "from_state": "q0", "input_symbol": "1", "stack_top": "X",
            "to_state": "q1", "stack_push": []
        })
        client.post(f"/api/dpda/{sample_dpda_id}/transition", json={
            "from_state": "q1", "input_symbol": "1", "stack_top": "X",
            "to_state": "q1", "stack_push": []
        })
        client.post(f"/api/dpda/{sample_dpda_id}/transition", json={
            "from_state": "q1", "input_symbol": None, "stack_top": "$",
            "to_state": "q2", "stack_push": []
        })

        # Test accepted string
        response = client.post(
            f"/api/dpda/{sample_dpda_id}/compute",
            json={"input_string": "0011", "show_trace": False}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["accepted"] is True
        assert data["final_state"] == "q2"

        # Test rejected string
        response = client.post(
            f"/api/dpda/{sample_dpda_id}/compute",
            json={"input_string": "001", "show_trace": True}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["accepted"] is False
        assert data["trace"] is not None
        assert len(data["trace"]) > 0

    def test_validate_endpoint(self, client, sample_dpda_id):
        """Test DPDA validation."""
        # Setup a valid DPDA
        client.post(f"/api/dpda/{sample_dpda_id}/states", json={
            "states": ["q0", "q1"],
            "initial_state": "q0",
            "accept_states": ["q1"]
        })
        client.post(f"/api/dpda/{sample_dpda_id}/alphabets", json={
            "input_alphabet": ["a"],
            "stack_alphabet": ["$"],
            "initial_stack_symbol": "$"
        })
        client.post(f"/api/dpda/{sample_dpda_id}/transition", json={
            "from_state": "q0", "input_symbol": "a", "stack_top": "$",
            "to_state": "q1", "stack_push": []
        })

        # Validate
        response = client.post(f"/api/dpda/{sample_dpda_id}/validate")
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True
        assert len(data["violations"]) == 0

    def test_export_endpoint(self, client, sample_dpda_id):
        """Test DPDA export."""
        # Setup DPDA
        client.post(f"/api/dpda/{sample_dpda_id}/states", json={
            "states": ["q0", "q1"],
            "initial_state": "q0",
            "accept_states": ["q1"]
        })
        client.post(f"/api/dpda/{sample_dpda_id}/alphabets", json={
            "input_alphabet": ["a"],
            "stack_alphabet": ["$"],
            "initial_stack_symbol": "$"
        })

        # Export as JSON
        response = client.get(f"/api/dpda/{sample_dpda_id}/export?format=json")
        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "json"
        assert "states" in data["data"]
        assert data["version"] == "1.0"

    def test_epsilon_transitions_with_null_stack(self, client, sample_dpda_id):
        """Test epsilon transitions with null stack_top."""
        # Setup DPDA with epsilon transitions
        client.post(f"/api/dpda/{sample_dpda_id}/states", json={
            "states": ["q0", "q1", "q2"],
            "initial_state": "q0",
            "accept_states": ["q2"]
        })
        client.post(f"/api/dpda/{sample_dpda_id}/alphabets", json={
            "input_alphabet": ["a", "b"],
            "stack_alphabet": ["$", "A"],
            "initial_stack_symbol": "$"
        })

        # Add epsilon transition with null stack_top (should not check stack)
        response = client.post(f"/api/dpda/{sample_dpda_id}/transition", json={
            "from_state": "q0",
            "input_symbol": None,  # epsilon input
            "stack_top": None,     # epsilon stack (no stack check)
            "to_state": "q1",
            "stack_push": ["A"]    # Push A on top of existing stack
        })
        assert response.status_code == 200

        # Add regular transition
        client.post(f"/api/dpda/{sample_dpda_id}/transition", json={
            "from_state": "q1",
            "input_symbol": "a",
            "stack_top": "A",
            "to_state": "q2",
            "stack_push": []
        })

        # Validate should pass with epsilon transitions
        response = client.post(f"/api/dpda/{sample_dpda_id}/validate")
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True, f"Validation failed: {data.get('violations', [])}"

        # Test computation
        response = client.post(
            f"/api/dpda/{sample_dpda_id}/compute",
            json={"input_string": "a", "show_trace": True}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["accepted"] is True
        assert data["final_state"] == "q2"

    def test_visualize_endpoint(self, client, sample_dpda_id):
        """Test DPDA visualization."""
        # Setup DPDA
        client.post(f"/api/dpda/{sample_dpda_id}/states", json={
            "states": ["q0", "q1"],
            "initial_state": "q0",
            "accept_states": ["q1"]
        })
        client.post(f"/api/dpda/{sample_dpda_id}/alphabets", json={
            "input_alphabet": ["a"],
            "stack_alphabet": ["$"],
            "initial_stack_symbol": "$"
        })
        client.post(f"/api/dpda/{sample_dpda_id}/transition", json={
            "from_state": "q0", "input_symbol": "a", "stack_top": "$",
            "to_state": "q1", "stack_push": []
        })

        # Get DOT visualization
        response = client.get(f"/api/dpda/{sample_dpda_id}/visualize?format=dot")
        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "dot"
        assert "digraph" in data["data"]

        # Get D3.js visualization
        response = client.get(f"/api/dpda/{sample_dpda_id}/visualize?format=d3")
        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "d3"
        assert "nodes" in data["data"]
        assert "links" in data["data"]

    def test_list_dpdas_endpoint(self, client):
        """Test listing all DPDAs."""
        # Create multiple DPDAs
        client.post("/api/dpda/create", json={"name": "dpda1"})
        client.post("/api/dpda/create", json={"name": "dpda2"})

        # List all
        response = client.get("/api/dpda/list")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 2
        assert len(data["dpdas"]) >= 2

    def test_delete_dpda_endpoint(self, client, sample_dpda_id):
        """Test deleting a DPDA."""
        # Delete DPDA
        response = client.delete(f"/api/dpda/{sample_dpda_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["deleted"] is True

        # Try to get deleted DPDA
        response = client.get(f"/api/dpda/{sample_dpda_id}")
        assert response.status_code == 404

    def test_cors_headers(self, client):
        """Test CORS configuration."""
        response = client.options("/api/dpda/create")
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"