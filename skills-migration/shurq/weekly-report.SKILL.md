---
name: weekly-report
description: >
  Generate a Sophie Society weekly PPC performance report for an Amazon client from a
  SINGLE call — no XLSX, no manual download. Pulls the client config from Supabase, the
  performance data straight from the SHURQ MCP, the client's pending tasks from
  ClickUp, and the last 7–14 days of the client's internal Slack channel, then writes the
  report and sends it to the client's internal Slack channel. Trigger whenever Nacho says "weekly report para
  [client]", "run the weekly report", "do the report for [brand]", "generate the weekly
  for [brand]", "hacé el weekly de [brand]", or a brand name + "weekly" in any combination.
  Single-brand mode — for multi-marketplace clients (US + CA) generate one report per marketplace.
---

# Weekly Report Skill — Single-Call (V4 · SHURQ edition)

**Versión actual:** V4 (2026-09-11) — migrada de AdLabs a **SHURQ**. Misma estructura de reporte y
misma lógica de rankings que V3; lo único que cambió es la **capa de datos** (AdLabs → SHURQ) y la
**resolución de cuenta** (`adlabs_team_id`/`adlabs_profile_id` → `shurq_account_id` + `mkp_id`).

**Historial:** V3 (2026-08-16) — data pulled live from AdLabs, zero local files, zero Excel.

You generate a Sophie Society weekly PPC performance report for an Amazon client. **V4 pulls
everything itself in one call from SHURQ:**

- **Config** → Supabase `clients` table (POD 66 project)
- **Performance data** → SHURQ MCP (`get_ads_daily_trend` + `get_sales_traffic` + `get_orders_summary`), rolled up to Sun–Sat weeks
- **Pending tasks** → ClickUp (per-brand folder in the POD 66 space) — feeds Next Steps
- **Recent client context** → last 7–14 days of the client's internal Slack channel — feeds Next Steps
- **Output** → Slack message sent to the client's internal channel (for Nacho to review and forward to the client)

Week convention: **Sunday → Saturday** (NOT ISO Mon–Sun). Single-brand mode only.

**Respondé a Nacho en español.** El reporte se escribe en el idioma del cliente (`report_language`).

---

## Cómo se llama a SHURQ (mecánica del conector)

SHURQ expone **tres tools genéricas**: `search` (descubrir tools), `get_schema` (ver params) y
`execute` (correr Python restringido que llama `call_tool(name, params)`). Los tools "semánticos"
que usa este skill (`get_ads_daily_trend`, etc.) se invocan **desde adentro de `execute`** con
`await call_tool("<tool>", {...})`, o directo si el runtime los expone como tools MCP.

Reglas del sandbox de `execute` (importan para el rollup):
- Python de verdad: `None/True/False`, dict/list literales. **NO** hay `json.loads` (el resultado ya
  viene parseado como dict), **NO** hay `pandas`/`numpy`, **NO** hay `datetime.now()`/`date.today()`.
- `call_tool` es **async**: siempre `await call_tool(...)`.
- Para ventanas de fecha, pasá `start_date`/`end_date` como `'YYYY-MM-DD'` (el server calcula el rango).
- Encadená varias llamadas en un mismo bloque y `return` el resultado final.

**No hay `start_chat_session` ni `read_resource` ni references `mcp://data/...`** — eso era de AdLabs.
SHURQ no tiene sesión ni references que expiren; cada llamada es autónoma y trae los datos ya materializados.

---

## Config contract (Supabase `clients` table)

Project: **POD 66 - Organization** (`awhiobrcgghyiycxukjm`), table `public.clients`,
column `config` (jsonb). Fields used by this skill:

| Field | Required | Use |
|---|---|---|
| `brand_name` | ✅ | Display name + matching |
| `shurq_account_id` | ✅ | **SHURQ account (int), ej. 747.** Reemplaza `adlabs_team_id`/`adlabs_profile_id`. |
| `amazon_marketplace` | ✅ | "US"/"CA"/"UK"/… → derivá `mkp_id` (ver tabla abajo) |
| `slack_internal_channel_id` | ✅ | Internal channel the message is sent to |
| `owners` / `slack_names` | rec | Greeting ("Hey Jenna Doughton") |
| `acos_target` / `tacos_target` | rec | Target language in KPI section |
| `account_stage` | rec | Next Steps template baseline |
| `onboarding_date` | rec | "since you started with Sophie" framing window |
| `report_language` | rec | "en" / "es" |
| `dashboard_url` | rec | Client dashboard link for the header ("full data dashboard HERE"). If missing, omit the link line. |
| `team_took_over_date` | rec | When POD 66 took over the account. Drives the "since our team took over (last N weeks)" ranking window. Fallback: `onboarding_date`. |

> **Compat:** los campos `adlabs_team_id` / `adlabs_profile_id` pueden seguir en el config — este skill
> los **ignora**. Si `shurq_account_id` falta, flag + skip brand (ver edge cases).

### Marketplace → `mkp_id`

| amazon_marketplace | mkp_id | | amazon_marketplace | mkp_id |
|---|---|---|---|---|
| US | 1 | | IT | 10 |
| GB / UK | 2 | | NL | 16 |
| CA | 4 | | PL | 19 |
| MX | 5 | | SE | 20 |
| BR | 6 | | BE | 21 |
| DE | 7 | | AE | 15 |
| ES | 8 | | SA | 23 |
| FR | 9 | | IE | 24 |

Si el marketplace del cliente no está en la tabla, resolvé el `mkp_id` con
`call_tool("list_my_accounts", {})` (cada cuenta lista sus `marketplaces` con `mkp_id` + `country`).

---

## Step 1: Resolve brand → load config from Supabase

```sql
-- via Supabase MCP execute_sql on project awhiobrcgghyiycxukjm
-- Resolve by brand, brand_name, OR any alternative_names entry — clients are often known by
-- a consumer brand that differs from the legal entity (e.g. "Solar Reserve" → Every Cloud,
-- "MyNextGen" → Hekaya). Matching only `brand` misses these.
SELECT brand, active, config
FROM clients
WHERE active = true
  AND (
    lower(brand) LIKE '%' || lower(:requested_brand) || '%'
    OR lower(config->>'brand_name') LIKE '%' || lower(:requested_brand) || '%'
    OR EXISTS (
      SELECT 1
      FROM jsonb_array_elements_text(coalesce(config->'alternative_names','[]'::jsonb)) alt
      WHERE lower(alt) LIKE '%' || lower(:requested_brand) || '%'
    )
  );
```

- **1 row** → use it.
- **2+ rows** (multi-marketplace, e.g. Happy Fox US + CA) → tell Nacho up-front and run once per row, one Slack message each.
- **0 rows** → suggest running `client-onboarding`; do not fabricate.

Validate `shurq_account_id`, `amazon_marketplace`, `slack_internal_channel_id` are present. If a
required field is missing, warn and skip that brand. Derivá `account_id = int(shurq_account_id)` y
`mkp_id` desde `amazon_marketplace`.

---

## Step 2: Pull performance data from SHURQ (replaces the XLSX / AdLabs timeline)

> ⚠️ **MANDATORY — do NOT shortcut this step. This is a live single-call skill; there is NO
> attached XLSX.** Never wait for, expect, or fall back to "the file you attach." **You MUST pull the
> full trailing ~52-week window** and roll up **every** week, or every ranking silently breaks (a
> 3-week pull makes "best week of the last N" meaningless / falsely "record"). If SHURQ returns fewer
> weeks for a metric, that is fine — the data-aware ranking (Step 3) handles it — but you must always
> REQUEST the full window.

### 2a. Date window (Sun–Sat, "last complete week available")

Anclá al día de corrida (ART). SHURQ no da `date.today()` en su sandbox, así que computá las fechas
**vos** (el modelo sabe la fecha de hoy) y pasá strings `YYYY-MM-DD`:

```
today            = <hoy ART>
days_since_sunday = (weekday(today) + 1) % 7      # Mon=0..Sun=6 -> Sun=0
this_sunday      = today - days_since_sunday       # Sunday of the in-progress week
rw_end           = this_sunday - 1 day             # Saturday = end of last COMPLETE week
rw_start         = rw_end - 6 days                 # Sunday
pw_start         = rw_start - 7 days ; pw_end = pw_start + 6 days
# Run on Friday 2026-09-11 -> rw = 2026-08-31 .. 2026-09-06
date_from        = rw_start - 52 weeks             # trailing ~53-week window for rankings
date_to          = rw_end
```

### 2b. Pull the daily series (two SHURQ tools)

```python
acc = <account_id>; mkp = <mkp_id>
# Ad-attributed (PPC) daily: date, impressions, clicks, cost, sales, orders, units, acos, roas, cpc, ctr, cvr
ads = await call_tool("get_ads_daily_trend",
        {"account_id": acc, "marketplace_id": mkp, "start_date": date_from, "end_date": date_to})
# Total business daily: date, sessions, revenue, orders, units (Sales & Traffic + P&L)
st  = await call_tool("get_sales_traffic",
        {"account_id": acc, "marketplace_id": mkp, "start_date": date_from, "end_date": date_to})
```

- Both return `{"data": [ {row per day}, ... ], "metadata": {...}, "summary": {...}}`.
- **Currency:** read it from `get_orders_summary(...).metadata.currency` (pull once for the reporting
  week window), or from the account. Never hardcode `$` — UK clients → £, etc.

> **⚠️ SHURQ window cap:** si un tool cachea/limita el rango largo (devuelve menos filas de las
> esperadas o error de rango), **paginá en chunks de ~90 días** por `start_date`/`end_date` y
> concatená los `data[]`. La profundidad del ranking depende de cuántas semanas devuelva SHURQ; el
> ranking data-aware (Step 3) ya se adapta. Nunca acortes el REQUEST a propósito.

### 2c. Roll up daily → weekly (Sun–Sat) — VALIDATED MAPPING

Agrupá cada fila por su `week_start` (el domingo de esa fecha) y sumá. **Field mapping validado**
(Natchiketa, semana Aug 31–Sep 6 2026, reconcilia al centavo con el reporte real):

| Weekly KPI | Fuente | Cómo |
|---|---|---|
| `spend` | ads_daily | `sum(cost)` |
| `ppc_sales` | ads_daily | `sum(sales)` (ad-attributed) |
| `ppc_orders` | ads_daily | `sum(orders)` |
| `clicks` / `impressions` | ads_daily | `sum(clicks)` / `sum(impressions)` |
| `total_sales` | sales_traffic | `sum(revenue)` (= Seller Central total sales; == `get_orders_summary.revenue`) |
| `total_orders` | sales_traffic | `sum(orders)` |
| `total_sessions` | sales_traffic | `sum(sessions)` **si >0**, si no → `None` (ver caveat) |
| `organic_sales` | derived | `total_sales - ppc_sales` |

Ratios (idénticos a V3):
```
acos          = spend/ppc_sales            roas       = ppc_sales/spend
tacos         = spend/total_sales          total_roas = total_sales/spend
ppc_cvr       = ppc_orders/clicks          ctr        = clicks/impressions
total_cvr     = total_orders/total_sessions   (solo si total_sessions no es None)
```

**DATA-PRESENCE FLAGS (el fix anti-"rank de 53"):** una semana solo cuenta para una métrica si el
dato de esa métrica existe esa semana. Poné la métrica en `None` si no:
```
has_ppc = (spend>0) or (clicks>0) or (impressions>0)   # datos pagos presentes
has_org = total_sales>0                                 # datos orgánicos/marketplace presentes
# PPC / mixtas → None si not has_ppc ; orgánicas → None si not has_org
```

> **⚠️ Caveat SHURQ — Total Sessions / Total CVR:** en algunas cuentas `get_sales_traffic` devuelve
> `sessions: 0` (el reporte Sales & Traffic no está poblado en la fuente PG). Si **toda** la ventana
> viene con `sessions==0`, tratá `total_sessions` y `total_cvr` como **no disponibles**: mostralos
> como `N/A`, **no los rankees**, y omití la línea de sesiones en el análisis en vez de inventar un
> proxy. (V3/AdLabs las derivaba de `org_traffic + clicks`; SHURQ usa las sesiones reales de Amazon,
> mejores cuando existen, ausentes cuando la fuente no las trae.) Si vienen pobladas, usalas normal.

```
rw = weekly_data[rw_start]  (o la semana completa más reciente si falta)
pw = weekly_data[pw_start]  (o la anterior disponible)
```

---

## Step 3: WoW deltas, formatting, 3-week trend, rankings

Idéntico a V3 (source-agnostic). Resumen:

```python
def wow(this, prev, fmt):
    if this is None or prev in (None,0): return "N/A"
    if fmt=='pp':
        d=(this-prev)*100; return f"{'↓' if d<0 else '↑'} {abs(d):.2f} pp"
    d=(this-prev)/abs(prev)*100; return f"{'↑' if d>0 else '↓'} {abs(d):.1f}%"
SYM = {'USD':'$','GBP':'£','EUR':'€','CAD':'C$','AUD':'A$'}
CUR = SYM.get(currency_code, currency_code + ' ')   # currency_code de get_orders_summary.metadata.currency
fmt_pct   = lambda v: f"{v*100:.2f}%" if v is not None else "N/A"
fmt_dollar= lambda v: f"{CUR}{v:,.2f}" if v is not None else "N/A"
fmt_int   = lambda v: f"{int(round(v)):,}" if v is not None else "N/A"
fmt_roas  = lambda v: f"{v:.2f}x" if v is not None else "N/A"
```

| KPI | Display | Delta |
|---|---|---|
| ACOS / TACOS / Total CVR | fmt_pct | pp (ACOS,TACOS) · rel% (CVR) |
| Total Sales / PPC Sales / Organic Sales / Spend | fmt_dollar | rel% |
| Total Sessions | fmt_int | rel% |
| ROAS / Total ROAS | fmt_roas | rel% |

**3-week trend** (ACOS & TACOS): las últimas 3 semanas hasta rw, ej. `"37.99% → 33.81% → 47.11%"`.

**Rankings — DATA-AWARE windows (crítico para clientes nuevos / transferidos).**
SHURQ puede devolver menos semanas de PPC que de orgánico (bounded por lo que la Amazon Ads API
backfilleó al conectar la cuenta). **Nunca rankees una métrica PPC sobre semanas sin dato PPC** —
inventa semanas "record". Rankeá cada KPI solo sobre las semanas donde *esa métrica* tiene dato real.

```python
hist = [w for w in all_weeks if w <= rw_start]      # nunca rankear contra el futuro
def rank(metric, lower, window_start=None):
    weeks = [w for w in hist
             if weekly_data[w].get(metric) is not None
             and (window_start is None or w >= window_start)]
    if len(weeks) < 2 or weekly_data.get(rw_start, {}).get(metric) is None:
        return None
    s = sorted(weeks, key=lambda w: weekly_data[w][metric], reverse=not lower)
    return {'rank': s.index(rw_start) + 1, 'total': len(weeks)}
```

> ⚠️ **El denominador nunca es la ventana pulleada.** Si vas a escribir "of 52"/"of 53", pará: eso es
> el pull crudo, no el dato. Citá `total` de `rank()`. Direction: lower-is-better = acos, tacos;
> higher-is-better = el resto.

Metric → su data window (lo que `rank()` produce solo):
| Familia | Miembros | Rankea sobre |
|---|---|---|
| PPC | acos, roas, ppc_sales, ppc_cvr, ctr, spend | semanas ≥ `ppc_data_start` |
| Mixed (PPC-dependent) | tacos, total_sessions, total_cvr | semanas ≥ `ppc_data_start` |
| Organic / marketplace | total_sales, organic_sales, total_orders | semanas ≥ `organic_data_start` |

**Relationship frame** (elegí el que la historia necesita, siempre intersectado con la data window):
- **Data window** = todas las semanas elegibles para esa métrica. Frasea el conteo real:
  *"rank 3 of the last 11 weeks"*. **Nunca** "in account history" / "all-time".
- **Since you started with Sophie** = semanas ≥ `onboarding_date`.
- **Since our team took over** = semanas ≥ `team_took_over_date`. Para clientes **directos**
  (`team_took_over_date` null) = `onboarding_date` → un solo frame. Para **transferidos** es la fecha
  posterior → **ambos frames válidos y distintos**.

**Guards:**
- **Wording exacto — no los mezcles.** `onboarding_date` → **"since you started with Sophie"** (YOU =
  cliente). `team_took_over_date` → **"since our team took over"** (OUR = POD). Nunca híbridos.
- **Solo conteos nominales** — nunca percentage rank, nunca "all-time".
- **Anti-overclaim:** si una métrica tiene **< 6 semanas** de dato, sin superlativos; *"in the N weeks
  of paid data we have so far"* u omití el ranking de ese KPI.
- **Nunca cruces familias:** un "record" PPC se scopea a la ventana PPC; uno orgánico a la orgánica.
- Si la reporting week **precede `ppc_data_start`** (PPC recién lanzó): reportá orgánico/total normal y
  notá que paid tiene solo N semanas.

### Point 3 — Transferred clients (Sophie earlier, POD 66 later)
Dos fechas en config → dos frames distintos: `onboarding_date` (*"since you started with Sophie"*) y
`team_took_over_date` (*"since our team took over"*). Directos: `team_took_over_date` null → un frame.
Target language: mencioná `acos_target`/`tacos_target` cuando el KPI está at/below target o bajando.

---

## Step 4: Build Next Steps inputs — Data analysis + ClickUp + Slack

Idéntico a V3. Next Steps salen de **tres fuentes; el análisis de datos es obligatorio** — nunca
armes Next Steps solo de ClickUp + Slack.

### 4a. Data-driven recommendations (MANDATORY — las generás vos)
Razoná sobre la reporting week **y las semanas previas** (no solo esta). Mirá: WoW moves & 3-week
trends; eficiencia vs target (ACOS/TACOS vs `acos_target`/`tacos_target`); diagnóstico del driver
(¿caída de Total Sales fue paid-led u organic-led? ¿suba de ACOS por ventas más blandas a spend flat
o por más spend? ¿CVR cayó con tráfico sano → listing/targeting, o cayó el tráfico?); rankings
(proteger/escalar vs corregir); ad-dependency & halo. Convertí cada señal material en un paso
accionable. 2–4 pasos data-driven = la espina dorsal.

### 4b. Pending ClickUp tasks (per-brand folder en el space POD 66)
ClickUp workspace **90132860513**, space **POD 66** (`901312362368`). Cada cliente es un **folder**
con el nombre de la marca (ej. Natchiketa = `901318202158`) con listas `PPC Tasks` / `Content Tasks`.
Statuses en español (`pendiente`, `completado`).
```
clickup_search(workspace_id="90132860513", keywords="<brand>", filters={"asset_types":["task"]})
  -> hierarchy.category.id donde category.name == brand (folder_id)
clickup_filter_tasks(workspace_id="90132860513", folder_ids=[<folder_id>], include_closed=false)
  -> tareas cuyo status NO es completado/closed
```

### 4c. Recent client-channel context (last 7–14 days)
```
slack_read_channel(channel_id=<slack_internal_channel_id>, limit=60)   # filtrá a los últimos 14 días
```
Extraé señales operativas (stock, on/off de campañas, ediciones de listing/precio, launches,
reactivaciones). **Leé el canal SOLO para contexto — NUNCA para decidir si postear.** El canal tendrá
mensajes auto-posteados (Weekly Wins del lunes, reportes previos, Daily Checks): ignoralos como
contexto y **nunca los trates como "el reporte ya está hecho"**. Un Weekly Wins NO es un Weekly Report.

### 4d. Synthesize Next Steps
Hasta **5** bullets, priorizados. Mezclá las tres fuentes — **4a siempre presente**; ClickUp y Slack
aterrizan y completan. Dedupe donde una señal de datos y un item de ClickUp/Slack apuntan a lo mismo.
Usá el template de `account_stage` solo para llenar gaps:
- **launch:** expand keyword coverage · harvest converting terms · monitor ACOS · review bid floors · flag organic signals
- **growth:** raise bids on top converters · reallocate to efficient campaigns · review negatives · monitor halo · test match types
- **optimization:** audit high-spend/low-CVR keywords · consolidate overlaps · push ACOS to target · strengthen listing if CVR soft · review placements
- **scaling:** scale budget at-target campaigns · expand adjacent keywords · add SB/SD · watch TACOS as spend grows · set stretch targets

---

## Step 5: Write the report (real Sophie structure)

Slack-ready plain text, Slack bold con `*asteriscos*` y `_italics_`. Idioma per `report_language`
("en" default; "es" → full Spanish, misma estructura).

**Writing style — que se lea como una persona del equipo, no una IA:**
- **Segunda persona ("you"/"your").** El mensaje es PARA los owners en `slack_names`/`owners`; el único
  nombre que usás es el saludo ("Hey Mohamed,"), después es "you/your".
- **Nunca em dash `—`.** Terminá con punto, o usá coma, dos puntos o paréntesis. (El `–` en labels
  tipo "ACOS – 47%" está OK; el prohibido es el em dash largo a mitad de oración.)
- **Nunca tilde `~`** para aproximar. Escribí "about"/"around" o el número pelado.
- Variá cómo abren las oraciones; evitá la cadencia repetitiva "clause — clause".

```
Hey @[Owner], hope you're having a great week! Here's your performance snapshot and key takeaways for the week of [rw_start "Month DD"].
[If dashboard_url present:] You can find your full data dashboard HERE. ← hyperlink "HERE" to dashboard_url

*Performance Highlights*
[Un párrafo, 3–5 oraciones. Abrí con la señal más fuerte. Nombre métrica, valor, WoW move.
Bold a las cifras clave. Conectá los puntos (paid vs organic, efficiency vs volume). Tono directo.]

*KPI Performance*

*ACOS – [value] ([WoW pp]):*
3-week trend: [t1 → t2 → t3]. [1–2 líneas: ranking, target context, driver.]

*TACOS – [value] ([WoW pp]):*
3-week trend: [t1 → t2 → t3]. [ad-dependency, target context.]

*Total Sales – [value] ([WoW %]):*
[ranking, paid vs organic mix.]

*PPC Sales – [value] ([WoW %]):*
[efficiency, ROAS context.]

*Organic Sales – [value] ([WoW %]):*
[organic health, halo signal.]

*Total Sessions – [value] ([WoW %]):*
[traffic level + trend. Si sessions no disponibles en SHURQ → omití esta línea, no escribas N/A raro.]

*Total CVR – [value] ([WoW %]):*
[conversion quality, traffic mix. Idem: omití si no hay sessions.]

*Performance Analysis*
[Un párrafo, 3–5 oraciones. 2–3 rankings notables. Frame con las data-aware windows:
"of the last N weeks" / "since you started with Sophie" / "since our team took over".
Nunca "in account history" / "all-time". Cerrá con una línea forward-looking.]

*Next Steps*

• [step 1] … • [hasta 5, de Step 4d]

[Closing, ej.: "Thank you very much [Owner] and I hope you have an amazing weekend!"]
```

**Multi-marketplace:** mención sutil del marketplace en el opener ("…for the CA marketplace, week of …").

### Historical ranking language
Cada template nombra una ventana concreta — "of the last N weeks", "since you started with Sophie", o
"since our team took over" — nunca "in account history".

| Rank | Window | Template |
|---|---|---|
| 1 | either | "the best [KPI] week [since our team took over / since you started with Sophie / of the last N weeks]" |
| 2–3 | either | "[2nd/3rd] best [KPI] week [named window]" |
| 4–5 | 10+ weeks | "one of the top 5 [KPI] weeks [named window]" |
| 6–10 | 15+ weeks | "rank [n] of [N] [named window]" |
| bottom quartile | either | "one of the weaker [KPI] weeks [named window], worth addressing" |

Siempre rank/count nominal ("rank 12 of the last 14 weeks"). Nunca %, nunca "all-time".

---

## Step 6: Send to the internal Slack channel

- **SIEMPRE posteá. No hay chequeo de "ya posteado".** No escanees el canal para saltear porque hay un
  mensaje. El Weekly Wins del lunes es OTRO mensaje y nunca es "el reporte está hecho". Las ÚNICAS
  razones para saltear una marca son las de Steps 1–2 (config faltante / `shurq_account_id` / sin data).
- Enviá con **`slack_send_message`** directo a `slack_internal_channel_id` — el canal **interno**,
  nunca uno client-facing. Nacho lo revisa y lo forwardea. Usá send directo, **no**
  `slack_send_message_draft` (un draft puede fallar si alguien está componiendo; el post interno es
  seguro, se revisa antes de llegar al cliente).
- Sin canal → output inline a Nacho con nota. Multi-marketplace → un mensaje por marketplace.

---

## Edge cases

| Situation | Behavior |
|---|---|
| Brand not in Supabase `clients` | Suggest `client-onboarding`; do not fabricate |
| Missing `shurq_account_id` | Flag + skip brand (es problema de config real) |
| Missing `amazon_marketplace` | Resolvé `mkp_id` vía `list_my_accounts`; si sigue ambiguo, preguntá |
| Missing `slack_internal_channel_id` | Output inline, skip send |
| Missing `dashboard_url` | Omit the "full data dashboard HERE" line |
| Missing `team_took_over_date` | Fall back to `onboarding_date`, else last-14-weeks window |
| Missing `acos_target`/`tacos_target` | Skip target language for that KPI |
| **SHURQ `get_sales_traffic` sessions == 0 toda la ventana** | Total Sessions / Total CVR = no disponibles: N/A, no rankear, omitir esas líneas |
| **SHURQ limita la ventana larga** | Paginar en chunks de ~90 días por start/end_date y concatenar `data[]` |
| SHURQ tool devuelve error transitorio (timeout/rate-limit) | Reintentar 1 vez; si sigue, reportar el error real y skip esa marca (no inventar causa de config) |
| Reporting week absent in data | Use most recent complete week + flag to Nacho |
| < 2 weeks of history | Skip rankings; minimal report + tell Nacho |
| Newly onboarded — PPC data ≪ organic | Rank PPC metrics solo sobre `ppc_data_start`+; organic sobre `organic_data_start`+. Cite real counts |
| PPC metric con < 6 semanas | Skip superlatives; "in the N weeks of paid data so far" u omití ese ranking |
| Reporting week predates `ppc_data_start` | Report organic/total; notá paid tiene solo N semanas |
| Transferred client (`team_took_over_date` > `onboarding_date`) | Ambos frames válidos & distintos |
| `team_took_over_date` null | Directo POD-66 → tratar como `= onboarding_date` |
| DSP present | Este reporte es PPC-only; DSP fuera de scope |
| ClickUp folder not found for brand | Skip ClickUp; Next Steps de data + Slack |
| Slack channel unreadable | Skip Slack context en silencio; nunca bloquea el reporte |
| `report_language: "es"` | Full Spanish, misma estructura |

---

## Data-source quick reference (SHURQ edition)

| Need | Source | Key call |
|---|---|---|
| Client config | Supabase `clients` | `execute_sql` (project awhiobrcgghyiycxukjm) |
| Weekly PPC KPIs | SHURQ | `get_ads_daily_trend(account_id, marketplace_id, start_date, end_date)` → rollup |
| Total sales / orders / sessions | SHURQ | `get_sales_traffic(account_id, marketplace_id, start_date, end_date)` → rollup |
| Currency + totals sanity | SHURQ | `get_orders_summary(account_id, marketplace_id, start_date, end_date)` |
| Account/mkp resolution | SHURQ | `list_my_accounts()` |
| Pending tasks | ClickUp | `clickup_search` (folder) → `clickup_filter_tasks` (open) |
| Recent context | Slack | `slack_read_channel` (last 7–14 d) |
| Output | Slack | `slack_send_message` to the internal channel |

> **Migración AdLabs → SHURQ (para referencia):** `get_entity_data(profile)` + `query(profile_id)` +
> `get_entity_data(timeline)` + `download_data` + pandas rollup  →  `get_ads_daily_trend` +
> `get_sales_traffic` + rollup en plain Python. `adlabs_team_id`/`adlabs_profile_id` → `shurq_account_id`
> + `mkp_id`. Sin `start_chat_session`/`read_resource`/references.
