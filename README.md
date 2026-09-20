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
- Entra PKCE sign-in and API JWT checks; budget admission guard; responsive case workspace, source review, import preview and evidence packet download.

## Demonstration economics

All figures are synthetic. An 18,000-unit proposal at $80 costs $1.44m. Reported 14,000 stock includes 2,000 duplicate-custody units, 3,000 incompatible units and 1,000 quarantined units: 8,000 are usable. Add 4,000 confirmed inbound against 22,000 protected demand. The recommendation is **10,000 new units / $800,000**, a **$640,000 modeled commitment difference**. This is not achieved savings. Reserving 1,000 usable units increases the new purchase to 11,000 and invalidates earlier approvals.

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

The normal application always invokes the version-pinned hosted agent and shared admission ledger. There is no silent mocked-model fallback. Local demo identities must never be exposed through a public tunnel. The separate Durable/Azurite development mode is documented in [the runbook](docs/07-runbook.md).

```sh
.venv/bin/pytest -q --junitxml=evidence/implementation-tests.xml
.venv/bin/ruff check lastbuy functions export_functions scripts tests
.venv/bin/python -m scripts.evaluate offline
```

Live evaluation consumes the shared allowance. Do not run it automatically on every build. The application allowance reserves failed/uncertain attempts and cannot be independently reset by starting another process. The user authorized **₹1,000 total development/testing**, allocated conservatively as ₹700 model/prior-use admission allowance plus ₹300 infrastructure buffer. This is not an Azure billing hard cap; billing API throttling prevents verified actual-cost reporting.

## Deployment and review

- [Current implementation and evidence](docs/06-implementation-status.md)
- [Operations, deployment, rollback and cleanup](docs/07-runbook.md)
- [Contest handover and three-minute recording script](docs/08-contest-handover.md)
- [Exact buyer, financial evidence and competitors](docs/01-business-case.md)
- [Foundry feature decisions](docs/02-foundry-capability-audit.md)
- [Architecture and contracts](docs/03-architecture-and-contracts.md)
- [Original build/evaluation plan](docs/04-build-evaluation-and-demo.md)

Key code: `lastbuy/` domain, solver, workflow, authorization and adapters; `hosted/` Foundry entrypoint; `functions/` Durable orchestration and web API; `export_functions/` isolated export worker; `web/` decision workspace; `evaluations/` frozen synthetic cases; `evidence/` reproducible execution records.

Research and historical checkpoints are dated. The current implementation report supersedes the original setup-only notes. Public Git repository creation and contest submission are not automatic parts of deployment. The participant must record and edit their own final video under the official contest rules.
