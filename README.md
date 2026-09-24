# SFDA Regulatory Compliance Agent

> **Saudi FDA (SFDA) regulatory pre-check AI agent** for medical device submissions.
> Detects missing documents, format issues, and regulatory language gaps BEFORE submission — saving 2-3 months of regulator back-and-forth.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Status: v0.1.0 MVP](https://img.shields.io/badge/status-v0.1.0%20MVP-orange.svg)](docs/roadmap.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> ⚠️ **For demonstration and testing purposes only.** The regulatory corpus is synthetic and the sample submission is fictional. The output is not legal or regulatory advice and not a regulatory clearance. **All legal and regulatory obligations arising from use of this software remain solely with the user.** See [DISCLAIMER.md](DISCLAIMER.md).

**Author**: Ali Can Efe — Dubai, UAE

---

## 🎯 What this is

A deterministic AI agent that scans medical-device submission packages against the Saudi SFDA regulatory corpus and flags issues before submission. Designed for **medical device manufacturers** and **regulatory affairs teams** who submit to SFDA.

**Why this exists**: A single missing form, an unverified Arabic translation, or a clinical evaluation report citing the wrong MEDDEV revision can mean **2-3 months of delay** with the regulator. This agent catches those issues before submission.

## 🏗️ Architecture (4-layer)

```
┌─────────────────────────────────────────────────────────────────┐
│  Layer 4: UI + Excel Log                                        │  ← Streamlit + openpyxl (hash chain)
├─────────────────────────────────────────────────────────────────┤
│  Layer 3: Deterministic Agent Graph (state machine)             │  ← YAML-driven, LLM does not pick agents
├─────────────────────────────────────────────────────────────────┤
│  Layer 2: Fixed Vector Layer + Hybrid Retrieval                │  ← BGE-M3 + BM25 + Cohere Rerank
├─────────────────────────────────────────────────────────────────┤
│  Layer 1: Document Ingest + Standardization                    │  ← unstructured + pypdf + Tesseract
└─────────────────────────────────────────────────────────────────┘
```

📖 **Full plan**: [`docs/PLAN.md`](docs/PLAN.md) (4-layer architecture, 7 agent roles, state machine, fixed vector schema, big-document strategy, Excel log sheets, current SFDA regulations)

📖 **Behavior & Attention**: [`docs/BEHAVIOR_AND_ATTENTION.md`](docs/BEHAVIOR_AND_ATTENTION.md) (15 refinements, 10 behavior rules, 30-item attention priority list P0-P3, 4-phase implementation)

📖 **Architecture**: [`docs/architecture.md`](docs/architecture.md) (defense layers, failure modes, production upgrade path)

📖 **Roadmap**: [`docs/roadmap.md`](docs/roadmap.md) (v0.1 MVP → v1.0 production)

## 🤖 7 Agent Roles

| Agent | Role | Status |
|---|---|---|
| **Orchestrator** | Manages state machine, generates user messages | 🚧 stub |
| **Ingest Agent** | OCR/parse, chunk, extract metadata | 🚧 stub |
| **Classifier Agent** | MDS-G008 + MDS-G5 risk class detection | 🚧 stub |
| **Evidence Validator** | Clause-level compliance validation | 🚧 stub |
| **Checklist Agent** | Per-class document list | 🚧 stub |
| **Excel Logger** | Hash-chain audit trail to .xlsx | 🚧 stub |
| **Regulatory Watcher** | SFDA site scanning, version diffs | 🚧 stub |

State machine (YAML-driven):
```
UPLOAD → INGEST → CLASSIFY → CONFIRM_CLASS → CHECKLIST → COLLECT → VALIDATE → REPORT → DONE
```

## 🚀 Quick start (v0.1 MVP — currently minimal)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set your Cohere API key (free trial at https://cohere.com)
cp .env.example .env
# Edit .env and add COHERE_API_KEY

# 3. Run the MVP pre-check (currently uses Cohere Command R+)
cd src
python main.py --submission ../data/sample_submission/sample_package.json
```

Expected output on the sample submission (example MRI system → UAE MoHAP):
- 🔴 Critical: Labelling Arabic missing
- 🔴 Critical: IFU Arabic is machine-translated (must be certified)
- 🔴 Critical: Cybersecurity documentation missing
- 🟡 Warning: PMS System documentation missing
- 🟡 Warning: Data protection compliance statement missing

## 📊 Current state

- **Status**: v0.1 MVP — single-jurisdiction pre-check, basic RAG + tool use
- **What works**: Cohere Command R+ with RAG + tool use + grounded citation defense (3-layer hallucination prevention)
- **What's stubbed**: all 7 agent modules in `src/agents/` (the MVP validation flow lives in `src/main.py`), state machine dispatcher, Excel hash chain, Regulatory Watcher
- **What's missing**: Arabic NLP pipeline, multi-jurisdiction support, web UI, audit hardening

See [`docs/roadmap.md`](docs/roadmap.md) for full v0.1 → v1.0 plan.

## 🗂️ Repository layout

```
SFDA-Regulatory-Compliance-Agent/
├── README.md                          ← this file
├── LICENSE                            ← MIT
├── DISCLAIMER.md                      ← Demonstration-only terms and user responsibility
├── requirements.txt
├── .env.example
├── .gitignore
│
├── docs/
│   ├── PLAN.md                        ← Project plan (architecture, agents, SFDA regulations)
│   ├── BEHAVIOR_AND_ATTENTION.md     ← Refinements, behavior rules, attention priorities
│   ├── architecture.md                ← Detailed architecture
│   └── roadmap.md                     ← v0.1 → v1.0 roadmap
│
├── src/
│   ├── main.py                        ← v0.1 MVP entry point (Cohere agent)
│   ├── state_machine.py               ← TODO: YAML-driven state transitions
│   ├── context_packet.py              ← TODO: Context packet builder
│   ├── agents/                        ← 7 agent role stubs
│   │   ├── orchestrator.py
│   │   ├── ingest.py
│   │   ├── classifier.py
│   │   ├── checklist.py
│   │   ├── evidence_validator.py
│   │   ├── excel_logger.py
│   │   └── regulatory_watcher.py
│   ├── retrieval/
│   │   ├── vector_store.py            ← ChromaDB wrapper (TODO)
│   │   ├── embeddings.py              ← BGE-M3 wrapper (fixed schema, TODO)
│   │   └── rerank.py                  ← Cohere Rerank wrapper (TODO)
│   ├── prompts/
│   │   ├── classifier.md
│   │   ├── evidence_validator.md
│   │   └── orchestrator.md
│   └── utils/
│       ├── excel_writer.py            ← openpyxl + hash chain (TODO)
│       ├── audit.py                   ← Hash chain validator (TODO)
│       └── config.py
│
├── data/
│   ├── regulatory_corpus/             ← Saudi + UAE + IMDRF sample clauses
│   │   ├── saudi_fda_requirements.txt
│   │   ├── uae_mohap_requirements.txt
│   │   └── imdrf_requirements.txt
│   ├── sample_submission/
│   │   └── sample_package.json        ← Test case (example MRI system → UAE MoHAP)
│   └── state_machine.yaml             ← State machine definition (TODO)
│
├── notebooks/
│   └── demo_walkthrough.ipynb         ← TODO: End-to-end demo notebook
│
└── tests/
    └── __init__.py
```

## ⚠️ Disclaimers

- **This project is for demonstration and testing purposes only.** It must not be used for real medical device submissions or compliance decisions.
- Sample regulatory clauses in `data/regulatory_corpus/` are **synthetic** — written for demonstration only, they do NOT represent official SFDA regulatory text
- The sample submission in `data/sample_submission/` is **fictional**; names are used for illustration only
- This agent does NOT provide legal or regulatory advice, and its output is not a regulatory clearance
- **The user is solely responsible** for verifying requirements with the authority and for **all legal and regulatory obligations** arising from use of this software or decisions based on its output
- The author accepts no liability for any loss, rejection, delay or other consequence arising from its use
- This is **independent R&D**, not affiliated with or endorsed by SFDA or any other authority
- For actual regulatory compliance work, always consult official SFDA sources and a licensed regulatory affairs professional

Full terms: [DISCLAIMER.md](DISCLAIMER.md).

## 👤 Author

**Ali Can Efe** — biomedical engineer with 10 years in medical imaging (MRI product management, META region; regulatory and compliance work for AI-enabled imaging). Based in Dubai, UAE.
