"""API endpoints for AI Tester simulations, scenarios, and personalities."""
import uuid
import time
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from server.db import (
    register_scenario, get_scenario, list_scenarios, update_scenario, delete_scenario,
    register_personality, get_personality, list_personalities, update_personality, delete_personality,
    store_simulation_run, get_simulation_run, list_simulation_runs,
)
from agent.simulation_tester import simulation_engine, BUILTIN_SCENARIOS, BUILTIN_PERSONALITIES

# Auto-seed built-in presets if not already loaded
for sc_id, sc_data in BUILTIN_SCENARIOS.items():
    if not get_scenario(sc_id):
        register_scenario(sc_id, sc_data)
for p_id, p_data in BUILTIN_PERSONALITIES.items():
    if not get_personality(p_id):
        register_personality(p_id, p_data)

router = APIRouter(prefix="/api/simulations", tags=["simulations"])


# ---------------------------------------------------------------------------
# Pydantic Request Models
# ---------------------------------------------------------------------------
class ScenarioCreateRequest(BaseModel):
    name: str
    vertical: str
    instructions: str
    success_criteria: Optional[Dict[str, Any]] = None
    assistant_overrides: Optional[Dict[str, Any]] = None


class ScenarioUpdateRequest(BaseModel):
    name: Optional[str] = None
    instructions: Optional[str] = None
    success_criteria: Optional[Dict[str, Any]] = None
    assistant_overrides: Optional[Dict[str, Any]] = None


class PersonalityCreateRequest(BaseModel):
    name: str
    assistant: Dict[str, Any]


class PersonalityUpdateRequest(BaseModel):
    name: Optional[str] = None
    assistant: Optional[Dict[str, Any]] = None


class RunSimulationRequest(BaseModel):
    scenario_id: Optional[str] = None
    personality_id: Optional[str] = None
    # Support inline custom scenarios or personalities
    custom_scenario: Optional[Dict[str, Any]] = None
    custom_personality: Optional[Dict[str, Any]] = None
    max_turns: Optional[int] = None


# ---------------------------------------------------------------------------
# Scenario Endpoints
# ---------------------------------------------------------------------------
@router.get("/scenarios")
async def get_all_scenarios(vertical: Optional[str] = None):
    """List all simulation scenarios (built-in and custom)."""
    return {"scenarios": list_scenarios(vertical)}


@router.post("/scenarios", status_code=201)
async def create_new_scenario(req: ScenarioCreateRequest):
    """Create a new custom simulation scenario."""
    scenario_id = f"custom_scenario_{uuid.uuid4().hex[:8]}"
    data = {
        "id": scenario_id,
        "name": req.name,
        "vertical": req.vertical,
        "instructions": req.instructions,
        "success_criteria": req.success_criteria or {},
        "assistant_overrides": req.assistant_overrides or {},
        "is_builtin": False,
        "created_at": time.time(),
    }
    register_scenario(scenario_id, data)
    return data


@router.get("/scenarios/{scenario_id}")
async def get_single_scenario(scenario_id: str):
    """Retrieve a scenario by ID."""
    scenario = get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found")
    return scenario


@router.patch("/scenarios/{scenario_id}")
async def update_existing_scenario(scenario_id: str, req: ScenarioUpdateRequest):
    """Update a custom scenario (built-in scenarios cannot be modified)."""
    scenario = get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found")
    if scenario.get("is_builtin"):
        raise HTTPException(status_code=400, detail="Built-in scenarios cannot be modified with PATCH. Clone it into a custom scenario instead.")

    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    updated = update_scenario(scenario_id, updates)
    return updated


@router.delete("/scenarios/{scenario_id}", status_code=204)
async def remove_existing_scenario(scenario_id: str):
    """Delete a custom scenario (built-in scenarios are protected)."""
    scenario = get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found")
    if scenario.get("is_builtin"):
        raise HTTPException(status_code=400, detail="Built-in scenarios cannot be deleted")
    delete_scenario(scenario_id)


# ---------------------------------------------------------------------------
# Personality Endpoints
# ---------------------------------------------------------------------------
@router.get("/personalities")
async def get_all_personalities():
    """List all AI tester personalities (built-in and custom)."""
    return {"personalities": list_personalities()}


@router.post("/personalities", status_code=201)
async def create_new_personality(req: PersonalityCreateRequest):
    """Create a new custom AI tester personality."""
    personality_id = f"custom_personality_{uuid.uuid4().hex[:8]}"
    data = {
        "id": personality_id,
        "name": req.name,
        "assistant": req.assistant,
        "is_builtin": False,
        "created_at": time.time(),
    }
    register_personality(personality_id, data)
    return data


@router.get("/personalities/{personality_id}")
async def get_single_personality(personality_id: str):
    """Retrieve an AI tester personality by ID."""
    personality = get_personality(personality_id)
    if not personality:
        raise HTTPException(status_code=404, detail=f"Personality '{personality_id}' not found")
    return personality


@router.patch("/personalities/{personality_id}")
async def update_existing_personality(personality_id: str, req: PersonalityUpdateRequest):
    """Update a custom personality (built-in personalities cannot be modified)."""
    personality = get_personality(personality_id)
    if not personality:
        raise HTTPException(status_code=404, detail=f"Personality '{personality_id}' not found")
    if personality.get("is_builtin"):
        raise HTTPException(status_code=400, detail="Built-in personalities cannot be modified with PATCH. Clone it into a custom personality instead.")

    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    updated = update_personality(personality_id, updates)
    return updated


@router.delete("/personalities/{personality_id}", status_code=204)
async def remove_existing_personality(personality_id: str):
    """Delete a custom personality (built-in personalities are protected)."""
    personality = get_personality(personality_id)
    if not personality:
        raise HTTPException(status_code=404, detail=f"Personality '{personality_id}' not found")
    if personality.get("is_builtin"):
        raise HTTPException(status_code=400, detail="Built-in personalities cannot be deleted")
    delete_personality(personality_id)


# ---------------------------------------------------------------------------
# Simulation Execution Endpoints
# ---------------------------------------------------------------------------
@router.post("/run")
async def execute_simulation(req: RunSimulationRequest):
    """Executes a multi-turn simulation between an AI Tester and a Tandem Voice Agent."""
    # Resolve Scenario
    scenario = None
    if req.scenario_id:
        scenario = get_scenario(req.scenario_id)
    elif req.custom_scenario:
        scenario = req.custom_scenario

    if not scenario:
        # Default to dispatch chlorine leak if none provided
        scenario = get_scenario("dispatch_hazmat_leak")
        if not scenario:
            raise HTTPException(status_code=400, detail="Scenario not specified or found")

    # Resolve Personality
    personality = None
    if req.personality_id:
        personality = get_personality(req.personality_id)
    elif req.custom_personality:
        personality = req.custom_personality

    if not personality:
        # Default to impatient concise caller
        personality = get_personality("impatient_concise")
        if not personality:
            raise HTTPException(status_code=400, detail="Personality not specified or found")

    # Run Multi-Turn Simulation
    result = await simulation_engine.run_simulation(
        scenario=scenario,
        personality=personality,
        max_turns_override=req.max_turns,
    )

    run_dict = result.to_dict()
    store_simulation_run(result.run_id, run_dict)

    return run_dict


@router.get("/runs")
async def get_recent_simulation_runs(limit: int = 20):
    """List recent simulation run results."""
    return {"runs": list_simulation_runs(limit)}


@router.get("/runs/{run_id}")
async def get_single_simulation_run(run_id: str):
    """Retrieve full details and transcript of a simulation run."""
    run = get_simulation_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Simulation run '{run_id}' not found")
    return run
