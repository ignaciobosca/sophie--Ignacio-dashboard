# BRAND.md template

Use this structure when writing the user's `BRAND.md`. Fill in what's known. For anything genuinely missing after the intake, write `Unspecified — ask before assuming` rather than inventing. Keep the marker on the very first line.

```markdown
<!-- INTAKE_COMPLETE -->

# {Brand Name} — Brand Kit

_Last updated: {YYYY-MM-DD}_

## At a glance
- **What they sell:** {one sentence}
- **Category:** {Amazon category or general industry}
- **Target customer:** {one sentence}
- **Tagline / hero line:** {if any}

## Colors
| Role | Hex | Notes |
|---|---|---|
| Primary | #XXXXXX | {when to use} |
| Secondary | #XXXXXX | {when to use} |
| Accent | #XXXXXX | {when to use — buttons, highlights} |
| Background | #XXXXXX | {page bg} |
| Surface | #XXXXXX | {cards, panels} |
| Text — primary | #XXXXXX | |
| Text — muted | #XXXXXX | |
| Border / divider | #XXXXXX | |
| Success / Warning / Danger | #XXXXXX / #XXXXXX / #XXXXXX | only if specified |

## Typography
- **Headings:** {Font Family}, weights {e.g. 600/700}, fallback `system-ui, sans-serif`
- **Body:** {Font Family}, weights {e.g. 400/500}, fallback `system-ui, sans-serif`
- **Mono / numeric:** {Font Family or fallback}
- **Scale:** {if specified, e.g. 12 / 14 / 16 / 20 / 24 / 32 / 48}
- **Letter-spacing / case rules:** {e.g. headings in title case, all-caps for eyebrows only}

## Logo and imagery
- **Logo file(s):** `assets/{filename}` — {primary / mark / wordmark / dark / light variants present}
- **Logo clear space and min size:** {if specified}
- **Imagery style:** {lifestyle vs studio, warm vs cool, minimal vs busy, props/backgrounds, on-model vs flat lay}
- **Image color palette:** {dominant tones in product photos}
- **Examples / packaging photos:** `assets/{filename}`, `assets/{filename}`

## Voice and tone
- **Voice in three adjectives:** {e.g. warm, confident, plainspoken}
- **Sounds like:** {2–3 example phrases or taglines they love}
- **Never sounds like:** {phrases / tone / jargon to avoid}
- **Reading level / sentence length:** {if specified}
- **POV:** {first-person plural "we" / second-person "you" / etc.}

## Required and forbidden claims
- **Always include / mention:** {e.g. "BPA-free", "Family-owned since 2014", certifications, trademark symbols}
- **Never claim:** {e.g. medical claims, "best", competitor comparisons, specific allergens}
- **Required disclaimers:** {if any}

## Inspiration
- {URL or brand name} — {what to channel from it}
- {URL or brand name} — {what to channel from it}

## Notes
{Anything else the user wants Claude to remember — competitor positioning, recurring product line names, naming conventions, hashtags, etc.}
```

## Notes for the skill (not part of the template output)

- The first line MUST be `<!-- INTAKE_COMPLETE -->` so the skill knows intake is done. Without that marker, the skill will think it needs to re-run intake and the user will be re-asked everything.
- Use real markdown tables for colors — they're easy to scan and easy for Claude to parse on later runs.
- Save uploaded files into the skill's `assets/` folder and reference relative paths (e.g. `assets/logo-primary.svg`), not absolute paths, so the skill stays portable if it's re-installed elsewhere.
- If a section has no information, keep the heading and write `Unspecified — ask before assuming` underneath. Don't silently delete sections; future-you needs to know what's still open.
