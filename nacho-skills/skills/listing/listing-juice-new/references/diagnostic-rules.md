# Diagnostic Rules

How to turn raw input data into diagnoses. Covers SQP funnel bucketing, COSMO dimensional scoring, review-theme prioritization, competitive benchmarking, and PPC search-term harvest.

## Core principle: market-relative, not absolute

Wherever possible, diagnoses compare your ASIN's metric to the market's metric **for the same query or attribute** — not to arbitrary thresholds. SQP already provides market-level data per query. Use it, but compute market CTR and market CVR-from-clicks manually — the rate fields Amazon provides (`Click Rate %`, `Purchase Rate %`) are all denominated by Search Query Volume, not impressions or clicks. See `input-parsing.md` for the full explanation.

Sample-size floors protect against noise: a 50% CTR on 2 impressions is not a signal, it's a fluctuation. Every market-relative comparison below has a floor.

## ⚠️ SQP sanity check before running diagnostics

Before trusting any bucketing, verify your interpretation of the SQP rate fields. Pick any query and test:

```python
r = df.iloc[0]  # first row
assert abs(r['Clicks: Click Rate %'] - 100 * r['Clicks: Total Count'] / r['Search Query Volume']) < 0.1, \
    "Click Rate % is SQV-denominated, not impression-denominated — see input-parsing.md"

# Compute correct market CTR (clicks/impressions) — typical values 1–3%
market_ctr = 100 * r['Clicks: Total Count'] / r['Impressions: Total Count']
assert 0.1 <= market_ctr <= 10, f"Market CTR {market_ctr:.2f}% outside typical range — investigate"

# Compute correct market CVR-from-clicks — typical values 1–5%
market_cvr = 100 * r['Purchases: Total Count'] / r['Clicks: Total Count']
assert 0.1 <= market_cvr <= 15, f"Market CVR-from-clicks {market_cvr:.2f}% outside typical range — investigate"
```

If the first assertion fails, Amazon changed the field semantics — update this skill before proceeding. If market CTR shows >10%, you're using the wrong field; re-read `input-parsing.md`.

---

## SQP funnel bucketing

Each query in the SQP export gets classified into one of five buckets based on where it fails (or wins) in the funnel. For each bucket, sort descending by query volume and take the top 5 per bucket — those are the queries that drive rewrite decisions.

### Bucket 1 — Impression problem

The market is searching this query with meaningful volume, but your ASIN barely appears.

- Market impression volume > 1,000 for the quarter, AND
- Your ASIN's `Impressions: ASIN Count` < (market `Impressions: Total Count` × 0.5%)

*Diagnosis: Alexa Shopping / A9 doesn't associate you with this query. Fix: head-term coverage in title, backend search terms, PPC ranking campaigns, structured attributes that match the query's intent.*

### Bucket 2 — CTR problem

You're showing up on the SERP but shoppers skip past your listing.

- Your impression count >= 100 (sample-size floor), AND
- Your ASIN CTR < (market CTR × 0.5)
  - Your ASIN CTR = `Clicks: ASIN Count` / `Impressions: ASIN Count` × 100
  - **Market CTR = `Clicks: Total Count` / `Impressions: Total Count` × 100** (computed manually — see note below)

**⚠️ Do NOT use `Clicks: Click Rate %` as market CTR.** That field divides by Search Query Volume, not impressions. Typical values are 30–60% and are NOT comparable to your ASIN's clicks/impressions ratio. See `input-parsing.md` for the full explanation. Always compute market CTR from the raw totals.

Sanity check: market CTR values should typically land in the 0.5–5% range. If you're seeing 40%+, you used the wrong field.

*Diagnosis: the SERP preview (main image, title mobile cutoff, price, star rating, badges) isn't winning the click. Copy can help at the margin — a better title or badge-eligible language — but the primary fixes are image and price positioning.*

### Bucket 3 — CVR problem

Shoppers click through but don't buy.

- Your click count >= 5 (sample-size floor), AND
- Your ASIN CVR < (market CVR-from-clicks × 0.5)
  - Your ASIN CVR = `Purchases: ASIN Count` / `Clicks: ASIN Count` × 100
  - **Market CVR-from-clicks = `Purchases: Total Count` / `Clicks: Total Count` × 100** (computed manually — see note below)

**⚠️ Do NOT use `Purchases: Purchase Rate %` as market CVR-from-clicks.** That field divides by Search Query Volume, not clicks. It answers "what % of searches result in a purchase" which is a different question. Always compute market CVR-from-clicks from the raw totals.

Sanity check: market CVR-from-clicks values should typically land in the 1–5% range.

*Diagnosis: the listing fails the shopper post-click. Fix: bullets, description, A+ content, pricing, reviews. **This is where full listing rewrites move the needle most.***

### Bucket 4 — Positioning gold

Queries where your ASIN outperforms the market.

- Your click count >= 5 (sample-size floor for CVR signal), AND
- Your purchase count >= 2 (you've actually converted), AND
- Either:
  - Your ASIN CVR-from-clicks > market CVR-from-clicks × 1.5, OR
  - Your `Purchases: ASIN Share %` > 5% (you capture a meaningful slice of ALL purchases on this query)

Where:
- Your CVR-from-clicks = `Purchases: ASIN Count` / `Clicks: ASIN Count` × 100
- Market CVR-from-clicks = `Purchases: Total Count` / `Clicks: Total Count` × 100

*Diagnosis: you're winning here. Defend the vocabulary that's working — keep these phrases in the title. Expand: use the language of these queries in backend terms, bullets, and any new PPC targeting.*

### Bucket 5 — Expansion opportunity

Queries that convert well at the search level in the category but your ASIN is absent.

- Search-level purchase rate (`Purchases: Purchase Rate %`) > 3%, AND
- Your impression share < 1%, AND
- Search Query Volume > 1,000 (meaningful market demand)

Note the threshold is 3%, not 10%. Recall that `Purchases: Purchase Rate %` is purchases ÷ search volume (not per-click), so a 10% threshold is unrealistic — few queries clear that bar. 3% represents a healthy search-to-purchase conversion.

*Diagnosis: high-intent query where you're invisible. Add to PPC targeting and to backend search terms. Consider whether your product genuinely fits the query before leaning in — some high-converting queries are for products that you don't actually sell.*

### Sample-size noise flag

Some queries will look dramatic but be statistically meaningless. Flag and DE-prioritize any query where:

- Your ASIN impression count < 10 (too few impressions to estimate your CTR reliably), OR
- Your ASIN click count < 3 (too few clicks to estimate your CVR reliably)

These get surfaced in the HTML with a "low-sample-size, needs more data" annotation instead of being acted on in the rewrite. Don't let a 1-click 100% CVR drive title decisions — it's noise.

### Tiebreakers within buckets

When multiple queries tie on volume, break ties deterministically:
1. Purchase share DESC (higher-converting wins)
2. Query alphabetical ASC

This ensures reproducibility across runs — same SQP input produces the same bucket assignments.

---

## COSMO 15-dimension scoring

For the full dimension definitions and scoring rubric (0/1/2/N/A per dimension with examples and pre-shipping validation rules), read `cosmo.md`. This section covers how category context shapes the scoring and how SQP data reweights dimension priorities.

### Score semantically, not mechanically

The keyword detectors in `category-families.md` are **hints, not gates**. Score a dimension 1+ if the listing addresses it in any recognizable way, even if the exact keywords aren't present. "For people winding down after the office" covers Audience even without matching any audience-keyword from a list. Use judgment.

### Category-routed scoring

Before scoring an ASIN, read its `product_type` from the flat file and look up the category family in `category-families.md`. The family determines:

- Which dimensions are critical vs low-priority for this category
- Which dimensions are N/A by default (e.g., Body Part is N/A for most supplements and hardgoods)
- Which keyword hints apply (supplement keywords differ from apparel keywords)

If `product_type` doesn't map to any family, use the **generic** family — universal COSMO dimensions, no keyword hints, conservative scoring.

### SQP-weighted dimension priority (runs only when SQP is provided)

After the raw COSMO scorecard is computed, do a second pass that reweights priorities based on what the ASIN's top converting SQP queries actually target.

1. Take the ASIN's top 20 queries by purchase share (any query with >= 1 purchase in the quarter).
2. For each query, semantically map its intent to one or two COSMO dimensions. For example:
   - "kava gummies for sleep" → Problem Solved (sleep), Product Type (gummies)
   - "alcohol alternative" → Alternative Use
   - "stress relief" → Want/Activity, Problem Solved
3. Count how often each dimension shows up across those top 20 queries.
4. **Upgrade priority** of missing/partial dimensions that appear in 5+ top converting queries (high commercial signal).
5. **Downgrade priority** of missing/partial dimensions that appear in 0 top converting queries (no evidence shoppers care).

Mark each gap in the HTML report with its data-backed priority:
- 🔴 **High priority** — dimension gap AND appears in 5+ converting queries
- 🟡 **Medium priority** — dimension gap AND appears in 1-4 converting queries
- ⚪ **Low priority** — dimension gap AND doesn't appear in converting queries (address only if surface real estate allows)

When SQP is not provided, every dimension gets equal priority and this weighting step is skipped.

### Structured vs unstructured surface weighting

Alexa Shopping weights structured attributes heavily. When scoring a dimension:

- Dimension covered only in backend search terms → score 1
- Dimension covered only in unstructured copy (title/bullets/description) → score 1 or 2 per strength
- Dimension covered in a populated structured attribute → score 2 regardless of unstructured strength
- Dimension covered in both structured and unstructured → score 2, note as strength

Always flag missing structured fields even if the unstructured copy covers the angle — populating a structured field is the cheapest, highest-ROI Alexa Shopping fix.

---

## Review theme prioritization

Given review data with positive and negative topic insights, ASIN %mentions, category %mentions, and star-rating impact.

### High-priority themes to pre-empt in copy

- **Negative themes where ASIN %mentions > 2x Category %mentions.** These are differentiated weaknesses — something bothers customers about your product more than peers. Pre-empt in bullet 2 (capability) or bullet 4 (outcome).
- **Negative themes with star-rating impact <= -0.3 for ASIN.** Themes actively dragging your rating down. Highest-priority pre-empts.

### Themes to lean into

- **Positive themes where ASIN %mentions > 2x Category %mentions.** Differentiated strengths — customers love something about your product that peers don't deliver. Feature prominently in bullet 1 or 5.
- **Positive themes with star-rating impact >= +0.5 for ASIN.** Themes actively lifting your rating. Double down on the language customers use to describe these.

### Vocabulary to steal

From review snippets, extract phrases that are:
- Short (under 10 words each)
- Descriptive of the experience or outcome
- In natural customer voice

Use these patterns in bullets — **paraphrase, don't lift verbatim sentences**. A snippet saying "calms my racing mind without leaving me feeling foggy the next morning" becomes the concept "calm without fog" or "supports a calm mind without feeling foggy in the morning." Customer sentences include personal markers ("I felt...", "my husband...") that read oddly in product copy; the concept travels, the exact words don't.

**Minimum review count to trust mining:** 50 for most categories, 100 for apparel fit-patterns (which need more volume to separate signal from noise), 30 for electronics (thinner review bases). See `category-families.md` for per-category thresholds. Below the threshold, mention the review data exists but don't extract themes — flag "review data below trustworthy threshold ([N] reviews, need [threshold])" in the HTML.

---

## Competitive benchmark (Xray ASINs)

For each seller ASIN in the flat file, compare to the top 20 competitors in the Xray file (by Display Order — position in the seed search).

| Dimension | Comparison | Flag if |
|---|---|---|
| Title length | Seller vs median of top 20 | Seller is > 10% shorter than median |
| Image count | Seller vs median | Seller count < median - 1 |
| Price percentile | Where seller price sits in top 20 distribution | Below 25th percentile (may signal quality perception issue) OR above 75th (premium needs premium positioning) |
| Review count | Seller vs median | Seller < 50% of median |
| Star rating | Seller vs median | Seller < 4.0 OR (seller < median by 0.3+) |

### Positioning white-space detection

Tokenize all 20 competitor titles into individual words. Count word frequency.

- **White-space terms:** words appearing in <10% of competitor titles (0-2 out of 20) but semantically relevant to the product — positioning opportunities competitors haven't claimed
- **Saturated terms:** words appearing in >50% of competitor titles (10+ out of 20) — saturated, don't lead with them

Report the top 5 white-space terms and top 5 saturated terms per ASIN.

---

## PPC search term harvest (when PPC report is provided)

Filter the PPC search term report to rows where `orders > 0` AND `acos < 50%`.

Group by unique search term, sum impressions/clicks/orders/sales, take top 20 by orders. These are proven-converting phrases for this specific account — they've ACTUALLY converted, which is stronger evidence than SQP (SQP shows category-level patterns; PPC shows account-level proof).

**Use these in:**
- Backend search terms (include verbatim, ordered by conversion strength)
- Bullet rewrites (where the phrasing fits naturally)
- Title (if a short converting phrase fills a priority COSMO dimension)

**Also flag:** the bottom 20 by ACoS (highest ACoS, lowest ROAS, orders > 0). These are marginal performers — not necessarily negatives, but worth calling out in the HTML as "consider whether these are worth defending."

**Pure negatives** — search terms with spend > $5 AND orders = 0 — go into the HTML as negative-keyword candidates. Not part of the copy rewrite but useful for PPC optimization.

---

## Summary of what runs based on available inputs

| Input available | Diagnostic output |
|---|---|
| Flat file only | COSMO scorecard (category-routed), structured attribute gaps |
| + SQP | All of above + 5-bucket funnel diagnostic + SQP-weighted dimension priority |
| + Review XLSX | All of above + customer vocabulary extraction + objection-to-pre-empt list |
| + Xray ASINs | All of above + competitive benchmark + white-space positioning |
| + Xray keywords | Marginal sharpening of head-term decisions (pair with SQP) |
| + PPC search terms | All of above + proven-converting phrase harvest + negative-keyword flagging |

Graceful degradation means lower-tier outputs still run even when higher-tier data is missing. Always print a clear readout of what was and wasn't included.
