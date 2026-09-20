"""Authoritative workflow, human authorization, immutable decisions and outbox."""

import asyncio
import uuid
from datetime import datetime, timedelta

from sqlalchemy import select

from .agents import ROLES
from .domain import (
    APPROVAL_ROLES,
    POLICY_VERSION,
    Actor,
    ApprovalRequest,
    Snapshot,
    digest,
    now,
)
from .solver import solve, verify_solution
from .store import (
    Approval,
    Audit,
    Case,
    OrchestrationMessage,
    Outbox,
    Person,
    PlanVersion,
    Store,
    audit,
    verify_audit,
)


class DomainError(Exception):
    def __init__(self, message, status=409):
        self.message, self.status = message, status


class Workflow:
    def __init__(
        self, store: Store, analyst, erp, clock=now, durable=False, archive=None
    ):
        self.store, self.analyst, self.erp, self.clock = store, analyst, erp, clock
        self.durable = durable
        self.archive = archive

    def orchestration_message(self, session, case, operation):
        if self.durable and case.analysis_id:
            session.add(
                OrchestrationMessage(
                    id=str(uuid.uuid4()),
                    case_id=case.id,
                    run_id=case.analysis_id,
                    operation=operation,
                    status="PENDING",
                )
            )

    def require(self, actor: Actor, role: str | None = None):
        current = self.store.actor(actor.id)
        if (
            current is None
            or not current.active
            or current.organization != actor.organization
        ):
            raise DomainError("Identity is inactive or not provisioned", 403)
        if role and role not in current.roles:
            raise DomainError(f"The {role} role is required", 403)
        return current

    def case(self, session, case_id, actor):
        self.require(actor)
        case = session.get(Case, case_id)
        if case is None or case.organization != actor.organization:
            raise DomainError("Case not found", 404)
        return case

    def create(self, snapshot: Snapshot, actor: Actor):
        self.require(actor, "planner")
        if snapshot.organization != actor.organization:
            raise DomainError("Cannot create a case outside your organization", 403)
        with self.store.transaction() as session:
            if session.get(Case, snapshot.case_id):
                raise DomainError("Case already exists")
            case = Case(
                id=snapshot.case_id,
                organization=actor.organization,
                snapshot=snapshot.model_dump(mode="json"),
                status="DRAFT",
                stages=[],
            )
            session.add(case)
            audit(
                session,
                case,
                actor.id,
                "CASE_CREATED",
                {"snapshot_sha256": digest(snapshot), "synthetic": snapshot.synthetic},
            )
        return self.get(snapshot.case_id, actor)

    def listing(self, actor):
        self.require(actor)
        with self.store.session() as session:
            return [
                {
                    "id": c.id,
                    "title": c.snapshot["title"],
                    "status": c.status,
                    "revision": c.revision,
                    "material": c.snapshot["material"],
                    "synthetic": c.snapshot["synthetic"],
                    "plan": c.plan,
                }
                for c in session.scalars(
                    select(Case)
                    .where(Case.organization == actor.organization)
                    .order_by(Case.id)
                )
            ]

    def get(self, case_id, actor):
        with self.store.session() as session:
            case = self.case(session, case_id, actor)
            approvals = [
                a.data
                for a in session.scalars(
                    select(Approval).where(Approval.case_id == case.id)
                )
            ]
            events = [
                {"hash": a.id, "data": a.data}
                for a in session.scalars(
                    select(Audit)
                    .where(Audit.case_id == case.id)
                    .order_by(Audit.sequence)
                )
            ]
            exports = [
                {"key": e.key, "status": e.status, "receipt": e.receipt}
                for e in session.scalars(
                    select(Outbox).where(Outbox.case_id == case.id)
                )
            ]
            return {
                "id": case.id,
                "analysis_id": case.analysis_id,
                "revision": case.revision,
                "status": case.status,
                "snapshot": case.snapshot,
                "snapshot_sha256": digest(case.snapshot),
                "plan": case.plan,
                "stages": case.stages,
                "approvals": approvals,
                "audit": events,
                "audit_valid": verify_audit(events),
                "exports": exports,
            }

    def replace_snapshot(
        self, case_id, snapshot: Snapshot, expected_revision: int, actor: Actor
    ):
        self.require(actor, "planner")
        with self.store.transaction() as session:
            case = self.case(session, case_id, actor)
            if case.revision != expected_revision:
                raise DomainError("Case changed; reload before editing")
            if case.status in {"EXPORT_PENDING", "EXPORT_UNCERTAIN", "EXPORTED"}:
                raise DomainError(
                    "Export has started; reconcile it before opening a superseding case"
                )
            if (
                snapshot.case_id != case.id
                or snapshot.organization != case.organization
                or snapshot.source_revision <= case.snapshot["source_revision"]
            ):
                raise DomainError("Source identity/revision is invalid")
            case.snapshot = snapshot.model_dump(mode="json")
            case.status = "STALE" if case.plan else "DRAFT"
            self.orchestration_message(session, case, "notify")
            case.analysis_id = None
            case.stages = []
            audit(
                session,
                case,
                actor.id,
                "SOURCE_CHANGED_APPROVALS_INVALIDATED",
                {
                    "snapshot_sha256": digest(snapshot),
                    "source_revision": snapshot.source_revision,
                },
            )
        return self.get(case_id, actor)

    def begin(self, case_id, actor):
        self.require(actor, "planner")
        if hasattr(self.analyst, "ensure_run_allowance"):
            self.analyst.ensure_run_allowance()
        with self.store.transaction() as session:
            case = self.case(session, case_id, actor)
            if case.status in {
                "ANALYZING",
                "EXPORT_PENDING",
                "EXPORT_UNCERTAIN",
                "EXPORTED",
            }:
                raise DomainError(
                    "Case cannot start another analysis in its current state"
                )
            run_id = str(uuid.uuid4())
            case.status, case.analysis_id = "ANALYZING", run_id
            case.analysis_started = self.clock().isoformat()
            case.stages = [{"role": role, "status": "QUEUED"} for role in ROLES]
            self.orchestration_message(session, case, "start")
            audit(
                session,
                case,
                actor.id,
                "ANALYSIS_STARTED",
                {"run_id": run_id, "snapshot_sha256": digest(case.snapshot)},
            )
            return run_id, Snapshot.model_validate(case.snapshot)

    def stage(self, case_id, run_id, role, status, result=None):
        with self.store.transaction() as session:
            case = session.get(Case, case_id)
            if not case or case.analysis_id != run_id or case.status != "ANALYZING":
                raise DomainError("Analysis superseded by another case version")
            case.stages = [
                {
                    "role": role,
                    "status": status,
                    **({"result": result} if result else {}),
                }
                if x["role"] == role
                else x
                for x in case.stages
            ]

    async def run_stage(self, case_id, run_id, role):
        """Durable activity: reuse a committed result after retry or process restart."""
        if role not in ROLES:
            raise DomainError("Unknown specialist")
        with self.store.session() as session:
            case = session.get(Case, case_id)
            if not case or case.analysis_id != run_id or case.status != "ANALYZING":
                raise DomainError("Analysis superseded by another case version")
            stage = next(s for s in case.stages if s["role"] == role)
            if stage["status"] == "COMPLETE":
                return {
                    "role": role,
                    "result_sha256": digest(stage["result"]),
                    "reused": True,
                }
            snapshot = Snapshot.model_validate(case.snapshot)
        calculation = await asyncio.to_thread(solve, snapshot, self.clock())
        self.stage(case_id, run_id, role, "RUNNING")
        result = await self.analyst.assess(role, snapshot, calculation)
        self.stage(case_id, run_id, role, "COMPLETE", result)
        return {"role": role, "result_sha256": digest(result), "reused": False}

    def finish_analysis(self, case_id, run_id):
        """Idempotent finalization; orchestration history carries only IDs/hashes."""
        with self.store.session() as session:
            case = session.get(Case, case_id)
            if not case or case.analysis_id != run_id:
                raise DomainError("Analysis superseded")
            if (
                case.plan
                and case.plan.get("run_id") == run_id
                and case.status != "ANALYZING"
            ):
                return {"status": case.status, "plan_sha256": case.plan["plan_sha256"]}
            if (
                case.status != "ANALYZING"
                or len(case.stages) != len(ROLES)
                or any(s["status"] != "COMPLETE" for s in case.stages)
            ):
                raise DomainError("Not all specialist activities are complete")
            snapshot = Snapshot.model_validate(case.snapshot)
            results = [s["result"] for s in case.stages]
        calculation = solve(snapshot, self.clock())
        model_blockers = [
            f["summary"]
            for r in results
            for f in r["assessment"]["findings"]
            if f["severity"] in {"blocker", "review"}
        ]
        plan = {
            **calculation,
            "assessments": results,
            "run_id": run_id,
            "created_at": self.clock().isoformat(),
            "required_approvals": list(APPROVAL_ROLES),
        }
        if self.archive:
            plan["snapshot_archive"] = self.archive.put(snapshot)
        plan["blockers"] = [*plan["blockers"], *model_blockers]
        if model_blockers:
            plan["status"] = "NEEDS_REVIEW"
        plan["plan_sha256"] = digest(plan)
        with self.store.transaction() as session:
            case = session.get(Case, case_id)
            if (
                case.analysis_id != run_id
                or digest(case.snapshot) != digest(snapshot)
                or case.status != "ANALYZING"
            ):
                raise DomainError("Source changed during analysis; result discarded")
            case.plan, case.status = plan, plan["status"]
            session.add(
                PlanVersion(
                    hash=plan["plan_sha256"],
                    case_id=case_id,
                    payload=plan,
                    snapshot=snapshot.model_dump(mode="json"),
                )
            )
            audit(
                session,
                case,
                "analysis-worker",
                "ANALYSIS_COMPLETED",
                {
                    "run_id": run_id,
                    "plan_sha256": plan["plan_sha256"],
                    "status": case.status,
                },
            )
        return {"status": plan["status"], "plan_sha256": plan["plan_sha256"]}

    def fail_analysis(self, case_id, run_id, error_type):
        with self.store.transaction() as session:
            case = session.get(Case, case_id)
            if case and case.analysis_id == run_id and case.status == "ANALYZING":
                case.status = "ANALYSIS_FAILED"
                case.stages = [
                    {**s, "status": "FAILED", "error": error_type}
                    if s["status"] == "RUNNING"
                    else s
                    for s in case.stages
                ]
                audit(
                    session,
                    case,
                    "analysis-worker",
                    "ANALYSIS_FAILED",
                    {"run_id": run_id, "error_type": error_type},
                )

    def approval_status(self, case_id, run_id):
        with self.store.session() as session:
            case = session.get(Case, case_id)
            if not case or case.analysis_id != run_id:
                return {"status": "STALE"}
            if case.status == "APPROVED":
                self._fresh(case)
                self._valid_approvals(session, case.plan)
            return {"status": case.status}

    async def analyze(self, case_id, run_id, snapshot):
        try:
            for role in ROLES:
                await self.run_stage(case_id, run_id, role)
            return self.finish_analysis(case_id, run_id)
        except Exception as error:
            self.fail_analysis(case_id, run_id, type(error).__name__)
            raise

    def _fresh(self, case):
        plan = case.plan
        if not plan or plan["input_snapshot_sha256"] != digest(case.snapshot):
            raise DomainError("Sources changed; analyze and approve a fresh plan")
        unhashed = {k: v for k, v in plan.items() if k != "plan_sha256"}
        if (
            digest(unhashed) != plan["plan_sha256"]
            or plan["policy_version"] != POLICY_VERSION
        ):
            raise DomainError("Plan integrity/policy check failed")
        if (
            datetime.fromisoformat(
                case.snapshot["quote"]["order_deadline"].replace("Z", "+00:00")
            )
            <= self.clock()
        ):
            raise DomainError("Supplier deadline expired")
        if plan["status"] != "READY_FOR_APPROVAL" or plan["blockers"]:
            raise DomainError("Unresolved blockers prevent purchase approval")
        verify_solution(Snapshot.model_validate(case.snapshot), plan)
        if self.archive:
            if not plan.get("snapshot_archive"):
                raise DomainError("An archived source snapshot is required")
            self.archive.verify(
                plan["snapshot_archive"], Snapshot.model_validate(case.snapshot)
            )
        return plan

    def approve(self, case_id, request: ApprovalRequest, actor: Actor):
        current = self.require(actor, request.role)
        if request.role not in APPROVAL_ROLES:
            raise DomainError("Planner cannot provide a release approval", 403)
        with self.store.transaction() as session:
            case = self.case(session, case_id, actor)
            if case.status not in {
                "READY_FOR_APPROVAL",
                "APPROVAL_PENDING",
                "APPROVED",
            }:
                raise DomainError("Case is not accepting approvals")
            plan = self._fresh(case)
            if plan["plan_sha256"] != request.plan_sha256:
                raise DomainError("Approval refers to a superseded plan")
            if (
                request.role in {"finance", "procurement"}
                and current.authority_minor < plan["commitment_minor"]
            ):
                raise DomainError("Commitment exceeds your authority", 403)
            approvals = list(
                session.scalars(
                    select(Approval).where(Approval.plan_hash == request.plan_sha256)
                )
            )
            if any(
                a.data["actor"] == actor.id and a.data["role"] != request.role
                for a in approvals
            ):
                raise DomainError("Separation of duties requires different people", 403)
            key = digest({"plan": request.plan_sha256, "role": request.role})
            existing = session.get(Approval, key)
            if existing:
                if (
                    existing.data["actor"] == actor.id
                    and existing.data["decision"] == request.decision
                ):
                    return existing.data
                raise DomainError("This role already recorded a decision")
            data = {
                **request.model_dump(),
                "actor": actor.id,
                "actor_name": actor.name,
                "snapshot_sha256": plan["input_snapshot_sha256"],
                "policy_version": POLICY_VERSION,
                "at": self.clock().isoformat(),
                "expires_at": (self.clock() + timedelta(hours=24)).isoformat(),
            }
            session.add(
                Approval(
                    id=key, case_id=case.id, plan_hash=request.plan_sha256, data=data
                )
            )
            accepted = {
                a.data["role"] for a in approvals if a.data["decision"] == "approve"
            }
            accepted.add(request.role)
            case.status = (
                "REJECTED"
                if request.decision == "reject"
                else (
                    "APPROVED"
                    if accepted == set(APPROVAL_ROLES)
                    else "APPROVAL_PENDING"
                )
            )
            audit(
                session,
                case,
                actor.id,
                "HUMAN_" + request.decision.upper(),
                {"role": request.role, "plan_sha256": request.plan_sha256},
            )
            self.orchestration_message(session, case, "notify")
            return data

    def _valid_approvals(self, session, plan):
        approvals = list(
            session.scalars(
                select(Approval).where(Approval.plan_hash == plan["plan_sha256"])
            )
        )
        roles, people = set(), set()
        for approval in approvals:
            a = approval.data
            person = session.get(Person, a["actor"])
            if not person:
                raise DomainError("An approver is no longer provisioned", 403)
            actor = Actor.model_validate(person.data)
            case = session.get(Case, approval.case_id)
            if (
                not actor.active
                or actor.organization != case.organization
                or a["role"] not in actor.roles
                or a["decision"] != "approve"
                or a["snapshot_sha256"] != plan["input_snapshot_sha256"]
                or a["policy_version"] != POLICY_VERSION
                or datetime.fromisoformat(a["expires_at"]) <= self.clock()
            ):
                raise DomainError(
                    "An approval expired or its authority was revoked", 403
                )
            if (
                a["role"] in {"finance", "procurement"}
                and actor.authority_minor < plan["commitment_minor"]
            ):
                raise DomainError("Approver financial authority has changed", 403)
            if actor.id in people:
                raise DomainError("Separation of duties violation", 403)
            people.add(actor.id)
            roles.add(a["role"])
        if roles != set(APPROVAL_ROLES):
            raise DomainError("All four approvals are required")

    def enqueue_export(self, case_id, plan_hash, actor):
        self.require(actor, "procurement")
        with self.store.transaction() as session:
            case = self.case(session, case_id, actor)
            if not case.plan or case.plan["plan_sha256"] != plan_hash:
                raise DomainError("Export refers to a superseded plan")
            key = digest(
                {
                    "case": case.id,
                    "plan": plan_hash,
                    "operation": "draft-requisition-v1",
                }
            )
            existing = session.get(Outbox, key)
            if existing:
                return {
                    "key": key,
                    "status": existing.status,
                    "receipt": existing.receipt,
                }
            if case.status != "APPROVED":
                raise DomainError("Case requires complete, current approvals")
            plan = self._fresh(case)
            self._valid_approvals(session, plan)
            payload = {
                "case_id": case.id,
                "organization": case.organization,
                "material": case.snapshot["material"],
                "quantity_each": plan["purchase_quantity"],
                "currency": plan["currency"],
                "amount_minor": plan["commitment_minor"],
                "plan_sha256": plan_hash,
                "synthetic": case.snapshot["synthetic"],
            }
            if not payload["synthetic"]:
                raise DomainError(
                    "A production ERP adapter has not been configured", 503
                )
            case.status = "EXPORT_PENDING"
            session.add(
                Outbox(key=key, case_id=case.id, status="PENDING", payload=payload)
            )
            audit(
                session,
                case,
                actor.id,
                "EXPORT_ENQUEUED",
                {"external_key": key, "plan_sha256": plan_hash},
            )
            return {"key": key, "status": "PENDING", "receipt": None}

    def dispatch(self, key, lose_response=False):
        """Worker boundary. Look up an uncertain external write before retrying it."""
        with self.store.session() as session:
            row = session.get(Outbox, key)
            if row is None:
                raise DomainError("Export job not found", 404)
            if row.status == "COMPLETE":
                return row.receipt
            payload, case_id = row.payload, row.case_id
        receipt = self.erp.lookup(key)
        if receipt is None:
            with self.store.session() as session:
                case = session.get(Case, case_id)
                plan = self._fresh(case)
                if plan["plan_sha256"] != payload["plan_sha256"]:
                    raise DomainError("Export plan changed")
                self._valid_approvals(session, plan)
            try:
                receipt = self.erp.create_draft(
                    key, payload, lose_response=lose_response
                )
            except TimeoutError:
                with self.store.transaction() as session:
                    row, case = session.get(Outbox, key), session.get(Case, case_id)
                    if row.status != "COMPLETE":
                        row.status, case.status = "UNCERTAIN", "EXPORT_UNCERTAIN"
                        audit(
                            session,
                            case,
                            "export-worker",
                            "EXPORT_RESPONSE_LOST",
                            {"external_key": key},
                        )
                return None
        if receipt["payload_sha256"] != digest(payload):
            raise DomainError(
                "External receipt payload does not match approved request"
            )
        with self.store.transaction() as session:
            row, case = session.get(Outbox, key), session.get(Case, case_id)
            if row.status != "COMPLETE":
                row.receipt, row.status, case.status = receipt, "COMPLETE", "EXPORTED"
                audit(
                    session,
                    case,
                    "export-worker",
                    "DRAFT_REQUISITION_RECONCILED",
                    {
                        "external_key": key,
                        "external_reference": receipt["external_reference"],
                    },
                )
        return receipt
