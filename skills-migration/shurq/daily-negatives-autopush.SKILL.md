---
name: daily-negatives-autopush
description: >
  Puente automático: toma el snapshot de daily-negatives-supabase y empuja los negativos
  irrelevantes a Amazon Ads vía SHURQ sin copy-paste, auto-derivando el destino por línea de
  producto (ad groups ENABLED SP+SB, menos Scavenger). Solo keywords (los ASINs van a revisión
  manual). GATE: autopushea confianza high/medium; los 'low' quedan para tu aprobación en el
  dashboard. Deja recibo en Supabase. Modos: 'run' (default), 'dry-run' y 'approved' (pushea +
  aprende los LOW que aprobaste, y pushea held con la línea que le asignaste). Trigger: "autopush
  negatives para [Brand]", "run daily-negatives-autopush for [Brand]", "pushear aprobados de
  [Brand]", "pushear low aprobados de [Brand]".
---

# Daily Negatives — Autopush (snapshot → SHURQ, automático)

**Versión:** V3.0 (2026-09-11) — **migrada de AdLabs a SHURQ.** Misma lógica de gate + MODE=approved
que V2.0; lo que cambió es el **motor de push** (AdLabs `create_entities`/`apply` → SHURQ
`add_negative_keyword` + `confirm_action`) y la **resolución de cuenta/destino**
(`adlabs_team_id`/`profile_id` + `get_entity_data(ad_group, CONTAINS_ASINS)` → `shurq_account_id` +
`mkp_id` + `list_product_ads`).

**Historial:** V2.0 (2026-09-06) — gate de confianza + MODE=approved. V1.0 (2026-08-30) — puente
snapshot→AdLabs, auto-ruteo por línea, recibo + idempotencia.

Es el eslabón entre **identificar** y **aplicar**. `daily-negatives-supabase` ya decide QUÉ
negativizar, con qué match y con qué **confianza** (`high`/`medium`/`low`), y lo deja en el snapshot.
Este skill lo **empuja solo**, con un **gate**: solo autopushea `high`+`medium`; los `low` quedan
retenidos (`held_low_confidence`) para el dashboard. Cuando Nacho aprueba LOW, corre en
**`MODE=approved`**: empuja esos términos (salteando el gate) + **los aprende**.

**Respondé a Nacho en español.**

> **Relación con los otros skills:**
> - `daily-negatives-supabase` (run) → escribe el snapshot. **Corre ANTES.**
> - **este skill** → lee el snapshot y pushea vía SHURQ. **Corre DESPUÉS.**
> - `weekly-negatives-review` → red de seguridad semanal.
> - `adlabs-push-negatives` / (su sucesor `shurq-push-negatives`) → la mecánica de push manual/ad-hoc.
> El snapshot es **agnóstico de la fuente**: sirve igual si el identificador todavía corre en AdLabs
> durante la transición. Solo el PUSH de este skill cambia a SHURQ.

---

## Cómo se llama a SHURQ (mecánica del conector)

SHURQ expone `search` / `get_schema` / `execute`. Los tools semánticos (`list_product_ads`,
`add_negative_keyword`, `confirm_action`, `get_action_status`) se invocan desde `execute` con
`await call_tool("<tool>", {...})`. Sandbox: Python real (`None/True/False`), **sin** `json.loads`
(el resultado ya viene parseado), **sin** pandas, **sin** `date.today()`; `call_tool` es **async**.

**Patrón de escritura SHURQ (preview → confirm → verify):**
1. `add_negative_keyword(account_id, mkp_id, keyword, campaign_id, ad_group_id, match_type, level)`
   → devuelve `{action_id, status:"pending_confirmation", preview:{...}, guardrail_check:{passed, block_type, reason}, expires_at, hint}`. **Esto NO aplica nada todavía.**
2. Revisá `guardrail_check.passed`. Si `false` → **no confirmes**, registralo como skipped con el
   `block_type`/`reason`.
3. `confirm_action(action_id)` → encola la acción al worker (async). **Esto sí aplica a Amazon.**
4. `get_action_status(account_id, action_id)` → verificá el resultado (creado / ya existía / error).

> ⚠️ **El preview expira en ~5 minutos.** Confirmá **inmediatamente después** de cada preview
> (secuencia preview→confirm por keyword), no acumules previews para confirmar al final.

No hay `start_chat_session`, `read_resource`, references `mcp://data/...`, ni `create_entities` — eso
era AdLabs.

---

## Reglas de oro (no negociables — heredadas)

1. **Destino explícito SIEMPRE, nunca "a toda la cuenta".** El destino lo deriva el skill desde el
   `product` (línea/parent) de cada candidato. Red de seguridad: **si un candidato no tiene producto
   resoluble a un set de ASINs concreto (`product = "General (sin asignar)"`, o la línea no matchea
   `managed_asins`), NO se pushea.** Queda en el snapshot como "retenido". Un destino vacío jamás
   significa "todas".
2. **Nivel = AD GROUP** (`level="ad_group"`). Sirve para SP y SB, y es quirúrgico.
3. **Match type + QUÉ texto se pushea (clave):** el snapshot fija el match; el modelo no lo re-decide.
   - `match:"phrase"` → `match_type="phrase"`, y **se pushea el `root`, NO el término completo.** El
     `root` es la raíz limpia (marca/competidor/familia) que el identificador ya extrajo (ej.
     `re u hair serum` → `root:"re u"`). Negar `re u` como phrase bloquea todas las búsquedas con
     "re u" sin tocar genéricos como "hair serum". Si `root` viene vacío, fallback: pushear el `term`.
   - `match:"exact"` → `match_type="exact"`, y se pushea el **`term` completo** (root vacío en exact).
   - No hay product target acá (regla 10: ASINs no se pushean).
   > **Bonus:** pushear el root evita el límite de Amazon de **4 palabras en phrase** (`force facto
   > hair growth excelerator` = 5 palabras violaría; el root `force facto` = 2, OK).
4. **Auto-apply.** El flujo va derecho preview → resumen → confirm, pero SIEMPRE imprime el resumen
   exacto (qué línea, qué ad groups, cuántos negativos) antes de confirmar. `dry-run` frena antes del
   confirm (hace los previews pero NO los confirma).
5. **Solo ENABLED.** De `list_product_ads`, quedate solo con `ad_status=="ENABLED"`. (El estado de
   campaña se refleja en que sus product ads enabled existan; si dudás, cruzá con `list_campaigns`
   status=enabled.)
6. **Excluir Scavenger SIEMPRE** (regla de Nacho): descartá todo ad group cuyo `campaign_name`
   contenga `scavenger` (case-insensitive). Las Scavenger son de descubrimiento intencional.
7. **`note` significativa por push** para el audit log. SHURQ no toma un `note` libre en
   `add_negative_keyword`, así que el rastro queda en el **recibo de Supabase** (Step 7) con
   `source_terms`, línea, y `action_id`+status de cada confirm.
8. **Nunca negativices marca propia ni `managed_asins` del cliente.** El snapshot ya los excluye;
   re-chequealo como red.
9. **Idempotencia.** Si ya se pusheó hoy (recibo `negatives_push` del día), saltear los `(term, match,
   line)` ya aplicados. Además, si `get_action_status` reporta "already exists", contalo como
   `skipped_existing` (no error).
10. **NUNCA auto-negativices ASINs (pedido de Nacho).** Cualquier candidato `kind=="asin"` (matchea
    `^b0[a-z0-9]{8}$`) NO se pushea → va a `asins_skipped[]` para revisión manual. Solo keyword-negatives.
11. **Términos con caracteres especiales NO se pueden negar.** Si el `push_text` tiene cualquier char
    fuera de `[A-Za-z0-9 '&-]` (no-ASCII: acentos, `ą`,`ł`,`ñ`, emojis… o símbolos como coma,`/`,`+`,
    `%`,`"`), Amazon lo rechaza → **NO se pushea.** A `dropped[]` con `reason:"special_char"`. (Hyphen,
    apóstrofo y `&` sí se permiten.)
12. **GATE DE CONFIANZA.** Solo se autopushean `confidence ∈ {"high","medium"}`. Los `low` NO se
    pushean: van a `held_low_confidence[]` para el dashboard. Snapshot viejo **sin** `confidence` → se
    trata como `high` (comportamiento V1). En `MODE=approved` el gate se saltea para lo aprobado.

---

## Constants

```
Fuente de datos: Supabase (conector MCP, proyecto POD 66 - Organization, awhiobrcgghyiycxukjm)
  Config cliente: public.clients (config JSONB) — brand_name, shurq_account_id, amazon_marketplace, managed_asins
  Perfil relevancia: public.relevance_profiles (profile JSONB) — protected_relevant (red de seguridad)
  Snapshot del día: public.dashboard_snapshots, tipo='negatives', fecha=HOY(ART) — lo escribe daily-negatives-supabase
  Recibo de push: public.dashboard_snapshots, tipo='negatives_push', fecha=HOY(ART) — lo escribe ESTE skill
Timezone: America/Argentina/Buenos_Aires (ART) — anclar SIEMPRE a ART (las Routines corren en UTC)
SHURQ: account_id (int) + mkp_id. Tools: list_product_ads, add_negative_keyword, confirm_action, get_action_status.
```

### Marketplace → `mkp_id`
US=1 · GB/UK=2 · CA=4 · MX=5 · BR=6 · DE=7 · ES=8 · FR=9 · IT=10 · NL=16 · PL=19 · SE=20 · BE=21 ·
AE=15 · SA=23 · IE=24. Si falta, resolvé con `list_my_accounts()`.

---

## Startup (siempre)

En paralelo:
1. Supabase: leé el `config` del cliente (Step 1).
2. SHURQ: no requiere startup. (Opcional: `get_my_write_guardrails(account_id, mkp_id)` para conocer
   los caps de escritura antes de un bulk grande — así sabés si un push va a chocar un guardrail.)

---

## MODE = run (default — un cliente)

### Step 1 — Resolver cliente + config (Supabase)
```sql
select brand, active, config from public.clients
where lower(brand)=lower('<requested_brand>')
   or exists (select 1 from jsonb_array_elements_text(coalesce(config->'alternative_names','[]'::jsonb)) a
              where lower(a)=lower('<requested_brand>'));
```
Zero rows / `config` null → STOP y listá `select brand from public.clients where active`. Tomá `cfg = config`.
Requeridos: `brand_name`, `shurq_account_id`, `amazon_marketplace`, `managed_asins`. Derivá
`account_id = int(shurq_account_id)` y `mkp_id` del marketplace. Multi-marketplace = 1 corrida por config.

> **⚠️ Diagnóstico honesto de config vs. error de SHURQ:** chequeá los requeridos **contra el config**
> y reportá lo que ves:
> - Campo **realmente** ausente/null → `reason:"config incompleto: falta <campo>"`, saltá ese cliente.
> - Si `shurq_account_id` **está presente**, **NUNCA** concluyas "cuenta no conectada" si después una
>   llamada a SHURQ falla. Un fallo transitorio (timeout, rate-limit por correr 5 clientes seguidos)
>   NO es problema de config: **reintentá 1 vez**; si vuelve a fallar, `reason:"shurq_error: <msg>"`,
>   lo no aplicado queda pendiente (idempotente) y **seguís con los demás clientes**.

Armá el índice de líneas desde `cfg.managed_asins`:
- `line_asins`: mapa `línea/parent → [asins]` (por `product_line` si existe, o colapsando children a
  su `parent_asin`, igual que `daily-negatives-supabase` Step 4b).
- `own_asins`: set de TODOS los ASINs del cliente (red de seguridad regla 8).

### Step 2 — Leer el snapshot del día
```sql
select datos from public.dashboard_snapshots
where cliente = '<brand_name>' and tipo = 'negatives' and fecha = '<HOY-ART YYYY-MM-DD>';
```
- Zero rows → **STOP suave**: `No hay snapshot de negatives de hoy para {brand}. Corré daily-negatives-supabase primero.`
- `datos.day.candidates` vacío → `Sin candidatos hoy para {brand}, nada que pushear.` Fin.
- `datos.client.status == "datafail"` → reportá y fin.

### Step 3 — Leer el recibo de push de hoy (idempotencia)
```sql
select datos from public.dashboard_snapshots
where cliente = '<brand_name>' and tipo = 'negatives_push' and fecha = '<HOY-ART>';
```
Si existe, armá `already_pushed` = set de `(term, match, line)` ya aplicados (de `datos.applied[]`).
Clave por línea (no solo term+match): un mismo término puede negarse en dos líneas el mismo día.

### Step 4 — Preparar candidatos + red de seguridad
Cada candidato trae `{term, clicks, spend, match, root, reason, kind, product, confidence, evidence,
origin_campaign, origin_ad_group}`.

> **`push_text` — QUÉ se negativiza (regla 3):** `match=="phrase"` → `push_text = root` (fallback
> `term` si root vacío); `match=="exact"` → `push_text = term`. Todo lo de abajo (chars especiales,
> límites, dedup, idempotencia) opera sobre `push_text`. Guardá el/los `term` como `source_terms`.

Clasificá cada candidato **en este orden** (el primero que aplica gana):
1. **Marca propia (regla 8):** `kind=="asin"` y ASIN ∈ `own_asins` → descartar. `kind=="keyword"` y
   término claramente marca propia → descartar. `dropped[]` (`reason:"own_brand"`).
2. **protected_relevant:** cargá `protected_relevant` del perfil
   (`select profile->'protected_relevant' from public.relevance_profiles where brand='<brand_name>'`).
   El `reason` de cada excepción fija el alcance (contención/wildcard vs SOLO igualdad exacta). Chequeá
   el `push_text`:
   - **Contención/wildcard** → toda la familia es relevante → descartar (`protected_relevant`).
   - **Igualdad, candidato PHRASE, `term` completo MÁS LARGO que el protegido y no matchea excepción**
     → re-rutear a **EXACT del `term` completo** (mové a `exact[]`, `push_text=term`). Ej. Hekaya:
     `turkish` protegido solo por igualdad; `turkish cotton towel` (root `turkish`) NO se pushea phrase
     `turkish` → se pushea exact `turkish cotton towel`.
   - **Igualdad y `push_text`/`term` ES el protegido** → descartar (`protected_relevant`).
3. **ASINs NUNCA (regla 10):** `kind=="asin"` → NO pushear → `asins_skipped[]` con todo el contexto.
4. **Chars especiales (regla 11):** `push_text` con char fuera de `[A-Za-z0-9 '&-]` → NO pushear →
   `dropped[]` (`reason:"special_char"`). Chequealo ANTES de agrupar.
5. **Retención por producto no resoluble (regla 1):** `product == "General (sin asignar)"` o línea no
   en `line_asins` → **retener** → `held[]` con contexto + `suggested_line` best-effort (matcheá
   `origin_campaign`/`origin_ad_group` contra nombres de línea; si no hay match claro → `null`).
6. **Idempotencia:** `(push_text, match, line)` ∈ `already_pushed` → saltear.
7. **Gate de confianza (regla 12) — SOLO run/dry-run:** `high`/`medium` → sigue; `low` → NO pushear →
   `held_low_confidence[]` con contexto (para el dashboard); sin `confidence` → tratar como `high`.
   En **MODE=approved** este gate NO corre.

Los sobrevivientes se agrupan por **línea** → `push_groups[linea] = {phrase[], exact[]}` (**sin ASINs**),
cada lista con `push_text` **deduplicados** (case-insensitive). Conservá `source_terms` por `push_text`.

### Step 5 — Resolver destino por línea + PUSH vía SHURQ

Traé el catálogo de product ads UNA vez por cuenta:
```python
pa = await call_tool("list_product_ads", {"account_id": account_id, "marketplace_id": mkp_id})
ads = pa["data"]   # cada fila: {ad_status, amazon_asin, api_type, campaign_id, campaign_name, adgroup_id, ...}
```
> **Paginación:** `list_product_ads` trae hasta `limit` (default 100) filas. Si `metadata.rows_returned
> == limit`, subí `limit` o paginá hasta traer todo el catálogo (cuentas grandes tienen >100 product
> ads). No pushees con un catálogo truncado.

Por cada `linea` en `push_groups`:
1. `asins_linea = set(line_asins[linea])`.
2. **Resolver ad groups destino** (reemplaza el `CONTAINS_ASINS` de AdLabs): de `ads`, quedate con las
   filas donde:
   - `amazon_asin in asins_linea`, **y**
   - `ad_status == "ENABLED"`, **y**
   - `api_type in ("sp","sb")` (keyword-negatives NO aplican a SD → salteá `sd`), **y**
   - `"scavenger" not in campaign_name.lower()` (regla 6).
   Deduplicá a pares únicos `(campaign_id, adgroup_id)`. Ese es el set destino de la línea.
3. **Set vacío (0 ad groups ENABLED que anuncian la línea):** NO pushees. Sumá la línea a
   `held_no_dest[]` con motivo "sin ad groups ENABLED que anuncien esta línea".
4. **Validar `push_text` con FALLBACK a exact (NO drop):** ≤80 chars; PHRASE ≤4 palabras; EXACT ≤10.
   - **PHRASE que supera 4 palabras (o 80 chars):** NO descartar → re-rutear a **EXACT del `term`
     completo** (mové a `exact[]`, `push_text=term`). Solo si el `term` también supera exact
     (>10 palabras / >80 chars) → drop `reason:"limit_violation"`.
   - **EXACT que supera 10 palabras / 80 chars:** drop `reason:"limit_violation"`.
5. **PUSH (preview → confirm → verify), por cada `(campaign_id, adgroup_id)` × `push_text` × match:**
```python
results = []
for (cid, agid) in dest_pairs:
    for kw in phrase_list:      # y análogo para exact_list con match_type="exact"
        prev = await call_tool("add_negative_keyword", {
            "account_id": account_id, "mkp_id": mkp_id,
            "keyword": kw, "campaign_id": cid, "ad_group_id": agid,
            "match_type": "phrase", "level": "ad_group"})
        gc = prev.get("guardrail_check", {})
        if not gc.get("passed", True):
            results.append({"kw": kw, "cid": cid, "agid": agid, "status": "blocked",
                            "reason": gc.get("block_type") or gc.get("reason")})
            continue
        aid = prev["action_id"]
        # dry-run: NO confirmar — solo registrar el preview
        if MODE == "dry-run":
            results.append({"kw": kw, "cid": cid, "agid": agid, "status": "previewed", "action_id": aid})
            continue
        await call_tool("confirm_action", {"action_id": aid})
        stt = await call_tool("get_action_status", {"account_id": account_id, "action_id": aid})
        results.append({"kw": kw, "cid": cid, "agid": agid, "status": stt, "action_id": aid})
```
   - Confirmá **inmediatamente** tras cada preview (expira en 5 min).
   - `get_action_status` que reporte "already exists" → contalo `skipped_existing`, no error.
   - **Conteo esperado** = pares (ad groups) × keywords por match. A diferencia de AdLabs, cada negativo
     es una llamada; no hay preview cartesiano único. Si el volumen es alto, considerá `get_my_write_guardrails`
     para no chocar el cap de acciones/día.

### Step 6 — Resumen (imprimir SIEMPRE) + confirm
Imprimí, por línea, el destino resuelto y los conteos ANTES de confirmar. Ejemplo:
> **Autopush {brand} — {fecha}:**
> - Línea **Hair Growth Serum** → 8 ad groups ENABLED (SP+SB) que anuncian sus 2 ASINs (2 Scavenger excluidas)
> - 5 kw PHRASE × 8 ad groups = 40 · 3 kw EXACT × 8 = 24
> - **ASINs (no auto-negados):** 3 términos b0… → revisar a mano.
> - **Retenidos:** 4 keywords sin producto resoluble → dashboard.
> - **Baja confianza (gate):** 6 keywords `low` → dashboard con checkboxes.
> Confianza pusheada: 12 high · 5 medium.

**Si modo = `dry-run`:** parás acá. Mostrá conteos + `action_id`s previewados (sin confirmar). No apliques.
**Si modo = `run`:** ejecutá los `confirm_action` del Step 5 y verificá con `get_action_status`.

### Step 7 — Recibo de push a Supabase (auditoría + idempotencia + insumo del weekly)
Construí `datos` schema `negatives-push-v1` (mismo schema que V2 — el dashboard no cambia) y upserteá.
Marcá `summary.engine:"shurq"` para trazabilidad. En `applied[]`, `term` = `push_text` (root en phrase),
`clicks`/`spend` = suma de los `source_terms`, y agregá `action_ids:[...]` de los confirms exitosos.
```json
{ "schema":"negatives-push-v1", "generated_at_iso":"<ISO ART>", "engine":"shurq",
  "brand":"<brand_name>", "marketplace":"US", "currency_prefix":"$",
  "date_iso":"<HOY-ART>", "data_window":"<ayer, del snapshot>",
  "summary":{"applied_terms":N,"created":N,"skipped_existing":N,"blocked":N,"held":N,"held_low_confidence":N,
             "asins_skipped":N,"dropped":N,"held_spend":F,"low_confidence_spend":F,"asins_spend":F,
             "ad_groups_touched":N,"lines":N,"confidence_pushed":{"high":N,"medium":N}},
  "applied":[{"term":"<push_text>","source_terms":["<orig>"],"clicks":N,"spend":F,"match":"phrase|exact",
              "kind":"keyword","line":"...","ad_groups":N,"created":N,"skipped":N,"action_ids":["act_..."]}],
  "held":[{"term":"...","clicks":N,"spend":F,"match":"...","kind":"keyword",
           "product":"General (sin asignar)","reason":"...","origin_campaign":"...","origin_ad_group":"...","suggested_line":"<linea>|null"}],
  "held_low_confidence":[{"term":"...","clicks":N,"spend":F,"match":"...","root":"...","kind":"keyword",
           "product":"<linea>","confidence":"low","evidence":"<hecho>","reason":"...","origin_campaign":"...","origin_ad_group":"..."}],
  "asins_skipped":[{"term":"b0xxxxxxxx","clicks":N,"spend":F,"kind":"asin","product":"<linea|General>",
           "origin_campaign":"...","origin_ad_group":"...","reason":"ASIN - no auto-negado (regla de Nacho)"}],
  "dropped":[{"term":"...","reason":"own_brand | protected_relevant | special_char | limit_violation | blocked_guardrail"}] }
```
```sql
insert into public.dashboard_snapshots (cliente, tipo, fecha, datos)
values ('<brand_name>', 'negatives_push', '<HOY-ART>', $push$<datos>$push$::jsonb)
on conflict (cliente, tipo, fecha) do update set datos = excluded.datos, actualizado = now();
```
> **Merge en re-run:** si ya había recibo hoy, MERGEá `applied[]` (no lo pises) — sumá solo lo nuevo.

Confirmá:
`Autopush {brand} — {fecha}: {created} keyword-negatives creados en {ad_groups_touched} ad groups ({lines} líneas) [{high} high / {medium} medium], {skipped_existing} ya existían, {blocked} bloqueados por guardrail, {asins_skipped} ASINs no auto-negados, {held} retenidos, {held_low_confidence} en baja confianza, {dropped} descartados.`

---

## MODE = dry-run
Idéntico hasta Step 6, **sin confirmar** (hace los `add_negative_keyword` preview pero NO llama
`confirm_action`). Los previews expiran solos en 5 min → no tocan Amazon.
- **Por default (ad-hoc):** no escribe recibo; solo imprime resumen + conteos previewados.
- **Dry-run + recibo (Routine de estreno):** si te lo piden, SÍ escribe el recibo `negatives_push` con
  `summary.mode:"dry-run"` y `applied[]` = lo que HABRÍA creado (conteo = pares × keywords por match).
  > **⚠️ Caveat:** el conteo del dry-run **no descuenta** negativos ya existentes (SHURQ recién lo sabe
  > en el confirm/status). Interpretá el número como "techo / candidatos a crear", no como neto final.

---

## MODE = approved (empujar lo que Nacho aprobó desde el dashboard + aprenderlo)
El carril de vuelta del dashboard. Dos casos, mismo comando/formato:
- **LOW aprobados:** candidatos `low` que el gate retuvo. Nacho tilda y copia.
- **Held asignados:** keywords retenidos por producto no resoluble a los que Nacho ahora **asigna una
  línea** en el dashboard y copia.
**Aprobar = pushear hoy + aprender** (un comando).

**Trigger:** *"pushear aprobados de [Brand]"*, *"pushear low aprobados de [Brand]"*, *"aprobar estos
negativos de [Brand]"* + el bloque pegado (`term ⇥ match ⇥ reason ⇥ product/línea`; la 4ta columna es
la **línea destino**).

1. **Resolver cliente + config** (Step 1) y **leer snapshot** (Step 2). Del snapshot tomá el contexto
   de cada término (match, root, origin_*, evidence) matcheando por `term`. **La 4ta columna pegada
   MANDA** y **override** el `product` del snapshot. Sin línea y snapshot sin resolverla → retener.
2. **Redes de seguridad SÍ, gate NO.** Corré Step 4 items 1–5 (marca propia, protected_relevant, ASIN,
   char especial, idempotencia). **Saltá el gate (item 7).** La retención por producto no resoluble NO
   aplica cuando la 4ta columna trae una línea válida (∈ `line_asins`). Línea pegada que no matchea →
   retener y reportar.
3. **Pushear** con el mismo motor SHURQ: Step 5 (resolver destino por línea vía `list_product_ads` →
   `add_negative_keyword` → `confirm_action` → `get_action_status`) → Step 6 (resumen + confirm).
4. **Aprender (obligatorio).** Por cada término aprobado, aplicá el **`MODE=learn` de
   `daily-negatives-supabase`** (upsert a `relevance_profiles`, schema v2): `match=phrase` →
   agregar/confirmar `root` como `{confidence:"high", basis:"profile", evidence:"aprobado por Nacho
   desde el dashboard <fecha>", added_by:"approved", ...}`; competidor/licensed → a `competitors`.
   (Si Nacho marcó "aprobar solo hoy, no aprender", saltá el learn para ese.)
5. **Recibo** (Step 7) con `summary.mode:"approved"`, `engine:"shurq"`; en `applied[]` marcá
   `origin:"approved_low"` u `origin:"approved_held"`. Confirmá:
   `Aprobados {brand} — {fecha}: {created} negativos creados ({n} términos: {n_low} low + {n_held} held asignados), {learned} aprendidos al perfil, {held}/{dropped} retenidos/descartados.`

---

## Scheduling (Routines de nube — las crea Nacho, NO este skill)
- **Feeder autopush — batches por OFFSET:** una Routine por offset, cada una procesa 5 clientes
  (`select brand from public.clients where active=true order by brand limit 5 offset <N>`), mismo prompt
  cambiando solo `<N>` (0/5/10/15/…). Corren **después** del identificador y **antes** del composer.
  Connectors **Supabase + SHURQ** (ya no AdLabs), sesión nueva por corrida, sin repo.
- **Estrenar en dry-run** (recibo con `mode='dry-run'`, sin confirmar), y pasar a run cuando esté validado.
- Multi-marketplace = cubierto (cada CA es su propio `brand`).
- **Orden importa:** si el autopush corre sin snapshot del día → STOP suave, no pushea. Seguro por diseño.

---

## Edge cases
| Situación | Comportamiento |
|---|---|
| No hay snapshot de negatives hoy | STOP suave, no pushea. "Corré daily-negatives-supabase primero." |
| Snapshot con candidates:[] | Nada que pushear. Fin limpio. |
| Candidato `kind=="asin"` | NUNCA se pushea (regla 10). Va a `asins_skipped[]`. |
| Candidato `product = "General (sin asignar)"` (keyword) | RETENER. `held[]`. Dashboard. |
| Línea sin ad groups ENABLED que la anuncien | RETENER esa línea (`held_no_dest[]`). Nunca pushear sobre 0 destinos. |
| `list_product_ads` truncado (`rows_returned == limit`) | Paginar / subir limit hasta el catálogo completo. No pushear truncado. |
| `guardrail_check.passed == false` en el preview | No confirmar. `dropped[]`/`blocked` con el `block_type`/`reason`. |
| `get_action_status` = "already exists" | `skipped_existing`, no error. |
| Fetch de SHURQ falla (timeout/rate-limit) | Reintentar 1 vez; si sigue, `reason:"shurq_error"`, seguir con los demás. NUNCA "cuenta no conectada" si `shurq_account_id` está. |
| Config con `shurq_account_id` ausente/null | `reason:"config incompleto: falta shurq_account_id"`, saltar (eso SÍ es config). |
| Campaña Scavenger en el destino | Excluida (regla 6). Reportar cuántas. |
| Término/ASIN de marca propia o managed_asins | Descartar (regla 8). `dropped`. |
| `push_text` en protected_relevant por contención | Descartar. `dropped` (`protected_relevant`). |
| Raíz phrase = protegido por igualdad y `term` más largo | Re-rutear a exact del `term` completo. |
| Búsqueda pelada = protegido por igualdad | Descartar (`protected_relevant`). |
| Keyword con chars especiales | NO negable (regla 11). `dropped` (`special_char`). |
| PHRASE > 4 palabras / 80 chars | Re-rutear a exact del `term`; si también supera exact → `limit_violation`. |
| Candidato `confidence=="low"` | NO autopush (gate). `held_low_confidence[]`. Vuelve por `MODE=approved`. |
| Candidato sin `confidence` (snapshot viejo) | Tratar como `high` → se pushea. |
| MODE=approved: término que cae en protected/own/ASIN/special | Redes de seguridad SÍ valen — se descarta/retiene (solo el gate se saltea). |
| MODE=approved: término "no aprender" | Se pushea hoy pero NO se agrega al perfil. |
| Re-run el mismo día | Idempotente: saltea `(term,match,line)` del recibo; mergea lo nuevo. |
| Preview SHURQ expiró (>5 min) | Re-preview + confirm inmediato (nunca acumules previews). |
| Multi-marketplace | 1 corrida por config; el brand ya distingue US/CA. |

---

## Migración AdLabs → SHURQ (referencia rápida)
| AdLabs (V2) | SHURQ (V3) |
|---|---|
| `adlabs_team_id` + `adlabs_profile_id` | `shurq_account_id` (int) + `mkp_id` |
| `start_chat_session` + `read_resource` | (nada — sin sesión) |
| `get_entity_data(ad_group, CONTAINS_ASINS, STATE=ENABLED)` → reference | `list_product_ads` filtrado por `amazon_asin`+`ad_status=ENABLED`+`api_type∈{sp,sb}`+no-Scavenger |
| `read(reference)` | leer `data[]` del `list_product_ads` (paginar) |
| `create_entities(negative_targeting, keywords, match_types)` → preview_id | `add_negative_keyword(..., match_type="phrase"/"exact", level="ad_group")` → action_id (por keyword×ad group) |
| `create_entities(negative_targeting_apply, preview_id, note)` | `confirm_action(action_id)` + `get_action_status(account_id, action_id)` |
| `AD_GROUP_NEGATIVE_PHRASE/EXACT` | `match_type="phrase"/"exact"`, `level="ad_group"` |
| `note` obligatorio en el apply | rastro en el recibo de Supabase (`action_ids`, `source_terms`) |
