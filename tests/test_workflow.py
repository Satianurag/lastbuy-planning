import asyncio
from datetime import timedelta

import pytest

from lastbuy.domain import Actor, ApprovalRequest
from lastbuy.erp import SyntheticERP
from lastbuy.fixtures import DEMO_ACTORS, FIXTURE_CLOCK, demo_snapshot
from lastbuy.service import DomainError, Workflow
from lastbuy.store import Case, Person, Store


class TestAnalyst:
    __test__ = False

    async def assess(self, role, snapshot, calculation):
        return {
            "assessment": {
                "role": role,
                "summary": "Test double: no live model called",
                "findings": [],
                "evidence": ["pcn"],
            },
            "source": "test-double",
        }


@pytest.fixture
def workflow(tmp_path):
    store = Store("sqlite:///" + str(tmp_path / "cases.db"))
    for actor in DEMO_ACTORS.values():
        store.register(actor)
    w = Workflow(
        store,
        TestAnalyst(),
        SyntheticERP(str(tmp_path / "erp.db")),
        clock=lambda: FIXTURE_CLOCK,
    )
    w.create(demo_snapshot(), DEMO_ACTORS["planner"])
    return w


def analyzed(w):
    run, snapshot = w.begin("LTB-2026-017", DEMO_ACTORS["planner"])
    asyncio.run(w.analyze(snapshot.case_id, run, snapshot))
    return w.get(snapshot.case_id, DEMO_ACTORS["planner"])


def approve_all(w, plan):
    for role in ("engineering", "service", "finance", "procurement"):
        w.approve(
            "LTB-2026-017",
            ApprovalRequest(
                plan_sha256=plan["plan_sha256"],
                role=role,
                decision="approve",
                reason="Reviewed evidence and scoped authority.",
            ),
            DEMO_ACTORS[role],
        )


def test_full_flow_approval_and_idempotent_export(workflow):
    w = workflow
    c = analyzed(w)
    approve_all(w, c["plan"])
    queued = w.enqueue_export(
        c["id"], c["plan"]["plan_sha256"], DEMO_ACTORS["procurement"]
    )
    first = w.dispatch(queued["key"])
    assert first == w.dispatch(queued["key"])
    again = w.enqueue_export(
        c["id"], c["plan"]["plan_sha256"], DEMO_ACTORS["procurement"]
    )
    assert again["receipt"] == first
    state = w.get(c["id"], DEMO_ACTORS["planner"])
    assert state["status"] == "EXPORTED" and state["audit_valid"]


def test_lost_erp_response_reconciles_after_restart(workflow):
    w = workflow
    c = analyzed(w)
    approve_all(w, c["plan"])
    job = w.enqueue_export(
        c["id"], c["plan"]["plan_sha256"], DEMO_ACTORS["procurement"]
    )
    assert w.dispatch(job["key"], lose_response=True) is None
    assert w.get(c["id"], DEMO_ACTORS["planner"])["status"] == "EXPORT_UNCERTAIN"
    restarted = Workflow(
        w.store, TestAnalyst(), SyntheticERP(w.erp.path), clock=lambda: FIXTURE_CLOCK
    )
    receipt = restarted.dispatch(job["key"])
    assert receipt == w.erp.lookup(job["key"])
    assert w.get(c["id"], DEMO_ACTORS["planner"])["status"] == "EXPORTED"


def test_changed_snapshot_invalidates_approved_plan(workflow):
    w = workflow
    c = analyzed(w)
    approve_all(w, c["plan"])
    c = w.get(c["id"], DEMO_ACTORS["planner"])
    s = demo_snapshot()
    s.source_revision = 2
    s.lots[0].reserved = 1000
    w.replace_snapshot(c["id"], s, c["revision"], DEMO_ACTORS["planner"])
    with pytest.raises(DomainError):
        w.enqueue_export(c["id"], c["plan"]["plan_sha256"], DEMO_ACTORS["procurement"])
    newer = analyzed(w)
    assert newer["plan"]["purchase_quantity"] == 11000
    with pytest.raises(DomainError):
        w.enqueue_export(
            c["id"], newer["plan"]["plan_sha256"], DEMO_ACTORS["procurement"]
        )


@pytest.mark.parametrize(
    "failure",
    [
        "wrong_role",
        "missing_approvals",
        "expired_approval",
        "revoked_actor",
        "transferred_approver",
        "reduced_authority",
        "tampered_plan",
        "old_hash",
        "cross_organization",
        "duty_collision",
        "expired_deadline",
    ],
)
def test_release_boundaries(workflow, failure):
    w = workflow
    c = analyzed(w)
    plan = c["plan"]
    if failure not in {"missing_approvals", "wrong_role", "duty_collision"}:
        approve_all(w, plan)
    with pytest.raises(DomainError):
        if failure == "wrong_role":
            w.approve(
                c["id"],
                ApprovalRequest(
                    plan_sha256=plan["plan_sha256"],
                    role="finance",
                    decision="approve",
                    reason="Should be forbidden",
                ),
                DEMO_ACTORS["planner"],
            )
            return
        if failure == "expired_approval":
            w.clock = lambda: FIXTURE_CLOCK + timedelta(hours=25)
        if failure == "expired_deadline":
            w.clock = lambda: FIXTURE_CLOCK + timedelta(days=30)
        if failure in {"revoked_actor", "reduced_authority", "transferred_approver"}:
            with w.store.transaction() as session:
                p = session.get(Person, DEMO_ACTORS["finance"].id)
                p.data = {
                    **p.data,
                    **(
                        {"active": False}
                        if failure == "revoked_actor"
                        else (
                            {"organization": "OTHER"}
                            if failure == "transferred_approver"
                            else {"authority_minor": 1}
                        )
                    ),
                }
        if failure == "tampered_plan":
            with w.store.transaction() as session:
                case = session.get(Case, c["id"])
                case.plan = {**case.plan, "purchase_quantity": 1}
        if failure == "cross_organization":
            outsider = Actor(
                id="outsider",
                name="Other",
                organization="OTHER",
                roles=["procurement"],
                authority_minor=999999999,
            )
            w.store.register(outsider)
            w.get(c["id"], outsider)
            return
        if failure == "duty_collision":
            actor = DEMO_ACTORS["engineering"].model_copy(deep=True)
            actor.roles = ["engineering", "service"]
            with w.store.transaction() as session:
                session.get(Person, actor.id).data = actor.model_dump(mode="json")
            for role in ["engineering", "service"]:
                w.approve(
                    c["id"],
                    ApprovalRequest(
                        plan_sha256=plan["plan_sha256"],
                        role=role,
                        decision="approve",
                        reason="Same person must not approve both",
                    ),
                    actor,
                )
            return
        w.enqueue_export(
            c["id"],
            "0" * 64 if failure == "old_hash" else plan["plan_sha256"],
            DEMO_ACTORS["procurement"],
        )


def test_source_changed_during_analysis_discards_result(workflow):
    w = workflow
    run, snapshot = w.begin("LTB-2026-017", DEMO_ACTORS["planner"])
    case = w.get(snapshot.case_id, DEMO_ACTORS["planner"])
    replacement = snapshot.model_copy(deep=True)
    replacement.source_revision = 2
    w.replace_snapshot(
        snapshot.case_id, replacement, case["revision"], DEMO_ACTORS["planner"]
    )
    with pytest.raises(DomainError):
        asyncio.run(w.analyze(snapshot.case_id, run, snapshot))
    assert w.get(snapshot.case_id, DEMO_ACTORS["planner"])["plan"] is None


def test_model_failure_is_visible_and_never_auto_approved(workflow):
    class BrokenAnalyst:
        async def assess(self, *args):
            raise TimeoutError("Provider unavailable")

    w = workflow
    w.analyst = BrokenAnalyst()
    with pytest.raises(TimeoutError):
        analyzed(w)
    state = w.get("LTB-2026-017", DEMO_ACTORS["planner"])
    assert state["status"] == "ANALYSIS_FAILED" and state["plan"] is None


def test_durable_activity_retry_reuses_committed_result_after_restart(workflow):
    w = workflow
    run, snapshot = w.begin("LTB-2026-017", DEMO_ACTORS["planner"])
    first = asyncio.run(w.run_stage(snapshot.case_id, run, "engineering"))

    class MustNotRun:
        async def assess(self, *args):
            raise AssertionError("A completed activity must not call a model again")

    resumed = Workflow(w.store, MustNotRun(), w.erp, clock=lambda: FIXTURE_CLOCK)
    again = asyncio.run(resumed.run_stage(snapshot.case_id, run, "engineering"))
    assert first["result_sha256"] == again["result_sha256"] and again["reused"]


def test_finalization_is_idempotent_and_never_skips_missing_roles(workflow):
    w = workflow
    run, snapshot = w.begin("LTB-2026-017", DEMO_ACTORS["planner"])
    with pytest.raises(DomainError):
        w.finish_analysis(snapshot.case_id, run)
    for role in ("engineering", "service", "supply", "commitment"):
        asyncio.run(w.run_stage(snapshot.case_id, run, role))
    first = w.finish_analysis(snapshot.case_id, run)
    assert first == w.finish_analysis(snapshot.case_id, run)
    events = w.get(snapshot.case_id, DEMO_ACTORS["planner"])["audit"]
    assert sum(e["data"]["action"] == "ANALYSIS_COMPLETED" for e in events) == 1


def test_unresolved_review_cannot_receive_financial_approval(workflow):
    class ReviewAnalyst(TestAnalyst):
        async def assess(self, role, snapshot, calculation):
            result = await super().assess(role, snapshot, calculation)
            result["assessment"]["findings"] = [
                {"severity": "review", "summary": "Release authority needs resolution"}
            ]
            return result

    workflow.analyst = ReviewAnalyst()
    case = analyzed(workflow)
    assert case["status"] == "NEEDS_REVIEW"
    with pytest.raises(DomainError):
        approve_all(workflow, case["plan"])


def test_concurrent_events_with_unchanged_status_cannot_branch_audit(workflow):
    from sqlalchemy.orm.exc import StaleDataError

    from lastbuy.store import audit

    first = workflow.store.session()
    second = workflow.store.session()
    try:
        a = first.get(Case, "LTB-2026-017")
        b = second.get(Case, "LTB-2026-017")
        assert a.status == b.status == "DRAFT"
        audit(first, a, "test-one", "CONCURRENT_TEST", {})
        first.commit()
        with pytest.raises(StaleDataError):
            audit(second, b, "test-two", "CONCURRENT_TEST", {})
        second.rollback()
    finally:
        first.close()
        second.close()
    assert workflow.get("LTB-2026-017", DEMO_ACTORS["planner"])["audit_valid"]


@pytest.mark.parametrize("record", ["cohort", "coverage", "forecast", "stock", "quote"])
def test_wrong_system_cannot_supply_business_authority(workflow, record):
    snapshot = demo_snapshot()
    if record == "cohort":
        snapshot.cohorts[0].evidence = ["pcn"]
    if record == "coverage":
        snapshot.scenarios[0].demand[0].evidence = ["forecast"]
    if record == "forecast":
        snapshot.scenarios[0].demand[0].evidence = ["amendment"]
    if record == "stock":
        snapshot.lots[0].evidence = ["bom"]
    if record == "quote":
        snapshot.quote.evidence = ["stock"]
    case = workflow.get(snapshot.case_id, DEMO_ACTORS["planner"])
    snapshot.source_revision += 1
    workflow.replace_snapshot(
        snapshot.case_id, snapshot, case["revision"], DEMO_ACTORS["planner"]
    )
    with pytest.raises(DomainError, match="Source authority"):
        workflow.begin(snapshot.case_id, DEMO_ACTORS["planner"])
    assert workflow.get(snapshot.case_id, DEMO_ACTORS["planner"])["status"] == "DRAFT"


def test_cancelled_analysis_discards_late_result_and_cannot_approve(workflow):
    run, snapshot = workflow.begin("LTB-2026-017", DEMO_ACTORS["planner"])
    workflow.cancel_analysis(snapshot.case_id, DEMO_ACTORS["planner"])
    with pytest.raises(DomainError):
        workflow.stage(
            snapshot.case_id, run, "engineering", "COMPLETE", {"ignored": True}
        )
    workflow.fail_analysis(snapshot.case_id, run, "CancelledWorker")
    assert workflow.approval_status(snapshot.case_id, run)["status"] == "CANCELLED"
    assert workflow.get(snapshot.case_id, DEMO_ACTORS["planner"])["audit_valid"]
    with pytest.raises(DomainError):
        workflow.enqueue_export(snapshot.case_id, "a" * 64, DEMO_ACTORS["procurement"])


def test_approval_expiry_updates_state_and_is_idempotent(workflow):
    case = analyzed(workflow)
    result = workflow.expire_approval_wait(case["id"], case["analysis_id"])
    assert result["status"] == "APPROVAL_WAIT_EXPIRED"
    assert workflow.expire_approval_wait(case["id"], case["analysis_id"]) == result
    current = workflow.get(case["id"], DEMO_ACTORS["planner"])
    assert (
        len(
            [
                a
                for a in current["audit"]
                if a["data"]["action"] == "APPROVAL_WAIT_EXPIRED"
            ]
        )
        == 1
    )
    with pytest.raises(DomainError):
        approve_all(workflow, case["plan"])
    newer, _ = workflow.begin(case["id"], DEMO_ACTORS["planner"])
    assert (
        workflow.expire_approval_wait(case["id"], case["analysis_id"])["status"]
        == "STALE"
    )
    assert workflow.get(case["id"], DEMO_ACTORS["planner"])["analysis_id"] == newer


def test_approval_at_expiry_boundary_is_not_revoked(workflow):
    case = analyzed(workflow)
    approve_all(workflow, case["plan"])
    assert (
        workflow.expire_approval_wait(case["id"], case["analysis_id"])["status"]
        == "APPROVED"
    )


def test_restored_ledger_reconciles_external_write_newer_than_backup(
    workflow, tmp_path
):
    import sqlite3
    from pathlib import Path

    from lastbuy.store import Outbox

    case = analyzed(workflow)
    approve_all(workflow, case["plan"])
    job = workflow.enqueue_export(
        case["id"], case["plan"]["plan_sha256"], DEMO_ACTORS["procurement"]
    )
    restored_path = tmp_path / "restored.db"
    with sqlite3.connect(workflow.store.engine.url.database) as original:
        with sqlite3.connect(restored_path) as backup:
            original.backup(backup)
    receipt = workflow.dispatch(job["key"])
    restored = Workflow(
        Store("sqlite:///" + str(restored_path)),
        TestAnalyst(),
        SyntheticERP(workflow.erp.path),
        clock=lambda: FIXTURE_CLOCK,
    )
    with restored.store.session() as session:
        assert session.get(Outbox, job["key"]).status == "PENDING"
    assert restored.dispatch(job["key"]) == receipt
    state = restored.get(case["id"], DEMO_ACTORS["planner"])
    assert state["status"] == "EXPORTED" and state["audit_valid"]
    with sqlite3.connect(workflow.erp.path) as external:
        assert (
            external.execute(
                "SELECT count(*) FROM requisitions WHERE external_key=?", (job["key"],)
            ).fetchone()[0]
            == 1
        )
    import json

    Path("evidence/local-restore-verification.json").write_text(
        json.dumps(
            {
                "scope": "Actual SQLite backup/restore of synthetic decision ledger; independent ERP file retained. Model test double. Not Azure SQL PITR.",
                "restored_outbox_initial_status": "PENDING",
                "external_receipt_newer_than_backup": True,
                "reconciled_same_receipt": True,
                "external_rows": 1,
                "audit_chain_valid": True,
            },
            indent=2,
        )
    )
