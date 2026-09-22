# Buyer-Intent Dimensions (COSMO-style) — for SEO + AI/Alexa coverage

This is a **self-contained** coverage checklist written for this skill. Use it during generation to
widen *intent* coverage instead of repeating or stacking synonyms. It is how titles and Item
Highlights become legible to AI shopping assistants (Rufus, Alexa voice search) as well as classic
keyword search (A9).

Modern Amazon retrieval rewards listings that answer the **implicit context** behind a query, not
just the head keyword. A shopper (or Alexa) who says *"airtight glass containers for meal prep that
are dishwasher safe"* is expressing several intent dimensions at once. Cover the ones the data
supports; do not invent claims.

## The dimensions

| # | Dimension | Question it answers | Example tokens |
|---|---|---|---|
| 1 | **Product type** | What is it? | glass food containers, desk organizer |
| 2 | **Key attribute / material** | Made of / defining spec | borosilicate glass, stainless steel, bamboo |
| 3 | **Use case / job** | What is it for? | meal prep, lunch, office storage, travel |
| 4 | **Audience** | Who is it for? | for toddlers, for men, for runners |
| 5 | **Occasion / context** | When / where used? | freezer to oven, gym, camping, dorm |
| 6 | **Compatibility / fit** | Works with what? | fits standard shelves, iPhone 15, KitchenAid |
| 7 | **Quantity / format** | Pack / size / count | 10 pack, family size, 32 oz, set of 6 |
| 8 | **Functional benefit** | What problem solved? | leakproof, airtight, stackable, non-slip |
| 9 | **Quality / build signal** | Durability cue (factual) | heavy duty, reinforced, BPA-free* |
| 10 | **Care / convenience** | Upkeep | dishwasher safe, microwave safe, machine washable |

\* Some of these (e.g. "BPA-free", "eco-friendly") are **restricted in certain categories** — always
clear generated copy through `restricted-keywords.md` before finalizing.

## How to apply

- **Title:** pick the 2–4 dimensions with the strongest data backing (anchor term first), phrased as
  one natural line. Don't try to cram all ten.
- **Item Highlights:** use the remaining high-value dimensions — especially **material (2)**,
  **use case (3)**, **occasion (5)**, **care (10)** — in spoken-phrase form, since that is what Item
  Highlights surfaces in comparison and what voice assistants read back.
- **Voice/Alexa tip:** prefer the full phrase a person *says* over a clipped keyword fragment
  ("dishwasher safe glass containers for meal prep" reads better to Alexa than
  "glass container dishwasher meal prep set deal").
- Each dimension you add should be **new coverage** — if a token only restates one already present,
  drop it (see the no-synonym-stacking rule in `copy-rules.md`).
