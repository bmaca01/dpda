"""FastAPI endpoints for DPDA REST API."""

from fastapi import FastAPI, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Optional, Any
import uuid

from api.models import (
    CreateDPDARequest, CreateDPDAResponse,
    SetStatesRequest, SetAlphabetsRequest,
    AddTransitionRequest, ComputeRequest, ComputeResponse,
    ValidationResponse, DPDAInfoResponse,
    ExportResponse, VisualizationResponse,
    ErrorResponse, ListDPDAsResponse,
    DeleteTransitionResponse, TransitionsResponse, TransitionItem,
    UpdateDPDARequest, UpdateDPDAResponse,
    UpdateStatesRequest, UpdateAlphabetsRequest,
    UpdateTransitionRequest, UpdateTransitionResponse
)
from api.dependencies import get_session_id
from api.errors import APIError
from api.storage_helpers import session_storage
from core.session import DPDASession, SessionError
from core.dpda_engine import DPDAEngine
from validation.dpda_validator import DPDAValidator
from serialization.dpda_serializer import DPDASerializer
from visualization.graph_builder import GraphBuilder
from models.transition import Transition
from models.configuration import Configuration


# Create FastAPI app
app = FastAPI(
    title="DPDA Simulator API",
    description="REST API for Deterministic Pushdown Automaton simulation",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Note: Storage backend is now configured via STORAGE_BACKEND environment variable
# - 'memory': In-memory storage (fast, non-persistent)
# - 'database': SQLite storage (persistent across restarts)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}


@app.post("/api/dpda/create", response_model=CreateDPDAResponse)
async def create_dpda(request: CreateDPDARequest, session_id: str = Depends(get_session_id)):
    """Create a new DPDA."""
    # Generate unique DPDA ID
    dpda_id = f"dpda_{uuid.uuid4().hex[:8]}"

    try:
        # Create session and store it
        session_storage.create_session(dpda_id, session_id, request.name)

        return CreateDPDAResponse(
            id=dpda_id,
            name=request.name,
            created=True,
            message="DPDA created successfully"
        )
    except SessionError as e:
        raise APIError.bad_request(str(e))


@app.get("/api/dpda/list", response_model=ListDPDAsResponse)
async def list_dpdas(session_id: str = Depends(get_session_id)):
    """List all DPDAs for the current session."""
    # Get all DPDAs for this session from storage
    dpdas = session_storage.list_sessions(session_id)
    dpda_list = []

    for dpda_info in dpdas:
        dpda_id = dpda_info['id']

        # Get session to check validity
        session = session_storage.get_session(dpda_id, session_id)
        is_valid = False

        if session:
            builder = session.get_current_builder()
            # Check validity if possible
            try:
                if builder.states and builder.initial_state:
                    dpda = session.build_current_dpda()
                    validator = DPDAValidator()
                    result = validator.validate(dpda)
                    is_valid = result.is_valid
            except:
                pass

        dpda_list.append({
            "id": dpda_id,
            "name": dpda_info.get('name', 'unnamed'),
            "is_valid": is_valid
        })

    return ListDPDAsResponse(dpdas=dpda_list, count=len(dpda_list))


@app.get("/api/dpda/{dpda_id}", response_model=DPDAInfoResponse)
async def get_dpda_info(dpda_id: str, session_id: str = Depends(get_session_id)):
    """Get information about a DPDA."""
    session = session_storage.get_session(dpda_id, session_id)
    if not session:
        raise APIError.not_found("DPDA")

    builder = session.get_current_builder()

    # Check if DPDA can be built
    is_complete = all([
        builder.states,
        builder.initial_state,
        builder.stack_alphabet,
        builder.initial_stack_symbol
    ])

    # Validate if complete
    is_valid = False
    if is_complete:
        try:
            dpda = session.build_current_dpda()
            validator = DPDAValidator()
            result = validator.validate(dpda)
            is_valid = result.is_valid
        except:
            pass

    return DPDAInfoResponse(
        id=dpda_id,
        name=session.current_dpda_name or "unnamed",
        states=list(builder.states),
        input_alphabet=list(builder.input_alphabet),
        stack_alphabet=list(builder.stack_alphabet),
        initial_state=builder.initial_state or "",
        initial_stack_symbol=builder.initial_stack_symbol or "",
        accept_states=list(builder.accept_states),
        num_transitions=len(builder.transitions),
        is_complete=is_complete,
        is_valid=is_valid
    )


@app.get("/api/dpda/{dpda_id}/transitions", response_model=TransitionsResponse)
async def get_transitions(dpda_id: str, session_id: str = Depends(get_session_id)):
    """Get all transitions for a DPDA."""
    session = session_storage.get_session(dpda_id, session_id)
    if not session:
        raise APIError.not_found("DPDA")
    builder = session.get_current_builder()

    # Convert transitions to API format
    transition_items = []
    for trans in builder.transitions:
        # Convert stack_push string to array
        if trans.stack_push:
            stack_push_array = trans.stack_push.split(',')
        else:
            stack_push_array = []

        transition_items.append(TransitionItem(
            from_state=trans.from_state,
            input_symbol=trans.input_symbol,
            stack_top=trans.stack_top,
            to_state=trans.to_state,
            stack_push=stack_push_array
        ))

    return TransitionsResponse(
        transitions=transition_items,
        total=len(transition_items)
    )


@app.post("/api/dpda/{dpda_id}/states")
async def set_states(dpda_id: str, request: SetStatesRequest, session_id: str = Depends(get_session_id)):
    """Set DPDA states."""
    session = session_storage.get_session(dpda_id, session_id)
    if not session:
        raise APIError.not_found("DPDA")

    try:
        # Set states directly as strings
        session.set_states(set(request.states))

        # Set initial state
        session.set_initial_state(request.initial_state)

        # Set accept states
        session.set_accept_states(set(request.accept_states))

        # Save updated session to storage
        session_storage.update_session(dpda_id, session_id, session)

        return {"success": True, "message": "States configured successfully"}
    except (SessionError, ValueError) as e:
        raise APIError.bad_request(str(e))


@app.post("/api/dpda/{dpda_id}/alphabets")
async def set_alphabets(dpda_id: str, request: SetAlphabetsRequest, session_id: str = Depends(get_session_id)):
    """Set DPDA alphabets."""
    session = session_storage.get_session(dpda_id, session_id)
    if not session:
        raise APIError.not_found("DPDA")

    try:
        session.set_input_alphabet(set(request.input_alphabet))
        session.set_stack_alphabet(set(request.stack_alphabet))
        session.set_initial_stack_symbol(request.initial_stack_symbol)

        # Save updated session to storage
        session_storage.update_session(dpda_id, session_id, session)

        return {"success": True, "message": "Alphabets configured successfully"}
    except SessionError as e:
        raise APIError.bad_request(str(e))


@app.post("/api/dpda/{dpda_id}/transition")
async def add_transition(dpda_id: str, request: AddTransitionRequest, session_id: str = Depends(get_session_id)):
    """Add a transition to the DPDA."""
    session = session_storage.get_session(dpda_id, session_id)
    if not session:
        raise APIError.not_found("DPDA")

    try:
        # Handle stack push
        if request.stack_push:
            stack_push = ",".join(request.stack_push)
        else:
            stack_push = ""  # Empty string for no push, not None

        session.add_transition(
            from_state=request.from_state,
            input_symbol=request.input_symbol,
            stack_top=request.stack_top,
            to_state=request.to_state,
            stack_push=stack_push
        )

        # Save updated session to storage
        session_storage.update_session(dpda_id, session_id, session)

        return {"added": True, "message": "Transition added successfully"}
    except (SessionError, ValueError, IndexError) as e:
        raise APIError.bad_request(str(e))


@app.delete("/api/dpda/{dpda_id}/transition/{index}", response_model=DeleteTransitionResponse)
async def delete_transition(dpda_id: str, index: int, session_id: str = Depends(get_session_id)):
    """Delete a transition from the DPDA."""
    session = session_storage.get_session(dpda_id, session_id)
    if not session:
        raise APIError.not_found("DPDA")

    try:
        session.remove_transition(index)

        # Save updated session to storage
        session_storage.update_session(dpda_id, session_id, session)

        return DeleteTransitionResponse(
            deleted=True,
            message="Transition removed successfully",
            remaining_transitions=len(session.get_current_builder().transitions)
        )
    except (SessionError, IndexError) as e:
        raise APIError.not_found("Transition")


@app.post("/api/dpda/{dpda_id}/compute", response_model=ComputeResponse)
async def compute_string(dpda_id: str, request: ComputeRequest, session_id: str = Depends(get_session_id)):
    """Compute whether a string is accepted by the DPDA."""
    session = session_storage.get_session(dpda_id, session_id)
    if not session:
        raise APIError.not_found("DPDA")

    try:
        dpda = session.build_current_dpda()
        engine = DPDAEngine()
        result = engine.compute(dpda, request.input_string, request.max_steps)

        # Format trace if requested
        trace = None
        if request.show_trace and result.trace:
            trace = []
            for config in result.trace:
                trace.append({
                    "state": config.state,
                    "input": config.remaining_input,
                    "stack": config.stack
                })

        # Get final stack from last configuration in trace
        final_stack = []
        if result.trace and len(result.trace) > 0:
            final_stack = result.trace[-1].stack

        return ComputeResponse(
            accepted=result.accepted,
            final_state=result.final_state,
            final_stack=final_stack,
            steps_taken=result.steps_taken,
            trace=trace,
            reason=result.rejection_reason
        )
    except SessionError as e:
        raise APIError.bad_request(str(e))


@app.post("/api/dpda/{dpda_id}/validate", response_model=ValidationResponse)
async def validate_dpda(dpda_id: str, session_id: str = Depends(get_session_id)):
    """Validate the DPDA for determinism properties."""
    session = session_storage.get_session(dpda_id, session_id)
    if not session:
        raise APIError.not_found("DPDA")

    try:
        dpda = session.build_current_dpda()
        validator = DPDAValidator()
        result = validator.validate(dpda)

        # Format violations
        violations = []
        for error in result.errors:
            violations.append({
                "type": error.split(":")[0] if ":" in error else "UNKNOWN",
                "description": error
            })

        return ValidationResponse(
            is_valid=result.is_valid,
            violations=violations,
            message="DPDA is deterministic" if result.is_valid else "DPDA violates determinism properties"
        )
    except SessionError as e:
        raise APIError.bad_request(str(e))


@app.get("/api/dpda/{dpda_id}/export", response_model=ExportResponse)
async def export_dpda(dpda_id: str, format: str = Query("json", description="Export format"), session_id: str = Depends(get_session_id)):
    """Export the DPDA definition."""
    session = session_storage.get_session(dpda_id, session_id)
    if not session:
        raise APIError.not_found("DPDA")

    try:
        dpda = session.build_current_dpda()
        serializer = DPDASerializer()

        if format == "json":
            data_dict = serializer.to_dict(dpda)
            # Extract just the DPDA data for the response
            return ExportResponse(
                format="json",
                data=data_dict['dpda'],
                version=data_dict['version']
            )
        else:
            raise APIError.unsupported_format("export", format)
    except SessionError as e:
        raise APIError.bad_request(str(e))


@app.get("/api/dpda/{dpda_id}/visualize", response_model=VisualizationResponse)
async def visualize_dpda(dpda_id: str, format: str = Query("dot", description="Visualization format"), session_id: str = Depends(get_session_id)):
    """Generate visualization data for the DPDA."""
    session = session_storage.get_session(dpda_id, session_id)
    if not session:
        raise APIError.not_found("DPDA")

    try:
        dpda = session.build_current_dpda()
        graph_builder = GraphBuilder()

        if format == "dot":
            data = graph_builder.to_dot(dpda)
            return VisualizationResponse(format="dot", data=data)
        elif format == "d3":
            data = graph_builder.to_d3(dpda)
            return VisualizationResponse(format="d3", data=data)
        elif format == "cytoscape":
            data = graph_builder.to_cytoscape(dpda)
            return VisualizationResponse(format="cytoscape", data=data)
        else:
            raise APIError.unsupported_format("visualization", format)
    except SessionError as e:
        raise APIError.bad_request(str(e))


@app.delete("/api/dpda/{dpda_id}")
async def delete_dpda(dpda_id: str, session_id: str = Depends(get_session_id)):
    """Delete a DPDA."""
    if not session_storage.exists(dpda_id, session_id):
        raise APIError.not_found("DPDA")

    session_storage.delete_session(dpda_id, session_id)
    return {"deleted": True, "message": "DPDA deleted successfully"}


@app.patch("/api/dpda/{dpda_id}", response_model=UpdateDPDAResponse)
async def update_dpda_metadata(dpda_id: str, request: UpdateDPDARequest, session_id: str = Depends(get_session_id)):
    """Update DPDA metadata (name and description)."""
    session = session_storage.get_session(dpda_id, session_id)
    if not session:
        raise APIError.not_found("DPDA")

    try:
        changes = session.update_metadata(
            name=request.name,
            description=request.description
        )

        # Save updated session to storage
        # If name was changed, pass it to update the storage record
        new_name = request.name if 'name' in changes else None
        session_storage.update_session(dpda_id, session_id, session, name=new_name)

        return UpdateDPDAResponse(
            id=dpda_id,
            updated=True,
            message="DPDA updated successfully",
            changes=changes
        )
    except SessionError as e:
        raise APIError.bad_request(str(e))


@app.put("/api/dpda/{dpda_id}/states")
async def update_states_full(dpda_id: str, request: SetStatesRequest, session_id: str = Depends(get_session_id)):
    """Full replacement of states configuration (PUT)."""
    session = session_storage.get_session(dpda_id, session_id)
    if not session:
        raise APIError.not_found("DPDA")

    try:
        # Full replacement - use existing set_states methods
        session.set_states(set(request.states))
        session.set_initial_state(request.initial_state)
        session.set_accept_states(set(request.accept_states))

        # Save updated session to storage
        session_storage.update_session(dpda_id, session_id, session)

        return {"updated": True, "message": "States updated successfully"}
    except (SessionError, ValueError) as e:
        raise APIError.bad_request(str(e))


@app.patch("/api/dpda/{dpda_id}/states")
async def update_states_partial(dpda_id: str, request: UpdateStatesRequest, session_id: str = Depends(get_session_id)):
    """Partial update of states configuration (PATCH)."""
    session = session_storage.get_session(dpda_id, session_id)
    if not session:
        raise APIError.not_found("DPDA")

    try:
        changes = session.update_states(
            states=set(request.states) if request.states else None,
            initial_state=request.initial_state,
            accept_states=set(request.accept_states) if request.accept_states else None
        )

        # Save updated session to storage
        session_storage.update_session(dpda_id, session_id, session)

        return {
            "updated": True,
            "message": "States updated successfully",
            "changes": changes
        }
    except (SessionError, ValueError) as e:
        raise APIError.bad_request(str(e))


@app.put("/api/dpda/{dpda_id}/alphabets")
async def update_alphabets_full(dpda_id: str, request: SetAlphabetsRequest, session_id: str = Depends(get_session_id)):
    """Full replacement of alphabets configuration (PUT)."""
    session = session_storage.get_session(dpda_id, session_id)
    if not session:
        raise APIError.not_found("DPDA")

    try:
        session.set_input_alphabet(set(request.input_alphabet))
        session.set_stack_alphabet(set(request.stack_alphabet))
        session.set_initial_stack_symbol(request.initial_stack_symbol)

        # Save updated session to storage
        session_storage.update_session(dpda_id, session_id, session)

        return {"updated": True, "message": "Alphabets updated successfully"}
    except SessionError as e:
        raise APIError.bad_request(str(e))


@app.patch("/api/dpda/{dpda_id}/alphabets")
async def update_alphabets_partial(dpda_id: str, request: UpdateAlphabetsRequest, session_id: str = Depends(get_session_id)):
    """Partial update of alphabets configuration (PATCH)."""
    session = session_storage.get_session(dpda_id, session_id)
    if not session:
        raise APIError.not_found("DPDA")

    try:
        changes = session.update_alphabets(
            input_alphabet=set(request.input_alphabet) if request.input_alphabet else None,
            stack_alphabet=set(request.stack_alphabet) if request.stack_alphabet else None,
            initial_stack_symbol=request.initial_stack_symbol
        )

        # Save updated session to storage
        session_storage.update_session(dpda_id, session_id, session)

        return {
            "updated": True,
            "message": "Alphabets updated successfully",
            "changes": changes
        }
    except SessionError as e:
        raise APIError.bad_request(str(e))


@app.put("/api/dpda/{dpda_id}/transition/{index}", response_model=UpdateTransitionResponse)
async def update_transition(dpda_id: str, index: int, request: UpdateTransitionRequest, session_id: str = Depends(get_session_id)):
    """Update a specific transition by index (PUT)."""
    session = session_storage.get_session(dpda_id, session_id)
    if not session:
        raise APIError.not_found("DPDA")

    try:
        # Handle stack push conversion if provided
        stack_push = None
        if request.stack_push is not None:
            stack_push = ",".join(request.stack_push) if request.stack_push else ""

        changes = session.update_transition(
            index=index,
            from_state=request.from_state,
            input_symbol=request.input_symbol,
            stack_top=request.stack_top,
            to_state=request.to_state,
            stack_push=stack_push
        )

        # Save updated session to storage
        session_storage.update_session(dpda_id, session_id, session)

        return UpdateTransitionResponse(
            updated=True,
            message="Transition updated successfully",
            changes=changes
        )
    except IndexError:
        raise APIError.not_found("Transition")
    except (SessionError, ValueError) as e:
        raise APIError.bad_request(str(e))