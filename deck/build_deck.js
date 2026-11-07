// Builds deck/AI_Process_Redesign_Case_Study.pptx
// Run from repo root: NODE_PATH=$(npm root -g) node deck/build_deck.js
const pptxgen = require("pptxgenjs");
const path = require("path");
const SKILL = process.env.PPTX_SKILL_DIR;
const { applyTheme } = require(path.join(SKILL, "scripts/apply_theme.js"));

const THEME = {
  name: "Service Triage",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "1B2A30", lt1: "FFFFFF", dk2: "0B3C49", lt2: "EEF3F4",
    accent1: "117A8B", accent2: "E9A23B", accent3: "C8475A", accent4: "4C9A62",
    accent5: "7FA7B0", accent6: "5A6B70", hlink: "117A8B", folHlink: "5A6B70",
  },
};
const HEX = THEME.colors;

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9"; // 10 x 5.625
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "AI Process Redesign: Resident Service Requests";
pres.author = "Bushra Faruq Mujawar";
const C = pres.SchemeColor;

pres.defineSlideMaster({
  title: "Dark title",
  background: { color: C.text2 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 1.5, w: 8.8, h: 1.6, fontSize: 36, bold: true, color: C.background1, valign: "bottom", align: "left", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.6, y: 3.25, w: 8.8, h: 1.2, fontSize: 16, color: C.background2, valign: "top", align: "left", margin: 0 }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "Title only",
  background: { color: C.background1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.5, y: 0.3, w: 9.0, h: 0.75, fontSize: 24, bold: true, color: C.text2, valign: "top", align: "left", margin: 0 }, text: "" } },
    { text: { text: "AI process redesign case study | synthetic data", options: { x: 0.5, y: 5.2, w: 6, h: 0.3, fontSize: 9, color: C.accent6 } } },
  ],
  slideNumber: { x: 9.0, y: 5.2, w: 0.5, h: 0.3, fontSize: 9, color: C.accent6 },
});

function titleSlide(title, sub, section) {
  const s = pres.addSlide({ masterName: "Dark title", sectionTitle: section });
  s.addText(title, { placeholder: "title" });
  s.addText(sub, { placeholder: "body" });
  return s;
}
function content(title, section) {
  const s = pres.addSlide({ masterName: "Title only", sectionTitle: section });
  s.addText(title, { placeholder: "title" });
  return s;
}
function card(s, x, y, w, h, fill, name) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.08, fill: { color: fill }, line: { color: fill }, objectName: name });
}
function tb(s, text, opts) {
  s.addText(text, { isTextBox: true, margin: 0, valign: "top", ...opts });
}

// ---------------- 1. Title
pres.addSection({ title: "Summary" });
const s1 = titleSlide("Getting urgent requests to the right people, fast",
  "AI process redesign case study: resident service requests in a 450-bed residential building\nBushra Faruq Mujawar", "Summary");
s1.addNotes("Case study built on synthetic data. The organisation is generic; no employer data is used.");

// ---------------- 2. Executive summary
const s2 = content("Executive summary", "Summary");
const ex = [
  ["Problem", "Every request is read by a person before anyone knows it is urgent. Urgent emails wait a median 78 minutes; 18% of requests go to the wrong team.", C.accent3],
  ["Redesign", "An AI agent reads each request on arrival and proposes category, priority and owner. A coordinator decides. Safety issues alert the duty manager at once.", C.accent1],
  ["Value", "Coordinator effort falls from 156 to 64 hours a month. Net EUR 26.8k a year on an EUR 11k build; payback about 5 months.", C.accent4],
];
ex.forEach(([h, b, col], i) => {
  const x = 0.5 + i * 3.05;
  card(s2, x, 1.2, 2.85, 2.75, C.background2, `card-${h}`);
  s2.addShape(pres.shapes.OVAL, { x: x + 0.2, y: 1.38, w: 0.42, h: 0.42, fill: { color: col }, line: { color: col }, objectName: `dot-${h}` });
  tb(s2, String(i + 1), { x: x + 0.2, y: 1.38, w: 0.42, h: 0.42, fontSize: 14, bold: true, color: C.background1, align: "center", valign: "middle" });
  tb(s2, h, { x: x + 0.75, y: 1.43, w: 1.9, h: 0.35, fontSize: 18, bold: true, color: C.text2, fontFace: THEME.headFontFace });
  tb(s2, b, { x: x + 0.2, y: 2.0, w: 2.45, h: 1.85, fontSize: 13, color: C.text1 });
});
card(s2, 0.5, 4.15, 9.0, 0.8, C.text2, "recommendation");
tb(s2, [
  { text: "Recommendation: ", options: { bold: true, color: C.accent2 } },
  { text: "approve a two-week shadow trial. The keyword prototype fails the safety gate (P1 recall 69% vs 95% needed), so go-live depends on the LLM version passing the same test.", options: { color: C.background1 } },
], { x: 0.75, y: 4.2, w: 8.5, h: 0.7, fontSize: 13, valign: "middle" });

// ---------------- 3. Current state stats
pres.addSection({ title: "Current state" });
const s3 = content("Urgency is only discovered when someone reads the inbox", "Current state");
const stats = [
  ["78 min", "median wait before an urgent email request is triaged", C.accent3],
  ["64%", "of urgent inbox requests wait over an hour", C.accent3],
  ["18%", "of requests go to the wrong team first time", C.accent2],
  ["156 h", "coordinator time a month on triage, rework and chasers", C.accent1],
];
stats.forEach(([n, l, col], i) => {
  const x = 0.5 + i * 2.28;
  card(s3, x, 1.35, 2.1, 2.3, C.background2, `stat-${i}`);
  tb(s3, n, { x: x + 0.15, y: 1.55, w: 1.8, h: 0.9, fontSize: 36, bold: true, color: col, fontFace: THEME.headFontFace });
  tb(s3, l, { x: x + 0.15, y: 2.5, w: 1.8, h: 1.05, fontSize: 13, color: C.text1 });
});
tb(s3, "Six months, 7,894 requests (synthetic). 70% arrive by email or portal; 30% arrive outside desk hours, when the inbox is not worked at all. Also: 25% of priorities are inconsistent and 29% of residents chase for an update.",
  { x: 0.5, y: 3.95, w: 9.0, h: 0.9, fontSize: 13, color: C.accent6 });

// ---------------- 4. As-is flow and root cause
const s4 = content("Root cause: the first read of every request is manual", "Current state");
const steps = ["Email, portal, walk-in, phone", "Shared inbox, checked in batches", "Coordinator reads and judges", "Re-typed into CRM", "Forwarded to a team"];
steps.forEach((t, i) => {
  const x = 0.5 + i * 1.84;
  card(s4, x, 1.3, 1.6, 0.95, i === 1 || i === 2 ? "F6E3E6" : C.background2, `asis-${i}`);
  tb(s4, t, { x: x + 0.1, y: 1.3, w: 1.4, h: 0.95, fontSize: 12, color: C.text1, align: "center", valign: "middle" });
  if (i < steps.length - 1) s4.addShape(pres.shapes.RIGHT_ARROW, { x: x + 1.62, y: 1.67, w: 0.2, h: 0.22, fill: { color: C.accent6 }, line: { color: C.accent6 }, objectName: `arrow-${i}` });
});
const pains = [
  ["Batches and nights", "Inbox worked every ~2 hours, not at all 20:00-08:00"],
  ["No shared rules", "Category and priority depend on who is on shift"],
  ["Silent hand-offs", "No acknowledgement, so 29% of residents chase"],
];
pains.forEach(([h, b], i) => {
  const y = 2.6 + i * 0.75;
  s4.addShape(pres.shapes.OVAL, { x: 0.5, y: y + 0.08, w: 0.3, h: 0.3, fill: { color: C.accent3 }, line: { color: C.accent3 }, objectName: `pain-${i}` });
  tb(s4, [{ text: h + ": ", options: { bold: true } }, { text: b }], { x: 0.95, y, w: 4.6, h: 0.6, fontSize: 13, color: C.text1, valign: "middle" });
});
card(s4, 5.9, 2.6, 3.6, 2.2, C.text2, "rootcause");
tb(s4, [
  { text: "5 whys, in one line", options: { bold: true, color: C.accent2, breakLine: true } },
  { text: "A ceiling leak waited 80 minutes because nobody knew it was urgent until a person read it, and nobody reads the inbox continuously. This first read is the step AI can take over.", options: { color: C.background1 } },
], { x: 6.1, y: 2.75, w: 3.2, h: 1.95, fontSize: 13, paraSpaceAfter: 6 });

// ---------------- 5. Opportunities
pres.addSection({ title: "Design" });
const s5 = content("Eight opportunities scored; three form Wave 1", "Design");
const hdr = ["Opportunity", "Value", "Feas.", "Data", "Risk*", "Adopt.", "Score", "Decision"];
const rows = [
  ["Instant acknowledgement + response time", 3, 5, 5, 5, 5, "4.40", "Wave 1"],
  ["AI triage & routing, human approval", 5, 4, 4, 4, 4, "4.30", "Wave 1"],
  ["Automated weekly KPI report", 3, 5, 4, 5, 4, "4.10", "Wave 1"],
  ["Duplicate / same-issue detection", 3, 3, 3, 4, 4, "3.35", "Wave 2"],
  ["Predictive maintenance", 4, 2, 1, 4, 3, "3.00", "Wave 2"],
  ["Sentiment escalation", 2, 4, 3, 3, 3, "2.90", "Not now"],
  ["Resident FAQ assistant", 3, 3, 2, 3, 3, "2.85", "Not now"],
  ["Autonomous resolution", 4, 2, 2, 1, 2, "2.40", "Not now"],
];
const decCol = { "Wave 1": C.accent4, "Wave 2": C.accent2, "Not now": C.accent6 };
const tableRows = [hdr.map((h) => ({ text: h, options: { bold: true, color: C.background1, fill: { color: C.text2 } } }))];
rows.forEach((r) => tableRows.push(r.map((v, j) => ({
  text: String(v),
  options: j === 7 ? { bold: true, color: decCol[v] } : j === 6 ? { bold: true } : {},
}))));
s5.addTable(tableRows, {
  x: 0.5, y: 1.15, w: 9.0, colW: [3.3, 0.7, 0.7, 0.7, 0.7, 0.75, 0.75, 1.4],
  fontSize: 11, color: C.text1, border: { type: "solid", pt: 0.5, color: "D5DEE0" }, rowH: 0.36, valign: "middle",
  objectName: "opportunity-table",
});
tb(s5, "Weights: value 30%, feasibility 20%, data readiness 15%, risk 20%, adoption 15%. *Risk scored 5 = low risk. Wave 1 is one product: triage creates the structured data the other two use.",
  { x: 0.5, y: 4.55, w: 9.0, h: 0.5, fontSize: 11, color: C.accent6 });

// ---------------- 6. Future state flow
const s6 = content("Future state: the agent proposes, a person decides", "Design");
const fx = [["Request arrives, any channel", C.background2], ["Personal data removed", C.background2], ["AI agent proposes category, priority, owner, reply", "D7ECEF"]];
fx.forEach(([t, fill], i) => {
  const y = 1.2 + i * 0.95;
  card(s6, 0.5, y, 2.6, 0.75, fill, `fs-${i}`);
  tb(s6, t, { x: 0.6, y, w: 2.4, h: 0.75, fontSize: 12, color: C.text1, align: "center", valign: "middle" });
  if (i < 2) s6.addShape(pres.shapes.DOWN_ARROW, { x: 1.7, y: y + 0.76, w: 0.2, h: 0.18, fill: { color: C.accent6 }, line: { color: C.accent6 }, objectName: `fs-arrow-${i}` });
});
const lanes = [
  ["Safety or urgent", "Duty manager alerted now; coordinator confirms for the record", C.accent3, "15%"],
  ["Confident (>= 0.6)", "Coordinator approves in one click", C.accent4, "72.5%"],
  ["Unsure (< 0.6)", "Coordinator reviews in full, proposal as a hint", C.accent2, "12.5%"],
];
lanes.forEach(([h, b, col, pct], i) => {
  const y = 1.2 + i * 0.95;
  s6.addShape(pres.shapes.RIGHT_ARROW, { x: 3.2, y: 2.18 + 0.12, w: 0.35, h: 0.25, fill: { color: C.accent6 }, line: { color: C.accent6 }, objectName: `lane-arrow-${i}` });
  card(s6, 3.7, y, 3.6, 0.75, C.background2, `lane-${i}`);
  s6.addShape(pres.shapes.OVAL, { x: 3.82, y: y + 0.2, w: 0.35, h: 0.35, fill: { color: col }, line: { color: col }, objectName: `lane-dot-${i}` });
  tb(s6, [{ text: h, options: { bold: true, breakLine: true } }, { text: b }], { x: 4.3, y: y + 0.05, w: 2.3, h: 0.65, fontSize: 11, color: C.text1, valign: "middle" });
  tb(s6, pct, { x: 6.55, y, w: 0.7, h: 0.75, fontSize: 13, bold: true, color: col, align: "right", valign: "middle" });
});
card(s6, 7.5, 1.2, 2.0, 2.65, C.text2, "fs-out");
tb(s6, [
  { text: "Then, automatically", options: { bold: true, color: C.accent2, breakLine: true } },
  { text: "Route to the team", options: { bullet: true, breakLine: true } },
  { text: "Acknowledge resident with target time", options: { bullet: true, breakLine: true } },
  { text: "Log proposal, decision, override", options: { bullet: true } },
], { x: 7.65, y: 1.35, w: 1.75, h: 2.4, fontSize: 11, color: C.background1, paraSpaceAfter: 5 });
tb(s6, "Shares are the prototype's review-mode mix on the 80-request test set.", { x: 0.5, y: 4.2, w: 9, h: 0.4, fontSize: 11, color: C.accent6 });

// ---------------- 7. Controls
const s7 = content("Controls built into the design", "Design");
const ctr = [
  ["Human approval", "No request is routed without a coordinator in release 1; overrides are logged and reviewed weekly."],
  ["Safety bypass + rule net", "Safety and P1 skip the queue. Keyword safety signals can add an escalation on top of the model, never remove one."],
  ["Privacy by design", "Emails, phones, IBANs, card numbers and Eircodes are removed before the model sees text or anything is logged."],
  ["Fail safe", "Model output is validated against a schema; any failure falls back to rules, so no request is dropped."],
  ["Audit trail", "Every proposal, decision and override is written to a log for accountability and improvement."],
  ["Go-live gate", "Pilot only if P1 recall and quick-approve precision are both at least 95% on the test set."],
];
ctr.forEach(([h, b], i) => {
  const col = i % 2, row = Math.floor(i / 2);
  const x = 0.5 + col * 4.6, y = 1.2 + row * 1.25;
  card(s7, x, y, 4.4, 1.08, C.background2, `ctrl-${i}`);
  tb(s7, [{ text: h, options: { bold: true, color: C.text2, breakLine: true } }, { text: b, options: { color: C.text1 } }],
    { x: x + 0.2, y: y + 0.1, w: 4.0, h: 0.9, fontSize: 12, paraSpaceAfter: 3 });
});

// ---------------- 8. Value case
pres.addSection({ title: "Value and evidence" });
const s8 = content("Value case: 0.6 of a coordinator back each month", "Value and evidence");
s8.addChart(pres.charts.BAR, [{ name: "Hours per month", labels: ["Current", "Future (base)"], values: [156, 64] }], {
  x: 0.5, y: 1.15, w: 4.0, h: 3.4, barDir: "col",
  chartColors: [HEX.accent6, HEX.accent1], invertedColors: [HEX.accent6, HEX.accent1],
  showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 12, dataLabelColor: HEX.dk1, dataLabelFontFace: "+mn-lt",
  showTitle: true, title: "Coordinator hours a month", titleFontSize: 13, titleColor: HEX.dk2, titleFontFace: "+mn-lt",
  catAxisLabelColor: HEX.accent6, valAxisLabelColor: HEX.accent6, catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt",
  catAxisLabelFontSize: 11, valAxisLabelFontSize: 10, valGridLine: { color: "DDE4E6", size: 0.5 }, catGridLine: { style: "none" },
  showLegend: false, valAxisMaxVal: 180, objectName: "effort-chart",
});
const scen = [
  [{ text: "Scenario", options: { bold: true, color: C.background1, fill: { color: C.text2 } } },
   { text: "Net / year", options: { bold: true, color: C.background1, fill: { color: C.text2 } } },
   { text: "Payback", options: { bold: true, color: C.background1, fill: { color: C.text2 } } }],
  ["Low (60%)", "EUR 13,600", "9.7 months"],
  [{ text: "Base", options: { bold: true } }, { text: "EUR 26,800", options: { bold: true } }, { text: "4.9 months", options: { bold: true } }],
  ["High (125%)", "EUR 35,000", "3.8 months"],
];
s8.addTable(scen, { x: 4.9, y: 1.2, w: 4.6, colW: [1.5, 1.6, 1.5], fontSize: 12, color: C.text1, rowH: 0.38,
  border: { type: "solid", pt: 0.5, color: "D5DEE0" }, valign: "middle", objectName: "scenario-table" });
tb(s8, [
  { text: "Build EUR 11,000 (20 days); run about EUR 6,200 a year.", options: { bullet: true, breakLine: true } },
  { text: "Saving is capacity, not headcount: time moves from admin to residents.", options: { bullet: true, breakLine: true } },
  { text: "The case fails only if coordinators don't trust proposals and re-read everything, hence the precision gate.", options: { bullet: true } },
], { x: 4.9, y: 2.95, w: 4.6, h: 1.6, fontSize: 12, color: C.text1, paraSpaceAfter: 5 });

// ---------------- 9. Evaluation
const s9 = content("Prototype routes well but misses urgency", "Value and evidence");
const evals = [
  ["Category accuracy", "88.7%", "", C.text2],
  ["Quick-approve precision", "98.3%", "Gate 95%: pass", C.accent4],
  ["P1 (urgent) recall", "69.2%", "Gate 95%: fail", C.accent3],
  ["Safety escalation recall", "72.7%", "Gate 95%: fail", C.accent3],
];
evals.forEach(([l, v, g, col], i) => {
  const x = 0.5 + i * 2.28;
  card(s9, x, 1.2, 2.1, 1.75, C.background2, `eval-${i}`);
  tb(s9, v, { x: x + 0.15, y: 1.32, w: 1.8, h: 0.7, fontSize: 30, bold: true, color: col, fontFace: THEME.headFontFace });
  tb(s9, l, { x: x + 0.15, y: 2.02, w: 1.8, h: 0.45, fontSize: 12, color: C.text1 });
  if (g) tb(s9, g, { x: x + 0.15, y: 2.5, w: 1.8, h: 0.3, fontSize: 11, bold: true, color: col });
});
tb(s9, [
  { text: "What the misses show", options: { bold: true, color: C.text2, breakLine: true } },
  { text: "Keywords find what a request is about, not how bad it is: \"toilet overflowing onto the floor\" was routed right but marked routine.", options: { bullet: true, breakLine: true } },
  { text: "The riskiest cases use ordinary words: \"a man I don't know followed me in through the main door\".", options: { bullet: true, breakLine: true } },
  { text: "Next: run the LLM classifier, with the rule safety net kept, through the same 80-request test.", options: { bullet: true } },
], { x: 0.5, y: 3.15, w: 9.0, h: 1.8, fontSize: 13, color: C.text1, paraSpaceAfter: 5 });

// ---------------- 10. Roadmap
pres.addSection({ title: "Next steps" });
const s10 = content("Roadmap and decision needed", "Next steps");
const phases = [
  ["Weeks 1-2", "Evaluate and shadow", "LLM classifier through the test gate. Agent proposes in the background; coordinators work as today. Measure the real baseline."],
  ["Weeks 3-8", "Pilot", "Email and portal only, one building. Weekly override review; KPIs reported weekly."],
  ["Month 3+", "Scale and Wave 2", "All channels. Add duplicate detection; collect data for predictive maintenance."],
];
phases.forEach(([w, h, b], i) => {
  const x = 0.5 + i * 3.05;
  card(s10, x, 1.2, 2.85, 2.35, C.background2, `phase-${i}`);
  tb(s10, w, { x: x + 0.2, y: 1.32, w: 2.45, h: 0.3, fontSize: 11, bold: true, color: C.accent1 });
  tb(s10, h, { x: x + 0.2, y: 1.62, w: 2.45, h: 0.4, fontSize: 17, bold: true, color: C.text2, fontFace: THEME.headFontFace });
  tb(s10, b, { x: x + 0.2, y: 2.08, w: 2.45, h: 1.4, fontSize: 12, color: C.text1 });
  if (i < 2) s10.addShape(pres.shapes.RIGHT_ARROW, { x: x + 2.88, y: 2.25, w: 0.15, h: 0.25, fill: { color: C.accent6 }, line: { color: C.accent6 }, objectName: `phase-arrow-${i}` });
});
card(s10, 0.5, 3.8, 9.0, 1.05, C.text2, "decision");
tb(s10, [
  { text: "Decision: ", options: { bold: true, color: C.accent2 } },
  { text: "approve two weeks of evaluation and shadow running (about 6 days of effort, no change for residents). Go or no-go on the pilot is set by the safety gate, not by opinion.", options: { color: C.background1 } },
], { x: 0.75, y: 3.85, w: 8.5, h: 0.95, fontSize: 14, valign: "middle" });

(async () => {
  const out = path.join(__dirname, "AI_Process_Redesign_Case_Study.pptx");
  await pres.writeFile({ fileName: out });
  await applyTheme(out, THEME);
  console.log("wrote", out);
})();
