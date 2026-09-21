---
name: daily-restock-supabase
description: >
  PILOT (Supabase) copy of daily-restock. Restock feeder for the Sophie Master Dashboard.
  For ONE client: reads the config from Supabase (clients table), makes ONE Sophie Hub call
  (get_restock_recommendations), and UPSERTs the snapshot to Supabase (dashboard_snapshots table,
  tipo='restock', one row per day) instead of writing a local JSON. Lightweight 1-call feeder
  (does NOT run the heavy restock-radar-mcp engine). WEEKLY cadence (Wednesday). Single mode: 'run'.
  Trigger ONLY with explicit pilot phrasing: "run daily-restock-supabase for [Brand]",
  "restock supabase para [Brand]", "restock supabase for [Brand]".
---

# Daily Restock — Feeder (Master Dashboard, Fase 3)

**Versión:** V1.0 SUPABASE (2026-08-03). Copia piloto de `daily-restock` V1.0. Corre **en paralelo** al original sin pisarlo. Cambios: (1) config desde Supabase (tabla `clients`), no de archivos locales; (2) el snapshot se **upsertea** a `dashboard_snapshots` (`tipo='restock'`, una fila por día) en vez de escribir un JSON local; (3) fecha anclada a ART. La resolución de store y el pull de Sophie Hub son idénticos. Ver `memory/dashboard_cloud_migration.md`.

> **🧪 ESTO ES EL PILOTO.** Lee/escribe Supabase, no disco. El `daily-restock` original queda intacto.

> **Cadencia: SEMANAL, miércoles.** El nombre `daily-restock` es solo por consistencia con la familia (`daily-check`, `daily-negatives`); NO corre a diario.

## Constants
```
Config cliente:  Supabase, tabla public.clients (columna config JSONB) — via conector Supabase MCP.
Snapshot:        Supabase, tabla public.dashboard_snapshots, tipo='restock', UNA FILA POR DÍA
                 (clave única cliente,tipo,fecha). El compose toma el snapshot más reciente por cliente.
Fuente de datos: Sophie Hub MCP → get_restock_recommendations (1 call). NO usar el motor restock-radar.
Timezone:        America/Argentina/Buenos_Aires (ART) — anclar la fecha a ART, no a date.today().
```

## MODE = run (un cliente)

### Step 1 — Resolver brand → config (Supabase) + store de Sophie Hub
- Resolver `requested_brand` contra la tabla `clients` de Supabase (igual que `daily-check-client-supabase` Step 1b):
  ```sql
  select brand, active, config from public.clients
  where lower(brand)=lower('<requested_brand>')
     or exists (select 1 from jsonb_array_elements_text(coalesce(config->'alternative_names','[]'::jsonb)) a where lower(a)=lower('<requested_brand>'));
  ```
  Zero rows / `config` null → STOP y listá `select brand from public.clients where active`. Tomá `cfg = config`.
- Resolver el **store de Sophie Hub**: `list_stores` y matchear `brand_name` (o `alternative_names` del config) contra el `name` del store → tomar `seller_id`. Ojo con aliases: Poop Juice = "BURI Brands", Chill Rover = "chillrover", Pavida's = "Pavida's wellness". Si no resuelve a 1 store → STOP y listar los stores.
  (Referencia validada 2026-07-09: Natchiketa = `A23BV3INI9U1YI`.)

### Step 2 — Pull (1 call)
```
get_restock_recommendations(store=<seller_id>, compact=true, limit=60)
```
Devuelve por SKU: `asin, sku, available, alert, days_of_supply, sales_30d, recommended_qty, recommended_ship_date`, más `snapshot_date_from/to` y `currency`.

### Step 3 — Shape
- **Dropear listings muertos:** filas con `sales_30d == 0 AND available == 0` (SKUs discontinuados/duplicados).
- **Nombre por print:** mapear cada `asin` a un nombre legible desde `cfg.managed_asins[].asin/.name`. Si el asin no está en el config → `name = "New print"`.
- **risk por item:** `"reorder"` si `recommended_qty > 0` o `alert` no vacío o `days_of_supply < 30`; sino `"watch"` si `days_of_supply < 60`; sino `"ok"`.
- **Ordenar** por `days_of_supply` ascendente (más urgente primero).
- Multi-marketplace (ej. Happy Fox US/CA): 1 snapshot por config; el store de cada marketplace puede diferir — resolver por marketplace.

### Step 4 — Upsert del snapshot a Supabase — schema `restock-snapshot-v1`
Armá el objeto `datos` (schema `restock-snapshot-v1`, IDÉNTICO al del original):
```json
{ "schema":"restock-snapshot-v1","generated_at_iso":"<ISO ART>",
  "meta":{"title_date":"...","short_date":"Jul 9","snapshot_date":"<report snapshot date>","pull_time":"HH:MM ART","data_source":"sophie-hub",
          "note":"Amazon FBA Restock Recommendations. The deep forecast lives in restock-radar."},
  "client":{"brand_name":"...","marketplace":"US","currency_prefix":"$","status":"ok",
    "product_summary":"...","skus_total":N,"reorder_now":N,"lowest_cover":<min dos>,
    "items":[{"asin","name","available","days_of_supply","sales_30d","recommended_qty","recommended_ship_date","alert","risk"}]}}
```
`currency_prefix` = `CA$` si marketplace CA, else `$`. Upsert vía el conector Supabase `execute_sql` (dollar-quote con tag `$rst$`):
```sql
insert into public.dashboard_snapshots (cliente, tipo, fecha, datos)
values ('<brand_name>', 'restock', '<YYYY-MM-DD hoy ART>', $rst$<el objeto datos>$rst$::jsonb)
on conflict (cliente, tipo, fecha)
do update set datos = excluded.datos, actualizado = now();
```
- `cliente` = `cfg["brand_name"]` (= `clients.brand`) · `tipo` = `'restock'` · `fecha` = HOY en ART (anclada a `America/Argentina/Buenos_Aires`, no a `date.today()`) · `datos` = el objeto de arriba.
No deployar acá (lo hace el master compose, no migrado). Confirmá: `Restock (Supabase) written for {brand} — {N} SKUs, {r} to reorder, lowest coverage {c}d.`

## Scheduling (PILOTO — Routines de nube)
- **Semanal, miércoles** (ej. 12:30 ART). Igual patrón que negatives: Routines por **lotes de 5 clientes** (`order by brand limit 5 offset {0,5,10,15}`) para escalar, connectors **Supabase + Sophie Hub**, sin repo, sin carpeta local. El master compose (no migrado todavía) levantará el snapshot de restock más reciente por cliente.

## Edge cases
| Situación | Comportamiento |
|---|---|
| Store no resuelve | STOP, listar stores de `list_stores`. |
| get_restock_recommendations vacío | Snapshot con items:[], reorder_now 0, status "ok". |
| ASIN sin nombre en config | name = "New print". |
| SKU muerto ($0 y 0 stock) | Dropear. |
| Sophie Hub no responde | status:"datafail", items:[]. |
