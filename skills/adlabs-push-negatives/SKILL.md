---
name: adlabs-push-negatives
description: >
  Empuja y aplica términos/ASINs a negativizar directo en campañas de Amazon Ads vía el conector
  AdLabs. Pegás la lista y el destino, y el skill crea negativos a nivel AD GROUP (Exact/Phrase para
  keywords, Product Target para ASINs) y los aplica a Amazon (auto-apply). El
  destino puede ser una campaña/ad group nombrado, un patrón de nombre ("todas menos las que tienen
  X"), las que anuncian un ASIN/producto, o una categoría/tipo de producto ("las de jabones sólidos").
  NUNCA aplica a todo sin destino: si no das ni lista ni regla, para y pregunta. A diferencia de daily-negatives / negative-targeting (que solo
  IDENTIFICAN y arman listas para copiar), este hace el PUSH vía MCP. Trigger:
  "negativizá estos términos en [campaña]", "empujá/aplicá estos negativos en AdLabs", "aplicá esta
  lista en phrase a todas las campañas menos las que tienen X", "en exact a las que anuncian el ASIN
  B0…", o pegar términos/ASINs para cargarlos como negativos. NO usar para DESCUBRIR qué negativizar
  ni para harvesting positivo.
---

# AdLabs — Push Negatives (aplicar negativos a Amazon)

Tomás una lista de términos/ASINs que Nacho ya decidió negativizar y los **creás y aplicás
como negativos a nivel ad group** en campañas concretas de Amazon Ads vía el MCP de AdLabs.

Este skill es el eslabón que faltaba: `daily-negatives` y `negative-targeting` deciden
*qué* negativizar y arman listas para copiar a mano. Acá se hace el **push real** por API.

**Respondé a Nacho en español.** El contenido de instrucciones está en inglés/español mezclado
para el modelo, pero la conversación con Nacho es en español.

---

## Reglas de oro (no negociables)

1. **El destino tiene que ser explícito. NUNCA apliques "a todas" por defecto o por accidente.**
   El destino se puede expresar de dos formas, y ambas son válidas:
   - una **lista de nombres** de campaña/ad group, o
   - una **regla de selección** (patrón de nombre / exclusión, ASIN/producto anunciado, o categoría/
     tipo de producto — ver "Targeting modes").

   Si Nacho **no da ni una lista ni una regla** (p.ej. solo pega términos sin decir a dónde),
   **pará y preguntá** cuáles campañas/ad groups. Un destino faltante jamás significa "todas".
   Esta es la red de seguridad del modo auto-apply, y es sagrada porque un negativo mal dirigido
   apaga tráfico que sí convierte. Una regla amplia (ej. "todas menos SCAVENGER") **sí** es un
   destino explícito y se ejecuta — pero siempre resolviendo y mostrando el set exacto primero.

2. **Nivel = AD GROUP por defecto** (`AD_GROUP_NEGATIVE_*`). Es el default que eligió Nacho:
   sirve igual para Sponsored Products y Sponsored Brands, y es más quirúrgico que campaign-level.
   Solo usá `CAMPAIGN_NEGATIVE_*` si Nacho lo pide explícito (y ojo: campaign-level solo existe
   en SP, no en SB).

3. **Match types — respetá lo que pida Nacho; si no dice nada, usá el default:**
   - Si dice **"en phrase"** → solo `AD_GROUP_NEGATIVE_PHRASE`. Si dice **"en exact"** → solo
     `AD_GROUP_NEGATIVE_EXACT`. Si dice **"broad"** → `AD_GROUP_NEGATIVE_BROAD` (solo SP).
   - Default (no especifica) para keywords → `AD_GROUP_NEGATIVE_EXACT` + `AD_GROUP_NEGATIVE_PHRASE`.
   - ASINs (product targets) → siempre `AD_GROUP_NEGATIVE_PRODUCT_TARGET`.

4. **Auto-apply, también en bulk.** El flujo va derecho: preview → resumen → apply, sin pausa de
   confirmación, **incluso cuando el destino es una regla amplia** que toca muchos ad groups.
   PERO siempre imprimí el resumen exacto (qué campañas/ad groups resolvió, cuántos, qué match
   types, cuántos negativos) *antes* del apply, para que quede el registro y puedas frenarlo si
   ves algo raro. Excepción: **modo dry-run** (ver abajo) frena antes del apply.

5. **Solo ENABLED, siempre.** Toda fetch de ad groups lleva `CAMPAIGN_STATE=ENABLED` +
   `AD_GROUP_STATE=ENABLED`. Nunca apliques negativos a campañas/ad groups pausados o archivados
   (no tiene sentido gastar en negativizar lo que no corre, y achica el set). Única excepción:
   Nacho lo pide explícito ("incluí las pausadas").

6. **`note` significativa siempre.** El `apply` exige un `note` para el audit log. Usá algo como:
   `"MCP push: N negativos AD_GROUP (exact+phrase) en <campaña/ad groups> — pedido por Nacho, <fecha>"`.

---

## Modos

- **`apply`** (default): crea y aplica los negativos a Amazon.
- **`dry-run`**: hace todo hasta el preview (te da el conteo y el link "View in AdLabs")
  y **NO** aplica. Usalo cuando Nacho diga "dry run", "solo preview", "no lo apliques todavía",
  "mostrame qué se va a crear", "probá sin aplicar". También usalo vos por default la
  **primera vez** que corras contra una campaña nueva si tenés cualquier duda sobre el destino.

---

## Targeting modes (cómo Nacho nombra el destino)

Todos resuelven a una **reference de `ad_group`** (con `ad_group_id`), que es lo que necesitan
los negativos a nivel ad group. Se pueden combinar (ej. exclusión + ASIN). Siempre filtrá a
`CAMPAIGN_STATE=ENABLED` + `AD_GROUP_STATE=ENABLED` y agregá un `DATE` (últimos 14 días) porque
`ad_group` es entidad con métricas.

**A. Lista de nombres** — "en la campaña *SP - Exact - Core*", "en el ad group X".
   → filtro `CAMPAIGN_NAME` (LIKE) y/o `AD_GROUP_NAME` (LIKE), o `CAMPAIGN_ID`/`AD_GROUP_ID` si los tenés.

**B. Patrón de nombre / exclusión** — "todas las campañas menos las que tienen SCAVENGER",
   "las que empiezan con SP", "todas las que digan Brand".
   → **exclusión:** `CAMPAIGN_NAME_NOT` con operador `NOT_LIKE` (ej. value `"SCAVENGER"`).
   → **inclusión por patrón:** `CAMPAIGN_NAME` con `LIKE`.
   Ejemplo de filtro de exclusión:
   `{"key":"CAMPAIGN_NAME_NOT","conditions":[{"operator":"NOT_LIKE","values":["SCAVENGER"]}]}`
   Podés combinar varias exclusiones agregando condiciones con `"logical_operator":"AND"`.

**C. Producto anunciado (ASIN / feature product)** — "las campañas que anuncian el ASIN B0…",
   "donde tengo como feature product tal ASIN/producto".
   El ASIN vive a nivel ad group (los product ads están en el ad group), así que:
   - **Default (elegido por Nacho): solo los ad groups que anuncian ese ASIN.** Filtro `CONTAINS_ASINS`
     en la fetch de `ad_group`:
     `{"key":"CONTAINS_ASINS","conditions":[{"operator":"IN","values":["B07PGL2N7J"]}]}`
   - **Variante "toda la campaña"** (solo si Nacho lo pide explícito, ej. "a toda la campaña que
     anuncie X"): resolvé primero los ad groups con `CONTAINS_ASINS` (ref R1), después traé todos
     los ad groups de esas campañas pasando la ref como `CAMPAIGN_ID IN <R1>`
     (`CAMPAIGN_ID` acepta una reference URI `mcp://data/...` como `values`).
   - Si Nacho da un **nombre de producto o SKU** en vez de un ASIN, resolvé primero el/los ASIN
     vía `get_entity_data(entity_type="advertised_product", filters: PRODUCT_TITLE LIKE … / AD_SKU …)`
     y usá esos ASINs en `CONTAINS_ASINS`.

**D. Categoría / tipo de producto** — "las campañas de jabones sólidos", "solo las de tal línea".
   AdLabs **no** conoce categorías (solo ASINs, nombres y tags), así que hay que *definir* la
   categoría con una de estas fuentes, en orden de preferencia:
   1. **Nombre** — si las campañas/ad groups nombran el tipo (ej. "…Jabón Sólido…"), es un mode B
      (`CAMPAIGN_NAME LIKE`). El más limpio; probá esto primero.
   2. **Tag / Data Group** — si HEKAYA tiene un tag de producto para esa categoría, resolvé su ID con
      el tool `tags` y filtrá la fetch de `ad_group`/`advertised_product` por `PRODUCT_DATA_GROUP_ITEM`.
   3. **Resolver ASINs** — conseguí los ASINs de la categoría (por `advertised_product` con
      `PRODUCT_TITLE LIKE`, o cruzando con el catálogo de Sophie Hub) y usalos en `CONTAINS_ASINS`.

   **Matiz "SOLO contengan X"** (exclusividad): "contiene el ASIN/categoría" ≠ "solo contiene esa
   categoría". Si Nacho dice "que **solo** contengan jabones sólidos", después de traer los ad groups
   candidatos tenés que **descartar** los que además anuncian productos de otra categoría: revisá los
   ASINs anunciados de cada ad group (via `advertised_product` filtrado por esos ad groups, o
   `AD_GROUP_TOTAL_PRODUCTS`) y quedate solo con los exclusivos. Reportá cuántos descartaste por mezcla.

   **Regla clave del mode D:** como la categoría es una *inferencia*, **declará siempre cómo la
   definiste** (qué patrón de nombre / tag / lista de ASINs usaste) y listá las campañas resueltas en
   el resumen antes de aplicar. Si **no** podés resolverla con confianza (no hay patrón, ni tag, ni
   títulos claros) → tratala como destino faltante: **preguntá**, no adivines. Un mapeo de categoría
   mal inferido mete negativos en campañas equivocadas.

Después de resolver, **leé la reference** (`read`) y mostrá cuántas campañas / ad groups quedaron
y sus nombres (o los primeros N + total) en el resumen del Paso 6. Si son 0 filas, avisá y par
— no apliques sobre una selección vacía (probablemente el patrón/ASIN está mal escrito).

## Startup (siempre)

Corré esto al empezar, en este orden:

1. `start_chat_session()` → guardá el `chat_session_id`. Pasalo en **todas** las llamadas siguientes.
2. `read_resource(uri="adlabs://instructions", chat_session_id=...)` — carga las reglas operativas.
3. Si no tenés fresca la mecánica de creación, `read_resource(uri="adlabs://docs/create_actions/negative_targeting")`
   y `.../negative_targeting_apply`. La mecánica clave ya está resumida en este skill (sección
   "Mecánica AdLabs"), así que no hace falta releer si ya la tenés clara.

---

## Flujo paso a paso

### Paso 1 — Parsear el pedido de Nacho

Extraé del mensaje (y del bloque pegado):

- **Brand / cuenta** (para resolver el profile). Si hay ambigüedad multi-marketplace, preguntá cuál.
- **Destino** — identificá cuál de los targeting modes (A/B/C/D, o combinación) está usando Nacho:
  - **A** lista de nombres · **B** patrón/exclusión de nombre · **C** ASIN/producto anunciado ·
    **D** categoría/tipo de producto ("las de jabones sólidos", "solo las de tal línea").
  - **Si no hay ni lista ni regla → Paso 2b (parar y preguntar).** Si es mode D y no podés definir
    la categoría con confianza (nombre/tag/ASINs), también parás y preguntás (ver "Targeting modes").
- **Términos:** las líneas de la lista. Separá en:
  - **ASINs** → cualquier token tipo `B0XXXXXXXX` (10 chars, empieza con B0) o que Nacho marque como ASIN/product target.
  - **Keywords** → todo lo demás (search terms / palabras).
  - Ojo: no confundas un ASIN que es **destino** (mode C, "campañas que anuncian B0…") con un ASIN
    que es **término a negativizar** (product target negativo). El contexto lo aclara: "campañas
    que anuncian X" = destino; "negativizá X" / X en la lista de términos = término.
- **Match type explícito:** "en phrase" / "en exact" / "broad" (ver regla 3). Si no dice → default.
- **Nivel:** ad group (default) salvo que pida "a nivel campaña".
- **Modo:** `apply` (default) o `dry-run`.

Acepta también el bloque copy-paste de `daily-negatives` / `negative-targeting`: esos bloques ya
traen término + kind (keyword/asin) + a veces phrase/exact. Respetá lo que traiga; si trae
clasificación exact/phrase por término, honrala.

### Paso 2 — Resolver team + profile

- `get_entity_data(entity_type="teams", chat_session_id=..., team_id?)` → obtené el `team_id`.
- `get_entity_data(entity_type="profiles", team_id=..., chat_session_id=...)` → matcheá por nombre de brand → `profile_id`.
- Si hay varios profiles que matchean (p.ej. US y CA), preguntá cuál (o corré uno por marketplace si Nacho lo pide).

### Paso 2b — GUARDRAIL de destino

Si tras el Paso 1 **no hay ni lista ni regla** de destino: **detené el flujo** y preguntá algo como:
> "¿A qué campaña(s) o ad group(s) aplico estos N negativos? Puedo tomar una lista de nombres, un
> patrón (ej. 'todas menos SCAVENGER') o las que anuncian un ASIN. No aplico a toda la cuenta sin
> que me lo digas."

No sigas hasta tener el destino. No infieras "todas" cuando no hay ninguna regla.

### Paso 3 — Resolver los ad groups destino (construir la reference)

Los negativos a nivel ad group necesitan `ad_group_id` en la reference. Armá la fetch de `ad_group`
según el/los targeting mode(s) del Paso 1 (ver "Targeting modes" arriba para los filtros exactos),
**siempre** con `CAMPAIGN_STATE=ENABLED`, `AD_GROUP_STATE=ENABLED` y un `DATE` (últimos 14 días):

```
get_entity_data(
  entity_type="ad_group",
  team_id=..., profile_id=..., chat_session_id=...,
  filters: [ <filtros del targeting mode: CAMPAIGN_NAME / CAMPAIGN_NAME_NOT / CONTAINS_ASINS / CAMPAIGN_ID…>,
             CAMPAIGN_STATE=ENABLED, AD_GROUP_STATE=ENABLED, DATE=<últimos 14 días> ]
)
```

- Devuelve una reference `mcp://data/...` con las filas de ad group (cada una con su `ad_group_id`).
  **Nunca construyas la URI a mano** — siempre viene de `get_entity_data`.
- Filtros de nombre son **case-sensitive** en el valor pero se usan como constantes UPPERCASE en la
  key del schema (ej. `CAMPAIGN_NAME_NOT`); el matching de `LIKE`/`NOT_LIKE` es por substring.
- Si el destino es una campaña (o varias) con múltiples ad groups, los negativos van a **todos** sus
  ad groups habilitados. Es esperable, pero **decílo en el resumen** (cantidad + nombres). Si Nacho
  quiere solo algunos, sumá un filtro `AD_GROUP_NAME`/`AD_GROUP_ID`.
- **Siempre `read(reference=...)`** (hasta 100 filas) para ver qué resolviste antes de crear el
  preview — sobre todo en modes B/C, donde el set puede ser grande o inesperado. Si vuelve **0
  filas**: avisá y **par** — no sigas con una reference vacía (patrón/ASIN mal escrito, o nada
  habilitado). Si son >100 filas, usá `group_by_column` por `campaign_name` para reportar el alcance.

### Paso 4 — Validar términos (antes de crear el preview)

Límites de Amazon (si un término los viola, el apply lo saltea; avisalo):
- Máx **80 caracteres** por keyword.
- **PHRASE**: máx **4 palabras**. **EXACT**: máx **10 palabras**.
- **BROAD** solo aplica a Sponsored Products; SD no está soportado (se saltea solo).

Deduplicá la lista de términos. Contá keywords y ASINs por separado.

### Paso 5 — Crear el preview

**Para keywords** (Mode B — reference de ad_group + keywords explícitas):

```
create_entities(
  entity_type="negative_targeting",
  team_id=..., profile_id=..., chat_session_id=...,
  reference=<ad_group ref del Paso 3>,
  keywords=[<lista de keywords>],
  match_types=<según regla 3: ["AD_GROUP_NEGATIVE_EXACT","AD_GROUP_NEGATIVE_PHRASE"] por default,
               o ["AD_GROUP_NEGATIVE_PHRASE"] si dijo "phrase", o ["AD_GROUP_NEGATIVE_EXACT"] si dijo "exact">
)
```

**Para ASINs / product targets:**

```
create_entities(
  entity_type="negative_targeting",
  team_id=..., profile_id=..., chat_session_id=...,
  reference=<ad_group ref del Paso 3>,
  expressions=["asin=\"B07PGL2N7J\"", ...],
  match_types=["AD_GROUP_NEGATIVE_PRODUCT_TARGET"]
)
```

- Cada `create_entities(negative_targeting)` devuelve un **`preview_id`** y un link **"View in AdLabs"**.
- Si hay keywords **y** ASINs, hacé **dos** previews (uno de keywords, uno de product targets) y
  aplicá los dos.
- **Conteo esperado = filas (ad groups) × match_types × términos** (producto cartesiano). NO está
  deduplicado contra negativos ya existentes: los que ya existen se saltean recién en el apply y
  salen reportados en el recibo. Así que no te asustes si el conteo del preview parece alto.

### Paso 6 — Resumen (imprimir SIEMPRE) + apply

Imprimí un resumen claro **antes** de aplicar, p.ej.:

> **A punto de aplicar (auto-apply):**
> - Cuenta: **Happy Fox (US)** · profile `123`
> - Destino: campaña **SP - Exact - Core** → 3 ad groups habilitados (Core-A, Core-B, Core-C)
> - Keywords negativas: 12 términos × EXACT+PHRASE × 3 ad groups = **72 negativos** (preview `#441`)
> - ASINs negativos: 4 × PRODUCT_TARGET × 3 ad groups = **12 negativos** (preview `#442`)
> - Los que ya existan se saltean automáticamente.

**Si modo = `dry-run`:** parás acá. Mostrá el/los link(s) "View in AdLabs" y el conteo, y no apliques.

**Si modo = `apply` (default):** aplicá cada preview:

```
create_entities(
  entity_type="negative_targeting_apply",
  team_id=..., profile_id=..., chat_session_id=...,
  preview_id=<id del Paso 5>,
  note="MCP push: <N> negativos AD_GROUP (<match types>) en <destino> — pedido por Nacho, <fecha>"
)
```

### Paso 7 — Recibo final

Reportá el resultado del/los apply: cuántos negativos se **crearon** y cuántos se **saltearon**
(ya existían o eran filas no soportadas como SD/BROAD-no-SP), leyendo el recibo que devuelve el apply.
Cerrá con una línea accionable, p.ej. "Listo: 72 keyword-negatives + 12 ASIN-negatives aplicados a
3 ad groups de SP - Exact - Core; 5 ya existían y se saltearon."

---

## Mecánica AdLabs (referencia rápida)

- **Jerarquía:** Organization → Team → Profile → Campaign → Ad Group → Target/Search Term.
  `team_id` y `profile_id` se descubren con `get_entity_data` (`teams`, luego `profiles`).
- **Dos modos de `negative_targeting`:**
  - **Mode A** — reference de `search_term`: las keywords se leen de la columna `search_term` de cada fila.
    (Útil si en vez de una lista, Nacho pasa una selección de search terms ya fetcheada.)
    Para negativizar un ASIN encontrado en un search term, igual hay que pasar `expressions` explícitas.
  - **Mode B** — reference de `campaign` o `ad_group` + `keywords`/`expressions` explícitas. **Este es
    el modo por defecto de este skill** (Nacho pega la lista).
- **Requisitos por match type:**
  - `AD_GROUP_NEGATIVE_*` requiere `ad_group_id` en la reference → por eso fetcheamos ad groups.
  - Keyword match types requieren `keywords` no vacío (Mode B). Product-target match types requieren `expressions` no vacío.
  - `CAMPAIGN_NEGATIVE_*` y `BROAD` solo SP. SB solo soporta `AD_GROUP_NEGATIVE_*`. SD no soportado (se saltea).
- **Preview → apply:** `create_entities(negative_targeting)` devuelve `preview_id` + link "View in AdLabs".
  `create_entities(negative_targeting_apply, preview_id, note)` manda a Amazon. El `note` es obligatorio.
- **References** son tokens opacos `mcp://data/...`, siempre de `get_entity_data`; expiran con la sesión
  (si una reference da error, re-fetcheá).
- **Alternativa nativa:** si Nacho quiere revisar en la UI antes de aplicar en vez de auto-apply, dale
  el link "View in AdLabs" del preview y no llames al apply (equivale a un dry-run con confirmación manual).

---

## Ejemplos

**Ejemplo 1 — exclusión por nombre + phrase (bulk):**
Input: *"Aplicá esta lista de negativos en PHRASE a todos los ad groups de todas las campañas menos
las que tienen SCAVENGER en el nombre: [lista]"* — cuenta Happy Fox.
- Mode B (exclusión). Fetch `ad_group` con `CAMPAIGN_NAME_NOT NOT_LIKE "SCAVENGER"` + states ENABLED + DATE.
- `read` la ref → p.ej. 40 ad groups en 12 campañas (SCAVENGER excluidas).
- Preview `negative_targeting` con `keywords=[lista]`, `match_types=["AD_GROUP_NEGATIVE_PHRASE"]`.
- Resumen: "22 términos × PHRASE × 40 ad groups = 880 negativos, 12 campañas (excluidas 3 SCAVENGER)".
- Auto-apply → recibo (creados vs ya existentes).

**Ejemplo 2 — por ASIN anunciado + exact:**
Input: *"Aplicá esta lista de negativos en exact a las campañas que tienen como feature product el
ASIN B08XYZ1234: [lista]"*.
- Mode C (default: solo ad groups que anuncian el ASIN). Fetch `ad_group` con
  `CONTAINS_ASINS IN ["B08XYZ1234"]` + states ENABLED + DATE.
- `read` la ref → p.ej. 6 ad groups en 4 campañas.
- Preview con `keywords=[lista]`, `match_types=["AD_GROUP_NEGATIVE_EXACT"]`.
- Resumen + auto-apply + recibo.

**Ejemplo 3 — categoría/tipo de producto, "solo contengan" + phrase (HEKAYA):**
Input: *"En HEKAYA aplicá términos negativos en phrase a las campañas que solo contengan jabones
sólidos: [lista]"*.
- Mode D. Definí "jabón sólido" (probá en orden): ¿el nombre de campaña lo dice? → `CAMPAIGN_NAME LIKE`.
  ¿Hay tag de producto? → `PRODUCT_DATA_GROUP_ITEM`. Si no, resolvé los ASINs de jabón sólido por
  título / catálogo Sophie Hub → `CONTAINS_ASINS`.
- **Declará** la definición usada ("campañas con 'Jabón Sólido' en el nombre" / "tag #42" / "8 ASINs").
- Aplicá el matiz **"solo"**: descartá los ad groups que además anuncian otra categoría.
- `read` la ref, listá las campañas resueltas. Si la categoría no se puede definir con confianza → **preguntá**.
- Preview `match_types=["AD_GROUP_NEGATIVE_PHRASE"]` → resumen (con la definición) → auto-apply → recibo.

## Errores comunes y cómo evitarlos

- **Reference vacía / destino mal escrito** → 0 filas de ad group. Confirmá el nombre exacto de la
  campaña (case-sensitive en states: `'Enabled'`, no `'enabled'`). No apliques sobre reference vacía.
- **Conteo del preview enorme** → normal: es el producto filas×match_types×términos. Los duplicados
  se filtran en el apply. No lo interpretes como error.
- **Aplicar a toda la cuenta** → prohibido. Si dudás del destino, dry-run o preguntá.
- **SD en el destino** → se saltea solo; avisalo en el recibo.
- **Keyword > límites (80 chars / 4 palabras phrase / 10 exact)** → se saltea; avisá cuáles.
