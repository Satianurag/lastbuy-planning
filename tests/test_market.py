from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from lastbuy.market import market_reference

CHECKED = datetime(2026, 9, 20, 17, 32, tzinfo=UTC)


@pytest.mark.parametrize("currency,total", [("INR", "200119.92"), ("USD", "2094.40")])
def test_exact_observed_250_unit_total(currency, total):
    result = market_reference(250, currency, at=CHECKED)
    assert result["calculation"]["subtotal"] == total
    assert result["calculation"]["purchase_authority"] is False
    assert result["calculation"]["existing_case_modified"] is False
    assert result["reference"]["conversion_used"] is False
    for tier in result["reference"]["offers"][currency]["tiers"]:
        assert (Decimal(tier["unit_price"]) * tier["quantity"]).quantize(
            Decimal("0.01")
        ) == Decimal(tier["extended_price"])


def test_bulk_shortfall_is_not_made_into_a_firm_quote():
    c = market_reference(10_000, at=CHECKED)["calculation"]
    assert c["subtotal"] is None
    assert c["unit_price"] is None
    assert c["observed_stock_shortfall"] == 7799
    assert c["status"] == "QUOTE_REQUIRED"


def test_stock_boundary_and_replacement_are_separate():
    assert market_reference(2201, at=CHECKED)["calculation"]["subtotal"] is not None
    assert market_reference(2202, at=CHECKED)["calculation"]["subtotal"] is None


def test_stale_snapshot_does_not_claim_current_price():
    c = market_reference(250, at=CHECKED + timedelta(days=1))["calculation"]
    assert c["stale"] and c["subtotal"] is None


def test_no_invented_deadline_cutoff():
    c = market_reference(250, at=datetime(2026, 10, 7, tzinfo=UTC))["calculation"]
    assert any("time zone" in reason for reason in c["reasons"])
    assert c["subtotal"] is None


@pytest.mark.parametrize(
    "quantity,currency",
    [
        (0, "INR"),
        (-1, "USD"),
        (2.5, "USD"),
        (True, "USD"),
        (1_000_001, "INR"),
        (250, "EUR"),
    ],
)
def test_invalid_quantity_or_unobserved_currency_rejected(quantity, currency):
    with pytest.raises(ValueError):
        market_reference(quantity, currency, at=CHECKED)
