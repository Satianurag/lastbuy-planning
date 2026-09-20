> Historical setup checkpoint. The application has since been implemented and deployed; see [current implementation evidence](06-implementation-status.md).

# Verified development setup

Verified on 20 September 2026. **Preparation is ready for implementation. LastBuy itself has not been implemented.** The deployed agent is a diagnostic that calls one harmless Python tool and verifies its exact output. It handles no customer records or purchasing logic.

## Selected path and actual proof

Choose **Python SDK** in the Microsoft hosted-agent quickstart. Use Python 3.13, Microsoft Agent Framework, a source ZIP with remote dependency build, and the Invocations protocol. Azure CLI handles sign-in and resource management. VS Code and Docker are optional for this route.

| Check | Observed result | Evidence |
| --- | --- | --- |
| Microsoft account authentication | Normal browser sign-in/MFA succeeded; Azure CLI can access the subscription and project. | `evidence/azure-account.json`, `azure-project.json` |
| Model availability/quota | `gpt-5.4-mini`, version `2026-03-17`, deployed successfully as `lastbuy-dev-mini`. | `evidence/model-deployment-verified.json` |
| Local real-model tool call | Handler recorded exactly one `setup_probe` call; model returned the exact nonce; `ok: true`. | `evidence/local-probe-result.json` |
| Hosted source build and routing | `lastbuy-setup-check`, version `1`, became active and received 100% endpoint traffic. | `evidence/hosted-probe.json` |
| Actual cloud execution | HTTP 200; `ok: true`; one real Python tool call; exact nonce returned. | `evidence/cloud-probe-result.json` |
| Telemetry connection | Projects SDK resolves the Application Insights connection; credentials were not printed. | `evidence/telemetry-sdk-check.json` |
| Telemetry ingestion | Azure Monitor returned successful `invoke_agent`, model calls and `execute_tool setup_probe` spans with the same operation ID. | `evidence/telemetry-request-proof.json`, `telemetry-correlated-spans.json` |
| Local storage emulator | Blob, Queue and Table write/read round trips passed; probe records deleted. | `evidence/azurite-probe.json` |
| Python dependencies | 138 installed packages satisfy their dependency constraints; Ruff checks pass for setup scripts and diagnostic. | Final verification commands below |
| Linux dependency availability | Selected hosted diagnostic resolves for Python 3.13 / Linux x86_64 with binary distributions and hashes. | `evidence/hosted-linux-requirements.lock.txt`, `linux-resolution.log` |

One successful diagnostic is evidence of access, deployment and execution, not a workload benchmark or proof of production reliability. The observed server request took approximately 4.1 seconds; that is one diagnostic span, not LastBuy latency or a cold-start guarantee. The saved deployment ZIP hash identifies the submitted archive; subsequent local formatting means it must not be treated as a byte-for-byte checksum of today's working files. The actual product release must retain its archive, source revision and resolved build dependencies.

The final preparation audit is saved in `evidence/final-readiness-check.json`: 28 source snapshot hashes verified, local document links valid, cloud tool result and correlated spans verified, and Python/Ruff/Core Tools checks passed.

## Azure resources

Existing development resource group: `rg-anuragsati6476-5065`. Existing Foundry account: `anuragsati6476-4126-resource`. Project: `anuragsati6476-4126`. Account region: **West US 3**. Subscription identifier is recorded in the private local evidence rather than repeated throughout the plan.

| Resource prepared | Configuration and purpose |
| --- | --- |
| Model deployment `lastbuy-dev-mini` | `DataZoneStandard`, capacity 10; API reports 10 requests/minute and 10,000 tokens/minute. Consumption inference, not reserved PTU. |
| Hosted diagnostic `lastbuy-setup-check` v1 | Python 3.13, 0.5 CPU, 1 GiB memory, Invocations 2.0.0, configured 120-second session idle timeout. Retained for repeatable diagnostics; not a running LastBuy application. |
| Log Analytics `lastbuy-dev-logs` | West US 3, PerGB2018, 30-day retention, 0.1 GB daily ingestion quota. |
| Application Insights `lastbuy-dev-insights` | Workspace-based, connected to the above workspace. |
| Project connection `lastbuy-dev-telemetry` | Application Insights connection, verified through the Projects SDK. Connection string handled internally and not stored in project files. |

The model's Data Zone processing boundary is not the same as execution only in West US 3. Existing public networking and local-key settings were left unchanged; use synthetic inputs in this environment. Security defaults were not disabled and no user/agent roles were broadened during setup.

Model tokens, active hosted CPU/memory and telemetry can incur charges. Model quota and the log ingestion quota are **not hard spending caps**. No billing budget/alert has been configured and no precise monthly bill is claimed. Product implementation must add bounded case concurrency, token/retry limits and measured per-case cost; production rollout additionally needs offer-specific pricing and cost alerts.

## Local toolchain

Workspace: `/Users/Apple/Documents/lastbuy-planning`. It is a local Git repository without a remote. Python packages are isolated in `.venv`; Azurite is local to `tooling/node_modules`.

| Tool | Installed version / role |
| --- | --- |
| Python | 3.13.15 in the project environment |
| uv | 0.12.6, environment and dependency management |
| Azure CLI | 2.90.0, authenticated infrastructure/API access |
| Azure Developer CLI | 1.34.1, optional; delegated Azure CLI authentication configured |
| Azure Functions Core Tools | 4.14.0, installed, linked and executable |
| Bicep | 0.47.16, executable infrastructure compiler |
| Azurite | 3.37.0, pinned in npm lockfile |
| Projects SDK | `azure-ai-projects==2.6.1` |
| Agent Framework Foundry | `agent-framework-foundry==1.13.1` |
| Invocations host | `azure-ai-agentserver-invocations==1.1.0`, core `2.1.0` |
| Deterministic math | OR-Tools 9.15.6755 and SciPy 1.18.1; native import/toy solver checked |
| Local workflow SDK | `azure-functions==2.3.0`, `azure-functions-durable==1.7.0` |
| Validation/evaluation | Pydantic 2.13.5, pytest 9.1.1, Ruff 0.16.8, Azure AI Evaluation 1.18.5 |

Direct setup dependencies are in `requirements.in`; the entire tested environment is in `requirements.lock.txt`. This wider planning environment includes exploratory packages not needed by the selected hosted diagnostic. The diagnostic has its own five direct requirements. Some transitive packages and optional CLI extensions remain prerelease; an unqualified all-GA-stack claim would be incorrect.

## Reproduce the verified checks

From the workspace, with the existing Azure CLI session:

```sh
uv pip check --python .venv/bin/python
.venv/bin/ruff check scripts spikes/invocations-preflight
.venv/bin/python scripts/hosted_probe.py status
.venv/bin/python scripts/hosted_probe.py invoke
```

`invoke` makes one chargeable model request through the existing cloud diagnostic. It checks the actual tool result and writes fresh evidence. Do not run `create` again: the script deliberately refuses an existing record/name to avoid accidental duplicate deployment.

For a local diagnostic:

```sh
set -a
source .env.example
set +a
.venv/bin/python spikes/invocations-preflight/main.py
```

In another terminal:

```sh
curl --fail-with-body http://127.0.0.1:8088/invocations \
  -H 'Content-Type: application/json' \
  -d '{"nonce":"setup-local-repeat"}'
```

Start Azurite when implementing/testing Durable Functions:

```sh
tooling/node_modules/.bin/azurite \
  --location evidence/azurite-data \
  --blobHost 127.0.0.1 --queueHost 127.0.0.1 --tableHost 127.0.0.1
```

Temporary local diagnostic/emulator processes are stopped after preparation; these commands restart them. Azure CLI authentication remains in its normal credential cache. No passwords, bearer tokens or model keys are required in `.env.example`.

To deliberately remove only the diagnostic version later, use `.venv/bin/python scripts/hosted_probe.py cleanup`. This leaves the shared project, model and telemetry resources intact. Its parent agent may remain without a deployable version; this is not a whole-environment teardown command.

## Problems found and resolved

- Device-code authentication was rejected by tenant security defaults (`AADSTS530035`). Normal browser login/MFA succeeded. Repeating device login or weakening the tenant was unnecessary.
- `azd` remote-sample initialization failed in its credential subprocess. Direct SDK deployment succeeded, so the chosen path does not depend on that failing command.
- The regional connection API rejected the newest advertised API version. The explicitly supported `2026-05-01` ARM version created the telemetry connection successfully.
- The hosted Invocations endpoint requires `?api-version=v1`; the initial missing-version request returned 400. The corrected request passed.
- Homebrew required explicit trust of Microsoft's Functions formula alias before linking. Core Tools now returns version 4.14.0.

## Deliberately remaining implementation and pilot work

No product UI, domain agents, solver formulation, case database, approval policy, durable business workflow or ERP exporter has been implemented. No Azure SQL, production storage, private network, Function App, Entra application registration, production roles or CI/CD pipeline has been provisioned. Core Tools installation and emulator tests do not prove Durable Functions replay behavior. Evaluation packages are installed; no LastBuy evaluation scores exist yet, and an Invocations evaluation adapter remains to be built.

These are explicit build gates in `04-build-evaluation-and-demo.md`, not hidden setup successes. Actual SAP, Windchill, Dataverse and contract-repository connections require customer access and source contracts. Commercial validity requires historical buyer cases and comparison to the incumbent workflow. The public Founderz curriculum path and rules were reviewed; gated lessons and the authenticated submission form were not accessed.

The next implementation step is Gate 1: freeze the source schemas, evidence precedence, approval policy and independently specified synthetic truth set. That work should precede the production agents and UI.
