import os
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT_DIR / ".env"

if ENV_FILE.exists():
    load_dotenv(ENV_FILE)

PORT = int(os.getenv("PORT", "8000"))
HOST = os.getenv("HOST", "0.0.0.0")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

LIVEKIT_URL = os.getenv("LIVEKIT_URL", "wss://parity-9hhf288x.livekit.cloud")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY", "")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET", "")

DATABASE_URL = os.getenv("DATABASE_URL", "")
REDIS_URL = os.getenv("REDIS_URL", "")

CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://app.parity.ai",
]
