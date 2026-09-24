# Roadmap — SFDA Regulatory Compliance Agent

> Honest roadmap. Updated as the project evolves.

## Current state (v0.1 MVP — September 2026)

### What works
- ✅ Cohere Command R+ with RAG + tool use
- ✅ Grounded citation defense (3-layer hallucination prevention)
- ✅ Sample regulatory corpus (Saudi + UAE + IMDRF)
- ✅ Sample submission package (Canon VITRAE MRI → UAE MoHAP)
- ✅ CLI output (table / JSON / markdown)
- ✅ All planning docs (PLAN.md, BEHAVIOR_AND_ATTENTION.md, architecture.md)

### What's honest
- Single-step flow (no state machine yet)
- Single jurisdiction (UAE MoHAP in MVP — Saudi SFDA will be first real target)
- In-memory cosine (no ChromaDB persistent)
- No Excel audit log (no hash chain)
- No Regulatory Watcher
- No Arabic NLP pipeline
- No web UI (CLI only)
- No tests

## v0.2 — State Machine + Excel Audit
**Target: 2 weeks**

### Must-do
- [ ] Implement state machine (`src/state_machine.py`) — YAML-driven
- [ ] Replace inline flow in `main.py` with state machine dispatch
- [ ] Implement Excel logger with hash chain (`src/agents/excel_logger.py`)
- [ ] Implement 7 agent stubs (real implementations, not stubs):
  - [ ] Orchestrator (user messaging + transition logic)
  - [ ] Ingest (pypdf + python-docx + Tesseract)
  - [ ] Classifier (MDS-G008 prompt template + LLM call)
  - [ ] Evidence Validator (clause-level validation with L3 defense)
  - [ ] Checklist (rule-based, already in stub)
  - [ ] Excel Logger (openpyxl + hash chain)
- [ ] Add Streamlit web UI (basic: upload + checklist + report)
- [ ] Add 5 document types (IFU, Technical File, Risk Management File, QMS Certificate, AR Letter)

### Should-do
- [ ] Real Saudi FDA regulatory corpus (replace synthetic samples with actual MDS-G5, MDS-G008, MDS-G010, MDS-G27, MDS-REQ9, MDS-REQ5 excerpts — license + permission required)
- [ ] ChromaDB persistent vector store (replace in-memory)
- [ ] BGE-M3 embedder (replace Cohere Embed v3)
- [ ] Cohere Rerank v3 wrapper
- [ ] Tests for classifier + evidence validator (mock LLM)

## v0.3 — Regulatory Watcher + Audit Hardening
**Target: +2 weeks**

- [ ] Implement Regulatory Watcher (SFDA site scanning, weekly)
- [ ] Version snapshot capture at CLASSIFY state
- [ ] Trigger re-validation of past decisions when regulator updates
- [ ] Hash chain audit validator (`src/utils/audit.py`)
- [ ] Pre-submission meeting recommendation (Class C/D)
- [ ] Periodic safety update reminders (PSUR)
- [ ] Multi-jurisdiction flag (PLAN.md §A15) — Saudi + UAE + Turkey

## v1.0 — Production
**Target: +4 weeks**

- [ ] Arabic NLP pipeline (CAMeL Tools for RTL + tokenization)
- [ ] LangGraph migration (special state machine → LangGraph)
- [ ] SSO (Keycloak) for multi-user access
- [ ] Rate limiting + DLP (data loss prevention)
- [ ] Monitoring (Grafana + alerting on agent failures)
- [ ] Documentation for regulator-facing audit (the auditor reads this)
- [ ] Customer onboarding flow (first customer)

## What I will NOT do (honest scoping)

- ❌ Pretend this is production-grade before it is
- ❌ Add features that look impressive but aren't tested
- ❌ Submit a CV that claims more than this repo proves
- ❌ Use real customer data without explicit consent
- ❌ Bypass regulatory version locking (every decision must be version-stamped)

## Why this roadmap is public

1. **Customer credibility** — if I'm asking SFDA submitters to trust this agent, transparency matters
2. **Self-discipline** — public commitments are harder to break
3. **Hiring signal** — recruiters can see exactly where I am, no overselling

## v1.0 success criteria

This project is "v1.0" when:
- [ ] A regulatory affairs team uses it for a real SFDA submission
- [ ] The agent catches at least one issue that the team missed
- [ ] The submission is accepted by SFDA on first review (or with minimal back-and-forth)
- [ ] The audit trail is verified by an independent party
- [ ] The team reports time savings vs their previous manual workflow

Until those happen, it's pre-1.0.
