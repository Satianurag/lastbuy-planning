"""Fail-closed checks of critical extracted facts against accepted structured inputs.

Extraction remains model-assisted and can be wrong. Exact quotes and deterministic
comparison reduce silent disagreements; they do not replace authorized reviewers.
"""

from decimal import Decimal, InvalidOperation

from .domain import Assessment, Finding, Snapshot


def critical_fields(role: str, snapshot: Snapshot) -> list[dict]:
    fields = []

    def add(key, record, field, expected, evidence, kind="text"):
        fields.append(
            dict(
                key=key,
                record=record,
                field=field,
                expected=str(expected).lower()
                if isinstance(expected, bool)
                else str(expected),
                evidence=evidence,
                kind=kind,
            )
        )

    if role == "engineering":
        for c in snapshot.cohorts:
            add(
                f"{c.id}:released",
                c.id,
                "engineering release approved (true/false)",
                c.engineering_released,
                c.evidence,
                "bool",
            )
    elif role == "service":
        for s in snapshot.scenarios:
            for index, d in enumerate(s.demand):
                key = f"{s.id}:{index}"
                add(
                    key + ":coverage",
                    d.cohort,
                    "component-specific coverage end YYYY-MM-DD",
                    d.coverage_end,
                    d.evidence,
                )
                add(
                    key + ":signed",
                    d.cohort,
                    "governing component-specific amendment signed (true/false)",
                    d.signed_coverage,
                    d.evidence,
                    "bool",
                )
                add(
                    key + ":demand",
                    d.cohort,
                    "approved demand quantity in EACH",
                    d.quantity,
                    d.evidence,
                    "number",
                )
    elif role == "supply":
        for lot in snapshot.lots:
            add(
                lot.id + ":quantity",
                lot.physical_id,
                "physical quantity in EACH before reservations",
                lot.quantity,
                lot.evidence,
                "number",
            )
            if lot.kind == "inbound":
                add(
                    lot.id + ":confirmed",
                    lot.physical_id,
                    "inbound delivery confirmed (true/false)",
                    lot.confirmed,
                    lot.evidence,
                    "bool",
                )
    elif role == "commitment":
        add(
            "quote:price",
            snapshot.material,
            "supplier unit price in major currency units (not cents)",
            Decimal(snapshot.quote.unit_price_minor) / 100,
            snapshot.quote.evidence,
            "number",
        )
        add(
            "quote:max",
            snapshot.material,
            "supplier maximum allocated quantity EACH",
            snapshot.quote.max_quantity,
            snapshot.quote.evidence,
            "number",
        )
    return fields


def extraction_requests(role: str, snapshot: Snapshot) -> list[dict]:
    # Expected values are deliberately excluded from the extraction checklist.
    return [
        {k: v for k, v in f.items() if k != "expected"}
        for f in critical_fields(role, snapshot)
    ]


def reconcile(assessment: Assessment, snapshot: Snapshot) -> Assessment:
    """Reject incomplete/unverifiable extraction; mismatches become server blockers."""
    expected = {f["key"]: f for f in critical_fields(assessment.role, snapshot)}
    checks = {c.key: c for c in assessment.checks}
    if len(checks) != len(assessment.checks) or checks.keys() != expected.keys():
        raise ValueError(
            "Critical evidence checks missing, duplicated or outside scope"
        )
    sources = {s.id: s.text for s in snapshot.sources}
    blockers = []
    for key, spec in expected.items():
        check = checks[key]
        if not check.supporting_quotes:
            raise ValueError("Critical check has no supporting source quote")
        for q in check.supporting_quotes:
            if (
                q.source_id not in spec["evidence"]
                or q.quote not in sources[q.source_id]
            ):
                raise ValueError(
                    "Critical check quote does not match its record authority"
                )
        observed = check.observed_value
        matches = (
            observed is not None
            and observed.strip().lower() == spec["expected"].lower()
        )
        if observed is not None and spec["kind"] == "number":
            try:
                matches = Decimal(observed.replace(",", "")) == Decimal(
                    spec["expected"]
                )
                # An extractor cannot copy the expected number without quoting that number.
                import re

                quote_numbers = [
                    Decimal(n.replace(",", ""))
                    for q in check.supporting_quotes
                    for n in re.findall(
                        r"(?<![\w.-])\d[\d,]*(?:\.\d+)?(?![\w-]|\.\d)", q.quote
                    )
                ]
                if Decimal(observed.replace(",", "")) not in quote_numbers:
                    raise ValueError(
                        "Extracted number is absent from its supporting quotation"
                    )
            except InvalidOperation as error:
                raise ValueError(
                    "Critical numeric extraction is not a number"
                ) from error
        if not matches:
            blockers.append(
                Finding(
                    code="SOURCE_FACT_CONFLICT",
                    severity="blocker",
                    summary=f"Source reconciliation requires review: {spec['record']} / {spec['field']}. Accepted input and extracted evidence disagree or the evidence is unsupported.",
                    evidence=list(
                        dict.fromkeys(q.source_id for q in check.supporting_quotes)
                    ),
                    supporting_quotes=check.supporting_quotes,
                )
            )
    result = assessment.model_copy(deep=True)
    # Idempotent: hosted and API boundary both independently reconcile.
    result.findings = [
        f for f in result.findings if f.code != "SOURCE_FACT_CONFLICT"
    ] + blockers
    return result
