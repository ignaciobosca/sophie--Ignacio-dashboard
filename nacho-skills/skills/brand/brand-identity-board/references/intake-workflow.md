# Brand Kit — Intake & Creation Workflow (v2)

A brand kit is only as good as its inputs. NEVER generate a board from
assumptions. Work through the steps below with the person who runs the brand, in
order, using the listed sources. Only when the inputs are resolved do you
assemble the board (format: `template-spec.md`) and deliver the PDF.

---

## Step 0 — Whose brand is this? (ask first, never assume)

Before anything else — before listing inputs or reading any uploaded file — ask
one plain question:

> **"Are we setting up your own company's brand, or a client's / partner's brand?"**

- **Never assume it is the operator's own employer.** Do not pull in colors,
  fonts, voice, or claims from any company you weren't told to use. (A real
  tester saw the skill quietly drag in an unrelated company's guidelines — this
  question is the fix.)
- Once they name the brand, **scope strictly to that one brand.** Ignore
  guidelines belonging to any other company. Nothing from a default employer
  leaks into a client's kit.
- Ask for the brand's **ASIN** at the same time (the Amazon product number).
  It names the output folder — `/creative-brief/<ASIN>/` — so two brands never
  collide. If they don't have it yet, use a temporary label and fix it later.

## Step 0b — List what helps, then take whatever they have (multi-path bootstrap)

Tell the user up front everything that helps, so they can gather it in one go:
brand name + casing + tagline, ASIN, packaging photos, logo file, an optional
brand book, an optional website link, font files or names, who the product is
for, and any "always say / never say" rules they already know.

Then accept whatever they actually have — you are never blocked:

1. **Brand book / brand guidelines** (best) — if they have a brand book PDF or
   guidelines doc, read colors, fonts, voice and claims straight from it.
2. **Packaging photos** — the primary source for colors and logo when there's
   no brand book.
3. **Logo file** — vector or high-res transparent PNG (see Input 5).
4. **Website link** (optional) — if they give a URL and a live fetch is
   available, you may pull colors/voice cues from it. This needs an internet
   fetch, so it stays optional — never required.
5. **"Brands I like" fallback** — if they have almost nothing, ask for one or
   two brands they admire and why. Use that only to *propose* a starting
   direction they then confirm — never to copy another brand.

---

## Input 1 — Brand name
**How to get it:** ask directly.
- Exact spelling and casing as it should appear in the wordmark
  (lowercase / Titlecase / UPPERCASE).
- Any suffix or tagline (e.g. "LONDON", "®").

## Input 2 — Color palette
**How to get it (priority order):**
1. **Product packaging** — photos or print files of the actual packaging.
   This is the primary source of truth for brand colors.
2. **Live listing / product images** — ask for links or screenshots of the
   current listing or the actual product.
3. **Owner's explanation** — any verbal description of the colors they use
   or want.

**What to produce from it:** extract dominant colors, then normalize into the
5-slot structure (lightest neutral → accents/mids → dark → near-black anchor),
uppercase hex. **Render the palette and show the owner the picture before
asking them to lock it** — render the swatches (each color circle with its name
+ hex), or render the draft board, which already shows the swatches together
with the font specimens, and show that image. Never ask them to confirm colors
from a list of hex codes alone. Only after they've seen the rendered swatches
do you lock the palette. (See "Show before you lock" in the Output section.)

## Input 3 — Product purpose & audience
**How to get it:** ask for a short explanation or keywords.
- One or two sentences max: what is the product, what is it for, who uses it.
- This drives the moodboard content and the pattern motifs — the motifs must
  be thematically tied to the purpose (earbuds → soundwaves, hair oil →
  botanical leaves), never generic decoration.
- **Audience:** also capture who the brand is for in one line (e.g. "women
  28-45 with dry hair seeking clean, salon-grade care"). It shapes the voice
  and the moodboard. Draft it from what they tell you and show it back for a
  quick yes before locking. Saved to `brand.audience`.

## Input 4 — Fonts
You need two fonts: a **display** font (for headings) and a **body** font (for
smaller text). There are several ways to give them to me, and you never have to
have everything ready — pick whichever option fits what you have. We'll never
get stuck here: if you can't provide a font, I'll propose one for you.

Offer these options, in this preference order:

1. **Best — share the font file(s).** If you have the actual font file(s) for
   your display and/or body font, upload them. This gives the most accurate
   result, because I use exactly the font you do. If a font comes in a zip,
   I'll check the included license and flag it if it's marked for personal /
   non-commercial use only.

2. **Name it.** If you know the font name(s) but don't have the files, just
   tell me. For free and common fonts (for example, the popular Google Fonts
   families) I can fetch the font automatically from the name. For an unusual
   or custom display font that isn't freely available, I may still need you to
   upload the file.

3. **Always available — I propose a pair and show you specimens to pick from.**
   If you'd rather not do either of the above, I'll suggest two fonts that fit
   your brand's mood — a display font and a body font, both open-source / safe
   to use commercially — and show you the actual specimens (the letters set in
   each font) so you can pick from what you see. This option always works, so
   the board is never blocked waiting on fonts.

**Show before you lock:** whichever option we use, I'll render the specimens —
the "Aa" plus the font name set in the real font — and show you that picture
before asking you to lock the fonts. You're never asked to confirm a font you
haven't seen. (See "Show before you lock" in the Output section.)

**For a logo's distinctive lettering, we use your logo image as the exact
reference rather than trying to match the font.** We do not try to identify or
copy the font in a logo (for example a signature or script wordmark) — instead
we place your logo image itself directly on the board (see Input 5), so the
lettering is always exactly right.

**Why it matters:** whatever fonts we settle on get used in every generated
image that contains text. This is the #1 source of visible inconsistency — a
board where the specimen says one font and the images render another is a
failed board. Two roles needed: SPECIAL (display/headings) and MAIN (body).

## Input 5 — Logo asset
**How to get it (priority order):**
1. **Logo file** — vector (SVG/AI/EPS) or high-res transparent PNG. Ask directly.
2. **Crop from packaging** — if no file exists, a clean straight-on packaging
   photo can be cropped/traced as a temporary asset.
3. **Typographic placeholder** — last resort for drafts only; the board must
   carry a visible PLACEHOLDER tag until the real logo lands.

**If a logo image is supplied, use it directly as a placed image in the header
and the logo variations. Never recreate the wordmark by typesetting it in the
board fonts.** This is what keeps a distinctive logo (for example a signature
or script wordmark) looking exactly like itself, instead of being redrawn in
the wrong font. Only typeset a text wordmark when no logo image exists — that
is the placeholder case.

A board is not final while the logo slot holds a placeholder.

## Input 6 — Voice & tone
**How to get it:** draft it from everything they've already given you (brand
book, packaging copy, how they describe the brand), then show it back for
confirmation. Don't make them fill in a blank form. Capture, into `voice`:

- **adjectives** — 3-5 words for the tone (e.g. "nurturing, grounded,
  confident").
- **sounds_like** — a couple of short example lines the brand *would* say.
- **never_sounds_like** — phrasings the brand would *never* use (e.g. "miracle
  cure!", "beats every other brand").
- **reading_level** — plain target, e.g. "grade 7, short sentences".
- **pov** — point of view, e.g. "we / you".

Draft these, **show them**, then confirm — same "show before you lock" rule as
palette and fonts. They appear on the board's Voice & Tone section.

## Input 7 — Claims (say this / never say this)
**How to get it:** ask what they must always say and what they must never say,
and draft sensible defaults from the category. Capture, into `claims`:

- **required** — claims that should appear (e.g. "Cruelty-free",
  "Cold-pressed argan oil").
- **forbidden** — claims to avoid (e.g. medical/treatment claims, superlatives
  like "best" or "#1", competitor comparisons).
- **disclaimers** — required fine print (e.g. "Results vary. For external use
  only.").

These are plain text fields — no special tools needed. Draft, **show**, then
confirm. They appear on the board's Claims section, with forbidden claims and
disclaimers inside a clearly flagged guardrail box.

---

## Show before you lock (palette + fonts + voice + claims)
**Never ask the owner to lock a palette, fonts, voice or claims they haven't
seen rendered.** The order is always: pull/draft → render a preview → show the
owner the picture → then ask them to lock/confirm.

- **Palette:** render the swatches (each color circle with its name + hex), or
  render the draft board — which already shows the palette swatches and the
  font specimens together — and show that image. Don't ask the owner to confirm
  from a list of hex codes alone.
- **Fonts:** show the actual specimens — the "Aa" plus the font name set in the
  real font — so the choice is visual, not just a list of font names. This
  applies to all three font options above, including the pair I propose.
- **Voice & claims:** draft the adjectives, sounds-like / never-like lines, and
  required / forbidden claims from their inputs, then show them on the rendered
  draft board's Voice & Tone and Claims sections (or as a written draft) before
  asking them to lock.

Only after the owner has seen the rendered swatches, font specimens, and the
drafted voice & claims do you lock them and flip status DRAFT → CONFIRMED.

## Output — assembling the board
With the inputs locked, produce the board per
`template-spec.md`, then auto-render and hand over the PDF (+PNG) into
`/creative-brief/<ASIN>/` — see SKILL.md Phase 5. The moodboard section
specifically:

- Different-sized images composed together (hero / lifestyle / context /
  close-up grid).
- Each image shows the **purpose** of the product — what it's for, in use.
- Style target: **neutral, flat but catchy, well-made.** No clutter, no
  text overlays, no drama for drama's sake — clean commercial photography
  graded to the locked palette.

## Hard rules
1. **Ask whose brand first** — own company vs client/partner — and scope
   strictly to that one brand. Never assume the operator's employer or bleed in
   another company's guidelines.
2. Ask before assuming — every input above comes from the brand owner or
   their materials, not from imagination.
3. Palette is extracted from real product/packaging imagery whenever it
   exists; verbal description is a fallback, not a default.
4. Never ask the owner to lock a palette, fonts, voice or claims they haven't
   seen — render/draft a preview and show it first.
5. If a logo image is supplied, place it directly in the header and variations;
   never recreate the wordmark by typesetting it in the board fonts.
6. The locked font is non-negotiable downstream: all future image
   generations for this brand must render text in it.
7. The finished brand kit (`/creative-brief/<ASIN>/brand-kit.json`) is the
   consistency anchor for every later step. If it isn't confirmed by the owner,
   nothing downstream gets generated.
8. End by auto-delivering the board PDF (+PNG); never leave it behind a request.
