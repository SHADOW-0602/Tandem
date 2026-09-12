# Product Requirements Document (PRD)
## Sub-10ms Context Retrieval Voice Agents for Enterprise Field & Mission-Critical Operations

---

## 1. Executive Summary

Traditional Retrieval-Augmented Generation (RAG) architectures introduce 300ms to 800ms of latency over remote vector databases (network round-trips, ANN indexing, re-ranking), blowing conversational response budgets beyond 1.2 seconds. In spoken human communication, pauses longer than 700ms feel awkward, sluggish, or disconnected.

**Tandem** solves this by combining **Moss (`moss-agent`)**, **LiveKit Cloud**, **Groq LPU (Llama 3.1/3.3)**, **FastAPI**, and **Next.js**. By prewarming hot in-memory indexes directly within the agent worker process, **retrieval executes in sub-10ms (<8ms)**. Furthermore, Moss retrieval is executed concurrently with speech finalization and prompt staging, removing knowledge retrieval from the critical path entirely and achieving an end-to-end response turnaround of **~588ms**.

---

## 2. Target Personas & Enterprise Verticals

### Vertical 1: 911 & Emergency Tactical CAD Dispatch
- **Target User:** Police officers, EMS paramedics, municipal 911 dispatchers.
- **Corpus:** APCO Standard 10-Codes (10-4 to 10-99), Incident Command System (ICS-100/NIMS), Priority Dispatch Tiers (Code 1 to Code 3 Lights & Sirens), HAZMAT Emergency Response Guidebook (ERG Guide 124 Chlorine, Guide 128 Flammables).
- **Critical Guardrail:** Any mention of officer distress (Signal 13 / 10-99), weapons, or active violence instantly locks frequency, activates Code 3, and transfers to Watch Commander.

### Vertical 2: Healthcare & Clinical Emergency Triage
- **Target User:** Emergency room triage nurses, outpatient clinical staff, paramedics.
- **Corpus:** Emergency Severity Index (ESI Levels 1-5), Acute Coronary Syndrome (ACS) STEMI protocol, Cincinnati Prehospital Stroke Scale (FAST), Anaphylaxis Epinephrine dosing (0.3mg IM), HIPAA minimum necessary rules, HMO/PPO prior authorization.
- **Critical Guardrail:** Mandatory clinical disclaimer (*"I am an AI assistant and cannot provide medical diagnosis"*). Any reported crushing chest pain, facial droop, or airway compromise immediately triggers emergency 911 redirect.

### Vertical 3: Field Industrial Operations & Safety
- **Target User:** Industrial plant technicians, high-voltage electricians, heavy equipment mechanics.
- **Corpus:** OSHA 29 CFR 1910.147 Lockout/Tagout (LOTO) 6-step zero-energy verification, Caterpillar & Cummins SPN/FMI diesel engine fault codes, NFPA 70E Arc Flash Boundaries (PPE Category 1-4), Confined Space Entry atmospheric limits (LEL <10%, O2 19.5-23.5%).
- **Critical Guardrail:** Explosive gas concentrations (>10% LEL) or energized electrical work without an arc permit triggers immediate site evacuation and emergency equipment lockout.

### Vertical 4: Enterprise Customer Support & SaaS SLA
- **Target User:** Enterprise support agents, DevOps engineers, billing coordinators.
- **Corpus:** Enterprise SLA Matrix (P0 15-minute response, P1 1-hour response), Billing & refund thresholds (automated authority up to $500.00 USD), HTTP 429 API rate limiting (exponential backoff with jitter), SAML 2.0 / SCIM token resolution.
- **Critical Guardrail:** Automated supervisor transfer upon legal threat or refund requests exceeding $500.00 USD.

### Vertical 5: Freight Fleet Logistics & Aviation Dispatch
- **Target User:** Commercial long-haul truck drivers, freight coordinators, flight dispatchers.
- **Corpus:** FMCSA Hours of Service (11-hour driving, 14-hour on-duty window, 34-hour restart), FDA FSMA cold-chain excursion limits (perishables > 40°F), Part 121 aviation fuel reserves (1-2-3 alternate airport rule), CVSA out-of-service brake criteria.
- **Critical Guardrail:** Immediate emergency pullover instruction for critical air brake pressure loss or driver fatigue.

### Vertical 6: Financial Services & Banking Compliance
- **Target User:** Bank branch specialists, fraud analysts, anti-money laundering (AML) officers.
- **Corpus:** Bank Secrecy Act Currency Transaction Reports (CTR > $10,000 cash), Suspicious Activity Report (SAR) structuring detection (31 U.S.C. 5324), Regulation E consumer liability tiers (2-day vs 60-day notification), Emergency debit card lock procedures.
- **Critical Guardrail:** Strict prohibition against tipping off customers regarding internal SAR inquiries; immediate card freeze upon verified credentials compromise.

---

## 3. Latency Budget SLA & Technical Benchmark

| Pipeline Stage | Target Latency | Actual Measured | Architecture Mechanism |
|---|---|---|---|
| **1. Streaming STT** | ~250 ms | 240 ms | Deepgram Nova-3 / Groq Whisper streaming over WebRTC |
| **2. Moss Retrieval** | **&lt; 10 ms** | **0.0 - 7.8 ms** | Hot in-memory index prewarmed in process via `moss-agent` |
| **3. LLM TTFT** | ~180 ms | 175 ms | Groq LPU Llama 3.1 8B Instant (low temperature, streaming tokens) |
| **4. TTS TTFB** | ~150 ms | 145 ms | Cartesia Sonic streaming audio chunked on sentence boundaries |
| **Total Turnaround** | **~590 ms** | **~568 ms** | **Retrieval off critical path: concurrent execution** |

---

## 4. Key System Principles & Guardrails

1. **Zero-Network-Hop Context:** The Moss index is loaded once during worker `prewarm()`. In-call queries execute directly against memory, eliminating external database roundtrips.
2. **Instant Barge-In & Cancellation:** When the caller interrupts the agent, Silero VAD triggers speech detection, causing LiveKit's `AgentSession` to immediately cancel in-flight LLM/TTS generation (`asyncio.CancelledError`) and flush audio buffers, preventing overlap.
3. **Sub-Millisecond Guardrail Interceptor:** Safety rules evaluate transcripts prior to model assembly. Critical safety violations bypass generation completely and speak pre-authorized safety orders within 50ms.
4. **Full-Duplex WebRTC Transport:** Built on LiveKit Cloud SFU with adaptive jitter buffers and acoustic echo cancellation (AEC).

---

## 5. Deliverables & Monorepo Topology

- `/agent`: LiveKit Voice Agent worker, prewarmed Moss indexes, prompts, guardrails, and telemetry.
- `/server`: FastAPI control plane with token minting, vertical registry, live telemetry, and webhooks.
- `/web`: Next.js 14 WebRTC command center, live audio waveforms, latency waterfall, and knowledge inspector.
- `/docs`: High-resolution architecture diagrams and benchmarking documentation.
