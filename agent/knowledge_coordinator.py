"""Knowledge Coordinator: Concurrent co-retrieval across Moss and Local Qdrant with dynamic sync."""
import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from agent.config import VERTICAL_INDEX_MAP, ENABLE_DYNAMIC_KNOWLEDGE
from agent.qdrant_engine import qdrant_engine

logger = logging.getLogger("agent.knowledge_coordinator")


@dataclass
class CoRetrievalResult:
    merged_text: str
    doc_ids: List[str] = field(default_factory=list)
    snippets: List[str] = field(default_factory=list)
    moss_docs: List[Any] = field(default_factory=list)
    qdrant_docs: List[Dict[str, Any]] = field(default_factory=list)
    moss_latency_ms: float = 0.0
    qdrant_latency_ms: float = 0.0
    total_latency_ms: float = 0.0
    is_sub_10ms: bool = True


class KnowledgeCoordinator:
    """Orchestrates concurrent sub-10ms co-retrieval between Moss (core SOPs) and Qdrant (dynamic updates)."""

    def __init__(self):
        self.qdrant = qdrant_engine

    async def concurrent_retrieve(
        self,
        moss_call: Any,
        vertical: str,
        query: str,
        limit: int = 3,
    ) -> CoRetrievalResult:
        """Executes Moss query and Local Qdrant query concurrently in parallel (<10ms)."""
        moss_index = VERTICAL_INDEX_MAP.get(vertical, "dispatch_emergency_ops")
        t_start = time.perf_counter()

        # Task 1: Moss Query (Mandatory Core SOPs)
        async def fetch_moss():
            t0 = time.perf_counter()
            try:
                if moss_call and hasattr(moss_call, "query"):
                    res = await moss_call.query(moss_index, query)
                    return res, (time.perf_counter() - t0) * 1000
            except Exception as e:
                logger.error(f"Moss co-retrieval error: {e}")
            return None, (time.perf_counter() - t0) * 1000

        # Task 2: Qdrant Query (Dynamic Updates & Local Facts)
        async def fetch_qdrant():
            t0 = time.perf_counter()
            try:
                if ENABLE_DYNAMIC_KNOWLEDGE:
                    # Run sync fastembed/qdrant search in thread executor to avoid blocking event loop
                    loop = asyncio.get_running_loop()
                    res = await loop.run_in_executor(
                        None,
                        lambda: self.qdrant.query(vertical, query, limit=limit)
                    )
                    return res, (time.perf_counter() - t0) * 1000
            except Exception as e:
                logger.error(f"Qdrant co-retrieval error: {e}")
            return [], (time.perf_counter() - t0) * 1000

        # Execute concurrently with asyncio.gather
        (moss_res, moss_time_ms), (qdrant_docs, qdrant_time_ms) = await asyncio.gather(
            fetch_moss(),
            fetch_qdrant(),
        )

        total_elapsed_ms = (time.perf_counter() - t_start) * 1000

        # Merge and format results
        doc_ids = []
        snippets = []
        context_parts = []
        seen_ids = set()

        # 1. Incorporate Moss Core SOPs
        moss_doc_list = []
        if moss_res and hasattr(moss_res, "docs") and moss_res.docs:
            moss_doc_list = moss_res.docs[:limit]
            for d in moss_doc_list:
                d_id = getattr(d, "id", "moss_doc")
                if d_id not in seen_ids:
                    seen_ids.add(d_id)
                    doc_ids.append(d_id)
                    text_val = getattr(d, "text", str(d))
                    snippets.append(text_val[:140] + "...")
                    context_parts.append(f"[MOSS CORE SOP] {text_val}")

        # 2. Incorporate Local Qdrant Dynamic Facts
        for qd in qdrant_docs:
            q_id = qd.get("id", "qdrant_doc")
            if q_id not in seen_ids:
                seen_ids.add(q_id)
                doc_ids.append(q_id)
                q_text = qd.get("text", "")
                category = qd.get("category", "dynamic")
                snippets.append(q_text[:140] + "...")
                context_parts.append(f"[DYNAMIC UPDATE: {category.upper()}] {q_text}")

        merged_text = "\n\n".join(context_parts)
        is_sub_10ms = total_elapsed_ms <= 10.0

        logger.info(
            f"Co-Retrieval completed in {total_elapsed_ms:.2f}ms "
            f"(Moss: {moss_time_ms:.2f}ms, Qdrant: {qdrant_time_ms:.2f}ms) "
            f"| Retrieved {len(doc_ids)} items"
        )

        return CoRetrievalResult(
            merged_text=merged_text,
            doc_ids=doc_ids,
            snippets=snippets,
            moss_docs=moss_doc_list,
            qdrant_docs=qdrant_docs,
            moss_latency_ms=moss_time_ms,
            qdrant_latency_ms=qdrant_time_ms,
            total_latency_ms=total_elapsed_ms,
            is_sub_10ms=is_sub_10ms,
        )

    async def sync_qdrant_to_moss(self, moss_agent: Any, vertical: str) -> Dict[str, Any]:
        """Exports dynamic Qdrant documents into a consolidated Moss index via hot reload."""
        if not moss_agent:
            return {"status": "error", "message": "MossAgent instance not provided"}

        from moss_agent import DocumentInfo
        target_index = VERTICAL_INDEX_MAP.get(vertical, "dispatch_emergency_ops")

        # Scroll active docs from Qdrant
        all_qdrant_docs = self.qdrant.list_documents(vertical, limit=200)
        active_docs = [d for d in all_qdrant_docs if not d.get("is_expired")]

        moss_docs = [
            DocumentInfo(id=d["id"], text=f"[{vertical.upper()}] {d['title']}\n{d['text_preview']}")
            for d in active_docs
        ]

        if not moss_docs:
            return {"status": "noop", "message": "No active dynamic documents to sync"}

        try:
            # Refresh Moss index
            await moss_agent.create_index(target_index, moss_docs)
            await moss_agent.load_indexes([target_index])
            logger.info(f"Successfully synced {len(moss_docs)} dynamic docs into Moss index '{target_index}'")
            return {"status": "success", "synced_count": len(moss_docs), "index": target_index}
        except Exception as e:
            logger.error(f"Error syncing Qdrant to Moss: {e}")
            return {"status": "error", "message": str(e)}


coordinator = KnowledgeCoordinator()
