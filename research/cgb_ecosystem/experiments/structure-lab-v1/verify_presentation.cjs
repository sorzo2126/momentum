// Validate Markdown and render it in memory; no HTML deliverable is created.
const fs=require('fs'), path=require('path'), {pathToFileURL}=require('url');
const {chromium}=require('playwright');
const root=__dirname;
function walk(dir){return fs.readdirSync(dir,{withFileTypes:true}).flatMap(e=>e.isDirectory()?(e.name==='__pycache__'?[]:walk(path.join(dir,e.name))):[path.join(dir,e.name)]);}
(async()=>{
  const {marked}=await import(pathToFileURL(require.resolve('marked')).href);
  const files=walk(root).filter(f=>f.endsWith('.md')).concat(path.resolve(root,'../../docs/trader-use.md')).sort();
  const options={headless:true};
  if(process.env.BROWSER_EXECUTABLE)options.executablePath=process.env.BROWSER_EXECUTABLE;
  const browser=await chromium.launch(options), results=[];
  try{
    const page=await browser.newPage({viewport:{width:1250,height:1100}});
    for(const file of files){
      const md=fs.readFileSync(file,'utf8'), dir=path.dirname(file), name=path.relative(root,file).replace(/\\/g,'/');
      if(md.includes('$$'))throw Error('Raw display math: '+name);
      for(const m of md.matchAll(/\]\((<[^>]+>|[^\s)]+)\)/g)){
        const target=m[1].replace(/^<|>$/g,'');
        if(/^(https?:|mailto:|#)/.test(target))continue;
        if(/^[A-Za-z]:/.test(target))throw Error('Nonportable file link: '+target);
        if(!fs.existsSync(path.resolve(dir,decodeURIComponent(target.split('#')[0]))))throw Error('Missing link '+name+' -> '+target);
      }
      const html=marked.parse(md).replace(/src="([^"]+)"/g,(_,url)=>{
        const image=path.resolve(dir,url);
        if(!fs.existsSync(image))throw Error('Missing image '+image);
        return `src="data:image/${image.endsWith('.svg')?'svg+xml':'png'};base64,${fs.readFileSync(image).toString('base64')}"`;
      });
      for(const scheme of ['light','dark']){
        await page.emulateMedia({colorScheme:scheme});
        await page.setContent(`<style>:root{color-scheme:light dark}body{max-width:1080px;margin:30px auto;padding:0 25px;background:light-dark(#fff,#17191c);color:light-dark(#202124,#e8eaed);font:16px/1.65 system-ui}h1,h2{line-height:1.3}h2{margin-top:42px}img{max-width:100%;vertical-align:middle}p:has(>img:only-child){margin:25px 0}table{border-collapse:collapse;font-size:13px;display:block;overflow:auto}td,th{border:1px solid #888;padding:8px}code{font-size:13px;overflow-wrap:anywhere}</style>${html}`,{waitUntil:'load'});
        const stats=await page.evaluate(()=>({images:document.images.length,broken:[...document.images].filter(x=>!x.complete||!x.naturalWidth).length,rawMath:document.body.innerText.includes('$$'),mathBoxes:[...document.querySelectorAll('pre')].filter(x=>/\\frac|\$\$/.test(x.textContent)).length}));
        if(stats.broken||stats.rawMath||stats.mathBoxes)throw Error(name+JSON.stringify(stats));
        results.push({file:name,scheme,...stats});
        if(name==='observability/REPORT.md'){
          if(stats.images!==7)throw Error('Expected four equations and three figures.');
          const eq=page.locator('img[alt="Research equation"]').nth(1);
          await eq.evaluate(el=>window.scrollTo(0,el.getBoundingClientRect().top+window.scrollY-100));
          await page.screenshot({path:path.join(root,`render-check-${scheme}.png`)});
        }
      }
    }
  }finally{await browser.close();}
  const result={status:'PASS',documents:files.length,scheme_checks:results.length,rendered_equations:4,results};
  fs.writeFileSync(path.join(root,'render-verification.json'),JSON.stringify(result,null,2)+'\n');
  console.log(JSON.stringify({...result,results:undefined}));
})().catch(e=>{console.error(e);process.exit(1);});
