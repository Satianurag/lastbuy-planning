import {
  initializeAuth,
  authorization,
  signInMicrosoft,
  signOutMicrosoft,
} from "/assets/auth.js";
const root = document.querySelector("#app");
const state = {
  session: null,
  cases: [],
  case: null,
  tab: "overview",
  busy: false,
};
const esc = (value) =>
  String(value ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
const n = (value) =>
  value == null ? "—" : Number(value).toLocaleString("en-US");
const money = (value) =>
  value == null
    ? "—"
    : new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: state.case?.plan?.currency || "USD",
        maximumFractionDigits: 0,
      }).format(value / 100);
const human = (value) =>
  String(value || "")
    .toLowerCase()
    .replaceAll("_", " ");
const labels = {
  engineering: "Engineering applicability",
  service: "Service obligations",
  supply: "Supply reconciliation",
  commitment: "Commitment planning",
};
const descriptions = {
  engineering: "Released BOM, revisions & serial effectivity",
  service: "Component coverage & signed amendments",
  supply: "Physical ownership, custody & availability",
  commitment: "Verified allocation & purchase constraints",
};
function badge(status) {
  const good = [
    "READY_FOR_APPROVAL",
    "APPROVED",
    "EXPORTED",
    "COMPLETE",
    "approve",
  ];
  const bad = ["REJECTED", "ANALYSIS_FAILED", "INFEASIBLE", "FAILED", "CANCELLED", "APPROVAL_WAIT_EXPIRED"];
  return `<span class="badge ${good.includes(status) ? "good" : bad.includes(status) ? "bad" : ["STALE", "NEEDS_REVIEW", "EXPORT_UNCERTAIN", "APPROVAL_PENDING", "ANALYZING"].includes(status) ? "warn" : ""}">${esc(human(status))}</span>`;
}
function toast(message) {
  const el = document.querySelector("#toast");
  el.textContent = message;
  el.classList.add("visible");
  setTimeout(() => el.classList.remove("visible"), 6000);
}
async function api(path, options = {}) {
  const authHeaders = await authorization();
  const response = await fetch("/api" + path, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "X-CSRF-Token": state.session?.csrf || "",
      ...authHeaders,
      ...options.headers,
    },
  });
  let data;
  try {
    data = await response.json();
  } catch {
    throw new Error("The server returned an unreadable response.");
  }
  if (!response.ok)
    throw new Error(
      typeof data.detail === "string"
        ? data.detail
        : "The request could not be validated. Check the source fields.",
    );
  return data;
}
async function refresh() {
  state.cases = await api("/cases");
  const requested = new URLSearchParams(window.location.search).get("case");
  const id = [state.case?.id, requested, state.cases.find(c => c.status === "READY_FOR_APPROVAL")?.id, state.cases[0]?.id].find(id => state.cases.some(c => c.id === id));
  if (id) state.case = await api("/cases/" + encodeURIComponent(id));
  render();
}
async function login(persona) {
  state.session = await api("/session", {
    method: "POST",
    body: JSON.stringify({ persona }),
  });
  await refresh();
}
function signIn() {
  if (state.session?.mode === "entra")
    return `<main class="auth"><div class="brand-mark">L<span>↗</span></div><h1>Final purchase.<br>Fully accounted for.</h1><p>Sign in with your provisioned Microsoft work identity to review your organization’s cases.</p><button class="btn primary" id="microsoft-signin">Sign in with Microsoft</button><p class="subtitle">Access and approval authority are assigned by your organization.</p></main>`;
  return `<main class="auth"><div class="brand-mark">L<span>↗</span></div><h1>Final purchase.<br>Fully accounted for.</h1><p>Review the evidence behind a semiconductor last-time buy. Verify coverage, reconcile stock, and approve the exact decision.</p><span class="login-badge">Local demonstration · synthetic enterprise records</span><div class="login-choices">${(state.session.personas || []).map((p) => `<button class="btn" data-login="${esc(p.key)}"><span>${esc(p.name)}</span><span>${esc(p.key)} →</span></button>`).join("")}</div><p class="subtitle">Demo personas exercise role boundaries. They are not production identity verification.</p></main>`;
}
function planBlocked(c) {
  return Boolean(c.plan?.blockers?.length) || ["NEEDS_REVIEW", "INFEASIBLE", "REJECTED", "CANCELLED", "ANALYSIS_FAILED", "APPROVAL_WAIT_EXPIRED"].includes(c.status);
}
function render() {
  if (!state.session?.actor) {
    root.innerHTML = signIn();
    return;
  }
  const c = state.case;
  if (!c) {
    root.innerHTML = '<main class="empty">No cases available.</main>';
    return;
  }
  const p = c.plan,
    actor = state.session.actor;
  const stale =
    p &&
    (p.input_snapshot_sha256 !== c.snapshot_sha256 || c.status === "STALE");
  const blocked = planBlocked(c);
  const initials = actor.name
    .split(" ")
    .map((x) => x[0])
    .join("");
  root.innerHTML = `<div class="layout"><aside class="sidebar"><div class="brand"><div class="brand-mark">L<span>↗</span></div><div>LastBuy<small>COMMIT WITH EVIDENCE</small></div></div><div class="org"><strong>Northstar Instruments</strong>Service supply chain · Demo</div><div class="nav-label">Workspace</div><button class="nav-item active" data-tab="overview"><span>▦</span> Final-buy cases <span class="count">${state.cases.length}</span></button><button class="nav-item" data-tab="evidence"><span>▤</span> Source evidence</button><button class="nav-item" data-tab="approvals"><span>✓</span> Approvals</button><button class="nav-item" data-tab="audit"><span>◷</span> Decision history</button><div class="org"><strong>Current case</strong><select class="case-picker" id="case-picker" aria-label="Select case">${state.cases.map((x) => `<option value="${esc(x.id)}" ${x.id === c.id ? "selected" : ""}>${esc(x.id)}</option>`).join("")}</select></div><div class="sidebar-bottom"><div class="environment"><span class="dot"></span>Microsoft Foundry<br>Live analysis · deterministic solver</div><p class="side-note">Purchase authority stays with people.<br>Every approval binds to a plan version.</p></div></aside><div class="content"><header class="topbar"><div class="breadcrumb">Procurement &nbsp; / &nbsp; <b>Final-buy decisions</b></div><div class="user"><span class="avatar">${esc(initials)}</span>${state.session.mode === "local-demo" ? `<select id="persona" aria-label="Switch demo role">${(state.session.personas || []).map((x) => `<option value="${esc(x.key)}" ${x.id === actor.id ? "selected" : ""}>${esc(x.name)} · ${esc(x.key)}</option>`).join("")}</select>` : `<span>${esc(actor.name)}</span><button class="btn ghost" id="microsoft-signout">Sign out</button>`}</div></header><div class="demo-strip"><span>◈</span><strong>${c.snapshot.synthetic ? "SYNTHETIC DATA" : "ENTERPRISE CASE"}</strong> &nbsp; ${c.snapshot.synthetic ? "Enterprise records and ERP exports are simulated. Foundry analysis is live." : "Approvals bind to verified source and plan versions."}</div><main id="main" class="main"><div class="mobile-cases"><label for="mobile-case-picker">Current case</label><select id="mobile-case-picker">${state.cases.map((x) => `<option value="${esc(x.id)}" ${x.id === c.id ? "selected" : ""}>${esc(x.id)}</option>`).join("")}</select></div><div class="eyebrow">LAST-TIME-BUY VERIFICATION</div><div class="headline"><div><h1>One final buy. Every unit justified.</h1><p class="subtitle">${esc(c.snapshot.title)} &nbsp;·&nbsp; Resolve the evidence before the order becomes irreversible.</p></div><div class="actions">${state.session.mode === "local-demo" && actor.roles.includes("planner") ? '<button class="btn" id="import-case">＋ Import case</button>' : ""}<button class="btn ghost" id="download-packet">↓ Evidence packet</button><button class="btn primary" id="analyze" ${state.busy || c.status === "ANALYZING" || !actor.roles.includes("planner") || ["EXPORTED", "EXPORT_PENDING", "EXPORT_UNCERTAIN"].includes(c.status) ? "disabled" : ""}>${c.status === "ANALYZING" ? "Analysis running…" : p ? "↻ Re-analyze case" : "↗ Analyze case"}</button>${c.status === "ANALYZING" && actor.roles.includes("planner") ? `<button class="btn" id="cancel-analysis" ${state.busy ? "disabled" : ""}>Cancel analysis</button>` : ""}</div></div><div class="case-ribbon"><div class="ribbon-cell"><span>Case</span>${esc(c.id)}</div><div class="ribbon-cell"><span>Component</span>${esc(c.snapshot.material)}</div><div class="ribbon-cell"><span>Supplier deadline</span>${new Date(c.snapshot.quote.order_deadline).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" })} · UTC</div><div class="ribbon-cell"><span>Source revision</span>v${c.snapshot.source_revision} · ${c.snapshot.sources.length} records</div>${badge(c.status)}</div>${stale ? '<div class="callout"><strong>Sources changed. Previous approvals no longer apply.</strong>The figures below belong to the previous plan. Re-analyze the current snapshot and collect new approvals before exporting.</div>' : ""}${c.status === "CANCELLED" ? '<div class="callout"><strong>Analysis cancelled.</strong>Late model results cannot change this case. Start a fresh analysis when ready.</div>' : ""}${c.status === "APPROVAL_WAIT_EXPIRED" ? '<div class="callout"><strong>The approval window expired.</strong>Create a fresh plan and collect new approvals before exporting.</div>' : ""}${c.status === "ANALYSIS_FAILED" ? '<div class="callout error"><strong>Analysis did not finish.</strong>No result was substituted. Inspect the failed specialist below and retry after the provider recovers.</div>' : ""}${p?.blockers?.length ? `<div class="callout error"><strong>This plan is blocked</strong>${p.blockers.map(esc).join("<br>")}</div>` : ""}<div class="metric-grid"><div class="metric ${blocked || stale ? "" : "featured"}"><div class="label">${stale ? "PREVIOUS PLAN · DIFFERENCE" : blocked ? "UNVERIFIED SCENARIO DIFFERENCE" : "MODELED COMMITMENT REDUCTION"}</div><div class="value">${money(p?.commitment_difference_minor)}</div><div class="foot">${blocked ? "Resolve source conflicts before relying on this comparison." : p?.commitment_difference_minor != null ? `${((p.commitment_difference_minor / p.baseline_commitment_minor) * 100).toFixed(1)}% versus original proposal · synthetic scenario` : "Awaiting verified analysis · no savings claimed"}</div></div><div class="metric"><div class="label">${stale ? "PREVIOUS PLAN · PURCHASE" : blocked ? "PROVISIONAL QUANTITY · BLOCKED" : "RECOMMENDED FINAL PURCHASE"}</div><div class="value">${n(p?.purchase_quantity)}<small>units</small></div><div class="foot">${p?.purchase_quantity != null ? `${money(p.commitment_minor)} purchase commitment` : "MOQ, compatibility and coverage constrained"}</div></div><div class="metric"><div class="label">ORIGINAL PURCHASE PROPOSAL</div><div class="value">${money(c.snapshot.baseline_quantity * c.snapshot.quote.unit_price_minor)}</div><div class="foot">${n(c.snapshot.baseline_quantity)} units · ${money(c.snapshot.quote.unit_price_minor)} per unit</div></div></div><nav class="tabs" aria-label="Case sections">${[
    ["overview", "Decision overview"],
    ["evidence", "Evidence"],
    ["approvals", "Approvals"],
    ["audit", "Audit trail"],
  ]
    .map(
      ([key, title]) =>
        `<button class="tab ${state.tab === key ? "active" : ""}" data-tab="${key}" aria-current="${state.tab === key ? "page" : "false"}">${title}${key === "evidence" ? `<em>${c.snapshot.sources.length}</em>` : key === "approvals" ? `<em>${currentApprovals().length}/4</em>` : ""}</button>`,
    )
    .join(
      "",
    )}</nav>${state.tab === "overview" ? overview() : state.tab === "evidence" ? evidence() : state.tab === "approvals" ? approvals() : audit()}<footer class="footnote"><span>All monetary comparisons are modeled. No purchase order is released by LastBuy.</span><span>${p ? "Plan " + esc(p.plan_sha256.slice(0, 12)) + " · " : ""}Audit chain ${c.audit_valid ? "verified ✓" : "invalid — investigate"}</span></footer></main></div></div>`;
}
function currentApprovals() {
  const c = state.case;
  if (
    ["STALE", "DRAFT", "ANALYZING", "ANALYSIS_FAILED", "REJECTED", "CANCELLED", "APPROVAL_WAIT_EXPIRED"].includes(
      c.status,
    )
  )
    return [];
  return c.approvals.filter(
    (a) =>
      a.plan_sha256 === c.plan?.plan_sha256 &&
      a.snapshot_sha256 === c.snapshot_sha256 &&
      a.policy_version === c.plan?.policy_version &&
      a.decision === "approve" &&
      new Date(a.expires_at) > new Date(),
  );
}
function stages() {
  const stages = state.case.stages.length
    ? state.case.stages
    : Object.keys(labels).map((role) => ({ role, status: "QUEUED" }));
  return `<section class="panel"><header class="panel-header"><div><h2>Specialist analysis</h2><p>Four bounded roles. One immutable snapshot.${planBlocked(state.case) ? " Recorded model assessments below are subject to the blocking decision gates." : ""}</p></div><span class="badge">Foundry</span></header><div class="panel-body">${stages.map((s, i) => `<div class="stage ${esc(s.status)}"><span class="stage-number">${s.status === "COMPLETE" ? "✓" : i + 1}</span><div><h3>${labels[s.role]}</h3><p>${esc(descriptions[s.role])}</p>${s.result ? `<p>${esc(s.result.assessment.summary)}</p>` : ""}${s.error ? `<p>${esc(s.error)} · run did not complete</p>` : ""}</div><span class="stage-status">${esc(human(s.status))}</span></div>`).join("")}</div><div class="panel-footer">${stages.some((s) => s.result?.source === "live-foundry") ? "Live model results with evidence-tool execution recorded." : "No model results yet. Start an analysis to review live findings."}</div></section>`;
}
function scenarioComparison(plan) {
  if (!plan?.scenario_requirements?.length) return "";
  return `<section class="panel"><header class="panel-header"><div><h2>Scenario coverage</h2><p>One purchase is checked against each protected forecast separately.</p></div></header><div class="table-scroll"><table class="evidence-table"><thead><tr><th>Scenario</th><th>Demand</th><th>Allocated</th></tr></thead><tbody>${plan.scenario_requirements.map(s => {
    const allocated = plan.allocations.filter(a => a.scenario === s.id).reduce((total, a) => total + a.quantity, 0);
    return `<tr><td><strong>${esc(s.id)}</strong><small>${s.protected ? "Protected coverage" : "Planning reference · not constrained"}</small></td><td>${n(s.quantity)} EACH</td><td>${s.protected ? `${n(allocated)} EACH` : "—"}</td></tr>`;
  }).join("")}</tbody></table></div><div class="panel-footer">Alternative forecasts reuse the same physical stock. Their allocations are never added together.</div></section>`;
}
function overview() {
  const c = state.case,
    p = c.plan;
  const blocked = planBlocked(c);
  const findings =
    p?.assessments?.flatMap((r) =>
      r.assessment.findings.map((f) => ({ ...f, role: r.assessment.role })),
    ) || [];
  const severityOrder = { blocker: 0, review: 1, info: 2 };
  findings.sort((a, b) => (severityOrder[a.severity] ?? 3) - (severityOrder[b.severity] ?? 3));
  return `<div class="workspace"><div class="stack"><section class="panel"><header class="panel-header"><div><h2>${blocked ? "Provisional calculation from disputed inputs" : "From reported stock to a defensible purchase"}</h2><p>${blocked ? "Resolve all blockers before these quantities can support a purchase decision." : "Each adjustment has an evidence trail."}</p></div><span class="badge">EACH</span></header>${p ? `<div class="panel-body"><div class="bridge-row"><span class="label"><i class="swatch"></i>Reported on-hand inventory</span><span class="number">${n(p.reported_on_hand)}</span></div>${p.exclusions.map((x) => `<div class="bridge-row muted"><span class="label">− ${esc(x.reason)} <button class="evidence-link" data-source="${esc(x.evidence[0])}">Evidence ↗</button></span><span class="number">−${n(x.quantity)}</span></div>`).join("")}<div class="bridge-row"><span class="label"><i class="swatch green"></i>Eligible on-hand inventory</span><span class="number">${n(p.eligible_on_hand)}</span></div><div class="bridge-row"><span class="label"><i class="swatch gold"></i>Confirmed compatible inbound</span><span class="number">+${n(p.confirmed_inbound)}</span></div><div class="bridge-row total"><span>${blocked ? "Provisional purchase quantity" : "Required final purchase"}</span><span class="number">${n(p.purchase_quantity)} units</span></div>${p.purchase_quantity != null ? `<div class="equation"><span><b>${n(p.eligible_on_hand)}</b><small>ELIGIBLE STOCK</small></span>+<span><b>${n(p.confirmed_inbound)}</b><small>CONFIRMED INBOUND</small></span>+<span><b>${n(p.purchase_quantity)}</b><small>${blocked ? "PROVISIONAL BUY" : "FINAL BUY"}</small></span>=<span><b>${n(p.eligible_on_hand + p.confirmed_inbound + p.purchase_quantity)}</b><small>PLANNED SUPPLY</small></span></div>` : ""}</div>` : '<div class="empty"><strong>The proposed purchase needs verification.</strong>Run the four specialists to reconcile coverage and stock.<br>The solver will calculate a constraint-checked purchase.</div>'}<div class="panel-footer">${p ? `Solver: ${esc(p.solver_status)} · ${p.allocations.length} allocations checked against structured inputs${blocked ? " · source validation blocked" : ""}` : "Signed coverage, released engineering and supplier constraints are required."}</div></section><section class="panel"><header class="panel-header"><div><h2>What changes the decision</h2><p>Governing evidence and specialist findings.</p></div></header><div class="panel-body">${
    findings.length
      ? `<ul class="findings">${findings
          .slice(0, 8)
          .map(
            (f) =>
              `<li><div class="finding-role">${labels[f.role]} · ${esc(f.severity)}</div>${esc(f.summary)} <button class="evidence-link" data-source="${esc(f.evidence[0])}">Read source ↗</button></li>`,
          )
          .join("")}</ul>`
      : `<p class="note">The case includes a detector-only warranty and a separate component-specific service amendment. The review must establish which document actually governs ASIC coverage.</p>`
  }<div class="proof"><span>⌁</span><div><strong>Coverage takes priority over a cheaper number.</strong>A signed amendment can increase the required buy. The system must preserve approved service demand, even when that raises commitment.</div></div></div></section>${scenarioComparison(p)}</div><div class="stack">${stages()}<section class="panel"><header class="panel-header"><div><h2>Commitment controls</h2><p>Before a draft requisition can leave this workspace.</p></div></header><div class="panel-body"><div class="bridge-row"><span>Named role approvals</span><b>${currentApprovals().length} / 4</b></div><div class="bridge-row"><span>Snapshot matches plan</span>${p ? badge(p.input_snapshot_sha256 === c.snapshot_sha256 ? "COMPLETE" : "STALE") : "—"}</div><div class="bridge-row"><span>Audit integrity</span>${badge(c.audit_valid ? "COMPLETE" : "FAILED")}</div><div class="actions"><button class="btn" data-tab="approvals">Review approvals →</button></div></div></section></div></div>`;
}
function evidence() {
  const c = state.case;
  return `<section class="panel"><header class="panel-header"><div><h2>Immutable source manifest</h2><p>Inspect the exact record and content hash used in this case. Source system names below describe synthetic fixtures.</p></div>${badge(c.snapshot.complete ? "COMPLETE" : "NEEDS_REVIEW")}</header><table class="evidence-table"><thead><tr><th>Record / governing content</th><th>System</th><th>Version / hash</th><th></th></tr></thead><tbody>${c.snapshot.sources.map((s) => `<tr><td><strong>${esc(s.record_id)}</strong><small>${esc(s.locator)}</small></td><td>${esc(s.system)}</td><td><strong>Revision ${esc(s.revision)}</strong><small class="mono">${esc(s.sha256.slice(0, 16))}</small></td><td><button class="btn ghost" data-source="${esc(s.id)}">Inspect ↗</button></td></tr>`).join("")}</tbody></table><div class="panel-footer mono">Snapshot SHA-256: ${esc(c.snapshot_sha256)}</div></section>`;
}
function approvals() {
  const c = state.case,
    p = c.plan,
    actor = state.session.actor;
  const accepted = currentApprovals();
  const role = actor.roles.find((x) =>
    ["engineering", "service", "finance", "procurement"].includes(x),
  );
  const canApprove =
    role &&
    p &&
    ["READY_FOR_APPROVAL", "APPROVAL_PENDING"].includes(c.status) &&
    !accepted.some((a) => a.role === role);
  const receipt = c.exports.find((e) => e.status === "COMPLETE")?.receipt;
  return `<div class="workspace"><section class="panel"><header class="panel-header"><div><h2>Human approval, bound to this decision</h2><p>Four distinct people attest to the exact plan and source snapshot.</p></div>${badge(c.status)}</header>${[
    "engineering",
    "service",
    "finance",
    "procurement",
  ]
    .map((r) => {
      const a = accepted.find((a) => a.role === r);
      return `<div class="approval"><span class="stage-number">${a ? "✓" : "○"}</span><div><h3>${r}</h3><p>${a ? `${esc(a.actor_name)} · ${esc(a.reason)}` : { engineering: "Released compatibility and repair effectivity", service: "Component-specific coverage and demand envelope", finance: "Commitment amount and approved risk assumptions", procurement: "Supplier terms, deadline and purchasing authority" }[r]}</p></div>${badge(a ? "approve" : "PENDING")}</div>`;
    })
    .join(
      "",
    )}${canApprove ? `<form id="approval-form" class="approval-form"><label for="reason">Your ${esc(role)} decision</label><textarea id="reason" name="reason" minlength="8" maxlength="1000" required placeholder="Record what you reviewed and the basis for your decision."></textarea><div class="actions"><button class="btn primary" name="decision" value="approve" ${state.busy ? "disabled" : ""}>Approve this plan</button><button class="btn danger" name="decision" value="reject" ${state.busy ? "disabled" : ""}>Reject & return for analysis</button></div></form>` : `<div class="panel-footer">${!p ? "Run analysis before requesting approvals." : role ? "Your decision is already recorded or this plan is not accepting approvals." : "Your current identity has no approval role. An assigned approver must review this plan."}</div>`}</section><div class="stack"><section class="panel"><header class="panel-header"><div><h2>Draft requisition</h2><p>Final purchase-order release remains in the ERP.</p></div></header><div class="panel-body"><div class="bridge-row"><span>Quantity</span><b>${n(p?.purchase_quantity)} EACH</b></div><div class="bridge-row"><span>Commitment</span><b>${money(p?.commitment_minor)}</b></div><p class="note">The export worker checks source freshness and current approver authority again. A repeated submission reconciles the same external reference.</p>${receipt ? `<div class="export-box"><strong>${esc(receipt.external_reference)}</strong><br>Draft requisition recorded in synthetic ERP.<br><span class="mono">${esc(receipt.external_key.slice(0, 24))}</span></div>` : ""}${c.status === "EXPORT_UNCERTAIN" ? '<div class="callout"><strong>Response lost after submission.</strong>Reconcile the external reference before retrying. The ERP may already have accepted this draft.</div>' : ""}${state.session.mode === "local-demo" ? '<label class="export-options"><input type="checkbox" id="lose-response"> Demo: lose ERP response after acceptance</label>' : ""}<div class="actions"><button class="btn primary" id="export" ${state.busy || !actor.roles.includes("procurement") || !["APPROVED", "EXPORT_PENDING", "EXPORT_UNCERTAIN", "EXPORTED"].includes(c.status) ? "disabled" : ""}>${["EXPORT_PENDING", "EXPORT_UNCERTAIN"].includes(c.status) ? "Reconcile external receipt" : receipt ? "Verify existing receipt" : "Export approved draft"} →</button></div></div></section>${state.session.mode === "local-demo" ? `<section class="panel"><header class="panel-header"><div><h2>Demonstrate a source change</h2><p>Reserve 1,000 units for another service case.</p></div></header><div class="panel-body"><p class="note">This creates a new source revision and invalidates previous approvals. Re-analysis must reflect the reduced available stock.</p><div class="actions"><button class="btn" id="reserve" ${state.busy || state.session.mode !== "local-demo" || !actor.roles.includes("planner") || ["EXPORT_PENDING", "EXPORT_UNCERTAIN", "EXPORTED"].includes(c.status) ? "disabled" : ""}>Apply synthetic reservation</button></div></div></section>` : ""}</div></div>`;
}
function audit() {
  return `<section class="panel"><header class="panel-header"><div><h2>Decision history</h2><p>Append-only application events linked by hashes. Operational traces are separate from this decision record.</p></div>${badge(state.case.audit_valid ? "COMPLETE" : "FAILED")}</header>${state.case.audit.map((a) => `<div class="audit-row"><span class="audit-index">${String(a.data.sequence).padStart(2, "0")}</span><div><h3>${esc(human(a.data.action))}</h3><p class="note">${esc(a.data.actor)}</p><p class="mono">${esc(a.hash.slice(0, 24))}</p></div><time>${esc(new Date(a.data.at).toLocaleString())}</time></div>`).join("")}</section>`;
}
function sourceDialog(id) {
  const source = state.case.snapshot.sources.find((s) => s.id === id);
  if (!source) return;
  const dialog = document.querySelector("#evidence-dialog");
  dialog.innerHTML = `<div class="dialog-heading"><div><div class="eyebrow">SYNTHETIC SOURCE RECORD</div><h2 id="evidence-title">${esc(source.record_id)}</h2></div><button class="close" id="close-dialog" aria-label="Close evidence">×</button></div><div class="source-meta"><div><span>SYSTEM</span>${esc(source.system)}</div><div><span>REVISION / LOCATOR</span>${esc(source.revision)} · ${esc(source.locator)}</div><div><span>EFFECTIVE DATE</span>${esc(source.effective_at)}</div><div><span>OBSERVED AT</span>${esc(source.observed_at)}</div></div><div class="source-content">${esc(source.text)}</div><p class="note mono">Content SHA-256<br>${esc(source.sha256)}</p>`;
  dialog.showModal();
}
function clearImportPreview() {
  state.pendingImport = null;
  const panel = document.querySelector("#import-preview");
  if (panel) panel.innerHTML = "";
}
function importDialog() {
  const dialog = document.querySelector("#evidence-dialog");
  state.pendingImport = null;
  dialog.innerHTML = `<div class="dialog-heading"><div><div class="eyebrow">REVIEW BEFORE IMPORT</div><h2 id="evidence-title">Bring in a source snapshot</h2></div><button class="close" id="close-dialog" aria-label="Close import">×</button></div><p class="subtitle">This development workspace accepts synthetic, normalized JSON records. Content hashes and source revisions are verified before saving.</p><div class="import-controls"><button class="btn" id="load-template">Load synthetic template</button><label class="btn" for="import-file">Choose JSON file</label><input id="import-file" type="file" accept=".json,application/json" /></div><label for="import-json">Snapshot JSON</label><textarea id="import-json" class="import-json" spellcheck="false" placeholder="Paste a normalized source snapshot"></textarea><button class="btn primary" id="preview-import">Validate & preview changes</button><div id="import-preview" aria-live="polite"></div>`;
  dialog.showModal();
}
async function action(callback) {
  if (state.busy) return;
  state.busy = true;
  try {
    await callback();
    await refresh();
  } catch (error) {
    toast(error.message);
  } finally {
    state.busy = false;
    render();
  }
}
document.addEventListener("click", async (event) => {
  const target = event.target.closest("button");
  if (!target) return;
  if (target.id === "microsoft-signin") {
    await signInMicrosoft();
    return;
  }
  if (target.id === "microsoft-signout") {
    await signOutMicrosoft();
    return;
  }
  if (target.id === "download-packet") {
    try {
      const packet = await api(
        `/cases/${encodeURIComponent(state.case.id)}/packet`,
      );
      const url = URL.createObjectURL(
        new Blob([JSON.stringify(packet, null, 2)], {
          type: "application/json",
        }),
      );
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `${state.case.id}-evidence.json`;
      anchor.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (error) {
      toast(error.message);
    }
    return;
  }
  if (target.dataset.login) {
    try {
      await login(target.dataset.login);
    } catch (e) {
      toast(e.message);
    }
    return;
  }
  if (target.dataset.tab) {
    state.tab = target.dataset.tab;
    render();
    return;
  }
  if (target.dataset.source) {
    sourceDialog(target.dataset.source);
    return;
  }
  if (target.id === "close-dialog") {
    document.querySelector("#evidence-dialog").close();
    return;
  }
  if (target.id === "import-case") {
    importDialog();
    return;
  }
  if (target.id === "load-template") {
    try {
      const value = await api("/import/template");
      document.querySelector("#import-json").value = JSON.stringify(
        value,
        null,
        2,
      );
      clearImportPreview();
    } catch (error) {
      toast(error.message);
    }
    return;
  }
  if (target.id === "preview-import") {
    try {
      const text = document.querySelector("#import-json").value;
      if (new TextEncoder().encode(text).length > 2_000_000)
        throw new Error("Snapshot exceeds 2 MB.");
      const snapshot = JSON.parse(text);
      const preview = await api("/import/preview", {
        method: "POST",
        body: JSON.stringify(snapshot),
      });
      state.pendingImport = { snapshot, preview };
      document.querySelector("#import-preview").innerHTML =
        `<div class="export-box"><strong>${esc(preview.operation)} ${esc(preview.case_id)}</strong><p>${preview.source_count} hashed sources · ${preview.lot_count} stock records · ${preview.scenario_count} demand scenarios</p><p>Structured changes: ${preview.structured_changes.map(esc).join(", ") || "none"}</p>${preview.source_changes.map((x) => `<p>${esc(x.source_id)}: ${esc(x.change)} · ${esc(x.previous_revision || "—")} → ${esc(x.new_revision || "—")}</p>`).join("")}<p>${preview.requires_reanalysis ? "This replaces the current snapshot and invalidates its approvals." : "A new case will be created. No model call or ERP write occurs."}</p><button class="btn primary" id="commit-import">Save reviewed snapshot</button></div>`;
    } catch (error) {
      toast(error.message);
    }
    return;
  }
  if (target.id === "commit-import" && state.pendingImport) {
    const { snapshot, preview } = state.pendingImport;
    await action(async () => {
      state.case = await api(
        preview.operation === "create"
          ? "/cases"
          : `/cases/${encodeURIComponent(snapshot.case_id)}/snapshot`,
        {
          method: preview.operation === "create" ? "POST" : "PUT",
          body: JSON.stringify(
            preview.operation === "create"
              ? snapshot
              : { snapshot, expected_revision: preview.expected_revision },
          ),
        },
      );
      document.querySelector("#evidence-dialog").close();
      state.pendingImport = null;
      state.tab = "evidence";
      toast("Reviewed snapshot saved. Analyze it before collecting approvals.");
    });
    return;
  }
  if (target.id === "analyze")
    await action(async () => {
      await api(`/cases/${state.case.id}/analyze`, { method: "POST" });
      toast(
        "Analysis started. Results will appear as each specialist finishes.",
      );
    });
  if (target.id === "cancel-analysis")
    await action(async () => {
      await api(`/cases/${state.case.id}/cancel`, {method: "POST"});
      toast("Analysis cancelled. In-flight calls may finish, but their results cannot authorize a purchase.");
    });
  if (target.id === "reserve")
    await action(async () => {
      await api(`/cases/${state.case.id}/demo-reservation`, { method: "POST" });
      toast(
        "Source revision changed. Existing approvals cannot authorize this new snapshot.",
      );
    });
  if (target.id === "export") {
    const lost = document.querySelector("#lose-response")?.checked;
    await action(async () => {
      const result = await api(`/cases/${state.case.id}/export`, {
        method: "POST",
        body: JSON.stringify({
          plan_sha256: state.case.plan.plan_sha256,
          simulate_lost_response: !!lost,
        }),
      });
      toast(
        result.receipt
          ? `Verified ${result.receipt.external_reference}`
          : result.message || "Response lost. Use “Reconcile external receipt” to recover safely.",
      );
    });
  }
});
document.addEventListener("input", (event) => {
  if (event.target.id === "import-json") clearImportPreview();
});
document.addEventListener("change", async (event) => {
  if (event.target.id === "import-file") {
    const file = event.target.files[0];
    if (!file) return;
    if (file.size > 2_000_000) {
      toast("Snapshot exceeds 2 MB.");
      return;
    }
    document.querySelector("#import-json").value = await file.text();
    clearImportPreview();
  }
  if (event.target.id === "persona") {
    try {
      await login(event.target.value);
    } catch (e) {
      toast(e.message);
    }
  }
  if (["case-picker", "mobile-case-picker"].includes(event.target.id)) {
    state.case = await api("/cases/" + encodeURIComponent(event.target.value));
    render();
  }
});
document.addEventListener("submit", async (event) => {
  if (event.target.id !== "approval-form") return;
  event.preventDefault();
  const reason = new FormData(event.target).get("reason");
  const role = state.session.actor.roles.find((x) =>
    ["engineering", "service", "finance", "procurement"].includes(x),
  );
  const decision = event.submitter.value;
  await action(async () => {
    await api(`/cases/${state.case.id}/approvals`, {
      method: "POST",
      body: JSON.stringify({
        plan_sha256: state.case.plan.plan_sha256,
        role,
        reason,
        decision,
      }),
    });
    toast(
      decision === "approve"
        ? "Approval recorded against this exact plan."
        : "Plan rejected. A new analysis is required.",
    );
  });
});
setInterval(async () => {
  if (state.case?.status === "ANALYZING" && !state.busy) {
    try {
      await refresh();
    } catch (error) {
      toast(error.message);
    }
  }
}, 2500);
try {
  await initializeAuth();
  state.session = await api("/session");
  if (state.session.actor) await refresh();
  else render();
} catch (error) {
  root.innerHTML = `<main class="error-page"><h1>Workspace unavailable</h1><p>${esc(error.message)}</p><p>Refresh after the API is available.</p></main>`;
}
