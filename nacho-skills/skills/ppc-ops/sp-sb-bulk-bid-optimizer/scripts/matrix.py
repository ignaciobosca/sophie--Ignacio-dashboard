"""Exhaustive operator-run matrix against a real bulk.

For every strategy (and every CPC-Managed mode) x every product scope: score, render, build both
xlsx routes, drive a real browser session, download the files the operator would actually get, and
cross-check the three output routes against each other.
"""
import asyncio, json, os, subprocess, sys, pathlib, openpyxl
from playwright.async_api import async_playwright

BULK = "moonleaf_bulk.xlsx"
OUT = pathlib.Path("mx"); OUT.mkdir(exist_ok=True)
ENV = dict(os.environ, SOPHIE_RUN_TS="2026-08-28T22:00:00")
PARAMS = ["--target-acos", "45", "--min-cpc", "0.50", "--max-cpc", "3.50",
          "--brand-terms", "moonleaf, moonleaf matcha", "--currency-symbol", "$",
          "--window-days", "30"]
TABS = ["bids", "pauses", "placements", "budgets", "negations",
        "sbbids", "sbpauses", "sbplacements", "sbnegations", "method"]

COMBOS = []
for strat in ("profit_first", "balanced", "launch", "ranking"):
    COMBOS.append((strat, None, "both"))
for mode in ("daily", "weekly", "monthly"):
    COMBOS.append(("cpc_managed", mode, "both"))
COMBOS += [("balanced", None, "sp"), ("balanced", None, "sb"),
           ("launch", None, "sb"), ("ranking", None, "sp")]

problems = []
def flag(tag, msg):
    problems.append((tag, msg))

def sheet_rows(path):
    wb = openpyxl.load_workbook(path); out = {}
    for sh in wb.sheetnames:
        ws = wb[sh]; hdr = [str(c.value).lower().strip() if c.value else "" for c in ws[1]]
        col = lambda n: hdr.index(n) if n in hdr else None
        ei, bi, si, pci, pli = col("entity"), col("bid"), col("state"), col("percentage"), col("placement")
        kid, ptid = col("keyword id"), col("product targeting id")
        for r in range(2, ws.max_row + 1):
            g = lambda i: (ws.cell(r, i + 1).value if i is not None else None)
            key = (sh, str(g(ei)).lower(), str(g(kid) or g(ptid) or ""), str(g(pli) or ""))
            out[key] = {"bid": g(bi), "state": g(si), "pct": g(pci), "entity": g(ei)}
    return out

async def run(pg, strat, mode, products):
    tag = f"{strat}{'/'+mode if mode else ''}:{products}"
    stem = f"{strat}_{mode or 'x'}_{products}"
    jf = OUT / f"{stem}.json"
    cmd = [sys.executable, "scorer.py", "--input", BULK, "--strategy", strat,
           "--products", products, *PARAMS, "--output-json", str(jf)]
    if mode: cmd += ["--felix-mode", mode]
    p = subprocess.run(cmd, capture_output=True, text=True, env=ENV)
    if p.returncode != 0:
        flag(tag, f"scorer exited {p.returncode}: {p.stderr.strip()[-160:]}"); return tag, None
    doc = json.loads(jf.read_text())
    if "error" in doc:
        return tag, {"skipped": doc.get("message", doc["error"])}

    # determinism
    jf2 = OUT / f"{stem}_2.json"
    subprocess.run([c if c != str(jf) else str(jf2) for c in cmd], capture_output=True, env=ENV)
    if jf.read_text() != jf2.read_text():
        flag(tag, "scorer is not deterministic across identical runs")

    dash = OUT / f"{stem}.html"
    r = subprocess.run([sys.executable, "renderer.py", "--results", str(jf), "--source", BULK,
                        "--input", BULK, "--output", str(dash)], capture_output=True, text=True, env=ENV)
    if not dash.exists():
        flag(tag, f"renderer produced nothing: {r.stderr.strip()[-160:]}"); return tag, None

    pyx = OUT / f"{stem}_py.xlsx"; pyr = OUT / f"{stem}_py_rev.xlsx"
    a = subprocess.run([sys.executable, "applier.py", "--input", BULK, "--results", str(jf),
                        "--upload-xlsx", str(pyx), "--reverse-xlsx", str(pyr)],
                       capture_output=True, text=True, env=ENV)
    if a.returncode != 0:
        flag(tag, f"applier exited {a.returncode}: {a.stderr.strip()[-160:]}")

    # ---- browser session ----
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:120]))
    await pg.goto(dash.resolve().as_uri()); await pg.wait_for_timeout(250)
    ov = await pg.evaluate("()=>[...document.querySelectorAll('*')].filter(e=>e.scrollWidth>e.clientWidth+2&&e.clientWidth>0&&!e.classList.contains('table-scroll')).length")
    if ov: flag(tag, f"{ov} element(s) overflow horizontally")
    # Iterate the tabs THIS build renders. A fixed list stops unlocking the gate the moment a
    # new tab ships, which is exactly what happened when v4.0 added the low-data tabs.
    present = await pg.evaluate("()=>[...document.querySelectorAll('.tab-btn')].map(b=>b.dataset.tab)")
    for t in present:
        await pg.click(f".tab-btn[data-tab='{t}']"); await pg.wait_for_timeout(40)
    gate = await pg.evaluate("()=>document.getElementById('btn-forward').disabled")
    if gate: flag(tag, "download gate stayed locked after visiting every tab")
    await pg.click(".tab-btn[data-tab='summary']"); await pg.wait_for_timeout(80)

    nrows = await pg.evaluate("()=>sheetsFor(false).reduce((n,s)=>n+s.rows.length,0)")
    brx = bjs = None
    if nrows:
        async with pg.expect_download() as d1: await pg.click("#btn-forward")
        brx = OUT / f"{stem}_browser.xlsx"; await (await d1.value).save_as(brx)
        try:
            async with pg.expect_download() as d2: await pg.click("#btn-approved-json")
            bjs = OUT / f"{stem}_approved.json"; await (await d2.value).save_as(bjs)
        except Exception:
            bjs = None   # nothing pushable is legitimate (e.g. a placements-only run)
    if errs: flag(tag, f"JS error(s): {errs[:2]}")

    # ---- three-route cross-check ----
    if brx and pyx.exists():
        P, B = sheet_rows(pyx), sheet_rows(brx)
        if set(P) - set(B) or set(B) - set(P):
            flag(tag, f"row sets differ: py-only {len(set(P)-set(B))}, browser-only {len(set(B)-set(P))}")
        diff = [k for k in set(P) & set(B)
                if (str(P[k]["bid"]), str(P[k]["state"]), str(P[k]["pct"])) !=
                   (str(B[k]["bid"]), str(B[k]["state"]), str(B[k]["pct"]))]
        if diff:
            k = diff[0]
            flag(tag, f"{len(diff)} row(s) differ between routes, e.g. {k[2] or k[3]}: "
                      f"py={P[k]['bid']}/{P[k]['state']} browser={B[k]['bid']}/{B[k]['state']}")
        for (sh, ent, _, _), v in B.items():
            if ent.startswith("bidding"):
                want = "Bidding Adjustment by Placement" if "sponsored products" not in sh.lower() else "Bidding Adjustment"
                if v["entity"] != want:
                    flag(tag, f"placement Entity on '{sh}' is {v['entity']!r}, Amazon uses {want!r}")
    if bjs and brx:
        d = json.loads(bjs.read_text()); B = sheet_rows(brx)
        xb = {(k[0], k[2]): v["bid"] for k, v in B.items()
              if v["bid"] not in (None, "") and k[1] in ("keyword", "product targeting")}
        for arr, hint in ((d.get("target_bids", []), "sponsored products"), (d.get("sb_target_bids", []), "sb")):
            for x in arr:
                hit = [vv for (sh, tid), vv in xb.items()
                       if tid == str(x["targetId"]) and hint.split()[0] in sh.lower()]
                if hit and abs(float(hit[0]) - x["final_bid"]) > 1e-9:
                    flag(tag, f"push bid {x['final_bid']} != xlsx bid {hit[0]} for {x.get('text') or x['targetId']}")
                    break
    c = doc["counts"]
    return tag, {"sp_bids": c.get("bid_changes"), "sp_pause": c.get("pauses"),
                 "sp_pl": c.get("placement_changes"), "budg": c.get("budget_changes"),
                 "neg": c.get("negations"), "sb_bids": c.get("sb_bid_changes"),
                 "sb_pause": c.get("sb_pauses"), "sb_pl": c.get("sb_placement_changes"),
                 "sb_neg": c.get("sb_negations"), "rows": nrows}

async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch()
        ctx = await b.new_context(viewport={"width": 1440, "height": 1000}, accept_downloads=True)
        pg = await ctx.new_page()
        print(f"{'combination':<28} {'SPbid':>5} {'SPpau':>5} {'SPpl':>4} {'bud':>3} {'neg':>3} "
              f"{'SBbid':>5} {'SBpau':>5} {'SBpl':>4} {'SBneg':>5} {'rows':>5}")
        for strat, mode, prod in COMBOS:
            tag, res = await run(pg, strat, mode, prod)
            if res is None:
                print(f"{tag:<28}  FAILED")
            elif "skipped" in res:
                print(f"{tag:<28}  (no rows: {res['skipped'][:44]})")
            else:
                print(f"{tag:<28} " + " ".join(f"{str(res[k]):>{w}}" for k, w in
                      [("sp_bids",5),("sp_pause",5),("sp_pl",4),("budg",3),("neg",3),
                       ("sb_bids",5),("sb_pause",5),("sb_pl",4),("sb_neg",5),("rows",5)]))
        await b.close()
    print()
    if problems:
        print(f"!! {len(problems)} PROBLEM(S):")
        for t, m in problems: print(f"   [{t}] {m}")
        sys.exit(1)
    print("no problems found across the matrix")

asyncio.run(main())
