const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('playwright');

(async () => {
  const root = __dirname;
  const dest = path.join(root, 'capture/website');
  for (const dir of ['screenshots', 'assets/media', 'extracted']) fs.mkdirSync(path.join(dest, dir), { recursive: true });
  const source = path.join(root, 'capture/site/PROMARK-preview');
  fs.cpSync(path.join(source, 'media'), path.join(dest, 'assets/media'), { recursive: true });
  fs.copyFileSync(path.join(source, 'logo.svg'), path.join(dest, 'assets/logo-original.svg'));
  const browser = await chromium.launch({ executablePath: '/usr/bin/chromium', headless: true,
    args: ['--no-sandbox', '--disable-dev-shm-usage'],
    env: { ...process.env, XDG_CACHE_HOME: '/tmp/promark-browser-cache', XDG_CONFIG_HOME: '/tmp/promark-browser-config' } });
  try {
    const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
    await page.goto('http://127.0.0.1:4307/', { waitUntil: 'networkidle' });
    await page.evaluate(() => document.fonts.ready);
    const metrics = await page.evaluate(() => {
      const styles = [...document.querySelectorAll('*')].map(e=>getComputedStyle(e));
      const colors = {};
      for (const s of styles) for (const c of [s.color,s.backgroundColor]) colors[c]=(colors[c]||0)+1;
      return { capture_basis: 'Local rendering of the source repository bundled website; not a successful live GitHub Pages crawl',
        colors: Object.entries(colors).sort((a,b)=>b[1]-a[1]).slice(0,12),
        fonts: [...new Set(styles.map(s=>s.fontFamily))], sections: document.querySelectorAll('main section').length,
        headings: document.querySelectorAll('h1,h2,h3').length, ctas: document.querySelectorAll('.button').length,
        images: [...document.images].map(i=>({src:i.getAttribute('src'),alt:i.alt,width:i.naturalWidth,height:i.naturalHeight})),
        text: [...document.querySelectorAll('h1,h2,h3,p,a')].map(e=>`[${e.tagName.toLowerCase()}] ${e.innerText.replace(/\s+/g,' ').trim()}`).filter(x=>x.length>4),
        full_height: document.documentElement.scrollHeight };
    });
    fs.writeFileSync(path.join(dest,'extracted/tokens.json'),JSON.stringify(metrics,null,2)+'\n');
    fs.writeFileSync(path.join(dest,'extracted/visible-text.txt'),metrics.text.join('\n')+'\n');
    fs.writeFileSync(path.join(dest,'extracted/asset-descriptions.md'),metrics.images.map(i=>`- ${i.src}: ${i.alt} (${i.width} × ${i.height})`).join('\n')+'\n');
    for (const [n,y] of [0,800,1800,3000].entries()) {
      await page.evaluate(y=>window.scrollTo(0,y),y); await page.waitForTimeout(300);
      await page.screenshot({path:path.join(dest,`screenshots/scroll-${String(n).padStart(3,'0')}.png`)});
    }
    const mobile = await browser.newPage({viewport:{width:480,height:900},deviceScaleFactor:2});
    await mobile.goto('http://127.0.0.1:4307/',{waitUntil:'networkidle'});
    await mobile.waitForTimeout(500);
    await mobile.screenshot({path:path.join(dest,'screenshots/mobile-home.png')});
    await mobile.screenshot({path:path.join(dest,'screenshots/mobile-home-full.png'),fullPage:true});
    const serviceTop = await mobile.evaluate(()=>[...document.querySelectorAll('h2')].find(e=>e.textContent.includes('Contenu, web'))?.closest('section')?.offsetTop || 1600);
    fs.writeFileSync(path.join(dest,'extracted/mobile-geometry.json'),JSON.stringify({viewport:[480,900],device_scale:2,service_top_css_pixels:serviceTop},null,2)+'\n');
    await mobile.evaluate(y=>window.scrollTo(0,y),serviceTop);await mobile.waitForTimeout(500);
    await mobile.screenshot({path:path.join(dest,'screenshots/mobile-services.png')});
    await mobile.goto('http://127.0.0.1:4307/services/index.html',{waitUntil:'networkidle'});
    await mobile.waitForTimeout(400);
    await mobile.screenshot({path:path.join(dest,'screenshots/mobile-services-page.png')});
    console.log(JSON.stringify({screenshots:8,assets:fs.readdirSync(path.join(dest,'assets/media')).length+1,sections:metrics.sections,headings:metrics.headings,ctas:metrics.ctas,fonts:metrics.fonts,serviceTop},null,2));
  } finally { await browser.close(); }
})().catch(e=>{console.error(e);process.exit(1)});
