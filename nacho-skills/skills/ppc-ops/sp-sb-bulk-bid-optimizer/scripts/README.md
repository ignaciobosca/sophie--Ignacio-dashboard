# Bid optimizer regression harness

Two files. No dependencies beyond `openpyxl`.

```
python3 make_fixture.py          # writes fixture_bulk.xlsx
python3 verify.py path/to/SKILL.md
```

`kw_research.xlsx` / `.csv` / `.txt` are the keyword-research fixtures for the strategic-keep
checks. All three hold the same five terms in different shapes, plus a section-header row and a
numeric row that must NOT be read as keywords.

`verify.py` extracts the four embedded Python blocks straight out of the SKILL.md,
imports them, and runs 100 checks:

- the four scripts parse and import
- the placement dials behave per strategy (Ranking Push +25pp on Top of Search only,
  Profit-First +5pp, Balanced +15pp, all cut at -50pp)
- a 0% SP placement can be created, is flagged, and a weak one is still left alone
- a rising bid respects the max-change cap after the visibility-floor reorder
- the scorer runs clean across all five strategies and sp / sb / both
- the approved xlsx has one sheet per ad product, never mixes them, and stores every
  ID column as text
- the dashboard renders, has no browser-clock leak, and carries no stale rule copy
- the same inputs produce byte-identical scorer JSON and byte-identical HTML
- the chosen currency symbol reaches the dashboard and the approved JSON
- a search-term row with no State column is still evaluated, a paused one is still skipped
- a missing SP search-term sheet is reported as skipped, never as zero waste
- v4.0: Shopper Cohort rows never become placement rows; low-data targets are never bid down on
  any strategy; the low-data tab, sort/filter, tab dots and save-plan all work, and sorting or
  filtering never changes what gets exported
- the strategic-keep flag: all three file formats agree, matching is case-insensitive, headers
  and numeric noise are not read as keywords, the flagged row sorts first and carries the keep
  instruction, and — the check that matters most — supplying keyword research changes **no** bid,
  pause, placement or budget, for either ad product

The scratch dir is wiped on every run. It reused it once, and a stale artifact from the
previous version passed a check the version under test actually failed - so point it at an
older SKILL.md occasionally and confirm the new checks go red. A suite that cannot fail is
not telling you anything.

The fixture is deliberately awkward: branded and non-branded keywords, a zero-click
target, an auto row with no explicit bid, a product target, SB across all three ad
formats, the duplicated legacy SB sheet Amazon really emits, and search terms for both
products. Add a case to `make_fixture.py` whenever you find a new edge.
