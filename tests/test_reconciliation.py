import hashlib

import pytest

from lastbuy.domain import Assessment, EvidenceCheck, EvidenceQuote
from lastbuy.fixtures import demo_snapshot
from lastbuy.reconciliation import critical_fields, reconcile


def extraction(role, snapshot):
    fields = critical_fields(role, snapshot)
    return Assessment(
        role=role,
        summary="Test double extraction",
        findings=[],
        evidence=[snapshot.sources[0].id],
        checks=[
            EvidenceCheck(
                key=f["key"],
                observed_value=f["expected"],
                supporting_quotes=[
                    EvidenceQuote(
                        source_id=f["evidence"][0],
                        quote=next(
                            s.text for s in snapshot.sources if s.id == f["evidence"][0]
                        ),
                    )
                ],
            )
            for f in fields
        ],
    )


def test_critical_numeric_conflict_cannot_hide_behind_info_summary():
    s = demo_snapshot()
    a = extraction("supply", s)
    stock = next(x for x in s.sources if x.id == "stock")
    content = stock.text.replace("6,000 owned", "500 owned")
    stock = stock.model_copy(
        update={"text": content, "sha256": hashlib.sha256(content.encode()).hexdigest()}
    )
    s.sources = [stock if x.id == "stock" else x for x in s.sources]
    for c in a.checks:
        if c.supporting_quotes[0].source_id == "stock":
            c.supporting_quotes[0].quote = stock.text
    # False copied structured value is absent from the source and rejected.
    with pytest.raises(ValueError, match="absent"):
        reconcile(a, s)
    a.checks[0].observed_value = "500"
    result = reconcile(a, s)
    assert any(f.severity == "blocker" for f in result.findings)
    assert reconcile(result, s) == result


def test_release_conflict_forces_server_blocker():
    s = demo_snapshot()
    a = extraction("engineering", s)
    a.checks[0].observed_value = "false"
    assert reconcile(a, s).findings[0].severity == "blocker"


@pytest.mark.parametrize(
    "mutation", ["missing", "duplicate", "wrong-source", "fabricated-quote"]
)
def test_incomplete_or_unverifiable_extraction_fails_closed(mutation):
    s = demo_snapshot()
    a = extraction("engineering", s)
    if mutation == "missing":
        a.checks.pop()
    if mutation == "duplicate":
        a.checks.append(a.checks[0])
    if mutation == "wrong-source":
        a.checks[0].supporting_quotes[0].source_id = "pcn"
    if mutation == "fabricated-quote":
        a.checks[0].supporting_quotes[0].quote = "Fabricated source text"
    with pytest.raises(ValueError):
        reconcile(a, s)


def test_supplier_number_followed_by_sentence_punctuation_is_valid():
    snapshot = demo_snapshot()
    result = reconcile(extraction("commitment", snapshot), snapshot)
    assert result.findings == []
