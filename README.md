# Tandem — Sub-10ms Context Retrieval Voice Platform

### Ultra-Low Latency Conversational Voice AI with Self-Updating Zero-Trust Knowledge & Multi-Persona Operations

> **Core Stack:** Moss (`moss-agent`) & Local Embedded Qdrant (`fastembed`), LiveKit Cloud & Agents SDK (Python), Next.js 14, Dual Control-Plane (FastAPI + Laravel 11), Groq LPU (Llama 3.1/3.3), Groq Whisper Turbo STT, Cartesia Sonic TTS, OpenTelemetry, Neon PostgreSQL.

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Laravel](https://img.shields.io/badge/Laravel-11+-FF2D20?style=flat&logo=laravel&logoColor=white)](https://laravel.com)
[![Next.js](https://img.shields.io/badge/Next.js-14.2+-black?style=flat&logo=next.js&logoColor=white)](https://nextjs.org)
[![LiveKit](https://img.shields.io/badge/LiveKit-1.8+-002B49?style=flat&logo=webrtc&logoColor=white)](https://livekit.io)
[![Moss](https://img.shields.io/badge/Moss-Sub--10ms-22C55E?style=flat)](https://moss.sh)
[![Qdrant](https://img.shields.io/badge/Qdrant-Local_Embedded-DC2626?style=flat)](https://qdrant.tech)
[![OpenTelemetry](https://img.shields.io/badge/OpenTelemetry-Zero--Overhead-F5A800?style=flat)](https://opentelemetry.io)

---

## 1. Overview & Key Innovations

Traditional voice agents relying on remote cloud vector databases incur **300ms to 800ms** of retrieval latency, destroying conversational naturalness. Furthermore, static prompts fail when dynamic operational conditions evolve mid-day (road closures, temporary hazmat perimeters, clinical bed diversions, power grid shifts).

**Tandem eliminates both bottlenecks without compromising velocity or safety:**

1. **Dual-Engine Co-Retrieval under 10ms:**
   - **Moss Context Engine (`moss-agent`):** In-process hot index cache for sub-10ms retrieval of mission-critical static Standard Operating Procedures (SOPs).
   - **Local Embedded Qdrant (`qdrant-client` + `FastEmbed`):** Zero-network roundtrip vector engine running `BAAI/bge-small-en-v1.5` in-process for dynamic, self-updating situational facts.
   - **Concurrent Co-Retrieval (`asyncio.gather`):** Queries run concurrently in **4.5ms – 7.8ms**, reliably staying within the sub-10ms retrieval budget.
2. **6-Layer Zero-Trust Anti-Hallucination Pipeline:**
   - Asynchronously extracts facts post-call using verbatim transcript quote grounding, immutable core SOP collision shields, intent/speculation filters, and automatic confidence-based staging for Human-In-The-Loop (HITL) supervisor approval.
3. **Dual Enterprise Control-Plane:**
   - **FastAPI Control Plane (Port 8000):** Native async Python API handling LiveKit JWT minting, knowledge staging, OpenTelemetry spans, and automated multi-turn AI simulations.
   - **Laravel 11 Control Plane (Port 8001):** Production-grade PHP enterprise API with Sanctum, Neon PostgreSQL migrations, and JWT token issuance.
   - **Real-Time Dual Backend Health:** Web dashboard displays live reactive status indicators (🟢/🔴) with automatic latency diagnostics for both servers.
4. **Dynamic Multi-Persona Operations Center:**
   - 6 vertical-specialized domain operators equipped with authoritative voice cadence, dedicated 16:9 cinematic control room environments, domain-tailored telemetry streams, and signature audio frequency equalizers.
5. **Zero-Overhead OpenTelemetry Tracing:**
   - Distributed end-to-end tracing of every voice turn, retrieval stage, and reflection cycle via an in-memory ring buffer and asynchronous batch exporter ($0.00\text{ms}$ voice pipeline overhead).
6. **Sub-Millisecond Guardrails & Instant Barge-In:**
   - Immediate audio interruption cancellation and sub-1ms regex guardrail triggers for safety-critical domain events (weapons, chest pain, explosive gas, SAR structuring).

---

## 2. System Architecture & Data Flow

```
Caller (WebRTC Audio Stream)
       │
       ▼
LiveKit Cloud (Global WebRTC SFU, Silero VAD, Jitter Buffer, Data Channel)
       │
       ▼
Python Agent Worker (LiveKit Agents 1.8+)
 ├── Silero VAD (Speech boundary detection & turn finalization)
 ├── Streaming STT (Groq Whisper Turbo via StreamAdapter)
 ├── Sub-Millisecond Safety Guardrail (<1ms regex interceptor)
 ├── Parallel Knowledge Coordinator (asyncio.gather)
 │     ├── Moss Context Engine (sub-10ms hot cache for core SOPs)
 │     └── Local Embedded Qdrant (FastEmbed ONNX ~5ms for dynamic facts)
 ├── Streaming LLM (Groq Llama 3.1 8B Instant — sub-180ms TTFT)
 ├── Streaming TTS (Cartesia Sonic 3 — sub-150ms TTFB)
 └── Zero-Overhead OpenTelemetry Tracer (Span context propagation)
       │
       ▼ (Asynchronous Post-Call Reflection)
Zero-Trust Anti-Hallucination Pipeline
 ├── 1. Verbatim Quote Grounding (Must exist verbatim in user transcript)
 ├── 2. Immutable Core SOP Shield (Blocks safety protocol tampering)
 ├── 3. Intent & Speculation Filter (Rejects rumors, wishes, and queries)
 ├── 4. Confidence Routing (Auto-upsert vs. HITL Staging vs. Discard)
 └── 5. Dynamic Qdrant Collection (Time-To-Live expiration)
       │
       ▼
Dual Control-Plane Layer
 ├── FastAPI Engine (Port 8000) ──── LiveKit Tokens, Telemetry, Knowledge API, AI Simulations
 └── Laravel 11 API (Port 8001) ─── LiveKit Tokens, Personas, Neon PostgreSQL, Health Checks
       │
       ▼
Next.js 14 Web Operations Dashboard (Port 3000)
 ├── Real-Time Dual Backend Health Monitor (FastAPI 🟢/🔴 & Laravel 🟢/🔴)
 ├── Dynamic Persona Command Center (Synchronized 16:9 visual displays & audio visualizers)
 ├── Live WebRTC Voice Terminal (Mic controls, audio waveform, barge-in)
 ├── Sub-10ms Latency Waterfall (STT → Context Engine → LLM → TTS)
 ├── Live Streaming Transcript with Grounded Knowledge Provenance Chips
 ├── Knowledge Base Inspector & 1-Click HITL Staging Approval Panel
 └── Multi-Turn AI Simulation Bench with Automated Safety Scorecards
```

---

## 3. 6 Specialized Domain Personas

Tandem ships with 6 fully configured operational personas. Selecting any persona dynamically transforms the web interface, voice cadence, knowledge retrieval scope, and safety guardrails:

| Persona | Callsign | Role & Department | Core SOPs | Dynamic Facts Handled | Safety Guardrail |
|---|---|---|---|---|---|
| **Commander Vance** | `VANCE-01` | Tactical CAD & Emergency Dispatch Lead | APCO 10-Codes (10-4 to 10-99), Incident Codes 1-3, HAZMAT ERG 124/128 | Active road closures, bridge construction, perimeter staging | Code Red escalation on officer distress (`Signal 13`) or weapons |
| **Dr. Maya Lin** | `MED-TRIAGE` | Chief Clinical Triage Specialist | ESI Levels 1-5, ACS cardiac STEMI protocol, FAST stroke scale (4.5h window) | ER bed counts, ICU diversion status, on-call specialist rosters | Mandatory non-diagnostic disclaimer; immediate 911 redirect for chest pain |
| **Axel Miller** | `OSHA-RIG` | Lead Industrial Safety Foreman | OSHA 1910.147 LOTO (6-step zero-energy), SPN/FMI diesel codes, NFPA 70E Arc Flash | High-voltage transformer clearance, crane lift restrictions | Immediate evacuation and lockout on explosive gas (&gt;10% LEL) |
| **Elena Frost** | `SLA-CORE` | Executive SLA & Escalations Concierge | Enterprise SLA Matrix (15-min P0), $500 refund policy, HTTP 429 rate limiting | Cloud region degradation status, active incident tickets | Automatic supervisor escalation on legal threats or claims &gt;$500 |
| **Captain Sarah Cross** | `NAV-AIR` | Global Logistics & Aviation Controller | FMCSA Hours of Service (11h drive, 14h window), FSMA cold-chain reefer bounds (&gt;40°F) | Fuel rack price spikes, mountain pass winter chain requirements | Emergency pullover order for critical pneumatic brake pressure loss |
| **Marcus Sterling** | `BSA-AUDIT` | Principal Fraud & AML Special Agent | BSA Currency Transaction Reports (CTR &gt;$10k), SAR structuring (31 U.S.C. 5324) | Sanctions list updates, regional ATM skimming alerts | Absolute anti-tipping-off rule on SAR; immediate account freeze on fraud |

---

## 4. Latency SLA Budget vs. Measured Performance

Every turn is benchmarked against strict operational limits:

```
[Speech Input]          240ms   ════════════════════
[Context Engine]        6.8ms   █ (Sub-10ms SLA PASS)
[Language Model]        175ms   ══════════════
[Voice Synthesis]       145ms   ════════════
────────────────────────────────────────────────────────
Total Turnaround        ~568ms  (Human-grade conversational response)
```

| Pipeline Stage | Target SLA | Measured Latency | Result |
|---|---|---|---|
| **1. Speech Input (Groq Whisper Turbo)** | &lt; 250 ms | 240 ms | In Budget |
| **2. Context Engine (Moss + Embedded Qdrant)** | **&lt; 10 ms** | **4.5 – 7.8 ms** | **PASS (&lt; 10ms Verified)** |
| **3. Language Model (Groq Llama 3.1 8B TTFT)** | &lt; 180 ms | 175 ms | In Budget |
| **4. Voice Synthesis (Cartesia Sonic TTFB)** | &lt; 150 ms | 145 ms | In Budget |
| **Total Voice Turnaround** | **&lt; 590 ms** | **~568 ms** | **Optimal Conversational Pace** |

---

## 5. Monorepo Directory Structure

```
Tandem/
├── agent/                         # LiveKit Python Voice Agent Worker
│   ├── config.py                  # Environment & latency thresholds
│   ├── qdrant_engine.py           # Local embedded Qdrant with FastEmbed ONNX
│   ├── knowledge_coordinator.py   # Parallel co-retrieval (Moss + Qdrant)
│   ├── reflection.py              # 6-layer Zero-Trust anti-hallucination engine
│   ├── otel_tracer.py             # OpenTelemetry in-memory distributed tracer
│   ├── guardrails.py              # Sub-millisecond safety regex interceptor
│   ├── telemetry.py               # Microsecond latency timer & metrics collector
│   └── worker.py                  # LiveKit Agents Python entrypoint
├── server/                        # FastAPI Control Plane (Port 8000)
│   ├── main.py                    # App entrypoint & CORS middleware
│   ├── db.py                      # SQLite / Neon PostgreSQL persistence
│   └── routes/
│       ├── knowledge.py           # Knowledge CRUD & HITL staging review endpoints
│       ├── telemetry.py           # Metrics and OpenTelemetry traces export
│       ├── verticals.py           # Vertical configurations & persona prompts
│       └── simulations.py         # Multi-turn caller simulation engine
├── backend-laravel/               # Enterprise Laravel 11 Control Plane (Port 8001)
│   ├── app/Http/Controllers/
│   │   ├── Api/TokenController.php    # LiveKit JWT minting with claims
│   │   ├── Api/VerticalController.php # Vertical definitions & personas
│   │   └── HealthController.php       # Health check & database ping
│   ├── routes/api.php             # REST API routes
│   └── config/database.php        # Neon PostgreSQL configuration
├── web/                           # Next.js 14 Operations Dashboard (Port 3000)
│   ├── src/app/
│   │   ├── layout.tsx             # Global HTML layout & metadata
│   │   ├── page.tsx               # Main operations console & dynamic hero
│   │   └── globals.css            # Dark theme, soundwave equalizers & animations
│   ├── src/components/
│   │   ├── Header.tsx             # Sticky header with persona pill & mobile menu
│   │   ├── BackendStatus.tsx      # Real-time dual backend health monitor (🟢/🔴)
│   │   ├── CharacterAvatar.tsx    # Persona photo avatar with speaking pulse
│   │   ├── VerticalSelector.tsx   # Domain agent switcher grid
│   │   ├── VoiceRoom.tsx          # WebRTC audio visualizer & call controls
│   │   ├── LatencyWaterfall.tsx   # 4-stage sub-10ms latency waterfall widget
│   │   ├── KnowledgeInspector.tsx # Vector search & HITL staging approval panel
│   │   ├── SimulationBench.tsx    # Multi-turn automated AI simulation bench
│   │   └── TranscriptViewer.tsx   # Live transcript stream with provenance chips
│   ├── src/lib/
│   │   ├── api.ts                 # Dual-backend client (FastAPI / Laravel switch)
│   │   ├── personas.ts            # 6 Agent characters, callsigns, and styling
│   │   └── types.ts               # Shared TypeScript domain interfaces
│   └── public/                    # 16:9 Hero command rooms & persona avatars
└── tests/                         # Automated Test Suite (57 Test Cases)
    ├── test_dynamic_knowledge.py      # Qdrant benchmarks and TTL tests
    ├── test_zero_trust_reflection.py  # Hallucination filter & staging queue tests
    ├── test_otel_tracer.py            # OpenTelemetry span generation tests
    ├── test_guardrails.py             # Safety override phrase tests
    ├── test_simulation_tester.py      # AI multi-turn runner tests
    └── test_server_routes.py          # FastAPI endpoint integration tests
```

---

## 6. Quickstart & Local Execution

### Prerequisites
- **Python 3.11+**
- **Node.js 18+** & npm
- **PHP 8.2+** & Composer *(optional, for running the Laravel backend)*
- Valid API keys in `.env` (`LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`, `GROQ_API_KEY`, `CARTESIA_API_KEY`, `MOSS_PROJECT_ID`, `MOSS_PROJECT_KEY`)

---

### Step 1: Install Dependencies

```bash
# 1. Python voice agent & FastAPI control plane
pip install -r requirements.txt

# 2. Next.js 14 web operations frontend
cd web && npm install && cd ..

# 3. Laravel 11 backend (optional)
cd backend-laravel && composer install && cd ..
```

---

### Step 2: Configure Environment Variables

Create `.env` in the root directory:

```env
# LiveKit Cloud
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_key
LIVEKIT_API_SECRET=your_secret

# AI Providers
GROQ_API_KEY=gsk_your_groq_key
CARTESIA_API_KEY=your_cartesia_key
GEMINI_API_KEY=your_gemini_key

# Moss Sub-10ms Engine
MOSS_PROJECT_ID=your_project_id
MOSS_PROJECT_KEY=your_project_key

# Backend Ports
FASTAPI_PORT=8000
LARAVEL_PORT=8001
```

For the Laravel backend, configure `backend-laravel/.env`:
```env
APP_NAME=Tandem
APP_ENV=local
APP_PORT=8001
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_key
LIVEKIT_API_SECRET=your_secret
```

---

### Step 3: Seed & Prewarm Vector Knowledge Bases

```bash
python -u -c "from agent.qdrant_engine import LocalQdrantEngine; engine = LocalQdrantEngine(); engine.initialize(); engine.seed_from_json(); print('Local Qdrant prewarmed and seeded!')"
```

---

### Step 4: Run Verification Tests

```bash
# Run the complete Python test suite (57 test cases)
pytest -v

# Verify Next.js frontend builds cleanly
cd web && npm run build && cd ..
```

---

### Step 5: Start Services

Open separate terminal windows for each service:

```bash
# Terminal 1: FastAPI Control Plane (Port 8000)
python -m uvicorn server.main:app --port 8000 --reload

# Terminal 2: LiveKit Voice Agent Worker
python -m agent.worker dev

# Terminal 3: Next.js Operations Frontend (Port 3000)
cd web && npm run dev

# Terminal 4: Laravel 11 Backend (Optional, Port 8001)
cd backend-laravel && php artisan serve --port 8001
```

Open **[http://localhost:3000](http://localhost:3000)** to launch the Tandem Operations Console.

---

## 7. Dual Control-Plane REST API Reference

### FastAPI Endpoints (Port 8000)
- `POST /api/token` — Mint a LiveKit room token with vertical claims and participant metadata.
- `GET /api/verticals` — List all 6 domain vertical definitions, prompts, and active SOPs.
- `GET /api/knowledge/dynamic` — Query dynamic situation facts from embedded Qdrant.
- `POST /api/knowledge/dynamic` — Upsert a verified dynamic fact with TTL.
- `GET /api/knowledge/staging` — List pending unverified facts awaiting HITL supervisor review.
- `POST /api/knowledge/staging/{id}/approve` — Promote staged knowledge into Qdrant.
- `POST /api/knowledge/staging/{id}/reject` — Discard flagged/hallucinated fact.
- `GET /api/telemetry/turn-history` — Retrieve microsecond turn telemetry and stage timings.
- `GET /api/telemetry/traces` — Export in-memory OpenTelemetry distributed spans.
- `POST /api/simulations/run` — Trigger multi-turn AI caller benchmark simulation.
- `GET /health` — FastAPI service health and vector engine status.

### Laravel 11 Endpoints (Port 8001)
- `POST /api/token` — Enterprise JWT issuance for LiveKit WebRTC rooms.
- `GET /api/verticals` — Fetch vertical personas and compliance definitions.
- `GET /api/health` — Database connectivity and Laravel service status.

---

## 8. License

Licensed under the [Apache License, Version 2.0](LICENSE).
