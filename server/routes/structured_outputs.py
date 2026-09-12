"""Structured Outputs API — schema registry and extraction results endpoints."""
import time
import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from server.db import (
    register_schema, get_schema, list_schemas, delete_schema,
    get_extraction_results, store_extraction_results,
    get_custom_schemas_for_vertical,
)
from agent.structured_outputs import run_extraction_for_call, VERTICAL_SCHEMAS
from agent.memory import memory_manager

router = APIRouter(prefix="/api/structured-outputs", tags=["structured-outputs"])


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------
class ExtractionCondition(BaseModel):
    type: str                           # "minMessages" | "minCallDuration" | "endedReason"
    count: Optional[int] = None
    seconds: Optional[int] = None
    operator: Optional[str] = None      # "oneOf" | "notOneOf"
    values: Optional[List[str]] = None


class CustomModelConfig(BaseModel):
    provider: str = "google"
    model: str = "gemini-2.0-flash"
    temperature: float = 0.1
    messages: Optional[List[Dict[str, Any]]] = None


class SchemaCreateRequest(BaseModel):
    name: str = Field(..., max_length=40)
    vertical: str
    description: Optional[str] = None
    schema_definition: Dict[str, Any] = Field(..., alias="schema")
    conditions: Optional[List[ExtractionCondition]] = None
    model: Optional[CustomModelConfig] = None

    model_config = {"populate_by_name": True}


class ManualExtractRequest(BaseModel):
    call_id: str
    vertical: str
    message_count: Optional[int] = None
    call_duration_seconds: float = 0.0
    ended_reason: str = "agent-ended-call"


# ---------------------------------------------------------------------------
# Schema CRUD
# ---------------------------------------------------------------------------
@router.get("")
async def list_all_schemas(vertical: Optional[str] = None):
    """List all registered structured output schemas.
    Optionally filter by ?vertical=dispatch
    """
    custom = list_schemas(vertical)
    # Include default schemas in the listing
    defaults = []
    for v, sdef in VERTICAL_SCHEMAS.items():
        if vertical and v != vertical:
            continue
        defaults.append({
            "schema_id": f"default_{v}",
            "vertical": v,
            "name": sdef["name"],
            "description": sdef.get("description", ""),
            "is_default": True,
            "schema": sdef["schema"],
        })
    return {"schemas": defaults + custom, "total": len(defaults) + len(custom)}


@router.post("", status_code=201)
async def create_schema(req: SchemaCreateRequest):
    """Register a new structured output schema definition."""
    schema_id = f"custom_{uuid.uuid4().hex[:8]}"
    definition = {
        "name": req.name,
        "vertical": req.vertical,
        "description": req.description,
        "schema": req.schema_definition,
        "conditions": [c.model_dump(exclude_none=True) for c in req.conditions] if req.conditions else [],
        "model": req.model.model_dump() if req.model else None,
        "created_at": time.time(),
        "is_default": False,
    }
    register_schema(schema_id, definition)
    return {"schema_id": schema_id, **definition}


@router.get("/defaults")
async def list_default_schemas():
    """List the built-in default schemas for every vertical."""
    return {
        v: {
            "schema_id": f"default_{v}",
            "name": sdef["name"],
            "description": sdef.get("description", ""),
            "schema": sdef["schema"],
        }
        for v, sdef in VERTICAL_SCHEMAS.items()
    }


@router.get("/{schema_id}")
async def get_one_schema(schema_id: str):
    """Retrieve a single schema by ID."""
    # Check default schemas first
    if schema_id.startswith("default_"):
        vertical = schema_id.removeprefix("default_")
        sdef = VERTICAL_SCHEMAS.get(vertical)
        if sdef:
            return {"schema_id": schema_id, "vertical": vertical, "is_default": True, **sdef}
    schema = get_schema(schema_id)
    if not schema:
        raise HTTPException(status_code=404, detail=f"Schema '{schema_id}' not found")
    return schema


@router.delete("/{schema_id}", status_code=204)
async def remove_schema(schema_id: str):
    """Delete a custom schema. Default schemas cannot be deleted."""
    if schema_id.startswith("default_"):
        raise HTTPException(status_code=400, detail="Default schemas cannot be deleted")
    if not delete_schema(schema_id):
        raise HTTPException(status_code=404, detail=f"Schema '{schema_id}' not found")


# ---------------------------------------------------------------------------
# Extraction results
# ---------------------------------------------------------------------------
@router.get("/results/{call_id}")
async def get_call_results(call_id: str):
    """Get all structured output extraction results for a completed call."""
    results = get_extraction_results(call_id)
    return {
        "call_id": call_id,
        "total": len(results),
        "results": results,
    }


# ---------------------------------------------------------------------------
# Manual extraction trigger (for testing / replay)
# ---------------------------------------------------------------------------
@router.post("/extract")
async def trigger_extraction(req: ManualExtractRequest, background_tasks: BackgroundTasks):
    """Manually trigger structured output extraction for a call.

    Useful for replaying extraction on a finished call or testing schemas.
    Extraction runs in the background; poll GET /results/{call_id} for results.
    """
    history = memory_manager.get_history(req.call_id)
    message_count = req.message_count if req.message_count is not None else len(history)

    custom_schemas = get_custom_schemas_for_vertical(req.vertical)

    async def _run():
        results = await run_extraction_for_call(
            call_id=req.call_id,
            vertical=req.vertical,
            message_count=message_count,
            call_duration_seconds=req.call_duration_seconds,
            ended_reason=req.ended_reason,
            custom_schemas=custom_schemas,
        )
        store_extraction_results(req.call_id, [r.to_dict() for r in results])

    background_tasks.add_task(_run)

    return {
        "status": "extraction_queued",
        "call_id": req.call_id,
        "vertical": req.vertical,
        "message_count": message_count,
        "poll_url": f"/api/structured-outputs/results/{req.call_id}",
    }
