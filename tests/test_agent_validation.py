import pytest

from lastbuy.agents import display_calculation, validate_assessment
from lastbuy.domain import Assessment
from lastbuy.fixtures import FIXTURE_CLOCK, demo_snapshot
from lastbuy.solver import solve


def assessment(summary="Modeled difference is USD 640,000.00, not achieved savings."):
    return Assessment.model_validate(
        {
            "role": "commitment",
            "summary": summary,
            "findings": [
                {
                    "code": "COST",
                    "severity": "info",
                    "summary": summary,
                    "evidence": ["pcn"],
                    "supporting_quotes": [
                        {"source_id": "pcn", "quote": "USD 80 per EACH"}
                    ],
                }
            ],
            "evidence": ["pcn"],
        }
    )


def test_deterministic_currency_formatting_precedes_model():
    result = display_calculation(solve(demo_snapshot(), FIXTURE_CLOCK))
    assert result["commitment_difference"] == "USD 640,000.00"
    assert result["commitment"] == "USD 800,000.00"
    assert not any(k.endswith("_minor") for k in result)


@pytest.mark.parametrize(
    "text",
    [
        "USD 64,000,000 reduction",
        "USD 64 million reduction",
        "$640m reduction",
        "USD 1.44 billion saved",
        "USD 800,001 commitment",
    ],
)
def test_incorrect_monetary_narration_rejected(text):
    s = demo_snapshot()
    with pytest.raises(ValueError, match="Monetary narration"):
        validate_assessment(
            assessment(text),
            "commitment",
            [x.model_dump(mode="json") for x in s.sources],
            solve(s, FIXTURE_CLOCK),
        )


@pytest.mark.parametrize(
    "mutation",
    [
        "quote_changed",
        "wrong_source",
        "unquoted_citation",
        "unknown_citation",
        "wrong_role",
    ],
)
def test_invalid_evidence_cannot_be_accepted(mutation):
    s = demo_snapshot()
    a = assessment()
    if mutation == "quote_changed":
        a.findings[0].supporting_quotes[0].quote = "USD 8 per EACH"
    if mutation == "wrong_source":
        a.findings[0].supporting_quotes[0].source_id = "warranty"
    if mutation == "unquoted_citation":
        a.findings[0].evidence.append("bom")
    if mutation == "unknown_citation":
        a.evidence.append("made-up")
    if mutation == "wrong_role":
        a.role = "supply"
    with pytest.raises(ValueError):
        validate_assessment(
            a,
            "commitment",
            [x.model_dump(mode="json") for x in s.sources],
            solve(s, FIXTURE_CLOCK),
        )


def test_matching_quote_and_amounts_accepted():
    s = demo_snapshot()
    validate_assessment(
        assessment(),
        "commitment",
        [x.model_dump(mode="json") for x in s.sources],
        solve(s, FIXTURE_CLOCK),
    )
