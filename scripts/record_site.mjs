#!/usr/bin/env node
// Record a REAL site as footage: the page loading in real time, then a smooth eased scroll, frame by frame.
//
//   node record_site.mjs <url> <out.mp4> [--scroll 2400] [--load 2.6] [--secs 5] [--dark] [--desktop]
//
// Mobile by default (432x768 @2.5x -> 1080x1920, fills a vertical reel). Use the MP4 in a `clip` scene.
import { spawn } from 'node:child_process';
import ffmpegStatic from 'ffmpeg-static';
import { launch } from './chrome.mjs';

const args = process.argv.slice(2);
const flag = (k, d) => { const i = args.indexOf('--' + k); return i < 0 ? d : args[i + 1]; };
const [url, out] = args.filter((a, i) => !a.startsWith('--') && !(i > 0 && ['--scroll', '--load', '--secs'].includes(args[i - 1])));
if (!url || !out) { console.error('usage: record_site.mjs <url> <out.mp4> [--scroll px] [--load s] [--secs s] [--dark] [--desktop]'); process.exit(2); }
const dark = args.includes('--dark'), desktop = args.includes('--desktop');
const FPS = 30, LOAD = +flag('load', 2.6), SCROLL = +flag('secs', 5), PX = +flag('scroll', 2400);

const b = await launch();
try {
  const p = await b.newPage();
  await p.setViewport(desktop ? { width: 1280, height: 1560, deviceScaleFactor: 1 } : { width: 432, height: 768, deviceScaleFactor: 2.5, isMobile: true, hasTouch: true });
  if (!desktop) await p.setUserAgent('Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1');
  await p.emulateMediaFeatures([{ name: 'prefers-color-scheme', value: dark ? 'dark' : 'light' }]);
  const ff = spawn(process.env.FFMPEG || ffmpegStatic, ['-y', '-v', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-', '-vf', 'scale=1080:-2', '-c:v', 'libx264', '-crf', '17', '-pix_fmt', 'yuv420p', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const push = async buf => { if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r)); };
  const grab = () => p.screenshot({ type: 'jpeg', quality: 90 });
  // 1. the real page load, one frame per 1/FPS of wall time (repeat the last paint while the next one is slow)
  await p.goto('about:blank');
  const nav = p.goto(url, { waitUntil: 'networkidle2', timeout: 60000 }).catch(() => {});
  const t0 = Date.now(); let k = 0;
  while ((Date.now() - t0) / 1000 < LOAD) { const buf = await grab().catch(() => null); const due = Math.floor((Date.now() - t0) / 1000 * FPS); while (buf && k <= due) { await push(buf); k++; } }
  await nav;
  await p.addStyleTag({ content: 'html{scroll-behavior:auto!important}' }).catch(() => {});
  await new Promise(r => setTimeout(r, 1200));
  // 2. eased scroll, frame-exact
  const n = SCROLL * FPS;
  for (let i = 0; i <= n; i++) {
    const q = i / n, e = q < .5 ? 4 * q * q * q : 1 - Math.pow(-2 * q + 2, 3) / 2;
    await p.evaluate(y => scrollTo(0, y), Math.round(e * PX));
    await new Promise(r => setTimeout(r, 30));
    await push(await grab());
  }
  ff.stdin.end(); await new Promise(r => ff.on('close', r));
  console.log('OK', out, `${(k / FPS + SCROLL).toFixed(1)} s`);
} finally { await b.close(); }
