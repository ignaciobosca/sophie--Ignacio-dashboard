---
name: aplus-plan-per-banner
description: >-
  Interview an Amazon seller and produce an Amazon A+ PREMIUM content BUILD PLAN in the PER-BANNER
  style — 6 STANDALONE banners, ONE module each (Hero, Transformational, Us-vs-Them, Product
  Detail, Disclaimer/Value, Reviews), each a self-contained image at 1464×600 desktop / 600×450
  mobile, built one banner at a time, uploaded as-is with NO splitting. Every banner prompt states
  the exact Higgsfield settings (Model: GPT Image 2, Quality: Mid, Resolution: 2K, aspect ratio per
  banner). Then EITHER a FAQ module OR a Cross-Promotion table (6 banners + 1 = the 7-module cap).
  Use this for "A+ plan per banner", "standalone A+ banners", "build my A+ banner by banner", "one
  module per banner", or when the seller wants each module as its own standalone image rather than a
  continuous design. The sibling skill "aplus-plan-seamless" designs 3 banners as continuous images
  split into halves. Do NOT use for the Brand Story carousel (brand-story-plan /
  brand-story-plan-higgsfield-studio) or a full listing/A+ content audit.
---

# A+ Plan (per Banner)

Turn a seller's inputs into a Premium A+ page a designer/copywriter can build immediately:
compliance-screened **copy** for every module and a **verbatim image-generation prompt** for each
banner, plus the FAQ and Cross-Promotion modules. Each banner is a **standalone, self-contained
image (no splitting)**, and every prompt carries an explicit **Higgsfield settings** block. We work
**banner by banner**. Output is a short, polished HTML plan (same style as the Brand Story plan)
with a **Notes / Design Guidance** cell on every module.

Two phases: **(1) collect inputs (strict), then (2) build the plan, one banner at a time.**

## Reference files (read as needed)
- `references/aplus-modules.md` — **the formula.** The 3-banner / 6-module structure, FAQ,
  Cross-Promotion, all hard rules, and the self-audit. **Read this first.**
- `references/image-prompt-format.md` — the STEP 1 / STEP 2 banner-prompt skeleton, the 6 icon
  styles, the 30 pt floor, product scale, and "How to use each prompt."
- `references/layout-styles.md` — 100 named layouts for banner composition.
- `references/restricted-keywords.md` — Amazon compliance matrix. Screen ALL copy against it.
- `assets/plan-template.html` — the HTML skeleton for the plan.

---

## Phase 1 — Collect inputs (be strict; get the required set up front)

A+ Premium copy is only as good as the intake. **Be explicit and strict** — ask for everything in
the first message, and don't start planning on a partial set. Several modules (Good Reviews, S&S,
FAQ, Cross-Promotion) depend on **real screenshots**; without them you must flag, never invent.

### Message 1 — ask for ALL required inputs at once
1. **ASIN + store/brand.** You'll pull the listing (data tools, else `amazon.com/dp/<ASIN>`) for the exact product name, category, and features. **Match the brand/product name exactly.**
2. **Product listing** — live URL or screenshot (features + any "claims to verify" gaps).
3. **Raw product photos, several angles — MANDATORY.** These are attached to the banner prompts; the model can't render the product from text alone.
4. **Exact dimensions + weight.**
5. **Brand style kit** — hex colors + fonts. If none, **pause and run the `quick-brand-kit` skill first**, then return. Never guess brand colors.
6. **Target buyer persona** — who it's for, their pain points and aspirations (drives Module 2 and the tone).
7. **Review screenshots** — like-for-like **competitor** review threads and/or the brand's **own** reviews. Needed for the **FAQ** (Module 7) and **Good Reviews** (Module 6). Ask for real screenshots.
8. **Subscribe & Save?** If **yes**, the S&S screenshot with the **exact wording + percentage** (copied verbatim). If **no**, we'll run Good Reviews instead (needs a review screenshot).
9. **Brand promise / values** the seller wants emphasized (for Module 5 if no disclaimer is needed).
10. **Cross-Promotion: 3–6 ASINs** to cross-promote (min 3, max 6) **plus, for each ASIN, its title and key bullet points (or at least the title).** You cannot see other ASINs' listings, so you need the seller to send this product info — without it you can't write the 5 comparison features. (No **images** needed — Seller Central auto-populates each product's image and title from the ASIN.)

Also ask (short) which **Module 4** angle fits: has variants? notable materials/ingredients? a learning curve (how-to)? care instructions? multiple use cases? — pick 1–2.

**Confirm ASIN + exact brand name + category before continuing.** Keep questions concise — clear options, no paragraphs.

---

## Phase 2 — Build the plan, ONE BANNER AT A TIME

Work **banner by banner**: present Banner 1 fully (copy + Notes + both prompts), get a nod, then 2,
3, and so on through 6, then the FAQ or Cross-Promotion. **Each banner is ONE module** — a
standalone, self-contained image, **NO splitting**. Each banner gets **two image prompts, MOBILE
first, then desktop** (same copy, layout re-composed per size). Follow `references/aplus-modules.md`.

**6 banners, one module each:**
1. **Banner 1** — Module 1 **Hero** (name + 8–12 word tagline).
2. **Banner 2** — Module 2 **Transformational**.
3. **Banner 3** — Module 3 **Us vs Them** (pick bullet or prose; justify in Notes).
4. **Banner 4** — Module 4 **Product Detail** (1–2 sub-modules; reason in Notes).
5. **Banner 5** — Module 5 **Disclaimer or Value** (mark which).
6. **Banner 6** — Module 6 **S&S or Good Reviews** (verbatim from screenshots).

> **No split.** Each banner is one self-contained image at **1464 × 600 desktop / 600 × 450 mobile**,
> uploaded **as-is** (do not split — that's the sibling "seamless" skill).

**Module budget — EITHER/OR.** Premium A+ caps at 7 modules. 6 banners = 6 modules, leaving **one**
slot, so present both of these and have the seller **pick one**:
- **Module 7 — FAQ** — 4–6 questions, **each ≤ 50 characters (count them)**, plain 1–3 sentence answers. Text only.
- **Cross-Promotion — Premium Comparison Table** — 3–6 products (just ASINs — Seller Central auto-fills image 200:225 + title), **5 features each**, note the Show reviews/prices/add-to-cart preference.

### Copy rules (enforce while writing)
- Obey every **GLOBAL HARD RULE** in `aplus-modules.md`: no competitor names, **no em-dashes**, no AI phrases, exact brand name, no fabrication, compliance-screened.
- **Screen every line** against `references/restricted-keywords.md` for the category; rewrite flagged terms and note swaps.
- Where a module depends on a screenshot the seller didn't provide, **write the flag, not placeholder copy**.

### Banner image prompts (two per banner: mobile first, then desktop) + Higgsfield settings
For each banner, write both prompts using the skeleton in `references/image-prompt-format.md`:
- Lock the same copy in **STEP 1** (exact headlines/taglines; do not invent text) for both sizes.
- **Mobile prompt:** `[Aspect Ratio]` 4:3, `[Dimensions]` **600 × 450 px**, text **mobile-optimized, nothing below 30 px**.
- **Desktop prompt:** `[Aspect Ratio]` ~2.44:1 (wide band), `[Dimensions]` **1464 × 600 px**.
- Both: `[Resolution]` 2K, `[Colors]` + `[Typography]` from the brand kit (big-typography-led), `[Layout]` from `layout-styles.md`, `[Icons]`, `[Product scale]` (real dimensions). **No split** — each banner is one module uploaded as-is.
- **Add a Higgsfield settings block to every prompt** so the seller knows exactly what to select:
  `Higgsfield: Model = GPT Image 2 · Quality = Mid · Resolution = 2K · Aspect Ratio = 4:3 (mobile) / wide band (desktop)`.
- Attach the seller's product photos when generating (state this).

### Run the A+ self-audit
Before finalizing, run the **self-audit checklist** at the end of `aplus-modules.md` (FAQ char
counts, Module 3/4/5/6 checks, no competitor names, no em-dashes, cross-promo 3–6 + ≥5 features).
Note: for this per-banner skill there is **no split** and **both FAQ + Cross-Promotion** are allowed.

### Assemble the HTML plan
Build from `assets/plan-template.html`. One tight block per module with: a header, the copy, a
**Notes / Design Guidance** callout, and (for banners) the two image prompts in `<pre>` blocks each
with its Higgsfield settings line. Put a **"How to use these prompts"** callout at the top (attach
product photo; paste into Higgsfield with the stated settings; **no split, upload each banner
as-is**). Save the file and tell the user where it is.

---

## Guardrails
- **Strict intake.** Don't plan on a partial set; several modules need real screenshots.
- **Never fabricate** reviews, S&S wording, quotes, disclaimers, specs, or features — trace everything to the seller's inputs; flag gaps instead of inventing.
- **No competitor brand names. No em-dashes. No AI phrases.** Match the brand name exactly.
- **No invented names or recipients** — address the seller as "you"; never "hand this to <name>".
- **Compliance is non-negotiable** — screen all copy against the category rules.
- **Mobile-first banners** — big headline, short support, nothing below 30 pt; attach product photos to every banner prompt.
- **FAQ ≤ 50 chars per question** — count programmatically; rewrite any that exceed.
- **AI face → 18px disclaimer.** If a banner renders a visible human face, add the 18px line "Some performers in this advertisement are AI‑generated and do not depict real people" (bottom edge). Only when a face is visible; skip for product-only/hands-only. See `image-prompt-format.md`.
- **Cross-Promotion needs product info** — get each ASIN's title + bullets (or at least the title) from the seller before writing the comparison features; never invent them.
