// Read-only documentation, notebook and delivered-chart integrity checks.
// Browser screenshots containing market prices are never written to a tracked path.
const fs=require('fs'),path=require('path'),crypto=require('crypto'),{pathToFileURL}=require('url'),{chromium}=require('playwright');
const root=__dirname,sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
function walk(dir){return fs.readdirSync(dir,{withFileTypes:true}).flatMap(e=>e.isDirectory()?(['private','__pycache__'].includes(e.name)?[]:walk(path.join(dir,e.name))):[path.join(dir,e.name)]);}
async function mathMarkdown(md){
 if(!md.includes('$$'))return md;
 const cache=path.join(root,'private','katex-0.16.22.cjs');
 if(!fs.existsSync(cache)){const response=await fetch('https://cdn.jsdelivr.net/npm/katex@0.16.22/dist/katex.js');if(!response.ok)throw Error('Cannot load pinned math renderer');fs.mkdirSync(path.dirname(cache),{recursive:true});fs.writeFileSync(cache,await response.text());}
 const katex=require(cache);
 return md.replace(/\$\$([\s\S]*?)\$\$/g,(_,formula)=>'\n<div class="display-math">'+katex.renderToString(formula,{displayMode:true,throwOnError:true,output:'mathml'})+'</div>\n')
  .replace(/(?<!\$)\$([^\n$]+)\$(?!\$)/g,(match,formula)=>formula.trim()!==formula?match:katex.renderToString(formula,{displayMode:false,throwOnError:true,output:'mathml'}));
}
(async()=>{
 const {marked}=await import(pathToFileURL(require.resolve('marked')).href),files=walk(root).filter(p=>p.endsWith('.md'));
 const browser=await chromium.launch({headless:true,executablePath:process.env.BROWSER_EXECUTABLE}),checks=[];
 try{const page=await browser.newPage({viewport:{width:1000,height:1000}});
 for(const file of files){const md=fs.readFileSync(file,'utf8');
  if([...md.matchAll(/```[\s\S]*?```/g)].some(m=>m[0].includes('$$')))throw Error('Formula inside code box: '+file);
  for(const m of md.matchAll(/\]\((<[^>]+>|[^\s)]+)\)/g)){const target=m[1].replace(/^<|>$/g,'');if(/^(https?:|mailto:|#)/.test(target))continue;if(!fs.existsSync(path.resolve(path.dirname(file),decodeURIComponent(target.split('#')[0]))))throw Error('Broken document link: '+target);}
  const html=marked.parse(await mathMarkdown(md)).replace(/src="([^"]+)"/g,(_,url)=>{const p=path.resolve(path.dirname(file),url);if(!fs.existsSync(p))throw Error('Missing figure: '+p);return `src="data:image/png;base64,${fs.readFileSync(p).toString('base64')}"`;});
  for(const scheme of ['light','dark']){await page.emulateMedia({colorScheme:scheme});await page.setContent(`<style>:root{color-scheme:light dark}body{font:16px/1.6 system-ui;margin:24px;max-width:950px;background:light-dark(#fff,#17191c);color:light-dark(#202124,#e8eaed)}h1,h2{line-height:1.3}img{max-width:100%}table{display:block;overflow:auto;border-collapse:collapse;font-size:13px}td,th{border-bottom:1px solid #888;padding:8px}pre{overflow:auto}code{overflow-wrap:anywhere}</style>${html}`,{waitUntil:'load'});
   const state=await page.evaluate(()=>({broken:[...document.images].filter(x=>!x.complete||!x.naturalWidth).length,mathBoxes:[...document.querySelectorAll('pre')].filter(x=>x.textContent.includes('$$')).length}));if(state.broken||state.mathBoxes)throw Error('Render failure '+file);checks.push({file:path.relative(root,file),scheme,status:'PASS'});
  }
 }
 }finally{await browser.close();}
 const nb=JSON.parse(fs.readFileSync(path.join(root,'SPY-real-data-study.ipynb'),'utf8'));
 if(nb.nbformat!==4||nb.cells.some(c=>c.outputs?.some(o=>o.output_type==='error')))throw Error('Notebook error');
 const verification=JSON.parse(fs.readFileSync(path.join(root,'verification.json'),'utf8'));
 if(sha(path.join(root,'run_study.py'))!==verification.checks.runner_sha256)throw Error('Runner hash mismatch');
 if(sha(path.join(root,'protocol.json'))!==verification.checks.protocol_sha256)throw Error('Protocol changed after run');
 const ui=JSON.parse(fs.readFileSync(path.join(root,'private/ui-verification.json'),'utf8'));
 if(ui.status!=='PASS'||ui.data_sha256!==sha(path.join(root,'private/chart-data.json')))throw Error('UI tested another dataset');
 if(process.argv[2]){
  const fragment=fs.readFileSync(process.argv[2],'utf8');if(sha(process.argv[2])!==ui.fragment_sha256)throw Error('Inline preview differs from tested version');
  const inline=JSON.parse(fragment.match(/<script id="sw-data" type="application\/json">([\s\S]*?)<\/script>/)[1]);
  if(JSON.stringify(inline)!==JSON.stringify(JSON.parse(fs.readFileSync(path.join(root,'private/chart-data.json'),'utf8'))))throw Error('Inline market data mismatch');
 }
 const result={status:'PASS',documents:files.length,render_checks:checks.length,notebook_cells:nb.cells.length,notebook_error_outputs:0,browser_cases:ui.completed_cases,inline_data_and_hash_verified:!!process.argv[2],checks};
 fs.writeFileSync(path.join(root,'delivery-verification.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify({...result,checks:undefined}));
})().catch(e=>{console.error(e.message);process.exitCode=1;});
