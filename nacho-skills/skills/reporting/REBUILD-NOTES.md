# Reporting 🔧 — mapa de rebuild (cutover Sophie Hub)

Estas 3 skills dependen de **Sophie Hub** (que no vas a tener). Abajo, las tools
reales que llama cada una (extraídas por grep) y su reemplazo en tu stack nuevo:
**SHURQ (cuenta única) + Helium10 + Keepa/DataDive + Amazon reports**.

## Mapa Sophie Hub → stack nuevo

| Sophie Hub | Reemplazo | Notas |
|---|---|---|
| `get_sales_traffic` / `query_sales_traffic` | **SHURQ** `get_sales_traffic` | directo |
| `get_orders_summary` | **SHURQ** `get_orders_summary` | directo |
| `get_ads_summary` / `query_ppc` / `get_ads_daily_trend` | **SHURQ** `get_ads_summary` + `query_table` + `list_campaigns/keywords/search_terms` | directo |
| `get_account_performance_summary` | **SHURQ** (componer `get_ads_summary` + `get_orders_summary`) | no hay 1:1; se arma |
| `list_top_products` | **SHURQ** `list_top_products` | directo |
| `get_product` / `get_product_catalog_bulk` / `get_product_performance_summary` | **SHURQ** `get_product_detail` / `search_products` · **Helium10** `get_listing_details` | |
| `get_organic_rank` | **SHURQ** `get_organic_rank` | directo |
| `list_negative_targets` | **SHURQ** `list_keywords` (filtrar negativos) / `query_table` | |
| `get_financial_summary` (P&L, fees) | **SHURQ** `get_pnl_summary` · **Helium10** `get_product_profit_and_loss_*` | SHURQ da P&L; Helium10 para fees/COGS detallado |
| `get_sqp_metrics` | **Helium10** `get_search_query_performance` / `search_amazon_brand_analytics` | SHURQ no tiene SQP |
| `get_inventory_availability` / `get_restock_recommendations` | **Helium10** `get_fba_inventory_health_status` / `get_inventory_values` / `get_sales_velocity` | |
| `get_competitors` | **Helium10** `search_competitors_by_asin` | |
| `sophie_call_keepa_adapter` | **Keepa** MCP directo | precio/BSR history |
| `sophie_call_datadive_adapter` | **DataDive** MCP directo | niches / rank radar |
| `get_amazon_report_full` / `query_report` / `discover_amazon_reports` | **Amazon Ads/SP-API** reports directo, o **SHURQ** `query_table` | |
| `get_subscribe_save` | ⚠️ **GAP** | ni SHURQ ni Helium10 lo dan. Reporte S&S de Seller Central (manual) o quitar esa sección |

## Por skill

### `monthly-report`
- Fuentes: sales/traffic, P&L, SQP, subscribe&save, inventory, competitors, negativos, Keepa/DataDive.
- Rebuild: la mayoría → SHURQ; **SQP → Helium10**; **S&S → gap** (sacar o alimentar manual);
  inventory → Helium10; Keepa/DataDive → MCPs directos.
- Branding: usa template Sophie (PPTX) → parametrizar con `brand_kit` (Fase 5).

### `account-performance-dashboard`
- El más pesado en Sophie Hub: `get_financial_summary` (46), `get_orders_summary` (32),
  `query_sales_traffic` (27), `get_subscribe_save` (22), `get_ads_summary` (22).
- Rebuild: ads/orders/traffic → SHURQ; **Profitability (P&L + fees) → SHURQ `get_pnl_summary`
  + Helium10 P&L**; **tab Subscribe&Save → gap** (esconder si no hay fuente).
- Arranca de `assets/dashboard-template.html` (data-as-props) → solo cambiar el data layer.

### `weekly-exec-summary-hub-v2`
- Fuentes: top products, sales/traffic, restock, account summary, search terms, ppc.
- Rebuild: todo → SHURQ salvo **restock → Helium10**.
- La más fácil de las 3 (menos superficie).

## Prioridad sugerida
1. `weekly-exec-summary-hub-v2` (menos deps) — prueba de que el data layer SHURQ funciona.
2. `account-performance-dashboard` (template ya listo, solo data).
3. `monthly-report` (más superficie + PPTX branding).

> Gap a decidir: **Subscribe & Save**. Sin fuente en el stack nuevo. Opciones:
> (a) alimentar manual desde el reporte de Seller Central, (b) quitar esa sección,
> (c) sumar un conector que lo tenga. Recomiendo (b) al inicio y (a) si un cliente lo pide.
