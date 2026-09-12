import json
import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from livekit.api import AccessToken, VideoGrants
from server.config import LIVEKIT_API_KEY, LIVEKIT_API_SECRET, LIVEKIT_URL
from server.db import record_session_start

router = APIRouter(prefix="/api", tags=["tokens"])

class TokenRequest(BaseModel):
    room_name: Optional[str] = None
    identity: Optional[str] = None
    name: Optional[str] = None
    vertical: Optional[str] = "dispatch"

class TokenResponse(BaseModel):
    token: str
    url: str
    room_name: str
    identity: str
    vertical: str

@router.post("/token", response_model=TokenResponse)
async def create_token(req: TokenRequest):
    if not LIVEKIT_API_KEY or not LIVEKIT_API_SECRET:
        raise HTTPException(status_code=500, detail="LiveKit credentials are not configured on the server.")

    room = req.room_name or f"room-{uuid.uuid4().hex[:8]}"
    identity = req.identity or f"caller-{uuid.uuid4().hex[:6]}"
    name = req.name or f"Operator ({req.vertical.capitalize()})"
    vertical = req.vertical or "dispatch"

    metadata = json.dumps({"vertical": vertical, "caller_name": name})

    try:
        grant = VideoGrants(
            room_join=True,
            room=room,
            can_publish=True,
            can_subscribe=True,
            can_publish_data=True,
        )

        jwt_token = (
            AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
            .with_identity(identity)
            .with_name(name)
            .with_metadata(metadata)
            .with_grants(grant)
            .to_jwt()
        )

        record_session_start(room, vertical, {"identity": identity, "name": name})

        # Explicitly dispatch agent worker to this room
        try:
            from livekit.api import LiveKitAPI
            from livekit.protocol import agent_dispatch
            async with LiveKitAPI(LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET) as api:
                dispatch_req = agent_dispatch.CreateAgentDispatchRequest(
                    agent_name="sub10ms-voice-agent",
                    room=room,
                    metadata=metadata,
                )
                await api.agent_dispatch.create_dispatch(dispatch_req)
        except Exception as dispatch_err:
            pass

        return TokenResponse(
            token=jwt_token,
            url=LIVEKIT_URL,
            room_name=room,
            identity=identity,
            vertical=vertical,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate LiveKit token: {str(e)}")
