"""Build one consistent participant handover from the reviewed entry description."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
entry = json.loads((ROOT / "submission/entry.json").read_text())
out = ROOT / "output/submission"
out.mkdir(parents=True, exist_ok=True)
(out / "entry-description.txt").write_text(
    entry["title"] + "\n\n" + entry["description"] + "\n"
)
lines = [
    "# LastBuy: final recording guide",
    "",
    "This is the single current eight-scene script. It uses existing verified results, source inspection and recorded recovery evidence. No new paid model call or new approval/export is required. The participant creates the final recording, screenshots and editing.",
    "",
    "| Time | Show | Narration |",
    "|---|---|---|",
]
for beat in entry["beats"]:

    def time(n):
        return f"{n // 60}:{n % 60:02d}"

    lines.append(
        f"| {time(beat['start'])}-{time(beat['end'])} | {beat['screen']} | {beat['narration']} |"
    )
lines.extend(
    [
        "",
        "## Prepare before recording",
        "",
        "- Public market screen: https://lastbuy-dev-4126.azurewebsites.net/?view=market. Prices are the observation dated 20 September, not a promise of future availability. If recording after its 24-hour window, show the historical reference as dated or reverify first.",
        "- Completed Foundry case: http://127.0.0.1:8810/?case=LTB-CLOUD-RELEASE-7. The local copy preserves the completed cloud result and its original plan hash.",
        "- Captured-response failure: http://127.0.0.1:8810/?case=LTB-LIVE-CURRENT-BALANCE-20260920. Inspect stock evidence; switch to the engineering demo role to show approval unavailable. Do not click Re-analyze.",
        "- Recovery evidence: evidence/cloud-export-verification-LIVE-20260920.json and evidence/cloud-historical-gate-verification.json. Present these as recorded integration-test results; synthetic approver fixtures and ERP are identified in the record.",
        "- Include actual application screenshots/example interactions in your video or supporting materials. Page 8 of the PDF provides traceable readouts, not screenshots.",
        "- Target a finished video of 170-179 seconds to leave room below the 180-second maximum. Rehearse and trim the supplied narration yourself.",
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
    + "\n\n## Current supporting material\n\nThe eight-page design PDF covers buyer/problem, four-role architecture, human authority, the same eight-scene demo, 161 passing automated tests with live failures disclosed, production gates, real dated market evidence, and recorded interactions. All public prices belong to onsemi AP0202AT2L00XPGA0-DR; the USD 80 / USD 640,000 figures belong only to the separate constructed enterprise case.\n\nPublic catalogue calculations are deterministic and do not invoke Foundry. The four specialists in the enterprise workflow are the AI agent solution. A manufacturer-recommended alternative is not a customer engineering approval.\n\n## Judging alignment\n\n- Innovation: exact evidence-to-input checks, deterministic purchase constraints and authority tied to the source version. Servigistics and Z2Data already address this problem category; exclusivity is not claimed.\n- Usability: inspect quantity adjustments, source owners, provisional blocked results and clear next actions. Browser workflows were exercised; independent buyer study remains a pilot task.\n- Impact: reproducible modeled commitment and a measured customer-pilot plan, targeting at least 50% less active reconciliation time without more missed coverage obligations. Targets are not achieved outcomes.\n\n[Official rules](https://founderz.com/agentathon-terms/) give each criterion 30 points and use Innovation first in ties. The final participant video must satisfy their originality requirements.\n\n"
    + guide.replace(
        "# LastBuy: final recording guide", "## Three-minute recording script", 1
    )
    + "\n## Refinements supported by evidence\n\nLive stock extraction selected a historical quantity; a currentness gate now blocks the captured response and the cloud exporter rejected a legacy-approved fixture with zero writes. A transient SQL connection timeout motivated bounded connection retry. A matched-input single-call baseline used fewer tokens but falsely blocked the clean golden case; this one historical comparison does not establish general superiority. Actual Functions checkpoint recovery completed through approval wait. These are separate evidence sets, not a single perfect accuracy statistic.\n"
)
(ROOT / "docs/08-contest-handover.md").write_text(handover)
(out / "README.md").write_text(
    "# LastBuy submission handover\n\nUse the eight-page PDF in ../pdf/LastBuy-Architect-Solution-Design.pdf as required supporting material. Paste entry-description.txt where the form permits or include it in your entry narrative. Follow recording-guide.md for one consistent three-minute presentation.\n\nStatus: documentation and software evidence prepared; final participant video/screenshots, eligibility/originality review and Founderz upload/submission remain pending. Do not upload this ZIP in place of the required PDF/video.\n\nThe current release, artifact hashes and scoped evidence are recorded in package-manifest.json. Research and first-party source links are embedded in the PDF.\n"
)
print("Prepared description, recording guide and matching handover")
