"""Regression of observed provider output plus connection-only retry boundaries."""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from lastbuy.domain import Assessment, Snapshot
from lastbuy.evidence_time import historical_numeric_support, historical_plan_checks
from lastbuy.reconciliation import reconcile
from lastbuy.sql_connect import connect_with_retry

ROOT = Path(__file__).parents[1]


def test_actual_live_historical_balance_response_is_blocked():
    manifest = json.loads(
        (ROOT / "evaluations/live-acceptance-20260920.json").read_text()
    )
    live = json.loads((ROOT / "evidence/live-acceptance-novel.json").read_text())
    snapshot = Snapshot.model_validate(manifest["novel"]["snapshot"])
    assessment = Assessment.model_validate(live["result"]["assessment"])
    fixed = reconcile(assessment, snapshot)
    assert any(
        f.code == "HISTORICAL_SOURCE_FACT" and f.severity == "blocker"
        for f in fixed.findings
    )
    assert reconcile(fixed, snapshot) == fixed
    assert historical_plan_checks({"assessments": [live["result"]]}, snapshot) == [
        "SAP-01:quantity"
    ]


@pytest.mark.parametrize(
    "text,quote,value,blocked",
    [
        ("Opening balance was 6,000. Current balance is 4,800.", "6,000", "6000", True),
        ("Prior quantity: 6000; revised balance: 4800.", "6000", "6000", True),
        (
            "Opening balance was 6,000. Current balance is 4,800.",
            "4,800",
            "4800",
            False,
        ),
        (
            "Opening balance was 6,000, current balance is 4,800.",
            "4,800",
            "4800",
            False,
        ),
        (
            "LOT-A opening balance was 6,000. LOT-B has 2,000 units.",
            "2,000",
            "2000",
            False,
        ),
    ],
)
def test_currentness_uses_full_source_context(text, quote, value, blocked):
    assert (
        historical_numeric_support(
            {
                "observed_value": value,
                "supporting_quotes": [{"source_id": "stock", "quote": quote}],
            },
            {"stock": text},
        )
        is blocked
    )


@pytest.mark.parametrize("state,expected_calls", [("HYT00", 2), ("28000", 1)])
def test_connection_retry_does_not_retry_authentication_errors(
    monkeypatch, state, expected_calls
):
    calls = []

    def connect(*args, **kwargs):
        calls.append(1)
        if len(calls) == 1:
            raise RuntimeError(state, "Connection failed")
        return "connected"

    monkeypatch.setattr("lastbuy.sql_connect.time.sleep", lambda _: None)
    dbapi = SimpleNamespace(connect=connect, Error=RuntimeError)
    if state == "28000":
        with pytest.raises(RuntimeError):
            connect_with_retry(dbapi, [], {})
    else:
        assert connect_with_retry(dbapi, [], {}) == "connected"
    assert len(calls) == expected_calls


def test_connection_retry_is_bounded(monkeypatch):
    calls = []

    def connect(*args, **kwargs):
        calls.append(1)
        raise RuntimeError("HYT00")

    monkeypatch.setattr("lastbuy.sql_connect.time.sleep", lambda _: None)
    with pytest.raises(RuntimeError):
        connect_with_retry(SimpleNamespace(connect=connect, Error=RuntimeError), [], {})
    assert len(calls) == 2


def test_actual_provider_failure_stops_plan_finalization_and_approval():
    from lastbuy.domain import ApprovalRequest
    from lastbuy.fixtures import DEMO_ACTORS
    from lastbuy.service import DomainError, Workflow
    from lastbuy.store import Case, Store

    manifest = json.loads(
        (ROOT / "evaluations/live-acceptance-20260920.json").read_text()
    )
    live = json.loads((ROOT / "evidence/live-acceptance-novel.json").read_text())
    original = json.loads((ROOT / "evidence/full-cloud-release7.json").read_text())
    snapshot = Snapshot.model_validate(manifest["novel"]["snapshot"])
    store = Store("sqlite:///:memory:")
    for actor in DEMO_ACTORS.values():
        store.register(actor)
    w = Workflow(store, None, None)
    w.create(snapshot, DEMO_ACTORS["planner"])
    run, snapshot = w.begin(snapshot.case_id, DEMO_ACTORS["planner"])
    for stage in original["stages"]:
        result = live["result"] if stage["role"] == "supply" else stage["result"]
        w.stage(snapshot.case_id, run, stage["role"], "COMPLETE", result)
    result = w.finish_analysis(snapshot.case_id, run)
    assert result["status"] == "NEEDS_REVIEW"
    with pytest.raises(DomainError, match="not accepting approvals"):
        w.approve(
            snapshot.case_id,
            ApprovalRequest(
                plan_sha256=result["plan_sha256"],
                role="engineering",
                decision="approve",
                reason="Attempting approval of captured historical fact",
            ),
            DEMO_ACTORS["engineering"],
        )
    with store.session() as session:
        case = session.get(Case, snapshot.case_id)
        assert any("historical quantities" in b for b in case.plan["blockers"])
