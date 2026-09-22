# Spec multi-tenant — skills para varias agencias

Doc de referencia para la Fase 3 de la migración. Objetivo: que **una sola base
de skills** sirva a varias agencias/clientes sin forkear, y sin nada de "Sophie"
hardcodeado. Apoyado en el schema real (`../supabase/schema.sql`) y las notas de
de-Sophie-fication (`../MIGRATION-NOTES.md`).

---

## 1. Principios

1. **Una skill, N agencias.** Nada específico de una agencia vive en la skill.
   Todo lo variable (config, branding, conectores, destinos) se resuelve en runtime.
2. **La identidad de un cliente es `(agency_id, brand)`**, no `brand` solo. Dos
   agencias pueden tener un brand con el mismo nombre.
3. **Secrets fuera del código.** Tokens (service_role, SHURQ, Slack, etc.) viven
   como secrets del entorno, nunca en las skills ni en git.
4. **Hardcode → config.** Canales de Slack, repo de GitHub Pages, nombre de pod,
   idioma de reporte: todo sale de la DB, no del texto de la skill.

---

## 2. Modelo de datos

### Estado actual (Sophie)
- `clients` (PK `brand`) — config jsonb por cliente.
- `dashboard_snapshots` (`cliente` = brand) — feeders upsert por `(cliente,tipo,fecha)`.
- `relevance_profiles` (PK `brand`).
- `organic_rank_snapshots` (`brand`).
- `dashboards` (id='master') — template del composer.

### Estado target (multi-tenant)
Agrega la dimensión agencia. Dos opciones para las tablas de snapshots:

| Opción | Cómo | Pro | Contra |
|---|---|---|---|
| **A — columna `agency_id`** (recomendada) | Agregar `agency_id` a `clients`, `dashboard_snapshots`, `relevance_profiles`, `organic_rank_snapshots`; unique compuesto | Limpio, queryable, FKs reales | Toca los feeders (agregar la columna al upsert) |
| B — `cliente` namespaced | `cliente = 'agency:brand'` como string | Cambio mínimo en el schema | Frágil, no hay FK, parsing por string |

➡️ **Recomiendo A.** El add-on SQL base está en `../supabase/multi-tenant.sql`
(crea `agencies` + `brand_kits` y agrega `agency_id` a `clients`). Para completar A,
extender también snapshots:

```sql
alter table public.dashboard_snapshots    add column if not exists agency_id text;
alter table public.relevance_profiles     add column if not exists agency_id text;
alter table public.organic_rank_snapshots add column if not exists agency_id text;

-- Reemplazar los unique por versiones que incluyan agency_id:
alter table public.dashboard_snapshots drop constraint dashboard_snapshots_uq;
alter table public.dashboard_snapshots
  add constraint dashboard_snapshots_uq unique (agency_id, cliente, tipo, fecha);
-- (idem para relevance_profiles PK y uq_ors_row)
```

### Tablas nuevas (de `multi-tenant.sql`)
- **`agencies`** — 1 fila por agencia. `connectors` jsonb con IDs/refs no sensibles
  (workspace de Slack, team de ClickUp, carpeta Drive raíz, etc.).
- **`brand_kits`** — branding por agencia (`(agency_id, name)`). Reemplaza el branding
  Sophie hardcodeado. Estructura sugerida del `kit` jsonb:
  ```json
  {
    "palette": { "primary": "#…", "accent": "#…", "bg": "#…", "text": "#…" },
    "fonts":   { "heading": "…", "body": "…" },
    "logo_url": "https://…",
    "voice":   "casual-profesional, asertivo",
    "footer":  "© … / disclaimer",
    "report_language_default": "es"
  }
  ```

---

## 3. Resolución de config (el contrato que toda skill sigue)

Al arrancar, cada skill resuelve en este orden:

```
input: agency_id (o se infiere del contexto/канал), brand
1. cfg      = clients.config       where (agency_id, brand)
2. agency   = agencies.connectors  where agency_id
3. kit      = brand_kits.kit       where (agency_id, cfg.brand_kit ?? 'default')
4. secrets  = del entorno (service_role, tokens SHURQ/Slack/…) por agency_id
5. destinos = cfg.slack_internal_channel_id, cfg.dashboard_url, etc.
```

Con eso la skill tiene: qué cliente, con qué cuenta SHURQ (`cfg.shurq_account_id`),
a qué Slack postea (`cfg.slack_internal_channel_id`), con qué branding (`kit`) y con
qué credenciales (`secrets[agency_id]`).

> Las keys de `clients.config` ya existen y sirven casi todas tal cual: `shurq_account_id`,
> `amazon_marketplace`, `slack_internal_channel_id`, `acos_target`, `tacos_target`,
> `managed_asins`, `competitor_asins`, `report_language`, `dashboard_url`… (lista completa
> en `../supabase/DATA-DICTIONARY.md`). Solo falta **agregar `agency_id`** por fila y,
> opcionalmente, `brand_kit` (nombre del kit a usar).

---

## 4. Credenciales / secrets

| Secret | Scope | Dónde |
|---|---|---|
| Supabase `service_role` | por proyecto | secret del entorno |
| SHURQ token | por agencia (o global si es tu cuenta) | secret, mapeado por `agency_id` |
| Slack token | por workspace/agencia | secret |
| ClickUp token | por workspace/agencia | secret |
| Drive/otros | por agencia | secret |

Regla: la skill nunca ve un token en su texto; lo pide al entorno por `agency_id`.

---

## 5. De hardcode a config (checklist de refactor)

Lo que hoy está fijo (ver `MIGRATION-NOTES.md`) pasa a la DB:

| Hoy hardcodeado | Pasa a |
|---|---|
| `#pod-66-team`, `#harvest-and-negations`, `#client-drafts-nacho`, … | `agencies.connectors.channels.*` o `clients.config.slack_*` |
| "POD 66" / "pod-66" | `agencies.name` |
| Link `ignaciobosca.github.io/sophie--Ignacio-dashboard/` | `agencies.connectors.pages_url` o `clients.config.dashboard_url` |
| Branding Sophie (colores, footer, voz) | `brand_kits.kit` |
| Tablas Supabase | igual (schema replicado) + `agency_id` |

---

## 6. Orden de refactor sugerido

1. **DB:** aplicar `schema.sql` → `multi-tenant.sql` → extender snapshots (§2).
2. **Resolver de config:** implementar el contrato §3 como helper único que todas
   las skills importan (evita repetir la lógica en cada una).
3. **Feeders primero** (`daily-*-supabase`, `biweekly-bid-optimizer`): agregar `agency_id`
   al upsert. Son los más simples y desbloquean el dashboard.
4. **Composer** (`master-dashboard-supabase`): leer por `agency_id`, publicar a
   `agencies.connectors.pages_url`, notificar al canal de config.
5. **PPC ops SHURQ** (weekly-report, negativos, harvest): reapuntar destinos Slack y cuenta SHURQ vía config.
6. **Skills 🏷️** (listing, reporting, creativos): inyectar `brand_kit` en el output.
7. **Skills 🔧** (cutover Sophie Hub): recién acá, en paralelo, cambiar la fuente de datos.

---

## 7. Convenciones

- `agency_id`: slug corto, estable, minúsculas (`acme`, `nacho-direct`).
- `brand`: como lo nombra la agencia; único **dentro** de la agencia.
- `tipo` en snapshots: mantener los 7 valores actuales (`daily_check`, `harvest`,
  `negatives`, `negatives_push`, `negatives_review`, `optimizations`, `restock`).
- Un `brand_kit` `default` por agencia; overrides por cliente vía `clients.config.brand_kit`.

---

## 8. Decisiones abiertas (para vos)

1. **¿SHURQ es tu cuenta única o una por agencia?** Define si el token SHURQ es global
   o mapeado por `agency_id`.
2. **¿Un Supabase para todas las agencias, o uno por agencia?** Recomiendo **uno solo
   multi-tenant** (más simple de operar); uno por agencia solo si un cliente exige
   aislamiento de datos por contrato.
3. **¿Dashboards: un repo Pages por agencia o uno con subcarpetas?** Subcarpetas
   (`/acme/`, `/otra/`) es más simple; repos separados si querés permisos distintos.
4. **Idioma de reporte:** ya existe `report_language` en config — default por `brand_kit`.
