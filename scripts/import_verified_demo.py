"""Copy a completed synthetic cloud plan for local review without another paid call."""

import json
from pathlib import Path

from lastbuy.domain import Snapshot, digest
from lastbuy.fixtures import DEMO_ACTORS
from lastbuy.service import Workflow
from lastbuy.store import Case, PlanVersion, Store, audit

root = Path(__file__).resolve().parents[1]
record = json.loads((root / "evidence/full-cloud-release7.json").read_text())
snapshot = Snapshot.model_validate(record["snapshot"])
plan = record["plan"]
assert snapshot.synthetic and record["status"] == "READY_FOR_APPROVAL"
assert plan["input_snapshot_sha256"] == digest(snapshot)
assert (
    digest({k: v for k, v in plan.items() if k != "plan_sha256"}) == plan["plan_sha256"]
)
store = Store("sqlite:///" + str(root / "data/durable.db"))
for actor in DEMO_ACTORS.values():
    store.register(actor)
w = Workflow(store, None, None)
if not any(c["id"] == snapshot.case_id for c in w.listing(DEMO_ACTORS["planner"])):
    w.create(snapshot, DEMO_ACTORS["planner"])
    with store.transaction() as session:
        case = session.get(Case, snapshot.case_id)
        case.plan = plan
        case.status = "READY_FOR_APPROVAL"
        case.stages = record["stages"]
        case.analysis_id = plan["run_id"]
        session.add(
            PlanVersion(
                hash=plan["plan_sha256"],
                case_id=case.id,
                payload=plan,
                snapshot=snapshot.model_dump(mode="json"),
            )
        )
        audit(
            session,
            case,
            "local-demo-import",
            "VERIFIED_SYNTHETIC_CLOUD_PLAN_IMPORTED",
            {
                "plan_sha256": plan["plan_sha256"],
                "origin": "full-cloud-release7.json",
                "new_model_call": False,
            },
        )
print(
    "Imported exact completed synthetic cloud plan for local review; no approval or model call created."
)
