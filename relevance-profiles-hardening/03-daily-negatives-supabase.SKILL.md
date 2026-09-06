---
name: daily-negatives-supabase
description: >
  PILOT (Supabase) copy of daily-negatives. Para UN cliente: extrae los search terms con
  clicks y CERO ventas de AYER (t-1) desde AdLabs (Shurq fallback), los pasa por el filtro
  de relevancia semantica (solo sobreviven los IRRELEVANTES), le asigna a cada uno un nivel
  de CONFIANZA (high/medium/low) + EVIDENCIA + BASIS usando la FICHA DE PRODUCTO del perfil v2
  como vara, clasifica cada uno como negative PHRASE o EXACT, y hace UPSERT de la fila del dia a Supabase (tabla
  dashboard_snapshots, tipo='negatives', una fila por dia) en vez de escribir un JSON local.
  Lee el config y el perfil de relevancia desde Supabase (tablas clients y
  relevance_profiles). Dos modos activos: 'run' (default, por cliente → upsert) y 'learn'
  (escribe los aprendizajes DIRECTO a la tabla relevance_profiles de Supabase). El modo
  'compose' (master dashboard 4 tabs) NO esta migrado todavia — vive en el composer del
  master, se migra al final de Fase B. Trigger SOLO con fraseo piloto explicito:
  "run daily-negatives-supabase for [Brand]", "negativos supabase para [Brand]",
  "learn supabase para [Brand]".
---

# Daily Negatives — Per-Client (Master Dashboard, Fase 1)

**Versión:** V2.0 SUPABASE (2026-09-06) — endurecimiento de confianza. Sube de V1.0. Cambios de V2.0:
(1) este skill es ahora **la fuente del motor de juicio endurecido** (antes se remitía a `negative-targeting`
Step 3b, hoy suspendido; el criterio vive acá, ver Step 4); (2) cada Irrelevante lleva **`confidence`
(high/medium/low) + `evidence` + `basis` (profile/model/rule)** con una rúbrica explícita — es lo que
gobierna el gate del autopush (`high`+`medium` se pushean solo, `low` va a tu review); (3) la **vara** del
juicio es la **ficha de producto** (`product_fiche`) del perfil `relevance-profile-v2`, no una ficha inferida
de un label de ASIN; (4) el perfil se lee **v1 o v2** (retrocompat); (5) el snapshot pasa a
`daily-negatives-snapshot-v4` (candidatos con confidence/evidence/basis); (6) `MODE=learn` escribe `roots`/
`competitors` como **objetos v2** con confidence+evidence. Ver `relevance-profiles-hardening/01-relevance-profile-v2.md`.

**Historial:** V1.0 SUPABASE (2026-08-02) — copia piloto de `daily-negatives` V1.2, config + perfil desde
Supabase, upsert fila-por-día a `dashboard_snapshots`, `learn` directo a `relevance_profiles`, `compose` no migrado.

> **🧪 ESTO ES EL PILOTO.** Lee/escribe Supabase, no disco. El `daily-negatives` original queda intacto alimentando tu master dashboard local.

**El motor de juicio endurecido vive acá** (Step 4). `negative-targeting` está suspendido; no se remite más a él.
Ventana diaria, **nada de términos relevantes en el output** (Nacho: "los que tienen relación directa con mi
producto no deberían aparecer"), destino = dashboard. Cada Irrelevante lleva confidence/evidence/basis para el gate.

## Constants

```
Fuente de datos:  Supabase (conector Supabase MCP, proyecto POD 66 - Organization)
  Config cliente:      tabla public.clients (columna config JSONB) — brand_name, adlabs_team_id, adlabs_profile_id, managed_asins, etc.
  Perfil relevancia:   tabla public.relevance_profiles (columna profile JSONB), schema relevance-profile-v2:
                       { brand_name, config_stem, schema:"relevance-profile-v2",
                         product_fiche:{items:[{asin,name,line,status,attributes_present{...7 dims...},
                                        attributes_absent:[{attr,evidence}],source_listing,...}]}  <- LA VARA,
                         roots:[{root,match,reason,confidence,evidence,basis,...}],
                         competitors:[{name,reason,confidence,evidence,basis,monitor_only,...}],
                         protected_relevant:[{term, reason, scope}]  <- scope: equals|contains; excepciones
                                        que NUNCA se negativizan; última palabra sobre roots/competitors Y el juicio;
                         updated, updated_by, change_log:[...] }
                       RETROCOMPAT: si el perfil todavía es v1 (roots/competitors como strings, sin
                       product_fiche, protected sin scope) → leerlo con las reglas de retrocompat del
                       schema v2 (ver relevance-profiles-hardening/01-relevance-profile-v2.md).
  Snapshots negatives: tabla public.dashboard_snapshots, tipo='negatives', UNA FILA POR DÍA
                       (clave única cliente,tipo,fecha). El registro de 7 días = query de los últimos 7 días.
Timezone:  America/Argentina/Buenos_Aires (ART)
AdLabs:    entity search_term. team_id/profile_id del config.
Slack/XLSX/deploy: NADA en modo run (igual que el original). El compose (master 4 tabs) no está en este skill.
```

---

## MODE = run  (default — un cliente)

### Step 1 — Resolver + cargar config (desde Supabase)
Resolvé el `requested_brand` contra la tabla `clients` de Supabase (igual que `daily-check-client-supabase` Step 1b):
```sql
select brand, active, config from public.clients
where lower(brand)=lower('<requested_brand>')
   or exists (select 1 from jsonb_array_elements_text(coalesce(config->'alternative_names','[]'::jsonb)) a where lower(a)=lower('<requested_brand>'));
```
Zero rows / `config` null → STOP y listá `select brand from public.clients where active`. Tomá `cfg = config`. Requeridos: `brand_name`, `adlabs_team_id`, `adlabs_profile_id`. Multi-marketplace = 1 corrida por config (el `brand` ya distingue US/CA, ej. "Happy Fox (CA)").

Construir `product_context` (marca, category, description desde `notes.client_overview.product_description` o `product_portfolio.structure`, lista de ASINs con `name`) — idéntico a negative-targeting Step 1.

### Step 2 — Ventana = AYER (t-1) — ANCLADA A ART
```python
from datetime import datetime, timedelta
import zoneinfo
today_art = datetime.now(zoneinfo.ZoneInfo("America/Argentina/Buenos_Aires")).date()
y = (today_art - timedelta(days=1)).isoformat()   # ventana = ayer (ART)
# DATE = y → y  (un solo día)
```
> **⚠️ Anclar SIEMPRE a ART, no a `date.today()`.** El entorno de las Routines corre en UTC; usar `date.today()` haría que, corriendo entre ~21:00 y 24:00 ART, "hoy"/"ayer" salgan un día adelantados (fecha UTC). `today_art` lo evita. Además, la `fecha` de la fila del snapshot (Step 5) = `today_art` (el día del run en ART).

Ventana SIEMPRE ayer. (No hay lag-risk material: el filtro semántico solo deja irrelevantes, que no venderían igual.)

### Step 3 — Pull search terms de ayer (AdLabs primario / Shurq fallback)
```
get_entity_data(entity_type="search_term", team_id, profile_id=str(profile_id), filters=[
  DATE >= y, DATE <= y,
  CLICKS >= 1,
  ORDERS = 0,
  CAMPAIGN_STATE = ENABLED
])
```
> ⚠️ NO usar los filtros select `SEARCH_TERM_NEGATED=false` ni `SEARCH_TERM_BRAND_ASIN=false`: en el test 2026-07-04 (Natchiketa) devolvieron 0 (no populan en todas las cuentas). La exclusión de **marca propia** y **ya-negados** se hace en el juicio (marca propia → Relevante/nunca negar; ya-negados → el dashboard igual los muestra pero Nacho los saltea). 

Dedup por término: `group_by_column(columns="search_term")` (recalcula clicks/spend sumados cross-campaña). Para volumen alto, exportar con `download_data` a CSV y parsear (evita volcar ~100 columnas al contexto). Guardar `pool_total`, `pool_clicks`, `pool_spend` (totales del pool). **Al deduplicar, CONSERVAR por término la(s) campaña(s)/ad-group(s) de origen** (`campaign_name`/`ad_group_name`, y el ASIN anunciado si está disponible) — se usan en Step 4b para asignar el producto/línea.

**⛔ Excluir campañas Scavenger (regla de Nacho — OBLIGATORIO):** ANTES de deduplicar, descartá del pull todas las filas cuya campaña de origen (`campaign_name`) contenga la palabra `scavenger` (case-insensitive). Consecuencia: un término que SOLO venía de campañas Scavenger desaparece del pool; uno que además tiene clicks en campañas NO-Scavenger sobrevive, pero solo con esos clicks/spend de las no-Scavenger. Motivo: las campañas Scavenger son de descubrimiento intencional — sus search terms zero-sale NO son waste a negativizar. Los totales `pool_total`/`pool_clicks`/`pool_spend` se calculan sobre el pool YA filtrado.

Fallback Shurq: `negative_keyword_finder(start_date=y, end_date=y)` si AdLabs falla. Si ambos fallan → snapshot con `status:"datafail"` y `candidates:[]`.

### Step 4 — Juicio de relevancia (PASO DEL MODELO) — solo IRRELEVANTES, con confianza
Cargar el perfil desde Supabase (`select profile from public.relevance_profiles where brand = '<brand_name>'`).
Leerlo **v1 o v2** (retrocompat: strings de roots/competitors → objetos `confidence:"high", basis:"profile"`;
protected sin `scope` → derivar del `reason`). Evaluar EN ESTE ORDEN:

1. **Excepciones protegidas (PRIMERO — última palabra):** chequear `protected_relevant` (`{term, reason, scope}`) ANTES que nada. Si un término del pool matchea → **Relevante directo**, NO va al snapshot, gana sobre roots/competitors y sobre el juicio del modelo. Alcance por `scope`: `contains` = contención/wildcard (raíz de marca/atributo propio, ej. `woodland` protege `woodland animal theme nursery`); `equals` = solo igualdad case-insensitive (descriptor de categoría, ej. `spiced rum` protege la búsqueda pelada pero `liverpool lost dock spiced rum` **SÍ** se niega). Retrocompat sin `scope`: derivarlo del `reason` ("SOLO igualdad"/"equality only" → equals; "todo lo que incluya"/raíz de marca → contains; ante la duda → equals).
2. **Perfil que aprende (híbrido) → `basis:"profile"`, `confidence:"high"`:** los `roots`/`competitors` ya confirmados en el perfil se marcan **Irrelevante directo con confianza ALTA** (ya pasaron por el ojo de Nacho) — **salvo que hayan quedado protegidos en el paso 1**, y salvo `competitors` con `monitor_only:true` (esos son Relevante/no negar). `evidence` = `"root del perfil: <root>"` / `"competitor del perfil: <name>"`. El resto lo juzga el modelo.
3. **La VARA = `product_fiche` del perfil.** Para cada ASIN/línea usar `attributes_present` (las 7 dimensiones) y `attributes_absent` (ausencias explícitas) como la ficha real contra la que se juzga. Si el perfil **no** trae `product_fiche` (v1 sin migrar, o ASIN `no_fiche`) → caer a la ficha inferida de `product_context` (lógica de hoy) y **el juicio de ese producto nunca llega a `high` por attribute-mismatch** (sin vara confiable de ausencia).
4. **Juzgar cada término** (`basis:"model"`, en tandas si es grande): Relevante SOLO si producto base + TODOS los calificadores matchean la ficha. Salida **binaria** (Relevante/Irrelevante). Motivos de irrelevancia: `competitor brand`, `licensed character`, `off-category`, `DIY / craft intent`, `attribute mismatch`. **Marca propia → Relevante (nunca negar).** A cada Irrelevante asignarle `confidence` + `evidence` según la **rúbrica de abajo**.
5. **Reglas determinísticas → `basis:"rule"`, `confidence:"high"`:** marca propia (Relevante), ASIN (ver Step 4b), char no-negable, etc.
6. **Solo los Irrelevante pasan al snapshot.** Los Relevante NO aparecen (regla de Nacho). Cada Irrelevante lleva `confidence`, `evidence`, `basis`.

#### Rúbrica de confianza (OBLIGATORIA — gobierna el gate del autopush)
Regla de oro: **si la irrelevancia no se puede fundamentar con evidencia concreta, NO es `high`.**

- **`high`** — verificable sin criterio opinable:
  - matchea un `root`/`competitor` del perfil (`basis=profile`), o
  - **marca ajena reconocida con certeza** (marca conocida, no "parece"), o
  - **off-category inequívoco** (palabra clara de otra categoría: `furniture`, `diapers`), o
  - **attribute mismatch donde el atributo pedido está en `attributes_absent`** de la ficha (ausencia EXPLÍCITA).
  - `evidence` = el hecho: `"bamboo ∈ attributes_absent"`, `"off-category: furniture"`, `"marca reconocida"`.
- **`medium`** — probable pero apoyada en inferencia:
  - **"parece" nombre de marca** ajena no reconocida, o
  - **equivalencia de dominio** aplicada (declararla en `evidence`), o
  - **attribute mismatch donde el atributo NO está** ni en present ni en absent (no confirmable), o
  - la ficha del ASIN es **`no_fiche`** / el perfil no trae `product_fiche` (juicio sin vara → nunca high).
- **`low`** — señal débil / ambiguo: el modelo se inclina a Irrelevante pero con dudas.

**Recordá el gate (lo aplica `daily-negatives-autopush`):** `high`+`medium` se autopushean; `low` va a tu review
en el dashboard. Por eso `evidence` tiene que ser legible de un vistazo. **PROHIBIDO** inflar a `high` sin el
hecho que lo respalde: un `high` mal puesto se pushea solo y mata tráfico bueno.

**Match type (default; Nacho ajusta en el dashboard con el toggle):**
- `root` = la raíz a negar como PHRASE cuando es una **familia limpia** que el cliente nunca va a querer: marca/competidor (ej. `little unicorn`, `burts bees`), personaje licenciado (`winnie the pooh`), material/feature ajeno (`bamboo`, `weighted`, `upf`), intent DIY (`fabric`, `pattern`, `crochet`), categoría ajena con palabra clara (`furniture`, `diapers`). → `match:"phrase"`, `root:"<raíz>"`.
- `exact` = junk de título de ASIN ajeno (shoes/shorts/dog toys/etc.), mismatch de atributo puntual sobre buen producto base, o size mismatch (twin/queen). → `match:"exact"`, `root:""`.
- Nuance heredado de negative-targeting: ahí un attribute mismatch iba SIEMPRE Exact (proteger el base). Acá, familias limpias de atributo (weighted/bamboo/upf) van Phrase por default porque el cliente nunca las vende. El toggle del dashboard es la última palabra.

### Step 4b — Tipo (asin/keyword) y Producto (línea/parent) — por cada candidato Irrelevante
- **kind:** `asin` si el término matchea `^b0[a-z0-9]{8}$`, else `keyword`.
- **⚠️ Términos tipo-ASIN — INCLUIRLOS SIEMPRE (regla de Nacho 2026-08-02, NO auto-excluir):** un search term que ES un ASIN no se juzga semánticamente (es un código, no una frase), así que NO pasa por el motor de relevancia del Step 4 y **NO se excluye** — ni por el tipo de campaña (Subs/Comps-Close/PT) ni por "no puedo verificar el producto sin lookup". Tratamiento determinístico:
    1. Si el ASIN es uno de los `managed_asins` del PROPIO cliente (mirar `cfg.managed_asins`) → es self-targeting, NO es negativo → descartarlo.
    2. Cualquier OTRO ASIN con clicks≥1 y 0 ventas → **incluir como candidato** `kind:"asin"`, `match:"exact"`, `root:""`, `reason:"ASIN target ajeno zero-sale — revisar en dashboard"`, `product` = la línea del ASIN anunciado (Step 4b, o "General (sin asignar)").
  El dashboard es el filtro humano (Nacho selecciona antes de aplicar), así que surfacearlos es lo correcto — NO retenerlos por incertidumbre. (Si en el futuro se quiere que el modelo verifique la identidad de cada ASIN, se suma un lookup; por ahora se incluyen por defecto.)
- **product (línea/parent, AUTO — editable en el dashboard):** asignar la **LÍNEA de producto a nivel PARENT** (no child) del producto anunciado en la campaña/ad-group donde el término quemó clicks (conservado en Step 3). Mapear por: (a) ASIN anunciado → su parent vía `managed_asins`, o (b) el nombre de campaña/ad-group (suele codificar la línea). Si no se puede determinar → `"General (sin asignar)"`. Es híbrido: el dashboard lo deja re-asignar.
  - **PARENT, no child:** en Natchiketa (1 parent, 18 prints) todo va a la única línea = *across the board*; en Masofta las líneas son `Hair Growth Serum` (agrupa 50ml+30ml), `Shea Butter Lip Balm`, `Body Glue`.
- **`client.products` (lista de líneas):** derivar de `managed_asins` colapsando children a su parent (por `parent_asin`; agrupar variantes obvias de la misma línea, ej. serum 50ml/30ml → "Hair Growth Serum"). Formato `[{asin, name}]` (asin = parent representativo). Incluir siempre `{"asin":"","name":"General (sin asignar)"}` al final.

### Step 5 — Upsert de la fila del día a Supabase (row-per-day)
> **Cambio clave del piloto:** el registro de 7 días ya NO es un array `days[]` que se lee-modifica-escribe. Cada día es **una fila** en `dashboard_snapshots` (`tipo='negatives'`, `fecha=hoy`). El upsert pisa la fila del mismo día (idempotente en re-runs). El master composer reconstruye el registro de 7 días con una query (`fecha >= hoy-6`). Nunca inferir "aplicado" por ausencia — cada día queda preservado como su propia fila.

1. Armá el objeto `datos` de HOY. Ojo la diferencia con el original: en vez de `client.days[]` (array), esta fila lleva UN solo `day` (el de este run). El composer junta el `day` de las últimas 7 filas para reconstruir `days[]`.
```json
{ "schema":"daily-negatives-snapshot-v4","generated_at_iso":"<ISO ART>",
  "meta":{"title_date":"...","short_date":"Aug 1","window_label":"Ayer · <Mon D>","pull_time":"HH:MM ART","data_source":"adlabs"},
  "client":{"brand_name":"...","marketplace":"US","currency_prefix":"$","status":"ok|datafail",
    "product_summary":"...","window_days":7,
    "products":[{"asin":"<parent>","name":"Hair Growth Serum"}, ... ,{"asin":"","name":"General (sin asignar)"}]},
  "day":{ "date_iso":"<ventana = ayer>","date_label":"Aug 1","window_label":"Ayer · Aug 1",
          "pool_total":N,"pool_clicks":N,"pool_spend":F,"candidates_spend":F,
          "candidates":[{"term":"...","clicks":N,"spend":F,"match":"phrase|exact","root":"...","reason":"...",
                         "confidence":"high|medium|low","evidence":"<hecho verificable>","basis":"profile|model|rule",
                         "kind":"keyword|asin","product":"<linea/parent>","origin_campaign":"<campaña de origen>","origin_ad_group":"<ad group de origen>"}]} }
```
> **Nuevo en v4:** cada candidato lleva `confidence` (high/medium/low) + `evidence` (hecho corto y verificable)
> + `basis` (profile/model/rule). El autopush usa `confidence` como gate; el dashboard muestra `evidence`
> al lado de cada LOW para que Nacho decida rápido. `kind:"asin"` (Step 4b) → `confidence:"high"`, `basis:"rule"`,
> `evidence:"ASIN target ajeno zero-sale"`.
> **`origin_campaign`/`origin_ad_group` (agregado 2026-08-30):** la campaña/ad-group de origen que ya
> conservás en Step 3 (para asignar el producto en Step 4b) ahora se **persiste** en cada candidato. Los
> consume `daily-negatives-autopush`: cuando un candidato queda retenido con `product="General (sin asignar)"`,
> el informe diario (tab Push del Master Dashboard) muestra el origen para que Nacho decida la línea. Si hay
> varias campañas de origen, guardá la de mayor spend (o unilas con `; `). Retro-compat: si faltan, quedan `""`.

`candidates` = irrelevantes de hoy (con 0 → `candidates:[]`). `candidates_spend` = suma spend de candidatos. `currency_prefix` = `CA$` si marketplace CA, else `$`. El `date_iso`/labels dentro de `day` describen la **ventana de datos (ayer)**, para display.

2. Upsert vía el conector Supabase `execute_sql` (dollar-quote el JSON con tag `$neg$`, que no aparece en el contenido):
```sql
insert into public.dashboard_snapshots (cliente, tipo, fecha, datos)
values ('<brand_name>', 'negatives', '<YYYY-MM-DD>', $neg$<el objeto datos>$neg$::jsonb)
on conflict (cliente, tipo, fecha)
do update set datos = excluded.datos, actualizado = now();
```
- `cliente` = `cfg["brand_name"]` (debe igualar `clients.brand`).
- `tipo` = `'negatives'`.
- `fecha` = **HOY, el día del run en ART** (`YYYY-MM-DD`) — es la clave del día en el registro. (La ventana de DATOS es ayer/t-1, pero la FILA se indexa por el día del run, consistente con `daily_check`.)
- `datos` = el objeto de arriba.

**No** deployar acá (el master dashboard es el compose, que no está migrado en este skill). Confirmá: `Fila negatives (Supabase) escrita para {brand} — {fecha}: {n} candidatos ({kw} kw / {as} asin) — confianza: {high} high / {medium} medium / {low} low.`

---

## MODE = compose  — NO MIGRADO EN ESTE SKILL
El master dashboard de 4 tabs (Daily / Negatives / Harvest / Restock) se compone leyendo las 4 fuentes. Como todavía faltan migrar `restock` y `harvest` a Supabase, **el master composer se migra al FINAL de Fase B**, en su propio skill. Mientras tanto, el `daily-negatives` **original** conserva su compose local para tu master dashboard actual.

Si alguien dispara este skill en modo compose → **STOP** y respondé: `El compose del master no está migrado a Supabase todavía (se hace al final de Fase B). Para el master dashboard actual usá el daily-negatives original (local).`

Diseño previsto para cuando se migre: el composer leerá de Supabase — negatives = `select cliente, datos from public.dashboard_snapshots where tipo='negatives' and fecha >= <hoy-6> order by cliente, fecha desc` y reconstruye `client.days[]` juntando el `day` de cada fila por cliente (contexto de cliente de la fila más nueva); daily/harvest/restock = sus respectivos `tipo`. Render + deploy = igual patrón que `daily-check-dashboard-supabase`.

---

## MODE = learn  (aprendizaje — actualiza el perfil de relevancia EN SUPABASE)
Trigger: "learn supabase para [Brand]" / "actualizar perfil de relevancia de [Brand]" + **(a)** el bloque pegado del dashboard (líneas `term\tmatch\treason[\tproduct]`) y/o **(b)** notas sueltas en lenguaje natural de Nacho (ej. "`comforter` no se debe negar", "todo lo que incluya `woodland` no negar", "`little unicorn` es competidor a monitorear, no negar").

> **PILOTO: el perfil se LEE y se ESCRIBE en la tabla Supabase `relevance_profiles` (columna `profile`), NO en un archivo local.** Supabase es la fuente de verdad de los perfiles.

1. Resolver el brand contra `clients` (mismo query que Step 1). Tomá `brand` = `clients.brand`.
2. Cargar el perfil actual: `select profile from public.relevance_profiles where brand = '<brand>'`. Si no existe, arrancá uno nuevo schema `relevance-profile-v2`: `{brand_name, config_stem, schema:"relevance-profile-v2", product_fiche:{items:[]}, roots:[], competitors:[], protected_relevant:[], updated, updated_by, change_log:[]}`. **Si el perfil es v1 → migralo a v2 primero** (envolver roots/competitors como objetos, derivar `scope` de protected; ver `relevance-profiles-hardening/01-migrate-v1-to-v2.py`). NO tocar `product_fiche` (lo maneja el onboarding).
3. **Del bloque del dashboard:** por cada línea, agregar como **objeto v2**:
   - `match=phrase` → `roots += {root:"<raíz>", match:"phrase", reason, confidence:"high", evidence:"confirmado por Nacho en review <fecha>", basis:"profile", added_by:"learn", added_on:<hoy>, confirmations:1}`. Si el `root` ya existía → subir `confirmations` en 1 (más confirmaciones = más confianza) en vez de duplicar.
   - `reason` contiene `competitor`/`licensed` → `competitors += {name:"<marca>", reason, confidence:"high", evidence:"confirmado por Nacho", basis:"profile", added_by:"learn", added_on:<hoy>, confirmations:1, monitor_only:false}`.
   Dedup por `root`/`name` (case-insensitive), merge (nunca borrar histórico). Un término que Nacho aprueba desde el carril LOW entra por acá → la próxima corrida lo toma como `basis=profile`/`high` y se autopushea solo (el círculo que gana confianza con el uso).
4. **De las notas en lenguaje natural** → agregar `{term:"X", reason:"<motivo>", scope:"equals|contains"}` a `protected_relevant`. **Fijá el `scope` explícito:** raíz de marca/atributo propio o "todo lo que incluya X" → `contains`; **descriptor de categoría** (ej. "spiced rum") que solo debe proteger la búsqueda genérica → `equals`. Ante la duda → `equals`. (Nota "competidor a monitorear, no negar" → agregar/actualizar el `competitor` con `monitor_only:true`, no a protected.) Dedup por `term`.
5. **⚠️ Chequeo de conflicto OBLIGATORIO (antes de guardar):** por cada `term` de `protected_relevant`, si coincide con un `root`/`competitor` existente según su `scope` (`equals` → solo igualdad; `contains` → contención) → **removerlo** (gana la excepción) y registrar la reversión en `change_log`. La excepción SIEMPRE gana; nunca dejar un término a la vez protegido y en roots/competitors.
6. Actualizá `updated`/`updated_by`, appendeá una línea de resumen al `change_log`, y **upserteá a Supabase** (dollar-quote con tag `$prof$`):
```sql
insert into public.relevance_profiles (brand, profile)
values ('<brand>', $prof$<el profile JSON actualizado>$prof$::jsonb)
on conflict (brand) do update set profile = excluded.profile, updated = now();
```
Confirmá `Perfil (Supabase) de {brand}: +{k} roots, +{m} competidores, +{p} protegidos ({c} conflictos resueltos).`
En la próxima corrida del feeder, el Step 4 aplica `protected_relevant` PRIMERO (última palabra) y luego roots/competitors → consistencia y menos trabajo del modelo.

---

## Scheduling (PILOTO — Routines de nube, no tareas locales)
- **Feeder (modo run):** una Routine que recorre los clientes activos y corre este skill por marca, a **mediodía ART** (ventana separada del Daily Check de las 9am). Mismo patrón que el feeder de `daily-check`: batchear los pulls de AdLabs donde se pueda, continue-on-error, connectors **Supabase + Adlabs + SHURQ**, sin repo. NO necesita carpeta local (todo Supabase).
- **Compose (master):** no migrado (ver MODE=compose). Se agenda cuando exista el master composer de Supabase, al final de Fase B.
- Multi-marketplace = ya cubierto (cada marca CA es su propio `brand`, ej. "Happy Fox (CA)").

## Edge cases
| Situación | Comportamiento |
|---|---|
| Ayer sin data (lag/fin de semana) | Pool 0 → snapshot con candidates:[] + status ok. Dashboard muestra "sin candidatos". |
| Filtros select AdLabs (NEGATED/BRAND_ASIN) devuelven 0 | No usarlos; filtrar por CLICKS/ORDERS/CAMPAIGN_STATE y excluir marca propia en el juicio. |
| Marca propia en un término | Relevante — nunca negar. |
| Término en `protected_relevant` | Relevante SIEMPRE — nunca va al snapshot. Gana sobre roots/competitors y sobre el juicio del modelo (Step 4.1). Match por igualdad o contención (wildcard). |
| Término protegido que también figura en roots/competitors | Conflicto: en MODE=learn se remueve de roots/competitors (gana la excepción) y se loguea en `change_log`. |
| Término relevante | NO va al snapshot (regla de Nacho). |
| Pool enorme | Juzgar en tandas; nunca subir el piso de clicks (≥1 es el corazón). |
| Ni AdLabs ni Shurq | status:"datafail", candidates:[]. |
| Perfil sin `product_fiche` (v1 sin migrar) | Juzgar con la ficha inferida de `product_context` (lógica de hoy); ningún juicio llega a `high` por attribute-mismatch. Correr onboarding/refresh de ficha para tener la vara real. |
| ASIN con `product_fiche.status="no_fiche"` | Sin vara de atributos para ese producto → su attribute-mismatch no llega a `high` (queda medium/low). |
| `competitor` con `monitor_only:true` | Relevante — nunca negar (se monitorea, no se niega). No va al snapshot. |
| Duda entre high y medium | Bajar a `medium` (nunca inflar a high sin evidencia). Sigue siendo autopush, pero deja el hecho explícito. |
| Config sin product_description y sin product_fiche | Juicio más conservador; igual reconoce marcas/off-category. Backfillear vía onboarding (ficha) y product_description. |
