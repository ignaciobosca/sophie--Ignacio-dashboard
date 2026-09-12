# Migración ADLABS → SHURQ — Guía maestra (Sophie Society / Nacho)

**Objetivo:** dejar de usar AdLabs y correr todos los skills sobre **SHURQ** manteniendo todo
funcionando. Este doc es el patrón probado con los 2 pilotos para escalar al resto.

**Estado (2026-09-12):**
- ✅ **Infra Supabase lista:** `clients.config.shurq_account_id` está cargado para los 20 clientes
  activos (backfilleé `LongTeaVity` US+CA = `1940`; los otros 18 ya lo tenían).
- ✅ **Piloto lectura migrado:** `weekly-report` (V4 · SHURQ) — validado al centavo (Natchiketa,
  Aug 31–Sep 6).
- ✅ **Piloto escritura migrado:** `daily-negatives-autopush` (V3 · SHURQ) — contrato de push validado
  (preview → confirm) sin escribir nada.
- ✅ **Prioridades de Nacho migradas (por orden de importancia):**
  1. `daily-harvest-supabase` (V2.0 · SHURQ)
  2. `weekly-negatives-review` — **EN PAUSA**: SHURQ aún no expone tool para archivar/remover *negative
     keywords* (sí lee `list_negative_targets`, y archiva product/negative-product con `remove_product_target`,
     pero no keywords). Reanudar cuando dev entregue la tool.
  3. `weekly-wins` (V6 · SHURQ)
  4. `monthly-report` (V2.0 · SHURQ)
  5. `daily-check` (V6.0 · SHURQ, config → Supabase)
  6. `ppc-adlabs-audit` → **deprecado**. Se consolidó en el `ppc-audit` (SHURQ) ya existente, adaptado a
     mi workflow (config Supabase, fix de 4 tools inexistentes, triggers/branding). Ver §5.
- ⏳ **Pendiente:** validar todo en real; reanudar `weekly-negatives-review` cuando exista la tool; migrar
  el resto de skills de menor prioridad con este mismo patrón.

---

## 1. Diferencias de conector (el corazón de la migración)

| Concepto | AdLabs | SHURQ |
|---|---|---|
| Identidad de cuenta | `team_id` + `profile_id` | `account_id` (int) + `mkp_id` (marketplace) |
| Sesión | `start_chat_session()` + `read_resource("adlabs://instructions")` | ninguna |
| Descubrir capacidades | tools fijos | `search(query)` → `get_schema(tools)` |
| Traer datos | `get_entity_data(entity_type, filters)` → reference `mcp://data/...` | tools semánticos (`get_ads_daily_trend`, `list_keywords`, `list_product_ads`, …) o `execute` (Python) |
| Filtrar/leer refs | `query(ref, SQL)`, `read(ref)`, `group_by_column`, `download_data` | el tool ya devuelve `{data:[...], metadata, summary}` materializado |
| Crear negativos | `create_entities("negative_targeting", ...)` → `preview_id` | `add_negative_keyword` / `add_negative_asin` → `action_id` |
| Aplicar | `create_entities("negative_targeting_apply", preview_id, note)` | `confirm_action(action_id)` + `get_action_status(account_id, action_id)` |
| Cambiar bids | `update_entities(...)` | `change_bid` / `change_target_bid` / `bulk_rule` → `confirm_action` |
| Crear campañas | `create_entities("campaign"/...)` | `create_campaign` / `build_campaign` / `create_ad_group` / `add_keyword` / `add_product_ad` → `confirm_action` |
| Guardrails | (n/a) | `get_my_write_guardrails` / `update_my_write_guardrails` (caps de bid/spend/acciones-día) |
| References que expiran | sí (con la sesión) | no; los previews de escritura expiran en **5 min** |

**Regla de oro del sandbox `execute` de SHURQ:** Python real (`None/True/False`), `await call_tool(...)`,
sin `json.loads` (ya viene parseado), sin `pandas`/`numpy`, sin `date.today()` (pasá `start_date`/`end_date`).

---

## 2. Resolución de cuenta (aplica a TODOS los skills)

1. Config del cliente en Supabase `public.clients` (proyecto **POD 66 - Organization**,
   `awhiobrcgghyiycxukjm`), columna `config` jsonb.
2. `account_id = int(config->>'shurq_account_id')`.
3. `mkp_id` desde `config->>'amazon_marketplace'`:
   US=1 · GB/UK=2 · CA=4 · MX=5 · BR=6 · DE=7 · ES=8 · FR=9 · IT=10 · NL=16 · PL=19 · SE=20 · BE=21 ·
   AE=15 · SA=23 · IE=24. Fallback: `list_my_accounts()` (cada cuenta lista sus `marketplaces`).
4. Los campos `adlabs_team_id`/`adlabs_profile_id` pueden quedar en el config: se **ignoran**.

### Mapeo brand → shurq_account_id (snapshot 2026-09-11)
| brand | shurq_account_id | mkp |
|---|---|---|
| Ayurveda Wellness (Urban Veda) | 1812 | US |
| BloomTrail | 1822 | US |
| Chill Rover | 1394 | US |
| Dr. Cohen's Acuball | 1845 | US |
| DynamoMe | 465 | US |
| Every Cloud (Solar Reserve) | 1815 | UK |
| Farm Made Organics | 1881 | US |
| Happy Fox | 842 | US |
| Happy Fox (CA) | 842 | CA |
| Hekaya (MyNextGen) | 1852 | US |
| House of Thalen | 1816 | US |
| Leefy Organics | 1682 | US |
| LongTeaVity | 1940 | US |
| LongTeaVity (CA) | 1940 | CA |
| Masofta Inc | 1556 | US |
| Moomade | 745 | US |
| Natchiketa | 747 | US |
| Pavida's | 1749 | US |
| Poop Juice (BURI Brands) | 1683 | US |
| Second Kind | 1793 | US |
| Zola Zola | 1844 | UK |

> Multi-marketplace (Happy Fox, LongTeaVity) comparten `account_id`; se distinguen por `mkp_id`.

---

## 3. Mapeo de datos validado (para los reporting skills)

Semana Natchiketa (acct 747, mkp 1) Aug 31–Sep 6 2026 — **reconcilia al centavo**:

| KPI | Valor | SHURQ source |
|---|---|---|
| Spend | $4,197.78 | `get_ads_daily_trend` → `sum(cost)` |
| PPC Sales | $9,044.70 | `get_ads_daily_trend` → `sum(sales)` |
| Total Sales | $15,301.65 | `get_sales_traffic` → `sum(revenue)` (== `get_orders_summary.revenue`) |
| Organic Sales | $6,256.95 | derived: Total − PPC |
| ACOS | 46.41% | spend/ppc_sales |
| TACOS | 27.43% | spend/total_sales |

**⚠️ Caveat conocido:** `get_sales_traffic.sessions` puede venir `0` en algunas cuentas (Sales &
Traffic no poblado en PG) → **Total Sessions / Total CVR** no siempre disponibles. Degradar a N/A y no
rankear, nunca inventar un proxy.

**⚠️ Ventana larga:** para rankings de ~52 semanas, si SHURQ limita el rango, paginar en chunks de
~90 días por `start_date`/`end_date` y concatenar `data[]`.

---

## 4. Catálogo de tools SHURQ por caso de uso (lo que reemplaza a AdLabs)

**Lectura / reporting:**
- `get_ads_summary`, `get_ads_daily_trend`, `weekly_change_summary` — performance PPC.
- `get_sales_traffic`, `get_orders_summary` — ventas totales / tráfico / órdenes.
- `get_pnl_summary`, `get_pnl_by_product`, `revenue_attribution` — P&L / orgánico vs PPC.
- `list_campaigns`, `list_ad_groups`, `list_keywords`, `list_search_terms`, `targeting_performance`,
  `list_advertised_products`, `list_product_ads` — inventario y performance por entidad.
- `list_my_accounts` — resolución de cuenta/marketplace.

**Escritura (siempre preview → `confirm_action` → `get_action_status`):**
- `add_negative_keyword`, `add_negative_asin` — negativos (level `ad_group`/`campaign`).
- `change_bid`, `change_target_bid`, `adjust_placement`, `bulk_rule` — bids/placements.
- `create_campaign`, `build_campaign`, `create_ad_group`, `add_keyword`, `add_product_ad`,
  `add_product_target` — creación de estructura.
- `pause_campaign`/`resume_campaign`, `pause_keyword` — estados.
- `get_my_write_guardrails` / `update_my_write_guardrails` — límites de seguridad.

---

## 5. Plan por skill (los ~18 restantes)

**Solo lectura → migración directa con el patrón de `weekly-report` (bajo riesgo):**
`weekly-wins`, `monthly-report`, `daily-check` / `daily-check-client(-supabase)` /
`daily-check-dashboard(-supabase)`, `kpi-quick-check`, `client-meeting-prep`, `client-reply-drafter`,
`master-dashboard-supabase`.

> **`ppc-adlabs-audit` → DEPRECADO (decisión 2026-09-12).** No se creó un skill nuevo: ya existía un
> `ppc-audit` (SHURQ, deck .pptx de 11 slides con branding Sophie Society) que hace exactamente el
> audit end-to-end sobre SHURQ. Se adaptó ese (config desde `public.clients` en Supabase; fix de 4
> tools que no existen en el connector actual — `list_advertised_products`/`get_pnl_by_product` →
> `query_table(sp_pnl_asin_daily)`, `get_orders_daily_trend` → `get_sales_traffic`, `get_cogs_coverage`
> → `query_table(cogs)`; triggers/branding a mi workflow) y se subió a `SHURQ/ppc-audit.skill`. El
> `.docx` del AdLabs-audit se descarta: los audits reales en Drive ya son `.pptx`. **Acción manual
> pendiente:** el `ppc-audit` canónico en `General Skills/` conviene reemplazarlo por esta versión
> adaptada, y quitar/deshabilitar `ppc-adlabs-audit` del entorno de Cowork skills.
→ Reemplazar el pull de AdLabs por `get_ads_daily_trend` / `get_ads_summary` / `get_sales_traffic` /
`get_pnl_summary`. Config `shurq_account_id` + `mkp_id`. Sin sesión/references.

**Escriben en Amazon → migración con el patrón de `daily-negatives-autopush` (validar en dry-run):**
- `daily-negatives-supabase` / `daily-negatives` (identifican; el push va acá) — el identificador lee
  search terms: `list_search_terms(account_id, mkp_id, ...)` en vez del `get_entity_data(search_term)`.
- `adlabs-push-negatives` → renombrar **`shurq-push-negatives`**: mismo motor de push que el autopush
  (targeting modes A/B/C/D resueltos vía `list_campaigns`/`list_ad_groups`/`list_product_ads`).
- `negative-targeting`, `search-term-harvest` / `daily-harvest-supabase` (harvest → `add_keyword`),
  `biweekly-bid-optimizer` (bids → `change_bid`/`bulk_rule`), `weekly-negatives-review` (archivar
  negativos), `launch-sponsored-products` (`create_campaign`/`build_campaign`).

**Config / onboarding:**
- `client-onboarding` / `onboarding-operational-tasks` → capturar `shurq_account_id` (de
  `list_my_accounts`, match por seller_name) en vez de `adlabs_team_id`/`adlabs_profile_id`.

**Orden sugerido:** (1) validar los 2 pilotos en real → (2) reporting skills (bajo riesgo, alto uso) →
(3) el identificador `daily-negatives-supabase` (para cortar la dependencia de AdLabs en el feeder) →
(4) el resto de escritura en dry-run primero → (5) onboarding.

---

## 6. Cutover
- **Routines:** cambiar el connector de las Routines de nube de **AdLabs → SHURQ** (Supabase + SHURQ)
  cuando el skill correspondiente esté migrado y validado.
- **Estrenar escritura en dry-run** (recibo `mode:"dry-run"`), pasar a `run` con confianza.
- **Rollback:** mientras un skill no esté validado, se puede seguir instalando la versión AdLabs
  original (están intactas en `General Skills/`). La subcarpeta `SHURQ/` es aditiva.
