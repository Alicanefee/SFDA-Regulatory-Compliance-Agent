"""
Agent: Excel Logger
===================

Role: Write all events to local .xlsx file with hash-chain audit trail.

Input: Event data (step, agent, status, duration, etc.)
Output: Appends a row to the Excel file with prev_hash + this_hash

Tool: openpyxl

Sheets (6 total):
- Process: timestamp, step, status, agent, duration, prev_hash, this_hash
- Documents: doc_id, name, type, upload_date, status, source_authority
- Classification: device_name, intended_use, class, rule_id, justification, version_snapshot
- Validation: doc_id, requirement, result, missing_items, notes, prev_hash, this_hash
- API_Log: timestamp, agent, model, tokens, cost, latency
- Audit: hash_chain_verification (computed on each event)

Hash chain (audit trail integrity):
- this_hash = sha256(prev_hash + row_content + timestamp)
- First row: prev_hash = "GENESIS"
- Inspector can verify chain integrity with separate script

See docs/BEHAVIOR_AND_ATTENTION.md §A2 for the hash chain design.

TODO (v0.2): Implement.
"""
from __future__ import annotations
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any


class ExcelLogger:
    """Writes audit-trail events to local .xlsx with hash chain.

    Sheets:
      - Process, Documents, Classification, Validation, API_Log, Audit
    """

    GENESIS_HASH = "GENESIS"

    def __init__(self, xlsx_path: str | Path) -> None:
        self.xlsx_path = Path(xlsx_path)
        self.last_hash = self._load_last_hash()
        # TODO: initialize workbook with 6 sheets if file doesn't exist

    def log(self, sheet: str, event: dict) -> None:
        """Append a row to the specified sheet with hash chain."""
        timestamp = datetime.now().isoformat()
        row_content = json.dumps(event, sort_keys=True)
        this_hash = hashlib.sha256(
            f"{self.last_hash}{row_content}{timestamp}".encode()
        ).hexdigest()
        event_with_hash = {
            **event,
            "timestamp": timestamp,
            "prev_hash": self.last_hash,
            "this_hash": this_hash,
        }
        # TODO: write to xlsx using openpyxl
        self.last_hash = this_hash

    def verify_chain(self) -> bool:
        """Verify the hash chain integrity. Returns True if valid."""
        # TODO (v0.2)
        # Read all rows, recompute hashes, verify prev_hash matches
        raise NotImplementedError

    def _load_last_hash(self) -> str:
        """Load the last this_hash from the Excel file."""
        # TODO (v0.2): read last row's this_hash column
        return self.GENESIS_HASH
