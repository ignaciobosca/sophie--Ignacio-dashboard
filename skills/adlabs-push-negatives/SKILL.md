---
name: adlabs-push-negatives
description: >
  Empuja y aplica términos/ASINs a negativizar directamente en campañas de Amazon Ads
  vía el conector AdLabs. Pegás una lista de search terms / palabras / ASINs y el destino
  (campaña o ad group), y el skill los crea como negativos a nivel AD GROUP (Exact + Phrase
  para keywords, Product Target para ASINs) y los aplica a Amazon en la misma pasada
  (auto-apply). NUNCA aplica a todas las campañas: si no le das destino, para y pregunta.
  A diferencia de daily-negatives y negative-targeting (que solo IDENTIFICAN candidatos y
  arman listas para copiar a mano), este hace el PUSH final vía MCP. Trigger: "negativizá estos
  términos en [campaña]", "empujá estos negativos a [Brand]", "aplicá estos negativos en AdLabs",
  "push these negatives", "agregá estos negativos a la campaña X", o pegar una lista de
  términos/ASINs (incluido el bloque copy-paste de
  daily-negatives / negative-targeting) para cargar como negativos en campañas concretas.
  NO usar para DESCUBRIR qué negativizar ni para harvesting de keywords positivas.
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

1. **NUNCA aplicar a todas las campañas de la cuenta.** El destino (campaña/s o ad group/s)
   tiene que ser **explícito**. Si el mensaje de Nacho no nombra un destino concreto, **pará
   y preguntá** cuáles campañas o ad groups. Un destino faltante jamás significa "todas".
   Esta es la única red de seguridad del modo auto-apply, y es sagrada porque un negativo mal
   dirigido apaga tráfico que sí convierte.

2. **Nivel = AD GROUP por defecto** (`AD_GROUP_NEGATIVE_*`). Es el default que eligió Nacho:
   sirve igual para Sponsored Products y Sponsored Brands, y es más quirúrgico que campaign-level.
   Solo usá `CAMPAIGN_NEGATIVE_*` si Nacho lo pide explícito (y ojo: campaign-level solo existe
   en SP, no en SB).

3. **Match types por defecto:**
   - Keywords → `AD_GROUP_NEGATIVE_EXACT` + `AD_GROUP_NEGATIVE_PHRASE`.
   - ASINs (product targets) → `AD_GROUP_NEGATIVE_PRODUCT_TARGET`.
   Respetá overrides si Nacho los da ("solo exact", "solo phrase", "a nivel campaña", "broad").

4. **Auto-apply.** El flujo va derecho: preview → resumen → apply, sin pausa de confirmación.
   PERO siempre imprimí el resumen exacto (cuántos negativos, en qué ad groups, qué match types)
   *antes* del apply, para que quede el registro. Excepción: **modo dry-run** (ver abajo) frena
   antes del apply.

5. **`note` significativa siempre.** El `apply` exige un `note` para el audit log. Usá algo como:
   `"MCP push: N negativos AD_GROUP (exact+phrase) en <campaña/ad groups> — pedido por Nacho, <fecha>"`.

---

## Modos

- **`apply`** (default): crea y aplica los negativos a Amazon.
- **`dry-run`**: hace todo hasta el preview (te da el conteo y el link "View in AdLabs")
  y **NO** aplica. Usalo cuando Nacho diga "dry run", "solo preview", "no lo apliques todavía",
  "mostrame qué se va a crear", "probá sin aplicar". También usalo vos por default la
  **primera vez** que corras contra una campaña nueva si tenés cualquier duda sobre el destino.

---

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
- **Destino:** nombre(s) de campaña o de ad group. **Si no hay destino explícito → Paso 2b (parar y preguntar).**
- **Términos:** las líneas de la lista. Separá en:
  - **ASINs** → cualquier token tipo `B0XXXXXXXX` (10 chars, empieza con B0) o que Nacho marque como ASIN/product target.
  - **Keywords** → todo lo demás (search terms / palabras).
- **Overrides de match type / nivel** si los menciona.
- **Modo:** `apply` (default) o `dry-run`.

Acepta también el bloque copy-paste de `daily-negatives` / `negative-targeting`: esos bloques ya
traen término + kind (keyword/asin) + a veces phrase/exact. Respetá lo que traiga; si trae
clasificación exact/phrase por término, honrala.

### Paso 2 — Resolver team + profile

- `get_entity_data(entity_type="teams", chat_session_id=..., team_id?)` → obtené el `team_id`.
- `get_entity_data(entity_type="profiles", team_id=..., chat_session_id=...)` → matcheá por nombre de brand → `profile_id`.
- Si hay varios profiles que matchean (p.ej. US y CA), preguntá cuál (o corré uno por marketplace si Nacho lo pide).

### Paso 2b — GUARDRAIL de destino

Si tras el Paso 1 **no hay** campaña/ad group explícito: **detené el flujo** y preguntá algo como:
> "¿A qué campaña(s) o ad group(s) querés que aplique estos N negativos? No los aplico a toda la
> cuenta por seguridad."

No sigas hasta tener el destino. No infieras "todas".

### Paso 3 — Resolver los ad groups destino (construir la reference)

Los negativos a nivel ad group necesitan `ad_group_id` en la reference. Traé los ad groups
del destino y filtrá a los habilitados:

```
get_entity_data(
  entity_type="ad_group",
  team_id=..., profile_id=..., chat_session_id=...,
  filters: { CAMPAIGN_NAME (o CAMPAIGN_ID) = <destino>, campaign_state='Enabled', ad_group_state='Enabled', DATE=<últimos 14 días> }
)
```

- Esto devuelve una reference `mcp://data/...` con las filas de ad group (cada una con su `ad_group_id`).
- **Nunca construyas la URI a mano** — siempre viene de `get_entity_data`.
- Si el destino es una campaña con varios ad groups, los negativos se van a aplicar a **todos**
  los ad groups habilitados de esa campaña. Eso es esperable, pero **decílo en el resumen**
  (nombre y cantidad de ad groups) para que no sea una sorpresa. Si Nacho quiere solo algunos
  ad groups, filtrá por `AD_GROUP_NAME`/`AD_GROUP_ID`.
- Si el `read` de la reference vuelve con 0 filas, avisá que no encontraste ad groups habilitados
  para ese destino y confirmá el nombre — no sigas con una reference vacía.

> Tip: si querés ver qué ad groups resolviste, `read(reference=...)` (hasta 100 filas) antes de crear el preview.

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
  match_types=["AD_GROUP_NEGATIVE_EXACT","AD_GROUP_NEGATIVE_PHRASE"]
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

## Errores comunes y cómo evitarlos

- **Reference vacía / destino mal escrito** → 0 filas de ad group. Confirmá el nombre exacto de la
  campaña (case-sensitive en states: `'Enabled'`, no `'enabled'`). No apliques sobre reference vacía.
- **Conteo del preview enorme** → normal: es el producto filas×match_types×términos. Los duplicados
  se filtran en el apply. No lo interpretes como error.
- **Aplicar a toda la cuenta** → prohibido. Si dudás del destino, dry-run o preguntá.
- **SD en el destino** → se saltea solo; avisalo en el recibo.
- **Keyword > límites (80 chars / 4 palabras phrase / 10 exact)** → se saltea; avisá cuáles.
