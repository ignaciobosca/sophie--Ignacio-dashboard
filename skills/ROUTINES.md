# Routines a crear (las armás vos, manual) — Negative Targeting automático

Estas Routines las creás **vos** en tu panel de Routines para que corran bajo tu autorización (sin
aprobaciones manuales). Copiá los prompts tal cual. Todo corre en el entorno **"Daily Check"**
(`env_01PLsdw2426SeBeqP2FQqZNS`, full network), en **sesión nueva por corrida**, sin repo adjunto.

## Dónde encaja en tu día (horarios en ART y UTC)

| Hora ART | Hora UTC | Routine | Estado |
|---|---|---|---|
| 06:00–06:30 | 09:00–09:30 | **Daily Negatives** (identificador, 4 batches) — ya existe | escribe snapshot `negatives` |
| **07:30** | **10:30** | **Autopush** ← NUEVA | lee snapshot, pushea keywords, recibo `negatives_push` |
| 08:30 | 11:30 | **Master Dashboard Composer** — ya existe | publica el dashboard (con el tab Push) |
| Viernes 08:00 | Viernes 11:00 | **Weekly Negatives Review** ← NUEVA | propone archivar (no archiva solo) |

El autopush va **después** del identificador y **antes** del composer, así el push del día ya se ve
en el dashboard de esa mañana.

---

## 1) Routine: Autopush diario

- **Cron (UTC):** `30 10 * * *`  (07:30 ART)
- **Entorno:** Daily Check · **sesión nueva por corrida** · **sin repo**
- **Connectors:** **Supabase + Adlabs**
- **Notificaciones:** push/email a gusto (te avisa cuando termina)

### Opción A — Arrancar en DRY-RUN (recomendado para estrenar)
Escribe el recibo (el tab Push muestra lo que HARÍA) pero **no aplica nada** a Amazon. Lo dejás unos
días, revisás el tab, y cuando estés conforme cambiás el prompt a la Opción B.

Prompt:
```
Para CADA cliente activo en Supabase (proyecto POD 66 "awhiobrcgghyiycxukjm",
tabla public.clients donde active = true), corré el skill daily-negatives-autopush
en modo DRY-RUN para esa marca:
- Leé el snapshot de negatives de HOY (tipo='negatives', fecha = hoy en horario ART). Si no hay, saltealo.
- Clasificá: los ASINs (kind='asin') van a asins_skipped (NO se pushean); los keywords con caracteres
  especiales (fuera de [A-Za-z0-9 '&-]) van a dropped(special_char); 'General (sin asignar)' va a held;
  el resto se agrupa por línea de producto.
- Derivá el destino por línea con ad_group CONTAINS_ASINS (SP+SB, CAMPAIGN_STATE=ENABLED,
  AD_GROUP_STATE=ENABLED, DATE últimos 14 días, EXCLUYENDO campañas con "Scavenger" en el nombre).
- NO apliques a Amazon (dry-run): creá los previews para obtener el conteo, pero no llames al apply.
- Escribí el recibo a Supabase (dashboard_snapshots, tipo='negatives_push', fecha=hoy ART) con
  summary.mode='dry-run' y applied[] = lo que HABRÍA creado, más held/asins_skipped/dropped completos.
Continuá ante error (procesá todos los clientes). No pidas confirmación.
```

### Opción B — Apply real (cuando ya lo validaste)
Igual que A pero **aplica** los keyword-negatives. Cambiá el prompt a:
```
Para CADA cliente activo en Supabase (proyecto POD 66 "awhiobrcgghyiycxukjm",
tabla public.clients donde active = true), corré el skill daily-negatives-autopush
(modo run / apply) para esa marca: leé el snapshot de negatives de HOY, pusheá los
keyword-negatives a AdLabs con el destino auto-derivado por línea (CONTAINS_ASINS SP+SB,
ENABLED, últimos 14 días, EXCLUYENDO Scavenger), salteando ASINs (kind='asin') y términos con
caracteres especiales, y escribí el recibo negatives_push a Supabase. Anclá "hoy" a horario ART.
Continuá ante error; procesá todos los clientes. No pidas confirmación.
```

> **Batching (opcional, como tu Daily Negatives):** si preferís no correr los ~20 clientes en una sola
> sesión, hacé 4 Routines espejando tus batches de 5 clientes, con el mismo prompt pero nombrando los 5
> clientes de cada batch, y crons escalonados `30 10`, `35 10`, `40 10`, `45 10 * * *` (07:30–07:45 ART).
> Una sola Routine all-clients también funciona; si tarda, los recibos igual quedan en Supabase y el
> dashboard los toma en el próximo compose.

---

## 2) Routine: Weekly Negatives Review (viernes)

- **Cron (UTC):** `0 11 * * 5`  (viernes 08:00 ART)
- **Entorno:** Daily Check · **sesión nueva por corrida** · **sin repo**
- **Connectors:** **Supabase + Adlabs**

> **Importante:** este skill **PROPONE, no archiva solo** (archivar en AdLabs es irreversible). Corriendo
> desatendido llega hasta la propuesta y la deja en Supabase con `status:"pending"`; **vos confirmás**
> después qué archivar diciendo "archivá la revisión de [Brand]".

Prompt:
```
Para CADA cliente activo en Supabase (proyecto POD 66 "awhiobrcgghyiycxukjm",
tabla public.clients donde active = true), corré el skill weekly-negatives-review para esa marca:
- Descubrí las campañas "Loose Match - High Likelihood" por patrón de nombre (contiene "loose" Y
  "high likelihood", case-insensitive), una por ASIN.
- Leé los negativos aplicados ahí (entity negative_targeting, NEGATIVE_TARGET_STATE=ENABLED) y
  re-juzgá cada uno contra el producto + el relevance_profile.
- Armá la propuesta de candidatos a archivar (los que podrían bloquear tráfico relevante) con motivo y
  confianza, y escribila a Supabase (dashboard_snapshots, tipo='negatives_review', fecha=hoy ART) con
  status='pending'. NO archives nada (esperá el OK manual de Nacho).
Continuá ante error; procesá todos los clientes. No pidas confirmación.
```

Cuando querés cerrar la revisión de un cliente: en un chat normal decís **"archivá la revisión de [Brand]"**
(o "archivá solo los de alta confianza"), el skill archiva esos negativos en AdLabs y los agrega a
`protected_relevant` para que el autopush no los vuelva a negar.

---

## Transición dry-run → apply
Cuando el tab Push te muestre unos días de dry-run y estés conforme:
1. Editá el prompt de la Routine de autopush: de la **Opción A** a la **Opción B**.
2. (No hace falta tocar nada más — mismo horario, mismos connectors.)
Desde la próxima corrida aplica de verdad. ASINs y caracteres especiales **nunca** se aplican, en ningún modo.
