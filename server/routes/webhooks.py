import asyncio
import logging
from typing import Any, Dict
from fastapi import APIRouter, BackgroundTasks, Request
from server.db import record_session_start, record_session_end, CALLS_STORE
from server.db import get_custom_schemas_for_vertical, store_extraction_results

logger = logging.getLogger("server.webhooks")
router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


async def _run_post_call_extraction(room_name: str, vertical: str, turn_count: int):
    """Background task: extract structured outputs after a call ends."""
    try:
        from agent.structured_outputs import run_extraction_for_call
        call_record = CALLS_STORE.get(room_name, {})
        start_time = call_record.get("start_time", 0)
        end_time = call_record.get("end_time", 0)
        duration = max(end_time - start_time, 0.0)

        custom_schemas = get_custom_schemas_for_vertical(vertical)
        results = await run_extraction_for_call(
            call_id=room_name,
            vertical=vertical,
            message_count=turn_count,
            call_duration_seconds=duration,
            ended_reason="room-finished",
            custom_schemas=custom_schemas,
        )
        store_extraction_results(room_name, [r.to_dict() for r in results])
        extracted = [r.name for r in results if not r.skipped and r.result]
        skipped = [r.name for r in results if r.skipped]
        logger.info(
            f"[{room_name}] Structured extraction complete — "
            f"extracted: {extracted}, skipped: {skipped}"
        )
    except Exception as e:
        logger.error(f"[{room_name}] Structured extraction error: {e}")


@router.post("/livekit")
async def handle_livekit_webhook(request: Request, background_tasks: BackgroundTasks):
    """Webhook listener for LiveKit Cloud room events."""
    try:
        body = await request.json()
        event = body.get("event")
        room_info = body.get("room", {})
        room_name = room_info.get("name", "unknown")

        logger.info(f"LiveKit Webhook received: {event} for room {room_name}")

        if event == "room_started":
            # Parse vertical from room metadata
            vertical = "dispatch"
            metadata = room_info.get("metadata", "")
            if metadata:
                try:
                    import json
                    meta = json.loads(metadata)
                    vertical = meta.get("vertical", "dispatch")
                except Exception:
                    if metadata in ["dispatch", "healthcare", "field_worker",
                                    "customer_support", "logistics_fleet", "financial_compliance"]:
                        vertical = metadata
            record_session_start(room_name, vertical, room_info)

        elif event == "room_finished":
            record_session_end(room_name)
            call_record = CALLS_STORE.get(room_name, {})
            vertical = call_record.get("vertical", "dispatch")
            turn_count = call_record.get("turns", 0)
            # Fire extraction off the critical path
            background_tasks.add_task(
                _run_post_call_extraction, room_name, vertical, turn_count
            )
            logger.info(
                f"[{room_name}] room_finished — queued structured extraction "
                f"({turn_count} turns, vertical={vertical})"
            )

        return {"status": "success", "event": event}
    except Exception as e:
        logger.error(f"Error handling webhook: {e}")
        return {"status": "ignored", "error": str(e)}
