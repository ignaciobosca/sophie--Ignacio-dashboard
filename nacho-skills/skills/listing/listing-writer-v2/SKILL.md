---
name: listing-writer-v2
description: Amazon listing writer and renovator (US) for a NEW product with no live listing, OR an EXISTING live listing being renovated. Builds a full listing (75-char title, Item Highlights, 5 bullets, description, backend terms, structured attributes, image brief) optimized for Rufus and A9 via keyword tiering. Conversational intake; parses competitor listings, Helium 10 review exports, and keyword research (Cerebro/Magnet); runs a negative-review counter-claim gate; outputs a 3-tab xlsx. v2 adds renovation mode, a Seller Central field-by-field entry walkthrough, a compliance playbook (lithium/dangerous goods, Prop 65, CPC/ASTM toy safety, PFAS), an age-range consistency check, and AI image-generation prompts per image slot. Trigger on: create/write/build a listing, first listing, listing writer, renovate/update/rebuild my listing, listing renovation, or a seller describing a product live or pre-launch. For a live listing with full SQP/PPC/own-review data, amazon-listing-optimizer is the deeper tool.
---

# Listing Writer v2

## What this skill does

For Amazon US sellers, this skill walks through a conversational, section-at-a-time intake, parses competitor listings + Helium 10 review-analysis exports + keyword research, then drafts a full listing optimized in parallel for **Rufus discoverability** (COSMO commonsense intent dimensions) and **A9 organic rank** (priority-tiered keyword coverage), respecting Amazon TOS and category rules.

v2 runs in one of two modes, chosen at Section 1:

- **NEW MODE** — pre-launch product, no live listing yet. Identical to v1 behavior.
- **RENOVATION MODE** — an existing live listing the seller wants rebuilt. The current title/bullets/description/images become intake inputs, competitor review exports drive the counter-claim gate, and the run ends not just at the xlsx but optionally walks the seller through pasting it into Seller Central field by field.

The core output is a 3-tab .xlsx workbook saved to `/mnt/user-data/outputs/`:

1. **Listing Copy** — title, 5 bullets, product description, brand, backend search terms, paste-ready
2. **Structured Attributes** — Rufus-relevant backend fields with proposed values, source attribution, confidence, and a "seller must confirm" flag
3. **Image Brief** — hero plus 6 secondary images, each tied to a COSMO dimension or a competitor objection copy can't carry; followed by a Coverage Map and a "Claims to verify before publishing" gap list

In RENOVATION MODE the skill also offers two follow-on services after the xlsx (see Phase D and Phase E):
- A **Seller Central entry walkthrough** that maps every cell to the exact form field, tab by tab, in page order.
- A **compliance escalation pass** for regulated categories (toys, electronics with batteries, supplements, baby).

After saving, the skill offers a Google Drive push via the connector.

**What this skill does NOT do:**
- Replace `amazon-listing-optimizer` when the seller has 30-60+ days of their own SQP, PPC, and review data (that tool renovates against real performance; this one renovates against copy + competitor inputs)
- Produce an upload-ready flat file (seller pastes manually, or uses the walkthrough)
- Invent product facts (every claim traces to seller input)
- Make legal/regulatory determinations (it flags and routes them; the seller attests with supplier docs)
- Cover non-US marketplaces

## Mode selection (do this first, at Section 1)

Ask whether this is a new product or a live listing being renovated. Detection shortcuts:
- Seller pastes an "active title" / current bullets / a live ASIN / Seller Central screenshots -> **RENOVATION MODE**.
- Seller describes a product with no live listing, asks to "create"/"write"/"draft" a first listing -> **NEW MODE**.

If RENOVATION MODE, say so plainly and note the trade-off once: this renovates against the product brief + competitor inputs, and if the seller later has their own SQP/PPC/review data, `amazon-listing-optimizer` is the stronger follow-up. Do not belabor it.

## Critical rules (do not violate)

### Rule 1 — Never invent product facts
Every concrete claim ("112 double-sided cards", "USB-C rechargeable", "blue-light-free") must trace to a specific field in the seller's intake or supplier/spec docs. If a claim would strengthen copy but isn't supported, drop it or surface it in "Claims to verify before publishing." Never guess. Strictest when converting negative competitor reviews into positive claims (Rule 4).

### Rule 2 — Writing voice rules for all Claude-authored content
Every Claude-authored string in the xlsx (title, bullets, description, attribute values, image brief copy) AND every chat message during intake:
- **No em-dashes (`—`) or en-dashes (`–`) anywhere.** Use commas, periods, parentheses, colons. This is the #1 AI-tell. In RENOVATION MODE, scan the seller's *existing* copy for em-dashes too and flag them for removal, they are usually present in the live listing.
- **No AI-typical phrases:** "delve into", "let's", "it is worth noting", "in summary", "seamless", "utilize", "leverage", "unlock the power of", "navigate the landscape", "elevate your experience", "discover", "introducing". Write like a person describing a product they use.
- **Match the seller's brand voice when samples are provided.** Study sentence length, warmth, vocabulary, capitalization, how they address the buyer.
- **No curly-quote HTML entities.** Use real Unicode characters or straight quotes.
- **Plain seller-facing language in explanatory text.** No "COSMO", no "tier 2". Rufus and A9 may appear by name with a one-line plain definition.

### Rule 3 — TOS compliance is enforced, not advised
- **Title (current structure):** **75 characters or less, including spaces**, for all categories except media. This is a hard cap; over-length titles get auto-rewritten by Amazon's AI (brand-registered sellers get a short review window, others do not, you do not want the machine choosing your title). Structure the 75 chars as: **brand first, then product type, then the single highest-intent keyword**, and a defining variant/attribute only if it still fits. Do not try to cram size, pack, material, use case, compatibility, color, and benefit into the title anymore. Also: no ALL CAPS except brand acronyms; no promo language ("best", "cheapest", "#1", "free shipping", "sale", "%"); no symbols (`! ? * $ ~`); no emojis; no quotes/non-language characters; no word repetition.
- **Item Highlights (new field, carries what the title used to):** up to **125 characters**, formatted as **comma-separated phrases, NOT sentences** (Amazon's own example style: "USB-C, PPS Support, Cable not included"). This field is searchable and shows under the title in search results and on the detail page. It holds the secondary terms displaced by the 75-char title cap: material, key use cases, pack/variant detail, compatibility, the comparison facts a shopper scans. No promo language, no sentences, no keyword stuffing, no dumping the old long title here.
- **Bullets:** <= 500 chars each (target 200-250); no contact info; no promo claims; no competitor brands; no HTML
- **Description:** <= 2000 chars; plain text (prefer clean plain text, Amazon strips most HTML); no contact info, no URLs, no "100% safe"/"cures"/"treats"
- **Backend search terms:** <= 250 **bytes** (target 240); no competitor brands; no promo/temporary terms; no repetition of words already in title/Item Highlights/bullets/description; single spaces only
- **Category-specific:** load `references/category-tos-rules.md`. Some categories cap titles even lower than 75 and have extra restrictions. Supplements/baby/medical/beauty/TOYS: no medical/therapy claims; toys autism angle = supportive/self-paced language only.

The title and Item Highlights now work as a hierarchy: the title is the clean mobile-first hook (brand + type + top keyword), Item Highlights carries the searchable supporting detail, and bullets/description/backend carry the rest. The full keyword strategy still matters; the structure changed, not the SEO ambition.

If a seller-supplied feature would violate TOS, do not use it in copy; surface it in "Claims to verify."

### Rule 4 — Strict gate on negative-review counter-claims
When review insights show a recurring complaint, write copy that preempts it ONLY if the seller's product info explicitly supports the counter-claim.
1. Extract the recurring complaint (rank by mention frequency / star-rating impact)
2. Check seller intake + supplier docs for an attribute that addresses it
3. If supported: write a feature-anchored claim ("rounded corners, one-piece body, wipe-clean film"), never a vague subjective claim
4. If not supported: surface it in "Claims to verify" as a question
Never invent a counter-claim. Never make unverifiable subjective claims.

### Rule 5 — COSMO coverage attempted on all 15, N/A only with a reason
Consider all 15 COSMO dimensions (product type, target audience, use scenario, occasion, material, special features, quality/durability, portability, included components, item form/shape, theme, brand, color, pattern, compatibility, care). Cover in copy (note placement in the coverage map) or mark N/A with a one-line reason. Forced filler is worse than an honest N/A.

### Rule 6 — Output checklist before present_files
Before presenting: xlsx exists; all 3 tabs populated; every Claude cell passes the voice scan and TOS scan; backend de-duped against title+bullets+description; coverage map present. Run `scripts/self_audit.py` (or replicate its checks inline if scripts are absent).

### Rule 7 — Backend keyword de-duplication
Every backend token must NOT appear as a whole word in title, Item Highlights, bullets, or description. Build a lowercased concat of ALL of that copy (title + Item Highlights + bullets + description), fail any candidate token with a whole-word match. Hyphenated compounds are safe. Prioritize remaining slots with misspellings, Spanish equivalents, foreign-brand-equivalent phrases, edge synonyms. Target <= 240 bytes.

### Rule 8 (NEW in v2) — Keyword universe hygiene for noisy Cerebro/Magnet exports
Raw competitor-keyword exports are frequently majority-noise. Before tiering:
- **Drop competitor brand terms entirely** (relevance 0). Build the brand list from the export's own column headers (the ASIN columns) plus obvious brand tokens in phrases.
- **Drop foreign-language terms that contradict the product.** If the product is English-only audio, terms like "chinese", "korean", "spanish flash cards", "aprende", "abecedario" are not relevant to what the product DOES, even at high volume. They go to backend (Spanish-buyer-intent) only if they describe a real buyer the product still serves (e.g. "english learning for spanish speakers" is valid; "learn korean" is not).
- Expect to drop 40-65% of rows. Report the kept/total count to the seller.

### Rule 9 (NEW in v2) — Age-range internal-consistency check
For any kids/baby/toy product, the age claim must agree across THREE places, or the listing risks a suppression flag:
1. The age in the **title** and head keywords (e.g. "for toddlers 1-3", "ages 1-7")
2. The **structured attributes** (Manufacturer Min/Max Age in months, Age Range Description)
3. The **safety determination** (small-parts / choking hazard often forces a 3+ minimum regardless of marketing)
If these disagree, flag it loudly in "Claims to verify" and in the Seller Central walkthrough. Example caught in practice: title said ages 1-7 but Min/Max Age fields said 36-120 months (3-10), and small cards/stylus may force 3+. Resolve before publishing.

### Rule 10 (NEW) — Title is a 75-char hook, Item Highlights carries the rest
The title is no longer the SEO workhorse. It is a clean mobile-first hook: brand + product type + one highest-intent keyword, 75 chars max. Everything the old long title used to carry (material, pack, size, use case, compatibility, secondary keywords) moves into Item Highlights (125 chars, comma-separated phrases) or down into bullets/description/backend. Never produce a title over 75 chars: an over-length title is not just weaker, it gets auto-rewritten by Amazon's AI, which optimizes for clean rather than for ranking and can quietly cost the seller their keyword placement. The skill's job is to make that structural decision deliberately (what stays in title vs what moves to highlights) so the machine never makes it for them. Keep the decision consistent across a product family.

## Conversational intake — how the skill talks to the seller

Seller does everything in chat. No external forms. Walk 9 sections in order, one section per turn. Use the `ask_user_input` tool for multi-choice questions (mode, style, which inputs available) rather than prose bullets, it is faster on mobile.

### Pacing rules
- One section per message, short (3-5 lines), warm, no em-dashes.
- Every prompt closes with a paste-everything escape hatch.
- Detect early-dump: scan each reply for content answering later sections, acknowledge what was captured, jump to the next unanswered section.
- Files: one consolidated ask at Section 8, except keyword research at Section 7 (format drives parsing).

### The 9 sections
1. **Product + MODE.** Product type/category + brand, AND new-vs-renovation. Loads TOS rules + sets mode. (Capture the exact brand string including spacing, e.g. "Acme Goods" vs "AcmeGoods", and reuse it consistently.)
2. **Tell me about it.** Materials, dimensions, color, pack, country of origin, certifications, battery type/chemistry, care, warranty. (Battery chemistry matters for compliance, Phase E.)
3. **Who's it for and why?** Target user, top 3 use cases, top 3 benefits paired with the features that create them. Capture the age range explicitly (Rule 9).
4. **Variations.** Single ASIN or parent/child.
5. **Competition.** 3-5 competitor listings (or, in RENOVATION MODE, the seller's current live copy counts as one input plus competitors).
6. **Voice of the customer.** Review insights for the main head keyword. v2: accept Helium 10 Review-Analysis xlsx exports directly (see `references/h10-review-analysis-format.md`).
7. **Keyword research.** File upload (Cerebro/Magnet/Data Dive/Jungle Scout/generic). Apply Rule 8 hygiene.
8. **Anything else?** Consolidated file ask. Supplier docs, brand voice samples, compatibility, restricted-category notes, Seller Central screenshots (RENOVATION MODE).
9. **Recap + style pick.** Summarize captured inputs, recommend a copywriting style, confirm "ready to draft?". Proceed only on explicit yes.

## Pipeline

### Phase A — Intake (Sections 1-9, conversational)
Walk the sections. Update `/tmp/intake_state.json` after every reply. End only when Section 9 recap is confirmed.

### Phase B — Parse, plan, draft (silent)
- **B1 Parse** competitor listings, H10 review exports (positive/negative topic insights ranked by mentions and star-rating impact; returns topics if present), keyword file (Rule 8 hygiene), supplier docs, category TOS.
- **B2 Keyword universe + tiering.** relevance = attribute-word overlap (0-1); priority = relevance x log(volume+1). With the 75-char title cap, tiers re-route:
  - **Tier 1 (title, ~1-3 terms):** only the single highest-intent head keyword fits alongside brand + product type in 75 chars. Pick the one term with the best priority that a shopper actually types.
  - **Tier 2 (Item Highlights, comma-separated, <=125 chars):** the next 3-6 high-priority terms that used to live in the title, expressed as short comma-separated phrases (material, use case, variant, compatibility, key spec).
  - **Tier 3 (bullets):** next 10-15 terms, rel>=0.5.
  - **Tier 4 (description):** next 15-25, rel>=0.3, long-tail/semantic.
  - **Tier 5 (backend):** remaining applicable terms, misspellings, Spanish equivalents.
  - Drop rel<0.2, brand-only, foreign-contradictory, TOS-violating.
- **B3 COSMO plan.** All 15, placement or N/A+reason.
- **B4 Draft** in order: title (75-char cap), **Item Highlights (comma-separated phrases, <=125 chars)**, bullets, description, backend, structured attributes, image brief. (Drafting detail otherwise unchanged from v1.)
- **B5 Self-audit** against Rules 2/3/7/9 before writing, including the 75-char title check and the 125-char comma-separated Item Highlights check. Fix and re-audit until clean.
- **B6 Write xlsx** (tabs below). Styling is your agency house style, set once in `scripts/config.py` (default navy `#0A2333` headers, green `#13835B` secondary, orange `#EA6C34` flags, off-white `#F3F3F1` fills, DM Sans). Swap these for any client/agency palette without touching skill logic. Filename: `Listing_[Renovation|Draft]_[ProductSlug]_[YYYY-MM-DD].xlsx`.

### Phase C — Verify + present + optional Drive push
Run `scripts/check_outputs.py` (or inline checks). Present the xlsx. Brief chat summary (<250 words): product, mode, style, COSMO count, keyword tier counts (and kept/total from Rule 8), top 3 neutralized review patterns with supporting feature, count of claims-to-verify, next step. Offer Drive push.

## xlsx tab structure (v2)

The workbook generic across any brand. No client names hardcoded; the brand string comes from intake. Tabs:

### Tab 1 — Listing Copy
Columns: `Field`, `Value`, `Count`, `TOS Limit`, `What Changed`, `Notes`.
- Rows: Brand, Title, **Item Highlights**, Bullet 1-5, Description, Backend Search Terms.
- The **Title** row shows its count against the 75-char cap and flags if over. The **Item Highlights** row shows count against 125 chars and must read as comma-separated phrases, not a sentence.
- **`What Changed`** (NEW): in RENOVATION MODE, a short before/after note per field. For the title, this almost always reads like "was 186 chars carrying 14 jobs; trimmed to brand + product type + top keyword under 75; secondary terms moved to Item Highlights." In NEW MODE this column reads "New" for every row.
- Paste-ready: the seller copies the `Value` column straight into Seller Central.

### Tab 2 — Structured Attributes (copy-paste revamp block)
Columns: `Attribute`, `Proposed Value`, `Source`, `Confidence`, `Seller Action`.
- One row per Rufus-relevant backend field for the category.
- A **"PASTE BLOCK" section** at the top: a single contiguous, clean two-column list (Attribute -> Value) with no styling noise, designed so the seller can paste the live-listing title + attributes back to the skill for a revamp, and so the values drop cleanly into Seller Central. This is the "share live listing, get attributes back" loop the seller asked for.
- Regulated/uncertain fields blank with an orange "SELLER MUST CONFIRM" action.

### Tab 3 — Image Brief
Columns: `Slot`, `Visual Goal`, `COSMO Dimension`, `Shopper Question Answered`, `AI Image Prompt`, `Production Notes`.
- 7 rows: Hero + 6 secondary.
- **`AI Image Prompt`** (NEW): a ready-to-paste prompt for ChatGPT / an image model to generate or mock that specific image, with the Amazon guideline for that slot baked into the prompt text (see `references/image-prompt-guidelines.md`). The main-image prompt always specifies pure white RGB 255,255,255 background, product fills ~85% of frame, no text/logo/props. Secondary-image prompts allow lifestyle/infographic per Amazon's rules for non-main images.
- Followed by the **Coverage Map** (every COSMO dimension: status + placement; every keyword tier: which keyword, placed where, why) and the **Claims to Verify Before Publishing** list.

### Phase D (NEW in v2) — Seller Central entry walkthrough (RENOVATION MODE, opt-in)
If the seller is pasting into Seller Central (they share screenshots or ask "where does this go"), walk the live form **tab by tab, in on-screen page order**. For each field: state the exact value to enter, mark already-correct fields with a check, flag mismatches, and mark safe-to-skip fields. Cover the standard tabs:

- **Product Details tab:** Item Name (title), Brand Name (check spacing consistency, e.g. "Acme Goods" vs "AcmeGoods"), Item Type Keyword, Target Audience Keyword, Model Name, Manufacturer, Product Description (paste CLEAN plain text, strip em-dashes and HTML), Bullet Points x5, Generic Keyword (backend), Target Gender, Age Range Description, Material, Color, Theme, Part Number, Manufacturer Min/Max Age (months) (RULE 9 CHECK HERE), Included Components, Item Dimensions, Language Type/Language, Educational Objective (multi-value, priority order). Note dropdown-only fields and give the closest valid option (e.g. Age Range Description has Baby/Kid/Teen/Adult -> pick Kid for a 1-7 product; Theme dropdown -> pick the closest functional match like Phonics; Language Type -> Spoken for talking audio).
- **Offer tab:** mostly seller-owned pricing/fulfillment, do NOT advise on price. Flag Gift Options (set Yes if positioning leans on gifting AND fulfillment supports it), Package Dimensions/Weight (fill for correct shipping fees, use the CARTON not the device specs), skip the used/refurb Supplemental Condition block, and leave other-marketplace toggles OFF for an English-only US listing.
- **Always note the stale header cache:** the page header keeps showing the OLD title until Save and finish is clicked on Product Details.

State plainly: "I'm mapping fields, not setting your price."

### Phase E (NEW in v2) — Compliance escalation pass (regulated categories, opt-in)
For toys, electronics-with-batteries, supplements, baby, or any category with a Safety & Compliance tab, walk it and ESCALATE the legal-liability fields. The skill flags and routes; the seller attests with supplier docs. Never assert a regulatory value the seller hasn't confirmed.

Standard escalations:
- **Country/Region of Origin** — required; from supplier.
- **Dangerous Goods Regulations** — if the product has a lithium battery (most USB-C rechargeable toys/electronics do), "Not Applicable" is likely WRONG. It usually needs the lithium classification plus a UN38.3 test report. Make the seller confirm battery chemistry before accepting Not Applicable.
- **California Prop 65** — many plastic/electronic/battery products carry a warning. Do not assert "No Warning Applicable" unless the supplier confirms in writing.
- **Has Replaceable Battery** — match the spec (built-in rechargeable = No).
- **Contains PFAS** — confirm with supplier; usually No for plastic/LCD but do not guess.
- **Safety Attestation / CPC** — US children's products need a Children's Product Certificate backed by CPSIA/ASTM F963 testing. Only attest Yes if the docs exist. Missing CPC is a launch blocker, not a field to bluff.
- **Small-parts / choking hazard vs age claim** — RULE 9: small cards, stylus, slots often force a 3+ rating that contradicts a "1-3" or "ages 1+" marketing claim. Reconcile.
- **Non-EU/US-only:** skip GPSR Responsible Person, EU compliance media, GHS/SDS chemical fields, BAA/TAA.

Output of Phase E is a short prioritized action list of the 2-4 fields that carry actual liability and must be confirmed before Save and finish.

## Edge cases
- Seller changes declared inputs mid-run (says "keyword-only" then uploads reviews): adapt and tell them plainly it makes the draft sharper (the counter-claim gate is now live). Do not hold them to the earlier statement.
- Skill ships SKILL.md only, referenced scripts/refs absent: execute the described logic directly (build keyword universe, tier, COSMO plan, draft, audit, write xlsx in Python). Do not block on missing scaffolding.
- Seller pastes everything in message 1: parse for early-dump, jump to first unanswered section.
- Restricted category: warn at Section 1 after the category is named.
- Keyword file missing/unparseable: ask once for format, then accept pasted keyword+volume text, then accept none (warn the draft leans on category-standard terms).

## References — read only what's needed
1. `references/conversational-intake.md` — per-section prompts, push-back, early-dump logic. Read at start.
2. `references/intake-state-schema.md` — JSON schema for intake state. Read once.
3. `references/category-tos-rules.md` — US TOS per category family. Read at Section 1 after category named.
4. `references/cosmo-dimensions.md` — the 15 dimensions + applicability. Read at B3.
5. `references/copywriting-styles.md` — six style templates. Read at B4 after style pick.
6. `references/keyword-format-detection.md` — header patterns for keyword exports. Read if parsing is ambiguous.
7. `references/h10-review-analysis-format.md` (NEW) — Helium 10 Review-Analysis xlsx tab structure (Positive/Negative Topic Insights, Trends, Star Rating Impact, Returns Topics) and how to rank complaints. Read at Section 6 / B1 when an H10 review export is uploaded.
8. `references/seller-central-field-map.md` (NEW) — the Product Details / Offer / Safety & Compliance field list with the v2 mapping rules and common dropdown answers. Read at Phase D/E.
9. `references/compliance-escalation.md` (NEW) — the regulated-category checklist (lithium/DG, Prop 65, CPC/ASTM, PFAS, age-vs-small-parts). Read at Phase E.
10. `references/image-prompt-guidelines.md` (NEW) — Amazon per-image guidelines (main vs secondary) and the AI-image-prompt templates used to fill Tab 3's `AI Image Prompt` column. Read at B4 when drafting the image brief.
11. `references/banned-words.md` — promotional/banned-word list. Read if the audit flags a violation.

Defensive reading of the full reference set is the #1 cause of budget exhaustion. Skip anything not triggered.

## Related skills
- `amazon-listing-optimizer` — for a live listing with the seller's own SQP/PPC/review data. The deeper renovation tool. This skill is the copy + Seller-Central-entry renovator and the pre-launch writer.
- `rufus-discoverability-audit`, `rufus-cosmo-audit`, `rufus-cosmo-lite` — COSMO-only audits of existing listings.

This skill is self-contained: no runtime dependency on the others.
