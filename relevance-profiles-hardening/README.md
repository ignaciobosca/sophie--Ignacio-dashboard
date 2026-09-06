# Endurecimiento de los perfiles de relevancia (negativización)

Objetivo: **máxima confianza** al seleccionar términos a negativizar, con foco en el **autopush**
(lo que se empuja solo a Amazon tiene que ser a prueba de balas).

Este proyecto endurece el perfil de relevancia en **tres frentes que se refuerzan**:

1. **Nutrición desde el día 1** — el perfil deja de armarse a partir de un label de ASIN y pasa a
   contener la **ficha real del producto** (title/bullets/description + atributos), auto-jalada en el onboarding.
2. **Confianza + evidencia** — cada decisión de "Irrelevante" lleva `confidence` (high/medium/low) +
   `evidence` + `basis`, con una rúbrica clara.
3. **Gate + carril del LOW** — `high`/`medium` se autopushean; `low` va al dashboard para tu review,
   y aprobarlo = pushear hoy + aprender (un comando).

---

## Decisiones acordadas (con Nacho)

| Tema | Decisión |
|---|---|
| Frentes | Confianza+evidencia **y** motor de juicio |
| Foco | Autopush |
| Gate | **`high` + `medium` se autopushean; `low` va a review** |
| Motor (fuente) | Vive en **`daily-negatives-supabase`** (la cadena que corre). `negative-targeting` está suspendido → **no se toca**. |
| Carril del LOW | **MODE=approved** en el autopush: aprobar un LOW = **pushear hoy + aprender** (queda en el perfil), en un comando. Dashboard con **checkboxes** + botón "copiar aprobados". |
| Nutrición | Onboarding **auto-jala** listing (title/bullets/description + atributos estructurados si están), **sin revisión**, con robustez (source/fetched_on, `no_fiche` si falla, `attributes_absent` conservador). |
| Dónde vive la ficha | **En el perfil de relevancia** (schema v2), no en el config. |
| Profundidad por ASIN | Title + bullets + description **+ atributos estructurados si están**. |
| Refresh de ficha | **Manual bajo demanda** — comando *"actualizar ficha de [producto] de [Brand]"* en `client-onboarding`. Sin auto-refresh (el semanal murió). |
| Entrega | SKILL.md **completos**, reescritos, para reemplazar 1:1 y re-sincronizar. Todo commiteado acá como referencia. |

---

## Flujo endurecido (de punta a punta)

```
ONBOARDING                     DAILY (corre)                         REVIEW / APROBACIÓN
──────────                     ─────────────                         ───────────────────
auto-jala listing por ASIN     motor de juicio (Step 4)              dashboard tab Negatives
  → ficha v2 en el perfil        usa la ficha v2 como vara            ├─ high/medium: ya pusheados (recibo)
  (attributes_present/absent)     cada Irrelevante:                    └─ LOW: checkboxes + "copiar aprobados"
                                   confidence + evidence + basis              │
       ▲                              │                                       ▼
       │ refresh manual               ▼                              "pushear low aprobados de [Brand]"
       │ "actualizar ficha de X"   GATE (autopush)                            │
       └───────────────────        high+medium → push solo                    ▼
                                   low → held_low_confidence          MODE=approved:
                                                                      saltea gate → push (mismo motor:
                                                                      redes de seguridad + ruteo por línea
                                                                      + apply + recibo) + LEARN (queda en perfil)
```

La ficha v2 es la **vara**: qué ES / qué TIENE / qué NO TIENE el producto. Cuanto mejor la vara,
menos falsos positivos (negar algo relevante) y menos falsos negativos (dejar pasar gasto). El
`learn` sigue sumando `roots`/`competitors` confirmados (basis=profile → high automático), así el
sistema **gana confianza con el uso**.

---

## Entregables

| # | Archivo | Estado |
|---|---|---|
| 1 | `01-relevance-profile-v2.md` — schema v2 (contrato) | ✅ listo |
| 1 | `01-migrate-v1-to-v2.py` — migración v1→v2 (idempotente, con smoke test) | ✅ listo |
| 2 | `02-client-onboarding.SKILL.md` — auto-jala ficha + refresh manual (Step 4.6 + MODE refresh_fiche) | ✅ listo |
| 3 | `03-daily-negatives-supabase.SKILL.md` — motor confidence/evidence + ficha v2 + learn v2 | ✅ listo |
| 4 | `04-daily-negatives-autopush.SKILL.md` — gate high+medium + MODE=approved | ✅ listo |
| 5 | `05-dashboard.md` — cola de aprobación LOW: checkboxes + "copiar aprobados" | ✅ listo |

## Orden de instalación (recomendado)

1. **Migrar los perfiles** (#1): correr `01-migrate-v1-to-v2.py` en DRY-RUN → validar 1–2 perfiles reales
   conmigo → APPLY. (El motor lee v1 y v2, así que esto no es bloqueante, pero conviene primero.)
2. **Reemplazar los 3 SKILL.md** (#2, #3, #4) por sus versiones nuevas y re-sincronizar. Son 1:1.
3. **Cargar la ficha**: correr `client-onboarding` (o *"actualizar ficha de [producto] de [Brand]"*) para
   un cliente piloto → verificar que `product_fiche` quedó en `relevance_profiles`.
4. **Dashboard** (#5): aplicar el cambio del composer + el renderer en el template del master.
5. **Probar el ciclo**: correr el daily → ver confidence en el snapshot → autopush (high/medium push, low
   retenido) → aprobar un LOW desde el dashboard → MODE=approved (push + aprende) → confirmar que el término
   quedó en el perfil como `basis=profile`/`high`.

**Sugerencia:** estrenar el autopush V2 en `dry-run` sobre 1 cliente antes de dejar la Routine en apply.
