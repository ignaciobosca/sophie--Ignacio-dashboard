---
name: inbox-triage
description: Triage Matias's Gmail inbox into a clean Slack digest, with Gmail drafts auto-prepared for urgent and existing-client emails. Categorizes each unread message into Urgent (pinned at top, drafts ready), Existing clients (drafts ready), New contacts, or Recurring contacts using Gmail's `Clients/*` labels as the primary signal and Sent-history as a fallback. Filters out marketing/notification noise. Use this skill whenever Matias asks to "triage my inbox", "check my email", "run my inbox triage", "run the email digest", "summarize my unread email", or any phrasing about cleaning, filtering, prioritizing, or scanning his Gmail inbox. Also runs autonomously via the `inbox-triage` scheduled task at 8am, 1pm, and 5pm America/New_York. Posts ONE Slack message per run to `#matias-inbox-triage` (falls back to Slackbot DM if the channel doesn't exist yet) — never spammy, always one consolidated digest.
---

# Inbox Triage

A focused, low-friction triage of Matias's Gmail inbox. Three checkpoints a day, one Slack message per run, drafts pre-staged in Gmail for the items that need a reply.

## Why this exists

Matias gets a lot of email and most of it is noise (newsletters, transactional alerts, marketing). The cost of missing a real client message buried in that noise is high. The goal of this skill is: **in under 30 seconds, Matias should know exactly what he needs to reply to today, and the drafts should already be waiting in Gmail when he clicks through.**

This is not a spam filter — it doesn't move, archive, or label anything. It only **surfaces and drafts**. Matias retains full control of his inbox.

## Configuration

These values are stable defaults. Don't change them unless Matias asks.

- **Gmail account**: `matias@sophiesociety.com` (whichever account is authenticated on the Gmail tool)
- **Slack target**: `#matias-inbox-triage` — resolve via `slack_search_channels`. If not found, fall back to Slackbot DM (channel_id = `U07HD4089KP`, Matias's user_id) and add a one-line note in the digest footer reminding Matias to create the channel.
- **Schedule**: 8am, 1pm, 5pm Matias's local time / UTC+7 (handled by the `inbox-triage` scheduled task; cron `0 8,13,17 * * *`)
- **Time window**: Since the last digest post (see Step 1)
- **Existing-client signal**: Gmail labels under `Clients/*` (primary) + Sent-history domain match (secondary)
- **Noise label**: `Newsletters & Marketing` — anything tagged with this is dropped
- **Urgent cap**: 5 items per digest

## Workflow

Execute these steps in order. Read each step fully before acting.

### Step 1: Determine the time window

The window is "everything that arrived since the last digest." To compute it:

1. Resolve the Slack target. Try `slack_search_channels` with query `matias-inbox-triage`. If found, capture its `channel_id`. If not, set `channel_id` to `U07HD4089KP` (Matias's DM) and remember to add a setup-reminder line in the footer.
2. Read the most recent message from that channel/DM via `slack_read_channel` with `limit: 1`. Extract the `ts` (Slack message timestamp) of the latest digest post.
3. Set the lower bound to that `ts` converted to a Unix timestamp. If the channel is empty (no prior digest), default to `now - 5 hours`.
4. Cap the lower bound at `now - 24h`. This prevents a 200-item digest after a long weekend or vacation. If the cap is applied, note it in the footer.
5. Set the upper bound to `now`.

### Step 2: Pull the inbox window

Call `search_threads` with query:

```
in:inbox after:<lower_unix> -label:Newsletters_&_Marketing
```

Use `pageSize: 50`. Note: Gmail's label filter syntax requires escaping spaces in label names. Use `Newsletters_&_Marketing` or `"Newsletters & Marketing"` as appropriate (test both if the first returns nothing). If the search returns the page-token field, paginate until done OR until 100 threads have been processed (cap to keep latency reasonable).

For each returned thread, identify the latest *inbound* message — the one not from Matias. If the latest message is outbound (Matias replied last), skip the thread entirely.

### Step 3: Filter out noise

Apply these filters in order. Each sub-step has a specific intent — read the rationale, don't just match patterns.

#### 3a — Marketing/transactional senders

Drop the message if any of these are true:

- The thread is labeled `Newsletters & Marketing` (already filtered in Step 2, but double-check after fetching the full thread).
- Sender domain or local-part matches: `noreply@`, `no-reply@`, `notifications@`, `donotreply@`, `mailer-daemon@`, `*@email.*`, `*@mail.*`, `*@updates.*`, `*@notifications.*`, `*@news.*`, `*@bounce.*`, `*@em.*`.
- The Subject line is a transactional auto-message: starts with `[GitHub]`, `[Stripe Receipt]`, `[Amazon Order]`, `Your receipt from`, `Your order`, `Welcome to`, `Verify your email`, `Action required: Verify`, `Your invoice from`, etc.

**Important exception** — keep `noreply@` / automated alerts when the subject contains: `payment failed`, `chargeback`, `fraud`, `account suspended`, `disabled`, `at risk`, `invoice overdue`, `payment overdue`, `past due`. These are operationally critical even though they come from automated senders (e.g. `noreply@sophiesociety.com` flagging an overdue client invoice).

#### 3b — SaaS digests

Drop messages from `support@` / `team@` / `digest@` of SaaS tools Matias uses transactionally — ClickUp digests, Asana digests, Stripe receipts, Notion notifications, Read AI auto-recaps, calendar invites from booking tools. Use judgment. The signal: would Matias glance at this and immediately recognize it as "I'll deal with this later in the app, not in email"? If yes, drop.

#### 3c — Internal calendar protocol drop

Drop the thread if **both** of these are true:

- Sender is internal (`@sophiesociety.com` domain).
- Subject line starts with one of: `Accepted:`, `Declined:`, `Tentative:`, `Invitation:`, `Updated invitation:`, `Canceled:`, `Updated:` (when the rest of the subject looks like a calendar event).

Rationale: internal calendar acceptances/invitations are protocol traffic — they're already handled by Calendar. Surfacing them as "new email" creates noise. (In a real 12h sample, 8 of 25 threads were internal calendar shuffles.) **Exception**: if the subject contains `urgent` or the thread body has substantive content beyond the standard calendar block, keep it.

#### 3d — Cold outreach detection

Drop the message if **all three** of these are true:

- Sender domain is **not** in `Clients/*` labels and not in any prior Sent-history thread (i.e. zero prior contact).
- Sender's local-part suggests outbound sales: `cs@`, `sales@`, `growth@`, `outreach@`, `partnerships@`, `bd@`, `hello@`, `team@` from a domain that looks like a tool/agency.
- The body or subject contains cold-sales signal phrases: `boost your sales`, `grow your revenue`, `we help [brands/companies/sellers]`, `book a quick call`, `15-minute call`, `free audit`, `free strategy session`, `our clients have seen`, `case study`, `would love to chat`, `quick intro`, `noticed you sell on Amazon`, `noticed your brand`, `improve your rankings`, `scale your`, or similar templated cold-sales phrasing.

Rationale: real inbound brand inquiries usually come from a personal email address with specific, non-templated language about their own brand or situation. Cold-sales emails are templated and benefit-leading. (In the 12h sample, `cs@postpurchasepro.co` was the canonical example.) **When uncertain — especially if the sender mentions Matias or Sophie Society by name in a non-generic way — keep it. Better to surface one cold pitch than miss a real inbound.**

#### Bias

After all four filters: **bias toward keeping.** The cost of one false positive in the digest (an extra line Matias glances at) is far lower than the cost of dropping a real client message. When uncertain, keep.

### Step 4: Categorize each kept message

For each surviving message, determine its bucket using this priority order:

1. **Existing client (label match)** — if the thread has any label starting with `Clients/`, the sender is an existing client. Capture the specific client name (e.g., `Clients/Aironex` → `Aironex`).
2. **Existing client (domain match)** — if no `Clients/*` label, search Sent for any prior thread to the sender's domain that *was* under a `Clients/*` label: query `in:sent label:Clients to:*@<domain> newer_than:18m`. If 1+ result, treat as existing client and use the most common matched client label as the name.
3. **Recurring contact** — no client label match, but Matias has corresponded with this domain/email before. Query: `in:sent to:<email_or_domain> newer_than:12m`. If 1+ result, bucket here.
4. **New contact** — no prior Sent thread.

For free-mail domains (`gmail.com`, `outlook.com`, `yahoo.com`, `hotmail.com`, `icloud.com`, `proton.me`, `gmx.*`, `web.de`), match on the **full email address**, not the domain — otherwise every random Gmail user gets bucketed as "recurring."

Don't run more than ~30 Sent-history queries per digest. If you have more candidates than that, batch by domain (one query per unique domain) and reuse the result across messages from that domain.

### Step 5: Score urgency

Mark a message as **Urgent** if any of these match:

- Sender is an Existing client AND the message body or subject contains: `urgent`, `ASAP`, `today`, `tomorrow`, `EOD`, `by end of day`, `deadline`, `overdue`, `past due`, `blocker`, `blocked`, `down`, `broken`, `not working`, `issue`, `problem`, `wrong`, `error`, `please confirm`, `please review`, `need this`, `waiting on`.
- Sender is an Existing client AND the latest message ends with a question mark, OR contains a direct ask phrasing (`can you`, `could you`, `please send`, `please share`, `let me know`).
- Subject literally contains `URGENT` (any case) regardless of sender.
- Sender is a New contact AND subject suggests a real inbound business inquiry: `intro`, `introduction`, `interested in`, `working with`, `onboard`, `proposal`, `quote`, `engagement`, `enquiry`, `inquiry`, `partnership`. Exclude obvious cold sales: `boost your sales`, `grow your`, `book a call with us`, `we help [companies/brands]`, `discovery call`.
- Sender is a Recurring contact AND the message has any deadline cue from the first bullet.

Cap urgent items at **5 per digest**. If more would qualify, take the 5 most recent and surface a `(+N more urgent items below)` note. Each additional urgent item still appears in its normal bucket — it just doesn't get pinned to the top.

### Step 6: Generate Gmail drafts

Drafts are created for these messages only:

- **Every Urgent item** (regardless of which bucket it came from)
- **Every Existing-client item** (urgent or not)

Do NOT draft replies for New contacts (Matias wants to assess these personally) or non-urgent Recurring contacts.

For each draft-eligible message, call `create_draft` with:

- `to`: the sender's email address (extract from `From` header)
- `subject`: same as the original message subject (Gmail will preserve the `Re:` thread linkage when `replyToMessageId` is set)
- `replyToMessageId`: the `messageId` of the latest inbound message in the thread
- `body`: a short, professional acknowledgment in Matias's voice. **Do NOT fabricate facts, commitments, or specifics.** Only acknowledge receipt and propose a near-term next step. Use this template:

```
Hi <FirstName>,

Thanks for the note — I'll get back to you on <one-line paraphrase of their ask> shortly. <One brief acknowledgment that shows you understood the specific request, e.g. "Looking into the campaign data now and will share findings later today.">

Best,
Matias
```

Adapt the second line to match the message: if it's an internal client question about ads, mention reviewing ads/data; if it's a calendar/scheduling ask, propose a couple of slots in vague terms ("a few times this week"); if it's an introduction, acknowledge the intro warmly. **When in doubt, keep it short and generic — Matias will edit before sending.**

Capture the returned `draftId` so it can be linked from Slack.

### Step 7: Post the digest to Slack

Compose ONE message to the resolved Slack channel using `slack_send_message`. Format:

```
:envelope_with_arrow: *Inbox triage — <weekday short-month day, h:MM AM/PM local>*
Window: <lower_bound short> → now  •  <kept_count> kept · <filtered_count> filtered

:rotating_light: *Urgent (<n>)* — drafts ready
• *<Sender Name>* (<email>) <client tag if applicable>: <one-line summary, ≤90 chars> · <Open thread|gmail_thread_url> · <Draft|gmail_draft_url>
• ...

:large_green_circle: *Existing clients (<n>)* — drafts ready
• *<Sender Name>* (<email>) — <ClientLabel>: <summary> · <Open thread|gmail_thread_url> · <Draft|gmail_draft_url>
• ...

:large_yellow_circle: *New contacts (<n>)*
• *<Sender Name>* (<email>): <summary> · <Open thread|gmail_thread_url>
• ...

:white_circle: *Recurring contacts (<n>)*
• *<Sender Name>* (<email>): <summary> · <Open thread|gmail_thread_url>
• ...

_<footer with caveats: window cap applied, channel-fallback note, anything filtered the user might want to know about>_
```

Formatting notes:

- Use Slack's link syntax: `<https://mail.google.com/mail/u/0/#inbox/<thread_id>|Open thread>` and `<https://mail.google.com/mail/u/0/#drafts/<draft_id>|Draft>`.
- Threads in Gmail are linkable by thread_id. Drafts are linkable by draft_id.
- Keep summaries ≤90 chars. They should describe the *ask*, not the email's full content. Examples: "asking for the April Aironex ads recap", "follow-up on the J&B onboarding contract", "intro to a brand looking for Amazon PPC help".
- If a bucket has 0 items, **omit the entire section** including the header.
- If the entire digest is empty (everything filtered or no new mail), post just one line: `:envelope_with_arrow: *<time>* — Inbox is clear. <kept> new since <lower bound>.`

### Step 8: Capture state, finish

No labels to apply. No emails to mark read. The Slack post itself is the state — its timestamp becomes the lower bound for the next run.

If anything failed mid-run (Gmail auth error, Slack post failed), post a single line to the Slack channel: `:warning: Inbox triage couldn't complete this run — <one-sentence reason>. Will retry next scheduled run.` so Matias knows the gap is real and not "no new mail."

## Tone of summaries

The one-line summaries should sound like Matias talking to himself, not like email subject lines. Examples:

- Bad: "Re: April performance"
- Good: "Aironex asking for April performance review before Friday's call"
- Bad: "Quick question"
- Good: "Krauterland wants a quick clarification on the Q2 ad budget split"
- Bad: "Hi Matias"
- Good: "New brand (Petfino) interested in Sophie Society for their Amazon launch"

## Failure modes & edge cases

- **Slack channel `matias-inbox-triage` doesn't exist**: post to Matias's DM (`U07HD4089KP`) and add this footer line: `_Tip: create #matias-inbox-triage in Slack so future digests land there instead of your DMs._`
- **Gmail tool unauthorized**: post `:warning: Gmail auth needs refresh — couldn't run triage this round.` to the Slack target and stop.
- **Empty inbox window** (no new mail): post the single-line "Inbox is clear" message.
- **Long gap** (cap applied): include `_Window capped at 24h — earlier mail not surveyed this run._` in the footer.
- **More than 100 threads in window**: process the most recent 100 and add `_Window had <N> threads — surveyed the most recent 100. Older items will not appear in future digests; consider running on-demand triage if needed._` in the footer.

## When this skill triggers vs. doesn't

**Trigger this skill when Matias says:**
- "run my inbox triage"
- "check my email" / "scan my inbox"
- "what's important in my inbox right now"
- "triage my unread email"
- "any client emails this morning?"
- "did I miss anything in email?"
- "summarize my new mail"

**Don't trigger this skill for:**
- Searching for a specific email he remembers ("find that email from Aironex about ads") → use Gmail search directly
- Drafting a one-off email that isn't a reply to something in the inbox → use `create_draft` directly
- Anything related to Slack triage, ClickUp triage, or non-Gmail inboxes
