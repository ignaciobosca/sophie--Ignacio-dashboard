#!/usr/bin/env python3
"""
parse_inputs.py — Ingest all Alexa Shopping Tier 2 audit inputs and emit a single JSON.

Usage:
    python3 parse_inputs.py --uploads /mnt/user-data/uploads --out /tmp/parsed.json
    python3 parse_inputs.py --uploads <dir> --out <path> [--asin B0XXXXXXXX]
    python3 parse_inputs.py --uploads <dir> --listing-json /tmp/listing.json --out <path>

Consolidates into one call what would otherwise take 5-8 separate tool invocations:
  - Walks uploads directory, detects input mode (2=flat file, 3=screenshot, none=error)
  - Parses Category Listings Report (.xlsm or .xlsx), auto-detecting row 4 vs row 5
    attribute layout
  - Parses SQP CSV (US_Search_Query_Performance*.csv)
  - Parses Helium 10 Review Analysis XLSX(s)
  - Parses Helium 10 Xray CSV(s) — detects ASIN xray vs keyword xray
  - Parses PPC search term reports (Campaign Manager or AdLabs format)
  - Reconciles ASINs across sources

Output JSON shape:
    {
      "mode": 2 | 3 | 4 | null,   # 4 = listing-JSON (Sophie Hub MCP pull, no workbook)
      "inputs_detected": {...},
      "warnings": [...],
      "errors": [...],
      "flat_file": {  # Mode 2 only
        "path": str,
        "sheet_name": str,
        "attr_row": int,           # 4 or 5
        "data_start_row": int,     # attr_row + 2
        "total_rows": int,
        "marketplace": "US" | "UK" | "DE" | ... | "UNKNOWN",  # detected from marketplace_id
        "asins": [
          {
            "sku": str, "asin": str | null, "row": int,
            "title": str, "brand": str, "product_type": str,
            "description": str, "bullets": [str, str, str, str, str],
            "backend": str,
            "structured": {<attr_id>: <value>, ...},  # all non-empty populated fields
            "empty_structured": [<attr_id>, ...],     # populated field list, empty
          },
          ...
        ]
      },
      "sqp": { "asin": str, "queries": [...] } | null,
      "reviews": [ { "asin": str, "positive_topics": [...], "negative_topics": [...],
                     "positive_star_impact": [...], "negative_star_impact": [...] }, ... ],
      "xray_asins": [...],   # competitor ASINs with metrics
      "xray_keywords": [...] | null,
      "ppc_search_terms": [...] | null,
      "screenshot_paths": [...]
    }

Exit codes:
    0 = success
    2 = hard failure (writes error detail to stdout + the JSON output)
"""

import argparse
import io
import json
import math
import os
import re
import sys
import traceback
from datetime import datetime

# Amazon marketplace_id -> marketplace code (Listing Juice v2: multi-marketplace support).
# Covers US + UK/EU + other major marketplaces. Detection is advisory only: an unknown or
# missing id degrades to a WARNING, never a hard error, so a non-US file still parses.
MARKETPLACE_MAP = {
    'ATVPDKIKX0DER': 'US',
    'A2EUQ1WTGCTBG2': 'CA',
    'A1AM78C64UM0Y8': 'MX',
    'A2Q3Y263D00KWC': 'BR',
    'A1F83G8C2ARO7P': 'UK',
    'A1PA6795UKMFR9': 'DE',
    'A13V1IB3VIYZZH': 'FR',
    'APJ6JRA9NG5V4': 'IT',
    'A1RKKUPIHCS9HS': 'ES',
    'A1805IZSGTT6HS': 'NL',
    'A2NODRKZP88ZB9': 'SE',
    'A1C3SOZRARQ6R3': 'PL',
    'AMEN7PMS3EDWL': 'BE',
    'A33AVAJ2PDY3EV': 'TR',
    'A2VIGQ35RCS4UG': 'AE',
    'A17E79C6D8DWNP': 'SA',
    'ARBP9OOSHTCHU': 'EG',
    'A21TJRUUN4KGV': 'IN',
    'A1VC38T7YXB528': 'JP',
    'A39IBJ37TRP1C6': 'AU',
    'A19VAU5U5O7RUS': 'SG',
}


def detect_marketplace(title_attr):
    """Detect the Amazon marketplace from a Category Listings Report attribute id.

    Returns (marketplace_code, warning_or_None). Never raises and never blocks: an unknown
    or missing marketplace_id degrades to a WARNING so a non-US file (UK/EU/etc.) still parses.
    The brand/description/generic_keyword find_col fallbacks are locale-agnostic, so removing
    the old US-only gate lets a UK/DE/FR/... file parse correctly.
    """
    s = str(title_attr) if title_attr is not None else ''
    m = re.search(r'marketplace_id=([A-Z0-9]+)', s)
    if not m:
        return 'UNKNOWN', (
            "No marketplace_id found in the Category Listings Report title attribute; "
            "defaulting marketplace to UNKNOWN. Ask the seller which Amazon marketplace "
            "this listing belongs to before relying on locale-specific guidance."
        )
    mid = m.group(1)
    if mid in MARKETPLACE_MAP:
        return MARKETPLACE_MAP[mid], None
    return mid, (
        f"Unrecognized marketplace_id={mid}; proceeding with marketplace set to the raw id. "
        f"Confirm the marketplace with the seller and verify locale-specific rules manually."
    )


def safe_json(obj):
    """Coerce NaN/Inf/datetime to JSON-compatible values."""
    if isinstance(obj, dict):
        return {k: safe_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [safe_json(x) for x in obj]
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
    if isinstance(obj, datetime):
        return obj.isoformat()
    return obj


def walk_uploads(uploads_dir):
    """Classify every file in the uploads directory."""
    if not os.path.isdir(uploads_dir):
        return {"error": f"Uploads dir {uploads_dir} does not exist"}
    inventory = {
        "flat_file": None,
        "sqp": None,
        "reviews": [],           # one per ASIN
        "xray_asins": None,
        "xray_keywords": None,
        "ppc_search_terms": None,
        "screenshots": [],
        "unrecognized": [],
    }
    for fn in sorted(os.listdir(uploads_dir)):
        path = os.path.join(uploads_dir, fn)
        if not os.path.isfile(path):
            continue
        lower = fn.lower()
        if re.match(r'category[_ ]listings[_ ]report.*\.(xlsm|xlsx)$', lower, re.I):
            inventory["flat_file"] = path
        elif re.match(r'^[a-z]{2}[_ ]search[_ ]query[_ ]performance.*\.csv$', lower, re.I):
            inventory["sqp"] = path
        elif re.match(r'helium[_ ]10[_ ]review[_ ]analysis[_ ]-[_ ]([a-z0-9]{10})', lower, re.I):
            m = re.search(r'([A-Z0-9]{10})', fn)
            inventory["reviews"].append({"path": path, "asin": m.group(1) if m else None})
        elif re.match(r'helium[_ ]10[_ ]xray.*\.csv$', lower, re.I):
            inventory["xray_asins"] = path
        elif re.match(r'xray[_ ]keyword.*\.csv$', lower, re.I):
            inventory["xray_keywords"] = path
        elif lower.endswith(('.png', '.jpg', '.jpeg')):
            inventory["screenshots"].append(path)
        elif 'search term' in lower and lower.endswith('.csv'):
            inventory["ppc_search_terms"] = path
        elif lower.endswith(('.xlsx', '.xlsm', '.csv')):
            # Could be PPC — try to detect by first read
            inventory["unrecognized"].append(path)
    return inventory


def parse_flat_file(path, target_asin=None):
    """Parse Amazon Category Listings Report. Auto-detects row 4 vs row 5 attribute layout."""
    import openpyxl
    wb = openpyxl.load_workbook(path, keep_vba=False, data_only=True)

    # Find the template sheet
    ws = None
    attr_row = None
    attrs = None
    for name in wb.sheetnames:
        candidate = wb[name]
        for candidate_row in (5, 4):
            row_vals = [candidate.cell(row=candidate_row, column=c).value
                        for c in range(1, candidate.max_column + 1)]
            if any(v and '::record_action' in str(v) for v in row_vals):
                ws = candidate
                attr_row = candidate_row
                attrs = row_vals
                break
        if ws is not None:
            break

    if ws is None:
        return {"error": f"No template sheet found. Sheets: {wb.sheetnames}"}

    def find_col(pattern, exact=False):
        for idx, a in enumerate(attrs):
            if a is None:
                continue
            s = str(a)
            if (s == pattern) if exact else (pattern in s):
                return idx + 1
        return None

    def find_bullet_col(n):
        for idx, a in enumerate(attrs):
            if a and 'bullet_point[' in str(a) and f']#{n}' in str(a):
                return idx + 1
        return None

    # Required columns
    sku_col = find_col('contribution_sku')
    title_col = find_col('item_name[')
    record_action_col = find_col('::record_action')
    if not all([sku_col, title_col, record_action_col]):
        missing = [n for n, c in [('sku', sku_col), ('item_name', title_col),
                                  ('record_action', record_action_col)] if not c]
        return {"error": f"Required columns missing: {missing}"}

    # Marketplace detection (multi-marketplace: US + UK/EU + others). Never blocks — an
    # unknown/missing id becomes a warning so a non-US file still audits.
    title_attr = attrs[title_col - 1]
    marketplace, mp_warning = detect_marketplace(title_attr)
    ff_warnings = []
    if mp_warning:
        ff_warnings.append(f"WARNING: {mp_warning}")

    # Locate other common cols
    col_map = {
        'product_type': find_col('product_type#1.value') or find_col('product_type'),
        'brand': find_col('brand[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#1.value') or find_col('brand['),
        'description': find_col('product_description[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#1.value') or find_col('product_description['),
        'generic_keyword': find_col('generic_keyword[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#1.value') or find_col('generic_keyword['),
        'product_id': find_col('amzn1.volt.ca.product_id_value') or find_col('external_product_id'),
        'product_id_type': find_col('amzn1.volt.ca.product_id_type') or find_col('external_product_id_type'),
        'parentage_level': find_col('parentage_level'),
    }
    bullet_cols = [find_bullet_col(n) for n in range(1, 6)]
    data_start = attr_row + 2

    # Image URL columns — used to populate image_count (Rule 2: numbers must be traceable
    # to JSON so Claude doesn't eyeball-count from screenshots).
    image_cols = []
    main_image_col = find_col('main_product_image_locator') or find_col('main_image_url')
    if main_image_col:
        image_cols.append(main_image_col)
    for i in range(1, 9):  # other_product_image_locator_1 through _8
        c = find_col(f'other_product_image_locator_{i}') or find_col(f'other_image_url{i}')
        if c:
            image_cols.append(c)

    # Build the full attribute index (for "show everything populated" per row)
    attr_by_col = {idx + 1: str(a) for idx, a in enumerate(attrs) if a}

    # Collect all data rows
    asins_data = []
    for r in range(data_start, ws.max_row + 1):
        sku = ws.cell(row=r, column=sku_col).value
        if not sku or str(sku).strip() == '' or str(sku).strip() == 'ABC123':
            continue
        asin_val = ws.cell(row=r, column=col_map['product_id']).value if col_map['product_id'] else None
        asin_str = str(asin_val).strip() if asin_val else None

        # Skip early if filtering for specific ASIN
        if target_asin and asin_str != target_asin:
            continue

        structured = {}
        empty_fields = []
        for col_idx, attr_id in attr_by_col.items():
            if col_idx in (sku_col, title_col, record_action_col,
                           col_map.get('description'), col_map.get('generic_keyword'),
                           *[bc for bc in bullet_cols if bc]):
                continue  # handled separately
            val = ws.cell(row=r, column=col_idx).value
            if val is not None and str(val).strip() != '':
                structured[attr_id] = str(val).strip() if not isinstance(val, (int, float)) else val
            else:
                # Only log attr as "empty and populated" for a curated list of common fields
                # to keep output manageable
                short = attr_id.split('[')[0].replace(':', '').strip()
                if short and short not in ('settings', 'settings2'):
                    empty_fields.append(attr_id)

        # Count populated image URL cells (main + other_1..8)
        image_count = 0
        for ic in image_cols:
            v = ws.cell(row=r, column=ic).value
            if v is not None and str(v).strip():
                image_count += 1

        asin_row = {
            "sku": str(sku).strip(),
            "asin": asin_str,
            "row": r,
            "title": str(ws.cell(row=r, column=title_col).value or '').strip(),
            "brand": str(ws.cell(row=r, column=col_map['brand']).value or '').strip() if col_map['brand'] else '',
            "product_type": str(ws.cell(row=r, column=col_map['product_type']).value or '').strip() if col_map['product_type'] else '',
            "description": str(ws.cell(row=r, column=col_map['description']).value or '').strip() if col_map['description'] else '',
            "bullets": [str(ws.cell(row=r, column=bc).value or '').strip() if bc else '' for bc in bullet_cols],
            "backend": str(ws.cell(row=r, column=col_map['generic_keyword']).value or '').strip() if col_map['generic_keyword'] else '',
            "parentage_level": str(ws.cell(row=r, column=col_map['parentage_level']).value or '').strip() if col_map['parentage_level'] else '',
            "image_count": image_count,
            "structured": structured,
            "empty_structured_fields": empty_fields[:200],  # cap to avoid JSON bloat
        }
        asins_data.append(asin_row)

    return {
        "path": path,
        "sheet_name": ws.title,
        "attr_row": attr_row,
        "data_start_row": data_start,
        "total_rows": ws.max_row - data_start + 1,
        "marketplace": marketplace,
        "warnings": ff_warnings,
        "asins": asins_data,
        "col_map": col_map,
        "bullet_cols": bullet_cols,
        "sku_col": sku_col,
        "title_col": title_col,
        "record_action_col": record_action_col,
    }


# ---------------------------------------------------------------------------
# Mode 4 — listing JSON (Sophie Hub MCP pull)
# ---------------------------------------------------------------------------
# There is no Category Listings Report in the Sophie Hub / SP-API pipeline. The
# closest S3 report (GET_MERCHANT_LISTINGS_ALL_DATA) is a flat 30-column TSV
# with no bullets, no backend terms and no structured attributes, so it cannot
# satisfy parse_flat_file(). Mode 4 therefore skips the workbook entirely: the
# runner assembles a listing payload from MCP calls and hands it over as JSON.
# Contract is documented in references/sophie-hub-pull.md.
#
# Mode 4 never produces an upload-ready flat file (no Listing Loader template
# exists to partial-update), and backend search terms are not exposed by any
# Sophie Hub or Keepa surface, so `backend` is normally null.

LISTING_JSON_REQUIRED = ("asin", "title")


def parse_listing_json(path, target_asin=None):
    """Parse a runner-assembled listing payload into the flat_file shape.

    Emits exactly the structure run_diagnostics.py expects from mode 2, so no
    downstream script needs to know where the data came from.
    """
    try:
        with io.open(path, encoding="utf-8") as fh:
            payload = json.load(fh)
    except Exception as e:
        return {"error": f"could not read listing JSON: {e}"}

    if not isinstance(payload, dict):
        return {"error": "listing JSON must be an object"}

    rows = payload.get("asins")
    if not isinstance(rows, list) or not rows:
        return {"error": "listing JSON has no 'asins' array"}

    marketplace = str(payload.get("marketplace") or "US").upper()
    warnings = []
    asins_data = []

    for i, r in enumerate(rows):
        if not isinstance(r, dict):
            warnings.append(f"listing JSON: entry {i} is not an object, skipped")
            continue
        missing = [k for k in LISTING_JSON_REQUIRED if not r.get(k)]
        if missing:
            warnings.append(f"listing JSON: entry {i} missing {missing}, skipped")
            continue

        asin = str(r["asin"]).strip().upper()
        if target_asin and asin != target_asin.strip().upper():
            continue

        bullets = [str(b).strip() for b in (r.get("bullets") or []) if str(b).strip()]

        # Guard against the get_product_catalog flattening bug: the Catalog Items
        # payload collapses per-marketplace attribute arrays to a single value, so
        # bullet_point comes back as ONE bullet even when the live listing has five
        # or six. Auditing 1/6th of the copy silently is worse than saying so.
        if len(bullets) <= 1:
            warnings.append(
                f"{asin}: only {len(bullets)} bullet(s) supplied. Amazon allows five and most "
                "live listings use them. If these came from get_product_catalog, the payload "
                "was flattened — re-pull the bullets from Keepa (keepa_get_product -> features) "
                "before trusting the bullet audit."
            )

        backend = r.get("backend")
        backend = str(backend).strip() if backend else ""
        if not backend:
            warnings.append(
                f"{asin}: backend search terms not available. No Sophie Hub, SP-API or Keepa "
                "surface exposes the generic_keyword field, so the current backend cannot be "
                "audited and any proposed backend has no baseline to dedupe against. Check it "
                "in Seller Central before overwriting."
            )

        structured = r.get("structured") or {}
        if not isinstance(structured, dict):
            structured = {}
        empty_fields = r.get("empty_structured_fields") or []
        if not isinstance(empty_fields, list):
            empty_fields = []

        asins_data.append({
            "sku": str(r.get("sku") or "").strip(),
            "asin": asin,
            "row": None,                      # no workbook row in mode 4
            "title": str(r.get("title") or "").strip(),
            "brand": str(r.get("brand") or "").strip(),
            "product_type": str(r.get("product_type") or "").strip(),
            "description": str(r.get("description") or "").strip(),
            "bullets": bullets,
            "backend": backend,
            "parentage_level": str(r.get("parentage_level") or "").strip(),
            "image_count": r.get("image_count"),
            "structured": structured,
            "empty_structured_fields": empty_fields[:200],
        })

    if not asins_data:
        return {"error": "listing JSON produced no usable ASIN rows"}

    stale = payload.get("listing_report_date")
    if stale:
        warnings.append(
            f"Listing content reflects the pipeline snapshot dated {stale}. "
            "If that is more than ~30 days old, the live listing may have changed."
        )

    return {
        "path": path,
        "sheet_name": None,
        "attr_row": None,
        "data_start_row": None,
        "total_rows": len(asins_data),
        "marketplace": marketplace,
        "warnings": warnings,
        "asins": asins_data,
        "col_map": {},
        "bullet_cols": [],
        "sku_col": None,
        "title_col": None,
        "record_action_col": None,
        # Hard gate for write_flat_file.py: there is no source workbook to
        # partial-update, so the xlsx path must never run in mode 4.
        "has_workbook": False,
        "source": payload.get("source", "sophie-hub-mcp"),
        "store": payload.get("store"),
    }


SQP_REQUIRED_COLS = (
    'Search Query', 'Search Query Volume',
    'Impressions: Total Count', 'Impressions: ASIN Count',
    'Clicks: Total Count', 'Clicks: ASIN Count',
    'Purchases: Total Count', 'Purchases: ASIN Count',
)


def parse_sqp(path):
    """Parse SQP export. Auto-detects two-level vs flat-header layouts.

    Two layouts exist in the wild:

    - Legacy / ASIN View (multi-level): row 0 = ASIN filter metadata, row 1 = empty,
      row 2 = category header (Impressions / Clicks / Purchases), row 3 = metric header
      (Total Count / ASIN Count / ASIN Share %), row 4+ = data.

    - Simple (flat): row 0 = ASIN filter metadata, row 1 = single combined header
      ("Search Query", "Impressions: Total Count", "Clicks: Click Rate %", ...),
      row 2+ = data.

    Same output shape either way: columns are flattened to "Impressions: Total Count"
    form so downstream diagnostics work identically. See references/input-parsing.md
    § SQP Parsing.
    """
    import pandas as pd
    # Extract ASIN from the filter metadata line. Only look at the first line so we don't
    # pick up 10-char alphanumeric noise from later rows. ASINs start with "B0".
    with open(path, 'rb') as f:
        filter_line = f.readline().decode('utf-8-sig', errors='replace')
    asins = re.findall(r'\bB0[A-Z0-9]{8}\b', filter_line)

    # Detect which layout we have by sniffing the header row of the Simple format
    # (file-row index 1, 0-indexed). If it already contains the combined-token form
    # ("Search Query" AND something like "Impressions: Total Count"), it's flat.
    import csv
    with open(path, 'r', encoding='utf-8-sig', errors='replace') as f:
        reader = csv.reader(f)
        rows_peek = []
        for i, row in enumerate(reader):
            rows_peek.append(row)
            if i >= 3:
                break
    row1 = rows_peek[1] if len(rows_peek) > 1 else []
    is_flat_header = (
        any(c.strip() == 'Search Query' for c in row1)
        and any(': ' in c for c in row1)  # combined tokens like "Impressions: Total Count"
    )

    if is_flat_header:
        # Simple format — single header row at file-row index 1.
        df = pd.read_csv(path, header=0, skiprows=1)
        df.columns = [str(c).strip() for c in df.columns]
    else:
        # Legacy two-level header at file rows 2 and 3 (after skipping row 0).
        df = pd.read_csv(path, header=[2, 3], skiprows=1)
        # Flatten: "Impressions" + "Total Count" -> "Impressions: Total Count"
        flat_cols = []
        for tup in df.columns:
            a, b = (tup[0], tup[1]) if isinstance(tup, tuple) else (tup, '')
            a_s = '' if a is None or str(a).startswith('Unnamed') else str(a).strip()
            b_s = '' if b is None or str(b).startswith('Unnamed') else str(b).strip()
            if a_s and b_s:
                flat_cols.append(f"{a_s}: {b_s}")
            else:
                flat_cols.append(a_s or b_s)
        df.columns = flat_cols

    # Fail loudly if the expected schema is missing — silently producing a no-SQP audit
    # is worse than a clear error.
    missing = [c for c in SQP_REQUIRED_COLS if c not in df.columns]
    if missing:
        layout = 'flat' if is_flat_header else 'two-level'
        raise ValueError(f"SQP schema mismatch ({layout} layout) — missing columns: {missing}. "
                         f"Got columns: {list(df.columns)[:20]}...")

    df = df.replace({float('nan'): None})
    queries = df.to_dict('records')
    return {
        "path": path,
        "asin": asins[0] if asins else None,
        "all_asins": asins,
        "reporting_range": filter_line.strip(),
        "query_count": len(queries),
        "queries": queries,
        "header_layout": "flat" if is_flat_header else "two-level",
    }


def parse_reviews(path, asin=None):
    """Parse Helium 10 Review Analysis XLSX."""
    import openpyxl
    wb = openpyxl.load_workbook(path, data_only=True)

    def read_sheet(name, cols):
        if name not in wb.sheetnames:
            return []
        ws = wb[name]
        rows = []
        for r in range(2, ws.max_row + 1):
            row = {cols[i]: ws.cell(row=r, column=i+1).value for i in range(len(cols))}
            if any(row.values()):
                rows.append(row)
        return rows

    topic_cols = ["topic", "subtopic", "asin_mentions", "asin_pct", "category_pct", "snippets"]
    impact_cols = ["topic", "asin_impact", "category_impact"]
    trend_cols = ["month", "asin_pct", "category_pct"]

    return {
        "path": path,
        "asin": asin,
        "positive_topics": read_sheet("Positive Topic Insights", topic_cols),
        "negative_topics": read_sheet("Negative Topic Insights", topic_cols),
        "positive_star_impact": read_sheet("Positive Star Rating Impact", impact_cols),
        "negative_star_impact": read_sheet("Negative Star Rating Impact", impact_cols),
    }


def parse_xray_asins(path):
    """Parse Helium 10 Xray CSV (competitor ASINs)."""
    import pandas as pd
    df = pd.read_csv(path, encoding='utf-8-sig')
    df = df.replace({float('nan'): None})
    records = df.to_dict('records')
    # Normalize numeric columns
    def clean_num(v):
        if v is None:
            return None
        if isinstance(v, (int, float)):
            return v
        s = str(v).replace(',', '')
        try: return float(s)
        except: return None
    # Price column name varies by marketplace currency: 'Price  $' (US), 'Price  £' (UK),
    # 'Price  €' (EU). Match by 'Price' prefix so all currencies normalize instead of
    # silently leaving UK/EU prices as un-parsed strings.
    price_col = None
    if records:
        for k in records[0].keys():
            if str(k).startswith('Price'):
                price_col = k
                break
    numeric_cols = ['Ratings', 'Review Count', 'Images', 'BSR', 'Title Char. Count', 'Display Order']
    if price_col:
        numeric_cols.append(price_col)
    for r in records:
        for k in numeric_cols:
            if k in r:
                r[k] = clean_num(r[k])
    return records


# ---------------------------------------------------------------------------
# Competitor set from the Helium 10 MCP (mode 4 companion)
# ---------------------------------------------------------------------------
# The competitive benchmark in run_diagnostics.py reads Helium 10 X-Ray records.
# X-Ray is a browser-extension export, but the same numbers are reachable through
# the Helium 10 MCP (get_listing_details / search_competitors_by_asin /
# compare_listings). Rather than changing the diagnostics schema, this normalises
# an MCP-derived competitor list into the exact record shape parse_xray_asins
# produces, so run_competitive() works unchanged.
#
# Required per competitor: asin. Everything else is optional and degrades to None,
# which the benchmark already handles (it filters None before taking medians).

COMPETITOR_FIELD_MAP = {
    "asin": "ASIN",
    "brand": "Brand",
    "title_chars": "Title Char. Count",
    "reviews": "Review Count",
    "rating": "Ratings",
    "images": "Images",
    "bsr": "BSR",
    "price": "Price  $",
    "rank": "Display Order",
}


def parse_competitors_json(path):
    """Normalise an MCP-derived competitor list into X-Ray record shape."""
    try:
        with io.open(path, encoding="utf-8") as fh:
            payload = json.load(fh)
    except Exception as e:
        return {"error": f"could not read competitors JSON: {e}"}

    rows = payload.get("competitors") if isinstance(payload, dict) else payload
    if not isinstance(rows, list) or not rows:
        return {"error": "competitors JSON has no 'competitors' array"}

    def num(v):
        if v is None or isinstance(v, bool):
            return None
        if isinstance(v, (int, float)):
            return float(v)
        try:
            return float(str(v).replace(",", "").replace("$", "").strip())
        except Exception:
            return None

    records, warnings, skipped = [], [], 0
    for i, r in enumerate(rows):
        if not isinstance(r, dict) or not r.get("asin"):
            skipped += 1
            continue
        rec = {}
        for src, dst in COMPETITOR_FIELD_MAP.items():
            v = r.get(src)
            rec[dst] = v if dst in ("ASIN", "Brand") else num(v)
        rec["ASIN"] = str(rec["ASIN"]).strip().upper()
        rec["Brand"] = str(rec.get("Brand") or "").strip()
        if rec.get("Display Order") is None:
            rec["Display Order"] = float(i + 1)   # preserve supplied order
        records.append(rec)

    if skipped:
        warnings.append(f"competitors JSON: {skipped} entry/entries had no asin and were skipped")
    if len(records) < 5:
        warnings.append(
            f"Competitor set has only {len(records)} listing(s). Medians from a set this small "
            "are not a market benchmark — report them as indicative or omit the comparison."
        )
    missing_titles = sum(1 for r in records if r.get("Title Char. Count") is None)
    if missing_titles == len(records):
        warnings.append(
            "No competitor title lengths supplied, so the title-length benchmark will be skipped."
        )
    return {"records": records, "warnings": warnings}


def parse_ppc_search_terms(path):
    """Parse a PPC search term report. Handles Campaign Manager and AdLabs formats."""
    import pandas as pd
    if path.lower().endswith('.csv'):
        df = pd.read_csv(path)
    else:
        df = pd.read_excel(path)
    df = df.replace({float('nan'): None})
    # Normalize column names — detect format
    cols = set(df.columns)
    records = df.to_dict('records')
    fmt = 'campaign_manager' if 'Customer Search Term' in cols else ('adlabs' if 'search_term' in cols else 'unknown')
    return {"format": fmt, "records": records}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--uploads', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--asin', default=None, help='Optional: filter flat file to this ASIN only')
    ap.add_argument('--competitors-json', default=None,
                    help='Optional: competitor set pulled from the Helium 10 MCP, normalised '
                         'into X-Ray record shape. Use when no X-Ray CSV was uploaded. '
                         'See references/sophie-hub-pull.md.')
    ap.add_argument('--listing-json', default=None,
                    help='Mode 4: path to a runner-assembled listing payload pulled from '
                         'Sophie Hub + Keepa (see references/sophie-hub-pull.md). Replaces '
                         'the Category Listings Report; no workbook, no xlsx output.')
    args = ap.parse_args()

    result = {
        "mode": None,
        "inputs_detected": {},
        "warnings": [],
        "errors": [],
        "flat_file": None,
        "sqp": None,
        "reviews": [],
        "xray_asins": None,
        "xray_keywords": None,
        "ppc_search_terms": None,
        "screenshot_paths": [],
    }

    try:
        inventory = walk_uploads(args.uploads)
        if "error" in inventory:
            result["errors"].append(inventory["error"])
            result["mode"] = None
        else:
            result["inputs_detected"] = {
                "flat_file": inventory["flat_file"],
                "sqp": inventory["sqp"],
                "reviews_count": len(inventory["reviews"]),
                "xray_asins": inventory["xray_asins"],
                "xray_keywords": inventory["xray_keywords"],
                "ppc_search_terms": inventory["ppc_search_terms"],
                "screenshots_count": len(inventory["screenshots"]),
                "unrecognized_files": inventory["unrecognized"],
            }

            # Mode 4 (listing JSON from the Sophie Hub pull) wins over a screenshot
            # but yields to a real flat file: an uploaded Category Listings Report is
            # strictly richer (it carries backend terms, which no MCP surface exposes).
            if inventory["flat_file"]:
                result["mode"] = 2
                if args.listing_json:
                    result["warnings"].append(
                        "Both a Category Listings Report and a listing JSON were supplied. "
                        "Using the flat file: it carries backend search terms and supports "
                        "the upload-ready xlsx, neither of which mode 4 can do."
                    )
            elif args.listing_json:
                result["mode"] = 4
            elif inventory["screenshots"]:
                result["mode"] = 3
            else:
                result["mode"] = None
                result["errors"].append("No flat file, listing JSON or screenshot found. Provide a Category Listings Report (.xlsm/.xlsx), a Sophie Hub listing JSON (--listing-json), or a Seller Central screenshot (.png/.jpg).")

            # Parse what's available (all inputs are independent)
            if result["mode"] == 4:
                lj = parse_listing_json(args.listing_json, target_asin=args.asin)
                if "error" in lj:
                    result["errors"].append(f"Listing JSON: {lj['error']}")
                else:
                    result["flat_file"] = lj
                    result["warnings"].extend(lj.get("warnings", []))
                    result["inputs_detected"]["listing_json"] = args.listing_json

            if inventory["flat_file"]:
                ff = parse_flat_file(inventory["flat_file"], target_asin=args.asin)
                if "error" in ff:
                    result["errors"].append(f"Flat file: {ff['error']}")
                else:
                    result["flat_file"] = ff
                    # Surface marketplace-detection warnings (non-US / unknown) without blocking.
                    result["warnings"].extend(ff.get("warnings", []))
                    # Targeted --asin with no match is a hard error — producing an empty
                    # report silently is worse than failing.
                    if args.asin and not ff["asins"]:
                        result["errors"].append(
                            f"Target ASIN {args.asin} not found in flat file. "
                            f"Check the ASIN or omit --asin to audit the full portfolio."
                        )

            if inventory["sqp"]:
                try:
                    result["sqp"] = parse_sqp(inventory["sqp"])
                except Exception as e:
                    result["errors"].append(f"SQP parse failed: {e}")

            for rev in inventory["reviews"]:
                if args.asin and rev["asin"] != args.asin:
                    continue
                try:
                    result["reviews"].append(parse_reviews(rev["path"], rev["asin"]))
                except Exception as e:
                    result["warnings"].append(f"Review parse failed for {rev['asin']}: {e}")

            # MCP competitor set — only when no X-Ray CSV was uploaded. An uploaded
            # X-Ray is richer (full SERP with display order), so it always wins.
            if args.competitors_json and not inventory["xray_asins"]:
                cj = parse_competitors_json(args.competitors_json)
                if "error" in cj:
                    result["warnings"].append(f"Competitors JSON: {cj['error']}")
                else:
                    result["xray_asins"] = cj["records"]
                    result["warnings"].extend(cj["warnings"])
                    result["inputs_detected"]["competitors_json"] = args.competitors_json
            elif args.competitors_json and inventory["xray_asins"]:
                result["warnings"].append(
                    "Both an X-Ray CSV and a competitors JSON were supplied. Using the X-Ray: "
                    "it carries the full SERP with display order."
                )

            if inventory["xray_asins"]:
                try:
                    result["xray_asins"] = parse_xray_asins(inventory["xray_asins"])
                except Exception as e:
                    result["warnings"].append(f"Xray ASINs parse failed: {e}")

            if inventory["xray_keywords"]:
                try:
                    import pandas as pd
                    df = pd.read_csv(inventory["xray_keywords"], encoding='utf-8-sig').replace({float('nan'): None})
                    result["xray_keywords"] = df.to_dict('records')
                except Exception as e:
                    result["warnings"].append(f"Xray keywords parse failed: {e}")

            if inventory["ppc_search_terms"]:
                try:
                    result["ppc_search_terms"] = parse_ppc_search_terms(inventory["ppc_search_terms"])
                except Exception as e:
                    result["warnings"].append(f"PPC parse failed: {e}")

            result["screenshot_paths"] = inventory["screenshots"]

    except Exception as e:
        result["errors"].append(f"Unhandled: {e}\n{traceback.format_exc()}")

    # Write out
    with open(args.out, 'w') as f:
        json.dump(safe_json(result), f, indent=2, default=str)

    # Print a short summary to stdout so Claude sees what happened
    print(f"Mode: {result['mode']}")
    print(f"Inputs: {result['inputs_detected']}")
    if result['flat_file']:
        print(f"Flat file: {len(result['flat_file']['asins'])} ASINs parsed (row layout: attr_row={result['flat_file']['attr_row']})")
    if result['sqp']:
        print(f"SQP: {result['sqp']['query_count']} queries for {result['sqp']['asin']}")
    print(f"Reviews: {len(result['reviews'])} ASINs")
    print(f"Xray ASINs: {len(result['xray_asins']) if result['xray_asins'] else 0}")
    if result['warnings']:
        print(f"Warnings: {result['warnings']}")
    if result['errors']:
        print(f"ERRORS: {result['errors']}")
        sys.exit(2)
    print(f"Wrote {args.out}")


if __name__ == '__main__':
    main()
