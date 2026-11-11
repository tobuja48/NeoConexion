/* Video playback follows a selected real API record. Replaying never resends JSON. */
(() => {
  const el=id=>document.getElementById(id),video=el('printerVideo'),stage=el('printerStage');
  const pause=el('printerPause'),replay=el('printerReplay'),status=el('printerMediaStatus');
  const reduced=matchMedia('(prefers-reduced-motion: reduce)');
  const files={preview:'espera.mp4',entrada:'entrada.mp4',espera:'espera.mp4',salida:'salida.mp4'};
  const playbackSpeed=2;
  video.muted=true;video.defaultMuted=true;
  video.defaultPlaybackRate=playbackSpeed;video.playbackRate=playbackSpeed;
  let entry=null,identity=null,phase='idle',generation=0,userPaused=false,manualMotion=false;
  const animate=()=>!reduced.matches||manualMotion;
  function label(){
    stage.dataset.phase=phase;stage.dataset.motion=animate()?'normal':'reduced';
    el('printerError').hidden=phase!=='error';
    if(phase==='error'){
      const detail=entry?.response?.error?.message;
      const reason=typeof detail==='string'?detail:'La API no confirmó un resultado exitoso.';
      const missingCandidate=entry?.status===404&&reason.toLowerCase().includes('candidato');
      const missingJob=entry?.status===404&&reason.toLowerCase().includes('vacante');
      el('printerError').textContent=missingCandidate?
        `${reason} Guarda el perfil o sincroniza los ejemplos desde Integración NeoConexión en la app de vacantes.`:
        missingJob?`${reason} Publica la vacante o sincroniza los ejemplos desde Integración NeoConexión.`:
        `${entry?.status?'HTTP '+entry.status+': ':''}${reason} No se imprime una salida de éxito.`;
    }
    const done=entry?.state==='success';
    el('printerPhase').textContent=phase==='preview'?'Video automático · esperando actividad real de la API':phase==='idle'?'Esperando una solicitud real':phase==='error'?`Error${entry?.status?' HTTP '+entry.status:''} · sin impresión de éxito`:
      phase==='entrada'?(done?`Entrada · HTTP ${entry.status} ya confirmado; representación visual`:'Entrada del JSON · solicitud real observada'):
      phase==='espera'?'Esperando la respuesta real de NeoConexión':phase==='salida'?`HTTP ${entry.status} confirmado · imprimiendo salida`:`Documento confirmado · HTTP ${entry.status}`;
    pause.disabled=phase==='idle'||phase==='error'||phase==='complete';
    pause.textContent=userPaused||video.paused?'Reproducir video':'Pausar video';
    replay.disabled=!done;
  }
  function stop(next){
    generation++;phase=next;video.onloadedmetadata=null;video.autoplay=false;video.pause();video.removeAttribute('src');video.load();label();
  }
  function clip(next,{freezeEnd=false}={}){
    const token=++generation;phase=next;video.pause();video.loop=next==='espera'||next==='preview';
    video.autoplay=animate()&&!userPaused;
    const url=new URL('./media/'+files[next],location.href).href;
    video.onloadedmetadata=()=>{
      if(token!==generation||video.currentSrc!==url)return;
      video.playbackRate=playbackSpeed;
      video.currentTime=freezeEnd?Math.max(0,video.duration-.035):0;
      if(freezeEnd){phase='complete';label();}
      else if(animate()&&!userPaused){
        video.play().then(()=>{if(token===generation)label();}).catch(()=>{
          if(token===generation){status.textContent='Pulsa Reproducir video para habilitar la reproducción.';label();}
        });
      }
      label();
    };
    status.textContent=!animate()?'Movimiento reducido · fotograma estático.':next==='preview'?'Bucle visual automático · no genera solicitudes ni resultados.':'Representación visual de una operación real · los JSON no se generan en el video.';
    video.src=url;video.load();label();
  }
  function sync(current){
    entry=current;
    if(!entry||entry.state==='draft'){
      if(phase!=='preview')clip('preview');
      else if(!animate()){video.autoplay=false;video.pause();label();}
      else if(!userPaused&&video.paused){video.autoplay=true;video.play().then(label).catch(()=>{status.textContent='Pulsa Reproducir video para habilitar la reproducción.';label();});}
      return;
    }
    if(entry.id!==identity){
      identity=entry.id;
      if(entry.state==='error'){stop('error');return;}
      if(!animate())clip(entry.state==='success'?'salida':'espera',{freezeEnd:entry.state==='success'});
      else clip('entrada');
    }else if(entry.state==='error'){if(phase!=='error')stop('error');}
    else if(entry.state==='success'&&phase==='espera')clip('salida',{freezeEnd:!animate()});
    label();
  }
  video.addEventListener('ended',()=>{
    if(phase==='entrada'){
      if(entry?.state==='error')stop('error');
      else clip(entry?.state==='success'?'salida':'espera');
    }else if(phase==='salida'){phase='complete';label();}
  });
  video.addEventListener('error',()=>{
    if(video.getAttribute('src'))status.textContent='No se pudo reproducir el video. Los JSON y el estado HTTP siguen disponibles.';
  });
  pause.onclick=()=>{
    if(video.paused){userPaused=false;manualMotion=true;video.play().then(label).catch(()=>status.textContent='El navegador bloqueó el video; los JSON siguen disponibles.');}
    else{userPaused=true;video.pause();label();}
  };
  replay.onclick=()=>{if(entry?.state==='success'){identity=null;sync(entry);}};
  reduced.addEventListener('change',()=>{manualMotion=false;identity=null;sync(entry);});
  document.addEventListener('visibilitychange',()=>{
    if(document.hidden)video.pause();else if(animate()&&!userPaused&&!['idle','error','complete'].includes(phase))video.play().catch(()=>{});
  });
  window.PrinterVideo={sync};sync(null);
})();
