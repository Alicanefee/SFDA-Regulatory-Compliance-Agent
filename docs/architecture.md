# Architecture — SFDA Regulatory Compliance Agent

> Detailed technical architecture. See [PLAN.md](PLAN.md) for the full project plan.

## System diagram (4-layer)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Layer 4: UI + Excel Log                                                 │
│  ┌──────────────────────────┐  ┌──────────────────────────┐             │
│  │  Streamlit Web UI         │  │  Excel Logger (hash chain)│             │
│  │  - Upload files           │  │  - 6 sheets              │             │
│  │  - View checklist         │  │  - Audit trail            │             │
│  │  - Confirm classification │  │  - Hash chain integrity   │             │
│  └──────────────────────────┘  └──────────────────────────┘             │
├─────────────────────────────────────────────────────────────────────────┤
│  Layer 3: Deterministic Agent Graph (state machine)                     │
│  ┌──────────────────────────────────────────────────────────┐             │
│  │  State machine (YAML-driven) — LLM does not pick agents  │             │
│  │  UPLOAD→INGEST→CLASSIFY→CONFIRM→CHECKLIST→COLLECT         │             │
│  │  →VALIDATE→REPORT→DONE                                   │             │
│  └──┬──────────────────────────────────────────────────────┘             │
│     │ dispatches to                                                       │
│     ▼                                                                     │
│  7 agent roles: Orchestrator | Ingest | Classifier | Evidence Validator │
│                 Checklist | Excel Logger | Regulatory Watcher            │
├─────────────────────────────────────────────────────────────────────────┤
│  Layer 2: Fixed Vector Layer + Hybrid Retrieval                         │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐       │
│  │  BGE-M3 (fixed)  │  │  BM25 (keyword)  │  │  Cohere Rerank   │       │
│  │  1024 dim, L2    │  │  Arabic-aware    │  │  v3 (precision)  │       │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘       │
│       │                       │                       │                  │
│       └───────────────────────┴───────────────────────┘                  │
│                              ▼                                            │
│  Collections: sfda_regulations | user_documents | templates | faq       │
│  (CRITICAL: sfda_regulations and user_documents MUST NOT mix)            │
├─────────────────────────────────────────────────────────────────────────┤
│  Layer 1: Document Ingest + Standardization                            │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐     │
│  │  pypdf           │  │  python-docx     │  │  Tesseract OCR    │     │
│  │  (PDF parsing)   │  │  (DOCX parsing)  │  │  (image OCR)      │     │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘     │
│       → Standard JSON chunks with metadata                              │
└─────────────────────────────────────────────────────────────────────────┘
```

## Component detail

### Layer 1: Document Ingest

**Input**: PDF, DOCX, image, plain text
**Output**: List of standardized chunks:
```json
{
  "chunk_id": "string",
  "doc_id": "string",
  "source_file": "filename.pdf",
  "section": "5.1",
  "language": "en|ar|mixed",
  "page": 4,
  "text": "...",
  "version_date": "2023-01-03",
  "tokens": 350
}
```

**Chunking strategy**:
- Split by heading + clause number (NOT just by token count)
- Max 512 tokens per chunk
- 50 token overlap between adjacent chunks
- For Arabic: detect RTL direction, may need different chunking

### Layer 2: Fixed Vector Layer + Hybrid Retrieval

**Fixed schema** (cannot change without re-indexing everything):
- Embedding model: BGE-M3 (multilingual, 1024 dim)
- Normalization: L2
- Chunk size: max 512 tokens, overlap 50

**4 collections** (see PLAN.md §3.1):
| Collection | Purpose | Used as rule source? |
|---|---|---|
| `sfda_regulations` | Saudi SFDA official documents | ✅ YES (only this one) |
| `user_documents` | User's submission documents | ❌ NO (evidence only) |
| `templates` | Document templates (IFU, technical file) | ❌ NO (reference) |
| `faq` | Common questions + answers | ❌ NO (reference) |

**Hybrid retrieval** (PLAN.md §3.1):
1. BM25 keyword retrieval → top 15
2. Vector (BGE-M3) retrieval → top 15
3. Merge + deduplicate → ~20 candidates
4. Cohere Rerank v3 → top 5

**Critical rule** (PLAN.md §3.2): `sfda_regulations` and `user_documents` collections **MUST NOT mix** in retrieval. When classifying, only retrieve from `sfda_regulations`. When validating evidence, retrieve from both — but only as rule + evidence, never as combined.

### Layer 3: Deterministic Agent Graph

**State machine** (YAML-driven, see `data/state_machine.yaml`):
- 9 states + 1 fallback (MANUAL_REVIEW)
- Each state has: entry_condition, agent, input, output, next, on_error
- Loops (CONFIRM_CLASS, COLLECT) have max_loops to prevent infinite cycling
- LLM does NOT pick which agent to call — the state machine does

**7 agent roles** (see `src/agents/` for stubs):
1. **Orchestrator** — state machine + user communication
2. **Ingest** — document parsing + chunking
3. **Classifier** — MDS-G008 risk class detection
4. **Evidence Validator** — clause-level compliance validation
5. **Checklist** — per-class document list (rule-based, no LLM)
6. **Excel Logger** — hash chain audit trail
7. **Regulatory Watcher** — SFDA site scanning for new versions

### Layer 4: UI + Excel Log

**Streamlit web UI**:
- File upload
- State progress dashboard
- Classification card (with rule_id citation)
- Document checklist (per class)
- Findings report (P0/P1/P2/P3 grouped)
- Excel download

**Excel logger** (6 sheets):
1. Process: timestamp, step, status, agent, duration, prev_hash, this_hash
2. Documents: doc_id, name, type, upload_date, status, source_authority
3. Classification: device_name, intended_use, class, rule_id, justification, version_snapshot
4. Validation: doc_id, requirement, result, missing_items, notes, prev_hash, this_hash
5. API_Log: timestamp, agent, model, tokens, cost, latency
6. Audit: hash_chain_verification results

**Hash chain** (BEHAVIOR_AND_ATTENTION.md §A2):
- `this_hash = sha256(prev_hash + row_content + timestamp)`
- First row: `prev_hash = "GENESIS"`
- Inspector can run `audit.py` to verify chain integrity
- Any tampering → mismatch detected

## Defense layers (hallucination prevention)

| Layer | What it does | Failure mode it prevents |
|---|---|---|
| L1 Preamble constraint | LLM told "only cite clauses from retrieved_rules" | Casual hallucination |
| L2 Tool use for lookup | LLM must call `lookup_clause(clause_id)` before citing | Mid-level fabrication |
| L3 Post-process validator | Drops any cited_clause not in retrieved_rules | Even if LLM ignores preamble |
| L4 Hash chain audit | Every decision logged with prev_hash → tamper-evident | Post-hoc modification |
| L5 Version snapshot | Every decision records which MDS-Gxxx version was used | Stale decisions after regulator updates |

## Big document strategy (PLAN.md §4)

For documents > 1024k tokens (technical files, clinical evaluation reports):

1. **Structural split**: by heading + clause + appendix
2. **Per-section summary** (map step): each section summarized separately
3. **Document map** (reduce step): summaries combined into a doc map
4. **Query-driven retrieval**: only relevant sections + their summaries sent to LLM
5. **Never send the full document to the LLM**

Tools: LangChain `load_summarize_chain` (map_reduce, refine), sliding window.

## Anticipated failure modes

| Failure | Mitigation |
|---|---|
| LLM hallucinates clause ID | L3 post-process validator drops the citation |
| Excel file locked by user | Retry with 5s backoff; if persistent → switch to temp file |
| Cohere API timeout | Retry with exponential backoff (max 3 retries) |
| Empty submission package | Early exit with help message |
| Arabic text parsed as Latin | RTL detection in Ingest agent, flag for re-OCR |
| Vector store corruption | Backup daily; restore from last known good |
| State machine infinite loop | max_loops = 3 for COLLECT, max_loops = 1 for CONFIRM_CLASS |
| Regulatory version changes mid-submission | version_snapshot captured at CLASSIFY, never updated mid-flow |
| User uploads wrong file type | Ingest agent validates MIME type, rejects with helpful error |

## Production upgrade path

| Current (v0.1 MVP) | Production (v1.0) |
|---|---|
| Cohere Command R+ only | UnifiedLLMClient (Cohere + OpenAI + Anthropic + Gemini + local) |
| Single jurisdiction (UAE MoHAP in MVP) | Multi-jurisdiction (Saudi + UAE + Turkey) |
| In-memory retrieval | ChromaDB persistent |
| CLI only | Streamlit web UI |
| No state machine | YAML-driven state machine |
| No Excel log | Excel + hash chain audit |
| No Regulatory Watcher | Scheduled SFDA site scanning |
| No Arabic NLP | CAMeL Tools + RTL detection |
| No auth | Keycloak SSO |
| No monitoring | Grafana + alerting |
