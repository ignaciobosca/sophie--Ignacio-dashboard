---
name: brand-identity-board
description: Build a complete brand kit and identity board for a product brand — logo header and variations, font specimens, a 5-color palette, a moodboard photo grid, voice and tone, and required/forbidden claims. It confirms whose brand it is, runs a guided intake, and locks everything into a brand-kit JSON. The board layout is assembled deterministically in HTML/CSS and rendered headlessly, so only the 6 photo/pattern slots are AI-generated; it then auto-delivers a finished board PDF (plus PNG) without being asked. Use whenever the user wants a brand board, brand kit, brand guidelines, brand identity, style board, or moodboard; uploads packaging, a logo, or a font and mentions branding; asks to extract a brand palette from packaging; wants to define brand voice and tone or allowed/forbidden claims; or wants on-brand AI imagery anchored to a brand. Also triggers on "brand identity for [brand]" or regenerating a single slot of an existing board.
---

# Brand Identity Board

Produce a brand identity board in a fixed 7-section format. The core principle:
**the layout is never AI-generated**. Typography, colors, and structure are
assembled as HTML/CSS and rendered headlessly — pixel-identical every run.
Only 6 image slots (4 moodboard photos + 2 patterns) come from an image model,
each from a short prompt derived from a confirmed brand identity file. This is
what makes output consistent across brands and across re-runs.

Pipeline: **whose-brand gate → intake → brand kit JSON (confirmed) → assemble
board → generate 6 assets → QA → swap in → auto-render PDF (+PNG)**.

## Phase 1 — Intake (never skip, never assume)

**Step 0 — Whose brand? (ask before anything else.)** Open with one plain
question: *"Are we setting up your own company's brand, or a client's /
partner's brand?"* Never silently assume the operator's employer, and never
bleed in another company's colors, fonts, voice, or claims (a real bug). Once
they name the brand, scope strictly to it. Ask for the **ASIN** too — it names
the output folder `/creative-brief/<ASIN>/`. Then list what helps and take
whatever they have (multi-path bootstrap: brand book → packaging/logo → optional
website link → "brands I like" fallback). Full detail in
`references/intake-workflow.md` — read it on first use.

Then collect the inputs from the brand owner. Summary:

1. **Brand name** — ask directly; exact casing + any suffix/tagline.
2. **Color palette** — extract from packaging photos (best), live listing
   screenshots, or verbal description (last resort). Normalize to 5 slots:
   lightest neutral → two accent/mid slots → dark → near-black anchor.
   Uppercase hex. **Render the palette and SHOW it before asking to confirm**
   (see "Show before you lock" below) — never confirm colors blind.
3. **Product purpose & audience** — 1-2 sentences on the product, plus one line
   on who it's for (`brand.audience`). Drives moodboard briefs, voice, and
   pattern motifs (motifs must tie to the product: earbuds → soundwaves, shea
   hair mask → shea seeds — never generic decoration).
4. **Fonts** — two roles: SPECIAL (display) and MAIN (body). Offer a tiered,
   never-blocking choice: (1) best — user uploads the actual font file(s);
   (2) name it — free/common fonts (e.g. Google Fonts) can be fetched from the
   name, unusual display fonts may still need the file; (3) always-available —
   I propose an open-source/commercial-safe display + body pair matching the
   brand mood AND show you the specimens to pick from, so the board is never
   blocked. **Render the specimens and SHOW them before asking to confirm**
   (see "Show before you lock") — never confirm fonts blind. For a logo's
   distinctive lettering, we use your logo image as the exact reference rather
   than trying to match the font. Check the license file in any font zip —
   flag non-commercial-only licenses to the user.
5. **Logo asset** — vector/PNG file, or crop from a straight-on packaging
   photo. **If a logo image is supplied, use it directly as a placed image in
   the header and variations. Never recreate the wordmark by typesetting it in
   the board fonts.** Only typeset a text wordmark when no logo image exists:
   then use a typographic stand-in and tag the board "LOGO PLACEHOLDER" — the
   board is not final until the real logo lands.
6. **Voice & tone** — draft from their inputs, don't make them fill a blank
   form: 3-5 tone adjectives, a couple of "sounds like" lines, "never sounds
   like" lines, reading level, and point of view (`voice` object). Show before
   locking. Renders as the board's Voice & Tone section.
7. **Claims** — required claims (say this), forbidden claims (never say —
   medical/treatment, superlatives, competitor comparisons), and required
   disclaimers (`claims` object). Plain text fields, no special tools. Show
   before locking. Renders as the board's Claims section with a flagged
   guardrail box for the forbidden claims and disclaimers.

Also capture `imagery_direction` (lean-in / avoid lines drawn from the real
product photos) — it complements the AI moodboard grid.

Write the answers into the brand kit JSON. The canonical output is
**`/creative-brief/<ASIN>/brand-kit.json`** (one file per brand; optionally also
emit a `BRAND.md` companion). Mark it `"status": "DRAFT"`. On confirmation, flip
the status to `CONFIRMED <date>`. This file is the single source of truth: every
downstream prompt derives from it, and any change request (new motif, new font,
new claim) gets written here first.

### Show before you lock (palette + fonts + voice + claims)

**Never ask the user to lock a palette, fonts, voice or claims they haven't
seen.** Order is always: pull/draft → RENDER or draft a preview → SHOW the user
→ THEN ask them to lock/confirm. Don't ask them to confirm from a list of hex
codes or font names alone; draft the voice & claims and show them on the draft
board before locking.

- **Palette:** render a visual preview of the swatches — each color circle with
  its name + hex underneath. The fastest path is to fill the board template's
  palette section (and font section) and render that draft, which already shows
  the swatches and the font specimens together; show that image. (A standalone
  swatch strip works too.) Read the rendered PNG yourself, then present it.
- **Fonts:** show the actual specimens — the rendered "Aa" plus the font name
  set in the real font via `@font-face` — so the choice is visual, not just a
  list of font names. This applies to all three font options, including the
  pair you propose: render the specimens and let the user pick from what they
  can see.

Only after the user has seen the rendered palette swatches and font specimens
(and the drafted voice & claims) do you ask them to lock/confirm, then flip the
JSON status to `CONFIRMED`.

## Phase 2 — Assemble the board

Copy `assets/board-template.html` into the brand's output folder
(`/creative-brief/<ASIN>/`) and fill the `{{TOKENS}}` from the brand kit JSON.
The 9-section layout contract (now including Voice & Tone and Claims) lives in
`references/template-spec.md` — read it before editing the template structure.
Fill the Voice & Tone and Claims sections from the `voice{}` and `claims{}`
objects; they are pure HTML/CSS text and need no image generation. Key rules:

- Embed real font files via `@font-face` (copy them into the board folder).
- Exact hexes as CSS variables — never approximations.
- **Logo:** if a logo image is supplied, place the actual image file in the
  header (S1) and in both logo-variation slots (S2) via the `{{LOGO_IMAGE}}`
  token. Never recreate the wordmark by typesetting it in the board fonts. Use
  the text-wordmark path only when no logo image exists (placeholder mode).
- Until assets exist, the 6 image slots show their generation briefs as
  tagged placeholders, so the user can review the whole board (typography,
  palette, layout) before spending any generation credits.

**Font gotchas learned the hard way:**
- *Variable fonts* may load at an extreme default instance (e.g. ultra
  compressed). If a specimen renders squished, parse the `fvar` table for
  real axis ranges (axes are often non-standard, e.g. wdth 100–1000 with
  default 358) and pin `font-variation-settings` to the normal-width cut.
  A PowerShell/Python fvar parser is in `references/template-spec.md`.
- *Caps-only display fonts*: drop the lowercase row from the specimen
  rather than showing fake lowercase.

Render with headless Chrome (works on any OS with Chrome/Edge):

```
chrome --headless=new --disable-gpu --hide-scrollbars \
  --window-size=1480,4280 --virtual-time-budget=15000 \
  --screenshot="<out>.png" "file:///<path-to-board.html>"
```

Render the placeholder draft, **look at the PNG yourself** (read it as an
image), fix what's broken, and show the user before generating assets.

## Phase 3 — Generate the 6 assets

Write one short prompt per slot, derived from the brand JSON: the slot brief
+ shared grading line + mood keywords + palette hexes inline. Save them to
`/creative-brief/<ASIN>/higgsfield-prompts.md` so they're reproducible. Append a
global negative to every prompt: *no text, no letters, no logos, no
watermarks, no extra products, no oversaturation* (and *no plastic-looking
skin or hair* for people shots).

If the Higgsfield MCP is connected, generate directly. Model mapping:

| Slot | Model | Aspect |
|---|---|---|
| Hero (product) | `marketing_studio_image` | 2:3 |
| Lifestyle (person) | `soul_2` | 9:16 |
| Context (person/use) | `soul_2` | 1:1 |
| Close-up (macro) | `nano_banana_pro` | 1:1 |
| Pattern A | `nano_banana_pro` | 16:9 |
| Pattern B | `nano_banana_pro` | 21:9 |

Practical notes: preflight with `get_cost: true` once per model; submit all
6 jobs in parallel; poll with `job_display`. For product hero shots, prompt
"label removed" — image models mangle label text; the real label can be
composited later. If no Higgsfield MCP is available, hand the prompts file to
the user to run manually and continue when they drop the images.

## Phase 4 — QA, swap in, render

Download assets to `/creative-brief/<ASIN>/assets/` and **inspect every image
yourself** before assembly. Check: palette present in-frame, brief respected,
no text artifacts, no warped anatomy.

- **Text artifacts** (gibberish banners/labels are common, especially on
  people shots): if the artifact is at an edge, crop it off deterministically
  (System.Drawing / PIL) instead of re-rolling — cheaper and keeps an image
  the user may already like. Re-generate only if the defect is structural. Save
  downloaded assets to `/creative-brief/<ASIN>/assets/`.
- Swap images into the template as `background: url(...) center/cover`,
  remove placeholder briefs/tags for filled slots, keep the logo tag if the
  logo is still a stand-in. For a pattern band, set the section
  `background-image` and DELETE that band's `.corner-caption` (the only
  placeholder element on a pattern band — there is no centered label to remove).
- Re-render, read the PNG, verify, then continue to Phase 5 (auto-PDF) and
  present to the user with: what passed QA, what was fixed and how, what
  remains placeholder.

## Phase 5 — Auto-deliver the PDF (+PNG)

**End by producing the finished file automatically — don't wait to be asked.**
A non-technical user won't know to request a PDF, so the skill renders the board
to **PDF** (the headline deliverable) and **PNG**, and hands them over as the
last step. Offer-not-require: deliver it proactively.

Render both with the headless Chrome that's already available (no extra
install). Drop outputs into `/creative-brief/<ASIN>/`:

```
chrome --headless=new --disable-gpu --no-pdf-header-footer \
  --virtual-time-budget=15000 \
  --print-to-pdf="/creative-brief/<ASIN>/board.pdf" "file:///<abs-path>/board.html"
```

(`msedge` / `chromium` accept the same flags if `chrome` is absent.)

The board's Voice & Tone, Claims, palette, fonts, and logo are all pure HTML/CSS,
so **the PDF is a complete one-pager even before any photo lands.** If the
Higgsfield MCP is absent, still produce the PDF now: the 6 image slots render as
prompt-only placeholders and you also emit `higgsfield-prompts.md` so the user
can generate elsewhere and drop the images back in. The deliverable is never
blocked.

## Editing a single slot later

This is the payoff of the split pipeline — one slot changes, nothing else
moves:

- **Motif/content change** (e.g. "leaves → shea seeds"): import the existing
  asset via `media_import_url`, then generate with the returned `media_id`
  as reference and a prompt of the form *"Edit this pattern: replace X with
  Y in the same style; keep everything else identical: same strokes
  (#HEX), same background (#HEX), same arrangement"*. Update the motif in
  the brand JSON too — it must stay the source of truth.
- **Font/color change**: edit the brand JSON, re-fill tokens, re-render.
  No image regeneration needed unless the palette itself changed.

## Output structure

```
/creative-brief/<ASIN>/
├── brand-kit.json               # source of truth, DRAFT → CONFIRMED
├── BRAND.md                     # optional companion (interop)
├── board.html                   # filled template
├── <fontfile>.ttf               # embedded fonts (if files supplied)
├── higgsfield-prompts.md        # the 6 derived prompts
├── assets/                      # generated images + logo
├── board-vN.png                 # rendered versions (draft, v1, v2…)
└── board.pdf                    # AUTO-delivered final deliverable
```

Keep every rendered version — the user compares them.
