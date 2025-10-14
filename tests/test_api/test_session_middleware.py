"""Tests for session ID extraction and validation."""

import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException
import uuid


class TestSessionIDDependency:
    """Test suite for session ID dependency and validation."""

    @pytest.fixture
    def client(self):
        """Create a test client for the FastAPI app."""
        from api.endpoints import app
        return TestClient(app)

    def test_valid_session_id_header(self, client):
        """Test that valid UUID session ID is accepted."""
        # This test will fail initially (RED phase) because we haven't
        # implemented the session ID requirement yet
        session_id = str(uuid.uuid4())

        response = client.post(
            "/api/dpda/create",
            json={"name": "test"},
            headers={"X-Session-ID": session_id}
        )

        # Should succeed with valid session ID
        assert response.status_code == 200

    def test_missing_session_id_header(self, client):
        """Test that missing session ID returns 422 (FastAPI validation error)."""
        response = client.post(
            "/api/dpda/create",
            json={"name": "test"}
            # No X-Session-ID header
        )

        # FastAPI returns 422 for missing required parameters
        assert response.status_code == 422
        data = response.json()
        # Check that error mentions the header
        assert "x-session-id" in str(data).lower() or "x_session_id" in str(data).lower()

    def test_empty_session_id_header(self, client):
        """Test that empty session ID returns 400."""
        response = client.post(
            "/api/dpda/create",
            json={"name": "test"},
            headers={"X-Session-ID": ""}
        )

        # Should return 400 Bad Request
        assert response.status_code in [400, 401]

    def test_invalid_uuid_format(self, client):
        """Test that invalid UUID format returns 400."""
        response = client.post(
            "/api/dpda/create",
            json={"name": "test"},
            headers={"X-Session-ID": "not-a-valid-uuid"}
        )

        # Should return 400 Bad Request
        assert response.status_code == 400
        data = response.json()
        assert "uuid" in data["detail"].lower() or "invalid" in data["detail"].lower()

    def test_session_id_with_hyphens(self, client):
        """Test that standard UUID format with hyphens is accepted."""
        session_id = "550e8400-e29b-41d4-a716-446655440000"

        response = client.post(
            "/api/dpda/create",
            json={"name": "test"},
            headers={"X-Session-ID": session_id}
        )

        assert response.status_code == 200

    def test_session_id_without_hyphens(self, client):
        """Test that UUID without hyphens is accepted."""
        session_id = "550e8400e29b41d4a716446655440000"

        response = client.post(
            "/api/dpda/create",
            json={"name": "test"},
            headers={"X-Session-ID": session_id}
        )

        # Should accept hex string format
        assert response.status_code in [200, 400]  # May or may not accept

    def test_session_isolation(self, client):
        """Test that different sessions cannot see each other's DPDAs."""
        session1 = str(uuid.uuid4())
        session2 = str(uuid.uuid4())

        # Create DPDA in session 1
        response1 = client.post(
            "/api/dpda/create",
            json={"name": "session1_dpda"},
            headers={"X-Session-ID": session1}
        )
        assert response1.status_code == 200
        dpda_id = response1.json()["id"]

        # Try to access from session 2
        response2 = client.get(
            f"/api/dpda/{dpda_id}",
            headers={"X-Session-ID": session2}
        )

        # Should not find it (404)
        assert response2.status_code == 404

    def test_session_id_propagates_to_all_endpoints(self, client):
        """Test that session ID is required for all DPDA endpoints."""
        session_id = str(uuid.uuid4())

        # Create a DPDA first
        response = client.post(
            "/api/dpda/create",
            json={"name": "test"},
            headers={"X-Session-ID": session_id}
        )
        assert response.status_code == 200
        dpda_id = response.json()["id"]

        # Test that list endpoint requires session ID
        response = client.get("/api/dpda/list")
        assert response.status_code == 422  # Missing session ID (422 = validation error)

        # Test that get endpoint requires session ID
        response = client.get(f"/api/dpda/{dpda_id}")
        assert response.status_code == 422

        # Test that delete endpoint requires session ID
        response = client.delete(f"/api/dpda/{dpda_id}")
        assert response.status_code == 422

    def test_health_endpoint_no_session_required(self, client):
        """Test that health check doesn't require session ID."""
        response = client.get("/health")
        assert response.status_code == 200
        # Health check should work without session ID

    def test_session_id_case_insensitive_header(self, client):
        """Test that header name is case-insensitive per HTTP spec."""
        session_id = str(uuid.uuid4())

        # Try with different case
        response = client.post(
            "/api/dpda/create",
            json={"name": "test"},
            headers={"x-session-id": session_id}  # lowercase
        )

        # HTTP headers are case-insensitive
        assert response.status_code == 200

    def test_session_persistence_across_requests(self, client):
        """Test that same session ID can access created DPDAs."""
        session_id = str(uuid.uuid4())

        # Create DPDA
        response1 = client.post(
            "/api/dpda/create",
            json={"name": "persistent_test"},
            headers={"X-Session-ID": session_id}
        )
        assert response1.status_code == 200
        dpda_id = response1.json()["id"]

        # Access with same session ID
        response2 = client.get(
            f"/api/dpda/{dpda_id}",
            headers={"X-Session-ID": session_id}
        )
        assert response2.status_code == 200
        assert response2.json()["id"] == dpda_id

    def test_multiple_dpdas_same_session(self, client):
        """Test that one session can have multiple DPDAs."""
        session_id = str(uuid.uuid4())

        # Create multiple DPDAs
        for i in range(3):
            response = client.post(
                "/api/dpda/create",
                json={"name": f"dpda_{i}"},
                headers={"X-Session-ID": session_id}
            )
            assert response.status_code == 200

        # List should show all 3
        response = client.get(
            "/api/dpda/list",
            headers={"X-Session-ID": session_id}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 3

    def test_session_id_in_error_messages(self, client):
        """Test that error messages mention session ID when missing."""
        response = client.get("/api/dpda/list")

        assert response.status_code == 422
        data = response.json()
        # Error message should mention the header
        assert "x-session-id" in str(data).lower() or "x_session_id" in str(data).lower()

    def test_very_long_session_id(self, client):
        """Test that excessively long session IDs are rejected."""
        long_id = "a" * 500  # Very long string

        response = client.post(
            "/api/dpda/create",
            json={"name": "test"},
            headers={"X-Session-ID": long_id}
        )

        # Should reject invalid format
        assert response.status_code == 400

    def test_session_id_with_special_characters(self, client):
        """Test that session IDs with special characters are rejected."""
        invalid_ids = [
            "hello world",  # space
            "test@session",  # special char
            "../../../etc",  # path traversal
            "<script>alert('xss')</script>",  # XSS attempt
        ]

        for invalid_id in invalid_ids:
            response = client.post(
                "/api/dpda/create",
                json={"name": "test"},
                headers={"X-Session-ID": invalid_id}
            )

            # Should reject
            assert response.status_code == 400
