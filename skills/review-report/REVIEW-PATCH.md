# Weekly Negatives Review -> Tab "Review" del Master Dashboard

Nacho pidió que las propuestas del **Weekly Negatives Review** (negativos candidatos a archivar por
posiblemente bloquear tráfico relevante) se vieran en el Master Dashboard. El Weekly Review ya escribía a
Supabase (`dashboard_snapshots` tipo=`negatives_review`, schema `negatives-review-v1`) pero el composer
**no lo leía** -> no había superficie que lo mostrara (por eso "no entregó nada para revisar"). Se agrega
como **6to tab ("Review")** entre Push y Harvest.

## Piezas coordinadas (1 de datos ya existía + 2 nuevos)

| # | Pieza | Archivo | Estado |
|---|---|---|---|
| 1 | El weekly review deja un snapshot rico por corrida | `weekly-negatives-review` (schema `negatives-review-v1`) | ✅ ya existía |
| 2 | El composer arma `DATA.review` desde `negatives_review` | `master-dashboard-supabase` V2.2 (Step 1a query + Step 2 compose + guard 6 keys) | ✅ hecho |
| 3 | El template renderiza el tab | `dashboards.template_html` (id='master') en Supabase | ✅ APLICADO (2026-09-04) |

## Flujo de datos

```
weekly-negatives-review (viernes)
   └─► escribe fila  dashboard_snapshots  tipo='negatives_review'  fecha=viernes
        datos = { proposal[], proposed_count, reviewed_count, archived_count,
                  excluded_root_conflicts_kept[], note }   (schema negatives-review-v1)
                                   │
master-dashboard-supabase (cierre diario)
   └─► lee las filas negatives_review de los últimos 7 días  →  DATA.review.clients[].days[]
        └─► inyecta en index.html  →  git push a main  →  GitHub Pages
                                   │
Template (renderReview)  →  Tab "Review":  Candidatos a archivar + Mantenidos negados
```

## Cambio 3 — template en Supabase (5 inserciones + renderReview)

El template es el HTML de `dashboards.template_html` (id='master'), token `@@DATA@@`. Se insertan **5 cositas**
(el código completo del render está en `review-tab.js`, junto a este archivo):

1. **DOM** — después de `<div class="page" id="page-push"></div>`:
   ```html
   <div class="page" id="page-review"></div>
   ```
2. **`TABS[]`** — entrada del tab **después** de `push` (queda Daily · Negatives · Push · Review · Harvest ·
   Restock). El badge cuenta los **propuestos a archivar** del snapshot más nuevo por cliente:
   ```js
   {id:'review',label:'Review',badgeFn:()=>{let n=0;((DATA.review&&DATA.review.clients)||[]).forEach(c=>{const d=(c.days||[])[0];n+=d?(d.proposed!=null?d.proposed:((d.proposal||[]).length)):0;});return n;}},
   ```
3. **`allClients()`** — sumar `'review'`:
   ```js
   ['negatives','push','review','harvest','restock'].forEach(k=>(((DATA[k]&&DATA[k].clients)||[]).forEach(c=>names.add(c.brand_name))));
   ```
4. **`clientSel.onchange`** — agregar `renderReview()`:
   ```js
   sel.onchange=()=>{CURRENT=sel.value;renderNegatives();renderPush();renderReview();renderHarvest();renderRestock();highlightDaily();};
   ```
5. **boot** — agregar `renderReview()`:
   ```js
   buildTabs(); buildClientSelector(); renderDaily(); renderNegatives(); renderPush(); renderReview(); renderHarvest(); renderRestock(); highlightDaily();
   ```

Y pegar la función **`renderReview()`** completa (de `review-tab.js`) junto a las otras `render*`.

> **Aplicado 2026-09-04:** las 5 inserciones + `renderReview()` se aplicaron a `dashboards.template_html`
> (id='master') vía SQL `replace()` con dollar-quoting. Backup del template previo en la fila
> `id='master__bak_20260904_review'`. Validado: `node --check` OK sobre el script compuesto (1.2MB),
> compose de los 6 tabs OK (regression guard 7 keys), y render headless en Chromium confirmó el tab Review
> poblado (Ayurveda Wellness: 22 candidatos con chips de confianza). @@DATA@@ intacto (1 sola vez).

## Qué muestra el tab (por cliente, selector de revisión)

- **KPIs:** Revisados · A archivar · Archivados.
- **Candidatos a archivar** (`proposal[]`, ordenados por confianza alta→baja): **checkbox** · Término · Match ·
  Confianza (alta/media/baja) · Producto/línea · Motivo. Toolbar: **Todos / Solo alta confianza / Ninguno** +
  **Generar bloque (N)**.
- **Selector + bloque copy-paste:** Nacho tilda los candidatos que quiere y aprieta **Generar bloque** → un
  `textarea` (con botón **Copiar**) con un **comando listo para pegar en un chat**. El comando trae la marca +
  la sublista `- "término" (MATCH)` y pide (1) **archivar** en AdLabs (`negative_targeting` → `update_status
  ARCHIVED`, solo esos) y (2) **proteger** en `protected_relevant` como **IGUALDAD EXACTA**. Pegándolo en un
  chat (Supabase + Adlabs), `weekly-negatives-review` lo ejecuta. IRREVERSIBLE. (También sigue valiendo el
  atajo "archivá la revisión de [Brand]" / "solo los de alta confianza".)
- **Mantenidos negados pese a tocar un término relevante** (`excluded_root_conflicts_kept[]`): informativo —
  términos que contienen un root protegido pero se mantienen negados por mismatch de producto/intent.

> **Seguro por diseño:** si el template no tuviera el tab, `DATA.review` no se usa y el dashboard sigue igual.
> El composer arma `DATA.review` siempre (V2.2+).

## Reaplicar el tab tras un cambio de template

Decime **"aplicá el tab Review al template del master dashboard"** y repito las 5 inserciones + `renderReview()`
de `review-tab.js`, validando con `node --check` antes de escribir a Supabase.
