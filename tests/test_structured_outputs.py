"""Tests for the structured output extraction engine."""
import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from dataclasses import dataclass
from typing import List

from agent.structured_outputs import (
    ConditionEvaluator,
    build_transcript,
    ExtractionResult,
    VERTICAL_SCHEMAS,
    run_extraction_for_call,
)
from agent.memory import ConversationTurn


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_turns(n: int) -> List[ConversationTurn]:
    return [
        ConversationTurn(
            turn_id=i,
            user_text=f"User message {i}",
            agent_text=f"Agent response {i}",
        )
        for i in range(n)
    ]


# ---------------------------------------------------------------------------
# ConditionEvaluator
# ---------------------------------------------------------------------------

class TestConditionEvaluator:
    def test_no_conditions_always_runs(self):
        ok, reason = ConditionEvaluator.evaluate([], 0, 0, "unknown")
        assert ok is True
        assert reason is None

    def test_min_messages_pass(self):
        ok, reason = ConditionEvaluator.evaluate(
            [{"type": "minMessages", "count": 4}], 5, 30, "unknown"
        )
        assert ok is True

    def test_min_messages_fail(self):
        ok, reason = ConditionEvaluator.evaluate(
            [{"type": "minMessages", "count": 4}], 2, 30, "unknown"
        )
        assert ok is False
        assert "minMessages" in reason

    def test_min_call_duration_pass(self):
        ok, reason = ConditionEvaluator.evaluate(
            [{"type": "minCallDuration", "seconds": 10}], 5, 15.0, "unknown"
        )
        assert ok is True

    def test_min_call_duration_fail(self):
        ok, reason = ConditionEvaluator.evaluate(
            [{"type": "minCallDuration", "seconds": 10}], 5, 5.0, "unknown"
        )
        assert ok is False
        assert "minCallDuration" in reason

    def test_ended_reason_one_of_pass(self):
        ok, reason = ConditionEvaluator.evaluate(
            [{"type": "endedReason", "operator": "oneOf", "values": ["customer-ended-call"]}],
            4, 30, "customer-ended-call"
        )
        assert ok is True

    def test_ended_reason_one_of_fail(self):
        ok, reason = ConditionEvaluator.evaluate(
            [{"type": "endedReason", "operator": "oneOf", "values": ["customer-ended-call"]}],
            4, 30, "agent-ended-call"
        )
        assert ok is False

    def test_ended_reason_not_one_of_pass(self):
        ok, reason = ConditionEvaluator.evaluate(
            [{"type": "endedReason", "operator": "notOneOf", "values": ["silence-timed-out"]}],
            4, 30, "agent-ended-call"
        )
        assert ok is True

    def test_ended_reason_not_one_of_fail(self):
        ok, reason = ConditionEvaluator.evaluate(
            [{"type": "endedReason", "operator": "notOneOf", "values": ["silence-timed-out"]}],
            4, 30, "silence-timed-out"
        )
        assert ok is False

    def test_all_conditions_must_pass(self):
        """AND semantics — all must pass."""
        ok, reason = ConditionEvaluator.evaluate(
            [
                {"type": "minMessages", "count": 4},
                {"type": "minCallDuration", "seconds": 10},
            ],
            5, 5.0, "unknown"  # duration fails
        )
        assert ok is False


# ---------------------------------------------------------------------------
# build_transcript
# ---------------------------------------------------------------------------

class TestBuildTranscript:
    def test_empty_history(self):
        assert build_transcript([]) == ""

    def test_single_turn(self):
        turns = make_turns(1)
        t = build_transcript(turns)
        assert "User message 0" in t
        assert "Agent response 0" in t

    def test_multiple_turns_ordered(self):
        turns = make_turns(3)
        t = build_transcript(turns)
        lines = t.splitlines()
        assert any("User message 0" in l for l in lines)
        assert any("User message 2" in l for l in lines)

    def test_filters_placeholder_agent_text(self):
        turns = [ConversationTurn(
            turn_id=0,
            user_text="Hello",
            agent_text="Response synthesized with SOP"  # filtered placeholder
        )]
        t = build_transcript(turns)
        assert "synthesized" not in t
        assert "Hello" in t


# ---------------------------------------------------------------------------
# VERTICAL_SCHEMAS
# ---------------------------------------------------------------------------

class TestVerticalSchemas:
    def test_all_six_verticals_present(self):
        expected = {"dispatch", "healthcare", "field_worker",
                    "customer_support", "logistics_fleet", "financial_compliance"}
        assert set(VERTICAL_SCHEMAS.keys()) == expected

    def test_schemas_have_required_keys(self):
        for vertical, sdef in VERTICAL_SCHEMAS.items():
            assert "name" in sdef, f"{vertical} missing 'name'"
            assert "schema" in sdef, f"{vertical} missing 'schema'"
            schema = sdef["schema"]
            assert schema.get("type") == "object", f"{vertical} schema must be type:object"
            assert "properties" in schema, f"{vertical} schema missing 'properties'"
            assert "required" in schema, f"{vertical} schema missing 'required'"

    def test_required_fields_are_boolean_safety_fields(self):
        """Every vertical requires at least one boolean safety/compliance field."""
        for vertical, sdef in VERTICAL_SCHEMAS.items():
            required = sdef["schema"].get("required", [])
            props = sdef["schema"].get("properties", {})
            bool_required = [
                f for f in required
                if props.get(f, {}).get("type") == "boolean"
            ]
            assert bool_required, (
                f"{vertical} should require at least one boolean safety field, got required={required}"
            )


# ---------------------------------------------------------------------------
# StructuredOutputExtractor — mocked Gemini call
# ---------------------------------------------------------------------------

class TestStructuredOutputExtractor:
    @pytest.fixture
    def extractor(self):
        from agent.structured_outputs import StructuredOutputExtractor
        return StructuredOutputExtractor(api_key="test-key", model_name="gemini-2.0-flash")

    def test_extraction_success(self, extractor):
        mock_response = MagicMock()
        mock_response.text = '{"incidentType": "Traffic Stop", "hazmatInvolved": false, "escalatedToCommandSupervisor": false}'

        with patch.object(extractor, "_get_client") as mock_client_getter:
            mock_client = MagicMock()
            mock_client_getter.return_value = mock_client
            mock_client.models.generate_content.return_value = mock_response

            schema_def = {
                **VERTICAL_SCHEMAS["dispatch"],
                "vertical": "dispatch",
            }
            result = asyncio.run(extractor.extract(
                call_id="test-123",
                schema_id="default_dispatch",
                schema_def=schema_def,
                transcript="User: Unit 12 traffic stop on Main St.\nAgent: Ten four, Unit 12.",
                conditions=[],
                message_count=2,
                call_duration_seconds=45.0,
            ))

        assert result.skipped is False
        assert result.result is not None
        assert result.result["incidentType"] == "Traffic Stop"
        assert result.result["hazmatInvolved"] is False

    def test_skipped_when_condition_fails(self, extractor):
        schema_def = {**VERTICAL_SCHEMAS["dispatch"], "vertical": "dispatch"}
        result = asyncio.run(extractor.extract(
            call_id="test-456",
            schema_id="default_dispatch",
            schema_def=schema_def,
            transcript="User: hello.\nAgent: hi.",
            conditions=[{"type": "minMessages", "count": 10}],
            message_count=2,
            call_duration_seconds=5.0,
        ))
        assert result.skipped is True
        assert result.result is None
        assert "minMessages" in result.skip_reason

    def test_empty_transcript_skipped(self, extractor):
        schema_def = {**VERTICAL_SCHEMAS["healthcare"], "vertical": "healthcare"}
        result = asyncio.run(extractor.extract(
            call_id="test-789",
            schema_id="default_healthcare",
            schema_def=schema_def,
            transcript="",
            conditions=[],
            message_count=0,
            call_duration_seconds=0.0,
        ))
        assert result.skipped is True
        assert "Empty transcript" in result.skip_reason

    def test_extraction_handles_invalid_json(self, extractor):
        mock_response = MagicMock()
        mock_response.text = "Sorry, I cannot do that."  # not JSON

        with patch.object(extractor, "_get_client") as mock_client_getter:
            mock_client = MagicMock()
            mock_client_getter.return_value = mock_client
            mock_client.models.generate_content.return_value = mock_response

            schema_def = {**VERTICAL_SCHEMAS["dispatch"], "vertical": "dispatch"}
            result = asyncio.run(extractor.extract(
                call_id="test-bad-json",
                schema_id="default_dispatch",
                schema_def=schema_def,
                transcript="Something happened on the call.",
                conditions=[],
                message_count=3,
                call_duration_seconds=30.0,
            ))

        assert result.skipped is False
        assert result.result is None  # graceful null on bad JSON


# ---------------------------------------------------------------------------
# Server DB functions
# ---------------------------------------------------------------------------

class TestServerDb:
    def test_register_and_get_schema(self):
        from server.db import register_schema, get_schema, delete_schema
        register_schema("test-schema-01", {"name": "Test", "vertical": "dispatch"})
        schema = get_schema("test-schema-01")
        assert schema is not None
        assert schema["name"] == "Test"
        delete_schema("test-schema-01")

    def test_list_schemas_by_vertical(self):
        from server.db import register_schema, list_schemas, delete_schema
        register_schema("sA", {"name": "A", "vertical": "dispatch"})
        register_schema("sB", {"name": "B", "vertical": "healthcare"})
        dispatch_schemas = list_schemas("dispatch")
        assert any(s["schema_id"] == "sA" for s in dispatch_schemas)
        assert not any(s["schema_id"] == "sB" for s in dispatch_schemas)
        delete_schema("sA")
        delete_schema("sB")

    def test_store_and_get_extraction_results(self):
        from server.db import store_extraction_results, get_extraction_results
        results = [{"schema_id": "default_dispatch", "name": "Dispatch Incident Summary", "result": {"incidentType": "Fire"}}]
        store_extraction_results("call-abc-123", results)
        fetched = get_extraction_results("call-abc-123")
        assert len(fetched) >= 1
        assert fetched[0]["result"]["incidentType"] == "Fire"
