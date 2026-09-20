"""Local embedded Qdrant vector engine with FastEmbed for sub-10ms dynamic retrieval."""
import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastembed import TextEmbedding
from qdrant_client import QdrantClient, models

from agent.config import (
    EMBEDDING_MODEL_NAME,
    QDRANT_STORAGE_PATH,
    VERTICAL_INDEX_MAP,
)

logger = logging.getLogger("agent.qdrant_engine")

# Year 9999 sentinel timestamp for permanent SOPs
PERMANENT_EXPIRY_TS = 253402300799.0
VECTOR_DIMENSION = 384  # bge-small-en-v1.5 produces 384-dimensional embeddings


class LocalQdrantEngine:
    """Embedded in-process Qdrant vector database with FastEmbed for sub-10ms retrieval."""

    def __init__(
        self,
        storage_path: Optional[str] = None,
        model_name: str = EMBEDDING_MODEL_NAME,
    ):
        self.storage_path = storage_path or QDRANT_STORAGE_PATH
        self.model_name = model_name
        self.client: Optional[QdrantClient] = None
        self.embedder: Optional[TextEmbedding] = None
        self._is_initialized = False

    def _get_embedder(self) -> TextEmbedding:
        """Lazy-loads FastEmbed ONNX model only when embedding operations are required."""
        if self.embedder is None:
            t0 = time.perf_counter()
            logger.info(f"Loading FastEmbed ONNX model '{self.model_name}' on demand...")
            self.embedder = TextEmbedding(model_name=self.model_name)
            logger.info(f"FastEmbed model loaded in {(time.perf_counter() - t0)*1000:.1f}ms")
        return self.embedder

    def initialize(self) -> None:
        """Initializes the Qdrant client and verifies collection schema (lightweight, zero ONNX bloat)."""
        if self._is_initialized:
            return

        t_start = time.perf_counter()
        logger.info(f"Initializing LocalQdrantEngine (Storage: {self.storage_path})...")

        if self.storage_path == ":memory:":
            self.client = QdrantClient(":memory:")
        else:
            storage_dir = Path(self.storage_path)
            storage_dir.mkdir(parents=True, exist_ok=True)
            try:
                self.client = QdrantClient(path=str(storage_dir))
            except Exception as le:
                logger.warning(f"File storage lock detected ({le}), using in-memory Qdrant client fallback.")
                self.client = QdrantClient(":memory:")

        # Ensure vertical collections exist (pure metadata, minimal RAM)
        distinct_verticals = set(VERTICAL_INDEX_MAP.keys())
        for vert in distinct_verticals:
            col_name = self._collection_name(vert)
            if not self.client.collection_exists(col_name):
                logger.info(f"Creating local Qdrant collection: {col_name}")
                self.client.create_collection(
                    collection_name=col_name,
                    vectors_config=models.VectorParams(
                        size=VECTOR_DIMENSION,
                        distance=models.Distance.COSINE,
                    ),
                )

        self._is_initialized = True
        elapsed_ms = (time.perf_counter() - t_start) * 1000
        logger.info(f"LocalQdrantEngine initialized in {elapsed_ms:.2f}ms")

    def _collection_name(self, vertical: str) -> str:
        return f"tandem_{vertical.lower()}"

    def is_seeded(self) -> bool:
        """Checks if all vertical collections contain seeded documents without re-embedding."""
        if not self._is_initialized:
            self.initialize()
        distinct_verticals = set(VERTICAL_INDEX_MAP.keys())
        for vert in distinct_verticals:
            col_name = self._collection_name(vert)
            if not self.client.collection_exists(col_name):
                return False
            try:
                if self.client.count(col_name).count == 0:
                    return False
            except Exception:
                return False
        return True

    def seed_from_json(self, knowledge_dir: Optional[Path] = None, force_reload: bool = False) -> Dict[str, int]:
        """Seeds baseline SOPs from JSON files into local collections."""
        import gc

        if not self._is_initialized:
            self.initialize()

        if knowledge_dir is None:
            knowledge_dir = Path(__file__).resolve().parent / "knowledge"

        file_vertical_map = {
            "dispatch_sops.json": "dispatch",
            "logistics_fleet.json": "logistics_fleet",
            "healthcare_triage.json": "healthcare",
            "field_worker_loto.json": "field_worker",
            "customer_support_sla.json": "customer_support",
            "financial_compliance.json": "financial_compliance",
        }

        counts = {}
        for fname, vertical in file_vertical_map.items():
            fpath = knowledge_dir / fname
            if not fpath.exists():
                logger.warning(f"Knowledge file {fpath} not found")
                continue

            col_name = self._collection_name(vertical)
            current_count = self.client.count(col_name).count
            if current_count > 0 and not force_reload:
                counts[vertical] = current_count
                continue

            with open(fpath, "r", encoding="utf-8") as f:
                items = json.load(f)

            points = []
            texts_to_embed = []
            for item in items:
                doc_text = f"[{item.get('vertical','').upper()} | {item.get('category','').upper()}] {item['title']}\n{item['text']}"
                texts_to_embed.append(doc_text)

            vectors = list(self._get_embedder().embed(texts_to_embed))

            for idx, (item, vec, full_text) in enumerate(zip(items, vectors, texts_to_embed)):
                doc_id = item["id"]
                point_id = abs(hash(doc_id)) % (2**63 - 1)
                points.append(
                    models.PointStruct(
                        id=point_id,
                        vector=vec.tolist(),
                        payload={
                            "doc_id": doc_id,
                            "title": item.get("title", ""),
                            "text": full_text,
                            "raw_text": item.get("text", ""),
                            "category": item.get("category", "general"),
                            "vertical": vertical,
                            "is_immutable": True,  # Core SOPs are immutable
                            "expires_at": PERMANENT_EXPIRY_TS,
                            "created_at": time.time(),
                        },
                    )
                )

            if points:
                self.client.upsert(collection_name=col_name, points=points)
                counts[vertical] = len(points)
                logger.info(f"Seeded {len(points)} immutable documents into {col_name}")

            # Reclaim transient memory after each vertical embedding batch
            del points, texts_to_embed, vectors
            gc.collect()

        return counts

    def query(
        self,
        vertical: str,
        query_text: str,
        limit: int = 3,
        score_threshold: float = 0.40,
    ) -> List[Dict[str, Any]]:
        """Executes ultra-fast (<8ms) vector search with TTL filtering against local Qdrant."""
        if not self._is_initialized:
            self.initialize()

        col_name = self._collection_name(vertical)
        if not self.client.collection_exists(col_name):
            return []

        q_vec = list(self._get_embedder().embed([query_text]))[0].tolist()

        now = time.time()
        ttl_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="expires_at",
                    range=models.Range(gt=now),
                )
            ]
        )

        res = self.client.query_points(
            collection_name=col_name,
            query=q_vec,
            query_filter=ttl_filter,
            limit=limit,
            score_threshold=score_threshold,
        )

        docs = []
        for p in res.points:
            payload = p.payload or {}
            docs.append(
                {
                    "id": payload.get("doc_id", str(p.id)),
                    "title": payload.get("title", ""),
                    "text": payload.get("text", ""),
                    "raw_text": payload.get("raw_text", ""),
                    "category": payload.get("category", "general"),
                    "is_immutable": payload.get("is_immutable", False),
                    "expires_at": payload.get("expires_at", PERMANENT_EXPIRY_TS),
                    "score": float(p.score) if hasattr(p, "score") and p.score is not None else 0.0,
                }
            )

        return docs

    def upsert_document(
        self,
        vertical: str,
        doc_id: str,
        title: str,
        text: str,
        category: str = "dynamic_update",
        is_immutable: bool = False,
        ttl_hours: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Dynamically adds or updates an SOP or operational fact in local Qdrant."""
        if not self._is_initialized:
            self.initialize()

        col_name = self._collection_name(vertical)
        if not self.client.collection_exists(col_name):
            self.client.create_collection(
                collection_name=col_name,
                vectors_config=models.VectorParams(size=VECTOR_DIMENSION, distance=models.Distance.COSINE),
            )

        full_text = f"[{vertical.upper()} | {category.upper()}] {title}\n{text}"
        vec = list(self._get_embedder().embed([full_text]))[0].tolist()

        now = time.time()
        expires_at = now + (ttl_hours * 3600.0) if ttl_hours else PERMANENT_EXPIRY_TS

        point_id = abs(hash(doc_id)) % (2**63 - 1)
        payload = {
            "doc_id": doc_id,
            "title": title,
            "text": full_text,
            "raw_text": text,
            "category": category,
            "vertical": vertical,
            "is_immutable": is_immutable,
            "expires_at": expires_at,
            "created_at": now,
            "metadata": metadata or {},
        }

        self.client.upsert(
            collection_name=col_name,
            points=[models.PointStruct(id=point_id, vector=vec, payload=payload)],
        )

        logger.info(f"Upserted document '{doc_id}' into {col_name} (TTL: {ttl_hours}h)")
        return {"status": "success", "doc_id": doc_id, "vertical": vertical, "expires_at": expires_at}

    def delete_document(self, vertical: str, doc_id: str, force: bool = False) -> bool:
        """Deletes a document from the local collection. Immutable SOPs cannot be deleted without force=True."""
        if not self._is_initialized:
            self.initialize()

        col_name = self._collection_name(vertical)
        if not self.client.collection_exists(col_name):
            return False

        point_id = abs(hash(doc_id)) % (2**63 - 1)

        existing = self.client.retrieve(collection_name=col_name, ids=[point_id])
        if existing and existing[0].payload.get("is_immutable") and not force:
            raise ValueError(f"Cannot delete immutable core SOP '{doc_id}' without force=True.")

        self.client.delete(
            collection_name=col_name,
            points_selector=models.PointIdsList(points=[point_id]),
        )
        logger.info(f"Deleted document '{doc_id}' from {col_name}")
        return True

    def list_documents(self, vertical: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Lists active documents in a vertical collection."""
        if not self._is_initialized:
            self.initialize()

        col_name = self._collection_name(vertical)
        if not self.client.collection_exists(col_name):
            return []

        records, _ = self.client.scroll(
            collection_name=col_name,
            limit=limit,
            with_payload=True,
            with_vectors=False,
        )

        docs = []
        now = time.time()
        for r in records:
            p = r.payload or {}
            docs.append(
                {
                    "id": p.get("doc_id", str(r.id)),
                    "title": p.get("title", ""),
                    "category": p.get("category", "general"),
                    "is_immutable": p.get("is_immutable", False),
                    "is_expired": p.get("expires_at", PERMANENT_EXPIRY_TS) <= now,
                    "expires_at": p.get("expires_at", PERMANENT_EXPIRY_TS),
                    "created_at": p.get("created_at", 0),
                    "text_preview": (p.get("raw_text", "")[:120] + "..."),
                }
            )
        return docs


# Global shared engine instance
qdrant_engine = LocalQdrantEngine()
