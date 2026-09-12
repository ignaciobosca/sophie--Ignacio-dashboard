# report_data.json schema, slide catalog & narrative guidance

You assemble ONE `report_data.json`, then run `build_charts.py` and `build_deck.py` on it. Write it
to a working dir (e.g. `/tmp/mbr-<brand>/report_data.json`); charts land in `<dir>/charts/` and the
`.pptx` next to the json.

## Top level

```json
{
  "meta": {"brand": "Hekaya", "filename": "09012026_Hekaya_Monthly Report_August 2026.pptx"},
  "charts_dir": "charts",
  "targets": {"acos": 50, "tacos": 25},          // PERCENT numbers; from Supabase or stage default
  "top_products_title": "Top Products by Revenue — August (41% from the Variety 7-Pack)",
  "top_products": [["Variety 7-Pack", 949.62], ["Royal Oud 4-Pack", 424.83]],
  "monthly": { ...see build_charts.py header... },
  "slides": [ {"type": "...", ...}, ... ]
}
```

`monthly` arrays are all the same length, one entry per calendar month (chronological). Store
`acos/tacos/ctr/cvr` as percent numbers (108.8, not 1.088), `cpc/$` as dollars, `acos` = 0 or null
in months with no ad sales. Charts auto-skip when their series is all zero.

## Design notes

`Deck.header()` renders the title only — green, bold, no kicker unless one is explicitly passed, no
rule/underline, no vertical bar. Earlier versions added a horizontal rule and a small accent stripe next
to a kicker on every slide; both are gone. This isn't cosmetic preference — decorative accent lines under
titles and edge stripes on cards read as AI-generated filler (see `/mnt/skills/public/pptx/SKILL.md`'s
design-quality rules) and the reference client-facing look (AdLabs-style PPC audit decks) doesn't use
them: title, whitespace, then the table. Don't reintroduce header rules/stripes when adding new slide
types.

## Rich text ("runs")

A paragraph is a list of runs; a run is `[text, style]`. Style keys: `size`, `bold`, `italic`,
`color`. Color is a hex (`"#13835B"`) or a token: `DARK GREEN GOLD RED G900 G700 G300 WHITE`.
A bare string works as an unstyled run.

## Slide catalog (set `"type"`)

- **cover** — `{brand, subtitle, period_label, period, meta}`
- **exec_summary** — `{title, highlight:[runs-of-one-paragraph], tiles:[{label,val,sub}]×4, working_title, working:[str]}`. The highlight is ONE paragraph (a list of runs). Lead the working bullets with the single positive point.
- **kpi_table** — `{title, header:[5 strings], rows:[[metric,prev,cur,delta,target]], delta_dir:["up"|"down"|"neutral" per data row — is the delta FAVORABLE?], footnote}`. "up"=green, "down"=red, "neutral"=grey. For ACOS/TACOS a decrease is favorable → "up".
- **chart** — `{title, image:"chart_sales.png", takeaway}`. `image` is a filename in charts_dir.
- **narrative** — `{title, paragraphs:[{head, body}]}` (3–4). Analytical prose.
- **bullets** — `{title, subtitle?, items:[{head?, body}], size?, gap?, footnote?  OR  banner:{label,text}}`. Use for Organic/SQP, Competitive, Search-term recap, PPC narrative, Work Completed, Next Steps.
- **two_card** — `{title, subtitle?, left:{...}, right:{...}}`. Each card: `{accent:"GOLD"|"GREEN"|"RED", heading, big?, big_sub?, bullets:[{head?,body}]  or  body}`. Use for Inventory & S&S, or any two-panel section.
- **pl_table** — `{title, rows:[{label,val,color?,bold?}], note?, panel:{accent,title,runs}, footnote?}`. The Profitability slide.
- **data_table** — `{title, subtitle?, intro?:[runs-of-one-paragraph], header:[strings], rows:[[cell,...]], col_widths?:[numbers], chart_image?:"chart_x.png", caption?:[runs-of-one-paragraph], banner?:{label,text}}`. **The default slide type for any finding with per-row entities** — campaigns, search terms, keywords, competitors, products, tactics/buckets. A cell is a bare string, or `["text","COLOR_TOKEN"]` to flag a value (typically `RED` for a zero-return/bleeder row, left plain for everything else — don't color-code a whole table, only the specific bad numbers). `col_widths` are relative weights (default: first column 2x the rest, since it usually holds the longest label). `chart_image` places one small chart to the right of a narrowed table (see build_charts.py output) for a table+chart split slide. `caption` is 1-3 short lines under the table with the "so what" — this is where the analysis lives, not in a separate prose slide. Renders via `build_deck.py`'s `s_data_table`.
- **thankyou** — `{line?}`

## Section order → slide types (default deck)

1 cover · 2 exec_summary · 3 kpi_table · 4–7 chart (sales, spend_sales, sessions_cvr, products) ·
8–13 **data_table** (PPC Deep Dive: what's-working, where-budget-is-going, root-cause/negate candidates,
harvest opportunities; Organic & Search Visibility; Competitive / Share of Voice) · 14 pl_table
(Profitability) · 15 bullets (Promotions & Coupons) · 16 two_card or bullets (Inventory) · 17 two_card
or bullets (Subscribe & Save) · 18 bullets (Work Completed) · 19 bullets (Next Steps) · 20 thankyou.
(Inventory + S&S can share one two_card if both are thin.) Optional per-ASIN: 3 data_table/bullets
slides per requested ASIN before thankyou.

Add the TACOS&ACOS and CPC&CTR charts (`chart_tacos_acos.png`, `chart_cpc_ctr.png`) as extra chart
slides when the client is ad-heavy and they add signal.

**Do not use a standalone `narrative` slide for the PPC/Organic/Competitive findings** — that reads as
a wall of text next to the rest of the deck's tables (this was a real client-facing complaint: too much
prose, not enough table, from slide 8 through the search-term recap). `narrative` still exists for the
rare case where there's genuinely no natural row/entity to tabulate; default to `data_table` otherwise.
Pull real per-row data before writing these slides — search-term-level rows (`entity_type="search_term"`)
give a far sharper root-cause number ("90.7% of spend touched a zero-order search term") than a
campaign-level rollup does, and Keepa's `keepa_get_product` gives a real competitor table instead of
a prose paragraph about "well-funded competitors."

## Narrative guidance (this is where the value is)

Write like Nacho: casual-professional, assertive, strategist-level, English. Never filler.

- **Executive Summary highlight:** one tight paragraph — the month's story in 2–3 sentences, honest.
  Then the `working` bullets, led by the single strongest positive (the "1 positive paragraph" rule).
- **Performance Analysis (narrative):** 4 paragraphs — (1) Revenue (total, organic vs paid split,
  MoM), (2) Efficiency (spend %, ACOS, TACOS vs comparison), (3) Conversion (CVR, sessions, units),
  (4) Forward signal / key insight. For each: state the delta, explain the probable *cause* (not
  just what moved), cite specific numbers (% and pp), end on the "so what".
- **PPC Deep Dive:** audit depth. Structure health, spend concentration, winners (ACOS<target) to
  scale and bleeders (ACOS≫target / spend-no-sale) to cut/negate, budget pacing, and the one clear
  play ("move budget from X to Y, negate Z"). Bot findings are bug reports — verify and act.
- **Competitive / Share of Voice (two layers).** Layer 1 (always): SQP share — split keywords into
  the **beachhead** (terms where we win purchase share → defend) and the **headroom** (big head terms
  where share ≈ 0 → who's taking it). Layer 2 (only with competitor ASINs, from Keepa/DataDive — see
  data-pulls §Competitive): a **named-competitor table** — one bullet per competitor with price ·
  rating · reviews · BSR · est. units/mo — so headroom stops being abstract ("[Comp] owns [term] at
  $24.99, 4.6★/12k, ~3k u/mo vs our 600"); plus the **organic-rank move** from DataDive Rank Radar
  ("#22 → #8 on [money kw]"). Render the competitor table as a `bullets` slide (head = competitor
  name, body = the stats line); keep the SQP read as the framing above/below it. **Month-1 caveat:**
  if the Rank Radar was just set up at onboarding, there's no trend yet — show the current-rank
  snapshot and label it "baseline (trend from next month)". If no competitor ASINs resolve, ship
  layer 1 only and flag "limited data — no competitor set configured; add 5 at onboarding".
- **Profitability:** lead with the real fees → net proceeds → COGS → net contribution. If the account
  is underwater, reframe honestly: is the loss customer-acquisition/launch investment (unit economics
  positive pre-ad) or a structural ACOS problem? Say which. Put the single sharpest number in the panel.
- **Reframes that land:** organic share climbing; unit contribution before ads; LACoS/lifetime value
  when ACOS looks scary; the efficiency trend (direction) when the level is still off-target.
- **Honesty:** a soft month is a soft month — say so, then show the discipline/plan. Flag every
  "limited data" section and every estimate on the deck itself, and repeat the caveats in the chat
  hand-off so the user isn't surprised in the meeting.

## Filename

`MMDDYYYY_[Brand]_Monthly Report_[Range].pptx` — MMDDYYYY = today; Range = reported month/label.
