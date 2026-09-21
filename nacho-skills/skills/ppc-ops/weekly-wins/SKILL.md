---
name: weekly-wins
description: >
  Generate a Sophie Society Weekly Wins Slack message for a client from a SINGLE call — no
  XLSX, no manual download. Pulls the client config from Supabase and the performance data
  straight from the SHURQ MCP (same engine as weekly-report), then writes a short, Slack-ready
  client touchpoint and sends it to the client's internal Slack channel. The message is not only celebratory wins:
  it can also highlight an improving multi-week trend, or flag a focus area to concentrate on
  this week. Trigger whenever Nacho says "wins para [Brand]", "weekly wins for [Brand]", "write
  the wins for [Brand]", "do the weekly wins", "resaltá la mejora de [Brand]", "en qué enfocarnos
  esta semana en [Brand]", or any "wins"/"highlights"/"mejora"/"foco" + a client brand name.
  Single-brand mode — for multi-marketplace clients (US + CA), one message per marketplace.
---

# Weekly Wins Skill — Single-Call (V6 · SHURQ edition)

**Versión actual:** V6 (2026-09-12) — migrada de AdLabs a **SHURQ**. Misma lógica de rankings, selección
de highlights y mensaje que V5; lo único que cambió es la **capa de datos** (AdLabs `profile → query →
timeline → download` → SHURQ `get_ads_daily_trend` + `get_sales_traffic` + `custom_metric_calculator`) y
la **resolución de cuenta** (`adlabs_team_id`/`adlabs_profile_id` → `shurq_account_id` + `mkp_id`).

**Historial:** V5 (2026-08-16) — data pulled live en ~4 llamadas AdLabs, zero local files, zero Excel.

A short, Slack-ready client touchpoint (sent Mondays) built from the **same data engine as
`weekly-report` V4.2 (SHURQ)**. El engine SHURQ pulla la ventana completa en 3 series diarias
(`get_ads_daily_trend` + `get_sales_traffic` + `custom_metric_calculator`) y agrega en Python, sin
sesión ni references que expiren.

**This message has three possible flavors** (pick per the data and Nacho's phrasing):
1. **Wins** — metrics ranking near the top of their window. Celebratory.
2. **Improvement** — a metric on a clear positive recent trend (even if not top-ranked yet).
3. **Focus** — one thing to concentrate on / improve this week. Constructive, not alarmist.

Week convention: **Sunday → Saturday**. Single-brand mode only.

---

## Cómo se llama a SHURQ (mecánica del conector)

SHURQ expone `search` / `get_schema` / `execute`. Los tools semánticos (`get_ads_daily_trend`, etc.) se
invocan desde `execute` con `await call_tool("<tool>", {...})`, o directo si el runtime los expone.
Sandbox: Python real (`None/True/False`, dicts/listas), **sin** `json.loads` (el result ya viene
parseado), **sin** `pandas`/`numpy`, **sin** `datetime.now()`/`date.today()`. `call_tool` es async.
Fechas como `'YYYY-MM-DD'` (el server calcula el rango). **No hay `start_chat_session`/`read_resource`/
`query`/`download_data`** — eso era AdLabs.

---

## Shared with weekly-report (do NOT diverge)

Weekly Wins y Weekly Report deben quedar **consistentes**. Reusá verbatim:

- **Config source** — Supabase `clients` (project `awhiobrcgghyiycxukjm`). Campos: `brand_name`,
  **`shurq_account_id`**, **`amazon_marketplace`**, `slack_internal_channel_id`, `owners`/`slack_names`,
  `onboarding_date`, `team_took_over_date`, `report_language`, `dashboard_url`.
- **Data engine** — SHURQ `get_ads_daily_trend` + `get_sales_traffic` + `custom_metric_calculator`,
  rolled up a semanas Sun–Sat en Python. Mismo mapeo validado que weekly-report V4.2.
- **KPI definitions** — fórmulas idénticas. En particular, **el naming de CVR es fijo y compartido**:
  - **`CVR` = Total CVR = total_orders ÷ total_sessions**, donde **`total_sessions` viene de
    `custom_metric_calculator`** (sessions reales de Amazon, NO `seller_org_traffic + clicks`;
    `get_sales_traffic.sessions` está roto = 0). Esto reemplaza el proxy org_traffic+clicks de V5 y
    matchea weekly-report V4.2.
  - **`PPC CVR` = ppc_orders ÷ clicks.**
  Nunca etiquetes PPC CVR como "CVR" ni viceversa, en ningún skill.
- **Ranking windows** — misma lógica **data-aware** (abajo). **Nunca digas "in account history"** ni
  "all-time": solo pulleamos ~52 semanas y la historia PPC suele ser más corta. Usá el conteo real.
- **Currency** — nunca hardcodees `$`. Leé `currency` de `get_orders_summary(...).metadata.currency`
  (`USD`→$, `GBP`→£, `EUR`→€, `CAD`→C$). Clientes UK (Solar Reserve, Zola Zola) reportan en £.

### Marketplace → `mkp_id`
US=1 · GB/UK=2 · CA=4 · MX=5 · BR=6 · DE=7 · ES=8 · FR=9 · IT=10 · NL=16 · PL=19 · SE=20 · BE=21 ·
AE=15 · SA=23 · IE=24. Fallback: `list_my_accounts()`.

---

## Step 1: Resolve brand → config from Supabase

```sql
-- Resolve by brand, brand_name, OR alternative_names (e.g. "Solar Reserve" → Every Cloud,
-- "MyNextGen" → Hekaya). Matching only `brand` misses consumer-brand aliases.
SELECT brand, active, config FROM clients
WHERE active = true
  AND (
        lower(brand)                LIKE '%' || lower(:requested_brand) || '%'
     OR lower(config->>'brand_name') LIKE '%' || lower(:requested_brand) || '%'
     OR EXISTS (
          SELECT 1
          FROM jsonb_array_elements_text(coalesce(config->'alternative_names','[]'::jsonb)) alt
          WHERE lower(alt) LIKE '%' || lower(:requested_brand) || '%'
        )
  );
```
1 row → use it. 2+ (multi-marketplace) → one message per row. 0 → suggest `client-onboarding`.
Require `shurq_account_id`, `amazon_marketplace`, `slack_internal_channel_id`. Derivá
`account_id = int(shurq_account_id)` y `mkp_id` desde `amazon_marketplace`.

> **Compat:** `adlabs_team_id`/`adlabs_profile_id` pueden seguir en el config — este skill los ignora.
> Si `shurq_account_id` falta → flag + skip brand.

---

## Step 2: Pull + roll up performance data (same engine as weekly-report V4.2)

> ⚠️ **MANDATORY — do NOT shortcut this step. This is a live single-call skill; there is NO
> attached XLSX.** Never wait for, expect, or fall back to "the file you attach" — that was V2/V4.
> **You MUST pull the full trailing ~52-week window** via the daily series and roll up **every** week.
> A short pull silently breaks every ranking and every "improving trend". El pull completo es el mismo
> costo (3 llamadas). Si SHURQ devuelve menos semanas para una métrica, está bien — el ranking
> data-aware lo maneja — pero siempre REQUEST la ventana completa.

Reporting week = last complete Sun–Sat week as of the run day (Wins runs Mondays → the week that
ended the prior Saturday). Pull a trailing ~53-week window.

### 2a. Date window (Sun–Sat) — computalo vos (el sandbox SHURQ no tiene date.today())
```
today            = <hoy ART>
days_since_sunday = (weekday(today) + 1) % 7
this_sunday      = today - days_since_sunday
rw_end           = this_sunday - 1 día              # Saturday = fin de la última semana COMPLETA
rw_start         = rw_end - 6 días                  # Sunday
pw_start         = rw_start - 7 días ; pw_end = pw_start + 6 días
date_from        = rw_start - 52 semanas            # ventana ~53 semanas para rankings
date_to          = rw_end
```

### 2b. Pull the daily series (THREE SHURQ tools — igual que weekly-report)
```python
acc = <account_id>; mkp = <mkp_id>
ads = await call_tool("get_ads_daily_trend",
        {"account_id": acc, "marketplace_id": mkp, "start_date": date_from, "end_date": date_to})
st  = await call_tool("get_sales_traffic",       # usá SOLO revenue + orders; su `sessions` está roto (0)
        {"account_id": acc, "marketplace_id": mkp, "start_date": date_from, "end_date": date_to})
sess = await call_tool("custom_metric_calculator",   # sessions por día (fuente que funciona)
        {"account_id": acc, "numerator": "orders", "denominator": "sessions",
         "marketplace_id": mkp, "start_date": date_from, "end_date": date_to})
```
- Los tres devuelven `{"data":[{fila por día}], "metadata":{...}, "summary":{...}}`.
- **Sessions:** `sess.data[].sessions` (validado: Natchiketa semana Aug 30–Sep 5 = 13,936 sessions).
  **Nunca uses `st.data[].sessions`** (bug SHURQ = 0).
- **⚠️ Cap de ventana:** si un tool limita el rango largo, paginá en chunks de ~90 días por
  `start_date`/`end_date` y concatená los `data[]`. Nunca acortes el REQUEST a propósito.

### 2c. Roll up daily → weekly (Sun–Sat) — VALIDATED MAPPING (idéntico a weekly-report)
Agrupá cada fila por su `week_start` (domingo de esa fecha), sumá por semana:

| Weekly field | Fuente | Cómo |
|---|---|---|
| `spend` | ads | `sum(cost)` |
| `ppc_sales` (sales) | ads | `sum(sales)` (ad-attributed) |
| `ppc_orders` (orders) | ads | `sum(orders)` |
| `clicks` / `impressions` | ads | `sum(clicks)` / `sum(impressions)` |
| `total_sales` (seller_sales) | sales_traffic | `sum(revenue)` |
| `total_orders` (seller_orders) | sales_traffic | `sum(orders)` |
| `total_sessions` | **custom_metric_calculator** | `sum(sess.data[].sessions)` por semana |

```python
def kpis(r):
    spend  = r['spend'] or 0;  ppc = r['ppc_sales'] or 0;  tot = r['total_sales'] or 0
    orders = r['total_orders'] or 0;  ppc_orders = r['ppc_orders'] or 0
    clicks = r['clicks'] or 0;  impressions = r['impressions'] or 0
    total_sessions = r['total_sessions']    # de custom_metric_calculator, no proxy
    # DATA-PRESENCE FLAGS (anti-"rank de 53"): una semana solo cuenta para una métrica si el dato existe.
    has_ppc = (spend > 0) or (clicks > 0) or (impressions > 0)
    has_org = tot > 0
    ts = total_sessions if (has_ppc and total_sessions) else None
    return {
      # PPC / mixtas → None si no hay datos pagos esa semana
      'spend':      spend if has_ppc else None,
      'ppc_sales':  ppc   if has_ppc else None,
      'acos':   (spend/ppc)         if (has_ppc and ppc)         else None,
      'roas':   (ppc/spend)         if (has_ppc and spend)       else None,
      'ppc_cvr':(ppc_orders/clicks) if (has_ppc and clicks)      else None,   # "PPC CVR"
      'ctr':    (clicks/impressions)if (has_ppc and impressions) else None,
      'tacos':  (spend/tot)         if (has_ppc and tot)         else None,
      'total_sessions': ts,
      'total_cvr': (orders/ts) if (has_ppc and ts) else None,                 # "CVR" (Total CVR)
      # Orgánicas / marketplace → None si no hay datos orgánicos esa semana
      'total_sales':   tot               if has_org else None,
      'organic_sales': max(tot - ppc, 0) if has_org else None,
      'total_orders':  orders            if has_org else None,
      'total_roas':    (tot/spend) if (has_ppc and has_org and spend) else None,
    }

# weekly_data[week_start] = kpis(fila semanal). all_weeks = sorted(weekly_data)
# rankings NO ven futuro — solo semanas <= reporting week:
hist = [w for w in all_weeks if w <= rw_key]
rw = weekly_data.get(rw_key) or (weekly_data[hist[-1]] if hist else {})
pw = weekly_data.get(pw_key, {})
```

> **Fuente Sessions/Total CVR (resuelto — igual que weekly-report V4.2):** `custom_metric_calculator`
> (`orders/sessions`) trae `sessions` por día en toda la ventana. `get_sales_traffic.sessions` está roto
> (0). Fallback defensivo: si `custom_metric_calculator` diera `NO_DATA` para la cuenta → no rankees CVR/
> sessions y avisá en el hand-off interno; con el snapshot actual casi nunca pasa.

---

## Step 3: Data-aware ranking windows (identical to weekly-report — no "account history")

`kpis()` pone una métrica en `None` en semanas sin dato, así que el ranking dropea `None` y el `total`
que citás es **el número de semanas con dato real** para esa métrica, nunca la ventana pulleada (~52/53).

```python
def rank(metric, lower, window_start=None):
    weeks = [w for w in hist
             if weekly_data[w].get(metric) is not None
             and (window_start is None or w >= window_start)]
    if len(weeks) < 2 or weekly_data.get(rw_key, {}).get(metric) is None:
        return None
    s = sorted(weeks, key=lambda w: weekly_data[w][metric], reverse=not lower)
    return {'rank': s.index(rw_key) + 1, 'total': len(weeks)}   # 'total' = semanas CON dato
```

Metric → data window:
| Family | Members | Window |
|---|---|---|
| PPC | acos, roas, ppc_sales, ppc_cvr, ctr, spend | weeks ≥ `ppc_data_start` |
| Mixed (PPC-dependent) | tacos, total_sessions, total_cvr | weeks ≥ `ppc_data_start` |
| Organic / marketplace | total_sales, organic_sales, total_orders | weeks ≥ `organic_data_start` |

Direction: lower-is-better = acos, tacos; higher-is-better = el resto.

**Relationship frames** (bounded por la data window):
- **Data window** → *"rank 3 of the last 11 weeks"* (conteo real).
- **Since you started with Sophie** → weeks ≥ `onboarding_date`.
- **Since our team took over** → weeks ≥ `team_took_over_date` (directos: null → = `onboarding_date`).

**Guards (client-facing — estrictos):**
- **Wording exacto — no mezclar.** `onboarding_date` → **"since you started with Sophie"** (YOU =
  cliente); `team_took_over_date` → **"since our team took over"** (OUR = POD). Nunca híbridos.
- **Nunca "in account history" / "all-time".** Siempre conteo nominal sobre ventana nombrada.
- **Anti-overclaim:** métrica con **< 6 semanas** de dato → sin superlativo (*"in the N weeks of paid
  data so far"* u omitir). Nunca un rank-1-of-3 como record.
- **Nunca cruces familias:** "best week" PPC scopeado a la ventana PPC; orgánico a la orgánica.

---

## Step 4: Select what to highlight (wins / improvement / focus)

Computá por KPI: rank + count en su data window (`rank_pct = rank/total`), su WoW move, y un short
recent trend (últimas 3 semanas elegibles). Armá **3–5 highlights** across los tres tipos. La frase de
Nacho fija el modo; default **auto** (lead con wins, sumá improvements, opcional un focus).

**1. Wins** — `rank_pct <= 0.34` en la ventana de la métrica (y ≥ 6 semanas de dato). Dedupe pares
   redundantes (no ROAS & Total ROAS juntos; no PPC Sales & Total Sales salvo que la historia lo pida).
   Lead con el más fuerte (menor rank_pct).

**2. Improvement** — métrica con tendencia reciente positiva aunque no esté top: mejoró WoW Y/O
   monótona en las últimas 3 semanas elegibles. Frame como momentum:
   *"ACOS has improved three weeks running (44% → 39% → 35%)."*

**3. Focus** — como mucho uno, solo si importa: métrica floja en su ventana o deteriorándose, en la que
   conviene concentrarse. Constructivo y específico, nunca alarmista. Omitir si todo está sano.

**Mode from Nacho's phrasing:**
- "wins / highlights / resaltá lo bueno" → wins-first, focus omitido salvo que sea notable.
- "mejora / cómo venimos / progreso" → lead con improvement trend(s).
- "en qué enfocarnos / qué mejorar" → lead con el focus, igual abrí con un win real.
- unspecified → auto.

Si **nada califica como win o improvement**, no inventes uno: armá el mensaje alrededor del focus, o
decile a Nacho que no hay win claro esta semana.

---

## Step 5: Write the message (client-facing, Slack)

Slack-ready, `*bold*` para metric+value. Greeting de `slack_names` (fallback `owners`); single owner → `@[Name]`.
Language per `report_language` ("en" default; "es" → full Spanish).

**Writing style — que se lea como una persona del equipo, no una IA:**
- **Segunda persona ("you"/"your").** El mensaje es PARA los owners; el único nombre es el saludo.
- **Nunca em dash `—`.** Usá punto, coma, dos puntos o paréntesis.
- **Nunca tilde `~`** para aproximar. "about"/"around", o el número pelado.
- Variá cómo abren las oraciones; evitá la cadencia repetitiva "clause — clause".

```
@[SlackName]

[1 framing sentence matched to the mode: celebratory, progress, or focus.]

• *[Metric] [verb] at [value]*, [data-aware ranking or trend context]. [brief spin.]
• *[Metric] …*, …
• [3 to 5 bullets total, mixing wins / improvement / at most one focus]

[1–2 closing sentences: account health + forward-looking, tone matched.]
```

**Verbs:** sales → "reached / came in at / closed at"; orders → "reached / hit"; ACOS/TACOS/CVR/CTR
→ "came in at / held at / landed at"; ROAS → "closed at / came in at".

**Spin bank:** Organic → "organic momentum is building"; Total Sales → "the account is holding at a
healthy level"; CVR (Total) → "shoppers are converting well"; PPC CVR → "paid traffic is converting
efficiently"; ROAS → "every ad dollar is working"; Orders → "demand stayed strong"; ACOS/TACOS
improving → "efficiency is trending the right way".

**Multi-marketplace:** subtle marketplace mention en el opener. **No dashboard link required**
(Wins es un touchpoint liviano); incluilo solo si `dashboard_url` está seteado y el mensaje lo amerita.

---

## Step 6: Send to the internal Slack channel

**ALWAYS post the Wins message — no hay chequeo de "ya posteado".** No escanees el canal para saltear.
Un **Weekly Report es otro mensaje** (otro skill); ver un Report o un Wins anterior en el canal es
esperable y nunca es razón para saltear. Las únicas razones para saltear una marca son config faltante /
sin data.

Enviá con **`slack_send_message`** directo a `slack_internal_channel_id` — el canal **interno** del
cliente, nunca uno client-facing. Nacho lo revisa y lo forwardea. Send directo, **no**
`slack_send_message_draft` (un draft puede fallar si alguien está componiendo; el post interno es
seguro). Sin canal → output inline. Multi-marketplace → un mensaje por marketplace; decile a Nacho
cuántos y dónde.

---

## Edge cases

| Situation | Behavior |
|---|---|
| Brand not in Supabase | Suggest `client-onboarding`; don't fabricate |
| Missing `shurq_account_id` | Flag + skip (problema de config real) |
| Missing `amazon_marketplace` | Resolvé `mkp_id` vía `list_my_accounts`; si sigue ambiguo, preguntá |
| Missing `slack_internal_channel_id` | Output inline, skip send |
| Newly onboarded — short PPC history | Rank PPC metrics solo sobre `ppc_data_start`+; cite real counts; no "account history" |
| PPC metric < 6 weeks of data | No superlative; "in the N weeks of paid data so far" o omitir |
| Transferred client (`team_took_over_date` > `onboarding_date`) | Ambos frames válidos & distintos |
| `team_took_over_date` null | Directo → tratar como `= onboarding_date` |
| Sessions/Total CVR | Fuente = `custom_metric_calculator`; solo si da NO_DATA → no rankear CVR/sessions + flag interno |
| SHURQ limita la ventana larga | Paginar en chunks de ~90 días por start/end_date y concatenar `data[]` |
| SHURQ tool error transitorio | Reintentar 1 vez; si sigue, reportar el error real y skip esa marca |
| No win or improvement qualifies | Armar alrededor del focus, o avisar a Nacho — nunca fabricar un win |
| < 2 weeks of history | Skip rankings; nota mínima + avisar a Nacho |
| `report_language: "es"` | Full Spanish, misma estructura |
| Notion changelog available | Contexto liviano opcional; nunca fabricar causalidad |

---

## Data-source quick reference (SHURQ edition)

| Need | Source | Key call |
|---|---|---|
| Client config | Supabase `clients` | `execute_sql` (project awhiobrcgghyiycxukjm) |
| Weekly PPC KPIs | SHURQ | `get_ads_daily_trend(account_id, marketplace_id, start_date, end_date)` → rollup |
| Total sales / orders | SHURQ | `get_sales_traffic(...)` → rollup (usá `revenue` + `orders`; NO `sessions`) |
| **Sessions / Total CVR** | SHURQ | `custom_metric_calculator(account_id, numerator="orders", denominator="sessions", ...)` → `sum(sessions)` por semana |
| Currency + totals sanity | SHURQ | `get_orders_summary(...).metadata.currency` |
| Account/mkp resolution | SHURQ | `list_my_accounts()` |
| Output | Slack | `slack_send_message` to the internal channel |

> **Migración AdLabs → SHURQ (referencia):** `get_entity_data(profile)` + `query(profile_id)` +
> `get_entity_data(timeline)` + `download_data` + pandas rollup → `get_ads_daily_trend` +
> `get_sales_traffic` + `custom_metric_calculator` + rollup en plain Python. `adlabs_team_id`/
> `adlabs_profile_id` → `shurq_account_id` + `mkp_id`. Sin `start_chat_session`/`read_resource`/references.
> **Total CVR:** `total_sessions` ahora viene de `custom_metric_calculator` (sessions reales), no del
> proxy `seller_org_traffic + clicks` de V5 — alineado con weekly-report V4.2.
