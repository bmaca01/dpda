"""FastAPI dependencies for API endpoints."""

import re
from fastapi import Header
from api.errors import APIError


def get_session_id(x_session_id: str = Header(..., description="Session identifier for DPDA isolation")) -> str:
    """
    FastAPI dependency to extract and validate session ID from headers.

    Args:
        x_session_id: Session identifier from X-Session-ID header

    Returns:
        Validated session ID string

    Raises:
        HTTPException: 422 if header is missing (FastAPI validation)
        HTTPException: 400 if UUID format is invalid or header is empty

    Usage:
        @app.get("/api/dpda/list")
        async def list_dpdas(session_id: str = Depends(get_session_id)):
            # session_id is validated and ready to use
            pass
    """
    # Check for empty string (Header(...) ensures it's not missing)
    if not x_session_id or x_session_id.strip() == "":
        raise APIError.bad_request(APIError.INVALID_SESSION_ID_EMPTY)

    # Validate UUID format (with or without hyphens)
    # UUIDv4 format: 8-4-4-4-12 hex digits
    uuid_pattern_with_hyphens = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    uuid_pattern_without_hyphens = r'^[0-9a-f]{32}$'

    session_id_lower = x_session_id.lower()

    if not (re.match(uuid_pattern_with_hyphens, session_id_lower) or
            re.match(uuid_pattern_without_hyphens, session_id_lower)):
        raise APIError.bad_request(APIError.INVALID_SESSION_ID_FORMAT)

    # Additional security checks
    if len(x_session_id) > 100:  # Reasonable max length
        raise APIError.bad_request(APIError.INVALID_SESSION_ID_LENGTH)

    return x_session_id


def get_session_id_optional(x_session_id: str = Header(None, description="Optional session identifier")) -> str | None:
    """
    Optional session ID dependency for endpoints that don't require authentication.

    Args:
        x_session_id: Optional session identifier from X-Session-ID header

    Returns:
        Validated session ID string or None if not provided
    """
    if x_session_id is None:
        return None

    # If provided, validate it
    return get_session_id(x_session_id=x_session_id)
