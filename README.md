# LastBuy — verify the final purchase before it becomes irreversible

A working Microsoft Foundry application for an industrial thermal-camera OEM's final purchase of a discontinued image-processing ASIC. The buyer is the Director of Global Service Supply Chain. The workspace reconciles released engineering applicability, component-specific service obligations, uniquely owned usable stock and confirmed deliveries, then requests four distinct human approvals for an exact, versioned purchase plan.

**Cloud workspace:** https://lastbuy-dev-4126.azurewebsites.net/ — single-tenant Microsoft sign-in. The provisioned real user is a planner, not a financial approver. **Local demonstration:** http://127.0.0.1:8810/ — explicit synthetic role switching, loopback only.

This is an implemented and cloud-tested development prototype. Enterprise source records and ERP are synthetic; Microsoft Foundry, Azure Functions, Azure SQL, Blob and Entra wiring are real. No real purchase has been submitted. Customer adapters, independent evaluation, actual buyer validation and production operations remain deployment gates.

## What works

- Four bounded, read-only Foundry specialists: engineering, service coverage, supply and commitment. Hosted release v7 includes mandatory source-fact extraction, exact quotes and server comparisons after v3 stress testing exposed missed contradictions.
- CP-SAT allocation with an independent verifier. The model cannot choose purchase quantities or override constraints. Inputs use integer units/minor currency amounts and canonical hashes.
- Durable Functions orchestration; SQL decision ledger; source archive; optimistic concurrency; hash-linked audit; approval expiry and invalidation when sources/policy change.
- Four distinct engineering, service, finance and procurement identities, with current role/amount authority checked before export. Unresolved review findings block approval.
- Separate export Function identity and separate SQL ERP simulator, with a unique external reference and recovery after an uncertain write. No purchase-order release API exists.
- Entra PKCE sign-in verified in Firefox, API JWT checks and budget admission guard; responsive case workspace, scenario coverage, source review, import preview and evidence packet download.
- Source-owner and historical-number validation, analysis cancellation and authoritative approval timeout. Versioned Durable orchestration preserves existing replay histories. Live acceptance checks exposed and drove fixes for a historical-stock error and a SQL connection timeout.
- Read-only recorded-response inspection exposes the hosted version, scoped tool, original model summary and quoted structured facts, with current validation shown separately. The captured failure visibly distinguishes 4,800 current units in the summary from the incorrect 6,000-unit structured input.

## Demonstration economics

The enterprise example figures are synthetic. An 18,000-unit proposal at $80 costs $1.44m. Reported 14,000 stock includes 2,000 duplicate-custody units, 3,000 incompatible units and 1,000 quarantined units: 8,000 are usable. Add 4,000 confirmed inbound against 22,000 protected demand. The recommendation is **10,000 new units / $800,000**, a **$640,000 modeled commitment difference**. This is not achieved savings. Reserving 1,000 usable units increases the new purchase to 11,000 and invalidates earlier approvals.

## Run locally

Requires Python 3.13, Azure CLI authenticated to the configured project, and the pinned dependencies. This workspace already has `.venv`. For a clean checkout:

```sh
python3.13 -m venv .venv
.venv/bin/pip install -r requirements.lock.txt
```

```sh
set -a
source .env.example
set +a
LASTBUY_AUTH_MODE=local-demo LASTBUY_DATABASE_URL=sqlite:///data/lastbuy.db \
  .venv/bin/uvicorn lastbuy.api:create_app --factory --host 127.0.0.1 --port 8810
```

New analyses invoke the version-pinned hosted agent and shared admission ledger; inspecting completed results makes no new model call. There is no silent mocked-model fallback. Local demo identities must never be exposed through a public tunnel. The separate Durable/Azurite development mode is documented in [the runbook](docs/07-runbook.md).

```sh
.venv/bin/pytest -q --junitxml=evidence/implementation-tests.xml
.venv/bin/ruff check lastbuy functions export_functions scripts tests
.venv/bin/python -m scripts.evaluate offline
```

Live evaluation consumes the shared allowance. Do not run it automatically on every build. The application allowance reserves failed/uncertain attempts and cannot be independently reset by starting another process. The user authorized **₹1,000 total development/testing**, allocated conservatively as ₹700 model/prior-use admission allowance plus ₹300 infrastructure buffer. Reservations are not actual Azure charges or a billing hard cap. Azure Cost Management reported ₹112.28 month-to-date ActualCost for the whole subscription on 24 September 2026; this is posted usage at query time, not a LastBuy-only cost allocation. The earlier HTTP 429 was a failed historical query.

## Deployment and review

- [Current implementation and evidence](docs/06-implementation-status.md)
- [Requirement-by-requirement completion audit](docs/09-completion-audit.md)
- [Operations, deployment, rollback and cleanup](docs/07-runbook.md)
- [Contest handover and three-minute recording script](docs/08-contest-handover.md)
- [Professional contest assessment, 20 September 2026](docs/10-contest-strategy-2026-09-20.md)
- [Final three-reviewer demo assessment, 22 September 2026](docs/13-final-demo-review-2026-09-22.md)
- [Required Architect supporting PDF](output/pdf/LastBuy-Architect-Solution-Design.pdf)
- [Exact buyer, financial evidence and competitors](docs/01-business-case.md)
- [Foundry feature decisions](docs/02-foundry-capability-audit.md)
- [Architecture and contracts](docs/03-architecture-and-contracts.md)
- [Original build/evaluation plan](docs/04-build-evaluation-and-demo.md)

Key code: `lastbuy/` domain, solver, workflow, authorization and adapters; `hosted/` Foundry entrypoint; `functions/` Durable orchestration and web API; `export_functions/` isolated export worker; `web/` decision workspace; `evaluations/` frozen synthetic cases; `evidence/` reproducible execution records.

Research and historical checkpoints are dated. The current implementation report supersedes the original setup-only notes. Source is backed up in a private GitHub repository; no contest entry has been submitted. The participant must record and edit their own final video under the official contest rules.

### Real public market evidence

Open [the supplier evidence screen](https://lastbuy-dev-4126.azurewebsites.net/?view=market) for directly observed USD/INR prices, quantity tiers, stock limits and an onsemi discontinuance notice. The calculator preserves five-decimal unit pricing, blocks estimates beyond observed availability or after its freshness window, and cannot write purchase decisions. Research and refresh instructions: [public market evidence](docs/11-public-market-evidence.md).

## Current submission package

The eight-page Architect PDF, short description, canonical recording guide and integrity manifest are indexed in `output/submission/README.md`. The **seven-scene, 175-second** script in `submission/entry.json` starts with the enterprise purchase, shows governing evidence and recorded Foundry responses, then the captured failure and authority/recovery controls. Real public onsemi evidence is supporting material, separate from the example's assumed USD 80 price. See [the click guide](output/demo/START-HERE.md). Final participant video/screenshots, participant review and Founderz submission remain pending.
