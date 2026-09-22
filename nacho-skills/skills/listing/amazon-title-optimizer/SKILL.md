---
name: amazon-title-optimizer
description: >
  Optimizes existing Amazon titles and writes Item Highlights to the current format (title <=75
  chars incl. spaces, Item Highlights <=125), SEO + AI/Alexa optimized and data-driven from
  Sophie Hub. Triggers on "optimize my title", "rewrite Amazon titles", "fix titles for the 75
  character format", "create item highlights", "title and item highlights optimization", or a
  brand plus ASIN(s) with a request for better-performing titles. Per ASIN it pulls the PPC
  Search Term Report, Brand Analytics SQP, and the catalog, derives a market-CVR benchmark, and
  produces 3-4 paired Title + Item Highlights options (each with a data rationale) presented in a
  Sophie-Society-branded PowerPoint deck (option slides + a data slide per ASIN), delivered as a
  download (open in PowerPoint or Google Slides). Pure-stdlib scripts do the deterministic math and
  validation; copywriting is in-context. Full pipeline, rules, and data contracts are in the body
  below. Self-contained except the Sophie brand palette.
---

# Amazon Title + Item Highlights Optimizer

Turns an ASIN's *existing* title into **3–4 optimized Title + Item Highlights options** that fit
Amazon's current listing format and are driven entirely by that ASIN's own performance data. The deliverable
is a **Sophie-Society-branded PowerPoint deck** — per ASIN: **option slides** (2 options each, as
client-facing cards, so a 4-option run gets 2 slides) **+ a data/insights slide**, delivered as a
**download** (open in PowerPoint or Google Slides). Fully branded, and corruption-proof because it
ships as a file — never pushed through Drive as base64.

> **Code footprint:** The skill ships **three** stdlib scripts; pure-local, no network.
> - `scripts/analyze.py` — the **deterministic data engine**: aggregates STR + SQP, computes the
>   market-vs-ASIN CVR benchmark, picks the anchor(s) + hedge, and finds trending terms. Exact and
>   identical for every teammate/run, and it keeps big reports out of the context window (lower
>   usage). Stdlib only.
> - `scripts/validate.py` — the **deterministic validation rules** (exact char counts, allowed
>   characters, promo/caps/repetition, restricted-keyword scan). Stdlib; imported by build_pptx.
> - `scripts/build_pptx.py` — renders the **branded PowerPoint deck** (the
>   deliverable). Needs `python-pptx` (auto-installs).
>
> What stays **in-context** (the model): the **semantic judgment** that code can't do — which SQP
> queries are on-product, dropping competitor-brand terms, and **writing the titles/highlights**.
> You self-check copy as you write; `build_pptx.py` (via `validate.py`) is the final gate on
> Pass/Fail — failing options are not shown and trigger a console WARNING to fix and re-run.

> **Self-containment rule:** Every rule, threshold, and word list lives in *this package*
> (`SKILL.md` + `references/`) or comes from a live connector. Do **not** import logic from any
> other skill. The only thing reused from outside is the Sophie Society brand palette (below).

---

## Format targets (the whole point)

| Field | Limit | Notes |
|---|---|---|
| **Title** | **≤ 75 characters incl. spaces** | All categories **except media** (books, music, video, DVD). Media ASINs are flagged and skipped for the length rule. |
| **Item Highlights** | **≤ 125 characters incl. spaces** | Searchable; shown below the title in search results & on the detail page. Use for materials / recommended use-cases that help shoppers compare. |

The Title's job is to **earn the click and own indexing** — not to "sell". It must read naturally
(no keyword stuffing) and lead with the strongest performing term.

---

## Prerequisites (tell the user if missing)

1. **Sophie Hub MCP** connected — for the Search Term Report, SQP, and listing data. **Confirm the
   connector before running** (call `list_stores`; if it returns stores, the connector is live).
   Note: a `get_product_catalog` "not found" or an empty `list_product_catalog` is **common and does
   NOT mean the connector is broken or the data is missing** — use the Step 1 fallback chain
   (`list_top_products`) to get the title. Only fall back to a **manual upload** (STR `.xlsx`, SQP
   `.csv`/`.xlsx`, listing copy) if `list_stores` itself fails or every Step 1 source comes back
   empty.
2. **Python 3** in the sandbox — runs `analyze.py` (stdlib) and `build_pptx.py`, which `pip install`s
   **python-pptx** on first run if missing. The deck is delivered as a **download** from the Cowork
   outputs folder; Google Drive is **not** required (the deck is a file, never uploaded as base64).

---

## Intake — ask ALL of these BEFORE running

1. **Brand**.
2. **Which ASIN(s) do you want to run this for?** Accept **any number** — there is **no hard cap**.
3. **Batch size — framed explicitly as a TOKEN-USAGE / cost choice (ask once you know the count).**
   Make clear *why* you're suggesting a limit: each ASIN pulls catalog + STR + SQP and renders its
   own slides, so **more ASINs = more tokens and higher cost / longer runs**. There is **no hard
   cap** — this is purely to help them control token spend. Tell them the count and recommend:
   - **1–5 ASINs:** fine to run all at once.
   - **6–15:** doable in one go, but recommend batching in groups of **~5** to keep **token usage**
     down and the deck easy to review.
   - **16+:** recommend batches of **~5–8** across separate runs to manage **token usage**.
   Ask it as a cost decision, e.g.: *"To manage token usage I'd suggest ~5 ASINs per run — want me to
   run all N now, or batch into groups of K?"* State plainly that the limit is **only about token
   usage, not a capability limit**, and **honor their choice** (if they say run all, run all).
4. **Include the brand name in the title?** Default **No**. If yes, allow the brand and note it in
   the rationale. Ask once; apply to the whole run.
5. **Will you add a Product Opportunity Explorer (POE) search-term download for the niche?**
   Ask this explicitly before running. If **yes**, wait for them to upload the POE export and use
   its 180-day trend (it overrides the SQP period-over-period trend for the "trending up" logic).
   If **no**, proceed and derive the trend from SQP.
6. Confirm the **analysis window**: default **90 days**, fall back to **60** if 90 isn't available.

Do not re-ask for anything you can pull from the catalog.

---

## Usage discipline (cost control — without weakening the output)

Most of a run is fixed cost; the one big variable is the **size of the SQP / STR pulls**. Keep runs
cheap while keeping the analysis complete:

- **Calibrate first.** On a new account, run **one ASIN**, check `/cost` before and after, and
  multiply by your typical batch size to predict spend.
- **Always cap the pulls — but not below the data you need.** Pull SQP and STR with a `limit`
  (~50 rows) and the `asin` filter so you get that ASIN's queries, not the whole catalog. An
  *uncapped* SQP pull can exceed 100KB and dominate the run. To stay both cheap and on-target, add
  `search_query_contains` with a core product word (e.g. "eye mask") so you only pull on-product
  queries.
- **Quality gate — do not over-trim.** The benchmark must still see **every query where the ASIN
  had ≥ 1 purchase**. If a capped pull returns only a handful of relevant queries, raise the limit
  (or loosen the filter) and re-pull — a complete benchmark is worth the extra tokens. Stop trimming
  the moment it would drop converting queries; the deliverable's value comes first.
- **No hard ASIN cap** — but cost scales roughly linearly with ASIN count, so follow the intake
  batching recommendation (~5 per run is a good default; the operator decides).
- The row math (`analyze.py`) and the restricted-keyword scan (`validate.py`) run in the
  sandbox at ~0 model-token cost, so the data **pull** is the only thing you actively manage.

## Pipeline (per ASIN, one at a time)

### Step 1 — Pull the data (connectors)
**First resolve the store:** call `list_stores` and match the brand to its `seller_id`; pass that
`seller_id` as `store`/`seller_id` to every other Sophie Hub tool. Then, scoped to the window:

- **Existing listing + category — use this FALLBACK CHAIN; do NOT give up on the first miss.**
  Many stores have an **unpopulated catalog snapshot**, so `get_product_catalog` alone is unreliable.
  A "not found" there does **NOT** mean the product data is unavailable — it almost always is, via
  another tool. Work down this list:
  1. `get_product_catalog(seller_id, asin)` → best case: title, bullets, description, category,
     variation relationships.
  2. **If it returns "ASIN not found"/empty (or `list_product_catalog` shows 0 ASINs):** get the
     **current title** from `list_top_products(store, days=90, compact=false)` — locate the ASIN's
     row. Its title comes from the merchant-listings report and is reliable even when the catalog
     snapshot is empty. (This is the exact case that made earlier runs wrongly report "can't reach
     Sophie Hub product info" — fall through, don't stop.)
  3. **Category:** use the catalog `browseClassification`/`salesRanks` if present; otherwise infer
     the bucket from the product (for the restricted-keyword filter) and confirm with the operator if
     unsure.
  4. **Bullets / description:** if the catalog is empty, ask the operator to paste them — useful
     context but **not required**; the optimizer runs off the title + STR/SQP keyword data.
  Only ask for a full **manual upload** if every step above fails.
  *Variation note (relevance first):* `list_top_products` reveals the variation family. If the
  target ASIN is a **low-volume child with sparse SQP**, you MAY supplement with the **parent/hero
  ASIN's** SQP — but **relevance to THIS variation overrides "it's the same family."** Variation
  themes differ: a **pack-size** child (e.g. 16 vs 30 count) usually shares the parent's intent, but
  **color / scent / flavor / type / use-case** variations often draw genuinely **different search
  queries**. So: keep only the parent queries that truly match this product, weight the child's own
  data where it diverges, and if the intent clearly differs, do **not** inherit the family's
  queries — note the divergence in the rationale. Borrow family data for coverage, never at the cost
  of relevance to what this specific product actually is.
- **Search Term Report (PPC)** — `get_search_terms_top` / `query_ppc`. The *advertising* search-term
  report (impressions, clicks, spend, orders, CVR, CTR by customer search term).
- **Search Query Performance (SQP / Brand Analytics)** — `get_sqp_metrics`. The *organic market*
  report (search-query volume; market impressions/clicks/purchases; the ASIN's own
  impressions/clicks/purchases per query). Pull with the `asin` filter + a `limit` (~50), and
  optionally `search_query_contains` a core product word, to control tokens (see Usage discipline) —
  but confirm the result still includes every query where the ASIN converted.

### Step 2 — Analyze (deterministic — `scripts/analyze.py`)
First, the **semantic** step only you can do: from the SQP pull, **drop competitor-brand and clearly
off-product queries**, and **mark branded ones** (`is_branded: true`). For a variation, "on-product"
means relevant to **this variation's** theme (per the Step 1 Variation note) — don't keep a family
query that doesn't match this product just because the parent ranks for it. Then write the MCP pulls into
`outputs/<ASIN>_raw.json` in the "Data contract" shape (map the report columns to the field names)
and run:
```
python scripts/analyze.py --in outputs/<ASIN>_raw.json --out outputs/<ASIN>_analysis.json
```
The script does the exact math (so it is identical for every teammate and keeps big reports out of
context):
- **Aggregates within each report, never across them** — STR duplicate search terms across campaigns
  are summed and KPIs recomputed on the totals; SQP duplicate queries are combined. STR and SQP stay
  separate.
- **Numeric relevance:** keeps SQP queries with **≥ 1 ASIN purchase** (your semantic filter already
  ran upstream).
- **Benchmark:** per-query `market CVR = market purchases ÷ market clicks` and
  `ASIN CVR = ASIN purchases ÷ ASIN clicks`; then click-weighted aggregates, plus the STR ad-CVR as
  a corroborating signal. Verdict = **preserve** (ASIN ≥ market by ≥ 2 pts → keep content, change
  for format), **balanced**, or **flexible** (below market → freer rewrites).
- **Anchors:** volume-led visibility anchor (kept if its CVR ≥ market), the highest-CVR relevant
  term, and the **two-anchor hedge** flag (triggers when the top-volume term converts > 25%
  relatively below its market CVR).
- **Trending:** POE 180-day trend if supplied, else SQP period-over-period volume growth > 10%.

Read `analysis.json` back; if STR and SQP disagree on the verdict, lean to the more flexible reading
and note it in the rationale.

### Step 3 — Generate the options (anchor-driven title directions)
Each option = **Title + Item Highlights + a one-line "why" rationale** (name the term and the
number). They are anchor-driven, each a different risk/reach trade. Produce **3 by default, plus
Option 4 when a CTR-hedge anchor exists**:

1. **Volume anchor** — lead with the **highest search-volume term the ASIN already converts on**
   (`visibility_anchor`). Safest swap: proven demand, no need to win a new query cluster.
   `strategy` = `"Volume anchor"`.
2. **CVR hedge anchor** — lead with the term where the **ASIN's CVR beats market the most**
   (`high_cvr_anchor` / top strength term). Lower volume, higher win-rate — trades reach for
   relevance. `strategy` = `"CVR hedge anchor"`.
3. **Trend / differentiation** — build around a **trending-up term** (POE 180-day, else SQP growth)
   or a specific **use-case sub-niche**. Highest upside if the trend holds, riskiest (bets on
   forward demand). `strategy` = `"Trend / differentiation"`.
4. **CTR hedge anchor** *(include only if `anchor.ctr_hedge_anchor` is present)* — lead with the
   **highest-CTR term that also has real search volume** (the engine drops the low-volume tail so the
   pick still drives visibility, then ranks by CTR) **and has room to improve CVR** (clicks well,
   converts below its market rate). CTR is the lead signal; CVR is the **secondary** metric. Useful
   mid creative-test. `strategy` = `"CTR hedge anchor"`. If `ctr_hedge_anchor` is null, ship 3.

Across all options, the **Item Highlights** carry materials, benefits, and — where the product has
them — **variation details** (size, color, scent, count), as readable copy.

**Title ↔ Item Highlights must complement, not repeat** — the highlights *extend* coverage; do not
restate the title's multi-word phrases or its use-cases (only the core product noun may appear in
both). See `copy-rules.md`.

**Two-anchor hedge:** when `two_anchor_hedge` is true (top-volume term converts >25% below its
market rate), Option 1 takes the visibility term and Option 2 takes the high-CVR term — that split
*is* the hedge; call it out in the rationale.

**Thin / no data?** If an ASIN lacks a clear trend, sub-niche, or CTR-hedge term, ship the options
that do apply (minimum the Volume + CVR anchors) and note the limitation.

**Brand:** include in the title only if the operator opted in.

### Step 4 — Writing rules (SEO + AI/Alexa)
Follow `references/copy-rules.md` and `references/cosmo-intent.md`:
- **Readability is non-negotiable and overrides keyword coverage.** Every Title and Item Highlights
  must read as natural, grammatical English — **read it aloud; if any part doesn't parse, rewrite.**
  Item Highlights are either clean comma-separated self-contained noun phrases OR short complete
  sentences — never comma-spliced fragments like "moist heat warms tired, dry eyes…". Drop a keyword
  before shipping a broken phrase.
- Lead with **product noun + top attribute**, in the words a shopper would **say aloud** (Alexa);
  favor full **spoken-query phrases** from SQP.
- **No unnecessary repetition between Title and Item Highlights.** The highlights must add *new*
  coverage — don't echo the title's multi-word phrases or its use-cases (only the core product noun
  may repeat). If a phrase is already in the title, spend the highlight space on a different
  attribute, material, or use-case instead.
- Put conversational **use-case / material** phrases in the Item Highlights (ones not already in the
  title).
- Use the **COSMO intent dimensions** as a coverage checklist (use-case, audience, compatibility,
  material, occasion, care…) to widen *intent* coverage, not synonyms.
- **Unique keyword coverage** — no synonym stacking, no same phrase in different forms, no filler
  adjectives unless they signal real buyer intent.

### Step 5 — Self-check while writing (the script is the final gate)
As you write each Title / Item Highlights, **count characters exactly including spaces** and keep
them within 75 / 125, using `references/copy-rules.md` + `references/restricted-keywords.md` (no
promo language, no ALL-CAPS, allowed characters only, no word >2×, no category-restricted keyword).
As you write each Title / Item Highlights, **count characters exactly including spaces** and keep
them within 75 / 125, using `references/copy-rules.md` + `references/restricted-keywords.md` (no
promo language, no ALL-CAPS, allowed characters only, no word >2×, no category-restricted keyword).
You do **not** hand-author the Pass/Fail — `build_pptx.py` (via `validate.py`) re-computes every
check deterministically (exact length, allowed chars, emoji, promo, caps, repetition, restricted
keywords for the category). A failing option is **not shown** and triggers a console WARNING — fix
the copy in the JSON and re-run.

### Step 6 — Assemble the final JSON and build the branded deck
Write **one `*_final.json` per ASIN** in the shape under "Data contract" below (existing copy,
benchmark, anchor, trending, relevant_queries, and the 3-4 bundles — title, item_highlights,
rationale). Then build the deck. Structure:
- **Cover** — Sophie Society logo (from `assets/` if present, else a text wordmark) + title + brand,
  ASIN count, date.
- **How the options are weighed** — the four signals (SQP volume, above-market SQP CVR, STR orders,
  POE trend) + the anchor-selection / two-anchor-hedge logic.
- **What you get: up to four title directions** — Volume anchor / CVR hedge anchor /
  Trend-differentiation / CTR hedge anchor (the last shown only when a CTR-hedge term exists).
- Then **per ASIN**: **"OPTIMIZED OPTIONS" card slides** — 2 options per slide so each title +
  highlights present clearly (a 4-option ASIN gets two option slides, labeled 1/2 and 2/2; each card
  shows the title, item highlights, char counts, and the "why").
- **"DATA & INSIGHTS"** (per ASIN) — KPI tiles (ASIN vs market CVR, verdict) + the relevant-query table.

To brand the cover, drop a logo at `assets/sophie-society-logo.png` (see `assets/README.txt`). Pass
multiple `--in` files to put several ASINs in one deck:
```
python scripts/build_pptx.py --in outputs/<ASIN1>_final.json [<ASIN2>_final.json ...] \
    --out outputs/Title_Optimization_<Brand>.pptx
```
If the script prints a validation WARNING, fix the copy in the JSON and re-run before delivering.

### Step 7 — Deliver
The `.pptx` is written to the Cowork **outputs** folder — hand the user the **download** (it opens in
PowerPoint or Google Slides). It is a binary file, so **never push it through the Drive connector as
base64** (that is what corrupted earlier uploads); if the user wants it in Drive, they drag the
downloaded file in (Drive converts it to Google Slides cleanly). No Drive connector call is needed.

---

## Data contracts

### `analyze.py` input — `outputs/<ASIN>_raw.json` (you assemble from the MCP pulls)
```json
{
  "asin": "B0XXXXXXX", "brand": "BrandName", "category": "Home & Kitchen",
  "window_days": 90, "include_brand_in_title": false,
  "options": { "hedge_relative_gap": 0.25, "outperform_margin_pts": 2.0 },
  "str_rows": [
    {"search_term": "...", "campaign": "...", "impressions": 0, "clicks": 0, "spend": 0.0, "orders": 0}
  ],
  "sqp_rows": [
    {"search_query": "...", "search_query_volume": 0, "prev_search_query_volume": 0,
     "market_impressions": 0, "market_clicks": 0, "market_purchases": 0,
     "asin_impressions": 0, "asin_clicks": 0, "asin_purchases": 0, "is_branded": false}
  ],
  "poe_rows": [ {"term": "...", "trend_180d": 0.0, "search_volume": 0} ]
}
```
Only include SQP queries you judge **on-product** (drop competitor-brand / irrelevant); mark branded
ones `is_branded: true`. `analyze.py` does the rest of the math.

### `build_pptx.py` input — `outputs/<ASIN>_final.json`
Assemble this by taking `analysis.json` (which already contains `benchmark`, `anchor`, `trending`,
`relevant_queries`) and adding `existing`, `run_date`, and the 3 `bundles` you wrote:

```json
{
  "brand": "BrandName", "asin": "B0XXXXXXX", "category": "Home & Kitchen",
  "window_days": 90, "run_date": "2026-06-12",
  "existing": { "title": "...", "bullets": ["...", "..."] },
  "benchmark": { "weighted_asin_cvr": 0.14, "weighted_market_cvr": 0.09,
                 "delta_points": 5.0, "verdict": "preserve",
                 "verdict_note": "ASIN beats market; keep content, change for format.",
                 "relevant_query_count": 3, "str_overall_cvr": 0.12 },
  "anchor": { "two_anchor_hedge": false,
              "visibility_anchor": {"search_query": "...", "search_query_volume": 12000,
                                    "asin_cvr": 0.14, "market_cvr": 0.09},
              "high_cvr_anchor": {"search_query": "...", "asin_cvr": 0.28} },
  "trending": { "source": "SQP_period_over_period",
                "terms": [{"term": "...", "growth": 0.6, "volume": 8000}] },
  "relevant_queries": [ {"search_query": "...", "search_query_volume": 12000,
                         "asin_cvr": 0.14, "market_cvr": 0.09, "is_branded": false} ],
  "bundles": [
    {"strategy": "Volume anchor",          "title": "...", "item_highlights": "...", "rationale": "..."},
    {"strategy": "CVR hedge anchor",       "title": "...", "item_highlights": "...", "rationale": "..."},
    {"strategy": "Trend / differentiation","title": "...", "item_highlights": "...", "rationale": "..."}
  ]
}
```
Add a 4th bundle with `"strategy": "CTR hedge anchor"` when `anchor.ctr_hedge_anchor` is present.
Char counts and Pass/Fail are computed by the script — do not pre-fill them. For multiple ASINs,
pass multiple `--in` files to `build_pptx.py`; each ASIN gets its own option slide(s) + data slide
in one deck.

---

## Reference files

- **`references/restricted-keywords.md`** — complete Amazon restricted-keyword table by listing area
  and category. For titles, use the **Listing Copy** column + the ASIN's category (plus "General").
  Bundled and complete; no editing needed to run.
- **`references/copy-rules.md`** — the hard rules (char limits, allowed characters, banned promotional
  words, caps, repetition) and writing guidelines (unique coverage, no synonym stacking, intent-first).
- **`references/cosmo-intent.md`** — buyer-intent dimensions for SEO + AI/Alexa coverage.

## Branding (PowerPoint deck)

The deck is fully Sophie-branded, applied by `build_pptx.py`: a **navy** header band + **teal**
accent strip on every slide, **gold** table headers, alternating light/white rows, **rounded KPI
tiles**, and a color-coded verdict (green = preserve, gold = balanced, orange = flexible). Because it
is a real PowerPoint file (not a CSV→Sheet), colors render exactly — and because it ships as a
**download** (never base64-through-Drive), it cannot corrupt.

Palette: Dark Navy `#1A2B3B`, Orange `#E8643A`, Teal `#4ECDC4`, Gold `#F5A623`, Green `#4CAF50`.
To add a logo or restyle, edit the palette constants / `_header` in `build_pptx.py`.

## Tone for client-facing rationale text
Direct, specific, data-anchored. Name the term and the number
(e.g. "Anchored on 'glass food containers' — 1,240 query vol, ASIN CVR 14% vs market 9%").
