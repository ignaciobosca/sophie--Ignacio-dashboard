---
name: biweekly-bid-optimizer
description: >
  Bi-weekly (Tue/Fri) bid + placement optimizer feeder for the Sophie Master Dashboard, using SHURQ's
  NATIVE Bid Optimizer engine (preview_bid_changes — the /ad-manager reference engine, not a custom scorer).
  Per client: resolves config from Supabase, picks a 14/30-day window by click volume, maps a preset,
  previews bid + placement changes with +-15% guardrails, and upserts a proposal snapshot
  (tipo='optimizations', status='pending'). Writes NOTHING to Amazon. MODE=apply pushes only the rows Nacho
  approved in the dashboard (apply_bid_changes → confirm_action). SP only at launch. Trigger: scheduled
  Tue/Fri, or "corre el biweekly bid optimizer para [Brand]", "biweekly bid optimizer for [Brand]",
  "optimizacion de bids biweekly para [Brand]". Apply: "aplica los bids aprobados de [Brand]" /
  "push approved bids for [Brand]".
---

# Biweekly Bid & Placement Optimizer — Feeder (Master Dashboard)

**Versión:** V2.0 SHURQ (2026-09-12) — **migración AdLabs → SHURQ.** El motor nativo pasa de AdLabs
`optimizer(preview_optimization/apply_optimization)` al **Bid Optimizer nativo de SHURQ** (`preview_bid_changes`
= la misma engine del /ad-manager, `get_bid_preview_rows` para paginar, `apply_bid_changes`→`confirm_action`
para aplicar). Cambios clave:
1. **Config/cuenta:** `shurq_account_id` + `mkp_id` (ya no `adlabs_team_id`/`adlabs_profile_id`). Sin handshake/sesión.
2. **Feeder (Step 2-8):** clasificación por clicks vía `query_table("campaigns_daily")`; destino = `campaign_ids`
   de campañas SP ENABLED **sin Scavenger** (regla 11) pasados a `preview_bid_changes`; preview con
   `preset` (mapeado a SHURQ), `target_acos` (PERCENT), `max_increase_pct=15`/`max_decrease_pct=15`,
   `include_placements=true`, `exclude_dates`. Filas vía `get_bid_preview_rows` (filtros raise/cut/hold/segment).
3. **Redondeo de placements a múltiplo de 5 → SOLO display** en el snapshot: `apply_bid_changes` aplica los
   modifiers que computó SHURQ (no se puede inyectar un valor redondeado en el apply). El Step 6 se conserva
   para el número que muestra el dashboard, no para el write.
4. **MODE=apply (decisión de Nacho 2026-09-12 — Opción A):** re-preview con los mismos params (el `preview_id`
   de SHURQ **expira a los 30 min**) → `apply_bid_changes(preview_id, keyword_ids=<ids aprobados>)` →
   `confirm_action` (un batch, hasta 500 filas, respeta los write-guardrails del seller). **El apply usa el
   valor RECOMPUTADO del re-preview del día**, no el exacto del snapshot (cambia la vieja regla 7; mismo día
   ≈ el aprobado). Selección por los `id` de las filas aprobadas.
5. **MODE=audit / audit-apply: ELIMINADO** — eran resync de *optimization groups* de AdLabs, que no existen
   en SHURQ. El feeder ya optimiza sobre el ACOS de perfil vía `target_acos`, así que no hacen falta.

**Versión previa:** V1.5 (2026-09-08). Prototipo del tab Optimizations construido y probado contra las 705 filas
reales de DynamoMe (bulk approve + de-select por fila/grupo/visibles, filtros, copy). Fix de correctitud:
**identidad de fila = `(entity_id, bidding_entity)`** — los placements comparten `entity_id` entre slots
(37 filas / 25 ids), así que aprobación/exclusión/apply keyean por `id|be`. El botón "Copiar aprobados"
emite una línea `entity_id|bidding_entity` por fila.

**Versión:** V1.4 (2026-09-08). Fix de correctitud en el redondeo de placements (hallado en el test
DynamoMe): con modifiers chicos, redondear+clampear podía **invertir la dirección** del cambio de AdLabs.
`round_placement` ahora **nunca invierte** (si no hay step de 5% válido → deja `old`, sin cambio). Snapshot
schema `optimizations-v1` con lookup `campaigns[]` + filas compactas, validado escribiéndolo a Supabase
(DynamoMe, 705 filas full / mini live). El row schema y el bulk-approve del tab quedaron definidos.

**Versión:** V1.3 (2026-09-08). **Regla de oro nueva (Nacho):** las campañas con `scavenger` en el nombre
(case-insensitive) **NUNCA se optimizan** — se excluyen de la reference antes del preview (filtro
`CAMPAIGN_NAME NOT_LIKE "Scavenger"` + red case-insensitive vía `query`) y del pull de clasificación. Regla
11. Verificado en vivo (DynamoMe tenía 3 Scavenger; filtro las saca 28→25). Además: unidad del placement
modifier verificada (test DynamoMe) = %/100 (2.93=+293%), redondeo a múltiplo de 0.05, guardrail ±15%
relativo (Step 6).

**Versión:** V1.2 (2026-09-08). **Decisión de Nacho:** optimizar sobre el **ACOS de PERFIL**
(`cfg.acos_target` + `override_group_settings=true`), NO sobre los optimization groups. En consecuencia el
**audit (MODE=audit / audit-apply) pasa a OPCIONAL, NO prerequisito** — el feeder ignora los grupos. El
scan real 2026-09-08 mostró que la mayoría de los grupos son segmentación intencional (no basura stale), así
que un resync en bloque sería destructivo. Además: los ACOS/TACOS targets de las cuentas se sincronizaron en
Supabase (`config.acos_target`/`tacos_target`) para espejar los targets de perfil de AdLabs, con
`target_source` documentado.

**Historial:** V1.1 (2026-09-08) — sumó MODE=audit + MODE=audit-apply; shapes de `list_groups`/`create_group`/
`update_group` verificados contra `adlabs://docs/optimizer_actions`. · V1.0 (2026-09-08). Feeder de la familia Supabase. Propone **bids Y placement modifiers**
dos veces por semana (Tue/Fri) usando el **motor nativo de AdLabs** (`optimizer(preview_optimization)`),
no un scorer propio de Sophie. Escribe un snapshot de propuesta a `dashboard_snapshots`
(`tipo='optimizations'`) como `status:"pending"`. **No toca Amazon en el feeder** — el push lo hace
`MODE=apply` solo con los `entity_id` que Nacho aprobó en el tab Optimizations del Master Dashboard.
Diseño cerrado vía grill-me (2026-09-08). Ver `memory/dashboard_cloud_migration.md`.

> **🧪 Piloto.** Lee/escribe Supabase, corre headless en Routines de nube. En el arranque, **scope =
> cuentas piloto** (§Scheduling): Urban Veda (Ayurveda Wellness), Dr. Cohen's HEATABLE, DynamoMe.
> El compose del Master (tab Optimizations) es una pieza **separada** (no vive en este skill).

> **Motor = SHURQ Bid Optimizer** (`preview_bid_changes`), la misma engine que el seller ve en
> /ad-manager → Bid Optimizer preview. `preview_bid_changes` computa y **no escribe** (parkea el preview
> 30 min); `get_bid_preview_rows(preview_id)` pagina las filas; `apply_bid_changes(preview_id, keyword_ids)`
> encola el batch y **nada llega a Amazon hasta `confirm_action(action_id)`**. El feeder optimiza sobre el
> **ACOS de perfil** (`cfg.acos_target` → param `target_acos` en PERCENT). No hay optimization groups ni
> handshake de sesión.

**Respondé a Nacho en español.**

---

## Reglas de oro (no negociables)

1. **El feeder NO escribe a Amazon.** `preview_bid_changes` computa y parkea (no aplica nada). El único
   paso que escribe live es `apply_bid_changes(preview_id, keyword_ids)` + `confirm_action(action_id)` en
   `MODE=apply`, y solo con las filas que Nacho aprobó. Un run programado jamás aplica ni confirma.
2. **SP only** al arranque: el destino son campañas SP (api_type `sp`); el executor de `apply_bid_changes`
   es **SP-only** (filas de placement SB/SD quedan en `not_applied`). Nunca SB/SD/TV.
3. **Solo ENABLED:** solo campañas `campaign_status = ENABLED` entran al preview.
4. **Guardrails uniformes ±15%** por ciclo, iguales para todas las cuentas: bid ±15%, placement ±15%
   (sin override por cuenta). Se pasan como params al preview.
5. **Placement redondeado a múltiplo de 5 → SOLO DISPLAY** (Step 6): `apply_bid_changes` aplica el
   modifier que computó SHURQ, así que el redondeo es cosmético para el dashboard, NO el valor escrito.
   Los **bids** quedan como los da SHURQ (no se redondean).
6. **`preview_params` se guarda VERBATIM** en el snapshot. Es lo que `MODE=apply` re-corre después para
   regenerar un `preview_id` válido (el **`preview_id` de SHURQ expira a los 30 min**; los `id` de fila
   —keyword/target/campaign— son estables y no expiran).
7. **Apply = valor RECOMPUTADO del re-preview del día (Opción A, decisión de Nacho 2026-09-12).** En
   `MODE=apply` se re-corre el preview con los mismos params y se aplican, vía `apply_bid_changes`, las
   filas aprobadas con el valor **fresco** que computa SHURQ (no se puede inyectar el valor exacto del
   snapshot en `apply_bid_changes`). Mismo día ≈ el valor aprobado. El snapshot se usa para saber
   **cuáles** filas (`id`s) aprobó Nacho, no para forzar el número.
8. **Diagnóstico honesto config vs. SHURQ:** si `shurq_account_id` **está** en el config, un fallo de
   SHURQ (timeout, rate-limit, sync, preview expirado) es **transitorio** — reintentá 1 vez, después
   reportá el error real de SHURQ y seguí con los demás. NUNCA concluyas "cuenta no configurada" si el ID
   está. Solo si `shurq_account_id`/`amazon_marketplace`/`acos_target` faltan/null →
   `reason:"config incompleto: falta <campo>"` y saltás esa cuenta.
9. **Idempotencia:** el snapshot se indexa por `(cliente, 'optimizations', fecha=hoy ART)`. Re-runs del
   mismo día pisan la fila (no duplican). Tue y Fri son fechas distintas → dos filas por semana.
10. **Sin memoria de rechazados** (decisión #13): cada run es fresco. Una propuesta que Nacho rechazó
    puede reaparecer el próximo run si la data la sigue respaldando. No se persiste "rechazado".
11. **⛔ Campañas Scavenger NUNCA se optimizan (regla de Nacho — OBLIGATORIO).** Toda campaña cuyo
    `campaign_name` contenga `scavenger` (case-insensitive) se **excluye de la lista de `campaign_ids`
    que se pasa a `preview_bid_changes`** — el motor de SHURQ solo optimiza las campañas que le pasás, así
    que no genera propuestas de bid ni de placement para las Scavenger. Se excluyen también del pull de
    clasificación (Step 2). Las Scavenger son de descubrimiento intencional; sus bids/placements no se
    tocan. (Misma regla que la familia de negatives.)

---

## Constants

```
Fuente de datos:  Supabase (conector Supabase MCP, proyecto POD 66 - Organization) + SHURQ MCP.
  Config cliente:   public.clients (config JSONB) — brand_name, shurq_account_id, amazon_marketplace,
                    account_stage, acos_target, alternative_names, (opcional) acos_watchlist / flags.
                    (adlabs_team_id/adlabs_profile_id pueden seguir en el config; se IGNORAN.)
  Snapshot:         public.dashboard_snapshots, tipo='optimizations', UNA FILA POR RUN
                    (clave única cliente,tipo,fecha). El compose del Master toma las filas de los
                    últimos 7 días por cliente y reconstruye days[] (pending + applied history).
Timezone:  America/Argentina/Buenos_Aires (ART) — anclar SIEMPRE a ART, no a date.today()
           (las Routines corren en UTC).
SHURQ:     `preview_bid_changes` (motor nativo), `get_bid_preview_rows` (paginar filas),
           `apply_bid_changes` + `confirm_action` (aplicar), `list_campaigns` / `query_table("campaigns_daily")`
           (resolver campañas SP ENABLED sin Scavenger + clasificación por clicks). account_id = int(shurq_account_id),
           mkp_id del config. Sin sesión/handshake.
Slack/deploy: NADA en este skill (ni feeder ni apply). El aviso consolidado a #pod-66-team lo manda
           el master compose. El feeder es silencioso.
```

### ACOS watchlist (gobierna el mapeo de preset — decisión #7)
Watchlist de cuentas con ACOS volátil/escalando (a confirmar vigencia al build/run):
**Urban Veda, Dr. Cohen's HEATABLE, Masofta Inc, MyNextGen, Suji Health.**

> **Preferí data-driven:** si el config del cliente trae un flag explícito (`cfg.acos_watchlist == true`
> o `cfg.optimizer.preset` override), **ese manda**. Si no hay flag, caé a esta lista constante
> (match por `brand_name`/`alternative_names`, case-insensitive). Mantené la lista sincronizada con la
> memoria del equipo; idealmente migrala a un flag de config para no tocar el skill.

---

## Startup (siempre)

1. **Supabase:** leé el `config` del cliente (Step 1) → `shurq_account_id`, `amazon_marketplace`, `acos_target`, `account_stage`.
2. **SHURQ:** no requiere sesión ni handshake. (Opcional: `list_my_accounts()` para confirmar que la cuenta es alcanzable.)
   Las tools (`preview_bid_changes`, `get_bid_preview_rows`, `apply_bid_changes`, `confirm_action`, `list_campaigns`,
   `query_table`) se llaman directo.

---

## MODE = run  (default — el feeder, un cliente)

### Step 1 — Resolver cliente + config (Supabase)
```sql
select brand, active, config from public.clients
where lower(brand)=lower('<requested_brand>')
   or exists (select 1 from jsonb_array_elements_text(coalesce(config->'alternative_names','[]'::jsonb)) a
              where lower(a)=lower('<requested_brand>'));
```
Zero rows / `config` null → STOP y listá `select brand from public.clients where active`. Tomá `cfg = config`.
**Requeridos:** `brand_name`, `shurq_account_id`, `amazon_marketplace`, `acos_target`, `account_stage`.
- Si falta/null `shurq_account_id`/`amazon_marketplace`/`acos_target` → `reason:"config incompleto: falta
  <campo>"`, saltá esta cuenta (eso SÍ es problema de config).
- Resolvé la cuenta: `acc = int(cfg["shurq_account_id"])`; `mkp` desde `amazon_marketplace` (mapa MKP:
  US=1, GB/UK=2, CA=4, MX=5, BR=6, DE=7, ES=8, FR=9, IT=10, NL=16, PL=19, SE=20, BE=21, AE=15, SA=23, IE=24).
- `acos_target` es la **vara** del optimizer → mapea al param **`target_acos` en PERCENT** (`acos_target*100`;
  ej. 0.5 → `50`). **NO uses `tacos_target`.**
- Multi-marketplace = 1 corrida por config (el `brand` distingue US/CA).

### Step 2 — Ventana ancla + clasificación de actividad (por clicks reales — decisión #11/#12)
Anclá las fechas a ART:
```python
from datetime import datetime, timedelta
import zoneinfo
today_art = datetime.now(zoneinfo.ZoneInfo("America/Argentina/Buenos_Aires")).date()
end_date  = (today_art - timedelta(days=1))          # t-1 (ayer ART): último día cerrado
c14_start = (end_date - timedelta(days=13))           # ventana de clasificación = 14 días
```
Pull de clasificación (suma de clicks, 14 días, ENABLED, SP, **sin Scavenger** — regla 11) vía
`query_table("campaigns_daily")` paginado por offset:
```python
rows = []; offset = 0
while True:
    cf = [
      {"column":"report_date","operator":">=","value": c14_start.isoformat()},
      {"column":"report_date","operator":"<=","value": end_date.isoformat()},
      {"column":"mkp_id","operator":"=","value": mkp},
      {"column":"campaign_status","operator":"=","value":"ENABLED"},
    ]
    r = await call_tool("query_table", {
        "account_id": acc, "table_name": "campaigns_daily",
        "columns": "campaign_id,campaign_name,clicks,api_type,campaign_status",
        "filters": <cf como STRING JSON>, "limit": 200, "offset": offset})
    rows += r["data"]
    if not r["metadata"].get("has_more"): break
    offset += 200
# SP only + sin Scavenger (case-insensitive)
rows = [x for x in rows
        if str(x.get("api_type") or "").lower()=="sp"
        and "scavenger" not in str(x.get("campaign_name") or "").lower()]
clicks_14d = sum(int(x.get("clicks") or 0) for x in rows)
```
Regla:
- **≥ 200 clicks en 14 días → "mucha actividad" → ventana de datos = 14 días.**
- **< 200 → "poca actividad" → ventana de datos = 30 días.**

Fijá la ventana de datos del preview:
```python
window_days = 14 if clicks_14d >= 200 else 30
start_date  = end_date - timedelta(days=window_days-1)
# periodo de comparación = el periodo igual inmediatamente anterior (para guardar verbatim)
compare_end_date   = start_date - timedelta(days=1)
compare_start_date = compare_end_date - timedelta(days=window_days-1)
```

### Step 3 — Mapear preset (decisión #7 — el orden importa)
SHURQ tiene 4 presets: `balanced` | `growth` (=sales) | `profit` (=efficiency) | `gentle`. Mapeo:
```
1) on_watchlist  -> "profit"    (ACOS volátil/escalando → cortar ACOS; watchlist gana aunque sea launch)
2) account_stage == "launch" AND NOT on_watchlist -> "growth"   (subir para escalar ventas)
3) else -> "balanced"
```
`on_watchlist` = flag de config (`cfg.acos_watchlist`) o, si no hay flag, match del `brand_name`/
`alternative_names` contra la ACOS watchlist (§Constants). Si el config trae `cfg.optimizer.preset`
explícito (uno de los 4 de SHURQ), ese override manda sobre todo. Guardá `preset_used` (el valor SHURQ).

### Step 4 — Resolver los `campaign_ids` destino (SP ENABLED, SIN Scavenger — regla 11)
SHURQ no usa references: al preview le pasás los `campaign_ids` a optimizar. Armá la lista de campañas
SP habilitadas **excluyendo Scavenger** (case-insensitive) con `list_campaigns` (o reusá el pull de
`campaigns_daily` del Step 2, que ya trae `campaign_id`/`api_type`/`campaign_name`/estado):
```python
cams = await call_tool("list_campaigns", {"account_id": acc, "marketplace_id": mkp})
ids = sorted({ str(c["campaign_id"]) for c in cams["data"]
               if str(c.get("api_type") or "").lower()=="sp"
               and str(c.get("status") or c.get("campaign_status") or "").upper()=="ENABLED"
               and "scavenger" not in str(c.get("campaign_name") or "").lower() })
campaign_ids = ",".join(ids)     # comma-separated para preview_bid_changes
```
> ⚠️ `preview_bid_changes` capea en **200 campañas** por preview (las de mayor daily budget primero; el
> response avisa cuándo el cap muerde). Si una cuenta supera 200 SP enabled no-Scavenger, el preview toma
> el top-200 por budget; anotalo en el snapshot (`note`).

Lista vacía (0 campañas SP ENABLED no-Scavenger) → snapshot con `proposal:[]`, `status:"pending"`,
`note:"sin campañas SP ENABLED en la ventana"`. Fin limpio.

### Step 5 — Preview (motor nativo SHURQ — NO escribe a Amazon)
```python
prev = await call_tool("preview_bid_changes", {
  "account_id": acc, "marketplace_id": mkp,
  "campaign_ids": campaign_ids,           # SP ENABLED sin Scavenger (Step 4)
  "days": window_days,                     # 14 o 30 (≤90) — la ventana del Step 2
  "preset": preset_used,                   # balanced | growth | profit | gentle (Step 3)
  "target_acos": round(acos_target*100, 2),# ⚠️ PERCENT (0.5 → 50), NO fracción, NO tacos_target
  "include_placements": True,              # también modifiers de placement (TOS / product page / rest)
  "max_increase_pct": 15, "max_decrease_pct": 15,   # guardrails ±15% (enteros %)
  # "exclude_dates": "YYYY-MM-DD,...",      # opcional (ej. Prime Day)
  # "margin": <fracción 0-1>,               # opcional: hace los cortes HIGH_ACOS profit-affordable
})
preview_id = prev["preview_id"] if isinstance(prev, dict) else None  # también viene en el summary del result
```
> **⚠️ `target_acos` va en PERCENT** (30 = 30%). Mapealo a `cfg.acos_target*100`. NUNCA `tacos_target`.
> `preview_bid_changes` **no escribe**: computa y parkea el preview **30 min**.

Leé las filas con `get_bid_preview_rows(preview_id, offset, limit, filter)` (limit máx 200, paginar por
offset; `filter` ∈ '' | raise | cut | hold | changed | keyword | target | placement | campaign:<id> |
segment:<high_acos|high_spend_no_sales|low_acos|low_visibility> | texto libre). Para el snapshot traé
`filter="changed"` (solo filas con cambio real).

Cada fila trae (según el engine): el `id` (id de keyword/target; para placements, la fila se selecciona
por `campaign_id`), el tipo (keyword/target vs placement + slot TOS/product_page/rest), `campaign_name`/
`campaign_id`, el targeting/keyword text, `old_value`, `new_value`, y las razones/caps del cambio.
> **Identidad de fila (SHURQ):** los bids se aplican por el `id` de la keyword/target; los **placements**
> se seleccionan por `campaign_id` (`apply_bid_changes`: "campaign ids also select that campaign's placement
> rows"). Guardá ambos en el snapshot (`id` para bids, `campaign_id`+slot para placements) para el apply.

### Step 6 — Redondeo de placements a múltiplo de 5% (⚠️ SOLO PARA DISPLAY en el snapshot)
> **Cambio SHURQ:** `apply_bid_changes` aplica los modifiers que **computó SHURQ** (no se puede inyectar
> un valor redondeado en el apply). Por eso el redondeo pasa a ser **solo cosmético para el dashboard**
> (el número que ve Nacho en el tab), NO el valor que se escribe. Al aplicar, se usa el valor de SHURQ.
> Guardá el redondeado como `new` (display) y el crudo de SHURQ como `new_value_raw`.

Solo para filas de placement (slots TOS / product page / rest of search). Los bids de keyword/product
target quedan intactos.

> **✅ Unidad VERIFICADA contra un preview real (DynamoMe, 2026-09-08).** El `old_value`/`new_value` de un
> placement es **el porcentaje del modifier dividido 100**: `2.93` = **+293%**, `2.49` = +249%. El guardrail
> ±15% es **relativo (multiplicativo)** a `old_value` (ej. 2.93 → 2.49 = exactamente −15%; confirmado con el
> `limit_reasons`). Por eso "redondear a múltiplo de 5%" = **redondear el valor a múltiplo de `0.05`**, y el
> re-clamp usa las bandas `old*(1±0.15)`. Caso borde real observado: `2.60 → 2.99` (299%) redondearía a
> `3.00` (300%) pero eso supera el +15% (máx 2.99) → **re-clampa a 2.95**.

> **⚠️ Edge de modifier chico (encontrado en el test DynamoMe):** con un modifier chico (ej. `old=0.14` =
> +14%) donde AdLabs propone bajar, la banda del guardrail (`[0.119, 0.14]`) **no contiene ningún múltiplo
> de 0.05** → redondear+clampear puede **invertir la dirección** (bajada→subida). Regla: **el redondeo
> nunca invierte la dirección del cambio de AdLabs.** Si no hay step de 5% válido dentro del guardrail en la
> dirección correcta → **dejar `old` (sin cambio este ciclo)** (esa fila se filtra en Step 7).

```python
import math
def round_placement(old_v, new_v, gr=0.15, step=0.05):
    # Valor = %/100 (2.93 = 293%). Redondear a múltiplo de 5% = múltiplo de 0.05 en el valor.
    lo, hi = old_v*(1-gr), old_v*(1+gr)
    v = min(max(new_v, lo), hi)                 # 1) respetar el guardrail ±15% relativo
    r = round(v/step)*step                      # 2) redondear a 0.05
    if r > hi: r = math.floor(hi/step)*step      # 3) re-clamp dentro del guardrail
    if r < lo: r = math.ceil(lo/step)*step
    # 4) NUNCA invertir la dirección del cambio de AdLabs. Si el redondeo cruzó old → sin cambio.
    if (new_v < old_v and r > old_v) or (new_v > old_v and r < old_v):
        r = old_v
    return round(r, 2)
```
Aplicá `new_value = round_placement(old_value, new_value)` a cada fila placement. Si el redondeo deja
`new_value == old_value` (sin cambio efectivo), esa fila NO es una propuesta (se filtra en Step 7).
Guardá el crudo pre-redondeo como `new_value_raw` para auditoría.

### Step 7 — Armar las filas de propuesta (schema COMPACTO — validado 2026-09-08)
Filtrá a filas donde **`new != old`** (cambio real, después del redondeo de placements). Para achicar el
JSONB (una cuenta puede tener **cientos** de filas — DynamoMe dio 705), usá un **lookup de campañas** y
**claves cortas**:
- `campaigns`: array de `campaign_name` únicos; cada fila referencia por índice `ci`.
- Fila: `{ "id":<id de keyword/target, o "" en placements>, "be":<KEYWORD|PRODUCT_TARGET|PLACEMENT_TOP|
  PLACEMENT_PRODUCT_PAGE|PLACEMENT_REST_OF_SEARCH>, "kind":"bid|placement", "ci":<índice campaña>,
  "cid":<campaign_id>, "tgt":targeting, "old":old_value, "new":new_value(display/redondeado) }` +
  **opcionales**: `"raw":new_value_raw` (placements, valor crudo de SHURQ = el que se aplica),
  `"why":change_reasons`, `"cap":limit_reasons` (solo si la fila fue capeada).
- `kind`/`be` distingue tipo: `KEYWORD`/`PRODUCT_TARGET` (bids) vs `PLACEMENT_*` (placements). `ad_type` se
  omite (SP only). El tab calcula el %Δ y la dirección desde `old`/`new`.
- **⚠️ IDENTIDAD DE FILA (SHURQ):** los **bids** se identifican y aplican por el **`id`** de keyword/target.
  Los **placements** se aplican por **`campaign_id`** (`apply_bid_changes` selecciona las filas de placement
  de una campaña por su campaign id) — por eso guardá `cid` en cada fila. La aprobación/exclusión del tab
  keyea por `id` (bids) o por `cid`+slot (placements). El botón "Copiar aprobados" emite, por fila, el `id`
  (bids) o el `cid` (placements) que el apply usa como `keyword_ids`.

### Step 8 — Upsert del snapshot a Supabase — schema `optimizations-v1`
Armá el objeto `datos` (`json.dumps(..., separators=(",",":"))` para compactar):
```json
{ "schema":"optimizations-v1",
  "generated_at_iso":"<ISO ART>",
  "brand":"<brand_name>",
  "marketplace":"US",
  "preset_used":"balanced|growth|profit|gentle",
  "window_days": 14,
  "tacos_used": 0.5,
  "activity":{"clicks_14d": N, "bucket":"mucha|poca"},
  "status":"pending",
  "counts":{"total": N, "bids": N, "placements": N, "up": N, "down": N, "capped": N},
  "campaigns":[ "<campaign_name>", ... ],
  "proposal":[ { "id":"...","be":"...","kind":"bid|placement","ci":0,"cid":"...","tgt":"...","old":0.30,"new":0.35,
                 "why":"LOW_ACOS","cap":"MAX_BID_INCREASE" }, ... ],
  "preview_params":{
     "account_id": <acc>, "marketplace_id": <mkp>,
     "campaign_ids": "<comma-separated SP ENABLED sin Scavenger>",
     "days": 14,
     "preset":"balanced",
     "target_acos": 50,
     "include_placements": true,
     "max_increase_pct": 15, "max_decrease_pct": 15,
     "exclude_dates": ""
  }
}
```
> **`preview_params` VERBATIM (regla 6).** Es lo que `MODE=apply` re-corre para regenerar un `preview_id`
> válido (expira a 30 min; no se guarda). No lo edites ni lo "resumas". Guardá el `campaign_ids` exacto
> del run para que el re-preview del apply optimice el mismo set (sin Scavenger).

Upsert vía el conector Supabase `execute_sql` (dollar-quote con tag `$opt$`, que no aparece en el JSON):
```sql
insert into public.dashboard_snapshots (cliente, tipo, fecha, datos)
values ('<brand_name>', 'optimizations', '<YYYY-MM-DD hoy ART>', $opt$<el objeto datos>$opt$::jsonb)
on conflict (cliente, tipo, fecha)
do update set datos = excluded.datos, actualizado = now();
```
- `cliente` = `cfg["brand_name"]` (= `clients.brand`) · `tipo` = `'optimizations'` · `fecha` = HOY ART
  (día del run) · `datos` = el objeto de arriba.

**No** deployar ni avisar a Slack acá. Confirmá:
`Optimizations (Supabase) escrito para {brand} — {fecha}: {total} cambios ({bids} bids / {placements} placements), preset {preset_used}, ventana {window_days}d ({clicks_14d} clicks/14d), tacos {tacos_used}. status=pending.`

---

## MODE = apply  (empujar SOLO lo aprobado — lo dispara Nacho, NO la Routine)

Carril de vuelta del tab Optimizations. **Escribe live a Amazon** (`apply_bid_changes` + `confirm_action`
es IRREVERSIBLE). **Opción A (decisión de Nacho 2026-09-12): un batch vía `apply_bid_changes`.**

**Trigger:** *"aplicá los bids aprobados de [Brand]"*, *"push approved bids for [Brand]"* + el bloque
pegado del dashboard: el botón "Copiar aprobados" emite, por fila aprobada, el **`id`** que usa el apply
(el `id` de keyword/target para bids; el `cid` de la campaña para placements).

1. **Resolver cliente + config** (Step 1). SHURQ no necesita handshake.
2. **Leer el snapshot pendiente** (el run más reciente con `status:"pending"` de esa marca):
   ```sql
   select fecha, datos from public.dashboard_snapshots
   where cliente = '<brand_name>' and tipo = 'optimizations'
   order by fecha desc, actualizado desc limit 5;
   ```
   Tomá el más reciente cuyo `datos.status == "pending"`. Sacá `preview_params` (verbatim) y el set
   `proposal[]`. Parseá el bloque pegado → set de `id`s aprobados. Matcheá contra `proposal[]`: para bids
   por `id`, para placements por `cid` (+ slot). Reuní `approved_ids` = la unión de `id`s (bids) y `cid`s
   (placements) aprobados. Un id pegado que no está en el snapshot → reportar y saltear (no inventes).
3. **Re-preview fresco con `preview_params` verbatim** (el `preview_id` del feeder ya expiró a los 30 min):
   ```python
   prev = await call_tool("preview_bid_changes", { **preview_params })   # mismos account/mkp/campaign_ids/days/preset/target_acos/guardrails
   preview_id = prev["preview_id"]
   ```
   El `campaign_ids` verbatim ya excluye Scavenger (regla 11); igual re-validá que ningún id aprobado caiga
   en una Scavenger.
4. **Aplicar SOLO lo aprobado — `apply_bid_changes` (Opción A: valor RECOMPUTADO del re-preview):**
   ```python
   res = await call_tool("apply_bid_changes", {
     "preview_id": preview_id,
     "keyword_ids": ",".join(approved_ids),   # ids de keyword/target (bids) + campaign ids (placements)
     "include_placements": True,
     "max_rows": 500})
   aid = res["action_id"]                      # (o el id que devuelva el result)
   await call_tool("confirm_action", {"action_id": aid})   # ← ESTO escribe a Amazon
   ```
   - **`keyword_ids` vacío = TODAS las filas cambiadas** → NUNCA lo dejes vacío en apply (aplicarías todo).
     Pasá siempre los `approved_ids`.
   - Un batch = hasta **500 filas** (`max_rows`); si hay más aprobadas, batchear de a 500 (cada batch =
     su `confirm_action`). Respeta los write-guardrails del seller (bid cap/floor, max % change, daily cap).
   - SB/SD placement rows quedan en `not_applied` (executor SP-only) — reportalo.
   - Los ids aprobados que ya no existan/estén pausados → el apply los reporta en `not_applied`; saltealos,
     no frenes el resto.
5. **Marcar el snapshot como aplicado** (queda como history): `datos.status = "applied"` +
   `datos.applied = {at_iso, by:"Nacho", ids:[...], note:"Bid Optimizer via SHURQ MCP (Opción A, recomputado)"}`.
   Upsert a la MISMA fila `(cliente,'optimizations',fecha del snapshot)`:
   ```sql
   update public.dashboard_snapshots
   set datos = $opt$<datos con status=applied + applied{}>$opt$::jsonb, actualizado = now()
   where cliente = '<brand_name>' and tipo = 'optimizations' and fecha = '<fecha del snapshot>';
   ```
   Confirmá: `Applied {brand} — {n} filas pusheadas a Amazon ({aplicadas} ok / {not_applied} salteadas),
   snapshot {fecha} marcado applied. (valores del re-preview del día — Opción A)`

---

## MODE = audit / audit-apply  — ELIMINADO en la migración a SHURQ

> Estos modos resincronizaban los **optimization groups de AdLabs**, que **no existen en SHURQ**. El
> feeder optimiza sobre el ACOS de perfil vía el param `target_acos` de `preview_bid_changes`, así que
> no hay grupos que auditar ni resincronizar. Si alguien dispara este skill en modo audit → respondé:
> `MODE=audit no aplica bajo SHURQ (no hay optimization groups). El feeder ya optimiza sobre acos_target.`

## Scheduling (Routine de nube — la crea Nacho, NO este skill)

- **Cadencia:** **Martes y Viernes**, automática/unattended (decisión #5/#14). Ej. ~11:00 ART, después
  de que corran los feeders diarios y antes del master compose de la tarde (o su propio compose slot).
- **Scope al arranque = pilotos** (decisión #4): **Urban Veda (Ayurveda Wellness), Dr. Cohen's HEATABLE,
  DynamoMe.** Una Routine que recorre esas 3 marcas (o el patrón por offset de la familia si se escala a
  las 20). Connectors **Supabase + SHURQ**. Sin repo, sin carpeta local.
- **Prompt sugerido:** `Run the biweekly-bid-optimizer skill in MODE=run for each pilot brand
  (Urban Veda, Dr. Cohen's HEATABLE, DynamoMe): resolve config from Supabase, classify activity by
  clicks, map preset, run SHURQ preview_bid_changes with +-15% guardrails, and upsert the optimizations
  snapshot (status pending). Write nothing to Amazon. Don't ask for confirmation. Continue on error.`
- **El apply NO se agenda** — lo dispara Nacho a mano después de revisar el tab (MODE=apply).
- **Sin prerequisito de audit:** no hay optimization groups en SHURQ; el feeder optimiza sobre el ACOS de
  perfil vía `target_acos`. El único prerequisito real es que `config.acos_target` de cada cuenta esté cargado.

---

## Edge cases
| Situación | Comportamiento |
|---|---|
| Config sin `shurq_account_id`/`amazon_marketplace`/`acos_target` | `reason:"config incompleto: falta <campo>"`, saltar esa cuenta (SÍ es config). |
| `preview_bid_changes`/`query_table` de SHURQ falla (timeout/rate-limit/sync/preview expirado) | Reintentar 1 vez; si sigue, `reason:"shurq_error: <msg>"`, seguir con las demás. NUNCA "cuenta no configurada" si el ID está (regla 8). |
| 0 campañas SP ENABLED en la ventana | Snapshot `proposal:[]`, `status:"pending"`, note. Fin limpio. |
| Preview devuelve 0 cambios (todo new==old) | Snapshot `proposal:[]`, `counts` en 0, `status:"pending"`. |
| Cuenta en watchlist Y launch | Watchlist gana → `profit` (orden del Step 3). |
| `cfg.optimizer.preset` override presente | Ese preset (SHURQ) manda sobre el auto-mapeo. |
| Redondeo de placement (solo display) deja new==old | Esa fila no es propuesta de display (se filtra en Step 7); el valor que aplica es el de SHURQ. |
| Re-run el mismo día (run) | Idempotente: pisa la fila `(cliente,'optimizations',hoy)`. |
| apply: `id` pegado no está en el snapshot | Reportar y saltear (no inventar). |
| apply: `id` ya no válido (pausado/borrado) | `apply_bid_changes` lo devuelve en `not_applied`; saltear, reportar, aplicar el resto igual. |
| apply: `preview_id` expirado (>30 min) | Esperado — se regenera re-corriendo `preview_bid_changes` con `preview_params` verbatim (Step 3). |
| apply: `keyword_ids` vacío | ⛔ NUNCA en apply — aplicaría TODAS las filas cambiadas. Pasar siempre los `approved_ids`. |
| > 500 filas aprobadas | Batchear de a 500 (`max_rows`); cada batch = su `confirm_action`. |
| SB/SD placement rows en el destino | Quedan en `not_applied` (executor SP-only); reportar. |
| Multi-marketplace | 1 corrida por config; el `brand` distingue US/CA. |
| Campaña Scavenger en la cuenta | Excluida del `campaign_ids` que se pasa al preview (regla 11, case-insensitive). Nunca se optimizan bids ni placements. |
| Identidad de fila (SHURQ) | Bids por `id` de keyword/target; placements por `campaign_id` (`cid`). El apply usa esos ids como `keyword_ids`. |
| target_acos param | Va en **PERCENT** (`acos_target*100`, ej. 0.5→50). NUNCA `tacos_target`. |
| > 200 campañas SP enabled | `preview_bid_changes` toma el top-200 por daily budget; anotarlo en el `note` del snapshot. |

---

## Notas de build / open items a cerrar antes de prod (§9 del spec)
- **Configs de pilotos:** resolver `shurq_account_id / amazon_marketplace / acos_target / account_stage`
  de Urban Veda (Ayurveda Wellness), Dr. Cohen's HEATABLE y DynamoMe desde `public.clients` antes del
  primer run (los `shurq_account_id` ya están backfilleados para las 20 cuentas activas).
- **Watchlist:** confirmar vigencia (Urban Veda, Dr. Cohen's HEATABLE, Masofta Inc, MyNextGen, Suji
  Health) o migrar a flag de config `acos_watchlist`.
- **Validar en vivo (1 cuenta piloto):** correr `preview_bid_changes` contra DynamoMe y confrontar el
  conteo/valores contra el Bid Optimizer del /ad-manager de SHURQ; confirmar la identidad de fila (id de
  keyword/target para bids, campaign_id para placements) que usa `apply_bid_changes`.
- **Piezas separadas (no en este skill):** (a) master compose v2.4 (rama SQL `tipo='optimizations'`,
  days[], assert, count Slack); (b) template HTML del tab Optimizations (renderOptimizations()). El botón
  "Copiar aprobados" debe emitir el `id` (bids) / `cid` (placements) que consume el apply.
