"""
Agent: Checklist
================

Role: Generate per-class document checklist.

Input: Risk class (A/B/C/D)
Output: Document list + source authority (SFDA / ISO / IEC)

Model: Rule-based (no LLM needed) — checklists are deterministic per class.

Per-class document list (Saudi SFDA):

Class A:
- Declaration of Conformity
- Technical File (simplified)
- IFU (Arabic + English)
- QMS certificate (ISO 13485)

Class B (additionally):
- Clinical Evaluation Report (equivalence-based, MEDDEV 2.7/1 rev.4)
- Risk Management File (ISO 14971) — full
- Labelling (Arabic + English)
- Authorized Representative (AR) appointment letter (notarized + apostilled)

Class C (additionally):
- Clinical Evaluation Report (with clinical data + literature review)
- Cybersecurity documentation (if connected) — IEC 81001-5-1 + SBOM + threat model
- Post-Market Surveillance Plan (PMSP)
- Periodic Safety Update Report (PSUR) — annually for first 2 years
- UDI DI + PI labeling verified

Class D (additionally):
- Clinical Evaluation Report (with clinical investigation data + PMCF)
- Penetration test report (if connected)
- Full cybersecurity documentation (above + PMCP)
- PSUR annually

See docs/BEHAVIOR_AND_ATTENTION.md §A9-A12 for class-based depth rules.

TODO (v0.2): Implement with full per-class checklist tables.
"""
from __future__ import annotations
from typing import Any


# Class-based checklist (rule-based, no LLM)
CLASS_CHECKLISTS: dict[str, list[dict]] = {
    "A": [
        {"name": "Declaration of Conformity", "source": "SFDA", "mandatory": True},
        {"name": "Technical File (simplified)", "source": "SFDA", "mandatory": True},
        {"name": "IFU (Arabic + English)", "source": "SFDA", "mandatory": True},
        {"name": "QMS Certificate (ISO 13485:2016)", "source": "ISO", "mandatory": True},
    ],
    "B": [
        # All of Class A, plus:
        {"name": "Clinical Evaluation Report (equivalence-based)", "source": "MEDDEV 2.7/1 rev.4", "mandatory": True},
        {"name": "Risk Management File (ISO 14971:2019)", "source": "ISO", "mandatory": True},
        {"name": "Labelling (Arabic + English)", "source": "SFDA", "mandatory": True},
        {"name": "AR Appointment Letter (notarized + apostilled)", "source": "SFDA", "mandatory": True},
    ],
    "C": [
        # All of Class B, plus:
        {"name": "Clinical Evaluation Report (with clinical data)", "source": "MEDDEV 2.7/1 rev.4", "mandatory": True},
        {"name": "Cybersecurity documentation (if connected)", "source": "IEC 81001-5-1", "mandatory": True},
        {"name": "Post-Market Surveillance Plan (PMSP)", "source": "SFDA", "mandatory": True},
        {"name": "Periodic Safety Update Report (PSUR) — annual", "source": "SFDA", "mandatory": True},
        {"name": "UDI DI + PI labeling verified", "source": "GUDID", "mandatory": True},
    ],
    "D": [
        # All of Class C, plus:
        {"name": "Clinical Evaluation Report (with clinical investigation + PMCF)", "source": "MEDDEV 2.7/1 rev.4", "mandatory": True},
        {"name": "Penetration test report (if connected)", "source": "IEC 62443", "mandatory": True},
        {"name": "Full cybersecurity documentation (with PMCP)", "source": "IEC 81001-5-1", "mandatory": True},
    ],
}


class ChecklistAgent:
    """Generates per-class document checklist.

    Pure rule-based — no LLM needed. Checklists are deterministic.
    """

    def generate(self, risk_class: str) -> list[dict]:
        """Generate checklist for a given risk class.

        Args:
            risk_class: "A", "B", "C", or "D"

        Returns:
            List of required documents with source authority.
        """
        if risk_class not in CLASS_CHECKLISTS:
            raise ValueError(f"Unknown risk class: {risk_class}. Must be A/B/C/D.")

        # Cumulative: class C includes all B's requirements, etc.
        result = []
        for cls in ["A", "B", "C", "D"]:
            if cls > risk_class:
                break
            result.extend(CLASS_CHECKLISTS[cls])
        return result

    def get_missing_documents(
        self, risk_class: str, submitted_documents: list[str]
    ) -> list[dict]:
        """Compare required vs submitted, return missing list."""
        required = self.generate(risk_class)
        submitted_lower = [d.lower() for d in submitted_documents]
        missing = [
            r for r in required
            if not any(r["name"].lower() in s for s in submitted_lower)
        ]
        return missing
