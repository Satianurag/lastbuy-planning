# LastBuy: exactly what to show

Rehearsed against the actual application on 22 September 2026. Use the same eight scenes as the submitted supporting PDF and [338-word narration](../submission/recording-guide.md). This is the click guide for that script, not a different presentation.

Your story: a final semiconductor purchase becomes non-cancelable. LastBuy checks which obligations and stock records can authorize it, explains a smaller defensible purchase, and prevents a plausible model mistake from becoming purchasing authority.

## Prepare once

The local demo is running at http://127.0.0.1:8810. To start it after a restart, run this in Terminal and keep the terminal open:

```sh
bash /Users/Apple/Documents/lastbuy-planning/scripts/start_demo.sh
```

Before recording, maximize the browser so text is readable. Prefer a landscape recording around 1920×1080; keep the pointer still while speaking. Close unrelated windows and pre-open these three app tabs plus the PDF. Record your own screen and narration, aiming to finish at 2:50–2:59.

1. [Supplier reference](http://127.0.0.1:8810/?view=market): dated public commercial evidence. Default India/INR, quantity 250.
2. [Completed purchase case](http://127.0.0.1:8810/?case=LTB-CLOUD-RELEASE-7): choose **Maya Chen · planner** if asked. Start at the top of Decision overview.
3. [Captured stock failure](http://127.0.0.1:8810/?case=LTB-LIVE-CURRENT-BALANCE-20260920): start at Decision overview. You will switch to **Arjun Rao · engineering** for the approval refusal.
4. Open `output/pdf/LastBuy-Architect-Solution-Design.pdf`: page 3 for architecture, page 8 for recorded export proof, page 5 for evaluation.

The local role cookie is shared across tabs. After switching roles, reload another app tab before using its actions, then choose the intended role. Do not click **Re-analyze case**, **Apply synthetic reservation** or **Export approved draft** in this three-minute walkthrough; the script inspects completed results and existing recovery evidence. Those actions would change the demonstration state or request another run.

## The eight scenes

| Time | Exactly what to do | What the audience should understand |
|---|---|---|
| 0:00–0:20 | Supplier tab: show the MPN, **7 Oct 2026** deadline, observation date and the **250 / ₹800.47968 / ₹2,00,119.92** table row. Keep the calculator's re-verification warning visible if it appears. | A real procurement deadline motivates the problem. Say **“On 20 September, the distributor listed…”**. This table is dated; its price is not today's accepted quote. |
| 0:20–0:40 | Completed case, top of Decision overview: point to **$1,440,000 original proposal**, **10,000 units**, and **$640,000 modeled difference**. | The buyer is a thermal-camera OEM's service supply-chain director. This separate example uses an assumed $80 ASIC price and a 15 October example deadline. Neither belongs to the onsemi reference. The displayed four-stage Foundry run is already completed. |
| 0:40–1:05 | Click **Evidence** → **Inspect** beside **WARRANTY-SYN-10**; close. Then **SERVICE-SYN-A07**; hold on the sentence increasing demand from 20,000 to **22,000** and naming ASIC coverage; close. If time permits, inspect **ECO-SYN-482** for released A2 compatibility. | Source meaning matters: detector warranty is not processor coverage. A signed component amendment governs the decision. Engineering, service, supply and commitment have distinct source responsibilities. |
| 1:05–1:30 | Return to **Decision overview**. Show **14,000 − 3,000 − 1,000 − 2,000 = 8,000** eligible stock. Click **Evidence ↗** beside duplicate custody; show it is the same physical LOT-02; close. Show **8,000 + 4,000 + 10,000 = 22,000**, then the four completed Specialist analysis roles. | The evidence explains the inputs. The deterministic solver calculates the constrained buy. $640,000 is a modeled commitment difference, not booked customer savings. |
| 1:30–2:05 | Switch to the failure tab. Show **This plan is blocked** and **PROVISIONAL QUANTITY · BLOCKED**. Open **Evidence → STOCK-SYN-0919 → Inspect**. Point to 6,000 opening, 1,200 scrapped, **4,800 current**. Close; choose **Arjun Rao · engineering** at top right; open **Approvals**. Show no approval action and the disabled **Export approved draft** button. | A real provider response selected the historical number in its structured check. The current gate refuses that captured response. Even a named approver cannot authorize the disputed plan. |
| 2:05–2:25 | PDF **page 3**, architecture diagram. Follow planner → Durable Functions → four Foundry roles → deterministic solver → human review → separate exporter. Point to **four distinct human roles**. | Persistence, controlled tools and separate authority are part of the workflow. Local role switching is a test facility; actual cloud identity uses Entra and the real account is planner-only. |
| 2:25–2:45 | PDF **page 8**, final two interaction rows. Show **HTTP 409 / zero external rows**, then **CREATE and RECOVER / one row per case / repeated receipt unchanged**. | These are recorded cloud integration results against the ERP simulator, not a new export during the video. The exporter rejects unsafe evidence and reconciles repeated requests. |
| 2:45–3:00 | PDF **page 5** for **161 automated tests**, then state the pilot target verbally (page 6 contains it). Finish by 2:59. | Testing exposed a failure and drove a fix. Next measure at least 50% less active reconciliation time on buyer-provided cases, without worse coverage. This is a pilot target, not an achieved result. |

Use the supplied narration as rehearsal notes and put it into your own words. Rehearse the source-dialog clicks twice; cut optional ECO inspection first if you run long. Keep the stock-failure and refusal scene intact: it demonstrates the most consequential behavior.

## Two lines to remember

Opening: “When a component reaches its final order date, a wrong stock or coverage assumption becomes an irreversible purchase. LastBuy makes every unit traceable before people commit.”

Closing: “LastBuy connects source meaning, exact quantities and human authority. The next pilot measures planner time and service coverage against historical cases.”

## Answers if a judge asks

- **Why AI?** The language work is distinguishing component coverage, engineering effectivity and historical versus current statements. Arithmetic, quantity conservation, approval and writes are deterministic.
- **Why four agents?** Separate source ownership and validation contracts make failures attributable. A one-case comparison is recorded; it does not prove general superiority over one agent.
- **Did the model really fail?** Yes. Its summary mentioned 4,800, but its structured `SAP-01:quantity` selected 6,000 with the opening-count quote. The gate checks the structured fact that could authorize a purchase; fluent prose alone is insufficient.
- **Is this live?** These are genuine completed Foundry results being inspected in the local application. ERP data and enterprise scenarios are examples. The recorded cloud recovery test is separate from the current interactive walkthrough.
- **Why not just buy 11,200 in the blocked case?** Correct the governed source input, rerun verification and obtain fresh approvals. The application does not silently rewrite purchasing inputs on a model's suggestion.
- **What distinguishes this from incumbent planning tools?** The focused demonstration is evidence-to-quantity verification tied to versioned human authority and recoverable export. Existing products already do obsolescence and final-buy planning; exclusive capability is not claimed.

## Recording and fallback

The cloud preview initially returned a startup message during this rehearsal, then its market API returned successfully. Use the prepared local UI for the walkthrough and describe the completed cloud execution accurately. Local data persists; opening existing cases makes no model call.

The September 20 catalogue observation is now older than 24 hours. Both local and cloud APIs correctly return **QUOTE_REQUIRED** with no current subtotal; the historical tier table remains visible. Do not suppress this warning or change its date to make it look fresh. The first scene intentionally shows the dated source row.

If a source dialog opens off-screen, close it and use the **Evidence** tab's named record. If a case is missing or no longer has the expected state, run `.venv/bin/python scripts/demo_preflight.py` from the project folder; do not overwrite its records to manufacture a passing scene. If the server is down, use the launcher above. The PDF provides the existing recorded proof if a cloud page cold-starts.

The [official rules](https://founderz.com/agentathon-terms/) require a video up to three minutes/150 MB and participant-owned filming/editing. The signed-in form also requires the PDF/Word support under 30 MB. Recheck the final video's duration, size and audio; the supplied script and this guide are preparation, not a submitted recording.

## Verified rehearsal evidence

[Current local preflight](preflight.json) checks the unchanged completed plan, four v7 stage records, blocked failure case, dated pricing behavior, the reviewed PDF hash, and recorded recovery results. Browser rehearsal verified the actual source dialogs and engineering refusal. No new model calls, approvals or exports were made.
