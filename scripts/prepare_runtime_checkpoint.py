"""Prepare isolated real Durable recovery test from exact committed Foundry results.

No invented model responses: snapshot and stage assessments are copied byte-for-
byte from the recorded v7 case. This exercises checkpoint reuse, not fresh inference.
"""

import json
import uuid
import zipfile
from pathlib import Path

from lastbuy.domain import Snapshot, digest, now
from lastbuy.fixtures import DEMO_ACTORS
from lastbuy.service import Workflow
from lastbuy.store import Case, Store, audit

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "data/runtime-acceptance"
DEST.mkdir(parents=True, exist_ok=True)
record = json.loads((ROOT / "evidence/full-cloud-release7.json").read_text())
snapshot = Snapshot.model_validate(record["snapshot"])
assert digest(snapshot) == record["plan"]["input_snapshot_sha256"]
assert all(
    s["status"] == "COMPLETE" and s["result"]["agent_version"] == "7"
    for s in record["stages"]
)
url = "sqlite:///" + str(DEST / "cases.db")
store = Store(url)
w = Workflow(store, None, None)
for actor in DEMO_ACTORS.values():
    store.register(actor)
if w.listing(DEMO_ACTORS["planner"]):
    print("Existing checkpoint preserved; do not reset a live run.")
    raise SystemExit(0)
w.create(snapshot, DEMO_ACTORS["planner"])
run_id = str(uuid.uuid4())
with store.transaction() as session:
    case = session.get(Case, snapshot.case_id)
    case.status = "ANALYZING"
    case.analysis_id = run_id
    case.analysis_started = now().isoformat()
    case.stages = record["stages"]
    audit(
        session,
        case,
        "runtime-verification",
        "VERIFIED_CLOUD_CHECKPOINT_LOADED",
        {
            "origin": "full-cloud-release7.json",
            "origin_run_id": record["plan"]["run_id"],
            "snapshot_sha256": digest(snapshot),
            "new_model_call": False,
            "purpose": "Exercise persisted-stage recovery in actual Functions runtime",
        },
    )
package = json.loads((ROOT / "evidence/functions-source-release.json").read_text())
functions = DEST / "functions"
with zipfile.ZipFile(ROOT / package["archive"]) as z:
    z.extractall(functions)
values = {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "LASTBUY_DATABASE_URL": url,
    "LASTBUY_SCHEMA_MODE": "managed",
    "LASTBUY_LOCAL_PROBE": "1",
    "LASTBUY_HOSTED_VERSION": "7",
    "LASTBUY_HOSTED_AGENT": "lastbuy-analysis",
    "LASTBUY_ARCHIVE_URL": "https://lastbuydev4126.blob.core.windows.net",
    "FOUNDRY_PROJECT_ENDPOINT": "https://anuragsati6476-4126-resource.services.ai.azure.com/api/projects/anuragsati6476-4126",
    "AZURE_AI_MODEL_DEPLOYMENT_NAME": "lastbuy-dev-mini",
    "LASTBUY_BUDGET_DATABASE_URL": "mssql+pyodbc://@lastbuy-dev-4126.database.windows.net/lastbuy?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no&Connection+Timeout=60",
    "FUNCTIONS_CORE_TOOLS_TELEMETRY_OPTOUT": "1",
}
(functions / "local.settings.json").write_text(
    json.dumps({"IsEncrypted": False, "Values": values}, indent=2) + "\n"
)
host = json.loads((functions / "host.json").read_text())
host["extensions"]["durableTask"]["hubName"] = "LastBuyAcceptance20260920"
(functions / "host.json").write_text(json.dumps(host, indent=2) + "\n")
summary = {
    "case_id": snapshot.case_id,
    "run_id": run_id,
    "database_url": url,
    "snapshot_sha256": digest(snapshot),
    "host_source_sha256": package["sha256"],
    "function_directory": str(functions),
    "hub": "LastBuyAcceptance20260920",
    "origin": "Actual completed hosted v7 stage results; checkpoint recovery test, not new model inference",
}
(DEST / "checkpoint.json").write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps(summary, indent=2))
