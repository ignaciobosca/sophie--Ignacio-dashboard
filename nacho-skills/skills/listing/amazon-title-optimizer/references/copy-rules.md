# Copy Rules — Title & Item Highlights

These are the canonical rules for this skill. You (the model) self-check the **hard rules** as you
write — count characters exactly including spaces and revise any candidate that fails. The bundled
`scripts/build_pptx.py` (via `scripts/validate.py`) then re-checks all hard rules deterministically;
a failing option is not shown and triggers a console warning, so it is the final gate. The **writing
guidelines** steer generation. Everything here is self-contained to this skill.

---

## Hard rules (check in-context — a failure forces a revise + recount)

### Character limits (including spaces)
- **Title:** ≤ **75** characters — for all categories **except media** (books, music, video, DVD,
  software). For media ASINs, the validator **flags** the title (the 75-char rule does not apply) and
  the skill skips length enforcement for that ASIN.
- **Item Highlights:** ≤ **125** characters.

### Allowed characters
- Allowed: **letters, numbers, spaces, hyphen `-`, comma `,`, period `.`**
- **Commas and periods are explicitly allowed and encouraged** to separate phrases and keep the copy
  readable (e.g. `Glass Food Storage Containers with Lids, 10 Pack, Meal Prep`). "No special
  characters" means symbols like `! * $ #` — it does **not** mean dropping commas. Use them.
- Disallowed: every other symbol — `! ? * $ # % ^ & ( ) _ + = | / \ < > { } [ ] ~ @ ; : " '` etc.
- **No emojis** of any kind.

### No ALL-CAPS
- Only the first letter of a word may be capitalized (Title Case or sentence case).
- Acronyms that are genuinely part of the product (e.g. "USB", "LED", "BPA") are allowed but should
  be used sparingly; everything else with 2+ consecutive capital letters fails.

### No promotional / unsupported language
Banned tokens (case-insensitive; the validator also catches the restricted list in
`restricted-keywords.md`):

```
free, best, best seller, bestseller, best-selling, top rated, top-rated, #1, number one,
no. 1, guaranteed, guarantee, sale, on sale, discount, deal, cheap, cheapest, affordable,
save, savings, bonus, gift, premium quality (as a claim), 100%, risk-free, money back,
buy now, order now, limited time, hot, hottest, new (as a hype claim), amazing, perfect,
ultimate, world's best, award-winning, eco-friendly (see restricted list), proven
```

> "Free" is explicitly banned — Amazon bots flag it out of context. Promotional superlatives both
> risk suppression and waste title space that should carry indexed keywords.

### Word repetition
- No **non-stop-word** may appear more than **twice** across a single field.
- Stop words exempt from the count: `a, an, and, as, at, by, for, from, in, of, on, or, the, to,
  with, your`.
- Applies per field (title counted separately from item highlights).

### Restricted keywords
- No keyword whose **Listing Copy** cell is restricted for the ASIN's **category** (or the
  **General** bucket, which applies to everything) may appear. See `restricted-keywords.md`.

---

## Writing guidelines (generation — quality, not pass/fail)

- **READABILITY IS NON-NEGOTIABLE — this overrides keyword coverage.** Every Title and every Item
  Highlights must read as natural, grammatical English that a person could say out loud. **Read it
  aloud; if any part doesn't parse, rewrite it.** Better to drop a keyword than ship a fragment.
  - Item Highlights use one of two clean styles: **(a)** comma-separated **self-contained noun
    phrases** (a feature list where each phrase stands alone), or **(b)** short **complete
    sentences**. Never a mash-up where a verb phrase is split by commas into something ambiguous.
  - The failure to avoid: `Moist heat warms tired, dry eyes for sleep, travel, and spa.` — "warms
    tired" reads broken. Fix: `Warming moist heat soothes tired, dry eyes. Great for sleep, travel,
    or the spa.`
  - No keyword stacking, no comma-spliced run-ons, no telegraphic fragments. It must read like copy,
    not a tag list.
- **Title = click + index, not a sales pitch.** Lead with the **product noun + #1 attribute**, in the
  words a shopper would actually search or *say* (voice/Alexa). Make it read naturally — no stuffing.
- **Item Highlights = comparison helper.** Use the 125 chars for **materials and recommended
  use-cases** that help a shopper choose between options. This is also where conversational,
  full-phrase intent language lives for Rufus/Alexa.
- **Title and Item Highlights must COMPLEMENT, not echo each other.** The highlights should *extend*
  coverage with attributes, materials, and use-cases the title doesn't already carry — not restate
  the title's phrases or repeat its use-cases. Don't repeat a multi-word phrase (e.g. "certified new
  zealand") or the same use-cases (e.g. "tea", "baking") in both. The core product noun may appear
  in both; beyond that, every word in the highlights should add *new* search/intent coverage.
  Example of the problem to avoid — Title: "Manuka Honey MGO 50 Certified New Zealand, Pure Honey
  for Tea and Baking" / Highlights: "Certified New Zealand manuka honey, MGO 50 rated. Smooth rich
  taste for tea, coffee, smoothies, toast, and baking." ("certified new zealand", "tea", "baking"
  repeat). Fix: drop the repeats from the highlights and use that space for new terms (raw,
  unpasteurized, resealable jar, gift, immune-support use, etc., where true).
- **Unique keyword coverage over repetition.** Every word should earn its place by adding new search
  coverage or real buyer intent.
  - No **synonym stacking** — e.g. "Organizer Storage Organizer", "Container Bin Container".
  - No **same phrase in different morphological forms** — e.g. "organize / organizer / organizing".
  - No **filler adjectives** that add no search value, unless the adjective is a genuine **intent
    indicator** (e.g. "stackable", "leakproof", "dishwasher safe", "for toddlers").
- **Anchor first.** The strongest performing term (from the analysis) goes near the front of the
  title where indexing weight and mobile truncation matter most.
- **Brand:** only include the brand name in the title if the operator opted in at intake.

---

## Quick examples

Good title (Home & Kitchen, ~70 chars, no brand):
`Glass Food Storage Containers with Lids, Leakproof, 10 Pack, Meal Prep`

Good Item Highlights (~120 chars):
`Borosilicate glass, microwave and dishwasher safe, airtight snap lids. Meal prep, lunch, leftovers, freezer to oven use.`

Bad (fails: "Free", caps, symbol, stacking):
`BEST Glass Containers - FREE Lids! Storage Container Organizer Container 100%`
