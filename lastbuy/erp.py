"""Synthetic ERP with an independent database and real external-key uniqueness.

It simulates a draft requisition, never claims a live SAP transaction. Application
analysis credentials do not reference this adapter. Production supplies a separate
export service identity and a customer-approved SAP adapter.
"""

import json
import sqlite3
from pathlib import Path

from .domain import canonical, digest, now


class SyntheticERP:
    def __init__(self, path="data/synthetic-erp.db"):
        self.path = path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(path) as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS requisitions (external_key TEXT PRIMARY KEY, payload_hash TEXT NOT NULL, receipt TEXT NOT NULL)"
            )

    def lookup(self, key):
        with sqlite3.connect(self.path) as connection:
            row = connection.execute(
                "SELECT receipt FROM requisitions WHERE external_key=?", (key,)
            ).fetchone()
            return json.loads(row[0]) if row else None

    def create_draft(self, key, payload, lose_response=False):
        receipt = {
            "external_reference": "SYN-PR-" + key[:12].upper(),
            "external_key": key,
            "status": "DRAFT_REQUISITION",
            "synthetic": True,
            "payload_sha256": digest(payload),
            "at": now().isoformat(),
        }
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                "INSERT OR IGNORE INTO requisitions VALUES (?,?,?)",
                (key, digest(payload), canonical(receipt)),
            )
            row = connection.execute(
                "SELECT payload_hash,receipt FROM requisitions WHERE external_key=?",
                (key,),
            ).fetchone()
            if row[0] != digest(payload):
                raise ValueError("External key already used for a different payload")
            receipt = json.loads(row[1])
        if lose_response:
            raise TimeoutError(
                "Synthetic ERP accepted the draft; response deliberately lost"
            )
        return receipt
