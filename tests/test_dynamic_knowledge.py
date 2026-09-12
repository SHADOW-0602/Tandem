"""Unit tests for Local Embedded Qdrant Engine and Concurrent Knowledge Coordinator."""
import asyncio
import time
import pytest
from pathlib import Path
from agent.qdrant_engine import LocalQdrantEngine
from agent.knowledge_coordinator import KnowledgeCoordinator


@pytest.fixture
def qdrant_test_engine(tmp_path):
    """Initializes an isolated temporary LocalQdrantEngine instance."""
    engine = LocalQdrantEngine(storage_path=str(tmp_path / "test_qdrant"))
    engine.initialize()
    return engine


def test_qdrant_initialization_and_seeding(qdrant_test_engine):
    """Verifies that collections are created and baseline SOPs are seeded correctly."""
    counts = qdrant_test_engine.seed_from_json(force_reload=True)
    assert len(counts) > 0
    assert "dispatch" in counts
    assert counts["dispatch"] > 0

    docs = qdrant_test_engine.list_documents("dispatch")
    assert len(docs) > 0
    assert any("APCO" in d["title"] or "10-" in d["text_preview"] or "CODE" in d["text_preview"] for d in docs)


def test_qdrant_sub_10ms_query_speed(qdrant_test_engine):
    """Benchmarks that retrieval strictly completes in under 10ms."""
    qdrant_test_engine.seed_from_json(force_reload=False)

    # Warmup queries to initialize disk mmap page cache and ONNX execution provider
    for _ in range(2):
        _ = qdrant_test_engine.query("dispatch", "motor vehicle accident", limit=2)

    # Timed benchmark
    latencies = []
    queries = [
        "10-50 traffic collision",
        "Chlorine gas evacuation distance",
        "Code 3 lights and sirens",
        "HAZMAT flammable liquids",
        "pursuit protocol",
    ]

    for q in queries:
        t0 = time.perf_counter()
        results = qdrant_test_engine.query("dispatch", q, limit=2)
        elapsed_ms = (time.perf_counter() - t0) * 1000
        latencies.append(elapsed_ms)
        assert len(results) > 0

    avg_latency = sum(latencies) / len(latencies)
    print(f"\nAverage local Qdrant query latency: {avg_latency:.2f}ms (Max: {max(latencies):.2f}ms)")
    assert avg_latency < 10.0, f"Average latency {avg_latency:.2f}ms exceeded 10ms SLA"


def test_qdrant_dynamic_live_upsert_and_delete(qdrant_test_engine):
    """Verifies live upsert and immediate availability on next search."""
    doc_id = "test_detour_sop_01"
    upsert_res = qdrant_test_engine.upsert_document(
        vertical="dispatch",
        doc_id=doc_id,
        title="Interstate 80 Closure",
        text="Interstate 80 Eastbound is closed at Exit 42 due to severe mudslide. Divert all units to Route 10.",
        category="traffic_detour",
        ttl_hours=12,
    )
    assert upsert_res["status"] == "success"

    # Query immediately
    results = qdrant_test_engine.query("dispatch", "mudslide Exit 42 detour", limit=2)
    assert len(results) > 0
    assert any(r["id"] == doc_id for r in results)

    # Test deletion
    del_res = qdrant_test_engine.delete_document("dispatch", doc_id)
    assert del_res is True

    # Query again to confirm removal
    post_delete_results = qdrant_test_engine.query("dispatch", "mudslide Exit 42 detour", limit=2)
    assert not any(r["id"] == doc_id for r in post_delete_results)


def test_qdrant_ttl_filtering(qdrant_test_engine):
    """Verifies that expired facts are automatically filtered out from search."""
    # 1. Add active doc
    qdrant_test_engine.upsert_document(
        vertical="dispatch",
        doc_id="active_fact",
        title="Active Weather Hazard",
        text="Heavy dense fog warning across Sector 4.",
        ttl_hours=1,
    )

    # 2. Add expired doc (using negative TTL)
    qdrant_test_engine.upsert_document(
        vertical="dispatch",
        doc_id="expired_fact",
        title="Old Fog Warning",
        text="Sector 4 dense fog has cleared.",
        ttl_hours=-1,
    )

    results = qdrant_test_engine.query("dispatch", "dense fog Sector 4", limit=5)
    ids = [r["id"] for r in results]
    assert "active_fact" in ids
    assert "expired_fact" not in ids


def test_concurrent_co_retrieval(qdrant_test_engine):
    """Verifies concurrent co-retrieval between mock Moss and Local Qdrant."""
    qdrant_test_engine.seed_from_json()
    coordinator = KnowledgeCoordinator()
    coordinator.qdrant = qdrant_test_engine

    class MockMossDoc:
        def __init__(self, id, text):
            self.id = id
            self.text = text

    class MockMossCall:
        async def query(self, index, query_str):
            await asyncio.sleep(0.005)  # Simulate 5ms Moss engine
            return type("MossRes", (), {"docs": [MockMossDoc("moss_10_50", "APCO 10-50 Motor Vehicle Accident")]})()

    async def _run():
        mock_call = MockMossCall()
        result = await coordinator.concurrent_retrieve(
            moss_call=mock_call,
            vertical="dispatch",
            query="10-50 traffic accident",
            limit=2,
        )
        assert result.total_latency_ms < 20.0
        assert len(result.doc_ids) > 0
        assert "MOSS CORE SOP" in result.merged_text

    asyncio.run(_run())
