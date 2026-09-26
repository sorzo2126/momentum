// Verify the published Markdown in memory; no HTML artifact is created.
const fs=require('fs'), path=require('path'), {pathToFileURL}=require('url');
const {chromium}=require('playwright');
const root=__dirname;

(async()=>{
  const {marked}=await import(pathToFileURL(require.resolve('marked')).href);
  const files=fs.readdirSync(root).filter(x=>x.endsWith('.md')).sort();
  const options={headless:true};
  if(process.env.BROWSER_EXECUTABLE) options.executablePath=process.env.BROWSER_EXECUTABLE;
  const browser=await chromium.launch(options);
  const results=[];
  try {
    const page=await browser.newPage({viewport:{width:1250,height:1100}});
    for(const name of files){
      const md=fs.readFileSync(path.join(root,name),'utf8');
      if(md.includes('$$')) throw Error('Unrendered display equation: '+name);
      // Check every relative Markdown destination, including references outside this subfolder.
      for(const match of md.matchAll(/\]\((<[^>]+>|[^\s)]+)\)/g)){
        const target=match[1].replace(/^<|>$/g,'');
        if(/^(https?:|mailto:|#)/.test(target))continue;
        if(/^[A-Za-z]:/.test(target))throw Error('Nonportable local link: '+target);
        const file=decodeURIComponent(target.split('#')[0]);
        if(!fs.existsSync(path.resolve(root,file)))throw Error('Missing link '+name+' -> '+target);
      }
      const html=marked.parse(md).replace(/src="([^\"]+)"/g,(_,url)=>{
        const file=path.resolve(root,url);
        if(!fs.existsSync(file))throw Error('Missing image '+file);
        return `src="data:image/${file.endsWith('.svg')?'svg+xml':'png'};base64,${fs.readFileSync(file).toString('base64')}"`;
      });
      for(const scheme of ['light','dark']){
        await page.emulateMedia({colorScheme:scheme});
        await page.setContent(`<style>:root{color-scheme:light dark}body{max-width:1080px;margin:30px auto;padding:0 25px;background:light-dark(#fff,#17191c);color:light-dark(#202124,#e8eaed);font:16px/1.65 system-ui}h1,h2{line-height:1.3}h2{margin-top:42px}img{max-width:100%;vertical-align:middle}p:has(>img:only-child){margin:25px 0}table{border-collapse:collapse;font-size:13px;display:block;overflow:auto}td,th{border:1px solid #888;padding:8px}code{font-size:13px;overflow-wrap:anywhere}</style>${html}`,{waitUntil:'load'});
        const stats=await page.evaluate(()=>({images:document.images.length,
          broken:[...document.images].filter(x=>!x.complete||x.naturalWidth===0).length,
          rawMath:document.body.innerText.includes('$$'),
          mathBoxes:[...document.querySelectorAll('pre')].filter(x=>/\\frac|\$\$/.test(x.textContent)).length}));
        if(stats.broken||stats.rawMath||stats.mathBoxes)throw Error(name+JSON.stringify(stats));
        results.push({file:name,scheme,...stats});
        if(name==='REPORT.md'){
          if(stats.images!==19)throw Error('Expected 18 equations and one existing result plot.');
          await page.getByRole('heading',{name:'7. Give the thermodynamics a definite job',exact:true}).evaluate(el=>window.scrollTo(0,el.offsetTop-20));
          await page.screenshot({path:path.join(root,`render-check-${scheme}.png`)});
        }
      }
    }
  }finally{await browser.close();}
  fs.writeFileSync(path.join(root,'render-verification.json'),JSON.stringify({status:'PASS',results},null,2)+'\n');
  console.log(JSON.stringify({status:'PASS',documents:files.length,scheme_checks:results.length,math_equations:18}));
})().catch(e=>{console.error(e);process.exit(1);});
