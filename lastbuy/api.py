"""Authenticated decision API. Local demo personas are explicitly loopback-only."""

import asyncio
import hashlib
import logging
import os
import secrets
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

import jwt
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import StaleDataError
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .archive import BlobArchive
from .budget import BudgetExceeded
from .domain import POLICY_VERSION, Actor, ApprovalRequest, Contract, Snapshot
from .durable_client import DurableDispatcher
from .erp import SyntheticERP
from .fixtures import DEMO_ACTORS, demo_snapshot
from .http_limits import BodyLimitMiddleware
from .ingestion import compare_snapshots
from .market import market_reference
from .remote import HostedAnalyst
from .service import DomainError, Workflow
from .store import Case, Store, audit

LOG = logging.getLogger("lastbuy")
ROOT = Path(__file__).resolve().parents[1]


class PersonaRequest(Contract):
    persona: str


class SourceUpdate(Contract):
    expected_revision: int = Field(ge=1)
    snapshot: Snapshot


class ExportRequest(Contract):
    plan_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    simulate_lost_response: bool = False


def create_app(workflow=None, demo=None):
    demo = (
        demo
        if demo is not None
        else os.getenv("LASTBUY_AUTH_MODE", "entra") == "local-demo"
    )
    if workflow is None:
        store = Store(os.getenv("LASTBUY_DATABASE_URL", "sqlite:///data/lastbuy.db"))
        analyst = HostedAnalyst()
        workflow = Workflow(
            store,
            analyst,
            SyntheticERP(),
            archive=BlobArchive() if os.getenv("LASTBUY_ARCHIVE_URL") else None,
        )
    if demo:
        for actor in DEMO_ACTORS.values():
            workflow.store.register(actor)
        if not workflow.listing(DEMO_ACTORS["planner"]):
            workflow.create(demo_snapshot(), DEMO_ACTORS["planner"])
    tenant, audience = os.getenv("AZURE_TENANT_ID"), os.getenv("LASTBUY_API_AUDIENCE")
    if not demo and (not tenant or not audience):
        raise RuntimeError(
            "Entra tenant and API audience are required outside local demo mode"
        )
    jwks = (
        jwt.PyJWKClient(
            f"https://login.microsoftonline.com/{tenant}/discovery/v2.0/keys"
        )
        if not demo
        else None
    )
    tasks = set()
    analysis_slots = asyncio.Semaphore(1)
    dispatcher = DurableDispatcher() if os.getenv("LASTBUY_DURABLE_URL") else None
    workflow.durable = (
        dispatcher is not None or os.getenv("LASTBUY_DURABLE_IN_PROCESS") == "1"
    )

    async def relay_messages():
        while True:
            try:
                await dispatcher.relay(workflow.store)
            except Exception as error:
                LOG.warning("durable_relay_retry error_type=%s", type(error).__name__)
            await asyncio.sleep(5)

    @asynccontextmanager
    async def lifespan(app):
        # Local worker restart: interrupted runs are explicit and require retry.
        # Production orchestration will resume individual Durable activities.
        with workflow.store.transaction() as session:
            for case in session.scalars(select(Case)):
                if (
                    case.plan
                    and case.plan.get("policy_version") != POLICY_VERSION
                    and case.status
                    not in {"EXPORTED", "EXPORT_PENDING", "EXPORT_UNCERTAIN", "STALE"}
                ):
                    case.status = "STALE"
                    audit(
                        session,
                        case,
                        "policy-loader",
                        "POLICY_CHANGED_APPROVALS_INVALIDATED",
                        {"policy_version": POLICY_VERSION},
                    )
            for case in (
                []
                if workflow.durable
                else session.scalars(select(Case).where(Case.status == "ANALYZING"))
            ):
                case.status = "ANALYSIS_FAILED"
                case.stages = [
                    {**s, "status": "INTERRUPTED"}
                    if s["status"] in {"QUEUED", "RUNNING"}
                    else s
                    for s in case.stages
                ]
                audit(
                    session,
                    case,
                    "local-worker",
                    "PROCESS_RESTART_INTERRUPTED_ANALYSIS",
                    {},
                )
        relay_task = asyncio.create_task(relay_messages()) if dispatcher else None
        yield
        if relay_task:
            relay_task.cancel()
            await asyncio.gather(relay_task, return_exceptions=True)
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    app = FastAPI(title="LastBuy", version="0.1.0", lifespan=lifespan)
    app.add_middleware(BodyLimitMiddleware)
    app.state.workflow = workflow
    if demo:
        app.add_middleware(
            TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "[::1]"]
        )
        app.add_middleware(
            SessionMiddleware,
            secret_key=secrets.token_hex(32),
            same_site="strict",
            max_age=3600,
            https_only=False,
        )

    @app.middleware("http")
    async def boundaries(request, call_next):
        if demo and (
            not request.client or request.client.host not in {"127.0.0.1", "::1"}
        ):
            return JSONResponse(
                {"detail": "Local demo identities are only available on loopback"},
                status_code=403,
            )
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            origin = request.headers.get("origin")
            if demo and origin != str(request.base_url).rstrip("/"):
                return JSONResponse(
                    {"detail": "Same-origin request required"}, status_code=403
                )
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
            + (
                "connect-src 'self'; "
                if demo
                else "connect-src 'self' https://login.microsoftonline.com; frame-src https://login.microsoftonline.com; "
            )
            + "frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
        )
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.exception_handler(BudgetExceeded)
    async def budget_exceeded(request, error):
        return JSONResponse({"detail": str(error)}, status_code=503)

    @app.exception_handler(DomainError)
    async def domain_error(request, error):
        return JSONResponse({"detail": error.message}, status_code=error.status)

    @app.exception_handler(StaleDataError)
    @app.exception_handler(IntegrityError)
    async def concurrent_change(request, error):
        return JSONResponse(
            {
                "detail": "Concurrent update detected; reload and reconcile before retrying"
            },
            status_code=409,
        )

    def identity(request: Request) -> Actor:
        if demo:
            actor_id = request.session.get("actor")
            if request.method not in {
                "GET",
                "HEAD",
                "OPTIONS",
            } and not secrets.compare_digest(
                request.headers.get("x-csrf-token", ""),
                request.session.get("csrf", "invalid"),
            ):
                raise HTTPException(403, "CSRF token required")
        else:
            token = request.headers.get("authorization", "")
            if not token.startswith("Bearer "):
                raise HTTPException(401, "Entra access token required")
            try:
                key = jwks.get_signing_key_from_jwt(token[7:])
                claims = jwt.decode(
                    token[7:],
                    key.key,
                    algorithms=["RS256"],
                    audience=audience,
                    issuer=f"https://login.microsoftonline.com/{tenant}/v2.0",
                    options={"require": ["exp", "iat", "oid", "tid"]},
                )
                if claims["tid"] != tenant:
                    raise ValueError("Wrong tenant")
                if "access_as_user" not in claims.get("scp", "").split():
                    raise ValueError("A delegated LastBuy API scope is required")
                actor_id = claims["oid"]
            except (jwt.PyJWTError, ValueError):
                raise HTTPException(401, "Invalid Entra access token") from None
        actor = workflow.store.actor(actor_id) if actor_id else None
        if actor is None or not actor.active:
            raise HTTPException(401, "Sign in with a provisioned identity")
        return actor

    @app.get("/api/health")
    def health():
        return {
            "status": "ok",
            "auth_mode": "local-demo" if demo else "entra",
            "model": os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME", "lastbuy-dev-mini"),
        }

    @app.get("/api/market-prices")
    def public_market_prices(
        quantity: int = Query(default=250, ge=1, le=1_000_000),
        currency: str = Query(default="INR", pattern="^(USD|INR)$"),
    ):
        # Public, curated catalogue facts only. No tenant data or decision writes.
        return market_reference(quantity, currency)

    @app.get("/api/session")
    def session_info(request: Request):
        if demo:
            actor = workflow.store.actor(request.session.get("actor", ""))
            return {
                "mode": "local-demo",
                "actor": actor.model_dump() if actor and actor.active else None,
                "csrf": request.session.get("csrf"),
                "personas": [
                    {"key": k, **v.model_dump()} for k, v in DEMO_ACTORS.items()
                ],
            }
        return {
            "mode": "entra",
            "actor": identity(request).model_dump()
            if request.headers.get("authorization")
            else None,
        }

    @app.get("/api/auth/config")
    def auth_config():
        return {
            "mode": "local-demo" if demo else "entra",
            "tenant": tenant,
            "client_id": os.getenv("LASTBUY_SPA_CLIENT_ID"),
            "scope": os.getenv("LASTBUY_API_SCOPE"),
        }

    @app.post("/api/session")
    def demo_session(data: PersonaRequest, request: Request):
        if not demo:
            raise HTTPException(404)
        if data.persona not in DEMO_ACTORS:
            raise HTTPException(400, "Unknown demo persona")
        request.session.clear()
        request.session.update(
            {"actor": DEMO_ACTORS[data.persona].id, "csrf": secrets.token_hex(24)}
        )
        return session_info(request)

    @app.get("/api/cases")
    def cases(actor=Depends(identity)):
        return workflow.listing(actor)

    @app.get("/api/import/template")
    def template(actor=Depends(identity)):
        workflow.require(actor, "planner")
        if not demo:
            raise HTTPException(404)
        snapshot = demo_snapshot()
        snapshot.case_id = "LTB-" + uuid.uuid4().hex[:8].upper()
        return snapshot.model_dump(mode="json")

    @app.post("/api/import/preview")
    def preview(snapshot: Snapshot, actor=Depends(identity)):
        workflow.require(actor, "planner")
        if not demo or not snapshot.synthetic:
            raise HTTPException(
                403, "This import is for synthetic development records only"
            )
        if snapshot.organization != actor.organization:
            raise HTTPException(403, "Snapshot belongs to another organization")
        before, revision = None, None
        with workflow.store.session() as session:
            if session.get(Case, snapshot.case_id):
                case = workflow.case(session, snapshot.case_id, actor)
                before = Snapshot.model_validate(case.snapshot)
                revision = case.revision
                if snapshot.source_revision <= before.source_revision:
                    raise HTTPException(
                        409, "Replacement requires a newer source revision"
                    )
        return {
            **compare_snapshots(before, snapshot),
            "case_id": snapshot.case_id,
            "operation": "replace" if before else "create",
            "expected_revision": revision,
        }

    @app.get("/api/cases/{case_id}")
    def case(case_id: str, actor=Depends(identity)):
        return workflow.get(case_id, actor)

    def require_supported_snapshot(snapshot: Snapshot):
        if snapshot.synthetic:
            return
        if demo:
            raise HTTPException(400, "Local demo accepts only synthetic snapshots")
        raise HTTPException(
            403,
            "Customer-source adapters are not configured; this deployment accepts only explicitly synthetic snapshots",
        )

    @app.post("/api/cases", status_code=201)
    def create(snapshot: Snapshot, actor=Depends(identity)):
        if not demo:
            workflow.require(actor, "ingester")
        require_supported_snapshot(snapshot)
        return workflow.create(snapshot, actor)

    @app.put("/api/cases/{case_id}/snapshot")
    def update(case_id: str, data: SourceUpdate, actor=Depends(identity)):
        if not demo:
            workflow.require(actor, "ingester")
        require_supported_snapshot(data.snapshot)
        return workflow.replace_snapshot(
            case_id, data.snapshot, data.expected_revision, actor
        )

    async def run_analysis(case_id, run_id, snapshot):
        try:
            async with analysis_slots:
                await workflow.analyze(case_id, run_id, snapshot)
        except Exception as error:
            LOG.error(
                "analysis_failed case=%s run=%s error_type=%s",
                case_id,
                run_id,
                type(error).__name__,
            )

    @app.post("/api/cases/{case_id}/analyze", status_code=202)
    async def analyze(case_id: str, actor=Depends(identity)):
        if len(tasks) >= 3:
            raise HTTPException(
                429, "Analysis queue is full; wait for a current case to finish"
            )
        run_id, snapshot = workflow.begin(case_id, actor)
        if workflow.durable:
            return {
                "run_id": run_id,
                "status": "ANALYZING",
                "execution": "durable",
                "handoff": "persisted",
            }
        task = asyncio.create_task(run_analysis(case_id, run_id, snapshot))
        tasks.add(task)
        task.add_done_callback(tasks.discard)
        return {"run_id": run_id, "status": "ANALYZING"}

    @app.post("/api/cases/{case_id}/cancel")
    def cancel(case_id: str, actor=Depends(identity)):
        return workflow.cancel_analysis(case_id, actor)

    @app.post("/api/cases/{case_id}/approvals")
    def approve(case_id: str, data: ApprovalRequest, actor=Depends(identity)):
        return workflow.approve(case_id, data, actor)

    @app.post("/api/cases/{case_id}/export")
    def export(case_id: str, data: ExportRequest, actor=Depends(identity)):
        if data.simulate_lost_response and not demo:
            raise HTTPException(
                400, "Failure injection is only available in local demo"
            )
        job = workflow.enqueue_export(case_id, data.plan_sha256, actor)
        if os.getenv("LASTBUY_EXPORT_TRANSPORT") == "remote":
            from .export_client import dispatch_remote

            return dispatch_remote(job)
        if os.getenv("LASTBUY_EXPORT_TRANSPORT") == "outbox":
            return {
                "key": job["key"],
                "receipt": job["receipt"],
                "status": job["status"],
            }
        receipt = workflow.dispatch(
            job["key"], lose_response=data.simulate_lost_response
        )
        return {
            "key": job["key"],
            "receipt": receipt,
            "status": "COMPLETE" if receipt else "UNCERTAIN",
        }

    @app.post("/api/cases/{case_id}/demo-reservation")
    def change_stock(case_id: str, actor=Depends(identity)):
        if not demo:
            raise HTTPException(404)
        current = workflow.get(case_id, actor)
        snapshot = Snapshot.model_validate(current["snapshot"])
        lot = next((item for item in snapshot.lots if item.id == "SAP-01"), None)
        if not lot or lot.quantity - lot.reserved < 1000:
            raise HTTPException(
                400, "Demo needs at least 1,000 unreserved units in SAP-01"
            )
        lot.reserved += 1000
        snapshot.source_revision += 1
        for source in snapshot.sources:
            if source.id == "stock":
                # Construct the replacement atomically so hash validation stays valid.
                text = (
                    source.text
                    + f"\nSYNTHETIC UPDATED RESERVATION: LOT-01 now reserves {lot.reserved} EACH for another approved case. This replaces the prior no-reservations statement."
                )
                replacement = {
                    **source.model_dump(mode="json"),
                    "text": text,
                    "sha256": hashlib.sha256(text.encode()).hexdigest(),
                    "revision": str(int(source.revision) + 1),
                }
                snapshot.sources = [
                    type(source).model_validate(replacement) if s.id == source.id else s
                    for s in snapshot.sources
                ]
                break
        return workflow.replace_snapshot(case_id, snapshot, current["revision"], actor)

    @app.get("/api/cases/{case_id}/packet")
    def packet(case_id: str, actor=Depends(identity)):
        data = workflow.get(case_id, actor)
        return JSONResponse(
            data,
            headers={
                "Content-Disposition": f'attachment; filename="{case_id}-evidence.json"'
            },
        )

    app.mount("/assets", StaticFiles(directory=ROOT / "web"), name="assets")

    @app.get("/")
    def index():
        return FileResponse(ROOT / "web/index.html")

    return app
