"""The live baseline must satisfy the same scoped checks as four hosted stages."""

import copy
import json
from pathlib import Path

import pytest

from lastbuy.domain import Snapshot
from lastbuy.solver import solve
from scripts.live_acceptance import validate_union


def inputs():
    case = json.loads(
        (Path(__file__).parents[1] / "evidence/full-cloud-release7.json").read_text()
    )
    return Snapshot.model_validate(case["snapshot"]), {
        s["role"]: copy.deepcopy(s["result"]["assessment"]) for s in case["stages"]
    }


def test_comparator_accepts_actual_recorded_four_stage_contract():
    snapshot, payload = inputs()
    assert set(validate_union(payload, snapshot, solve(snapshot))) == {
        "engineering",
        "service",
        "supply",
        "commitment",
    }


def test_comparator_rejects_omitted_fact_check():
    snapshot, payload = inputs()
    payload["supply"]["checks"].pop()
    with pytest.raises(ValueError, match="Critical evidence checks"):
        validate_union(payload, snapshot, solve(snapshot))


def test_comparator_rejects_cross_role_authority():
    snapshot, payload = inputs()
    payload["engineering"]["checks"][0]["supporting_quotes"][0] = {
        "source_id": "pcn",
        "quote": snapshot.sources[0].text,
    }
    with pytest.raises(ValueError):
        validate_union(payload, snapshot, solve(snapshot))
