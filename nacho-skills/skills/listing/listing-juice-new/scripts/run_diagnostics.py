#!/usr/bin/env python3
"""
run_diagnostics.py — Take parsed.json (from parse_inputs.py) and run all diagnostics
in one pass. Emits a second JSON that Claude can reason over.

Usage:
    python3 run_diagnostics.py --parsed /tmp/parsed.json --out /tmp/diagnostics.json [--asin B0XXXXXXXX]

Consolidates into one call:
  - SQP 5-bucket funnel (with CORRECT math: market CTR = clicks/impressions,
    market CVR-from-clicks = purchases/clicks, NOT the SQV-denominated rate fields)
  - Review theme prioritization (differentiated strengths/weaknesses)
  - Competitive benchmark vs top 20 Xray competitors
  - White-space token analysis
  - Category family detection
  - Listing quality scorecard (title length, image count, bullet coverage)
  - COSMO dimension coverage hints (structural, not semantic — Claude scores semantically)

Output JSON shape:
    {
      "per_asin": {
        "<ASIN>": {
          "product_type": str,
          "category_family": str,   # supplements|jewelry|apparel|...
          "listing_state": {
              "title": str, "title_chars": int, "bullets": [...], "bullet_lengths": [...],
              "description": str, "description_words": int,
              "backend": str, "backend_bytes": int,
              "image_count": int | null
          },
          "sqp_buckets": {
              "b1_impression_problem": [...],
              "b2_ctr_problem": [...],
              "b3_cvr_problem": [...],
              "b4_positioning_gold": [...],
              "b5_expansion": [...],
              "total_purchases": int,
              "overall_impr_ctr_pct": float,
              "overall_click_cvr_pct": float
          },
          "reviews": {
              "positive_differentiated": [...],   # ASIN%Mentions > 2x Category%
              "negative_differentiated": [...],
              "star_rating_drivers_positive": [...],
              "star_rating_drivers_negative": [...],
              "review_count": int | null,
              "below_threshold": bool
          },
          "competitive": {
              "top20_asins": [...],                # name, price, rating, reviews, images, title_chars
              "your_position": {...},
              "benchmarks": {
                  "title_chars_median": float, "your_title_chars": int, "gap_pct": float,
                  "image_count_median": float, "your_image_count": int | null,
                  "price_percentile": int, "your_price": float,
                  "review_median": float, "your_reviews": float,
                  "rating_median": float, "your_rating": float
              },
              "white_space_terms": [...],
              "saturated_terms": [...]
          },
          "structured_gaps": {
              "populated_fields_count": int,
              "empty_fields_sample": [...]
          }
        }
      },
      "global": {...},
      "warnings": [...]
    }

Exit codes: 0 = success, 2 = failure
"""

import argparse
import json
import math
import re
import sys
from collections import Counter


# =======================================================================================
# Tunable constants — consolidated here so `diagnostic-rules.md` and the code don't drift.
# Update this block together with the reference doc.
# =======================================================================================

# SQP bucket thresholds (see references/diagnostic-rules.md § SQP funnel bucketing)
SQP_B1_MIN_MARKET_IMPRESSIONS = 1000   # B1 — impression problem: only queries with real demand
SQP_B1_MAX_ASIN_IMPR_SHARE    = 0.005  # your impressions < 0.5% of market impressions
SQP_B2_MIN_ASIN_IMPRESSIONS   = 100    # B2 — CTR problem: sample-size floor
SQP_B2_CTR_UNDERPERFORM_RATIO = 0.5    # your CTR < 50% of market CTR
SQP_B3_MIN_ASIN_CLICKS        = 5      # B3 — CVR problem: sample-size floor
SQP_B3_CVR_UNDERPERFORM_RATIO = 0.5    # your CVR-from-clicks < 50% of market
SQP_B4_MIN_ASIN_CLICKS        = 5      # B4 — positioning gold
SQP_B4_MIN_ASIN_PURCHASES     = 2
SQP_B4_CVR_OVERPERFORM_RATIO  = 1.5    # your CVR > 150% of market OR purchase share > 5%
SQP_B4_PURCHASE_SHARE_FLOOR   = 5.0
SQP_B5_MIN_MARKET_PURCHASE_RATE = 3.0  # B5 — expansion: market converts well on this query
SQP_B5_MAX_ASIN_IMPR_SHARE      = 1.0  # but you're barely showing up
SQP_B5_MIN_QUERY_VOLUME         = 1000

# Review theme diff thresholds (see references/diagnostic-rules.md § Review prioritization)
REVIEW_DIFF_RATIO            = 2.0     # ASIN % > 2x Category % = differentiated
REVIEW_POS_STAR_IMPACT_FLOOR = 0.3     # positive star-rating driver threshold
REVIEW_NEG_STAR_IMPACT_CEIL  = -0.1    # negative star-rating driver threshold (magnitude)

# PPC search-term harvest/negate (see references/diagnostic-rules.md § PPC harvest)
PPC_HARVEST_MIN_ORDERS       = 1
PPC_HARVEST_MAX_ACOS         = 50.0    # harvest if ACOS < 50%
PPC_NEGATE_MIN_SPEND         = 5.0     # negate if spent > $5 with 0 orders
PPC_NEGATE_MAX_ORDERS        = 0


# Category family detection. Keep in sync with references/category-families.md.
# Match is substring on PRODUCT_TYPE.upper().
CATEGORY_FAMILIES = [
    ('supplements', ['HERBAL_SUPPLEMENT', 'VITAMIN', 'DIETARY_SUPPLEMENTS', 'NUTRITIONAL_SUPPLEMENT', 'SUPPLEMENTS']),
    ('consumables', ['GROCERY', 'BEVERAGE', 'COFFEE', 'TEA', 'SNACK_FOOD', 'CONDIMENT', 'CANDY', 'GOURMET_FOOD']),
    ('beauty',      ['BEAUTY', 'SKIN_CARE', 'MAKEUP', 'HAIR_CARE', 'PERSONAL_CARE_APPLIANCE', 'FRAGRANCE']),
    ('apparel',     ['SHIRT', 'DRESS', 'PANTS', 'SHOES', 'OUTERWEAR', 'UNDERWEAR', 'SOCKS', 'ACCESSORY']),
    ('jewelry',     ['NECKLACE', 'RING', 'EARRING', 'BRACELET', 'ANKLET', 'FINEOTHER', 'JEWELRY']),
    ('hardgoods',   ['HOME', 'KITCHEN', 'COOKWARE', 'FURNITURE', 'HOME_BED_AND_BATH',
                     'BED_AND_BATH', 'LAWN_AND_GARDEN', 'TOOLS', 'HARDWARE']),
    ('electronics', ['CONSUMER_ELECTRONICS', 'COMPUTER', 'CELL_PHONE_ACCESSORY',
                     'WIRELESS_ACCESSORY', 'CE', 'HEADPHONES']),
    ('pets',        ['PET', 'PET_FOOD', 'PET_SUPPLIES', 'PET_TOYS']),
    ('children',    ['TOYS', 'ASSORTED_TOYS', 'BABY_PRODUCT', 'CHILDRENS_CLOTHING', 'CHILDRENS_BOOK']),
]

def detect_family(product_type):
    if not product_type:
        return 'generic'
    pt = str(product_type).upper().strip()
    for family, types in CATEGORY_FAMILIES:
        for t in types:
            if t in pt:
                return family
    return 'generic'


def safe_num(v):
    if v is None: return None
    if isinstance(v, (int, float)):
        if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
            return None
        return v
    try: return float(str(v).replace(',', ''))
    except: return None


def run_sqp_buckets(sqp_queries):
    """Apply the corrected 5-bucket funnel logic.

    Rate math (see references/input-parsing.md § CRITICAL):
      market CTR     = Clicks: Total Count / Impressions: Total Count    (compute ourselves)
      your CTR       = Clicks: ASIN Count  / Impressions: ASIN Count
      market CVR-clk = Purchases: Total Count / Clicks: Total Count
      your CVR-clk   = Purchases: ASIN Count  / Clicks: ASIN Count

    The raw SQP rate fields (`Click Rate %`, `Purchase Rate %`) divide by Search Query
    Volume, not by the preceding funnel step — wrong denominator for this diagnostic.
    """
    import pandas as pd
    import numpy as np
    df = pd.DataFrame(sqp_queries)

    # Coerce numeric columns — SQP records come in as JSON and can be int, float, or None.
    numeric_cols = [
        'Search Query Volume',
        'Impressions: Total Count', 'Impressions: ASIN Count', 'Impressions: ASIN Share %',
        'Clicks: Total Count', 'Clicks: ASIN Count', 'Clicks: ASIN Share %',
        'Purchases: Total Count', 'Purchases: ASIN Count', 'Purchases: ASIN Share %',
        'Purchases: Purchase Rate %',
    ]
    for c in numeric_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')

    # Divide-by-zero safe: convert 0 to NaN before division using .where() (modern pandas
    # keeps ints as 0 on .replace(0, None), which corrupts the result).
    def rate(numer, denom):
        d = df[denom].where(df[denom] > 0, np.nan)
        return df[numer] / d * 100

    df['market_impr_ctr']   = rate('Clicks: Total Count',    'Impressions: Total Count')
    df['your_impr_ctr']     = rate('Clicks: ASIN Count',     'Impressions: ASIN Count')
    df['market_click_cvr']  = rate('Purchases: Total Count', 'Clicks: Total Count')
    df['your_click_cvr']    = rate('Purchases: ASIN Count',  'Clicks: ASIN Count')
    df = df.fillna(value={'your_impr_ctr': 0, 'your_click_cvr': 0,
                          'market_impr_ctr': 0, 'market_click_cvr': 0})

    # B1 — Impression problem: query has real market demand, your ASIN barely shows up
    b1 = df[(df['Impressions: Total Count'] > SQP_B1_MIN_MARKET_IMPRESSIONS) &
            (df['Impressions: ASIN Count'] < df['Impressions: Total Count'] * SQP_B1_MAX_ASIN_IMPR_SHARE)]
    b1 = b1.sort_values('Impressions: Total Count', ascending=False).head(10)

    # B2 — CTR problem: you have impressions but underperform market CTR
    b2 = df[(df['Impressions: ASIN Count'] >= SQP_B2_MIN_ASIN_IMPRESSIONS) &
            (df['your_impr_ctr'] < df['market_impr_ctr'] * SQP_B2_CTR_UNDERPERFORM_RATIO)]
    b2 = b2.sort_values('Impressions: ASIN Count', ascending=False).head(10)

    # B3 — CVR problem: you have clicks but underperform market post-click CVR
    b3 = df[(df['Clicks: ASIN Count'] >= SQP_B3_MIN_ASIN_CLICKS) &
            (df['your_click_cvr'] < df['market_click_cvr'] * SQP_B3_CVR_UNDERPERFORM_RATIO)]
    b3 = b3.sort_values('Clicks: ASIN Count', ascending=False).head(15)

    # B4 — Positioning gold: you convert better than market OR own a large purchase share
    b4 = df[(df['Clicks: ASIN Count'] >= SQP_B4_MIN_ASIN_CLICKS) &
            (df['Purchases: ASIN Count'] >= SQP_B4_MIN_ASIN_PURCHASES) &
            ((df['your_click_cvr'] > df['market_click_cvr'] * SQP_B4_CVR_OVERPERFORM_RATIO) |
             (df['Purchases: ASIN Share %'].fillna(0) > SQP_B4_PURCHASE_SHARE_FLOOR))]
    b4 = b4.sort_values('Purchases: ASIN Count', ascending=False).head(15)

    # B5 — Expansion: market converts well on this query, but you're barely visible
    b5 = df[(df['Purchases: Purchase Rate %'] > SQP_B5_MIN_MARKET_PURCHASE_RATE) &
            (df['Impressions: ASIN Share %'].fillna(0) < SQP_B5_MAX_ASIN_IMPR_SHARE) &
            (df['Search Query Volume'] > SQP_B5_MIN_QUERY_VOLUME)]
    b5 = b5.sort_values('Search Query Volume', ascending=False).head(10)

    def to_records(bucket):
        # Only keep the most decision-relevant columns to keep JSON tight
        keep = ['Search Query', 'Search Query Score', 'Search Query Volume',
                'Impressions: Total Count', 'Impressions: ASIN Count', 'Impressions: ASIN Share %',
                'Clicks: Total Count', 'Clicks: ASIN Count', 'Clicks: ASIN Share %',
                'Purchases: Total Count', 'Purchases: ASIN Count', 'Purchases: ASIN Share %',
                'Purchases: Purchase Rate %',
                'market_impr_ctr', 'your_impr_ctr', 'market_click_cvr', 'your_click_cvr']
        out = []
        for _, r in bucket.iterrows():
            d = {k: (None if pd.isna(r.get(k)) else (round(float(r[k]), 3) if isinstance(r.get(k), float) else r.get(k))) for k in keep if k in bucket.columns}
            out.append(d)
        return out

    # Overall stats, ASIN side
    total_asin_impressions = float(df['Impressions: ASIN Count'].sum())
    total_asin_clicks = float(df['Clicks: ASIN Count'].sum())
    total_asin_purchases = float(df['Purchases: ASIN Count'].sum())
    overall_impr_ctr = 100 * total_asin_clicks / total_asin_impressions if total_asin_impressions else 0
    overall_click_cvr = 100 * total_asin_purchases / total_asin_clicks if total_asin_clicks else 0

    # Overall stats, market side (same query set, all sellers combined)
    # Gives Claude an apples-to-apples aggregate baseline for the funnel comparison string,
    # instead of eyeballing a range from head-term rows which biases toward whatever
    # segment the seller over-indexes on.
    total_market_impressions = float(df['Impressions: Total Count'].sum())
    total_market_clicks = float(df['Clicks: Total Count'].sum())
    total_market_purchases = float(df['Purchases: Total Count'].sum())
    market_overall_impr_ctr = 100 * total_market_clicks / total_market_impressions if total_market_impressions else 0
    market_overall_click_cvr = 100 * total_market_purchases / total_market_clicks if total_market_clicks else 0

    return {
        "b1_impression_problem": to_records(b1),
        "b2_ctr_problem": to_records(b2),
        "b3_cvr_problem": to_records(b3),
        "b4_positioning_gold": to_records(b4),
        "b5_expansion": to_records(b5),
        "total_asin_impressions": int(total_asin_impressions),
        "total_asin_clicks": int(total_asin_clicks),
        "total_asin_purchases": int(total_asin_purchases),
        "overall_impr_ctr_pct": round(overall_impr_ctr, 3),
        "overall_click_cvr_pct": round(overall_click_cvr, 3),
        "market_overall_impr_ctr_pct": round(market_overall_impr_ctr, 3),
        "market_overall_click_cvr_pct": round(market_overall_click_cvr, 3),
    }


def run_review_analysis(review_data):
    """Prioritize review themes: differentiated strengths, differentiated weaknesses."""
    out = {
        "positive_differentiated": [],
        "negative_differentiated": [],
        "star_rating_drivers_positive": [],
        "star_rating_drivers_negative": [],
        "positive_themes_all": review_data.get("positive_topics", []),
        "negative_themes_all": review_data.get("negative_topics", []),
        "below_threshold": False,
    }
    # Diff strengths/weaknesses: ASIN % mentioned > REVIEW_DIFF_RATIO x Category %
    for row in review_data.get("positive_topics", []):
        asin_pct = safe_num(row.get("asin_pct"))
        cat_pct = safe_num(row.get("category_pct"))
        if asin_pct and cat_pct and cat_pct > 0 and asin_pct > REVIEW_DIFF_RATIO * cat_pct:
            out["positive_differentiated"].append(row)
    for row in review_data.get("negative_topics", []):
        asin_pct = safe_num(row.get("asin_pct"))
        cat_pct = safe_num(row.get("category_pct"))
        if asin_pct and cat_pct and cat_pct > 0 and asin_pct > REVIEW_DIFF_RATIO * cat_pct:
            out["negative_differentiated"].append(row)
    # Star-rating drivers: themes with high absolute impact on star rating
    for row in review_data.get("positive_star_impact", []):
        asin = safe_num(row.get("asin_impact"))
        if asin is not None and asin >= REVIEW_POS_STAR_IMPACT_FLOOR:
            out["star_rating_drivers_positive"].append(row)
    for row in review_data.get("negative_star_impact", []):
        asin = safe_num(row.get("asin_impact"))
        if asin is not None and asin <= REVIEW_NEG_STAR_IMPACT_CEIL:
            out["star_rating_drivers_negative"].append(row)
    return out


def run_ppc_analysis(ppc_data):
    """Bucket PPC search terms into harvest candidates and negate candidates.

    Harvest: converted at acceptable ACOS — promote to exact-match campaigns.
    Negate: spent budget without converting — add as negative to stop the bleed.

    Column naming varies between Campaign Manager and AdLabs exports; detect both.
    """
    if not ppc_data or not ppc_data.get('records'):
        return None
    records = ppc_data['records']
    fmt = ppc_data.get('format', 'unknown')

    # Column name detection — Campaign Manager vs AdLabs
    col_map_candidates = {
        'term':    ['Customer Search Term', 'search_term', 'Search Term'],
        'orders':  ['7 Day Total Orders (#)', 'orders', 'Orders'],
        'spend':   ['Spend', 'spend', 'Cost'],
        'sales':   ['7 Day Total Sales ', '7 Day Total Sales', 'sales', 'Sales'],
        'acos':    ['Total Advertising Cost of Sales (ACOS) ', 'acos', 'ACOS'],
        'clicks':  ['Clicks', 'clicks'],
    }
    def pick_col(logical, sample):
        for cand in col_map_candidates[logical]:
            if cand in sample:
                return cand
        return None

    sample = records[0] if records else {}
    col_term   = pick_col('term', sample)
    col_orders = pick_col('orders', sample)
    col_spend  = pick_col('spend', sample)
    col_sales  = pick_col('sales', sample)
    col_acos   = pick_col('acos', sample)
    col_clicks = pick_col('clicks', sample)

    if not col_term or not col_orders or not col_spend:
        return {"format": fmt, "error": "missing required columns (term/orders/spend)",
                "harvest": [], "negate": []}

    # Aggregate by term (same query can appear in multiple campaigns)
    agg = {}
    for r in records:
        term = r.get(col_term)
        if not term or not str(term).strip():
            continue
        term = str(term).strip().lower()
        orders = safe_num(r.get(col_orders)) or 0
        spend  = safe_num(r.get(col_spend))  or 0
        sales  = safe_num(r.get(col_sales))  or 0
        clicks = safe_num(r.get(col_clicks)) if col_clicks else None
        a = agg.setdefault(term, {"term": term, "orders": 0, "spend": 0.0,
                                  "sales": 0.0, "clicks": 0})
        a["orders"] += orders
        a["spend"]  += spend
        a["sales"]  += sales
        if clicks is not None:
            a["clicks"] += clicks

    for a in agg.values():
        a["acos"] = round(100 * a["spend"] / a["sales"], 2) if a["sales"] > 0 else None

    harvest = [a for a in agg.values()
               if a["orders"] >= PPC_HARVEST_MIN_ORDERS
               and a["acos"] is not None
               and a["acos"] < PPC_HARVEST_MAX_ACOS]
    harvest.sort(key=lambda x: (-x["orders"], x["acos"]))

    negate = [a for a in agg.values()
              if a["orders"] <= PPC_NEGATE_MAX_ORDERS
              and a["spend"] >= PPC_NEGATE_MIN_SPEND]
    negate.sort(key=lambda x: -x["spend"])

    return {
        "format": fmt,
        "unique_terms": len(agg),
        "harvest": harvest[:25],
        "negate": negate[:25],
    }


def _norm_brand(v):
    """Case-fold + strip a brand name for equality matching."""
    return str(v or '').strip().upper()


def _get_price(row):
    """Return the numeric price from an Xray row regardless of currency column name.

    Helium 10 Xray exports name the price column by marketplace currency: 'Price  $' (US),
    'Price  £' (UK), 'Price  €' (EU). Prefer the US name for backward compatibility, then
    fall back to any column whose name starts with 'Price' so UK/EU prices are not silently
    dropped as None.
    """
    if not row:
        return None
    if 'Price  $' in row:
        return row.get('Price  $')
    for k in row.keys():
        if str(k).startswith('Price'):
            return row.get(k)
    return None


def run_competitive(xray_records, own_asin, own_brand):
    """Competitive benchmark vs top 20 competitors + white-space token analysis.

    Own-row resolution order:
      1. Exact ASIN match (most reliable when seller's ASIN is in the Xray set)
      2. Brand equality, BUT only if exactly one brand row exists (prevents picking the
         wrong SKU when the seller has multiple products in the same Xray)
    If neither, own_row is None and positional/benchmark fields are nulled — don't silently
    pick an arbitrary row.
    """
    own_brand_norm = _norm_brand(own_brand)
    competitors = [r for r in xray_records
                   if _norm_brand(r.get('Brand')) != own_brand_norm or not own_brand_norm]

    own_row = None
    asin_matches = [r for r in xray_records if r.get('ASIN') == own_asin]
    if asin_matches:
        own_row = asin_matches[0]
    elif own_brand_norm:
        brand_matches = [r for r in xray_records if _norm_brand(r.get('Brand')) == own_brand_norm]
        if len(brand_matches) == 1:
            own_row = brand_matches[0]

    # Top 20 by display order
    top20 = sorted([r for r in competitors if r.get('Display Order') is not None],
                   key=lambda r: r['Display Order'])[:20]

    # Benchmarks
    def pct(values, q):
        vals = [v for v in values if v is not None]
        if not vals: return None
        vals = sorted(vals)
        idx = int(q * (len(vals) - 1))
        return vals[idx]

    def med(values):
        """True statistical median — average of the two middle values for even-length lists."""
        vals = sorted([v for v in values if v is not None])
        n = len(vals)
        if not n:
            return None
        if n % 2 == 1:
            return vals[n // 2]
        return (vals[n // 2 - 1] + vals[n // 2]) / 2

    t20_titles = [r.get('Title Char. Count') for r in top20]
    t20_images = [r.get('Images') for r in top20]
    t20_prices = [_get_price(r) for r in top20]
    t20_reviews = [r.get('Review Count') for r in top20]
    t20_ratings = [r.get('Ratings') for r in top20]

    title_med = med(t20_titles)
    own_title_chars = own_row.get('Title Char. Count') if own_row else None
    gap_pct = None
    if title_med and own_title_chars:
        gap_pct = round(100 * (own_title_chars - title_med) / title_med, 1)

    own_price = _get_price(own_row) if own_row else None
    price_percentile = None
    if own_price and t20_prices:
        sorted_prices = sorted([p for p in t20_prices if p is not None])
        below = sum(1 for p in sorted_prices if p < own_price)
        price_percentile = int(100 * below / len(sorted_prices)) if sorted_prices else None

    # White-space token analysis
    STOPWORDS = set("with this that your from have been were will each they their some more "
                    "necklace women womens gift gifts silver for and the to in of a an is it our "
                    "you on all are as be by or is it was".split())
    all_tokens = []
    for r in top20:
        t = str(r.get('Product Details', '')).lower()
        tokens = re.findall(r'\b[a-z]{4,}\b', t)
        all_tokens.extend([w for w in tokens if w not in STOPWORDS])
    counts = Counter(all_tokens)
    white_space = sorted([(w, c) for w, c in counts.items() if 1 <= c <= 2], key=lambda x: -x[1])[:20]
    saturated = [(w, c) for w, c in counts.most_common(15)]

    return {
        "top20_asins": [
            {"display_order": r.get('Display Order'), "brand": r.get('Brand'),
             "asin": r.get('ASIN'), "title": r.get('Product Details'),
             "price": _get_price(r), "rating": r.get('Ratings'),
             "reviews": r.get('Review Count'), "images": r.get('Images'),
             "bsr": r.get('BSR'), "title_chars": r.get('Title Char. Count')}
            for r in top20
        ],
        "your_position": {
            "display_order": own_row.get('Display Order') if own_row else None,
            "title_chars": own_title_chars,
            "images": own_row.get('Images') if own_row else None,
            "price": own_price,
            "rating": own_row.get('Ratings') if own_row else None,
            "reviews": own_row.get('Review Count') if own_row else None,
            "bsr": own_row.get('BSR') if own_row else None,
        } if own_row else None,
        "benchmarks": {
            "title_chars_median": title_med,
            "title_chars_gap_pct": gap_pct,
            "image_count_median": med(t20_images),
            "your_image_count": own_row.get('Images') if own_row else None,
            "price_p25": pct(t20_prices, 0.25),
            "price_median": med(t20_prices),
            "price_p75": pct(t20_prices, 0.75),
            "price_percentile": price_percentile,
            "review_median": med(t20_reviews),
            "rating_median": med(t20_ratings),
        },
        "white_space_terms": [{"term": w, "count": c} for w, c in white_space],
        "saturated_terms": [{"term": w, "count": c} for w, c in saturated],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--parsed', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--asin', default=None)
    args = ap.parse_args()

    with open(args.parsed) as f:
        parsed = json.load(f)

    result = {"per_asin": {}, "global": {}, "warnings": []}

    if not parsed.get("flat_file"):
        result["warnings"].append("No flat file parsed — per-ASIN diagnostics require Mode 2 or Mode 3 data")

    # Build per-ASIN analysis
    asins_to_process = []
    if parsed.get("flat_file"):
        for a in parsed["flat_file"]["asins"]:
            if args.asin and a["asin"] != args.asin:
                continue
            asins_to_process.append(a)

    # Dedupe by ASIN, but prefer the row that actually carries listing content.
    # On variation families the parent row often has empty title/bullets — auditing that
    # row while the child SKU has the real copy would flag a healthy listing as broken.
    best_by_asin = {}
    for a in asins_to_process:
        asin = a["asin"]
        if not asin:
            continue
        # "Content score" = title presence + non-empty bullet count (rough but reliable).
        score = (1 if a.get("title") else 0) + sum(1 for b in a.get("bullets", []) if b)
        if asin not in best_by_asin or score > best_by_asin[asin][0]:
            best_by_asin[asin] = (score, a)
    unique = [v[1] for v in best_by_asin.values()]

    # Shared PPC analysis (run once; attach to each ASIN — PPC reports aren't per-ASIN scoped)
    ppc_analysis = None
    if parsed.get("ppc_search_terms"):
        try:
            ppc_analysis = run_ppc_analysis(parsed["ppc_search_terms"])
        except Exception as e:
            result["warnings"].append(f"PPC analysis failed: {e}")

    # Xray lookup index for populating review_count when own ASIN is in Xray
    xray_by_asin = {}
    if parsed.get("xray_asins"):
        for r in parsed["xray_asins"]:
            if r.get('ASIN'):
                xray_by_asin[r['ASIN']] = r

    for a in unique:
        asin = a["asin"]
        # Review count — pull from Xray when available (flat file doesn't contain it).
        review_count = None
        xray_own = xray_by_asin.get(asin)
        if xray_own:
            review_count = safe_num(xray_own.get('Review Count'))

        pa = {
            "product_type": a["product_type"],
            "category_family": detect_family(a["product_type"]),
            "listing_state": {
                "title": a["title"],
                "title_chars": len(a["title"]),
                "bullets": a["bullets"],
                "bullet_lengths": [len(b) for b in a["bullets"]],
                "description": a["description"],
                "description_words": len(a["description"].split()),
                "backend": a["backend"],
                "backend_bytes": len(a["backend"].encode('utf-8')),
                # image_count comes from parse_flat_file counting populated image URL
                # cells; review_count comes from Xray if own ASIN is present.
                "image_count": a.get("image_count"),
                "review_count": review_count,
            },
            "structured_gaps": {
                "populated_fields_count": len(a["structured"]),
                "populated_structured": a["structured"],
                "empty_fields_sample": a["empty_structured_fields"][:50],
            },
        }

        # SQP buckets (if SQP ASIN matches)
        if parsed.get("sqp") and parsed["sqp"].get("asin") == asin:
            try:
                pa["sqp_buckets"] = run_sqp_buckets(parsed["sqp"]["queries"])
            except Exception as e:
                result["warnings"].append(f"SQP buckets failed for {asin}: {e}")

        # Reviews
        review_data = next((r for r in parsed.get("reviews", []) if r.get("asin") == asin), None)
        if review_data:
            pa["reviews"] = run_review_analysis(review_data)

        # Competitive
        if parsed.get("xray_asins"):
            try:
                pa["competitive"] = run_competitive(parsed["xray_asins"], asin, a["brand"])
            except Exception as e:
                result["warnings"].append(f"Competitive analysis failed for {asin}: {e}")

        # PPC (shared across ASINs)
        if ppc_analysis is not None:
            pa["ppc"] = ppc_analysis

        result["per_asin"][asin] = pa

    result["global"] = {
        "mode": parsed.get("mode"),
        "marketplace": (parsed.get("flat_file") or {}).get("marketplace", "UNKNOWN"),
        "asins_processed": list(result["per_asin"].keys()),
        "inputs_used": {
            "flat_file": parsed.get("flat_file") is not None,
            "sqp": parsed.get("sqp") is not None,
            "reviews": len(parsed.get("reviews", [])),
            "xray_asins": parsed.get("xray_asins") is not None,
            "ppc": parsed.get("ppc_search_terms") is not None,
        }
    }

    with open(args.out, 'w') as f:
        json.dump(result, f, indent=2, default=str)

    print(f"Processed {len(result['per_asin'])} ASINs")
    for asin, data in result["per_asin"].items():
        ls = data['listing_state']
        print(f"  {asin}: family={data['category_family']} title_chars={ls['title_chars']} "
              f"images={ls.get('image_count')} reviews={ls.get('review_count')}")
        if 'sqp_buckets' in data:
            sb = data['sqp_buckets']
            print(f"    SQP: B1={len(sb['b1_impression_problem'])} B2={len(sb['b2_ctr_problem'])} "
                  f"B3={len(sb['b3_cvr_problem'])} B4={len(sb['b4_positioning_gold'])} "
                  f"B5={len(sb['b5_expansion'])} | overall CTR {sb['overall_impr_ctr_pct']}% "
                  f"vs market {sb['market_overall_impr_ctr_pct']}% | "
                  f"CVR {sb['overall_click_cvr_pct']}% "
                  f"vs market {sb['market_overall_click_cvr_pct']}%")
        if 'reviews' in data:
            r = data['reviews']
            print(f"    Reviews: +diff={len(r['positive_differentiated'])} "
                  f"-diff={len(r['negative_differentiated'])}")
        if 'competitive' in data:
            b = data['competitive']['benchmarks']
            your_tc = data['competitive'].get('your_position', {}).get('title_chars') if data['competitive'].get('your_position') else None
            med_tc = b.get('title_chars_median')
            gap = b.get('title_chars_gap_pct')
            print(f"    Competitive: your title {your_tc} vs median {med_tc} (gap {gap}%)")
        if 'ppc' in data and data['ppc']:
            p = data['ppc']
            print(f"    PPC: harvest={len(p.get('harvest', []))} negate={len(p.get('negate', []))}")
    if result["warnings"]:
        print("Warnings:", result["warnings"])
    print(f"Wrote {args.out}")


if __name__ == '__main__':
    main()
