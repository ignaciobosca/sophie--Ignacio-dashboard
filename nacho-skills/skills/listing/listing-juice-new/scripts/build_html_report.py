#!/usr/bin/env python3
"""
build_html_report.py, assemble the full branded HTML report from a report JSON
that Claude produces. Collapses 5-8 HTML-assembly tool calls into 1.

Usage:
    python3 build_html_report.py \\
        --report /tmp/report.json \\
        --out "/mnt/user-data/outputs/Listing Juice - <ASIN> - <Brand> - <YYYY-MM-DD>.html"

The report JSON shape Claude is expected to produce. See the schema block below.

Design principles (Listing Juice v3):
  * v3: Sophie Hub MCP-or-manual acquire + upfront intake gate (analysis core unchanged).
    The wrapper now offers an OPTIONAL Sophie Hub MCP mode that fetches the Amazon-native
    reports into the uploads dir so parse_inputs.py picks them up unchanged, with manual
    upload as the always-works fallback; the RUN GATE gathers all inputs upfront. No script
    analysis logic changed, this build script and the deterministic core are untouched by v3
    except this changelog note.

Design principles (Listing Juice v2, multi-marketplace):
  * v2 changelog: the skill now supports US, UK/EU, and other Amazon marketplaces instead of
    hard-refusing non-US. parse_inputs.py detects the marketplace from the Category Listings
    Report's marketplace_id (never blocks: unknown/missing -> warning), run_diagnostics.py
    resolves the currency-varying Helium 10 price column ($/£/€), and the report surfaces the
    detected marketplace in the header meta (MARKETPLACE / HAS_MARKETPLACE). For any non-US
    marketplace, IS_NON_US_MARKETPLACE renders a caveat that the US-based regulatory/claims
    examples and picklists must be re-checked against the local marketplace's rules and
    regulators. No other v11/A+ behavior changed.

Design principles (Listing Juice, post-V11 feedback):
  * Listing Juice changelog: always-on Sophie Society image + A+ Premium recommendations.
    Every ASIN section now carries three guaranteed blocks, sourced from
    references/sophie-society-image-and-aplus-sops.md: (1) a Main image recommendations
    screen, (2) a 7-slot Secondary image sequence, and (3) a 7-module A+ Premium plan.
    Claude emits them as a single combined raw-HTML string in the new
    sophie_recommendations_html field, and the script renders it via HAS_SOPHIE_BLOCKS /
    SOPHIE_BLOCKS into a dedicated slot in per_asin.html AFTER the rewrite section and
    BEFORE the structured-attributes blocks. This is a dedicated always-rendered slot,
    NOT routed through strict_structured_block (which the script overwrites whenever
    strict_structured_rows is present, silently dropping raw HTML). Omit the field to
    render nothing (backward compatible), but per SKILL.md Step 4b it is always required.

Design principles (V11, post-V10 feedback):
  * V11 changelog: full structured-attribute visibility. The audit's structured-attributes
    section now shows the COMPLETE category-relevant attribute set, not just the ones needing
    action. The two action sub-sections (safe-to-apply strict rows, needs-verification advisory)
    are unchanged. A new informational bucket, verified_structured_rows ({field, current,
    status}), carries the attributes that are already correct or not relevant for the category;
    build_structured_status_table renders them as a Field/Current/Status table (no proposed
    column, no copy buttons) inside a collapsed-by-default optional-section accordion right after
    the action sub-sections. HAS_COLLAPSED_STRUCTURED gates it; empty rows render nothing.

Design principles (V10, post-V9 feedback):
  * V10 changelog: SKILL.md intake/onboarding unified (no build-logic change). The single
    "When you're invoked (intake)" section now folds in the warm, plain-language onboarding
    for less-experienced sellers: a recommended-vs-optional input breakdown (Category
    Listings Report is the only must-have), friendly step-by-step "where to get each file"
    click-paths for Seller Central + Helium 10 shown when a required input is missing
    (then stop and wait), and an always-confirm-the-exact-SKU/child-ASIN rule. The single
    HTML deliverable stance and the opt-in, explicit-request-only xlsx are unchanged from V9.

Design principles (V9, post-V8 feedback):
  * Seller-facing. No internal jargon ("validation gate", "COSMO", "north star").
  * No em-dashes anywhere in Claude-authored strings. Use commas, periods, or parentheses.
  * Rewrite copy matches the current listing's voice, not an AI-neutral tone.
  * Every number traces to diagnostics.json, not visual estimation.
  * Curly quotes are typed directly, not as &ldquo;/&rdquo; entities.
  * Product facts are emitted in a machine-readable block (human table + copy-pasteable
    JSON) so downstream image-generation skills get deterministic facts, not prose. The
    pack-count conflict between the Category Listings Report unit_count and the title is
    reconciled at the source and surfaced visibly (V7).
  * Intake leads with the goal and the single HTML deliverable, then asks for inputs
    (including the target ASIN); the optional xlsx is no longer a decision gate (V8).
  * The product-facts block is image-skill handover data, not seller-facing analysis, so it
    renders as a quiet, collapsed-by-default accordion at the very END of each ASIN section,
    after all the seller-facing analysis, never mid-report (V9). Data is unchanged.


===== REPORT JSON SCHEMA =====

This is a schema, not a specific example. Every string shown below is a placeholder
describing the shape and semantic purpose of the field. Do NOT copy any of these
placeholder strings into a real report, build each field fresh from the current
run's diagnostics data.

{
  "brand": "<seller brand name from diagnostics.listing_state.brand>",
  "date": "<YYYY-MM-DD of the run>",
  "mode": 2 | 3 | 4,   // 4 = Sophie Hub listing pull (no workbook, no xlsx)
  "is_screenshot_mode": <true if mode 3 else false>,
  "has_flat_file_output": <true if an xlsx was also generated this run>,
  "header_subtitle": "<free-form subtitle, e.g. 'ASIN <id> . <Category>' or for multi-ASIN '<N> listings'>",
  "marketplace": "<detected marketplace code from diagnostics.global.marketplace, e.g. 'US', 'UK', 'DE', or 'UNKNOWN'. Shown in the header meta; any non-US value also renders a caveat that the US regulatory examples/picklists must be re-checked against the local marketplace's rules.>",

  // Headline block (the "short version" card)
  "headline_pill_class": "" | "ctr",                           // "ctr" colors the pill orange (use when CTR is the primary issue); "" uses navy
  "headline_pill_text": "<primary issue name, 4-10 words>",    // e.g. "<primary-issue-name>" such as "Pricing is the issue" or "Structured attributes missing"
  "headline_one_liner": "<one punchy sentence naming the core problem and/or strength, seller-friendly, no em-dashes>",
  "headline_plain": "<2-4 sentence plain-language summary with the key numbers from diagnostics>",

  // Opportunity cards (exactly 3)
  "top_opportunities": [
    {
      "rank": 1, "primary": true,                              // primary: true gives the card an orange rank pill
      "category": "<short tag, 1-3 words, e.g. 'Title', 'Reviews', 'Backend keywords', 'Compliance'>",
      "title": "<action title, 6-14 words>",
      "body": "<plain-language paragraph, 3-5 sentences, explaining the issue and the fix. Cite numbers from diagnostics.>",
      "why_this_one": "<one sentence on priority reasoning>"
    },
    // ranks 2 and 3: "primary": false
  ],

  // Example seller-style Alexa Shopping queries for the "How to know" section (4-6 queries)
  // Each query reads like something a real shopper would type/speak, not like a keyword
  "sample_alexa_queries": [
    "<query in natural shopper voice, no em-dashes, 4-12 words>",
    // ...
  ],

  // Apply-these-changes ordered list. Each item is already-wrapped in <strong>...</strong>
  // for the lead, followed by plain sentence. Sequence by dependency
  // (compliance fixes first, structural rewrites second, attribute fills third)
  "apply_steps": [
    "<strong><bold lead, 2-4 words>.</strong> <rest of the sentence>",
    // ...
  ],

  // Input inventory rows (data sources)
  "input_inventory": [
    {"source": "<source name>", "status": "ok"|"med"|"low", "status_label": "Used"|"Used (low sample)"|"Not provided",
     "unlocked": "<what this source contributed>"},
    // ...
  ],

  // Optional multi-ASIN reconciliation (omit for single-ASIN runs)
  "reconciliation": {
    "rows": [{"asin": "<asin>", "flat_file": true, "sqp": true, "reviews": true, "xray": true, "ppc": false}],
    "mismatches": "<free-form note on any coverage gaps, or empty string>"
  },

  "drift_flagged_asins": [],   // list of ASIN strings where portfolio drift was detected

  // One entry per audited ASIN
  "asins": [
    {
      "asin": "<ASIN>",
      "product_name_short": "<seller-friendly product name, not the full title>",
      "asin_chip_text": "<optional short warning chip text, shown in orange next to ASIN, e.g. 'Compliance + CTR issue'>",
      "nothing_to_change": false,

      // One-thing summary card (the peach-gradient block at top of ASIN body)
      "one_thing_headline": "<one-sentence framing of the biggest issue and fix>",
      "one_thing_body": "<plain-language paragraph with key diagnostic numbers>",
      "one_thing_lever": "<one sentence: the biggest action, seller-friendly>",

      // Optional compliance/suppression-risk callout at the top of the ASIN body
      // Set has_compliance_flag only when the listing has genuine compliance risk
      // (medical claims on jewelry, FDA-issue language on supplements, etc.)
      "has_compliance_flag": false,
      "compliance_flag_title": "<short title for the callout>",
      "compliance_flag_body": "<the risk explanation, seller-friendly>",

      // Funnel display (from SQP diagnostics). Omit or set has_sqp=false if no SQP data
      "has_sqp": true,
      "funnel_impressions": "<formatted number, e.g. '1,234,567'>",
      "funnel_impressions_note": "<context line under the impressions box, e.g. 'Across N tracked queries'>",
      "funnel_clicks": "<formatted number>",
      "funnel_clicks_class": "problem" | "strength" | "",          // problem = orange border, strength = green, "" = neutral
      "funnel_ctr": "<X.XX%>",
      "funnel_ctr_compare": "<comparison sentence, e.g. 'Market: X.X%, below/above'>",
      "funnel_ctr_compare_class": "warn" | "good" | "",
      "funnel_purchases": "<formatted number>",
      "funnel_purch_class": "problem" | "strength" | "",
      "funnel_cvr": "<X.XX%>",
      "funnel_cvr_compare": "<comparison sentence>",
      "funnel_cvr_compare_class": "warn" | "good" | "",

      // What we're looking at, pre-built <li> HTML. Claude assembles from diagnostics fields.
      // Include: title + char count, category, price vs market, reviews vs market, rating,
      // BSR, image count, bullet lengths, backend keyword byte count.
      "what_we_see_rows": "<li>...</li><li>...</li>...",

      // Rewrites (each uses the rewrite.html template)
      "title_rewrite": {
        "field_name": "Proposed title rewrite",
        "current_value": "<current title>",
        "current_meta": "<e.g. 'N chars'>",      // optional parenthetical on the Current label
        "proposed_value": "<proposed title>",
        "proposed_meta": "<e.g. 'N chars'>",
        "evidence_text": "<plain-language reasoning in seller voice, no em-dashes>",
        "has_assumption": false,
        "assumption_text": "<only if has_assumption: specific factual claim the seller must verify>",
        "tier_class": "",
        "did_not_ship": false
      },

      // Optional shorter-title layer (Amazon July 27 title update). Additive: omit to keep prior behavior.
      "has_title_compliance": false,
      "title_compliance_intro": "<plain seller text: this shorter-title rule was set for 2025 but never enforced, so the longer title above still works today>",
      "title_compliance_chars": "<e.g. '74 chars'>",
      "title_compliance_value": "<compliant ~75-char title: Brand + primary keyword + one differentiator + size/variant>",
      "title_compliance_note": "<plain seller text: from July 27 Amazon may auto-rewrite titles over ~75 chars without approval; you get ~14 days in Review Listings Changes; use this to stay in control>",

      // Structured product facts for downstream image-generation skills (hero + secondary).
      // Additive: omit the whole object to keep prior behavior. When present, the script renders
      // BOTH a human-readable table AND a copy-pasteable JSON object in the report. Every value
      // here must be a deterministic fact traced to the Category Listings Report (listing_state.
      // structured / title / bullets), NOT a marketing claim. Never fabricate, emit null + a note.
      "product_facts": {
        "pack_count": <int reconciled true unit count, or null if genuinely unknown>,
        "pack_count_source": "<which signal won, e.g. 'title (\"2 Pack\") over report unit_count=1'>",
        "colour": "<single value from structured color attribute, or null>",
        "material": "<full material value, not the truncated cell; e.g. 'Silicone and metal'. null if unknown>",
        "on_pack_text": null,            // ALWAYS null here, this is vision-only (read from the photo)
        // Conflict surfacing. Set has_conflict true when the report's unit_count disagrees with the
        // pack count implied by the title/bullets. The script renders a visible amber note, do not
        // silently resolve. rationale states why the chosen pack_count is correct.
        "has_conflict": <true/false>,
        "conflict_note": "<plain seller text naming both values and which detail page field to fix>",
        "rationale": "<one sentence: why the chosen pack_count is the correct one>",
        // Per-field provenance/stub notes. Each is a short string or null. on_pack_text MUST carry
        // a STUB note telling the image skill to read it from the product photo, never fabricate.
        "notes": {
          "pack_count": "<optional note, or null>",
          "colour": "<optional note, or null>",
          "material": "<note if the report value was truncated/corrected, or null>",
          "on_pack_text": "STUB: read from the actual product photo. The image skill must transcribe the on-pack text from the hero image, never invent it. Not derivable from listing or report data."
        }
      },

      "bullet_rewrites": [ rewrite, rewrite, ... ],    // usually 5 for a fully-populated listing
      "description_rewrite": { rewrite },
      "backend_rewrite": { rewrite },

      // ALWAYS-ON Sophie Society image + A+ Premium recommendations (Listing Juice).
      // A single raw-HTML string containing all THREE blocks in this order:
      //   1. Main image recommendations (heading: "Main image recommendations")
      //   2. Secondary image sequence     (heading: "Secondary image sequence")
      //   3. A+ Premium module plan       (heading: "A+ Premium module plan")
      // Sourced from references/sophie-society-image-and-aplus-sops.md, per SKILL.md Step 4b.
      // Rendered in a DEDICATED slot after the rewrites and before the structured attributes,
      // gated by HAS_SOPHIE_BLOCKS. Do NOT route these through strict_structured_block: the
      // script overwrites STRICT_STRUCTURED_BLOCK from strict_structured_rows whenever those
      // rows are present, which would silently drop the raw HTML. This field is required on
      // every run (never emit an empty block; write "current stack is on target because X").
      "sophie_recommendations_html": "<h4>Main image recommendations</h4>...<h4>Secondary image sequence</h4>...<h4>A+ Premium module plan</h4>...",

      // Pre-built HTML blocks Claude writes (structured attr tables, review tables)
      // Strict structured attributes. PREFERRED: pass strict_structured_rows and the script
      // renders the Field/Current/Proposed/Evidence table (with copy buttons) deterministically.
      // Legacy strict_structured_block (pre-built HTML) still works as a fallback if rows absent.
      "strict_structured_rows": [
        {"field": "<attribute_id>", "current": "<current value or empty>", "proposed": "<value>",
         "evidence": "<where the value comes from>"}
      ],
      "strict_structured_block": "<div class='rewrite'>...</div>",
      "has_advisory": true,
      "advisory_structured_block": "<div class='rewrite advisory'>...</div>",
      // Informational bucket (V11): category-relevant attributes that are already correct or
      // not relevant. Rendered as a Field/Current/Status table (no proposed, no copy buttons)
      // inside a collapsed-by-default accordion. Omit/empty -> accordion does not render.
      "verified_structured_rows": [
        {"field": "<attribute_id>", "current": "<current value or empty>",
         "status": "Already correct"}
      ],
      "has_claims_to_verify": true,
      "claims_to_verify_list": "<li>...</li><li>...</li>",

      // "More detail" diagnostic blocks (pre-built HTML)
      "sqp_bucket_tables": "<h4>...</h4><table>...</table>...",
      "has_reviews": true,
      "review_analysis": "<div class='two-col'>...</div>",
      "has_xray": true,
      "competitive_analysis": "<table>...</table>...",

      // 15-dimension Alexa Shopping scorecard
      "alexa_score": <int>,              // current total across 15 dimensions (range 0-30)
      "alexa_proposed_score": <int>,     // proposed total after rewrites
      "alexa_total": <int>,              // denominator. Typically 26 or 30, lower when multiple dimensions are N/A for the product type
      "cosmo_rows": [
        // Exactly 15 rows. Use seller-friendly dimension names (e.g. "Who it's for")
        // not internal COSMO codes ("Audience dim 3"). See references/cosmo.md for the full list.
        {"dim": "<seller-friendly dimension name>",
         "current": <int 0-2 | null for N/A>,
         "proposed": <int 0-2 | null for N/A>,
         "priority": "high"|"med"|"low",
         "priority_label": "High"|"Medium"|"Low"|"N/A",
         "evidence": "<one-line annotation for this dimension>"},
        // ...14 more
      ]
    }
  ]
}

Claude supplies the judgment content and pre-built HTML fragments for tables. The script
handles all scaffolding, CSS, conditional blocks, and per-ASIN layout.
"""

import argparse
import html
import json
import re
import sys
from pathlib import Path


def escape(s):
    """HTML-escape a string, preserving None/numeric.

    Use this only for plain text from the report JSON. For pre-built HTML fragments
    (tables, lists, formatted blocks), pass through unescaped, Claude is trusted
    to produce valid HTML there.
    """
    if s is None:
        return ''
    if isinstance(s, (int, float)):
        return str(s)
    return html.escape(str(s), quote=False)


def render_conditional_blocks(template, flags):
    """Process {{#FLAG}}...{{/FLAG}} and {{^FLAG}}...{{/FLAG}} blocks.

    - {{#FLAG}}...{{/FLAG}}: keep content if flags[FLAG] is truthy, else strip
    - {{^FLAG}}...{{/FLAG}}: keep content if flags[FLAG] is falsy, else strip

    Multiple passes handle nesting.
    """
    for _ in range(5):
        prev = template
        for flag, value in flags.items():
            pattern_pos = re.compile(
                r'\{\{#' + re.escape(flag) + r'\}\}(.*?)\{\{/' + re.escape(flag) + r'\}\}',
                re.DOTALL
            )
            if value:
                template = pattern_pos.sub(r'\1', template)
            else:
                template = pattern_pos.sub('', template)
            pattern_neg = re.compile(
                r'\{\{\^' + re.escape(flag) + r'\}\}(.*?)\{\{/' + re.escape(flag) + r'\}\}',
                re.DOTALL
            )
            if value:
                template = pattern_neg.sub('', template)
            else:
                template = pattern_neg.sub(r'\1', template)
        if template == prev:
            break
    return template


def render_placeholders(template, values):
    """Replace {{KEY}} with values[KEY]. Pass through unknowns for later flagging."""
    def repl(m):
        key = m.group(1)
        if key.startswith('#') or key.startswith('/') or key.startswith('^'):
            return m.group(0)
        if key in values:
            v = values[key]
            return '' if v is None else str(v)
        return m.group(0)
    return re.sub(r'\{\{([A-Z_0-9]+)\}\}', repl, template)


def build_opportunity_cards(opportunities):
    """Render the 3 top-level opportunity cards."""
    out = []
    for opp in opportunities:
        primary_class = ' primary' if opp.get('primary') else ''
        rank = opp.get('rank', '?')
        out.append(
            f'<div class="opp-card{primary_class}">'
            f'<span class="opp-rank">#{escape(rank)}</span>'
            f'<div class="opp-category">{escape(opp.get("category", ""))}</div>'
            f'<h4>{escape(opp.get("title", ""))}</h4>'
            f'<p>{escape(opp.get("body", ""))}</p>'
            f'<div class="opp-why"><strong>Why this one:</strong> {escape(opp.get("why_this_one", ""))}</div>'
            f'</div>'
        )
    return '\n'.join(out)


def build_sample_queries_list(queries):
    """Render the example-query <li>s for the 'How to know' section."""
    if not queries:
        return '<li><em>No sample queries provided.</em></li>'
    return '\n'.join(f'<li>"{escape(q)}"</li>' for q in queries)


def build_apply_steps(steps):
    """Render the apply-these-changes <li>s. Steps may contain <strong> tags,
    so they pass through unescaped. Claude is trusted to produce valid HTML here."""
    if not steps:
        return '<li>No specific apply steps were generated.</li>'
    return '\n'.join(f'<li>{step}</li>' for step in steps)


def build_cosmo_rows(cosmo_rows):
    """Render the 15-dimension Alexa Shopping scorecard rows."""
    out = []
    for row in cosmo_rows:
        current = row.get('current')
        proposed = row.get('proposed')

        def score_cell(val):
            if val is None:
                return '<span style="color: var(--text-secondary);">N/A</span>'
            # Color-code: red for 0, orange for 1, green for 2
            color = {0: '#a33', 1: 'var(--orange)', 2: 'var(--green)'}.get(val, 'var(--text)')
            return f'<span style="color: {color}; font-weight: 700;">{val}/2</span>'

        priority = row.get('priority', 'low')
        priority_label = row.get('priority_label', priority.upper())
        pill_class = {'high': 'high', 'med': 'med', 'low': 'low', 'ok': 'ok'}.get(priority, 'low')

        out.append(
            f"<tr>"
            f"<td><strong>{escape(row.get('dim', ''))}</strong></td>"
            f"<td>{score_cell(current)}</td>"
            f"<td>{score_cell(proposed)}</td>"
            f"<td><span class='pill {pill_class}'>{escape(priority_label)}</span></td>"
            f"<td style='font-size: 13px;'>{escape(row.get('evidence', ''))}</td>"
            f"</tr>"
        )
    return '\n'.join(out)


def build_structured_table(rows):
    """Render the strict structured-attribute table deterministically from data, with a copy
    button on each proposed value. Guarantees the Field/Current/Proposed/Evidence table every
    run instead of relying on hand-authored HTML."""
    if not rows:
        return ''
    out = ['<table>',
           '<thead><tr><th>Field</th><th>Current</th><th>Proposed</th><th>Evidence</th></tr></thead>',
           '<tbody>']
    for r in rows:
        field = escape(r.get('field', ''))
        cur = r.get('current', '')
        cur_disp = escape(cur) if (cur not in (None, '')) else '<span style="color: var(--text-secondary);">(empty)</span>'
        prop = r.get('proposed', '')
        if prop not in (None, ''):
            attr = html.escape(str(prop), quote=True)
            prop_cell = escape(prop) + ' <button type="button" class="copy-btn" data-copy="' + attr + '" onclick="ssCopy(this)">Copy</button>'
        else:
            prop_cell = ''
        ev = escape(r.get('evidence', ''))
        out.append('<tr><td>' + field + '</td><td>' + cur_disp + '</td><td>' + prop_cell + "</td><td style='font-size: 13px;'>" + ev + '</td></tr>')
    out += ['</tbody>', '</table>']
    return chr(10).join(out)


def build_structured_status_table(rows):
    """Render the informational structured-attribute status table (V11): the category-relevant
    attributes that are already correct or not relevant for the category. Field/Current/Status,
    with NO Copy buttons and NO proposed column, since these rows are informational only. This
    feeds the collapsed-by-default accordion. Returns '' when there are no rows."""
    if not rows:
        return ''
    out = ['<table>',
           '<thead><tr><th>Field</th><th>Current</th><th>Status</th></tr></thead>',
           '<tbody>']
    for r in rows:
        field = escape(r.get('field', ''))
        cur = r.get('current', '')
        cur_disp = escape(cur) if (cur not in (None, '')) else '<span style="color: var(--text-secondary);">(empty)</span>'
        status = escape(r.get('status', ''))
        out.append('<tr><td>' + field + '</td><td>' + cur_disp + "</td><td style='font-size: 13px;'>" + status + '</td></tr>')
    out += ['</tbody>', '</table>']
    return chr(10).join(out)


def build_rewrite_block(rewrite, template_rewrite):
    """Render a single rewrite block."""
    if not rewrite:
        return ''

    flags = {
        'HAS_ASSUMPTION': bool(rewrite.get('has_assumption')) and bool(rewrite.get('assumption_text')),
        'DID_NOT_SHIP': bool(rewrite.get('did_not_ship')),
        'HAS_CURRENT_META': bool(rewrite.get('current_meta')),
        'HAS_PROPOSED_META': bool(rewrite.get('proposed_meta')),
        'HAS_PROPOSED': bool(rewrite.get('proposed_value')),
    }
    values = {
        'TIER_CLASS': rewrite.get('tier_class', ''),
        'FIELD_NAME': escape(rewrite.get('field_name', '')),
        'CURRENT_VALUE': escape(rewrite.get('current_value', '')),
        'PROPOSED_VALUE': escape(rewrite.get('proposed_value', '')),
        'CURRENT_META': escape(rewrite.get('current_meta', '')),
        'PROPOSED_META': escape(rewrite.get('proposed_meta', '')),
        'EVIDENCE_TEXT': escape(rewrite.get('evidence_text', '')),
        'ASSUMPTION_TEXT': escape(rewrite.get('assumption_text', '')),
        'PROPOSED_VALUE_ATTR': html.escape(str(rewrite.get('proposed_value', '')), quote=True),
    }
    rendered = render_conditional_blocks(template_rewrite, flags)
    rendered = render_placeholders(rendered, values)
    return rendered


def build_product_facts_block(pf, asin):
    """Render the structured product-facts block, human table + copy-pasteable JSON.

    Downstream image-generation skills (hero + secondary image) need deterministic
    product facts. This block emits the same facts twice: a human-readable table for the
    seller and a machine-readable JSON object the image skill copies verbatim. Returns ''
    when no product_facts are supplied (additive, omitting keeps prior behavior).

    on_pack_text is always null here: it is vision-only and must be read from the actual
    product photo by the image skill, never fabricated. The JSON carries a STUB note saying so.
    """
    if not pf:
        return ''

    def fact_cell(v):
        if v in (None, ''):
            return '<span style="color: var(--text-secondary);">null (not in report)</span>'
        return escape(v)

    notes = pf.get('notes') or {}
    # Guarantee the on_pack_text STUB note is always present and never blank, regardless of
    # what Claude supplied, this field cannot come from listing/report data.
    on_pack_stub = notes.get('on_pack_text') or (
        'STUB: read from the actual product photo. The image skill must transcribe the '
        'on-pack text from the hero image, never invent it. Not derivable from listing or '
        'report data.'
    )

    def note_html(key):
        n = notes.get(key)
        return f'<div class="pf-note">{escape(n)}</div>' if n else ''

    has_conflict = bool(pf.get('has_conflict'))

    rows = [
        '<table class="product-facts-table">',
        '<thead><tr><th>Fact</th><th>Value</th><th>Source / note</th></tr></thead>',
        '<tbody>',
        '<tr><td><strong>pack_count</strong></td><td>' + fact_cell(pf.get('pack_count')) +
        '</td><td style="font-size:13px;">' + escape(pf.get('pack_count_source', '')) +
        note_html('pack_count') + '</td></tr>',
        '<tr><td><strong>colour</strong></td><td>' + fact_cell(pf.get('colour')) +
        '</td><td style="font-size:13px;">' + note_html('colour') + '</td></tr>',
        '<tr><td><strong>material</strong></td><td>' + fact_cell(pf.get('material')) +
        '</td><td style="font-size:13px;">' + note_html('material') + '</td></tr>',
        '<tr><td><strong>on_pack_text</strong></td><td>'
        '<span style="color: var(--text-secondary);">null</span></td>'
        '<td style="font-size:13px;"><span class="pf-stub">' + escape(on_pack_stub) +
        '</span></td></tr>',
        '</tbody></table>',
    ]
    table_html = chr(10).join(rows)

    conflict_html = ''
    if has_conflict:
        conflict_html = (
            '<div class="callout warning" style="margin-top:12px;">'
            '<strong>⚠️ Pack-count conflict reconciled.</strong> '
            + escape(pf.get('conflict_note', '')) + ' '
            + escape(pf.get('rationale', '')) + '</div>'
        )

    # Machine-readable JSON object the image skill copies verbatim. on_pack_text is forced to
    # null with its stub note so the downstream skill knows to read it from the photo.
    json_obj = {
        'asin': asin,
        'pack_count': pf.get('pack_count'),
        'colour': pf.get('colour'),
        'material': pf.get('material'),
        'on_pack_text': None,
        'on_pack_text_note': on_pack_stub,
    }
    if has_conflict:
        json_obj['pack_count_conflict'] = {
            'note': pf.get('conflict_note', ''),
            'rationale': pf.get('rationale', ''),
            'source': pf.get('pack_count_source', ''),
        }
    json_text = json.dumps(json_obj, indent=2, ensure_ascii=False)
    json_attr = html.escape(json_text, quote=True)

    json_html = (
        '<div class="pf-json-wrap">'
        '<div class="label-row">'
        '<div class="label-mini">Copy-pasteable JSON (for the image-generation skill)</div>'
        '<button type="button" class="copy-btn" data-copy="' + json_attr +
        '" onclick="ssCopy(this)">Copy</button></div>'
        '<pre class="pf-json">' + escape(json_text) + '</pre></div>'
    )

    # V9: de-emphasised. This is handover data for the downstream image skill, not something
    # the seller reading the audit needs. Render it as a quiet, collapsed-by-default accordion
    # tucked at the very end of the ASIN section, not a headline section in the reading flow.
    return (
        '<details class="pf-handover">'
        '<summary>Image-generation handover data (for the image skill)</summary>'
        '<div class="pf-handover-body">'
        '<p class="pf-handover-intro">Technical metadata only. Deterministic product facts '
        'the hero and secondary image skills read instead of re-deriving them from prose. '
        'on_pack_text is left blank on purpose, the image skill reads it from the actual '
        'product photo. Nothing here changes the audit above.</p>'
        + table_html
        + conflict_html
        + json_html
        + '</div></details>'
    )


def build_per_asin_section(asin_data, template_per_asin, template_rewrite, is_first):
    """Render one ASIN block."""
    flags = {
        'NOTHING_TO_CHANGE': bool(asin_data.get('nothing_to_change')),
        'HAS_SQP': bool(asin_data.get('has_sqp')),
        'HAS_REVIEWS': bool(asin_data.get('has_reviews')),
        'HAS_XRAY': bool(asin_data.get('has_xray')),
        'HAS_ADVISORY': bool(asin_data.get('has_advisory')) and bool(asin_data.get('advisory_structured_block')),
        'HAS_COLLAPSED_STRUCTURED': bool(asin_data.get('verified_structured_rows')),
        'HAS_CLAIMS_TO_VERIFY': bool(asin_data.get('has_claims_to_verify')) and bool(asin_data.get('claims_to_verify_list')),
        'HAS_COMPLIANCE_FLAG': bool(asin_data.get('has_compliance_flag')),
        'HAS_ASIN_CHIP': bool(asin_data.get('asin_chip_text')),
        'HAS_TITLE_COMPLIANCE': bool(asin_data.get('has_title_compliance')) and bool(asin_data.get('title_compliance_value')),
        'HAS_PRODUCT_FACTS': bool(asin_data.get('product_facts')),
        'HAS_SOPHIE_BLOCKS': bool(asin_data.get('sophie_recommendations_html')),
    }

    bullets = asin_data.get('bullet_rewrites', [])
    bullet_blocks = '\n'.join(
        build_rewrite_block(b, template_rewrite) for b in bullets if b
    )

    values = {
        'OPEN_IF_FIRST': 'open' if is_first else '',
        'ASIN': escape(asin_data.get('asin', '')),
        'PRODUCT_NAME_SHORT': escape(asin_data.get('product_name_short', '')),
        'ASIN_CHIP_TEXT': escape(asin_data.get('asin_chip_text', '')),

        # One-thing
        'ONE_THING_HEADLINE': escape(asin_data.get('one_thing_headline', '')),
        'ONE_THING_BODY': escape(asin_data.get('one_thing_body', '')),
        'ONE_THING_LEVER': escape(asin_data.get('one_thing_lever', '')),

        # Compliance callout
        'COMPLIANCE_FLAG_TITLE': escape(asin_data.get('compliance_flag_title', '')),
        'COMPLIANCE_FLAG_BODY': escape(asin_data.get('compliance_flag_body', '')),

        # Funnel
        'FUNNEL_IMPRESSIONS': escape(asin_data.get('funnel_impressions', '')),
        'FUNNEL_IMPRESSIONS_NOTE': escape(asin_data.get('funnel_impressions_note', '')),
        'FUNNEL_CLICKS': escape(asin_data.get('funnel_clicks', '')),
        'FUNNEL_CLICKS_CLASS': escape(asin_data.get('funnel_clicks_class', '')),
        'FUNNEL_CTR': escape(asin_data.get('funnel_ctr', '')),
        'FUNNEL_CTR_COMPARE': escape(asin_data.get('funnel_ctr_compare', '')),
        'FUNNEL_CTR_COMPARE_CLASS': escape(asin_data.get('funnel_ctr_compare_class', '')),
        'FUNNEL_PURCHASES': escape(asin_data.get('funnel_purchases', '')),
        'FUNNEL_PURCH_CLASS': escape(asin_data.get('funnel_purch_class', '')),
        'FUNNEL_CVR': escape(asin_data.get('funnel_cvr', '')),
        'FUNNEL_CVR_COMPARE': escape(asin_data.get('funnel_cvr_compare', '')),
        'FUNNEL_CVR_COMPARE_CLASS': escape(asin_data.get('funnel_cvr_compare_class', '')),

        # What we're looking at (pre-built HTML list)
        'WHAT_WE_SEE_ROWS': asin_data.get('what_we_see_rows', ''),

        # Rewrites
        'TITLE_REWRITE_BLOCK': build_rewrite_block(asin_data.get('title_rewrite'), template_rewrite),
        'BULLET_REWRITE_BLOCKS': bullet_blocks,
        'DESCRIPTION_REWRITE_BLOCK': build_rewrite_block(asin_data.get('description_rewrite'), template_rewrite),
        'BACKEND_REWRITE_BLOCK': build_rewrite_block(asin_data.get('backend_rewrite'), template_rewrite),

        # Pre-built HTML blocks
        'STRICT_STRUCTURED_BLOCK': (build_structured_table(asin_data['strict_structured_rows'])
                                   if asin_data.get('strict_structured_rows')
                                   else asin_data.get('strict_structured_block', '')),
        'ADVISORY_STRUCTURED_BLOCK': asin_data.get('advisory_structured_block', ''),
        'COLLAPSED_STRUCTURED_BLOCK': build_structured_status_table(asin_data.get('verified_structured_rows', [])),
        'CLAIMS_TO_VERIFY_LIST': asin_data.get('claims_to_verify_list', ''),
        'SQP_BUCKET_TABLES': asin_data.get('sqp_bucket_tables', ''),
        'REVIEW_ANALYSIS': asin_data.get('review_analysis', ''),
        'COMPETITIVE_ANALYSIS': asin_data.get('competitive_analysis', ''),

        # Scorecard
        'COSMO_ROWS': build_cosmo_rows(asin_data.get('cosmo_rows', [])),
        'ALEXA_SCORE': asin_data.get('alexa_score', 0),
        'ALEXA_PROPOSED_SCORE': asin_data.get('alexa_proposed_score', 0),
        'ALEXA_TOTAL': asin_data.get('alexa_total', 30),

        # Optional shorter-title layer (additive)
        'TITLE_COMPLIANCE_INTRO': escape(asin_data.get('title_compliance_intro', '')),
        'TITLE_COMPLIANCE_CHARS': escape(asin_data.get('title_compliance_chars', '')),
        'TITLE_COMPLIANCE_VALUE': escape(asin_data.get('title_compliance_value', '')),
        'TITLE_COMPLIANCE_VALUE_ATTR': html.escape(str(asin_data.get('title_compliance_value', '')), quote=True),
        'TITLE_COMPLIANCE_NOTE': escape(asin_data.get('title_compliance_note', '')),

        # Structured product facts for downstream image generation (additive)
        'PRODUCT_FACTS_BLOCK': build_product_facts_block(asin_data.get('product_facts'),
                                                         asin_data.get('asin', '')),

        # ALWAYS-ON Sophie Society image + A+ Premium recommendations (Listing Juice).
        # Raw HTML (Claude-authored, trusted) with the three guaranteed blocks. Rendered in a
        # dedicated slot, NOT via strict_structured_block. Empty string -> slot does not render.
        'SOPHIE_BLOCKS': asin_data.get('sophie_recommendations_html', ''),
    }

    rendered = render_conditional_blocks(template_per_asin, flags)
    rendered = render_placeholders(rendered, values)
    return rendered


def build_input_inventory_rows(inventory):
    """Render input inventory table rows."""
    out = []
    for item in inventory:
        status = item.get('status', 'med')
        status_label = item.get('status_label', '')
        out.append(
            f"<tr>"
            f"<td>{escape(item.get('source', ''))}</td>"
            f"<td><span class='pill {status}'>{escape(status_label)}</span></td>"
            f"<td>{escape(item.get('unlocked', ''))}</td>"
            f"</tr>"
        )
    return '\n'.join(out)


def build_reconciliation_rows(rows):
    """Render ASIN-coverage reconciliation rows."""
    def tick(v):
        return '✓' if v else '✗'
    out = []
    for r in rows:
        out.append(
            f"<tr>"
            f"<td><code>{escape(r.get('asin', ''))}</code></td>"
            f"<td>{tick(r.get('flat_file'))}</td>"
            f"<td>{tick(r.get('sqp'))}</td>"
            f"<td>{tick(r.get('reviews'))}</td>"
            f"<td>{tick(r.get('xray'))}</td>"
            f"<td>{tick(r.get('ppc'))}</td>"
            f"</tr>"
        )
    return '\n'.join(out)


# ==== TEMPLATE PATHS ====
SCRIPT_DIR = Path(__file__).parent
TEMPLATE_BASE_PATH = SCRIPT_DIR / 'html_templates' / 'base.html'
TEMPLATE_PER_ASIN_PATH = SCRIPT_DIR / 'html_templates' / 'per_asin.html'
TEMPLATE_REWRITE_PATH = SCRIPT_DIR / 'html_templates' / 'rewrite.html'


def load_templates():
    templates = {}
    for name, path in [('base', TEMPLATE_BASE_PATH),
                       ('per_asin', TEMPLATE_PER_ASIN_PATH),
                       ('rewrite', TEMPLATE_REWRITE_PATH)]:
        if not path.exists():
            print(f"ERROR: Template file missing: {path}", file=sys.stderr)
            sys.exit(2)
        templates[name] = path.read_text()
    return templates


def brand_safe(brand):
    """Filesystem-safe brand name for filename references."""
    return re.sub(r'[^A-Za-z0-9_-]', '_', brand or 'Brand')



# Wrong rewrite key names render SILENTLY BLANK, which is the worst failure mode
# in this script: the report looks finished and the seller gets an empty panel.
# The schema is current_value / proposed_value / evidence_text. It is easy to
# author them as current / proposed / rationale. Catch that here, loudly.
REWRITE_ALIASES = {
    "current": "current_value",
    "proposed": "proposed_value",
    "rationale": "evidence_text",
    "reason": "evidence_text",
    "why": "evidence_text",
}


def validate_rewrite_keys(report):
    """Raise on aliased or missing rewrite keys before anything is rendered."""
    problems = []

    def check(obj, label):
        if not isinstance(obj, dict):
            return
        for alias, correct in REWRITE_ALIASES.items():
            if alias in obj and correct not in obj:
                problems.append(
                    f"{label}: found '{alias}' but the schema expects '{correct}'. "
                    f"This would render blank."
                )
        for required in ("current_value", "proposed_value"):
            if required not in obj:
                problems.append(f"{label}: missing required '{required}'.")

    for a in report.get("asins", []) or []:
        tag = a.get("asin", "?")
        check(a.get("title_rewrite"), f"{tag} title_rewrite")
        check(a.get("description_rewrite"), f"{tag} description_rewrite")
        check(a.get("backend_rewrite"), f"{tag} backend_rewrite")
        for i, b in enumerate(a.get("bullet_rewrites", []) or []):
            check(b, f"{tag} bullet_rewrites[{i}]")

    if problems:
        raise SystemExit(
            "build_html_report: report JSON has invalid rewrite blocks.\n  - "
            + "\n  - ".join(problems)
            + "\n\nFix the key names and re-run. Rendering was stopped on purpose: "
              "wrong keys produce a report that looks complete but has empty panels."
        )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--report', required=True, help='Path to report JSON (Claude-produced)')
    ap.add_argument('--out', required=True, help='Path to write the HTML file')
    ap.add_argument('--allow-unsubstituted', action='store_true',
                    help='Write the HTML even if {{PLACEHOLDER}} markers remain. Debug only, '
                         'a seller-facing report with literal {{PLACEHOLDER}} text is a '
                         'credibility killer.')
    args = ap.parse_args()

    templates = load_templates()
    template_base = templates['base']
    template_per_asin = templates['per_asin']
    template_rewrite = templates['rewrite']

    with open(args.report) as f:
        report = json.load(f)
    validate_rewrite_keys(report)

    asins = report.get('asins', [])
    n_asins = len(asins)

    # Build per-ASIN sections
    per_asin_sections = []
    for i, asin in enumerate(asins):
        per_asin_sections.append(
            build_per_asin_section(asin, template_per_asin, template_rewrite, is_first=(i == 0))
        )
    per_asin_html = '\n'.join(per_asin_sections)

    # Build base-level data
    top_opps_html = build_opportunity_cards(report.get('top_opportunities', []))
    sample_queries_html = build_sample_queries_list(report.get('sample_alexa_queries', []))
    apply_steps_html = build_apply_steps(report.get('apply_steps', []))

    reconciliation = report.get('reconciliation', {})
    has_reconciliation = bool(reconciliation.get('rows'))
    reconciliation_rows = ''
    has_mismatches = False
    mismatch_notes = ''
    if has_reconciliation:
        reconciliation_rows = build_reconciliation_rows(reconciliation.get('rows', []))
        mismatch_notes = reconciliation.get('mismatches', '')
        has_mismatches = bool(mismatch_notes)

    drift_flagged = report.get('drift_flagged_asins', [])
    drift_html = '\n'.join(f"<li><code>{escape(a)}</code></li>" for a in drift_flagged)

    is_screenshot_mode = bool(report.get('is_screenshot_mode'))
    has_flat_file_output = bool(report.get('has_flat_file_output'))

    # Marketplace (Listing Juice v2: multi-marketplace). Surfaced in the header meta; a
    # non-US (or UNKNOWN) marketplace also renders the US-assumptions caveat block.
    marketplace = str(report.get('marketplace') or '').strip()
    has_marketplace = bool(marketplace)
    is_non_us_marketplace = has_marketplace and marketplace.upper() != 'US'

    flags = {
        'HAS_RECONCILIATION': has_reconciliation,
        'HAS_MISMATCHES': has_mismatches,
        'IS_SCREENSHOT_MODE': is_screenshot_mode,
        'HAS_DRIFT_FLAGS': bool(drift_flagged),
        'HAS_FLAT_FILE_OUTPUT': has_flat_file_output,
        'HAS_MARKETPLACE': has_marketplace,
        'IS_NON_US_MARKETPLACE': is_non_us_marketplace,
    }

    s_suffix = '' if n_asins == 1 else 's'

    values = {
        'BRAND': escape(report.get('brand', 'Portfolio')),
        'BRAND_SAFE': brand_safe(report.get('brand', '')),
        'DATE': escape(report.get('date', '')),
        'N_ASINS': n_asins,
        'S': s_suffix,
        'HEADER_SUBTITLE': escape(report.get('header_subtitle', '')),
        'MARKETPLACE': escape(marketplace),

        # Headline card
        'HEADLINE_PILL_CLASS': escape(report.get('headline_pill_class', '')),
        'HEADLINE_PILL_TEXT': escape(report.get('headline_pill_text', '')),
        'HEADLINE_ONE_LINER': escape(report.get('headline_one_liner', '')),
        'HEADLINE_PLAIN': escape(report.get('headline_plain', '')),

        # Opportunities
        'TOP_OPPORTUNITIES': top_opps_html,

        # ASIN sections
        'PER_ASIN_SECTIONS': per_asin_html,

        # Drift
        'DRIFT_FLAGGED_ASINS': drift_html,

        # How to know
        'SAMPLE_ALEXA_QUERIES_LIST': sample_queries_html,

        # How to apply
        'APPLY_STEPS': apply_steps_html,

        # Data sources
        'INPUT_INVENTORY_ROWS': build_input_inventory_rows(report.get('input_inventory', [])),
        'RECONCILIATION_ROWS': reconciliation_rows,
        'MISMATCH_NOTES': escape(mismatch_notes),
    }

    rendered = render_conditional_blocks(template_base, flags)
    rendered = render_placeholders(rendered, values)

    # Check for unsubstituted placeholders
    unsubstituted = re.findall(r'\{\{([A-Z_0-9]+)\}\}', rendered)
    unsubstituted = [u for u in unsubstituted if not (u.startswith('#') or u.startswith('/') or u.startswith('^'))]
    unique_missing = sorted(set(unsubstituted))

    if unique_missing and not args.allow_unsubstituted:
        print(f"ERROR: {len(unique_missing)} unsubstituted placeholder(s) in rendered HTML: "
              f"{unique_missing}", file=sys.stderr)
        print(f"  Fill these fields in the report JSON and re-run, or pass --allow-unsubstituted "
              f"to write the HTML anyway (debug only).", file=sys.stderr)
        sys.exit(2)

    # Secondary linter: em-dashes and HTML-entity quote bugs in Claude-authored content
    # Run over Claude-authored strings only (the rendered HTML now includes CSS which
    # may legitimately contain U+2014 in comments; we scan inside the container only).
    container_match = re.search(r'<div class="container">(.*?)</div>\s*<footer>', rendered, re.DOTALL)
    body = container_match.group(1) if container_match else rendered
    em_dashes = body.count('\u2014') + body.count('\u2013')   # em and en
    ldquo_literals = body.count('&ldquo;') + body.count('&rdquo;') + body.count('&amp;ldquo;') + body.count('&amp;rdquo;')
    if em_dashes:
        print(f"  ⚠ {em_dashes} em-dash or en-dash character(s) found in body. "
              f"Claude-authored strings should use commas/periods/parentheses instead.",
              file=sys.stderr)
    if ldquo_literals:
        print(f"  ⚠ {ldquo_literals} literal &ldquo;/&rdquo; HTML entity found in body. "
              f"These render as literal text, not curly quotes. Use \u201C/\u201D directly.",
              file=sys.stderr)

    # Write output
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(rendered)

    # Report
    total_rewrites = sum(
        (1 if a.get('title_rewrite') else 0) +
        len(a.get('bullet_rewrites', [])) +
        (1 if a.get('description_rewrite') else 0) +
        (1 if a.get('backend_rewrite') else 0)
        for a in asins
    )
    print(f"Wrote {args.out}")
    print(f"  Size: {len(rendered):,} bytes ({rendered.count(chr(10)):,} lines)")
    print(f"  ASINs: {n_asins}")
    print(f"  Rewrites rendered: {total_rewrites}")
    if unique_missing:
        print(f"  ⚠ Wrote HTML with {len(unique_missing)} unsubstituted placeholder(s) "
              f"(--allow-unsubstituted): {unique_missing[:10]}")


if __name__ == '__main__':
    main()
