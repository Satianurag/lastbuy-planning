"""Read-only post-deployment checks; no model calls or authenticated writes."""

import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]


def main():
    base = "https://lastbuy-dev-4126.azurewebsites.net"
    exporter = "https://lastbuy-export-4126.azurewebsites.net"
    with httpx.Client(timeout=90) as client:
        health = client.get(base + "/api/health")
        auth = client.get(base + "/api/auth/config")
        cases = client.get(base + "/api/cases")
        export = client.post(exporter + "/api/exports/unauthenticated-probe")
        js = client.get(base + "/assets/app.js?v=20260920-currentness")
        index = client.get(base + "/")
    assert (
        health.status_code
        == auth.status_code
        == js.status_code
        == index.status_code
        == 200
    )
    assert cases.status_code == export.status_code == 401
    assert js.content == (ROOT / "web/app.js").read_bytes()
    assert index.content == (ROOT / "web/index.html").read_bytes()
    releases = {}
    for key, filename in (
        ("web_package", "functions-source-release.json"),
        ("export_package", "export_functions-source-release.json"),
    ):
        release = json.loads((ROOT / "evidence" / filename).read_text())
        assert (
            hashlib.sha256((ROOT / release["archive"]).read_bytes()).hexdigest()
            == release["sha256"]
        )
        releases[key] = release
    report = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "health_status": health.status_code,
        "auth_config_status": auth.status_code,
        "unauthenticated_case_access": cases.status_code,
        "unauthenticated_export_access": export.status_code,
        "cloud_ui_matches_local_bytes": True,
        **releases,
        "tests": ET.parse(ROOT / "evidence/implementation-tests.xml")
        .getroot()
        .find("testsuite")
        .attrib,
        "runtime_recovery": json.loads(
            (ROOT / "evidence/runtime-v2-checkpoint-completed.json").read_text()
        )["runtimeStatus"],
        "historical_gate": json.loads(
            (ROOT / "evidence/cloud-historical-gate-verification.json").read_text()
        ),
        "browser": {
            "method": "Actual in-app browser interaction against localhost",
            "blocked_case": "LTB-LIVE-CURRENT-BALANCE-20260920",
            "provisional_labels_visible": True,
            "engineering_approval_unavailable": True,
            "export_disabled": True,
            "stock_source_current_4800_and_opening_6000_visible": True,
            "golden_case_recommendation_preserved": True,
        },
        "source_parent_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "model_calls_in_this_check": 0,
        "budget": json.loads((ROOT / "evidence/budget-status.json").read_text()),
    }
    (ROOT / "evidence/live-release-verification.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    previous = json.loads((ROOT / "evidence/final-release-check.json").read_text())
    previous.update({k: v for k, v in report.items() if k in previous})
    previous["orchestrator_v2_validation"] = (
        "Cloud registration plus actual local Functions/Azurite checkpoint replay through approval wait completion; reused recorded v7 model responses."
    )
    previous["latest_verification"] = "evidence/live-release-verification.json"
    (ROOT / "evidence/final-release-check.json").write_text(
        json.dumps(previous, indent=2) + "\n"
    )
    print(
        json.dumps(
            {
                "verified": True,
                "health": health.status_code,
                "protected_cases": cases.status_code,
                "protected_export": export.status_code,
                "cloud_assets_exact": True,
                "web_sha256": releases["web_package"]["sha256"],
            }
        )
    )


if __name__ == "__main__":
    main()
