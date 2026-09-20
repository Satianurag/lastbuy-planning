# LastBuy: current implementation and verified boundaries

Updated 20 September 2026. The development prototype is implemented and deployed. This report distinguishes real cloud execution from synthetic business data, tests, and work that needs the participant/customer. It supersedes the earlier setup checkpoints.

## Live result

- Cloud: https://lastbuy-dev-4126.azurewebsites.net/ (single-tenant Microsoft sign-in).
- Local: http://127.0.0.1:8810/ (explicit synthetic demo identities, loopback only).
- Current Foundry release: `lastbuy-analysis` **v7**, prompt `lastbuy-specialists-5`, policy `lastbuy-policy-3`; exact code archive in `evidence/lastbuy-agent-release.json`.
- Verified current cloud case: `LTB-CLOUD-RELEASE-7`, **READY_FOR_APPROVAL**, 10,000 units, USD 800,000 commitment, USD 640,000 modeled difference. All four hosted specialists, Azure Functions, SQL and Blob participated. No approval or ERP write occurred for this case.
- The exact completed synthetic cloud plan is also available locally for review without another paid model call. It is explicitly imported as an existing verified result, not presented as a new live execution.

The successful stage responses total **12,569 tokens** and **18.085 seconds** reported model/tool runtime. This excludes session startup, orchestration, SQL, retries and network latency. It is one observation, not a production p95. The budget ledger retains failed/retried attempts separately.

## Evidence map

| Capability | Verification |
|---|---|
| Deterministic purchase/lot conservation | CP-SAT solver and independent verifier; `tests/test_solver.py`; 50 structured constraint fixtures in frozen evaluation |
| Identity, role/amount authority, 4 distinct humans, stale/expired approval denial | Entra JWT tests and workflow negative tests; actual cloud real user is planner-only |
| Typed/hash-verified source input, read-only import preview | API/import tests and browser import/preview/save; no real SAP/PLM connector credentials used |
| Foundry bounded tools and exact citations | Versioned hosted runs; scoped structured output; source quote checks; mandatory critical-fact extraction and server comparison |
| Current full cloud path | `evidence/full-cloud-release7.json`; plan hash `631cb1a621d6…`; all four results pin v7 |
| Actual process crash/resume | `durable-before-crash.json`, `durable-after-restart.json`, `durable-completed-history.json`; same run resumed after worker SIGKILL using persisted Azurite history |
| Real SQL transactions and optimistic concurrency | `azure-sql-verification.json`; explicit test-double model, real Entra/TLS SQL |
| Real Blob content-addressed source archive | `azure-blob-verification.json`, current cloud plan archive receipt; conditional create and hash verification |
| Separate exporter identity and independent ERP database | `cloud-export-verification-LIVE-20260920.json` (fresh re-run after connection fix): actual cloud worker created one synthetic requisition; repeat returned same receipt; separate preseeded lost-response case reconciled one receipt. Model/approval identities in this integration test are explicit fixtures. |
| Browser workflow | Real Firefox Microsoft sign-in and protected cloud case data verified. Local import, case switch, source viewer, four demo approvals, lost-response/reconcile and 390px layout checked. Current result shows 10,000 / $800,000 / $640,000, with scenario coverage. Cancellation was exercised on an explicitly seeded no-model fixture; Return/Escape source-dialog focus behavior passed. See `browser-final-verification.json`. |
| Source-owner boundary | Engineering requires Windchill, coverage requires Contracts/Dataverse, demand requires Planning, lots require SAP/Depot and terms require Supplier manifest references. Five wrong-owner cases fail before analysis. These checks trust the ingester’s manifest; external authenticity is not proven. |
| Cancellation and approval timeout | Authoritative CANCELLED/APPROVAL_WAIT_EXPIRED transitions, no late result commit, no old-run expiry of a newer run; preserved approved-at-boundary behavior. V1 retained for history replay; v2 registered in cloud; actual local Functions/Azurite checkpoint-to-approval completion plus offline cancellation/expiry branches. Recovery reused recorded model responses. |
| Actual local backup/restore | SQLite backup restored while the independent synthetic ERP retained a newer receipt; reconciliation returned the same reference, one external row and a valid audit chain. `local-restore-verification.json`; model test double, not Azure SQL PITR. |
| Automated checks | **147 passed**, JUnit `implementation-tests.xml`; **60/60 offline evaluation cases** (50 solver fixtures + 10 security regression references); Ruff and JavaScript syntax checks |
| Observability | `lastbuy-deployed-model-traces.json` contains correlated model/tool spans; input/output content capture disabled explicitly for current hosted release and Durable |
| Budget enforcement | Shared SQL admission ledger, atomic reservation, retained failure allowance, full-run preflight, concurrency tests; no automatic replenishment |

## Live model evaluation: failures remain visible

| Release / set | Attempts | Correct accepted classifications | Abstentions | Silent pass of a conflict | Clean cases accepted |
|---|---:|---:|---:|---:|---:|
| v3 original frozen text stress set | 12 | 7 | 1 | **4 of 7 conflicts** | 3/3 |
| v4 synthetic acceptance after tuning | 12 | 9 | 3 | 0 of 7 conflicts | 3/4 |
| v7 selected regression after fixes | 9 | 6 | 3 | 0 of 4 conflicts | 4/4 |

In the v7 conflict subset, one case returned an explicit blocker and three failed validation/abstained. **Do not call this 100% model accuracy or 100% conflict explanation quality.** No silent conflict pass was observed in this small subset; it does not establish a production false-negative rate. The source-injection case also completed without following the injected approval/export instruction.

The final regression reused cases after inspection; it is not a new holdout. The original 60-case offline suite is not 60 live LLM tests. All labels/cases are author-created and synthetic. A matched-input single-call comparison has now been executed on the recorded golden case: four stages correctly accepted it; the single-call comparator returned an unnecessary review blocker. Broader incumbent/manual, buyer-usability and customer-data studies remain release-plan work. The one-case result does not establish universal four-agent superiority.

Raw records, failed attempts, suite hashes and summary are retained in `evaluations/` and `evidence/evaluation-summary.json`.

## Additional live acceptance run

Two actual Foundry calls were made after freezing `evaluations/live-acceptance-20260920.json`. The single-call comparator used the same four scoped assessment contracts, mandatory critical-field checks and server validation as the historical four-stage record. It used 8,363 response-reported tokens versus 12,569 for the four-stage record, but falsely escalated already-resolved duplicate custody. This is a one-case historical comparison, not a concurrent randomized trial or measured billing comparison.

A new stock test explicitly stated a 6,000-unit opening count and a 4,800-unit current balance. Hosted v7 selected the historical 6,000 and the previous validator accepted it. The captured raw failure is retained. The corrected API/workflow/authority gate now detects explicitly historical numeric evidence, including quotations that omit the temporal label by checking the surrounding source sentence. Replaying the actual response produces an explicit blocker and prevents plan approval. This is an evidence-validation fix; it does not claim that the model has learned the correct extraction. The actual deployed exporter also rejected a legacy-approved fixture using that response with HTTP 409 and zero external rows (`cloud-historical-gate-verification.json`). See `live-acceptance-summary.json`.

Actual Functions v2 executed all four saved stage checkpoints, archived/finalized the plan, waited, and completed after four synthetic role approvals. The model responses are exact recorded v7 results; no new inference was made for the recovery test. Histories are in `runtime-v2-checkpoint-*.json`.

Browser verification of the captured-failure case confirmed **NEEDS_REVIEW**, visibly provisional quantities, source inspection showing both 6,000 opening and 4,800 current units, and disabled approval/export even as the engineering demo role. The valid golden case retains its recommendation. Recorded model narrative is preserved with a reminder that decision gates govern the result.

A real cloud export attempt also exposed a transient SQL HYT00 connection failure. A bounded connection-only retry was added; fresh create and lost-response reconciliation tests then each retained exactly one external row and a valid audit chain. SQL statement execution is not replayed by this helper.

## Fixes motivated by observed failures

1. V3 sometimes marked an unreleased engineering record as merely `review`, and missed stock, inbound and supplier conflicts. All unresolved review findings now block financial approval. Specialist tools expose the underlying records. Mandatory extracted release status, coverage, signed authority, demand/stock quantities, inbound confirmation, price and allocation limit are compared with accepted fields by server code.
2. Exact supporting quotes are validated, and numeric extracted values must appear in those quotes. A punctuation bug rejected quoted quantities followed by a period; a regression test now covers it. These checks reduce unsupported acceptance but do not prove semantic correctness of every extracted fact.
3. Citation IDs are now derived from the model's validated quotes, avoiding two independently generated lists that could disagree. Unsupported explicit monetary narration fails closed.
4. Foundry's handling of 5xx responses repeated failed validation calls. The handler now returns 422 for application analysis failure, while the metered Durable workflow owns retries. Failed attempts remain charged to the conservative admission allowance.
5. Concurrent audit appends now always take the case optimistic lock, even when two approvals leave the status unchanged. This prevents two events from branching the hash chain; a targeted regression and a real Azure SQL concurrency check pass (`azure-sql-audit-concurrency.json`).
6. A partially funded four-stage run is rejected before its first model call. This prevents spending the remaining allowance on a run that cannot finish.

## Security and operational scope

The API verifies Entra issuer, tenant, audience, signature, expiry, delegated scope and a server-owned actor registry. Hosted agents have read-only evidence tools and no approval/export capability. The frontend cannot write to the ERP simulator database. The exporter can read current decision/authority records, update outbox status, append audit and insert a synthetic requisition; it has no Foundry role. Its archive permission is read-only, with host/deployment container permissions scoped separately.

SQL is Entra-only and TLS protected, restricted to a Functions VNet service endpoint plus one temporary developer IP. Both SQL databases use free-limit exhaustion AutoPause. Functions have zero always-ready instances. Blob shared keys and anonymous access are disabled.

Development limits: hosted input is capped at 12,000 UTF-8 bytes per snapshot for this budget-limited prototype; large enterprise document sets need a separately validated ingestion/chunking design. The frontend's host and archive share a storage account, Blob retention is not locked WORM, the server-to-exporter transport uses an encrypted Function key rather than workload-token authorization, production alert routing and point-in-time restore drills are not done, and no production private-endpoint topology is certified. Detailed recovery/rollback guidance is in the runbook.

`npm audit` reports four moderate findings in the local Azurite dependency tree, no high/critical findings. Its suggested “fix” downgrades Azurite to 2.7.1 and was not applied blindly. Azurite is loopback development tooling and is not shipped to Functions or the browser. The vendored browser MSAL dependency is not one of those findings.

## ₹1,000 development/testing cap

The user authorized **₹1,000 total**. The shared ledger has a ₹700 admission allowance (including ₹200 reserved for prior activity) and ₹300 infrastructure buffer. Latest checkpoint: **₹700 reserved allowance, ₹0 unreserved allowance**. These are deliberately conservative allocations, **not an invoice**. A new four-stage analysis needs ₹40 allowance and is therefore blocked before any paid call. Existing results, approvals, source review and synthetic export can still be demonstrated.

Azure Cost Management repeatedly returned HTTP 429. Actual billed spend is **unverified**, not zero. Empty/zero token metrics are not proof of no usage. No extra paid benchmarking is authorized beyond the existing cap, and the ledger has not been replenished to finish tests. See `budget-status.json` and `cost-management-current.json`.

## Remaining external gates

- Microsoft sign-in is verified for the real planner. Real engineering, service, finance and procurement approvers have not been onboarded; local role switching remains explicitly synthetic.
- Customer-owned SAP, PLM, contract and service data/adapters, registered real approvers, independent evaluation, buyer validation and finance-verified savings are necessary before production use. Source-system labels and model extraction are not substitutes for trusted connector authority.
- The authenticated Founderz syllabus, written assignment and upload form are now reviewed. Required six-page PDF support material is prepared; the participant must review it, create their own recording/editing and submit the entry. Seven lesson videos have not all been watched. No public Git repository or contest entry has been published.

Code, source archives, research, test evidence, operating runbook and submission/recording script are ready for review. These deliverables are a cloud-tested contest prototype, not a claim that a real enterprise production rollout or contest submission is complete.
