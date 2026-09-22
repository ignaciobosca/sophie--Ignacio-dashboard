# Sophie Society Image + A+ Premium SOPs (consolidated)

Single reference file for the `listing-juice` skill. Contains the distilled Sophie Society SOPs for primary images, secondary images, and Premium A+ content. Snapshotted from Sophie Society Notion on 2026-06-22.

**Where this file sits.** `references/sophie-society-image-and-aplus-sops.md` inside the skill folder.

**Refresh cadence.** Re-fetch the source Notion pages and update this file when Sophie signals an SOP change, or on a monthly review. Source pages:
- Main Image Best Practices
- Secondary Images Best Practices
- Premium A+ Content Guide

**Skill rule.** Read this file on every run. Emit the three corresponding HTML blocks per ASIN (main image, secondary image sequence, A+ Premium plan) into the report JSON's `sophie_recommendations_html` field, in that order. (This is a single raw-HTML string containing all three blocks. Do NOT route them through `strict_structured_block`, which the build script overwrites whenever `strict_structured_rows` is present.)

---

## Section 1: Main Image SOP

**One-line summary.** Improving the main image is the highest-leverage single CTR move on a listing. Screen every ASIN against the 15 tactics below and rank the top 3 to 6 by fit.

### The 15 CTR-boosting tactics

1. **Show what's inside.** Tease contents next to the packaging. Gummies next to the box, cards next to the game, cream squeezed next to the tube. Signals "here's what you're actually buying."

2. **Add bright colors.** Boost saturation, add a lively background element, make the frame pop against SERP grid. Especially effective for products in categories dominated by muted or beige competitors.

3. **Add a customer avatar.** Person using the product, subtle placement in a corner or along the edge. Amazon's rules technically frown on this, but many sellers operate in the gray area without issues. The key is subtle integration.

4. **Remove the white space.** Fill the 1500x1500 frame with product, not empty white. Zesty Paws is the reference brand for this pattern.

5. **Add "fake packaging."** Mock a premium wrap or box even if actual product ships plain. Especially valuable for otherwise-plain SKUs (cutting boards, bar soaps, cast-iron cookware).

6. **Add the product title to the packaging.** Highest-search-volume KW bold and centered on the pack. Not the brand, the product-type keyword. Olly's "Beat the Bloat" style. Choose the highest-relevance, highest-search-volume keyword as the on-pack title.

7. **Add color or style variations.** Small color swatch circles or rectangles at the bottom edge showing the variant options. Even when Amazon doesn't auto-render the variant carousel.

8. **Add numbers to packaging.** "25 grams," "100mg," "6 bottles," "3 x 4 oz." Quantitative precision. Especially effective for supplements, food, multi-pack.

9. **Show different angles.** Front-of-product + inset back or side for products with important non-front features. Universal power adapters, tools, or anything with ports/controls on the back.

10. **Kaizen strategy.** Continuous iteration. Ship, measure, refine. Don't treat the main image as done.

11. **Add a "Made in [country]" label.** Small circular flag badge or ribbon in a corner, using the country of origin that matters to the seller's marketplace (for example "Made in the USA" for a US listing, "Made in the UK" or the relevant origin for a UK/EU listing). Subtle placement, not the whole frame. Signals quality and craftsmanship to shoppers who prefer domestic or trusted-origin manufacturing. Only use it when the origin claim is true for the product.

12. **Use 3D renders.** Better than photos for shiny, reflective, or glass surfaces. Beverages, metals, premium consumer electronics. Test only if photo reads flat next to competitor renders.

13. **Show the product's main feature.** Feature in action, not just static. Blender blades spinning, UV light glowing, dispenser dispensing. Makes the primary use case immediately clear.

14. **Show all content.** Everything included in the box shown at once. Multi-part products, bundles, subscription boxes.

15. **Add "props" next to the product.** Thematic objects that reinforce category or use. Eucalyptus twigs next to a candle, coffee beans around a bag, wood grain under a knife.

### Amazon hard rules the tactics must respect
- Pure white background (RGB 255, 255, 255) required.
- Product must fill at least 85% of the frame.
- No text overlays that read as CTAs or promotional badges (small on-pack text as a design element is allowed).
- No borders, watermarks, or animated elements.

### How the skill applies this

Per ASIN in Step 4:
1. Note the current main-image state (angle, fill ratio, presence of contents / label / avatar / variant swatch).
2. Screen the 15 tactics for fit. A tactic fits when:
   - The current main image is missing it, AND
   - It matches a review-driven positive signal or a competitor-title-vocab signal, AND
   - It doesn't conflict with a strict Amazon main-image rule.
3. Rank the top 3 to 6 with product-specific mockup direction. Don't recommend all 15.
4. Include one A/B-testable "wild card" tactic (something the seller wouldn't obviously reach for) when confidence is medium-to-high.
5. Emit as an HTML table with columns: Rank / Sophie tactic / Product-specific mockup / Why this ASIN.
6. Always include a "run as an A/B test via Amazon Manage Your Experiments" line at the bottom of the block.

---

## Section 2: Secondary Images SOP

**One-line summary.** Secondary images are a conversion story in 7 fixed slots. Slots 2 and 7 are lifestyle bookends. Slots 3 to 6 are infographics that answer purchase questions.

### The fixed 7-image sequence

| Slot | Type | Purpose |
|---|---|---|
| 1 | Primary Image (white background) | See Section 1. Amazon requires white background. |
| 2 | Lifestyle Shot | Emotional opening hook. Product in use, evoke the feeling the buyer wants. |
| 3 | Infographic, Main Features/Benefits | 4 to 5 bold icons + short phrases. Sets the value proposition. |
| 4 | Infographic (choose from taxonomy) | Answers the top purchase question. |
| 5 | Infographic (choose from taxonomy) | Answers the next purchase question. |
| 6 | Infographic (choose from taxonomy) | Answers the next purchase question. |
| 7 | Lifestyle Shot | Emotional closing bookend. Same person or setting as slot 2 where possible. |

Slots 2 and 7 create an emotional frame that opens with the aspiration and closes with the payoff.

### Infographic taxonomy for slots 4, 5, 6

Choose 3 from this list based on the ASIN's category, review themes, and competitive white-space. Don't default to the same 3 across every product.

- Main Features / Benefits
- Us vs Them Comparison
- What's Included
- Different Use Cases
- Size Guide / Comparison
- Size Comparison (product next to familiar object)
- Guarantee / Warranty
- Origin of Ingredients
- Ingredient List
- Nutrition Facts
- Full Product Line
- Certification / Badges
- How to Use / Prepare
- Before / After Images (region-dependent, some EU regions prohibit)
- Other Instructions (feeding, assembly)
- Compatibility (for accessories)
- Material / Quality
- Eco-Friendliness / Sustainability
- Customer Reviews / Brand Recognition
- Brand Mission Statement / Brand Story

### Text rules
- 3 to 5 short phrases per image. No long sentences.
- Minimum font size 20 to 24 pixels for mobile readability.
- Bold, high contrast (black on white or white on colored fill).
- Preview every image on a mobile device before shipping.

### Style rules
- Colors match brand and category:
  - Skincare and beauty: warm neutrals with 1 accent.
  - Medical: blues and bright greens for cleanliness and professionalism.
  - Eco / natural products: greens and earth tones.
  - Coffee and rich consumables: deep browns and blacks.
- Consistency across the 6 secondary slots: one layout, one font, one icon set, one icon style (stroke OR filled, not mixed).
- Modern and sleek. Reference Apple, Bose, Beats, Anker. Avoid 90s highlights, gradients, or busy fonts.
- Prioritize clarity and simplicity over cluttered or gimmicky visuals.

### Ban list (copy)
"High quality," "premium quality," "best." Replace with proof, specs, or outcomes.

### How the skill applies this

Per ASIN in Step 4:
1. Read the review themes (differentiated positives and negatives) from diagnostics.
2. Read the competitive title vocabulary and comp-set image counts from diagnostics.
3. Choose 3 infographic types for slots 4, 5, 6 that answer the top-3 purchase questions those signals imply.
4. Write per-slot content with product-specific detail. Every text overlay under 8 words.
5. Emit as an HTML table with columns: Slot / Sophie type / Product-specific content.
6. Include the consistency-across-slots style note at the bottom of the block.

---

## Section 3: Premium A+ Content SOP

**One-line summary.** Premium A+ Content lifts sales ~20% (Sophie data). Sophie's Pro structure uses exactly 7 modules pulled from 4 of Amazon's 19 available Premium module types. Use the fixed sequence below.

### Access requirements
- Brand Registry active.
- 15+ approved A+ content project submissions in the trailing 12 months.
- A+ Brand Story published on every ASIN the seller owns.
- Enrollment is monthly, not automatic. Access granted at the start of the next month after criteria are met.
- Find it in Seller Central under: Advertising > A+ Content Manager > Start Creating A+ Content > Create Premium A+.

### Sophie's 7-slot Pro structure

| # | Sophie module | Seller Central module name | Purpose |
|---|---|---|---|
| 1 | Hero Image | Premium Full Image | Large product on clean or lifestyle background, mini description + brand slogan + 3 to 5 benefit icons. |
| 2 | Transformational Effect OR Video | Premium Full Image or Premium Full Video | CTA-style banner OR a 15 to 30s video. Video wrapped in a static frame matching hero background so edges align. |
| 3 | 3 to 4 Slide Benefit Carousel | Premium Navigation Carousel | Feature (2 to 3 words) + benefit (5 to 8 words) per slide. |
| 4 | Features Hotspots | Premium Hotspots 1 | Up to 5 hotspots on a product image. Each with title + description. On mobile renders 1 image per hotspot. |
| 5 | Best-case Uses / How-to Carousel | Premium Navigation Carousel | 3 to 4 slides, verbs up front. Best uses, how to use, or how it works. |
| 6 | Q&A Module | Premium Q&A | Exactly 3 questions pulled from real review pain points. |
| 7 | Comparison Table | Premium Comparison Table 1 (cross-sell own products) OR Premium Comparison Table 3 (vs competitors) OR Premium Full Image (reviews banner if neither fits) | Fallback to reviews banner only if there's nothing to compare to. |

Sophie only uses these 4 module types (Full Image, Full Video, Navigation Carousel, Hotspots 1, Q&A, Comparison Tables 1 and 3). Don't recommend other Premium module types from Amazon's 19-type menu.

### Per-module character limits and content rules

**Slot 1 Hero (Premium Full Image).** Slogan short and punchy. Benefit icon labels 2 to 3 words each. Warm neutral + 1 accent, no harsh black-and-white for beauty.

**Slot 2 Video (Premium Full Video) or Transformational Effect (Premium Full Image).** Video wrapped in a static frame matching hero background so panel edges align on desktop and mobile. CTA tagline. Headline ≤45 chars desktop, ≤32 chars mobile. Subhead ≤80 chars. Silent-friendly captions if video (assume shopper is scrolling with sound off).

**Slot 3 Benefit Carousel (Premium Navigation Carousel).** Feature name 2 to 3 words + benefit body 5 to 8 words. Verbs up front.

**Slot 4 Hotspots (Premium Hotspots 1).** Up to 5 hotspots on a clean product hero. Title ≤50 characters. Description 50 to 100 characters. Mobile renders as 1 image per hotspot.

**Slot 5 How-to Carousel (Premium Navigation Carousel).** 3 tiles max. Verbs up front. Same title + body length rule as Slot 3.

**Slot 6 Q&A (Premium Q&A).** Exactly 3 questions. Question ≤120 characters. Answer ≤250 characters. Pull questions from the negative-review themes and the top-of-mind purchase objections shopper reviews reveal.

**Slot 7 Comparison Table (Premium Comparison Table 1 or 3).** Product names ≤25 characters. Metric names ≤30 characters. Metric data ≤30 characters. Use "✓" for check marks. Include 4 to 5 metrics.

### Limited Premium A+ 5-module fallback

For sellers with Premium access but limited creative assets, or as an interim plan while working toward the 15-submission threshold:

1. **Hero / Value Proposition.** Big product, subtle lifestyle background, short promise, 3 to 5 micro-badges.
2. **Transformation / Outcome.** Before/after or "with vs without" scene. Formula: outcome (benefit) → why (tech/ingredient) → proof (stat).
3. **Features → Benefits.** 3 to 5 callouts with pictograms or hotspots. Formula per callout: feature name (2 to 3 words) + benefit (5 to 8 words).
4. **Use / Setup / Versatility.** Steps (1 to 3) or tiles showing top use cases / audiences.
5. **Trust & Comparison.** "Us vs Them" mini-table or badges (certifications, cruelty-free, BPA-free). Reviews banner also works.

### Design rules (all modules)
- Mobile-first. Assume most shoppers see A+ on mobile.
- One clear promise per module. Each banner answers one question: What is it? Why should I care? How do I use it? Is it better? Who is it for?
- Show, then tell. Lifestyle or in-use imagery first, overlays second. No walls of text.
- Hierarchy > density. Big headline (benefit), subhead (mechanism), tiny helper text only if truly needed.
- Standardize art direction. One color system, one type scale, consistent icon set, same model / lighting where possible.
- Warm neutral base + 1 accent for beauty. Avoid harsh black-and-white.
- Safe margins: keep text and key UI ≥60px from edges at 1464px export width.
- Text on photos: use 8 to 16% overlay gradient so copy remains readable on mobile.
- One icon style (stroke OR filled, never mixed).

### Copy rules
- No section labels ("Features," "Benefits") that waste pixels. Lead with the promise.
- Headlines ≤45 chars desktop, ≤32 chars mobile. Verb + outcome format.
- Subheads ≤80 chars. Explain the mechanism, ingredient, or tech.
- Bullets max 2 per module, ≤8 words each.
- Voice: speak to the buyer (parents, sensitive-skin sufferers, hosts, shooters), not the product.
- Ban list: "high quality," "premium quality," "best." Replace with proof, specs, or outcomes.
- Banned symbols: ™, ®.
- Add keyword-relevant alt text to every image (helps SEO, accessibility, and Alexa Shopping voice matching).

### File specs
- Export all A+ images at 1464px width.
- Text ≥28 to 32 px at 1464 width for mobile clarity.
- JPG at quality 80 to 90 for photos.
- PNG for plates and graphics that need crisp edges.
- Keep each panel under 1 MB to avoid mobile lag.

### How the skill applies this

Per ASIN in Step 4:
1. Draft all 7 modules with product-specific content.
2. Q&A questions pulled from the negative-review themes in diagnostics.
3. Comparison Table columns pulled from the top-5 comps in Xray OR from the seller's own catalog if cross-sell is more valuable.
4. Emit as an HTML table with columns: # / Sophie module + Seller Central name / Product-specific content plan / Copy limits.
5. Include the Limited Premium A+ 5-module fallback note at the bottom of the block.

---

## Section 4: Skill integration checklist

Every run of `listing-juice` must produce three HTML blocks per ASIN, in this order, combined into the single `sophie_recommendations_html` raw-HTML field of the report JSON (NOT `strict_structured_block`). Use these exact `<h4>` headings so the Step 9 enforcement grep can confirm all three are present:

1. **`Main image recommendations`** — ranked 15-tactic screening (see Section 1).
2. **`Secondary image sequence`** — fixed 7-slot table with 3 chosen infographic types (see Section 2).
3. **`A+ Premium module plan`** — 7-module Pro structure with Limited fallback note (see Section 3).

Rule: never emit an empty block. If a listing has no obvious opportunity, write "current image stack is on target because X, no changes recommended" rather than skipping.

Rule: never use content from outside these three sections. If Sophie updates the SOP, update this file, don't invent A+ Premium module types or main-image tactics that aren't listed here.

Rule: always cite Sophie Society as the source in the block headers so the seller-facing report is transparent about the provenance.
