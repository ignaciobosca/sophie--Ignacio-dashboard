# Supabase — diccionario de datos

Estructura real del schema `public` del Supabase de POD 66 (leído en vivo).
**Solo estructura, sin data de clientes.** El DDL está en `schema.sql`.

## Tablas

| Tabla | PK | Filas (origen) | Rol |
|---|---|---|---|
| `clients` | `brand` | 22 | Config por cliente. La leen todas las skills. |
| `dashboard_snapshots` | `id` | ~2.7k | Feeders upsert 1 fila por `(cliente,tipo,fecha)`. Lo lee el composer. |
| `dashboards` | `id` | 3 | Templates/artefactos. Fila `id='master'` = master dashboard. |
| `relevance_profiles` | `brand` | 22 | Perfil de relevancia por brand (negativos). |
| `organic_rank_snapshots` | `id` | ~5.5k | Snapshots semanales de rank (weekly-organic-ranks). |

> Nota: en el origen existen 2 tablas de backup (`dashboards_backup_i18n`,
> `_master_tmpl_bak`) con **RLS deshabilitado** — NO migrar, son basura/backups.

## `clients.config` (jsonb) — keys reales
Agrupadas por función:

- **Targets/stage:** `acos_target`, `tacos_target`, `target_notes`, `target_source`, `account_stage`, `monthly_budget`, `monthly_budget_note`, `budget_currency`
- **Identidad producto:** `brand_name`, `alternative_names`, `alternative_names_note`, `product_category`, `managed_asins`, `competitor_asins`
- **Conectores/IDs externos:** `shurq_account_id`, `amazon_marketplace`, `adlabs_profile_id`, `adlabs_team_id`, `datadive_niche_id`, `datadive_rank_radar_id`, `drive_folder_id`, `dashboard_url`
- **Slack:** `slack_internal_channel_id`, `slack_internal_channel_name`, `slack_external_channel_id`, `slack_names`, `slack_names_note`
- **Contacto/owners:** `contact`, `email`, `phone`, `owners`
- **Estado/flags:** `active`, `paused`, `paused_date`, `paused_reason`, `autopush_paused`, `onboarding_date`, `team_took_over_date`, `report_language`, `notes`

## `relevance_profiles.profile` (jsonb) — keys reales
`brand_name`, `product_fiche`, `roots`, `competitors`, `competitors_note`,
`allowlist`, `negatives_exact`, `protected_relevant`, `pending_review`,
`change_log`, `config_stem`, `schema`, `semantics_note`, `notes`,
`updated`, `updated_by`.

## `dashboard_snapshots.tipo` — valores reales
`daily_check`, `harvest`, `negatives`, `negatives_push`, `negatives_review`,
`optimizations`, `restock`.
(Cada uno alimenta un tab del master dashboard; `datos` es el payload jsonb del día.)

## Cómo se conecta con las skills
- Los feeders (`daily-*-supabase`, `biweekly-bid-optimizer`) resuelven config desde
  `clients` y hacen **upsert** a `dashboard_snapshots` por el unique `(cliente,tipo,fecha)`.
- El composer `master-dashboard-supabase` lee `dashboard_snapshots` + el template de
  `dashboards` (id='master') y publica el HTML.
- Los skills de negativos leen/escriben `relevance_profiles`.

## Credenciales
- Escritura vía **service_role key** (bypassa RLS). Guardala como secret del entorno,
  nunca en las skills ni en git.
- En cada skill hay que reapuntar el **project ref / URL** del Supabase nuevo.
