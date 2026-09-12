"""Knowledge Management REST Endpoints: Dynamic live updates, CRUD, and HITL review queue."""
import logging
import time
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from agent.qdrant_engine import qdrant_engine
from agent.reflection import (
    get_staged_facts,
    approve_staged_fact,
    reject_staged_fact,
    check_immutable_collision,
)

logger = logging.getLogger("server.routes.knowledge")

router = APIRouter(prefix="/api/knowledge", tags=["Dynamic Knowledge Base"])


class UpsertRequest(BaseModel):
    vertical: str = Field(description="Target vertical, e.g. 'dispatch', 'healthcare'")
    doc_id: str = Field(description="Unique document identifier, e.g. 'sop_detour_01'")
    title: str = Field(description="Title of SOP or operational update")
    text: str = Field(description="Body of SOP or instructions")
    category: str = Field(default="dynamic_update", description="Category taxonomy")
    ttl_hours: Optional[int] = Field(default=None, description="Optional TTL in hours before automatic expiration")
    is_immutable: bool = Field(default=False, description="Whether document is protected from deletion/overwriting")


class DeleteRequest(BaseModel):
    vertical: str
    doc_id: str
    force: bool = False


class SearchRequest(BaseModel):
    vertical: str
    query: str
    limit: int = 3


@router.get("/list")
async def list_knowledge(vertical: str = Query(..., description="Vertical name")):
    """Lists all active and expired documents in a vertical collection."""
    try:
        docs = qdrant_engine.list_documents(vertical=vertical, limit=100)
        return {
            "status": "success",
            "vertical": vertical,
            "count": len(docs),
            "documents": docs,
        }
    except Exception as e:
        logger.error(f"Error listing knowledge for {vertical}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upsert")
async def upsert_knowledge(req: UpsertRequest):
    """Dynamically adds or updates an SOP in the local vector store."""
    # Zero-Trust Check: reject if attempting to overwrite immutable safety protocol without admin flag
    collision = check_immutable_collision(req.title, req.text, req.vertical)
    if collision and not req.is_immutable:
        raise HTTPException(
            status_code=400,
            detail=f"Safety Guardrail: Document matches protected immutable pattern ({collision}).",
        )

    try:
        res = qdrant_engine.upsert_document(
            vertical=req.vertical,
            doc_id=req.doc_id,
            title=req.title,
            text=req.text,
            category=req.category,
            is_immutable=req.is_immutable,
            ttl_hours=req.ttl_hours,
        )
        return res
    except Exception as e:
        logger.error(f"Error upserting knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/delete")
async def delete_knowledge(req: DeleteRequest):
    """Deletes an SOP or dynamic fact from the local vector store."""
    try:
        success = qdrant_engine.delete_document(vertical=req.vertical, doc_id=req.doc_id, force=req.force)
        return {"status": "success" if success else "not_found", "doc_id": req.doc_id}
    except ValueError as ve:
        raise HTTPException(status_code=403, detail=str(ve))
    except Exception as e:
        logger.error(f"Error deleting knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search")
async def search_knowledge(req: SearchRequest):
    """Benchmarks and tests vector search latency in milliseconds."""
    t0 = time.perf_counter()
    try:
        results = qdrant_engine.query(vertical=req.vertical, query_text=req.query, limit=req.limit)
        elapsed_ms = (time.perf_counter() - t0) * 1000
        return {
            "status": "success",
            "vertical": req.vertical,
            "query": req.query,
            "latency_ms": round(elapsed_ms, 2),
            "is_sub_10ms": elapsed_ms <= 10.0,
            "result_count": len(results),
            "results": results,
        }
    except Exception as e:
        logger.error(f"Error searching knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/staging")
async def get_staging_queue():
    """Returns candidate operational facts awaiting human-in-the-loop review."""
    items = get_staged_facts()
    return {"status": "success", "count": len(items), "staged_facts": items}


@router.post("/staging/{stage_id}/approve")
async def approve_staging_item(stage_id: str):
    """Approves a staged fact and promotes it to the active Qdrant vector database."""
    item = approve_staged_fact(stage_id)
    if not item:
        raise HTTPException(status_code=404, detail="Staged item not found")
    return {"status": "approved", "item": item}


@router.post("/staging/{stage_id}/reject")
async def reject_staging_item(stage_id: str):
    """Rejects and dismisses a candidate fact."""
    success = reject_staged_fact(stage_id)
    if not success:
        raise HTTPException(status_code=404, detail="Staged item not found")
    return {"status": "rejected", "stage_id": stage_id}


@router.post("/seed")
async def seed_knowledge_base(force: bool = False):
    """Seeds baseline SOPs from JSON files into the local Qdrant engine."""
    try:
        counts = qdrant_engine.seed_from_json(force_reload=force)
        return {"status": "success", "seeded_collections": counts}
    except Exception as e:
        logger.error(f"Error seeding knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))
