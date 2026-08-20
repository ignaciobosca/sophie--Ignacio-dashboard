---
name: launch-amazon-campaigns
description: >-
  Launch live Amazon Sponsored Products (SP) campaigns by API through a guided,
  question-by-question intake. Use this whenever Nacho wants to CREATE, LAUNCH,
  ACTIVATE, or SET UP one or more Amazon PPC / Sponsored Products campaigns —
  e.g. "lanzá una campaña", "lanzar campañas en Amazon", "crear una campaña SP",
  "armar una campaña de PPC", "activá esta campaña", "nueva campaña para [ASIN]",
  "launch a campaign", "create SP campaigns", "set up PPC for [brand]", or a
  request to push auto/manual keyword/product-targeting campaigns live. The skill
  asks for everything Amazon needs (store, marketplace, targeting type, ASINs,
  budget, keywords, bids, placements, negatives, activation date), suggests
  Sophie-convention names and Helium10-based bids, shows a global summary, and
  creates everything only after one final OK. It creates entities LIVE via the
  Amazon Ads API, so it is the right skill anytime the intent is to actually
  launch/activate — not to generate a bulk upload file (that is sp-bulk-builder)
  and not to audit or optimize existing campaigns.
---

# Launch Amazon Campaigns (Sponsored Products, live via API)

This skill walks Nacho through launching one or more **Sponsored Products** campaigns
and creates them **live via the Amazon Ads API**. Nothing is created until a single
final confirmation. Think of yourself as a careful media buyer sitting next to him:
ask what's needed, suggest sensible defaults, never touch the account without the OK.

**Scope:** Sponsored Products only (Auto, Manual-keyword, Manual-product/ASIN targeting).
Not Sponsored Brands/Display yet. This is *not* `sp-bulk-builder` (that produces an XLSX
to upload by hand); here we create entities by API.

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
3. **Campaign name:** propose one using the **Sophie convention** (below) and let him edit.
4. **Daily budget.**
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
   Display/DSP. If Nacho asks for an audience % modifier, say it's out of scope for SP
   and flag it as the natural add for the future SB/SD extension; don't fake it with a
   placement.
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

**Rendering:** campaign names contain `|` (the Sophie convention), which breaks Markdown
tables. Always show each full campaign name on its own line or in a code block — never
inside a piped table — so it's never truncated.

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

## Naming convention (Sophie)

Mirror `sp-bulk-builder`. Base pattern:

```
SO | [Product Name] | [ASIN] | [Campaign Type] | [Details]
```

Campaign-type strings:
- Auto: `SPA | Close Match` · `SPA | Loose Match` · `SPA | Substitutes` · `SPA | Complements`
  (for a plain single auto campaign, `SPA | Auto` is fine)
- Manual keyword theme: `SPM | [Theme] | Broad` · `SPM | [Theme] | Phrase` · `SPM | [Theme] | Exact`
- Single keyword: `SPM | SK | Br|Ph|Ex | [keyword]`
- Brand: `SPM | Brand [Theme] | Broad|Phrase|Exact` · `SPM | Brand Only`
- Product targeting: `SPM | PT | [Competitor Brand] | Exact` · `SPM | PT | [Competitor Brand] | Expanded`
- Catch-all: `Catch All | 10 cents`

Always show the suggested name and let Nacho edit before it's locked in.

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
- If Nacho asks for Sponsored Brands/Display, say those aren't covered yet and offer to
  scope them as a follow-up.

## Dry-run

If Nacho says "dry run", "sin crear", "solo mostrame el resumen", or similar, run the
whole intake and print the summary **but do not call any create tool.** Useful for
reviewing structure and bids before committing.
