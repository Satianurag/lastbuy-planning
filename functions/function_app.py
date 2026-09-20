"""Internal orchestration endpoints. Function keys stay on the API server."""

import asyncio
import json
import logging
import os
import uuid
from functools import lru_cache

import azure.durable_functions as df
import azure.functions as func

from lastbuy.archive import BlobArchive
from lastbuy.durable_client import NativeDurableDispatcher
from lastbuy.erp import SyntheticERP
from lastbuy.orchestration import lastbuy_orchestrator_v2
from lastbuy.orchestration_v1 import lastbuy_orchestrator
from lastbuy.remote import HostedAnalyst
from lastbuy.service import Workflow
from lastbuy.store import Case, Store

app = df.DFApp(http_auth_level=func.AuthLevel.FUNCTION)
app.orchestration_trigger(context_name="context")(lastbuy_orchestrator)
app.orchestration_trigger(context_name="context")(lastbuy_orchestrator_v2)


@lru_cache
def workflow():
    return Workflow(
        Store(os.environ["LASTBUY_DATABASE_URL"]),
        HostedAnalyst(),
        None
        if os.getenv("LASTBUY_ENABLE_WEB") == "1"
        else SyntheticERP(
            os.getenv("LASTBUY_SYNTHETIC_ERP_PATH", "data/synthetic-erp.db")
        ),
        archive=BlobArchive() if os.getenv("LASTBUY_ARCHIVE_URL") else None,
    )


@app.route(route="api/orchestrations/{run_id}", methods=["POST"])
@app.durable_client_input(client_name="client")
async def start(req: func.HttpRequest, client):
    try:
        run_id = str(uuid.UUID(req.route_params["run_id"]))
        case_id = req.get_json()["case_id"]
        with workflow().store.session() as session:
            case = session.get(Case, case_id)
            if case is None or case.analysis_id != run_id or case.status != "ANALYZING":
                return func.HttpResponse("Run is not active", status_code=409)
    except (ValueError, KeyError):
        return func.HttpResponse("Invalid run identifier", status_code=400)
    existing = await client.get_status(run_id)
    if existing is None or existing.runtime_status is None:
        await client.start_new(
            "lastbuy_orchestrator_v2",
            instance_id=run_id,
            client_input={"case_id": case_id, "run_id": run_id},
        )
    # Do not return the host's management URLs/function keys to a browser.
    return func.HttpResponse(
        json.dumps({"run_id": run_id, "accepted": True}),
        status_code=202,
        mimetype="application/json",
    )


@app.route(route="api/orchestrations/{run_id}/notify", methods=["POST"])
@app.durable_client_input(client_name="client")
async def notify(req: func.HttpRequest, client):
    try:
        run_id = str(uuid.UUID(req.route_params["run_id"]))
    except ValueError:
        return func.HttpResponse("Invalid run identifier", status_code=400)
    existing = await client.get_status(run_id)
    if existing is not None and existing.runtime_status is not None:
        await client.raise_event(
            run_id, "decision_changed", {"refresh_from_database": True}
        )
    return func.HttpResponse(status_code=204)


@app.activity_trigger(input_name="request")
async def analyze_stage(request):
    return await workflow().run_stage(
        request["case_id"], request["run_id"], request["role"]
    )


@app.activity_trigger(input_name="request")
def finalize_analysis(request):
    return workflow().finish_analysis(request["case_id"], request["run_id"])


@app.activity_trigger(input_name="request")
def read_approval_status(request):
    return workflow().approval_status(request["case_id"], request["run_id"])


@app.activity_trigger(input_name="request")
def expire_approval_wait(request):
    return workflow().expire_approval_wait(request["case_id"], request["run_id"])


@app.activity_trigger(input_name="request")
def record_analysis_failure(request):
    workflow().fail_analysis(
        request["case_id"], request["run_id"], "DurableActivityFailed"
    )
    state = workflow().approval_status(request["case_id"], request["run_id"])
    return (
        state
        if state["status"] in {"CANCELLED", "STALE"}
        else {"status": "ANALYSIS_FAILED"}
    )


if os.getenv("LASTBUY_ENABLE_WEB") == "1":
    from lastbuy.api import create_app

    @lru_cache
    def web_app():
        # FastAPI verifies Entra JWTs. No local personas are provisioned in cloud mode.
        return func.AsgiMiddleware(create_app(workflow=workflow(), demo=False))

    startup_lock = asyncio.Lock()
    startup_complete = False

    @app.route(
        route="{*route}",
        methods=["GET", "POST", "PUT", "OPTIONS"],
        auth_level=func.AuthLevel.ANONYMOUS,
    )
    @app.durable_client_input(client_name="client")
    async def web(req: func.HttpRequest, context: func.Context, client):
        global startup_complete
        if not startup_complete:
            async with startup_lock:
                if not startup_complete:
                    startup_complete = await web_app().notify_startup()
                    if not startup_complete:
                        return func.HttpResponse(
                            "Workspace is starting; retry shortly", status_code=503
                        )
        response = await web_app().handle_async(req, context)
        if req.method in {"POST", "PUT"}:
            try:
                await NativeDurableDispatcher(client).relay(workflow().store)
            except Exception as error:
                logging.warning(
                    "Persisted handoff awaits retry: %s", type(error).__name__
                )
        return response

    @app.timer_trigger(schedule="0 0 */2 * * *", arg_name="tick", run_on_startup=False)
    @app.durable_client_input(client_name="client")
    async def recover_handoffs(tick: func.TimerRequest, client):
        await NativeDurableDispatcher(client).relay(workflow().store)
