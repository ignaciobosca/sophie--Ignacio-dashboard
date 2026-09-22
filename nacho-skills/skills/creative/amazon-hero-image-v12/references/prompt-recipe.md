# Hero Prompt Recipe — the Four Mandatory Blocks

Adapted from the upstream image skill's four-block recipe, but **populated from
the building-block inputs** (the V7 `product_facts` JSON + `product-reference/`)
instead of spoken guesses. Assemble all four blocks into one prose `prompt`
string per concept. The hero is **always** the strict white-background type, so
Block 3 is fixed.

## The four blocks

1. **Preserve on-pack text verbatim.** "Preserve every existing text, logo,
   icon, and graphic exactly as it appears on the product/packaging. Do not
   invent, translate, paraphrase, or re-case any copy." → `product_facts.
   on_pack_text` is **always null**, so source the exact on-pack text by
   **vision-reading the `product-reference/` images** (Step 0). That vision read
   is the source of truth — never take on-pack text from the listing/audit, and
   never invent text.

2. **Exactly N units.** N = `product_facts.pack_count` (an int; if a
   `pack_count_conflict` was present, V7 already resolved it and `pack_count` is
   the resolved value — Rule 5). "Show exactly N units, arranged so all N are
   clearly countable." A 2-pack shows 2; a single SKU shows 1.

3. **Text & background rail — strict white-bg (fixed for hero).** "Pure white
   background (RGB 255, 255, 255), no gradient, no texture, no off-white. No
   added text, callout boxes, benefit labels, badges, stickers, watermarks,
   borders, props, mannequins, or logos beyond what already exists physically on
   the product. Product fills ~85–90% of the frame. Amazon main-image
   compliant." (This rail never relaxes for hero.)

4. **Reference-lock.** "Treat the attached reference image as the absolute
   source of truth for silhouette, proportions, label layout, label colours,
   logo placement, and any cap/lid/clip shape. Only camera angle, lighting,
   shadow, and composition may differ." → Attach the real `product-reference/`
   image(s) on every call. Use `product_facts.colour` (scalar) and
   `product_facts.material` to describe the locked product.
   **MANDATORY — ENUMERATE the transcribed identity.** Do not stop at a generic
   "preserve all text and logos." Spell out, inside this block, the **specific
   features transcribed from the reference** (Step 0c item 4): the exact printed
   text strings verbatim (spelling/casing), each distinct physical component and
   its material/finish (e.g. "polished metal X over a matte foam Y"), and the
   silhouette/form. Generic locks are why fine, distinguishing details drop —
   naming them is what keeps them.
   **MANDATORY — preserve ORIENTATION & proportions.** Reproduce the product in
   the **same orientation, rotation, and proportions as the reference photo**. Do
   **not** rotate, flip, tilt, lay on its side, re-orient, or re-stretch the
   product — e.g. a vertically-hanging pendant stays vertical, a tall bottle stays
   upright, a wide box stays wide. The product's "up" direction and aspect/relative
   proportions must match the reference exactly; only the camera angle/lighting/
   shadow/composition may vary. (This is a non-negotiable part of reference-lock —
   it sits alongside silhouette/label/colour, not below it.)

**Prose skeleton:** `PRODUCT: … REFERENCE LOCK: … CONCEPT: … STYLE: … STRICT: …`

A, B, C are three distinct **angles/compositions** of the same locked product
(e.g. front-on hero, three-quarter, top-down) — identity constant, composition
varied. That is the entire degree of freedom for hero.

> **Apply the canonical best-practices.** When populating the blocks, apply
> `references/main-image-best-practices.md` (composition, background, fill %,
> allowed/forbidden, fidelity). If the product hit a §10 **nuanced-case fork**
> (sold on a printed card/insert, multipack, size/scale cue, apparel flat-lay vs
> on-model, transparent/reflective, or a bundle), the skill has already ASKED the
> user before this step — build all three concepts to the answer they gave, and
> never decide it for them here.

## Populated example — real PBnJ `product_facts` (from the V7 audit)

The actual `product_facts` JSON extracted from the V7 HTML audit's
`<pre class="pf-json">` block for ASIN **B0C5P9TP3Q**:

```json
{
  "asin": "B0C5P9TP3Q",
  "pack_count": 2,
  "colour": "Black",
  "material": "Silicone and metal",
  "on_pack_text": null,
  "on_pack_text_note": "STUB: read from the actual product photo. ... never invent it. Not derivable from listing or report data.",
  "pack_count_conflict": {
    "note": "The Category Listings Report has unit_count=1, but the title and bullets say 2 Pack. Set the detail page Number of Items / unit count to 2 so the page and any future flat file agree.",
    "rationale": "The title is the buyer-facing promise of what ships, and two clips are shown in the images, so 2 is the true pack count.",
    "source": "title (\"2 Pack\") over report unit_count=1"
  }
}
```

Fact-sheet derived from it:
**N = `pack_count` = 2** (the `pack_count_conflict` is already resolved by V7 to
2, source `title ("2 Pack") over report unit_count=1` — echo this to the user,
do not re-pick); **colour = `"Black"`** (scalar, single colour);
**material = `"Silicone and metal"`**; **on_pack_text = null** → vision-read the
on-clip text from `product-reference/` and use that verbatim. The hero must show
**2** clips.

> **PRODUCT:** PBnJ baby Stroller Hooks — **2-pack** (`pack_count: 2`) of
> adjustable carabiner-style stroller clips, **Black** (`colour`), made of
> **silicone and metal** (`material`): a smooth silicone-covered gripping surface
> over a metal clip body.
> **REFERENCE LOCK:** Treat the attached product photo(s) as the absolute source
> of truth for the clip silhouette, the silicone-over-metal surface, the black
> colour, the clasp/gate shape, and any text or logo physically on the clip. Only
> camera angle, lighting, shadow, and composition may differ.
> **CONCEPT (variant A):** Front-on hero shot, both clips standing upright side
> by side, clasps facing the camera, a slight floating drop-shadow for depth.
> **STYLE:** Clean studio product photography, soft even lighting, crisp focus.
> **STRICT:** Pure white background RGB 255,255,255 — no gradient, texture, or
> off-white. Show **exactly 2** clips, both fully visible and countable. No added
> text, badges, callouts, watermarks, props, borders, or graphics beyond markings
> physically on the clips. Preserve all on-clip text/logos **verbatim as
> vision-read from the reference photo** (`on_pack_text` was null in
> `product_facts`). Product fills ~85–90% of the frame. Black stays black;
> silicone-over-metal form unchanged. **Keep the clips in the SAME orientation,
> rotation, and proportions as the reference photo — do not rotate, flip, tilt,
> lay on their side, re-orient, or re-stretch them.** Amazon main-image compliant.

Variant **B**: three-quarter angle, one clip open / one closed to show the gate
action, both still countable. Variant **C**: top-down or close framing
emphasising the silicone grip texture — same two black clips, same rules. The
audit wants "2 Pack" legible at thumbnail: if that text is **physically printed**
on the product/packaging (confirm via the vision read), the reference-lock
carries it; if it is NOT physically on the unit, it cannot be added to the hero
(Rule 3) — flag for a packaging-as-hero variant or a secondary image instead.

## Backend (how prompts are passed)

**Default = Higgsfield via MCP** (the demoed path). One prose `prompt` string per
concept; re-pass the same product reference on every concept (never chain a prior
job as the reference).

```
generate_image({ params: {
  model: "marketing_studio_image",          // default; use "nano_banana_2" for text-heavy / packaging-as-hero (4K, strongest on text)
  prompt: "<the four blocks concatenated into one prose string>",
  medias: [{ value: "<media_id | Amazon CDN URL>", role: "reference" }],
  aspect_ratio: "1:1",
  count: 1
}})
```

- Preferred reference = a reconstructed Amazon CDN URL (skips upload); fallback =
  `media_upload` → PUT bytes → `media_confirm`.
- Poll `job_status({ jobId, sync: true })`; full PNG in `results.rawUrl`.
- Gotcha: `nano_banana_2` silently coerces to `nano_banana_flash` in some
  workspaces — flag to the user if it happens.

**Alternates:** ChatGPT (GPT-image-1) — best identity preservation, but only
native 1024² so must upscale; one image = one fresh chat. Gemini (Pro model;
every prompt must start "Generate an image:"). Same four blocks, same intent —
only the transport differs.
