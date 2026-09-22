# listing-writer v2 — Changelog

This is a NEW skill (`listing-writer-v2`), not a replacement. Your existing `listing-writer` is untouched. v2 is a superset: everything v1 did, plus the upgrades that came out of the SmartyFlash renovation chat.

## What carried over unchanged from v1
- 3-tab xlsx output (Listing Copy, Structured Attributes, Image Brief)
- Rufus/COSMO 15-dimension coverage + A9 keyword tiering (relevance x log(volume))
- The 7 critical rules (no invented facts, voice rules, TOS enforcement, negative-review gate, COSMO N/A-with-reason, output checklist, backend de-dup)
- Conversational 9-section intake, Sophie Society xlsx styling, Drive push offer

## What's NEW in v2 (the upgrades observed in chat)

1. **Renovation mode.** v1 explicitly refused live listings ("Do NOT use for an existing live listing"). In the chat the skill was used on a LIVE SmartyFlash listing anyway and adapted cleanly. v2 makes this a first-class mode chosen at Section 1, with the brief+images+current copy as intake inputs.

2. **Seller Central entry walkthrough (Phase D).** v1 ended at the xlsx + Drive push. The chat spent four screens mapping copy into the live form across Product Details, Offer, and Safety & Compliance, in page order. v2 adds Phase D plus `references/seller-central-field-map.md`, including dropdown-only answers (Age Range -> Kid, Theme -> Phonics, Language Type -> Spoken) and the stale-header-cache reminder.

3. **Compliance escalation (Phase E).** v1's "claims to verify" only covered marketing claims. The chat surfaced lithium/dangerous-goods classification, Prop 65, CPC/ASTM toy safety, and PFAS, legal-liability fields. v2 adds Phase E plus `references/compliance-escalation.md`, which routes these to supplier confirmation rather than letting Claude assert them.

4. **Age-range internal-consistency check (Rule 9).** The chat caught the title saying 1-7 while Min/Max Age said 36-120 months, and the small-parts-vs-age conflict. v2 codifies this as a hard rule checked across title, attributes, and safety.

5. **Keyword universe hygiene (Rule 8).** The chat dropped ~63% of the Cerebro export (competitor brands like joycat/leapfrog, foreign-language terms like chinese/korean that contradict an English-only product). v1 only said "drop brand-only terms." v2 makes the heavier filtering explicit and tells the skill to report kept/total.

6. **H10 review-analysis xlsx support.** The chat parsed Helium 10 Review-Analysis exports directly (Positive/Negative Topic Insights, Star Rating Impact, Returns Topics). v2 adds `references/h10-review-analysis-format.md` with a complaint-ranking method (star-rating impact primary, mentions secondary, returns-topics routes to images).

7. **Mid-run input change handling.** The chat seller said "keyword-only" then uploaded reviews; the skill adapted and told them it made the draft sharper. v2 adds this to edge cases.

8. **Missing-scaffolding resilience.** The installed v1 shipped only SKILL.md (no scripts/refs). The chat executed the logic directly in Python. v2 documents this as expected behavior so the skill never blocks on absent scaffolding.

## Honest note on what was NOT a real upgrade
Most of the core method (intake, tiering, COSMO, the gate, the audit) was used exactly as v1 scripts it. The genuine net-new value is operational: renovation mode, the Seller Central walkthrough, and the compliance escalation. Those three are where the chat went beyond the written skill.

## Install
Drop the `listing-writer-v2/` folder into your skills directory alongside `listing-writer/`. They coexist. Trigger v2 with renovation/update phrasing or when a live listing or Seller Central screenshots are involved.

## Title structure update (baked into v2 logic)
v2 encodes Amazon's current title structure: **titles cap at 75 characters** (all categories except media), and a **new Item Highlights field** (125 chars, comma-separated searchable phrases) carries the supporting detail the title used to hold. Over-length titles get auto-rewritten by Amazon's AI, which optimizes for clean rather than ranking, so the skill always produces a compliant 75-char title (brand + product type + top keyword) and routes the displaced secondary terms into Item Highlights. Tiering changed accordingly: Tier 1 -> title, Tier 2 -> Item Highlights, Tier 3 -> bullets, Tier 4 -> description, Tier 5 -> backend. The xlsx Tab 1 now has an Item Highlights row, the Seller Central field map documents the new field, and Rule 3 + Rule 10 enforce the hierarchy. The full keyword ambition is unchanged; only the structure moved.
