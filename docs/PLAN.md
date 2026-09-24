# SFDA AI Compliance Agent — Detailed Plan

> Project plan, written to be implementable at engineering level.
> Last updated: 2026-09-24

---

## 1. Overall Architecture and Layered Approach

Four main layers:

| Layer | Responsibility | Output |
|---|---|---|
| **Layer 1: Document Ingest and Standardization** | OCRs/parses uploaded documents, converts them to structured JSON, extracts metadata | Standardized chunks |
| **Layer 2: Fixed Vector Layer and Retrieval** | Embeds chunks with a fixed embedding model, splits them into collections, performs hybrid retrieval | Relevant chunks |
| **Layer 3: Deterministic Agent Graph** | Fixed agent roles managed by a state machine | Classification, validation, checklist |
| **Layer 4: UI and Local Log** | Web UI, Excel logging, process tracking | User interaction, audit trail |

## 2. Fixed Agent Graph (Background Agentization)

The LLM does not choose agents. Whichever agent the state machine specifies is the one that runs. Agent roles, their inputs/outputs and transition conditions are fixed in YAML.

### 2.1 Agent Roles

| Agent | Responsibility | Input | Output | Model Type |
|---|---|---|---|---|
| **Orchestrator** | Manages the state machine, generates user messages | State, Context Packet | Next state, user message | Strong model (optional) |
| **Ingest Agent** | OCRs/parses documents, chunks them, extracts metadata | Uploaded file | Standardized JSON chunks | Rule-based + lightweight LLM |
| **Classifier Agent** | Determines risk class per MDS-G008 + MDS-G5 rules | Intended use, regulatory rules | Class + justification + source | Strong model |
| **Evidence Validator** | Compares user documents against regulatory requirements | Document text, relevant regulatory clause | Compliant / missing / unclear | Mid-tier model |
| **Checklist Agent** | Produces the required document list for the class | Class | Document list + issuing authority | Rule-based |
| **Excel Logger** | Writes every step to the local Excel file | Event data | `.xlsx` update | Tool call |
| **Regulatory Watcher** | Scans the SFDA website, checks for new versions | URL list | New version notification | Lightweight model + diff |

### 2.2 State Machine

```
UPLOAD → INGEST → CLASSIFY → CONFIRM_CLASS → CHECKLIST → COLLECT → VALIDATE → REPORT → DONE
```

Every state has an entry condition, an agent to run, an exit condition and an error (fallback) path.

**Critical:** The LLM is never asked "which agent should I call?". The state machine decides.

## 3. Fixed Vector Layer and Retrieval

### 3.1 Fixed Schema

| Field | Value |
|---|---|
| Embedding model | `BGE-M3` (multilingual, 1024 dimensions) |
| Vector dimension | 1024 (changing the model requires full re-indexing) |
| Normalization | L2 normalize |
| Chunking | Heading + clause number boundaries; max 512 tokens, overlap 50 |
| Collections | `sfda_regulations`, `user_documents`, `templates`, `faq` |
| Metadata | `source_type`, `doc_id`, `section`, `version_date`, `effective_date`, `language` |
| Retrieval | Hybrid: BM25 + vector, top_k=5, filter required |
| Source attribution | Every chunk carries `source_type` and `doc_id` |

### 3.2 Retrieval Rules

- The regulatory rules collection (`sfda_regulations`) and the user documents collection (`user_documents`) **never mix**.
- During classification, search runs only with the `source_type = sfda_regulations` filter.
- User documents are used only as evidence; they can never be a source of rules.
- Every output states which clause of which SFDA document it is based on.

## 4. Large Document Strategy (Beyond 1024k Tokens)

Some documents (especially technical files and clinical evaluation reports) can exceed 1024k tokens.

### Hierarchical Summarization

1. **Structural split:** The document is split by headings, clauses and annexes.
2. **Section summary:** Each section is summarized separately (map step).
3. **Document map:** The summaries form a "document map" (reduce step).
4. **Query-driven retrieval:** Sections relevant to the user's task are found via vector retrieval.
5. **Selective submission:** Only the relevant sections and their summaries are sent to the model.

### Map-Reduce and Refine Chains

- **Map-Reduce:** Processes the whole document piece by piece and merges the results.
- **Refine:** Processes piece by piece, improving the previous result at each step.
- **Sliding Window:** Summarizes long texts by sliding a window across them.

## 5. Context and Attention Mechanism

The full history is not sent on every agent call. A fixed JSON called the **Context Packet** is sent instead:

```json
{
  "step": "CLASSIFY",
  "device_intended_use": "...",
  "retrieved_rules": [
    {"rule_id": "MDS-G008-R1", "text": "...", "source": "MDS-G008", "version": "2023"}
  ],
  "user_evidence": [
    {"doc_id": "IFU-001", "page": 4, "text": "..."}
  ],
  "previous_state": "INGEST"
}
```

This packet focuses the LLM's attention only on the relevant regulatory rule and user evidence. This is how the "lost-in-the-middle" problem is avoided.

## 6. Local Excel Log

No database. The entire process is kept in an `.xlsx` file with 6 sheets: Process, Documents, Classification, Validation, API_Log, Audit.

## 7. Web UI and Model/API Selection

### 7.1 Web UI

- Process dashboard, classification card, document checklist, model selection, Excel download.

### 7.2 Model/API Selection

- Users enter their own API key and can choose a model per agent.
- A `UnifiedLLMClient` supports OpenAI, Anthropic, Gemini and local APIs.

## 8. Current SFDA Regulations

### 8.1 Key Documents

| Document | Description | Version |
|---|---|---|
| **MDS-G5** | Medical Device Listing and Marketing Authorization | v5.0, 22/06/2020 |
| **MDS-G008** | Classification Guidance | Classification rules |
| **MDS-G010** | AI/ML-Enabled Medical Devices | v1.0, 03/01/2023 |
| **MDS-G27** | Digital Health Products Guidance | August 2025 |
| **MDS-REQ9** | Licensing of Medical Devices Establishments | v2, 11/06/2024 |
| **MDS-REQ5** | Importation and Shipments Clearance | v6.0, 19/07/2023 |

### 8.2 Key Requirements

- **MDMA requirement**: Mandatory for every medical device since January 2022.
- **AR requirement**: Foreign manufacturers cannot apply directly; a Saudi-resident Authorized Representative is required.
- **UDI**: As of 2025, 460,745 devices and 1,782 manufacturers are registered.
- **Cybersecurity**: Two separate guidance documents (for healthcare providers and for manufacturers).

## 9. Data Security and Currency Checks

- Automated scanning, version comparison, user notifications, certificate reminders, MDSAP acceptance.

## 10. Technology Stack

| Component | Choice |
|---|---|
| Agent orchestration | LangGraph or a custom Python state machine |
| Vector store | ChromaDB persistent / FAISS + SQLite |
| Embedding | BGE-M3 (fixed) |
| LLM access | UnifiedLLMClient |
| Excel | openpyxl or an MCP Excel server |
| Web | React / Vue / plain HTML+JS |
| Document processing | `unstructured`, `pypdf`, Tesseract OCR |
| Summarization | LangChain `load_summarize_chain` |

## 11. Critical Rules

1. The LLM does not choose agents; the state machine does.
2. The regulatory rules collection and the user documents collection never mix.
3. Every output cites its source; no output is produced without a source.
4. The embedding model and dimension are fixed; changing them requires re-indexing.
5. Excel is the single source of truth for logs; there is no database.
6. Users can change the model; agent roles do not change.
7. Human approval is mandatory for Class C and D.
8. Documents exceeding 1024k tokens are processed with hierarchical summarization + selective retrieval.
