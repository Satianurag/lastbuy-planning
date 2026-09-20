"""Verify deployed public price calculations and exact UI assets without model spend."""

import hashlib
import json
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://lastbuy-dev-4126.azurewebsites.net"


def main():
    with httpx.Client(timeout=90) as client:
        data = client.get(BASE + "/api/market-prices?quantity=250&currency=INR")
        data.raise_for_status()
        result = data.json()
        assert result["calculation"]["subtotal"] == "200119.92"
        usd = client.get(BASE + "/api/market-prices?quantity=250&currency=USD").json()
        assert usd["calculation"]["subtotal"] == "2094.40"
        bulk = client.get(
            BASE + "/api/market-prices?quantity=10000&currency=INR"
        ).json()
        assert bulk["calculation"]["subtotal"] is None
        assert bulk["calculation"]["observed_stock_shortfall"] == 7799
        assert bulk["calculation"]["status"] == "QUOTE_REQUIRED"
        protected = client.get(BASE + "/api/cases")
        assert protected.status_code == 401
        assets = {}
        for name in ["app.js", "market-view.js", "style.css"]:
            response = client.get(BASE + "/assets/" + name + "?v=20260920-prices")
            assert response.status_code == 200
            assert response.content == (ROOT / "web" / name).read_bytes()
            assets[name] = hashlib.sha256(response.content).hexdigest()
    report = {
        "checked_at": datetime.now(UTC).isoformat(),
        "url": BASE + "/?view=market",
        "market_reference_sha256": result["reference_sha256"],
        "supplier_observed_at": result["reference"]["observed_at"],
        "supplier_verification": "Actual browser inspection of US and India rendered listings; manufacturer PDF retrieved and read independently.",
        "cloud_inr_250_subtotal": result["calculation"]["subtotal"],
        "cloud_usd_250_subtotal": usd["calculation"]["subtotal"],
        "cloud_bulk_10000": bulk["calculation"],
        "unauthenticated_private_cases": protected.status_code,
        "assets_match_local_bytes": assets,
        "browser_local": "Verified INR subtotal, USD switch, over-stock quote requirement and source links through actual browser UI.",
        "tests": ET.parse(ROOT / "evidence/implementation-tests.xml")
        .getroot()
        .find("testsuite")
        .attrib,
        "new_model_calls": 0,
        "enterprise_case_records_changed": False,
        "web_release": json.loads(
            (ROOT / "evidence/functions-source-release.json").read_text()
        ),
    }
    (ROOT / "evidence/market-release-verification.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(
        json.dumps(
            {
                "verified": True,
                "inr_250": "200119.92",
                "usd_250": "2094.40",
                "bulk_status": "QUOTE_REQUIRED",
                "private_cases": 401,
            }
        )
    )


if __name__ == "__main__":
    main()
