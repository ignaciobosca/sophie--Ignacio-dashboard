---
name: daily-harvest-supabase
description: >
  PILOT (Supabase) copy of search-term-harvest, a LIGHTWEIGHT snapshot-only version for the
  Sophie Master Dashboard (Harvest tab). For ONE client: analyzes search terms from auto/broad
  campaigns (SHURQ), identifies candidates to graduate to exact/phrase, and UPSERTS the snapshot
  to Supabase (table dashboard_snapshots, tipo='harvest', one row per day). Does NOT generate
  XLSX or a Slack draft (that stays in the original search-term-harvest). Does NOT use the harvest
  history (history dedup omitted; the live Step 5 removes the already-graduated). Reads the config
  from Supabase (table clients). WEEKLY cadence. Trigger ONLY with explicit pilot phrasing:
  "run daily-harvest-supabase for [Brand]", "harvest supabase para [Brand]", "harvest supabase for [Brand]".
---

# Daily Harvest — Feeder liviano (Supabase, Master Dashboard tab Harvest)

**Versión:** V2.0 SUPABASE · SHURQ edition (2026-09-12) — **migrada de AdLabs a SHURQ.** Mismo análisis
endurecido que V1.0 (Steps 2, 3, 5, 6, 7b idénticos en lógica); lo único que cambió es **de dónde salen
los datos** (AdLabs `get_entity_data` → SHURQ `get_ads_summary` + `query_table`) y la **resolución de
cuenta** (`adlabs_team_id`/`adlabs_profile_id` → `shurq_account_id` + `mkp_id`). El motor de filtro de
candidatos (Step 6) y el snapshot (Step 7b) son **agnósticos de la fuente** y quedan idénticos.

**Historial:** V1.0 SUPABASE (2026-08-03) — copia LIVIANA de `search-term-harvest` V4.4, solo-snapshot,
AdLabs primario / Shurq fallback. Corre **en paralelo** al original sin pisarlo.

> **🧪 PILOTO SOLO-SNAPSHOT — LEER PRIMERO.** Este skill hace ÚNICAMENTE el snapshot del dashboard a Supabase. Respecto al original:
> - **Config:** desde Supabase (tabla `clients`), no de archivos locales (ver Step 1 modificado abajo).
> - **SALTEAR COMPLETOS:** Step 4 (harvest history — tratá `previously_harvested = False` para todos), Step 7 (XLSX), Step 8 (escribir history), Step 9 (Slack draft). NO generar XLSX, NO tocar Slack, NO leer/escribir `_harvest_history.json`.
> - **Análisis IDÉNTICO al original:** Steps 2 (CVR de cuenta), 3 (pull search terms auto/broad), 5 (excluir ya-targeted exact/phrase, EN VIVO), 6 (filtro de candidatos).
> - **Step 7b:** en vez de escribir un JSON local, hace **upsert a Supabase** (ver Step 7b modificado abajo). Fecha anclada a ART.

## Cómo se llama a SHURQ (mecánica del conector)

SHURQ expone `search` / `get_schema` / `execute` + tools semánticas directas. Las fuentes de datos son:
- **`get_ads_summary(account_id, marketplace_id, start_date, end_date)`** → resumen de cuenta (CVR).
- **`query_table(table_name=...)`** → consulta scopeada a la cuenta contra tablas allowlisted, con
  filtros server-side y **paginación por `offset`** (`metadata.has_more`).

Sandbox de `execute`: Python real, **sin** `json.loads` (el `result` viene como string JSON — parsealo
con string ops o devolvelo y procesalo afuera), **sin** pandas, **sin** `date.today()`; `call_tool` es async.
No hay `start_chat_session`/`read_resource`/`get_entity_data`/`query`/`read`/`download_data` — eso era AdLabs.

> **⚠️ Tope de las tools semánticas:** `list_search_terms` y `list_keywords` topean en **200 filas y NO
> tienen `offset`** → NO usarlas para el pull completo. Usar **`query_table`** (paginable) para search
> terms y keywords. `get_ads_summary` sí sirve para el resumen (una sola llamada, sin filas).

---

## Global config

```
Config cliente:  Supabase, tabla public.clients (columna config JSONB) — via conector Supabase MCP.
Snapshot:        Supabase, tabla public.dashboard_snapshots, tipo='harvest', UNA FILA POR DÍA (clave cliente,tipo,fecha).
Fuente de datos: SHURQ (conector de nube) — get_ads_summary + query_table. account_id + mkp_id del config.
Timezone:        America/Argentina/Buenos_Aires (ART) — anclar la fecha a ART, no a date.today().
NADA de: XLSX, Slack, harvest history local. (El original conserva todo eso.)
```

### Marketplace → `mkp_id`
US=1 · GB/UK=2 · CA=4 · MX=5 · BR=6 · DE=7 · ES=8 · FR=9 · IT=10 · NL=16 · PL=19 · SE=20 · BE=21 ·
AE=15 · SA=23 · IE=24. Fallback: `list_my_accounts()`.

---

## Step 1: Resolve brand → load config

Resolvé el `requested_brand` contra la tabla `clients` de Supabase (igual que `daily-check-client-supabase` Step 1b):
```sql
select brand, active, config from public.clients
where lower(brand)=lower('<requested_brand>')
   or exists (select 1 from jsonb_array_elements_text(coalesce(config->'alternative_names','[]'::jsonb)) a where lower(a)=lower('<requested_brand>'));
```
Zero rows / `config` null → STOP y listá `select brand from public.clients where active`. Tomá `cfg = config`.

Requeridos para el análisis: `brand_name`, `shurq_account_id`, `amazon_marketplace`. Derivá
`account_id = int(shurq_account_id)` y `mkp_id` del marketplace. Derivados:
```python
acos_target = cfg.get("acos_target") or 0.50   # fallback conservador 50% si falta
harvest_min_clicks = cfg.get("harvest_min_clicks", 10)
```
Multi-marketplace: cada marca CA es su propio `brand` en `clients` (ej. "Happy Fox (CA)") → 1 corrida por brand.

> **Diagnóstico honesto:** si `shurq_account_id` falta/null → STOP ese entry con
> `reason:"config incompleto: falta shurq_account_id"`. Si está presente y una llamada SHURQ falla →
> transitorio, reintentá 1 vez; nunca "cuenta no conectada".

**Ventana de datos (ANCLADA A ART):**
```
today_art  = <hoy en America/Argentina/Buenos_Aires>   # NO date.today() (entorno=UTC)
window_days = 30
start_date = (today_art - 30 días) → 'YYYY-MM-DD'
end_date   = (today_art - 1 día)   → 'YYYY-MM-DD'   (ayer)
```
Respetar ventana custom si Nacho la especifica. Como salteamos Step 4 (history), antes del Step 6 seteá
`term["previously_harvested"] = False` para todos los search terms.

> **⚠️ Cap de 90 días:** `get_ads_summary`/`query_table` aceptan rangos ≤ 90 días. Con `window_days=30`
> no hay problema; si Nacho pide una ventana > 90 días, partila en chunks ≤ 90 y sumá.

---

## Step 2: CVR promedio de la cuenta (SHURQ get_ads_summary)

```python
acc = <account_id>; mkp = <mkp_id>
s = await call_tool("get_ads_summary", {
    "account_id": acc, "marketplace_id": mkp,
    "start_date": start_date, "end_date": end_date})
# s["data"]["overall"] → { clicks, orders, cvr, ... }
overall = s["data"]["overall"]
total_clicks = overall["clicks"]; total_orders = overall["orders"]
account_cvr = (total_orders / total_clicks) if total_clicks else None
if not account_cvr:
    raise ValueError(f"Sin CVR para {cfg['brand_name']}. Stop.")   # datafail si no hay tráfico
data_source_summary = "shurq"
print(f"Account CVR: {account_cvr:.2%} | window: {start_date} → {end_date} | source: shurq")
```
> `overall.cvr` viene ya calculado (en %); usalo solo como sanity-check. La vara del filtro es
> `account_cvr = orders/clicks` (fracción), consistente con el CVR por término del Step 3.

---

## Step 3: Pull search terms (SHURQ query_table, reemplaza AdLabs)

Pull de `searchterms_daily` (una fila por search term × keyword × día) sobre TODA la ventana, paginando.
Traemos SOLO fuentes de **descubrimiento** (auto/broad) — es de ahí que se gradúa a exact/phrase.

```python
rows = []; offset = 0
while True:
    filters = [
      {"column":"report_date","operator":">=","value": start_date},
      {"column":"report_date","operator":"<=","value": end_date},
      {"column":"mkp_id","operator":"=","value": mkp},
      {"column":"clicks","operator":">=","value": 1},
      {"column":"campaign_status","operator":"=","value":"ENABLED"},
    ]
    r = await call_tool("query_table", {
        "account_id": acc, "table_name": "searchterms_daily",
        "columns": "searched_term,campaign_name,campaign_id,clicks,cost,orders,sales,match_type,api_type",
        "filters": <filters como STRING JSON>, "sort_by": "cost", "sort_dir": "DESC",
        "limit": 200, "offset": offset})
    page = r["data"]; rows += page
    if not r["metadata"].get("has_more"): break
    offset += 200
```

- **`filters` va como STRING JSON.** `account_id` se aplica solo. **Paginación obligatoria** con `offset += 200`
  mientras `metadata.has_more == true`. No cortar antes.
- **Fuente auto/broad (regla de harvest):** quedate SOLO con filas cuyo `match_type` sea **`null` (auto/SPA)**
  o **`"BROAD"`** (broad manual). Descartá `EXACT`/`PHRASE` (apariciones ya-graduadas) y `ASIN_*`/PT (no son
  harvest de keyword). Esto reemplaza el `match_type IN ('Auto','Broad')` de AdLabs.
- **Scavenger SE INCLUYE acá (a diferencia de daily-negatives):** las Scavenger son descubrimiento
  intencional — un término que **convierte** en Scavenger ES candidato a graduar (ese es el punto de la
  Scavenger). NO excluir Scavenger en este Step. (Sí se excluye en el Step 5, ver ahí.)

**Dedup por término** (sobre las filas auto/broad): agrupá por `searched_term`, sumando
`clicks`/`cost`/`sales`/`orders` cross-campaña/keyword. Conservá por término la **campaña de ORIGEN**
(la de mayor `cost`) en `campaign_name`, y derivá `match_type` (src) de esa campaña de origen:
```python
def _src(mt, campaign_name):
    m = (mt or "").lower()
    cn = (campaign_name or "").lower()
    if m == "broad": return "broad"
    if "spa" in cn or m in ("", "none"): return "auto"   # SPA/auto → match_type null
    return "auto"
```
Estructura esperada por search term (post-dedup):
```python
term = {"search_term":"...","campaign_name":"...","match_type":"auto|broad",
        "impressions":0,"clicks":0,"spend":0.0,"sales":0.0,"orders":0}
term["acos"] = term["spend"]/term["sales"] if term["sales"]>0 else None
term["cvr"]  = term["orders"]/term["clicks"] if term["clicks"]>0 else None
term["cpc"]  = term["spend"]/term["clicks"] if term["clicks"]>0 else None
```
> `searchterms_daily` no trae `impressions` en el set de columnas pedido arriba (para achicar el payload);
> si el snapshot necesita impressions, agregá `impressions` a `columns`. Por defecto `impressions=0`.

> **Sin data:** si el pull devuelve 0 filas (o error tras 1 reintento) → snapshot con `status:"datafail"`
> (si fue error) o `status:"ok"` + `candidates:[]` (si no hubo tráfico auto/broad). Nunca inventes términos.

---

## Step 4: Cargar harvest history (dedup cross-runs)

> **⛔ PILOTO — SALTEAR.** No se usa harvest history en este feeder (dedup por history omitido; el Step 5 en
> vivo saca los ya-graduados). Tratá `term["previously_harvested"] = False` para todos. NO leer ni escribir
> `_harvest_history.json`, NO tocar Drive.

---

## Step 5: Excluir keywords ya existentes como Exact/Phrase (SHURQ query_table)

Traé el **catálogo de keywords enabled** de `keywords_daily` para armar el set de "ya-graduados".
Usar `query_table` (paginable) — NO `list_keywords` (topea en 200 sin offset).

```python
kw_rows = []; offset = 0
while True:
    kf = [
      {"column":"report_date","operator":">=","value": start_date},
      {"column":"report_date","operator":"<=","value": end_date},
      {"column":"mkp_id","operator":"=","value": mkp},
      {"column":"campaign_status","operator":"=","value":"ENABLED"},
    ]
    r = await call_tool("query_table", {
        "account_id": acc, "table_name": "keywords_daily",
        "columns": "keyword_text,match_type,campaign_name,campaign_status",
        "filters": <kf como STRING JSON>, "limit": 200, "offset": offset})
    kw_rows += r["data"]
    if not r["metadata"].get("has_more"): break
    offset += 200

# ⛔ EXCLUIR CAMPAÑAS SCAVENGER del set de "ya-targeted": las Scavenger targetean TODAS las palabras
# con los 3 match types, así que sus keywords exact/phrase NO cuentan como "ya graduado" — si contaran,
# se excluiría casi todo el pool de harvest.
existing_set = { r["keyword_text"].lower()
                 for r in kw_rows
                 if r.get("keyword_text")
                 and r.get("match_type") in ("EXACT","PHRASE")
                 and "scavenger" not in str(r.get("campaign_name") or "").lower() }

for term in search_terms:
    term["already_targeted"] = term["search_term"].lower() in existing_set
```
> Traemos el catálogo sobre TODA la ventana (report_date entre start y end) y deduplicamos por
> `keyword_text` — así capturamos cualquier keyword enabled que tuvo tráfico en los últimos 30 días.
> Una keyword enabled con CERO impresiones en 30 días es rara y de bajo riesgo (probablemente inefectiva).

---

## Step 6: Filtrar candidatos (IDÉNTICO al original — agnóstico de la fuente)

```python
THRESHOLDS = {
    "min_clicks":          harvest_min_clicks,   # default 10
    "min_orders":          1,
    "max_acos":            acos_target,
    "min_cvr_ratio":       1.0,                  # CVR >= account_cvr
    "strong_acos_override": 0.6,                 # ACOS < target × 0.6 → bypasea CVR
}

harvest_candidates = []; excluded = []
for term in search_terms:
    if term["previously_harvested"]:
        excluded.append({**term, "exclusion_reason": f"Previously Harvested ({term['previously_harvested']})"}); continue
    if term["already_targeted"]:
        excluded.append({**term, "exclusion_reason": "Already targeted as Exact/Phrase"}); continue
    reason = None
    if term["clicks"] < THRESHOLDS["min_clicks"]:
        reason = f"Clicks insuficientes ({term['clicks']} < {THRESHOLDS['min_clicks']})"
    elif term["orders"] < THRESHOLDS["min_orders"]:
        reason = "Sin conversiones"
    elif term["acos"] is None or term["acos"] > THRESHOLDS["max_acos"]:
        acos_str = f"{term['acos']:.0%}" if term["acos"] else "N/A"
        reason = f"ACOS fuera de target ({acos_str} > {THRESHOLDS['max_acos']:.0%})"
    else:
        cvr_ok = term["cvr"] is not None and term["cvr"] >= account_cvr * THRESHOLDS["min_cvr_ratio"]
        strong_acos = term["acos"] is not None and term["acos"] < acos_target * THRESHOLDS["strong_acos_override"]
        if cvr_ok or strong_acos:
            harvest_candidates.append(term); continue
        cvr_str = f"{term['cvr']:.2%}" if term["cvr"] else "N/A"
        reason = f"CVR por debajo del promedio ({cvr_str} < {account_cvr:.2%})"
    excluded.append({**term, "exclusion_reason": reason})

harvest_candidates.sort(key=lambda t: (-t["sales"], -(t["cvr"] or 0)))
excluded.sort(key=lambda t: -t["clicks"])

def proposed_action(search_term):
    return "Add as Phrase" if len(search_term.strip().split()) <= 2 else "Add as Exact"
for t in harvest_candidates:
    t["action"] = proposed_action(t["search_term"])
```

---

## Step 7: Build XLSX (un solo archivo, 4 hojas)

> **⛔ PILOTO — SALTEAR ESTE STEP COMPLETO.** Este feeder es solo-snapshot: NO genera XLSX. Andá directo al Step 7b.

---

## Step 7b: Snapshot para el Master Dashboard (tab Harvest)

Escribir un snapshot que alimenta la tab **Harvest** del Master Dashboard (Pod Nacho). Reusa
`harvest_candidates` ya calculados (que YA excluyen ya-targeteados-exact/phrase). Cero pulls extra.

```python
def _mtsrc(mt):   # src del snapshot desde el match_type derivado en Step 3
    m=(mt or "").lower()
    return "auto" if "auto" in m else ("broad" if "broad" in m else (m or "manual"))

snap_cands = [{
    "term": t["search_term"], "orders": t["orders"], "clicks": t["clicks"],
    "spend": round(t["spend"],2), "sales": round(t["sales"],2),
    "acos": round(t["acos"]*100) if t["acos"] is not None else None,
    "cvr":  round(t["cvr"]*100)  if t["cvr"]  is not None else None,
    "src": _mtsrc(t.get("match_type")),
    "match": "phrase" if t["action"]=="Add as Phrase" else "exact",
} for t in harvest_candidates]

snapshot = {
  "schema":"weekly-harvest-snapshot-v1","generated_at_iso":"<ISO ART>",
  "meta":{"title_date":"<hoy ART, ej. Friday, September 12, 2026>","short_date":"<Sep 12>",
          "window_label":f"Last {window_days} days - {start_date} to {end_date}","pull_time":"HH:MM ART","data_source":"shurq"},
  "client":{"brand_name":cfg["brand_name"],"marketplace":cfg.get("amazon_marketplace","US"),
            "currency_prefix":"CA$" if cfg.get("amazon_marketplace")=="CA" else "$","status":"ok",
            "product_summary":<product desc del cfg, sino product_category>,
            "window_days":window_days,"acos_target":acos_target,
            "pool_total":len([t for t in search_terms if t.get("orders",0)>0]),
            "candidates_sales":round(sum(t["sales"] for t in harvest_candidates),2),
            "candidates":snap_cands}
}
```
`product_summary` sale de `cfg.notes.client_overview.product_description` o `cfg.product_portfolio.structure`;
si no hay, `cfg.product_category`.

**Upsert a Supabase** (dollar-quote con tag `$hrv$`, que no aparece en el contenido):
```sql
insert into public.dashboard_snapshots (cliente, tipo, fecha, datos)
values ('<cfg["brand_name"]>', 'harvest', '<today_art YYYY-MM-DD>', $hrv$<el objeto snapshot como JSON>$hrv$::jsonb)
on conflict (cliente, tipo, fecha) do update set datos = excluded.datos, actualizado = now();
```
- `cliente` = `cfg["brand_name"]` (= `clients.brand`) · `tipo` = `'harvest'` · `fecha` = `today_art` (ART) · `datos` = el objeto `snapshot`.
Confirmá: `Harvest (Supabase) upsert for {cfg['brand_name']}: {len(snap_cands)} candidates.`

> **⛔ ESTE FEEDER TERMINA ACÁ. SALTEAR Steps 7 (XLSX), 8 (history) y 9 (Slack) por completo.** El master
> compose (no migrado) levantará el snapshot de harvest más reciente por cliente.

## Step 8: Update harvest history — ⛔ PILOTO — SALTEAR
## Step 9: Slack draft — ⛔ PILOTO — SALTEAR

---

## Scheduling (PILOTO — Routines de nube)
- **Feeder (modo run):** una Routine por batch de clientes activos, cadencia **semanal**. Connectors
  **Supabase + SHURQ** (ya no AdLabs), continue-on-error, sin repo.
- **Compose:** no migrado.
- Multi-marketplace = cubierto (cada marca CA es su propio `brand`).

## Edge cases
| Situación | Comportamiento |
|---|---|
| Brand not in clients / config null | STOP + listar activos. No fabricar. |
| Config sin `shurq_account_id` | STOP ese entry: `reason:"config incompleto: falta shurq_account_id"`. |
| `get_ads_summary` sin tráfico (CVR null) | Stop ese entry (`status:"datafail"`), log, seguir con otros. |
| `query_table` error tras 1 reintento | `status:"datafail"`, `candidates:[]`. |
| `query_table` 0 filas | Pool 0 → snapshot `candidates:[]` + status ok. |
| Paginación (`has_more`) | Seguir con `offset += 200` hasta traer todo (search terms Y keywords). |
| Filas EXACT/PHRASE/ASIN en searchterms_daily | Descartar en Step 3 (solo auto/broad se gradúa). |
| Scavenger en searchterms_daily (Step 3) | INCLUIR (descubrimiento intencional → candidato si convierte). |
| Scavenger en keywords_daily (Step 5) | EXCLUIR del set "ya-targeted" (no bloquea el harvest). |
| `acos_target` null | Default 0.50, avisar a Nacho. |
| 0 candidatos | Snapshot igual (`candidates:[]`, status ok). |
| Multi-marketplace | 1 harvest por config (cada marca CA es su propio `brand`). |
| Ventana custom de Nacho > 90 días | Partir en chunks ≤ 90 días y sumar. |

---

## Migración AdLabs → SHURQ (referencia rápida)
| AdLabs (V1.0) | SHURQ (V2.0) |
|---|---|
| `adlabs_team_id` + `adlabs_profile_id` | `shurq_account_id` (int) + `mkp_id` |
| Step 2: `get_entity_data(profile)` → `query` → `read` (total_clicks/orders) | `get_ads_summary(account_id, marketplace_id, start, end)` → `overall.clicks/orders` |
| Step 3: `get_entity_data(search_term)` filtrado `orders>0` + `match_type IN (Auto,Broad)` | `query_table("searchterms_daily")` + paginación offset; filtrar fuente auto/broad (`match_type` null/BROAD) + dedup en Python |
| Step 5: `get_entity_data(target)` `target_type IN (KEYWORD_EXACT, KEYWORD_PHRASE)` state Enabled | `query_table("keywords_daily")` `match_type IN (EXACT,PHRASE)` `campaign_status=ENABLED` + paginación offset |
| exclusión Scavenger del set ya-targeted | idéntico: excluir filas `"scavenger" in campaign_name.lower()` del `existing_set` |
| `start_chat_session`/`read_resource`/`query`/`read` | no existen en SHURQ — `get_ads_summary` + `query_table` |
| Shurq fallback (`get_ads_summary`, `search_term_harvesting`, `list_keywords`) | SHURQ es primario; sin fallback AdLabs |
