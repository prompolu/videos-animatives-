// Render single frames: node tools/stills.mjs out_dir t1 t2 ...
const { chromium } = require('playwright');
const fs = require('node:fs');
(async () => {
const [out, ...ts] = process.argv.slice(2);
fs.mkdirSync(out, { recursive: true });
const browser = await chromium.launch({ args: ['--force-device-scale-factor=1', '--disable-web-security'] });
const page = await browser.newPage({ viewport: { width: 1440, height: 1440 } });
page.on('console', m => console.log('console:', m.text()));
page.on('pageerror', e => console.log('pageerror:', e.message));
await page.goto(process.env.URL || 'http://127.0.0.1:8765/launch/prompolu/index.html');
await page.evaluate(() => window.ready);
for (const t of ts) {
  const t0 = Date.now();
  await page.evaluate(t => window.seek(t), Number(t));
  await page.locator('#frame').screenshot({ path: `${out}/t${Number(t).toFixed(3)}.jpg`, quality: 90, type: 'jpeg' });
  console.log(t, Date.now() - t0, 'ms');
}
await browser.close();
})();
