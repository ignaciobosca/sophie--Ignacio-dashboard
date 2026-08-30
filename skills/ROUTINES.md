# Routines a crear (las armás vos, manual) — Negative Targeting automático

Estas Routines las creás **vos** en tu panel de Routines para que corran bajo tu autorización (sin
aprobaciones manuales). Copiá los prompts tal cual. Todo corre en el entorno **"Daily Check"**
(`env_01PLsdw2426SeBeqP2FQqZNS`, full network), en **sesión nueva por corrida**, sin repo adjunto,
connectors **Supabase + Adlabs**.

## Dónde encaja en tu día (horarios en ART y UTC)

| Hora ART | Hora UTC | Routine | Estado |
|---|---|---|---|
| 06:00–06:30 | 09:00–09:30 | **Daily Negatives** (identificador, 4 batches) — ya existe | escribe snapshot `negatives` |
| **07:30–07:45** | **10:30–10:45** | **Autopush** (4 batches) ← NUEVA | lee snapshot, pushea keywords, recibo `negatives_push` |
| 08:30 | 11:30 | **Master Dashboard Composer** — ya existe | publica el dashboard (con el tab Push) |
| Viernes 08:00 | Viernes 11:00 | **Weekly Negatives Review** ← NUEVA | propone archivar (no archiva solo) |

El autopush va **después** del identificador y **antes** del composer, así el push del día ya se ve
en el dashboard de esa mañana.

---

## 1) Autopush diario — 4 batches (RECOMENDADO)

**Layout recomendado:** 4 Routines de 5 clientes cada una, escalonadas (igual que tu "Daily Negatives").

**Por qué batches y no una sola:**
- **Resiliencia:** si un batch falla (AdLabs tira error, una reference expira), los otros 3 siguen.
- **Entra en la ventana:** ~1h entre el identificador (termina ~06:50 ART) y el composer (08:30 ART); 4 batches escalonados terminan holgados; una corrida única de 20 podría pasarse.
- **Reparte la carga de AdLabs** y mantiene cada sesión corta.
- **Idempotente:** el recibo del día evita duplicados, así que re-correr un batch es seguro.

**Config (las 4):**
- **Crons (UTC):** `30 10 * * *` · `35 10 * * *` · `40 10 * * *` · `45 10 * * *`  (07:30–07:45 ART)
- **Entorno:** Daily Check · **sesión nueva por corrida** · **sin repo**
- **Connectors:** **Supabase + Adlabs**
- **Notificaciones:** push/email a gusto.
- Partí los ~20 clientes en 4 grupos de 5 — podés reusar los grupos de tu "Daily Negatives" o armarlos como quieras (a las 07:30 ya están **todos** los snapshots escritos, así que el grupo no tiene que coincidir con el del identificador).

### Prompt por batch — DRY-RUN (recomendado para estrenar)
Escribe el recibo (el tab Push muestra lo que HARÍA) pero **no aplica nada** a Amazon. Reemplazá
`<CLIENTE 1..5>` por los 5 nombres de marca del batch, tal como figuran en Supabase (ej. `Masofta Inc`):
```
Corré el skill daily-negatives-autopush en modo DRY-RUN para estas 5 marcas:
<CLIENTE 1>, <CLIENTE 2>, <CLIENTE 3>, <CLIENTE 4>, <CLIENTE 5>.
Para cada una:
- Leé el snapshot de negatives de HOY (tipo='negatives', fecha = hoy ART). Si no hay, saltala.
- Clasificá: ASINs (kind='asin') -> asins_skipped (NO se pushean); keywords con caracteres especiales
  (fuera de [A-Za-z0-9 '&-]) -> dropped(special_char); 'General (sin asignar)' -> held; el resto por linea.
- Derivá el destino por linea con ad_group CONTAINS_ASINS (SP+SB, CAMPAIGN_STATE=ENABLED,
  AD_GROUP_STATE=ENABLED, DATE ultimos 14 dias, EXCLUYENDO campanas con "Scavenger" en el nombre).
- NO apliques a Amazon: crea los previews para el conteo, pero no llames al apply.
- Escribi el recibo a Supabase (tipo='negatives_push', fecha=hoy ART) con summary.mode='dry-run' y
  applied[] = lo que HABRIA creado, mas held/asins_skipped/dropped.
Continua ante error. No pidas confirmacion. Proyecto Supabase POD 66 "awhiobrcgghyiycxukjm".
```

### Prompt por batch — APPLY (cuando ya lo validaste)
Igual pero **aplica** los keyword-negatives:
```
Corré el skill daily-negatives-autopush (modo run / apply) para estas 5 marcas:
<CLIENTE 1>, <CLIENTE 2>, <CLIENTE 3>, <CLIENTE 4>, <CLIENTE 5>.
Para cada una: lee el snapshot de negatives de HOY, pushea los keyword-negatives a AdLabs con el
destino auto-derivado por linea (CONTAINS_ASINS SP+SB, ENABLED, ultimos 14 dias, EXCLUYENDO Scavenger),
salteando ASINs (kind='asin') y terminos con caracteres especiales, y escribi el recibo negatives_push.
Ancla "hoy" a ART. Continua ante error. No pidas confirmacion. Proyecto Supabase POD 66 "awhiobrcgghyiycxukjm".
```

### Alternativa — una sola Routine all-clients (mínimo mantenimiento)
Si preferís no mantener 4: 1 Routine, cron `30 10 * * *`, el mismo prompt pero **"para CADA cliente
activo en Supabase (public.clients donde active = true)"** en vez de las 5 marcas. Más simple, pero corre
los ~20 en una sola sesión larga (puede pasarse de la ventana del composer; el push igual queda en
Supabase y lo toma el compose siguiente). Es segura por la idempotencia, solo menos resiliente/puntual.

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
