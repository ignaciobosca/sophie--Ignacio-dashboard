---
name: account-performance-dashboard
description: Build the Sophie Society Account Performance Dashboard (v2) for any Amazon store from live data on the active Sophie Hub MCP. One self-contained 5-tab HTML (Overview, Advertising, Products, Profitability, Subscribe and Save) with exchangeable Overview KPI cards, granularity-correct cards plus a granularity-driven P&L chart and matrix, a Child-ASIN to Parent product view toggle, a multi-select product filter, COGS editor, and a Subscribe and Save active-subscribers chart. Data-as-props with an embedded refresh manifest so it ships as a Cowork live artifact. Profitability uses real Amazon fees (referral, FBA, promotions, refunds via get_financial_summary; storage best-effort) plus COGS; Subscribe and Save uses get_subscribe_save. Use whenever the team asks for an account or brand performance dashboard - 'build a dashboard for [brand]', 'account performance dashboard', 'rebuild the account dashboard with fresh data', or any refresh. ALWAYS start from assets/dashboard-template.html; never hand-build the HTML.
---

# Sophie Society Account Performance Dashboard

The canonical account-performance dashboard for the Sophie Society team. One template, one shape, one set of charts — populated with whichever store's live Sophie Hub data is requested. This is the **enhanced (v2)** build: exchangeable KPI cards, granularity-correct cards + matrix, a parent-level product view, and an Active-Subscribers chart. See **Enhancements in v2** below.

## CRITICAL — read first

1. **ALWAYS start from `assets/dashboard-template.html` — the ONE canonical template — and VERIFY it before building.** Copy it, then inject the **single data blob** at `/*__DATA__*/` (Step 3). Do NOT build the HTML, CSS, chart configs, filter logic, or P&L matrix from scratch — they are 1000+ lines and cannot be reliably reproduced from instructions. **Verify the copy is the right one AND complete:** it must contain `APD-TEMPLATE schema=2` near the top **and end with** the `APD-TEMPLATE-END schema=2` sentinel. If either is missing, the file is **stale or truncated on fetch** — STOP, re-fetch (Install), and **never** fall back to an older/production template or hand-build. *(Observed failure mode: a truncated fetch → silent fallback to the old production template → a fixed "Last 30 days" campaign snapshot that ignores the Period filter and mislabels reconciled multi-month spend. The two markers make that impossible to miss — if you can't get a verified template, say so and stop rather than shipping the wrong one.)*
2. **Preserve every character of the template except the injection point and the pipeline slot.** This is what guarantees every store's dashboard looks the same. The dashboard is **data-as-props** (all data + a `meta`/`manifest` in one seed blob). It ships as a **native Cowork live artifact**: the seed is embedded and painted instantly, and an **in-page refresh pipeline** (`assets/refresh-pipeline.js`, inlined at build) re-pulls only the trailing 30 days from the Sophie Hub MCP on open, merges them over the saved 6-month blob in `localStorage`, and reloads. The heavy backfill runs **once** (the seed); every open after is a light tail refresh — **no agent turn required.** See **Step 3** (build) and **Step 5** (deliver via `create_artifact`).
3. **Output filename:** `{Brand}_Dashboard.html`, saved to the workspace folder.
4. **Data source: the active Sophie Hub MCP.** Use the semantic tools (`get_orders_summary`, `query_sales_traffic`, `get_ads_summary`, `list_top_products`, `query_ppc`, `discover_amazon_reports`, `query_report`). The store's `seller_id` is passed as `store` to every tool. Detect the MCP prefix at runtime (see Install) — never hardcode it. Use the consumer-facing brand (the store `name`) on the dashboard.
5. **Profitability is COGS + real Amazon fees.** Referral (Commission), FBA fulfillment, other fees, promotions and refunds now come from **`get_financial_summary`** (sourced from the SP-API Finances feed). Net = Revenue − Ad Spend − COGS − fees. **COGS is still collected at setup (Step 0) and stays editable in the dashboard's COGS editor** — the tool supplies everything except COGS. **Subscribe and Save** subscriber metrics (active subscribers, shipped units, program revenue, OOS, lift) come from **`get_subscribe_save`** (the Replenishment feed); the settlement $ (sales/units/discount) come from `get_financial_summary`. Storage fees (not in `get_financial_summary`) are attempted separately from `GET_FBA_STORAGE_FEE_CHARGES_DATA` — but this is **best-effort only**: it fails (`"Response was not valid JSON"`) on many stores, in which case storage defaults to 0 and is excluded from net (Step 1F). See **Data coverage & the Profitability tab** below.

## Period cohorts are CALENDAR-anchored (build 2026-08-26b)

`This Month (MTD)`, `Last Month`, `Last 3 Months`, `This Quarter` and `YTD` resolve against the
**viewer's real calendar date**, then intersect with the months actually loaded. They are NOT
"the last month in the file" — that was the old behaviour and it drifted as a snapshot aged
(a 24-Aug build opened in October still read "August 2026 (MTD)").

Consequences you should know when building:
- A cohort with no loaded data renders KPI values as `—` and shows a red banner naming what the
  file does cover. It does NOT silently fall back to the latest month, and it does NOT show `$0`.
- A partly-covered cohort renders the months it has plus an amber "Partial: data ends <month>" note.
- A file more than 32 days past its `meta.dataThrough` shows a "rebuild it for current figures" note.
- `Lifetime` and `Custom Range` are unchanged — both are index-based over the loaded axis.
- `meta.dataThrough` drives the staleness note, so always set it to the last day with real data.

A dashboard viewed on its build date behaves exactly as before — verified value-for-value across
all seven cohorts. Only aged snapshots change, which is the point.

### Rebuilds now beat a stale browser cache

`okShape()` also drops any cached blob whose `meta.generatedAt` predates the seed's. Before this,
the cache won on shape alone, so re-running the skill for a store someone had already opened left
them looking at the previous build's numbers indefinitely in snapshot mode. A cache the refresh
pipeline has legitimately tail-updated always carries a `generatedAt` >= the seed's, so it is still
preserved. **Always set `meta.generatedAt` to the build date** — it is now load-bearing.

## Enhancements in v2 (interactive features built into the template)

Every enhancement below is **already built into `assets/dashboard-template.html`** (its JS/HTML/CSS). The **data pipeline is unchanged** — Steps 0-5 pull and shape the exact same blob. So the rule is the same: **start from this template and inject the one data blob**; do not re-implement these features and do not strip them out. The only new *data* affordance is an optional `PARENTS` blob key (below); everything else needs nothing extra.

1. **Exchangeable Overview KPI cards.** The 5 Overview cards are each a dropdown that can show any of **11 metrics**: Total Sales, Organic Sales, PPC Sales, Ad Spend, ACOS, TACOS, ROAS, Units Ordered, Orders, Profit Margin, Profit ($). Defaults: Total Sales / Units / Ad Spend / Profit / TACOS. The chosen layout persists in `localStorage` (`apd_ovsel`). Changing a card calls `renderOvCards()` **only** — it does not rebuild the charts (no wasted work). For ACOS / TACOS / Ad Spend the comparison chip treats a decrease as good.

2. **Granularity-independent KPI cards (Overview + Advertising).** KPI card totals are computed as **period totals on the monthly (settled/ordered) basis** — they do **not** change when the user flips the global Daily/Weekly/Monthly toggle (same period = same number). Granularity only re-buckets the **charts** below. (Root-cause fix: the cards used to sum the granularity-bucketed series, which is COGS/promo-free and SP-only ad at daily/weekly.)

3. **Profitability follows the global granularity — chart AND matrix.** The global Daily/Weekly/Monthly toggle drives the configurable P&L chart *and* the **P&L Matrix** (columns become months / weeks / days). Because Amazon settles fees, promos, refunds & COGS **monthly**, sub-monthly columns are **prorated estimates** (each month's settled totals distributed across its days by that day's share of account sales) and always reconcile back to the settled monthly totals; a caption says so on weekly/daily. The Matrix's local "By Month/Week/Day" dropdown mirrors the global toggle both ways.

4. **Products: Child-ASIN to Parent view toggle.** A "View" toggle on the Products tab rolls child ASINs up into **variation families** (cards, charts, and the detail table all aggregate; ACOS/TACOS/net/margin recompute at the parent level; the COGS editor stays per-ASIN). Families come from the optional `PARENTS` blob key; if absent they are **auto-derived from the SKU prefix** (letters before the first size/pack token) so the toggle always works. See `PARENTS` in the blob-keys table.

5. **Multi-select product filter + working granularity.** The product filter is multi-select, and Daily/Weekly granularity works under a product subset (each selected product's monthly total is distributed across days on the account's real daily curve).

6. **Subscribe & Save — Active Subscribers area chart.** A dedicated filled area chart of point-in-time active subscribers, below the existing combo chart. It honours the **Period** and **Granularity** filters (monthly = reported values; daily/weekly hold each month's value, since Amazon reports S&S monthly). Subscribers are account-level, so the Product filter does not split it (noted under the chart).

7. **Split ACOS / TACOS.** Advertising trend plots ACOS (ad / ad-sales) and TACOS (ad / total sales) as two lines; the Overview exposes both as selectable card metrics.

**Because all of the above lives in the template**, a Cowork live refresh (which only re-injects the blob) preserves them automatically — as long as you re-inject into a copy of THIS template (or the customized file), never a blank/older template.

## Step 0 — resolve store, timeframe, COGS, scope (interactive setup)

Do all three before pulling data. Ask the user; don't silently default.

**a) Store.** Always call `list_stores` first. **If the user named a brand/store** (even loosely — "the 4GiftSake dashboard", "do YouChews"), **fuzzy-match it against `list_stores` before asking**: normalize (lowercase, strip punctuation/spaces) and substring/contains-match the user's phrase against each `name`. One clear match → use it and just confirm in passing ("Building for **4GiftSake** (store …)"), don't make them pick from a list. Multiple plausible matches → show only those compact `name` + store candidates and ask. No match / no name given → ask which store, listing the options. Each store has a `seller_id` (pass as `store`) and a display `name` (the brand label). Say "store" to the user, never "store ID" / "seller ID". Capture `seller_id`, brand display name (store `name`), and the marketplace label (derive from data — see `MARKETPLACE` below; default `US marketplace`).

**b) Timeframe (ask).** **Default to 6 months ONLY when the user doesn't specify a window.** If the user gives an **explicit** window — a month/week count ("2 months", "last 8 weeks") or a date range — **honor it exactly** (down to a ~1-month floor); do NOT round up to 6. The in-dashboard Period filter narrows *within* what you load, but it must **never override an explicit request**: a user who asks for 2 months must see **2 months on the axis, not 6.** Extend to whatever history they ask for, limited only by how far the store's data goes back. The dashboard renders a monthly axis plus an in-browser Period filter (Lifetime / MTD / Last Month / YTD / Custom) that slices within the loaded range. How the axis is built from the choice:
  - Resolve `end_date = today − 1` (data lags ~1–2 days; never pull "today").
  - Resolve `start_date` = first day of the month `N` months before the end month, where `N = max(6, requested)`. For "all history" / "as far back as possible", set `start_date` well back (e.g. 24–36 months) and let the empty-month drop trim it to real coverage.
  - Pull the wide daily window once, bucket `rows[].date` by `YYYY-MM`, and **drop empty leading months** (a store may have less history than requested — e.g. ask for 12 but only 8 have data → axis is those 8, but never trim below the 6-month floor when 6+ months exist). The surviving buckets, oldest→newest, are `MO`/`MF`/`MMAP`. `DATA_THROUGH` = the last day with nonzero data, not `end_date`.
  - If the user names an explicit range or count ("Jan 2025–Apr 2026", "last 18 months", "**last 2 months**", "this year"), **honor it verbatim** (down to ~1 month) — do NOT round up to 6. Only apply the 6-month default when the user states no window at all. (The "monthly data starts on the 1st" invariant still holds: for "last 2 months" ending 2026-07-06, load 2026-06-01 → 2026-07-06.)

**c) COGS (ask).** COGS drives Net Profit and margin, so collect it now:
  - First get the product list (`list_top_products`, Step 1D) so you know which ASINs/SKUs need a cost.
  - Ask the user for **per-unit COGS per product** — accept a pasted list, a cost file (CSV/sheet with ASIN-or-SKU → unit cost), or a quick per-ASIN dictation. Map each cost to its product and build the `COGS` array in **PROD order**.
  - If the user doesn't have costs handy, tell them the dashboard will open with COGS = $0 (Net = Revenue − Ad Spend) and they can fill them anytime in the **COGS editor on the Products tab** — it recalculates net & margin live across every tab. Set `COGS = [0, 0, …]` (one per product) in that case.
  - Either way the per-unit values you inject become the editor's pre-filled starting values, so setup and later editing use the same path.

**d) Reporting scope — ASINs (only ask if there are more than 30).** After you have the product list (Step 1D):
  - **30 or fewer active products → ALWAYS include all of them.** Don't ask.
  - **More than 30 → ask** whether to report on **all ASINs** or just the **top 30 by revenue**. Be honest about the trade-off: more ASINs = more per-month `by_asin` + `product_ads` calls (≈ `2 × months × ceil(asins/batch)`) and a heavier/slower artifact (and live refresh). Default to top 30 if they're unsure; honour "all" if they ask. Record the choice in `meta.scope` (e.g. `"all 61"` or `"top 30 of 61"`) so the footer states coverage truthfully.

**e) Manual cost inputs no feed returns (ask, like COGS).** A couple of costs Amazon never exposes — collect them now or skip:
  - **Per-unit outbound shipping for seller-fulfilled (FBM) units** — not in `get_financial_summary` (FBA outbound shipping is already inside `fba_fees`, so FBA brands need nothing here). If the brand ships its own units, ask for a per-unit FBM shipping cost and **fold it into the per-unit COGS** (COGS = product cost + FBM ship) so it flows into net; default 0.
  - COGS itself is the other manual input (asked in (c)). Everything else — Amazon fees, promotions, refunds, **storage**, and Subscribe & Save — is pulled from tools/reports (Step 1F–1G); never ask the user for those.

**Window strategy (mechanics).** The Sophie Hub reporting tools are window/day-shaped, not month-shaped. A `days=30` window only spans ~2 partial months. To build the multi-month `MO`/`MF` axis you must EITHER (a) pull one wide daily window with an **explicit `start_date = <earliest-month>-01`** (first of the month) and bucket the daily rows by `YYYY-MM` yourself, OR (b) issue one call per calendar month with `start_date`/`end_date`. Both patterns are used below.

> **INVARIANT — monthly data ALWAYS starts on the 1st.** Every month bucket (the earliest included) must span from `YYYY-MM-01`. Do **NOT** use a rolling `days:N` window as the axis-defining pull: `days:180` starts mid-month, so the earliest bucket holds only part of that month and **undercounts it**. Always round the start back to the 1st (`start_date = YYYY-MM-01`). If a leading month is still genuinely partial because the store's history begins mid-month, **drop it** rather than render a partial-month column. The live refresh already honours this — `pullMonth` pulls each month from `key + "-01"`, so only the seed build has to be careful.

## Step 1 — pull data from Sophie Hub

All calls target the store's `seller_id` passed as `store`. For YouChews that is `A1RELYWMLK4CK5`. The tools below are the **only** ones confirmed working against a live store — do not substitute.

> **Omitting `marketplace_id` does NOT mean "US".** It means *every* marketplace the store sells in. On a single-marketplace store those are the same thing, which is why this used to read "defaults to US" — it was true by accident. On a multi-marketplace store it is the difference between a real number and a wrong one.
>
> **Resolve the store's currencies BEFORE pulling anything** (Step 0). `get_orders_summary` returns `data.by_currency[]`; more than one entry ⇒ multi-currency. **A multi-currency store MUST be built scoped to one marketplace** — stamp `__APD_MARKETPLACE__` and pass `marketplace_id` on every call. This dashboard renders a single `$` and is single-currency by construction; there is no way for it to show two.
>
> Unscoped, `get_ads_summary` returns **`cost: null` / `sales: null`** and moves the real figures into `by_currency` — which carries **no `by_type` (SP/SB/SD) split**, so a month cannot be rebuilt from it. The refresh pipeline throws on a null `cost` and keeps the last saved month rather than writing `0`. Do not "fix" that by coercing null to 0: reporting **$0 ad spend** to a partner who spent $3.5k is worse than any gap.

### Budget & batching (read before you start pulling)

**This is a ~20–25 tool-call job.** Most of those calls are independent and many are per-month loops — batch the independent ones from the start instead of discovering the shape call by call. The fixed cost is roughly: 1 catalog + 1 wide sales-daily + 1 wide ads-daily + 1 wide financials(`full`) + 1 subscribe_save + 1 campaigns-discover + (3 campaign `query_report`) + **per-month loops** for `M.orders`, the `by_type` ad split, per-product sales/ppc, and storage. Plan the per-month loops as batches up front. Tell the user the rough call count when you begin so a multi-minute pull isn't a surprise.

### Tool gotchas — file caps, payload sizes, and the jq detours (read before you start)

Several of these tools hit hard limits or blow the inline token budget and **auto-dump to a file** that you must re-read with `jq`. Knowing this in advance avoids a retry per tool:

- **`list_top_products` / `get_orders_summary` cap at ~30 underlying weekly files.** A 12-month window errors with `"57 files, max is 30"`. So **pull ≤ ~6 months per call, or loop per calendar month** — never "pull the whole window" for these two when the window is long. (Per-month loops are needed anyway for `M.orders`.)
- **`get_financial_summary view="full"`** routinely exceeds the inline token limit (~160K+ chars) and dumps to a file. Pull it **once** for the whole window and parse from the file. Shape: `data.by_month[]`, `data.by_sku_month[]`, `data.by_date[]`, `data.totals`.
  - `jq '.data.by_month[] | {month, gross_sales, units, referral_fees, fba_fees, other_fees, promotions, refunds, sns_sales, sns_units, sns_discount, net_proceeds}' FILE`
  - `jq '.data.by_sku_month[] | {sku, month, gross_sales, units, referral_fees, fba_fees, other_fees}' FILE`
- **`get_ads_summary view="by_date"`** over a long window can exceed the limit (~60KB) and dump. `jq '.data.rows[] | {date, cost, sales, impressions, clicks}' FILE`.
- **`discover_amazon_reports api_type="ADS"`** is large (~175K chars) and dumps. **The report list is nested under `profiles[].report_types[]`, not a flat array** — first jq guesses usually miss. Use: `jq '.profiles[].report_types[] | select(.report_type|test("sp-campaign|sb-campaign|sd-campaign")) | {report_type, s3_key, start, end}' FILE` (adjust the `test()` to the actual `report_type` strings you see). For SP storage discovery (`api_type="SP"`), the shape differs — inspect with `jq 'keys' FILE` first.
- General rule: when a tool returns a "saved to … .txt/.json" pointer instead of inline data, **don't re-call it** — `jq` the file. Inspect unknown shapes with `jq 'paths(scalars) | join(".")' FILE | sort -u | head` before guessing field paths.

### Coverage probe — pick sources adaptively, don't assume Sales & Traffic is complete

**Do this before committing to per-month and per-product pulls.** `query_sales_traffic` (S&T) is the *preferred* rev/units source, but it is **sparse or near-empty on many newer / POD / recently-migrated stores** (e.g. a store with only ~22 days of S&T inside a 6-month window). If you follow the S&T path blindly there, the entire trend and every per-ASIN series come back near-empty. So **probe first, then route:**

1. **Probe:** one wide `query_sales_traffic { view:"by_date", store, days:<window> }` call. Count days with nonzero `ordered_product_sales`.
2. **Decide:** if covered days ≈ the window (S&T healthy) → use the S&T path exactly as written in 1A/1B/1D below. If covered days are **materially fewer than the window** (e.g. < ~60% of expected days, or only a few weeks inside a multi-month window) → S&T is unreliable for this store; **switch to the fallback chain** and note it in `meta` (e.g. `meta.sourceNote: "S&T sparse — monthly rev/units from get_orders_summary, daily from settled Finances, per-product from financials by_sku_month"`).

**Fallback chain (when S&T is sparse):**

| Series | Default (S&T healthy) | Fallback (S&T sparse) |
|---|---|---|
| Monthly `M.rev` / `M.units` | `query_sales_traffic by_date`, bucket by month | **`get_orders_summary` per month** → `by_currency[USD]` revenue/units (full history) |
| `M.orders` | `get_orders_summary` per month | same (already the orders source) |
| Daily `DAILY[].rev/units` | `query_sales_traffic by_date` | **settled Finances `get_financial_summary view="by_date"`** (`by_date[].gross_sales`/`units`) — far more days than sparse S&T |
| Per-product `PROD[].rev/units` | `query_sales_traffic by_asin` per month | **`get_financial_summary view="full"` `by_sku_month[]`** (`gross_sales`/`units`, map sku→asin) — you're already pulling this for fees, so it adds **zero** calls and removes the ~`months` empty `by_asin` calls |

When you take the fallback, the per-product figures become **settled** (not ordered) — label the Overview/Products numbers accordingly in `meta` and skip the per-month `by_asin` loop entirely. The account `M.*` and per-product still reconcile because settled is used consistently. Each improvised swap should be confirmed against the actual payload (one `jq` peek) before you trust it.

### 1A. Brand metadata + the daily series (orders / sales / traffic)

**`list_stores`** (once) → matched `store.name` is the brand label → `BRAND_NAME`.

**`get_orders_summary`** — `{ store, days: <window> }` (or per-month `start_date`/`end_date`).
- Returns `data.by_currency[]` and `data.by_marketplace[]`; **`data.overall` is NULL** — read `data.by_currency[]` filtered to `currency == "USD"`.
- **Exclude** any stray `UNKNOWN`-currency / `Non-Amazon` marketplace row (carries a few $0 orders).
- `by_currency[USD].order_count` is the **only true distinct order count**, but it is window-level only (no per-day, no per-month). `metadata.date_range {start,end}` feeds `DATE_RANGE`.
- Source for the window order total and, called once per month, for `M.orders` (see 1B).

**`query_sales_traffic`** — `{ view: "by_date", store, days: <window> }` — daily series.
- `data.rows[]`, one per day: `date`, `ordered_product_sales` (revenue), `units_ordered`, `total_order_items`, `sessions`, `page_views`, `unit_session_percentage_avg`, `currency`.
- **Cleanest daily rev/units source — WHEN it has coverage.** `DAILY[].rev` ← `ordered_product_sales`, `DAILY[].units` ← `units_ordered`, `DAILY[].date` ← `date`. **If the coverage probe flagged S&T sparse, build `DAILY` from settled Finances instead:** `get_financial_summary view="by_date"` `by_date[]` → `DAILY[].rev` ← `gross_sales`, `DAILY[].units` ← `units` (far more days than sparse S&T; posted-date basis, so the last ~1–2 weeks are partial — same caveat as the daily fees). You already pull `view:"full"` (which returns `by_date`) for fees, so this is no extra call.
- **No daily order count.** `total_order_items` is order line-items, not distinct orders → `DAILY[].orders` has no true source (see gaps). The Daily **tiles** don't need one: they're windows, so they take true counts from `ROLL` (three scoped `get_orders_summary` calls — see the `ROLL` shape below). Never render a summed `DAILY[].orders` as an order count.

**`get_account_performance_summary`** — `{ view: "by_date", store, days: <window> }` — alternative joined daily source.
- `data.rows[]` per day: `date, total_revenue, units_ordered, sessions, page_views, ad_spend, ad_sales, organic_revenue, organic_share, acos, tacos, roas`, plus a `data.summary` rollup.
- Use this for `DAILY` **if** you want rev+units+ad joined in one call. Its per-day `total_revenue`/`units_ordered` match `query_sales_traffic`.
- **Pick ONE source for `DAILY` and stay on it** — `query_sales_traffic by_date` and `account_performance_summary by_date` cover slightly different spans for the same window (e.g. 28 vs 30 rows), so mixing them causes off-by-N.

**`DATA_THROUGH`**: the last day where data has actually landed (last `rows[]` entry with nonzero `ordered_product_sales`/`sessions`) **of whichever daily source you committed to**. The trailing 1–2 calendar days are typically zero (data lag) — do not use the window end blindly.

### 1B. Monthly rollups — `M.*` (sales side)

- **Combined monthly totals** (`M.rev`, `M.units`): take the `query_sales_traffic view=by_date` daily rows from one wide window, group `rows[].date` by `YYYY-MM`, `SUM(ordered_product_sales)` → `M.rev`, `SUM(units_ordered)` → `M.units`, ordered oldest→newest to match `MO`. **If the coverage probe flagged S&T as sparse, do NOT trust these buckets** — instead loop `get_orders_summary` per month and read `by_currency[USD]` revenue/units for `M.rev`/`M.units` (full history), exactly the same per-month loop you already run for `M.orders` (so it folds in at no extra call shape).
- **Monthly order count** (`M.orders`): there is no monthly-orders call. Loop one **`get_orders_summary`** call per month bucket with `start_date`/`end_date` = month bounds and read `by_currency[USD].order_count`.

### 1C. Advertising rollup — `M.ad / adSales / impr / clicks / sp / sb / sd / spSales / sbSales / sdSales`

**`get_ads_summary`** owns every advertising-rollup field. Spend is field **`cost`** (NOT `spend`).

Channel split — **`{ view: "overall", store, days: <window> }`** (or per-month `start_date`/`end_date`):
- `data.overall.{impressions, clicks, cost, sales, orders, units, acos, roas, cpc, ctr, cvr}` — window totals.
- `data.by_type.{sp,sb,sd}.cost` → `M.sp / M.sb / M.sd`.
- `data.by_type.{sp,sb,sd}.sales` → `M.spSales / M.sbSales / M.sdSales`.
- **`by_type` exists ONLY in `view=overall`** (never in `by_date`). For a per-month channel split, call `view=overall` **once per calendar month** and read `by_type` each time.

Daily / combined-monthly — **`{ view: "by_date", store, days: <window> }`**:
- `data.rows[]` per day: `date, impressions, clicks, cost, sales, orders, units, acos, roas, cpc, ctr, cvr` (combined SP+SB+SD).
- Combined monthly arrays: group `rows[].date` by `YYYY-MM` and SUM → `M.ad` ← `cost`, `M.adSales` ← `sales`, `M.impr` ← `impressions`, `M.clicks` ← `clicks`.
- **Daily ad spend IS available**: `DAILY[].ad` (index 5) ← build a `{date: cost}` map from `by_date rows[]` and write each day's `cost`; days with no ad activity → 0.

> Plan **N+1 calls** for an N-month dashboard if you need the per-channel monthly split: one wide `by_date` call for combined totals + one `overall` call per month for SP/SB/SD. Ad sales are attribution figures and will NOT reconcile exactly to product sales (`M.rev`) — label them PPC-attributed.

### 1D. Per-product — `PROD[]`

**`list_top_products`** — `{ store, days: <window>, limit: <high>, compact: false }` (once) — the ASIN universe + metadata.
- `data.products[]`: `asin, sku, title, units_sold, orders, revenue, avg_price, currency`.
- `PROD[].asin` ← `asin`, `PROD[].name` ← `title` (full), `PROD[].sku` ← `sku`.
- **This is the ONLY reliable title/sku source** — `get_product_catalog_bulk` returns "Not found" for some stores, and the by_asin views return `sku=null`.
- Drop any ASIN whose id starts with `_` (placeholder guard).
- **Apply the Step-0 scope:** ≤30 active products → keep ALL. >30 → keep all or the top-30-by-revenue per the user's Step-0 choice. Trimming PROD only changes which products get cards/rows; the account `M.*` totals still come from the account-level sales/ads/finance pulls (1A–1C, 1F), so the P&L stays whole regardless.

Per-month per-product series — **loop one call per calendar month, passing the FULL `asins` array in that single call** (no tool returns month-bucketed per-ASIN series in one shot). Both tools accept a plural `asins` list and return one row per ASIN, so an N-month dashboard needs ~`2 × N` calls total (one sales-traffic + one PPC per month) — **do NOT loop per ASIN per month** (that is `2 × N × #ASINs` calls and will stall the run):
- **`query_sales_traffic`** `{ view: "by_asin", store, asins: [all PROD asins], start_date, end_date }` → per returned ASIN row: `PROD[].rev[m]` ← `ordered_product_sales`, `PROD[].units[m]` ← `units_ordered`. ASIN missing from a month's response → 0. **CONDITIONAL on the coverage probe:** only run this `by_asin` loop when S&T tested healthy (Step 1 "Coverage probe"). **When S&T is sparse, SKIP this loop entirely** and take `PROD[].rev/units` from `get_financial_summary view="full"` `by_sku_month[]` (`gross_sales`/`units`, settled, map sku→asin) — which you already pull for fees, so the per-product numbers cost zero extra calls. This is the single biggest call-saver on sparse stores (removes ~N empty `by_asin` calls).
- **`query_ppc`** `{ view: "product_ads", store, asins: [all PROD asins], start_date, end_date }` → per ASIN row: `PROD[].ad[m]` ← `spend` (SP+SB+SD), `PROD[].acos[m]` ← `acos` (fraction, e.g. `0.7772`). ASIN missing → 0. Retry the single month on a transient 502. Note: some months have **no PPC report at all** (e.g. a month where ingestion hasn't landed) — `files_loaded: 0` means ad/acos are unknown for that month; record 0 but treat it as "not reported", not confirmed zero spend.
- Drive `ad[]`/`acos[]` from `query_ppc product_ads` (consistent monthly loop) rather than `get_product_performance_summary` to avoid an ACoS attribution mismatch.
- The template renders ACOS per product as `p.ad / (p.ad / p.acos * 100)`; supply `PROD[].acos[m]` as a **percent** (multiply the fraction by 100) so the math resolves. (Confirm against a hand-check on one ASIN.)
- `PROD[].fees[]` — real per-SKU Amazon fees from `get_financial_summary view="full"` (`|referral|+|fba|+|other|` per sku-month, mapped sku→asin; length == `MO`; absent → 0). See 1F + Step 2.
- `PROD[].short` and `PROD[].emoji` have **no MCP source** — synthesize `short` from the title/sku pack size (e.g. "Coffee Chews 30ct") and assign `emoji` by category heuristic.

### 1E. Campaigns — `CAMP[]` (per-campaign MONTHLY series)

**Shape:** `CAMP = [ { name, type, status, spend:[…], sales:[…], orders:[…], impr:[…], clicks:[…] } ]` — each array month-aligned to `MO`. `renderCampaigns()` **sums each campaign over the active Period**, so the table is period-aware. A flat one-day snapshot is wrong here — it showed the same tiny $1–4 rows for every period.

**`discover_amazon_reports`** — `{ api_type: "ADS", seller_id, report_type_filter: "report-v3-<sp|sb|sd>-campaign" }` (re-run each refresh; s3 keys rotate).

> **CRITICAL — pick RANGE files, not single-day snapshots (silent zero-conversion trap).** `discover` returns **two file classes** for `report-v3-sp-campaign`/`sb-campaign`: **single-day snapshot files** (`date_from == date_to`) where the conversion columns come back **0** (spend-only), and **rolling range files** (`date_from != date_to`) where real `cost` + `sales30d`/`sales7d` + `purchases30d`/`purchases7d` live. If you filter to the newest file blindly you'll often grab a single-day snapshot → spend with **zero sales/ACOS/ROAS**, and it looks like the feed has no conversions when it does. **Always require a span:** pick the freshest `date_ranges[]` entry with `13 ≤ (date_to − date_from) ≤ 30` (a real range file). Verify: `sales30d > 0` on the top campaigns (this store's top SP campaign: cost $3.9k → sales30d $12k). Use `sales30d` if populated, else `sales7d`. **Per-campaign detail begins later than account-level ads** (range reports start after the account ads history), so early months may have no campaign file — that's expected; reconcile spend to the account `M.sp/sb/sd` for those months and leave conversions 0. For month-exact bucketing (vs. the reconcile-by-share method below), tile **non-overlapping** range windows across the axis and clip each with `where.date_filter` to the month.

Pick the freshest ~14–30-day **range** `date_ranges[].s3_key` per type.

**`query_report`** — per type, `{ s3_key, group_by: ["campaignName"], metrics: SUM(cost) + SP: SUM(sales30d)+SUM(purchases30d) (SB: SUM(sales)+SUM(purchases)) + SUM(impressions)+SUM(clicks), limit: 200 }`. Reports are daily rows → aggregate server-side by `campaignName`. This yields each campaign's **report-window totals** (`cost`, `sales`, `orders`, `impr`, `clicks`).

**Build the monthly series — cheap-but-accurate (do NOT pull ~180 daily files).** For each calendar month `m` and each type `t ∈ {sp,sb,sd}`:
- **Spend (reconciled, exact):** distribute the account's real per-type monthly spend `M.<t>[m]` (already pulled from `get_ads_summary view=overall`) across that type's campaigns by within-type **cost-share**: `spend[m] = M.<t>[m] × (campaign.cost / Σ type cost)`. Campaign spend now **reconciles to account totals per month** and stays period-correct.
- **Conversions (honest, spend-weighted):** `x[m] = campaign.x × (spend[m] / campaign.cost)` for `sales/orders/impr/clicks` — each campaign's real reported conversions distributed by its reconciled monthly spend (observed efficiency).
- `CAMP[].type` ← which report (`sp`/`sb`/`sd`) — authoritative, do NOT parse the name. `CAMP[].status` ← no source → `'ENABLED'`.

**Honest zeros → "—".** SP carries real `sales30d`/`purchases30d`; **SB** = orders only (`sales=0`); **SD** = neither; and on many stores SP conversions are 0 at campaign grain. Leave those **0** — do NOT fabricate. The template renders Ad Sales / ACOS / ROAS / Orders as **"—"** (no data), not `$0 / 0.0% / 0.00x`, and recomputes ACOS/ROAS from the period sums. Keep the top **40 by lifetime spend**; the heading is the dynamic `periodLabel()`, not "Last 30 days".

### 1F. Fees / promo / refunds / Subscribe and Save — `M.varFees/fbaFul/promo/refunds`, `PROD[].fees[]`, SnS

**`get_financial_summary`** owns every fee/promotion/refund/SnS field. It reads the SP-API Finances feed and returns real numbers, fully aggregated — no raw-report parsing needed.

- **Monthly fee arrays** — call once per calendar month (or one wide window and bucket the returned `by_month`): `{ store, start_date, end_date, view: "summary" }`.
  - `data.totals` / `data.by_month[]` each carry: `gross_sales, units, referral_fees, fba_fees, other_fees, promotions, tax_withheld, refunds, sns_sales, sns_units, sns_discount, net_proceeds`.
  - **CRITICAL sign flip:** the tool returns fees/promotions/refunds as **negative**, but the template's net math *subtracts* these arrays — so store **positive magnitudes** (take the absolute value). Map: `M.varFees[m]` ← `|referral_fees|`, `M.fbaFul[m]` ← `|fba_fees|`, `M.operating[m]` ← `|other_fees|`, `M.promo[m]` ← `|promotions|`, `M.refunds[m]` ← `|refunds|`. (The template's net = `rev − ad − (varFees+operating+fbaFul+storage) − promo − refunds − cogs`.)
  - **Settled revenue/units (the Profitability P&L basis)** — from the same `by_month[]`: `M.grossSales[m]` ← `gross_sales` (already **positive**; settled shipped Principal), `M.gunits[m]` ← `units`. The **Profitability tab uses these instead of ordered `M.rev`/`M.units`** so its P&L reconciles to Amazon payouts (Sellerboard basis); **Overview/Products keep ordered `M.rev`/`M.units`** (demand). The template auto-falls back to ordered for the **current partial month and the daily view** (settlement posts ~2 weeks later, so order data is more complete there). Per-product settled figures come from `view:"full"` `by_sku_month[]` → `PROD[].grev[m]` ← `gross_sales`, `PROD[].sunits[m]` ← `units` (map sku→asin like `fees[]`); per-product settled **fees** already = `PROD[].fees[]`.
  - `M.storage[m]` (FBA monthly storage) and `M.lowInv[m]` (low-inventory fee) are **NOT** in the Finances feed. **Pull storage separately** (next bullet — it exists in S3, so wire it). `lowInv` stays 0 (no dedicated report; low-inventory fees land in `other_fees`, already in `M.operating`).
- **Storage fees → `M.storage[m]` (BEST-EFFORT — default 0, do not block on it):** **Known to fail on many stores** — `get_amazon_report_full { s3_key }` on `GET_FBA_STORAGE_FEE_CHARGES_DATA` returns `"Response was not valid JSON"` (the storage file isn't always JSON-parseable through this tool). **Treat storage as best-effort, not required:** attempt it, but if it errors for a month, **set `M.storage[m] = 0` and move on** — never let it stall the run or fail the build. The attempt: `discover_amazon_reports { api_type:"SP", seller_id, report_type_filter:"GET_FBA_STORAGE_FEE_CHARGES_DATA" }` → for each month's `s3_key`, `get_amazon_report_full { s3_key }` → if it parses, SUM the per-row monthly storage charge (confirm the column on first success, likely `estimated_monthly_storage_fee`) → `M.storage[m]` (positive); if it throws or returns non-JSON, leave 0. `M.storage` is in the template's fee sum (`varFees+operating+fbaFul+storage+lowInv`), so any real value flows into net automatically; 0 just means storage isn't reflected. When storage came back empty for the whole window, say so in `meta` (e.g. `meta.storageNote: "FBA storage unavailable for this store — excluded from net"`) so the P&L isn't read as if storage = $0.
- **Per-product fees** — call `{ store, start_date, end_date, view: "full" }` once for the whole window; read `data.by_sku_month[]` (`sku, month, referral_fees, fba_fees, other_fees, promotions`). Per `(sku, month)` sum `|referral_fees|+|fba_fees|+|other_fees|` (positive magnitude), map `sku → asin` via the `PROD` SKUs from `list_top_products`, and write `PROD[].fees[m]` (one value per month, in `MO` order; absent → 0).
- **Subscribe and Save settlement $** — from the same `by_month[]`: `sns_sales`, `sns_units`, `|sns_discount|` per month are the **settled** SnS dollar figures. `|sns_discount|` feeds `SNS.discount[]` (already folded into `M.promo`, so don't double-count it into net). The SnS tab's headline revenue uses the **program** figure from `get_subscribe_save` (see 1G), not `sns_sales` — they differ (program > settlement).
- **Daily fees** — call `{ store, start_date, end_date, view: "by_date" }` for the dashboard's daily window; read `data.by_date[]` (same fields as `by_month[]`, keyed by `date` = `YYYY-MM-DD`). Build a `{date: row}` map and write `DAILY[].fees[d]` ← `|referral_fees|+|fba_fees|+|other_fees|` and `DAILY[].refunds[d]` ← `|refunds|` (positive magnitudes; the template's daily net subtracts them). A day absent from `by_date` → 0. **Caveat: by posted (settlement) date, not order date** — the most recent ~1–2 weeks are partial and will restate as settlements close, so daily fees won't tie exactly to that day's sales; the daily/weekly P&L is directional. (If you already pull `view:"full"` once for the whole window, that response also carries `by_date` — no extra call needed.)
- Always hand-check one month: `M.varFees`/`M.fbaFul`/`M.promo` should be **positive**, and `net ≈ rev − ad − varFees − fbaFul − operating − promo − cogs`.

### 1G. Subscribe and Save subscriber metrics — `SNS`

**`get_subscribe_save`** owns the SnS *subscriber* side (active subscriber count, shipped subscription units, **program** subscription revenue, OOS units, and the trailing-12-month subscriber-vs-nonsubscriber lift). It reads the SP-API Replenishment feed and is distinct from `get_financial_summary`'s settlement $ (the two won't tie exactly).

- One wide call covers the whole window: `{ store, start_date, end_date }` (or `days` ≤ 365). US is the default marketplace; pass `marketplace_id` for a non-US store and confirm scope first.
- Read `data.by_month[]` (`month`, `active_subscriptions`, `shipped_subscription_units`, `subscription_revenue`, `not_delivered_oos_units`) and `data.lift` (`subscriber_avg_revenue`, `non_subscriber_avg_revenue`, `lift_ratio`, `window`).
- Map `by_month[]` into the **month-aligned `SNS` arrays** (length == `MO`, by `MMAP[month]`): `SNS.active[]` ← `active_subscriptions` (point-in-time; absent → leave `null`, **never** 0 — null renders as "—", 0 would imply zero subs), `SNS.units[]` ← `shipped_subscription_units`, `SNS.rev[]` ← `subscription_revenue` (the **program** figure — this is the SnS Revenue KPI), `SNS.oos[]` ← `not_delivered_oos_units`. `SNS.discount[]` ← `|sns_discount|` from `get_financial_summary` (settlement coupon cost, for the table).
- `SNS.lift` ← `{ ratio: lift_ratio, subAvg: subscriber_avg_revenue, nonSubAvg: non_subscriber_avg_revenue, window }`. The template shows it as `+(ratio−1)×100%`.
- Set `SNS.available = true` when the feed returned months; if the tool errors or returns no months (e.g. a store with no SnS program, or `get_subscribe_save` not yet deployed), set `SNS = null` (or `{available:false}`) and the tab falls back to its empty state automatically.
- **Interim (tool not deployed yet):** if `get_subscribe_save` isn't available in the session, you may still populate `SNS.rev`/`SNS.units`/`SNS.discount` from `get_financial_summary` (`sns_sales`/`sns_units`/`sns_discount`) and leave `SNS.active`/`SNS.lift` null — the subscriber KPIs show "—" but revenue/units/OOS render. Prefer the real tool when present.

## Step 2 — assemble the data blob (data-as-props)

The dashboard is **data-as-props**: everything ships in ONE JSON blob injected at the single `/*__DATA__*/` point, so a Cowork live artifact can refresh it. Build this object (index 0 = oldest month, N-1 = newest):

```jsonc
{
  "meta": { /* drives the header, date pill, SnS subtitle/badge, brand filter, footer, live badge */ },
  "MO": [], "MF": [], "MMAP": {},     // month axis
  "M": { /* 21 keys, each array length == MO */ },
  "PROD": [], "DAILY": [], "CAMP": [], "COGS": [], "PARENTS": [],   // optional: variation families for the Products Parent view (auto-derived from SKU if omitted)
  "SNS": { /* Subscribe & Save; arrays length == MO. null/omitted → tab empty state */ },
  "OVR": { /* optional manual/backfill overrides: { 'YYYY-MM': { sales,units,ad,varFees,fbaFul,operating,storage,promo,refunds } } */ },
  "ADDED": [ /* optional 'YYYY-MM' months to add to the axis that the API never returned (e.g. ads beyond the ad-report lookback) */ ]
}
```

### `meta` (header + refresh contract — NOT {{}} text anymore)

| Field | Source | Derivation |
|---|---|---|
| `brand` | `list_stores` → matched `store.name` | Consumer-facing label, e.g. `YouChews`. Shown in header, SnS, brand filter, document title. |
| `store` | the `seller_id` | Pass-through (used in the manifest). |
| `marketplace` | `get_orders_summary` → `data.by_marketplace[]` + `metadata` | `US marketplace` for a single Amazon.com store; derive for other/multi marketplaces — do NOT assume US. |
| `dateRange` | any tool → `metadata.date_range` | `Mon YYYY - Mon YYYY`. |
| `dateRangeUpper` | derived | `dateRange.toUpperCase()`. |
| `dataThrough` | chosen daily source → last `rows[]` with nonzero rev/sessions | Last day data actually landed — NOT the window end. |
| `generatedAt` | today's date | `YYYY-MM-DD`. |
| `window` | Step 0 choice | `{ start, end, months }`. |
| `sourceNote` | coverage probe (Step 1) | *Optional.* Set when S&T was sparse and you took the fallback chain (e.g. `"S&T sparse — monthly/daily from get_orders_summary + settled Finances; per-product settled (by_sku_month)"`). Surfaced in the footer so the basis is honest. Omit when S&T was healthy. |
| `storageNote` | storage attempt (Step 1F) | *Optional.* Set when `GET_FBA_STORAGE_FEE_CHARGES_DATA` failed/returned non-JSON and storage defaulted to 0 (e.g. `"FBA storage unavailable for this store — excluded from net"`). Omit when storage parsed. |
| `snsDailyEstimatedBefore` | Step 1G / build | *Optional date string* (`YYYY-MM-DD`). Subscribe & Save is reported **monthly** by Amazon; when the user views the S&S tab at Daily/Weekly granularity the dashboard **estimates** a daily series by distributing each month's S&S totals across days in proportion to that day's share of total account sales. This field sets the cutoff the disclaimer names — "daily figures before `<date>` are estimated." Set it to the date true daily S&S reporting begins for the store (the Replenishment daily-cron start, ~`2026-06-09`); **omit/null → the disclaimer reads "all daily figures are estimated"** (correct today, since the MCP tool still returns monthly only). |
| `schema` | build constant | Integer version of the blob **shape** (currently **2** — object-per-campaign `CAMP` monthly series). The loader drops any cached blob whose `meta.schema` ≠ the seed's, so a stale cache can never feed a mismatched shape into the template. **Bump it on any blob-key shape change** (see the HARD RULE in Step 3). |
| `manifest` | the Step 1 calls | The **refresh contract** — see "Refresh manifest" below. |

### Blob data keys

| Key | Source | Derivation |
|---|---|---|
| `MO` | `query_sales_traffic by_date` → `rows[].date` grouped by `YYYY-MM` | Short labels oldest→newest, e.g. `['Dec 25','Jan 26',...]`. |
| `MF` | same buckets | Full labels, same order/length, e.g. `['December 2025',...]`. |
| `MMAP` | derived | `{'YYYY-MM': index}`. |
| `M` | see object table below | 21 keys, each an array length == `MO`. |
| `PROD` | see object table below | Per-product objects, ordered by lifetime revenue descending. |
| `DAILY` | see DAILY table below | One row per day. |
| `CAMP` | see CAMP table below | Per-campaign **monthly series** (arrays aligned to `MO`); `renderCampaigns()` sums over the active Period, filters to spend>0, top 40 by spend. |
| `COGS` | user / cost file (Step 0c) | Per-unit COGS in **PROD order**. If none, `[0,0,...]` (one zero per product). |
| `PARENTS` | *optional* — you / catalog / SKU families | **New in this version.** Explicit variation families for the Products **Parent** view: `[{id, name, emoji, asins:[...]}]`. Omit (or `[]`) => the template **auto-derives** families from the SKU prefix. Supply it when you want exact parent groupings/labels (e.g. from Amazon catalog relationships or known product lines). Account-level only; does not affect any other tab. |
| `SNS` | `get_subscribe_save` (+ `get_financial_summary` discount) | Subscribe & Save object — see SNS table below. `null` (or `{available:false}`) → the tab renders its empty state. |
| `OVR` | optional / user | Manual **backfill & override** layer: `{ 'YYYY-MM': { sales, units, ad, varFees, fbaFul, operating, storage, promo, refunds } }`. Applied on top of the pulled `M` each render (manual value wins). Usually omit (`{}`) — the **dashboard itself** lets the user fill/override these via the "Manual data & backfill" card on the Profitability tab (inline editor **or** CSV/XLSX upload). Only pre-seed `OVR` if the user hands you historical numbers at build time. Keys map to `M` fields; `sales`→`rev`+`grossSales`, `units`→`units`+`gunits`. A month key in `OVR` (or `ADDED`) that isn't in `MMAP` **extends the month axis** — the dashboard re-aligns every `M`/`PROD`/`SNS` array (0 where unpulled) so the new month flows into the trend, P&L and totals (account-level only — no per-product split for added months). |
| `ADDED` | optional / user | `['YYYY-MM', …]` months to add to the axis that the **API never returned** — e.g. ads beyond the ad-report lookback window (sales/financials reach further back than SP/SB/SD reports). The dashboard's "+ Add month" button writes here; pre-seed only if backfilling at build time. Pair with `OVR[month]` to give the added month its values (typically just `ad`). |

#### `M` (monthly) object — every key present, each an array same length as `MO`

| Key | Source | Derivation |
|---|---|---|
| `rev` | `query_sales_traffic by_date` `ordered_product_sales` | Group by month, SUM. |
| `units` | `query_sales_traffic by_date` `units_ordered` | Group by month, SUM. |
| `orders` | `get_orders_summary` `by_currency[USD].order_count`, one call per month | True monthly distinct orders. |
| `ad` | `get_ads_summary by_date` `cost` | Group by month, SUM (combined SP+SB+SD). |
| `adSales` | `get_ads_summary by_date` `sales` | Group by month, SUM (PPC-attributed). |
| `impr` | `get_ads_summary by_date` `impressions` | Group by month, SUM. |
| `clicks` | `get_ads_summary by_date` `clicks` | Group by month, SUM. |
| `sp`/`sb`/`sd` | `get_ads_summary view=overall` `by_type.{sp,sb,sd}.cost`, one call/month | Per-channel spend. |
| `spSales`/`sbSales`/`sdSales` | `get_ads_summary view=overall` `by_type.{sp,sb,sd}.sales`, one call/month | Per-channel ad sales. |
| `net` | derived (informational) | The **template recomputes net in-browser** as `rev − ad − fees − promo − refunds − (per-unit COGS × units)` using the real fee arrays above. The value you supply isn't read; the COGS editor + fee arrays drive the live figure. |
| `varFees` | `get_financial_summary` `by_month[].referral_fees` | **`|value|`** (positive magnitude). Referral (Commission). |
| `fbaFul` | `get_financial_summary` `by_month[].fba_fees` | **`|value|`**. FBA fulfillment fees. |
| `promo` | `get_financial_summary` `by_month[].promotions` | **`|value|`**. Includes SnS discount. |
| `refunds` | `get_financial_summary` `by_month[].refunds` | **`|value|`**. Net of refund events. |
| `operating` | `get_financial_summary` `by_month[].other_fees` | **`|value|`**. Any non-referral/non-FBA item fees. |
| `storage` | `GET_FBA_STORAGE_FEE_CHARGES_DATA` (per-month report) → SUM monthly storage charge | Positive magnitude per month; in the template fee sum so it flows into net. |
| `lowInv` | none (lands in `other_fees`→`operating`) | `0`. |
| `grossSales` | `get_financial_summary` `by_month[].gross_sales` | Positive (settled shipped Principal). **Profitability P&L revenue** for closed months (Overview uses ordered `rev`). Absent → template falls back to `rev`. |
| `gunits` | `get_financial_summary` `by_month[].units` | Settled units; Profitability COGS basis for closed months. Absent → falls back to `units`. |

> **COGS is per-unit, not a dollar total.** The template multiplies `COGS[productIndex] × PROD.units[month]` (`cogsMonth()`) to get monthly COGS dollars, then nets it out. Supply the blob's `COGS` array as per-unit dollars in PROD order; never pre-multiply.

#### `PROD` object — one entry per active product, each array length == `MO`

| Field | Source | Derivation |
|---|---|---|
| `asin` | `list_top_products` `asin` | Direct. Drop `_`-prefixed placeholders. |
| `name` | `list_top_products` `title` | Full title. |
| `short` | none | Synthesize from title/sku pack size, e.g. `Coffee Chews 30ct`. |
| `emoji` | none | One-character category emoji. |
| `sku` | `list_top_products` `sku` | Direct. |
| `rev[]` | `query_sales_traffic by_asin` `ordered_product_sales`, per month | `rev[monthIndex]`; absent → 0. |
| `units[]` | `query_sales_traffic by_asin` `units_ordered`, per month | absent → 0. |
| `ad[]` | `query_ppc product_ads` `spend`, per month | SP+SB+SD; absent → 0. |
| `acos[]` | `query_ppc product_ads` `acos`, per month | As **percent** (fraction × 100); guard months with 0 ad sales. |
| `fees[]` | `get_financial_summary` `view="full"` `by_sku_month[]` | Per `(sku,month)` sum `|referral_fees|+|fba_fees|+|other_fees|` (positive; **exclude** promotions — the template allocates promo per-product by revenue share via `M.promo`); map sku→asin; one value per month (length == `MO`); absent → 0. |
| `grev[]` | `get_financial_summary` `view="full"` `by_sku_month[].gross_sales` | Settled revenue per `(sku,month)`, map sku→asin; the **Profitability per-product P&L** uses this for closed months; absent → falls back to ordered `rev[]`. |
| `sunits[]` | `get_financial_summary` `view="full"` `by_sku_month[].units` | Settled units per `(sku,month)`, map sku→asin; Profitability per-product COGS basis; absent → falls back to `units[]`. |

Filter out ASINs with zero revenue across every month AND zero ad spend across every month. Sort `PROD` by lifetime revenue descending.

#### `DAILY` — `[date, rev, units, orders, fees, ad, refunds]`, one row per day

| Index | Field | Source |
|---|---|---|
| 0 | `date` | chosen daily source `rows[].date` (`YYYY-MM-DD`, ascending) |
| 1 | `rev` | `query_sales_traffic by_date` `ordered_product_sales` |
| 2 | `units` | `query_sales_traffic by_date` `units_ordered` |
| 3 | `orders` | **none** → `0` (no per-day distinct order count; `total_order_items` is a line-item proxy only). **Not read by the tiles** — they use `ROLL` (below). Leave `0`; never surface this column as an order count. |
| 4 | `fees` | `get_financial_summary` `view="by_date"` `by_date[]` — match by date, `|referral_fees|+|fba_fees|+|other_fees|`; missing day → 0. **Posted-date basis; recent days partial** (see 1F). |
| 5 | `ad` | `get_ads_summary by_date` `cost` (match by date; missing day → 0) |
| 6 | `refunds` | `get_financial_summary` `view="by_date"` `by_date[]` — match by date, `|refunds|`; missing day → 0. |

#### `ROLL` — `{ today, yest, last7 }`, true distinct order counts for the rolling Daily tiles

The Daily tile preset renders five tiles: Today, Yesterday, Last 7 days, Month to date, Last month. The two month tiles read `M.orders` (real, from the per-month `get_orders_summary` loop). The three rolling tiles used to sum `DAILY[][3]`, which is **always `0`** — so they rendered **"0 orders / 459 units"**, which is self-evidently impossible and reads as "you had no orders."

`get_orders_summary` returns a true distinct order count for **any** window via `start_date`/`end_date` — that's exactly what the per-month loop exploits. Every tile is a window, so the rolling tiles get their own scoped call:

| Key | Call | Window |
|---|---|---|
| `today` | `get_orders_summary` | `start_date = end_date = DAILY[n-1][0]` (the last daily row — **not** the wall-clock date; the orders snapshot lags) |
| `yest` | `get_orders_summary` | `start_date = end_date = DAILY[n-2][0]` |
| `last7` | `get_orders_summary` | `start_date = DAILY[max(0,n-7)][0]`, `end_date = DAILY[n-1][0]` |

**Sum `order_count` across EVERY `by_currency[]` row — not just USD.** An order count is unit-less: `292 US + 98 CA + 2 MX = 392 orders` is valid arithmetic. Currency mixing corrupts **money**, never **counts**. Reading `by_currency[USD]` here (as `M.orders` does) would put US-only orders next to all-marketplace units on the same tile. Drop the stray `UNKNOWN` / `Non-Amazon` row (a few $0 orders). Three extra calls, each loading 1–2 weekly files — nowhere near the ~30-file cap.

> **Note the asymmetry with `M.orders`**, which still reads `by_currency[USD]` only. On a multi-currency store the month tiles therefore under-count orders relative to the rolling tiles. That's pre-existing and blocked on the wider currency decision — don't "fix" it by making `ROLL` USD-only too.

**Omit `ROLL` entirely rather than guessing.** Absent → the tiles render **"—"**. Same rule as the campaign table (*Honest zeros → "—"*): a `0` we can't source is a fabricated number, and it contradicts the units sitting next to it. The template also suppresses `ROLL` under a product filter — `get_orders_summary` has no ASIN filter, so an account-level count would overstate a filtered view.

> **Known remaining gap:** the P&L chart's `Orders` metric at day/week granularity still reads `DAILY[][3]` and plots zeros. `ROLL` covers three windows, not a per-day series, so it can't fix that. Prefer month granularity when charting Orders.

#### `CAMP` — per-campaign **monthly series**: `{ name, type, status, spend[], sales[], orders[], impr[], clicks[] }`

One object per campaign; every array month-aligned to `MO` (length == `MO`). Built per 1E: `spend[]` reconciled to the account's per-type monthly spend; `sales[]`/`orders[]`/`impr[]`/`clicks[]` spend-weighted from the freshest report (SP real; SB orders-only; SD none — zeros render as "—"). `status` = `'ENABLED'` placeholder. `renderCampaigns()` sums over the active Period, filters to `spend>0 || sales>0`, sorts by spend, takes top 40, and recomputes ACOS/ROAS. **ACOS/ROAS are never stored** — the template derives them from the period sums so they stay period-correct.

#### `SNS` object — Subscribe & Save (arrays length == `MO`, month-aligned via `MMAP`)

| Field | Source | Derivation |
|---|---|---|
| `available` | derived | `true` when `get_subscribe_save` returned months. `false`/`null` → tab empty state. |
| `marketplace` | `get_subscribe_save` `metadata.marketplace` | The resolved marketplace id (e.g. `ATVPDKIKX0DER`). |
| `active[]` | `by_month[].active_subscriptions` | Point-in-time count per month; **absent → `null`** (renders "—"), never 0. |
| `units[]` | `by_month[].shipped_subscription_units` | Can be fractional; absent → 0. |
| `rev[]` | `by_month[].subscription_revenue` | **Program** revenue (the SnS Revenue KPI); absent → 0. |
| `oos[]` | `by_month[].not_delivered_oos_units` | Units missed due to OOS; absent → 0. |
| `discount[]` | `get_financial_summary` `by_month[].sns_discount` | `|value|`; settlement coupon cost (table only — already in `M.promo`). |
| `lift` | `get_subscribe_save` `data.lift` | `{ ratio: lift_ratio, subAvg: subscriber_avg_revenue, nonSubAvg: non_subscriber_avg_revenue, window }`. |

The tab respects the Period filter (it slices `SNS.*` by the same month range as the other tabs). Active Subscribers KPI = latest in-period month with a value; SnS Revenue / Shipped Units = sums over the period; Subscriber Lift = `lift.ratio` shown as `+(ratio−1)×100%`; OOS Lost Revenue = `Σ oos[i] × (rev[i]/units[i])`. 30/90-day retention and coupon penetration are **not exposed by the Amazon feed** → the template shows them as N/A.

**Daily/Weekly granularity on the S&S tab (estimated).** Amazon reports S&S **monthly** (`get_subscribe_save` → `by_month[]`). When the user switches the global Granularity toggle to **Daily** or **Weekly**, the S&S tab no longer no-ops — it **estimates** a daily/weekly series by distributing each in-period month's `SNS.rev`/`units`/`oos` across that month's days **in proportion to each day's share of total account sales** (the `DAILY` revenue curve), so the line moves with the account's real sales rhythm instead of being flat. Totals are preserved (the daily estimates always sum back to the monthly figure; months with no `DAILY` coverage fall back to an even calendar spread so nothing is dropped). Active Subscribers is point-in-time → held flat at the month value. A disclaimer banner appears in this mode, driven by `meta.snsDailyEstimatedBefore` (see meta table) — name the date true daily reporting begins, or omit it so the banner says all daily figures are estimated. **You don't build any of this** — it's in the template; just supply the monthly `SNS` arrays + `DAILY` as usual, and optionally set `meta.snsDailyEstimatedBefore`. *(Note: the underlying SP-API Replenishment ingestion now pulls a rolling 7-day window at `DAY` granularity going forward — but only the trailing ~week exists at true daily grain and the MCP tool still returns monthly, so the dashboard estimates rather than using real daily rows. When the tool later exposes daily rows, this section can switch from estimate to real.)*

### Refresh manifest (`meta.manifest`) — the live-artifact refresh contract

Record the exact Step-1 calls **you actually made** so Cowork (and a future you) can re-run them. The shape below is the S&T-healthy path; **if the coverage probe sent you down the fallback chain, record the calls you actually used** (e.g. drop `products_sales`, point `sales_daily`/monthly rev-units at `get_orders_summary` + settled `by_date`) so a refresh doesn't re-pull empty S&T. Shape:

```jsonc
"manifest": {
  "store": "<seller_id>", "marketplace_id": "US default (omit)",
  "window": { "start": "YYYY-MM-DD", "end": "YYYY-MM-DD", "months": 6 },
  "calls": [
    { "id": "catalog",            "tool": "list_top_products",   "args": {…}, "note": "ASIN universe + titles/sku" },
    { "id": "sales_daily",        "tool": "query_sales_traffic", "args": {"view":"by_date",…}, "note": "MO/MF/MMAP + M.rev/M.units + DAILY rev/units" },
    { "id": "orders_monthly",     "tool": "get_orders_summary",  "args": {"per":"month"}, "note": "M.orders" },
    { "id": "orders_roll",        "tool": "get_orders_summary",  "args": {"per":"tile-window"}, "note": "ROLL.today/yest/last7 — one scoped call per rolling tile window" },
    { "id": "ads_daily",          "tool": "get_ads_summary",     "args": {"view":"by_date",…}, "note": "M.ad/adSales/impr/clicks + DAILY ad" },
    { "id": "ads_overall_monthly","tool": "get_ads_summary",     "args": {"view":"overall","per":"month"}, "note": "M.sp..M.sdSales" },
    { "id": "products_sales",     "tool": "query_sales_traffic", "args": {"view":"by_asin","asins":"ALL","per":"month"}, "note": "PROD.rev/units" },
    { "id": "products_ppc",       "tool": "query_ppc",           "args": {"view":"product_ads","asins":"ALL","per":"month"}, "note": "PROD.ad/acos" },
    { "id": "financials",         "tool": "get_financial_summary", "args": {"view":"full","per":"month"}, "note": "M.varFees/fbaFul/promo/refunds/operating + M.grossSales/gunits (settled P&L revenue/units) + PROD.fees/grev/sunits + SnS settlement $ (sns_sales/units/discount) + DAILY.fees/refunds (view:full also returns by_date + by_sku_month)" },
    { "id": "subscribe_save",     "tool": "get_subscribe_save",  "args": {"per":"window"}, "note": "SNS.active/units/rev/oos + lift (subscriber metrics)" },
    { "id": "storage_fees",       "tool": "discover_amazon_reports + get_amazon_report_full", "args": {"api_type":"SP","report_type":"GET_FBA_STORAGE_FEE_CHARGES_DATA","per":"month"}, "note": "M.storage (sum monthly storage charge) — BEST-EFFORT: often 'Response was not valid JSON' → default 0, set meta.storageNote" },
    { "id": "campaigns",          "tool": "discover_amazon_reports + query_report", "args": {"api_type":"ADS"}, "note": "CAMP" }
  ],
  "refresh": "Re-run these for the same store+window, re-shape per Step 1-2, re-inject the blob. Fees/promo/refunds + SnS settlement $ come from get_financial_summary; SnS subscriber metrics from get_subscribe_save; storage from GET_FBA_STORAGE_FEE_CHARGES_DATA; lowInv stays 0; COGS persists from the user."
}
```

Do NOT put the literal characters `/*__DATA__*/` inside any manifest string (it trips the marker check). Say "the data injection point" instead.

## Step 3 — build the live artifact (inject seed, stamp config, inline the pipeline)

The template ships **pre-spliced** for the native live artifact: a seed loader in `<head>`, a cache-first `__APD__` read, a `window.__APD_USER__` capture in `renderAll` (so COGS / manual-backfill survive a refresh reload), and a `<!--__REFRESH_PIPELINE__-->` slot before `</body>`. Your build does **four string edits** on a working copy — nothing else in the template changes.

1. **Copy** `assets/dashboard-template.html` → `{Brand}_Dashboard.html`.
2. **Inject the seed blob.** There is exactly **one** injection site: `window.__APD_SEED__ = /*__DATA__*/{};` (in the seed loader). Replace `/*__DATA__*/{}` with the whole blob JSON so it reads `window.__APD_SEED__ = {…blob…};`. Match the full `/*__DATA__*/{};` (with the trailing `{};`) — the literal `/*__DATA__*/` also appears once in the header `<!-- -->` doc comment, so never match a bare `/*__DATA__*/`. **The blob shape is exactly Step 2, unchanged** (same `meta`/`manifest`/`M`/`PROD`/`DAILY`/`CAMP`/`COGS`/`SNS`). The `meta.manifest` still records the calls — it's the human-readable contract and the pipeline's source of tool shapes.
3. **Stamp the localStorage key.** Replace every `__APD_LSKEY__` with `apd_<store>_v2` (lowercase `seller_id`; the `v2` mirrors the current `meta.schema` — see the HARD RULE after step 6). This is the loader's cache key and MUST match step 4.
4. **Inline + stamp the refresh pipeline.** Read `assets/refresh-pipeline.js`, replace its four build-time config tokens, and inline the result at `<!--__REFRESH_PIPELINE__-->` as an inline `<script>…</script>` (an external `src` is blocked in the file-preview sandbox — it MUST be inlined):
   - `__APD_STORE__` → the `seller_id`
   - `__APD_LSKEY__` → `apd_<store>_v2` (identical to step 3)
   - `__APD_PREFIX__` → the live MCP prefix detected this session (e.g. `mcp__<server>__`) — never hardcode it
   - `__APD_MARKETPLACE__` → the `marketplace_id` this dashboard is scoped to. **Required whenever the store has more than one currency** (Step 0's `by_currency[]` check) — not just "when it's non-US". Leave the token/empty ONLY for a genuinely single-currency store (the pipeline treats an unreplaced token as "omit"). A US-primary store that also sells CA/MX **is multi-currency and must be stamped** — that's exactly the case that shipped `$0` ad spend.
5. **Validate** (parses every script block, checks no leftover markers/tokens, seed + manifest present):

```bash
node -e "const fs=require('fs');const h=fs.readFileSync('OUT.html','utf8');const B=h.match(/<script>([\\s\\S]*?)<\\/script>/g)||[];if(B.length<3)throw new Error('expected >=3 script blocks, got '+B.length);B.forEach((b,i)=>{try{new Function(b.replace(/<\\/?script>/g,''))}catch(e){throw new Error('block '+i+' parse: '+e.message)}});const S=B.join('');const bad=(S.match(/\\/\\*__[A-Z_]+__\\*\\//g)||[]).concat(S.match(/__APD_(?:STORE|LSKEY|PREFIX|MARKETPLACE)__/g)||[]).concat(S.match(/{{[A-Z_]+}}/g)||[]);if(bad.length)throw new Error('leftover: '+bad.join(','));if(!h.includes('\"manifest\"'))throw new Error('missing manifest');if(!h.includes('window.__APD_SEED__'))throw new Error('missing seed loader');console.log('OK: '+B.length+' blocks parse, seed+manifest present, no leftover tokens')"
```

6. **Save** `{Brand}_Dashboard.html` to the workspace folder.

> **HARD RULE — the render schema and the refresh-pipeline output schema MUST stay in lockstep.** The template reads blob keys one way; `refresh-pipeline.js` writes them another; a stale `localStorage` cache holds yesterday's shape. If any of the three disagree on a key's shape, that tab renders empty or `NaN` (this is exactly how the CAMP table went blank — the template was changed to an object-per-campaign monthly series while the pipeline still emitted the old flat array and a stale cache still held it). So whenever you change the shape of ANY blob key: **(a)** update `refresh-pipeline.js` to emit the identical shape (its `mergeMonth`/reshape), **(b)** bump `meta.schema` (and the `apd_<store>_v<schema>` key follows it), and **(c)** the loader's `okShape()` guard already drops caches whose `meta.schema` differs or whose `CAMP[0]` isn't the object shape — extend that sniff if you add another shape-sensitive key. Never change one side alone.

**Runtime contract to verify on first live open** (the one thing that couldn't be pre-tested): the pipeline calls `window.cowork.callMcpTool(<prefix+tool>, args)` and unwraps `r.structuredContent ?? JSON.parse(r.content[0].text)`, throwing on `r.isError`. If the live Cowork signature differs, adjust **only** `callMcpTool()` in `refresh-pipeline.js` — nothing else touches `window.cowork`. Watch the console `[APD]` logs on first open for capped-call bisections or skipped-empty-month messages.

## Step 4 — verify

- JS parses; `window.__APD__.meta.manifest.calls` has one entry per data call (the live self-check).
- All five tabs render. Profitability shows real fees. **Subscribe & Save:** when `SNS` is populated, the tab shows Active Subscribers, SnS (program) Revenue, Shipped Units, Subscriber Lift, the Active-Subscribers-&-Revenue combo chart, the OOS % chart, OOS Lost Revenue, and the monthly detail table; 30/90-day retention + coupon penetration show N/A. With `SNS = null` the tab falls back to its empty state without erroring.
- KPIs match a hand-summed check: `sum(M.rev)` ≈ overview Sales; `sum(M.ad)/sum(M.rev)*100` ≈ TACOS.
- Header wordmark / date pill / SnS badge are populated (from `meta`) — not blank.
- Comparison behaves honestly: a full-window/Lifetime view with a "Previous period" comparison shows **"no data"** (no equal prior period); pick Last Month or Last 3 Months for a genuine delta. A partial latest month is badged and excluded from the trend; its KPI delta is day-matched.
- Profitability shows real fees: Net = settled Revenue − Ad Spend − COGS − (referral + FBA + other fees + storage + promotions + refunds). Sanity-check that `sum(M.varFees)` and `sum(M.fbaFul)` are **positive magnitudes** on the order of ~15% and ~10–20% of `sum(M.grossSales)` respectively; `sum(M.storage)` is small and positive **if** the storage report parsed — but it commonly comes back 0 (report fails on many stores); 0 is acceptable and should be noted in `meta.storageNote`, not treated as a bug.
- **Settlement-basis reconciliation:** the Profitability tab uses settled `M.grossSales` (not ordered `M.rev`) for closed months, so its totals should tie to `sum(net_proceeds) − COGS − Ad` over those months and to the brand's Amazon payouts. It will **not** equal the Overview (ordered-sales) net — that gap is expected (ordered vs shipped/settled timing, ad-attributed sales, refunds settling later) and the tab's banner explains it. Confirm the current partial month and the daily tiles fall back to ordered (settlement not posted yet).

## Step 5 — deliver as a native live artifact (`create_artifact`)

- **In Claude Cowork (the live path):** deliver with **`create_artifact`**, granting the eight refresh tools so the in-page pipeline can call them on open:
  ```
  create_artifact({
    id: "<store>-account-performance",
    html_path: "<the built {Brand}_Dashboard.html>",
    mcp_tools: [ get_orders_summary, get_ads_summary, query_sales_traffic, query_ppc,
                 get_financial_summary, get_subscribe_save, discover_amazon_reports, query_report ]
                 // fully-qualify EACH with the live MCP prefix detected this session
  })
  ```
  On open the seed paints instantly; the pipeline then re-pulls the trailing 30 days, merges over the saved blob, updates `meta`, and reloads for a clean render — **no agent turn needed.** A status banner shows "updated N min ago" with a "Refresh now" button; auto-refresh is throttled to once/hour. Tell the user it self-refreshes on open.
- **Fallback (`present_files`) for non-Cowork delivery:** the same file is a fully-working interactive **snapshot** — the pipeline sees `window.cowork` is absent and shows "Snapshot mode" instead of refreshing. Use this for a downloaded file, a Netlify deploy, or a shared demo. **These never self-refresh** — a scheduled rebuild is the only way to keep them current. The footer states the data-through date.
- **CRITICAL — Chart.js is INLINED, do not re-externalise it.** The template embeds Chart.js 4.5.0 inline (`<script>/*! Chart.js v4.5.0 inlined */…</script>`), so charts render in **every** delivery path — Cowork live artifact, the **file-preview sandbox** (which blocks ALL external scripts), a downloaded file in Chrome, and offline. This was a recurring blank-render bug: a CDN `<script src>` loads fine in Chrome/artifact but is **blocked in the file-preview sandbox** → `Chart` undefined → render throws → blank. Inlining removes the dependency entirely. If you ever rebuild from a raw template, keep Chart.js inline (re-inline from `cdn.jsdelivr.net/npm/chart.js@4.5.0/dist/chart.umd.js`); never swap back to an external tag.
- **Optional XLSX reader** lazy-loads SheetJS from jsdelivr **only** when the user uploads an `.xlsx` in the Manual-data card; it's off the render path and has a "save as CSV" fallback if the sandbox blocks it. **Google Fonts** (`fonts.googleapis.com`/`gstatic.com`) is not allowlisted in the sandbox — Inter falls back to system fonts (cosmetic only).
- **Delivery:** in Cowork, deliver via **`create_artifact`** with the `mcp_tools` grant above (not a file-preview) — that grant is what lets the in-page pipeline call `window.cowork.callMcpTool`. Inlined charts mean it renders in every path, but the in-page **refresh** only runs where `window.cowork` is present.

### How the in-page refresh works (what's inlined)

`assets/refresh-pipeline.js` is brand-agnostic; only the four `__APD_*__` tokens are stamped per store (Step 3.4). On open it:

1. **Seeds once, then caches.** First open writes the seed blob to `localStorage[apd_<store>_v2]` and paints it. Later opens read the cached (tail-refreshed) blob — the template's `const __APD__=(window.__APD_CACHE__||window.__APD_SEED__)` is cache-first. A loader `okShape()` guard drops the cache if its `meta.schema` or `CAMP` shape doesn't match the seed (so a schema bump self-heals stale caches).
2. **Freezes >30 days, re-pulls the tail.** It recomputes the calendar months intersecting the trailing 30 days and re-pulls **only those** — six calls per month (`get_orders_summary`, `get_ads_summary view=overall`, `query_sales_traffic by_date`, `query_sales_traffic by_asin`, `query_ppc product_ads`, `get_financial_summary view=full`), reshaped **exactly like Step 1–2**. 30 days covers Amazon's ~2-week settlement lag + 7/14-day ad-attribution maturation. Everything older stays frozen.
3. **Merges, then reloads.** `mergeMonth` overwrites `M.*[i]`, each `PROD[*].*[i]`, and that month's `DAILY` rows; it **never** touches `COGS`/`OVR`/`ADDED`/`PARENTS`. SnS (whole window) and CAMP (freshest ~14-day campaign report) refresh separately and keep seed values on any failure. Then `location.reload()` — the template does its clean one-time render from fresh cache (sidesteps Chart.js "canvas already in use").
4. **Guards.** (a) A month is merged only when it has signal (`rev+ad+orders>0`) so a user's off clock or an empty window can't zero out good months. (b) Server-side file-count caps are handled by an auto **window-splitter** that bisects the date range and merges per shape. (c) Model-context "saved to file" limits do **not** apply in-browser — `callMcpTool` hands full JSON to JS; do not replicate file-dump handling. (d) Live COGS / manual-backfill edits are captured from `window.__APD_USER__` before reload so they persist.

### Data-accuracy notes to surface in `meta` (generic to the source)

- **Settled fees lag ~40 days.** `get_financial_summary` fully settles only ~the last 40 days, so itemized referral/FBA/promo/refund are complete for closed months only; earlier/current months fall back to ordered revenue with fees→0. State in `meta.storageNote`/`meta.sourceNote`.
- **Top-N scope on long-tail catalogs.** Account tabs are complete; only the Products tab is scoped to the chosen ASIN set. Record in `meta.scope` + footer.
- **Ordered vs settled, USD only.** Overview/Products use ordered Sales & Traffic (USD, US); Profitability uses settled gross for closed months. Note both in `meta.sourceNote`.
- **Daily ad spend is allocated,** distributed across each month by daily revenue share (not pulled per-day) — noted on the daily/weekly views.

## Data coverage & the Profitability tab

**Live from Sophie Hub (real numbers):** product sales, units, sessions/traffic (daily + monthly); true distinct order count (window-level; per-month via one call/month); full advertising rollup incl. SP/SB/SD split and daily ad spend; per-product rev/units/ad-spend/ACoS per month; campaigns (top 40, ~30d) with name/type/spend and — for SP — sales/ACoS/ROAS/orders. **Plus, via `get_financial_summary` (SP-API Finances feed):** referral (Commission), FBA fulfillment, other fees, promotions, refunds and the **Subscribe and Save split** (sales/units/discount) — per month and per SKU.

**Best-effort (often fails):** `M.storage` from `GET_FBA_STORAGE_FEE_CHARGES_DATA`. `get_amazon_report_full` frequently returns `"Response was not valid JSON"` for this report → storage defaults to 0 and is excluded from net. When it does parse, it's summed per month and folded into the fee sum. Don't present storage as a guaranteed line; note it in `meta.storageNote` when it's missing.

**Daily fees now wired:** `DAILY[].fees`/`DAILY[].refunds` come from `get_financial_summary` `view:"by_date"` (or `view:"full"`, which also returns `by_date`) — posted-date basis, so the latest ~1–2 weeks are partial until settlement closes; treat the daily/weekly P&L as directional, not a tie-out to that day's sales.

**Still zero (no source):** `M.lowInv` (low-inventory fee — no dedicated report; lands in `other_fees`→`M.operating`); `DAILY[].orders` (no per-day distinct order count); `CAMP[].status` (placeholder `ENABLED`); SB per-campaign sales/ACoS/ROAS and SD per-campaign sales/orders/ACoS/ROAS. Per-product **SB/SD** ad spend isn't attributable per ASIN — shown as a "Brand & Display (unallocated)" line in the per-product P&L. Truly manual (ask at setup): FBM outbound shipping. Not yet ingested: refund admin fee (in financialEvents, needs `get_financial_summary` to expose it) and sellable-returns disposition (needs the FBA customer-returns report).

**Profitability tab:** real fees. Net = `rev − ad − cogs − (referral + fba + other + promotions + refunds)`. COGS is still supplied by the user / a cost file (per-unit, PROD order); if none, COGS = 0 and Net = Revenue − Ad − fees. Storage fees are *attempted* from `GET_FBA_STORAGE_FEE_CHARGES_DATA` (best-effort — often fails with `"Response was not valid JSON"`, in which case storage = 0 and is noted in `meta.storageNote`); low-inventory fee (`M.lowInv`) stays 0 (it's inside `other_fees`).

**Subscribe and Save:** fully wired. Build the `SNS` object (Step 1G + Step 2): subscriber count / shipped units / **program** revenue / OOS / trailing-12-month lift from **`get_subscribe_save`** (the Replenishment feed), plus `discount[]` from `get_financial_summary`. The template's `#tab-sns` renders the KPIs, the Active-Subscribers-&-Revenue combo chart, the OOS % chart, OOS Lost Revenue and the monthly detail table, and respects the Period filter. 30/90-day retention and coupon penetration are **not exposed by any Amazon feed** → shown as N/A. Per-ASIN SnS is unavailable (Amazon's per-offer metrics ship empty). If `get_subscribe_save` isn't deployed in the session yet, populate the SnS $ side from `get_financial_summary` and leave `SNS.active`/`SNS.lift` null (subscriber KPIs show "—"); set `SNS = null` for a store with no SnS program to get the clean empty state.

## What NOT to do

- Don't build the dashboard HTML/CSS/charts from scratch. Always start from the template.
- Don't rename, restyle, or rearrange tabs, KPI cards, charts, or tables. Consistency is the whole point.
- Don't substitute the consumer-facing brand with a seller-account alias.
- Don't add or remove tabs. Subscribe & Save stays even when a store has no SnS orders (it just renders empty).
- Don't fabricate or estimate fees — pull the real numbers from `get_financial_summary`. Storage from `GET_FBA_STORAGE_FEE_CHARGES_DATA` is best-effort and **often fails** (`"Response was not valid JSON"`) → default it to 0 and note it; don't block the run on it. `M.lowInv` stays 0 (it's inside `other_fees`); never guess either one.
- Don't pre-multiply COGS by units — supply per-unit COGS; the template does the multiply.
- Don't hand-format numbers; the JS formatters in the template handle that.

## When to refresh

If the user asks for "yesterday's data", "this week's data", or to "update the dashboard", re-run the `meta.manifest` calls with the new end date (today minus 1), recompute the current-month bucket and the daily tail, re-run `discover_amazon_reports` for fresh campaign s3 keys, rebuild the blob (carry the user's COGS forward), re-inject at `/*__DATA__*/`, and overwrite the same `{Brand}_Dashboard.html`. In Cowork this is exactly what the live artifact does automatically on open.

---

## Install (run before Step 1 if the template isn't already on disk)

This skill needs **two** assets, both shipped inside `skill-scripts.json`: `assets/dashboard-template.html` (the pre-spliced 5-tab template) and `assets/refresh-pipeline.js` (the in-page live-refresh pipeline, inlined at build — Step 3.4). On a local Claude Code install the files are already next to this `SKILL.md` — use them and skip the rest. On a cold Atlas/Hub install, fetch + unpack the bundle once (the loop below writes every bundle entry, so both land automatically).

1. **Resolve `<SLUG>`** — do not hardcode it. Use the slug from the "Supporting files" footer the Hub appends, else the slug this skill was invoked under.
2. **Resolve `<skill-path>`.** If `assets/dashboard-template.html` already exists next to `SKILL.md`, set `<skill-path>` to that directory and **skip to Step 1**. Otherwise set `<skill-path> = $CACHE = ~/.cache/sophie-hub-skills/<SLUG>/` (fall back to `<cwd>/audit-tmp/skill-cache/<SLUG>/` if `~` isn't writable).
3. **Detect the MCP prefix off a tool you can already see** — take a Sophie-Hub tool name as it appears in this session (e.g. `mcp__<server>__get_skill_asset`), strip the bare tool name; the rest is `<prefix>`. Use that same prefix for every data tool in Step 1.
4. **One fetch, then unpack** — `fetch_envelope("skill-scripts.json")` → `json.loads(env["content"])` → `write_text` each entry under `<skill-path>`.
5. **Verify** `assets/dashboard-template.html` exists and contains the **single** data-as-props marker `/*__DATA__*/`. **There are no `/*__MONTHS__*/` / `/*__COGS__*/` markers and no `{{BRAND_NAME}}` placeholder anymore** — the old multi-marker / mustache format was replaced by one injection point (`const __APD__=/*__DATA__*/{};`) that `applyMeta()` reads at runtime. Checking for the old markers will falsely fail. **Note the marker literally appears twice in the file:** once in the header `<!-- -->` doc comment (line ~13) and once at the real injection site (`const __APD__=…`). The injection target is the one *with the trailing `{};`* — match `/*__DATA__*/{};` (or the full `const __APD__=/*__DATA__*/{};`), never a bare `/*__DATA__*/`, so you don't overwrite the comment copy. The leftover-marker check in Step 3 already scopes to `<script>` blocks, so the comment copy doesn't trip it; just don't use a naive whole-file `grep /*__DATA__*/` as a "did I inject?" test — it will always find the comment copy.

```python
import json, re, pathlib

SLUG = "<resolved-slug>"
CACHE = pathlib.Path.home() / ".cache" / "sophie-hub-skills" / SLUG

def fetch_envelope(path: str) -> dict:
    # mcp_get_skill_asset = the get_skill_asset tool under the detected <prefix>
    resp = mcp_get_skill_asset(slug=SLUG, path=path)
    if isinstance(resp, dict):
        return resp
    if isinstance(resp, str):                       # large responses auto-save to a .txt
        m = re.search(r"saved to (\S+\.txt)", resp)
        if m:
            return {"content": pathlib.Path(m.group(1)).read_text(encoding="utf-8")}
    raise RuntimeError(f"unexpected get_skill_asset response: {str(resp)[:200]}")

bundle = json.loads(fetch_envelope("skill-scripts.json")["content"])
for rel, src in bundle.items():
    dest = CACHE / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(src, encoding="utf-8", newline="")

tpl = (CACHE / "assets" / "dashboard-template.html").read_text(encoding="utf-8")
pipe = (CACHE / "assets" / "refresh-pipeline.js").read_text(encoding="utf-8")
# Single seed-injection point (in the __APD_SEED__ loader). The marker /*__DATA__*/ also
# appears once in the header <!-- --> doc comment — the injection site is the one with `{};`.
assert "/*__DATA__*/{};" in tpl, "template missing the window.__APD_SEED__ = /*__DATA__*/{}; injection site"
assert "APD-TEMPLATE schema=2" in tpl, "WRONG/OLD template (no APD-TEMPLATE version marker) — do NOT fall back to another template; re-fetch the canonical one"
assert "APD-TEMPLATE-END schema=2" in tpl[-300:], "template TRUNCATED on fetch (missing end sentinel) — re-fetch; NEVER build from a partial file"
assert "<!--__REFRESH_PIPELINE__-->" in tpl, "template missing the pipeline inline slot"
assert "__APD_STORE__" in pipe and "__APD_PREFIX__" in pipe, "refresh-pipeline.js missing its build-time config tokens"
print("template + pipeline ready at", CACHE / "assets")
```

Keep run commands written as `<skill-path>/assets/dashboard-template.html` so they work in both the local-disk and cold-install cases.
