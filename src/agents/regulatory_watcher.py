"""
Agent: Regulatory Watcher
=========================

Role: Periodically scan SFDA official documents page for new versions.

Input: URL list (SFDA official document URLs)
Output: New version notifications + diff analysis

Pipeline:
1. Poll SFDA document URLs on schedule (weekly)
2. Download each document
3. Compute version hash (sha256 of text)
4. Compare with last-seen hash
5. If changed → fetch both versions, run diff
6. Notify user: "MDS-G008 updated from v3.0 to v3.1 — 14 clauses changed"
7. Trigger re-validation of past decisions that depended on the old version

Model: Lightweight model for diff summarization

See docs/BEHAVIOR_AND_ATTENTION.md §A1 (version lock) — the watcher is
the trigger that initiates re-validation of stale decisions.

TODO (v0.3): Implement.
"""
from __future__ import annotations
import hashlib
from datetime import datetime
from typing import Any


# SFDA official document URLs to watch
SFDA_DOCUMENT_URLS = {
    "MDS-G5": "https://www.sfda.gov.sa/en/medical-devices/regulations/mds-g5",
    "MDS-G008": "https://www.sfda.gov.sa/en/medical-devices/regulations/mds-g008",
    "MDS-G010": "https://www.sfda.gov.sa/en/medical-devices/regulations/mds-g010",
    "MDS-G27": "https://www.sfda.gov.sa/en/medical-devices/regulations/mds-g27",
    "MDS-REQ9": "https://www.sfda.gov.sa/en/medical-devices/regulations/mds-req9",
    "MDS-REQ5": "https://www.sfda.gov.sa/en/medical-devices/regulations/mds-req5",
}


class RegulatoryWatcher:
    """Watches SFDA regulatory documents for new versions.

    Maintains a version registry:
        {
          "MDS-G008": {
            "current_version": "v3.0",
            "current_hash": "sha256:...",
            "last_checked": "2026-09-24T11:30:00",
            "last_changed": "2024-03-15"
          },
          ...
        }
    """

    def __init__(self, version_registry_path: str = "version_registry.json") -> None:
        self.registry_path = version_registry_path
        # TODO: load existing registry

    def scan_all(self) -> list[dict]:
        """Scan all SFDA documents for new versions.

        Returns: list of changes detected.
        """
        # TODO (v0.3): implement
        # - For each URL: fetch document
        # - Compute hash
        # - Compare with registry
        # - If changed: compute diff, notify
        raise NotImplementedError

    def notify_change(self, doc_id: str, old_version: str, new_version: str, diff_summary: str) -> dict:
        """Generate a user notification for a regulatory version change.

        Includes a list of past decisions that depend on the old version
        (retrieved from Excel audit trail).
        """
        # TODO (v0.3)
        raise NotImplementedError

    def trigger_revalidation(self, doc_id: str, old_version: str) -> list[str]:
        """Find past decisions that depended on the old version.

        Returns: list of decision_ids to re-validate.
        """
        # TODO (v0.3): query Excel audit trail for decisions citing old_version
        raise NotImplementedError
