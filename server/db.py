import logging
import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

logger = logging.getLogger("server.db")

# In-memory fast cache and persistence fallback
CALLS_STORE: Dict[str, Dict[str, Any]] = {}
TELEMETRY_LOGS: List[Dict[str, Any]] = []
GUARDRAIL_EVENTS: List[Dict[str, Any]] = []

# Structured Output registry and results
# schema_id → full schema definition dict
STRUCTURED_OUTPUT_SCHEMAS: Dict[str, Dict[str, Any]] = {}
# call_id → list of ExtractionResult dicts
STRUCTURED_OUTPUT_RESULTS: Dict[str, List[Dict[str, Any]]] = {}

# Simulation AI Tester Scenarios & Personalities
SCENARIOS_STORE: Dict[str, Dict[str, Any]] = {}
PERSONALITIES_STORE: Dict[str, Dict[str, Any]] = {}
SIMULATION_RUNS_STORE: Dict[str, Dict[str, Any]] = {}

def record_session_start(room_name: str, vertical: str, metadata: Optional[Dict[str, Any]] = None):
    CALLS_STORE[room_name] = {
        "room_name": room_name,
        "vertical": vertical,
        "start_time": time.time(),
        "end_time": None,
        "turns": 0,
        "status": "active",
        "metadata": metadata or {},
    }

def record_session_end(room_name: str):
    if room_name in CALLS_STORE:
        CALLS_STORE[room_name]["end_time"] = time.time()
        CALLS_STORE[room_name]["status"] = "finished"

def store_turn_telemetry(payload: Dict[str, Any]):
    TELEMETRY_LOGS.append(payload)
    room = payload.get("call_id")
    if room and room in CALLS_STORE:
        CALLS_STORE[room]["turns"] += 1
    
    guardrail = payload.get("guardrail_action")
    if guardrail:
        GUARDRAIL_EVENTS.append({
            "call_id": room,
            "vertical": payload.get("vertical"),
            "action": guardrail,
            "user_transcript": payload.get("user_transcript"),
            "timestamp": payload.get("timestamp", time.time()),
        })

def get_recent_calls(limit: int = 50) -> List[Dict[str, Any]]:
    items = list(CALLS_STORE.values())
    items.sort(key=lambda x: x.get("start_time", 0), reverse=True)
    return items[:limit]

def get_telemetry_stats() -> Dict[str, Any]:
    if not TELEMETRY_LOGS:
        return {
            "total_turns": 0,
            "avg_moss_latency_ms": 0.0,
            "avg_total_latency_ms": 0.0,
            "p50_total_latency_ms": 0.0,
            "p95_total_latency_ms": 0.0,
            "sub_10ms_ratio": 1.0,
            "recent_turns": [],
            "guardrail_events": GUARDRAIL_EVENTS[-10:],
        }

    moss_times = [t.get("moss_latency_ms", 0.0) for t in TELEMETRY_LOGS]
    total_times = [t.get("total_latency_ms", 0.0) for t in TELEMETRY_LOGS]
    sub10_count = sum(1 for m in moss_times if m < 10.0)

    sorted_total = sorted(total_times)
    p50 = sorted_total[len(sorted_total) // 2]
    p95 = sorted_total[int(len(sorted_total) * 0.95)]

    return {
        "total_turns": len(TELEMETRY_LOGS),
        "avg_moss_latency_ms": round(sum(moss_times) / len(moss_times), 2),
        "avg_total_latency_ms": round(sum(total_times) / len(total_times), 2),
        "p50_total_latency_ms": round(p50, 2),
        "p95_total_latency_ms": round(p95, 2),
        "sub_10ms_ratio": round(sub10_count / len(moss_times), 3),
        "recent_turns": TELEMETRY_LOGS[-15:],
        "guardrail_events": GUARDRAIL_EVENTS[-15:],
    }

# ---------------------------------------------------------------------------
# Structured Output Schema Registry
# ---------------------------------------------------------------------------

def register_schema(schema_id: str, definition: Dict[str, Any]) -> None:
    """Upserts a structured output schema definition."""
    STRUCTURED_OUTPUT_SCHEMAS[schema_id] = {**definition, "schema_id": schema_id}

def get_schema(schema_id: str) -> Optional[Dict[str, Any]]:
    return STRUCTURED_OUTPUT_SCHEMAS.get(schema_id)

def list_schemas(vertical: Optional[str] = None) -> List[Dict[str, Any]]:
    schemas = list(STRUCTURED_OUTPUT_SCHEMAS.values())
    if vertical:
        schemas = [s for s in schemas if s.get("vertical") == vertical]
    return schemas

def delete_schema(schema_id: str) -> bool:
    if schema_id in STRUCTURED_OUTPUT_SCHEMAS:
        del STRUCTURED_OUTPUT_SCHEMAS[schema_id]
        return True
    return False

def get_custom_schemas_for_vertical(vertical: str) -> List[Dict[str, Any]]:
    """Returns only user-registered (non-default) schemas for a vertical."""
    return [
        s for s in STRUCTURED_OUTPUT_SCHEMAS.values()
        if s.get("vertical") == vertical and not s.get("schema_id", "").startswith("default_")
    ]

# ---------------------------------------------------------------------------
# Structured Output Extraction Results
# ---------------------------------------------------------------------------

def store_extraction_results(call_id: str, results: List[Dict[str, Any]]) -> None:
    """Appends extraction results for a call. Merges if called multiple times."""
    if call_id not in STRUCTURED_OUTPUT_RESULTS:
        STRUCTURED_OUTPUT_RESULTS[call_id] = []
    STRUCTURED_OUTPUT_RESULTS[call_id].extend(results)
    # Also tag the call record
    if call_id in CALLS_STORE:
        CALLS_STORE[call_id]["structured_outputs_extracted"] = True

def get_extraction_results(call_id: str) -> List[Dict[str, Any]]:
    return STRUCTURED_OUTPUT_RESULTS.get(call_id, [])


# ---------------------------------------------------------------------------
# Simulation AI Tester Scenarios & Personalities Registry
# ---------------------------------------------------------------------------

def register_scenario(scenario_id: str, data: Dict[str, Any]) -> None:
    """Registers or updates a simulation scenario."""
    SCENARIOS_STORE[scenario_id] = {**data, "id": scenario_id}

def get_scenario(scenario_id: str) -> Optional[Dict[str, Any]]:
    return SCENARIOS_STORE.get(scenario_id)

def list_scenarios(vertical: Optional[str] = None) -> List[Dict[str, Any]]:
    items = list(SCENARIOS_STORE.values())
    if vertical:
        items = [s for s in items if s.get("vertical") == vertical]
    return items

def update_scenario(scenario_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if scenario_id not in SCENARIOS_STORE:
        return None
    SCENARIOS_STORE[scenario_id].update(updates)
    return SCENARIOS_STORE[scenario_id]

def delete_scenario(scenario_id: str) -> bool:
    if scenario_id in SCENARIOS_STORE:
        # Built-in protection
        if SCENARIOS_STORE[scenario_id].get("is_builtin"):
            return False
        del SCENARIOS_STORE[scenario_id]
        return True
    return False

def register_personality(personality_id: str, data: Dict[str, Any]) -> None:
    """Registers or updates a simulation personality."""
    PERSONALITIES_STORE[personality_id] = {**data, "id": personality_id}

def get_personality(personality_id: str) -> Optional[Dict[str, Any]]:
    return PERSONALITIES_STORE.get(personality_id)

def list_personalities() -> List[Dict[str, Any]]:
    return list(PERSONALITIES_STORE.values())

def update_personality(personality_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if personality_id not in PERSONALITIES_STORE:
        return None
    PERSONALITIES_STORE[personality_id].update(updates)
    return PERSONALITIES_STORE[personality_id]

def delete_personality(personality_id: str) -> bool:
    if personality_id in PERSONALITIES_STORE:
        if PERSONALITIES_STORE[personality_id].get("is_builtin"):
            return False
        del PERSONALITIES_STORE[personality_id]
        return True
    return False

def store_simulation_run(run_id: str, run_data: Dict[str, Any]) -> None:
    SIMULATION_RUNS_STORE[run_id] = run_data

def get_simulation_run(run_id: str) -> Optional[Dict[str, Any]]:
    return SIMULATION_RUNS_STORE.get(run_id)

def list_simulation_runs(limit: int = 50) -> List[Dict[str, Any]]:
    runs = list(SIMULATION_RUNS_STORE.values())
    runs.sort(key=lambda x: x.get("started_at", 0), reverse=True)
    return runs[:limit]
