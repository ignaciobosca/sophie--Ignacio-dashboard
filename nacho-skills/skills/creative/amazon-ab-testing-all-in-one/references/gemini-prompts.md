# Gemini Image Generation Prompts for Amazon A/B Testing

Ready-to-use prompt templates for generating product listing images with Google Gemini. Customize the bracketed sections for your specific product.

> **IMPORTANT:** All prompts must comply with the **Strict Rules (1-7)** in the main SKILL.md. Before using any template: verify the product's actual packaging (Rule 1), exact colors (Rule 2), form factor (Rule 3), and unit count (Rule 4). Fill the pre-flight checklist in SKILL.md first. Product must fill maximum space (Rule 5), added elements must connect to the product (Rule 6), and every concept must be consistent with previous ones (Rule 7).

---

## Table of Contents

1. [Prompt Engineering Principles for Product Images](#prompt-engineering-principles)
2. [Main Image Templates](#main-image-templates)
3. [Secondary Image Templates](#secondary-image-templates)
4. [Category-Specific Templates](#category-specific-templates)
5. [Refinement & Iteration Prompts](#refinement--iteration-prompts)
6. [Common Pitfalls & Fixes](#common-pitfalls--fixes)

---

## Prompt Engineering Principles

Before using any template, understand these core principles for getting photorealistic product images from Gemini:

### CRITICAL: Always Start Prompts with "Generate an image:"
Gemini sometimes interprets product prompts as questions or business requests instead of image generation tasks. Always begin your prompt with **"Generate an image:"** to force image generation mode. This was discovered when Gemini returned a business analysis instead of a product image.

### DO:
- **Start with "Generate an image:"** — Forces Gemini into image generation mode
- **Specify "product photography"** — This anchors Gemini in realism, not illustration
- **Name the lighting setup** — "soft studio lighting," "rim light," "three-point lighting"
- **Describe the surface/background** — "pure white background," "clean white cyclorama"
- **Include material descriptors** — "matte finish," "glossy plastic," "brushed metal," "soft cotton"
- **Mention camera details** — "shot with a 85mm lens," "macro photography," "shallow depth of field"
- **Describe the angle** — "45-degree angle," "front-facing slightly angled," "bird's eye view"
- **State the mood** — "clean," "premium," "professional," "clinical," "luxurious"
- **List EVERY color explicitly** — If the product comes in 5 colors, name all 5 in the prompt
- **State exact pack count** — "This is a 5-PACK SET" not just "multiple items"
- **Describe what CANNOT change** — Call out branding, logo position, colors as fixed

### DON'T:
- Don't say "AI generated" or "digital art" — this pushes toward stylized output
- Don't use vague terms like "nice" or "good looking" — be specific
- Don't request text on the image — AI-generated text is almost always garbled
- Don't over-complicate — one clear product shot with specific lighting beats a complex scene
- Don't assume Gemini remembers product details — re-state colors, pack count, and branding in EVERY prompt
- Don't skip the "Generate an image:" prefix — Gemini may misinterpret your intent
- **Don't let Gemini add text that isn't on the physical product** — no callout boxes, no benefit labels, no feature text. Explicitly add to EVERY prompt: "No added text, no callout boxes, no benefit labels — only text that exists on the actual physical product packaging." Gemini loves to add helpful-looking text boxes. They are prohibited on Amazon main images and look unprofessional.

---

## Main Image Templates

### Template 1: Premium Product Shot (White Background)
Best for: Supplements, beauty, health, home products — any Amazon main image

```
Professional product photography of a [PRODUCT NAME/DESCRIPTION] on a pure white
background. The [PRODUCT MATERIAL — e.g., "matte black bottle with gold label"] is
photographed at a [ANGLE — e.g., "slight 30-degree angle"] to show dimension.

Lighting: Soft studio lighting with subtle rim light on the [left/right] edge creating
a gentle highlight that gives the product a premium, three-dimensional look. A very
soft, barely visible shadow beneath the product grounds it naturally.

The image is sharp, clean, and photorealistic — resembling a high-end Amazon product
listing. Shot with an 85mm lens, shallow depth of field. The product fills
approximately 85% of the frame. No text, no graphics, no props — just the product.

Style: Commercial product photography, e-commerce, premium, clean.
```

### Template 2: Product + Packaging Combo
Best for: Products that ship in branded boxes — proven effective for supplements, mattress protectors, home goods

```
Professional product photography on a pure white background showing [PRODUCT NAME]
next to its branded packaging box. The [PRODUCT] is positioned in front and slightly
to the [left/right] of the box, which is angled at 45 degrees to show both the front
and side panels.

The product is the hero — it's larger and more prominent than the box. The box adds
context and brand presence without dominating.

Lighting: Clean, soft studio lighting. Subtle highlights on the product surface
suggesting premium quality. The shadow is very soft and barely noticeable.

Photorealistic, commercial product photography style. No text overlays.
Clean, professional, Amazon-ready.
```

### Template 3: Product with Ingredient/Context Element
Best for: Supplements (show the key ingredient), food products, flavored products

```
Professional product photography on a pure white background. In the center, a
[PRODUCT DESCRIPTION — e.g., "sleek black supplement bottle"]. Arranged artfully
nearby: [CONTEXT ELEMENTS — e.g., "fresh turmeric roots and a small pile of golden
turmeric powder"].

The product is the clear focal point, filling the majority of the frame. The natural
ingredients are smaller and positioned as accents — they communicate the key
ingredient without overwhelming the composition.

Style: Premium commercial photography with natural elements. Soft, warm studio
lighting. The ingredients look fresh and vibrant. Photorealistic, no text,
Amazon main image compliant.
```

### Template 4: Product Showing Scale/Size
Best for: Products where size matters — mattress protectors, blankets, storage containers, furniture items

```
Professional product photography of a [PRODUCT] on a pure white background. The
product is shown [HOW — e.g., "neatly folded to show thickness and texture" /
"slightly unfolded to reveal the interior lining"].

[SIZE INDICATOR — e.g., "A subtle size reference shows this is a Queen-size product"
or "The proportions clearly suggest a large, substantial product"].

Clean studio lighting, sharp details, photorealistic. The fabric/material texture
is clearly visible — you can almost feel the [TEXTURE — e.g., "soft, plush
cotton surface"]. Minimal shadow, white background, premium quality.
```

### Template 4B: Multi-Pack — Color Fan / Cascade
Best for: Multi-packs with different colors/variants (moving bags, storage containers, organizers, towels)

```
Generate an image: [BRAND] - A/B Experiment [LETTER]. Based on the attached product
image, create a professional product photography shot. This is a [BRAND] [PRODUCT NAME]
[PACK COUNT]-PACK SET in [COUNT] DIFFERENT COLORS: [LIST EVERY COLOR]. Each [item]
has [KEY DETAILS — logo, lid, handles, etc.].

CONCEPT: Color Fan/Cascade arrangement. Show ALL [COUNT] [items] fanned out at dynamic
angles, with the [HERO COLOR] as the hero in front (largest, most prominent). The other
[COUNT-1] [items] ([LIST REMAINING COLORS]) fan out behind at staggered angles, each
color clearly visible and distinct. The arrangement should look dynamic and premium —
NOT a flat grid. Each [item] shows its unique color and [BRANDING]. The material should
look [MATERIAL DESCRIPTION].

Pure white background (RGB 255,255,255). Product group fills 85% of the frame. Soft
studio lighting with subtle rim light. Very soft shadow. Photorealistic commercial
product photography, Amazon main image style.
```

### Template 4C: Multi-Pack — Hero + Color Lineup
Best for: When you want premium single-item impact PLUS full color range visible

```
Generate an image: [BRAND] - A/B Experiment [LETTER]. Based on the attached product
image, create a professional product photography shot. This is a [BRAND] [PRODUCT NAME]
[PACK COUNT]-PACK SET in [COUNT] DIFFERENT COLORS: [LIST EVERY COLOR]. Each [item]
has [KEY DETAILS].

CONCEPT: Hero + Color Lineup. The [HERO COLOR] is the HERO — large, prominent, filling
about 50% of the frame, angled at 30 degrees for a premium 3D look. Behind or below
the hero, the other [COUNT-1] [items] ([LIST REMAINING COLORS]) are arranged in a
neat, evenly-spaced row, smaller but each clearly showing its unique color and
[BRANDING]. The hero shows material texture, [DETAILS] in detail. All [items] show
[CONSISTENT DETAILS — e.g., white lid, logo].

Pure white background (RGB 255,255,255). Soft studio lighting with rim highlights on
the hero. Very soft shadow. Photorealistic commercial product photography, Amazon main
image style.
```

### Template 4D: Multi-Pack — Stacked Tower
Best for: Compact vertical arrangement, works when competitors show flat grids

```
Generate an image: [BRAND] - A/B Experiment [LETTER]. Based on the attached product
image, create a professional product photography shot. This is a [BRAND] [PRODUCT NAME]
[PACK COUNT]-PACK SET in [COUNT] DIFFERENT COLORS: [LIST EVERY COLOR]. Each [item]
has [KEY DETAILS].

CONCEPT: Stacked Tower. Show ALL [COUNT] [items] stacked on top of each other in a
neat vertical tower. Each [item] is a different color, creating a visually striking
color progression from bottom to top. The stack should be slightly angled (about 15-20
degrees) to show dimension and [BRANDING] on each [item]. Each color is clearly
distinct. The material should look [MATERIAL DESCRIPTION].

Pure white background (RGB 255,255,255). Product tower fills 85% of the frame
vertically. Soft studio lighting. Very soft shadow. Photorealistic commercial product
photography, Amazon main image style.
```

### Template 4E: Multi-Pack — Product in Context + Color Lineup
Best for: Showing the product in use while still displaying all color variants

```
Generate an image: [BRAND] - A/B Experiment [LETTER]. Based on the attached product
image, create a professional product photography shot. This is a [BRAND] [PRODUCT NAME]
[PACK COUNT]-PACK SET in [COUNT] DIFFERENT COLORS: [LIST EVERY COLOR]. Each [item]
has [KEY DETAILS].

CONCEPT: Packed Hero + Color Lineup. The hero [item] ([HERO COLOR]) is in the
foreground, [CONTEXT — e.g., "partially open with the lid slightly ajar, revealing
neatly folded clothes/blankets/towels packed inside in neutral tones"]. This shows
the product in use. Behind the hero, the other [COUNT-1] [items] ([REMAINING COLORS])
are closed and arranged in a neat row, each clearly showing its unique color. The hero
fills about 50% of the frame. All [items] show [BRANDING].

Pure white background (RGB 255,255,255). Soft studio lighting. Very soft shadow.
The [context elements] add context showing what the [item] is for, while the color
lineup communicates the full [COUNT]-pack variety. Photorealistic commercial product
photography, Amazon main image style.
```

---

## Secondary Image Templates

Secondary images have more creative freedom — no white background requirement.

### Template 5: Lifestyle / In-Use Shot
Best for: Any product — shows the product being used in its natural environment

```
Lifestyle product photography showing [PRODUCT] being used in a [SETTING — e.g.,
"modern, bright bedroom" / "clean, minimalist kitchen" / "cozy living room"].

[SCENE DESCRIPTION — e.g., "A person is placing the mattress protector on a
king-size bed. The room is bright with natural light coming from a large window.
The bedding is neutral-toned (white/gray) and the overall feel is clean and
aspirational."]

The product is clearly visible and in focus. The setting enhances the product's
appeal without distracting from it.

Photography style: Editorial lifestyle, warm natural lighting, slightly shallow
depth of field. Looks like a page from a home decor magazine. Photorealistic.
```

### Template 6: Before/After or Comparison Shot
Best for: Cleaning products, beauty products, organizational products

```
Split-screen product photography showing a clear before and after.

Left side: [BEFORE STATE — e.g., "A stained, messy mattress surface with visible
marks and discoloration"].

Right side: [AFTER STATE — e.g., "The same mattress with a pristine white
mattress protector, looking fresh, clean, and protected"].

The [PRODUCT] is visible in the center/transition area between the two sides.
Clean, well-lit photography. The contrast between before and after is dramatic
but realistic. No text or graphics.
```

### Template 7: Feature Detail / Zoom Shot
Best for: Products with texture, material quality, fine craftsmanship

```
Extreme close-up macro photography of [PRODUCT DETAIL — e.g., "the waterproof
membrane layer of a mattress protector" / "the precision-cut blade of a glass
foot file" / "the tightly woven fabric of a Swedish dishcloth"].

The detail fills the entire frame, showing [WHAT TO HIGHLIGHT — e.g., "the
tightly knit fiber structure that creates the waterproof barrier"].

Shot with a macro lens, very shallow depth of field. Professional studio
lighting reveals every texture detail. Photorealistic, clinical precision.
```

---

## Category-Specific Templates

### Supplements & Health Products

```
Premium product photography of a [COLOR/MATERIAL] supplement bottle with
[LABEL DESCRIPTION] on a pure white background. The bottle cap is [on/slightly
off to show pills inside]. [NUMBER] [COLOR] capsules/tablets are artfully
scattered in front of the bottle.

The bottle has a premium, almost pharmaceutical-grade look with clean highlights
running along its surface. Shot from a slight low angle to make the product
feel substantial and trustworthy.

Lighting: Professional studio, three-point lighting setup. Subtle warm tones.
The label is crisp and readable. Photorealistic commercial photography.
```

### Pet Products

```
Professional product photography of [PET PRODUCT] on a pure white background
with a [BREED — "Golden Retriever" or "French Bulldog"] interacting with it.

The dog is [ACTION — e.g., "lying on the pet bed looking comfortable and content" /
"sitting next to the product looking at the camera"]. The dog is clearly visible
and not hidden behind the product.

The product is the primary focus, with the dog adding warmth and context.
Clean studio lighting, photorealistic, sharp details on both the product
and the dog. Warm, inviting mood.
```

### Food Containers & Kitchen Products

```
Professional product photography of [CONTAINER/KITCHEN PRODUCT DESCRIPTION] on
a pure white background. [ARRANGEMENT — e.g., "Three containers are stacked
with a slight offset, showing different sizes. The front container is open,
revealing fresh, colorful food inside (sliced strawberries and blueberries)."]

The containers look practical yet premium. The food inside is fresh, vibrant,
and appetizing. Clean studio lighting with a focus on the product's functionality
and quality. Photorealistic, no text.
```

### Beauty & Skincare

```
Luxury product photography of [PRODUCT — e.g., "a glass bottle of facial serum
with a gold dropper cap"] on a pure white background. The dropper is positioned
on the [left] side of the bottle.

A single drop of [COLOR — "golden" / "clear"] serum is visible at the tip of
the dropper, catching the light. The glass bottle shows [COLOR] liquid inside
with beautiful light refraction.

Lighting: Glamorous studio lighting with a soft spotlight creating an elegant
highlight on the glass surface. Subtle reflection on the surface beneath.
Ultra-premium, editorial beauty photography. Photorealistic.
```

---

## Refinement & Iteration Prompts

After generating an initial image, use these follow-up prompts to refine:

### Make It More Premium
```
Take this product image and enhance the premium quality. Add more refined
lighting with subtle rim highlights along the product edges. Make the surface
reflections more sophisticated. The overall feel should be luxury e-commerce —
like something you'd see on a high-end brand's Amazon listing. Keep the
white background.
```

### Simplify / Declutter
```
Simplify this product image. Remove [SPECIFIC ELEMENTS]. Keep only the core
product and [ONE KEY ELEMENT]. Increase the white space around the product.
The result should feel clean, minimal, and premium — not busy or crowded.
```

### Fix the Shadow
```
Adjust the shadow in this product image. Make it extremely soft and diffused —
barely visible, just enough to ground the product on the surface. There should
be no visible shadow edge or line. The shadow should feel natural and subtle,
like soft ambient light in a professional photography studio.
```

### Zoom In / Fill the Frame
```
Crop and recompose this product image so the product fills approximately 85-90%
of the frame. The product should feel substantial and be the clear focal point.
Maintain the white background and studio lighting quality.
```

### Add a Detail Inset
```
Add a circular zoom-in detail shot in the [lower-right / upper-right] corner
of this product image. The circle should show [SPECIFIC DETAIL — e.g., "the
fabric weave texture" / "the precision blade edge"]. Give the circle a thin
[COLOR] border. The inset should be about 25% of the total image size.
```

---

## Common Pitfalls & Fixes

### Problem: AI-Generated Text Looks Garbled
**Fix:** Never ask Gemini to generate text on labels or packaging. Instead, generate the product without text and add label text in post-production (Photoshop, Canva).

### Problem: Product Looks Flat / 2D
**Fix:** Add these to your prompt: "three-dimensional look," "subtle rim lighting on edges," "visible surface texture and material properties," "shot with depth — not a flat scan."

### Problem: Unrealistic Proportions
**Fix:** Specify exact proportions or reference real objects: "standard 8oz bottle size," "king-size mattress protector shown folded to approximately 12x12 inches."

### Problem: Background Isn't Pure White
**Fix:** Emphasize in the prompt: "pure white background, RGB 255,255,255, no gradient, no texture, no shadows on the background — only beneath the product."

### Problem: Product Looks AI-Generated (Uncanny Valley)
**Fix:** Add: "photorealistic, indistinguishable from a real product photograph taken in a professional studio. Natural imperfections in lighting. Real-world material properties."

### Problem: Too Many Elements Competing
**Fix:** Follow the rule of three: product + ONE context element + ONE accent. No more. Prompt: "minimalist composition, the product is the hero, all other elements are supporting actors."

### Problem: Amazon Compliance Risk
**Fix for main images:** Always include: "pure white background, no text overlays, no graphics, no watermarks, no badges, no lifestyle elements — Amazon main image compliant."

---

## Gemini-Specific Failure Patterns (Learned from Real Sessions)

These are failure modes specific to how Gemini behaves, not general AI image issues.

### Problem: Gemini Interprets Prompt as a Question Instead of Generating an Image
**What happens:** You send a detailed product prompt and Gemini responds with text analysis, business advice, or a description instead of generating an image.
**Why:** Gemini sometimes defaults to text mode, especially if the prompt reads like a description or if there's unrelated context in the chat.
**Fix:** ALWAYS start your prompt with "Generate an image:" — this forces image generation mode. If it still fails, start a new chat.

### Problem: Context Corruption — Unrelated Content Mixes In
**What happens:** Gemini's output references people, topics, or content that have nothing to do with the product (e.g., a business contact's name appearing in an image generation response).
**Why:** Gemini's context can bleed between conversations, especially when using the workspace/organization account. Previous chats or documents in Google Workspace may influence the output.
**Fix:** Start a completely new Gemini chat. Do NOT try to continue — the context is corrupted. In the new chat: paste a fresh product image, write a clean prompt with "Generate an image:" prefix.

### Problem: Clipboard Not Working — "Document is not focused" Error
**What happens:** When running the JavaScript to copy an Amazon image to clipboard, you get `NotAllowedError: Failed to execute 'write' on 'Clipboard': Document is not focused`.
**Why:** The browser tab with the image must be actively focused for clipboard access. If you're switching between tabs programmatically, the focus can be lost.
**Fix:** Click anywhere on the image tab page first to focus it, then re-run the JavaScript clipboard command.

### Problem: Clipboard Gets Overwritten Between Tabs
**What happens:** You copy the product image to clipboard, switch to Gemini, but what you paste is not the image (or nothing pastes).
**Why:** Other browser actions between the copy and paste can overwrite the clipboard.
**Fix:** Copy the image → immediately switch to Gemini → immediately paste (Ctrl+V). Do not do anything else between these steps. If it doesn't work, go back to the image tab, re-focus, re-copy, and try again.

### Problem: Product Form Factor Drifts Across Iterations
**What happens:** First generation looks correct, but after refinement prompts, the product shape gradually changes — bags become boxes, bottles get taller, handles disappear.
**Why:** Gemini's image model doesn't have strong object permanence across iterations. Each generation is semi-independent.
**Fix:** If the form factor drifts, apply SKILL Rule 4 (new chat with last good image). In the new prompt, be extra explicit about the form factor: "This is a rectangular bag with..." not just "this product."

### Problem: Color Count Wrong in Multi-Pack
**What happens:** You ask for 5 colors but Gemini generates 3, 4, or 6 items.
**Why:** Gemini doesn't reliably count. It's a known limitation.
**Fix:** Be extremely explicit: "Show EXACTLY 5 bags: 1 Black, 1 Gray, 1 Navy Blue, 1 Khaki/Olive Green, 1 Burgundy/Red. No more, no less." List each color individually rather than saying "5 different colors." If still wrong, new chat.

### Problem: Gemini Defaults to "Fast" Model
**What happens:** Image quality is noticeably lower — less photorealistic, more illustrated look.
**Why:** Every new Gemini chat defaults to the Fast model. Pro must be manually selected.
**Fix:** Before sending any prompt, look at the bottom of the chat input area. Click the model selector and switch to "Pro." Do this for EVERY new chat — it never remembers.

---

## Quick-Start Workflow

1. Pick the template closest to your product category
2. Fill in the bracketed sections with your specific product details
3. Generate in Gemini
4. If the result isn't right, use the refinement prompts above
5. Check against Amazon compliance (especially for main images)
6. Share in #team-ab-testing-lab for team feedback before launching the A/B test
7. Add proper label text/branding in post-production (Canva / Photoshop)
8. Launch the test and track CTR, CVR, and TACOS
