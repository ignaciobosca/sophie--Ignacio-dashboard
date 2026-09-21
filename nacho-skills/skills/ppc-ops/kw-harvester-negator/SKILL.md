---
name: kw-harvester-negator
description: Decide which Amazon Sponsored Products search terms to harvest into exact-match and which to negate, then tick the ones you want, choose where each lands, and export an Amazon Ads bulk-operations CSV (negatives + harvested keywords/ASINs) ready to upload. Pulls the Search Term report from Sophie Hub when connected, otherwise accepts an uploaded .xlsx; optionally reads your current Amazon SP bulk export to map campaign and ad-group names to IDs so the export is upload-ready. Output is a Sophie Society-branded interactive HTML action list with checkboxes, negate scope/match controls, and harvest destination/bid pickers. Trigger on uploads of Amazon search term reports, or phrases like harvest search terms, find negatives, negate wasted spend, what should I negate, what should I harvest, clean up my search terms, build a bulk file from search terms, export negatives to Amazon. Do NOT trigger for full-account gap analysis (that is ppc-expansion-finder) or dashboard visualization (that is search-term-dashboard).
---

# Amazon Keyword Harvester & Negator

**Self-contained skill.** This single SKILL.md file contains everything needed to run the skill — both Python scripts are embedded at the bottom between explicit fences. On first run, extract them to `scripts/peek.py` and `scripts/harvest_negate.py`.

Takes an Amazon SP Search Term Report as input — either pulled directly from **Sophie Hub** (preferred) via MCP or uploaded as an `.xlsx` — asks 4 setup questions, optionally clusters against a keyword research file, optionally reads the account's current Amazon SP bulk export to map names→IDs, and writes a dated Sophie Society-branded **interactive** HTML action list to the user's Downloads folder.

**Output:** one HTML file with four sections — Harvest (Keywords), Harvest (ASINs), Negate, Watch. The Harvest and Negate rows are interactive: each has a checkbox, and a sticky export bar builds an **Amazon Sponsored Products bulk-operations CSV** (the canonical 26-column schema) from only the ticked rows — ready to paste into Amazon Ads → Bulk Operations.

- **Negate rows** → `Negative Keyword` (ad-group scope) or `Campaign Negative Keyword` (whole-campaign scope) rows, Negative Exact or Negative Phrase, targeting the source ad group/campaign by ID.
- **Harvest keyword rows** → `Keyword` (Exact) `Create` rows added to a chosen existing ad group, at a CPC-derived bid.
- **Harvest ASIN rows** → `Product Targeting` (`asin="…"`) `Create` rows into a chosen ad group.
- **Funnel negatives** (optional toggle) → a Negative Exact of each harvested term in its source ad group, so source traffic flows to the new exact target.

Two destinations for harvests:

- **Add to an existing ad group** — the `Keyword`/`Product Targeting` CSV rows above (when you already have an exact campaign to grow).
- **Launch *new* campaigns** — the **Launch new campaigns →** button builds a ready **SP Bulk Builder** `BULK_INTAKE_DATA: {…}` intake payload from the ticked harvests: keyword themes grouped by cluster (exact-match keyword groups), harvested ASINs as competitor product targeting, and a CPC-derived bid. It opens in a modal with Copy / Download — paste it into a chat with the `sp-bulk-builder` skill to generate the full Sophie campaign architecture. Product / ASIN / SKUs are best-guessed from the campaign names and must be confirmed in SP Bulk Builder before generating.

Campaign/ad-group **IDs** come from the account's current bulk export (Step 1.5). Without it, the CSV rows export with names only (paste beneath a freshly downloaded Amazon template); the Launch payload does not need IDs (sp-bulk-builder creates everything new).

---

## Inputs

| Input | Status | What it's for | How it's provided |
|---|---|---|---|
| **SP Search Term Report** | **Required** | The data the whole analysis runs on (terms, clicks, spend, orders, ACOS, source campaign/ad group). | Pulled live from **Sophie Hub** (Step 0, preferred) or an uploaded `.xlsx` (Step 1). |
| **Current Amazon SP bulk export** (`.xlsx`) | **Recommended** | Maps campaign/ad-group **names → IDs** so negatives/harvests are upload-ready; powers the harvest **destination picker**; auto-detects your account's Negative Exact/Phrase wording. | Amazon Ads → Bulk Operations → download. Pass to `--bulk-export` (Step 1.5). |
| **Keyword research file** (`.xlsx`/`.csv`/`.txt`) | Optional | Clusters harvests into named themes and flags **strategic** terms to keep off the negate list. | Pass to `--kw-research` (Step 4). |

Settings collected in the interview (Step 3): **Target ACOS %** (required, no default), **Min clicks** (recommended value computed from account CVR), **Min orders** (default 1).

Without the bulk export the skill still runs — negatives export with names only and harvests can't pick a destination ad group, but the **Launch new campaigns** payload still works (sp-bulk-builder creates everything new).

---

## Installation (first run only)

Before running any of the workflow steps below, check whether the two Python scripts exist at the expected paths. If either is missing, extract it from the embedded code block at the bottom of this file using the Write tool:

- `<SKILL_DIR>/scripts/peek.py` — see the `### Embedded: scripts/peek.py` section below
- `<SKILL_DIR>/scripts/harvest_negate.py` — see the `### Embedded: scripts/harvest_negate.py` section below

`<SKILL_DIR>` is the directory containing this SKILL.md (typically `~/.claude/skills/kw-harvester-negator/`). The extraction is idempotent — if both files already exist, skip this step.

Python dependency: `openpyxl` (`pip install openpyxl`).

---

## Workflow

### Step 0 — Source the data: try Sophie Hub first

**Always ask about Sophie Hub first.** It's the preferred data source because it removes the manual export step.

Ask the user in a single message: *"Before we start — are you connected to Sophie Hub for this account? If yes, I can pull the Search Term report directly. Otherwise, just paste the path to an exported `.xlsx`."*

**If user says yes (or says "use Sophie Hub"):**

1. Verify the session is live:
   - Call `mcp__22c44a1b-73ce-432f-b5bb-70897f8bf7b3__verify_session` (this is Sophie Hub's session probe).
   - If it errors or returns unauthenticated, tell the user Sophie Hub isn't reachable right now and fall back to Step 1 (file upload). **Do not silently continue.**
2. List the user's connected stores with `mcp__22c44a1b-73ce-432f-b5bb-70897f8bf7b3__list_stores`. If there is more than one, show a numbered list and ask which.
3. Discover what's available for the selected store with `mcp__22c44a1b-73ce-432f-b5bb-70897f8bf7b3__discover_amazon_reports`. Look for a **Sponsored Products Search Term** report.
   - If the account has no SP search term data yet, tell the user plainly and fall back to file upload. Don't substitute a different report.
4. Pull the report:
   - Prefer `mcp__22c44a1b-73ce-432f-b5bb-70897f8bf7b3__get_ads_report_from_s3` if a signed URL / S3 path is available — download it as a `.xlsx` to a temp file.
   - Otherwise use `mcp__22c44a1b-73ce-432f-b5bb-70897f8bf7b3__get_amazon_report_data`, inspect the returned rows, and write them into a `.xlsx` that mirrors the Amazon schema (headers: `Customer Search Term`, `Campaign Name`, `Ad Group Name`, `Match Type`, `Targeting`, `Impressions`, `Clicks`, `Spend`, `7 Day Total Sales`, `7 Day Total Orders (#)`, `Total Advertising Cost of Sales (ACOS)`, `7 Day Conversion Rate`, `Currency`). Save to `~/Downloads/_sophiehub_search_terms_<store>_<date>.xlsx`.
5. Confirm back to the user: *"Pulled N rows from Sophie Hub for <store>. Continuing..."* and jump to **Step 2** with this file as the `<report_path>`.

**If user says no (or says "file" / "paste" / "I have a file"):**
Skip straight to Step 1.

**Session caching:** once verified in this conversation, don't probe again on subsequent runs. The next run starts directly at Step 2 with the same store assumed unless the user specifies otherwise.

### Step 1 — Locate the search term report (fallback)

Only reach this step if Sophie Hub is unavailable or the user opted out. If the user hasn't provided a path, ask. Accept paths to `.xlsx` exports from Amazon Ads Console → Reports → Sponsored Products → Search Term. Typical column headers include: `Customer Search Term`, `Clicks`, `Spend`, `7 Day Total Sales`, `7 Day Total Orders (#)`, `Total Advertising Cost of Sales (ACOS)`, `7 Day Conversion Rate`, `Campaign Name`, `Ad Group Name`, `Match Type`, `Targeting`.

### Step 1.5 — Ask for the current Amazon bulk export (recommended)

The Search Term Report names campaigns and ad groups but has **no IDs**. To make the exported negatives/harvests truly upload-ready, the classifier needs to map those names → Campaign IDs / Ad Group IDs. The cleanest source is the account's **current Amazon SP bulk download**:

> *"Optional but recommended: drop in your current Amazon Sponsored Products bulk export (Amazon Ads → Bulk Operations → download). I'll use it to fill in the campaign/ad-group IDs so the file you export is ready to upload as-is, and to give you a destination picker for the harvested keywords. Skip it and the export will carry names only — you'd paste those into a freshly downloaded template."*

Pass the path to `--bulk-export` in Step 4. It is a normal Amazon bulk `.xlsx` (sheet name like *Sponsored Products Campaigns*, columns `Entity`, `Campaign Id`, `Ad Group Id`, …). The parser is tolerant of `Id`/`ID` casing and large files, and auto-detects the account's own Negative Exact / Negative Phrase wording.

### Step 2 — Peek at the file to compute context

Run this before asking the interview questions so the min-clicks recommendation is grounded:

```bash
python <SKILL_DIR>/scripts/peek.py "<report_path>"
```

This prints a JSON blob with: row count, distinct campaigns, total spend, total orders, account-level avg CVR, avg CPC, currency symbol. Use these to:

- Confirm the file parsed (if not, ask the user to re-export).
- Compute the recommended min-clicks = `max(8, ceil(1.5 / avg_cvr))`. Example: 10% CVR → 15 clicks, 5% CVR → 30 clicks, 20% CVR → 8 clicks (floor).

### Step 3 — Ask the 4 interview questions in a single batched message

Show the file summary first (1-2 lines), then ask:

1. **Target ACOS %?** — the profitability threshold. No default; must be provided.
2. **Minimum clicks for a decision?** — recommend the computed value with reasoning: *"Your account avg CVR is X% → I suggest N clicks before negating (gives enough data to trust the zero-order signal). Override?"*
3. **Minimum orders to count as a harvest?** — default 1. Users running bigger accounts often want 2-3.
4. **Keyword research file? (optional)** — used only for semantic core tagging and the "don't negate strategic terms" safety flag. Skip freely if not available.

### Step 4 — Run the classifier

```bash
python <SKILL_DIR>/scripts/harvest_negate.py \
  --report "<report_path>" \
  --target-acos 30 \
  --min-clicks 15 \
  --min-orders 1 \
  --account-label "wobble-stool" \
  --kw-research "<optional_path>" \
  --bulk-export "<optional_current_bulk.xlsx>"
```

Flags:

- `--target-acos` — percent, e.g. `30` means 30%.
- `--min-clicks` — integer.
- `--min-orders` — integer, default 1.
- `--account-label` — slug used in the output filename.
- `--kw-research` — optional path to a `.xlsx` / `.csv` / `.txt` with keywords. Loose parsing: any column with > 5 unique short text values is treated as a KW column. If structured with Sophie-Society-style `🔎 "core" KWs` headers, those headers become cluster names directly.
- `--bulk-export` — optional path to the account's current Amazon SP bulk `.xlsx` (Step 1.5). Maps campaign/ad-group names → IDs so exported rows are upload-ready, and populates the harvest destination picker. Omit it and exports carry names only.

The script writes `~/Downloads/kw-harvest-<label>-<YYYY-MM-DD>.html` and prints a JSON summary (counts, wasted spend, `bulk_export_loaded`, `ad_groups_in_catalog`, `ids_resolved`, and the output path).

### Step 5 — Open the file and walk the user through the export

```bash
start "" "<output_path>"   # Windows (use the path the script printed)
```

Report the classification counts (harvest KW, harvest ASIN, negate waste, negate unprofitable, watch), total wasted spend, and potential harvest revenue. Then explain the **interactive export** — this is the whole point of the new flow:

1. Rows are **pre-ticked** (strategic-protected negatives start un-ticked). The user unticks anything to hold.
2. For each **negate** row they pick *Apply to* = **This ad group** (default) or **Whole campaign**, and *Match* = **Negative Exact** (default) or **Negative Phrase**.
3. For each **harvest** row they pick the destination ad group (defaults to the first Exact-named ad group from the bulk export) and a bid (defaults to the term's CPC).
4. The sticky **Build upload sheet** bar shows live counts and four buttons — **Negatives CSV**, **Harvests CSV**, **Combined CSV**, and **Launch new campaigns →** — plus an *Add funnel negatives* toggle. The three CSV buttons download an Amazon SP bulk-operations CSV of only the ticked rows.
5. To upload the CSVs: Amazon Ads → Bulk Operations → download a Sponsored Products bulk template → paste the exported rows beneath its header → upload (Amazon validates before applying).
6. **Launch new campaigns** is the alternative for harvests: it opens a modal with a ready `BULK_INTAKE_DATA: {…}` payload built from the ticked harvest rows. Copy it (or download the `.json`) and paste it into a chat where the `sp-bulk-builder` skill is active — it pre-fills the intake (exact keyword groups from the clusters, competitor PT from the ASINs, CPC bid) so you build brand-new campaigns instead of growing an existing ad group. Tell the user to confirm Product / ASIN / SKUs in SP Bulk Builder before it generates.

If `--bulk-export` was omitted, flag that the negatives carry names but no IDs, and that harvests can't pick a destination ad group for the CSV path — recommend re-running with the bulk export. (The Launch payload still works without it.)

---

## Classification rules (reference)

A search term row is classified into exactly one bucket, evaluated in this order:

| Bucket | Condition | Suggested action column |
|---|---|---|
| HARVEST | `orders ≥ min_orders` AND `clicks ≥ min_clicks` AND `acos ≤ target_acos` | Add as Exact keyword (or ASIN product target) to a chosen existing ad group |
| NEGATE — unprofitable | `orders ≥ 1` AND `clicks ≥ min_clicks` AND `acos > target_acos × 1.5` | Negative exact in the source ad group |
| NEGATE — wasted | `clicks ≥ min_clicks` AND `orders = 0` | Negative exact in the source ad group |
| WATCH | `orders ≥ 1` but below min thresholds, OR any row with `0 < clicks < min_clicks` AND `spend > 0` | — |
| (ignore) | Everything else (dead impressions, etc.) | — |

**Split harvest output:** rows where `search_term` starts with `b0` (case-insensitive) and is 10 chars long go into the **ASIN harvest** table; everything else goes into the **Keyword harvest** table.

**Dedup:** one row per unique (`search_term`, `ad_group`) pair — negation scope is ad-group-level, so the same term across different ad groups needs separate negative keywords.

**Bulk export → IDs (only when `--bulk-export` provided):** `parse_bulk_export` reads the account's current Amazon SP bulk `.xlsx` and builds `campaign_name→Campaign Id`, `(campaign, ad_group)→Ad Group Id`, an ad-group catalog (sorted Exact-named campaigns first, used for the harvest destination picker), and the account's own Negative Exact / Negative Phrase / Exact match-type wording. Each classified row is stamped with its **source** Campaign Id + Ad Group Id by name match; unmatched rows are flagged `no ID` in the UI and export with names only. All ID resolution and CSV assembly happen client-side in the HTML from an embedded JSON blob — nothing is exported until the user ticks rows and clicks an export button.

**Strategic-keyword safety flag (only when KW research provided):** if a term flagged for negation matches a keyword in the research file (exact string, case-insensitive), flip its recommendation to `"Don't negate — strategic. Raise bid or move to own campaign."` and keep it visible in a separate subsection of the Negate table.

**Cluster tagging (only when KW research provided):**

- If research file has Sophie Society-style `🔎 "core" KWs` columns, the header core names are the cluster labels. Each harvest term is tagged with the cluster whose KWs share the most trigrams with the harvest term.
- Otherwise, `scripts/harvest_negate.py` runs n-gram clustering on the research KWs (trigram overlap → bigram overlap fallback) and derives cluster names from the most frequent bigram per cluster.
- Terms with no matching cluster are tagged `uncategorized`.

---

## File layout

```
kw-harvester-negator/
  SKILL.md                  # THIS FILE — self-contained, embeds both scripts below
  scripts/                  # Extracted on first run from the code blocks at the bottom
    peek.py
    harvest_negate.py
```

No external assets, no HTML template file — `harvest_negate.py` emits the complete standalone HTML with inlined Sophie Society brand CSS, the interactive selection controls, the embedded data blob, and the client-side Amazon bulk-CSV export JS. Everything runs offline straight from the Downloads folder — no server, no CDN.

---

## Embedded: scripts/peek.py

Extract the following Python code block to `<SKILL_DIR>/scripts/peek.py` on first run.

```python
"""Quick-peek stats for the Amazon SP Search Term Report. Prints JSON to stdout."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

try:
    import openpyxl
except ImportError:
    print(json.dumps({"error": "openpyxl not installed. Run: pip install openpyxl"}))
    sys.exit(1)


CURRENCY_SYMBOLS = {"USD": "$", "GBP": "£", "EUR": "€", "JPY": "¥", "CAD": "CA$", "AUD": "A$", "MXN": "MX$", "BRL": "R$", "SEK": "kr", "PLN": "zł", "TRY": "₺", "INR": "₹", "AED": "د.إ", "SAR": "﷼", "SGD": "S$"}


def norm(s: str) -> str:
    return (s or "").strip().lower().replace("_", " ")


def find_col(headers: list[str], *patterns: str) -> int | None:
    lower = [norm(h) for h in headers]
    for p in patterns:
        p = p.lower()
        for i, h in enumerate(lower):
            if p in h:
                return i
    return None


def main(path: str) -> None:
    p = Path(path)
    if not p.exists():
        print(json.dumps({"error": f"File not found: {path}"}))
        sys.exit(1)

    import warnings as _w
    _w.filterwarnings("ignore", module="openpyxl")
    wb = openpyxl.load_workbook(p, data_only=True)
    # Search-term reports usually have one data sheet; pick the one with "search term" in name, else the largest
    sheet = None
    for ws in wb.worksheets:
        if "search" in ws.title.lower():
            sheet = ws
            break
    if sheet is None:
        sheet = max(wb.worksheets, key=lambda w: (w.max_row or 0))

    rows_iter = sheet.iter_rows(values_only=True)
    headers: list[str] = []
    # Skip blank leading rows (Amazon exports sometimes have a title row)
    for r in rows_iter:
        if r and any(c is not None and str(c).strip() for c in r):
            headers = [str(c) if c is not None else "" for c in r]
            # Must contain a plausible search-term column
            if find_col(headers, "customer search term", "search term") is not None:
                break
    if not headers:
        print(json.dumps({"error": "Could not locate header row with Customer Search Term column."}))
        sys.exit(1)

    i_clicks = find_col(headers, "clicks")
    i_spend = find_col(headers, "spend", "cost")
    i_orders = find_col(headers, "orders (#)", "total orders", "orders")
    i_sales = find_col(headers, "total sales", "sales")
    i_currency = find_col(headers, "currency")
    i_campaign = find_col(headers, "campaign name")

    clicks_total = 0
    spend_total = 0.0
    orders_total = 0
    sales_total = 0.0
    rows = 0
    currency_codes: set[str] = set()
    campaigns: set[str] = set()

    for r in rows_iter:
        if not r or all(c is None or str(c).strip() == "" for c in r):
            continue
        rows += 1
        try:
            if i_clicks is not None and r[i_clicks] is not None:
                clicks_total += int(float(r[i_clicks]))
        except (ValueError, TypeError):
            pass
        try:
            if i_spend is not None and r[i_spend] is not None:
                spend_total += float(r[i_spend])
        except (ValueError, TypeError):
            pass
        try:
            if i_orders is not None and r[i_orders] is not None:
                orders_total += int(float(r[i_orders]))
        except (ValueError, TypeError):
            pass
        try:
            if i_sales is not None and r[i_sales] is not None:
                sales_total += float(r[i_sales])
        except (ValueError, TypeError):
            pass
        if i_currency is not None and r[i_currency]:
            currency_codes.add(str(r[i_currency]).strip().upper())
        if i_campaign is not None and r[i_campaign]:
            campaigns.add(str(r[i_campaign]).strip())

    avg_cvr = (orders_total / clicks_total) if clicks_total else 0.0
    avg_cpc = (spend_total / clicks_total) if clicks_total else 0.0
    recommended_min_clicks = max(8, int(math.ceil(1.5 / avg_cvr))) if avg_cvr > 0 else 15

    currency = next(iter(currency_codes), "USD") if currency_codes else "USD"
    symbol = CURRENCY_SYMBOLS.get(currency, currency + " ")

    out = {
        "rows": rows,
        "distinct_campaigns": len(campaigns),
        "total_spend": round(spend_total, 2),
        "total_sales": round(sales_total, 2),
        "total_clicks": clicks_total,
        "total_orders": orders_total,
        "avg_cvr_pct": round(avg_cvr * 100, 2),
        "avg_cpc": round(avg_cpc, 2),
        "currency": currency,
        "currency_symbol": symbol,
        "recommended_min_clicks": recommended_min_clicks,
        "min_clicks_rationale": f"avg CVR {round(avg_cvr*100,1)}% → ~{recommended_min_clicks} clicks to trust a zero-order signal",
    }
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "usage: python peek.py <report.xlsx>"}))
        sys.exit(1)
    main(sys.argv[1])
```

---

## Embedded: scripts/harvest_negate.py

Extract the following Python code block to `<SKILL_DIR>/scripts/harvest_negate.py` on first run.

```python
"""Classify each row of an Amazon SP Search Term Report into harvest/negate/watch,
optionally cluster harvests against a keyword-research file, and render a
Sophie Society-branded HTML action list.

The HTML is interactive: every harvest/negate row has a checkbox plus controls
to choose WHERE the action lands (ad-group vs campaign-level negative; which
destination ad group + bid for a harvest). The export buttons assemble an
Amazon Sponsored Products **bulk-operations CSV** (the canonical 26-column
schema) from only the ticked rows, client-side. Optionally reads the user's
current Amazon SP bulk export to map campaign/ad-group NAMES -> IDs so the rows
are upload-ready."""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import math
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

try:
    import openpyxl
except ImportError:
    sys.exit("openpyxl not installed. Run: pip install openpyxl")


CURRENCY_SYMBOLS = {"USD": "$", "GBP": "£", "EUR": "€", "JPY": "¥", "CAD": "CA$", "AUD": "A$", "MXN": "MX$", "BRL": "R$", "SEK": "kr", "PLN": "zł", "TRY": "₺", "INR": "₹", "AED": "د.إ", "SAR": "﷼", "SGD": "S$"}

STOPWORDS = {"the","a","an","and","or","for","of","with","to","in","on","at","by","is","are","was","were","be","been","best","new","top","very","my","your","our","from","this","that","these","those","it","as","but","if","so","no","not","do","does"}

ASIN_RE = re.compile(r"^b0[a-z0-9]{8}$", re.IGNORECASE)

# Canonical 26-column Amazon SP bulk-operations schema (matches sp-bulk-builder output).
BULK_COLS = [
    "Product", "Entity", "Operation", "Campaign ID", "Ad Group ID", "Portfolio ID",
    "Ad ID", "Keyword ID", "Product Targeting ID", "Campaign Name", "Ad Group Name",
    "Start Date", "End Date", "Targeting Type", "State", "Daily Budget", "SKU", "ASIN",
    "Ad Group Default Bid", "Bid", "Keyword Text", "Match Type", "Bidding Strategy",
    "Placement", "Percentage", "Product Targeting Expression",
]

# --- SP Bulk Builder hand-off (launch NEW campaigns from harvested winners) ---
# Placement defaults mirror sp-bulk-builder's intake form.
SP_PLACEMENT_DEFAULTS = {
    "kw": {"tos": 66, "ros": 33, "pdp": 0},
    "pt": {"tos": 0, "ros": 0, "pdp": 66},
    "auto_close_loose": {"tos": 66, "ros": 33, "pdp": 0},
    "auto_subs_comps": {"tos": 0, "ros": 0, "pdp": 66},
}
# Harvest = promote proven terms to EXACT. Pre-select exact keyword groups + competitor PT only.
LAUNCH_CAMPAIGNS = {
    "close_match": False, "loose_match": False, "substitutes": False, "complements": False,
    "kg_broad": False, "kg_phrase": False, "kg_exact": True,
    "sk_broad": False, "sk_phrase": False, "sk_exact": False,
    "pt_asin_exact": True, "pt_asin_expanded": False,
    "brand_kwg_broad": False, "brand_kwg_phrase": False, "brand_kwg_exact": False,
    "brand_only": False, "catch_all": False,
}


# ---------- helpers ----------

def norm(s) -> str:
    return (str(s) if s is not None else "").strip().lower().replace("_", " ")


def as_float(v) -> float:
    if v is None or v == "":
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace(",", "").replace("%", "")
    try:
        return float(s)
    except ValueError:
        return 0.0


def as_int(v) -> int:
    return int(as_float(v))


def pct(v) -> float:
    """Normalize a percent field — Amazon sometimes exports 30 (meaning 30%), sometimes 0.30."""
    f = as_float(v)
    if f > 1.5:  # already a percent like 30
        return f
    return f * 100.0


def find_col(headers: list[str], *patterns: str) -> int | None:
    lower = [norm(h) for h in headers]
    for p in patterns:
        p = p.lower()
        for i, h in enumerate(lower):
            if p == h:
                return i
        for i, h in enumerate(lower):
            if p in h:
                return i
    return None


# ---------- parse search term report ----------

def parse_report(path: Path) -> tuple[list[dict], dict]:
    import warnings as _w
    _w.filterwarnings("ignore", module="openpyxl")
    wb = openpyxl.load_workbook(path, data_only=True)
    sheet = None
    for ws in wb.worksheets:
        if "search" in ws.title.lower():
            sheet = ws
            break
    if sheet is None:
        sheet = max(wb.worksheets, key=lambda w: (w.max_row or 0))

    rows_iter = sheet.iter_rows(values_only=True)
    headers: list[str] = []
    for r in rows_iter:
        if r and any(c is not None and str(c).strip() for c in r):
            headers = [str(c) if c is not None else "" for c in r]
            if find_col(headers, "customer search term", "search term") is not None:
                break
    if not headers:
        sys.exit("Could not find header row. Is this an Amazon SP Search Term Report?")

    idx = {
        "search_term": find_col(headers, "customer search term", "search term"),
        "campaign": find_col(headers, "campaign name"),
        "ad_group": find_col(headers, "ad group name", "ad group"),
        "targeting": find_col(headers, "targeting"),
        "match_type": find_col(headers, "match type"),
        "impressions": find_col(headers, "impressions"),
        "clicks": find_col(headers, "clicks"),
        "spend": find_col(headers, "spend", "cost"),
        "orders": find_col(headers, "orders (#)", "total orders", "orders"),
        "sales": find_col(headers, "total sales", "sales"),
        "acos": find_col(headers, "advertising cost of sales", "acos"),
        "cvr": find_col(headers, "conversion rate"),
        "cpc": find_col(headers, "cost per click", "cpc"),
        "currency": find_col(headers, "currency"),
    }
    if idx["search_term"] is None:
        sys.exit("Missing 'Customer Search Term' column.")

    rows: list[dict] = []
    currencies: Counter = Counter()
    total_spend = 0.0
    total_sales = 0.0
    total_clicks = 0
    total_orders = 0

    for r in rows_iter:
        if not r or all(c is None or str(c).strip() == "" for c in r):
            continue
        term_raw = r[idx["search_term"]] if idx["search_term"] is not None else ""
        term = (str(term_raw) if term_raw is not None else "").strip()
        if not term:
            continue
        clicks = as_int(r[idx["clicks"]]) if idx["clicks"] is not None else 0
        spend = as_float(r[idx["spend"]]) if idx["spend"] is not None else 0.0
        orders = as_int(r[idx["orders"]]) if idx["orders"] is not None else 0
        sales = as_float(r[idx["sales"]]) if idx["sales"] is not None else 0.0
        impressions = as_int(r[idx["impressions"]]) if idx["impressions"] is not None else 0
        acos = pct(r[idx["acos"]]) if idx["acos"] is not None and r[idx["acos"]] not in (None, "") else (spend / sales * 100 if sales > 0 else 0.0)
        cvr = pct(r[idx["cvr"]]) if idx["cvr"] is not None and r[idx["cvr"]] not in (None, "") else (orders / clicks * 100 if clicks > 0 else 0.0)
        cpc = as_float(r[idx["cpc"]]) if idx["cpc"] is not None else (spend / clicks if clicks > 0 else 0.0)
        if idx["currency"] is not None and r[idx["currency"]]:
            currencies[str(r[idx["currency"]]).strip().upper()] += 1

        rows.append({
            "search_term": term,
            "search_term_norm": term.lower().strip(),
            "campaign": str(r[idx["campaign"]]).strip() if idx["campaign"] is not None and r[idx["campaign"]] else "",
            "ad_group": str(r[idx["ad_group"]]).strip() if idx["ad_group"] is not None and r[idx["ad_group"]] else "",
            "targeting": str(r[idx["targeting"]]).strip() if idx["targeting"] is not None and r[idx["targeting"]] else "",
            "match_type": str(r[idx["match_type"]]).strip() if idx["match_type"] is not None and r[idx["match_type"]] else "",
            "impressions": impressions,
            "clicks": clicks,
            "spend": spend,
            "orders": orders,
            "sales": sales,
            "acos": acos,
            "cvr": cvr,
            "cpc": cpc,
        })
        total_spend += spend
        total_sales += sales
        total_clicks += clicks
        total_orders += orders

    currency = currencies.most_common(1)[0][0] if currencies else "USD"
    stats = {
        "row_count": len(rows),
        "currency": currency,
        "symbol": CURRENCY_SYMBOLS.get(currency, currency + " "),
        "total_spend": total_spend,
        "total_sales": total_sales,
        "total_clicks": total_clicks,
        "total_orders": total_orders,
        "avg_cvr": (total_orders / total_clicks) if total_clicks else 0.0,
        "avg_cpc": (total_spend / total_clicks) if total_clicks else 0.0,
    }
    return rows, stats


# ---------- parse the account's current Amazon SP bulk export (for name -> ID) ----------

def parse_bulk_export(path: Path) -> dict:
    """Read the user's current Amazon SP bulk download and build:
      - campaign_id_by_name: {campaign_name_norm: campaign_id}
      - adgroup_id_by_key:   {(campaign_norm, ad_group_norm): ad_group_id}
      - ad_groups:           [{camp, campId, ag, agId, tt, exact}]  (for the harvest destination picker)
      - conv:                detected match-type strings used by this account
    Tolerant of header casing ('Campaign Id' vs 'Campaign ID') and of large files."""
    import warnings as _w
    _w.filterwarnings("ignore", module="openpyxl")
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)

    # Prefer the SP Campaigns sheet; else the largest.
    sheet = None
    for ws in wb.worksheets:
        t = ws.title.lower()
        if "sponsored product" in t or "campaign" in t:
            sheet = ws
            break
    if sheet is None:
        sheet = max(wb.worksheets, key=lambda w: (w.max_row or 0))

    rows_iter = sheet.iter_rows(values_only=True)
    headers: list[str] = []
    for r in rows_iter:
        if r and any(c is not None and str(c).strip() for c in r):
            cand = [str(c) if c is not None else "" for c in r]
            if find_col(cand, "campaign id") is not None and find_col(cand, "entity") is not None:
                headers = cand
                break
    if not headers:
        sys.exit("Could not find the bulk header row (need 'Entity' + 'Campaign Id'). Is this an Amazon SP bulk export?")

    ix = {
        "entity": find_col(headers, "entity"),
        "campaign_id": find_col(headers, "campaign id"),
        "ad_group_id": find_col(headers, "ad group id"),
        "campaign_name": find_col(headers, "campaign name"),
        "ad_group_name": find_col(headers, "ad group name"),
        "targeting_type": find_col(headers, "targeting type"),
        "match_type": find_col(headers, "match type"),
    }

    def cell(r, key):
        i = ix[key]
        if i is None or i >= len(r):
            return ""
        v = r[i]
        return "" if v is None else str(v).strip()

    campaign_id_by_name: dict[str, str] = {}
    adgroup_id_by_key: dict[tuple[str, str], str] = {}
    camp_tt: dict[str, str] = {}
    ag_seen: set[tuple[str, str]] = set()
    ad_groups: list[dict] = []
    neg_exact = neg_phrase = pos_exact = ""

    for r in rows_iter:
        if not r:
            continue
        entity = cell(r, "entity")
        camp_name = cell(r, "campaign_name")
        camp_id = cell(r, "campaign_id")
        ag_name = cell(r, "ad_group_name")
        ag_id = cell(r, "ad_group_id")
        mt = cell(r, "match_type")
        tt = cell(r, "targeting_type")

        if camp_name and camp_id:
            campaign_id_by_name.setdefault(norm(camp_name), camp_id)
        if entity.lower() == "campaign" and camp_name and tt:
            camp_tt[norm(camp_name)] = tt
        if camp_name and ag_name and ag_id:
            key = (norm(camp_name), norm(ag_name))
            adgroup_id_by_key.setdefault(key, ag_id)
            if key not in ag_seen:
                ag_seen.add(key)
                ad_groups.append({"camp": camp_name, "campId": camp_id, "ag": ag_name, "agId": ag_id})

        # Detect this account's match-type wording.
        low = mt.lower()
        if "negative" in low and "exact" in low and not neg_exact:
            neg_exact = mt
        elif "negative" in low and "phrase" in low and not neg_phrase:
            neg_phrase = mt
        elif low == "exact" and not pos_exact:
            pos_exact = mt

    # Attach campaign targeting type + flag likely-exact ad groups (for default destination ordering).
    for ag in ad_groups:
        tt = camp_tt.get(norm(ag["camp"]), "")
        ag["tt"] = tt
        name_l = ag["camp"].lower()
        ag["exact"] = ("exact" in name_l) or ("| ex" in name_l) or (" ex " in name_l)

    # Stable sort: exact campaigns first, then alpha — nicest default for the destination picker.
    ad_groups.sort(key=lambda a: (not a["exact"], a["camp"].lower(), a["ag"].lower()))

    return {
        "campaign_id_by_name": campaign_id_by_name,
        "adgroup_id_by_key": adgroup_id_by_key,
        "ad_groups": ad_groups,
        "conv": {
            "negExact": neg_exact or "Negative Exact",
            "negPhrase": neg_phrase or "Negative Phrase",
            "posExact": pos_exact or "Exact",
        },
    }


def resolve_ids(rows: list[dict], bulk: dict | None) -> None:
    """Stamp source campaign_id / ad_group_id onto each row from the bulk export (by name)."""
    for r in rows:
        cid = aid = ""
        if bulk:
            cid = bulk["campaign_id_by_name"].get(norm(r["campaign"]), "")
            aid = bulk["adgroup_id_by_key"].get((norm(r["campaign"]), norm(r["ad_group"])), "")
        r["campaign_id"] = cid
        r["ad_group_id"] = aid
        r["id_resolved"] = bool(cid and aid)


# ---------- dedup by (term, ad_group) ----------

def dedup_rows(rows: list[dict]) -> list[dict]:
    agg: dict[tuple[str, str], dict] = {}
    for r in rows:
        key = (r["search_term_norm"], r["ad_group"].lower())
        if key not in agg:
            agg[key] = dict(r)
            continue
        a = agg[key]
        a["impressions"] += r["impressions"]
        a["clicks"] += r["clicks"]
        a["spend"] += r["spend"]
        a["orders"] += r["orders"]
        a["sales"] += r["sales"]
        # Recompute rates
        a["acos"] = (a["spend"] / a["sales"] * 100) if a["sales"] > 0 else 0.0
        a["cvr"] = (a["orders"] / a["clicks"] * 100) if a["clicks"] > 0 else 0.0
        a["cpc"] = (a["spend"] / a["clicks"]) if a["clicks"] > 0 else 0.0
    return list(agg.values())


# ---------- classification ----------

def classify(rows: list[dict], target_acos: float, min_clicks: int, min_orders: int) -> list[dict]:
    for r in rows:
        c, o, a, s = r["clicks"], r["orders"], r["acos"], r["spend"]
        term = r["search_term"].strip()
        is_asin = bool(ASIN_RE.match(term.replace(" ", "")))

        if o >= min_orders and c >= min_clicks and a <= target_acos and a > 0:
            r["bucket"] = "harvest"
            r["subtype"] = "asin" if is_asin else "keyword"
            r["reason"] = f"{o} orders @ {a:.1f}% ACOS (≤ {target_acos:.0f}% target)"
        elif o >= 1 and c >= min_clicks and a > target_acos * 1.5:
            r["bucket"] = "negate"
            r["subtype"] = "unprofitable"
            r["reason"] = f"ACOS {a:.1f}% > {target_acos*1.5:.0f}% ({o} orders, {s:.2f} spend)"
        elif c >= min_clicks and o == 0:
            r["bucket"] = "negate"
            r["subtype"] = "wasted"
            r["reason"] = f"{c} clicks, 0 orders, {s:.2f} wasted"
        elif o >= 1 and (o < min_orders or c < min_clicks):
            r["bucket"] = "watch"
            r["subtype"] = "early_signal"
            r["reason"] = f"{o} orders but below thresholds (clicks {c}, need {min_clicks})"
        elif 0 < c < min_clicks and s > 0:
            r["bucket"] = "watch"
            r["subtype"] = "insufficient_data"
            r["reason"] = f"{c} clicks — not enough data yet"
        else:
            r["bucket"] = "ignore"
            r["subtype"] = ""
            r["reason"] = ""
    return rows


# ---------- keyword research parsing + clustering ----------

def parse_kw_research(path: Path) -> tuple[list[str], dict[str, list[str]]]:
    """Return (flat_kw_list, cluster_map). cluster_map: {cluster_name: [kw,...]}.
    If the file is a Sophie Society-style sheet with 🔎 "core" KWs column headers,
    those become the cluster map directly."""
    suffix = path.suffix.lower()
    kws: list[str] = []
    clusters: dict[str, list[str]] = {}

    if suffix in {".txt", ".csv"}:
        text = path.read_text(encoding="utf-8", errors="ignore")
        for line in text.splitlines():
            for part in re.split(r"[,;\t]", line):
                p = part.strip().strip('"').lower()
                if 2 <= len(p) <= 80 and any(ch.isalpha() for ch in p):
                    kws.append(p)
        return list(dict.fromkeys(kws)), clusters

    if suffix in {".xlsx", ".xlsm"}:
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        for ws in wb.worksheets:
            header_row: list[str] = []
            col_kws: dict[int, list[str]] = defaultdict(list)
            for i, row in enumerate(ws.iter_rows(values_only=True)):
                if not row:
                    continue
                if i == 0:
                    header_row = [str(c) if c is not None else "" for c in row]
                    continue
                for j, val in enumerate(row):
                    if val is None:
                        continue
                    s = str(val).strip().lower()
                    if 2 <= len(s) <= 80 and any(ch.isalpha() for ch in s):
                        col_kws[j].append(s)
            # Pick columns that look like keyword lists (≥5 distinct short strings)
            for j, vals in col_kws.items():
                if len(set(vals)) < 5:
                    continue
                header = header_row[j] if j < len(header_row) else ""
                m = re.search(r'"([^"]+)"', header) or re.search(r"'([^']+)'", header)
                if m:
                    clusters.setdefault(m.group(1).strip().lower(), []).extend(vals)
                kws.extend(vals)
        return list(dict.fromkeys(kws)), {k: list(dict.fromkeys(v)) for k, v in clusters.items()}

    return [], {}


def ngrams(s: str, n: int) -> set[tuple[str, ...]]:
    toks = [t for t in re.findall(r"[a-z0-9]+", s.lower()) if t not in STOPWORDS and len(t) > 1]
    if len(toks) < n:
        return set()
    return {tuple(toks[i:i+n]) for i in range(len(toks) - n + 1)}


def cluster_keywords(kws: list[str]) -> dict[str, list[str]]:
    """Greedy n-gram clustering: trigrams first, then bigrams, then leftover."""
    if not kws:
        return {}
    remaining = list(dict.fromkeys(kws))
    clusters: dict[str, list[str]] = {}

    for n in (3, 2):
        gram_to_kws: dict[tuple, list[str]] = defaultdict(list)
        for k in remaining:
            for g in ngrams(k, n):
                gram_to_kws[g].append(k)
        # Sort by size desc, take large groups
        sorted_grams = sorted(gram_to_kws.items(), key=lambda x: -len(x[1]))
        used: set[str] = set()
        for gram, members in sorted_grams:
            free = [m for m in members if m not in used]
            if len(free) < 3:
                continue
            label = " ".join(gram)
            clusters.setdefault(label, []).extend(free)
            used.update(free)
        remaining = [k for k in remaining if k not in used]

    if remaining:
        clusters["uncategorized"] = remaining

    return {k: list(dict.fromkeys(v)) for k, v in clusters.items()}


def tag_term_with_cluster(term: str, clusters: dict[str, list[str]]) -> str:
    """Pick the cluster whose KWs share the most bigrams/trigrams with `term`."""
    if not clusters:
        return ""
    term_tri = ngrams(term, 3)
    term_bi = ngrams(term, 2)
    best_label, best_score = "", 0
    for label, kws in clusters.items():
        if label == "uncategorized":
            continue
        score = 0
        for kw in kws:
            score += len(term_tri & ngrams(kw, 3)) * 3
            score += len(term_bi & ngrams(kw, 2))
        if score > best_score:
            best_score, best_label = score, label
    return best_label if best_score > 0 else "uncategorized"


# ---------- rendering ----------

BRAND_CSS = """
:root{
  --navy:#0A2333;--navy-soft:#1D1F1E;--off-white:#F3F3F1;--white:#FFFFFF;--cream:#FAF9F5;
  --text:#212121;--text-2:#666666;--green:#13835B;--green-soft:#E1F0E9;--green-tint:#F0F8F4;
  --orange:#EA6C34;--orange-soft:#FDE5CF;--orange-tint:#FFF5EF;--peach:#F9C8A5;
  --light-blue:#C2D9E6;--blue-tint:#EEF5FA;--beige:#E9E2D9;--border:#E6E6E6;
  --radius-sm:4px;--radius-md:8px;--radius-lg:12px;
  --shadow-soft:0 2px 8px rgba(10,35,51,.06);
  --shadow-hero:0 4px 24px rgba(10,35,51,.10);
}
*{box-sizing:border-box}
html,body{margin:0;padding:0}
body{font-family:'BROmega','BR Omega','Inter','DM Sans',-apple-system,system-ui,Segoe UI,Roboto,sans-serif;background:var(--off-white);color:var(--text);font-size:15px;line-height:1.6}
h1,h2,h3,h4{color:var(--navy);font-weight:700;letter-spacing:-0.015em;margin:0}
h1{font-size:36px;line-height:1.15}
h2{font-size:26px;line-height:1.25}
h3{font-size:18px}
h4{font-size:12px;text-transform:uppercase;letter-spacing:.08em;color:var(--text-2);font-weight:700}
.container{max-width:1320px;margin:0 auto;padding:0 32px 48px}

/* Hero */
.hero{background:var(--navy);color:var(--white);padding:48px 0 52px;margin-bottom:40px;position:relative;overflow:hidden}
.hero::before{content:"";position:absolute;top:0;right:-120px;width:380px;height:380px;background:radial-gradient(circle,rgba(234,108,52,.18) 0%,rgba(234,108,52,0) 70%);pointer-events:none}
.hero-inner{max-width:1320px;margin:0 auto;padding:0 32px;position:relative;z-index:1}
.hero .eyebrow{color:var(--peach);font-size:12px;text-transform:uppercase;letter-spacing:.12em;font-weight:700;margin-bottom:12px}
.hero h1{color:var(--white);font-size:40px}
.hero .brand-rule{background:var(--orange);height:3px;width:60px;border-radius:2px;margin:14px 0 18px}
.hero .tag{color:rgba(255,255,255,.72);font-size:15px;max-width:680px}
.hero .meta{display:flex;gap:28px;margin-top:22px;color:rgba(255,255,255,.85);font-size:13px}
.hero .meta strong{color:var(--white);font-weight:700}

/* Executive summary ribbon */
.summary{background:var(--white);border:1px solid var(--border);border-radius:var(--radius-lg);padding:28px 32px;margin-top:-34px;margin-bottom:32px;box-shadow:var(--shadow-hero);position:relative;z-index:2}
.summary h4{margin-bottom:14px}
.summary p{margin:0;font-size:16px;line-height:1.65;color:var(--text)}
.summary .hilite-green{color:var(--green);font-weight:700}
.summary .hilite-orange{color:var(--orange);font-weight:700}

/* Setup card */
.setup-card{background:var(--white);border:1px solid var(--border);border-radius:var(--radius-lg);padding:22px 26px;margin-bottom:32px}
.setup{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:22px}
.setup .k{color:var(--text-2);text-transform:uppercase;font-size:10.5px;letter-spacing:.08em;font-weight:700}
.setup .v{color:var(--navy);font-weight:700;font-size:17px;margin-top:4px;font-variant-numeric:tabular-nums}

/* KPI row */
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:18px;margin-bottom:40px}
.kpi{background:var(--white);border:1px solid var(--border);border-radius:var(--radius-lg);padding:22px 24px;position:relative;overflow:hidden;transition:transform .15s ease-out,box-shadow .15s ease-out;isolation:isolate}
.kpi::before{content:"";position:absolute;left:0;top:0;bottom:0;width:4px;background:var(--beige)}
.kpi.good::before{background:var(--green)}
.kpi.warn::before{background:var(--orange)}
.kpi.info::before{background:var(--light-blue)}
.kpi .lbl{color:var(--text-2);font-size:11px;text-transform:uppercase;letter-spacing:.08em;font-weight:700}
.kpi .val{color:var(--navy);font-size:44px;font-weight:700;margin-top:6px;line-height:1;font-variant-numeric:tabular-nums;letter-spacing:-0.02em}
.kpi.good .val{color:var(--green)}
.kpi.warn .val{color:var(--orange)}
.kpi .sub{color:var(--text-2);font-size:13px;margin-top:10px;line-height:1.4}

/* Export bar (sticky) */
.export-bar{position:sticky;top:0;z-index:20;background:var(--navy);color:var(--white);border-radius:var(--radius-lg);padding:16px 22px;margin-bottom:8px;box-shadow:var(--shadow-hero);display:flex;flex-wrap:wrap;align-items:center;gap:14px}
.export-bar .eb-title{font-weight:700;color:var(--white);font-size:14px;margin-right:4px}
.export-bar .eb-count{display:inline-flex;align-items:center;gap:6px;background:rgba(255,255,255,.10);border-radius:9999px;padding:5px 12px;font-size:12px;font-weight:700}
.export-bar .eb-count b{font-variant-numeric:tabular-nums}
.export-bar .eb-spacer{flex:1}
.export-bar label.eb-toggle{display:inline-flex;align-items:center;gap:8px;font-size:12.5px;color:rgba(255,255,255,.88);cursor:pointer;user-select:none}
.export-bar button.btn{min-height:40px}
.eb-hint{color:rgba(255,255,255,.6);font-size:11.5px;flex-basis:100%}
.eb-hint strong{color:rgba(255,255,255,.85)}

/* Launch modal (SP Bulk Builder hand-off) */
.modal-overlay{position:fixed;inset:0;background:rgba(10,35,51,.55);display:none;align-items:center;justify-content:center;z-index:100;padding:24px}
.modal-card{background:var(--white);border-radius:var(--radius-lg);max-width:780px;width:100%;max-height:86vh;overflow:auto;padding:28px 30px;box-shadow:var(--shadow-hero)}
.modal-card h3{margin-bottom:4px;font-size:20px}
.modal-card p{font-size:13px;color:var(--text-2);margin:8px 0 14px;line-height:1.6}
.modal-card p strong{color:var(--navy)}
.modal-card textarea{width:100%;min-height:240px;font-family:ui-monospace,Menlo,Consolas,'Courier New',monospace;font-size:12px;border:1px solid var(--border);border-radius:var(--radius-md);padding:12px;background:var(--cream);color:var(--text);resize:vertical;white-space:pre}
.modal-actions{display:flex;gap:10px;margin-top:14px;flex-wrap:wrap}

/* Section headers */
.section{margin-top:44px}
.section-head{display:flex;align-items:flex-end;justify-content:space-between;gap:20px;margin-bottom:14px}
.section-head .title-block{flex:1}
.section-head h2{display:flex;align-items:center;gap:12px}
.section-head .brand-rule{height:3px;width:44px;background:var(--orange);border-radius:2px;margin-top:8px}
.section-head .actions{display:flex;gap:10px;align-items:center}
.count-pill{background:var(--navy);color:var(--white);padding:4px 12px;border-radius:9999px;font-size:12px;font-weight:700;letter-spacing:.02em;min-width:28px;text-align:center}
.count-pill.muted{background:var(--beige);color:var(--navy)}
.sel-links{font-size:12px;color:var(--text-2)}
.sel-links a{color:var(--green);font-weight:700;cursor:pointer;text-decoration:none}
.sel-links a:hover{text-decoration:underline}

/* Buttons */
button.btn{background:var(--green);color:var(--white);border:none;padding:12px 22px;border-radius:var(--radius-md);font-weight:700;font-size:13px;cursor:pointer;font-family:inherit;letter-spacing:.01em;min-height:44px;min-width:44px;transition:background .15s ease-out,transform .1s ease-out}
button.btn:active{transform:translateY(1px)}
button.btn.secondary{background:var(--white);color:var(--navy);border:1px solid var(--border)}
button.btn.warn{background:var(--orange)}
button.btn:focus-visible,details>summary:focus-visible{outline:2px solid var(--peach);outline-offset:2px}

/* Form controls inside tables */
input[type=checkbox].rowchk{width:18px;height:18px;accent-color:var(--green);cursor:pointer}
select.cell-select,input.cell-bid{font-family:inherit;font-size:12px;padding:5px 8px;border:1px solid var(--border);border-radius:6px;background:var(--white);color:var(--text);max-width:240px}
input.cell-bid{width:78px;text-align:right;font-variant-numeric:tabular-nums}
select.cell-select:focus,input.cell-bid:focus{outline:2px solid var(--light-blue);outline-offset:1px}

/* Tables */
.table-wrap{background:var(--white);border:1px solid var(--border);border-radius:var(--radius-lg);overflow:hidden}
.scroll{max-height:640px;overflow:auto}
table{border-collapse:collapse;width:100%;font-size:13px}
th,td{padding:11px 14px;vertical-align:middle;text-align:left;border-bottom:1px solid var(--border)}
th{background:var(--cream);color:var(--navy);font-weight:700;font-size:10.5px;letter-spacing:.08em;text-transform:uppercase;position:sticky;top:0;z-index:1;border-bottom:2px solid var(--border)}
tbody tr:nth-child(even) td{background:var(--cream)}
td.num{text-align:right;font-variant-numeric:tabular-nums}
td.chk,th.chk{text-align:center;width:42px}
.row-harvest td:first-child{border-left:3px solid var(--green)}
.row-negate td:first-child{border-left:3px solid var(--orange)}
.row-strategic td:first-child{border-left:3px solid var(--light-blue)}

/* Pills */
.pill{display:inline-block;padding:3px 10px;border-radius:9999px;font-size:10.5px;font-weight:700;letter-spacing:.03em;text-transform:uppercase;white-space:nowrap}
.p-green{background:var(--green-soft);color:var(--green)}
.p-orange{background:var(--orange-soft);color:var(--orange)}
.p-red{background:#FDE8E0;color:var(--orange)}
.p-blue{background:var(--light-blue);color:var(--navy)}
.p-gray{background:var(--beige);color:var(--text-2)}
.id-flag{font-size:9.5px;padding:2px 7px;margin-left:6px}

/* Banners */
.strategic-banner{background:var(--blue-tint);color:var(--navy);padding:14px 20px;border-radius:var(--radius-md);font-size:14px;margin-bottom:14px;border-left:4px solid var(--light-blue);display:flex;align-items:center;gap:12px}
.strategic-banner strong{color:var(--navy);font-weight:700}
.strategic-banner .icon{background:var(--light-blue);color:var(--navy);width:28px;height:28px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;font-weight:700;flex-shrink:0}
.warn-banner{background:var(--orange-tint);color:var(--navy);padding:12px 18px;border-radius:var(--radius-md);font-size:13px;margin-bottom:14px;border-left:4px solid var(--orange)}

/* Empty state */
.empty{color:var(--text-2);padding:32px;text-align:center;font-size:14px}
.empty .big{display:block;color:var(--navy);font-weight:700;font-size:16px;margin-bottom:6px}

/* Details summary */
details{margin-top:6px}
details summary{cursor:pointer;color:var(--navy);font-weight:700;padding:10px 14px;background:var(--white);border:1px solid var(--border);border-radius:var(--radius-md);list-style:none;font-size:13px;user-select:none}
details summary::-webkit-details-marker{display:none}
details summary::before{content:"▸ ";color:var(--orange);font-size:14px;margin-right:4px}
details[open] summary::before{content:"▾ "}

/* Next-steps footer card */
.next-steps{background:var(--navy);color:var(--white);border-radius:var(--radius-lg);padding:32px 36px;margin-top:48px}
.next-steps h3{color:var(--white);font-size:20px;margin-bottom:6px}
.next-steps .brand-rule{background:var(--orange);height:3px;width:44px;border-radius:2px;margin:10px 0 18px}
.next-steps ol{margin:0;padding-left:20px;color:rgba(255,255,255,.88);font-size:14px}
.next-steps ol li{margin-bottom:8px}
.next-steps ol li strong{color:var(--white)}

footer.page-footer{color:var(--text-2);font-size:12px;text-align:center;padding:28px 0 14px}
footer.page-footer .dot{margin:0 8px;color:var(--border)}

/* Hover effects only on devices that truly hover (not touch) */
@media (hover: hover) and (pointer: fine){
  .kpi:hover{transform:translateY(-1px);box-shadow:var(--shadow-soft)}
  button.btn:hover{background:#0F6D4B}
  button.btn.secondary:hover{background:var(--cream)}
  button.btn.warn:hover{background:#D85A24}
  tbody tr:hover td{background:var(--blue-tint)}
}

/* Respect the user's motion preference */
@media (prefers-reduced-motion: reduce){
  *,*::before,*::after{
    transition-duration:.01ms !important;
    animation-duration:.01ms !important;
    animation-iteration-count:1 !important;
    scroll-behavior:auto !important;
  }
  .kpi:hover{transform:none}
}

/* Print: hide interactive chrome, expand scroll regions, keep tables intact */
@media print{
  body{background:var(--white)}
  .export-bar,.modal-overlay{display:none !important}
  .hero{background:var(--white);color:var(--text);padding:24px 0;box-shadow:none}
  .hero::before{display:none}
  .hero h1,.hero .tag,.hero .eyebrow{color:var(--navy)}
  .hero .meta{color:var(--text-2)}
  .hero .meta strong{color:var(--navy)}
  .summary{box-shadow:none;margin-top:16px}
  .section-head .actions,button.btn{display:none !important}
  .scroll{max-height:none;overflow:visible}
  .table-wrap,tr,.kpi,.summary,.next-steps{break-inside:avoid}
  .next-steps{background:var(--cream);color:var(--text);border:1px solid var(--border)}
  .next-steps h3,.next-steps h4,.next-steps ol li strong{color:var(--navy)}
  .next-steps ol{color:var(--text)}
  details>summary{display:none}
  details[open]>summary{display:none}
  details{display:block}
}
"""

# Legacy raw-data CSV export (reads the visible table); kept for the Watch list.
EXPORT_JS = """
function exportCsv(tableId, filename){
  const tbl = document.getElementById(tableId);
  if(!tbl){return;}
  const rows = [...tbl.querySelectorAll('tr')];
  const csv = rows.map(tr =>
    [...tr.querySelectorAll('th,td')].map(c => {
      let v = c.getAttribute('data-raw') !== null ? c.getAttribute('data-raw') : c.innerText.replace(/\\s+/g,' ').trim();
      if(/[",\\n]/.test(v)){ v = '"' + v.replace(/"/g,'""') + '"'; }
      return v;
    }).join(',')
  ).join('\\n');
  const blob = new Blob([csv], {type: 'text/csv;charset=utf-8;'});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = filename;
  document.body.appendChild(a); a.click(); document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
"""

# Amazon SP bulk-operations CSV builder — assembles 26-col rows from ticked selections only.
EXPORT_BULK_JS = """
function _val(id){ const el=document.getElementById(id); return el? el.value : ''; }
function _chk(id){ const el=document.getElementById(id); return el? el.checked : false; }

function _blankRow(){ const r={}; BULK.cols.forEach(c=>{ r[c]=''; }); r['Product']=BULK.product; r['Operation']='Create'; r['State']='enabled'; return r; }

function _gatherNegatives(includeFunnel){
  const out=[];
  BULK.items.forEach(it=>{
    if(it.kind!=='negate') return;
    if(!_chk('neg-chk-'+it.uid)) return;
    const scope=_val('neg-scope-'+it.uid)||'adgroup';
    const match=_val('neg-match-'+it.uid)||'exact';
    const mt = (match==='phrase') ? BULK.conv.negPhrase : BULK.conv.negExact;
    const r=_blankRow();
    r['Keyword Text']=it.term;
    r['Match Type']=mt;
    if(scope==='campaign'){
      r['Entity']='Campaign Negative Keyword';
      r['Campaign ID']=it.campId; r['Campaign Name']=it.camp;
    } else {
      r['Entity']='Negative Keyword';
      r['Campaign ID']=it.campId; r['Ad Group ID']=it.agId;
      r['Campaign Name']=it.camp; r['Ad Group Name']=it.ag;
    }
    out.push(r);
  });
  if(includeFunnel){
    BULK.items.forEach(it=>{
      if(it.kind.indexOf('harv')!==0) return;
      if(!_chk('harv-chk-'+it.uid)) return;
      if(!it.campId || !it.agId) return; // can only funnel-negate when the source ad group is resolved
      const r=_blankRow();
      r['Entity']='Negative Keyword';
      r['Campaign ID']=it.campId; r['Ad Group ID']=it.agId;
      r['Campaign Name']=it.camp; r['Ad Group Name']=it.ag;
      r['Keyword Text']=it.term;
      r['Match Type']=BULK.conv.negExact;
      out.push(r);
    });
  }
  return out;
}

function _gatherHarvests(){
  const out=[]; let noDest=0;
  BULK.items.forEach(it=>{
    if(it.kind!=='harvkw' && it.kind!=='harvasin') return;
    if(!_chk('harv-chk-'+it.uid)) return;
    const di=_val('harv-dest-'+it.uid);
    const dest = (di!=='' && BULK.adGroups[di]) ? BULK.adGroups[di] : null;
    if(!dest){ noDest++; return; }
    const bid=_val('harv-bid-'+it.uid)||'';
    const r=_blankRow();
    r['Campaign ID']=dest.campId; r['Ad Group ID']=dest.agId;
    r['Campaign Name']=dest.camp; r['Ad Group Name']=dest.ag;
    r['Bid']=bid;
    if(it.kind==='harvkw'){
      r['Entity']='Keyword';
      r['Keyword Text']=it.term;
      r['Match Type']=BULK.conv.posExact;
    } else {
      r['Entity']='Product Targeting';
      r['Product Targeting Expression']='asin="'+String(it.term).toUpperCase()+'"';
    }
    out.push(r);
  });
  if(noDest){ alert(noDest+' harvest row(s) had no destination ad group selected and were skipped. Provide a bulk export, or pick a destination.'); }
  return out;
}

function _toCsv(rows){
  const esc=v=>{ v=(v===undefined||v===null)?'':String(v); if(/[",\\n]/.test(v)){ v='"'+v.replace(/"/g,'""')+'"'; } return v; };
  const lines=[BULK.cols.map(esc).join(',')];
  rows.forEach(r=>{ lines.push(BULK.cols.map(c=>esc(r[c])).join(',')); });
  return lines.join('\\n');
}

function _download(csv, name){
  const blob=new Blob([csv],{type:'text/csv;charset=utf-8;'});
  const url=URL.createObjectURL(blob);
  const a=document.createElement('a'); a.href=url; a.download=name;
  document.body.appendChild(a); a.click(); document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function exportSel(which){
  const funnel=_chk('funnel-neg');
  let rows=[];
  if(which==='neg') rows=_gatherNegatives(funnel);
  else if(which==='harv') rows=_gatherHarvests();
  else rows=_gatherNegatives(funnel).concat(_gatherHarvests());
  if(!rows.length){ alert('Nothing ticked for this export. Tick at least one row first.'); return; }
  const nm = (which==='neg') ? 'amazon-bulk-negatives-'+BULK.stamp+'.csv'
           : (which==='harv') ? 'amazon-bulk-harvests-'+BULK.stamp+'.csv'
           : 'amazon-bulk-combined-'+BULK.stamp+'.csv';
  _download(_toCsv(rows), nm);
}

function updateCounts(){
  let neg=0, harv=0, missing=0;
  BULK.items.forEach(it=>{
    if(it.kind==='negate' && _chk('neg-chk-'+it.uid)){ neg++; if(!it.campId) missing++; }
    if((it.kind==='harvkw'||it.kind==='harvasin') && _chk('harv-chk-'+it.uid)) harv++;
  });
  const set=(id,v)=>{ const el=document.getElementById(id); if(el) el.textContent=v; };
  set('cnt-neg',neg); set('cnt-harv',harv);
  const warn=document.getElementById('id-warn');
  if(warn){
    if(missing){ warn.style.display=''; warn.textContent='⚠ '+missing+' ticked negative(s) have no matched Campaign ID — they will export with names only (Amazon may reject). Re-check the bulk export covers this account.'; }
    else { warn.style.display='none'; }
  }
}

function selAll(kind,on){
  BULK.items.forEach(it=>{
    if(kind==='negate' && it.kind==='negate'){ const el=document.getElementById('neg-chk-'+it.uid); if(el) el.checked=on; }
    if(kind==='harvest' && (it.kind==='harvkw'||it.kind==='harvasin')){ const el=document.getElementById('harv-chk-'+it.uid); if(el) el.checked=on; }
  });
  updateCounts();
}

/* ---- Launch NEW campaigns: build an sp-bulk-builder BULK_INTAKE_DATA payload from ticked harvests ---- */
function _titleCase(s){ return String(s).replace(/\\b\\w/g, c=>c.toUpperCase()); }

function buildLaunchPayload(){
  const themes={}, order=[]; const asins=[]; let bidSum=0, bidN=0;
  BULK.items.forEach(it=>{
    if(it.kind==='harvkw' && _chk('harv-chk-'+it.uid)){
      const c=(it.cluster && it.cluster!=='uncategorized') ? it.cluster : 'Harvested Keywords';
      if(!themes[c]){ themes[c]=[]; order.push(c); }
      themes[c].push(it.term);
      const b=parseFloat(it.bid); if(b>0){ bidSum+=b; bidN++; }
    }
    if(it.kind==='harvasin' && _chk('harv-chk-'+it.uid)){
      asins.push(String(it.term).toUpperCase());
      const b=parseFloat(it.bid); if(b>0){ bidSum+=b; bidN++; }
    }
  });
  if(!order.length && !asins.length) return null;
  const kwt = order.map(c=> 'Theme: '+_titleCase(c)+'\\n'+themes[c].join('\\n')).join('\\n\\n');
  const payload = JSON.parse(JSON.stringify(BULK.launchBase));
  payload.keywordThemesRaw = kwt;
  payload.competitorsRaw = asins.length ? ('Harvested ASINs: '+asins.join(', ')) : '';
  if(bidN){ payload.defaultBid = (bidSum/bidN).toFixed(2); }
  return payload;
}

function openLaunch(){
  const p=buildLaunchPayload();
  if(!p){ alert('Tick at least one harvest row first — Launch builds new campaigns from harvested winners.'); return; }
  document.getElementById('launch-text').value = 'BULK_INTAKE_DATA: ' + JSON.stringify(p);
  document.getElementById('launch-modal').style.display='flex';
}
function closeLaunch(){ document.getElementById('launch-modal').style.display='none'; }
function copyLaunch(){
  const t=document.getElementById('launch-text'); t.focus(); t.select();
  try { navigator.clipboard.writeText(t.value); } catch(e) { try { document.execCommand('copy'); } catch(_){} }
  const b=document.getElementById('launch-copy'); if(b){ const o=b.textContent; b.textContent='Copied ✓'; setTimeout(()=>{ b.textContent=o; }, 1400); }
}
function downloadLaunch(){ _download(document.getElementById('launch-text').value, 'sp-bulk-launch-'+BULK.stamp+'.json'); }

document.addEventListener('DOMContentLoaded', updateCounts);
"""


def money(v: float, sym: str) -> str:
    return f"{sym}{v:,.2f}"


def harvest_bid(r: dict, stats: dict) -> float:
    """A sensible starting exact-match bid: the term's own CPC, else account avg CPC, else 0.75."""
    cpc = r.get("cpc") or 0.0
    if cpc <= 0:
        cpc = stats.get("avg_cpc") or 0.0
    if cpc <= 0:
        cpc = 0.75
    return round(float(cpc), 2)


def dest_options(bulk: dict | None) -> tuple[str, bool]:
    """Build the <option> list for the harvest-destination picker. Returns (html, has_catalog)."""
    if not bulk or not bulk["ad_groups"]:
        return '<option value="">(provide a bulk export to choose a destination)</option>', False
    opts = []
    for i, ag in enumerate(bulk["ad_groups"]):
        sel = " selected" if i == 0 else ""  # list is sorted exact-first, so index 0 is the best default
        label = html.escape(f'{ag["camp"]} › {ag["ag"]}')
        opts.append(f'<option value="{i}"{sel}>{label}</option>')
    return "".join(opts), True


def guess_product_asin(rows: list[dict]) -> tuple[str, str]:
    """Best-guess Product name + parent ASIN from campaign names like 'SO | Product | B0XXXXXXXX | …'."""
    asin_re = re.compile(r"\bB0[A-Z0-9]{8}\b", re.IGNORECASE)
    counts: Counter = Counter()
    name_by_asin: dict[str, str] = {}
    for r in rows:
        name = r.get("campaign", "") or ""
        m = asin_re.search(name)
        if m:
            a = m.group(0).upper()
            counts[a] += 1
            name_by_asin.setdefault(a, name)
    if not counts:
        return "", ""
    asin = counts.most_common(1)[0][0]
    segs = [s.strip() for s in name_by_asin.get(asin, "").split("|")]
    product = ""
    for i, s in enumerate(segs):
        if s.upper() == asin and i > 0:
            product = segs[i - 1]
            break
    return product, asin


def build_launch_base(setup: dict, rows: list[dict]) -> dict:
    """A complete sp-bulk-builder BULK_INTAKE_DATA template; JS fills themes/competitors/bid from the
    ticked harvest rows. Mirrors the intake form's flat field shape exactly."""
    product, asin = guess_product_asin(rows)
    return {
        "campaigns": dict(LAUNCH_CAMPAIGNS),
        "client": "", "productName": product, "asin": asin,
        "skus": [], "brandVariations": [],
        "keywordThemesRaw": "", "skListRaw": "", "competitorsRaw": "",
        "dailyBudget": "50", "budgetMode": "uniform", "perTypeBudgets": {},
        "bidMode": "uniform", "perTypeBids": {}, "defaultBid": "0.75",
        "adGroupBid": "1.00", "catchAllBid": "0.10", "startDate": "",
        "useDefaultPlacements": True,
        "placements": {k: dict(v) for k, v in SP_PLACEMENT_DEFAULTS.items()},
        "allSkusAllCampaigns": True, "splitExactFromPhrase": True, "useSTR": False,
        "notes": f"Harvested winners from the {setup['account_label']} search term report. "
                 f"Exact-match keyword groups + competitor product targeting pre-selected. "
                 f"VERIFY Product / ASIN / SKUs before generating.",
        "overridesExpanded": False,
        "manualBidding": "Fixed bid", "autoBidding": "Dynamic bids - down only",
        "biddingMode": "uniform",
        "disableBrandNegPhrase": False, "disableSkNegExact": False, "allowNegInExact": False,
    }


# ---------- interactive row renderers ----------

def render_harvest_row(r: dict, sym: str, show_cluster: bool, dest_html: str, kind: str, has_catalog: bool) -> str:
    uid = r["uid"]
    term = html.escape(r["search_term"])
    camp = html.escape(r["campaign"])
    ag = html.escape(r["ad_group"])
    cluster = html.escape(r.get("cluster", "")) if show_cluster else ""
    cluster_cell = f'<td data-raw="{cluster}"><span class="pill p-blue">{cluster or "—"}</span></td>' if show_cluster else ""
    dest_select = (
        f'<select class="cell-select" id="harv-dest-{uid}">{dest_html}</select>'
        if has_catalog else f'<span class="pill p-gray">no bulk export</span>'
    )
    bid = r.get("harvest_bid", 0.0)
    return (
        f'<tr class="row-harvest">'
        f'<td class="chk"><input type="checkbox" class="rowchk" id="harv-chk-{uid}" checked onchange="updateCounts()"></td>'
        f'<td data-raw="{term}"><strong>{term}</strong></td>'
        + cluster_cell +
        f'<td data-raw="{camp}">{camp}</td>'
        f'<td data-raw="{ag}">{ag}</td>'
        f'<td class="num" data-raw="{r["clicks"]}">{r["clicks"]:,}</td>'
        f'<td class="num" data-raw="{r["orders"]}">{r["orders"]:,}</td>'
        f'<td class="num" data-raw="{r["sales"]:.2f}">{money(r["sales"], sym)}</td>'
        f'<td class="num" data-raw="{r["acos"]:.1f}">{r["acos"]:.1f}%</td>'
        f'<td>{dest_select}</td>'
        f'<td class="num"><input type="number" step="0.01" min="0" class="cell-bid" id="harv-bid-{uid}" value="{bid:.2f}"></td>'
        f'</tr>'
    )


def render_negate_row(r: dict, sym: str) -> str:
    uid = r["uid"]
    term = html.escape(r["search_term"])
    camp = html.escape(r["campaign"])
    ag = html.escape(r["ad_group"])
    reason = html.escape(r["reason"])
    subtype_label = "Unprofitable" if r["subtype"] == "unprofitable" else "Wasted spend"
    strategic = r.get("strategic", False)
    row_class = "row-strategic" if strategic else "row-negate"
    type_pill = '<span class="pill p-blue">Strategic · keep</span>' if strategic else f'<span class="pill p-orange">{subtype_label}</span>'
    id_flag = "" if r.get("id_resolved") else '<span class="pill p-red id-flag">no ID</span>'
    checked = "" if strategic else " checked"  # strategic terms default to NOT negating
    scope_select = (
        f'<select class="cell-select" id="neg-scope-{uid}">'
        f'<option value="adgroup" selected>This ad group</option>'
        f'<option value="campaign">Whole campaign</option>'
        f'</select>'
    )
    match_select = (
        f'<select class="cell-select" id="neg-match-{uid}">'
        f'<option value="exact" selected>Negative Exact</option>'
        f'<option value="phrase">Negative Phrase</option>'
        f'</select>'
    )
    return (
        f'<tr class="{row_class}">'
        f'<td class="chk"><input type="checkbox" class="rowchk" id="neg-chk-{uid}"{checked} onchange="updateCounts()"></td>'
        f'<td data-raw="{term}"><strong>{term}</strong></td>'
        f'<td data-raw="{subtype_label}">{type_pill}</td>'
        f'<td data-raw="{camp}">{camp}</td>'
        f'<td data-raw="{ag}">{ag}{id_flag}</td>'
        f'<td class="num" data-raw="{r["clicks"]}">{r["clicks"]:,}</td>'
        f'<td class="num" data-raw="{r["orders"]}">{r["orders"]:,}</td>'
        f'<td class="num" data-raw="{r["spend"]:.2f}">{money(r["spend"], sym)}</td>'
        f'<td class="num" data-raw="{r["acos"]:.1f}">{r["acos"]:.1f}%</td>'
        f'<td>{scope_select}</td>'
        f'<td>{match_select}</td>'
        f'<td data-raw="{reason}">{reason}</td>'
        f'</tr>'
    )


def render_watch_row(r: dict, sym: str) -> str:
    term = html.escape(r["search_term"])
    camp = html.escape(r["campaign"])
    ag = html.escape(r["ad_group"])
    reason = html.escape(r["reason"])
    return (
        f'<tr>'
        f'<td data-raw="{term}">{term}</td>'
        f'<td data-raw="{camp}">{camp}</td>'
        f'<td data-raw="{ag}">{ag}</td>'
        f'<td class="num" data-raw="{r["clicks"]}">{r["clicks"]:,}</td>'
        f'<td class="num" data-raw="{r["orders"]}">{r["orders"]:,}</td>'
        f'<td class="num" data-raw="{r["spend"]:.2f}">{money(r["spend"], sym)}</td>'
        f'<td class="num" data-raw="{r["sales"]:.2f}">{money(r["sales"], sym)}</td>'
        f'<td class="num" data-raw="{r["acos"]:.1f}">{r["acos"]:.1f}%</td>'
        f'<td data-raw="{reason}">{reason}</td>'
        f'</tr>'
    )


def build_html(*, rows: list[dict], stats: dict, setup: dict, clusters: dict, bulk: dict | None) -> str:
    sym = stats["symbol"]
    harvest_kw = [r for r in rows if r["bucket"] == "harvest" and r["subtype"] == "keyword"]
    harvest_asin = [r for r in rows if r["bucket"] == "harvest" and r["subtype"] == "asin"]
    negate = [r for r in rows if r["bucket"] == "negate"]
    watch = [r for r in rows if r["bucket"] == "watch"]

    harvest_kw.sort(key=lambda r: (-r["sales"], r["acos"]))
    harvest_asin.sort(key=lambda r: (-r["sales"], r["acos"]))
    negate.sort(key=lambda r: (not r.get("strategic"), -r["spend"]))
    watch.sort(key=lambda r: -r["clicks"])

    # Assign stable uids + a starting harvest bid to each actionable row.
    uid = 0
    items_js: list[dict] = []
    for r in harvest_kw + harvest_asin:
        r["uid"] = uid
        r["harvest_bid"] = harvest_bid(r, stats)
        items_js.append({
            "uid": uid, "kind": "harvkw" if r["subtype"] == "keyword" else "harvasin",
            "term": r["search_term"], "camp": r["campaign"], "ag": r["ad_group"],
            "campId": r.get("campaign_id", ""), "agId": r.get("ad_group_id", ""),
            "cluster": r.get("cluster", ""), "bid": f'{r["harvest_bid"]:.2f}',
        })
        uid += 1
    for r in negate:
        r["uid"] = uid
        items_js.append({
            "uid": uid, "kind": "negate",
            "term": r["search_term"], "camp": r["campaign"], "ag": r["ad_group"],
            "campId": r.get("campaign_id", ""), "agId": r.get("ad_group_id", ""),
        })
        uid += 1

    strategic_count = len([r for r in negate if r.get("strategic")])
    negate_actionable = len([r for r in negate if not r.get("strategic")])
    total_wasted = sum(r["spend"] for r in negate if not r.get("strategic"))
    total_harvest_revenue = sum(r["sales"] for r in harvest_kw + harvest_asin)
    total_actionable = len(harvest_kw) + len(harvest_asin) + negate_actionable
    show_cluster = bool(clusters)
    dest_html, has_catalog = dest_options(bulk)

    # Embedded data for the client-side bulk-CSV builder.
    gen_date = dt.date.today().isoformat()
    bulk_data = {
        "cols": BULK_COLS,
        "product": "Sponsored Products",
        "stamp": gen_date,
        "conv": bulk["conv"] if bulk else {"negExact": "Negative Exact", "negPhrase": "Negative Phrase", "posExact": "Exact"},
        "adGroups": [{"camp": a["camp"], "campId": a["campId"], "ag": a["ag"], "agId": a["agId"]} for a in (bulk["ad_groups"] if bulk else [])],
        "items": items_js,
        "launchBase": build_launch_base(setup, rows),
    }
    data_json = json.dumps(bulk_data, ensure_ascii=False).replace("</", "<\\/")

    # Executive summary copy — conditional on what we found
    summary_parts = []
    if len(harvest_kw) + len(harvest_asin) > 0:
        summary_parts.append(f'<span class="hilite-green">{len(harvest_kw) + len(harvest_asin)} search terms</span> are ready to be promoted into exact-match, carrying <span class="hilite-green">{money(total_harvest_revenue, sym)}</span> in attributed sales.')
    if negate_actionable > 0:
        summary_parts.append(f'<span class="hilite-orange">{negate_actionable} terms</span> are burning <span class="hilite-orange">{money(total_wasted, sym)}</span> in wasted spend and should be negated at the ad-group level.')
    if strategic_count > 0:
        summary_parts.append(f'<span class="hilite-orange">{strategic_count} term{"s" if strategic_count != 1 else ""}</span> would have been negated but match{"" if strategic_count != 1 else "es"} your keyword research — keep {"them" if strategic_count != 1 else "it"} and raise bids instead.')
    if total_actionable == 0 and strategic_count == 0:
        summary_parts.append(f'No action items hit these thresholds — the {len(watch)} terms in the <strong>Watch</strong> list still need more clicks before they can be decisioned.')
    summary_text = " ".join(summary_parts)

    kpis_html = "".join([
        f'<div class="kpi good"><div class="lbl">Harvest · Keywords</div><div class="val">{len(harvest_kw)}</div><div class="sub">{money(sum(r["sales"] for r in harvest_kw), sym)} attributed sales</div></div>',
        f'<div class="kpi good"><div class="lbl">Harvest · ASINs</div><div class="val">{len(harvest_asin)}</div><div class="sub">{money(sum(r["sales"] for r in harvest_asin), sym)} attributed sales</div></div>',
        f'<div class="kpi warn"><div class="lbl">To negate</div><div class="val">{negate_actionable}</div><div class="sub">{money(total_wasted, sym)} wasted spend to recover</div></div>',
        f'<div class="kpi info"><div class="lbl">Watch list</div><div class="val">{len(watch)}</div><div class="sub">signal building · not yet decisioned</div></div>',
    ])

    bulk_status = (
        f'<div><div class="k">Bulk export</div><div class="v">{len(bulk["ad_groups"])} ad groups</div></div>'
        if bulk else '<div><div class="k">Bulk export</div><div class="v">Not provided</div></div>'
    )
    setup_html = "".join([
        f'<div><div class="k">Target ACOS</div><div class="v">{setup["target_acos"]:.0f}%</div></div>',
        f'<div><div class="k">Min clicks</div><div class="v">{setup["min_clicks"]}</div></div>',
        f'<div><div class="k">Min orders</div><div class="v">{setup["min_orders"]}</div></div>',
        f'<div><div class="k">Account avg CVR</div><div class="v">{stats["avg_cvr"]*100:.1f}%</div></div>',
        f'<div><div class="k">Account avg CPC</div><div class="v">{money(stats["avg_cpc"], sym)}</div></div>',
        f'<div><div class="k">KW research</div><div class="v">{str(len(clusters)) + " clusters" if clusters else "Not provided"}</div></div>',
        bulk_status,
    ])

    cluster_th = "<th>Cluster</th>" if show_cluster else ""

    # Harvest KW table
    if harvest_kw:
        harvest_kw_rows = "".join(render_harvest_row(r, sym, show_cluster, dest_html, "harvkw", has_catalog) for r in harvest_kw)
        harvest_kw_body = f'''<div class="scroll"><table id="tbl-harvest-kw">
<thead><tr><th class="chk">✓</th><th>Search term</th>{cluster_th}<th>Src campaign</th><th>Src ad group</th><th>Clicks</th><th>Orders</th><th>Sales</th><th>ACOS</th><th>Harvest into (exact)</th><th>Bid</th></tr></thead>
<tbody>{harvest_kw_rows}</tbody></table></div>'''
    else:
        harvest_kw_body = '<div class="empty"><span class="big">No keyword harvests yet</span>No search term cleared both the click gate and the ACOS target.</div>'

    # Harvest ASIN table
    if harvest_asin:
        harvest_asin_rows = "".join(render_harvest_row(r, sym, show_cluster, dest_html, "harvasin", has_catalog) for r in harvest_asin)
        harvest_asin_body = f'''<div class="scroll"><table id="tbl-harvest-asin">
<thead><tr><th class="chk">✓</th><th>ASIN</th>{cluster_th}<th>Src campaign</th><th>Src ad group</th><th>Clicks</th><th>Orders</th><th>Sales</th><th>ACOS</th><th>Target into (PT)</th><th>Bid</th></tr></thead>
<tbody>{harvest_asin_rows}</tbody></table></div>'''
    else:
        harvest_asin_body = '<div class="empty"><span class="big">No ASIN harvests</span>No competitor ASINs converted profitably at these thresholds.</div>'

    # Negate table
    strategic_banner = ""
    if strategic_count:
        strategic_banner = (
            f'<div class="strategic-banner">'
            f'<span class="icon">!</span>'
            f'<div><strong>{strategic_count} strategic term{"s" if strategic_count != 1 else ""}</strong> matched your keyword research — '
            f'left un-ticked. Tick to negate anyway, or keep them and bid up in their own campaign.</div>'
            f'</div>'
        )
    id_warn = '<div class="warn-banner" id="id-warn" style="display:none"></div>'
    no_export_banner = ""
    if not bulk:
        no_export_banner = (
            '<div class="warn-banner">No bulk export was provided, so rows export with campaign/ad-group '
            '<strong>names only</strong> (no IDs). Paste them beneath a freshly downloaded Amazon SP bulk template, '
            'or re-run with your current bulk export to fill IDs.</div>'
        )
    if negate:
        negate_rows = "".join(render_negate_row(r, sym) for r in negate)
        negate_body = f'''{strategic_banner}{id_warn}<div class="scroll"><table id="tbl-negate">
<thead><tr><th class="chk">✓</th><th>Search term</th><th>Type</th><th>Src campaign</th><th>Src ad group</th><th>Clicks</th><th>Orders</th><th>Spend</th><th>ACOS</th><th>Apply to</th><th>Match</th><th>Reason</th></tr></thead>
<tbody>{negate_rows}</tbody></table></div>'''
    else:
        negate_body = '<div class="empty"><span class="big">Nothing to negate</span>No term exceeded the click gate without orders. Clean slate.</div>'

    # Watch table
    if watch:
        watch_rows = "".join(render_watch_row(r, sym) for r in watch)
        watch_body = f'''<div class="scroll"><table id="tbl-watch">
<thead><tr><th>Search term</th><th>Src campaign</th><th>Src ad group</th><th>Clicks</th><th>Orders</th><th>Spend</th><th>Sales</th><th>ACOS</th><th>Reason</th></tr></thead>
<tbody>{watch_rows}</tbody></table></div>'''
    else:
        watch_body = '<div class="empty">Nothing currently on the watch list.</div>'

    # Next-steps card
    steps = []
    steps.append('<li><strong>Review & tick:</strong> the rows you want are pre-ticked. Untick anything you want to hold; for negatives pick <em>ad-group vs whole-campaign</em> and the match type; for harvests pick the destination ad group + bid.</li>')
    steps.append('<li><strong>Export:</strong> use the bar at the top — <em>Negatives</em>, <em>Harvests</em>, or <em>Combined</em> — to download an Amazon SP bulk-operations CSV of just the ticked rows.</li>')
    steps.append('<li><strong>Upload:</strong> in Amazon Ads → Bulk Operations, download a Sponsored Products bulk template, paste the exported rows beneath its header, and upload. Amazon validates before it applies.</li>')
    if strategic_count:
        steps.append(f'<li><strong>Protect:</strong> the {strategic_count} strategic term{"s" if strategic_count != 1 else ""} are left un-ticked — bid up / isolate rather than negate.</li>')
    if len(watch) > 20:
        steps.append(f'<li><strong>Re-evaluate in 2 weeks:</strong> {len(watch)} watch-list terms need more data. Re-run once they cross the click threshold.</li>')
    steps_html = "".join(steps)

    label = setup["account_label"]

    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8" />
<title>KW Harvester &amp; Negator · {html.escape(label)}</title>
<style>{BRAND_CSS}</style></head><body>

<header class="hero">
  <div class="hero-inner">
    <div class="eyebrow">Sophie Society · Amazon PPC</div>
    <h1>Keyword Harvester &amp; Negator</h1>
    <div class="brand-rule"></div>
    <div class="tag">Tick the harvests and negatives you want, choose where each lands, then export an Amazon Sponsored Products bulk-operations sheet ready to upload.</div>
    <div class="meta">
      <div><strong>{html.escape(label)}</strong></div>
      <div>Generated {gen_date}</div>
      <div>{stats["row_count"]:,} rows · {money(stats["total_spend"], sym)} spend · {money(stats["total_sales"], sym)} sales</div>
    </div>
  </div>
</header>

<div class="container">

  <div class="export-bar">
    <span class="eb-title">Build upload sheet</span>
    <span class="eb-count">Negatives <b id="cnt-neg">0</b></span>
    <span class="eb-count">Harvests <b id="cnt-harv">0</b></span>
    <span class="eb-spacer"></span>
    <label class="eb-toggle"><input type="checkbox" id="funnel-neg"> Add funnel negatives for harvested terms</label>
    <button class="btn warn" onclick="exportSel('neg')">Negatives CSV</button>
    <button class="btn" onclick="exportSel('harv')">Harvests CSV</button>
    <button class="btn secondary" onclick="exportSel('combined')">Combined CSV</button>
    <button class="btn" onclick="openLaunch()">Launch new campaigns →</button>
    <div class="eb-hint">Negatives / Harvests / Combined export only the ticked rows in Amazon's 26-column SP bulk format (Harvests &amp; Combined add the proven term to an existing ad group). <strong>Launch new campaigns</strong> instead hands the ticked harvests to the SP Bulk Builder as a ready intake payload, to build fresh exact-match + competitor campaigns. Funnel negatives add a Negative Exact of each harvested term in its source ad group.</div>
  </div>

  <div class="summary">
    <h4>The headline</h4>
    <p>{summary_text}</p>
  </div>

  <div class="setup-card">
    <h4 style="margin-bottom:14px">Thresholds &amp; inputs</h4>
    <div class="setup">{setup_html}</div>
  </div>

  <div class="kpis">{kpis_html}</div>

  <section class="section">
    <div class="section-head">
      <div class="title-block">
        <h2>Harvest · Keywords <span class="count-pill">{len(harvest_kw)}</span></h2>
        <div class="brand-rule"></div>
      </div>
      <div class="actions">
        <span class="sel-links"><a onclick="selAll('harvest',true)">All</a> · <a onclick="selAll('harvest',false)">None</a></span>
        <button class="btn secondary" onclick="exportCsv('tbl-harvest-kw','harvest-keywords-data-{gen_date}.csv')">Raw CSV</button>
      </div>
    </div>
    <div class="table-wrap">{harvest_kw_body}</div>
  </section>

  <section class="section">
    <div class="section-head">
      <div class="title-block">
        <h2>Harvest · ASIN targets <span class="count-pill">{len(harvest_asin)}</span></h2>
        <div class="brand-rule"></div>
      </div>
      <div class="actions">
        <button class="btn secondary" onclick="exportCsv('tbl-harvest-asin','harvest-asins-data-{gen_date}.csv')">Raw CSV</button>
      </div>
    </div>
    <div class="table-wrap">{harvest_asin_body}</div>
  </section>

  <section class="section">
    <div class="section-head">
      <div class="title-block">
        <h2>Negate <span class="count-pill">{negate_actionable}</span>{' <span class="count-pill muted">+' + str(strategic_count) + ' strategic</span>' if strategic_count else ''}</h2>
        <div class="brand-rule"></div>
      </div>
      <div class="actions">
        <span class="sel-links"><a onclick="selAll('negate',true)">All</a> · <a onclick="selAll('negate',false)">None</a></span>
        <button class="btn secondary" onclick="exportCsv('tbl-negate','negate-data-{gen_date}.csv')">Raw CSV</button>
      </div>
    </div>
    {no_export_banner}
    <div class="table-wrap">{negate_body}</div>
  </section>

  <section class="section">
    <div class="section-head">
      <div class="title-block">
        <h2>Watch list <span class="count-pill muted">{len(watch)}</span></h2>
        <div class="brand-rule"></div>
      </div>
      <div class="actions">
        <button class="btn secondary" onclick="exportCsv('tbl-watch','watch-{gen_date}.csv')">Raw CSV</button>
      </div>
    </div>
    <details><summary>Show watch list (terms with signal but below thresholds)</summary>
      <div class="table-wrap" style="margin-top:12px">{watch_body}</div>
    </details>
  </section>

  <div class="next-steps">
    <h4 style="color:var(--peach)">Next steps</h4>
    <h3>Your playbook</h3>
    <div class="brand-rule"></div>
    <ol>{steps_html}</ol>
  </div>

  <footer class="page-footer">
    Generated {gen_date}
    <span class="dot">·</span> Thresholds: ACOS ≤ {setup["target_acos"]:.0f}% · ≥ {setup["min_clicks"]} clicks · ≥ {setup["min_orders"]} orders
    <span class="dot">·</span> Sophie Society
  </footer>

</div>

<div class="modal-overlay" id="launch-modal" style="display:none">
  <div class="modal-card">
    <h3>Launch new campaigns → SP Bulk Builder</h3>
    <p>This is a ready <strong>BULK_INTAKE_DATA</strong> payload for the SP Bulk Builder skill, pre-filled from your ticked harvest winners — keyword themes (grouped by cluster) for exact-match keyword groups, harvested ASINs as competitor product targeting, and a bid from their CPC. Paste it into a chat with SP Bulk Builder. If it shows the intake form, your themes/competitors are already in section 3 — just confirm <strong>Product / ASIN / SKUs</strong> and submit.</p>
    <textarea id="launch-text" readonly></textarea>
    <div class="modal-actions">
      <button class="btn" id="launch-copy" onclick="copyLaunch()">Copy</button>
      <button class="btn secondary" onclick="downloadLaunch()">Download .json</button>
      <button class="btn secondary" onclick="closeLaunch()">Close</button>
    </div>
  </div>
</div>

<script>const BULK = {data_json};</script>
<script>{EXPORT_JS}</script>
<script>{EXPORT_BULK_JS}</script>
</body></html>'''


# ---------- main ----------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", required=True, help="Path to Amazon SP Search Term Report .xlsx")
    ap.add_argument("--target-acos", type=float, required=True, help="Target ACOS in percent, e.g. 30")
    ap.add_argument("--min-clicks", type=int, required=True)
    ap.add_argument("--min-orders", type=int, default=1)
    ap.add_argument("--account-label", default="account")
    ap.add_argument("--kw-research", default=None)
    ap.add_argument("--bulk-export", default=None, help="Path to the account's current Amazon SP bulk export (.xlsx) — used to map campaign/ad-group names to IDs so exports are upload-ready.")
    ap.add_argument("--out-dir", default=None, help="Override output directory. Default: ~/Downloads")
    args = ap.parse_args()

    report_path = Path(args.report).expanduser()
    if not report_path.exists():
        sys.exit(f"Report not found: {report_path}")

    rows, stats = parse_report(report_path)
    rows = dedup_rows(rows)
    rows = classify(rows, args.target_acos, args.min_clicks, args.min_orders)

    # Bulk export (optional) — name -> ID mapping + destination catalog
    bulk: dict | None = None
    if args.bulk_export:
        bulk_path = Path(args.bulk_export).expanduser()
        if not bulk_path.exists():
            print(f"[warn] bulk-export file not found: {bulk_path} — continuing without IDs", file=sys.stderr)
        else:
            bulk = parse_bulk_export(bulk_path)
    resolve_ids(rows, bulk)

    # KW research (optional)
    clusters: dict[str, list[str]] = {}
    kw_set: set[str] = set()
    if args.kw_research:
        kw_path = Path(args.kw_research).expanduser()
        if not kw_path.exists():
            print(f"[warn] kw-research file not found: {kw_path} — skipping", file=sys.stderr)
        else:
            kws, explicit_clusters = parse_kw_research(kw_path)
            kw_set = {k.lower() for k in kws}
            clusters = explicit_clusters if explicit_clusters else cluster_keywords(kws)

    # Strategic-keyword safety flag on negate rows
    if kw_set:
        for r in rows:
            if r["bucket"] == "negate" and r["search_term_norm"] in kw_set:
                r["strategic"] = True

    # Cluster tagging for harvests
    if clusters:
        for r in rows:
            if r["bucket"] == "harvest":
                r["cluster"] = tag_term_with_cluster(r["search_term"], clusters)

    setup = {
        "target_acos": args.target_acos,
        "min_clicks": args.min_clicks,
        "min_orders": args.min_orders,
        "account_label": args.account_label,
    }
    html_doc = build_html(rows=rows, stats=stats, setup=setup, clusters=clusters, bulk=bulk)

    out_dir = Path(args.out_dir) if args.out_dir else Path.home() / "Downloads"
    out_dir.mkdir(parents=True, exist_ok=True)
    today = dt.date.today().isoformat()
    out_path = out_dir / f"kw-harvest-{args.account_label}-{today}.html"
    out_path.write_text(html_doc, encoding="utf-8")

    # Summary to stdout
    harvest_kw = [r for r in rows if r["bucket"] == "harvest" and r["subtype"] == "keyword"]
    harvest_asin = [r for r in rows if r["bucket"] == "harvest" and r["subtype"] == "asin"]
    negate = [r for r in rows if r["bucket"] == "negate"]
    watch = [r for r in rows if r["bucket"] == "watch"]
    wasted = sum(r["spend"] for r in negate if not r.get("strategic"))
    strategic = [r for r in negate if r.get("strategic")]
    resolved = len([r for r in (harvest_kw + harvest_asin + negate) if r.get("id_resolved")])
    summary = {
        "harvest_keywords": len(harvest_kw),
        "harvest_asins": len(harvest_asin),
        "negate": len([r for r in negate if not r.get("strategic")]),
        "negate_strategic_skip": len(strategic),
        "watch": len(watch),
        "total_wasted_spend": round(wasted, 2),
        "currency_symbol": stats["symbol"],
        "bulk_export_loaded": bool(bulk),
        "ad_groups_in_catalog": len(bulk["ad_groups"]) if bulk else 0,
        "ids_resolved": resolved,
        "output": str(out_path),
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
```
