# Foundry capabilities mapped to LastBuy

Reviewed on 20 September 2026 against official documentation, the installed CLIs/SDKs and the actual Azure subscription. Documentation snapshots and hashes are in `evidence/docs-manifest.json`. “Documented” does not mean “enabled and tested in this tenant.”

## Deployment choice has three independent dimensions

1. **Developer surface:** Azure Developer CLI, Python SDK, C# SDK, VS Code, Foundry Skills, or Foundry Canvas. These are ways of operating the platform; VS Code is not a hosting requirement.
2. **Runtime:** prompt agent, own code in a Foundry hosted agent, or code hosted elsewhere calling Foundry models/tools.
3. **Package/protocol:** source ZIP or container image; Responses or Invocations (and other supported protocols).

**Selected direction:** choose **Python SDK** in “Choose a deployment method.” Use Python 3.13 + Microsoft Agent Framework + Foundry hosted code, managed from the terminal. Use `az` for Azure inventory/auth/resource management and the Python Projects SDK for explicit hosted version creation, routing, invocation and cleanup. Deploy source ZIP with pinned dependencies. VS Code remains optional. `azd` is installed for optional development commands, but it is not the critical deployment path: its remote-sample initialization hit an AzureDeveloperCLICredential subprocess timeout, while direct SDK deployment created an active hosted version. This is an evidence-based choice for this environment, not a claim that `azd` cannot work elsewhere.

For LastBuy's non-conversational case-processing API, **Invocations** fits the typed case/stage input and structured result. Agents inside it still call Foundry model APIs. Responses is convenient for standard agent clients and eval tooling, but its outer conversation abstraction is not necessary for procurement decisions. Compare the actual selected Invocations runtime and evaluation adapter in the setup report; do not assume a Responses tutorial is interchangeable with an Invocations handler.

| Surface | Suitability and decision |
| --- | --- |
| Azure Developer CLI | Optional convenience: terminal commands, versions, logs, local run and environments. Installed Foundry extensions are beta; its credential subprocess failed in our preflight. Keep it off the required deployment path. |
| Python SDK | Chosen deployment and application API. Explicit version/routing operations worked in our environment. The quickstart's Python script deletes its temporary version in `finally`; a persistent application needs deliberate lifecycle handling. |
| C# SDK | Capable, but changing language brings no benefit for our Python statistics/optimization and existing environment. |
| VS Code Toolkit | Useful debugger and Inspector, optional. It does not add unique hosted runtime capabilities. |
| Foundry Skills | Guidance/automation layer over APIs/CLI, not a distinct compute architecture. Review generated changes like other code. |
| Agent Canvas | Useful guided authoring, but unnecessary for a typed pipeline controlled in Git. |

Sources: [hosted quickstart](https://learn.microsoft.com/en-us/azure/foundry/agents/quickstarts/quickstart-hosted-agent), [deployment guide](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/deploy-hosted-agent), [developer tools](https://learn.microsoft.com/en-us/azure/foundry/how-to/develop/install-cli-sdk).

## Capability coverage

| Capability family | What it provides | LastBuy decision / limitation |
| --- | --- | --- |
| Model catalog and inference | Model discovery, comparison, versioned deployments, multiple publishers. | Start with the verified accessible mini model; benchmark a stronger model on ambiguity cases before paying for it. Pin model version/deployment in each decision. |
| Deployment capacity | Standard/global/data-zone, batch and provisioned choices. | Use consumption-based online inference. Batch is unsuitable for the live demo; PTU reservations are unjustified for this workload. Data-zone processing is not the same as processing only in West US 3. |
| Routing and fine-tuning | Router and supported model customization. | Fixed model per release for reproducibility. No fine-tuning before representative labeled errors justify it. No model router silently changing behavior behind financial approvals. |
| Prompt agents | Managed instructions/model/tools, portal or API authored. | Valid for simple roles, but custom orchestration and deterministic policy are easier to maintain in our hosted code. |
| Hosted agents | Own code, isolated session compute, managed endpoint and identity. | Host bounded read-only analysis stages; do not keep a sandbox alive while a person approves a purchase. |
| Protocols | Responses, Invocations, streaming and other channel interfaces. | Typed Invocations for case stages; browser UI talks to our authenticated backend. Voice and A2A provide no first-release value. |
| Multi-agent workflow | Microsoft Agent Framework graph/executors and tool calls. | Four bounded specialist roles; deterministic coordinator validates outputs. No unconstrained agent debates or recursive delegation. |
| Portal workflows | Existing declarative workflow surface. | **Do not use for new LastBuy work: Microsoft documents retirement on 1 December 2026.** |
| Routines and skills | Reusable procedures/behavior. | Keep prompts/policies as versioned code artifacts initially. Platform skills are preview; they are not authorization enforcement. |
| Function calling | Typed requests to application functions; client executes functions. | Primary tool mechanism for our allowlisted domain adapters and solver. A model's tool request is never proof the action ran. |
| MCP / OpenAPI / Toolbox | Governed reusable remote tool access, authentication and versioning. | Useful for an organization's shared adapters. Start with narrow functions; add Toolbox when external tool reuse warrants it. Pin tools; avoid dynamic tool discovery in financial commit flow. |
| File search / AI Search / Foundry IQ | Retrieval, indexes and knowledge bases. | Retrieve clauses/notices when necessary. Authoritative quantities come from structured records, not a vector search result. Exhaustive signed-amendment manifests are required; top-k retrieval cannot prove no amendment exists. |
| Work IQ / Fabric IQ / SharePoint | Context from licensed enterprise systems. | Optional integration paths, not assumed available. Dataverse/ERP exports are sufficient for the first pilot. No claim that Foundry includes a universal SAP connector. |
| Code Interpreter | Sandboxed generated code. | Exclude from purchase mathematics; use reviewed deterministic Python/OR-Tools instead. |
| Web/Bing/browser/computer use | Current web information and UI-based tool interaction. | Public research only. Supplier notices/terms must be snapshotted from an approved source. No browser automation to release orders. |
| Memory / state store | Cross-session memory; hosted durable state APIs. | Memory and state store are preview. Neither is the authoritative procurement ledger. Use Azure SQL and Blob. |
| Background/resilient execution | Async work, replay and recovery primitives. | Resilience remains preview and does not provide deterministic workflow replay or exactly-once external side effects. Durable Functions controls business stages and human waits. |
| Tracing | OpenTelemetry spans and model/tool visibility. | Correlate case, stage, snapshot hash, model and tool outcome. Redact content. Foundry tracing is GA for prompt/hosted agents; specific portal/private-network experiences can differ. |
| Evaluation | Dataset runs, agent/tool quality and custom metrics. | Deterministic business invariants are release blockers; model-as-judge is supplemental. Invocations needs a tested custom adapter where hosted eval tooling assumes Responses. |
| Optimization / red teaming | Prompt/agent optimization and adversarial testing. | Run offline on held-out data. Optimizer is preview; no self-modifying production prompts. Explicit injection/security cases remain mandatory. |
| Monitoring/control plane | Usage, latency, policy, fleet visibility and token controls. | Azure Monitor/Application Insights is the operational base; do not make preview dashboards necessary for incident detection. App request/token limits bound work. |
| Identity/RBAC | Dedicated agent identity, project identity, Entra/OBO connections. | Runtime agent gets read-only analysis access. Requisition exporter has a separate identity. Four logical agents in one process are not four Entra security boundaries. |
| Network isolation | Private endpoints, BYO/managed VNet options. | Existing public project is suitable for synthetic development only. Current networking docs require the injection choice at resource creation; plan a dedicated production account/network instead of promising to retrofit this one. |
| Guardrails | Model filtering and preview agent/tool/egress controls. | Defense in depth. SQL authorization, tool validation and private egress enforce actual boundaries; prompt shields do not grant financial authority. |
| Storage/encryption/policy | Azure resources, retention, CMK and Azure Policy options. | Explicit tenant data map, retention and least privilege; storage geography and inference geography checked separately. |
| Publishing | Managed endpoints plus Teams/Microsoft 365 channels. | Browser decision workspace first. Foundry API access does not require Teams publication; Teams notifications are optional future integration. |
| Speech/vision/language/content extraction | Broader Foundry/Azure AI services. | OCR only if real inputs are scans. No voice, image generation, healthcare models, or translation merely to increase feature count. |

Sources: [models](https://learn.microsoft.com/en-us/azure/foundry/concepts/foundry-models-overview), [agent types](https://learn.microsoft.com/en-us/azure/foundry/agents/overview), [hosted behavior](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/hosted-agents), [Toolbox](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/toolbox-overview), [Foundry IQ](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/what-is-foundry-iq), [readiness by feature](https://learn.microsoft.com/en-us/azure/foundry/concepts/general-availability), [capability reference](https://learn.microsoft.com/en-us/azure/foundry/concepts/capability-reference).

## Production constraints that change the design

- Hosted compute is per active session; multi-agent roles do not require separate hosted containers. The documented idle interval is 2–60 minutes, default 15; session data can expire after inactivity. Never depend on the session filesystem for an audit record retained for years.
- Default session quota and model token quota are different. A capacity allocation is not a spending limit. Implement bounded attempts, timeouts, tokens and active case concurrency.
- Foundry's state store has a 1 MB/item limit and is preview. Hosted resilience explicitly leaves checkpoints and safe side effects to the application. SQL transactions, version predicates and idempotent ERP export are our responsibility.
- Identity does not automatically confer access to SAP, SQL, Blob or a customer's records. User context and service credentials need explicit scopes. The application's authorization cannot be replaced by passing a tenant ID from the client.
- Runtime GA, portal GA and SDK/CLI release status differ. Our setup records package versions, including preview packages, and must not advertise an all-GA stack if any selected execution dependency remains prerelease.
- Current public pricing page returns placeholders for numeric compute rates. No fabricated monthly quote: use signed-in offer/region pricing and measured usage before a budgeted environment rollout.

Sources: [hosted sessions](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/hosted-agents), [state store](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/agent-state-store), [resilience](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/long-running-agent-resilience), [networking](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/networking-options), [permissions](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/hosted-agent-permissions), [pricing](https://azure.microsoft.com/en-us/pricing/details/foundry-agent-service/).
