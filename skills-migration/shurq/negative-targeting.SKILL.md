---
name: negative-targeting
description: >
  Negative Targeting audit for Sophie Society. Analyzes search terms and ASINs
  that are burning budget without converting, generates candidates to negate, and
  delivers an XLSX to the client's Drive-synced folder + a draft to their internal channel
  with the Drive link to the XLSX. Uses SHURQ as the only data source (config from Supabase public.clients).
  Trigger when Nacho says "negative targeting para [Brand]", "negative targeting for [Brand]", "audit de negativos
  para [Brand]", "negatives audit for [Brand]", "qué negativos agrego para [Brand]", "which negatives do I add for [Brand]",
  "negative keyword audit", "negativos para [Brand]", "negatives for [Brand]", "run the negatives for [Brand]",
  "wasted spend en [Brand]", "wasted spend for [Brand]", or any combination of "negativ" + client name. For multi-marketplace
  (Happy Fox US + CA), generate a separate audit per marketplace.
---

# Negative Targeting Skill (V4 · SHURQ)

**Versión actual:** V4.0 SHURQ (2026-09-12) — **migración AdLabs → SHURQ + config a Supabase.** Sube de V3.7.1.
Cambios de V4.0 (SOLO capa de datos; el motor de juicio de relevancia del Step 3b, el XLSX del Step 5 y el
Slack draft del Step 6 quedan **idénticos**):
1. **Config desde Supabase** `public.clients` (ya no JSONs locales de Drive ni `_active_clients.json`).
   Resolución de cuenta por `shurq_account_id` + `mkp_id` (ya no `adlabs_team_id`/`adlabs_profile_id`).
2. **Step 2 (CVR):** `get_ads_summary` de SHURQ scopeado a la cuenta (sin fallback AdLabs).
3. **Step 3 (search terms):** `query_table("searchterms_daily")` paginado (reemplaza `negative_keyword_finder`,
   que ya NO existe, y el fallback `get_entity_data`). El cross-check de órdenes usa el mismo pull.
4. **Step 4 (ASINs):** ASIN targets zero-sale desde `query_table("searchterms_daily")` (search terms que SON
   un ASIN; reemplaza `negative_asin_targets`, que ya NO existe, y el fallback AdLabs). `get_product_detail`
   de SHURQ sigue para el cross-check de categoría.
5. Output (XLSX a Drive + Slack draft) **sin cambios** — sigue local/Drive.

**Versión previa:** V3.7.1 (2026-06-09) — ver changelog en `memory/negative_targeting_changelog.md`

Audit de negative targeting: encuentra search terms y product targets que queman budget sin convertir. Output: 1 XLSX por config (multi-marketplace → 2 XLSX) en la carpeta Drive-synced del cliente, más un Slack draft al canal interno que contiene **únicamente el link de Drive al XLSX** (sin resumen ni listas de candidatos).

> 🚨 **REGLA CRÍTICA (V3.1):** El XLSX (Step 5) DEBE ejecutarse SIEMPRE antes del Slack draft (Step 6), incluso si hay 0 candidatos. NUNCA saltar Step 5. Si el save del XLSX falla, capturar el error y agregarlo como warning visible al Slack draft — pero igual mandar el Slack. Al final del skill, imprimir SIEMPRE en el chat la ruta absoluta del XLSX y su tamaño en bytes (o el error si falló).

> 🚨 **REGLA CRÍTICA (V3.7) — POOL LOW-CLICK: ≥1 CLICK SIGNIFICA ≥1, SIN EXCEPCIONES.** PROHIBIDO subir el piso de clicks (a 2, 3 o lo que sea) "para que el análisis sea manejable" — los términos de 1 click son EL CORAZÓN de esta capa (las marcas competidoras casi siempre tienen 1 solo click). El volumen se maneja con tandas (`JUDGE_BATCH`), NUNCA filtrando. PROHIBIDO también crear categorías intermedias tipo "revisión manual": cada término sale `Relevante` o `Irrelevante`, nada más — marca ajena va DIRECTO a Irrelevante, no a revisión. Step 3b incluye asserts y prints obligatorios que hacen visible cualquier desvío (ver checklist al final de Step 3b).

> 🚨 **REGLA CRÍTICA (V3.6) — VENTANA DE DATOS = 7 DÍAS, HARDCODEADA.** La ventana es SIEMPRE los últimos 7 días (`window_days = 7`). NO usar 30, NO usar 10, NO inferir otra ventana de corridas anteriores ni de otros skills. La ÚNICA excepción es que Nacho pida explícitamente otra ventana EN EL MENSAJE DE ESTA corrida (ej. "negative targeting para X, últimos 30 días"). Si no lo pidió en este mensaje → 7 días, sin preguntar. Imprimir la ventana usada al inicio de la corrida: `Ventana: {start_date} → {end_date} (7 días default)`.

---

## Global config

```
Config del cliente:          Supabase (conector Supabase MCP, proyecto POD 66 - Organization)
  Tabla public.clients (columna config JSONB) — brand_name, shurq_account_id, amazon_marketplace,
  managed_asins/asins, product_category, notes, drive_folder_id, slack_internal_channel_id.
  (adlabs_team_id/adlabs_profile_id pueden seguir en el config; se IGNORAN.)

Datos (search terms / CVR / ASIN targets):  SHURQ (conector de nube) — get_ads_summary + query_table.
  account_id = int(shurq_account_id), mkp_id derivado de amazon_marketplace.

Output folder pattern (Drive-synced):
  C:\Users\Nacho Bosca\Desktop\Claude\Projects\[FolderName]\Negative Targeting\
  FolderName = nombre REAL de la carpeta del cliente (con espacios), derivado del título de la
  carpeta de Drive en cfg["drive_folder_id"]. NO normalizar sacando espacios (ver Step 5).

Slack draft tool:            slack_send_message_draft  (NEVER direct send)
Fallback Slack channel:      #harvest-and-negations  (C0APNUJK1PW) — solo si el config no tiene slack_internal_channel_id

Drive link al XLSX (Step 6):
  cfg["drive_folder_id"] = ID de la carpeta RAÍZ del cliente en Drive (Projects\[FolderName]\),
  capturado en client-onboarding. El skill resuelve la subcarpeta "Negative Targeting" debajo
  para que el link/upload caiga exactamente en el path syncheado con la carpeta local.
  Si el config no tiene drive_folder_id, el skill degrada a búsqueda global por título.
```

---

## Step 1: Resolve brand → load config (desde Supabase)

Resolvé el `requested_brand` contra la tabla `clients` de Supabase (igual que `daily-check-client-supabase` /
`daily-negatives-supabase` Step 1):
```sql
select brand, active, config from public.clients
where active
  and (lower(brand) like lower('%<requested_brand>%')
       or exists (select 1 from jsonb_array_elements_text(coalesce(config->'alternative_names','[]'::jsonb)) a
                  where lower(a) like lower('%<requested_brand>%')));
```
`matching_entries` = filas que matchean (para multi-marketplace habrá 2, ej. "Happy Fox" + "Happy Fox (CA)").
Zero filas → STOP y listá `select brand from public.clients where active`.

**Multi-marketplace:** N filas → N audits separados (Step 2-7 corre N veces, 1 XLSX y 1 Slack draft por config).

**Schema validation + resolución de cuenta SHURQ:**
```python
REQUIRED = ["brand_name", "shurq_account_id", "amazon_marketplace"]
MKP = {"US":1,"GB":2,"UK":2,"CA":4,"MX":5,"BR":6,"DE":7,"ES":8,"FR":9,"IT":10,
       "NL":16,"PL":19,"SE":20,"BE":21,"AE":15,"SA":23,"IE":24}

for entry in matching_entries:
    cfg = entry["config"]                       # jsonb de public.clients
    missing = [k for k in REQUIRED if not cfg.get(k)]
    if missing:
        warn(f"[{cfg.get('brand_name','?')}] faltan campos requeridos: {missing} → STOP ese entry")
        continue
    if not cfg.get("slack_internal_channel_id"):
        warn(f"[{cfg['brand_name']}] sin slack_internal_channel_id → usar #harvest-and-negations como fallback")
    acc = int(cfg["shurq_account_id"])           # cuenta SHURQ
    mkp = MKP.get(str(cfg["amazon_marketplace"]).upper())
    if mkp is None:
        warn(f"[{cfg['brand_name']}] marketplace inválido: {cfg.get('amazon_marketplace')} → STOP ese entry")
        continue

# Productos del cliente — esquema de config inconsistente: unos usan "managed_asins",
# otros "asins". El item trae "name" (NO "title") y NO trae "category" por ASIN;
# la categoría vive a nivel raíz en cfg["product_category"]. Unificamos acá una sola vez.
managed_asins = cfg.get("managed_asins") or cfg.get("asins") or []

# product_context: usado por el juicio de relevancia (Step 3b) y el cross-check de ASINs (Step 4).
# Cuanto más rico, mejor juzga el modelo. Se incluye descripción de producto si está en notes.
def _extract_product_desc(cfg):
    notes = cfg.get("notes")
    if isinstance(notes, dict):
        for path in (("client_overview", "product_description"),
                     ("product_portfolio", "structure")):
            d = notes
            for k in path:
                d = d.get(k) if isinstance(d, dict) else None
            if d:
                return d
    return ""

product_context = {
    "brand":        cfg["brand_name"],
    "category":     cfg.get("product_category", ""),
    "description":  _extract_product_desc(cfg),
    "products":     [{"asin": m.get("asin"), "name": m.get("name", "")} for m in managed_asins],
}
# client_categories para el cross-check de relevancia de ASINs (Step 4).
client_categories = {cfg["product_category"]} if cfg.get("product_category") else set()
```

**Ventana de datos:**
```python
from datetime import date, timedelta
today = date.today()
window_days = 7   # 🚨 HARDCODED (V3.6). NO cambiar salvo pedido EXPLÍCITO de Nacho en este mensaje.
start_date = (today - timedelta(days=window_days)).isoformat()
end_date   = (today - timedelta(days=1)).isoformat()
print(f"Window: {start_date} → {end_date} ({window_days} days default)")
```

Ventana: **SIEMPRE últimos 7 días** (ver REGLA CRÍTICA al inicio). Solo usar otra si Nacho la pidió explícitamente en el mensaje de esta corrida.

---

## Step 2: Calcular CVR promedio de la cuenta

```python
# SHURQ (account-scoped). get_ads_summary devuelve data.overall.{clicks,orders,cost,sales,acos,...}
summary = await call_tool("get_ads_summary", {
    "account_id": acc, "marketplace_id": mkp,
    "start_date": start_date, "end_date": end_date})
overall = summary["data"]["overall"]
total_clicks = overall.get("clicks", 0)
total_orders = overall.get("orders", 0)
data_source = "shurq"

import math
account_cvr = total_orders / total_clicks if total_clicks > 0 else None
if not account_cvr:
    raise ValueError(f"No se pudo calcular CVR para {cfg['brand_name']}. Stop.")

dynamic_min_clicks = math.ceil((1 / account_cvr) * 1.3)
print(f"Account CVR: {account_cvr:.2%} | dynamic_min_clicks: {dynamic_min_clicks} | source: {data_source}")
```

---

## Step 3: Candidatos a Negative Keywords

### Pull de search terms (SHURQ `query_table`)

Traé TODO el pool de search terms de la ventana (7 días) con `clicks >= 1` de campañas ENABLED, paginando por
offset. Se trae **todo** (no solo zero-order) porque el cross-check del criterio necesita sumar órdenes por
término. Reemplaza `negative_keyword_finder` (ya no existe) y el fallback AdLabs.
```python
raw = []; offset = 0
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
    raw += r["data"]
    if not r["metadata"].get("has_more"): break
    offset += 200

# Dedup por término (sumando cross-campaña/keyword/día). Conservar campaña de ORIGEN (mayor cost) y match_type.
import re
ASIN_RE = re.compile(r'^b0[a-z0-9]{8}$', re.I)   # searched_term que ES un ASIN → va a Step 4, no acá
agg = {}
for row in raw:
    term = (row.get("searched_term") or "").strip()
    if not term or ASIN_RE.match(term): continue   # ASINs se manejan en Step 4 (negative ASINs)
    k = term.lower()
    d = agg.setdefault(k, {"search_term": term, "clicks":0, "orders":0, "spend":0.0, "sales":0.0,
                           "campaign_name":"", "match_type":"", "_max_cost":-1})
    d["clicks"] += int(row.get("clicks") or 0)
    d["orders"] += int(row.get("orders") or 0)
    d["spend"]  += float(row.get("cost") or 0)
    d["sales"]  += float(row.get("sales") or 0)
    c = float(row.get("cost") or 0)
    if c > d["_max_cost"]:
        d["_max_cost"] = c
        d["campaign_name"] = row.get("campaign_name") or ""
        d["match_type"] = row.get("match_type") or ""
search_terms = list(agg.values())
data_source_st = "shurq"
```
> **Sin data:** si el pull devuelve 0 filas → seguí con `search_terms=[]` (0 candidatos → igual se genera el XLSX,
> regla V3.1). Si `query_table` falla tras 1 reintento → abortá ese entry con warning (no hay fallback AdLabs).
> `searched_term` que ES un ASIN (`^b0...`) se maneja en Step 4 (negative ASINs), no acá.

### Criterio + cross-check (igual que V1)

```python
candidates_raw = [
    t for t in search_terms
    if t["clicks"] >= dynamic_min_clicks and t["orders"] == 0
]

# Cross-check: excluir términos con >1 orden en cualquier campaña en la ventana.
# El pull de SHURQ ya trajo TODOS los términos (con y sin órdenes) deduplicados → reusarlo.
all_search_terms = search_terms   # mismo pool deduplicado (incluye los que sí convirtieron)
orders_by_term = {}
for t in all_search_terms:
    key = t["search_term"].lower()
    orders_by_term[key] = orders_by_term.get(key, 0) + t.get("orders", 0)

neg_keyword_candidates = [
    t for t in candidates_raw
    if orders_by_term.get(t["search_term"].lower(), 0) <= 1
]

# Match type recomendado
def get_neg_match_type(search_term):
    return "Phrase" if len(search_term.strip().split()) <= 2 else "Exact"

for t in neg_keyword_candidates:
    t["neg_match_type"]  = get_neg_match_type(t["search_term"])
    t["match_type_src"]  = t.get("match_type", "—")   # Step 5 lee match_type_src en todas las filas
    t["source"]          = "Direct"

neg_keyword_candidates.sort(key=lambda x: x["spend"], reverse=True)
```

### Pattern aggregation (igual que V1)

```python
from collections import Counter

long_tail = [t for t in neg_keyword_candidates if t["neg_match_type"] == "Exact"]
all_words = []
for t in long_tail:
    all_words.extend(t["search_term"].lower().strip().split())
word_counts = Counter(all_words)

PATTERN_THRESHOLD = 3
existing_terms = {t["search_term"].lower() for t in neg_keyword_candidates}

pattern_candidates = []
for word, count in word_counts.items():
    if count >= PATTERN_THRESHOLD and word not in existing_terms:
        related = [t for t in long_tail if word in t["search_term"].lower().split()]
        pattern_candidates.append({
            "search_term":    word,
            "campaign_name":  "— (múltiples campañas)",
            "match_type_src": "—",
            "clicks":         sum(t["clicks"] for t in related),
            "spend":          sum(t["spend"]  for t in related),
            "orders":         0,
            "neg_match_type": "Phrase",
            "source":         f"Pattern Aggregation (x{count})",
            "pattern_count":  count,
        })

pattern_candidates.sort(key=lambda x: x["spend"], reverse=True)
```

### Step 3b: Términos irrelevantes de bajo click (NUEVO V3.4)

Captura los search terms que **no** llegan al umbral duro (`dynamic_min_clicks`) pero gastaron **≥1 click sin convertir** y son **irrelevantes** al producto. Irrelevante incluye tres motivos: **marca ajena/competidor**, **otra categoría/uso**, y — clave — **mismatch de atributos**: el término nombra la categoría correcta pero pide un ingrediente/scent/tamaño/feature que el producto NO tiene (ej. *"hair serum with tea tree"* para un hair serum sin tea tree). La decisión la toma el **modelo** (juicio semántico contra la ficha de atributos del producto). **Sin piso de spend y sin cap**: se juzga el pool completo (la ventana de 7 días ya acota el volumen), en tandas para mantenerlo tratable.

```python
# 1) Universo: TODOS los términos con ≥1 click, 0 órdenes en TODA la ventana,
#    que NO son ya candidatos directos ni pattern. Dedup por término (sumo clicks/spend
#    across campañas — la decisión de negar es a nivel término, no campaña).
direct_terms   = {t["search_term"].lower() for t in neg_keyword_candidates}
pattern_terms  = {t["search_term"].lower() for t in pattern_candidates}
excluded_terms = direct_terms | pattern_terms

agg = {}
for t in all_search_terms:            # full report, mismo source que el cross-check
    key = t["search_term"].lower()
    if t.get("orders", 0) != 0:        continue   # 0 órdenes estrictas (bajo volumen → 1 orden ya importa)
    if orders_by_term.get(key, 0) != 0: continue
    if t["clicks"] < 1:                continue
    if key in excluded_terms:          continue
    if key not in agg:
        agg[key] = {"search_term": t["search_term"], "campaign_name": "— (varias campañas)",
                    "match_type": t.get("match_type", "—"), "clicks": 0, "orders": 0, "spend": 0.0}
    agg[key]["clicks"] += t["clicks"]
    agg[key]["spend"]  += t.get("spend", 0.0)

low_click_pool = sorted(agg.values(), key=lambda x: x["spend"], reverse=True)

# 🚨 VERIFICACIÓN OBLIGATORIA DEL POOL (V3.7) — imprime stats que hacen visible cualquier
# filtro indebido. Si one_click_count == 0 en una cuenta con tráfico, es señal casi segura de
# que se aplicó un piso de clicks prohibido.
one_click_count = sum(1 for t in low_click_pool if t["clicks"] == 1)
min_clicks_pool = min((t["clicks"] for t in low_click_pool), default=0)
print(f"📊 low_click_pool: {len(low_click_pool)} terms | with 1 click: {one_click_count} "
      f"| min clicks in pool: {min_clicks_pool}")
assert min_clicks_pool <= 1 or not low_click_pool, (
    "VIOLACIÓN: el pool no tiene términos de 1 click — se aplicó un piso de clicks prohibido. "
    "Rearmar el pool con clicks >= 1."
)

# SIN CAP (V3.4): se juzga TODO el pool, no se descarta nada por spend ni por clicks — los
# términos de marcas competidoras suelen tener 1 solo click y poco spend (justo lo que NO
# queremos perder). La ventana de 7 días (Step 1) ya acota el volumen. El juicio del modelo
# se hace EN TANDAS de ~150 para mantenerlo tratable, recorriendo el pool COMPLETO.
# Guardarraíl anti-runaway (no es un cap funcional): si el pool es enorme, avisar — no truncar.
JUDGE_BATCH = 150
RUNAWAY_GUARD = 2000
if len(low_click_pool) > RUNAWAY_GUARD:
    warn(f"[{cfg['brand_name']}] low_click_pool MUY grande ({len(low_click_pool)} términos). "
         f"Se juzgan TODOS igual, en tandas de {JUDGE_BATCH}; puede tardar. "
         f"PROHIBIDO reducirlo filtrando por clicks/spend — solo Nacho puede acortar la ventana.")

# product_context y client_categories ya se construyeron en Step 1 (esquema de config unificado).
```

> **Juicio de relevancia — PASO DEL MODELO (no código determinístico).**
> Recorré **TODO** `low_click_pool` (sin cap), en **tandas de `JUDGE_BATCH` (~150)** términos, hasta cubrir el pool completo.
>
> **Paso previo (1 vez por corrida): armar la ficha de atributos del producto.** Antes de juzgar términos, derivá de `product_context` (nombres de ASINs, category, description, notes) una lista explícita de atributos REALES de los productos: ingredientes/componentes, scents/sabores, tamaños/formatos, materiales, audiencia y casos de uso. Imprimila en el chat (ej. para Masofta: *"Hair Growth Serum [ingredientes: los del listing, NO tea tree / NO rosemary / NO biotin salvo que estén en el nombre o notes], Shea Butter Lip Balm [ingrediente: shea butter], Body Glue"*). Esta ficha es la vara contra la que se juzga cada término. Si un atributo no se puede confirmar desde el config, tratarlo como "el producto NO lo tiene".
>
> **Juicio por término — la regla central (V3.6): un término es Relevante SOLO si TODOS sus calificadores matchean los atributos reales del producto.** No alcanza con que el término nombre la categoría correcta. Evaluá término completo = producto base + calificadores:
> - **Producto base no matchea** (otra categoría, otro uso, audiencia equivocada) → **Irrelevante**.
> - **Producto base matchea pero ≥1 calificador NO** (ingrediente que el producto no tiene, scent/sabor que no existe, tamaño/formato que no se vende, material distinto, feature ausente) → **Irrelevante**, negar como **Exact** (ver abajo). Ejemplo canónico de Nacho: producto = Hair Growth Serum sin tea tree → *"hair serum with tea tree"* es **Irrelevante** aunque "hair serum" matchee, porque el cliente busca específicamente tea tree y no lo va a comprar.
> - **Marca ajena** (competidor o cualquier marca ≠ `product_context["brand"]`) → **Irrelevante**. Sin lista de competidores en config: reconocé activamente nombres de marca, incluso de nicho — ante una palabra que parezca nombre propio de marca ajena, tratala como competidor.
> - **Término genérico sin calificadores conflictivos** (ej. *"hair growth serum"*, *"hair serum for women"* si aplica) → **Relevante** — NO negativizar; poco click no alcanza para concluir.
> **El beneficio de la duda aplica al producto base, no a los calificadores:** si no sabés si la categoría matchea → Relevante. Pero si el calificador nombra un atributo específico (ingrediente, scent, tamaño) que NO podés confirmar en la ficha → Irrelevante (el shopper pide algo que el producto no ofrece).
>
> **Excepción — equivalencias de dominio (V3.7.1):** el modelo SÍ puede usar conocimiento de dominio para resolver sinónimos y equivalencias de ingredientes/atributos (caso real validado por Nacho: *"pea sprout extract"* = **AnaGain**, el activo del hair serum → Relevante). Condiciones: (a) la equivalencia tiene que ser **confiable** (identidad conocida, no una especulación tipo "podría contenerlo"); (b) tiene que mapear a un atributo que el producto SÍ tiene (confirmado en la ficha o en el conocimiento del producto); (c) **declarar cada equivalencia usada en el chat** (`🔗 Equivalencias aplicadas: pea sprout extract = AnaGain (activo del Hair Growth Serum)`) para que Nacho pueda validarla o corregirla. Sin equivalencia confiable → aplica la regla general: el producto NO lo tiene → Irrelevante.
>
> **Salida binaria obligatoria:** cada término termina `Relevante` o `Irrelevante` — PROHIBIDO crear buckets intermedios ("revisión manual", "dudoso", "a confirmar"). Marca ajena va DIRECTO a Irrelevante (competitor brand), nunca a revisión.
>
> **Match type para esta capa:** los irrelevantes por **calificador** (producto base correcto + atributo ausente) van SIEMPRE como **Exact** — una phrase mataría tráfico bueno del producto base (`neg_match_type = "Exact"`, override de `get_neg_match_type`). Los irrelevantes por **producto base o marca ajena** siguen la regla normal (`get_neg_match_type`: ≤2 palabras → Phrase, ≥3 → Exact).
>
> Solo los `"Irrelevante"` pasan al output. En la columna Source del XLSX, distinguí el motivo: `Irrelevant (attribute mismatch)`, `Irrelevant (competitor brand)`, `Irrelevant (off-category)`.

```python
# 3) Filtrar a irrelevantes + etiquetar (mismas keys que el resto para el XLSX).
#    El modelo setea en cada término t["relevance"] y t["irrelevance_reason"] ∈
#    {"attribute mismatch", "competitor brand", "off-category"}.
low_click_irrelevant = [t for t in low_click_pool if t.get("relevance") == "Irrelevante"]
for t in low_click_irrelevant:
    reason = t.get("irrelevance_reason", "off-category")
    if reason == "attribute mismatch":
        t["neg_match_type"] = "Exact"   # override: phrase mataría tráfico bueno del producto base
    else:
        t["neg_match_type"] = get_neg_match_type(t["search_term"])
    t["match_type_src"] = t.get("match_type", "—")
    t["source"]         = f"Irrelevant ({reason})"
low_click_irrelevant.sort(key=lambda x: x["spend"], reverse=True)

# 🚨 CHECKLIST DE SALIDA DE STEP 3b (V3.7) — imprimir SIEMPRE estas 4 líneas en el chat
# antes de pasar a Step 4. Si alguna no se puede afirmar con verdad, NO seguir: corregir y re-correr 3b.
judged_count = sum(1 for t in low_click_pool if t.get("relevance") in ("Relevante", "Irrelevante"))
print(f"✔ Full pool judged: {judged_count}/{len(low_click_pool)} terms "
      f"(in {-(-len(low_click_pool)//JUDGE_BATCH)} batches)")
print(f"✔ Click floor: 1 (1-click terms in pool: {one_click_count})")
print(f"✔ Categories used: only Relevante/Irrelevante (no 'manual review' or intermediates)")
print(f"✔ Irrelevantes: {len(low_click_irrelevant)} "
      f"(attr mismatch: {sum(1 for t in low_click_irrelevant if 'attribute' in t['source'])}, "
      f"competitor: {sum(1 for t in low_click_irrelevant if 'competitor' in t['source'])}, "
      f"off-category: {sum(1 for t in low_click_irrelevant if 'off-category' in t['source'])})")
assert judged_count == len(low_click_pool), (
    "VIOLACIÓN: quedaron términos del pool sin juzgar. Completar las tandas restantes antes de Step 4."
)
```

---

## Step 4: Candidatos a Negative ASINs

Los negative-ASIN candidates salen de los search terms que **son un ASIN** (product targeting) — se filtran del
mismo pull `raw` de SHURQ (Step 3), reemplazando `negative_asin_targets` (ya no existe) y el fallback AdLabs.
```python
# Reusar `raw` (filas sin deduplicar de Step 3). Quedarse con searched_term que ES un ASIN, dedup por ASIN.
asin_agg = {}
for row in raw:
    term = (row.get("searched_term") or "").strip()
    if not ASIN_RE.match(term): continue      # solo ASINs
    a = term.upper()
    d = asin_agg.setdefault(a, {"asin": a, "clicks":0, "orders":0, "spend":0.0, "sales":0.0,
                                "campaign_name":"", "_max_cost":-1})
    d["clicks"] += int(row.get("clicks") or 0)
    d["orders"] += int(row.get("orders") or 0)
    d["spend"]  += float(row.get("cost") or 0)
    d["sales"]  += float(row.get("sales") or 0)
    c = float(row.get("cost") or 0)
    if c > d["_max_cost"]:
        d["_max_cost"] = c; d["campaign_name"] = row.get("campaign_name") or ""
asin_targets = list(asin_agg.values())
data_source_asin = "shurq"

# Threshold + cross-check (excluir propios ASINs). Umbral de ASINs = clicks >= 10 (como V3), orders == 0.
own_asins = {m["asin"].upper() for m in managed_asins}
neg_asin_candidates = [
    a for a in asin_targets
    if a["clicks"] >= 10 and a["orders"] == 0 and a["asin"].upper() not in own_asins
]
```

### Relevancia de categoría (sin cambios)

```python
# client_categories ya se construyó en Step 1 desde cfg["product_category"] (los configs NO
# traen categoría por ASIN). Si está vacío → category_relevant siempre "Desconocido" (ver edge cases).
# La categoría de cada ASIN candidato se trae de SHURQ get_product_detail (searchterms_daily no la trae).
for a in neg_asin_candidates:
    try:
        pd = await call_tool("get_product_detail", {
            "account_id": acc, "marketplace_id": mkp, "asin": a["asin"]})
        a["category"] = (pd.get("data") or {}).get("category", "") or ""
    except Exception:
        a["category"] = ""   # sin lookup → "Desconocido" abajo

def is_category_relevant(asin_category, client_categories):
    if not asin_category:
        return "Desconocido"
    asin_cat_lower = asin_category.lower()
    match = any(
        cat.lower() in asin_cat_lower or asin_cat_lower in cat.lower()
        for cat in client_categories
    )
    return "Sí" if match else "No"

for a in neg_asin_candidates:
    a["category_relevant"] = is_category_relevant(
        a.get("category", ""),
        client_categories
    )

# Ordenar: "No" primero (más fuertes), luego "Desconocido", luego "Sí". Dentro de cada grupo, spend desc.
order_key = {"No": 0, "Desconocido": 1, "Sí": 2}
neg_asin_candidates.sort(key=lambda a: (order_key.get(a["category_relevant"], 3), -a["spend"]))
```

---

## Step 5: Build XLSX

Output único: un archivo `.xlsx` en la carpeta del cliente Drive-synced.

```python
import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment
from openpyxl.utils import get_column_letter
from pathlib import Path

import re

# --- Resolver el nombre REAL de la carpeta del cliente ---
# Fuente de verdad: el TÍTULO de la carpeta de Drive en cfg["drive_folder_id"]. Ese título es el
# nombre exacto de la carpeta local syncheada — CON espacios y todo (ej. "Happy Fox", "Leefy
# Organics"). NO normalizar sacando espacios: eso crearía una carpeta nueva NO syncheada que no
# matchea drive_folder_id, dejando el XLSX en un folder distinto del que se linkea en Step 6.
if cfg.get("drive_folder_id"):
    FOLDER_NAME = get_file_metadata(fileId=cfg["drive_folder_id"])["title"]   # "Happy Fox", "Pavidas", ...
else:
    # Fallback sin drive_folder_id: brand_name sin chars ilegales en Windows. Menos confiable —
    # backfilleá drive_folder_id vía client-onboarding para garantizar el path correcto.
    FOLDER_NAME = re.sub(r'[<>:"/\\|?*]', '', cfg["brand_name"]).strip()
    warn(f"[{cfg['brand_name']}] sin drive_folder_id: usando carpeta '{FOLDER_NAME}'. "
         f"Backfilleá drive_folder_id (client-onboarding) para asegurar el path syncheado.")

# Token normalizado SOLO para el filename (sin espacios). Multi-MP/línea agrega sufijo de
# marketplace para que US y CA no colisionen dentro de la MISMA carpeta del cliente.
BRAND_TOKEN = "".join(FOLDER_NAME.split())                          # "Happy Fox" → "HappyFox"
if len(matching_entries) > 1 and cfg.get("amazon_marketplace"):
    BRAND_TOKEN += f"_{cfg['amazon_marketplace']}"                  # US→HappyFox_US, CA→HappyFox_CA

OUTPUT_DIR = Path(r"C:\Users\Nacho Bosca\Desktop\Claude\Projects") / FOLDER_NAME / "Negative Targeting"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

date_str = date.today().strftime("%Y%m%d")
out_path = OUTPUT_DIR / f"{date_str}_{BRAND_TOKEN}_NegativeTargeting.xlsx"

# Styling
RED_FILL    = PatternFill("solid", fgColor="FF4444")
ORANGE_FILL = PatternFill("solid", fgColor="FFA500")
HEADER_FILL = PatternFill("solid", fgColor="2D2D2D")
HEADER_FONT = Font(color="FFFFFF", bold=True)

def style_header(ws, row, n_cols):
    for col in range(1, n_cols + 1):
        cell = ws.cell(row=row, column=col)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center")

def autofit(ws):
    for col in ws.columns:
        max_len = max((len(str(cell.value or "")) for cell in col), default=0)
        ws.column_dimensions[get_column_letter(col[0].column)].width = min(max_len + 4, 60)

wb = openpyxl.Workbook()
wb.remove(wb.active)

# --- Hoja 1: Neg Keywords ---
ws = wb.create_sheet("Neg Keywords")
headers = ["Search Term", "Campaign", "Match Type (Src)", "Clicks", "Orders", "Spend ($)", "Proposed Neg. Type", "Source"]
ws.append(headers)
style_header(ws, 1, len(headers))

for t in neg_keyword_candidates:
    ws.append([
        t["search_term"], t["campaign_name"], t["match_type_src"],
        t["clicks"], t["orders"], round(t["spend"], 2),
        t["neg_match_type"], "Direct"
    ])
    spend = t["spend"]
    fill = RED_FILL if spend >= 10 else (ORANGE_FILL if spend >= 5 else None)
    if fill:
        for col in range(1, len(headers) + 1):
            ws.cell(row=ws.max_row, column=col).fill = fill

if pattern_candidates:
    ws.append([])
    ws.append(["--- Pattern Aggregation ---"])
    for t in pattern_candidates:
        ws.append([
            t["search_term"], t["campaign_name"], t["match_type_src"],
            t["clicks"], t["orders"], round(t["spend"], 2),
            t["neg_match_type"], t["source"]
        ])

if low_click_irrelevant:
    ws.append([])
    ws.append(["--- Irrelevant (low-click) — <threshold, irrelevant to the product ---"])
    for t in low_click_irrelevant:
        ws.append([
            t["search_term"], t["campaign_name"], t["match_type_src"],
            t["clicks"], t["orders"], round(t["spend"], 2),
            t["neg_match_type"], t["source"]
        ])
        # Estos son por definición de bajo spend → marca naranja para distinguirlos de los duros.
        for col in range(1, len(headers) + 1):
            ws.cell(row=ws.max_row, column=col).fill = ORANGE_FILL

autofit(ws)

# --- Hoja 2: Neg ASINs ---
ws = wb.create_sheet("Neg ASINs")
headers = ["ASIN", "Product Title", "Campaign", "Clicks", "Orders", "Spend ($)", "Category", "Cat. Relevant?", "Neg. Level"]
ws.append(headers)
style_header(ws, 1, len(headers))

for a in neg_asin_candidates:
    ws.append([
        a["asin"], a.get("product_title", ""), a.get("campaign_name", ""),
        a["clicks"], a["orders"], round(a["spend"], 2),
        a.get("category", ""), a.get("category_relevant", "?"),
        a.get("neg_level", "Campaign")
    ])
    if a.get("category_relevant") == "No":
        for col in range(1, len(headers) + 1):
            ws.cell(row=ws.max_row, column=col).fill = RED_FILL

autofit(ws)

# --- Hoja 3: Copy-Paste Lists ---
ws = wb.create_sheet("Copy-Paste Lists")
ws.append(["NEGATIVE KEYWORDS"])
style_header(ws, 1, 1)
for t in neg_keyword_candidates:
    ws.append([t["search_term"]])
if pattern_candidates:
    ws.append([])
    ws.append(["PATTERN AGGREGATION"])
    style_header(ws, ws.max_row, 1)
    for t in pattern_candidates:
        ws.append([t["search_term"]])
if low_click_irrelevant:
    ws.append([])
    ws.append(["IRRELEVANT (LOW-CLICK)"])
    style_header(ws, ws.max_row, 1)
    for t in low_click_irrelevant:
        ws.append([t["search_term"]])
ws.append([])
ws.append(["NEGATIVE ASINs"])
style_header(ws, ws.max_row, 1)
for a in neg_asin_candidates:
    ws.append([a["asin"]])
ws.column_dimensions["A"].width = 50

# --- Hoja 4: Summary ---
ws = wb.create_sheet("Summary", 0)   # insert as first sheet
ws.append([f"Negative Targeting Audit — {cfg['brand_name']}"])
ws["A1"].font = Font(bold=True, size=14)
ws.append([])
ws.append(["Marketplace:", cfg.get("amazon_marketplace", "—")])
ws.append(["Window:", f"{start_date} → {end_date}"])
ws.append(["Account CVR:", f"{account_cvr:.2%}"])
ws.append(["Dynamic min_clicks:", dynamic_min_clicks])
ws.append(["Min clicks (ASINs):", 10])
ws.append([])
ws.append(["Neg Keywords (Direct):", len(neg_keyword_candidates)])
ws.append(["Neg Keywords (Pattern):", len(pattern_candidates)])
ws.append(["Neg Keywords (Irrelevant low-click):", len(low_click_irrelevant)])
ws.append(["Neg ASINs:", len(neg_asin_candidates)])
ws.append([])
total_kw_spend = sum(t["spend"] for t in neg_keyword_candidates)
total_lowclick_spend = sum(t["spend"] for t in low_click_irrelevant)
total_asin_spend = sum(a["spend"] for a in neg_asin_candidates)
ws.append(["Wasted spend (KW direct):", f"${total_kw_spend:.2f}"])
ws.append(["Wasted spend (KW irrelevant low-click):", f"${total_lowclick_spend:.2f}"])
ws.append(["Wasted spend (ASINs):", f"${total_asin_spend:.2f}"])
ws.append(["Total wasted spend:", f"${total_kw_spend + total_lowclick_spend + total_asin_spend:.2f}"])
ws.append([])
ws.append(["Data source (search terms):", data_source_st])
ws.append(["Data source (ASIN targets):", data_source_asin])
```

---

## Step 5b: Save + verificación obligatoria

```python
xlsx_saved = False
xlsx_error = None
xlsx_size_bytes = None

try:
    wb.save(out_path)
    # Verificación dura: el archivo tiene que existir en disco
    if not out_path.exists():
        raise FileNotFoundError(f"wb.save() corrió sin error pero {out_path} no existe en disco.")
    xlsx_size_bytes = out_path.stat().st_size
    if xlsx_size_bytes < 1000:
        raise ValueError(f"XLSX guardado pero tamaño sospechoso ({xlsx_size_bytes} bytes).")
    xlsx_saved = True
    print(f"✅ XLSX saved OK: {out_path.resolve()} ({xlsx_size_bytes:,} bytes)")
except Exception as e:
    xlsx_error = f"{type(e).__name__}: {e}"
    print(f"❌ XLSX FALLÓ: {xlsx_error}")
    # NO abortar — seguir a Step 6 (Slack) con warning.
```

**REGLA:** Step 6 SIEMPRE se ejecuta después de este bloque, sin importar si `xlsx_saved` es True o False. El estado se refleja en el Slack draft.

---

## Step 6: Slack draft al canal interno del cliente

El draft al canal interno contiene **únicamente el link de Drive al XLSX** — sin wasted spend, sin listas de keywords/ASINs. Esto aplica **siempre**, incluso con 0 candidatos (el XLSX se guarda igual con la hoja Summary en 0s). El detalle completo vive dentro del XLSX (hojas Summary / Neg Keywords / Neg ASINs / Copy-Paste Lists).

El XLSX ya está guardado local en una carpeta Drive-synced (Step 5b), así que Drive Desktop lo está subiendo. Lo ubicamos por nombre para obtener su `webViewLink`.

```python
import time, base64

slack_channel = cfg.get("slack_internal_channel_id") or "C0APNUJK1PW"   # fallback al canal centralizado
fell_back_to_central = (slack_channel == "C0APNUJK1PW" and not cfg.get("slack_internal_channel_id"))
mp_suffix = f" — {cfg.get('amazon_marketplace', '')}" if len(matching_entries) > 1 else ""

# --- Obtener el link de Drive al XLSX (solo si se guardó OK en Step 5b) ---
drive_link = None
if xlsx_saved:
    # Resolver la subcarpeta "Negative Targeting" que está syncheada con OUTPUT_DIR local.
    # cfg["drive_folder_id"] = ID de la carpeta RAÍZ del cliente en Drive.
    brand_folder_id = cfg.get("drive_folder_id")
    neg_folder_id = None
    if brand_folder_id:
        sub = search_files(query=(
            f"title = 'Negative Targeting' and parentId = '{brand_folder_id}' "
            f"and mimeType = 'application/vnd.google-apps.folder'"
        ))
        sub_hits = sub.get("files", [])
        neg_folder_id = sub_hits[0]["id"] if sub_hits else None
        # NO crear la subcarpeta por API: Drive Desktop la crea vía sync. Crearla arriesga duplicate folder.
        # Si no existe todavía, caemos a brand_folder_id (un nivel arriba).

    # Ubicar el archivo que Drive Desktop está sincronizando. Retry: el sync tarda unos segundos.
    # Si tenemos la subcarpeta, scopeamos ahí (más rápido + evita colisiones de nombre entre clientes).
    file_name = out_path.name   # ej. 20260530_PoopJuice_NegativeTargeting.xlsx (multi-MP: ..._HappyFox_CA_...)
    scope = f" and parentId = '{neg_folder_id}'" if neg_folder_id else ""
    for attempt in range(6):   # ~hasta ~60s
        results = search_files(query=f"title = '{file_name}'{scope}")
        files = results.get("files", [])
        if files:
            f = files[0]
            drive_link = f.get("webViewLink") or get_file_metadata(fileId=f["id"]).get("webViewLink")
            break
        time.sleep(10)

    # Fallback: si el sync no lo subió, subirlo directo. parentId = subcarpeta (path correcto,
    # syncheado con la carpeta local) → raíz del cliente → My Drive raíz.
    if not drive_link:
        warn(f"[{cfg['brand_name']}] XLSX no encontrado en Drive vía sync tras 6 intentos. Subiendo directo.")
        created = create_file(
            title=file_name,
            base64Content=base64.b64encode(out_path.read_bytes()).decode("ascii"),
            contentMimeType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            parentId=neg_folder_id or brand_folder_id,   # None → My Drive raíz
        )
        drive_link = created.get("webViewLink") or get_file_metadata(fileId=created["id"]).get("webViewLink")

# --- Mensaje único: solo el link (o warning si el XLSX falló) ---
header = f"🚫 *Negative Targeting Audit — {cfg['brand_name']}{mp_suffix}* | {start_date} → {end_date}"
if xlsx_saved and drive_link:
    msg = f"{header}\n{drive_link}"
elif xlsx_saved and not drive_link:
    warn(f"[{cfg['brand_name']}] No se pudo obtener link de Drive. Usando path local.")
    msg = f"{header}\n`{out_path}`"   # último recurso: path local (no clickeable)
else:
    msg = f"{header}\n⚠️ *Could not generate the XLSX* — error: `{xlsx_error}`. Notify Nacho."

slack_send_message_draft(channel=slack_channel, text=msg)

# Confirm to Nacho — SIEMPRE imprimir ambos status (Slack + XLSX)
if fell_back_to_central:
    print(f"⚠️ [{cfg['brand_name']}] sin slack_internal_channel_id — draft fue a #harvest-and-negations.")
else:
    print(f"✅ [{cfg['brand_name']}{mp_suffix}] — draft con link enviado al canal interno.")

# Reporte final OBLIGATORIO del XLSX
if xlsx_saved:
    print(f"✅ XLSX: {out_path.resolve()} ({xlsx_size_bytes:,} bytes)")
else:
    print(f"❌ XLSX was NOT saved for [{cfg['brand_name']}{mp_suffix}]. Error: {xlsx_error}")
    print(f"   Ruta esperada: {out_path.resolve()}")
```

> El resumen (wasted spend, keywords, ASINs, pattern aggregation) ya **no** va al Slack: vive todo dentro del XLSX. El draft es deliberadamente un mensaje de una línea + link. Con 0 candidatos, el XLSX se guarda igual (Summary en 0s) y se manda el mismo mensaje de una línea + link.

---

## Edge cases

| Situación | Comportamiento |
|---|---|
| Brand no está en `public.clients` (o `active=false`) | Sugerir `client-onboarding`. No fabricar. |
| Fila sin `shurq_account_id` o marketplace inválido | Flag + skip ese entry, seguir con otros. Backfillear vía onboarding. |
| `query_table`/`get_ads_summary` de SHURQ falla tras 1 reintento | Stop ese entry, log error, seguir con otros (no hay fallback AdLabs). |
| `slack_internal_channel_id` null | Fallback a `#harvest-and-negations` con warning. |
| `get_product_detail` falla para un ASIN | `category=""` → `category_relevant="Desconocido"` (no rompe). |
| 0 candidatos totales | XLSX se guarda igual (Summary en 0s). Draft = mismo mensaje de una línea + link de Drive. |
| `acos_target` null | Ignorar — no se usa en V3. |
| Multi-marketplace (Happy Fox) | 2 audits: ambos escriben en `Projects\Happy Fox\Negative Targeting\` con filenames `..._HappyFox_US_...` / `..._HappyFox_CA_...` (no colisionan), 2 drafts a sus respectivos canales. |
| Multi-product line | Tratado igual que multi-marketplace: 1 audit por línea. |
| Cualquier cantidad de candidatos | El draft solo lleva el link de Drive — el detalle completo vive en el XLSX. |
| Carpeta de output no existe | `mkdir(parents=True, exist_ok=True)`. |
| `drive_folder_id` ausente en config | Carpeta de output = `brand_name` saneado; búsqueda global por título + fallback `create_file` a My Drive raíz. Sugerir `client-onboarding` para capturarlo. |
| Drive no encuentra el XLSX (sync lento) | Retry ~60s; si falla, upload directo vía `create_file` a la subcarpeta Negative Targeting; último recurso: path local en el draft. |
| Subcarpeta `Negative Targeting` no existe aún en Drive (1ª corrida + sync lento) | No se crea por API (riesgo duplicate folder); upload va a la raíz del cliente. El sync luego sube la copia a la subcarpeta → posible duplicate puntual del XLSX. |
| XLSX no se guardó (error en Step 5b) | Draft lleva el warning del error en vez del link (no hay archivo que linkear). |
| Drive Desktop no sincronizando | Archivo queda local. Avisar a Nacho si el sync está caído. |
| Config usa `asins` en vez de `managed_asins` | Step 1 unifica: `cfg.get("managed_asins") or cfg.get("asins")`. El item trae `name` (no `title`). |
| Sin productos ni `product_category` en config (ej. Masofta) | `product_context` queda con solo `brand` → el modelo juzga con menos contexto (más conservador), pero igual reconoce marcas competidoras. Backfilleá `product_category` + ASINs vía onboarding para mejor juicio. |
| Términos low-click irrelevantes (Step 3b) | Términos con ≥1 click, 0 órdenes, <umbral, juzgados irrelevantes por el modelo con 3 motivos: attribute mismatch (→ **Exact** forzado), competitor brand, off-category. Sin piso de spend, **sin cap**. Van marcados naranja en "Neg Keywords" + sección propia en Copy-Paste. |
| Término con producto base correcto pero atributo ausente (ej. "hair serum with tea tree") | **Irrelevante (attribute mismatch)** → negar como **Exact** (nunca Phrase: mataría tráfico bueno del producto base). |
| Atributo no confirmable desde el config | Tratarlo como "el producto NO lo tiene" → el término que lo pide es Irrelevante. **Excepción:** si el modelo conoce una equivalencia confiable con un atributo que el producto SÍ tiene (ej. pea sprout extract = AnaGain) → Relevante, declarando la equivalencia en el chat (`🔗 Equivalencias aplicadas: ...`) para que Nacho la valide. |
| `low_click_pool` enorme (> 2000) | Se juzga **todo igual** en tandas de ~150, **con warning** de que puede tardar. No se trunca ni se filtra por clicks/spend — solo Nacho puede acortar la ventana. |
| Tentación de subir el piso de clicks "para que sea manejable" | **PROHIBIDO** (regla crítica V3.7). El assert del pool falla si no hay términos de 1 click. El volumen se maneja con tandas, nunca filtrando. |
| Término dudoso → ¿bucket "revisión manual"? | **NO existe.** Salida binaria: Relevante o Irrelevante. Marca ajena → directo Irrelevante (competitor brand). |
| Ventana de datos | **SIEMPRE 7 días, hardcodeada** (V3.6 — regla crítica al inicio). Solo otra ventana si Nacho la pide explícitamente en el mensaje de esta corrida. |
