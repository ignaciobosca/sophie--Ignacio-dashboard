# nacho-skills

Staging del **export de skills** para mi entorno propio (proyecto independiente,
colaboración con varias agencias). Copiadas desde el entorno de Sophie con OK
(construcciones colaborativas). Este folder es el punto de partida — desde acá
las llevo a mi repo `nacho-skills/` propio y las instalo en mi entorno Claude.

> Tarea de seguimiento: ClickUp → POD 66 → Interno → PPC Tasks →
> "🚀 Migración de procesos a entorno propio (Nacho)".

## Qué hay acá — triage COMPLETO

De **96 skills** en Sophie, me llevo **42** (24 ✅ portá tal cual · 8 🔧 rebuild · 10 🏷️ re-brand).
Organizadas en `skills/` por grupo: master-dashboard, ppc-ops, comms-workflow,
reporting, listing, research, creative, brand, setup.

➡️ **La lista completa, con tag por skill y orden de arranque, está en
[`docs/INVENTORY.md`](docs/INVENTORY.md).** Es la fuente de verdad.

Registros de decisión (revisado una-por-una con Nacho):
- `docs/rebuild-decisions.md` — las 🔧 (cutover Sophie Hub) + mapa de reemplazo.
- `docs/rebrand-decisions.md` — las 🏷️ (branding vía brand-kit).
- `docs/utilities-comms-decisions.md` — research liviano / utilidades / comms.
- `docs/multi-tenant-spec.md` — cómo una base de skills sirve a varias agencias.

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
