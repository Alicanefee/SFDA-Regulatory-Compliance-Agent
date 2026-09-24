"""
Agent: Ingest
=============

Role: Document ingestion + standardization.

Input: Uploaded file (PDF, DOCX, image, etc.)
Output: Standard JSON chunks with metadata

Pipeline:
1. Detect file type
2. Extract text (pypdf / python-docx / Tesseract OCR)
3. Detect language (en / ar / mixed)
4. Chunk by heading + clause number (max 512 tokens, overlap 50)
5. Extract metadata: source_file, doc_id, section, version_date, language
6. Output: list[chunk_dict]

Tools: `unstructured`, `pypdf`, `python-docx`, `pytesseract`

TODO (v0.2): Implement.
"""
from __future__ import annotations
from typing import Any


class IngestAgent:
    """Ingests uploaded documents and outputs standardized chunks.

    Output schema (per chunk):
        {
          "chunk_id": str,
          "doc_id": str,
          "source_file": str,
          "section": str,
          "language": "en" | "ar" | "mixed",
          "page": int,
          "text": str,
          "version_date": str,  # if detectable from doc
          "tokens": int
        }
    """

    def __init__(self) -> None:
        pass

    def ingest(self, file_path: str) -> list[dict]:
        """Ingest a file and return standardized chunks."""
        # TODO (v0.2): implement
        # - file type detection
        # - text extraction (PDF, DOCX, image OCR)
        # - language detection
        # - chunking with heading + clause-number boundaries
        # - metadata extraction
        raise NotImplementedError

    def chunk_by_structure(self, text: str, max_tokens: int = 512, overlap: int = 50) -> list[str]:
        """Chunk by heading + clause number (not just by token count)."""
        # TODO (v0.2)
        raise NotImplementedError
