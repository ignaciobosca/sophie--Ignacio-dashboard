/* =============================================================================
   Master Dashboard - TAB "Review" (revision semanal de negativos)
   -----------------------------------------------------------------------------
   Se agrega al TEMPLATE del Master Dashboard (Supabase: dashboards.template_html,
   id='master'), dentro del <script>. Reusa las mismas clases CSS y helpers
   ($, el, escapeHtml, CURRENT) que las otras tabs. Consume DATA.review que arma el
   composer master-dashboard-supabase desde los snapshots tipo='negatives_review'
   (schema negatives-review-v1 escrito por weekly-negatives-review).

   Ver REVIEW-PATCH.md para los 5 puntos de insercion (DOM, TABS[], allClients,
   clientSel.onchange, boot) ademas de esta funcion.
   ============================================================================= */

function renderReview(){
  const p=$('#page-review'); if(!p) return; p.innerHTML='';
  const R=DATA.review||{clients:[]};
  const intro=el('div'); intro.style.cssText='margin-bottom:14px;color:var(--mut);font-size:13px';
  intro.innerHTML='Revision semanal (viernes): negativos ya aplicados que <b>podrian estar bloqueando '+
    'trafico relevante</b> y son <b>candidatos a archivar</b> (des-negativizar). El skill solo PROPONE - no '+
    'archiva solo, porque archivar en AdLabs es irreversible. Para confirmar deci en un chat: '+
    '<b>"archiva la revision de '+escapeHtml(CURRENT||'[Brand]')+'"</b> (todos) o '+
    '<b>"archiva solo los de alta confianza"</b>.';
  p.appendChild(intro);

  function confRank(x){const c=(x||'').toLowerCase();return c==='high'?0:(c==='med'||c==='medium'?1:2);}
  function confChip(x){const c=(x||'').toLowerCase();
    const col=c==='high'?'var(--green)':(c==='med'||c==='medium'?'var(--amber)':'var(--dim)');
    const lbl=c==='high'?'alta':(c==='med'||c==='medium'?'media':(c==='low'?'baja':(x||'-')));
    return '<span style="color:'+col+';font-weight:700;font-size:12px">'+lbl+'</span>';}

  const sub=(R.clients||[]).filter(c=>c.brand_name===CURRENT);
  sub.forEach((c,ci)=>{
    const days=(c.days||[]).slice();               // nueva -> vieja
    const panel=el('div','client');

    const head=el('div','head');
    head.innerHTML=`<div><div class="name">${escapeHtml(c.brand_name)}<span class="mkt">${c.marketplace||''}</span></div>
      <div class="prod">Revision semanal - candidatos a archivar (des-negativizar)</div></div>
      <div class="kpis">
        <div class="kpi"><div class="n teal" id="rv-rev-${ci}">-</div><div class="l">Revisados</div></div>
        <div class="kpi"><div class="n amber" id="rv-prop-${ci}">-</div><div class="l">A archivar</div></div>
        <div class="kpi"><div class="n green" id="rv-arch-${ci}">-</div><div class="l">Archivados</div></div>
      </div>`;
    panel.appendChild(head);

    const bar=el('div','daybar');
    const dopts=days.map((d,di)=>`<option value="${di}">${d.date_iso||('rev '+(di+1))}${di===0?' (ultima)':''}</option>`).join('');
    bar.innerHTML=`<span class="lbl">Revision</span><select class="daysel" id="rv-day-${ci}">${dopts}</select>
      <span class="meta" id="rv-meta-${ci}"></span>`;
    panel.appendChild(bar);

    const body=el('div'); body.id='rv-body-'+ci; panel.appendChild(body);

    function renderDay(di){
      const d=days[di]||{};
      const prop=(d.proposal||[]).slice();
      const kept=d.excluded_kept||[];
      $('#rv-rev-'+ci).textContent=(d.reviewed!=null?d.reviewed:'-');
      $('#rv-prop-'+ci).textContent=(d.proposed!=null?d.proposed:prop.length);
      $('#rv-arch-'+ci).textContent=(d.archived!=null?d.archived:0);
      $('#rv-meta-'+ci).textContent=(d.note||'');

      body.innerHTML='';

      // --- CANDIDATOS A ARCHIVAR ---
      const h1=el('div'); h1.style.cssText='font-weight:600;margin:6px 0 4px;color:var(--amber)';
      h1.innerHTML=`Candidatos a archivar (${prop.length})`;
      body.appendChild(h1);
      if(prop.length){
        const tw=el('div'); tw.style.overflowX='auto';
        const t=el('table');
        t.innerHTML='<thead><tr><th class="term">Termino</th><th>Match</th><th class="num">Confianza</th>'+
          '<th>Producto / linea</th><th>Motivo</th></tr></thead>';
        const tb=el('tbody');
        prop.sort((a,b)=>confRank(a.confidence)-confRank(b.confidence)).forEach(x=>tb.appendChild(el('tr','',
          `<td class="term">${escapeHtml(x.texto||x.term||'')}</td>`+
          `<td>${escapeHtml(x.match||x.kind||'')}</td>`+
          `<td class="num">${confChip(x.confidence)}</td>`+
          `<td>${escapeHtml(x.product||'')}</td>`+
          `<td class="dim">${escapeHtml(x.reason||'')}</td>`)));
        t.appendChild(tb); tw.appendChild(t); body.appendChild(tw);
        const hint=el('div','note'); hint.style.marginTop='8px';
        hint.innerHTML='Estos negativos podrian estar bloqueando busquedas relevantes. Revisa cada uno; para '+
          'des-negativizarlos deci: <b>"archiva la revision de '+escapeHtml(c.brand_name)+'"</b> (archiva todos) o '+
          '<b>"archiva solo los de alta confianza de '+escapeHtml(c.brand_name)+'"</b>. Es IRREVERSIBLE.';
        body.appendChild(hint);
      } else body.appendChild(el('div','empty','Sin candidatos a archivar esta semana. Los negativos aplicados no bloquean trafico relevante.'));

      // --- MANTENIDOS NEGADOS (conflicto de root, informativo) ---
      if(kept.length){
        const h2=el('div'); h2.style.cssText='font-weight:600;margin:16px 0 4px;color:var(--dim)';
        h2.innerHTML=`Mantenidos negados pese a tocar un termino relevante (${kept.length})`;
        body.appendChild(h2);
        const tw2=el('div'); tw2.style.overflowX='auto';
        const t2=el('table');
        t2.innerHTML='<thead><tr><th class="term">Termino</th><th>Por que se mantiene negado</th></tr></thead>';
        const tb2=el('tbody');
        kept.forEach(x=>tb2.appendChild(el('tr','',
          `<td class="term">${escapeHtml(x.texto||x.term||'')}</td><td class="dim">${escapeHtml(x.reason||'')}</td>`)));
        t2.appendChild(tb2); tw2.appendChild(t2); body.appendChild(tw2);
      }
    }

    bar.querySelector('#rv-day-'+ci).onchange=e=>renderDay(+e.target.value);
    panel.appendChild(body);
    p.appendChild(panel);
    if(days.length) renderDay(0); else body.appendChild(el('div','empty','Sin revisiones para este cliente.'));
  });

  if(!sub.length)
    p.appendChild(el('div','placeholder','<h2>Sin datos</h2><p class="muted">No hay revision semanal para '+(CURRENT||'-')+'.</p>'));
}
