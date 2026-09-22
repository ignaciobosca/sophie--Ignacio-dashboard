# COSMO Framework + Scoring Rubric

Merged reference covering the 15 COSMO intent dimensions (definitions, examples, failure modes) with the 0/1/2/N/A scoring rubric for each. The COSMO dimensions come from Amazon's research (SIGMOD 2024), which mined millions of search-buy and co-buy behaviors to identify the structural ways customers connect intent to products. A listing that covers these dimensions broadly is structurally more discoverable on Alexa Shopping.

Use alongside `category-families.md` for category-specific framing and priority.

---

## Scoring scale

| Score | Label | Meaning |
|-------|-------|---------|
| **2** | Covered | Dimension explicitly addressed in unstructured copy OR populated structured attribute. A shopper (or Alexa Shopping) would clearly infer this angle. |
| **1** | Partial | Dimension weakly addressed — mentioned briefly, implied rather than stated, or present only in backend search terms. |
| **0** | Missing | No evidence of this dimension anywhere in the listing. |
| **N/A** | Not applicable | Dimension doesn't sensibly apply to this category. Reduce the denominator by 2. |

**Score semantically, not mechanically.** A dimension counts as covered if the listing addresses it in any recognizable way — even without exact keywords from `category-families.md`. "For people winding down after a long day" covers Audience even without the word "for" appearing in an audience keyword list. Use judgment.

---

## 1. Function / Usage (`used_for_func`)

**What it captures:** The core functional purpose — what the product does.

**Why it matters:** The most basic intent. Almost every listing covers this, but many do so weakly ("great for home" vs "absorbs up to 3x its weight in water").

**Examples across categories:**
- Kitchen: "peels potatoes without removing flesh"
- Apparel: "wicks moisture during high-intensity workouts"
- Electronics: "charges two devices simultaneously"
- Pet: "removes tartar from back molars"
- Supplements: "supports a calm mind for winding down after stressful days"

**Common failure mode:** Listings that describe *features* (20oz capacity) without translating to *function* (holds enough coffee for a full morning).

---

**Scoring:**

- **2:** Specific, quantified function described in title or first two bullets. "Absorbs 3x its weight in water within 5 seconds."
- **1:** Function mentioned but generic. "Highly absorbent."
- **0:** Only features listed, no functional translation. "Microfiber material."

---

## 2. Event / Activity (`used_for_eve`)

**What it captures:** Occasions, events, or activities the product is used for.

**Why it matters:** Huge Alexa Shopping intent volume — shoppers regularly search "X for [occasion]". Gift-giving, travel, sports, and seasonal events are the largest sub-categories.

**Examples:**
- Apparel: "wedding", "job interview", "black-tie event", "hiking"
- Home: "dinner party", "housewarming", "outdoor bbq"
- Toys: "birthday party", "road trip", "rainy day"
- Food: "game day", "potluck", "meal prep"
- Supplements: "before social gatherings", "travel days", "bedtime routines"

**Common failure mode:** Listing says "great for any occasion" — which is worse than naming three specific occasions, because it signals to Alexa Shopping no particular occasion fit.

---

**Scoring:**

- **2:** Three or more specific occasions named across title/bullets. "Wedding gifts, housewarmings, anniversaries."
- **1:** One or two occasions mentioned, or generic "any occasion" framing.
- **0:** No occasion framing at all.

---

## 3. Audience (`used_for_aud`)

**What it captures:** Who the product is intended for (the user, not necessarily the buyer).

**Why it matters:** Alexa Shopping is explicitly audience-aware in its query parsing. "Gift for my dad who loves grilling" decomposes into [audience: dad, interest: grilling, intent: gift].

**Examples:**
- Apparel: "petite women", "tall men", "plus-size"
- Home: "renters", "small-apartment dwellers", "first-time homeowners"
- Kitchen: "home cooks", "professional bakers", "college students"
- Pet: "senior dogs", "puppies", "cats with dental issues"
- Supplements: "stressed professionals", "sober-curious adults", "new parents navigating sleep regressions"

**Common failure mode:** Gendered or age-generic ("for women") without specifying the life stage or need state.

---

**Scoring:**

- **2:** Specific audience named with a modifier. "For new moms navigating sleep regressions." Structured `target_audience` field populated counts as 2.
- **1:** Generic audience ("for women", "for kids") without specificity.
- **0:** No audience mentioned anywhere.

---

## 4. Capability (`capable_of`)

**What it captures:** What the product can do — its performance envelope.

**Why it matters:** Overlaps with Function but emphasizes specs with verbs. "Can hold 50 lbs" vs "holds items".

**Examples:**
- Tools: "drives 3-inch deck screws without pre-drilling"
- Electronics: "streams 4K video without buffering on 25 Mbps"
- Outdoor: "withstands sustained winds up to 40 mph"
- Supplements: "750mg kavalactones per serving (50mg per gummy)"

**Common failure mode:** Vague superlatives ("super strong") instead of quantified capability.

---

**Scoring:**

- **2:** Quantified capability statement. "Supports up to 300 lbs." "Cuts through 2-inch lumber." "750mg per serving."
- **1:** Qualitative capability. "Heavy-duty." "Strong." "High-potency."
- **0:** No capability claims.

---

## 5. Alternative Use (`used_as`)

**What it captures:** Secondary or non-obvious uses.

**Why it matters:** Captures the "versatility" angle. Alexa Shopping will surface a product for queries the listing doesn't explicitly target if alternative uses are documented. Particularly strong for "replaces X" framing.

**Examples:**
- Kitchen: "serving bowl doubles as a decorative centerpiece"
- Apparel: "scarf works as a beach cover-up"
- Tools: "pry bar also functions as a nail puller"
- Supplements: "alcohol alternative for social evenings"

**Common failure mode:** Over-claiming alternative uses that stretch credibility and invite returns.

---

**Scoring:**

- **2:** Explicit secondary use named. "Doubles as a serving tray for appetizers."
- **1:** Implied versatility ("multi-purpose", "versatile") without specifics.
- **0:** No alternative use mentioned. (This is often fine — not every product needs this.)

---

## 6. Product Type / Category (`is_a`)

**What it captures:** What the product fundamentally is — its category identity.

**Why it matters:** Anchors the listing in Amazon's taxonomy. Critical for both browse-node placement and Alexa Shopping category routing.

**Examples:**
- "cold brew coffee maker" (not just "pitcher")
- "ergonomic office chair" (not just "chair")
- "reusable silicone food storage bag" (not just "bag")
- "kava root gummies" (not just "relaxation supplement")

**Common failure mode:** Using a cute brand term instead of the recognized category name. "The Perfectly Portable Potable" is clever; Alexa Shopping has no idea what it is.

---

**Scoring:**

- **2:** Widely-recognized category name in title. "Cold brew coffee maker." "Kava root gummies."
- **1:** Category implied but dressed in brand language. "The ultimate morning companion" (with "coffee maker" buried in bullet 3).
- **0:** Category name absent or replaced entirely by branded term.

---

## 7. Time / Season (`used_on`)

**What it captures:** When the product is used — seasonally, daily, annually.

**Why it matters:** Seasonality drives enormous query volume spikes. Products with no seasonal framing miss predictable demand waves.

**Examples:**
- Apparel: "summer vacation", "late fall", "holiday parties"
- Home: "winter heating season", "spring cleaning"
- Food: "weekday dinners", "Sunday meal prep"
- Supplements: "30-60 minutes before bedtime", "after a stressful workday"

**Common failure mode:** Ignoring the time dimension entirely on products that clearly have one.

---

**Scoring:**

- **2:** Specific season, time of year, or time of day named. "Summer picnics." "Weekday mornings." "30-60 minutes before bedtime."
- **1:** Generic time framing. "Year-round use."
- **0:** No time dimension. (Often N/A.)

---

## 8. Location / Facility (`used_in_loc`)

**What it captures:** Where the product is used — physical setting.

**Why it matters:** Distinguishes near-identical products by use context. "Bedroom lamp" vs "desk lamp" vs "nursery lamp" all describe similar objects with very different intent profiles.

**Examples:**
- Home: "bedroom", "home office", "entryway", "dorm room"
- Outdoor: "backyard", "patio", "campsite", "boat"
- Professional: "hair salon", "daycare", "nail studio"
- Supplements: "nightstand", "travel bag", "gym bag"

**Common failure mode:** Treating location as obvious. It's often not — a "tumbler" could be for the office, the gym, or the car, and each is a separate search intent.

---

**Scoring:**

- **2:** Specific location named. "Kitchen counter." "Home office." "Nightstand."
- **1:** Generic location ("indoor/outdoor", "anywhere").
- **0:** No location mentioned.

---

## 9. Body Part (`used_in_body`)

**What it captures:** Where on the body the product is used or worn.

**Why it matters:** High-specificity intent, especially in apparel, beauty, and health categories.

**Examples:**
- Beauty: "sensitive skin", "oily T-zone", "cuticles"
- Apparel: "wide feet", "narrow shoulders", "short torso"
- Health: "lower back", "plantar fasciitis", "carpal tunnel"

**Applicability:** N/A for most home goods, food, tools, supplements (unless topical). Apply only when relevant — don't penalize listings that have no body-part dimension.

---

**Scoring:**

- **2:** Specific body part or body-type modifier. "Wide feet." "Sensitive scalp."
- **1:** Generic body framing. "All skin types."
- **0:** No body reference.
- **N/A:** Product has no body-part relevance (e.g., throw pillow, blender, lawn tool, most supplements).

---

## 10. Complementary (`used_with`)

**What it captures:** What the product pairs with, fits, or enhances.

**Why it matters:** Captures bundled-intent queries and cross-sell angles. Also crucial for compatibility-sensitive categories (electronics, automotive, appliances).

**Examples:**
- Electronics: "works with iPhone 15 and newer"
- Kitchen: "fits standard mason jars"
- Automotive: "compatible with 2018–2024 Honda Civic"
- Supplements: "stack with magnesium for deeper sleep"

**Common failure mode:** Not listing compatible models/sizes — leads to returns and bad reviews on products that would have fit fine for the right buyer.

---

**Scoring:**

- **2:** Specific compatible products or sizes listed. "Fits 32-oz mason jars. Compatible with iPhone 12 and newer."
- **1:** Generic compatibility claim ("works with most", "universal fit").
- **0:** No compatibility information, on a product where it's relevant.
- **N/A:** Standalone product with no compatibility dimension.

---

## 11. Used By (`used_by`)

**What it captures:** Who typically uses the product, distinct from Audience — this is habitual use, often professional or role-based.

**Why it matters:** Role-based search is common ("tools used by professional mechanics", "knives used by sushi chefs").

**Examples:**
- "used by professional photographers"
- "used by daycare workers"
- "used by competitive cyclists"

**Overlap with Audience (#3):** Audience is "who the product is *for*"; Used By is "who *actually uses* it". Often the same but sometimes different (e.g., a baby product is *for* babies, *used by* parents and caregivers).

---

**Scoring:**

- **2:** Specific user persona named. "Used by professional chefs." "Trusted by competitive cyclists."
- **1:** Generic pro framing. "Professional-grade."
- **0:** No user persona named.

---

## 12. Interest / Affinity (`xIntersted_in`)

**What it captures:** Lifestyle groups, hobbies, or affinities.

**Why it matters:** Captures identity-adjacent search. "Gift for someone who loves [X]" is a massive search category.

**Examples:**
- "for coffee enthusiasts"
- "for plant parents"
- "for vinyl collectors"
- "for true crime fans"
- "for wellness-minded professionals"

**Common failure mode:** Ignoring affinity entirely on products that clearly have one (a knife block is a tool — for whom? Home cooks. Professional chefs. Foodies. Each is a different shelf in Alexa Shopping's mental model.)

---

**Scoring:**

- **2:** Specific lifestyle or interest group named. "For coffee enthusiasts." "For plant parents." "For wellness-minded professionals."
- **1:** Vague affinity signal. "For discerning buyers."
- **0:** No affinity framing.

---

## 13. Audience Identity (`xIs_a`)

**What it captures:** Who the buyer *is* as an identity — life stage, role, or self-concept.

**Why it matters:** Distinct from Audience (#3) in that this is about the *buyer's* identity, not just who uses the product. "I am a new mom" vs "for babies".

**Examples:**
- "new parents"
- "first-time homeowners"
- "empty nesters"
- "college freshmen"
- "sober-curious adults"

**Overlap with #3:** The framework calls these two out separately because Alexa Shopping often treats them differently. A gift given by a new parent to another new parent versus a gift for a baby are different queries.

---

**Scoring:**

- **2:** Buyer identity explicitly addressed. "First-time parents." "Empty nesters downsizing." "Sober-curious adults."
- **1:** Implied buyer identity without specificity.
- **0:** No buyer-identity framing.

---

## 14. Want / Activity (`xWant`)

**What it captures:** What the buyer wants *to do* with their life — the aspirational activity the product enables.

**Why it matters:** Captures the "I want to start ___" category. Fitness, hobbies, habit changes, lifestyle shifts.

**Examples:**
- "start running"
- "learn sourdough baking"
- "get into bird photography"
- "improve my posture"
- "unwind without alcohol"

**Common failure mode:** Describing the product's features without connecting them to the customer's aspiration.

---

**Scoring:**

- **2:** Aspirational activity named. "Start your sourdough journey." "Build a home gym." "Unwind without alcohol."
- **1:** Generic aspiration. "Achieve your goals."
- **0:** No aspiration framing.

---

## 15. Problem Solved (implicit in several COSMO relations)

**What it captures:** The pain point or problem the product addresses.

**Why it matters:** "Stops ___", "prevents ___", "fixes ___" queries are high-intent and high-conversion. Listings that lead with problem-framing often outperform feature-first copy.

**Examples:**
- "stops dog from pulling on leash"
- "prevents cold brew from over-extracting"
- "eliminates static cling"
- "reduces back pain from long drives"
- "supports calm during a racing mind at bedtime" (note: for supplements, use "supports" language — see category-families.md on FDA framing)

**Note:** This isn't a single COSMO relation but rather a synthesis across `used_for_func`, `capable_of`, and `xWant`. It's listed separately because problem-framing is such a dominant pattern in high-performing Amazon copy that treating it as its own dimension is useful.

---

## Scoring notes

- **Applicability varies by category.** Beauty products should score body-part; food products should score time/season; tools should score used-by. Don't penalize listings for not covering irrelevant dimensions — mark those N/A and reduce the denominator.
- **Structured attribute coverage compensates for unstructured gaps.** If a listing's unstructured copy doesn't say "for new moms" but the Seller Central `target_audience` field is populated with "new mothers", Alexa Shopping still sees it. Score accordingly.
- **Backend search terms count but with diminishing returns.** A dimension covered only in backend terms scores 1, not 2 — Alexa Shopping and search both weight visible copy more heavily than hidden keywords.
- **Use semantic judgment, not mechanical keyword matching.** A listing that says "for people winding down after the office" covers the Audience dimension even without using the word "audience" or any list of audience keywords. Score based on whether the dimension is genuinely addressed, not whether specific vocabulary appears. Keyword lists (where provided in `category-families.md`) are hints, not gates.

**Scoring:**

- **2:** Specific problem stated and solution claimed. "Stops dog pulling in under 2 weeks." "Ends back pain from long commutes." "Supports calm during a racing mind at bedtime."
- **1:** Vague problem framing. "Solves common issues."
- **0:** No problem framing, feature-first copy only.

**For supplements specifically:** any "problem solved" language must use "supports/promotes/helps with" framing rather than "cures/treats/prevents." See `category-families.md` for FDA-safe language patterns.

## Interpreting the total score

Assuming all 15 dimensions apply (total possible: 30):

| Score | Interpretation |
|-------|----------------|
| 24–30 | Strong. Minor gaps only. |
| 18–23 | Solid baseline with real opportunities. Typical high-performing listing. |
| 12–17 | Meaningful gaps. Most listings fall here. Clear rewrite opportunity. |
| 6–11 | Weak. Copy is likely feature-first and narrow. High-impact rewrite candidate. |
| 0–5 | Severely underserved. Often small-seller or new-launch listings with placeholder copy. |

When some dimensions are N/A, scale the ranges proportionally (e.g., if 12 dimensions apply, total possible is 24 and ranges shift accordingly).

## Structured vs unstructured weighting

Alexa Shopping weights structured attributes heavily because they're unambiguous. When scoring, note the breakdown per dimension across surfaces:

- **Structured field populated** → score 2 even if unstructured copy is weak
- **Unstructured copy strong, structured field empty** → score 2 but flag the structured gap in the audit
- **Both strong** → score 2 and note as a strength
- **Both weak or absent** → score 0 or 1 per the general rubric

The rewrite proposal should always address structured gaps first when they exist — populating a field is cheaper and higher-ROI than rewriting a bullet.

## Pre-shipping validation

Every rewrite proposal should be scored against this rubric BEFORE it's written to the flat file:

1. Score the current copy (title, each bullet, description) per dimension
2. Score the proposed rewrite on the same dimensions
3. Only ship the rewrite to the flat file if:
   - The proposed copy scores strictly higher overall, OR
   - It fills a confirmed structured-attribute gap, OR
   - It addresses a specific SQP-identified funnel problem (CTR/CVR issue on a target query)
4. If the proposed rewrite scores equal or worse than current, leave the current copy in place. Surface the alternative phrasing in the HTML report under "Alternatives to consider" but don't apply it mechanically.

Apply this gate bullet-by-bullet, not just at the listing level. If bullet 3 is already strong (scores 2 on three dimensions), don't replace it just because bullets 1, 2, 4, 5 are being rewritten. Keep what's working.

Show before/after scores in the HTML report so the seller sees the delta: "Title: current 12/30 → proposed 18/30, +6 intent dimensions covered."

---
