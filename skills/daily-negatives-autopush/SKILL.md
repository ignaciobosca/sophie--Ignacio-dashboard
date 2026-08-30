---
name: daily-negatives-autopush
description: >
  El PUENTE automático del negative targeting diario. Toma el snapshot que dejó
  daily-negatives-supabase (dashboard_snapshots, tipo='negatives') y, SIN selección ni
  copy-paste, empuja cada candidato irrelevante como negativo a AdLabs, auto-derivando el
  destino desde el producto/línea del candidato: todos los ad groups ENABLED (SP + SB) que
  anuncian los ASINs de esa línea, menos Scavenger. Keywords al match del snapshot
  (phrase/exact); ASINs como product target. Deja recibo en Supabase (tipo='negatives_push')
  para auditoría e idempotencia. NUNCA pushea candidatos sin producto resoluble ("General
  (sin asignar)"): quedan para el dashboard/manual. Reusa la mecánica de adlabs-push-negatives.
  Modos: 'run' (default) y 'dry-run'. Trigger: "autopush negatives para [Brand]", "empujá los
  negativos de hoy de [Brand]", "run daily-negatives-autopush for [Brand]", o una Routine. NO
  identifica términos ni hace harvesting positivo.
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
3. **Match type = el que trae el snapshot por candidato.** `match:"phrase"` → `AD_GROUP_NEGATIVE_PHRASE`;
   `match:"exact"` → `AD_GROUP_NEGATIVE_EXACT`; `kind:"asin"` → `AD_GROUP_NEGATIVE_PRODUCT_TARGET`.
   No lo re-decide el modelo: el snapshot ya lo fijó (con el toggle histórico de Nacho aprendido).
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
Si existe, armá `already_pushed` = set de `(term, match)` ya aplicados (de `datos.applied[]`). En Step 6 se saltean.
Si no existe, `already_pushed = {}`.

### Step 4 — Preparar candidatos + red de seguridad
Cada candidato del snapshot trae `{term, clicks, spend, match, root, reason, kind, product, origin_campaign, origin_ad_group}`
(los dos `origin_*` los persiste `daily-negatives-supabase` Step 5; si un snapshot viejo no los trae, quedan `""`).
Recorré `candidates`. Por cada uno:
1. **Retención por producto no resoluble (regla 1):** si `product == "General (sin asignar)"` o la línea no
   está en `line_asins` → **retener** (no pushear). Sumalo a `held[]` con TODO el contexto para que Nacho
   decida: `term`, `clicks`, `spend`, `match`, `kind`, `origin_campaign`, `origin_ad_group`, `reason`, y una
   **`suggested_line`** (best-effort): matcheá `origin_campaign`/`origin_ad_group` contra los nombres de línea de
   `line_asins` (substring/semántico); si no hay match claro → `suggested_line: null`. NUNCA pushees por la
   sugerencia — es solo para que Nacho la vea en el informe y decida.
2. **Red de marca propia (regla 8):** si `kind=="asin"` y el ASIN ∈ `own_asins` → descartar (self-targeting).
   Si `kind=="keyword"` y el término es claramente marca propia → descartar. Sumar a `dropped_own[]`.
3. **Red de protected_relevant (regla — última palabra):** cargá `protected_relevant` del perfil
   (`select profile->'protected_relevant' from public.relevance_profiles where brand='<brand_name>'`).
   Si el término matchea (igualdad o contención/wildcard) una excepción protegida → **descartar** y sumar a
   `dropped_protected[]`. (No debería aparecer si el snapshot está sano, pero es la red final.)
4. **Idempotencia:** si `(term, match)` ∈ `already_pushed` → saltear (ya aplicado hoy).
Los que sobreviven se agrupan por **línea de producto** (`product`) → `push_groups[linea] = {keywords_phrase[], keywords_exact[], asins[]}`.

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
5. **Validar términos** (límites Amazon): ≤80 chars; PHRASE ≤4 palabras; EXACT ≤10 palabras. El que viole se
   saltea en el apply (avisalo). Deduplicá.
6. **Crear previews** (hasta 3 por línea):
   - keywords phrase → `create_entities(negative_targeting, reference=<ref>, keywords=[...phrase...], match_types=["AD_GROUP_NEGATIVE_PHRASE"])`
   - keywords exact → `create_entities(negative_targeting, reference=<ref>, keywords=[...exact...], match_types=["AD_GROUP_NEGATIVE_EXACT"])`
   - asins → `create_entities(negative_targeting, reference=<ref>, expressions=["asin=\"B0...\"", ...], match_types=["AD_GROUP_NEGATIVE_PRODUCT_TARGET"])`
   Cada uno devuelve un `preview_id` + link "View in AdLabs". Conteo esperado = ad groups × match_types × términos
   (producto cartesiano; los ya-existentes se saltean recién en el apply).

### Step 6 — Resumen (imprimir SIEMPRE) + apply
Imprimí, por línea, el destino resuelto y los conteos antes de aplicar. Ejemplo:
> **Autopush {brand} — {fecha}:**
> - Línea **Hair Growth Serum** → 8 ad groups ENABLED (SP+SB) que anuncian sus 2 ASINs (2 Scavenger excluidas)
>   - 5 kw PHRASE × 8 ad groups = 40 · 3 kw EXACT × 8 = 24 · 1 ASIN PT × 8 = 8  (previews #a/#b/#c)
> - Línea **Body Glue** → 3 ad groups · 2 kw EXACT × 3 = 6 (preview #d)
> - **Retenidos (no pusheados):** 4 candidatos sin producto resoluble → quedan para el dashboard.

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
  "summary":{"applied_terms":N,"created":N,"skipped_existing":N,"held":N,"dropped":N,
             "held_spend":F,"ad_groups_touched":N,"lines":N},
  "applied":[{"term":"...","clicks":N,"spend":F,"match":"phrase|exact|product_target","kind":"keyword|asin",
              "line":"...","ad_groups":N,"created":N,"skipped":N,"preview_id":"..."}],
  "held":[{"term":"...","clicks":N,"spend":F,"match":"phrase|exact","kind":"keyword|asin",
           "product":"General (sin asignar)","reason":"General (sin asignar) | sin ad groups ENABLED | ...",
           "origin_campaign":"...","origin_ad_group":"...","suggested_line":"<linea>|null"}],
  "dropped":[{"term":"...","reason":"own_brand | protected_relevant | limit_violation"}] }
```
`held_spend` = suma de `spend` de los retenidos (para priorizar cuáles resolver primero). El informe diario del
Master Dashboard (tab **Push**) lee estas filas — ver `skills/push-report/` para el composer y el template.
```sql
insert into public.dashboard_snapshots (cliente, tipo, fecha, datos)
values ('<brand_name>', 'negatives_push', '<HOY-ART>', $push$<datos>$push$::jsonb)
on conflict (cliente, tipo, fecha) do update set datos = excluded.datos, actualizado = now();
```
> **Merge en re-run:** si ya había recibo hoy, MERGEá `applied[]` (no lo pises) — sumá solo lo nuevo de este run.

Confirmá:
`Autopush {brand} — {fecha}: {created} negativos creados en {ad_groups_touched} ad groups ({lines} líneas), {skipped_existing} ya existían, {held} retenidos, {dropped} descartados por red de seguridad.`

---

## MODE = dry-run
Idéntico hasta el Step 6, sin aplicar. Útil para la primera corrida de un cliente nuevo, o para revisar el
destino que derivó el skill sin tocar Amazon. No escribe recibo (o lo escribe con `summary.mode:"dry-run"` y
`applied:[]` si Nacho quiere ver qué HABRÍA hecho — por default no escribe).

---

## Scheduling (Routines de nube — crear aparte, NO en este skill)
- **Feeder autopush:** una Routine por cliente activo, **después** del feeder de `daily-negatives-supabase`
  (que corre a mediodía ART). Escaloná +15 min respecto del identificador para que el snapshot ya esté escrito
  (ej. identificador 12:00–12:30, autopush 12:45–13:15). Prompt: `Run daily-negatives-autopush for {brand_name}`.
  Connectors: **Supabase + Adlabs** (+ SHURQ si se quiere el fallback). Sin repo, sin carpeta local.
- Multi-marketplace = 1 Routine por config (cada CA es su propio `brand`).
- **Orden importa:** si el autopush corre y no hay snapshot del día (identificador falló/atrasado), hace STOP suave
  y no pushea nada — seguro por diseño.

---

## Edge cases
| Situación | Comportamiento |
|---|---|
| No hay snapshot de negatives hoy | STOP suave, no pushea. "Corré daily-negatives-supabase primero." |
| Snapshot con candidates:[] | Nada que pushear. Fin limpio. |
| Candidato `product = "General (sin asignar)"` | RETENER (no push). Queda para el dashboard. Reportado en `held`. |
| Línea sin ad groups ENABLED que la anuncien | RETENER esa línea (reference vacía). Nunca aplicar sobre 0 filas. |
| Campaña Scavenger en el destino | Excluida (regla 6). Reportar cuántas. |
| Término/ASIN de marca propia o managed_asins | Descartar (red regla 8). Reportado en `dropped`. |
| Término en protected_relevant | Descartar (red final). Reportado en `dropped`. |
| Re-run el mismo día | Idempotente: saltea `(term,match)` ya en el recibo; mergea lo nuevo. |
| Keyword viola límites (80/4/10) | Se saltea en el apply. Avisar cuál. |
| AdLabs reference expiró | Re-fetcheá el ad_group (las references expiran con la sesión). |
| Multi-marketplace | 1 corrida por config; el brand ya distingue US/CA. |
