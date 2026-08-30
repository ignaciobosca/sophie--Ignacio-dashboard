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
- **ASINs nunca se auto-negativizan** (regla de Nacho): los términos `b0…` (`kind:"asin"`) no se pushean;
  van a `asins_skipped[]` y se muestran en el tab Push para decidir a mano. El autopush crea solo keyword-negatives.
- **Caracteres especiales no se pueden negar** (regla de Nacho): un keyword con char fuera de `[A-Za-z0-9 '&-]`
  (no-ASCII o coma/símbolos) Amazon lo rechaza → no se pushea, va a `dropped[]` con `reason:"special_char"`.
  Aplica al autopush y al push manual (`adlabs-push-negatives`).
- **Revisión semanal = propone, Nacho confirma.** Des-negar reabre gasto, así que no se archiva sin OK.
  El OK alimenta `protected_relevant` (learn) → el sistema deja de re-negar ese término.
- **Loose Match por patrón:** las campañas se descubren por nombre que contiene `loose` **y**
  `high likelihood` (case-insensitive). Hay **una por ASIN/producto** (ej. Urban Veda).

## Verificaciones en vivo (2026-08-30, AdLabs + Supabase conectados)

✅ **Ya verificado:**
1. **Entidad de negativos para leerlos** — es `negative_targeting` (schema `adlabs://schema/filters/negative_targeting`).
   Filtros: `CAMPAIGN_ID`, `NEGATIVE_TARGET_STATE`, `TARGET_TYPE`, `NEGATIVE_KEYWORD_MATCH_TYPE`,
   `NEGATIVE_TARGETING_LEVEL`, `NEGATIVE_TARGET_ID`. Row-level trae `id`, `match_type_raw`, `campaign_id`.
2. **Archivar un negativo** — `update_entities(entity_type="negative_targeting", action="update_status",
   status="ARCHIVED", reference, note)`. **Irreversible** (no se des-archiva; recuperar = re-crear).
3. **Patrón Loose Match** — `CAMPAIGN_NAME LIKE "Loose"` funciona; confirmado en Urban Veda (cuenta
   "Ayurveda Wellness"): 3 campañas, una por ASIN, con el ASIN en el nombre y "Loose … High Likelihood".

⏳ **Falta verificar (en la 1ª corrida del autopush, en `dry-run`):**
- **`CONTAINS_ASINS` + exclusión Scavenger** (autopush Step 5): que la reference de ad_group resuelva bien
  y que `CAMPAIGN_NAME_NOT NOT_LIKE "Scavenger"` corte como se espera.

Correr el autopush en `dry-run` con un cliente antes de agendar las Routines en full-auto.

## Informe diario del autopush → Tab "Push" del Master Dashboard

Además del push automático, el autopush deja un **recibo diario por cliente** en Supabase
(`dashboard_snapshots`, tipo `negatives_push`) con lo que se pusheó (`applied`), lo **retenido** por
`General (sin asignar)` (`held`, con clicks/spend/campaña de origen/línea sugerida) y lo descartado
por la red de seguridad (`dropped`). Eso se muestra como una **5ta tab "Push"** en el Master Dashboard
de siempre, con selector de día y la lista de retenidos accionable para que decidas la línea.

Carpeta `push-report/`:
- `push-tab.js` — la función `renderPush()` + los puntos de inserción del template.
- `PATCH.md` — las 3 piezas de datos (autopush · snapshot · composer) + cómo aplicar el tab al template
  en Supabase, con el código exacto en el apéndice.

**Skills existentes patcheados** (cambios aditivos, documentados en `push-report/PATCH.md`):
- `daily-negatives-supabase` — persiste `origin_campaign`/`origin_ad_group` en cada candidato.
- `master-dashboard-supabase` — lee `negatives_push` y arma `DATA.push` (5ta tab).

**Estado (2026-08-30):** el tab Push YA está aplicado al `template_html` (id='master') en Supabase,
validado con `node --check` + Chromium y verificado por MD5. La próxima corrida del composer lo publica.

## Instalación
Cada carpeta (`daily-negatives-autopush/`, `weekly-negatives-review/`) es un skill con su `SKILL.md`.
Instalar en la librería de skills (mismo mecanismo que los demás skills del pod). Los `.skill`
empaquetados, si se generaron, están junto a este README.
