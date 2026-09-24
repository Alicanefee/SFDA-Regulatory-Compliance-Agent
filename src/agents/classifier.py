"""
Agent: Classifier
=================

Role: Determine device risk class per MDS-G008 + MDS-G5 rules.

Input: Device intended use, technology, applicable rules (retrieved from vector store)
Output: Risk class (A/B/C/D) + cited rule_id + justification

Model: Strong model (Command R+ / GPT-4 / Claude 3.5)

Decision logic:
- Class A: low risk (e.g. bandages, non-invasive, non-active)
- Class B: low-moderate (e.g. surgical instruments, non-active invasive short-term)
- Class C: moderate-high (e.g. diagnostic imaging with non-ionizing radiation, active implantable)
- Class D: high (e.g. implantable long-term, life-supporting, drug delivery)

Conservative-by-design rule:
- Borderline B/C → classify as C (per SFDA safety-first approach)
- Borderline C/D → classify as D
- Any uncertainty → route to MANUAL_REVIEW

See docs/BEHAVIOR_AND_ATTENTION.md §B2 rule #2 (conservative by design).

TODO (v0.2): Implement.
"""
from __future__ import annotations
from typing import Any


class ClassifierAgent:
    """Determines risk class per MDS-G008.

    Output schema:
        {
          "class": "A" | "B" | "C" | "D",
          "rule_id": str,  # e.g. "MDS-G008-R13"
          "justification": str,  # 2-3 sentences citing the rule
          "is_uncertain": bool,  # if true → MANUAL_REVIEW
          "uncertainty_reason": str  # if is_uncertain
        }
    """

    def __init__(self) -> None:
        pass

    def classify(self, intended_use: str, retrieved_rules: list[dict]) -> dict:
        """Classify device per MDS-G008.

        Args:
            intended_use: Free-text device intended use statement
            retrieved_rules: List of retrieved MDS-G008 rules from vector store

        Returns: Classification result with cited rule_id.
        """
        # TODO (v0.2): implement
        # - Build context packet
        # - Call LLM with constrained prompt (JSON-only output)
        # - Validate cited rule_id exists in retrieved_rules
        # - If uncertain → flag for MANUAL_REVIEW
        raise NotImplementedError
