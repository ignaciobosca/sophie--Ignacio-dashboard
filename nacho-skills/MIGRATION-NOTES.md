# MIGRATION NOTES — de-Sophie-fication

Referencias hardcodeadas a Sophie que hay que cambiar **antes** de usar las
skills en mi entorno. Extraído por grep sobre el source copiado.

## 1. Dependencia de Sophie Hub 🔧 (rebuild obligatorio)
Estas skills tiran del MCP `Sophie_Hub`, que NO voy a tener. Reapuntar a
**Helium10 + Keepa/DataDive + Amazon Ads API (Adlabs) + SHURQ**:

| Skill | Uso de Sophie Hub | Reemplazo sugerido |
|---|---|---|
| `master-dashboard/daily-restock-supabase` | `get_restock_recommendations` | Helium10 inventory / Amazon Ads API restock, o SHURQ |
| `ppc-ops/kw-harvester-negator` | data de keywords/search terms | SHURQ `list_search_terms` + Helium10 |
| `ppc-ops/launch-sponsored-products` (+ `references/amazon-ads-sp-api.md`) | creación de campañas | SHURQ `create_campaign` / Amazon Ads API directo |
| `ppc-ops/sp-sb-bulk-bid-optimizer` | push de bids / placement | SHURQ `apply_bid_changes` |
| `comms-workflow/client-reply-drafter` | contexto de cuenta | SHURQ + ClickUp + Slack |

> El resto de las skills de este export NO dependen de Sophie Hub — solo
> necesitan el find/replace de abajo.

## 2. Canales de Slack (find → replace por tu workspace)
| Hardcodeado | Cambiar a |
|---|---|
| `#pod-66-team` | tu canal de equipo / notificaciones |
| `#harvest-and-negations` | tu canal de harvest/negativos |
| `#client-drafts-nacho` | tu canal de drafts de cliente |
| `#tbody-bids` | tu canal de bids |
| `#nacho-personal` | tu canal personal |
| `#matias-inbox-triage` | tu canal de inbox triage |
| `#masofta-sophie`, `#inbox` | según corresponda por agencia |

## 3. POD 66 / branding interno
- Reemplazar todas las menciones a **"POD 66" / "pod-66"** (15+ ocurrencias) por
  tu nombre de proyecto o hacerlo parámetro por agencia.

## 4. GitHub Pages (master dashboard)
- Link hardcodeado: `ignaciobosca.github.io/sophie--Ignacio-dashboard/`
  (5 ocurrencias, en el composer `master-dashboard-supabase`).
- Cambiar por tu repo/Pages nuevo. Recomendado: repo dedicado
  `nacho-dashboard` (no reusar el de Sophie) con GitHub Pages activo.

## 5. Tablas de Supabase (recrear el schema en tu proyecto)
Las skills asumen estas tablas (config + snapshots):
- `public.clients` (40 refs) — config por cliente
- `public.dashboard_snapshots` (27 refs) — feeders escriben acá
- `public.relevance_profiles` (9 refs) — perfiles de relevancia (negativos)
- `public.dashboards` (4 refs) — template del master (id='master')

➡️ Fase 2: exportar el DDL de estas 4 tablas (estructura, sin data) y aplicarlo
en el Supabase nuevo.
➡️ Fase 3 (multi-tenant): agregar `agency_id` a `clients` y una tabla
`brand_kit` por agencia para parametrizar el branding.

## Checklist rápido de cutover por skill
- [ ] Reapuntar MCP `Sophie_Hub` → alternativas (5 skills 🔧)
- [ ] Find/replace de canales Slack (todas las que notifican)
- [ ] Find/replace "POD 66" → proyecto propio
- [ ] Cambiar link GitHub Pages en `master-dashboard-supabase`
- [ ] Recrear schema Supabase + `agency_id` + `brand_kit`
- [ ] Reconfigurar credenciales SHURQ/ClickUp/Slack por agencia
