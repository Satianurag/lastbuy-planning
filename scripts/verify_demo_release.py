"""Read-only cloud checks for the demo UI; write a separate verification report.

No inference, approval, export, supplier refresh or deployment is requested.
Historical provider and integration evidence remains separately attributed.
"""

import hashlib
import json
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://lastbuy-dev-4126.azurewebsites.net"
CACHE_VERSION = "20260922-proof"
REPORT = ROOT / "evidence/demo-ui-release-verification.json"


def main():
    reference = json.loads((ROOT / "lastbuy/market_prices.json").read_text())
    release = json.loads((ROOT / "evidence/functions-source-release.json").read_text())
    archive_sha256 = hashlib.sha256(
        (ROOT / release["archive"]).read_bytes()
    ).hexdigest()
    assert archive_sha256 == release["sha256"], "Release archive hash mismatch"
    tier = next(t for t in reference["offers"]["INR"]["tiers"] if t["quantity"] == 250)
    observed_total = (Decimal(tier["unit_price"]) * 250).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    assert observed_total == Decimal(tier["extended_price"]) == Decimal("200119.92")
    assert 10000 - reference["stock_observed"] == 7799

    with httpx.Client(timeout=45, follow_redirects=False) as client:
        health = client.get(BASE + "/api/health")
        assert health.status_code == 200, "Cloud health did not return HTTP 200"
        assert health.json()["status"] == "ok"
        assert health.json()["auth_mode"] == "entra"
        assert "data_mode" not in health.json(), (
            "Authentication cannot imply customer data"
        )
        protected = client.get(BASE + "/api/cases")
        assert protected.status_code == 401, (
            "Private cases are not rejecting anonymous access"
        )

        assets = {}
        for name in ("index.html", "app.js", "style.css", "market-view.js"):
            path = "/" if name == "index.html" else "/assets/" + name
            response = client.get(BASE + path, params={"v": CACHE_VERSION})
            assert response.status_code == 200, f"Asset unavailable: {name}"
            assert response.content == (ROOT / "web" / name).read_bytes(), (
                f"Deployed bytes differ from local asset: {name}"
            )
            assets[name] = hashlib.sha256(response.content).hexdigest()

        response = client.get(
            BASE + "/api/market-prices", params={"quantity": 250, "currency": "INR"}
        )
        response.raise_for_status()
        market = response.json()
        assert market["reference"] == reference, (
            "Cloud market observation differs from the local source"
        )
        calculation = market["calculation"]
        assert calculation["quantity"] == 250 and calculation["currency"] == "INR"
        assert calculation["tier_quantity"] == 250
        assert isinstance(calculation["stale"], bool)
        if calculation["stale"]:
            assert calculation["status"] == "QUOTE_REQUIRED"
            assert calculation["subtotal"] is None and calculation["unit_price"] is None
        else:
            assert calculation["status"] == "CATALOGUE_ESTIMATE"
            assert Decimal(calculation["subtotal"]) == observed_total
            assert Decimal(calculation["unit_price"]) == Decimal(tier["unit_price"])
        assert calculation["purchase_authority"] is False
        assert calculation["existing_case_modified"] is False

        response = client.get(
            BASE + "/api/market-prices", params={"quantity": 10000, "currency": "INR"}
        )
        response.raise_for_status()
        bulk = response.json()
        assert bulk["reference"] == reference
        assert bulk["calculation"]["quantity"] == 10000
        assert bulk["calculation"]["currency"] == "INR"
        assert bulk["calculation"]["status"] == "QUOTE_REQUIRED"
        assert bulk["calculation"]["subtotal"] is None
        assert bulk["calculation"]["observed_stock_shortfall"] == 7799
        assert bulk["calculation"]["purchase_authority"] is False
        assert bulk["calculation"]["existing_case_modified"] is False

    report = {
        "checked_at": datetime.now(UTC).isoformat(),
        "verified": True,
        "url": BASE,
        "health_http_status": health.status_code,
        "auth_mode": health.json()["auth_mode"],
        "unauthenticated_private_cases": protected.status_code,
        "assets_match_local_bytes": assets,
        "asset_cache_version": CACHE_VERSION,
        "web_release": release,
        "archive_sha256_verified": archive_sha256,
        "market_reference_sha256": market["reference_sha256"],
        "market_observed_at": reference["observed_at"],
        "market_status": calculation["status"],
        "market_stale": calculation["stale"],
        "observed_tier_250_inr_total": str(observed_total),
        "cloud_inr_250_subtotal": calculation["subtotal"],
        "cloud_bulk_10000": bulk["calculation"],
        "supplier_reverified_in_this_check": False,
        "historical_provider_evidence_scope": (
            "The UI exposes stored Foundry results. The completed golden case and "
            "captured supply failure retain their original provider provenance. "
            "The failure replay reuses other roles from the reference case; its "
            "current validation is separate from the recorded response. Cloud "
            "export/recovery records are separate historical integration tests "
            "against an ERP simulator. This check does not rerun those tests."
        ),
        "historical_provider_evidence": [
            "evidence/full-cloud-release7.json",
            "evidence/live-acceptance-novel.json",
            "evidence/cloud-historical-gate-verification.json",
            "evidence/cloud-export-verification-LIVE-20260920.json",
        ],
        "new_model_calls": 0,
        "enterprise_case_records_changed": False,
        "scope": "Public HTTP read checks and local archive integrity; no browser interaction verification.",
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
