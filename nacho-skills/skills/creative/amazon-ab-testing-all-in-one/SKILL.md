---
name: amazon-ab-testing-all-in-one
description: "Complete Amazon A/B testing workflow — competitor research, concept ideation, and AI image generation via ChatGPT (GPT-image-1) or Gemini. Use whenever the user wants to run an A/B test for Amazon listing images, research competitors from a user-supplied PDF/screenshot, generate images with ChatGPT or Gemini, improve CTR/CVR/TACOS, or produce primary/lifestyle/features/benefits/comparison/instructional graphics. Works across every product niche and every Amazon marketplace. Trigger on: A/B test, split test, main image, listing image, CTR, CVR, TACOS, competitor research, image strategy, ChatGPT product image, GPT-image, DALL-E, Gemini image, AI product image, Us vs Them, features graphic, benefits graphic, comparison graphic, instructional graphic, packaging-as-hero, JSON master prompt. Also trigger when an ASIN is shared and the user wants new image concepts."
---

# Amazon A/B Testing — Complete Workflow

End-to-end system for creating winning Amazon listing images through A/B testing. Three steps: research, ideate, generate. Step 3 forks by tool — ChatGPT (GPT-image-1) or Gemini — and you ask the user which one before generating.

Skip a step and you're guessing instead of testing.

---

## Hard Rules — Read Before Anything Else

These override any later guidance. Non-negotiable.

### Rule 0 — Never Interact with Seller Central
Do not open, navigate to, click inside, or interact with any `sellercentral.amazon.*` tab. All Seller Central actions — running experiments via Manage Your Experiments, editing listings, checking ad metrics — are performed by the user manually. Hand off clearly: *"User: run this in Manage Your Experiments."*

### Rule 1 — Never Write to Notion Without Explicit Permission
Reading Notion for context (prior test results, playbooks) is fine. Writing to Notion — creating pages, updating database rows, posting comments — is not, unless the user explicitly asks in the current request. Results logging is a manual step; produce the entry as text the user can paste in.

### Rule 2 — Drive End-to-End, Hand Off ONLY on Auth Walls

Drive the workflow autonomously through research, ideation, and generation. Stop ONLY on:

- An actual login wall, captcha, or account picker that physically blocks the next action.
- Actions Hard Rule 0 (Seller Central) or Hard Rule 1 (Notion writes) forbid.

The workflow is pre-authorized. **Do NOT:**

- **Offer Mode B as an alternative when Mode A is available.** Mode B exists only for environments without browser tools. When `mcp__Claude_in_Chrome__*` tools are present, Mode A is the only path — never present "I can drive it OR hand you paste-ready prompts" as a choice. The choice has already been made by the capability check.
- **Ask the user to "say the word", "say go", or "confirm before I start".** They invoked the skill — that's the go signal. Don't manufacture a confirmation step that the workflow has already resolved.
- **Preemptively ask if they're logged in.** Just `navigate` to the target. If a login wall appears, THEN hand off (*"You're logged out of [tool] — please log in, then say 'continue'."*). Asking before trying wastes a turn and breaks autonomy.
- **Recap the workflow at decision points.** Step 1 and Step 2 outputs already covered what's happening. Don't restate "I'll open chats, attach images, paste prompts, run generations, run identity checks, save…" — just do it.
- **Self-narrate or apologize for thinking.** Phrases like *"My bad — I read the reference and then dropped the thread"* or *"I've been overthinking this"* are friction. Act on the reference; don't narrate the process.
- **Pause for permission to do anything covered by Steps 1–3 of this skill.** All those actions are pre-authorized.
- **Run a question ladder for facts visible in attached files.** If the user has dropped a product image, screenshot, or listing PDF, extract product name, form factor, colors, pack count, branding, packaging details, on-pack text, and main keyword directly from the file. Present what you extracted as a single confirm-block (*"Here's what I see — correct anything wrong"*). Don't ask *"What's the form factor? What colors? How many in the pack?"* line by line. The Pre-Flight Read in Step 2 is the canonical pattern.

**Graceful degradation when inputs are partial.** If the user gives less than the skill ideally needs, proceed with what you have and **flag the limitation explicitly** — don't block, don't keep asking, don't refuse.

The two truly-required gates (cannot work around):

1. **Step 1 search-results screenshot/PDF** — Rule 5 forbids navigating Amazon. Without it, Step 1 produces no output. Ask once. If the user still doesn't provide it, offer to skip Step 1 and proceed with Step 2 using only the user's product image + general category knowledge (output will be weaker but possible).
2. **Step 2 product reference image bytes** — Hard Rule 3 forbids text-only generation. Without bytes, Step 3 cannot run. Ask once via the Drive-link prompt. If the user still doesn't provide the image, you can still produce **concept strategies** (Step 2 written brief) but explicitly flag: *"I can produce the 5-concept written brief without the image, but Step 3 image generation requires the actual product reference. We can run Steps 1–2 now and circle back to Step 3 once you share the image."*

Everything else is a nice-to-have. When a nice-to-have is missing (specific concept preference, brand context, marketplace, multi-angle reference, etc.), produce the best output with what you have and append a one-line caveat: *"I went with [defaulted value] based on [extraction] — if you meant [alternative], say so and I'll re-run."* Then proceed. **Don't iterate field-by-field through nice-to-haves** — that's the question-ladder anti-pattern in disguise.

The framing for the user when inputs are sparse: *"I'll do my best with what's given. Output would be sharper with [specific missing input] — but I can ship a useful first pass without it."* Then ship.

If you're tempted to ask *"shall I proceed?"* anywhere in this workflow — don't. The answer is yes. Proceed.

### Rule 3 — Always Attach the Original Product Image(s) as Reference

Never generate from text description alone. Always attach real Amazon product photos as vision input — this applies whether the tool is ChatGPT or Gemini. On restarts, start from the original — never feed a previous AI output back as the seed once product identity has drifted. Multi-angle reference (2–3 images) sharply improves identity preservation. If only one image is available, use the paranoid PRODUCT block pattern documented in the Step 3 reference file.

**Image acquisition order** (when the user provides a Google Drive link instead of pasting/uploading the image directly):

1. **Try the Google Drive MCP first.** Inspect your tool list for Drive-shaped tools — look for names ending in `__download_file_content`, `__read_file_content`, `__get_file_metadata`, or `__search_files`. Tool prefixes vary per install (e.g. `mcp__<uuid>__download_file_content`); pattern-match the suffix. Extract the file ID from the URL — common patterns: `drive.google.com/file/d/<ID>/view`, `drive.google.com/open?id=<ID>`, `drive.google.com/uc?id=<ID>`, `docs.google.com/.../<ID>/...` — and call the download tool with that ID. Save the bytes to a predictable local path (e.g. `/tmp/abtest-<brand>-ref-<n>.png`).
2. **Fall back to Claude in Chrome** if the Drive MCP isn't connected, the file isn't shared with the MCP's auth scope, or the download errors. `tabs_create_mcp` opens the Drive link, wait for the preview to render, then either `computer` screenshot the image at full resolution OR find the Drive download button (top-right toolbar) and trigger a browser download. Save to the same `/tmp/abtest-...` path. (Note: Drive's download button on shared images requires the user to have view-or-higher permission on the file.)
3. **Hand off to the user** only if both paths fail: *"I can't reach this Drive file via the Drive MCP or in the browser — please share view access with me, or paste the image directly into chat."*

**What to NOT do at this step (Hard Rule 2 in practice):**

- Don't ask the user to "make sure the link is shared" before trying. Try first; ask only on actual failure.
- Don't ask the user to paste the image directly when a Drive link is present and Drive MCP / browser tools are available.
- Don't ask the user to also paste/upload the image into chat after a successful Drive fetch. The local `/tmp/abtest-...png` bytes are the canonical reference — use them directly for Pre-Flight Read vision input AND for Mode A `file_upload` into ChatGPT/Gemini.
- Don't proceed without real image bytes. The skill always operates on real reference images, never on text descriptions of images.

### Rule 4 — Identity Guardrails (Binary Checklist)
The #1 failure mode is the product "shifting" between generations. Use this binary checklist on every output. **Any single identity fail → start a new chat from the original reference.** Composition issues stay in chat for refinement.

**Identity (any fail = restart):**
- **Text fidelity** — every word in the reference appears character-exact, same case, same order. Missing word, invented word, recased word, translated copy = fail.
- **Logo geometry** — same position on the same label panel; brand mark recognizable. Logo moved to a different face = fail.
- **Container silhouette** — outline overlay differences should look like camera angle, not shape. Pouch became box, neck slimmer, cap rounded vs flat = fail.
- **Color hierarchy** — dominant label color and accent ratio match. Lighting drift OK; category drift (red→orange, navy→black) = fail.
- **Element count** — same number of label panels, badges/seals, callouts, ingredient banners. Missing or invented = fail.
- **Quantity/size text** — "60 GUMMIES", "30 ML", "Net Wt 8 oz" must match exactly. Breaks more than people realize and silently lies to customers.

**Composition (allowed to drift, that's the point):**
- Camera angle, focal length, lighting direction, shadow length, scene background, props, framing crop.

### Rule 5 — Research Input Is Always a User-Supplied PDF/Screenshot (All Environments)
Claude **never** navigates to `amazon.com` for competitor research. **This applies in every environment** — claude.ai chat, Claude in Chrome, Cowork, any other agentic setup. Even when a browser tool is available and `amazon.com` is reachable, Claude does not use it for Step 1. The user always supplies a **PDF or screenshot** dropped into the chat. If no file is attached, stop and ask — don't work from category knowledge alone, don't `web_fetch`, don't `navigate`, don't pretend to have browsed. Covers public `amazon.com` product/search pages and `sellercentral.amazon.*` (Rule 0 already forbids the latter).

### Rule 6 — One Image = One Chat (Both Tools)
Every concept, every variant, every refinement-that-isn't-a-tiny-tweak gets its own fresh chat, opened from scratch, with the original Amazon product reference re-attached. This applies to both ChatGPT and Gemini.

Why: image models carry visual memory across turns. Asking for Concept B in a chat that already rendered Concept A anchors the model to Concept A's composition, not the original pack reference. Identity drifts 5–15% per turn — invisible in a single output, obvious when you line concepts up side-by-side. In-chat "regenerate" or "redo with new spec" is a trap.

The narrow exception: tight tweaks to the **same** concept ("same shot, softer rim light", "move the cap 10% right"). Those stay in chat. The moment instruction materially changes composition, angle, subject arrangement, or creative intent — open a new chat, re-attach the original reference, rename the chat correctly, send ONE concept prompt, download, close.

If you're tempted to skip this because re-attaching is tedious, that tedium is the price of identity integrity. Pay it every time.

---

## Why This Workflow Works

The best A/B test ideas don't come from guessing. They come from (1) studying what's already winning in the category, (2) combining that with patterns proven across hundreds of real tests (see `references/patterns.md` — Glow C Beauty Kit, Santino's turmeric soap, Daian's Swedish Dishcloth, Macray's comparison, Petra's polling, and others — actual test sources, not vibes), and (3) generating high-quality concepts with AI.

ChatGPT and Gemini both work for Step 3. Their strengths differ:

- **ChatGPT (GPT-image-1)** — better identity preservation when given multi-angle reference, reliable in-chat refinement for small tweaks, parses structured JSON prompts (the JSON `master_prompt` pattern enables multi-module compositions like Us-vs-Them comparison graphics).
- **Gemini Pro** — works on a clipboard-canvas paste flow on Amazon images, slightly weaker on consistency across iterations, golden rule is "if it drifts, stop and start fresh from the last good image."

The choice happens at Step 3. Step 1 and Step 2 are tool-agnostic.

---

## STEP 1: Competitor Research

**Hard rule (Rule 5):** Research is **always** done from a PDF or screenshot the user drops into this chat. Claude does not navigate to Amazon in any environment.

If the user hasn't attached a PDF/screenshot, STOP and ask:

> *"Drop a PDF or screenshot of `amazon.com/s?k=[keyword]` showing the top 2–3 rows of results. I don't pull it from Amazon myself — the research runs off what you send me."*

Don't start Step 1 without the file. Don't work from general category knowledge. Don't try to work around the rule via cached pages, archives, or third-party scrapers.

### Once the file is attached

1. **Read it carefully.** Focus on the top 8–12 organic results (first 2–3 rows on desktop search). Note Best Seller / Amazon's Choice badges if visible.
2. **Be honest about what's readable.** Zoomed-out screenshots often have unreadable titles and small copy at thumbnail scale. You can reliably read **visual patterns** (colors, compositions, floating elements, jar shapes, label density) but may not be able to read on-label text or competitor titles cleanly. When that happens, flag it: *"I can read visual language but not specific competitor titles/copy at this zoom — ask for a closer-crop screenshot if title-level keyword patterns matter."*
3. **Analyze:** what they show (product only / product + packaging / product + context), visual quality (professional / amateur / rendered), composition (clean / cluttered / white-bg compliant), text/callouts on-label, context elements (floating product, ingredients, people, props), color palette patterns.
4. **Identify patterns and gaps:** what winners share, what nobody is doing (those are opportunity spaces).

### Output Format

```
## Competitor Image Analysis: [KEYWORD]

### Category Overview
[2–3 sentences on what the typical main image looks like]

### Top Performers
1. [BRAND] — [What makes their image work]
2. [BRAND] — [What makes their image work]

### Common Patterns
- [Pattern 1]
- [Pattern 2]

### Gaps & Opportunities
- [Opportunity 1 — something nobody is doing]
- [Opportunity 2]

### Mistakes the current main image is making
- [Mistake 1]
- [Mistake 2]

### Recommendations for Testing
[2–4 specific ideas ready to develop into concepts in Step 2]
```

Flag inferred vs. read-from-screenshot content: *"(inferred from category knowledge — screenshot too zoomed to confirm)"*. Honesty about evidence quality beats overclaiming.

### Tips
- **Think like a shopper.** Which thumbnail grabs your eye scanning the row? That gut reaction is data.
- **Mobile matters.** Most Amazon shopping is on phones — thumbnails are tiny. Details that look fine at desktop scale may be invisible.
- **#1 Best Seller deserves close study.** They're #1 for a reason.
- **Premium-look ↔ price.** Premium-looking images often command higher prices in the same category. A $17.99 product with a $30-looking image has an advantage.

---

## STEP 2: Concept Ideation

Turn competitor research and proven patterns into concrete A/B test concepts.

### Inputs

1. **Product reference image(s)** — actual image bytes. Hard Rule 3 forbids generating from text descriptions alone. Acquired via the next subsection if not already in chat.
2. **Competitor research** from Step 1 — what's working, what's not, where the gaps are.
3. **Pattern library** — read `references/patterns.md` for the full catalog with cited test sources.

### Get the product reference image(s) — ask for Google Drive links explicitly

Concept generation needs actual image bytes. If the user hasn't already pasted or uploaded product images in this chat, ask for them explicitly:

> *"Drop the Google Drive link(s) to your product images. Multi-angle (front + back + side, or front + label close-up) is best — single image works but expect more identity drift in Step 3. 2–3 angles ideal."*

When Drive links come in, follow the **Image acquisition order** in Hard Rule 3: try the Google Drive MCP first (pattern-match `__download_file_content` / `__read_file_content` tool suffixes), fall back to Claude in Chrome (`tabs_create_mcp` → wait for preview → screenshot or download), hand off only if both paths fail. Save bytes to `/tmp/abtest-<brand>-ref-<n>.png`.

If the user pasted or uploaded images directly into the chat, you already have the bytes — skip the ask, move straight to the Pre-Flight Read.

**Once the bytes are saved locally (`/tmp/abtest-<brand>-ref-<n>.png`), that file IS the canonical reference image for the rest of the workflow.** Use it directly for the Pre-Flight Read (vision input from the local file) and for Mode A image attachment in Step 3 (`file_upload` the same `/tmp` path into the ChatGPT or Gemini composer). Do NOT ask the user to also paste or upload the image into this chat — that's redundant work for them and violates Hard Rule 2.

**If the user proceeds without providing the image** (e.g., says *"just go"* or *"do your best"* without a Drive link or upload): apply Hard Rule 2's graceful-degradation rule. You can still produce the Step 2 written concept brief — pattern selection, hypothesis statements, mistake mappings — using just Step 1 research and category knowledge. But explicitly flag: *"I'll produce the 5-concept brief now without the product reference. Step 3 image generation needs the actual image — share a Drive link or paste when you have it, and I'll run Step 3 then. The brief itself I can ship now."* Don't keep asking. Don't refuse. Ship the brief, mark Step 3 as pending.

Don't ask the user to "describe the product" or "tell me about the packaging" as a substitute for the image — that violates Hard Rule 3 and produces unreliable concept briefs anyway.

### Core Principles

**1. Simplicity wins almost always.** Cleaner versions win 20:1 in polls. One brand doubled CVR by removing visual noise. Rule: if you can remove an element without losing critical info, remove it. BUT: "simple" ≠ "show fewer items than the customer is buying." For a 5-pack, all 5 in a clean arrangement IS simple. Removing 4 to show 1 is misleading.

**2. Premium look = premium clicks.** Images that look like high-end 3D renders outperform flat photos. Direct competitor test: same price/ratings/size, the bottle with better highlights outsold by 50%.

**3. Show the product in context.** Products in use outperform isolated shots. Food containers with food beat empty ones. Pet products with Golden Retrievers / French Bulldogs beat generic. Context elements must be **logically connected** to the product (no random props).

**4. AI-generated images are a competitive advantage.** Well-prompted AI matches or beats professional photography. One AI mattress protector hit 71% preference over the original.

**5. Iterate relentlessly.** The biggest wins come from multiple rounds. Plan for 3–4 A/B tests, not one.

**6. Shadows must be flawless.** Visible edge artifacts, unrealistic angles, harsh cutout lines destroy trust. If it's not perfect, skip it.

**7. Text hierarchy.** Column layouts beat horizontal for benefit callouts (29:5 in testing). Key text must pop at thumbnail size on mobile.

**8. Consistency across concepts.** When generating multiple concepts for the same product, the product itself must look identical in every image — same colors, same branding, same form factor, same pack count. Only composition/arrangement/angle/context change.

### Strict Rules — Never Break These

These are non-negotiable on every prompt and every output.

- **Never change actual packaging.** Shape, structure, material, design stay exactly as in the real product.
- **Never change actual colors.** Burgundy stays burgundy. 5 colors means exactly those 5 — not 4, not 6, not "similar".
- **Never change form factor.** A bag stays a bag, not a box. A bottle keeps its shape.
- **Verify actual unit count.** Check the listing title + images + badge before any prompt. 5-pack = show 5. Single = show 1.
- **Product fills maximum space.** If there's empty space in the frame, the product isn't big enough. ~85–90% of frame.
- **Added details must connect to the product.** Written ON / attached TO / part of packaging / what goes INTO / key INGREDIENT. Random props not allowed.
- **Never add text that isn't on the physical product.** No callout boxes, benefit labels, feature text, or watermarks. The only text is what's physically printed on the packaging. Amazon prohibits added text/graphics on main images; for secondary images add text in post (Canva/Photoshop), not via AI.
- **Results must be consistent across concepts.** Same colors, same branding, same form, same pack count across A/B/C/D/E. Only composition/arrangement/context changes.

### Pre-Flight Read (extract from the attached product image — do NOT ask the user line-by-line)

Read the product image yourself and produce a single confirm-block. Every field below must come from the image, the listing title, or both. Only ask the user when something is genuinely ambiguous or missing.

Output to the user as ONE block they can correct in one line:

> *"From the image I'm seeing:*
> *— Product: [name from label]*
> *— Form factor: [bag / bottle / box / tube / pouch / etc.]*
> *— Colors: [every distinct color visible]*
> *— Pack quantity: [N units — from image or listing title, say which]*
> *— Branding: [logo placement, brand name, key label text]*
> *— Packaging details: [lid / handle / zipper / closure / material]*
> *— Full target keyword on pack: [yes / no, based on what's readable on the label]*
> *— Main keyword to test: [inferred from listing title — say where you got it]*
>
> *Proceed, or correct anything wrong?"*

Wait for ONE line of correction (or *"proceed"*), then move to concept generation. **Do NOT** ask any of these as separate questions.

If the image isn't readable enough to extract a field (zoomed too far out, label illegible, color washed by lighting), say so explicitly inline: *"Pack quantity unclear from the image — listing title says 5-pack, confirm?"*. Don't fill in a silent guess.

The constants — what CAN change (composition, lighting, angle, context) vs what CANNOT change (shape, colors, pack count, branding, form factor) — are the Strict Rules below, not user input. Don't ask about them; they're constraints the workflow enforces by default.

### Concept Generation — 5 Concepts (3 Compliant + 2 Lifestyle)

Default split:

- **Concepts A, B, C** — main-image compliant (pure white, no overlay text, product fills ~85–90%)
- **Concepts D, E** — lifestyle / action / contextual — secondary-image creative freedom

### Sixth slot — Packaging-as-Hero (when applicable)

Add as first-class when **any** of these hold:
- Full target keyword does NOT appear on the actual product unit
- Competitors in the category use boxes on main image
- Pure-product concepts feel too similar to each other

Two variants:
- **Closed-box hero + 2–3 unit accents** leaning against it. Box front = smile/category graphic + full keyword headline + quantity callout.
- **Open-box reveal** — lid flipped 110°, units fanning outward.

Tool note: split the PRODUCT block in the prompt into two — tight "preserve exactly" block for the unit (reference-locked) and verbose "build from scratch" block for the box (the model is inventing it). Reference-lock applies ONLY to the unit, not the invented box.

### Each concept must include

- **Concept name** — descriptive
- **Hypothesis** — what you expect and why. Specific: *"This will increase CTR because…"*
- **Changes from current** — every specific change (add, remove, modify)
- **Based on** — which `references/patterns.md` entry or test result supports this (cite by name)
- **Why it fits THIS product** — connect the pattern to the specific category
- **Mistake mapping** — name which Step 1 *Mistake* or *Gap* this concept addresses. If it can't be mapped, cut it and replace.

### Prioritize Test Order

Rank by:
1. **Diagnosed-mistake coverage** — how many Step 1 mistakes does this concept fix?
2. **Expected CTR delta** — main-image compliance fixes (size, framing, white-bg) usually dominate. Creative angle changes are smaller deltas, higher variance.
3. **Confidence the gap is real** — read-from-screenshot evidence beats inferred-from-category-knowledge.
4. **Execution risk** — concepts with lots of invented packaging carry more identity-drift risk. Penalize.

Test order = highest expected delta × highest confidence first. Manage Your Experiments only runs one variant vs control at a time, so order is the actual decision.

### Output Format

```
## A/B Test Concepts for [PRODUCT NAME] — [MARKETPLACE]

### Current State
[Brief description of current main image and its strengths/weaknesses]

---

### Concept A: [Name]
**Hypothesis:** [What you expect and why]
**Changes from current:**
- [Change 1]
- [Change 2]
**Based on:** [Pattern name + cited test]
**Why it fits:** [Specific reasoning]
**Addresses Step 1 Mistake:** [#X — which mistake from research]

---

### Concept B …  (same format)
### Concept C …
### Concept D …  (lifestyle)
### Concept E …  (lifestyle)

---

### Recommended Test Order
1. **Test first:** [Concept X] — [Why]
2. **Test second:** [Concept Y] — [Why]
…

### What to Measure
- **CTR** (Click-Through Rate) — Does the thumbnail attract more clicks?
- **CVR** (Conversion Rate) — Does the full image help convert?
- **TACOS** (Total Advertising Cost of Sales) — Does overall efficiency improve?

Run each test for at least 2 weeks with sufficient traffic before calling a winner.
```

---

## STEP 3: AI Image Generation — Choose Your Tool, Then Pick a Mode

Concepts are ready. Step 3 has two decision points: (1) which image tool, (2) whether you can drive that tool autonomously or have to hand the user paste-ready prompts.

### 3a. Ask which tool

Send this verbatim before generating anything:

> *"5 concepts ready. Which image tool are we generating with?*
> ***1.** ChatGPT (GPT-image-1) — best identity preservation with multi-angle reference. Required for JSON `master_prompt` comparison graphics (Us vs Them).*
> ***2.** Gemini Pro — works if you only have Gemini access. Slightly weaker on consistency; uses clipboard-canvas paste from Amazon image tabs.*
>
> *Default if you don't say: ChatGPT (2.0)."*

Wait for the user's pick.

### 3b. Capability check — autonomous vs manual

Before generating, check whether you have **Claude in Chrome** browser tools available. Look for tools with the `mcp__Claude_in_Chrome__` prefix in your tool list — `navigate`, `find`, `computer`, `read_page`, `form_input`, `file_upload` are the load-bearing ones. If those are present in your tool schema, you're in autonomous mode. If not, you're in manual-paste mode.

**If browser tools are available → Mode A (Autonomous). Announce in ONE sentence, then immediately start the operator loop.**

Send exactly this (substitute the tool name, concept count, save path — nothing else):

> *"Generating [N] concepts in [ChatGPT / Gemini] now — one fresh chat per image, original reference re-attached each time, outputs saving to [path]."*

Then proceed directly to the Mode A operator loop in `references/step-3-[tool].md`. The first concrete action is `navigate` to `chatgpt.com` or `gemini.google.com`. If — and only if — a login wall appears during that navigation, hand off: *"You're logged out of [tool] — please log in, then say 'continue'."*

**What NOT to do at this branch (Hard Rule 2 in practice):**

- Don't offer Mode B as an alternative ("…or I can hand you paste-ready prompts if you'd rather"). The capability check has already resolved the choice — Mode A is the only path when browser tools are present.
- Don't ask the user to confirm they're logged in. Try first; ask only on actual failure.
- Don't ask for the save path or filename convention. Default to project folder if available, else `/tmp/[tool]-ab-output-[brand]-[concept-letter].png`. State the path in the announcement; don't ask.
- Don't recap the workflow ("I'll open chats, attach images, paste prompts, run generations, run identity checks, save outputs…"). The user already sat through Steps 1 and 2 — they know the shape.
- Don't end with "say the word and I'll go" or any variant. Hard Rule 2 forbids manufactured confirmation steps.

**If browser tools are NOT available → Mode B (Manual Paste).** Tell the user verbatim:

> *"I don't have browser-driving tools in this environment, so I can't generate images directly. Two paths:*
>
> *1. **For autonomous generation:** install **Cowork** with the **Claude in Chrome** plugin. That gives me browser tools and I can drive [ChatGPT / Gemini] end-to-end — paste images, generate, review, download. Best path if you're producing many images per round, or if you want me to run the identity checks for you.*
>
> *2. **For manual generation right now:** I'll output all 5 concept prompts as paste-ready text blocks. You handle paste / generate / download yourself in [ChatGPT / Gemini]. Takes you ~5–10 minutes per image but works in any environment, including this chat.*
>
> *Which do you prefer?"*

If they pick (1), **stop generating** — wait for them to set up Cowork before proceeding.
If they pick (2), follow the **Mode B: Manual Paste** section in the matching Step 3 reference file.

### 3c. Load the matching tool reference

- **ChatGPT** → load and follow `references/step-3-chatgpt.md`. That file is the canonical Step 3 operator manual for GPT-image-1: prompt structure, JSON `master_prompt` for comparison graphics, the four mandatory prompt blocks, the reference-lock pattern, the paranoid PRODUCT fallback for single-reference cases, the 6-graphic-type template library (primary / lifestyle / features / benefits / comparison / instructional), refinement prompts, common issues. **Mode A** = autonomous Claude in Chrome operator loop. **Mode B** = paste-ready prompt brief for the user.
- **Gemini** → load and follow `references/step-3-gemini.md`. That file covers: Gemini Pro model selection, the clipboard-canvas JS for pasting Amazon images, the golden Rule (stop and restart from last good image on drift), prompt structure, the prompt template library, refinement prompts, and Gemini-specific failure modes. **Mode A** = autonomous Claude in Chrome operator loop. **Mode B** = paste-ready prompt brief for the user.

Both references inherit Hard Rules 0–6 from this parent SKILL.md. Don't restate them in Step 3 — they apply by default.

---

## After All Concepts Are Generated — Handoff

1. Review all 5 generated concepts against the brief and the compliance checklist in the Step 3 reference.
2. Present them to the user (brief + inline preview images) with a short summary per concept.
3. Get user approval on which concepts to take forward.
4. User downloads final images via the tool's download button.
5. Optional: upscale to 2000px for zoom capability (Topaz Gigapixel, Photoshop Preserve Details 2.0, Let's Enhance — GPT-image-1 caps at 1024–1536; Gemini Pro at native generated size).
6. **User handles everything past this point.** That includes:
   - Posting concepts in the team channel with a "1, 2, 3, … or current?" poll (always include the current main image as baseline — that's the whole point of the vote)
   - Running the A/B test in Seller Central's Manage Your Experiments (user does this — Rule 0)
   - Logging results in the Notion A/B Testing database with CTR Before / CTR After / Successful / Status (user does this — Rule 1)

The skill's role ends at "concepts delivered, user briefed." Never navigate Seller Central or write to Notion from this skill.

---

## References

- `references/patterns.md` — Full catalog of proven A/B testing patterns from real tests, organized by category, with cited sources (Glow C Beauty Kit, Santino's turmeric soap, Swedish Dishcloth, Macray's comparison, Petra's polling, etc.). Read before generating concepts.
- `references/step-3-chatgpt.md` — Canonical Step 3 operator manual for ChatGPT / GPT-image-1. Loaded when the user picks ChatGPT in Step 3. Includes JSON `master_prompt` pattern, 6-graphic-type templates, paranoid single-reference PRODUCT block, Claude-in-Chrome operator loop.
- `references/step-3-gemini.md` — Canonical Step 3 operator manual for Gemini Pro. Loaded when the user picks Gemini in Step 3. Includes Pro model setup, clipboard-canvas JS, the golden Rule 4 (stop-and-restart), Gemini prompt templates.
