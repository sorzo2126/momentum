// Local verification only. Market-bearing outputs stay under ../private/.
// Usage: node verify_ui.cjs [absolute task-owned inline fragment]
const fs=require('fs'),path=require('path'),crypto=require('crypto'),{chromium}=require('playwright');
const root=__dirname,privateDir=path.resolve(root,'../private'),dataPath=path.join(privateDir,'chart-data.json');
const data=JSON.parse(fs.readFileSync(dataPath,'utf8'));
const css=fs.readFileSync(path.join(root,'workspace.css'),'utf8'),js=fs.readFileSync(path.join(root,'workspace.js'),'utf8');
const source=d=>`<main></main><style>${css}</style><script id="sw-data" type="application/json">${JSON.stringify(d).replace(/</g,'\\u003c')}</script><script>${js}</script>`;
const supplied=process.argv[2]?fs.readFileSync(process.argv[2],'utf8'):null;
const checks=[],errors=[],iterationsFile=path.join(privateDir,'ui-test-runs.json');
const mock=`window.Tweak=class{constructor(o){this.redraw=o.onChange}addSelect(obj,key){window.uiDesign=window.uiDesign||{};window.uiDesign[key]=value=>{obj[key]=value;this.redraw()}}addToggle(obj,key){this.addSelect(obj,key)}};window.openai={widgetState:null,setWidgetState:async s=>{window.savedState=s}};`;
function assert(v,msg){if(!v)throw Error(msg);}
async function cutoff(page,n){await page.locator('#sw-replay').evaluate((el,v)=>{el.value=v;el.dispatchEvent(new Event('input',{bubbles:true}));},String(n));}
async function geometry(page){return page.evaluate(()=>{
 const r=document.getElementById('spy-workspace'),boundary=r.getBoundingClientRect(),texts=[...r.querySelectorAll('svg text')].filter(el=>el.getBoundingClientRect().width),clipped=[],overlap=[];
 for(const t of texts){const b=t.getBoundingClientRect();if(b.left<boundary.left-1||b.right>boundary.right+1)clipped.push(t.textContent);}
 for(let i=0;i<texts.length;i++)for(let j=i+1;j<texts.length;j++){const a=texts[i],b=texts[j];if(a.ownerSVGElement!==b.ownerSVGElement)continue;const x=a.getBoundingClientRect(),y=b.getBoundingClientRect();if(Math.min(x.right,y.right)-Math.max(x.left,y.left)>1&&Math.min(x.bottom,y.bottom)-Math.max(x.top,y.top)>1)overlap.push([a.textContent,b.textContent]);}
 return {overflow:document.documentElement.scrollWidth>innerWidth,clipped,overlap};
});}
async function open(page,scheme,fragment){page.on('pageerror',e=>errors.push(e.message));await page.setContent(`<meta name="viewport" content="width=device-width, initial-scale=1"><style>html{color-scheme:${scheme}}body{margin:0}</style><script>${mock}</script><script src="https://cdn.jsdelivr.net/npm/d3@7.9.0/dist/d3.min.js"></script>${fragment.replace('<script src="https://cdn.jsdelivr.net/npm/d3@7.9.0/dist/d3.min.js"></script>','')}`,{waitUntil:'load'});await page.waitForFunction(()=>document.querySelectorAll('[data-layer="candles"] [data-time]').length>0);}
(async()=>{
 assert(data.meta.instrument==='SPY'&&data.meta.synthetic===false,'Not real SPY study');
 assert(data.bars.every(b=>b.time===b.start_time+data.meta.bar_minutes*60000),'Bar end differs from documented start plus interval');
 assert(data.bars.every(b=>b.flow_available===false&&b.flow_pressure==null&&b.spread_ticks==null),'OHLCV invents aggressor flow or spread');
 assert(data.forecasts.every(f=>Math.abs(f.p_up+f.p_neutral+f.p_down-1)<1e-7),'Probabilities do not sum to one');
 const baseline=data.meta.default_cutoff_index??29,end=data.bars.length-1,orIndex=data.bars.findIndex(b=>b.time>=data.opening_range.known_at_time);
 const browser=await chromium.launch({headless:true,executablePath:process.env.BROWSER_EXECUTABLE});let failure=null;
 try{
  for(const scheme of (process.env.SPY_UI_TOUCH_ONLY?[]:['dark','light']))for(const width of [1440,1024,736,390,360,320]){
   const page=await browser.newPage({viewport:{width,height:1100},colorScheme:scheme});await open(page,scheme,supplied??source(data));
   assert(await page.locator('[data-layer="candles"] [data-time]').count()===baseline+1,'Wrong default cutoff');
   assert((await page.locator('#sw-session').textContent()).includes(data.meta.session),'Hardcoded session');
   assert((await page.locator('#sw-flow-value').textContent()).includes('aggressor flow unavailable'),'Unavailable flow hidden');
   assert((await page.locator('#sw-vwap-toggle').textContent()).includes('Bar VWAP proxy'),'Proxy relabelled tape VWAP');
   assert(!/CGB|SYNTHETIC|SIM_|19 Feb 2025/.test(await page.locator('#spy-workspace').textContent()),'Old product/data label leaked');
   const g=await geometry(page);assert(!g.overflow&&!g.clipped.length&&!g.overlap.length,'Initial geometry '+JSON.stringify({scheme,width,...g}));
   if(scheme==='dark'&&width===1024)await page.locator('#spy-workspace').screenshot({path:path.join(privateDir,'ui-desktop-dark.png')});
   if(scheme==='light'&&width===360)await page.locator('#spy-workspace').screenshot({path:path.join(privateDir,'ui-mobile-light.png')});
   for(const horizon of [60,120,240]){await page.locator('#sw-horizon').selectOption(String(horizon));const f=data.forecasts.find(f=>f.time===data.bars[baseline].time&&f.horizon_minutes===horizon);if(f){assert(Number(await page.locator('#sw-forecast').getAttribute('data-pup'))===f.p_up,'Saved probability mismatch');}else assert(await page.locator('#sw-forecast').getAttribute('data-origin')==='','Missing horizon invented');}
   const cutoffs=[...new Set([0,Math.max(0,orIndex-1),orIndex,orIndex+1,baseline,Math.min(baseline+12,end),end])];
   for(const n of cutoffs){
    await cutoff(page,n);const time=data.bars[n].time;
    const rendered=await page.locator('[data-time]').evaluateAll(es=>es.map(e=>Number(e.dataset.time)));assert(rendered.every(t=>t<=time),'Future object rendered');
    assert(await page.locator('[data-layer="opening-range"]').count()===(time<data.opening_range.known_at_time?0:2),'Range availability violated');
    assert(await page.locator('[data-layer="events"] [data-time]').count()===data.events.filter(e=>e.time<=time).length,'Event timing mismatch');
    const received=data.bars.slice(0,n+1).flatMap(b=>[b.low,b.high,b.vwap]).filter(Number.isFinite);if(time>=data.opening_range.known_at_time)received.push(data.opening_range.low,data.opening_range.high);const expected=Math.max(...received)+Math.max((Math.max(...received)-Math.min(...received))*.11,.025);
    assert(Math.abs(+(await page.locator('#sw-price-chart').getAttribute('data-price-max'))-expected)<1e-9,'Price scale contains future');
    const values=await page.locator('#sw-flow-chart [data-value]').evaluateAll(es=>es.map(e=>({v:+e.dataset.value,fill:e.getAttribute('fill')})));assert(values.every(v=>v.v>=0&&v.fill==='var(--sw-muted)'),'Volume inferred aggressor sign');
    const gg=await geometry(page);assert(!gg.overflow&&!gg.clipped.length&&!gg.overlap.length,'Replay geometry '+JSON.stringify({scheme,width,n,...gg}));
   }
   assert((await page.locator('#sw-forecast').textContent()).includes('session close'),'Late horizon not unavailable');
   const later=Math.min(baseline+12,end);await cutoff(page,later);await page.locator('#sw-horizon').selectOption('60');await page.locator('#sw-inspect').selectOption(String(baseline));
   const f=data.forecasts.find(f=>f.time===data.bars[baseline].time&&f.horizon_minutes===60);assert(f,'Baseline primary forecast absent');assert(await page.locator('#sw-forecast').getAttribute('data-origin')===String(f.time),'Historical readout mismatch');assert((await page.locator('#sw-selected-label').textContent()).includes('PINNED HISTORY'),'Historical selection undisclosed');
   const pos=await page.locator('#sw-price-chart [data-layer="candles"] [data-time]').evaluateAll(es=>es.map(e=>({time:+e.dataset.time,x:e.querySelector('line').getBoundingClientRect().x}))),a=pos[baseline],b=pos[baseline+1],hit=await page.locator('#sw-price-chart [data-chart-hit]').boundingBox();
   await page.mouse.move(a.x+(b.x-a.x)*.8,hit.y+hit.height/2);assert(await page.locator('#sw-forecast').getAttribute('data-origin')===String(a.time),'Between-bar cursor chose future');await page.mouse.move(0,0);
   const guides=await page.locator('[data-chart-hover-guide]').evaluateAll(es=>es.map(e=>Number(e.getAttribute('x1'))));assert(new Set(guides).size===1,'Crosshair mismatch');
   await page.locator('#sw-details summary').click();assert((await page.locator('#sw-risk').textContent()).includes('Unavailable in OHLCV'),'Spread fabricated');
   const known=data.events.filter(e=>e.time<=data.bars[later].time);if(known.length){await page.locator('#sw-event').selectOption('0');assert(await page.locator('#sw-readout').getAttribute('data-selected-time')===String(known[0].time),'Event selection wrong clock');}
   await page.locator('#sw-latest').click();await page.evaluate(()=>window.uiDesign.health('stale'));assert((await page.locator('#sw-forecast').textContent()).includes('withheld'),'Stale forecast presented current');assert(await page.locator('#sw-forecast').getAttribute('data-pup')==='','Stale probability retained');
   await page.locator('#sw-inspect').selectOption(String(baseline));assert(await page.locator('#sw-forecast').getAttribute('data-origin')===String(f.time),'History erased by current staleness');await page.evaluate(()=>window.uiDesign.health('normal'));
   await page.locator('#sw-range-toggle').click();assert(await page.locator('[data-layer="opening-range"]').count()===0,'Range toggle failed');await page.locator('#sw-range-toggle').click();await page.locator('#sw-vwap-toggle').click();assert(await page.locator('[data-layer="vwap"]').count()===0,'Proxy toggle failed');await page.locator('#sw-vwap-toggle').click();
   await page.evaluate(()=>window.uiDesign.volume(false));assert(!(await page.locator('#sw-flow-pane').isVisible()),'Volume toggle failed');await page.evaluate(()=>window.uiDesign.volume(true));
   await page.locator('#sw-replay').focus();await page.keyboard.press('Home');assert(await page.locator('[data-layer="candles"] [data-time]').count()===1,'Keyboard Home failed');await page.keyboard.press('ArrowRight');assert(await page.locator('[data-layer="candles"] [data-time]').count()===2,'Keyboard step failed');
   await cutoff(page,baseline);await page.locator('#sw-horizon').selectOption('120');const saved=await page.evaluate(()=>window.savedState.modelContent);assert(saved.chart==='spy-replay-v1'&&saved.horizon===120&&saved.cutoff===baseline,'Incorrect widget state');
   const gg=await geometry(page);assert(!gg.overflow&&!gg.clipped.length&&!gg.overlap.length,'Details geometry '+JSON.stringify({scheme,width,...gg}));
   checks.push({scheme,width,status:'PASS',cutoffs:cutoffs.length,exact_probabilities:true,causal_levels:true,no_future_scale:true,unsigned_volume:true,unavailable_flow:true,shared_cursor:true,keyboard:true,persistence:true,geometry:true});await page.close();
  }
  const page=await browser.newPage({viewport:{width:360,height:1100},hasTouch:true,isMobile:true,colorScheme:'dark'});await open(page,'dark',source(data));
  const targets=await page.locator('button,select,summary').evaluateAll(es=>es.filter(e=>e.getBoundingClientRect().width).map(e=>e.getBoundingClientRect().height));assert(targets.every(h=>h>=43.9),'Touch target too small');
  await page.locator('#spy-workspace').screenshot({path:path.join(privateDir,'ui-touch-dark.png')});
  const box=await page.locator('#sw-price-chart [data-chart-hit]').boundingBox();assert(box,'Touch chart hit surface has no visible bounding box');await page.touchscreen.tap(box.x+box.width*.4,box.y+box.height*.6);assert((await page.locator('#sw-selected-label').textContent()).includes('PINNED HISTORY'),'Touch did not pin');checks.push({status:'PASS',touch:true,coarse_targets:true});await page.close();
  for(const condition of ['missing-volume','zero-volume','neutral-model','missing-forecast']){
   const fixture=structuredClone(data),bar=fixture.bars[baseline],model=fixture.forecasts.find(f=>f.time===bar.time&&f.horizon_minutes===60);
   if(condition==='missing-volume')bar.volume=null;if(condition==='zero-volume')bar.volume=0;if(condition==='neutral-model'){model.p_up=.1;model.p_down=.1;model.p_neutral=.8;}if(condition==='missing-forecast')fixture.forecasts=fixture.forecasts.filter(f=>!(f.time===bar.time&&f.horizon_minutes===60));
   const p=await browser.newPage({viewport:{width:736,height:1100}});await open(p,'light',source(fixture));
   if(condition==='missing-volume'){assert((await p.locator('#sw-flow-value').textContent()).includes('Volume unavailable'),'Missing volume zero-filled');assert(await p.locator(`#sw-flow-chart [data-missing-time="${bar.time}"]`).count()===1,'Missing volume not marked');}
   if(condition==='zero-volume')assert(await p.locator(`#sw-flow-chart [data-time="${bar.time}"]`).getAttribute('data-value')==='0','Zero volume treated missing');
   if(condition==='neutral-model')assert((await p.locator('#sw-forecast').textContent()).includes('Neutral 80%')&&(await p.locator('#sw-model-value').textContent())==='0.0 pp','Neutral forecast confused with unavailable');
   if(condition==='missing-forecast')assert(await p.locator('#sw-forecast').getAttribute('data-origin')==='','Missing forecast backfilled');
   assert((await p.locator('#sw-flow-value').textContent()).includes('aggressor flow unavailable'),'Aggressor flow fabricated in fixture');checks.push({status:'PASS',fixture:condition,source_data_modified:false});await p.close();
  }
  assert(!errors.length,'Browser errors '+errors.join(';'));
 }catch(e){failure=e.message;}finally{await browser.close();}
 const run={time:new Date().toISOString(),status:failure?'FAIL':'PASS',failure,completed_cases:checks.length,source_sha256:crypto.createHash('sha256').update(js+css).digest('hex'),data_sha256:crypto.createHash('sha256').update(fs.readFileSync(dataPath)).digest('hex'),fragment_sha256:supplied?crypto.createHash('sha256').update(supplied).digest('hex'):null};
 const history=fs.existsSync(iterationsFile)?JSON.parse(fs.readFileSync(iterationsFile,'utf8')):[];history.push(run);fs.writeFileSync(iterationsFile,JSON.stringify(history,null,2)+'\n');fs.writeFileSync(path.join(privateDir,'ui-verification.json'),JSON.stringify({...run,browser_errors:errors,checks},null,2)+'\n');console.log(JSON.stringify({status:run.status,failure,completed_cases:checks.length}));if(failure)process.exitCode=1;
})();
