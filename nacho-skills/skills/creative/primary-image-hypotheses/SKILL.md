---
name: primary-image-hypotheses
description: >-
  Generate CTR-boosting Amazon PRIMARY (main / hero) image hypotheses for a product, grounded in Sophie Society's Main Image Best Practices. Produces 5 distinct test concepts, each with a paste-ready image-generation prompt for nano banana pro / ChatGPT Images and guidance on which reference photo to attach. Use this whenever someone wants new main-image ideas, primary image concepts, ways to raise click-through rate (CTR) on a listing, "hypotheses for a new main image", A/B test ideas for the hero image, or asks how to make their Amazon main photo get more clicks — even if they don't say the word "skill" or "primary image" explicitly. Trigger it when a user uploads product photos and/or a current main image plus a screenshot of the first page of competitors and wants image ideas. Do NOT use it for secondary/listing images (slots 2-7), full listing-copy audits, or keyword research.
---

# Primary Image Hypotheses

## What this skill does and why

The main image is the single biggest lever on an Amazon listing's click-through rate. Shoppers scan a grid of near-identical thumbnails and click on instinct in well under a second. This skill turns a product's photos and its competitive field into **5 concrete, testable hypotheses** for a new primary image, each mapped to a proven Sophie Society tactic and each shipped with a ready-to-run AI image-generation prompt. The goal is not a finished image — it's a short, high-signal menu of experiments the user can generate and A/B test.

The output is deliberately framed as *hypotheses* because CTR is won empirically: you form a hypothesis about what will make more people click, then confirm it with Amazon's built-in experiment tool. This skill produces the hypotheses and the prompts to render them; the user tests and keeps the winner.

## Inputs

**Required — do not proceed without these:**

1. **Product images.** Any of: the current live primary image, and/or plain phone photos of the product by itself and in use. These anchor the AI prompts to the real hardware so generated images keep the true geometry, colors, and materials.
2. **Competitor screenshot.** A full-page capture of the **first page of ranking competitors** for the product's main search term, taken with the **GoFullPage Chrome extension** (search the main keyword for the product on Amazon, then click the GoFullPage extension to capture the entire results page as one image or PDF). This is what tells you which tactics are saturated (and therefore no longer differentiating) versus which are winning. Read it carefully — it is the core of the analysis, not a formality.

**Optional — use if provided:**

3. **SQP report** (Search Query Performance / Brand Analytics). If the user has it, use it to see the actual search terms driving impressions and purchases for the ASIN, and let that shape which benefit or keyword to feature (e.g. if buyers convert on a specific use case or spec, lead with it). Never require it; many products won't have one.

If a required input is missing, ask for just that one thing in plain language before continuing. If the user only has phone photos and no current primary, that's fine — proceed. If they have no competitor screenshot, explain why it matters (you can't tell what's saturated without it) and ask them to grab one using the **GoFullPage Chrome extension**: search their main keyword on Amazon, then click the GoFullPage icon to capture the whole first page of results in one shot.

## Workflow

1. **Read the current image.** Note what it already does well and where it's weak — small product in a sea of white space, no information, generic angle, etc.
2. **Read the competitor field closely.** Identify the *saturated* tactics (what almost everyone is already doing — these no longer differentiate) and the *winning* tactics (what the highest-rated, most-reviewed listings do that others don't). The best-rated competitors are the ones to learn from, not the cheapest.
3. **Identify the buyer's top 1–2 questions.** For every product there are a couple of make-or-break questions a shopper needs answered at a glance (e.g. "will it fit / is it compatible?", "how big / how much?", "is it sturdy / high quality?"). If an SQP report is provided, let the real search + conversion data sharpen this.
4. **Select 5 distinct tactics** from the Sophie Society tactic list (see `references/sop-tactics.md`) that (a) attack the competitor gaps and (b) answer the buyer's top questions. Favor variety — don't ship five variations of the same idea. Always include at least one **fully TOS-compliant** concept the user can publish live without an experiment.
5. **Write each concept** using the output template below.
6. **Write a paste-ready AI prompt** for each concept following the prompt rules below.
7. **Deliver as a markdown file** so the user can copy prompts straight out.

## Compliance rules (these are non-negotiable and shape every concept)

Amazon's official main-image policy: **pure white background (RGB 255,255,255), the real product filling ~85% of the frame, and NO text, badges, watermarks, borders, inset graphics, or accessories that aren't included.** Violations can get a listing suppressed.

**🔑 The text rule (most-broken, most important):** Text can **never be laid flat / photoshopped over the image.** Every word must sit on a **physical object in the scene** — either a **hang tag attached to the product** or **printed on packaging / a box** placed next to it (the "fake packaging" tactic). When you write prompts, always put copy on a tag or box and explicitly instruct the AI to add no floating captions, labels, or overlay graphics. This is the difference between a concept that can pass review and one that can't.

**Ghost/"not-included" items:** showing a grayed-out companion product (e.g. a ghost mic on a stand) or a compatible device is gray-area, but where it's near-universal in the category it carries low practical risk. Label it gray-area (run via A/B test to be safe), and note the low risk so the user can weigh it.

**Gray-area vs compliant:** any concept using text, props, non-included items, or overlay elements is **gray area** — it should be run through **Seller Central → Brands → Manage Your Experiments → Product Image A/B test**, where a rejected image fails quietly inside the experiment instead of suppressing the live listing. Concepts that are pure product on white with no text/props are **compliant** and can go live directly. Label every concept with its risk level, and recommend running each experiment the full **14 days** for a trustworthy read.

For **visually plain, text-free product categories** (bare hardware, tools, accessories), the reliably-compliant tactics are naturally fewer — mainly *Remove white space* (#4) and *3D render* (#12). That's expected, not a failure: include both if needed and differentiate them by angle and by what each emphasizes (sheer size/presence vs. premium finish), rather than dropping down to a single compliant option.

## AI prompt rules

Each concept needs one prompt the user can paste into nano banana pro (Gemini) or ChatGPT Images. Write prompts that:

- **Start from the reference photo.** Instruct the tool to use the attached product photo as the exact reference and keep the real geometry, colors, and materials identical. Name the specific parts that must stay true.
- **Specify pure white background** (RGB 255,255,255) and the product filling ~85% of the frame.
- **Put any text on a physical tag or box only**, and explicitly forbid floating text/captions/graphics.
- **Use `[bracketed placeholders]`** for any spec number (load, size, count, dimensions) so the user drops in their real value — never invent figures.
- Describe lighting, angle, shadow/reflection, and premium e-commerce quality.
- Tell the user **which uploaded photo to attach** for that concept (geometry reference; add the current primary when the concept keeps a ghost companion item).

## Output template

Deliver a markdown file named `<product>-primary-image-hypotheses.md` (if the caller specifies a filename or path, use theirs instead) with exactly this structure:

```
# Primary Image Hypotheses — [Product]

## What I looked at
- Current main image: [what it does well / where it's weak]
- The ranking field: [saturated tactics vs. what the best-rated competitors win with]
- SQP signal (if provided): [what the search/conversion data says to feature]

## The single biggest opportunity
[1 short paragraph: the clearest gap between the current image and the winners]

## ⚠️ Compliance note
[White-background TOS + the hard text-on-tag/packaging rule + Manage Your Experiments / 14-day A/B testing. Note which concept(s) are TOS-safe vs gray-area.]

## Reference images to attach
[Which uploaded photo to use for geometry, for the ghost/companion look, for in-use.]

## Concept 1 — [Name]
**Hypothesis:** [what change will lift CTR and why]
**SOP tactic:** [which tactic(s)]  **TOS risk:** [compliant / gray-area → A/B test]  [note where text lives]
**Prompt:**
​```
[paste-ready prompt following the AI prompt rules]
​```

## Concept 2 … 5
[same structure, distinct tactics, at least one TOS-compliant concept]

## Suggested test order
[ranked, with the reasoning; recommend one test at a time vs. current image, 14 days each]

### Sources
[Sophie Society SOP + Amazon image-policy references]
```
