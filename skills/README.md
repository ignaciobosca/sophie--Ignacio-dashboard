# Negative Targeting — automatización (Sophie Society, Pod Nacho)

Dos skills nuevos que sacan los pasos manuales del proceso de negative targeting. Se instalan en
la librería de skills de Claude (Cowork / Claude Code), junto a los skills existentes
`daily-negatives-supabase`, `adlabs-push-negatives` y `negative-targeting`.

## El pipeline completo

```
                      ┌─────────────────────────────┐
   mediodía ART  ───► │ daily-negatives-supabase     │  identifica search terms irrelevantes de AYER
                      │ (run, ya existía)            │  → snapshot a Supabase (tipo='negatives')
                      └──────────────┬──────────────┘
                                     │  (Routine escalonada +15 min)
                      ┌──────────────▼──────────────┐
   ~13:00 ART    ───► │ daily-negatives-autopush ★   │  lee el snapshot, deriva destino por producto,
                      │ (NUEVO)                      │  pushea negativos a AdLabs SOLO. Recibo a Supabase
                      └──────────────┬──────────────┘  (tipo='negatives_push'). Retiene lo no resoluble.
                                     │
                      ┌──────────────▼──────────────┐
   lunes AM ART  ───► │ weekly-negatives-review ★    │  revisa los negativos de las campañas
                      │ (NUEVO)                      │  "Loose Match - High Likelihood", propone
                      └─────────────────────────────┘  archivar los que bloquean tráfico relevante.
                                                        Con tu OK: archiva + learn. Snapshot review.
```

★ = skills nuevos de este branch.

## Qué automatiza cada uno

| Paso manual de hoy | Antes | Ahora |
|---|---|---|
| Identificar irrelevantes | `daily-negatives-supabase` (ya auto) | igual |
| Seleccionar exact/phrase en el dashboard | manual ✋ | el match ya lo trae el snapshot; el push lo respeta |
| Copiar bloques copy-paste | manual ✋ | eliminado — el autopush lee el snapshot directo |
| Tipear el destino y disparar el push | manual ✋ (`adlabs-push-negatives`) | auto-derivado por producto (`daily-negatives-autopush`) |
| Vigilar que no se corte tráfico bueno | ad hoc / no sistemático | revisión semanal estructurada (`weekly-negatives-review`) |

El **Master Dashboard** deja de ser el portón y pasa a ser superficie de auditoría: seguís viendo
todo (candidatos, pushes, revisiones), pero ya no tenés que seleccionar ni copiar.

## Decisiones de diseño (confirmadas con Nacho, 2026-08-30)

- **Push diario = automático**, sin selección. Alcance: todos los ad groups ENABLED (SP+SB) que
  anuncian el ASIN/línea del candidato, **menos Scavenger**. Nunca a "toda la cuenta".
- **Guardrail duro:** un candidato sin producto resoluble a ASINs concretos (`General (sin asignar)`)
  **NO se pushea** — queda para el dashboard/manual. Un destino vacío jamás significa "todas".
- **Revisión semanal = propone, Nacho confirma.** Des-negar reabre gasto, así que no se archiva sin OK.
  El OK alimenta `protected_relevant` (learn) → el sistema deja de re-negar ese término.
- **Loose Match por patrón:** las campañas se descubren por nombre que contiene `loose` **y**
  `high likelihood` (case-insensitive). Hay **una por ASIN/producto** (ej. Urban Veda).

## ⚠️ Verificaciones en vivo pendientes (hacer en la 1ª corrida real, con AdLabs conectado)

Estos skills se escribieron con AdLabs/Supabase desconectados (piden auth en sesión interactiva).
Antes de agendar las Routines, correr **una vez en modo `dry-run` / con OK manual** y confirmar:

1. **Entidad de negativos en AdLabs para leerlos** (Step 3 del weekly): nombre exacto
   (`negative_keyword` / `negative_target`) y columnas (`match_type`, `ad_group_id`, `state`, texto/expresión, `id`).
   Confirmar con `read_resource(uri="adlabs://instructions")` o el schema.
2. **Mecanismo de archivar un negativo** (Step 5 del weekly): si `update_entities` acepta
   `state=ARCHIVED` para negativos, o si hay que usar pause / la UI. Dejar registrado cuál se usa.
3. **`CONTAINS_ASINS` + exclusión Scavenger** (Step 5 del autopush): confirmar que la reference de
   ad_group resuelve como se espera y que el filtro `CAMPAIGN_NAME_NOT NOT_LIKE "Scavenger"` corta bien.
4. **Filtro `CAMPAIGN_NAME LIKE "Loose"`** (Step 2 del weekly): confirmar que trae las campañas y
   validar el AND de las dos palabras en el modelo (AdLabs matchea substring simple).

Correr primero con un cliente de prueba (ej. Natchiketa o Masofta) en `dry-run` antes de full-auto.

## Instalación
Cada carpeta (`daily-negatives-autopush/`, `weekly-negatives-review/`) es un skill con su `SKILL.md`.
Instalar en la librería de skills (mismo mecanismo que los demás skills del pod). Los `.skill`
empaquetados, si se generaron, están junto a este README.
