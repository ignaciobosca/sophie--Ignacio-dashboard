#!/usr/bin/env python3
"""
write_flat_file.py — Take the seller's flat file + a rewrites JSON, produce the
upload-ready PartialUpdate xlsx.

Usage:
    python3 write_flat_file.py \
        --flat-file /mnt/user-data/uploads/Category_Listings_Report_*.xlsm \
        --rewrites /tmp/rewrites.json \
        --out /mnt/user-data/outputs/Category_Listings_Report_<Brand>_Tier2_Updated.xlsx

The rewrites JSON shape Claude is expected to produce (placeholders, not a real run):
    {
      "brand": "<seller brand name>",
      "asins": {
        "<ASIN>": {
          "title": {"value": "<new title>", "passed_gate": true | false},
          "bullets": [
            {"value": "<new bullet 1>", "passed_gate": bool},
            {"value": "<new bullet 2>", "passed_gate": bool},
            // ... 5 total
          ],
          "description": {"value": "<new description>", "passed_gate": bool},
          "backend": {"value": "<new backend terms>", "passed_gate": bool},
          "strict_structured_fills": {
              "<attribute_id_substring>": "<value>",
              // ...
          }
        }
      }
    }

Rules enforced by this script:
  - Every audited row's ::record_action is set to "PartialUpdate"
  - Only fields with passed_gate=true are written
  - Strict-tier structured fills only write if the current cell is empty
  - Title capped at 200 chars (truncate at word boundary with warning)
  - Bullets capped at 500 chars
  - Backend capped at 249 bytes (UTF-8 aware)
  - Advisory-tier fills MUST NOT be in the rewrites JSON (Claude filters before passing)
  - Never touches feed_product_type, ::last_modified, or child_parent_sku_relationship

Output: writes the xlsx, prints a summary of what was written per ASIN, exits 0 on success.
"""

import argparse
import json
import re
import sys
from shutil import copyfile


def find_attr_row(ws):
    for candidate_row in (5, 4):
        row_vals = [ws.cell(row=candidate_row, column=c).value
                    for c in range(1, ws.max_column + 1)]
        if any(v and '::record_action' in str(v) for v in row_vals):
            return candidate_row, row_vals
    return None, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--flat-file', required=True)
    ap.add_argument('--rewrites', required=True)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()

    # Mode 4 guard. A Sophie Hub listing pull has no Listing Loader workbook behind
    # it, so there is nothing to partial-update. Fail loudly rather than emitting an
    # xlsx that looks uploadable but is not.
    if not str(args.flat_file).lower().endswith(('.xlsm', '.xlsx')):
        sys.stderr.write(
            "write_flat_file: --flat-file is not an .xlsm/.xlsx workbook.\n"
            "Mode 4 (Sophie Hub listing JSON) cannot produce an upload-ready flat file: "
            "SP-API exposes listing content but not the Listing Loader template needed for "
            "a partial update. Ship the HTML audit, and if the seller wants an upload file, "
            "ask them to download the Category Listings Report from Seller Central and re-run "
            "in mode 2.\n"
        )
        sys.exit(2)

    # Copy fresh
    copyfile(args.flat_file, args.out)

    import openpyxl
    wb = openpyxl.load_workbook(args.out, keep_vba=False)

    # Locate sheet + attr row
    ws = None
    attr_row = None
    attrs = None
    for name in wb.sheetnames:
        candidate = wb[name]
        r, a = find_attr_row(candidate)
        if r:
            ws, attr_row, attrs = candidate, r, a
            break
    if ws is None:
        print("ERROR: No template sheet found")
        sys.exit(2)

    def find_col(pattern):
        for idx, a in enumerate(attrs):
            if a and pattern in str(a):
                return idx + 1
        return None

    def find_structured_col(pattern):
        """Stricter match for structured fills. Requires the pattern to be followed by a
        boundary character (`[`, `#`, or end-of-string) so `diet_type` doesn't match
        `diet_type_keyword` and silently write to the wrong column.

        Falls back to unique-substring match (exactly one column contains the pattern) to
        stay tolerant of minor attribute-ID variations between template versions.
        """
        # Strict: pattern is a full attribute ID fragment
        for idx, a in enumerate(attrs):
            if not a:
                continue
            s = str(a)
            if re.search(re.escape(pattern) + r'(\[|#|$)', s):
                return idx + 1
        # Fallback: unique substring
        matches = [idx + 1 for idx, a in enumerate(attrs)
                   if a and pattern in str(a)]
        return matches[0] if len(matches) == 1 else None

    def find_bullet_col(n):
        for idx, a in enumerate(attrs):
            if a and 'bullet_point[' in str(a) and f']#{n}' in str(a):
                return idx + 1
        return None

    record_action_col = find_col('::record_action')
    sku_col = find_col('contribution_sku')
    title_col = find_col('item_name[')
    bullet_cols = [find_bullet_col(n) for n in range(1, 6)]
    description_col = find_col('product_description[')
    backend_col = find_col('generic_keyword[')
    asin_col = find_col('amzn1.volt.ca.product_id_value') or find_col('external_product_id')

    data_start = attr_row + 2

    # Build row index by ASIN
    rows_by_asin = {}
    for r in range(data_start, ws.max_row + 1):
        sku = ws.cell(row=r, column=sku_col).value
        if not sku or str(sku).strip() in ('', 'ABC123'):
            continue
        asin = ws.cell(row=r, column=asin_col).value if asin_col else None
        if asin and str(asin).strip():
            rows_by_asin.setdefault(str(asin).strip(), []).append(r)

    # Load rewrites
    with open(args.rewrites) as f:
        rewrites = json.load(f)

    brand = rewrites.get('brand', 'Portfolio')
    summary = {"rows_updated": 0, "per_asin": {}, "warnings": []}

    # Forbidden columns never to touch
    forbidden_patterns = ('feed_product_type', '::last_modified',
                          'child_parent_sku_relationship', 'parentage_level')

    for asin, asin_rw in rewrites.get('asins', {}).items():
        if asin not in rows_by_asin:
            summary["warnings"].append(f"ASIN {asin} not found in flat file")
            continue
        per_asin_summary = {"fields_written": [], "fields_skipped": [], "structured_filled": [], "structured_skipped": []}

        for row_idx in rows_by_asin[asin]:
            # Set record_action
            ws.cell(row=row_idx, column=record_action_col, value='PartialUpdate')

            # Title
            title_rw = asin_rw.get('title', {})
            if title_rw.get('passed_gate') and title_rw.get('value'):
                val = title_rw['value']
                if len(val) > 200:
                    val = val[:200].rsplit(' ', 1)[0]
                    summary["warnings"].append(f"{asin}: title truncated to {len(val)} chars at word boundary")
                ws.cell(row=row_idx, column=title_col, value=val)
                per_asin_summary["fields_written"].append(f"title ({len(val)} chars)")
            else:
                per_asin_summary["fields_skipped"].append("title (gate failed or missing)")

            # Bullets
            for n, bullet_rw in enumerate(asin_rw.get('bullets', []), start=1):
                col = bullet_cols[n-1] if n-1 < len(bullet_cols) else None
                if not col:
                    continue
                if bullet_rw.get('passed_gate') and bullet_rw.get('value'):
                    val = bullet_rw['value']
                    if len(val) > 500:
                        val = val[:500].rsplit(' ', 1)[0]
                        summary["warnings"].append(f"{asin}: bullet {n} truncated")
                    ws.cell(row=row_idx, column=col, value=val)
                    per_asin_summary["fields_written"].append(f"bullet_{n} ({len(val)} chars)")
                else:
                    per_asin_summary["fields_skipped"].append(f"bullet_{n} (gate failed or missing)")

            # Description
            desc_rw = asin_rw.get('description', {})
            if desc_rw.get('passed_gate') and desc_rw.get('value') and description_col:
                ws.cell(row=row_idx, column=description_col, value=desc_rw['value'])
                per_asin_summary["fields_written"].append(f"description ({len(desc_rw['value'])} chars)")
            else:
                per_asin_summary["fields_skipped"].append("description (gate failed or missing)")

            # Backend
            backend_rw = asin_rw.get('backend', {})
            if backend_rw.get('passed_gate') and backend_rw.get('value') and backend_col:
                val = backend_rw['value']
                # Byte-safe truncation
                while len(val.encode('utf-8')) > 249:
                    if ' ' not in val:
                        val = val[:-1]
                    else:
                        val = val.rsplit(' ', 1)[0]
                ws.cell(row=row_idx, column=backend_col, value=val)
                per_asin_summary["fields_written"].append(f"backend ({len(val.encode('utf-8'))} bytes)")
            else:
                per_asin_summary["fields_skipped"].append("backend (gate failed or missing)")

            # Strict-tier structured fills — use anchored match so e.g. `diet_type` can't
            # silently write to `diet_type_keyword`.
            for pattern, value in asin_rw.get('strict_structured_fills', {}).items():
                # Skip forbidden
                if any(fp in pattern for fp in forbidden_patterns):
                    per_asin_summary["structured_skipped"].append(f"{pattern} (forbidden)")
                    continue
                col = find_structured_col(pattern)
                if col is None:
                    per_asin_summary["structured_skipped"].append(f"{pattern} (ambiguous or not in template)")
                    continue
                current = ws.cell(row=row_idx, column=col).value
                if current is not None and str(current).strip() != '':
                    per_asin_summary["structured_skipped"].append(f"{pattern} (already populated)")
                    continue
                ws.cell(row=row_idx, column=col, value=value)
                per_asin_summary["structured_filled"].append(f"{pattern}={value}")

            summary["rows_updated"] += 1

        summary["per_asin"][asin] = per_asin_summary

    wb.save(args.out)

    # Verify
    wb2 = openpyxl.load_workbook(args.out)
    ws2 = None
    for name in wb2.sheetnames:
        cand = wb2[name]
        r, _ = find_attr_row(cand)
        if r:
            ws2 = cand
            break
    for asin in rewrites.get('asins', {}):
        for row_idx in rows_by_asin.get(asin, []):
            action = ws2.cell(row=row_idx, column=record_action_col).value
            if action != 'PartialUpdate':
                print(f"VERIFICATION FAILED: row {row_idx} action = {action}")
                sys.exit(2)

    print(f"Wrote {args.out}")
    print(f"Rows updated: {summary['rows_updated']}")
    for asin, ps in summary['per_asin'].items():
        print(f"\n{asin}:")
        if ps['fields_written']:
            print(f"  ✓ wrote: {', '.join(ps['fields_written'])}")
        if ps['fields_skipped']:
            print(f"  · skipped: {', '.join(ps['fields_skipped'])}")
        if ps['structured_filled']:
            print(f"  ✓ structured: {', '.join(ps['structured_filled'])}")
        if ps['structured_skipped']:
            print(f"  · structured skipped: {', '.join(ps['structured_skipped'][:5])}{' ...' if len(ps['structured_skipped']) > 5 else ''}")
    if summary['warnings']:
        print(f"\nWarnings: {summary['warnings']}")


if __name__ == '__main__':
    main()
