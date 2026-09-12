/**
 * PPC Audit Presentation Generator
 * 
 * USAGE: Populate the DATA object below with values from Shurq tool calls,
 * then run: node generate_audit.js
 * 
 * This template produces an 11-slide deck following the PPC Audit formula.
 * Adapt slide content based on account characteristics (see SKILL.md).
 */

const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");

// ============================================================
// DATA — Fill this section from Shurq tool results
// ============================================================
const DATA = {
  // Account info
  accountName: "ACCOUNT_NAME",
  dateRange: "Feb 14 – Mar 15, 2026",
  presentationDate: "March 16, 2026",

  // Slide 2: Snapshot metrics
  snapshot: {
    revenue: "$4,065",
    orders: "172",
    aov: "$23.63",
    units: "180",
    adSpend: "$1,629",
    tacos: "40.1%",
    acos: "124%",
    roas: "0.81x",
  },
  warningMessage: "Ad spend is 40% of total revenue. Immediate restructuring required.",

  // Slide 3: Product comparison (2+ products)
  products: [
    {
      name: "Product A",
      status: "good", // "good" or "bad"
      metrics: [
        ["Revenue", "$2,791"],
        ["Units Sold", "129"],
        ["ACoS", "70.5%"],
        ["TACoS", "19.2%"],
        ["ROAS", "1.42x"],
        ["CPC", "$0.86"],
        ["CVR", "5.29%"],
        ["Gross Margin", "78.9%"],
      ],
      summary: "Solid foundation — needs keyword refinement",
    },
    {
      name: "Product B",
      status: "bad",
      metrics: [
        ["Revenue", "$1,273"],
        ["Units Sold", "51"],
        ["ACoS", "198.7%"],
        ["TACoS", "85.8%"],
        ["ROAS", "0.50x"],
        ["CPC", "$1.64"],
        ["CVR", "3.30%"],
        ["Gross Margin", "73.1%"],
      ],
      summary: "Spending $1,092 to generate $550 in ad sales",
    },
  ],

  // Slide 4: Ad budget chart
  adBudgetChart: {
    labels: ["Product A (SP)", "Product A (SB)", "Product B (SP)"],
    spend: [537, 778, 1092],
    sales: [762, 1130, 550],
    insights: [
      { title: "Product A SB: 1.45x ROAS", detail: "Best performing channel.", color: "green" },
      { title: "Product A SP: 1.42x ROAS", detail: "Decent but lagging SB.", color: "orange" },
      { title: "Product B SP: 0.50x ROAS", detail: "Losing $0.50 for every $1 spent.", color: "red" },
    ],
    campaignCount: 961,
    monthlyRevenue: "$4K",
  },

  // Slide 5: Top converting search terms (up to 8 rows)
  topTerms: [
    { term: "lavender syrup (SB)", sales: "$461.79", orders: "20", acos: "68.9%", cvr: "5.9%", roas: "1.45x" },
    { term: "lavender syrup (SP)", sales: "$175.92", orders: "8", acos: "51.6%", cvr: "8.2%", roas: "1.94x" },
    { term: "lavender earl grey syrup", sales: "$131.94", orders: "5", acos: "23.8%", cvr: "13.2%", roas: "4.19x" },
    // ... add more rows
  ],
  topTermsInsight: '"Lavender earl grey syrup" converts at 13.2% with 4.19x ROAS — this is the hero keyword.',

  // Slide 6: New keywords to create (up to 10)
  newKeywords: [
    { kw: "lilac syrup", roas: "38.6x", note: "Niche adjacent — huge CVR" },
    { kw: "blueberry lavender syrup", roas: "44.9x", note: "100% CVR on small volume" },
    { kw: "lavender syrup for alcohol", roas: "51.1x", note: "Cocktail buyer intent" },
    // ... add more
  ],
  newKeywordsStrategy: 'Create exact match campaigns. Start with low bids ($0.60–$0.80) and scale winners.',

  // Slide 7: Problem product stats
  problemProduct: {
    stats: [
      { val: "198.7%", label: "ACoS", sub: "Losing $1 for every $1 earned" },
      { val: "$49.65", label: "Cost Per Acquisition", sub: "On a $24.99 product" },
      { val: "0.50x", label: "ROAS", sub: "50 cents back per dollar spent" },
    ],
    wastedTerms: [
      ["ryze mushroom coffee (SP exact)", "$191.67", "4 orders", "191.8% ACoS"],
      ["mushroom coffee (SP exact)", "$143.03", "5 orders", "114.5% ACoS"],
      ["mushroom coffee instant", "$83.50", "0 orders", "∞ ACoS"],
      // ... add more
    ],
  },

  // Slide 8: Keyword actions (create vs negative)
  keywordActions: {
    create: [
      { kw: "mushroom coffee pods", note: "8.6% ACoS, 100% CVR" },
      { kw: "flavored mushroom coffee", note: "11.6% ACoS, 50% CVR" },
      // ... add more
    ],
    negative: [
      { kw: "ryze mushroom coffee", spend: "$289" },
      { kw: "mushroom coffee instant", spend: "$83" },
      // ... add more
    ],
  },

  // Slide 9: Syrup/main product negatives
  mainProductNegatives: [
    { term: "lavender syrup for coffee", spend: "$41.24", channel: "SP", reason: "Converts on SB but not SP" },
    { term: "lavender coffee syrup", spend: "$17.39", channel: "SP", reason: "Zero orders despite 19 clicks" },
    // ... add more
  ],
  estimatedSavings: "$735+",

  // Slide 10: Action plan
  actionPlan: {
    thisWeek: [
      "Pause or drastically cut Problem Product ad spend",
      "Add all negative keywords listed in this report",
      "Consolidate campaigns into structured groups",
      "Enter COGS data for accurate profitability tracking",
    ],
    nextTwoWeeks: [
      "Create exact match campaigns for new keywords",
      "Launch competitor conquest campaigns",
      "Build new keyword themes discovered",
      "Test lower bids on long-tail keywords only",
    ],
    ongoing: [
      "Weekly search term mining & negative keyword hygiene",
      "Scale SB Video creative to new keywords",
      "Monitor TACoS target: get below 20% overall",
      "Review problem product listing for conversion optimization",
    ],
  },
};

// ============================================================
// DESIGN SYSTEM — Consistent across all audits
// ============================================================
const C = {
  dark: "1A1A2E",
  darkAlt: "16213E",
  accent: "E94560",
  gold: "F5A623",
  green: "27AE60",
  red: "E74C3C",
  orange: "F39C12",
  white: "FFFFFF",
  offWhite: "F8F9FA",
  lightGray: "E9ECEF",
  medGray: "6C757D",
  text: "2D3436",
  textLight: "636E72",
  teal: "0F9B8E",
  purple: "8E44AD",
};

const makeShadow = () => ({ type: "outer", blur: 4, offset: 2, angle: 135, color: "000000", opacity: 0.12 });

// Icon helper
function renderIconSvg(IconComponent, color, size = 256) {
  return ReactDOMServer.renderToStaticMarkup(
    React.createElement(IconComponent, { color, size: String(size) })
  );
}
async function iconToBase64Png(IconComponent, color, size = 256) {
  const svg = renderIconSvg(IconComponent, color, size);
  const pngBuffer = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + pngBuffer.toString("base64");
}

// Color helpers for tables
function acosColor(val) {
  const n = parseFloat(val);
  if (n < 30) return C.green;
  if (n < 70) return C.orange;
  return C.red;
}
function roasColor(val) {
  const n = parseFloat(val);
  if (n >= 2) return C.green;
  if (n >= 1) return C.orange;
  return C.red;
}
function insightAccentColor(color) {
  if (color === "green") return C.green;
  if (color === "orange") return C.orange;
  return C.red;
}

// ============================================================
// SLIDE BUILDERS
// ============================================================

function addTopBar(slide, color = C.accent) {
  slide.addShape("rect", { x: 0, y: 0, w: 10, h: 0.06, fill: { color } });
}

function addSlideTitle(slide, title, opts = {}) {
  const color = opts.color || C.dark;
  slide.addText(title, {
    x: 0.6, y: 0.3, w: 8.8, h: 0.6,
    fontSize: opts.fontSize || 24, fontFace: "Trebuchet MS", color, bold: true, margin: 0,
  });
}

// --- Slide 1: Title ---
function buildTitleSlide(pres) {
  const s = pres.addSlide();
  s.background = { color: C.dark };
  addTopBar(s, C.accent);
  s.addText(DATA.accountName.toUpperCase(), {
    x: 0.8, y: 1.2, w: 8.4, h: 1.0,
    fontSize: 48, fontFace: "Trebuchet MS", color: C.white, bold: true, charSpacing: 4, margin: 0,
  });
  s.addText("PPC Performance Audit & Keyword Strategy", {
    x: 0.8, y: 2.1, w: 8.4, h: 0.6,
    fontSize: 22, fontFace: "Calibri", color: C.gold, margin: 0,
  });
  s.addText(`30-Day Review  •  ${DATA.dateRange}`, {
    x: 0.8, y: 2.8, w: 8.4, h: 0.5,
    fontSize: 14, fontFace: "Calibri", color: C.medGray, margin: 0,
  });
  s.addShape("rect", { x: 0, y: 5.0, w: 10, h: 0.625, fill: { color: "0D0D1A" } });
  s.addText("Prepared by Sophie Society  |  Powered by Shurq Analytics", {
    x: 0.8, y: 5.05, w: 6.0, h: 0.525,
    fontSize: 11, fontFace: "Calibri", color: C.medGray, align: "left", valign: "middle",
  });
  s.addText(DATA.presentationDate, {
    x: 7.0, y: 5.05, w: 2.5, h: 0.525,
    fontSize: 11, fontFace: "Calibri", color: C.medGray, align: "right", valign: "middle",
  });
}

// --- Slide 2: Snapshot ---
async function buildSnapshotSlide(pres) {
  const { FaExclamationTriangle } = require("react-icons/fa");
  const s = pres.addSlide();
  s.background = { color: C.offWhite };
  addTopBar(s, C.accent);
  addSlideTitle(s, "30-DAY PERFORMANCE SNAPSHOT");

  const row1 = [
    { val: DATA.snapshot.revenue, label: "Total Revenue", color: C.teal },
    { val: DATA.snapshot.orders, label: "Orders", color: C.darkAlt },
    { val: DATA.snapshot.aov, label: "Avg Order Value", color: C.purple },
    { val: DATA.snapshot.units, label: "Units Sold", color: C.gold },
  ];
  const row2 = [
    { val: DATA.snapshot.adSpend, label: "Ad Spend", color: C.red },
    { val: DATA.snapshot.tacos, label: "TACoS", color: C.orange },
    { val: DATA.snapshot.acos, label: "ACoS", color: C.red },
    { val: DATA.snapshot.roas, label: "ROAS", color: C.red },
  ];

  const boxW = 2.05, gap = 0.2, startX = 0.6;
  [row1, row2].forEach((row, ri) => {
    row.forEach((d, i) => {
      const bx = startX + i * (boxW + gap);
      const by = ri === 0 ? 1.15 : 2.75;
      s.addShape("rect", { x: bx, y: by, w: boxW, h: 1.3, fill: { color: C.white }, shadow: makeShadow() });
      s.addShape("rect", { x: bx, y: by, w: boxW, h: 0.05, fill: { color: d.color } });
      const isRedVal = ri === 1 && [C.red].includes(d.color);
      s.addText(d.val, {
        x: bx, y: by + 0.2, w: boxW, h: 0.65,
        fontSize: 28, fontFace: "Trebuchet MS", color: isRedVal ? C.red : C.dark, bold: true, align: "center", valign: "middle", margin: 0,
      });
      s.addText(d.label, {
        x: bx, y: by + 0.85, w: boxW, h: 0.35,
        fontSize: 11, fontFace: "Calibri", color: C.textLight, align: "center", valign: "top", margin: 0,
      });
    });
  });

  // Warning callout
  s.addShape("rect", { x: 0.6, y: 4.35, w: 8.8, h: 0.95, fill: { color: "FFF3CD" }, shadow: makeShadow() });
  s.addShape("rect", { x: 0.6, y: 4.35, w: 0.06, h: 0.95, fill: { color: C.orange } });
  const warnIcon = await iconToBase64Png(FaExclamationTriangle, "#F39C12", 256);
  s.addImage({ data: warnIcon, x: 0.85, y: 4.55, w: 0.35, h: 0.35 });
  s.addText(DATA.warningMessage, {
    x: 1.35, y: 4.4, w: 7.9, h: 0.85,
    fontSize: 12, fontFace: "Calibri", color: C.text, valign: "middle", margin: 0,
  });
}

// --- Slide 3: Product Comparison ---
async function buildProductComparisonSlide(pres) {
  if (DATA.products.length < 2) return; // Skip for single-product accounts
  const { FaCheckCircle, FaTimesCircle } = require("react-icons/fa");
  const s = pres.addSlide();
  s.background = { color: C.offWhite };
  addTopBar(s, C.accent);
  addSlideTitle(s, "PRODUCT PERFORMANCE COMPARISON");

  const checkIcon = await iconToBase64Png(FaCheckCircle, "#27AE60", 256);
  const crossIcon = await iconToBase64Png(FaTimesCircle, "#E74C3C", 256);

  DATA.products.slice(0, 2).forEach((p, pi) => {
    const px = pi === 0 ? 0.6 : 5.15;
    const isGood = p.status === "good";
    const accentColor = isGood ? C.green : C.red;

    s.addShape("rect", { x: px, y: 1.1, w: 4.25, h: 4.15, fill: { color: C.white }, shadow: makeShadow() });
    s.addShape("rect", { x: px, y: 1.1, w: 4.25, h: 0.06, fill: { color: accentColor } });
    s.addImage({ data: isGood ? checkIcon : crossIcon, x: px + 0.25, y: 1.3, w: 0.3, h: 0.3 });
    s.addText(p.name, {
      x: px + 0.65, y: 1.28, w: 3.4, h: 0.35,
      fontSize: 15, fontFace: "Trebuchet MS", color: accentColor, bold: true, margin: 0,
    });

    p.metrics.forEach((m, i) => {
      const my = 1.8 + i * 0.38;
      s.addText(m[0], { x: px + 0.3, y: my, w: 2.2, h: 0.32, fontSize: 11, fontFace: "Calibri", color: C.textLight, valign: "middle", margin: 0 });
      const isRedMetric = !isGood && ["ACoS", "TACoS", "ROAS", "CPC"].includes(m[0]);
      s.addText(m[1], {
        x: px + 2.6, y: my, w: 1.4, h: 0.32,
        fontSize: 12, fontFace: "Calibri", color: isRedMetric ? C.red : C.dark, bold: true, align: "right", valign: "middle", margin: 0,
      });
      if (i < p.metrics.length - 1) {
        s.addShape("line", { x: px + 0.3, y: my + 0.34, w: 3.7, h: 0, line: { color: C.lightGray, width: 0.5 } });
      }
    });

    s.addText(p.summary, {
      x: px + 0.3, y: 4.85, w: 3.7, h: 0.3,
      fontSize: 10, fontFace: "Calibri", color: accentColor, italic: true, margin: 0,
    });
  });
}

// --- Slide 4: Ad Budget Breakdown ---
function buildAdBudgetSlide(pres) {
  const s = pres.addSlide();
  s.background = { color: C.offWhite };
  addTopBar(s, C.accent);
  addSlideTitle(s, "WHERE THE AD BUDGET GOES");

  const d = DATA.adBudgetChart;
  s.addChart(pres.charts.BAR, [
    { name: "Ad Spend", labels: d.labels, values: d.spend },
    { name: "Ad Sales", labels: d.labels, values: d.sales },
  ], {
    x: 0.4, y: 1.0, w: 5.5, h: 3.5, barDir: "col",
    chartColors: [C.red, C.teal],
    chartArea: { fill: { color: C.white }, roundedCorners: true },
    catAxisLabelColor: C.textLight, catAxisLabelFontSize: 9,
    valAxisLabelColor: C.textLight,
    valGridLine: { color: "E2E8F0", size: 0.5 },
    catGridLine: { style: "none" },
    showValue: true, dataLabelPosition: "outEnd", dataLabelColor: C.text, dataLabelFontSize: 9,
    showLegend: true, legendPos: "b", legendFontSize: 10,
    valAxisNumFmt: "$#,##0",
  });

  // Insight cards
  d.insights.forEach((ins, i) => {
    const iy = 1.1 + i * 1.1;
    s.addShape("rect", { x: 6.1, y: iy, w: 3.6, h: 0.9, fill: { color: C.white }, shadow: makeShadow() });
    s.addShape("rect", { x: 6.1, y: iy, w: 0.05, h: 0.9, fill: { color: insightAccentColor(ins.color) } });
    s.addText([
      { text: ins.title, options: { bold: true, fontSize: 12, breakLine: true } },
      { text: ins.detail, options: { fontSize: 10, color: C.textLight } },
    ], { x: 6.3, y: iy + 0.08, w: 3.2, h: 0.74, fontFace: "Calibri", color: C.dark, valign: "top", margin: 0 });
  });

  if (d.campaignCount) {
    s.addShape("rect", { x: 6.1, y: 4.0, w: 3.6, h: 0.75, fill: { color: "FDECEA" } });
    s.addText([
      { text: `${d.campaignCount} campaigns `, options: { bold: true, fontSize: 14, color: C.red } },
      { text: `for a ${d.monthlyRevenue}/mo account — massive campaign sprawl`, options: { fontSize: 11, color: C.text } },
    ], { x: 6.25, y: 4.05, w: 3.3, h: 0.65, fontFace: "Calibri", valign: "middle", margin: 0 });
  }
}

// --- Slide 5: Top Converting Terms ---
async function buildTopTermsSlide(pres) {
  const { FaBullseye } = require("react-icons/fa");
  const s = pres.addSlide();
  s.background = { color: C.offWhite };
  addTopBar(s, C.green);

  const icon = await iconToBase64Png(FaBullseye, "#27AE60", 256);
  s.addImage({ data: icon, x: 0.6, y: 0.35, w: 0.35, h: 0.35 });
  s.addText("TOP CONVERTING SEARCH TERMS", {
    x: 1.05, y: 0.3, w: 8.4, h: 0.5,
    fontSize: 22, fontFace: "Trebuchet MS", color: C.dark, bold: true, margin: 0,
  });

  const headerRow = [[
    { text: "Search Term", options: { bold: true, color: C.white, fill: { color: C.dark }, fontSize: 10, fontFace: "Calibri" } },
    { text: "Sales", options: { bold: true, color: C.white, fill: { color: C.dark }, fontSize: 10, fontFace: "Calibri", align: "right" } },
    { text: "Orders", options: { bold: true, color: C.white, fill: { color: C.dark }, fontSize: 10, fontFace: "Calibri", align: "center" } },
    { text: "ACoS", options: { bold: true, color: C.white, fill: { color: C.dark }, fontSize: 10, fontFace: "Calibri", align: "center" } },
    { text: "CVR", options: { bold: true, color: C.white, fill: { color: C.dark }, fontSize: 10, fontFace: "Calibri", align: "center" } },
    { text: "ROAS", options: { bold: true, color: C.white, fill: { color: C.dark }, fontSize: 10, fontFace: "Calibri", align: "center" } },
  ]];

  const dataRows = DATA.topTerms.map((t, i) => {
    const rf = { fill: { color: i % 2 === 0 ? C.white : "F4F6F8" } };
    return [
      { text: t.term, options: { ...rf, fontSize: 10, fontFace: "Calibri", color: C.dark } },
      { text: t.sales, options: { ...rf, fontSize: 10, fontFace: "Calibri", color: C.dark, bold: true, align: "right" } },
      { text: t.orders, options: { ...rf, fontSize: 10, fontFace: "Calibri", color: C.dark, align: "center" } },
      { text: t.acos, options: { ...rf, fontSize: 10, fontFace: "Calibri", color: acosColor(t.acos), align: "center", bold: true } },
      { text: t.cvr, options: { ...rf, fontSize: 10, fontFace: "Calibri", color: C.dark, align: "center" } },
      { text: t.roas, options: { ...rf, fontSize: 10, fontFace: "Calibri", color: roasColor(t.roas), align: "center", bold: true } },
    ];
  });

  s.addTable(headerRow.concat(dataRows), {
    x: 0.6, y: 1.0, w: 8.8, colW: [2.8, 1.0, 0.8, 0.9, 0.8, 0.8], border: { pt: 0.5, color: C.lightGray }, rowH: 0.32,
  });

  // Insight callout
  const tableBottom = 1.0 + (DATA.topTerms.length + 1) * 0.32 + 0.3;
  s.addShape("rect", { x: 0.6, y: tableBottom, w: 8.8, h: 1.0, fill: { color: "E8F8F5" }, shadow: makeShadow() });
  s.addShape("rect", { x: 0.6, y: tableBottom, w: 0.06, h: 1.0, fill: { color: C.green } });
  s.addText([
    { text: "Key Insight: ", options: { bold: true, fontSize: 12 } },
    { text: DATA.topTermsInsight, options: { fontSize: 11 } },
  ], { x: 0.85, y: tableBottom + 0.05, w: 8.35, h: 0.9, fontFace: "Calibri", color: C.dark, valign: "middle", margin: 0 });
}

// --- Slide 6: New Keywords ---
async function buildNewKeywordsSlide(pres) {
  const { FaRocket, FaLightbulb } = require("react-icons/fa");
  const s = pres.addSlide();
  s.background = { color: C.offWhite };
  addTopBar(s, C.teal);

  const icon = await iconToBase64Png(FaRocket, "#0F9B8E", 256);
  s.addImage({ data: icon, x: 0.6, y: 0.35, w: 0.35, h: 0.35 });
  s.addText("NEW KEYWORDS TO CREATE", {
    x: 1.05, y: 0.3, w: 8.4, h: 0.5,
    fontSize: 22, fontFace: "Trebuchet MS", color: C.dark, bold: true, margin: 0,
  });
  s.addText("High-converting search terms discovered — ready for exact match harvesting", {
    x: 0.6, y: 0.85, w: 8.8, h: 0.35, fontSize: 11, fontFace: "Calibri", color: C.textLight, margin: 0,
  });

  const cardW = 4.25, cardH = 0.38;
  DATA.newKeywords.slice(0, 10).forEach((k, i) => {
    const col = i < 5 ? 0 : 1;
    const row = i < 5 ? i : i - 5;
    const cx = 0.6 + col * (cardW + 0.3);
    const cy = 1.35 + row * (cardH + 0.12);
    s.addShape("rect", { x: cx, y: cy, w: cardW, h: cardH, fill: { color: C.white }, shadow: makeShadow() });
    s.addShape("rect", { x: cx, y: cy, w: 0.04, h: cardH, fill: { color: C.teal } });
    s.addText(k.kw, { x: cx + 0.12, y: cy, w: 2.0, h: cardH, fontSize: 10, fontFace: "Calibri", color: C.dark, bold: true, valign: "middle", margin: 0 });
    s.addText(k.roas, { x: cx + 2.1, y: cy, w: 0.65, h: cardH, fontSize: 10, fontFace: "Calibri", color: C.green, bold: true, align: "center", valign: "middle", margin: 0 });
    s.addText(k.note, { x: cx + 2.7, y: cy, w: 1.45, h: cardH, fontSize: 8, fontFace: "Calibri", color: C.textLight, valign: "middle", margin: 0 });
  });

  // Strategy callout
  s.addShape("rect", { x: 0.6, y: 4.1, w: 8.8, h: 1.2, fill: { color: "E0F2FE" }, shadow: makeShadow() });
  s.addShape("rect", { x: 0.6, y: 4.1, w: 0.06, h: 1.2, fill: { color: C.teal } });
  const bulb = await iconToBase64Png(FaLightbulb, "#0F9B8E", 256);
  s.addImage({ data: bulb, x: 0.85, y: 4.35, w: 0.3, h: 0.3 });
  s.addText([
    { text: "Strategy: ", options: { bold: true, fontSize: 12 } },
    { text: DATA.newKeywordsStrategy, options: { fontSize: 11 } },
  ], { x: 1.3, y: 4.15, w: 7.9, h: 1.1, fontFace: "Calibri", color: C.dark, valign: "middle", margin: 0 });
}

// --- Slide 7: Problem Product ---
function buildProblemSlide(pres) {
  const d = DATA.problemProduct;
  const s = pres.addSlide();
  s.background = { color: C.dark };
  addTopBar(s, C.red);
  addSlideTitle(s, "THE PROBLEM", { color: C.white });

  d.stats.forEach((st, i) => {
    const bx = 0.6 + i * 3.1;
    s.addShape("rect", { x: bx, y: 1.15, w: 2.8, h: 1.6, fill: { color: "2A1A2E" } });
    s.addShape("rect", { x: bx, y: 1.15, w: 2.8, h: 0.05, fill: { color: C.red } });
    s.addText(st.val, { x: bx, y: 1.3, w: 2.8, h: 0.7, fontSize: 32, fontFace: "Trebuchet MS", color: C.red, bold: true, align: "center", valign: "middle", margin: 0 });
    s.addText(st.label, { x: bx, y: 2.0, w: 2.8, h: 0.3, fontSize: 12, fontFace: "Calibri", color: C.white, align: "center", valign: "middle", margin: 0 });
    s.addText(st.sub, { x: bx, y: 2.3, w: 2.8, h: 0.3, fontSize: 9, fontFace: "Calibri", color: C.medGray, align: "center", valign: "top", margin: 0 });
  });

  s.addText("TOP WASTED SPEND TERMS", {
    x: 0.6, y: 3.05, w: 8.8, h: 0.4, fontSize: 14, fontFace: "Trebuchet MS", color: C.gold, bold: true, margin: 0,
  });

  const hdr = [[
    { text: "Search Term", options: { bold: true, color: C.white, fill: { color: C.red }, fontSize: 10, fontFace: "Calibri" } },
    { text: "Spend", options: { bold: true, color: C.white, fill: { color: C.red }, fontSize: 10, fontFace: "Calibri", align: "right" } },
    { text: "Result", options: { bold: true, color: C.white, fill: { color: C.red }, fontSize: 10, fontFace: "Calibri", align: "center" } },
    { text: "ACoS", options: { bold: true, color: C.white, fill: { color: C.red }, fontSize: 10, fontFace: "Calibri", align: "center" } },
  ]];
  const rows = d.wastedTerms.map((r, i) => {
    const rf = { fill: { color: i % 2 === 0 ? "2A1A2E" : C.dark } };
    return [
      { text: r[0], options: { ...rf, fontSize: 10, fontFace: "Calibri", color: C.white } },
      { text: r[1], options: { ...rf, fontSize: 10, fontFace: "Calibri", color: C.gold, bold: true, align: "right" } },
      { text: r[2], options: { ...rf, fontSize: 10, fontFace: "Calibri", color: r[2].includes("0") ? C.red : C.medGray, align: "center" } },
      { text: r[3], options: { ...rf, fontSize: 10, fontFace: "Calibri", color: C.red, bold: true, align: "center" } },
    ];
  });
  s.addTable(hdr.concat(rows), {
    x: 0.6, y: 3.5, w: 8.8, colW: [4.0, 1.3, 1.5, 2.0], border: { pt: 0.5, color: "333355" }, rowH: 0.3,
  });
}

// --- Slide 8: Keyword Actions ---
async function buildKeywordActionsSlide(pres) {
  const { FaCheckCircle, FaBan } = require("react-icons/fa");
  const s = pres.addSlide();
  s.background = { color: C.offWhite };
  addTopBar(s, C.accent);
  addSlideTitle(s, "KEYWORD ACTIONS");

  const checkIcon = await iconToBase64Png(FaCheckCircle, "#27AE60", 256);
  const banIcon = await iconToBase64Png(FaBan, "#E74C3C", 256);

  // LEFT: Create
  s.addShape("rect", { x: 0.6, y: 1.0, w: 4.25, h: 4.3, fill: { color: C.white }, shadow: makeShadow() });
  s.addShape("rect", { x: 0.6, y: 1.0, w: 4.25, h: 0.05, fill: { color: C.green } });
  s.addImage({ data: checkIcon, x: 0.85, y: 1.18, w: 0.25, h: 0.25 });
  s.addText("CREATE (Exact Match)", {
    x: 1.18, y: 1.15, w: 3.5, h: 0.35, fontSize: 14, fontFace: "Trebuchet MS", color: C.green, bold: true, margin: 0,
  });
  DATA.keywordActions.create.forEach((k, i) => {
    const ky = 1.6 + i * 0.33;
    s.addShape("rect", { x: 0.8, y: ky, w: 3.85, h: 0.28, fill: { color: i % 2 === 0 ? "F0FFF4" : C.white } });
    s.addText(k.kw, { x: 0.9, y: ky, w: 2.0, h: 0.28, fontSize: 9.5, fontFace: "Calibri", color: C.dark, bold: true, valign: "middle", margin: 0 });
    s.addText(k.note, { x: 2.9, y: ky, w: 1.65, h: 0.28, fontSize: 8, fontFace: "Calibri", color: C.textLight, valign: "middle", margin: 0 });
  });

  // RIGHT: Negative
  s.addShape("rect", { x: 5.15, y: 1.0, w: 4.25, h: 4.3, fill: { color: C.white }, shadow: makeShadow() });
  s.addShape("rect", { x: 5.15, y: 1.0, w: 4.25, h: 0.05, fill: { color: C.red } });
  s.addImage({ data: banIcon, x: 5.4, y: 1.18, w: 0.25, h: 0.25 });
  s.addText("NEGATIVE IMMEDIATELY", {
    x: 5.73, y: 1.15, w: 3.5, h: 0.35, fontSize: 14, fontFace: "Trebuchet MS", color: C.red, bold: true, margin: 0,
  });
  DATA.keywordActions.negative.forEach((k, i) => {
    const ky = 1.6 + i * 0.33;
    s.addShape("rect", { x: 5.35, y: ky, w: 3.85, h: 0.28, fill: { color: i % 2 === 0 ? "FFF0F0" : C.white } });
    s.addText(k.kw, { x: 5.45, y: ky, w: 2.65, h: 0.28, fontSize: 9.5, fontFace: "Calibri", color: C.dark, bold: true, valign: "middle", margin: 0 });
    s.addText(k.spend, { x: 8.1, y: ky, w: 0.95, h: 0.28, fontSize: 9, fontFace: "Calibri", color: C.red, bold: true, align: "right", valign: "middle", margin: 0 });
  });
}

// --- Slide 9: Negative Recommendations ---
async function buildNegativesSlide(pres) {
  const { FaBan, FaMoneyBillWave } = require("react-icons/fa");
  const s = pres.addSlide();
  s.background = { color: C.offWhite };
  addTopBar(s, C.orange);

  const banIcon = await iconToBase64Png(FaBan, "#E74C3C", 256);
  s.addImage({ data: banIcon, x: 0.6, y: 0.35, w: 0.35, h: 0.35 });
  s.addText("NEGATIVE KEYWORD RECOMMENDATIONS", {
    x: 1.05, y: 0.3, w: 8.4, h: 0.5, fontSize: 22, fontFace: "Trebuchet MS", color: C.dark, bold: true, margin: 0,
  });

  const hdr = [[
    { text: "Search Term", options: { bold: true, color: C.white, fill: { color: C.dark }, fontSize: 10, fontFace: "Calibri" } },
    { text: "Spend", options: { bold: true, color: C.white, fill: { color: C.dark }, fontSize: 10, fontFace: "Calibri", align: "right" } },
    { text: "Channel", options: { bold: true, color: C.white, fill: { color: C.dark }, fontSize: 10, fontFace: "Calibri", align: "center" } },
    { text: "Reason", options: { bold: true, color: C.white, fill: { color: C.dark }, fontSize: 10, fontFace: "Calibri" } },
  ]];
  const rows = DATA.mainProductNegatives.map((r, i) => {
    const rf = { fill: { color: i % 2 === 0 ? C.white : "F8F9FA" } };
    return [
      { text: r.term, options: { ...rf, fontSize: 10, fontFace: "Calibri", color: C.dark, bold: true } },
      { text: r.spend, options: { ...rf, fontSize: 10, fontFace: "Calibri", color: C.red, bold: true, align: "right" } },
      { text: r.channel, options: { ...rf, fontSize: 10, fontFace: "Calibri", color: C.dark, align: "center" } },
      { text: r.reason, options: { ...rf, fontSize: 9, fontFace: "Calibri", color: C.textLight } },
    ];
  });
  s.addTable(hdr.concat(rows), {
    x: 0.6, y: 1.0, w: 8.8, colW: [2.3, 0.9, 0.9, 4.7], border: { pt: 0.5, color: C.lightGray }, rowH: 0.35,
  });

  // Savings callout
  const moneyIcon = await iconToBase64Png(FaMoneyBillWave, "#F39C12", 256);
  s.addShape("rect", { x: 0.6, y: 4.55, w: 8.8, h: 0.75, fill: { color: "FFF3CD" }, shadow: makeShadow() });
  s.addShape("rect", { x: 0.6, y: 4.55, w: 0.06, h: 0.75, fill: { color: C.orange } });
  s.addImage({ data: moneyIcon, x: 0.85, y: 4.72, w: 0.3, h: 0.3 });
  s.addText([
    { text: `Estimated monthly savings: ~${DATA.estimatedSavings} `, options: { bold: true, fontSize: 12 } },
    { text: "by implementing all negative keyword recommendations above.", options: { fontSize: 11 } },
  ], { x: 1.3, y: 4.6, w: 7.9, h: 0.65, fontFace: "Calibri", color: C.dark, valign: "middle", margin: 0 });
}

// --- Slide 10: Action Plan ---
function buildActionPlanSlide(pres) {
  const s = pres.addSlide();
  s.background = { color: C.dark };
  addTopBar(s, C.gold);
  s.addText("ACTION PLAN", {
    x: 0.6, y: 0.25, w: 8.8, h: 0.6, fontSize: 28, fontFace: "Trebuchet MS", color: C.white, bold: true, margin: 0,
  });

  const cols = [
    { title: "THIS WEEK", color: C.red, items: DATA.actionPlan.thisWeek },
    { title: "NEXT 2 WEEKS", color: C.orange, items: DATA.actionPlan.nextTwoWeeks },
    { title: "ONGOING", color: C.green, items: DATA.actionPlan.ongoing },
  ];
  cols.forEach((col, i) => {
    const px = 0.6 + i * 3.1;
    s.addShape("rect", { x: px, y: 1.05, w: 2.8, h: 4.2, fill: { color: "1F1F3A" } });
    s.addShape("rect", { x: px, y: 1.05, w: 2.8, h: 0.05, fill: { color: col.color } });
    s.addText(col.title, {
      x: px, y: 1.2, w: 2.8, h: 0.45, fontSize: 14, fontFace: "Trebuchet MS", color: col.color, bold: true, align: "center", valign: "middle", margin: 0,
    });
    s.addShape("line", { x: px + 0.3, y: 1.7, w: 2.2, h: 0, line: { color: "333355", width: 0.5 } });
    const bullets = col.items.map((item, j) => ({
      text: item, options: { bullet: true, breakLine: j < col.items.length - 1, fontSize: 10, color: C.white, paraSpaceAfter: 8 },
    }));
    s.addText(bullets, { x: px + 0.2, y: 1.85, w: 2.4, h: 3.2, fontFace: "Calibri", valign: "top", margin: 0 });
  });
}

// --- Slide 11: Thank You ---
function buildThankYouSlide(pres) {
  const s = pres.addSlide();
  s.background = { color: C.dark };
  addTopBar(s, C.accent);
  s.addText("THANK YOU", {
    x: 0.8, y: 1.5, w: 8.4, h: 1.0,
    fontSize: 48, fontFace: "Trebuchet MS", color: C.white, bold: true, align: "center", charSpacing: 6, margin: 0,
  });
  s.addText("Let's turn this data into profit.", {
    x: 0.8, y: 2.5, w: 8.4, h: 0.6,
    fontSize: 20, fontFace: "Calibri", color: C.gold, align: "center", italic: true, margin: 0,
  });
  s.addShape("line", { x: 3.5, y: 3.3, w: 3, h: 0, line: { color: "333355", width: 1 } });
  s.addText("Sophie Society  |  Amazon PPC Management", {
    x: 0.8, y: 3.6, w: 8.4, h: 0.4, fontSize: 14, fontFace: "Calibri", color: C.medGray, align: "center", margin: 0,
  });
  s.addText("Powered by Shurq Analytics", {
    x: 0.8, y: 4.0, w: 8.4, h: 0.4, fontSize: 12, fontFace: "Calibri", color: C.medGray, align: "center", margin: 0,
  });
}

// ============================================================
// MAIN
// ============================================================
async function main() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_16x9";
  pres.author = "Sophie Society / Shurq";
  pres.title = `${DATA.accountName} - PPC Performance Audit`;

  buildTitleSlide(pres);
  await buildSnapshotSlide(pres);
  await buildProductComparisonSlide(pres);
  buildAdBudgetSlide(pres);
  await buildTopTermsSlide(pres);
  await buildNewKeywordsSlide(pres);
  buildProblemSlide(pres);
  await buildKeywordActionsSlide(pres);
  await buildNegativesSlide(pres);
  buildActionPlanSlide(pres);
  buildThankYouSlide(pres);

  const fileName = DATA.accountName.toLowerCase().replace(/\s+/g, "_") + "_audit.pptx";
  await pres.writeFile({ fileName: `/home/claude/${fileName}` });
  console.log(`✅ Created: ${fileName}`);
}

main().catch(console.error);
