---
name: launch-sponsored-products
description: >-
  Launch live Amazon Sponsored Products (SP) ONLY campaigns by API through a
  guided, question-by-question intake. Does NOT launch Sponsored Brands or
  Sponsored Display (their creatives aren't creatable via our tools). Use
  whenever Nacho wants to CREATE, LAUNCH, ACTIVATE, or SET UP Amazon Sponsored
  Products campaigns — e.g. "lanzá una campaña", "lanzar campañas en Amazon",
  "crear una campaña SP", "armar una campaña de PPC", "activá esta campaña",
  "nueva campaña para [ASIN]", "launch a campaign", "create SP campaigns", "set
  up PPC for [brand]", or any request to push auto/manual keyword or
  product-targeting campaigns live. Asks for everything Amazon needs (store,
  marketplace, targeting, ASINs, budget, keywords, bids, placements, negatives,
  activation date), suggests Sophie-convention names and Helium10 bids, shows a
  summary, and creates only after one final OK. NOT sp-bulk-builder (that makes
  an XLSX) and not for auditing or optimizing existing campaigns.
---

# Launch Sponsored Products (SP only, live via API)

This skill walks Nacho through launching one or more **Sponsored Products** campaigns
and creates them **live via the Amazon Ads API**. Nothing is created until a single
final confirmation. Think of yourself as a careful media buyer sitting next to him:
ask what's needed, suggest sensible defaults, never touch the account without the OK.

**Scope:** Sponsored Products only (Auto, Manual-keyword, Manual-product/ASIN targeting).
**Sponsored Brands and Sponsored Display are deliberately out of scope** — their creatives
require an Amazon Ads asset library / brand tooling that isn't exposed to us, so they
can't be launched end-to-end by API. If Nacho asks to launch SB or SD, say so plainly and
point him to the Ads console for those. This is also *not* `sp-bulk-builder` (that produces
an XLSX to upload by hand); here we create entities by API.

**Writes are restricted to Sophie Society staff.** Nacho qualifies. If a write is
rejected as unauthorized, report it plainly — don't try to work around it.

The full API contract (exact tool names, argument shapes, enums) lives in
`references/amazon-ads-sp-api.md`. **Read that file before making any create call.**

---

## Core principles (the "why")

- **Safety through review, not guesswork.** Live API writes are hard to undo. So we
  collect *all* campaigns first, print one clear summary, and only create after Nacho
  says go. This mirrors how he asked for it: configure everything, one OK at the end.
- **No spend today unless he wants it.** Instead of pausing campaigns, we set the
  **activation date** (`startDateTime`) — default **tomorrow**. An ENABLED campaign with
  a future start date sits idle until that date, so it "starts by itself" the next day.
- **Suggest, don't impose.** Names follow the Sophie convention but are always editable.
  Bids are suggested from real CPC data but Nacho edits anything before the OK.
- **Flexible scale.** He may launch one campaign, or two or three, or a whole Sophie
  architecture. Loop the intake; don't force a fixed set.

---

## The flow

### Step 0 — Store & marketplace
1. Call `mcp__Sophie_Hub__list_stores` and let Nacho pick the store (say "store", never "seller ID").
2. Ask **which marketplace** to launch to and offer the store's marketplaces as options
   (US, CA, MX, UK/GB, DE, …). One marketplace per run keeps things simple; if he wants
   several, confirm and repeat the create per marketplace.
3. Resolve the Amazon Ads **profileId** for that store+marketplace (needed for every call).
   If you can't resolve it from the store record, use
   `mcp__Sophie_Hub__sophie_call_amazon_ads_mcp` with a profile/account query tool, or ask.

### Step 1 — How many campaigns
Ask what he wants to launch this run: a single campaign, a few, or a full architecture.
Then intake them **one at a time** in a loop ("¿otra campaña?" after each) until he's done.
Hold each configured campaign in a working list — **create nothing yet.**

### Step 2 — Per-campaign intake
For each campaign, ask (reuse earlier answers as defaults so he isn't re-asked needlessly):

1. **Targeting type:** Auto · Manual keywords · Manual product/ASIN targeting.
2. **ASIN(s) to advertise:** he pastes them. (For sellers you'll resolve ASIN→SKU later.)
3. **Campaign name — fixed structure, confirm the theme.** The name ALWAYS follows the
   6-field structure in *Naming convention* below:
   `SO | [Product] | [ASIN] | SPM|SPA | [Keyword Theme] | [Match Type]`. Only the
   **[Keyword Theme]** is up to you to infer — **suggest** it from the keyword list and ask
   Nacho to confirm or edit (offer to split a heterogeneous list into several themes →
   several campaigns). Everything else is determined by the choices already made. Assemble
   the full name and **show it inside a fenced code block** (never inline — a `|` in prose
   truncates it) for a final edit. The **ad group name is identical to the campaign name.**
4. **Daily budget — default $20.** Propose **$20** as the default and let Nacho change it;
   if he just confirms, use $20.
5. **Targets** (skip for Auto):
   - He pastes the keyword list (or ASINs for product targeting).
   - **One match type for the whole batch** — ask which (Broad / Phrase / Exact for
     keywords; Exact / Similar for product targets).
6. **Bids:** suggest a bid per target from CPC data (see *Bidding*), show the numbers,
   let him edit any. **No guardrails** — use the CPC as-is; he reviews in the summary.
   For Auto (and as fallback), ask a **base bid** for the ad group default.
7. **Bid strategy:** default **Dynamic bids – down only** (`SALES_DOWN_ONLY`); offer to
   switch to up-and-down or fixed.
8. **Placements:** **ask every time** — the % for Top of Search and Rest of Search
   (and Product pages if he wants). 0 = no adjustment. Note: Sponsored Products only
   supports **placement** bid modifiers. Audience modifiers ("high interest", in-market,
   remarketing/views, etc.) do **not** exist in SP — they belong to Sponsored
   Display/DSP, which this skill does not cover. If Nacho asks for an audience % modifier,
   say it's out of scope (SP only) and don't fake it with a placement.
9. **Negatives (optional):** offer to add negative keywords / negative ASINs; he can skip
   with enter. Ask match type (Exact/Phrase for negative keywords).
10. **Activation date:** default **tomorrow**; let him pick another date. Confirm the
    marketplace timezone assumption if it matters.

### Step 3 — Enrich bids
Before the summary, fill in suggested bids for every keyword (see *Bidding* below).

### Step 4 — Resolve products (sellers)
Seller product ads are created **by SKU**, and one ASIN can have **several SKUs**
(FBA + FBM, replens, relisted offers). Advertising the wrong SKU advertises the wrong
offer, so resolve carefully:

1. Enumerate the SKUs for each advertised ASIN. `get_product_catalog` /
   `get_product_catalog_bulk` returns the snapshot SKU; when an ASIN may have more than
   one SKU, cross-check a listings/inventory source (e.g. Helium10 `list_my_products` /
   FBA inventory, or `list_top_products` which carries the selling `sku`).
2. **One SKU** → use it.
3. **Several SKUs** → prefer the **active, in-stock, FBA** offer. If it's still ambiguous
   (e.g. two live FBA SKUs), **show Nacho the candidates (SKU, fulfillment, stock) and let
   him pick** — never guess silently.
4. If no SKU can be resolved, flag that ASIN and keep going (report at the end).

### Step 5 — Global summary + single OK
Print one compact summary of **all** campaigns: name, type, marketplace, budget, bid
strategy, placement adjustments, activation date, advertised products, and the target
list with per-target match type, **search volume**, and bid (and negatives). Then ask
for **one final confirmation** to create everything. Do not create before this OK.

**Rendering:** campaign/ad-group names contain `|`, which breaks Markdown (inline or in a
table) and truncated a real preview down to just "SO |". So show **every name inside its
own fenced code block** (triple backticks), one per line — never inline in a sentence,
never in a piped table. Put the rest of each campaign's fields (budget, bids, dates, etc.)
in the surrounding text or a table, but keep the name itself in the code block.

### Step 6 — Create (after OK)
Create each campaign using `references/amazon-ads-sp-api.md`:
- **Auto** → `create_singleshot_sp_campaign` (Path A), one call each.
- **Manual** → `create_campaign` → `create_ad_group` → `create_ad` (one per ASIN/SKU) →
  `create_target` (batch, per-keyword bids) → `create_target` negatives (Path B).

Capture returned ids at each step; a later step needs the earlier id.

**On error: continue and report at the end.** If a campaign (or a row) fails —
ineligible ASIN, missing SKU, rejected keyword — skip that item, keep creating the rest,
and finish with a clear report: what was created (with ids) and what failed (with the
reason and enough detail to retry).

---

## Naming convention (FIXED — always exactly this)

Every campaign name follows this exact 6-field structure, in this order, joined by
" | " (space-pipe-space). No other variants, ever:

```
SO | [Product] | [ASIN] | [SPM|SPA] | [Keyword Theme] | [Match Type]
```

- **Field 4** is `SPM` for manual campaigns or `SPA` for auto campaigns.
- **[Keyword Theme]** is the keyword cluster label (e.g. "Hair Growth", "Scalp Care") —
  not the product, not the match type. For **auto (SPA)** campaigns use `Auto` as the theme.
- **[Match Type]** — manual keyword: `Broad` / `Phrase` / `Exact`; manual product
  targeting: `Product Exact` / `Product Similar`; auto (SPA): `Auto` (or the auto group
  Close Match / Loose Match / Substitutes / Complements if Nacho splits them).

**The ad group name MUST be identical to the campaign name** — same 6 fields, same order.
Set them to the same string.

Examples:
```
SO | Hair Growth Serum 30ml | B0CWY24FTC | SPM | Hair Growth | Exact
SO | Hair Growth Serum 30ml | B0CWY24FTC | SPA | Auto | Auto
```

Building the name (Step 2.3): infer the **[Keyword Theme]** from the keywords, **suggest**
it and have Nacho confirm/edit before locking (offer to split a heterogeneous keyword list
into several themes → several campaigns). Everything else in the name is fixed. Always show
the suggested name and let Nacho edit before it's locked in.

**Reference existing account campaigns.** When it helps (matching an existing product name
spelling, an established theme label, portfolio, or how similar campaigns are structured),
pull the account's current campaigns first — `mcp__Sophie_Hub__list_ad_campaigns` (fast), or
Amazon Ads `campaign_management-query_campaign` via `sophie_call_amazon_ads_mcp` — and align
the new names/structure to what's already there so the account stays consistent.

**Displaying names — never let them truncate.** A `|` in prose or inside a Markdown table
breaks rendering (that's what cut a preview down to just "SO |"). So **always show every
campaign/ad-group name inside its own fenced code block** (triple backticks) on its own
line — never inline in a sentence, never in a piped table, never after a bullet. This
applies to the intake preview, the theme confirmation, and the final summary.

---

## Bidding — suggested bid source chain

Nacho reviews and edits all bids, so aim for a useful *starting* number per keyword.
Amazon's own "suggested bid" endpoint is **not** available through our tools, so use this
chain and take the first source that returns a CPC for the keyword:

1. **Helium10 Cerebro** — `mcp__Helium10__analyze_keywords({ keywords:[...], marketplace })`
   returns a per-keyword **`suggested_bid_usd`** (use this as the bid) plus `search_volume`
   (show it next to the bid for context). Batch up to 200 keywords per call. This is the
   primary, cleanest source. If `suggested_bid_usd` is absent for a row, fall back to any
   CPC field on that row, then to the chain below. (`mcp__Helium10__get_keywords_by_keyword`
   also returns these for a seed.) Match rows by the `phrase` field — output order ≠ input order.
2. **Shurq** — fall back to the account's own historical CPC for keywords already seen.
   Discover the right tool via `mcp__SHURQ_-_NEW__get_schema` / `search`, then `execute`.
3. **DataDive** — `mcp__Sophie_Hub__sophie_list_datadive_tools` then
   `sophie_call_datadive_adapter` for a keyword CPC if H10 and Shurq have nothing.
4. **Base bid fallback** — for ASIN/product targets, or keywords no source covers, use the
   **base bid** Nacho set for the campaign.

No floor/ceiling is applied — present the raw CPC and let him adjust. Match H10 results by
the `phrase` field (output order is not input order). Note the source next to each
suggested bid in the summary so he knows where the number came from.

---

## What to reuse / not reinvent

- Store & product data: Sophie Hub (`list_stores`, `get_product_catalog`).
- Keyword CPC: Helium10 Cerebro (primary).
- Never generate an XLSX here — that's `sp-bulk-builder`. This skill only creates live.
- If Nacho asks for Sponsored Brands/Display, say those are out of scope: their creatives
  need an asset library / brand tooling that isn't available to us, so point him to the
  Ads console for SB/SD instead of starting a flow that can't finish.

## Dry-run

If Nacho says "dry run", "sin crear", "solo mostrame el resumen", or similar, run the
whole intake and print the summary **but do not call any create tool.** Useful for
reviewing structure and bids before committing.
