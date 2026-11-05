/* Two independent pages: exact supplied vacancy HTML and real server observer. */
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict');
const {randomUUID,createHash}=require('node:crypto');
const {execFileSync}=require('node:child_process');
const path=require('node:path'),fs=require('node:fs');
const base=process.env.BASE_URL||'http://127.0.0.1:18000',apiKey=process.env.API_KEY||'';
const prefix='test-neoconexion-'+randomUUID().replaceAll('-','')+'-',repo=path.resolve(__dirname,'../..');
const candidate={id:prefix+'candidate',name:'Ana Prueba',headline:'Backend',city:prefix+'City',years:3,skills:[prefix+'Python',prefix+'Docker'],workMode:'remote',salary:5000000};
const company={id:'co-test',name:prefix+'Company',sector:'Pruebas',city:prefix+'City',color:'#2F6FB0'};
const job={id:prefix+'job',companyId:company.id,title:prefix+'Backend',city:prefix+'City',workMode:'remote',experience:3,requiredSkills:[prefix+'Python',prefix+'SQL'],desiredSkills:[prefix+'Docker'],salaryMin:4000000,salaryMax:6000000,contract:'Término indefinido',description:'Prueba real',postedAt:Date.now()};
const data={companies:[company],candidates:[candidate],jobs:[job],applications:[],invites:[]};
(async()=>{
  const browser=await chromium.launch(process.env.BROWSER_CHANNEL?{channel:process.env.BROWSER_CHANNEL,headless:true}:{headless:true});
  const context=await browser.newContext({viewport:{width:1440,height:1080}});
  const original=await context.newPage(),viewer=await context.newPage(),errors=[];
  for(const page of [original,viewer])page.on('pageerror',e=>errors.push(e.message));
  const api=context.request,headers=apiKey?{'X-API-Key':apiKey}:{};
  let createdJobId=null;
  const get=async route=>{const r=await api.get(base+route,{headers});assert.equal(r.ok(),true,await r.text());return r.json();};
  try{
    const bytes=await(await api.get(base+'/app/')).body();
    assert.equal(createHash('sha256').update(bytes).digest('hex'),'0177c4ba32f5d6e3acca56a23bbdd2d6b6814ab01d786698603e20bc29462126');
    await context.addInitScript(({data,base,apiKey})=>{
      localStorage.setItem('conecta-empleos-v1',JSON.stringify(data));localStorage.setItem('conecta-session','cand:'+data.candidates[0].id);
      localStorage.setItem('conecta-neoconexion-config',JSON.stringify({mode:'http',baseUrl:base,apiKey}));sessionStorage.setItem('conecta-observer-key',apiKey);
    },{data,base,apiKey});
    assert.equal((await api.post(base+'/api/v1/candidates',{headers,data:{id:candidate.id,name:candidate.name,location:candidate.city,yearsOfExperience:3,skills:candidate.skills,preferredWorkMode:'remote'}})).status(),201);
    assert.equal((await api.post(base+'/api/v1/jobs',{headers,data:{id:job.id,company:company.name,title:job.title,location:job.city,workMode:'remote',requiredExperience:3,requiredSkills:job.requiredSkills,desiredSkills:job.desiredSkills}})).status(),201);
    await original.goto(base+'/app/');await original.waitForSelector('#sf');
    assert.equal(await original.locator('#jsonMachine').count(),0);
    await viewer.goto(base+'/app/maquina.html');await viewer.waitForFunction(()=>document.getElementById('connection').textContent.startsWith('Conectado'));
    await original.locator('#nav [data-go="perfil"]').click();await original.locator('#p_name').fill('Ana Desde Original');
    await original.locator('#pf [type=submit]').click();
    await viewer.waitForFunction(()=>{try{return JSON.parse(document.getElementById('machineOutput').textContent).name==='Ana Desde Original';}catch{return false;}});
    let output=JSON.parse(await viewer.locator('#machineOutput').textContent());
    assert.deepEqual(output,await get('/api/v1/candidates/'+candidate.id));
    assert.match(await viewer.locator('#machineRequestId').textContent(),/X-Request-ID:/);

    await original.locator('#p_name').fill('x'.repeat(201));await original.locator('#pf [type=submit]').click();
    await viewer.waitForFunction(()=>{try{return JSON.parse(document.getElementById('machineOutput').textContent).error.code==='VALIDATION_ERROR';}catch{return false;}});
    assert.equal((await get('/api/v1/candidates/'+candidate.id)).name,'Ana Desde Original');

    // Transport failure before reaching the API must not fabricate a server trace.
    const before=(await get('/api/v1/visualization/requests')).cursor;
    const offline=r=>r.abort('failed');await original.route('**/api/v1/candidates',offline);
    await original.locator('#p_name').fill('Cambio sin conexión');await original.locator('#pf [type=submit]').click();
    await original.waitForFunction(()=>document.getElementById('p_msg').textContent.includes('no pudimos'));
    assert.equal((await get('/api/v1/visualization/requests?after='+before)).requests.length,0);
    await original.unroute('**/api/v1/candidates',offline);

    await original.locator('#sess').selectOption('co:'+company.id);await original.locator('#nav [data-go="publicar"]').click();
    await original.locator('#v_title').fill(prefix+'Publicado');await original.locator('#v_smin').fill('4000000');await original.locator('#v_smax').fill('6000000');await original.locator('#v_req').fill(prefix+'Python');
    const pending=original.waitForResponse(r=>r.request().method()==='POST'&&r.url().endsWith('/api/v1/jobs'));
    await original.locator('#jf [type=submit]').click();const saved=await pending;assert.equal(saved.status(),201);createdJobId=(await saved.json()).id;
    await viewer.waitForFunction(()=>[...document.querySelectorAll('#machineHistory button')].filter(b=>b.textContent.includes('POST /api/v1/jobs')).length>=2);
    await viewer.locator('#machineHistory button').filter({hasText:'POST /api/v1/jobs'}).first().click();
    output=JSON.parse(await viewer.locator('#machineOutput').textContent());assert.equal(output.id,createdJobId);
    assert.deepEqual(output,await get('/api/v1/jobs/'+createdJobId));
    if(apiKey)assert.equal((await viewer.locator('#jsonMachine').textContent()).includes(apiKey),false);
    const activity=await get('/api/v1/visualization/requests');assert.ok(activity.requests.every(r=>!r.path.includes('visualization')));
    await viewer.evaluate(()=>window.scrollTo(0,0));
    if(process.env.SCREENSHOT_DIR){fs.mkdirSync(process.env.SCREENSHOT_DIR,{recursive:true});await viewer.screenshot({path:path.join(process.env.SCREENSHOT_DIR,'maquina-independiente.png')});}
    await viewer.setViewportSize({width:390,height:844});assert.equal(await viewer.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false);
    await viewer.emulateMedia({reducedMotion:'reduce'});
    await viewer.waitForFunction(()=>document.getElementById('printerStage').dataset.motion==='reduced');
    assert.equal(await viewer.locator('#printerVideo').evaluate(e=>e.paused),true);
    assert.deepEqual(errors,[]);
    console.log('PASS: exact original HTML SHA-256; two pages; real profile/job persistence from server; real 422; no fabricated trace on network failure; no API Key leakage; mobile and reduced motion.');
  }finally{
    await browser.close();assert.ok(createdJobId===null||/^j-[a-z0-9-]+$/.test(createdJobId));
    execFileSync(process.env.DOCKER_EXE||'docker',['compose','exec','-T','api','python','-c',`from app.core.neo4j_driver import get_driver; from app.repositories.test_support import cleanup_test_data; d=get_driver(); s=d.session(); s.run('MATCH (j:Job {id: $id}) WHERE j.title STARTS WITH $prefix DETACH DELETE j',id='${createdJobId||''}',prefix='${prefix}').consume(); s.close(); cleanup_test_data(d,'${prefix}')`],{cwd:repo,stdio:'pipe'});
  }
})().catch(e=>{console.error(e);process.exit(1)});
