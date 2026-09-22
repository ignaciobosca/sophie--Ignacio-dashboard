# Hero Image — Dimensions & Resolution

Exact specs quoted from the upstream image skill (`amazon-ab-testing-all-in-one`,
`step-3-chatgpt.md` "Output Resolution"). No numbers are invented.

## Target spec

- **Aspect ratio:** square **1:1**.
- **Amazon minimum:** 1000px on the longest side.
- **Amazon recommended (zoom):** **2000×2000** — required to enable hover-zoom.
- **Colour space:** sRGB.
- **File formats accepted:** JPEG, PNG, or TIFF.
- **Text legibility:** any text physically on the product must be legible at
  **375px wide** (mobile thumbnail scale).

## Generator resolution reality

- **GPT-image-1** emits only three native sizes: **1024×1024 (1:1)**,
  1024×1536 (2:3 portrait), 1536×1024 (3:2 landscape). Asking for an arbitrary
  "2000×2000" does nothing — output always lands on one of these three.
  Resolution stated in a JSON prompt is flavour text only.
  → **Must UPSCALE** to ≥2000px (Topaz Gigapixel, Photoshop Preserve Details
  2.0, or Let's Enhance) to hit Amazon's recommended 2000px zoom size.
- **Higgsfield** uses an `aspect_ratio` param (`"1:1"` for hero).
  **`nano_banana_2` reaches 4K** — no separate upscale needed for it.
  `marketing_studio_image` (default) may still need an upscale to reach 2000px.

## Post-generation QA gate (run in Step 4)

Every hero variant must pass all gates before it is written to output. Any fail
→ regenerate or fix, then re-check.

- [ ] **Background = pure white.** Sample background pixels = RGB 255,255,255.
      Snap off-white (~250) to pure white in post if needed.
- [ ] **No added text detected.** Only on-product markings present; no overlay
      text, badges, watermarks, or graphics.
- [ ] **Unit count correct.** Exactly N physical units visible (N = `product_facts.pack_count`).
- [ ] **Identity matches reference.** Colour, form factor, on-pack text, logo
      placement consistent with `product-reference/`.
- [ ] **Resolution.** Longest side ≥ **2000px**; aspect ratio 1:1; sRGB.
- [ ] **Thumbnail legibility.** Product clearly identifiable and any "N Pack"
      text legible at ~375px wide.
