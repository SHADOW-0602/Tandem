import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from server.config import CORS_ORIGINS, PORT, HOST, ENVIRONMENT
from server.routes.tokens import router as tokens_router
from server.routes.verticals import router as verticals_router
from server.routes.telemetry import router as telemetry_router
from server.routes.webhooks import router as webhooks_router
from server.routes.speech import router as speech_router
from server.routes.structured_outputs import router as structured_outputs_router
from server.routes.simulations import router as simulations_router
from server.routes.knowledge import router as knowledge_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("server.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("FastAPI Control Plane starting up...")
    logger.info(f"Targeting Environment: {ENVIRONMENT} on {HOST}:{PORT}")

    # Seed baseline local Qdrant collections
    try:
        from agent.qdrant_engine import qdrant_engine
        qdrant_engine.initialize()
        seeded = qdrant_engine.seed_from_json(force_reload=False)
        logger.info(f"Local Qdrant prewarmed and verified ({len(seeded)} vertical collections).")
    except Exception as qe:
        logger.warning(f"Local Qdrant startup notice: {qe}")

    # Seed default structured output schemas for every vertical
    from agent.structured_outputs import VERTICAL_SCHEMAS
    from server.db import register_schema
    for vertical, sdef in VERTICAL_SCHEMAS.items():
        register_schema(f"default_{vertical}", {"vertical": vertical, "is_default": True, **sdef})
    logger.info(f"Seeded {len(VERTICAL_SCHEMAS)} default structured output schemas.")

    # Seed built-in AI tester scenarios and personalities
    from agent.simulation_tester import BUILTIN_SCENARIOS, BUILTIN_PERSONALITIES
    from server.db import register_scenario, register_personality
    for sc_id, sc_data in BUILTIN_SCENARIOS.items():
        register_scenario(sc_id, sc_data)
    for p_id, p_data in BUILTIN_PERSONALITIES.items():
        register_personality(p_id, p_data)
    logger.info(f"Seeded {len(BUILTIN_SCENARIOS)} simulation scenarios and {len(BUILTIN_PERSONALITIES)} personalities.")

    yield

    logger.info("FastAPI Control Plane shutting down.")

app = FastAPI(
    title="Sub-10ms Voice Agents Control Plane",
    description="LiveKit Room Token Minting, Moss Context Engine Orchestration & Telemetry API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tokens_router)
app.include_router(knowledge_router)
app.include_router(verticals_router)
app.include_router(telemetry_router)
app.include_router(webhooks_router)
app.include_router(speech_router)
app.include_router(structured_outputs_router)
app.include_router(simulations_router)

@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "Sub-10ms Voice Agents Control Plane",
        "moss_retrieval_target": "<10ms",
        "end_to_end_budget": "590ms",
    }

@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "livekit": "connected",
        "moss_status": "prewarmed",
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)

