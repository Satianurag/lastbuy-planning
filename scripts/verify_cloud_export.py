"""Synthetic identity-boundary integration test, explicitly uses a model test double."""

import asyncio
import json
import os
import subprocess
from pathlib import Path

import requests
from sqlalchemy import func, select

from lastbuy.archive import BlobArchive
from lastbuy.domain import ApprovalRequest
from lastbuy.fixtures import DEMO_ACTORS, demo_snapshot
from lastbuy.service import Workflow
from lastbuy.sql_erp import Requisition, SQLSyntheticERP
from lastbuy.store import Outbox, Store

ROOT = Path(__file__).resolve().parents[1]
settings = json.loads((ROOT / "evidence/export-public-settings.json").read_text())
os.environ["LASTBUY_ARCHIVE_URL"] = settings["LASTBUY_ARCHIVE_URL"]
store = Store(settings["LASTBUY_DATABASE_URL"], initialize=False)
erp = SQLSyntheticERP(settings["LASTBUY_ERP_DATABASE_URL"])
for actor in DEMO_ACTORS.values():
    store.register(actor)


class TestAnalyst:
    async def assess(self, role, snapshot, calculation):
        return {
            "assessment": {
                "role": role,
                "summary": "Explicit integration test double; no model called",
                "findings": [],
                "evidence": ["pcn"],
            },
            "source": "test-double",
        }


workflow = Workflow(store, TestAnalyst(), None, archive=BlobArchive())
key_response = subprocess.run(
    [
        "az",
        "functionapp",
        "keys",
        "list",
        "-g",
        "rg-anuragsati6476-5065",
        "-n",
        "lastbuy-export-4126",
        "-o",
        "json",
    ],
    check=True,
    capture_output=True,
    text=True,
)
key = json.loads(key_response.stdout)["functionKeys"]["default"]
records = []
for suffix, lost in [("CREATE", False), ("RECOVER", True)]:
    case_id = "LTB-CLOUD-EXPORT-TEST-" + suffix
    snapshot = demo_snapshot(case_id)
    snapshot.title = "Synthetic worker identity test · model test double"
    if not any(c["id"] == case_id for c in workflow.listing(DEMO_ACTORS["planner"])):
        workflow.create(snapshot, DEMO_ACTORS["planner"])
        run_id, snapshot = workflow.begin(case_id, DEMO_ACTORS["planner"])
        asyncio.run(workflow.analyze(case_id, run_id, snapshot))
        case = workflow.get(case_id, DEMO_ACTORS["planner"])
        for role in ["engineering", "service", "finance", "procurement"]:
            workflow.approve(
                case_id,
                ApprovalRequest(
                    plan_sha256=case["plan"]["plan_sha256"],
                    role=role,
                    decision="approve",
                    reason="Synthetic integration authorization fixture; no real purchase.",
                ),
                DEMO_ACTORS[role],
            )
    case = workflow.get(case_id, DEMO_ACTORS["planner"])
    job = workflow.enqueue_export(
        case_id, case["plan"]["plan_sha256"], DEMO_ACTORS["procurement"]
    )
    if lost and erp.lookup(job["key"]) is None:
        with store.session() as session:
            payload = session.get(Outbox, job["key"]).payload
        try:
            erp.create_draft(job["key"], payload, lose_response=True)
        except TimeoutError:
            pass
    url = "https://lastbuy-export-4126.azurewebsites.net/api/exports/" + job["key"]
    first = requests.post(url, headers={"x-functions-key": key}, timeout=180)
    if first.status_code != 200:
        print("Worker returned", first.status_code, first.text[:600], flush=True)
        first.raise_for_status()
    second = requests.post(url, headers={"x-functions-key": key}, timeout=180)
    second.raise_for_status()
    assert first.json()["receipt"] == second.json()["receipt"]
    with erp.store.session() as session:
        count = session.scalar(
            select(func.count())
            .select_from(Requisition)
            .where(Requisition.key == job["key"])
        )
    final = workflow.get(case_id, DEMO_ACTORS["planner"])
    assert count == 1 and final["status"] == "EXPORTED" and final["audit_valid"]
    records.append(
        {
            "case_id": case_id,
            "lost_response_preseeded": lost,
            "repeat_same_receipt": True,
            "external_rows": count,
            "receipt": first.json()["receipt"],
            "status": final["status"],
            "audit_valid": final["audit_valid"],
        }
    )
report = {
    "scope": "Real cloud worker identity, primary Azure SQL, separate synthetic ERP Azure SQL, Blob archive. Explicit model/approver test fixtures; not authentic finance approvals or SAP.",
    "records": records,
}
(ROOT / "evidence/cloud-export-verification.json").write_text(
    json.dumps(report, indent=2)
)
print(json.dumps(report, indent=2))
