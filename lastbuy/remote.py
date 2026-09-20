"""Authenticated transport to the deployed Foundry analysis service."""

import asyncio
import os
import uuid
from urllib.parse import quote

import httpx
from azure.ai.projects import AIProjectClient, models
from azure.core.exceptions import HttpResponseError, ResourceNotFoundError
from azure.identity import AzureCliCredential, DefaultAzureCredential

from .agents import ROLES, validate_assessment
from .budget import BudgetGuard
from .domain import Assessment, digest
from .reconciliation import reconcile
from .solver import verify_solution


class HostedAnalyst:
    def ensure_run_allowance(self):
        BudgetGuard().ensure_run_allowance()

    async def assess(self, role, snapshot, calculation):
        budget = BudgetGuard()
        attempt_id = budget.reserve(snapshot.case_id, role)
        completed = None
        endpoint = os.environ["FOUNDRY_PROJECT_ENDPOINT"].rstrip("/")
        name = os.getenv("LASTBUY_HOSTED_AGENT", "lastbuy-analysis")
        version = os.environ["LASTBUY_HOSTED_VERSION"]
        session_id = str(
            uuid.uuid5(
                uuid.NAMESPACE_URL, f"{endpoint}/{name}/{version}/{digest(snapshot)}"
            )
        )
        url = (
            endpoint
            + "/agents/"
            + quote(name, safe="")
            + "/endpoint/protocols/invocations?api-version=v1"
            + "&agent_session_id="
            + session_id
        )
        credential = (
            AzureCliCredential(process_timeout=60)
            if os.getenv("LASTBUY_LOCAL_PROBE") == "1"
            else DefaultAzureCredential()
        )
        try:

            def ensure_session():
                with AIProjectClient(
                    endpoint=endpoint, credential=credential
                ) as project:
                    try:
                        session = project.agents.get_session(
                            agent_name=name, session_id=session_id
                        )
                    except ResourceNotFoundError:
                        try:
                            session = project.agents.create_session(
                                agent_name=name,
                                agent_session_id=session_id,
                                version_indicator=models.VersionRefIndicator(
                                    agent_version=version
                                ),
                            )
                        except HttpResponseError as error:
                            if error.status_code != 409:
                                raise
                            session = project.agents.get_session(
                                agent_name=name, session_id=session_id
                            )
                    if session.version_indicator.agent_version != version:
                        raise ValueError(
                            "Session does not pin the required hosted release"
                        )

            await asyncio.to_thread(ensure_session)
            token = await asyncio.to_thread(
                credential.get_token, "https://ai.azure.com/.default"
            )
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(180, connect=15)
            ) as client:
                response = await client.post(
                    url,
                    headers={"Authorization": "Bearer " + token.token},
                    json={"role": role, "snapshot": snapshot.model_dump(mode="json")},
                )
                response.raise_for_status()
                data = response.json()
            if (
                data.get("snapshot_sha256") != digest(snapshot)
                or data.get("role") != role
            ):
                raise ValueError(
                    "Hosted response does not match the requested snapshot and stage"
                )
            result = data["result"]
            sources = [
                s.model_dump(mode="json")
                for s in snapshot.sources
                if s.system in ROLES[role][1]
            ]
            validate_assessment(
                Assessment.model_validate(result["assessment"]),
                role,
                sources,
                calculation,
            )
            result["assessment"] = reconcile(
                Assessment.model_validate(result["assessment"]), snapshot
            ).model_dump(mode="json")
            if not result.get("tool_calls") or result.get("source") != "live-foundry":
                raise ValueError(
                    "Hosted stage did not return live tool execution evidence"
                )
            if (
                role == "commitment"
                and calculation.get("purchase_quantity") is not None
            ):
                verify_solution(snapshot, data["calculation"])
                if (
                    data["calculation"]["purchase_quantity"]
                    != calculation["purchase_quantity"]
                ):
                    raise ValueError(
                        "Remote and local deterministic verifiers disagree"
                    )
            completed = {
                **result,
                "transport": "foundry-hosted",
                "agent": name,
                "agent_version": version,
                "agent_session_id": session_id,
            }
            return completed
        finally:
            try:
                budget.finish(attempt_id, completed)
            finally:
                credential.close()
