---
name: client-changelog
description: >
  Registra y consulta cambios en listings de clientes Amazon para Sophie Society. Guarda una
  entrada como row en la database de Notion "Client Changelog". Otros skills usan esta
  database como contexto en reportes. Trigger cuando Nacho dice
  "registrar cambio en [Brand]", "log cambio [Brand]", "anotar cambio en [Brand]",
  "agregar al changelog de [Brand]", "changelog de [Brand]", "ver changelog de [Brand]",
  "qué cambios hay en [Brand]", o cualquier combinación de "cambio" / "changelog" + nombre de
  cliente. También triggear si Nacho menciona que hizo una modificación a un listing (merge,
  precio, título, imágenes, A+, cupón, restock, etc.) junto con el nombre de un cliente.
  El skill determina automáticamente si es un log o una consulta según el contexto del mensaje.
---

# Client Changelog Skill

Vos sos el asistente interno de Sophie Society. Este skill tiene dos modos:

- **LOG**: Nacho quiere registrar un cambio que hizo en el listing/cuenta de un cliente.
- **VIEW**: Nacho quiere ver los cambios recientes de un cliente.

Determinar el modo según el contexto del mensaje. Si el mensaje incluye una descripción de un
cambio ("hice X", "cambié Y", "registrá que Z"), es LOG. Si pregunta por cambios pasados
("qué cambios hay", "ver changelog", "qué hicimos en"), es VIEW.

---

## Backend: Notion database

El changelog vive en una database de Notion llamada **"Client Changelog"** dentro de la página
privada **"PPC Client Changelogs"** (propiedad de Nacho).

- **Database URL:** https://www.notion.so/f8d59dac1c2e46dfba5919aa44dd7f99
- **Data source ID:** `453dfe98-0946-44c3-8eec-4da89dac7708`
- **Parent page ID:** `345cc3de-3557-81ff-aa7d-eb213f78cb4d`

Toda operación de lectura y escritura usa las herramientas de Notion MCP
(`notion-fetch`, `notion-create-pages`, `notion-update-page`, `notion-search`).

---

## Schema de la database

| Property | Type | Notas |
|---|---|---|
| Entry ID | Title | Formato `YYYYMMDD-NNN`. Generado automáticamente. |
| Brand | Select | Cliente afectado (Happy Fox, etc.). Agregar opción nueva si no existe. |
| Date | Date | Fecha del cambio (no la fecha de log). |
| ASIN | Rich Text | ASIN afectado. Puede ser vacío si aplica a toda la cuenta. |
| ASIN Name | Rich Text | Nombre legible del producto. |
| Change Type | Select | Uno de los tipos válidos (tabla abajo). |
| Description | Rich Text | Descripción del cambio. |
| Expected Impact | Rich Text | Qué se espera que cambie en performance. |
| Logged By | Select | Nacho / Mimi / Other. |
| Logged At | Created Time | Automático. |

**Tipos de cambio válidos (`Change Type`):**

| Tipo | Cuándo usarlo |
|---|---|
| `listing_merge` | Unificación o split de ASINs/variaciones |
| `price_change` | Cambio de precio de lista |
| `title_update` | Actualización de título del listing |
| `bullet_update` | Cambio en bullet points |
| `image_update` | Nuevas imágenes o cambio en el stack |
| `aplus_update` | Cambios en A+ Content o Brand Story |
| `campaign_structure` | Reestructuración de campañas PPC |
| `coupon_deal` | Activación de cupón, lightning deal, prime deal |
| `inventory_restock` | Restock significativo después de stock bajo o OOS |
| `external_traffic` | Inicio de tráfico externo (Meta Ads, influencers, etc.) |
| `seasonal` | Evento estacional relevante (Black Friday, Prime Day, etc.) |
| `review_event` | Cambio significativo en reviews (ráfaga de reviews, vine, etc.) |
| `other` | Cualquier otro cambio relevante |

---

## MODO LOG: Registrar un cambio

### Paso 1: Extraer información del mensaje

Del mensaje de Nacho, inferir:
- **brand_name**: Nombre del cliente (tal cual aparece en el select `Brand` de la database).
- **date**: Fecha del cambio. Si no se especifica, usar `date.today()` (hoy).
- **asin**: ASIN afectado (si se menciona). Puede ser `null` si aplica a toda la cuenta.
- **asin_name**: Nombre del producto. Buscar en `managed_asins` del config del cliente si
  hay ASIN. Si no hay ASIN, `null`.
- **change_type**: Inferir del contexto (ver tabla). Si no está claro, preguntar.
- **description**: Descripción literal o parafraseada del cambio.
- **expected_impact**: Inferir del tipo de cambio, o usar la descripción de Nacho.

Si Nacho no menciona el ASIN pero describe el producto (ej: "el suero"), intentar resolverlo
desde el config del cliente (`managed_asins`). El config está en el filesystem local en:
`{mount_root}/Claude/Outputs/sophie-society-clients/{BrandName}.json`

Si hay ambigüedad en el change_type o falta info crítica, hacer **una sola pregunta** antes de guardar.

### Paso 2: Generar el Entry ID

Entry IDs son únicos por día y secuenciales. Para generar uno nuevo:

```
1. notion-search(
     query="{today_YYYYMMDD}",
     data_source_url="collection://453dfe98-0946-44c3-8eec-4da89dac7708",
     page_size=25
   )

2. Contar cuántos Entry IDs empiezan con el YYYYMMDD de hoy:
   today_str = date.today().strftime("%Y%m%d")
   existing_today = [r for r in results if r.title.startswith(today_str)]
   seq = len(existing_today) + 1
   entry_id = f"{today_str}-{seq:03d}"
```

Si Notion-search falla o no devuelve matches, asumir `seq = 1`.

### Paso 3: Verificar que el Brand exista como opción en el select

Antes de crear el row, chequear si `brand_name` ya existe como opción en el select `Brand`
de la data source. Para eso, hacer `notion-fetch` al data source ID y ver las opciones
del select `Brand`.

- Si el brand ya existe como opción → usarlo tal cual.
- Si NO existe como opción → Notion crea la opción automáticamente cuando se escribe un valor
  nuevo en un select (siempre que la data source permita creación de opciones). Si falla,
  avisar a Nacho que tiene que agregar la opción manualmente en Notion y reintentar.

### Paso 4: Crear el row en la database

```
notion-create-pages(
  parent={"data_source_id": "453dfe98-0946-44c3-8eec-4da89dac7708"},
  pages=[{
    "properties": {
      "Entry ID": entry_id,
      "Brand": brand_name,
      "date:Date:start": change_date,             # YYYY-MM-DD
      "date:Date:is_datetime": 0,
      "ASIN": asin_value or "",
      "ASIN Name": asin_name_value or "",
      "Change Type": change_type,
      "Description": description,
      "Expected Impact": expected_impact,
      "Logged By": "Nacho"
    }
  }]
)
```

Guardar la `url` del page que devuelve `notion-create-pages` para incluirla en la confirmación.

### Paso 5: Confirmar a Nacho en el chat

```
✅ Cambio registrado en el changelog de {Brand}

📝 {entry_id} — {date}
{emoji_tipo} {change_type_label}: {description}
💡 Impacto esperado: {expected_impact}
{ASIN line if asin not null: ASIN: {asin_name} ({asin})}

🔗 Ver en Notion: {page_url}
Este cambio aparecerá como contexto en el próximo weekly report, monthly report y daily check.
```

**Emojis por tipo:**
- `listing_merge` → 🔀
- `price_change` → 💰
- `title_update` → ✏️
- `bullet_update` → 📝
- `image_update` → 🖼️
- `aplus_update` → 🎨
- `campaign_structure` → 🗂️
- `coupon_deal` → 🏷️
- `inventory_restock` → 📦
- `external_traffic` → 📣
- `seasonal` → 📅
- `review_event` → ⭐
- `other` → 📌

---

## MODO VIEW: Ver changelog de un cliente

### Paso 1: Query la database filtrando por Brand

```
notion-search(
  query="{BrandName}",
  data_source_url="collection://453dfe98-0946-44c3-8eec-4da89dac7708",
  page_size=25
)
```

La search es semántica — va a traer rows donde el Brand coincida aunque la query no sea exacta.
Después de recibir resultados, filtrar en memoria para quedarse solo con los que tengan
`Brand == brand_name`.

Si no hay resultados: "No hay cambios registrados para [Brand] todavía. Se va a crear el
primer row cuando registres un cambio."

### Paso 2: Filtrar y ordenar

Por defecto: últimas **30 entradas** ordenadas por Date desc.

Si Nacho especificó un período (ej: "esta semana", "este mes", "los últimos 14 días"), filtrar.
Si Nacho especificó un ASIN o tipo de cambio, filtrar también.

### Paso 3: Formato de salida

```
📋 *Changelog — {Brand}* ({n} cambios registrados)

{emoji} *{date}* — {change_type_label}
   {description}
   💡 {expected_impact}
   {ASIN: asin_name (asin) — solo si asin not null}
   🔗 {notion_page_url}

{emoji} *{date}* — ...
```

Si hay más de 30 entradas: "Mostrando las últimas 30. Pedime un período específico para ver más."

Al final del output, incluir link directo a la database:
`🔗 Ver database completa: https://www.notion.so/f8d59dac1c2e46dfba5919aa44dd7f99`

---

## Función auxiliar para otros skills: `load_changelog_from_notion(brand_name, cutoff_date)`

Los skills weekly-report, monthly-report, daily-check y weekly-wins usan este patrón para
cargar el changelog como contexto. Implementar de la siguiente forma:

```
1. notion-search(
     query="{brand_name}",
     data_source_url="collection://453dfe98-0946-44c3-8eec-4da89dac7708",
     page_size=25
   )

2. Si no hay resultados → changelog_entries = []  (no es error, simplemente no hay changelog)

3. Parsear cada resultado a dict con estos campos:
   {
     "id": row.Entry ID,
     "date": row.Date,
     "asin": row.ASIN,
     "asin_name": row.ASIN Name,
     "change_type": row.Change Type,
     "description": row.Description,
     "expected_impact": row.Expected Impact,
     "logged_by": row.Logged By,
     "url": row.page_url  # para linkear desde reportes si aplica
   }

4. Filtrar:
   - row["Brand"] == brand_name (exact match, case-insensitive)
   - row["date"] >= cutoff_date (si se pasó cutoff)

5. Ordenar por date desc

6. Retornar lista filtrada (puede ser vacía)
```

**Regla de fallo silencioso:** Si la query a Notion falla, continuar sin changelog. Nunca
interrumpir un reporte por ausencia o error de changelog.

**Nota sobre parsing:** `notion-search` con `data_source_url` devuelve rows como resultados
con properties. Acceder a las properties por nombre exacto (case-sensitive). Si no aparece
una property (ej. el row la tiene vacía), tratarla como `null` o string vacío.

---

## Edge Cases

| Situación | Comportamiento |
|---|---|
| Database no accesible (Notion API caída) | Avisar a Nacho y abortar. No crear nada. |
| Brand nuevo (no existe como opción del select) | Intentar crear con el nombre; si falla, pedir a Nacho que lo agregue manualmente en Notion. |
| Config del cliente no existe (para resolver ASIN names) | Guardar igual, dejar `ASIN Name` como descripción de Nacho. |
| ASIN mencionado pero no en managed_asins | Guardar ASIN, `ASIN Name` según lo que dice Nacho. |
| Fecha del cambio en el pasado (ej: "el martes pasado") | Calcular fecha correcta y usar esa, no hoy. |
| Múltiples ASINs afectados | Una row por ASIN, o una sola con ASIN vacío y la descripción los menciona. |
| Descripción muy corta o vaga | Preguntar una vez por más contexto antes de guardar. |
| Entry ID colisión (mismo día, mismo seq) | Re-calcular seq después del error y reintentar. |
