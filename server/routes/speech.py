import logging
from typing import Optional
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import edge_tts

logger = logging.getLogger("server.speech")
router = APIRouter(prefix="/v1", tags=["speech"])

class SpeechRequest(BaseModel):
    model: Optional[str] = "edge-tts"
    input: str
    voice: Optional[str] = "en-US-AriaNeural"
    response_format: Optional[str] = "mp3"
    speed: Optional[float] = 1.0

VOICE_MAP = {
    "alloy": "en-US-AriaNeural",
    "ash": "en-US-GuyNeural",
    "echo": "en-US-ChristopherNeural",
    "coral": "en-US-JennyNeural",
    "shimmer": "en-US-AriaNeural",
    "af_bella": "en-US-JennyNeural",
}

@router.post("/audio/speech")
async def generate_speech(req: SpeechRequest):
    voice_name = VOICE_MAP.get(req.voice, req.voice or "en-US-AriaNeural")
    logger.info(f"Synthesizing edge-tts speech for: '{req.input[:40]}...' using {voice_name}")
    
    communicate = edge_tts.Communicate(req.input, voice_name)

    async def audio_stream():
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                yield chunk["data"]

    return StreamingResponse(
        audio_stream(),
        media_type="audio/mpeg",
        headers={
            "Content-Type": "audio/mpeg",
            "Transfer-Encoding": "chunked",
        }
    )
