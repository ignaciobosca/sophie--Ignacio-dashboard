# Background Layout Rules (Desktop & Mobile)

The Brand Story background sits **behind the scrolling product cards**, so its composition is
not free-form. These rules are fixed templates — copy them into Step 2 of every background
prompt as **HARD RULES**. What changes per brand is only the *content* (colors, fonts, logo,
background image/pattern, hero product, and the headline/subhead text). The **structure** below
does not change.

Two things are non-negotiable on every background: **where the text goes** and **the CTA button**.

---

## Desktop background — HARD RULES

Canvas: **1464 × 625 px min**, wide (~2.34:1).

- **Content zone (strict — models drift wider, so state it forcefully):** ALL content — logo,
  headline, subhead, hero product, AND the CTA — MUST fit inside the **LEFT one-quarter (25%) or
  narrower**, as a tall narrow column on the far left. The **right 75%+ MUST be completely empty**
  (brand color + faint pattern only); nothing crosses the quarter line. This matters because the
  scrolling product cards overlay everything past the left column — at ⅓ width the content gets
  hidden behind the first card.
- **Text at the top:** logo top-left, headline beneath it, subhead below that — all inside the
  left ¼ column. If the headline is long, **stack it onto multiple short lines** to keep it in the
  column; never let it run wide across the top. No text in the center or right.
- **CTA button pinned to the BOTTOM edge (bottom-left):** a rounded pill button with the **exact
  text `Scroll right to see more →`**. This tells shoppers the strip scrolls — always include it.
- **Hero product** sits in the left region, below the text and above the CTA.

## Mobile background — HARD RULES

Canvas: **463 × 625 px min**, tall (~0.74:1).

- **Text at the top:** logo top-left, headline across the top, subhead directly beneath the
  headline. Reserve the top band for text.
- **CTA at the BOTTOM edge:** a bar/pill spanning the lower edge with the **exact text
  `Scroll right to see more →`**.
- **Hero product centered:** keep all key elements centered — the mobile crop cuts the sides hard.

---

## What is VARIABLE per brand (pull from the style guide / brand inputs)
- Colors (Primary / Secondary / Background)
- Fonts (title & body)
- Logo and its placement
- Background image or pattern
- Hero product shot
- Headline + subhead wording (the CTA text stays fixed)

---

## Prompt block to reuse (fill the VARIABLE lines only)

```
STEP 2 — Build the DESKTOP Brand Story background to this template.

TEMPLATE & HARD RULES (do not deviate — this image sits BEHIND scrolling product cards):
- CONTENT ZONE: ALL text + hero product inside the LEFT one-quarter (vertical 1/4). Right three-quarters stays clean so overlaid cards stay readable.
- TEXT AT TOP: headline top-left, subhead beneath; within the top ~1/10 band or the left 1/4 column. No center/right text.
- CTA BUTTON on the BOTTOM edge (bottom-left): rounded pill, exact text "Scroll right to see more →".
- HERO PRODUCT in the left region, below the text, above the CTA.

VARIABLE PER BRAND:
[Aspect Ratio]: wide ~2.34:1
[Resolution]: Minimum 1K resolution
[Colors]: Primary: <#>, Secondary: <#>, Background: <#>
[Typography]: <headline pt> / <subhead pt> / <CTA pt> — <title font> bold headline, <body font> (mobile-optimized; nothing below 30 pt — subhead & CTA ≥30 pt, headline ≥40 pt)
[Logo]: <logo + placement>
[Background]: <brand pattern/image>
[Hero]: <product shot>
[Dimensions]: 1464 × 625 px min
```

For mobile, swap the HARD RULES block for the mobile rules above and set `[Aspect Ratio]: tall
~0.74:1` and `[Dimensions]: 463 × 625 px min`.
