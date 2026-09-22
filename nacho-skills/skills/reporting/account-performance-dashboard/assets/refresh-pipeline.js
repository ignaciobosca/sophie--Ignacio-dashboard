/* =============================================================================
   Sophie Society — Account Performance Dashboard — IN-PAGE LIVE REFRESH PIPELINE
   =============================================================================
   Ported VERBATIM from the verified Kinzie Direct Cowork build, then made
   BRAND-AGNOSTIC: only the four __APD_*__ tokens below are stamped per store at
   build time (SKILL Step 3.4). Seed carries 6 months. On open we render the cache
   instantly, then re-pull only the trailing 30 days, merge those months over the
   cache, save, and reload (clean one-time render — no Chart.js re-init pitfalls).

   Two additive improvements over the Kinzie build (both supported by the template
   splice, both no-ops for a single-marketplace US store):
     • preserves live in-dashboard COGS / manual-backfill edits across the reload
       (reads window.__APD_USER__, which renderAll exposes);
     • injects marketplace_id (MKT) to scope every call to ONE marketplace.

   MKT is REQUIRED for any store spanning more than one currency — not merely for a
   "non-US" store. Omitting marketplace_id does not mean "US", it means every
   marketplace; and get_ads_summary now nulls all money when the loaded profiles
   span currencies. A US-primary store that also sells CA/MX is multi-currency and
   must be stamped. Left unstamped it used to render $0 ad spend, because the old
   `(ov.cost || 0)` read turned "we cannot say" into "you spent nothing".

   Runtime contract (the one thing to verify on first live open):
     window.cowork.callMcpTool(PREFIX + tool, args) returns a payload in
     r.structuredContent (or JSON.parse(r.content[0].text)); r.isError on failure.
   ========================================================================== */
(function(){
  "use strict";
  var PREFIX = "__APD_PREFIX__";          // MCP tool-name prefix, e.g. "mcp__<uuid>__"
  var KEY = "__APD_LSKEY__";              // localStorage key; MUST equal the loader's K
  var STORE = "__APD_STORE__";           // Amazon seller_id
  var MARKETPLACE = "__APD_MARKETPLACE__"; // marketplace_id for a non-US store; token/empty => US default (omit)
  var FREEZE_DAYS = 30;
  var REFRESH_TTL_MS = 60 * 60 * 1000;

  // Treat an unreplaced token or empty string as "US default -> omit marketplace_id".
  var MKT = (MARKETPLACE && MARKETPLACE.indexOf("__APD_") !== 0) ? MARKETPLACE : "";
  function args0(extra){ var a = { store: STORE }; if (MKT) a.marketplace_id = MKT; if (extra) Object.assign(a, extra); return a; }

  function log(){ try { console.log.apply(console, ["[APD]"].concat([].slice.call(arguments))); } catch(e){} }
  function pad(n){ return (n < 10 ? "0" : "") + n; }
  function iso(d){ return d.getUTCFullYear() + "-" + pad(d.getUTCMonth() + 1) + "-" + pad(d.getUTCDate()); }
  function parse(s){ var p = s.split("-"); return new Date(Date.UTC(+p[0], +p[1] - 1, +p[2])); }
  function addDays(s, n){ var d = parse(s); d.setUTCDate(d.getUTCDate() + n); return iso(d); }
  function daysDiff(a, b){ return Math.round((parse(b) - parse(a)) / 86400000); }
  function midpoint(a, b){ return addDays(a, Math.floor(daysDiff(a, b) / 2)); }
  function mkey(s){ return s.slice(0, 7); }
  var MSHORT = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
  var MLONG = ["January","February","March","April","May","June","July","August","September","October","November","December"];
  function shortLabel(k){ var p = k.split("-"); return MSHORT[+p[1] - 1] + " " + p[0].slice(2); }
  function fullLabel(k){ var p = k.split("-"); return MLONG[+p[1] - 1] + " " + p[0]; }
  function shortRange(k){ var p = k.split("-"); return MSHORT[+p[1] - 1] + " " + p[0]; }

  function loadCache(){ try { return JSON.parse(localStorage.getItem(KEY)); } catch(e){ return null; } }
  function saveCache(b){ try { localStorage.setItem(KEY, JSON.stringify(b)); return true; } catch(e){ log("save failed", e); return false; } }

  function isCapError(msg){ return /max is|exceed|files|50000|too many|rows/i.test(msg || ""); }

  async function call(tool, args){
    if (!(window.cowork && window.cowork.callMcpTool)) throw new Error("cowork.callMcpTool unavailable");
    var r = await window.cowork.callMcpTool(PREFIX + tool, args);
    if (r && r.isError) {
      var em = (r.content && r.content[0] && r.content[0].text) || "error";
      throw new Error(tool + ": " + em);
    }
    var d = r ? r.structuredContent : null;
    if (d == null && r && r.content && r.content[0] && r.content[0].text) d = JSON.parse(r.content[0].text);
    if (d == null) throw new Error(tool + ": empty response");
    return d;
  }

  async function pullSplit(tool, args, s, e, mergeFn){
    try {
      var a = Object.assign({}, args, { start_date: s, end_date: e });
      return await call(tool, a);
    } catch(err){
      var msg = (err && err.message) || "";
      if (daysDiff(s, e) >= 2 && isCapError(msg)) {
        var mid = midpoint(s, e);
        var left = await pullSplit(tool, args, s, mid, mergeFn);
        var right = await pullSplit(tool, args, addDays(mid, 1), e, mergeFn);
        return mergeFn(left, right);
      }
      throw err;
    }
  }

  function rowsOf(x){ return (x && x.data && x.data.rows) || []; }

  /* Money keys vs count keys. get_ads_summary NULLS every money field when the loaded
     profiles span currencies (the real figures move to by_currency). Counts and
     count-ratios carry no currency and stay populated regardless.
     Null must propagate: `(x || 0) + (y || 0)` turns "we cannot say" into "you spent
     nothing" — the exact class of lie this whole change exists to kill. */
  var ADS_MONEY_KEYS = ["cost", "sales"];
  var ADS_COUNT_KEYS = ["impressions", "clicks", "orders", "units"];
  function addMoney(x, y){ return (x == null || y == null) ? null : x + y; }

  function mAdsOverall(a, b){
    var out = { data: { overall: {}, by_type: { sp: {}, sb: {}, sd: {} } } };
    var oa = (a.data && a.data.overall) || {};
    var ob = (b.data && b.data.overall) || {};
    ADS_COUNT_KEYS.forEach(function(k){ out.data.overall[k] = (oa[k] || 0) + (ob[k] || 0); });
    ADS_MONEY_KEYS.forEach(function(k){ out.data.overall[k] = addMoney(oa[k], ob[k]); });
    ["sp", "sb", "sd"].forEach(function(t){
      var xa = (a.data && a.data.by_type && a.data.by_type[t]) || {};
      var xb = (b.data && b.data.by_type && b.data.by_type[t]) || {};
      ADS_COUNT_KEYS.forEach(function(k){ out.data.by_type[t][k] = (xa[k] || 0) + (xb[k] || 0); });
      ADS_MONEY_KEYS.forEach(function(k){ out.data.by_type[t][k] = addMoney(xa[k], xb[k]); });
    });
    // Carried so the caller can name the currencies it refused to blend.
    out.data.by_currency = (a.data && a.data.by_currency) || (b.data && b.data.by_currency) || [];
    return out;
  }

  function mPpc(a, b){
    var map = {};
    function add(x){
      rowsOf(x).forEach(function(r){
        var id = (r.key && r.key.advertisedAsin) || r.advertisedAsin;
        if (!id) return;
        var t = map[id] || (map[id] = { spend: 0, sales: 0, impressions: 0, clicks: 0, purchases: 0, units: 0 });
        ["spend", "sales", "impressions", "clicks", "purchases", "units"].forEach(function(k){ t[k] += (r[k] || 0); });
      });
    }
    add(a); add(b);
    var out = [];
    Object.keys(map).forEach(function(id){
      var v = map[id];
      out.push({ key: { advertisedAsin: id }, spend: v.spend, sales: v.sales, impressions: v.impressions, clicks: v.clicks, purchases: v.purchases, units: v.units });
    });
    return { data: { rows: out } };
  }

  function mSTDate(a, b){ return { data: { rows: rowsOf(a).concat(rowsOf(b)) } }; }

  function mSTAsin(a, b){
    var map = {};
    function add(x){
      rowsOf(x).forEach(function(r){
        var t = map[r.asin] || (map[r.asin] = { ordered_product_sales: 0, units_ordered: 0 });
        t.ordered_product_sales += (r.ordered_product_sales || 0);
        t.units_ordered += (r.units_ordered || 0);
      });
    }
    add(a); add(b);
    var out = [];
    Object.keys(map).forEach(function(id){ out.push({ asin: id, ordered_product_sales: map[id].ordered_product_sales, units_ordered: map[id].units_ordered }); });
    return { data: { rows: out } };
  }

  function usdRow(oc){
    var bc = (oc && oc.data && oc.data.by_currency) || [];
    for (var i = 0; i < bc.length; i++) { if (bc[i].currency === "USD") return bc[i]; }
    return {};
  }
  function mOrders(a, b){
    var x = usdRow(a), y = usdRow(b);
    return { data: { by_currency: [ { currency: "USD", order_count: (x.order_count || 0) + (y.order_count || 0), units_sold: (x.units_sold || 0) + (y.units_sold || 0), revenue: (x.revenue || 0) + (y.revenue || 0) } ] } };
  }

  function lastDayOfMonth(key){
    var d = parse(key + "-01");
    d.setUTCMonth(d.getUTCMonth() + 1);
    d.setUTCDate(0);
    return iso(d);
  }

  async function pullMonth(key, endCap){
    var s = key + "-01";
    var e = lastDayOfMonth(key);
    if (e > endCap) e = endCap;

    var cache = window.__APD_CACHE__ || {};
    var prodList = cache.PROD || [];
    var prodAsins = prodList.map(function(p){ return p.asin; });
    var skuOf = {};
    prodList.forEach(function(p){ if (p.sku) skuOf[p.asin] = p.sku; });

    var orders = await pullSplit("get_orders_summary", args0(), s, e, mOrders);
    var ads = await pullSplit("get_ads_summary", args0({ view: "overall" }), s, e, mAdsOverall);
    var sd = await pullSplit("query_sales_traffic", args0({ view: "by_date" }), s, e, mSTDate);
    var sa = await pullSplit("query_sales_traffic", args0({ view: "by_asin", asins: prodAsins }), s, e, mSTAsin);
    var pa = await pullSplit("query_ppc", args0({ view: "product_ads", asins: prodAsins }), s, e, mPpc);
    var fin = await call("get_financial_summary", args0({ view: "full", start_date: s, end_date: e }));

    var o = usdRow(orders);
    var ov = (ads.data && ads.data.overall) || {};
    var bt = (ads.data && ads.data.by_type) || {};
    var bsp = bt.sp || {}, bsb = bt.sb || {}, bsd = bt.sd || {};

    /* Ads money is null => the store's ad profiles span currencies and this call was not
       scoped to one. This dashboard renders a single "$" and has no way to show two.
       by_currency carries no by_type (SP/SB/SD) split, so we cannot rebuild the month from
       it either — the build must stamp __APD_MARKETPLACE__ so every call is scoped.
       THROW rather than fall through: the caller keeps the previously saved month, which
       beats writing 0 and reporting "no ad spend" to a partner. */
    if (ov.cost == null) {
      var codes = ((ads.data && ads.data.by_currency) || [])
        .map(function(c){ return c.currency; }).filter(Boolean);
      throw new Error(
        "ads money is null — profiles span " +
        (codes.length ? codes.join(" + ") : "multiple currencies") +
        (MKT ? " even scoped to " + MKT : " and no marketplace_id is stamped") +
        "; rebuild the dashboard scoped to one marketplace"
      );
    }

    var mrev = 0, muni = 0;
    rowsOf(sd).forEach(function(r){ mrev += (r.ordered_product_sales || 0); muni += (r.units_ordered || 0); });

    var byMonth = (fin.data && fin.data.by_month) || [];
    var fm = {};
    for (var i = 0; i < byMonth.length; i++) { if (byMonth[i].month === key) { fm = byMonth[i]; break; } }

    var acct = {
      rev: mrev, units: muni, orders: (o.order_count || 0),
      ad: (ov.cost || 0), adSales: (ov.sales || 0), impr: (ov.impressions || 0), clicks: (ov.clicks || 0),
      sp: (bsp.cost || 0), sb: (bsb.cost || 0), sd: (bsd.cost || 0),
      spSales: (bsp.sales || 0), sbSales: (bsb.sales || 0), sdSales: (bsd.sales || 0),
      varFees: Math.abs(fm.referral_fees || 0), fbaFul: Math.abs(fm.fba_fees || 0), operating: Math.abs(fm.other_fees || 0),
      promo: Math.abs(fm.promotions || 0), refunds: Math.abs(fm.refunds || 0),
      grossSales: (fm.gross_sales || 0), gunits: (fm.units || 0), storage: 0, lowInv: 0
    };

    var salesByAsin = {};
    rowsOf(sa).forEach(function(r){ salesByAsin[r.asin] = r; });
    var adByAsin = {};
    rowsOf(pa).forEach(function(r){ var id = (r.key && r.key.advertisedAsin) || r.advertisedAsin; if (id) adByAsin[id] = r; });
    var feeBySku = {};
    ((fin.data && fin.data.by_sku_month) || []).forEach(function(r){ if (r.month === key) feeBySku[r.sku] = r; });

    var prod = {};
    prodAsins.forEach(function(a2){
      var srow = salesByAsin[a2] || {};
      var arow = adByAsin[a2] || {};
      var spend = arow.spend || 0, asales = arow.sales || 0;
      var fr = (skuOf[a2] && feeBySku[skuOf[a2]]) ? feeBySku[skuOf[a2]] : null;
      var fee = fr ? (Math.abs(fr.referral_fees || 0) + Math.abs(fr.fba_fees || 0) + Math.abs(fr.other_fees || 0)) : 0;
      prod[a2] = {
        rev: srow.ordered_product_sales || 0,
        units: srow.units_ordered || 0,
        ad: spend,
        acos: asales > 0 ? (spend / asales * 100) : 0,
        fees: fee,
        grev: fr ? (fr.gross_sales || 0) : 0,
        sunits: fr ? (fr.units || 0) : 0
      };
    });

    var finByDate = {};
    ((fin.data && fin.data.by_date) || []).forEach(function(r){
      finByDate[r.date] = { f: Math.abs(r.referral_fees || 0) + Math.abs(r.fba_fees || 0) + Math.abs(r.other_fees || 0), r: Math.abs(r.refunds || 0) };
    });
    var totRev = mrev || 1;
    var daily = [];
    rowsOf(sd).forEach(function(r){
      var share = (r.ordered_product_sales || 0) / totRev;
      var fb = finByDate[r.date] || { f: 0, r: 0 };
      daily.push([r.date, r.ordered_product_sales || 0, r.units_ordered || 0, 0, round2(fb.f), round2(acct.ad * share), round2(fb.r)]);
    });

    return { key: key, acct: acct, prod: prod, daily: daily };
  }

  function round2(n){ return Math.round((+n || 0) * 100) / 100; }

  var M_KEYS = ["rev","units","orders","ad","adSales","impr","clicks","sp","sb","sd","spSales","sbSales","sdSales","varFees","fbaFul","operating","promo","refunds","grossSales","gunits","storage","lowInv"];

  function ensureMonth(blob, key){
    if (blob.MMAP[key] !== undefined) return blob.MMAP[key];
    var i = blob.MO.length;
    blob.MO.push(shortLabel(key));
    blob.MF.push(fullLabel(key));
    blob.MMAP[key] = i;
    M_KEYS.concat(["net"]).forEach(function(k){
      if (!blob.M[k]) blob.M[k] = [];
      while (blob.M[k].length <= i) blob.M[k].push(0);
    });
    (blob.PROD || []).forEach(function(p){
      ["rev","units","ad","acos","fees","grev","sunits"].forEach(function(k){
        if (!p[k]) p[k] = [];
        while (p[k].length <= i) p[k].push(0);
      });
    });
    if (blob.SNS) {
      ["active","units","rev","oos","discount"].forEach(function(k){
        if (!blob.SNS[k]) blob.SNS[k] = [];
        while (blob.SNS[k].length <= i) blob.SNS[k].push(k === "active" ? null : 0);
      });
    }
    if (Array.isArray(blob.CAMP)) {
      blob.CAMP.forEach(function(c){
        ["spend","sales","orders","impr","clicks"].forEach(function(k){
          if (!Array.isArray(c[k])) c[k] = [];
          while (c[k].length <= i) c[k].push(0);
        });
      });
    }
    return i;
  }

  function mergeMonth(blob, rec){
    var i = ensureMonth(blob, rec.key);
    M_KEYS.forEach(function(k){ blob.M[k][i] = round2(rec.acct[k]); });
    (blob.PROD || []).forEach(function(p){
      var pm = rec.prod[p.asin] || {};
      ["rev","units","ad","acos","fees","grev","sunits"].forEach(function(k){ p[k][i] = round2(pm[k]); });
    });
    var mk = rec.key;
    var kept = (blob.DAILY || []).filter(function(row){ return String(row[0]).slice(0, 7) !== mk; });
    blob.DAILY = kept.concat(rec.daily);
    blob.DAILY.sort(function(a, b){ return a[0] < b[0] ? -1 : (a[0] > b[0] ? 1 : 0); });
  }

  async function pullSNS(startWin, endWin){
    try {
      var s = await call("get_subscribe_save", args0({ start_date: startWin, end_date: endWin }));
      if (s.data && s.data.by_month) return s;
    } catch(e){ log("SNS refresh failed, keeping saved", e.message); }
    return null;
  }

  // Campaign v3 reports are daily/rolling-window files (no clean monthly aggregate). Take each
  // campaign's cost/sales/orders/impr/clicks totals from the freshest ~14-30d report per type;
  // applyCampaigns() then reconciles them per month against the account's real SP/SB/SD monthly spend.
  async function pullCampaigns(){
    async function freshestKey(type){
      var disc = await call("discover_amazon_reports", { api_type: "ADS", seller_id: STORE, report_type_filter: "report-v3-" + type + "-campaign" });
      var prof = disc.profiles && disc.profiles[0];
      var rt = prof && prof.report_types && prof.report_types[0];
      var drs = (rt && rt.date_ranges) || [];
      var w = drs.filter(function(r){ var d = daysDiff(r.date_from, r.date_to); return d >= 13 && d <= 30; });
      w.sort(function(a, b){ return a.date_to < b.date_to ? 1 : -1; });
      return w[0] ? w[0].s3_key : null;
    }
    async function q(type, isSp){
      var key = await freshestKey(type);
      if (!key) return [];
      var metrics = [
        { field: "cost", op: "sum", alias: "cost" },
        { field: (isSp ? "sales30d" : "sales"), op: "sum", alias: "sales" },
        { field: (isSp ? "purchases30d" : "purchases"), op: "sum", alias: "orders" },
        { field: "impressions", op: "sum", alias: "impr" },
        { field: "clicks", op: "sum", alias: "clicks" }
      ];
      var r = await call("query_report", { s3_key: key, group_by: ["campaignName"], metrics: metrics, sort_by: { field: "cost", direction: "desc" }, limit: 200 });
      return (r.rows || []).map(function(x){ return { name: x.campaignName, cost: x.cost || 0, sales: x.sales || 0, orders: x.orders || 0, impr: x.impr || 0, clicks: x.clicks || 0 }; });
    }
    return { sp: await q("sp", true), sb: await q("sb", false), sd: await q("sd", false) };
  }

  var CAMP_ARR = ["spend","sales","orders","impr","clicks"];
  var TYPE_SPEND_KEY = { sp: "sp", sb: "sb", sd: "sd" };
  function campArrays(c, n){ CAMP_ARR.forEach(function(k){ if (!Array.isArray(c[k])) c[k] = []; while (c[k].length < n) c[k].push(0); }); return c; }

  // Reconcile campaign spend to the account's real per-type monthly spend (M.sp/sb/sd) for each
  // refreshed month, then distribute each campaign's reported conversions by its own spend share
  // (observed efficiency). Spend is exact vs account totals; sales/orders scale with reconciled
  // spend; feeds with no campaign-grain conversions (SD, this store's SP) stay 0 -> template "—".
  function applyCampaigns(blob, byType, monthIdxs){
    if (!Array.isArray(blob.CAMP)) blob.CAMP = [];
    var n = blob.MO.length;
    var idx = {};
    blob.CAMP.forEach(function(c){ campArrays(c, n); idx[c.type + "::" + c.name] = c; });
    function getCamp(name, type){
      var k = type + "::" + name, c = idx[k];
      if (!c){ c = campArrays({ name: name, type: type, status: "ENABLED" }, n); blob.CAMP.push(c); idx[k] = c; }
      return c;
    }
    ["sp","sb","sd"].forEach(function(type){
      var list = byType[type] || [];
      var totalCost = list.reduce(function(a, r){ return a + (r.cost || 0); }, 0);
      var present = {};
      list.forEach(function(r){ present[r.name] = 1; });
      monthIdxs.forEach(function(i){
        var acctSpend = ((blob.M[TYPE_SPEND_KEY[type]]) || [])[i] || 0;
        list.forEach(function(r){
          var share = totalCost > 0 ? (r.cost || 0) / totalCost : 0;
          var spend_i = acctSpend * share;
          var per = r.cost > 0 ? spend_i / r.cost : 0;   // reconciled-spend / report-spend for this campaign
          var c = getCamp(r.name, type);
          c.spend[i] = round2(spend_i);
          c.sales[i] = round2((r.sales || 0) * per);
          c.orders[i] = Math.round((r.orders || 0) * per);
          c.impr[i] = Math.round((r.impr || 0) * per);
          c.clicks[i] = Math.round((r.clicks || 0) * per);
        });
        blob.CAMP.forEach(function(c){   // campaigns absent from the freshest report => no recent spend this month
          if (c.type === type && !present[c.name]) CAMP_ARR.forEach(function(k){ c[k][i] = 0; });
        });
      });
    });
    if (blob.CAMP.length > 40) {   // keep bounded: top 40 by lifetime spend
      var life = function(c){ return (c.spend || []).reduce(function(x, y){ return x + (y || 0); }, 0); };
      blob.CAMP.sort(function(a, b){ return life(b) - life(a); });
      blob.CAMP = blob.CAMP.slice(0, 40);
    }
  }

  async function refresh(status){
    var blob = loadCache() || window.__APD_SEED__;
    window.__APD_CACHE__ = blob;

    // Preserve live in-dashboard edits (COGS / manual backfill) across the reload.
    try {
      var u = window.__APD_USER__;
      if (u) {
        if (Array.isArray(u.cogs)) blob.COGS = u.cogs;
        if (u.ovr && typeof u.ovr === "object") blob.OVR = u.ovr;
        if (Array.isArray(u.added)) blob.ADDED = u.added;
      }
    } catch(e){}

    var now = new Date();
    var endCap = iso(new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate() - 1)));
    var winStart = addDays(endCap, -(FREEZE_DAYS - 1));

    var months = [];
    var k = mkey(winStart), guard = 0;
    while (k <= mkey(endCap) && guard++ < 6) {
      months.push(k);
      var d = parse(k + "-01");
      d.setUTCMonth(d.getUTCMonth() + 1);
      k = mkey(iso(d));
    }
    log("refresh window", winStart, "->", endCap, "months", months);

    var done = 0;
    for (var mi = 0; mi < months.length; mi++) {
      status("Refreshing " + fullLabel(months[mi]) + " (" + (mi + 1) + "/" + months.length + ")…");
      try {
        var rec = await pullMonth(months[mi], endCap);
        var signal = (rec.acct.rev || 0) + (rec.acct.ad || 0) + (rec.acct.orders || 0);
        if (signal > 0) { mergeMonth(blob, rec); done++; }
        else { log("skip empty month (no data in window) — keeping saved", months[mi]); }
      } catch(e){ log("month " + months[mi] + " failed, keeping saved:", e.message); }
    }

    /* ROLL — true distinct order counts for the rolling Daily tiles (Today / Yesterday / Last 7 days).
       DAILY has no per-day order column, so the tiles read these instead of summing zeros.
       Windows are anchored to the last DAILY row, NOT wall-clock: the orders snapshot lags, and
       pfTileSpecs slices DAILY the same way — anchoring to "now" would silently offset the tiles.
       On any failure DELETE ROLL rather than leave a stale count: the tiles then render "—",
       which is honest. A stale order count next to fresh units is worse than no order count. */
    status("Refreshing order counts…");
    try {
      var dl = blob.DAILY || [];
      if (!dl.length) { delete blob.ROLL; }
      else {
        /* Sum order_count across EVERY currency, not just USD. An order count is unit-less —
           292 US + 98 CA + 2 MX = 392 orders is valid arithmetic. Currency mixing corrupts money,
           never counts. (usdRow is deliberately NOT used here: on a multi-marketplace store it
           would put US-only orders next to all-marketplace units.) Drop the stray UNKNOWN /
           Non-Amazon row, which carries a few $0 orders. */
        var rollOf = async function(s, e){
          var r = await call("get_orders_summary", args0({ start_date: s, end_date: e }));
          var bc = (r && r.data && r.data.by_currency) || [];
          var n = null;
          bc.forEach(function(row){
            if (!row || !row.currency || row.currency === "UNKNOWN") return;
            n = (n || 0) + (row.order_count || 0);
          });
          return n;
        };
        var dToday = dl[dl.length - 1][0];
        var dYest  = dl.length >= 2 ? dl[dl.length - 2][0] : null;
        var d7     = dl[Math.max(0, dl.length - 7)][0];
        blob.ROLL = {
          today: await rollOf(dToday, dToday),
          yest:  dYest ? await rollOf(dYest, dYest) : null,
          last7: await rollOf(d7, dToday)
        };
        log("ROLL", blob.ROLL);
      }
    } catch(e){ log("ROLL refresh failed, dropping (tiles render —):", e.message); delete blob.ROLL; }

    status("Refreshing Subscribe & Save…");
    var firstKey = Object.keys(blob.MMAP)[0];
    var snsStart = firstKey ? firstKey + "-01" : winStart;
    var sns = await pullSNS(snsStart, endCap);
    if (sns && blob.SNS) {
      var byk = {};
      ((sns.data && sns.data.by_month) || []).forEach(function(r){ byk[r.month] = r; });
      Object.keys(blob.MMAP).forEach(function(key){
        var i = blob.MMAP[key], r = byk[key];
        if (!r) return;
        blob.SNS.active[i] = (r.active_subscriptions != null) ? r.active_subscriptions : blob.SNS.active[i];
        blob.SNS.units[i] = r.shipped_subscription_units || 0;
        blob.SNS.rev[i] = r.subscription_revenue || 0;
        blob.SNS.oos[i] = r.not_delivered_oos_units || 0;
      });
      if (sns.data.lift) {
        blob.SNS.lift = { ratio: sns.data.lift.lift_ratio, subAvg: sns.data.lift.subscriber_avg_revenue, nonSubAvg: sns.data.lift.non_subscriber_avg_revenue, window: sns.data.lift.window };
      }
    }

    status("Refreshing campaigns…");
    try {
      var byType = await pullCampaigns();
      var refIdx = months.map(function(k){ return blob.MMAP[k]; }).filter(function(i){ return i != null; });
      applyCampaigns(blob, byType, refIdx);
    } catch(e){ log("CAMP refresh failed, keeping saved", e.message); }

    var lastDay = "";
    (blob.DAILY || []).forEach(function(r){ if ((r[1] || 0) > 0 && r[0] > lastDay) lastDay = r[0]; });
    blob.meta = blob.meta || {};
    blob.meta.dataThrough = lastDay || blob.meta.dataThrough;
    blob.meta.generatedAt = iso(new Date());
    var mk2 = Object.keys(blob.MMAP);
    if (mk2.length) {
      blob.meta.dateRange = shortRange(mk2[0]) + " - " + shortRange(mk2[mk2.length - 1]);
      blob.meta.dateRangeUpper = blob.meta.dateRange.toUpperCase();
    }
    blob.meta.refreshedAt = new Date().toISOString();

    saveCache(blob);
    try { sessionStorage.setItem("apd_refreshed", String(Date.now())); } catch(e){}
    status("Updated " + done + "/" + months.length + " months — reloading…");
    setTimeout(function(){ location.reload(); }, 700);
  }

  function banner(){
    var el = document.getElementById("apd-live");
    if (el) return el;
    el = document.createElement("div");
    el.id = "apd-live";
    el.style.cssText = "position:fixed;right:14px;bottom:14px;z-index:99999;background:#111;color:#fff;font:12px/1.4 -apple-system,Segoe UI,Roboto,sans-serif;padding:9px 12px;border-radius:10px;box-shadow:0 6px 24px rgba(0,0,0,.25);max-width:340px;opacity:.97";
    document.body.appendChild(el);
    return el;
  }
  function setStatus(msg, withBtn){
    var el = banner();
    el.innerHTML = "<span style='display:inline-block;width:8px;height:8px;border-radius:50%;background:#38d39f;margin-right:7px;vertical-align:middle'></span>" + msg;
    if (withBtn) {
      var b = document.createElement("button");
      b.textContent = "Refresh now";
      b.style.cssText = "margin-left:10px;background:#38d39f;border:0;color:#03231a;font-weight:600;padding:3px 9px;border-radius:7px;cursor:pointer";
      b.onclick = function(){ try { sessionStorage.removeItem("apd_refreshed"); } catch(e){} runRefresh(true); };
      el.appendChild(b);
    }
  }
  function hideSoon(){ setTimeout(function(){ var el = document.getElementById("apd-live"); if (el) el.style.display = "none"; }, 6000); }

  function timeAgo(t){
    if (!t) return "just now";
    var s = (Date.now() - t) / 1000;
    if (s < 90) return "just now";
    if (s < 5400) return Math.round(s / 60) + " min ago";
    if (s < 172800) return Math.round(s / 3600) + " h ago";
    return Math.round(s / 86400) + " d ago";
  }

  async function runRefresh(force){
    var last = 0;
    try { last = +(sessionStorage.getItem("apd_refreshed") || 0); } catch(e){}
    var cache = loadCache();
    var stamp = (cache && cache.meta && cache.meta.refreshedAt) ? Date.parse(cache.meta.refreshedAt) : 0;
    var fresh = stamp && (Date.now() - stamp < REFRESH_TTL_MS);
    if (!force && (fresh || (last && Date.now() - last < 5000))) {
      setStatus("Live • last updated " + timeAgo(stamp), true);
      hideSoon();
      return;
    }
    if (!(window.cowork && window.cowork.callMcpTool)) {
      setStatus("Snapshot mode (open in Cowork for live refresh)", false);
      hideSoon();
      return;
    }
    try {
      await refresh(function(m){ setStatus(m, false); });
    } catch(e){
      log("refresh error", e);
      setStatus("Live refresh failed — showing saved data", true);
      hideSoon();
    }
  }

  function boot(){ setTimeout(function(){ runRefresh(false); }, 900); }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();

  try { window.__APD_REFRESH__ = { run: runRefresh, store: STORE }; } catch(e){}
})();
