"""
Vector Store (ChromaDB wrapper)
================================

Persistent vector store using ChromaDB. Stores document chunks + embeddings.

Fixed schema (see PLAN.md §3.1):
- Embedding model: BGE-M3 (multilingual, 1024 dim)
- Vector size: 1024 (must re-index if model changes)
- Normalization: L2
- Chunking: max 512 tokens, overlap 50, by heading + clause number
- Collections: sfda_regulations, user_documents, templates, faq
- Metadata: source_type, doc_id, section, version_date, effective_date, language

CRITICAL RULE (see PLAN.md §3.2):
- sfda_regulations collection is the ONLY source of regulatory rules
- user_documents collection is for evidence only — NEVER used as rule source
- These collections MUST NOT mix in retrieval

TODO (v0.2): Implement ChromaDB persistent backend.
"""
from __future__ import annotations
from typing import Any


# Collections (must not mix in retrieval)
COLLECTION_SFDA = "sfda_regulations"
COLLECTION_USER_DOCS = "user_documents"
COLLECTION_TEMPLATES = "templates"
COLLECTION_FAQ = "faq"


class VectorStore:
    """ChromaDB persistent vector store with fixed schema."""

    def __init__(self, persist_dir: str = "./chroma_db") -> None:
        self.persist_dir = persist_dir
        # TODO (v0.2): initialize ChromaDB client
        # import chromadb
        # self.client = chromadb.PersistentClient(path=persist_dir)

    def add_documents(
        self,
        collection: str,
        documents: list[dict],  # each has: chunk_id, text, metadata, embedding
    ) -> None:
        """Add documents to a collection."""
        # TODO (v0.2): implement with proper embedding model
        raise NotImplementedError

    def retrieve(
        self,
        collection: str,
        query: str,
        top_k: int = 5,
        filter_metadata: dict | None = None,
    ) -> list[dict]:
        """Retrieve top-k chunks from a collection.

        Args:
            collection: must be one of COLLECTION_* constants
            query: search query text
            top_k: number of results
            filter_metadata: ChromaDB metadata filter (e.g. {"source_type": "sfda_regulations"})

        Returns:
            List of chunks with scores.
        """
        # TODO (v0.2)
        raise NotImplementedError

    def hybrid_retrieve(
        self,
        collection: str,
        query: str,
        top_k: int = 5,
    ) -> list[dict]:
        """Hybrid retrieval: BM25 (keyword) + vector (semantic).

        Over-retrieve top 3x, then rerank with Cohere Rerank.
        See PLAN.md §3.1 (Hybrid: BM25 + vector, top_k=5, filter required).
        """
        # TODO (v0.2): implement
        # 1. BM25 keyword retrieval → top 15
        # 2. Vector retrieval → top 15
        # 3. Merge + deduplicate
        # 4. Pass to Rerank (see rerank.py)
        raise NotImplementedError
