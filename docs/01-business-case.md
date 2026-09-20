# LastBuy: verify the final semiconductor purchase before it becomes irreversible

Research date: 20 September 2026. This is the business rationale and customer validation plan for the cloud-tested development prototype; no deployed customer system or achieved savings is claimed.

## Decisive recommendation

Build LastBuy for the **Director of Global Service Supply Chain at an industrial thermal-camera OEM**. It reconciles a proposed final purchase of one discontinued image-processing ASIC against serial-specific service coverage, approved board compatibility, uniquely owned usable inventory, and confirmed receipts. It produces a versioned, reproducible purchase recommendation and a human-approved requisition payload before the supplier's non-cancellable order deadline.

The entry point is an existing last-time-buy case and proposed purchase quantity. The product is a decision workspace: evidence conflicts, quantity bridge, coverage scenarios, approvals and export status. The central interaction is reviewing a purchase decision, not asking a chatbot questions.

Initial commercial scope: one OEM business unit, one discontinued component per case, multiple eligible camera cohorts and depots. Exclude safety-critical control systems, counterfeit sourcing, automatic engineering qualification, and autonomous purchase-order release. These exclusions keep the technical authority and evidence requirements concrete.

## What the evidence proves—and what it does not

| Evidence | Supported conclusion | Limit |
| --- | --- | --- |
| [Teledyne Q2 2026 filing, Note 6](https://www.sec.gov/Archives/edgar/data/1094285/000109428526000043/tdy-20260628.htm) reports $1,166.4m net inventories, including $738.1m raw materials/supplies; its excess/obsolete adjustment considers part quantities, demand and historical use. | Inventory and its mismatch to demand are material financial exposures in an actual industrial-imaging parent company. | Consolidated company figures, not FLIR-only exposure, not last-time-buy losses, not recoverable savings. |
| [FLIR 2–10 warranty](https://www.flir.com/en-ca/support/warranty/instruments/2-10-thermal-camera-warranty-from-flir/) separates general camera coverage from ten-year detector coverage. [Extended warranty example](https://support.flir.com/dsdownload/assets/inst-ew-0120-en-us.html) describes parts/labor coverage. | Service obligations differ by component, product and contract. | A ten-year detector warranty does **not** establish ten-year coverage for an image-processing ASIC. Never extrapolate it that way. |
| Manufacturer-authored [FLIR PCN20250004, distributed by DigiKey](https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/7333/PCN20250004.pdf), identifies camera discontinuation due to component availability and qualified acceptance of final orders. | Component availability can cause an imaging product's discontinuation; final-order fulfillment is not automatically guaranteed. | This is a machine-vision camera notice, not proof of our hypothetical thermal-camera ASIC case. |
| [Rochester's obsolescence discussion](https://www.rocelec.com/news/predicting-component-obsolescence) describes long-lived systems and uncertain/short discontinuation notices. [Authorized distribution](https://www.rocelec.com/solutions/authorized-distribution) supplies EOL parts beyond original availability. | Final-buy planning is a real industry practice. Authorized future supply can change the optimal decision. | A supplier's market discussion does not establish a customer's loss or willingness to buy LastBuy. |
| [End-of-Life Inventory Management Problem](https://arxiv.org/abs/2101.09729), Ozyoruk, Erkip and Ararat | Established research models existing stock, ordering and outside sources; ignoring alternatives can be costly. | Our forecast/optimization is not a new scientific invention; results from that paper are not LastBuy performance. |

**Confidence:** high that the problem category is real and financially material; medium that this cross-system verification gap is underserved; unverified that a named buyer has the exact gap, accessible records, or purchase intent. We have not interviewed a buyer, accessed a real customer ERP, or measured recoverable spend. That distinction must remain visible in the pitch.

## Existing products and the actual differentiation hypothesis

| Product | Already does | LastBuy's proposed place |
| --- | --- | --- |
| [PTC Servigistics](https://www.ptc.com/en/products/servigistics/capabilities) | Service-parts planning, lifecycle demand and last-time-buy capability. | Consume its approved demand scenarios; verify the eligibility and inventory inputs to a particular final commitment. Do not rebuild its entire forecasting suite. |
| [Z2Data Lifecycle Management](https://www.z2data.com/products/lifecycle-management/) | Multi-level BOM impact, obsolescence cases, ERP/PLM integration, evidence, approvals and last-time-buy documentation. | An executable reconciliation across signed service obligations, serial-level engineering applicability and unique stock ownership, with freshness-bound approval and duplicate-write prevention. Merely adding audit trails or approvals would not differentiate us. |
| [SiliconExpert](https://www.siliconexpert.com/by-role/engineering/) | Component lifecycle intelligence, BOM risk, alerts and alternatives. | Treat authoritative lifecycle/PCN feeds as inputs. Engineering approval of a substitute remains with the OEM. |
| [Syncron inventory planning](https://www.syncron.com/blog/back-to-basics-the-fundamentals-of-inventory-optimization-part-two) | Inventory/network planning, retention and obsolescence considerations. | Verify the particular supply and obligation facts behind the commit decision; export into existing planning/procurement workflows. |

Public material cannot prove that none of these products can be configured to do the same thing. The defensible claim is a **specific implementation and measurable workflow improvement**, not “world's first.” The competitive test is to give the same conflicting case to the incumbent workflow and LastBuy, with the same qualified forecast/solver, and measure resolution time, missed constraints and unsupported assumptions.

## Buyer, users and prerequisites

- Economic buyer: Director/VP Global Service Supply Chain, accountable for service-parts inventory and repair availability. Finance controller co-signs the investment and material commitments.
- Champion/operator: service-parts planner or obsolescence manager handling a final-buy notice.
- Engineering approver: sustaining electronics engineer owning released BOM effectivity, substitution and repair compatibility.
- Service approver: service-program/contract owner owning coverage, support end date and exception interpretation.
- Procurement approver: commodity manager with supplier terms, MOQ/order multiples, NCNR deadline and purchase authority.
- Finance approver: controller approving amount and approved risk assumptions.
- IT/data owners: SAP MM owner, PLM owner, Dataverse/service-system owner, enterprise identity/security team.

Minimum viable customer data: a released BOM/effectivity export, installed-base cohort records, signed service coverage records, repair consumption, uniquely identifiable stock/inbound records, supplier notice/quote and the currently proposed quantity. Missing fields become explicit blockers. A CSV/JSON export with timestamps is a valid pilot input; pretending to have a live SAP integration is not.

## Financial case without invented ROI

Synthetic demonstration: baseline proposal 18,000 ASICs at $80 = $1.44m. Reported inventory is 14,000; mutually exclusive exclusions remove 2,000 duplicate-custody records, 3,000 incompatible units and 1,000 quarantined units, leaving 8,000 eligible. Confirmed, compatible inbound is 4,000. An approved service-demand scenario originally required 20,000; a scoped contract amendment raises it to 22,000. Required new purchase is 22,000 − 8,000 − 4,000 = 10,000, costing $800,000. Commitment difference is $640,000 (44.4%).

These numbers are deliberately constructed test data. The $640,000 is a **modeled commitment reduction**, not profit, realized cash savings, inventory already freed, or avoided write-off. Both alternatives must use the same updated coverage requirement. The amendment alone increases the recommendation from 8,000 to 10,000; show this to prove the system does not always minimize purchases at the expense of coverage.

Measure a pilot using matched historical cases: baseline proposed commitment; planner-accepted revised commitment; subsequent receipts/credits; planning labor; service availability; forecast calibration; data remediation cost. Finance signs off the counterfactual. An illustrative 15% annual carrying rate on a genuinely avoided $640,000 balance is $96,000/year before implementation costs—but 15% is a scenario assumption, not a researched customer rate, and principal and annual carrying savings must not be double counted.

Proceed to a commercial pilot only if a buyer supplies at least 10 historical final-buy cases and a data owner confirms identifiers/effectivity. Target at least 50% reduction in active reconciliation time without increased missed coverage constraints, and positive finance-reviewed net benefit after integration and operation costs. If incumbent configuration resolves the same problem cheaply or IDs cannot be reconciled safely, narrow to an incumbent extension or stop the commercial investment. A synthetic contest demo cannot satisfy this customer-validation gate.

## Real public market reference added to the submission

The separate onsemi AP0202AT2L00XPGA0-DR reference now provides directly observed USD/INR prices and manufacturer notice PD27281ZA, with final-buy date 7 October 2026. See [the dated source record](11-public-market-evidence.md). This grounds the commercial context; it does not identify a real thermal-camera customer using that SKU, replace the example ASIC price, or prove customer qualification for the manufacturer-recommended replacement.
