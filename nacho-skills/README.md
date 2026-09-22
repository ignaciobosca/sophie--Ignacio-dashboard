# nacho-skills

Staging del **export de skills** para mi entorno propio (proyecto independiente,
colaboración con varias agencias). Copiadas desde el entorno de Sophie con OK
(construcciones colaborativas). Este folder es el punto de partida — desde acá
las llevo a mi repo `nacho-skills/` propio y las instalo en mi entorno Claude.

> Tarea de seguimiento: ClickUp → POD 66 → Interno → PPC Tasks →
> "🚀 Migración de procesos a entorno propio (Nacho)".

## Qué hay acá (Fase 1 — ✅ "portá tal cual")

Skills cuyo stack ya tengo en el entorno nuevo (SHURQ + Supabase + Slack/ClickUp).
No dependen de Sophie Hub salvo las marcadas 🔧 en `MIGRATION-NOTES.md`.

### `skills/master-dashboard/` — el sistema de dashboard (mi arquitectura)
Feeders → Supabase (`dashboard_snapshots`) → composer → GitHub Pages.
- `master-dashboard-supabase` — composer de los 7 tabs + publish a GitHub Pages
- `daily-check-dashboard-supabase`
- `daily-check-client-supabase`
- `daily-negatives-supabase`
- `daily-harvest-supabase`
- `daily-restock-supabase` 🔧 (Sophie Hub)

### `skills/ppc-ops/` — operativa PPC sobre SHURQ
- `weekly-report`, `weekly-wins`
- `search-term-harvest`
- `negative-targeting`, `daily-negatives-autopush`, `weekly-negatives-review`, `shurq-push-negatives`
- `biweekly-bid-optimizer`, `sp-sb-bulk-bid-optimizer` 🔧 (Sophie Hub)
- `launch-sponsored-products` 🔧 (Sophie Hub)
- `kw-harvester-negator` 🔧 (Sophie Hub)

### `skills/comms-workflow/` — comms y flujo diario
- `client-reply-drafter` 🔧, `client-onboarding` 🔧 (crea la config en Supabase), `slack-channel-review`, `inbox-triage`
- `client-changelog` (mové la DB de Notion), `morning`, `personal-assistant-skill`

### `skills/reporting/` — reporting 🔧 (rebuild)
- `monthly-report`

### `skills/listing/` — listing
- `listing-juice-new` 🔧 (rebuild pesado), `amazon-title-optimizer` 🔧 (liviano), `listing-writer-v2` 🏷️ (re-brand)

### `skills/research/` — research 🔧 (rebuild)
- `bundle-crosssell-finder`

### `skills/creative/` — imágenes / A+ 🏷️ (re-brand)
- `amazon-hero-image-v12`, `amazon-ab-testing-all-in-one`, `ab-secondary-image-creator`, `primary-image-hypotheses`, `aplus-plan-per-banner`, `brand-story-plan`

### `skills/brand/` — branding 🏷️ (base multi-tenant)
- `brand-kit` (base del branding por agencia), `brand-identity-board`

> El grupo 🏷️ (listing/creativos) y sus decisiones keep/drop están en
> **`docs/rebrand-decisions.md`**. No dependen de Sophie Hub: solo re-brand vía `brand-kit`.

> Las skills 🔧 que se rebuildean (y las que se descartaron) están en
> **`docs/rebuild-decisions.md`**, con el mapa Sophie Hub → SHURQ/Helium10/Keepa/DataDive,
> el orden de cutover y el gap de Subscribe & Save. Decidido una-por-una con Nacho.

## Antes de instalarlas
Leé **`MIGRATION-NOTES.md`**: lista el find/replace concreto (canales de Slack,
POD 66, link de GitHub Pages, tablas de Supabase) y qué skills necesitan cortar
la dependencia de Sophie Hub.

## Lo que NO viajó (y por qué)
- Sin secrets ni llaves de Supabase embebidas: la config se pulls en runtime
  desde `public.clients`. Hay que recrear ese schema en el Supabase nuevo (Fase 2).
- Sin data de clientes de Sophie.
- Branding Sophie (`sophie-brand`, `sophie-society-brand`) queda afuera → rehacer propio.

## Pendiente (próximas tareas)
- Fase 2: DDL del schema Supabase (`clients`, `dashboard_snapshots`, `relevance_profiles`, `dashboards`).
- Fase 3: rediseño multi-tenant (`agency_id` + `brand_kit` por agencia).
- Fase 4: rebuild de las 🔧 (cutover Sophie Hub → Helium10 / Keepa / Amazon Ads API).
