# Input Parsing

Exact steps and quirks for each supported input. Applies across both supported modes (flat file / screenshot). For Category Listings Report parsing, validation, and writing, see `flat-file.md` — this file covers SQP, reviews, Xray, and PPC reports only.

## Category Listings Report (flat-file mode)

Moved to `flat-file.md`. That file covers the full lifecycle: template-sheet discovery, attribute-row detection (row 4 vs row 5 depending on template version), validation, column mapping, and writing back a partial-update xlsx. Read `flat-file.md` for anything flat-file related.

---

## Seller Central screenshot (Mode 3 only)

A screenshot of the Seller Central edit-listing page as a last-resort input when no flat file is available.

### What to extract via OCR

- ASIN (top of page, after "ASIN:")
- Product title (Product Name field)
- Bullet points (Key Product Features section)
- Product description (Description section)
- Product type / category (visible in page header or side panel)
- Any visible structured attributes (Item Type, Target Audience, etc.)

### Limitations (call these out prominently in the HTML)

- **OCR noise:** small text, numbers, special characters, trademark symbols often mistranscribe
- **Collapsed sections:** the edit-listing page has many collapsible sections. If the seller didn't expand them before screenshotting, structured attributes appear empty when they may be populated
- **Truncated bullets:** long bullets that wrap beyond the visible frame are cut off
- **No backend search terms:** backend terms live on a separate tab; one screenshot of the main page won't show them
- **Single ASIN only:** each screenshot is one listing

### When to recommend switching modes

If the seller provides only a screenshot and you can see they have multiple ASINs to audit, recommend: "For multi-ASIN audits, the Category Listings Report upload (Mode 2) is more reliable. Would you like to switch modes?"

If critical fields appear blank due to collapsed sections, prompt the seller to screenshot again with sections expanded.

---

## SQP (Search Query Performance) Export

**File pattern:** `<CC>_Search_Query_Performance*.csv` in `/mnt/user-data/uploads/`, where `<CC>` is the two-letter marketplace country prefix Amazon prepends (`US_`, `UK_`, `DE_`, `FR_`, ...). The detector matches `^[a-z]{2}[_ ]search[_ ]query[_ ]performance.*\.csv$` (case-insensitive), so any marketplace's export is picked up, not just US.

Amazon Brand Analytics export. One row per search query, per ASIN, per reporting period.

### Header structure

Row 0 contains filter metadata like `"Marketplace=[""ATVPDKIKX0DER""]","ASIN or Product=[""B0..."", ""B1...""]","Reporting Range=..."`. Parse this to identify which ASIN(s) the file covers.

Row 1 is empty. Row 2 has two-level column headers — primary category (Impressions, Clicks, Cart Adds, Purchases) over secondary metrics (Total Count, ASIN Count, ASIN Share %, Click Rate %, etc.).

Row 3 and beyond are data rows.

### Parsing

```python
import pandas as pd
# Parse top row to get the ASIN(s) this file covers
with open(path) as f:
    filter_line = f.readline()
# Extract ASINs via regex from filter_line — looking for 10-char alphanumeric patterns after "ASIN or Product="

# Read the body with a 2-row header
df = pd.read_csv(path, header=[2, 3], skiprows=1)
# Flatten the two-level column index
df.columns = [f"{a}: {b}".strip() if b else a for a, b in df.columns]
```

### Key columns

| Column (flattened) | What it means |
|---|---|
| `Search Query` | the literal query text |
| `Search Query Score` | Amazon's internal relevance score (proxy for volume) |
| `Search Query Volume` | unique searches for this query in the reporting period (the denominator for all rate fields below) |
| `Impressions: Total Count` | market-level impressions for this query (all ASINs, all shoppers) |
| `Impressions: ASIN Count` | your ASIN's impressions for this query |
| `Impressions: ASIN Share %` | your share of impressions |
| `Clicks: Total Count` | market-level clicks |
| `Clicks: Click Rate %` | **% of searches that produced any click** = `Clicks: Total Count / Search Query Volume`. This is NOT clicks-per-impression. Typical values 30–60%. |
| `Clicks: ASIN Count` | your clicks |
| `Clicks: ASIN Share %` | your share of clicks |
| `Cart Adds: Total Count` | market-level cart adds |
| `Cart Adds: Cart Add Rate %` | **% of searches that produced a cart add** = `Cart Adds: Total Count / Search Query Volume`. Typical 3–15%. |
| `Purchases: Total Count` | market-level purchases |
| `Purchases: Purchase Rate %` | **% of searches that produced a purchase** = `Purchases: Total Count / Search Query Volume`. Typical 1–8%. |
| `Purchases: ASIN Count` | your purchases |
| `Purchases: ASIN Share %` | your share of purchases |

### CRITICAL — rate fields are search-denominated, not impression-denominated

Amazon's `Click Rate %`, `Cart Add Rate %`, and `Purchase Rate %` in SQP all divide by `Search Query Volume` (unique searches), NOT by impressions or by the preceding funnel step. This is counter-intuitive because the names suggest otherwise.

**What this means for diagnostics:**

- **There is no market "CTR" in SQP.** If you want clicks-per-impression, compute it yourself: `Clicks: Total Count / Impressions: Total Count`. This is typically 1–3% and IS comparable to your ASIN's clicks/impressions.
- **"Market CVR-from-clicks" must be computed manually**: `Purchases: Total Count / Clicks: Total Count`. Typical 1–5%. Do NOT use `Purchases: Purchase Rate %` as "market CVR-from-clicks" — they're different denominators.
- **When comparing your ASIN's per-query performance to the market**, always compare like-to-like:
  - Your CTR (clicks/impressions) vs Market CTR (`Clicks: Total Count / Impressions: Total Count`)
  - Your CVR-from-clicks (purchases/clicks) vs Market CVR-from-clicks (`Purchases: Total Count / Clicks: Total Count`)

The `Click Rate %` and `Purchase Rate %` fields from SQP remain useful as absolute measures of query health (how often does this search convert to anything at all?) — but they are NOT benchmarks for your ASIN's CTR or post-click CVR.

### ASIN matching

The same SQP file may cover multiple ASINs. If so, group rows by the ASIN column if present, or by the filter metadata. When in doubt, ask the seller which ASIN the data should be attributed to.

---

## Helium 10 Review Insights

**File pattern:** `Helium_10_Review_Analysis_-_<ASIN>.xlsx` — one file per ASIN. Multiple files can be present for multi-ASIN audits.

The ASIN is embedded in the filename. Extract via regex: `([A-Z0-9]{10})`.

### Sheet structure

Two sheets of interest:

- **Positive Topic Insights** — positive themes with ASIN %, Category %, star-rating impact, sample review snippets
- **Negative Topic Insights** — same columns but for negative themes

### Key columns

| Column | Meaning |
|---|---|
| `Topic` | theme name (short phrase) |
| `ASIN Percentage of Reviews Mentioned %` | % of reviews on this ASIN that mention this theme |
| `Category Percentage of Reviews Mentioned %` | % of reviews across the category that mention it |
| `ASIN Impact on Star Rating` | signed float — how much this theme moves this ASIN's rating |
| `Category Impact on Star Rating` | same for the category |
| `Review Snippets` | actual customer sentences (sometimes multiple, semicolon-separated) |

### Trusted threshold check

Before mining themes, verify the ASIN has enough reviews. Read the total review count — either from the sheet summary, the flat file (`customer_reviews_count` column if present), or a separate Xray file. If under the category family's minimum (50 for most categories, 100 for apparel, 30 for electronics — see `category-families.md`), flag "review data below trustworthy threshold" and skip the theme mining.

### Vocabulary extraction — voice quality rule

Use review snippets as **concept sources**, not sentence templates. Paraphrase into brand voice.

- Snippet: "calms my racing mind without leaving me feeling foggy the next morning"
- Concept extracted: "calm without fog"
- Brand-voice copy: "Supports a calm mind without feeling foggy in the morning"

Never copy-paste a review sentence into listing copy. Customer sentences include personal markers ("I felt...", "my husband...") that read as off-voice. See `rewrite-rules.md` on voice quality.

---

## Helium 10 Xray (ASINs)

**File pattern:** `Helium_10_Xray_<date>.csv`. Competitive intelligence on the top 20-50 ASINs for a seed search.

### Key columns

| Column | Meaning |
|---|---|
| `ASIN` | the competitor ASIN |
| `Product Details` | title |
| `Brand` | seller brand (flag if the seller's own brand appears — not a competitor, exclude) |
| `Price` | listed price |
| `Monthly Revenue` | Helium 10's estimate |
| `Ratings` | star rating |
| `Review Count` | review count |
| `Images` | image count |
| `BSR` | Best Sellers Rank |
| `Display Order` | ranking position in the seed search (1 = top of page 1) |

### Exclude own brand

When comparing against competitors, filter out the seller's own brand (match on Brand column, case-insensitive). Otherwise the seller appears as their own competitor, which makes the comparison nonsensical.

### Use cases

- Title length / image count benchmarks (see `diagnostic-rules.md`)
- Price percentile detection
- Positioning white-space (tokenize all competitor titles, find low-frequency terms)

---

## Helium 10 Xray (keywords)

**File pattern:** `Xray_Keyword<date>.csv` — market-level keyword search volume context, one row per keyword.

### Key columns

| Column | Meaning |
|---|---|
| `Keyword Phrase` | the query |
| `Search Volume` | Helium 10's monthly volume estimate |
| `Keyword Sales` | estimated units sold monthly on this query |
| `CPR` | Cerebro Product Rank (Helium 10's internal metric) |
| `Competing Products` | number of results on the SERP |

Use primarily as a second-opinion on SQP volume rankings — if SQP shows a query as high-volume but this file shows near-zero estimated volume, flag the discrepancy.

---

## PPC Search Term Report

**File pattern:** varies. Campaign Manager export or AdLabs search-term CSV. Detect by columns.

### Key columns (varies)

| Campaign Manager | AdLabs | Meaning |
|---|---|---|
| `Customer Search Term` | `search_term` | query text |
| `Impressions` | `impressions` | impressions |
| `Clicks` | `clicks` | clicks |
| `Spend` | `cost` | dollars spent |
| `7 Day Total Sales` | `sales` | attributed sales |
| `7 Day Total Orders (#)` | `orders` | attributed orders |
| `ACoS` | `acos` | advertising cost of sale |
| `Advertised ASIN` | `advertised_products` | ASIN the ad was for |

### Processing

See `diagnostic-rules.md` on the PPC harvest filter (`orders > 0 AND acos < 50%`), grouping, and top-20 by orders. Also detect negatives (`spend > $5 AND orders = 0`).

### ASIN matching

The report covers the account's ads but may include ASINs outside the current flat file (e.g., if the seller advertises products they're not auditing). Filter to the ASINs in the current audit set. Flag ASINs referenced in the PPC report but missing from the flat file as a reconciliation mismatch.

---

## What to do when inputs disagree

Occasional cross-input conflicts:

- SQP shows your ASIN ranking for "kava gummies sleep" but flat file's `product_type` is unrelated → trust the flat file's product_type (structural), note the SQP-visible search-term usage in the HTML
- Review file ASIN doesn't match any ASIN in the flat file → flag as reconciliation mismatch, skip that review file for the current audit
- PPC search terms reference ASINs that look like variants (e.g., B0DNRL8MLX in flat, B0DNBPLZC7 in PPC) → flag. Could be parent/child mismatch or different listing entirely. Don't merge.

Print reconciliation issues upfront in chat so the seller knows what was kept and what was skipped.
