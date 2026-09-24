"""Build the Architect supporting document from explicit, reviewed project facts."""

import json
import xml.etree.ElementTree as ET
from pathlib import Path

from reportlab.graphics.shapes import Drawing, Line, Polygon, Rect, String
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output/pdf/LastBuy-Architect-Solution-Design.pdf"
ENTRY = json.loads((ROOT / "submission/entry.json").read_text())
MARKET = json.loads((ROOT / "lastbuy/market_prices.json").read_text())
TEST_COUNT = (
    ET.parse(ROOT / "evidence/implementation-tests.xml")
    .getroot()
    .find("testsuite")
    .attrib["tests"]
)
GREEN = colors.HexColor("#173e35")
LIME = colors.HexColor("#dce8b4")
INK = colors.HexColor("#20362f")
GRAY = colors.HexColor("#546860")
PALE = colors.HexColor("#f0f5f1")
LINE = colors.HexColor("#d5dfd9")
styles = {
    "k": ParagraphStyle(
        "k",
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=13,
        textColor=GREEN,
        spaceAfter=9,
    ),
    "h": ParagraphStyle(
        "h",
        fontName="Helvetica-Bold",
        fontSize=25,
        leading=29,
        textColor=GREEN,
        spaceAfter=13,
    ),
    "sub": ParagraphStyle(
        "sub",
        fontName="Helvetica",
        fontSize=12,
        leading=17,
        textColor=GRAY,
        spaceAfter=15,
    ),
    "b": ParagraphStyle(
        "b", fontName="Helvetica", fontSize=10, leading=14, textColor=INK, spaceAfter=9
    ),
    "s": ParagraphStyle(
        "s",
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=GRAY,
        spaceAfter=6,
    ),
    "th": ParagraphStyle(
        "th", fontName="Helvetica-Bold", fontSize=9, leading=12, textColor=colors.white
    ),
    "td": ParagraphStyle(
        "td", fontName="Helvetica", fontSize=9, leading=12.3, textColor=INK
    ),
    "sec": ParagraphStyle(
        "sec",
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=GREEN,
        spaceBefore=8,
        spaceAfter=8,
    ),
}


def P(t, s="b"):
    return Paragraph(t, styles[s])


def table(rows, widths):
    t = Table(
        [[P(v, "th" if i == 0 else "td") for v in row] for i, row in enumerate(rows)],
        colWidths=widths,
        hAlign="LEFT",
        repeatRows=1,
    )
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), GREEN),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [PALE, colors.white]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 9),
                ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
                ("LINEBELOW", (0, -1), (-1, -1), 0.5, LINE),
            ]
        )
    )
    return t


def start(n, title, sub):
    if n > 1:
        story.append(PageBreak())
    story.extend(
        [P(f"LASTBUY / ARCHITECT DESIGN / {n:02d}", "k"), P(title, "h"), P(sub, "sub")]
    )


def sec(title, text):
    story.extend([P(title, "sec"), P(text)])


def footer(c, d):
    c.setStrokeColor(LINE)
    c.line(42, 44, A4[0] - 42, 44)
    c.setFont("Helvetica", 8)
    c.setFillColor(GRAY)
    c.drawString(
        42,
        30,
        "25 September 2026 (IST)  |  Foundry execution + dated market evidence",
    )
    c.drawRightString(A4[0] - 42, 30, f"LastBuy  /  {d.page}")
    c.setFillColor(GREEN)
    c.rect(0, A4[1] - 8, A4[0], 8, fill=1, stroke=0)


def architecture():
    d = Drawing(510, 264)

    def box(x, y, w, h, lines, dark=False):
        d.add(
            Rect(
                x,
                y,
                w,
                h,
                rx=6,
                ry=6,
                fillColor=GREEN if dark else PALE,
                strokeColor=LINE,
            )
        )
        for i, t in enumerate(lines):
            d.add(
                String(
                    x + w / 2,
                    y + h - 17 - i * 13,
                    t,
                    fontName="Helvetica-Bold" if i == 0 else "Helvetica",
                    fontSize=9,
                    textAnchor="middle",
                    fillColor=colors.white if dark else INK,
                )
            )

    def arrow(x1, y1, x2, y2):
        d.add(Line(x1, y1, x2, y2, strokeColor=GRAY, strokeWidth=1))
        if y2 < y1:
            d.add(
                Polygon(
                    [x2, y2, x2 - 3, y2 + 6, x2 + 3, y2 + 6],
                    fillColor=GRAY,
                    strokeColor=GRAY,
                )
            )
        else:
            d.add(
                Polygon(
                    [x2, y2, x2 - 6, y2 - 3, x2 - 6, y2 + 3],
                    fillColor=GRAY,
                    strokeColor=GRAY,
                )
            )

    box(0, 206, 154, 48, ["Planner workspace", "Entra + case authorization"], True)
    box(
        178,
        206,
        154,
        48,
        ["Durable Functions", "Persisted state / bounded retry"],
        True,
    )
    box(356, 206, 154, 48, ["SQL + Blob", "Plans / approvals / source hashes"])
    arrow(154, 230, 178, 230)
    arrow(332, 230, 356, 230)
    box(
        0,
        122,
        332,
        59,
        [
            "Foundry hosted application v7",
            "Engineering | Service | Supply | Commitment",
            "One scoped read_case_evidence tool per role",
        ],
    )
    arrow(255, 206, 255, 181)
    box(
        356,
        122,
        154,
        59,
        [
            "Deterministic solver",
            "CP-SAT + independent checks",
            "Model cannot set buy quantity",
        ],
    )
    arrow(332, 151, 356, 151)
    box(
        0,
        29,
        154,
        60,
        [
            "Evidence + plan review",
            "Blockers stop approval",
            "Four distinct human roles",
        ],
    )
    box(
        178,
        29,
        154,
        60,
        [
            "Separate export identity",
            "Current authority + outbox",
            "Reconcile external reference",
        ],
    )
    box(
        356,
        29,
        154,
        60,
        ["Synthetic ERP database", "One draft requisition", "Real SAP adapter: future"],
    )
    arrow(77, 122, 77, 89)
    arrow(154, 59, 178, 59)
    arrow(332, 59, 356, 59)
    d.add(Line(433, 122, 433, 101, strokeColor=GRAY))
    d.add(Line(433, 101, 77, 101, strokeColor=GRAY))
    d.add(
        String(
            0,
            4,
            "Application Insights: correlated stage/model/tool traces; source content capture disabled.",
            fontName="Helvetica",
            fontSize=9,
            fillColor=GRAY,
        )
    )
    return d


story = []
start(
    1,
    "Every unit justified before<br/>the final order.",
    "LastBuy verifies one discontinued image-processing ASIC purchase for an industrial thermal-camera manufacturer.",
)
story.append(P("OPEN THE EVIDENCE", "k"))
story.append(
    P(
        '<link href="https://lastbuy-dev-4126.azurewebsites.net/?view=market" color="#173e35"><b>Public evidence screen</b></link>'
        f'  |  <link href="{MARKET["notice_url"]}" color="#173e35"><b>Manufacturer notice</b></link>'
        f'  |  <link href="{MARKET["offers"]["USD"]["url"]}" color="#173e35"><b>USD listing</b></link>'
        f'  |  <link href="{MARKET["offers"]["INR"]["url"]}" color="#173e35"><b>INR listing</b></link>',
        "b",
    )
)
story.append(
    P(
        "Links open primary market evidence. The public screen is a deterministic catalogue reference; the private, four-agent Foundry decision workflow is demonstrated in the companion video. Architecture p3; evaluation p5; production controls p6; market evidence p7; executed proof p8.",
        "s",
    )
)
story.append(
    P(
        "<b>Decision:</b> how many components must the OEM buy before the supplier closes final orders, while preserving the approved repair obligations for eligible camera cohorts?"
    )
)
story.append(
    table(
        [
            ["Accountability", "Exact enterprise role"],
            [
                "Target economic buyer",
                "Director of Global Service Supply Chain; finance controller co-signs material commitments.",
            ],
            [
                "Daily user",
                "Service-parts planner / obsolescence manager reconciling the final-buy proposal.",
            ],
            [
                "Approval owners",
                "Sustaining engineer, service-contract owner, finance controller and procurement manager; four distinct people.",
            ],
        ],
        [110, 400],
    )
)
sec(
    "Financial stakes with a traceable example",
    'Reported stock can include duplicate custody records, incompatible board revisions and quarantined units. Service amendments can increase demand. A wrong input becomes unnecessary capital commitment or an uncovered obligation. <link href="https://www.sec.gov/Archives/edgar/data/1094285/000109428526000043/tdy-20260628.htm" color="#173e35">Inventory exposure</link> and <link href="https://www.flir.com/en-ca/support/warranty/instruments/2-10-thermal-camera-warranty-from-flir/" color="#173e35">component-specific warranty</link> are documented publicly; no customer has validated LastBuy.',
)
story.append(
    table(
        [
            ["Synthetic decision bridge", "Units / value"],
            ["Reported on-hand stock", "14,000"],
            ["Remove duplicate / incompatible / quarantine", "2,000 / 3,000 / 1,000"],
            ["Eligible stock + confirmed inbound", "8,000 + 4,000"],
            ["Protected demand / required new buy", "22,000 / 10,000"],
            [
                "Original proposal / verified plan",
                "18,000 x $80 = $1.44m / 10,000 x $80 = $800,000",
            ],
        ],
        [310, 200],
    )
)
story.append(Spacer(1, 10))
story.append(
    P(
        "<b>$640,000 modeled commitment difference.</b> Constructed test data, not achieved savings. Hosted Foundry agents completed the cloud case; changed coverage can increase the recommendation."
    )
)
start(
    2,
    "Specialists with a reason<br/>to exist.",
    "Use language models to reconcile source meaning. Keep quantity, authority and external writes under deterministic control.",
)
story.append(
    table(
        [
            [
                "Specialist",
                "Evidence and bounded responsibility",
                "Output checked by server",
            ],
            [
                "Engineering",
                "Released PLM records; component/board revision and cohort applicability.",
                "Release/effectivity checks, exact quotes and unresolved conflicts.",
            ],
            [
                "Service",
                "Signed coverage records and approved demand scenarios; distinguish detector warranty from ASIC coverage.",
                "Coverage and demand-source checks; governing evidence and blockers.",
            ],
            [
                "Supply",
                "ERP/depot lot records, reservations, holds and inbound confirmations.",
                "Quantity/confirmation checks; evidence for each disjoint exclusion.",
            ],
            [
                "Commitment",
                "Supplier quote, purchase limits and the deterministic calculation.",
                "Price/allocation checks and explanation of the verified commitment.",
            ],
        ],
        [84, 232, 194],
    )
)
sec(
    "Implemented tool contract",
    "Each role uses <b>read_case_evidence</b> with a server-selected source scope. The tool returns the immutable snapshot hash, permitted source records, required extractions and relevant structured facts. No arbitrary SQL, URL fetch, shell, approval or ERP-write tool is available.",
)
sec(
    "Structured handoffs",
    "Durable activities share a case/run ID and the same accepted snapshot. Each assessment returns role, summary, findings, exact supporting quotes and critical-field checks. The server validates scope, quote membership and agreement with accepted fields; unresolved review findings block approval. The final plan includes allocations, costs, blockers, source hash, policy version and plan hash.",
)
sec(
    "Why multiple agents can help",
    "The engineering, contract and stock records have different owners and authority rules. Scoped assessments make failures attributable and allow role-specific tests and bounded retries. One generic instruction set would combine these authority questions. The fourth role explains supplier commitment against the deterministic result; it does not calculate the purchase.",
)
story.append(
    P(
        "<b>First matched-input comparison:</b> on the same golden snapshot and model deployment, the four-stage record correctly accepted the case (12,569 response-reported tokens). A single-call comparator using the same four validation contracts falsely flagged resolved duplicate custody (8,363 tokens). This is one case with a historical comparator, not a broad superiority claim. Logical roles share one hosted process.",
        "s",
    )
)
start(
    3,
    "A decision workflow<br/>with durable authority.",
    "Deployed development architecture. Azure services are real; enterprise sources and requisitions are synthetic.",
)
story.append(architecture())
sec(
    "Sequence from evidence to draft requisition",
    "1. Import a typed, hash-checked synthetic snapshot and source revision.<br/>2. Validate source-owner references; run four bounded specialist activities.<br/>3. Validate assessments; solve and independently verify allocation constraints.<br/>4. Archive the snapshot and store the versioned decision for evidence review.<br/>5. Collect engineering, service, finance and procurement approval for the exact hash.<br/>6. Recheck stored source/policy/authority; enqueue one export reference.<br/>7. The isolated worker writes a synthetic draft and reconciles uncertain responses.",
)
story.append(
    table(
        [
            ["Boundary", "Implemented behavior / production extension"],
            [
                "Model hosting",
                "Foundry hosted v7; Microsoft Agent Framework; lastbuy-dev-mini model deployment. Deterministic stage order controls current quota and cost.",
            ],
            [
                "Data ownership",
                "SAP/depot: stock; Windchill: applicability; Contracts/Dataverse: coverage; Planning: scenarios; Supplier: quote. Current imports trust manifest labels.",
            ],
            [
                "Customer integration",
                "Approved SAP/PLM/Dataverse APIs or extracts, complete paging and live revision refetch are required for a customer deployment; not implemented as live connectors.",
            ],
        ],
        [113, 397],
    )
)
start(
    4,
    "Make the consequence<br/>visible to the planner.",
    "The central interaction is a purchase decision: inspect what changed, which evidence governs it, and who must act.",
)
sec(
    "Decision workspace",
    "The quantity bridge links each stock exclusion to its source. Scenario coverage shows the protected demand envelope. Blockers identify the source owner and next action. Version-bound approvals and a recoverable requisition receipt complete the planner's workflow.",
)
sec(
    "The decisive demonstration",
    "Open inside the enterprise purchase decision. Inspect the governing service amendment, quantity bridge and recorded Foundry tool response. The decisive reveal puts the correct 4,800-unit summary beside the incorrect 6,000-unit structured field. Show the current refusal, next source owner and four human approval roles. Keep public onsemi research in the supporting evidence.",
)
story.append(
    table(
        [
            ["2:55 presentation", "Proof to show"],
            *[
                [
                    f"{b['start'] // 60}:{b['start'] % 60:02d}-{b['end'] // 60}:{b['end'] % 60:02d}",
                    b["screen"],
                ]
                for b in ENTRY["beats"]
            ],
        ],
        [132, 378],
    )
)
story.append(Spacer(1, 9))
story.append(
    P(
        "Use clearly labeled completed Foundry results if a cold run exceeds the recording window. Do not present deterministic previews, test doubles or edited timing as new live agent execution. The participant records and edits the final video.",
        "s",
    )
)
story.append(P("The judging lens", "sec"))
story.append(
    P(
        "<b>Innovation:</b> the 6,000-unit historical field is blocked despite a correct 4,800-unit summary.<br/>"
        "<b>Usability:</b> the planner sees the quantity bridge, governing quote, owner and next action.<br/>"
        "<b>Impact:</b> the modeled commitment falls from $1.44m to $800,000; the pilot measures time, coverage and finance benefit.",
        "s",
    )
)
start(
    5,
    "Prove quality.<br/>Expose the failures.",
    "Evaluation and operating evidence are part of the product design, not a final presentation decoration.",
)
story.append(
    table(
        [
            ["Evidence", "What it establishes / limit"],
            [
                f"{TEST_COUNT} automated tests",
                "Solver, workflow, authority, replay, cancellation, expiry and export behaviors within covered fixtures. Includes captured provider failures and exact public-price arithmetic.",
            ],
            [
                "60/60 offline suite",
                "50 structured solver fixtures and 10 security regression references. Not a full independent language-understanding benchmark.",
            ],
            [
                "New live stock challenge",
                "The model summary said 4,800 current units, while its structured check selected 6,000 opening units. Captured-response regression drove a currentness gate. The corrected deployed worker rejected a legacy-approved fixture with HTTP 409 and zero ERP rows.",
            ],
            [
                "v7 regression: 9 attempts",
                "Six correct accepted outcomes, three abstentions. Four conflicts: one explicit block, three abstentions, zero silent passes. Four clean cases accepted. Reused post-tuning cases; not a new holdout.",
            ],
            [
                "Real recovery evidence",
                "Worker kill/resume; actual v2 checkpoint-to-approval completion; real SQL concurrency; cloud export/reconciliation; local backup/restore. Connection timeout evidence drove bounded connection retry.",
            ],
        ],
        [137, 373],
    )
)
sec(
    "Evaluation in the development lifecycle",
    "Freeze cases and labels before prompt changes. Run offline arithmetic/authority tests on every relevant change. Within an approved allowance, compare candidate and current hosted versions on an untouched conflict/clean/injection set; retain failed attempts. Gate release on zero observed unsafe exports, exact quantity checks, source resolvability and explicit conflict/abstention metrics. Report sample sizes and false blocks.",
)
sec(
    "Observability that answers operational questions",
    "Correlate case/run, snapshot and plan hashes across Durable, model and tool spans. Track stage duration, retries, token usage, validation failures, approval transitions and uncertain exports. Input/output content capture is disabled. A successful cloud case reported 12,569 stage tokens and 18.085 seconds of model/tool runtime; this excludes end-to-end overhead and is not p95.",
)
start(
    6,
    "A credible path<br/>from prototype to production.",
    "The contest entry demonstrates architectural judgment. A real customer rollout needs additional evidence and authority.",
)
story.append(
    table(
        [
            ["Control or outcome", "Current implementation and release gate"],
            [
                "Identity and approval",
                "Entra PKCE/JWT; current server-owned roles/amount limits; four distinct approvers. Real cloud user is planner-only; demo personas do not establish customer approval.",
            ],
            [
                "Safe boundaries",
                "LLM has read-only evidence tools. Separate exporter identity/database; external-reference uniqueness. Supplier text cannot grant engineering authority.",
            ],
            [
                "Reliable changes",
                "Source/policy changes invalidate approvals. Cancellation blocks late completion; v2 approval wait expiry is authoritative. V1 is retained for existing replay histories.",
            ],
            [
                "Production hardening",
                "Add trusted customer connectors and live source refetch, workload-token export transport, reviewed private networking, locked retention and tested cloud restore/alerts.",
            ],
            [
                "Pilot outcome",
                "At least 10 buyer-provided historical cases. Target at least 50% less active reconciliation time, no increased missed coverage and positive finance-validated net benefit. Targets are not measured results.",
            ],
        ],
        [133, 377],
    )
)
sec(
    "Differentiation to test",
    "Servigistics already provides last-time-buy planning; Z2Data already offers obsolescence cases, integration and approvals. LastBuy targets verification across component-specific service obligations, released engineering effectivity and uniquely owned eligible stock, binding the resulting commitment to fresh approval and a recoverable export. Public product descriptions cannot establish exclusive capability or competitive superiority.",
)
story.append(P("Primary sources — click each name", "sec"))
refs = [
    (
        "Microsoft Agent-a-Thon / Level 3",
        "https://www.microsoft.com/en-us/events/local-events/microsoft-agent-a-thon",
    ),
    (
        "Official rules / judging and entry requirements",
        "https://founderz.com/agentathon-terms/",
    ),
    (
        "Authenticated Architect final assignment",
        "https://learn.founderz.com/lesson/final-activity-design-and-deliver-a-multi-agent-solution/294477ca-84d6-4c42-b258-b56fa24a331b",
    ),
    ("Microsoft teaching repository", "https://github.com/microsoft/FrontierWeekHack"),
    (
        "Microsoft orchestration guidance",
        "https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns",
    ),
    (
        "Teledyne Q2 2026 filing / inventory context",
        "https://www.sec.gov/Archives/edgar/data/1094285/000109428526000043/tdy-20260628.htm",
    ),
    (
        "FLIR component-specific warranty",
        "https://www.flir.com/en-ca/support/warranty/instruments/2-10-thermal-camera-warranty-from-flir/",
    ),
    (
        "PTC Servigistics capabilities",
        "https://www.ptc.com/en/products/servigistics/capabilities",
    ),
    (
        "Z2Data lifecycle management",
        "https://www.z2data.com/products/lifecycle-management/",
    ),
]
for label, url in refs:
    story.append(P(f'<link href="{url}" color="#173e35">{label}</link>', "s"))
story.append(
    P(
        "Contest/rules review: 24 September 2026. Authenticated form recheck: 24 September. Market observations: 20 September. Technical outcomes on pages 5 and 8 are backed by retained run, test and cloud-export records; these records contain private case data and are demonstrated in the companion video.",
        "s",
    )
)

start(
    7,
    "Real commercial evidence.<br/>Precisely bounded use.",
    "A separate public catalogue reference: onsemi AP0202AT2L00XPGA0-DR, an image signal processor in 100-VFBGA packaging.",
)
story.append(
    P(
        "<b>Observed 20 September 2026, 17:31:43 UTC.</b> Direct browser inspection of DigiKey US and India listings; currencies are independently observed, not converted. The manufacturer-authored discontinuance notice was retrieved and read."
    )
)
rows = [["Quantity", "USD / unit", "INR / unit", "INR line total"]]
for usd, inr in zip(MARKET["offers"]["USD"]["tiers"], MARKET["offers"]["INR"]["tiers"]):
    rows.append(
        [
            str(inr["quantity"]),
            usd["unit_price"],
            inr["unit_price"],
            inr["extended_price"],
        ]
    )
story.append(table(rows, [65, 120, 140, 185]))
sec(
    "Manufacturer notice PD27281ZA",
    "Issued 7 January 2026. Last-time-buy: <b>7 October 2026</b>. Final shipment: <b>7 April 2027</b>. Orders become non-cancelable/non-returnable, subject to availability and commercial terms. The notice lists AP0202AT2L00XPGA0-TR as replacement; customer board, firmware and assembly qualification remains a separate engineering decision. No cutoff hour or time zone is invented.",
)
sec(
    "Exact calculation and a meaningful refusal",
    "At 250 units, INR 800.47968 per unit produces <b>INR 200119.92</b>, rounding the extended line once. Observed DR stock is 2,201 with backorders unavailable. A 10,000-unit request has a 7,799-unit shortfall: the calculator returns <b>QUOTE_REQUIRED</b> without a fabricated subtotal. Replacement stock is not pooled into this allocation.",
)
sec(
    "Price evidence is not purchasing authority",
    "Catalogue prices exclude taxes, duties, tariffs, freight and customer discounts. The application stops current estimates after its 24-hour observation window; the dated source table remains historical evidence. This public calculator is deterministic. It has not been analyzed as a new Foundry case and does not change the example ASIC's USD 80 price, approval hashes or USD 640,000 modeled difference.",
)
for label, url in [
    ("DigiKey US price source", MARKET["offers"]["USD"]["url"]),
    ("DigiKey India price source", MARKET["offers"]["INR"]["url"]),
    ("onsemi discontinuance notice via DigiKey", MARKET["notice_url"]),
    (
        "Open deployed public evidence screen",
        "https://lastbuy-dev-4126.azurewebsites.net/?view=market",
    ),
]:
    story.append(P(f'<link href="{url}" color="#173e35">{label}</link>', "s"))

start(
    8,
    "Evidence an enterprise<br/>buyer can audit.",
    "Executed checks from the development release, followed by the exact decision record a customer would review.",
)
story.append(
    table(
        [
            ["Input / interaction", "Observed result", "Evidence record"],
            [
                "Public INR catalogue; 250 units",
                "CATALOGUE_ESTIMATE; INR 200119.92. USD catalogue: USD 2094.40.",
                "Market release verification",
            ],
            [
                "Public catalogue; 10,000 units",
                "QUOTE_REQUIRED; 7,799 units beyond observed stock; no subtotal.",
                "Market release verification",
            ],
            [
                "Captured live stock response selected historical 6,000 rather than current 4,800",
                "Inspector shows summary 4,800 versus field 6,000; current validation NEEDS_REVIEW; engineering approval unavailable; export disabled.",
                "Novel live acceptance + corrected release verification",
            ],
            [
                "Legacy-approved fixture carrying the same historical fact",
                "Deployed exporter: HTTP 409; zero external requisition rows.",
                "Cloud historical-evidence gate",
            ],
            [
                "Valid CREATE and preseeded lost-response RECOVER; repeat request",
                "One external row per case; repeated receipt unchanged; audit chain valid.",
                "Cloud export CREATE / RECOVER",
            ],
        ],
        [171, 196, 143],
    )
)
sec(
    "Decision record, not an opaque answer",
    "The versioned output binds case ID, source-snapshot SHA-256, policy version and plan hash; each specialist finding carries a source ID, exact quote, field check and blocker status. The deterministic plan records eligible stock, confirmed inbound, protected demand, buy quantity, price basis, allocations and independently checked constraints. Each approval binds an Entra object ID, role and amount limit to the same plan hash. Export records an idempotency key, external reference and reconciliation state.",
)
sec(
    "Release evidence and measured limits",
    "Completed cloud case LTB-CLOUD-RELEASE-7 used hosted application v7; its four specialist results total 12,569 response-reported tokens. The corrected deployed worker denied a historically approved but stale-evidence export with HTTP 409 and zero external rows. Current evidence establishes a working development system with synthetic enterprise data; buyer-provided historical cases, real connectors and finance sign-off remain the gates to a production claim.",
)
story.append(
    P(
        "Public catalogue references are observations dated 20 September 2026. They must be refreshed before a later current-price claim or purchase. The USD 640,000 modeled difference is a constructed case result, not realized savings. No private case, approval or customer integration is exposed by the public market link.",
        "s",
    )
)

OUT.parent.mkdir(parents=True, exist_ok=True)
SimpleDocTemplate(
    str(OUT),
    pagesize=A4,
    rightMargin=42,
    leftMargin=42,
    topMargin=38,
    bottomMargin=57,
    title="LastBuy | Architect Solution Design",
    author="LastBuy project",
    subject="Microsoft Agent-a-Thon Architect supporting design document",
).build(story, onFirstPage=footer, onLaterPages=footer)
print(OUT)
