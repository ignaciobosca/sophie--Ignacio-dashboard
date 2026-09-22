# Flat File — Column Map, Template Variants, Error Interpretation

Everything seller-facing for Mode 2's Category Listings Report. The heavy lifting
(validation, parsing, strict/advisory classification, byte-safe truncation, verification) is
done by `scripts/parse_inputs.py` and `scripts/write_flat_file.py`. This reference exists
so Claude can (a) explain script errors back to the seller, (b) debug unexpected templates,
(c) pick the right column pattern when proposing structured fills.

---

## Template structure — row 4 vs row 5

Amazon has shipped at least two layouts for the Category Listings Report:

- **Older (pre-2025):** row 4 = attribute IDs (`item_name[...]`, `::record_action`), row 5 = human-readable labels, data starts row 7.
- **Newer (2025+):** row 4 = human labels, **row 5 = attribute IDs**, data starts row 7.

Attribute IDs are stable; labels change. The scripts scan for the row containing
`::record_action` and use `attr_row + 2` as the data start — they work against both variants
without edits. If Amazon ships a new layout that shifts these rows, the script's "No template
sheet found" error is the signal.

---

## Column map

Every column is resolved by substring match against the attribute ID row. Patterns:

### Required (all categories)

| Purpose | Pattern | Notes |
|---|---|---|
| Record action | `::record_action` | Writer sets to `PartialUpdate` on every row it touches |
| Title | `item_name[` | Trailing `[` disambiguates from `item_name_keyword` etc. |
| Bullet N (1-5) | `bullet_point[` AND `]#{N}` | |
| Description | `product_description[` | |
| Backend | `generic_keyword[` | 250-byte cap, space-separated, UTF-8 bytes not chars |
| SKU | `contribution_sku` | Row identity |
| ASIN | `amzn1.volt.ca.product_id_value` or `external_product_id` | Template-dependent |
| Product type | `product_type` | Drives category family detection |
| Brand | `brand[` or `brand_name` | Used to exclude own brand from competitor set |
| Main image | `main_product_image_locator` or `main_image_url` | |
| Other images | `other_product_image_locator_1` … `_8` | Counted into `image_count` |

### Category-specific (strict vs advisory tiers in `category-families.md`)

- **Jewelry:** `gem_type`, `metal_type`, `metal_stamp`, `chain_type`, `setting_type`, `stone_shape`, `target_gender`, `occasion`, `theme`, `pendant_description`, `color`
- **Supplements/consumables:** `diet_type`, `dosage_form`, `item_form`, `flavor`, `container_type`. Advisory-only: `recommended_uses_for_product`, `special_ingredients`
- **Beauty:** `skin_type`, `hair_type`, `material_feature`
- **Apparel:** `size_name`, `color_name`, `style_name`, `material_type`, `care_instructions`, `seasons`, `target_gender`, `age_range_description`
- **Hardgoods:** `material_type`, `room_type`, `mounting_type`, `power_source`, `color_name`, `size_name`
- **Electronics:** `compatible_devices`, `connectivity_technology`, `power_source`
- **Pets:** `pet_breed`, `pet_size`, `pet_age_range`, `flavor`, `material_type`
- **Children:** `age_range_description`, `minimum_manufacturer_age_in_months`, `maximum_manufacturer_age_in_months`, `educational_objective`

### Anchored match for structured fills

`write_flat_file.py::find_structured_col` anchors the pattern to a word boundary (`[`, `#`,
or end-of-string) so `diet_type` can't silently write to `diet_type_keyword`. When proposing
a strict-tier structured fill, pass the bare attribute ID (e.g. `diet_type`, `chain_type`),
not a partial substring.

---

## Interpreting script errors

| Script message | What it means | What to tell the seller |
|---|---|---|
| `Required columns missing: [...]` | Template was modified or wrong category | Re-download the Category Listings Report from Seller Central without modifying headers |
| `No template sheet found` | Sheet name unrecognized AND no row contains `::record_action` | Not the right file type; likely Inventory Report or a pivot export. Re-download the Listing template. |
| `WARNING: ...marketplace...` (in warnings, not errors) | `marketplace_id` was unrecognized or missing | Not a blocker. The skill supports US, UK/EU, and other marketplaces. Confirm the marketplace with the seller and re-check US-based regulatory/claims examples against the local rules. |
| `Target ASIN X not found in flat file` | `--asin` filter matched zero rows | ASIN is mistyped or not in this report. Omit `--asin` to audit the full portfolio. |
| `SQP schema mismatch — missing columns` | SQP CSV shape doesn't match the expected two-level header | Re-download SQP from Seller Central → Brand Analytics → Search Query Performance (not a custom pivot). |

---

## Writer behavior (what `write_flat_file.py` guarantees)

- Every written row gets `::record_action = PartialUpdate` — **blank cells are preserved**, not blanked out.
- Only fields with `passed_gate: true` in the rewrites JSON are written. Failed-gate fields stay blank, so PartialUpdate keeps the seller's existing value.
- Strict-tier structured fills only write when the current cell is **empty** — explicit seller data is never overwritten.
- Advisory-tier fills must NOT be in the rewrites JSON. They surface in the HTML only.
- Forbidden columns: `feed_product_type`, `::last_modified`, `child_parent_sku_relationship`, `parentage_level`. The writer refuses to touch them.
- Length caps enforced on write: title 200 chars, each bullet 500 chars, backend 250 UTF-8 bytes (word-boundary truncation with a warning in the summary).
- After save, the writer re-opens the xlsx and asserts every audited row has `::record_action == 'PartialUpdate'`. Failure exits non-zero.

### Picklist validation

For controlled-vocabulary attributes (`occasion`, `chain_type`, `setting_type`, etc.), check
`amazon-picklist-values.md` before including in `strict_structured_fills`. Invalid picklist
values are silently rejected by Amazon at upload — surface them in the HTML advisory block
instead, with the list of valid values.

---

## Output naming convention

```
Category_Listings_Report_[Brand]_Tier2_Updated_YYYY-MM-DD.xlsx
```

`[Brand]` = the most common value in the `brand` column across audited rows. If mixed or
unclear, use `Portfolio`.
