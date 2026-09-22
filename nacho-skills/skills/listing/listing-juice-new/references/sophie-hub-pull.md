# Sophie Hub pull — the real procedure (mode 4)

Everything here was verified against a live Sophie Society store (Hope Love Shine,
`AGA47QMYRYAUM`, Amazon US) on 2 September 2026. Where an earlier version of this
skill assumed something that turned out to be false, the correction is called out
explicitly, because those assumptions were producing silently wrong audits.

Read this only when the Sophie Hub tools are present in the session. If they are
not, skip it entirely and use manual upload.

---

## The single most important fact

**There is no Category Listings Report in the Sophie Hub pipeline.**

`parse_inputs.py` mode 2 needs a Seller Central Listing Loader workbook: an
`.xlsm`/`.xlsx` with `::record_action` in row 4 or 5, plus `contribution_sku`,
`item_name[...]` and `bullet_point[...]#n` attribute headers. Nothing in S3
produces that shape.

The closest report, `GET_MERCHANT_LISTINGS_ALL_DATA`, is a flat 30-column TSV:

```
item-name, item-description, listing-id, seller-sku, price, quantity, open-date,
image-url, item-is-marketplace, product-id-type, ... asin1, asin2, asin3, ...
fulfillment-channel, status
```

No bullets. No `generic_keyword`. No structured attributes. Feeding it to
`parse_flat_file()` returns `No template sheet found`.

So mode 4 does **not** try to fake a workbook. The runner assembles a listing
payload from MCP calls and passes it with `--listing-json`. See the contract at
the bottom of this file.

---

## What mode 4 can and cannot deliver

| | mode 2 (uploaded CLR) | mode 4 (Sophie Hub pull) |
|---|---|---|
| Title, description | ✅ | ✅ |
| Bullets | ✅ | ✅ via Keepa (see the flattening trap below) |
| Structured attributes | ✅ | ✅ richer, and live rather than as-of-export |
| Backend search terms | ✅ | ❌ **not exposed anywhere** |
| SQP funnel | ✅ if uploaded | ✅ better, with cadence + market comparison |
| PPC search terms | ✅ if uploaded | ✅ better, attributed per-ASIN |
| Review insights | ✅ if uploaded | ✅ via Helium 10 MCP |
| Competitor benchmark | ✅ if X-Ray uploaded | ✅ via Helium 10 MCP |
| Upload-ready xlsx | ✅ on request | ❌ no Listing Loader template to patch |
| Seller effort | downloads 1–5 files | none |

Two hard gaps, and both must be surfaced in the pre-run data check:

1. **Backend search terms.** Not in Catalog Items, not in the merchant-listings
   TSV, not in Keepa. You cannot audit what is there, and any backend you propose
   has no baseline to dedupe against. Tell the seller to check Seller Central
   before overwriting. This is not a bug to route around; it is a real limit, and
   it matters — a CLR-based run on this same ASIN found the live backend was 282
   bytes against a 250-byte cap, with two misspellings. Invisible via MCP.
2. **No upload-ready flat file.** `write_flat_file.py` hard-exits in mode 4.

---

## Trap: `get_product_catalog` flattens the bullets

The tool description says it is "marketplace-flattened: per-marketplace attribute
arrays are collapsed to a single value." That applies to `bullet_point` too.

On B08W2H1PNM the catalog payload returned **one** bullet. Keepa returned **six**.
An audit built on the catalog payload alone would have scored one sixth of the copy
and reported it as the whole listing — and on that ASIN the missed bullets included
a medical claim that is a suppression risk.

**Always take bullets from Keepa**, never from `get_product_catalog`.
`parse_inputs.py` warns when it receives one bullet or fewer, but do not rely on the
warning to save you.

---

## The pull, step by step

### 1. Resolve the store

```
Sophie Hub:list_stores(compact=true)
```

Match on the brand name. Say "store" to the seller, never "seller ID". If several
match, ask. If zero come back, fall back to manual per the §6 ladder.

> `verify_session` is documented in older references but did not appear in the
> Sophie Hub tool set when this was written. Do not gate the flow on it. Call
> `list_stores` first; if it errors on auth, that is your case (b) signal.

### 2. Pick the ASIN

If the seller named one, use it. If not, rank by revenue rather than asking:

```
Sophie Hub:list_top_products(store=<id>, days=30, limit=5,
                             compact=true, marketplace_id=<mp>)
```

Confirm the choice with the seller before auditing. Never guess a variation:
`get_product_catalog` → `relationships` gives the parent and variation theme.

### 3. Listing content

```
Sophie Hub:get_product_catalog(
    seller_id=<store>, asin=<ASIN>, marketplace_id=<mp>,
    fields=["attributes","summaries","salesRanks","relationships"])
```

Gives title, description, every structured attribute, browse node, BSR, parentage.
Take **everything except the bullets** from here.

```
keepa:keepa_get_product(asins=[<ASIN>], domain="com")
```

`features[]` is the real bullet array. Also gives image count, rating, review count,
current price and the variation family. Use `images` length for `image_count`.

**Staleness check.** Run `discover_amazon_reports(api_type="SP", seller_id=<store>)`
and read the `latest` date on `GET_MERCHANT_LISTINGS_ALL_DATA`. If the catalog
snapshot is more than ~30 days old, say so in the report. On a healthy store this
refreshes daily.

### 4. SQP — use the purpose-built tools, not a raw report fetch

```
Sophie Hub:list_sqp_windows(store=<id>)
```

Stores usually carry **both** weekly and monthly windows. They are different reports
with different spans, and `get_sqp_metrics` returns `needs_selection` if you omit
`cadence` when several exist. Pick MONTH and a full quarter for a listing audit.

```
Sophie Hub:get_sqp_metrics(store=<id>, asin=<ASIN>, cadence="MONTH",
                           start_date=..., end_date=..., limit=25)
```

**Compute the click-rate comparison. This is the highest-value analysis in the
whole audit and it is easy to skip.** Each row carries the market's totals and the
ASIN's slice:

- your CTR = `asin_click_count / asin_impression_count`
- market CTR = `click_through_rate` (already the market's)
- your CVR = `asin_purchase_count / asin_click_count`
- market CVR = `conversion_rate`

Aggregate across the top queries and report both ratios. Impression *share* alone
reads as "chase different keywords"; the CTR ratio tells you whether the real
problem is the main image and the first 40 characters of the title. On
B08W2H1PNM this came out at 0.46x market CTR against 1.57x market CVR — shown
plenty, converts well, loses everything at the click. Share figures alone would
have pointed at the wrong fix.

### 5. PPC search terms

```
Sophie Hub:query_ppc(store=<id>, view="search_terms",
                     asins=[<ASIN>], days=60, limit=30)
```

Rows from multi-ASIN ad groups come back `shared: true` with `co_asins`. Those are
full ad-group metrics, not the ASIN's split — say so before quoting a shared row's
ROAS as the ASIN's own.

### 6. Reviews — available via MCP, contrary to older guidance

Earlier versions of this skill state that Helium 10 is upload-only because Sophie
Hub does not carry third-party data. That is true of Sophie Hub and false of the
session: the **Helium 10 MCP** is normally connected alongside it.

```
Helium10:get_asin_review_analysis(asin=<ASIN>, marketplace="US")
```

Returns positive and negative topics with mention counts, occurrence percentages,
star-rating impact, per-topic review snippets and ~6 months of trend. This is the
Review Insights export.

Two cautions. The window is roughly six months, so a low-velocity ASIN may yield
only a few dozen mentions — check the counts before calling a theme dominant. And
paraphrase the snippets; never lift them into listing copy.

### 7. Competitors

Also reachable, and the biggest remaining quality gap when skipped:

```
Helium10:get_listing_details(main_asin=<ASIN>, marketplace="US")
Helium10:search_competitors_by_asin(...)
Helium10:compare_listings(...)
```

You want the comp-set medians the diagnostics use: title length, image count, price
(and the audited ASIN's percentile within the set), review count, rating. Price
percentile is what licenses the "premium price has to be earned" argument, and
competitor title vocabulary tells you which terms are saturated — sometimes the
opposite of what SQP conversion alone suggests.

### 8. Write the payload and hand off

Write the JSON below, then run the normal pipeline:

```bash
python3 scripts/parse_inputs.py \
    --uploads /mnt/user-data/uploads \
    --listing-json /tmp/listing.json \
    --asin B0XXXXXXXX \
    --out /tmp/parsed.json
```

`--uploads` is still required and still scanned: anything the seller *did* upload
(an X-Ray CSV, a review export, an SQP file) is parsed alongside the pull. Hybrid is
the normal case, not an edge case. An uploaded Category Listings Report wins over
the listing JSON, and the parser says so in a warning, because the CLR carries
backend terms and supports the xlsx.

From here everything is identical to mode 2: `run_diagnostics.py` →
`summarize_diagnostics.py` → Step 4 semantic work → `build_html_report.py`.

---

## Listing JSON contract

```json
{
  "source": "sophie-hub+keepa",
  "store": "AGA47QMYRYAUM",
  "marketplace": "US",
  "pulled_at": "2026-09-02",
  "listing_report_date": "2026-09-02",
  "asins": [
    {
      "asin": "B08W2H1PNM",
      "sku": "",
      "title": "...",
      "brand": "HOPE LOVE SHINE",
      "product_type": "pendant-necklaces",
      "description": "...",
      "bullets": ["...", "...", "...", "...", "..."],
      "backend": null,
      "parentage_level": "child",
      "image_count": 5,
      "structured": { "occasion_type": "new beginnings", "metal_type": "Sterling Silver" },
      "empty_structured_fields": ["target_audience_keyword", "seasons"]
    }
  ]
}
```

- `asin` and `title` are the only required fields per entry.
- `bullets` from Keepa `features[]`. One or fewer triggers a warning.
- `backend` is normally `null` and triggers a warning. Never invent a value.
- `structured` is the flattened `attributes` block from `get_product_catalog`.
- `empty_structured_fields` drives the "fields Amazon reads that you left blank"
  section. Populate it from the category family's expected attribute list.

## Report a populated field that holds a wrong value

`empty_structured_fields` only catches blanks. A field filled with a value that does
not describe the product is worse than a blank, because it feeds Amazon's filters.
On B08W2H1PNM the live catalog carried `style: "Pride"`, `theme: "Rainbow,Love,Space"`,
`initial_character: "C"` and an ASIN-shaped string in `model_number`. Screen the
populated attributes against the product during Step 4 and report wrong values
alongside the empty ones.

---

## File contract — get these exactly right

Everything below was found by running mode 4 end to end and watching it fail. §0.4 used
to say "save under filenames the detector recognizes" without naming them. Both failures
were **silent**: the file was simply ignored or a bucket quietly returned empty.

### Filenames the detector matches

`walk_uploads()` matches on filename. Miss the pattern and the file lands in
`unrecognized_files` with no error.

| Input | Pattern that must match | Working example |
|---|---|---|
| Category Listings Report | `category[_ ]listings[_ ]report.*\.(xlsm\|xlsx)` | `Category_Listings_Report_1234.xlsm` |
| SQP | `^[a-z]{2}[_ ]search[_ ]query[_ ]performance.*\.csv` | `US_Search_Query_Performance_B08W2H1PNM.csv` |
| Review Insights | `helium[_ ]10[_ ]review[_ ]analysis[_ ]-[_ ]<ASIN>` | `Helium_10_Review_Analysis_-_B08W2H1PNM.xlsx` |
| X-Ray (ASINs) | `helium[_ ]10[_ ]xray.*\.csv` | `Helium_10_Xray_necklace.csv` |
| PPC search terms | **`search term` with a SPACE**, ending `.csv` | `Sponsored Products Search term report.csv` |

⚠️ **The PPC one is the trap.** Underscores do not match — `sponsored_products_search_term_report.csv`
is silently ignored. The pattern is `'search term' in filename.lower()`, matching Amazon's real
Campaign Manager export name, which has spaces.

### SQP CSV columns

Row 0 is a metadata line, row 1 is the header. The eight count columns are not enough:
`run_diagnostics.py` also needs four share/rate columns, and without them SQP bucketing
fails with `SQP buckets failed: 'Purchases: ASIN Share %'` and you get an audit with no funnel.

```
Search Query, Search Query Volume,
Impressions: Total Count, Impressions: ASIN Count, Impressions: ASIN Share %,
Clicks: Total Count, Clicks: ASIN Count, Clicks: ASIN Share %,
Purchases: Total Count, Purchases: ASIN Count, Purchases: ASIN Share %,
Purchases: Purchase Rate %
```

`get_sqp_metrics` returns shares as 0–1 decimals (`impression_share: 0.0427`). **Emit them as
percentages** (4.27), not decimals. Derive the two rate columns:

- `Purchases: ASIN Share %` = `asin_purchase_count / purchase_count * 100`
- `Purchases: Purchase Rate %` = `asin_purchase_count / asin_click_count * 100`

### PPC CSV columns

Lowercase AdLabs-style headers are accepted. `query_ppc` returns `purchases`; the column map
wants **`orders`** — rename it or the PPC bucketing returns
`missing required columns (term/orders/spend)`.

```
search_term, impressions, clicks, spend, sales, orders, acos
```

### Review Insights XLSX sheets

Four sheets, header in row 1, data from row 2. Sheet names are matched exactly:

| Sheet | Columns, in order |
|---|---|
| `Positive Topic Insights` | Topic, Subtopic, ASIN Mentions, ASIN %, Category %, Review Snippets |
| `Negative Topic Insights` | same |
| `Positive Star Rating Impact` | Topic, ASIN Star Impact, Category Star Impact |
| `Negative Star Rating Impact` | same |

Map from `get_asin_review_analysis`: `topics_mentions.topics.positiveTopics[]` gives topic,
subtopics, `asinMetrics.numberOfMentions`, `asinMetrics.occurrencePercentage`,
`browseNodeMetrics.occurrencePercentage.allProducts`, and `reviewSnippets` (join with ` | `).
Star impact comes from `topics_star_rating_impact`.

### Competitors JSON (`--competitors-json`)

New in v4.3. Normalised into X-Ray record shape and fed to the **same** benchmark code an
uploaded X-Ray feeds, so nothing downstream changes. An uploaded X-Ray CSV always wins.

```json
{
  "competitors": [
    {"asin": "B0XXXXXXXX", "brand": "...", "title_chars": 147, "reviews": 51,
     "rating": 4.6, "images": 7, "bsr": 41233, "price": 26.49, "rank": 1}
  ]
}
```

Only `asin` is required; anything missing degrades to null and the benchmark filters it out
before taking medians. `rank` is the SERP position and defaults to array order. Warnings fire
below 5 competitors and when no title lengths are supplied.

Build it from `Helium10:search_competitors_by_asin` plus `get_listing_details` per ASIN. Include
the audited ASIN itself in the set if you can, so `run_competitive()` resolves the own-row and
can report the price percentile.

### The report JSON trap

`build_html_report.py` expects `current_value` / `proposed_value` / `evidence_text` on every
rewrite block. Authoring them as `current` / `proposed` / `rationale` used to render **silently
blank** panels in a report that otherwise looked finished. As of v4.3 the builder validates the
keys and refuses to render. Do not work around it by renaming in the template.
