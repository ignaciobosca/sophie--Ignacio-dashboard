---
name: sp-sb-bulk-bid-optimizer
description: Run the Sophie Society bidding method on one Amazon Ads bulk export, covering both Sponsored Products and Sponsored Brands including SBV. Five strategies (Profit-First, Balanced, Launch, Ranking Push, ACOS-Targeted but CPC-Managed) set the dials; a deterministic Python scorer does all bid math. Asks whether Sponsored Brands should match the SP parameters or use its own, then splits SB by ad format (Video, Product Collection, Store Spotlight) so each is benchmarked against itself, and pauses SB more patiently than SP. Produces one branded HTML approval dashboard where the operator ticks, unticks and edits, then downloads an approved xlsx (SP and SB sheets), a reverse xlsx, or an approved_changes.json that pushes bids and placement modifiers live to the account via the Sophie Hub MCP, pre-flighted and canary-first. Trigger on requests to optimize, recompute, adjust or push Sponsored Products, Sponsored Brands or SBV bids, with or without an uploaded bulk.
sophie-skill-format: v1
---

## ▶▶ RUN GATE — do this FIRST, before anything else (do NOT skip)
**STOP. Before any tool call, MCP/connector call, file read, script run, or workflow step — STOP and do this first.**

1. This skill runs on an **uploaded Amazon Ads bulk export** and scores it with **local Python**. It has **NO live-data connector.** Present the modes:
   - **MCP — N/A (does not exist for this skill).** There is no MCP path, for **Sponsored Products or Sponsored Brands**. **Never call Sophie Hub, the Amazon Ads MCP, Keepa, or any connector to source this skill's data.** If a connector is open in the session, ignore it for this skill. *(This N/A is strictly about SOURCING the input data — it stays manual-upload only. It does NOT forbid the optional OUTPUT write-back in "Push live to Amazon via Sophie Hub" below, which applies changes the operator has already reviewed and approved in the dashboard, and only when they explicitly ask.)*

     **Why — verified, do not re-litigate this.** Two independent reasons:
     1. **There is no bulk-operations endpoint.** The Amazon Ads MCP exposes ~76 tools (account management, campaign management, reporting v3, AMC, billing). None of them exports or snapshots a bulk file.
     2. **The report data that exists cannot feed the engine — and this bites hardest on Sponsored Brands.** `report-v3-sb-targeting` carries exactly `date, cost, targetingId, matchType, campaignId, clicks, impressions, campaignName, adGroupId`. **No sales, no orders, no keyword text** — just a numeric target id. `query_ppc view=sb_video` reports SB conversions at campaign grain only and returns `sales: 0` per target. The engine's core formula is `Target CPC = RPC × Target ACOS` where `RPC = sales ÷ clicks` **per target**, so an SB feed with no per-target sales cannot produce a bid. `query_ppc view=placements` is SP-only, so SB placement data is not available there either.

     **Per-keyword Sponsored Brands sales exist in exactly one place: the bulk export.** That is why the upload is not a convenience — it is the only source.
   - **Manual — AVAILABLE (this is the only real path).** You (the user) download **one** bulk xlsx from the Amazon Ads console and upload it here. That single file carries **both** Sponsored Products and Sponsored Brands — see the "You provide" list in §4. This is how every run works.
   - **Hybrid — N/A.** With no MCP half, there is no hybrid.
2. **Hard rules:** Do not source any data from a mode marked N/A. Do not open, validate, or score any file, and do not run any §5 step, until the user has (a) picked a **strategy** from the full menu (Phase 0), (b) told you **which ad products** to score and, if Sponsored Brands is included, whether SB **matches the SP parameters or uses its own**, and (c) uploaded the **correct bulk xlsx for the strategy's window**. Never say "proceed without asking."
3. **First action is always Phase 0** in §5 — the intro line plus the full five-strategy menu WITH explanations — even if a file is already attached (acknowledge it, hold it, still show the menu first). Only after the user picks a strategy do you open and validate the file.

# SP & SB Bulk Bid Optimizer — deterministic multi-strategy Sponsored Products + Sponsored Brands (SBV) bid update from ONE uploaded bulk

## §1 Overview
Runs the Sophie Society bidding method on an uploaded Amazon Ads **bulk export** covering **both Sponsored Products and Sponsored Brands (including SBV)** and produces one Sophie-Society-branded **HTML approval dashboard** (tabs: SP Bids, SP Pauses, SP Placements, Budgets, SP Negations, SB Bids, SB Pauses, SB Placements, SB Negations) with in-browser forward + reverse **.xlsx** download buttons, plus an optional annotated review xlsx. Five selectable strategies (Profit-First, Balanced, Launch, Ranking Push, ACOS-Targeted-but-CPC-Managed) set the engine's dials; a deterministic Python scorer is the only source of truth for bid math (same inputs produce the same output). **This skill runs ONE way — Manual (upload + local compute). MCP and Hybrid are N/A: it has no live-data connector.**

- **`output.format: html`** (the approval dashboard is the primary artifact; the forward/reverse **xlsx** are secondary, generated client-side in-browser and/or by `apply_changes_v3.py`).

**One file, one run, one dashboard.** SP and SB come out of the same workbook. The approved xlsx carries **two sheets** — `Sponsored Products Campaigns` and the SB sheet — because Amazon's Bulk UI reads each ad product from its own sheet. SP rows never appear on the SB sheet and vice versa; each sheet mirrors its own header row from the uploaded file, since the two templates differ in both column names and column count.

**Three things about Sponsored Brands that are not true of Sponsored Products:**

1. **SBV is not a separate sheet.** It is a *filter* on the SB sheet. Video campaigns are the rows where `Ad Format` is video **or** `Video Asset IDs` / `Video Media IDs` is populated; Product Collection and Store Spotlight share the same sheet. Keyword and targeting rows inherit the format from their parent campaign.
2. **Every SB row is scored against its OWN ad format.** Video is benchmarked on video RPC, Product Collection on Product Collection RPC. Blending them is the obvious mistake here — a video keyword judged against Product Collection's conversion rate gets a wrong bid and, worse, a wrong pause. The dashboard prints the per-format benchmark table as the evidence.
3. **SB pauses more patiently than SP** (`SB_PAUSE_PATIENCE = 1.5`). SB keywords are fewer, dearer and often brand-defensive, and video has a longer path to purchase. A zero-order SB keyword needs 1.5× the clicks an SP keyword would before a pause is proposed.

| Stage | MCP | Manual | Hybrid |
|-------|-----|--------|--------|
| Acquire bulk export (SP **and** SB) | N/A (no connector — see RUN GATE) | **Yes** — user downloads one bulk xlsx from Amazon Ads console and uploads | N/A |
| Score bids (Python) | N/A | **Yes** — local `python` scorer, both products | N/A |
| Render dashboard + build 2-sheet xlsx | N/A | **Yes** — local Python + client-side JS | N/A |

## §2 Dependencies
| Kind | Name | Pinned version | Per-OS fallback |
|------|------|----------------|-----------------|
| MCP  | none | — | **N/A by design** — never call a connector for this skill |
| Runtime | python3 | 3.9+ | preinstalled on macOS/Linux; Windows: python.org |
| Lib  | openpyxl | 3.1.x | `pip install openpyxl==3.1.5` (reads the uploaded bulk; write-only build of the upload/review xlsx) |
| Runtime | modern browser | — | dashboard is self-contained HTML; opens in any browser |

## §3 Preflight & mode select  *(ask up front, required)*
1. Optionally run `python3 scripts/sophie_skill.py probe` to confirm OS, python, openpyxl.
2. **MCP check:** none required — this skill has no connector. Do not probe or call one.
3. Present the modes (per the RUN GATE): **MCP N/A**, **Manual = the only path**, **Hybrid N/A**.
4. Proceed to §5 Phase 0. Record strategy + mode (+ cpc_managed sub-mode) + window in the run manifest.

## §4 Inputs
| Input | Type | Required | Default | If missing |
|-------|------|----------|---------|-----------|
| Ad products | sp / sb / both | yes | — | ask (Phase 0 step 2) |
| Strategy | one of the 5 | yes | — | ask (show full menu with explanations first) |
| cpc_managed sub-mode | daily/weekly/monthly | only if strategy = ACOS-Targeted-CPC-Managed | daily | ask |
| Bulk export | .xlsx | yes | — | ask; tell user exactly what to download (window per strategy) |
| Yesterday bulk export | .xlsx | only if cpc_managed **daily** | — | ask (1-day export for the budget check) |
| Target ACOS | number (%) | yes | — | ask; do NOT anchor with example ranges |
| Min CPC | number | yes | — | ask; do NOT anchor |
| Max CPC | number | yes | — | ask; do NOT anchor |
| Brand terms | comma list or "none" | yes | none | ask |
| Currency symbol | text | no | `$` | ask (Phase 2 step 7b); display only, no maths depends on it |
| Low-data tab | yes / no | no | yes | ask (Phase 2 step 8a); presentational only, no maths depends on it |
| Keyword research file | `.xlsx` / `.csv` / `.txt` | no | none | ask (Phase 2 step 8b); drives the strategic-keep flag on the Negations tabs only |
| **SB matches SP?** | yes / no | only if SB included | — | **ask once** (Phase 2 step 8) |
| SB target ACOS | number (%) | only if SB differs | matches SP | ask; do NOT anchor |
| SB Min CPC | number | only if SB differs | matches SP | ask; do NOT anchor |
| SB Max CPC | number | only if SB differs | matches SP | ask; do NOT anchor |
| SB brand terms | comma list or "none" | only if SB differs | matches SP | ask |
| SB strategy | one of the 5 | only if SB differs | matches SP | ask (offer the same menu) |
| SB ad formats | comma list | only if SB included | all present | ask only if they want to narrow it |

Validate before any work. Fail fast: "I need <X>". If zero enabled keyword/target rows parse for the requested products, stop and warn the file looks like an unexpected format. If SB was requested but no SB rows are present, say so plainly and name the three checkboxes they need to re-tick — do not silently return an SP-only run.

### Manual-mode inputs — "You provide"  *(this IS the run; there is no MCP equivalent)*
| Input | Format | Where/how to get it | Required |
|-------|--------|---------------------|----------|
| Bulk export (SP **and** SB in ONE file) | .xlsx | advertising.amazon.com → **Campaign Manager → Bulk operations → Download campaigns**. Set *Date range for performance metrics* to the strategy's window; targeting filter = Enabled + Paused. **Check:** Sponsored Products data, Placement data for campaigns, Sponsored Products search term data — **plus, when Sponsored Brands is included: Sponsored Brands data, Sponsored Brands multi-ad group data, Sponsored Brands search term data.** **Leave unchecked:** terminated campaigns, zero-impression items, Sponsored Display data, Budget Rules. Download, then upload the .xlsx here. | yes |
| Yesterday bulk export | .xlsx | Same path, *Date range* = **Yesterday** (1 day). Only for cpc_managed **daily** (budget check). | conditional |
| Target ACOS / Min CPC / Max CPC | numbers | Your own targets — the skill will not suggest ranges (no anchoring). | yes |
| Currency symbol | text | The symbol your account bills in (£, €, $, ¥ …). Labels the dashboard only. | no |
| Keyword research file | .xlsx / .csv / .txt | Any keyword list — a Sophie KW research export, a Cerebro export, or a single column of keywords. Only used to protect researched terms from negation. | no |
| Brand terms | text | Your brand name + variations, comma separated, or "none". | yes |
| Window by strategy | — | Profit-First 30d; Balanced 30d (14d if very high volume); Launch 7d; Ranking 7-14d; cpc_managed daily = one 14-30d file + one Yesterday file; cpc_managed weekly/monthly 30d. | yes |

## §6 Fallback rules
- **No MCP to fall back from or to** — if a connector is connected in the session, ignore it; never fetch this skill's data from it.
- **Wrong window uploaded** → say the detected date range does not match the strategy; offer to re-download or switch strategy. Do not score a mismatched file silently.
- **Zero enabled rows / unexpected format** → stop, warn, ask for a correct export (do not emit a half-file).
- **cpc_managed daily missing the Yesterday file** → budget check is skipped; tell the user and proceed with bid cuts only, or ask for the second file.
- **openpyxl missing at run time** → `pip install openpyxl==3.1.5`, else stop cleanly.

## §7 Output contract  (`output.format: html`)
Primary artifact = the self-contained HTML approval dashboard. Secondary = forward/reverse .xlsx (client-side JS in the dashboard, and/or `apply_changes_v3.py` via openpyxl write-only).
- **Self-contained HTML:** inline CSS/JS, no CDN/external fetch (already satisfied — the report generator inlines everything).
- **Live artifact / snapshot:** ships as an **interactive SNAPSHOT** (`refreshable:false`). This is an **upload / local-compute** skill with **no MCP data source**, so it cannot self-refresh in Cowork — that is honest, not a gap. The dashboard is already fully interactive client-side.
- **xlsx secondary contract:** built with openpyxl write-only (`Workbook(write_only=True)`), fresh workbook (never mutate Amazon's template), one sheet per ad product (`Sponsored Products Campaigns` and, when Sponsored Brands ran, the SB sheet), each mirroring its OWN header row from the uploaded file, ID columns forced to text. A sheet with no rows is omitted rather than written empty. No volatile functions. If byte-identical xlsx is required, pin the clock in `docProps/core.xml` and run `sophie_skill.py normalize --ts <ts>` as a post-step.
- **Embed the run manifest** (strategy, sub-mode, window days, Target ACOS, Min/Max CPC, brand terms, input filename, `SOPHIE_RUN_TS`).
- Finish with the delivery card (`sophie_skill.py card`) → clickable `file://` link to the dashboard and to the Downloads xlsx.

**Determinism flags (author attention):**
- ⚠️ **Clock leak (pinned by harden):** `render_report.py` read `datetime.datetime.now().strftime(...)` for the report timestamp — hardened to honor `SOPHIE_RUN_TS`. Run with `SOPHIE_RUN_TS=<manifest ts>` for reproducible output.
- ✅ **Client-side JS clock leak — FIXED in v3.** The page now receives `RUN_TS` / `RUN_DATE` as data-as-props from `SOPHIE_RUN_TS`, and every in-browser filename plus the approved-JSON `generated_at` uses them. There are zero `new Date()` calls left in the body JS, so two operators downloading the same run get identical filenames regardless of browser timezone.
- ⚠️ **Unembedded fonts:** the dashboard uses `BROmega → BR Omega → Inter → DM Sans → system-ui`. None are embedded (no `@font-face` with a bundled/base64 file), so glyphs fall back to whatever the viewer has. Embed BROmega/Inter as base64 in `assets/` for pixel-stable rendering.
- ✅ No CDN/external fetch; no `toLocaleString`/`Intl` locale leak found.

## §8 Gates
- No credit-spend and no outward action (no Slack/Notion/email/publish, no MCP) — nothing to gate on cost.
- **Human-review gate (mandatory, from the original):** the dashboard proposes changes; the user must open each tab, untick anything unwanted, and download the **Summary-tab** approved .xlsx. Always deliver the "how to use the dashboard" numbered message and the bid-reality-check note. Never imply the output is safe to upload unreviewed. The **review_annotated** xlsx is read-only — never upload it to Amazon.

## §5 Run procedure — original skill logic (verbatim, authoritative)

# SP & SB Bulk Bid Optimizer — run procedure

Produce a deterministic, RPC-based bid update for an Amazon Ads bulk export using the **Sophie Society bidding method**. Output is a Sophie-Society-branded HTML approval dashboard with forward + reverse **xlsx** download buttons (Amazon Ads Bulk UI accepts .xlsx only), plus an optional annotated review xlsx with highlighted rows + cell comments.

**Critical determinism rule:** the Python scoring script is the only source of truth for bid math. You (Claude) handle the conversation and render the HTML. You never compute bids yourself. Same inputs must always produce byte-identical outputs.

## How the method works

The optimizer answers one question per keyword or target: how much is a click actually worth here. It sets the bid to that value, bounded by safety rails, and a chosen strategy decides how aggressive to be. The scoring is deterministic: a Python script is the only source of truth for the math, the same inputs always produce the same output, and Claude never computes a bid.

### The engine (shared by every strategy)

1. Revenue Per Click (RPC) is total sales divided by total clicks in the window. The core formula is Target CPC = RPC x Target ACOS. If a click brings in 2.40 of sales and the target ACOS is 30 percent, the most you should pay for that click is 0.72.
2. Confidence tiers pick the formula by data quality. High (at least 10 clicks and at least 1 order) uses the RPC formula. Medium (3 to 9 clicks, or 10 or more with zero orders) uses RPC if there are orders, otherwise a CPA projection that ratchets the bid down with every non-converting click. Low (fewer than 3 clicks) takes only a small step toward the ad group RPC.
2b. Low-data targets are never bid down either. A target with fewer clicks than the strategy's medium tier (3 on every current strategy) is treated like a zero-click one: never cut, stepped up toward the ad group's click value where the strategy's zero_click dial says raise, held where it says hold. One or two clicks is not evidence; the target has spent almost nothing, and a cut mostly delays the click that would settle the question. These rows are badged Low data and, unless the operator declines, given their own dashboard tab so a firm decision and a coin-flip are never in the same list.
2a. Zero-click targets are never bid down, under any strategy. A target that has never been clicked has spent nothing, so cutting it saves nothing and only makes a click - the one thing that would produce evidence - less likely. What happens instead is set by the strategy's zero_click dial: Balanced, Launch and Ranking Push step the bid up toward what a click is worth at the ad group's revenue per click and stop there (a target already at or above that value is left alone), while Profit-First and CPC-Managed hold the bid where it is rather than spend more on an unproven target. This applies to Sponsored Products and Sponsored Brands alike, each following its own strategy's dial.
3. The grace band leaves a converting keyword alone when its ACOS is already within the strategy's band of target. This is the main anti-churn rule.
4. The visibility floor protects converting keywords from being starved. The max potential bid (the base bid times one plus the campaign's top placement modifier) must stay at or above 75 percent of a reference CPC. The reference CPC is the keyword's own recent CPC when the window is 14 days or longer, and the account average CPC on shorter windows. Min CPC is the hard floor underneath.
5. Clamps run last, in order: an asymmetric max-change cap (separate up and down limits per strategy), the Min CPC floor (flagged, not silently cut), and the Max CPC ceiling. The max-change cap runs after the visibility floor on purpose, so it is a real per-run guarantee: a starved keyword still climbs back to its floor, at the strategy's step size, over successive runs rather than in one jump. Then round, and drop any row whose bid did not change.
6. The pause rule targets waste. A target with zero orders is paused when its clicks reach the strategy multiplier times the clicks the account normally needs for one order, computed separately for branded and non-branded terms and adjusted by match type (exact 1.0, phrase 1.3, broad and auto 1.6). A target with at least one order is never auto-paused. If there is not enough order data to compute the threshold (fewer than 10 orders in the segment and fewer than 20 in the account), it does not pause.
7. Branded protection: when brand terms are given, branded keywords may step down but never up, and branded search terms are never suggested for negation.
8. Placement modifiers are tuned separately from bids, using Revenue Per Click per placement relative to the campaign. Increases are capped per strategy (5 points on Profit-First, 15 on Balanced and Launch, 25 on Ranking Push but only on Top of Search), decreases may move up to 50 points. A placement sitting at 0 percent can be raised, which creates a modifier the campaign did not have, so those rows are badged in the dashboard and named in the run notes. The Amazon Business placement is left untouched.
9. Negations are advisory only. A customer search term is flagged when it has zero orders and its clicks reach the account clicks-to-order number, or when it has zero orders and its CPC is at least twice the account average. Branded terms and terms identical to the keyword are never flagged.
9a. The strategic-keyword safety flag. When a keyword research file is supplied, a term that met the negation rule but exactly matches a keyword the operator researched is re-labelled "Don't negate - strategic. Raise bid or move to own campaign.", sorted to the top of the Negations tab, badged, and left unticked. The reasoning is that such a term is not waste but a term they deliberately targeted which has not converted yet, and negating it throws the research away. Matching is exact string, case-insensitive, the same rule kw-harvester-negator uses, so the two skills agree on what counts as strategic. It applies to Sponsored Products and Sponsored Brands alike and affects nothing but the Negations tabs.
10. Auto-targeting is optimized like any other target. If an auto clause has no explicit bid, an explicit bid is proposed from the formula rather than changing the ad group default.

### The five strategies

A strategy is a saved set of the engine's dials. Balanced is the original behavior; the others change the dials, not the engine.

- Profit-First. Protects margin on a fixed footprint. Tight grace band, cut-biased clamps (up 10 percent, down 25 percent), prompt pausing, splits below-min rows, and cut-biased placements too - it will trim a weak placement at the full 50-point cap but raise a strong one by at most 5 points per run. The ACOS goal you enter is treated as break-even and the optimizer aims at or below it.
- Balanced. The default and the original behavior. Symmetric 15 percent clamps, 10 percent grace band, standard pausing, floors below-min rows.
- Launch / New Product. Buys data and visibility. Wider grace band, larger steps, patient pausing, keeps below-min rows. The ACOS goal is allowed to run about 1.5 times higher while the product gathers data.
- Ranking Push. Wins or holds top of search for a chosen set of terms, time-boxed. Up-biased clamps, patient pausing, and a larger placement increase cap that applies to Top of Search only - every other placement stays on the standard cap, so the strategy pushes the placement it names rather than bidding everything up. It leans on top-of-search impression share, which is not in the bulk export, so for now its placement push is moderate.
- ACOS-Targeted but CPC-Managed . A profitability strategy that scales volume through budget while grinding cost-per-click down. It runs in one of three modes per run and never changes bids and placements in the same run. Daily: raise the budget of any campaign that spent its full budget yesterday (plus 10, never decreased) and trim bids; needs a second one-day export for the budget check. Weekly: tune placements with the test ladder (0, 31, 51, 81, 101 percent; halve on a drop). Monthly: reallocate budget toward higher-ROAS campaigns, holding the account total roughly constant.

### What it does not do

It does not pull live data; every input is an uploaded report. It does not run automatically; every change is reviewed in the dashboard before the file is built. It covers Sponsored Products and Sponsored Brands (including SBV); it does not cover Sponsored Display.

## Trigger

Activate when the user asks to optimize, recompute, or adjust Sponsored Products bids, with or without a file. ALWAYS begin with Phase 0 below (the intro plus the full strategy menu with explanations), even if the user has ALREADY uploaded a bulk file. If a file is already attached, acknowledge it, set it aside, and still show the strategy menu first; only after they pick a strategy do you open and validate the file. Never skip the intro and never ask the user to choose a strategy before showing all five strategies with their explanations. Do not activate for pure audits or harvest-only requests.

## Conversation flow (strict order)

Write for someone new to Claude and to Amazon. No emojis, no em-dashes, no filler. State what each input controls in plain words, then ask one thing at a time. Do NOT offer benchmark, typical, or example ranges for Target ACOS, Min CPC, or Max CPC: these vary widely by product and category, so let the user supply their own number and do not anchor them. Do not run any calculation until you have the strategy, the mode if relevant, and the correct uploaded file for the right window. ALWAYS open with the intro message and the full strategy menu in Phase 0 step 1, including every strategy's explanation and best-for, BEFORE asking the user to choose, even if a file is already uploaded. Never present a bare list of strategy names without the explanations.

### Phase 0: pick the strategy and get the right report (runs even with no file yet)

1. ALWAYS start here, even if the user already uploaded a file (acknowledge the file, hold it, and still show this first). Open with a short intro line, then present ALL five strategies below, each with its explanation and best-for, then ask which one fits their goal. Never show only the names. Use wording like: "Before we optimize, here are the five strategies, pick the one that fits your goal:" followed by the five with their explanations:
   - Profit-First. Protects profit; trims expensive keywords, raises cautiously. Best for established products where profit matters more than growth, or tight budgets.
   - Balanced (the standard). Sets each bid to what a click is worth at your target ACOS; steady. Best for most products you want to grow sustainably.
   - ACOS-Targeted but CPC-Managed. Scales sales by feeding budget to winners while lowering cost-per-click. Best for scaling without letting ACOS rise. Runs in three modes.
   - Launch / New Product. Bids a bit bolder to gain visibility and data, and is patient. Best for products in their first 8 weeks.
   - Ranking Push. Pushes top of search for chosen keywords for a limited time. Best for climbing or defending rank.

2. **Ask which ad products to optimize.** Ask this right after the strategy, before the download instructions, because the answer changes which boxes they tick in Amazon. Wording:
   "Which do you want to optimize? It is the same download either way, so including both costs you nothing extra."
   - Sponsored Products only.
   - Sponsored Brands only (this includes SBV, Sponsored Brands Video).
   - Both, in one dashboard. (This is the usual answer.)

   If they say Sponsored Brands or Both, add one plain line so they know what they are getting: "Sponsored Brands covers Video, Product Collection and Store Spotlight. I score each format against its own numbers rather than lumping them together, so a video keyword is never judged by how Product Collection converts."

3. If they pick ACOS-Targeted but CPC-Managed, ask which mode.
   - Daily: budget and bid cuts. Run most days.
   - Weekly: placement tuning. Run about weekly. Do not run on the same day as bids.
   - Monthly: budget reallocation. Run about monthly.

4. Tell them exactly what to download from Amazon. **One file covers both products.**
   - Open advertising.amazon.com, go to Campaign Manager, then Bulk operations, then click Download campaigns.
   - In the Download campaigns window: set Date range for performance metrics to the window for their strategy (below); set the targeting filter to Enabled and Paused.
   - Check, always: Sponsored Products data, Placement data for campaigns, Sponsored Products search term data.
   - **Check as well, whenever Sponsored Brands is included: Sponsored Brands data, Sponsored Brands multi-ad group data, Sponsored Brands search term data.** These are the three boxes that carry Sponsored Brands, and SBV lives inside them. Without them there is no SB data at all — the Amazon Ads API cannot supply it (see the RUN GATE).
   - Leave unchecked: Terminated campaigns, Campaign items with zero impressions, Sponsored Display data, Budget Rules Data. (If they are running SP only, also leave the three Sponsored Brands boxes unchecked.)
   - Click Download, then upload the xlsx here.
   - Date range by strategy: Profit-First 30 days; Balanced 30 days (14 if very high volume); Launch 7 days; Ranking 7 to 14 days; CPC-Managed daily needs two files, one of 14 to 30 days for bids and one set to Yesterday for the budget check; CPC-Managed weekly and monthly 30 days. The window applies to both products — one date range, one file.

### Phase 1: open and validate

5. Open the file. Echo the counts and the detected date range.
   - For Sponsored Products: enabled campaigns, keywords, product targets, placement rows.
   - **For Sponsored Brands, report the split by ad format** — how many enabled targets are Video (SBV), Product Collection and Store Spotlight, and which SB sheet they came from (`SB Multi Ad Group Campaigns` or `Sponsored Brands Campaigns`). This tells the user immediately whether their SBV campaigns actually made it into the file.
   - If the window does not match the chosen strategy, say so and offer to re-download or switch strategy.
   - If zero enabled keyword or target rows are found for the requested products, stop and warn that the file looks like an unexpected format.
   - **If SB was requested but the SB sheet is missing or empty, stop and say exactly which three boxes to re-tick** (Sponsored Brands data, Sponsored Brands multi-ad group data, Sponsored Brands search term data), then ask for a fresh download. Do not quietly continue as an SP-only run.
   - If the SB sheet is there but the SB search term sheet is not, say so: SB bids and pauses still run, SB negations are skipped.

### Phase 2: confirm the few inputs the strategy needs

6. Target ACOS. The share of sales you will spend on ads. For Launch, say plainly that this is your normal target and Launch will run about 1.5 times higher while gathering data.
7. Min CPC and Max CPC. The floor and ceiling for any bid. Min CPC keeps you in the auction; Max CPC catches runaway bids.
7b. Currency. Which currency is this account billed in? Ask plainly, offer the marketplace's usual symbol as the obvious answer, and say what it does: it only changes how money is labelled in the dashboard and in the exported CSVs. No bid maths depends on it, and the reader already strips currency symbols out of the uploaded file. Ask this on every run — an account on amazon.co.uk or amazon.de whose dashboard says $ is the kind of thing that gets a client report sent back.
8. Brand terms. Your brand name and variations, comma separated, or none. Branded keywords are protected from bid-ups and from negation.
8a. Low-data tab. Ask: "Some targets will have fewer clicks than the strategy needs to make a confident call. Do you want those on their own tab, separate from the ones with enough data to decide on? Most people say yes." Default yes. Explain what it does NOT do: the split is presentational, the bid maths is identical either way, and low-data targets are never bid down regardless. Pass `--low-data-tab no` if they want everything in one list.
8b. Keyword research file (optional). Ask: "Do you have a keyword research file for this product? If you upload one, any search term I would have flagged for negation that matches a keyword you researched gets marked a strategic keep instead — it sorts to the top of the Negations tab, starts unticked, and tells you to raise the bid or move it to its own campaign rather than negate it." Accept .xlsx, .csv or .txt. Say plainly what it does NOT do: it never touches bids, pauses, placements or budgets — Negations only. If they have no file, say that is fine and move on; the rest of the run is unchanged.
   The other dials (grace band, tier patience, step size, max change, pause multiplier, below-min policy, placement caps) come from the chosen strategy and are not asked.

#### Phase 2b: Sponsored Brands parameters — ask once, then only if they differ

**Skip this whole section if the user chose Sponsored Products only.**

9. Ask the single gate question:
   "Should Sponsored Brands use the same settings as Sponsored Products, or its own?"
   - **Same as Sponsored Products.** Reuse the target ACOS, Min CPC, Max CPC, brand terms and strategy already given. Say "Using your Sponsored Products settings for Sponsored Brands too" and move on. **Ask nothing further.**
   - **Different.** Then ask the same questions again, in the same order and the same plain words, labelled for Sponsored Brands. Ask one at a time, and **do not anchor** — no benchmark, typical or example ranges, exactly as for SP:
     - SB Target ACOS. The share of Sponsored Brands sales you will spend on Sponsored Brands ads.
     - SB Min CPC and SB Max CPC. The floor and ceiling for any Sponsored Brands bid.
     - SB brand terms. Usually the same list; ask anyway, and offer "same as before" as an easy answer.
     - SB strategy. Offer the same five-strategy menu with the same explanations. Most people keep the SP strategy; only re-show the full menu if they want to change it.

   Two things worth saying plainly when they choose "different", because they are the usual reasons someone would:
   - Sponsored Brands often runs at a higher target ACOS than Sponsored Products, because it buys brand-new-to-brand traffic rather than bottom-of-funnel clicks. That is a judgement for the user, not a number this skill supplies.
   - Sponsored Brands CPCs are usually higher, so an SP Max CPC can clamp almost every SB bid at the ceiling. If their SB Max CPC ends up below their SB average CPC, say so before scoring rather than after.

10. Ad formats. Only ask if they want to narrow the run: "I will score Video, Product Collection and Store Spotlight. Want me to limit it to just one?" Default is everything present in the file. Whatever is present but not scored is named in the dashboard, so nothing is silently dropped.

### Phase 3: score and approve

11. Run the scoring script once, with `--products sp|sb|both`, the strategy, the mode if relevant, the window in days, and the inputs above (and the yesterday file for the daily mode). **Pass an `--sb-*` argument only for a dial the user actually changed** — every omitted `--sb-*` flag means "match Sponsored Products", which is exactly the semantics of the Phase 2b gate question. Show the summary counts, and when SB ran, show the per-ad-format line (Video / Product Collection / Store Spotlight) so the split is visible before they open anything.
12. Render the dashboard (it opens in the browser and is saved to Downloads). Then ALWAYS give the user a short, plain how-to message in chat, in these words or very close:
    - "Here is how to use the dashboard:"
    - "1. Open every tab once. That unlocks the download button."
    - "2. Untick any change you do not want, and edit a bid in place if needed. Select-all and the All / None / Invert buttons only affect the tab you are on."
    - "2a. Tabs with an orange dot have not been reviewed yet. Sort or filter any table to work through it (confidence first is a good start) - that only changes what you see, never what gets exported. If you need a break, Save review plan writes your ticks and edits to a file you can load back."
    - "3. On the first tab (Summary), click Download approved xlsx. That is your upload file."
    - "4. Upload that .xlsx in Amazon Ads, Bulk operations. Download reverse xlsx is only for undoing a run."
    - "Or, to have me apply it for you: click Download approved changes (.json), then send it back and say push. I'll push the Sponsored Products bids and placements straight to the account via Sophie Hub."
    - "The green Export this tab as CSV buttons are optional, audit-only views of one tab. Do not upload a CSV; Amazon needs the .xlsx from the Summary tab."
    When Sponsored Brands ran, add these two lines:
    - "One file covers both. The approved xlsx has a Sponsored Products sheet and a Sponsored Brands sheet — upload it once, Amazon reads both."
    - "The push route covers both too — Sponsored Products and Sponsored Brands bids and placements. Pauses and budget changes always go through the upload."
13. After the run, show this note, and never imply the output is safe to upload unreviewed:
    - Human review is essential. This tool proposes changes, it does not replace your judgment. Review every tab and untick anything that does not fit before you download. Do not blindly upload.
    - Bid reality check: these bids come from what a click is worth, the tool does not know each keyword's competitive CPC or top-of-search share, so look closely at large cuts on high-visibility, branded, or ranking terms and at any Min-CPC floor hits.
    - When Sponsored Brands ran, add: Sponsored Brands bids move real brand visibility, and a video keyword that looks expensive per click may be doing upper-funnel work this file cannot see. Look hardest at cuts on branded and defensive SB terms.
    - When any SB placement row came back advisory, add: some Sponsored Brands placement labels were not ones this skill has confirmed, so they are shown for your judgement and left out of the upload file on purpose.
14. **Optional — push live to Amazon via Sophie Hub.** Only when the operator explicitly asks (e.g. "push these", "apply to the account") and has handed back an **approved_changes.json** exported from the dashboard: follow **Push live to Amazon via Sophie Hub** below. The saved JSON already encodes exactly what they ticked and edited — including placements — so **never re-ask about placements**; one confirmation covers the whole push. The write is allowlist-gated and falls back to the xlsx route if the account isn't cleared. This is opt-in — never push without an explicit request. (This is the ONLY sanctioned Sophie Hub call in this skill, and it is OUTPUT/write-back, not data sourcing — the RUN GATE's "no MCP" rule is about input only.)
    - **Scope: bids and placements, both ad products.** The JSON carries `push_scope: "sponsored_products_and_brands"`, with Sponsored Brands on its own `sb_target_bids` / `sb_placement_changes` payloads. **Pauses and budget changes are never pushed, for either product** — they go via the xlsx. Every SB row is pre-flighted against the live account before any write; see the push section.

## Algorithm (config-driven)

The Python scorer is the source of truth. Strategy presets live in the STRATEGIES table at the top of the script; do not tune them in conversation. Per-run inputs (strategy, mode, target ACOS, Min CPC, Max CPC, brand terms, window days) are passed as arguments.

Per-strategy dials (grace_band, clicks_high, clicks_med_min, step_size, max_change_up, max_change_down, below_min, pause_multiplier, target_acos_mult, placement_mode, zero_click):
- profit_first: 0.05, 10, 3, 0.075, up 0.10, down 0.25, split, pause 1.0, acos x1.0, trim (placement +5pp up / -50pp down), zero_click HOLD
- balanced: 0.10, 10, 3, 0.10, up 0.15, down 0.15, floor, pause 1.0, acos x1.0, rpc (placement +15pp up / -50pp down), zero_click RAISE
- launch: 0.15, 15, 3, 0.15, up 0.25, down 0.20, keep, pause 1.5, acos x1.5, rpc (placement +15pp up / -50pp down), zero_click RAISE
- ranking: 0.15, 12, 3, 0.15, up 0.30, down 0.10, keep, pause 1.25, acos x1.0, tos (placement +25pp up on Top of Search only, +15pp elsewhere / -50pp down), zero_click RAISE
- cpc_managed (ACOS-Targeted, CPC-Managed): 0.10, 10, 3, 0.10, up 0.20, down 0.20, keep, pause 1.0, acos x1.0, ladder, zero_click HOLD

**The `zero_click` dial.** No strategy ever bids a zero-click target DOWN -- a target that has never been clicked has spent nothing, so a cut saves nothing and only makes a click less likely. What differs is what happens instead:
- `raise` (Balanced, Launch, Ranking Push): step the bid up toward what a click is worth at the ad group's RPC, capped at that value. Buys a chance at evidence without ever overpaying for it.
- `hold` (Profit-First, CPC-Managed): leave the bid exactly where it is. Both strategies exist to protect margin or to drive CPC down, and neither is served by spending more on a target that has yet to prove anything.

Fixed constants: visibility floor 75 percent of reference CPC against max potential bid, applied before the max-change clamp so the per-run cap is never exceeded; placement increase cap 15 points by default, 5 on Profit-First, 25 on Ranking Push for Top of Search only, decrease cap 50 points, minimum 30 clicks per placement; pause data gates 10 orders per segment and 20 per account; match-type factors exact 1.0, phrase 1.3, broad and auto 1.6; negation at clicks-to-order or 2 times average CPC; Amazon Business placement excluded; CPC-Managed budget bump plus 10 with a 2x cap.

The reader is case-insensitive on column names and on Entity and Placement values, so current Amazon exports (sentence case) and older exports (Title case) both parse. Each output sheet mirrors its own uploaded sheet's exact header row.

### Sponsored Brands: what changes and what does not

**The engine does not change.** `decide_bid()` is product-agnostic — same formula, same confidence tiers, same grace band, same clamps, same visibility floor, same branded gate. Four things around it change:

1. **Which benchmarks it is handed.** SB rows are bucketed by ad format and each bucket gets its own `account_metrics()` and ad-group RPC map. A Video keyword's low-data step moves toward *video* RPC and its pause threshold comes from *video* clicks-to-order. This is the single most important SB behaviour, and it is not cosmetic: on the reference fixture, pooling the formats flips a keyword from a bid cut to a pause.
2. **Which parameters it uses.** Target ACOS, Min CPC, Max CPC, brand terms and strategy are taken from the `--sb-*` arguments where given, and from the SP values where not. Omitting a flag *is* the "match SP" answer.
3. **Pause patience.** `SB_PAUSE_PATIENCE = 1.5` multiplies the strategy's `pause_multiplier` for SB rows only, so SB needs 1.5× the zero-order clicks SP would before a pause is proposed. Everything else about pausing is unchanged: one order still protects a target, and the data gates (10 orders in the segment, 20 in the account) still apply — which on a small SB account usually means no pause at all, correctly.
4. **Placement gating, and signed percentages.** SB placement labels are not identical to SP's. A bidding-adjustment row whose label resolves through `sb_placement_enum()` to an Amazon enum is writable and pushable; anything else is emitted with `advisory: True`, shown in the dashboard greyed out, and **excluded from both the upload file and the push**. Separately, SB percentages are **signed** — SP can only bid a placement up, SB can bid one down — so the SB path does not floor the ideal at zero. Extend the mapping only after confirming a label against a real SB bulk. A wrong modifier on a live SB campaign is not worth a guess.

**Ad-format detection**, in priority order: a populated `Video Asset IDs` / `Video Media IDs` (strongest — only video campaigns carry one); then the `Ad Format` text; then the parent campaign's values, since keyword and targeting rows usually carry neither; then, last resort, the Sophie campaign-naming convention where video campaigns are tagged `SBV`. Anything still unresolved is bucketed `unknown` and scored against other unknowns rather than being guessed into a format.

**SB bids and placements ARE part of the live push**, on their own payloads and behind a mandatory pre-flight. See Phase 3 step 14 and the push section. SB pauses and budgets are not pushed — nor are SP's.

## Python scoring script

Save this to a temp file and run with `python`. Read the JSON it prints.

```python
# bulk_bid_optimizer_v3.py
# Multi-strategy Sophie Society bidding method. Deterministic: same inputs -> same output.
# Engine unchanged in spirit (Target CPC = RPC x Target ACOS, tiers, clamps, branded gate,
# RPC-relative placements, advisory negations). v2 added: case-insensitive reader + zero-row
# guard, per-strategy config presets, asymmetric max-change, segmented clicks-to-order pause,
# unified visibility floor (75% of reference CPC vs max potential bid), new negation rule,
# auto-targeting optimization, and the CPC-Managed (Felix) mechanism with 3 modes.
#
# v3 adds SPONSORED BRANDS (SB) from the SAME uploaded bulk workbook:
#   - reads the SB sheet ("SB Multi Ad Group Campaigns", falling back to
#     "Sponsored Brands Campaigns") and the SB search term sheet;
#   - splits every SB row by AD FORMAT (video / product_collection / store_spotlight) and
#     benchmarks each format against ITSELF, so SBV is never scored against Product
#     Collection RPC;
#   - runs SB with its OWN parameters (target ACOS / min CPC / max CPC / brand terms),
#     which may match SP or differ -- the caller passes them explicitly;
#   - is MORE PATIENT than SP on pauses (SB_PAUSE_PATIENCE), because SB keywords are
#     fewer, dearer and often brand-defensive;
#   - gates SB placement changes behind label recognition: an SB bidding-adjustment row
#     whose placement label does not resolve to an Amazon placement enum is emitted
#     ADVISORY-ONLY and never reaches the upload file or the live push.
# SB conversions exist per-keyword ONLY in this bulk export. The Amazon Ads API reports SB
# sales at campaign grain (report-v3-sb-targeting carries cost/clicks/impressions and a bare
# targetingId -- no sales, no keyword text), so there is no MCP path to this data. Do not
# add one.
import json, argparse
from decimal import Decimal, ROUND_HALF_EVEN
import openpyxl

# ---------------- strategy presets (the locked config) ----------------
STRATEGIES = {
    "profit_first": {
        "grace_band": 0.05, "clicks_high": 10, "clicks_med_min": 3, "step_size": 0.075,
        "max_change_up": 0.10, "max_change_down": 0.25, "below_min": "split",
        "pause_multiplier": 1.0, "target_acos_mult": 1.0, "placement_mode": "trim",
        "zero_click": "hold",
    },
    "balanced": {
        "grace_band": 0.10, "clicks_high": 10, "clicks_med_min": 3, "step_size": 0.10,
        "max_change_up": 0.15, "max_change_down": 0.15, "below_min": "floor",
        "pause_multiplier": 1.0, "target_acos_mult": 1.0, "placement_mode": "rpc",
        "zero_click": "raise",
    },
    "launch": {
        "grace_band": 0.15, "clicks_high": 15, "clicks_med_min": 3, "step_size": 0.15,
        "max_change_up": 0.25, "max_change_down": 0.20, "below_min": "keep",
        "pause_multiplier": 1.5, "target_acos_mult": 1.5, "placement_mode": "rpc",
        "zero_click": "raise",
    },
    "ranking": {
        "grace_band": 0.15, "clicks_high": 12, "clicks_med_min": 3, "step_size": 0.15,
        "max_change_up": 0.30, "max_change_down": 0.10, "below_min": "keep",
        "pause_multiplier": 1.25, "target_acos_mult": 1.0, "placement_mode": "tos",
        "zero_click": "raise",
    },
    "cpc_managed": {  # Felix
        "grace_band": 0.10, "clicks_high": 10, "clicks_med_min": 3, "step_size": 0.10,
        "max_change_up": 0.20, "max_change_down": 0.20, "below_min": "keep",
        "pause_multiplier": 1.0, "target_acos_mult": 1.0, "placement_mode": "ladder",
        "zero_click": "hold",
    },
}
FLOOR_PCT = 0.75              # max potential bid must stay >= 75% of reference CPC
PLACEMENT_MIN_CLICKS = 30
PLACEMENT_MAX_UP_PP = 15.0    # increases capped at 15 points/run (default)
PLACEMENT_MAX_DOWN_PP = 50.0  # decreases may move faster
# Per-mode increase caps. These are what make the placement dials mean something:
#   trim (Profit-First) raises grudgingly and cuts at the full down-cap;
#   tos  (Ranking Push)  raises TOP OF SEARCH harder and holds every other placement
#                        at the default, which is what "pushes top of search" has to mean;
#   rpc  (Balanced, Launch) uses the default both ways.
TRIM_MAX_UP_PP = 5.0          # Profit-First: cut-biased, barely raises
TOS_MAX_UP_PP = 25.0          # Ranking Push: top of search only
TOS_PLACEMENT = "placement top"
LADDER = [0, 31, 51, 81, 101]
SEG_MIN_ORDERS = 10           # segment clicks-to-order needs >=10 orders
ACCT_MIN_ORDERS = 20          # else account number needs >=20 orders, else do not pause
MATCH_FACTOR = {"exact": 1.0, "phrase": 1.3, "broad": 1.6, "auto": 1.6, "": 1.6}
EXCLUDE_PLACEMENT = {"placement amazon business"}  # do not optimize B2B placement

# ---------------- Sponsored Brands (v3) ----------------
SP_SHEET = "sponsored products campaigns"
# Newer multi-ad-group exports use the first name; it is often EMPTY on legacy accounts,
# so we try it, and fall through to the legacy sheet when it yields no leaf rows.
SB_SHEET_CANDIDATES = ["sb multi ad group campaigns", "sponsored brands campaigns"]
SB_ST_SHEET_CANDIDATES = ["sb search term report", "sponsored brands search term report",
                          "sb search terms", "sponsored brands search terms"]
SP_ST_SHEET = "sp search term report"

# SB pauses need MORE evidence than SP: SB keywords are fewer, dearer and often
# brand-defensive, and SBV in particular is an upper-funnel format with a longer path to
# purchase. This multiplies the chosen strategy's pause_multiplier for SB rows only.
SB_PAUSE_PATIENCE = 1.5

# Ad-format buckets. Every SB row is scored against its OWN format's benchmarks so that a
# video keyword is never compared with a Product Collection keyword's RPC.
SB_FORMAT_LABELS = {"video": "Video (SBV)", "product_collection": "Product Collection",
                    "store_spotlight": "Store Spotlight", "unknown": "Unclassified"}
SB_FORMAT_ORDER = ["video", "product_collection", "store_spotlight", "unknown"]

# SB placement labels -> Amazon Ads API enum.
# Verified live 2026-08-21 against campaign_management-query_campaign / update_campaign:
# the enum is HOME_PAGE | PRODUCT_PAGE | REST_OF_SEARCH | SITE_AMAZON_BUSINESS | TOP_OF_SEARCH.
# HOME_PAGE is the SB-specific one (Sponsored Products never serves there).
# A bulk label that resolves to an enum is WRITABLE and PUSHABLE; anything unresolved is
# emitted advisory-only, excluded from the upload file and from the push. Do not add a
# mapping on the strength of a guess -- a wrong modifier on a live campaign is not free.
SB_PLACEMENT_ENUMS = {"HOME_PAGE", "PRODUCT_PAGE", "REST_OF_SEARCH", "TOP_OF_SEARCH"}

def sb_placement_enum(label):
    """Map an SB bulk placement label to its API enum, or None if we cannot be sure.

    Order matters: 'home' is checked before 'page', because "Home Page" contains both and
    must not be mis-read as PRODUCT_PAGE.
    """
    k = str(label or "").strip().lower()
    if not k: return None
    if "business" in k: return None          # B2B placement is never optimized
    if "home" in k: return "HOME_PAGE"
    if "top" in k: return "TOP_OF_SEARCH"
    if "rest" in k or "other" in k: return "REST_OF_SEARCH"
    if "product" in k or "detail" in k: return "PRODUCT_PAGE"
    return None

# SB placement percentages are SIGNED integers -- verified live: a real campaign carried
# {"percentage": -10, "placement": "REST_OF_SEARCH"}. This is a genuine difference from
# Sponsored Products, whose modifiers are 0..900 and can only ever bid a placement UP.
# Being able to bid a weak SB placement DOWN is the more useful half of the feature.
# The bound below is deliberately conservative; the API rejects anything out of range and
# the push surfaces that rather than silently clipping.
SB_PLACEMENT_MIN_PP = -99
SB_PLACEMENT_MAX_PP = 99

def r2(x):
    return float(Decimal(str(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN))

def fnum(v, d=0.0):
    if v in (None, ""): return d
    try:
        if isinstance(v, str):
            v = v.replace(",", "").replace("$", "").replace("EUR", "").replace("€", "").replace("£", "").replace("%", "").strip()
            if not v: return d
        return float(v)
    except Exception:
        return d

# ---------------- case-insensitive reader (the shim) ----------------
def _read_sheet(wb, name):
    """Return (original_header_row, [normalized rows]) for one sheet, or (None, [])."""
    ws = wb[name]
    headers = [c.value for c in ws[1]]
    if not any(h is not None for h in headers):
        return None, []
    rows = []
    for r in ws.iter_rows(min_row=2):
        row = {(str(h).lower().strip() if h is not None else h): v
               for h, v in zip(headers, [x.value for x in r])}
        row["__sheet"] = name          # so the applier writes each row back to its own sheet
        rows.append(row)
    return headers, rows

def _sb_row_key(r):
    """Identity of one SB row for cross-sheet dedupe. Two rows with the same key are the
    same object seen through two of Amazon's sheet views, not two different targets."""
    return (ent(r), str(g(r, "campaign id") or ""), str(g(r, "ad group id") or ""),
            str(g(r, "keyword id") or ""), str(g(r, "product targeting id") or ""),
            str(g(r, "keyword text") or ""), str(g(r, "placement") or ""))

def load_workbook_all(path):
    """Open the uploaded bulk ONCE and return every sheet this skill understands.

    Returns a dict:
      sp_headers, sp_rows, sp_st_rows          -- Sponsored Products
      sb_headers, sb_rows, sb_st_rows          -- Sponsored Brands (all ad formats)
      sb_sheet_names                           -- which SB sheets actually carried rows
    SB rows from BOTH the multi-ad-group sheet and the legacy sheet are concatenated (an
    account can legitimately have both); each row remembers its source sheet in "__sheet",
    and the applier mirrors that sheet's own header row on the way out.
    """
    wb = openpyxl.load_workbook(path, data_only=True)
    by_lower = {n.lower().strip(): n for n in wb.sheetnames}
    out = {"sp_headers": None, "sp_rows": [], "sp_st_rows": [],
           "sb_headers": None, "sb_rows": [], "sb_st_rows": [], "sb_sheet_names": [],
           "sb_sheets": {}, "sb_duplicate_rows": 0}

    if SP_SHEET in by_lower:
        out["sp_headers"], out["sp_rows"] = _read_sheet(wb, by_lower[SP_SHEET])
    if SP_ST_SHEET in by_lower:
        _, out["sp_st_rows"] = _read_sheet(wb, by_lower[SP_ST_SHEET])

    # ---- SB sheets: DEDUPE, never blindly concatenate ----
    # Amazon exports the SAME Sponsored Brands campaigns into BOTH the legacy
    # "Sponsored Brands Campaigns" sheet and the newer "SB Multi Ad Group Campaigns" sheet.
    # Verified on a real export: 13 keywords appeared in both, with identical Keyword IDs.
    # Concatenating would score every SB keyword twice, double the account order counts that
    # gate pausing, and emit each change twice into the upload file. So: pick a PRIMARY sheet
    # and take rows from the other only if that exact row is not already present.
    sb_found = []
    for cand in SB_SHEET_CANDIDATES:
        if cand not in by_lower: continue
        hdr, rows = _read_sheet(wb, by_lower[cand])
        if not rows: continue
        leaves = sum(1 for r in rows if is_enabled(r) and is_leaf(r))
        sb_found.append({"name": by_lower[cand], "hdr": hdr, "rows": rows, "leaves": leaves})
    # Primary = most enabled leaf rows; ties go to the sheet listed first in
    # SB_SHEET_CANDIDATES (the multi-ad-group sheet), because it is the richer view --
    # it is the only one carrying ad-group and placement rows.
    sb_found.sort(key=lambda d: -d["leaves"])
    seen = set()
    for i, d in enumerate(sb_found):
        kept = []
        for r in d["rows"]:
            k = _sb_row_key(r)
            if k in seen: continue
            seen.add(k)
            kept.append(r)
        # Count duplicates BEFORE the skip, or a sheet that was entirely duplicated (the
        # normal case for the legacy view) would report zero rows dropped.
        out["sb_duplicate_rows"] += len(d["rows"]) - len(kept)
        if not kept: continue
        out["sb_sheet_names"].append(d["name"])
        out["sb_sheets"][d["name"]] = d["hdr"]
        if out["sb_headers"] is None:
            out["sb_headers"] = d["hdr"]
        out["sb_rows"].extend(kept)
    for cand in SB_ST_SHEET_CANDIDATES:
        if cand not in by_lower: continue
        _, rows = _read_sheet(wb, by_lower[cand])
        out["sb_st_rows"].extend(rows)
    return out

def load_bulk(path):
    """Back-compat 3-tuple used by the SP path and the Felix yesterday-file check."""
    d = load_workbook_all(path)
    if d["sp_headers"] is None:
        raise KeyError("Sponsored Products Campaigns")
    return d["sp_headers"], d["sp_rows"], d["sp_st_rows"]

def g(r, name):  # case-insensitive get
    return r.get(name.lower().strip())

def is_enabled(r):
    ag = g(r, "ad group state (informational only)")
    return (str(g(r, "state")).lower() == "enabled"
            and str(g(r, "campaign state (informational only)")).lower() == "enabled"
            and (ag in (None, "") or str(ag).lower() == "enabled"))

def ent(r):
    return str(g(r, "entity")).lower().strip()

def is_leaf(r):
    return ent(r) in ("keyword", "product targeting")

def is_branded(text, brand_terms):
    if not brand_terms or not text: return False
    t = str(text).lower()
    return any(bt in t for bt in brand_terms)

def base_bid(r):
    b = fnum(g(r, "bid"))
    if b <= 0:
        b = fnum(g(r, "ad group default bid"))  # auto/blank-bid rows fall back to ad group default
    return b

# ---------------- account + campaign aggregates ----------------
def account_metrics(rows, brand_terms):
    leaf = [r for r in rows if is_enabled(r) and is_leaf(r)]
    clicks = sum(fnum(g(r, "clicks")) for r in leaf)
    orders = sum(fnum(g(r, "orders")) for r in leaf)
    sales = sum(fnum(g(r, "sales")) for r in leaf)
    spend = sum(fnum(g(r, "spend")) for r in leaf)
    def seg(branded):
        rs = [r for r in leaf if is_branded(g(r, "keyword text") or g(r, "product targeting expression"), brand_terms) == branded]
        c = sum(fnum(g(r, "clicks")) for r in rs); o = sum(fnum(g(r, "orders")) for r in rs)
        return c, o
    bc, bo = seg(True); nc, no = seg(False)
    return {
        "aov": sales / orders if orders > 0 else 0.0,
        "actc": clicks / orders if orders > 0 else float("inf"),
        "avg_cpc": spend / clicks if clicks > 0 else 0.0,
        "acct_clicks": clicks, "acct_orders": orders,
        "cto_branded": (bc / bo) if bo > 0 else None, "branded_orders": bo,
        "cto_nonbranded": (nc / no) if no > 0 else None, "nonbranded_orders": no,
    }

def campaign_rpc(rows):
    by = {}
    for r in rows:
        if not (is_enabled(r) and is_leaf(r)): continue
        d = by.setdefault(g(r, "campaign id"), {"clicks": 0.0, "sales": 0.0})
        d["clicks"] += fnum(g(r, "clicks")); d["sales"] += fnum(g(r, "sales"))
    return by

def adgroup_rpc(rows):
    by = {}
    for r in rows:
        if not (is_enabled(r) and is_leaf(r)): continue
        k = (g(r, "campaign id"), g(r, "ad group id"))
        d = by.setdefault(k, {"clicks": 0.0, "sales": 0.0})
        d["clicks"] += fnum(g(r, "clicks")); d["sales"] += fnum(g(r, "sales"))
    return {k: (v["sales"] / v["clicks"] if v["clicks"] > 0 else 0.0) for k, v in by.items()}

def campaign_top_modifier(rows):
    by = {}
    for r in rows:
        if ent(r) != "bidding adjustment": continue
        pl = str(g(r, "placement") or "").lower().strip()
        if pl in EXCLUDE_PLACEMENT: continue
        pct = fnum(g(r, "percentage")) / 100.0
        cid = g(r, "campaign id")
        by[cid] = max(by.get(cid, 0.0), pct)
    return by

def campaign_budget_map(rows):
    out = {}
    for r in rows:
        if ent(r) == "campaign" and is_enabled(r):
            out[g(r, "campaign id")] = {"budget": fnum(g(r, "daily budget")),
                                        "name": g(r, "campaign name (informational only)")}
    return out

def decide_budget_daily(main_rows, yrows, bump, cap_mult):
    # campaign spent ~100% of budget yesterday -> raise budget by +bump (never decrease, cap at cap_mult x)
    budg = campaign_budget_map(main_rows)
    yspend = {}
    for r in yrows:
        if is_enabled(r) and is_leaf(r):
            cid = g(r, "campaign id")
            yspend[cid] = yspend.get(cid, 0.0) + fnum(g(r, "spend"))
    out = []
    for cid, info in budg.items():
        old = info["budget"]
        if old <= 0: continue
        if yspend.get(cid, 0.0) >= 0.98 * old:  # treated as 100% spent
            new = round(min(old + bump, old * cap_mult), 2)
            if new > old:
                out.append({"campaign_id": cid, "campaign_name": info["name"],
                            "old_budget": old, "new_budget": new, "reason": "Spent ~100%% of %.2f budget; +%.0f" % (old, bump)})
    return out

def decide_budget_monthly(main_rows, cap=0.15):
    # reallocate toward higher ROAS: top half +cap, bottom half -cap (total stays ~constant)
    budg = campaign_budget_map(main_rows)
    perf = {}
    for r in main_rows:
        if is_enabled(r) and is_leaf(r):
            cid = g(r, "campaign id")
            d = perf.setdefault(cid, {"spend": 0.0, "sales": 0.0})
            d["spend"] += fnum(g(r, "spend")); d["sales"] += fnum(g(r, "sales"))
    ranked = sorted((cid for cid in budg if perf.get(cid, {}).get("spend", 0) > 0),
                    key=lambda c: perf[c]["sales"] / perf[c]["spend"], reverse=True)
    if len(ranked) < 4: return []
    n = max(1, len(ranked) // 4)
    out = []
    for cid in ranked[:n]:  # top performers up
        old = budg[cid]["budget"]; new = round(old * (1 + cap), 2)
        if new != old: out.append({"campaign_id": cid, "campaign_name": budg[cid]["name"], "old_budget": old, "new_budget": new, "reason": "Top ROAS: +%.0f%%" % (cap * 100)})
    for cid in ranked[-n:]:  # bottom performers down to fund it
        old = budg[cid]["budget"]; new = round(old * (1 - cap), 2)
        if new != old: out.append({"campaign_id": cid, "campaign_name": budg[cid]["name"], "old_budget": old, "new_budget": new, "reason": "Bottom ROAS: -%.0f%%" % (cap * 100)})
    return out

# ---------------- strategic-keyword safety flag (ported from kw-harvester-negator) ----------------
# A search term that the negation rule wants to kill, but which appears in the operator's own
# keyword research, is not waste -- it is a term they deliberately targeted that is not converting
# YET. Negating it burns the research. The flag never changes the decision for them: the row still
# appears, sorted to the top, but it carries a different instruction and starts UNTICKED, because
# keeping a strategic term is a judgement call and the rest of the tab is not.
#
# Matching is EXACT STRING, case-insensitive, after whitespace collapse -- deliberately the same
# rule kw-harvester-negator uses, so a term flagged strategic in one skill is flagged strategic in
# the other. A looser token-set match would catch "protein powder vanilla" against a research term
# of "vanilla protein powder", but it would also flag terms the operator never researched, and a
# false "keep" quietly protects real waste. Exact is the conservative half of that trade.
STRATEGIC_REASON = "Don't negate - strategic. Raise bid or move to own campaign."

# Header/section rows in a Sophie KW research export are not keywords. Anything matching these, or
# obviously not a search term, is dropped rather than becoming a spurious keep.
_KW_COL_HINTS = ("keyword", "search term", "phrase", "term", "query", "kw")

def _kw_clean(v):
    s = " ".join(str(v or "").split()).strip().lower()
    if not s or len(s) > 80: return ""
    if s.startswith("#") or "\U0001f50e" in s: return ""     # section markers
    if s.replace(".", "", 1).replace(",", "").isdigit(): return ""
    return s

def load_strategic_terms(path):
    """Read any keyword list -- .txt, .csv, or .xlsx -- into a normalised set.

    Deliberately forgiving about shape: a Sophie KW research workbook, a Cerebro export, or a
    single pasted column all work. Where a header names a keyword-ish column that column is used;
    otherwise the first column of each sheet is taken, which is where a bare keyword list lives.
    """
    if not path: return set()
    p = str(path); low = p.lower()
    terms = set()
    if low.endswith(".txt"):
        with open(p, encoding="utf-8-sig", errors="replace") as f:
            for line in f:
                t = _kw_clean(line)
                if t: terms.add(t)
        return terms
    if low.endswith(".csv"):
        import csv
        with open(p, newline="", encoding="utf-8-sig", errors="replace") as f:
            rows = list(csv.reader(f))
        if not rows: return terms
        hdr = [str(x or "").strip().lower() for x in rows[0]]
        col = next((i for i, h in enumerate(hdr) if any(k in h for k in _KW_COL_HINTS)), None)
        body = rows[1:] if col is not None else rows
        if col is None: col = 0
        for r in body:
            if col < len(r):
                t = _kw_clean(r[col])
                if t: terms.add(t)
        return terms
    wb = openpyxl.load_workbook(p, data_only=True, read_only=True)
    try:
        for ws in wb.worksheets:
            rows = ws.iter_rows(values_only=True)
            try:
                first = next(rows)
            except StopIteration:
                continue
            hdr = [str(x or "").strip().lower() for x in first]
            col = next((i for i, h in enumerate(hdr) if any(k in h for k in _KW_COL_HINTS)), None)
            if col is None:
                col = 0
                t = _kw_clean(first[0] if first else "")
                if t: terms.add(t)
            for r in rows:
                if col < len(r):
                    t = _kw_clean(r[col])
                    if t: terms.add(t)
    finally:
        wb.close()
    return terms

def cto_for(branded, acct):
    seg = acct["cto_branded"] if branded else acct["cto_nonbranded"]
    seg_orders = acct["branded_orders"] if branded else acct["nonbranded_orders"]
    if seg is not None and seg_orders >= SEG_MIN_ORDERS:
        return seg
    if acct["acct_orders"] >= ACCT_MIN_ORDERS and acct["acct_orders"] > 0:
        return acct["acct_clicks"] / acct["acct_orders"]
    return None  # not enough data -> do not pause

def tier(clicks, orders, cfg):
    if clicks >= cfg["clicks_high"] and orders >= 1: return "High"
    if clicks >= cfg["clicks_med_min"]: return "Medium"
    return "Low"

# ---------------- per-row bid decision (value-based strategies) ----------------
def decide_bid(r, cfg, acct, ag_rpc, camp_mod, window_days):
    clicks = fnum(g(r, "clicks")); orders = fnum(g(r, "orders"))
    sales = fnum(g(r, "sales")); spend = fnum(g(r, "spend"))
    bid = base_bid(r)
    if bid <= 0: return None
    target_acos = cfg["target_acos"]
    branded = is_branded(g(r, "keyword text") or g(r, "product targeting expression"), cfg["brand_terms"])
    mt = str(g(r, "match type") or "").lower().strip()
    auto_default = fnum(g(r, "bid")) <= 0  # used the ad group default bid

    # --- pause check first (zero-order waste), single order protects ---
    if orders == 0 and clicks > 0:
        cto = cto_for(branded, acct)
        if cto is not None:
            factor = MATCH_FACTOR.get(mt, 1.6)
            if clicks >= cfg["pause_multiplier"] * cto * factor:
                return {"action": "pause", **_meta(r, bid, clicks, orders, sales, branded, "Pause: %d clicks, 0 orders (>= %.1f x clicks-to-order)" % (clicks, cfg["pause_multiplier"] * cto * factor))}

    # --- grace band (ACOS) ---
    if orders >= 1 and sales > 0:
        row_acos = spend / sales
        if abs(row_acos - target_acos) / target_acos <= cfg["grace_band"]:
            return None

    t = tier(clicks, orders, cfg)
    if t == "High":
        rpc = sales / clicks; new = rpc * target_acos; formula = "RPC %.2f x ACOS %.0f%%" % (rpc, target_acos * 100)
    elif t == "Medium":
        if orders >= 1:
            rpc = sales / clicks; new = rpc * target_acos; formula = "RPC %.2f x ACOS %.0f%% (med)" % (rpc, target_acos * 100)
        else:
            if acct["actc"] == float("inf") or acct["aov"] == 0: return None
            new = target_acos * (acct["aov"] / (clicks + acct["actc"])); formula = "CPA projection"
    else:
        rpc = ag_rpc.get((g(r, "campaign id"), g(r, "ad group id")), 0.0)
        if rpc <= 0: return None
        value = rpc * target_acos          # what a click is modelled to be worth here
        if clicks == 0:
            # ---- ZERO-CLICK RULE: never cut a target that has never been clicked. ----
            # No clicks means no spend, so cutting its bid saves exactly $0. The only thing a
            # cut achieves is making a click less likely -- which is the one event that would
            # tell us whether the target is any good. Pure downside.
            # Two sub-cases, one rule: step the bid UP toward what a click is worth and stop
            # there. If it has no impressions the bid is the only lever that can make it
            # serve; if it has impressions but no clicks, a better placement may be what earns
            # the click. Either way we never pay MORE than the modelled value of a click, and
            # a target already at or above that value is left alone rather than pushed higher.
            # The "never cut" half is universal -- no strategy benefits from trimming a row
            # that spends nothing. The "raise toward value" half is a strategy choice, set by
            # the zero_click dial: "raise" buys a chance at data, "hold" declines to spend on
            # an unproven target at all. Profit-First and CPC-Managed hold, because buying
            # unproven traffic works against protecting margin and against grinding CPC down.
            if cfg.get("zero_click", "raise") == "hold":
                return None
            if bid >= value: return None
            new = min(bid * (1 + cfg["step_size"]), value)
            formula = "Zero-click step up toward value (adgroup RPC %.2f, capped at %.2f)" % (rpc, value)
        else:
            # ---- LOW-DATA RULE (v4.0): a target below the strategy's medium-tier click
            # threshold is never bid DOWN. It is the same argument as the zero-click rule, only
            # slightly weaker: one or two clicks is not evidence, the row has spent almost
            # nothing, and a cut mainly delays the click that would actually tell us something.
            # Reported from a live run where Sponsored Brands rows with 0-3 clicks were being cut
            # 10-15% off what the formula called a "low-data step".
            # The direction is the strategy's own zero_click dial, so Profit-First and
            # CPC-Managed still decline to spend on unproven traffic.
            if cfg.get("zero_click", "raise") == "hold":
                return None
            if bid >= value: return None
            new = min(bid * (1 + cfg["step_size"]), value)
            formula = ("Low-data step up toward value (%d click%s, adgroup RPC %.2f, capped at %.2f)"
                       % (int(clicks), "" if int(clicks) == 1 else "s", rpc, value))

    # brand gate: down only
    if branded and new > bid:
        return {"_branded_up_blocked": True}

    # unified visibility floor (converting keywords only): max potential bid >= 75% of ref CPC.
    # This runs BEFORE the max-change clamp, deliberately. Applied after, it could raise a bid
    # straight through the clamp and make "max change per run" a promise the engine does not
    # keep. Applied here, the floor still protects a converting keyword from being starved --
    # it just gets there over successive runs at the strategy's own step size instead of in one
    # jump, and the per-run guarantee printed in the docs and the dashboard stays true.
    if orders >= 1:
        ref_cpc = (spend / clicks) if (window_days >= 14 and clicks > 0) else acct["avg_cpc"]
        if ref_cpc > 0:
            m = camp_mod.get(g(r, "campaign id"), 0.0)
            floor_bid = (FLOOR_PCT * ref_cpc) / (1 + m)
            if new < floor_bid:
                new = floor_bid

    # asymmetric max-change clamp -- the outer per-run guarantee, so it runs last
    if new > bid:
        new = min(new, bid * (1 + cfg["max_change_up"]))
    else:
        new = max(new, bid * (1 - cfg["max_change_down"]))

    below_min = new < cfg["min_cpc"]
    clamped_max = False
    if new > cfg["max_cpc"]:
        new = cfg["max_cpc"]; clamped_max = True
    new = r2(new)
    if new == r2(bid): return None
    # A Low-tier row is "low data": fewer clicks than the strategy needs for a medium-confidence
    # call. It is surfaced separately in the dashboard so a firm decision and a coin-flip are not
    # sitting in the same list.
    out = {"action": "bid", "new_bid": new, "confidence": t, "formula": formula,
           "low_data": (t == "Low"), "clicks_seen": int(clicks),
           "flag_below_min": below_min, "flag_ceiling": clamped_max, "auto_default_bid": auto_default,
           **_meta(r, bid, clicks, orders, sales, branded, formula)}
    out["delta_pct"] = round((new - bid) / bid * 100, 2) if bid > 0 else None
    return out

def _meta(r, bid, clicks, orders, sales, branded, formula):
    e = ent(r)
    return {"entity": "Keyword" if e == "keyword" else "Product Targeting",
            "campaign_id": g(r, "campaign id"), "ad_group_id": g(r, "ad group id"),
            "keyword_id": g(r, "keyword id") or g(r, "product targeting id"),
            "campaign_name": g(r, "campaign name (informational only)"),
            "ad_group_name": g(r, "ad group name (informational only)"),
            "portfolio_name": g(r, "portfolio name (informational only)"),
            "text": g(r, "keyword text") or g(r, "product targeting expression"),
            "match_type": g(r, "match type"), "current_bid": r2(bid),
            "clicks": clicks, "orders": orders, "sales": sales, "is_branded": branded,
            "formula": formula}

# ---------------- placements ----------------
def _is_cohort_row(r):
    """A Shopper Cohort / Audience Segment adjustment, not a placement adjustment.

    Amazon puts these on the same Entity as placement adjustments but gives them no Placement --
    they carry Shopper Cohort Percentage, Shopper Cohort Type and an Audience ID instead. They are
    a different lever entirely and this skill does not optimize them. Writing one out produces a
    Percentage with an empty Placement, which Amazon rejects.
    """
    return bool(str(g(r, "audience id") or "").strip()
                or str(g(r, "shopper cohort type") or "").strip()
                or str(g(r, "shopper cohort percentage") or "").strip())

def decide_placements(rows, cfg, camp_rpc_v):
    out = []
    for r in rows:
        if ent(r) != "bidding adjustment": continue
        if str(g(r, "campaign state (informational only)")).lower() != "enabled": continue
        if _is_cohort_row(r): continue
        pl = str(g(r, "placement") or "").lower().strip()
        # No placement label means we cannot say WHICH placement a percentage applies to, so the
        # row is unwritable by definition. Never emit one.
        if not pl: continue
        if pl in EXCLUDE_PLACEMENT: continue
        cur = fnum(g(r, "percentage"))
        clicks = fnum(g(r, "clicks")); sales = fnum(g(r, "sales"))
        cid = g(r, "campaign id")
        camp = camp_rpc_v.get(cid)
        if not camp or camp["clicks"] == 0: continue
        crpc = camp["sales"] / camp["clicks"]
        if clicks < PLACEMENT_MIN_CLICKS or crpc <= 0: continue
        prpc = sales / clicks if clicks > 0 else 0.0
        if prpc <= 0: continue
        if cfg["placement_mode"] == "ladder":
            nxt = next((x for x in LADDER if x > cur), cur)  # step up the ladder
            new = nxt if prpc >= crpc else max(0, round(cur * 0.5))  # halve on weak performance
        else:
            ideal = max(0.0, ((prpc / crpc) - 1.0) * 100.0)
            delta = ideal - cur
            # Per-mode increase cap. Ranking Push's extra headroom applies ONLY to top of
            # search -- giving it to product pages and rest-of-search too is not "pushing top
            # of search", it is just bidding everything up harder.
            if cfg["placement_mode"] == "tos":
                cap_up = TOS_MAX_UP_PP if pl == TOS_PLACEMENT else PLACEMENT_MAX_UP_PP
            elif cfg["placement_mode"] == "trim":
                cap_up = TRIM_MAX_UP_PP
            else:
                cap_up = PLACEMENT_MAX_UP_PP
            if delta > cap_up: delta = cap_up
            if delta < -PLACEMENT_MAX_DOWN_PP: delta = -PLACEMENT_MAX_DOWN_PP
            new = max(0.0, round(cur + delta))
        if new == cur: continue
        # A placement sitting at 0% is Amazon's default, so refusing to move off zero (the old
        # rule) left SP placement tuning inert on most campaigns -- the same defect Sponsored
        # Brands had fixed in v3.3. Moving off zero CREATES a modifier the campaign did not
        # have, which is a bigger decision than nudging an existing one, so it is flagged and
        # badged in the dashboard rather than slipped in silently. Note that `ideal` is floored
        # at 0 for SP, so a 0% placement can only ever be CREATED when its RPC beats the
        # campaign's -- a weak 0% placement stays at 0 and is dropped by the equality check
        # above.
        creates = int(round(cur)) == 0
        out.append({"campaign_id": cid, "campaign_name": g(r, "campaign name (informational only)"),
                    "placement": g(r, "placement"), "current_pct": cur, "new_pct": new,
                    "placement_rpc": round(prpc, 2), "campaign_rpc": round(crpc, 2),
                    "clicks": clicks, "creates_modifier": creates})
    return out

# ---------------- negations (new rule) ----------------
def find_negations(st_rows, cfg, acct):
    """Advisory negation candidates from a customer-search-term sheet.

    Note the state gate: several Amazon search-term exports carry NO State column at all. The
    old check was `state != "enabled" -> skip`, which turned a missing column into
    `"none" != "enabled"` and silently dropped every row -- an empty Negations tab that looks
    exactly like "your account has no waste". A row is in the search term report because it
    served, so a blank or absent state is treated as enabled; only an explicitly non-enabled
    state is skipped. main() also warns when a search-term sheet had rows but the state filter
    removed all of them, so a genuinely all-paused sheet is never mistaken for a clean account.
    """
    out = []
    cto = (acct["acct_clicks"] / acct["acct_orders"]) if acct["acct_orders"] >= ACCT_MIN_ORDERS and acct["acct_orders"] > 0 else None
    avg_cpc = acct["avg_cpc"]
    for r in st_rows:
        _state = str(g(r, "state") or "").strip().lower()
        if _state and _state != "enabled": continue
        if fnum(g(r, "orders")) > 0: continue
        clicks = fnum(g(r, "clicks")); spend = fnum(g(r, "spend"))
        cpc = spend / clicks if clicks > 0 else 0.0
        kw = (g(r, "keyword text") or "").strip().lower()
        st = (g(r, "customer search term") or "").strip().lower()
        if not st or kw == st: continue
        if is_branded(kw, cfg["brand_terms"]) or is_branded(st, cfg["brand_terms"]): continue
        hit_clicks = cto is not None and clicks >= cto
        hit_cost = avg_cpc > 0 and cpc >= 2 * avg_cpc
        if not (hit_clicks or hit_cost): continue
        reason = []
        if hit_clicks: reason.append("%d clicks >= clicks-to-order %.1f, 0 orders" % (clicks, cto))
        if hit_cost: reason.append("CPC %.2f >= 2x avg %.2f" % (cpc, avg_cpc))
        strategic = st in cfg.get("strategic_terms", ())
        out.append({"campaign_name": g(r, "campaign name (informational only)"),
                    "ad_group_name": g(r, "ad group name (informational only)"),
                    "keyword_text": g(r, "keyword text"), "match_type": g(r, "match type"),
                    "customer_search_term": g(r, "customer search term"),
                    "clicks": clicks, "spend": round(spend, 2),
                    "strategic": strategic,
                    "reason": (STRATEGIC_REASON + " (Would have been negated: " + "; ".join(reason) + ")")
                              if strategic else "; ".join(reason)})
    # Strategic keeps sort to the top: they are the rows that need a human decision, and burying
    # them under fifty genuine negations is how a researched term gets killed by a bulk tick.
    out.sort(key=lambda x: (not x.get("strategic"), -x.get("spend", 0.0)))
    return out

# ================= Sponsored Brands (v3) =================
# SB reuses the SAME engine as SP -- decide_bid() is product-agnostic. What changes is
# WHICH benchmarks it is handed: SB rows are bucketed by ad format and each bucket gets its
# own account_metrics() and ad-group RPC map. That is the whole point of the split: a video
# keyword's "Low-data step toward ad group RPC" must step toward VIDEO RPC, and its pause
# threshold must come from VIDEO clicks-to-order, not from a Product Collection blend.

def sb_campaign_index(sb_rows):
    """campaign id -> {ad_format, video_ids, name, budget}. Built from Campaign rows, which
    are the only rows that reliably carry Ad Format / Video Asset IDs; keyword and targeting
    rows inherit from their parent campaign."""
    idx = {}
    for r in sb_rows:
        if ent(r) != "campaign": continue
        cid = g(r, "campaign id")
        if cid in (None, ""): continue
        idx[cid] = {
            "ad_format": str(g(r, "ad format") or "").strip().lower(),
            "video_ids": str(g(r, "video asset ids") or g(r, "video media ids") or "").strip(),
            "name": g(r, "campaign name (informational only)") or g(r, "campaign name"),
            "budget": fnum(g(r, "daily budget")),
            "state": str(g(r, "state") or "").strip().lower(),
        }
    return idx

def sb_ad_format(r, cidx):
    """Classify one SB row into video / product_collection / store_spotlight / unknown.

    A populated video asset id is the STRONGEST signal (Amazon has shipped several spellings
    of the Ad Format value over time, but a video asset id only ever appears on a video
    campaign). Falls back to the Ad Format text, then to the parent campaign, then -- last
    resort -- to the Sophie campaign-naming convention, which tags video campaigns "SBV".
    """
    af = str(g(r, "ad format") or "").strip().lower()
    vids = str(g(r, "video asset ids") or g(r, "video media ids") or "").strip()
    parent = cidx.get(g(r, "campaign id")) or {}
    if not af: af = parent.get("ad_format", "")
    if not vids: vids = parent.get("video_ids", "")
    if vids: return "video"
    if "video" in af: return "video"
    if "product collection" in af or "productcollection" in af: return "product_collection"
    if "store spotlight" in af or "storespotlight" in af: return "store_spotlight"
    name = str(parent.get("name") or g(r, "campaign name (informational only)") or "").lower()
    # Sophie naming convention: "... | SBV | ..." -- only used when Amazon told us nothing.
    for tok in str(name).replace("|", " ").split():
        if tok.strip() == "sbv": return "video"
    return "unknown"

def sb_segments(sb_rows, cidx, brand_terms):
    """Bucket enabled SB leaf rows by ad format and compute per-format benchmarks."""
    buckets = {}
    for r in sb_rows:
        if not (is_enabled(r) and is_leaf(r)): continue
        buckets.setdefault(sb_ad_format(r, cidx), []).append(r)
    segs = {}
    for fmt, rows in buckets.items():
        segs[fmt] = {
            "rows": rows,
            "acct": account_metrics(rows, brand_terms),   # per-format, not account-wide
            "ag_rpc": adgroup_rpc(rows),
            "clicks": sum(fnum(g(r, "clicks")) for r in rows),
            "spend": round(sum(fnum(g(r, "spend")) for r in rows), 2),
            "sales": round(sum(fnum(g(r, "sales")) for r in rows), 2),
            "orders": sum(fnum(g(r, "orders")) for r in rows),
        }
    return segs

def decide_sb_bids(sb_rows, cidx, sb_cfg, window_days):
    """Score every enabled SB leaf row against its OWN ad format's benchmarks."""
    segs = sb_segments(sb_rows, cidx, sb_cfg["brand_terms"])
    changes, branded_blocked = [], 0
    for fmt in SB_FORMAT_ORDER:
        seg = segs.get(fmt)
        if not seg: continue
        # SB gets no placement-modifier headroom in the visibility floor: SB placement
        # semantics differ from SP's and we will not infer a multiplier we cannot verify.
        camp_mod = {}
        for r in seg["rows"]:
            d = decide_bid(r, sb_cfg, seg["acct"], seg["ag_rpc"], camp_mod, window_days)
            if not d: continue
            if d.get("_branded_up_blocked"):
                branded_blocked += 1
                continue
            d["product"] = "Sponsored Brands"
            d["ad_format"] = fmt
            d["ad_format_label"] = SB_FORMAT_LABELS.get(fmt, fmt)
            d["sheet"] = r.get("__sheet")
            changes.append(d)
    return changes, branded_blocked, segs

def decide_sb_placements(sb_rows, sb_cfg, cidx):
    """SB placement modifiers -- recognition-gated, and SIGNED.

    Two ways this differs from the Sponsored Products version:

    1. **Signed percentages.** SB accepts negative placement modifiers (verified live: a real
       campaign carried REST_OF_SEARCH at -10). SP cannot go below 0. So where the SP engine
       floors the ideal at 0 and can only ever bid a placement up, SB is allowed to bid a
       weak placement down, which is what the RPC-relative formula naturally wants to do.
    2. **Enum gating.** A label that resolves to an API enum is writable and pushable; an
       unresolved label is advisory-only -- shown in the dashboard, excluded from the upload
       file AND from the live push. We do not send a number we cannot address.
    """
    out = []
    camp = {}
    for r in sb_rows:
        if not (is_enabled(r) and is_leaf(r)): continue
        cid = g(r, "campaign id")
        d = camp.setdefault(cid, {"clicks": 0.0, "sales": 0.0})
        d["clicks"] += fnum(g(r, "clicks")); d["sales"] += fnum(g(r, "sales"))
    for r in sb_rows:
        # Sponsored Brands names this entity "Bidding Adjustment by Placement", NOT the
        # "Bidding Adjustment" that Sponsored Products uses. Verified on a real export.
        # Match on the prefix so both spellings (and any future suffix) are picked up.
        if not ent(r).startswith("bidding adjustment"): continue
        if str(g(r, "campaign state (informational only)")).lower() != "enabled": continue
        if _is_cohort_row(r): continue
        label = str(g(r, "placement") or "").strip()
        key = label.lower()
        if not key: continue          # unwritable: a percentage with no placement is rejected
        if key in EXCLUDE_PLACEMENT: continue
        cid = g(r, "campaign id")
        c = camp.get(cid)
        if not c or c["clicks"] == 0: continue
        crpc = c["sales"] / c["clicks"]
        clicks = fnum(g(r, "clicks")); sales = fnum(g(r, "sales"))
        if clicks < PLACEMENT_MIN_CLICKS or crpc <= 0: continue
        prpc = sales / clicks if clicks > 0 else 0.0
        if prpc <= 0: continue
        cur = fnum(g(r, "percentage"))
        # NOT floored at 0 -- SB may go negative. The same per-run step caps still apply.
        ideal = ((prpc / crpc) - 1.0) * 100.0
        delta = ideal - cur
        if delta > PLACEMENT_MAX_UP_PP: delta = PLACEMENT_MAX_UP_PP
        if delta < -PLACEMENT_MAX_DOWN_PP: delta = -PLACEMENT_MAX_DOWN_PP
        new = int(round(cur + delta))
        new = max(SB_PLACEMENT_MIN_PP, min(SB_PLACEMENT_MAX_PP, new))
        if new == int(round(cur)): continue
        enum = sb_placement_enum(label)
        advisory = enum is None
        # SB placement modifiers default to 0, so most real accounts have every SB placement
        # sitting at zero. Refusing to move off zero (the Sponsored Products rule) would make
        # this feature inert on SB. We do allow it, but a 0 -> n move CREATES a modifier the
        # operator never had, which is a bigger decision than nudging an existing one -- so it
        # is flagged and shown as such in the dashboard rather than slipped in silently.
        creates = int(round(cur)) == 0
        out.append({"product": "Sponsored Brands", "campaign_id": cid,
                    "campaign_name": g(r, "campaign name (informational only)"),
                    "ad_format": sb_ad_format(r, cidx),
                    "placement": label, "placement_enum": enum or "",
                    "current_pct": cur, "new_pct": new,
                    "placement_rpc": round(prpc, 2), "campaign_rpc": round(crpc, 2),
                    "clicks": clicks, "advisory": advisory, "creates_modifier": creates,
                    "sheet": r.get("__sheet"),
                    "advisory_reason": ("" if not advisory else
                        "Placement label '%s' does not map to an Amazon placement enum - "
                        "shown for review, excluded from the upload file and the push" % label)})
    return out

def sb_summary(segs, changes, placement_changes, negations, branded_blocked):
    by_fmt = {}
    for fmt in SB_FORMAT_ORDER:
        seg = segs.get(fmt)
        if not seg: continue
        fmt_changes = [c for c in changes if c.get("ad_format") == fmt]
        by_fmt[fmt] = {
            "label": SB_FORMAT_LABELS.get(fmt, fmt),
            "enabled_targets": len(seg["rows"]),
            "clicks": seg["clicks"], "orders": seg["orders"],
            "spend": seg["spend"], "sales": seg["sales"],
            "avg_cpc": round(seg["acct"]["avg_cpc"], 2),
            "bid_changes": sum(1 for c in fmt_changes if c["action"] == "bid"),
            "pauses": sum(1 for c in fmt_changes if c["action"] == "pause"),
        }
    return {
        "by_ad_format": by_fmt,
        "counts": {
            "bid_changes": sum(1 for c in changes if c["action"] == "bid"),
            "pauses": sum(1 for c in changes if c["action"] == "pause"),
            "below_min": sum(1 for c in changes if c.get("flag_below_min")),
            "branded_bid_ups_blocked": branded_blocked,
            "placement_changes": sum(1 for p in placement_changes if not p.get("advisory")),
            "placement_advisory": sum(1 for p in placement_changes if p.get("advisory")),
            "negations": len(negations),
        },
    }

# ---------------- main ----------------
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--strategy", required=True, choices=list(STRATEGIES.keys()))
    p.add_argument("--felix-mode", choices=["daily", "weekly", "monthly"], default="daily")
    p.add_argument("--target-acos", required=True, type=float)
    p.add_argument("--min-cpc", required=True, type=float)
    p.add_argument("--max-cpc", required=True, type=float)
    p.add_argument("--brand-terms", default="")
    p.add_argument("--low-data-tab", choices=["yes", "no"], default="yes",
                   help="Put low-data targets (fewer clicks than the strategy's medium tier) on "
                        "their own dashboard tab instead of mixing them into Bids. Display only.")
    p.add_argument("--keyword-research", default="",
                   help="Optional keyword list (.xlsx / .csv / .txt). Any search term flagged for "
                        "negation that exactly matches one of these is re-labelled a strategic keep "
                        "and starts unticked. Negations only - it never affects bids or pauses.")
    p.add_argument("--currency-symbol", default="$",
                   help="Symbol used to LABEL money in the dashboard. Display only - the reader "
                        "already strips $ EUR GBP symbols from the bulk, and no maths depends on it.")
    p.add_argument("--window-days", type=int, default=30)
    p.add_argument("--yesterday-input", default="", help="Felix daily: a 1-day (yesterday) bulk for the budget check")
    p.add_argument("--felix-bump", type=float, default=10.0)
    p.add_argument("--budget-cap-mult", type=float, default=2.0)
    # --- v3: Sponsored Brands ---
    p.add_argument("--products", default="sp", choices=["sp", "sb", "both"],
                   help="Which ad products to score from this one workbook.")
    p.add_argument("--sb-target-acos", type=float, default=None,
                   help="SB target ACOS %%. Omit to MATCH the SP value.")
    p.add_argument("--sb-min-cpc", type=float, default=None, help="Omit to match SP.")
    p.add_argument("--sb-max-cpc", type=float, default=None, help="Omit to match SP.")
    p.add_argument("--sb-brand-terms", default=None, help="Omit to match SP.")
    p.add_argument("--sb-strategy", default=None, choices=list(STRATEGIES.keys()),
                   help="Omit to match the SP strategy.")
    p.add_argument("--sb-ad-formats", default="video,product_collection,store_spotlight,unknown",
                   help="Comma list of ad formats to score.")
    p.add_argument("--output-json", required=True)
    args = p.parse_args()

    cfg = dict(STRATEGIES[args.strategy])
    cfg["min_cpc"] = args.min_cpc; cfg["max_cpc"] = args.max_cpc
    cfg["target_acos"] = (args.target_acos / 100.0) * cfg["target_acos_mult"]
    cfg["brand_terms"] = [x.strip().lower() for x in args.brand_terms.split(",") if x.strip()]
    cfg["currency_symbol"] = args.currency_symbol or "$"
    # One research file serves the whole account, so it applies to Sponsored Brands too regardless
    # of whether SB matched or differed on the other dials -- a term is strategic or it is not.
    _strategic = load_strategic_terms(args.keyword_research)
    cfg["strategic_terms"] = _strategic

    wbd = load_workbook_all(args.input)
    sp_rows, st_rows = wbd["sp_rows"], wbd["sp_st_rows"]
    headers = wbd["sp_headers"]
    sb_rows, sb_st_rows = wbd["sb_rows"], wbd["sb_st_rows"]

    want_sp = args.products in ("sp", "both")
    want_sb = args.products in ("sb", "both")

    # --- SB config: each dial either MATCHES SP or was explicitly overridden ---
    sb_strategy = args.sb_strategy or args.strategy
    sb_cfg = dict(STRATEGIES[sb_strategy])
    sb_acos_pct = args.sb_target_acos if args.sb_target_acos is not None else args.target_acos
    sb_cfg["min_cpc"] = args.sb_min_cpc if args.sb_min_cpc is not None else args.min_cpc
    sb_cfg["max_cpc"] = args.sb_max_cpc if args.sb_max_cpc is not None else args.max_cpc
    sb_cfg["target_acos"] = (sb_acos_pct / 100.0) * sb_cfg["target_acos_mult"]
    _sb_bt = args.sb_brand_terms if args.sb_brand_terms is not None else args.brand_terms
    sb_cfg["brand_terms"] = [x.strip().lower() for x in _sb_bt.split(",") if x.strip()]
    sb_cfg["strategic_terms"] = _strategic
    # SB is deliberately more patient than SP on pauses (see SB_PAUSE_PATIENCE).
    sb_cfg["pause_multiplier"] = sb_cfg["pause_multiplier"] * SB_PAUSE_PATIENCE
    sb_matches_sp = (args.sb_strategy in (None, args.strategy)
                     and args.sb_target_acos in (None, args.target_acos)
                     and args.sb_min_cpc in (None, args.min_cpc)
                     and args.sb_max_cpc in (None, args.max_cpc)
                     and args.sb_brand_terms in (None, args.brand_terms))
    sb_formats_wanted = [x.strip().lower() for x in args.sb_ad_formats.split(",") if x.strip()]

    acct = account_metrics(sp_rows, cfg["brand_terms"])
    camp = campaign_rpc(sp_rows)
    ag = adgroup_rpc(sp_rows)
    cmod = campaign_top_modifier(sp_rows)

    enabled_leaf = [r for r in sp_rows if is_enabled(r) and is_leaf(r)]
    sb_enabled_leaf = [r for r in sb_rows if is_enabled(r) and is_leaf(r)]
    warnings = []
    if want_sp and not enabled_leaf:
        if not want_sb or not sb_enabled_leaf:
            print(json.dumps({"error": "zero_enabled_rows",
                              "message": "No enabled keyword/target rows found. The file may be an unexpected format."}))
            return
        warnings.append("No enabled Sponsored Products rows found - scoring Sponsored Brands only.")
        want_sp = False
    if want_sb and not sb_enabled_leaf:
        warnings.append("No enabled Sponsored Brands rows found. Re-download the bulk with "
                        "'Sponsored Brands data' and 'Sponsored Brands search term data' ticked.")
        want_sb = False
    if want_sb and not sb_st_rows:
        warnings.append("No SB search term sheet in this workbook - SB negations skipped.")
    if not want_sp and not want_sb:
        print(json.dumps({"error": "zero_enabled_rows",
                          "message": "No enabled keyword/target rows found for the requested products."}))
        return

    # Mode-aware emission. Felix never mixes bids and placements in one run.
    felix = args.strategy == "cpc_managed"
    mode = args.felix_mode
    do_bids = (not felix) or mode == "daily"
    do_placements = (not felix) or mode == "weekly"
    # CPC-Managed deliberately never moves bids and placements in the same run. That is correct,
    # but an empty tab reads as "nothing to change" rather than "not scored", so say which it is.
    # Same principle as the search-term warnings: never let a suppressed check look like a clean
    # result.
    if felix:
        if not do_bids:
            warnings.append(
                "CPC-Managed %s mode tunes %s only - bids and pauses were NOT scored this run, so "
                "empty Bids and Pauses tabs mean 'not evaluated', not 'nothing to change'. Run "
                "daily mode for bids." % (mode, "placements" if mode == "weekly" else "budgets"))
        if not do_placements:
            warnings.append(
                "CPC-Managed %s mode does not touch placements - the Placements tabs are empty "
                "because they were not evaluated. Run weekly mode for placements." % mode)

    changes, branded_blocked = [], 0
    if do_bids and want_sp:
        for r in sp_rows:
            if not (is_enabled(r) and is_leaf(r)): continue
            d = decide_bid(r, cfg, acct, ag, cmod, args.window_days)
            if not d: continue
            if d.get("_branded_up_blocked"): branded_blocked += 1; continue
            d["product"] = "Sponsored Products"
            d["sheet"] = r.get("__sheet")
            changes.append(d)

    placement_changes = decide_placements(sp_rows, cfg, camp) if (do_placements and want_sp) else []
    for p in placement_changes:
        p["product"] = "Sponsored Products"
    _sp_created = sum(1 for p in placement_changes if p.get("creates_modifier"))
    if _sp_created:
        warnings.append(
            "%d Sponsored Products placement modifier(s) would be CREATED from 0%% - these add a "
            "modifier the campaign did not have. Review them before approving." % _sp_created)
    negations = find_negations(st_rows, cfg, acct) if (do_bids and want_sp) else []
    for n in negations:
        n["product"] = "Sponsored Products"
    # Distinguish "no waste found" from "we never looked". An empty Negations tab is the most
    # dangerous kind of empty, because it reads as a clean account.
    if do_bids and want_sp:
        if not st_rows:
            warnings.append("No 'SP Search Term Report' sheet in this workbook - Sponsored Products "
                            "negations were skipped, not found to be zero. Re-download the bulk with "
                            "'Sponsored Products search term data' ticked if you want them.")
        elif not negations:
            warnings.append("The Sponsored Products search term sheet had %d row(s) but none met the "
                            "negation rule - that is a genuine zero, not a missing sheet." % len(st_rows))

    # ---- Sponsored Brands, from the same workbook, split by ad format ----
    sb_changes, sb_branded_blocked, sb_segs = [], 0, {}
    sb_placement_changes, sb_negations, sb_meta = [], [], None
    if want_sb:
        cidx = sb_campaign_index(sb_rows)
        if do_bids:
            sb_changes, sb_branded_blocked, sb_segs = decide_sb_bids(
                sb_rows, cidx, sb_cfg, args.window_days)
            sb_changes = [c for c in sb_changes if c.get("ad_format") in sb_formats_wanted]
        else:
            sb_segs = sb_segments(sb_rows, cidx, sb_cfg["brand_terms"])
        if do_placements:
            sb_placement_changes = [p for p in decide_sb_placements(sb_rows, sb_cfg, cidx)
                                    if p.get("ad_format") in sb_formats_wanted]
        if do_bids and sb_st_rows and not [r for r in sb_st_rows
                                           if (str(g(r, "state") or "").strip().lower() or "enabled") == "enabled"]:
            warnings.append("The Sponsored Brands search term sheet had %d row(s) but every one is in a "
                            "non-enabled state, so SB negations are empty by filter rather than by "
                            "finding nothing." % len(sb_st_rows))
        if do_bids and sb_st_rows:
            # Negate against the blended SB account, not one format: a wasteful search term
            # is wasteful regardless of which SB format served it.
            sb_acct_all = account_metrics(
                [r for r in sb_rows if is_enabled(r) and is_leaf(r)], sb_cfg["brand_terms"])
            sb_negations = find_negations(sb_st_rows, sb_cfg, sb_acct_all)
            for n in sb_negations:
                n["product"] = "Sponsored Brands"
        sb_meta = sb_summary(sb_segs, sb_changes, sb_placement_changes,
                             sb_negations, sb_branded_blocked)
        sb_meta["matches_sp"] = sb_matches_sp
        sb_meta["strategy"] = sb_strategy
        sb_meta["pause_patience_multiplier"] = SB_PAUSE_PATIENCE
        sb_meta["sheets_read"] = wbd["sb_sheet_names"]
        sb_meta["duplicate_rows_dropped"] = wbd["sb_duplicate_rows"]
        sb_meta["counts"]["negations_strategic"] = sum(1 for n in sb_negations if n.get("strategic"))
        sb_meta["counts"]["low_data"] = sum(1 for c in sb_changes
                                            if c.get("low_data") and c["action"] == "bid")
        sb_meta["config"] = {"strategy": sb_strategy, "target_acos": sb_acos_pct,
                             "min_cpc": sb_cfg["min_cpc"], "max_cpc": sb_cfg["max_cpc"],
                             "brand_terms": _sb_bt, "below_min": sb_cfg["below_min"],
                             "zero_click": sb_cfg.get("zero_click", "raise"),
                             "ad_formats": sb_formats_wanted}
        skipped = [SB_FORMAT_LABELS.get(f, f) for f in SB_FORMAT_ORDER
                   if f in sb_segs and f not in sb_formats_wanted]
        if skipped:
            warnings.append("SB ad formats present but not scored this run: " + ", ".join(skipped))
        if wbd["sb_duplicate_rows"]:
            warnings.append(
                "Amazon exported the same Sponsored Brands rows on more than one sheet; "
                "%d duplicate row(s) were dropped so nothing is scored or uploaded twice."
                % wbd["sb_duplicate_rows"])
        created = sum(1 for p in sb_placement_changes if p.get("creates_modifier") and not p.get("advisory"))
        if created:
            warnings.append(
                "%d Sponsored Brands placement modifier(s) would be CREATED from 0%% - these "
                "add a modifier the campaign did not have. Review them before approving." % created)
        adv = sum(1 for p in sb_placement_changes if p.get("advisory"))
        if adv:
            warnings.append("%d SB placement row(s) had an unrecognised placement label - "
                            "shown as advisory and excluded from the upload file." % adv)

    if _strategic:
        _kept = sum(1 for n in negations if n.get("strategic")) + \
                sum(1 for n in (sb_negations or []) if n.get("strategic"))
        warnings.append(
            "Keyword research loaded (%d term(s)). %d search term(s) that met the negation rule "
            "match your research and are shown as STRATEGIC KEEPS - they sort to the top of the "
            "Negations tab and start unticked. Raise the bid or move them to their own campaign "
            "rather than negating them." % (len(_strategic), _kept))
    elif args.keyword_research:
        warnings.append("The keyword research file yielded no usable terms - the strategic-keep flag "
                        "did not run. Check the file has a keyword column.")

    if not felix:
        warnings.append(
            "Budgets are only adjusted by the ACOS-Targeted but CPC-Managed strategy; this run "
            "used %s, so the Budgets tab is empty by design rather than because nothing needed "
            "changing." % args.strategy)
    _n_low = sum(1 for c in changes if c.get("low_data") and c["action"] == "bid") + \
             sum(1 for c in (sb_changes or []) if c.get("low_data") and c["action"] == "bid")
    if _n_low:
        warnings.append(
            "%d target(s) have fewer than %d clicks. These are LOW DATA: never bid down, stepped "
            "up toward what a click is worth only where the strategy allows it, and %s."
            % (_n_low, cfg["clicks_med_min"],
               "shown on their own tab" if args.low_data_tab == "yes"
               else "badged in the Bids tabs"))

    _zc = cfg.get("zero_click", "raise")
    _zc_rows = sum(1 for r in sp_rows if is_enabled(r) and is_leaf(r) and fnum(g(r, "clicks")) == 0) if want_sp else 0
    _zc_rows += sum(1 for r in sb_rows if is_enabled(r) and is_leaf(r) and fnum(g(r, "clicks")) == 0) if want_sb else 0
    if _zc_rows:
        warnings.append(
            "%d target(s) have never been clicked. No strategy bids those down; %s treats them as "
            "'%s'%s." % (_zc_rows, args.strategy,
                         _zc,
                         " - their bids are left exactly as they are" if _zc == "hold"
                         else " - their bids step up toward what a click is worth, capped at that value"))

    budget_changes = []
    if felix and mode == "daily" and args.yesterday_input:
        _, yrows, _ = load_bulk(args.yesterday_input)
        budget_changes = decide_budget_daily(sp_rows, yrows, args.felix_bump, args.budget_cap_mult)
        if not budget_changes:
            warnings.append("No campaign spent its full budget yesterday, so no budget increases "
                            "are proposed - that is a genuine zero, the check did run.")
    elif felix and mode == "daily":
        # The daily budget check NEEDS the one-day export. Without it the tab reads 0, which looks
        # exactly like "no campaign spent out" -- the opposite of the truth, which is that nothing
        # was checked. The skill's own fallback rules say to tell the operator; now it does.
        warnings.append(
            "CPC-Managed daily mode had no Yesterday bulk to compare against, so the budget check "
            "was SKIPPED, not passed. A zero on the Budgets tab here means 'not evaluated'. "
            "Re-download a 1-day (Yesterday) bulk and re-run if you want the budget increases.")
    elif felix and mode == "monthly":
        budget_changes = decide_budget_monthly(sp_rows)
        if not budget_changes:
            warnings.append("Monthly reallocation needs at least 4 campaigns with spend to rank; "
                            "this account has too few, so no budget moves are proposed.")

    summary = {
        "strategy": args.strategy, "felix_mode": args.felix_mode if args.strategy == "cpc_managed" else None,
        "products": args.products,
        "account": {k: (round(v, 2) if isinstance(v, float) and v != float("inf") else v) for k, v in acct.items()},
        "counts": {
            "bid_changes": sum(1 for c in changes if c["action"] == "bid"),
            "pauses": sum(1 for c in changes if c["action"] == "pause"),
            "below_min": sum(1 for c in changes if c.get("flag_below_min")),
            "branded_bid_ups_blocked": branded_blocked,
            "placement_changes": len(placement_changes), "negations": len(negations),
            # Negatives are applied per ad group, so one wasteful term legitimately produces one
            # row per ad group it served in. The row count is therefore right but reads as
            # inflated; the distinct-term count is what an operator actually has to decide about.
            "negations_distinct_terms": len({str(n.get("customer_search_term", "")).strip().lower()
                                             for n in negations}),
            "negations_strategic": sum(1 for n in negations if n.get("strategic")),
            "low_data": sum(1 for c in changes if c.get("low_data") and c["action"] == "bid"),
            "budget_changes": len(budget_changes),
        },
        "changes": changes, "placement_changes": placement_changes, "negations": negations,
        "budget_changes": budget_changes,
        # --- Sponsored Brands lives in its own namespace so nothing downstream can confuse
        # an SB row for an SP row; they are written to DIFFERENT sheets in the upload file. ---
        "sb": (None if not want_sb else {
            "changes": sb_changes,
            "placement_changes": sb_placement_changes,
            "negations": sb_negations,
            "meta": sb_meta,
        }),
        "warnings": warnings,
        "config": {"strategy": args.strategy, "target_acos": args.target_acos, "min_cpc": args.min_cpc,
                   "currency_symbol": cfg["currency_symbol"],
                   "low_data_tab": args.low_data_tab == "yes",
                   "keyword_research": (args.keyword_research or None),
                   "strategic_terms_loaded": len(_strategic),
                   "max_cpc": args.max_cpc, "window_days": args.window_days, "below_min": cfg["below_min"],
                   "zero_click": cfg.get("zero_click", "raise"),
                   "products": args.products,
                   "sb": (sb_meta or {}).get("config") if want_sb else None,
                   "sb_matches_sp": sb_matches_sp if want_sb else None},
    }
    if want_sb:
        summary["counts"]["sb_bid_changes"] = sb_meta["counts"]["bid_changes"]
        summary["counts"]["sb_pauses"] = sb_meta["counts"]["pauses"]
        summary["counts"]["sb_placement_changes"] = sb_meta["counts"]["placement_changes"]
        summary["counts"]["sb_placement_advisory"] = sb_meta["counts"]["placement_advisory"]
        summary["counts"]["sb_negations"] = sb_meta["counts"]["negations"]
        summary["counts"]["sb_branded_bid_ups_blocked"] = sb_meta["counts"]["branded_bid_ups_blocked"]
    with open(args.output_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, default=str)
    print(json.dumps(summary["counts"]))

if __name__ == "__main__":
    main()
```

## Writing outputs after approval

Two files, two purposes:

1. **`bulk_upload_<source>_<YYYYMMDD_HHMM>.xlsx`** - the **only** file meant for Amazon Ads bulk upload. Fresh xlsx built via `openpyxl.Workbook()` (not `load_workbook` on the template), single sheet named `Sponsored Products Campaigns`, 52-column header + `Operation=Update` rows only. Amazon Ads Bulk UI accepts **.xlsx only** - CSV uploads are rejected. Building fresh rather than mutating Amazon's template avoids the "Invalid or corrupt" errors that come from openpyxl restructuring shared strings / theme / drawings during a save.

2. **`review_annotated_<source>_<YYYYMMDD_HHMM>.xlsx`** - a **review-only** copy of the source bulk with highlighted rows + cell comments explaining each change. **Do NOT upload this to Amazon** - mutating the source xlsx through openpyxl is known to produce "Invalid or corrupt" file errors because openpyxl rewrites shared strings, drops theme data, and restructures drawings. Filename is deliberately prefixed `review_annotated_` so humans don't confuse it with the upload file.

**Critical upload guardrail:** Always tell the user which file to upload. The upload xlsx is the forward action; the review xlsx is annotated-and-read-only. Never upload the review file.

```python
# apply_changes_v3.py
# Builds the Amazon-upload xlsx and a COMPLETE reverse xlsx from the scorer JSON.
# Output headers MIRROR the uploaded file's exact header row (so casing always matches
# what Amazon currently accepts). Reverse restores pre-change values for every change
# type: bid, pause-state, placement percentage, and budget.
#
# v3: the upload workbook can carry TWO sheets -- "Sponsored Products Campaigns" and the
# Sponsored Brands sheet -- because Amazon's Bulk UI reads each product from its own sheet
# in a single file. SP rows NEVER appear on the SB sheet and vice versa: each sheet mirrors
# its OWN header row from the uploaded workbook, since the SP and SB templates differ in
# both column count and column names. SB placement rows flagged advisory=True are excluded
# from the upload sheet by construction (see _sb_writable).
import json, argparse
from openpyxl import load_workbook, Workbook
from openpyxl.cell.cell import WriteOnlyCell

ID_COLS = {"campaign id", "ad group id", "portfolio id", "ad id", "keyword id",
           "product targeting id", "audience id"}

SP_SHEET = "Sponsored Products Campaigns"
SB_SHEET_CANDIDATES = ["sb multi ad group campaigns", "sponsored brands campaigns"]

def uploaded_headers(path):
    wb = load_workbook(path, data_only=True)
    ws = wb[SP_SHEET]
    hdr = [c.value for c in ws[1]]
    return hdr

def sb_uploaded_headers(path):
    """(sheet_name, header_row) for the SB sheet, or (None, None) if the workbook has none."""
    wb = load_workbook(path, data_only=True)
    by_lower = {n.lower().strip(): n for n in wb.sheetnames}
    for cand in SB_SHEET_CANDIDATES:
        if cand in by_lower:
            ws = wb[by_lower[cand]]
            hdr = [c.value for c in ws[1]]
            if any(h is not None for h in hdr):
                return by_lower[cand], hdr
    return None, None

def _sb_writable(p):
    """An SB placement change is written only when its placement label was recognised."""
    return not p.get("advisory")

def col_index(headers):
    return {(str(h).lower().strip() if h is not None else h): i for i, h in enumerate(headers)}

def blank_row(n):
    return ["" for _ in range(n)]

def setv(row, idx, name, value):
    j = idx.get(name.lower().strip())
    if j is not None:
        row[j] = value

def _product_of(rec):
    """The Product column MUST match the sheet the row lands on.

    The scorer stamps every change with product = "Sponsored Products" or
    "Sponsored Brands"; honour it. Hardcoding "Sponsored Products" here would put SP-labelled
    rows on the Sponsored Brands sheet, which Amazon rejects. Default only for legacy JSON
    written before v3, which was SP-only anyway.
    """
    return rec.get("product") or "Sponsored Products"

def _forward_row(c, headers, idx, below_min_policy, min_cpc, reverse):
    row = blank_row(len(headers))
    setv(row, idx, "product", _product_of(c))
    setv(row, idx, "operation", "Update")
    setv(row, idx, "campaign id", c["campaign_id"])
    if c.get("action") in ("bid", "pause"):
        setv(row, idx, "entity", c["entity"])
        setv(row, idx, "ad group id", c["ad_group_id"])
        # Informational-only columns, mirrored so the file reads the same as the one the
        # dashboard's in-browser writer produces.
        setv(row, idx, "campaign name (informational only)", c.get("campaign_name") or "")
        setv(row, idx, "ad group name (informational only)", c.get("ad_group_name") or "")
        if c["entity"] == "Keyword":
            setv(row, idx, "keyword id", c["keyword_id"])
            setv(row, idx, "keyword text", c.get("text"))
            setv(row, idx, "match type", c.get("match_type") or "")
        else:
            setv(row, idx, "product targeting id", c["keyword_id"])
            expr = str(c.get("text") or "")
            if not expr.startswith("keyword-group="):
                setv(row, idx, "product targeting expression", expr)
        was_paused = (c.get("action") == "pause") or (
            c.get("action") == "bid" and c.get("flag_below_min") and
            (below_min_policy == "pause" or (below_min_policy == "split" and c["orders"] == 0)))
        if reverse:
            # restore: bid back to old; re-enable anything the forward run paused
            setv(row, idx, "bid", c["current_bid"])
            if was_paused:
                setv(row, idx, "state", "enabled")
        else:
            if was_paused:
                setv(row, idx, "state", "paused")  # no bid on a paused row
            elif c.get("action") == "bid":
                nb = min_cpc if (c.get("flag_below_min") and below_min_policy == "floor") else c["new_bid"]
                setv(row, idx, "bid", nb)
    return row

# Amazon uses a DIFFERENT entity name per ad product for the placement row. Verified on a real
# export: the Sponsored Products sheet carries "Bidding Adjustment", the Sponsored Brands sheet
# carries "Bidding Adjustment by Placement". Writing SP's value onto the SB sheet gets the row
# rejected. The reader already matches on prefix, so our own output still round-trips.
SP_PLACEMENT_ENTITY = "Bidding Adjustment"
SB_PLACEMENT_ENTITY = "Bidding Adjustment by Placement"

def _placement_entity(p):
    return SB_PLACEMENT_ENTITY if _product_of(p) == "Sponsored Brands" else SP_PLACEMENT_ENTITY

def _placement_row(p, headers, idx, reverse):
    row = blank_row(len(headers))
    setv(row, idx, "product", _product_of(p))
    setv(row, idx, "operation", "Update")
    setv(row, idx, "entity", _placement_entity(p))
    setv(row, idx, "campaign id", p["campaign_id"])
    setv(row, idx, "placement", p["placement"])
    setv(row, idx, "percentage", p["current_pct"] if reverse else p["new_pct"])
    return row

def _budget_row(b, headers, idx, reverse):
    row = blank_row(len(headers))
    setv(row, idx, "product", _product_of(b))
    setv(row, idx, "operation", "Update")
    setv(row, idx, "entity", "Campaign")
    setv(row, idx, "campaign id", b["campaign_id"])
    setv(row, idx, "daily budget", b["old_budget"] if reverse else b["new_budget"])
    return row

def _append_sheet(wb, sheet_name, headers, rows):
    idx_id = {i for i, h in enumerate(headers) if (str(h).lower().strip() if h else "") in ID_COLS}
    ws = wb.create_sheet(sheet_name)
    ws.append(headers)
    for r in rows:
        out = []
        for i, v in enumerate(r):
            if v == "" or v is None:
                out.append("")
            elif i in idx_id:
                cell = WriteOnlyCell(ws, value=str(v)); cell.number_format = "@"; out.append(cell)
            else:
                out.append(v)
        ws.append(out)
    return len(rows)

def write_xlsx(path, sheets):
    """sheets: list of (sheet_name, headers, rows). One workbook, one sheet per ad product.

    A sheet with no rows is omitted entirely -- Amazon rejects a bulk file containing a
    header-only sheet for a product you are not updating.
    """
    wb = Workbook(write_only=True)
    total = 0
    written = []
    for name, headers, rows in sheets:
        if not rows or not headers: continue
        total += _append_sheet(wb, name, headers, rows)
        written.append({"sheet": name, "rows": len(rows), "columns": len(headers)})
    if not written:   # never save an empty workbook
        return 0, []
    wb.save(path)
    return total, written

def build(data, headers, reverse, below_min_policy, min_cpc):
    """Sponsored Products rows."""
    idx = col_index(headers)
    rows = []
    for c in data.get("changes", []):
        rows.append(_forward_row(c, headers, idx, below_min_policy, min_cpc, reverse))
    for p in data.get("placement_changes", []):
        rows.append(_placement_row(p, headers, idx, reverse))
    for b in data.get("budget_changes", []):
        rows.append(_budget_row(b, headers, idx, reverse))
    return rows

def build_sb(data, headers, reverse, below_min_policy, min_cpc):
    """Sponsored Brands rows -- same row builders, SB's own header row and policy.

    Note the below-min policy and Min CPC come from the SB config block, not SP's, because
    the operator may have given SB different floors.
    """
    sb = data.get("sb") or {}
    if not headers: return []
    idx = col_index(headers)
    rows = []
    for c in sb.get("changes", []):
        rows.append(_forward_row(c, headers, idx, below_min_policy, min_cpc, reverse))
    for p in sb.get("placement_changes", []):
        if not _sb_writable(p): continue      # advisory rows never reach the upload file
        rows.append(_placement_row(p, headers, idx, reverse))
    return rows

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="the uploaded bulk (for header mirroring)")
    ap.add_argument("--results", required=True, help="scorer JSON")
    ap.add_argument("--upload-xlsx", required=True)
    ap.add_argument("--reverse-xlsx", required=True)
    args = ap.parse_args()
    data = json.load(open(args.results, encoding="utf-8"))
    headers = uploaded_headers(args.input)
    cfg = data.get("config", {})
    bmp = cfg.get("below_min", "floor"); mn = cfg.get("min_cpc", 0.10)

    sb_cfg = (cfg.get("sb") or {})
    sb_bmp = sb_cfg.get("below_min", bmp)
    sb_mn = sb_cfg.get("min_cpc", mn)
    sb_sheet, sb_headers = (None, None)
    if data.get("sb"):
        sb_sheet, sb_headers = sb_uploaded_headers(args.input)

    fwd_sheets = [(SP_SHEET, headers, build(data, headers, False, bmp, mn))]
    rev_sheets = [(SP_SHEET, headers, build(data, headers, True, bmp, mn))]
    if sb_sheet:
        fwd_sheets.append((sb_sheet, sb_headers, build_sb(data, sb_headers, False, sb_bmp, sb_mn)))
        rev_sheets.append((sb_sheet, sb_headers, build_sb(data, sb_headers, True, sb_bmp, sb_mn)))

    n1, w1 = write_xlsx(args.upload_xlsx, fwd_sheets)
    n2, w2 = write_xlsx(args.reverse_xlsx, rev_sheets)
    print(json.dumps({"upload_rows": n1, "upload_sheets": w1,
                      "reverse_rows": n2, "reverse_sheets": w2,
                      "headers_mirrored": len(headers),
                      "sb_headers_mirrored": (len(sb_headers) if sb_headers else 0)}))

if __name__ == "__main__":
    main()
```

## Post-approval file outputs (final)

Two files to `the user's Downloads folder (resolve with `pathlib.Path.home() / 'Downloads'` - never hardcode)`. Tell the user explicitly which is which:

- **Upload to Amazon:** `bulk_upload_<source>_<timestamp>.xlsx`
- **Review only (do NOT upload):** `review_annotated_<source>_<timestamp>.xlsx`

Never give the user the xlsx as the upload path. openpyxl-mutated Amazon bulk xlsx files reliably fail Amazon's validation with "The input file is invalid or corrupt" because the rewritten ZIP loses `xl/sharedStrings.xml` and restructures the template in ways Amazon's parser rejects.

## HTML report

The HTML report MUST use the Sophie Society brand palette and typography - this is locked so every run produces a stylistically identical output. No ad-hoc styling by Claude. Use the generator below verbatim.

**Brand tokens (do not change):**
- Navy `#0A2333` (headers, primary)
- Off-white `#F3F3F1` (page bg)
- White `#FFFFFF` (card surfaces)
- Charcoal `#212121` (body)
- Green `#13835B` (positive / bid-up / CTA)
- Orange `#EA6C34` (attention / flags)
- Light Blue `#C2D9E6` (info highlights)
- Light Gray `#E6E6E6` (borders)
- Font: BROmega → Inter → system-ui fallback
- Radius: 12px cards, 8px buttons, 4px badges

```python
# render_report.py
import json, argparse, datetime, html

CSS = """
/* Sophie Society brand tokens (locked - do not change) */
:root{
  --navy:#0A2333;--off-white:#F3F3F1;--white:#FFFFFF;
  --text:#212121;--text-secondary:#666;--muted:#666;
  --green:#13835B;--orange:#EA6C34;
  --peach:#F9C8A5;--light-peach:#FDE5CF;--light-blue:#C2D9E6;--beige:#E9E2D9;
  --border:#E6E6E6;--dark-card:#1D1F1E;
  --r-sm:4px;--r-md:8px;--r-lg:12px;
  --shadow:0 2px 8px rgba(10,35,51,.08);
  /* Emil */
  --fw-normal:400;--fw-medium:500;--fw-bold:700;
  --ease-out:cubic-bezier(0.215,0.61,0.355,1);
  --ease:cubic-bezier(0.4,0,0.2,1);
  --dur-fast:120ms;--dur-base:180ms;
}
*{box-sizing:border-box}
html,body{margin:0;padding:0}
html{scroll-behavior:smooth}
@media (prefers-reduced-motion:reduce){
  html{scroll-behavior:auto}
  *,*::before,*::after{animation-duration:.01ms!important;transition-duration:.01ms!important}
}
body{
  font-family:'BROmega','BR Omega','Inter','DM Sans',-apple-system,system-ui,'Segoe UI',Roboto,sans-serif;
  background:var(--off-white);color:var(--text);font-size:15px;line-height:1.55;
  -webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale;text-rendering:optimizeLegibility;
}
a{color:var(--green);text-decoration:none;border-bottom:1px dotted var(--green)}
a:hover{border-bottom-style:solid}
code{font-family:SFMono-Regular,Consolas,monospace;font-size:12px}

/* Hero - eyebrow + h1 + subtitle on navy */
.hero{background:var(--navy);color:#fff;padding:48px 48px 32px}
.hero .wrap{max-width:1400px;margin:0 auto}
.hero .eyebrow{text-transform:uppercase;letter-spacing:.15em;font-size:12px;color:var(--peach);margin-bottom:10px;font-weight:var(--fw-bold)}
.hero h1{font-size:36px;font-weight:var(--fw-bold);margin:0 0 6px;text-wrap:balance;letter-spacing:-0.01em}
.hero p{font-size:14px;color:#b9c5cd;max-width:780px;margin:0}
.hero .config{display:flex;gap:8px;flex-wrap:wrap;margin-top:20px}
.hero .config span{background:rgba(255,255,255,.08);color:#C2D9E6;padding:5px 11px;border-radius:var(--r-sm);font-size:12px;font-variant-numeric:tabular-nums}

/* Sticky tab navigation */
nav.tabs{background:var(--white);border-bottom:1px solid var(--border);position:sticky;top:0;z-index:10;display:flex;flex-wrap:wrap;padding:0 48px;box-shadow:var(--shadow)}
.tab-btn{background:transparent;border:0;padding:16px 18px;border-bottom:3px solid transparent;font:inherit;font-weight:var(--fw-bold);cursor:pointer;color:var(--text-secondary);font-size:14px;white-space:nowrap;transition:color var(--dur-fast) var(--ease),border-color var(--dur-fast) var(--ease);touch-action:manipulation}
.tab-btn:focus-visible{outline:2px solid var(--orange);outline-offset:-2px}
@media (hover:hover) and (pointer:fine){
  .tab-btn:hover{color:var(--navy)}
}
.tab-btn.active{color:var(--navy);border-bottom-color:var(--orange)}
.tab-btn .count{display:inline-block;margin-left:6px;font-size:11px;padding:2px 7px;background:var(--off-white);color:var(--text-secondary);border-radius:999px;font-variant-numeric:tabular-nums}
.tab-btn.active .count{background:var(--navy);color:#fff}
.tab-panel{display:none}.tab-panel.active{display:block}
.tab-inner{max-width:1400px;margin:0 auto;padding:28px 48px 64px}
.meta{color:var(--text-secondary);font-size:13px;margin:0 0 16px}

h2{color:var(--navy);font-size:22px;font-weight:var(--fw-bold);margin:0 0 14px;text-wrap:balance}
h3{color:var(--navy);font-size:17px;font-weight:var(--fw-bold);margin:24px 0 10px;text-wrap:balance}

.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:14px;margin:0 0 28px}
.card{background:var(--white);border:1px solid var(--border);border-radius:var(--r-lg);padding:20px;box-shadow:var(--shadow);transition:box-shadow var(--dur-base) var(--ease),transform var(--dur-base) var(--ease)}
.card .label{font-size:11px;color:var(--text-secondary);text-transform:uppercase;letter-spacing:.1em;margin-bottom:8px;font-weight:var(--fw-bold)}
.card .value{font-size:28px;font-weight:var(--fw-bold);color:var(--navy);font-variant-numeric:tabular-nums;line-height:1.2}
.card .value.green{color:var(--green)}
.card .value.orange{color:var(--orange)}
.card .sublabel{font-size:12px;color:var(--text-secondary);margin-top:6px}
@media (hover:hover) and (pointer:fine){
  .card:hover{box-shadow:0 6px 16px rgba(10,35,51,.12);transform:translateY(-1px)}
}

.table-scroll{overflow-x:auto;border-radius:var(--r-lg)}
table{width:100%;min-width:760px;border-collapse:collapse;background:var(--white);border-radius:var(--r-lg);overflow:hidden;border:1px solid var(--border);box-shadow:var(--shadow)}
th{background:var(--navy);color:#fff;text-align:left;padding:11px 14px;font-size:11px;font-weight:var(--fw-bold);text-transform:uppercase;letter-spacing:.1em}
td{padding:11px 14px;border-bottom:1px solid var(--border);font-size:13px;vertical-align:top;font-variant-numeric:tabular-nums}
tr:last-child td{border-bottom:none}
tr:nth-child(even) td{background:#FAF9F5}
tbody tr{transition:background-color var(--dur-fast) var(--ease)}
@media (hover:hover) and (pointer:fine){
  tbody tr:hover td{background:var(--beige)}
}

.badge{display:inline-block;padding:2px 7px;border-radius:var(--r-sm);font-size:10px;font-weight:var(--fw-bold);text-transform:uppercase;letter-spacing:.08em}
.badge.high{background:#D6EDE3;color:var(--green)}
.badge.med{background:var(--light-peach);color:var(--orange)}
.badge.low{background:var(--light-blue);color:var(--navy)}
.badge.branded{background:var(--beige);color:var(--navy)}
.badge.strategic{background:var(--light-blue);color:var(--navy)}
.badge.lowdata{background:var(--beige);color:var(--navy)}
tr.row-lowdata td:first-child{border-left:3px solid var(--peach)}

/* Tab review indicator: an unvisited tab carries a dot, so "which tabs still need me" is
   visible at a glance instead of only being enforced by the disabled download button. */
.tab-btn .dot{display:inline-block;width:7px;height:7px;border-radius:50%;background:var(--orange);margin-left:7px;vertical-align:middle}
.tab-btn.seen .dot{background:var(--green);opacity:.35}
.tab-btn.seen .count{opacity:.75}

/* Sort + filter toolbar */
.tools{display:flex;gap:8px;flex-wrap:wrap;align-items:center;padding:10px 14px;background:var(--white);border:1px solid var(--border);border-radius:var(--r-md);margin:0 0 12px;box-shadow:var(--shadow)}
.tools .lbl{font-size:11px;font-weight:var(--fw-bold);text-transform:uppercase;letter-spacing:.1em;color:var(--text-secondary)}
.tools select{font:inherit;font-size:12px;padding:5px 8px;border:1px solid var(--border);border-radius:var(--r-sm);background:var(--white);color:var(--text)}
.tools .hits{font-size:12px;color:var(--text-secondary);font-variant-numeric:tabular-nums;margin-left:auto}
tr.row-filtered{display:none}

/* Save / resume */
.plan-bar{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin-top:14px;grid-column:1/-1}
.plan-bar .note{font-size:12px;color:#B8CAD5}
.btn-plan{display:inline-flex;align-items:center;min-height:36px;padding:8px 14px;border-radius:var(--r-md);border:1px solid rgba(255,255,255,.3);background:transparent;color:#fff;font:inherit;font-size:13px;font-weight:var(--fw-bold);cursor:pointer}
.btn-plan:hover{background:rgba(255,255,255,.08)}
tr.row-strategic td{background:#F2F7FA !important}
tr.row-strategic td:first-child{border-left:3px solid var(--navy)}
/* A strategic keep starts unticked, which would otherwise dim it to 45% via .row-off -- making
   the one row that most needs reading the faintest on the page. Keep it at full strength: it is
   deliberately unselected, not deselected. */
tr.row-strategic.row-off td{opacity:1}
tr.row-strategic td:nth-last-child(1){color:var(--navy) !important}
.strategic-banner{background:var(--light-blue);color:var(--navy);padding:14px 20px;border-radius:var(--r-md);font-size:14px;margin:0 0 14px;border-left:4px solid var(--navy);display:flex;align-items:flex-start;gap:12px}
.strategic-banner strong{font-weight:var(--fw-bold)}
.strategic-banner .icon{background:var(--navy);color:#fff;width:26px;height:26px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;font-weight:var(--fw-bold);flex-shrink:0;font-size:13px}
.badge.flag{background:#FEE4D8;color:var(--orange)}
.delta-up{color:var(--green);font-weight:var(--fw-bold);font-variant-numeric:tabular-nums}
.delta-dn{color:var(--orange);font-weight:var(--fw-bold);font-variant-numeric:tabular-nums}

.panel-head{display:flex;justify-content:space-between;align-items:center;gap:16px;flex-wrap:wrap;margin:0 0 12px}
.panel-head h2{margin:0}

.method-block{background:var(--white);border:1px solid var(--border);border-radius:var(--r-lg);padding:28px 32px;box-shadow:var(--shadow)}
.method-block h3{margin-top:0}
.method-block p{margin:8px 0 14px;font-size:14px;color:var(--text)}

.hint{color:var(--text-secondary);font-size:12px;margin-top:10px;font-style:italic}
.hint code{background:var(--beige);padding:2px 6px;border-radius:var(--r-sm);font-style:normal;color:var(--navy)}

/* Emil button */
.btn{
  display:inline-flex;align-items:center;justify-content:center;
  min-height:40px;padding:8px 18px;
  background:var(--green);color:#fff;border:none;border-radius:var(--r-md);
  font-family:inherit;font-size:13px;font-weight:var(--fw-bold);
  cursor:pointer;text-decoration:none;border-bottom:none;
  touch-action:manipulation;user-select:none;
  transition:background-color var(--dur-fast) var(--ease),box-shadow var(--dur-fast) var(--ease);
  box-shadow:0 1px 2px rgba(10,35,51,.08);
}
.btn:active{transform:translateY(1px);box-shadow:none}
.btn:focus-visible{outline:2px solid var(--orange);outline-offset:2px}
@media (hover:hover) and (pointer:fine){
  .btn:hover{background:#0E6D4C;box-shadow:0 2px 6px rgba(10,35,51,.12)}
}

/* Approval bar (dark card) */
.approve-bar{background:var(--dark-card);color:#fff;padding:22px 28px;border-radius:var(--r-lg);margin:32px 0 0;display:flex;justify-content:space-between;align-items:center;gap:20px;flex-wrap:wrap}
.approve-bar .msg{flex:1;min-width:280px}
.approve-bar .msg strong{color:#fff;font-size:16px;display:block;margin-bottom:4px;font-weight:var(--fw-bold)}
.approve-bar .msg span{color:#B8CAD5;font-size:13px}
.approve-bar code{background:rgba(255,255,255,.1);color:#fff;padding:2px 7px;border-radius:var(--r-sm);font-size:12px}

footer{color:var(--text-secondary);font-size:12px;padding:20px 48px;text-align:center;border-top:1px solid var(--border);background:var(--white)}

@media (max-width:900px){
  .hero{padding:32px 24px}
  nav.tabs{padding:0 16px}
  .tab-inner{padding:20px 20px 48px}
  footer{padding:16px 20px}
}

/* v2: selection + filter UI */
.filter-bar{display:flex;gap:10px;flex-wrap:wrap;align-items:center;padding:12px 14px;background:var(--white);border:1px solid var(--border);border-radius:var(--r-md);margin:0 0 14px;box-shadow:var(--shadow)}
.filter-bar .lbl{font-size:11px;font-weight:var(--fw-bold);text-transform:uppercase;letter-spacing:.1em;color:var(--text-secondary);margin-right:4px}
.chip-btn{display:inline-flex;align-items:center;gap:6px;padding:5px 11px;background:var(--off-white);border:1px solid var(--border);border-radius:999px;font:inherit;font-size:12px;cursor:pointer;user-select:none;touch-action:manipulation;transition:background-color var(--dur-fast) var(--ease)}
.chip-btn:hover{background:var(--beige)}
.chip-btn.active{background:var(--navy);color:#fff;border-color:var(--navy)}
.chip-btn .n{opacity:.7;font-size:11px}
.mini-btn{font:inherit;font-size:12px;font-weight:var(--fw-bold);background:var(--white);color:var(--navy);border:1px solid var(--border);padding:5px 10px;border-radius:var(--r-md);cursor:pointer;touch-action:manipulation}
.mini-btn:hover{background:var(--navy);color:#fff;border-color:var(--navy)}

/* Checkbox column */
th.chk, td.chk{width:36px;padding-left:12px;padding-right:4px;text-align:center}
input[type="checkbox"]{width:16px;height:16px;accent-color:var(--green);cursor:pointer;touch-action:manipulation}
tr.row-off td{opacity:.45}
tr.row-off td.chk{opacity:1}

/* Per-row below-min override */
select.bm-override{font:inherit;font-size:12px;padding:4px 6px;border:1px solid var(--border);border-radius:var(--r-sm);background:var(--white);color:var(--text);cursor:pointer;max-width:140px}
select.bm-override:focus-visible{outline:2px solid var(--orange);outline-offset:1px}

/* Editable bid / percentage inputs */
input.edit-bid, input.edit-pct{
  font:inherit;font-size:13px;font-weight:var(--fw-bold);
  width:70px;padding:4px 6px;
  border:1px solid var(--border);border-radius:var(--r-sm);
  background:var(--white);color:var(--navy);
  font-variant-numeric:tabular-nums;text-align:right;
  transition:border-color var(--dur-fast) var(--ease),background-color var(--dur-fast) var(--ease);
}
input.edit-pct{width:56px}
input.edit-bid:hover, input.edit-pct:hover{border-color:var(--navy)}
input.edit-bid:focus-visible, input.edit-pct:focus-visible{outline:2px solid var(--orange);outline-offset:1px;border-color:var(--orange)}
input.edit-bid.dirty, input.edit-pct.dirty{background:var(--light-peach);border-color:var(--orange)}
input.edit-bid.invalid, input.edit-pct.invalid{background:#FEE4D8;border-color:var(--orange);color:var(--orange)}
.arrow-sep{color:var(--text-secondary);margin:0 4px;font-weight:var(--fw-normal)}
.before-val{color:var(--text-secondary);font-variant-numeric:tabular-nums}

/* Download panel + review gate */
.download-panel{background:var(--dark-card);color:#fff;padding:28px 32px;border-radius:var(--r-lg);margin:0 0 24px;display:grid;grid-template-columns:minmax(0,1fr);gap:20px;align-items:start}
.download-panel .info strong{color:#fff;font-size:18px;display:block;margin-bottom:6px;font-weight:var(--fw-bold)}
.download-panel .info span{color:#B8CAD5;font-size:13px;line-height:1.5;max-width:80ch;display:block}
.download-panel .info .counter{display:block;margin-top:8px;font-size:12px;color:var(--peach);font-variant-numeric:tabular-nums}
.download-panel .actions{display:flex;gap:10px;flex-wrap:wrap;justify-content:flex-start;min-width:0}
.download-panel .upload-note{font-size:11px;color:#B8CAD5;margin-top:0;font-style:italic;grid-column:1/-1;max-width:80ch}
.btn-dl{display:inline-flex;align-items:center;justify-content:center;min-height:44px;padding:10px 22px;border:none;border-radius:var(--r-md);font-family:inherit;font-size:14px;font-weight:var(--fw-bold);cursor:pointer;touch-action:manipulation;user-select:none;white-space:nowrap;transition:background-color var(--dur-fast) var(--ease),box-shadow var(--dur-fast) var(--ease)}
.btn-dl.primary{background:var(--green);color:#fff}
.btn-dl.primary:hover:not(:disabled){background:#0E6D4C}
.btn-dl.secondary{background:transparent;color:#fff;border:1px solid rgba(255,255,255,.3)}
.btn-dl.secondary:hover:not(:disabled){background:rgba(255,255,255,.08)}
.btn-dl:active{transform:translateY(1px)}
.btn-dl:focus-visible{outline:2px solid var(--orange);outline-offset:2px}
.btn-dl:disabled{opacity:.4;cursor:not-allowed}
.gate-badge{display:inline-block;background:var(--orange);color:#fff;font-size:10px;font-weight:var(--fw-bold);text-transform:uppercase;letter-spacing:.1em;padding:2px 8px;border-radius:var(--r-sm);margin-left:8px}
@media (max-width:900px){
  .download-panel{grid-template-columns:1fr}
  .download-panel .actions{justify-content:stretch}
  .btn-dl{flex:1}
}
"""

METHOD_HTML = """
<div class="method">
<h3>The Sophie Society bidding method</h3>
<p><strong>Core formula:</strong> Target CPC = RPC x Target ACOS. RPC (Revenue Per Click) = Sales / Clicks over the report window.</p>
<p><strong>Confidence tiers:</strong> <span class="badge high">High</span> clicks and orders sufficient: direct RPC formula. <span class="badge med">Medium</span>: RPC if it has orders, otherwise a CPA projection that ratchets down with each non-converting click. <span class="badge low">Low</span>: small step using ad-group RPC. Tier thresholds vary by strategy.</p>
<p><strong>Strategy:</strong> one chosen strategy sets the dials (grace band, tier patience, step size, max-change up and down, pause patience, below-min policy, placement behavior). Balanced is the original behavior; Profit-First, Launch, Ranking Push, and ACOS-Targeted but CPC-Managed change the dials.</p>
<p><strong>Grace band:</strong> a converting keyword within the strategy band of target is left alone.</p>
<p><strong>Zero-click rule:</strong> a target with no clicks is never bid down, under any strategy. It has spent nothing, so a cut saves nothing and only makes a click less likely. What happens instead is the strategy's <code>zero_click</code> dial: <em>raise</em> (Balanced, Launch, Ranking Push) steps the bid up toward what a click is worth and stops there; <em>hold</em> (Profit-First, CPC-Managed) leaves it untouched rather than spend more on an unproven target.</p>
<p><strong>Safety rails:</strong> asymmetric max-change per run, Min and Max CPC floor and ceiling, rounded to 2 decimals, no-change rows dropped.</p>
<p><strong>Visibility floor:</strong> a converting keyword's max potential bid (base bid times one plus the campaign top placement modifier) stays at or above 75 percent of a reference CPC.</p>
<p><strong>Pause:</strong> a zero-order target pauses when clicks reach the strategy multiple of the clicks-to-order benchmark (separate for branded and non-branded, adjusted by match type). One order protects a target.</p>
<p><strong>Branded gate:</strong> branded keywords may step down but never up, and are excluded from negations.</p>
<p><strong>Placement modifiers:</strong> RPC-relative, increases capped at 15 points per run, decreases faster. The Amazon Business placement is left untouched.</p>
</div>
"""

CURRENCY_SYMBOL = "$"  # overridden per-render from cfg["currency_symbol"] - see render()
def fmt_money(x):
    try: return f"{CURRENCY_SYMBOL}{float(x):.2f}"
    except: return str(x)
def fmt_pct(x):
    try: return f"{float(x):.1%}" if abs(float(x))<2 else f"{float(x):.1f}%"
    except: return str(x)
def h(x): return html.escape(str(x)) if x is not None else ""

def render(data, src_name, out_path):
    c = data["counts"]; a = data["account"]; cfg = data["config"]
    ts = (datetime.datetime.fromisoformat(__import__("os").environ["SOPHIE_RUN_TS"]) if __import__("os").environ.get("SOPHIE_RUN_TS") else datetime.datetime.now()).strftime("%Y-%m-%d %H:%M")
    from collections import Counter as _Counter
    _bidc = [x for x in data["changes"] if x.get("action") == "bid"]
    _pausec = [x for x in data["changes"] if x.get("action") == "pause"]
    _budgetc = data.get("budget_changes", [])
    _byconf = _Counter(x.get("confidence") for x in _bidc)
    _ceiling = sum(1 for x in _bidc if x.get("flag_ceiling"))
    _strategy = data.get("strategy") or cfg.get("strategy", "balanced")
    _felix = data.get("felix_mode")
    _hdrs = data.get("headers") or []
    _labels = {"profit_first":"Profit-First","balanced":"Balanced","launch":"Launch / New Product","ranking":"Ranking Push","cpc_managed":"ACOS-Targeted but CPC-Managed"}
    _strategy_label = _labels.get(_strategy, _strategy)
    # ---- Sponsored Brands block (v3). Absent -> the SB tabs are not rendered at all. ----
    _sb = data.get("sb") or {}
    _sb_on = bool(_sb)
    _sbc = _sb.get("changes", []) if _sb_on else []
    _sb_bidc = [x for x in _sbc if x.get("action") == "bid"]
    _sb_pausec = [x for x in _sbc if x.get("action") == "pause"]
    _sb_pl = _sb.get("placement_changes", []) if _sb_on else []
    _sb_neg = _sb.get("negations", []) if _sb_on else []
    _sb_meta = _sb.get("meta") or {}
    _sb_counts = _sb_meta.get("counts", {})
    _sb_cfg = _sb_meta.get("config", {})
    _sb_hdrs = data.get("sb_headers") or []
    _sb_sheet = data.get("sb_sheet") or "Sponsored Brands Campaigns"
    _sb_byfmt = _sb_meta.get("by_ad_format", {})
    _sb_matches = _sb_meta.get("matches_sp")
    _sb_strategy_label = _labels.get(_sb_meta.get("strategy"), _sb_meta.get("strategy") or "")
    _warnings = data.get("warnings", [])
    # Currency symbol for the report - comes from config if set, defaults to $.
    # Chat flow can ask for this; scorer persists it into config.
    global CURRENCY_SYMBOL
    CURRENCY_SYMBOL = cfg.get("currency_symbol") or "$"

    cards = f"""
    <div class="cards">
      <div class="card"><div class="label">Bid changes</div><div class="value">{c['bid_changes']}</div><div class="sublabel">{_byconf.get('High',0)} High · {_byconf.get('Medium',0)} Med · {_byconf.get('Low',0)} Low</div></div>
      <div class="card"><div class="label">Pauses</div><div class="value orange">{c.get('pauses',0)}</div><div class="sublabel">Zero-order targets</div></div>
      <div class="card"><div class="label">Placement changes</div><div class="value">{c['placement_changes']}</div><div class="sublabel">Max +15pp per run</div></div>
      <div class="card"><div class="label">Budget changes</div><div class="value">{c.get('budget_changes',0)}</div><div class="sublabel">Budget moves</div></div>
      <div class="card"><div class="label">Negation candidates</div><div class="value orange">{c['negations']}</div><div class="sublabel">Advisory &middot; {c.get('negations_distinct_terms', c['negations'])} distinct term(s){(' &middot; ' + str(c['negations_strategic']) + ' strategic keep') if c.get('negations_strategic') else ''}</div></div>
      <div class="card"><div class="label">Branded bid-ups blocked</div><div class="value green">{c['branded_bid_ups_blocked']}</div><div class="sublabel">Halo defended</div></div>
    </div>
    """

    baseline = f"""
    <div class="cards">
      <div class="card"><div class="label">Account AOV</div><div class="value">{fmt_money(a['aov'])}</div></div>
      <div class="card"><div class="label">Avg CPC</div><div class="value">{fmt_money(a['avg_cpc'])}</div></div>
      <div class="card"><div class="label">Enabled clicks</div><div class="value">{int(a['acct_clicks']):,}</div></div>
      <div class="card"><div class="label">Enabled orders</div><div class="value">{int(a['acct_orders']):,}</div></div>
      <div class="card"><div class="label">Clicks/order (non-branded)</div><div class="value">{a.get('cto_nonbranded') if a.get('cto_nonbranded') is not None else 'n/a'}</div></div>
    </div>
    """

    def conf_badge(t):
        cls = {"High":"high","Medium":"med","Low":"low"}[t]
        return f'<span class="badge {cls}">{t}</span>'

    def delta_cell(v):
        if v is None: return ""
        cls = "delta-up" if v > 0 else "delta-dn"
        sign = "+" if v > 0 else ""
        return f'<span class="{cls}">{sign}{v:.1f}%</span>'

    def bm_override(c, idx, tbl="bids"):
        if not c.get("flag_below_min"): return ""
        return (f'<select class="bm-override" data-tbl="{tbl}" data-idx="{idx}">'
                f'<option value="">default</option>'
                f'<option value="floor">Floor to Min</option>'
                f'<option value="pause">Pause</option>'
                f'<option value="keep">Keep below-min</option>'
                f'</select>')

    BRAND_BADGE = ' <span class="badge branded">Brand</span>'
    FLAG_MIN = ' <span class="badge flag">Below min</span>'
    FLAG_CEIL = ' <span class="badge flag">Ceiling</span>'

    def _bid_row(i, c):
        camp = h(c.get('campaign_name') or '')
        port = h(c.get('portfolio_name') or '')
        match = h(c.get('match_type') or c.get('entity') or '')
        brand_badge = BRAND_BADGE if c.get('is_branded') else ''
        flag_badges = (FLAG_MIN if c.get('flag_below_min') else '') + (FLAG_CEIL if c.get('flag_ceiling') else '')
        low = bool(c.get('low_data'))
        low_badge = " <span class='badge lowdata'>Low data</span>" if low else ""
        row_cls = " row-lowdata" if low else ""
        return (
            f"<tr class='{row_cls.strip()}' data-tbl='bids' data-idx='{i}' data-campaign='{camp}' data-portfolio='{port}' data-match='{match}' "
            f"data-conf='{c.get('confidence','')}' data-delta='{c.get('delta_pct') or 0}' "
            f"data-clicks='{int(c.get('clicks') or 0)}' data-spend='{float(c.get('sales') or 0)}' data-low='{1 if low else 0}'>"
            f"<td class='chk'><input type='checkbox' data-tbl='bids' data-idx='{i}' checked aria-label='Include this bid change'></td>"
            f"<td>{h(c.get('campaign_name'))}</td><td>{h(c.get('ad_group_name'))}</td>"
            f"<td>{h(c.get('text'))}{brand_badge}{low_badge}</td>"
            f"<td>{h(c.get('match_type') or c.get('entity'))}</td>"
            f"<td><span class='before-val'>{fmt_money(c['current_bid'])}</span>"
            f"<span class='arrow-sep'>→</span>"
            f"<input type='number' class='edit-bid' data-tbl='bids' data-idx='{i}' "
            f"data-initial='{c['new_bid']}' value='{c['new_bid']}' step='0.01' min='0.02' "
            f"inputmode='decimal' aria-label='New bid (editable)'></td>"
            f"<td><span class='delta-live' data-tbl='bids' data-idx='{i}'>{delta_cell(c.get('delta_pct'))}</span></td>"
            f"<td>{conf_badge(c['confidence'])}</td>"
            f"<td>{int(c['clicks'])} cl · {int(c['orders'])} ord · {fmt_money(c['sales'])}</td>"
            f"<td style='font-size:12px;color:var(--muted)'>{h(c['formula'])}{flag_badges}</td>"
            f"<td class='chk'>{bm_override(c, i)}</td></tr>"
        )

    _split_low = bool(cfg.get("low_data_tab", True))
    _is_low = lambda c: bool(c.get("low_data"))
    bid_rows = "".join(_bid_row(i, c) for i, c in enumerate(data["changes"])
                       if c.get("action") == "bid" and not (_split_low and _is_low(c))) or \
        "<tr><td colspan='11' style='text-align:center;color:var(--muted);padding:32px'>No bid changes.</td></tr>"
    lowdata_rows = "".join(_bid_row(i, c) for i, c in enumerate(data["changes"])
                           if c.get("action") == "bid" and _is_low(c)) or \
        "<tr><td colspan='11' style='text-align:center;color:var(--muted);padding:32px'>No low-data targets.</td></tr>"
    _n_low_sp = sum(1 for c in data["changes"] if c.get("action") == "bid" and _is_low(c))

    def _pl_row(i, p):
        camp = h(p.get('campaign_name') or '')
        new_badge = ' <span class="badge med">New modifier</span>' if p.get('creates_modifier') else ''
        return (
            f"<tr data-tbl='placements' data-idx='{i}' data-campaign='{camp}'>"
            f"<td class='chk'><input type='checkbox' data-tbl='placements' data-idx='{i}' checked aria-label='Include this placement change'></td>"
            f"<td>{h(p['campaign_name'])}</td><td>{h(p['placement'])}{new_badge}</td>"
            f"<td><span class='before-val'>{p['current_pct']:.0f}%</span>"
            f"<span class='arrow-sep'>→</span>"
            f"<input type='number' class='edit-pct' data-tbl='placements' data-idx='{i}' "
            f"data-initial='{int(p['new_pct'])}' value='{int(p['new_pct'])}' step='1' min='0' max='900' "
            f"inputmode='numeric' aria-label='New placement modifier % (editable)'>%</td>"
            f"<td>{fmt_money(p['placement_rpc'])}</td><td>{fmt_money(p['campaign_rpc'])}</td>"
            f"<td>{int(p['clicks'])}</td></tr>"
        )
    pl_rows = "".join(_pl_row(i, p) for i, p in enumerate(data["placement_changes"])) or \
        "<tr><td colspan='7' style='text-align:center;color:var(--muted);padding:32px'>No placement changes.</td></tr>"

    def _neg_row(i, n):
        camp = h(n.get('campaign_name') or '')
        strat = bool(n.get('strategic'))
        # Strategic keeps start UNTICKED. Ticking a negation row means "put it in my negation
        # worklist"; a researched term should only get there if the operator decides so.
        row_cls = " class='row-strategic'" if strat else ""
        chk_attr = "" if strat else " checked"
        strat_badge = " <span class='badge strategic'>Strategic keep</span>" if strat else ""
        return (
            f"<tr data-tbl='negations' data-idx='{i}' data-campaign='{camp}'{row_cls}>"
            f"<td class='chk'><input type='checkbox' data-tbl='negations' data-idx='{i}'"
            f"{chk_attr} aria-label='Include this negation'></td>"
            f"<td>{h(n['campaign_name'])}</td><td>{h(n['keyword_text'])}</td>"
            f"<td>{h(n['match_type'])}</td><td><strong>{h(n['customer_search_term'])}</strong>"
            f"{strat_badge}</td>"
            f"<td>{int(n['clicks'])}</td><td>{fmt_money(n['spend'])}</td>"
            f"<td style='font-size:12px;color:var(--muted)'>{h(n['reason'])}</td></tr>"
        )
    neg_rows = "".join(_neg_row(i, n) for i, n in enumerate(data["negations"])) or \
        "<tr><td colspan='8' style='text-align:center;color:var(--muted);padding:32px'>No negation candidates.</td></tr>"

    def _pause_row(i, c):
        return (
            f"<tr data-tbl='bids' data-idx='{i}' data-campaign='{h(c.get('campaign_name') or '')}'>"
            f"<td class='chk'><input type='checkbox' data-tbl='bids' data-idx='{i}' checked aria-label='Include this pause'></td>"
            f"<td>{h(c.get('campaign_name'))}</td><td>{h(c.get('ad_group_name'))}</td>"
            f"<td>{h(c.get('text'))}</td><td>{h(c.get('match_type') or c.get('entity'))}</td>"
            f"<td>{int(c['clicks'])} cl &middot; {int(c['orders'])} ord</td>"
            f"<td style='font-size:12px;color:var(--muted)'>{h(c.get('formula'))}</td></tr>"
        )
    pause_rows = "".join(_pause_row(i, c) for i, c in enumerate(data["changes"]) if c.get("action") == "pause") or \
        "<tr><td colspan='7' style='text-align:center;color:var(--muted);padding:32px'>No pauses.</td></tr>"

    def _budget_row(i, b):
        return (
            f"<tr data-tbl='budgets' data-idx='{i}' data-campaign='{h(b.get('campaign_name') or '')}'>"
            f"<td class='chk'><input type='checkbox' data-tbl='budgets' data-idx='{i}' checked aria-label='Include this budget change'></td>"
            f"<td>{h(b['campaign_name'])}</td>"
            f"<td><span class='before-val'>{fmt_money(b['old_budget'])}</span><span class='arrow-sep'>&rarr;</span>{fmt_money(b['new_budget'])}</td>"
            f"<td style='font-size:12px;color:var(--muted)'>{h(b.get('reason'))}</td></tr>"
        )
    budget_rows = "".join(_budget_row(i, b) for i, b in enumerate(_budgetc)) or \
        "<tr><td colspan='4' style='text-align:center;color:var(--muted);padding:32px'>No budget changes.</td></tr>"

    # Distinct campaigns & portfolios for the filter chip bar
    _campaigns = sorted({c.get('campaign_name') for c in data['changes'] if c.get('campaign_name')})
    _portfolios = sorted({c.get('portfolio_name') for c in data['changes'] if c.get('portfolio_name')}) if any(c.get('portfolio_name') for c in data['changes']) else []
    campaign_chips = "".join(f'<button class="chip-btn" data-filter="campaign" data-value="{h(x)}">{h(x)}</button>' for x in _campaigns)
    portfolio_chips = "".join(f'<button class="chip-btn" data-filter="portfolio" data-value="{h(x)}">{h(x)}</button>' for x in _portfolios)

    # ---------------- Sponsored Brands tables ----------------
    AF_BADGE = {"video": "high", "product_collection": "low", "store_spotlight": "branded",
                "unknown": "flag"}

    def af_badge(c):
        fmt = c.get("ad_format") or "unknown"
        return f'<span class="badge {AF_BADGE.get(fmt,"low")}">{h(c.get("ad_format_label") or fmt)}</span>'

    def _sb_bid_row(i, c):
        camp = h(c.get('campaign_name') or '')
        brand_badge = ' <span class="badge branded">Brand</span>' if c.get('is_branded') else ''
        flag_badges = (' <span class="badge flag">Below min</span>' if c.get('flag_below_min') else '') + \
                      (' <span class="badge flag">Ceiling</span>' if c.get('flag_ceiling') else '')
        low = bool(c.get('low_data'))
        low_badge = " <span class='badge lowdata'>Low data</span>" if low else ""
        row_cls = " row-lowdata" if low else ""
        return (
            f"<tr class='{row_cls.strip()}' data-tbl='sbbids' data-idx='{i}' data-campaign='{camp}' data-format='{h(c.get('ad_format') or '')}' "
            f"data-conf='{c.get('confidence','')}' data-delta='{c.get('delta_pct') or 0}' "
            f"data-clicks='{int(c.get('clicks') or 0)}' data-spend='{float(c.get('sales') or 0)}' data-low='{1 if low else 0}'>"
            f"<td class='chk'><input type='checkbox' data-tbl='sbbids' data-idx='{i}' checked aria-label='Include this SB bid change'></td>"
            f"<td>{af_badge(c)}</td>"
            f"<td>{h(c.get('campaign_name'))}</td><td>{h(c.get('ad_group_name'))}</td>"
            f"<td>{h(c.get('text'))}{brand_badge}{low_badge}</td>"
            f"<td>{h(c.get('match_type') or c.get('entity'))}</td>"
            f"<td><span class='before-val'>{fmt_money(c['current_bid'])}</span>"
            f"<span class='arrow-sep'>→</span>"
            f"<input type='number' class='edit-bid' data-tbl='sbbids' data-idx='{i}' "
            f"data-initial='{c['new_bid']}' value='{c['new_bid']}' step='0.01' min='0.02' "
            f"inputmode='decimal' aria-label='New SB bid (editable)'></td>"
            f"<td><span class='delta-live' data-tbl='sbbids' data-idx='{i}'>{delta_cell(c.get('delta_pct'))}</span></td>"
            f"<td>{conf_badge(c['confidence'])}</td>"
            f"<td>{int(c['clicks'])} cl · {int(c['orders'])} ord · {fmt_money(c['sales'])}</td>"
            f"<td style='font-size:12px;color:var(--muted)'>{h(c['formula'])}{flag_badges}</td>"
            f"<td class='chk'>{bm_override(c, i, 'sbbids')}</td></tr>"
        )
    sb_bid_rows = "".join(_sb_bid_row(i, c) for i, c in enumerate(_sbc)
                          if c.get("action") == "bid" and not (_split_low and _is_low(c))) or \
        "<tr><td colspan='12' style='text-align:center;color:var(--muted);padding:32px'>No Sponsored Brands bid changes.</td></tr>"
    sb_lowdata_rows = "".join(_sb_bid_row(i, c) for i, c in enumerate(_sbc)
                              if c.get("action") == "bid" and _is_low(c)) or \
        "<tr><td colspan='12' style='text-align:center;color:var(--muted);padding:32px'>No low-data Sponsored Brands targets.</td></tr>"
    _n_low_sb = sum(1 for c in _sbc if c.get("action") == "bid" and _is_low(c))

    def _sb_pause_row(i, c):
        return (
            f"<tr data-tbl='sbbids' data-idx='{i}' data-campaign='{h(c.get('campaign_name') or '')}'>"
            f"<td class='chk'><input type='checkbox' data-tbl='sbbids' data-idx='{i}' checked aria-label='Include this SB pause'></td>"
            f"<td>{af_badge(c)}</td>"
            f"<td>{h(c.get('campaign_name'))}</td><td>{h(c.get('ad_group_name'))}</td>"
            f"<td>{h(c.get('text'))}</td><td>{h(c.get('match_type') or c.get('entity'))}</td>"
            f"<td>{int(c['clicks'])} cl &middot; {int(c['orders'])} ord</td>"
            f"<td style='font-size:12px;color:var(--muted)'>{h(c.get('formula'))}</td></tr>"
        )
    sb_pause_rows = "".join(_sb_pause_row(i, c) for i, c in enumerate(_sbc) if c.get("action") == "pause") or \
        "<tr><td colspan='8' style='text-align:center;color:var(--muted);padding:32px'>No Sponsored Brands pauses.</td></tr>"

    def _sb_pl_row(i, p):
        adv = p.get("advisory")
        adv_badge = ' <span class="badge flag">Advisory only</span>' if adv else (
            ' <span class="badge med">New modifier</span>' if p.get("creates_modifier") else '')
        pct_cell = (f"<span class='before-val'>{p['current_pct']:.0f}%</span><span class='arrow-sep'>→</span>"
                    f"<strong>{int(p['new_pct'])}%</strong>") if adv else (
                    f"<span class='before-val'>{p['current_pct']:.0f}%</span>"
                    f"<span class='arrow-sep'>→</span>"
                    f"<input type='number' class='edit-pct' data-tbl='sbplacements' data-idx='{i}' "
                    f"data-initial='{int(p['new_pct'])}' value='{int(p['new_pct'])}' step='1' min='-99' max='99' "
                    f"inputmode='numeric' aria-label='New SB placement modifier % (editable)'>%")
        chk = ("<td class='chk'>&mdash;</td>" if adv else
               f"<td class='chk'><input type='checkbox' data-tbl='sbplacements' data-idx='{i}' checked aria-label='Include this SB placement change'></td>")
        return (
            f"<tr data-tbl='sbplacements' data-idx='{i}' data-campaign='{h(p.get('campaign_name') or '')}'{' class=row-off' if adv else ''}>"
            f"{chk}<td>{h(p.get('campaign_name'))}</td><td>{h(p['placement'])}{adv_badge}</td>"
            f"<td>{pct_cell}</td>"
            f"<td>{fmt_money(p['placement_rpc'])}</td><td>{fmt_money(p['campaign_rpc'])}</td>"
            f"<td>{int(p['clicks'])}</td>"
            f"<td style='font-size:12px;color:var(--muted)'>{h(p.get('advisory_reason') or '')}</td></tr>"
        )
    sb_pl_rows = "".join(_sb_pl_row(i, p) for i, p in enumerate(_sb_pl)) or \
        "<tr><td colspan='8' style='text-align:center;color:var(--muted);padding:32px'>No Sponsored Brands placement changes.</td></tr>"

    def _sb_neg_row(i, n):
        strat = bool(n.get('strategic'))
        row_cls = " class='row-strategic'" if strat else ""
        chk_attr = "" if strat else " checked"
        strat_badge = " <span class='badge strategic'>Strategic keep</span>" if strat else ""
        camp = h(n.get('campaign_name') or '')
        return (
            f"<tr data-tbl='sbnegations' data-idx='{i}' data-campaign='{camp}'{row_cls}>"
            f"<td class='chk'><input type='checkbox' data-tbl='sbnegations' data-idx='{i}'"
            f"{chk_attr} aria-label='Include this SB negation'></td>"
            f"<td>{h(n['campaign_name'])}</td><td>{h(n['keyword_text'])}</td>"
            f"<td>{h(n['match_type'])}</td><td><strong>{h(n['customer_search_term'])}</strong>"
            f"{strat_badge}</td>"
            f"<td>{int(n['clicks'])}</td><td>{fmt_money(n['spend'])}</td>"
            f"<td style='font-size:12px;color:var(--muted)'>{h(n['reason'])}</td></tr>"
        )
    sb_neg_rows = "".join(_sb_neg_row(i, n) for i, n in enumerate(_sb_neg)) or \
        "<tr><td colspan='8' style='text-align:center;color:var(--muted);padding:32px'>No Sponsored Brands negation candidates.</td></tr>"

    # Per-ad-format benchmark table: the evidence that each format was scored against itself
    def _fmt_bench_rows():
        if not _sb_byfmt:
            return "<tr><td colspan='9' style='text-align:center;color:var(--muted);padding:24px'>No Sponsored Brands rows.</td></tr>"
        out = []
        for fmt, v in _sb_byfmt.items():
            rpc = (v['sales'] / v['clicks']) if v['clicks'] else 0.0
            acos = (v['spend'] / v['sales']) if v['sales'] else None
            out.append(
                f"<tr><td><span class='badge {AF_BADGE.get(fmt,'low')}'>{h(v['label'])}</span></td>"
                f"<td>{v['enabled_targets']}</td><td>{int(v['clicks']):,}</td><td>{int(v['orders']):,}</td>"
                f"<td>{fmt_money(v['spend'])}</td><td>{fmt_money(v['sales'])}</td>"
                f"<td><strong>{fmt_money(rpc)}</strong></td>"
                f"<td>{(('%.0f%%' % (acos*100)) if acos is not None else 'n/a')}</td>"
                f"<td>{v['bid_changes']} bid · {v['pauses']} pause</td></tr>")
        return "".join(out)
    sb_bench_rows = _fmt_bench_rows()

    def _strategic_banner(rows, label):
        k = sum(1 for n in rows if n.get("strategic"))
        if not k: return ""
        return ("<div class='strategic-banner'><span class='icon'>!</span><div>"
                "<strong>%d %s term%s would have been negated but match%s your keyword research.</strong> "
                "They are sorted to the top and <strong>start unticked</strong>. These are terms you "
                "deliberately targeted that have not converted yet - raise the bid or move them to their "
                "own campaign rather than negating them." % (
                    k, label, "s" if k != 1 else "", "" if k != 1 else "es"))  + "</div></div>"
    sp_strategic_banner = _strategic_banner(data.get("negations", []), "Sponsored Products")
    sb_strategic_banner = _strategic_banner(_sb_neg, "Sponsored Brands")

    warnings_html = ""
    if _warnings:
        items = "".join(f"<li>{h(w)}</li>" for w in _warnings)
        warnings_html = (
            "<div style='background:var(--light-peach);border-left:4px solid var(--orange);"
            "border-radius:var(--r-md);padding:14px 18px;margin:0 0 20px'>"
            "<strong style='color:var(--navy);font-size:14px'>Notes from this run</strong>"
            f"<ul style='margin:8px 0 0;padding-left:20px;font-size:13px;line-height:1.6'>{items}</ul></div>")

    sb_cards = ""
    if _sb_on:
        sb_cards = f"""
    <h2>Sponsored Brands</h2>
    <p class="meta">Scored from the same workbook, on the <code>{h(_sb_sheet)}</code> sheet.
    Strategy: <strong>{h(_sb_strategy_label)}</strong> ·
    {'parameters match Sponsored Products' if _sb_matches else 'parameters differ from Sponsored Products'} ·
    Target ACOS {_sb_cfg.get('target_acos','?')}% · Min {fmt_money(_sb_cfg.get('min_cpc',0))} ·
    Max {fmt_money(_sb_cfg.get('max_cpc',0))} · pause patience &times;{_sb_meta.get('pause_patience_multiplier',1)} vs SP.</p>
    <div class="cards">
      <div class="card"><div class="label">SB bid changes</div><div class="value">{_sb_counts.get('bid_changes',0)}</div><div class="sublabel">Across {len(_sb_byfmt)} ad format(s)</div></div>
      <div class="card"><div class="label">SB pauses</div><div class="value orange">{_sb_counts.get('pauses',0)}</div><div class="sublabel">More patient than SP</div></div>
      <div class="card"><div class="label">SB placements</div><div class="value">{_sb_counts.get('placement_changes',0)}</div><div class="sublabel">{_sb_counts.get('placement_advisory',0)} advisory, not written</div></div>
      <div class="card"><div class="label">SB negations</div><div class="value orange">{_sb_counts.get('negations',0)}</div><div class="sublabel">Advisory</div></div>
      <div class="card"><div class="label">SB branded bid-ups blocked</div><div class="value green">{_sb_counts.get('branded_bid_ups_blocked',0)}</div><div class="sublabel">Halo defended</div></div>
    </div>
    <h3>Benchmarks by ad format</h3>
    <p class="meta">Each ad format is scored against its OWN revenue per click, never a blended
    Sponsored Brands average. A video keyword is compared with video, not with Product Collection.</p>
    <div class='table-scroll'><table><thead><tr><th>Ad format</th><th>Targets</th><th>Clicks</th><th>Orders</th><th>Spend</th><th>Sales</th><th>RPC</th><th>ACOS</th><th>Changes</th></tr></thead>
    <tbody>{sb_bench_rows}</tbody></table></div>
    """

    import hashlib as _hash
    data_json = json.dumps({
        "changes": data["changes"],
        "placement_changes": data["placement_changes"],
        "negations": data["negations"],
        "budget_changes": _budgetc,
        "headers": _hdrs,
        # --- Sponsored Brands: separate arrays, separate header row, separate sheet ---
        "sb_changes": _sbc,
        "sb_placements": _sb_pl,
        "sb_negations": _sb_neg,
        "sb_headers": _sb_hdrs,
        "sb_sheet": _sb_sheet,
        "sb_min_cpc": _sb_cfg.get("min_cpc"),
        "sb_below_min": _sb_cfg.get("below_min"),
        "hash": _hash.sha1(json.dumps([data["changes"], _sbc], sort_keys=True, default=str).encode()).hexdigest()[:12],
        "currency_symbol": cfg.get("currency_symbol", "$"),
    }, default=str)
    below_min_default_json = json.dumps(cfg.get("below_min", "floor"))
    min_cpc_json = json.dumps(cfg.get("min_cpc", 0.02))
    run_ts_json = json.dumps(
        __import__("os").environ.get("SOPHIE_RUN_TS")
        or datetime.datetime.now().isoformat(timespec="seconds"))

    # SB tabs are only emitted when SB was actually scored, so the review gate never asks
    # the operator to open a tab that does not exist.
    sb_tabs = "" if not _sb_on else (
        f'<button class="tab-btn" data-tab="sbbids" role="tab">SB Bids <span class="count">{_sb_counts.get("bid_changes",0) - (_n_low_sb if _split_low else 0)}</span><span class="dot"></span></button>'
        + (f'<button class="tab-btn" data-tab="sblowdata" role="tab">SB Low Data <span class="count">{_n_low_sb}</span><span class="dot"></span></button>' if _split_low else '')
        + f'<button class="tab-btn" data-tab="sbpauses" role="tab">SB Pauses <span class="count">{_sb_counts.get("pauses",0)}</span><span class="dot"></span></button>'
        f'<button class="tab-btn" data-tab="sbplacements" role="tab">SB Placements <span class="count">{len(_sb_pl)}</span><span class="dot"></span></button>'
        f'<button class="tab-btn" data-tab="sbnegations" role="tab">SB Negations <span class="count">{_sb_counts.get("negations",0)}</span><span class="dot"></span></button>')

    sb_panels = "" if not _sb_on else f"""
<section class="tab-panel" data-panel="sbbids">
  <div class="tab-inner">
    <div class="panel-head"><h2>Sponsored Brands bid changes</h2><button class="btn" onclick="exportCSV('sb_bid_changes')">Export this tab as CSV (audit only, do not upload)</button></div>
    <p class="meta">{_sb_counts.get('bid_changes',0)} Sponsored Brands target(s) move this run. Each row was scored against its OWN ad format's revenue per click - the Ad format column shows which benchmark applied.</p>
    <div class="filter-bar">
      <span class="lbl">Select</span>
      <button class="mini-btn" data-bulk="all" data-tbl="sbbids">All</button>
      <button class="mini-btn" data-bulk="none" data-tbl="sbbids">None</button>
      <button class="mini-btn" data-bulk="invert" data-tbl="sbbids">Invert</button>
    </div>
<div class="tools" data-tools="sbbids">
      <span class="lbl">Sort</span>
      <select data-sort="sbbids">
        <option value="">Original order</option>
        <option value="conf">Confidence (High first)</option>
        <option value="conf-asc">Confidence (Low first)</option>
        <option value="delta-desc">Biggest increase</option>
        <option value="delta-asc">Biggest decrease</option>
        <option value="clicks-desc">Most clicks</option>
        <option value="spend-desc">Most sales</option>
      </select>
      <span class="lbl" style="margin-left:8px">Show</span>
      <select data-filter="sbbids">
        <option value="">Everything</option>
        <option value="High">High confidence only</option>
        <option value="Medium">Medium confidence only</option>
        <option value="Low">Low confidence only</option>
        <option value="up">Increases only</option>
        <option value="down">Decreases only</option>
      </select>
      <span class="hits" data-hits="sbbids"></span>
    </div>
    <div class='table-scroll'><table><thead><tr><th class="chk"><input type="checkbox" data-select-all="sbbids" checked aria-label="Select all SB bid changes"></th><th>Ad format</th><th>Campaign</th><th>Ad Group</th><th>Keyword / Target</th><th>Match</th><th>Current → New</th><th>Δ</th><th>Conf</th><th>Performance</th><th>Formula</th><th class="chk" title="Below-min policy override">BM</th></tr></thead>
    <tbody id="tbody-sbbids">{sb_bid_rows}</tbody></table></div>
    <p class="hint">Sponsored Brands below-min policy is <code>{_sb_cfg.get('below_min','floor')}</code>. Override per-row via the <strong>BM</strong> column on flagged rows, exactly as on the Sponsored Products tab.</p>
  </div>
</section>

<section class="tab-panel" data-panel="sblowdata">
  <div class="tab-inner">
    <div class="panel-head"><h2>Sponsored Brands low-data targets</h2><button class="btn" onclick="exportCSV('sb_bid_changes')">Export this tab as CSV (audit only, do not upload)</button></div>
    <p class="meta">{_n_low_sb} target(s) with fewer than {_sb_cfg.get('clicks_med_min', cfg.get('clicks_med_min', 3))} clicks. Fewer clicks than this strategy needs for a medium-confidence call. These rows are <strong>never bid down</strong> — one or two clicks is not evidence, the target has spent almost nothing, and a cut mostly delays the click that would tell you something. Where the strategy allows it they step up toward what a click is worth at the ad group's revenue per click, capped at that value; Profit-First and CPC-Managed hold instead.</p>
    <div class="filter-bar">
      <span class="lbl">Select</span>
      <button class="mini-btn" data-bulk="all" data-tbl="sbbids">All</button>
      <button class="mini-btn" data-bulk="none" data-tbl="sbbids">None</button>
      <button class="mini-btn" data-bulk="invert" data-tbl="sbbids">Invert</button>
    </div>
    <div class='table-scroll'><table><thead><tr><th class="chk"><input type="checkbox" data-select-all="sbbids" checked aria-label="Select all SB low-data changes"></th><th>Ad format</th><th>Campaign</th><th>Ad Group</th><th>Keyword / Target</th><th>Match</th><th>Current → New</th><th>Δ</th><th>Conf</th><th>Performance</th><th>Formula</th><th class="chk">BM</th></tr></thead>
    <tbody id="tbody-sblowdata">{sb_lowdata_rows}</tbody></table></div>
  </div>
</section>

<section class="tab-panel" data-panel="sbpauses">
  <div class="tab-inner">
    <div class="panel-head"><h2>Sponsored Brands pauses</h2></div>
    <p class="meta">{_sb_counts.get('pauses',0)} zero-order Sponsored Brands target(s) flagged. SB needs
    <strong>&times;{_sb_meta.get('pause_patience_multiplier',1)}</strong> the evidence Sponsored Products does before a pause is proposed:
    SB keywords are fewer, dearer and often brand-defensive, and video in particular has a longer path to purchase.
    A target with at least one order is never auto-paused.</p>
    <div class="filter-bar"><span class="lbl">Select</span>
      <button class="mini-btn" data-bulk="all" data-tbl="sbbids">All</button>
      <button class="mini-btn" data-bulk="none" data-tbl="sbbids">None</button></div>
    <div class='table-scroll'><table><thead><tr><th class="chk"><input type="checkbox" data-select-all="sbbids" checked aria-label="Select all SB pauses"></th><th>Ad format</th><th>Campaign</th><th>Ad Group</th><th>Keyword / Target</th><th>Match</th><th>Performance</th><th>Reason</th></tr></thead>
    <tbody id="tbody-sbpauses">{sb_pause_rows}</tbody></table></div>
  </div>
</section>

<section class="tab-panel" data-panel="sbplacements">
  <div class="tab-inner">
    <div class="panel-head"><h2>Sponsored Brands placement changes</h2><button class="btn" onclick="exportCSV('sb_placements')">Export this tab as CSV (audit only, do not upload)</button></div>
    <p class="meta">{_sb_counts.get('placement_changes',0)} writable, {_sb_counts.get('placement_advisory',0)} advisory.</p>
    <p class="hint">Sponsored Brands placement labels are not identical to Sponsored Products'. A row whose
    placement label this skill has not confirmed against a real SB bulk is marked
    <strong>Advisory only</strong>: it is shown for your judgement and is <strong>excluded from the approved
    xlsx</strong>. We will not write a modifier to a live campaign when we cannot be sure what Amazon does with it.</p>
    <div class="filter-bar">
      <span class="lbl">Select</span>
      <button class="mini-btn" data-bulk="all" data-tbl="sbplacements">All</button>
      <button class="mini-btn" data-bulk="none" data-tbl="sbplacements">None</button>
      <button class="mini-btn" data-bulk="invert" data-tbl="sbplacements">Invert</button>
    </div>
    <div class='table-scroll'><table><thead><tr><th class="chk"><input type="checkbox" data-select-all="sbplacements" checked aria-label="Select all SB placement changes"></th><th>Campaign</th><th>Placement</th><th>Current → New</th><th>Placement RPC</th><th>Campaign RPC</th><th>Clicks</th><th>Note</th></tr></thead>
    <tbody id="tbody-sbplacements">{sb_pl_rows}</tbody></table></div>
  </div>
</section>

<section class="tab-panel" data-panel="sbnegations">
  <div class="tab-inner">
    <div class="panel-head"><h2>Sponsored Brands negation candidates</h2><button class="btn" onclick="exportCSV('sb_negations')">Export this tab as CSV (audit only, do not upload)</button></div>
    <p class="meta">{_sb_counts.get('negations',0)} Sponsored Brands search terms flagged - zero orders with either enough clicks to have bought one, or a CPC at least twice the SB average. Branded searches are never flagged.</p>
    <p class="hint">Advisory only - apply these by hand through Amazon's negative-keyword workflow. Nothing on this tab is written to your bulk upload.</p>
    {sb_strategic_banner}
    <div class="filter-bar">
      <span class="lbl">Select</span>
      <button class="mini-btn" data-bulk="all" data-tbl="sbnegations">All</button>
      <button class="mini-btn" data-bulk="none" data-tbl="sbnegations">None</button>
      <button class="mini-btn" data-bulk="invert" data-tbl="sbnegations">Invert</button>
    </div>
    <div class='table-scroll'><table><thead><tr><th class="chk">Add as negative<br><input type="checkbox" data-select-all="sbnegations"{'' if _sb_counts.get('negations_strategic') else ' checked'} aria-label="Select all SB negations"></th><th>Campaign</th><th>Keyword</th><th>Match</th><th>Customer search term</th><th>Clicks</th><th>Spend</th><th>Reason</th></tr></thead>
    <tbody id="tbody-sbnegations">{sb_neg_rows}</tbody></table></div>
  </div>
</section>
"""

    html_doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sophie Society · Bid Optimization · {h(src_name)}</title>
<style>{CSS}</style></head>
<body>

<div class="hero">
  <div class="wrap">
    <div class="eyebrow">Sophie Society · SP &amp; SB Bulk Bid Optimizer</div>
    <h1>Bid optimization report</h1>
    <p>Sophie Society bidding method applied to <strong>{h(src_name)}</strong> · generated {ts}</p>
    <div class="config">
      <span>Strategy: {h(_strategy_label)}{(' &middot; ' + h(_felix)) if _felix else ''}</span>
      <span>Target ACOS {cfg['target_acos']}%</span>
      <span>Min {fmt_money(cfg['min_cpc'])}</span>
      <span>Max {fmt_money(cfg['max_cpc'])}</span>
      <span>Window {cfg.get('window_days','?')}d</span>
      <span>Below-min: {cfg.get('below_min','floor')}</span>
      <span>Zero-click: {cfg.get('zero_click','raise')}</span>
    </div>
  </div>
</div>

<nav class="tabs" role="tablist">
  <button class="tab-btn active seen" data-tab="summary" role="tab">Summary</button>
  <button class="tab-btn" data-tab="bids" role="tab">SP Bids <span class="count">{c['bid_changes'] - (_n_low_sp if _split_low else 0)}</span><span class="dot" title="not reviewed yet"></span></button>
  {('<button class="tab-btn" data-tab="lowdata" role="tab">SP Low Data <span class="count">' + str(_n_low_sp) + '</span><span class="dot" title="not reviewed yet"></span></button>') if _split_low else ''}
  <button class="tab-btn" data-tab="pauses" role="tab">SP Pauses <span class="count">{c.get('pauses',0)}</span><span class="dot"></span></button>
  <button class="tab-btn" data-tab="placements" role="tab">SP Placements <span class="count">{c['placement_changes']}</span><span class="dot"></span></button>
  <button class="tab-btn" data-tab="budgets" role="tab">Budgets <span class="count">{c.get('budget_changes',0)}</span><span class="dot"></span></button>
  <button class="tab-btn" data-tab="negations" role="tab">SP Negations <span class="count">{c['negations']}</span><span class="dot"></span></button>
  {sb_tabs}
  <button class="tab-btn" data-tab="method" role="tab">Method<span class="dot"></span></button>
</nav>

<section class="tab-panel active" data-panel="summary">
  <div class="tab-inner">
    <div style="background:var(--light-blue);border-radius:var(--r-lg);padding:18px 22px;margin:0 0 22px">
      <strong style="color:var(--navy);font-size:15px">How to use this</strong>
      <ol style="margin:10px 0 0;padding-left:20px;line-height:1.7">
        <li>Open every tab once. Opening them all unlocks the download button below.</li>
        <li>Untick any change you do not want to apply, and edit a bid or percentage in place if needed. The header checkbox and the All / None / Invert buttons act on the tab you are looking at and nothing else.</li>
        <li>Sort or filter a table to work through it in order — confidence first is a good default. Sorting and filtering change only what you are looking at, never what gets exported.</li>
        <li>Tabs you have not opened yet carry an orange dot. Reviewing a long run in one sitting is optional: <strong>Save review plan</strong> keeps your ticks and edits in a file you can load back later.</li>
        <li>On this Summary tab, click <strong>Download approved xlsx (upload this to Amazon)</strong>.</li>
        <li>Upload that .xlsx in Amazon Ads, Bulk operations. Use <strong>Download reverse xlsx</strong> only if you need to undo the run.</li>
      </ol>
      <p style="margin:10px 0 0;font-size:12px;color:var(--text-secondary)">The green "Export this tab as CSV (audit only)" buttons are optional, just for viewing one tab in a spreadsheet. Do not upload a CSV to Amazon. Always review before uploading: this tool proposes changes, it does not replace your judgment.</p>
    </div>

    <div class="download-panel">
      <div class="info">
        <strong>Ready to ship?</strong>
        <span>Two ways to apply your ticked changes. <strong>Upload route:</strong> download the approved xlsx and upload it at Amazon Ads → Bulk operations — one file, a Sponsored Products sheet and a Sponsored Brands sheet. <strong>Push route:</strong> download the approved changes (.json) and hand it back to Claude to push the bids and placement modifiers straight to the account via Sophie Hub, for both ad products. Pauses and budget changes always go through the upload. The reverse xlsx rolls every ticked row back to its pre-change value.</span>
        <span class="counter" id="selection-counter">0 of 0 changes selected</span>
      </div>
      <div class="actions">
        <button class="btn-dl primary" id="btn-forward" disabled>Download approved xlsx (upload this to Amazon) <span class="gate-badge" id="gate-fwd">Review all tabs</span></button>
        <button class="btn-dl primary" id="btn-approved-json" disabled>Download approved changes (.json) <span class="gate-badge" id="gate-json">Review all tabs</span></button>
        <button class="btn-dl secondary" id="btn-reverse" disabled>Download reverse xlsx <span class="gate-badge" id="gate-rev">Review all tabs</span></button>
      </div>
      <div class="plan-bar">
        <button class="btn-plan" id="btn-save-plan">Save review plan (.json)</button>
        <label class="btn-plan" for="load-plan" style="cursor:pointer">Load a saved plan</label>
        <input type="file" id="load-plan" accept="application/json,.json" style="display:none">
        <span class="note">Your ticks and edits are already kept in this browser automatically. Saving a plan lets you stop halfway through a long review and pick it up later, or on another machine.</span>
      </div>
      <div class="upload-note"><strong>Human review is essential: this tool proposes changes, it does not replace your judgment. Review every tab and untick anything that does not fit. Do not blindly upload.</strong> Upload as-is to Amazon Ads (Bulk operations accepts .xlsx only). If you open the file in Excel for inspection, don't re-save - Excel can corrupt 15-digit Campaign IDs on save.</div>
    </div>

    {warnings_html}
    <h2>Sponsored Products</h2>
    {cards}
    <h2>Account baseline</h2>
    {baseline}
    {sb_cards}
  </div>
</section>

<section class="tab-panel" data-panel="bids">
  <div class="tab-inner">
    <div class="panel-head"><h2>Bid changes</h2><button class="btn" onclick="exportCSV('bid_changes')">Export this tab as CSV (audit only, do not upload)</button></div>
    <p class="meta">{c['bid_changes']} keyword / target rows will move - {_byconf.get('High',0)} High, {_byconf.get('Medium',0)} Medium, {_byconf.get('Low',0)} Low. Clamps: {c['below_min']} below-min flag, {_ceiling} ceiling-capped, {c['branded_bid_ups_blocked']} branded bid-ups blocked.</p>
    <div class="filter-bar">
      <span class="lbl">Select</span>
      <button class="mini-btn" data-bulk="all" data-tbl="bids">All</button>
      <button class="mini-btn" data-bulk="none" data-tbl="bids">None</button>
      <button class="mini-btn" data-bulk="invert" data-tbl="bids">Invert</button>
      <span class="lbl" style="margin-left:12px">By campaign</span>{campaign_chips or '<span style="font-size:12px;color:var(--text-secondary)">(no campaigns)</span>'}
    </div>
<div class="tools" data-tools="bids">
      <span class="lbl">Sort</span>
      <select data-sort="bids">
        <option value="">Original order</option>
        <option value="conf">Confidence (High first)</option>
        <option value="conf-asc">Confidence (Low first)</option>
        <option value="delta-desc">Biggest increase</option>
        <option value="delta-asc">Biggest decrease</option>
        <option value="clicks-desc">Most clicks</option>
        <option value="spend-desc">Most sales</option>
      </select>
      <span class="lbl" style="margin-left:8px">Show</span>
      <select data-filter="bids">
        <option value="">Everything</option>
        <option value="High">High confidence only</option>
        <option value="Medium">Medium confidence only</option>
        <option value="Low">Low confidence only</option>
        <option value="up">Increases only</option>
        <option value="down">Decreases only</option>
      </select>
      <span class="hits" data-hits="bids"></span>
    </div>
    <div class='table-scroll'><table><thead><tr><th class="chk"><input type="checkbox" data-select-all="bids" checked aria-label="Select all bid changes"></th><th>Campaign</th><th>Ad Group</th><th>Keyword / Target</th><th>Match</th><th>Current → New</th><th>Δ</th><th>Conf</th><th>Performance</th><th>Formula</th><th class="chk" title="Below-min policy override">BM</th></tr></thead>
    <tbody id="tbody-bids">{bid_rows}</tbody></table></div>
    <p class="hint">Below-min policy default is <code>{cfg.get('below_min','floor')}</code>. Override per-row via the <strong>BM</strong> column on flagged rows.</p>
  </div>
</section>

<section class="tab-panel" data-panel="lowdata">
  <div class="tab-inner">
    <div class="panel-head"><h2>Sponsored Products low-data targets</h2><button class="btn" onclick="exportCSV('bid_changes')">Export this tab as CSV (audit only, do not upload)</button></div>
    <p class="meta">{_n_low_sp} target(s) with fewer than {cfg.get('clicks_med_min', 3)} clicks. Fewer clicks than this strategy needs for a medium-confidence call. These rows are <strong>never bid down</strong> — one or two clicks is not evidence, the target has spent almost nothing, and a cut mostly delays the click that would tell you something. Where the strategy allows it they step up toward what a click is worth at the ad group's revenue per click, capped at that value; Profit-First and CPC-Managed hold instead.</p>
    <div class="filter-bar">
      <span class="lbl">Select</span>
      <button class="mini-btn" data-bulk="all" data-tbl="bids">All</button>
      <button class="mini-btn" data-bulk="none" data-tbl="bids">None</button>
      <button class="mini-btn" data-bulk="invert" data-tbl="bids">Invert</button>
    </div>
    <div class='table-scroll'><table><thead><tr><th class="chk"><input type="checkbox" data-select-all="bids" checked aria-label="Select all low-data changes"></th><th>Campaign</th><th>Ad Group</th><th>Keyword / Target</th><th>Match</th><th>Current → New</th><th>Δ</th><th>Conf</th><th>Performance</th><th>Formula</th><th class="chk">BM</th></tr></thead>
    <tbody id="tbody-lowdata">{lowdata_rows}</tbody></table></div>
  </div>
</section>

<section class="tab-panel" data-panel="pauses">
  <div class="tab-inner">
    <div class="panel-head"><h2>Pauses</h2></div>
    <p class="meta">{c.get('pauses',0)} zero-order target(s) flagged to pause: clicks reached the strategy multiple of the clicks-to-order benchmark. Targets with at least one order are never auto-paused.</p>
    <div class="filter-bar"><span class="lbl">Select</span>
      <button class="mini-btn" data-bulk="all" data-tbl="bids">All</button>
      <button class="mini-btn" data-bulk="none" data-tbl="bids">None</button></div>
    <div class='table-scroll'><table><thead><tr><th class="chk"><input type="checkbox" data-select-all="bids" checked aria-label="Select all pauses"></th><th>Campaign</th><th>Ad Group</th><th>Keyword / Target</th><th>Match</th><th>Performance</th><th>Reason</th></tr></thead>
    <tbody id="tbody-pauses">{pause_rows}</tbody></table></div>
  </div>
</section>

<section class="tab-panel" data-panel="placements">
  <div class="tab-inner">
    <div class="panel-head"><h2>Placement modifier changes</h2><button class="btn" onclick="exportCSV('placements')">Export this tab as CSV (audit only, do not upload)</button></div>
    <p class="meta">{c['placement_changes']} placement modifier(s) move this run. Ideal = (placement RPC ÷ campaign RPC − 1) × 100, floored at 0% (Amazon constraint). Increase caps per run: +15pp on Balanced and Launch, +5pp on Profit-First, +25pp on Ranking Push but on Top of Search only. Decreases may move up to −50pp. A placement at 0% can be created, and is badged <strong>New modifier</strong> when it would be.</p>
    <div class="filter-bar">
      <span class="lbl">Select</span>
      <button class="mini-btn" data-bulk="all" data-tbl="placements">All</button>
      <button class="mini-btn" data-bulk="none" data-tbl="placements">None</button>
      <button class="mini-btn" data-bulk="invert" data-tbl="placements">Invert</button>
    </div>
    <div class='table-scroll'><table><thead><tr><th class="chk"><input type="checkbox" data-select-all="placements" checked aria-label="Select all placement changes"></th><th>Campaign</th><th>Placement</th><th>Current → New</th><th>Placement RPC</th><th>Campaign RPC</th><th>Clicks</th></tr></thead>
    <tbody id="tbody-placements">{pl_rows}</tbody></table></div>
  </div>
</section>

<section class="tab-panel" data-panel="budgets">
  <div class="tab-inner">
    <div class="panel-head"><h2>Budget changes</h2></div>
    <p class="meta">{c.get('budget_changes',0)} campaign budget change(s). Daily mode raises budgets that spent out (never decreased) and needs a Yesterday bulk to do it; monthly mode reallocates toward higher-ROAS campaigns. Every other strategy leaves budgets alone entirely — an empty tab there means budgets are out of scope, not that nothing needed changing.</p>
    <div class="filter-bar"><span class="lbl">Select</span>
      <button class="mini-btn" data-bulk="all" data-tbl="budgets">All</button>
      <button class="mini-btn" data-bulk="none" data-tbl="budgets">None</button></div>
    <div class='table-scroll'><table><thead><tr><th class="chk"><input type="checkbox" data-select-all="budgets" checked aria-label="Select all budget changes"></th><th>Campaign</th><th>Current &rarr; New</th><th>Reason</th></tr></thead>
    <tbody id="tbody-budgets">{budget_rows}</tbody></table></div>
  </div>
</section>

<section class="tab-panel" data-panel="negations">
  <div class="tab-inner">
    <div class="panel-head"><h2>Negation candidates</h2><button class="btn" onclick="exportCSV('negations')">Export this tab as CSV (audit only, do not upload)</button></div>
    <p class="meta">{c['negations']} customer search terms flagged - zero orders with either enough clicks to have bought one, or a CPC at least twice the account average, and the search term differs from the keyword text. Branded searches are never flagged.</p>
    <p class="hint">These are advisory only — apply them by hand through Amazon's negative-keyword workflow. Nothing on this tab is written to your bulk upload; ticking rows just chooses which appear in the audit CSV.</p>
    {sp_strategic_banner}
    <div class="filter-bar">
      <span class="lbl">Select</span>
      <button class="mini-btn" data-bulk="all" data-tbl="negations">All</button>
      <button class="mini-btn" data-bulk="none" data-tbl="negations">None</button>
      <button class="mini-btn" data-bulk="invert" data-tbl="negations">Invert</button>
    </div>
    <div class='table-scroll'><table><thead><tr><th class="chk">Add as negative<br><input type="checkbox" data-select-all="negations"{'' if c.get('negations_strategic') else ' checked'} aria-label="Select all negations"></th><th>Campaign</th><th>Keyword</th><th>Match</th><th>Customer search term</th><th>Clicks</th><th>Spend</th><th>Reason</th></tr></thead>
    <tbody id="tbody-negations">{neg_rows}</tbody></table></div>
  </div>
</section>
{sb_panels}
<section class="tab-panel" data-panel="method">
  <div class="tab-inner">
    <h2>The Sophie Society bidding method</h2>
    <p class="meta">The full methodology the scorer applies - deterministic, same inputs produce byte-identical decisions.</p>
    {METHOD_HTML}
  </div>
</section>

<footer>Generated by the Sophie Society SP &amp; SB Bulk Bid Optimizer · deterministic output · {ts}</footer>

<script>
const DATA = {data_json};
const BELOW_MIN_DEFAULT = {below_min_default_json};
const MIN_CPC = {min_cpc_json};
// Sponsored Products column order, mirrored from the uploaded workbook's SP sheet
const MIRROR_COLS = DATA.headers || [];
const MIRROR_L = MIRROR_COLS.map(x=>String(x).toLowerCase().trim());
// Sponsored Brands has a DIFFERENT template (different columns, different count), so it
// carries its own mirrored header row and writes to its own sheet in the upload workbook.
const SB_MIRROR_COLS = DATA.sb_headers || [];
const SB_MIRROR_L = SB_MIRROR_COLS.map(x=>String(x).toLowerCase().trim());
const SB_SHEET_NAME = DATA.sb_sheet || 'Sponsored Brands Campaigns';
const SB_MIN_CPC = (DATA.sb_min_cpc == null ? MIN_CPC : DATA.sb_min_cpc);
const SB_BELOW_MIN_DEFAULT = DATA.sb_below_min || BELOW_MIN_DEFAULT;
const SP_SHEET_NAME = 'Sponsored Products Campaigns';
// Run stamps come from the GENERATOR (SOPHIE_RUN_TS), not the viewer's browser clock, so
// downloaded filenames and the approved-JSON timestamp are stable across machines and
// timezones. This closes the client-side clock leak flagged in the output contract.
const RUN_TS = {run_ts_json};
const RUN_DATE = RUN_TS.slice(0,10);

// Preview-CSV column sets (for per-tab audit exports)
const PREV_COLS = {{
  bid_changes:['applied','campaign_name','ad_group_name','text','match_type','entity','current_bid','new_bid','delta_pct','confidence','clicks','orders','sales','formula','is_branded','flag_below_min','flag_ceiling'],
  placements:['campaign_name','placement','current_pct','new_pct','placement_rpc','campaign_rpc','clicks'],
  negations:['strategic','campaign_name','ad_group_name','keyword_text','match_type','customer_search_term','clicks','spend','reason'],
  sb_bid_changes:['applied','ad_format_label','campaign_name','ad_group_name','text','match_type','entity','current_bid','new_bid','delta_pct','confidence','clicks','orders','sales','formula','is_branded','flag_below_min','flag_ceiling'],
  sb_placements:['ad_format','campaign_name','placement','current_pct','new_pct','placement_rpc','campaign_rpc','clicks','advisory','advisory_reason'],
  sb_negations:['strategic','campaign_name','ad_group_name','keyword_text','match_type','customer_search_term','clicks','spend','reason']
}};

function csvEscape(v){{ if(v==null) return ''; const s=String(v); return /[",\\n]/.test(s)?'"'+s.replace(/"/g,'""')+'"':s; }}
function toCSV(rows, cols){{
  if(!rows.length) return cols.join(',')+'\\n';
  return [cols.join(',')].concat(rows.map(r=>cols.map(c=>csvEscape(r[c])).join(','))).join('\\n');
}}
function downloadFile(name, data, mime){{
  const blob = (data instanceof Uint8Array) ? new Blob([data], {{type:mime}}) : new Blob([data], {{type:mime}});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = name;
  document.body.appendChild(a); a.click(); document.body.removeChild(a);
  URL.revokeObjectURL(url);
}}

// Preview CSV download (per-tab audit) - stays CSV for quick spreadsheet auditing
function exportCSV(key){{
  // Export only the ticked rows, with the operator's current edits applied, so the CSV
  // matches what the approved xlsx will contain (not the raw proposal).
  const TBL_FOR = {{bid_changes:'bids', placements:'placements', negations:'negations',
                   sb_bid_changes:'sbbids', sb_placements:'sbplacements', sb_negations:'sbnegations'}};
  const tbl = TBL_FOR[key] || key;
  const ticked = i => {{ const cb=document.querySelector(`input[type=checkbox][data-tbl='${{tbl}}'][data-idx='${{i}}']`); return cb && cb.checked; }};
  const isSb = key.indexOf('sb_') === 0;
  const floor = isSb ? SB_MIN_CPC : MIN_CPC;
  const bmDefault = isSb ? SB_BELOW_MIN_DEFAULT : BELOW_MIN_DEFAULT;
  let data;
  if(key==='bid_changes' || key==='sb_bid_changes'){{
    const src = isSb ? (DATA.sb_changes||[]) : DATA.changes;
    data = src.map((c,i)=>[c,i]).filter(([c,i])=>ticked(i)).map(([c,i])=>{{
      if(c.action==='pause') return {{...c, new_bid:'', applied:'pause'}};
      const nb = editedBid(i, c.new_bid, tbl);
      const sel = document.querySelector(`select.bm-override[data-tbl='${{tbl}}'][data-idx='${{i}}']`)
               || (isSb ? null : document.querySelector(`select.bm-override[data-idx='${{i}}']`));
      const policy = (sel && sel.value) || bmDefault;
      let applied='bid', outBid=nb;
      if(nb < floor){{ if(policy==='pause'){{ applied='pause'; outBid=''; }} else if(policy!=='keep'){{ outBid=floor; }} }}
      return {{...c, new_bid:outBid, applied}};
    }});
  }} else if(key==='placements' || key==='sb_placements'){{
    const src = isSb ? (DATA.sb_placements||[]) : DATA.placement_changes;
    // Advisory SB rows have no editable input; export them as proposed, clearly flagged.
    data = src.map((p,i)=>[p,i]).filter(([p,i])=>p.advisory || ticked(i))
              .map(([p,i])=>({{...p, new_pct: p.advisory ? p.new_pct : editedPct(i,p.new_pct,tbl)}}));
  }} else {{
    const src = isSb ? (DATA.sb_negations||[]) : DATA.negations;
    data = src.filter((n,i)=>ticked(i));
  }}
  downloadFile(key+'_approved_'+RUN_DATE+'.csv', toCSV(data, PREV_COLS[key]), 'text/csv;charset=utf-8');
}}

// ========== Minimal inline xlsx writer ==========
// Amazon Ads Bulk UI accepts xlsx only. We build a fresh workbook (5 XML files in a ZIP)
// - no template inheritance, no shared strings, no styles beyond text-format for ID columns.
// CRC-32 table for ZIP
const CRC_TBL = (() => {{
  const t = new Uint32Array(256);
  for (let i = 0; i < 256; i++) {{
    let c = i;
    for (let j = 0; j < 8; j++) c = (c & 1) ? (0xEDB88320 ^ (c >>> 1)) : (c >>> 1);
    t[i] = c >>> 0;
  }}
  return t;
}})();
function crc32(bytes){{
  let c = 0xFFFFFFFF;
  for (let i = 0; i < bytes.length; i++) c = CRC_TBL[(c ^ bytes[i]) & 0xFF] ^ (c >>> 8);
  return (c ^ 0xFFFFFFFF) >>> 0;
}}
const TE = new TextEncoder();
function zipStored(files){{
  // files: [[name, string|Uint8Array], ...] - stored (no compression), ZIP spec
  const parts = []; const central = []; let offset = 0;
  for (const [name, content] of files) {{
    const nameBytes = TE.encode(name);
    const data = typeof content === 'string' ? TE.encode(content) : content;
    const crc = crc32(data);
    const lfh = new Uint8Array(30 + nameBytes.length);
    const dv = new DataView(lfh.buffer);
    dv.setUint32(0, 0x04034b50, true);
    dv.setUint16(4, 20, true);  dv.setUint16(6, 0, true);
    dv.setUint16(8, 0, true);   // compression = stored
    dv.setUint16(10, 0, true);  dv.setUint16(12, 0x0021, true); // fixed time/date
    dv.setUint32(14, crc, true);
    dv.setUint32(18, data.length, true);
    dv.setUint32(22, data.length, true);
    dv.setUint16(26, nameBytes.length, true);
    dv.setUint16(28, 0, true);
    lfh.set(nameBytes, 30);
    parts.push(lfh, data);
    central.push({{nameBytes, crc, size: data.length, offset}});
    offset += lfh.length + data.length;
  }}
  const cdParts = []; let cdSize = 0;
  for (const e of central) {{
    const cdh = new Uint8Array(46 + e.nameBytes.length);
    const dv = new DataView(cdh.buffer);
    dv.setUint32(0, 0x02014b50, true);
    dv.setUint16(4, 20, true);   dv.setUint16(6, 20, true);
    dv.setUint16(8, 0, true);    dv.setUint16(10, 0, true);
    dv.setUint16(12, 0, true);   dv.setUint16(14, 0x0021, true);
    dv.setUint32(16, e.crc, true);
    dv.setUint32(20, e.size, true);
    dv.setUint32(24, e.size, true);
    dv.setUint16(28, e.nameBytes.length, true);
    dv.setUint16(30, 0, true);   dv.setUint16(32, 0, true);
    dv.setUint16(34, 0, true);   dv.setUint16(36, 0, true);
    dv.setUint32(38, 0, true);
    dv.setUint32(42, e.offset, true);
    cdh.set(e.nameBytes, 46);
    cdParts.push(cdh);
    cdSize += cdh.length;
  }}
  const eocd = new Uint8Array(22);
  const dv = new DataView(eocd.buffer);
  dv.setUint32(0, 0x06054b50, true);
  dv.setUint16(4, 0, true);    dv.setUint16(6, 0, true);
  dv.setUint16(8, central.length, true);
  dv.setUint16(10, central.length, true);
  dv.setUint32(12, cdSize, true);
  dv.setUint32(16, offset, true);
  dv.setUint16(20, 0, true);
  const total = parts.reduce((s, p) => s + p.length, 0) + cdSize + 22;
  const out = new Uint8Array(total);
  let pos = 0;
  for (const p of parts) {{ out.set(p, pos); pos += p.length; }}
  for (const p of cdParts) {{ out.set(p, pos); pos += p.length; }}
  out.set(eocd, pos);
  return out;
}}
function xmlEsc(s){{ return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/[\\x00-\\x08\\x0B\\x0C\\x0E-\\x1F]/g,''); }}
function colLetter(n){{ let s = ''; while (n > 0) {{ n--; s = String.fromCharCode(65 + (n % 26)) + s; n = Math.floor(n / 26); }} return s; }}
const ID_COLS = new Set(["campaign id","ad group id","portfolio id","ad id","keyword id","product targeting id","audience id"]);
function sheetXmlFor(cols, rows){{
  // Cells: numbers go as <c><v>N</v></c>, strings as <c t="inlineStr"><is><t>S</t></is></c>
  // ID columns always go as inline strings (preserve 15+ digit precision)
  const rowsXml = [];
  // Header row (row 1) -- mirrors THIS sheet's own header row from the uploaded workbook
  rowsXml.push('<row r="1">' + cols.map((h, i) =>
    `<c r="${{colLetter(i+1)}}1" t="inlineStr"><is><t>${{xmlEsc(h)}}</t></is></c>`
  ).join('') + '</row>');
  // Data rows
  rows.forEach((row, rIdx) => {{
    const r = rIdx + 2;
    const cells = cols.map((h, cIdx) => {{
      const v = row[String(h).toLowerCase().trim()];
      if (v === '' || v == null) return '';
      const ref = colLetter(cIdx+1) + r;
      const forceStr = ID_COLS.has(String(h).toLowerCase().trim());
      if (!forceStr && typeof v === 'number') return `<c r="${{ref}}"><v>${{v}}</v></c>`;
      if (!forceStr && typeof v === 'string' && /^-?\\d+(\\.\\d+)?$/.test(v) && Math.abs(Number(v)) < 1e15) {{
        return `<c r="${{ref}}"><v>${{v}}</v></c>`;
      }}
      return `<c r="${{ref}}" t="inlineStr"><is><t>${{xmlEsc(v)}}</t></is></c>`;
    }});
    rowsXml.push(`<row r="${{r}}">${{cells.join('')}}</row>`);
  }});
  return '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' +
    '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">' +
    `<sheetData>${{rowsXml.join('')}}</sheetData></worksheet>`;
}}

// buildXlsx takes a LIST of sheets so one upload file can carry both ad products:
//   [{{name:'Sponsored Products Campaigns', cols:[...], rows:[...]}}, {{name:'SB ...', ...}}]
// Amazon's Bulk UI reads each product from its own sheet. Sheets with no rows are dropped --
// a header-only sheet for a product you are not updating gets the file rejected.
function buildXlsx(sheets){{
  const live = (sheets||[]).filter(s => s && s.cols && s.cols.length && s.rows && s.rows.length);
  if (!live.length) return null;
  const parts = [];
  const sheetEntries = [], overrides = [], relEntries = [];
  live.forEach((s, i) => {{
    const n = i + 1;
    parts.push([`xl/worksheets/sheet${{n}}.xml`, sheetXmlFor(s.cols, s.rows)]);
    sheetEntries.push(`<sheet name="${{xmlEsc(s.name)}}" sheetId="${{n}}" r:id="rId${{n}}"/>`);
    overrides.push(`<Override PartName="/xl/worksheets/sheet${{n}}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>`);
    relEntries.push(`<Relationship Id="rId${{n}}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet${{n}}.xml"/>`);
  }});
  const workbookXml = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' +
    '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" ' +
    'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">' +
    `<sheets>${{sheetEntries.join('')}}</sheets></workbook>`;
  const contentTypes = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' +
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">' +
    '<Default Extension="xml" ContentType="application/xml"/>' +
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>' +
    '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>' +
    overrides.join('') +
    '</Types>';
  const rootRels = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' +
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' +
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>' +
    '</Relationships>';
  const workbookRels = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' +
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' +
    relEntries.join('') +
    '</Relationships>';
  return zipStored([
    ['[Content_Types].xml', contentTypes],
    ['_rels/.rels', rootRels],
    ['xl/workbook.xml', workbookXml],
    ['xl/_rels/workbook.xml.rels', workbookRels],
  ].concat(parts));
}}

// ========== Upload row builder (feeds buildXlsx below) ==========
// Returns a blank row template keyed by ONE sheet's lowercased header row.
// SP and SB have different templates, so always pass the right column list.
function emptyRow(colsL){{ const o={{}}; (colsL||MIRROR_L).forEach(c=>o[c]=''); return o; }}
function sbEmptyRow(){{ return emptyRow(SB_MIRROR_L); }}

// Below-min resolution for one bid change. minCpc differs per product when the operator
// gave Sponsored Brands its own floor.
// Below-min resolution. MUST mirror apply_changes_v3.py exactly -- the two routes are documented
// as producing identical rows, and an operator downloads the browser one. 'split' was missing
// here and fell through to floor, so on Profit-First the downloaded file KEPT six targets running
// at the floor that the Python route paused. Opposite actions on the same rows.
//   pause  -> always pause
//   split  -> pause when the target has no orders, otherwise leave the below-min bid alone
//   keep   -> leave the below-min bid alone
//   floor  -> raise to Min CPC
function resolveBidRow(c, policy, minCpc){{
  const floor = (minCpc == null ? MIN_CPC : minCpc);
  let newBid = c.new_bid, state = '';
  if(c.flag_below_min){{
    if(policy === 'pause'){{ state='paused'; newBid=''; }}
    else if(policy === 'split'){{
      if(Number(c.orders) === 0){{ state='paused'; newBid=''; }}
    }}
    else if(policy === 'keep'){{ /* use new_bid as-is */ }}
    else {{ newBid = floor; }}
  }}
  return {{newBid, state}};
}}

// Read the operator's edited bid for row i (if valid), else fall back to c.new_bid.
// tbl selects which table's inputs to read: 'bids' (SP) or 'sbbids' (SB).
function editedBid(i, fallback, tbl){{
  const t = tbl || 'bids';
  const inp = document.querySelector(`input.edit-bid[data-tbl='${{t}}'][data-idx='${{i}}']`);
  if(!inp || inp.classList.contains('invalid')) return fallback;
  const v = parseFloat(inp.value);
  return (Number.isFinite(v) && v > 0) ? Number(v.toFixed(2)) : fallback;
}}
// Sponsored Brands placement modifiers are SIGNED; Sponsored Products' are 0..900.
function pctRange(tbl){{ return tbl === 'sbplacements' ? [-99, 99] : [0, 900]; }}
function editedPct(i, fallback, tbl){{
  const t = tbl || 'placements';
  const inp = document.querySelector(`input.edit-pct[data-tbl='${{t}}'][data-idx='${{i}}']`);
  if(!inp || inp.classList.contains('invalid')) return fallback;
  const v = parseInt(inp.value, 10);
  const [lo, hi] = pctRange(t);
  return (Number.isFinite(v) && v >= lo && v <= hi) ? v : fallback;
}}

// ---------- Sponsored Brands rows (their own sheet, their own header row) ----------
function isTicked(tbl, i){{
  const cb = document.querySelector(`input[type=checkbox][data-tbl='${{tbl}}'][data-idx='${{i}}']`);
  return !!(cb && cb.checked);
}}
function buildSbRows(reverse){{
  const rows = [];
  if(!SB_MIRROR_COLS.length) return rows;
  const bmSel = Object.fromEntries(Array.from(document.querySelectorAll("select.bm-override[data-tbl='sbbids']")).map(s=>[s.dataset.idx, s.value]));
  (DATA.sb_changes||[]).forEach((c,i)=>{{
    if(!isTicked('sbbids', i)) return;
    const r = sbEmptyRow();
    r['product']='Sponsored Brands'; r['entity']=c.entity; r['operation']='Update';
    r['campaign id']=c.campaign_id; r['ad group id']=c.ad_group_id;
    if(c.entity==='Keyword'){{ r['keyword id']=c.keyword_id; r['keyword text']=c.text||''; r['match type']=c.match_type||''; }}
    else {{
      r['product targeting id']=c.keyword_id;
      const expr = c.text || '';
      if (!String(expr).startsWith('keyword-group=')) r['product targeting expression']=expr;
    }}
    r['campaign name (informational only)']=c.campaign_name||'';
    r['ad group name (informational only)']=c.ad_group_name||'';
    if(reverse){{
      r['bid']=c.current_bid;
      if(c.action==='pause' || c.flag_below_min) r['state']='enabled';
      rows.push(r); return;
    }}
    if(c.action==='pause'){{ r['state']='paused'; rows.push(r); return; }}
    const effective = {{...c, new_bid: editedBid(i, c.new_bid, 'sbbids')}};
    effective.flag_below_min = effective.new_bid < SB_MIN_CPC;
    const policy = bmSel[i] || SB_BELOW_MIN_DEFAULT;
    const {{newBid, state}} = resolveBidRow(effective, policy, SB_MIN_CPC);
    if(state) r['state']=state; else r['bid']=newBid;
    rows.push(r);
  }});
  (DATA.sb_placements||[]).forEach((p,i)=>{{
    if(!isTicked('sbplacements', i)) return;
    // Advisory rows are never written to the upload file: we could not confirm what Amazon
    // does with an unrecognised SB placement label, so we do not send a number for it.
    if(p.advisory) return;
    const r = sbEmptyRow();
    // Sponsored Brands names this entity differently from Sponsored Products; sending SP's
    // value on the SB sheet gets the row rejected.
    r['product']='Sponsored Brands'; r['entity']='Bidding Adjustment by Placement'; r['operation']='Update';
    r['campaign id']=p.campaign_id; r['placement']=p.placement;
    r['percentage']= reverse ? p.current_pct : editedPct(i, p.new_pct, 'sbplacements');
    rows.push(r);
  }});
  return rows;
}}

// Build forward upload rows (ticked changes; lowercase-keyed to mirror the uploaded header row)
function buildForwardRows(){{
  const rows = [];
  const bmSel = Object.fromEntries(Array.from(document.querySelectorAll("select.bm-override[data-tbl='bids']")).map(s=>[s.dataset.idx, s.value]));
  DATA.changes.forEach((c,i)=>{{
    const cb = document.querySelector(`input[type=checkbox][data-tbl='bids'][data-idx='${{i}}']`);
    if(!cb || !cb.checked) return;
    const r = emptyRow();
    r['product']='Sponsored Products'; r['entity']=c.entity; r['operation']='Update';
    r['campaign id']=c.campaign_id; r['ad group id']=c.ad_group_id;
    if(c.entity==='Keyword'){{ r['keyword id']=c.keyword_id; r['keyword text']=c.text||''; r['match type']=c.match_type||''; }}
    else {{
      r['product targeting id']=c.keyword_id;
      const expr = c.text || '';
      if (!String(expr).startsWith('keyword-group=')) r['product targeting expression']=expr;
    }}
    r['campaign name (informational only)']=c.campaign_name||'';
    r['ad group name (informational only)']=c.ad_group_name||'';
    if(c.action==='pause'){{ r['state']='paused'; rows.push(r); return; }}
    const effective = {{...c, new_bid: editedBid(i, c.new_bid)}};
    effective.flag_below_min = effective.new_bid < MIN_CPC;
    const policy = bmSel[i] || BELOW_MIN_DEFAULT;
    const {{newBid, state}} = resolveBidRow(effective, policy);
    if(state) r['state']=state; else r['bid']=newBid;
    rows.push(r);
  }});
  DATA.placement_changes.forEach((p,i)=>{{
    const cb = document.querySelector(`input[type=checkbox][data-tbl='placements'][data-idx='${{i}}']`);
    if(!cb || !cb.checked) return;
    const r = emptyRow();
    r['product']='Sponsored Products'; r['entity']='Bidding Adjustment'; r['operation']='Update';
    r['campaign id']=p.campaign_id; r['placement']=p.placement; r['percentage']=editedPct(i, p.new_pct);
    rows.push(r);
  }});
  (DATA.budget_changes||[]).forEach((b,i)=>{{
    const cb = document.querySelector(`input[type=checkbox][data-tbl='budgets'][data-idx='${{i}}']`);
    if(!cb || !cb.checked) return;
    const r = emptyRow();
    r['product']='Sponsored Products'; r['entity']='Campaign'; r['operation']='Update';
    r['campaign id']=b.campaign_id; r['daily budget']=b.new_budget;
    rows.push(r);
  }});
  return rows;
}}

// Build reverse upload rows - same selection, values restored to PRE-change
function buildReverseRows(){{
  const rows = [];
  DATA.changes.forEach((c,i)=>{{
    const cb = document.querySelector(`input[type=checkbox][data-tbl='bids'][data-idx='${{i}}']`);
    if(!cb || !cb.checked) return;
    const r = emptyRow();
    r['product']='Sponsored Products'; r['entity']=c.entity; r['operation']='Update';
    r['campaign id']=c.campaign_id; r['ad group id']=c.ad_group_id;
    if(c.entity==='Keyword'){{ r['keyword id']=c.keyword_id; r['keyword text']=c.text||''; r['match type']=c.match_type||''; }}
    else {{
      r['product targeting id']=c.keyword_id;
      const expr = c.text || '';
      if (!String(expr).startsWith('keyword-group=')) r['product targeting expression']=expr;
    }}
    r['campaign name (informational only)']=c.campaign_name||'';
    r['ad group name (informational only)']=c.ad_group_name||'';
    r['bid']=c.current_bid;
    if(c.action==='pause' || c.flag_below_min) r['state']='enabled';
    rows.push(r);
  }});
  DATA.placement_changes.forEach((p,i)=>{{
    const cb = document.querySelector(`input[type=checkbox][data-tbl='placements'][data-idx='${{i}}']`);
    if(!cb || !cb.checked) return;
    const r = emptyRow();
    r['product']='Sponsored Products'; r['entity']='Bidding Adjustment'; r['operation']='Update';
    r['campaign id']=p.campaign_id; r['placement']=p.placement; r['percentage']=p.current_pct;
    rows.push(r);
  }});
  (DATA.budget_changes||[]).forEach((b,i)=>{{
    const cb = document.querySelector(`input[type=checkbox][data-tbl='budgets'][data-idx='${{i}}']`);
    if(!cb || !cb.checked) return;
    const r = emptyRow();
    r['product']='Sponsored Products'; r['entity']='Campaign'; r['operation']='Update';
    r['campaign id']=b.campaign_id; r['daily budget']=b.old_budget;
    rows.push(r);
  }});
  return rows;
}}

// ========== Approved-changes JSON (feeds the Sophie Hub push) ==========
// Maps the human placement label used in the bulk sheet to the Amazon Ads API enum.
function placementEnum(label){{
  const k = String(label||'').trim().toLowerCase();
  if(k.indexOf('top')>=0) return 'TOP_OF_SEARCH';
  if(k.indexOf('product')>=0) return 'PRODUCT_PAGE';
  if(k.indexOf('rest')>=0) return 'REST_OF_SEARCH';
  if(k.indexOf('business')>=0) return 'SITE_AMAZON_BUSINESS';
  return '';  // prepare_push.py will re-map / flag unknowns
}}
// Serialize exactly the ticked + edited changes, carrying the Amazon target IDs so the push
// step can call update_target_bid / update_campaign with no re-derivation. Rows that resolve
// to a PAUSE (action==='pause', or below-min + pause/split policy) have no numeric bid to push,
// so they go in paused_targets (surfaced, not pushed). Budget changes are passed through for the
// record; the live push covers bids + placements (the validated write paths) — budgets ship via
// the xlsx route.
function buildApprovedJson(){{
  const bmSel = Object.fromEntries(Array.from(document.querySelectorAll("select.bm-override[data-tbl='bids']")).map(s=>[s.dataset.idx, s.value]));
  const sbBmSel = Object.fromEntries(Array.from(document.querySelectorAll("select.bm-override[data-tbl='sbbids']")).map(s=>[s.dataset.idx, s.value]));
  const target_bids = [], paused_targets = [], placement_changes = [], budget_changes = [];
  DATA.changes.forEach((c,i)=>{{
    const cb = document.querySelector(`input[type=checkbox][data-tbl='bids'][data-idx='${{i}}']`);
    if(!cb || !cb.checked) return;
    if(c.action === 'pause'){{
      paused_targets.push({{targetId: String(c.keyword_id), entity: c.entity, text: c.text||'', match_type: c.match_type||'', reason: 'pause'}});
      return;
    }}
    const effective = {{...c, new_bid: editedBid(i, c.new_bid)}};
    effective.flag_below_min = effective.new_bid < MIN_CPC;
    const policy = bmSel[i] || BELOW_MIN_DEFAULT;
    const {{newBid, state}} = resolveBidRow(effective, policy);
    if(state === 'paused' || newBid === '' || !(Number(newBid) > 0)){{
      paused_targets.push({{targetId: String(c.keyword_id), entity: c.entity, text: c.text||'', match_type: c.match_type||'', reason: 'below_min_pause'}});
      return;
    }}
    target_bids.push({{
      entity: c.entity, targetId: String(c.keyword_id), text: c.text||'', match_type: c.match_type||'',
      campaign_id: String(c.campaign_id), ad_group_id: String(c.ad_group_id),
      current_bid: c.current_bid, final_bid: Number(Number(newBid).toFixed(2))
    }});
  }});
  DATA.placement_changes.forEach((p,i)=>{{
    const cb = document.querySelector(`input[type=checkbox][data-tbl='placements'][data-idx='${{i}}']`);
    if(!cb || !cb.checked) return;
    placement_changes.push({{
      campaign_id: String(p.campaign_id), campaign_name: p.campaign_name||'',
      placement: p.placement, placement_enum: placementEnum(p.placement),
      current_pct: p.current_pct, final_pct: editedPct(i, p.new_pct)
    }});
  }});
  (DATA.budget_changes||[]).forEach((b,i)=>{{
    const cb = document.querySelector(`input[type=checkbox][data-tbl='budgets'][data-idx='${{i}}']`);
    if(!cb || !cb.checked) return;
    budget_changes.push({{campaign_id: String(b.campaign_id), campaign_name: b.campaign_name||'', old_budget: b.old_budget, new_budget: b.new_budget}});
  }});
  // --- Sponsored Brands: pushable, on its own payloads. ---
  // current_bid / current_pct are carried deliberately: the push PRE-FLIGHTS every SB row
  // against the live account and refuses to write when what is on the account does not match
  // what the operator reviewed. That is the guard against a stale dashboard or an id mismatch.
  const sb_target_bids = [], sb_paused_targets = [], sb_placement_changes = [];
  (DATA.sb_changes||[]).forEach((c,i)=>{{
    if(!isTicked('sbbids', i)) return;
    if(c.action === 'pause'){{
      sb_paused_targets.push({{targetId: String(c.keyword_id), entity: c.entity, text: c.text||'',
                              match_type: c.match_type||'', ad_format: c.ad_format||'', reason: 'pause'}});
      return;
    }}
    // Apply the below-min policy, exactly as the SP branch above does. Without this the push
    // sent the raw modelled bid, so a Min CPC of 0.50 shipped 0.40-0.44 to the live account --
    // the one place in this skill where a defect writes a number nobody approved.
    const nb = editedBid(i, c.new_bid, 'sbbids');
    const sbEff = {{...c, new_bid: nb}};
    sbEff.flag_below_min = Number(nb) < SB_MIN_CPC;
    const sbPolicy = sbBmSel[i] || SB_BELOW_MIN_DEFAULT;
    const sbRes = resolveBidRow(sbEff, sbPolicy, SB_MIN_CPC);
    if(sbRes.state === 'paused' || sbRes.newBid === '' || !(Number(sbRes.newBid) > 0)){{
      sb_paused_targets.push({{targetId: String(c.keyword_id), entity: c.entity, text: c.text||'',
                              match_type: c.match_type||'', ad_format: c.ad_format||'', reason: 'below_min_pause'}});
      return;
    }}
    sb_target_bids.push({{
      entity: c.entity, targetId: String(c.keyword_id), text: c.text||'', match_type: c.match_type||'',
      ad_format: c.ad_format||'', campaign_id: String(c.campaign_id), ad_group_id: String(c.ad_group_id),
      current_bid: c.current_bid, final_bid: Number(Number(sbRes.newBid).toFixed(2))
    }});
  }});
  (DATA.sb_placements||[]).forEach((p,i)=>{{
    // No enum, no push. An advisory row is one we could not address; it never ships.
    if(p.advisory || !p.placement_enum) return;
    if(!isTicked('sbplacements', i)) return;
    sb_placement_changes.push({{
      campaign_id: String(p.campaign_id), campaign_name: p.campaign_name||'',
      ad_format: p.ad_format||'', placement: p.placement, placement_enum: p.placement_enum,
      creates_modifier: !!p.creates_modifier,
      current_pct: p.current_pct, final_pct: editedPct(i, p.new_pct, 'sbplacements')
    }});
  }});
  return {{
    schema: 'sophie.bulk-bid-optimizer.approved/3',
    generated_at: RUN_TS,   // the RUN's timestamp, not the browser clock
    source_hash: DATA.hash || '',
    currency_symbol: DATA.currency_symbol || '$',
    counts: {{ target_bids: target_bids.length, paused_targets: paused_targets.length,
              placement_changes: placement_changes.length, budget_changes: budget_changes.length,
              sb_target_bids: sb_target_bids.length, sb_paused_targets: sb_paused_targets.length,
              sb_placement_changes: sb_placement_changes.length }},
    target_bids, paused_targets, placement_changes, budget_changes,
    // Sponsored Brands pushes through the same two write paths as SP (update_target_bid and
    // update_campaign), but on separate payloads with a mandatory pre-flight. State changes
    // (pauses) and budgets remain xlsx-only for BOTH products.
    push_scope: 'sponsored_products_and_brands',
    sb_target_bids, sb_paused_targets, sb_placement_changes
  }};
}}

// ========== Tab visitation gate ==========
const VISITED = new Set(['summary']);  // summary visited on load
const TOTAL_TABS = document.querySelectorAll('.tab-btn').length;
function refreshGate(){{
  const allVisited = document.querySelectorAll('.tab-btn').length === VISITED.size;
  document.getElementById('btn-forward').disabled = !allVisited;
  document.getElementById('btn-reverse').disabled = !allVisited;
  const jsonBtn = document.getElementById('btn-approved-json');
  if(jsonBtn) jsonBtn.disabled = !allVisited;
  const fwdGate = document.getElementById('gate-fwd');
  const revGate = document.getElementById('gate-rev');
  const jsonGate = document.getElementById('gate-json');
  if(allVisited){{ fwdGate.style.display='none'; revGate.style.display='none'; if(jsonGate) jsonGate.style.display='none'; }}
  else {{ fwdGate.textContent = `Review ${{TOTAL_TABS - VISITED.size}} more tab${{TOTAL_TABS - VISITED.size===1?'':'s'}}`; revGate.textContent = fwdGate.textContent; if(jsonGate) jsonGate.textContent = fwdGate.textContent; }}
}}

// ========== Counter ==========
function refreshCounter(){{
  const sel = document.querySelectorAll('input[type=checkbox][data-tbl][data-idx]:checked').length;
  const tot = document.querySelectorAll('input[type=checkbox][data-tbl][data-idx]').length;
  document.getElementById('selection-counter').textContent = `${{sel}} of ${{tot}} changes selected`;
}}

// ========== localStorage persistence ==========
const STATE_KEY = 'sophie-bbo-'+(DATA.hash||'v2');
function saveState(){{
  const unchecked = Array.from(document.querySelectorAll('input[type=checkbox][data-tbl][data-idx]:not(:checked)')).map(cb=>`${{cb.dataset.tbl}}:${{cb.dataset.idx}}`);
  const overrides = {{}};
  // Everything is keyed "table:index", never bare index: SP row 3 and SB row 3 are
  // different rows, and a bare index would let one product's edit land on the other's.
  document.querySelectorAll('select.bm-override').forEach(s=>{{
    if(s.value) overrides[(s.dataset.tbl||'bids')+':'+s.dataset.idx] = s.value;
  }});
  // Persist operator's edited bid / percentage values (only if dirty - i.e. differ from initial)
  const editedBids = {{}};
  document.querySelectorAll('input.edit-bid.dirty').forEach(i=>{{ editedBids[i.dataset.tbl+':'+i.dataset.idx] = i.value; }});
  const editedPcts = {{}};
  document.querySelectorAll('input.edit-pct.dirty').forEach(i=>{{ editedPcts[i.dataset.tbl+':'+i.dataset.idx] = i.value; }});
  const tools = {{}};
  document.querySelectorAll('select[data-sort], select[data-filter]').forEach(s=>{{
    const k = (s.dataset.sort ? 'sort:' : 'filter:') + (s.dataset.sort || s.dataset.filter);
    if(s.value) tools[k] = s.value;
  }});
  try{{ localStorage.setItem(STATE_KEY, JSON.stringify({{unchecked, overrides, editedBids, editedPcts, tools, visited:Array.from(VISITED)}})); }}catch(e){{}}
}}
function loadState(){{
  try{{
    const raw = localStorage.getItem(STATE_KEY);
    if(!raw) return;
    const s = JSON.parse(raw);
    (s.unchecked||[]).forEach(key=>{{
      const [tbl, idx] = key.split(':');
      const cb = document.querySelector(`input[type=checkbox][data-tbl='${{tbl}}'][data-idx='${{idx}}']`);
      if(cb) cb.checked = false;
    }});
    const splitKey = (k, defTbl) => {{
      const i = k.indexOf(':');
      return i < 0 ? [defTbl, k] : [k.slice(0,i), k.slice(i+1)];
    }};
    Object.entries(s.overrides||{{}}).forEach(([k,val])=>{{
      const [tbl, idx] = splitKey(k, 'bids');
      const sel = document.querySelector(`select.bm-override[data-tbl='${{tbl}}'][data-idx='${{idx}}']`)
               || document.querySelector(`select.bm-override[data-idx='${{idx}}']`);
      if(sel) sel.value = val;
    }});
    Object.entries(s.editedBids||{{}}).forEach(([k,val])=>{{
      const [tbl, idx] = splitKey(k, 'bids');
      const inp = document.querySelector(`input.edit-bid[data-tbl='${{tbl}}'][data-idx='${{idx}}']`);
      if(inp) {{ inp.value = val; inp.classList.add('dirty'); refreshDelta(parseInt(idx,10), tbl); }}
    }});
    Object.entries(s.editedPcts||{{}}).forEach(([k,val])=>{{
      const [tbl, idx] = splitKey(k, 'placements');
      const inp = document.querySelector(`input.edit-pct[data-tbl='${{tbl}}'][data-idx='${{idx}}']`);
      if(inp) {{ inp.value = val; inp.classList.add('dirty'); }}
    }});
    Object.entries(s.tools||{{}}).forEach(([k,v])=>{{
      const [kind, tbl] = k.split(':');
      const sel = document.querySelector(`select[data-${{kind}}='${{tbl}}']`);
      if(sel) sel.value = v;
    }});
    (s.visited||[]).forEach(t=>VISITED.add(t));
  }}catch(e){{}}
}}

// ========== Wire up events ==========
// Tab switching + visitation tracking
document.querySelectorAll('.tab-btn').forEach(btn => {{
  btn.addEventListener('click', () => {{
    const tab = btn.dataset.tab;
    VISITED.add(tab);
    btn.classList.add('seen');   // the dot goes green: this tab has been looked at
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.toggle('active', b === btn));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.toggle('active', p.dataset.panel === tab));
    window.scrollTo({{top:0,behavior:'smooth'}});
    refreshGate(); saveState();
  }});
}});

// Per-row checkbox changes
document.addEventListener('change', (e) => {{
  if(e.target.matches('input[type=checkbox][data-tbl][data-idx]')){{
    const tr = e.target.closest('tr');
    if(tr) tr.classList.toggle('row-off', !e.target.checked);
    syncSelectAll(panelOf(e.target));
    refreshCounter(); saveState();
  }}
  if(e.target.matches('select.bm-override')){{ saveState(); }}
}});

// Editable bid / percentage fields
function refreshDelta(idx, tbl){{
  // Update the live Δ% cell next to an edited bid. tbl selects which product's array the
  // index refers to -- SP and SB each index their own change list.
  const t = tbl || 'bids';
  const c = (t === 'sbbids' ? (DATA.sb_changes||[]) : DATA.changes)[idx];
  const inp = document.querySelector(`input.edit-bid[data-tbl='${{t}}'][data-idx='${{idx}}']`);
  const span = document.querySelector(`.delta-live[data-tbl='${{t}}'][data-idx='${{idx}}']`);
  if(!c || !inp || !span) return;
  const v = parseFloat(inp.value);
  if(!Number.isFinite(v) || c.current_bid <= 0) {{ span.innerHTML = ''; return; }}
  const pct = ((v - c.current_bid) / c.current_bid) * 100;
  const cls = pct > 0 ? 'delta-up' : (pct < 0 ? 'delta-dn' : '');
  const sign = pct > 0 ? '+' : '';
  span.innerHTML = cls ? `<span class="${{cls}}">${{sign}}${{pct.toFixed(1)}}%</span>` : `${{pct.toFixed(1)}}%`;
}}
document.addEventListener('input', (e) => {{
  if(e.target.matches('input.edit-bid')){{
    const inp = e.target;
    const v = parseFloat(inp.value);
    const initial = parseFloat(inp.dataset.initial);
    const valid = Number.isFinite(v) && v > 0;
    inp.classList.toggle('invalid', !valid);
    inp.classList.toggle('dirty', valid && v.toFixed(2) !== Number(initial).toFixed(2));
    if(valid) refreshDelta(parseInt(inp.dataset.idx,10), inp.dataset.tbl);
    saveState();
  }}
  if(e.target.matches('input.edit-pct')){{
    const inp = e.target;
    const v = parseInt(inp.value, 10);
    const initial = parseInt(inp.dataset.initial, 10);
    const [lo, hi] = pctRange(inp.dataset.tbl);
    const valid = Number.isFinite(v) && v >= lo && v <= hi;
    inp.classList.toggle('invalid', !valid);
    inp.classList.toggle('dirty', valid && v !== initial);
    saveState();
  }}
}});

// Select-all checkbox in each table header
// ---- Selection scoping ----
// SP Bids and SP Pauses are two VIEWS of the same `changes` array, so their rows share
// data-tbl='bids' and one index space on purpose -- that shared index is what lets the applier
// map a ticked row back to its change. The consequence is that a document-wide
// querySelectorAll("[data-tbl='bids']") sweeps BOTH tabs, which is how "select none" on Pauses
// used to wipe every tick on Bids. Every bulk control is therefore scoped to the .tab-panel it
// sits in. Same applies to SB Bids / SB Pauses on 'sbbids'.
function panelOf(el){{ return (el && el.closest('.tab-panel')) || document; }}
function rowsIn(scope, tbl){{
  return Array.from(scope.querySelectorAll(`input[type=checkbox][data-tbl='${{tbl}}'][data-idx]`));
}}
// Keep a panel's header checkbox honest: checked when all its OWN rows are ticked, indeterminate
// when some are. Previously it stayed checked while rows underneath were unticked, which is what
// made the bug look like the header was "linked to another tab".
function syncSelectAll(scope){{
  if(!scope || scope === document) return;
  scope.querySelectorAll('input[type=checkbox][data-select-all]').forEach(head=>{{
    const rows = rowsIn(scope, head.dataset.selectAll);
    if(!rows.length){{ head.checked = false; head.indeterminate = false; return; }}
    const on = rows.filter(r=>r.checked).length;
    head.checked = on === rows.length;
    head.indeterminate = on > 0 && on < rows.length;
  }});
}}
function syncAllPanels(){{ document.querySelectorAll('.tab-panel').forEach(syncSelectAll); }}

document.querySelectorAll('input[type=checkbox][data-select-all]').forEach(cb=>{{
  cb.addEventListener('change', () => {{
    const scope = panelOf(cb);
    rowsIn(scope, cb.dataset.selectAll).forEach(x=>{{
      x.checked = cb.checked;
      const tr = x.closest('tr');
      if(tr) tr.classList.toggle('row-off', !cb.checked);
    }});
    cb.indeterminate = false;
    refreshCounter(); saveState();
  }});
}});

// Bulk select buttons (All / None / Invert per-table)
document.querySelectorAll('.mini-btn[data-bulk]').forEach(btn=>{{
  btn.addEventListener('click', () => {{
    const mode = btn.dataset.bulk;
    const scope = panelOf(btn);          // this tab only -- see the scoping note above
    rowsIn(scope, btn.dataset.tbl).forEach(x=>{{
      if(mode==='all') x.checked = true;
      else if(mode==='none') x.checked = false;
      else if(mode==='invert') x.checked = !x.checked;
      const tr = x.closest('tr');
      if(tr) tr.classList.toggle('row-off', !x.checked);
    }});
    syncSelectAll(scope);
    refreshCounter(); saveState();
  }});
}});

// Campaign / portfolio chip filters - toggle rows by campaign value
document.querySelectorAll('.chip-btn[data-filter]').forEach(btn=>{{
  btn.addEventListener('click', () => {{
    btn.classList.toggle('active');
    const active = Array.from(document.querySelectorAll('.chip-btn[data-filter].active')).map(b=>b.dataset.value);
    const anyActive = active.length > 0;
    // Only affects bid table's rows (campaign filter is a refinement, not a hard cut)
    document.querySelectorAll("#tbody-bids tr[data-tbl='bids']").forEach(tr=>{{
      const cb = tr.querySelector("input[type=checkbox]");
      if(!cb) return;
      const matches = !anyActive || active.includes(tr.dataset.campaign) || active.includes(tr.dataset.portfolio);
      cb.checked = matches;
      tr.classList.toggle('row-off', !matches);
    }});
    refreshCounter(); saveState();
  }});
}});

// Download buttons - emit xlsx (Amazon Ads Bulk UI is xlsx-only)
const XLSX_MIME = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';
// One workbook, one sheet per ad product. RUN_DATE is stamped by the generator (not the
// browser clock), so two operators downloading the same run get the same filename.
function sheetsFor(reverse){{
  const sp = reverse ? buildReverseRows() : buildForwardRows();
  const sb = buildSbRows(reverse);
  return [
    {{name: SP_SHEET_NAME, cols: MIRROR_COLS, rows: sp}},
    {{name: SB_SHEET_NAME, cols: SB_MIRROR_COLS, rows: sb}},
  ];
}}
function totalRows(sheets){{ return sheets.reduce((n,s)=>n+(s.rows?s.rows.length:0),0); }}
document.getElementById('btn-forward').addEventListener('click', () => {{
  const sheets = sheetsFor(false);
  if (!totalRows(sheets)) {{ alert('No rows selected. Tick at least one change to export.'); return; }}
  downloadFile('bulk_upload_'+RUN_DATE+'.xlsx', buildXlsx(sheets), XLSX_MIME);
}});
document.getElementById('btn-reverse').addEventListener('click', () => {{
  const sheets = sheetsFor(true);
  if (!totalRows(sheets)) {{ alert('No rows selected. Tick at least one change to export.'); return; }}
  downloadFile('bulk_reverse_'+RUN_DATE+'.xlsx', buildXlsx(sheets), XLSX_MIME);
}});
// Approved-changes JSON - the input to the Sophie Hub push route
const jsonBtnEl = document.getElementById('btn-approved-json');
if(jsonBtnEl) jsonBtnEl.addEventListener('click', () => {{
  const payload = buildApprovedJson();
  if (!payload.target_bids.length && !payload.placement_changes.length) {{ alert('Nothing to push. Tick at least one bid or placement change.'); return; }}
  downloadFile('approved_changes_'+RUN_DATE+'.json', JSON.stringify(payload, null, 2), 'application/json');
}});

// Reflect any tabs restored from a saved review as already seen.
function paintSeen(){{
  document.querySelectorAll('.tab-btn').forEach(b=>b.classList.toggle('seen', VISITED.has(b.dataset.tab)));
}}

// ---- Sort and filter ----
// Reordering is done on the DOM only. Row identity lives in data-idx, and every writer reads
// checkboxes by [data-tbl][data-idx], so sorting can never change what gets exported -- only the
// order you review it in.
function applyTools(tbl){{
  const tbody = document.getElementById('tbody-' + tbl)
             || document.querySelector(`.tab-panel [id^='tbody-'] tr[data-tbl='${{tbl}}']`)?.closest('tbody');
  if(!tbody) return;
  const sortSel = document.querySelector(`select[data-sort='${{tbl}}']`);
  const filtSel = document.querySelector(`select[data-filter='${{tbl}}']`);
  const rows = Array.from(tbody.querySelectorAll('tr[data-idx]'));
  if(!rows.length) return;
  const f = filtSel ? filtSel.value : '';
  let shown = 0;
  rows.forEach(tr=>{{
    const conf = tr.dataset.conf || '', d = parseFloat(tr.dataset.delta || '0');
    let keep = true;
    if(f === 'up') keep = d > 0;
    else if(f === 'down') keep = d < 0;
    else if(f) keep = conf === f;
    tr.classList.toggle('row-filtered', !keep);
    if(keep) shown++;
  }});
  const s = sortSel ? sortSel.value : '';
  if(s){{
    const rank = {{High:3, Medium:2, Low:1}};
    const num = (tr,k)=>parseFloat(tr.dataset[k] || '0');
    const cmp = {{
      'conf':        (a,b)=>(rank[b.dataset.conf]||0)-(rank[a.dataset.conf]||0),
      'conf-asc':    (a,b)=>(rank[a.dataset.conf]||0)-(rank[b.dataset.conf]||0),
      'delta-desc':  (a,b)=>num(b,'delta')-num(a,'delta'),
      'delta-asc':   (a,b)=>num(a,'delta')-num(b,'delta'),
      'clicks-desc': (a,b)=>num(b,'clicks')-num(a,'clicks'),
      'spend-desc':  (a,b)=>num(b,'spend')-num(a,'spend'),
    }}[s];
    if(cmp){{ rows.slice().sort(cmp).forEach(tr=>tbody.appendChild(tr)); }}
  }} else {{
    rows.slice().sort((a,b)=>parseInt(a.dataset.idx,10)-parseInt(b.dataset.idx,10))
        .forEach(tr=>tbody.appendChild(tr));
  }}
  const hits = document.querySelector(`[data-hits='${{tbl}}']`);
  if(hits) hits.textContent = shown === rows.length
    ? `${{rows.length}} row${{rows.length===1?'':'s'}}`
    : `showing ${{shown}} of ${{rows.length}}`;
}}
document.querySelectorAll('select[data-sort], select[data-filter]').forEach(sel=>{{
  sel.addEventListener('change', ()=>{{
    applyTools(sel.dataset.sort || sel.dataset.filter);
    saveState();
  }});
}});

// ---- Save / resume a review ----
// localStorage already persists within this browser. An explicit plan file lets a long review be
// paused, moved to another machine, or handed to someone else. It carries only the operator's
// decisions -- never the bid data itself -- and is checked against the run hash on load.
function planPayload(){{
  const st = JSON.parse(localStorage.getItem(STATE_KEY) || '{{}}');
  return {{schema:'sophie.bulk-bid-optimizer.review-plan/1', run_hash: DATA.hash || '',
          generated_at: RUN_TS, visited: Array.from(VISITED), state: st}};
}}
const savePlanBtn = document.getElementById('btn-save-plan');
if(savePlanBtn) savePlanBtn.addEventListener('click', ()=>{{
  saveState();
  downloadFile('review_plan_'+RUN_DATE+'.json', JSON.stringify(planPayload(), null, 2), 'application/json');
}});
const loadPlanInput = document.getElementById('load-plan');
if(loadPlanInput) loadPlanInput.addEventListener('change', (e)=>{{
  const file = e.target.files && e.target.files[0];
  if(!file) return;
  const rd = new FileReader();
  rd.onload = () => {{
    let p;
    try {{ p = JSON.parse(rd.result); }}
    catch(err) {{ alert('That file is not a saved review plan.'); return; }}
    if(!p || !p.state){{ alert('That file is not a saved review plan.'); return; }}
    if(p.run_hash && DATA.hash && p.run_hash !== DATA.hash){{
      if(!confirm('That plan was saved from a DIFFERENT run of the optimizer. The rows it refers to '
                + 'may not be the rows in this dashboard. Load it anyway?')) return;
    }}
    try {{ localStorage.setItem(STATE_KEY, JSON.stringify(p.state)); }} catch(err) {{}}
    (p.visited||[]).forEach(t=>VISITED.add(t));
    loadState(); paintSeen(); refreshCounter(); refreshGate(); syncAllPanels();
    document.querySelectorAll('input[type=checkbox][data-tbl][data-idx]').forEach(cb=>{{
      const tr = cb.closest('tr'); if(tr) tr.classList.toggle('row-off', !cb.checked);
    }});
    alert('Review plan loaded. Your ticks, edits and reviewed tabs have been restored.');
  }};
  rd.readAsText(file);
}});

// Initial wire-up
loadState();
paintSeen();
['bids','sbbids'].forEach(applyTools);
refreshCounter();
refreshGate();
// Apply row-off class on any unchecked rows from saved state
document.querySelectorAll('input[type=checkbox][data-tbl][data-idx]').forEach(cb=>{{
  if(!cb.checked){{ const tr = cb.closest('tr'); if(tr) tr.classList.add('row-off'); }}
}});
// Header checkboxes start reflecting their own panel (strategic keeps ship unticked, so a
// Negations header is legitimately indeterminate on load).
syncAllPanels();
</script>
</body></html>"""

    with open(out_path, "w", encoding="utf-8") as f: f.write(html_doc)
    print(out_path)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--results", required=True)
    p.add_argument("--source", required=True, help="original bulk filename for header")
    p.add_argument("--input", required=True, help="uploaded bulk, for mirroring the header row")
    p.add_argument("--output", required=True)
    args = p.parse_args()
    with open(args.results, encoding="utf-8") as f: data = json.load(f)
    import openpyxl as _ox
    _wb = _ox.load_workbook(args.input, data_only=True)
    _ws = _wb["Sponsored Products Campaigns"]
    data["headers"] = [c.value for c in _ws[1]]
    # Mirror the SB sheet's OWN header row too -- SP and SB templates differ, and each
    # sheet in the approved workbook must carry the header Amazon expects for that product.
    if data.get("sb"):
        _by_lower = {n.lower().strip(): n for n in _wb.sheetnames}
        for _cand in ["sb multi ad group campaigns", "sponsored brands campaigns"]:
            if _cand in _by_lower:
                _sbws = _wb[_by_lower[_cand]]
                _sbhdr = [c.value for c in _sbws[1]]
                if any(x is not None for x in _sbhdr):
                    data["sb_headers"] = _sbhdr
                    data["sb_sheet"] = _by_lower[_cand]
                    break
    render(data, args.source, args.output)
    # Open the finished dashboard in the default browser (Chrome if it is the default).
    # Cross-platform; silently skips if no browser is available (e.g. headless runs).
    try:
        import webbrowser, pathlib
        webbrowser.open(pathlib.Path(args.output).resolve().as_uri())
        print("opened in browser")
    except Exception:
        pass

if __name__ == "__main__":
    main()
```

## Edit → save → push (the review-and-apply loop)

The dashboard is the edit surface and emits **three** artifacts, all filtered by the same ticks and gated behind the review-all-tabs gate: the **approved xlsx** (upload route), the **approved changes (.json)** (push route — carries the Amazon target IDs, edited bids, and placement changes with API enums), and the **reverse xlsx** (rollback).

The loop: operator reviews every tab, unticks anything to skip, edits bids / placement percentages inline → clicks **Download approved changes (.json)** and saves it → hands it back and says to push → Claude runs the push procedure below. Because the saved JSON encodes exactly what was approved (placements included), **Claude never re-asks about placements**; one confirmation covers the whole push.

**Scope of the live push:** target **bids** and **placement modifiers**, for **both Sponsored Products and Sponsored Brands** — the two write paths validated against the Sophie Hub adapter (SP 2026-07, SB 2026-08-21). **Budget** changes are carried in the JSON for the record but are applied via the **xlsx upload route**, not the live push. Rows that resolve to a **pause** (a state change) are surfaced in `paused_targets` / `sb_paused_targets`, not pushed. Every target is pre-flighted against the live account before it is written.

## Push live to Amazon via Sophie Hub (optional write-back)

Applies the approved changes **directly to the live Amazon Ads account** through the Sophie Hub MCP, as an alternative to the manual xlsx upload. **Opt-in only** — run it solely when the operator explicitly asks to push AND has a saved **approved_changes.json** from the dashboard. This is OUTPUT write-back; it does not change the RUN GATE rule that input data is manual-upload only.

**Scope: bids and placement modifiers, for Sponsored Products AND Sponsored Brands.** State changes (pauses) and budget changes are **not** pushed for either product — they go via the approved xlsx.

### Gates (do not skip)
- **Live write.** These calls change real bids and placement modifiers immediately. Confirm **once**, naming both products: *"Push N SP target bids + M SP placements and P SB target bids + Q SB placements live to <store>? Reversible via the reverse xlsx / stored originals."* Then proceed with the whole set. Do **not** ask a separate question about placements, and do **not** ask separately about Sponsored Brands — one confirmation covers everything the operator ticked.
- **Allowlist.** Sophie Hub write access is restricted to allowlisted callers. If the first write returns an authorization/allowlist error, **stop, don't retry**, and fall back to the xlsx upload route — tell the operator their account isn't cleared for API writes and the approved xlsx does the identical thing.
- **Pre-flight (mandatory, and it is the SB safety net).** Before any write, `query_target` the ids you are about to change and compare each live bid with the `expected_current_bid` in `push_preflight.json`. **Any target that is missing, is `negative: true`, has the wrong `adProduct`, or whose live bid differs from what the operator reviewed is dropped from the push and reported** — never written. A drifted bid means someone else changed the account since the dashboard was generated, and a missing or negative target means the id space is not what we assumed. Both are reasons to stop, not to push harder.
- **Canary first, per product.** SP and SB each get their own canary: push one target, verify it landed with the right bid, then release the rest of that product. An SB canary failure must not stop SP changes that already landed, and vice versa — report each product's outcome separately.
- **Rollback.** Keep the reverse xlsx and the `current_bid` / `current_pct` values inside the approved JSON.

### Data contract (validated live against Sophie Hub's Amazon Ads adapter — SP 2026-07, SB 2026-08-21)
- Tool: `mcp__Sophie_Hub__sophie_call_amazon_ads_mcp` with `profile_id` + `tool_name` + `arguments`.
- The bulk sheet's **`keyword_id` (Keyword ID / Product Targeting ID) IS the API `targetId`** — same value, no lookup. Holds for keyword, product, and theme/auto targets, **and for Sponsored Brands**: the id `455419943708231` appears identically as the bulk Keyword ID, as `targetingId` in `report-v3-sb-targeting`, and as `targetId` in `query_target`. All update through `campaign_management-update_target_bid`.
- **Bids are plain dollars** (e.g. `1.04`), not micros.
- Every body needs `accessRequestedAccount: {"profileId": "<pid>"}`. Reads also need `adProductFilter: {"include": ["SPONSORED_PRODUCTS"]}` or `["SPONSORED_BRANDS"]`.
- **Update a target bid** (targets array batches, ~45/call) — **identical shape for SP and SB**. Bid is nested — `"bid": {"bid": <number>}`; a bare number or a `currencyCode` key both fail validation:
  ```json
  {"body": {"accessRequestedAccount": {"profileId": "<pid>"},
            "targets": [{"targetId": "<id>", "bid": {"bid": 1.04}}]}}
  ```
  Response has `success[]` / `error[]` / `partialSuccess[]`; each success echoes the new bid + fresh `lastUpdatedDateTime`.
- **Read an SB target** to pre-flight it:
  ```json
  {"body": {"accessRequestedAccount": {"profileId": "<pid>"},
            "adProductFilter": {"include": ["SPONSORED_BRANDS"]},
            "targetIdFilter": {"include": ["<id>", "..."]}}}
  ```
  A live SB target looks like `{"targetId":"455419943708231","adProduct":"SPONSORED_BRANDS","bid":{"bid":0.94,"currencyCode":"USD"},"negative":false,"targetType":"THEME"|"KEYWORD"|"PRODUCT",...}`.
- ⚠️ **Negative targets share the same list.** `query_target` returns SB negative keywords with `"negative": true` and **no `bid` field at all**. Never write a bid to one. The scorer already excludes them (only `Keyword` / `Product Targeting` entities are scored, never `Negative Keyword`), and the pre-flight drops any target that comes back `negative: true`.
- **Placement modifiers** are read-modify-write via `campaign_management-update_campaign`, same mechanism for both products, with **three Sponsored Brands differences**:
  - **Enums:** `TOP_OF_SEARCH`, `PRODUCT_PAGE`, `REST_OF_SEARCH`, `SITE_AMAZON_BUSINESS`, and — Sponsored Brands only — **`HOME_PAGE`**. Map "Home Page" before any "…page" rule or it will be mis-read as `PRODUCT_PAGE`.
  - ⚠️ **SB percentages are SIGNED.** A live SB campaign carried `{"percentage": -10, "placement": "REST_OF_SEARCH"}`. Sponsored Products modifiers are `0..900` and can only bid a placement up; Sponsored Brands can bid one **down**. Do not clamp SB at zero, and do not reject a negative SB percentage as invalid. This skill clamps SB to `[-99, +99]`.
  - ⚠️ **SB campaigns carry their own `bidStrategy`** (e.g. `NEW_TO_BRAND`, not SP's values) **and a `goalSettings` block**. Echo the campaign's existing `bidStrategy` back verbatim and do not send `goalSettings` at all — read it, leave it alone.
  - **Read** the campaign first (`campaign_management-query_campaign`); take its `optimizations.bidSettings.bidAdjustments.placementBidAdjustments` array (and `bidStrategy`). Change **only** the one placement's `percentage`; keep the other placements and the `bidStrategy` — a partial array wipes the others.
  - ⚠️ **The enum may not be in the array yet.** Both ad products can now propose a modifier on a placement sitting at 0%, and a campaign that has never had one carries no entry for it — on some accounts `placementBidAdjustments` is absent entirely. When the plan's `placement_enum` is not present, **append** `{"placement": "<enum>", "percentage": <n>}` to the array rather than skipping the row or replacing the array. The plan marks these rows `creates_modifier: true`, so you know before you read which ones to expect. Verify the response echoes the new entry alongside the untouched ones.
  - **Write** body (identical for SP and SB):
    ```json
    {"body": {"accessRequestedAccount": {"profileId": "<pid>"},
              "campaigns": [{"campaignId": "<cid>",
                "optimizations": {"bidSettings": {"bidStrategy": "<existing>",
                  "bidAdjustments": {"placementBidAdjustments": [ <full modified array> ]}}}}]}}
    ```

### Procedure

Run the Sponsored Products half first, then the Sponsored Brands half. They are independent: a failure in one does not abort the other, and each is reported separately.

1. **Confirm** (single gate above — one confirmation, both products).
2. **Resolve store + profile_id.** `mcp__Sophie_Hub__list_stores` → match by name → `mcp__Sophie_Hub__discover_amazon_reports(api_type=ADS, seller_id=<store>)` → read `profiles[].profile_id` for the marketplace. Cache it. The same profile serves SP and SB.
3. **Prepare payloads.** Run `prepare_push.py` with the approved JSON + profile_id → writes `push_targets_canary.json`, `push_targets_chunk_*.json`, `push_placement_plan.json`, and — when `push_scope` is `sponsored_products_and_brands` — `push_sb_targets_canary.json`, `push_sb_targets_chunk_*.json`, `push_sb_placement_plan.json`, plus `push_preflight.json`. It prints counts, including how many SB placement moves are negative.
4. **Pre-flight both products.** `query_target` with `targetIdFilter.include` over the ids in `push_preflight.json` (batch the reads; use the matching `adProductFilter`). For each id compare the live `bid.bid` with `expected_current_bid`. **Drop** any target that is absent, `negative: true`, the wrong `adProduct`, or whose live bid differs. Report what you dropped and why before writing anything. If more than a quarter of either product's targets drift, stop and tell the operator the dashboard is stale — a fresh bulk is the fix, not a forced push.
5. **SP bids — canary, then remainder.** Call `update_target_bid` with the SP canary body; verify `success[0]`. Allowlist/authorization error → stop the whole push and fall back to xlsx. Then send each chunk; tally `success` / `error` / `partialSuccess`; retry `error` entries once.
6. **SP placements** (only if the plan is non-empty). `query_campaign` for the plan's campaign IDs → merge each new percentage into that campaign's existing `placementBidAdjustments`, changing only the matching enum, or **appending** the entry when the campaign has none for that placement (`creates_modifier: true` rows) → `update_campaign` (batch several per call) → verify each returned percentage.
7. **SB bids — its own canary, then remainder.** Same calls, `push_sb_targets_*` payloads. Verify the canary landed with the right bid **and** that the response echoes `adProduct: SPONSORED_BRANDS` before releasing the rest. If the SB canary fails while SP already succeeded, say so plainly, leave SP applied, and hand SB to the xlsx route.
8. **SB placements** (only if the plan is non-empty). Same read-modify-write as SP, with the SB rules from the data contract: preserve the campaign's own `bidStrategy`, leave `goalSettings` untouched, allow negative percentages, and change only the one matching enum. Verify each returned percentage — including that a negative one came back negative rather than clamped to 0.
9. **Report, per product.** "Applied X/Y Sponsored Products target bids and Z/W placement changes, and P/Q Sponsored Brands target bids and R/S placement changes, to <store>. N target(s) were skipped by pre-flight because the live bid had moved. Paused rows and budget changes were left for the xlsx route. Rollback available."

### prepare_push.py

Run: `python prepare_push.py --approved approved_changes.json --profile-id <pid> [--out-dir DIR] [--batch 45]`. Normalizes and chunks only — no network calls (the MCP writes are Claude's, per the procedure).

```python
# prepare_push.py — normalize an approved_changes.json into ready-to-send MCP payloads.
# No network calls. Emits, per ad product:
#   SP: push_targets_canary.json, push_targets_chunk_<n>.json, push_placement_plan.json
#   SB: push_sb_targets_canary.json, push_sb_targets_chunk_<n>.json, push_sb_placement_plan.json
#   both: push_preflight.json  (targetId -> the bid the operator reviewed, for verification)
#
# SB write contract, verified live 2026-08-21 against Duke & Lefty:
#   - SB targets are ordinary targets: campaign_management-query_target with
#     adProductFilter.include=["SPONSORED_BRANDS"] returns targetId + bid{bid,currencyCode},
#     and update_target_bid takes the same {"targetId","bid":{"bid":N}} shape as SP.
#   - The bulk sheet's Keyword ID, the reporting targetingId and the API targetId are the
#     same number (confirmed: 455419943708231 appeared identically in report-v3-sb-targeting
#     and in query_target).
#   - SB placement enums include HOME_PAGE, which Sponsored Products never serves.
#   - SB placement percentages are SIGNED integers (a live campaign carried -10 on
#     REST_OF_SEARCH). SP modifiers are 0..900. Do not clamp SB at zero.
#   - SB campaigns carry their own bidStrategy values (e.g. NEW_TO_BRAND) and a goalSettings
#     block. Both must survive a placement write untouched.
import argparse, json, sys
from pathlib import Path

# SITE_AMAZON_BUSINESS is a valid Amazon enum but this skill NEVER optimizes the B2B
# placement, so it is deliberately absent from both sets below. Keeping it out here means an
# Amazon Business row cannot reach a payload even if one somehow reached the approved JSON.
# This mirrors sb_placement_enum() in the scorer -- the two must agree, or the push could
# write something the scorer refused to propose.
PLACEMENT_ENUMS = {"TOP_OF_SEARCH", "PRODUCT_PAGE", "REST_OF_SEARCH"}
SB_ONLY_ENUMS = {"HOME_PAGE"}

def map_placement(label, given_enum, product="SP"):
    allowed = PLACEMENT_ENUMS | (SB_ONLY_ENUMS if product == "SB" else set())
    if given_enum in allowed:
        return given_enum
    if given_enum:                       # named an enum we will not write -> refuse
        return None
    k = str(label or "").strip().lower()
    if "business" in k: return None      # B2B placement is never optimized
    # "home" before any "...page" rule: "Home Page" contains "page" and must not fall
    # through to PRODUCT_PAGE. HOME_PAGE is Sponsored Brands only.
    if "home" in k: return "HOME_PAGE" if product == "SB" else None
    if "top" in k: return "TOP_OF_SEARCH"
    if "rest" in k or "other" in k: return "REST_OF_SEARCH"
    if "product" in k or "detail" in k: return "PRODUCT_PAGE"
    return None

def body(pid, targets):
    return {"body": {"accessRequestedAccount": {"profileId": str(pid)}, "targets": targets}}

def normalize_targets(rows, allow_zero_floor=True):
    """Rows -> (payload targets, preflight map, skipped). Deduped by targetId."""
    targets, preflight, skipped = [], {}, []
    for t in rows:
        tid = str(t.get("targetId") or "").strip()
        try:
            bid = round(float(t["final_bid"]), 2)
        except (KeyError, TypeError, ValueError):
            bid = None
        if not tid or bid is None or bid <= 0:
            skipped.append(t); continue
        targets.append({"targetId": tid, "bid": {"bid": bid}})
        preflight[tid] = {"expected_current_bid": t.get("current_bid"),
                          "final_bid": bid, "text": t.get("text", ""),
                          "ad_format": t.get("ad_format", "")}
    dedup = {}
    for x in targets: dedup[x["targetId"]] = x
    return list(dedup.values()), preflight, skipped

def write_target_files(outd, pid, targets, batch, prefix):
    canary, rest = targets[:1], targets[1:]
    if canary:
        (outd / f"{prefix}_canary.json").write_text(json.dumps(body(pid, canary)), encoding="utf-8")
    chunks = [rest[i:i+batch] for i in range(0, len(rest), batch)]
    for i, ck in enumerate(chunks):
        (outd / f"{prefix}_chunk_{i}.json").write_text(json.dumps(body(pid, ck)), encoding="utf-8")
    return len(canary), len(chunks)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--approved", required=True)
    ap.add_argument("--profile-id", required=True)
    ap.add_argument("--out-dir", default=".")
    ap.add_argument("--batch", type=int, default=45)
    a = ap.parse_args()

    doc = json.loads(Path(a.approved).read_text(encoding="utf-8"))
    if doc.get("schema", "").split("/")[0] != "sophie.bulk-bid-optimizer.approved":
        print("[warn] unexpected schema tag; proceeding best-effort", file=sys.stderr)
    scope = doc.get("push_scope", "sponsored_products_only")
    push_sb = scope == "sponsored_products_and_brands"
    outd = Path(a.out_dir); outd.mkdir(parents=True, exist_ok=True)

    # ---------------- Sponsored Products ----------------
    targets, sp_preflight, skipped = normalize_targets(doc.get("target_bids", []))
    n_canary, n_chunks = write_target_files(outd, a.profile_id, targets, a.batch, "push_targets")

    plan, bad = [], []
    for p in doc.get("placement_changes", []):
        enum = map_placement(p.get("placement"), p.get("placement_enum"), "SP")
        try:
            pct = int(round(float(p["final_pct"])))
        except (KeyError, TypeError, ValueError):
            pct = None
        # SP modifiers cannot go negative; a negative here means something upstream is wrong.
        if enum is None or pct is None or pct < 0:
            bad.append(p); continue
        plan.append({"campaign_id": str(p.get("campaign_id")), "campaign_name": p.get("campaign_name", ""),
                     "placement_enum": enum, "final_pct": pct, "current_pct": p.get("current_pct")})
    (outd / "push_placement_plan.json").write_text(json.dumps(plan, indent=2), encoding="utf-8")

    # ---------------- Sponsored Brands ----------------
    sb_targets, sb_preflight, sb_skipped = [], {}, []
    sb_n_canary = sb_n_chunks = 0
    sb_plan, sb_bad = [], []
    if push_sb:
        sb_targets, sb_preflight, sb_skipped = normalize_targets(doc.get("sb_target_bids", []))
        sb_n_canary, sb_n_chunks = write_target_files(outd, a.profile_id, sb_targets, a.batch,
                                                      "push_sb_targets")
        for p in doc.get("sb_placement_changes", []):
            enum = map_placement(p.get("placement"), p.get("placement_enum"), "SB")
            try:
                pct = int(round(float(p["final_pct"])))
            except (KeyError, TypeError, ValueError):
                pct = None
            # SB percentages ARE signed -- only reject what is out of range or unaddressable.
            if enum is None or pct is None or not (-99 <= pct <= 99):
                sb_bad.append(p); continue
            sb_plan.append({"campaign_id": str(p.get("campaign_id")),
                            "campaign_name": p.get("campaign_name", ""),
                            "ad_format": p.get("ad_format", ""),
                            "placement_enum": enum, "final_pct": pct,
                            "current_pct": p.get("current_pct")})
        (outd / "push_sb_placement_plan.json").write_text(json.dumps(sb_plan, indent=2), encoding="utf-8")
    else:
        held = len(doc.get("sb_target_bids", [])) + len(doc.get("sb_placement_changes", []))
        if held:
            print("[note] push_scope is %r, so %d Sponsored Brands change(s) are NOT pushed - "
                  "apply them via the approved xlsx." % (scope, held), file=sys.stderr)

    # Pre-flight map: what the operator reviewed, keyed by targetId. The push procedure reads
    # the live account and refuses to write any target whose current bid has drifted from this.
    (outd / "push_preflight.json").write_text(json.dumps(
        {"sp": sp_preflight, "sb": sb_preflight}, indent=2), encoding="utf-8")

    summary = {
        "profile_id": str(a.profile_id),
        "push_scope": scope,
        "target_bids_pushable": len(targets),
        "canary": n_canary,
        "chunk_files": n_chunks,
        "batch_size": a.batch,
        "placement_changes": len(plan),
        "placement_campaigns": sorted({p["campaign_id"] for p in plan}),
        "sb_target_bids_pushable": len(sb_targets),
        "sb_canary": sb_n_canary,
        "sb_chunk_files": sb_n_chunks,
        "sb_placement_changes": len(sb_plan),
        "sb_placement_campaigns": sorted({p["campaign_id"] for p in sb_plan}),
        "sb_placement_negatives": sum(1 for p in sb_plan if p["final_pct"] < 0),
        "skipped_target_rows": len(skipped) + len(doc.get("paused_targets", [])),
        "sb_skipped_target_rows": len(sb_skipped) + len(doc.get("sb_paused_targets", [])),
        "budget_changes_not_pushed": len(doc.get("budget_changes", [])),
        "unmapped_placement_rows": len(bad),
        "sb_unmapped_placement_rows": len(sb_bad),
        "out_dir": str(outd),
    }
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
```

## File outputs

All go to `the user's Downloads folder (resolve with `pathlib.Path.home() / 'Downloads'` - never hardcode)`:
- `bulk_upload_<source>_YYYYMMDD_HHMM.xlsx` - **upload this to Amazon Ads** (fresh xlsx, Amazon Bulk UI is xlsx-only)
- `review_annotated_<source>_YYYYMMDD_HHMM.xlsx` - annotated copy for review only (DO NOT upload)
- `bid_changes_YYYYMMDD_HHMM.csv` - change log
- `negations_YYYYMMDD_HHMM.csv` - negation shortlist
- `placement_changes_YYYYMMDD_HHMM.csv` - placement modifier deltas
- `bid_optimization_report_YYYYMMDD_HHMM.html` - branded report

The dashboard also lets the operator download (client-side, from their ticks) `approved_changes_<date>.json` — the push contract (target IDs + edited bids + placement changes for both ad products; pauses and budgets carried for the record only). The push step then writes to the working directory: `push_targets_canary.json`, `push_targets_chunk_*.json`, `push_placement_plan.json` (Sponsored Products), `push_sb_targets_canary.json`, `push_sb_targets_chunk_*.json`, `push_sb_placement_plan.json` (Sponsored Brands), and `push_preflight.json` (the reviewed bid per target id, used to verify the live account before writing).

## Guardrails

- Never run scoring without the chosen strategy (and the mode if applicable), the chosen ad products, and a correctly windowed file.
- Never edit any sheet other than `Sponsored Products Campaigns` and the Sponsored Brands sheet (`SB Multi Ad Group Campaigns` or `Sponsored Brands Campaigns`).
- Never change `Operation` on rows you did not touch.
- The reader is case-insensitive; if zero enabled keyword or target rows are found for the requested products, stop and warn the file looks like an unexpected format rather than returning an empty result.
- Bid changes and pauses are target-level only; never pause whole campaigns automatically.
- Placement increases are capped per strategy (5 points on Profit-First, 15 on Balanced and Launch, 25 on Ranking Push for Top of Search only); decreases at 50 points. Creating a modifier on a 0 percent placement is allowed but always badged and named in the run notes. The Amazon Business placement is never optimized.
- Each output sheet mirrors its own uploaded sheet's exact header row; the reverse file restores bid, pause-state, placement, and budget changes for both products.
- Never write a placement row without a placement label. Amazon exports Shopper Cohort / Audience Segment adjustments on the same entity as placement adjustments but with no Placement, using Shopper Cohort Percentage and an Audience ID instead. Those rows are a different lever, are not optimized by this skill, and are skipped; emitting one produces a percentage Amazon cannot apply and the upload row fails.
- If the `SP Search Term Report` sheet is missing, still optimize bids and skip negations, and say so.
- The strategic-keep flag never changes a bid, a pause, a placement or a budget, and never removes a row from the Negations tab. It re-labels, re-sorts and unticks. Do not extend it to suppress pauses without asking the operator first — a term worth keeping in a search-term report is not automatically a keyword worth keeping enabled.
- ACOS-Targeted but CPC-Managed never changes bids and placements in the same run; daily mode also requires the yesterday file for the budget check. This applies to Sponsored Brands identically.

Sponsored Brands guardrails:
- **Never source Sponsored Brands data from the MCP.** `report-v3-sb-targeting` has no sales and no keyword text, and SB conversions are reported at campaign grain only. The bulk export is the sole source. If someone proposes reconstructing SB performance from the API, the answer is no — the numbers are not there.
- **Never blend ad formats.** Video, Product Collection and Store Spotlight are benchmarked separately, always. If a format has too little data to score, it gets no changes rather than borrowing another format's RPC.
- **Never write an unrecognised SB placement label.** A label that does not resolve to an API enum is advisory: shown in the dashboard, excluded from both the upload file and the push. Do not extend `sb_placement_enum()` on the strength of a guess.
- **Never clamp an SB placement percentage at zero.** SB modifiers are signed; bidding a weak placement down is a legitimate and useful outcome. Clamping at 0 is an SP rule that does not apply here.
- **Never write a bid to a negative target.** `query_target` returns SB negative keywords in the same list with `negative: true` and no bid. The pre-flight drops them.
- **Never skip the pre-flight on an SB push,** and never write a target whose live bid has drifted from what the operator reviewed. Drift means the account moved under the dashboard; the fix is a fresh bulk, not a forced write.
- **Never send `goalSettings` on an SB placement write,** and always echo the campaign's existing `bidStrategy` back — SB uses values SP does not.
- **Never make SB pause on SP's evidence threshold.** `SB_PAUSE_PATIENCE` exists deliberately; do not tune it away to make the counts look busier.
- **Never mix products on one sheet.** SP rows go on the SP sheet, SB rows on the SB sheet; the templates differ and a mixed sheet fails Amazon validation.
- If Sponsored Brands was requested and the SB sheet is missing or empty, stop and name the three checkboxes. Do not silently downgrade to an SP-only run.
- If the SB search term sheet is missing, run SB bids and pauses, skip SB negations, and say so.
- Sponsored Brands **is** part of the live push route, but only for bids and placement modifiers, only behind the pre-flight, and never for pauses or budgets.

Push route (Sophie Hub write-back) guardrails:
- Never push without an explicit operator request AND a saved `approved_changes.json`. The push is opt-in; the default deliverable is still the xlsx + report. It is the ONLY sanctioned Sophie Hub call in this skill, and it is OUTPUT write-back — the RUN GATE's "no MCP" rule governs input sourcing only.
- Confirm once (counts + store, naming both ad products). Do not ask a separate question about placements, and do not ask a separate question about Sponsored Brands — one confirmation covers everything ticked.
- Pre-flight every target against the live account first; drop and report drifted, missing, negative or wrong-product ids rather than writing them.
- SP and SB each get their own canary and their own outcome line. One product failing never silently aborts or half-applies the other.
- Canary first, verify it landed, then release the rest. Bids are dollars; `keyword_id` == Amazon `targetId`.
- On an allowlist/authorization error, stop and fall back to the xlsx route — don't retry the write loop.
- For placement writes, read the campaign's current `placementBidAdjustments` first and change only the one placement, appending the entry when the campaign has no modifier for that placement yet; never send a partial array and never drop `bidStrategy`.
- Paused rows (`paused_targets`, `sb_paused_targets`) and budget changes are not part of the bid push, for either product — apply those via the xlsx route.
- Keep the reverse xlsx / original values for rollback.

## Version

v4.0 — 2026-08-29. **Quality pass from a POD-leader review of a live run.**

- **Upload rows were failing Amazon validation, and it was a regression I introduced.** Amazon
  exports Shopper Cohort / Audience Segment bidding adjustments on the *same entity* as placement
  adjustments, but with **no Placement** — they carry Shopper Cohort Percentage and an Audience ID
  instead. Before v3.5 they were skipped by accident, because their Percentage cell is blank and
  the old rule discarded anything sitting at 0. Letting Sponsored Products create modifiers from 0%
  (v3.5) removed that accidental guard, so a cohort row could be proposed and written as a
  percentage with an empty Placement — which Amazon rejects. Both ad products now skip cohort rows
  and any adjustment row with no placement label.
- **Low-data targets are never bid down.** Reported: Sponsored Brands rows with 0–2 clicks were
  getting 10–15% cuts, labelled "low-data step". They now follow the same rule as zero-click
  targets — never cut, stepped up toward what a click is worth where the strategy's dial says
  raise, held where it says hold. One or two clicks is not evidence, and a cut mostly delays the
  click that would settle it. **This changes proposals**; it is the only behavioural change here.
- **Low-data targets get their own flag and, by default, their own tab.** Asked at run time. The
  split is presentational — the maths is identical either way — but it keeps a firm decision and a
  coin-flip out of the same list.
- **Empty tabs now say why.** "0 budget recommendations" alongside a hundred other suggestions
  reads as a fault; it is usually just that budgets are only touched by CPC-Managed. Every strategy
  that leaves budgets alone now says so in the run notes.
- **Sort and filter on the bid tables** — by confidence, by size of change, by clicks, by sales;
  filter to one confidence band or to increases/decreases only. Reordering is DOM-only: row
  identity lives in `data-idx` and every writer reads by index, so sorting can never change what
  gets exported. Verified.
- **Save and resume a review.** Ticks and edits were already kept in the browser; there is now an
  explicit review-plan file so a long review can be paused, moved to another machine, or handed
  over. It carries decisions only, never bid data, and warns if loaded against a different run.
- **Tabs you have not opened carry a dot**, so the review gate stops being a guessing game.

One thing deliberately NOT changed: the 3–7 click rows that also draw cuts sit in the **Medium**
tier and come from the CPA projection, a different path from the low-data step. Extending the
no-cut rule to them would be a larger change to the engine and has not been made.

v3.10 — 2026-08-28. **Silent zeros in the CPC-Managed modes**, found by running all three modes
plus every other strategy against a real bulk and reading the output rather than only checking it
did not crash.

- **Daily mode with no Yesterday bulk reported "0 budget changes" and said nothing.** The budget
  check needs the one-day export; without it the check does not run at all. A zero on that tab is
  indistinguishable from "no campaign spent out", which is the opposite of the truth. The skill's
  own fallback rules already said to tell the operator — the code never did. It now says the check
  was skipped, not passed, and how to fix it. A genuine zero (Yesterday file present, nothing spent
  out) is now labelled as genuine.
- **Weekly and monthly modes showed empty Bids, Pauses and Placements tabs with no explanation.**
  CPC-Managed deliberately never moves bids and placements in the same run, which is correct, but
  the empty tabs read as "nothing to change" rather than "not evaluated". Each suppressed area now
  says which mode would score it.
- **Monthly reallocation now explains itself when it proposes nothing** — it needs at least four
  campaigns with spend to rank, and on a small account that is a legitimate no-op rather than a
  fault.

This is the same principle as the v3.6 search-term warnings: a check that did not run must never
look like a check that passed. Verified across every strategy, all three CPC-Managed modes, and
all three product scopes on a real 30-day bulk — 11 combinations, each driven as a full operator
session with real downloads and a three-way route comparison. No scoring changed.

v3.9 — 2026-08-28. **Four defects found by running the skill as an operator would** — Profit-First
against a real 30-day bulk, reviewing every tab and downloading the actual files rather than
calling the scripts directly. Three of the four only appear on Profit-First, which is why nine
prior versions of testing missed them: it is the only strategy whose below-min policy is `split`.

- **The three output routes disagreed with each other.** On the same six Sponsored Brands targets:
  the Python applier **paused** them (correct for `split`), the xlsx the operator actually
  downloads **kept them running at the floor**, and the live-push JSON **kept them running at
  0.40-0.44** — below the operator's own 0.50 Min CPC. Three routes, three different actions, on
  rows nobody had approved differently.
  - The in-browser writer's `resolveBidRow()` had no `split` branch at all, so it fell through to
    floor. It now mirrors `apply_changes_v3.py` exactly, including that `split` pauses only
    zero-order rows and leaves a converting below-min bid alone.
  - The approved-JSON builder applied the below-min policy for Sponsored Products and skipped it
    entirely for Sponsored Brands, sending raw modelled bids. It now runs the same
    `resolveBidRow()` with the SB floor and the SB policy. This was the only defect in the skill
    capable of writing an unapproved number to a live account.
- **Sponsored Brands placement rows carried the wrong Entity.** Amazon's SB sheet uses
  `Bidding Adjustment by Placement`; both writers emitted `Bidding adjustment`, the Sponsored
  Products value, which Amazon rejects on the SB sheet. Verified against a real export. SP now
  also emits Amazon's own casing, `Bidding Adjustment`.
- **Sponsored Brands rows had no below-min override control.** Sponsored Products rows carry a BM
  dropdown; SB rows never rendered one, even though the JavaScript already looked for it. On the
  test account every below-min row was on Sponsored Brands, so the operator had no per-row
  recourse at all on the product where the policy actually bit. The SB Bids tab now has the same
  BM column, and the SP and SB overrides are read separately rather than by a single selector that
  mixed the two products' row indices.

No scoring changed: bids, pauses, placements and budgets are byte-identical to v3.8 for every
strategy. Everything here is in what gets written out.

v3.8 — 2026-08-27. **Selection controls no longer leak across tabs.** Reported from a live run:
clicking the header checkbox on SP Pauses to deselect everything also cleared every tick on SP
Bids, and ticking all of SP Bids re-enabled all of SP Pauses.

Cause: SP Bids and SP Pauses are two *views of the same* `changes` array, so their rows share
`data-tbl='bids'` and a single index space **by design** — that shared index is what lets the
applier map an approved row back to its change, and renumbering would break the upload file. The
defect was in the handlers, which queried the whole document by that attribute and so swept both
tabs at once. SB Bids and SB Pauses had the identical problem on `sbbids`.

Fixed by scoping every bulk control to the `.tab-panel` it sits in — a `panelOf()` / `rowsIn()`
pair the select-all handler and the All / None / Invert buttons both go through. The index space
is untouched, so approved xlsx, reverse xlsx and approved JSON are byte-identical for any given
set of ticks.

Also fixed the symptom that made it look like the header was "linked to another tab": the header
checkbox never reflected its own rows, staying checked while rows underneath were unticked. It
now shows checked, unchecked, or **indeterminate** for a partial selection, and updates as rows
are ticked individually. A Negations tab with strategic keeps is legitimately indeterminate on
load, which is now visible rather than misleading.

v3.7 — 2026-08-24. **Strategic-keyword safety flag on the Negations tabs**, ported from
`kw-harvester-negator` where it has been earning its keep. Optional `--keyword-research` input
(.xlsx / .csv / .txt — a Sophie KW research export, a Cerebro export, or a bare column of
keywords). A customer search term that meets the negation rule but **exactly matches** a keyword
the operator researched is re-labelled *"Don't negate - strategic. Raise bid or move to own
campaign."*, sorts to the top of the tab, gets a **Strategic keep** badge and a blue rail, and
**starts unticked** — because keeping a researched term is a judgement call and the rest of the
tab is not. A banner names the count above the table, and the Summary card breaks it out.

The point is that such a term is not waste. It is a term the operator deliberately targeted that
has not converted *yet*, and negating it throws the research away — usually the week before
someone asks why the campaign stopped covering its own core terms.

Scope is deliberately narrow, matching the operator's call: **Negations only, both ad products.**
It never touches a bid, a pause, a placement or a budget, and it never removes a row — it
re-labels, re-sorts and unticks. Matching is exact string, case-insensitive, after whitespace
collapse: the same rule `kw-harvester-negator` uses, so the two skills agree on what counts as
strategic. A token-set match would catch "protein powder vanilla" against a researched "vanilla
protein powder", but it would also flag terms nobody researched, and a false keep quietly protects
real waste.

v3.6 — 2026-08-24. Four defects found by probing the paths the v3.5 pass did not reach — the
push preparation, the negation rule, and the money formatting. Two of them were silent: they
produced a plausible-looking empty result rather than an error.
- **Every dashboard said `$`, whatever the account billed in.** `render_report.py` reads
  `cfg["currency_symbol"]`, and the scorer never wrote one — there was no argument for it and no
  question in the flow, so the fallback fired on every run. A GBP or EUR account got a full set of
  dollar-signed figures in a client-facing artifact. Added `--currency-symbol`, persisted into the
  run config and the approved JSON, and a Phase 2 question that now gets asked every run.
- **A missing State column on a search-term sheet emptied the Negations tab silently.** The gate
  was `state != "enabled" -> skip`, and several Amazon search-term exports carry no State column,
  so `str(None).lower()` fell through and dropped every row. Zero negations, no warning, and it
  reads exactly like a clean account. A blank or absent state now counts as enabled, since a row
  is in the search term report because it served.
- **Nothing distinguished "no waste found" from "we never looked."** SB warned when its search
  term sheet was missing; SP warned about nothing at all, though the guardrails said it should.
  Both products now say which of the two happened, including the case where a sheet is present but
  every row is filtered out by state.
- **The push had no instruction for creating a placement modifier that does not exist yet.** v3.5
  let both ad products propose a modifier on a 0% placement, but the write procedure only ever said
  "change the matching enum" — a campaign with no entry for that placement would have been skipped
  or, worse, guessed at. It now says to append, and `creates_modifier` tells you which rows to
  expect before you read the campaign.
- Negation counts now also report **distinct search terms**. Negatives apply per ad group, so one
  wasteful term legitimately produces one row per ad group — the row count is correct but reads as
  inflated, and the distinct count is what the operator actually has to decide about.

v3.5 — 2026-08-24. **Ships-correctly pass.** Eight defects found by extracting the scorer and
renderer, running them against a purpose-built SP+SB fixture, and driving the dashboard in a
headless browser. Nothing in the core bid formula changed; High, Medium and Low tier bids are
identical to v3.4 except where the clamp reorder in the last item applies.
- **The approval dashboard was unusable.** `.download-panel` used `grid-template-columns:1fr auto`,
  and the three `white-space:nowrap` download buttons plus their review-gate badges sized the
  `auto` track to 1,145px of a 1,304px panel. The text column collapsed to **71px wide and
  1,643px tall** - one word per line down the left edge. Now stacked on `minmax(0,1fr)`, measured
  at 1,240 x 506.
- **Negative Sponsored Brands placement edits were silently discarded.** The scorer correctly
  emitted signed values, then the dashboard rendered them into `min="0"` inputs and validated
  `v >= 0`, so every negative SB row was flagged invalid on touch and any operator edit was thrown
  away in favour of the original. Typing `-30` shipped `-40`. Fixed with a per-table `pctRange()`
  used by the input attributes and both validators. This was the one that could put a number on a
  live campaign that nobody chose.
- **Two of eleven tabs were off-screen** at 1,440px (`scrollWidth 1717`), while the download gate
  demanded every tab be opened. The tab bar now wraps.
- **Three of the five placement dials did nothing.** `trim` and `rpc` were the same code path with
  the same constants, and the block meant to make Ranking Push target top of search was a literal
  `pass` - it simply raised the cap to 25pp on every placement. Now real: Profit-First raises by at
  most 5pp, Ranking Push's 25pp applies to Top of Search alone.
- **Sponsored Products placement tuning could never start from zero,** so it was inert on most
  campaigns - 0% is Amazon's default. This is the same defect SB had fixed in v3.3; SP now matches,
  badged "New modifier" and named in the run notes. A 0% placement can still only be created when
  its RPC beats the campaign's.
- **Two tab descriptions documented rules that no longer existed** - a "+/-10 percentage points"
  placement cap against real constants of +15/-50, printed directly above a row moving 25% to 0%,
  and a negation rule ("spend > 1.5x breakeven") that `find_negations()` has never implemented.
  Both now say what the code does.
- **The visibility floor ran after the max-change clamp,** so on a bid moving UP it could push
  straight through the cap. Reproduced on Balanced: a 0.50 bid whose max legal rise was +15%
  (0.58) came back at **0.68, a +36% jump in one run**. The documented and dashboard-printed
  per-run guarantee simply was not true in that direction. (Downward moves were never affected -
  the down-clamp is a lower bound and the floor only ever raises.) The floor now runs first and
  the clamp is the outer guarantee, so a starved converting keyword still climbs to its floor,
  over successive runs at the strategy's step size instead of in one jump.
- **Wide tables had no scroll container** and one empty-state `colspan` was off by one.

v3.4 — 2026-08-21. **Zero-click rule, with a per-strategy `zero_click` dial.** A target that has never been clicked is never bid DOWN, under any strategy: it has spent nothing, so a cut saves nothing and only makes a click — the one event that would produce evidence — less likely. What happens instead is now a strategy decision: `raise` (Balanced, Launch, Ranking Push) steps the bid up toward what a click is worth at the ad group's RPC and stops there; `hold` (Profit-First, CPC-Managed) leaves it untouched, because buying unproven traffic works against protecting margin and against grinding CPC down. Found on a real account where 65% of targets had never been clicked and 31% of all proposed bid changes were cuts to rows that had spent $0. The change is conservative in both directions — besides removing 107 pointless cuts it also capped 23 raises that the old symmetric step would have pushed ABOVE the modelled click value. Every formula, tier, clamp, grace band, floor, brand gate and pause rule is unchanged; High and Medium tiers, and Low-tier rows with 1–2 clicks, are bit-for-bit identical to v3.3. The stance used is printed in the run notes and shown in the dashboard config bar.

v3.3 — 2026-08-21. Fixes found by the first real-account run (Niacinex), none of which the synthetic fixture could reach:
- **Duplicate SB sheets.** Amazon exports the same Sponsored Brands campaigns into BOTH `Sponsored Brands Campaigns` and `SB Multi Ad Group Campaigns`, with identical Keyword IDs. The reader concatenated them, which scored every SB keyword twice, doubled the order count gating pauses, and would have written every SB change into the upload file twice. Now deduped against a primary sheet (39 duplicate rows dropped on the test file).
- **SB placement entity name.** Sponsored Brands calls it `Bidding Adjustment by Placement`, not Sponsored Products' `Bidding Adjustment`. The exact-match check found zero SB placement rows, silently disabling the whole SB placement feature. Now matched on prefix.
- **SB placement creation.** SB modifiers default to 0, so refusing to move off zero (the SP rule) would leave SB placement tuning permanently inert. Moving off zero is allowed, badged "New modifier" in the dashboard and called out in the run notes.
- Dedupe counter reported 0 when an entirely-duplicated sheet was dropped.
- Six stale v3.0 lines removed, three of which claimed Sponsored Brands was not pushable and contradicted the push section.

v3.0 — 2026-08-21. **Adds Sponsored Brands, including SBV, from the same single bulk upload.** One run, one dashboard, one approved xlsx with a Sponsored Products sheet and a Sponsored Brands sheet.
- **Same input, three more checkboxes.** SB comes from the identical Download campaigns export; tick Sponsored Brands data, Sponsored Brands multi-ad group data, Sponsored Brands search term data. SBV is not a separate sheet — it is the video rows within the SB sheet.
- **Split by ad format.** Video, Product Collection and Store Spotlight each get their own RPC, clicks-to-order and ad-group benchmarks. The dashboard shows the per-format benchmark table as evidence. Verified against a reference fixture that pooling the formats changes the decisions.
- **Match-or-differ parameters.** One gate question asks whether SB should use the SP settings; if not, the same questions are asked again for SB, unanchored, in the same words. Every omitted `--sb-*` flag means "match SP".
- **More patient pausing on SB** (`SB_PAUSE_PATIENCE = 1.5`), verified as exactly 1.5× the SP click threshold.
- **Recognition-gated SB placements.** Confirmed labels are writable; unconfirmed labels are advisory-only and excluded from the upload file.
- **Two-sheet xlsx** in both the Python applier and the in-browser writer, each sheet mirroring its own header row. Both routes verified to produce identical rows.
- **Client-side clock leak fixed** — `RUN_TS` / `RUN_DATE` passed in as data-as-props; no `new Date()` left in the page.
- **MCP re-confirmed N/A for both products**, now with the evidence recorded in the RUN GATE: no bulk endpoint exists, and `report-v3-sb-targeting` carries no sales and no keyword text, so the RPC engine cannot be fed from the API.
- **Live push now covers Sponsored Brands too** (`push_scope: "sponsored_products_and_brands"`, approved-JSON schema `/3`). Verified live against the account before building: SB targets update through the same `update_target_bid` shape, and the bulk Keyword ID, the reporting `targetingId` and the API `targetId` are the same number. Three SB-specific differences are handled and documented — `HOME_PAGE` in the placement enum, **signed** placement percentages (SP can only bid a placement up; SB can bid one down), and SB's own `bidStrategy` / `goalSettings` which must survive a placement write. Pauses and budgets stay xlsx-only for both products.
- **Mandatory pre-flight before any write.** Every target is read back from the live account and dropped if it is missing, `negative: true`, the wrong ad product, or its bid has drifted from what the operator reviewed. SP and SB each get their own canary and their own outcome line.
- All SP bidding math unchanged.

v2.2 — 2026-07-27. Adds the optional **Sophie Hub write-back push**: dashboard emits `approved_changes.json` (target IDs + edited bids + placements + budget passthrough), `prepare_push.py` chunks it, and Claude applies bids + placements live via `update_target_bid` + `update_campaign` (canary-first, allowlist-gated, placements auto-included, reversible). Upload route and all bidding math unchanged; input sourcing stays manual-upload only.

v2.1 — Negations tab relabeled as a manual negative-KW picker with the advisory note surfaced above the table.

v2 - 2026-06-26. Sophie Society bidding method, multi-strategy. Five strategies: Profit-First, Balanced, Launch, Ranking Push, ACOS-Targeted but CPC-Managed (three modes). Deterministic. Sponsored Products only. Case-insensitive reader for current Amazon exports; output mirrors the uploaded header row.
