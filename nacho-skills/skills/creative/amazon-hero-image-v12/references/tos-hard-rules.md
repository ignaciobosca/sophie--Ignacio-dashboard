# Amazon Hero / Primary Image — TOS Hard Rules

> The **canonical** main-image best-practices (composition, background, fill %,
> allowed/forbidden, fidelity, resolution, the four-block recipe, and the
> nuanced-case decision forks) live in `references/main-image-best-practices.md`.
> This file is the focused TOS-rules + pre-flight view; read the canonical file
> for the full set.

These are the formal Amazon main-image requirements the hero MUST satisfy.
Facts are quoted faithfully from the upstream image skill
(`amazon-ab-testing-all-in-one`) and the PBnJ listing audit — no numbers are
invented. The hero is **always** the strict white-background type.

## Hard rules (numbered)

1. **Pure white background — RGB 255, 255, 255.** No gradient, no texture, no
   off-white. (If output lands at ~250 off-white, snap to pure white in post:
   Photoshop Levels, or `magick input.png -level 97%,100% output.png`.)
2. **Product fills ~85–90% of the frame.** Maximum product presence; minimal
   empty margin.
3. **NO added text, logos, badges, watermarks, callout boxes, benefit labels,
   feature text, stickers, graphics, props, mannequins, borders, or
   backgrounds.** The only text/markings allowed are those **physically printed
   on the product or its packaging.** Amazon prohibits added text/graphics on
   main images. (Added text belongs on secondary images, applied in post —
   never here.)
4. **Accurately depict the actual product for sale.** The image must be the real
   product, reference-locked. No imagined products, no stand-ins.
5. **Never alter colour, form factor, packaging, or unit count.** Black stays
   black; a clip stays a clip; a 2-pack shows exactly 2 units. The form factor
   and packaging shown must match what ships.
6. **Show the correct pack count.** A 2-pack must show 2 physical units. If the
   listing markets the pack count in text (e.g. "2 Pack"), that text must be
   **legible at thumbnail size** (the PBnJ audit: main image must read instantly
   at thumbnail — product clearly identifiable and "2 Pack" visible — on a clean
   white background).
7. **No competitor brand names.** Never include another brand's name or logo. In
   any comparison context use "OTHER BRAND" / "STANDARD" — naming competitors is
   a policy + legal risk. (Hero is single-product, so this almost never applies,
   but it is an absolute bar.)

## Pre-flight checklist (run in Step 1, BEFORE writing prompts)

Check each item against the Step-0 product fact-sheet. Resolve or flag any
failure here — not after generation.

- [ ] **The agent has a VIEWABLE copy of the reference and has looked at it**
      (not merely attached it to the generator); identity transcribed from it
      (printed text verbatim, each component + finish, silhouette, count,
      orientation). If not viewable, bring a viewable copy in before proceeding —
      never generate from the typed description alone. (BLOCKING.)
- [ ] **The REFERENCE LOCK block enumerates those specific features**, not a
      generic "preserve all text and logos."
- [ ] Background spec = pure white RGB 255,255,255 (no gradient/texture/off-white).
- [ ] Product fills ~85–90% of the frame.
- [ ] No added text/logos/badges/watermarks/graphics planned beyond on-product markings.
- [ ] No props, mannequins, borders, or background scenery planned.
- [ ] Colour matches `product_facts.colour` exactly (no invented colour).
- [ ] Form factor / packaging matches the real product.
- [ ] **Product orientation & proportions match the reference (not rotated,
      flipped, tilted, laid on its side, re-oriented, or stretched).** The "up"
      direction and relative proportions match the reference photo (a
      vertically-hanging pendant stays vertical, a tall bottle stays upright). A
      first-class check alongside white-bg / count / legibility; if a generated
      version fails it, REGENERATE that version.
- [ ] Pack count N = `product_facts.pack_count` and is unambiguous. If a
      `pack_count_conflict` was present, V7's resolution has been ECHOED to the
      user (chosen N + source) — not re-litigated.
- [ ] The image will show exactly N units.
- [ ] If the listing markets "N Pack" in text, it will be legible at thumbnail (≈375px wide).
- [ ] No competitor brand names anywhere.
- [ ] On-pack text to preserve has been VISION-READ verbatim from
      product-reference (`product_facts.on_pack_text` is null — never use the listing).
