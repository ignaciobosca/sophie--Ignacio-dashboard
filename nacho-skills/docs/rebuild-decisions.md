# Decisiones de rebuild 🔧 (skills que dependían de Sophie Hub)

Registro de la revisión una-por-una. De las 28 skills con dependencia de Sophie Hub:
**8 se rebuildean, 13 se descartan, 7 eran duplicados/test (auto-descartadas).**

## ✅ SE REBUILDEAN (8) — en el staging

| Skill | Grupo | Esfuerzo | Fuente de reemplazo |
|---|---|---|---|
| `monthly-report` | reporting/ | Medio | SHURQ (sales, orders, ads, P&L `get_pnl_summary`, top products, organic) + **Helium10** (SQP, inventory) + Keepa/DataDive directo. ⚠️ S&S = gap |
| `daily-restock-supabase` | master-dashboard/ | Medio | **Helium10** (`get_fba_inventory_health_status`, `get_inventory_values`, `get_sales_velocity`) |
| `launch-sponsored-products` | ppc-ops/ | Medio | **SHURQ** `create_campaign` / Amazon Ads API |
| `bundle-crosssell-finder` | research/ | Medio | Market Basket → **Helium10** `search_amazon_brand_analytics` (o reporte Brand Analytics directo) |
| `listing-juice-new` | listing/ | **Pesado** | SHURQ (search terms, catálogo) + **Helium10** (SQP, reviews, listing details, competitors) + Category Listings Report (upload) |
| `amazon-title-optimizer` | listing/ | Liviano | SHURQ search terms + **Helium10** SQP + catálogo |
| `client-reply-drafter` | comms-workflow/ | Liviano | Solo contexto: SHURQ + Slack + ClickUp |
| `client-onboarding` | comms-workflow/ | Liviano | SHURQ (`list_my_accounts`, `get_product_detail` para la ficha) + write a Supabase |

**Orden sugerido de cutover:** primero las livianas (`client-onboarding`, `client-reply-drafter`,
`amazon-title-optimizer`) para validar el data layer SHURQ/Helium10 → después las medias
(`daily-restock-supabase`, `launch-sponsored-products`, `bundle-crosssell-finder`, `monthly-report`)
→ al final la pesada (`listing-juice-new`).

## ❌ DESCARTADAS en la revisión (13)
`account-performance-dashboard`, `weekly-exec-summary-hub-v2`, `restock-radar-mcp`,
`inventory-velocity-dashboard`, `stock-alert`, `sp-sb-bulk-bid-optimizer`,
`kw-harvester-negator-sp-sb`, `kw-asin-research-sophie-hub-intent`,
`market-research-mcp-v4`, `product-finder`, `repeat-purchase-lacos`,
`sbv-video-generator`, `amazon-q4-plan`.

## 🔁 AUTO-DESCARTADAS (7 · duplicados/test, no se revisaron)
`july-1-sophiehub-...-dashboard`, `daily-restock`, `restock-radar`,
`kw-harvester-negator`, `market-research-mcp`, `kw-asin-research-sophie-hub-cores`,
`sqp-ctr-cvr-benchmark-q3-challenge`.

> Nota: `kw-harvester-negator` (y su variante `-sp-sb`) quedan afuera. La función
> harvest + negate ya está cubierta por `search-term-harvest` + los skills de negativos
> (SHURQ, sin dependencia de Sophie Hub), que sí están en el staging.

## Gap a decidir
- **Subscribe & Save** (lo usa `monthly-report`): sin fuente en el stack nuevo.
  Recomendación: sacar esa sección al inicio; alimentar manual desde Seller Central solo si un cliente lo pide.
