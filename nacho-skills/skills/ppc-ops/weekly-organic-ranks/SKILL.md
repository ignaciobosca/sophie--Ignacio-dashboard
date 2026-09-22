---
name: weekly-organic-ranks
description: >
  Generate a Sophie Society Weekly Organic Ranks message for an Amazon client from a SINGLE
  call — no XLSX, no manual download. For each managed ASIN it pulls the tracked-keyword
  organic ranks from Shurq, snapshots them into Supabase, diffs week-over-week against last
  week's snapshot, and writes a Slack-ready internal brief (Resumen + per-product movers +
  Foco) covering the keywords that moved and the page-1 footprint. Trigger whenever Nacho says
  "ranks para [Brand]", "organic ranks for [Brand]", "movimientos de keywords de [Brand]",
  "weekly ranks [Brand]", "rank movers para [Brand]", "cómo se movieron los ranks de [Brand]",
  or any "ranks"/"rankings"/"organic"/"keyword movements" + a client brand name. Single-brand
  mode — for multi-marketplace clients (US + CA) generate one message per marketplace. Also
  runs unattended as a weekly cloud Routine across all active clients.
---

# Weekly Organic Ranks Skill — Shurq + Supabase (V1)

**Versión actual:** V1 (2026-08-24) — ver changelog en `memory/weekly_organic_ranks_changelog.md`

You generate a Sophie Society **Weekly Organic Ranks** brief — a Slack-ready internal touchpoint
(operational tone, for the pod) that reports how each managed product's **organic search-term
ranks** moved week-over-week. Data comes from **Shurq** (organic rank tracking). Movement is
computed by **diffing this week's snapshot against last week's**, both stored in a Supabase table.

Unlike weekly-report/weekly-wins, this is **not** a PPC/KPI report — it is purely about **organic
keyword positions**: which search terms climbed, which dropped, and the page-1 footprint.

Week convention: the **run date** is the snapshot's `week_date`. The comparison baseline is the
**most recent prior snapshot** for that brand+marketplace (normally 7 days earlier).

---

## Global config & constants

```
Supabase project:      POD 66 - Organization  ->  awhiobrcgghyiycxukjm
Config table:          public.clients            (column config jsonb)
Snapshot table:        public.organic_rank_snapshots
Shurq tools:           get_all_tracked_keywords (primary), get_organic_rank_trend (backfill/detail)
Slack:                 slack_send_message  ->  cfg.slack_internal_channel_id  (internal, Routine-safe)
Report language:       cfg.report_language ("es" default here — internal pod brief; "en" if set)
```

**Movement thresholds (locked with Nacho):**
- A keyword is a **mover** only if `abs(delta) >= 3` positions **AND** `abs(delta) >= 0.10 * prev_rank`.
  (Both conditions — the ±3 floor kills top-rank micro-noise like 5→4; the 10% keeps it relative.)
- `delta = prev_rank - curr_rank`  →  **positive = improved (subió)**, negative = worsened (bajó).
  Remember: *rank up = smaller number*.
- Show **top 5 subas + top 5 bajas per product**, ordered by `abs(delta)` desc.
- **Página 1** = `organic_rank <= 48`. **Top-10** = `organic_rank <= 10`.

**Marketplace string → Shurq `marketplace_id`:**
```
US=1, GB=2, UK=2, CA=4, MX=5, BR=6, DE=7, ES=8, FR=9, IT=10, NL=16, SE=20, PL=19, BE=21, AE=15, SA=23, IE=24
```
(`UK` is an alias of `GB`=2 — some configs store the marketplace as "UK", e.g. Every Cloud, Zola Zola.)

---

## Step 1: Resolve brand → load config(s) from Supabase

```sql
-- Supabase MCP execute_sql on project awhiobrcgghyiycxukjm
SELECT brand, active, config
FROM clients
WHERE active = true
  AND (
        lower(brand)                 LIKE '%' || lower(:requested_brand) || '%'
     OR lower(config->>'brand_name')  LIKE '%' || lower(:requested_brand) || '%'
     OR EXISTS (
          SELECT 1 FROM jsonb_array_elements_text(coalesce(config->'alternative_names','[]'::jsonb)) alt
          WHERE lower(alt) LIKE '%' || lower(:requested_brand) || '%'
        )
  );
```

- **1 row** → run once.
- **2+ rows** (multi-marketplace, e.g. Happy Fox US + CA) → tell Nacho up-front, run once per row, one Slack message each.
- **0 rows** → suggest `client-onboarding`; do not fabricate.

**Fields used from `config`:**

| Field | Required | Use |
|---|---|---|
| `brand_name` | ✅ | Display name |
| `managed_asins` | ✅ | List of `{asin, name}` — the products to report |
| `amazon_marketplace` | ✅ | "US"/"CA"/… → `marketplace_id` via the map above |
| `shurq_account_id` | ✅ | Shurq account (e.g. Happy Fox = 842). **If missing**, resolve via `list_my_accounts` by matching `seller_name` to the brand, warn Nacho, and suggest backfilling it into config. |
| `slack_internal_channel_id` | ✅ | Destination channel |
| `report_language` | rec | "es" (default) / "en" |

Validate `managed_asins`, `shurq_account_id`, `amazon_marketplace`, `slack_internal_channel_id`.
Missing a required field → warn and skip that brand.

---

## Step 2: Pull tracked-keyword organic ranks from Shurq

Do the whole pull inside **one** Shurq `execute` call (the sandbox loops internally — one round
trip). For each ASIN call `get_all_tracked_keywords`. Emit ready-to-insert SQL VALUES rows for
this week's snapshot, and record coverage per ASIN.

> Shurq sandbox notes: **restricted Python** — no `%` string formatting (use concatenation),
> no `Date.now()`/`date.today()` (pass the run date as a literal string), `import json` is OK,
> and `call_tool` returns a dict whose `result` is a JSON **string** you must `json.loads`.

```python
import json
asins = [ (a["asin"], a["name"]) for a in cfg["managed_asins"] ]   # from config
ACC = int(cfg["shurq_account_id"])
MKP_ID = MKP_MAP[cfg["amazon_marketplace"]]     # e.g. US -> 1
MKP = cfg["amazon_marketplace"]                 # stored as the string in the table
WEEK = run_date_iso                             # 'YYYY-MM-DD' — the run date, injected by the skill

def esc(s): return str(s).replace("'", "''")
def num(v): return "NULL" if v is None else str(int(v))
def boolv(v): return "true" if v else "false"

rows, coverage = [], {}
for asin, name in asins:
    r = await call_tool("get_all_tracked_keywords",
                        {"account_id": ACC, "marketplace_id": MKP_ID, "asin": asin, "days": 14})
    d = r.get("result") if isinstance(r, dict) else r
    if isinstance(d, str): d = json.loads(d)
    kws = d.get("data", [])
    coverage[asin] = len(kws)
    for k in kws:
        rows.append(
          "('" + esc(cfg["brand_name"]) + "','" + MKP + "'," + str(ACC) + ",'" + asin + "','"
          + esc(name) + "','" + esc(k.get("keyword")) + "',"
          + num(k.get("organic_rank")) + "," + num(k.get("page")) + "," + num(k.get("sponsored_rank")) + ","
          + num(k.get("best_rank_30d")) + "," + num(k.get("worst_rank_30d")) + "," + num(k.get("data_points")) + ","
          + boolv(k.get("best_seller")) + "," + boolv(k.get("amazon_choice")) + ",'" + WEEK + "')")
return {"coverage": coverage, "values": ",\n".join(rows)}
```

- ASINs with **0 tracked keywords** are real (Shurq only tracks keyword+ASIN pairs that have
  been added). Record them for the coverage note; they do not block the run.
- If **every** ASIN returns 0 → tell Nacho no tracked keywords exist for this brand yet (nothing
  to report); suggest tracking the priority terms in Shurq.

---

## Step 3: Upsert this week's snapshot into Supabase

```sql
INSERT INTO public.organic_rank_snapshots
(brand,marketplace,account_id,asin,asin_name,keyword,organic_rank,page,sponsored_rank,
 best_rank_30d,worst_rank_30d,data_points,best_seller,amazon_choice,week_date)
VALUES
  <the VALUES string from Step 2>
ON CONFLICT (brand,marketplace,asin,keyword,week_date) DO UPDATE
SET organic_rank=excluded.organic_rank, page=excluded.page,
    best_rank_30d=excluded.best_rank_30d, worst_rank_30d=excluded.worst_rank_30d,
    data_points=excluded.data_points, sponsored_rank=excluded.sponsored_rank;
```

The unique index `(brand,marketplace,asin,keyword,week_date)` makes re-runs on the same day
idempotent.

**Table schema (already created):**
```
organic_rank_snapshots(
  id, brand, marketplace, account_id, asin, asin_name, keyword,
  organic_rank, page, sponsored_rank, best_rank_30d, worst_rank_30d, data_points,
  best_seller, amazon_choice, week_date, created_at
)
```

---

## Step 4: Diff week-over-week (the movement engine)

Find the previous snapshot date and diff on `(asin, keyword)`. All classification is done in
SQL so it is deterministic; the message step only renders the rows.

```sql
WITH curr_date AS (
  SELECT max(week_date) d FROM organic_rank_snapshots
  WHERE brand=:brand AND marketplace=:mkp
),
prev_date AS (
  SELECT max(week_date) d FROM organic_rank_snapshots
  WHERE brand=:brand AND marketplace=:mkp
    AND week_date < (SELECT d FROM curr_date)
),
c AS (
  SELECT asin,asin_name,keyword,organic_rank FROM organic_rank_snapshots
  WHERE brand=:brand AND marketplace=:mkp AND week_date=(SELECT d FROM curr_date)
),
p AS (
  SELECT asin,keyword,organic_rank FROM organic_rank_snapshots
  WHERE brand=:brand AND marketplace=:mkp AND week_date=(SELECT d FROM prev_date)
)
SELECT c.asin, c.asin_name, c.keyword,
       p.organic_rank AS prev, c.organic_rank AS curr,
       (p.organic_rank - c.organic_rank) AS delta,
       CASE WHEN abs(p.organic_rank - c.organic_rank) >= 3
             AND abs(p.organic_rank - c.organic_rank) >= 0.10*p.organic_rank
            THEN true ELSE false END AS is_mover,
       CASE WHEN c.organic_rank<=48 AND p.organic_rank>48 THEN 'ENTERS_P1'
            WHEN c.organic_rank>48 AND p.organic_rank<=48 THEN 'EXITS_P1'
            ELSE '' END AS p1_move
FROM c JOIN p ON c.asin=p.asin AND c.keyword=p.keyword
ORDER BY c.asin_name, delta DESC;
```

Also compute, per product, the **status counts** from the current snapshot (and the prior one
for the P1 delta):

```sql
-- current-week status per ASIN
SELECT asin, asin_name,
       count(*) FILTER (WHERE organic_rank<=48) AS p1,
       count(*) FILTER (WHERE organic_rank<=10) AS top10
FROM organic_rank_snapshots
WHERE brand=:brand AND marketplace=:mkp AND week_date=(SELECT max(week_date) ...)
GROUP BY asin, asin_name;
```

**First run / no prior snapshot** (`prev_date` is null): there are no movers yet. Post a short
baseline message — current page-1 footprint per product + coverage — and note that movers start
next week. Never fabricate movement.

**Classification from the diff rows:**
- **Subas** = `is_mover AND delta>0`, top 5 by `delta` desc.
- **Bajas** = `is_mover AND delta<0`, top 5 by `abs(delta)` desc.
- Tag `⚠️ salió de P1` on EXITS_P1 rows and `✨ entró a P1` on ENTERS_P1 rows.
- Movers are **not** restricted to page 1 — the biggest real moves live on pages 2–5, and a
  keyword that fell off page 1 is exactly what to flag.

---

## Step 5: Write the message (internal pod brief)

Slack plain text. Bold with `*asterisks*`, italics `_underscores_`. Default language **Spanish**
(internal brief); use English if `report_language == "en"`. Keyword bullets are **one KW per
line**, indented under the product. Header uses the current snapshot date and the prior one.

**Writing rules (inherited house style):**
- **Keyword formatting — NEVER wrap keywords in backticks or any code/monospace formatting.**
  Slack renders inline code in **red**, which reads like an error. Put each keyword in **Slack
  bold** (`*keyword*`) — never `` `keyword` ``. Plain text is also acceptable, but never code.
- **Never** use the em dash `—` (not even as a separator between keyword and rank — use `·`, a
  colon, `→`, or parentheses instead).
- **Never** use the tilde `~` for approximations (write "cerca de"/"about").
- Ground every claim in the numbers; never invent causality for a move (you may *suggest*
  possible drivers as hypotheses in Foco, phrased as such).

**Structure:**

```
📊 *Organic Ranks — [Brand] ([MKP])* · Semana [curr_date short]
_vs semana anterior ([prev_date short]) · fuente: Shurq · [N] keywords trackeadas en [M]/[Total] productos_

*Resumen de la semana*
[One paragraph, 3–5 sentences. Lead with the net picture: X keywords subieron / Y bajaron
(piso ±3 y ≥10%), and the page-1 footprint change (net + which entered/exited). Then the single
strongest win (product + its climbing terms) and the single biggest concern (product + its
dropping terms). Direct, operational, no hype.]

*Por producto*

[emoji] *[Product name]* · P1: [p1] ([prevP1]→[currP1]) · Top-10: [top10]
 ▲ *Subieron*
　• *[kw]* [prev] → [curr] (▲[delta])
　• …  (top 5)
 ▼ *Bajaron*
　• *[kw]* [prev] → [curr] (▼[abs delta]) [⚠️ salió de P1]
　• …  (top 5)

[…repeat per product with tracked keywords…]

*Foco de la semana*
 • [1–3 operational bullets: biggest declines to investigate, wins to reinforce, near-P1 pushes.
   Tie each to a product and an action.]

⚪ _[K] ASINs sin keywords trackeadas en Shurq ([names]). Si querés cobertura, hay que trackearlos._
```

> Keywords go in **bold** (`*kw*`), never backticks. Note the header/product separators use `·`,
> not `—`.

### First-run / baseline message (no prior snapshot)

Same header, but no movers yet. Show the current page-1 footprint and top current positions per
product, keywords in **bold**, no em dashes:

```
📊 *Organic Ranks — [Brand] ([MKP])* · Semana [curr_date short]
_Primer snapshot de la semana · fuente: Shurq · [N] keywords trackeadas en [M]/[Total] productos_

*Resumen*
[2–4 sentences: this is the first snapshot, so no WoW comparison yet (starts next week). State
the page-1 / top-10 footprint and each product's best current position.]

*Por producto*

[emoji] *[Product name]* · P1: [p1] · Top-10: [top10]
　• *[kw]* rank [rank] (pág [page])
　• …  (top ~5 by rank; then "([K] más trackeadas, todas pág X+)")

⚪ _[coverage note if any ASIN has 0 tracked keywords]_
```

**Per-product emoji cue** (quick visual health of the week's movement, not absolute rank):
- 🟢 net positive movement or clear wins · 🔴 broadly declining (bajas dominate) · 🟡 flat / low signal (few movers, no page-1 presence).

**Ordering of products:** those with tracked keywords first (roughly by page-1 footprint /
significance), products with 0 tracked keywords go only into the coverage note.

**Multi-marketplace:** one message per marketplace; mention the marketplace in the header.

---

## Step 6: Send to the internal Slack channel

- Send with **`slack_send_message`** directly to `cfg.slack_internal_channel_id` (internal
  channel, Routine-safe — same rationale as weekly-report: a direct internal post is more robust
  under a scheduled Routine than a draft, and it is reviewed before reaching the client).
- Missing/null channel → output the message inline to Nacho with a note.
- Multi-marketplace → one message per marketplace; tell Nacho how many and where.

---

## Edge cases

| Situation | Behavior |
|---|---|
| Brand not in Supabase `clients` | Suggest `client-onboarding`; do not fabricate |
| Missing `shurq_account_id` | Resolve via `list_my_accounts` (match seller_name), warn, suggest backfill; skip if unresolved |
| Missing `managed_asins` / `amazon_marketplace` | Flag + skip brand |
| Missing `slack_internal_channel_id` | Output inline, skip send |
| One ASIN has 0 tracked keywords | Include it in the coverage note; continue with the rest |
| ALL ASINs have 0 tracked keywords | Tell Nacho there is nothing to report; suggest tracking priority terms in Shurq |
| No prior snapshot (first run) | Baseline message (P1 footprint + coverage), note movers begin next week |
| Prior snapshot older than ~10 days (missed a week) | Still diff against it; note the comparison window is longer than 7 days |
| Keyword present this week but not last week | Not shown as a mover (no baseline); it just contributes to the current P1 counts |
| `report_language: "en"` | Full English translation, same structure |
| Multi-marketplace (US + CA) | One snapshot + one message per marketplace |

---

## Data-source quick reference

| Need | Source | Key call |
|---|---|---|
| Client config | Supabase `clients` | `execute_sql` (project awhiobrcgghyiycxukjm) |
| Tracked keyword ranks | Shurq | `get_all_tracked_keywords` (1 call/ASIN, looped in one sandbox `execute`) |
| Per-keyword daily history (backfill/detail) | Shurq | `get_organic_rank_trend` (asin + keyword + days) |
| Snapshot store + WoW diff | Supabase `organic_rank_snapshots` | `execute_sql` (upsert + diff query) |
| Output | Slack | `slack_send_message` to the internal channel |

---

## Notes for scheduling as a Routine

- All-active-clients pass: `SELECT brand, config FROM clients WHERE active = true`, then run
  Steps 1b–6 per brand (one message per marketplace row).
- Cadence: weekly. Because movement is snapshot-diff based, the Routine must run on a **fixed
  weekly day** so the prior snapshot is consistently ~7 days back.
- `run_date_iso` in a Routine = the day the Routine fires (available to the runtime); pass it as
  the literal `WEEK` string into the Shurq sandbox and the SQL.
