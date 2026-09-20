# Build order, evidence gates and contest demonstration

This document defines future work. A planned test is not a passed test. The current setup report identifies what has actually run.

## Build in dependency order

| Gate | Build deliverable | Required evidence before continuing |
| --- | --- | --- |
| 0. Preparation | Capability audit, buyer/problem evidence, architecture decisions, installed/pinned tools, Azure authentication, model and hosted-runtime probes. | Reproducible local and cloud tool-call result; deployment version and region recorded; no secrets in repository. |
| 1. Domain contract | Data dictionary, source precedence, approval policy, typed schemas and synthetic truth set. | Engineering/service reviewer can determine the correct result without an LLM. All demo quantities trace to fixtures. Commercial pilot additionally needs customer case/data validation. |
| 2. Deterministic core | Unit/alias rules, lot conservation, scenario allocation, solver verifier, state transitions and export idempotency. | Brute-force cross-checks on small allocations; negative-state-transition and timeout/duplicate-write tests. |
| 3. Agent evidence extraction | Four bounded roles, typed tools, evidence resolution and abstention. | Held-out extraction/contradiction tests, tool traces, schema validation and no critical unsupported facts entering a certifiable plan. |
| 4. Vertical case workflow | Snapshot → analyze → review → approve → revalidate → draft export. | One complete synthetic case including changed source, revoked approval and retry after uncertain export. |
| 5. Decision UI | Case queue, evidence comparison, quantity bridge, scenario comparison, role approvals and export receipt. | Task-based usability sessions; keyboard access; clear loading/error/stale/infeasible states. UI labels synthetic sources. |
| 6. Operational hardening | Durable Functions, SQL/Blob, Entra scopes, trace redaction, resource/cost limits, release and rollback. | Crash/replay tests, access-denial tests, restored database evidence, runtime permissions and observed telemetry. |
| 7. Contest release | Frozen demo dataset, versioned deploy, evaluations, 3-minute script, screenshots, lessons and concise description. | Demo repeatability on exact deployed version; own-recorded video within limits; actual submission requirements rechecked. |
| 8. Customer pilot | Real source adapters, buyer-approved metrics, private deployment, data agreement and baseline study. | Business improvement measured against current process with same coverage policy; no synthetic ROI represented as real. |

No deadline-driven shortcuts are required by this plan. However, the contest has a submission deadline independent of how much project-building time is available. Completing a production pilot is separate from presenting a credible contest prototype.

## Evaluation design

Use three baselines: existing manual/incumbent workflow; deterministic rules with pre-cleaned inputs; a single-agent implementation using the same tools. The four-agent design must outperform the simpler version on ambiguity/conflict quality enough to justify latency and tokens. If it does not, consolidate roles while preserving the workflow and controls.

Freeze a first suite of 60 independently specified cases: 20 ordinary cases, 15 obligation/engineering contradictions, 10 inventory/inbound edge cases, 10 injection/authorization/export failures and 5 insufficient-data/infeasible cases. This count is a planned starting suite, not an existing dataset. Split development and held-out cases before tuning, and separate nearly identical variants so they cannot leak between sets.

| Metric | Definition | Proposed acceptance gate |
| --- | --- | --- |
| Critical fact precision | Accepted coverage/compatibility/ownership facts supported by the gold source record. | Zero critical unsupported accepted facts in the release suite; report sample size, not a universal guarantee. |
| Evidence resolvability | Evidence locators resolve to the exact snapshotted record/field/clause. | 100% of decision-relevant facts. |
| Conflict/blocker recall | Material seeded contradictions/missing authority correctly block certification. | 100% of critical cases; target ≥95% overall. |
| Quantity/currency correctness | Exact match to deterministic reference for fully specified cases. | 100%; same constraints and scenario definitions. |
| Solver validity | Conservation, compatibility, periods, MOQ and service constraints hold. | 100%; report feasible/optimal/gap accurately. |
| Approval/write safety | Unauthorized, stale, duplicate, replayed or mismatched approvals cannot export. | Zero unsafe exports in adversarial suite. |
| Recovery | Retry/crash at each boundary produces consistent state and at most one externally identified requisition. | All injected failure cases reconcile; uncertain writes stay blocked. |
| Tool-call accuracy | Correct allowlisted tool, arguments, scope and version. | ≥98% on suite; any unsafe call is a blocker even if aggregate score passes. |
| User effectiveness | Planner can explain quantity bridge and find governing evidence without help. | ≥90% task success; measure active time against baseline. |
| Performance | End-to-end frozen case, warm/cold runs separated. | Target p95 ≤120s analysis; track each stage and use earlier completed stages for safe resume. Target, not measured performance. |
| Cost | Model tokens + tools + active compute + telemetry per completed case. | Record p50/p95, failed-case cost and retries; set numeric budget after actual tariff and workload measurement. |
| Business effect | Finance-approved commitment change at equal coverage, planning time, service outcome. | Positive net benefit; ≥50% active reconciliation-time reduction target for matched pilot cases. |

Foundry evaluation records model/tool quality and explanations; deterministic validators remain authoritative for arithmetic and approval gates. A high fluency or groundedness score alone cannot pass a purchasing release. An Invocations endpoint must be exercised by a custom evaluation adapter if a hosted-agent evaluation path only supports Responses.

Required edge cases: detector-only warranty incorrectly assumed to cover ASIC; superseded contract amendment; serial effectivity gap; ambiguous MPN alias; one lot in two custody systems; overlapping exclusion reasons; reserved inventory; quarantine released after deadline; inbound short shipment; late arrivals; MOQ rounding; pack-vs-each units; currency mismatch; depleted stock after approval; expired buyer authority; stale plan hash; repeated submit; ERP accepted but response lost; tool outage; cancellation; insufficient forecast exposure; solver timeout; prompt injection in a supplier note.

## Three-minute demo

All enterprise records and financial numbers are synthetic; Foundry calls and the running application must be real. Label those two facts separately. No accelerated recording represented as live timing; prepare the input snapshot ahead of the timed demo.

| Time | On screen | Point proved |
| --- | --- | --- |
| 0:00–0:20 | Final-buy case: deadline, discontinued ASIC, original 18,000-unit / $1.44m request. | One buyer, one consequential decision. |
| 0:20–0:55 | Run analysis; show four stage statuses and source evidence. Open the 14,000 → 8,000 inventory bridge. | Duplicate custody, incompatible revision and quarantine change usable supply. |
| 0:55–1:25 | Open signed synthetic service amendment; 20,000 → 22,000 required units. Show why detector-only warranty does not cover every ASIC repair. | Coverage interpretation changes real constraints; evidence is actionable. |
| 1:25–1:50 | Plan: 8,000 eligible + 4,000 inbound + 10,000 buy = 22,000. Compare $800k commitment to original $1.44m. | $640k modeled commitment reduction at the same updated coverage. |
| 1:50–2:20 | Approve a plan, then inject a stock revision change. Export becomes stale/blocked; recompute and require fresh approval. | Governance is implemented behavior, not a disclaimer or fake button. |
| 2:20–2:40 | Submit approved synthetic requisition; repeat submission returns the same external reference. | Separate human authority and duplicate-write protection. |
| 2:40–3:00 | Show Foundry trace, exact release test result, source labels and pilot targets. | Reliability and measurable impact; no claims of real SAP connectivity or achieved savings. |

If the full analysis exceeds the allotted portion, show a clearly labeled completed run and execute the freshness/approval/export interaction live. Never hard-code a “successful” agent result to simulate a real run.

## Contest alignment and source limitations

The official rubric allocates 30 points each to Innovation, Usability and Impact, with Innovation first in tie-breaking. Innovation rests on the executable, evidence-linked reconciliation and change-aware commitment, not a claim that last-time-buy planning is new. Usability is the quantity bridge, precise blockers and role-specific actions. Impact is a quantified synthetic scenario plus a credible measurement plan.

Submission checklist: ≤3-minute and ≤150 MB video via Founderz; short issue/impact/build description; clear audience; refinement summary; screenshots/example interactions; lessons learned; participant-original work and rights to content. The video itself must be the participant's own filming/editing/design work. Supporting documentation is optional. These requirements come from the [official rules](https://founderz.com/agentathon-terms/); check the logged-in submission form for any additional fields before uploading.

The rules' sections 3/4 specify 24 September 2026 at 23:59 PDT, while the prize section also mentions GMT. Until clarified, target the earlier 24 September 23:59 GMT (25 September 05:29 IST). Do not take “no time restrictions” to mean the competition has no cutoff.

Reviewed the [Microsoft event](https://www.microsoft.com/en-us/events/local-events/microsoft-agent-a-thon), [public Founderz Architect path](https://founderz.com/skilling/agent-a-thon-fz/sign-up/) and the actual [FrontierWeekHack repository](https://github.com/microsoft/FrontierWeekHack) at commit `cd7ec1717fbf109bf6e76edfa38a5a7cfc0d88ea`. The repo teaches build, monitor, evaluate and orchestration with Python; its examples are learning material, not an implementation specification for LastBuy. Its portal workflow step conflicts with newer retirement guidance, so adopt the learning objective using Agent Framework code. Gated Founderz lesson videos and the authenticated submission form have not been accessed; do not describe them as fully reviewed.
