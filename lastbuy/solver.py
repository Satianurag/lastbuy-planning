"""Deterministic, scenario-robust, time/effectivity-constrained purchase allocation."""

from datetime import datetime

from ortools.sat.python import cp_model

from .domain import POLICY_VERSION, Snapshot, digest, now


def reconcile(snapshot: Snapshot, at: datetime | None = None) -> dict:
    at = at or now()
    blockers, exclusions, eligible = [], [], []
    if not snapshot.complete or snapshot.missing_sources:
        blockers.append("Source manifest is incomplete")
    if snapshot.quote.order_deadline <= at:
        blockers.append("Supplier order deadline has expired")
    for cohort in snapshot.cohorts:
        if cohort.engineering_released is not True:
            blockers.append(f"Engineering effectivity is not released: {cohort.id}")
    for scenario in snapshot.scenarios:
        if scenario.approved is not True:
            blockers.append(f"Demand scenario lacks approval: {scenario.id}")
        for demand in scenario.demand:
            if demand.signed_coverage is not True:
                blockers.append(f"Signed coverage is unresolved: {demand.cohort}")
            if demand.coverage_component != snapshot.material:
                blockers.append(
                    f"Coverage applies to another component: {demand.cohort}"
                )
            if demand.due > demand.coverage_end:
                blockers.append(
                    f"Demand exceeds confirmed support window: {demand.cohort}"
                )
    revisions = {r for c in snapshot.cohorts for r in c.compatible_revisions}
    seen = {}
    for lot in sorted(snapshot.lots, key=lambda x: x.id):
        key = (lot.owner, lot.physical_id)
        # Custodian, source record ID and evidence may differ for the same stock.
        physical = lot.model_dump(mode="json", exclude={"id", "custodian", "evidence"})
        if key in seen:
            if physical != seen[key]:
                blockers.append(f"Conflicting physical-lot records: {lot.physical_id}")
            exclusions.append(
                {
                    "lot": lot.id,
                    "quantity": lot.quantity,
                    "reason": "duplicate custody",
                    "evidence": lot.evidence,
                }
            )
            continue
        seen[key] = physical
        if lot.revision is None or lot.quarantined is None or lot.confirmed is None:
            blockers.append(f"Unresolved lot eligibility: {lot.id}")
            reason = "unknown eligibility"
        elif lot.owner != snapshot.organization:
            reason = "not owned"
        elif lot.revision not in revisions:
            reason = "incompatible revision"
        elif lot.quarantined:
            reason = "quarantined"
        elif lot.kind == "inbound" and not lot.confirmed:
            reason = "unconfirmed inbound"
        else:
            reason = None
        if reason:
            exclusions.append(
                {
                    "lot": lot.id,
                    "quantity": lot.quantity,
                    "reason": reason,
                    "evidence": lot.evidence,
                }
            )
            continue
        if lot.reserved:
            exclusions.append(
                {
                    "lot": lot.id,
                    "quantity": lot.reserved,
                    "reason": "reserved",
                    "evidence": lot.evidence,
                }
            )
        eligible.append(
            {**lot.model_dump(mode="json"), "usable": lot.quantity - lot.reserved}
        )
    return {
        "blockers": sorted(set(blockers)),
        "eligible": eligible,
        "exclusions": exclusions,
    }


def solve(
    snapshot: Snapshot, at: datetime | None = None, timeout: float = 10.0
) -> dict:
    facts = reconcile(snapshot, at)
    base = {
        "schema_version": "1",
        "case_id": snapshot.case_id,
        "input_snapshot_sha256": digest(snapshot),
        "policy_version": POLICY_VERSION,
        "solver_version": "lastbuy-cpsat-1/ortools-9.15.6755",
        "currency": snapshot.quote.currency,
        "unit_price_minor": snapshot.quote.unit_price_minor,
        "baseline_quantity": snapshot.baseline_quantity,
        "baseline_commitment_minor": snapshot.baseline_quantity
        * snapshot.quote.unit_price_minor,
        "reported_on_hand": sum(
            lot.quantity for lot in snapshot.lots if lot.kind == "on_hand"
        ),
        "eligible_on_hand": sum(
            lot["usable"] for lot in facts["eligible"] if lot["kind"] == "on_hand"
        ),
        "confirmed_inbound": sum(
            lot["usable"] for lot in facts["eligible"] if lot["kind"] == "inbound"
        ),
        "exclusions": facts["exclusions"],
        "blockers": facts["blockers"],
        "evidence": [s.id for s in snapshot.sources],
        "allocations": [],
    }
    if facts["blockers"]:
        return {**base, "status": "NEEDS_REVIEW", "solver_status": "NOT_RUN"}
    model = cp_model.CpModel()
    quote = snapshot.quote
    packs = model.new_int_var(0, quote.max_quantity // quote.multiple, "packs")
    buy = model.new_int_var(0, quote.max_quantity, "purchase")
    model.add(buy == packs * quote.multiple)
    purchasing = model.new_bool_var("purchasing")
    model.add(buy >= max(1, quote.minimum)).only_enforce_if(purchasing)
    model.add(buy == 0).only_enforce_if(purchasing.Not())
    cohorts = {c.id: c for c in snapshot.cohorts}
    supplies = [
        *facts["eligible"],
        {
            "id": "NEW_PURCHASE",
            "revision": quote.revision,
            "usable": quote.max_quantity,
            "available": str(quote.available),
            "expires": None,
        },
    ]
    variables = []
    for scenario in snapshot.scenarios:
        if not scenario.protected:
            continue  # Stress scenarios reported separately; never silently certified.
        used = {s["id"]: [] for s in supplies}
        for index, demand in enumerate(scenario.demand):
            allocations = []
            for supply in supplies:
                if (
                    supply["revision"]
                    not in cohorts[demand.cohort].compatible_revisions
                ):
                    continue
                if supply["available"] > str(demand.due) or (
                    supply["expires"] and supply["expires"] < str(demand.due)
                ):
                    continue
                v = model.new_int_var(
                    0,
                    min(supply["usable"], demand.quantity),
                    f"{scenario.id}_{index}_{supply['id']}",
                )
                allocations.append(v)
                used[supply["id"]].append(v)
                variables.append(
                    (
                        v,
                        scenario.id,
                        index,
                        demand.cohort,
                        str(demand.due),
                        supply["id"],
                    )
                )
            model.add(sum(allocations) == demand.quantity)
        for supply in supplies:
            model.add(
                sum(used[supply["id"]])
                <= (buy if supply["id"] == "NEW_PURCHASE" else supply["usable"])
            )
    model.minimize(buy)  # One quoted part/price. Monetary ranking is equivalent.
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = timeout
    solver.parameters.num_search_workers = 1
    solver.parameters.random_seed = 7
    status = solver.solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return {
            **base,
            "status": "INFEASIBLE" if status == cp_model.INFEASIBLE else "NEEDS_REVIEW",
            "solver_status": solver.status_name(status),
            "blockers": [
                "No coverage-feasible purchase exists"
                if status == cp_model.INFEASIBLE
                else "Solver did not establish a feasible plan"
            ],
        }
    quantity = solver.value(buy)
    allocations = [
        {
            "scenario": sc,
            "demand_index": ix,
            "cohort": co,
            "due": due,
            "lot": lot,
            "quantity": solver.value(v),
        }
        for v, sc, ix, co, due, lot in variables
        if solver.value(v)
    ]
    result = {
        **base,
        "status": "READY_FOR_APPROVAL"
        if status == cp_model.OPTIMAL
        else "NEEDS_REVIEW",
        "solver_status": solver.status_name(status),
        "purchase_quantity": quantity,
        "commitment_minor": quantity * quote.unit_price_minor,
        "commitment_difference_minor": (snapshot.baseline_quantity - quantity)
        * quote.unit_price_minor,
        "allocations": allocations,
        "scenario_requirements": [
            {
                "id": s.id,
                "quantity": sum(d.quantity for d in s.demand),
                "protected": s.protected,
            }
            for s in snapshot.scenarios
        ],
        "optimality_gap_units": max(0, quantity - int(solver.best_objective_bound)),
    }
    if status != cp_model.OPTIMAL:
        result["blockers"].append(
            "Feasible incumbent is not proven optimal; review required"
        )
    verify_solution(snapshot, result, facts)
    return result


def verify_solution(snapshot: Snapshot, result: dict, facts: dict | None = None):
    """Independent arithmetic/constraint check, without calling the optimizer."""
    facts = facts or reconcile(snapshot)
    q = result["purchase_quantity"]
    quote = snapshot.quote
    if (
        q < 0
        or q > quote.max_quantity
        or q % quote.multiple
        or (q and q < quote.minimum)
    ):
        raise ValueError("Purchase violates supplier constraints")
    if result["commitment_minor"] != q * quote.unit_price_minor:
        raise ValueError("Incorrect commitment")
    supplies = {s["id"]: s for s in facts["eligible"]}
    supplies["NEW_PURCHASE"] = {
        "revision": quote.revision,
        "usable": q,
        "available": str(quote.available),
        "expires": None,
    }
    cohorts = {c.id: c for c in snapshot.cohorts}
    protected = {s.id: s for s in snapshot.scenarios if s.protected}
    used, covered = {}, {}
    for a in result["allocations"]:
        if a["scenario"] not in protected or a["lot"] not in supplies:
            raise ValueError("Unknown allocation scope")
        scenario = protected[a["scenario"]]
        ix = a["demand_index"]
        if not isinstance(ix, int) or not 0 <= ix < len(scenario.demand):
            raise ValueError("Unknown demand index")
        demand = scenario.demand[ix]
        s = supplies[a["lot"]]
        n = a["quantity"]
        if (
            type(n) is not int
            or n <= 0
            or a["cohort"] != demand.cohort
            or a["due"] != str(demand.due)
        ):
            raise ValueError("Invalid allocation")
        if (
            s["revision"] not in cohorts[demand.cohort].compatible_revisions
            or s["available"] > str(demand.due)
            or (s["expires"] and s["expires"] < str(demand.due))
        ):
            raise ValueError("Allocation violates effectivity/time")
        key = (scenario.id, a["lot"])
        used[key] = used.get(key, 0) + n
        covered[(scenario.id, ix)] = covered.get((scenario.id, ix), 0) + n
    if any(n > supplies[lot]["usable"] for (_, lot), n in used.items()):
        raise ValueError("Physical stock consumed more than once in a scenario")
    for sc in protected.values():
        for ix, d in enumerate(sc.demand):
            if covered.get((sc.id, ix), 0) != d.quantity:
                raise ValueError("Protected service demand is not covered")
