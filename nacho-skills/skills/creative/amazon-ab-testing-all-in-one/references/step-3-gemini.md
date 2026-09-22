# Step 3 — Gemini Pro Image Generation

This is the Step 3 operator manual for the Gemini branch of the workflow. The parent `SKILL.md` has already established Hard Rules 0–6 (no Seller Central, no Notion writes, no Amazon nav, always attach reference, identity guardrails, one-image-one-chat) — those apply here by default.

This file covers what's specific to Gemini: Pro model selection, the clipboard-canvas JS for pasting Amazon images, the golden Rule "if it drifts, stop and start fresh from the last good image," prompt structure, the prompt template library, and Gemini-specific failure modes.

---

## Why Gemini for this workflow

Gemini Pro is the right tool when:
- The user only has Gemini access (no ChatGPT subscription or quota issues there)
- The shot is single-subject and doesn't need JSON `master_prompt` multi-module structure
- The user wants the clipboard-canvas paste flow (works directly on Amazon image tabs in same-origin)

Trade-offs vs. ChatGPT:
- Slightly weaker on consistency across iterations — context can "corrupt" mid-thread, requiring a restart from the last good image
- Less reliable in-chat refinement for moderate issues — when Gemini gets a detail wrong, follow-up corrections often compound the error
- No structured-JSON adapter — comparison graphics (Us vs Them) are noticeably harder than in ChatGPT

The golden rule that flows from these properties: **if Gemini messes up, STOP and start fresh from the last good image** — don't try to fix it in the same chat.

---

## Naming Every Chat

Format: **[Brand Name] - A/B Experiment**

Examples:
- `VI PRESTIGE - A/B Experiment`
- `GlowC Beauty - A/B Experiment`
- `PawComfort - A/B Experiment`

For multiple concepts, add the concept letter: `Mila & Lulu - A/B Experiment Concept B`
For restarts, add a number: `VI PRESTIGE - A/B Experiment 2`

Gemini auto-names chats based on the first prompt. Type the brand name early in your prompt or rename the chat manually after generation.

---

## Model Selection — Always Pro

Every new Gemini chat defaults to **Fast**. You MUST switch to **Pro** before sending any prompt.

**How to switch:**
1. Open the model picker in the Gemini interface (usually near the prompt input area)
2. Select "Pro" — NOT Fast, NOT Thinking
3. Confirm Pro is selected before typing anything

Pro generates significantly better photorealistic product images. Fast produces lower-quality output that isn't suitable for product photography references. Check the model picker EVERY new chat — the default reverts.

---

## Attaching the Original Product Image — Rule 3 Applied

Hard Rule 3 (parent SKILL.md): always attach the real Amazon product photo. Gemini's reliable path is the clipboard-canvas method.

### Clipboard-canvas paste (primary method)

1. Open the Amazon product image in its own browser tab (click the main image, then right-click → "Open image in new tab" to get full-resolution).
2. Focus that tab (click on it).
3. Run this JavaScript in the console to copy the image to clipboard:

```javascript
(async () => {
  const img = document.querySelector('img');
  const canvas = document.createElement('canvas');
  canvas.width = img.naturalWidth;
  canvas.height = img.naturalHeight;
  const ctx = canvas.getContext('2d');
  ctx.drawImage(img, 0, 0);
  const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/png'));
  await navigator.clipboard.write([new ClipboardItem({'image/png': blob})]);
  return 'done';
})();
```

4. Switch to the Gemini tab.
5. Click on the prompt input area.
6. Paste (Ctrl+V) — the image should appear as an attachment.
7. Type your prompt below the pasted image.
8. Send.

**Important — same-origin restriction:** This clipboard method only works on **same-origin** images. It works on Amazon product image tabs because you're on `amazon.com` copying an `amazon.com` image. It does **NOT** work on Gemini-generated images (cross-origin restriction — the canvas becomes "tainted" and `toBlob` fails).

**To re-use a Gemini-generated image** (e.g., to restart from the last good output per the Golden Rule):
- Right-click the Gemini image → "Save image as..." → save locally
- OR ask the user to manually save the image
- Then upload to a new Gemini chat via drag-and-drop or the upload button

**Fallback if clipboard fails:** ask the user to manually download the product image and drag it into the Gemini chat, or use Gemini's file upload button.

---

## Golden Rule — If Gemini Messes Up, STOP and Start Fresh

This is the most important lesson from real experience with Gemini specifically. Hard Rule 6 (one-image-one-chat) covers the general principle; this is the Gemini-specific failure mode.

**When Gemini gets product details wrong** (wrong shape, wrong colors, wrong zipper placement, missing logo, extra elements that don't exist on the real product):

1. **STOP immediately.** Do NOT try to fix it in the same chat thread.
2. Trying to correct Gemini in the same conversation almost always makes it worse — it starts compounding errors.
3. **Take the last GOOD image** — the last version that was acceptable before the error.
4. **Start a brand new Gemini chat.**
5. **Switch to Pro model** (the new chat will default to Fast).
6. **Attach the last good image** (not the original product photo — the last Gemini output that was correct).
7. **Write refinement instructions** referencing the attached image.
8. **Continue work in the new chat.**

**Why:** Gemini's conversation context can "corrupt" — once it generates a wrong detail (like a diagonal zipper instead of a straight one), it tends to persist or worsen that error in follow-ups within the same thread. A fresh chat with a clean reference image gives the best results.

**Caveat per Hard Rule 3:** if the product identity itself has drifted (not just a small detail), restart from the **original Amazon product image**, not a Gemini output. Gemini outputs are only acceptable seeds when they were correct on identity but you're refining a small composition issue.

---

## Prompt Structure

**CRITICAL:** Always begin Gemini prompts with **"Generate an image:"** — without this, Gemini may interpret the prompt as a question instead of generating an image.

### Standard structure

```
Generate an image: [Brand Name] - A/B Experiment [Number] Concept [Letter]. Based on the attached product image, create a professional product photography shot of the [PRODUCT NAME].

PRODUCT: [Exact description — name, colors, materials, key features, all visible packaging elements]. Preserve every existing text and graphic on the packaging exactly. Render ONE (single) unit only [or for multi-pack: list each item: "1 Black, 1 Gray, 1 Navy, 1 Red, 1 Olive"].

CONCEPT: [Concept name and detailed composition instructions].

REQUIREMENTS:
- Pure white background (RGB 255, 255, 255)
- Product fills 85%+ of the frame
- Photorealistic — looks like a professional product photo, not AI art
- Soft studio lighting with subtle rim light
- Very soft, barely visible shadow beneath the product
- Amazon main image compliant: no added text, no graphics, no props (unless concept calls for context elements on secondary images)

CRITICAL PRODUCT DETAILS TO GET RIGHT:
- [Detail 1 — e.g., "The zipper runs straight vertically along the right side, NOT diagonal"]
- [Detail 2 — e.g., "The logo is a white 'VI' centered on the front panel"]
- [Detail 3 — e.g., "There are exactly 6 bags: 2 royal blue, 2 dark charcoal, 2 light gray"]
```

For single-item products, drop the pack count and color list but keep everything else the same.

For the full library of prompt templates (premium shots, packaging combos, lifestyle shots, ingredient context, zoom details, category-specific), see `references/gemini-prompts.md`.

---

## Generate One Concept at a Time — With Learning

For EVERY concept after the first, you MUST review the previous concept's output before writing the next prompt. This is how you maintain consistency and learn what Gemini gets right/wrong.

### Concept generation workflow

1. **Open a new Gemini chat** (`gemini.google.com`)
2. **Switch to Pro model** (every new chat defaults to Fast — Hard rule for Gemini)
3. **Paste the product image** via the clipboard-canvas JS
4. **Send the prompt** for one concept (always start with "Generate an image:")
5. **Review against the identity checklist** (Hard Rule 4 in parent SKILL.md):
   - Text fidelity — every word character-exact?
   - Logo geometry held?
   - Container silhouette held?
   - Color hierarchy held?
   - Element count held?
   - Quantity/size text exact?
   - Only one unit (if single-SKU)?
6. **If good** → write down what Gemini got right (note for the next prompt) → move to the next concept in a new chat
7. **If small composition fix needed** → send a tight refinement prompt in the same chat
8. **If any identity check fails** → STOP → new chat with the last good image (Golden Rule above)

### Before writing each subsequent concept prompt, answer:

- What did Gemini get RIGHT in the last concept? (Carry this forward)
- What did Gemini get WRONG? (Explicitly correct this in the next prompt)
- Is product identity consistent with prior concepts? (Same colors, same branding, same form)

This review step is NOT optional. Skipping it is how you end up with Concept A showing 5 colors and Concept C showing 3.

---

## Refinement Prompts

When the image is close but needs a tweak:

**Make product more prominent:**
```
Make the product larger in the frame — it should fill about 90% of the image. Keep everything else the same.
```

**Fix lighting:**
```
Enhance the lighting to look more premium. Add subtle rim lighting along the product edges and softer, more diffused shadows. Keep the white background pure.
```

**Add context element:**
```
Add [ELEMENT — e.g., "a pair of dress shoes partially visible emerging from one of the bags"] to make the product's purpose immediately clear. The product is still the hero — the context element is secondary and smaller.
```

**Simplify:**
```
Remove [ELEMENT]. Simplify the composition. Just the product with clean studio lighting on white.
```

**Fix shadow:**
```
Make shadow extremely soft and diffused — barely visible, no hard edges.
```

**Reduce to one unit:**
```
Render only ONE (single) unit — remove any additional copies. This is a single-unit product, not a multi-pack.
```

---

## Amazon Main Image Compliance Checklist

Before finalizing any main image:

- [ ] Pure white background (RGB 255, 255, 255)
- [ ] No text, logos, or graphics added (product's own branding is fine)
- [ ] No watermarks or badges
- [ ] Product fills 85%+ of the frame
- [ ] No lifestyle elements or props (main image only — secondary images more flexible)
- [ ] Image resolution at least 1000px on the longest side (ideally 2000px for zoom)
- [ ] All on-pack text matches the reference exactly
- [ ] Product accurately represents the actual physical product

---

## Common Gemini Issues and Fixes

| Issue | Don't Do This | Do This Instead |
|-------|--------------|-----------------|
| Wrong product details (shape, color, features, missing logo) | Try to describe the correction in the same chat | STOP → New chat with last good image (Golden Rule) |
| Gemini answers in text, no image | Re-send the same prompt | Start prompt with "Generate an image:" — or new chat |
| Context corruption (random topics, off-track responses) | Try to redirect | New chat immediately. Old context is poisoned. |
| Clipboard "not focused" error | Re-run from Gemini tab | Click the IMAGE tab page first, then re-run clipboard JS, then switch to Gemini |
| Looks too "AI-ish" | Add more complexity | Add "photorealistic, indistinguishable from real photography, natural lighting imperfections" |
| Product too small | Ask to "zoom in" (often distorts) | Re-prompt: "product fills 90% of the frame" |
| Background not pure white | Ask to "fix the background" | Re-prompt: "pure white background, RGB 255,255,255, no gradient, no off-white cast" |
| Garbled text on labels | Try to fix the text | Don't generate text — add labels in post-production (Photoshop/Canva) |
| Harsh shadows | Ask to "soften shadows" | Re-prompt: "extremely soft diffused shadow, barely visible, no hard edges" |
| Context element overwhelms product | Ask to "make it smaller" | Re-prompt with explicit sizing: "context element at 20% scale compared to product" |
| Wrong color count in multi-pack | Re-prompt vaguely ("show all colors") | List each color individually: "1 Black, 1 Gray, 1 Navy, 1 Red..." not "5 colors" |
| Form factor drifts after iteration (bag → pouch, bottle → tube) | Try to correct in same chat | New chat with last good image. Re-state form factor explicitly. |
| Model is on "Fast" not "Pro" | Send the prompt anyway | Check model picker EVERY time. Switch to Pro before any prompt. |
| Gemini adds callout text/labels not on the product | Ask it to remove | Explicitly add "No added text, no callout boxes, no benefit labels — only text physically on the product" |

For the full list of Gemini-specific failure patterns with detailed explanations, see `references/gemini-prompts.md`.

---

## Saving Output

To save a Gemini-generated image:
- Use Gemini's built-in **"Download full size image"** button (top of the generated image)
- OR right-click → "Save image as..."

Save with a clear filename: `concept-A-premium-render.png`, `concept-B-in-context.png`, etc.

Note: Gemini outputs are subject to cross-origin restrictions, so you can't reuse them via the clipboard-canvas method. To feed a Gemini output back into a new chat (per the Golden Rule), download locally and drag-drop or upload.

---

## Mode A: Autonomous (Claude in Chrome — recommended when available)

This is the autonomous path — Claude drives the Gemini tab end-to-end. The parent SKILL.md's Step 3b capability check has already confirmed you're here. If you somehow landed in this section without browser tools (`mcp__Claude_in_Chrome__*` prefix not present in your tool list), STOP and switch to **Mode B** below — never simulate browser actions without the tools.

### The operator loop, per concept

1. **Navigate to Gemini.** `navigate` to `https://gemini.google.com/`. If there's a sign-in wall, Google account picker, or captcha, **stop and hand off to the user** — never log into Google on someone's behalf (user_privacy: never authorize account access).

2. **Start a new chat.** Click "New chat" (top of the left sidebar, usually a pencil icon). Verify a fresh empty composer appears.

3. **Switch to Pro model — CRITICAL.** Every new chat defaults to **Fast**. Click the model picker (near the prompt input area, top of page or in the composer). Select **Pro** — NOT Fast, NOT Thinking. Verify Pro is selected before any prompt. If you skip this step, output quality drops sharply and the rest of the loop is wasted. Re-check the picker on every new chat — Gemini silently reverts the default.

4. **Attach the product image to Gemini — JS blob download from Drive + click-override on the dynamic file input + `file_upload`.** **Confirmed working 2026-04-29 via tester.** Clipboard-based paths (Ctrl+A/Ctrl+C, JS canvas + clipboard.write) ALL FAIL on Gemini specifically because **Gemini's composer ignores image paste events entirely** — confirmed under controlled test where the OS clipboard demonstrably contained image bytes and Ctrl+V produced no thumbnail. The Drive picker (formerly Path C) is also blocked by browser popup policy in the automation context. The path that works combines three mechanisms to fix each other.

   **Path A (preferred — confirmed working) — JS blob download + click-override + file_upload.**

   Three phases:

   **Phase 1 — Get image bytes onto host filesystem via JS-triggered blob download.**
   - `tabs_create_mcp` to `https://drive.google.com/file/d/<FILE_ID>/view`. The image loads inside Drive's viewer using the user's authenticated cookies, accessible via same-origin fetch.
   - `left_click` somewhere in the page body to focus the document.
   - `javascript_tool`:
     ```javascript
     (async () => {
       // Pick the LARGEST image — skips Google profile avatar (32x32),
       // favicons, and decorative icons. Drive's viewer has multiple
       // googleusercontent images including the user's avatar at index 0.
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
       return a.download;
     })();
     ```
     Return value is the downloaded filename. File lands in `C:\Users\marti\Downloads\<that-filename>` because Chrome treats `a[download].click()` as a real user-initiated download (not the JS-injected variety blocked by file:// policy).

   **Phase 2 — Open Gemini, install click-override, capture the dynamic file input.**
   - `tabs_context_mcp` to the Gemini tab (or `tabs_create_mcp` to `gemini.google.com` if not open). Confirm Pro model.
   - `javascript_tool` — install the click-override BEFORE clicking "Upload files":
     ```javascript
     (() => {
       window._capturedInput = null;
       const orig = HTMLInputElement.prototype.click;
       HTMLInputElement.prototype.click = function() {
         if (this.type === 'file') {
           window._capturedInput = this;
           return; // suppress the OS picker
         }
         return orig.apply(this, arguments);
       };
       return 'override installed';
     })();
     ```
     This neutralizes the `.click()` Gemini's "Upload files" handler makes on its dynamically-created `<input type="file">`. The input element is created and attached to the DOM, but the OS picker never opens.
   - `left_click` the **"+"** icon in the Gemini composer.
   - `left_click` "Upload files" in the menu. Gemini creates a fresh `<input type="file">` and fires its `.click()` — the override captures the input into `window._capturedInput` and suppresses the picker.

   **Phase 3 — Attach the captured input to the downloaded file.**
   - `javascript_tool` to verify the capture and assign a stable id:
     ```javascript
     (() => {
       const input = window._capturedInput;
       if (!input) return 'no-input-captured';
       input.id = input.id || 'cowork-captured-input';
       if (!document.body.contains(input)) document.body.appendChild(input);
       return input.id;
     })();
     ```
     If return is `'no-input-captured'`, the override didn't fire — verify the override was installed BEFORE the "Upload files" click. Re-install and retry.
   - `find` for the input by id, get a ref.
   - `file_upload` using that ref, path = `C:\Users\marti\Downloads\<filename-from-Phase-1>`.
   - Wait ~5 seconds, `read_page` to verify the thumbnail rendered AND no spinner. If thumbnail appears but spinner is stuck, dispatch the change event manually:
     ```javascript
     document.getElementById('cowork-captured-input').dispatchEvent(new Event('change', { bubbles: true }));
     ```

   **Multi-angle:** for each additional Drive link, repeat all three phases. Each Gemini chat needs a fresh capture — Gemini creates a new file input on every "Upload files" click.

   ---

   **Path B (TESTED-FAILED on Gemini 2026-04-29 — kept for diagnostic reference, may work on ChatGPT) — Direct image URL → Ctrl+A + Ctrl+C → switch tab → Ctrl+V.**

   - Extract `FILE_ID` from the user's Drive link (Step 2 already did this for the MCP fetch).
   - `tabs_create_mcp` to `https://drive.google.com/thumbnail?id=<FILE_ID>&sz=w2000`. Google's thumbnail endpoint — serves a high-quality JPEG and renders inline as a standalone page. More reliable than `uc?export=view` (observed redirecting to `drive.usercontent.google.com/download?...` for some files). If thumbnail returns 403 or doesn't render, fall back to `https://drive.google.com/uc?export=view&id=<FILE_ID>` and verify it actually shows the image before continuing.

   **Why this path is now demoted on Gemini:** the OS clipboard receives the image bytes correctly (verified via test), but Gemini's composer ignores the paste — no thumbnail, no error. This is a Gemini-side composer behavior, not a Cowork bug. Use Path A instead on Gemini.
   - **Wait for the image to actually finish loading before continuing.** Either sleep ~2 seconds, or `read_page` and confirm the image element is rendered. Skipping this caused a real bug in production: Ctrl+A fired before the new image was in the DOM, so the selection was empty and Ctrl+C snapshotted whatever stale content was already in the OS clipboard (a previous tab's URL).
   - `left_click` somewhere on the image area to focus the page.
   - `key: "ctrl+a"` — selects the image as a unit (on a standalone-image page, Ctrl+A grabs the image).
   - `key: "ctrl+c"` — OS-level keyboard event, copies image bytes to the OS clipboard.
   - `tabs_context_mcp` to switch to the Gemini tab.
   - `left_click` into the Gemini prompt input area.
   - `key: "ctrl+v"` — verify the thumbnail appears in the composer.
   - **Multi-angle:** for each additional image, `tabs_context_mcp` back to the Drive tab, `navigate` to the next direct image URL, **wait again** before click + Ctrl+A + Ctrl+C, switch to Gemini, Ctrl+V. The wait after every navigate is non-negotiable.

   **Path B (fallback if Path A doesn't render the image) — JS fetch + canvas re-encode + clipboard.write from inside the Drive viewer URL.** Works because the fetch runs same-origin from inside `drive.google.com`. **Caveat: tab-switching after `clipboard.write()` may lose the clipboard before Gemini's paste handler receives it** (Cowork's clipboard doesn't reliably bridge tabs in some sessions). Try once; if no thumbnail after paste, abandon to Path C.
   - `tabs_create_mcp` to `https://drive.google.com/file/d/<FILE_ID>/view` (the regular sharing URL).
   - **`left_click` somewhere in the page body to focus the document** — required for the Clipboard API to accept a write.
   - `javascript_tool` to run:
     ```javascript
     (async () => {
       // Pick the LARGEST image — skips Google profile avatar (32x32),
       // favicons, and decorative icons. Drive's viewer has multiple
       // googleusercontent images including the user's avatar at index 0.
       const imgs = Array.from(document.querySelectorAll('img'))
         .filter(img => img.naturalWidth > 100)
         .sort((a, b) => (b.naturalWidth * b.naturalHeight) - (a.naturalWidth * a.naturalHeight));
       const img = imgs[0];
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
     The PNG re-encode is mandatory — Clipboard API only accepts PNG for images.
   - Switch to Gemini, click composer, `key: "ctrl+v"`.

   **Path C (last fallback before giving up) — Click "+" in Gemini composer → "Add from Drive" → pick the file.** Native first-party integration. Often blocked because the Drive picker is rendered in a cross-origin iframe that Cowork's `find` returns `[BLOCKED: Cookie/query string data]` on. Worth trying if A and B fail, but abandon immediately on the first BLOCKED response — don't keep probing.

   **Path D (Amazon-URL flow only — no Drive link given) — Same-origin clipboard-canvas trick.** Same as Path B but on the Amazon image URL.

   **Path E (last resort) — Switch to Mode B paste-ready output.** After ONE failed attempt at each of A, B, and C, stop autonomous paths and produce the Mode B brief. Tell the user explicitly: *"Autonomous image attach to Gemini failed at [specific path]. Switching to Mode B. Here are 5 paste-ready prompts — open gemini.google.com yourself, click '+' → 'Add from Drive' to attach (which works for you because you have document focus), then paste each prompt."*

   Path A is the default in Cowork-driven runs that started from a Drive link. It's also the path that has empirically worked across both ChatGPT and Gemini in production runs.

   **Anti-patterns — known to fail with specific error signatures, do NOT try:**
   - `file_upload` returns success and a thumbnail placeholder appears, but the upload spinner never resolves → **Cowork's `file_upload` sets `input.files` programmatically but doesn't dispatch the `change` event that the AI tool's React handler listens for. The upload POST never fires.** Confirmed on ChatGPT 2026-04-29 via diagnostic (manual drag-drop of same file uploaded instantly). Likely identical issue on Gemini if `file_upload` ever does find an input. **Operating rule:** if the spinner is still spinning 30 seconds after `file_upload` reported success, abandon. Don't loop. Switch to Path A (Ctrl+A + Ctrl+C from direct image URL).
   - `file_upload` from any `AppData\Roaming\Claude\...` or `/tmp/...` path → returns `{"code":-32000,"message":"Not allowed"}`. Sandbox paths are blocked at the extension layer.
   - `file_upload` on Gemini's "Upload files" button → "Element is not a file input." (It's a `<button>`.)
   - `file_upload` on Gemini even with a real host Windows path → may still fail because Gemini's composer doesn't expose a persistent `<input type="file">` ref. Path A bypasses this entirely.
   - `navigator.clipboard.write()` from `javascript_tool` injection without first focusing the page → `NotAllowedError: Document is not focused`.
   - `canvas.toBlob()` on a Drive viewer's `<img>` element where src is `lh3.googleusercontent.com` and page is `drive.google.com` → tainted canvas SecurityError. Path B works around this by fetching same-origin first, then re-encoding through the canvas.
   - `fetch()` from `gemini.google.com` to a Drive endpoint → CORS-blocked.
   - Right-click on the image inside Drive's preview viewer → context menu suppressed.
   - `file://` URL navigation → Chrome extension permission blocks.
   - Local HTTP server in Cowork sandbox → networking namespaces don't bridge.
   - Looping the same path 3+ times — tab groups can destabilize, clipboard can clear on focus shifts, retry overhead exceeds the cost of falling through.

5. **Insert the prompt into Gemini's Quill editor — DOM `createElement` + `appendChild` on `.ql-editor`.** **Confirmed working 2026-04-29.** Gemini's composer is a Quill rich-text editor with a Trusted Types policy. The clipboard pattern that works for ChatGPT (`navigator.clipboard.writeText()` + Ctrl+V) **DOES NOT work on Gemini** — `clipboard.writeText` times out indefinitely (>45s, observed twice in production), `execCommand('copy')` from a hidden textarea returns false, and `innerHTML` injection is blocked by Trusted Types ("This document requires 'TrustedHTML' assignment"). The working pattern is direct DOM node creation with `textContent` (which bypasses Trusted Types because it's not HTML).

   **Method (only one that works on Gemini) — DOM createElement + appendChild on `.ql-editor`.**

   `javascript_tool`:
   ```javascript
   (() => {
     const editor = document.querySelector('.ql-editor');
     if (!editor) return 'no-editor-found';
     // Clear placeholder children
     while (editor.firstChild) editor.removeChild(editor.firstChild);
     // Split prompt on double-newlines into paragraph chunks
     const text = `<<FULL PROMPT TEXT HERE — must start with "Generate an image:", backticks-quoted, newlines preserved>>`;
     const paragraphs = text.split('\n\n');
     for (const para of paragraphs) {
       const p = document.createElement('p');
       p.textContent = para;  // textContent bypasses Trusted Types (innerHTML would be blocked)
       editor.appendChild(p);
     }
     // Remove the placeholder class so Gemini stops showing "Enter a prompt"
     editor.classList.remove('ql-blank');
     // Dispatch input event so Gemini's React/Quill handler picks up the change and activates the send button
     editor.dispatchEvent(new Event('input', { bubbles: true }));
     return 'inserted ' + paragraphs.length + ' paragraphs, ' + editor.textContent.length + ' chars';
   })();
   ```
   Verify the return: `'inserted N paragraphs, M chars'` matching the prompt length. If `'no-editor-found'`, Gemini's UI hasn't fully loaded — wait 2 seconds and retry.

   **Verify before sending.** `read_page` to confirm the prompt is in the composer. First three words must be "Generate an image:" — without that lead-in Gemini answers in text instead of generating. Last line should also be present (long prompts may scroll within the composer; check both ends).

   **Send the prompt.** Two methods, both confirmed working:

   **Method A (preferred) — `find` the send button by aria-label, click via ref.**
   - `find` for `button[aria-label="Send message"]` — get a ref.
   - Click via the ref. Confirmed working 2026-04-29.

   **Method B (fallback if click-by-ref doesn't fire) — `dispatchEvent` directly on the button.**
   - `javascript_tool`:
     ```javascript
     (() => {
       const btn = document.querySelector('button[aria-label="Send message"]');
       if (!btn) return 'no-send-button';
       btn.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
       return 'sent';
     })();
     ```
     `dispatchEvent` fires the click on the DOM element regardless of viewport visibility. Use this if the send button renders just below the visible viewport (~y=742 on a 735px-tall window) and coordinate clicks miss, or if `element.click()` reports success but the event doesn't fire.

   Verify the URL changes to a chat ID (e.g. `gemini.google.com/app/<chat-id>`) — that confirms submission and Gemini is processing.

   **What does NOT work on Gemini (confirmed-failed, do NOT try):**
   - `navigator.clipboard.writeText()` → times out indefinitely. Worked fine on ChatGPT but not here.
   - `document.execCommand('copy')` from a hidden textarea → returns false (CSP / missing real user gesture).
   - Setting `editor.innerHTML = text` → blocked by Trusted Types policy.
   - `element.click()` on the send button → inconsistent; reports success but Gemini's handler doesn't always fire.
   - Coordinate click on send button → unreliable due to off-screen rendering at narrow viewports.
   - `form_input` for multi-line prompts → newlines fire Enter and prematurely submit.

6. **Wait for generation.** Gemini Pro typically takes 30–90 seconds. Don't interact with the page during generation — clicking away can cancel it.

7. **Check the output.** Use `computer` screenshot or `read_page` to capture the rendered image. Run the identity checklist (Hard Rule 4 in the parent SKILL.md):
   - Text fidelity, logo geometry, container silhouette, color hierarchy, element count, quantity/size text — all must hold.
   - **If passed** → step 8.
   - **If small composition issue** (lighting, shadow, angle, single missing detail) → send a tight refinement prompt in the same chat. Sample refinements in the *Refinement Prompts* section above.
   - **If identity drifted** (wrong shape, wrong colors, missing logo, garbled text, extra elements) → **STOP**. Apply the Golden Rule: open a new chat, re-pick Pro, re-attach the **original Amazon product image** (NOT a Gemini output), and re-send. Hard Rule 6 + Golden Rule both apply.

8. **Download the image.** Use Gemini's "Download full size image" button (top of the image in the chat) — cleanest path. If unavailable, right-click → "Save image as". Save to a predictable path (project folder if available, otherwise `/tmp/gemini-ab-output-[brand]-[concept].png`). Verify with `bash_tool ls`.

9. **Move to the next concept.** Back to step 2. New chat. **Re-pick Pro** (default reverts). Re-attach the original product image via clipboard JS. Hard Rule 6 — never reuse a chat across concepts.

### Things Claude in Chrome must NOT do here

- Don't log into Google on the user's behalf. If the session is logged out, hand off. (user_privacy)
- Don't accept Google ToS / cookie banners / privacy updates without user permission. (explicit_permission)
- Don't navigate to `amazon.com` for any reason — Hard Rule 5 still applies, even though you're now in a browser-capable environment.
- Don't open any `sellercentral.amazon.*` tab — Hard Rule 0.
- Don't write to Notion from this flow unless the user explicitly asked in the current turn — Hard Rule 1.
- Don't click "Share" on a generated image or copy a public link without user permission.
- Don't click "Delete chat" on previous chats in the sidebar, even if they look stale — destructive.

### When the browser gets stuck (Gemini-specific)

| Symptom | Fix |
|---------|-----|
| "Sign in to continue" wall | Stop. Hand off to the user to sign in. |
| Captcha / account verification | Stop. Never solve captchas. |
| Model defaults to Fast on every new chat | Always re-pick Pro before each prompt. The default reverts. Use `read_page` to verify Pro is selected before sending. |
| Clipboard JS returns `SecurityError: tainted canvas` | Image is cross-origin (most likely a Gemini output). Save the source locally with `bash_tool curl ...` then use `file_upload` instead of clipboard. |
| Image generation pending forever (>3 min) | Refresh the page once and retry. If it fails twice, account may be rate-limited — hand off and tell the user to check their plan / wait for reset. |
| Gemini answered with text and no image | Prompt didn't start with "Generate an image:" or Gemini routed to a non-image flow. New chat, re-pick Pro, re-prompt with the exact "Generate an image:" lead-in. |
| Output looks low-quality / flat | Pro picker silently reverted to Fast. New chat, re-pick Pro, retry. |
| Context corruption (off-topic responses) | New chat immediately. Old context is poisoned and won't recover. |
| Pasted thumbnail doesn't appear after Ctrl+V | Either the click landed on the wrapper (not the editable composer) or the clipboard JS didn't actually copy. Re-run the clipboard JS, screenshot to verify the click target, retry the paste. |
| Prompt fired mid-typing — only "Generate an image:" or first line went out, rest stuck in composer | You used `form_input` (typing) instead of clipboard paste. The composer interprets the newline at the end of the first line as Enter and submits. **Fix:** always use the `navigator.clipboard.writeText` + `ctrl+v` two-step pattern in step 5. Never `form_input` a multi-line prompt. To recover from this specific incident: the partial response is useless — Hard Rule 6 + Golden Rule force a new chat. Open a new chat, re-pick Pro, re-attach the original product image, and re-send the full prompt atomically via clipboard paste. |
| Saved Gemini image fails to upload back to a fresh chat via clipboard | Cross-origin restriction. Download Gemini outputs locally first, then use `file_upload` from disk. |

---

## Mode B: Manual Paste Output (when Claude in Chrome isn't available)

You're here because Step 3b's capability check found no browser tools. Your job is to **produce a paste-ready brief the user can run themselves in `gemini.google.com`**, not to simulate browsing. The parent SKILL.md has already told the user this mode is what's running and offered them Cowork as the autonomous alternative — they declined or aren't set up yet.

### What to deliver to the user

Output a single, scan-friendly message containing five parts in this order:

**Part 1 — Setup instructions (one block, generic, applies to all 5 concepts):**

> *Here are 5 paste-ready prompts. For EACH concept (one fresh chat per image — no exceptions):*
>
> *1. Open `gemini.google.com` → click "New chat" (top-left of sidebar).*
> *2. **Switch to Pro model.** Every new chat defaults to Fast — Fast produces flat, unusable output for product photography. Click the model picker, select Pro. Verify Pro is selected before pasting anything. **This is the #1 reason Gemini results disappoint.***
> *3. (Optional, recommended) Type the brand name early in your first prompt so the chat auto-names usefully — or rename via the sidebar after the first message.*
> *4. Attach the original Amazon product image. Gemini doesn't accept direct OS image paste — use the clipboard-canvas JS in Part 2 below to copy from the Amazon image tab into your clipboard, then Ctrl+V into Gemini.*
> *5. Paste the prompt block (from Part 3) below the attached image.*
> *6. Send. Wait 30–90 seconds. Don't interact with the page during generation.*
> *7. Run the identity checklist (in Part 4) on the output.*
> *8. If the output passes: click "Download full size image" at the top of the image, or right-click → Save image as.*
> *9. If small composition issue (lighting, shadow, angle, single small detail): send a refinement prompt in the SAME chat (samples in Part 5).*
> *10. If identity drifted (wrong shape, wrong color, missing logo, garbled text): close the chat, open a NEW one, re-pick Pro, re-attach the **original Amazon image** (NOT a previous Gemini output), and re-send. **Don't try to fix identity drift in the same chat — Gemini's context corrupts and it gets worse.***
> *11. Repeat for the next concept in a fresh chat.*

**Part 2 — Clipboard-canvas JS for attaching Amazon images:**

Output the JS snippet from the *Attaching the Original Product Image* section above as a fenced code block. Tell the user:

> *Run this in the browser DevTools console while focused on the tab that has the Amazon product image open (right-click the main listing image → "Open image in new tab" first to get the full-resolution version). It copies the image to your clipboard. Then switch to your Gemini tab, click into the prompt area, Ctrl+V to paste.*
>
> *If the JS fails with a "tainted canvas" error, the image is cross-origin — save it locally instead and drag-and-drop into Gemini, or use Gemini's upload button.*

**Part 3 — One block per concept (5 blocks: A, B, C, D, E):**

For each concept, produce a fenced code block with this structure (filling in the actual values from Step 1 + Step 2 outputs — no template placeholders should reach the user):

```
Generate an image: [Brand] - A/B Experiment [Round] Concept [Letter].

Based on the attached product image, create a professional product photography shot of the [PRODUCT NAME].

PRODUCT: [full physical description: colors, materials, exact text on pack, logo placement, pack count if multi-pack]. Preserve every existing text and graphic on the packaging exactly. Render ONE (single) unit only [or for multi-pack: list each item explicitly: "1 Black, 1 Gray, 1 Navy, 1 Red, 1 Olive"].

CONCEPT: [Concept-specific composition — angle, framing, context elements, lighting mood from Step 2 output].

REQUIREMENTS:
- Pure white background (RGB 255, 255, 255)  [for compliant A/B/C — replace with scene description for lifestyle D/E]
- Product fills 85%+ of the frame
- Photorealistic — looks like a professional product photo, not AI art
- [Concept-specific style: soft studio lighting, rim light, etc.]
- [Concept-specific shadow treatment: barely visible diffused / natural in-context / etc.]
- Amazon main image compliant: no added text, no graphics, no callout boxes, no badges  [for A/B/C — relax for lifestyle D/E if the concept calls for overlay]

CRITICAL PRODUCT DETAILS TO GET RIGHT:
- [Detail 1 — character-exact on-pack text quote]
- [Detail 2 — logo placement / shape]
- [Detail 3 — color list, exact count, container shape, anything Gemini routinely drifts on]
```

Concepts D and E (lifestyle) replace "pure white background" with the actual scene description and relax the "no added text/graphics" rule. For comparison graphics specifically — Gemini handles these worse than ChatGPT regardless of prompt structure; consider recommending the user switch to ChatGPT for those concepts and stick with Gemini for primary + lifestyle.

**Part 4 — Identity checklist (Hard Rule 4, restated for the user):**

> *Identity (any fail → close chat, open NEW chat with original reference, do NOT fix in same chat — that's Gemini's Golden Rule):*
> *— Every word on the pack matches the reference exactly (no missing, invented, recased, translated).*
> *— Logo in same position on the same panel, same shape.*
> *— Container silhouette differences look like camera angle, not shape change.*
> *— Dominant label color matches; accent ratio matches.*
> *— Same number of label panels, badges, callouts, ingredient banners.*
> *— Quantity/size text exact ("60 GUMMIES" vs "60 Gummies" matters).*
> *— Only one unit (unless legitimately a multi-pack).*
>
> *Composition (allowed to drift — refine in same chat):*
> *— Camera angle, focal length, lighting direction, shadow length, scene background, props, framing crop.*

**Part 5 — Sample refinement prompts (paste-ready, fenced code blocks):**

Pull from the *Refinement Prompts* section earlier in this file. Include at minimum: make-product-bigger, fix-lighting, add-context-element, simplify, fix-shadow, reduce-to-one-unit. Each should be one paste-ready block the user can drop into the same chat for small fixes.

### Mode B operating principles

- **Don't generate prompts in a vacuum.** PRODUCT, CONCEPT, REQUIREMENTS, and CRITICAL PRODUCT DETAILS for each of A–E come from Step 1 + Step 2 outputs. Stitch the actual concept brief into each prompt — never ship template placeholders like `[Detail 1]` to the user.
- **Always include "Generate an image:" at the very start of each prompt.** Without it, Gemini may answer in text instead of generating. Non-negotiable.
- **Always remind the user to switch to Pro.** Gemini's Fast default is the #1 reason "this skill didn't work for me" — flag it in Part 1 setup AND in any error tip the user might hit.
- **Don't include browser-driving operator instructions.** Mode A had paste-ready coordinates and tool calls for autonomous browser control; Mode B is paste-ready text for a human.
- **Format for scanning.** Headings for each part, fenced code blocks for everything paste-ready (Parts 2, 3, 5), plain prose only for the surrounding instructions in Parts 1 and 4. The user is going to copy out of this — don't make them work to find boundaries.

---

## Quick-Start Checklist

Before sending any Gemini prompt:

- [ ] Chat renamed to `[Brand] - A/B Experiment [Round] Concept [Letter]` (or set up to auto-name with brand name in the prompt)
- [ ] Model switched to **Pro** (not Fast, not Thinking) — verify EVERY new chat
- [ ] Original Amazon product image attached via clipboard-canvas paste
- [ ] Prompt starts with "Generate an image:"
- [ ] Prompt includes the four mandatory expectations (preserve text / one unit / pure white background / no added text)
- [ ] Critical product details called out explicitly (zipper direction, logo placement, exact color list)
- [ ] No real competitor brand names in the prompt

After generation:

- [ ] Identity checklist (Hard Rule 4) all green
- [ ] On-pack text legible and character-exact
- [ ] Only one unit rendered (or correct multi-pack count)
- [ ] Background truly pure white (for main images)
- [ ] No added overlay text, badges, watermarks
- [ ] Product fills 85%+ of frame (for main images)
- [ ] Saved with clear filename
- [ ] Upscale to 2000px longest side before handoff if going straight to listing

If any "After generation" check fails on identity → Golden Rule: STOP, new chat, last good image as seed.
