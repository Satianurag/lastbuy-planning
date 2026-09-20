"""Independent SQL-backed synthetic ERP for cloud recovery tests, never live SAP."""

from sqlalchemy import JSON, String
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from .domain import digest, now
from .store import Store


class ERPBase(DeclarativeBase):
    pass


class Requisition(ERPBase):
    __tablename__ = "synthetic_requisitions"
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    payload_hash: Mapped[str] = mapped_column(String(64))
    receipt: Mapped[dict] = mapped_column(JSON)


class SQLSyntheticERP:
    def __init__(self, url):
        self.store = Store(url, initialize=False)

    def lookup(self, key):
        with self.store.session() as session:
            row = session.get(Requisition, key)
            return row.receipt if row else None

    def create_draft(self, key, payload, lose_response=False):
        if payload.get("synthetic") is not True:
            raise ValueError(
                "The independent ERP simulator only accepts synthetic records"
            )
        receipt = {
            "external_reference": "SYN-CLOUD-PR-" + key[:12].upper(),
            "external_key": key,
            "status": "DRAFT_REQUISITION",
            "synthetic": True,
            "payload_sha256": digest(payload),
            "at": now().isoformat(),
        }
        try:
            with self.store.transaction() as session:
                session.add(
                    Requisition(key=key, payload_hash=digest(payload), receipt=receipt)
                )
        except IntegrityError:
            pass
        current = self.lookup(key)
        if not current or current["payload_sha256"] != digest(payload):
            raise ValueError("External key conflicts with a different approved payload")
        if lose_response:
            raise TimeoutError("Synthetic ERP accepted the draft; response lost")
        return current
