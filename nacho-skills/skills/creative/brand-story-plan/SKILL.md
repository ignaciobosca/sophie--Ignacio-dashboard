---
name: brand-story-plan
description: >-
  Interview an Amazon seller and produce a complete Amazon Brand Story carousel BUILD PLAN —
  copy plus ready-to-run image-generation prompts (with exact dimensions) for a desktop
  background, a mobile background, and the 7 brand story cards (Company Story, Founder
  Highlight, Product Showcase, Individual Value, Quote + Powerful Visual, Customer Testimonial
  & Case Study, Design-Centered Imagery). Use this skill whenever the user wants to create,
  plan, write, or design an Amazon Brand Story, Brand Story carousel, Brand Story A+ module,
  or asks to "plan my brand story", "write brand story copy", "brand story cards", "brand
  story background", or shares brand/founder/product details and wants them turned into an
  Amazon Brand Story. Trigger even if they only say "brand story" in an Amazon/A+ context and
  don't spell out the cards. Do NOT use for a general website "about us" narrative unrelated
  to Amazon, or for full listing/A+ audits (that's a content audit).
---

# Brand Story Plan

Turn a seller's raw brand inputs into a Brand Story carousel they (or a designer) can build
immediately: on-brand **copy** for every element plus a **verbatim image-generation prompt**
carrying the exact dimensions, colors, typography, layout, and icon style. The output is a
short, polished HTML plan.

Work in two phases: **(1) interview**, then **(2) generate the plan**. Don't skip the
interview — the plan is only as good as the brand truth you collect, and Amazon compliance
depends on knowing the product category.

## Reference files (read as needed)
- `references/modules-and-cards.md` — the 4 Amazon module types, the 7 content cards, all
  dimensions, and copy limits. **Read this first** — it defines the structure you're planning.
- `references/image-prompt-format.md` — the exact STEP 1 / STEP 2 prompt skeleton + the 6 icon
  styles. Every card prompt you write follows this.
- `references/background-rules.md` — the fixed layout HARD RULES for the desktop & mobile
  backgrounds (text position, content zone, and the mandatory "Scroll right to see more →" CTA).
  **Use this for every background prompt** instead of the generic skeleton.
- `references/layout-styles.md` — 100 named layouts. Pick one per card for the `[Layout]` field.
- `references/restricted-keywords.md` — Amazon compliance matrix. Screen ALL copy against it.
- `assets/plan-template.html` — the Sophie Society HTML skeleton for the final plan.

---

## Phase 1 — Collect inputs (be strict; get the required set up front)

The output is only as good as the inputs. **Be explicit and strict** — don't proceed on a loose
or partial set, and don't silently skip a required asset. Missing assets (no product photos, no
brand colors) noticeably degrade the result.

### Message 1 — ask for ALL required inputs at once
List these together in your first reply. If the seller omits a required one, ask again before
planning — do not continue without it.

1. **ASIN + store/brand.** You'll pull the listing (data tools, else `amazon.com/dp/<ASIN>`) for title, category, and features.
2. **Product listing** — the live URL or a screenshot (features, A+ content, real review quotes).
3. **Raw product photos, several angles — MANDATORY.** The image model cannot infer the product or its proportions from text alone; these become the reference images the seller attaches to every prompt. Without them, renders miss or invent the product. Do not skip this or accept "generate from description."
4. **Exact product dimensions + weight** — from the listing or the seller. Baked into every prompt for true scale.
5. **Brand style kit** — hex colors + fonts. If they have one, link/attach it. **If they don't, pause and run the `quick-brand-kit` skill first** — it turns their product photos into a brand board with exact HEX codes — then come back with those colors. Never default-guess brand colors.

Optional: a **reference Brand Story** they admire, to imitate its layout.

**Confirm ASIN + brand + category before continuing.**

### Then — only after ASIN/brand are set — ask the story questions
Keep them tight: give the preset question, ask for a **one-line** answer (not an essay). Offer
clear options, no paragraphs. (If they have an "About Us" page, offer to pull the answers from
its URL instead of typing.)

- **Origin** — *How did we get our start?* (1–2 lines)
- **Unique** — *What makes our product unique?* (the #1 difference)
- **Why / problem** — *Why do we love what we do? / What problem are we solving?* (the shopper's feeling)
- **Founder card** — real founder **(+ photo)** or **"the team"** angle?
- **Brand Store grid** — **4 ASINs** to feature (list them) or **skip**?

Use the 3 strongest answers for the single **Brand Q&A module** (600/600 shared, ~150–200 chars each).

---

## Phase 2 — Generate the plan

Produce a plan in this order: **Desktop Background → Mobile Background → one Brand Q&A module
(3 questions) → the visual cards** (Founder Highlight, Product Showcase, Quote + Powerful Visual,
Customer Testimonial, Design-Centered Imagery). The 7 content angles still all appear — Company
Story and Individual Value live inside the single Q&A module (alongside "Why do we love what we
do?"); the rest are Brand Focus Image cards. For each **image** element deliver three things:
**copy**, a **verbatim image prompt**, and **specs** (dimensions, layout, icons). The Q&A module
delivers **copy only** (it's text over the background). Skip the ASIN & Store Showcase card if
the seller has no 4 ASINs.

### Step 1 — Write the copy (compliance-first)
- Draft copy for each element from the interview inputs. Keep the story arc coherent across the
  7 cards — beginning (Company Story / Founder), middle (Product / Value / Quote), proof
  (Testimonial), and feel (Design-Centered Imagery).
- Respect the limits in `modules-and-cards.md`: Brand Focus Image = heading + short description;
  **Brand Q&A = one module, 3 question/answer pairs, 600/600 shared** (≈150–200 chars per
  answer); backgrounds = headline + subhead + the fixed CTA text.
- **Screen every line against `references/restricted-keywords.md`** for the A+ / Infographic
  format columns AND the seller's category column. Rewrite anything flagged and note the swap.
  When unsure, replace the term — a suppressed listing costs far more than a blander line.
- Use the seller's exact wording where they gave you strong lines; don't invent claims,
  testimonials, or results they didn't provide.

### Step 2 — Build the image prompt for each element
**Backgrounds:** build from `references/background-rules.md` — copy its HARD RULES (text at top,
content zone, and the "Scroll right to see more →" CTA on the bottom edge) into the prompt, then
fill only the brand-variable lines. **Brand Q&A:** no image prompt — copy only.

For the **Brand Focus Image cards**, follow the skeleton in `references/image-prompt-format.md`
exactly. Every card prompt must:
- Lock the copy in **STEP 1** ("use the exact headlines as written; do not make up any text")
  with the specific headline/body for that element.
- Fill **STEP 2** with `[Aspect Ratio]`, `[Resolution: min 1K]`, `[Colors]` (from the style
  guide), `[Typography]` (from the style guide, **always mobile-optimized** — hard floor of
  **30 pt for all text**, titles ≥40 pt), `[Layout]` (a named layout from `layout-styles.md`
  that fits the card), `[Icons]` (one of the 6 styles, or none), `[Product scale]` (real
  dimensions + a relative-size cue), and `[Dimensions]`.
- **Always state the text size and keep it mobile-legible** — ~80% of shoppers are on phones and
  the mobile background crops to 463 px wide.

**Default most cards to the big-typography-led pattern** (see the "Default card style" section in
`image-prompt-format.md`): a large dominant headline (~60–90 pt), a short support line, and the
product as a secondary hero — because it's by far the most mobile-legible. Favor layouts #6, #99,
#13, #3. Keep the card copy short so it fits this style. Use a person layout (#42/#57/#61) for the
Founder card, and a denser text-panel layout (#8/#10) only when a card genuinely needs more copy
(e.g. a longer testimonial) — and even then lead with a big headline.

### Dimensions (hard specs)
| Element | Dimensions (min) |
|---|---|
| Desktop background | **1464 × 625 px** |
| Mobile background | **463 × 625 px** |
| Brand Focus Image card | **362 × 453 px** |
Brief all images at **≥1K resolution**; Amazon downscales cleanly but never upscales.

### Step 3 — Assemble the HTML plan
Build from `assets/plan-template.html` (the Sophie Society design system). It should be a **short
build plan, not an audit** — one tight block per element with: a numbered header + module tag,
spec pills, the copy block(s), the image prompt in a `<pre>` verbatim, and a one-line compliance
note. Open the story with 2–3 sentences on the arc. **Add a "How to use these prompts" callout at
the top** (attach the product photo, which tool to paste into — see the "How to use each prompt"
section in `references/image-prompt-format.md`), and repeat the one-line reminder on each card.
Save the file and tell the user where it is.

---

## Guardrails
- **Compliance is non-negotiable.** Never ship copy containing a term flagged for the format or
  category. If a great line must be cut, offer a compliant alternative.
- **Don't fabricate.** No invented founder details, testimonials, awards, or metrics. Ask, or
  leave a clearly-marked placeholder.
- **No invented names or recipients.** Never address the plan to a person the seller didn't name
  (no "hand this to <name>"), and never invent a designer/reviewer/teammate. Write to the seller
  directly as "you"; use only names they actually provided.
- **Never write "Verified buyer" / "verified purchase" / "verified review"** (or similar) as a
  testimonial attribution — Amazon doesn't let brands self-certify reviews and it reads as fake.
  Attribute plainly ("— Home baker") or leave the quote unattributed.
- **Founder Highlight: always add a founder-photo note.** Tell the seller to supply their own
  photo as the AI reference/base image if they want their real likeness shown — a real founder
  builds more trust than a generated face. If no photo is given, render a representative person
  with the face not shown, and say so in the prompt.
- **Mobile-first always.** Every prompt states a mobile-legible text size; keep headlines short.
- **Faithful copy.** The image prompt's STEP 1 must reproduce the plan's copy exactly — the
  generator fills design, never text.
- The detailed **image-generation best practices** (photorealism, lighting, per-module examples)
  are a planned next layer — see the placeholder at the end of `references/image-prompt-format.md`.
