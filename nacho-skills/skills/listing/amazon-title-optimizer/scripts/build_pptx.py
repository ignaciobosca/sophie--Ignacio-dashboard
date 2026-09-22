#!/usr/bin/env python3
"""
build_pptx.py - Sophie-Society-branded PowerPoint for the amazon-title-optimizer
skill. TWO SLIDES PER ASIN:
  Slide 1 "OPTIMIZED OPTIONS" - existing title + the 3 Title/Item Highlights options.
  Slide 2 "DATA & INSIGHTS"   - KPI tiles + the relevant-search-query table.

Delivered as a downloadable .pptx (Cowork outputs) or opened in Google Slides /
PowerPoint - NOT pushed through Drive as base64, so there is no corruption risk.

Reuses the deterministic validation from validate.py (single source of truth).
The Pass/Fail check is INTERNAL: failing options are not shown; a console WARNING
is printed so the operator fixes them. Auto-installs python-pptx if missing.

Usage:
  python build_pptx.py --in <ASIN1>_final.json [<ASIN2>_final.json ...] --out Title_Optimization_<Brand>.pptx
"""

import argparse
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from validate import (validate_field, load_restricted_keywords, is_media_category,
                      TITLE_MAX, HIGHLIGHTS_MAX, pct as _pct)

try:
    import pptx  # noqa
except ImportError:
    print("[build_pptx.py] installing python-pptx ...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", "python-pptx"])

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR, MSO_AUTO_SIZE

NAVY = RGBColor(0x1A, 0x2B, 0x3B)
ORANGE = RGBColor(0xE8, 0x64, 0x3A)
TEAL = RGBColor(0x4E, 0xCD, 0xC4)
GOLD = RGBColor(0xF5, 0xA6, 0x23)
GREEN = RGBColor(0x4C, 0xAF, 0x50)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT = RGBColor(0xF0, 0xF0, 0xEF)
GREY = RGBColor(0x60, 0x60, 0x60)

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)


def _box(slide, l, t, w, h, fill=None, line=None, shape=1):
    shp = slide.shapes.add_shape(shape, l, t, w, h)  # 1 = rectangle, 5 = rounded rect
    if fill is None:
        shp.fill.background()
    else:
        shp.fill.solid(); shp.fill.fore_color.rgb = fill
    if line is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line
    shp.shadow.inherit = False
    return shp


def _text(slide, l, t, w, h, text, size=12, color=NAVY, bold=False, align=PP_ALIGN.LEFT,
          anchor=MSO_ANCHOR.TOP, wrap=True, autofit=False):
    tb = slide.shapes.add_textbox(l, t, w, h)
    tf = tb.text_frame
    tf.word_wrap = wrap
    tf.vertical_anchor = anchor
    if autofit:  # shrink text to fit the box so long copy never overflows in the deck
        tf.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
    tf.margin_left = Pt(4); tf.margin_right = Pt(4); tf.margin_top = Pt(2); tf.margin_bottom = Pt(2)
    p = tf.paragraphs[0]; p.alignment = align
    r = p.add_run(); r.text = text
    f = r.font
    f.size = Pt(size); f.bold = bold; f.color.rgb = color; f.name = "Calibri"
    return tb


def _header(slide, d, label):
    # Taller band so the ASIN can headline it prominently.
    _box(slide, 0, 0, SLIDE_W, Inches(1.18), fill=NAVY)
    # Headline row: section label (left) + big ASIN (right, gold) — easy to see which ASIN.
    _text(slide, Inches(0.45), Inches(0.14), Inches(7.6), Inches(0.5), label,
          size=20, color=WHITE, bold=True, anchor=MSO_ANCHOR.MIDDLE)
    _text(slide, Inches(8.1), Inches(0.14), Inches(4.8), Inches(0.5),
          f"ASIN {d.get('asin','-')}", size=22, color=GOLD, bold=True,
          align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)
    # Sub-line: agency + client + context.
    _text(slide, Inches(0.45), Inches(0.7), Inches(12.45), Inches(0.32),
          f"Sophie Society   |   {d.get('brand','-')}   |   {d.get('category','-') or '-'}"
          f"   |   {d.get('window_days','-')}d   |   {d.get('run_date','-')}",
          size=11, color=TEAL, bold=True)
    _box(slide, 0, Inches(1.18), SLIDE_W, Inches(0.08), fill=TEAL)


def _kpi_tiles(slide, bm, top):
    try:
        delta_val = float(bm.get("delta_points"))
    except (TypeError, ValueError):
        delta_val = 0.0
    verdict = str(bm.get("verdict", "-")).upper()
    vcolor = {"PRESERVE": GREEN, "BALANCED": GOLD, "FLEXIBLE": ORANGE}.get(verdict, TEAL)
    tiles = [
        ("ASIN CVR", _pct(bm.get("weighted_asin_cvr")), WHITE, NAVY, GREY),
        ("Market CVR", _pct(bm.get("weighted_market_cvr")), WHITE, NAVY, GREY),
        ("vs Market", f"{'+' if delta_val >= 0 else ''}{bm.get('delta_points','-')} pts",
         WHITE, (GREEN if delta_val >= 0 else ORANGE), GREY),
        ("Verdict", verdict, vcolor, WHITE, WHITE),
    ]
    tw_, th_, gap, x = Inches(3.0), Inches(1.05), Inches(0.21), Inches(0.35)
    for label, value, fill, vcol, lcol in tiles:
        _box(slide, x, top, tw_, th_, fill=fill, line=TEAL, shape=5)
        _text(slide, x, top + Inches(0.14), tw_, Inches(0.5), value, size=24, color=vcol,
              bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        _text(slide, x, top + Inches(0.68), tw_, Inches(0.3), label, size=11, color=lcol,
              align=PP_ALIGN.CENTER)
        x += tw_ + gap


def _style_header_cell(cell, text, fill):
    cell.fill.solid(); cell.fill.fore_color.rgb = fill
    cell.text = text
    p = cell.text_frame.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    p.runs[0].font.size = Pt(12); p.runs[0].font.bold = True
    p.runs[0].font.color.rgb = NAVY; p.runs[0].font.name = "Calibri"


def _logo_path():
    here = os.path.dirname(os.path.abspath(__file__))
    for name in ("sophie-society-logo.png", "sophie-logo.png", "logo.png",
                 "sophie-society-logo.jpg", "logo.jpg"):
        p = os.path.join(here, "..", "assets", name)
        if os.path.exists(p):
            return p
    return None


def _rainbow(slide, y):
    seg = 13.333 / 6.0
    for i, color in enumerate([GOLD, ORANGE, RGBColor(0xE0, 0x3B, 0x3B),
                               RGBColor(0x2E, 0x7D, 0x32), TEAL, RGBColor(0x4A, 0x90, 0xD9)]):
        _box(slide, Inches(seg * i), y, Inches(seg + 0.02), Inches(0.13), fill=color)


def _section_header(slide, title):
    _box(slide, 0, 0, SLIDE_W, Inches(0.95), fill=NAVY)
    _text(slide, Inches(0.45), Inches(0.22), Inches(12.4), Inches(0.55), title,
          size=22, color=WHITE, bold=True)
    _box(slide, 0, Inches(0.95), SLIDE_W, Inches(0.08), fill=TEAL)


# ---------------------------------------------------------------------------
# Cover
# ---------------------------------------------------------------------------
def build_cover_slide(prs, brand, run_date, asins):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _box(slide, 0, 0, SLIDE_W, SLIDE_H, fill=NAVY)
    logo = _logo_path()
    if logo:
        try:
            slide.shapes.add_picture(logo, Inches(5.42), Inches(1.25), height=Inches(1.35))
        except Exception:
            logo = None
    if not logo:
        _text(slide, 0, Inches(1.45), SLIDE_W, Inches(0.7), "SOPHIE SOCIETY",
              size=36, color=WHITE, bold=True, align=PP_ALIGN.CENTER)
        _text(slide, 0, Inches(2.15), SLIDE_W, Inches(0.35), "AMAZON GROWTH PARTNERS",
              size=13, color=TEAL, bold=True, align=PP_ALIGN.CENTER)
    _box(slide, Inches(5.17), Inches(3.05), Inches(3.0), Inches(0.06), fill=TEAL)
    _text(slide, 0, Inches(3.35), SLIDE_W, Inches(0.8), "Title + Item Highlights Optimization",
          size=30, color=WHITE, bold=True, align=PP_ALIGN.CENTER)
    sub = brand + (f"      {len(asins)} ASIN" + ("s" if len(asins) != 1 else "") if asins else "")
    sub += f"      {run_date}"
    _text(slide, 0, Inches(4.25), SLIDE_W, Inches(0.4), sub, size=15, color=TEAL,
          align=PP_ALIGN.CENTER)
    _rainbow(slide, Inches(6.75))


# ---------------------------------------------------------------------------
# Methodology
# ---------------------------------------------------------------------------
def build_method_slide(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _section_header(slide, "How the options are weighed")
    _text(slide, Inches(0.5), Inches(1.3), Inches(12.3), Inches(0.55),
          "A search query earns its place in a title when it scores on at least one of four "
          "performance signals:", size=15, color=NAVY, bold=True)
    signals = [
        ("Purchase volume (SQP)", "High search-query purchase volume in Brand Analytics."),
        ("Above-market CVR (SQP)", "The ASIN converts that query better than the market average."),
        ("Proven orders (STR)", "Real orders on the term in the PPC Search Term Report."),
        ("180-day trend (POE)", "A rising trend in Product Opportunity Explorer, when provided."),
    ]
    y = 2.05
    for name, desc in signals:
        _box(slide, Inches(0.5), Inches(y), Inches(0.16), Inches(0.5), fill=TEAL)
        _text(slide, Inches(0.8), Inches(y - 0.03), Inches(4.3), Inches(0.5), name, size=13,
              color=NAVY, bold=True, anchor=MSO_ANCHOR.MIDDLE)
        _text(slide, Inches(5.2), Inches(y - 0.03), Inches(7.6), Inches(0.5), desc, size=12,
              color=GREY, anchor=MSO_ANCHOR.MIDDLE)
        y += 0.66
    _box(slide, Inches(0.5), Inches(5.15), Inches(12.33), Inches(1.75), fill=LIGHT, shape=5)
    _text(slide, Inches(0.78), Inches(5.32), Inches(6), Inches(0.35), "Anchor selection",
          size=14, color=ORANGE, bold=True)
    _text(slide, Inches(0.78), Inches(5.72), Inches(11.8), Inches(1.05),
          "The highest-volume term becomes the visibility lead; the highest ASIN-CVR term becomes "
          "the conversion hedge. If the top-volume term converts more than 25% below its market "
          "rate, a two-anchor hedge is flagged - so the title never puts all its weight on a term "
          "the product does not actually win.", size=13, color=NAVY)


# ---------------------------------------------------------------------------
# What you get - 3 directions
# ---------------------------------------------------------------------------
def build_options_explainer_slide(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _section_header(slide, "What you get: up to four title directions")
    cards = [
        (TEAL, "Option 1  -  Volume anchor",
         "Leads with the highest search-volume term the ASIN already converts on. The safest swap: "
         "proven demand, no need to win a new query cluster it has not been indexed for."),
        (GOLD, "Option 2  -  CVR hedge anchor",
         "Leads with the term where the ASIN's conversion rate beats the market the most. Lower "
         "volume but a higher win-rate, so it trades reach for relevance."),
        (ORANGE, "Option 3  -  Trend / differentiation",
         "Built around a query cluster growing in the POE data, or a use-case sub-niche (disposable, "
         "travel, sleep). Highest upside if the trend holds; riskiest, as it bets on forward demand."),
        (RGBColor(0x4A, 0x90, 0xD9), "Option 4  -  CTR hedge anchor",
         "Leads with a high-CTR term that also has real search volume (so it still drives "
         "visibility) and room to improve CVR (clicks well, converts below market); CVR is the "
         "secondary metric. Useful mid creative-test. Shown only when such a term exists."),
    ]
    y = 1.3
    for color, title, desc in cards:
        _box(slide, Inches(0.5), Inches(y), Inches(12.33), Inches(1.4), fill=LIGHT, shape=5)
        _box(slide, Inches(0.5), Inches(y), Inches(0.22), Inches(1.4), fill=color)
        _text(slide, Inches(0.95), Inches(y + 0.1), Inches(11.6), Inches(0.38), title,
              size=15, color=NAVY, bold=True)
        _text(slide, Inches(0.95), Inches(y + 0.52), Inches(11.6), Inches(0.82), desc,
              size=12, color=GREY)
        y += 1.5


# ---------------------------------------------------------------------------
# Optimized options - card layout, 2 options per slide (paginates to 2 slides
# when there are 4 options) so each title/highlight presents clearly.
# ---------------------------------------------------------------------------
SPINE_BY_STRATEGY = {
    "Volume anchor": TEAL,
    "CVR hedge anchor": GOLD,
    "Trend / differentiation": ORANGE,
    "CTR hedge anchor": RGBColor(0x4A, 0x90, 0xD9),
}


def _option_card(slide, b, cat, restricted, is_media, y0, h):
    spine = SPINE_BY_STRATEGY.get(b.get("strategy", ""), TEAL)
    title, hl = b.get("title", ""), b.get("item_highlights", "")
    tchk = validate_field(title, TITLE_MAX, cat, restricted, True, is_media)
    hchk = validate_field(hl, HIGHLIGHTS_MAX, cat, restricted, False, is_media)
    _box(slide, Inches(0.45), Inches(y0), Inches(12.43), Inches(h), fill=LIGHT, shape=5)
    _box(slide, Inches(0.45), Inches(y0), Inches(0.2), Inches(h), fill=spine)
    _text(slide, Inches(0.8), Inches(y0 + 0.09), Inches(11.9), Inches(0.34),
          b.get("strategy", "-"), size=15, color=NAVY, bold=True)
    _text(slide, Inches(0.8), Inches(y0 + 0.5), Inches(11.9), Inches(0.22),
          f"TITLE     {tchk['length']}/{TITLE_MAX} characters", size=9, color=GREY, bold=True)
    _text(slide, Inches(0.8), Inches(y0 + 0.71), Inches(12.0), Inches(0.5),
          title, size=13, color=NAVY, autofit=True)
    _text(slide, Inches(0.8), Inches(y0 + 1.26), Inches(11.9), Inches(0.22),
          f"ITEM HIGHLIGHTS     {hchk['length']}/{HIGHLIGHTS_MAX} characters", size=9, color=GREY,
          bold=True)
    _text(slide, Inches(0.8), Inches(y0 + 1.47), Inches(12.0), Inches(0.5),
          hl, size=12, color=NAVY, autofit=True)
    if b.get("rationale"):
        _text(slide, Inches(0.8), Inches(y0 + 2.0), Inches(12.0), Inches(0.42),
              "Why: " + b.get("rationale", ""), size=9, color=GREY, autofit=True)
    ok = tchk["pass"] and hchk["pass"]
    return None if ok else (None, b.get("strategy"), tchk["reasons"] + hchk["reasons"])


def build_option_slides(prs, d, restricted):
    cat = d.get("category", "")
    is_media = is_media_category(cat)
    bundles = (d.get("bundles") or [])[:4]
    has_ctr = any((b.get("strategy", "") or "").strip().lower() == "ctr hedge anchor" for b in bundles)
    pages = [bundles[i:i + 2] for i in range(0, len(bundles), 2)] or [[]]
    failures = []
    for pi, page in enumerate(pages):
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        label = "OPTIMIZED OPTIONS" + (f"   ({pi + 1}/{len(pages)})" if len(pages) > 1 else "")
        _header(slide, d, label)
        y = 1.55
        if pi == 0:
            ex = d.get("existing", {}) or {}
            _text(slide, Inches(0.45), Inches(1.5), Inches(1.8), Inches(0.3), "Existing title",
                  size=10, color=GREY, bold=True)
            _text(slide, Inches(2.15), Inches(1.48), Inches(10.7), Inches(0.5),
                  f"{ex.get('title','-')}  ({len(ex.get('title') or '')} chars)", size=9, color=GREY)
            y = 2.05
        avail = 7.32 - y
        ch = min(2.6, (avail - 0.15 * (len(page) - 1)) / max(1, len(page)))
        cy = y
        for b in page:
            f = _option_card(slide, b, cat, restricted, is_media, cy, ch)
            if f:
                failures.append((d.get("asin"), f[1], f[2]))
            cy += ch + 0.15
        # On the last options slide, if no CTR-hedge option was generated, say why.
        if pi == len(pages) - 1 and not has_ctr:
            ny = min(max(cy + 0.05, 6.35), 6.9)
            _box(slide, Inches(0.45), Inches(ny), Inches(12.43), Inches(0.5), fill=LIGHT, shape=5)
            _box(slide, Inches(0.45), Inches(ny), Inches(0.2), Inches(0.5),
                 fill=RGBColor(0x4A, 0x90, 0xD9))
            _text(slide, Inches(0.8), Inches(ny + 0.06), Inches(12.0), Inches(0.4),
                  "Note: a 4th option (CTR hedge anchor) was not included because the data did not "
                  "support it - no search term had high CTR with room to improve CVR at meaningful "
                  "volume.", size=10, color=GREY, autofit=True)
    return failures


# ---------------------------------------------------------------------------
# Slide 2 - data & insights
# ---------------------------------------------------------------------------
def build_data_slide(prs, d):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _header(slide, d, "DATA & INSIGHTS")
    bm = d.get("benchmark", {}) or {}
    an = d.get("anchor", {}) or {}
    va = an.get("visibility_anchor") or {}

    _kpi_tiles(slide, bm, Inches(1.55))

    ctr_a = an.get("ctr_hedge_anchor") or {}
    ctr_bit = (f"    |    CTR hedge: {ctr_a.get('search_query')}" if ctr_a.get("search_query") else "")
    detail = (f"Verdict: {str(bm.get('verdict','-')).upper()} - {bm.get('verdict_note','')}    |    "
              f"Anchor: {va.get('search_query','-')} (vol {va.get('search_query_volume','-')})    |    "
              f"Two-anchor hedge: {'Yes' if an.get('two_anchor_hedge') else 'No'}    |    "
              f"STR ad CVR {_pct(bm.get('str_overall_cvr'))}{ctr_bit}")
    _text(slide, Inches(0.35), Inches(2.78), Inches(12.6), Inches(0.4), detail, size=10, color=NAVY)

    rq = d.get("relevant_queries") or []
    _text(slide, Inches(0.35), Inches(3.25), Inches(8), Inches(0.3),
          f"RELEVANT SEARCH QUERIES  ({bm.get('relevant_query_count', len(rq))} where this ASIN converts)",
          size=12, color=ORANGE, bold=True)
    n = min(len(rq), 8)
    if n:
        tbl = slide.shapes.add_table(n + 1, 5, Inches(0.35), Inches(3.6), Inches(12.63),
                                     Inches(min(3.6, 0.42 * (n + 1)))).table
        for w, c in zip([5.13, 1.9, 1.9, 1.9, 1.8], range(5)):
            tbl.columns[c].width = Inches(w)
        for c, h in enumerate(["Search query", "Volume", "ASIN CVR", "Market CVR", "Branded"]):
            _style_header_cell(tbl.cell(0, c), h, TEAL)
        for i in range(n):
            q = rq[i]
            beats = (q.get("asin_cvr") or 0) >= (q.get("market_cvr") or 0)
            vals = [q.get("search_query", ""), f"{q.get('search_query_volume','')}",
                    _pct(q.get("asin_cvr")), _pct(q.get("market_cvr")),
                    "Yes" if q.get("is_branded") else ""]
            for c, v in enumerate(vals):
                cell = tbl.cell(i + 1, c)
                cell.fill.solid(); cell.fill.fore_color.rgb = WHITE if i % 2 else LIGHT
                cell.vertical_anchor = MSO_ANCHOR.MIDDLE
                cell.text = v
                p = cell.text_frame.paragraphs[0]
                p.alignment = PP_ALIGN.LEFT if c == 0 else PP_ALIGN.CENTER
                run = p.runs[0] if p.runs else p.add_run()
                run.font.size = Pt(10); run.font.name = "Calibri"
                # green text where the ASIN's CVR beats the market (a strength)
                run.font.color.rgb = GREEN if (c == 2 and beats) else NAVY
                run.font.bold = (c == 2 and beats)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="infiles", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    restricted = load_restricted_keywords()
    datas = []
    for path in args.infiles:
        with open(path, "r", encoding="utf-8") as fh:
            datas.append(json.load(fh))
    brand = datas[0].get("brand", "-") if datas else "-"
    run_date = datas[0].get("run_date", "-") if datas else "-"
    asins = [d.get("asin") for d in datas]

    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H
    build_cover_slide(prs, brand, run_date, asins)      # Cover
    build_method_slide(prs)                             # How options are weighed
    build_options_explainer_slide(prs)                  # What you get: 3 directions
    all_failures = []
    for d in datas:
        all_failures += build_option_slides(prs, d, restricted)  # 1-2 option slides
        build_data_slide(prs, d)                                 # data & insights slide
    prs.save(args.out)
    print(f"[build_pptx.py] wrote {args.out} ({len(prs.slides._sldIdLst)} slides: "
          f"3 intro + {len(datas)} ASIN(s))")
    for asin, strat, reasons in all_failures:
        print(f"[build_pptx.py] WARNING validation FAIL {asin} / {strat}: {'; '.join(reasons)}")


if __name__ == "__main__":
    sys.exit(main())
