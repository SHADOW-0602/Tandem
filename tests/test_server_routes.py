import pytest
from fastapi.testclient import TestClient
from server.main import app

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "moss_retrieval_target" in data

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_list_verticals():
    response = client.get("/api/verticals")
    assert response.status_code == 200
    verticals = response.json()
    assert len(verticals) >= 6
    vert_ids = [v["id"] for v in verticals]
    assert "dispatch" in vert_ids
    assert "healthcare" in vert_ids
    assert "field_worker" in vert_ids
    assert "customer_support" in vert_ids
    assert "logistics_fleet" in vert_ids
    assert "financial_compliance" in vert_ids

def test_token_minting():
    response = client.post(
        "/api/token",
        json={"room_name": "test-room-42", "identity": "tester-1", "vertical": "dispatch"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert len(data["token"]) > 50
    assert data["room_name"] == "test-room-42"
    assert data["vertical"] == "dispatch"

def test_telemetry_ingestion_and_stats():
    payload = {
        "call_id": "test-call-99",
        "turn_id": 1,
        "vertical": "dispatch",
        "user_transcript": "Unit 4 reporting 10-50",
        "agent_response": "10-4 Unit 4",
        "retrieved_doc_ids": ["disp-001"],
        "retrieved_snippets": ["APCO Ten-Codes: 10-50 Motor vehicle accident"],
        "stt_latency_ms": 240.0,
        "moss_latency_ms": 6.8,
        "llm_ttft_ms": 175.0,
        "tts_ttfb_ms": 140.0,
        "total_latency_ms": 561.8,
        "is_sub_10ms_moss": True,
        "within_budget": True,
    }
    post_res = client.post("/api/telemetry", json=payload)
    assert post_res.status_code == 200

    stats_res = client.get("/api/telemetry/stats")
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert stats["total_turns"] >= 1
    assert stats["avg_moss_latency_ms"] <= 10.0
