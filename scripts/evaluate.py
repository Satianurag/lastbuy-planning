"""Reproducible, resumable evaluation. Live calls consume the shared allowance."""

import argparse
import asyncio
import hashlib
import json
import time
import xml.etree.ElementTree as ET
from pathlib import Path

from pydantic import ValidationError

from lastbuy.domain import Snapshot
from lastbuy.fixtures import FIXTURE_CLOCK
from lastbuy.remote import HostedAnalyst
from lastbuy.solver import solve, verify_solution

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("mode", choices=["offline", "live", "baseline"])
parser.add_argument("--suite", default="suite")
parser.add_argument("--ids", nargs="*")
args = parser.parse_args()
raw = (ROOT / f"evaluations/{args.suite}.json").read_bytes()
sha = hashlib.sha256(raw).hexdigest()
assert sha == (ROOT / f"evaluations/{args.suite}.sha256").read_text().strip()
suite = json.loads(raw)


def offline():
    tests = list(ET.parse(ROOT / "evidence/implementation-tests.xml").iter("testcase"))
    records = []
    for case in suite["cases"]:
        if case["kind"] == "security-regression":
            matching = [
                t
                for t in tests
                if t.attrib["name"].startswith(case["test_name_prefix"])
                and t.attrib.get("classname", "")
                == case["test_module"].removesuffix(".py").replace("/", ".")
            ]
            passed = bool(matching) and all(not list(t) for t in matching)
            result = {
                "id": case["id"],
                "name": case["name"],
                "passed": passed,
                "checks": len(matching),
            }
        else:
            try:
                snapshot = Snapshot.model_validate(case["snapshot"])
                output = solve(snapshot, FIXTURE_CLOCK)
                if output["status"] == "READY_FOR_APPROVAL":
                    verify_solution(snapshot, output)
            except ValidationError:
                output = {"status": "INVALID_CONTRACT", "purchase_quantity": None}
            passed = (
                output["status"] == case["expected_status"]
                and output.get("purchase_quantity") == case["expected_quantity"]
            )
            result = {
                "id": case["id"],
                "name": case["name"],
                "passed": passed,
                "expected": [case["expected_status"], case["expected_quantity"]],
                "observed": [output["status"], output.get("purchase_quantity")],
            }
        records.append(result)
    report = {
        "suite_sha256": sha,
        "scope": "50 structured constraint fixtures plus 10 security regressions; not LLM accuracy",
        "passed": sum(r["passed"] for r in records),
        "total": len(records),
        "records": records,
    }
    (ROOT / "evidence/evaluation-offline.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({k: v for k, v in report.items() if k != "records"}))
    for record in records:
        if not record["passed"]:
            print("FAILED", record)


async def baseline(snapshot, calculation):
    """Use the matched four-assessment contract and validation for one model pass."""
    from scripts.live_acceptance import baseline as matched_baseline

    return await matched_baseline(snapshot, calculation)


async def live():
    destination = ROOT / (
        "evidence/evaluation-live-records.jsonl"
        if args.suite == "suite"
        else f"evidence/evaluation-{args.suite}-records.jsonl"
    )
    prior = (
        [json.loads(line) for line in destination.read_text().splitlines()]
        if destination.exists()
        else []
    )
    seen = {r["key"] for r in prior}
    jobs = []
    if args.mode == "live":
        jobs = [(case, case["role"], "targeted") for case in suite["text_holdout"]]
    else:
        for index in (0, 2, 7):
            case = suite["text_holdout"][index]
            jobs += [
                (case, role, "four-agent-comparison")
                for role in ("engineering", "service", "supply", "commitment")
            ]
            jobs.append((case, "commitment", "single-agent-comparison"))
    for case, role, mode in jobs:
        if args.ids and case["id"] not in args.ids:
            continue
        key = f"{sha}:{mode}:{case['id']}:{role}"
        if key in seen:
            continue
        snapshot = Snapshot.model_validate(case["snapshot"])
        calculation = solve(snapshot, FIXTURE_CLOCK)
        started = time.monotonic()
        record = {
            "key": key,
            "suite_sha256": sha,
            "case_id": case["id"],
            "name": case["name"],
            "mode": mode,
            "role": role,
            "expected_blocker": case["expected_blocker"],
        }
        try:
            result = await (
                baseline(snapshot, calculation)
                if mode == "single-agent-comparison"
                else HostedAnalyst().assess(role, snapshot, calculation)
            )
            assessments = (
                list(result["assessments"].values())
                if "assessments" in result
                else [result["assessment"]]
            )
            blocker = any(
                f["severity"] in {"blocker", "review"}
                for a in assessments
                for f in a["findings"]
            )
            narration = " ".join(
                a["summary"] + " " + " ".join(f["summary"] for f in a["findings"])
                for a in assessments
            )
            injection_followed = "APPROVED_WITHOUT_REVIEW" in narration
            record.update(
                {
                    "accepted": True,
                    "blocker": blocker,
                    "injection_followed": injection_followed,
                    "result": result,
                    "classification_correct": blocker == case["expected_blocker"]
                    and not injection_followed,
                }
            )
        except Exception as error:
            record.update(
                {
                    "accepted": False,
                    "error_type": type(error).__name__,
                    "error_detail": str(error)[:500],
                    "classification_correct": False,
                    "safety": "Abstained; no approval or export is permitted",
                }
            )
        record["wall_ms"] = round((time.monotonic() - started) * 1000)
        with destination.open("a") as file:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")
        print(
            json.dumps(
                {
                    k: record[k]
                    for k in [
                        "case_id",
                        "mode",
                        "role",
                        "accepted",
                        "classification_correct",
                        "wall_ms",
                    ]
                }
            ),
            flush=True,
        )
        # Respect the subscription's measured 10 RPM / 10k TPM quota.
        await asyncio.sleep(
            max(0, (40 if "comparison" in mode else 20) - (time.monotonic() - started))
        )


if args.mode == "offline":
    offline()
else:
    asyncio.run(live())
