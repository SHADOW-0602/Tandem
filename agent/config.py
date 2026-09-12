import os
from pathlib import Path
from dotenv import load_dotenv

# Find root .env file
ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT_DIR / ".env"

if ENV_FILE.exists():
    load_dotenv(ENV_FILE)

# LiveKit Configuration
LIVEKIT_URL = os.getenv("LIVEKIT_URL", "wss://parity-9hhf288x.livekit.cloud")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY", "")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET", "")

# Moss Configuration
MOSS_API_URL = os.getenv("MOSS_API_URL", "https://api.moss.sh")
MOSS_PROJECT_ID = os.getenv("MOSS_PROJECT_ID", "bbbe10ba-70bd-4ba2-ba91-df87740df27d")
MOSS_PROJECT_KEY = os.getenv("MOSS_PROJECT_KEY", os.getenv("MOSS_API_KEY", ""))

# Model & Provider Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
CARTESIA_API_KEY = os.getenv("CARTESIA_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "groq/compound-mini")
STT_PROVIDER = os.getenv("STT_PROVIDER", "groq")
TTS_PROVIDER = os.getenv("TTS_PROVIDER", "cartesia") # 'cartesia', 'kokoro', or 'openai'

# Structured Output Extraction — Google Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_EXTRACTION_MODEL = os.getenv("GEMINI_EXTRACTION_MODEL", "gemini-2.0-flash")

# Control Plane & Telemetry
CONTROL_PLANE_URL = os.getenv("CONTROL_PLANE_URL", "http://localhost:8000")
DATABASE_URL = os.getenv("DATABASE_URL", "")
REDIS_URL = os.getenv("REDIS_URL", "")

# Target Latency Thresholds (Milliseconds)
TARGET_STT_MS = 250.0
TARGET_MOSS_MS = 10.0
TARGET_LLM_TTFT_MS = 180.0
TARGET_TTS_TTFB_MS = 150.0
TARGET_TOTAL_MS = 590.0

# Supported Verticals & Mappings to Consolidated Moss Indexes
VERTICAL_INDEX_MAP = {
    "dispatch": "dispatch_emergency_ops",
    "logistics_fleet": "dispatch_emergency_ops",
    "healthcare": "clinical_healthcare_triage",
    "field_worker": "enterprise_field_and_support",
    "customer_support": "enterprise_field_and_support",
    "financial_compliance": "enterprise_field_and_support",
}

ALL_MOSS_INDEXES = list(set(VERTICAL_INDEX_MAP.values()))

# Local Embedded Qdrant & Dynamic Knowledge Configuration
QDRANT_STORAGE_PATH = os.getenv("QDRANT_STORAGE_PATH", str(ROOT_DIR / "data" / "qdrant_db"))
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-small-en-v1.5")
ENABLE_DYNAMIC_KNOWLEDGE = os.getenv("ENABLE_DYNAMIC_KNOWLEDGE", "true").lower() == "true"

# OpenTelemetry Distributed Tracing Configuration
ENABLE_OTEL_TRACING = os.getenv("ENABLE_OTEL_TRACING", "true").lower() == "true"
OTEL_SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "tandem-voice-agent")
OTEL_EXPORTER_OTLP_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "")


