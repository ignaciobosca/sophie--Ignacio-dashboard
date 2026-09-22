# A+ Premium: The Formula (Modules, Rules & Self-Audit)

Amazon **Premium A+ content** is the upgraded A+ tier for brand-registered sellers. This is the
**PER-BANNER** version: build the page as **3 standalone banners + a FAQ module + a Cross-Promotion
table**, one banner at a time, with **no splitting**. Read this file fully before planning.

**Page structure — 6 STANDALONE banners, ONE module each (mobile + desktop, mobile first), plus EITHER a FAQ module OR a Cross-Promotion table:**
- **Banner 1** = Module 1 (Hero)
- **Banner 2** = Module 2 (Transformational)
- **Banner 3** = Module 3 (Us vs Them)
- **Banner 4** = Module 4 (Product Detail)
- **Banner 5** = Module 5 (Disclaimer / Value)
- **Banner 6** = Module 6 (Subscribe & Save / Good Reviews)
- **Then ONE of:** Module 7 **FAQ** (text) **— OR — Cross-Promotion** Premium Comparison Table (3–6 ASINs)

> **Module budget — Premium A+ allows up to 7 modules.** Each standalone banner uploads as **one
> image = one module**, so **6 banners = 6 modules**. That leaves **one** slot, so the seller must
> **choose either the FAQ module OR the Cross-Promotion table, not both.** Present both, mark as either/or.

**Each banner ships in two sizes — same copy, layout re-composed per size. List MOBILE first, then desktop:**
- **Mobile:** **600 × 450 px** (4:3). Text must be mobile-optimized, **nothing below 30 px**.
- **Desktop:** **1464 × 600 px** (wide band).

> **No split.** Each banner is a single self-contained image, uploaded **as-is**. Do NOT split it
> into halves (that is the sibling "seamless" skill). Compose each banner to stand on its own.
>
> **Higgsfield settings — put this line in every banner prompt:** `Model = GPT Image 2 · Quality =
> Mid · Resolution = 2K · Aspect Ratio = 2:3 (mobile) / ~5:4 (desktop)`.

Every module in the plan output carries a **Notes / Design Guidance** cell (format choice,
selection reasoning, "verify with seller" flags, layout direction).

---

## GLOBAL HARD RULES (apply to all copy — self-audit against these)
1. **No competitor brand names** anywhere in A+ copy (Amazon TOS). Compare to "the typical option / the old way," never a named brand.
2. **No em-dashes.** Use periods, commas, or "and". (Also avoid the AI tells: "discover the difference," "elevate," "unlock," "in today's world," "look no further," "whether you're… or…", vague superlatives like "amazing quality.")
3. **Match the brand/product name exactly** as it appears on the live listing.
4. **Never fabricate.** Reviews, S&S wording, disclaimers, specs, and quotes all trace back to the seller's inputs/screenshots. If something's missing, flag it — do not write placeholder or invented copy.
5. **Compliance:** screen every line against `references/restricted-keywords.md` for the product's category (A+ / Infographic columns). Rewrite flagged terms.
6. **Mobile-first typography** on banners: big headline, short support, nothing below 30 pt (see `image-prompt-format.md`).

---

## Banner 1

### Module 1 — A+ Hero
- **Headline:** the product name (match the brand/listing exactly).
- **Tagline:** one punchy line, **8–12 words**, leading with the single strongest benefit. No filler, no vague superlatives. Ask: what makes someone stop scrolling?

### Module 2 — Transformational
- Why does this product exist, and why does this buyer need it? Speak directly to the **target buyer persona** (from intake) in their language — their pain points, their aspirations.
- **2–3 short paragraphs or 4–6 punchy lines.** Not a spec list — an emotional pitch that shows the buyer their life with the product.

---

## Banner 2

### Module 3 — Us vs Them
Compare the product to the generic competitor experience. **Never name a competitor brand.** Pick
the format that fits, and **justify the choice in the Notes cell**:
- **Bullet format** (functional / spec-driven): 3–5 rows, left = "the old way / typical option," right = "our product." Each side ≤ 15 words.
- **Conversational prose** (lifestyle / comfort / emotional): short flowing copy that paints the contrast naturally.
If in doubt, note both options in the Notes cell.

### Module 4 — Product Detail
Choose **ONE or TWO** of these sub-modules (never more than two — keep it focused, not a spec
dump). **State the selection reasoning in the Notes cell.**
- **How to use** — 3–5 numbered steps, plain action verbs (tools, appliances, supplements, skincare).
- **Materials / ingredients** — the 2–3 most meaningful, each with a short benefit note (consumables, textiles, personal care).
- **Care / maintenance** — washing, storage, cleaning; short and practical (textiles, kitchenware, equipment).
- **Variety of uses** — 4–6 use cases as short phrases/icons (multipurpose items).
- **Variations explained** — when/why to choose each variant; reduces returns (any parent/child ASIN set).
- **Size & weight** — dimensions/weight in practical terms ("fits on a standard nightstand" beats "23 cm x 14 cm").
Selection logic: use what the seller provided. Learning curve → "How to use." Variants → "Variations explained." Materials are the differentiator → lead with "Materials / ingredients."

---

## Banner 3

### Module 5 — Disclaimer / Value
- **If the product needs a legal/safety disclaimer** (supplements, baby items, medical devices, cleaning products, anything with allergen or regulatory exposure): write a clean, plain-English disclaimer **under 100 words**. Do NOT invent disclaimers for products that don't need one. Mark the Notes cell: **"DISCLAIMER — verify with seller before publishing."**
- **If no disclaimer is needed:** replace with a **Value / Brand Promise** module — 2–4 sentences reinforcing the brand's core commitment (quality, ethics, sustainability, craftsmanship, whatever the seller emphasized). Mark the Notes cell: **"VALUE MODULE — no disclaimer needed."**

### Module 6 — Subscribe & Save OR Good Reviews
- **If Subscribe & Save applies** (confirmed at intake): copy the S&S messaging **exactly** as it appears on the live-listing screenshot — same wording, same percentage. Do not rewrite or paraphrase. If no screenshot, ask the seller to paste the exact S&S line.
- **If Subscribe & Save does NOT apply:** use a **Good Reviews** module. Pull **2–3 real review quotes** from the seller's screenshots, **verbatim, in quotation marks**, exactly as written. Choose quotes with a strong emotional outcome or a specific benefit — not generic "great product!" lines. Do NOT paraphrase, invent, or composite. If no review screenshot was provided, flag in Notes: **"Seller must provide review screenshot — do not write placeholder copy."**

---

## Module 7 — FAQ
- Write **4–6 FAQs** drawn from the most common questions in competitor review threads and any "claims to verify" gaps in the listing.
- **HARD RULE: every question ≤ 50 characters (including spaces).** Count each one; reject and rewrite any that exceed. Abbreviate, cut filler, rephrase.
  - "Does it come with batteries included?" (42) ✓
  - "What is the exact size and weight of this product?" (51) ✗ → "What are the dimensions and weight?" (35) ✓
- **Answers:** 1–3 sentences, plain and direct, no hype. This is the last thing a buyer reads before deciding.
- FAQ is **text only** (no image to generate).

---

## Cross-Promotion — Premium Comparison Table
The Premium Comparison Table cross-sells the brand's range. **Nothing to render or upload for the
images** — when the seller enters each ASIN in Seller Central, Amazon auto-populates that product's
image (200:225) and title. You only configure structure + copy.
- **Products: minimum 3, maximum 6** (one hero + 2–5 comparison products). Each is just an **ASIN** — image and title fill in automatically.
- Write **5 features per product** as the comparison metrics (the table supports 5–12 metric rows; use at least 5). Metrics are **Checkbox** (✓/✗) or short **Text** values, e.g. Best for, Count, Vegan, Non-GMO, Speed.
- Toggles available: **Show reviews · Show prices · Add-to-cart** (note the seller's preference).
- Ask the seller for the **ASINs to cross-promote (3–6) AND, for each, its title + key bullet points (or at least the title).** You cannot see other ASINs' listings, so the seller must supply this product info — you need it to write the 5 comparison features. Do not invent products or features; if the seller sends only ASINs, ask for the titles/bullets before building the table.

---

## A+ SELF-AUDIT (run before finalizing the plan)
- [ ] **6 standalone banners (one module each, no split)** + **only ONE of FAQ / Cross-Promotion** (6 + 1 = 7 cap).
- [ ] Every banner prompt states the **Higgsfield settings** line (GPT Image 2 · Mid · 2K · aspect per banner) and the module size (1464×600 / 600×450).
- [ ] Every FAQ question **≤ 50 characters** — counted, none exceed.
- [ ] Module 3 **format choice justified** in the Notes cell.
- [ ] Module 4 uses **at most 2 sub-modules**, with selection reasoning noted.
- [ ] Module 5 clearly marked **disclaimer vs value**.
- [ ] Module 6 correctly reflects **S&S availability** from intake (verbatim if S&S; real quotes if reviews).
- [ ] **No competitor brand names** anywhere.
- [ ] **No em-dashes, no AI phrases.**
- [ ] Brand/product name matches the listing exactly.
- [ ] All copy compliance-screened for the category.
- [ ] Cross-Promotion has **3–6 products** and **≥5 features each**.
