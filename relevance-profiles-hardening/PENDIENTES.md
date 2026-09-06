# Pendientes — Endurecimiento de perfiles de relevancia

Rama: `claude/relevancia-perfiles-negativizacion-vib2ew` · carpeta: `relevance-profiles-hardening/`

## ✅ Ya hecho (sin acción tuya)
- Migración de perfiles v1 → v2 aplicada y verificada (20 perfiles).
- Fichas de producto cargadas: 20 clientes / 41 líneas.
- Piloto Pavida's cargado y verificado.

## ⏳ Pendientes tuyos

### 1. Instalar los 4 skills (reemplazar 1:1 + re-sincronizar)
| Reemplazar el skill… | …con este archivo |
|---|---|
| `client-onboarding` | `02-client-onboarding.SKILL.md` |
| `daily-negatives-supabase` | `03-daily-negatives-supabase.SKILL.md` |
| `daily-negatives-autopush` | `04-daily-negatives-autopush.SKILL.md` |
| `master-dashboard-supabase` | `06-master-dashboard-supabase.SKILL.md` |

> `negative-targeting` y `daily-negatives` (local) NO se tocan (negative-targeting está suspendido).

### 2. Aplicar el patch del template del dashboard (cola de aprobación LOW)
- Archivo: `05-dashboard.md` (renderer `renderApprovalQueue` + integración con `renderDay`).
- Va en el template del master en Supabase (`dashboards` id='master').
- **Hacerlo DESPUÉS de instalar el autopush V2** (si no, la cola sale vacía).
- Lo puedo aplicar yo en vivo con tu OK (validando el JS antes de publicar).

### 3. Re-jalar 2 fichas que no resolvieron (`no_fiche`)
- Leefy — Immunity/Defense Blend (`B0C6LYYDOY`) → posible ASIN desmergeado + pausado en PPC.
- House of Thalen — GLP-1 (`B0GV4TR6PJ`) → listing nuevo, aún sin indexar.
- Cómo: *"actualizar ficha de [Brand]"* cuando el ASIN resuelva.

### 4. Revisar 3 excepciones marcadas `_needs_scope_review`
Venían como texto suelto en data vieja; la migración les puso un scope por defecto — confirmá:
- Every Cloud → `dark rum` (equals), `el dorado rum` (equals — ojo: es marca de ron competidora).
- Hekaya → `laurel` (contains).

### 5. Guardar el backup en Drive
- Te lo mandé como archivo: `relevance_profiles_v1_backup_2026-09-06.json`.
- Sugerido: Drive › `sophie-society-clients`. (No lo commiteé al repo porque publica en Pages público.)

### 6. (Opcional) Hallazgo de listing — Pavida's
- El título dice "Vitamin C y Kakadu Plum Extract" pero el campo `ingredients` no los lista. Alinear el listing.

## Referencia de archivos en `relevance-profiles-hardening/`
- `README.md` — decisiones + flujo + estado
- `01-relevance-profile-v2.md` — schema (contrato)
- `01-migrate-v1-to-v2.py` — migración (ya corrida)
- `02` … `06` — los skills / specs de arriba
- `PENDIENTES.md` — este archivo
