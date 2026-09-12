import asyncio
import pytest
from moss_agent import MossAgent
from agent.config import MOSS_PROJECT_ID, MOSS_PROJECT_KEY, ALL_MOSS_INDEXES

def test_moss_prewarmed_query_latency():
    async def _run():
        agent = MossAgent(
            project_id=MOSS_PROJECT_ID,
            project_key=MOSS_PROJECT_KEY,
        )
        
        # Prewarm
        res = await agent.load_indexes(ALL_MOSS_INDEXES)
        if hasattr(res, "failed") and "credit_exhausted" in str(res.failed):
            pytest.skip("Moss Cloud API credit quota exhausted on project key.")
            return

        # Verify sub-10ms retrieval internal latency on hot index
        query = "10-50 accident response protocol"
        query_res = await agent.query("dispatch_emergency_ops", query)
        
        assert query_res is not None
        assert len(query_res.docs) > 0
        internal_time = getattr(query_res, "time_taken_ms", 0.0)
        print(f"\nInternal Moss retrieval time: {internal_time} ms")
        assert internal_time <= 10.0, f"Moss internal time {internal_time}ms exceeded 10ms target"

    asyncio.run(_run())

