---
name: bundle-crosssell-finder
description: >
  Finds bundle, cross-sell, and Sponsored Display targeting opportunities for a Sophie Society
  client from raw Market Basket reports (Amazon Brand Analytics) via Sophie Hub, aggregated over
  several months. Separates the client's own ASINs (bundle/cross-sell) from external ASINs (SD
  targeting) and delivers a branded, beginner-friendly XLSX. Built so someone with no Amazon
  knowledge, connected to Sophie Hub, can run it via click-to-select questions. Trigger on "bundle
  finder [Brand]", "bundle ideas for [Brand]", "cross-sell [Brand]", "market basket [Brand]", "what
  bundles can I build for [Brand]", "frequently bought together [Brand]", "sd targeting ideas
  [Brand]", "run the bundle finder for [Brand]", or any combination of "bundle" / "cross-sell" /
  "market basket" / "frequently bought together" / "sd targeting" plus a client name. Also trigger
  if the user asks which products are bought together or what to build as a combo for a client.
---

# Bundle / Cross-Sell Finder

## 👋 What this skill does (plain English — read this first)

When people shop on Amazon, they often buy two products **in the same order**. Amazon tracks this
and calls it the **Market Basket** report. This skill reads that report for one brand and turns it
into a simple, actionable list:

- **Products the brand ALREADY sells that get bought together** → you can either sell them as a
  **bundle** (one listing, two products) or run a **cross-sell ad** pointing one product at the other.
- **Other sellers' products that get bought together with the brand's products** → you can run
  **Sponsored Display ads** that show the brand's product to people looking at those other products.

**You do NOT need to know anything about Amazon to run this.** The skill will ask you a few
questions with options to click, do all the analysis, and hand you one spreadsheet (XLSX) plus a
short plain-English summary in the chat.

### Before you start
You need to be **connected to Sophie Hub** (the data source). If the store list in STEP A comes
back empty or errors, tell the user Sophie Hub isn't connected and stop — nothing else will work
without it.

### What you get at the end
One branded Excel file with these tabs:
1. **Start Here** — plain-English overview + the top opportunities, so you never have to read raw numbers.
2. **Bundle & Cross-Sell** — the brand's own products that are bought together.
3. **Ad Targeting (Sponsored Display)** — other sellers' products worth targeting with ads.
4. **All Data** — every raw row, month by month, if you want to audit.
5. **Glossary** — every column explained in one line.

Plus a short summary posted in the chat. **No Slack message is sent.**

> **Technical note (for the assistant, not the user):** do NOT use Sophie Hub's `get_market_basket`
> tool — it has two confirmed gaps: (1) it returns `combination_count = 0` always because Amazon
> gives no absolute count, only a **combination %** (`combinationPct`) the tool doesn't map; and
> (2) it only loads the **latest month** (`files_loaded: 1`), ignoring the rest of the history.
> This skill reads the raw reports directly (`discover_amazon_reports` + `get_amazon_report_full`)
> to get the real % aggregated over several months.

---

## Global Config

```
Config dir:     resolve via glob (see PRE-STEP)
GDrive output:  G:\My Drive\Claude\Clients\[BrandName]\Bundle Finder\
Data source:    Sophie Hub — raw S3 reports (GET_BRAND_ANALYTICS_MARKET_BASKET_REPORT)
Window:         last 6 months of available reports (default; user can pick another in STEP A)
XLSX language:  ALWAYS English (headers, banners, notes). This is a fixed rule of this skill,
                independent of report_language in the client config — no exceptions.
User-facing:    ALL questions, the guide, and the chat summary are in English too.
```

---

## STEP A: Guided intake (ask with click-to-select options)

This is the front door for a non-expert user. Present these as **click-to-select questions**
(use the host's multiple-choice UI). Never make the user type an exact brand name or config
filename unless nothing else works.

**A1 — Which store?**
Call `list_stores` first. Show each store's **display name** as a selectable option (add an
"Other / not listed" escape). If the user already named a brand in their message and it matches
exactly one store, skip this question and confirm the choice in one line instead.
> Always say "store" to the user — never "store ID" or "seller ID".

**A2 — How far back should I look?**
- **Last 6 months** *(recommended — best balance of signal and recency)*
- Last 12 months *(more data, may include older buying patterns)*
- Last 3 months *(only the most recent trend)*

Maps to `MONTHS_WINDOW` in STEP 2. If the store has fewer months than requested, use what's
available and say so (never fail).

**A3 — All products, or just one?**
- **All products** *(recommended — analyze the whole catalog)*
- Just one product — *(if picked, ask the user to paste the ASIN, or offer a short list of the
  brand's top products from `list_top_products` to click)*

If "just one," filter each month's `dataByAsin` to **rows where the chosen ASIN appears as EITHER
`asin` OR `purchasedWithAsin`** — NOT only as `asin`. This is critical: Amazon builds the report
from the seller's own anchors, so a hub product (a bestseller) shows up mostly as the *partner* of
its sibling variations, not as its own anchor. Filtering to `asin == chosen` only keeps the chosen
product's own top-3 partners (often weak external noise) and throws away every "sibling bought WITH
the chosen product" row — which is where the real bundle/cross-sell signal lives. Keep both
directions; STEP 3's bidirectional logic then pairs and de-dupes them correctly.

```python
# Single-product scope — keep BOTH directions involving the chosen anchor
chosen = "B0..."   # from A3
raw_rows = [r for r in raw_rows if r["anchor"] == chosen or r["partner"] == chosen]
```

Once answered, briefly confirm the three choices in one plain sentence, then run everything else
without further questions unless something breaks.

---

## PRE-STEP: Establish context

```python
import json, os, glob
from datetime import date

matches = glob.glob("/sessions/*/mnt/Outputs/sophie-society-clients/")
if not matches:
    matches = glob.glob("/sessions/*/mnt/Claude/Outputs/sophie-society-clients/")
config_dir = matches[0] if matches else None

# A config is helpful (gives store_id, managed_asins) but NOT required — a non-expert user may
# not know the brand maps to a config. If found, load it; if not, rely on STEP A + list_stores.
cfg = {}
brand_name = "resolved from STEP A (store display name)"
if config_dir and os.path.exists(os.path.join(config_dir, f"{brand_name}.json")):
    with open(os.path.join(config_dir, f"{brand_name}.json")) as f:
        cfg = json.load(f)

store_id      = cfg.get("sophie_store_id")       # see STEP 0
managed_asins = cfg.get("managed_asins", [])     # [{asin, name, type}]
```

If a config exists it saves a step. If not, don't block the user — proceed with the store picked
in STEP A.

---

## STEP 0: Resolve the `store` (Seller ID)

- Use `cfg["sophie_store_id"]` if it exists.
- Otherwise use the store the user picked in **STEP A1** (via `list_stores`); if it came from
  `list_stores` and a config exists, remind the user (once) they can persist `sophie_store_id`.
- No store resolved → stop and ask the user to pick a store.

---

## STEP 1: Build the universe of own ASINs

You need to know which ASINs belong to the client so you can classify each bought-together pair.

```python
# Primary: list_product_catalog(store=store_id) → all ASINs in the store
# Fallback: use managed_asins from the config if the catalog isn't available
own_asins = { set of all own ASINs, upper-cased }
```

> Use the **full catalog** (not just managed_asins): an own ASIN bought together may be a product
> Sophie doesn't manage but is still "own" → still a bundle, not an SD target. If you fall back to
> managed_asins, flag it in the XLSX.

> **This `own_asins` is the starting point, not the final set.** STEP 3 expands it with own ASINs
> that are no longer in the active catalog but appear as anchors in Market Basket history
> (delisted) — see STEP 3.

---

## STEP 2: Pull Market Basket (raw reports, chosen window)

**Do not use `get_market_basket`** (see technical note above). Instead:

```python
MONTHS_WINDOW = 6  # from STEP A2 (6 default, or 12 / 3 / custom)

# 1. Discover all available monthly reports
reports = discover_amazon_reports(
    api_type="SP",
    seller_id=store_id,
    report_type_filter="GET_BRAND_ANALYTICS_MARKET_BASKET_REPORT",
)
date_ranges = reports["report_types"][0]["date_ranges"]  # chronologically ordered

# 2. Take the last N available months (may be fewer than requested if the store is new)
recent = date_ranges[-MONTHS_WINDOW:]
months_available = len(recent)   # note: may be < MONTHS_WINDOW → reflect it in the output

# 3. Fetch each raw report and accumulate rows
raw_rows = []  # (month_label, anchor, partner, rank, combination_pct)
for rep in recent:
    full = get_amazon_report_full(s3_key=rep["s3_key"])
    for row in full["data"]["dataByAsin"]:
        raw_rows.append({
            "month": rep["date_from"][:7],           # "YYYY-MM"
            "anchor": row["asin"].upper(),
            "partner": row["purchasedWithAsin"].upper(),
            "rank": row["purchasedWithRank"],          # 1..3, already ordered by Amazon
            "pct": row["combinationPct"],              # real combination % — this is the strong signal
        })
```

> **Raw-data notes:**
> - Per anchor per month, Amazon gives **the top 3 partners** (`purchasedWithRank` 1–3) with their
>   real `combinationPct`. There are never more than 3 per anchor per month — an Amazon limit, not the skill's.
> - If `months_available < MONTHS_WINDOW`, the store has less history than requested — use what's
>   available and say so in the XLSX banner (don't fail).
> - If an individual report is empty (`dataByAsin` empty), skip it and continue with the rest.

---

## STEP 3: Expand own_asins with legacy anchors, aggregate across months, classify

**Before aggregating:** the catalog (STEP 1) may not include own ASINs that were delisted but
still appear in Market Basket history. Because Amazon generates this report **only from the
seller's own anchors**, any ASIN that appears as an `anchor` in `raw_rows` is guaranteed own —
whether or not it's in `list_product_catalog`. Expand the set before classifying:

```python
observed_anchors = {r["anchor"] for r in raw_rows}
legacy_asins = observed_anchors - own_asins     # anchors not in the catalog → own, delisted
own_asins = own_asins | legacy_asins            # final own_asins, used in all classification below
# Keep legacy_asins separately so they can be labeled in the XLSX (see STEP 4)
```

> If `legacy_asins` isn't empty, note it in the XLSX banner and the chat summary: "N own ASINs
> detected only from history (delisted / outside the active catalog)." These won't have a name in
> `get_product_catalog_bulk` (they return "Not found") — label them `"[Legacy/Delisted ASIN]"` in
> the name column.

The same pair `(anchor, partner)` can appear in several months with different `pct`, or be absent
in some (drops out of the top-3 that month). Aggregate like this:

```python
from collections import defaultdict

agg = defaultdict(list)  # (anchor, partner) -> [(month, pct, rank), ...]
for r in raw_rows:
    agg[(r["anchor"], r["partner"])].append((r["month"], r["pct"], r["rank"]))

def pair_stats(obs, months_available):
    months_present = len(obs)
    avg_pct   = sum(pct for _, pct, _ in obs) / months_present
    best_rank = min(rank for _, _, rank in obs)
    consistency  = months_present / months_available
    basket_score = avg_pct * consistency

    # Low-confidence flag: only one month of history AND an extreme % (near 0% or near 100%).
    # With a single month of sample, an extreme % is almost always low volume (few total orders
    # that month), not a real pattern. Do NOT hide it: flag it explicitly.
    low_confidence = months_present == 1 and (avg_pct >= 0.5 or avg_pct <= 0.05)

    return dict(months_present=months_present, avg_pct=avg_pct, best_rank=best_rank,
                basket_score=basket_score, low_confidence=low_confidence)

pair_stats_by_key = {k: pair_stats(obs, months_available) for k, obs in agg.items()}
```

**Bidirectional own+own pairs — do NOT collapse to a single direction.** If `(A,B)` and `(B,A)`
both exist, **show both directions explicitly** in the same row (e.g. `"100.0% (A→B) / 18.8% (B→A)"`),
never just the higher one — collapsing hides the asymmetry and can overstate the pair's real strength:

```python
def build_own_pair_rows(pair_stats_by_key, own_asins):
    seen = set()
    rows = []
    for (anchor, partner), stats in pair_stats_by_key.items():
        if partner not in own_asins:
            continue
        key = frozenset((anchor, partner))
        if key in seen:
            continue
        seen.add(key)
        reverse = pair_stats_by_key.get((partner, anchor))
        if reverse:
            # Bidirectional: conservative score = the LOWER of the two scores (not the higher)
            basket_score  = min(stats["basket_score"], reverse["basket_score"])
            low_confidence = stats["low_confidence"] or reverse["low_confidence"]
        else:
            basket_score, low_confidence = stats["basket_score"], stats["low_confidence"]
        rows.append(dict(anchor=anchor, partner=partner, fwd=stats, rev=reverse,
                          basket_score=basket_score, low_confidence=low_confidence))
    return rows
```

> **Why the conservative score (min, not max):** if `A→B` is 100% but `B→A` is 18.8%, keeping the
> 100% sells a stronger pair than it really is. Use the lower of the two scores to sort, and show
> **both numbers** in the cell so the asymmetry is visible.

**Why Basket Score and not just `avg_pct`:** a pair that appears at 30% in a single month (possible
noise / one-off spike) shouldn't rank above one that appears at 12% across all 6 months (consistent
signal). The score weighs both. Show `avg_pct` and `months_present` as separate columns alongside
the score so the logic is auditable.

**Name enrichment:**
- Own ASINs (anchor and own partner): `get_product_catalog_bulk` for title/price.
- External ASINs: a title may not be available (other sellers') → leave the name blank; the ASIN
  is enough as an SD target.

---

## STEP 4: Build the XLSX (openpyxl, Sophie Society brand)

Canonical palette (sophie-brand): header `#13835B` white text; light green `#E8F5F0`;
gray `#F5F5F5`; text `#1A1A1A`; gold `#F5A623`.

> **ALL XLSX text is in English** (headers, banners, notes, actions). Do not use `report_language`
> for this skill.

**Column-naming rule (beginner-friendly):** every header uses a **plain-English name with the
technical term in parentheses**, e.g. `How Often Bought Together (Avg Combination %)`. The plain
name comes first so a non-expert reads it instantly; the parenthetical keeps it precise for the team.

> **Context banner (top of the Bundle tab), always present, in English:**
> `"Window: last {months_available} months ({first_month} → {last_month}) · Amazon reports the
> top 3 partners per product per month · Opportunity Score = Avg Combination % × Consistency
> (months present / {months_available})."`
> If `months_available < MONTHS_WINDOW` requested, add in gold: "⚠ this store only has
> {months_available} months of Market Basket history available."

### Formatting standards (apply to EVERY data tab — Tabs 2, 3, 4)

These four upgrades are what make the file readable for a non-expert. Apply all of them.

**(1) Group rows by anchor product — don't ship a flat list.**
In `Bundle & Cross-Sell` and `Ad Targeting`, keep all rows of the same anchor **contiguous**.
Order the anchor groups by each group's **best (max) Opportunity Score** desc, and within a group
sort partners by Opportunity Score desc. Make the grouping visible AND keep it filterable:

```python
# Sort: strongest anchor group first, strongest partner first within the group
groups = {}                     # anchor -> [row, ...]
for r in rows:
    groups.setdefault(r["anchor"], []).append(r)
group_order = sorted(groups, key=lambda a: max(x["basket_score"] for x in groups[a]), reverse=True)

excel_row = 2                   # row 1 = headers
for gi, anchor in enumerate(group_order):
    members = sorted(groups[anchor], key=lambda x: x["basket_score"], reverse=True)
    band = "#FFFFFF" if gi % 2 == 0 else "#E8F5F0"   # alternate the band PER GROUP, not per row
    first_row_of_group = excel_row
    for m in members:
        write_row(excel_row, m, fill=band)
        # native Excel outline so the user can collapse/expand each anchor
        ws.row_dimensions[excel_row].outline_level = 1
        excel_row += 1
    # medium top border on the first row of each group = clean visual separator
    apply_top_border(first_row_of_group, weight="medium")
ws.sheet_properties.outlinePr.summaryBelow = False
```

- Repeat the anchor ASIN/name in **every** row of the group (do **not** merge or blank them) so
  autofilter and sorting stay intact.
- The per-group color band + top border reads as a group at a glance; the outline lets the user
  collapse an anchor to a single line.

**(2) Strength traffic light — a `Strength` column, first signal column after the names.**
One glyph so a non-expert judges a row without reading numbers. Rule (uses the conservative score
if bidirectional):

```python
def strength(basket_score, low_confidence):
    if low_confidence:            return "🔴 Low data"
    if basket_score >= 0.10:      return "🟢 Strong"
    if basket_score >= 0.04:      return "🟡 Medium"
    return "🔴 Weak"
```

Also add a **3-color scale conditional format** on the `Opportunity Score` column (red → yellow →
green, low → high) so the number itself is shaded. Keep the glyph column AND the color scale —
the glyph is the plain read, the scale is the gradient.

**(3) Clickable Amazon links on every ASIN.**
Make each ASIN cell a hyperlink to the product page so someone with zero Amazon knowledge can open
it. Pick the domain by marketplace (default `.com`):

```python
AMZ_DOMAIN = {  # extend as needed; key by marketplace_id or country
    "US": "amazon.com", "CA": "amazon.ca", "UK": "amazon.co.uk", "DE": "amazon.de",
    "FR": "amazon.fr", "ES": "amazon.es", "IT": "amazon.it", "MX": "amazon.com.mx",
    "JP": "amazon.co.jp",
}
def asin_link(asin, domain="amazon.com"):
    return f"https://www.{domain}/dp/{asin}"
# cell.hyperlink = asin_link(asin, dom); cell.value = asin; cell.style = "Hyperlink"
```

Apply to own AND external ASINs (external is where it helps most — no catalog name to go on).
Legacy/delisted ASINs still get a link (it just may 404) — that's fine, don't special-case them.

**(4) Pro formatting on every data tab.**
- **Auto column widths**: size each column to its longest cell (cap ~55 chars for name columns; wrap text there).
- **Real percentage format** on any **single-direction** `Avg Combination %` cell → number format `0.0%`
  (store the numeric fraction, not a string). Bidirectional cells stay the combined string
  `"100.0% (A→B) / 18.8% (B→A)"` — Excel can't make one cell two numbers, and showing both directions wins.
- **`Opportunity Score`** → number format `0.000`, right-aligned.
- **AutoFilter** on the header row of every data tab (`ws.auto_filter.ref = ws.dimensions`).
- **Freeze panes** below the header and to the right of the name columns: `freeze_panes = "E2"` on
  Bundle/Ad Targeting (keeps Main Product + partner + name + strength visible while scrolling right),
  `"A2"` on All Data.
- Header row: bold, white text, tab's header color, `wrap_text=True`, row height ~30.
- Numbers right-aligned; text left-aligned; vertical-align top on wrapped cells.

### Tab 1: `Start Here` (NEW — first tab, plain English, no numbers required)

This is the tab a non-expert reads first. Build it so it stands alone without any chat context.

Layout (single column of stacked sections, Sophie header band on top):
1. **Title band** (`#13835B`, white): `"{Brand} — Bundle & Cross-Sell Finder"` + `"Generated {today} · Window: last {months_available} months"`.
2. **What this file is** — 2–3 plain sentences: *"When shoppers buy your product, Amazon tells us
   what else they bought in the same order. This file turns that into two lists: products of yours
   worth bundling or cross-selling, and other sellers' products worth targeting with ads."*
3. **How to read it** — one line per tab (mirror the tab list from the intro), e.g.
   *"Bundle & Cross-Sell tab → your own products bought together. Ad Targeting tab → others'
   products to target with Sponsored Display ads. All Data → raw month-by-month rows. Glossary →
   every column explained."*
4. **Top opportunities** — a small table of the **top 5 rows from the Bundle & Cross-Sell tab**
   (sorted by Opportunity Score desc, excluding ⚠ Low-confidence rows if enough non-flagged rows
   exist). Columns: `Strength` (🟢/🟡/🔴 glyph), `Main Product`, `Bought Together With`, `How Often`,
   `What To Do`. Plain values only; the ASIN behind each product name is a clickable Amazon link.
   If there are no own+own pairs, say so in one line and point to the Ad Targeting tab instead.
5. **One-line caveat** — *"These are starting points based on past buying patterns, not guarantees.
   Rows marked ⚠ Low need more data before acting."*

Header `#13835B`. No frozen panes needed (it's a readable page, not a data grid).

### Tab 2: `Bundle & Cross-Sell` (own + own pairs)

| Col | Header (plain name + technical) |
|---|---|
| A | Main Product (Anchor ASIN) — **clickable Amazon link** |
| B | Main Product Name |
| C | Bought Together With (Own ASIN) — **clickable Amazon link** |
| D | Bought-Together Product Name |
| E | **Strength** — 🟢 Strong / 🟡 Medium / 🔴 Weak or Low-data (from `strength()`) |
| F | **How Often Bought Together (Avg Combination %)** — if bidirectional, show **both directions**: `"100.0% (A→B) / 18.8% (B→A)"`, never just one; single-direction cells stored as a real `0.0%` number |
| G | Months Seen (out of {months_available}) — both directions if they differ |
| H | Best Rank (1 = strongest) |
| I | **Opportunity Score (Basket Score)** — if bidirectional, the **conservative** value (min of the two), not the max; format `0.000` + 3-color scale |
| J | **Data Confidence** — `"⚠ Low (1 month, extreme %)"` if `low_confidence=True`; otherwise "OK" |
| K | What To Do (Suggested Action) — "Bundle listing" / "Cross-sell campaign" / "SD self-targeting" |

**Rows grouped by anchor** (see Formatting standards): anchor groups ordered by best score, partners
by score within each. Header `#13835B`. `freeze_panes = "E2"`. AutoFilter on the header row.

> **Data Confidence flag:** a pair with `months_present == 1` and an extreme `avg_pct` (≥ 50% or
> ≤ 5%) signals **low volume**, not a real pattern — a 100%/0% from a single monthly sample isn't
> as strong as a steady 12% over 4 months. Flag it explicitly; never hide it or "smooth" it into the average.

> **What To Do** (rule on `avg_pct` + `months_present`, using the conservative side if bidirectional):
> - `avg_pct ≥ 0.15` **and** `months_present ≥ months_available/2` **and NOT** `low_confidence` → "Bundle listing".
> - `avg_pct ≥ 0.10` and not low-confidence → "Cross-sell campaign (SP/SB)".
> - `low_confidence = True` → "Needs more data (low volume) — monitor before acting".
> - Otherwise → "SD self-targeting (defensive)" as an always-viable floor.

### Tab 3: `Ad Targeting (Sponsored Display)` (external partner)

| Col | Header (plain name + technical) |
|---|---|
| A | Your Product (Anchor ASIN, own) — **clickable Amazon link** |
| B | Your Product Name |
| C | Product to Target (External ASIN) — **clickable Amazon link** |
| D | Type (Book/Media or Product) |
| E | **Strength** — 🟢 / 🟡 / 🔴 (same `strength()` rule as Tab 2) |
| F | How Often Bought Together (Avg Combination %) — real `0.0%` number |
| G | Months Seen (out of {months_available}) |
| H | Best Rank (1 = strongest) |
| I | **Opportunity Score (Basket Score)** — format `0.000` + 3-color scale |
| J | **Data Confidence** — same flag as Tab 2 |
| K | Suggested Campaign — "SD Product Targeting", or "Needs more data (low volume)" if `low_confidence` |

**Rows grouped by anchor** (see Formatting standards): all targets for one of your products sit
together, groups ordered by best score, targets by score within. Header in secondary green
`#0D5C3F`, white text. `freeze_panes = "E2"`. AutoFilter on the header row.
This is the ready-to-load list of ASINs to target in Sponsored Display. Close with a note in English:
external product names don't come from the client's catalog — the Amazon link lets you open each
one; look them up in Seller Central / Product Opportunity Explorer before launching.

### Tab 4: `All Data` (raw reference, month by month)

All raw rows, un-aggregated. English headers: Month, Main Product (Anchor ASIN), Bought-With ASIN,
Own or External, Rank, Combination %. Both ASIN columns are **clickable Amazon links**; Combination %
uses the real `0.0%` number format. Header gray `#7A7A7A`, `freeze_panes = "A2"`, AutoFilter on.
Lets the user audit month by month where the aggregate comes from — here each direction of a pair is
shown separately, not collapsed.

**Naming footer** in Tab 2: a context row in English with
`"Client: {Brand} | Date: {today} | Own ASINs detected: {n} | Unique pairs: {m} | Window: {months_available} months"`.

### Tab 5: `Glossary` (ALWAYS included, last tab — not optional)

Explains, in simple English with no jargon, what each column across Tabs 2–4 means. This is the
tab the user shares with teammates who didn't watch the process — it must stand alone. Format:
two columns, **Term** | **What it means**, one row per term, header `#7A7A7A`, text `#1A1A1A`,
zebra rows like the other tabs.

Minimum contents (wording adjustable, but cover every term — list both the plain and technical name):

| Term | What it means |
|---|---|
| Main Product (Anchor ASIN / Name) | The product Amazon's report is measuring purchases *from* — the starting point of the pair. |
| Bought Together With / Product to Target | The other product that showed up in the same order as the main product. |
| How Often Bought Together (Avg Combination %) | Of the customers who bought the main product in a given month, what % *also* bought this other product in the same order — averaged across the months this pair showed up. Not a count of orders, a percentage of the main product's buyers. |
| Months Seen (n / N) | Out of the N months analyzed, how many months this pair showed up in Amazon's top-3 list for the main product. Low number = less consistent signal. |
| Best Rank | The best (lowest number = strongest) rank this pair reached in any single month. Amazon ranks the top 3 partners 1–3 per product per month. |
| Opportunity Score (Basket Score) | Avg Combination % × (Months Seen / N). Combines strength and consistency into one number so a single-month spike doesn't outrank a pair that shows up reliably every month. Used to sort every tab. |
| Strength (🟢/🟡/🔴) | A quick traffic light built from the Opportunity Score and Data Confidence: 🟢 Strong (score ≥ 0.10), 🟡 Medium (0.04–0.10), 🔴 Weak or Low-data. Read this first if you don't want to read the numbers. |
| Amazon link (on ASINs) | Every ASIN cell is a clickable link to that product's Amazon page (amazon.com/dp/ASIN, or the matching marketplace domain). External-product links may sometimes not resolve if the item was removed. |
| Data Confidence | Flags pairs based on only 1 month of data AND an extreme % (≥50% or ≤5%) — likely low order volume, not a real pattern. Treat "⚠ Low" pairs as needing more data before acting on them. |
| Bidirectional | A pair where BOTH directions exist in the data (A bought with B, and B bought with A) — shown as two values ("X% (A→B) / Y% (B→A)") instead of picking the higher one, since the two directions can differ a lot depending on each product's own sales volume. |
| Type (External) | Whether a non-owned co-purchased ASIN is a Book/Media product (ISBN-style ASIN) or another type of Product — useful for splitting SD campaigns by category. |
| What To Do / Suggested Campaign | An automatic recommendation based on the strength, consistency, and confidence of the pair — not a guarantee, a starting point for review. |
| Own / External (All Data tab) | Whether the bought-with ASIN belongs to this brand's own catalog (Own) or to a different seller (External). |
| [Legacy/Delisted ASIN] | An ASIN that no longer appears in the current product catalog but showed up as its own anchor in Amazon's historical report — confirming it belongs to this brand, even though it's since been removed or discontinued. |

If the user asks to adjust terms or add one (because a new column is added to the skill later),
this tab updates alongside the rest — it should never go stale.

---

## STEP 5: Save and deliver

```
Path:   G:\My Drive\Claude\Clients\[BrandName]\Bundle Finder\
Name:   MMDDYYYY_[BrandName]_Bundle & Cross-sell Finder.xlsx
```

Create the folder if it doesn't exist (`google_drive_search` → upload). `present_files` the XLSX
in the chat.

**Chat summary — plain English, friendly, no jargon.** Use this shape:

```
✅ Bundle & Cross-Sell Finder is ready for {Brand}.

📊 What I looked at: {months_available} months of "bought together" data ({first_month} → {last_month}).

🎁 Bundle / cross-sell ideas (your own products): {n_bundle}
   Top pick: {Main Product Name} + {Bought-Together Name} — bought together {top_pct} of the time.
🎯 Ad targeting ideas (other sellers' products): {n_sd} ASINs ready for Sponsored Display.

📄 Full breakdown is in the spreadsheet — start on the "Start Here" tab.
```

- If any rows are ⚠ Low confidence, add one line: `⚠ {k} pairs are based on limited data — the file marks them so you know to double-check before acting.`
- If `legacy_asins` isn't empty: `ℹ {len} of your products showed up only in older history (delisted / discontinued) — they're labeled in the file.`
- If the store was resolved via `list_stores` (no config): add the one-line reminder to persist `sophie_store_id`.

---

## Edge Cases

| Situation | Behavior |
|---|---|
| Sophie Hub not connected / `list_stores` empty or errors | Tell the user Sophie Hub isn't connected and stop — nothing works without it |
| Store not specified | Show the `list_stores` picker (STEP A1) |
| Config not found | Not a blocker — proceed with the store picked in STEP A; a config only saves a step |
| `sophie_store_id` absent | Resolve via `list_stores`; remind (once) to persist it |
| Market Basket has no data | Tell the user — the brand may not have Brand Analytics enabled, or has low volume |
| **Store with fewer than the requested months of history** | Use the months available; warn in the gold banner ⚠ with the real number |
| **Individual monthly report empty** (`dataByAsin` empty) | Skip it, continue with the other months, don't fail |
| **Pair present in few months with a high %** (possible noise) | Opportunity Score penalizes it vs. consistent pairs; and if `months_present==1` with an extreme % → explicit "⚠ Low" confidence flag |
| **Bidirectional own+own pair** | Show **both directions** in the same row (`"X% (A→B) / Y% (B→A)"`); Opportunity Score = the conservative (min), not the max. Never collapse to one direction |
| **Anchor not in `list_product_catalog`** | It's an own ASIN that was delisted (Amazon only generates anchors from the seller's own products) — add it to `own_asins`, label it `"[Legacy/Delisted ASIN]"` (no name via `get_product_catalog_bulk`, returns "Not found"), and note it in the XLSX banner |
| `list_product_catalog` unavailable | Fall back to managed_asins as the own set and flag it in the XLSX |
| All pairs are external | Bundle tab empty with a note; focus on Ad Targeting |
| All pairs are own | Ad Targeting tab empty with a note; focus on Bundle/Cross-Sell |
| External partner has no title | Leave the name blank; the ASIN is enough for SD targeting |
| User anchors on one specific ASIN (STEP A3) | Filter each month's `dataByAsin` to rows where that ASIN is **either `asin` OR `purchasedWithAsin`** (both directions) before aggregating — never `asin` only, or you lose the "siblings bought WITH it" signal for hub products. See STEP A3 |
| User picks another window (e.g. 12 months) | Adjust `MONTHS_WINDOW` and reflect it in the banner |
