---
name: daily-negatives-autopush
description: >
  El PUENTE automático del negative targeting diario. Toma el snapshot que dejó
  daily-negatives-supabase (dashboard_snapshots, tipo='negatives') y, SIN selección ni
  copy-paste, empuja cada candidato irrelevante como negativo a AdLabs, auto-derivando el
  destino desde el producto/línea del candidato: todos los ad groups ENABLED (SP + SB) que
  anuncian los ASINs de esa línea, menos Scavenger. Empuja SOLO keywords: en phrase negativiza el
  ROOT/raíz del snapshot (ej. "re u", no "re u hair serum"); en exact, el término. Los ASINs
  (términos b0…) NUNCA se auto-negativizan: van a un bucket
  asins_skipped para revisar a mano. Deja recibo en Supabase (tipo='negatives_push') para
  auditoría e idempotencia. NUNCA pushea candidatos sin producto resoluble ("General (sin
  asignar)"): quedan para el dashboard/manual. Modos: 'run' (default) y 'dry-run'. Trigger:
  "autopush negatives para [Brand]", "run daily-negatives-autopush for [Brand]", o una Routine.
  NO identifica términos ni hace harvesting positivo.
---

# Daily Negatives — Autopush (snapshot → AdLabs, automático)

**Versión:** V1.0 (2026-08-30). Es el eslabón que faltaba entre **identificar** y **aplicar**.
`daily-negatives-supabase` ya decide QUÉ negativizar (y con qué match) y lo deja en el snapshot
del día. Este skill lo **empuja solo**: deriva el destino desde el producto de cada candidato y
crea + aplica los negativos vía el MCP de AdLabs, sin que toques el dashboard.

**Respondé a Nacho en español.**

> **Relación con los otros skills:**
> - `daily-negatives-supabase` (run) → escribe el snapshot. **Corre ANTES.**
> - **este skill** → lee el snapshot y pushea. **Corre DESPUÉS** (Routine escalonada).
> - `weekly-negatives-review` → la red de seguridad semanal que revisa lo negado.
> - `adlabs-push-negatives` → la mecánica de push manual/ad-hoc. **Este skill reusa su Paso 3–7.**
> El dashboard (Master Dashboard tab Negatives) deja de ser el portón y pasa a ser tu
> superficie de auditoría: seguís viendo todo, pero ya no tenés que seleccionar ni copiar.

---

## Reglas de oro (no negociables — heredadas de adlabs-push-negatives)

1. **Destino explícito SIEMPRE, nunca "a toda la cuenta".** Acá el destino no lo tipeás vos: lo
   deriva el skill desde el `product` (línea/parent) de cada candidato. Pero la red de seguridad
   se mantiene: **si un candidato no tiene producto resoluble a un set de ASINs concreto
   (`product = "General (sin asignar)"`, o la línea no matchea `managed_asins`), NO se pushea.**
   Queda en el snapshot para el dashboard/manual y se reporta como "retenido". Un destino vacío
   jamás significa "todas".
2. **Nivel = AD GROUP** (`AD_GROUP_NEGATIVE_*`). Sirve para SP y SB, y es quirúrgico.
3. **Match type + QUÉ texto se pushea (clave):** el snapshot fija el match; el modelo no lo re-decide.
   - `match:"phrase"` → `AD_GROUP_NEGATIVE_PHRASE`, y **se pushea el `root`, NO el término completo.** El
     `root` es la raíz limpia (marca/competidor/familia) que el identificador ya extrajo, ej.
     `re u hair serum` → `root:"re u"`. Negar `re u` como phrase bloquea TODAS las búsquedas con "re u"
     (re u serum, re u regrow…) **sin** tocar genéricos como "hair serum" — que es justo lo correcto. Si por
     algún motivo `root` viene vacío, recién ahí pushear el `term` como phrase (fallback).
   - `match:"exact"` → `AD_GROUP_NEGATIVE_EXACT`, y se pushea el **`term` completo** (root vacío en exact).
   - No hay product target acá (regla 10: ASINs no se pushean).
   > **Bonus:** pushear el root también evita violar el límite de Amazon de **4 palabras en phrase**
   > (ej. `force facto hair growth excelerator` = 5 palabras violaría; el root `force facto` = 2, OK).
4. **Auto-apply.** El flujo va derecho preview → resumen → apply, pero SIEMPRE imprime el resumen
   exacto (qué línea, qué ad groups, cuántos negativos) antes de aplicar. `dry-run` frena antes del apply.
5. **Solo ENABLED.** Toda fetch de ad groups lleva `CAMPAIGN_STATE=ENABLED` + `AD_GROUP_STATE=ENABLED`.
6. **Excluir Scavenger SIEMPRE** (regla de Nacho): descartá del destino toda campaña cuyo nombre
   contenga `scavenger` (case-insensitive). Las Scavenger son de descubrimiento intencional.
7. **`note` significativa en cada apply** para el audit log de AdLabs.
8. **Nunca negativices marca propia ni `managed_asins` del cliente.** El snapshot ya los excluye,
   pero re-chequeá como red: un término/ASIN que sea del propio cliente se descarta y se reporta.
9. **Idempotencia.** Si ya se pusheó hoy (hay recibo `negatives_push` del día), saltear los
   candidatos ya aplicados. Re-runs del mismo día no duplican.
10. **NUNCA auto-negativices ASINs (pedido de Nacho).** Cualquier candidato `kind=="asin"` (término que
   matchea `^b0[a-z0-9]{8}$`) NO se pushea — va a `asins_skipped[]` para que Nacho lo revise a mano en el
   informe. El autopush crea **solo** keyword-negatives (phrase/exact), nunca negative product targets.
11. **Términos con caracteres especiales NO se pueden negar (pedido de Nacho).** Si un keyword contiene
   cualquier carácter fuera del set seguro `[A-Za-z0-9 '&-]` (o sea: **cualquier char no-ASCII** — acentos,
   `ą`, `ł`, `ñ`, emojis… — **o** símbolos como coma, `/`, `+`, `%`, `"`), Amazon lo rechaza → **NO se pushea.**
   Sumalo a `dropped[]` con `reason:"special_char"` para que quede registrado. Ej.: `kofeiną, kopexilem`
   (coma + `ą`) → no negable. (Hyphen `-`, apóstrofo `'` y `&` sí se permiten: son comunes en keywords reales.)

---

## Constants

```
Fuente de datos:  Supabase (conector MCP, proyecto POD 66 - Organization)
  Config cliente:      public.clients (config JSONB) — brand_name, adlabs_team_id, adlabs_profile_id, managed_asins
  Perfil relevancia:   public.relevance_profiles (profile JSONB) — protected_relevant (red de seguridad)
  Snapshot del día:    public.dashboard_snapshots, tipo='negatives', fecha=HOY(ART) — lo escribe daily-negatives-supabase
  Recibo de push:      public.dashboard_snapshots, tipo='negatives_push', fecha=HOY(ART) — lo escribe ESTE skill
Timezone:  America/Argentina/Buenos_Aires (ART)  — anclar SIEMPRE a ART, no a date.today() (Routines corren en UTC)
AdLabs:    entities ad_group / advertised_product / negative_targeting. team_id/profile_id del config.
```

---

## Startup (siempre)

En paralelo:
1. AdLabs: `start_chat_session()` → guardá `chat_session_id` (pasalo en TODAS las llamadas AdLabs).
   Luego `read_resource(uri="adlabs://instructions", chat_session_id=...)`.
2. Supabase: leé el `config` del cliente (ver Step 1).

Si no tenés fresca la mecánica de creación de negativos, leé
`read_resource(uri="adlabs://docs/create_actions/negative_targeting")` y `.../negative_targeting_apply`.
La mecánica ya está resumida en `adlabs-push-negatives` (sección "Mecánica AdLabs") — no re-leas si la tenés clara.

---

## MODE = run  (default — un cliente)

### Step 1 — Resolver cliente + config (Supabase)
Igual que `daily-negatives-supabase` Step 1:
```sql
select brand, active, config from public.clients
where lower(brand)=lower('<requested_brand>')
   or exists (select 1 from jsonb_array_elements_text(coalesce(config->'alternative_names','[]'::jsonb)) a
              where lower(a)=lower('<requested_brand>'));
```
Zero rows / `config` null → STOP y listá `select brand from public.clients where active`. Tomá `cfg = config`.
Requeridos: `brand_name`, `adlabs_team_id`, `adlabs_profile_id`, `managed_asins`. Multi-marketplace = 1 corrida por config.

> **⚠️ Diagnóstico honesto de config vs. error de AdLabs (aprendido 2026-08-31, caso BloomTrail):**
> Chequeá los requeridos **contra el config de Supabase** y reportá exactamente lo que ves:
> - Un campo **realmente** ausente/null → `reason:"config incompleto: falta <campo>"`, saltá ese cliente.
> - Si `adlabs_team_id` y `adlabs_profile_id` **están presentes**, entonces **NUNCA** concluyas "profile no
>   configurado" / "cuenta no conectada" si después una llamada a AdLabs falla. Un fallo del fetch de AdLabs
>   (timeout, rate-limit por correr 5 clientes seguidos, sync en curso, reference expirada) es **transitorio**,
>   no un problema de config. En ese caso: **reintentá el cliente 1 vez**; si vuelve a fallar, reportá el
>   **error real de AdLabs** (`reason:"adlabs_error: <mensaje>"`), no lo aplicado queda pendiente para la
>   próxima corrida (idempotente), y **seguís con los demás clientes**. No inventes causas de config.

Armá el índice de líneas del cliente desde `cfg.managed_asins`:
- `line_asins`: mapa `línea/parent → [asins]`. Derivá la línea de cada ASIN por `product_line` (si existe) o
  colapsando children a su parent (`parent_asin`), igual que `daily-negatives-supabase` Step 4b.
- `own_asins`: set de TODOS los ASINs del cliente (para la red de seguridad de la regla 8).

### Step 2 — Leer el snapshot del día
```sql
select datos from public.dashboard_snapshots
where cliente = '<brand_name>' and tipo = 'negatives' and fecha = '<HOY-ART YYYY-MM-DD>';
```
- Zero rows → **STOP suave**: `No hay snapshot de negatives de hoy para {brand}. Corré daily-negatives-supabase primero.`
- `datos.day.candidates` vacío → `Sin candidatos hoy para {brand}, nada que pushear.` Fin.
- `datos.client.status == "datafail"` → reportá y fin (no hubo data ayer).

### Step 3 — Leer el recibo de push de hoy (idempotencia)
```sql
select datos from public.dashboard_snapshots
where cliente = '<brand_name>' and tipo = 'negatives_push' and fecha = '<HOY-ART>';
```
Si existe, armá `already_pushed` = set de `(term, match, line)` ya aplicados (de `datos.applied[]`). En Step 6 se saltean.
Si no existe, `already_pushed = {}`. **Clave por línea (no solo term+match):** un mismo término puede negarse en
dos líneas distintas el mismo día; incluir `line` evita que un re-run parcial (falló después de la línea A,
antes de la B) saltee la línea B por error.

### Step 4 — Preparar candidatos + red de seguridad
Cada candidato del snapshot trae `{term, clicks, spend, match, root, reason, kind, product, origin_campaign, origin_ad_group}`
(los dos `origin_*` los persiste `daily-negatives-supabase` Step 5; si un snapshot viejo no los trae, quedan `""`).

> **`push_text` — QUÉ se negativiza por candidato (regla 3):** para `match=="phrase"` → `push_text = root`
> (si `root` está vacío, fallback `push_text = term`); para `match=="exact"` → `push_text = term`. **Todo lo
> de abajo (caracteres especiales, límites, dedup, idempotencia, lo que se pushea y lo que se reporta) opera
> sobre `push_text`, NO sobre el `term` crudo.** Guardá el/los `term` originales como `source_terms` para el recibo.

Recorré `candidates` y clasificá cada uno **en este orden** (el primero que aplica gana):
1. **Red de marca propia (regla 8):** si `kind=="asin"` y el ASIN ∈ `own_asins` → **descartar** (self-targeting).
   Si `kind=="keyword"` y el término es claramente marca propia → **descartar**. Sumar a `dropped[]` (`reason:"own_brand"`).
2. **Red de protected_relevant (regla — última palabra):** cargá `protected_relevant` del perfil
   (`select profile->'protected_relevant' from public.relevance_profiles where brand='<brand_name>'`).
   Si el término matchea (igualdad o contención/wildcard) una excepción protegida → **descartar**
   (`dropped[]`, `reason:"protected_relevant"`). (No debería aparecer si el snapshot está sano; red final.)
3. **ASINs NUNCA se auto-negativizan (regla 10 — pedido de Nacho):** si `kind=="asin"` (el término matchea
   `^b0[a-z0-9]{8}$`) → **NO pushear.** Sumalo a `asins_skipped[]` con TODO el contexto (`term`, `clicks`,
   `spend`, `product`, `origin_campaign`, `origin_ad_group`, `reason`) para que Nacho lo vea en el informe y
   decida a mano. **El autopush pushea SOLO keywords.**
4. **Caracteres especiales NO negables (regla 11)** — ya solo keywords: si el **`push_text`** tiene algún char
   fuera de `[A-Za-z0-9 '&-]` (no-ASCII o símbolos como coma/`/`/`+`/`%`/`"`) → **NO pushear.** Sumalo a
   `dropped[]` con `reason:"special_char"`. Chequealo ANTES de agrupar/validar límites. (Chequear el root y no
   el término suele salvar casos: si `re u kofeiną` tiene root `re u`, el root es limpio y sí se puede negar.)
5. **Retención por producto no resoluble (regla 1)** — keywords limpias: si `product == "General (sin
   asignar)"` o la línea no está en `line_asins` → **retener** (no pushear). Sumalo a `held[]` con TODO el
   contexto para que Nacho decida: `term`, `clicks`, `spend`, `match`, `kind`, `origin_campaign`,
   `origin_ad_group`, `reason`, y una **`suggested_line`** (best-effort): matcheá `origin_campaign`/
   `origin_ad_group` contra los nombres de línea de `line_asins`; si no hay match claro → `suggested_line: null`.
   NUNCA pushees por la sugerencia — es solo para el informe.
6. **Idempotencia:** si `(push_text, match, line)` ∈ `already_pushed` → saltear (ya aplicado hoy para esa línea).
Los keywords que sobreviven se agrupan por **línea de producto** (`product`) → `push_groups[linea] = {phrase[], exact[]}`
(**sin ASINs** — nunca), donde cada lista tiene los `push_text` **deduplicados** (case-insensitive):
- `phrase[]` = roots únicos de los candidatos phrase de esa línea (ej. `re u hair serum` + `re u serum` → un solo `re u`).
- `exact[]` = términos de los candidatos exact.
Por cada `push_text` conservá los `source_terms` (los términos originales que lo generaron) para el recibo.

### Step 5 — Resolver destino por línea + crear previews (reusa adlabs-push-negatives Paso 3–5)
Por cada `linea` en `push_groups`:
1. `asins_linea = line_asins[linea]` (los ASINs de esa línea del cliente).
2. **Fetch ad groups destino** (mode C de adlabs-push-negatives — CONTAINS_ASINS):
```
get_entity_data(entity_type="ad_group", team_id, profile_id, chat_session_id,
  filters=[ {CONTAINS_ASINS IN asins_linea}, CAMPAIGN_STATE=ENABLED, AD_GROUP_STATE=ENABLED, DATE=<últimos 14 días> ])
```
   Devuelve una reference `mcp://data/...`. **`read(reference=...)`** para ver los ad groups resueltos.
3. **Excluir Scavenger (regla 6):** si la reference incluye campañas con `scavenger` en el nombre, re-fetcheá
   agregando `{"key":"CAMPAIGN_NAME_NOT","conditions":[{"operator":"NOT_LIKE","values":["Scavenger"]}]}` (y variantes
   de capitalización que veas), o filtrá las filas Scavenger antes de crear el preview. Reportá cuántas excluiste.
4. **Reference vacía (0 ad groups ENABLED que anuncian la línea):** NO pushees. Sumá la línea a `held_no_dest[]`
   con motivo "sin ad groups ENABLED que anuncien esta línea". (Nunca apliques sobre reference vacía.)
5. **Validar `push_text` con FALLBACK a exact (NO drop):** ≤80 chars; PHRASE ≤4 palabras; EXACT ≤10 palabras.
   - **PHRASE que supera 4 palabras (o 80 chars):** **NO descartar.** Re-rutealo a **EXACT del `term` completo**
     (movelo de `phrase[]` a `exact[]`, con `push_text = term`). Solo si el `term` TAMBIÉN supera exact
     (>10 palabras o >80 chars) → drop `reason:"limit_violation"`. Motivo (pedido de Nacho): mejor negar el
     waste como exact que perderlo por el límite de phrase.
   - **EXACT que supera 10 palabras / 80 chars:** drop `reason:"limit_violation"` (raro).
   Los de caracteres especiales ya se sacaron en Step 4 (regla 11). (Como en phrase pusheás el root, casi nunca
   rozás el límite; y si lo rozás, cae a exact en vez de perderse.)
   > **Nota (visto en el dry-run de Masofta):** algunos ad groups del set CONTAINS_ASINS son de **product
   > targeting** (no keyword). AdLabs **saltea solo** los keyword-negatives ahí ("ad group targets products")
   > y lo reporta en el preview/apply. No es error: por eso los negativos efectivos pueden ser < keywords ×
   > ad groups. Contá los `skipped` del recibo del preview.
6. **Crear previews** (solo keywords — los ASINs NO se pushean, regla 10). Las keywords son los **`push_text`**
   (roots para phrase, términos para exact):
   - phrase → `create_entities(negative_targeting, reference=<ref>, keywords=phrase[], match_types=["AD_GROUP_NEGATIVE_PHRASE"])`  (ej. `["re u","force facto","sisley"]`, NO `"re u hair serum"`)
   - exact → `create_entities(negative_targeting, reference=<ref>, keywords=exact[], match_types=["AD_GROUP_NEGATIVE_EXACT"])`
   Cada uno devuelve un `preview_id` + link "View in AdLabs". Conteo esperado = ad groups × match_types × keywords
   (producto cartesiano; los ya-existentes se saltean recién en el apply). **Nunca** crees previews de product
   target (`AD_GROUP_NEGATIVE_PRODUCT_TARGET`) en el autopush.

### Step 6 — Resumen (imprimir SIEMPRE) + apply
Imprimí, por línea, el destino resuelto y los conteos antes de aplicar. Ejemplo:
> **Autopush {brand} — {fecha}:**
> - Línea **Hair Growth Serum** → 8 ad groups ENABLED (SP+SB) que anuncian sus 2 ASINs (2 Scavenger excluidas)
>   - 5 kw PHRASE × 8 ad groups = 40 · 3 kw EXACT × 8 = 24  (previews #a/#b)
> - Línea **Body Glue** → 3 ad groups · 2 kw EXACT × 3 = 6 (preview #c)
> - **ASINs (no auto-negados):** 3 términos b0… → quedan para revisar a mano en el informe.
> - **Retenidos (no pusheados):** 4 keywords sin producto resoluble → quedan para el dashboard.

**Si modo = `dry-run`:** parás acá. Mostrá los links "View in AdLabs" y los conteos. No apliques.

**Si modo = `run` (default):** aplicá cada preview:
```
create_entities(entity_type="negative_targeting_apply", team_id, profile_id, chat_session_id,
  preview_id=<id>,
  note="Autopush diario: <N> negativos AD_GROUP (<match>) en línea <linea> (<M> ad groups) — daily-negatives-autopush, <fecha ART>")
```

### Step 7 — Recibo de push a Supabase (auditoría + idempotencia + insumo del weekly)
Construí `datos` schema `negatives-push-v1` y upserteá:
```json
{ "schema":"negatives-push-v1", "generated_at_iso":"<ISO ART>",
  "brand":"<brand_name>", "marketplace":"US", "currency_prefix":"$",
  "date_iso":"<HOY-ART>", "data_window":"<ayer, del snapshot>",
  "summary":{"applied_terms":N,"created":N,"skipped_existing":N,"held":N,"asins_skipped":N,"dropped":N,
             "held_spend":F,"asins_spend":F,"ad_groups_touched":N,"lines":N},
  "applied":[{"term":"<push_text: root en phrase / término en exact>","source_terms":["<término(s) original(es)>"],
              "clicks":N,"spend":F,"match":"phrase|exact","kind":"keyword",
              "line":"...","ad_groups":N,"created":N,"skipped":N,"preview_id":"..."}],
  "held":[{"term":"...","clicks":N,"spend":F,"match":"phrase|exact","kind":"keyword",
           "product":"General (sin asignar)","reason":"General (sin asignar) | sin ad groups ENABLED | ...",
           "origin_campaign":"...","origin_ad_group":"...","suggested_line":"<linea>|null"}],
  "asins_skipped":[{"term":"b0xxxxxxxx","clicks":N,"spend":F,"kind":"asin","product":"<linea|General>",
                    "origin_campaign":"...","origin_ad_group":"...","reason":"ASIN - no auto-negado (regla de Nacho)"}],
  "dropped":[{"term":"...","reason":"own_brand | protected_relevant | special_char | limit_violation"}] }
```
`held_spend`/`asins_spend` = suma de `spend` de retenidos / de ASINs skippeados (para priorizar). `applied`/`held`
son **solo keywords** (`kind:"keyword"`); los ASINs viven en `asins_skipped[]`. En `applied`, `term` es el
**`push_text`** (el root en phrase, ej. `re u`), y `clicks`/`spend` = **suma de los `source_terms`** que
colapsaron en ese root. El tab **Push** del dashboard muestra `term` (o sea el root que realmente se negó) —
los `source_terms` quedan en el recibo para auditoría. Ver `skills/push-report/` para el composer y el template.
```sql
insert into public.dashboard_snapshots (cliente, tipo, fecha, datos)
values ('<brand_name>', 'negatives_push', '<HOY-ART>', $push$<datos>$push$::jsonb)
on conflict (cliente, tipo, fecha) do update set datos = excluded.datos, actualizado = now();
```
> **Merge en re-run:** si ya había recibo hoy, MERGEá `applied[]` (no lo pises) — sumá solo lo nuevo de este run.

Confirmá:
`Autopush {brand} — {fecha}: {created} keyword-negatives creados en {ad_groups_touched} ad groups ({lines} líneas), {skipped_existing} ya existían, {asins_skipped} ASINs no auto-negados (para revisar), {held} retenidos, {dropped} descartados.`

---

## MODE = dry-run
Idéntico hasta el Step 6, **sin aplicar** (no llama `negative_targeting_apply`). Útil para estrenar la
automatización o revisar el destino sin tocar Amazon.
- **Por default (dry-run ad-hoc):** no escribe recibo; solo imprime el resumen + los links "View in AdLabs".
- **Dry-run + recibo (para poblar el tab Push):** si te lo piden (típicamente la Routine de estreno), **SÍ**
  escribe el recibo `negatives_push` con `summary.mode:"dry-run"` y **`applied[]` = lo que HABRÍA creado**
  (término, match, línea, `ad_groups`, `created` = conteo del preview), más `held`/`asins_skipped`/`dropped`
  completos. Así el dashboard muestra el plan del día sin haber aplicado nada. El conteo `created` sale del
  preview (contá los `skipped` de PT ad groups). Cuando pases a apply real, el mismo recibo se escribe sin
  el flag `mode`.
  > **⚠️ Caveat del `created` en dry-run:** el conteo del preview es el producto cartesiano
  > (keywords × match × ad groups) y **NO descuenta los negativos que ya existen** — la dedup contra los
  > existentes recién ocurre en el apply. Así que en dry-run `created` **sobre-estima** lo que apply
  > realmente crearía (el apply reporta muchos `skipped_existing`). Interpretá el número de dry-run como
  > "techo / candidatos a crear", no como el neto final.

---

## Scheduling (Routines de nube — las crea Nacho, NO este skill)
- **Feeder autopush — batches por OFFSET** (mismo patrón que las Routines "Daily Negatives"): una Routine
  por offset, cada una procesa 5 clientes (`select brand from public.clients where active=true order by brand
  limit 5 offset <N>`), con el **mismo prompt** cambiando solo `<N>` (0/5/10/15/…). Cantidad de Routines =
  ceil(clientes_activos/5). Corren **después** del identificador y **antes** del composer (ej. identificador
  06:00–06:30 ART, autopush 07:30–07:45 ART, composer 08:30 ART). Connectors **Supabase + Adlabs**, sesión
  nueva por corrida, sin repo. Los prompts exactos (dry-run y apply) están en `skills/ROUTINES.md`.
- **Estrenar en dry-run** (escribe el recibo con `mode='dry-run'` para poblar el tab Push, sin aplicar), y
  pasar a apply cambiando el prompt cuando esté validado.
- Multi-marketplace = ya cubierto (cada CA es su propio `brand`, entra en el orden alfabético del offset).
- **Orden importa:** si el autopush corre y no hay snapshot del día (identificador falló/atrasado), hace STOP
  suave y no pushea nada — seguro por diseño.

---

## Edge cases
| Situación | Comportamiento |
|---|---|
| No hay snapshot de negatives hoy | STOP suave, no pushea. "Corré daily-negatives-supabase primero." |
| Snapshot con candidates:[] | Nada que pushear. Fin limpio. |
| Candidato `kind=="asin"` (término b0…) | NUNCA se pushea (regla 10). Va a `asins_skipped[]` para revisar a mano. |
| Candidato `product = "General (sin asignar)"` (keyword) | RETENER (no push). Queda para el dashboard. Reportado en `held`. |
| Línea sin ad groups ENABLED que la anuncien | RETENER esa línea (reference vacía). Nunca aplicar sobre 0 filas. |
| Fetch de AdLabs falla para un cliente (timeout/rate-limit/sync/reference expirada) | Reintentar 1 vez; si sigue, `reason:"adlabs_error"`, seguir con los demás. **NUNCA** reportarlo como "profile no configurado" si el `adlabs_profile_id` está en el config. |
| Config con `adlabs_profile_id`/`adlabs_team_id` ausente o null | `reason:"config incompleto: falta <campo>"`, saltar ese cliente (eso SÍ es problema de config). |
| Campaña Scavenger en el destino | Excluida (regla 6). Reportar cuántas. |
| Término/ASIN de marca propia o managed_asins | Descartar (red regla 8). Reportado en `dropped`. |
| Término en protected_relevant | Descartar (red final). Reportado en `dropped`. |
| Keyword con caracteres especiales (no-ASCII/coma/símbolos) | NO negable (regla 11). `dropped` con `reason:"special_char"`. |
| Ad group de product targeting en el set CONTAINS_ASINS | AdLabs saltea solo el keyword-negative ahí ("ad group targets products"). Contar los `skipped` del preview. |
| Re-run el mismo día | Idempotente: saltea `(term,match)` ya en el recibo; mergea lo nuevo. |
| Keyword viola límites (80/4/10) | Se saltea en el apply. Avisar cuál. |
| AdLabs reference expiró | Re-fetcheá el ad_group (las references expiran con la sesión). |
| Multi-marketplace | 1 corrida por config; el brand ya distingue US/CA. |
