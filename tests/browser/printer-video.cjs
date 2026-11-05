/* Playback-state tests with controlled frontend events. Real persistence is covered by conecta.cjs. */
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict');
const path=require('node:path');
const base=process.env.BASE_URL||'http://127.0.0.1:18000';
(async()=>{
  const browser=await chromium.launch(process.env.BROWSER_CHANNEL?{channel:process.env.BROWSER_CHANNEL,headless:true}:{headless:true});
  try{
    const page=await browser.newPage({viewport:{width:1440,height:1080}}),errors=[];
    page.on('pageerror',e=>errors.push(e.message));
    await page.route('**/api/v1/visualization/requests?*',r=>r.fulfill({json:{stream_id:'controlled-video-test',cursor:0,requests:[]}}));
    await page.goto(base+'/app/maquina.html');await page.waitForFunction(()=>!!window.PrinterVideo);
    assert.equal(await page.locator('.machine-gear').count(),0);
    assert.equal(await page.locator('#printerVideo').count(),1);
    await page.waitForFunction(()=>{const v=document.getElementById('printerVideo');return v.readyState>=2&&!v.paused&&v.currentTime>0;});
    assert.equal(await page.locator('#printerStage').getAttribute('data-phase'),'preview');
    assert.match(await page.locator('#printerVideo').getAttribute('src'),/espera.mp4$/);
    assert.equal(await page.locator('#printerVideo').evaluate(v=>v.loop&&v.muted&&v.autoplay),true);
    assert.equal(await page.locator('#machineHistory button').count(),0);
    assert.match(await page.locator('#printerPhase').textContent(),/esperando actividad real/);
    await page.locator('#printerPause').click();assert.equal(await page.locator('#printerVideo').evaluate(v=>v.paused),true);
    await page.locator('#printerPause').click();await page.waitForFunction(()=>!document.getElementById('printerVideo').paused);
    await page.emulateMedia({reducedMotion:'reduce'});
    await page.waitForFunction(()=>document.getElementById('printerVideo').paused);
    await page.emulateMedia({reducedMotion:'no-preference'});
    await page.waitForFunction(()=>!document.getElementById('printerVideo').paused);
    await page.evaluate(()=>window.videoTestEntry=JsonMachine.start('POST','/api/v1/candidates',{id:'video-test'}));
    await page.waitForFunction(()=>{const v=document.getElementById('printerVideo');return v.readyState>=2&&!v.paused;});
    assert.match(await page.locator('#printerVideo').getAttribute('src'),/entrada.mp4$/);
    // Let the input clip really finish. No success response has been supplied.
    await page.waitForFunction(()=>document.getElementById('printerStage').dataset.phase==='espera',{},{timeout:12000});
    assert.equal(await page.locator('#printerVideo').evaluate(v=>v.loop),true);
    assert.match(await page.locator('#machineOutput').textContent(),/todavía no hay JSON/);
    assert.doesNotMatch(await page.locator('#printerVideo').getAttribute('src'),/salida/);
    await page.evaluate(()=>JsonMachine.finish(videoTestEntry,{status:201,ok:true,headers:new Headers({'X-Request-ID':'video-test'})},{id:'video-test'},'{"id":"video-test"}',true));
    await page.waitForFunction(()=>document.getElementById('printerStage').dataset.phase==='salida');
    await page.waitForFunction(()=>{const v=document.getElementById('printerVideo');return v.readyState>=2&&!v.paused;});
    assert.equal(await page.locator('#printerVideo').evaluate(v=>v.loop),false);
    assert.deepEqual(JSON.parse(await page.locator('#machineOutput').textContent()),{id:'video-test'});
    await page.waitForFunction(()=>document.getElementById('printerStage').dataset.phase==='complete',{},{timeout:12000});
    assert.equal(await page.locator('#printerVideo').evaluate(v=>v.paused),true);
    if(process.env.SCREENSHOT_DIR)await page.screenshot({path:path.join(process.env.SCREENSHOT_DIR,'visor-video-impresora.png')});
    await page.locator('#printerReplay').click();await page.waitForFunction(()=>document.getElementById('printerStage').dataset.phase==='entrada');
    await page.waitForFunction(()=>!document.getElementById('printerVideo').paused);
    await page.locator('#printerPause').click();assert.equal(await page.locator('#printerVideo').evaluate(v=>v.paused),true);
    // A rejection during playback must immediately prevent green output.
    await page.evaluate(()=>{const e=JsonMachine.start('POST','/api/v1/jobs',{});JsonMachine.finish(e,{status:422,ok:false,headers:new Headers()},{error:{code:'VALIDATION_ERROR'}},'{}',true);});
    assert.equal(await page.locator('#printerStage').getAttribute('data-phase'),'error');
    assert.equal(await page.locator('#printerVideo').getAttribute('src'),null);
    assert.equal(await page.locator('#printerError').isVisible(),true);
    await page.emulateMedia({reducedMotion:'reduce'});
    await page.evaluate(()=>{const e=JsonMachine.start('GET','/api/v1/jobs/a');JsonMachine.finish(e,{status:200,ok:true,headers:new Headers()},{id:'a'},'{"id":"a"}',true);});
    await page.waitForFunction(()=>document.getElementById('printerStage').dataset.phase==='complete');
    assert.equal(await page.locator('#printerVideo').evaluate(v=>v.paused),true);
    assert.ok(await page.locator('#printerVideo').evaluate(v=>v.currentTime>4.8));
    await page.setViewportSize({width:390,height:844});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false);
    assert.deepEqual(errors,[]);
    console.log('PASS: automatic muted loop on page load without requests; reduced motion; real MP4 input -> pending loop -> confirmed output; no output before success; error stops video; pause/replay; mobile.');
  }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});
