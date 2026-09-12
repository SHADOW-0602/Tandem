"""Tests for the AI Tester & Simulation Suite."""
import asyncio
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from agent.simulation_tester import (
    BUILTIN_SCENARIOS,
    BUILTIN_PERSONALITIES,
    AITesterEngine,
    SimulationTurnRecord,
)
from server.db import (
    register_scenario,
    get_scenario,
    list_scenarios,
    update_scenario,
    delete_scenario,
    register_personality,
    get_personality,
    list_personalities,
    update_personality,
    delete_personality,
    store_simulation_run,
    get_simulation_run,
    list_simulation_runs,
)
from server.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Test 1: Built-in Scenarios and Personalities Integrity
# ---------------------------------------------------------------------------
class TestBuiltinIntegrity:
    def test_builtin_scenarios_exist(self):
        assert len(BUILTIN_SCENARIOS) >= 6
        for sc_id, sc in BUILTIN_SCENARIOS.items():
            assert "name" in sc
            assert "vertical" in sc
            assert "instructions" in sc
            assert sc.get("is_builtin") is True

    def test_builtin_personalities_exist(self):
        assert "impatient_concise" in BUILTIN_PERSONALITIES
        assert "calm_cooperative" in BUILTIN_PERSONALITIES
        assert "stressed_urgent" in BUILTIN_PERSONALITIES
        assert "adversarial_tester" in BUILTIN_PERSONALITIES
        for p_id, p in BUILTIN_PERSONALITIES.items():
            assert "assistant" in p
            assert p.get("is_builtin") is True
            asst = p["assistant"]
            assert "model" in asst
            assert "firstMessageMode" in asst


# ---------------------------------------------------------------------------
# Test 2: Database Store & Customization CRUD
# ---------------------------------------------------------------------------
class TestSimulationDbCrud:
    def test_scenario_crud_and_builtin_protection(self):
        # Built-in scenario deletion should be rejected
        assert delete_scenario("dispatch_hazmat_leak") is False

        # Create custom scenario
        custom_id = "custom_test_scenario_1"
        register_scenario(custom_id, {
            "name": "Custom Test Scenario",
            "vertical": "dispatch",
            "instructions": "Test instructions",
            "is_builtin": False
        })

        fetched = get_scenario(custom_id)
        assert fetched is not None
        assert fetched["name"] == "Custom Test Scenario"

        # Update custom scenario
        updated = update_scenario(custom_id, {"name": "Updated Custom Scenario"})
        assert updated["name"] == "Updated Custom Scenario"

        # Delete custom scenario
        assert delete_scenario(custom_id) is True
        assert get_scenario(custom_id) is None

    def test_personality_crud_and_builtin_protection(self):
        # Built-in personality deletion should be rejected
        assert delete_personality("impatient_concise") is False

        # Create custom personality
        custom_p_id = "custom_impatient_copy"
        register_personality(custom_p_id, {
            "name": "Custom Impatient Copy",
            "assistant": {"model": {"model": "gemini-2.0-flash"}},
            "is_builtin": False
        })

        fetched = get_personality(custom_p_id)
        assert fetched is not None
        assert fetched["name"] == "Custom Impatient Copy"

        # Update
        updated = update_personality(custom_p_id, {"name": "Renamed Personality"})
        assert updated["name"] == "Renamed Personality"

        # Delete
        assert delete_personality(custom_p_id) is True
        assert get_personality(custom_p_id) is None


# ---------------------------------------------------------------------------
# Test 3: Success Criteria Evaluation Logic
# ---------------------------------------------------------------------------
class TestSuccessCriteriaEvaluation:
    def test_evaluate_guardrail_pass(self):
        engine = AITesterEngine()
        scenario = {
            "success_criteria": {
                "expected_guardrail": "TRIGGER_HAZMAT_PERIMETER",
                "required_keywords": ["evacuate"],
            }
        }
        turn_records = [
            SimulationTurnRecord(
                turn_id=1,
                tester_utterance="Chlorine leak at rail yard",
                agent_response="Evacuate 1.5 miles downwind immediately.",
                guardrail_action="TRIGGER_HAZMAT_PERIMETER",
                total_latency_ms=280.0
            )
        ]
        result = engine._evaluate_success_criteria(
            scenario=scenario,
            turn_records=turn_records,
            total_duration=5.0
        )
        assert result["passed"] is True
        assert result["score"] == 100.0

    def test_evaluate_guardrail_fail(self):
        engine = AITesterEngine()
        scenario = {
            "success_criteria": {
                "expected_guardrail": "TRIGGER_HAZMAT_PERIMETER",
            }
        }
        turn_records = [
            SimulationTurnRecord(
                turn_id=1,
                tester_utterance="Hello dispatch",
                agent_response="Hello, how can I help?",
                guardrail_action=None,
                total_latency_ms=300.0
            )
        ]
        result = engine._evaluate_success_criteria(
            scenario=scenario,
            turn_records=turn_records,
            total_duration=3.0
        )
        assert result["passed"] is False
        assert result["score"] == 0.0


# ---------------------------------------------------------------------------
# Test 4: Multi-Turn Simulation Runner (Mocked LLM)
# ---------------------------------------------------------------------------
class TestMultiTurnSimulationRunner:
    def test_run_simulation_with_mocked_dialogue(self):
        engine = AITesterEngine()

        scenario = {
            "id": "test_sc",
            "name": "Test Hazmat",
            "vertical": "dispatch",
            "instructions": "Report chlorine leak and end after receiving perimeter.",
            "success_criteria": {
                "expected_guardrail": "TRIGGER_HAZMAT_PERIMETER",
                "max_turns": 3
            }
        }

        personality = {
            "id": "test_p",
            "name": "Test Impatient",
            "assistant": {
                "firstMessage": "Chlorine tanker leaking at track 4!",
                "firstMessageMode": "assistant-speaks-first",
                "maxTurns": 2
            }
        }

        # Mock tester generating second turn with stopping condition
        async def mock_gen(*args, **kwargs):
            return ("Copy that evacuation order. [END_CONVERSATION]", True)

        with patch.object(engine, "generate_tester_response", side_effect=mock_gen):
            result = asyncio.run(engine.run_simulation(
                scenario=scenario,
                personality=personality,
                max_turns_override=2
            ))

        assert result.status == "completed"
        assert result.total_turns >= 1
        assert len(result.turns) >= 1
        assert result.turns[0]["tester_utterance"] == "Chlorine tanker leaking at track 4!"


# ---------------------------------------------------------------------------
# Test 5: API Endpoints (FastAPI TestClient)
# ---------------------------------------------------------------------------
class TestSimulationsAPI:
    def test_get_scenarios(self):
        res = client.get("/api/simulations/scenarios")
        assert res.status_code == 200
        data = res.json()
        assert "scenarios" in data
        assert len(data["scenarios"]) >= 6

    def test_create_and_delete_custom_scenario(self):
        payload = {
            "name": "API Custom Scenario",
            "vertical": "healthcare",
            "instructions": "Report acute abdominal pain.",
            "success_criteria": {"max_turns": 4}
        }
        create_res = client.post("/api/simulations/scenarios", json=payload)
        assert create_res.status_code == 201
        created = create_res.json()
        sc_id = created["id"]
        assert created["name"] == "API Custom Scenario"

        # Delete
        del_res = client.delete(f"/api/simulations/scenarios/{sc_id}")
        assert del_res.status_code == 204

    def test_get_personalities(self):
        res = client.get("/api/simulations/personalities")
        assert res.status_code == 200
        data = res.json()
        assert "personalities" in data
        assert len(data["personalities"]) >= 4

    def test_create_and_delete_custom_personality(self):
        payload = {
            "name": "API Custom Personality",
            "assistant": {
                "model": {"model": "gemini-2.0-flash"},
                "firstMessageMode": "assistant-speaks-first"
            }
        }
        create_res = client.post("/api/simulations/personalities", json=payload)
        assert create_res.status_code == 201
        created = create_res.json()
        p_id = created["id"]

        del_res = client.delete(f"/api/simulations/personalities/{p_id}")
        assert del_res.status_code == 204
