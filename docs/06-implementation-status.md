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
| Separate exporter identity and independent ERP database | `cloud-export-verification.json`: actual cloud worker created one synthetic requisition; repeat returned same receipt; separate preseeded lost-response case reconciled one receipt. Model/approval identities in this integration test are explicit fixtures. |
| Browser workflow | Import, case switch, source viewer, four local demo approvals, lost-response/reconcile; 390px layout checked. Latest cloud plan visibly shows 10,000 / $800,000 / $640,000 in local workspace. |
| Automated checks | **123 passed**, JUnit `implementation-tests.xml`; **60/60 offline evaluation cases** (50 solver fixtures + 10 security regression references); Ruff and JavaScript syntax checks |
| Observability | `lastbuy-deployed-model-traces.json` contains correlated model/tool spans; input/output content capture disabled explicitly for current hosted release and Durable |
| Budget enforcement | Shared SQL admission ledger, atomic reservation, retained failure allowance, full-run preflight, concurrency tests; no automatic replenishment |

## Live model evaluation: failures remain visible

| Release / set | Attempts | Correct accepted classifications | Abstentions | Silent pass of a conflict | Clean cases accepted |
|---|---:|---:|---:|---:|---:|
| v3 original frozen text stress set | 12 | 7 | 1 | **4 of 7 conflicts** | 3/3 |
| v4 synthetic acceptance after tuning | 12 | 9 | 3 | 0 of 7 conflicts | 3/4 |
| v7 selected regression after fixes | 9 | 6 | 3 | 0 of 4 conflicts | 4/4 |

In the v7 conflict subset, one case returned an explicit blocker and three failed validation/abstained. **Do not call this 100% model accuracy or 100% conflict explanation quality.** No silent conflict pass was observed in this small subset; it does not establish a production false-negative rate. The source-injection case also completed without following the injected approval/export instruction.

The final regression reused cases after inspection; it is not a new holdout. The original 60-case offline suite is not 60 live LLM tests. All labels/cases are author-created and synthetic. A controlled single-agent comparison, incumbent/manual comparison, independent buyer usability study and customer-data evaluation have not been completed. Four-agent superiority is unproven.

Raw records, failed attempts, suite hashes and summary are retained in `evaluations/` and `evidence/evaluation-summary.json`.

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

The user authorized **₹1,000 total**. The shared ledger has a ₹700 admission allowance (including ₹200 reserved for prior activity) and ₹300 infrastructure buffer. Latest checkpoint: **₹680 reserved allowance, ₹20 unreserved allowance**. These are deliberately conservative allocations, **not an invoice**. A new four-stage analysis needs ₹40 allowance and is therefore blocked before any paid call. Existing results, approvals, source review and synthetic export can still be demonstrated.

Azure Cost Management repeatedly returned HTTP 429. Actual billed spend is **unverified**, not zero. Empty/zero token metrics are not proof of no usage. No extra paid benchmarking is authorized beyond the existing cap, and the ledger has not been replenished to finish tests. See `budget-status.json` and `cost-management-current.json`.

## Remaining external gates

- The real user's browser OAuth/MFA login for the new LastBuy app is awaiting confirmation. The sign-in redirect, API 401 boundary and JWT validation tests passed; successful browser login must not be claimed yet.
- Customer-owned SAP, PLM, contract and service data/adapters, registered real approvers, independent evaluation, buyer validation and finance-verified savings are necessary before production use. Source-system labels and model extraction are not substitutes for trusted connector authority.
- The participant must review the authenticated Founderz form, create their own recording/editing, and submit the entry. Gated curriculum and final submission form were not accessed. No public Git repository or contest entry has been published.

Code, source archives, research, test evidence, operating runbook and submission/recording script are ready for review. These deliverables are a cloud-tested contest prototype, not a claim that a real enterprise production rollout or contest submission is complete.
