/* Real API + Neo4j. POST responses are held only to assert no premature animation output.
   Failure-path requests use browser interception and are explicitly marked as such. */
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert = require('node:assert/strict');
const {randomUUID} = require('node:crypto');
const {execFileSync} = require('node:child_process');
const path = require('node:path');
const fs = require('node:fs');
const base = process.env.BASE_URL || 'http://127.0.0.1:18000';
const prefix = 'test-neoconexion-' + randomUUID().replaceAll('-','') + '-';
const repo = path.resolve(__dirname, '../..');
const apiKey = process.env.API_KEY || '';
const company = {id: 'co-test', name: prefix+'Company', sector:'Pruebas',city:prefix+'City',color:'#2F6FB0'};
const candidate = {id:prefix+'candidate',name:'Ana Prueba',headline:'Backend',city:prefix+'City',years:3,
  skills:[prefix+'Python',prefix+'Docker'],workMode:'remote',salary:5000000};
const job = {id:prefix+'job',companyId:company.id,title:prefix+'Backend',city:prefix+'City',workMode:'remote',experience:3,
  requiredSkills:[prefix+'Python',prefix+'SQL'],desiredSkills:[prefix+'Docker'],salaryMin:4000000,salaryMax:6000000,
  contract:'Término indefinido',description:'Prueba real',postedAt:Date.now()};
const data = {companies:[company],candidates:[candidate],jobs:[job],applications:[],invites:[]};

(async()=>{
  const browser = await chromium.launch(process.env.BROWSER_CHANNEL ? {channel:process.env.BROWSER_CHANNEL,headless:true} : {headless:true});
  const context = await browser.newContext({viewport:{width:1440,height:1080}});
  const page = await context.newPage(); const errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  let release = ()=>{};
  let createdJobId = null;
  const api = context.request;
  const headers = apiKey ? {'X-API-Key':apiKey} : {};
  const json = async response=>{assert.equal(response.ok(),true,await response.text());return response.json();};
  const waitState = state=>page.waitForFunction(s=>document.getElementById('jsonMachine').dataset.state===s,state);
  const output = ()=>page.locator('#machineOutput').textContent().then(JSON.parse);
  try {
    await page.addInitScript(({data,base,apiKey})=>{
      localStorage.setItem('conecta-empleos-v1',JSON.stringify(data));
      localStorage.setItem('conecta-session','cand:'+data.candidates[0].id);
      localStorage.setItem('conecta-neoconexion-config',JSON.stringify({mode:'http',baseUrl:base}));
      sessionStorage.setItem('conecta-api-key',apiKey);
    },{data,base,apiKey});
    await json(await api.post(base+'/api/v1/jobs',{headers,data:{id:job.id,company:company.name,title:job.title,
      description:job.description,location:job.city,workMode:job.workMode,requiredExperience:3,
      requiredSkills:job.requiredSkills,desiredSkills:job.desiredSkills}}));
    await page.goto(base+'/app/');
    await page.waitForSelector('#sf');
    await page.locator('#nav [data-go="perfil"]').click();
    await page.locator('#p_name').fill('Ana Confirmada');
    const input=JSON.parse(await page.locator('#machineInput').textContent());
    assert.equal(input.name,'Ana Confirmada');
    assert.equal(await page.locator('#jsonMachine').getAttribute('data-state'),'draft');

    let captured, arrived;
    const received=new Promise(resolve=>arrived=resolve);
    const gate=new Promise(resolve=>release=resolve);
    const hold=async route=>{const response=await route.fetch();captured=await response.json();arrived();await gate;await route.fulfill({response});};
    await page.route('**/api/v1/candidates',hold);
    await page.locator('#pf [type=submit]').click();
    await received;
    assert.equal(await page.locator('#jsonMachine').getAttribute('data-state'),'pending');
    assert.equal(await page.locator('#pf [type=submit]').isDisabled(),true);
    assert.match(await page.locator('#machineOutput').textContent(),/todavía no hay JSON/);
    // The server already committed, but the UI has not received the held response.
    const persisted=await json(await api.get(base+'/api/v1/candidates/'+candidate.id,{headers}));
    assert.deepEqual(persisted,captured);
    release(); await waitState('success');
    await page.waitForFunction(()=>document.getElementById('p_msg').textContent.includes('Perfil confirmado'));
    assert.deepEqual(await output(),persisted);
    assert.match(await page.locator('#machineRequestId').textContent(),/X-Request-ID:/);
    await page.unroute('**/api/v1/candidates',hold);
    if(apiKey)assert.equal((await page.locator('#jsonMachine').textContent()).includes(apiKey),false);

    await page.locator('#nav [data-go="empleos"]').click();
    await page.waitForSelector('.jobcard'); await waitState('success');
    assert.equal((await output()).recommendations[0].matchScore,82.5);
    await page.locator(`[data-go="vacante"][data-id="${job.id}"]`).first().click();
    await page.waitForSelector('.fit-score'); await waitState('success');
    assert.equal((await output()).matchScore,82.5);
    assert.deepEqual((await output()).missingSkills,[prefix+'SQL']);

    await page.locator('#sess').selectOption('co:'+company.id);
    await page.locator('#nav [data-go="publicar"]').click();
    await page.locator('#v_title').fill(prefix+'Vacante publicada');
    await page.locator('#v_smin').fill('4000000');await page.locator('#v_smax').fill('6000000');
    await page.locator('#v_req').fill(prefix+'Python');await page.locator('#v_des').fill(prefix+'Docker');
    const newJobId=JSON.parse(await page.locator('#machineInput').textContent()).id;
    createdJobId=newJobId;
    const postResponse=page.waitForResponse(r=>r.request().method()==='POST'&&r.url().endsWith('/api/v1/jobs'));
    await page.locator('#jf [type=submit]').click();const post=await postResponse;assert.equal(post.status(),201);
    await waitState('success');
    const saved=await json(await api.get(base+'/api/v1/jobs/'+newJobId,{headers}));
    assert.deepEqual(await output(),saved);
    await page.locator('#v_title').fill(prefix+'Vacante actualizada');
    await page.locator('#jf [type=submit]').click(); await waitState('success');
    assert.match(await page.locator('#v_msg').textContent(),/HTTP 200/);
    assert.equal(await page.evaluate(()=>JSON.parse(localStorage.getItem('conecta-empleos-v1')).jobs.length),2);

    // Real 422 from Pydantic; must not overwrite the confirmed local or remote record.
    await page.locator('#v_title').fill('x'.repeat(201));
    await page.locator('#jf [type=submit]').click();await waitState('error');
    assert.equal((await output()).error.code,'VALIDATION_ERROR');
    assert.match(await page.locator('#v_msg').textContent(),/HTTP 422/);
    const unchanged=await json(await api.get(base+'/api/v1/jobs/'+newJobId,{headers}));
    assert.equal(unchanged.title,prefix+'Vacante actualizada');
    assert.equal(await page.evaluate(id=>JSON.parse(localStorage.getItem('conecta-empleos-v1')).jobs.find(j=>j.id===id).title,newJobId),unchanged.title);

    // Simulated transport outage: there must be no fabricated output JSON or local save.
    const offline=route=>route.abort('failed');await page.route('**/api/v1/jobs',offline);
    await page.locator('#v_title').fill('Cambio que no debe guardarse');
    await page.locator('#jf [type=submit]').click();await waitState('error');
    assert.match(await page.locator('#machineOutput').textContent(),/No se recibió respuesta HTTP/);
    assert.equal(await page.locator('#copyMachineOutput').isDisabled(),true);
    assert.equal(await page.evaluate(id=>JSON.parse(localStorage.getItem('conecta-empleos-v1')).jobs.find(j=>j.id===id).title,newJobId),unchanged.title);
    await page.unroute('**/api/v1/jobs',offline);

    await page.locator('#goIntegration').click();
    await page.route('**/api/v1/jobs',offline);await page.route('**/api/v1/candidates',offline);
    await page.locator('#i_sync').click();
    await page.waitForFunction(()=>document.getElementById('i_msg').textContent.includes('sin confirmar'));
    assert.match(await page.locator('#i_msg').textContent(),/0 de 3 registros confirmados/);
    await page.unroute('**/api/v1/jobs',offline);await page.unroute('**/api/v1/candidates',offline);
    await page.locator('#i_test').click();await waitState('success');
    assert.match(await page.locator('#i_msg').textContent(),/Conexión real confirmada/);
    await page.locator('#i_sync').click();
    await page.waitForFunction(()=>document.getElementById('i_msg').textContent.includes('3 de 3 registros confirmados'));
    await waitState('success');

    // Review a previous request without replacing it with a different response.
    await page.locator('#machineHistory button').filter({hasText:'POST /api/v1/jobs'}).last().click();
    assert.equal((await output()).id,newJobId);
    await page.evaluate(()=>window.scrollTo(0,0));
    if(process.env.SCREENSHOT_DIR){fs.mkdirSync(process.env.SCREENSHOT_DIR,{recursive:true});await page.screenshot({path:path.join(process.env.SCREENSHOT_DIR,'conecta-machine-desktop.png')});}
    await page.setViewportSize({width:390,height:844});
    if(process.env.SCREENSHOT_DIR)await page.screenshot({path:path.join(process.env.SCREENSHOT_DIR,'conecta-machine-mobile.png'),fullPage:true});
    if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1))console.log(await page.evaluate(()=>[...document.querySelectorAll('body *')].filter(e=>e.getBoundingClientRect().right>innerWidth+1).slice(0,12).map(e=>({tag:e.tagName,id:e.id,class:e.className,width:e.getBoundingClientRect().width,right:e.getBoundingClientRect().right}))));
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false,'Mobile overflow');
    await page.emulateMedia({reducedMotion:'reduce'});
    assert.equal(await page.locator('.machine-gear').first().evaluate(e=>getComputedStyle(e).animationName),'none');
    assert.deepEqual(errors,[]);
    console.log('PASS: JSON preview; real POST -> Neo4j verified before animation output; exact response; ranking/diagnosis 82.5; publish/update without duplicates; real 422; simulated network errors; accurate sync counts; request history; mobile and reduced motion.');
  } finally {
    release(); await browser.close();
    // Only our UUID-prefixed fixture records are removed; never clear the database.
    const docker=process.env.DOCKER_EXE || 'docker';
    assert.ok(createdJobId===null || /^j-[a-f0-9-]+$/.test(createdJobId));
    execFileSync(docker,['compose','exec','-T','api','python','-c',
      `from app.core.neo4j_driver import get_driver; from app.repositories.test_support import cleanup_test_data; driver=get_driver(); session=driver.session(); session.run('MATCH (j:Job {id: $id}) WHERE j.title STARTS WITH $prefix DETACH DELETE j', id='${createdJobId||''}', prefix='${prefix}').consume(); session.close(); cleanup_test_data(driver, '${prefix}')`],{cwd:repo,stdio:'pipe'});
  }
})().catch(e=>{console.error(e);process.exit(1)});
