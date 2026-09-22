---
name: weekly-exec-summary-hub-v2
description: Scheduled, CEO-grade weekly executive brief for one or more Amazon stores, posted to Slack. Pulls live data from Sophie Hub MCP, compares the last 7 days vs the prior week and a trailing 4-week baseline, and leads with a one-line verdict, real wins, and a ranked "needs a call" list where every flag carries a dollar figure and a recommended action. Covers TACoS vs target, inventory stockout risk, demand softness (traffic vs conversion vs buy-box), wasted ad spend, and an accountability loop on open issues. Runs in two modes — an interactive Setup that saves answers to a config memory file, then unattended Scheduled runs that read that config and post automatically. Triggers on "weekly exec summary", "weekly CEO brief", "schedule the weekly report", "set up the weekly recap", "weekly performance brief to Slack", "WoW summary for a brand", or any request for a scheduled multi-store executive recap delivered to Slack. Does NOT generate creative briefs, audits, or dashboards — use the sibling skills for those.
---

# Weekly Executive Summary v2 → Slack (CEO-grade, scheduled)

A weekly brief written the way you'd brief a CEO: **lead with the verdict, quantify everything in dollars, and every flag carries a recommended call.** Pulls live data from Sophie Hub MCP, runs on a schedule, and posts a single Slack message per week.

> **The bar.** A CEO does not want a pile of metrics — they want a trusted operator who has already done the thinking. Three tests for every line you write:
> 1. **Is it the bottom line, or supporting detail?** Bottom line goes up top.
> 2. **Is it in dollars?** Rates are evidence; money is the headline.
> 3. **Does it imply a decision or an owner?** If not, it's noise — cut it.

This is the v2 of `weekly-exec-summary-hub`. The v1 sibling is a simpler, interactive narrative recap; this version is the scheduled, dollar-ranked, risk-flagging brief.

**Where this runs (read first).** This is a **locally-installed Claude Code skill** — the user downloads the folder into their `.claude/skills/`. It is **not** an Atlas / `library_item` skill and ships **no bundle** (prose only). It relies on **local disk persistence**, so it must run in **Claude Code** (CLI/IDE), where the config + state file survives between runs and `/schedule` fires the weekly run on the same machine. **Claude Desktop's sandbox does not reliably persist files between runs — not a supported target.**

**Config + state file (pinned):** `$CONFIG = ~/.claude/weekly-exec-summary-hub-v2/config.md` — created by Setup, read and rewritten by every Scheduled run. Kept **outside** the skill folder so re-downloading the skill never clobbers it. All file references below use `$CONFIG`.

---

## Two modes

| Mode | When | Behaviour |
|---|---|---|
| **Setup** | Once, before scheduling (a human is present) | Interactive. Asks for stores, Slack channel, per-store targets, optional margin + lead time. Writes everything to `$CONFIG`. **The only mode that may ask questions.** |
| **Scheduled** | Weekly, unattended (cron via `/schedule`) | Reads `$CONFIG`. **Never asks anything** — there is no human at the keyboard. Pulls data, computes flags, posts to Slack, rewrites the open-issues state in `$CONFIG`. |

Detect the mode from the request: "set up / configure the weekly report" → Setup. "Run the weekly report" / a scheduled trigger → Scheduled. If a Scheduled run finds no `$CONFIG`, abort and tell the user to run Setup first — **do not** fall back to asking questions (a cron job has nobody to answer).

---

## Hard constraints

- **MCP only.** Every number comes from an MCP call. If the Sophie Hub MCP isn't wired in, fail loudly. Never ask for an upload.
- **No fabrication — ever.** A "win" must be **real and validated against the trailing 4-week average**, not a one-week pop. If a store genuinely had a flat/bad week, the honest line is *"quiet week — no standout,"* never a hollow "ad spend went down" (which is usually sales cratering). A manufactured win destroys the brief's credibility faster than a missing one.
- **Criticals are never hidden.** A red flag (stockout, listing down) is **always visible in the first screen**, even on a great week — never buried below a divider or below the wins.
- **Signal only — never cry wolf.** Apply the volume/$ floors (below). Don't narrate a 200%-swing-on-$40. An unattended report that false-alarms gets muted by week four.
- **TACoS is the only profitability read.** Say **"efficient,"** never **"profitable"** — we don't have margin. An owner who intentionally loss-leads for rank/subscribers just sets a high target TACoS, and we grade against that.
- **Honest confidence.** When the data can't support a cause, say *"cause unclear — investigating,"* not a fabricated story. Lost-sales figures are **estimates** and must be phrased as such.
- **Flag essential gaps; never degrade silently.** If an essential input (ads, Sales & Traffic, orders) comes back blank, surface a **`⚠️ Data gap`** line so the reader knows we're flying blind on that metric — don't let a number quietly vanish or, worse, report a misleading `0%`. (Non-essential gaps like a missing restock snapshot get a quiet note.) See Phase 2.5.
- **Dollars within type, never across.** Rank flags inside their type (revenue-at-risk vs wasted-cost are different dollars). Never sort a $9k stockout against $1k wasted spend on one axis.
- **Currency matches each store's marketplace.** Read currency from a tool that returns it (`get_ads_summary.summary.currency`, `list_top_products[].currency`) or infer from `marketplace_id`. Each store in its own currency; no conversion.

---

## MCP tool prefix

The Sophie Hub MCP prefix is environment-specific (staging / prod / local — e.g. `mcp__claude_ai_Sophie_Hub__…`). At the start of every run, bind to whichever prefix exposes these tool names:

- `list_stores`
- `get_account_performance_summary` — headline (sales / ad spend / ad sales / organic / TACoS / sessions), one `view='overall'` call per window
- `query_sales_traffic` — per-ASIN `sessions`, `unit_session_percentage` (CVR = units/session), `buy_box_percentage` (the demand decomposition)
- `query_ppc` — `view='search_terms'` for the operator detail
- `list_top_products` — ASIN revenue + units (for movers and per-ASIN ASP / weekly revenue)
- `get_restock_recommendations` — Title-Case columns `"Total Days of Supply (including units from open shipments)"`, `"Alert"`, `"Sales last 30 days"`, `"Available"` (stockout flag); call with `alert_only=false`

Slack: bind to whichever prefix exposes `slack_send_message` (and `slack_search_channels`, used only in Setup). If no Slack MCP is wired in, compose the message and print it, and tell the user Slack isn't connected.

---

## Setup mode

A human is present, so this is the **only** place `AskUserQuestion` is allowed. Collect, confirm, then write `$CONFIG`.

1. **Stores** — call `list_stores`. Ask which stores to include (default: all). Resolve each to its `seller_id`. **Guard:** each store adds ~8–12 MCP calls per run (5 weekly headline buckets + traffic + search terms + products + inventory). If the list exceeds **~10 stores**, warn that a weekly run will be slow and quota-heavy, and suggest scoping to the brands that matter or splitting into two schedules.
2. **Slack channel** — ask for the destination; resolve a channel name to an ID via `slack_search_channels`. Never guess.
3. **Targets** — ask for **target TACoS** per store (one global value or per-store). This is the profitability spine and the owner's implicit break-even/strategy line. Also accept an optional target ACoS (demoted to detail).
4. **Optional — margin %** (per-SKU or blended). If given, the brief may grade the TACoS target as survivable; if omitted, never imply profitability.
5. **Optional — replenishment lead time** (weeks, default off). If given, unlocks the stockout **total-exposure** number; if omitted, the stockout flag shows the $/wk run-rate only.

Write a human-readable config file to **`$CONFIG`** (create `~/.claude/weekly-exec-summary-hub-v2/` if it doesn't exist) — this is the "memory md" every scheduled run reads:

```markdown
# Weekly Exec Summary — Config

## Stores
- <Store name> · seller_id: <id> · target TACoS: <x>% · target ACoS: <y>% · margin: <z>% (optional) · lead_time_weeks: <n> (optional)
- …

## Delivery
- slack_channel_id: <id>

## Open issues (auto-maintained by the scheduled run — do not edit by hand)
- (none yet)

## Last run
- (none yet)
```

Confirm the file back to the user, then tell them how to schedule it **in Claude Code** — e.g. *"Run `/schedule` to fire this weekly (Monday morning): the scheduled run reads `$CONFIG` and posts automatically."* The skill only needs `$CONFIG` to exist on the same machine the schedule runs on; it does not create the schedule itself.

---

## Scheduled run

Reads `$CONFIG`; asks nothing. Phases below.

### Phase 1 — Windows

| Window | Range | Use |
|---|---|---|
| `current` | today−7d → today−1d | this week |
| `prior` | today−14d → today−8d | WoW delta |
| `baseline` | trailing 4 weeks (today−28d → today−1d, by week) | trend; the anti-blip reference |

Pull the headline metrics as **per-week buckets for the last 5 weeks** (current + 4 prior) so you can both compute the 4-week average **and** detect "N weeks running" trends (e.g. TACoS over target 3 weeks straight). Prefer the widest single call per store and bucket into 7-day weeks; fall back to one call per week if a by-date view isn't available.

### Phase 2 — Pull data per store (parallelize across stores)

- **2a · Headline** — `get_account_performance_summary(store, view='overall', start_date, end_date)` for current, prior, and each of the 4 baseline weeks. Capture total revenue, ad spend, ad sales, organic, ACoS, **TACoS**, sessions, currency. **TACoS source (critical — verified live):** this tool returns `derived.tacos: 0` and `organic_share: null` when the store has **no Sales & Traffic data** (only ADS ingested). If `total_revenue == 0` or `metadata.sales_traffic_files_loaded == 0`, **never report TACoS as 0%** — it would tell a CEO "ads are free." Fall back to an **order-based proxy: `TACoS ≈ ad_spend ÷ order_revenue`**, where `order_revenue` is the **summed `list_top_products` revenue** (2d — already pulled, no extra tool needed). If that's also empty, print "efficiency unavailable — no revenue data."
- **2b · Per-ASIN demand** — `query_sales_traffic(store, view='by_asin')` for **current** and the **4-week baseline**. Capture per ASIN: `sessions`, `ordered_product_sales`, `units_ordered`, `unit_session_percentage_avg` (CVR = units/session), `buy_box_percentage_avg`. **If this returns `rows: []` / `files_loaded: 0`** (no S&T for the store — verified live), the demand decomposition **cannot run**: skip Type B entirely and fall back to the raw revenue movers from 2d. Never emit a demand estimate from empty traffic.
- **2c · Search terms** — `query_ppc(store, view='search_terms', start_date=current.start, end_date=current.end, limit=200)`. Rows carry spend, sales, `purchases`, ACoS, and a `source` (SP / SB / SP+SB).
- **2d · Products** — `list_top_products(store, start_date, end_date, sort_by='revenue', limit=20, compact=true)` for current and prior. Gives `asin`, `revenue`, `units_sold` → per-ASIN **ASP = revenue ÷ units**, the **ASIN revenue movers** (current vs prior delta), and the **order-revenue total** for the proxy-TACoS fallback (2a).
- **2e · Inventory** — `get_restock_recommendations(store, alert_only=false)`. **Always pass `alert_only=false`** — verified live that `alert_only=true` returns 0 rows even with a fresh snapshot, and the summary `alert_count` reported 0 despite many alerted rows. **Don't trust `alert_only` or `alert_count`; read the rows.** Real columns are **Title-Case with spaces** (not snake_case): `"ASIN"`, `"Available"`, `"Alert"` (`out_of_stock` / `low_stock` / empty), `"Total Days of Supply (including units from open shipments)"`, `"Days of Supply at Amazon Fulfillment Network"`, `"Sales last 30 days"`, `"Units Sold Last 30 Days"`, `"Recommended ship date"`, `"Recommended replenishment qty"`, `"Recommended action"`. Rows are **per-SKU/FNSKU — multiple rows per ASIN** (a healthy primary SKU often sits next to a dead `out_of_stock` duplicate with $0 sales). Roll-up rules in Type A.

### Phase 2.5 — Data-coverage check (flag essential blanks)

Before computing flags, check which inputs came back **blank**, and **flag the essential ones in the brief** — a CEO must know when we're flying blind, not silently see a metric vanish. Classify:

| Input | Essential? | If blank |
|---|---|---|
| Ads (`get_account_performance_summary` ads block) | **Essential** | Flag loudly — efficiency, search terms, wasted spend all depend on it. |
| Sales & Traffic (`total_revenue`/`sales_traffic_files_loaded`, `query_sales_traffic` rows) | **Essential** | Flag: "TACoS is an order-based proxy and demand can't be assessed — S&T data missing this week." |
| Orders / products (`list_top_products`) | **Essential** | Flag — revenue, movers, and the TACoS fallback all depend on it. |
| Restock snapshot | Non-essential | Quiet note ("no restock data"); omit the inventory section. |

Surface essential gaps as a **`⚠️ Data gap`** line in the brief (see Phase 4), and degrade the affected flags rather than fabricating around them. Never let an essential blank pass unmentioned.

### Phase 3 — Compute flags + dollars

All dollars are gross (no margin). **Rank within type, never across.** Apply the signal floors before anything reaches the message.

**Signal floors (config-adjustable defaults):**
- Demand/CVR estimate: ASIN needs **≥ 100 sessions** this week (below that, CVR is noise → suppress).
- Harvest candidate: **purchases ≥ 2**.
- Wasted spend: a term counts if **0 sales** AND (**spend ≥ $15 absolute** OR **> 5% of total search-term spend**). The 5%-only gate almost never fires — verified live, the biggest single zero-sale term was ~1–3% of spend — so the absolute floor is what surfaces real waste. Always also report **aggregate** zero-sale spend (Type C).
- Inventory: only flag an ASIN with **material recent sales** (`"Sales last 30 days" ≥ $50`) — dead $0 SKUs are not "at risk."
- ASIN mover / WoW delta: suppress if the absolute $ move is below a small floor (don't narrate trivia).

#### Type A — Revenue at risk (forward): Inventory
**Roll up to ASIN first.** Rows are per-SKU; group by `"ASIN"` and take the **actively-selling position** — sum `"Available"` across that ASIN's SKUs, and use the SKU(s) with non-zero `"Sales last 30 days"` for velocity. **Ignore dead duplicate SKUs** (`out_of_stock` with $0 sales) — they are not at risk. Drop any ASIN below the inventory sales floor.

For each surviving ASIN, take **days of cover** = `"Total Days of Supply (including units from open shipments)"` (fall back to the FC-network field), and **tier** it:
- 🔴 **< 14 days** (urgent) · 🟡 **14–45 days** (restock soon) · ℹ️ **45–90 days** (FYI only).
- **$/wk run-rate** = `"Sales last 30 days" ÷ 4.3` (summed across the ASIN's selling SKUs). Note direction if clearly growing/declining.
- Headline: *"~$408/wk, ~6 days cover, ship by Jun 2"* (`"Recommended ship date"`).
- **Total exposure** (`$/wk × lead_time_weeks`) only if lead time is configured — never fabricate a lead time.
- **Qualitative caveats** (one line, no number): *"partially offset by sibling variations"*; *"plus rank/organic recovery cost after restock."*
- **Rank the 🔴 tier by days-of-cover** (a 6-day fire beats a bigger-$ SKU at 26 days), then by $/wk; the 🟡/ℹ️ tiers rank by $/wk. Recommended call: **place the restock PO this week.**
- If no ASIN clears the floors, omit the inventory section.

#### Type B — Realized softness (this week): Demand
Per ASIN that cleared the session floor and whose sales fell, decompose vs the 4-week baseline:
```
lost units        = (CVR_4wk − CVR_now) × sessions_now          # CVR is units/session
buy-box lost units ≈ (BB_4wk − BB_now) × sessions_now × CVR_4wk  # sessions you lost the cart on
listing lost units = lost units − buy-box lost units              # residual: detail-page conversion
lost sales ≈ lost units × ASP_now                                 # ASP = revenue ÷ units (2d)
```
- Report as an **estimate**: *"≈€600 of softness — ~€420 lost buy-box (price/competition), ~€180 on-listing."*
- Two causes → two calls: buy-box loss → **check price/competition**; residual → **check the detail page**.
- **Price caveat:** if price rose this week, a CVR dip can be intentional — don't flag it as loss.
- **Severity & seasonality:** a large but *plausibly seasonal* drop (event/season-driven catalog — e.g. graduation gifts in late May; verified live on a −37% week) is **🟡 "worth watching — confirm cause,"** not a 🔴 emergency. Don't assert a seasonal cause you can't support; say *"likely seasonal — confirm it isn't a rank/impression loss."* A drop with healthy buy-box and steady CVR is **traffic/demand**, not listing or availability — say so.
- **No S&T data → skip this type** (see 2b) and report the raw revenue movers instead; the Data-gap line carries the "demand can't be assessed" note.
- Rank by lost-$.

#### Type C — Wasted cost (controllable): Wasted spend
Two sub-signals — report both; they catch different leaks:
1. **Zero-sale terms** — spend but **0 sales**, clearing the wasted floor (≥ $15 OR > 5% of search-term spend). List the top offenders by spend.
2. **Bleeding converters** — terms that *do* convert but at a punishing ACoS (e.g. **ACoS > 2× the account ACoS**, min ~$15 spend). A zero-sale rule misses these — verified live, one term spent $210 at 131% ACoS while "converting."
Also report the **aggregate** zero-sale spend (*"~$300 across N zero-sale terms"*) so death-by-a-thousand-cuts waste is visible even when no single term is large.
- Headline = the **spend** ("$X, 0 attributed sales" / "$X at 131% ACoS") — controllable cost, ~100% recoverable.
- Call: **negative-keyword sweep** (zero-sale) / **cut bids or pause** (bleeding converters). Rank by spend.

#### Wins (Type: positive — leads the message)
Surface only **real, material** wins, each **validated against the 4-week trend**:
- **best week in the trailing 4**, TACoS crossing **under** target, an ASIN breakout vs its 4-wk avg, organic share up vs the 4-wk avg, a multi-week improving streak. (We only hold ~4–5 weeks of data — never claim an all-time "record" we can't verify.)
- If a store has no genuine win, say *"quiet week — no standout."* Do not manufacture one.

#### Accountability loop
Compare this run's flags to the `Open issues` persisted in `$CONFIG`:
- A prior flag no longer present → mark *"no longer flagged"* (NOT "you fixed it" — a cleared stockout could be a restock *or* a sales collapse; a dropped wasted term could be negated *or* just stopped spending).
- A prior flag still present → *"Brand C efficiency — still open (week N)."*
- Then overwrite `Open issues` with this run's flags for next week.

### Phase 4 — Compose the single message

One Slack message (mrkdwn). **Highlights first, detail below**, split by a divider. Order: **Net verdict → Wins → [adaptive attention header] (ranked within type) → ━ Detail ━.**

```
Executive Summary for <current.start spelled out> to <current.end spelled out>

*Net:* Portfolio <currency><total> (<WoW>% WoW, <vs-4wk>% vs 4-wk) — <one-word health>. <The single call needed this week>.

⚠️ *Data gap:* <only if an essential input was blank — e.g. "no Sales & Traffic for Brand X — TACoS is an order-based proxy, demand not assessed.">

✅ *Wins*
🏆 <Store> — <real win, validated vs 4-wk>
📈 <Store> — <real win>

⚠️ *Action needed*           (header = "Action needed" if any 🔴, else "Worth watching"; grouped by type, ranked within each by $)
🔴 <Store> — <stockout: $/wk, ~Nd cover> → place restock PO this week
🟡 <Store> — TACoS <x>% vs <target>% target, ↑<N> wks → <call>
🟡 <Store> — demand ≈<currency><lost> soft (buy-box <a> / listing <b>) → <calls>
   <wasted spend lines, etc.>
↳ _carried over: <prior open issue> — still open (week N)._

━━━━━ *Detail* ━━━━━           (Watch stores only; on-track stores stay one line above)
*<Store>* — TACoS <x>% (target <y>%) · sales <wow>% WoW, <vs4wk> vs 4-wk
⚠️ Demand: <decomposition, estimate-framed>
• Harvest potential KWs: `<term>` (<orders> ord, <acos>% ACoS) · `<term>` (…)
• Top Spending KWs: `<term>` (<currency><spend>, <acos>%) · `<term>` (…)
• Wasted Spend: `<term>` (<currency><spend>, 0 sales) · ~<currency><agg> across <N> zero-sale terms ⚠️
• ASIN highlights: top `<asin>` (<currency><delta> WoW) · watch `<asin>` (<currency><delta> WoW)
```

**Layout rules:**
- **Header** is spelled out: `Executive Summary for May 12 to 18` (full month, "to", no en-dash).
- **Net verdict** is one line: state of the business + the single most important call. A CEO reads this and nothing else, and still knows what to do.
- **Data gap line** sits right under the verdict (above wins) whenever an essential input was blank — the reader must see it before reading numbers that depend on it. Omit when coverage is complete.
- **Wins lead**, but a **critical 🔴 always appears in the first screen** (right under the wins) even on a great week.
- **The attention header adapts to severity:** *"Action needed"* when any 🔴 fires, *"Worth watching"* when only 🟡/ℹ️, and **omit the section** (verdict says "nothing urgent") when clean. Grouped by type (revenue-at-risk / efficiency / softness / wasted), ranked within each by $; every line ends in a **recommended call**.
- **On-track stores collapse to one glance line** with no detail block — there's nothing to act on.
- **Only Watch stores expand** into the Detail zone (decomposition + operator bullets). Search-term/ASIN detail and ACoS live here, for the hands-on owners.

**Voice:** decisive and pre-digested, like a trusted operator — "TACoS drifting 3 weeks → pull broad-match (unless intentional for the launch)." Use `~` for rounded figures. Never invent context (no "lines up with last week's launch" unless the user logged one). Estimates say "≈" and "attributable."

### Phase 5 — Post + persist

1. `slack_send_message(channel=<config channel>, text=<composed message>)`.
2. Update `$CONFIG`: overwrite `Open issues` with this run's flags, and stamp `Last run`.
3. Surface to the user (or run log): a 1-line confirmation (+ permalink if returned) and the full message text as a fenced block. If the Slack post fails, show the error — do **not** silently retry.

---

## Failure modes — surface explicitly, never paper over

| Symptom | What to do |
|---|---|
| No Sophie Hub MCP wired in | Abort. The skill requires Sophie Hub MCP. |
| Scheduled run, no `$CONFIG` | Abort: "Run Setup first." Never fall back to prompting. |
| No Slack MCP | Compose + print the message; tell the user to paste it. |
| `list_stores` returns 0 | Abort: "no stores connected." |
| Store has < 5 weeks of history (new) | Skip the 4-wk trend for that store; report current-week only with a one-line "store is new to Hub — no trend yet." Don't fabricate a baseline. |
| **No Sales & Traffic data** (`total_revenue==0`, `sales_traffic_files_loaded==0`, `query_sales_traffic` empty) | **Flag it** as a Data gap. Don't print TACoS 0% — use the order-based proxy (2a). Skip the demand decomposition (2b); fall back to raw revenue movers. |
| **Any essential input blank** (ads / S&T / orders) | Add a `⚠️ Data gap` line; degrade the affected flags, never fabricate around the hole. |
| ASIN below the session floor | Suppress its demand estimate (noise). |
| No term clears the wasted floors | Omit zero-sale offenders, but still report aggregate zero-sale spend if material. |
| `get_restock_recommendations` empty / no snapshot | Omit the inventory section; quiet note "no restock data." Don't rely on `alert_only`/`alert_count` — read the rows. |
| Slack post fails | Show error, offer to re-send, no auto-retry. |

---

## Example output (reference shape — numbers will be live)

```
Executive Summary for May 12 to 18

*Net:* Portfolio $48.2k (+6% WoW, +3% vs 4-wk) — healthy. One call this week: Brand A restock (~$9k/wk at risk). One to watch: Brand C efficiency (week 3).

✅ *Wins*
🏆 *Brand B* — best week in 4, $12.4k (+18% WoW, +14% vs 4-wk) · TACoS 12%
📈 *Brand D* — TACoS 14%→11%, now under the 12% target (4 wks improving)

⚠️ *Action needed*
🔴 *Brand A* — hero SKU B0AAA ~9 days cover → ~$2.3k/wk at risk (declining SKU; partly offset by variations; plus rank-recovery cost after restock). *Place restock PO this week.*
🟡 *Brand C* — TACoS 31% vs 20% target, ↑3 wks → ~€600/wk over target. *Pull broad-match, unless intentional.*
🟡 *Brand C* — demand ≈€600 soft this week: ~€420 lost buy-box (price/competition), ~€180 on-listing. *Check the price war + the detail page.*
↳ _carried over: Brand C efficiency flagged 2 wks ago — still open (week 3)._

━━━━━ *Detail* ━━━━━
*Brand C* — TACoS 31% (target 20%) · sales −15% WoW, flat vs 4-wk · buy-box 96%→72%
⚠️ Demand: the drop is conversion, not traffic — CVR 8%→5%, sessions flat (est., ≈€600).
• Harvest potential KWs: `example term` (6 ord, 14% ACoS) · `example term` (4 ord, 18%)  [SP+SB]
• Top Spending KWs: `example term` (€41, 22% ACoS) · `example term` (€33, 41%)
• Wasted Spend: `example term` (€38, 0 sales) · ~€120 across 9 zero-sale terms ⚠️
• ASIN highlights: top `B0XXXXXX1` (+€88 WoW) · watch `B0YYYYYY7` (−€42 WoW)
```

A store missing essential data reads like this instead — the gap is flagged, not hidden:

```
*Net:* Pili Hunters — soft week, revenue ~$6.3k (−9% WoW). Ad efficiency steady (~4% TACoS, proxy). One call: Raw Cacao 16oz ~6 days cover (~$408/wk).
⚠️ *Data gap:* no Sales & Traffic this week — TACoS is an order-based proxy and demand softness can't be assessed.
```
