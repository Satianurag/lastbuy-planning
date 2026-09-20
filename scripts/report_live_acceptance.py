"""Summarize observed live outcomes and replay the captured defect through the fix."""

import json
from pathlib import Path

from lastbuy.domain import Assessment, Snapshot, now
from lastbuy.reconciliation import reconcile

ROOT = Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT / "evaluations/live-acceptance-20260920.json").read_text())
baseline = json.loads((ROOT / "evidence/live-acceptance-baseline.json").read_text())
novel = json.loads((ROOT / "evidence/live-acceptance-novel.json").read_text())
original = json.loads((ROOT / "evidence/full-cloud-release7.json").read_text())
fixed = reconcile(
    Assessment.model_validate(novel["result"]["assessment"]),
    Snapshot.model_validate(manifest["novel"]["snapshot"]),
)
comparison = {
    "cases": 1,
    "same_snapshot": baseline["snapshot_sha256"]
    == original["plan"]["input_snapshot_sha256"],
    "same_model_deployment": baseline["result"]["model"] == "lastbuy-dev-mini",
    "four_stage_observed": "Correctly accepted the clean golden case",
    "single_call_observed": "False review block on duplicate custody already excluded by the calculation",
    "four_stage_successful_response_tokens": sum(
        s["result"]["usage"].get("total_token_count", 0) for s in original["stages"]
    ),
    "single_call_response_tokens": baseline["result"]["usage"]["total_token_count"],
    "interpretation": "On this case, the one-call design consumed fewer response-reported tokens but introduced a false review block. Historical four-stage comparator; not a broad or concurrent randomized comparison.",
}
report = {
    "updated_at": now().isoformat(),
    "real_provider_attempts_this_run": 2,
    "comparison": comparison,
    "new_stock_case": {
        "original_live_response": "Selected 6000 opening units despite an explicit current 4800 balance; pipeline originally accepted",
        "captured_response_replay_after_fix": fixed.model_dump(mode="json"),
        "corrected_outcome": "Explicit historical-evidence blocker",
        "new_inference_after_fix": False,
    },
    "runtime_recovery": "Actual Functions v2 completed from exact recorded stage checkpoints through four synthetic approvals; see runtime-v2-checkpoint-completed.json",
    "cost": "INR 20 admission allowance reserved for these two attempts; total admission reservation INR 700. INR 300 infrastructure buffer. Actual invoice remains unknown after Cost Management 429.",
}
assert comparison["same_snapshot"] and comparison["same_model_deployment"]
assert any(f.code == "HISTORICAL_SOURCE_FACT" for f in fixed.findings)
(ROOT / "evidence/live-acceptance-summary.json").write_text(
    json.dumps(report, indent=2) + "\n"
)
print(
    json.dumps(
        {"comparison": comparison, "captured_defect_now_blocked": True}, indent=2
    )
)
