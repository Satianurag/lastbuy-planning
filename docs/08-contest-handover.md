# LastBuy contest handover

## Submission description

**LastBuy: every unit justified before the final order.**

When a semiconductor supplier discontinues an image-processing ASIC, a thermal-camera manufacturer's service supply-chain director must place a final, non-cancellable purchase. The proposed quantity may rely on a detector warranty that does not cover that ASIC, a superseded service amendment, incompatible board revisions, duplicated depot custody records, quarantined stock or an unconfirmed delivery. Once the deadline passes, either unnecessary capital or service coverage can be permanently at risk.

LastBuy verifies one such decision. Four read-only Microsoft Foundry specialists review released engineering applicability, component-specific service coverage, physical supply and supplier commitment. They extract critical facts with exact source quotations. Server checks compare those facts with accepted inputs; an independent deterministic solver calculates the smallest purchase satisfying approved coverage, compatibility, timing and order constraints. Unresolved conflicts stop approval.

A decision workspace shows the quantity bridge, source records, blockers and versioned approvals. Engineering, service, finance and procurement approve with distinct identities. Any source/policy change invalidates the old authority. A separate export worker rechecks the approved plan and reconciles a unique external reference before creating a draft requisition. The model cannot approve, write an order or release a purchase order.

The synthetic demonstration reduces an 18,000-unit / $1.44m proposal to 10,000 units / $800,000 after preserving 22,000 units of protected service demand. The $640,000 is a **modeled commitment difference**, not achieved customer savings. Our pilot target is at least 50% less active reconciliation time with no increase in missed coverage constraints, validated against at least ten historical cases and the customer's incumbent workflow.

Built with Microsoft Foundry hosted agents, Microsoft Agent Framework, Azure Durable Functions, Azure SQL, Blob, Entra and Application Insights. Enterprise records and ERP are simulated. The cloud services, model invocations and managed-identity boundaries are real.

## Why the three criteria fit

| Criterion | Demonstrate | Evidence / limit |
|---|---|---|
| Innovation — 30 points | Evidence-to-input reconciliation, deterministic allocation, freshness-bound approval and uncertain-write recovery for one final ASIC commitment | Existing Servigistics and Z2Data products already address last-time buys. Claim a specific executable workflow, not invention of the problem or proven product uniqueness. |
| Usability — 30 points | A planner sees what changes the quantity and exactly which authority is missing; each approver has one scoped action | Responsive workspace and import/approval/export paths exercised. No independent buyer usability study completed. |
| Impact — 30 points | Show the $640,000 modeled difference and why preserving service obligations sometimes increases the buy | Synthetic arithmetic is reproducible. Actual savings, buyer adoption and net ROI need a customer pilot. |

The [official rules](https://founderz.com/agentathon-terms/) prioritize Innovation in tie-breaking. Their video limit is three minutes and 150 MB; the participant must do their own filming/editing/design. The authenticated form was reviewed on 20 September 2026: title, video (mp4/mov/m4v; 3 minutes/150 MB), and REQUIRED supporting document (pdf/docx/doc; 30 MB). The six-page design PDF is in `output/pdf/LastBuy-Architect-Solution-Design.pdf`. The seven lesson videos were not all watched.

## Three-minute recording script

Record the working application yourself. Use synthetic demo identities visibly labeled as such. Pre-run the real hosted analysis so the recording can show its actual results and execution evidence without pretending to accelerate a cold cloud start. Do not replace failed runs with edited success screens.

| Time | Screen and action | Suggested narration |
|---|---|---|
| 0:00–0:20 | Open final-buy case; point to discontinued ASIC, deadline and $1.44m proposal | “A thermal-camera OEM gets one final chance to buy this component. A wrong coverage assumption or duplicate lot becomes an irreversible commitment.” |
| 0:20–0:45 | Source viewer: detector warranty, signed ASIC service amendment, released BOM | “A ten-year detector warranty does not authorize ASIC coverage. The component-specific amendment and released engineering record do. LastBuy binds each accepted fact to its source.” |
| 0:45–1:10 | Supply bridge: 14,000 reported → 8,000 eligible; 4,000 inbound | “The same depot lot appears twice. Incompatible and quarantined stock cannot cover repairs. The solver enforces ownership, compatibility, dates and supplier constraints.” |
| 1:10–1:30 | Show 10,000-unit / $800,000 result; inspect specialist evidence and one actual trace | “Four scoped Foundry specialists reconcile the evidence. The quantity comes from verified constraints. This synthetic case shows $640,000 less modeled commitment, not a realized-savings claim.” |
| 1:30–1:55 | Demonstrate source reservation on a separate prepared case; old approvals become stale | “Another service job reserves 1,000 units. The previous approval no longer authorizes this snapshot. The revised purchase becomes 11,000 units.” |
| 1:55–2:20 | Approved original case; show four distinct synthetic roles and approval hash | “Engineering, service, finance and procurement keep authority. The model cannot approve. Unresolved source checks stop the workflow.” |
| 2:20–2:40 | Export approved draft with simulated lost response; reconcile the same reference | “The ERP can accept a request and lose its response. LastBuy looks up the original reference, so retrying does not create another requisition.” |
| 2:40–3:00 | Architecture/evaluation summary; end on measurable pilot outcome | “Foundry analysis, Durable orchestration, SQL decision state and an isolated export identity. The next test is less planner effort without missed obligations across real historical cases.” |

Keep the stock-change and final export on different prepared cases so the source-change segment does not misleadingly reuse invalidated approvals. Current real cloud identity is planner-only; demonstrate role switching only in the explicitly local synthetic demo.

## Refinements and lessons to disclose

- Initial citation identifiers and minor-unit narration were unreliable. Scoped schemas, server-derived citation IDs, exact quotes and deterministic currency validation improved the contract.
- A clean golden case was insufficient. The first frozen stress set exposed missed engineering, stock and supplier contradictions. Mandatory critical-field extraction and server comparison were added; unresolved review now blocks approval. Historical failures remain in the evaluation evidence.
- A strict numeric-quote check initially rejected a valid number followed by sentence punctuation. A regression test now covers that bug. Fail-closed behavior preserved the approval boundary but still hurt usability.
- Hosting and session lifecycle required explicit source packaging, pinned agent versions and bounded calls. Foundry 5xx retries repeated failed validation attempts; the final handler returns a non-retriable application failure and lets the metered Durable workflow own retries.
- Durable Functions resumed after a real worker process kill. A separate cloud export identity and ERP database reconciled both repeat submissions and a preseeded lost-response receipt.
- Four specialists provide scoped tools and responsibilities. A controlled single-agent comparison has not established superior accuracy or cost. Do not claim that it has.

## Ready assets and remaining participant actions

Code, frozen cases, execution evidence, research, architecture, runbook and this script are in the repository. Record screenshots from the actual local/cloud workspace; preserve the synthetic-data notice. Record/edit the final video yourself, check duration/file size, use the verified Founderz form, attach the required design PDF, confirm eligibility, and submit your own entry. No entry has been uploaded and no public repository has been published automatically.

The official rules contain a PDT/GMT cutoff inconsistency described in the original research. Use the earlier stated cutoff as a conservative target and verify any clarification on the official platform. Build completion does not extend the contest deadline.
