---
name: kpi-quick-check
description: >
  Chequeo rápido de KPIs — snapshot AL MOMENTO (hoy en tiempo real) de Spend,
  PPC Sales, Total Sales y ACOS para TODOS los clientes, en un solo listado.
  Usa el conector Shurq (tool `realtime_ad_metrics`), los mismos números
  penny-perfect que muestra el dashboard de Shurq. NO es el daily check (eso es
  MTD con targets y va a Slack) — esto es un pulso instantáneo, liviano, que se
  imprime en el chat.
  Triggerear SIEMPRE que Nacho diga "chequeo rápido", "quick check", "kpi check",
  "kpis rápido", "cómo venimos hoy", "cómo vamos hoy", "pulso de las cuentas",
  "snapshot de kpis", "spend y acos ahora", "spend / ppc / total sales / acos del
  momento", "listado de clientes con sus kpis", "how are the accounts right now",
  "quick kpi snapshot", o cualquier pedido de ver Spend / PPC Sales / Total Sales /
  ACOS de todos los clientes en este instante. Si el pedido menciona MTD, targets,
  budget pacing, o mandar a Slack, ese es el skill `daily-check`, no este.
---

# KPI Quick Check

Pulso instantáneo de la cartera. En una sola pasada trae, para **todos los
clientes activos**, cuatro KPIs del **día de hoy hasta el momento exacto** en que
se pide:

- **Spend** — inversión en ads hoy
- **PPC Sales** — ventas atribuidas a ads (ad sales)
- **Total Sales** — ventas totales del negocio (incluye orgánico)
- **ACOS** — Spend / PPC Sales

El objetivo es velocidad y confianza en el número: cero configs de Drive, cero
AdLabs, cero Slack. Un solo listado impreso en el chat, listo en segundos.

---

## Por qué Shurq `realtime_ad_metrics` y nada más

`realtime_ad_metrics` es la **única fuente autorizada** para "cuánto llevo hoy".
Corre el mismo código que el dashboard y el /stream de Shurq, así que el número
que imprimís acá es idéntico al que Nacho ve en la web:

- Días finalizados: penny-perfect desde la Amazon Reports API (ClickHouse).
- **Hoy (tiempo real):** `max(finalizado, live-stream × ratio de limpieza de 8
  días)` por tipo de ad — o sea la lectura más fresca sin inflar el spend como
  hace el stream crudo.
- **Total Sales** = ingreso real de órdenes (denominador de TACOS), no solo lo
  atribuido a ads.
- **ACOS** = ad spend / ad sales · **TACOS** = ad spend / total sales.

Detalle clave que ahorra trabajo: **la ventana por defecto ya es "today
(real-time)"**. No hace falta pasar `days`, y de hecho el sandbox de Shurq no
tiene reloj (no hay `date.today()`), así que nunca calcules la fecha vos —
dejá que la tool resuelva "hoy" del lado del servidor.

No uses `get_ads_summary`, P&L, ni las tools de stream por keyword/hora para este
chequeo: son más lentas o no cuadran con el dashboard.

---

## Cómo se corre (una pasada + un reintento de las que fallen)

### Paso 1 — Traer los clientes y sus KPIs

Corré este bloque en **`mcp__SHURQ_-_NEW__execute`** tal cual. Lista las cuentas
con `list_my_accounts` y, para cada activa, pide `realtime_ad_metrics` sin `days`
(ventana = hoy en tiempo real). Sin `marketplace_id`, la tool **agrega todos los
marketplaces del cliente y normaliza a USD**, que es justo lo que querés para un
listado de cartera.

```python
import json

def parse_row(name, aid, r):
    p = json.loads(r["result"])
    if "data" not in p:           # payload de throttle/error → sin "data"
        return None
    d = p["data"]
    return {
        "account_id": aid, "name": name,
        "spend": d.get("ad_spend"), "ppc_sales": d.get("ad_sales"),
        "total_sales": d.get("total_sales"), "acos_pct": d.get("acos_pct"),
        "tacos_pct": d.get("tacos_pct"), "roas": d.get("roas"),
        "mkps": d.get("marketplaces"), "window": d.get("window"),
    }

accts = json.loads((await call_tool("list_my_accounts", {}))["result"])["accounts"]
active = [a for a in accts if a.get("status") == "active"]

rows, failed = [], []
for a in active:
    row = parse_row(a["seller_name"], a["account_id"], await call_tool("realtime_ad_metrics", {"account_id": a["account_id"]}))
    (rows if row else failed).append(row if row else {"account_id": a["account_id"], "name": a["seller_name"]})

return {"rows": rows, "failed": failed, "n_active": len(active)}
```

### Paso 2 — Reintentar SOLO las que fallaron (si hay)

Disparar 19 llamadas seguidas puede gatillar un rate-limit transitorio de Shurq
(la cuenta vuelve como payload sin `data`). Se recupera solo entre round-trips,
así que si `failed` no está vacío, corré este **segundo** bloque de `execute` con
la lista de fallidas. El hecho de ser una llamada aparte ya da el espaciado que
destraba el throttle. Repetí una vez más si todavía queda alguna.

```python
import json
# failed_ids = [ {"account_id":..,"name":".."}, ... ]  ← pegá acá las de Paso 1
recovered, still_failed = [], []
for f in failed_ids:
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

Mergeá `rows + recovered`. Las que sigan en `still_failed` tras un par de
reintentos van en el listado con `—` y una nota `⚠️ Sin datos`. **Nunca inventes
un número, y nunca rellenes con data de ayer** (`multi_account_summary` /
`portfolio_performance_matrix` con `days=1` devuelven AYER, no hoy — mezclar
ventanas rompe la promesa de "al momento").

### Paso 3 — Ordenar y totalizar (en el runtime, no en Shurq)

```python
rows.sort(key=lambda r: (r.get("total_sales") or 0), reverse=True)  # mayor Total Sales primero
spend = round(sum((r.get("spend") or 0) for r in rows), 2)
ppc   = round(sum((r.get("ppc_sales") or 0) for r in rows), 2)
total = round(sum((r.get("total_sales") or 0) for r in rows), 2)
port_acos = round(spend / ppc * 100) if ppc else None   # ACOS cartera = Spend / PPC Sales
```

### Paso 2 — Imprimir el listado en el chat

Renderizá una tabla markdown con una fila por cliente + una fila de **TOTAL
cartera** al final. Formato exacto:

```
📊 *KPI Quick Check — {fecha} · {hora} ART*  ·  hoy en tiempo real (Shurq)

| Cliente | Spend | PPC Sales | Total Sales | ACOS |
|---|---|---|---|---|
| {name} | ${spend:,.2f} | ${ppc_sales:,.2f} | ${total_sales:,.2f} | {acos} |
| ... | | | | |
| *TOTAL ({n})* | *${spend:,.2f}* | *${ppc_sales:,.2f}* | *${total_sales:,.2f}* | *{acos}* |

_Valores en USD (multi-marketplace normalizado por Shurq). ACOS = Spend / PPC Sales._
```

Reglas de formato que importan:

- **ACOS cuando PPC Sales = 0 → mostrá `—`, no `0%`.** Sin ventas atribuidas el
  ACOS no está definido; Shurq devuelve `acos_pct = 0` pero eso engaña. Regla:
  `acos = f"{r['acos_pct']:.0f}%" if r["ppc_sales"] else "—"`.
- Sacá la fecha/hora del reloj del **runtime** (no del sandbox de Shurq), en
  `America/Argentina/Buenos_Aires`. Es solo para el encabezado.
- Redondeá Spend/PPC/Total a 2 decimales; ACOS a entero (`35%`).
- Clientes con actividad `$0.00` en todo van al final (ya vienen ordenados así).

Mantené el mensaje corto: la tabla, el total, la nota de una línea, y si hubo
`errors`, una línea `⚠️ Sin datos: {clientes}`. Nada de análisis salvo que lo
pidan — esto es un pulso, no un reporte.

---

## Variantes que puede pedir Nacho

- **Un solo cliente** ("kpi rápido de Happy Fox") → filtrá `accts` por
  `seller_name` (match parcial, case-insensitive) y mostrá esa fila sola. Si hay
  varias coincidencias, listalas y preguntá cuál.
- **Por marketplace** ("desglosado por país" / "solo US") → volvé a llamar
  `realtime_ad_metrics` con `marketplace_id` (1=US, 4=CA, 5=MX, 6=BR, 2=UK,
  7=DE, 8=ES, 9=FR, 10=IT, …) y armá una fila por marketplace de ese cliente.
- **Ordenar por Spend** ("ordená por gasto") → cambiá la clave de `sort` a
  `spend`.
- **Sumar TACOS/ROAS** → ya vienen en cada `row` (`tacos_pct`, `roas`); agregá
  columnas si las pide.

---

## Guardrails

- **Nunca inventes ni arrastres números de una corrida previa.** Cada quick check
  es un pull nuevo; si una cuenta falla, es `—` + nota, no un valor estimado.
- **No es el daily check.** Si el pedido trae MTD, comparación vs mes anterior,
  targets de ACOS/TACOS, budget pacing o "mandalo a Slack", ese es `daily-check`.
  Ofrecé cambiar de skill en vez de forzar este.
- **El loop va DENTRO de `execute`.** No dispares 19 `call_tool` sueltos a nivel
  MCP; el for va dentro del bloque de Python restringido. Lo único que se corre en
  un `execute` aparte es la pasada de reintento de las fallidas (Paso 2).
- **Sintaxis del sandbox:** Python restringido, no JS. `None/True/False`, sin
  `Date.now()`, sin pandas/numpy. `call_tool` es async → siempre `await`. El
  `["result"]` que devuelve cada tool es un string JSON → `json.loads` sobre él.
