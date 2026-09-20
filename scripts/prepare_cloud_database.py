"""Operator-only schema/identity provisioning. Never run with the runtime identity."""

import json
import uuid
from pathlib import Path

from sqlalchemy import select, text

from lastbuy.domain import Actor
from lastbuy.fixtures import demo_snapshot
from lastbuy.service import Workflow
from lastbuy.store import BudgetAccount, BudgetAttempt, Store

root = Path(__file__).resolve().parents[1]
settings = json.loads((root / "evidence/function-public-settings.json").read_text())
identity = json.loads((root / "evidence/function-identity.json").read_text())
store = Store(settings["LASTBUY_DATABASE_URL"], initialize=True)
# SQL maps application principals by client ID, not the service-principal object ID.
sid = uuid.UUID(identity["clientId"]).bytes_le.hex()
with store.engine.begin() as connection:
    connection.execute(
        text(
            f"IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name='lastbuy-runtime') "
            f"CREATE USER [lastbuy-runtime] WITH SID=0x{sid}, TYPE=E"
        )
    )
    actual = connection.execute(
        text(
            "SELECT CONVERT(varchar(36),CAST(sid AS uniqueidentifier)) FROM sys.database_principals WHERE name='lastbuy-runtime'"
        )
    ).scalar_one()
    if actual.lower() != identity["clientId"].lower():
        raise RuntimeError(
            "Existing SQL principal maps to another identity; operator review required"
        )
    for table in [
        "cases",
        "orchestration_messages",
        "budget_accounts",
        "budget_attempts",
    ]:
        connection.execute(
            text(f"GRANT SELECT, INSERT, UPDATE ON dbo.[{table}] TO [lastbuy-runtime]")
        )
    for table in ["plan_versions", "approvals", "audit", "outbox"]:
        connection.execute(
            text(f"GRANT SELECT, INSERT ON dbo.[{table}] TO [lastbuy-runtime]")
        )
    connection.execute(text("GRANT SELECT ON dbo.people TO [lastbuy-runtime]"))
print(
    "Runtime SQL identity has table-scoped permissions; no DDL or registry writes.",
    flush=True,
)

actor = Actor(
    id="7642d701-b864-47df-a70d-9654c4572c2d",
    name="Anurag Sati",
    organization="NORTHSTAR",
    roles=["planner"],
    authority_minor=0,
)
store.register(actor)
workflow = Workflow(store, None, None)
snapshot = demo_snapshot()
snapshot.case_id = "LTB-CLOUD-001"
snapshot.title = "Cloud workspace · thermal-camera final buy"
if not any(c["id"] == snapshot.case_id for c in workflow.listing(actor)):
    workflow.create(snapshot, actor)

local = Store("sqlite:///" + str(root / "data/budget.db"))
with local.session() as session:
    prior = session.get(BudgetAccount, "development").reserved_paise
    attempts = [(a.id, a.data) for a in session.scalars(select(BudgetAttempt))]
with store.transaction() as session:
    if session.get(BudgetAccount, "development") is None:
        session.add(
            BudgetAccount(id="development", limit_paise=70_000, reserved_paise=prior)
        )
        session.flush()
        for attempt_id, data in attempts:
            session.add(BudgetAttempt(id=attempt_id, account="development", data=data))
# Close the old admission ledger; two independent allowances must never remain active.
with local.transaction() as session:
    account = session.get(BudgetAccount, "development")
    account.limit_paise = account.reserved_paise
print(
    "Cloud case seeded; real identity is planner only. Budget migrated; old allowance closed.",
    flush=True,
)
store.engine.dispose()
