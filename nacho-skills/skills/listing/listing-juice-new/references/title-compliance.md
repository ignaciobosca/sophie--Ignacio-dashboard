# Title compliance and the 75-character title layer

This reference covers Amazon's product-title rules and how this skill applies them. There are two
distinct layers, and they are treated differently:

1. **Hard title rules** (already enforced). Apply to EVERY title the skill proposes, both the
   performance title and the shorter compliant title. These are not optional.
2. **The 75-character target** (announced for 2025, enforced via AI rewrite from July 27). This is
   the OPTIONAL dual-option layer. The skill recommends both a longer performance title and a
   shorter compliant title, presents both, and lets the seller choose.

Sources (reconfirm the live policy page before relying on exact character lists, Amazon edits these):
- Product title requirements and guidelines: https://sellercentral.amazon.com/help/hub/reference/external/GYTR6SYGFA5E3EQC?locale=en-US
- "Updates to improve your product titles begin on July 27": https://sellercentral.amazon.com/seller-forums/discussions/t/145b6d0f-999c-4555-896c-c694bda2e470

> **Marketplace note.** These help URLs point at the US Seller Central (`sellercentral.amazon.com`, `locale=en-US`). Sellers on other marketplaces should open the same pages on their local Seller Central domain and locale instead, for example `sellercentral.amazon.co.uk` (`en_GB`), `sellercentral.amazon.de` (`de_DE`), `sellercentral.amazon.fr` (`fr_FR`). When you know the detected marketplace, cite the matching domain. The hard title rules below (lint) are generic and apply everywhere, but the specific character caps and, crucially, the ~75-character target and the "July 27 auto-rewrite" rollout timing are US announcements and can differ by marketplace, confirm the live policy for the seller's own marketplace before promising exact numbers or dates.

---

## Layer 1 — Hard title rules (apply to BOTH title options, always)

These came in with the January 2025 title update and have been enforced since. A proposed title
that breaks any of these is wrong regardless of length, so check both the performance title and the
compliant title against this list before shipping either.

- **200-character maximum** for most categories (some categories are lower). A title over the cap
  gets truncated. Aim under 80 characters of *critical* content up front so nothing important is
  cut off on mobile.
- **Title case.** Capitalize the first letter of each word except prepositions, conjunctions, and
  articles (a, an, the, and, or, for, of, with, etc.).
- **No ALL-CAPS words.** Do not shout whole words in capitals. Genuine acronyms, unit symbols, and
  size codes are fine (LED, USB, XL, 3XL, SPF, ml). This is a real conflict point: the bullet
  voice-matching rule (SKILL.md Rule 4 / Step 4.0) tells Claude to PRESERVE ALL-CAPS bullet
  headers. That preservation is for bullets only. NEVER carry an ALL-CAPS lead into the title.
- **No word more than twice.** The same word may not appear more than twice in a title.
  Prepositions, articles, and conjunctions are exempt. This caps keyword stuffing, so when title
  budget is tight, push extra keyword coverage into backend search terms instead.
- **Banned characters:** `!  $  ?  _  {  }  ^  ¬  ¦` are not allowed UNLESS they are part of the
  registered brand name.
- **Conditional characters:** `~  #  <  >  *` may appear only to identify a product or a
  measurement (for example "Style #131" or ">3lb"), not as decoration.
- **Recommended word order** when applicable: Brand > Flavor/style > Product type > Key attribute >
  Color > Size or pack count > Model number.

### Lint to run during Step 4 (Claude does this over the proposed title strings)

For each proposed title (performance AND compliant), check: character count vs 200; any whole word
in ALL CAPS that is not an acronym/unit/size code; any word (excluding prepositions/articles/
conjunctions) appearing 3+ times; any banned character not inside the brand name; any conditional
character used outside a product-ID or measurement context. Fix before shipping. Surface any fix in
the HTML evidence text in plain seller language ("removed the exclamation mark, Amazon does not
allow it in titles"). These checks never block the run, they just clean the proposed copy.

---

## Layer 2 — The 75-character title (optional dual-option layer)

This is the new layer added on top of the existing analysis. **It does not replace the existing
title logic.** The performance title (benchmarked against competitors, can run long) is still
produced exactly as before. The 75-character title is an ADDITIONAL recommendation presented
alongside it.

### What changed and why it matters

- Amazon announced a roughly 75-character practical title limit. It was scheduled for 2025 but was
  not actually enforced, so longer titles still work today and often perform well.
- From **July 27**, titles still over ~75 characters get rewritten by Amazon's own AI, gradually.
  In many categories that AI rewrite can go live WITHOUT seller approval.
- Brand-registered owners get roughly a 14-day window in **Review Listings Changes** in Seller
  Central to review or approve Amazon's proposed title before it goes live.
- Net for the seller: keep the longer title and accept that after July 27 Amazon may rewrite it for
  you, or proactively ship a clean ~75-character title you control.

### What the skill produces

For each ASIN, present TWO titles:

1. **Performance title** — the existing rewrite from the normal analysis (competitor-benchmarked,
   COSMO/A9 optimized, can be long). This stays the recommended option for ranking and coverage
   today.
2. **Compliant ~75-character title** — built to survive the July 27 rule untouched, and built to
   use the 75 characters as fully and productively as possible. Lead with the brand by default (the
   brand-in-title check below decides when SQP says otherwise), then give the single most important
   GENERIC (non-branded) keyword the most prominent position and its full
   phrasing. That lead keyword is the term the listing most needs to rank and convert for, pull it
   from SQP bucket 4 (your best converting queries), PPC harvest terms, or the highest-volume
   relevant query. After the lead keyword, add one differentiator and size or variant, then keep
   adding value-bearing terms (a second high-value generic keyword, or a meaningful attribute)
   until you approach 75 characters. Formula: Brand + top generic keyword + differentiator +
   size/variant + (additional high-value terms up to the budget).

Both must pass the Layer 1 hard lint.

### Budget vs quality gate (fill toward 75, but only with value)

Treat 75 characters as a target to fill, not just a ceiling. A 69-character title that could
productively be 74 is leaving prime ranking real estate unused. So push the length up, but gate
every added token on whether it earns its place:

- KEEP adding while each new token increases keyword coverage, shopper clarity, or relevance.
- STOP (and accept a shorter title) when the next token would: repeat a word beyond the twice
  limit, read as filler or a low-value modifier, hurt readability or click-through, or dilute the
  prominence of the lead generic keyword.
- NEVER pad to hit 75. Fuller is better only when fuller is also better. Quality and keyword
  efficiency win over raw length every time.

Record the final character count in `title_compliance_chars` so the seller sees how much of the
budget was used.

### Should the brand be in the ~75-char title? (SQP-driven, default keep)

In a tight 75-character budget every token competes, so the brand name (which earns its place
automatically in a long performance title) is a fair question for the short title. Let the SQP data
answer it, but default to keeping the brand.

How to read brand demand from SQP: find the branded search queries (the query text contains the
brand name, case-insensitive), then look at the purchases and purchase share they drive versus the
ASIN's total tracked purchases.

- **Clear brand demand** (branded queries drive a meaningful share of purchases): keep the brand
  first and prominent. Shoppers look for you by name, do not bury it.
- **Negligible or zero brand demand**: the brand is a candidate to shorten or move later, freeing
  space for the top generic keyword. Treat full brand removal as ADVISORY only, surface it for the
  seller to confirm, never drop it automatically.
- **No SQP file**: always keep the brand first. There is no basis to remove it.

Why default to keeping it (the data cannot see these):

- Brand Registry and many category style guides expect or require the brand at the start of the
  title. Dropping it can itself trigger a compliance flag, and Amazon's July 27 auto-rewrite may
  re-insert the brand, undoing the gain.
- SQP is backward-looking. A new or growing brand legitimately has little branded search yet, but
  hiding the brand slows brand-building, weakens ad attribution, and can cost trust and CTR even on
  generic searches.
- The brand is usually one short token, so the space freed is often marginal against that downside.

When brand demand is negligible and you raise the advisory, show the seller the evidence (branded
query purchase share from SQP) so they can decide. Put the recommendation, keep / de-emphasize /
advisory-drop, in the title-compliance callout text.

### How to present it (HTML)

Render the normal title rewrite block as before, then add the optional title-compliance callout
(only shown when `has_title_compliance` is true on the ASIN). The callout explains, in plain seller
language: this shorter rule was supposed to apply in 2025 and never did, so the longer title above
still works today, but from July 27 Amazon may auto-rewrite anything over ~75 characters without
your approval (you get about 14 days to review in Review Listings Changes), so here is a ready,
compliant short title if you would rather control it yourself.

Seller-friendly framing, no jargon, no em-dashes (SKILL.md Rule 4 applies to this text too).

The fields that drive the callout (set on each ASIN in the report JSON):
`has_title_compliance`, `title_compliance_intro`, `title_compliance_chars`, `title_compliance_value`,
`title_compliance_note`. Omit them and the report renders exactly as it did before this layer
existed.

### How to handle the opt-in xlsx

A flat file holds ONE title per ASIN, so it cannot carry both options. When the seller asks for the
upload-ready xlsx, ask which title variant to write (performance or compliant 75-char). If they do
not specify, default to the performance title and note in the HTML that the compliant short title is
available on request. This is the only place the dual-option layer forces a choice, everything else
is purely additive.
