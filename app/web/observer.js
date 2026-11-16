(() => {
  const el=id=>document.getElementById(id), seen=new Map();
  let cursor=0, stream=null, key='', running=true, controller=null;
  try{const config=JSON.parse(localStorage.getItem('conecta-neoconexion-config')||'{}');key=sessionStorage.getItem('conecta-observer-key')||sessionStorage.getItem('conecta-api-key')||config.apiKey||'';}catch{}
  el('observerKey').value=key;el('apiOrigin').textContent=location.origin;
  document.querySelector('.machine-intro').innerHTML='Esta página observa las solicitudes <strong>reales del servidor</strong>. La app original de vacantes permanece intacta en su propia pestaña. La salida se muestra cuando la API ha producido la respuesta.';
  el('observerSettings').onsubmit=event=>{event.preventDefault();key=el('observerKey').value;try{sessionStorage.setItem('conecta-observer-key',key);}catch{}controller?.abort();};
  async function poll(){
    controller=new AbortController();const timer=setTimeout(()=>controller.abort(),10000);
    try{
      const response=await fetch(`/api/v1/visualization/requests?after=${cursor}`,{headers:key?{'X-API-Key':key}:{},signal:controller.signal,cache:'no-store'});
      if(!response.ok)throw Error(response.status===401?'API Key incorrecta o ausente':`HTTP ${response.status}`);
      const data=await response.json();
      if(stream!==null&&stream!==data.stream_id){cursor=0;stream=data.stream_id;seen.clear();return;}
      stream=data.stream_id;cursor=data.cursor;
      for(const request of data.requests){
        let entry=seen.get(request.id);
        if(!entry){entry=JsonMachine.start(request.method,request.path,request.request_body??undefined);seen.set(request.id,entry);if(seen.size>80)seen.delete(seen.keys().next().value);}
        entry.body=request.request_body??undefined;
        entry.request_truncated=request.request_truncated;entry.response_truncated=request.response_truncated;
        if(request.state==='completed'){
          entry.started=performance.now()-request.duration_ms;
          const headers=new Headers();if(request.request_id)headers.set('X-Request-ID',request.request_id);
          JsonMachine.finish(entry,{status:request.status,ok:request.status>=200&&request.status<300,headers},request.response,request.response_raw,request.response_json);
        }else if(request.state==='interrupted')JsonMachine.fail(entry,new Error('Solicitud interrumpida'));
        else JsonMachine.refresh(entry);
      }
      el('connection').textContent=`Conectado a ${location.origin} · actividad real · actualización automática`;
    }catch(error){el('connection').textContent=`Visor sin conexión: ${error.name==='AbortError'?'espera agotada o reconexión':error.message}. No se inventan nuevas respuestas.`;}
    finally{clearTimeout(timer);controller=null;}
  }
  (async()=>{while(running){await poll();await new Promise(resolve=>setTimeout(resolve,700));}})();
  window.addEventListener('pagehide',()=>{running=false;controller?.abort();});
})();
