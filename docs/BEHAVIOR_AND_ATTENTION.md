# SFDA AI Compliance Agent — Behavior, Attention and Refinements

> This document complements [`PLAN.md`](PLAN.md) with: (1) agent behavior/identity, (2) an attention priority list, and (3) 15 critical refinements to the plan.

---

## PART A — 15 Critical Refinements to the Plan

These items make the plan's architecture more robust without changing it.

### A1. Version Lock — Critical

Whenever a decision is made, a **version snapshot** of the SFDA documents in force at that moment must be recorded. The following columns should be added to the Excel `Classification` sheet:

```
mds_g5_version | mds_g008_version | mds_g010_version | mds_g27_version | decision_date
```

If MDS-G010 v2.0 is published six months later, **earlier decisions must still be shown as based on v1.0**. When an auditor asks "What is this decision based on?", the answer is: v1.0 (3 January 2023, in force at the time).

### A2. Audit Trail Integrity — Hash Chain

An Excel file is easy to modify, and an auditor cannot prove it has not been changed. Solution:

- Every log row contains `prev_hash` and `this_hash`
- `this_hash = sha256(prev_hash + row_content + timestamp)`
- The first row has `prev_hash = "GENESIS"`
- During an inspection, a separate script verifies the hash chain

```python
# Audit trail integrity — every row carries a hash
def log_event(event):
    prev_hash = get_last_hash()
    row_content = json.dumps(event, sort_keys=True)
    timestamp = datetime.now().isoformat()
    this_hash = sha256(f"{prev_hash}{row_content}{timestamp}".encode()).hexdigest()
    write_to_excel(event + {"prev_hash": prev_hash, "this_hash": this_hash})
```

Without this, the Excel log is an "editable document" and its legal weight is limited.

### A3. Hallucination Defense Specification

The plan requires source attribution but does not define the mechanism. Three-layer defense:

| Layer | What it does | What it prevents |
|---|---|---|
| **L1 Preamble constraint** | Instructs the LLM to "only cite rule_ids present in retrieved_rules" | Casual hallucination |
| **L2 Tool-based lookup** | The LLM cannot cite a clause without calling the `lookup_rule(rule_id)` tool to verify its text | Mid-level fabrication |
| **L3 Post-process validator** | Checks that every `rule_id` the LLM produced exists in the actual retrieved_rules list; otherwise the finding is dropped and marked "unverified" | Cases where the LLM ignores the preamble |

A simplified version of this defense is implemented in the v0.1 MVP (`src/main.py`); the same structure will be carried over to the agent modules.

### A4. Class Change Cascade

If the user changes the classification (B → C), the checklist changes completely. In the CLASSIFY → CONFIRM_CLASS → CHECKLIST flow, a "no" answer at CONFIRM_CLASS must return to CLASSIFY.

**Loop guard**: at most 1 return. On the second return → fall back to the MANUAL_REVIEW state.

### A5. UDI DI vs PI Distinction

UDI is not a single concept — it consists of two segments:

- **DI (Device Identifier)**: manufacturer + product code. Must be on the package.
- **PI (Production Identifier)**: lot, serial number, manufacturing date, expiry date. Must be on the device.

The checklist should include:
- Is the DI on the package label?
- Is the PI on the device label?
- Is the DI format GS1 or HIBC compliant?
- Has the device been registered in the GUDID database?
- Does the PI use expiry date, lot, or both?

### A6. AR License Verification

The plan mentions the AR requirement, but the checklist needs an **"Is the AR license valid?"** item. SFDA provides an ARL lookup tool: https://www.sfda.gov.sa/en/medical-devices/registered

The agent should scan this URL periodically and warn "This AR's license has expired".

### A7. Arabic IFU Translation Verification Mechanics

The language requirements are mentioned, but the following mechanical checks are needed:

1. **RTL detection**: Is the Arabic IFU actually right-to-left (character-range check)?
2. **Medical terminology suitability**: Was a certified Arabic medical translator used (request proof)?
3. **Cross-consistency with English**: Is the same procedure described in both EN and AR?

```python
def verify_arabic_ifu(ar_text, en_text):
    # 1. RTL check
    if not is_rtl_dominant(ar_text):
        return Finding(severity='critical', msg='Arabic IFU appears to be Latin-script')
    # 2. Translation certificate
    if not has_translator_certificate(ar_text):
        return Finding(severity='critical', msg='No certified Arabic medical translator stamp')
    # 3. Cross-language consistency
    return cross_validate_sections(ar_text, en_text)
```

### A8. Pre-submission Meeting Recommendation

SFDA recommends a pre-submission meeting for Class C/D devices. The checklist should include:

> "A pre-submission meeting with SFDA is recommended for Class C/D devices. Submit the request form via sfda.gov.sa. Average response time: 4-6 weeks."

The agent should automatically flag this as a "recommended action" — not critical, but high value.

### A9. CER (Clinical Evaluation Report) Depth by Class

The plan says "a CER is required", but the required depth varies by class:

| Class | CER depth | Minimum requirement |
|---|---|---|
| **A** | Usually not required | (literature review only is sufficient) |
| **B** | Equivalence justification | Predicate device + literature review |
| **C** | Clinical data + literature | MEDDEV 2.7/1 rev.4 methodology |
| **D** | Clinical investigation + PMCF | Full CER + PMCF plan |

The Classifier must distinguish between these.

### A10. PSUR (Periodic Safety Update Report) Frequency

| Class | Frequency |
|---|---|
| **A** | Annual |
| **B** | Annual for the first 2 years, then every 2 years |
| **C** | Annual for the first 2 years, then every 2 years |
| **D** | Annual |

The checklist's "Is there a PSUR plan?" item should ask different questions depending on class.

### A11. Risk Management File Depth (ISO 14971:2019)

Mandatory for all classes, but depth differs:

- **Class A**: Basic hazard analysis
- **Class B**: Full risk management file + residual risk assessment
- **Class C/D**: Full RMF + benefit-risk analysis + post-production information

### A12. Cybersecurity Documentation by Class

The plan mentions cybersecurity, but depth depends on class:

| Class | Cybersecurity requirement |
|---|---|
| **A** (non-connected) | Usually none |
| **B** (connected) | IEC 81001-5-1 self-attestation |
| **C** (connected) | Threat model + SBOM + IEC 81001-5-1 |
| **D** (connected) | Full penetration test report + SBOM + threat model + IEC 81001-5-1 |

### A13. Change Notification (Post-Market)

If a device changes after MDMA is granted, a "change notification" to SFDA is required. The agent should track the post-market phase as well — not only pre-submission.

Change types:
- **Notable change** (new risk) → requires SFDA approval
- **Non-notable change** (form change) → notification only
- **Administrative change** (company name) → log only

### A14. Post-Market Vigilance Reporting Timelines

| Event | Timeline | Recipient |
|---|---|---|
| Adverse event (death/serious injury) | 10 days | SFDA |
| Field Safety Corrective Action (FSCA) | 5 days | SFDA |
| Trend report | Quarterly (Class C/D) | SFDA |
| PSUR | By class (A10) | SFDA |

The agent should set up reminder alerts.

### A15. Multi-Jurisdiction Flag

If a device is going to Saudi Arabia + UAE + Turkey, each jurisdiction needs a **separate checklist**. The plan is currently Saudi-focused, but the agent should support a "multi-jurisdiction mode".

```python
class Jurisdiction(Enum):
    SAUDI = "sfda"
    UAE = "mohap"
    TURKEY = "titck"

# Cross-jurisdiction flag
if submission.jurisdictions_count > 1:
    checklist = build_unified_checklist(submission.jurisdictions)
    # → mark each item as "common" vs "specific"
```

---

## PART B — Agent Behavior and Identity

> The agent is not just a function; it has a character. An auditor reading its report should conclude that "this agent is careful, consistent and reliable".

### B1. Persona

The agent should act as a **"resident regulatory assistant"**:

- **Consistent**: Same input → same output (temperature=0)
- **Unembellished**: No words like "great", "excellent", "perfect". Only finding + source + recommendation.
- **Concise**: One finding = max 2 sentences. Long explanations tire auditors.
- **Quantitative**: Instead of "missing", say "3 items missing (SFDA-MDS-G008-R5.2, R5.3, R5.7)".
- **Sourced**: Every finding carries `rule_id` + `doc_id` + `page`.

### B2. Behavior Rules

| # | Rule | Rationale |
|---|---|---|
| 1 | **Know when to say "I don't know"** | In borderline cases, "cannot decide — human review" is better than a wrong decision |
| 2 | **Conservative by design** | For borderline B/C, choose C. Aligned with SFDA's safety-first approach |
| 3 | **Pre-check citations** | Do not return output without verifying that every returned `rule_id` actually exists in retrieved_rules |
| 4 | **Time-aware** | Evaluate against the decision date (e.g. as of 2026-09-24: MDS-G27 (Aug 2025) → in effect; MDS-G010 v2 not published → v1.0 still valid). When a new version is released → "review earlier decisions" warning |
| 5 | **Mandatory disclaimer** | Every output must state: "This agent does not provide official SFDA advice; consult SFDA for official approval" |
| 6 | **Audit-ready** | Every decision must be able to answer "What is this based on?" (hash chain + version snapshot) |
| 7 | **Reverse-check translation** | Arabic and English documents must yield the same findings. Consistency test |
| 8 | **Lexical vs semantic distinction** | "ISO 13485" → exact match (lexical). "Clinical evaluation" → semantic. Never mix the two |
| 9 | **No silent fallback** | If an agent fails, show the user: "Classifier agent LLM error — falling back to MANUAL_REVIEW" |
| 10 | **One finding = one source** | A finding must rest on a single rule source. "Based on two rules" = two separate findings |

### B3. Communication Templates

The agent should communicate with the user as follows:

**After classification (CONFIRM_CLASS):**
```
[Classification Result]
Device: Canon VITRAE MRI System (1.5T)
Intended use: Diagnostic imaging via magnetic resonance
Risk class: **C** (per MDS-G008, Rule 13 — diagnostic imaging with non-ionizing radiation)

Cited clause: MDS-G008 §13.2
Justification: "Active diagnostic devices using non-ionizing radiation for diagnosis 
fall under Class C unless they are intended for monitoring of vital physiological 
parameters where the nature of variations could result in immediate danger."

Confirm class? [Yes / No (re-classify) / Manual review]
```

**After validation (REPORT):**
```
[Validation Findings — Class C submission]

🔴 Critical (2):
  1. Cybersecurity documentation missing (MDS-G27 §4.2)
     Source: MDS-G27, page 14, clause 4.2.1
     Suggested fix: Prepare threat model + SBOM per IEC 81001-5-1
     
  2. Arabic IFU not certified-translator stamped (MDS-G5 §6.1)
     Source: MDS-G5, page 22, clause 6.1.3
     Suggested fix: Engage certified Arabic medical translator; stamp + sign

🟡 Warning (1):
  3. Risk management file incomplete (ISO 14971 §5.4)
     Source: ISO 14971:2019, clause 5.4
     Suggested fix: Add benefit-risk analysis section (Class C requirement)

🔵 Info (1):
  4. Pre-submission meeting recommended for Class C devices
     Source: SFDA MDMA process overview, step 3
     Suggested fix: Submit pre-submission request via sfda.gov.sa

Audit hash: 7f3a9b...e4c2 (chain verification OK)
Version snapshot: MDS-G5 v5.0 / MDS-G008 (current) / MDS-G27 Aug 2025
```

### B4. Silent Failure Modes (to avoid)

Behaviors the agent must never fall into:

| Bad behavior | Why it is bad | Correct behavior |
|---|---|---|
| Writing "no findings" and moving on | It may simply be wrong | "No gaps detected against the retrieved rules; this does not imply compliance. Human review recommended" |
| Writing multiple findings on a single line | Hard for auditors to trace | Each finding on its own line, with its own source |
| Giving recommendations without a source | Auditors cannot verify them | "Pre-submission meeting recommended (source: SFDA MDMA Process Overview, step 3)" |
| Guessing under uncertainty | Wrong class = 6-month delay | "Classification of this device is ambiguous — between MDS-G008 §13 and §14. Sent to human review" |
| Responding in a language other than English | Audits are conducted in English | All output in English (auditors generally read English) |
| Silently overwriting a previous finding | Legally risky | New finding + "Previous finding #X superseded" marker |

### B5. Version Management Behavior

SFDA documents change over time. How the agent behaves as they do:

```
T0 (2026-09-24): MDS-G010 v1.0 (current)
T1 (2027-03-01): MDS-G010 v2.0 published
T2 (2027-03-02): Agent is triggered →
  "New MDS-G010 version detected (v2.0, 1 March 2027).
   47 earlier decisions are based on MDS-G010 v1.0.
   [ ] Re-validate decisions against v2.0
   [ ] Show only affected decisions
   [ ] Remind me later"
```

---

## PART C — Attention Priority List

> What the agent must pay attention to, in priority order. This list determines which items are injected into the agent's prompt at each state of the state machine.

### C1. P0 — Critical (wrong decision = submission rejection + 6-month delay)

1. **Class C/D detection** — the correct risk class must be determined for every device. MDS-G008 + intended use + technology combination
2. **AR license validity** — an expired AR = automatic rejection. Verify with the SFDA ARL lookup tool
3. **MDMA requirement** — MDMA is required even with CE/FDA approval. Since January 2022
4. **UDI DI + PI format** — GUDID compliant, correct segment labels
5. **IFU in Arabic + English** — English only = rejection. RTL + certified translator
6. **Clinical Evaluation Report present** — mandatory for Class C/D (MEDDEV 2.7/1 rev.4)
7. **Risk Management File** — ISO 14971:2019, all classes (depth by class)
8. **QMS certificate** — ISO 13485:2016 (MDSAP preferred)
9. **Cybersecurity documentation** — for connected devices (IEC 81001-5-1 + SBOM + threat model)
10. **Saudi-specific labeling** — Arabic + English + Saudi FDA logo/format requirements

### C2. P1 — High (wrong decision = 1-2 month delay)

11. **AR notarization + apostille** — missing legalization in the foreign country
12. **TFA (Technical File Assessment) depth** — by class (B = self-declaration, C = review, D = clinical)
13. **Conformity assessment route** — is the Annex II vs Annex III choice correct?
14. **IFU Arabic translation quality** — certified Arabic medical translator, not machine translation
15. **SBOM completeness** — are all dependencies (direct + transitive) listed?
16. **Threat model coverage** — was the STRIDE or PASTA methodology used?
17. **Penetration test report** — for Class D connected devices
18. **Pre-submission meeting recommendation** — recommended by SFDA for Class C/D devices

### C3. P2 — Medium (wrong decision = iterative correction)

19. **Post-market surveillance plan format** (PMSP) — frequency by class
20. **Periodic Safety Update Report** frequency — see A10
21. **Vigilance reporting timeline** — adverse event 10 days, FSCA 5 days
22. **Clinical literature search strategy** — MEDDEV 2.7/1 rev.4 reproducible search
23. **Equivalence justification rigor** — predicate device + biological/technical/clinical equivalence
24. **Software documentation level** — IEC 62304 class A/B/C
25. **Usability engineering file** — IEC 62366-1

### C4. P3 — Low (improvement)

26. **Best practice tips** — working groups, conferences, ICF benchmarking
27. **Glossary access** — term definitions
28. **Cross-reference validation** — internal document consistency
29. **Document formatting checks** — page numbers, header/footer, font
30. **Translation quality alerts** — terminology consistency flag

### C5. Which priority levels apply at each state?

| State | Attention level |
|---|---|
| INGEST | P3 (formatting) + P1 (translation quality) |
| CLASSIFY | P0 (#1 class detection) |
| CONFIRM_CLASS | P0 (#1) — route to human review |
| CHECKLIST | P0 (1-10) + P1 (11-18) |
| COLLECT | P1 (12-18) — missing document detection |
| VALIDATE | P0 (4-10) + P1 (11-18) + P2 (19-25) |
| REPORT | All levels — auditor-ready output |
| (Post-market) | P2 (19-21) — vigilance + PSUR + change notification |

---

## PART D — Implementation Phases

### D1. MVP (v0.1) — 2 weeks — "Pre-check Class B"
**Scope:**
- 4 agents: Orchestrator, Ingest, Classifier, Checklist (no Evidence Validator or Regulatory Watcher)
- 1 jurisdiction (Saudi SFDA)
- 3 document types: IFU, Technical File, Risk Management File
- ChromaDB (no Excel yet)
- CLI only (no web UI)
- Output: class detection (MDS-G008) + class-specific checklist
- 5 of the P0 items are checked (#1, #2, #5, #6, #7)

### D2. v0.2 — +2 weeks — "Validation + Excel Log"
- Evidence Validator agent (real clause-level validation)
- Excel logger (openpyxl + hash chain)
- Web UI (Streamlit — fast to build)
- 5 document types (the above + QMS certificate + AR letter)
- 2 jurisdictions (Saudi + UAE MoHAP — A15 multi-jurisdiction flag)
- Full P0 (1-10) checks

### D3. v0.3 — +2 weeks — "Regulatory Watcher + Audit Hardening"
- Regulatory Watcher (SFDA website scanning + RSS)
- Version lock + snapshot (A1)
- Audit hash chain (A2)
- Pre-submission meeting recommendation (A8)
- Periodic safety update reminders (A14)
- P1 (11-18) checks

### D4. v1.0 — +4 weeks — "Production"
- Multi-jurisdiction cross-validation (Saudi + UAE + Turkey)
- Arabic NLP pipeline (CAMeL Tools — RTL detection, terminology)
- LangGraph migration (custom state machine → LangGraph)
- Production hardening: auth, rate limiting, monitoring, error recovery
- P2 (19-25) + P3 (26-30) checks

---

## PART E — Next Step: UAE MoHAP

This document completes the Saudi plan. The next step is to prepare the same structure for **UAE MoHAP**. Key differences:

  - Law: Federal Law No. 8 of 2023 (Medical Devices)
  - Regulatory body: MoHAP (SFDA in Saudi Arabia)
  - MDMA equivalent: MoHAP Device Registration Certificate
  - AR: Local Authorized Representative (LAR) — UAE-resident
  - Cybersecurity: mandatory under Article 2.4 (IEC 81001-5-1 + SBOM + threat model + PMCP)
  - Data protection: UAE PDPL (Federal Decree-Law No. 45 of 2021)
  - Vigilance timeline: FSCA 10 days (5 days in Saudi Arabia)
  - PSUR: Class IIa every 2 years, IIb/III annually

Once the UAE plan is prepared with the same "agent behavior + attention list + refinements" structure, the two plans will be split into a **shared core** + **jurisdiction-specific modules** (the foundation of the A15 multi-jurisdiction flag).
