---
name: ab-secondary-image-creator
description: Generates Amazon secondary/gallery listing images from a listing-optimizer audit's per-slot image-stack table. Takes three inputs — a Sophie Society Alexa Shopping Tier 2 audit HTML (or equivalent per-ASIN image-stack table), a brand kit (palette + typography), and a product reference (Drive link or URL). Renders one image per recommended secondary slot (typically 2–9, skipping slot 1 the Amazon main) via Higgsfield MCP, packaged as a Sophie-branded HTML with a 3-per-row grid, per-slot post-production notes, identity checklist, and ship order. Main image is out of scope — use amazon-ab-testing-all-in-one for that. Trigger on 'secondary image refresh', 'gallery image refresh', 'generate secondary images', 'A/B secondary images', 'run the secondary creator', 'render the gallery slots', 'build the secondary image stack', 'refresh my gallery from the audit', 'A/B Secondary Image Creator', or any request to turn a listing-optimizer image-stack recommendation into rendered gallery images.
---

# A/B Secondary Image Creator

Turns a listing-optimization audit's per-slot image-stack table into a rendered set of Amazon secondary/gallery images, packaged as a Sophie-Society-branded HTML handoff. Secondaries only — slot 1 (Amazon main image) is intentionally out of scope; that path lives in the parent `amazon-ab-testing-all-in-one` skill.

This skill inherits every hard rule from that parent skill. Restated tersely below, but the reasoning is in `amazon-ab-testing-all-in-one/SKILL.md` — read that first if unsure.

## Portability / who can run this

This skill contains no account-specific data and is safe to share. Anyone you share it with can run it, provided their environment has:

- **A Google Drive (or equivalent file) connector** — used to fetch the product reference image. Referred to below by function (`search_files`, `download_file_content`), NOT by a fixed server ID. Connector instance IDs are unique per user, so resolve the Drive tools at runtime by their name/function rather than copying any hash from this document.
- **A Higgsfield connector** (paid image generation) — used for `media_import_url`, `generate_image`, `job_display`, etc. Same rule: resolve by function at runtime.
- **The parent skill `amazon-ab-testing-all-in-one`** present in the same skills set — this skill references its hard rules and its main-image path. If you share this skill on its own, share the parent alongside it (or the inherited-rule references won't resolve).

Any `mcp__<hash>__toolname` strings that appear in older copies of this doc are illustrative only. Treat every connector call as "the Drive connector's `search_files`" or "the Higgsfield connector's `generate_image`" — Claude picks the correct connected server at runtime.

## Hard rules (unchanged from parent skill)

- **Rule 0** — Never interact with Seller Central. All Manage Your Experiments and listing edits are the user's manual step.
- **Rule 1** — Never write to Notion without explicit permission.
- **Rule 2** — Drive end-to-end. Ask ONE bundled question turn if inputs missing; then proceed on partial inputs with a flagged caveat rather than iterating field-by-field. If tempted to ask "shall I proceed?" — don't. Proceed.
- **Rule 3** — Always attach the real product reference image (via Higgsfield `media_import_url` from a Drive link or by uploading local bytes). Never generate from text description alone.
- **Rule 4** — Identity guardrails on every render (text fidelity, logo geometry, container silhouette, color hierarchy, element count, quantity/size text). Any single identity fail → re-roll from the original reference.
- **Rule 5** — Research inputs are user-supplied files. Never navigate `amazon.com`. The audit HTML is the only research input this skill needs — Step 1 competitor SERP research from the parent skill is NOT part of this skill's scope (the audit already reflects that analysis).
- **Rule 6** — Each Higgsfield `generate_image` call is a fully independent job. Re-pass the same reference `media_id` on every concept's `medias` array. Never chain a previous job's `job_id` in as reference for a different concept.
- **Rule 7 — Dual mobile + desktop legibility (mandatory on every slot).** The majority of Amazon shoppers view the gallery on a phone, where each secondary renders as a small thumbnail before it's tapped. Every image MUST read clearly at both full desktop size AND at mobile-thumbnail scale. Concretely, on every slot: one core idea per image; on-image copy kept to a short headline plus minimal supporting labels (aim ≤6–8 words for the headline, avoid paragraphs); large, high-contrast type that stays legible when the image is scaled down to ~300px (mobile PDP) and recognizable at ~150px (search thumbnail); the product and any critical text held inside the central ~80% "safe zone" so nothing important is lost to mobile edge-crop; generous negative space, no tiny dense infographics. When the audit's brief for a slot implies a text-dense layout (long ingredient lists, multi-column comparisons), simplify or split for the phone rather than shrinking type. Any slot that fails the mobile-thumbnail read is treated like an identity fail under Rule 4 → re-roll.

## Inputs (three, all required)

1. **Listing optimization audit HTML** — Sophie Society Alexa Shopping Tier 2 audit is the reference format. Any HTML with a per-ASIN "Image stack recommendations" table (`slot | image type | what to show | why`) works.
2. **Brand kit** — image showing the palette hex values and typography. Extract:
   - 3–5 hex colors (background cream, mid tone, deep tone, accent, dark accent)
   - Serif header font (e.g. Playfair Display)
   - Sans body font (e.g. Montserrat)
3. **Product reference image** — Google Drive link (folder or file). Multi-angle best; single works.

## Step 0 — Confirm ASIN, don't ask 4 questions

Read the audit HTML with `Grep` for `<summary>` blocks and `<h4>Image stack recommendations` — the audit contains one image-stack table per ASIN. If there are multiple ASINs, ask ONE question (via `AskUserQuestion`) with each ASIN as an option. Skip the ask if there's only one.

**Do NOT ask** about image type (this skill is secondaries only) or count (audit's table defines the count) or brand context (extract from brand kit image + audit).

## Step 1 — Parse the audit's image stack table

Use `Grep` on the audit HTML:

```
pattern: <h4>Image stack recommendations
output_mode: content
-C: 40
```

The relevant HTML looks like:

```html
<h4>Image stack recommendations (currently 6 images, target 8 to 9)</h4>
<table>
<thead><tr><th>Slot</th><th>Image type</th><th>What to show</th><th>Why</th></tr></thead>
<tbody>
<tr><td>1 (Main)</td>...</tr>
<tr><td>2</td><td>Ingredients infographic</td><td>...</td><td>...</td></tr>
<tr><td>3</td><td>Use case grid</td>...</tr>
...
</tbody>
</table>
```

**Extract each row's `slot`, `type`, `what to show`, `why`.** Skip slot 1 (main image is out of scope). Keep every other slot (typically 2–9).

**Also grep for supporting audit context** the prompts will need to inject:
- Category positioning (price vs median, review count vs median)
- Top positive/negative review themes
- SQP top competitor keywords

These enrich the per-slot prompt bodies with data-anchored language.

## Step 2 — Ingest the brand kit and product reference in parallel

**Brand kit** — user uploads an image. Read it with the `Read` tool and visually extract:
- 3–5 hex palette values (typically shown as swatches with hex codes underneath)
- Header font name
- Body font name
- Any specific brand voice cues (moodboard imagery, e.g. "warm neutrals + botanicals" vs "matte black + gold + honeycomb")

**Product reference** — user pastes a Drive link. If it's a folder, use the Drive connector's `search_files` with `parentId = '<folder_id>' and mimeType contains 'image/'` to list contents. Download the specific product image via the Drive connector's `download_file_content`, decode base64 from the saved tool-result file, save the bytes to `/sessions/*/mnt/outputs/product_ref.png`. (Resolve the Drive tools by function at runtime — do not hardcode a connector hash; it differs per user, per the "Portability / who can run this" note above.)

**Then import into Higgsfield via the Higgsfield connector's `media_import_url`** with the Drive `lh3.googleusercontent.com/d/<FILE_ID>=s3000` URL. This is server-side fetch — bypasses sandbox network restrictions on `upload.higgsfield.ai` PUT. Alternative: local-bytes upload via `media_upload` + PUT + `media_confirm`, but that PUT is often firewall-blocked in Cowork sandboxes. `media_import_url` is the reliable path.

Hold the returned `media_id` — reuse it on EVERY concept's `medias` array.

## Step 3 — Model selection per slot

Map each parsed audit slot to a Higgsfield model:

- **Photographic slots** (use case grid, texture/absorption, sourcing story, before/after, lifestyle) → `marketing_studio_image`
- **Infographic and comparison slots** (ingredients infographic, comparison chart, tube-vs-jar, us-vs-them, routine card) → `nano_banana_2` (which may silently coerce to `nano_banana_flash` in the workspace — that's a workspace-availability thing, not a prompt issue; flag it in the deliverable's caveat block)

## Step 4 — Prompt structure per slot

Every slot's prompt string is built from six blocks concatenated as prose (Higgsfield takes a single `prompt` string):

### Block 1 — Slot heading + verbatim audit brief

Quote the audit's `What to show` and `Why` columns verbatim into the prompt as an "Audit brief for this slot (verbatim):" preamble. This anchors the model to the audit's exact language and makes drift diagnosable.

### Block 2 — PRODUCT block (paranoid reference-lock)

Describe the product tube/bottle/jar/box in tight forensic detail — every label zone, every on-pack text string character-exact, every color and small graphic element. This is the "paranoid PRODUCT block" pattern from the parent skill's single-reference case.

### Block 3 — REFERENCE LOCK

> *Treat the reference image as source of truth for silhouette, proportions, label layout, colors, logo placement, cap shape, on-pack typography. Replicate exactly — only camera angle, lighting, and composition may differ.*

For comparison graphics (us-vs-them), scope the reference-lock explicitly to only the user's product side; the invented right-side generic product is built from scratch.

### Block 4 — BRAND PALETTE (hex values, hard constraint)

Pass the extracted brand kit hex values as an explicit palette constraint:

> *BRAND PALETTE (use these hex values exactly): background <hex>. Dark accents <hex>. Warm tan <hex>. Mid brown <hex>. Deep brown <hex>. Do not introduce any color outside this palette except <specific exceptions like pearl-white cream, translucent amber-gold jojoba, and the small red diagonal strikethrough lines>.*

For infographic slots, also declare typography explicitly (Playfair Display for serif headers, Montserrat sans for body labels).

### Block 5 — CONCEPT (composition, adapted from audit's "What to show" but rendered as visual layout)

Describe the visual layout in structured prose. Break multi-module images (comparison, before/after, routine card) into explicit LEFT/RIGHT/TOP/BOTTOM bands with hex-specific backgrounds. Name every text element that should appear, its font style, and its color. For photographic slots, describe framing, depth of field, lighting direction, and skin/environment details.

### Block 6 — STRICT (allow-list of text; forbid everything else)

List every text string that may appear character-exact. Explicitly forbid invented brand names, badges, prices, ratings, callouts, or any copy not in the allow-list. For comparison/us-vs-them graphics, forbid real competitor brand names on the invented right-side product — use a generic placeholder like "STANDARD" or "TYPICAL DRUGSTORE MOISTURIZER."

### Block 7 — MOBILE-SAFE (dual desktop + mobile legibility, per Rule 7)

Append a mobile-legibility constraint to every slot's prompt, verbatim or adapted:

> *MOBILE + DESKTOP LEGIBILITY (hard constraint): this image must read clearly both at full size and as a small phone thumbnail. Communicate ONE core idea. Keep on-image copy minimal — a single large headline (≤6–8 words) plus only the essential supporting labels; no paragraphs, no fine print. Use large, bold, high-contrast type that stays legible when the image is scaled to ~300px wide and recognizable at ~150px. Keep the product and all critical text inside the central 80% safe zone, away from the edges. Use generous negative space; do NOT pack the frame with tiny dense text or many small elements.*

For infographic/comparison slots whose audit brief implies dense text (long ingredient lists, multi-column tables), simplify the layout for the phone — fewer rows, bigger labels, or split the idea across the frame — rather than shrinking type to fit. A crowded desktop-only infographic is a Rule 7 failure.

## Step 4 — Fire all slots in parallel, poll, identity check

Fire all N slot generations in a single message (multiple `generate_image` calls). Each call:

```
generate_image({
  params: {
    model: "<marketing_studio_image | nano_banana_2>",
    prompt: "<7-block prose prompt for this slot (Blocks 1–7, incl. MOBILE-SAFE)>",
    medias: [{ value: "<media_id from Step 2>", role: "image" }],
    aspect_ratio: "1:1",
    resolution: "2k"
  }
})
```

Sleep ~40-60s (marketing_studio_image is slower than nano_banana_flash). Then call `job_display({ id: <job_id> })` on each job. Any job showing `status: in_progress` — sleep another 20-30s and re-poll.

For each completed job:
- Pull `results.rawUrl` for the full-res PNG.
- Run the Rule 4 identity checklist mentally. Any identity fail → re-fire from the original `media_id` (not the failed job's id) with a tightened reference-lock block. If a text-heavy slot on `nano_banana_flash` fails identity twice, escalate that one slot to ChatGPT GPT-image-1 (out of skill's automated scope; hand off to user).
- **Run the Rule 7 mobile-thumbnail check.** Shrink the render in your head (or view it small) to ~150px: is the core idea still obvious and is the headline still readable? Is critical text clear of the edges? If it turns to mush at thumbnail scale or the copy is too small/dense, treat it as a fail → re-fire with a tighter MOBILE-SAFE block (bigger headline, fewer words, more negative space), or simplify a dense infographic slot.

## Step 5 — Build the deliverable HTML

Use the template at `assets/deliverable-template.html` in this skill's directory. Substitute:

- **Header meta:** brand name + product name (from audit + brand kit), ASIN, date, slot count, model tally
- **Palette badges:** the extracted brand-kit hex swatches
- **Grid of slot cards:** one card per rendered slot, each with `slot number`, `slot title` (from audit's "Image type"), image, `Slot X · Gallery · <tag>` line, description paragraph with inline italic *Answers:* line (derived from the audit's "Why" column), post-production caveat where relevant
- **Identity checklist** — palette-anchored to the user's product's specific text/logo/color spec, and including the Rule 7 mobile-thumbnail read item (the template ships this item by default)
- **Ship order** — extracted from the audit's "Do these three things next" section + the per-slot Why columns; secondaries only

Layout: 1180px container, 3-column grid at wide viewports (`repeat(3, 1fr)`), collapses to 2 columns at ≤960px and single-column at ≤640px. Full-width text blocks (checklist, ship order, intro) constrained to 900px max-width for readability. Playfair Display + Inter typography.

Save as `<BrandName>_Secondary_Images_<ProductName>_<YYYY-MM-DD>_v2.html` in the user's project folder. Present via `mcp__cowork__present_files`.

## Step 6 — Handoff

Concise summary. State model tally (which slots used marketing_studio_image vs nano_banana_flash), any coercion flags, and any identity concerns. Do NOT ship to Seller Central (Rule 0). Do NOT log to Notion (Rule 1). Point the user to Manage Your Experiments for the main-image test path (out of scope for this skill — parent `amazon-ab-testing-all-in-one` skill handles that).

## What this skill does NOT do

- **Slot 1 main image.** Out of scope by design. If the user needs a main-image A/B test alongside the secondary refresh, run this skill AND the parent `amazon-ab-testing-all-in-one` skill separately.
- **Competitor SERP research.** The audit HTML already reflects that; re-doing it is wasted work. If the user wants fresh competitor research, run the parent skill's Step 1 separately.
- **Concept ideation from scratch.** This skill anchors 1:1 to the audit's per-slot recommendations. If the audit is thin or missing image guidance, run the parent skill first.
- **Seller Central upload or Notion logging.** Both forbidden by the shared hard rules.

## Failure modes and known workarounds

- **Higgsfield PUT firewall.** Cowork's sandbox can't reach `upload.higgsfield.ai`. Always use `media_import_url` with a `lh3.googleusercontent.com/d/<FILE_ID>=s3000` URL, not the local-bytes `media_upload` → PUT path.
- **`nano_banana_2` → `nano_banana_flash` silent coercion.** Workspace-level availability. Flash is weaker on small strikethroughs and dense ingredient lists. Flag it in the deliverable's post-production caveats. If a specific slot won't hold text after one re-roll on flash, escalate that one slot to ChatGPT GPT-image-1 (manual handoff to user).
- **Drive folder search returns too many files.** Filter with `title contains '<product name>'` first, then fall back to inspecting the largest .png files (the numbered listing image slots are usually 001.png–007.png at 5-9 MB each).
- **Audit HTML too long for one Read.** Read line 428 region (or whatever line contains "Image stack recommendations") after grepping for that anchor.

## Reference — parent skill

Full flow lives in `amazon-ab-testing-all-in-one/SKILL.md`. That skill covers the complete A/B testing pipeline (research, ideation, generation, main + secondary). This skill is the trimmed-down variant that assumes ideation is done (audit provides it) and skips main-image generation entirely.
