# Decisiones de re-brand 🏷️ (listing / creativos)

Skills con lógica genérica pero **output branded Sophie**. Ninguna depende de Sophie Hub:
el único trabajo es swappear el branding (paleta/logo/footer) por el tuyo, parametrizado
por agencia vía `brand-kit` (ver `multi-tenant-spec.md`). Revisado una-por-una.

## ✅ SE QUEDAN (9) — en el staging

| Skill | Grupo | Refs Sophie a cambiar | Nota |
|---|---|---|---|
| `listing-writer-v2` | listing/ | 1 | Redacción de listing desde cero |
| `amazon-hero-image-v12` | creative/ | 2 | Main image, corre standalone |
| `amazon-ab-testing-all-in-one` | creative/ | 0 | A/B testing de imágenes (ya brand-agnostic) |
| `ab-secondary-image-creator` | creative/ | 6 | Galería secundaria (slots 2-9) |
| `primary-image-hypotheses` | creative/ | 7 | Hipótesis a testear en la main |
| `aplus-plan-per-banner` | creative/ | 1 | Plan A+ Premium banner por banner |
| `brand-story-plan` | creative/ | 3 | Brand Story carousel |
| `brand-kit` | brand/ | 0 | **Base del branding por agencia** (multi-tenant) |
| `brand-identity-board` | brand/ | 0 | Brand board completo (PDF/PNG) |

> Nota: en `listing/` ya estaban `listing-juice-new` y `amazon-title-optimizer` (grupo 🔧).

## ❌ DESCARTADAS (4)
- `amazon-listing-optimizer` — se pisa con `listing-juice-new`.
- `alexa-audit` — Rufus/COSMO ya cubierto por `listing-juice-new`.
- `brand-defense-audit` — no la usás en el flujo.
- `sophie-creative-pipeline` — orquestador; corrés cada skill creativa suelta.

## 🔁 AUTO-DESCARTADAS (4 · duplicados/test/IP)
`amazon-listing-optimizer-75` (test variant), `listing-juice` (viejo → `listing-juice-new`),
`sophie-brand` + `sophie-society-brand` (IP de Sophie → rehacés la tuya con `brand-kit`).

## Cómo re-brandear (mismo patrón para las 9)
1. Definir tu `brand-kit` (o uno por agencia) — es la fuente de verdad del branding.
2. En cada skill creativa, reemplazar el branding Sophie hardcodeado (paleta/logo/footer)
   por lectura de `brand_kit(agency_id)` — igual que el §5 del `multi-tenant-spec.md`.
3. Las de 0 refs (`amazon-ab-testing-all-in-one`, `brand-kit`, `brand-identity-board`)
   entran casi sin tocar; el resto es swap de paleta/footer (esfuerzo bajo).

**Prioridad:** `brand-kit` primero (habilita a todas las demás) → después las creativas.
