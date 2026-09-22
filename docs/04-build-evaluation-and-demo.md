# Build order, evidence gates and contest demonstration

This document preserves the original build and acceptance plan. Much of the prototype is now implemented, but planned acceptance gates are not automatically passed. See [current implementation evidence](06-implementation-status.md) and the [requirement-by-requirement audit](09-completion-audit.md).

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

The current **seven-scene, 175-second** sequence is generated from `submission/entry.json` into [the contest handover](08-contest-handover.md) and `output/submission/recording-guide.md`. Start with the $1.44m enterprise proposal, establish protected demand, explain the quantity bridge, inspect a recorded Foundry response, then show the captured stock error, human authority and separate recorded recovery evidence. The response inspector exposes the correct 4,800-unit summary beside the wrong 6,000-unit structured fact and current refusal. Public onsemi evidence belongs in the supporting material. No fresh paid model call is required. Earlier market-first timings and the stock-reservation/reanalysis scene are superseded; [the September 22 review](13-final-demo-review-2026-09-22.md) explains the final choices.

## Contest alignment and source limitations

The official rubric allocates 30 points each to Innovation, Usability and Impact, with Innovation first in tie-breaking. Innovation rests on the executable, evidence-linked reconciliation and change-aware commitment, not a claim that last-time-buy planning is new. Usability is the quantity bridge, precise blockers and role-specific actions. Impact is a quantified synthetic scenario plus a credible measurement plan.

Submission checklist: ≤3-minute and ≤150 MB video via Founderz; short issue/impact/build description; clear audience; refinement summary; screenshots/example interactions; lessons learned; participant-original work and rights to content. The video itself must be the participant's own filming/editing/design work. The public rules describe supporting documentation as optional, but the authenticated Architect upload form requires PDF/Word support material (30 MB; pdf/docx/doc). Provide the design PDF. These requirements come from the [official rules](https://founderz.com/agentathon-terms/); check the logged-in submission form for any additional fields before uploading.

The rules' sections 3/4 specify 24 September 2026 at 23:59 PDT, while the prize section also mentions GMT. Until clarified, target the earlier 24 September 23:59 GMT (25 September 05:29 IST). Do not take “no time restrictions” to mean the competition has no cutoff.

The September 20 review covered the [Microsoft event](https://www.microsoft.com/en-us/events/local-events/microsoft-agent-a-thon), [public Founderz Architect path](https://founderz.com/skilling/agent-a-thon-fz/sign-up/) and actual [FrontierWeekHack repository](https://github.com/microsoft/FrontierWeekHack) at commit `cd7ec1717fbf109bf6e76edfa38a5a7cfc0d88ea`. The repo teaches build, monitor, evaluate and orchestration with Python; its examples are learning material, not an implementation specification for LastBuy. Its portal workflow step conflicts with newer retirement guidance, so adopt the learning objective using Agent Framework code. Public rules, event and repository were rechecked on September 22. The authenticated syllabus, written final activity and upload form were inspected on September 20; seven lesson videos have not all been watched. See [the final review](13-final-demo-review-2026-09-22.md) for exact review boundaries.
