/* The animation observes the actual HTTP client. It never fabricates a response. */
(() => {
  const entries = [];
  let selected = null, sequence = 0, ticker = null;
  const shell = document.createElement('section');
  shell.className = 'machine'; shell.id = 'jsonMachine'; shell.dataset.state = 'idle';
  shell.setAttribute('aria-label', 'Máquina JSON conectada a NeoConexión');
  shell.innerHTML = `
    <div class="machine-inner"><details open id="machineDetails"><summary>
      <div><div class="machine-eyebrow">Laboratorio en vivo</div><h2>La máquina de NeoConexión</h2></div>
      <span class="machine-summary" id="machineCount">Sin solicitudes</span></summary>
      <p class="machine-intro">Completa un perfil o publica una vacante. Aquí verás <strong>el JSON que viaja a la API y su respuesta real</strong>. Los engranajes giran mientras la solicitud espera; la salida se libera al recibir HTTP.</p>
      <div class="machine-line">
        <div class="machine-port"><span class="machine-port-icon">{ → }</span><b>JSON de entrada</b><small id="machineRoute">Prepara un formulario</small></div>
        <div class="machine-wire machine-wire-in"><i class="machine-packet"></i></div>
        <div class="machine-core"><i class="machine-led"></i><svg viewBox="0 0 110 76" aria-hidden="true">
          <g class="machine-gear" fill="none" stroke="#7ce7c2" stroke-width="6"><circle cx="41" cy="33" r="20" stroke-dasharray="7 5"/><circle cx="41" cy="33" r="10" stroke-width="3"/></g>
          <g class="machine-gear reverse" fill="none" stroke="#ffcc83" stroke-width="5"><circle cx="77" cy="51" r="15" stroke-dasharray="6 4"/><circle cx="77" cy="51" r="6" stroke-width="3"/></g></svg>
          <b>NeoConexión</b><small>FastAPI · motor de matching · Neo4j</small></div>
        <div class="machine-wire machine-wire-out"><i class="machine-packet"></i></div>
        <div class="machine-port machine-output"><span class="machine-port-icon">{ … }</span><b id="machineOutputTitle">Esperando entrada</b><small id="machineResponseHint">Sin respuesta todavía</small></div>
      </div>
      <div class="machine-steps" aria-label="Estado de la solicitud"><span class="machine-step" data-step="draft">01 Preparado</span><span class="machine-step" data-step="pending">02 Enviado / esperando</span><span class="machine-step" data-step="received">03 Respuesta HTTP</span></div>
      <div class="machine-state"><strong id="machineState" role="status" aria-live="polite">La máquina está lista</strong><span id="machineElapsed"></span><code id="machineRequestId"></code></div>
      <div class="machine-json-grid">
        <div class="machine-json"><div class="machine-json-head"><span>ENTRADA · cuerpo enviado</span><button type="button" id="copyMachineInput" disabled>Copiar</button></div><pre id="machineInput">Completa los datos de un formulario para ver su JSON.</pre></div>
        <div class="machine-json response"><div class="machine-json-head"><span>SALIDA · respuesta de la API</span><button type="button" id="copyMachineOutput" disabled>Copiar</button></div><pre id="machineOutput">La salida aparecerá únicamente después de recibir una respuesta real.</pre></div>
      </div><div class="machine-history" id="machineHistory" aria-label="Solicitudes de esta sesión"></div>
      <p class="machine-empty">El historial vive en esta pestaña. No incluye la API Key. La animación representa el viaje HTTP; no mide pasos internos del servidor.</p>
    </details></div>`;
  document.querySelector('header.top').after(shell);
  const launch = document.createElement('button');
  launch.type='button'; launch.className='machine-launch'; launch.textContent='Ver máquina JSON ↗';
  launch.onclick=()=>{document.getElementById('machineDetails').open=true; shell.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth',block:'start'});};
  document.body.append(launch);
  const el=id=>document.getElementById(id);
  const format=value=>JSON.stringify(value,null,2);
  function renderHistory(){
    const history=el('machineHistory'); history.replaceChildren();
    entries.slice().reverse().forEach(entry=>{
      const button=document.createElement('button'); button.type='button';
      button.textContent=`${entry.status ?? (entry.state==='pending'?'…':'ERR')} · ${entry.method} ${entry.path}`;
      button.title=button.textContent; button.dataset.state=entry.state;
      button.setAttribute('aria-pressed',String(entry===selected));
      button.onclick=()=>{selected=entry; render();}; history.append(button);
    });
    const pending=entries.filter(e=>e.state==='pending').length;
    el('machineCount').textContent=`${entries.length} solicitudes · ${pending} en curso`;
  }
  function render(){
    const entry=selected;
    shell.dataset.state=entry?.state ?? 'idle';
    el('machineRoute').textContent=entry ? `${entry.method} ${entry.path}` : 'Prepara un formulario';
    el('machineInput').textContent=entry?.request_truncated?'La entrada supera el límite del visor; no se muestra como un JSON completo.':entry ? (entry.body===undefined?'Sin cuerpo JSON en esta solicitud.':format(entry.body)) : 'Esperando una solicitud real de la API.';
    el('copyMachineInput').disabled=entry?.body===undefined||!!entry?.request_truncated;
    const received=!!entry?.received;
    el('copyMachineOutput').disabled=!received||!!entry?.response_truncated;
    el('machineOutput').textContent=entry?.response_truncated?'La respuesta supera el límite del visor; no se muestra como un JSON completo.':received ? (entry.json ? format(entry.response) : entry.raw || '(respuesta sin cuerpo)') :
      entry?.state==='error' ? 'No se recibió respuesta HTTP. No hay JSON de salida confirmado.' :
      entry?.state==='pending' ? 'Esperando a NeoConexión… todavía no hay JSON de salida.' : 'Todavía no se envió esta entrada a la API.';
    el('machineOutputTitle').textContent=received ? `HTTP ${entry.status}` : entry?.state==='pending'?'Procesando solicitud…':entry?.state==='error'?'Sin confirmación':'Esperando envío';
    el('machineResponseHint').textContent=received ? (entry.state==='success'?'Respuesta real recibida':'La API devolvió un error') : entry?.state==='pending'?'La máquina espera al servidor':'Sin respuesta todavía';
    el('machineState').textContent=entry?.message ?? 'La máquina está lista';
    el('machineRequestId').textContent=entry?.requestId?`X-Request-ID: ${entry.requestId}`:'';
    el('machineElapsed').textContent=entry?.started!==undefined?`${Math.round((entry.ended??performance.now())-entry.started)} ms`:'';
    shell.querySelectorAll('[data-step]').forEach(step=>step.classList.toggle('active',
      step.dataset.step==='draft'?!!entry:step.dataset.step==='pending'?!!entry&&entry.state!=='draft':received));
    renderHistory();
  }
  function schedule(){
    if(ticker===null) ticker=setInterval(()=>{
      if(selected?.state==='pending') el('machineElapsed').textContent=`${Math.round(performance.now()-selected.started)} ms`;
      if(!entries.some(e=>e.state==='pending')){clearInterval(ticker);ticker=null;}
    },200);
  }
  window.JsonMachine={
    preview(method,path,body){
      if(entries.some(e=>e.state==='pending'&&e.method==='POST')) return;
      selected={state:'draft',method,path,body:JSON.parse(JSON.stringify(body)),message:'JSON preparado · todavía no enviado'}; render();
    },
    start(method,path,body){
      const entry={id:++sequence,state:'pending',method,path,
        body:body===undefined?undefined:JSON.parse(JSON.stringify(body)),started:performance.now(),message:'Solicitud enviada · esperando respuesta real de NeoConexión'};
      entries.push(entry);
      if(entries.length>40){const index=entries.findIndex(e=>e.state!=='pending');if(index>=0)entries.splice(index,1);}
      selected=entry; render(); schedule();
      if(method==='POST'){
        el('machineDetails').open=true;
        shell.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth',block:'start'});
      }
      return entry;
    },
    finish(entry,response,body,raw,isJson){
      Object.assign(entry,{received:true,status:response.status,response:body,raw,json:isJson,
        state:response.ok&&(isJson||entry.response_truncated)?'success':'error',ended:performance.now(),requestId:response.headers.get('X-Request-ID'),
        message:entry.response_truncated?`Respuesta HTTP ${response.status} recibida · cuerpo demasiado grande para el visor`:!isJson?`La respuesta HTTP ${response.status} no contiene JSON válido`:response.ok?`Confirmado por la API · HTTP ${response.status}`:`Respuesta de error de la API · HTTP ${response.status}`});
      if(selected===entry)render();else renderHistory();
    },
    fail(entry,error){
      Object.assign(entry,{state:'error',ended:performance.now(),received:false,
        message:error.name==='AbortError'?'Tiempo de espera agotado · no se recibió confirmación':'No se pudo conectar · no hay respuesta confirmada'});
      if(selected===entry)render();else renderHistory();
    },
    refresh(entry){if(selected===entry)render();}
  };
  [['copyMachineInput','machineInput'],['copyMachineOutput','machineOutput']].forEach(([button,target])=>{
    el(button).onclick=async()=>{try{await navigator.clipboard.writeText(el(target).textContent);el(button).textContent='Copiado';}catch{el(button).textContent='Selecciona el texto';}setTimeout(()=>el(button).textContent='Copiar',1800);};
  });
})();
