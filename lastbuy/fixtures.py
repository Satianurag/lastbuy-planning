"""Clearly synthetic, independently specified contest scenario. No customer data."""

import hashlib
from datetime import UTC, datetime

from .domain import Actor, Snapshot

DEMO_ACTORS = {
    "planner": Actor(
        id="demo-planner",
        name="Maya Chen",
        organization="NORTHSTAR",
        roles=["planner"],
        authority_minor=0,
    ),
    "engineering": Actor(
        id="demo-engineering",
        name="Arjun Rao",
        organization="NORTHSTAR",
        roles=["engineering"],
        authority_minor=0,
    ),
    "service": Actor(
        id="demo-service",
        name="Elena Ortiz",
        organization="NORTHSTAR",
        roles=["service"],
        authority_minor=0,
    ),
    "finance": Actor(
        id="demo-finance",
        name="David Kim",
        organization="NORTHSTAR",
        roles=["finance"],
        authority_minor=200_000_000,
    ),
    "procurement": Actor(
        id="demo-procurement",
        name="Sam Taylor",
        organization="NORTHSTAR",
        roles=["procurement"],
        authority_minor=200_000_000,
    ),
}


def demo_snapshot(case_id="LTB-2026-017") -> Snapshot:
    entries = [
        (
            "pcn",
            "Supplier",
            "PCN-SYN-017",
            "1",
            "Notice §2",
            "SYNTHETIC: ASIC-SYN-017 final order deadline 2026-10-15 23:59 UTC. Quote: USD 80 per EACH, revision A2, minimum 1,000, order multiple 1,000, max allocation 25,000. Delivery by 2027-01-01. Non-cancellable order; this is a planning fixture.",
        ),
        (
            "bom",
            "Windchill",
            "ECO-SYN-482",
            "C",
            "Released BOM rows 17–18",
            "SYNTHETIC RELEASED ENGINEERING RECORD: TC-640 board C firmware 4.2, serial N640-0001 through N640-9999; TC-320 board B firmware 3.8, serial N320-0001 through N320-9999. Both accept ASIC-SYN-017 revision A2. Revision A1 is incompatible. No substitute is engineering-qualified.",
        ),
        (
            "warranty",
            "Contracts",
            "WARRANTY-SYN-10",
            "1",
            "Warranty §4",
            "SYNTHETIC: Ten-year detector warranty covers the detector only. It does not cover the image-processing ASIC. Do not infer ASIC coverage from this warranty.",
        ),
        (
            "amendment",
            "Contracts",
            "SERVICE-SYN-A07",
            "2",
            "Signed amendment §3",
            "SYNTHETIC SIGNED SERVICE AMENDMENT: supersedes revision 1 for these serial cohorts. ASIC-SYN-017 repairs for TC-640 and TC-320 remain covered through 2031-12-31. Approved service forecast increases from 20,000 to 22,000 total units. This component-specific amendment, not the detector warranty, governs ASIC coverage.",
        ),
        (
            "forecast",
            "Planning",
            "FORECAST-SYN-2031",
            "3",
            "Approved scenario rows 1–2",
            "SYNTHETIC PLANNER-APPROVED conservative demand envelope: TC-640 requires 10,000 ASIC units by 2030-12-31; TC-320 requires 12,000 by 2031-12-31. These are approved scenario quantities, not calibrated failure probabilities.",
        ),
        (
            "stock",
            "SAP",
            "STOCK-SYN-0919",
            "7",
            "Material stock / batch rows",
            "SYNTHETIC: LOT-01 has 6,000 owned A2 units. LOT-02 has 2,000 owned A2 units in external depot custody. LOT-03 has 3,000 incompatible A1 units. LOT-04 has 1,000 quarantined A2 units. No reservations. All amounts are EACH.",
        ),
        (
            "depot",
            "Depot",
            "DEPOT-SYN-002",
            "2",
            "Custody ledger row 12",
            "SYNTHETIC: 2,000 A2 units for NORTHSTAR in LOT-02. This is the same physical lot recorded in SAP, not additional inventory.",
        ),
        (
            "inbound",
            "SAP",
            "PO-SYN-401",
            "4",
            "Confirmed schedule line 10",
            "SYNTHETIC: 4,000 confirmed A2 units owned by NORTHSTAR, expected 2027-01-01. This is separate physical lot LOT-05. No quarantine or reservations.",
        ),
    ]
    sources = [
        {
            "id": sid,
            "system": system,
            "record_id": record,
            "revision": rev,
            "effective_at": "2026-09-19",
            "observed_at": "2026-09-20T12:00:00Z",
            "locator": locator,
            "text": text,
            "sha256": hashlib.sha256(text.encode()).hexdigest(),
        }
        for sid, system, record, rev, locator, text in entries
    ]

    def lot(id, physical, quantity, revision="A2", **kwargs):
        return {
            "id": id,
            "physical_id": physical,
            "kind": "on_hand",
            "owner": "NORTHSTAR",
            "custodian": "MAIN",
            "revision": revision,
            "quantity": quantity,
            "available": "2026-09-19",
            "evidence": ["stock"],
            **kwargs,
        }

    return Snapshot.model_validate(
        {
            "case_id": case_id,
            "organization": "NORTHSTAR",
            "material": "ASIC-SYN-017",
            "title": "Thermal camera ASIC · final purchase",
            "synthetic": True,
            "source_revision": 1,
            "complete": True,
            "baseline_quantity": 18000,
            "sources": sources,
            "cohorts": [
                {
                    "id": name,
                    "board_revision": board,
                    "firmware": fw,
                    "serial_from": start,
                    "serial_to": end,
                    "compatible_revisions": ["A2"],
                    "engineering_released": True,
                    "evidence": ["bom"],
                }
                for name, board, fw, start, end in [
                    ("TC-640", "C", "4.2", "N640-0001", "N640-9999"),
                    ("TC-320", "B", "3.8", "N320-0001", "N320-9999"),
                ]
            ],
            "scenarios": [
                {
                    "id": "SERVICE-PROTECTED",
                    "label": "Approved service envelope",
                    "approved": True,
                    "protected": True,
                    "demand": [
                        {
                            "cohort": cohort,
                            "due": due,
                            "quantity": quantity,
                            "coverage_component": "ASIC-SYN-017",
                            "coverage_end": "2031-12-31",
                            "signed_coverage": True,
                            "evidence": ["amendment", "forecast"],
                        }
                        for cohort, due, quantity in [
                            ("TC-640", "2030-12-31", 10000),
                            ("TC-320", "2031-12-31", 12000),
                        ]
                    ],
                }
            ],
            "lots": [
                lot("SAP-01", "LOT-01", 6000),
                lot("SAP-02", "LOT-02", 2000),
                lot("WMS-02", "LOT-02", 2000, custodian="DEPOT", evidence=["depot"]),
                lot("SAP-03", "LOT-03", 3000, "A1"),
                lot("SAP-04", "LOT-04", 1000, quarantined=True),
                lot(
                    "PO-05",
                    "LOT-05",
                    4000,
                    kind="inbound",
                    available="2027-01-01",
                    evidence=["inbound"],
                ),
            ],
            "quote": {
                "revision": "A2",
                "unit_price_minor": 8000,
                "currency": "USD",
                "minimum": 1000,
                "multiple": 1000,
                "max_quantity": 25000,
                "available": "2027-01-01",
                "order_deadline": "2026-10-15T23:59:00Z",
                "evidence": ["pcn"],
            },
        }
    )


FIXTURE_CLOCK = datetime(2026, 9, 20, 12, tzinfo=UTC)
