// Render Markdown in memory; no HTML deliverable is created.
const fs = require('fs'), path = require('path'), {pathToFileURL} = require('url');
const {chromium} = require('playwright');
const root = process.env.CGB_SIMULATION_OUTPUT ? path.resolve(process.env.CGB_SIMULATION_OUTPUT) : path.resolve(__dirname, '..');

(async () => {
  const {marked} = await import(pathToFileURL(require.resolve('marked')).href);
  const md = fs.readFileSync(path.join(root, 'REPORT.md'), 'utf8');
  const html = marked.parse(md).replace(/src="([^\"]+)"/g, (_, url) => {
    const file = path.resolve(root, url);
    if (!fs.existsSync(file)) throw Error('Missing image: ' + file);
    return `src="data:image/${file.endsWith('.svg') ? 'svg+xml' : 'png'};base64,${fs.readFileSync(file).toString('base64')}"`;
  });
  const options = {headless: true};
  if (process.env.BROWSER_EXECUTABLE) options.executablePath = process.env.BROWSER_EXECUTABLE;
  const browser = await chromium.launch(options);
  const results = [];
  try {
    const page = await browser.newPage({viewport: {width: 1250, height: 1050}});
    for (const scheme of ['light', 'dark']) {
      await page.emulateMedia({colorScheme: scheme});
      await page.setContent(`<style>:root{color-scheme:light dark}body{max-width:1080px;margin:30px auto;padding:0 25px;background:light-dark(#fff,#17191c);color:light-dark(#202124,#e8eaed);font:16px/1.65 system-ui}h1,h2{line-height:1.3}h2{margin-top:42px}img{max-width:100%;vertical-align:middle}p:has(>img:only-child){margin:25px 0}table{border-collapse:collapse;font-size:13px;display:block;overflow:auto}td,th{border:1px solid #888;padding:8px}code{font-size:13px}</style>${html}`, {waitUntil: 'load'});
      const stats = await page.evaluate(() => ({
        images: document.images.length,
        broken: [...document.images].filter(x => !x.complete || x.naturalWidth === 0).length,
        rawMath: document.body.innerText.includes('$$'),
        mathBoxes: [...document.querySelectorAll('pre')].filter(x => /\\frac|\$\$/.test(x.textContent)).length
      }));
      results.push({scheme, ...stats});
      await page.getByRole('heading', {name: '7. Discount curves: one source for many prices', exact: true}).evaluate(el => window.scrollTo(0, el.offsetTop - 20));
      await page.screenshot({path: path.join(root, `render-check-${scheme}.png`)});
    }
  } finally { await browser.close(); }
  if (results.some(x => x.images !== 49 || x.broken || x.rawMath || x.mathBoxes)) throw Error(JSON.stringify(results));
  fs.writeFileSync(path.join(root, 'render-verification.json'), JSON.stringify(results, null, 2));
  console.log(JSON.stringify(results));
})().catch(error => { console.error(error); process.exit(1); });
