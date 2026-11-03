// node tools/render.cjs <firstFrame> <endFrame> <out.mp4>
// 60 fps, 4 subframes per frame blended with ffmpeg tmix (motion blur by averaging).
const { chromium } = require('playwright');
const { spawn } = require('node:child_process');
(async () => {
  const [a, b, out] = [Number(process.argv[2]), Number(process.argv[3]), process.argv[4]];
  const SUB = 4, FPS = 60;
  const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-c:v', 'mjpeg', '-framerate', String(FPS * SUB), '-i', '-',
    '-vf', `tmix=frames=${SUB}:weights='1 1 1 1',select='eq(mod(n\\,${SUB})\\,${SUB - 1})',setpts=N/(${FPS}*TB)`,
    '-r', String(FPS), '-c:v', 'libx264', '-crf', '12', '-preset', 'medium', '-pix_fmt', 'yuv420p', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const browser = await chromium.launch({ args: ['--force-device-scale-factor=1'] });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1440 } });
  page.on('pageerror', e => console.error('pageerror:', e.message));
  await page.goto(process.env.URL || 'http://127.0.0.1:8765/launch/prompolu/index.html');
  await page.evaluate(() => window.ready);
  const t0 = Date.now();
  for (let f = a; f < b; f++) {
    for (let k = 0; k < SUB; k++) {
      const t = (f * SUB + k) / (FPS * SUB);
      await page.evaluate(t => window.seek(t), t);
      const buf = await page.screenshot({ type: 'jpeg', quality: 95, clip: { x: 0, y: 0, width: 1440, height: 1440 } });
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    }
    if ((f - a) % 60 === 0) console.log(out, f, ((Date.now() - t0) / 1000).toFixed(0) + 's');
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  await browser.close();
})();
