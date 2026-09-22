#!/usr/bin/env python3
"""
check_outputs.py — Script-enforced version of SKILL.md Rule 3 (output completeness).

Usage:
    python3 check_outputs.py --parsed /tmp/parsed.json --outputs-dir /mnt/user-data/outputs

Fails with exit code 2 if:
  - Flat-file mode run with --xlsx-requested but no xlsx in outputs dir
  - No HTML in outputs dir
  - HTML is suspiciously small (< 10 KB — likely an error page or empty template)
  - HTML contains literal "{{" placeholder text (shouldn't happen now that
    build_html_report.py fails on unsubstituted placeholders, but double-check)

The xlsx partial-update flat file is OPT-IN — pass --xlsx-requested only when the
seller explicitly asked for an upload-ready flat file. Default runs ship HTML only,
which saves a writer pass and keeps single-chat runs inside budget. Sellers can
re-run with --xlsx-requested when they're ready to apply changes.

This is the final pre-`present_files` gate. Run it after the writer scripts complete.
"""

import argparse
import json
import sys
from pathlib import Path


MIN_HTML_BYTES = 10_000  # empty templates are ~8KB; real reports are >>20KB


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--parsed', required=True, help='Path to parsed.json from parse_inputs.py')
    ap.add_argument('--outputs-dir', required=True, help='Directory where outputs live')
    ap.add_argument('--xlsx-requested', action='store_true',
                    help='Seller explicitly asked for the partial-update xlsx. '
                         'When set, Mode 2 runs require the xlsx to exist. '
                         'When omitted (default), xlsx is optional and a missing one is not an error.')
    args = ap.parse_args()

    with open(args.parsed) as f:
        parsed = json.load(f)
    mode = parsed.get('mode')
    outputs = Path(args.outputs_dir)
    if not outputs.is_dir():
        print(f"ERROR: outputs dir does not exist: {outputs}", file=sys.stderr)
        sys.exit(2)

    html_files = sorted(outputs.glob('Listing Juice*.html'))
    xlsx_files = sorted(outputs.glob('Category_Listings_Report_*_Tier2_Updated_*.xlsx'))

    errors = []
    warnings = []

    # HTML is required in every mode
    if not html_files:
        errors.append("No HTML report found (Listing Juice*.html). Did build_html_report.py run?")
    else:
        newest = max(html_files, key=lambda p: p.stat().st_mtime)
        size = newest.stat().st_size
        if size < MIN_HTML_BYTES:
            errors.append(f"HTML report suspiciously small ({size:,} bytes): {newest.name}. "
                          f"Likely incomplete — check build_html_report.py output.")
        else:
            # Sanity check: no literal {{PLACEHOLDER}} leaked through
            content = newest.read_text()
            leftover = []
            for token in content.split('{{')[1:]:
                end = token.find('}}')
                if end > 0 and end < 40:
                    key = token[:end]
                    if key.isupper() and key.replace('_', '').replace('0', '').isalnum():
                        leftover.append(key)
            if leftover:
                errors.append(f"HTML contains unsubstituted placeholder(s): {sorted(set(leftover))[:10]}")

            # Seller-facing quality lints. Em-dashes and &ldquo;/&rdquo; entities are
            # common AI-tell/encoding bugs that slip through even when placeholders
            # are clean. Scan the body (skip CSS, which may contain U+2014 in comments).
            import re as _re
            body_m = _re.search(r'<div class="container">(.*?)</div>\s*<footer>', content, _re.DOTALL)
            body_text = body_m.group(1) if body_m else content
            em_count = body_text.count('\u2014') + body_text.count('\u2013')
            entity_count = sum(body_text.count(e) for e in
                               ('&ldquo;', '&rdquo;', '&amp;ldquo;', '&amp;rdquo;'))
            if em_count:
                warnings.append(f"{em_count} em-dash/en-dash character(s) in seller-facing body. "
                                f"User preference is to replace with commas, periods, or parentheses.")
            if entity_count:
                warnings.append(f"{entity_count} literal &ldquo;/&rdquo; HTML entity in seller-facing "
                                f"body (renders as literal text, not a curly quote). Use \u201C/\u201D "
                                f"characters directly in report JSON.")

    # xlsx only required when seller explicitly asked for it. Default is HTML-only.
    # Only flat-file mode (mode == 2) can produce the xlsx; screenshot mode cannot.
    mode_can_produce_xlsx = (mode == 2)
    needs_xlsx = args.xlsx_requested and mode_can_produce_xlsx
    if needs_xlsx and not xlsx_files:
        errors.append(f"Seller requested an xlsx (--xlsx-requested) for Mode {mode}, but no "
                      f"Category_Listings_Report_*_Tier2_Updated_*.xlsx was found in {outputs}. "
                      f"Did write_flat_file.py run? Do not call present_files without it.")
    elif not args.xlsx_requested and xlsx_files:
        warnings.append(f"xlsx present in outputs without --xlsx-requested — probably fine "
                        f"(seller may have asked mid-run), will be presented alongside HTML.")

    # Print results
    if html_files:
        for f in html_files:
            print(f"  HTML: {f.name} ({f.stat().st_size:,} bytes)")
    if xlsx_files:
        for f in xlsx_files:
            print(f"  xlsx: {f.name} ({f.stat().st_size:,} bytes)")

    for w in warnings:
        print(f"⚠ {w}")
    for e in errors:
        print(f"ERROR: {e}", file=sys.stderr)

    if errors:
        sys.exit(2)
    print("Output completeness check passed.")


if __name__ == '__main__':
    main()
