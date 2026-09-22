# Brand Story: Modules, Cards & Specs

The Amazon Brand Story is a horizontally-scrolling strip that sits inside a product's A+
content. It has **one persistent background** (rendered separately for desktop and mobile)
plus a series of **cards** that scroll left-to-right. The seller fills those cards using
Amazon's native **module types**; the **7 content cards** below are the storytelling angles
we map onto those modules.

---

## The 4 Amazon module types (the native building blocks)

These are the actual slots Amazon gives you. Every card in the plan is realized as one of these.

1. **Brand ASIN & Store Showcase** — a shoppable grid of up to 4 products with a short section
   heading and a "Shop all" link to the Brand Store (e.g. *"Best breeds for kids → Shop all"*).
   Requires the seller's 4 ASINs + a heading.
2. **Brand Focus Image** — one hero image + a heading + a short description. The workhorse card.
   Image spec: **362 × 453 px minimum**.
3. **Brand Logo & Description** — the brand logo/tagline plus an "About Us" paragraph.
4. **Brand Q&A** — a question-and-answer format. Amazon presets the questions (see below).
   This is **ONE module that holds up to 3 question/answer pairs** — never split it into three
   separate modules. The copy budget is **600 / 600 shared across all pairs** (≈600 chars total
   for the questions, ≈600 chars total for the answers), so keep each answer to ~150–200 chars.
   It renders as **text over the brand background** — no separate image is generated for it.

---

## The 7 Brand Story content cards (the storytelling angles)

Map each of these onto the module type that fits it best (noted in parentheses).

1. **Company Story** *(Brand Logo & Description, or Brand Focus Image)* — the origin/mission narrative: how the brand began and what it stands for.
2. **Founder Highlight** *(Brand Focus Image)* — the person behind the brand; a human, credible face.
3. **Product Showcase** *(Brand Focus Image, or Brand ASIN & Store Showcase)* — the hero product(s) and what makes them different.
4. **Individual Value** *(Brand Focus Image)* — one core value or benefit, spotlighted on its own (e.g. craftsmanship, small-batch, tested).
5. **Quote + Powerful Visual** *(Brand Focus Image)* — a short, punchy line (brand promise, review quote, or mantra) paired with strong imagery.
6. **Customer Testimonial & Case Study** *(Brand Focus Image or Brand Q&A)* — social proof: a real result or paraphrased review.
7. **Design-Centered Imagery** *(Brand Focus Image)* — a visually-led card that carries the brand aesthetic with minimal or no copy.

> The video this framework comes from notes that of the 4 module types, sellers get the most
> mileage from **Brand Focus Image** and **Brand Q&A** — they carry the story and the copy.
> Lead with those two unless the brand has a strong reason to feature the ASIN grid.

---

## Backgrounds (always included, separate from the cards)

The background sits behind the whole strip and must be delivered in two crops:

- **Desktop background** — **1464 × 625 px minimum**
- **Mobile background** — **463 × 625 px minimum** (a tall/narrow crop of the same idea)

Backgrounds are **not** free-form: they sit behind the scrolling cards and follow fixed layout
rules — text at the top, a specific content zone, and a mandatory **"Scroll right to see more →"
CTA** on the bottom edge. **Read `references/background-rules.md` and copy those HARD RULES into
every background prompt.** Only the brand content (colors, fonts, logo, pattern, hero, headline)
changes; the structure and the CTA do not.

---

## Brand Q&A preset questions

When a card uses the Brand Q&A module, the question comes from Amazon's preset list. Offer these:

- How did we get our start?
- What makes our products unique?
- Why do we love what we do?
- What problem are we solving?
- **Custom** (the seller writes their own question)

Plan for **one Brand Q&A module with 3 question/answer pairs**, keeping the whole set within
the shared **600 / 600** budget (questions total ≈600, answers total ≈600). Use it to carry the
text-heavy story angles — typically Company Story, Individual Value, and "Why do we love what we
do?" — so the image cards can stay visual.

---

## Spec summary (quick reference)

| Element | Image dimensions (min) | Copy limits |
|---|---|---|
| Desktop background | 1464 × 625 px | Optional: brand name / 3–5 word tagline |
| Mobile background | 463 × 625 px | Optional: brand name / 3–5 word tagline |
| Brand Focus Image card | 362 × 453 px | Heading + short description |
| Brand Q&A (one module) | text over background | 3 Q&A pairs, 600/600 shared total |
| Brand ASIN & Store Showcase | (uses ASIN imagery) | Section heading + "Shop all" |
| Brand Logo & Description | (logo asset) | "About Us" paragraph |

All generated images should be **at least 1K resolution** regardless of the minimums above —
Amazon downscales cleanly but never upscales, so we brief high and let Amazon compress.
