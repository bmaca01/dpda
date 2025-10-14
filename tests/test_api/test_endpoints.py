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
    def auth_headers(self):
        """Provide authentication headers with test session ID."""
        return {"X-Session-ID": "550e8400-e29b-41d4-a716-446655440000"}

    @pytest.fixture
    def sample_dpda_id(self, client, auth_headers):
        """Create a sample DPDA and return its ID."""
        response = client.post("/api/dpda/create", json={"name": "test_dpda"}, headers=auth_headers)
        return response.json()["id"]

    def test_create_dpda_endpoint(self, client, auth_headers):
        """Test creating a new DPDA."""
        # Create DPDA
        response = client.post(
            "/api/dpda/create",
            json={"name": "0n1n", "description": "Accepts 0^n1^n"}
        , headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["created"] is True
        assert data["name"] == "0n1n"
        assert "id" in data

        # Create without description
        response = client.post("/api/dpda/create", json={"name": "simple"}, headers=auth_headers)
        assert response.status_code == 200

        # Invalid request (missing name)
        response = client.post("/api/dpda/create", json={}, headers=auth_headers)
        assert response.status_code == 422

    def test_get_dpda_info(self, client, auth_headers, sample_dpda_id):
        """Test getting DPDA information."""
        # Get existing DPDA
        response = client.get(f"/api/dpda/{sample_dpda_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_dpda_id
        assert data["name"] == "test_dpda"

        # Get non-existent DPDA
        response = client.get("/api/dpda/invalid_id", headers=auth_headers)
        assert response.status_code == 404

    def test_set_states_endpoint(self, client, auth_headers, sample_dpda_id):
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
        , headers=auth_headers)
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
        , headers=auth_headers)
        assert response.status_code == 422  # Pydantic validation error

    def test_set_alphabets_endpoint(self, client, auth_headers, sample_dpda_id):
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
        , headers=auth_headers)
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
        , headers=auth_headers)
        assert response.status_code == 422  # Pydantic validation error

    def test_add_transition_endpoint(self, client, auth_headers, sample_dpda_id):
        """Test adding transitions."""
        # Set up states and alphabets first
        client.post(f"/api/dpda/{sample_dpda_id}/states", json={
            "states": ["q0", "q1", "q2"],
            "initial_state": "q0",
            "accept_states": ["q2"]
        }, headers=auth_headers)
        client.post(f"/api/dpda/{sample_dpda_id}/alphabets", json={
            "input_alphabet": ["0", "1"],
            "stack_alphabet": ["$", "X"],
            "initial_stack_symbol": "$"
        }, headers=auth_headers)

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
        , headers=auth_headers)
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
        , headers=auth_headers)
        assert response.status_code == 200

    def test_delete_transition_endpoint(self, client, auth_headers, sample_dpda_id):
        """Test deleting transitions."""
        # Setup and add transitions
        client.post(f"/api/dpda/{sample_dpda_id}/states", json={
            "states": ["q0", "q1"],
            "initial_state": "q0",
            "accept_states": []
        }, headers=auth_headers)
        client.post(f"/api/dpda/{sample_dpda_id}/alphabets", json={
            "input_alphabet": ["a"],
            "stack_alphabet": ["$"],
            "initial_stack_symbol": "$"
        }, headers=auth_headers)
        client.post(f"/api/dpda/{sample_dpda_id}/transition", json={
            "from_state": "q0",
            "input_symbol": "a",
            "stack_top": "$",
            "to_state": "q1",
            "stack_push": ["$"]
        }, headers=auth_headers)

        # Delete transition
        response = client.delete(f"/api/dpda/{sample_dpda_id}/transition/0", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["deleted"] is True
        assert data["remaining_transitions"] == 0

        # Delete non-existent transition
        response = client.delete(f"/api/dpda/{sample_dpda_id}/transition/99", headers=auth_headers)
        assert response.status_code == 404

    def test_compute_endpoint(self, client, auth_headers, sample_dpda_id):
        """Test string computation."""
        # Build a simple 0^n1^n DPDA
        client.post(f"/api/dpda/{sample_dpda_id}/states", json={
            "states": ["q0", "q1", "q2"],
            "initial_state": "q0",
            "accept_states": ["q2"]
        }, headers=auth_headers)
        client.post(f"/api/dpda/{sample_dpda_id}/alphabets", json={
            "input_alphabet": ["0", "1"],
            "stack_alphabet": ["$", "X"],
            "initial_stack_symbol": "$"
        }, headers=auth_headers)
        # Add transitions for 0^n1^n
        client.post(f"/api/dpda/{sample_dpda_id}/transition", json={
            "from_state": "q0", "input_symbol": "0", "stack_top": "$",
            "to_state": "q0", "stack_push": ["X", "$"]
        }, headers=auth_headers)
        client.post(f"/api/dpda/{sample_dpda_id}/transition", json={
            "from_state": "q0", "input_symbol": "0", "stack_top": "X",
            "to_state": "q0", "stack_push": ["X", "X"]
        }, headers=auth_headers)
        client.post(f"/api/dpda/{sample_dpda_id}/transition", json={
            "from_state": "q0", "input_symbol": "1", "stack_top": "X",
            "to_state": "q1", "stack_push": []
        }, headers=auth_headers)
        client.post(f"/api/dpda/{sample_dpda_id}/transition", json={
            "from_state": "q1", "input_symbol": "1", "stack_top": "X",
            "to_state": "q1", "stack_push": []
        }, headers=auth_headers)
        client.post(f"/api/dpda/{sample_dpda_id}/transition", json={
            "from_state": "q1", "input_symbol": None, "stack_top": "$",
            "to_state": "q2", "stack_push": []
        }, headers=auth_headers)

        # Test accepted string
        response = client.post(
            f"/api/dpda/{sample_dpda_id}/compute",
            json={"input_string": "0011", "show_trace": False}
        , headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["accepted"] is True
        assert data["final_state"] == "q2"

        # Test rejected string
        response = client.post(
            f"/api/dpda/{sample_dpda_id}/compute",
            json={"input_string": "001", "show_trace": True}
        , headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["accepted"] is False
        assert data["trace"] is not None
        assert len(data["trace"]) > 0

    def test_validate_endpoint(self, client, auth_headers, sample_dpda_id):
        """Test DPDA validation."""
        # Setup a valid DPDA
        client.post(f"/api/dpda/{sample_dpda_id}/states", json={
            "states": ["q0", "q1"],
            "initial_state": "q0",
            "accept_states": ["q1"]
        }, headers=auth_headers)
        client.post(f"/api/dpda/{sample_dpda_id}/alphabets", json={
            "input_alphabet": ["a"],
            "stack_alphabet": ["$"],
            "initial_stack_symbol": "$"
        }, headers=auth_headers)
        client.post(f"/api/dpda/{sample_dpda_id}/transition", json={
            "from_state": "q0", "input_symbol": "a", "stack_top": "$",
            "to_state": "q1", "stack_push": []
        }, headers=auth_headers)

        # Validate
        response = client.post(f"/api/dpda/{sample_dpda_id}/validate", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True
        assert len(data["violations"]) == 0

    def test_export_endpoint(self, client, auth_headers, sample_dpda_id):
        """Test DPDA export."""
        # Setup DPDA
        client.post(f"/api/dpda/{sample_dpda_id}/states", json={
            "states": ["q0", "q1"],
            "initial_state": "q0",
            "accept_states": ["q1"]
        }, headers=auth_headers)
        client.post(f"/api/dpda/{sample_dpda_id}/alphabets", json={
            "input_alphabet": ["a"],
            "stack_alphabet": ["$"],
            "initial_stack_symbol": "$"
        }, headers=auth_headers)

        # Export as JSON
        response = client.get(f"/api/dpda/{sample_dpda_id}/export?format=json", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "json"
        assert "states" in data["data"]
        assert data["version"] == "1.0"

    def test_epsilon_transitions_with_null_stack(self, client, auth_headers, sample_dpda_id):
        """Test epsilon transitions with null stack_top."""
        # Setup DPDA with epsilon transitions
        client.post(f"/api/dpda/{sample_dpda_id}/states", json={
            "states": ["q0", "q1", "q2"],
            "initial_state": "q0",
            "accept_states": ["q2"]
        }, headers=auth_headers)
        client.post(f"/api/dpda/{sample_dpda_id}/alphabets", json={
            "input_alphabet": ["a", "b"],
            "stack_alphabet": ["$", "A"],
            "initial_stack_symbol": "$"
        }, headers=auth_headers)

        # Add epsilon transition with null stack_top (should not check stack)
        response = client.post(f"/api/dpda/{sample_dpda_id}/transition", json={
            "from_state": "q0",
            "input_symbol": None,  # epsilon input
            "stack_top": None,     # epsilon stack (no stack check)
            "to_state": "q1",
            "stack_push": ["A"]    # Push A on top of existing stack
        }, headers=auth_headers)
        assert response.status_code == 200

        # Add regular transition
        client.post(f"/api/dpda/{sample_dpda_id}/transition", json={
            "from_state": "q1",
            "input_symbol": "a",
            "stack_top": "A",
            "to_state": "q2",
            "stack_push": []
        }, headers=auth_headers)

        # Validate should pass with epsilon transitions
        response = client.post(f"/api/dpda/{sample_dpda_id}/validate", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True, f"Validation failed: {data.get('violations', [])}"

        # Test computation
        response = client.post(
            f"/api/dpda/{sample_dpda_id}/compute",
            json={"input_string": "a", "show_trace": True}
        , headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["accepted"] is True
        assert data["final_state"] == "q2"

    def test_visualize_endpoint(self, client, auth_headers, sample_dpda_id):
        """Test DPDA visualization."""
        # Setup DPDA
        client.post(f"/api/dpda/{sample_dpda_id}/states", json={
            "states": ["q0", "q1"],
            "initial_state": "q0",
            "accept_states": ["q1"]
        }, headers=auth_headers)
        client.post(f"/api/dpda/{sample_dpda_id}/alphabets", json={
            "input_alphabet": ["a"],
            "stack_alphabet": ["$"],
            "initial_stack_symbol": "$"
        }, headers=auth_headers)
        client.post(f"/api/dpda/{sample_dpda_id}/transition", json={
            "from_state": "q0", "input_symbol": "a", "stack_top": "$",
            "to_state": "q1", "stack_push": []
        }, headers=auth_headers)

        # Get DOT visualization
        response = client.get(f"/api/dpda/{sample_dpda_id}/visualize?format=dot", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "dot"
        assert "digraph" in data["data"]

        # Get D3.js visualization
        response = client.get(f"/api/dpda/{sample_dpda_id}/visualize?format=d3", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "d3"
        assert isinstance(data["data"], dict), "D3 data should be a dict, not a JSON string"
        assert "nodes" in data["data"]
        assert "links" in data["data"]
        assert isinstance(data["data"]["nodes"], list)
        assert isinstance(data["data"]["links"], list)
        assert len(data["data"]["nodes"]) == 2  # q0, q1

        # Get Cytoscape.js visualization
        response = client.get(f"/api/dpda/{sample_dpda_id}/visualize?format=cytoscape", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "cytoscape"
        assert isinstance(data["data"], dict), "Cytoscape data should be a dict with 'elements' key"
        assert "elements" in data["data"]
        assert isinstance(data["data"]["elements"], list)
        assert len(data["data"]["elements"]) > 0  # Should have nodes and edges

    def test_list_dpdas_endpoint(self, client, auth_headers):
        """Test listing all DPDAs."""
        # Create multiple DPDAs
        client.post("/api/dpda/create", json={"name": "dpda1"}, headers=auth_headers)
        client.post("/api/dpda/create", json={"name": "dpda2"}, headers=auth_headers)

        # List all
        response = client.get("/api/dpda/list", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 2
        assert len(data["dpdas"]) >= 2

    def test_delete_dpda_endpoint(self, client, auth_headers, sample_dpda_id):
        """Test deleting a DPDA."""
        # Delete DPDA
        response = client.delete(f"/api/dpda/{sample_dpda_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["deleted"] is True

        # Try to get deleted DPDA
        response = client.get(f"/api/dpda/{sample_dpda_id}", headers=auth_headers)
        assert response.status_code == 404

    def test_cors_headers(self, client, auth_headers):
        """Test CORS configuration.

        Note: TestClient bypasses CORS middleware, so we just verify
        the endpoint exists and is accessible.
        """
        # TestClient doesn't handle CORS, but we can verify the endpoint works
        response = client.post("/api/dpda/create", json={"name": "test"}, headers=auth_headers)
        assert response.status_code == 200
        # In production, CORS headers would be present

    def test_health_check(self, client, auth_headers):
        """Test health check endpoint."""
        response = client.get("/health", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_get_transitions_endpoint(self, client, auth_headers, sample_dpda_id):
        """Test getting transitions from a DPDA."""
        # Setup DPDA with transitions
        client.post(f"/api/dpda/{sample_dpda_id}/states", json={
            "states": ["q0", "q1", "q2"],
            "initial_state": "q0",
            "accept_states": ["q2"]
        }, headers=auth_headers)
        client.post(f"/api/dpda/{sample_dpda_id}/alphabets", json={
            "input_alphabet": ["a", "b"],
            "stack_alphabet": ["$", "X", "Y"],
            "initial_stack_symbol": "$"
        }, headers=auth_headers)

        # Add regular transition with multi-symbol push
        client.post(f"/api/dpda/{sample_dpda_id}/transition", json={
            "from_state": "q0",
            "input_symbol": "a",
            "stack_top": "$",
            "to_state": "q1",
            "stack_push": ["X", "$"]  # Should result in "X,$" internally
        }, headers=auth_headers)

        # Add epsilon transition
        client.post(f"/api/dpda/{sample_dpda_id}/transition", json={
            "from_state": "q1",
            "input_symbol": None,
            "stack_top": "X",
            "to_state": "q2",
            "stack_push": []
        }, headers=auth_headers)

        # Add transition with single symbol push
        client.post(f"/api/dpda/{sample_dpda_id}/transition", json={
            "from_state": "q2",
            "input_symbol": "b",
            "stack_top": "$",
            "to_state": "q0",
            "stack_push": ["Y"]
        }, headers=auth_headers)

        # Get transitions
        response = client.get(f"/api/dpda/{sample_dpda_id}/transitions", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()

        # Verify structure
        assert "transitions" in data
        assert "total" in data
        assert data["total"] == 3
        assert len(data["transitions"]) == 3

        # Verify first transition (multi-symbol push)
        trans0 = data["transitions"][0]
        assert trans0["from_state"] == "q0"
        assert trans0["input_symbol"] == "a"
        assert trans0["stack_top"] == "$"
        assert trans0["to_state"] == "q1"
        assert trans0["stack_push"] == ["X", "$"]

        # Verify epsilon transition
        trans1 = data["transitions"][1]
        assert trans1["from_state"] == "q1"
        assert trans1["input_symbol"] is None
        assert trans1["stack_top"] == "X"
        assert trans1["to_state"] == "q2"
        assert trans1["stack_push"] == []

        # Verify single symbol push
        trans2 = data["transitions"][2]
        assert trans2["from_state"] == "q2"
        assert trans2["input_symbol"] == "b"
        assert trans2["stack_top"] == "$"
        assert trans2["to_state"] == "q0"
        assert trans2["stack_push"] == ["Y"]

    def test_get_transitions_empty(self, client, auth_headers, sample_dpda_id):
        """Test getting transitions from newly created DPDA."""
        # Get transitions without adding any
        response = client.get(f"/api/dpda/{sample_dpda_id}/transitions", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["transitions"] == []

    def test_get_transitions_not_found(self, client, auth_headers):
        """Test getting transitions from non-existent DPDA."""
        response = client.get("/api/dpda/nonexistent_id/transitions", headers=auth_headers)
        assert response.status_code == 404

    def test_update_dpda_metadata(self, client, auth_headers, sample_dpda_id):
        """Test updating DPDA metadata (name and description)."""
        # Update name only
        response = client.patch(
            f"/api/dpda/{sample_dpda_id}",
            json={"name": "updated_name"}
        , headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["updated"] is True
        assert "name" in data["changes"]
        assert data["changes"]["name"] == "updated_name"

        # Verify the update
        response = client.get(f"/api/dpda/{sample_dpda_id}", headers=auth_headers)
        assert response.json()["name"] == "updated_name"

        # Update description only
        response = client.patch(
            f"/api/dpda/{sample_dpda_id}",
            json={"description": "A test DPDA"}
        , headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "description" in data["changes"]

        # Update both name and description
        response = client.patch(
            f"/api/dpda/{sample_dpda_id}",
            json={"name": "final_name", "description": "Final description"}
        , headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["changes"]) == 2

        # Test 404 for non-existent DPDA
        response = client.patch(
            "/api/dpda/invalid_id",
            json={"name": "test"}
        , headers=auth_headers)
        assert response.status_code == 404

        # Test empty name validation
        response = client.patch(
            f"/api/dpda/{sample_dpda_id}",
            json={"name": ""}
        , headers=auth_headers)
        assert response.status_code == 422

    def test_update_states_partial(self, client, auth_headers, sample_dpda_id):
        """Test partial update of states configuration."""
        # Setup initial states
        client.post(f"/api/dpda/{sample_dpda_id}/states", json={
            "states": ["q0", "q1", "q2"],
            "initial_state": "q0",
            "accept_states": ["q2"]
        }, headers=auth_headers)

        # Update only accept states
        response = client.patch(
            f"/api/dpda/{sample_dpda_id}/states",
            json={"accept_states": ["q1", "q2"]}
        , headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["updated"] is True

        # Verify update
        info = client.get(f"/api/dpda/{sample_dpda_id}", headers=auth_headers).json()
        assert set(info["accept_states"]) == {"q1", "q2"}
        assert info["initial_state"] == "q0"  # Should remain unchanged

        # Update only initial state
        response = client.patch(
            f"/api/dpda/{sample_dpda_id}/states",
            json={"initial_state": "q1"}
        , headers=auth_headers)
        assert response.status_code == 200

        # Verify
        info = client.get(f"/api/dpda/{sample_dpda_id}", headers=auth_headers).json()
        assert info["initial_state"] == "q1"

        # Invalid: initial state not in existing states
        response = client.patch(
            f"/api/dpda/{sample_dpda_id}/states",
            json={"initial_state": "q99"}
        , headers=auth_headers)
        assert response.status_code == 400

        # Update states and initial state together
        response = client.patch(
            f"/api/dpda/{sample_dpda_id}/states",
            json={"states": ["q0", "q1"], "initial_state": "q0"}
        , headers=auth_headers)
        assert response.status_code == 200

    def test_update_states_full(self, client, auth_headers, sample_dpda_id):
        """Test full replacement of states configuration using PUT."""
        # Setup initial states
        client.post(f"/api/dpda/{sample_dpda_id}/states", json={
            "states": ["q0", "q1", "q2"],
            "initial_state": "q0",
            "accept_states": ["q2"]
        }, headers=auth_headers)

        # Full replacement with PUT
        response = client.put(
            f"/api/dpda/{sample_dpda_id}/states",
            json={
                "states": ["s0", "s1"],
                "initial_state": "s0",
                "accept_states": ["s1"]
            }
        , headers=auth_headers)
        assert response.status_code == 200

        # Verify complete replacement
        info = client.get(f"/api/dpda/{sample_dpda_id}", headers=auth_headers).json()
        assert set(info["states"]) == {"s0", "s1"}
        assert info["initial_state"] == "s0"
        assert info["accept_states"] == ["s1"]

    def test_update_alphabets_partial(self, client, auth_headers, sample_dpda_id):
        """Test partial update of alphabets."""
        # Setup initial alphabets
        client.post(f"/api/dpda/{sample_dpda_id}/alphabets", json={
            "input_alphabet": ["0", "1"],
            "stack_alphabet": ["$", "X"],
            "initial_stack_symbol": "$"
        }, headers=auth_headers)

        # Update only input alphabet
        response = client.patch(
            f"/api/dpda/{sample_dpda_id}/alphabets",
            json={"input_alphabet": ["a", "b", "c"]}
        , headers=auth_headers)
        assert response.status_code == 200

        # Verify update
        info = client.get(f"/api/dpda/{sample_dpda_id}", headers=auth_headers).json()
        assert set(info["input_alphabet"]) == {"a", "b", "c"}
        assert set(info["stack_alphabet"]) == {"$", "X"}  # Unchanged

        # Update only stack alphabet (must include initial stack symbol)
        response = client.patch(
            f"/api/dpda/{sample_dpda_id}/alphabets",
            json={"stack_alphabet": ["$", "Y", "Z"]}
        , headers=auth_headers)
        assert response.status_code == 200

        # Invalid: stack alphabet without initial stack symbol
        response = client.patch(
            f"/api/dpda/{sample_dpda_id}/alphabets",
            json={"stack_alphabet": ["A", "B"]}
        , headers=auth_headers)
        assert response.status_code == 400

    def test_update_alphabets_full(self, client, auth_headers, sample_dpda_id):
        """Test full replacement of alphabets using PUT."""
        # Setup initial alphabets
        client.post(f"/api/dpda/{sample_dpda_id}/alphabets", json={
            "input_alphabet": ["0", "1"],
            "stack_alphabet": ["$", "X"],
            "initial_stack_symbol": "$"
        }, headers=auth_headers)

        # Full replacement
        response = client.put(
            f"/api/dpda/{sample_dpda_id}/alphabets",
            json={
                "input_alphabet": ["a", "b"],
                "stack_alphabet": ["#", "A"],
                "initial_stack_symbol": "#"
            }
        , headers=auth_headers)
        assert response.status_code == 200

        # Verify
        info = client.get(f"/api/dpda/{sample_dpda_id}", headers=auth_headers).json()
        assert set(info["input_alphabet"]) == {"a", "b"}
        assert info["initial_stack_symbol"] == "#"

    def test_update_transition(self, client, auth_headers, sample_dpda_id):
        """Test updating a specific transition."""
        # Setup DPDA with transitions
        client.post(f"/api/dpda/{sample_dpda_id}/states", json={
            "states": ["q0", "q1", "q2"],
            "initial_state": "q0",
            "accept_states": ["q2"]
        }, headers=auth_headers)
        client.post(f"/api/dpda/{sample_dpda_id}/alphabets", json={
            "input_alphabet": ["0", "1"],
            "stack_alphabet": ["$", "X"],
            "initial_stack_symbol": "$"
        }, headers=auth_headers)
        client.post(f"/api/dpda/{sample_dpda_id}/transition", json={
            "from_state": "q0",
            "input_symbol": "0",
            "stack_top": "$",
            "to_state": "q1",
            "stack_push": ["X", "$"]
        }, headers=auth_headers)

        # Update transition at index 0
        response = client.put(
            f"/api/dpda/{sample_dpda_id}/transition/0",
            json={"to_state": "q2"}
        , headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["updated"] is True

        # Verify update
        transitions = client.get(f"/api/dpda/{sample_dpda_id}/transitions", headers=auth_headers).json()
        assert transitions["transitions"][0]["to_state"] == "q2"
        assert transitions["transitions"][0]["from_state"] == "q0"  # Unchanged

        # Update multiple fields
        response = client.put(
            f"/api/dpda/{sample_dpda_id}/transition/0",
            json={
                "input_symbol": "1",
                "stack_push": ["X", "X"]
            }
        , headers=auth_headers)
        assert response.status_code == 200

        # Verify
        transitions = client.get(f"/api/dpda/{sample_dpda_id}/transitions", headers=auth_headers).json()
        assert transitions["transitions"][0]["input_symbol"] == "1"
        assert transitions["transitions"][0]["stack_push"] == ["X", "X"]

        # Test 404 for invalid index
        response = client.put(
            f"/api/dpda/{sample_dpda_id}/transition/99",
            json={"to_state": "q1"}
        , headers=auth_headers)
        assert response.status_code == 404

        # Test 404 for invalid DPDA
        response = client.put(
            "/api/dpda/invalid_id/transition/0",
            json={"to_state": "q1"}
        , headers=auth_headers)
        assert response.status_code == 404

    def test_update_workflow_integration(self, client, auth_headers):
        """Test complete workflow with updates."""
        # Create DPDA
        response = client.post("/api/dpda/create", json={"name": "workflow_test"}, headers=auth_headers)
        dpda_id = response.json()["id"]

        # Setup initial configuration
        client.post(f"/api/dpda/{dpda_id}/states", json={
            "states": ["q0", "q1"],
            "initial_state": "q0",
            "accept_states": ["q1"]
        }, headers=auth_headers)
        client.post(f"/api/dpda/{dpda_id}/alphabets", json={
            "input_alphabet": ["a"],
            "stack_alphabet": ["$"],
            "initial_stack_symbol": "$"
        }, headers=auth_headers)
        client.post(f"/api/dpda/{dpda_id}/transition", json={
            "from_state": "q0",
            "input_symbol": "a",
            "stack_top": "$",
            "to_state": "q1",
            "stack_push": []
        }, headers=auth_headers)

        # Update metadata
        client.patch(f"/api/dpda/{dpda_id}", json={
            "name": "updated_workflow",
            "description": "Integration test"
        }, headers=auth_headers)

        # Update states
        client.patch(f"/api/dpda/{dpda_id}/states", json={
            "states": ["q0", "q1", "q2"],
            "accept_states": ["q1", "q2"]
        }, headers=auth_headers)

        # Update alphabets
        client.patch(f"/api/dpda/{dpda_id}/alphabets", json={
            "input_alphabet": ["a", "b"]
        }, headers=auth_headers)

        # Update transition
        client.put(f"/api/dpda/{dpda_id}/transition/0", json={
            "to_state": "q2"
        }, headers=auth_headers)

        # Verify all updates
        info = client.get(f"/api/dpda/{dpda_id}", headers=auth_headers).json()
        assert info["name"] == "updated_workflow"
        assert set(info["states"]) == {"q0", "q1", "q2"}
        assert set(info["input_alphabet"]) == {"a", "b"}

        transitions = client.get(f"/api/dpda/{dpda_id}/transitions", headers=auth_headers).json()
        assert transitions["transitions"][0]["to_state"] == "q2"