// Usage: node verify_ui.cjs [absolute inline-fragment path]
// No HTML deliverable is created. Omit the argument to test the committed JS/CSS/data.
const fs=require('fs'),path=require('path'),crypto=require('crypto'),{chromium}=require('playwright');
const root=__dirname,data=JSON.parse(fs.readFileSync(path.join(root,'chart-data.json'),'utf8'));
const css=fs.readFileSync(path.join(root,'workspace.css'),'utf8'),js=fs.readFileSync(path.join(root,'workspace.js'),'utf8');
const source=`<main></main><style>${css}</style><script id="cw-data" type="application/json">${JSON.stringify(data)}</script><script>${js}</script>`;
const fragment=process.argv[2]?fs.readFileSync(process.argv[2],'utf8'):source;
const checks=[],errors=[],iterationsFile=path.join(root,'test-runs.json');
const mock=`window.Tweak=class{constructor(o){this.redraw=o.onChange}addSelect(obj,key){window.uiDesign=window.uiDesign||{};window.uiDesign[key]=value=>{obj[key]=value;this.redraw()}}addToggle(obj,key){this.addSelect(obj,key)}};window.openai={widgetState:null,setWidgetState:async s=>{window.savedState=s}};`;
function assert(v,msg){if(!v)throw Error(msg);}
async function cutoff(page,n){await page.locator('#cw-replay').evaluate((el,v)=>{el.value=v;el.dispatchEvent(new Event('input',{bubbles:true}));},String(n));}
async function geometry(page){return page.evaluate(()=>{
 const root=document.getElementById('cgb-workspace'),boundary=root.getBoundingClientRect(),texts=[...root.querySelectorAll('svg text')].filter(el=>el.getBoundingClientRect().width),clipped=[];
 for(const t of texts){const b=t.getBoundingClientRect();if(b.left<boundary.left-1||b.right>boundary.right+1)clipped.push(t.textContent);}
 const overlap=[];for(let i=0;i<texts.length;i++)for(let j=i+1;j<texts.length;j++){const a=texts[i],b=texts[j];if(a.ownerSVGElement!==b.ownerSVGElement)continue;const ar=a.getBoundingClientRect(),br=b.getBoundingClientRect();if(Math.min(ar.right,br.right)-Math.max(ar.left,br.left)>1&&Math.min(ar.bottom,br.bottom)-Math.max(ar.top,br.top)>1)overlap.push([a.textContent,b.textContent]);}
 return {overflow:document.documentElement.scrollWidth>innerWidth,clipped,overlap};
});}
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.BROWSER_EXECUTABLE});let failure=null;
 try{
  for(const scheme of ['dark','light'])for(const width of [1440,1024,736,390,360,320]){
   const page=await browser.newPage({viewport:{width,height:1100},colorScheme:scheme});page.on('pageerror',e=>errors.push(e.message));
   await page.setContent(`<style>html{color-scheme:${scheme}}body{margin:0}</style><script>${mock}</script><script src="https://cdn.jsdelivr.net/npm/d3@7.9.0/dist/d3.min.js"></script>${fragment.replace('<script src="https://cdn.jsdelivr.net/npm/d3@7.9.0/dist/d3.min.js"></script>','')}`,{waitUntil:'load'});
   await page.waitForFunction(()=>document.querySelectorAll('[data-layer="candles"] [data-time]').length>0);
   const g=await geometry(page);assert(!g.overflow&&!g.clipped.length&&!g.overlap.length,'Initial geometry '+JSON.stringify({scheme,width,...g}));
   if(scheme==='dark'&&width===1024)await page.locator('#cgb-workspace').screenshot({path:path.join(root,'desktop-dark.png')});
   if(scheme==='light'&&width===360)await page.locator('#cgb-workspace').screenshot({path:path.join(root,'mobile-light.png')});
   await cutoff(page,29);
   for(const horizon of [60,120,240]){await page.locator('#cw-horizon').selectOption(String(horizon));const f=data.forecasts.find(f=>f.time===data.bars[29].time&&f.horizon_minutes===horizon);assert(Number(await page.locator('#cw-forecast').getAttribute('data-pup'))===f.p_up,'Saved probability mismatch');assert((await page.locator('#cw-forecast-label').textContent()).includes(horizon/60+'h'),'Horizon label mismatch');}
   for(const n of [0,4,5,6,7,29,43,95]){
    await cutoff(page,n);const time=data.bars[n].time;
    const rendered=await page.locator('[data-time]').evaluateAll(es=>es.map(e=>Number(e.dataset.time)));assert(rendered.every(t=>t<=time),'Future object rendered');
    assert(await page.locator('[data-layer="opening-range"]').count()===(n<5?0:2),'Range drawn before availability');
    assert(await page.locator('[data-layer="events"] [data-time]').count()===data.events.filter(e=>e.time<=time).length,'Event timing or spam');
    const domain=await page.locator('#cw-price-chart').getAttribute('data-price-max');const received=data.bars.slice(0,n+1).flatMap(b=>[b.low,b.high,b.vwap]);if(n>=5)received.push(data.opening_range.low,data.opening_range.high);const extent=Math.max(...received)-Math.min(...received),expected=Math.max(...received)+Math.max(extent*.11,.025);assert(Math.abs(+domain-expected)<1e-9,'Price scale includes future');
    const stateGeometry=await geometry(page);assert(!stateGeometry.overflow&&!stateGeometry.clipped.length&&!stateGeometry.overlap.length,'Replay geometry '+JSON.stringify({scheme,width,n,...stateGeometry}));
   }
   assert((await page.locator('#cw-forecast').textContent()).includes('session close'),'Late horizon not marked unavailable');
   await cutoff(page,43);await page.locator('#cw-horizon').selectOption('60');await page.locator('#cw-inspect').selectOption('29');
   assert(await page.locator('#cw-forecast').getAttribute('data-origin')===String(data.bars[29].time),'Cursor/readout clock mismatch');assert((await page.locator('#cw-selected-label').textContent()).includes('PINNED HISTORY'),'Historical selection not explicit');assert((await page.locator('#cw-replay-time').textContent()).includes('11:40'),'Inspect moved replay cutoff');
   const positions=await page.locator('#cw-price-chart [data-layer="candles"] [data-time]').evaluateAll(es=>es.map(e=>({time:+e.dataset.time,x:e.querySelector('line').getBoundingClientRect().x})));
   const a=positions[29],b=positions[30],hitBox=await page.locator('#cw-price-chart [data-chart-hit]').boundingBox();await page.mouse.move(a.x+(b.x-a.x)*.8,hitBox.y+hitBox.height/2);
   assert(await page.locator('#cw-forecast').getAttribute('data-origin')===String(a.time),'Between-bar cursor selected future completed bar');await page.mouse.move(0,0);
   const guides=await page.locator('[data-chart-hover-guide]').evaluateAll(es=>es.map(e=>Number(e.getAttribute('x1'))));assert(new Set(guides).size===1,'Shared crosshair misaligned');
   await page.locator('#cw-details summary').click();await page.locator('#cw-event').selectOption('1');assert((await page.locator('#cw-selected-label').textContent()).includes('08:40'),'Held event backdated');assert((await page.locator('#cw-event-detail').textContent()).includes('second completed close'),'Event lacks exact meaning');
   await page.locator('#cw-latest').click();await page.evaluate(()=>window.uiDesign.health('stale'));assert((await page.locator('#cw-forecast').textContent()).includes('withheld'),'Stale forecast shown as current');assert(await page.locator('#cw-forecast').getAttribute('data-pup')==='','Stale model probability remains actionable');
   if(scheme==='dark'&&width===1024)await page.locator('#cgb-workspace').screenshot({path:path.join(root,'stale-dark.png')});
   await page.locator('#cw-inspect').selectOption('29');assert(await page.locator('#cw-forecast').getAttribute('data-origin')===String(data.bars[29].time),'Staleness destroyed historical forecast');
   await page.evaluate(()=>window.uiDesign.health('normal'));await page.locator('#cw-range-toggle').click();assert(await page.locator('[data-layer="opening-range"]').count()===0,'Range toggle inactive');await page.locator('#cw-range-toggle').click();await page.locator('#cw-vwap-toggle').click();assert(await page.locator('[data-layer="vwap"]').count()===0,'VWAP toggle inactive');await page.locator('#cw-vwap-toggle').click();
   await page.evaluate(()=>window.uiDesign.flow(false));assert(!(await page.locator('#cw-flow-pane').isVisible()),'Flow toggle inactive');await page.evaluate(()=>window.uiDesign.flow(true));
   await page.locator('#cw-replay').focus();await page.keyboard.press('Home');assert(await page.locator('[data-layer="candles"] [data-time]').count()===1,'Keyboard Home failed');await page.keyboard.press('ArrowRight');assert(await page.locator('[data-layer="candles"] [data-time]').count()===2,'Keyboard step failed');
   await cutoff(page,29);await page.locator('#cw-horizon').selectOption('120');const saved=await page.evaluate(()=>window.savedState.modelContent);assert(saved.horizon===120&&saved.cutoff===29,'Widget state not persisted');
   const openG=await geometry(page);assert(!openG.overflow&&!openG.clipped.length&&!openG.overlap.length,'Open details geometry '+JSON.stringify({scheme,width,...openG}));
   checks.push({scheme,width,status:'PASS',horizon_checks:3,replay_cutoffs:8,causal_levels_events:true,shared_history_clock:true,stale_and_history:true,keyboard:true,persistence:true,geometry:true});await page.close();
  }
  // Coarse-pointer targets and touch pinning: actual touch input, no hover dependency.
  const page=await browser.newPage({viewport:{width:360,height:1000},hasTouch:true,isMobile:true,colorScheme:'dark'});
  page.on('pageerror',e=>errors.push(e.message));
  await page.setContent(`<meta name="viewport" content="width=device-width, initial-scale=1"><style>html{color-scheme:dark}body{margin:0}</style><script>${mock}</script><script src="https://cdn.jsdelivr.net/npm/d3@7.9.0/dist/d3.min.js"></script>${source}`,{waitUntil:'load'});
  await page.waitForFunction(()=>document.querySelectorAll('[data-layer="candles"] [data-time]').length>0);
  const targets=await page.locator('button,select,summary').evaluateAll(es=>es.filter(e=>e.getBoundingClientRect().width).map(e=>({text:e.textContent,h:e.getBoundingClientRect().height})));assert(targets.every(t=>t.h>=43.9),'Touch targets '+JSON.stringify(targets));
  const box=await page.locator('#cw-price-chart [data-chart-hit]').boundingBox();await page.touchscreen.tap(box.x+box.width*.4,box.y+box.height*.6);assert((await page.locator('#cw-selected-label').textContent()).includes('PINNED HISTORY'),'Touch did not pin history');
  checks.push({status:'PASS',width:360,coarse_targets:true,touch_pinning:true,committed_source:true});await page.close();
  // Deliberate UI failure fixtures; these do not change the saved market/model data.
  for(const condition of ['missing-flow','zero-flow','neutral-model','missing-forecast']){
   const fixture=structuredClone(data),bar=fixture.bars[43],model=fixture.forecasts.find(f=>f.time===bar.time&&f.horizon_minutes===60);
   if(condition==='missing-flow'){bar.flow_available=false;bar.flow_pressure=null;}
   if(condition==='zero-flow')bar.flow_pressure=0;
   if(condition==='neutral-model'){model.p_up=.1;model.p_down=.1;model.p_neutral=.8;}
   if(condition==='missing-forecast')fixture.forecasts=fixture.forecasts.filter(f=>!(f.time===bar.time&&f.horizon_minutes===60));
   const p=await browser.newPage({viewport:{width:736,height:1000}});p.on('pageerror',e=>errors.push(e.message));
   await p.setContent(`<main></main><style>${css}</style><script>${mock}</script><script src="https://cdn.jsdelivr.net/npm/d3@7.9.0/dist/d3.min.js"></script><script id="cw-data" type="application/json">${JSON.stringify(fixture)}</script><script>${js}</script>`,{waitUntil:'load'});
   const flow=await p.locator('#cw-flow-value').textContent(),forecast=await p.locator('#cw-forecast').textContent();
   if(condition==='missing-flow'){assert(flow==='Unavailable','Missing flow shown as zero');assert(await p.locator(`#cw-flow-chart [data-missing-time="${bar.time}"]`).count()===1,'Missing flow not shown as gap');}
   if(condition==='zero-flow'){assert(flow==='0.000','Genuine zero not preserved');assert(await p.locator(`#cw-flow-chart [data-time="${bar.time}"]`).getAttribute('data-value')==='0','Zero drawn as missing');}
   if(condition==='neutral-model')assert(forecast.includes('Neutral 80%')&&(await p.locator('#cw-model-value').textContent())==='0.0 pp','Neutral distribution misrepresented');
   if(condition==='missing-forecast')assert(forecast==='No saved forecast at this time.'&&(await p.locator('#cw-forecast').getAttribute('data-origin'))==='','Missing forecast silently carried or mislabelled');
   checks.push({status:'PASS',fixture:condition,original_data_modified:false});await p.close();
  }
  assert(!errors.length,'Browser errors '+errors.join(';'));
 }catch(e){failure=e.message;}finally{await browser.close();}
 const run={time:new Date().toISOString(),status:failure?'FAIL':'PASS',failure,completed_cases:checks.length,fragment_sha256:crypto.createHash('sha256').update(fragment).digest('hex')};
 const history=fs.existsSync(iterationsFile)?JSON.parse(fs.readFileSync(iterationsFile,'utf8')):[];history.push(run);fs.writeFileSync(iterationsFile,JSON.stringify(history,null,2)+'\n');
 fs.writeFileSync(path.join(root,'ui-verification.json'),JSON.stringify({...run,browser_errors:errors,checks},null,2)+'\n');console.log(JSON.stringify(run));if(failure)process.exitCode=1;
})();
