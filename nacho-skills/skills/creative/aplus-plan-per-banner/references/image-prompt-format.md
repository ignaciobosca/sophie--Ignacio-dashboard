# Image-Generation Prompt Format

Every card and every background in the plan ships with an image-generation prompt built to
this exact shape. The two-step structure keeps the *copy* locked (Step 1) and the *design*
controlled (Step 2), so the generator never invents marketing text and never drifts off-brand.

> This file defines the **prompt skeleton**. Best-practice guidance for *how* to write great
> generation prompts (lighting, realism, negative prompts, etc.) is layered in separately —
> see the end of this file for the placeholder we'll expand next.

---

## How to use each prompt (ALWAYS include this in the plan output)

A prompt on its own does **not** know what the product looks like. Testing confirms it:
- **Prompt only (no image):** misses/invents the product — don't do this.
- **Prompt + main product image:** good, clean result.
- **Prompt + several raw product photos (angles):** most accurate scale and detail — best for the banners.

So every banner prompt the plan hands to the seller must be paired with usage instructions. Put a
short **"How to use these prompts"** callout at the top of the plan, and repeat the reminder on
each banner:

1. **Always attach the product photo(s)** with the prompt — the main listing image at minimum; add raw angle shots. The prompt fills text + design; the *image* supplies the actual product.
   - **Product accuracy is the #1 failure mode.** The model tends to get the product's **size, proportions, and how it's used** wrong. To fight this: (a) attach **2–4 references** including at least one **in-use/in-hand** photo so scale and grip are unmistakable; (b) in STEP 2 write a one-line **usage description** (how it's held and what it does, e.g. "held upright like a hand saw and drawn down through a loaf"); (c) tell the model to **match the reference exactly — do not resize, restyle, or reshape the product**; (d) keep the `[Product scale]` line concrete (real dimensions + a same-frame size anchor like a hand or the loaf).
2. **Where to paste it — Higgsfield with these exact settings** (state them in every prompt):
   **Model = GPT Image 2 · Quality = Mid · Resolution = 2K · Aspect Ratio = 2:3 (mobile) / ~5:4 (desktop)**. (ChatGPT / GPT Image or Google Nano Banana also work — paste the prompt, attach the product image.)
3. **Generate each banner in both sizes and upload as-is — NO split.** Mobile **600 × 450**, Desktop **1464 × 600**, each a standalone module (6 banners = 6 modules). List the mobile version first.
4. The **FAQ** and **Cross-Promotion** modules have no image to generate — FAQ is text (from reviews), cross-promo pulls each ASIN's own image.

---

## The prompt skeleton (fill every bracket)

```
STEP 1 — Use the text I provide:
- Use the exact headlines as written
- Do not make up any text
[Headline]: "<exact headline from the plan>"
[Body]: "<exact body copy from the plan, or 'none'>"

STEP 2 — Apply the style guide below to create the infographic:

[Aspect Ratio]: <ratio for this card/background — see below>
[Resolution]: Minimum 1K resolution
[Colors]: Primary: <#hex>, Secondary: <#hex>, Background: <#hex>   ← from the brand style guide
[Typography]: <title pt> title / <body pt> body, <title weight> title, <body weight> body ← from the brand style guide, mobile-optimized (see rule below)
[Layout]: <layout name from layout-styles.md that fits this card>
[Icons]: <one of the 6 icon styles below, or 'none'>
[Product scale]: <real product dimensions + a relative-size cue, e.g. "8-inch (20 cm) serrated blade; knife ~13 in overall; fills an adult hand; blade spans the width of a sourdough boule">
[Dimensions]: <exact px, e.g. 1464 × 1200 px>
```

### Product scale rule (always include)
Image models don't know how big your product is, so they guess — and guess wrong (a knife comes
out stubby, a bottle looks travel-sized, the product dwarfs or is dwarfed by the hand). Carry the
**real product dimensions in every prompt** and anchor them to something in frame (a hand, the
bread, a countertop) so proportions read true. Pull the dimensions from the listing / screenshot
/ seller during the interview. If you don't have exact numbers, state the best-known size and say
it's approximate — never leave scale unspecified. This applies to backgrounds and every card that
shows the product.

### Aspect ratio by element (A+ Premium) — each banner in two sizes, MOBILE first
- **Mobile banner** → **4:3** (**600 × 450**), standalone, uploaded as-is (no split). Text must be
  mobile-optimized, **nothing below 30 px**.
- **Desktop banner** → **wide band** (**1464 × 600**), standalone, uploaded as-is (no split).
- One module per banner, 6 banners total. State the exact px and the **Higgsfield settings**
  (GPT Image 2 · Mid · 2K · aspect) in each prompt.

### Two modules need special handling (no generated image)
- **FAQ module** — **text only** (accordion of 4–6 Q&A built from real reviews). No image prompt;
  deliver the Q&A copy, compliance-screened. See `references/aplus-modules.md`.
- **Cross-Promotion module** — uses each ASIN's **own Amazon image automatically**. No image
  prompt; just configure the heading + up to 6 ASINs.

### Mobile-optimized typography rule (always applies)
The prompt must **always** specify text size, and that size must be legible on a phone. Amazon
shoppers are ~80% mobile, and the mobile background crops to 463 px wide, so text that looks fine
on a desktop mockup is unreadable on a phone. **Hard floor: no text below 30 pt anywhere** —
this includes body copy, subheads, and CTAs, not just titles. Concretely:
- **Nothing below 30 pt.** Body / subhead / CTA: **≥ 30 pt**. Titles larger: **≥ 40 pt** (bigger
  still on backgrounds).
- Keep headline ≤ ~6 words so it survives the mobile crop.
- Pull weights (and any larger sizes) from the brand style guide the seller provides; if none is
  given, default to **40 pt bold title / 30 pt normal body** and say so in the prompt. Never go
  below the 30 pt floor even if a style guide suggests smaller.

### Default card style — big-typography-led (the "Quote" pattern) ← use this for MOST cards
The single most mobile-legible layout is the big-typography card: **the headline IS the hero** —
huge, bold, high-contrast (usually white on the brand color), filling a large share of the frame —
with only a short support line and the product as a *secondary* element. On a phone this reads
instantly; dense multi-line paragraphs do not. So **default the majority of cards to this
pattern**, not just the Quote card. Concretely, for a card prompt:
- Make the headline **dominant** — ~60–90 pt equivalent, occupying roughly the top third-to-half
  of the card. Keep it short (≤6 words) and punchy.
- Support/body copy is **short (1–3 short lines), ≥30 pt**, under or beside the headline.
- The **product is a supporting hero** (lower area or one side), not competing with the text.
- High contrast: white type on brand color, or brand-color type on white.
- Favor layouts **#6 Big Typography + Small Product**, **#99 Product in Hand With Large Benefit
  Word**, **#13 Bottom Product / Top Bold Claim**, **#3 Product Half-Off-Canvas**.
- Reserve dense text-panel layouts (#8, #10, #36) for the rare card that truly needs more copy
  (e.g. a longer testimonial or a feature list) — and even then, **lead with a big headline**.

Rewrite copy to fit this: if a card's body runs more than ~3 short lines, cut it or fold the
detail into the headline. Big and few beats small and many.

---

## AI-generated face disclaimer (ONLY when a human face is visible)
If a banner will render a **visible human face**, add a small disclaimer at the **bottom of the
image**, at **~18 px**: **"Some performers in this advertisement are AI‑generated and do not
depict real people"**. This 18 px legal line is the **one exception to the 30 px text floor**.
- Include it **only when a face is actually visible.** Skip it for product-only, hands-only,
  back-of-head, or faceless lifestyle images.
- Add a matching field to the prompt so the generator places it, e.g.:
  `[Disclaimer]: "Some performers in this advertisement are AI‑generated and do not depict real people" — 18px, bottom edge (included because a human face is visible)`
- If a real founder/customer photo is used as the reference (a real person, not generated), the
  disclaimer does not apply — note that in the prompt instead.

---

## The 6 iconography options (offer these; never more)

Give the seller these to choose from, or pick the best fit for the brand and name it in the prompt.

### 1. Linear Outline Icons
Thin or medium stroke, no fill. Best for clean, premium, minimalist designs.
*Example: outline shield, outline leaf, outline water drop.*

### 2. Solid Filled Icons
One-color filled icons, very readable on mobile. Best for bold Amazon images and simple benefit rows.
*Example: solid checkmark, solid heart, solid clock.*

### 3. Icon Inside Circle / Badge
Icon sits inside a circle, rounded square, shield, or badge shape. Best for feature highlights and quick scanning.
*Example: white icon inside colored circle.*

### 4. Cut-Out Icons
The icon is "cut out" from a solid shape, usually a circle or badge. Best for polished, modern ecommerce graphics.
*Example: green circle with a white cut-out leaf inside.*

### 5. Gradient / Duotone Icons
Icons use gradient color or two shades. Best for tech, beauty, wellness, and modern lifestyle products.
*Example: blue-to-purple gradient shield or two-tone water drop.*

### 6. Mini Illustration Icons
More detailed than basic icons, almost like tiny simplified drawings. Best for use cases, lifestyle benefits, or playful brands.
*Example: small garden scene, tiny kitchen counter, tiny dog bowl, small suitcase.*

---

## Worked example (Brand Focus Image — Founder Highlight card)

```
STEP 1 — Use the text I provide:
- Use the exact headlines as written
- Do not make up any text
[Headline]: "<Exact product name from the listing>"
[Tagline]: "<8–12 words, strongest benefit, no filler, no em-dash>"
[Body]: "<2–3 short lines of the transformational pitch to the buyer persona>"

STEP 2 — Apply the style guide below to create the banner (Banner 1: Hero + Transformational):

[Aspect Ratio]: ~5:4
[Resolution]: Minimum 1K resolution
[Colors]: Primary: <#>, Secondary: <#>, Background: <#>   ← from the brand kit
[Typography]: 64 pt headline / 34 pt tagline / 30 pt body, bold headline, normal body (nothing below 30 pt)
[Layout]: Bottom Product / Top Bold Claim (#13 from layout-styles.md)
[Icons]: none (or one of the 6 styles for a feature row)
[Product scale]: <real product dimensions + a relative-size cue>
[Dimensions]: 1464 × 1200 px
```

---

## TO EXPAND NEXT: image-generation best practices

*(Placeholder — the seller will layer in per-module best-practice guidance for photorealism,
lighting, composition fidelity, negative prompts, and per-module reference examples. When that
arrives, add a `references/image-best-practices.md` and point Step 2 of the skeleton at it.)*
