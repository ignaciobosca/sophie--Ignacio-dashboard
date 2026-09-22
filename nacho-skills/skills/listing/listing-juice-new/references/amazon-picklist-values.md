# Amazon Picklist Values

Known-valid values for structured attributes that use controlled picklists. Use alongside `flat-file.md` (picklist validation step in the Writing section) and `category-families.md` (per-family priority fields).

**Coverage is partial.** Amazon publishes thousands of picklist values across thousands of category templates. This reference covers the structured attributes that the skill most commonly writes to. For any value not listed here, validate by checking the data validation dropdown in the flat file itself.

## How to read this reference

Each section covers one structured attribute. For each:
- **Field name** (as it appears in row 4 attribute IDs)
- **Strict or advisory** — whether the skill may auto-fill it
- **Valid values** (common subset — full picklist is category-specific)
- **Guidance** — when to use which value

When a field is marked **advisory**, the skill writes suggestions in the HTML only, never to the flat file — even if a valid picklist value is detected.

---

## diet_type — strict

**Applies to:** supplements, consumables, pet food.

**Valid values:**
- Vegan
- Vegetarian
- Plant Based
- Gluten Free
- Keto
- Kosher
- Halal
- Paleo
- Dairy Free
- Nut Free
- Soy Free
- Organic
- Non GMO

**Strict auto-fill rule:** write only when the exact word (or close variant) appears as a standalone term in the title or bullets. "Vegan" in title → write `Vegan`. "Plant-based" in bullets → write `Plant Based`. Don't infer ("this has no animal ingredients, must be vegan").

---

## dosage_form / item_form — strict

**Applies to:** supplements primarily; item_form has broader category use.

**Valid dosage_form values:**
- Gummy
- Capsule
- Tablet
- Softgel
- Liquid
- Powder
- Drops
- Tincture
- Lozenge
- Chewable
- Gel
- Cream
- Spray

**Strict auto-fill rule:** the exact form must appear in title or bullets. "Kava gummies" → `Gummy`. "Magnesium capsules" → `Capsule`.

`item_form` accepts the same picklist in supplement categories but may have different valid values in other categories (e.g., consumables adds Bar, Cookie, Beverage).

---

## container_type — strict

**Applies to:** supplements, consumables, beauty.

**Valid values:**
- Bottle
- Bag
- Box
- Pouch
- Jar
- Tub
- Can
- Canister
- Sachet
- Stick Pack
- Blister Pack

**Strict auto-fill rule:** observable from the listing (images + description). Default to Bottle for supplements if unspecified — most common packaging.

---

## plant_or_animal_product_type — strict

**Applies to:** supplements, consumables.

**Valid values:**
- Plant
- Animal

**Strict auto-fill rule:** plants for herbal supplements (kava, ashwagandha, etc.), Animal for collagen / fish oil / bone broth.

---

## flavor — strict (free-text but short)

**Applies to:** supplements, consumables, pet food.

Free-text field, but keep values short and consistent. Examples:
- `Peach`
- `Mixed Berry`
- `Chocolate`
- `Vanilla`
- `Unflavored`

**Strict auto-fill rule:** the flavor must be explicitly named in the title or bullets. Don't guess.

---

## size_name / color_name / style_name — strict (category-specific)

**Applies to:** apparel, beauty, hardgoods, electronics.

Free-text but controlled per category. Match the existing values already populated in the seller's catalog (from sibling variants). If blank and the listing clearly states the attribute, auto-fill.

For variations, preserve the parent's chosen vocabulary. If siblings use "Navy Blue" not "Blue", new rows should use "Navy Blue".

---

## material_type — strict

**Applies to:** hardgoods, apparel, furniture, cookware.

Free-text but with preferred values. Common:
- Stainless Steel
- Cotton
- Polyester
- Wool
- Leather
- Silicone
- Ceramic
- Bamboo
- Plastic
- Wood
- Aluminum
- Cast Iron

**Strict auto-fill rule:** material must be explicitly stated in title or bullets.

---

## material_feature — advisory

**Applies to:** beauty, apparel, supplements, pets.

**Picklist values (common):**
- Vegan
- Cruelty Free
- Paraben Free
- Sulfate Free
- Fragrance Free
- Non GMO
- Organic
- Biodegradable
- Recyclable
- Eco Friendly

**Advisory-only reason:** most of these values are claims that require certification or substantiation. "Organic" requires USDA certification for food/supplements. "Vegan" is a defensible observable claim only if no animal ingredients. Don't auto-fill — surface in HTML with seller-verify note.

---

## recommended_uses_for_product — advisory

**Applies to:** supplements primarily.

**Picklist values (common, supplements-specific):**
- Sleep Aid
- Anxiety Relief
- Brain Health
- Immune Support
- Digestive Health
- Joint Health
- Muscle Recovery
- Energy Support
- Stress Relief
- Hangover Relief
- Weight Management
- Men's Health
- Women's Health
- Prenatal
- Hair Skin Nails

**Advisory-only reason:** every value is an FDA-regulated claim. Must not auto-fill. Surface in HTML with explicit callout: "These values are all health claims. Populate only if you have substantiation. Skill recommends these based on the listing's current framing but does NOT add them to the upload file."

---

## special_ingredients — advisory

**Applies to:** supplements, beauty.

Free-text field. Values are specific ingredient callouts like "Kava Root Extract" or "Hyaluronic Acid."

**Advisory-only reason:** claiming a specific ingredient requires actually having that ingredient at a meaningful dose. Skill doesn't have direct access to the ingredient label and shouldn't infer. Surface suggestions in HTML.

---

## seasons — strict

**Applies to:** apparel, home.

**Valid values:**
- Spring
- Summer
- Fall
- Autumn (interchangeable with Fall in Amazon)
- Winter
- All Season

Multiple values can be selected (some templates use comma-separated).

**Strict auto-fill rule:** seasons explicitly named in title or bullets. "Perfect for summer picnics" → `Summer`. Ambiguous cases ("year-round" → `All Season`) are OK.

---

## target_audience_keyword / target_gender — strict (with caveats)

**target_gender valid values:**
- Female
- Male
- Unisex

**target_audience_keyword:** free-text, but Amazon prefers short descriptors: "Adult", "Men", "Women", "Teen", "Child", "Toddler", "Infant".

**Strict auto-fill rule:** must be observable from the listing. "For women" → `Female`. Gender-neutral product → `Unisex` only if explicitly stated; otherwise leave blank.

---

## skin_type — strict

**Applies to:** beauty / skin care.

**Valid values:**
- Normal
- Dry
- Oily
- Combination
- Sensitive
- All Skin Types
- Acne Prone
- Mature

**Strict auto-fill rule:** must be explicitly named in title or bullets. Don't infer from product description alone.

---

## hair_type — strict

**Applies to:** beauty / hair care.

**Valid values:**
- Straight
- Wavy
- Curly
- Coily
- Fine
- Thick
- All Hair Types
- Color Treated
- Damaged

---

## age_range_description — strict

**Applies to:** children, apparel, toys, books.

Free-text but with common values:
- `Newborn` (0–3 months)
- `Infant` (3–12 months)
- `Baby` (0–24 months)
- `Toddler` (2–4 years)
- `Preschool` (3–5 years)
- `Kid` (5–12 years)
- `Teen` (13–17 years)
- `Adult` (18+)

For toys specifically, also provide `minimum_manufacturer_age_in_months` and `maximum_manufacturer_age_in_months` as integers.

**Strict auto-fill rule:** age range must be explicitly stated (e.g., "ages 3-6" in listing). Do not infer age from product type alone — there's legal risk on child safety products.

---

## pet_breed / pet_size / pet_age_range — strict

**Applies to:** pets.

**pet_size valid values:**
- Small
- Medium
- Large
- Extra Large
- Giant

**pet_age_range valid values:**
- Puppy
- Adult
- Senior
- All Life Stages
- Kitten

**pet_breed:** free-text. Only auto-fill if a specific breed is named in the listing (e.g., "for German Shepherds").

---

## connectivity_technology — strict

**Applies to:** electronics.

**Valid values:**
- Bluetooth
- Wi Fi
- USB
- USB C
- HDMI
- Ethernet
- Lightning
- Thunderbolt
- 3 5 mm
- Wireless
- Wired

Can be multiple.

---

## power_source — strict

**Applies to:** electronics, hardgoods.

**Valid values:**
- Battery Powered
- Corded Electric
- Solar Powered
- Rechargeable
- Manual
- Hand Crank

---

## ALWAYS validate before writing

Even when a value is in this reference, validate against the actual template's data-validation dropdown when possible (openpyxl's `data_validation` attribute on the column). Amazon updates picklists periodically and some values in this reference may be outdated.

If validation fails, skip the write and surface in HTML: "Consider adding {field} = {value}. Valid values in your template: {dropdown values}."

## When in doubt, don't write

This reference is NOT exhaustive. When the skill encounters:
- A category-specific attribute not covered here
- A seller-custom category with non-standard picklists
- Any value you're unsure about

Default to NOT writing. Surface as advisory in the HTML. The cost of a missed auto-fill is a manual seller action; the cost of writing a wrong value is rejected upload + lost seller trust.
