# HTML Report Template — MOVED

The live templates now live next to `build_html_report.py`:

- `scripts/html_templates/base.html` — page shell, CSS, top-level sections
- `scripts/html_templates/per_asin.html` — per-ASIN block layout
- `scripts/html_templates/rewrite.html` — single rewrite (title / bullet / description / backend)

**Edit those files directly if you need to change the visual structure.** This file is kept
only so outbound links from other references don't 404 — the former 27 KB template archive
was removed to eliminate a second source of truth.

The report JSON schema that `build_html_report.py` consumes is documented inline at the top
of `scripts/build_html_report.py`. Read there when assembling the report JSON.
