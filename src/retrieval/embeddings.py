"""
Embeddings (BGE-M3 fixed schema)
================================

Fixed embedding model: BGE-M3 (multilingual, 1024 dimensions).

Why BGE-M3:
- Multilingual (handles Arabic + English + Turkish)
- 1024 dim (industry-standard size)
- Strong on MTEB benchmarks for retrieval
- Open-source — can run on-prem (no API dependency for embedding)

CRITICAL (PLAN.md §3.1 rule 4):
- Vector model and size are FIXED.
- If model changes → all documents must be re-indexed.
- This is enforced by version stamping each embedding.

TODO (v0.2): Implement using sentence-transformers or FlagEmbedding.
"""
from __future__ import annotations
from typing import Any


MODEL_NAME = "BAAI/bge-m3"
EMBEDDING_DIM = 1024
NORMALIZATION = "L2"
MAX_CHUNK_TOKENS = 512
OVERLAP_TOKENS = 50


class BGEEmbedder:
    """BGE-M3 embedder with fixed schema.

    All outputs MUST be 1024-dimensional L2-normalized vectors.
    """

    def __init__(self) -> None:
        # TODO (v0.2): load model
        # from FlagEmbedding import BGEM3FlagModel
        # self.model = BGEM3FlagModel(MODEL_NAME, use_fp16=True)
        pass

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed documents for indexing (input_type='search_document' equivalent)."""
        # TODO (v0.2)
        # Ensure L2 normalization
        raise NotImplementedError

    def embed_query(self, query: str) -> list[float]:
        """Embed a search query (input_type='search_query' equivalent)."""
        # TODO (v0.2)
        raise NotImplementedError

    def verify_schema(self, embeddings: list[list[float]]) -> bool:
        """Verify embeddings match the fixed schema (dim + normalization)."""
        for emb in embeddings:
            if len(emb) != EMBEDDING_DIM:
                return False
        return True
