import copy
from datetime import date, timedelta

import pytest
from pydantic import ValidationError

from lastbuy.domain import Snapshot, canonical, digest
from lastbuy.fixtures import FIXTURE_CLOCK, demo_snapshot
from lastbuy.solver import solve, verify_solution


def test_golden_financial_case():
    result = solve(demo_snapshot(), FIXTURE_CLOCK)
    assert result["status"] == "READY_FOR_APPROVAL"
    assert result["purchase_quantity"] == 10000
    assert result["commitment_minor"] == 80000000
    assert result["commitment_difference_minor"] == 64000000
    assert result["reported_on_hand"] == 14000
    assert result["eligible_on_hand"] == 8000
    assert result["confirmed_inbound"] == 4000
    assert {e["reason"]: e["quantity"] for e in result["exclusions"]} == {
        "duplicate custody": 2000,
        "incompatible revision": 3000,
        "quarantined": 1000,
    }


@pytest.mark.parametrize(
    "demand,stock,multiple,minimum",
    [
        (d, s, m, n)
        for d, s, m, n in [
            (0, 0, 1, 0),
            (1, 0, 1, 0),
            (1, 0, 2, 0),
            (1, 0, 1, 4),
            (3, 2, 2, 0),
            (4, 4, 1, 5),
            (5, 8, 2, 3),
            (7, 2, 3, 4),
            (11, 4, 4, 0),
            (13, 1, 5, 8),
            (16, 7, 3, 0),
            (18, 0, 4, 8),
            (19, 4, 7, 0),
            (22, 2, 4, 12),
            (4, 3, 6, 7),
            (7, 0, 1, 0),
            (8, 1, 2, 2),
            (9, 2, 3, 3),
            (10, 3, 4, 4),
            (11, 4, 5, 5),
        ]
    ],
)
def test_small_problem_matches_exhaustive_feasible_purchase_search(
    demand, stock, multiple, minimum
):
    s = demo_snapshot()
    s.lots = [s.lots[0]]
    s.lots[0].quantity = stock
    s.scenarios[0].demand = [s.scenarios[0].demand[0]]
    s.scenarios[0].demand[0].quantity = demand
    s.quote.multiple, s.quote.minimum, s.quote.max_quantity = multiple, minimum, 100
    feasible = [
        q
        for q in range(101)
        if q % multiple == 0 and (q == 0 or q >= minimum) and q + stock >= demand
    ]
    result = solve(s, FIXTURE_CLOCK)
    assert result["purchase_quantity"] == min(feasible)


@pytest.mark.parametrize(
    "field,value", [("engineering_released", False), ("engineering_released", None)]
)
def test_unreleased_engineering_blocks(field, value):
    s = demo_snapshot()
    setattr(s.cohorts[0], field, value)
    assert solve(s, FIXTURE_CLOCK)["status"] == "NEEDS_REVIEW"


@pytest.mark.parametrize(
    "change",
    [
        "incomplete",
        "missing",
        "wrong_component",
        "unsigned",
        "unknown_coverage",
        "expired_coverage",
        "unapproved_forecast",
        "unknown_forecast",
        "expired_deadline",
        "unknown_revision",
        "unknown_hold",
        "unknown_confirmation",
        "conflicting_duplicate",
    ],
)
def test_critical_input_ambiguities_block_certification(change):
    s = demo_snapshot()
    if change == "incomplete":
        s.complete = False
    if change == "missing":
        s.missing_sources = ["contract-amendments-page-2"]
    if change == "wrong_component":
        s.scenarios[0].demand[0].coverage_component = "DETECTOR"
    if change == "unsigned":
        s.scenarios[0].demand[0].signed_coverage = False
    if change == "unknown_coverage":
        s.scenarios[0].demand[0].signed_coverage = None
    if change == "expired_coverage":
        s.scenarios[0].demand[0].coverage_end = date(2029, 1, 1)
    if change == "unapproved_forecast":
        s.scenarios[0].approved = False
    if change == "unknown_forecast":
        s.scenarios[0].approved = None
    if change == "expired_deadline":
        s.quote.order_deadline = FIXTURE_CLOCK - timedelta(seconds=1)
    if change == "unknown_revision":
        s.lots[0].revision = None
    if change == "unknown_hold":
        s.lots[0].quarantined = None
    if change == "unknown_confirmation":
        s.lots[0].confirmed = None
    if change == "conflicting_duplicate":
        s.lots[2].quantity = 2100
    result = solve(s, FIXTURE_CLOCK)
    assert result["status"] == "NEEDS_REVIEW"
    assert result["blockers"]
    assert "purchase_quantity" not in result


@pytest.mark.parametrize(
    "change,expected",
    [
        ("reserve", 11000),
        ("inbound_unconfirmed", 14000),
        ("inbound_late", 14000),
        ("on_hand_expired", 16000),
        ("foreign_owner", 16000),
        ("overlap_exclusion", 10000),
        ("released_quarantine", 9000),
        ("amendment_removed", 8000),
    ],
)
def test_inventory_and_coverage_effects(change, expected):
    s = demo_snapshot()
    if change == "reserve":
        s.lots[0].reserved = 500
    if change == "inbound_unconfirmed":
        s.lots[5].confirmed = False
    if change == "inbound_late":
        s.lots[5].available = date(2032, 1, 1)
    if change == "on_hand_expired":
        s.lots[0].expires = date(2029, 1, 1)
    if change == "foreign_owner":
        s.lots[0].owner = "ANOTHER-OEM"
    if change == "overlap_exclusion":
        s.lots[3].quarantined = True
    if change == "released_quarantine":
        s.lots[4].quarantined = False
    if change == "amendment_removed":
        s.scenarios[0].demand[1].quantity = 10000
    assert solve(s, FIXTURE_CLOCK)["purchase_quantity"] == expected


@pytest.mark.parametrize(
    "change",
    ["allocation_cap", "new_part_incompatible", "delivery_too_late", "all_stock_late"],
)
def test_infeasible_coverage_is_not_a_zero_buy_recommendation(change):
    s = demo_snapshot()
    if change == "allocation_cap":
        s.quote.max_quantity = 9000
    if change == "new_part_incompatible":
        s.quote.revision = "A1"
    if change == "delivery_too_late":
        s.quote.available = date(2032, 1, 1)
    if change == "all_stock_late":
        for lot in s.lots:
            lot.available = date(2032, 1, 1)
        s.quote.available = date(2032, 1, 1)
    assert solve(s, FIXTURE_CLOCK)["status"] == "INFEASIBLE"


def test_solver_timeout_never_certifies():
    assert solve(demo_snapshot(), FIXTURE_CLOCK, timeout=0)["status"] == "NEEDS_REVIEW"


def test_independent_verifier_rejects_double_consumption():
    s = demo_snapshot()
    result = solve(s, FIXTURE_CLOCK)
    result["allocations"].append(copy.deepcopy(result["allocations"][0]))
    with pytest.raises(ValueError):
        verify_solution(s, result)


def test_robust_scenarios_share_purchase_not_physical_consumption():
    s = demo_snapshot()
    other = s.scenarios[0].model_copy(deep=True)
    other.id = "HIGHER"
    other.demand[1].quantity = 15000
    s.scenarios.append(other)
    result = solve(s, FIXTURE_CLOCK)
    assert result["purchase_quantity"] == 13000
    verify_solution(s, result)


@pytest.mark.parametrize(
    "mutation",
    [
        "bad_hash",
        "bad_evidence",
        "negative",
        "float",
        "units",
        "unknown_cohort",
        "duplicate_id",
        "reserved_exceeds",
    ],
)
def test_invalid_contracts_rejected(mutation):
    data = demo_snapshot().model_dump(mode="json")
    if mutation == "bad_hash":
        data["sources"][0]["text"] += " modified"
    if mutation == "bad_evidence":
        data["lots"][0]["evidence"] = ["missing"]
    if mutation == "negative":
        data["lots"][0]["quantity"] = -1
    if mutation == "float":
        data["lots"][0]["quantity"] = 1.5
    if mutation == "units":
        data["lots"][0]["unit"] = "PACK"
    if mutation == "unknown_cohort":
        data["scenarios"][0]["demand"][0]["cohort"] = "OTHER"
    if mutation == "duplicate_id":
        data["lots"][1]["id"] = data["lots"][0]["id"]
    if mutation == "reserved_exceeds":
        data["lots"][0]["reserved"] = 9000
    with pytest.raises(ValidationError):
        Snapshot.model_validate(data)


def test_hash_is_order_stable_and_unicode_normalized():
    assert digest({"b": 1, "a": "e\u0301"}) == digest({"a": "é", "b": 1})
    with pytest.raises(ValueError):
        canonical({"q": 1.1})
