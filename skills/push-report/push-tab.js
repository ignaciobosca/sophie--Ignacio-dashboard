/* =============================================================================
   Master Dashboard - TAB "Push" (informe diario del autopush)
   -----------------------------------------------------------------------------
   Este bloque se agrega al TEMPLATE del Master Dashboard (Supabase:
   dashboards.template_html, id='master'), dentro del <script>. Reusa las mismas
   clases CSS y helpers ($ , el, money, escapeHtml) que las otras tabs - no hace
   falta CSS nuevo. Consume DATA.push que arma el composer master-dashboard-supabase.

   Ver PATCH.md para los 5 puntos de insercion (DOM, TABS[], allClients,
   clientSel.onchange, boot) ademas de esta funcion.
   ============================================================================= */

function renderPush(){
  const p=$('#page-push'); if(!p) return; p.innerHTML='';
  const P=DATA.push||{clients:[]};
  const intro=el('div'); intro.style.cssText='margin-bottom:14px;color:var(--mut);font-size:13px';
  intro.innerHTML='Informe diario del <b>autopush</b>: negativos que se aplicaron solos a AdLabs, y los '+
    '<b>retenidos</b> por no tener producto asignado (<b>General - sin asignar</b>) que necesitan tu '+
    'decision. Elegi el dia. Los retenidos muestran clicks, spend, la campania/ad-group de origen y una '+
    '<b>linea sugerida</b> para que decidas a que producto asignarlos.';
  p.appendChild(intro);

  const sub=(P.clients||[]).filter(c=>c.brand_name===CURRENT);
  sub.forEach((c,ci)=>{
    const cp=c.currency_prefix||'$';
    const days=(c.days||[]).slice();               // nuevo -> viejo
    const panel=el('div','client');

    // -- header ------------------------------------------------
    const head=el('div','head');
    head.innerHTML=`<div><div class="name">${escapeHtml(c.brand_name)}<span class="mkt">${c.marketplace||''}</span></div>
      <div class="prod">Autopush diario - negativos aplicados y retenidos</div></div>
      <div class="kpis">
        <div class="kpi"><div class="n green" id="pu-cre-${ci}">-</div><div class="l">Creados</div></div>
        <div class="kpi"><div class="n amber" id="pu-held-${ci}">-</div><div class="l">Retenidos</div></div>
        <div class="kpi"><div class="n teal" id="pu-hs-${ci}">-</div><div class="l">Spend retenido</div></div>
      </div>`;
    panel.appendChild(head);

    // -- selector de dia ---------------------------------------
    const bar=el('div','daybar');
    const dopts=days.map((d,di)=>`<option value="${di}">${d.date_iso||('dia '+(di+1))}${di===0?' (hoy)':''}</option>`).join('');
    bar.innerHTML=`<span class="lbl">Dia</span><select class="daysel" id="pu-day-${ci}">${dopts}</select>
      <span class="meta" id="pu-meta-${ci}"></span>`;
    panel.appendChild(bar);

    const body=el('div'); body.id='pu-body-'+ci; panel.appendChild(body);

    function renderDay(di){
      const d=days[di]||{}; const s=d.summary||{};
      const applied=d.applied||[], held=d.held||[], asins=d.asins_skipped||[], dropped=d.dropped||[];
      $('#pu-cre-'+ci).textContent=(s.created!=null?s.created:applied.reduce((a,x)=>a+(x.created||0),0));
      $('#pu-held-'+ci).textContent=(s.held!=null?s.held:held.length);
      const heldSpend=(s.held_spend!=null?s.held_spend:held.reduce((a,x)=>a+(x.spend||0),0));
      $('#pu-hs-'+ci).textContent=money(heldSpend,cp);
      $('#pu-meta-'+ci).textContent=(d.data_window?('Datos: '+d.data_window+' - '):'')+
        `${applied.length} aplicados - ${held.length} retenidos - ${asins.length} ASINs - ${dropped.length} descartados`;

      body.innerHTML='';

      // --- APLICADOS ---
      const h1=el('div'); h1.style.cssText='font-weight:600;margin:6px 0 4px'; h1.innerHTML='Pusheado a AdLabs';
      body.appendChild(h1);
      if(applied.length){
        const tw=el('div'); tw.style.overflowX='auto';
        const t=el('table');
        t.innerHTML='<thead><tr><th class="term">Termino</th><th class="num">Clk</th><th class="num">Spend</th>'+
          '<th>Negado como</th><th>Producto / linea</th><th class="num">Ad groups</th>'+
          '<th class="num">Creados</th><th class="num">Ya estaban</th></tr></thead>';
        const tb=el('tbody');
        applied.forEach(x=>tb.appendChild(el('tr','',
          `<td class="term">${escapeHtml(x.term)}</td><td class="num">${x.clicks!=null?x.clicks:'-'}</td>`+
          `<td class="num">${money(x.spend,cp)}</td><td>${escapeHtml(x.match||'')}</td>`+
          `<td>${escapeHtml(x.line||'')}</td><td class="num">${x.ad_groups!=null?x.ad_groups:'-'}</td>`+
          `<td class="num">${x.created!=null?x.created:'-'}</td><td class="num dim">${x.skipped!=null?x.skipped:'-'}</td>`)));
        t.appendChild(tb); tw.appendChild(t); body.appendChild(tw);
      } else body.appendChild(el('div','empty','Nada pusheado este dia.'));

      // --- RETENIDOS (General) - accionable ---
      const h2=el('div'); h2.style.cssText='font-weight:600;margin:16px 0 4px;color:var(--amber)';
      h2.innerHTML=`Retenidos - decidir producto (${held.length})`;
      body.appendChild(h2);
      if(held.length){
        const tw2=el('div'); tw2.style.overflowX='auto';
        const t2=el('table');
        t2.innerHTML='<thead><tr><th class="term">Termino</th><th class="num">Clk</th><th class="num">Spend</th>'+
          '<th>Tipo</th><th>Match</th><th>Campania de origen</th><th>Ad group</th>'+
          '<th>Linea sugerida</th><th>Motivo</th></tr></thead>';
        const tb2=el('tbody');
        held.slice().sort((a,b)=>(b.spend||0)-(a.spend||0)).forEach(x=>tb2.appendChild(el('tr','',
          `<td class="term">${escapeHtml(x.term)}</td><td class="num">${x.clicks!=null?x.clicks:'-'}</td>`+
          `<td class="num">${money(x.spend,cp)}</td><td>${escapeHtml(x.kind||'')}</td>`+
          `<td>${escapeHtml(x.match||'')}</td><td class="dim">${escapeHtml(x.origin_campaign||'-')}</td>`+
          `<td class="dim">${escapeHtml(x.origin_ad_group||'-')}</td>`+
          `<td>${x.suggested_line?('<b>'+escapeHtml(x.suggested_line)+'</b>'):'<span class="dim">sin sugerencia</span>'}</td>`+
          `<td class="dim">${escapeHtml(x.reason||'')}</td>`)));
        t2.appendChild(tb2); tw2.appendChild(t2); body.appendChild(tw2);
        const hint=el('div','note'); hint.style.marginTop='8px';
        hint.innerHTML='Para aplicar un retenido: asigna la linea en el onboarding/config del producto (o deci en un '+
          'chat: <b>"asigna estos terminos a la linea X en '+escapeHtml(c.brand_name)+' y pushealos"</b>) y corre '+
          'el autopush de nuevo - ya con producto resoluble los aplica.';
        body.appendChild(hint);
      } else body.appendChild(el('div','empty','Sin retenidos este dia. Todo se pudo asignar y pushear.'));

      // --- ASINs (no auto-negados) - decidir a mano ---
      const h4=el('div'); h4.style.cssText='font-weight:600;margin:16px 0 4px;color:var(--blue)';
      h4.innerHTML=`ASINs detectados - no auto-negados (${asins.length})`;
      body.appendChild(h4);
      if(asins.length){
        const tw3=el('div'); tw3.style.overflowX='auto';
        const t3=el('table');
        t3.innerHTML='<thead><tr><th class="term">ASIN</th><th class="num">Clk</th><th class="num">Spend</th>'+
          '<th>Producto / linea</th><th>Campania de origen</th><th>Ad group</th><th>Motivo</th></tr></thead>';
        const tb3=el('tbody');
        asins.slice().sort((a,b)=>(b.spend||0)-(a.spend||0)).forEach(x=>tb3.appendChild(el('tr','',
          `<td class="term">${escapeHtml(x.term)}</td><td class="num">${x.clicks!=null?x.clicks:'-'}</td>`+
          `<td class="num">${money(x.spend,cp)}</td><td>${escapeHtml(x.product||'')}</td>`+
          `<td class="dim">${escapeHtml(x.origin_campaign||'-')}</td><td class="dim">${escapeHtml(x.origin_ad_group||'-')}</td>`+
          `<td class="dim">${escapeHtml(x.reason||'ASIN - no auto-negado')}</td>`)));
        t3.appendChild(tb3); tw3.appendChild(t3); body.appendChild(tw3);
        const hintA=el('div','note'); hintA.style.marginTop='8px';
        hintA.innerHTML='Los ASINs (terminos b0...) NO se auto-negativizan por regla. Si queres negar alguno como '+
          'product target, deci: <b>"negativiza el ASIN b0... en '+escapeHtml(c.brand_name)+'"</b> (via adlabs-push-negatives).';
        body.appendChild(hintA);
      } else body.appendChild(el('div','empty','Sin ASINs detectados este dia.'));

      // --- DESCARTADOS (red de seguridad) - resumen ---
      if(dropped.length){
        const h3=el('div'); h3.style.cssText='font-weight:600;margin:16px 0 4px;color:var(--dim)';
        h3.innerHTML=`Descartados por red de seguridad (${dropped.length})`;
        body.appendChild(h3);
        const chips=el('div'); chips.style.cssText='display:flex;flex-wrap:wrap;gap:6px';
        dropped.forEach(x=>{const ch=el('span','chip'); ch.textContent=`${x.term} (${x.reason})`; chips.appendChild(ch);});
        body.appendChild(chips);
      }
    }

    bar.querySelector('#pu-day-'+ci).onchange=e=>renderDay(+e.target.value);
    panel.appendChild(body);
    p.appendChild(panel);
    if(days.length) renderDay(0); else body.appendChild(el('div','empty','Sin recibos de push para este cliente.'));
  });

  if(!sub.length)
    p.appendChild(el('div','placeholder','<h2>Sin datos</h2><p class="muted">No hay informe de push para '+(CURRENT||'-')+'.</p>'));
}
