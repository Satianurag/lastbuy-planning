"""Transactional records; SQLite for local development, SQLAlchemy for SQL Server."""

import os
import struct
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import JSON, ForeignKey, Integer, String, create_engine, event, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from sqlalchemy.pool import NullPool, StaticPool

from .domain import Actor, digest, now
from .sql_connect import connect_with_retry


class Base(DeclarativeBase):
    pass


class Case(Base):
    __tablename__ = "cases"
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    organization: Mapped[str] = mapped_column(String(100), index=True)
    revision: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="DRAFT")
    snapshot: Mapped[dict] = mapped_column(JSON)
    plan: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    stages: Mapped[list] = mapped_column(JSON, default=list)
    analysis_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    analysis_started: Mapped[str | None] = mapped_column(String(50), nullable=True)
    __mapper_args__ = {"version_id_col": revision}


class PlanVersion(Base):
    __tablename__ = "plan_versions"
    hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id"), index=True)
    payload: Mapped[dict] = mapped_column(JSON)
    snapshot: Mapped[dict] = mapped_column(JSON)


class Person(Base):
    __tablename__ = "people"
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    data: Mapped[dict] = mapped_column(JSON)


class Approval(Base):
    __tablename__ = "approvals"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id"), index=True)
    plan_hash: Mapped[str] = mapped_column(String(64), index=True)
    data: Mapped[dict] = mapped_column(JSON)


class Audit(Base):
    __tablename__ = "audit"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id"), index=True)
    sequence: Mapped[int] = mapped_column(Integer)
    data: Mapped[dict] = mapped_column(JSON)


class Outbox(Base):
    __tablename__ = "outbox"
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id"), index=True)
    status: Mapped[str] = mapped_column(String(30))
    payload: Mapped[dict] = mapped_column(JSON)
    receipt: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class OrchestrationMessage(Base):
    __tablename__ = "orchestration_messages"
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id"), index=True)
    run_id: Mapped[str] = mapped_column(String(100))
    operation: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), default="PENDING", index=True)


class BudgetAccount(Base):
    __tablename__ = "budget_accounts"
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    limit_paise: Mapped[int] = mapped_column(Integer)
    reserved_paise: Mapped[int] = mapped_column(Integer)


class BudgetAttempt(Base):
    __tablename__ = "budget_attempts"
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    account: Mapped[str] = mapped_column(ForeignKey("budget_accounts.id"))
    data: Mapped[dict] = mapped_column(JSON)


class Store:
    def __init__(self, url="sqlite:///data/lastbuy.db", initialize=None):
        if url.startswith("sqlite") and ":memory:" not in url:
            Path("data").mkdir(exist_ok=True)
        options = {"pool_pre_ping": True}
        if url.startswith("sqlite"):
            options["connect_args"] = {"check_same_thread": False, "timeout": 30}
            if ":memory:" in url:
                options["poolclass"] = StaticPool
        elif url.startswith("mssql+pyodbc"):
            # Leave no idle connections preventing the free serverless DB from pausing.
            options["poolclass"] = NullPool
        self.engine = create_engine(url, **options)
        if url.startswith("mssql+pyodbc"):
            from azure.identity import AzureCliCredential, DefaultAzureCredential

            credential = (
                AzureCliCredential(process_timeout=60)
                if os.getenv("LASTBUY_LOCAL_PROBE") == "1"
                else DefaultAzureCredential()
            )

            @event.listens_for(self.engine, "do_connect")
            def access_token(dialect, connection_record, cargs, cparams):
                cargs[0] = cargs[0].replace(";Trusted_Connection=Yes", "")
                raw = credential.get_token(
                    "https://database.windows.net/.default"
                ).token.encode("utf-16-le")
                cparams["attrs_before"] = {
                    1256: struct.pack(f"<I{len(raw)}s", len(raw), raw)
                }
                return connect_with_retry(dialect.loaded_dbapi, cargs, cparams)

        if url.startswith("sqlite"):

            @event.listens_for(self.engine, "connect")
            def pragmas(connection, _):
                connection.execute("PRAGMA foreign_keys=ON")
                connection.execute("PRAGMA journal_mode=WAL")

        if initialize is True or (
            initialize is None and os.getenv("LASTBUY_SCHEMA_MODE", "auto") == "auto"
        ):
            Base.metadata.create_all(self.engine)
        self.session = sessionmaker(self.engine, expire_on_commit=False)

    @contextmanager
    def transaction(self):
        with self.session.begin() as session:
            yield session

    def register(self, actor: Actor):
        with self.transaction() as session:
            old = session.get(Person, actor.id)
            if old is None:
                session.add(Person(id=actor.id, data=actor.model_dump(mode="json")))

    def actor(self, actor_id: str) -> Actor | None:
        with self.session() as session:
            person = session.get(Person, actor_id)
            return Actor.model_validate(person.data) if person else None


def audit(session, case: Case, actor: str, action: str, detail: dict):
    # Every audit append must take the case CAS, even when status stays unchanged
    # (e.g. the second and third human approvals both remain APPROVAL_PENDING).
    # Otherwise two transactions can append different events at the same sequence.
    case.revision = (case.revision or 0) + 1
    session.flush()
    previous = session.scalars(
        select(Audit)
        .where(Audit.case_id == case.id)
        .order_by(Audit.sequence.desc())
        .limit(1)
    ).first()
    payload = {
        "case_id": case.id,
        "sequence": previous.sequence + 1 if previous else 1,
        "at": now().isoformat(),
        "actor": actor,
        "action": action,
        "detail": detail,
        "previous_hash": previous.id if previous else "0" * 64,
    }
    session.add(
        Audit(
            id=digest(payload),
            case_id=case.id,
            sequence=payload["sequence"],
            data=payload,
        )
    )


def verify_audit(rows: list[dict]) -> bool:
    previous = "0" * 64
    for index, row in enumerate(rows, 1):
        data = row["data"]
        if (
            data["sequence"] != index
            or data["previous_hash"] != previous
            or digest(data) != row["hash"]
        ):
            return False
        previous = row["hash"]
    return True
