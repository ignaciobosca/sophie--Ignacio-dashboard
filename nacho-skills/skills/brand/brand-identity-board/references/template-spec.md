# Brand Board — Template Specification

The FIXED layout contract for every board. Nothing here changes between
brands; all brand-specific content comes from the brand identity JSON
(schema: `brand-identity-schema.json`).

Canvas: vertical stack, single column, 1480 px wide, ~4400 px tall.
Full-bleed bands stacked edge to edge, no outer margin. Sections are sized to
their content (a dense, deliberate rhythm) — no airy empty bands and no dead
white margin after the last pattern band.

## Section heights (px on the 1480-wide canvas)

| # | Section | Height | Background |
|---|---|---|---|
| 1 | Logo header | 360 | `lightest` (or `darkest` if logo is light/metallic) |
| 2 | Logo variations | 260 | 50/50 split: `accent_primary` block + `dark` block |
| 3 | Fonts | 300 | white |
| 4 | Color palette | 280 | white |
| 5 | Moodboard grid | 900 | white gutters, 12 px; container `overflow:hidden` |
| 6 | Voice & Tone | auto | white |
| 7 | Claims | auto | white |
| 8 | Pattern band A | 700 | pattern asset |
| 9 | Pattern band B | 460 | pattern asset |

Voice & Tone and Claims are text-only sections (no image generation); they grow
to fit their content. Everything in them is token-driven from the brand kit's
`voice{}` and `claims{}` objects.

## Section rules

1. **Logo header** — primary logo centered. Nothing else. **If a logo image is
   supplied, place the actual image here via the `{{LOGO_IMAGE}}` token (as an
   `<img>` or a `background-image`). Never recreate the wordmark by typesetting
   it in the board fonts.** Only when no logo file exists: typographic stand-in
   + visible "LOGO PLACEHOLDER" tag.
2. **Logo variations** — the same logo centered in each block, identical size
   both sides. **If a logo image is supplied, place the actual image in both
   slots** (the `{{LOGO_IMAGE}}` token) on backgrounds that suit the logo's
   colors. If a light-on-dark variant is needed and the logo has only one color,
   you may apply a simple CSS filter (e.g. `filter: invert(1)`) as a fallback —
   never re-typeset the wordmark. Only when no logo image exists: use the
   reversed (light) text wordmark in each block.
3. **Fonts** — centered letter-spaced `F O N T S` label; two columns split
   by a 1 px rule. Left: `SPECIAL FONT` micro-label, large Aa, font name,
   alphabet rows (caps / lowercase / numerals). Right: `MAIN FONT`, same.
   Caps-only fonts: omit the lowercase row. Specimens render in the real
   fonts via @font-face.
4. **Palette** — exactly 5 circles, equal size, one row, lightest → darkest.
   Uppercase hex under each in gray micro-text.
   Slot roles: lightest neutral / accent-or-light-mid / accent-or-mid /
   dark muted / near-black anchor.
5. **Moodboard** — 3 columns (32% / 33% / 35%, 12 px gutters):
   - col A: hero product shot, full column height (no filler chip row)
   - col B: lifestyle person shot, full height
   - col C: context shot over close-up shot (equal halves)
   The columns divide their height evenly so the grid fills cleanly with no
   leftover gap — there are NO filler color chips. The grid container and every
   `.ph` cell are `overflow:hidden`, and each image is `background center/cover`
   on its own cell, so an image is always clipped/contained to its rectangle and
   can never bleed off the page edge (no negative-x placement). All images graded
   to the brand palette. When injecting a moodboard image, set the `.ph`
   background and delete that slot's placeholder `.slot`/`.brief` children so no
   caption overlaps the photo.
6. **Voice & Tone** — text-only. Centered `V O I C E  &  T O N E` label, then the
   `voice.adjectives` as pills (first pill uses the accent fill, the rest plain).
   Below, a two-column lean-in / avoid pair: left "SOUNDS LIKE" lists
   `voice.sounds_like`, right "NEVER SOUNDS LIKE" lists `voice.never_sounds_like`. A
   meta line under that shows the `reading_level` and `pov`. The two lists sit on
   tinted **card panels** (rounded, padded, palette-fill, like the guardrail box):
   the positive "SOUNDS LIKE" card uses the `lightest` fill with a warm `accent`
   top rule; the "NEVER SOUNDS LIKE" card is a neutral muted panel. The section
   label is tinted with the warm `accent`/`slot3` token to tie the lower half back
   to the warm header. All pills/lines are palette-token driven; no AI image.
   These lists are **variable-length**: the
   template carries one exemplar element of each (one pill, one `SOUNDS LIKE` line,
   one `NEVER SOUNDS LIKE` line); the fill step **repeats that element once per
   entry** in the brand kit — never a fixed slot count. The pill row wraps to
   multiple rows (`flex-wrap`); each list grows vertically.
7. **Claims** — text-only. Centered `C L A I M S` label (warm `accent`/`slot3`
   tint), then `claims.required` as accent pills under a "SAY THIS" micro-label,
   all sitting on a tinted **"SAY THIS" card panel** (rounded, `lightest` fill,
   warm accent top rule) so the approved claims read as a designed set. Below, a
   distinct **guardrail box**
   (accent border, `lightest` fill, warning glyph) holding `claims.forbidden` as a
   "NEVER CLAIM" list and `claims.disclaimers` as disclaimer line(s). The guardrail
   box is visually flagged so forbidden claims can't be mistaken for usable copy.
   Every claims list is **variable-length** — this is a compliance section, so no
   claim may ever be silently dropped. The template carries one exemplar element of
   each (one required-claim pill, one forbidden-claim line, one disclaimer line); the
   fill step **repeats that element once per `claims.required[]` /
   `claims.forbidden[]` / `claims.disclaimers[]` entry — never a fixed slot count**,
   and omits the disclaimer line entirely if there are none. The pill row wraps
   (`flex-wrap`); the guardrail list grows vertically.
8. **Pattern A** — full-width asset. The band carries **no centered overlay label**.
   The only placeholder element is a small `.corner-caption` ("PATTERN A — to
   generate") shown in the un-generated state. When the pattern image is injected,
   set the section `background-image` and DELETE the `.corner-caption`. There is no
   centered label that could overlap the artwork — the template is structurally
   correct rather than relying on the render step to delete a centered element.
9. **Pattern B** — full-width asset, opposite tonality to A (one light
   background, one dark). Same rule: small corner caption only; delete
   `.corner-caption` when filled. No centered label.

## Global rules

- Only the two brand fonts appear on the board; only palette colors (plus
  white) appear in flat graphic elements.
- **If a logo image is supplied, use it directly as a placed image in the
  header (S1) and both variation slots (S2). Never recreate the wordmark by
  typesetting it in the board fonts.** The text-wordmark markup is the no-logo
  placeholder path only. For a light-on-dark variation with a single-color
  logo, a simple CSS filter (e.g. `invert`) is an acceptable fallback.
- Hex codes uppercase everywhere.
- Section order fixed 1→9; no omissions or additions.
- Pattern motifs tie to the product category — never generic decoration.
- Voice & Tone and Claims are pure HTML/CSS text — they render with no imagery,
  so the board PDF is a complete one-pager even before any photo asset lands.

## Render command (PNG, then PDF)

The board is delivered as a PDF (the headline deliverable) plus a PNG. Both come
from the same headless Chrome that is already available — no extra install.

PNG (for visual QA and the moodboard previews):

```
chrome --headless=new --disable-gpu --hide-scrollbars \
  --window-size=1480,5200 --virtual-time-budget=15000 \
  --screenshot="board-vN.png" "file:///<abs-path>/board.html"
```

PDF (the auto-delivered final file — see SKILL.md Phase 5):

```
chrome --headless=new --disable-gpu --no-pdf-header-footer \
  --virtual-time-budget=15000 \
  --print-to-pdf="/creative-brief/<ASIN>/board.pdf" "file:///<abs-path>/board.html"
```

URL-encode spaces in the file path (`%20`). `msedge` / `chromium` accept the same
flags if `chrome` is absent. Always read the output PNG afterwards and verify
visually before handing over the PDF.

## Variable font diagnosis (fvar parser)

If a @font-face specimen renders at a weird width/weight, the variable
font's default instance is at an axis extreme. Read the real axis ranges,
then pin `font-variation-settings` (e.g. `"wdth" 650, "wght" 500`).
Axis ranges are often non-standard — never assume wdth 100 = normal.

PowerShell:

```powershell
$bytes = [System.IO.File]::ReadAllBytes("font.ttf")
function RU16($o){ ($bytes[$o] -shl 8) -bor $bytes[$o+1] }
function RU32($o){ ([uint32]$bytes[$o] -shl 24) -bor ([uint32]$bytes[$o+1] -shl 16) -bor ([uint32]$bytes[$o+2] -shl 8) -bor [uint32]$bytes[$o+3] }
function RFix($o){ $v = RU32 $o; if ($v -gt 2147483647) { $v -= 4294967296 }; [math]::Round($v / 65536.0, 2) }
$numTables = RU16 4
for ($i=0; $i -lt $numTables; $i++) {
  $rec = 12 + 16*$i
  if ([System.Text.Encoding]::ASCII.GetString($bytes, $rec, 4) -eq 'fvar') { $fvarOff = RU32 ($rec+8) }
}
$axesOff = RU16 ($fvarOff+4); $axisCount = RU16 ($fvarOff+8); $axisSize = RU16 ($fvarOff+10)
for ($a=0; $a -lt $axisCount; $a++) {
  $ao = $fvarOff + $axesOff + $a*$axisSize
  "{0}  min={1} default={2} max={3}" -f [System.Text.Encoding]::ASCII.GetString($bytes, $ao, 4), (RFix ($ao+4)), (RFix ($ao+8)), (RFix ($ao+12))
}
```

Python equivalent: `pip install fonttools`, then
`from fontTools.ttLib import TTFont; [(a.axisTag, a.minValue, a.defaultValue, a.maxValue) for a in TTFont("font.ttf")["fvar"].axes]`.

## Cropping text artifacts off generated images

PowerShell (no dependencies):

```powershell
Add-Type -AssemblyName System.Drawing
$src = [System.Drawing.Bitmap]::FromFile("img.png")
$rect = New-Object System.Drawing.Rectangle(0, 0, $src.Width, <newHeight>)
$dst = $src.Clone($rect, $src.PixelFormat); $src.Dispose()
$dst.Save("img-clean.png", [System.Drawing.Imaging.ImageFormat]::Png); $dst.Dispose()
```

Python: `PIL.Image.open("img.png").crop((0, 0, w, new_h)).save("img-clean.png")`.
