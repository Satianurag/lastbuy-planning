"""Build the Architect supporting document from explicit, reviewed project facts."""

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
        42, 30, "20 September 2026  |  Synthetic business data; real Foundry execution"
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
                "Economic buyer",
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
    "Reported stock can include duplicate custody records, incompatible board revisions and quarantined units. Service amendments can also increase demand. A wrong input becomes unnecessary capital commitment or an uncovered service obligation.",
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
        "<b>$640,000 modeled commitment difference.</b> The figures are constructed test data, not achieved savings. Real Foundry hosted agents completed this synthetic cloud case. The recommendation can increase when coverage or reservations change."
    )
)
story.append(
    P(
        "Business basis: manufacturer discontinuation notices, component-specific warranty terms and material inventory exposures support the problem category. They do not prove that a named customer has validated LastBuy. Sources and limitations: page 6.",
        "s",
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
        "<b>Architectural hypothesis, not a benchmark result:</b> four agents have not been proven more accurate or cheaper than one agent using the same tools. The release comparison must hold inputs, model and solver constant; consolidate roles if the extra calls do not improve conflict handling enough to justify cost. Logical roles share one hosted process and are not isolated security principals.",
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
story.append(
    table(
        [
            ["Workspace surface", "User question answered"],
            [
                "Quantity bridge",
                "Why does reported stock differ from usable supply? Open the exact source behind an exclusion.",
            ],
            [
                "Scenario coverage",
                "Which approved demand envelope is protected? Show allocation per scenario without summing alternatives.",
            ],
            [
                "Blockers and evidence",
                "What is unresolved, who owns it, and which source revision must be corrected?",
            ],
            [
                "Approval and audit",
                "Which person approved which plan? Are source and authority still current?",
            ],
            [
                "Requisition receipt",
                "Was the draft accepted? Can a retry recover the existing reference without another write?",
            ],
        ],
        [132, 378],
    )
)
sec(
    "The decisive demonstration",
    "Show the verified 10,000-unit plan. Then introduce a 1,000-unit stock reservation on a separate prepared case. The old approval must become stale and export must stop. The deterministic revised requirement is 11,000 units, subject to fresh analysis and approval. Finish by reconciling a lost-response synthetic export to its original receipt.",
)
story.append(
    table(
        [
            ["Three-minute presentation", "Proof to show"],
            [
                "0:00-0:25",
                "One buyer, the final-order deadline and the $1.44m proposal.",
            ],
            [
                "0:25-1:15",
                "Coverage clause and stock bridge; the 22,000-unit obligation remains protected.",
            ],
            [
                "1:15-2:05",
                "The $800,000 plan; changed evidence invalidates authority and blocks export.",
            ],
            [
                "2:05-2:35",
                "Four visibly synthetic approval roles and one reconciled draft reference.",
            ],
            [
                "2:35-3:00",
                "Actual trace, one failure-driven refinement and the measured pilot target.",
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
                "134 automated tests",
                "Solver, workflow, authority, replay, cancellation, expiry and export behaviors within covered fixtures. Not 134 live model runs.",
            ],
            [
                "60/60 offline suite",
                "50 structured solver fixtures and 10 security regression references. Not a full independent language-understanding benchmark.",
            ],
            [
                "v3 text stress: 12 attempts",
                "Four of seven conflicts silently passed. The initial system was not safe to trust on contradictory records.",
            ],
            [
                "v7 regression: 9 attempts",
                "Six correct accepted outcomes, three abstentions. Four conflicts: one explicit block, three abstentions, zero silent passes. Four clean cases accepted. Reused post-tuning cases; not a new holdout.",
            ],
            [
                "Real recovery evidence",
                "Worker process kill/resume; real SQL concurrency; isolated cloud synthetic export/reconciliation; actual local backup/restore. Azure SQL PITR remains untested.",
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
sec(
    "What remains to be measured",
    "Run a controlled single-agent comparison and an independent buyer usability study. Measure warm/cold end-to-end latency, failure cost and billing per completed case. Production alert destinations, service thresholds and an Azure SQL restore drill require customer-owned operating decisions.",
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
story.append(P("Selected sources and reproducible evidence", "sec"))
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
        "Source review: 20 September 2026. Repository evidence: full-cloud-release7.json; evaluation-summary.json; implementation-tests.xml; cloud-export-verification.json; final-release-check.json. Full source qualifications and competitor links are in docs/01-business-case.md.",
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
