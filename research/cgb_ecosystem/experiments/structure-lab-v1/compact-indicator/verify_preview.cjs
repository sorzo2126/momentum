// Usage: node verify_preview.cjs <in-conversation fragment path>
// Browser rendering is in memory; no HTML deliverable is written.
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const {chromium}=require('playwright');
(async()=>{
 const fragment=fs.readFileSync(process.argv[2],'utf8');
 if(fragment.includes('__CGB_PREVIEW_DATA__')||fragment.includes('\\"'))throw Error('Unresolved or escaped markup');
 const browser=await chromium.launch({headless:true,executablePath:process.env.BROWSER_EXECUTABLE});
 const checks=[],errors=[];
 try{
  for(const scheme of ['light','dark'])for(const width of [736,360,320]){
   const page=await browser.newPage({viewport:{width,height:1100},colorScheme:scheme});
   page.on('pageerror',e=>errors.push(e.message));
   await page.setContent(`<style>html{color-scheme:${scheme}}body{margin:0;padding:0}</style><script>window.Tweak=class{constructor(o){this.redraw=o.onChange}addSelect(obj,key){window.testCase=value=>{obj[key]=value;this.redraw()}}addToggle(){}};<\/script>${fragment}`);
   const detail=await page.evaluate(()=>({overflow:document.documentElement.scrollWidth>innerWidth,hidden:!document.querySelector('#ci-details').open,forecastVisible:!document.querySelector('#ci-forecast').hidden}));
   if(detail.overflow||!detail.hidden||!detail.forecastVisible)throw Error('Initial layout '+JSON.stringify(detail));
   const data=JSON.parse(await page.locator('#ci-data').textContent());
   if(await page.locator('#ci-up-value').textContent()!==(100*data.cases.saved['60'].forecast.p_up).toFixed(1)+'%')throw Error('Wrong displayed probability');
   if(scheme==='light'&&width===736)await page.locator('#cgb-compact').screenshot({path:path.join(__dirname,'compact-preview.png')});
   for(const h of ['120','240','60']){
    await page.locator('#ci-horizon').selectOption(h);
    const txt=await page.locator('#ci-range').textContent(),f=data.cases.saved[h].forecast;
    if(!txt.includes(Math.abs(f.endpoint_q10_ticks).toFixed(1))||!txt.includes(Math.abs(f.endpoint_q90_ticks).toFixed(1)))throw Error('Horizon did not update range');
   }
   await page.locator('summary').click();
   if(!(await page.locator('#ci-detail-grid').textContent()).includes('local_z_30'))throw Error('Details missing');
   if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth))throw Error('Open details overflow');
   await page.locator('summary').click();
   for(const variant of ['stale','expired']){
    await page.evaluate(v=>window.testCase(v),variant);
    if(await page.locator('#ci-forecast').isVisible())throw Error('Stale probability still visible');
    if(!(await page.locator('#ci-mode').textContent()).includes('UI failure example'))throw Error('Unlabelled failure fixture');
    if(scheme==='light'&&width===736&&variant==='stale')await page.locator('#cgb-compact').screenshot({path:path.join(__dirname,'stale-preview.png')});
   }
   await page.evaluate(()=>window.testCase('saved'));
   if(!(await page.locator('#ci-forecast').isVisible()))throw Error('Recovery failed');
   checks.push({scheme,width,status:'PASS',horizon_switches:3,failure_states:2,details_tested:true});
   await page.close();
  }
 }finally{await browser.close();}
 if(errors.length)throw Error(errors.join('\n'));
 const result={status:'PASS',fragment_sha256:crypto.createHash('sha256').update(fragment).digest('hex'),scope:'Interactive saved-forecast preview; no live connection.',checks};
 fs.writeFileSync(path.join(__dirname,'preview-verification.json'),JSON.stringify(result,null,2)+'\n');
 console.log(JSON.stringify({status:'PASS',viewport_theme_cases:checks.length,browser_errors:errors.length}));
})().catch(e=>{console.error(e);process.exit(1);});
