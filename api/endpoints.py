"""FastAPI endpoints for DPDA REST API."""

from fastapi import FastAPI, HTTPException, Query
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
    DeleteTransitionResponse
)
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

# In-memory storage for DPDA sessions (in production, use a database)
sessions: Dict[str, DPDASession] = {}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}


@app.post("/api/dpda/create", response_model=CreateDPDAResponse)
async def create_dpda(request: CreateDPDARequest):
    """Create a new DPDA."""
    dpda_id = f"dpda_{uuid.uuid4().hex[:8]}"
    session = DPDASession(name=f"session_{dpda_id}")

    try:
        session.new_dpda(request.name)
        sessions[dpda_id] = session

        return CreateDPDAResponse(
            id=dpda_id,
            name=request.name,
            created=True,
            message="DPDA created successfully"
        )
    except SessionError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/dpda/{dpda_id}", response_model=DPDAInfoResponse)
async def get_dpda_info(dpda_id: str):
    """Get information about a DPDA."""
    if dpda_id not in sessions:
        raise HTTPException(status_code=404, detail="DPDA not found")

    session = sessions[dpda_id]
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


@app.post("/api/dpda/{dpda_id}/states")
async def set_states(dpda_id: str, request: SetStatesRequest):
    """Set DPDA states."""
    if dpda_id not in sessions:
        raise HTTPException(status_code=404, detail="DPDA not found")

    session = sessions[dpda_id]

    try:
        # Set states directly as strings
        session.set_states(set(request.states))

        # Set initial state
        session.set_initial_state(request.initial_state)

        # Set accept states
        session.set_accept_states(set(request.accept_states))

        return {"success": True, "message": "States configured successfully"}
    except (SessionError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/dpda/{dpda_id}/alphabets")
async def set_alphabets(dpda_id: str, request: SetAlphabetsRequest):
    """Set DPDA alphabets."""
    if dpda_id not in sessions:
        raise HTTPException(status_code=404, detail="DPDA not found")

    session = sessions[dpda_id]

    try:
        session.set_input_alphabet(set(request.input_alphabet))
        session.set_stack_alphabet(set(request.stack_alphabet))
        session.set_initial_stack_symbol(request.initial_stack_symbol)

        return {"success": True, "message": "Alphabets configured successfully"}
    except SessionError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/dpda/{dpda_id}/transition")
async def add_transition(dpda_id: str, request: AddTransitionRequest):
    """Add a transition to the DPDA."""
    if dpda_id not in sessions:
        raise HTTPException(status_code=404, detail="DPDA not found")

    session = sessions[dpda_id]

    try:
        # Handle stack push
        if request.stack_push:
            stack_push = ",".join(request.stack_push)
        else:
            stack_push = None

        session.add_transition(
            from_state=request.from_state,
            input_symbol=request.input_symbol,
            stack_top=request.stack_top,
            to_state=request.to_state,
            stack_push=stack_push
        )

        return {"added": True, "message": "Transition added successfully"}
    except (SessionError, ValueError, IndexError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/dpda/{dpda_id}/transition/{index}", response_model=DeleteTransitionResponse)
async def delete_transition(dpda_id: str, index: int):
    """Delete a transition from the DPDA."""
    if dpda_id not in sessions:
        raise HTTPException(status_code=404, detail="DPDA not found")

    session = sessions[dpda_id]

    try:
        session.remove_transition(index)
        return DeleteTransitionResponse(
            deleted=True,
            message="Transition removed successfully",
            remaining_transitions=len(session.current_builder.transitions)
        )
    except (SessionError, IndexError) as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/dpda/{dpda_id}/compute", response_model=ComputeResponse)
async def compute_string(dpda_id: str, request: ComputeRequest):
    """Compute whether a string is accepted by the DPDA."""
    if dpda_id not in sessions:
        raise HTTPException(status_code=404, detail="DPDA not found")

    session = sessions[dpda_id]

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
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/dpda/{dpda_id}/validate", response_model=ValidationResponse)
async def validate_dpda(dpda_id: str):
    """Validate the DPDA for determinism properties."""
    if dpda_id not in sessions:
        raise HTTPException(status_code=404, detail="DPDA not found")

    session = sessions[dpda_id]

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
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/dpda/{dpda_id}/export", response_model=ExportResponse)
async def export_dpda(dpda_id: str, format: str = Query("json", description="Export format")):
    """Export the DPDA definition."""
    if dpda_id not in sessions:
        raise HTTPException(status_code=404, detail="DPDA not found")

    session = sessions[dpda_id]

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
            raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")
    except SessionError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/dpda/{dpda_id}/visualize", response_model=VisualizationResponse)
async def visualize_dpda(dpda_id: str, format: str = Query("dot", description="Visualization format")):
    """Generate visualization data for the DPDA."""
    if dpda_id not in sessions:
        raise HTTPException(status_code=404, detail="DPDA not found")

    session = sessions[dpda_id]

    try:
        dpda = session.build_current_dpda()
        graph_builder = GraphBuilder()

        if format == "dot":
            data = graph_builder.to_dot(dpda)
            return VisualizationResponse(format="dot", data=data)
        elif format == "d3":
            data = graph_builder.to_d3_json(dpda)
            return VisualizationResponse(format="d3", data=data)
        elif format == "cytoscape":
            data = graph_builder.to_cytoscape(dpda)
            return VisualizationResponse(format="cytoscape", data=data)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")
    except SessionError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/dpda/list", response_model=ListDPDAsResponse)
async def list_dpdas():
    """List all DPDAs."""
    dpda_list = []
    for dpda_id, session in sessions.items():
        builder = session.current_builder
        is_valid = False

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
            "name": session.current_dpda_name or "unnamed",
            "is_valid": is_valid
        })

    return ListDPDAsResponse(dpdas=dpda_list, count=len(dpda_list))


@app.delete("/api/dpda/{dpda_id}")
async def delete_dpda(dpda_id: str):
    """Delete a DPDA."""
    if dpda_id not in sessions:
        raise HTTPException(status_code=404, detail="DPDA not found")

    del sessions[dpda_id]
    return {"deleted": True, "message": "DPDA deleted successfully"}