"""Validate current artifacts and package only explicitly selected public evidence.

Does not call a model, submit an entry, or infer readiness of a missing video.
Run after prepare_submission.py and build_submission_pdf.py.
"""

import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET
from datetime import UTC, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output/submission"


def read(path):
    return json.loads((ROOT / path).read_text())


def digest(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def main():
    entry = read("submission/entry.json")
    market = read("lastbuy/market_prices.json")
    tests = ET.parse(ROOT / "evidence/implementation-tests.xml").getroot()
    suites = list(tests.iter("testsuite"))
    count = sum(int(s.attrib["tests"]) for s in suites)
    assert count >= 160
    assert all(
        int(s.attrib.get(k, 0)) == 0
        for s in suites
        for k in ("failures", "errors", "skipped")
    )
    checked_suite_at = datetime.fromisoformat(suites[0].attrib["timestamp"])
    assert timedelta(0) <= datetime.now(UTC) - checked_suite_at <= timedelta(hours=24)
    beats = entry["beats"]
    assert len(beats) == 7 and beats[0]["start"] == 0
    assert beats[-1]["end"] == entry["planned_video_seconds"] == 175
    assert entry["planned_video_seconds"] < entry["video_max_seconds"] == 180
    assert all(b["start"] < b["end"] for b in beats)
    assert all(a["end"] == b["start"] for a, b in zip(beats, beats[1:]))
    assert (OUT / "entry-description.txt").read_text() == entry[
        "title"
    ] + "\n\n" + entry["description"] + "\n"
    for path in ("output/submission/recording-guide.md", "docs/08-contest-handover.md"):
        text = (ROOT / path).read_text()
        assert all(b["screen"] in text and b["narration"] in text for b in beats)
    click_guide = (ROOT / "output/demo/START-HERE.md").read_text()
    assert all(b["screen"] in click_guide and b["action"] in click_guide for b in beats)
    assert (ROOT / "output/demo/NARRATION.txt").read_text().strip() == "\n\n".join(
        b["narration"] for b in beats
    )
    assert (
        f"{sum(len(b['narration'].split()) for b in beats)} words"
        in (ROOT / "output/demo/RECORDING-CHECKLIST.md").read_text()
    )
    for offer in market["offers"].values():
        for tier in offer["tiers"]:
            total = (Decimal(tier["unit_price"]) * tier["quantity"]).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            assert str(total) == tier["extended_price"]
    pdf_path = "output/pdf/LastBuy-Architect-Solution-Design.pdf"
    pdf = PdfReader(ROOT / pdf_path)
    assert len(pdf.pages) == 8
    assert (ROOT / pdf_path).stat().st_size < entry["support_max_bytes"]
    pdf_text = "\n".join(p.extract_text() for p in pdf.pages)
    for claim in (
        f"{count} automated tests",
        "12,569",
        "8,363",
        "200119.92",
        "800.47968",
        "7 October 2026",
        "7 April 2027",
        "640,000",
        "HTTP 409",
        "NEEDS_REVIEW",
        "not achieved",
        "Decision record, not an opaque answer",
    ):
        assert claim in pdf_text, claim
    assert sum(len(p.get("/Annots", [])) for p in pdf.pages) >= 10
    first_page_links = {
        str(annot.get_object().get("/A", {}).get("/URI"))
        for annot in pdf.pages[0].get("/Annots", [])
    }
    assert market["notice_url"] in first_page_links
    assert all(
        offer["url"] in first_page_links for offer in market["offers"].values()
    )
    assert "https://lastbuy-dev-4126.azurewebsites.net/?view=market" in first_page_links
    releases = {}
    for name in (
        "functions-source-release",
        "export_functions-source-release",
        "lastbuy-agent-release",
    ):
        release = read(f"evidence/{name}.json")
        expected = release.get("sha256", release.get("source_sha256"))
        assert digest(release["archive"]) == expected
        with ZipFile(ROOT / release["archive"]) as z:
            assert z.testzip() is None
            if "files" in release:
                assert len(z.namelist()) == release["files"]
        releases[name] = release
    gate = read("evidence/cloud-historical-gate-verification.json")
    assert gate["http_status"] == 409 and gate["external_rows"] == 0
    exports = read("evidence/cloud-export-verification-LIVE-20260920.json")
    assert len(exports["records"]) == 2
    assert all(
        r["external_rows"] == 1 and r["repeat_same_receipt"] and r["audit_valid"]
        for r in exports["records"]
    )
    historical_market = read("evidence/market-release-verification.json")
    assert historical_market["cloud_inr_250_subtotal"] == "200119.92"
    assert historical_market["cloud_usd_250_subtotal"] == "2094.40"
    assert historical_market["supplier_observed_at"] == market["observed_at"]
    cloud = read("evidence/demo-ui-release-verification.json")
    assert cloud["health_http_status"] == 200
    assert cloud["unauthenticated_private_cases"] == 401
    assert cloud["new_model_calls"] == 0
    assert cloud["market_observed_at"] == market["observed_at"]
    if cloud["market_stale"]:
        assert cloud["market_status"] == "QUOTE_REQUIRED"
        assert cloud["cloud_inr_250_subtotal"] is None
    else:
        assert cloud["cloud_inr_250_subtotal"] == "200119.92"
    assert cloud["web_release"] == releases["functions-source-release"]
    assert all(
        digest("web/" + name) == sha
        for name, sha in cloud["assets_match_local_bytes"].items()
    )
    # No automatic assertion that an unreviewed newly added video meets the rules.
    videos = [
        str(p.relative_to(ROOT))
        for p in (ROOT / "output").rglob("*")
        if p.suffix.lower() in (".mp4", ".mov", ".m4v")
    ]
    assert not videos and not entry["video_present"] and not entry["submitted"]
    evidence_names = [
        "implementation-tests.xml",
        "evaluation-summary.json",
        "evaluation-offline.json",
        "full-cloud-release7.json",
        "live-acceptance-summary.json",
        "live-acceptance-novel.json",
        "cloud-historical-gate-verification.json",
        "cloud-export-verification-LIVE-20260920.json",
        "runtime-v2-checkpoint-completed.json",
        "market-release-verification.json",
        "demo-ui-release-verification.json",
        "founderz-platform-review.json",
        "functions-source-release.json",
        "export_functions-source-release.json",
        "lastbuy-agent-release.json",
    ]
    files = [
        pdf_path,
        "submission/entry.json",
        "lastbuy/market_prices.json",
        "README.md",
    ]
    files += [
        "output/submission/" + name
        for name in ("README.md", "entry-description.txt", "recording-guide.md")
    ]
    files += [
        "output/demo/" + name
        for name in (
            "START-HERE.md",
            "NARRATION.txt",
            "RECORDING-CHECKLIST.md",
            "preflight.json",
            "browser-rehearsal.json",
        )
    ]
    files += [
        "docs/" + name
        for name in (
            "01-business-case.md",
            "03-architecture-and-contracts.md",
            "08-contest-handover.md",
            "09-completion-audit.md",
            "10-contest-strategy-2026-09-20.md",
            "11-public-market-evidence.md",
            "13-final-demo-review-2026-09-22.md",
        )
    ]
    files += ["evidence/" + name for name in evidence_names]
    for path in files:
        if path.endswith((".md", ".txt")):
            text = (ROOT / path).read_text().lower()
            assert "147 tests" not in text and "six-page" not in text, path
    checked_at = datetime.now(UTC).isoformat()
    manifest = {
        "checked_at": checked_at,
        "status": "Supporting package verified; participant video/review/submission pending",
        "source_parent_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "automated_tests": count,
        "pdf_pages": len(pdf.pages),
        "pdf_bytes": (ROOT / pdf_path).stat().st_size,
        "narration_words": sum(len(b["narration"].split()) for b in beats),
        "planned_video_seconds": entry["planned_video_seconds"],
        "scene_count": len(beats),
        "video_present": False,
        "submitted": False,
        "participant_pending": entry["participant_pending"],
        "market_observed_at": market["observed_at"],
        "manufacturer_notice_sha256": market["notice_sha256"],
        "current_releases": releases,
        "release_note": "Older final-release-check and live-release-verification records are historical snapshots. These current descriptors identify the packaged web/export/hosted source releases.",
        "evidence_index": {
            "Current demo UI deployment and price-age guards": "evidence/demo-ui-release-verification.json",
            "Market release verification": "evidence/market-release-verification.json",
            "Novel live acceptance + corrected release verification": [
                "evidence/live-acceptance-novel.json",
                "evidence/cloud-historical-gate-verification.json",
            ],
            "Cloud historical-evidence gate": "evidence/cloud-historical-gate-verification.json",
            "Cloud export CREATE / RECOVER": "evidence/cloud-export-verification-LIVE-20260920.json",
        },
        "official_review": {
            "date": entry["review_date"],
            "rules": "https://founderz.com/agentathon-terms/",
            "teaching_repository": "https://github.com/microsoft/FrontierWeekHack",
            "repository_head": "cd7ec1717fbf109bf6e76edfa38a5a7cfc0d88ea",
            "repository_head_last_verified_on": "2026-09-24",
            "authenticated_form": "evidence/founderz-platform-review.json",
            "deadline_note": entry["deadline_note"],
            "conservative_submit_by_ist": entry["conservative_submit_by_ist"],
        },
        "new_model_calls_in_package_audit": 0,
        "checks": [
            "Eight-page PDF and form size limit",
            "Matching seven-scene, 175-second narrative and click guide",
            f"{count}-test zero-failure report, run within 24 hours",
            "Exact decimal public price totals",
            "Current source archive integrity",
            "Exact deployed UI bytes, price-age guards and private-case authentication",
            "Historical stock rejection and one-row recovery evidence",
            "Explicit distinction between public facts, examples and measured results",
        ],
        "files": {
            path: {"sha256": digest(path), "bytes": (ROOT / path).stat().st_size}
            for path in files
        },
    }
    (OUT / "package-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    files.append("output/submission/package-manifest.json")
    bundle = OUT / "LastBuy-Submission-Package.zip"
    with ZipFile(bundle, "w", ZIP_DEFLATED) as z:
        for path in files:
            z.write(ROOT / path, path)
    with ZipFile(bundle) as z:
        assert z.testzip() is None
        for path in files:
            assert z.read(path) == (ROOT / path).read_bytes()
    report = {
        "checked_at": checked_at,
        "passed": True,
        "pdf_visual_review": "All eight rendered pages inspected; no clipping or overflow",
        "files_packaged": len(files),
        "bundle_sha256": digest(str(bundle.relative_to(ROOT))),
        "pdf_pages": 8,
        "automated_tests": count,
        "new_model_calls": 0,
        "submitted": False,
        "participant_pending": entry["participant_pending"],
    }
    (ROOT / "evidence/submission-consistency-audit.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
