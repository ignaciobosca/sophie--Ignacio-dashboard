# Applying the brand by medium

When you're in apply mode, find the section below that matches what you're building and use it. The goal is consistency — the user should immediately recognize their brand whether they're looking at a slide, a PDF, or an Amazon listing.

General rules that apply everywhere:
- Read `BRAND.md` first. Use the colors and typography exactly as specified.
- Match the voice and tone in any copy you write.
- Respect required and forbidden claims — these are non-negotiable.
- If the user uploaded a logo, use it. Don't redraw or recreate it.
- If a needed element is missing from the brand kit, make a reasonable on-brand choice and quietly note it at the end of your reply.

---

## HTML pages, dashboards, web reports

- Define brand colors and fonts as CSS custom properties at the top of the `<style>` block:
  ```css
  :root {
    --color-primary: #XXXXXX;
    --color-secondary: #XXXXXX;
    --color-accent: #XXXXXX;
    --color-bg: #XXXXXX;
    --color-surface: #XXXXXX;
    --color-text: #XXXXXX;
    --color-text-muted: #XXXXXX;
    --color-border: #XXXXXX;
    --font-heading: '{Heading Font}', system-ui, -apple-system, sans-serif;
    --font-body: '{Body Font}', system-ui, -apple-system, sans-serif;
  }
  ```
- Use Google Fonts via `<link>` if the brand fonts are available there; otherwise fall back to the specified system stack.
- Use the primary color for primary CTAs and headlines, secondary for supporting accents, accent sparingly for highlights and links.
- Apply the logo in the header — use the asset path from BRAND.md (e.g. `assets/logo-primary.svg`).
- Match the imagery style described in BRAND.md if you're inserting placeholder images.

## Slide decks (.pptx)

- Set the master theme colors to the brand palette before creating slides.
- Use the heading font for slide titles and the body font for content.
- Title slide should feature the logo prominently. Pull from `assets/`.
- Use the primary brand color for the title bar / accent strip across slides; keep slide backgrounds in the brand background color (or white if not specified).
- For data-driven slides (charts), set chart colors to the brand palette in this order: primary → secondary → accent → tinted versions if more series are needed.
- Match voice in slide copy: short, declarative, in the brand's tone.

## Word documents (.docx)

- Set the document's default font to the brand's body font, headings to the heading font.
- Style heading 1 in the primary color, heading 2 in the secondary color, body in the text color from BRAND.md.
- Insert the logo in the header (or top of the title page for letterhead-style docs). Pull from `assets/`.
- Match voice in body copy.

## PDFs

- Treat PDFs as either an exported HTML/Word doc (then apply the rules above) or generated programmatically (then apply colors via the chosen library — reportlab, weasyprint, etc.).
- Always include the logo on the cover or in the page header/footer.
- Use the brand's heading and body fonts. If the PDF library can't embed the brand font, fall back to the closest available and note it.

## Amazon listing copy (titles, bullets, descriptions)

- **Voice:** match BRAND.md exactly. If voice is "warm, confident, plainspoken," do not write hype-y all-caps marketing speak.
- **Required claims:** always include the standard claims listed in BRAND.md (e.g. "BPA-free," certifications) where they're true and relevant.
- **Forbidden claims:** never include anything in the forbidden list (medical claims, superlatives the brand avoids, competitor comparisons, etc.).
- **Disclaimers:** include any required disclaimers verbatim.
- **Trademark symbols:** preserve ™ / ® usage exactly as the brand uses them.
- **Title format:** follow the brand's naming convention (e.g. "{Brand} {Product Type} — {Key Feature}, {Pack Size}, {Color/Variant}").
- **Bullets:** lead with the customer benefit, support with the feature, in the brand's voice.

## Amazon A+ content modules

- Use the brand colors and fonts in any text overlays or background panels.
- Imagery should match the imagery direction in BRAND.md (lifestyle vs studio, warm vs cool, props, etc.).
- Headlines in the heading font and primary color; body copy in the body font and text color.
- Use the logo where appropriate (typically the brand-story module).
- Voice and required/forbidden claims apply to all copy.

## Brand store pages

- Same rules as A+ content. Treat the store as the most prominent expression of the brand and lean into the imagery direction and voice.

## Social posts

- Visual posts: use brand colors and the heading font for any on-image copy. Logo in the corner if appropriate.
- Caption copy: match voice. Respect forbidden claims even on social.

## Email templates

- Same as HTML — apply brand colors and fonts via inline styles (since many email clients strip `<style>` blocks). Logo at the top.
- Subject lines and preview text should match brand voice.

## Charts and infographics

- Color order: primary → secondary → accent → tints/shades of the same family. Don't use rainbow palettes unless the brand explicitly calls for them.
- Use the body font for axis labels and legends; the heading font for chart titles.
- Background should be the brand background color or white. Gridlines in the border color, muted.

## Marketing one-pagers and reports

- Cover/header uses the logo and the primary color block.
- Section headings in the heading font and primary or secondary color.
- Body text in the body font and text color.
- Voice and required claims apply throughout.
- If charts or data tables are included, follow the chart rules above.

---

## When the brand kit doesn't cover something

If you need an element that isn't specified (e.g., a 5-color chart palette but the brand only specifies 3 colors, or a UI state color when only brand colors are defined):

1. Extend on-brand: tint, shade, or desaturate existing brand colors. Pick complementary neutrals from the same temperature family.
2. Use the deliverable.
3. At the end of your reply, mention it briefly: "I picked a soft slate as the 4th chart color since you hadn't specified — happy to lock it in if you like it."

Don't ask before doing — the user picked auto-apply silently. Just choose well, deliver, and offer to formalize.
