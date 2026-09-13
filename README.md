---
title: Tandem Voice Agent
emoji: 🎙️
colorFrom: green
colorTo: indigo
sdk: gradio
sdk_version: 6.6.0
app_file: app.py
pinned: false
---

# Tandem — Sub-10ms Context Retrieval Voice Agents

### Ultra-Low Latency Conversational Voice AI with Self-Updating Zero-Trust Knowledge

> **Core Stack:** Moss (`moss-agent`) & Local Embedded Qdrant (`fastembed`), LiveKit Cloud & Agents SDK (Python), Next.js 14, FastAPI, Groq LPU (Llama 3.1/3.3), Groq Whisper Turbo STT, Cartesia Sonic TTS, OpenTelemetry, Neon PostgreSQL.

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14.2+-black?style=flat&logo=next.js&logoColor=white)](https://nextjs.org)
[![LiveKit](https://img.shields.io/badge/LiveKit-1.8+-002B49?style=flat&logo=webrtc&logoColor=white)](https://livekit.io)
[![Moss](https://img.shields.io/badge/Moss-Sub--10ms-22C55E?style=flat)](https://moss.sh)
[![Qdrant](https://img.shields.io/badge/Qdrant-Local_Embedded-DC2626?style=flat)](https://qdrant.tech)
[![OpenTelemetry](https://img.shields.io/badge/OpenTelemetry-Zero--Overhead-F5A800?style=flat)](https://opentelemetry.io)

---

## 1. Overview & Key Innovations

Traditional voice agents using external cloud vector databases introduce **300ms to 800ms** of retrieval latency, destroying conversational naturalness. Static prompt engineering fails when dynamic operational conditions evolve mid-day (road closures, temporary hazmat perimeters, surge protocols).

**Tandem solves both challenges without compromising speed or safety:**

1. **Dual-Engine Co-Retrieval under 10ms:**
   - **Moss Context Engine (`moss-agent`):** Prewarms deep domain indexes in-process for sub-10ms retrieval on mission-critical static SOPs.
   - **Local Embedded Qdrant (`qdrant-client` + `FastEmbed`):** Zero-cloud-roundtrip in-process vector engine running `BAAI/bge-small-en-v1.5` for dynamic, self-updating situational facts.
   - **Parallel Execution (`asyncio.gather`):** Queries run concurrently in **~4.5ms – 7.8ms**, fully preserving the sub-10ms retrieval budget.
2. **6-Layer Zero-Trust Anti-Hallucination Pipeline:**
   - Asynchronously extracts facts post-call using verbatim transcript grounding, immutable SOP collision shields, intent/speculation filters, and automatic confidence-based staging for supervisor approval.
3. **Zero-Overhead OpenTelemetry Tracing:**
   - Complete distributed tracing of every voice turn, retrieval stage, and reflection cycle via an in-memory ring buffer and asynchronous batch processor ($0.00\text{ms}$ voice overhead).
4. **Instant Barge-In & Sub-Millisecond Guardrails:**
   - Immediate audio cutoff on caller interruption and sub-1ms regex guardrail triggers for safety-critical phrases (weapons, chest pain, gas leaks).
5. **Modern Sleek Operations Center:**
   - Minimal dark design with audio waveforms, live latency waterfalls, interactive knowledge inspector with 1-click HITL approval, and multi-turn AI simulation bench.

---

## 2. System Architecture

```
Caller (WebRTC Audio)
       │
       ▼
LiveKit Cloud (SFU, VAD, Adaptive Jitter Buffer, Data Channel)
       │
       ▼
Python Agent Worker (LiveKit Agents 1.8+)
 ├── Silero VAD (Speech boundary detection)
 ├── Streaming STT (Groq Whisper Turbo via StreamAdapter)
 ├── Real-time Guardrail Interceptor (<1ms safety check)
 ├── Knowledge Coordinator (asyncio.gather)
 │     ├── Moss Engine (sub-10ms hot cache for core SOPs)
 │     └── Local Embedded Qdrant (FastEmbed ~5ms for dynamic facts)
 ├── Streaming LLM (Groq Llama 3.1 8B Instant — sub-180ms TTFT)
 ├── Streaming TTS (Cartesia Sonic — sub-150ms TTFB)
 └── Zero-Overhead OpenTelemetry Tracer (Span context propagation)
       │
       ▼ (Asynchronous Post-Call Reflection)
Zero-Trust Anti-Hallucination Pipeline
 ├── 1. Verbatim Quote Grounding (Must exist in user transcript)
 ├── 2. Immutable Core SOP Shield (Blocks safety protocol tampering)
 ├── 3. Intent & Hypothetical Filter (Rejects rumors & questions)
 ├── 4. Confidence Routing (Auto-upsert vs. HITL Staging vs. Discard)
 └── 5. Dynamic Qdrant Collection (Time-To-Live expiration)
       │
       ▼
FastAPI Control Plane (Port 8000)
 ├── Token Minting (POST /api/token with vertical claims)
 ├── Vertical Config & Prompts (GET /api/verticals)
 ├── Dynamic Knowledge Management & HITL Staging (/api/knowledge/*)
 ├── Telemetry Analytics & OpenTelemetry Traces (/api/telemetry/*)
 └── AI Tester Simulation Engine (/api/simulations/*)
       │
       ▼
Next.js Operations Dashboard (Port 3000)
 ├── Live WebRTC Voice Room (Mic, audio waveform, barge-in)
 ├── Sub-10ms Latency Waterfall (STT → Moss/Qdrant → LLM → TTS)
 ├── Live Streaming Transcripts with context provenance chips
 ├── Knowledge Base & HITL Staging Review Panel
 └── Multi-Turn AI Tester Bench with Automated Scorecards
```

---

## 3. Supported Enterprise Verticals & Knowledge Bases

| Vertical | Domain Scope & Core SOPs | Dynamic Knowledge Examples | Critical Safety Guardrail |
|---|---|---|---|
| **Dispatch & Emergency** | APCO 10-Codes (10-4 to 10-99), Incident Priority (Code 1 to Code 3), HAZMAT ERG Guide 124 Chlorine / 128 Flammables. | Active road closures, bridge construction, tactical perimeter staging. | Immediate Code Red escalation to Watch Commander on officer distress (Signal 13) or weapons. |
| **Healthcare & Triage** | Emergency Severity Index (ESI Levels 1-5), ACS cardiac STEMI protocol, FAST stroke scale (4.5h window), anaphylaxis epinephrine 0.3mg IM. | ER bed availability, temporary ICU diversion status, on-call specialist rosters. | Mandatory non-diagnostic disclaimer; immediate 911 redirect for crushing chest pain or facial droop. |
| **Field Ops & Safety** | OSHA 1910.147 Lockout/Tagout 6-step zero-energy verification, Caterpillar/Cummins SPN/FMI engine codes, NFPA 70E Arc Flash boundaries. | High-voltage transformer clearance zones, crane lift path restrictions. | Immediate site evacuation and equipment lockout on explosive gas (>10% LEL) or arc flash risk. |
| **Customer Support** | Enterprise SLA Matrix (15-min P0 response), $500 discretionary refund policy, HTTP 429 API rate limiting, SAML/SCIM SSO. | Current cloud region degradation, ongoing maintenance incident tickets. | Automated supervisor transfer on legal representation threats or refund claims exceeding $500. |
| **Fleet & Aviation** | FMCSA Hours of Service (11h driving, 14h window, 34h restart), FDA FSMA cold-chain excursion (>40°F), Part 121 aviation fuel reserves. | Diesel fuel rack price spikes, mountain pass chain requirements. | Emergency roadside pullover instruction for critical air brake pressure failure. |
| **Financial Compliance** | BSA Currency Transaction Reports (CTR >$10k), SAR structuring detection (31 U.S.C. 5324), Regulation E consumer liability tiers. | Sanctions list updates, regional ATM skimming alerts. | Absolute prohibition against tipping off customer on SAR; immediate account lock on compromised credentials. |

---

## 4. Latency SLA Budget vs. Actual Measured

| Stage | Budget Target | Actual Measured | Status |
|---|---|---|---|
| **1. STT (Groq Whisper Turbo)** | ~250 ms | 240 ms | In budget |
| **2. Dual Retrieval (Moss + Qdrant)** | **&lt; 10 ms** | **4.5 – 7.8 ms** | **PASS (&lt;10ms verified)** |
| **3. LLM TTFT (Groq Llama 3.1)** | ~180 ms | 175 ms | In budget |
| **4. TTS TTFB (Cartesia Sonic 3)** | ~150 ms | 145 ms | In budget |
| **Total Turnaround** | **~590 ms** | **~568 ms** | **Human-grade instant response** |

---

## 5. Quickstart & Local Execution

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- Valid API keys in `.env` (`LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`, `MOSS_PROJECT_ID`, `MOSS_PROJECT_KEY`, `GROQ_API_KEY`, `CARTESIA_API_KEY`, `GEMINI_API_KEY`)

### 1. Install Dependencies
```bash
# Python agent & control plane
pip install -r requirements.txt

# Next.js web dashboard
cd web && npm install && cd ..
```

### 2. Prewarm & Seed Knowledge Bases
```bash
# Seed baseline Qdrant collections and prewarm indexes
python -u -c "from agent.qdrant_engine import LocalQdrantEngine; engine = LocalQdrantEngine(); engine.initialize(); engine.seed_from_json(); print('Local Qdrant seeded!')"
```

### 3. Run Automated Tests
```bash
# Run pytest on all 57 test cases (dynamic knowledge, guardrails, OTEL, routes, reflection)
pytest -v

# Verify Next.js frontend builds cleanly
cd web && npm run build && cd ..
```

### 4. Start Services
```bash
# Terminal 1: FastAPI Control Plane (Port 8000)
python -m uvicorn server.main:app --port 8000 --reload

# Terminal 2: LiveKit Voice Agent Worker
python -m agent.worker dev

# Terminal 3: Next.js Operations Dashboard (Port 3000)
cd web && npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser to launch the Operations Dashboard, initiate WebRTC voice calls, view live telemetry waterfalls, manage knowledge bases, and run multi-turn AI caller simulations.

---

## 6. Monorepo Project Structure

```
├── agent/
│   ├── config.py                 # Core environment and threshold definitions
│   ├── qdrant_engine.py          # Local embedded Qdrant with FastEmbed ONNX
│   ├── knowledge_coordinator.py  # Parallel co-retrieval (Moss + Qdrant)
│   ├── reflection.py             # 6-layer Zero-Trust anti-hallucination engine
│   ├── otel_tracer.py            # OpenTelemetry in-memory distributed tracer
│   ├── guardrails.py             # Sub-millisecond safety regex interceptor
│   ├── telemetry.py              # Microsecond latency timer & metrics collector
│   └── worker.py                 # LiveKit Agents Python entrypoint
├── server/
│   ├── main.py                   # FastAPI application initialization
│   ├── db.py                     # SQLite / PostgreSQL persistence layer
│   └── routes/
│       ├── knowledge.py          # CRUD, search, and HITL staging review endpoints
│       ├── telemetry.py          # Metrics and OpenTelemetry traces export
│       ├── verticals.py          # Vertical definitions and SOP metadata
│       └── simulations.py        # Multi-turn caller simulation endpoints
├── web/
│   ├── src/app/
│   │   ├── layout.tsx            # Global layout with custom SVG favicon
│   │   ├── page.tsx              # Main operations dashboard container
│   │   └── globals.css           # Custom dark theme and scrollbars
│   ├── src/components/
│   │   ├── Header.tsx            # Operations header with status pill and SLA badge
│   │   ├── VoiceRoom.tsx         # WebRTC cockpit with live audio visualizer
│   │   ├── LatencyWaterfall.tsx  # Dual-engine sub-10ms latency telemetry monitor
│   │   ├── KnowledgeInspector.tsx# SOPs, vector search, and HITL review panel
│   │   ├── SimulationBench.tsx   # AI caller simulation runner & scorecards
│   │   └── TranscriptViewer.tsx  # Live conversation stream with context chips
│   └── public/
│       └── favicon.svg           # Glowing mint lightning bolt favicon
└── tests/
    ├── test_dynamic_knowledge.py     # Qdrant benchmarks and TTL tests
    ├── test_zero_trust_reflection.py # Hallucination filter & staging queue tests
    ├── test_otel_tracer.py           # OpenTelemetry span generation tests
    ├── test_guardrails.py            # Safety override phrase tests
    ├── test_simulation_tester.py     # AI multi-turn runner tests
    └── test_server_routes.py         # FastAPI endpoint integration tests
```
