#!/usr/bin/env python3
"""Sophie Society MBR chart generator.

Reads a report_data.json and writes the standard Sophie-branded chart PNGs to
<json_dir>/charts/. Charts whose data is entirely zero/missing are skipped so a
thin (launch) account doesn't ship empty plots.

Usage:  python build_charts.py <path/to/report_data.json>

report_data.json → "monthly" block (all arrays same length, one entry per month):
  months     : ["Feb","Mar",...]           (short labels, chronological)
  total_rev  : [float]  total sales $
  ppc_sales  : [float]  ad-attributed sales $
  organic    : [float]  total_rev - ppc_sales (floored at 0)
  ad_spend   : [float]  ad spend $
  sessions   : [int]
  cvr        : [float]  store conversion % (e.g. 4.62)
  acos       : [float]  % (e.g. 108.8)   — 0/None where no ad sales
  tacos      : [float]  % (e.g. 65.4)
  cpc        : [float]  $ (ad months only ok; 0 tolerated)
  ctr        : [float]  % (e.g. 0.50)
report_data.json → "targets": {"acos": 50, "tacos": 25}  (percent numbers)
report_data.json → "top_products": [["Variety 7-Pack", 949.62], ...]  (name,$ desc)
"""
import json, os, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np

GREEN="#13835B"; DARK="#0D5C3F"; GOLD="#F5A623"; GRAY="#9AA0A6"
LIGHT="#CDE8DC"; GRID="#E5E5E5"; RED="#C0392B"
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":12,
                     "axes.edgecolor":"#CCCCCC","axes.linewidth":0.8,"figure.dpi":150})

def _style(ax):
    ax.grid(axis="y", color=GRID, linewidth=0.8, zorder=0); ax.set_axisbelow(True)
    for s in ("top","right"): ax.spines[s].set_visible(False)

def _nz(seq):  # any nonzero?
    return any((v or 0) for v in (seq or []))

def _money(v,_): return f"${v:,.0f}"
def _pct(v,_):   return f"{v:.0f}%"

def build(data, out):
    os.makedirs(out, exist_ok=True)
    m = data.get("monthly", {})
    months = m.get("months", [])
    made = []
    tg = data.get("targets", {}) or {}
    acos_t = tg.get("acos"); tacos_t = tg.get("tacos")

    def save(fig, name):
        p = os.path.join(out, name); fig.tight_layout()
        fig.savefig(p, bbox_inches="tight"); plt.close(fig); made.append(name)

    # 1) Total sales — PPC vs Organic (stacked)
    ppc, org, tot = m.get("ppc_sales",[]), m.get("organic",[]), m.get("total_rev",[])
    if months and _nz(tot):
        fig, ax = plt.subplots(figsize=(10,4.5))
        ax.bar(months, ppc, color=GOLD, label="PPC Sales", zorder=3)
        ax.bar(months, org, bottom=ppc, color=GREEN, label="Organic Sales", zorder=3)
        _style(ax); ax.yaxis.set_major_formatter(FuncFormatter(_money))
        top = max(tot) if tot else 1
        for i,t in enumerate(tot):
            ax.text(i, t+top*0.015, f"${t:,.0f}", ha="center", va="bottom",
                    fontsize=9.5, fontweight="bold", color=DARK)
        ax.set_ylim(0, top*1.16)
        ax.legend(frameon=False, loc="upper left", fontsize=11)
        ax.set_title("Total Sales by Month  —  PPC vs Organic", fontsize=14,
                     fontweight="bold", color=DARK, loc="left", pad=12)
        save(fig, "chart_sales.png")

    # 2) Advertising efficiency — spend vs ad-sales bars + ACOS line
    spend, acos = m.get("ad_spend",[]), m.get("acos",[])
    if months and _nz(spend):
        x = np.arange(len(months)); w = 0.4
        fig, ax = plt.subplots(figsize=(10,4.5))
        ax.bar(x-w/2, spend, w, color=GOLD, label="Ad Spend", zorder=3)
        ax.bar(x+w/2, ppc,   w, color=GREEN, label="Ad Sales", zorder=3)
        _style(ax); ax.set_xticks(x); ax.set_xticklabels(months)
        ax.yaxis.set_major_formatter(FuncFormatter(_money))
        ax.set_ylim(0, (max(spend) or 1)*1.24)
        ax2 = ax.twinx()
        ax2.plot(x, acos, marker="o", color=RED, lw=2.5, zorder=5, label="ACOS")
        if acos_t:
            ax2.axhline(acos_t, ls="--", color=GREEN, lw=1.2)
            ax2.text(0.1, acos_t*1.05, f"ACOS target {acos_t:.0f}%", fontsize=9, color=GREEN)
        cap = max([a for a in acos if a] or [100])*1.25
        ax2.set_ylim(0, max(cap, (acos_t or 0)*1.4))
        ax2.yaxis.set_major_formatter(FuncFormatter(_pct))
        for i in range(len(months)):
            if acos[i]:
                ax2.text(x[i], acos[i]+cap*0.03, f"{acos[i]:.0f}%", ha="center",
                         fontsize=8.5, color=RED, fontweight="bold")
        ax2.spines["top"].set_visible(False)
        ax.legend(frameon=False, loc="upper right", fontsize=10)
        ax.set_title("Advertising Efficiency  —  Spend vs Ad Sales & ACOS", fontsize=14,
                     fontweight="bold", color=DARK, loc="left", pad=12)
        save(fig, "chart_spend_sales.png")

    # 3) TACOS & ACOS lines with target bands
    tacos = m.get("tacos",[])
    if months and (_nz(tacos) or _nz(acos)):
        fig, ax = plt.subplots(figsize=(10,4.5))
        ax.plot(months, tacos, marker="o", color=GREEN, lw=2.5, label="TACOS", zorder=4)
        xa=[mm for mm,a in zip(months,acos) if a]; ya=[a for a in acos if a]
        if ya: ax.plot(xa, ya, marker="s", color=GOLD, lw=2.5, label="ACOS", zorder=4)
        if tacos_t: ax.axhline(tacos_t, ls="--", color=GREEN, lw=1.2, alpha=0.7)
        if acos_t:  ax.axhline(acos_t, ls="--", color=GOLD, lw=1.2, alpha=0.7)
        _style(ax); ax.yaxis.set_major_formatter(FuncFormatter(_pct))
        ax.legend(frameon=False, loc="upper left", fontsize=11)
        ax.set_title("Advertising Efficiency  —  TACOS & ACOS", fontsize=14,
                     fontweight="bold", color=DARK, loc="left", pad=12)
        save(fig, "chart_tacos_acos.png")

    # 4) Traffic & conversion — sessions + CVR
    sess, cvr = m.get("sessions",[]), m.get("cvr",[])
    if months and _nz(sess):
        fig, ax = plt.subplots(figsize=(10,4.5))
        b = ax.bar(months, sess, color=LIGHT, zorder=3)
        if b: b[-1].set_color(GREEN)
        _style(ax); ax.set_ylabel("Sessions", color=GRAY)
        ax2 = ax.twinx()
        ax2.plot(months, cvr, marker="o", color=DARK, lw=2.5, zorder=5)
        ax2.set_ylabel("Conversion Rate", color=DARK)
        ax2.yaxis.set_major_formatter(FuncFormatter(lambda v,_:f"{v:.0f}%"))
        ax2.set_ylim(0, (max(cvr) or 1)*1.35)
        for i,c in enumerate(cvr):
            ax2.text(i, c+(max(cvr) or 1)*0.03, f"{c:.1f}%", ha="center",
                     fontsize=9, color=DARK, fontweight="bold")
        ax2.spines["top"].set_visible(False)
        ax.set_title("Traffic & Conversion  —  Sessions & CVR", fontsize=14,
                     fontweight="bold", color=DARK, loc="left", pad=12)
        save(fig, "chart_sessions_cvr.png")

    # 5) CPC & CTR (ad months)
    cpc, ctr = m.get("cpc",[]), m.get("ctr",[])
    if months and _nz(cpc):
        fig, ax = plt.subplots(figsize=(10,4.5))
        b = ax.bar(months, cpc, color=LIGHT, zorder=3)
        if b: b[-1].set_color(GREEN)
        _style(ax); ax.set_ylabel("Avg CPC", color=GRAY)
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v,_:f"${v:.2f}"))
        for i,c in enumerate(cpc):
            if c: ax.text(i, c+(max(cpc) or 1)*0.02, f"${c:.2f}", ha="center",
                          fontsize=9, color=DARK, fontweight="bold")
        ax2 = ax.twinx()
        ax2.plot(months, ctr, marker="o", color=GOLD, lw=2.5)
        ax2.set_ylabel("CTR", color="#C7891A")
        ax2.yaxis.set_major_formatter(FuncFormatter(lambda v,_:f"{v:.2f}%"))
        ax2.set_ylim(0, (max(ctr) or 1)*1.4)
        ax2.spines["top"].set_visible(False)
        ax.set_title("Ad Cost Trend  —  CPC & CTR", fontsize=14, fontweight="bold",
                     color=DARK, loc="left", pad=12)
        save(fig, "chart_cpc_ctr.png")

    # 6) Top products (horizontal)
    tp = data.get("top_products", [])
    if tp:
        tp = tp[:10]
        labels = [p[0] for p in tp][::-1]; vals=[float(p[1]) for p in tp][::-1]
        fig, ax = plt.subplots(figsize=(10,4.6))
        cols=[GREEN]*len(vals)
        if cols: cols[-1]=DARK
        ax.barh(labels, vals, color=cols, zorder=3)
        ax.grid(axis="x", color=GRID, linewidth=0.8, zorder=0); ax.set_axisbelow(True)
        for s in ("top","right"): ax.spines[s].set_visible(False)
        ax.xaxis.set_major_formatter(FuncFormatter(_money))
        mx=max(vals) if vals else 1
        for i,v in enumerate(vals):
            ax.text(v+mx*0.01, i, f"${v:,.0f}", va="center", fontsize=9.5,
                    color=DARK, fontweight="bold")
        ax.set_xlim(0, mx*1.16)
        ttl = data.get("top_products_title", "Top Products by Revenue")
        ax.set_title(ttl, fontsize=13.5, fontweight="bold", color=DARK, loc="left", pad=12)
        save(fig, "chart_products.png")

    return made

def main():
    if len(sys.argv) < 2:
        print("usage: build_charts.py <report_data.json>"); sys.exit(1)
    jp = sys.argv[1]
    with open(jp) as f: data = json.load(f)
    out = os.path.join(os.path.dirname(os.path.abspath(jp)),
                       data.get("charts_dir", "charts"))
    made = build(data, out)
    print("charts:", made)

if __name__ == "__main__":
    main()
