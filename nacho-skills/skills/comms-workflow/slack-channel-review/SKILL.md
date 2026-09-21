---
name: slack-channel-review
description: >
  Reviews Sophie Society client Slack channels (#brand-name-sophie pattern) to surface
  pending items: unanswered client questions, client messages without a Sophie reply,
  and open commitments/follow-ups mentioned in the conversation.
  Outputs a structured, copy-pasteable summary in chat — ready to load into ClickUp or
  follow up with the client.
  Trigger whenever Nacho says "slack review", "revisá los canales", "qué hay pendiente en Slack",
  "channel review", "qué me falta responder", "open loops en Slack", "revisá los canales de clientes",
  or any combination of "slack" + "pendiente" / "review" / "open loops" / "seguimiento".
  Without a brand name = runs across ALL active clients. With a brand name = runs only for that client.
  Always use this skill when Nacho wants to audit what's pending or unresolved in client Slack channels.
---

# Slack Channel Review Skill

You are auditing Sophie Society's client Slack channels to surface what's pending, unanswered, or unresolved — so Nacho can take action, follow up, or log tasks in ClickUp.

---

## Global Config

```
Nacho's Slack user ID:  U084BE9B421
Channel pattern:        #[brand-name]-sophie  (e.g. #happy-fox-sophie, #masofta-sophie)
Client configs:         Available as project files in context (HappyFox.json, Masofta.json, etc.)
```

---

## STEP 0 — Parse the trigger

Determine scope and time window from Nacho's message:

**Scope:**
- No brand name → run for ALL active clients (`"active": true` in config)
- Brand name present → run only for that client

**Time window:**
- Default: last 7 days
- If Nacho says "últimas 48hs" / "last 48 hours" / "ayer" → use 48h window
- If Nacho says "esta semana" / "this week" → use 7-day window
- If Nacho says "este mes" / "last 2 weeks" → adjust accordingly

Calculate `oldest` timestamp = now minus the window in Unix seconds.

---

## STEP 1 — Discover client channels

For each client in scope:

1. Read the client's config JSON to get:
   - `brand_name`
   - `slack_names` (list of client contacts' Slack display names — may be empty)
   - `slack_internal_channel_id` (fallback if channel search fails)

2. Search for the channel using `slack_search_channels`:
   - Query: `[brand-name] sophie` (e.g. `happy fox sophie`, `masofta sophie`)
   - Filter: `private_channel,public_channel`
   - Match against the `#brand-name-sophie` pattern
   - If not found via search, fall back to `slack_internal_channel_id` from the config

3. Build a channel map:
```
[
  { brand: "Happy Fox",     channel_id: "C0AP7C0G5D1" },
  { brand: "Masofta",       channel_id: "C0B008LAW7J" },
  ...
]
```

Skip clients where no channel is found and note them at the end.

---

## STEP 2 — Read channel messages

For each channel, call `slack_read_channel`:
- `channel_id`: from Step 1
- `oldest`: Unix timestamp for the start of the time window
- `limit`: 100 (max)
- `response_format`: "detailed"

Collect all messages. If the channel returned 100 messages (max), note that the window may be truncated.

---

## STEP 3 — Identify participants

For each message, determine if the sender is **Sophie team** or **client**:

**Sophie team** = any of:
- Nacho: `U084BE9B421`
- Any user whose name does NOT appear in `slack_names` for the client AND is not the client's known contacts

**Client** = any of:
- Users listed in `slack_names` for that client (match on display name or real name)
- If `slack_names` is empty: anyone who is NOT Nacho (`U084BE9B421`) is treated as a potential client contact

> Note: If a channel has many participants and `slack_names` is empty, flag ambiguous senders with ⚠️.

---

## STEP 4 — Detect pending items

Scan messages for three categories:

### Category A — Unanswered client question
A message from a client contact that:
- Contains a `?` OR
- Implies a question or request (e.g. "can you", "could you", "when will", "what about", "do you have", "podés", "cuándo", "qué pasa con")
- AND has **no reply from Sophie** (Nacho or team) as a thread reply OR subsequent message in the channel within the time window

### Category B — Client message without Sophie reply
A message from a client contact that:
- Does NOT have any follow-up message from Sophie (Nacho or team) after it in the channel
- Has been sitting unanswered for **more than 24 hours** (adjustable — use 4h if the window is 48h)

### Category C — Open commitment / follow-up
A message from **anyone** (Sophie or client) that contains explicit commitment language:
- Sophie commitments: "te mando", "te paso", "voy a", "la semana que viene", "próxima semana", "vamos a revisar", "I'll send", "I'll check", "next week", "will follow up", "sending over", "te confirmo", "let me check"
- Client commitments: same patterns from the client side
- Flag if there's no subsequent message closing the loop (e.g., no file sent, no confirmation, no "listo" / "done" after)

---

## STEP 5 — Build pending item objects

For each pending item found:

```
{
  brand: "Happy Fox",
  channel_id: "C0AP7C0G5D1",
  category: "A" | "B" | "C",
  description: "One-line summary of what's pending",
  generated_by: "client" | "sophie",
  sender_name: "Mimi",
  date: "2026-05-04",
  message_ts: "1746400000.000100",
  slack_link: "https://app.slack.com/client/[WORKSPACE_ID]/[CHANNEL_ID]/p[MESSAGE_TS_NO_DOT]",
  confidence: "high" | "low"
}
```

**Confidence rules:**
- `high`: Clear question with no reply, or explicit commitment language
- `low`: Ambiguous message, multi-participant channel with `slack_names` empty, or unclear if commitment was closed

> To build the Slack link: replace the `.` in `message_ts` with nothing and prepend `p`.
> Format: `https://slack.com/archives/[CHANNEL_ID]/p[1746400000000100]`

---

## STEP 6 — Format output

Output in chat only. Structure:

```
📋 Slack Channel Review — [Time window] — [Date]

━━━━━━━━━━━━━━━━━━━━━━━━
🔤 [BRAND NAME]
━━━━━━━━━━━━━━━━━━━━━━━━

[A] ❓ Unanswered question — [Sender] · [Date]
→ [Description]
🔗 [Slack link]

[C] 📌 Open commitment (Sophie) — [Date]
→ [Description]
🔗 [Slack link]

[A] ⚠️ Possible question — [Sender] · [Date]  ← low confidence
→ [Description]
🔗 [Slack link]

━━━━━━━━━━━━━━━━━━━━━━━━
🔤 [NEXT BRAND]
━━━━━━━━━━━━━━━━━━━━━━━━
[items...]
```

**Category icons:**
- `[A]` ❓ = Unanswered client question
- `[B]` 💬 = Client message without Sophie reply
- `[C]` 📌 = Open commitment (add `(Sophie)` or `(Client)` to indicate who owes the action)
- ⚠️ = Low confidence — review manually

**After all brands with pendientes, add a closing block:**

```
━━━━━━━━━━━━━━━━━━━━━━━━
✅ No pending items in the window:
Leefy Organics · Natchiketa · Moomade

⚠️ Channels not found / no access:
[brand names if any]
━━━━━━━━━━━━━━━━━━━━━━━━
Total pending: X items across Y clients
```

**Ordering:** Alphabetical by brand name within the results.

---

## STEP 7 — Edge cases

| Situation | Handling |
|---|---|
| Channel not found via search | Fall back to `slack_internal_channel_id`; if still fails, list in "not found" block |
| `slack_names` empty | Use U084BE9B421 as only known Sophie member; flag all others as potential clients with ⚠️ |
| 100 messages returned (truncated) | Add note: "⚠️ Channel may have more activity — window was truncated at 100 messages" |
| Thread replies | Read threads for messages that appear to be questions — a thread reply from Sophie counts as a response |
| No messages in window | Include brand in the "no activity" block, NOT in "no pending items" block |
| Bot messages | Ignore — skip messages from bots |

---

## OUTPUT PRINCIPLES

- Never invent pending items — only report what's actually in the messages
- Be conservative on Category C (commitments) — only flag explicit language, not vague mentions
- Keep descriptions to one line — enough to understand without clicking the link
- Links are mandatory for every item — they're the whole point
- The output should be copy-pasteable directly to ClickUp as task titles + context
