---
name: client-call-summary
description: >
  Generate a Sophie Society client meeting recap from a Read.ai transcript and post it as a
  Slack draft to the client's internal channel. Pulls the most recent Read.ai meeting for the
  named brand, extracts decisions, owners, and follow-ups, and renders a structured summary
  with a warm opener, "Key points from the meeting", "Next steps for Sophie", "Next steps for
  [Brand]", and a warm closer — matching Nacho's executive voice. Trigger whenever Nacho says
  "client call summary for [Brand]", "summary of my call with [Brand]", "summarize the [Brand]
  meeting", "meeting recap for [Brand]", "resumen de la llamada con [Brand]", "armá el resumen
  de [Brand]", "post the recap to [Brand]", or any combination of "meeting / call / llamada /
  reunión / recap / resumen / summary" + a client brand name. Always uses Read.ai as the
  transcript source and posts as a Slack draft (never auto-sends).
---

# Client Call Summary — Read.ai → Slack draft

You generate a client-meeting recap for a Sophie Society brand. Input is a brand name. You pull the latest Read.ai meeting for that brand, parse the transcript, and produce a structured Slack-ready message that goes into the client's internal channel as a **draft** (never auto-sent).

The voice is Nacho's: warm, executive, decision-focused, specific. See `references/leefy_gold_example.md` for the gold-standard example. Read it once before drafting if you haven't seen it this session — it shows the exact register and bullet density to match.

---

## Global config

```
Configs folder (local, Drive-synced):
  C:\Users\Nacho Bosca\Desktop\Claude\Projects\General\sophie-society-clients\

Manifest filename:           _active_clients.json
Read.ai MCP tools:           mcp__d119e90a-..__list_meetings, mcp__d119e90a-..__get_meeting_by_id
Slack draft tool:            slack_send_message_draft   (NEVER slack_send_message)
```

---

## Step 1 — Resolve brand → client config

Read `_active_clients.json`. Find the entry whose `brand_name` matches the requested brand (case-insensitive, normalized — strip spaces and apostrophes). If multiple marketplaces match (e.g. Happy Fox US + CA), ask Nacho which one the meeting was for — meetings are usually a single conversation across marketplaces, so default to the primary entry unless he says otherwise. If zero matches, suggest running `client-onboarding`.

Load the matched config. You need at minimum:
- `brand_name` → used in the "Next steps for [Brand]" header and in the warm opener
- `slack_internal_channel_id` → where the draft is posted
- (optional) `client_contacts` or similar field if present → list of client-side names to recognize as `@-tag` targets in the recap

If the config is missing `slack_internal_channel_id`, stop and tell Nacho — don't guess the channel.

---

## Step 2 — Fetch the latest Read.ai meeting

Call `list_meetings` and find the most recent meeting whose title or participants mention the brand name (or known client contacts from the config). Typical Read.ai titles: "Leefy Organics ↔ Sophie Society", "[Brand] x Sophie sync", a participant's name, etc.

Pick the single most recent match. Show Nacho the meeting you picked — title, date, duration — and ask him to confirm before pulling the transcript. If multiple matches are close in time or ambiguous, list the top 3 and let him choose.

Then call `get_meeting_by_id` to fetch the full transcript.

If Read.ai is empty for that brand (no meetings found), ask Nacho whether he wants to paste the transcript manually instead.

---

## Step 3 — Parse the transcript for content

Read the transcript with intent. You're not transcribing it — you're extracting the **structural beats** the recap will be built from. While reading, build a mental map of:

- **Tone of the meeting** — was it warm? Tense? Recovering from a setback? Celebratory? Routine sync? This drives the opener.
- **Topics discussed** — group adjacent transcript chunks into discrete topics. A topic is anything that got more than ~30 seconds of conversation and resulted in a decision, an owner, or a follow-up.
- **Decisions made** — what was agreed. Don't list things that were debated and left open; flag those separately if Nacho needs them.
- **Owners and deadlines** — who committed to what, by when. Names are recognized from the transcript speaker list and config contacts.
- **Action items** — split into (a) things Sophie will do, (b) things the client will do. This split is essential to the output format.
- **Links and references mentioned** — Drive folders, Calendly links, decks, asset folders, ASINs. The transcript usually mentions them verbally but doesn't include URLs.

If something important is unclear from the transcript (a decision was made but you can't tell who owns it, or two owners were named for the same item), make a note and ask Nacho a focused question before drafting. Don't invent ownership.

---

## Step 4 — Draft the recap

Compose the message in this exact structure. Read `references/leefy_gold_example.md` before drafting if you haven't — it's the calibration target.

```
Hi @[Client first name(s)]

[Warm opener — one paragraph, ~2–3 sentences, meeting-specific. Tone matches the meeting. Reference what actually happened today, not a template. Do not reuse the same phrasing across meetings.]

Please, find attached to this message the presentation that we have gone through during our meeting and the meeting summary:

**Key points from the meeting**

* [Topic name]: [mini-paragraph capturing context, decision, owner tagged with @Name, mechanism/next mechanism, why it matters. 2–5 sentences. Substantive — never a one-liner.]
* [Next topic]: ...
* [Continue for every discrete topic from Step 3. Typically 5–8 bullets. Don't pad and don't merge unrelated topics.]

**Next steps for Sophie**

* [Action item — starts with a verb, Sophie owns it, includes timeline if mentioned.]
* ...

**Next steps for [Brand name from config]**

* [Action item — starts with a verb, client owns it.]
* ...

[Warm closer — one sentence, forward-looking. Vary the phrasing — don't reuse "Looking forward to our next call" every time.]
```

### Voice rules (apply throughout)

- **First person from Nacho.** "I have already reduced active campaigns…", "My number 1 structural recommendation…". Not "Sophie will…" in the body.
- **Direct, decision-focused.** Surface what was decided and why. Avoid hedging ("we discussed possibly considering…").
- **Specific.** Numbers, ASINs, product names, deadlines, dollar amounts — pull them in when they were mentioned. Vague bullets are a failure.
- **@-tags are plain text.** Write `@Hana Arraya` literally. Don't resolve to Slack user IDs (`<@U…>`). Slack will auto-link names that match workspace users; the rest stay as visible mentions.
- **Links surface as inline anchors with obvious placeholders.** When the transcript mentions a Drive folder, Calendly, deck, or asset folder but no URL is in the transcript, write the anchor text (e.g. `CLICK HERE`, `LINK: HERE`, `Calendly link`) immediately followed by a visible placeholder in this exact format: `[[FILL: short description of what URL goes here]]`. Example: `Drop the 30-second Focus video into the creative folder HERE [[FILL: ACME creative folder URL]]`. Double brackets and the `FILL:` prefix make the placeholder impossible to miss when Nacho scans the draft. After drafting, list every placeholder back to Nacho in the Step 5 summary so he can fill them before posting.
- **Closer must vary.** Don't open every recap with "Looking forward to…" — it becomes a tell. Rotate the close based on the meeting's actual energy. Options: forward-looking ("Excited to see Focus go live on the 27th"), reassuring ("We've got a clear path here — I'll keep you posted as the pieces land"), partnership-tone ("Appreciate the trust on the SnS push — let's make it pay off"), short-and-direct ("Talk next month"). Pick the one the meeting earned. Never reuse the same closer two recaps in a row when you can see the prior one.
- **Don't invent.** If the transcript doesn't say it, don't write it. If an owner is unclear, ask before drafting.
- **Bilingual handling.** Default to English even if the meeting was in Spanish — Sophie's client comms are English-first. Translate quotes/decisions into English. Override: if the client config has a field like `client_language: "es"` or Nacho says "el cliente es en castellano" / "draft in Spanish", produce the recap in Spanish, keeping the same structural template (Hi, opener, "Please, find attached…" line in Spanish — "Adjunto encontrarás la presentación y el resumen de la reunión:", "Puntos clave de la reunión", "Próximos pasos para Sophie", "Próximos pasos para [Brand]").

---

## Step 5 — Show Nacho the draft + list placeholders

Before sending to Slack, show the full draft in chat. Below it, list:

1. **Link placeholders** — every `[LINK]` you inserted, with the surrounding context. Nacho fills these.
2. **Open questions** — anything you flagged in Step 3 that you weren't sure about (ambiguous owners, half-decisions). Nacho resolves.
3. **The Slack channel** — name + ID from config, so Nacho confirms it's the right destination.

Ask Nacho: *"¿Lo mando como draft a [channel name] o querés ajustes primero?"*

---

## Step 6 — Post as Slack draft

Once Nacho confirms (and has filled placeholders), call `slack_send_message_draft` with:
- `channel_id` = `slack_internal_channel_id` from the config
- `text` = the full recap

**Never call `slack_send_message`.** A draft sits in Slack waiting for Nacho's manual send — that's the contract. He always wants a final look in Slack's own UI before the client sees it.

After posting, confirm in chat that the draft is live in the channel.

---

## Common failure modes to avoid

- **Template-y opener.** Reusing "Thank you very much for your time today. I think it was a very productive meeting…" verbatim across meetings makes every recap feel identical. Re-anchor on what actually happened.
- **One-liner bullets in Key points.** "Discussed PPC structure." is useless. Every bullet must carry decision + owner + mechanism.
- **Action items in Key points / topics in Next steps.** The two sections do different work. Key points = what we talked about and decided. Next steps = the action list. Don't double-list.
- **Mixed ownership in the wrong section.** Things Sophie owns go under "Next steps for Sophie". Things the client owes go under the client section. A bullet that says "Sophie and the client will both…" is a sign you need to split it.
- **Auto-sending instead of drafting.** Always `slack_send_message_draft`. Never the auto-send variant.
- **Inventing links or names.** If the URL isn't in the transcript, use `[LINK]` and surface it back to Nacho.

---

## References

- `references/leefy_gold_example.md` — gold-standard output with annotations on what makes it good. Read this before drafting if you haven't seen it this session.
