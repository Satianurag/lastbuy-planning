"""Check the existing rehearsal state without inference, approval or export writes."""

import hashlib
import json
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
BASE = "http://127.0.0.1:8810"


def main():
    saved = json.loads((ROOT / "evidence/full-cloud-release7.json").read_text())
    with httpx.Client(base_url=BASE, timeout=15) as client:
        health = client.get("/api/health")
        health.raise_for_status()
        assert health.json()["auth_mode"] == "local-demo"
        # Creates a separate local cookie session; it does not change case records.
        login = client.post(
            "/api/session", json={"persona": "planner"}, headers={"Origin": BASE}
        )
        login.raise_for_status()
        golden = client.get("/api/cases/LTB-CLOUD-RELEASE-7").json()
        failure = client.get("/api/cases/LTB-LIVE-CURRENT-BALANCE-20260920").json()
        market = client.get("/api/market-prices?quantity=250&currency=INR").json()
    assert golden["status"] == "READY_FOR_APPROVAL"
    assert golden["plan"] == saved["plan"]
    assert golden["plan"]["purchase_quantity"] == 10000
    assert golden["plan"]["commitment_difference_minor"] == 64000000
    assert golden["audit_valid"]
    assert len(golden["stages"]) == 4
    assert all(
        s["status"] == "COMPLETE" and s["result"]["agent_version"] == "7"
        for s in golden["stages"]
    )
    assert failure["status"] == "NEEDS_REVIEW" and failure["audit_valid"]
    assert any("historical quantities" in b for b in failure["plan"]["blockers"])
    captured_supply = next(s for s in failure["stages"] if s["role"] == "supply")[
        "result"
    ]["assessment"]
    assert "4,800" in captured_supply["summary"]
    captured_quantity = next(
        c for c in captured_supply["checks"] if c["key"] == "SAP-01:quantity"
    )
    assert str(captured_quantity["observed_value"]) == "6000"
    stock = next(
        s for s in failure["snapshot"]["sources"] if s["record_id"] == "STOCK-SYN-0919"
    )
    assert "4,800" in stock["text"] and "6,000" in stock["text"]
    if market["calculation"]["stale"]:
        assert market["calculation"]["subtotal"] is None
        assert market["calculation"]["status"] == "QUOTE_REQUIRED"
    assert (
        market["reference"]["offers"]["INR"]["tiers"][-1]["extended_price"]
        == "200119.92"
    )
    pdf = ROOT / "output/pdf/LastBuy-Architect-Solution-Design.pdf"
    manifest = json.loads(
        (ROOT / "output/submission/package-manifest.json").read_text()
    )
    assert (
        hashlib.sha256(pdf.read_bytes()).hexdigest()
        == manifest["files"][str(pdf.relative_to(ROOT))]["sha256"]
    )
    suite = (
        ET.parse(ROOT / "evidence/implementation-tests.xml").getroot().find("testsuite")
    )
    assert (
        int(suite.attrib["tests"]) == manifest["automated_tests"] > 0
        and int(suite.attrib["failures"]) == int(suite.attrib["errors"]) == 0
    )
    exports = json.loads(
        (ROOT / "evidence/cloud-export-verification-LIVE-20260920.json").read_text()
    )
    assert all(
        r["external_rows"] == 1 and r["repeat_same_receipt"] for r in exports["records"]
    )
    gate = json.loads(
        (ROOT / "evidence/cloud-historical-gate-verification.json").read_text()
    )
    assert gate["external_rows"] == 0 and gate["http_status"] == 409
    report = {
        "checked_at": datetime.now(UTC).isoformat(),
        "ready_for_local_rehearsal": True,
        "golden_plan_matches_recorded_cloud_result": True,
        "golden_plan_sha256": golden["plan"]["plan_sha256"],
        "failure_state": failure["status"],
        "captured_supply_summary_current_units": 4800,
        "captured_supply_structured_units": 6000,
        "captured_response_rejected_by_current_gate": True,
        "market_observed_at": market["reference"]["observed_at"],
        "market_requires_reverification": market["calculation"]["stale"],
        "market_demo_instruction": "Show the dated published table; do not describe a stale catalogue subtotal as a current quote.",
        "pdf_matches_reviewed_package": True,
        "cloud_export_evidence": "Existing recorded CREATE/RECOVER each one row; historical-stock fixture HTTP 409 and zero rows",
        "new_model_calls": 0,
        "case_records_changed": False,
        "participant_video_created": False,
    }
    dest = ROOT / "output/demo"
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "preflight.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
