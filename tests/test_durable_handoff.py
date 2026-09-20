import asyncio

import pytest
from sqlalchemy import select

from lastbuy.durable_client import DurableDispatcher
from lastbuy.erp import SyntheticERP
from lastbuy.fixtures import DEMO_ACTORS, demo_snapshot
from lastbuy.service import Workflow
from lastbuy.store import OrchestrationMessage, Store


def test_uncertain_start_retries_same_persisted_instance_after_restart(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("LASTBUY_DURABLE_URL", "http://127.0.0.1:7071")
    store = Store("sqlite:///" + str(tmp_path / "handoff.db"))
    actor = DEMO_ACTORS["planner"]
    store.register(actor)
    workflow = Workflow(
        store, None, SyntheticERP(str(tmp_path / "erp.db")), durable=True
    )
    snapshot = demo_snapshot()
    workflow.create(snapshot, actor)
    run_id, _ = workflow.begin(snapshot.case_id, actor)
    received = []

    class Uncertain(DurableDispatcher):
        async def start(self, case_id, run):
            received.append(run)
            raise TimeoutError("The remote starter accepted but response was lost")

    with pytest.raises(TimeoutError):
        asyncio.run(Uncertain().relay(store))
    with store.session() as session:
        assert session.scalars(select(OrchestrationMessage)).one().status == "PENDING"

    class Recovered(DurableDispatcher):
        async def start(self, case_id, run):
            received.append(run)

    restarted = Store("sqlite:///" + str(tmp_path / "handoff.db"))
    asyncio.run(Recovered().relay(restarted))
    asyncio.run(Recovered().relay(restarted))
    assert received == [run_id, run_id]
    with restarted.session() as session:
        assert session.scalars(select(OrchestrationMessage)).one().status == "DELIVERED"
