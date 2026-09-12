---
name: daily-negatives-supabase
description: >
  Copia Supabase de daily-negatives. Para UN cliente: extrae search terms de AYER (t-1) con
  clicks y CERO ventas, deja SOLO los IRRELEVANTES (juicio de relevancia contra la ficha de
  producto del perfil v2) y a cada uno le asigna CONFIANZA (high/medium/low) + evidencia; hace
  upsert de la fila del día a dashboard_snapshots. Modos: 'run' (default) y 'learn' (actualiza
  el perfil en relevance_profiles). Trigger: "negativos supabase para [Brand]",
  "run daily-negatives-supabase for [Brand]", "learn supabase para [Brand]".
---

# Daily Negatives — Per-Client (Master Dashboard, Fase 1)

**Versión:** V3.0 SUPABASE · SHURQ edition (2026-09-12) — **migrada de AdLabs a SHURQ.** Mismo motor de
juicio endurecido + confidence/evidence/basis + gate que V2.0; lo único que cambió es **de dónde salen
los search terms** (AdLabs `get_entity_data(search_term)` → SHURQ `query_table(searchterms_daily)`) y la
**resolución de cuenta** (`adlabs_team_id`/`adlabs_profile_id` → `shurq_account_id` + `mkp_id`). El resto
(Step 4 juicio, rúbrica de confianza, Step 4b, Step 5 snapshot, MODE=learn) es **agnóstico de la fuente**
y queda idéntico.

**Historial:** V2.0 SUPABASE (2026-09-06) — endurecimiento de confianza: fuente del motor de juicio,
`confidence`+`evidence`+`basis`, la vara = `product_fiche` del perfil v2, snapshot `daily-negatives-snapshot-v4`.
V1.0 SUPABASE (2026-08-02) — copia piloto de `daily-negatives` V1.2 a Supabase.

> **🧪 ESTO ES EL PILOTO (feeder del autopush).** Lee/escribe Supabase, no disco. Escribe el snapshot que
> consume `daily-negatives-autopush`. El `daily-negatives` original (AdLabs, local) queda intacto.

**El motor de juicio endurecido vive acá** (Step 4). `negative-targeting` está suspendido; no se remite más a él.
Ventana diaria, **nada de términos relevantes en el output** (Nacho: "los que tienen relación directa con mi
producto no deberían aparecer"), destino = dashboard. Cada Irrelevante lleva confidence/evidence/basis para el gate.

## Cómo se llama a SHURQ (mecánica del conector)

SHURQ expone `search` / `get_schema` / `execute`. La fuente de search terms es **`query_table`** (consulta
scopeada a la cuenta contra tablas allowlisted). Se invoca desde `execute` con `await call_tool(...)`.
Sandbox: Python real, **sin** `json.loads` (el `result` viene como string JSON — parsealo con string ops o
devolvelo y procesalo afuera), **sin** pandas, **sin** `date.today()`; `call_tool` es async.

No hay `start_chat_session`/`read_resource`/`get_entity_data`/`group_by_column`/`download_data` — eso era AdLabs.

## Constants

```
Fuente de datos: Supabase (conector Supabase MCP, proyecto POD 66 - Organization)
  Config cliente: tabla public.clients (columna config JSONB) — brand_name, shurq_account_id, amazon_marketplace, managed_asins, etc.
  Perfil relevancia: tabla public.relevance_profiles (columna profile JSONB), schema relevance-profile-v2:
      { brand_name, config_stem, schema:"relevance-profile-v2",
        product_fiche:{items:[{asin,name,line,status,attributes_present{...7 dims...},
          attributes_absent:[{attr,evidence}],source_listing,...}]}  <- LA VARA,
        roots:[{root,match,reason,confidence,evidence,basis,...}],
        competitors:[{name,reason,confidence,evidence,basis,monitor_only,...}],
        protected_relevant:[{term, reason, scope}]  <- scope: equals|contains; excepciones
          que NUNCA se negativizan; última palabra sobre roots/competitors Y el juicio;
        updated, updated_by, change_log:[...] }
      RETROCOMPAT v1 (roots/competitors strings, sin product_fiche, protected sin scope) → reglas de retrocompat v2.
  Snapshots negatives: tabla public.dashboard_snapshots, tipo='negatives', UNA FILA POR DÍA (cliente,tipo,fecha).
Timezone: America/Argentina/Buenos_Aires (ART)
FUENTE DE SEARCH TERMS: SHURQ query_table(table_name="searchterms_daily"). account_id + mkp_id del config.
Slack/XLSX/deploy: NADA en modo run. El compose (master 4 tabs) no está en este skill.
```

### Marketplace → `mkp_id`
US=1 · GB/UK=2 · CA=4 · MX=5 · BR=6 · DE=7 · ES=8 · FR=9 · IT=10 · NL=16 · PL=19 · SE=20 · BE=21 ·
AE=15 · SA=23 · IE=24. Fallback: `list_my_accounts()`.

---

## MODE = run (default — un cliente)

### Step 1 — Resolver + cargar config (desde Supabase)
```sql
select brand, active, config from public.clients
where lower(brand)=lower('<requested_brand>')
   or exists (select 1 from jsonb_array_elements_text(coalesce(config->'alternative_names','[]'::jsonb)) a where lower(a)=lower('<requested_brand>'));
```
Zero rows / `config` null → STOP y listá `select brand from public.clients where active`. Tomá `cfg = config`.
Requeridos: `brand_name`, `shurq_account_id`, `amazon_marketplace`. Derivá `account_id = int(shurq_account_id)`
y `mkp_id` del marketplace. Multi-marketplace = 1 corrida por config (el `brand` ya distingue US/CA).

> **Diagnóstico honesto:** si `shurq_account_id` falta/null → `reason:"config incompleto: falta shurq_account_id"`,
> saltá. Si está presente y una llamada SHURQ falla → transitorio, reintentá 1 vez; nunca "cuenta no conectada".

Construir `product_context` (marca, category, description desde `notes.client_overview.product_description` o
`product_portfolio.structure`, lista de ASINs con `name`) — idéntico a V2.0.

### Step 2 — Ventana = AYER (t-1) — ANCLADA A ART
```
today_art = <hoy en America/Argentina/Buenos_Aires>
y         = today_art - 1 día   (ventana = ayer, ART) → 'YYYY-MM-DD'
```
> **⚠️ Anclar SIEMPRE a ART, no a `date.today()`** (las Routines corren en UTC). La `fecha` de la fila del
> snapshot (Step 5) = `today_art` (el día del run en ART); la ventana de DATOS es `y` (ayer).

### Step 3 — Pull search terms de ayer (SHURQ `query_table`, reemplaza AdLabs)

Pull de `ads.searchterms_daily` (una fila por search term × keyword × día) con filtros server-side, paginando:

```python
acc = <account_id>; mkp = <mkp_id>
import json  # NO disponible en el sandbox → usá el bloque afuera, o parseo por string; abajo va la forma lógica
rows = []; offset = 0
while True:
    filters = [
      {"column":"report_date","operator":"=","value": y},
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

- **`filters` va como STRING JSON** (el param es string). El `account_id` se aplica solo.
- **Paginación obligatoria:** `limit` máx 200; seguí con `offset += 200` mientras `metadata.has_more == true`.
  No cortes antes (perderías waste de menor spend).
- **NO filtres `orders=0` server-side.** Un mismo término puede tener 0 órdenes en una campaña y convertir en
  otra; el "cero ventas" es a nivel **término agregado** (ver dedup). Traé todos los `clicks>=1` y filtrá
  `orders/sales == 0` DESPUÉS de agregar.

**⛔ Excluir campañas Scavenger (regla de Nacho — OBLIGATORIO, PRECISO por fila):** ANTES de deduplicar,
descartá toda **fila** cuyo `campaign_name` contenga `scavenger` (case-insensitive: `"scavenger" in
campaign_name.lower()`). Como `searchterms_daily` es una fila por término×keyword×campaña, esto es exacto: un
término que quemó clicks en Scavenger **y** en no-Scavenger conserva SOLO los clicks/spend de las filas
no-Scavenger; uno que SOLO venía de Scavenger desaparece. (Validado: en Natchiketa ~28% de las filas del pull
son Scavenger.) Motivo: las Scavenger son de descubrimiento intencional — su waste zero-sale NO se negativiza.

**Dedup por término** (sobre las filas ya sin-Scavenger): agrupá por `searched_term`, sumando
`clicks`/`cost`/`orders`/`sales` cross-campaña/keyword. **Conservá por término la campaña de ORIGEN** (la de
mayor `cost`, o unilas con `; `) en `origin_campaign` — se usa en Step 4b para asignar producto/línea, y se
persiste en el snapshot. (No hay `ad_group_name` ni ASIN anunciado en la tabla; el `campaign_name` de Sophie
codifica el ASIN/línea, ej. `SO | Solid Soap | B0HCNN4F9Y | …` → `origin_ad_group` = `origin_campaign` si no hay
otra señal.) Guardá `pool_total`/`pool_clicks`/`pool_spend` sobre el pool YA filtrado.

**Zero-sale (equivalente al ORDERS=0 de AdLabs):** quedate SOLO con los términos cuyo **total agregado**
`orders == 0` **y** `sales == 0`. Esos son el pool de candidatos que entra al juicio del Step 4.

> **Sin data:** si `query_table` devuelve 0 filas (o error tras 1 reintento) → snapshot con `status:"datafail"`
> (si fue error) o `status:"ok"` + `candidates:[]` (si ayer no hubo tráfico). Nunca inventes términos.

### Step 4 — Juicio de relevancia (PASO DEL MODELO) — solo IRRELEVANTES, con confianza
**(idéntico a V2.0 — agnóstico de la fuente).** Cargar el perfil desde Supabase
(`select profile from public.relevance_profiles where brand = '<brand_name>'`). Leerlo **v1 o v2** (retrocompat).
Evaluar EN ESTE ORDEN:

1. **Excepciones protegidas (PRIMERO — última palabra):** chequear `protected_relevant` (`{term, reason, scope}`)
   ANTES que nada. Match → **Relevante directo**, NO va al snapshot, gana sobre roots/competitors y sobre el
   juicio. `scope`: `contains` = contención/wildcard; `equals` = solo igualdad case-insensitive. Retrocompat sin
   `scope`: "SOLO igualdad"/"equality only" → equals; "todo lo que incluya"/"contención" → contains; sin marcador
   → una palabra → contains, multi-palabra → equals.
2. **Perfil que aprende → `basis:"profile"`, `confidence:"high"`:** `roots`/`competitors` ya confirmados →
   **Irrelevante directo confianza ALTA** (salvo que hayan quedado protegidos en el paso 1, y salvo
   `competitors` con `monitor_only:true` → Relevante). `evidence` = `"root del perfil: <root>"` / `"competitor del perfil: <name>"`.
3. **La VARA = `product_fiche` del perfil.** Usar `attributes_present` (7 dims) + `attributes_absent` como la
   ficha real. Sin `product_fiche` (v1 sin migrar, o ASIN `no_fiche`) → ficha inferida de `product_context` y
   **el juicio de ese producto nunca llega a `high` por attribute-mismatch**.
4. **Juzgar cada término** (`basis:"model"`, en tandas): Relevante SOLO si producto base + TODOS los
   calificadores matchean. Salida binaria. Motivos de irrelevancia: `competitor brand`, `licensed character`,
   `off-category`, `DIY / craft intent`, `attribute mismatch`. **Marca propia → Relevante (nunca negar).**
   A cada Irrelevante `confidence` + `evidence` según la rúbrica.
5. **Reglas determinísticas → `basis:"rule"`, `confidence:"high"`:** marca propia (Relevante), ASIN (Step 4b),
   char no-negable, etc.
6. **Solo los Irrelevante pasan al snapshot.** Los Relevante NO aparecen. Cada Irrelevante lleva
   `confidence`, `evidence`, `basis`.

#### Rúbrica de confianza (OBLIGATORIA — gobierna el gate del autopush)
Regla de oro: **si la irrelevancia no se puede fundamentar con evidencia concreta, NO es `high`.**
- **`high`** — verificable sin criterio opinable: matchea `root`/`competitor` del perfil (`basis=profile`); o
  marca ajena reconocida con certeza; o off-category inequívoco (`furniture`, `diapers`); o attribute mismatch
  donde el atributo pedido está en `attributes_absent` (ausencia EXPLÍCITA). `evidence` = el hecho.
- **`medium`** — probable pero por inferencia: "parece" marca ajena no reconocida; equivalencia de dominio
  (declararla); attribute mismatch donde el atributo NO está ni en present ni en absent; ficha `no_fiche`/sin
  `product_fiche` (juicio sin vara → nunca high).
- **`low`** — señal débil / ambiguo: el modelo se inclina a Irrelevante pero con dudas.

**Gate (lo aplica `daily-negatives-autopush`):** `high`+`medium` se autopushean; `low` va a tu review. **PROHIBIDO**
inflar a `high` sin el hecho. Ante duda high/medium → bajar a `medium`.

**Match type (default; Nacho ajusta en el dashboard con el toggle):**
- `root` = raíz a negar como PHRASE cuando es una familia limpia que el cliente nunca va a querer:
  marca/competidor, personaje licenciado, material/feature ajeno (`bamboo`, `weighted`, `upf`), intent DIY
  (`fabric`, `pattern`, `crochet`), categoría ajena clara (`furniture`, `diapers`). → `match:"phrase"`, `root:"<raíz>"`.
- `exact` = junk de título de ASIN ajeno, mismatch de atributo puntual, o size mismatch (twin/queen). →
  `match:"exact"`, `root:""`.

### Step 4b — Tipo (asin/keyword) y Producto (línea/parent) — por candidato Irrelevante
- **kind:** `asin` si el término matchea `^b0[a-z0-9]{8}$`, else `keyword`.
- **⚠️ Términos tipo-ASIN — INCLUIRLOS SIEMPRE (regla de Nacho):** no pasan por el motor semántico. Determinístico:
  1. Si el ASIN ∈ `cfg.managed_asins` del propio cliente → self-targeting → descartar.
  2. Cualquier OTRO ASIN con clicks≥1 y 0 ventas → **incluir** `kind:"asin"`, `match:"exact"`, `root:""`,
     `reason:"ASIN target ajeno zero-sale — revisar en dashboard"`, `product` = línea del ASIN anunciado o "General (sin asignar)".
- **product (línea/parent, AUTO — editable en el dashboard):** asignar la **LÍNEA a nivel PARENT** del producto
  anunciado en la campaña de origen (`origin_campaign`, conservada en Step 3). Mapear por: (a) ASIN parseado del
  `campaign_name` → su parent vía `managed_asins`, o (b) el nombre de campaña (suele codificar la línea). Sin
  determinar → `"General (sin asignar)"`.
- **`client.products`:** derivar de `managed_asins` colapsando children a su parent. Incluir siempre
  `{"asin":"","name":"General (sin asignar)"}` al final.

### Step 5 — Upsert de la fila del día a Supabase (row-per-day)
**(idéntico a V2.0.)** Armá `datos` schema `daily-negatives-snapshot-v4` con UN solo `day` (el de este run).
Marcá `meta.data_source:"shurq"`.
```json
{ "schema":"daily-negatives-snapshot-v4","generated_at_iso":"<ISO ART>",
  "meta":{"title_date":"...","short_date":"Sep 1","window_label":"Ayer · <Mon D>","pull_time":"HH:MM ART","data_source":"shurq"},
  "client":{"brand_name":"...","marketplace":"US","currency_prefix":"$","status":"ok|datafail",
    "product_summary":"...","window_days":7,
    "products":[{"asin":"<parent>","name":"..."}, ... ,{"asin":"","name":"General (sin asignar)"}]},
  "day":{ "date_iso":"<ayer>","date_label":"Sep 1","window_label":"Ayer · Sep 1",
    "pool_total":N,"pool_clicks":N,"pool_spend":F,"candidates_spend":F,
    "candidates":[{"term":"...","clicks":N,"spend":F,"match":"phrase|exact","root":"...","reason":"...",
      "confidence":"high|medium|low","evidence":"<hecho verificable>","basis":"profile|model|rule",
      "kind":"keyword|asin","product":"<linea/parent>","origin_campaign":"...","origin_ad_group":"..."}]} }
```
`candidates` = irrelevantes de hoy (0 → `candidates:[]`). `currency_prefix` = `CA$` si marketplace CA, else `$`.
`kind:"asin"` → `confidence:"high"`, `basis:"rule"`, `evidence:"ASIN target ajeno zero-sale"`.

Upsert (dollar-quote con tag `$neg$`):
```sql
insert into public.dashboard_snapshots (cliente, tipo, fecha, datos)
values ('<brand_name>', 'negatives', '<today_art YYYY-MM-DD>', $neg$<datos>$neg$::jsonb)
on conflict (cliente, tipo, fecha) do update set datos = excluded.datos, actualizado = now();
```
- `cliente` = `cfg["brand_name"]` (== `clients.brand`). `fecha` = **HOY (día del run, ART)**. La ventana de DATOS es ayer.

Confirmá: `Fila negatives (Supabase) escrita para {brand} — {fecha}: {n} candidatos ({kw} kw / {as} asin) — confianza: {high} high / {medium} medium / {low} low.`

---

## MODE = compose — NO MIGRADO EN ESTE SKILL
Igual que V2.0: el master composer se migra al final de Fase B. Si disparan compose → STOP y avisá que use el
`daily-negatives` original (local) para el master dashboard actual.

---

## MODE = learn (aprendizaje — actualiza el perfil de relevancia EN SUPABASE)
**(idéntico a V2.0 — agnóstico de la fuente.)** Trigger: "learn supabase para [Brand]" + (a) el bloque pegado del
dashboard (`term\tmatch\treason[\tproduct]`) y/o (b) notas en lenguaje natural.

1. Resolver brand contra `clients` (mismo query que Step 1). `brand` = `clients.brand`.
2. Cargar `select profile from public.relevance_profiles where brand = '<brand>'`. Si no existe → nuevo v2. Si es
   v1 → migrar a v2 primero (no tocar `product_fiche`).
3. **Del bloque:** `match=phrase` → `roots += {root, match:"phrase", reason, confidence:"high",
   evidence:"confirmado por Nacho en review <fecha>", basis:"profile", added_by:"learn", added_on:<hoy>, confirmations:1}`
   (si existe, subir `confirmations`). `reason` con `competitor`/`licensed` → `competitors += {name, reason,
   confidence:"high", evidence:"confirmado por Nacho", basis:"profile", added_by:"learn", added_on:<hoy>,
   confirmations:1, monitor_only:false}`. Dedup por root/name (case-insensitive), merge.
4. **De notas NL** → `protected_relevant += {term, reason, scope:"equals|contains"}`. Scope explícito: raíz de
   marca/atributo propio o "todo lo que incluya X" → contains; descriptor de categoría → equals; ante duda → equals.
   ("competidor a monitorear, no negar" → `competitor` con `monitor_only:true`.)
5. **⚠️ Chequeo de conflicto OBLIGATORIO:** por cada `term` de `protected_relevant`, si coincide con un
   `root`/`competitor` según su `scope` → removerlo (gana la excepción) y loguear en `change_log`.
6. Actualizá `updated`/`updated_by`, appendeá al `change_log`, y upserteá (tag `$prof$`):
```sql
insert into public.relevance_profiles (brand, profile)
values ('<brand>', $prof$<profile JSON>$prof$::jsonb)
on conflict (brand) do update set profile = excluded.profile, updated = now();
```
Confirmá `Perfil (Supabase) de {brand}: +{k} roots, +{m} competidores, +{p} protegidos ({c} conflictos resueltos).`

---

## Scheduling (PILOTO — Routines de nube)
- **Feeder (modo run):** una Routine por batch de clientes activos, a **mediodía ART** (separado del Daily Check
  9am). Connectors **Supabase + SHURQ** (ya no AdLabs), continue-on-error, sin repo. Corre **ANTES** del autopush.
- **Compose:** no migrado.
- Multi-marketplace = cubierto (cada marca CA es su propio `brand`).

## Edge cases
| Situación | Comportamiento |
|---|---|
| Ayer sin data (lag/finde) | Pool 0 → snapshot `candidates:[]` + status ok. |
| `query_table` error tras 1 reintento | `status:"datafail"`, `candidates:[]`. |
| Paginación (`has_more`) | Seguir con `offset += 200` hasta traer todo el pool. No cortar antes. |
| Filas Scavenger en el pull | Excluir por fila (case-insensitive) ANTES de deduplicar (preciso). |
| Término con órdenes en una campaña y 0 en otra | Zero-sale es sobre el **total agregado**: filtrar `orders==0 && sales==0` DESPUÉS de dedup. |
| Marca propia en un término | Relevante — nunca negar. |
| Término en `protected_relevant` | Relevante SIEMPRE — nunca va al snapshot (Step 4.1). |
| Término protegido que también está en roots/competitors | Conflicto: en learn se remueve de roots/competitors y se loguea. |
| Término relevante | NO va al snapshot. |
| Pool enorme (cuenta grande) | Paginar; juzgar en tandas; nunca subir el piso de clicks (≥1). |
| Perfil sin `product_fiche` (v1) | Ficha inferida; ningún juicio llega a `high` por attribute-mismatch. |
| ASIN con `product_fiche.status="no_fiche"` | attribute-mismatch de ese producto no llega a `high`. |
| `competitor` con `monitor_only:true` | Relevante — nunca negar. |
| Config sin `shurq_account_id` | `reason:"config incompleto: falta shurq_account_id"`, saltar. |

---

## Migración AdLabs → SHURQ (referencia rápida)
| AdLabs (V2.0) | SHURQ (V3.0) |
|---|---|
| `adlabs_team_id` + `adlabs_profile_id` | `shurq_account_id` (int) + `mkp_id` |
| `get_entity_data("search_term", filters DATE/CLICKS>=1/ORDERS=0/CAMPAIGN_STATE=ENABLED)` | `query_table("searchterms_daily", filters report_date=y, mkp_id, clicks>=1, campaign_status=ENABLED)` + paginación offset |
| `group_by_column("search_term")` + `download_data` CSV | dedup por `searched_term` en Python (sumar clicks/cost/orders/sales) |
| exclusión Scavenger sobre filas del pull | idéntico: excluir filas `"scavenger" in campaign_name.lower()` ANTES de dedup |
| `ORDERS=0` server-side (agregado) | filtrar `orders==0 && sales==0` DESPUÉS de agregar |
| ASIN anunciado / ad_group_name del row | parsear ASIN/línea del `campaign_name` (no hay columna ASIN/ad_group) |
| fallback Shurq `negative_keyword_finder` | SHURQ es primario; sin fallback AdLabs |
