---
name: client-reply-drafter
description: Scans every Sophie Society external client Slack channel (`[account]-sophie`) for unanswered client messages — top-level posts and thread replies — and pre-stages a reply draft via `slack_send_message_draft` in Nacho's voice, grounded in channel + `-sophie-internal` history. When a client asks a data question, it pulls the real figure (with its time window) into the draft, trying sources in order Shurq → Sophie Hub → Helium10, plus ClickUp/Notion/Read.ai for task status and meeting context. Never invents numbers. Trigger on "draft my client replies", "draftea mis respuestas a clientes", "revisá los canales de clientes", "qué clientes me están esperando", "check my client channels", "run the client drafter", "draft de respuestas en slack", "any client questions I missed?", or any phrasing about catching up on drafting answers for Sophie Society client channels. Runs 5x/day BA as the `client-reply-drafter` cloud Routine. Never auto-sends — drafts only.
---

# Client Reply Drafter

A focused, low-friction skill that watches every Sophie Society external client Slack channel and pre-stages a reply draft inside the message box of any channel/thread where a client is waiting on Nacho. Five checkpoints a day. One status line per run so Nacho can see at a glance what was drafted and where.

## Why this exists

Nacho runs many client accounts at once. Clients ping in their `-sophie` Slack channels constantly — new top-level questions AND replies inside existing threads — and the cost of a slow response compounds (clients perceive distance, threads pile up, internal team loses momentum). Most of those replies are tractable from the channel's own history plus what the internal team has been discussing in the matching `-sophie-internal` channel; some require pulling a number or a status from Shurq, Sophie Hub, ClickUp or Notion.

The skill exists so that, when Nacho opens Slack, **the right reply is already typed into the message box** for every channel/thread where a client is waiting. He reads it, edits a word or two if needed, and hits Enter. No "let me think and write from scratch" tax.

Critically: **never auto-send.** Drafts only.

## Configuration

Stable defaults. Don't change unless Nacho asks.

- **Slack workspace**: Sophie Society (the workspace where Nacho is signed in)
- **External channel pattern**: name ends in `-sophie` (e.g., `aironex-sophie`, `krauterland-sophie`). These are Slack Connect channels shared with clients.
- **Internal channel pattern**: name ends in `-sophie-internal` (e.g., `aironex-sophie-internal`). Internal-only — read for context, **never post drafts here**.
- **Status DM target**: `#client-drafts-nacho` if it exists, else Slackbot DM (`U084BE9B421`). One short status line per run.
- **Schedule**: 9am, 12pm, 3pm, 6pm, 10pm America/Argentina/Buenos_Aires (UTC-3). Runs as a **cloud Routine** (`client-reply-drafter`, trigger id `trig_01BevLxL3DoATGYf6onDg29x`) in the `Daily Check` environment — cron `0 1,12,15,18,21 * * *` (UTC). This replaced the old Cowork task. Manage it via the `RemoteTrigger` tool / https://claude.ai/code/routines.
- **Look-back window**: messages newer than `now - 14h`. This is wider than the longest cadence gap (the 11h overnight gap between 10pm and 9am BA time) so messages sent in the early hours are never missed. The state-file dedup (Step 3) prevents the wider window from causing duplicate-draft churn.
- **Stale-message handling**: **no hard cut-off.** If a client message has no team reply, it stays eligible for drafting on every subsequent run until somebody on the team responds. The state file makes this cheap — a thread we've already drafted for, and that has had no new client/team activity since, will be re-evaluated but **not re-drafted unless context has changed** (see Step 3).
- **Per-channel draft cap**: 5 drafts per channel per run. If more would qualify, draft the 5 most recent client messages and mention the overflow in the status DM.
- **Total draft cap**: 40 drafts per run. Above this, stop drafting and surface the overflow.
- **State file**: `client-reply-drafter/state.json` inside the current session's skill working dir. Keyed by `<channel_id>:<message_ts>` → `{last_drafted_at, draft_text_hash, client_msg_ts, internal_context_hash, channel_name}`. Used purely for "have I already drafted this exact thing?" dedup. Safe to delete; will be recreated. If the canonical path is read-only, fall back to a `state-client-reply-drafter.json` in the session's working dir and log the fallback once in the status DM footer.
- **Channel registry file**: same folder, `channels.json` — `{known_channel_ids: [...], first_seen: {channel_id: iso_timestamp}}`. Used to silently track newly onboarded clients and to fall back when Slack search lags.

## Voice & tone (the most important section)

Drafts must sound like Nacho. Before drafting in a given client channel, **always sample Nacho's recent voice in that channel first** — the way he writes to one client is not the way he writes to another, and he code-switches between Spanish and English depending on the client.

1. Pull the last ~50 messages in the channel via `slack_read_channel` (you'll already be doing this for context — reuse).
2. Filter to messages authored by Nacho (sender id `U084BE9B421`).
3. Note:
   - Average length (one-liner vs paragraph)
   - Greeting style (does he open with "Hi <Name>", "Hola", "Hey", or just dive in?)
   - Sign-off style (does he sign with "Nacho", "N", just a thumbs-up emoji, or nothing?)
   - Emoji usage (sparse, moderate, heavy)
   - **Spanish vs English** — Nacho code-switches heavily. With LATAm / Spanish-speaking clients he writes in Spanish; with US / EU clients in English. Mirror what he uses in this specific channel.
   - Use of bullet points vs prose

Match what you see. If Nacho never signs messages in that channel, don't add a sign-off. If he keeps it to two sentences, keep yours to two sentences.

If you have no Nacho messages in that channel yet (brand new client), default to: short, warm, professional, lowercase-first-word friendly opener, no emoji, no sign-off. Language defaults to the language the **client** is using. English example:

> Hey! Looking into this now — will share what I find later today. Quick clarifying question first: are you seeing this on SP, SB, or both?

Spanish example:

> Hola! Lo estoy revisando ahora — te paso lo que encuentre más tarde hoy. Una pregunta rápida antes: ¿lo estás viendo en SP, SB, o ambos?

Don't sound like an assistant. Don't write "Per your request" or "I hope this email finds you well" or "Please don't hesitate to" or "Quedo a su disposición". Nacho doesn't write like that.

## Workflow

Execute these steps in order. Don't skip Step 3's dedup or you'll churn the message box.

### Step 1 — Resolve channels and time window

**1a. Enumerate every `*-sophie` external channel (belt + suspenders).** Slack's search index lags for newly created channels, so use multiple sources and union the results:

1. `slack_search_channels` with query `-sophie` — capture all results, paginate if needed.
2. `slack_search_channels` with query `sophie` (broader — catches channels whose suffix changed or that include extra tokens).
3. Load the channel registry file (`channels.json`) and include every previously-known channel id.
4. If a `slack_list_user_conversations`-style endpoint is available, enumerate every channel Nacho is a member of and filter client-side.
5. **Filter**: keep channels whose name matches `^[a-z0-9][a-z0-9-]*-sophie$` AND does NOT end in `-sophie-internal`. Drop archived channels and channels Nacho is not a member of.
6. **Update the registry**: any channel in the resulting set that's NOT in `known_channel_ids` is silently added with `first_seen = now`. New channels participate in this very run — no waiting cycle.
7. **Sanity check**: if the new set is more than 25% smaller than the registry (likely a Slack search hiccup), use the registry as the authoritative list for this run and add a footer to the status DM: `:warning: Slack channel search returned fewer results than expected; used cached registry.`

**1b. Resolve the status DM target:**
- Try `slack_search_channels` for `client-drafts-nacho`. If found, capture `channel_id`.
- Otherwise use Slackbot DM `U084BE9B421` and add the "create this channel" footer hint to the status post.

**1c. Compute the look-back window:**
- Lower bound = `now - 14h` (Unix timestamp).
- Upper bound = `now`.

### Step 2 — Find unanswered client messages in each external channel

For each `*-sophie` channel, identify messages that need a reply. A message qualifies as "unanswered" if **all** of these are true:

- It was sent within the look-back window (top-level OR thread reply).
- The author is **not** on the Sophie Society team. Team membership signal: sender's email domain is `sophiesociety.com`, OR sender is in the known team-member ID list (see "Team member IDs" below). Cache the membership lookup per user_id to avoid repeated profile reads.
- The message contains substantive content (skip if it's only an emoji reaction-style message, a single ack like "ok", "thanks!", "got it", "👍", "dale", "listo" — those don't need a drafted reply).
- For top-level messages: no Sophie team member has posted any reply (top-level OR in-thread) after this message's timestamp.
- For in-thread messages: the latest reply in the thread is from the client (not from Sophie team), AND no team member has replied after this client reply.

**Thread detection — do this aggressively, not cheaply.** The biggest historical miss has been clients replying inside older threads. Use this procedure:

1. Read the last ~150 top-level messages of the channel via `slack_read_channel` (covers ~7–14 days of activity in most channels).
2. For every top-level message with `reply_count > 0` AND `latest_reply` within the last 14 days (NOT just the look-back window), call `slack_read_thread`.
3. For each thread, find the most recent client message. If that client message is within the look-back window AND no team member has replied after it, it qualifies.
4. Edge case: a client may have replied to a thread that's months old. As long as their reply is within the look-back window, draft it.

The 14-day thread overflow is intentional — quiet threads where a client just pinged "still waiting on this?" / "alguna novedad?" are exactly the conversations we don't want to miss.

For each qualifying message, capture:
- `channel_id`, `channel_name` (the `[account]-sophie` slug)
- `ts` (the client message timestamp — needed for `slack_send_message_draft` to target the right thread context)
- `thread_ts` (if it's a thread reply; otherwise null = a brand-new top-level conversation)
- `author_display_name`, `user_id`
- `message_text`
- Any attachments / files / links the client shared (record file IDs + names — see "Attachment handling" below)
- `permalink` (Slack returns it on most read operations; use directly in the status DM)
- **Urgency signal** (see Step 5b)

### Step 3 — Dedup against existing drafts, recent team replies, and prior runs

Before drafting, run these checks in order. The intent: this skill should feel additive, not overwrite-y.

**3a. Has a team member replied in the meantime?** Re-fetch the latest state of the channel/thread one more time just before drafting. Slack pages can lag a minute; if someone on the team replied while we were thinking, skip.

**3b. Have we already drafted for this exact client message?** Load the state file. Look up the key `<channel_id>:<client_msg_ts>`. If present:

- Compare the current `internal_context_hash` (hash of the last ~20 messages in the matching internal channel since the prior draft) to the stored one.
  - If unchanged → **skip**. Our previous draft is still the best we can produce, and re-drafting would overwrite any edit Nacho made.
  - If changed → context has moved (e.g., team posted an update internally). **Re-draft**, and overwrite the previous state entry.
- If the stored draft was generated >72h ago AND no team member has replied AND no internal context has changed → re-draft anyway with a slightly different opener (e.g., a brief "circling back on this — " / "volviendo a esto — " framing) and a stronger forward-mover. This handles "we drafted a holding response, nothing changed, but the client's still waiting" gracefully.

**3c. Is the client message text a near-duplicate of an even-older still-unanswered ask?** If the same question has been asked twice in the same channel within 7 days with no team reply between them, draft only the most recent one and acknowledge the repeat (e.g., "Sorry for the lag here — coming back to you now on this." / "Perdón por la demora — te respondo ahora.").

**State updates happen after a successful `slack_send_message_draft` call** in Step 6, not before — so a failed draft doesn't poison future runs.

### Step 4 — Gather context (ladder approach)

For each qualifying message, gather context using the ladder below. Climb only as high as you need to — most replies can be drafted from rung 1 or 2.

**First, triage: is this a data question?** Before climbing, decide whether the message asks for a specific number, metric, status, or trend (ACOS, spend, TACOS, margin, inventory/stockout, sales velocity, rank, SQP, BSR, reviews, "how did we do last week?", "¿cómo venimos?"). If yes, you will almost certainly need **Rung 3** — plan to pull the real figure from Shurq (ads + everything, incl. campaign granularity via `query_table`) → Sophie Hub → Helium10 and put it in the draft. Rungs 1–2 still run first (they may show the team already answered, or give you the ASIN/context you need to query), but a data question is not "done" until you've either pulled the number or exhausted the sources.

**Rung 1 — The external channel itself.**

Read the last ~100 messages of the channel via `slack_read_channel` (already fetched in Step 2 for thread detection — reuse). For thread replies, also fetch the full thread via `slack_read_thread`. This usually contains:
- What the client has been talking about
- What Nacho previously promised or said
- Any data points Nacho already shared (ad spend, ACOS, launch dates, ASINs, listing changes)

If the client's question can be answered confidently from this material, **stop here** and draft.

**Rung 2 — The matching `-sophie-internal` channel.**

Derive the internal channel name: replace `-sophie` suffix with `-sophie-internal`. Look it up via `slack_search_channels`. If found, read the last ~50 messages via `slack_read_channel`. This is where the Sophie team discusses each account internally — current campaign status, what's been delivered to the ads platform, what's pending, who is doing what, what's been escalated. Often the answer to a client question is "the team is on it, here's the current status" — and that status lives here.

If you find an internal thread that already addresses the client's question, draft a client-safe paraphrase of the team's conclusion. **Never copy internal Slack text verbatim into a client channel** — internal language is candid, sometimes lists internal names/tools, and is not for clients.

**High-signal shortcut**: if a recent `client-call-summary` recap was posted to the internal channel (look for the structured "Key points from the meeting / Next steps for Sophie / Next steps for [Brand]" format), prefer it as your primary internal-context source — it already distills decisions, owners, and follow-ups from the last call with this client. If the client question maps to a "Next steps for Sophie" item in that recap, the draft should reflect the current status of that commitment.

If rung 2 still doesn't give you what you need, go to rung 3.

**Rung 3 — Real data pull. This is no longer a last resort.**

**Whenever the client's message contains a data question, you pull the real figure from the source of truth and put it in the draft.** A data question is any request for a specific number, metric, status, or trend that Slack context alone can't answer — e.g. "how did we do last week?", "what's our ACOS?", "¿cómo venimos de TACOS?", "are we going to stock out?", "¿cuánto bajó el CPC?", "how's B0XXXX ranking for `<kw>`?", "what's the margin on this SKU?", "¿cuántas reviews tenemos ya?", "did sales pick up after the price change?".

The old behavior (acknowledge and promise to "come back with the number") is now the **fallback**, used only when the pull genuinely fails — not the default. If the client asked for a number and the number is pullable, the draft should already contain it.

#### Source priority — try in this order: **Shurq → Sophie Hub → Helium10**

> **AdLabs retirado (2026-09-12):** ya no se usa AdLabs. La granularidad de ad-campaña que antes salía de
> AdLabs ahora sale del **mismo Shurq** vía `query_table` (`campaigns_daily`, `searchterms_daily`,
> `keywords_daily`) — ver la tabla. El cascade quedó Shurq → Sophie Hub → Helium10.

**Shurq is the agency's primary source of truth.** For every data question, go to the **Shurq** connector ("SHURQ - NEW", `mcp.shurq.com`) first. Shurq is its own MCP connector — its tools are not prefixed like the others, so **discover Shurq's available tools at run time** and pull the metric there. Only if Shurq doesn't expose the metric, returns nothing, or errors do you fall to the next source.

Three connectors are involved; **do not confuse them** — Sophie Hub and Helium10 are DIFFERENT servers:

1. **Shurq** ("SHURQ - NEW", `mcp.shurq.com`) — **primary** for all metrics: sales, profit/margin, ACOS/TACOS, spend, velocity, inventory, **y granularidad de ad-campaña** (campaña/ad-group/keyword/search-term) vía `query_table` sobre `campaigns_daily` / `searchterms_daily` / `keywords_daily` (`account_id` + `mkp_id`, paginable por offset). Discover its tools at run time.
2. **Sophie Hub** (the "Sophie_Hub" connector, `api-hub.sophiesociety.com`) — **second**; the agency's own hub (account financials, subscribe & save, rollups). Its own connector, **separate from Helium10** — discover its tools at run time like Shurq.
3. **Helium10** (`mcp.helium10.com`, `mcp__3ee7e690-...__*`) — **final fallback** for granular Amazon analytics the two above don't carry: per-ASIN P&L, FBA inventory health, sales velocity, organic keyword rank, SQP, BSR, price, buy box, reviews. This one has documented tools (right column below).

**Where each metric naturally lives** (use to decide which source to jump to once Shurq lacks it — the priority order above still governs):

| Client is asking about... | If not in Shurq, go to... | Tools |
| --- | --- | --- |
| ACOS, ad-driven TACOS, spend, ROAS, CPC, impressions/clicks, campaign health, keyword / search-term performance, budget pacing, wasted spend | **Shurq** (`query_table`) | `campaigns_daily` (campaña), `searchterms_daily` (search terms), `keywords_daily` (keywords) — `account_id`+`mkp_id`, paginar por offset |
| Account financials, subscribe & save, account-level rollups | **Sophie Hub** | discover at run time |
| Net P&L, contribution margin, profit, blended TACOS, revenue / units | **Helium10** | `get_account_profit_and_loss_summary` (account) or `get_product_profit_and_loss_summary` (per-ASIN); `_series` variants for a trend line |
| Inventory health, stockout risk, days of cover, restock timing | **Helium10** | `get_fba_inventory_health_status`, `get_inventory_values`, `get_sales_velocity` |
| Sales velocity / run-rate | **Helium10** | `get_sales_velocity` |
| Organic rank vs PPC, keyword rank, top keywords | **Helium10** | `get_keywords_rank_history`, `get_keywords_by_asin`, `get_top_keywords` |
| SQP / search query performance funnel | **Helium10** | `get_search_query_performance` |
| BSR / price history / buy box | **Helium10** | `get_asin_bsr_history`, `get_asin_price_history`, `get_buybox_summary` |
| Reviews / rating / seller feedback | **Helium10** | `get_asin_reviews_history`, `get_seller_feedback` |
| Task / ticket status, "who's working on this" | ClickUp | `mcp__c05021e9-...__clickup_search`, `clickup_get_task`, `clickup_filter_tasks` |
| SOPs, past audits, strategic notes, client changelog | Notion | `mcp__18e6d3e2-...__notion-search`, `notion-fetch` |
| Calendar / meeting context | Calendar | `mcp__c0b89acf-...__list_events`, `get_event` |
| Past meeting recap / decisions made in a call | Read.ai | `mcp__d119e90a-...__list_meetings`, `get_meeting_by_id` — but check the internal channel (Rung 2) for a `client-call-summary` recap first |

**Resolve the account / ASIN once per channel.** Prefer the client config in Supabase `public.clients` (columna `config`) — tiene `shurq_account_id`, `amazon_marketplace`, target ACOS/TACOS y ASINs primarios, así que mapea `[account]-sophie` → cuenta + ASINs determinísticamente. If there's no config for the brand, resolve by slug via each source's own lookup: Shurq's account/brand selector (`list_my_accounts`, match del slug del canal, ej. `aironex-sophie` → `aironex` / `Aironex`); Helium10 `get_my_amazon_seller_accounts` / `list_my_products`.

**Cascade before giving up.** Shurq → Sophie Hub → Helium10, skipping any source that clearly doesn't own the metric (per the table). Only after the metric is unavailable in **all** applicable sources do you draft a holding response for that message.

**Pick the window the client implied, and always name it in the draft.** "last week" → trailing 7 days; "this month" / "cómo venimos" → MTD; "yesterday" → t-1. Default to trailing 7 days if unspecified. State the window in the reply ("en los últimos 7 días", "MTD") so the number is never ambiguous. When the client config carries a target for that metric, compare against it ("ACOS 24% vs tu target de 28%, venimos bien").

**Cost guardrail:** still don't pull for non-data messages (acks, scheduling, opinions, "thanks"). The gate is "does this message ask for a number/metric/status?" — if yes, pull (starting with Shurq); if no, draft from Rung 1/2.

If after all three rungs you still can't draft a confident reply, draft a **holding response** instead — something that acknowledges the message, sets expectations, and asks a clarifying question or buys time. Examples:

> Hey — thanks for flagging, looking into this with the team today. I'll come back to you by EOD your time with a clear answer.

> Buenísimo que lo flagearas — lo estoy mirando con el equipo hoy. Te vuelvo a escribir antes de fin de día con una respuesta concreta.

Holding responses are valid drafts. Don't refuse to draft.

### Step 5 — Draft the reply

Draft a reply that is:

- **In Nacho's voice** for this specific channel (see "Voice & tone" above) — including language (Spanish vs English) and formality level
- **Specific** — reference the client's actual ask, not a generic acknowledgment
- **Grounded in real data** — if the client asked a data question, the draft should carry the number you pulled in Rung 3, with its time window named. Don't hedge a number you actually have.
- **Forward-moving** — propose a concrete next step or a clarifying question, don't leave the conversation open-ended
- **The right length** — match the length Nacho typically uses in that channel. For a quick yes/no, one line. For a strategy question, 2–4 short paragraphs max.

**Never invent a number — but do use the ones you pulled.** These are different things:
- If you pulled a metric from Shurq or Sophie Hub this run (Rung 3), state it directly with its time window. That is reporting, not inventing — it's the whole point of the data pull.
- If the data call failed, or you never ran it, **never fabricate** a specific ACOS / spend / revenue / margin / inventory / BSR / rank / review figure, launch date, contract term, price, or deliverable timeline. Hedge instead: "let me confirm the exact number and come back to you" / "te confirmo el número exacto y te vuelvo a escribir" — never a made-up figure.
- **Never surface internal tool names** ("AdLabs", "Sophie Hub", "Shurq", "Sophie scorecard") to a client who doesn't already use them. Report the number, not where it came from.

**Internal-context translation**: when the internal channel has the answer, translate it into client-friendly language. Strip out internal tool names ("AdLabs", "Shurq", "Sophie scorecard", "P0 ticket") unless the client already uses them. Strip team member names. Strip any candid internal commentary ("this client is being unreasonable about X" → never surfaces in the draft, obviously).

**Language detection**: write the draft in whatever language the client is using. Look at the most recent 5 client messages in the channel — if 3+ are Spanish, draft in Spanish. If mixed, mirror the most recent client message's language. If unsure, mirror Nacho's most recent message in that channel. If still unsure, English.

**Multi-question handling**: if the client asked several distinct questions, address each — but consolidate. Don't write five separate paragraphs; group related points and use a short bulleted list if it genuinely helps readability.

#### Step 5a — Reference the client's ask when there's lag

If the client message is >24h old (e.g., we missed it on prior runs, or it's an old thread with a fresh client reply), open the draft with a brief acknowledgment of the lag, not just an answer. Examples: `"Sorry for the delay on this — "` / `"Perdón por la demora — "` / `"Volviendo a este tema — "` / `"Coming back to this — "`. This signals to the client that they weren't ignored.

#### Step 5b — Urgency signals

Detect and mark these in the captured message metadata:

- `@channel`, `@here`, or direct `@Nacho` mention
- Words/phrases (EN): `urgent`, `ASAP`, `today`, `EOD`, `still waiting`, `bumping this`, `friendly bump`, `following up`
- Words/phrases (ES): `urgente`, `por favor responde`, `alguna novedad`, `seguís ahí`, `bumpeando`, `te re-pingo`, `lo más pronto posible`, `cuanto antes`
- Multiple `?` in a single message (3+)
- Message sent during the client's known working hours (use channel TZ if discoverable)

If any urgency signal is present, prefix the channel in the status DM with `:rotating_light:` and surface those drafts at the top of the per-channel bullet list.

#### Step 5c — Attachment handling

If the client uploaded a file:
- **Image (PNG/JPG/GIF, screenshot, etc.)**: read it via `slack_read_file` and incorporate what it shows into the draft (e.g., "Looking at the screenshot — that's the SP keyword targeting tab; the issue is X.").
- **PDF**: read it if possible and reference its content.
- **CSV / XLSX**: don't try to fully parse in this skill. Acknowledge receipt and propose to dig into it ("Got the file, will dig in and circle back with what I find." / "Recibí el archivo, lo reviso y te vuelvo con lo que encuentre.").
- **Other (video, zip, etc.)**: acknowledge the file by name, propose a next step.

Never reference a file as if it's been read when it hasn't been.

### Step 6 — Stage the draft in Slack

Call `slack_send_message_draft` for each qualifying message.

- `channel_id`: the external channel's id
- `thread_ts`: the thread root timestamp if this is a thread reply (so the draft lands inside the thread). For brand-new top-level conversations, omit `thread_ts` so the draft lands in the channel's main message box.
- `text`: the drafted reply, plain text (not Block Kit). Slack mrkdwn applies — use `*bold*`, `_italic_`, backtick for code, and bullets if needed.

On success, **write to the state file**: `<channel_id>:<client_msg_ts>` → `{last_drafted_at: now, draft_text_hash: sha256(draft_text), internal_context_hash: sha256(internal_messages_joined), channel_name}`.

If the tool returns an error (e.g., no permission to draft on a Connect channel, or the channel is archived), capture the error and surface it in the status DM. Don't let one channel's failure block the rest of the run. Do NOT write to the state file on failure.

**Hard rule**: never call `slack_send_message` on a `*-sophie` channel. Only `slack_send_message_draft`. This skill must never auto-send to a client.

### Step 7 — Status DM

After all drafts are staged, post ONE short status message to the status DM target (`#client-drafts-nacho` if it exists, else Slackbot DM).

Format:

```
:writing_hand: *Client reply drafter — <weekday short-month day, h:MM AM/PM BA>*
Window: last 14h  •  <N> drafts staged across <M> channels  •  <C> channels checked

:rotating_light: *Urgent / bumped*
• *Aironex* — "still waiting on the SP audit?" (<thread|permalink>)

*Today's drafts*
• *Krauterland* — 2 drafts (1 top-level, 1 thread) — <permalink_1> · <permalink_2>
• *Petfino* — 1 draft (top-level) — <permalink>

*Still waiting (re-staged from previous runs)*
• *Liquidspectrum* — return-rate question, drafted 2 days ago, no team reply yet — <permalink>

_No new client messages in 17 other channels._
_<footer with any caveats: tool errors, overflow, channel-fallback note, newly-onboarded channels added silently>_
```

Formatting notes:

- Build the Slack permalink to the client's original message so Nacho can click straight there from the status post: `https://<workspace>.slack.com/archives/<channel_id>/p<ts_without_dot>` — Slack also returns a `permalink` field on most read operations; prefer that when available.
- The "Still waiting" section should only include items where the state file shows a prior draft AND no team reply has happened since. Cap at 5 entries; if more, add `_+ N more pending — see #client-drafts-nacho history_`.
- Newly-discovered channels: do NOT call them out as "NEW!" in the body. Just include them in the channel counts. The first_seen timestamp in the registry is for audit, not for noise.
- If 0 drafts were staged AND no "Still waiting" items exist, post a single line: `:writing_hand: *<time>* — No client messages waiting. <C> channels checked.`
- If something failed mid-run, end with: `:warning: <one-sentence reason>. Will retry next run.`

### Step 8 — Persist state

Write the updated state file and channel registry to disk. Both files are small JSON; keep them tidy:

- **state.json**: prune entries older than 14 days that have had a team reply (we don't need to remember closed threads). Keep entries with no team reply indefinitely — those are the "still waiting" set.
- **channels.json**: append-only for new channels; never delete entries (an archived channel re-opening keeps its first_seen).

If the file system is read-only at the canonical path, fall back to the session working dir and log the fallback in the status DM footer once per run.

## Team member IDs (for "is this person on the Sophie team" check)

Any message authored by one of these IDs (or by a user whose profile email ends in `@sophiesociety.com`) is **not** a client message and should not be drafted for. The email-domain check is the primary signal; the hardcoded IDs are a fallback for cases where the profile email isn't visible.

<!-- BEGIN EDITABLE: TEAM_IDS -->
- Nacho — U084BE9B421
<!-- END EDITABLE: TEAM_IDS -->

When in doubt, default to email-domain check via `slack_read_user_profile`. Any user with a `@sophiesociety.com` email is team, regardless of whether their ID is in the list above.

## Pod context (used when reaching for ads data)

Nacho's pod is pod-66. Team members for internal context: Nacho, Jeremias Steinmann, Facundo Karchenboim. The internal team channel where pod-level discussion happens is `#pod-66-team`. When a client question touches PPC and the matching `-sophie-internal` channel doesn't have the answer, `#pod-66-team` is the next-best source of internal context before climbing to external tools.

## Examples of good drafts

These are aspirational, not templates. Each is short, specific, and forward-moving.

### Example 1 — Client asks for last week's performance

**Client message in `aironex-sophie`:**
> Hey Nacho, can you share the weekly performance recap? Want to look at it before our call.

**Channel context:** Weekly recap is normally shared every Monday; today is Tuesday so they're a day late.
**Internal context (`aironex-sophie-internal`):** Jeremias posted yesterday "weekly recap going out tomorrow AM, waiting on Brand Analytics refresh."

**Good draft:**
> Hey! Recap is going out today — Brand Analytics didn't refresh in time yesterday, so we held it to make sure the numbers are clean. I'll have it in here within a couple hours, before the call.

Why this works: acknowledges the ask, owns the delay without over-explaining, sets a concrete time, doesn't drag the BA tool into a client-facing message.

### Example 2 — Thread reply with a clarifying question (Spanish client)

**Client thread in `krauterland-sophie`:** ongoing discussion about a new SKU launch. Client just replied with:
> Una rápida — ¿cuándo está la copy del listing v2?

**Channel context:** Content team confirmed in the internal channel two days ago that v2 is in review with the client's catalog team for German localization.

**Good draft:**
> v2 está en revisión de localización del lado alemán — última update fue hace ~48h. Pingueo al equipo de contenido para chequear el estado y te vuelvo hoy con un ETA concreto.

### Example 3 — Re-staged draft with no new context

**Client message in `liquidspectrum-sophie` (drafted 3 days ago, no team reply yet, no internal context changed):**
> Hey, can you take a look at the spike in returns on ASIN B0XXXXXX last week?

**Good re-draft (using the 72h refresh path from Step 3b):**
> Circling back on this — still pulling review comments + Q&A data for B0XXXXXX. I'll have a root-cause read in here by EOD tomorrow your time. Sorry for the lag.

### Example 4 — Urgent message with @here

**Client message in `petfino-sophie`:**
> @here Hey — Amazon just suppressed the listing for B0YYYYYY. Need help ASAP, this is our top SKU.

**Channel context:** No prior mention. Suppression is a real fire.

**Good draft (urgency signal triggers `:rotating_light:` in status DM):**
> On it now. Pulling the suppression reason from Seller Central and looping in our catalog team — will have a root cause and fix path in here within the hour.

### Example 5 — Holding response (couldn't fully resolve)

**Client message in `liquidspectrum-sophie`:**
> Hey, can you take a look at the spike in returns on ASIN B0XXXXXX last week? Want to understand why.

**Channel context:** No prior mention.
**Internal context:** No prior mention.
**External tools:** Shurq (`query_table` sobre `searchterms_daily`/product data) for that ASIN shows a real return-rate spike from 2.1% → 5.4% in the last 7 days, but no qualitative reason in any tool.

**Good draft:**
> Saw it — return rate on B0XXXXXX went from 2.1% to 5.4% over the last 7 days. Pulling review comments and recent customer Q&A now to see if it's quality, sizing, or a listing-mismatch issue, and looping in our catalog team. I'll come back with a root cause and proposed fix by EOD tomorrow your time.

### Example 6 — Data question, real Sophie Hub pull (Spanish client)

**Client message in `krauterland-sophie`:**
> quick one — ¿cuál es el margen neto del SKU principal este mes?

**Channel context:** nothing recent on margin.
**Internal context:** nothing recent.
**Data pull (Rung 3):** resolved the ASIN from the client config, then pulled from **Shurq first** (primary) → contribution margin 31% MTD, up from 28% last month; the lift is mostly from lower CPC on the exact campaigns.

**Good draft (Spanish, mirroring the client):**
> La contribución neta del SKU principal va en 31% MTD, arriba del 28% del mes pasado — sobre todo por el CPC que bajamos en las exact. Si querés te muestro el desglose por línea de costo en la call.

Why this works: the number is real and pulled this run, the window ("MTD") is named, it's compared to last month, and it never mentions the tool it came from — just reports the figure in Nacho's voice.

### Example 7 — Ad-metric question, Shurq campaign cut (English client)

**Client message in `aironex-sophie`:**
> how's our ACOS trending this week vs target?

**Data pull (Rung 3):** checked **Shurq** for trailing-7-day ACOS (headline 24%); the client also wanted the driver, so pulled the **campaign-level cut from the same Shurq** via `query_table("campaigns_daily", account_id, mkp_id, report_date last 7d)`. Client config target ACOS = 28% (de `public.clients`).

**Good draft:**
> ACOS is at 24% over the last 7 days — under your 28% target, so we've got room. Main driver is the exact campaigns tightening up. Want me to push a bit harder on scaling while we're below target?

## Things this skill never does

- **Never auto-sends** anything to a client channel. Drafts only.
- **Never posts to a `-sophie-internal` channel.** Reads only.
- **Never invents** numbers, dates, names, contract terms, or commitments.
- **Never copies internal Slack text** verbatim into a client draft.
- **Never drafts twice for the same client message** in a single run.
- **Never overwrites an existing draft** when context hasn't changed (state-file dedup).
- **Never replies on Nacho's behalf using `slack_send_message`** — that tool is not used by this skill at all.

## Failure modes & edge cases

- **`slack_send_message_draft` not authorized for a Connect channel**: capture the error, skip that draft, note in status DM. Don't retry; do not write state.
- **Client uploaded a file**: see "Attachment handling" (Step 5c).
- **Client tagged `@channel`, `@here`, or `@Nacho`**: bump priority via Step 5b (visual flag in status DM); behavior is otherwise unchanged — still drafts only.
- **Multiple client messages in the same thread within the window** with no team reply between them: draft once, addressing the latest message and referencing earlier asks if relevant. Don't draft N times in the same thread.
- **Previously drafted, still no team reply, no new context**: state-file dedup keeps the prior draft in place. Do NOT re-stage. Surface in the "Still waiting" section of the status DM.
- **Previously drafted, still no team reply, but internal channel has new activity**: re-draft with the new context. Overwrite the state entry.
- **Previously drafted >72h ago, nothing new**: re-draft once with a "circling back" / "volviendo a esto" framing (Step 3b) and surface in "Still waiting".
- **Long backfill** (came back from PTO, many unanswered messages): cap at 40 drafts total, take the most recent per channel (up to 5), and surface the remainder in a single `_+ N more older messages not drafted — run the skill again to continue_` footer line.
- **Status channel `#client-drafts-nacho` doesn't exist**: post to Slackbot DM and add this footer: `_Tip: create #client-drafts-nacho in Slack so future status posts land there instead of your DMs._`
- **New channel onboarded mid-run**: silently included via the channel registry; no special call-out in the status DM body.
- **Slack channel search returned suspiciously few results**: fall back to the cached registry and flag in the status DM footer.
- **State file unreadable / corrupted**: rebuild from empty. Don't error out. Log in the status DM footer once.
- **Tool/API outage** (Slack down, Shurq unreachable): degrade gracefully. Slack down → can't do anything, fail loudly via Slackbot DM if possible. Shurq down for a single message → intentá Sophie Hub/Helium10 (per the cascade); si todo falla, holding-response draft for that message.

## When this skill triggers vs. doesn't

**Trigger when Nacho says:**
- "draft my client replies"
- "draftea mis respuestas a clientes"
- "draft replies in client channels"
- "revisá los canales de clientes"
- "run the client drafter"
- "check my client channels"
- "qué clientes me están esperando"
- "what do my clients need from me?"
- "draft answers for clients"
- "any client questions I missed?"
- "draft de respuestas en slack"
- "stage replies in the sophie channels"

**Don't trigger for:**
- Drafting replies in `-sophie-internal` channels → those are internal; use a different workflow or just draft inline
- Posting meeting summaries to internal channels → use `team-meeting-summary` or `client-call-summary`
- Generating a weekly report for a client → use `weekly-report` / `weekly-wins`
- Sending a message Nacho already wrote (no drafting needed) → just call `slack_send_message` directly

## Maintenance

The **Team member IDs** block above (between the BEGIN EDITABLE markers) is the one volatile list. When a new team member joins the pod (or the email-domain check fails for an edge case), edit only the lines inside those markers. Everything else in this file should be stable.

If Nacho asks to change the cadence, the look-back window, the per-channel cap, or the status-DM target, update the Configuration section AND re-sync the cloud Routine by calling `RemoteTrigger` with `action: "update"`, `trigger_id: "trig_01BevLxL3DoATGYf6onDg29x"`, and a body carrying the new `cron_expression` and/or updated prompt. Remember the cron is in **UTC** (BA is UTC-3), so 5x/day BA = `0 1,12,15,18,21 * * *`. The updated SKILL.md must also be deployed into the `Daily Check` cloud environment for the Routine to pick up behavior changes (same manual skill-deploy flow as the other cloud skills).

The state file and channel registry are self-managed. Deleting either is safe — they'll be rebuilt on the next run (at the cost of one cycle of potentially-duplicate drafts for any thread that previously had a stale draft).
