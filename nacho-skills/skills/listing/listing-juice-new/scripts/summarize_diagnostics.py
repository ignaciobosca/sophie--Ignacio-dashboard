#!/usr/bin/env python3
"""
summarize_diagnostics.py — One-shot dump of everything Claude needs for semantic work.

Purpose: Replace 4-5 exploratory bash calls (inspecting listing_state, then sqp_buckets,
then reviews, then competitive, then structured_gaps...) with a single call that prints
all the load-bearing fields in a compact, Claude-readable layout.

Usage:
    python3 summarize_diagnostics.py --diagnostics /tmp/diagnostics.json [--asin B0XXXXXXXX]

If --asin is omitted, prints a summary for every ASIN in the diagnostics JSON. For
multi-ASIN runs, prefer calling once per ASIN during the per-ASIN semantic work loop
so the output stays focused.

Output layout per ASIN:
  1. Listing state (title + char count, bullet char lengths, description words, backend bytes,
     image count, review count)
  2. Structured attributes: populated count, key populated fields, empty-field sample
  3. SQP buckets: total impressions / clicks / purchases, overall ASIN CTR/CVR vs aggregate
     market CTR/CVR on the same query set, then top 6
     queries per bucket ranked by Search Query Volume with ASIN/market CTR + CVR deltas
  4. Reviews: all positive_differentiated + all negative_differentiated themes with
     asin_mentions, asin_pct, category_pct, and snippets
  5. Competitive: benchmarks (title chars median + gap, image median + yours, price percentile,
     review + rating medians), white-space terms, saturated terms
  6. Category family (for reference-loading decision)

Designed to be read by Claude in one pass, then all subsequent work is reasoning over
the JSON already in context — no further inspection calls needed.
"""

import argparse
import json
import sys
from pathlib import Path


def fmt_num(n, default="—"):
    if n is None:
        return default
    if isinstance(n, float):
        if n.is_integer():
            return str(int(n))
        return f"{n:.2f}"
    return str(n)


def summarize_asin(asin, a):
    lines = []
    lines.append(f"\n{'='*70}")
    lines.append(f"ASIN: {asin}  |  category_family: {a.get('category_family','?')}  |  product_type: {a.get('product_type','?')}")
    lines.append(f"{'='*70}")

    # 1. Listing state
    ls = a.get('listing_state', {})
    lines.append("\n--- LISTING STATE (authoritative — use these numbers, not image estimates) ---")
    title = ls.get('title', '')
    lines.append(f"title ({ls.get('title_chars','?')} chars): {title!r}")
    blens = ls.get('bullet_lengths', [])
    lines.append(f"bullet lengths: {blens}")
    for i, b in enumerate(ls.get('bullets', []), 1):
        lines.append(f"  bullet {i}: {b}")
    lines.append(f"description ({ls.get('description_words','?')} words): {ls.get('description','')}")
    lines.append(f"backend ({ls.get('backend_bytes','?')} bytes of 250 max): {ls.get('backend','')}")
    lines.append(f"image_count: {ls.get('image_count','?')}  |  review_count: {ls.get('review_count','?')}")

    # 2. Structured attributes
    sg = a.get('structured_gaps', {})
    lines.append(f"\n--- STRUCTURED ATTRIBUTES ({sg.get('populated_fields_count','?')} populated) ---")
    pop = sg.get('populated_structured', {})
    # Filter noise (image locators, ID fields) and keep category-relevant + flag-worthy ones
    skip_prefixes = ('other_product_image_locator', 'main_product_image_locator', 'swatch_product_image_locator',
                     'amzn1.volt', 'fulfillment_availability', 'purchasable_offer',
                     'item_package_', 'skip_offer', 'condition_type', 'merchant_shipping_group',
                     '::listing_status', 'product_site_launch_date', 'child_parent_sku_relationship',
                     'parentage_level', 'gift_options', 'supplier_declared', 'batteries_required')
    for k, v in pop.items():
        if any(k.startswith(p) for p in skip_prefixes):
            continue
        vs = str(v)[:120]
        lines.append(f"  {k}: {vs}")
    empty_sample = sg.get('empty_fields_sample', [])[:25]
    if empty_sample:
        lines.append(f"\n  empty fields (first {len(empty_sample)} of {len(sg.get('empty_fields_sample', []))}):")
        for e in empty_sample:
            lines.append(f"    - {e}")

    # 3. SQP buckets
    sb = a.get('sqp_buckets', {})
    if sb:
        lines.append("\n--- SQP FUNNEL ---")
        tot_impr = sb.get('total_asin_impressions')
        tot_clk = sb.get('total_asin_clicks')
        tot_pur = sb.get('total_asin_purchases')
        lines.append(f"totals: impressions={fmt_num(tot_impr)}  clicks={fmt_num(tot_clk)}  purchases={fmt_num(tot_pur)}")
        lines.append(f"overall: CTR={fmt_num(sb.get('overall_impr_ctr_pct'))}% vs market {fmt_num(sb.get('market_overall_impr_ctr_pct'))}%  CVR={fmt_num(sb.get('overall_click_cvr_pct'))}% vs market {fmt_num(sb.get('market_overall_click_cvr_pct'))}%")

        bucket_labels = {
            'b1_impression_problem': 'B1 IMPRESSION PROBLEM (market serves high-vol, you get low impr share)',
            'b2_ctr_problem':        'B2 CTR PROBLEM (getting impressions but clicks lag market)',
            'b3_cvr_problem':        'B3 CVR PROBLEM (clicks convert worse than market)',
            'b4_positioning_gold':   'B4 POSITIONING GOLD (already winning — defend in copy)',
            'b5_expansion':          'B5 EXPANSION (untapped volume)',
        }
        for bkey, blabel in bucket_labels.items():
            queries = sb.get(bkey, [])
            if not isinstance(queries, list):
                continue
            lines.append(f"\n  {blabel}  [{len(queries)} queries]")
            qs = sorted(queries, key=lambda x: (x.get('Search Query Volume') or 0), reverse=True)[:6]
            for q in qs:
                sq = q.get('Search Query')
                vol = q.get('Search Query Volume')
                impr_share = q.get('Impressions: ASIN Share %')
                pur_share = q.get('Purchases: ASIN Share %')
                your_ctr = q.get('your_impr_ctr')
                mkt_ctr = q.get('market_impr_ctr')
                your_cvr = q.get('your_click_cvr')
                mkt_cvr = q.get('market_click_cvr')
                impr = q.get('Impressions: ASIN Count')
                clicks = q.get('Clicks: ASIN Count')
                purch = q.get('Purchases: ASIN Count')
                lines.append(f"    {sq!r:55s} vol={fmt_num(vol)}  impr_share={fmt_num(impr_share)}%  pur_share={fmt_num(pur_share)}%")
                lines.append(f"      yours: impr={fmt_num(impr)} clicks={fmt_num(clicks)} purch={fmt_num(purch)}  |  CTR {fmt_num(your_ctr)}% vs mkt {fmt_num(mkt_ctr)}%  |  CVR {fmt_num(your_cvr)}% vs mkt {fmt_num(mkt_cvr)}%")

    # 4. Reviews
    r = a.get('reviews', {})
    if r:
        lines.append("\n--- REVIEW THEMES (differentiated = your ASIN mentions this vs category avg) ---")
        pos = r.get('positive_differentiated', [])
        lines.append(f"\n  POSITIVE DIFFERENTIATED ({len(pos)} themes — lean into these):")
        for t in pos:
            lines.append(f"    [{t.get('topic')} / {t.get('subtopic')}]  asin={t.get('asin_mentions')}x ({fmt_num(t.get('asin_pct'))}%) cat={fmt_num(t.get('category_pct'))}%  — {t.get('snippets','')[:100]}")
        neg = r.get('negative_differentiated', [])
        lines.append(f"\n  NEGATIVE DIFFERENTIATED ({len(neg)} themes — pre-empt these):")
        for t in neg:
            lines.append(f"    [{t.get('topic')} / {t.get('subtopic')}]  asin={t.get('asin_mentions')}x ({fmt_num(t.get('asin_pct'))}%) cat={fmt_num(t.get('category_pct'))}%  — {t.get('snippets','')[:100]}")

    # 5. Competitive
    c = a.get('competitive', {})
    if c:
        lines.append("\n--- COMPETITIVE BENCHMARK ---")
        bm = c.get('benchmarks', {})
        yp = c.get('your_position', {})
        if bm:
            lines.append(f"  title chars: median {fmt_num(bm.get('title_chars_median'))} — you are at {fmt_num(ls.get('title_chars'))} (gap {fmt_num(bm.get('title_chars_gap_pct'))}%)")
            lines.append(f"  images: median {fmt_num(bm.get('image_count_median'))} — you have {fmt_num(ls.get('image_count'))}")
            lines.append(f"  price: p25={fmt_num(bm.get('price_p25'))} / median={fmt_num(bm.get('price_median'))} / p75={fmt_num(bm.get('price_p75'))} — you at {fmt_num(yp.get('price'))} (~{fmt_num(bm.get('price_percentile'))}th pct)")
            lines.append(f"  reviews: median={fmt_num(bm.get('review_median'))} — you have {fmt_num(ls.get('review_count'))}")
            lines.append(f"  rating:  median={fmt_num(bm.get('rating_median'))} — you at {fmt_num(yp.get('rating'))}")
            if yp.get('bsr') is not None:
                lines.append(f"  BSR: {fmt_num(yp.get('bsr'))}")
        ws = c.get('white_space_terms', []) or []
        if ws:
            lines.append(f"\n  WHITE-SPACE TERMS (underused in competitor titles — consider claiming): " + ", ".join(f"{t['term']}({t['count']})" for t in ws[:15]))
        st = c.get('saturated_terms', []) or []
        if st:
            lines.append(f"\n  SATURATED TERMS (overused — avoid leading with): " + ", ".join(f"{t['term']}({t['count']})" for t in st[:15]))

    # 6. PPC if present
    ppc = a.get('ppc', {})
    if ppc and (ppc.get('harvest') or ppc.get('negate')):
        lines.append("\n--- PPC SIGNALS ---")
        h = ppc.get('harvest', [])[:10]
        n = ppc.get('negate', [])[:10]
        lines.append(f"  HARVEST (account-proven converters — prioritize in title/backend): {[x.get('search_term') for x in h]}")
        lines.append(f"  NEGATE (wasted spend — surface in HTML for campaign negatives): {[x.get('search_term') for x in n]}")

    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--diagnostics', required=True, help='Path to diagnostics.json')
    ap.add_argument('--asin', default=None, help='Limit output to one ASIN (optional)')
    args = ap.parse_args()

    with open(args.diagnostics) as f:
        d = json.load(f)

    per_asin = d.get('per_asin', {})
    if not per_asin:
        print("ERROR: diagnostics.json has no per_asin data", file=sys.stderr)
        sys.exit(2)

    # Global header
    g = d.get('global', {})
    print(f"Mode: {g.get('mode')}  |  ASINs: {g.get('asins_processed')}  |  inputs: {g.get('inputs_used')}")
    w = d.get('warnings', [])
    if w:
        print(f"Warnings: {w}")

    targets = [args.asin] if args.asin else list(per_asin.keys())
    for asin in targets:
        a = per_asin.get(asin)
        if a is None:
            print(f"\n[WARN] ASIN {asin} not in diagnostics.json")
            continue
        print(summarize_asin(asin, a))


if __name__ == '__main__':
    main()
