"""Authorized planner smoke run through deployed Functions; no financial approvals."""

import json
import subprocess
import time
from pathlib import Path

import requests

from lastbuy.fixtures import demo_snapshot
from lastbuy.service import Workflow
from lastbuy.store import Store

ROOT = Path(__file__).resolve().parents[1]
settings = json.loads((ROOT / "evidence/function-public-settings.json").read_text())
store = Store(settings["LASTBUY_DATABASE_URL"], initialize=False)
w = Workflow(store, None, None)
w.durable = True
actor = store.actor("7642d701-b864-47df-a70d-9654c4572c2d")
case_id = "LTB-CLOUD-RELEASE-" + settings["LASTBUY_HOSTED_VERSION"]
if not any(x["id"] == case_id for x in w.listing(actor)):
    s = demo_snapshot(case_id)
    s.title = "Cloud verification · current release · synthetic ASIC final buy"
    w.create(s, actor)
case = w.get(case_id, actor)
if case["status"] == "DRAFT":
    run_id, snapshot = w.begin(case_id, actor)
else:
    run_id = case["analysis_id"]
key = json.loads(
    subprocess.run(
        [
            "az",
            "functionapp",
            "keys",
            "list",
            "-g",
            "rg-anuragsati6476-5065",
            "-n",
            "lastbuy-dev-4126",
            "-o",
            "json",
        ],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
)["functionKeys"]["default"]
if case["status"] in ["DRAFT", "ANALYZING"]:
    response = requests.post(
        "https://lastbuy-dev-4126.azurewebsites.net/api/orchestrations/" + run_id,
        headers={"x-functions-key": key},
        json={"case_id": case_id},
        timeout=90,
    )
    response.raise_for_status()
print(
    json.dumps({"case_id": case_id, "run_id": run_id, "starter": "accepted"}),
    flush=True,
)
for _ in range(30):
    case = w.get(case_id, actor)
    print(
        json.dumps(
            {
                "status": case["status"],
                "stages": [(s["role"], s["status"]) for s in case["stages"]],
            }
        ),
        flush=True,
    )
    if case["status"] != "ANALYZING":
        break
    time.sleep(15)
path = (
    ROOT
    / "evidence"
    / ("full-cloud-release" + settings["LASTBUY_HOSTED_VERSION"] + ".json")
)
path.write_text(json.dumps(case, indent=2))
assert case["status"] == "READY_FOR_APPROVAL", case["status"]
assert (
    case["plan"]["purchase_quantity"] == 10000
    and case["plan"]["commitment_minor"] == 80000000
)
assert all(
    s["result"]["agent_version"] == settings["LASTBUY_HOSTED_VERSION"]
    for s in case["stages"]
)
assert case["plan"]["snapshot_archive"] and case["audit_valid"]
print(
    "Full current cloud release passed; no approvals or exports performed.", flush=True
)
