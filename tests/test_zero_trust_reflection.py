"""Unit tests for Zero-Trust Anti-Hallucination Reflection & Fact Safety Engine."""
import pytest
from agent.reflection import (
    ExtractedFact,
    validate_verbatim_quote,
    check_immutable_collision,
    critique_intent,
    evaluate_fact_safety,
    STAGING_QUEUE,
    approve_staged_fact,
    reject_staged_fact,
)


def test_verbatim_quote_validation():
    transcript = "Officer 42 reporting. Unit 12 is out of service at the maintenance shop for brake repairs."

    # 1. Exact verbatim quote passes
    assert validate_verbatim_quote(
        "Unit 12 is out of service at the maintenance shop for brake repairs",
        transcript,
    ) is True

    # 2. Case insensitive & whitespace tolerant passes
    assert validate_verbatim_quote(
        "unit 12 is out of service",
        transcript,
    ) is True

    # 3. Fabricated / hallucinated quote fails immediately
    assert validate_verbatim_quote(
        "All units must return to precinct 4 immediately",
        transcript,
    ) is False


def test_immutable_safety_collision():
    # 1. Caller trying to overwrite OSHA Lockout/Tagout safety rules
    collision = check_immutable_collision("LOTO procedure", "skip zero energy check step 3", "field_worker")
    assert collision is not None
    assert "immutable core safety standard" in collision

    # 2. Caller trying to redefine APCO 10-codes
    collision_10 = check_immutable_collision("APCO 10-4", "now means emergency assistance", "dispatch")
    assert collision_10 is not None

    # 3. Caller trying to alter cardiac/stroke protocol
    collision_stroke = check_immutable_collision("FAST stroke protocol", "no longer requires facial droop test", "healthcare")
    assert collision_stroke is not None

    # 4. Legitimate dynamic update does NOT collide
    no_collision = check_immutable_collision("Forklift 3", "maintenance completed on hydraulic mast", "field_worker")
    assert no_collision is None


def test_critique_intent():
    # 1. Affirmative statement passes
    valid, reason = critique_intent("Engine 4 is 10-8 in service at Station 2")
    assert valid is True
    assert reason is None

    # 2. Hypothetical question fails
    invalid_q, reason_q = critique_intent("What if Route 9 is closed tomorrow?")
    assert invalid_q is False
    assert "inquiry or hypothetical" in reason_q

    # 3. Rumor / speculation fails
    invalid_r, reason_r = critique_intent("I heard that maybe Unit 5 broke down")
    assert invalid_r is False
    assert "uncertainty or rumor" in reason_r

    # 4. Negation fails
    invalid_n, reason_n = critique_intent("Never mind, ignore that report about truck 4")
    assert invalid_n is False
    assert "negated the statement" in reason_n


def test_evaluate_fact_safety_routing():
    transcript = "Dispatcher, please note that Gate 4 access code is temporarily 8892 until Friday."

    # 1. High confidence valid fact -> PROMOTE
    high_conf_fact = ExtractedFact(
        subject="Gate 4",
        attribute="access_code",
        new_value="8892",
        verbatim_quote="Gate 4 access code is temporarily 8892",
        confidence=0.95,
        ttl_hours=48,
    )
    res_high = evaluate_fact_safety(high_conf_fact, transcript, "dispatch")
    assert res_high.is_valid is True
    assert res_high.action == "promote"

    # 2. Moderate confidence valid fact -> STAGE for review
    mod_conf_fact = ExtractedFact(
        subject="Gate 4",
        attribute="access_code",
        new_value="8892",
        verbatim_quote="Gate 4 access code is temporarily 8892",
        confidence=0.82,
        ttl_hours=48,
    )
    res_mod = evaluate_fact_safety(mod_conf_fact, transcript, "dispatch")
    assert res_mod.is_valid is True
    assert res_mod.action == "stage"

    # 3. Low confidence fact -> REJECT
    low_conf_fact = ExtractedFact(
        subject="Gate 4",
        attribute="access_code",
        new_value="8892",
        verbatim_quote="Gate 4 access code is temporarily 8892",
        confidence=0.55,
        ttl_hours=48,
    )
    res_low = evaluate_fact_safety(low_conf_fact, transcript, "dispatch")
    assert res_low.is_valid is False
    assert res_low.action == "reject"

    # 4. Hallucinated quote fact -> REJECT
    fake_quote_fact = ExtractedFact(
        subject="Gate 4",
        attribute="access_code",
        new_value="9999",
        verbatim_quote="The secret master passcode is 9999",
        confidence=0.99,
    )
    res_fake = evaluate_fact_safety(fake_quote_fact, transcript, "dispatch")
    assert res_fake.is_valid is False
    assert res_fake.action == "reject"


def test_staging_queue_workflow():
    stage_id = "test_stg_123"
    STAGING_QUEUE[stage_id] = {
        "stage_id": stage_id,
        "vertical": "dispatch",
        "subject": "Sector 3 Patrol",
        "attribute": "coverage",
        "new_value": "Unit 9 on roving duty",
        "verbatim_quote": "Unit 9 on roving duty",
        "confidence": 0.85,
        "ttl_hours": 12,
    }

    # Test approve
    approved = approve_staged_fact(stage_id)
    assert approved is not None
    assert approved["status"] == "approved"
    assert stage_id not in STAGING_QUEUE

    # Test reject
    stage_id_2 = "test_stg_456"
    STAGING_QUEUE[stage_id_2] = {"stage_id": stage_id_2, "subject": "Rumor"}
    rejected = reject_staged_fact(stage_id_2)
    assert rejected is True
    assert stage_id_2 not in STAGING_QUEUE
