/* =============================================================================
   Master Dashboard - TAB "Review" (revision semanal de negativos)
   -----------------------------------------------------------------------------
   Se agrega al TEMPLATE del Master Dashboard (Supabase: dashboards.template_html,
   id='master'), dentro del <script>. Reusa las mismas clases CSS y helpers
   ($, el, escapeHtml, CURRENT) que las otras tabs. Consume DATA.review que arma el
   composer master-dashboard-supabase desde los snapshots tipo='negatives_review'
   (schema negatives-review-v1 escrito por weekly-negatives-review).

   Trae un SELECTOR por termino (checkbox) + un boton "Generar bloque" que arma un
   comando COPY-PASTE con los seleccionados, para pegar en un chat: archiva esos
   negativos en AdLabs + los agrega a protected_relevant como IGUALDAD EXACTA.

   Ver REVIEW-PATCH.md para los 5 puntos de insercion (DOM, TABS[], allClients,
   clientSel.onchange, boot) ademas de esta funcion.
   ============================================================================= */

function renderReview(){
  const p=$('#page-review'); if(!p) return; p.innerHTML='';
  const R=DATA.review||{clients:[]};
  const intro=el('div'); intro.style.cssText='margin-bottom:14px;color:var(--mut);font-size:13px';
  intro.innerHTML='Revision semanal (viernes): negativos ya aplicados que <b>podrian estar bloqueando '+
    'trafico relevante</b> y son <b>candidatos a archivar</b> (des-negativizar). Tilda los que quieras y '+
    'genera el bloque: es un comando listo para pegar en un chat que <b>archiva</b> esos negativos en AdLabs '+
    'y los <b>protege</b> (igualdad exacta) para que el push no los vuelva a negar. Archivar es IRREVERSIBLE.';
  p.appendChild(intro);

  function esa(s){return String(s==null?'':s).replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
  function confRank(x){const c=(x||'').toLowerCase();return c==='high'?0:(c==='med'||c==='medium'?1:2);}
  function confChip(x){const c=(x||'').toLowerCase();
    const col=c==='high'?'var(--green)':(c==='med'||c==='medium'?'var(--amber)':'var(--dim)');
    const lbl=c==='high'?'alta':(c==='med'||c==='medium'?'media':(c==='low'?'baja':(x||'-')));
    return '<span style="color:'+col+';font-weight:700;font-size:12px">'+lbl+'</span>';}
  const btnCss='padding:4px 10px;border:1px solid var(--dim);border-radius:6px;background:transparent;color:inherit;cursor:pointer;font-size:12px';

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
      const prop=(d.proposal||[]).slice().sort((a,b)=>confRank(a.confidence)-confRank(b.confidence));
      const kept=d.excluded_kept||[];
      const dateIso=d.date_iso||'';
      $('#rv-rev-'+ci).textContent=(d.reviewed!=null?d.reviewed:'-');
      $('#rv-prop-'+ci).textContent=(d.proposed!=null?d.proposed:prop.length);
      $('#rv-arch-'+ci).textContent=(d.archived!=null?d.archived:0);
      $('#rv-meta-'+ci).textContent=(d.note||'');

      body.innerHTML='';

      // --- CANDIDATOS A ARCHIVAR (con selector) ---
      const h1=el('div'); h1.style.cssText='font-weight:600;margin:6px 0 4px;color:var(--amber)';
      h1.innerHTML=`Candidatos a archivar (${prop.length})`;
      body.appendChild(h1);

      if(prop.length){
        // toolbar de seleccion
        const tb=el('div'); tb.style.cssText='display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:6px 0 8px';
        tb.innerHTML=`<span class="dim" style="font-size:12px">Seleccionar:</span>
          <button id="rv-all-${ci}" style="${btnCss}">Todos</button>
          <button id="rv-high-${ci}" style="${btnCss}">Solo alta confianza</button>
          <button id="rv-none-${ci}" style="${btnCss}">Ninguno</button>
          <span style="flex:1"></span>
          <button id="rv-gen-${ci}" style="${btnCss};border-color:var(--amber);color:var(--amber);font-weight:600">Generar bloque (<span id="rv-cnt-${ci}">0</span>)</button>`;
        body.appendChild(tb);

        const tw=el('div'); tw.style.overflowX='auto';
        const t=el('table');
        t.innerHTML='<thead><tr><th style="width:28px"></th><th class="term">Termino</th><th>Match</th>'+
          '<th class="num">Confianza</th><th>Producto / linea</th><th>Motivo</th></tr></thead>';
        const tbody=el('tbody');
        prop.forEach((x,xi)=>{
          const term=x.texto||x.term||'';
          const match=(x.match||x.kind||'').toString();
          tbody.appendChild(el('tr','',
            `<td><input type="checkbox" class="rv-pick" data-i="${xi}" data-term="${esa(term)}" data-match="${esa(match)}" data-conf="${esa(x.confidence||'')}"></td>`+
            `<td class="term">${escapeHtml(term)}</td>`+
            `<td>${escapeHtml(match)}</td>`+
            `<td class="num">${confChip(x.confidence)}</td>`+
            `<td>${escapeHtml(x.product||'')}</td>`+
            `<td class="dim">${escapeHtml(x.reason||'')}</td>`));
        });
        t.appendChild(tbody); tw.appendChild(t); body.appendChild(tw);

        // bloque copy-paste (oculto hasta generar)
        const blk=el('div'); blk.id='rv-blk-'+ci; blk.hidden=true; blk.style.marginTop='10px';
        blk.innerHTML=`<div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">
            <b style="font-size:13px">Bloque para pegar en un chat</b>
            <button id="rv-copy-${ci}" style="${btnCss}">Copiar</button>
            <span id="rv-copied-${ci}" class="dim" style="font-size:12px"></span></div>
          <textarea id="rv-ta-${ci}" readonly style="width:100%;min-height:150px;font-family:monospace;font-size:12px;box-sizing:border-box;padding:8px;border:1px solid var(--dim);border-radius:6px;background:transparent;color:inherit"></textarea>
          <div class="note" style="margin-top:6px">Pega este bloque en un chat con Claude (conectores Supabase + Adlabs). Archiva los negativos seleccionados en AdLabs y los agrega a protected_relevant como igualdad exacta. Es IRREVERSIBLE.</div>`;
        body.appendChild(blk);

        // handlers
        const picks=()=>Array.from(body.querySelectorAll('.rv-pick'));
        const updCnt=()=>{$('#rv-cnt-'+ci).textContent=picks().filter(p=>p.checked).length;};
        body.querySelectorAll('.rv-pick').forEach(cb=>cb.addEventListener('change',updCnt));
        $('#rv-all-'+ci).onclick=()=>{picks().forEach(p=>p.checked=true);updCnt();};
        $('#rv-none-'+ci).onclick=()=>{picks().forEach(p=>p.checked=false);updCnt();};
        $('#rv-high-'+ci).onclick=()=>{picks().forEach(p=>{p.checked=((p.getAttribute('data-conf')||'').toLowerCase()==='high');});updCnt();};
        $('#rv-gen-'+ci).onclick=()=>{
          const sel=picks().filter(p=>p.checked);
          const blkEl=$('#rv-blk-'+ci), ta=$('#rv-ta-'+ci);
          if(!sel.length){blkEl.hidden=false; ta.value='(No hay terminos seleccionados. Tilda al menos uno.)'; return;}
          const lines=sel.map(p=>'- "'+p.getAttribute('data-term')+'" ('+((p.getAttribute('data-match')||'').toUpperCase()||'EXACT')+')').join('\n');
          const txt=
            'Archiva y protege en '+c.brand_name+' estos negativos de la revision semanal'+(dateIso?(' ('+dateIso+')'):'')+'.\n'+
            'Para CADA termino de la lista: (1) archivalo en AdLabs (entity negative_targeting -> update_status ARCHIVED, solo estos, con su reference row-level) y '+
            '(2) agregalo a protected_relevant del perfil de relevancia de '+c.brand_name+' como IGUALDAD EXACTA (Exact), dedup por termino, con nota en change_log. '+
            'No archives ni protejas ningun otro negativo. Es irreversible; confirmo estos:\n'+lines;
          ta.value=txt; blkEl.hidden=false;
          ta.focus(); ta.select();
        };
        $('#rv-copy-'+ci).onclick=()=>{
          const ta=$('#rv-ta-'+ci); ta.select();
          const done=()=>{$('#rv-copied-'+ci).textContent='Copiado';setTimeout(()=>{$('#rv-copied-'+ci).textContent='';},2000);};
          if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(ta.value).then(done,()=>{try{document.execCommand('copy');done();}catch(e){}});}
          else{try{document.execCommand('copy');done();}catch(e){}}
        };
        updCnt();
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
