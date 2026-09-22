# Category Families

Maps Amazon `product_type` values to category families, each with its own optimization rules. Read this reference when determining how to score and rewrite a given ASIN.

## Detection

Every row in the Category Listings Report has a `product_type` column. Read it per ASIN (not per flat file — a single file can mix categories). Map to a family via the lookup table below.

If `product_type` doesn't match any family, use the **generic** family and flag the fallback in the HTML report's per-ASIN section.

## Family lookup

| Family | Example product_types | Characteristics |
|---|---|---|
| **supplements** | `HERBAL_SUPPLEMENT`, `VITAMIN`, `DIETARY_SUPPLEMENTS`, `NUTRITIONAL_SUPPLEMENT` | FDA-sensitive claim language, picklists for diet_type / recommended_uses, benefit-driven bullets |
| **consumables** | `GROCERY`, `BEVERAGE`, `COFFEE`, `TEA`, `SNACK_FOOD`, `CONDIMENT`, `CANDY` | Taste + ingredient + occasion driven; some FDA structure-function rules on functional foods |
| **beauty** | `BEAUTY`, `SKIN_CARE`, `MAKEUP`, `HAIR_CARE`, `PERSONAL_CARE_APPLIANCE`, `FRAGRANCE` | FDA cosmetics rules (different from supplement rules); sensitive ingredient claims; body-part dimension critical |
| **apparel** | `SHIRT`, `DRESS`, `PANTS`, `SHOES`, `OUTERWEAR`, `UNDERWEAR`, `SOCKS`, `ACCESSORY` | Size/fit/material focus; occasion + season dimensions critical; body-part dimension relevant |
| **jewelry** | `NECKLACE`, `RING`, `EARRING`, `BRACELET`, `ANKLET`, `FINEOTHER`, `JEWELRY` | Gift-occasion + audience + material driven; rich structured attributes (gem_type, metal_type, chain_type, occasion, theme); no FDA issues but avoid medical claims on accessories |
| **hardgoods** | `HOME`, `KITCHEN`, `COOKWARE`, `FURNITURE`, `HOME_BED_AND_BATH`, `LAWN_AND_GARDEN`, `TOOLS`, `HARDWARE` | Spec-driven listings; capability + location + compatibility dimensions critical; no regulatory softening needed |
| **electronics** | `CONSUMER_ELECTRONICS`, `COMPUTER`, `CELL_PHONE_ACCESSORY`, `WIRELESS_ACCESSORY`, `CE`, `HEADPHONES` | Compatibility + capability dimensions critical; FCC/UL certification claims are risk surface; feature-spec listings |
| **pets** | `PET`, `PET_FOOD`, `PET_SUPPLIES`, `PET_TOYS` | Audience is both owner and pet; food rules differ from toy rules within the family — note per-ASIN |
| **children** | `TOYS`, `BABY_PRODUCT`, `CHILDRENS_CLOTHING`, `CHILDRENS_BOOK` | CPSC safety rules apply; age-grading critical; parents are buyers not users; choking hazard + lead testing claims |
| **generic** (fallback) | Anything else | No regulatory softening applied; universal COSMO scoring; no structured-attribute auto-fill; conservative rewrites |

### Reading this file efficiently

This file is ~400 lines with 10 family sections. **Only read the section for the detected family** — don't read the whole file. Use the line numbers below with `view(path, view_range=[start, end])`:

| Family | Section lines (approx) |
|---|---|
| supplements | 28–77 |
| consumables | 79–109 |
| beauty | 111–146 |
| apparel | 148–182 |
| jewelry | 184–242 |
| hardgoods | 244–275 |
| electronics | 277–306 |
| pets | 308–337 |
| children | 339–368 |
| generic | 370–392 |

Plus lines 394–403 ("Cross-family notes") for CBD, medical devices, and multi-family portfolios.

---

## supplements

**Regulatory framing:** FDA-regulated as dietary supplements. Must not make disease-treatment claims (no "cures," "treats," "prevents," "reverses," "clinically proven," "FDA approved"). Use structure-function language: "supports," "promotes," "helps with," "for [outcome]." Cultural/historical framing ("traditionally used for") and customer-experience framing ("many customers use this for") are safer than direct claims.

**Critical COSMO dimensions:** Product Type, Audience, Want/Activity, Problem Solved (with supports language), Capability (for dose/potency), Event/Occasion (when to take), Interest/Affinity.

**Low-priority dimensions:** Body Part (mostly N/A except topical supplements), Location (unless bedtime/travel specific).

**Keyword detectors (hints, not gates):**

| Dimension | Keywords to look for |
|---|---|
| 1 — Function | supports, promotes, helps, for, delivers, contains |
| 2 — Event | bedtime, travel, before, after, social, workout, stressful |
| 3 — Audience | adult, adults, professional, stressed, sober, curious, new parent, traveler |
| 4 — Capability | mg, ml, servings, dose, strength, potency, per gummy, per serving, per capsule |
| 6 — Product Type | gummy, gummies, capsule, tablet, tincture, drops, powder, extract, supplement |
| 7 — Time | minutes, nightly, daily, morning, evening, bedtime, fast, onset |
| 9 — Ingredients | specific ingredient names (kava, ashwagandha, GABA, magnesium, melatonin, noble, root); organic, natural, vegan, gluten-free, non-GMO |
| 13 — Identity | sober curious, stressed professional, new parent, wellness enthusiast |
| 14 — Want | relax, unwind, decompress, wind down, ease, calm, sleep, rest, recharge, mellow, focus |
| 15 — Problem | stress, anxiety, sleep, insomnia, restless, tension, overwhelm, burnout, racing mind, hangover |

**Structured attributes to prioritize (strict tier — auto-fill if exact word is in title/bullets):**
- `diet_type` (Vegan, Gluten Free, Plant Based, Vegetarian, Keto, Kosher, Halal, Paleo)
- `dosage_form` (Gummy, Capsule, Tablet, Softgel, Liquid, Powder, Drops, Tincture, Lozenge, Chewable)
- `item_form` (same values as dosage_form)
- `plant_or_animal_product_type` (Plant for herbal, Animal for e.g. collagen)
- `container_type` (Bag, Bottle, Pouch, Jar, Box, Tub, Canister)
- `flavor` (free-text, single value from listing)

**Structured attributes to surface as ADVISORY only (HTML only, not auto-filled):**
- `recommended_uses_for_product` — all values are health claims that need seller approval. Picklist includes: Sleep Aid, Anxiety Relief, Brain Health, Immune Support, Hangover Relief, Pain Relief, Digestive Health, Joint Health, Muscle Recovery, etc. Suggest 4-5 relevant values in the HTML with a "seller to review and apply manually" note and FDA-caution callout.
- `special_ingredients` (free-text ingredient callouts — needs seller verification)
- `material_feature` (Vegan, Non-GMO, etc. — needs seller verification of claim accuracy)

**Bullet structure (5 bullets):**
1. Differentiator + audience (what this is, who it's for)
2. Capability / dose quantification (per-unit specificity matters — pre-empts "misleading" complaints)
3. Events / occasions / locations (when and where people use it)
4. Outcome / problem addressed (FDA-safe "supports" language; customer vocabulary)
5. Origin, trust, quality signals (sourcing, testing, diet tags, certifications)

**Minimum data thresholds:**
- Min reviews to trust review mining: 50 (below this, themes are individual quirks not patterns)
- Min SQP queries to run funnel diagnostic: 20
- Min impressions per query to count in CTR analysis: 100
- Min clicks per query to count in CVR analysis: 5

---

## consumables

**Regulatory framing:** Standard FDA food labeling rules. No disease claims. Structure-function claims allowed on functional foods with proper substantiation. "Organic" requires USDA certification. "Natural" is not FDA-defined for foods.

**Critical COSMO dimensions:** Product Type, Taste/Flavor (captured through Ingredients #9), Event/Occasion (meal-prep, game-day, etc.), Audience, Interest/Affinity (diet-adjacent: keto, paleo, low-sugar).

**Keyword detectors:**

| Dimension | Keywords |
|---|---|
| 2 — Event | meal prep, weekday, weekend, game day, potluck, breakfast, lunch, dinner, snack |
| 3 — Audience | home cook, beginner, keto, paleo, low-carb, health-conscious |
| 9 — Ingredients | organic, non-GMO, gluten-free, sugar-free, grass-fed, pasture-raised, farm-to-table, specific ingredient names |
| 12 — Interest | keto lifestyle, paleo, low-carb, clean eating, foodie, enthusiast |

**Structured attributes (strict tier):**
- `diet_type` (same picklist as supplements)
- `flavor`
- `allergen_information` (Contains / Free From)
- `item_form`

**Bullet structure:**
1. What it is + primary taste/flavor descriptor
2. Ingredient quality / sourcing
3. Occasions / use cases (when to eat/drink, how to prepare)
4. Dietary fit (diet claims, allergen info)
5. Brand story / certification / trust

**Min thresholds:** 50 reviews for mining; 20 SQP queries for diagnostic.

---

## beauty

**Regulatory framing:** FDA cosmetics rules. Cosmetics can't claim to "change body structure or function" without moving into drug territory. "Firms skin" — borderline claim, needs substantiation. "Reduces wrinkles" is a structural claim; "softens the appearance of wrinkles" is a cosmetic claim (safer). "Anti-aging" is discouraged; "age-defying" or "youthful" are softer alternatives. SPF claims require FDA OTC drug registration.

**Critical COSMO dimensions:** Body Part (skin type, hair type, specific area), Audience, Ingredient (active and supporting), Function, Interest (clean beauty, vegan beauty, anti-aging, fragrance-free).

**Keyword detectors:**

| Dimension | Keywords |
|---|---|
| 3 — Audience | sensitive skin, oily skin, dry skin, combination, aging, dull, teen, mature |
| 9 — Ingredients | retinol, hyaluronic acid, niacinamide, vitamin c, peptide, ceramide, natural, organic, cruelty-free, vegan, clean, paraben-free, sulfate-free |
| 9b — Body Part | face, neck, eye, lip, hand, scalp, body, under-eye, T-zone |
| 14 — Want | glow, brighten, hydrate, firm (softly: "appearance of firmness"), smooth |
| 15 — Problem | dryness, dullness, breakouts (carefully), sensitivity, appearance of fine lines |

**Structured attributes (strict tier):**
- `skin_type` (Dry, Oily, Combination, Sensitive, Normal)
- `hair_type` (Straight, Wavy, Curly, Coily, etc.)
- `material_feature` (Vegan, Cruelty-Free, Paraben-Free, Sulfate-Free, Fragrance-Free)
- `size` / `volume`

**Advisory only:**
- Active ingredient claims beyond what's already stated
- "Anti-aging" or similar regulated claims

**Bullet structure:**
1. Skin/hair concern addressed + target audience
2. Hero ingredient(s) + what they do (cosmetic-safe language)
3. How to use / when to apply / routine fit
4. Result customers experience (cosmetic-claim safe)
5. Clean/ethical credentials + dermatologist tested / clinical data if applicable

**Min thresholds:** 50 reviews for mining.

---

## apparel

**Regulatory framing:** No FDA issues. Textile labeling rules apply (fiber content, country of origin) but these are structured fields, not copy concerns.

**Critical COSMO dimensions:** Product Type (specific garment category), Audience (body type, lifestyle), Event/Occasion, Time/Season, Complementary (fits/pairs with), Body Part (fit-specific).

**Keyword detectors:**

| Dimension | Keywords |
|---|---|
| 2 — Event | wedding, work, gym, hiking, outdoor, interview, date, travel, vacation, party, workout |
| 3 — Audience | petite, tall, plus-size, slim, athletic, curvy, mature |
| 4 — Capability | stretch, breathable, moisture-wicking, quick-dry, waterproof, insulated, UPF |
| 7 — Season | summer, winter, spring, fall, warm weather, cold weather, all-season |
| 9 — Material | cotton, polyester, wool, cashmere, linen, silk, spandex, leather, organic cotton |
| 9b — Body Part | shoulders, waist, hips, feet, back, torso, legs |

**Structured attributes (strict tier):**
- `size_name`, `color_name`, `style_name`
- `material_type` (specific fiber content)
- `care_instructions` (machine wash, hand wash, dry clean)
- `seasons`
- `target_gender`
- `age_range_description`

**Bullet structure:**
1. Silhouette/cut + target body type
2. Material + feel/weight + care
3. Occasions / outfit contexts / seasons
4. Fit notes (runs true to size / consider sizing up / etc. — from reviews if available)
5. Design details + versatility + styling ideas

**Min thresholds:** 100 reviews for fit-pattern mining (fit complaints are specific — need volume).

---

## jewelry

**Regulatory framing:** No FDA issues per se, but jewelry listings that make medical or health claims ("treats infertility", "balances hormones", "promotes fertility", "cures anxiety", "heals", "clinically proven") risk suppression and customer trust issues — an accessory making body-effect claims is a red flag to Alexa Shopping quality signals AND to Amazon compliance. Use soft symbolism framing instead: "a meaningful symbol of new beginnings", "a thoughtful gift for someone starting a new chapter", "traditionally associated with [theme]".

**Critical COSMO dimensions:** Product Type (specific jewelry category), Audience (the recipient, often a gift scenario), Event/Occasion (birthdays, anniversaries, milestones — highest priority for gift jewelry), Interest/Affinity (crystal lovers, spiritual, moon phase, astrology, minimalist), Material (gem + metal are both structured and searched), Problem Solved ("what to give for X moment"), Used By (the recipient's life stage or role).

**Low-priority dimensions:** Location/Facility (N/A unless travel jewelry), Time/Season (only relevant for birthstone/seasonal pieces), Body Part (partial — pendant on chest is implicit).

**Keyword detectors (hints, not gates):**

| Dimension | Keywords to look for |
|---|---|
| 1 — Function | meaningful, symbolic, reminder, represents, honors, celebrates |
| 2 — Event | birthday, anniversary, wedding, graduation, retirement, valentine, mothers day, christmas, engagement, divorce, promotion, new job, milestone |
| 3 — Audience | for her, for him, wife, daughter, mother, sister, best friend, coworker, granddaughter, mother-in-law |
| 6 — Product Type | necklace, pendant, ring, earrings, bracelet, anklet, choker, chain |
| 9 — Material | sterling silver, 925, 14k, 18k, gold-filled, rose gold, gemstone names (moonstone, opal, amethyst, citrine, garnet, etc.), diamond |
| 12 — Affinity | minimalist, boho, spiritual, witchy, celestial, moon, stars, nature, dainty, statement |
| 13 — Identity | new mom, empty nester, retiree, graduate, newlywed |
| 15 — Problem | struggling to find a gift, meaningful gift for X moment, something she'll actually wear |

**Structured attributes to prioritize (strict tier — auto-fill if the exact value is unambiguously in title/bullets AND the cell is currently empty):**

- `gem_type` (e.g., Moonstone, Opal, Amethyst, Citrine, Garnet, Aquamarine, Diamond) — fill if named in title or bullets
- `metal_type` (e.g., sterling-silver, 14k-gold, 18k-gold, rose-gold, gold-plated, silver-plated) — fill if named
- `metal_stamp` (e.g., "925 Sterling Silver", "14K") — fill if explicitly in copy
- `chain_type` (Cable, Box, Rope, Snake, Figaro, Curb, Singapore, Wheat) — fill if named
- `setting_type` (Bezel-Setting, Prong, Pavé, Channel, Tension) — fill if named
- `stone_shape` per stone slot (Round, Oval, Rectangular, Pear, Princess, Cushion, Emerald-Cut, Marquise, Heart) — fill if stated
- `target_gender` (Female, Male, Unisex) — fill from "for women"/"for men"/etc. framing
- `pendant_description` — short free-text describing the pendant shape ("teardrop moonstone", "rainbow moonstone square")
- `occasion` (Anniversary, Birthday, Wedding, Valentine's Day, Mother's Day, Christmas, Graduation, Engagement, Father's Day, Easter, Thanksgiving, Halloween, New Year, Promotion, Housewarming, Baby Shower) — **repeat the field for each applicable occasion**. Fill from explicit occasion framing in copy.
- `theme` (Rainbow, Nature, Spiritual, Love, Moon, Celestial, Animal, Tree of Life, Cross, Heart, Infinity, etc.) — free-ish text
- `chain_length_decimal_value` + `chain_length_unit` — if "18 inches" / "18-inch chain" is in copy, fill 18.00 + Inches
- `chain_length_minimum` / `chain_length_maximum` — for adjustable chains (fill both units)
- `number_of_items` — integer count if stated
- `color` / `color_name` — the visible metal/stone color

**Advisory tier (HTML only, NOT auto-filled):**

- `material_feature` values like "Hypoallergenic", "Nickel-Free", "Tarnish-Resistant" — seller must verify these are factually accurate before applying
- `stone_creation_method` = "Natural" vs "Lab-Created" vs "Synthetic" — fill only if seller confirms (don't infer from "genuine" or "real")
- `stone_treatment_method` (Heated, Irradiated, Bleached, Untreated) — seller must verify
- `stone_clarity` grades (VVS, VS, SI, etc.) — only if seller has a GIA/formal grading, never infer
- Any claim implying spiritual, healing, or mood effects (even when these words appear in the listing, do NOT populate a structured "benefit" field — those are suppression-risky claims)

**Bullet structure (5 bullets, mapped to jewelry gifting intent):**
1. Occasion + recipient + gift framing (who this is for, what moment it celebrates)
2. Design specifics (gem, metal stamp, chain details, size, setting — the physical anchors)
3. Quality + sourcing + durability (what makes this not-cheap; addresses common jewelry quality concerns)
4. Gift-ready presentation (packaging, card, gift box — huge lift for gifting queries)
5. Symbolism + meaning (soft framing, not medical; why this design, what it represents)

**Min thresholds:** 50 reviews for theme mining; 20 SQP queries for funnel diagnostic.

**Required HTML callout for jewelry listings with medical/healing language in current copy:**
> The current listing contains language that frames the product as affecting physical or mental health ("balances hormones", "promotes fertility", "heals", "treats [condition]"). This is a suppression risk on an accessory listing and hurts Alexa Shopping quality signals. Rewrite proposals soften this to symbolic framing ("meaningful symbol of", "traditionally associated with"). Seller should review the rewrite and apply if aligned with brand intent.

---

## hardgoods

**Regulatory framing:** No FDA issues. Product safety depends on specific category (cookware has lead-testing concerns; furniture has flammability standards; tools have OSHA relevance if professional). For general hardgoods, no special claim softening needed.

**Critical COSMO dimensions:** Product Type, Capability (specs drive purchase), Location/Facility, Complementary (compatibility, fits-with), Function (what it does specifically).

**Keyword detectors:**

| Dimension | Keywords |
|---|---|
| 4 — Capability | holds up to, supports up to, withstands, rated for, dishwasher safe, oven safe, microwave safe, heat resistant |
| 6 — Product Type | specific tool/appliance/furniture name |
| 8 — Location | kitchen, bathroom, bedroom, garage, backyard, outdoor, office, dorm |
| 9 — Material | stainless steel, cast iron, ceramic, bamboo, oak, pine, aluminum, silicone |
| 10 — Complementary | fits, compatible with, works with, universal, standard size |

**Structured attributes (strict tier):**
- `material_type`
- `color_name`, `size_name`
- `room_type` (if applicable — living room, kitchen, etc.)
- `mounting_type`, `power_source` (if applicable)

**Bullet structure:**
1. Product type + primary capability / spec (size, capacity)
2. Material + construction quality
3. Use cases / locations / compatibility
4. Care / maintenance / durability
5. Design + warranty / trust signals

**Min thresholds:** 50 reviews for quality-pattern mining.

---

## electronics

**Regulatory framing:** FCC certification required for wireless devices; UL for safety-rated electrical products. Don't claim certifications the product doesn't actually hold. "Medical device" claims trigger FDA scrutiny — most consumer electronics must avoid this.

**Critical COSMO dimensions:** Product Type, Capability (specs), Complementary (compatibility is often #1 for electronics), Audience, Function.

**Keyword detectors:**

| Dimension | Keywords |
|---|---|
| 4 — Capability | hz, ghz, mbps, gbps, mah, lumens, pixels, resolution, bandwidth, charge time, battery life |
| 6 — Product Type | specific device category |
| 10 — Complementary | compatible with, works with, fits [device], [brand] compatible, USB-C, Bluetooth [version], Wi-Fi [standard] |

**Structured attributes (strict tier):**
- `compatible_devices` (free-text)
- `connectivity_technology` (Bluetooth, Wi-Fi, USB, HDMI, etc.)
- `power_source`
- `color_name`

**Bullet structure:**
1. Product type + hero capability
2. Core spec breakdown (resolution, battery, charge time, etc.)
3. Compatibility (specific devices, OS versions, standards)
4. What's in the box + setup
5. Warranty / support / brand trust

**Min thresholds:** 30 reviews for mining (tech products often have thin review bases, threshold is lower).

---

## pets

**Regulatory framing:** Pet food is regulated by FDA (and AAFCO for nutritional adequacy claims). "Complete and balanced" requires AAFCO substantiation. Pet supplements follow animal drug vs dietary supplement distinction that varies by claim. Pet toys have general safety (choking hazards for small breeds).

**Critical COSMO dimensions:** Audience (the pet: species, breed size, age), Used By (the human buyer sometimes), Interest/Affinity (owner identity: "dog parent"), Problem Solved (specific pet issue).

**Keyword detectors:**

| Dimension | Keywords |
|---|---|
| 3 — Audience (pet) | puppy, adult dog, senior, small breed, large breed, kitten, senior cat, finicky |
| 9 — Ingredients | grain-free, high-protein, chicken, beef, salmon, limited ingredient, real meat first |
| 12 — Affinity | dog lover, cat parent, pet parent, pet wellness enthusiast |
| 15 — Problem (pet) | skin sensitivity, digestive sensitivity, dental tartar, anxiety, joint health, allergies |

**Structured attributes (strict tier):**
- `pet_breed` (if specific breed), `pet_size` (Small, Medium, Large, X-Large), `pet_age_range` (Puppy, Adult, Senior)
- `flavor` (for food/treats)
- `material_type` (for toys: rubber, rope, plush)

**Bullet structure:**
1. Pet audience + primary benefit
2. Ingredients (food) or materials (toys) + key differentiator
3. When/how to use (feeding guidance, play scenarios)
4. Problem addressed (specific pet concern)
5. Brand story / vet recommended / quality signals

**Min thresholds:** 50 reviews for mining.

---

## children

**Regulatory framing:** CPSC (Consumer Product Safety Commission) applies. Lead-in-paint testing required for children's products. Choking hazard warnings (for small parts, ages 3+). Age grading is regulated — "ages 3+" is a safety claim, not just a marketing choice. Educational claims on toys/books are subject to FTC scrutiny.

**Critical COSMO dimensions:** Audience (age range, developmental stage), Used By (parent/caregiver in baby products), Function (educational, developmental, entertainment), Interest/Affinity (parenting identity).

**Keyword detectors:**

| Dimension | Keywords |
|---|---|
| 3 — Audience (child) | toddler, preschool, kindergartner, elementary, ages 3-6, ages 6-10, baby, infant, newborn |
| 11 — Used By | new parents, caregivers, teachers, grandparents |
| 12 — Affinity | Montessori, STEM, educational, imaginative play, sensory play |
| 14 — Want (parental) | develop motor skills, learn letters, practice counting, screen-free |

**Structured attributes (strict tier):**
- `age_range_description`, `minimum_manufacturer_age_in_months`, `maximum_manufacturer_age_in_months`
- `material_type`
- `educational_objective`

**Bullet structure:**
1. Age range + developmental benefit
2. Materials + safety (non-toxic, no small parts if applicable)
3. What kids do with it / how they play
4. Parent/educator appeal (Montessori, STEM, screen-free, etc.)
5. Safety certifications + brand trust

**Min thresholds:** 50 reviews for mining.

---

## generic (fallback)

When `product_type` doesn't match any family above, use this.

**Regulatory framing:** None applied. Don't auto-soften claims or add caution language (without knowing the category, softening could weaken legitimate copy). In the HTML report, note that category-specific regulatory review is up to the seller.

**COSMO scoring:** Use `cosmo.md` semantic scoring only. Don't rely on keyword detectors — without category context, keyword lists mislead more than they help.

**Structured attributes:** Do NOT auto-fill any picklist attributes. The flat-file writer should only update title/bullets/description/backend for generic-family ASINs. Surface structured-attribute gaps in the HTML as advisory suggestions for the seller to investigate.

**Bullet structure (neutral):**
1. What it is + who it's for
2. What it does / primary capability
3. When/where/how to use
4. Why this one (differentiator)
5. Trust / guarantee / brand

**Min thresholds:** same as supplements (50 reviews, 20 SQP queries).

**Required HTML callout for generic-family ASINs:**
> Product type `[X]` didn't match a known category family. Generic optimization rules applied. Category-specific guidance (regulatory claim language, structured-attribute picklists, industry-standard bullet structure) was not applied. Manual review recommended for: (1) any benefit/claim language, (2) structured attribute fills, (3) bullet topic selection.

---

## Cross-family notes

**Multi-family portfolio:** If a flat file contains ASINs from different families, apply per-ASIN detection. The HTML executive summary notes the mix: "Mixed portfolio: 3 ASINs audited under supplements lens, 2 under hardgoods lens."

**CBD:** NOT covered by supplements family. CBD has its own regulatory complexity (state-by-state, FDA enforcement discretion, hemp-derived vs marijuana-derived). If `product_type` is CBD-related or the copy contains CBD/hemp/cannabidiol without being hemp-seed, apply generic family rules and add a prominent HTML callout: "CBD products have category-specific regulatory rules not covered by this skill. Manual legal review required before applying any copy changes."

**Medical devices / Class I or II:** Generic family. Add callout: "This appears to be a regulated medical device. Claim language is FDA-governed. Manual regulatory review required."

**Future families to consider adding:** automotive, books, music, software, digital products. Currently bucketed to `generic`. If you get a run with one of these and the generic output is weak, that's a signal to add a family.
