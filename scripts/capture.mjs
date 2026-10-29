#!/usr/bin/env node
// Screenshot a product's real screens for a hype reel.
//
//   node capture.mjs <url> <outdir> [--mobile] [--full] [--name home] [--scroll 900]
//                    [--wait 1500] [--dark] [--click "#start,.next"] [--js "code"] [--rects "h1,.pricing,#cta"]
//
// Writes <outdir>/<name>.jpg and prints its size plus, for every --rects selector,
// the element's box as fractions of the screenshot: paste those straight into a
// screen scene's "focus" list.
import fs from 'node:fs';
import path from 'node:path';
import { launch } from './chrome.mjs';

const args = process.argv.slice(2);
const flag = (k, d) => { const i = args.indexOf('--' + k); if (i < 0) return d; const v = args[i + 1]; return v === undefined || v.startsWith('--') ? true : v; };
const [url, outdir] = args.filter((a, i) => !a.startsWith('--') && !(i > 0 && args[i - 1].startsWith('--') && !['--mobile', '--full', '--dark'].includes(args[i - 1])));
if (!url || !outdir) { console.error('usage: capture.mjs <url> <outdir> [--mobile] [--full] [--name x] [--scroll px] [--wait ms] [--dark] [--click sel] [--rects "a,b"]'); process.exit(2); }

const mobile = !!flag('mobile', false), full = !!flag('full', false), dark = !!flag('dark', false);
const name = flag('name', mobile ? 'mobile' : 'desktop');
const vp = mobile ? { width: 390, height: 844, deviceScaleFactor: 3, isMobile: true, hasTouch: true } : { width: 1440, height: 900, deviceScaleFactor: 1.25 };

const browser = await launch();
try {
  const page = await browser.newPage();
  await page.setViewport(vp);
  if (mobile) await page.setUserAgent('Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1');
  if (dark) await page.emulateMediaFeatures([{ name: 'prefers-color-scheme', value: 'dark' }]);
  await page.goto(url, { waitUntil: 'networkidle2', timeout: 60000 }).catch(e => console.warn('WARN load:', e.message));
  await page.addStyleTag({ content: 'html{scroll-behavior:auto!important} *::-webkit-scrollbar{display:none}' }).catch(() => {});
  if (full) { // walk down once so lazy images and charts load
    await page.evaluate(async () => { for (let y = 0; y < document.body.scrollHeight; y += innerHeight * .8) { scrollTo(0, y); await new Promise(r => setTimeout(r, 120)); } scrollTo(0, 0); });
  }
  for (const sel of flag('click') ? String(flag('click')).split(',') : []) { // walk a flow: click each selector in turn
    await page.click(sel.trim()).catch(e => console.warn('WARN click:', e.message));
    await new Promise(r => setTimeout(r, 700));
  }
  if (flag('js')) await page.evaluate(`(async () => { ${flag('js')} })()`).catch(e => console.warn('WARN js:', e.message));
  if (flag('scroll')) await page.evaluate(y => scrollTo(0, y), +flag('scroll'));
  await new Promise(r => setTimeout(r, +flag('wait', 1200)));
  fs.mkdirSync(outdir, { recursive: true });
  const file = path.join(outdir, name + '.jpg');
  let clip;
  if (full) {
    const h = await page.evaluate(() => Math.min(document.documentElement.scrollHeight, 7000));
    clip = { x: 0, y: 0, width: vp.width, height: h };
  }
  await page.screenshot({ path: file, type: 'jpeg', quality: 86, captureBeyondViewport: full, ...(clip ? { clip } : {}) });
  const box = full ? clip : { x: 0, y: 0, width: vp.width, height: vp.height };
  const out = { file: file.replace(/\\/g, '/'), width: Math.round(box.width * vp.deviceScaleFactor), height: Math.round(box.height * vp.deviceScaleFactor), rects: {} };
  const sels = flag('rects') ? String(flag('rects')).split(',').map(s => s.trim()).filter(Boolean) : [];
  for (const sel of sels) {
    const r = await page.evaluate((sel, full) => { const el = document.querySelector(sel); if (!el) return null; const b = el.getBoundingClientRect(); const oy = full ? scrollY : 0; return { x: b.left, y: b.top + oy, w: b.width, h: b.height }; }, sel, full);
    out.rects[sel] = r ? { x: +(r.x / box.width).toFixed(4), y: +(r.y / box.height).toFixed(4), w: +(r.w / box.width).toFixed(4), h: +(r.h / box.height).toFixed(4) } : null;
  }
  console.log(JSON.stringify(out, null, 2));
} finally { await browser.close(); }
