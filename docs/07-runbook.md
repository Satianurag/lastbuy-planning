# LastBuy development runbook

The deployed environment contains synthetic data. Do not load customer records until the customer's identity, data processing, retention and integration requirements have been reviewed. The implemented controls are not a production certification.

## Resource inventory and access

Subscription `73cf0b28-d8af-4012-94d0-e7f7fc3ddd36`; resource group `rg-anuragsati6476-5065`; region West US 3. This is a shared resource group: never delete it as a cleanup shortcut.

| Component | Resource / configuration |
|---|---|
| Foundry | Project `anuragsati6476-4126` in account `anuragsati6476-4126-resource`; agent `lastbuy-analysis`; pinned release in `evidence/lastbuy-agent-release.json` |
| Model | `lastbuy-dev-mini`, GPT-5.4-mini DataZoneStandard, 10 RPM / 10k TPM observed quota |
| Web/orchestrator | `lastbuy-dev-4126`, Flex Consumption Python 3.13, 2GB, zero always-ready instances |
| Export worker | `lastbuy-export-4126`, separate system identity, no Foundry role |
| Primary database | SQL server `lastbuy-dev-4126`, database `lastbuy`, Entra-only, TLS 1.2, free-limit AutoPause |
| ERP simulator | Same server, separate `lastbuy-erp-sim` database; frontend has no database principal there |
| Archive/host storage | `lastbuydev4126`, shared keys and anonymous blob access disabled |
| Network | `lastbuy-dev-vnet/functions`, Microsoft.Sql service endpoint and SQL VNet rule; temporary developer IP firewall rule |
| Identity | Single-tenant SPA/API `2f1dc01e-10f7-467f-a24a-9b7c2725aefe`; only own `access_as_user` delegated scope |
| Monitoring | `lastbuy-dev-insights`, `lastbuy-dev-logs`, 30-day retention, 0.1 GB daily ingestion cap |

SQL free allowance exhaustion pauses the databases; it is not permission to enable paid overage. Model quota is a throughput limit, not a spending limit. Source ZIPs are content-hashed and retained under `evidence/releases/`.

## Start and deploy

Run commands from the repository root. Authenticate using `az login` with the existing account and MFA; do not disable tenant security defaults. The earlier device-code flow was blocked by the tenant.

1. Load `.env.example` using `set -a; source .env.example; set +a`. This contains non-secret project settings. Never copy access tokens into configuration.
2. Run unit/integration tests and Ruff as shown in README. Offline evaluation does not call the model.
3. Package/release Foundry with `.venv/bin/python scripts/deploy_agent.py package`, then `deploy --new-version`, inspect `status`, and route only after the version is active. `route` changes new routing; callers still explicitly pin the version. Keep the previous archive for investigation. Update `LASTBUY_HOSTED_VERSION` in local, Functions and evaluation settings together.
4. Freeze a new acceptance set before live validation. A set used to tune a prompt is a regression set afterwards, never a fresh holdout. Use `.venv/bin/python -m scripts.evaluate live --suite release4` only within the remaining allowance. It resumes already-recorded attempts without paying for them twice.
5. Package worker with `.venv/bin/python scripts/package_functions.py --export`. Deploy the returned exact archive using `az functionapp deployment source config-zip -g rg-anuragsati6476-5065 -n lastbuy-export-4126 --src <archive> --build-remote true --timeout 600`.
6. Package web/orchestrator with `.venv/bin/python scripts/package_functions.py`; `.venv/bin/python -m scripts.release_functions` wires the current release and server-only worker key, then deploys the frozen archive. It never prints the key. App settings are encrypted by Azure; Key Vault-backed or workload-token worker authentication remains a production hardening task.
7. Check `/api/health`, `/api/auth/config`, and unauthenticated `/api/cases` (must be 401). Test actual Microsoft sign-in and a planner case. Never grant the planner all four approval roles to simplify a demo.

`prepare_cloud_database.py` and `configure_export_worker.py` are **operator-only**, idempotent schema/identity setup for these exact development resources. Runtime identities have no schema or identity-registry write permission. Do not run the budget initializer with a new account name to bypass the user's total cap.

A fresh Azure subscription additionally needs resource provisioning, appropriate hosted-agent/model quota, a new Entra app and tenant-specific principal mapping. Current setup scripts deliberately target verified existing resources; they are not a universal one-command production installer.

## Local Durable mode

Install locked tooling with `npm ci --prefix tooling`; start Azurite on loopback (`tooling/node_modules/.bin/azurite --location evidence/azurite-data`). From `functions/`, run Azure Functions Core Tools `func start --port 7071` with a private `local.settings.json`. Use `AzureWebJobsStorage=UseDevelopmentStorage=true`, `LASTBUY_DATABASE_URL` pointing to an absolute local SQLite path, the same Foundry/version/budget settings, and no `LASTBUY_ENABLE_WEB`. Start the API with `LASTBUY_DURABLE_URL=http://127.0.0.1:7071` and the same database. Local settings are ignored by Git.

Both processes must share the **same absolute case database**. Durable history stores case/run IDs, not source documents. Azurite persists queues/history; killing the worker does not delete state. A crashed activity may remain invisible until its storage queue lease expires (observed about five minutes). Avoid manually starting a second run while waiting for lease recovery.

New starts use `lastbuy_orchestrator_v2`. The original `lastbuy_orchestrator` is retained unchanged in `orchestration_v1.py` for existing histories. Do not remove v1 while instances still reference it, or rename activities used by its history. V2 adds authoritative expiry and pending-timer cleanup. Its branches have offline generator tests, registration is verified in Azure, and actual local Functions/Azurite execution resumed recorded v7 checkpoints and completed the approval wait. This recovery verification reused committed model outputs; it did not invoke another full model run.

## Recovery and authority

- Failed model call: case becomes `ANALYSIS_FAILED`; consumed allowance stays reserved. Inspect provider/validation failure, then retry explicitly. There is no success-shaped fallback.
- Stale plan: source revision/hash or policy mismatch invalidates approval. Re-analyze and collect all four approvals. Preserve prior plan versions.
- Rejected/unresolved evidence: correct the authoritative record/import, then rerun. Never edit a stored finding from blocker to info.
- Cancellation: a planner can cancel ANALYZING. Pending stages become CANCELLED; a paid call already in flight may finish and its allowance is not refunded. Its late result cannot commit a plan or authorize export.
- Approval expiry: approvals expire after 24 hours; server validates current actor role, organization and amount authority again. V2 also transitions an unfinished approval wait to APPROVAL_WAIT_EXPIRED. An old run cannot expire a newer one. Expiry does not grant authorization.
- Source ownership: fix an invalid source-owner manifest before analysis. A supplier citation cannot stand in for engineering release or service-coverage authority. This is manifest validation, not external connector authentication.
- Export timeout: reconcile the existing outbox key. The ERP may already have accepted the draft. Never mint a replacement key or manually change `EXPORT_UNCERTAIN` to `APPROVED`.
- SQL cold start: a free serverless database may require a first request to resume and can time out. Connection establishment now makes at most two attempts for recognized transient SQL states, including HYT00; authentication failures are not retried. A second failure remains visible and may require retry after resumption. SQL statements and external writes are not automatically replayed by this connection helper. Do not broaden the firewall or switch to password authentication in response to a transient timeout.
- Database conflict: optimistic version failures mean another actor changed the case. Refresh and review; do not retry an outdated approval automatically.

The exporter validates current source/archive/approval authority before its first write. After an uncertain write, it looks up the already-issued receipt before checking whether a new write would now be allowed. That is reconciliation, not renewed authorization.

## Monitoring and evaluation

App Insights contains correlated hosted model/tool spans. Content capture is explicitly off for new hosted releases, and Durable input/output tracing is off. Keep connection strings, JWTs, raw contracts and private reasoning out of logs. Case evidence remains in the authorized application/SQL/Blob paths.

Useful KQL in Application Insights:

```kusto
requests
| where timestamp > ago(24h)
| summarize calls=count(), failures=countif(success == false), p50=percentile(duration,50), p95=percentile(duration,95) by name
```

```kusto
dependencies
| where timestamp > ago(24h)
| where name has "lastbuy-dev-mini" or name has "read_case_evidence"
| project timestamp, operation_Id, name, duration, success
```

```kusto
exceptions
| where timestamp > ago(1h)
| summarize count() by type, outerMessage
```

Do not interpret SDK IMDS resource-detector warnings alone as failed model invocations. Correlate them to the request outcome. Configure production alert routing with the customer's on-call owner: any successful unauthorized write (zero tolerance), export uncertainty older than 15 minutes, analysis failure rate >5%/15min (minimum 20 runs), SQL unavailable >5min, and admission allowance remaining below ₹100 in development. Notification destinations and paid scheduled-query alerts have **not** been provisioned in this budget-limited demo.

Evaluate exact quantity/constraints, critical evidence contradictions and abstentions separately. Track citation validity, critical-fact coverage, false-negative contradictions, clean-case false blocks, authorization bypass, duplicate external writes, warm/cold latency and measured billing. A 12-case synthetic check is not a statistically meaningful production p95 or proof of buyer usability.

## Backup, retention and rollback

An actual local SQLite backup/restore test keeps the independent synthetic ERP newer than the restored ledger, then reconciles its existing receipt without another row; the audit chain remains valid (`evidence/local-restore-verification.json`). It uses a model test double. Azure SQL platform backups exist, but a point-in-time restore drill has not been executed. Before production, restore to an isolated database, verify plan/source hashes and audit chains, compare outbox receipts against the external ERP, and rehearse identity/permission restoration. Never restore a ledger and blindly replay its outbox; the external system may contain writes newer than the database backup.

Blob snapshots are content-addressed and hash-verified, **not locked WORM**. Current frontend host-storage permissions are broader than an archive-only writer because host and archive share a development storage account. Production should separate archive storage and apply reviewed retention/legal-hold policies.

To roll back application code, deploy a retained known-good archive and its compatible hosted version, then verify policy contracts before accepting new decisions. Do not route back to v3 merely because its clean demo passed: v3 has documented missed source contradictions. Prefer leaving analysis unavailable over restoring a known unsafe gate. Never delete old decisions to make a rollback appear successful.

## Cost stop / cleanup

The user authorized ₹1,000 **total** development/testing. The SQL admission ledger reserves ₹10 per attempted specialist call, retaining reservations for failed/uncertain work. It has ₹700 total allowance including a ₹200 conservative reserve for earlier activity; ₹300 is held outside that ledger for infrastructure. These are allowances, not measured Azure charges. Cost Management has returned HTTP 429; report actual spend as unverified until billing can be read.

To close model admission without deleting evidence, an operator sets `budget_accounts.limit_paise = reserved_paise` for account `development` inside a transaction. Stop both Function Apps to prevent further executions, and terminate this task's hosted sessions if needed after exporting decision evidence. Keep SQL free-exhaustion AutoPause and zero always-ready settings. Do not assume stopping Functions deletes storage charges or model deployment state.

Remove only the named `LastBuyDeveloperTemporary` SQL firewall rule after local SQL access is no longer required. Remove application-specific role assignments when retiring the demo. Review and delete only LastBuy-specific resources individually after preserving evidence; the Foundry account, subscription and resource group may contain the user's unrelated work. No automatic recurring monitoring or cleanup job has been created.
