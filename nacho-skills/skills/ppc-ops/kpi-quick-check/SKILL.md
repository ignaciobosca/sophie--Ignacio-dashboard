---
name: kpi-quick-check
description: >
  Chequeo rápido de KPIs — snapshot AL MOMENTO (hoy en tiempo real) de Spend,
  PPC Sales, Total Sales y ACOS para TODOS los clientes, en un solo listado, vía
  Shurq `realtime_ad_metrics` (penny-perfect, idéntico al dashboard). Por defecto
  el pull es liviano (esas 4); ON-DEMAND suma Impresiones y Clicks de hoy para
  detectar si una campaña no está corriendo bien. NO es el daily check (eso es MTD
  con targets y va a Slack) — es un pulso instantáneo impreso en el chat.
  Triggerear cuando Nacho diga "chequeo rápido", "quick check", "kpi check", "kpis
  rápido", "cómo venimos/vamos hoy", "pulso de las cuentas", "snapshot de kpis",
  "spend y acos ahora", "listado de clientes con sus kpis", "how are the accounts
  right now". Activar el add-on de Impresiones/Clicks si pide "con impresiones y
  clicks", "chequeá la corrida", "están corriendo bien las campañas", "hay algún
  error en la corrida". Si menciona MTD, targets, budget pacing, o Slack, es el
  skill `daily-check`, no este.
---

# KPI Quick Check

Pulso instantáneo de la cartera. Por defecto trae, para **todos los clientes
activos**, del **día de hoy hasta el momento exacto** en que se pide:

- **Spend** — inversión en ads hoy
- **PPC Sales** — ventas atribuidas a ads (ad sales)
- **Total Sales** — ventas totales del negocio (incluye orgánico)
- **ACOS** — Spend / PPC Sales

Y, **solo si Nacho lo pide** (add-on on-demand), suma dos columnas de diagnóstico
de corrida:

- **Impresiones** — cuántas veces se sirvieron los ads hoy
- **Clicks** — cuántos clicks hoy

El default es liviano y rápido a propósito. Las impresiones/clicks salen de otra
tool más lenta (hay que traerlas en tandas), así que se activan bajo pedido, para
responder "¿está corriendo bien cada cuenta?" — no para performance fina. Cero
configs de Drive, cero AdLabs, cero Slack. Un listado impreso en el chat.

**Cuándo activar el add-on:** cuando el pedido incluya impresiones/clicks o hable
de la corrida de las campañas ("chequeá la corrida", "están corriendo bien",
"hay algún error", "con impresiones y clicks"). Si no, no lo corras.

---

## Fuentes de Shurq

**Plata (siempre) → `realtime_ad_metrics`.** Fuente autorizada para "cuánto llevo
hoy": mismo código que el dashboard/`/stream`, así que Spend/PPC Sales/Total
Sales/ACOS son idénticos a la web. La **ventana por defecto ya es "today
(real-time)"** — no pasar `days`. Sin `marketplace_id`, **agrega todos los
marketplaces del cliente y normaliza a USD**. ACOS = spend/ad_sales; Total Sales =
ingreso real de órdenes.

**Funnel (on-demand) → `live_campaign_dashboard`.** Devuelve, por campaña, las
impresiones/clicks/cost de hoy desde el stream. Se suman a nivel cuenta. **Solo
tomamos Impresiones y Clicks** — su `cost` es stream crudo (sobreestima), la plata
SIEMPRE sale de `realtime_ad_metrics`.

**Por qué no otras para el funnel:** `get_today_performance` da lo mismo pero es
**mucho más lenta** (revienta el timeout de 60s del `execute` con pocas cuentas).
`portfolio_performance_matrix`/`multi_account_summary` traen todo en una llamada
pero con `days=1` devuelven **AYER** (la Reports API finalizada no tiene "hoy" →
`NO_DATA`). Por eso el funnel de hoy sale de `live_campaign_dashboard` por cuenta,
en chunks.

Nota del sandbox: no tiene reloj (`date.today()` no existe). Nunca calcules la
fecha dentro del `execute`; las tools resuelven "hoy" server-side. El server de
Shurq puede aparecer con prefijo hasheado (p. ej. `mcp__6f7cb8ab-…__execute`) —
usá el `execute` del conector Shurq que esté conectado.

---

## Flujo por defecto (plata) — SIEMPRE

### Paso 1 — Traer clientes + KPIs de plata

```python
import json

def parse_money(name, aid, r):
    p = json.loads(r["result"])
    if "data" not in p:           # payload de throttle/error → sin "data"
        return None
    d = p["data"]
    return {"account_id": aid, "name": name,
            "spend": d.get("ad_spend"), "ppc_sales": d.get("ad_sales"),
            "total_sales": d.get("total_sales"), "acos_pct": d.get("acos_pct"),
            "tacos_pct": d.get("tacos_pct"), "roas": d.get("roas")}

accts = json.loads((await call_tool("list_my_accounts", {}))["result"])["accounts"]
active = [a for a in accts if a.get("status") == "active"]

rows, failed = [], []
for a in active:
    m = parse_money(a["seller_name"], a["account_id"], await call_tool("realtime_ad_metrics", {"account_id": a["account_id"]}))
    (rows if m else failed).append(m if m else {"account_id": a["account_id"], "name": a["seller_name"]})

return {"rows": rows, "failed": failed, "n_active": len(active)}
```

### Paso 2 — Reintentar SOLO las que fallaron (si hay)

~19 `realtime_ad_metrics` seguidas a veces gatillan un rate-limit transitorio
(vuelven sin `data`). Se recupera entre round-trips, así que si `failed` no está
vacío, corré este **segundo** `execute` con esas cuentas. Repetí una vez más si
queda alguna.

```python
import json
# failed = [ {"account_id":.., "name":".."}, ... ]  ← de Paso 1
recovered, still_failed = [], []
for f in failed:
    p = json.loads((await call_tool("realtime_ad_metrics", {"account_id": f["account_id"]}))["result"])
    if "data" in p:
        d = p["data"]
        recovered.append({"account_id": f["account_id"], "name": f["name"],
            "spend": d.get("ad_spend"), "ppc_sales": d.get("ad_sales"),
            "total_sales": d.get("total_sales"), "acos_pct": d.get("acos_pct"),
            "tacos_pct": d.get("tacos_pct"), "roas": d.get("roas")})
    else:
        still_failed.append(f)
return {"recovered": recovered, "still_failed": still_failed}
```

Mergeá `rows + recovered`. Las que sigan en `still_failed` van con `—` y nota
`⚠️ Sin datos`. **Nunca inventes un número ni rellenes hoy con data de ayer.**

### Paso 3 — Ordenar, totalizar e imprimir (4 columnas)

```python
rows.sort(key=lambda r: (r.get("total_sales") or 0), reverse=True)  # mayor Total Sales primero
t_spend = round(sum((r.get("spend") or 0) for r in rows), 2)
t_ppc   = round(sum((r.get("ppc_sales") or 0) for r in rows), 2)
t_total = round(sum((r.get("total_sales") or 0) for r in rows), 2)
port_acos = round(t_spend / t_ppc * 100) if t_ppc else None
```

```
📊 *KPI Quick Check — {fecha} · {hora} ART*  ·  hoy en tiempo real (Shurq)

| Cliente | Spend | PPC Sales | Total Sales | ACOS |
|---|---|---|---|---|
| {name} | ${spend:,.2f} | ${ppc:,.2f} | ${total:,.2f} | {acos} |
| ... | | | | |
| *TOTAL ({n})* | *${spend:,.2f}* | *${ppc:,.2f}* | *${total:,.2f}* | *{acos}* |

_USD (multi-marketplace normalizado por Shurq). ACOS = Spend / PPC Sales._
```

Reglas: **ACOS con PPC Sales = 0 → `—`, no `0%`** (`acos = f"{r['acos_pct']:.0f}%" if r["ppc_sales"] else "—"`).
Fecha/hora del reloj del **runtime**, `America/Argentina/Buenos_Aires`. Plata a 2
decimales, ACOS entero. Debajo, `⚠️ Sin datos: {clientes}` si hubo. Corto: tabla +
total + línea de flags. Nada de análisis salvo que lo pidan.

---

## Add-on ON-DEMAND — Impresiones y Clicks (chequeo de corrida)

Corré esto **solo si Nacho lo pidió** (ver "Cuándo activar el add-on"). Se agrega
DESPUÉS de tener la plata (Pasos 1–2). Suma dos columnas + una de flag.

### Paso A — Funnel de hoy en CHUNKS

`live_campaign_dashboard` es por cuenta. Probado: **10 cuentas por `execute` entra
bajo 60s; 19 se pasa**. Procesá en **chunks de ≤10 `account_id`** (para ~19 son 2
`execute`). Sumá impresiones/clicks de las campañas de cada cuenta.

```python
import json
chunk = [465, 745, 747, 842, ...]   # ≤10 account_id; repetí para el resto
funnel, no_data, fail = {}, [], []
for aid in chunk:
    p = json.loads((await call_tool("live_campaign_dashboard", {"account_id": aid}))["result"])
    if "data" in p:
        camps = p["data"] or []
        funnel[aid] = {"impr": int(sum(c.get("impressions") or 0 for c in camps)),
                       "clicks": int(sum(c.get("clicks") or 0 for c in camps))}
    elif p.get("error", {}).get("code") == "NO_DATA":
        no_data.append(aid)          # sin stream hoy → impr/clicks = 0 (señal de "no sirve")
    else:
        fail.append(aid)             # transitorio → reintentar en otro execute; si no, "—"
return {"funnel": funnel, "no_data": no_data, "fail": fail}
```

Funnel = **best-effort, nunca bloquea la plata**. `NO_DATA` → Impr/Clicks `0` +
flag ⚪. Error transitorio → reintentar esa cuenta en otro `execute`; si sigue →
`—`. La tool agrega los marketplaces de la cuenta, consistente con la plata.

### Paso B — Merge, totales y tabla de 6 columnas + flag

```python
fmap = {**funnel}   # de todos los chunks
for r in rows:
    f = fmap.get(r["account_id"])
    r["impr"]   = f["impr"]   if f else (0 if r["account_id"] in no_data else None)
    r["clicks"] = f["clicks"] if f else (0 if r["account_id"] in no_data else None)
t_impr   = int(sum((r.get("impr") or 0) for r in rows))
t_clicks = int(sum((r.get("clicks") or 0) for r in rows))
```

```
📊 *KPI Quick Check — {fecha} · {hora} ART*  ·  hoy en tiempo real (Shurq)

| Cliente | Spend | PPC Sales | Total Sales | ACOS | Impr | Clicks | |
|---|---|---|---|---|---|---|---|
| {name} | ${spend:,.2f} | ${ppc:,.2f} | ${total:,.2f} | {acos} | {impr:,} | {clicks:,} | {flag} |
| ... | | | | | | | |
| *TOTAL ({n})* | *${spend:,.2f}* | *${ppc:,.2f}* | *${total:,.2f}* | *{acos}* | *{impr:,}* | *{clicks:,}* | |

_USD normalizado por Shurq. ACOS = Spend / PPC Sales. Impr/Clicks = hoy en vivo (stream).
🔴/⚪/🟡 = chequear corrida._
```

Flag de corrida (última columna), por fila:

- `spend > 0` y `impr == 0` → 🔴 (spend sin impresiones — inconsistencia/tracking).
- `impr == 0` (incl. `NO_DATA`) → ⚪ (no está sirviendo hoy — pausada / sin budget / error).
- `impr > 0` y `clicks == 0` → 🟡 (sirve sin clicks — CTR/relevancia).
- si no, celda vacía.

Impr/Clicks con separador de miles, sin decimales; `None` → `—`. Debajo, resumen
de flags si hubo (ej. `⚪ Sin servir hoy: House of Thalen US`).

---

## Variantes que puede pedir Nacho

- **Un solo cliente** ("kpi rápido de Happy Fox") → filtrá `accts` por
  `seller_name` (parcial, case-insensitive); si hay varias, listalas y preguntá.
  Con una cuenta, el funnel es 1 llamada (no hace falta chunk).
- **Por marketplace** ("solo US") → `realtime_ad_metrics` con `marketplace_id`
  (1=US, 4=CA, 5=MX, 6=BR, 2=UK, 7=DE, 8=ES, 9=FR, 10=IT, …).
- **Qué campaña se rompió** → `live_campaign_dashboard` ya trae el desglose por
  campaña; mostrá las campañas con `impressions == 0` (o `cost > 0` sin impresiones)
  de la cuenta señalada.
- **Ordenar por Spend / Impresiones** → cambiá la clave del `sort`.
- **TACOS/ROAS** → ya vienen en cada `row` (`tacos_pct`, `roas`).

---

## Guardrails

- **La plata SIEMPRE es `realtime_ad_metrics`.** El `cost` de
  `live_campaign_dashboard` sobreestima — nunca como Spend. De esa tool solo salen
  Impresiones y Clicks, y solo cuando el add-on está activado.
- **No corras el add-on si no lo pidieron.** El default es 4 columnas, rápido.
- **Nunca inventes ni arrastres números** de una corrida previa; si algo falla es
  `—` + nota. Nunca rellenes hoy con data de ayer (`days=1` = ayer).
- **No es el daily check.** MTD / vs mes anterior / targets / pacing / Slack → ese
  es `daily-check`. Ofrecé cambiar de skill.
- **Loops dentro de `execute`; funnel en chunks de ≤10** (19 de una se pasa de 60s).
- **Sintaxis del sandbox:** Python restringido, no JS. `None/True/False`, sin
  `Date.now()`, sin pandas/numpy. `call_tool` async → siempre `await`. El
  `["result"]` de cada tool es string JSON → `json.loads`.
