"""
Agent: Evidence Validator
=========================

Role: Validate user submission evidence against retrieved regulatory rules.

Input: User document text + relevant regulatory clause
Output: COMPLIANT | MISSING | UNCLEAR (per clause)

Model: Mid-tier model (Command R / GPT-4o-mini / Claude Haiku)

Output schema:
    {
      "clause_id": str,
      "verdict": "compliant" | "missing" | "unclear",
      "evidence_cited": str,  # quote from user doc
      "explanation": str,  # 1-2 sentences
      "suggested_fix": str  # if not compliant
    }

Defense layers:
- L1 preamble: "only cite clauses from retrieved_rules"
- L2 tool use: lookup_clause(clause_id) to verify before citing
- L3 post-process: drop any cited_clause not in retrieved_rules

See docs/BEHAVIOR_AND_ATTENTION.md §A3 for the 3-layer hallucination defense.

TODO (v0.2): Implement. Currently the MVP main.py does a simplified version
of this inline (validation flow with Cohere Command R+).
"""
from __future__ import annotations
from typing import Any


class EvidenceValidator:
    """Validates user evidence against regulatory rules.

    Conservative by design (see BEHAVIOR_AND_ATTENTION.md §B2 rule #2):
    - If evidence is unclear → "unclear" verdict, not "compliant"
    - If cited rule_id is hallucinated → drop finding, mark "(unverified)"
    """

    def validate(
        self,
        user_evidence: list[dict],
        retrieved_rules: list[dict],
    ) -> list[dict]:
        """Validate each piece of evidence against applicable rules.

        Returns list of findings (one per rule evaluated).
        """
        # TODO (v0.2): implement
        # - For each retrieved rule, find matching evidence in user docs
        # - Call LLM with constrained prompt
        # - Validate cited clause IDs
        # - Return findings list
        raise NotImplementedError

    def _post_process_findings(self, findings: list[dict], retrieved_rules: list[dict]) -> list[dict]:
        """L3 defense: drop hallucinated clause citations."""
        valid_clause_ids = {r["rule_id"] for r in retrieved_rules}
        for f in findings:
            if f.get("cited_clause", "") not in valid_clause_ids:
                f["cited_clause"] = "(unverified)"
        return findings
