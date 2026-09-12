---
name: search-term-harvest
description: >
  Search Term Harvesting workflow for Sophie Society. Analyzes search terms from a
  client's auto and broad campaigns, identifies candidates to graduate to exact/phrase
  campaigns, and delivers an XLSX to the client's Drive-synced folder + a draft to the
  internal channel with the Drive link to the XLSX. Uses SHURQ as the only data source (config from Supabase public.clients).
  Trigger when Nacho says "search term harvest para [Brand]", "search term harvest for [Brand]", "harvest search terms",
  "qué términos puedo harvestear de [Brand]", "which terms can I harvest for [Brand]", "hacé el harvest de [Brand]", "do the harvest for [Brand]",
  "run the harvest for [Brand]", "qué exact terms graduamos", "which exact terms do we graduate", or any combination
  of "harvest" + client name. Multi-marketplace (Happy Fox US + CA) → 1 harvest
  separate per marketplace.
---

# Search Term Harvest Skill (V5 · SHURQ)

**Versión actual:** V5.0 SHURQ (2026-09-12) — **migración AdLabs → SHURQ + config a Supabase.** Sube de V4.4.
Cambios de V5.0 (SOLO capa de datos; el filtro de candidatos, el XLSX y el Slack draft quedan **idénticos**,
y el `_harvest_history.json` sigue siendo **local**):
1. **Config desde Supabase** `public.clients` (ya no JSONs locales ni `_active_clients.json`). Resolución de
   cuenta por `shurq_account_id` + `mkp_id` (ya no `adlabs_team_id`/`adlabs_profile_id`).
2. **Step 2 (CVR):** `get_ads_summary` de SHURQ scopeado a la cuenta (sin fallback AdLabs).
3. **Step 3 (search terms):** `query_table("searchterms_daily")` paginado, fuente auto/broad, `orders>0`
   (reemplaza `search_term_harvesting`, que ya NO existe, y el fallback `get_entity_data`). Scavenger SE INCLUYE.
4. **Step 5 (ya-graduados):** `query_table("keywords_daily")` EXACT/PHRASE enabled (reemplaza `list_keywords`
   —topea 200 sin offset— y el fallback AdLabs); Scavenger EXCLUIDO del `existing_set`.
5. Output (XLSX a Drive + Slack draft + history local) **sin cambios**.

**Versión previa:** V4.4 (2026-05-30) — ver changelog en `memory/search_term_harvest_changelog.md`

Identificá search terms en campañas auto/broad listos para graduar a Phrase/Exact. Output: 1 XLSX por config (multi-MP → N XLSX) en `Projects\[BrandFolder]\Search Term Harvest\`, más un Slack draft al canal interno del cliente que contiene **únicamente el link de Drive al XLSX** (sin resumen ni top candidatos).

---

## Global config

```
Config del cliente:          Supabase (conector Supabase MCP, proyecto POD 66 - Organization)
  Tabla public.clients (columna config JSONB) — brand_name, shurq_account_id, amazon_marketplace,
  acos_target, harvest_min_clicks, drive_folder_id, slack_internal_channel_id.
  (adlabs_team_id/adlabs_profile_id pueden seguir en el config; se IGNORAN.)

Datos (search terms / CVR / keywords):  SHURQ (conector de nube) — get_ads_summary + query_table.
  account_id = int(shurq_account_id), mkp_id derivado de amazon_marketplace.

Output folder pattern (Drive-synced):
  C:\Users\Nacho Bosca\Desktop\Claude\Projects\[BrandFolder]\Search Term Harvest\

Harvest history file:
  [output folder]\_harvest_history.json     (JSON con {"search_term": "YYYY-MM-DD"} de runs anteriores)
  IMPORTANTE: este archivo vive DENTRO de la carpeta Search Term Harvest/ del brand,
  NUNCA en la carpeta raíz del cliente. Usar pathlib local — NO usar Drive MCP.

Slack draft tool:            slack_send_message_draft  (NEVER direct send)
Fallback Slack channel:      #harvest-and-negations  (C0APNUJK1PW) — solo si config no tiene slack_internal_channel_id

Drive link al XLSX (Step 9):
  cfg["drive_folder_id"] = ID de la carpeta RAÍZ del cliente en Drive (Projects\[BrandFolder]\),
  capturado en client-onboarding. El skill resuelve la subcarpeta "Search Term Harvest" debajo
  para que el link/upload caiga exactamente en el path syncheado con la carpeta local.
  Si el config no tiene drive_folder_id, el skill degrada a búsqueda global por título.
```

---

## Step 1: Resolve brand → load config (desde Supabase)

Resolvé el `requested_brand` contra la tabla `clients` de Supabase (igual que `negative-targeting` /
`daily-negatives-supabase` Step 1):
```sql
select brand, active, config from public.clients
where active
  and (lower(brand) like lower('%<requested_brand>%')
       or exists (select 1 from jsonb_array_elements_text(coalesce(config->'alternative_names','[]'::jsonb)) a
                  where lower(a) like lower('%<requested_brand>%')));
```
`matching_entries` = filas que matchean (multi-marketplace → 2, ej. "Happy Fox" + "Happy Fox (CA)").
Zero filas → STOP y listá `select brand from public.clients where active`.

**Multi-marketplace:** N filas → N harvests separados (Step 2-7 corre N veces).

**Schema validation + resolución de cuenta SHURQ:**
```python
import json
from datetime import date, timedelta
REQUIRED = ["brand_name", "shurq_account_id", "amazon_marketplace"]
MKP = {"US":1,"GB":2,"UK":2,"CA":4,"MX":5,"BR":6,"DE":7,"ES":8,"FR":9,"IT":10,
       "NL":16,"PL":19,"SE":20,"BE":21,"AE":15,"SA":23,"IE":24}

for entry in matching_entries:
    cfg = entry["config"]                       # jsonb de public.clients
    missing = [k for k in REQUIRED if not cfg.get(k)]
    if missing:
        warn(f"[{cfg.get('brand_name','?')}] faltan campos requeridos: {missing} → STOP ese entry"); continue
    if not cfg.get("slack_internal_channel_id"):
        warn(f"[{cfg['brand_name']}] sin slack_internal_channel_id → fallback a #harvest-and-negations")
    acc = int(cfg["shurq_account_id"])
    mkp = MKP.get(str(cfg["amazon_marketplace"]).upper())
    if mkp is None:
        warn(f"[{cfg['brand_name']}] marketplace inválido: {cfg.get('amazon_marketplace')} → STOP ese entry"); continue

acos_target = cfg.get("acos_target") or 0.50   # fallback conservador 50% si falta
harvest_min_clicks = cfg.get("harvest_min_clicks", 10)
```

**Ventana de datos:**
```python
today = date.today()
window_days = 30
start_date = (today - timedelta(days=window_days)).isoformat()
end_date   = (today - timedelta(days=1)).isoformat()
```

Respetar ventana custom si Nacho la especifica.

---

## Step 2: CVR promedio de la cuenta (igual que negative-targeting)

```python
# SHURQ (account-scoped). get_ads_summary → data.overall.{clicks,orders,cost,sales,...}
summary = await call_tool("get_ads_summary", {
    "account_id": acc, "marketplace_id": mkp,
    "start_date": start_date, "end_date": end_date})
overall = summary["data"]["overall"]
total_clicks = overall.get("clicks", 0)
total_orders = overall.get("orders", 0)
data_source_summary = "shurq"

account_cvr = total_orders / total_clicks if total_clicks > 0 else None
if not account_cvr:
    raise ValueError(f"Sin CVR para {cfg['brand_name']}. Stop.")

print(f"Account CVR: {account_cvr:.2%} | window: {start_date} → {end_date} | source: {data_source_summary}")
```

---

## Step 3: Pull search terms

**SHURQ `query_table("searchterms_daily")` — reemplaza `search_term_harvesting` (ya no existe) y el fallback AdLabs.**
Traé de la ventana SOLO fuentes de descubrimiento (auto/broad) con conversiones (`orders>0`), paginando por offset:
```python
raw = []; offset = 0
while True:
    filters = [
      {"column":"report_date","operator":">=","value": start_date},
      {"column":"report_date","operator":"<=","value": end_date},
      {"column":"mkp_id","operator":"=","value": mkp},
      {"column":"orders","operator":">=","value": 1},
      {"column":"campaign_status","operator":"=","value":"ENABLED"},
    ]
    r = await call_tool("query_table", {
        "account_id": acc, "table_name": "searchterms_daily",
        "columns": "searched_term,campaign_name,campaign_id,clicks,cost,orders,sales,match_type,api_type",
        "filters": <filters como STRING JSON>, "sort_by": "sales", "sort_dir": "DESC",
        "limit": 200, "offset": offset})
    raw += r["data"]
    if not r["metadata"].get("has_more"): break
    offset += 200

# Fuente auto/broad (regla de harvest): quedate SOLO con match_type null (auto/SPA) o "BROAD".
# Descartá EXACT/PHRASE (ya-graduadas) y ASIN_*/PT (no son harvest de keyword).
def _is_autobroad(mt):
    m = (mt or "").upper()
    return m == "" or m == "NONE" or m == "BROAD"
raw = [x for x in raw if _is_autobroad(x.get("match_type"))]

# ⚠️ Scavenger SE INCLUYE (a diferencia de daily-negatives): un término que convierte en Scavenger ES
# candidato a graduar (ese es el punto de la Scavenger). NO excluir Scavenger acá.

# Dedup por término, sumando cross-campaña. Conservá la campaña de ORIGEN (mayor sales) y su match_type.
agg = {}
for row in raw:
    term = (row.get("searched_term") or "").strip()
    if not term: continue
    k = term.lower()
    d = agg.setdefault(k, {"search_term": term, "campaign_name":"", "match_type":"",
                           "impressions":0, "clicks":0, "spend":0.0, "sales":0.0, "orders":0, "_max_sales":-1})
    d["clicks"] += int(row.get("clicks") or 0)
    d["orders"] += int(row.get("orders") or 0)
    d["spend"]  += float(row.get("cost") or 0)
    d["sales"]  += float(row.get("sales") or 0)
    s = float(row.get("sales") or 0)
    if s > d["_max_sales"]:
        d["_max_sales"] = s
        d["campaign_name"] = row.get("campaign_name") or ""
        d["match_type"] = "broad" if (row.get("match_type") or "").upper()=="BROAD" else "auto"
search_terms = list(agg.values())
data_source_st = "shurq"
```
> `searchterms_daily` no trae `impressions` en el set pedido (payload más chico) → queda `impressions=0`;
> si el XLSX lo necesita, agregá `impressions` a `columns`. Sin data (0 filas) → seguí con `search_terms=[]`
> (igual se genera el XLSX). Si `query_table` falla tras 1 reintento → abortá ese entry con warning.

**Estructura esperada por search term:**
```python
term = {
    "search_term":   "...",
    "campaign_name": "...",
    "match_type":    "...",     # auto / broad (campaign source)
    "impressions":   0,
    "clicks":        0,
    "spend":         0.0,
    "sales":         0.0,
    "orders":        0,
}
# Derivados:
term["acos"] = term["spend"] / term["sales"] if term["sales"] > 0 else None
term["cvr"]  = term["orders"] / term["clicks"] if term["clicks"] > 0 else None
term["cpc"]  = term["spend"] / term["clicks"] if term["clicks"] > 0 else None
```

---

## Step 4: Cargar harvest history (dedup cross-runs)

> ⚠️ **IMPORTANTE — leer antes de implementar:**
> - El history file **siempre** vive dentro de `Search Term Harvest/` del brand, **NO** en la carpeta raíz del cliente.
> - **NO usar `google_drive_create_file`, `parentId`, `client_folder_id`, ni ningún tool del MCP de Drive** para este archivo. Usar pathlib local (la carpeta es Drive-synced, Drive Desktop replica el cambio).
> - El skill **debe** chequear `HISTORY_PATH.exists()` antes de escribir. Si existe → leer y mergear, **nunca** sobreescribir creando un archivo nuevo aparte.

```python
import re

# --- Resolver el nombre REAL de la carpeta del cliente ---
# Fuente de verdad: el TÍTULO de la carpeta de Drive en cfg["drive_folder_id"]. Ese título es el
# nombre exacto de la carpeta local syncheada — CON espacios y todo (ej. "Happy Fox", "Leefy
# Organics"). NO normalizar sacando espacios: eso crearía una carpeta nueva NO syncheada que
# no matchea drive_folder_id, dejando el XLSX en un folder distinto del que se linkea en Step 9.
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

OUTPUT_DIR = Path(r"C:\Users\Nacho Bosca\Desktop\Claude\Projects") / FOLDER_NAME / "Search Term Harvest"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
HISTORY_PATH = OUTPUT_DIR / "_harvest_history.json"   # ← exact path, no variations

# Idempotent read: existe o no
if HISTORY_PATH.exists():
    try:
        previously_harvested = json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
        print(f"History loaded from {HISTORY_PATH}: {len(previously_harvested)} terms.")
    except json.JSONDecodeError as e:
        warn(f"History file corrupto en {HISTORY_PATH}: {e}. Tratando como vacío y sobreescribiendo al final del run.")
        previously_harvested = {}
else:
    previously_harvested = {}   # primera vez para este brand/MP
    print(f"No prior history at {HISTORY_PATH} — first run.")

for term in search_terms:
    term["previously_harvested"] = previously_harvested.get(term["search_term"].lower())
```

**Carpeta vs filename:** `FOLDER_NAME` = nombre real de la carpeta (de Drive, con espacios) → define el path local syncheado. `BRAND_TOKEN` = versión sin espacios SOLO para el nombre del archivo. Ej. Happy Fox: ambos configs (US/CA) escriben en `Projects\Happy Fox\Search Term Harvest\`, con filenames `..._HappyFox_US_...` y `..._HappyFox_CA_...` (no colisionan).

---

## Step 5: Excluir keywords ya existentes como Exact/Phrase

Traé el catálogo de keywords EXACT/PHRASE **enabled** de `keywords_daily` (paginable) — NO `list_keywords`
(topea 200 sin offset). Reemplaza el fallback AdLabs.
```python
krows = []; offset = 0
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
    krows += r["data"]
    if not r["metadata"].get("has_more"): break
    offset += 200

# EXACT/PHRASE únicamente; ⛔ EXCLUIR Scavenger del set "ya-targeted" (las Scavenger targetean TODO →
# no deben bloquear el harvest hacia campañas normales).
existing_set = {
    (r.get("keyword_text") or "").lower()
    for r in krows
    if (r.get("match_type") or "").upper() in ("EXACT","PHRASE")
    and "scavenger" not in (r.get("campaign_name") or "").lower()
}

for term in search_terms:
    term["already_targeted"] = term["search_term"].lower() in existing_set
```

---

## Step 6: Filtrar candidatos

```python
THRESHOLDS = {
    "min_clicks":          harvest_min_clicks,   # default 10
    "min_orders":          1,
    "max_acos":            acos_target,
    "min_cvr_ratio":       1.0,                  # CVR >= account_cvr
    "strong_acos_override": 0.6,                 # ACOS < target × 0.6 → bypasea CVR
}

harvest_candidates = []
excluded = []

for term in search_terms:
    # Historial cross-runs
    if term["previously_harvested"]:
        excluded.append({**term, "exclusion_reason": f"Previously Harvested ({term['previously_harvested']})"})
        continue

    # Ya existe como Exact/Phrase
    if term["already_targeted"]:
        excluded.append({**term, "exclusion_reason": "Already targeted as Exact/Phrase"})
        continue

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
            harvest_candidates.append(term)
            continue
        cvr_str = f"{term['cvr']:.2%}" if term["cvr"] else "N/A"
        reason = f"CVR por debajo del promedio ({cvr_str} < {account_cvr:.2%})"

    excluded.append({**term, "exclusion_reason": reason})

# Orden: revenue desc, luego CVR desc
harvest_candidates.sort(key=lambda t: (-t["sales"], -(t["cvr"] or 0)))
excluded.sort(key=lambda t: -t["clicks"])

# Acción propuesta (match type)
def proposed_action(search_term):
    return "Add as Phrase" if len(search_term.strip().split()) <= 2 else "Add as Exact"

for t in harvest_candidates:
    t["action"] = proposed_action(t["search_term"])
```

---

## Step 7: Build XLSX (un solo archivo, 4 hojas)

```python
import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment
from openpyxl.utils import get_column_letter

GREEN_FILL  = PatternFill("solid", fgColor="38A169")
YELLOW_FILL = PatternFill("solid", fgColor="ECC94B")
HEADER_FILL = PatternFill("solid", fgColor="2D2D2D")
HEADER_FONT = Font(color="FFFFFF", bold=True)

def style_header(ws, row, n_cols):
    for col in range(1, n_cols + 1):
        c = ws.cell(row=row, column=col)
        c.fill = HEADER_FILL
        c.font = HEADER_FONT
        c.alignment = Alignment(horizontal="center")

def autofit(ws):
    for col in ws.columns:
        max_len = max((len(str(cell.value or "")) for cell in col), default=0)
        ws.column_dimensions[get_column_letter(col[0].column)].width = min(max_len + 4, 60)

date_str = date.today().strftime("%Y%m%d")
out_path = OUTPUT_DIR / f"{date_str}_{BRAND_TOKEN}_SearchTermHarvest.xlsx"
wb = openpyxl.Workbook()
wb.remove(wb.active)

# --- Hoja 1: Summary ---
ws = wb.create_sheet("Summary")
ws.append([f"Search Term Harvest — {cfg['brand_name']}"])
ws["A1"].font = Font(bold=True, size=14)
ws.append([])
ws.append(["Marketplace:", cfg.get("amazon_marketplace", "—")])
ws.append(["Window:", f"{start_date} → {end_date}"])
ws.append(["Account CVR:", f"{account_cvr:.2%}"])
ws.append(["ACOS target:", f"{acos_target:.0%}"])
ws.append(["Min clicks:", harvest_min_clicks])
ws.append([])
ws.append(["Harvest Candidates:", len(harvest_candidates)])
ws.append(["Excluded:", len(excluded)])
ws.append([])
if harvest_candidates:
    total_sales = sum(t["sales"] for t in harvest_candidates)
    total_spend = sum(t["spend"] for t in harvest_candidates)
    total_orders = sum(t["orders"] for t in harvest_candidates)
    ws.append(["Total candidates sales:", f"${total_sales:.2f}"])
    ws.append(["Total candidates spend:", f"${total_spend:.2f}"])
    ws.append(["Total candidates orders:", total_orders])
ws.append([])
ws.append(["Data source (summary):", data_source_summary])
ws.append(["Data source (search terms):", data_source_st])

# --- Hoja 2: Harvest Candidates ---
ws = wb.create_sheet("Harvest Candidates")
headers = ["Search Term","Campaign","Match Type","Impressions","Clicks","Orders",
           "Sales ($)","Spend ($)","ACOS","CVR","CPC ($)","ACOS vs Target","CVR vs Avg","Action"]
ws.append(headers)
style_header(ws, 1, len(headers))

for c in harvest_candidates:
    acos_vs = (c["acos"] - acos_target) * 100 if c["acos"] else None
    cvr_vs  = (c["cvr"]  - account_cvr) * 100 if c["cvr"]  else None
    ws.append([
        c["search_term"], c["campaign_name"], c["match_type"],
        c["impressions"], c["clicks"], c["orders"],
        round(c["sales"], 2), round(c["spend"], 2),
        f"{c['acos']:.1%}" if c["acos"] else "N/A",
        f"{c['cvr']:.2%}"  if c["cvr"]  else "N/A",
        round(c["cpc"], 2) if c["cpc"] else None,
        f"{acos_vs:+.1f}pp" if acos_vs is not None else "N/A",
        f"{cvr_vs:+.1f}pp"  if cvr_vs  is not None else "N/A",
        c["action"]
    ])
    # Highlight: strong ACOS (< target × 0.6) → green; rest of candidates → yellow
    fill = GREEN_FILL if c["acos"] and c["acos"] < acos_target * 0.6 else YELLOW_FILL
    for col in range(1, len(headers) + 1):
        ws.cell(row=ws.max_row, column=col).fill = fill

autofit(ws)

# --- Hoja 3: Excluded ---
ws = wb.create_sheet("Excluded")
ex_headers = headers + ["Exclusion Reason"]
ws.append(ex_headers)
style_header(ws, 1, len(ex_headers))

for c in excluded:
    acos_vs = (c["acos"] - acos_target) * 100 if c["acos"] else None
    cvr_vs  = (c["cvr"]  - account_cvr) * 100 if c["cvr"]  else None
    ws.append([
        c["search_term"], c["campaign_name"], c["match_type"],
        c["impressions"], c["clicks"], c["orders"],
        round(c["sales"], 2), round(c["spend"], 2),
        f"{c['acos']:.1%}" if c["acos"] else "N/A",
        f"{c['cvr']:.2%}"  if c["cvr"]  else "N/A",
        round(c["cpc"], 2) if c["cpc"] else None,
        f"{acos_vs:+.1f}pp" if acos_vs is not None else "N/A",
        f"{cvr_vs:+.1f}pp"  if cvr_vs  is not None else "N/A",
        proposed_action(c["search_term"]),
        c["exclusion_reason"]
    ])

autofit(ws)

# --- Hoja 4: Copy-Paste ---
ws = wb.create_sheet("Copy-Paste Lists")
ws.append(["PHRASE GRADUATES"])
style_header(ws, 1, 1)
for t in harvest_candidates:
    if t["action"] == "Add as Phrase":
        ws.append([t["search_term"]])
ws.append([])
ws.append(["EXACT GRADUATES"])
style_header(ws, ws.max_row, 1)
for t in harvest_candidates:
    if t["action"] == "Add as Exact":
        ws.append([t["search_term"]])
ws.column_dimensions["A"].width = 50

wb.save(out_path)
print(f"XLSX saved: {out_path}")
```

---

## Step 7b: Snapshot para el Master Dashboard (tab Harvest)

Además del XLSX, escribir un snapshot que alimenta la tab **Harvest** del Master Dashboard (Pod Nacho). Reusa `harvest_candidates` ya calculados (que YA excluyen ya-targeteados-exact/phrase y previously-harvested — por eso el dashboard nunca muestra términos ya graduados). Cero pulls extra.

```python
import json as _json
MD_DIR = Path(r"C:\Users\Nacho Bosca\Desktop\Claude\Projects\General\sophie-society-clients\master-dashboard\harvest")
MD_DIR.mkdir(parents=True, exist_ok=True)
STEM = entry["config_filename"].replace(".json","")   # p.ej. "Natchiketa", "HappyFox_CA"

def _src(mt):
    m=(mt or "").lower()
    return "auto" if "auto" in m else ("broad" if "broad" in m else (m or "manual"))

snap_cands = [{
    "term": t["search_term"], "orders": t["orders"], "clicks": t["clicks"],
    "spend": round(t["spend"],2), "sales": round(t["sales"],2),
    "acos": round(t["acos"]*100) if t["acos"] is not None else None,
    "cvr":  round(t["cvr"]*100)  if t["cvr"]  is not None else None,
    "src": _src(t.get("match_type")),
    "match": "phrase" if t["action"]=="Add as Phrase" else "exact",
} for t in harvest_candidates]

from datetime import datetime, timezone, timedelta
now_art = datetime.now(timezone(timedelta(hours=-3)))
snapshot = {
  "schema":"weekly-harvest-snapshot-v1","generated_at_iso":now_art.isoformat(),
  "meta":{"title_date":today.strftime("%A, %B %d, %Y"),"short_date":today.strftime("%b %-d") if os.name!="nt" else today.strftime("%b %#d"),
          "window_label":f"Ultimos {window_days} dias - {start_date} a {end_date}","pull_time":now_art.strftime("%H:%M ART"),"data_source":data_source_st},
  "client":{"brand_name":cfg["brand_name"],"marketplace":cfg.get("amazon_marketplace","US"),
            "currency_prefix":"CA$" if cfg.get("amazon_marketplace")=="CA" else "$","status":"ok",
            "product_summary":_extract_product_desc(cfg) if "_extract_product_desc" in dir() else cfg.get("product_category",""),
            "window_days":window_days,"acos_target":acos_target,
            "pool_total":len([t for t in search_terms if t.get("orders",0)>0]),
            "candidates_sales":round(sum(t["sales"] for t in harvest_candidates),2),
            "candidates":snap_cands}
}
(MD_DIR / f"{STEM}_Harvest.json").write_text(_json.dumps(snapshot,indent=2,ensure_ascii=False),encoding="utf-8")
print(f"Master dashboard harvest snapshot written: {STEM}_Harvest.json ({len(snap_cands)} candidates)")
```
> El compose del Master Dashboard (tarea `daily-negatives-compose`) levanta este snapshot en su próximo deploy. No hay que tocar el scheduling del harvest — las tareas semanales existentes en Cowork ya corren este skill; con este paso, además alimentan el dashboard. `product_summary` sale de la descripción de producto del config; si no hay, usa `product_category`.

## Step 8: Update harvest history

**Merge in-place, never create a parallel file.** `HISTORY_PATH` apunta al archivo único en `Search Term Harvest/_harvest_history.json` — siempre escribir a ESE path.

```python
# Mergear los candidatos del run actual con el historial existente
for t in harvest_candidates:
    previously_harvested[t["search_term"].lower()] = date.today().isoformat()

# Write in-place to the exact same path leído en Step 4
HISTORY_PATH.write_text(
    json.dumps(previously_harvested, indent=2, ensure_ascii=False, sort_keys=True),
    encoding="utf-8"
)
print(f"History updated in-place: {HISTORY_PATH} ({len(previously_harvested)} terms total)")
```

> ⚠️ **No usar `create_file`, `google_drive_create_file`, ni ningún workflow que pueda generar un duplicate del archivo** (`_harvest_history.json` en otra carpeta o con otro nombre). El sync de Drive Desktop se encarga de propagar el cambio sin generar duplicates.

---

## Step 9: Slack draft — solo el link de Drive al XLSX

El draft al canal interno contiene **únicamente el link de Drive al XLSX** que se guardó en Step 7 — sin resumen, sin top candidatos, sin lista de exclusiones. Esto aplica **siempre**, incluso si hubo 0 candidatos (el XLSX se guardó igual con la hoja Summary en 0s y la hoja Excluded poblada).

El XLSX ya está guardado local en una carpeta Drive-synced, así que Drive Desktop lo está subiendo a Google Drive. Lo ubicamos por nombre para obtener su `webViewLink`.

```python
import time, base64

slack_channel = cfg.get("slack_internal_channel_id") or "C0APNUJK1PW"   # fallback #harvest-and-negations
fell_back = (slack_channel == "C0APNUJK1PW" and not cfg.get("slack_internal_channel_id"))
mp_suffix = f" — {cfg.get('amazon_marketplace', '')}" if len(matching_entries) > 1 else ""

# --- Resolver la subcarpeta Drive que está syncheada con la carpeta local ---
# cfg["drive_folder_id"] = ID de la carpeta RAÍZ del cliente en Drive (Projects\[BrandFolder]\),
# capturado en client-onboarding. La subcarpeta "Search Term Harvest" cuelga de ella y es la que
# está syncheada con OUTPUT_DIR local. Si el config no tiene drive_folder_id → None (degradamos).
brand_folder_id = cfg.get("drive_folder_id")
harvest_folder_id = None
if brand_folder_id:
    sub = search_files(query=(
        f"title = 'Search Term Harvest' and parentId = '{brand_folder_id}' "
        f"and mimeType = 'application/vnd.google-apps.folder'"
    ))
    sub_hits = sub.get("files", [])
    harvest_folder_id = sub_hits[0]["id"] if sub_hits else None
    # NO crear la subcarpeta acá: Drive Desktop la crea vía sync. Crearla por API arriesga un
    # duplicate folder. Si no existe todavía, caemos a brand_folder_id (un nivel arriba).

# --- Obtener el link de Drive al XLSX ---
file_name = out_path.name   # ej. 20260530_PoopJuice_SearchTermHarvest.xlsx (multi-MP: ..._HappyFox_CA_...)
drive_link = None

# 1) Ubicar el archivo que Drive Desktop está sincronizando. Retry: el sync tarda unos segundos.
#    Si tenemos la subcarpeta, scopeamos la búsqueda ahí (más rápido + evita colisiones de nombre
#    entre clientes). Si no, búsqueda global por título.
scope = f" and parentId = '{harvest_folder_id}'" if harvest_folder_id else ""
for attempt in range(6):   # ~hasta ~60s
    results = search_files(query=f"title = '{file_name}'{scope}")
    files = results.get("files", [])
    if files:
        f = files[0]
        drive_link = f.get("webViewLink") or get_file_metadata(fileId=f["id"]).get("webViewLink")
        break
    time.sleep(10)

# 2) Fallback: si el sync todavía no lo subió, subirlo directo para garantizar un link.
#    parentId = subcarpeta Search Term Harvest (path correcto, syncheado con la carpeta local) →
#    sino la raíz del cliente → sino My Drive raíz.
if not drive_link:
    warn(f"[{cfg['brand_name']}] XLSX no encontrado en Drive vía sync tras 6 intentos. Subiendo directo.")
    created = create_file(
        title=file_name,
        base64Content=base64.b64encode(out_path.read_bytes()).decode("ascii"),
        contentMimeType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        parentId=harvest_folder_id or brand_folder_id,   # None → My Drive raíz
    )
    drive_link = created.get("webViewLink") or get_file_metadata(fileId=created["id"]).get("webViewLink")

# --- Mensaje único: solo el link ---
if drive_link:
    msg = f"🌾 *Search Term Harvest — {cfg['brand_name']}{mp_suffix}* | {start_date} → {end_date}\n{drive_link}"
else:
    # Último recurso si Drive no devuelve link: path local (no clickeable, pero no se pierde el output).
    warn(f"[{cfg['brand_name']}] No se pudo obtener link de Drive. Usando path local.")
    msg = f"🌾 *Search Term Harvest — {cfg['brand_name']}{mp_suffix}* | {start_date} → {end_date}\n`{out_path}`"

slack_send_message_draft(channel=slack_channel, text=msg)

if fell_back:
    print(f"⚠️ [{cfg['brand_name']}] sin slack_internal_channel_id — draft fue a #harvest-and-negations.")
else:
    print(f"✅ [{cfg['brand_name']}{mp_suffix}] — draft con link enviado al canal interno.")
```

> El resumen (cantidad de candidatos, top por revenue, exclusiones) ya **no** va al Slack: vive todo dentro del XLSX (hojas Summary / Harvest Candidates / Excluded). El draft es deliberadamente un mensaje de una línea + link.

---

## Edge cases

| Situación | Comportamiento |
|---|---|
| Brand no está en `public.clients` (o `active=false`) | Sugerir `client-onboarding`. No fabricar. |
| Fila sin `shurq_account_id` o marketplace inválido | Flag + skip ese entry, seguir con otros. Backfillear vía onboarding. |
| `query_table`/`get_ads_summary` de SHURQ falla tras 1 reintento | Stop ese entry, log error, seguir con otros (no hay fallback AdLabs). |
| `acos_target` null | Default 0.50, avisar a Nacho. |
| `slack_internal_channel_id` null | Fallback a `#harvest-and-negations` con warning. |
| `searchterms_daily` 0 filas auto/broad con orders | `search_terms=[]` → XLSX igual (Summary en 0s). |
| 0 candidatos | XLSX se guarda igual (Summary en 0s, Excluded poblada). Draft = mismo mensaje de una línea + link de Drive. |
| Multi-marketplace | 1 harvest por config (Happy Fox = 2 XLSX, 2 drafts). |
| Multi-product line | Tratado igual que multi-MP: 1 harvest por línea. |
| Historial cross-runs no existe | Primera vez — se crea al final del run. |
| Cualquier cantidad de candidatos | El draft solo lleva el link de Drive — el detalle completo vive en el XLSX. |
| Drive no encuentra el XLSX (sync lento) | Retry ~60s; si falla, upload directo vía `create_file` a la subcarpeta Search Term Harvest (`drive_folder_id`); último recurso: path local en el draft. |
| `drive_folder_id` ausente en config | Búsqueda global por título (sin scope de carpeta) + fallback `create_file` a My Drive raíz. Sugerir correr `client-onboarding` para capturarlo. |
| Subcarpeta `Search Term Harvest` no existe aún en Drive (1ª corrida + sync lento) | No se crea por API (riesgo de duplicate folder); upload va a la raíz del cliente. El sync luego sube la copia a la subcarpeta → posible duplicate puntual del XLSX, no del folder. |
| Carpeta de output no existe | `mkdir(parents=True, exist_ok=True)`. |
| Ventana custom de Nacho | Respetar. |
| Search term ya está como Phrase/Exact | Excluded tab con razón "Already targeted as Exact/Phrase". |
| Search term en historial | Excluded tab con "Previously Harvested (YYYY-MM-DD)". |
