# Rewrite Rules

How to turn diagnoses into concrete rewrite proposals that pass the pre-shipping validation gate. Category-specific rules live in `category-families.md` — read those alongside this file.

## The voice-matching rule (writes beat templates)

Every seller has a voice, audible in their current title, bullets, and description. The rewrite must sound like the same person kept writing, only better. This beats any abstract "professional jewelry voice" template.

Concrete process: before writing any rewrite, read `listing_state.title` + the five `bullet_N` fields + `description` from diagnostics.json for this ASIN. Note five things:

1. **Sentence length.** Short declarative? Long flowing? Match it.
2. **Warmth level.** Warm/personal ("Give this to a woman starting anew") or neutral/technical ("Premium sterling silver construction")? Match it.
3. **Bullet header convention.** All-caps with colon ("NEW BEGINNINGS GIFTS FOR WOMEN:"), title-case ("New Beginnings Gifts:"), or no header? Match it.
4. **How the seller names the buyer.** "She", "her", "you", "the recipient", "your loved one"? Use the same convention.
5. **Vocabulary register.** "Meaningful gift", "thoughtful", "perfect for her" (warm) vs "optimal choice", "premium-grade", "highest quality" (corporate) vs "the real deal", "no nonsense" (casual)? Match it.

If the rewrite doesn't sound like it could be the seller's own next draft, the rewrite fails even if all COSMO boxes tick.

## No-dash rule

No em-dashes (`—`) or en-dashes (`–`) anywhere in seller-facing Claude-authored strings. Use commas, periods, parentheses, or colons. Em-dashes are the single strongest AI-tell and the user has called them out directly as unacceptable. This applies to: headlines, one-liners, evidence paragraphs, all rewrite copy, opportunity-card text, and every field in the report JSON. The build script lints for this and warns; treat the warning as a hard fail.

## The voice-quality rule (not a word-count rule)

Product listing copy should sound like the **brand**, not like a customer review. This is the core quality test, and it matters more than any word-count threshold.

- Review snippets read as first-person, personal, situational: "I tried this before bed last Thursday and finally slept through." Good data, wrong voice.
- Listing copy should read as second- or third-person, benefit-forward: "30-60 minutes before bed, delivers a calm-without-fog unwind." Same concept, brand voice.

Paraphrase review concepts into brand voice. **Never lift customer sentences verbatim into listing copy**, not because of any legal rule, but because it sounds wrong. Customers notice, trust drops, Alexa Shopping quality signals drop.

Concrete test: if a bullet could be pasted into a review as-is without editing, you've lifted too much. Rewrite.

## Backend keyword de-duplication

Every token in the proposed backend search terms must NOT appear as a whole word in the proposed title, bullets, or description. Amazon already indexes copy terms; repeating them in backend wastes bytes.

Process:

1. After writing the proposed title, 5 bullets, and description, concatenate them into one lowercase string.
2. For each token you want to add to backend, run a whole-word match against that string (`\bword\b`). Drop any that match.
3. Target under 240 bytes (Amazon caps at 250, so leave headroom).
4. Priority order: SQP bucket 5 expansion queries not covered elsewhere > related recipient roles you haven't named in bullets > affinity/style terms from competitive white-space analysis > misspelling variations of key terms (only if you have budget).

Hyphenated compound terms like "mother-in-law" are safe because they don't match single tokens ("mother") via whole-word regex.

## The evidence pattern (every rewrite)

Every rewrite in the HTML must be presented with:

1. **Before:** current copy, with optional meta label (char count, byte count)
2. **After:** proposed copy, with optional meta label
3. **Evidence:** one plain-language paragraph explaining what data drove this (SQP query bucket, review theme, competitor gap, PPC converting term). No em-dashes. No jargon.
4. **Assumption to verify:** any factual claim the seller needs to confirm (dosage, material, use case, audience). Only set `has_assumption: true` when you have a real verification need, not to pad.

Skip any of these and the rewrite loses credibility. The rewrite template at `scripts/html_templates/rewrite.html` enforces this pattern per rewrite, don't output rewrites as bare before/after blocks. Before/after scoring is surfaced in the collapsible 15-dimension scorecard at the bottom of each ASIN, not on every rewrite.

## Strict vs advisory tiers

Every structured attribute the skill recommends gets classified. See `category-families.md` for per-category details.

**Strict tier — auto-fills into the flat file:**
- The exact word or value is unambiguously present in the title or bullets (not buried in description)
- The value represents an observable product fact, not a claim
- Picklist value exists in `amazon-picklist-values.md` and matches exactly
- Examples: `dosage_form: Gummy` when "gummy"/"gummies" appears in title; `diet_type: Vegan` when "vegan" is a standalone word in title or bullets; `color_name: Blue` when the listing calls the color blue

**Advisory tier — HTML only, NOT written to flat file:**
- Any health claim, safety certification, or benefit statement requiring seller verification
- Material claims not substantiated in the current copy
- Regulatory-sensitive values (`recommended_uses_for_product` for supplements, "non-GMO" / "organic" claims)
- Examples: `recommended_uses_for_product: Sleep Aid` (FDA claim territory); `material_feature: Non-GMO` when the current listing doesn't already claim non-GMO

Advisory suggestions in the HTML must:
- Appear under a clearly-labeled "Structured fields to add manually — seller to verify" section
- Include category-specific risk callout (FDA for supplement claims, false-advertising for unverified material claims)
- Be explicit: "NOT in the flat file — add via Seller Central if accurate"

## Never invent product facts

Every claim in the rewrite must be traceable to:
- The current listing (title/bullets/description/structured)
- Category context documented in the flat file (`product_type`, category nodes)
- Review data (themes, not unverified specifics)
- Competitor data (patterns, not invented claims)
- PPC data (proven-converting language)

Unverifiable claims go to the HTML's "Claims to verify before applying" section, not the flat file. If the proposed title says "750mg per serving" and the current listing's copy doesn't support that, flag it as a claim to verify.

## Pre-shipping validation gate

Before any rewrite is written to the flat file, score current vs proposed on:

1. **COSMO dimensional coverage** (per `cosmo.md`)
2. **A9-relevant keyword coverage** (priority keywords present in title, backend, bullets)
3. **Voice-quality sanity** (does it still sound like listing copy, not customer review?)
4. **Category-regulatory compliance** (per category family's softening rules)

**Ship to flat file only if:**
- Proposed scores strictly higher on COSMO, OR
- Fills a confirmed structured-attribute gap (empty field → populated with verified value), OR
- Fixes a specific SQP-identified funnel problem (Bucket 1, 2, or 3 query)
- AND does not degrade A9-relevant keyword coverage
- AND passes voice-quality + regulatory checks

**If proposed fails the gate:** leave current copy in the flat file. Surface the proposed phrasing in the HTML under "Alternatives to consider — current retained for better overall score."

Apply per-field, not per-listing. If bullet 3 scores better than the proposed rewrite, keep bullet 3. Replace only the bullets where the proposal is unambiguously better.

---

## Core rewrite patterns

Proven templates for closing common intent-dimension gaps. Adapt to brand voice and category.

### Pattern: Adding an audience angle

**When to use:** Audience dimension scores 0 or 1.

**Template:**
> Designed for [specific audience] who [specific situation or pain point].

**Examples:**
- Before: "Premium stainless steel water bottle."
- After: "Designed for commuters who want 8am coffee still steaming at noon."

- Before: "Kava root gummies."
- After: "For sober-curious adults and stressed professionals who want to unwind without alcohol."

**Pitfall:** Don't stack multiple audiences. Pick the primary one for the opening; mention secondaries in backend terms or later bullets.

### Pattern: Adding occasion depth

**When to use:** Event/Activity dimension scores 0 or 1, especially on gift-adjacent or habit-forming products.

**Template:**
> Perfect for [occasion 1], [occasion 2], or [occasion 3] — [why each works].

**Examples:**
- Before: "Great for any occasion."
- After: "Made for Friday nights, social gatherings, or winding down after a long day — no hangover, no foggy morning."

**Pitfall:** Three specific occasions beats ten. Confident specificity > exhaustive list.

### Pattern: Adding a use-location

**When to use:** Location dimension missing on a product whose use context shapes buying decisions.

**Template:**
> Fits [specific location] — [why that location's constraints are handled].

**Examples:**
- Before: "Compact design."
- After: "Fits apartment galley kitchens — 11-inch footprint with full-size function."

### Pattern: Lead-with-problem rewrite

**When to use:** Problem-Solved dimension scores 0. Feature-first copy that misses the "why should I care" angle.

**Template:**
> [Problem stated]. [Product] [specific solution mechanism].

**Examples:**
- Before: "Ergonomic memory foam pillow."
- After: "Waking up with neck pain? Contours to your spine's natural curve so back and side sleepers land in neutral alignment."

**Supplements-specific:** Use "supports"/"helps with" language, never "stops" or "ends":
- Before: "Stress relief supplement."
- After: "Supports calm through stressful days and racing-mind evenings."

**Pitfall:** Don't infomercial. "Are you TIRED of ___?" reads as cheap.

### Pattern: Quantifying capability

**When to use:** Capability dimension scores 1 — claim is qualitative.

**Template:**
> Rated for [specific threshold] — [what that means in practice].

**Examples:**
- Before: "Heavy-duty storage bin."
- After: "Rated for 75 lbs stacked — holds a full year's worth of seasonal clothes."

- Before: "High-potency kava."
- After: "750mg noble-root kavalactones per serving (50mg per gummy, 15 gummies per serving)."

### Pattern: Backend search term expansion

**When to use:** Multiple dimensions are covered only partially; backend terms have unused room.

**Approach:** Space-separated, no commas, no repeats of phrases already in visible copy. Cover audience/occasion/problem variants that visible copy doesn't address.

**Constraint:** 250 bytes total (not characters — bytes, so non-ASCII costs more). Stay under 249 to leave margin.

**Pitfall:** Don't stuff backend with title phrases. Amazon's indexes deduplicate.

### Pattern: Populating structured attributes (highest-ROI Alexa Shopping fix)

**When to use:** Structured attribute fields are empty and the answer is observable in current copy.

**Approach:** Check each category-relevant structured field. If the current copy contains the value, auto-fill (strict tier). If the field needs a claim to populate, surface as advisory (HTML only).

See `category-families.md` for per-family priority fields.

### Pattern: Title surgery (when character budget is tight)

**When to use:** Multiple dimensions need to land in the title but it's already near 200 chars.

**Audit the current title for waste:**
- Repeated brand name (Amazon strips duplicates in indexing)
- Feature-words with no search volume: "premium," "luxury," "professional-grade"
- Filler adjectives: "amazing," "incredible," "best-in-class"

Replace each waste-word with an intent-carrying term.

**Example:**
- Before (193 chars): "BrandName Premium Luxury Professional-Grade Stainless Steel Insulated Water Bottle — Amazing BPA-Free Leak-Proof Design, Perfect for All Occasions, Incredible 24oz Capacity"
- After (198 chars): "BrandName 24oz Insulated Water Bottle — Keeps Coffee Hot 12 Hours / Cold Drinks 24 Hours — Commuter-Friendly Narrow Fit for Car Cupholders — BPA-Free Stainless Steel — Gift-Ready"

Same length, three more dimensions covered (capability quantified, location added, audience implied).

### Pattern: Bullet structure per category family

Read `category-families.md` for the category's bullet template. Each family has a 5-bullet structure that maps to the most-important COSMO dimensions for that category.

The structure is a **starting frame**, not a script. If the category family says "bullet 2 = capability" but the ASIN's biggest gap is Audience, and Audience fits naturally in bullet 2, use bullet 2 for audience and move capability to bullet 3. Category bullet templates optimize for the typical gap profile; actual ASIN bullet assignments respond to actual ASIN gaps.

### Pattern: Evidence-grounded rewrite

**When to use:** Any time review insights, competitor data, or PPC converting terms are available.

**The pattern: claim → evidence → assumption.**

**Example annotation in the HTML:**

> **Bullet 2 rewrite**
>
> Before: "Comfortable fit."
>
> After: "True to size — customers with wide feet (D–EE width) report the toe box accommodates without squeezing."
>
> Evidence: Top-5 competitor ASINs have 340+ combined review mentions of "narrow" / "tight toe box" / "ran small." Leading with width specificity differentiates against that pattern.
>
> Assumption to verify: Seller confirms product actually fits D–EE width.

Never skip the assumption step on any rewrite that makes a factual product claim.

---

## Anti-patterns to avoid

- **Keyword-stuffing visible copy.** "Water bottle thermos flask hydration vessel tumbler" in a bullet reads as spam. Hurts CVR even if it catches a few extra searches.
- **Over-claiming versatility.** If the rewrite names more than 3 alternative uses, Alexa Shopping and shoppers both distrust.
- **Inventing audiences.** "For yoga moms, CEO dads, college students, grandparents" — that's every audience, which is none.
- **Replacing product-type language with brand terms.** "The SnoozePod" isn't a product type. Call it a pillow first, then name it.
- **Forcing problem-solved framing on delightful products.** Some products are indulgences, not pain relievers. "Stops boring weekends!" cheapens.
- **Supplement disease claims.** "Treats insomnia," "cures anxiety," "FDA approved" — never, regardless of how the seller requests it. Use structure-function language.
- **Duplicate bullets across ASINs.** If ASIN A's bullet 2 reads identically to ASIN B's bullet 2, Claude drifted. Each ASIN's rewrite must be evidence-grounded in its own data.
- **"For sale" SEO tricks** like stuffing bullets with numbered lists of keywords. Reads as spam. Listings that use this pattern score poorly on Alexa Shopping quality and are often flagged by Amazon's own compliance checks.

## Before you finalize a rewrite

Run through this mental checklist:

1. Does every claim trace to evidence in the inputs?
2. Would this read as listing copy, not review copy?
3. Did I check the category family rules (regulatory softening, bullet structure, strict/advisory tier)?
4. Did the pre-shipping validation gate pass (higher COSMO score, not worse A9, voice-quality OK)?
5. Are there any dimension gaps left that higher-priority SQP queries target?
6. Are the structured-field recommendations correctly split into strict (auto-fill) vs advisory (HTML only)?

If any answer is "no" or "not sure," revise before writing to the flat file.
