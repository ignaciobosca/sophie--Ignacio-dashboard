# Routines a crear (las armás vos, manual) — Negative Targeting automático

Estas Routines las creás **vos** en tu panel de Routines para que corran bajo tu autorización (sin
aprobaciones manuales). Copiá los prompts tal cual. Todo corre en el entorno **"Daily Check"**
(`env_01PLsdw2426SeBeqP2FQqZNS`, full network), en **sesión nueva por corrida**, sin repo adjunto,
connectors **Supabase + Adlabs**.

## Dónde encaja en tu día (horarios en ART y UTC)

| Hora ART | Hora UTC | Routine | Estado |
|---|---|---|---|
| 06:00–06:30 | 09:00–09:30 | **Daily Negatives** (identificador, en batches de 5) — ya existe | escribe snapshot `negatives` |
| **07:30 + offsets** | **10:30 + offsets** | **Autopush** (en batches de 5) ← NUEVA | lee snapshot, pushea keywords, recibo `negatives_push` |
| 08:30 | 11:30 | **Master Dashboard Composer** — ya existe | publica el dashboard (con el tab Push) |
| Viernes 08:00 | Viernes 11:00 | **Weekly Negatives Review** ← NUEVA | propone archivar (no archiva solo) |

El autopush va **después** del identificador y **antes** del composer, así el push del día ya se ve
en el dashboard de esa mañana.

---

## 1) Autopush diario — en batches de 5 por OFFSET (RECOMENDADO)

**Layout recomendado (igual que tu "Daily Negatives"):** **una Routine por offset**, cada una procesa 5
clientes, escalonadas +5 min. **El prompt es el MISMO en todas** — solo cambia el número de `OFFSET` (0, 5,
10, 15, …). No se nombran marcas: cada Routine toma sus 5 clientes con
`... order by brand limit 5 offset OFFSET`, así que **agregar/sacar clientes no obliga a editar prompts**.

La **cantidad de Routines = ceil(clientes_activos / 5)**: hoy **20 activos → 4 Routines** (offsets 0/5/10/15).
Si pasás a 25 → 5 (agregás offset 20), a 30 → 6, etc.

**Por qué batches y no una sola:**
- **Resiliencia:** si un batch falla (AdLabs tira error, una reference expira), los demás siguen.
- **Entra en la ventana:** ~1h entre el identificador (termina ~06:50 ART) y el composer (08:30 ART); los batches escalonados terminan holgados; una corrida única de todos podría pasarse.
- **Reparte la carga de AdLabs** y mantiene cada sesión corta.
- **Idempotente:** el recibo del día evita duplicados, así que re-correr un batch es seguro.

**Config (todas):** Entorno **Daily Check** · **sesión nueva por corrida** · **sin repo** · Connectors **Supabase + Adlabs** · notificaciones a gusto.

**Una Routine por offset** (arrancando 10:30 UTC / 07:30 ART, +5 min por offset):

| Routine | Cron (UTC) | Hora ART | OFFSET |
|---|---|---|---|
| Autopush - Offset 0  | `30 10 * * *` | 07:30 | 0 |
| Autopush - Offset 5  | `35 10 * * *` | 07:35 | 5 |
| Autopush - Offset 10 | `40 10 * * *` | 07:40 | 10 |
| Autopush - Offset 15 | `45 10 * * *` | 07:45 | 15 |
| (si hay 25+ clientes) Offset 20 | `50 10 * * *` | 07:50 | 20 |

### Prompt — DRY-RUN (recomendado para estrenar)
**El mismo prompt en cada Routine; cambiá solo el número de `OFFSET`.** Escribe el recibo (el tab Push
muestra lo que HARÍA) pero **no aplica nada** a Amazon:
```
En Supabase (proyecto POD 66 "awhiobrcgghyiycxukjm"), tomá los 5 clientes que devuelva:
  select brand from public.clients where active = true order by brand limit 5 offset OFFSET
Corré el skill daily-negatives-autopush en modo DRY-RUN para cada uno de esos 5 clientes:
- Lee el snapshot de negatives de HOY (tipo='negatives', fecha = hoy ART). Si no hay, saltalo.
- Clasifica: ASINs (kind='asin') -> asins_skipped (NO se pushean); keywords con caracteres especiales
  (fuera de [A-Za-z0-9 '&-]) -> dropped(special_char); 'General (sin asignar)' -> held; el resto por linea.
- Deriva el destino por linea con ad_group CONTAINS_ASINS (SP+SB, CAMPAIGN_STATE=ENABLED,
  AD_GROUP_STATE=ENABLED, DATE ultimos 14 dias, EXCLUYENDO campanas con "Scavenger" en el nombre).
- NO apliques a Amazon: crea los previews para el conteo, pero no llames al apply.
- Escribi el recibo a Supabase (tipo='negatives_push', fecha=hoy ART) con summary.mode='dry-run' y
  applied[] = lo que HABRIA creado, mas held/asins_skipped/dropped.
Continua ante error. No pidas confirmacion.
```
En la Routine Offset 0 el OFFSET es 0; en Offset 5 es 5; etc.

### Prompt — APPLY (cuando ya lo validaste)
Igual pero **aplica** los keyword-negatives (mismo patrón de OFFSET por Routine):
```
En Supabase (proyecto POD 66 "awhiobrcgghyiycxukjm"), tomá los 5 clientes que devuelva:
  select brand from public.clients where active = true order by brand limit 5 offset OFFSET
Corré el skill daily-negatives-autopush (modo run / apply) para cada uno de esos 5 clientes:
lee el snapshot de negatives de HOY, pushea los keyword-negatives a AdLabs con el destino auto-derivado
por linea (CONTAINS_ASINS SP+SB, ENABLED, ultimos 14 dias, EXCLUYENDO Scavenger), salteando ASINs
(kind='asin') y terminos con caracteres especiales, y escribi el recibo negatives_push.
Ancla "hoy" a ART. Continua ante error. No pidas confirmacion.
```

### Alternativa — una sola Routine all-clients (mínimo mantenimiento)
Si preferís no mantener varias: 1 Routine, cron `30 10 * * *`, el mismo prompt pero **"para CADA cliente
activo (select brand from public.clients where active = true)"** sin `limit/offset`. Más simple, pero corre
todos en una sola sesión larga (puede pasarse de la ventana del composer; el push igual queda en Supabase
y lo toma el compose siguiente). Segura por la idempotencia, solo menos resiliente/puntual.

---

## 2) Weekly Negatives Review — viernes

- **Cron (UTC):** `0 11 * * 5`  (viernes 08:00 ART)
- **Entorno:** Daily Check · **sesión nueva por corrida** · **sin repo**
- **Connectors:** **Supabase + Adlabs**
- Alcance: una sola Routine all-clients alcanza (es liviana: solo lee y propone). Si querés, la podés batchear igual que el autopush.

> **Importante:** este skill **PROPONE, no archiva solo** (archivar en AdLabs es irreversible). Corriendo
> desatendido llega hasta la propuesta y la deja en Supabase con `status:"pending"`; **vos confirmás**
> después qué archivar diciendo "archivá la revisión de [Brand]".

Prompt:
```
Para CADA cliente activo en Supabase (proyecto POD 66 "awhiobrcgghyiycxukjm",
tabla public.clients donde active = true), corré el skill weekly-negatives-review para esa marca:
- Descubri las campanas "Loose Match - High Likelihood" por patron de nombre (contiene "loose" Y
  "high likelihood", case-insensitive), una por ASIN.
- Lee los negativos aplicados ahi (entity negative_targeting, NEGATIVE_TARGET_STATE=ENABLED) y
  re-juzga cada uno contra el producto + el relevance_profile.
- Arma la propuesta de candidatos a archivar (los que podrian bloquear trafico relevante) con motivo y
  confianza, y escribila a Supabase (tipo='negatives_review', fecha=hoy ART) con status='pending'.
  NO archives nada (espera el OK manual de Nacho).
Continua ante error; procesa todos los clientes. No pidas confirmacion.
```

Cuando querés cerrar la revisión de un cliente: en un chat normal decís **"archivá la revisión de [Brand]"**
(o "archivá solo los de alta confianza"), el skill archiva esos negativos en AdLabs y los agrega a
`protected_relevant` para que el autopush no los vuelva a negar.

---

## Transición dry-run → apply
Cuando el tab Push te muestre unos días de dry-run y estés conforme:
1. Editá el prompt de cada Routine de autopush: del prompt **DRY-RUN** al prompt **APPLY**.
2. (No hace falta tocar nada más — mismo horario, mismos connectors.)
Desde la próxima corrida aplica de verdad. ASINs y caracteres especiales **nunca** se aplican, en ningún modo.
