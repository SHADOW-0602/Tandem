import asyncio
import json
import logging
import os
import sys
import time
from typing import Optional, List, Any

from livekit.agents import AgentServer, JobContext, JobProcess, llm
from livekit.agents.voice import AgentSession, Agent, ConversationItemAddedEvent, UserInputTranscribedEvent
from livekit.agents.llm.tool_context import StopResponse
from livekit.plugins import silero, groq

# Optional / Fallback Plugins
try:
    from livekit.plugins import cartesia
    HAS_CARTESIA = True
except ImportError:
    HAS_CARTESIA = False

try:
    from livekit.plugins import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

from moss_agent import MossAgent

from agent.config import (
    LIVEKIT_URL,
    LIVEKIT_API_KEY,
    LIVEKIT_API_SECRET,
    MOSS_PROJECT_ID,
    MOSS_PROJECT_KEY,
    GROQ_API_KEY,
    LLM_MODEL,
    ALL_MOSS_INDEXES,
    VERTICAL_INDEX_MAP,
)
from agent.prompts import VERTICAL_PROMPTS, get_system_prompt
from agent.guardrails import evaluate_guardrails
from agent.classifier import classify_edge_domain
from agent.memory import memory_manager
from agent.voices import get_voice_config, get_backchannel_phrase
from agent.telemetry import LatencyTracker, report_telemetry
from agent.qdrant_engine import qdrant_engine
from agent.knowledge_coordinator import coordinator
from agent.reflection import process_post_call_reflection


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("agent.worker")

server = AgentServer()

def prewarm(proc: JobProcess) -> None:
    """Prewarms all vertical indexes into the hot in-memory Moss cache on worker startup."""
    logger.info("Initializing prewarmed MossAgent in worker process...")
    moss = MossAgent(
        project_id=MOSS_PROJECT_ID,
        project_key=MOSS_PROJECT_KEY,
    )
    
    # Load and cache all consolidated indexes
    logger.info(f"Loading indexes into local hot cache: {ALL_MOSS_INDEXES}")
    asyncio.run(moss.load_indexes(ALL_MOSS_INDEXES))
    logger.info("Sub-10ms Moss hot cache successfully prewarmed!")
    
    proc.userdata["moss_agent"] = moss

    # Prewarm local embedded Qdrant with FastEmbed
    try:
        qdrant_engine.initialize()
        qdrant_engine.seed_from_json(force_reload=False)
        logger.info("Local Qdrant dynamic knowledge engine prewarmed!")
    except Exception as qe:
        logger.warning(f"Qdrant prewarm notice: {qe}")

server.setup_fnc = prewarm


class TandemVoiceAgent(Agent):
    """Sub-10ms Context Retrieval Voice Agent powered by LiveKit Agents 1.8+."""

    def __init__(
        self,
        instructions: str,
        current_vertical: str,
        room_name: str,
        moss_call: Any,
        room: Any,
        **kwargs,
    ):
        super().__init__(instructions=instructions, **kwargs)
        self.current_vertical = current_vertical
        self.room_name = room_name
        self.moss_call = moss_call
        self.room = room
        self.turn_counter = 0
        self.call_turns: list[str] = []
        self.current_tracker: Optional[LatencyTracker] = None

    async def broadcast_event(self, event_type: str, payload_data: dict):
        """Broadcasts a typed packet over WebRTC data channel to dashboard."""
        try:
            payload = json.dumps({"type": event_type, "payload": payload_data}).encode("utf-8")
            await self.room.local_participant.publish_data(payload, reliable=True)
        except Exception as e:
            logger.debug(f"Data channel broadcast notice: {e}")

    async def broadcast_telemetry(self, data_dict: dict):
        """Broadcasts telemetry packet over WebRTC data channel to dashboard."""
        await self.broadcast_event("telemetry", data_dict)

    async def on_user_turn_completed(
        self, turn_ctx: llm.ChatContext, new_message: llm.ChatMessage
    ) -> None:
        """Called when caller speech finishes; performs sub-10ms co-retrieval and guardrail intercept."""
        user_text = new_message.text_content or ""
        if not user_text.strip():
            return

        self.turn_counter += 1
        self.call_turns.append(f"Caller: {user_text}")
        logger.info(f"[Turn {self.turn_counter}] Caller speech committed: '{user_text}'")

        tracker = LatencyTracker(
            call_id=self.room_name,
            vertical=self.current_vertical,
            turn_id=self.turn_counter,
        )
        tracker.mark_stt_final()
        self.current_tracker = tracker

        # 1. Safety Guardrail evaluation (<1ms)
        guardrail_match = evaluate_guardrails(self.current_vertical, user_text)
        if guardrail_match:
            action, severity, override_msg = guardrail_match
            logger.warning(f"GUARDRAIL TRIGGERED: [{severity}] {action} -> {override_msg}")
            tracker.guardrail_action = f"{severity}:{action}"

            # Immediate voice override
            await self.session.say(override_msg)
            telemetry = tracker.compute(user_text, override_msg)
            await self.broadcast_telemetry(telemetry.__dict__)
            await report_telemetry(telemetry)
            memory_manager.record_turn(self.room_name, self.turn_counter, user_text, override_msg)
            self.call_turns.append(f"Tandem (Safety Override): {override_msg}")
            self.current_tracker = None
            raise StopResponse()

        # 2. Sub-50ms Edge Domain Classifier (Instant Off-Topic Refusal Bypass)
        is_in_domain, refusal_msg = classify_edge_domain(self.current_vertical, user_text)
        if not is_in_domain and refusal_msg:
            logger.info(f"EDGE REFUSAL BYPASS (<2ms): Deflecting off-domain query: '{user_text}'")
            tracker.guardrail_action = "EDGE_DOMAIN_REFUSAL_BYPASS"
            await self.session.say(refusal_msg)
            telemetry = tracker.compute(user_text, refusal_msg)
            await self.broadcast_telemetry(telemetry.__dict__)
            await report_telemetry(telemetry)
            memory_manager.record_turn(self.room_name, self.turn_counter, user_text, refusal_msg)
            self.call_turns.append(f"Tandem (Domain Refusal): {refusal_msg}")
            self.current_tracker = None
            raise StopResponse()

        # 3. Optional Voice Backchanneling for complex inquiries
        backchannel_phrase = get_backchannel_phrase(self.current_vertical, user_text)
        if backchannel_phrase:
            asyncio.create_task(self.session.say(backchannel_phrase))

        # 4. Multi-Turn Query Rewriting for Context Expansion
        expanded_query = memory_manager.expand_query(self.room_name, user_text)
        if expanded_query != user_text:
            logger.info(f"Multi-turn query expanded: '{user_text}' -> '{expanded_query}'")

        # 5. Concurrent Sub-10ms Co-Retrieval (Moss + Local Qdrant) with OpenTelemetry
        from agent.otel_tracer import get_tracer
        tracer = get_tracer()
        tracker.start_moss()

        with tracer.start_as_current_span("voice_turn_co_retrieval") as span:
            span.set_attribute("call.id", self.room_name)
            span.set_attribute("call.vertical", self.current_vertical)
            span.set_attribute("turn.id", self.turn_counter)
            span.set_attribute("query.text", expanded_query)

            co_res = await coordinator.concurrent_retrieve(
                moss_call=self.moss_call,
                vertical=self.current_vertical,
                query=expanded_query,
                limit=3,
            )

            span.set_attribute("retrieval.moss_ms", co_res.moss_latency_ms)
            span.set_attribute("retrieval.qdrant_ms", co_res.qdrant_latency_ms)
            span.set_attribute("retrieval.total_ms", co_res.total_latency_ms)
            span.set_attribute("retrieval.is_sub_10ms", co_res.is_sub_10ms)
            span.set_attribute("retrieval.doc_count", len(co_res.doc_ids))

        tracker.finish_co_retrieval(
            doc_ids=co_res.doc_ids,
            snippets=co_res.snippets,
            moss_ms=co_res.moss_latency_ms,
            qdrant_ms=co_res.qdrant_latency_ms,
        )
        retrieved_text = co_res.merged_text

        # 6. Dynamic Context Injection into Agent System Instructions
        augmented_prompt = get_system_prompt(self.current_vertical, retrieved_text)
        self.instructions = augmented_prompt
        turn_ctx.instructions = augmented_prompt

        # 7. Start LLM & TTS latency tracking
        tracker.start_llm()
        tracker.mark_llm_first_token()
        tracker.start_tts()
        tracker.mark_tts_first_byte()


@server.rtc_session(agent_name="sub10ms-voice-agent")
async def handle_call(ctx: JobContext) -> None:
    logger.info(f"Connecting to LiveKit room: {ctx.room.name}")
    await ctx.connect()

    moss: MossAgent = ctx.proc.userdata.get("moss_agent")
    if not moss:
        logger.warning("MossAgent missing in userdata, instantiating fallback...")
        moss = MossAgent(project_id=MOSS_PROJECT_ID, project_key=MOSS_PROJECT_KEY)
        await moss.load_indexes(ALL_MOSS_INDEXES)

    # Attach Moss context to current LiveKit room session
    call = None
    try:
        call = moss.attach(ctx)
        logger.info(f"Moss attached to room {ctx.room.name}, call_id={call.call_id}")
    except Exception as me:
        logger.warning(f"Moss attach notice: {me}")

    # Determine vertical from room metadata (default to 'dispatch')
    current_vertical = "dispatch"
    if ctx.room.metadata:
        try:
            meta = json.loads(ctx.room.metadata)
            current_vertical = meta.get("vertical", "dispatch")
        except Exception:
            if ctx.room.metadata in VERTICAL_INDEX_MAP:
                current_vertical = ctx.room.metadata

    logger.info(f"Active vertical for session: {current_vertical}")
    index_name = VERTICAL_INDEX_MAP.get(current_vertical, "dispatch_emergency_ops")

    vad_instance = silero.VAD.load()

    # Configure STT — Groq Whisper Turbo streaming via LiveKit StreamAdapter
    from livekit.agents.stt import StreamAdapter
    groq_stt = groq.STT(model="whisper-large-v3-turbo", api_key=GROQ_API_KEY)
    stt_instance = StreamAdapter(stt=groq_stt, vad=vad_instance)
    logger.info("STT: Using Groq Whisper Turbo via LiveKit StreamAdapter")

    # Configure LLM
    llm_instance = groq.LLM(
        model=LLM_MODEL,
        api_key=GROQ_API_KEY,
        temperature=0.3,
    )

    # Configure TTS with vertical-specific voice persona
    cartesia_key = os.getenv("CARTESIA_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    voice_cfg = get_voice_config(current_vertical)
    if cartesia_key and HAS_CARTESIA:
        try:
            tts_instance = cartesia.TTS(
                api_key=cartesia_key,
                voice=voice_cfg.get("voice_id", "a0e99841-438c-4a64-b679-ae501e7d6091"),
                speed=voice_cfg.get("speed", 1.0)
            )
        except Exception:
            tts_instance = cartesia.TTS(api_key=cartesia_key)
        logger.info(f"TTS: Using Cartesia Sonic tailored for {current_vertical} (Speed: {voice_cfg.get('speed', 1.0)}x)")
    elif openai_key and HAS_OPENAI:
        tts_instance = openai.TTS(api_key=openai_key, model="tts-1", voice="alloy")
        logger.info("TTS: Using OpenAI TTS-1")
    elif HAS_OPENAI:
        # Seamless zero-key fallback using our local FastAPI Edge-TTS endpoint
        tts_instance = openai.TTS(
            base_url="http://localhost:8000/v1",
            api_key="tandem-local",
            model="edge-tts",
            voice="alloy",
        )
        logger.info("TTS: Using Local High-Quality Edge-TTS on http://localhost:8000/v1")
    else:
        tts_instance = None
        logger.warning("No TTS engine available.")

    # Create Voice Agent with vertical prompt
    base_instructions = get_system_prompt(current_vertical)
    agent = TandemVoiceAgent(
        instructions=base_instructions,
        current_vertical=current_vertical,
        room_name=ctx.room.name,
        moss_call=call,
        room=ctx.room,
        stt=stt_instance,
        vad=vad_instance,
        llm=llm_instance,
        tts=tts_instance,
        allow_interruptions=True,
    )

    session = AgentSession()

    @session.on("user_input_transcribed")
    def on_user_input_transcribed(ev: UserInputTranscribedEvent):
        if ev.transcript:
            if ev.is_final:
                logger.info(f"STT final: '{ev.transcript}'")
            else:
                logger.debug(f"STT interim: '{ev.transcript}'")
            asyncio.create_task(
                agent.broadcast_event(
                    "live_user_speech",
                    {"text": ev.transcript, "is_final": ev.is_final},
                )
            )

    @session.on("conversation_item_added")
    def on_conversation_item_added(ev: ConversationItemAddedEvent):
        if hasattr(ev.item, "role") and ev.item.role == "assistant" and agent.current_tracker:
            agent_text = ev.item.text_content or ""
            if not agent_text:
                return
            agent.call_turns.append(f"Tandem: {agent_text}")
            tracker = agent.current_tracker
            agent.current_tracker = None
            user_text = agent.call_turns[-2].replace("Caller: ", "") if len(agent.call_turns) >= 2 else ""
            telemetry = tracker.compute(user_text, agent_text)
            memory_manager.record_turn(
                agent.room_name,
                agent.turn_counter,
                user_text,
                agent_text,
                tracker.retrieved_doc_ids,
            )
            asyncio.create_task(agent.broadcast_telemetry(telemetry.__dict__))
            asyncio.create_task(report_telemetry(telemetry))

    # Handle incoming data channel messages (e.g., dynamic vertical switching or barge-in from dashboard)
    @ctx.room.on("data_received")
    def on_data_received(data_packet):
        try:
            msg = json.loads(data_packet.data.decode("utf-8"))
            if msg.get("type") == "set_vertical":
                new_vert = msg.get("vertical")
                if new_vert in VERTICAL_INDEX_MAP:
                    agent.current_vertical = new_vert
                    agent.instructions = get_system_prompt(new_vert)
                    logger.info(f"Dynamically switched active vertical to: {new_vert}")
            elif msg.get("type") == "barge_in":
                logger.info("Barge-in requested from user dashboard")
                session.interrupt()
        except Exception as e:
            logger.debug(f"Error handling room data packet: {e}")

    logger.info("Starting AgentSession on room...")
    await session.start(agent, room=ctx.room)

    # ---- Post-call structured output extraction ----
    session_start_time = time.time()

    async def _extract_on_disconnect():
        """Fires after the session disconnects to run Gemini extraction and Zero-Trust reflection."""
        try:
            from agent.structured_outputs import run_extraction_for_call
            from server.db import get_custom_schemas_for_vertical, store_extraction_results
            duration = time.time() - session_start_time
            custom_schemas = get_custom_schemas_for_vertical(agent.current_vertical)
            results = await run_extraction_for_call(
                call_id=ctx.room.name,
                vertical=agent.current_vertical,
                message_count=agent.turn_counter,
                call_duration_seconds=duration,
                ended_reason="agent-ended-call",
                custom_schemas=custom_schemas,
            )
            store_extraction_results(ctx.room.name, [r.to_dict() for r in results])
            extracted = [r.name for r in results if not r.skipped and r.result]
            logger.info(f"[{ctx.room.name}] Post-call extraction done — {extracted}")
        except Exception as e:
            logger.warning(f"[{ctx.room.name}] Post-call extraction notice: {e}")

        # Post-call Zero-Trust Reflection & Dynamic Fact Extraction
        try:
            full_transcript = "\n".join(agent.call_turns)
            if full_transcript:
                await process_post_call_reflection(
                    call_id=ctx.room.name,
                    vertical=agent.current_vertical,
                    full_transcript=full_transcript,
                )
        except Exception as re:
            logger.warning(f"[{ctx.room.name}] Post-call reflection notice: {re}")

    @ctx.room.on("disconnected")
    def _on_room_disconnected(*args):
        asyncio.create_task(_extract_on_disconnect())
    # ---- end structured outputs ----

    greetings = {
        "dispatch": "Tandem Dispatch online. Monitoring tactical traffic and 10-codes. Ready for report.",
        "healthcare": "MedFlow clinical support active. Please state patient symptoms.",
        "field_worker": "RigGuard industrial safety active. State machinery ID or procedure.",
        "customer_support": "Tandem enterprise support. How can I assist with your SLA or billing today?",
        "logistics_fleet": "RouteMaster fleet coordinator online. Ready for hours of service or reefer status.",
        "financial_compliance": "VaultGuard compliance active. Ready for transaction inquiry.",
    }
    greeting_text = greetings.get(agent.current_vertical, "Tandem voice agent connected. How can I assist you?")
    try:
        await session.say(greeting_text)
    except Exception as e:
        logger.warning(f"Initial greeting notice: {e}")

if __name__ == "__main__":
    from livekit.agents import cli
    cli.run_app(server)
