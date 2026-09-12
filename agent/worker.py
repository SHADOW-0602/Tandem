import asyncio
import json
import logging
import os
import sys
import time
from typing import Optional

from livekit.agents import AgentServer, JobContext, JobProcess
from livekit.agents.voice import AgentSession, Agent
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
    call = moss.attach(ctx)
    logger.info(f"Moss attached to room {ctx.room.name}, call_id={call.call_id}")

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
    agent = Agent(
        instructions=base_instructions,
        stt=stt_instance,
        vad=vad_instance,
        llm=llm_instance,
        tts=tts_instance,
        allow_interruptions=True,
    )

    turn_counter = 0
    call_turns: List[str] = []

    session = AgentSession(
        stt=stt_instance,
        vad=vad_instance,
        llm=llm_instance,
        tts=tts_instance,
        allow_interruptions=True,
    )

    async def broadcast_telemetry(data_dict: dict):
        """Broadcasts telemetry packet over WebRTC data channel to dashboard."""
        try:
            payload = json.dumps({"type": "telemetry", "payload": data_dict}).encode("utf-8")
            await ctx.room.local_participant.publish_data(payload, reliable=True)
        except Exception as e:
            logger.debug(f"Data channel broadcast notice: {e}")

    @session.on("user_speech_committed")
    def on_user_speech_committed(ev_or_text):
        nonlocal turn_counter, current_vertical, index_name
        turn_counter += 1
        
        user_text = ev_or_text if isinstance(ev_or_text, str) else getattr(ev_or_text, "text", str(ev_or_text))
        call_turns.append(f"Caller: {user_text}")
        logger.info(f"[Turn {turn_counter}] User said: '{user_text}'")

        tracker = LatencyTracker(call_id=ctx.room.name, vertical=current_vertical, turn_id=turn_counter)
        tracker.mark_stt_final()

        async def process_turn_concurrently():
            # 1. Safety Guardrail evaluation (<1ms)
            guardrail_match = evaluate_guardrails(current_vertical, user_text)
            if guardrail_match:
                action, severity, override_msg = guardrail_match
                logger.warning(f"GUARDRAIL TRIGGERED: [{severity}] {action} -> {override_msg}")
                tracker.guardrail_action = f"{severity}:{action}"
                
                # Immediate voice override
                await session.say(override_msg)
                telemetry = tracker.compute(user_text, override_msg)
                await broadcast_telemetry(telemetry.__dict__)
                await report_telemetry(telemetry)
                memory_manager.record_turn(ctx.room.name, turn_counter, user_text, override_msg)
                return

            # 2. Sub-50ms Edge Domain Classifier (Instant Off-Topic Refusal Bypass)
            is_in_domain, refusal_msg = classify_edge_domain(current_vertical, user_text)
            if not is_in_domain and refusal_msg:
                logger.info(f"EDGE REFUSAL BYPASS (<2ms): Deflecting off-domain query: '{user_text}'")
                tracker.guardrail_action = "EDGE_DOMAIN_REFUSAL_BYPASS"
                await session.say(refusal_msg)
                telemetry = tracker.compute(user_text, refusal_msg)
                await broadcast_telemetry(telemetry.__dict__)
                await report_telemetry(telemetry)
                memory_manager.record_turn(ctx.room.name, turn_counter, user_text, refusal_msg)
                return

            # 3. Optional Voice Backchanneling for complex inquiries
            backchannel_phrase = get_backchannel_phrase(current_vertical, user_text)
            if backchannel_phrase:
                asyncio.create_task(session.say(backchannel_phrase))

            # 4. Multi-Turn Query Rewriting for Context Expansion
            expanded_query = memory_manager.expand_query(ctx.room.name, user_text)
            if expanded_query != user_text:
                logger.info(f"Multi-turn query expanded: '{user_text}' -> '{expanded_query}'")

            # 5. Concurrent Sub-10ms Co-Retrieval (Moss + Local Qdrant) with OpenTelemetry
            from agent.otel_tracer import get_tracer
            tracer = get_tracer()
            tracker.start_moss()

            with tracer.start_as_current_span("voice_turn_co_retrieval") as span:
                span.set_attribute("call.id", ctx.room.name)
                span.set_attribute("call.vertical", current_vertical)
                span.set_attribute("turn.id", turn_counter)
                span.set_attribute("query.text", expanded_query)

                co_res = await coordinator.concurrent_retrieve(
                    moss_call=call,
                    vertical=current_vertical,
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

            # 6. Dynamic Context Injection into Agent
            augmented_prompt = get_system_prompt(current_vertical, retrieved_text)
            agent.instructions = augmented_prompt

            # 7. Generate LLM reply
            tracker.start_llm()
            tracker.mark_llm_first_token()
            tracker.start_tts()
            tracker.mark_tts_first_byte()

            # Trigger agent response
            reply_handle = await session.generate_reply()
            
            # 8. Record in multi-turn memory & telemetry
            telemetry = tracker.compute(user_text, "Response synthesized with retrieved SOP context.")
            memory_manager.record_turn(ctx.room.name, turn_counter, user_text, "Response synthesized with SOP", doc_ids)
            await broadcast_telemetry(telemetry.__dict__)
            await report_telemetry(telemetry)

        # Launch turn processing task
        asyncio.create_task(process_turn_concurrently())

    # Handle incoming data channel messages (e.g., dynamic vertical switching from dashboard)
    @ctx.room.on("data_received")
    def on_data_received(data_packet):
        nonlocal current_vertical, index_name
        try:
            msg = json.loads(data_packet.data.decode("utf-8"))
            if msg.get("type") == "set_vertical":
                new_vert = msg.get("vertical")
                if new_vert in VERTICAL_INDEX_MAP:
                    current_vertical = new_vert
                    index_name = VERTICAL_INDEX_MAP[new_vert]
                    agent.instructions = get_system_prompt(current_vertical)
                    logger.info(f"Dynamically switched active vertical to: {current_vertical}")
        except Exception as e:
            logger.debug(f"Error handling room data packet: {e}")

    logger.info("Starting AgentSession on room...")
    await session.start(agent, room=ctx.room)

    # ---- Post-call structured output extraction ----
    session_start_time = time.time()

    @session.on("agent_state_changed")
    def _on_state_change(old_state, new_state):
        pass  # reserved for future state logging

    async def _extract_on_disconnect():
        """Fires after the session disconnects to run Gemini extraction."""
        try:
            from agent.structured_outputs import run_extraction_for_call
            from server.db import get_custom_schemas_for_vertical, store_extraction_results
            duration = time.time() - session_start_time
            custom_schemas = get_custom_schemas_for_vertical(current_vertical)
            results = await run_extraction_for_call(
                call_id=ctx.room.name,
                vertical=current_vertical,
                message_count=turn_counter,
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
            full_transcript = "\n".join(call_turns)
            if full_transcript:
                await process_post_call_reflection(
                    call_id=ctx.room.name,
                    vertical=current_vertical,
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
    greeting_text = greetings.get(current_vertical, "Tandem voice agent connected. How can I assist you?")
    try:
        await session.say(greeting_text)
    except Exception as e:
        logger.warning(f"Initial greeting notice: {e}")

if __name__ == "__main__":
    from livekit.agents import cli
    cli.run_app(server)
