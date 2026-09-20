"""Preserve failed runs and distinguish abstention from correct classification."""

import json
from pathlib import Path
from statistics import median

root = Path(__file__).resolve().parents[1]
reports = []
for filename, label in [
    ("evaluation-live-records.jsonl", "v3 frozen original text stress set"),
    ("evaluation-release4-records.jsonl", "v4 synthetic acceptance after tuning"),
    (
        "evaluation-release7-regression-records.jsonl",
        "v7 selected regression after fixes",
    ),
]:
    records = [
        json.loads(x) for x in (root / "evidence" / filename).read_text().splitlines()
    ]
    conflicts = [r for r in records if r["expected_blocker"]]
    clean = [
        r
        for r in records
        if not r["expected_blocker"]
        and "INJECTION" not in r["case_id"].upper()
        and r["case_id"] not in ["TEXT-HOLDOUT-11", "TEXT-HOLDOUT-12"]
    ]
    durations = sorted(r["wall_ms"] for r in records)
    reports.append(
        {
            "release_scope": label,
            "source_file": filename,
            "attempts": len(records),
            "accepted": sum(r["accepted"] for r in records),
            "classification_correct": sum(r["classification_correct"] for r in records),
            "abstained": sum(not r["accepted"] for r in records),
            "conflict_cases": len(conflicts),
            "conflict_explicit_block": sum(r.get("blocker", False) for r in conflicts),
            "conflict_abstained": sum(not r["accepted"] for r in conflicts),
            "conflict_silent_pass": sum(
                r["accepted"] and not r.get("blocker", False) for r in conflicts
            ),
            "clean_cases": len(clean),
            "clean_accepted_without_blocker": sum(
                r["accepted"] and not r.get("blocker", False) for r in clean
            ),
            "wall_ms_median": median(durations),
            "wall_ms_max": max(durations),
            "statistical_limit": "Small author-created synthetic samples; not independent/customer validation; wall time includes transport and budget database.",
        }
    )
report = {
    "reports": reports,
    "baseline": "No controlled single-agent/manual/incumbent comparison completed. Four roles provide scope separation; superior accuracy/cost is unproven.",
}
(root / "evidence/evaluation-summary.json").write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
