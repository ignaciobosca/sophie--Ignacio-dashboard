#!/usr/bin/env python3
"""
analyze.py - deterministic data engine for the amazon-title-optimizer skill.
Pure stdlib, no network. Does the math so the numbers are exact and identical
for every teammate and every run:

  - aggregates the STR (across campaigns) and SQP (across duplicate queries),
    each separately (never merged)
  - computes per-query market CVR and ASIN CVR, and the click-weighted
    aggregate benchmark (preserve / balanced / flexible verdict)
  - picks the volume-led anchor, the high-CVR anchor, and the two-anchor hedge
  - finds trending-up terms (SQP period-over-period, or POE if supplied)

The SEMANTIC judgment (which queries are on-product, dropping competitor-brand
terms, marking is_branded) is done UPSTREAM by the model when it assembles the
input JSON. This script only does the numeric work.

Output keys are aligned to build_pptx.py's input: merge this file's output
with `existing`, `run_date`, and the 3 generated `bundles` to form *_final.json.

Usage:
  python analyze.py --in outputs/<ASIN>_raw.json --out outputs/<ASIN>_analysis.json

Input JSON (model assembles from the MCP pulls):
{
  "asin": "B0XXXX", "brand": "...", "category": "Home & Kitchen",
  "window_days": 90, "include_brand_in_title": false,
  "options": {"hedge_relative_gap": 0.25, "outperform_margin_pts": 2.0},
  "str_rows": [{"search_term":"...","campaign":"...","impressions":0,"clicks":0,"spend":0.0,"orders":0}],
  "sqp_rows": [{"search_query":"...","search_query_volume":0,"prev_search_query_volume":0,
                "market_impressions":0,"market_clicks":0,"market_purchases":0,
                "asin_impressions":0,"asin_clicks":0,"asin_purchases":0,"is_branded":false}],
  "poe_rows": [{"term":"...","trend_180d":0.0,"search_volume":0}]
}
Only include SQP queries you judge on-product (drop competitor-brand / irrelevant);
mark branded ones with is_branded=true.
"""

import argparse
import json
import re
import sys

DEFAULT_HEDGE_RELATIVE_GAP = 0.25       # >25% relatively below market CVR -> hedge
DEFAULT_OUTPERFORM_MARGIN_PTS = 2.0     # >= +2 CVR points over market -> preserve
MIN_ANCHOR_CLICKS = 10                  # visibility anchor must have a real ASIN sample
MEDIA_TOKENS = ["book", "music", "video", "dvd", "blu-ray", "blu ray", "cd", "vinyl", "software"]


def _norm(s):
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def _safe_div(num, den):
    return (num / den) if den else 0.0


def is_media_category(category_str):
    cat = (category_str or "").lower()
    return any(tok in cat for tok in MEDIA_TOKENS)


def aggregate_str(rows):
    """Combine duplicate search terms across campaigns; recompute overall KPIs."""
    groups = {}
    for r in rows or []:
        key = _norm(r.get("search_term"))
        if not key:
            continue
        g = groups.setdefault(key, {
            "search_term": (r.get("search_term") or "").strip(),
            "impressions": 0, "clicks": 0, "spend": 0.0, "orders": 0, "campaigns": 0,
        })
        g["impressions"] += int(r.get("impressions") or 0)
        g["clicks"] += int(r.get("clicks") or 0)
        g["spend"] += float(r.get("spend") or 0.0)
        g["orders"] += int(r.get("orders") or 0)
        g["campaigns"] += 1
    for g in groups.values():
        g["ctr"] = round(_safe_div(g["clicks"], g["impressions"]), 4)
        g["cvr"] = round(_safe_div(g["orders"], g["clicks"]), 4)
    return sorted(groups.values(), key=lambda x: (x["orders"], x["cvr"]), reverse=True)


def aggregate_sqp(rows):
    """Combine duplicate search queries; recompute market + ASIN CVR."""
    groups = {}
    for r in rows or []:
        key = _norm(r.get("search_query"))
        if not key:
            continue
        g = groups.setdefault(key, {
            "search_query": (r.get("search_query") or "").strip(),
            "search_query_volume": 0, "prev_search_query_volume": 0,
            "market_impressions": 0, "market_clicks": 0, "market_purchases": 0,
            "asin_impressions": 0, "asin_clicks": 0, "asin_purchases": 0,
            "is_branded": False,
        })
        g["search_query_volume"] += int(r.get("search_query_volume") or 0)
        g["prev_search_query_volume"] += int(r.get("prev_search_query_volume") or 0)
        for f in ("market_impressions", "market_clicks", "market_purchases",
                  "asin_impressions", "asin_clicks", "asin_purchases"):
            g[f] += int(r.get(f) or 0)
        g["is_branded"] = g["is_branded"] or bool(r.get("is_branded"))
    for g in groups.values():
        g["market_cvr"] = round(_safe_div(g["market_purchases"], g["market_clicks"]), 4)
        g["asin_cvr"] = round(_safe_div(g["asin_purchases"], g["asin_clicks"]), 4)
        g["asin_ctr"] = round(_safe_div(g["asin_clicks"], g["asin_impressions"]), 4)
        g["market_ctr"] = round(_safe_div(g["market_clicks"], g["market_impressions"]), 4)
        prev = g["prev_search_query_volume"]
        g["volume_growth"] = round(_safe_div(g["search_query_volume"] - prev, prev), 4) if prev else None
    return sorted(groups.values(), key=lambda x: x["search_query_volume"], reverse=True)


def run_analyze(data):
    opts = data.get("options") or {}
    hedge_gap = float(opts.get("hedge_relative_gap", DEFAULT_HEDGE_RELATIVE_GAP))
    margin = float(opts.get("outperform_margin_pts", DEFAULT_OUTPERFORM_MARGIN_PTS)) / 100.0

    str_agg = aggregate_str(data.get("str_rows"))
    sqp_agg = aggregate_sqp(data.get("sqp_rows"))

    # Numeric relevance: ASIN had >=1 purchase. (Semantic relevance handled upstream.)
    relevant = [q for q in sqp_agg if q["asin_purchases"] >= 1]

    sum_asin_clicks = sum(q["asin_clicks"] for q in relevant)
    sum_asin_purch = sum(q["asin_purchases"] for q in relevant)
    sum_mkt_clicks = sum(q["market_clicks"] for q in relevant)
    sum_mkt_purch = sum(q["market_purchases"] for q in relevant)
    w_asin_cvr = _safe_div(sum_asin_purch, sum_asin_clicks)
    w_mkt_cvr = _safe_div(sum_mkt_purch, sum_mkt_clicks)

    str_clicks = sum(t["clicks"] for t in str_agg)
    str_orders = sum(t["orders"] for t in str_agg)
    str_cvr = _safe_div(str_orders, str_clicks)

    delta = w_asin_cvr - w_mkt_cvr
    if delta >= margin:
        verdict = "preserve"
    elif delta >= 0:
        verdict = "balanced"
    else:
        verdict = "flexible"

    # Volume-led, but require a real ASIN sample so we don't anchor on a
    # high-volume query the ASIN has barely touched (statistical noise).
    qualified = [q for q in relevant if q["asin_clicks"] >= MIN_ANCHOR_CLICKS]
    visibility_anchor = (qualified[0] if qualified
                         else (relevant[0] if relevant else (sqp_agg[0] if sqp_agg else None)))
    strengths = sorted(
        [q for q in relevant if q["asin_cvr"] >= q["market_cvr"] and q["market_cvr"] > 0],
        key=lambda x: x["search_query_volume"], reverse=True)
    cvr_candidates = sorted(
        [q for q in relevant if q["asin_clicks"] >= 5],
        key=lambda x: x["asin_cvr"], reverse=True)
    high_cvr_anchor = cvr_candidates[0] if cvr_candidates else None

    # CTR hedge: term that clicks well (high ASIN CTR) but whose CVR has room to
    # improve (below its market rate) — AND has enough search volume to be worth
    # leading the title on (visibility). CVR is the secondary metric here.
    # Exclude only the low-volume tail (bottom quartile) so the pick still has real
    # visibility, then lead with the HIGHEST CTR among the rest — CTR is what makes
    # this the CTR hedge; volume is a visibility floor, not the ranking key.
    rel_vols = sorted(q["search_query_volume"] for q in relevant)
    vol_floor = rel_vols[len(rel_vols) // 4] if rel_vols else 0  # ~25th percentile

    def _ctr_pool(min_vol):
        return sorted(
            [q for q in relevant if q["asin_impressions"] >= 50 and q["market_cvr"] > 0
             and q["asin_cvr"] < q["market_cvr"] and q["search_query_volume"] >= min_vol],
            key=lambda x: x.get("asin_ctr") or 0, reverse=True)

    ctr_candidates = _ctr_pool(vol_floor) or _ctr_pool(0)  # fall back if the floor empties it
    ctr_hedge_anchor = ctr_candidates[0] if ctr_candidates else None

    hedge = False
    if visibility_anchor and visibility_anchor["market_cvr"] > 0:
        gap = (visibility_anchor["market_cvr"] - visibility_anchor["asin_cvr"]) / visibility_anchor["market_cvr"]
        hedge = gap > hedge_gap

    poe = data.get("poe_rows") or []
    if poe:
        trending = sorted(
            [{"term": p.get("term"), "growth": p.get("trend_180d"), "volume": p.get("search_volume")}
             for p in poe if (p.get("trend_180d") or 0) > 0],
            key=lambda x: (x["growth"] or 0, x["volume"] or 0), reverse=True)[:10]
        trend_source = "POE_180d"
    else:
        trending = sorted(
            [{"term": q["search_query"], "growth": q["volume_growth"], "volume": q["search_query_volume"]}
             for q in sqp_agg if (q["volume_growth"] or 0) > 0.10],
            key=lambda x: (x["growth"] or 0, x["volume"] or 0), reverse=True)[:10]
        trend_source = "SQP_period_over_period"

    return {
        "asin": data.get("asin"),
        "brand": data.get("brand"),
        "category": data.get("category"),
        "is_media": is_media_category(data.get("category")),
        "window_days": data.get("window_days"),
        "include_brand_in_title": bool(data.get("include_brand_in_title")),
        "benchmark": {
            "weighted_asin_cvr": round(w_asin_cvr, 4),
            "weighted_market_cvr": round(w_mkt_cvr, 4),
            "delta_points": round(delta * 100, 2),
            "str_overall_cvr": round(str_cvr, 4),
            "verdict": verdict,
            "verdict_note": {
                "preserve": "ASIN beats market by >= margin; keep content, change for format.",
                "balanced": "ASIN at/slightly above market; moderate edits allowed.",
                "flexible": "ASIN below market; aggressive rewrites toward better terms.",
            }[verdict],
            "relevant_query_count": len(relevant),
        },
        "anchor": {
            "visibility_anchor": visibility_anchor,
            "high_cvr_anchor": high_cvr_anchor,
            "ctr_hedge_anchor": ctr_hedge_anchor,
            "two_anchor_hedge": hedge,
            "strength_terms": strengths[:10],
        },
        "trending": {"source": trend_source, "terms": trending},
        "relevant_queries": relevant[:25],
        "str_top_terms": str_agg[:15],
        "branded_queries": [q["search_query"] for q in sqp_agg if q["is_branded"]],
    }


def main():
    ap = argparse.ArgumentParser(description="amazon-title-optimizer deterministic analysis engine")
    ap.add_argument("--in", dest="infile", required=True, help="raw.json")
    ap.add_argument("--out", required=True, help="analysis.json")
    args = ap.parse_args()

    with open(args.infile, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    result = run_analyze(data)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, ensure_ascii=False)

    bm = result["benchmark"]
    print(f"[analyze.py] -> {args.out}")
    print(f"  verdict={bm['verdict']}  ASIN CVR {bm['weighted_asin_cvr']*100:.1f}% vs "
          f"market {bm['weighted_market_cvr']*100:.1f}% (delta {bm['delta_points']} pts)  "
          f"relevant={bm['relevant_query_count']}  hedge={result['anchor']['two_anchor_hedge']}")


if __name__ == "__main__":
    sys.exit(main())
