"""Public catalogue evidence; exact decimal estimates never authorize an ERP write."""

import json
from datetime import UTC, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from .domain import digest


def market_reference(quantity=250, currency="INR", *, at=None):
    if (
        isinstance(quantity, bool)
        or not isinstance(quantity, int)
        or not 1 <= quantity <= 1_000_000
    ):
        raise ValueError("Quantity must be a whole number from 1 to 1,000,000")
    reference = json.loads(Path(__file__).with_name("market_prices.json").read_text())
    if currency not in reference["offers"]:
        raise ValueError("Choose a directly observed USD or INR catalogue")
    at = at or datetime.now(UTC)
    if at.tzinfo is None:
        raise ValueError("A timezone is required")
    observed = datetime.fromisoformat(reference["observed_at"].replace("Z", "+00:00"))
    stale = at < observed or at - observed > timedelta(
        hours=reference["refresh_policy_hours"]
    )
    deadline = datetime.fromisoformat(reference["last_time_buy_date"]).date()
    reasons = []
    if stale:
        reasons.append(
            "Catalogue observation needs re-verification before estimating a current purchase."
        )
    if at.date() >= deadline:
        reasons.append(
            "Confirm the order deadline directly with the supplier; the notice gives no time zone or cutoff time."
        )
    if quantity > reference["stock_observed"]:
        reasons.append(
            "Requested quantity exceeds observed stock and backorders are unavailable; obtain a supplier allocation and quote."
        )
    tiers = reference["offers"][currency]["tiers"]
    tier = max(
        (t for t in tiers if t["quantity"] <= quantity), key=lambda t: t["quantity"]
    )
    total = (
        None
        if reasons
        else str(
            (Decimal(tier["unit_price"]) * quantity).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        )
    )
    return {
        "reference": reference,
        "reference_sha256": digest(reference),
        "calculation": {
            "quantity": quantity,
            "currency": currency,
            "tier_quantity": tier["quantity"],
            "unit_price": None if reasons else tier["unit_price"],
            "subtotal": total,
            "status": "QUOTE_REQUIRED" if reasons else "CATALOGUE_ESTIMATE",
            "reasons": reasons,
            "stale": stale,
            "observed_stock_shortfall": max(0, quantity - reference["stock_observed"]),
            "rounding": "Preserve five decimal places per unit; round the extended line once to two decimals, half up.",
            "purchase_authority": False,
            "existing_case_modified": False,
        },
    }
