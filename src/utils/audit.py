"""
Audit Trail Validator
=====================

Verifies the hash chain integrity of the Excel audit log.

Used by:
- Inspector (manual run)
- Periodic integrity check (automated, daily)

Reads the Excel file, recomputes hashes, verifies prev_hash chain is intact.
Reports any tampered rows.

See docs/BEHAVIOR_AND_ATTENTION.md §A2 for the hash chain design.

TODO (v0.2): Implement.
"""
from __future__ import annotations
from pathlib import Path
from typing import Any


class AuditValidator:
    """Verifies hash chain integrity of the Excel audit log."""

    def __init__(self, xlsx_path: str | Path) -> None:
        self.xlsx_path = Path(xlsx_path)

    def verify_chain(self) -> dict:
        """Verify the hash chain integrity.

        Returns:
            {
              "valid": bool,
              "rows_checked": int,
              "tampered_rows": list[int],  # row indices
              "breaks": list[dict],  # {row, expected_hash, actual_hash}
            }
        """
        # TODO (v0.2): implement
        # Read all rows in order
        # For each row, recompute this_hash = sha256(prev_hash + row_content + timestamp)
        # Compare with stored this_hash
        # If mismatch → tampered
        # Verify next row's prev_hash == current row's this_hash
        raise NotImplementedError

    def generate_audit_report(self) -> str:
        """Generate a markdown report for an inspector."""
        # TODO (v0.2)
        raise NotImplementedError
