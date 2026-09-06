---
name: client-onboarding
description: >
  Sophie Society client onboarding flow. Creates or updates a rich client config JSON file
  used by the daily-check, weekly-report, weekly-wins, and monthly-report skills. Trigger whenever
  Nacho says "onboard [BrandName]", "new client [BrandName]", "add a client", "set up [brand]",
  "create the config for [brand]", or "update the onboarding for [brand]". Also trigger automatically
  when any data-driven skill cannot find a config for the requested brand — in that case, ask Nacho
  if he wants to run onboarding before continuing. Always use this skill when a client config needs
  to be created or updated with fields like ACOS target, TACOS target, account stage, AdLabs IDs, etc.
  También corre en modo REFRESH DE FICHA cuando Nacho dice "actualizar ficha de [producto/ASIN] de [Brand]",
  "refrescar ficha de [Brand]", "update product fiche for [Brand]", o pide re-jalar la ficha de producto
  de un listing que cambió — en ese modo re-jala el listing y actualiza la ficha de relevancia sin rehacer
  el onboarding completo.
---

# Client Onboarding Skill

**Versión actual:** V2.5 (2026-09-06) — ver changelog en `memory/client_onboarding_changelog.md`
> V2.5: agrega **Step 4.6 — Ficha de producto (auto-jalado)**: en cada onboarding se auto-jala la copia
> del listing (title/bullets/description + atributos estructurados si están) por ASIN, se deriva la
> **ficha de relevancia** (`product_fiche` del schema `relevance-profile-v2`) y se hace **upsert a Supabase
> `relevance_profiles`**. Esa ficha es la vara contra la que el motor de `daily-negatives-supabase` juzga
> qué negativizar. Agrega también el **MODE = refresh_fiche** (re-jalar la ficha de un producto que cambió,
> bajo demanda). El config del cliente (JSON local + manifest) NO cambia; la ficha es un output nuevo y aparte.
> V2.4: agrega **Group F (competitor ASINs, hasta 5)** + **Step 4.5 (setup de tracking competitivo
> Keepa/DataDive Rank Radar)**. Los `competitor_asins` alimentan la capa 2 de la slide Competitive del
> Monthly Report; el Rank Radar se prende acá porque no es retroactivo (necesita un mes de runway).

You are running the Sophie Society client onboarding flow — an interactive process that collects all the relevant information for a new (or updated) client, saves it as a structured JSON config in the canonical Drive folder, and updates the master manifest. This config is consumed by `daily-check` (V3+), `weekly-report`, `weekly-wins`, `monthly-report`, `placement-optimizer`, and other AdLabs-dependent skills.

**Three outputs per onboarding:**
1. **Client config JSON** in Drive (one per marketplace or per product line).
2. **Updated `_active_clients.json` manifest** in the same Drive folder.
3. **Ficha de producto** (`product_fiche`) → **upsert a Supabase `relevance_profiles`** (Step 4.6). Es la
   vara del motor de negativización; vive en el perfil de relevancia, no en el config del cliente.

---

## Dos modos

- **`run` (default)** — onboarding completo (Steps 1–8). Incluye el auto-jalado de la ficha (Step 4.6).
- **`refresh_fiche`** — re-jalar SOLO la ficha de uno o varios ASINs de un cliente ya onboardeado, cuando
  su listing cambió. Trigger: *"actualizar ficha de [producto/ASIN] de [Brand]"*. Salta directo al Step 4.6
  para los ASINs pedidos y hace el upsert. Ver **## MODE = refresh_fiche** al final. Detectá el modo del
  mensaje de Nacho antes del Step 1.

---

## Global config

```
Configs folder (LOCAL, Drive-synced):
  C:\Users\Nacho Bosca\Desktop\Claude\Projects\General\sophie-society-clients\

Drive folder ID (daily-check reads from here, auto-synced from local):
  1cqULQYU4G7yuD6PKvQeGLKW3l5l5151j

Manifest filename:           _active_clients.json
Filename convention:         [BrandName].json                     (US/primary marketplace, single product)
                             [BrandName]_CA.json                  (additional marketplace)
                             [BrandName]_[Line].json              (multi-product line)
                             — normalize BrandName: strip spaces, apostrophes, special chars
                               (e.g. "Pavida's Wellness" → "PavidasWellness" → file `PavidasWellness.json`)
```

**Important architecture note:** the local folder above is **Drive Desktop-synced** with the Drive folder ID. Writing locally with `Write` / `Edit` tools auto-propagates to Drive within seconds. We do NOT use the Drive MCP (`create_file`) for writes — that MCP can't overwrite/delete, which created duplicate-file pain in V2.1. Reads can come from either source (daily-check reads from Drive for portability across machines).

---

## Step 1: Identify the brand + check for duplicates

If Nacho already named the brand in the trigger (e.g., *"onboard Moomade"*), use it. Otherwise ask:
> *"What's the brand name?"*

### Always read the local manifest first to check duplicates

```python
import json
from pathlib import Path

CONFIGS_DIR = Path(r"C:\Users\Nacho Bosca\Desktop\Claude\Projects\General\sophie-society-clients")
manifest_path = CONFIGS_DIR / "_active_clients.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
```

Si por algún motivo la carpeta local no está disponible (otra máquina sin sync), caer a leer de Drive vía `search_files` + `download_file_content` como fallback — pero el flujo principal es local.

Check if the brand already exists in either:
- **Manifest entries** (`clients[].brand_name`) — **case-insensitive match** (`brand.lower() == entry["brand_name"].lower()`). Normalizar también espacios y apóstrofes para detectar `"Pavida's"` vs `"Pavidas"` vs `"pavidas wellness"` como el mismo cliente.
- **Existing config files** in the folder (look for filename match, también case-insensitive)

**If duplicate found:**
> *"I found an existing config for [Brand] (`[filename]`, in the manifest since [date]). Do you want to update it, add a new marketplace/line, or start from scratch?"*

- **Update existing** → load current JSON, only update fields Nacho changes (preserve rest).
- **New marketplace/line** → proceed with a new file (`[Brand]_CA.json`, `[Brand]_Kids.json`, etc.).
- **Start fresh** → confirm with Nacho that he wants to overwrite, then proceed normally.

**If not found:** proceed to Step 2.

---

## Step 2: Check for product lines and marketplaces

Ask two questions (group them naturally — don't make it robotic):

> *"¿Este cliente tiene varias product lines que reportamos por separado (ej. Adult / Kids / Total Account), o es una sola cuenta?"*

> *"¿Corre en uno o varios marketplaces de Amazon (US, CA, UK, etc.)?"*

**Filename matrix:**

| Setup | Filenames |
|---|---|
| Single account, single marketplace (US) | `[BrandName].json` |
| Single account, multi-marketplace | `[BrandName].json` (US/primary) + `[BrandName]_CA.json`, `[BrandName]_UK.json`, etc. |
| Multi-product, single marketplace | `[BrandName]_Adult.json`, `[BrandName]_Kids.json` |
| Multi-product, multi-marketplace | `[BrandName]_Adult.json` + `[BrandName]_Adult_CA.json`, etc. |

**Run the data-collection flow (Step 3) once per file** — separate marketplaces and separate product lines each need their own config. Don't try to cram multiple marketplaces into one JSON; daily-check V3 expects one `adlabs_profile_id` per config.

---

## Step 3: Collect client information

Ask for the following fields. Group related questions naturally — don't fire them robotically.

### Group A — Contact & reporting
- **owners**: First names used in greetings (e.g., `["Omar", "Chiara"]`).
- **slack_names**: Full Slack display names for `@mentions` (e.g., `["Omar Mejia", "Chiara"]`). Must match the workspace exactly.

> ⚠️ **NO pedir `dashboard_url`.** Este campo fue removido del onboarding en V2.1. Si está presente en un config existente que estás actualizando, dejarlo como está (no borrarlo); pero no preguntar por él para clientes nuevos.

### Group B — AdLabs IDs (required for daily-check V3)
- **adlabs_team_id**: Team ID (number). Most Sophie Society clients share team `107154` — confirm with Nacho. *"AdLabs team ID? (probable 107154)"*
- **adlabs_profile_id**: Profile ID for THIS marketplace (number, no quotes). *"AdLabs profile ID para [marketplace]? Lo encontrás en la URL del profile en AdLabs."*

**❗ Critical:** these two fields are REQUIRED by daily-check V3. If Nacho doesn't have them, you can save `null` BUT warn him: *"⚠️ Without these IDs, the daily-check will flag `[Brand]` as an invalid schema and skip it. Better to complete them before it runs tomorrow."*

### Group C — Performance targets (recommended)
- **acos_target**: ACOS target as decimal (`0.30` = 30%).
- **tacos_target**: TACOS target as decimal (`0.15` = 15%).
- **monthly_budget**: PPC budget in USD (e.g., `2000`).

These son **recommended** (no required) por daily-check V3 — el config carga sin ellos, pero las comparaciones vs target y el pacing se omiten. Avisar a Nacho si los deja en `null`.

### Group D — Account context
- **active**: `true` (default for new clients) — incluido en daily-check.
- **paused**: `false` (default) — `true` cuando campañas están pausadas intencionalmente y querés silenciar alertas.
- **onboarding_date**: Fecha que Sophie Society arrancó con el cliente (YYYY-MM-DD).
- **amazon_marketplace**: Marketplace primario (`US`, `CA`, `UK`, `DE`, `MX`, etc.). Debe matchear el `adlabs_profile_id` provisto.
- **product_category**: Categoría principal en Amazon.
- **account_stage**: `launch` | `growth` | `optimization` | `scaling`.
  - `launch`: nuevo, primeras semanas de PPC.
  - `growth`: scaling, ACOS elevado pero mejorando.
  - `optimization`: performance estable, foco en eficiencia.
  - `scaling`: eficiencia lograda, foco en volumen con ACOS controlado.
- **report_language**: `"en"` o `"es"`. Default `"en"`.
- **drive_folder_id**: ID de la carpeta RAÍZ del cliente en Drive (`Projects\[BrandFolder]\`). Lo usan skills de export (search-term-harvest, y a futuro otros) para subir/linkear el archivo en la carpeta correcta —la que está syncheada con la carpeta local— en vez de My Drive raíz. *"¿Tenés el link de la carpeta de Drive de [Brand]? Pegámelo y saco el ID (`.../folders/<ESTE_ID>`)."* Opcional: si Nacho no la tiene a mano, guardar `null` (los skills degradan a búsqueda por nombre).
- **notes**: Free text — goals, constraints, product notes, history.

### Group E — Managed ASINs
Lista de parent/child ASINs que Sophie Society maneja activamente. Usado por Monthly Report y skills de análisis para scopear data pulls.

Para cada ASIN:
- `asin`: e.g., `"B0XXXXXXXX"`
- `name`: label corto, e.g., `"Eczema Cream"` (puede ser `null` si no se sabe)
- `type`: `"parent"` o `"child"`

Si Nacho no tiene los ASINs a mano, guardar `"managed_asins": []` y avisarle que los agregue antes de correr Monthly Report.

### Group F — Competitor ASINs (para tracking + análisis competitivo del Monthly Report)

Pedir hasta **5 ASINs de competidores directos** de este cliente/marketplace:

> *"Pasame hasta 5 ASINs de competidores directos de [Brand]. Los usamos para (a) trackearlos con Keepa/DataDive desde hoy y (b) alimentar la sección Competitive / Share of Voice del Monthly Report."*

Para cada uno guardar `{ "asin": "B0XXXXXXXX", "name": "<label corto o null>", "brand": "<marca o null>" }`
en `competitor_asins`. Estos son la fuente por defecto de la **capa 2** de la slide Competitive del
Monthly (precio, rating, reviews, BSR, units/mes vía Keepa + rank orgánico vía DataDive).

- Si Nacho no los tiene a mano → guardar `"competitor_asins": []` y avisar que sin ellos el Monthly
  corre la slide Competitive **solo con SQP share** (capa 1), sin competidores nombrados.
- **Importante (runway):** el tracking de rank orgánico de DataDive (Rank Radar) **NO es retroactivo**
  — solo acumula desde el día que se crea. Por eso se setea acá, en onboarding: así el primer Monthly
  ya tiene el mes de trend. Keepa sí es retroactivo (no necesita runway). Ver **Step 4.5**.

---

## Step 4: Find the internal Slack channel

Buscar el canal interno de Sophie Society para este cliente con `slack_search_channels`.

**Convención de nombres — canal interno (donde Sophie Society manda alertas):**
- `#[brand]-alerts` ✅
- `#[brand]-internal` ✅
- (cualquiera de los dos sufijos cuenta como canal interno válido)

**Canal compartido con cliente — NUNCA usar para alertas internas:**
- `#[brand]-sophie` ❌

**Lógica de búsqueda:**
1. Buscar canales que contengan el brand name.
2. De los resultados, priorizar el que termine en `-alerts` o `-internal`.
3. Si hay ambos (`-alerts` y `-internal`), preguntar a Nacho cuál usar.
4. Si solo hay `-sophie`, NO usarlo. Guardar `null` y avisar: *"⚠️ I only found `#[brand]-sophie` (shared with the client). `#[brand]-alerts` or `#[brand]-internal` still needs to be created for alerts. I'm leaving it as `null` for now."*
5. Si no se encuentra nada: guardar `null` y avisar a Nacho: *"⚠️ I couldn't find an internal channel for `[Brand]`. Add it manually once you create it."*

Extraer el channel ID (formato `CXXXXXXXXX`). Guardar en `slack_internal_channel_id`.

---

## Step 4.5: Set up competitive tracking (Keepa + DataDive)

**Solo si `competitor_asins` no está vacío.** Todo corre vía el dispatch de Sophie Hub
(`sophie_call_keepa_adapter` / `sophie_call_datadive_adapter`; descubrir esquemas con
`sophie_list_keepa_tools` / `sophie_list_datadive_tools`). Objetivo: dejar el tracking prendido HOY
para que el primer Monthly ya tenga historia.

1. **Keepa — empezar a snapshotear** (retroactivo igual, pero lo dejamos monitoreado):
   `keepa_track_asins(asins=[...competitor_asins + hero ASIN del cliente...], label="[Brand] competitive", priority="standard")`.
   Keepa ya tiene el histórico, así que el Monthly puede pedir price/BSR/units/mes cuando quiera; esto
   solo agrega detección de cambios.

2. **DataDive — crear el nicho** (si el cliente no tiene uno):
   `datadive_create_dive(keyword="<hero keyword del cliente>", asin="<hero ASIN del cliente>", marketplace="<mkt>", number_of_competitors=17)`.
   Es un job async → chequear con `datadive_get_dive_status(dive_id)`. Cuando termina, tomar el
   `niche_id` y guardarlo en `datadive_niche_id`. Si el cliente **ya** tiene nicho, buscarlo con
   `datadive_list_niches` y reutilizar el id.

3. **DataDive — crear el Rank Radar** (esto es lo que necesita runway):
   `datadive_create_rank_radar(asin="<hero ASIN del cliente>", niche_id=<datadive_niche_id>, marketplace="<mkt>", number_of_keywords=50)`.
   Se **auto-popula** con las top keywords del nicho por relevancia/volumen — Nacho NO pega keywords.
   Guardar el id devuelto en `datadive_rank_radar_id`. (Opcional: cruzar el auto-pick contra los
   términos donde el cliente convierte en SQP para confirmar que las *money keywords* estén dentro;
   si Nacho quiere, subir `number_of_keywords`.)

**Degradar con gracia:** si DataDive no tiene el cliente configurado o el dive falla, guardar los ids
en `null`, avisar a Nacho, y seguir. El Monthly correrá la capa Keepa (retroactiva) igual; la capa de
rank orgánico se activa cuando el radar exista. Guardar en el config:
`competitor_asins`, `datadive_niche_id`, `datadive_rank_radar_id`.

> ⚠️ **Runway:** el Rank Radar arranca a acumular desde HOY. El **primer** Monthly tras el onboarding
> muestra la slide Competitive con la tabla Keepa completa + una **foto** de rank actual (baseline);
> el **movimiento** de rank aparece recién del segundo Monthly en adelante. Avisar a Nacho.

---

## Step 4.6: Ficha de producto → perfil de relevancia (Supabase)

Auto-jala la copia real del listing de cada `managed_asin`, deriva la **ficha de relevancia** y hace
**upsert a Supabase `relevance_profiles`**. Esta ficha es la vara contra la que el motor de
`daily-negatives-supabase` juzga qué negativizar — cuanto más fiel, menos falsos positivos en el autopush.

> 🚨 **AUTO-JALADO SIN REVISIÓN (pedido de Nacho): se jala y se guarda directo, sin pausa de confirmación.**
> La robustez reemplaza a la revisión: **nunca se inventa una ficha.** Si una fuente falla o viene vacía,
> ese ASIN queda `status:"no_fiche"` y su juicio, en el daily, cae a la lógica conservadora de hoy
> (ningún juicio suyo llega a `high` por attribute-mismatch). Los `attributes_absent` se derivan **solo de
> ausencia clara**, jamás por inferencia agresiva.

Si `managed_asins` está vacío → saltear este step, avisar *"⚠️ Sin managed_asins no puedo armar la ficha de
relevancia; el motor de negativización va a juzgar con la lógica conservadora hasta que cargues ASINs + corras
'actualizar ficha'."* y seguir.

### 4.6.a — Resolver marketplace + store

- **marketplace short code** = `cfg["amazon_marketplace"]` (US/CA/UK/…). Es el que pide Helium10.
- **store (seller_id) de Sophie Hub** (para atributos estructurados): resolver con `list_stores` matcheando
  por brand. Si no resuelve un store claro → seguir **sin** atributos estructurados (la ficha se arma solo con
  la copia de texto; es la opción "+ atributos estructurados **si están**"). No bloquea.

### 4.6.b — Jalar la copia por ASIN (paso por ASIN)

Por cada `{asin, name, type}` en `managed_asins`:

1. **Copia de texto (primaria) — Helium10 `retrieve_listing_by_asin`** `(asin, marketplace)`:
   devuelve `product_name`, `bullet_points`, `description`. Mapear:
   `source_listing = {title: product_name, bullets: bullet_points, description}`.
   `source = "helium10:retrieve_listing_by_asin"`.
2. **Atributos estructurados (si hay store) — Sophie Hub `get_product_catalog`** `(seller_id, asin, marketplace_id)`:
   tomar de `attributes` / `summaries` / `productTypes` / `dimensions` los campos útiles (material, scent,
   size, item_form, target_audience, special_features, etc.). Son insumo para derivar `attributes_present` con
   más precisión y NO se inventan.
3. **Fallback de copia:** si `retrieve_listing_by_asin` falla, intentar `get_listing_details` (trae `title` y
   categoría, sin bullets/description) — ficha parcial. Si TAMBIÉN falla y no hay catalog → `status:"no_fiche"`.
4. Registrar `fetched_on = today` y `status = "ok"` (o `"no_fiche"`).

### 4.6.c — Derivar la ficha (PASO DEL MODELO)

De `source_listing` + atributos estructurados, derivá por ASIN las **7 dimensiones** de `attributes_present`:
`ingredients_actives`, `scents_flavors`, `sizes_formats`, `materials`, `audience`, `use_cases`, `features`.

- **`attributes_absent`** — SOLO ausencia clara: un atributo que el listing/atributos estructurados
  **contradicen o declaran explícitamente que no aplica** (ej. material declarado = 100% cotton ⇒ `bamboo`
  absent; "unscented" ⇒ scents absent). **Nunca** listar como absent algo que simplemente no se mencionó.
  Cada entry: `{attr, evidence}` con la evidencia textual.
- **`variations`** (opcional): scents/tamaños que SÍ existen en la familia, si el catalog los trae (para no
  negar variaciones propias). Si no vienen → `{}`.
- **`line`**: la línea/parent del producto (para el ruteo del push). Usar `name`/`type`; si es child, la línea
  es su parent.

Cada item queda:
```jsonc
{ "asin", "name", "line", "status": "ok|no_fiche", "source", "fetched_on",
  "source_listing": {"title","bullets":[...],"description"},
  "attributes_present": {ingredients_actives:[],scents_flavors:[],sizes_formats:[],materials:[],audience:[],use_cases:[],features:[]},
  "attributes_absent": [{"attr","evidence"}],
  "variations": {} }
```

### 4.6.d — Upsert a Supabase `relevance_profiles`

**Brand key** = el mismo `brand` que usa la cadena daily. Multi-marketplace: distinguí el marketplace en la
key igual que el resto de Supabase (ej. `"Happy Fox (CA)"`). El onboarding corre una vez por config, así que
cada corrida upserta la ficha de SU marketplace.

```sql
-- 1) leer el perfil actual (si existe)
select profile from public.relevance_profiles where brand = '<brand_key>';
```

- **Si no existe** → crear uno nuevo schema `relevance-profile-v2`:
  `{brand_name, config_stem, schema:"relevance-profile-v2", product_fiche:{...}, roots:[], competitors:[], protected_relevant:[], updated, updated_by:"onboarding", change_log:[]}`.
- **Si existe** → NO pisar `roots`/`competitors`/`protected_relevant` (eso es lo aprendido). Si el perfil es v1,
  migralo a v2 primero (ver `relevance-profiles-hardening/01-migrate-v1-to-v2.py` — envolver roots/competitors,
  derivar `scope`). Reemplazar **solo** `product_fiche` (por ASIN: pisar el item existente del mismo ASIN,
  conservar los demás).

`product_fiche = {updated: today, updated_by: "onboarding", items: [<un item por ASIN>]}`.
Appendear al `change_log`: `"<today>: ficha de producto cargada/actualizada en onboarding (N ASINs: X ok, Y no_fiche)."`

```sql
-- 2) upsert
insert into public.relevance_profiles (brand, profile)
values ('<brand_key>', $prof$<profile JSON v2 con product_fiche>$prof$::jsonb)
on conflict (brand) do update set profile = excluded.profile, updated = now();
```

### 4.6.e — Reporte

`Ficha de relevancia de {brand}: {N} ASINs ({ok} ok, {no_fiche} sin ficha) → upsert a relevance_profiles.`
Listar los `no_fiche` con el motivo (para que Nacho sepa cuáles quedaron sin vara).

---

## Step 5: Build the JSON

```json
{
  "brand_name": "Moomade",
  "active": true,
  "paused": false,
  "owners": ["Omar", "Chiara"],
  "slack_names": ["Omar Mejia", "Chiara"],
  "adlabs_team_id": 107154,
  "adlabs_profile_id": 3450450255213228,
  "slack_internal_channel_id": "C08CLK9PYET",
  "acos_target": 0.70,
  "tacos_target": 0.30,
  "onboarding_date": "2025-04-01",
  "amazon_marketplace": "US",
  "product_category": "Beef Tallow Balm",
  "monthly_budget": 2000,
  "account_stage": "growth",
  "report_language": "en",
  "drive_folder_id": "1AbCdEfGhIjKlMnOpQrStUvWxYz",
  "notes": "Focus on ACOS reduction. Strong organic history pre-PPC launch.",
  "managed_asins": [
    { "asin": "B0XXXXXXXX", "name": "Beef Tallow Balm", "type": "parent" }
  ],
  "competitor_asins": [
    { "asin": "B0YYYYYYYY", "name": "Rival Tallow Balm", "brand": "CompetitorCo" }
  ],
  "datadive_niche_id": "niche_abc123",
  "datadive_rank_radar_id": "radar_xyz789"
}
```

> Nota: V2.1 removió `dashboard_url` del schema. Configs viejos que lo tengan no se rompen; el campo simplemente queda sin uso. No agregarlo en configs nuevos.

### 5a. Validate against daily-check V3 contract

Antes de guardar, validar:

```python
REQUIRED = ["brand_name", "adlabs_team_id", "adlabs_profile_id"]
RECOMMENDED = ["acos_target", "tacos_target", "monthly_budget"]

missing_required = [k for k in REQUIRED if config.get(k) in (None, "", [])]
missing_recommended = [k for k in RECOMMENDED if config.get(k) in (None, "")]
```

- **Si faltan required:** mostrar a Nacho *"⚠️ Missing required fields: [list]. The daily-check will skip this client. Do we save it anyway or complete them first?"* — proceder solo si Nacho confirma.
- **Si faltan recommended:** info: *"ℹ️ Missing recommended fields: [list]. The daily-check will process it but without pacing / vs-target comparisons. Let me know if you want to complete them."* — proceder normal.

### 5b. Generate filename

Normalizar `brand_name` para el filename:
- Strip apostrophes, spaces, accents, special characters.
- Examples: `"Pavida's Wellness"` → `"PavidasWellness"` → `PavidasWellness.json`
- For additional marketplace: append `_[MARKETPLACE]` (e.g., `PavidasWellness_CA.json`).
- For product line: append `_[Line]` (e.g., `Moomade_Adult.json`).

### 5c. Save to local Drive-synced folder

Escribir el JSON directamente al filesystem local con `Write`. Drive Desktop se ocupa del sync.

```python
target_path = CONFIGS_DIR / f"{generated_filename}.json"
target_path.write_text(
    json.dumps(config, indent=2, ensure_ascii=False),
    encoding="utf-8"
)
```

**Si ya existe un archivo con ese nombre** (caso "update existing"):
- `Write` sobreescribe in-place — no hay duplicates en Drive, no hay limpieza manual.
- Antes de sobreescribir, leer el archivo viejo, hacer merge campo a campo con los cambios que Nacho confirmó, y solo persistir el resultado. **No clobberear campos que Nacho no quiso modificar.**


---

## Step 6: Update `_active_clients.json` manifest

Después de guardar el config, actualizar el manifest en Drive.

### 6a. Read the local manifest

```python
manifest_path = CONFIGS_DIR / "_active_clients.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
```

(Si ya lo cargaste en Step 1, reutilizar — no leer dos veces.)

### 6b. Build manifest entry

```json
{
  "brand_name": "[brand_name as in config]",
  "config_filename": "[generated_filename].json",
  "marketplace": "[US/CA/UK/...]",
  "expected": true,
  "notes": ""
}
```

### 6c. Insert or update

- Si **no existe** una entry con ese `brand_name` + `config_filename` → append a `manifest["clients"]`.
- Si **existe** (caso update) → reemplazar la entry preservando `notes` antiguas si Nacho no las cambió.

### 6d. Update meta + write back

```python
manifest["_meta"]["last_updated"] = today.isoformat()
manifest["_meta"]["version"] = manifest["_meta"].get("version", 1) + 1

manifest_path.write_text(
    json.dumps(manifest, indent=2, ensure_ascii=False),
    encoding="utf-8"
)
```

`Write` sobreescribe in-place. Drive Desktop sincroniza solo. **No hay duplicates, no hay limpieza manual.**

### 6e. Confirmación

> *"Done. Manifest updated with `[Brand]` (`[filename]`). Tomorrow's daily-check will pick it up automatically."*

---

## Step 7: Show summary + confirm

**Importante:** si el onboarding cubre múltiples marketplaces y/o múltiples product lines, correr Step 3-6 una vez por cada config. **Step 7 se ejecuta UNA sola vez al final, con resumen consolidado de todo lo que se creó.**

Mostrar a Nacho un resumen claro:

```
✅ Onboarding complete — [Brand Name]

Files written (auto-sync to Drive):
  • [filename1].json
  • [filename2].json   ← if multi-marketplace/product

Manifest:          updated (now: N expected clients, version [v])
AdLabs:            team [team_id], profiles [list]
Targets:           ACOS [X]%, TACOS [Y]%, Budget $[Z]/mo (per marketplace if it differs)
Internal Slack:    #[channel] ([channel_id])
Managed ASINs:     [N] products total
Competitor set:    [N] ASINs · Keepa tracking [on/—] · DataDive niche [id/—] · Rank Radar [id/—]
Ficha relevancia:  [N] ASINs ([ok] ok, [no_fiche] sin ficha) → relevance_profiles (Supabase)

⚠️ Pending (if any):
  • [Field X missing — complete before Y]
  • [ASINs not loaded yet]
  • [Slack channel missing]
  • [No competitor ASINs → Monthly Competitive slide runs SQP-only]
  • [Rank Radar just created → organic-rank trend starts next month; first Monthly is baseline]
  • [ASINs sin ficha (no_fiche) → sin vara de atributos; corré "actualizar ficha de [producto] de [Brand]" cuando resuelva]
```

Cerrar con: *"Anything else to adjust, or shall we move on to something else?"*

---

## Step 8 (Optional): Create folders for client deliverables

Si el cliente todavía no tiene carpetas en Drive para reports/exports, avisar a Nacho:

> *"Remember to create the Drive folders if they don't exist yet:*
> *• `Clients/[BrandName]/Weekly Report/`*
> *• `Clients/[BrandName]/Weekly Wins/`*
> *• `Clients/[BrandName]/Monthly Report/`*
> *• `Clients/[BrandName]/Harvests/`*
>
> *The PPC Manager should upload AdLabs exports following: `MMDDYYYY_[BrandName]_[ReportType].xlsx`."*

**Este step es opcional y solo informativo** — no bloquea el onboarding.

> 💡 **Capturá `drive_folder_id` acá si todavía no lo tenés.** Una vez que la carpeta raíz del cliente exista en Drive (`Projects\[BrandName]\`), pedile a Nacho el link y extraé el ID del segmento `.../folders/<ID>`. Guardalo en el config (`drive_folder_id`). Con eso, search-term-harvest (y futuros skills de export) suben/linkean los archivos en la carpeta correcta syncheada con la local, en vez de My Drive raíz. Si queda `null`, esos skills degradan a búsqueda por nombre — funcionan igual, solo que con un fallback menos preciso.

---

## MODE = refresh_fiche  (re-jalar la ficha de un producto que cambió)

Trigger: *"actualizar ficha de [producto/ASIN] de [Brand]"*, *"refrescá la ficha de [Brand]"*,
*"el listing de [producto] cambió, actualizá la ficha"*. Es un push manual — no rehace el onboarding.

1. **Resolver brand + ASINs.** Matchear `[Brand]` contra el manifest/config (Step 1) para tomar `brand_name`,
   `amazon_marketplace`, `managed_asins`. Resolver qué ASIN(s) refrescar:
   - Nacho dio un ASIN → ese.
   - Nacho dio un nombre de producto/línea → matchearlo contra `managed_asins[].name`/`type`.
   - Nacho dijo "toda la ficha" / no especificó producto → todos los `managed_asins`.
   Si no resuelve a ≥1 ASIN → parar y preguntar cuál.
2. **Correr el Step 4.6** (b→d) SOLO para esos ASINs: re-jalar copia + atributos, re-derivar la ficha, y
   **upsert a `relevance_profiles`** pisando únicamente el/los item(s) de esos ASINs dentro de `product_fiche.items`
   (conservar el resto de los ASINs y todo `roots`/`competitors`/`protected_relevant`). `updated_by:"manual-refresh"`.
   Appendear al `change_log`: `"<today>: ficha refrescada a mano — ASIN(s) [..] (motivo: listing actualizado)."`
3. **Confirmar:** `Ficha de {brand} actualizada: [ASIN(s)] re-jalados ({ok} ok, {no_fiche} sin ficha).`
   Si Nacho lo mencionó junto a un cambio de listing, sugerir registrarlo también en el `client-changelog`.

---

## Edge cases

| Situation | Behavior |
|---|---|
| Brand ya está en manifest + config existe | Step 1 detecta; preguntar update vs new marketplace vs start fresh |
| Brand en manifest pero config faltante en Drive | Avisar a Nacho que es un "manifest huérfano" — ofrecer crear el config ahora |
| Config en Drive pero no en manifest | Avisar; agregar al manifest después de confirmar con Nacho |
| `adlabs_team_id` / `adlabs_profile_id` desconocidos | Guardar `null`, warn explícito sobre impacto en daily-check |
| Multi-marketplace | Correr Step 3-6 una vez por marketplace (cada uno = file separado + entry separada en manifest) |
| Multi-product line (mismo marketplace) | Correr Step 3-6 una vez por línea; team_id y profile_id se comparten |
| Slack channel `-alerts` no encontrado | Guardar `null`, dejar nota en `notes`, continuar |
| `Write` al folder local falla | Verificar que la carpeta existe (`CONFIGS_DIR`); si no, avisar a Nacho que Drive Desktop puede estar desconectado. No usar `create_file` de Drive MCP como fallback (crea duplicates). |
| Drive Desktop sync lag (config recién escrito no aparece en Drive en el momento del próximo daily-check) | Nacho ve el cliente recién onboardeado el día siguiente. Sync típico es <1 min, lag mayor a 10 min indica problema de Drive Desktop a resolver fuera del skill. |
| Update existente con campos vacíos | NO sobreescribir con `null` — preservar valor anterior salvo que Nacho lo cambie explícitamente |
| Brand_name con caracteres especiales | Normalizar para filename pero preservar exacto en `brand_name` del JSON (case + apostrophes incluidos) |
| Listing no resuelve en ninguna fuente (H10 + catalog fallan para un ASIN) | `status:"no_fiche"`; NO inventar ficha. El daily juzga ese ASIN con lógica conservadora. Reportarlo en el resumen. |
| Sophie Hub store no resuelve | Armar la ficha solo con la copia de texto (H10); sin atributos estructurados. No bloquea. |
| Perfil v1 existente al hacer upsert de ficha | Migrar a v2 primero (envolver roots/competitors, derivar scope) antes de escribir `product_fiche`. Nunca pisar lo aprendido. |
| Multi-marketplace | La ficha se upserta con la brand key del marketplace (ej. `"Happy Fox (CA)"`), una corrida por config. |
| Refresh de ficha para brand sin perfil aún | Crear el perfil v2 con la ficha (como en un onboarding nuevo). |
| Manifest ausente en Drive | Crear uno nuevo con el cliente recién onboardeado como primer entry, mismo schema que el spec en `_active_clients.json` |
