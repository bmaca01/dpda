"""Standardized error handling for the API."""

from fastapi import HTTPException
from typing import Optional


class APIError:
    """Standardized error messages and utilities."""

    # Resource not found errors
    DPDA_NOT_FOUND = "DPDA not found in current session"
    TRANSITION_NOT_FOUND = "Transition not found at specified index"

    # Validation errors
    INVALID_SESSION_ID_EMPTY = "X-Session-ID header cannot be empty"
    INVALID_SESSION_ID_FORMAT = "X-Session-ID must be a valid UUID format (e.g., '550e8400-e29b-41d4-a716-446655440000')"
    INVALID_SESSION_ID_LENGTH = "X-Session-ID exceeds maximum length of 100 characters"

    # Format errors
    UNSUPPORTED_EXPORT_FORMAT = "Unsupported export format: {format}"
    UNSUPPORTED_VISUALIZATION_FORMAT = "Unsupported visualization format: {format}"

    @staticmethod
    def not_found(resource: str = "DPDA") -> HTTPException:
        """Create a 404 Not Found exception."""
        return HTTPException(
            status_code=404,
            detail=f"{resource} not found in current session"
        )

    @staticmethod
    def bad_request(message: str) -> HTTPException:
        """Create a 400 Bad Request exception."""
        return HTTPException(
            status_code=400,
            detail=message
        )

    @staticmethod
    def validation_error(message: str) -> HTTPException:
        """Create a 422 Validation Error exception."""
        return HTTPException(
            status_code=422,
            detail=message
        )

    @staticmethod
    def unsupported_format(format_type: str, format_value: str) -> HTTPException:
        """Create exception for unsupported format."""
        return HTTPException(
            status_code=400,
            detail=f"Unsupported {format_type} format: {format_value}"
        )
