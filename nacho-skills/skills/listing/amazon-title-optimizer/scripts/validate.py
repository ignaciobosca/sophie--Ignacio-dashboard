#!/usr/bin/env python3
"""
validate.py - deterministic copy validation for the amazon-title-optimizer skill.
Pure stdlib. Single source of truth for the hard rules; imported by build_pptx.py.

Checks each Title / Item Highlights for: exact char count incl. spaces, allowed
characters, emoji, promotional language, ALL-CAPS, word repetition, and
category-restricted keywords (read from references/restricted-keywords.md).
"""

import os
import re

TITLE_MAX = 75
HIGHLIGHTS_MAX = 125
ALLOWED_CHARS_RE = re.compile(r"^[A-Za-z0-9 \-,\.]*$")
STOP_WORDS = {"a", "an", "and", "as", "at", "by", "for", "from", "in", "of", "on",
              "or", "the", "to", "with", "your"}
CAPS_ALLOWLIST = {"USB", "LED", "HD", "UV", "TV", "PC", "XL", "XXL", "ML", "OZ", "LB"}
PROMO_BANNED = [
    "free", "best seller", "bestseller", "best-selling", "best selling", "best",
    "top rated", "top-rated", "#1", "number one", "no. 1", "no 1",
    "guaranteed", "guarantee", "on sale", "sale", "discount", "deal",
    "cheapest", "cheap", "savings", "save", "bonus", "gift",
    "100%", "risk-free", "risk free", "money back", "money-back",
    "buy now", "order now", "limited time", "hottest", "hot deal",
    "amazing", "perfect", "ultimate", "world's best", "worlds best",
    "award-winning", "award winning", "proven",
]
MEDIA_TOKENS = ["book", "music", "video", "dvd", "blu-ray", "blu ray", "cd", "vinyl", "software"]
CATEGORY_ALIASES = {
    "Health & HH": ["health", "household", "health & household", "health and household", "hh"],
    "Home & Kitchen": ["home & kitchen", "home and kitchen", "home", "kitchen"],
    "Kitchen & Dining": ["kitchen & dining", "kitchen and dining", "dining"],
    "Beauty & PC": ["beauty", "personal care", "beauty & personal care", "pc"],
    "Toys & Games": ["toys", "games", "toys & games"],
    "Sports/Outdoor": ["sports", "outdoors", "sports & outdoors", "outdoor"],
    "Patio/Lawn": ["patio", "lawn", "patio, lawn & garden"],
    "Garden & Outdoor": ["garden", "garden & outdoor"],
    "Pet Supplies": ["pet", "pet supplies"],
    "Office": ["office", "office products"],
    "Tools & HI": ["tools", "home improvement", "tools & home improvement"],
    "Electronics": ["electronics"],
    "Appliances": ["appliance", "appliances"],
    "Cell Phone Acc": ["cell phone", "phone accessor", "cell phone acc"],
    "Industrial": ["industrial", "scientific"],
    "Grocery": ["grocery", "gourmet food"],
    "Clothing/Shoes": ["clothing", "shoes", "apparel", "jewelry"],
}


def _norm(s):
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def _ref_path(name):
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, "..", "references", name)


def category_buckets(category_str):
    cat = (category_str or "").lower()
    buckets = {"General"}
    for bucket, aliases in CATEGORY_ALIASES.items():
        if any(a in cat for a in aliases):
            buckets.add(bucket)
    return buckets


def is_media_category(category_str):
    return any(tok in (category_str or "").lower() for tok in MEDIA_TOKENS)


def load_restricted_keywords():
    out = []
    try:
        with open(_ref_path("restricted-keywords.md"), "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line.startswith("|"):
                    continue
                cells = [c.strip() for c in line.strip("|").split("|")]
                if len(cells) < 5:
                    continue
                kw, listing_copy = cells[0], cells[1]
                if kw.lower() == "keyword" or set(kw) <= {"-", ":", " "}:
                    continue
                if "\U0001F6A9" not in listing_copy:
                    continue
                cats = {c.strip() for c in cells[4].split(",") if c.strip() and c.strip() != "—"}
                out.append((kw, cats))
    except FileNotFoundError:
        pass
    return out


def restricted_hits(text, category_str, restricted):
    buckets = category_buckets(category_str)
    low = " " + _norm(text) + " "
    hits = []
    for kw, cats in restricted:
        if not (("General" in cats) or (cats & buckets)):
            continue
        kw_low = kw.lower()
        if re.fullmatch(r"[a-z0-9 \-]+", kw_low):
            if re.search(r"(?<![a-z0-9])" + re.escape(kw_low) + r"(?![a-z0-9])", low):
                hits.append(kw)
        elif kw_low in low:
            hits.append(kw)
    return hits


def has_emoji(text):
    return any(ord(ch) > 0x2190 for ch in text or "")


def caps_violations(text):
    bad = []
    for tok in re.findall(r"[A-Za-z][A-Za-z'\-]*", text or ""):
        if re.search(r"[A-Z]{2,}", tok) and tok.upper() == tok and len(tok) > 1 \
                and tok.upper() not in CAPS_ALLOWLIST:
            bad.append(tok)
    return bad


def repetition_violations(text):
    counts = {}
    for tok in re.findall(r"[A-Za-z0-9][A-Za-z0-9'\-]*", (text or "").lower()):
        if tok in STOP_WORDS:
            continue
        counts[tok] = counts.get(tok, 0) + 1
    return {w: c for w, c in counts.items() if c > 2}


def promo_hits(text):
    low = " " + _norm(text) + " "
    hits = []
    for term in PROMO_BANNED:
        t = term.lower()
        if re.fullmatch(r"[a-z0-9 \-]+", t):
            if re.search(r"(?<![a-z0-9])" + re.escape(t) + r"(?![a-z0-9])", low):
                hits.append(term)
        elif t in low:
            hits.append(term)
    return hits


def validate_field(text, limit, category, restricted, is_title, is_media):
    reasons = []
    length = len(text or "")
    if is_title and is_media:
        reasons.append("MEDIA: 75-char rule not enforced (manual review)")
    elif length > limit:
        reasons.append(f"OVER LIMIT: {length}/{limit}")
    if not ALLOWED_CHARS_RE.match(text or ""):
        bad = sorted(set(re.findall(r"[^A-Za-z0-9 \-,\.]", text or "")))
        reasons.append("DISALLOWED CHARS: " + " ".join(bad))
    if has_emoji(text):
        reasons.append("EMOJI")
    cv = caps_violations(text)
    if cv:
        reasons.append("ALL-CAPS: " + ", ".join(cv))
    pr = promo_hits(text)
    if pr:
        reasons.append("PROMO: " + ", ".join(pr))
    rep = repetition_violations(text)
    if rep:
        reasons.append("REPEAT>2: " + ", ".join(f"{w}({c})" for w, c in rep.items()))
    rk = restricted_hits(text, category, restricted)
    if rk:
        reasons.append("RESTRICTED: " + ", ".join(rk))
    return {"length": length, "pass": not reasons, "reasons": reasons}


def pct(v):
    try:
        return f"{float(v) * 100:.1f}%"
    except (TypeError, ValueError):
        return "-"
