---
name: brand-kit
description: The user's living brand profile. Trigger at the start of ANY task that produces a designed or written deliverable — HTML pages, dashboards, PDFs, Word docs, slide decks, reports, emails, social posts, Amazon listing copy, A+ content, brand store pages, infographics, charts, marketing one-pagers, or any visual/written output the user or their customers will see. On first run it conducts a one-time conversational intake (colors, typography, logo, imagery, voice/tone, inspiration) — flexible enough for Amazon sellers who may only have a website link, packaging photos, or a logo. On every run after, it silently loads the saved brand and applies it so output looks and sounds on-brand without re-asking. Trigger even when the user does not say "brand," "design," or "style" — consistency only works if it's consulted every time, so default to consulting it. Also trigger on "update my brand," "change my colors," "I have a new logo," or "redo the brand kit."
---

# Brand Kit

This skill keeps every designed or written deliverable Claude produces for the user on-brand. There are two phases:

1. **First run** — interview the user, capture their brand, and save it to `BRAND.md` in this skill's folder.
2. **Every run after** — silently read `BRAND.md` and apply it to whatever Claude is building. Do not re-ask the user about brand on every task.

The user has chosen "auto-apply silently" as the default behavior. Honor that: the only time the user should hear the word "brand" come out of Claude's mouth is during the one-time intake or when they explicitly ask to update the kit. Otherwise, just produce on-brand output and move on.

## Step 0 — Detect which phase you're in

Read `BRAND.md` from the same directory as this `SKILL.md`.

- If the file is missing, empty, or contains the marker `<!-- INTAKE_INCOMPLETE -->` → first-run mode. Go to **First-run intake**.
- Otherwise → apply mode. Go to **Applying the brand**.

If the user explicitly says "update my brand kit" (or similar), treat it as a partial intake — skip to **Updating the brand** below.

## First-run intake

The job here is to meet the user wherever they are. Some users will have a polished brand book; most will not. Ask for the ideal, accept whatever they hand you and turn it into a workable brand, and if they have nothing at all, build a brand for them from inspiration. **Nobody walks away from this intake empty-handed** — every first run produces a usable BRAND.md, even if the user came in with zero brand assets.

### Open the conversation

Open warmly and inclusively. Make it explicit upfront that the ideal is great but not required, and that "I have nothing" is also a fine starting point. Something close to:

> "Quick one-time setup so everything I make for you stays on-brand. **Ideally** I'd love any of this you can send: a brand book or style guide, your logo file, hex codes for your colors, fonts you use, photos of your product packaging, a link to your website or Amazon storefront, screenshots of your existing marketing, or notes on how you want your brand to sound.
>
> **If you don't have most of that — totally fine.** Just send whatever's around: a logo, a website link, even a couple of phone photos of your packaging. I'll work backward from it.
>
> **And if you have nothing at all yet — also fine.** Just point me at 1–3 brands or websites whose look-and-feel you'd like to channel (other Amazon sellers, a Shopify store, a magazine, anything you find inspiring), tell me roughly what you sell and who buys it, and I'll draft a brand for you to react to."

Then go through the categories below. Ask naturally, infer where you can, confirm before saving. Don't make it feel like a form — it's a conversation.

### What to capture (in priority order)

For each category: ask for the ideal, accept what you get, and never block on a missing field. If something is genuinely unknown after asking, note it as `Unspecified — ask before assuming` and move on to the next thing.

**Brand essentials** _(always ask, but a one-liner each is fine)_
- Brand name and one-sentence description of what they sell
- Primary product category and target customer (kitchen, baby, supplements, pet, outdoors, etc.)

**Colors** _(ideal: hex codes for primary/secondary/accent + neutrals)_
- Ask for hex codes. If they only have descriptions ("navy and gold"), pin down specific shades together.
- If they uploaded a logo, sample dominant colors from it and propose them.
- If they shared a website URL, sample colors from the live site.
- If they have nothing, see "Brand from inspiration" below — don't leave colors blank.

**Typography** _(ideal: specific heading + body font names with weights)_
- Ask if they have specific fonts in mind. If yes, capture name and weights.
- If they don't know, describe a vibe and propose 2–3 pairings. Suggested defaults by vibe:
  - Clean modern → Inter (headings) + Inter (body)
  - Premium classic → Playfair Display (headings) + Source Sans Pro (body)
  - Friendly playful → Poppins (headings) + Nunito (body)
  - Editorial / lifestyle → DM Serif Display (headings) + DM Sans (body)
  - Bold / outdoor / sport → Oswald (headings) + Roboto (body)
  - Soft / wellness / beauty → Cormorant Garamond (headings) + Lato (body)
- Let them pick, or pick one yourself if they ask you to.

**Logo and imagery** _(ideal: logo file + description of image style)_
- Ask for the logo (file upload or URL). Save uploaded files to `assets/`.
- Ask about imagery direction: lifestyle vs. studio, warm vs. cool, minimal vs. busy, on-model vs. flat lay, color palette in imagery, props/backgrounds.
- If they have packaging photos, save them to `assets/` and use them as a reference for the imagery direction.
- If they have no logo yet, note it and offer: "Want me to make you a simple wordmark in your fonts and colors as a placeholder until you commission a real one?"

**Voice and tone** _(ideal: 3 adjectives + a sample of approved copy)_
- Adjectives for how copy should sound (warm, witty, premium, technical, playful, no-nonsense).
- Things they would never say (tone, jargon, slang to avoid).
- Examples of phrases or taglines they love. If they have none, ask them to point at a brand whose voice they admire and describe what they like about it.

**Inspiration** _(ideal: 2–3 links + what to channel from each)_
- Brands or pages they want to feel similar to. Capture both the link and a sentence about what specifically to take from each ("the way they use whitespace," "the warmth of their photography," "their no-bullshit copy").

**Required and forbidden claims** _(especially for Amazon sellers — important even if everything else is loose)_
- Always-include claims: "BPA-free," "Family-owned since 2014," "Made in USA," certifications, awards, trademark symbols.
- Never-claim items: medical claims, superlatives the brand avoids, competitor comparisons, allergens, anything compliance-sensitive.
- Required disclaimers verbatim.

**Anything else** they want Claude to remember (slogans, hashtags, naming conventions, recurring product line names).

### Working with whatever they have — by input type

Be opportunistic. Whatever shows up in the conversation, mine it for brand signal.

- **Brand book PDF uploaded** → read it end-to-end, extract structured data, confirm before saving. This is the gold standard — most everything else can be inferred from it.
- **Style guide screenshots** → read them, extract what you can.
- **Logo file uploaded** → save to `assets/`. Sample 2–4 dominant colors as a starting palette. Note whether it suggests a serif or sans-serif heading direction. Confirm with the user.
- **Website URL** → fetch it. Pull dominant colors from CSS (look at `--color-*` custom properties, hero backgrounds, button colors, primary text). Identify fonts in use (look at `font-family` declarations and Google Fonts links). Capture taglines and the imagery vibe from hero sections. Confirm before saving.
- **Amazon storefront URL** → fetch what you can. Extract palette from header and product imagery, voice from headlines and product titles.
- **Packaging photos uploaded** → save to `assets/`. Describe the visual language back to the user (color, finish, typography on pack, mood). Use as imagery direction reference.
- **Existing marketing screenshots** (emails, social posts, listings) → read them, mine for colors, fonts, voice, claims.
- **Just a logo and a vibe** → sample colors from the logo, ask leading questions about the vibe ("Premium and minimal, or warm and friendly? Saturated and bold, or muted and earthy?"), propose a palette and font pairing for them to react to.
- **A vague description and nothing else** → see "Brand from inspiration" below.

### Brand from inspiration (when the user has nothing)

If the user honestly has nothing — no logo, no colors, no fonts, no website, no marketing — don't give up and don't fill BRAND.md with `Unspecified` everywhere. Build them a starter brand from inspiration. This is a feature, not a fallback: a lot of Amazon sellers start 