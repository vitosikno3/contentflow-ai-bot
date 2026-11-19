// Рендер бесшовных зацикленных видео для LED-фотозоны.
// Запуск: node render.js [секунды=12] [fps=30]   (или node render.js preview — один кадр)
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const arg = process.argv[2];
const PREVIEW = arg === 'preview';
const SEC = PREVIEW ? 1 : +(arg || 12);
const FPS = +(process.argv[3] || 30);
const N = SEC * FPS;
const OUT = path.join(__dirname, 'out');
fs.mkdirSync(OUT, { recursive: true });

function ffmpeg(file) {
  const p = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'png', '-i', '-',
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '14', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', file], { stdio: ['pipe', 'inherit', 'inherit'] });
  return p;
}
const write = (p, buf) => new Promise(r => p.stdin.write(buf) ? r() : p.stdin.once('drain', r));
const close = p => new Promise(r => { p.on('close', r); p.stdin.end(); });

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('file://' + path.join(__dirname, 'scene.html') + '?render=1');
  await page.evaluate(() => window.ready);
  const grab = (id) => page.evaluate(id => document.getElementById(id).toDataURL('image/png').split(',')[1], id);

  if (PREVIEW) {
    for (const p of [0, 0.37]) {
      await page.evaluate(p => window.renderFrame(p), p);
      fs.writeFileSync(path.join(OUT, `preview_walls_${p}.png`), Buffer.from(await grab('walls'), 'base64'));
      fs.writeFileSync(path.join(OUT, `preview_floor_${p}.png`), Buffer.from(await grab('floor'), 'base64'));
    }
    await browser.close(); return;
  }
  const fw = ffmpeg(path.join(OUT, 'walls_2160x1440.mp4'));
  const ff = ffmpeg(path.join(OUT, 'floor_1080x1080.mp4'));
  for (let i = 0; i < N; i++) {
    await page.evaluate(p => window.renderFrame(p), i / N);  // i/N: кадр N совпадает с кадром 0 → бесшовная петля
    await write(fw, Buffer.from(await grab('walls'), 'base64'));
    await write(ff, Buffer.from(await grab('floor'), 'base64'));
    if (i % 30 === 0) process.stdout.write(`${i}/${N}\n`);
  }
  await Promise.all([close(fw), close(ff)]);
  await browser.close();
})();
