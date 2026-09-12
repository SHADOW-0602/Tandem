"""Unit tests for OpenTelemetry Distributed Tracing in Tandem."""
import pytest
from fastapi.testclient import TestClient
from agent.otel_tracer import get_tracer, get_trace_history, in_memory_exporter
from server.main import app


def test_otel_tracer_span_creation():
    """Verifies that OpenTelemetry spans are recorded and buffered into in-memory exporter."""
    tracer = get_tracer()

    with tracer.start_as_current_span("test_voice_turn") as span:
        span.set_attribute("call.id", "call_test_999")
        span.set_attribute("call.vertical", "dispatch")
        span.set_attribute("retrieval.moss_ms", 5.4)
        span.set_attribute("retrieval.qdrant_ms", 4.9)
        span.set_attribute("retrieval.is_sub_10ms", True)

    # Force export flush
    from opentelemetry import trace
    provider = trace.get_tracer_provider()
    if hasattr(provider, "force_flush"):
        provider.force_flush()

    traces = get_trace_history(limit=10)
    assert len(traces) > 0

    matching = [t for t in traces if t["name"] == "test_voice_turn"]
    assert len(matching) > 0
    span_data = matching[0]
    assert span_data["attributes"]["call.id"] == "call_test_999"
    assert span_data["attributes"]["retrieval.moss_ms"] == 5.4
    assert span_data["attributes"]["retrieval.is_sub_10ms"] is True


def test_otel_traces_api_endpoint():
    """Verifies that the /api/telemetry/traces endpoint returns recent spans."""
    client = TestClient(app)
    response = client.get("/api/telemetry/traces?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "spans" in data
    assert isinstance(data["spans"], list)
