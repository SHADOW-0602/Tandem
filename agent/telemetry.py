"""High-precision latency telemetry and instrumentation engine."""
import asyncio
import json
import logging
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional
import httpx
from agent.config import CONTROL_PLANE_URL, TARGET_TOTAL_MS

logger = logging.getLogger("agent.telemetry")

@dataclass
class TurnTelemetry:
    call_id: str
    turn_id: int
    vertical: str
    user_transcript: str
    agent_response: str
    retrieved_doc_ids: List[str] = field(default_factory=list)
    retrieved_snippets: List[str] = field(default_factory=list)
    guardrail_action: Optional[str] = None
    
    # Latency Breakdown (milliseconds)
    stt_latency_ms: float = 0.0
    moss_latency_ms: float = 0.0
    qdrant_latency_ms: float = 0.0
    llm_ttft_ms: float = 0.0
    tts_ttfb_ms: float = 0.0
    total_latency_ms: float = 0.0
    
    is_sub_10ms_moss: bool = True
    is_sub_10ms_retrieval: bool = True
    within_budget: bool = True
    timestamp: float = field(default_factory=time.time)

class LatencyTracker:
    def __init__(self, call_id: str, vertical: str, turn_id: int = 1):
        self.call_id = call_id
        self.vertical = vertical
        self.turn_id = turn_id
        
        self.t_stt_final: float = 0.0
        self.t_moss_start: float = 0.0
        self.t_moss_end: float = 0.0
        self.qdrant_ms: float = 0.0
        self.t_llm_start: float = 0.0
        self.t_llm_first_token: float = 0.0
        self.t_tts_start: float = 0.0
        self.t_tts_first_byte: float = 0.0
        
        self.retrieved_doc_ids: List[str] = []
        self.retrieved_snippets: List[str] = []
        self.guardrail_action: Optional[str] = None

    def mark_stt_final(self):
        self.t_stt_final = time.perf_counter()

    def start_moss(self):
        self.t_moss_start = time.perf_counter()

    def finish_moss(self, doc_ids: List[str], snippets: List[str]):
        self.t_moss_end = time.perf_counter()
        self.retrieved_doc_ids = doc_ids
        self.retrieved_snippets = snippets

    def finish_co_retrieval(self, doc_ids: List[str], snippets: List[str], moss_ms: float, qdrant_ms: float):
        self.t_moss_end = time.perf_counter()
        self.retrieved_doc_ids = doc_ids
        self.retrieved_snippets = snippets
        self.qdrant_ms = qdrant_ms

    def start_llm(self):
        self.t_llm_start = time.perf_counter()

    def mark_llm_first_token(self):
        if self.t_llm_first_token == 0.0:
            self.t_llm_first_token = time.perf_counter()

    def start_tts(self):
        self.t_tts_start = time.perf_counter()

    def mark_tts_first_byte(self):
        if self.t_tts_first_byte == 0.0:
            self.t_tts_first_byte = time.perf_counter()

    def compute(self, user_transcript: str, agent_response: str) -> TurnTelemetry:
        t_now = time.perf_counter()
        ref = self.t_stt_final if self.t_stt_final > 0 else self.t_moss_start
        
        moss_ms = (self.t_moss_end - self.t_moss_start) * 1000 if self.t_moss_end > self.t_moss_start else 0.0
        llm_ttft = (self.t_llm_first_token - self.t_llm_start) * 1000 if self.t_llm_first_token > self.t_llm_start else 0.0
        tts_ttfb = (self.t_tts_first_byte - self.t_tts_start) * 1000 if self.t_tts_first_byte > self.t_tts_start else 0.0
        total_ms = (t_now - ref) * 1000 if ref > 0 else 0.0

        telemetry = TurnTelemetry(
            call_id=self.call_id,
            turn_id=self.turn_id,
            vertical=self.vertical,
            user_transcript=user_transcript,
            agent_response=agent_response,
            retrieved_doc_ids=self.retrieved_doc_ids,
            retrieved_snippets=self.retrieved_snippets,
            guardrail_action=self.guardrail_action,
            stt_latency_ms=250.0, # Estimated streaming buffer
            moss_latency_ms=round(moss_ms, 2),
            qdrant_latency_ms=round(self.qdrant_ms, 2),
            llm_ttft_ms=round(llm_ttft, 2),
            tts_ttfb_ms=round(tts_ttfb, 2),
            total_latency_ms=round(total_ms, 2),
            is_sub_10ms_moss=(moss_ms < 10.0),
            is_sub_10ms_retrieval=(max(moss_ms, self.qdrant_ms) < 10.0),
            within_budget=(total_ms <= TARGET_TOTAL_MS),
        )
        return telemetry

async def report_telemetry(telemetry: TurnTelemetry):
    """Sends telemetry payload asynchronously to FastAPI control plane."""
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            await client.post(
                f"{CONTROL_PLANE_URL}/api/telemetry",
                json=asdict(telemetry)
            )
    except Exception as e:
        logger.debug(f"Telemetry submission note: {e}")
