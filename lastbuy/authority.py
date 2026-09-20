"""Record-owner checks at the business boundary, independent of model interpretation.

These validate a trusted ingester's manifest, not the authenticity of an external
system. Customer connector credentials and attestations remain a deployment gate.
"""

from .domain import Snapshot


def authority_issues(snapshot: Snapshot) -> list[str]:
    systems = {s.id: s.system for s in snapshot.sources}
    issues = []

    def requires(record, evidence, allowed, description):
        if not any(systems.get(ref) in allowed for ref in evidence):
            issues.append(f"{record}: {description}")

    for cohort in snapshot.cohorts:
        requires(
            cohort.id,
            cohort.evidence,
            {"Windchill"},
            "engineering applicability requires a PLM-owned record",
        )
    for scenario in snapshot.scenarios:
        for demand in scenario.demand:
            record = f"{scenario.id}/{demand.cohort}"
            requires(
                record,
                demand.evidence,
                {"Contracts", "Dataverse"},
                "service coverage requires a contract/service-owned record",
            )
            requires(
                record,
                demand.evidence,
                {"Planning"},
                "demand requires an approved planning-system record",
            )
    for lot in snapshot.lots:
        requires(
            lot.id,
            lot.evidence,
            {"SAP", "Depot"},
            "physical inventory requires an ERP/depot-owned record",
        )
    requires(
        "supplier quote",
        snapshot.quote.evidence,
        {"Supplier"},
        "purchase terms require a supplier-owned record",
    )
    return issues
