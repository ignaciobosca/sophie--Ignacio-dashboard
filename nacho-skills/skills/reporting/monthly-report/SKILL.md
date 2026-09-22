---
name: monthly-report
description: >-
  Generate a Sophie Society Monthly Business Review (MBR) as a branded PPTX for any Amazon client.
  Trigger whenever Nacho says "monthly report para [Brand]", "hacé el monthly de [Brand]", "generate
  the monthly for [Brand]", "MBR para [Brand]", "reporte mensual de [Brand]", or any variation of
  "monthly / mensual / MBR" plus a client brand name. The full end-to-end monthly deck the pod leader
  presents in client meetings — a ~20-slide strategic review of the whole account, not just PPC: KPI
  scorecard, trend charts, a full PPC audit, organic/SQP visibility, profitability, inventory,
  Subscribe & Save, competitive share-of-voice, promotions, work completed, next steps. Pulls data
  live (SHURQ + Sophie Hub + Supabase + ClickUp), builds Sophie-branded charts and a python-pptx
  deck, and delivers the .pptx to chat for Canva. Use for monthly/MBR reporting even without the word
  "skill". For a WEEKLY report use weekly-report; for a PPC-only audit use ppc-audit.
---

# Monthly Business Review (MBR) — PPTX generator

**Versión:** V2.0 · SHURQ edition (2026-09-12) — **migrada de AdLabs a SHURQ.** Misma estructura de deck,
mismas secciones y misma narrativa; lo único que cambió es la **capa de datos del trend KPI + PPC**
(AdLabs `profile`/`campaign`/`search_term`/`negative_targeting` → SHURQ `get_ads_daily_trend` +
`get_sales_traffic` + `custom_metric_calculator` + `query_table` + `list_negative_targets`) y la
**resolución de cuenta** (`adlabs_team_id`/`adlabs_profile_id` → `shurq_account_id` + `mkp_id`). Las
otras fuentes (Sophie Hub para P&L/S&S/inventario/SQP, Keepa, DataDive, ClickUp, Supabase) quedan
**idénticas**. Los scripts (`build_charts.py`, `build_deck.py`) leen `report_data.json` y son
agnósticos de la fuente — **no cambian** (sus menciones a "AdLabs-style" son de estilo visual del deck).

Generate the Sophie Society Monthly Business Review: a strategic, whole-account monthly deck
the pod leader presents to the client. Data is pulled live, charts are matplotlib, the deck is
python-pptx, and the finished `.pptx` is delivered to chat (the user edits it in Canva).

The deck's job is to make Nacho look like the account's **strategist**, not "the PPC guy" — so it
covers the full P&L story, not only advertising. Every number must be real and sourced; never
invent figures. When data for a section is missing, show the section with a "limited data" note
rather than fabricating or silently dropping it.

---

## STEP 0 — Resolve inputs (always ask for dates)

You need three things: **brand**, **start date**, **end date**.

- Brand comes from the trigger.
- **Always ask the user for the exact start and end dates** — do not assume a calendar month.
  Nacho reports on custom windows (e.g. Aug 1–30, or Jul 20–Aug 19). Ask: *"¿Qué rango exacto?
  (inicio + fin)"* if not given.
- **Comparison period = the same dates shifted back exactly one calendar month** (mirror, not
  "N days back"). Examples: `Aug 1–30 → Jul 1–30`; `Jul 20–Aug 19 → Jun 20–Jul 19`.
  Edge case: if the shifted day does not exist in the prior month (e.g. end date Mar 31 → "Feb 31"),
  use the **last day of that prior month**, and note it on the KPI slide.
- **12-month trend window** for charts = the 11 calendar months before the reported month's month,
  through the reported month. Use whole calendar months for the trend even when the reported
  window is a partial month.

**Always ask, at trigger time, whether to include the optional per-ASIN deep-dive** — do not wait
for the user to volunteer it. In the same clarifying round where you confirm the dates, ask e.g.
*"¿Sumo un breakdown per-ASIN? ¿De cuál/es?"* and offer the client's `managed_asins` (from config,
STEP 1) as click-to-pick options plus a "no, así está bien". Record the chosen ASINs as
`products_requested` (empty = skip). Each selected ASIN gets 3 slides (What's working / Underperforming
/ Actions) before the Thank You. If the user already named ASINs in the trigger
("incluí análisis de B0XXXXXXXX"), take those and skip the question.

**In the same round, ask whether to include the competitive enrichment** (layer 2 of the Competitive
slide). Ask e.g. *"¿Sumo análisis competitivo (Keepa/DataDive)?"* If the client's config already has
`competitor_asins` (set at onboarding), offer *"uso los 5 del config / pegame otros / no"* and default
to the config set. If the config has none, offer *"pegame hasta 5 ASINs / no"*. Record as
`competitors_requested` (empty = SQP-only). This only enriches the Competitive slide — the SQP share
layer runs regardless. See STEP 2 for how the two layers combine.

---

## STEP 1 — Load client config from Supabase

Config lives in the `clients` table of the **POD 66 - Organization** Supabase project
(`project_id: awhiobrcgghyiycxukjm`), one row per brand, with everything inside a `config` JSON.

Read `references/data-pulls.md` §Supabase for the exact query. Extract:
`brand_name, acos_target, tacos_target, account_stage, monthly_budget, report_language (default en),
adlabs_profile_id, adlabs_team_id, shurq_account_id, amazon_marketplace, managed_asins
(with per-child cogs_per_unit + shipping_cost_per_unit), competitor_asins (up to 5, set at
onboarding — feeds the Competitive slide's layer 2), datadive_niche_id / datadive_rank_radar_id
(if onboarding set up tracking), slack_internal_channel_id, drive_folder_id,
notes`. Also resolve the **Sophie Hub store (seller_id)** for the brand via `list_stores`
(match on brand/alternative names — some brands' seller account uses a different legal name,
e.g. **Hekaya's** seller is **"MyNextGen"**; the notes field flags these).

If no config row exists → tell the user and offer to run `client-onboarding` first.

**Targets fallback:** if `acos_target`/`tacos_target` are missing or "not defined", use
stage-based defaults and label them "(default)" on the deck:
`launch → ACOS 100% / TACOS 50%` · `growth → 40% / 25%` · `optimization → 30% / 20%`.

**Multi-marketplace clients** (e.g. Happy Fox US+CA, Solar Reserve EU): generate **one deck per
marketplace** (money never sums across currencies). Confirm which marketplace(s) to run.

---

## STEP 2 — Pull data (source-of-truth rules)

These rules exist because Sophie Hub's **advertising** data only goes back a few months, so it
silently reports `$0 ad spend` for older months and makes an ad-driven account look "organic-only".
**SHURQ has the full PPC + total-business history and is the source of truth for the whole KPI trend.**
Follow `references/data-pulls.md` for exact calls; the mapping:

| What | Source of truth |
|---|---|
| **Full monthly KPI + PPC trend** — spend, ad-sales, total sales, organic, sessions, units, CVR, CTR, CPC, ACOS, TACOS, per month | **SHURQ** (`get_ads_daily_trend` + `get_sales_traffic` + `custom_metric_calculator`, bucketed by calendar month). Fallback to **Sophie Hub** `get_account_performance_summary` only if SHURQ returns no total_sales for the account (then total/organic/sessions come from Sophie Hub and PPC from SHURQ). |
| PPC deep-dive — campaigns MoM, structure, wasted spend, search terms, negatives | **SHURQ** (`query_table` campaigns_daily / searchterms_daily / keywords_daily + `list_negative_targets`) |
| Real P&L (referral, FBA, other fees, promotions, refunds, net proceeds) | **Sophie Hub** `get_financial_summary` |
| Subscribe & Save (subscribers, lift) | **Sophie Hub** `get_subscribe_save` |
| Inventory (on-hand, days of cover) | **Sophie Hub** `get_inventory_availability` |
| SQP / search visibility / share of voice (Competitive slide, layer 1 — always) | **Sophie Hub** `get_sqp_metrics` |
| Competitive product intel — competitor price/rating/reviews/BSR/units, category rank (Competitive slide, layer 2 — only with `competitors_requested`) | **Keepa** via `sophie_call_keepa_adapter` |
| Organic-rank battlefield — organic vs sponsored rank, Rank Radar trend (Competitive slide, layer 2) | **DataDive** via `sophie_call_datadive_adapter` |
| Top products by revenue | **Sophie Hub** `list_top_products` |
| Targets, COGS per SKU, account config | **Supabase** `clients` |
| Work Completed (tasks done + pending) | **ClickUp** (auto-lookup by brand name) |

SHURQ is now the **primary** for the KPI + PPC trend (see `references/data-pulls.md` §SHURQ for the
90-day chunking that avoids its long-range cap). Sophie Hub is the fallback for total/organic/sessions.

Assemble everything into **one `report_data.json`** (schema in `references/slides.md` §report_data).
Round money to cents. Compute organic each month as `total_sales − ad_sales` (floor at 0).
Verify SHURQ `total_sales` (from `get_sales_traffic.revenue`) reconciles with Sophie Hub S&T revenue
for the reported month (they should match within rounding); if they diverge materially, note it and
trust SHURQ for the trend.

---

## STEP 3 — Build charts

Run the bundled generator (it reads `report_data.json` and writes Sophie-branded PNGs to `charts/`):

```bash
python scripts/build_charts.py <path/to/report_data.json>
```

It produces the standard MBR chart set from the monthly series: Total Sales (PPC vs Organic,
stacked), Advertising Efficiency (spend vs ad-sales + ACOS line with target), TACOS & ACOS lines,
Traffic & Conversion (sessions + CVR), CPC & CTR, and Top Products (horizontal). It skips any chart
whose data is all-zero. Do not hand-roll chart code — extend the script if a client needs a new
chart type so every future run benefits.

---

## STEP 4 — Build the deck

```bash
python scripts/build_deck.py <path/to/report_data.json>
```

This renders the full ~20-slide Sophie-branded PPTX from the `slides` array in `report_data.json`.
See `references/slides.md` for the section order, the slide-type catalog, and how to fill each.
The deck is **English** (override only if `report_language != en`), one long deck (all sections
inline), 16:9, Calibri, Sophie green `#13835B`.

**Narrative quality is the point.** For every text slide write real analytical prose (not filler):
state the MoM delta, explain the probable cause, cite the specific numbers, and end on the "so
what". Match Nacho's voice — casual-professional, assertive, strategist-level. `references/slides.md`
§narrative has the per-section guidance and the "1 positive paragraph" rule for the exec summary.

---

## STEP 5 — Deliver

Send the finished `.pptx` to chat with `SendUserFile` (the user uploads it to Canva). Do **not**
push to Google Drive or Slack. Filename: `MMDDYYYY_[Brand]_Monthly Report_[Range].pptx`.

Then give a short chat summary: the headline story, the KPI highlights (Total Sales, TACOS, ACOS,
Net contribution — each with MoM delta), and any **caveats** the user must know before presenting
(sections flagged "limited data", COGS estimated, targets defaulted, a source that failed). Be
honest about what's soft — the user is walking into a client meeting with this.

---

## Section list (default order — all inline)

Fixed structure; a section with no data still appears with a "limited data" note.

1. Cover
2. Executive Summary (headline + 4 stat tiles + "what's working")
3. KPI Scorecard (reported vs comparison, MoM delta, vs target)
4. Chart — Total Sales (PPC vs Organic)
5. Chart — Advertising Efficiency (spend vs ad-sales + ACOS)
6. Chart — Traffic & Conversion (sessions + CVR)
7. Chart — Product Mix (top products)
8. Performance Analysis (3–4 analytical paragraphs)
9–11. **PPC Deep Dive** (full audit depth — structure health, wasted spend, winners/bleeders,
   ACOS vs target by campaign, budget pacing, placements, harvest/negate opportunities).
   Lean on the `ppc-audit` (SHURQ) skill's methodology.
12. Organic & Search Visibility (SQP beachhead terms, share of voice)
13. **Competitive / Share of Voice** — layer 1 (always): SQP share by keyword (beachhead vs
   headroom). Layer 2 (with `competitors_requested`): named-competitor table (Keepa: price, rating,
   reviews, BSR, est. units/mo) + organic-rank move (DataDive Rank Radar). See `references/slides.md`.
14. **Search-term Optimization Recap** (what we harvested / negated this month, from SHURQ)
15. Profitability Snapshot (real fees → net proceeds → COGS → net contribution)
16. **Promotions & Coupons Impact** (from get_financial_summary promotions)
17. Inventory Health (on-hand, reorder priority, overstock/LTS risk)
18. Subscribe & Save (recurring base, lift)
19. Work Completed (from ClickUp — completed + pending)
20. Next Steps
21. Thank You
(+ optional 3 slides per ASIN in `products_requested`, before Thank You.)

Tier note: the structure is the same for every client; on a small/launch account many sections will
be thin — that's expected, flag them "limited data". Nacho deletes what he doesn't want in Canva.

---

## Reference files

- `references/data-pulls.md` — exact tool calls per source, incl. the **SHURQ monthly-fetch recipe**,
  the **Sophie-Hub fallback**, the **ClickUp lookup**, and the Supabase query.
- `references/slides.md` — the `report_data.json` schema, the slide-type catalog, and per-section
  narrative guidance.
- `scripts/build_charts.py` — Sophie-branded chart generator (reads report_data.json).
- `scripts/build_deck.py` — Sophie-branded PPTX builder (reads report_data.json).
