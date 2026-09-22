#!/usr/bin/env python3
"""
mcp_to_uploads.py — bridge MCP payloads into the uploads dir (mode 4 support).

The listing itself reaches parse_inputs.py via --listing-json. Everything else
(SQP, PPC search terms, Helium 10 review insights) still arrives as FILES, because
the detector in walk_uploads() classifies by filename and the parsers read CSV/XLSX.
Without this bridge, an MCP-mode run silently loses every optional input — you get a
listing-only audit and no funnel, no review themes, no PPC evidence.

The runner saves each MCP tool result verbatim as JSON, then calls this once. Output
lands in the uploads dir under names walk_uploads() already recognizes, so the rest of
the pipeline is unchanged and source-agnostic.

Usage:
    python3 scripts/mcp_to_uploads.py \\
        --uploads /mnt/user-data/uploads \\
        --asin B0XXXXXXXX \\
        --marketplace US \\
        [--sqp /tmp/sqp.json]        # Sophie Hub get_sqp_metrics result
        [--ppc /tmp/ppc.json]        # Sophie Hub query_ppc(view='search_terms') result
        [--reviews /tmp/reviews.json]# Helium10 get_asin_review_analysis result

Each input is optional and independent; a malformed one warns and is skipped rather
than failing the run.
"""

import argparse
import io
import json
import os
import sys


def _load(path, label, warnings):
    try:
        with io.open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception as e:
        warnings.append(f"{label}: could not read {path} ({e})")
        return None


# --------------------------------------------------------------------- SQP
def write_sqp(payload, uploads, asin, marketplace, warnings):
    """Sophie Hub get_sqp_metrics -> <CC>_Search_Query_Performance.csv (flat layout).

    Accepts either a single-window result (data.rows) or a date-range result
    (data.windows[]). For a range we use data.period, which is the combined total
    across windows with shares recomputed — that is what a quarter-long SQP export
    from Seller Central looks like.
    """
    import csv

    data = (payload or {}).get("data") or {}
    rows = None
    if isinstance(data.get("period"), dict) and data["period"].get("rows"):
        rows = data["period"]["rows"]
        span = f"{len(data.get('windows', []))} windows combined"
    elif data.get("rows"):
        rows = data["rows"]
        span = "single window"
    elif data.get("windows"):
        rows = (data["windows"][-1] or {}).get("rows")
        span = "latest window"
    if not rows:
        warnings.append("SQP: no rows found in payload, skipped")
        return None

    cc = (marketplace or "US").upper()[:2]
    out = os.path.join(uploads, f"{cc}_Search_Query_Performance_{asin}.csv")

    # run_diagnostics.py buckets on the ASIN Share % columns, not the raw counts.
    # Emitting counts alone makes the whole funnel diagnostic fail with a KeyError.
    header = [
        "Search Query", "Search Query Volume",
        "Impressions: Total Count", "Impressions: ASIN Count", "Impressions: ASIN Share %",
        "Clicks: Total Count", "Clicks: ASIN Count", "Clicks: ASIN Share %",
        "Clicks: Click Rate %",
        "Cart Adds: Total Count", "Cart Adds: ASIN Count", "Cart Adds: ASIN Share %",
        "Purchases: Total Count", "Purchases: ASIN Count", "Purchases: ASIN Share %",
        "Purchases: Purchase Rate %",
    ]
    with io.open(out, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        # Row 0 is the ASIN filter metadata line the parser sniffs for the ASIN.
        w.writerow([f'"ASIN={asin}" Reporting Range={span}'])
        w.writerow(header)
        for r in rows:
            def pct(part, whole):
                # Prefer the share the API already computed; fall back to deriving it.
                return round((part or 0) / whole * 100, 4) if whole else 0.0
            w.writerow([
                r.get("search_query", ""),
                r.get("search_query_volume", 0),
                r.get("impression_count", 0),
                r.get("asin_impression_count", 0),
                round((r.get("impression_share") or 0) * 100, 4)
                    or pct(r.get("asin_impression_count"), r.get("impression_count")),
                r.get("click_count", 0),
                r.get("asin_click_count", 0),
                round((r.get("click_share") or 0) * 100, 4)
                    or pct(r.get("asin_click_count"), r.get("click_count")),
                round((r.get("click_through_rate") or 0) * 100, 4),
                r.get("cart_add_count", 0),
                r.get("asin_cart_add_count", 0),
                round((r.get("cart_add_share") or 0) * 100, 4)
                    or pct(r.get("asin_cart_add_count"), r.get("cart_add_count")),
                r.get("purchase_count", 0),
                r.get("asin_purchase_count", 0),
                round((r.get("purchase_share") or 0) * 100, 4)
                    or pct(r.get("asin_purchase_count"), r.get("purchase_count")),
                round((r.get("conversion_rate") or 0) * 100, 4),
            ])
    return out, len(rows)


# --------------------------------------------------------------------- PPC
def write_ppc(payload, uploads, asin, warnings):
    """Sophie Hub query_ppc(view='search_terms') -> Campaign-Manager-shaped CSV.

    `shared: true` rows carry FULL ad-group metrics across co_asins, not this ASIN's
    split. They are kept (dropping them would hide real spend) but flagged in a
    column so the audit can caveat them instead of quoting a shared ROAS as the
    ASIN's own.
    """
    import csv

    rows = ((payload or {}).get("data") or {}).get("rows")
    if not rows:
        warnings.append("PPC: no rows found in payload, skipped")
        return None

    # walk_uploads() detects PPC with `'search term' in filename.lower()` — SPACES.
    # An underscored name falls through to "unrecognized" and the PPC data is lost.
    out = os.path.join(uploads, f"Sponsored Products Search term report {asin}.csv")
    header = [
        "Customer Search Term", "Impressions", "Clicks", "Spend",
        "7 Day Total Sales", "7 Day Total Orders (#)", "7 Day Total Units (#)",
        "Total Advertising Cost of Sales (ACOS)", "Total Return on Advertising Spend (ROAS)",
        "Cost Per Click (CPC)", "Click-Thru Rate (CTR)",
        "Advertised ASIN", "Shared Ad Group",
    ]
    with io.open(out, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        for r in rows:
            w.writerow([
                r.get("search_term", ""), r.get("impressions", 0), r.get("clicks", 0),
                r.get("spend", 0), r.get("sales", 0), r.get("purchases", 0),
                r.get("units", 0), r.get("acos", 0), r.get("roas", 0),
                r.get("cpc", 0), r.get("ctr", 0),
                r.get("asin", asin), "YES" if r.get("shared") else "NO",
            ])
    return out, len(rows)


# ----------------------------------------------------------------- REVIEWS
def write_reviews(payload, uploads, asin, warnings):
    """Helium10 get_asin_review_analysis -> Helium_10_Review_Analysis_-_<ASIN>.xlsx.

    Rebuilds the four sheets parse_reviews() reads, with the same column order.
    """
    try:
        import openpyxl
    except ImportError:
        warnings.append("Reviews: openpyxl not installed, skipped")
        return None

    data = (payload or {}).get("data") or {}
    mentions = ((data.get("topics_mentions") or {}).get("topics")) or {}
    impact = ((data.get("topics_star_rating_impact") or {}).get("topics")) or {}
    if not mentions and not impact:
        warnings.append("Reviews: no topic data found in payload, skipped")
        return None

    def topic_rows(topics):
        out = []
        for t in topics or []:
            am = t.get("asinMetrics") or {}
            bn = ((t.get("browseNodeMetrics") or {}).get("occurrencePercentage") or {})
            subs = t.get("subtopics") or []
            # One row per subtopic preserves the granularity the audit uses; a topic
            # with no subtopics still gets a row so nothing is dropped.
            for st in (subs or [{}]):
                sm = st.get("metrics") or {}
                snips = st.get("reviewSnippets") or t.get("reviewSnippets") or []
                out.append([
                    t.get("topic", ""),
                    st.get("subtopic", ""),
                    sm.get("numberOfMentions", am.get("numberOfMentions", 0)),
                    am.get("occurrencePercentage", 0),
                    bn.get("allProducts", 0),
                    " | ".join(str(x) for x in snips[:3]),
                ])
        return out

    def impact_rows(topics):
        out = []
        for t in topics or []:
            am = t.get("asinMetrics") or {}
            bn = ((t.get("browseNodeMetrics") or {}).get("starRatingImpact") or {})
            out.append([t.get("topic", ""),
                        am.get("starRatingImpact", 0),
                        bn.get("allProducts", 0)])
        return out

    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    sheets = [
        ("Positive Topic Insights",
         ["Topic", "Subtopic", "ASIN Mentions", "ASIN %", "Category %", "Snippets"],
         topic_rows(mentions.get("positiveTopics"))),
        ("Negative Topic Insights",
         ["Topic", "Subtopic", "ASIN Mentions", "ASIN %", "Category %", "Snippets"],
         topic_rows(mentions.get("negativeTopics"))),
        ("Positive Star Rating Impact",
         ["Topic", "ASIN Impact", "Category Impact"],
         impact_rows(impact.get("positiveTopics"))),
        ("Negative Star Rating Impact",
         ["Topic", "ASIN Impact", "Category Impact"],
         impact_rows(impact.get("negativeTopics"))),
    ]
    for name, header, rows in sheets:
        ws = wb.create_sheet(name)
        ws.append(header)
        for r in rows:
            ws.append(r)

    out = os.path.join(uploads, f"Helium_10_Review_Analysis_-_{asin}.xlsx")
    wb.save(out)
    total = sum(len(r) for _, _, r in sheets)
    return out, total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--uploads", required=True)
    ap.add_argument("--asin", required=True)
    ap.add_argument("--marketplace", default="US")
    ap.add_argument("--sqp", default=None)
    ap.add_argument("--ppc", default=None)
    ap.add_argument("--reviews", default=None)
    args = ap.parse_args()

    os.makedirs(args.uploads, exist_ok=True)
    warnings, written = [], []

    if args.sqp:
        p = _load(args.sqp, "SQP", warnings)
        if p:
            r = write_sqp(p, args.uploads, args.asin, args.marketplace, warnings)
            if r:
                written.append(f"SQP           -> {os.path.basename(r[0])}  ({r[1]} queries)")
    if args.ppc:
        p = _load(args.ppc, "PPC", warnings)
        if p:
            r = write_ppc(p, args.uploads, args.asin, warnings)
            if r:
                written.append(f"PPC           -> {os.path.basename(r[0])}  ({r[1]} terms)")
    if args.reviews:
        p = _load(args.reviews, "Reviews", warnings)
        if p:
            r = write_reviews(p, args.uploads, args.asin, warnings)
            if r:
                written.append(f"Reviews       -> {os.path.basename(r[0])}  ({r[1]} rows)")

    print("mcp_to_uploads: wrote %d file(s) into %s" % (len(written), args.uploads))
    for w in written:
        print("  " + w)
    for w in warnings:
        print("  WARNING: " + w)
    if not written:
        print("  (nothing written — the audit will run listing-only)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
