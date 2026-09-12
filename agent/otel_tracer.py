"""OpenTelemetry Distributed Tracing Engine for Tandem Voice Agents.

Provides zero-latency in-memory batch tracing for voice turns, concurrent co-retrieval
(Moss + Local Qdrant), and post-call Zero-Trust reflection.
"""
import logging
import os
import time
from typing import Any, Dict, List, Optional

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    SpanExporter,
    SpanExportResult,
)

logger = logging.getLogger("agent.otel_tracer")


class InMemoryRingSpanExporter(SpanExporter):
    """Thread-safe in-memory ring buffer that retains recent spans for the telemetry dashboard."""

    def __init__(self, capacity: int = 250):
        self.capacity = capacity
        self._spans: List[Dict[str, Any]] = []

    def export(self, spans) -> SpanExportResult:
        for s in spans:
            duration_ms = 0.0
            if s.end_time and s.start_time:
                duration_ms = (s.end_time - s.start_time) / 1e6  # nanoseconds to ms

            span_data = {
                "name": s.name,
                "context": {
                    "trace_id": format(s.context.trace_id, "032x") if s.context else "",
                    "span_id": format(s.context.span_id, "016x") if s.context else "",
                },
                "start_time": s.start_time / 1e9 if s.start_time else time.time(),
                "end_time": s.end_time / 1e9 if s.end_time else time.time(),
                "duration_ms": round(duration_ms, 2),
                "attributes": dict(s.attributes or {}),
                "status": str(s.status.status_code.name) if hasattr(s.status, "status_code") else "OK",
            }
            self._spans.append(span_data)

        # Trim to capacity
        if len(self._spans) > self.capacity:
            self._spans = self._spans[-self.capacity:]

        return SpanExportResult.SUCCESS

    def get_recent_spans(self, limit: int = 50) -> List[Dict[str, Any]]:
        return list(reversed(self._spans[-limit:]))

    def clear(self) -> None:
        self._spans.clear()

    def shutdown(self) -> None:
        pass


# Global singleton exporter and provider
in_memory_exporter = InMemoryRingSpanExporter(capacity=300)
_tracer: Optional[trace.Tracer] = None


def setup_telemetry(
    service_name: str = "tandem-voice-agent",
    otlp_endpoint: Optional[str] = None,
) -> trace.Tracer:
    """Initializes OpenTelemetry TracerProvider with asynchronous BatchSpanProcessor."""
    global _tracer
    if _tracer is not None:
        return _tracer

    logger.info(f"Initializing OpenTelemetry (Service: {service_name})...")
    resource = Resource.create({"service.name": service_name, "framework": "livekit-moss-tandem"})
    provider = TracerProvider(resource=resource)

    # 1. In-memory ring buffer exporter for instant API & web dashboard querying
    provider.add_span_processor(BatchSpanProcessor(in_memory_exporter))

    # 2. Optional remote OTLP exporter (e.g. Jaeger, SigNoz, Langfuse, or Phoenix)
    endpoint = otlp_endpoint or os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if endpoint:
        try:
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
            otlp_processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint))
            provider.add_span_processor(otlp_processor)
            logger.info(f"OpenTelemetry OTLP Exporter connected to: {endpoint}")
        except Exception as oe:
            logger.warning(f"Could not connect remote OTLP exporter: {oe}")

    trace.set_tracer_provider(provider)
    _tracer = trace.get_tracer(service_name)
    logger.info("OpenTelemetry Tracer ready.")
    return _tracer


def get_tracer() -> trace.Tracer:
    """Returns the global active OpenTelemetry tracer."""
    global _tracer
    if _tracer is None:
        _tracer = setup_telemetry()
    return _tracer


def get_trace_history(limit: int = 50) -> List[Dict[str, Any]]:
    """Returns recently recorded spans from the in-memory ring buffer."""
    return in_memory_exporter.get_recent_spans(limit=limit)
