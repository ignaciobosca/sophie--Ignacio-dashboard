# Step 3 — ChatGPT (GPT-image-1) Image Generation

This is the Step 3 operator manual for the ChatGPT branch of the workflow. The parent `SKILL.md` has already established Hard Rules 0–6 (no Seller Central, no Notion writes, no Amazon nav, always attach reference, identity guardrails, one-image-one-chat) — those apply here by default. Don't restate them in your output; just follow them.

This file covers what's specific to ChatGPT: prompt structure, the JSON `master_prompt` for complex compositions, the four mandatory prompt blocks, the paranoid PRODUCT block for single-reference fallback, the 6-graphic-type template library, refinement prompts, common issues, and the operator playbook for driving chatgpt.com in a browser.

---

## Why ChatGPT for this workflow

ChatGPT's image model (GPT-image-1, sometimes branded "DALL-E" in the UI) has three properties that matter for Amazon listings:

1. **Multi-image reference.** Identity preservation improves sharply when the model can triangulate a product from 2–3 reference angles vs. extrapolating from a single front shot. This single change fixes most "label looks weird" / "bottle shape is wrong" problems.
2. **Reliable in-chat refinement for small issues.** Lighting, shadow, angle tweaks usually work in the same chat. (Identity drift still requires a new chat per Rule 6.)
3. **Structured JSON parsing.** GPT-image-1 parses JSON prompts into explicit scene-graph nodes instead of flattening to a prose blob. This makes the JSON `master_prompt` pattern usable for split-screen / Us-vs-Them / multi-module compositions in a way Gemini struggles with.

Trade-off: occasionally less photorealism on edge cases, and the model sometimes routes to a cheaper/faster image variant on free tier. Mitigations below.

---

## Naming Every Chat

Format: **[Brand Name] - A/B Experiment [Round] Concept [Letter]**

Examples:
- `VI PRESTIGE - A/B Experiment 1 Concept A`
- `Mila & Lulu - A/B Experiment 2 Concept D`

Rename the chat in the ChatGPT sidebar immediately after creation (click the chat title → type the new name → Enter). ChatGPT auto-names from the first prompt and those auto-names are useless for tracking rounds.

If the rename field doesn't appear before the first message (it sometimes locks until the first prompt sends), send a placeholder first ("Setting up prompt — please wait."), let ChatGPT name the chat, then rename via the three-dot menu on the sidebar entry.

---

## Model Selection

ChatGPT image generation runs on **GPT-image-1** and is invoked automatically when you ask GPT-5, GPT-4o, or GPT-4.1 to make an image. But:

- **Free tier and some Plus sessions** may silently route to a cheaper image model with worse prompt adherence. If early generations look flat or ignore your "pure white background" instruction, open a fresh chat and explicitly start the prompt with: *"Use GPT-image-1 (the highest-quality image model) to generate:"*
- **Plus / Pro / Team / Enterprise** get higher daily image quotas. If generations start failing with "please try again later" or quality drops mid-session, you've likely hit the image quota. Start a fresh chat after the reset window or switch accounts.
- **Use a single model thread per concept.** Don't switch between GPT-5 and GPT-4o mid-chat — the image-model adapter behavior changes and consistency suffers.

This file covers chatgpt.com specifically. Driving via the OpenAI Platform / API directly is a different flow.

---

## Attaching the Original Product Image(s) — Rule 3 Applied

Hard Rule 3 (parent SKILL.md): always attach the real Amazon product photo(s). ChatGPT accepts vision input directly — no clipboard-canvas hack needed (that's Gemini's pattern).

### Clipboard paste (primary method)

1. Open the Amazon image URL in a browser tab
2. Click the image → Ctrl+C
3. Switch to ChatGPT → new chat → click directly on the "Ask ChatGPT" placeholder text (NOT the wrapper around it)
4. Ctrl+V — thumbnail appears in the composer
5. Type prompt, send

**Agent-operator nuance:** the ChatGPT composer is a contenteditable div inside a wrapper. Clicking the wrapper silently drops the paste. Always aim the click at the visible placeholder text coordinates.

**Fallbacks (in order):** right-click → Copy image; download + drag-drop into the composer; crossOrigin-blob + DataTransfer injection (last resort, for sandboxed agents when the proxy blocks the image CDN).

**Multi-angle reference:** when the listing has multiple images (front, side, back, lifestyle), attach 2–3 of the most informative angles. This is the single biggest identity-preservation win available with ChatGPT.

### Single-Reference Paranoid PRODUCT Block (fallback when only 1 image is available)

When only one reference image is available, the reference-locking block alone isn't enough — ChatGPT has no triangulation data and will silently invent the sides/back. Compensate by writing the PRODUCT block at **paranoid detail level**: spell out every visible label element explicitly, in plain language, as if describing it to someone who can't see the image.

What "paranoid" means in practice:

- Name every zone of the label (top-left, top-right, headline, ingredient callouts, bottom-left banner, bottom-right tagline, etc.) and what's in each zone
- Quote exact on-pack text character-for-character, including weird case/spacing ("G U M M I E S" with spaces, "ONE WORLD, ONE LIST." with the period)
- Name colors by description, not hex ("dark charcoal-gray background", "orange rectangular banner", "gold botanical line-drawing accents")
- Name small graphic elements ("circular badge with herbal sprig illustration", "small blueberry icon inside the orange banner")
- Describe the container: material, transparency, cap shape/color, any visible contents through the glass

This verbose PRODUCT block plus the reference-lock block (rule 4 below) gives belt-and-suspenders detail to hold identity on a single-reference run. When multi-angle reference IS available, write a shorter PRODUCT block (1–2 sentences) and let the reference images carry the detail. Paranoid mode is specifically for the single-image case.

---

## The Four Mandatory Prompt Blocks

Every ChatGPT prompt — regardless of category — must include these four blocks. The fourth (reference-lock) is the single biggest consistency upgrade in this workflow.

### 1. Preserve on-pack text verbatim

> *Preserve every existing text, logo, icon, and graphic on the packaging exactly as it appears in the attached reference. Do not invent, translate, paraphrase, or re-case any copy. The brand name, benefit lines, quantity banner, ingredient list, and all other printed text must match the attached reference character-for-character.*

ChatGPT is noticeably better than Gemini at preserving text, but still not perfect on small-point type — prompt it explicitly.

### 2. One unit only (for single-SKU products)

> *Render ONE (single) [box / bottle / tube / pouch / unit] only. Never show multiples, duplicates, or a row of products. This is a single-unit product, not a multi-pack.*

Skip only if the product is legitimately sold as a multi-pack and that's the visual you want.

### 3. Text & background rail — scoped by graphic type

This rule is **not universal**. Read which graphic type you're generating from the template library below and apply the matching rail.

- **Primary / main image (Concepts A/B/C):** strict rail — *"Pure white background (RGB 255, 255, 255), no gradient, no texture, no subtle off-white. No added text, callout boxes, benefit labels, badges, stickers, watermarks, or logos beyond what already exists on the product itself. Amazon main-image compliant."*
- **Lifestyle (Concepts D/E, or standalone lifestyle shot):** background and context flexible; no overlay text unless the template explicitly asks for it.
- **Features / benefits / comparison / instructional graphics:** overlay text is *required* (that's the point). Each template specifies which labels are allowed. Rail: *"Only the text labels specified in the layout block may appear. No additional overlay text, badges, or watermarks beyond those labels."*

Don't default to the main-image rail for everything — it will fight templates that need text.

### 4. Reference-locking block (the consistency fix)

> *Treat the attached reference image(s) as the absolute source of truth for: overall silhouette, proportions, label layout, label colors, logo placement, cap/lid shape, bottle/box dimensions, and on-pack typography. Do not "improve" or "modernize" any of these — replicate them exactly. Only the camera angle, lighting, and composition may differ from the reference.*

This one paragraph is what separates a 60% identity match from a 95% one. Without it, ChatGPT quietly re-interprets "the vibe" of the product and ships back something 80% right and 20% off. With it, the model is explicitly pinned to the reference for identity and only allowed to improvise on the shot.

---

## Output Resolution

GPT-image-1 supports three native aspect ratios:

- **1024 × 1024** — square, use for Amazon main images (1:1 is the Amazon standard anyway)
- **1024 × 1536** — portrait, use for vertical lifestyle shots, mobile A+ modules
- **1536 × 1024** — landscape, use for hero banners, feature graphics

You specify ratio in natural language ("square 1:1 composition" / "vertical 2:3 portrait" / "horizontal 3:2 landscape"). Asking for arbitrary resolutions like "2000×2000" does nothing — output always lands on one of these three. Plan for a post-generation upscale (Topaz Gigapixel, Photoshop Preserve Details 2.0, Let's Enhance) to hit Amazon's recommended 2000px zoom size.

---

## Standard Prompt Structure (Prose)

Use this for straightforward single-subject shots. For complex multi-module compositions (split-screen, Us vs Them, layered scenes), use the JSON `master_prompt` structure further down.

```
[Brand] - A/B Experiment [Round] Concept [Letter]. Based on the attached product reference(s), create a professional Amazon product photograph of the [PRODUCT NAME].

PRODUCT: [Exact physical description — materials, colors, shape, printed text/logo/icons, all visible packaging elements]. Preserve every existing text and graphic on the packaging exactly — do not invent, translate, paraphrase, or re-case any copy. Render ONE (single) unit only; never show multiples.

REFERENCE LOCK: Treat the attached reference image(s) as the absolute source of truth for silhouette, proportions, label layout, label colors, logo placement, cap/lid shape, and on-pack typography. Replicate these exactly — only the camera angle, lighting, and composition may differ.

CONCEPT: [Concept description — angle, composition, any context elements].

STYLE: Pure white background (RGB 255, 255, 255). Soft studio lighting with subtle rim highlight. Very soft diffused shadow beneath the product. Product fills ~85–90% of the frame. Sharp focus. Photorealistic commercial product photography, indistinguishable from real studio work. Amazon main-image compliant.

STRICT: No added text, callout boxes, benefit labels, badges, stickers, or logos beyond what already exists on the product. Square 1:1 composition.
```

---

## Shared Blocks Pattern (for multi-concept runs)

When generating 3–5 concepts of the **same product**, do not rewrite the PRODUCT, REFERENCE LOCK, and STRICT blocks for each concept. They're identical (same product, same compliance rail, same reference lock). Only the CONCEPT and STYLE blocks vary.

Pattern:

1. Write the shared blocks ONCE at the top of the concept brief:
   - `[PASTE PRODUCT BLOCK HERE]` — the full paranoid (or normal) PRODUCT description
   - `[PASTE REFERENCE LOCK BLOCK HERE]` — the reference-lock paragraph
   - `[PASTE STRICT BLOCK HERE]` — the compliance rail for the graphic type
2. In each per-concept prompt, drop in a PASTE-marker where each shared block goes, and fill only CONCEPT and STYLE.
3. When delivering prompts to the user, present the three shared blocks once at the top, then show each concept's lean prompt with PASTE-marker references.

This keeps output readable, forces consistency (same PRODUCT description across concepts means the product can't drift between concepts due to wording differences), and makes refinements trivial (edit one shared block, all concepts update). Worth the overhead at 3+ concepts; for single-concept runs, just inline.

---

## JSON `master_prompt` Structure (ChatGPT-specific power move)

ChatGPT handles structured JSON prompts noticeably better than prose for complex compositions — split-screen Us-vs-Them comparisons, multi-module lifestyle scenes, layered product+ingredient+effect shots. GPT-image-1's adapter parses JSON into explicit scene graph nodes instead of flattening to one prose blob.

**Use JSON when:** the shot has 2+ distinct visual modules, requires exact positional control, needs per-module atmosphere/lighting differences, or is a comparison graphic.

**Use prose when:** single-subject hero shot, simple lifestyle scene, features/benefits graphic — prose is fine and faster.

### Master JSON template

```json
{
  "master_prompt": {
    "global_settings": {
      "style": "Hyper-realistic commercial product photography",
      "layout": "[Vertical split-screen / single-frame hero / 2x2 grid / etc.]",
      "resolution": "8K UHD, cinematic lighting",
      "details": "Extreme clarity, frozen motion, micro-condensation, sharp focus throughout"
    },
    "module_1_left": {
      "subject": {
        "type": "[USER'S PRODUCT — full physical description]",
        "details": "[Texture, finish, condition cues — e.g., 'matte finish, visible condensation, crisp label']",
        "text_on_product": ["[EXACT on-pack text line 1]", "[line 2]", "[line 3]"]
      },
      "action": "[Dynamic element — e.g., 'gentle steam rising', 'soft splash at base', 'none (static hero)']",
      "floating_elements": [
        "[Context element 1 — e.g., 'whole turmeric root with water droplets']",
        "[Context element 2]",
        "[Context element 3]"
      ],
      "background": {
        "color": "[Deep brand-accent color / pure white / gradient description]",
        "lighting": "[Soft rim / cool moonlight / warm amber / clinical daylight]"
      }
    },
    "module_2_right": {
      "subject": {
        "type": "[COMPETITOR or contrast element — generic bottle, poor-quality alternative, etc.]",
        "details": "[Intentionally less premium than module 1]",
        "text_on_product": ["[Generic text only — never real competitor brands]"]
      },
      "action": "[Less dynamic or slightly negative — e.g., 'flat lighting, no action']",
      "floating_elements": [
        "[Elements that visually lose to module 1]"
      ],
      "background": {
        "color": "[Muted / grey / washed]",
        "atmosphere": "[Flat, unremarkable]"
      }
    },
    "surface_details": {
      "base": "[Reflective dark wet surface / clean white sweep / wooden counter]",
      "shadows": "Soft separated realistic shadows"
    }
  }
}
```

### How to use it

1. Attach the user's product image (and any reference images) — Hard Rule 3 still applies.
2. Prepend one short prose sentence above the JSON stating the task and naming the product:
   *"Based on the attached product reference, generate an Amazon listing 'Us vs Them' comparison image where `[PRODUCT NAME]` stands out on the left. Follow the JSON spec below exactly:"*
3. Paste the JSON.
4. Append the **four mandatory blocks** (preserve text / one unit / text-and-background rail matching the graphic type / reference-lock) as plain prose *after* the JSON. JSON alone doesn't reliably trigger them; ChatGPT treats trailing prose as override/reinforcement guidance.

### JSON rules

- **Never include real competitor brand names** in `module_2_right.subject.text_on_product`. Use generic placeholders ("OTHER BRAND", "STANDARD", blank labels). Naming competitors in AI image prompts is a policy + legal risk. If the user insists on a real name, refuse and explain why.
- For single-subject hero shots, use only `module_1_left` (or rename to `module_1_hero`) and drop the right module — ChatGPT handles partial schemas fine.
- Keep `text_on_product` arrays short (max ~5 lines). Long text renders poorly regardless of prompt structure.
- Resolution in JSON is flavor text; real output is still 1024×1024 / 1024×1536 / 1536×1024. Upscale in post.

---

## Generate One Concept at a Time (Rule 6 in practice)

1. Open a new ChatGPT chat, rename it correctly.
2. Confirm model (GPT-5 or GPT-4o — pick one and stay on it).
3. Attach the original product image(s) — main image first, additional angles after.
4. Send the prompt for ONE concept (prose template or JSON `master_prompt`).
5. Review against the identity checklist (Hard Rule 4):
   - Text fidelity — every word character-exact?
   - Logo geometry held?
   - Container silhouette held?
   - Color hierarchy held?
   - Element count held?
   - Quantity/size text exact?
   - Only one unit (if single-SKU)?
6. **If good** → move to the next concept in a new chat.
7. **If small composition issue** → send a tight refinement prompt in the same chat (ChatGPT handles these well).
8. **If any identity check fails** → start a new chat from the original product image(s), tighten the reference-lock block, re-send.

---

## Refinement Prompts (when output is close but needs a tweak)

- **Make it bigger:** *"Make the product larger — fill about 90% of the image. Keep everything else identical. Keep all reference-locked attributes (silhouette, label, logo, text) exactly the same."*
- **Fix lighting:** *"Enhance lighting to look more premium. Add subtle rim lighting along the edges, softer shadows. Keep white background pure. Do not alter the product itself."*
- **Simplify:** *"Remove [element]. Just the product with clean studio lighting on white. Keep the product identical to the reference."*
- **Fix shadow:** *"Make shadow extremely soft and diffused — barely visible, no hard edges. Do not change the product."*
- **Fix on-pack text:** *"The text on the packaging currently reading '[INCORRECT]' should read exactly '[CORRECT FROM REFERENCE]'. Match character-for-character including case and spacing. Leave everything else unchanged."*
- **Reduce to one unit:** *"Render only ONE (single) unit — remove any additional copies. This is a single-unit product, not a multi-pack."*
- **Lock product, change scene:** *"Keep the product pixel-identical. Only change [background / lighting / angle / composition element]."*

---

## Amazon Main Image Compliance Checklist

Before finalizing any main image:

- [ ] Pure white background (RGB 255, 255, 255) — snap off-white (~250) to pure white in Photoshop Levels or `magick input.png -level 97%,100% output.png`
- [ ] No text, logos, or graphics added (product's own printed branding is fine)
- [ ] No watermarks, badges, or stickers
- [ ] Product fills 85%+ of the frame
- [ ] No lifestyle elements for Concepts A/B/C
- [ ] Minimum 1000px on longest side; upscale to 2000px for zoom
- [ ] All on-pack text matches the reference exactly
- [ ] Only one unit rendered (unless multi-pack product)
- [ ] No ChatGPT watermark/signature in the corner (rare but happens — crop or remove in post if it appears)

---

## Common Issues & Fixes

| Issue | Fix |
|-------|-----|
| Identity drift (wrong shape / wrong logo / garbled text) | Start a new chat with the original product image(s); tighten the reference-lock block |
| Looks too "AI-ish" / plasticky | Add "photorealistic, indistinguishable from real photography, natural lighting imperfections, subtle surface texture" |
| Product too small | Re-prompt: "product fills 90% of the frame" |
| Background not pure white | Re-prompt: "pure white, RGB 255,255,255, no gradient, no off-white cast" — or snap in Photoshop Levels post-generation |
| Garbled text on labels | Re-prompt with exact text to preserve; attach a closer-crop reference of the label if possible; if persistent, post-fix in Photoshop |
| Re-cased or "improved" on-pack text | Re-send the preserve-text rule explicitly in its own paragraph |
| Multiple units when you wanted one | Add "Render ONE (single) unit only; never show multiples" |
| Harsh shadows | Re-prompt: "extremely soft diffused shadow, barely visible" |
| Context element too big or competes with hero | Re-prompt: "context element at 20% scale compared to product; product is the clear focal point" |
| Quota hit mid-session / quality drop | Likely hit the daily image quota and routed to a cheaper model. Start a fresh chat, wait for quota reset, or switch accounts |
| Output capped at 1024 max side | GPT-image-1 is capped. Upscale post-generation with Topaz Gigapixel, Photoshop Preserve Details 2.0, or Let's Enhance |
| JSON prompt ignored / output looks prose-like | Re-send with a one-line lead-in ("Follow the JSON spec below exactly:") and the four mandatory rules appended as prose after the JSON |
| Exact grid layout (2×5, 3×3) drifts or self-loops | GPT-image-1 renders 1×N stacks then self-iterates indefinitely. Tight refinement: "Stop iterating. Render ONE final image now: [exact spec]. Commit." OR use JSON `master_prompt` with per-unit positional coordinates. |
| ChatGPT refuses citing brand/competitor name | Remove any real competitor brand names; use "OTHER BRAND" / "STANDARD" placeholders in JSON `module_2` |

---

## Mode A: Autonomous (Claude in Chrome — recommended when available)

This is the autonomous path — Claude drives the ChatGPT tab end-to-end. The parent SKILL.md's Step 3b capability check has already confirmed you're here. If you somehow landed in this section without browser tools (`mcp__Claude_in_Chrome__*` prefix not present in your tool list), STOP and switch to **Mode B** below — never simulate browser actions without the tools.

### The operator loop, per concept

1. **Navigate to ChatGPT.** `navigate` to `https://chatgpt.com/`. If there's a login wall / captcha / account picker, **stop and hand off to the user** — logging into someone's ChatGPT account on their behalf is prohibited (user_privacy: never authorize account access).

2. **Start a new chat.** Find the "New chat" button (top-left of sidebar, pencil or "+" icon). Click. Verify a fresh empty composer appears and the model selector is visible top-center.

3. **Confirm / set the model.** Click the model picker (top-center). Pick GPT-5 if available; otherwise GPT-4o. Do NOT pick a "mini" or "auto" variant — image-model adapter behavior is inconsistent on those. Stay on the same model for the entire concept.

4. **Rename the chat immediately** (before any prompt sends — once the first prompt sends, ChatGPT locks an auto-name that's annoying to override). New chats don't always expose rename until the first message is sent. If rename isn't available yet, send a placeholder first ("Setting up prompt for product image generation — please wait."), let ChatGPT name the chat, then rename via the three-dot hover menu on the sidebar entry → Rename → type `[Brand] - A/B Experiment [Round] Concept [Letter]` → Enter. If the deliverable brief tracks each concept's chat URL, rename is optional — the URL table serves the tracking purpose.

5. **Attach the product image — JS blob download + `file_upload` from host Downloads.** **Confirmed working 2026-04-29 via tester.** ChatGPT has three persistent file inputs in the DOM (`#upload-files`, `#upload-photos`, `#upload-camera`) — `file_upload` against any of them works cleanly when the path is a real host Windows path (NOT a Cowork sandbox AppData path). No intercept trick needed (unlike Gemini, which requires the click-override pattern because its file input is created dynamically).

   **Path A (preferred — confirmed working) — JS blob download + file_upload.**

   **Phase 1 — Get image bytes onto host filesystem via JS-triggered blob download.**
   - `tabs_create_mcp` to `https://drive.google.com/file/d/<FILE_ID>/view`. The image loads inside Drive's viewer using the user's authenticated cookies (same-origin fetch reachable from inside the page).
   - `left_click` somewhere in the page body to focus the document.
   - `javascript_tool`:
     ```javascript
     (async () => {
       // Pick the LARGEST image on the page — skips Google avatar (32x32),
       // favicons, and any decorative icons. The product image is always
       // the biggest <img> in Drive's viewer.
       const imgs = Array.from(document.querySelectorAll('img'))
         .filter(img => img.naturalWidth > 100)
         .sort((a, b) => (b.naturalWidth * b.naturalHeight) - (a.naturalWidth * a.naturalHeight));
       const img = imgs[0];
       if (!img) return 'no-img-found';
       const res = await fetch(img.src);
       const blob = await res.blob();
       const url = URL.createObjectURL(blob);
       const a = document.createElement('a');
       a.href = url;
       a.download = 'abtest-ref-' + Date.now() + '.jpg';
       document.body.appendChild(a);
       a.click();
       URL.revokeObjectURL(url);
       return a.download + ' (' + img.naturalWidth + 'x' + img.naturalHeight + ')';
     })();
     ```
     Return value is the downloaded filename + the source dimensions (e.g. `abtest-ref-1714389123456.jpg (523x930)`). File lands at `C:\Users\marti\Downloads\<filename>`. **Verify the dimensions match the product image** — if they're 32x32 or similar, the filter didn't catch the avatar; widen the threshold and retry. **Don't use `querySelector('img[src*="googleusercontent"]')`** — Google Drive's viewer has multiple `googleusercontent` images including the user's profile avatar at index 0. Always select by size.

   **Phase 2 — `file_upload` to ChatGPT.**
   - `tabs_context_mcp` to ChatGPT tab (or `tabs_create_mcp` to `chatgpt.com` if not open). Confirm fresh chat with model picked.
   - `find` for one of the three persistent file inputs by id: `#upload-files`, `#upload-photos`, or `#upload-camera`. Any of them works — `#upload-files` is the most general.
   - `file_upload` using that ref, path = `C:\Users\marti\Downloads\<filename-from-Phase-1>`. **Critical:** use the real host Windows path, NOT a Cowork sandbox AppData path (sandbox paths cause the upload to either error with "Not allowed" or hang server-side).
   - Wait ~5 seconds, `read_page` to verify the thumbnail rendered AND no spinner.
   - Rare edge case: if the spinner sticks (mostly observed with sandbox paths, not host Downloads paths), dispatch the `change` event manually:
     ```javascript
     document.getElementById('upload-files').dispatchEvent(new Event('change', { bubbles: true }));
     ```
   - **Multi-angle:** repeat Phase 1 per Drive link, then `file_upload` each into the same ChatGPT chat. ChatGPT accepts multiple attached images per turn.

   ---

   **Path B (alternative — also confirmed working) — JS fetch + canvas re-encode + `clipboard.write` from inside Drive viewer URL → Ctrl+V into ChatGPT.**

   Slower than Path A but doesn't require finding a file input. Use as fallback if Path A fails.
   - `tabs_create_mcp` to `https://drive.google.com/file/d/<FILE_ID>/view`.
   - `left_click` page body to focus.
   - `javascript_tool`:
     ```javascript
     (async () => {
       const img = document.querySelector('img[src*="googleusercontent"]') || document.querySelector('img');
       const res = await fetch(img.src);
       const blob = await res.blob();
       const bitmap = await createImageBitmap(blob);
       const canvas = new OffscreenCanvas(bitmap.width, bitmap.height);
       const ctx = canvas.getContext('2d');
       ctx.drawImage(bitmap, 0, 0);
       const png = await canvas.convertToBlob({type: 'image/png'});
       await navigator.clipboard.write([new ClipboardItem({'image/png': png})]);
       return 'done';
     })();
     ```
     PNG re-encode is mandatory — Clipboard API only accepts PNG for images.
   - `tabs_context_mcp` to ChatGPT, `left_click` placeholder text, `key: "ctrl+v"`. Verify thumbnail.

   ---

   **Path C (TESTED-FAILED on ChatGPT 2026-04-29 — kept for diagnostic reference) — Direct image URL → Ctrl+A + Ctrl+C → Ctrl+V.**

   Was the previously documented primary based on a colleague's earlier run, but tester confirmed FAIL on a fresh ChatGPT session. Cowork's OS-clipboard transfer between tabs appears unreliable; the image bytes don't make it through to ChatGPT's paste handler. Skip on ChatGPT — Path A or B is faster anyway.

   - Extract `FILE_ID` from the user's Drive link.
   - `tabs_create_mcp` to `https://drive.google.com/thumbnail?id=<FILE_ID>&sz=w2000` (Google's thumbnail endpoint, more reliable than `uc?export=view` which has been observed redirecting to `drive.usercontent.google.com/download?...` for some files). If thumbnail returns 403 or doesn't render, fall back to `https://drive.google.com/uc?export=view&id=<FILE_ID>` and verify it actually shows the image before continuing.
   - **Wait for the image to actually finish loading before continuing.** Either sleep ~2 seconds, or `read_page` and confirm the image element is rendered. Skipping this caused a real bug in production: Ctrl+A fired before the new image was in the DOM, so the selection was empty and Ctrl+C snapshotted whatever stale content was already in the OS clipboard (a previous tab's URL).
   - `left_click` somewhere on the image area to focus the page.
   - `key: "ctrl+a"` — selects the image as a unit (on a standalone-image page, Ctrl+A grabs the image, not just text).
   - `key: "ctrl+c"` — OS-level keyboard event copies the actual image bytes to the OS clipboard. **Do NOT use `navigator.clipboard.write()`** from JS injection — it fails on the document-focus check.
   - `tabs_context_mcp` to switch to the ChatGPT tab.
   - `left_click` directly on the visible "Ask ChatGPT" placeholder text (NOT the wrapper around it — clicking the wrapper drops the paste silently).
   - `key: "ctrl+v"` — verify the thumbnail appears in the composer.
   - **Multi-angle:** for each additional image, `tabs_context_mcp` back to the Drive tab, `navigate` to the next direct image URL, **wait again** before click + Ctrl+A + Ctrl+C, switch to ChatGPT, Ctrl+V. The wait after every navigate is non-negotiable — without it, you'll attach the previous image again or nothing at all.

   **Path B (fallback if Path A doesn't render the image) — JS fetch + canvas re-encode + clipboard.write from inside the Drive viewer URL.** **Caveat: this path has been observed to fail in some Cowork sessions** because tab-switching after `navigator.clipboard.write()` loses the clipboard state before ChatGPT's paste handler receives it (Cowork's clipboard doesn't reliably bridge tabs). Try once; if no thumbnail appears in the composer after Ctrl+V, abandon to Path C.
   - `tabs_create_mcp` to `https://drive.google.com/file/d/<FILE_ID>/view` (the regular sharing URL). The image loads inside Drive's viewer using the user's authenticated cookies, so it's reachable via same-origin fetch from inside the page.
   - **`left_click` somewhere in the page body to focus the document** — required for the Clipboard API to accept a write.
   - `javascript_tool` to run:
     ```javascript
     (async () => {
       const img = document.querySelector('img[src*="googleusercontent"]') || document.querySelector('img');
       const res = await fetch(img.src);  // same-origin from inside drive.google.com
       const blob = await res.blob();
       const bitmap = await createImageBitmap(blob);
       const canvas = new OffscreenCanvas(bitmap.width, bitmap.height);
       const ctx = canvas.getContext('2d');
       ctx.drawImage(bitmap, 0, 0);
       const png = await canvas.convertToBlob({type: 'image/png'});
       await navigator.clipboard.write([new ClipboardItem({'image/png': png})]);
       return 'done';
     })();
     ```
     The PNG re-encode is mandatory — Clipboard API only accepts PNG for images natively.
   - Switch to ChatGPT, click composer, `key: "ctrl+v"`.

   **Path C (Amazon-URL flow only — no Drive link given) — Right-click copy from the Amazon image tab.**
   - `navigate` second tab to the Amazon image URL.
   - `right_click` on the displayed image → "Copy image". Amazon doesn't block the context menu like Drive's viewer does.
   - Switch to ChatGPT, paste.

   **Path D — Drive download → host Downloads → `file_upload` + manual `change` event dispatch.** This is the workaround for the React-handler bug where `file_upload` sets `input.files` but doesn't fire the `change` event ChatGPT listens for. Combines two known mechanisms to fix each other.
   - `navigate` Chrome to `https://drive.google.com/uc?export=download&id=<FILE_ID>`. Triggers a browser download via the user's Google session. File lands in `C:\Users\marti\Downloads\<original-filename>`.
   - Wait ~5 seconds for the download. Find the filename (Drive MCP `get_file_metadata.name` field, or `bash_tool ls -t /mnt/c/Users/marti/Downloads/` if mounted).
   - `file_upload` from the **real Windows host path** (e.g. `C:\Users\marti\Downloads\ref-1.jpg`). Sandbox AppData paths return "Not allowed"; the Downloads folder is a normal user dir and should be accepted.
   - **Immediately after `file_upload` returns success, dispatch the change event manually:**
     ```javascript
     (() => {
       const inputs = document.querySelectorAll('input[type="file"]');
       for (const input of inputs) {
         if (input.files && input.files.length > 0) {
           input.dispatchEvent(new Event('change', { bubbles: true }));
           return `dispatched change on input with ${input.files.length} files`;
         }
       }
       return 'no file input with files found';
     })();
     ```
   - Wait ~10 seconds, `read_page` to verify the thumbnail appears AND the spinner resolves. If the spinner is still spinning at 30s, abandon — Cowork's `file_upload` either didn't actually populate `input.files` or the React handler is wired differently than expected.
   - **Multi-angle:** repeat per Drive link. Each `file_upload` + manual dispatch sequence attaches one image.

   **Path E (last resort) — Switch to Mode B paste-ready output.** After ONE failed attempt at each of A, B, and (if applicable) C, stop autonomous attempts and produce the Mode B brief. Tell the user explicitly which paths failed and switch the framing: *"Autonomous attach failed at [specific path]. Switching to Mode B. Here are 5 paste-ready prompts — drag-drop the image into each fresh chat yourself, then paste the prompt."*

   Path A is the default in Cowork-driven runs that started from a Drive link. Empirically the most reliable.

   **Anti-patterns — known to fail with specific error signatures, do NOT try:**
   - `file_upload` returns success and a thumbnail placeholder appears in the composer, but the upload spinner never resolves → **Cowork's `file_upload` tool sets `input.files` programmatically but doesn't dispatch the `change` event that ChatGPT's React handler listens for. The upload POST never fires.** Confirmed via diagnostic 2026-04-29: same file drag-dropped manually uploads instantly, ruling out file/account issues. **Operating rule:** if the spinner is still spinning 30 seconds after `file_upload` reported success, abandon. Don't loop on `file_upload` — the failure is structural. Switch to Path A (Ctrl+A + Ctrl+C from direct image URL) which bypasses the file input entirely.
   - `file_upload` from any `AppData\Roaming\Claude\...` or `/tmp/...` path → returns `{"code":-32000,"message":"Not allowed"}`. Chrome's extension layer treats sandbox app-data dirs as untrusted. Different failure mode from the above; both reasons to avoid `file_upload`.
   - `file_upload` on Gemini's "Upload files" button (Gemini-side, but mentioned here for completeness) → "Element is not a file input."
   - `navigator.clipboard.write()` from `javascript_tool` injection without first focusing the page → `NotAllowedError: Document is not focused`.
   - `canvas.toBlob()` on a Drive viewer's `<img>` element when the src is `lh3.googleusercontent.com` and the page is `drive.google.com` → tainted canvas SecurityError. Workaround used in Path B: fetch the image first (same-origin from inside drive.google.com), then re-encode through the canvas.
   - `fetch()` from `chatgpt.com` to any Drive endpoint (`/uc?export=download`, `/file/d/.../preview`, `usercontent.google.com/download`, `/thumbnail`, `lh3.googleusercontent.com`) → `TypeError: Failed to fetch`. ChatGPT's CSP + extension URL filter blocks third-party fetches from chatgpt.com origin.
   - Right-click on the image inside Drive's preview viewer → context menu suppressed (Drive intercepts).
   - `file://C:/Users/...` URL navigation → Chrome extension permission blocks; silently redirects to `chrome://newtab`.
   - Local HTTP server in Cowork sandbox to serve the image to Chrome → networking namespaces don't bridge (Cowork's 127.0.0.1 ≠ host Chrome's 127.0.0.1).
   - `upload_image` tool with arbitrary screenshot IDs or sandbox file UUIDs → "Unable to access message history to retrieve image". Only resolves images from the conversation message stream.

6. **Paste the prompt — ALWAYS as one atomic clipboard paste, NEVER via typing.** The ChatGPT composer is a contenteditable div that interprets newline characters as Enter (= send). If you use `form_input` on a multi-line prompt, the model types it character-by-character; the first newline fires the send, the prompt goes out with only the first line, and the rest sits in the composer as an unsent draft. Always use the two-step clipboard pattern instead:

   a. **Focus the editor + insert via `execCommand('insertText')`.** ChatGPT's composer is a ProseMirror editor at `#prompt-textarea`. The `document.execCommand('insertText', false, text)` API is the **confirmed working method on ChatGPT** — verified via tester run 2026-04-29 (worked first try). `navigator.clipboard.writeText()` is **TESTED-FAILED on ChatGPT** even with `editor.focus()` first — it returns `NotAllowedError: Document is not focused`, presumably because the focus state from `javascript_tool` injection doesn't satisfy the browser's stricter permissions check for the Clipboard API. `form_input` typing also fails — ProseMirror swallows the synthesized key events.

      Use `javascript_tool` to run:
      ```javascript
      (() => {
        const editor = document.getElementById('prompt-textarea');
        if (!editor) return 'no-editor-found';
        editor.focus();
        document.execCommand('insertText', false, `<<FULL PROMPT TEXT — backticks-quoted, newlines preserved, no escaping needed>>`);
        return 'inserted ' + editor.textContent.length + ' chars';
      })();
      ```
      Verify the return is `'inserted N chars'` matching the prompt length. The prompt — including JSON `master_prompt`, multi-paragraph prose, all newlines — lands in the composer as one atomic operation that ProseMirror's change handler picks up correctly (so the send button activates).

      **No separate paste step needed.** `execCommand('insertText')` inserts directly into the editor — there's no clipboard hop and no Ctrl+V required.

      **Note on cross-tool consistency:** `execCommand('insertText')` also works on Gemini's Quill editor. If you want a single-method pattern across both tools, use it everywhere. Gemini also accepts the DOM `createElement + appendChild` pattern documented in `step-3-gemini.md`; both are confirmed working there.

   b. **Verify before sending.** Use `read_page` to confirm the entire prompt is in the composer. Long prompts may visually scroll within the composer — that's fine; check the last line of your prompt is present and the char count matches the input.

   **NEVER use `form_input` for multi-line prompts in Mode A.** ProseMirror swallows synthesized key events. Even single-line prompts should go through `execCommand('insertText')` — make it the default habit. The only exception is single-word fields with no newlines (e.g., a chat rename input).

   **TESTED-FAILED methods on ChatGPT (do NOT use):**
   - `navigator.clipboard.writeText()` + Ctrl+V — returns `NotAllowedError: Document is not focused` even after `editor.focus()`. The Clipboard API's permissions check isn't satisfied by JS-injected focus state.
   - `form_input` typing into the composer — ProseMirror swallows the synthesized events; partial or no text lands in the editor.
   - Setting `editor.textContent = text` directly — ProseMirror's internal state doesn't update; the send button stays disabled.
   - Direct `editor.value = text` — ProseMirror isn't a textarea; assignment does nothing visible.

7. **Send the prompt — `dispatchEvent` primary, find+click as fallback.** **Confirmed via `chat-flow-tester` 2026-04-29:** `find` + `left_click` by ref reports success but doesn't actually fire ChatGPT's submit handler. The reliable method is `dispatchEvent` directly on the send button.

   **Method A (preferred — confirmed working) — `dispatchEvent` directly.**
   ```javascript
   (() => {
     const btn = document.querySelector('button[data-testid="send-button"]');
     if (!btn) return 'no-send-button';
     btn.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
     return 'sent';
   })();
   ```
   Verify return is `'sent'`. Then verify the URL changed to `chatgpt.com/c/<chat-id>` (or the response stream visibly started) within 5 seconds.

   **Method B (fallback) — `find` + click via ref.**
   - `find` for `button[data-testid="send-button"]` → get a ref → click via the ref.
   - If the click reports success but the URL doesn't change and no response stream starts, the click didn't actually fire the submit handler — switch to Method A.

   ChatGPT shows "Creating image…" — typically 20–90 seconds. Don't interact with the page during generation — clicking away can cancel it.

   **Note for Gemini:** the tools are reversed there. On Gemini, `find` + click on `button[aria-label="Send message"]` works first try; `dispatchEvent` is the fallback. See `step-3-gemini.md` step 5 for the Gemini send-button section.

8. **Check the output.** Use `computer` screenshot or `read_page` to get the rendered image. Run the identity checklist (Hard Rule 4). If it passes, go to step 9. If small refinement needed, send one follow-up in the same chat. If identity drifts, go back to step 2 and start a new chat with the original reference — do NOT try to fix identity drift in the same chat.

9. **Download the image.** Hover the generated image; download icon appears (top-right of the image, arrow-down or "..." menu with Download option). Click. Save to a predictable path (project folder if available, otherwise `/tmp/chatgpt-ab-output-[brand]-[concept].png`). Verify with `bash_tool ls`.

10. **Move to the next concept.** Back to step 2 (new chat). Don't reuse the previous concept's chat for a different concept — Hard Rule 6.

### Things Claude in Chrome must NOT do here

- Don't open any `sellercentral.amazon.*` tab. Ever. (Hard Rule 0)
- Don't navigate to `amazon.com` for competitor research. (Hard Rule 5) Step 1 always comes from the PDF/screenshot the user dropped in chat — even in a browser-capable environment.
- Don't write to Notion from this flow unless the user explicitly asks in the current turn. (Hard Rule 1)
- Don't log into ChatGPT on the user's behalf. If the session is logged out, hand off. (user_privacy)
- Don't accept cookie banners or ToS updates without user permission. (explicit_permission)
- Don't click "Share" on any generated image or export it outside ChatGPT without user permission.
- Don't click "Delete chat" on any previous chats in the sidebar, even if they look stale — destructive.

### When the browser gets stuck

| Symptom | Fix |
|---------|-----|
| "Please log in" wall | Stop. Hand off to the user to log in. |
| Cloudflare / captcha challenge | Stop. Never attempt to solve captchas — hand off. |
| Upload button doesn't respond | Refresh the page, start over from step 2. Don't try to work around via drag-and-drop scripting. |
| Stale attachment spinner stuck ("Waiting for file upload") | Navigate away to chatgpt.com/ fresh, re-attach from scratch. Won't recover without navigation reset. |
| Ctrl+V pastes nothing / no thumbnail | Clicked the wrapper, not the editable area. Screenshot, aim click at placeholder text coords, retry. |
| Window globals disappear after "New chat" click | Expected — sidebar "New chat" triggers client-side reload. Re-run blob-fetch / re-attach per chat. |
| `browser_batch` times out at 60s | Don't queue >5 × wait-10s per batch. Split into two sequential batch calls for 60s+ waits. |
| Generation spins forever (>3 min) | Request likely failed silently. Refresh and retry once. If it fails twice, account may be rate-limited — hand off and tell the user to check plan status. |
| Image generated but looks terrible / low quality | Probably routed to a cheaper image model. Start a fresh chat with the explicit "Use GPT-image-1 (the highest-quality image model)" lead-in. |
| Rename field won't appear / grays out | ChatGPT locks rename until the first message completes. Send the placeholder message first (step 4 fallback). |
| Prompt doesn't fit in composer / gets cut off | Paste in two sends. Send the full shared blocks first ("Here is the product setup I'll be referencing for the next prompt:"), then the concept-specific prompt as a second message. ChatGPT holds context within a single chat. |
| Prompt fired mid-typing with only the first line — rest left in the composer as a draft | You used `form_input` (typing) instead of clipboard paste. The composer interprets the newline at the end of line 1 as Enter and submits. **Fix:** always use the `navigator.clipboard.writeText` + `ctrl+v` two-step pattern in step 6. Never `form_input` a multi-line prompt. To recover from this specific incident: read the composer with `read_page`, capture the unsent draft, copy what was already sent, stop the chat (don't try to interrupt mid-generation — let it finish), then either (a) start a new chat and re-send the full prompt atomically, or (b) reply in the same chat with "ignore the previous partial — here is the full prompt: …" and paste the full prompt. Option (a) is cleaner per Hard Rule 6. |

---

## Mode B: Manual Paste Output (when Claude in Chrome isn't available)

You're here because Step 3b's capability check found no browser tools. Your job is to **produce a paste-ready brief the user can run themselves in chatgpt.com**, not to simulate browsing. The parent SKILL.md has already told the user this mode is what's running and offered them Cowork as the autonomous alternative.

### What to deliver to the user

Output a single, scan-friendly message containing four parts in this order:

**Part 1 — Setup instructions (one block, generic, applies to all 5 concepts):**

> *Here are 5 paste-ready prompts. For EACH concept (one fresh chat per image — no exceptions):*
>
> *1. Open chatgpt.com → click "New chat" (top-left of sidebar).*
> *2. Confirm the model is GPT-5 or GPT-4o (NOT mini/auto). Stay on the same model for all 5 concepts.*
> *3. Rename the chat in the sidebar to the title shown above each prompt. (If rename is locked until first message, send the placeholder "Setting up — please wait.", let ChatGPT auto-name, then right-click the sidebar entry → Rename.)*
> *4. Attach the original Amazon product image(s). Multi-angle is best — open each image URL in its own tab, click → Ctrl+C → switch to ChatGPT, click directly on the placeholder text in the composer (NOT the wrapper around it), Ctrl+V. Repeat per image.*
> *5. Paste the prompt block below the attachments.*
> *6. Send. Wait 20–90 seconds. Don't click away during generation — that cancels it.*
> *7. Run the identity checklist (in Part 4 below) on the output.*
> *8. If the output passes: hover the image → click the download icon (top-right of the image, arrow-down or "..." menu → Download). Save to wherever you keep this round's outputs.*
> *9. If small composition issue (lighting, shadow, angle): send a refinement prompt in the SAME chat (sample refinements in Part 5).*
> *10. If identity drifted (wrong logo, garbled text, wrong shape, missing element): close the chat, open a NEW one with the original reference, tighten the reference-lock paragraph, re-send. Do NOT try to fix identity drift in the same chat — it compounds.*
> *11. Repeat for the next concept in a fresh chat.*

**Part 2 — Shared blocks (write each block once, the user pastes them inside each concept's prompt):**

Output the three reusable blocks the user will copy into each concept's prompt:

- `PRODUCT BLOCK` — the full physical description. Use **paranoid mode** (every label zone, every text quote, every color named) if only one reference image is available. Normal 1–2 sentences if multi-angle.
- `REFERENCE LOCK BLOCK` — the reference-lock paragraph from the "Four Mandatory Prompt Blocks" section above (verbatim, with the product type substituted in).
- `STRICT BLOCK` — the compliance rail matching each concept's graphic type. Concepts A/B/C use the main-image rail (pure white, no overlay text). Concepts D/E use the lifestyle rail (no overlay text unless the concept calls for it). Comparison/features/benefits/instructional graphics use their own rails per Appendix B.

Format the three blocks as fenced code blocks so the user can copy without picking up surrounding prose.

**Part 3 — One block per concept (5 blocks: A, B, C, D, E):**

For each concept, produce a fenced code block with this structure:

```
[Brand] - A/B Experiment [Round] Concept [Letter]

Based on the attached product reference(s), create a professional Amazon product photograph of the [PRODUCT NAME].

PRODUCT: [PASTE PRODUCT BLOCK HERE — from Part 2]

REFERENCE LOCK: [PASTE REFERENCE LOCK BLOCK HERE — from Part 2]

CONCEPT: [Concept-specific composition — angle, framing, context elements, lighting mood]

STYLE: [Concept-specific styling — pure white vs lifestyle bg, lighting type, shadow treatment, depth of field, lens style]

STRICT: [PASTE STRICT BLOCK HERE — from Part 2 — matched to this concept's graphic type]
```

Concepts D and E (lifestyle) replace `STYLE` block's "Pure white background" with the actual scene description. The `STRICT` block on D/E is the lifestyle rail, not the main-image rail. For comparison graphics, use the JSON `master_prompt` structure from earlier in this file instead of the prose template.

**Part 4 — Identity checklist (Hard Rule 4, restated in user-friendly form):**

Tell the user to run this on every output:

> *Identity (any fail → new chat with original reference, do NOT fix in same chat):*
> *— Every word on the pack matches the reference exactly (no missing, invented, recased, translated).*
> *— Logo in same position on the same panel, same shape.*
> *— Container silhouette differences look like camera angle, not shape change.*
> *— Dominant label color matches; accent ratio matches.*
> *— Same number of label panels, badges, callouts, ingredient banners.*
> *— Quantity/size text exact ("60 GUMMIES" vs "60 Gummies" matters).*
> *— Only one unit (unless legitimately a multi-pack).*
>
> *Composition (allowed to drift, that's the point — refine in same chat):*
> *— Camera angle, focal length, lighting direction, shadow length, scene background, props, framing crop.*

**Part 5 — Sample refinement prompts (paste-ready):**

Give the user 5–6 short refinement prompts they can copy into the same chat for small fixes. Pull from the "Refinement Prompts" section earlier in this file: make-it-bigger, fix-lighting, fix-shadow, fix-on-pack-text, lock-product-change-scene, reduce-to-one-unit. Format as a list of fenced code blocks.

### Mode B operating principles

- **Don't generate the prompts in a vacuum.** The PRODUCT block, the CONCEPT, and the STYLE for each of A–E come from Step 1 and Step 2 outputs. Stitch the actual concept brief into each prompt — never ship template placeholders like `[Concept-specific composition]` to the user.
- **Don't include UI screenshots.** Mode A had paste-ready coordinates for an autonomous browser; Mode B is paste-ready text for a human. Skip the Operator Actions content.
- **Don't tell the user to install browser tools mid-output.** That's the parent SKILL.md's job (Step 3b Cowork recommendation). By the time you're producing Mode B, the user has already declined Cowork — give them a clean paste-ready brief.
- **Format for scanning.** Headings for each part, fenced code blocks for everything paste-ready, plain prose only for the surrounding instructions. The user is going to copy out of this — don't make them work to find the boundaries.

---

## Appendix: Prompt Templates by Graphic Type

Six distinct graphic types. Each has a different purpose and a different prompt shape. Append the four mandatory blocks (preserve text / one unit / text-and-background rail scoped to this type / reference-lock) to whichever you use.

### B1. Primary Image (Main Listing Image)

Hero shot in search results. Pure white, no overlay text, product fills the frame, 1:1 square.

**Starter (minimal):**
```
Create a clean photo rendering of this product to be used as the primary image on an Amazon listing. Pure white background (RGB 255, 255, 255), Amazon main image compliant, product fills 85–90% of the frame, 1:1 square. Preserve all on-pack text, logos, and graphics exactly as shown in the reference. Render ONE (single) unit only.
```

**Full (premium shot):** use the Standard Prompt Structure in the main body of this file with CONCEPT = "Premium hero shot. Product angled 30 / 45 degrees to show dimension. Soft studio lighting from upper-left with subtle rim highlight."

### B2. Lifestyle Image (In-Use / Contextual)

Product being used by the target customer in a real setting. Secondary image slot — relaxed compliance rail.

**Starter:**
```
Create a lifestyle image of a [AVATAR — e.g., "fit woman in her 30s", "busy dad at home", "dog owner outdoors"] using this product in [SETTING — e.g., "a bright modern kitchen", "a sunny park", "a minimalist bathroom"]. This image is for an Amazon listing. Preserve the product's exact appearance and all on-pack text from the reference. Photorealistic, bright natural lighting, product is the clear focal point but integrated naturally into the scene.
```

**Variant (4-up grid for concept exploration):**
```
Create 4 lifestyle images of [AVATAR] using this product in [SETTING], arranged in a 2x2 grid. Each panel shows a different moment — [moment 1], [moment 2], [moment 3], [moment 4]. Preserve the product's exact appearance across all four panels. Consistent lighting and color grading.
```

### B3. Features Graphic

Call out 3–5 product features in a clean, mobile-optimized layout. A+ content or secondary image slot.

**Starter (minimal):**
```
Make a clean aesthetic features graphic for this product to be used on an Amazon listing. Mobile optimized. Preserve the product's exact appearance.
```

**Variant (specified features):**
```
Make a clean aesthetic features graphic for this product to be used on an Amazon listing with the following features: [FEATURE 1], [FEATURE 2], [FEATURE 3], [FEATURE 4]. Mobile optimized — text large and readable on a phone screen. Preserve the product's exact appearance from the reference.
```

**Layout details for full prompts:** Product on the left (or centered top if vertical). Four feature callouts in a column (vertical) or 2x2 grid (square), each with a simple line-icon and short label (2–4 words max). Clean minimal aesthetic, brand color accents on icons and dividers, plenty of white space, modern sans-serif. Smallest text legible at 375px wide.

### B4. Benefits Graphic

Communicate the emotional/outcome-based reasons to buy. Often paired with features graphic — same layout, different text angle. Benefits = what the customer gets ("Fall asleep faster", "Smoother skin in 7 days"). Features = what the product has ("5mg melatonin", "Vitamin E enriched"). Both can live in the same listing if angles are distinct.

**Starter (chained after a features graphic):**
```
Now create a similar graphic but for benefits instead of features.
```

### B5. Competitor Comparison Graphic

The "Us vs Them" visual. **Strongest use case for the JSON `master_prompt` pattern.**

**Starter (minimal, prose):**
```
Create a simple, modern, clean competitor comparison graphic of this product for an Amazon listing. Mobile optimized. Preserve the product's exact appearance.
```

**Full (JSON — recommended):**

Prepend: *"Based on the attached product reference, generate an Amazon listing 'Us vs Them' comparison image where `[PRODUCT NAME]` stands out on the left. Follow the JSON spec below exactly:"*

Paste the JSON `master_prompt` from the JSON section above, filling `module_1_left` with the user's product and `module_2_right` with the generic alternative (never a real competitor brand name).

Append:
```
STRICT: Preserve all on-pack text and graphics on the user's product exactly as shown in the reference. Render ONE (single) product unit on each side. Use only generic placeholders (e.g., "OTHER BRAND") on the right module — no real competitor brand names. Product reference lock applies to the left module only. Mobile-optimized readability.
```

### B6. Instructional Graphic

How to use the product in 3–4 steps. Great for products with non-obvious use cases (supplements, multi-step skincare, tools with specific technique).

**Starter (minimal):**
```
Create a clean aesthetic instructional graphic for this product to be used on an Amazon listing. Mobile optimized. Preserve the product's exact appearance.
```

**Variant (specified steps):**
```
Create a clean aesthetic instructional graphic for this product to be used on an Amazon listing. Include the following steps: [STEP 1], [STEP 2], [STEP 3], [STEP 4]. Mobile optimized.
```

**Layout details:** four numbered panels in a vertical column (mobile) or horizontal row (desktop). Each panel: icon or mini-scene of the step, step number prominently (1, 2, 3, 4), short instruction label (3–6 words). Clean minimal, brand color accents, modern sans-serif, smallest text legible at 375px wide.

---

## Quick-Start Checklist

Before sending any ChatGPT prompt:

- [ ] Chat renamed to `[Brand] - A/B Experiment [Round] Concept [Letter]`
- [ ] Model confirmed (GPT-5 or GPT-4o — pick one, don't switch mid-chat)
- [ ] Original Amazon product image(s) attached, main angle first
- [ ] Prompt includes all four mandatory blocks (preserve text / one unit / text-and-bg rail matching graphic type / reference-lock)
- [ ] Concept type matches graphic-type template (B1–B6)
- [ ] For complex multi-module compositions: JSON `master_prompt` used, four rules appended as prose
- [ ] No real competitor brand names in the prompt
- [ ] Aspect ratio stated in prose ("square 1:1" / "vertical 2:3" / "horizontal 3:2")

After generation:

- [ ] Identity checklist (Hard Rule 4) all green
- [ ] On-pack text legible and character-exact
- [ ] Only one unit rendered
- [ ] Background truly pure white (for main images)
- [ ] No added overlay text, badges, watermarks
- [ ] Product fills 85%+ of frame (for main images)
- [ ] Upscale to 2000px longest side before handoff if going straight to listing

If any "After generation" check fails → follow the decision tree in *Generate One Concept at a Time* above.
