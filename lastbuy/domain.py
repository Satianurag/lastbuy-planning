"""Versioned input contracts and canonical decision hashing.

All quantities are EACH; all currency amounts are integer minor units. Strings
are normalized to NFC for hashing. Floats are prohibited in hashed contracts.
"""

import hashlib
import json
import unicodedata
from datetime import UTC, date, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Quantity = Annotated[int, Field(strict=True, ge=0, le=10_000_000)]
Identifier = Annotated[str, Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,99}$")]
Role = Literal[
    "planner", "engineering", "service", "finance", "procurement", "ingester"
]
APPROVAL_ROLES = ("engineering", "service", "finance", "procurement")
POLICY_VERSION = "lastbuy-policy-3"


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


def now() -> datetime:
    return datetime.now(UTC)


def canonical(value) -> str:
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")

    def normalize(item):
        if isinstance(item, str):
            return unicodedata.normalize("NFC", item)
        if isinstance(item, float):
            raise ValueError("Floating point values are not allowed in decision hashes")
        if isinstance(item, dict):
            out = {normalize(k): normalize(v) for k, v in item.items()}
            if len(out) != len(item):
                raise ValueError("Canonical key collision")
            return out
        if isinstance(item, list | tuple):
            return [normalize(v) for v in item]
        return item

    return json.dumps(
        normalize(value),
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    )


def digest(value) -> str:
    return hashlib.sha256(canonical(value).encode()).hexdigest()


class Source(Contract):
    id: Identifier
    system: Literal[
        "SAP", "Windchill", "Dataverse", "Contracts", "Supplier", "Planning", "Depot"
    ]
    record_id: Identifier
    revision: Identifier
    effective_at: date
    observed_at: datetime
    locator: str = Field(min_length=1, max_length=300)
    text: str = Field(min_length=1, max_length=12000)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def valid_content(self):
        if hashlib.sha256(self.text.encode()).hexdigest() != self.sha256:
            raise ValueError("Evidence content does not match its SHA-256")
        if self.observed_at.tzinfo is None:
            raise ValueError("Observed timestamps require a timezone")
        return self


class Cohort(Contract):
    id: Identifier
    board_revision: Identifier
    firmware: Identifier
    serial_from: Identifier
    serial_to: Identifier
    compatible_revisions: list[Identifier] = Field(min_length=1)
    engineering_released: bool | None
    evidence: list[Identifier] = Field(min_length=1)


class Demand(Contract):
    cohort: Identifier
    due: date
    quantity: Quantity
    coverage_component: Identifier
    coverage_end: date
    signed_coverage: bool | None
    evidence: list[Identifier] = Field(min_length=1)


class Scenario(Contract):
    id: Identifier
    label: str = Field(max_length=120)
    approved: bool | None
    protected: bool = True
    demand: list[Demand] = Field(min_length=1, max_length=100)


class Lot(Contract):
    id: Identifier
    physical_id: Identifier
    kind: Literal["on_hand", "inbound"]
    owner: Identifier
    custodian: Identifier
    revision: Identifier | None
    quantity: Quantity
    reserved: Quantity = 0
    unit: Literal["EACH"] = "EACH"
    available: date
    expires: date | None = None
    quarantined: bool | None = False
    confirmed: bool | None = True
    evidence: list[Identifier] = Field(min_length=1)

    @model_validator(mode="after")
    def reservation(self):
        if self.reserved > self.quantity:
            raise ValueError("Reserved quantity exceeds physical quantity")
        return self


class Quote(Contract):
    revision: Identifier
    unit_price_minor: Annotated[int, Field(strict=True, gt=0, le=100_000_000)]
    currency: Literal["USD", "EUR", "GBP", "INR"]
    minimum: Quantity
    multiple: Annotated[int, Field(strict=True, gt=0, le=1_000_000)]
    max_quantity: Quantity
    available: date
    order_deadline: datetime
    evidence: list[Identifier] = Field(min_length=1)

    @model_validator(mode="after")
    def timezone_required(self):
        if self.order_deadline.tzinfo is None:
            raise ValueError("Order deadline requires a timezone")
        return self


class Snapshot(Contract):
    schema_version: Literal["1"] = "1"
    case_id: Identifier
    organization: Identifier
    material: Identifier
    title: str = Field(max_length=160)
    synthetic: bool
    source_revision: Annotated[int, Field(strict=True, ge=1)]
    complete: bool
    missing_sources: list[str] = Field(default_factory=list, max_length=30)
    baseline_quantity: Quantity
    cohorts: list[Cohort] = Field(min_length=1, max_length=30)
    scenarios: list[Scenario] = Field(min_length=1, max_length=20)
    lots: list[Lot] = Field(max_length=300)
    quote: Quote
    sources: list[Source] = Field(min_length=1, max_length=300)

    @model_validator(mode="after")
    def references(self):
        for items in (self.sources, self.cohorts, self.scenarios, self.lots):
            if len({x.id for x in items}) != len(items):
                raise ValueError("Record IDs must be unique within each collection")
        known = {x.id for x in self.sources}
        cohort_ids = {x.id for x in self.cohorts}
        objects = [*self.cohorts, *self.lots, self.quote]
        for scenario in self.scenarios:
            for demand in scenario.demand:
                if demand.cohort not in cohort_ids:
                    raise ValueError("Demand references an unknown cohort")
                objects.append(demand)
        if any(set(item.evidence) - known for item in objects):
            raise ValueError("Evidence reference does not resolve in this snapshot")
        if not any(s.protected for s in self.scenarios):
            raise ValueError("At least one protected demand scenario is required")
        return self


class EvidenceQuote(Contract):
    source_id: Identifier
    quote: str = Field(min_length=12, max_length=600)


class Finding(Contract):
    code: Identifier
    severity: Literal["blocker", "review", "info"]
    summary: str = Field(min_length=1, max_length=1200)
    evidence: list[Identifier] = Field(min_length=1, max_length=20)
    supporting_quotes: list[EvidenceQuote] = Field(min_length=1, max_length=5)


class EvidenceCheck(Contract):
    key: str = Field(min_length=1, max_length=180)
    observed_value: str | None = Field(max_length=100)
    supporting_quotes: list[EvidenceQuote] = Field(min_length=1, max_length=3)


class Assessment(Contract):
    role: Literal["engineering", "service", "supply", "commitment"]
    summary: str = Field(min_length=1, max_length=1600)
    findings: list[Finding] = Field(max_length=60)
    checks: list[EvidenceCheck] = Field(default_factory=list, max_length=40)
    evidence: list[Identifier] = Field(min_length=1, max_length=100)


class Actor(Contract):
    id: Identifier
    name: str
    organization: Identifier
    roles: list[Role]
    authority_minor: int = Field(ge=0)
    active: bool = True


class ApprovalRequest(Contract):
    plan_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    role: Role
    decision: Literal["approve", "reject"]
    reason: str = Field(min_length=8, max_length=1000)
