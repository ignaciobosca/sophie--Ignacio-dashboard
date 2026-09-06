# #5 — Dashboard: cola de aprobación de LOW (checkboxes + "copiar aprobados")

Los candidatos `low` que el gate del autopush retuvo salen en el **recibo de push** (`negatives_push`,
`held_low_confidence[]`). El dashboard los muestra en una **cola de aprobación** dentro del **tab Push**:
cada uno con checkbox + su `evidence` al lado, y un botón **"Copiar aprobados"** que arma el bloque que
después pegás en el chat con *"pushear low aprobados de [Brand]"* (→ `daily-negatives-autopush` MODE=approved).

Son **dos cambios**: (A) el composer pasa el campo nuevo al DATA; (B) el template lo renderiza.

---

## A) Composer — `master-dashboard-supabase` (Step 2, bloque PUSH)

En el armado del día del push (donde hoy se copian `applied/held/asins_skipped/dropped`), agregar una línea
para `held_low_confidence`:

```python
        "days": [
            {
                "date_iso": s.get("date_iso"),
                "data_window": s.get("data_window"),
                "summary": s.get("summary", {}),
                "applied": s.get("applied", []),
                "held": s.get("held", []),
                "held_low_confidence": s.get("held_low_confidence", []),   # ← NUEVO (V2 del autopush)
                "asins_skipped": s.get("asins_skipped", []),
                "dropped": s.get("dropped", []),
            }
            for s in snaps
        ],
```

Nada más cambia en el composer: `held_low_confidence` viaja dentro de `DATA.push.clients[].days[]`, ASCII-safe
como el resto. Retrocompat: recibos viejos sin el campo → `[]` (la cola no aparece, no rompe).

---

## B) Template del master (Supabase `dashboards` id='master') — renderer de la cola

Pegar esta función en el `<script>` del template y llamarla desde `renderPush()` (o donde se arma el tab Push),
una vez por cliente, pasándole el `day` más nuevo. Es vanilla JS, hereda los estilos del dashboard.

```html
<style>
  .aq-wrap{margin:16px 0;border:1px solid var(--border,#3334);border-radius:10px;padding:12px 14px}
  .aq-head{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;margin-bottom:8px}
  .aq-title{font-weight:600}
  .aq-title .aq-count{opacity:.7;font-weight:400}
  .aq-actions{display:flex;gap:8px;align-items:center}
  .aq-btn{cursor:pointer;border:1px solid var(--border,#3334);background:var(--btn,#2a2a30);
          color:inherit;border-radius:8px;padding:6px 10px;font-size:13px}
  .aq-btn:disabled{opacity:.45;cursor:not-allowed}
  .aq-table{width:100%;border-collapse:collapse;font-size:13px}
  .aq-table th,.aq-table td{text-align:left;padding:6px 8px;border-bottom:1px solid var(--border,#3334);vertical-align:top}
  .aq-table th{opacity:.7;font-weight:500}
  .aq-ev{opacity:.8}
  .aq-empty{opacity:.6;font-size:13px;padding:4px 2px}
  .aq-copied{color:var(--ok,#3ecf8e);font-size:12px}
</style>

<script>
// Cola de aprobación de LOW para un cliente. `day` = el día más nuevo del push (DATA.push.clients[i].days[0]).
function renderApprovalQueue(brand, day) {
  const rows = (day && day.held_low_confidence) || [];
  const safe = s => String(s == null ? "" : s)
      .replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
  const slug = brand.replace(/[^a-z0-9]+/gi,"_");

  if (!rows.length) {
    return `<div class="aq-wrap"><div class="aq-title">Cola de aprobacion (baja confianza)</div>
            <div class="aq-empty">Sin candidatos de baja confianza para ${safe(brand)}. Todo lo pusheable ya se aplico solo.</div></div>`;
  }

  const body = rows.map((r,i) => {
    const id = `aq_${slug}_${i}`;
    // data-* llevan lo que el bloque de copiado necesita (formato MODE=approved: term \t match \t reason \t product)
    return `<tr>
      <td><input type="checkbox" class="aq-cb aq-cb-${slug}" id="${id}"
                 data-term="${safe(r.term)}" data-match="${safe(r.match||'')}"
                 data-reason="${safe(r.reason||'')}" data-product="${safe(r.product||'')}"></td>
      <td><label for="${id}">${safe(r.term)}</label></td>
      <td>${safe(r.match||'')}</td>
      <td>${safe(r.product||'')}</td>
      <td class="aq-ev">${safe(r.evidence||r.reason||'')}</td>
      <td>${safe(r.spend!=null?r.spend:'')}</td>
    </tr>`;
  }).join("");

  return `<div class="aq-wrap" id="aq-wrap-${slug}">
    <div class="aq-head">
      <div class="aq-title">Cola de aprobacion (baja confianza) <span class="aq-count">· ${rows.length} terminos</span></div>
      <div class="aq-actions">
        <button class="aq-btn" onclick="aqToggleAll('${slug}',true)">Marcar todos</button>
        <button class="aq-btn" onclick="aqToggleAll('${slug}',false)">Limpiar</button>
        <button class="aq-btn" id="aq-copy-${slug}" onclick="aqCopyApproved('${slug}','${safe(brand)}')">Copiar aprobados</button>
        <span class="aq-copied" id="aq-msg-${slug}"></span>
      </div>
    </div>
    <table class="aq-table">
      <thead><tr><th></th><th>Termino</th><th>Match</th><th>Producto</th><th>Evidencia</th><th>Spend</th></tr></thead>
      <tbody>${body}</tbody>
    </table>
  </div>`;
}

function aqToggleAll(slug, on){
  document.querySelectorAll(".aq-cb-"+slug).forEach(cb => cb.checked = on);
}

function aqCopyApproved(slug, brand){
  const checked = [...document.querySelectorAll(".aq-cb-"+slug)].filter(cb => cb.checked);
  const msg = document.getElementById("aq-msg-"+slug);
  if (!checked.length){ if(msg) msg.textContent = "Nada seleccionado."; return; }
  // Formato que espera MODE=approved: una linea por termino, TAB-separado: term \t match \t reason \t product
  const lines = checked.map(cb =>
     [cb.dataset.term, cb.dataset.match, cb.dataset.reason, cb.dataset.product].join("\t"));
  const block = lines.join("\n");
  const done = () => { if(msg) msg.textContent = `${checked.length} copiados — pegalos con "pushear low aprobados de ${brand}"`; };
  if (navigator.clipboard && navigator.clipboard.writeText){
    navigator.clipboard.writeText(block).then(done, () => aqFallbackCopy(block, done));
  } else { aqFallbackCopy(block, done); }
}

function aqFallbackCopy(text, cb){
  const ta = document.createElement("textarea");
  ta.value = text; ta.style.position="fixed"; ta.style.opacity="0";
  document.body.appendChild(ta); ta.select();
  try { document.execCommand("copy"); } catch(e) {}
  document.body.removeChild(ta); cb && cb();
}
</script>
```

**Dónde llamarla:** dentro del render del tab Push, por cada cliente, después de las secciones existentes
(applied / held / asins_skipped). Ej.:

```js
// dentro del loop de clientes del tab Push:
html += renderApprovalQueue(client.brand_name, client.days[0]);
```

---

## Contrato del bloque copiado (NO cambiar sin actualizar el autopush)

El botón copia líneas **TAB-separadas**: `term ⇥ match ⇥ reason ⇥ product`.
Es exactamente lo que `daily-negatives-autopush` **MODE=approved** parsea (mismo formato que el `learn`).
Si se agrega/quita una columna acá, actualizar el parser del MODE=approved en `04-daily-negatives-autopush`.

## Flujo completo del LOW (recordatorio)

1. Autopush retiene `low` → `held_low_confidence[]` en el recibo `negatives_push`.
2. Composer lo pasa a `DATA.push` → template lo muestra como cola de aprobación con checkboxes.
3. Nacho tilda → **Copiar aprobados** → pega en el chat: *"pushear low aprobados de [Brand]"*.
4. Autopush `MODE=approved`: saltea el gate, pushea con el mismo motor (redes de seguridad + ruteo + apply)
   y **aprende** (queda en el perfil → la próxima vez entra como `high` y se autopushea solo).
