"""Server-only internal Durable starter/notification transport."""

import os
from urllib.parse import urlparse

import httpx
from sqlalchemy import select

from .store import Case, OrchestrationMessage


class DurableDispatcher:
    def __init__(self):
        self.url = os.environ["LASTBUY_DURABLE_URL"].rstrip("/")
        parsed = urlparse(self.url)
        if parsed.scheme != "https" and parsed.hostname not in {
            "localhost",
            "127.0.0.1",
            "::1",
        }:
            raise ValueError("Durable transport requires HTTPS outside loopback")
        self.headers = (
            {"x-functions-key": os.environ["LASTBUY_DURABLE_KEY"]}
            if os.getenv("LASTBUY_DURABLE_KEY")
            else {}
        )

    async def start(self, case_id, run_id):
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{self.url}/api/orchestrations/{run_id}",
                headers=self.headers,
                json={"case_id": case_id},
            )
            response.raise_for_status()
            return response.json()

    async def notify(self, run_id):
        if not run_id:
            return
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                f"{self.url}/api/orchestrations/{run_id}/notify", headers=self.headers
            )
            response.raise_for_status()

    async def relay(self, store):
        """At-least-once delivery; stable instance IDs make uncertain starts retryable."""
        with store.session() as session:
            pending = list(
                session.scalars(
                    select(OrchestrationMessage)
                    .where(OrchestrationMessage.status == "PENDING")
                    .limit(20)
                )
            )
        for message in pending:
            if message.operation == "start":
                with store.session() as session:
                    case = session.get(Case, message.case_id)
                    active = (
                        case
                        and case.analysis_id == message.run_id
                        and case.status == "ANALYZING"
                    )
                if active:
                    await self.start(message.case_id, message.run_id)
            else:
                await self.notify(message.run_id)
            with store.transaction() as session:
                current = session.get(OrchestrationMessage, message.id)
                current.status = "DELIVERED"


class NativeDurableDispatcher(DurableDispatcher):
    """Cloud host binding, avoiding self-HTTP calls and function-key storage."""

    def __init__(self, client):
        self.client = client

    async def start(self, case_id, run_id):
        current = await self.client.get_status(run_id)
        if current is None or current.runtime_status is None:
            await self.client.start_new(
                "lastbuy_orchestrator_v2",
                instance_id=run_id,
                client_input={"case_id": case_id, "run_id": run_id},
            )

    async def notify(self, run_id):
        current = await self.client.get_status(run_id)
        if current is not None and current.runtime_status is not None:
            await self.client.raise_event(
                run_id, "decision_changed", {"refresh_from_database": True}
            )
