# Informe diario del autopush → Tab "Push" del Master Dashboard

Nacho pidió un informe diario de lo que el autopush **pusheó** y lo que **retuvo** por estar en
`General (sin asignar)`, para decidir qué hacer con esos términos. Se entrega como una **5ta tab
("Push") en el Master Dashboard** (mismo dashboard de siempre: `ignaciobosca.github.io/sophie--Ignacio-dashboard/`).

## Piezas coordinadas (3 cambios de datos + 1 de template)

| # | Pieza | Archivo | Estado |
|---|---|---|---|
| 1 | El autopush deja un recibo rico por día | `daily-negatives-autopush` (Step 7, schema `negatives-push-v1`) | ✅ hecho |
| 2 | El snapshot persiste la campaña/ad-group de origen | `daily-negatives-supabase` (Step 5, candidato + `origin_campaign`/`origin_ad_group`) | ✅ hecho |
| 3 | El composer arma `DATA.push` desde `negatives_push` | `master-dashboard-supabase` (Step 1a query + Step 2 compose) | ✅ hecho |
| 4 | El template renderiza el tab | `dashboards.template_html` (id='master') en Supabase | ⏳ aplicar (abajo) |

Los cambios 1–3 ya están en los `SKILL.md`. El cambio 4 (template) hay que aplicarlo **una vez** al
`template_html` en Supabase — no se puede hacer sin el conector Supabase conectado.

## Flujo de datos

```
daily-negatives-autopush (diario)
   └─► escribe fila  dashboard_snapshots  tipo='negatives_push'  fecha=hoy
        datos = { summary, applied[], held[], dropped[] }   (schema negatives-push-v1)
                                   │
master-dashboard-supabase (cierre diario)
   └─► lee las filas negatives_push de los últimos 7 días  →  DATA.push.clients[].days[]
        └─► inyecta en index.html  →  git push a main  →  GitHub Pages
                                   │
Template (renderPush)  →  Tab "Push":  Pusheado + Retenidos (accionable) + Descartados
```

## Cómo aplicar el cambio 4 (template en Supabase)

El template es el HTML de `dashboards.template_html` (id='master'), con el token `@@DATA@@`. Hay que
insertar **5 cositas** (el código completo del render está en `push-tab.js`, junto a este archivo):

1. **DOM** — al lado de los otros `page-*`, agregar el contenedor de la página:
   ```html
   <div class="page" id="page-push"></div>
   ```
   (recomendado justo después de `<div class="page" id="page-negatives"></div>`)

2. **`TABS[]`** — insertar la entrada del tab **después** de `negatives` (así queda Daily · Negatives ·
   Push · Harvest · Restock). El badge cuenta los **retenidos** del día más nuevo por cliente (lo que
   necesita tu decisión):
   ```js
   {id:'push',label:'Push',badgeFn:()=>{let n=0;((DATA.push&&DATA.push.clients)||[]).forEach(c=>{const d=(c.days||[])[0];n+=d?((d.held||[]).length):0;});return n;}},
   ```

3. **`allClients()`** — sumar `'push'` a la lista de fuentes de nombres:
   ```js
   ['negatives','push','harvest','restock'].forEach(k=>(((DATA[k]&&DATA[k].clients)||[]).forEach(c=>names.add(c.brand_name))));
   ```

4. **`clientSel.onchange`** — agregar la llamada a `renderPush()` cuando cambia el cliente:
   ```js
   sel.onchange=()=>{CURRENT=sel.value;renderNegatives();renderPush();renderHarvest();renderRestock();highlightDaily();};
   ```

5. **boot** (última línea del `<script>`) — agregar `renderPush()`:
   ```js
   buildTabs(); buildClientSelector(); renderDaily(); renderNegatives(); renderPush(); renderHarvest(); renderRestock(); highlightDaily();
   ```

Y pegar la función **`renderPush()`** completa (de `push-tab.js`) junto a las otras `render*` del template.

> **Seguro por diseño:** si el template todavía NO tiene el tab, `DATA.push` simplemente no se usa y el
> dashboard sigue funcionando igual (4 tabs). No rompe nada. El composer ya escribe `DATA.push` siempre.

## Aplicarlo con Claude (cuando Supabase esté conectado)

Decime: **"aplicá el tab Push al template del master dashboard"**. Voy a:
1. `select template_html from public.dashboards where id='master'`.
2. Insertar las 5 piezas + `renderPush()` (de `push-tab.js`).
3. Validar con `node --check` el `<script>` resultante (obligatorio — un error deja el dashboard en negro).
4. `update dashboards set template_html = ... where id='master'`.
5. Correr el composer una vez para publicar y verificar que el tab aparece.

## Qué muestra el tab (por cliente, con selector de día, 7 días de historial)

- **KPIs:** Creados · Retenidos · Spend retenido.
- **Pusheado a AdLabs** (`applied[]`): término · clicks · spend · negado como · producto/línea · ad groups · creados · ya estaban.
- **Retenidos — decidir producto** (`held[]`, ordenados por spend desc): término · clicks · spend · tipo · match ·
  **campaña de origen** · ad group · **línea sugerida** · motivo. Es la lista accionable: con esa info decidís
  a qué línea pertenece y lo mandás a pushear.
- **Descartados por red de seguridad** (`dropped[]`): chips (marca propia / protegido / límite) — solo informativo.

---

## Apéndice — código exacto de los cambios 2 y 3 (para reproducir)

### Cambio 2 — `daily-negatives-supabase` (Step 5): persistir origen en cada candidato
Agregar `origin_campaign` y `origin_ad_group` al schema del candidato (los datos ya se conservan en Step 3):
```json
"candidates":[{"term":"...","clicks":N,"spend":F,"match":"phrase|exact","root":"...","reason":"...",
               "kind":"keyword|asin","product":"<linea/parent>",
               "origin_campaign":"<campaña de origen>","origin_ad_group":"<ad group de origen>"}]
```
Si hay varias campañas de origen, guardar la de mayor spend (o unirlas con `; `). Retro-compat: si faltan, `""`.

### Cambio 3 — `master-dashboard-supabase`
**Step 1a (query):** agregar la clave `push` al `json_build_object` (antes de `daily_link`):
```sql
  'push', (select coalesce(json_agg(json_build_object('cliente',cliente,'datos',datos)),'[]'::json)
           from (select cliente, datos, fecha from public.dashboard_snapshots
                 where tipo='negatives_push' and fecha >= (current_date - 7)
                 order by cliente, fecha desc) p),
```
**Step 2 (compose):** después del bloque RESTOCK, antes de armar `DATA`:
```python
push_by_client = OrderedDict()
for r in payload.get("push", []):
    push_by_client.setdefault(r["cliente"], []).append(r["datos"])
push_clients = []
for cli, snaps in push_by_client.items():
    newest = snaps[0]
    push_clients.append({
        "brand_name": newest.get("brand", cli),
        "marketplace": newest.get("marketplace"),
        "currency_prefix": newest.get("currency_prefix", "$"),
        "days": [{"date_iso": s.get("date_iso", ""), "data_window": s.get("data_window", ""),
                  "summary": s.get("summary", {}), "applied": s.get("applied", []),
                  "held": s.get("held", []), "dropped": s.get("dropped", [])} for s in snaps],
    })
```
Y en el dict `DATA`, agregar `"push": {"clients": push_clients},` (entre `negatives` y `harvest`).

