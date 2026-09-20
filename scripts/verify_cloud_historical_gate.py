"""Verify the deployed worker refuses a legacy-approved historical quantity.

The fixture uses captured real model responses replayed through the old packaged
workflow. All actors and enterprise data are synthetic; no new model call occurs.
"""

import json
import os
import subprocess
from pathlib import Path

import requests
from sqlalchemy import func, select

from lastbuy.sql_erp import Requisition, SQLSyntheticERP
from lastbuy.store import Store

ROOT = Path(__file__).resolve().parents[1]
CHILD = ROOT / "data/runtime-acceptance/legacy_fixture.py"
CHILD.write_text("""import asyncio,json
from pathlib import Path
from lastbuy.archive import BlobArchive
from lastbuy.domain import Snapshot,ApprovalRequest
from lastbuy.fixtures import DEMO_ACTORS
from lastbuy.service import Workflow
from lastbuy.store import Store,Case,Outbox,audit
import lastbuy.service as service
assert not hasattr(service,'historical_plan_checks'), 'Fixture must execute archived pre-fix workflow'
ROOT=Path(__file__).resolve().parents[2]
settings=json.loads((ROOT/'evidence/export-public-settings.json').read_text())
spec=json.loads((ROOT/'evaluations/live-acceptance-20260920.json').read_text())
novel=json.loads((ROOT/'evidence/live-acceptance-novel.json').read_text())
original=json.loads((ROOT/'evidence/full-cloud-release7.json').read_text())
snapshot=Snapshot.model_validate(spec['novel']['snapshot'])
snapshot.case_id='LTB-CLOUD-LEGACY-TIME-20260920'
snapshot.title='Synthetic regression: legacy historical count must be blocked'
responses={s['role']:s['result'] for s in original['stages']}
responses['supply']=novel['result']
class RecordedResponses:
    async def assess(self,role,snapshot,calculation):return responses[role]
store=Store(settings['LASTBUY_DATABASE_URL'],initialize=False)
for a in DEMO_ACTORS.values():store.register(a)
w=Workflow(store,RecordedResponses(),None,archive=BlobArchive())
if not any(c['id']==snapshot.case_id for c in w.listing(DEMO_ACTORS['planner'])):
    w.create(snapshot,DEMO_ACTORS['planner'])
    run,snapshot=w.begin(snapshot.case_id,DEMO_ACTORS['planner'])
    asyncio.run(w.analyze(snapshot.case_id,run,snapshot))
    c=w.get(snapshot.case_id,DEMO_ACTORS['planner'])
    assert c['status']=='READY_FOR_APPROVAL'
    with store.transaction() as session:
        case=session.get(Case,snapshot.case_id)
        audit(session,case,'regression-fixture','LEGACY_RECORDED_MODEL_REPLAY',{'new_model_call':False,'purpose':'Verify new worker rejects historical evidence accepted by previous software','captured_source':'live-acceptance-novel.json'})
    for role in ('engineering','service','finance','procurement'):
        w.approve(snapshot.case_id,ApprovalRequest(plan_sha256=c['plan']['plan_sha256'],role=role,decision='approve',reason='Synthetic legacy approval fixture; deployed corrected worker must reject.'),DEMO_ACTORS[role])
c=w.get(snapshot.case_id,DEMO_ACTORS['planner'])
job=w.enqueue_export(c['id'],c['plan']['plan_sha256'],DEMO_ACTORS['procurement'])
(ROOT/'data/runtime-acceptance/legacy-job.json').write_text(json.dumps({'case_id':c['id'],'key':job['key']},indent=2))
print('Legacy approved outbox fixture prepared; no model called.')
""")
env = dict(
    os.environ,
    PYTHONPATH=str(ROOT / "data/runtime-acceptance/functions"),
    LASTBUY_ARCHIVE_URL="https://lastbuydev4126.blob.core.windows.net",
)
subprocess.run([str(ROOT / ".venv/bin/python"), str(CHILD)], env=env, check=True)
job = json.loads((ROOT / "data/runtime-acceptance/legacy-job.json").read_text())
settings = json.loads((ROOT / "evidence/export-public-settings.json").read_text())
key = json.loads(
    subprocess.check_output(
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
        text=True,
    )
)["functionKeys"]["default"]
r = requests.post(
    "https://lastbuy-export-4126.azurewebsites.net/api/exports/" + job["key"],
    headers={"x-functions-key": key},
    timeout=180,
)
assert r.status_code == 409, (r.status_code, r.text[:400])
assert "Historical evidence" in r.json()["detail"], r.text
store = Store(settings["LASTBUY_DATABASE_URL"], initialize=False)
erp = SQLSyntheticERP(settings["LASTBUY_ERP_DATABASE_URL"])
with erp.store.session() as session:
    count = session.scalar(
        select(func.count())
        .select_from(Requisition)
        .where(Requisition.key == job["key"])
    )
assert count == 0
record = {
    "scope": "Actual deployed export worker, Azure SQL and real captured provider output replayed into an explicitly synthetic legacy-approved fixture; no new model call",
    "case_id": job["case_id"],
    "http_status": r.status_code,
    "reason": r.json()["detail"],
    "external_rows": count,
    "unsafe_write_prevented": True,
}
(ROOT / "evidence/cloud-historical-gate-verification.json").write_text(
    json.dumps(record, indent=2) + "\n"
)
print(json.dumps(record, indent=2))
