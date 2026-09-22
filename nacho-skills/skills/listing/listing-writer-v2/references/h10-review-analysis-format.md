# Helium 10 Review-Analysis Export Format

Helium 10's review-analysis export is an .xlsx with up to 8 sheets. Use it at Section 6 (voice of customer) and B1 (parse) when the seller uploads one. It replaces or supplements pasted/screenshotted review text.

## Sheets and what to pull

| Sheet | What it holds | How to use it |
|---|---|---|
| Positive Topic Insights | Topic, Subtopic, ASIN/Parent/Category %Mentions, Review Snippets | The themes to AMPLIFY in copy. Rank by ASIN %Mentions. Top themes for a learning toy are usually Educational, Fun/Entertainment, Reading/Writing, Ease of Use. |
| Negative Topic Insights | same columns, complaints | The themes to NEUTRALIZE via Rule 4 counter-claims. Rank by mentions. |
| Positive Topic Trends | monthly % by topic | Confirms a theme is durable vs a spike. Optional. |
| Negative Topic Trends | monthly % | Same, for complaints. |
| Positive Star Rating Impact | topic -> star delta | The numeric weight of each positive theme on rating. Lead bullets with the highest-impact positive (often Educational). |
| Negative Star Rating Impact | topic -> negative star delta | The numeric weight of each complaint. Prioritize counter-claims by the most negative delta (often Functionality, then Quality, then Durability). |
| Returns Topics | %Mentions per return reason | GOLD for image briefs. The top return reason (often Size-Overall, then Advertised-vs-Actual) tells you which image must show scale/accuracy to cut returns. |
| Returns Trends | monthly | Optional. |

## Ranking complaints for the Rule 4 gate

Use a blend, not raw mention count alone:
1. Negative Star Rating Impact (the field that actually moves rating) is the primary sort.
2. Negative Topic Insights mention count is the secondary sort.
3. Returns Topics tells you what to fix with IMAGES rather than copy (size, "not as pictured").

A complaint qualifies for a counter-claim bullet only if Rule 4 passes (the seller's product has a feature that addresses it). Otherwise it goes to "Claims to verify."

## Parsing notes
- Multiple competitor ASIN exports may be uploaded. Merge themes across them; a complaint appearing across several competitors is a stronger neutralize target.
- A category-wide "Flash Cards" export (not ASIN-specific) gives the category baseline %Mentions, use it to see whether a complaint is product-specific or category-endemic.
- Snippets are truncated; treat them as evidence of the theme, never quote them verbatim in copy.
