# LastBuy: final recording plan

Updated 24 September after rubric, editorial and proof reviews. One enterprise decision, seven scenes, 2:55 total. The PDF, description and narration use the same submission/entry.json source.

**The decisive moment:** the recorded model summary says 4,800 current units, but its structured purchase field says 6,000. Show both in the new inspector, then show that current validation blocks purchasing authority.

## Prepare these views

1. [Completed enterprise case](http://127.0.0.1:8810/?case=LTB-CLOUD-RELEASE-7): Maya Chen · planner, Decision overview, top of page.
2. [Captured supply-failure replay](http://127.0.0.1:8810/?case=LTB-LIVE-CURRENT-BALANCE-20260920): Decision overview; locate Supply reconciliation → Inspect recorded response.
3. Existing supporting PDF: output/pdf/LastBuy-Architect-Solution-Design.pdf. Bookmark page 3 (architecture) and page 8 (recorded recovery). Use each briefly; the application stays on screen for most of the video.

[Plain narration](NARRATION.txt) · [Timed narration and actions](../submission/recording-guide.md) · [Recording checklist](RECORDING-CHECKLIST.md)

After a restart, run `bash /Users/Apple/Documents/lastbuy-planning/scripts/start_demo.sh` and keep its terminal open. The launcher preserves the stored case results and shared model allowance. If asked to sign in locally, choose Maya Chen · planner.

Local role switching shares a cookie across tabs. After switching roles, reload another app tab before interacting, then choose the intended role. Opening the inspector is read-only. Do not use Re-analyze, Apply synthetic reservation or Export approved draft during this walkthrough; the sequence inspects completed results and recorded integration evidence.

## Exact click sequence

| Time | Show | Click / point |
|---|---|---|
| 0:00-0:18 | Completed enterprise case: $1.44m proposal, 18,000 units, service supply-chain buyer | Open LTB-CLOUD-RELEASE-7 at Decision overview. Point to the original proposal; leave the example/recorded-results label visible. |
| 0:18-0:46 | Governing service evidence: processor coverage and 22,000 protected demand | Evidence → SERVICE-SYN-A07 → Inspect. Hold on processor coverage and the increase to 22,000. Close and return to Decision overview. |
| 0:46-1:07 | Quantity bridge: eligible stock, confirmed inbound, 10,000-unit buy and modeled difference | Point through the quantity bridge. Briefly inspect Evidence beside duplicate custody, then close. Hold on 10,000 units and $640,000. |
| 1:07-1:30 | Four specialist roles and recorded Foundry response: v7, scoped tool, structured facts | Scroll to Specialist analysis. Open Supply → Inspect recorded response. Point to foundry-hosted, v7 and read_case_evidence; close. Briefly show PDF page 3 architecture. |
| 1:30-2:10 | Captured supply error: summary 4,800 versus structured 6,000; blocked approval and next owner | Failure case → Supply recorded response → Read recorded summary. Show 4,800 in the summary, SAP-01:quantity=6000 with the opening-count quote, and Current case validation: needs review. Close; show supply-planner next action. Select Arjun Rao · engineering → Approvals; show unavailable approval and disabled export. |
| 2:10-2:31 | Version-bound human approvals and recorded cloud export recovery | Hold on four pending approval roles. Show PDF page 8 final two rows: separate cloud integration fixtures, historical gate 409/zero rows and CREATE/RECOVER one row each. |
| 2:31-2:55 | Return to the purchase decision; quality evidence and customer-pilot target | Return to clean case Decision overview. End on the quantity bridge and modeled difference. Keep test details in the supporting PDF; finish at 2:55. |

## Make the proof readable

Rehearse at normal speech speed. The script contains 332 whitespace-delimited words; speaking numbers aloud takes longer. Aim for 2:55, not exactly 3:00. Hold the source amendment and the summary/structured-field mismatch long enough to read. Keep the mouse still on each key number. Record in a maximized landscape browser; avoid rapid zooms, music and a long logo intro.

The failure inspector opens its first SAP quantity check automatically. Expand Read recorded summary; its 4,800 current count and the 6000 structured field should be visible together. Current case validation is a separate panel. Close the inspector, show Next: supply planner, then switch to Arjun Rao · engineering and Approvals. No approval action is offered and Export approved draft is disabled.

Record the architecture insert for about five seconds and the recovery proof for about ten seconds. Return to the clean overview for the close. If the take runs long, shorten the architecture narration; preserve the mismatch and refusal demonstration.

## Precise answers for questions

- **Why agents?** They interpret released engineering applicability, governing component coverage, physical-stock identity and supplier terms. Exact arithmetic and permission checks remain deterministic.
- **Why four?** Distinct source scopes and validation contracts make errors attributable. All four roles share one hosted application; they are not four separately secured deployments. A one-case single-call comparison is recorded, not universal superiority.
- **Is this a fresh run?** The clean case is an actual completed Foundry v7 run. The failure replay combines a captured novel supply response with reused reference stages. COMPLETE means execution finished; the current validation gate decides acceptance.
- **Why not recalculate automatically?** The governed source input must be corrected and verified before obtaining fresh approvals. In a counterfactual, 11,200 is the raw shortfall; the 1,000-unit supplier order multiple would require 12,000. That arithmetic is not a newly approved plan.
- **Was a purchase made?** No. The clean demo case has no completed approvals/export. CREATE, lost-response RECOVER and historical-stock rejection are separate recorded cloud test fixtures against the ERP simulator.
- **Is the category new?** Servigistics already supports final-buy planning; Z2Data already offers lifecycle workflows and approvals. Demonstrate the exact evidence-to-field-to-quantity-to-authority chain; do not claim competitors cannot do it.
- **Has it saved $640,000?** That is the modeled commitment difference in this example. The 50% reduction in active reconciliation time is a pilot target. Both remain visibly qualified.

## Supporting evidence, outside the timed story

The [public supplier screen](http://127.0.0.1:8810/?view=market) and PDF page 7 substantiate a real last-time-buy event. The onsemi part, INR prices and 7 October deadline are separate from the example ASIC, USD 80 price and 15 October deadline. Do not splice their numbers together. The September 20 price observation is dated; after 24 hours its calculator correctly refuses a current estimate. It stays in the appendix rather than the opening.

The saved [preflight.json](preflight.json) records an earlier rehearsal. Run `.venv/bin/python scripts/demo_preflight.py` from the project directory before recording to check the current local cases and PDF. The local UI avoids cloud cold-start delays while retaining the original saved results. If a case or inspector is missing, stop the take and restart/refresh. Do not overwrite records to stage a passing result.

## Submission boundary

The participant creates and reviews the final recording. The official limit is three minutes / 150 MB; the authenticated form requires PDF or Word support up to 30 MB. Review the originality/rights/eligibility requirements before submission. Nothing in this preparation uploads an entry. [Official rules](https://founderz.com/agentathon-terms/).
