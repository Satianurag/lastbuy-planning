"""Build one consistent participant handover from the reviewed entry description."""

import json
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
entry = json.loads((ROOT / "submission/entry.json").read_text())
test_count = sum(
    int(suite.attrib["tests"])
    for suite in ET.parse(ROOT / "evidence/implementation-tests.xml")
    .getroot()
    .iter("testsuite")
)
out = ROOT / "output/submission"
out.mkdir(parents=True, exist_ok=True)
(out / "entry-description.txt").write_text(
    entry["title"] + "\n\n" + entry["description"] + "\n"
)
lines = [
    "# LastBuy: final recording guide",
    "",
    "This is the single current seven-scene script, ending at 2:55 with five seconds of buffer. It uses existing verified results, source inspection and recorded recovery evidence. No new paid model call or new approval/export is required. The participant creates the final recording, screenshots and editing.",
    "",
    "| Time | Show / exact action | Narration |",
    "|---|---|---|",
]
for beat in entry["beats"]:

    def time(n):
        return f"{n // 60}:{n % 60:02d}"

    lines.append(
        f"| {time(beat['start'])}-{time(beat['end'])} | {beat['screen']}. **Action:** {beat['action']} | {beat['narration']} |"
    )
lines.extend(
    [
        "",
        "## Prepare before recording",
        "",
        "- Optional market appendix (outside the timed video): https://lastbuy-dev-4126.azurewebsites.net/?view=market. Prices are the observation dated 20 September, not a promise of future availability. If recording after its 24-hour window, show the historical reference as dated or reverify first.",
        "- Completed Foundry case: http://127.0.0.1:8810/?case=LTB-CLOUD-RELEASE-7. The local copy preserves the completed cloud result and its original plan hash.",
        "- Captured-response failure: http://127.0.0.1:8810/?case=LTB-LIVE-CURRENT-BALANCE-20260920. Open Supply → Inspect recorded response → Read recorded summary; compare 4,800 with SAP-01:quantity=6000. Switch to engineering to show approval unavailable. Do not click Re-analyze.",
        "- Recovery evidence: evidence/cloud-export-verification-LIVE-20260920.json and evidence/cloud-historical-gate-verification.json. Present these as recorded integration-test results; synthetic approver fixtures and ERP are identified in the record.",
        "- Include actual application screenshots/example interactions in your video or supporting materials. Page 8 of the PDF provides traceable readouts, not screenshots.",
        "- Target a finished video of 175 seconds to leave room below the 180-second maximum. Rehearse and trim the supplied narration yourself.",
        "",
        "## Upload checks",
        "",
        "Video: mp4/mov/m4v, at most 180 seconds and 150,000,000 bytes. Support: PDF/Word, at most 30,000,000 bytes. Use ../pdf/LastBuy-Architect-Solution-Design.pdf. The ZIP is a local handover bundle, not a supported Founderz upload format.",
        "",
        "Final video, originality/rights/eligibility review and upload/submission remain participant actions. No entry is submitted by this generator.",
        "",
        entry["deadline_note"],
        "Conservative target in India: 25 September 2026, 05:29 IST.",
    ]
)
guide = "\n".join(lines) + "\n"
(out / "recording-guide.md").write_text(guide)
handover = (
    "# LastBuy contest handover\n\n## Submission description\n\n**"
    + entry["title"]
    + ".**\n\n"
    + entry["description"]
    + f"\n\n## Current supporting material\n\nThe eight-page design PDF covers buyer/problem, four-role architecture, human authority, the same seven-scene demo, {test_count} passing automated tests with live failures disclosed, production gates, real dated market evidence, and recorded interactions. All public prices belong to onsemi AP0202AT2L00XPGA0-DR; the USD 80 / USD 640,000 figures belong only to the separate constructed enterprise case.\n\nPublic catalogue calculations are deterministic and do not invoke Foundry. The four specialists in the enterprise workflow are the AI agent solution. A manufacturer-recommended alternative is not a customer engineering approval.\n\n## Judging alignment\n\n- Innovation: exact evidence-to-input checks, deterministic purchase constraints and authority tied to the source version. Servigistics and Z2Data already address this problem category; exclusivity is not claimed.\n- Usability: inspect quantity adjustments, source owners, provisional blocked results and clear next actions. Browser workflows were exercised; independent buyer study remains a pilot task.\n- Impact: reproducible modeled commitment and a measured customer-pilot plan, targeting at least 50% less active reconciliation time without more missed coverage obligations. Targets are not achieved outcomes.\n\n[Official rules](https://founderz.com/agentathon-terms/) give each criterion 30 points and use Innovation first in ties. The final participant video must satisfy their originality requirements.\n\n"
    + guide.replace(
        "# LastBuy: final recording guide", "## Three-minute recording script", 1
    )
    + "\n## Refinements supported by evidence\n\nThe live supply summary said 4,800 current units while its structured field selected 6,000 opening units; a currentness gate now blocks the captured response and the cloud exporter rejected a legacy-approved fixture with zero writes. A transient SQL connection timeout motivated bounded connection retry. A matched-input single-call baseline used fewer tokens but falsely blocked the clean golden case; this one historical comparison does not establish general superiority. Actual Functions checkpoint recovery completed through approval wait. These are separate evidence sets, not a single perfect accuracy statistic.\n"
)
(ROOT / "docs/08-contest-handover.md").write_text(handover)
(out / "README.md").write_text(
    "# LastBuy submission handover\n\nStart with [the final click guide](../demo/START-HERE.md), [plain narration](../demo/NARRATION.txt) and [Mac recording checklist](../demo/RECORDING-CHECKLIST.md). Follow recording-guide.md for the canonical seven-scene, 2:55 presentation.\n\nUse the eight-page PDF in ../pdf/LastBuy-Architect-Solution-Design.pdf as required supporting material. The authenticated form confirmed a title, video and required support upload; it did not confirm a separate description field. Keep entry-description.txt as a concise summary if one is requested.\n\nStatus: documentation and software evidence prepared; final participant video/screenshots, eligibility/originality review and Founderz upload/submission remain pending. Do not upload this ZIP in place of the required PDF/video.\n\nThe current release, artifact hashes and scoped evidence are recorded in package-manifest.json. Research and first-party source links are embedded in the PDF.\n"
)
print("Prepared description, recording guide and matching handover")

demo = ROOT / "output/demo"
demo.mkdir(parents=True, exist_ok=True)
(demo / "NARRATION.txt").write_text(
    "\n\n".join(beat["narration"] for beat in entry["beats"]) + "\n"
)
cue = [
    "# LastBuy: final recording plan",
    "",
    "Updated 24 September after rubric, editorial and proof reviews. One enterprise decision, seven scenes, 2:55 total. The PDF, description and narration use the same submission/entry.json source.",
    "",
    "**The decisive moment:** the recorded model summary says 4,800 current units, but its structured purchase field says 6,000. Show both in the new inspector, then show that current validation blocks purchasing authority.",
    "",
    "## Prepare these views",
    "",
    "1. [Completed enterprise case](http://127.0.0.1:8810/?case=LTB-CLOUD-RELEASE-7): Maya Chen · planner, Decision overview, top of page.",
    "2. [Captured supply-failure replay](http://127.0.0.1:8810/?case=LTB-LIVE-CURRENT-BALANCE-20260920): Decision overview; locate Supply reconciliation → Inspect recorded response.",
    "3. Existing supporting PDF: output/pdf/LastBuy-Architect-Solution-Design.pdf. Bookmark page 3 (architecture) and page 8 (recorded recovery). Use each briefly; the application stays on screen for most of the video.",
    "",
    "[Plain narration](NARRATION.txt) · [Timed narration and actions](../submission/recording-guide.md) · [Recording checklist](RECORDING-CHECKLIST.md)",
    "",
    "After a restart, run `bash /Users/Apple/Documents/lastbuy-planning/scripts/start_demo.sh` and keep its terminal open. The launcher preserves the stored case results and shared model allowance. If asked to sign in locally, choose Maya Chen · planner.",
    "",
    "Local role switching shares a cookie across tabs. After switching roles, reload another app tab before interacting, then choose the intended role. Opening the inspector is read-only. Do not use Re-analyze, Apply synthetic reservation or Export approved draft during this walkthrough; the sequence inspects completed results and recorded integration evidence.",
    "",
    "## Exact click sequence",
    "",
    "| Time | Show | Click / point |",
    "|---|---|---|",
]
for beat in entry["beats"]:
    cue.append(
        f"| {time(beat['start'])}-{time(beat['end'])} | {beat['screen']} | {beat['action']} |"
    )
cue.extend(
    [
        "",
        "## Make the proof readable",
        "",
        "Rehearse at normal speech speed. The script contains "
        + str(sum(len(b["narration"].split()) for b in entry["beats"]))
        + " whitespace-delimited words; speaking numbers aloud takes longer. Aim for 2:55, not exactly 3:00. Hold the source amendment and the summary/structured-field mismatch long enough to read. Keep the mouse still on each key number. Record in a maximized landscape browser; avoid rapid zooms, music and a long logo intro.",
        "",
        "The failure inspector opens its first SAP quantity check automatically. Expand Read recorded summary; its 4,800 current count and the 6000 structured field should be visible together. Current case validation is a separate panel. Close the inspector, show Next: supply planner, then switch to Arjun Rao · engineering and Approvals. No approval action is offered and Export approved draft is disabled.",
        "",
        "Record the architecture insert for about five seconds and the recovery proof for about ten seconds. Return to the clean overview for the close. If the take runs long, shorten the architecture narration; preserve the mismatch and refusal demonstration.",
        "",
        "## Precise answers for questions",
        "",
        "- **Why agents?** They interpret released engineering applicability, governing component coverage, physical-stock identity and supplier terms. Exact arithmetic and permission checks remain deterministic.",
        "- **Why four?** Distinct source scopes and validation contracts make errors attributable. All four roles share one hosted application; they are not four separately secured deployments. A one-case single-call comparison is recorded, not universal superiority.",
        "- **Is this a fresh run?** The clean case is an actual completed Foundry v7 run. The failure replay combines a captured novel supply response with reused reference stages. COMPLETE means execution finished; the current validation gate decides acceptance.",
        "- **Why not recalculate automatically?** The governed source input must be corrected and verified before obtaining fresh approvals. In a counterfactual, 11,200 is the raw shortfall; the 1,000-unit supplier order multiple would require 12,000. That arithmetic is not a newly approved plan.",
        "- **Was a purchase made?** No. The clean demo case has no completed approvals/export. CREATE, lost-response RECOVER and historical-stock rejection are separate recorded cloud test fixtures against the ERP simulator.",
        "- **Is the category new?** Servigistics already supports final-buy planning; Z2Data already offers lifecycle workflows and approvals. Demonstrate the exact evidence-to-field-to-quantity-to-authority chain; do not claim competitors cannot do it.",
        "- **Has it saved $640,000?** That is the modeled commitment difference in this example. The 50% reduction in active reconciliation time is a pilot target. Both remain visibly qualified.",
        "",
        "## Supporting evidence, outside the timed story",
        "",
        "The [public supplier screen](http://127.0.0.1:8810/?view=market) and PDF page 7 substantiate a real last-time-buy event. The onsemi part, INR prices and 7 October deadline are separate from the example ASIC, USD 80 price and 15 October deadline. Do not splice their numbers together. The September 20 price observation is dated; after 24 hours its calculator correctly refuses a current estimate. It stays in the appendix rather than the opening.",
        "",
        "The saved [preflight.json](preflight.json) records an earlier rehearsal. Run `.venv/bin/python scripts/demo_preflight.py` from the project directory before recording to check the current local cases and PDF. The local UI avoids cloud cold-start delays while retaining the original saved results. If a case or inspector is missing, stop the take and restart/refresh. Do not overwrite records to stage a passing result.",
        "",
        "## Submission boundary",
        "",
        "The participant creates and reviews the final recording. The official limit is three minutes / 150 MB; the authenticated form requires PDF or Word support up to 30 MB. Review the originality/rights/eligibility requirements before submission. Nothing in this preparation uploads an entry. [Official rules](https://founderz.com/agentathon-terms/).",
    ]
)
(demo / "START-HERE.md").write_text("\n".join(cue) + "\n")
